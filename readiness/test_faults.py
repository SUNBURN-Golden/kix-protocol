"""Fault checks for the local readiness journal.

These tests restart a boundary and probe local locks with offline processes.
They do not claim a
public endpoint, production conformance, bank exactly-once, or chain finality.
Protocol FSM `durable` flags stay false: the journal is not protocol truth.
"""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
import zlib
from collections import Counter
from pathlib import Path
from queue import Empty, Queue

from readiness.boundary import FsmBoundary, ReadinessClosed, ReadinessError
from readiness.ai_delegation_wrap import WrapError as AiDelegationWrapError
from ai_delegation_mock import AiDelegationError
from token_reward_model import PROVENANCE, TokenRewardError
from readiness.codec import CodecError, canonical_json, receipt_digest, strict_loads
from readiness.migrate import SCHEMA_VERSION, MigrationError, migrate, migrate_explicit
from readiness.policy import AdmitGate
from readiness.reward_wrap import RewardWrap, WrapError as RewardWrapError
from readiness.store import (
    HEADER_LEN, JOURNAL_NAME, MAX_RECORD_BYTES, ReadinessFault, ReadinessStore, StoreError,
)

from readiness.conformance import (
    BackendConformance,
    ai_delegation_issue,
    committed_face,
    reward_mark_eligible as _eligible_reward,
    reward_observe as _observe_reward,
    reward_opening as _reward_opening,
    reward_rid as _reward_rid,
)
from readiness.local_adapter import LocalReadinessAdapter
from readiness.test_conformance_sensitivity import ConformanceSensitivityTests


