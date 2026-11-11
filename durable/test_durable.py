"""Stage-5 durable layer on the adopted local PostgreSQL 17.11.

Needs /usr/lib/postgresql/17/bin/{postgres,initdb} and psycopg. A missing
backend fails the run loudly; nothing here skips. Budget numbers and provider
fields are synthetic fixtures, not product policy. Not wired into CI.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from contextlib import contextmanager

import psycopg

from readiness.conformance import BackendConformance
from readiness.store import StoreError

from durable import PINNED_POSTGRES
from durable.backend import DurablePostgresBackend
from durable.budgets import CLASSES, BudgetSpec, ClassLimit
from durable.cluster import PinnedPostgresCluster
from durable.errors import AliasConflict, Backpressure, UnknownOperation
from durable.inbox import (
    APPLIED, CONFLICT, DUPLICATE, FIRST, RECEIVED, SAME_FACT, UNMATCHED, SqlAliasStore,
)
from durable.model import Command
from durable.normalize import ProviderItem, Scope, resolve_alias
from durable.outbox import FIXTURE_DISPATCH_KIND, fixture_dispatcher
from durable.schema import CRC_TABLES, store_key

OBSERVED = {}

# Fixtures only. Not an approved limit of any kind.
BIG = ClassLimit(count=64, bytes=1_000_000, age_ms=10_000_000)
SCOPE = Scope('fixture-provider', 'fixture-account', 'fixture-env', 'fixture-profile-1')


def spec(**override):
    limits = {name: BIG for name in CLASSES}
    limits.update(override)
    return BudgetSpec(**limits)


def command(command_id='c1', slot='0', nonce='0', amount='10001'):
    return Command(command_id, 'fixture-show', slot, amount, 'buyer-1', nonce)


def raw_delivery(entries, delivery='t-1', pad=''):
    """A synthetic stand-in for an authenticated lookup response."""
    return json.dumps({'delivery': delivery, 'entries': entries}, sort_keys=True).encode() + pad.encode()


def entry(key='k1', amount=10001, status='DONE', kind='capture', operation='op-1'):
    return {
        'key': key, 'kind': kind, 'amount': amount, 'currency': 'KRW', 'method': 'fixture-method',
        'status': status, 'at': '2026-10-13T09:00:00', 'offset': None, 'operation': operation,
    }


def fixture_lookup(raw):
    document = json.loads(raw.decode().strip())
    items = []
    for one in document['entries']:
        operation = None
        if one['operation'] is not None:
            operation = {'provider': 'fixture-provider', 'account': 'fixture-account',
                         'operation': one['operation']}
        items.append(ProviderItem(
            fact_key=one['key'], kind=one['kind'], amount_krw=one['amount'],
            currency=one['currency'], method=one['method'], status=one['status'],
            occurred_at_text=one['at'], occurred_offset=one['offset'], operation=operation,
        ))
    return items


class FaultyConnection:
    """Wraps a live connection and fails one statement. mode 'before' raises
    without sending it; 'after' sends it and then raises (a lost response)."""

    def __init__(self, real, predicate, mode='before'):
        self._real = real
        self._predicate = predicate
        self._mode = mode
        self.hits = 0

    def execute(self, query, params=None):
        if self._predicate(str(query), params):
            self.hits += 1
            if self._mode == 'after':
                self._real.execute(query, params)
            raise psycopg.OperationalError('injected fault')
        return self._real.execute(query, params)

    def __getattr__(self, name):
        return getattr(self._real, name)


class _ClusterCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix='kixs5test-')
        cls.cluster = PinnedPostgresCluster(cls.root)
        cls.cluster.start()
        OBSERVED['version'] = cls.cluster.version
        OBSERVED['settings'] = cls.cluster.settings
        cls.backend = DurablePostgresBackend(cls.cluster)

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        shutil.rmtree(cls.root, ignore_errors=True)

    @contextmanager
    def unit(self, directory, budget=None):
        unit = self.backend.open_unit(directory, budget or spec())
        try:
            yield unit
        finally:
            unit.close()

    def side_count(self, directory, table, where='1 = 1'):
        """Count rows through a second connection: only committed rows are seen."""
        conn = self.cluster.connect()
        try:
            conn.execute('SET search_path TO d%s' % store_key(directory))
            return int(conn.execute('SELECT COUNT(*) FROM %s WHERE %s' % (table, where)).fetchone()[0])
        finally:
            conn.close()


class DurableConformance(BackendConformance, _ClusterCase):
    """The readiness conformance suite on the adopted backend."""

    def test_cluster_is_the_pinned_local_postgres_on_a_unix_socket(self):
        self.assertIn(PINNED_POSTGRES, self.cluster.version)
        settings = self.cluster.settings
        self.assertEqual(settings['listen_addresses']['setting'], '')
        for name in ('fsync', 'full_page_writes', 'synchronous_commit', 'data_checksums'):
            self.assertEqual(settings[name]['setting'], 'on')


class UnitTests(_ClusterCase):
    def test_atomic_unit_commits_all_rows(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            result = unit.apply(command(), 1)
            self.assertEqual(result['outcome'], 'new_success')
            counts = unit.table_counts()
            for table in ('command_result', 'slot_hold', 'minimal_order', 'outbox_intent', 'ledger'):
                self.assertEqual(counts[table], 1, table)
            for table in ('observation', 'outbox_attempt', 'inbox_delivery'):
                self.assertEqual(counts[table], 0, table)
            self.assertEqual([item['intentId'] for item in unit.outbox.pending()], ['intent-c1'])

    def test_injected_failure_leaves_no_partial_rows(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            real = unit.session.conn
            unit.session.conn = FaultyConnection(real, lambda q, p: 'INSERT INTO outbox_intent' in q)
            result = unit.apply(command(), 1)
            self.assertEqual(result['outcome'], 'error')
            unit.session.conn = real
            self.assertTrue(all(count == 0 for count in unit.table_counts().values()))
            self.assertEqual(unit.apply(command(), 2)['outcome'], 'new_success')

    def test_replay_returns_the_first_result_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.unit(tmp) as unit:
                first = unit.apply(command(), 1)
            with self.unit(tmp) as unit:
                before = unit.table_counts()
                again = unit.apply(command(), 99)
                self.assertEqual(again['outcome'], 'replayed')
                self.assertEqual(again['first_result'], first['first_result'])
                self.assertEqual(unit.table_counts(), before)

    def test_process_kill_preserves_first_result_inbox_and_outbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.unit(tmp) as unit:
                first = unit.apply(command(), 1)
                unit.inbox.receive(
                    SCOPE, raw_delivery([entry()]), verification_result='FIXTURE_UNVERIFIED',
                    received_ms=1, now_ms=1, lookup_fn=fixture_lookup, apply_fn=lambda item: None,
                )
            self.cluster.kill()
            self.cluster.start()
            with self.unit(tmp) as unit:
                again = unit.apply(command(), 2)
                self.assertEqual((again['outcome'], again['first_result']), ('replayed', first['first_result']))
                self.assertEqual([item['intentId'] for item in unit.outbox.pending()], ['intent-c1'])
                self.assertEqual([item['state'] for item in unit.inbox.items()], [APPLIED])
                self.assertEqual(unit.table_counts()['inbox_delivery'], 1)

    def test_commit_with_a_lost_response_is_unknown_and_the_effect_is_read_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.unit(tmp) as unit:
                real = unit.session.conn
                unit.session.conn = FaultyConnection(real, lambda q, p: q == 'COMMIT', mode='after')
                result = unit.apply(command(), 1)
                self.assertEqual(result['outcome'], 'unknown')
                self.assertEqual(result['first_result'], '')
                with self.assertRaises(StoreError) as closed:
                    unit.apply(command(), 2)
                self.assertEqual(closed.exception.code, 'JOURNAL_CLOSED')
                unit.session.conn = real
            with self.unit(tmp) as unit:
                again = unit.apply(command(), 3)
                self.assertEqual(again['outcome'], 'replayed')

    def test_commit_that_never_arrived_is_also_reported_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.unit(tmp) as unit:
                real = unit.session.conn
                unit.session.conn = FaultyConnection(real, lambda q, p: q == 'COMMIT', mode='before')
                self.assertEqual(unit.apply(command(), 1)['outcome'], 'unknown')
                unit.session.conn = real
                real.execute('ROLLBACK')
            with self.unit(tmp) as unit:
                self.assertEqual(unit.apply(command(), 2)['outcome'], 'new_success')
                self.assertEqual(unit.table_counts()['command_result'], 1)

    def test_u128_round_trips_as_decimal_text(self):
        top = str((1 << 128) - 1)
        with tempfile.TemporaryDirectory() as tmp:
            with self.unit(tmp) as unit:
                first = unit.apply(command('big', amount=top), 1)
                self.assertEqual(first['outcome'], 'new_success')
                self.assertEqual(unit.read_amount('big'), top)
            with self.unit(tmp) as unit:
                self.assertEqual(unit.read_amount('big'), top)
                self.assertEqual(unit.apply(command('big', amount=top), 2)['outcome'], 'replayed')
                self.assertIsNone(unit.read_amount('absent'))

    def test_business_rejection_keeps_the_command_without_an_order(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            unit.apply(command('c1', slot='0'), 1)
            rejected = unit.apply(command('c2', slot='0'), 2)
            self.assertEqual(rejected['outcome'], 'business_rejected')
            counts = unit.table_counts()
            self.assertEqual((counts['command_result'], counts['minimal_order'], counts['outbox_intent']), (2, 1, 1))
            self.assertEqual(unit.apply(command('c2', slot='0'), 3)['outcome'], 'replayed')

    def test_conflicting_payload_is_retained_once_and_the_first_result_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            first = unit.apply(command(), 1)
            conflict = unit.apply(command(nonce='1'), 2)
            self.assertEqual(conflict['outcome'], 'conflict_retained')
            self.assertEqual(conflict['first_result'], first['first_result'])
            self.assertEqual(unit.table_counts()['observation'], 1)
            unit.apply(command(nonce='1'), 3)
            self.assertEqual(unit.table_counts()['observation'], 1)
            self.assertEqual(unit.apply(command(), 4)['first_result'], first['first_result'])

    def test_a_corrupt_row_fails_closed_for_every_checksummed_table(self):
        for table in CRC_TABLES:
            with self.subTest(table=table), tempfile.TemporaryDirectory() as tmp:
                with self.unit(tmp) as unit:
                    unit.apply(command(), 1)
                    unit.apply(command(nonce='1'), 2)
                    unit.outbox.record_attempt('intent-c1', 3)
                    unit.inbox.receive(
                        SCOPE, raw_delivery([entry()]), verification_result='FIXTURE_UNVERIFIED',
                        received_ms=1, now_ms=1, lookup_fn=fixture_lookup,
                        apply_fn=lambda item: None,
                    )
                    self.assertGreater(unit.table_counts()[table], 0)
                self.backend.corrupt_unit_table(tmp, table)
                with self.assertRaises(StoreError) as raised:
                    self.backend.open_unit(tmp, spec())
                self.assertEqual(raised.exception.code, 'CHECKSUM_MISMATCH')

    def test_second_writer_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp):
            with self.assertRaises(StoreError) as raised:
                self.backend.open_unit(tmp, spec())
            self.assertEqual(raised.exception.code, 'JOURNAL_LOCKED')

    def test_a_different_budget_cannot_reopen_the_same_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.unit(tmp):
                pass
            with self.assertRaises(StoreError) as raised:
                self.backend.open_unit(tmp, spec(cancel=ClassLimit(count=1, bytes=1, age_ms=1)))
            self.assertEqual(raised.exception.code, 'JOURNAL_RECORD')

    def test_production_flags_stay_false(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            self.assertTrue(all(value is False for value in unit.flags().values()))
            body = json.loads(unit.apply(command(), 1)['first_result'])
            for name in ('protocolTruth', 'productionConformance', 'productionReadiness',
                         'productionEndpoint', 'fundsExecuted', 'chainWriter'):
                self.assertIs(body[name], False)


class BudgetTests(_ClusterCase):
    def test_inflow_capacity_preserves_replay_observation_and_service_paths(self):
        budget = spec(inflow=ClassLimit(count=1, bytes=1_000_000, age_ms=10_000_000))
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, budget) as unit:
            first = unit.apply(command('c1', slot='0'), 1)
            before = unit.table_counts()
            refused = unit.apply(command('c2', slot='1'), 2)
            self.assertEqual(
                (refused['outcome'], refused['capacity_class'], refused['capacity_reason']),
                ('capacity', 'inflow', 'count'),
            )
            self.assertEqual(unit.table_counts(), before)
            self.assertEqual(unit.apply(command('c1', slot='0'), 3)['first_result'], first['first_result'])
            self.assertEqual(unit.apply(command('c1', slot='0', nonce='1'), 4)['outcome'], 'conflict_retained')
            attempt = unit.outbox.record_attempt('intent-c1', 5)
            self.assertEqual((attempt['budgetClass'], attempt['state']), ('completion', 'NOT_DISPATCHED'))

    def test_observation_budget_is_separate_from_inflow(self):
        budget = spec(observation=ClassLimit(count=1, bytes=1_000_000, age_ms=10_000_000))
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, budget) as unit:
            unit.apply(command(), 1)
            self.assertEqual(unit.apply(command(nonce='1'), 2)['outcome'], 'conflict_retained')
            refused = unit.apply(command(nonce='2'), 3)
            self.assertEqual((refused['outcome'], refused['capacity_class']), ('capacity', 'observation'))
            self.assertEqual(unit.table_counts()['observation'], 1)
            self.assertEqual(unit.apply(command('c2', slot='1'), 4)['outcome'], 'new_success')

    def test_byte_budget_counts_the_payload(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, spec(inflow=ClassLimit(count=64, bytes=10, age_ms=1))) as unit:
            refused = unit.apply(command(), 1)
            self.assertEqual((refused['outcome'], refused['capacity_reason']), ('capacity', 'bytes'))
            self.assertTrue(all(count == 0 for count in unit.table_counts().values()))

    def test_age_budget_uses_the_callers_clock(self):
        budget = spec(inflow=ClassLimit(count=64, bytes=1_000_000, age_ms=100))
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, budget) as unit:
            unit.apply(command('c1', slot='0'), 1_000)
            self.assertEqual(unit.apply(command('c2', slot='1'), 1_100)['outcome'], 'new_success')
            late = unit.apply(command('c3', slot='2'), 1_101)
            self.assertEqual((late['outcome'], late['capacity_reason']), ('capacity', 'age'))
            self.assertEqual(unit.apply(command('c1', slot='0'), 1_101)['outcome'], 'replayed')

    def test_dispatching_an_intent_closes_its_inflow_age(self):
        budget = spec(inflow=ClassLimit(count=64, bytes=1_000_000, age_ms=100))
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, budget) as unit:
            unit.apply(command('c1', slot='0'), 1_000)
            unit.outbox.record_attempt('intent-c1', 1_001, dispatcher=lambda call: {'dispatched': True, 'kind': 'fixture-sent'})
            self.assertEqual(unit.apply(command('c2', slot='1'), 5_000)['outcome'], 'new_success')

    def test_recovery_attempts_use_their_own_class(self):
        budget = spec(recovery=ClassLimit(count=0, bytes=1_000_000, age_ms=10_000_000))
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, budget) as unit:
            unit.apply(command(), 1)
            first = unit.outbox.record_attempt('intent-c1', 2)
            self.assertEqual(first['budgetClass'], 'completion')
            called = []
            with self.assertRaises(Backpressure) as raised:
                unit.outbox.record_attempt('intent-c1', 3, dispatcher=lambda call: called.append(call))
            self.assertEqual((raised.exception.code, raised.exception.budget_class), ('OUTBOX_CAPACITY', 'recovery'))
            self.assertEqual(called, [])


class InboxTests(_ClusterCase):
    def receive(self, unit, raw, apply_fn=None, now_ms=1, lookup_fn=fixture_lookup):
        return unit.inbox.receive(
            SCOPE, raw, verification_result='FIXTURE_UNVERIFIED', received_ms=now_ms, now_ms=now_ms,
            lookup_fn=lookup_fn, apply_fn=apply_fn or (lambda item: None),
        )

    def test_raw_is_committed_before_the_apply_hook_and_the_ack(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            seen = {}

            def apply_fn(item):
                seen['deliveries'] = self.side_count(tmp, 'inbox_delivery')
                seen['items'] = self.side_count(tmp, 'inbox_item')

            raw = raw_delivery([entry()])
            ack = self.receive(unit, raw, apply_fn)
            self.assertEqual(seen, {'deliveries': 1, 'items': 1})
            self.assertTrue(ack['ack'])
            stored = unit.inbox.items()[0]
            self.assertEqual(stored['raw'], raw)
            self.assertEqual(stored['verificationResult'], 'FIXTURE_UNVERIFIED')

    def test_batch_yields_per_item_identities_and_durable_aliases(self):
        entries = [entry('k1'), entry('k2', kind='cancel', amount=300, status='PARTIAL'), entry('k3', amount=7)]
        with tempfile.TemporaryDirectory() as tmp:
            applied = []
            with self.unit(tmp) as unit:
                ack = self.receive(unit, raw_delivery(entries), applied.append)
                ids = [item['eventItemId'] for item in ack['items']]
                self.assertEqual(len(set(ids)), 3)
                self.assertEqual(len(applied), 3)
                self.assertEqual(unit.table_counts()['event_alias'], 3)
                self.assertEqual([i['relation'] for i in ack['items']], [FIRST] * 3)
            with self.unit(tmp) as unit:
                again = self.receive(unit, raw_delivery(entries, delivery='t-2'), applied.append, now_ms=2)
                self.assertEqual([i['eventItemId'] for i in again['items']], ids)
                self.assertEqual([i['relation'] for i in again['items']], [SAME_FACT] * 3)
                self.assertEqual(unit.table_counts()['event_alias'], 3)

    def test_the_delivery_id_never_becomes_the_item_identity(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            first = self.receive(unit, raw_delivery([entry()], delivery='t-1'))
            second = self.receive(unit, raw_delivery([entry()], delivery='t-2'), now_ms=2)
            self.assertNotEqual(first['deliveryId'], second['deliveryId'])
            self.assertEqual(first['items'][0]['eventItemId'], second['items'][0]['eventItemId'])

    def test_unknown_operation_stays_unmatched_then_reconciles_from_the_same_raw(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            raw = raw_delivery([entry()])

            def unknown(item):
                raise UnknownOperation()

            ack = self.receive(unit, raw, unknown)
            self.assertTrue(ack['ack'])
            self.assertEqual(ack['items'][0]['state'], UNMATCHED)
            item_id = ack['items'][0]['itemId']
            self.assertEqual(unit.inbox.state_log(item_id), [(1, RECEIVED), (2, UNMATCHED)])
            self.assertEqual(unit.table_counts()['inbox_item'], 1)
            self.assertEqual(unit.inbox.reconcile(unknown, 2), [])
            self.assertEqual(unit.inbox.state_log(item_id), [(1, RECEIVED), (2, UNMATCHED)])
            offered = []
            self.assertEqual(unit.inbox.reconcile(offered.append, 3), [item_id])
            self.assertEqual(offered[0]['raw'], raw)
            self.assertEqual(unit.inbox.state_log(item_id)[-1], (3, APPLIED))
            self.assertEqual(unit.inbox.reconcile(offered.append, 4), [])

    def test_a_fact_without_an_operation_reference_is_unmatched_and_never_applied(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            called = []
            ack = self.receive(unit, raw_delivery([entry(operation=None)]), called.append)
            self.assertEqual(ack['items'][0]['state'], UNMATCHED)
            self.assertEqual(called, [])
            self.assertEqual(unit.inbox.reconcile(called.append, 2), [])
            self.assertEqual(called, [])

    def test_persist_failure_means_backpressure_and_no_apply(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            real = unit.session.conn
            unit.session.conn = FaultyConnection(real, lambda q, p: 'INSERT INTO inbox_delivery' in q)
            called = []
            with self.assertRaises(Backpressure) as raised:
                self.receive(unit, raw_delivery([entry()]), called.append)
            self.assertEqual(raised.exception.code, 'INBOX_PERSIST_FAILED')
            unit.session.conn = real
            self.assertEqual(called, [])
            self.assertTrue(all(count == 0 for count in unit.table_counts().values()))

    def test_unknown_inbox_commit_means_backpressure_and_no_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            called = []
            with self.unit(tmp) as unit:
                real = unit.session.conn
                unit.session.conn = FaultyConnection(real, lambda q, p: q == 'COMMIT', mode='after')
                with self.assertRaises(Backpressure) as raised:
                    self.receive(unit, raw_delivery([entry()]), called.append)
                self.assertEqual(raised.exception.code, 'INBOX_PERSIST_UNKNOWN')
                unit.session.conn = real
            self.assertEqual(called, [])
            with self.unit(tmp) as unit:
                ack = self.receive(unit, raw_delivery([entry()]), called.append)
                self.assertFalse(ack['newDelivery'])
                self.assertEqual(len(called), 1)
                self.assertEqual(unit.table_counts()['inbox_delivery'], 1)

    def test_full_inflow_budget_means_backpressure_and_no_ack(self):
        budget = spec(inflow=ClassLimit(count=1, bytes=1_000_000, age_ms=10_000_000))
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, budget) as unit:
            self.receive(unit, raw_delivery([entry('k1')]))
            called = []
            before = unit.table_counts()
            with self.assertRaises(Backpressure) as raised:
                self.receive(unit, raw_delivery([entry('k2')], delivery='t-2'), called.append, now_ms=2)
            self.assertEqual(
                (raised.exception.code, raised.exception.budget_class, raised.exception.reason),
                ('INBOX_CAPACITY', 'inflow', 'count'),
            )
            self.assertEqual(called, [])
            self.assertEqual(unit.table_counts(), before)

    def test_full_observation_budget_blocks_new_conflict_evidence_not_the_first_facts(self):
        budget = spec(observation=ClassLimit(count=0, bytes=1_000_000, age_ms=10_000_000))
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, budget) as unit:
            self.receive(unit, raw_delivery([entry('k1')]))
            with self.assertRaises(Backpressure) as raised:
                self.receive(unit, raw_delivery([entry('k1', amount=5)], delivery='t-2'), now_ms=2)
            self.assertEqual((raised.exception.code, raised.exception.budget_class), ('INBOX_CAPACITY', 'observation'))
            self.assertEqual(unit.table_counts()['inbox_item'], 1)
            ack = self.receive(unit, raw_delivery([entry('k2')], delivery='t-3'), now_ms=3)
            self.assertEqual(ack['items'][0]['relation'], FIRST)

    def test_same_event_key_with_a_different_fact_is_kept_as_separate_conflict_evidence(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            first_raw = raw_delivery([entry('k1', amount=100)])
            second_raw = raw_delivery([entry('k1', amount=200)], delivery='t-2')
            first = self.receive(unit, first_raw)
            second = self.receive(unit, second_raw, now_ms=2)
            self.assertEqual(second['items'][0]['relation'], CONFLICT)
            self.assertEqual(first['items'][0]['eventItemId'], second['items'][0]['eventItemId'])
            items = {item['relation']: item for item in unit.inbox.items()}
            self.assertEqual(items[FIRST]['raw'], first_raw)
            self.assertEqual(items[FIRST]['fact']['amountKrw'], 100)
            self.assertEqual(items[CONFLICT]['raw'], second_raw)
            self.assertEqual(items[CONFLICT]['fact']['amountKrw'], 200)
            self.assertEqual(unit.table_counts()['inbox_delivery'], 2)

    def test_different_raw_bytes_of_the_same_fact_are_not_a_conflict(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            self.receive(unit, raw_delivery([entry()]))
            called = []
            ack = self.receive(unit, raw_delivery([entry()], pad='\n'), called.append, now_ms=2)
            self.assertEqual(ack['items'][0]['relation'], SAME_FACT)
            self.assertEqual(ack['items'][0]['state'], DUPLICATE)
            self.assertEqual(called, [])
            self.assertEqual(unit.table_counts()['inbox_delivery'], 2)

    def test_identical_redelivery_adds_nothing_and_is_not_applied_again(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            raw = raw_delivery([entry()])
            called = []
            self.receive(unit, raw, called.append)
            counts = unit.table_counts()
            ack = self.receive(unit, raw, called.append, now_ms=2)
            self.assertFalse(ack['newDelivery'])
            self.assertEqual(len(called), 1)
            self.assertEqual(unit.table_counts(), counts)

    def test_a_lookup_failure_keeps_the_raw_and_withholds_the_ack(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            raw = raw_delivery([entry()])

            def broken(_raw):
                raise RuntimeError('fixture lookup down')

            with self.assertRaises(RuntimeError):
                self.receive(unit, raw, lookup_fn=broken)
            counts = unit.table_counts()
            self.assertEqual((counts['inbox_delivery'], counts['inbox_item']), (1, 0))
            ack = self.receive(unit, raw, now_ms=2)
            self.assertTrue(ack['ack'])
            self.assertEqual(unit.table_counts()['inbox_delivery'], 1)

    def test_a_failed_apply_withholds_the_ack_and_redelivery_applies_it(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            raw = raw_delivery([entry()])

            def failing(item):
                raise RuntimeError('fixture apply failed')

            with self.assertRaises(RuntimeError):
                self.receive(unit, raw, failing)
            self.assertEqual(unit.inbox.items()[0]['state'], RECEIVED)
            called = []
            ack = self.receive(unit, raw, called.append, now_ms=2)
            self.assertEqual(ack['items'][0]['state'], APPLIED)
            self.assertEqual(len(called), 1)

    def test_state_survives_a_process_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            def unknown(item):
                raise UnknownOperation()

            with self.unit(tmp) as unit:
                raw = raw_delivery([entry()])
                self.receive(unit, raw, unknown)
            self.cluster.kill()
            self.cluster.start()
            with self.unit(tmp) as unit:
                item = unit.inbox.items()[0]
                self.assertEqual((item['state'], item['raw']), (UNMATCHED, raw))

    def test_an_alias_truncation_collision_is_refused_by_the_durable_table(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            fixed = lambda _scope, _key: 'cd' * 16  # noqa: E731
            store = SqlAliasStore(unit.session.conn)
            with unit.session.transaction():
                resolve_alias(store, 'scope-1', 'k1', fixed)
            with self.assertRaises(AliasConflict):
                with unit.session.transaction():
                    resolve_alias(store, 'scope-1', 'k2', fixed)
            self.assertEqual(unit.table_counts()['event_alias'], 1)
            with unit.session.transaction():
                self.assertEqual(resolve_alias(store, 'scope-1', 'k1', fixed), 'cd' * 16)


class OutboxTests(_ClusterCase):
    def test_pending_intents_survive_a_process_kill(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.unit(tmp) as unit:
                unit.apply(command('c1', slot='0'), 1)
                unit.apply(command('c2', slot='1'), 2)
            self.cluster.kill()
            self.cluster.start()
            with self.unit(tmp) as unit:
                pending = unit.outbox.pending()
                self.assertEqual([item['intentId'] for item in pending], ['intent-c1', 'intent-c2'])
                self.assertEqual({item['state'] for item in pending}, {'PENDING'})
                self.assertEqual({item['kind'] for item in pending}, {'FIXTURE_NOT_DISPATCHED'})

    def test_the_attempt_is_committed_before_the_dispatcher_runs(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            unit.apply(command(), 1)
            seen = {}

            def dispatcher(call):
                seen['attempting'] = self.side_count(tmp, 'outbox_attempt', "phase = 'ATTEMPTING'")
                seen['outcome'] = self.side_count(tmp, 'outbox_attempt', "phase = 'OUTCOME'")
                seen['call'] = call
                return {'dispatched': False, 'kind': 'fixture-not-sent'}

            unit.outbox.record_attempt('intent-c1', 2, dispatcher=dispatcher)
            self.assertEqual((seen['attempting'], seen['outcome']), (1, 0))
            self.assertEqual(seen['call']['intentId'], 'intent-c1')
            self.assertEqual(self.side_count(tmp, 'outbox_attempt'), 2)

    def test_the_default_dispatcher_calls_nothing_and_leaves_the_intent_pending(self):
        self.assertEqual(fixture_dispatcher({}), {'dispatched': False, 'kind': FIXTURE_DISPATCH_KIND})
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            unit.apply(command(), 1)
            result = unit.outbox.record_attempt('intent-c1', 2)
            self.assertEqual(result['state'], 'NOT_DISPATCHED')
            self.assertEqual([item['state'] for item in unit.outbox.pending()], ['NOT_DISPATCHED'])

    def test_a_dispatched_outcome_is_terminal_and_never_sent_twice(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            unit.apply(command(), 1)
            sent = []

            def dispatcher(call):
                sent.append(call['intentId'])
                return {'dispatched': True, 'kind': 'fixture-sent'}

            self.assertEqual(unit.outbox.record_attempt('intent-c1', 2, dispatcher=dispatcher)['state'], 'DISPATCHED')
            again = unit.outbox.record_attempt('intent-c1', 3, dispatcher=dispatcher)
            self.assertEqual((again['duplicate'], again['state']), (True, 'DISPATCHED'))
            self.assertEqual(sent, ['intent-c1'])
            self.assertEqual(unit.outbox.pending(), [])

    def test_a_dispatcher_exception_is_unknown_and_the_retry_keeps_the_identity(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            unit.apply(command(), 1)

            def broken(call):
                raise ConnectionError('fixture wire cut')

            self.assertEqual(unit.outbox.record_attempt('intent-c1', 2, dispatcher=broken)['state'], 'UNKNOWN')
            self.assertEqual(unit.outbox.status('intent-c1'), {'state': 'UNKNOWN', 'attempts': 1})
            calls = []

            def dispatcher(call):
                calls.append(call)
                return {'dispatched': True, 'kind': 'fixture-confirmed'}

            retry = unit.outbox.record_attempt('intent-c1', 3, dispatcher=dispatcher)
            self.assertEqual((retry['budgetClass'], retry['state']), ('recovery', 'DISPATCHED'))
            self.assertEqual((calls[0]['intentId'], calls[0]['previousState'], calls[0]['attemptNo']),
                             ('intent-c1', 'UNKNOWN', 2))

    def test_a_malformed_dispatcher_result_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            unit.apply(command(), 1)
            self.assertEqual(
                unit.outbox.record_attempt('intent-c1', 2, dispatcher=lambda call: 'sent')['state'], 'UNKNOWN',
            )

    def test_an_attempt_without_an_outcome_stays_attempting_across_a_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.unit(tmp) as unit:
                unit.apply(command(), 1)

                def crash(call):
                    raise KeyboardInterrupt()

                with self.assertRaises(KeyboardInterrupt):
                    unit.outbox.record_attempt('intent-c1', 2, dispatcher=crash)
            self.cluster.kill()
            self.cluster.start()
            with self.unit(tmp) as unit:
                self.assertEqual(unit.outbox.status('intent-c1'), {'state': 'ATTEMPTING', 'attempts': 1})
                seen = []
                unit.outbox.record_attempt('intent-c1', 3, dispatcher=lambda call: seen.append(call) or {'dispatched': False, 'kind': 'x'})
                self.assertEqual(seen[0]['previousState'], 'ATTEMPTING')

    def test_an_unrecorded_outcome_is_not_reported_as_sent_or_not_sent(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            unit.apply(command(), 1)
            real = unit.session.conn
            unit.session.conn = FaultyConnection(
                real, lambda q, p: 'INSERT INTO outbox_attempt' in q and p is not None and p[2] == 'OUTCOME',
            )
            with self.assertRaises(StoreError) as raised:
                unit.outbox.record_attempt('intent-c1', 2, dispatcher=lambda call: {'dispatched': True, 'kind': 'fixture-sent'})
            self.assertEqual(raised.exception.code, 'OUTBOX_OUTCOME_NOT_RECORDED')
            unit.session.conn = real
            self.assertEqual(unit.outbox.status('intent-c1'), {'state': 'ATTEMPTING', 'attempts': 1})

    def test_an_unknown_intent_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            with self.assertRaises(StoreError) as raised:
                unit.outbox.record_attempt('intent-missing', 1)
            self.assertEqual(raised.exception.code, 'UNKNOWN_INTENT')

    def test_a_full_completion_budget_stops_the_attempt_before_dispatch(self):
        budget = spec(completion=ClassLimit(count=0, bytes=1_000_000, age_ms=10_000_000))
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp, budget) as unit:
            unit.apply(command(), 1)
            called = []
            with self.assertRaises(Backpressure) as raised:
                unit.outbox.record_attempt('intent-c1', 2, dispatcher=lambda call: called.append(call))
            self.assertEqual(raised.exception.code, 'OUTBOX_CAPACITY')
            self.assertEqual(called, [])
            self.assertEqual(unit.table_counts()['outbox_attempt'], 0)


if __name__ == '__main__':
    unittest.main()
