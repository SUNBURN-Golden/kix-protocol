"""Process-local append-only readiness journal.

The file is a restart log for one writer. A complete frame with a bad
checksum fails closed. A trailing incomplete frame is a torn write: it is
discarded and the durable prefix is kept. This file is not protocol truth,
not a replication log, and not a production conformance record.
"""

from __future__ import annotations

import fcntl
import os
from pathlib import Path
import struct
import zlib

from readiness.codec import CodecError, canonical_json, strict_loads
from readiness.migrate import SCHEMA_VERSION, MigrationError, migrate
from readiness.policy import classify_budget

MAGIC = b'KIXRDY01'
HEADER_LEN = 16
MAX_RECORD_BYTES = 1024 * 1024
JOURNAL_NAME = 'journal.v1'

FSM_MACHINES = frozenset({
    'settlement', 'reservation', 'resale', 'credit', 'admission', 'ai_delegation',
})
CORE_MACHINE = 'integration_core'
_STAMPED = frozenset({'schema', 'protocolTruth', 'productionConformance'})
_COMMON = _STAMPED | {'kind', 'machine'}
_FSM_FIELDS = _COMMON | {'entry'}
_CORE_FIELDS = _COMMON | {'operationId', 'actor', 'action', 'body', 'receiptDigest'}


class StoreError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class ReadinessFault(StoreError):
    """Injected crash. The caller must not treat the attempt as durable."""


