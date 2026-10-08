"""Candidate adapters for the readiness conformance suite and the shared workload."""

from __future__ import annotations

import hashlib
import os
import struct
import zlib
from pathlib import Path

import psycopg
from psycopg import sql

from readiness.codec import CodecError, canonical_json, strict_loads
from readiness.store import ReadinessFault, StoreError, _stamp, _validate

from exploration.stage4.boundary import ExploreBoundary
from exploration.stage4.fdb_c import FdbError
from exploration.stage4.workload import decide, empty_state, payload_sha256

_CORE_PROBE = {
    'kind': 'core_commit',
    'machine': 'integration_core',
    'operationId': 'op-corrupt',
    'actor': 'operator',
    'action': 'advance_clock',
    'body': {'now': 1},
    'receiptDigest': 'ab' * 32,
}


def store_key(directory):
    return hashlib.sha256(os.path.realpath(directory).encode()).hexdigest()[:16]


def _pack(document):
    payload = canonical_json(document).encode('utf-8')
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return struct.pack('>I', crc) + payload


def _unpack(blob):
    if not isinstance(blob, (bytes, bytearray)) or len(blob) < 5:
        raise StoreError('CHECKSUM_MISMATCH')
    crc = struct.unpack('>I', blob[:4])[0]
    payload = bytes(blob[4:])
    if (zlib.crc32(payload) & 0xFFFFFFFF) != crc:
        raise StoreError('CHECKSUM_MISMATCH')
    try:
        return strict_loads(payload)
    except CodecError as exc:
        raise StoreError('JOURNAL_CORRUPT') from exc


def _command_document(command_id, digest, first_result, outcome, amount, nbytes):
    return {
        'admittedBytes': nbytes,
        'amountU128': amount,
        'commandId': command_id,
        'firstResult': first_result,
        'outcome': outcome,
        'payloadSha256': digest,
    }


def _crc(document):
    return zlib.crc32(canonical_json(document).encode('utf-8')) & 0xFFFFFFFF


class _Lock:
    def __init__(self, directory):
        path = Path(directory) / 'explore.lock'
        self._fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            import fcntl
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self._fd)
            raise StoreError('JOURNAL_LOCKED') from exc

    def release(self):
        if self._fd is None:
            return
        import fcntl
        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(self._fd)
        self._fd = None


def _result(decision, log_delta, entries):
    return {
        'outcome': decision.outcome,
        'first_result': decision.first_result,
        'log_delta': log_delta,
        'admitted_entries': entries,
        'capacity_reason': decision.capacity_reason,
        'exploration_data': True,
    }


class PostgresRecordStore:
    def __init__(self, cluster, directory, lock, conn, records, committed_bytes):
        self.cluster = cluster
        self.directory = directory
        self._lock = lock
        self._conn = conn
        self.records = records
        self.committed_bytes = committed_bytes

    @classmethod
    def open(cls, cluster, directory):
        lock = _Lock(directory)
        conn = cluster.connect()
        try:
            name = 's' + store_key(directory)
            conn.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(name)))
            conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(name)))
            conn.execute(
                'CREATE TABLE IF NOT EXISTS rec ('
                'seq bigint PRIMARY KEY, canonical text NOT NULL, '
                'nbytes integer NOT NULL, crc bigint NOT NULL)'
            )
            records, committed = _pg_load_records(conn)
        except Exception:
            conn.close()
            lock.release()
            raise
        return cls(cluster, directory, lock, conn, records, committed)

    def append(self, body, fault=None):
        if self._conn is None:
            raise StoreError('JOURNAL_CLOSED')
        if fault == 'crash_before_durable':
            raise ReadinessFault('CRASH_BEFORE_DURABLE')
        record = _stamp(body)
        _validate(record)
        payload = canonical_json(record).encode('utf-8')
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        text = payload.decode('utf-8')
        try:
            self._conn.execute('BEGIN')
            current = self._conn.execute('SELECT COALESCE(MAX(seq), 0) FROM rec').fetchone()
            seq = int(current[0]) + 1
            self._conn.execute(
                'INSERT INTO rec (seq, canonical, nbytes, crc) VALUES (%s, %s, %s, %s)',
                (seq, text, len(payload), crc),
            )
            if fault == 'partial':
                self._conn.execute('ROLLBACK')
                raise ReadinessFault('PARTIAL_WRITE')
            self._conn.execute('COMMIT')
        except ReadinessFault:
            raise
        except Exception:
            self._rollback()
            raise
        self.records.append(record)
        self.committed_bytes += len(payload)
        return record

    def has_operation(self, operation_id):
        return any(record.get('operationId') == operation_id for record in self.records)

    def can_accept(self, extra, max_records, max_bytes):
        if len(self.records) >= max_records:
            return False
        if self.committed_bytes + extra > max_bytes:
            return False
        return True

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        if self._lock is not None:
            self._lock.release()
            self._lock = None

    def _rollback(self):
        try:
            self._conn.execute('ROLLBACK')
        except psycopg.Error:
            pass