class StoreTests(unittest.TestCase):
    def test_version_one_roundtrip_and_explicit_migration_only(self):
        self.assertEqual(migrate(1, [{'schema': 1}]), [{'schema': 1}])
        with self.assertRaises(MigrationError) as raised:
            migrate(2, [])
        self.assertEqual(raised.exception.code, 'UNSUPPORTED_SCHEMA')
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            try:
                stored = store.append({
                    'kind': 'fsm_commit',
                    'machine': 'settlement',
                    'entry': {'op': 'initiate', 'idempotency_key': 'init-1'},
                })
                self.assertIs(stored['protocolTruth'], False)
                self.assertIs(stored['productionConformance'], False)
            finally:
                store.close()
            again = ReadinessStore.open(tmp)
            try:
                self.assertEqual(len(again.records), 1)
                self.assertEqual(again.records[0]['entry']['idempotency_key'], 'init-1')
                with self.assertRaises(StoreError) as locked:
                    ReadinessStore.open(tmp)
                self.assertEqual(locked.exception.code, 'JOURNAL_LOCKED')
            finally:
                again.close()

    def test_torn_tail_is_discarded_and_a_bad_checksum_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            try:
                store.append({
                    'kind': 'fsm_commit',
                    'machine': 'reservation',
                    'entry': {'op': 'hold', 'idempotency_key': 'hold-1'},
                })
                with self.assertRaises(ReadinessFault) as partial:
                    store.append({
                        'kind': 'fsm_commit',
                        'machine': 'reservation',
                        'entry': {'op': 'hold', 'idempotency_key': 'hold-2'},
                    }, fault='partial')
                self.assertEqual(partial.exception.code, 'PARTIAL_WRITE')
                with self.assertRaises(StoreError) as torn:
                    store.append({
                        'kind': 'fsm_commit',
                        'machine': 'reservation',
                        'entry': {'op': 'hold', 'idempotency_key': 'hold-3'},
                    })
                self.assertEqual(torn.exception.code, 'JOURNAL_TORN')
            finally:
                store.close()
            recovered = ReadinessStore.open(tmp)
            try:
                self.assertEqual(
                    [record['entry']['idempotency_key'] for record in recovered.records],
                    ['hold-1'],
                )
            finally:
                recovered.close()
            path = Path(tmp) / JOURNAL_NAME
            data = bytearray(path.read_bytes())
            data[20] ^= 0xFF
            path.write_bytes(data)
            with self.assertRaises(StoreError) as checksum:
                ReadinessStore.open(tmp)
            self.assertEqual(checksum.exception.code, 'CHECKSUM_MISMATCH')

    def test_unknown_schema_is_refused_without_a_guess(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            store.close()
            path = Path(tmp) / JOURNAL_NAME
            data = bytearray(path.read_bytes())
            struct.pack_into('>I', data, 8, 99)
            path.write_bytes(data)
            with self.assertRaises(StoreError) as raised:
                ReadinessStore.open(tmp)
            self.assertEqual(raised.exception.code, 'UNSUPPORTED_SCHEMA')

    def test_protocol_truth_label_cannot_be_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            try:
                with self.assertRaises(StoreError) as raised:
                    store.append({
                        'kind': 'fsm_commit',
                        'machine': 'settlement',
                        'entry': {},
                        'protocolTruth': True,
                    })
                self.assertEqual(raised.exception.code, 'JOURNAL_RECORD')
            finally:
                store.close()


class RecordSizeBoundaryTests(unittest.TestCase):
    """Class B: source-informed local size-limit characterization, not policy."""

    def _expected_payload(self, body):
        # Explicit stamp and stdlib oracle: do not derive expected bytes from
        # the store's stamping, parsing or canonical_json helpers.
        expected = {
            'schema': SCHEMA_VERSION,
            'protocolTruth': False,
            'productionConformance': False,
            **body,
        }
        payload = json.dumps(
            expected, ensure_ascii=False, sort_keys=True,
            separators=(',', ':'), allow_nan=False,
        ).encode('utf-8')
        return expected, payload

    def _body_for_payload_bytes(self, target, token):
        body = {
            'kind': 'fsm_commit',
            'machine': 'settlement',
            'entry': {'text': ''},
        }
        _, empty_payload = self._expected_payload(body)
        remaining = target - len(empty_payload)
        self.assertGreaterEqual(remaining, 0)
        repeats, remainder = divmod(remaining, len(token.encode('utf-8')))
        body['entry']['text'] = token * repeats + 'a' * remainder
        _, payload = self._expected_payload(body)
        self.assertEqual(len(payload), target)
        if token == '가🙂':
            self.assertEqual((len(token), len(token.encode('utf-8'))), (2, 7))
            self.assertLess(len(payload.decode('utf-8')), len(payload))
        return body

    def test_ascii_and_utf8_record_size_boundaries_roundtrip(self):
        for token in ('a', '가🙂'):
            for size in (MAX_RECORD_BYTES - 1, MAX_RECORD_BYTES):
                with self.subTest(token=token, payload_bytes=size), tempfile.TemporaryDirectory() as tmp:
                    body = self._body_for_payload_bytes(size, token)
                    expected, payload = self._expected_payload(body)
                    store = ReadinessStore.open(tmp)
                    path = Path(tmp) / JOURNAL_NAME
                    committed = HEADER_LEN + 4 + size + 4
                    try:
                        self.assertEqual(store.append(body), expected)
                        self.assertEqual(store.records, [expected])
                        self.assertEqual(store.committed_bytes, committed)
                        data = path.read_bytes()
                        self.assertEqual(len(data), committed)
                        self.assertEqual(struct.unpack_from('>I', data, HEADER_LEN)[0], size)
                        self.assertEqual(data[HEADER_LEN + 4:-4], payload)
                        self.assertEqual(
                            struct.unpack_from('>I', data, len(data) - 4)[0],
                            zlib.crc32(payload) & 0xFFFFFFFF,
                        )
                    finally:
                        store.close()
                    again = ReadinessStore.open(tmp)
                    try:
                        self.assertEqual(again.records, [expected])
                        self.assertEqual(again.committed_bytes, committed)
                        self.assertEqual(path.read_bytes(), data)
                    finally:
                        again.close()

    def test_oversized_record_rejection_is_atomic_and_store_reusable(self):
        for token in ('a', '가🙂'):
            with self.subTest(token=token), tempfile.TemporaryDirectory() as tmp:
                prefix_body = {
                    'kind': 'fsm_commit', 'machine': 'settlement',
                    'entry': {'text': 'accepted prefix'},
                }
                prefix, prefix_payload = self._expected_payload(prefix_body)
                oversized = self._body_for_payload_bytes(MAX_RECORD_BYTES + 1, token)
                _, oversized_payload = self._expected_payload(oversized)
                if token == '가🙂':
                    # A character-count admission check would accept this body.
                    self.assertLess(len(oversized_payload.decode('utf-8')), MAX_RECORD_BYTES)
                valid = self._body_for_payload_bytes(MAX_RECORD_BYTES, token)
                expected, payload = self._expected_payload(valid)
                store = ReadinessStore.open(tmp)
                path = Path(tmp) / JOURNAL_NAME
                committed = HEADER_LEN + 4 + len(prefix_payload) + 4 + 4 + len(payload) + 4
                try:
                    self.assertEqual(store.append(prefix_body), prefix)
                    before_bytes = path.read_bytes()
                    before_records = json_copy(store.records)
                    before_committed = store.committed_bytes
                    with self.assertRaises(StoreError) as raised:
                        store.append(oversized)
                    self.assertEqual(raised.exception.code, 'RECORD_TOO_LARGE')
                    self.assertEqual(path.read_bytes(), before_bytes)
                    self.assertEqual(store.records, before_records)
                    self.assertEqual(store.committed_bytes, before_committed)

                    # Reuse this handle before reopening: rejection must not fence it.
                    self.assertEqual(store.append(valid), expected)
                    self.assertEqual(store.records, [prefix, expected])
                    self.assertEqual(store.committed_bytes, committed)
                    data = path.read_bytes()
                    self.assertEqual(len(data), committed)
                    frame = struct.pack('>I', len(payload)) + payload
                    frame += struct.pack('>I', zlib.crc32(payload) & 0xFFFFFFFF)
                    self.assertEqual(data, before_bytes + frame)
                finally:
                    store.close()
                again = ReadinessStore.open(tmp)
                try:
                    self.assertEqual(again.records, [prefix, expected])
                    self.assertEqual(again.committed_bytes, committed)
                    self.assertEqual(path.read_bytes(), data)
                finally:
                    again.close()


class JsonCodecRegressionTests(unittest.TestCase):
    """Source-informed local codec characterization, not protocol encoding."""

    def _payload(self, entry):
        # Construct bytes directly so malformed JSON and duplicate keys survive.
        return (
            b'{"schema":1,"protocolTruth":false,"productionConformance":false,'
            b'"kind":"fsm_commit","machine":"settlement","entry":' + entry + b'}'
        )

    def _frame(self, payload):
        self.assertGreaterEqual(len(payload), 2)
        self.assertLessEqual(len(payload), MAX_RECORD_BYTES)
        frame = struct.pack('>I', len(payload)) + payload
        frame += struct.pack('>I', zlib.crc32(payload) & 0xFFFFFFFF)
        self.assertEqual(len(frame), len(payload) + 8)
        return frame

    def test_complete_frames_reject_invalid_json_without_rewriting(self):
        valid = self._payload(b'{"value":1}')
        cases = {
            'bom': b'\xef\xbb\xbf' + valid,
            'nested-duplicate': self._payload(b'{"nested":{"key":1,"key":2}}'),
            'array-object-duplicate': self._payload(b'{"items":[{"key":1,"key":2}]}'),
            'nan': self._payload(b'{"value":NaN}'),
            'infinity': self._payload(b'{"value":Infinity}'),
            'negative-infinity': self._payload(b'{"value":-Infinity}'),
            'missing-value': self._payload(b'{"value":}'),
            'trailing-comma': self._payload(b'{"value":1,}'),
            'unterminated-string': self._payload(b'{"value":"unfinished'),
            'trailing-text': valid + b' unexpected',
        }
        with tempfile.TemporaryDirectory() as seed:
            store = ReadinessStore.open(seed)
            try:
                store.append({'kind': 'fsm_commit', 'machine': 'settlement',
                              'entry': {'text': 'accepted prefix'}})
                prefix_end = store.committed_bytes
                store.append({'kind': 'fsm_commit', 'machine': 'settlement',
                              'entry': {'text': 'accepted suffix'}})
            finally:
                store.close()
            original = (Path(seed) / JOURNAL_NAME).read_bytes()
        self.assertGreater(prefix_end, HEADER_LEN)
        prefix, suffix = original[:prefix_end], original[prefix_end:]
        self.assertTrue(suffix)
        for name, payload in cases.items():
            with self.subTest(case=name, entry_point='strict_loads'):
                with self.assertRaises(CodecError) as raised:
                    strict_loads(payload)
                self.assertEqual(raised.exception.code, 'JOURNAL_CORRUPT')
            frame = self._frame(payload)
            for later in (b'', suffix):
                with self.subTest(case=name, before_suffix=bool(later)), tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / JOURNAL_NAME
                    before = prefix + frame + later
                    path.write_bytes(before)
                    with self.assertRaises(StoreError) as raised:
                        # Close an unexpected handle before assertRaises fails.
                        ReadinessStore.open(tmp).close()
                    self.assertEqual(raised.exception.code, 'JOURNAL_CORRUPT')
                    self.assertEqual(path.read_bytes(), before)

    def test_valid_json_controls_roundtrip(self):
        cases = [
            (b'{"text":"\xc3\xa9\xea\xb0\x80\xf0\x9f\x99\x82"}', {'text': 'é가🙂'}),
            (b'{"values":[0,7,-3,1.25,1e2]}', {'values': [0, 7, -3, 1.25, 100.0]}),
            (b'{"nested":{"a":1,"b":2},"items":[{"a":3},{"a":4}]}',
             {'nested': {'a': 1, 'b': 2}, 'items': [{'a': 3}, {'a': 4}]}),
            (b'{"names":["NaN","Infinity","-Infinity"]}',
             {'names': ['NaN', 'Infinity', '-Infinity']}),
        ]
        for entry_bytes, entry in cases:
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as tmp:
                expected = {
                    'schema': SCHEMA_VERSION, 'protocolTruth': False,
                    'productionConformance': False, 'kind': 'fsm_commit',
                    'machine': 'settlement', 'entry': entry,
                }
                payload = self._payload(entry_bytes)
                self.assertEqual(strict_loads(payload), expected)
                store = ReadinessStore.open(tmp)
                store.close()
                path = Path(tmp) / JOURNAL_NAME
                data = path.read_bytes() + self._frame(payload)
                path.write_bytes(data)
                store = ReadinessStore.open(tmp)
                try:
                    self.assertEqual(store.records, [expected])
                    self.assertEqual(store.committed_bytes, len(data))
                    self.assertEqual(path.read_bytes(), data)
                    self.assertEqual(store.append({
                        'kind': 'fsm_commit', 'machine': 'settlement', 'entry': entry,
                    }), expected)
                    committed = store.committed_bytes
                    appended = path.read_bytes()
                finally:
                    store.close()
                again = ReadinessStore.open(tmp)
                try:
                    self.assertEqual(again.records, [expected, expected])
                    self.assertEqual(again.committed_bytes, committed)
                    self.assertEqual(path.read_bytes(), appended)
                finally:
                    again.close()

    def test_serialization_failures_report_journal_record(self):
        circular = []
        circular.append(circular)
        cases = {
            'nan': float('nan'), 'infinity': float('inf'),
            'negative-infinity': -float('inf'), 'set': {1}, 'circular': circular,
        }
        for name, value in cases.items():
            entry = {'nested': [{'value': value}]}
            for encode in (canonical_json, receipt_digest):
                with self.subTest(case=name, encoder=encode.__name__):
                    with self.assertRaises(CodecError) as raised:
                        encode(entry)
                    self.assertEqual(raised.exception.code, 'JOURNAL_RECORD')
            with self.subTest(case=name, entry_point='append'), tempfile.TemporaryDirectory() as tmp:
                body = {'kind': 'fsm_commit', 'machine': 'settlement',
                        'entry': {'text': 'accepted'}}
                store = ReadinessStore.open(tmp)
                path = Path(tmp) / JOURNAL_NAME
                try:
                    expected = json_copy(store.append(body))
                    before = path.read_bytes()
                    records = json_copy(store.records)
                    committed = store.committed_bytes
                    # append currently propagates CodecError, not StoreError.
                    with self.assertRaises(CodecError) as raised:
                        store.append({**body, 'entry': entry})
                    self.assertEqual(raised.exception.code, 'JOURNAL_RECORD')
                    self.assertEqual(path.read_bytes(), before)
                    self.assertEqual(store.records, records)
                    self.assertEqual(store.committed_bytes, committed)
                    self.assertEqual(store.append(body), expected)
                    after = path.read_bytes()
                    self.assertEqual(store.records, [expected, expected])
                    self.assertEqual(store.committed_bytes, len(after))
                finally:
                    store.close()
                again = ReadinessStore.open(tmp)
                try:
                    self.assertEqual(again.records, [expected, expected])
                    self.assertEqual(again.committed_bytes, len(after))
                    self.assertEqual(path.read_bytes(), after)
                finally:
                    again.close()

    def test_canonical_unicode_bytes_and_receipt_digests(self):
        receipt = {'z': [True, None, 7], 'a': {'text': '가🙂', 'accent': 'é'}}
        expected = b'{"a":{"accent":"\xc3\xa9","text":"\xea\xb0\x80\xf0\x9f\x99\x82"},"z":[true,null,7]}'
        # Hash literal UTF-8 bytes independently, never the encoder's output.
        digest = hashlib.sha256(expected).hexdigest()
        self.assertEqual(canonical_json(receipt).encode('utf-8'), expected)
        self.assertEqual(strict_loads(expected), receipt)
        self.assertEqual(receipt_digest(receipt), digest)
        reordered = {'a': {'accent': 'é', 'text': '가🙂'}, 'z': [True, None, 7]}
        self.assertNotEqual(list(receipt), list(reordered))
        self.assertNotEqual(list(receipt['a']), list(reordered['a']))
        self.assertEqual(canonical_json(reordered).encode('utf-8'), expected)
        self.assertEqual(receipt_digest(reordered), digest)
        changed = {'a': {'accent': 'é', 'text': '가🙂'}, 'z': [True, None, 8]}
        changed_bytes = b'{"a":{"accent":"\xc3\xa9","text":"\xea\xb0\x80\xf0\x9f\x99\x82"},"z":[true,null,8]}'
        changed_digest = hashlib.sha256(changed_bytes).hexdigest()
        self.assertEqual(canonical_json(changed).encode('utf-8'), changed_bytes)
        self.assertEqual(strict_loads(changed_bytes), changed)
        self.assertEqual(receipt_digest(changed), changed_digest)
        self.assertNotEqual(changed_digest, digest)


# The competing opener has no append path. Fresh interpreters and close_fds
# ensure a child cannot inherit its parent's journal ownership.
_WRITER_LOCK_PROBE = r'''
import json
import sys
from readiness.boundary import FsmBoundary
from readiness.store import ReadinessStore

directory, mode = sys.argv[1:]

def emit(phase, **fields):
    print(json.dumps(dict(phase=phase, **fields)), flush=True)

def receive(phase):
    message = json.loads(sys.stdin.readline())
    assert message == {'phase': phase}, message

def identity(exc):
    return dict(error_type=type(exc).__name__, code=getattr(exc, 'code', None))

retained = None
try:
    handle = FsmBoundary(directory) if mode == 'boundary' else ReadinessStore.open(directory)
except Exception as exc:
    # Retain both: neither traceback disposal nor process exit may release a
    # leaked initialization handle before the parent's independent probe.
    retained = (exc, exc.__traceback__)
    emit('failed', **identity(exc))
else:
    handle.close()
    emit('unexpected_success')

if mode == 'owned':
    receive('reopen')
    store = ReadinessStore.open(directory)
    try:
        records, committed_bytes = store.records, store.committed_bytes
    finally:
        store.close()
    emit('reopened', records=records, committed_bytes=committed_bytes)
else:
    receive('finish')
    assert retained is not None
    exc, traceback = retained
    emit('retained', **identity(exc),
         traceback_retained=traceback is not None and exc.__traceback__ is traceback)
'''


class _WriterLockProcess:
    """Bounded blocking pipe/wait handshakes; no sleeps, polling or retries."""

    TIMEOUT = 30  # Harness deadlock guard, not a product timeout or SLO.

    def __init__(self, test, directory, mode):
        self.test = test
        self.messages = Queue()
        self.exits = Queue()
        self.threads = []
        self.process = subprocess.Popen(
            [sys.executable, '-u', '-c', _WRITER_LOCK_PROBE, str(directory), mode],
            cwd=Path(__file__).resolve().parents[1], close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True,
        )
        test.addCleanup(self.close)
        for target in (self._read, self._wait):
            thread = threading.Thread(target=target)
            self.threads.append(thread)
            thread.start()

    def _read(self):
        try:
            for line in self.process.stdout:
                self.messages.put(line)
        finally:
            self.messages.put(None)

    def _wait(self):
        self.exits.put(self.process.wait())

    def expect(self, message):
        line = self.messages.get(timeout=self.TIMEOUT)
        self.test.assertIsNotNone(line, 'probe closed stdout before handshake')
        self.test.assertEqual(json.loads(line), message)

    def send(self, phase):
        self.process.stdin.write(json.dumps({'phase': phase}) + '\n')
        self.process.stdin.flush()

    def finish(self):
        self.test.assertEqual(self.exits.get(timeout=self.TIMEOUT), 0)
        self.test.assertIsNone(self.messages.get(timeout=self.TIMEOUT),
                               'unexpected trailing probe output')

    def close(self):
        try:
            if self.process.returncode is None:
                self.process.terminate()
                try:
                    self.exits.get(timeout=self.TIMEOUT)
                except Empty:
                    self.process.kill()
                    self.exits.get(timeout=self.TIMEOUT)
                    raise
        finally:
            for thread in self.threads:
                thread.join(timeout=self.TIMEOUT)
            self.process.stdin.close()
            self.process.stdout.close()
        for thread in self.threads:
            self.test.assertFalse(thread.is_alive(), 'probe helper thread did not stop')


class WriterLockLifecycleTests(unittest.TestCase):
    """Local exclusion (class A); cleanup is a source-informed regression (B).

    Explicit-close and failed-init cleanup do not add contract semantics or
    backend-neutral requirements. Only the parent fixture writer appends.
    """

    def setUp(self):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.directory = Path(root.name)
        self.path = self.directory / JOURNAL_NAME

    def _open(self):
        store = ReadinessStore.open(self.directory)
        self.addCleanup(store.close)
        return store

    def _assert_failure(self, child, error_type, code, phase='failed'):
        message = dict(phase=phase, error_type=error_type, code=code)
        if phase == 'retained':
            message['traceback_retained'] = True
        child.expect(message)

    def test_competing_process_refused_then_reopens_after_close(self):
        store = self._open()
        store.append({
            'kind': 'fsm_commit', 'machine': 'settlement',
            'entry': {'op': 'initiate', 'idempotency_key': 'init-1'},
        })
        original = self.path.read_bytes()
        records, committed_bytes = json_copy(store.records), store.committed_bytes
        child = _WriterLockProcess(self, self.directory, 'owned')
        self._assert_failure(child, 'StoreError', 'JOURNAL_LOCKED')
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(store.records, records)
        self.assertEqual(store.committed_bytes, committed_bytes)
        # Implementation regression: explicit close permits the next opener.
        store.close()
        child.send('reopen')  # Ordered lifecycle transition, not a failure retry.
        child.expect(dict(phase='reopened', records=records, committed_bytes=committed_bytes))
        child.finish()
        self.assertEqual(self.path.read_bytes(), original)

    def test_store_open_failure_releases_lock_while_process_alive(self):
        store = self._open()
        # Same complete-frame corruption as StoreTests' checksum fixture.
        store.append({
            'kind': 'fsm_commit', 'machine': 'reservation',
            'entry': {'op': 'hold', 'idempotency_key': 'hold-1'},
        })
        store.close()
        damaged = bytearray(self.path.read_bytes())
        damaged[20] ^= 0xFF
        self.path.write_bytes(damaged)
        original = self.path.read_bytes()
        child = _WriterLockProcess(self, self.directory, 'store')
        self._assert_failure(child, 'StoreError', 'CHECKSUM_MISMATCH')
        # Implementation regression: lock acquisition precedes checksum parsing.
        # Use _open so even unexpected success registers immediate cleanup.
        with self.assertRaises(StoreError) as raised:
            self._open()
        self.assertIs(type(raised.exception), StoreError)
        self.assertEqual(raised.exception.code, 'CHECKSUM_MISMATCH')
        self.assertEqual(self.path.read_bytes(), original)
        child.send('finish')
        self._assert_failure(child, 'StoreError', 'CHECKSUM_MISMATCH', 'retained')
        child.finish()
        self.assertEqual(self.path.read_bytes(), original)

    def test_boundary_init_failure_releases_lock_while_process_alive(self):
        store = self._open()
        # Same valid core_commit as FaultTests' invalid-for-FSM fixture.
        store.append({
            'kind': 'core_commit', 'machine': 'integration_core',
            'operationId': 'op-1', 'actor': 'operator', 'action': 'advance_clock',
            'body': {'domain': 'kix:fixture:lifecycle:0.3', 'now': 1},
            'receiptDigest': 'cd' * 32,
        })
        records, committed_bytes = json_copy(store.records), store.committed_bytes
        store.close()
        original = self.path.read_bytes()
        child = _WriterLockProcess(self, self.directory, 'boundary')
        self._assert_failure(child, 'ReadinessError', 'UNEXPECTED_RECORD')
        # Implementation regression: a store can open while failed init lives.
        reopened = self._open()
        self.assertEqual(reopened.records, records)
        self.assertEqual(reopened.committed_bytes, committed_bytes)
        self.assertEqual(self.path.read_bytes(), original)
        reopened.close()
        child.send('finish')
        self._assert_failure(child, 'ReadinessError', 'UNEXPECTED_RECORD', 'retained')
        child.finish()
        self.assertEqual(self.path.read_bytes(), original)


class MigrationEdgeTests(unittest.TestCase):
    @staticmethod
    def _record(schema, item_id='fixture-1'):
        record = {
            'schema': schema,
            'kind': 'fsm_commit',
            'machine': 'settlement',
            'protocolTruth': False,
            'productionConformance': False,
            'entry': {'op': 'initiate', 'details': {'items': [{'id': item_id}]}},
            'fixtureNote': {'nested': [{'values': [None, False, 7, 'kept']}]},
        }
        if schema == 2:
            record['productionReadiness'] = False
            record['productionEndpoint'] = False
        return record

    def _assert_unsupported_without_mutation(self, source_version, records):
        original = json_copy(records)
        with self.assertRaises(MigrationError) as raised:
            migrate_explicit(source_version, 2, records)
        self.assertEqual(raised.exception.code, 'UNSUPPORTED_SCHEMA')
        self.assertEqual(records, original)

    def test_missing_identity_fields_are_not_invented(self):
        """READINESS_RUNTIME.md / 버전 이전: missing kind/machine is unsupported.

        Gap: the existing fixture removes both together; neither individual
        omission nor the independent 2-to-2 input was exercised.
        """
        for version in (1, 2):
            for field in ('kind', 'machine'):
                with self.subTest(route=(version, 2), field=field, value='missing'):
                    record = self._record(version)
                    del record[field]
                    self._assert_unsupported_without_mutation(version, [record])

    def test_required_false_labels_are_not_invented_or_coerced(self):
        """READINESS_RUNTIME.md / 버전 이전: required false labels are not filled.

        Gap: protocolTruth/productionConformance were always present and false;
        missing schema-2 production labels and coercion were not tested.
        """
        for version in (1, 2):
            for field in ('protocolTruth', 'productionConformance'):
                with self.subTest(route=(version, 2), field=field, value='missing'):
                    record = self._record(version)
                    del record[field]
                    self._assert_unsupported_without_mutation(version, [record])
                for value in (True, None, 0, 'false'):
                    with self.subTest(route=(version, 2), field=field, value=value):
                        record = self._record(version)
                        record[field] = value
                        self._assert_unsupported_without_mutation(version, [record])
        for field in ('productionReadiness', 'productionEndpoint'):
            with self.subTest(route=(2, 2), field=field, value='missing'):
                record = self._record(2)
                del record[field]
                self._assert_unsupported_without_mutation(2, [record])

    def test_production_labels_reject_contradictions(self):
        """READINESS_RUNTIME.md / 버전 이전: stamp only absent keys; never coerce.

        Gap: only productionReadiness=True on 1-to-2 was rejected; endpoint,
        other non-false values, 2-to-2 and pre-existing false labels were absent.
        """
        fields = ('productionReadiness', 'productionEndpoint')
        for present in ((), fields[:1], fields[1:], fields):
            with self.subTest(route=(1, 2), present=present):
                records = [self._record(1)]
                for field in present:
                    records[0][field] = False
                original = json_copy(records)
                result = migrate_explicit(1, 2, records)
                self.assertEqual(records, original)
                for field in fields:
                    self.assertIs(result[0][field], False)
        for version in (1, 2):
            for field in fields:
                for value in (True, None, 0, 'false'):
                    with self.subTest(route=(version, 2), field=field, value=value):
                        record = self._record(version)
                        record[field] = value
                        self._assert_unsupported_without_mutation(version, [record])

    def test_invalid_batch_suffix_preserves_all_inputs(self):
        """READINESS_RUNTIME.md / 버전 이전: copy records; unsupported stays closed.

        Gap: malformed suffixes after valid records were untested, including
        whether a failed 1-to-2 or 2-to-2 batch mutates any source record.
        """
        for version in (1, 2):
            for position in (1, 2):
                for malformed in ('non-record', 'wrong-schema', 'missing-field',
                                  'contradictory-label'):
                    with self.subTest(route=(version, 2), position=position,
                                      malformed=malformed):
                        records = [self._record(version, 'valid-%d' % i)
                                   for i in range(position)]
                        bad = self._record(version, 'invalid')
                        if malformed == 'non-record':
                            bad = None
                        elif malformed == 'wrong-schema':
                            bad['schema'] = 2 if version == 1 else 1
                        elif malformed == 'missing-field':
                            del bad['machine']
                        else:
                            bad['productionEndpoint'] = True
                        records.append(bad)
                        self._assert_unsupported_without_mutation(version, records)

    def test_nested_unknown_fields_survive_explicit_migration(self):
        """READINESS_RUNTIME.md / 버전 이전: whole-record copy, unknown keys kept.

        Gap: one shallow fixtureNote and an upgrade-derived 2-to-2 input did
        not assert complete nested values, record count/order or both sources.
        """
        for version in (1, 2):
            with self.subTest(route=(version, 2)):
                records = [self._record(version, 'fixture-%d' % i) for i in range(3)]
                records[1]['productionReadiness'] = False
                records[2]['productionEndpoint'] = False
                original = json_copy(records)
                expected = json_copy(records)
                if version == 1:
                    for record in expected:
                        record['schema'] = 2
                        record['productionReadiness'] = False
                        record['productionEndpoint'] = False
                result = migrate_explicit(version, 2, records)
                self.assertEqual(result, expected)
                self.assertEqual(records, original)
                for record in result:
                    for field in ('protocolTruth', 'productionConformance',
                                  'productionReadiness', 'productionEndpoint'):
                        self.assertIs(record[field], False)

    def test_returned_nested_copies_are_isolated(self):
        """READINESS_RUNTIME.md / 버전 이전: both explicit routes return copies.

        Gap: equality checks never mutated a returned nested dictionary/list,
        so shared entry or unknown-field containers could go undetected.
        """
        for version in (1, 2):
            with self.subTest(route=(version, 2)):
                records = [self._record(version, 'fixture-%d' % i) for i in range(2)]
                original = json_copy(records)
                result = migrate_explicit(version, 2, records)
                self.assertEqual(records, original)
                self.assertIsNot(result, records)
                for source, copied in zip(records, result):
                    self.assertIsNot(copied, source)
                    copied['entry']['details']['items'][0]['id'] = 'changed'
                    copied['entry']['details']['items'].append({'id': 'new'})
                    copied['entry']['details']['added'] = {'nested': []}
                    copied['fixtureNote']['nested'][0]['values'].append('new')
                    copied['fixtureNote']['nested'][0]['added'] = True
                    copied['fixtureNote']['nested'].append({'new': []})
                result.append(self._record(2, 'returned-only'))
                self.assertEqual(records, original)


class ExtensionTests(unittest.TestCase):
    def test_explicit_v2_migration_does_not_run_on_open_or_guess_fields(self):
        source = {
            'schema': 1,
            'protocolTruth': False,
            'productionConformance': False,
            'kind': 'fsm_commit',
            'machine': 'settlement',
            'entry': {'op': 'initiate'},
            'fixtureNote': {'kept': True},
        }
        original = json_copy(source)
        upgraded = migrate_explicit(1, 2, [source])
        self.assertEqual(source, original)
        self.assertEqual(upgraded[0]['schema'], 2)
        self.assertEqual(upgraded[0]['fixtureNote'], {'kept': True})
        self.assertIs(upgraded[0]['productionReadiness'], False)
        self.assertIs(upgraded[0]['productionEndpoint'], False)
        self.assertEqual(migrate_explicit(2, 2, upgraded), upgraded)
        self.assertEqual(migrate(1, [source]), [source])
        with self.assertRaises(MigrationError) as downgrade:
            migrate_explicit(2, 1, upgraded)
        self.assertEqual(downgrade.exception.code, 'UNSUPPORTED_SCHEMA')
        with self.assertRaises(MigrationError) as guessed:
            migrate_explicit(1, 2, [{'schema': 1, 'protocolTruth': False, 'productionConformance': False}])
        self.assertEqual(guessed.exception.code, 'UNSUPPORTED_SCHEMA')
        with self.assertRaises(MigrationError) as coerced:
            migrate_explicit(1, 2, [dict(source, productionReadiness=True)])
        self.assertEqual(coerced.exception.code, 'UNSUPPORTED_SCHEMA')
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            try:
                stored = store.append({
                    'kind': 'fsm_commit',
                    'machine': 'settlement',
                    'entry': {'op': 'initiate'},
                })
                self.assertEqual(stored['schema'], SCHEMA_VERSION)
                self.assertNotIn('productionReadiness', stored)
            finally:
                store.close()
            reopened = ReadinessStore.open(tmp)
            try:
                self.assertEqual(reopened.records[0]['schema'], 1)
                self.assertNotIn('productionEndpoint', reopened.records[0])
            finally:
                reopened.close()

    def test_budget_names_the_existing_limit_and_overload_does_not_queue(self):
        gate = AdmitGate(1)
        self.assertEqual(gate.try_admit(), 'OK')
        self.assertEqual(gate.try_admit(), 'OVERLOADED')
        self.assertEqual(gate.view(), {'inFlight': 1, 'maxInFlight': 1, 'queued': 0})
        gate.release()
        self.assertEqual(gate.try_admit(), 'OK')
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            try:
                code, limit = store.budget_decision(1, 1, store.committed_bytes)
                self.assertEqual((code, limit), ('JOURNAL_BUDGET', 'bytes'))
                self.assertEqual(store.records, [])
                store.append({
                    'kind': 'fsm_commit',
                    'machine': 'credit',
                    'entry': {'op': 'offer'},
                })
                code, limit = store.budget_decision(0, 1, store.committed_bytes + 10)
                self.assertEqual((code, limit), ('JOURNAL_BUDGET', 'records'))
                self.assertEqual(len(store.records), 1)
            finally:
                store.close()

    def test_ai_delegation_torn_revoke_replays_once_and_execution_stays_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = FsmBoundary(tmp)
            try:
                boundary.call('ai_delegation', lambda machine: machine.open_registry(['human-issuer'], ['agent-1']))
                issued = boundary.call('ai_delegation', lambda machine: _issue(machine))
                self.assertFalse(issued['duplicate'])
                self.assertIs(issued['grant']['durable'], False)
                self.assertIs(issued['grant']['execution_enabled'], False)
                queried = boundary.call(
                    'ai_delegation',
                    lambda machine: machine.call_tool('agent-1', 'g1', 'query_grant', {}, 10),
                )
                self.assertFalse(queried['duplicate'])
                self.assertEqual(boundary.last_observation['journalDecision'], 'unchanged')
                self.assertNotIn('entry', boundary.last_observation)
                self.assertNotIn('body', boundary.last_observation)
                self.assertIs(boundary.last_observation['fsmDurable'], False)
                self.assertIs(boundary.last_observation['productionReadiness'], False)
                with self.assertRaises(ReadinessFault):
                    boundary.call(
                        'ai_delegation',
                        lambda machine: machine.revoke_grant('human-issuer', 'g1', 'fixture-reason'),
                        fault='partial',
                    )
                self.assertEqual(boundary.last_observation['journalDecision'], 'fault')
                self.assertEqual(boundary.last_observation['faultCode'], 'PARTIAL_WRITE')
                self.assertNotIn('entry', boundary.last_observation)
            finally:
                boundary.close()
            recovered = FsmBoundary(tmp)
            try:
                self.assertEqual(recovered.machine('ai_delegation').view_grant('g1')['phase'], 'ACTIVE')
                self.assertIs(recovered.machine('ai_delegation').view_grant('g1')['durable'], False)
                revoked = recovered.call(
                    'ai_delegation',
                    lambda machine: machine.revoke_grant('human-issuer', 'g1', 'fixture-reason'),
                )
                self.assertFalse(revoked['duplicate'])
                self.assertEqual(revoked['grant']['phase'], 'REVOKED')
                self.assertIs(revoked['grant']['durable'], False)
                self.assertIs(revoked['grant']['execution_enabled'], False)
                replay = recovered.call(
                    'ai_delegation',
                    lambda machine: machine.revoke_grant('human-issuer', 'g1', 'fixture-reason'),
                )
                self.assertTrue(replay['duplicate'])
                with self.assertRaises(AiDelegationError) as execution:
                    recovered.machine('ai_delegation').attempt_execution('human-issuer', 'p1')
                self.assertEqual(execution.exception.code, 'DELEGATED_EXECUTION_DISABLED')
            finally:
                recovered.close()

    def test_ai_delegation_crash_before_issue_does_not_create_the_grant(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = FsmBoundary(tmp)
            try:
                boundary.call('ai_delegation', lambda machine: machine.open_registry(['human-issuer'], ['agent-1']))
                observed = boundary.last_observation
                self.assertEqual(observed['journalDecision'], 'appended')
                self.assertEqual(observed['schemaVersion'], SCHEMA_VERSION)
                self.assertNotIn('args', observed)
                with self.assertRaises(ReadinessFault) as raised:
                    boundary.call('ai_delegation', lambda machine: _issue(machine), fault='crash_before_durable')
                self.assertEqual(raised.exception.code, 'CRASH_BEFORE_DURABLE')
            finally:
                boundary.close()
            recovered = FsmBoundary(tmp)
            try:
                with self.assertRaises(Exception) as missing:
                    recovered.machine('ai_delegation').view_grant('g1')
                self.assertEqual(missing.exception.code, 'UNKNOWN_GRANT')
                issued = recovered.call('ai_delegation', lambda machine: _issue(machine))
                self.assertFalse(issued['duplicate'])
                self.assertIs(issued['grant']['durable'], False)
                replay = recovered.call('ai_delegation', lambda machine: _issue(machine))
                self.assertTrue(replay['duplicate'])
                self.assertEqual(
                    [entry['op'] for entry in recovered.machine('ai_delegation').export_journal()],
                    ['open_registry', 'issue_grant'],
                )
            finally:
                recovered.close()


REWARD_DIGEST = 'ab' * 32
REWARD_EFFECTS = 'ef' * 32


def _reward_approval():
    return {
        'record_id': 'approval-1',
        'generation': 1,
        'authority_id': 'authority-slot',
        'actor_type': 'HUMAN',
        'action': 'point-payout',
        'scope_ref': 'program-1',
        'evidence_refs': ['evidence-1'],
    }


class RewardWrapTests(unittest.TestCase):
    """Restart and fault checks for the reward wrap. MOCK only; durable stays false."""

    def test_reward_torn_write_replays_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = FsmBoundary(tmp)
            try:
                opened = boundary.call('reward', lambda machine: machine.open(_reward_opening()))
                self.assertTrue(opened['opened'])
                self.assertIs(opened['durable'], False)
                boundary.call('reward', lambda machine: _observe_reward(machine))
                held = boundary.call(
                    'reward',
                    lambda machine: machine.hold(_reward_rid(), idempotency_key='hold-1'),
                )
                self.assertEqual(held['reward']['phase'], 'HELD')
                with self.assertRaises(ReadinessFault) as raised:
                    boundary.call('reward', lambda machine: _eligible_reward(machine), fault='partial')
                self.assertEqual(raised.exception.code, 'PARTIAL_WRITE')
                self.assertEqual(boundary.last_observation['journalDecision'], 'fault')
                self.assertEqual(boundary.last_observation['faultCode'], 'PARTIAL_WRITE')
                self.assertIs(boundary.last_observation['fsmDurable'], False)
            finally:
                boundary.close()
            recovered = FsmBoundary(tmp)
            try:
                self.assertEqual(recovered.machine('reward').view(_reward_rid())['phase'], 'HELD')
                applied = recovered.call('reward', lambda machine: _eligible_reward(machine))
                self.assertFalse(applied['duplicate'])
                self.assertEqual(applied['reward']['phase'], 'ELIGIBLE')
                replay = recovered.call('reward', lambda machine: _eligible_reward(machine))
                self.assertIs(replay['duplicate'], True)
                self.assertIsNone(replay['applied'])
                machine = recovered.machine('reward')
                self.assertEqual(
                    [entry['op'] for entry in machine.export_journal()],
                    ['open', 'observe', 'hold', 'mark_eligible'],
                )
                self.assertIs(machine.view(_reward_rid())['durable'], False)
            finally:
                recovered.close()

    def test_reward_crash_before_observe_leaves_no_reward(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = FsmBoundary(tmp)
            try:
                boundary.call('reward', lambda machine: machine.open(_reward_opening()))
                with self.assertRaises(ReadinessFault) as raised:
                    boundary.call('reward', lambda machine: _observe_reward(machine), fault='crash_before_durable')
                self.assertEqual(raised.exception.code, 'CRASH_BEFORE_DURABLE')
            finally:
                boundary.close()
            recovered = FsmBoundary(tmp)
            try:
                with self.assertRaises(TokenRewardError) as missing:
                    recovered.machine('reward').view(_reward_rid())
                self.assertEqual(missing.exception.code, 'UNKNOWN_REWARD')
                observed = recovered.call('reward', lambda machine: _observe_reward(machine))
                self.assertFalse(observed['duplicate'])
                self.assertIs(observed['reward']['durable'], False)
                replay = recovered.call('reward', lambda machine: _observe_reward(machine))
                self.assertIs(replay['duplicate'], True)
                self.assertEqual(
                    [entry['op'] for entry in recovered.machine('reward').export_journal()],
                    ['open', 'observe'],
                )
            finally:
                recovered.close()

    def test_reward_restore_round_trips_canonical_state_and_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            boundary = FsmBoundary(tmp)
            try:
                boundary.call('reward', lambda machine: machine.open(_reward_opening()))
                boundary.call('reward', lambda machine: _observe_reward(machine))
                boundary.call(
                    'reward',
                    lambda machine: machine.hold(_reward_rid(), idempotency_key='hold-1'),
                )
                boundary.call('reward', lambda machine: _eligible_reward(machine))
                submitted = boundary.call(
                    'reward',
                    lambda machine: machine.submit(
                        _reward_rid(),
                        idempotency_key='sub-1',
                        approval_ref=_reward_approval(),
                        signed_bytes_digest=REWARD_DIGEST,
                        spend_pool='TOKEN_TREASURY_REWARD',
                    ),
                )
                self.assertEqual(submitted['reward']['phase'], 'ISSUING')
                issued = boundary.call(
                    'reward',
                    lambda machine: machine.observe_transfer_effects(
                        _reward_rid(),
                        idempotency_key='fx-1',
                        effects_digest=REWARD_EFFECTS,
                        outcome='SUCCESS',
                    ),
                )
                self.assertEqual(issued['reward']['phase'], 'ISSUED')
                machine = boundary.machine('reward')
                self.assertEqual(machine.view(_reward_rid())['provenance'], PROVENANCE)
                pool = machine.pool_view()
                self.assertEqual(pool['balances']['TOKEN_TREASURY_REWARD'], 46)
                self.assertEqual(
                    pool['spends'],
                    [{'pool': 'TOKEN_TREASURY_REWARD', 'amount': 4, 'program_ref': 'program-1'}],
                )
                journal = machine.export_journal()
                restored = RewardWrap.restore(journal)
                self.assertEqual(restored.canonical_state(), machine.canonical_state())
                self.assertEqual(restored.state_digest(), machine.state_digest())
                self.assertEqual(restored.export_journal(), journal)
                self.assertEqual(
                    [entry['op'] for entry in journal],
                    ['open', 'observe', 'hold', 'mark_eligible', 'submit', 'observe_transfer_effects'],
                )
                with self.assertRaises(TokenRewardError) as external:
                    machine.reject_external('TRANSFER')
                self.assertEqual(external.exception.code, 'EXTERNAL_EXECUTION_UNSUPPORTED')
                self.assertIs(boundary.last_observation['fsmDurable'], False)
            finally:
                boundary.close()
            again = FsmBoundary(tmp)
            try:
                self.assertEqual(again.machine('reward').state_digest(), restored.state_digest())
                self.assertIs(again.machine('reward').view(_reward_rid())['durable'], False)
            finally:
                again.close()


def _issue(machine):
    return ai_delegation_issue(machine)


def json_copy(value):
    import json
    return json.loads(json.dumps(value))


class _MutationGuardMachine:
    """Test-local journal/digest double; never used by recovery."""

    def __init__(self, journal, digest):
        self.journal = json_copy(journal)
        self.digest = digest

    def export_journal(self):
        return json_copy(self.journal)

    def state_digest(self):
        return self.digest


class BoundaryMutationGuardTests(unittest.TestCase):
    """Injected local-wrapper characterizations, source-informed by call().

    No rollback or production-durability proof. The double only replaces one
    local boundary's reservation machine; committed-prefix recovery is real.
    """

    def _fixture(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        boundary = FsmBoundary(tmp.name)
        self.addCleanup(boundary.close)
        helper = BackendConformance()
        helper._reservation_show(boundary)
        machine = boundary.machine('reservation')
        snapshot = {
            'bytes': (Path(tmp.name) / JOURNAL_NAME).read_bytes(),
            'records': json_copy(boundary.store.records),
            'count': len(boundary.store.records),
            'committed_bytes': boundary.store.committed_bytes,
            'journal': json_copy(machine.export_journal()),
            'digest': machine.state_digest(),
        }
        self.assertGreater(snapshot['count'], 0)
        self.assertTrue(snapshot['journal'])
        self.assertEqual(snapshot['committed_bytes'], len(snapshot['bytes']))
        return tmp.name, boundary, helper, snapshot

    def _assert_persisted_prefix(self, directory, boundary, snapshot):
        self.assertEqual((Path(directory) / JOURNAL_NAME).read_bytes(), snapshot['bytes'])
        self.assertEqual(boundary.store.records, snapshot['records'])
        self.assertEqual(len(boundary.store.records), snapshot['count'])
        self.assertEqual(boundary.store.committed_bytes, snapshot['committed_bytes'])
        for record in boundary.store.records:
            self.assertEqual(record['schema'], SCHEMA_VERSION)
            self.assertEqual(record['kind'], 'fsm_commit')
            self.assertEqual(record['machine'], 'reservation')
            self.assertIn('entry', record)
            self.assertIs(record['protocolTruth'], False)
            self.assertIs(record['productionConformance'], False)

    def _assert_observation(self, boundary, decision, fault_code=None):
        observed = boundary.last_observation
        self.assertEqual(observed['machine'], 'reservation')
        self.assertEqual(observed['journalDecision'], decision)
        self.assertEqual(observed['schemaVersion'], SCHEMA_VERSION)
        for flag in ('fsmDurable', 'protocolTruth', 'productionConformance',
                     'productionReadiness', 'productionEndpoint'):
            self.assertIs(observed[flag], False, flag)
        if fault_code is None:
            self.assertNotIn('faultCode', observed)
            self.assertEqual(observed['appendedEntries'], 0)
        else:
            self.assertEqual(observed['faultCode'], fault_code)

    def _inject(self, boundary, snapshot, mutation):
        double = _MutationGuardMachine(snapshot['journal'], snapshot['digest'])
        boundary.machines['reservation'] = double

        def mutate(machine):
            self.assertIs(machine, double)
            if mutation == 'rewrite':
                machine.journal[0]['idempotency_key'] = 'injected-rewrite'
                self.assertNotEqual(machine.export_journal(), snapshot['journal'])
                self.assertEqual(machine.state_digest(), snapshot['digest'])
            else:
                self.assertEqual(mutation, 'digest')
                machine.digest = 'injected-state-digest'
                self.assertNotEqual(machine.state_digest(), snapshot['digest'])
                self.assertEqual(machine.export_journal(), snapshot['journal'])

        return mutate

    def _assert_fenced_and_recovered(self, directory, boundary, snapshot):
        self._assert_persisted_prefix(directory, boundary, snapshot)
        invoked = Counter()

        def forbidden(machine):
            invoked['calls'] += 1

        for name in ('reservation', 'settlement'):
            with self.subTest(blocked_machine=name):
                with self.assertRaises(ReadinessClosed) as raised:
                    boundary.call(name, forbidden)
                self.assertEqual(raised.exception.code, 'READINESS_CLOSED')
        self.assertEqual(invoked['calls'], 0)
        self._assert_persisted_prefix(directory, boundary, snapshot)
        boundary.close()
        recovered = FsmBoundary(directory)
        try:
            self.assertNotIsInstance(recovered.machine('reservation'), _MutationGuardMachine)
            self.assertEqual(recovered.machine('reservation').export_journal(), snapshot['journal'])
            self.assertEqual(recovered.machine('reservation').state_digest(), snapshot['digest'])
            self._assert_persisted_prefix(directory, recovered, snapshot)
        finally:
            recovered.close()

    def test_journal_rewrite_fences_without_persisting(self):
        directory, boundary, _, snapshot = self._fixture()
        with self.assertRaises(ReadinessError) as raised:
            boundary.call('reservation', self._inject(boundary, snapshot, 'rewrite'))
        self.assertEqual(raised.exception.code, 'JOURNAL_REWRITE')
        self._assert_observation(boundary, 'fault', 'JOURNAL_REWRITE')
        self._assert_fenced_and_recovered(directory, boundary, snapshot)

    def test_unjournaled_mutation_fences_without_persisting(self):
        directory, boundary, _, snapshot = self._fixture()
        with self.assertRaises(ReadinessError) as raised:
            boundary.call('reservation', self._inject(boundary, snapshot, 'digest'))
        self.assertEqual(raised.exception.code, 'UNJOURNALED_MUTATION')
        self._assert_observation(boundary, 'fault', 'UNJOURNALED_MUTATION')
        self._assert_fenced_and_recovered(directory, boundary, snapshot)

    def test_mutation_then_exception_preserves_original_and_fences(self):
        for mutation in ('rewrite', 'digest'):
            with self.subTest(mutation=mutation):
                directory, boundary, _, snapshot = self._fixture()
                mutate = self._inject(boundary, snapshot, mutation)
                original = RuntimeError('injected callback failure')

                def fail(machine):
                    mutate(machine)
                    raise original

                with self.assertRaises(RuntimeError) as raised:
                    boundary.call('reservation', fail)
                self.assertIs(raised.exception, original)
                # Characterization: callback failures use this observation code
                # for both journal rewrites and digest-only mutation.
                self._assert_observation(boundary, 'fault', 'UNJOURNALED_MUTATION')
                self._assert_fenced_and_recovered(directory, boundary, snapshot)

    def _assert_usable(self, directory, boundary, helper, snapshot):
        self._assert_observation(boundary, 'unchanged')
        self._assert_persisted_prefix(directory, boundary, snapshot)
        self.assertEqual(boundary.machine('reservation').export_journal(), snapshot['journal'])
        self.assertEqual(boundary.machine('reservation').state_digest(), snapshot['digest'])
        result = boundary.call('reservation', lambda m: helper._hold(m, 'reserve-1', 'hold-1'))
        self.assertIs(result['duplicate'], False)
        self.assertEqual(len(boundary.store.records), snapshot['count'] + 1)
        self.assertEqual(boundary.store.records[:-1], snapshot['records'])
        self.assertEqual(boundary.store.records[-1]['entry']['op'], 'hold')
        self.assertEqual(boundary.last_observation['journalDecision'], 'appended')
        self.assertEqual(boundary.last_observation['appendedEntries'], 1)

    def test_nonmutating_success_keeps_boundary_usable(self):
        directory, boundary, helper, snapshot = self._fixture()
        sentinel = object()
        self.assertIs(boundary.call('reservation', lambda m: sentinel), sentinel)
        self._assert_usable(directory, boundary, helper, snapshot)

    def test_nonmutating_exception_keeps_boundary_usable(self):
        directory, boundary, helper, snapshot = self._fixture()
        original = RuntimeError('nonmutating callback failure')

        def fail(machine):
            raise original

        with self.assertRaises(RuntimeError) as raised:
            boundary.call('reservation', fail)
        self.assertIs(raised.exception, original)
        self._assert_usable(directory, boundary, helper, snapshot)


class FaultTests(BackendConformance, unittest.TestCase):
    backend = LocalReadinessAdapter()

    def test_core_record_in_an_fsm_journal_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ReadinessStore.open(tmp)
            store.append({
                'kind': 'core_commit',
                'machine': 'integration_core',
                'operationId': 'op-1',
                'actor': 'operator',
                'action': 'advance_clock',
                'body': {'domain': 'kix:fixture:lifecycle:0.3', 'now': 1},
                'receiptDigest': 'cd' * 32,
            })
            store.close()
            with self.assertRaises(ReadinessError) as raised:
                FsmBoundary(tmp)
            self.assertEqual(raised.exception.code, 'UNEXPECTED_RECORD')


class JournalByteSweepTests(unittest.TestCase):
    """Deterministic byte-level tear and flip sweep of journal.v1.

    Public API only. Mutations are applied to copies of a file that was written
    through ReadinessStore.append. Safety property for every mutation: open()
    raises StoreError, or the recovered records are an exact prefix of the
    originals. No power-loss, OS-crash or disk-flush claim: files are rewritten
    in-process. Not a BackendConformance control and not production durability.
    """

    def setUp(self):
        self._root = tempfile.TemporaryDirectory()
        self.addCleanup(self._root.cleanup)
        self._n = 0
        src = Path(self._root.name) / 'src'
        store = ReadinessStore.open(src)
        try:
            self.originals = []
            self.bounds = [HEADER_LEN]
            bodies = [
                {'kind': 'fsm_commit', 'machine': 'settlement',
                 'entry': {'op': 'initiate', 'idempotency_key': 'sweep-1'}},
                {'kind': 'fsm_commit', 'machine': 'reservation',
                 'entry': {'op': 'hold', 'idempotency_key': 'sweep-2'}},
                {'kind': 'core_commit', 'machine': 'integration_core',
                 'operationId': 'sweep-3', 'actor': 'operator',
                 'action': 'advance_clock',
                 'body': {'domain': 'kix:fixture:lifecycle:0.3', 'now': 1},
                 'receiptDigest': 'cd' * 32},
                {'kind': 'fsm_commit', 'machine': 'credit',
                 'entry': {'op': 'draw', 'idempotency_key': 'sweep-4'}},
            ]
            for body in bodies:
                self.originals.append(json_copy(store.append(body)))
                self.bounds.append(store.committed_bytes)
        finally:
            store.close()
        self.data = (src / JOURNAL_NAME).read_bytes()
        self.assertEqual(len(self.data), self.bounds[-1])
        self.assertEqual(self._sweep_outcome(self.data), ('ok', self.originals, len(self.data)))

    def _sweep_dir(self, data):
        self._n += 1
        path = Path(self._root.name) / ('m%d' % self._n)
        path.mkdir()
        (path / JOURNAL_NAME).write_bytes(bytes(data))
        return path

    def _sweep_outcome(self, data):
        path = self._sweep_dir(data)
        try:
            store = ReadinessStore.open(path)
        except StoreError as exc:
            return ('err', exc.code)
        try:
            return ('ok', json_copy(store.records), (path / JOURNAL_NAME).stat().st_size)
        finally:
            store.close()

    def _sweep_assert_safe(self, outcome, label):
        if outcome[0] == 'ok':
            records = outcome[1]
            self.assertEqual(records, self.originals[:len(records)], label)

    def _sweep_flip(self, index):
        data = bytearray(self.data)
        data[index] ^= 0xFF
        return data

    def _sweep_fields(self, i):
        start, end = self.bounds[i], self.bounds[i + 1]
        return range(start, start + 4), range(start + 4, end)

    def test_truncation_at_every_offset_keeps_the_longest_whole_frame_prefix(self):
        extra = {'kind': 'fsm_commit', 'machine': 'settlement',
                 'entry': {'op': 'initiate', 'idempotency_key': 'sweep-new'}}
        for k in range(HEADER_LEN, len(self.data) + 1):
            n = max(i for i in range(len(self.bounds)) if self.bounds[i] <= k)
            path = self._sweep_dir(self.data[:k])
            store = ReadinessStore.open(path)
            try:
                self.assertEqual(store.records, self.originals[:n], k)
                self.assertEqual(store.committed_bytes, self.bounds[n], k)
                self.assertEqual((path / JOURNAL_NAME).stat().st_size, self.bounds[n], k)
                new = json_copy(store.append(extra))
            finally:
                store.close()
            again = ReadinessStore.open(path)
            try:
                self.assertEqual(again.records, self.originals[:n] + [new], k)
            finally:
                again.close()

    def test_header_truncation_and_header_byte_flips_are_recorded(self):
        seen = Counter()
        empty = self._sweep_outcome(b'')
        self.assertEqual(empty, ('ok', [], HEADER_LEN))  # class B: reinitialised
        seen['reinit-empty'] += 1
        for k in range(1, HEADER_LEN):
            outcome = self._sweep_outcome(self.data[:k])
            self.assertEqual(outcome, ('err', 'JOURNAL_HEADER'), k)
            seen['JOURNAL_HEADER'] += 1
        for i in range(HEADER_LEN):
            outcome = self._sweep_outcome(self._sweep_flip(i))
            self.assertEqual(
                outcome, ('err', 'UNSUPPORTED_SCHEMA' if 8 <= i < 12 else 'JOURNAL_HEADER'), i)
            seen[outcome[1]] += 1
        self.assertEqual(seen, Counter({
            'reinit-empty': 1, 'JOURNAL_HEADER': 15 + 12, 'UNSUPPORTED_SCHEMA': 4}))

    def test_every_payload_and_crc_byte_flip_fails_closed(self):
        count = 0
        for i in range(len(self.originals)):
            for index in self._sweep_fields(i)[1]:
                outcome = self._sweep_outcome(self._sweep_flip(index))
                self.assertEqual(outcome, ('err', 'CHECKSUM_MISMATCH'), index)
                count += 1
        self.assertEqual(count, len(self.data) - HEADER_LEN - 4 * len(self.originals))

    def _sweep_length_outcomes(self):
        results = {}
        for i in range(len(self.originals)):
            for index in self._sweep_fields(i)[0]:
                outcome = self._sweep_outcome(self._sweep_flip(index))
                self._sweep_assert_safe(outcome, index)
                results[(i, index - self.bounds[i])] = outcome
        return results

    def test_length_prefix_flips_never_alter_or_fabricate_a_record(self):
        classes = Counter()
        for (i, byte), outcome in self._sweep_length_outcomes().items():
            if outcome[0] == 'err':
                self.assertEqual(outcome[1], 'CHECKSUM_MISMATCH', (i, byte))
                classes['CHECKSUM_MISMATCH'] += 1
            else:
                self.assertLess(len(outcome[1]), len(self.originals), (i, byte))
                self.assertEqual(outcome[1], self.originals[:i], (i, byte))
                self.assertEqual(outcome[2], self.bounds[i], (i, byte))
                classes['torn-prefix'] += 1
        self.assertEqual(sum(classes.values()), 16)

    def test_characterization_b_damaged_length_prefix_drops_later_acknowledged_frames(self):
        # CHARACTERIZATION (AGENTS section 8 class B): the contract defines only a
        # trailing incomplete frame and a complete frame with a bad checksum. A
        # length prefix pointing past EOF or above MAX_RECORD_BYTES is parsed as a
        # torn tail, so later complete frames are truncated away with no error.
        # Pins current behaviour; it is not an endorsement.
        results = self._sweep_length_outcomes()
        counts = Counter()
        for (i, byte), outcome in results.items():
            later = len(self.originals) - 1 - i
            if outcome[0] == 'err':
                counts['CHECKSUM_MISMATCH'] += 1
            elif later > 0:
                counts['silent-drop-later-complete-frames'] += 1
            else:
                counts['torn-final-frame'] += 1
        self.assertEqual(counts, Counter({
            'silent-drop-later-complete-frames': 9,
            'torn-final-frame': 3,
            'CHECKSUM_MISMATCH': 4,
        }))
        for i in range(len(self.originals)):
            for byte in (0, 1):  # 0xFF.. or 0x..FF prefix exceeds MAX_RECORD_BYTES
                self.assertEqual(results[(i, byte)][0], 'ok')
        # Restoring the byte afterwards does not bring the frames back.
        path = self._sweep_dir(self._sweep_flip(self.bounds[1]))
        ReadinessStore.open(path).close()
        self.assertEqual((path / JOURNAL_NAME).stat().st_size, self.bounds[1])
        (path / JOURNAL_NAME).write_bytes(self.data[:self.bounds[1]])
        store = ReadinessStore.open(path)
        try:
            self.assertEqual(store.records, self.originals[:1])
        finally:
            store.close()
        self.assertGreater(MAX_RECORD_BYTES, 0xFFFF)

    def test_crc_consistent_damage_is_rejected_not_repaired(self):
        start, end = self.bounds[0], self.bounds[1]
        payload = self.data[start + 4:end - 4]

        def reframe(body):
            frame = struct.pack('>I', len(body)) + body
            frame += struct.pack('>I', zlib.crc32(body) & 0xFFFFFFFF)
            return self.data[:start] + frame + self.data[end:]

        cases = {
            'invalid-utf8': payload[:-2] + b'\xff' + payload[-1:],
            'duplicate-key': payload[:-1] + b',"kind":"fsm_commit"}',
            'schema-2': payload.replace(b'"schema":1', b'"schema":2'),
            'protocol-truth-true': payload.replace(
                b'"protocolTruth":false', b'"protocolTruth":true'),
        }
        for name, body in cases.items():
            self.assertNotEqual(body, payload, name)
            outcome = self._sweep_outcome(reframe(body))
            self.assertEqual(outcome, ('err', 'JOURNAL_CORRUPT'), name)


if __name__ == '__main__':
    unittest.main()


class _Recorder:
    """Collects the (machine, step) pairs a BackendConformance helper would issue."""

    def __init__(self):
        self.steps = []

    def call(self, name, fn, fault=None):
        self.steps.append((name, fn))


class CrashPointSweepTests(unittest.TestCase):
    """Fault at every command of each BackendConformance scenario (class A/B map in CONFORMANCE.md).

    Public adapter surface only. Single process, single writer, local files; no
    power-loss, fsync or production claim.
    """

    backend = LocalReadinessAdapter()
    FAULT_CODES = {'partial': 'PARTIAL_WRITE', 'crash_before_durable': 'CRASH_BEFORE_DURABLE'}
    EXPECTED_COMMANDS = {
        'settlement': 5, 'reservation': 3, 'resale': 5, 'credit': 3,
        'admission': 4, 'ai_delegation': 3, 'reward': 6,
    }
    VIEW_IDS = {
        'settlement': 'claim-1', 'reservation': 'reserve-1', 'resale': 'list-1',
        'credit': 'adv-1', 'admission': 'issue-1', 'ai_delegation': 'g1',
        'reward': _reward_rid(),
    }
    VIEW_METHODS = {'ai_delegation': 'view_grant'}
    # class B: these resends raise the wrap's own error instead of returning a
    # duplicate result (the open calls carry no idempotency key). The wraps
    # define distinct WrapError classes, so each cell carries its error type.
    REPLAY_ERRORS = {
        ('ai_delegation', 0): (AiDelegationWrapError, 'ALREADY_OPEN'),
        ('reward', 0): (RewardWrapError, 'ALREADY_OPEN'),
    }
    FALSE_LABELS = (
        'durable', 'funds_executed', 'economic_finality_claimed',
        'chain_owner_current', 'admission_routing_production', 'bank_debit_observed',
    )
    executed = Counter()
    sequences = {}
    reference = {}

    @classmethod
    def _build_sequences(cls):
        helper = BackendConformance()
        out = {}
        rec = _Recorder()
        helper._settlement_until_capture(rec)
        rec.call('settlement', lambda m: m.commit('claim-1', idempotency_key='commit-1', **helper._commit_body()))
        rec.call('settlement', lambda m: m.distribute(
            'claim-1', idempotency_key='dist-1', order=['platform', 'organizer']))
        out['settlement'] = rec.steps
        rec = _Recorder()
        helper._reservation_show(rec)
        rec.call('reservation', lambda m: helper._hold(m, 'reserve-1', 'hold-1'))
        out['reservation'] = rec.steps
        rec = _Recorder()
        helper._resale_until_paid(rec)
        rec.call('resale', lambda m: m.accept_resale(
            'transfer-1', idempotency_key='transfer-1', listing_id='list-1'))
        out['resale'] = rec.steps
        rec = _Recorder()
        helper._credit_until_approved(rec, committed_face())
        rec.call('credit', lambda m: m.draw('adv-1', idempotency_key='draw-1', draw_id='draw-1'))
        out['credit'] = rec.steps
        rec = _Recorder()
        helper._admission_until_authorized(rec)
        rec.call('admission', lambda m: helper._consume(m))
        out['admission'] = rec.steps
        rec = _Recorder()
        helper._ai_delegation_opened(rec)
        rec.call('ai_delegation', ai_delegation_issue)
        rec.call('ai_delegation', lambda m: m.revoke_grant('human-issuer', 'g1', 'fixture-reason'))
        out['ai_delegation'] = rec.steps
        rec = _Recorder()
        helper._reward_opened(rec)
        rec.call('reward', _observe_reward)
        rec.call('reward', lambda m: m.hold(_reward_rid(), idempotency_key='hold-1'))
        rec.call('reward', _eligible_reward)
        rec.call('reward', lambda m: m.submit(
            _reward_rid(), idempotency_key='sub-1', approval_ref=_reward_approval(),
            signed_bytes_digest=REWARD_DIGEST, spend_pool='TOKEN_TREASURY_REWARD'))
        rec.call('reward', lambda m: m.observe_transfer_effects(
            _reward_rid(), idempotency_key='fx-1', effects_digest=REWARD_EFFECTS,
            outcome='SUCCESS'))
        out['reward'] = rec.steps
        return out

    @classmethod
    def _reference_run(cls, machine_name):
        steps = cls.sequences[machine_name]
        with tempfile.TemporaryDirectory() as tmp:
            boundary = cls.backend.open_boundary(tmp)
            try:
                machine = boundary.machine(machine_name)
                digests = [machine.state_digest()]
                results = []
                for name, step in steps:
                    results.append(boundary.call(name, step))
                    digests.append(boundary.machine(name).state_digest())
                journal = boundary.machine(machine_name).export_journal()
            finally:
                boundary.close()
        return {'results': results, 'digests': digests, 'journal': journal}

    @classmethod
    def setUpClass(cls):
        cls.sequences = cls._build_sequences()
        cls.reference = {name: cls._reference_run(name) for name in cls.sequences}

    def _resend(self, boundary, name, step):
        # Only place command i is resent after the fault.
        return boundary.call(name, step)

    def _false_labels_hold(self, value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in self.FALSE_LABELS:
                    self.assertIs(item, False, key)
                self._false_labels_hold(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                self._false_labels_hold(item)

    def _records(self, directory):
        store = self.backend.open_store(directory)
        try:
            return list(store.records)
        finally:
            store.close()

    def _sweep_case(self, machine_name, fault, i):
        steps = self.sequences[machine_name]
        ref = self.reference[machine_name]
        n = len(steps)
        name, step = steps[i]
        with tempfile.TemporaryDirectory() as tmp:
            boundary = self.backend.open_boundary(tmp)
            try:
                for j in range(i):
                    self.assertEqual(boundary.call(*steps[j]), ref['results'][j])
                with self.assertRaises(self.backend.fault_error) as raised:
                    boundary.call(name, step, fault=fault)
                self.assertEqual(raised.exception.code, self.FAULT_CODES[fault])
                with self.assertRaises(ReadinessError) as closed:
                    boundary.call(name, step)
                self.assertEqual(closed.exception.code, 'READINESS_CLOSED')
            finally:
                boundary.close()
            records = self._records(tmp)
            self.assertEqual(len(records), i)
            self.assertEqual([r['entry'] for r in records], ref['journal'][:i])
            for record in records:
                self.assertIs(record['protocolTruth'], False)
                self.assertIs(record['productionConformance'], False)
            boundary = self.backend.open_boundary(tmp)
            try:
                machine = boundary.machine(machine_name)
                # (a) recovered state is the prefix state only
                self.assertEqual(machine.state_digest(), ref['digests'][i])
                self.assertEqual(machine.export_journal(), ref['journal'][:i])
                # (b) resend applies exactly once with the uninterrupted result
                first = self._resend(boundary, name, step)
                self.assertEqual(first, ref['results'][i])
                if (machine_name, i) in self.REPLAY_ERRORS:
                    self.assertNotIn('duplicate', first)
                else:
                    self.assertIs(first['duplicate'], False)
                self.assertEqual(boundary.machine(machine_name).state_digest(), ref['digests'][i + 1])
                self.assertEqual(boundary.machine(machine_name).export_journal(), ref['journal'][:i + 1])
                replay_error = self.REPLAY_ERRORS.get((machine_name, i))
                if replay_error is None:
                    again = boundary.call(name, step)
                    self.assertIs(again['duplicate'], True)
                    if machine_name == 'ai_delegation':
                        self.assertNotIn('applied', again)
                    else:
                        self.assertIsNone(again['applied'])
                else:
                    error_type, error_code = replay_error
                    with self.assertRaises(error_type) as again:
                        boundary.call(name, step)
                    self.assertEqual(again.exception.code, error_code)
                self.assertEqual(boundary.machine(machine_name).state_digest(), ref['digests'][i + 1])
                self.assertEqual(boundary.machine(machine_name).export_journal(), ref['journal'][:i + 1])
                # (c) finishing reaches the uninterrupted final state
                for j in range(i + 1, n):
                    self.assertEqual(boundary.call(*steps[j]), ref['results'][j])
                machine = boundary.machine(machine_name)
                self.assertEqual(machine.state_digest(), ref['digests'][n])
                self.assertEqual(machine.export_journal(), ref['journal'])
                self._false_labels_hold(ref['results'])
                self._false_labels_hold(
                    getattr(machine, self.VIEW_METHODS.get(machine_name, 'view'))(
                        self.VIEW_IDS[machine_name],
                    ),
                )
            finally:
                boundary.close()
            # (d) record count equals accepted commands; labels stay false
            records = self._records(tmp)
            self.assertEqual(len(records), n)
            self.assertEqual([r['entry'] for r in records], ref['journal'])
            for record in records:
                self.assertIs(record['protocolTruth'], False)
                self.assertIs(record['productionConformance'], False)
            boundary = self.backend.open_boundary(tmp)
            try:
                self.assertEqual(boundary.machine(machine_name).state_digest(), ref['digests'][n])
            finally:
                boundary.close()

    def _sweep(self, machine_name):
        ran = Counter()
        for fault in self.FAULT_CODES:
            for i, (_, step) in enumerate(self.sequences[machine_name]):
                op = self.reference[machine_name]['journal'][i]['op']
                with self.subTest(machine=machine_name, fault=fault, command=i, op=op):
                    self._sweep_case(machine_name, fault, i)
                    ran[fault] += 1
        for fault in self.FAULT_CODES:
            type(self).executed[(machine_name, fault)] += ran[fault]
            self.assertEqual(ran[fault], self.EXPECTED_COMMANDS[machine_name], fault)

    def test_crash_point_sweep_settlement(self):
        self._sweep('settlement')

    def test_crash_point_sweep_reservation(self):
        self._sweep('reservation')

    def test_crash_point_sweep_resale(self):
        self._sweep('resale')

    def test_crash_point_sweep_credit(self):
        self._sweep('credit')

    def test_crash_point_sweep_admission(self):
        self._sweep('admission')

    def test_crash_point_sweep_ai_delegation(self):
        self._sweep('ai_delegation')

    def test_crash_point_sweep_reward(self):
        self._sweep('reward')

    def test_reference_runs_are_deterministic_and_one_entry_per_command(self):
        for name, steps in self.sequences.items():
            with self.subTest(machine=name):
                self.assertEqual(len(steps), self.EXPECTED_COMMANDS[name])
                again = self._reference_run(name)
                ref = self.reference[name]
                self.assertEqual(again, ref)
                # class B: every command emits exactly one journal entry
                self.assertEqual(len(ref['journal']), len(steps))
                self.assertEqual(len(ref['digests']), len(steps) + 1)

    def test_sweep_cells_subsume_the_existing_fault_cases(self):
        # Existing BackendConformance cases fault one command per machine; the
        # sweep reaches the same cells: (machine, fault, op).
        cells = [
            ('settlement', 'partial', 'commit'),
            ('reservation', 'partial', 'hold'),
            ('resale', 'partial', 'accept_resale'),
            ('credit', 'partial', 'draw'),
            ('admission', 'partial', 'consume'),
            ('settlement', 'crash_before_durable', 'authorize'),
            ('reservation', 'crash_before_durable', 'hold'),
            ('ai_delegation', 'partial', 'revoke_grant'),
            ('ai_delegation', 'crash_before_durable', 'issue_grant'),
            ('reward', 'partial', 'mark_eligible'),
            ('reward', 'crash_before_durable', 'observe'),
        ]
        for machine_name, fault, op in cells:
            with self.subTest(machine=machine_name, fault=fault, op=op):
                self.assertIn(fault, self.FAULT_CODES)
                ops = [entry['op'] for entry in self.reference[machine_name]['journal']]
                self.assertEqual(ops.count(op), 1)
