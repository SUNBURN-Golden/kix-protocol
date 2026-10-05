"""Fault checks for the local readiness journal.

These tests restart an in-process boundary and a file. They do not claim a
public endpoint, production conformance, bank exactly-once, or chain finality.
Protocol FSM `durable` flags stay false: the journal is not protocol truth.
"""

from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from readiness.boundary import FsmBoundary, ReadinessError
from readiness.migrate import MigrationError, migrate
from readiness.store import JOURNAL_NAME, ReadinessFault, ReadinessStore, StoreError

from readiness.conformance import BackendConformance
from readiness.local_adapter import LocalReadinessAdapter


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



if __name__ == '__main__':
    unittest.main()