def _pg_load_records(conn):
    rows = conn.execute('SELECT seq, canonical, nbytes, crc FROM rec ORDER BY seq').fetchall()
    records = []
    committed = 0
    expected = 1
    for seq, text, nbytes, crc in rows:
        if int(seq) != expected:
            raise StoreError('JOURNAL_CORRUPT')
        payload = text.encode('utf-8')
        if len(payload) != int(nbytes) or (zlib.crc32(payload) & 0xFFFFFFFF) != int(crc):
            raise StoreError('CHECKSUM_MISMATCH')
        try:
            record = strict_loads(payload)
        except CodecError as exc:
            raise StoreError('JOURNAL_CORRUPT') from exc
        try:
            _validate(record)
        except StoreError as exc:
            raise StoreError('JOURNAL_CORRUPT') from exc
        records.append(record)
        committed += len(payload)
        expected += 1
    return records, committed


class PostgresUnit:
    def __init__(self, cluster, directory, budget):
        self.cluster = cluster
        self.directory = directory
        self.budget = dict(budget)
        self._lock = _Lock(directory)
        self._conn = cluster.connect()
        try:
            name = 'u' + store_key(directory)
            self._conn.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(name)))
            self._conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(name)))
            self._conn.execute(
                'CREATE TABLE IF NOT EXISTS command_result ('
                'command_id text PRIMARY KEY, payload_sha256 text NOT NULL, '
                'first_result text NOT NULL, outcome text NOT NULL, '
                'amount_u128 text NOT NULL, admitted_bytes integer NOT NULL, '
                'crc bigint NOT NULL)'
            )
            self._conn.execute(
                'CREATE TABLE IF NOT EXISTS slot_hold ('
                'slot text PRIMARY KEY, command_id text NOT NULL)'
            )
            self._conn.execute(
                'CREATE TABLE IF NOT EXISTS observation ('
                'observation_id text PRIMARY KEY, nbytes integer NOT NULL)'
            )
            self._conn.execute(
                'CREATE TABLE IF NOT EXISTS meta (key text PRIMARY KEY, value text NOT NULL)'
            )
            self._ensure_budget()
        except Exception:
            self.close()
            raise

    def apply(self, command):
        before = self.cluster.wal_bytes()
        try:
            state = self._load(read_only=True)
            preview = decide(state, command)
            if not _writes(preview):
                after = self.cluster.wal_bytes()
                return _result(preview, after - before, state.admitted_entries)
            self._conn.execute('BEGIN')
            self._conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE READ WRITE')
            state = self._load(read_only=False)
            decision = decide(state, command)
            if not _writes(decision):
                self._conn.execute('ROLLBACK')
                after = self.cluster.wal_bytes()
                return _result(decision, after - before, state.admitted_entries)
            self._write(command, decision)
            self._conn.execute('COMMIT')
        except psycopg.Error as exc:
            self._rollback()
            return {
                'outcome': 'error',
                'first_result': '',
                'log_delta': None,
                'admitted_entries': None,
                'capacity_reason': None,
                'error': exc.__class__.__name__,
                'exploration_data': True,
            }
        except Exception:
            self._rollback()
            raise
        after = self.cluster.wal_bytes()
        loaded = self._load(read_only=True)
        return _result(decision, after - before, loaded.admitted_entries)

    def read_amount(self, command_id):
        state = self._load(read_only=True)
        existing = state.commands.get(command_id)
        if existing is None:
            return None
        return existing['amount_u128']

    def close(self):
        if getattr(self, '_conn', None) is not None:
            self._conn.close()
            self._conn = None
        if getattr(self, '_lock', None) is not None:
            self._lock.release()
            self._lock = None

    def _ensure_budget(self):
        row = self._conn.execute("SELECT value FROM meta WHERE key = 'budget'").fetchone()
        encoded = canonical_json(self.budget)
        if row is None:
            self._conn.execute(
                'INSERT INTO meta (key, value) VALUES (%s, %s)',
                ('budget', encoded),
            )
            return
        if row[0] != encoded:
            raise StoreError('JOURNAL_RECORD')

    def _load(self, read_only):
        if read_only:
            self._conn.execute('BEGIN')
            self._conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE READ ONLY')
        try:
            state = empty_state(self.budget)
            rows = self._conn.execute(
                'SELECT command_id, payload_sha256, first_result, outcome, '
                'amount_u128, admitted_bytes, crc FROM command_result',
            ).fetchall()
            for command_id, digest, first_result, outcome, amount, nbytes, crc in rows:
                document = _command_document(
                    command_id, digest, first_result, outcome, amount, int(nbytes),
                )
                if _crc(document) != int(crc):
                    raise StoreError('CHECKSUM_MISMATCH')
                state.commands[command_id] = {
                    'payload_sha256': digest,
                    'first_result': first_result,
                    'outcome': outcome,
                    'amount_u128': amount,
                    'admitted_bytes': int(nbytes),
                }
                state.admitted_entries += 1
                state.admitted_bytes += int(nbytes)
            for slot, command_id in self._conn.execute('SELECT slot, command_id FROM slot_hold'):
                state.slots[slot] = command_id
            for _obs_id, nbytes in self._conn.execute('SELECT observation_id, nbytes FROM observation'):
                state.observation_count += 1
                state.admitted_bytes += int(nbytes)
        except Exception:
            if read_only:
                self._rollback()
            raise
        if read_only:
            self._conn.execute('COMMIT')
        return state

    def _write(self, command, decision):
        if decision.store_command:
            document = _command_document(
                command.command_id,
                payload_sha256(command),
                decision.first_result,
                decision.outcome,
                command.amount_u128,
                decision.nbytes,
            )
            self._conn.execute(
                'INSERT INTO command_result ('
                'command_id, payload_sha256, first_result, outcome, '
                'amount_u128, admitted_bytes, crc) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (
                    command.command_id, document['payloadSha256'], decision.first_result,
                    decision.outcome, command.amount_u128, decision.nbytes, _crc(document),
                ),
            )
        if decision.store_slot:
            self._conn.execute(
                'INSERT INTO slot_hold (slot, command_id) VALUES (%s, %s)',
                (command.slot, command.command_id),
            )
        if decision.store_observation:
            self._conn.execute(
                'INSERT INTO observation (observation_id, nbytes) VALUES (%s, %s)',
                (decision.observation_id, decision.nbytes),
            )

    def _rollback(self):
        try:
            self._conn.execute('ROLLBACK')
        except psycopg.Error:
            pass