class ReadinessStore:
    def __init__(self, directory, file_obj, records, end_offset):
        self.directory = directory
        self._file = file_obj
        self.records = records
        self._end = end_offset
        self.committed_bytes = end_offset
        self._torn = False

    @classmethod
    def open(cls, directory):
        root = Path(directory)
        try:
            root.mkdir(parents=True, mode=0o700, exist_ok=True)
        except OSError as exc:
            raise StoreError('JOURNAL_PATH') from exc
        path = root / JOURNAL_NAME
        try:
            fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        except OSError as exc:
            raise StoreError('JOURNAL_PATH') from exc
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            raise StoreError('JOURNAL_LOCKED') from exc
        file_obj = os.fdopen(fd, 'r+b', buffering=0)
        try:
            data = file_obj.read()
            if not data:
                header = MAGIC + struct.pack('>II', SCHEMA_VERSION, 0)
                file_obj.write(header)
                _fsync(file_obj)
                _fsync_directory(root)
                return cls(root, file_obj, [], HEADER_LEN)
            records, end_offset, torn = _parse(data)
            if torn:
                file_obj.seek(end_offset)
                file_obj.truncate()
                _fsync(file_obj)
            file_obj.seek(end_offset)
            return cls(root, file_obj, records, end_offset)
        except Exception:
            try:
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            file_obj.close()
            raise

    def append(self, body, fault=None):
        if self._file is None:
            raise StoreError('JOURNAL_CLOSED')
        if self._torn:
            raise StoreError('JOURNAL_TORN')
        record = _stamp(body)
        payload = canonical_json(record).encode('utf-8')
        if len(payload) > MAX_RECORD_BYTES:
            raise StoreError('RECORD_TOO_LARGE')
        frame = struct.pack('>I', len(payload)) + payload
        frame += struct.pack('>I', zlib.crc32(payload) & 0xFFFFFFFF)
        if fault == 'crash_before_durable':
            raise ReadinessFault('CRASH_BEFORE_DURABLE')
        if fault == 'partial':
            self._file.write(frame[: max(1, len(frame) // 2)])
            self._file.flush()
            self._torn = True
            raise ReadinessFault('PARTIAL_WRITE')
        self._file.write(frame)
        self._file.flush()
        _fsync(self._file)
        self.records.append(record)
        self._end += len(frame)
        self.committed_bytes = self._end
        return record

    def has_operation(self, operation_id):
        return any(record.get('operationId') == operation_id for record in self.records)

    def budget_decision(self, extra, max_records, max_bytes):
        return classify_budget(
            len(self.records), self.committed_bytes, extra, max_records, max_bytes,
        )

    def can_accept(self, extra, max_records, max_bytes):
        code, _limit = self.budget_decision(extra, max_records, max_bytes)
        return code == 'OK'

    def close(self):
        file_obj = self._file
        self._file = None
        if file_obj is None:
            return
        try:
            _fsync(file_obj)
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        file_obj.close()


def _stamp(body):
    if not isinstance(body, dict):
        raise StoreError('JOURNAL_RECORD')
    if _STAMPED & set(body):
        raise StoreError('JOURNAL_RECORD')
    record = {
        'schema': SCHEMA_VERSION,
        'protocolTruth': False,
        'productionConformance': False,
    }
    record.update(body)
    _validate(record)
    return record


def _validate(record):
    if record.get('schema') != SCHEMA_VERSION:
        raise StoreError('UNSUPPORTED_SCHEMA')
    if record.get('protocolTruth') is not False:
        raise StoreError('PROTOCOL_TRUTH_REFUSED')
    if record.get('productionConformance') is not False:
        raise StoreError('PRODUCTION_CONFORMANCE_REFUSED')
    kind = record.get('kind')
    machine = record.get('machine')
    if kind == 'fsm_commit':
        if set(record) != _FSM_FIELDS or machine not in FSM_MACHINES:
            raise StoreError('JOURNAL_RECORD')
        if not isinstance(record.get('entry'), dict):
            raise StoreError('JOURNAL_RECORD')
        return
    if kind == 'core_commit':
        if set(record) != _CORE_FIELDS or machine != CORE_MACHINE:
            raise StoreError('JOURNAL_RECORD')
        if not isinstance(record.get('body'), dict):
            raise StoreError('JOURNAL_RECORD')
        for name in ('operationId', 'actor', 'action', 'receiptDigest'):
            value = record.get(name)
            if not isinstance(value, str) or not value:
                raise StoreError('JOURNAL_RECORD')
        digest = record['receiptDigest']
        if len(digest) != 64 or any(char not in '0123456789abcdef' for char in digest):
            raise StoreError('JOURNAL_RECORD')
        return
    raise StoreError('JOURNAL_RECORD')


def _parse(data):
    if len(data) < HEADER_LEN or data[:8] != MAGIC:
        raise StoreError('JOURNAL_HEADER')
    version, reserved = struct.unpack_from('>II', data, 8)
    if reserved != 0:
        raise StoreError('JOURNAL_HEADER')
    try:
        # The file reader calls migrate() only. That path is schema 1 to
        # schema 1. migrate_v1_to_v2 is not applied here.
        migrate(version, [])
    except MigrationError as exc:
        raise StoreError(exc.code) from exc
    if version != SCHEMA_VERSION:
        raise StoreError('UNSUPPORTED_SCHEMA')
    records = []
    pos = HEADER_LEN
    end_offset = HEADER_LEN
    while pos < len(data):
        if pos + 4 > len(data):
            break
        length = struct.unpack_from('>I', data, pos)[0]
        frame = 4 + length + 4
        if length < 2 or length > MAX_RECORD_BYTES or pos + frame > len(data):
            break
        payload = data[pos + 4:pos + 4 + length]
        crc = struct.unpack_from('>I', data, pos + 4 + length)[0]
        if (zlib.crc32(payload) & 0xFFFFFFFF) != crc:
            raise StoreError('CHECKSUM_MISMATCH')
        try:
            record = strict_loads(payload)
        except CodecError as exc:
            raise StoreError(exc.code) from exc
        try:
            _validate(record)
        except StoreError as exc:
            raise StoreError('JOURNAL_CORRUPT') from exc
        records.append(record)
        pos += frame
        end_offset = pos
    try:
        records = migrate(version, records)
    except MigrationError as exc:
        raise StoreError(exc.code) from exc
    for record in records:
        _validate(record)
    torn = data[end_offset:]
    return records, end_offset, torn


def _fsync(file_obj):
    file_obj.flush()
    os.fsync(file_obj.fileno())


def _fsync_directory(directory):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
