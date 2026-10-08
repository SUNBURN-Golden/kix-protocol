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
from ai_delegation_mock import AiDelegationError
from readiness.migrate import SCHEMA_VERSION, MigrationError, migrate, migrate_explicit
from readiness.policy import AdmitGate
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


def _issue(machine):
    return machine.issue_grant(
        'human-issuer',
        'g1',
        'agent-1',
        ['QUERY', 'PROPOSE'],
        {'surfaces': ['surface-a']},
        {
            'per_action_max': 100,
            'cumulative_max': 1000,
            'count_max': 5,
            'currency': 'KRW',
        },
        {'not_before': 10, 'not_after': 20},
    )


def json_copy(value):
    import json
    return json.loads(json.dumps(value))


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