class FoundationRecordStore:
    def __init__(self, cluster, directory, lock, prefix, records, committed_bytes):
        self.cluster = cluster
        self.directory = directory
        self._lock = lock
        self.prefix = prefix
        self.records = records
        self.committed_bytes = committed_bytes

    @classmethod
    def open(cls, cluster, directory):
        lock = _Lock(directory)
        prefix = b'kixexp/rec/' + store_key(directory).encode() + b'/'
        try:
            records, committed = _fdb_load_records(cluster, prefix)
        except Exception:
            lock.release()
            raise
        return cls(cluster, directory, lock, prefix, records, committed)

    def append(self, body, fault=None):
        if self._lock is None:
            raise StoreError('JOURNAL_CLOSED')
        if fault == 'crash_before_durable':
            raise ReadinessFault('CRASH_BEFORE_DURABLE')
        record = _stamp(body)
        _validate(record)
        payload = canonical_json(record).encode('utf-8')
        blob = _pack(record)
        seq = len(self.records) + 1
        key = self.prefix + ('%020d' % seq).encode()
        tr = self.cluster.database().transaction()
        try:
            tr.set(key, blob)
            if fault == 'partial':
                raise ReadinessFault('PARTIAL_WRITE')
            tr.commit()
        except ReadinessFault:
            raise
        except FdbError as exc:
            raise StoreError('JOURNAL_RECORD') from exc
        finally:
            tr.close()
        self.records.append(record)
        self.committed_bytes += len(payload)
        return record

    def has_operation(self, operation_id):
        return any(record.get('operationId') == operation_id for record in self.records)

    def can_accept(self, extra, max_records, max_bytes):
        if len(self.records) >= max_records:
            return False
        if self.committed_bytes + extra > max_bytes:
            return False
        return True

    def close(self):
        if self._lock is not None:
            self._lock.release()
            self._lock = None


def _fdb_load_records(cluster, prefix):
    records = []
    committed = 0
    seq = 1
    while True:
        tr = cluster.database().transaction()
        try:
            blob = tr.get(prefix + ('%020d' % seq).encode(), snapshot=True)
        finally:
            tr.close()
        if blob is None:
            return records, committed
        record = _unpack(blob)
        try:
            _validate(record)
        except StoreError as exc:
            raise StoreError('JOURNAL_CORRUPT') from exc
        payload = canonical_json(record).encode('utf-8')
        records.append(record)
        committed += len(payload)
        seq += 1


class FoundationUnit:
    def __init__(self, cluster, directory, budget):
        self.cluster = cluster
        self.directory = directory
        self.budget = dict(budget)
        self.prefix = b'kixexp/unit/' + store_key(directory).encode() + b'/'
        self._lock = _Lock(directory)
        try:
            self._ensure_budget()
        except Exception:
            self.close()
            raise

    def apply(self, command):
        try:
            state = self._load(snapshot=True)
            preview = decide(state, command)
            if not _writes(preview):
                return _result(preview, None, state.admitted_entries)
            tr = self.cluster.database().transaction()
            try:
                state = self._load_tr(tr, snapshot=False)
                decision = decide(state, command)
                if not _writes(decision):
                    return _result(decision, None, state.admitted_entries)
                self._write_tr(tr, state, command, decision)
                tr.commit()
            except FdbError as exc:
                outcome = 'unknown' if _unknown(exc) else 'error'
                return {
                    'outcome': outcome,
                    'first_result': '',
                    'log_delta': None,
                    'admitted_entries': None,
                    'capacity_reason': None,
                    'error': str(exc),
                    'exploration_data': True,
                }
            finally:
                tr.close()
        except FdbError as exc:
            outcome = 'unknown' if _unknown(exc) else 'error'
            return {
                'outcome': outcome,
                'first_result': '',
                'log_delta': None,
                'admitted_entries': None,
                'capacity_reason': None,
                'error': str(exc),
                'exploration_data': True,
            }
        loaded = self._load(snapshot=True)
        return _result(decision, None, loaded.admitted_entries)

    def read_amount(self, command_id):
        state = self._load(snapshot=True)
        existing = state.commands.get(command_id)
        if existing is None:
            return None
        return existing['amount_u128']

    def close(self):
        if getattr(self, '_lock', None) is not None:
            self._lock.release()
            self._lock = None

    def _meta_key(self):
        return self.prefix + b'meta'

    def _ensure_budget(self):
        tr = self.cluster.database().transaction()
        try:
            blob = tr.get(self._meta_key(), snapshot=False)
            if blob is None:
                tr.set(self._meta_key(), _pack({
                    'budget': self.budget,
                    'commands': [],
                    'slots': [],
                    'observations': [],
                }))
                tr.commit()
                return
            meta = _unpack(blob)
            if meta['budget'] != self.budget:
                raise StoreError('JOURNAL_RECORD')
        finally:
            tr.close()

    def _load(self, snapshot):
        tr = self.cluster.database().transaction()
        try:
            return self._load_tr(tr, snapshot)
        finally:
            tr.close()

    def _load_tr(self, tr, snapshot):
        meta = _unpack(tr.get(self._meta_key(), snapshot=snapshot))
        state = empty_state(self.budget)
        for command_id in meta['commands']:
            document = _unpack(tr.get(self.prefix + b'cmd/' + command_id.encode(), snapshot=snapshot))
            state.commands[command_id] = {
                'payload_sha256': document['payloadSha256'],
                'first_result': document['firstResult'],
                'outcome': document['outcome'],
                'amount_u128': document['amountU128'],
                'admitted_bytes': document['admittedBytes'],
            }
            state.admitted_entries += 1
            state.admitted_bytes += document['admittedBytes']
        for slot in meta['slots']:
            document = _unpack(tr.get(self.prefix + b'slot/' + slot.encode(), snapshot=snapshot))
            state.slots[slot] = document['commandId']
        for observation_id in meta['observations']:
            document = _unpack(tr.get(self.prefix + b'obs/' + observation_id.encode(), snapshot=snapshot))
            state.observation_count += 1
            state.admitted_bytes += document['nbytes']
        state.observation_ids = list(meta['observations'])
        return state

    def _write_tr(self, tr, state, command, decision):
        meta = {
            'budget': self.budget,
            'commands': list(state.commands),
            'slots': list(state.slots),
            'observations': list(state.observation_ids),
        }
        if decision.store_command:
            document = _command_document(
                command.command_id,
                payload_sha256(command),
                decision.first_result,
                decision.outcome,
                command.amount_u128,
                decision.nbytes,
            )
            tr.set(self.prefix + b'cmd/' + command.command_id.encode(), _pack(document))
            meta['commands'].append(command.command_id)
        if decision.store_slot:
            tr.set(
                self.prefix + b'slot/' + command.slot.encode(),
                _pack({'commandId': command.command_id}),
            )
            meta['slots'].append(command.slot)
        if decision.store_observation:
            tr.set(
                self.prefix + b'obs/' + decision.observation_id.encode(),
                _pack({'nbytes': decision.nbytes}),
            )
            meta['observations'].append(decision.observation_id)
        tr.set(self._meta_key(), _pack(meta))


def _writes(decision):
    return decision.store_command or decision.store_slot or decision.store_observation


def _unknown(exc):
    text = str(exc).lower()
    return 'commit result unknown' in text or 'commit_unknown_result' in text


class PostgresAdapter:
    fault_error = ReadinessFault

    def __init__(self, cluster):
        self.cluster = cluster

    def open_store(self, directory):
        return PostgresRecordStore.open(self.cluster, directory)

    def open_boundary(self, directory):
        return ExploreBoundary(self.open_store(directory))

    def open_unit(self, directory, budget):
        return PostgresUnit(self.cluster, directory, budget)

    def corrupt_store(self, directory):
        name = 's' + store_key(directory)
        conn = self.cluster.connect()
        try:
            conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(name)))
            updated = conn.execute(
                'UPDATE rec SET crc = crc + 1 WHERE seq = (SELECT MIN(seq) FROM rec)',
            ).rowcount
            if updated != 1:
                raise StoreError('JOURNAL_CORRUPT')
        finally:
            conn.close()


class FoundationAdapter:
    fault_error = ReadinessFault

    def __init__(self, cluster):
        self.cluster = cluster

    def open_store(self, directory):
        return FoundationRecordStore.open(self.cluster, directory)

    def open_boundary(self, directory):
        return ExploreBoundary(self.open_store(directory))

    def open_unit(self, directory, budget):
        return FoundationUnit(self.cluster, directory, budget)

    def corrupt_store(self, directory):
        prefix = b'kixexp/rec/' + store_key(directory).encode() + b'/'
        key = prefix + b'%020d' % 1
        tr = self.cluster.database().transaction()
        try:
            blob = tr.get(key, snapshot=False)
            if blob is None:
                raise StoreError('JOURNAL_CORRUPT')
            flipped = bytearray(blob)
            flipped[0] ^= 0xFF
            tr.set(key, bytes(flipped))
            tr.commit()
        finally:
            tr.close()


def corrupt_probe_body():
    return dict(_CORE_PROBE)

