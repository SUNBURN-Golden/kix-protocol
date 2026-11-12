"""On-sale admission layer on the adopted local PostgreSQL 17.11.

Needs /usr/lib/postgresql/17/bin/{postgres,initdb} and psycopg. A missing
backend fails the run loudly; nothing here skips. Every capacity, TTL, budget
number and key here is a synthetic fixture, not product policy (contract §10);
the signing key is generated per run and never committed. Not wired into CI.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import psycopg

from readiness.store import StoreError

from durable import PINNED_POSTGRES
from durable.budgets import CLASSES, BudgetSpec, ClassLimit
from durable.cluster import PinnedPostgresCluster
from durable.schema import store_key

import onsale
from onsale import tokens
from onsale.model import (
    AdmitRequest, EnqueueRequest, GaConfigError, OnsaleLimits, ReissueRequest,
    command_id,
)
from onsale.router import HintRouter
from onsale.room import WaitingRoom
from onsale.schema import ONSALE_CRC_TABLES
from onsale.unit import AdmissionUnit

OBSERVED = {}

# Fixtures only. Not an approved limit of any kind.
BIG = ClassLimit(count=256, bytes=10_000_000, age_ms=10_000_000)
SHOW = 'fixture-show'
EPOCH = 3
MODE = 'GeneralAdmissionSharded'
KEY_VERSION = 'fixture-v1'


def spec(**override):
    per_class = {name: BIG for name in CLASSES}
    per_class.update(override)
    return BudgetSpec(**per_class)


def limits(**override):
    values = dict(
        token_ttl_ms=1_000, hint_ttl_ms=500, max_queue_wait_ms=5_000,
        max_outstanding_tokens=16, max_sessions=16,
        group_max_count=4, group_max_bytes=1_000, group_max_wait_ms=50,
    )
    values.update(override)
    return OnsaleLimits(**values)


def enqueue_request(nonce='n1', shard='s1', ccid='c1', principal='buyer-1'):
    return EnqueueRequest(SHOW, EPOCH, MODE, principal, ccid, nonce, shard)


def admit_request(token, ccid='a1', principal='buyer-1'):
    return AdmitRequest(SHOW, EPOCH, MODE, principal, ccid, token)


def token_of(result):
    return json.loads(result['first_result'])['token']


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
        cls.root = tempfile.mkdtemp(prefix='kixonsale-')
        cls.cluster = PinnedPostgresCluster(cls.root)
        cls.cluster.start()
        cls.key = os.urandom(32)  # fixture key, generated per run, never committed
        OBSERVED['version'] = cls.cluster.version
        OBSERVED['settings'] = cls.cluster.settings

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        shutil.rmtree(cls.root, ignore_errors=True)

    @contextmanager
    def unit(self, directory, budget=None, lim=None, key=None, key_version=KEY_VERSION):
        unit = AdmissionUnit(self.cluster, directory, budget or spec(), lim or limits(),
                             key if key is not None else self.key, key_version)
        try:
            yield unit
        finally:
            unit.close()

    @contextmanager
    def configured(self, directory, capacities=None, budget=None, lim=None):
        capacities = capacities if capacities is not None else {'s1': 2, 's2': 2}
        with self.unit(directory, budget=budget, lim=lim) as unit:
            total = sum(capacities.values())
            result = unit.configure_ga(SHOW, EPOCH, MODE, 1, total, capacities, 1)
            self.assertEqual(result['outcome'], 'new_success')
            yield unit

    @contextmanager
    def fault(self, unit, predicate, mode='before'):
        real = unit.session.session.conn
        unit.session.session.conn = FaultyConnection(real, predicate, mode)
        try:
            yield
        finally:
            unit.session.session.conn = real

    def side(self, directory, query, params=None):
        """Run a query through a second connection: committed rows only."""
        conn = self.cluster.connect()
        try:
            conn.execute('SET search_path TO d%s' % store_key(directory))
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def side_count(self, directory, table, where='1 = 1'):
        return int(self.side(directory, 'SELECT COUNT(*) FROM %s WHERE %s' % (table, where))[0][0])

    def side_exec(self, directory, statement, params=None):
        conn = self.cluster.connect()
        try:
            conn.execute('SET search_path TO d%s' % store_key(directory))
            conn.execute(statement, params)
        finally:
            conn.close()

    def remaining(self, directory, shard='s1'):
        return int(self.side(
            directory,
            'SELECT remaining FROM onsale_ga_shard WHERE show_id = %s AND epoch = %s '
            'AND shard_id = %s', (SHOW, EPOCH, shard),
        )[0][0])

    def enter_and_admit(self, unit, principal, ccid, nonce, shard='s1',
                        admit_ccid=None, now=100, admit_now=200):
        enq = unit.enqueue(enqueue_request(nonce=nonce, shard=shard, ccid=ccid,
                                           principal=principal), now)
        self.assertEqual(enq['outcome'], 'new_success')
        admit = unit.admit(admit_request(token_of(enq), ccid=admit_ccid or ('a-' + ccid),
                                         principal=principal), admit_now)
        return enq, admit


class ClusterTests(_ClusterCase):
    def test_cluster_is_the_pinned_local_postgres_on_a_unix_socket(self):
        self.assertIn(PINNED_POSTGRES, self.cluster.version)
        settings = self.cluster.settings
        self.assertEqual(settings['listen_addresses']['setting'], '')
        for name in ('fsync', 'full_page_writes', 'synchronous_commit', 'data_checksums'):
            self.assertEqual(settings[name]['setting'], 'on')

    def test_package_flags_are_false_and_fixture_label_is_set(self):
        self.assertTrue(onsale.LOCAL_ONSALE_FIXTURE_ONLY)
        for name in ('PROTOCOL_TRUTH', 'PRODUCTION_CONFORMANCE', 'PRODUCTION_READINESS',
                     'PRODUCTION_ENDPOINT', 'FUNDS_EXECUTED', 'CHAIN_WRITER',
                     'DELEGATED_EXECUTION'):
            self.assertIs(getattr(onsale, name), False, name)


class ConfigureTests(_ClusterCase):
    def test_ga_creation_validates_the_sum_and_pins_the_config(self):
        with tempfile.TemporaryDirectory() as tmp, self.unit(tmp) as unit:
            with self.assertRaises(GaConfigError):
                unit.configure_ga(SHOW, EPOCH, MODE, 1, 5, {'s1': 2, 's2': 2}, 1)
            self.assertEqual(unit.table_counts()['onsale_ga_config'], 0)
            result = unit.configure_ga(SHOW, EPOCH, MODE, 1, 4, {'s1': 2, 's2': 2}, 1)
            self.assertEqual(result['outcome'], 'new_success')
            self.assertEqual(unit.table_counts()['onsale_ga_config'], 1)
            self.assertEqual(unit.table_counts()['onsale_ga_shard'], 2)
            self.assertEqual(self.remaining(tmp, 's1'), 2)
            self.assertEqual(self.remaining(tmp, 's2'), 2)

    def test_identical_reconfigure_is_idempotent_and_different_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            before = unit.table_counts()
            again = unit.configure_ga(SHOW, EPOCH, MODE, 1, 4, {'s1': 2, 's2': 2}, 5)
            self.assertEqual(again['outcome'], 'replayed')
            self.assertEqual(unit.table_counts(), before)
            with self.assertRaises(StoreError) as refused:
                unit.configure_ga(SHOW, EPOCH, MODE, 1, 6, {'s1': 3, 's2': 3}, 5)
            self.assertEqual(refused.exception.code, 'JOURNAL_RECORD')
            with self.assertRaises(StoreError):
                unit.configure_ga(SHOW, EPOCH, MODE, 2, 4, {'s1': 2, 's2': 2}, 5)
            self.assertEqual(unit.table_counts(), before)

    def test_limits_and_key_version_are_pinned_at_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.configured(tmp):
                pass
            with self.assertRaises(StoreError) as bad_limits:
                with self.unit(tmp, lim=limits(token_ttl_ms=9_999)):
                    pass
            self.assertEqual(bad_limits.exception.code, 'JOURNAL_RECORD')
            with self.assertRaises(StoreError) as bad_version:
                with self.unit(tmp, key_version='other-version'):
                    pass
            self.assertEqual(bad_version.exception.code, 'JOURNAL_RECORD')
            with self.unit(tmp, key=os.urandom(32)) as unit:
                self.assertEqual(unit.table_counts()['onsale_ga_config'], 1)

    def test_budget_spec_is_pinned_at_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.configured(tmp):
                pass
            with self.assertRaises(StoreError) as refused:
                with self.unit(tmp, budget=spec(inflow=ClassLimit(count=1, bytes=1, age_ms=1))):
                    pass
            self.assertEqual(refused.exception.code, 'JOURNAL_RECORD')

    def test_constructor_requires_every_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                AdmissionUnit(self.cluster, tmp, spec(), limits(), b'', KEY_VERSION)
            with self.assertRaises(ValueError):
                AdmissionUnit(self.cluster, tmp, spec(), limits(), self.key, '')
            with self.assertRaises(ValueError):
                AdmissionUnit(self.cluster, tmp, spec(), None, self.key, KEY_VERSION)
            with self.assertRaises(TypeError):
                AdmissionUnit(self.cluster, tmp, spec(), limits(), self.key)


class HappyPathTests(_ClusterCase):
    def test_waiting_room_enter_admit_and_bounded_views(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            room = WaitingRoom(unit, HintRouter('capacity_aware', random.Random(11)))
            enq = room.enter(show_id=SHOW, inventory_epoch=EPOCH, inventory_mode=MODE,
                             principal='buyer-1', client_command_id='c1', nonce='n1', now_ms=100)
            self.assertEqual(enq['outcome'], 'new_success')
            document = token_of(enq)
            self.assertTrue(tokens.verify(document, self.key))
            artifact = room.artifact(SHOW, EPOCH, 150)
            self.assertEqual(artifact['waiting'], 1)
            self.assertEqual(artifact['admitted'], 0)
            admit = room.admit(show_id=SHOW, inventory_epoch=EPOCH, inventory_mode=MODE,
                               principal='buyer-1', client_command_id='a1',
                               token=document, now_ms=200)
            self.assertEqual(admit['outcome'], 'new_success')
            body = json.loads(admit['first_result'])
            view = room.session(body['sessionId'], 'buyer-1')
            self.assertEqual(view['state'], 'ADMITTED')
            self.assertEqual(view['shardId'], document['shardId'])
            artifact = room.artifact(SHOW, EPOCH, 250)
            self.assertEqual(artifact['waiting'], 0)
            self.assertEqual(artifact['admitted'], 1)
            self.assertGreaterEqual(artifact['artifactVersion'], 1)

    def test_atomic_commit_writes_every_row_together(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            enq, admit = self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            self.assertEqual(admit['outcome'], 'new_success')
            counts = unit.table_counts()
            self.assertEqual(counts['onsale_command'], 2)
            self.assertEqual(counts['onsale_queue_ticket'], 1)
            self.assertEqual(counts['onsale_token'], 1)
            self.assertEqual(counts['onsale_token_state'], 2)
            self.assertEqual(counts['onsale_session'], 1)
            self.assertEqual(counts['onsale_evidence'], 2)
            self.assertEqual(counts['ledger'], 2)
            self.assertEqual(self.remaining(tmp), 1)
            rows = self.side(tmp, 'SELECT entry_id, is_open FROM ledger ORDER BY entry_id')
            self.assertTrue(all(is_open is False for _, is_open in rows))
            states = self.side(tmp, 'SELECT state FROM onsale_token_state ORDER BY seq')
            self.assertEqual([state for (state,) in states], ['ISSUED', 'CONSUMED'])

    def test_evidence_rows_carry_every_contract_field(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            rows = self.side(
                tmp,
                'SELECT kind, queue_ticket_id, position_identity, sequence, shard_id, '
                'reason, issued_at_ms, expires_at_ms, outcome, command_id, at_ms '
                'FROM onsale_evidence ORDER BY at_ms, kind',
            )
            self.assertEqual(len(rows), 2)
            for row in rows:
                for value in row:
                    self.assertIsNotNone(value)
            self.assertEqual(rows[0][0], 'enqueue')
            self.assertEqual(rows[1][0], 'admit')
            self.assertEqual(rows[1][8], 'new_success')
            self.assertEqual(rows[0][1], rows[1][1])
            self.assertEqual(rows[0][2], rows[1][2])

    def test_ticket_sequence_is_monotone_and_position_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            first = unit.enqueue(enqueue_request(ccid='c1', principal='buyer-1', nonce='n1'), 100)
            second = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 110)
            one = json.loads(first['first_result'])
            two = json.loads(second['first_result'])
            self.assertEqual((one['queueSeq'], two['queueSeq']), (1, 2))
            self.assertNotEqual(one['queuePositionIdentity'], two['queuePositionIdentity'])
            rows = self.side(tmp, 'SELECT seq FROM onsale_queue_ticket ORDER BY seq')
            self.assertEqual([seq for (seq,) in rows], [1, 2])

    def test_artifact_is_coarse_and_versioned_without_seat_or_user_labels(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            first = unit.queue_artifact(SHOW, EPOCH, 300)
            self.assertEqual(set(first), {
                'localOnsaleFixtureOnly', 'protocolTruth', 'productionConformance',
                'productionReadiness', 'productionEndpoint', 'fundsExecuted',
                'chainWriter', 'delegatedExecution', 'artifactVersion',
                'sourceCommitPosition', 'showId', 'inventoryEpoch', 'waiting', 'admitted',
            })
            unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 310)
            second = unit.queue_artifact(SHOW, EPOCH, 320)
            self.assertGreater(second['artifactVersion'], first['artifactVersion'])
            text = json.dumps(second)
            self.assertNotIn('buyer-', text)
            self.assertNotIn('seat', text.lower())

    def test_session_view_is_bounded_and_authorized(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            _, admit = self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            session_id = json.loads(admit['first_result'])['sessionId']
            view = unit.session_view(session_id, 'buyer-1')
            self.assertEqual(set(view), {
                'localOnsaleFixtureOnly', 'protocolTruth', 'productionConformance',
                'productionReadiness', 'productionEndpoint', 'fundsExecuted',
                'chainWriter', 'delegatedExecution', 'sessionId', 'commandId',
                'showId', 'inventoryEpoch', 'shardId', 'createdAtMs', 'state',
            })
            with self.assertRaises(StoreError) as forbidden:
                unit.session_view(session_id, 'buyer-2')
            self.assertEqual(forbidden.exception.code, 'FORBIDDEN')
            self.assertIsNone(unit.session_view('sess-missing', 'buyer-1'))

    def test_read_result_is_authorized_and_durable(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            enq, _ = self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            cmd = command_id(SHOW, EPOCH, MODE, 'buyer-1', 'c1')
            read = unit.read_result(cmd, 'buyer-1')
            self.assertEqual(read['firstResult'], enq['first_result'])
            self.assertEqual(read['outcome'], 'new_success')
            with self.assertRaises(StoreError) as forbidden:
                unit.read_result(cmd, 'buyer-2')
            self.assertEqual(forbidden.exception.code, 'FORBIDDEN')
            self.assertIsNone(unit.read_result('cmd-missing', 'buyer-1'))


class RetryAndUnknownTests(_ClusterCase):
    def test_replay_after_reopen_returns_the_first_result_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.configured(tmp) as unit:
                enq, admit = self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            with self.unit(tmp) as unit:
                before = unit.table_counts()
                again = unit.enqueue(enqueue_request(), 999)
                self.assertEqual(again['outcome'], 'replayed')
                self.assertEqual(again['first_result'], enq['first_result'])
                again_admit = unit.admit(admit_request(token_of(enq), ccid='a-c1'), 999)
                self.assertEqual(again_admit['outcome'], 'replayed')
                self.assertEqual(again_admit['first_result'], admit['first_result'])
                self.assertEqual(unit.table_counts(), before)
                self.assertEqual(self.remaining(tmp), 1)

    def test_conflicting_payload_is_retained_once(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            unit.enqueue(enqueue_request(), 100)
            conflict = unit.enqueue(enqueue_request(nonce='different'), 110)
            self.assertEqual(conflict['outcome'], 'conflict_retained')
            self.assertEqual(self.side_count(tmp, 'observation'), 1)
            again = unit.enqueue(enqueue_request(nonce='different'), 120)
            self.assertEqual(again['outcome'], 'conflict_retained')
            self.assertEqual(self.side_count(tmp, 'observation'), 1)
            self.assertEqual(self.side_count(tmp, 'onsale_queue_ticket'), 1)

    def test_lost_ack_on_admit_is_unknown_then_read_back_as_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.configured(tmp) as unit:
                enq = unit.enqueue(enqueue_request(), 100)
                with self.fault(unit, lambda q, p: q == 'COMMIT', mode='after'):
                    result = unit.admit(admit_request(token_of(enq)), 200)
                self.assertEqual(result['outcome'], 'unknown')
                self.assertEqual(result['first_result'], '')
                with self.assertRaises(StoreError) as closed:
                    unit.admit(admit_request(token_of(enq)), 210)
                self.assertEqual(closed.exception.code, 'JOURNAL_CLOSED')
            with self.unit(tmp) as unit:
                again = unit.admit(admit_request(token_of(enq)), 300)
                self.assertEqual(again['outcome'], 'replayed')
                self.assertEqual(self.remaining(tmp), 1)
                self.assertEqual(self.side_count(tmp, 'onsale_session'), 1)

    def test_lost_ack_on_enqueue_is_unknown_then_read_back_as_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.configured(tmp) as unit:
                with self.fault(unit, lambda q, p: q == 'COMMIT', mode='after'):
                    result = unit.enqueue(enqueue_request(), 100)
                self.assertEqual(result['outcome'], 'unknown')
            with self.unit(tmp) as unit:
                again = unit.enqueue(enqueue_request(), 200)
                self.assertEqual(again['outcome'], 'replayed')
                self.assertEqual(self.side_count(tmp, 'onsale_queue_ticket'), 1)

    def test_process_kill_preserves_first_result_and_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.configured(tmp) as unit:
                enq, admit = self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            self.cluster.kill()
            self.cluster.start()
            with self.unit(tmp) as unit:
                again = unit.admit(admit_request(token_of(enq), ccid='a-c1'), 500)
                self.assertEqual((again['outcome'], again['first_result']),
                                 ('replayed', admit['first_result']))
                self.assertEqual(self.remaining(tmp), 1)
                self.assertEqual(self.side_count(tmp, 'onsale_evidence'), 2)

    def test_injected_midwrite_failure_leaves_no_partial_rows(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            with self.fault(unit, lambda q, p: 'INSERT INTO onsale_session' in q):
                result = unit.admit(admit_request(token_of(enq)), 200)
            self.assertEqual(result['outcome'], 'error')
            self.assertEqual(self.remaining(tmp), 2)
            self.assertEqual(self.side_count(tmp, 'onsale_session'), 0)
            self.assertEqual(self.side_count(tmp, 'onsale_command'), 1)
            self.assertEqual(self.side_count(tmp, 'onsale_token_state'), 1)
            retry = unit.admit(admit_request(token_of(enq)), 210)
            self.assertEqual(retry['outcome'], 'new_success')

    def test_second_writer_on_the_same_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp):
            with self.assertRaises(StoreError) as locked:
                AdmissionUnit(self.cluster, tmp, spec(), limits(), self.key, KEY_VERSION)
            self.assertEqual(locked.exception.code, 'JOURNAL_LOCKED')


class CapacityAndHintTests(_ClusterCase):
    def test_admissions_never_exceed_shard_capacity(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 2}) as unit:
            outcomes = []
            for index in range(4):
                principal = 'buyer-%d' % index
                enq = unit.enqueue(enqueue_request(ccid='c%d' % index, principal=principal,
                                                   nonce='n%d' % index), 100 + index)
                self.assertEqual(enq['outcome'], 'new_success')
                admit = unit.admit(admit_request(token_of(enq), ccid='a%d' % index,
                                                 principal=principal), 200 + index)
                outcomes.append(admit['outcome'])
            self.assertEqual(outcomes.count('new_success'), 2)
            self.assertEqual(outcomes.count('business_rejected'), 2)
            self.assertEqual(self.remaining(tmp), 0)
            self.assertEqual(self.side_count(
                tmp, 'onsale_evidence', "kind = 'admit' AND outcome = 'new_success'"), 2)
            self.assertEqual(self.side_count(tmp, 'onsale_session'), 2)

    def test_threaded_admissions_never_exceed_shard_capacity(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 3}) as unit:
            documents = []
            for index in range(8):
                enq = unit.enqueue(enqueue_request(ccid='c%d' % index,
                                                   principal='buyer-%d' % index,
                                                   nonce='n%d' % index), 100 + index)
                documents.append((index, token_of(enq)))

            def attempt(item):
                index, document = item
                return unit.admit(admit_request(document, ccid='a%d' % index,
                                                principal='buyer-%d' % index), 300)

            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(attempt, documents))
            self.assertEqual(sum(r['outcome'] == 'new_success' for r in results), 3)
            self.assertEqual(self.remaining(tmp), 0)
            self.assertEqual(self.side_count(tmp, 'onsale_session'), 3)
            self.assertEqual(self.side_count(
                tmp, 'onsale_evidence', "kind = 'admit' AND outcome = 'new_success'"), 3)

    def test_shards_enforce_capacity_independently(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 1, 's2': 1}) as unit:
            _, first = self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1', shard='s1')
            self.assertEqual(first['outcome'], 'new_success')
            _, second = self.enter_and_admit(unit, 'buyer-2', 'c2', 'n2', shard='s2',
                                             now=110, admit_now=210)
            self.assertEqual(second['outcome'], 'new_success')
            self.assertEqual(self.remaining(tmp, 's1'), 0)
            self.assertEqual(self.remaining(tmp, 's2'), 0)
            self.assertEqual(self.side_count(tmp, 'onsale_ga_shard'), 2)
            self.assertEqual(self.side_count(tmp, 'onsale_ga_config'), 1)

    def test_sold_out_commit_returns_a_versioned_negative_hint(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 1}) as unit:
            self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            enq = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 110)
            admit = unit.admit(admit_request(token_of(enq), ccid='a2', principal='buyer-2'), 210)
            self.assertEqual(admit['outcome'], 'business_rejected')
            hint = admit['sold_hint']
            self.assertEqual(hint['reason'], 'SOLD_OUT')
            self.assertEqual(hint['inventoryEpoch'], EPOCH)
            self.assertEqual(hint['version'], 1)
            self.assertEqual(hint['expiresAtMs'], 210 + limits().hint_ttl_ms)
            self.assertIn('sourceCommitPosition', hint)
            stored = unit.negative_hint(SHOW, EPOCH, 's1', 220)
            self.assertEqual(stored, hint)
            self.assertIsNone(unit.negative_hint(SHOW, EPOCH, 's1', 210 + limits().hint_ttl_ms))
            self.assertIsNone(unit.negative_hint(SHOW, EPOCH + 1, 's1', 220))

    def test_optimistic_routing_is_rechecked_at_commit(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 1}) as unit:
            self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            fabricated = [{'shardId': 's1', 'observedRemaining': 99,
                           'outstandingUnexpiredTokens': 0, 'effectiveRemaining': 99,
                           'negativeHint': None}]
            router = HintRouter('capacity_aware', random.Random(5))
            self.assertEqual(router.route(fabricated, inventory_epoch=EPOCH, now_ms=300), 's1')
            enq = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 300)
            admit = unit.admit(admit_request(token_of(enq), ccid='a2', principal='buyer-2'), 310)
            self.assertEqual(admit['outcome'], 'business_rejected')
            self.assertEqual(self.remaining(tmp), 0)

    def test_expired_hint_is_not_a_permanent_sold_verdict(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 1}) as unit:
            self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            enq = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 110)
            unit.admit(admit_request(token_of(enq), ccid='a2', principal='buyer-2'), 210)
            late = 210 + limits().hint_ttl_ms + 1
            observations = unit.shard_hints(SHOW, EPOCH, late)
            router = HintRouter('capacity_aware', random.Random(5))
            self.assertIsNone(router.route(observations, inventory_epoch=EPOCH, now_ms=late))
            self.assertIsNone(unit.negative_hint(SHOW, EPOCH, 's1', late))
            self.assertEqual(self.remaining(tmp), 0)

    def test_session_cap_refuses_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 4}, lim=limits(max_sessions=1)) as unit:
            self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
            enq = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 110)
            before = unit.table_counts()
            admit = unit.admit(admit_request(token_of(enq), ccid='a2', principal='buyer-2'), 210)
            self.assertEqual(admit['outcome'], 'capacity')
            self.assertEqual(admit['capacity_reason'], 'sessions')
            self.assertEqual(unit.table_counts(), before)
            self.assertEqual(self.remaining(tmp), 3)

    def test_outstanding_token_cap_refuses_enqueue(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 4}, lim=limits(max_outstanding_tokens=1)) as unit:
            unit.enqueue(enqueue_request(), 100)
            before = unit.table_counts()
            refused = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 110)
            self.assertEqual(refused['outcome'], 'capacity')
            self.assertEqual(refused['capacity_reason'], 'outstanding_tokens')
            self.assertEqual(unit.table_counts(), before)

    def test_queue_wait_and_ttl_bounds_are_enforced_at_commit(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 4}, lim=limits(max_queue_wait_ms=50)) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            late = unit.admit(admit_request(token_of(enq)), 200)
            self.assertEqual(late['outcome'], 'business_rejected')
            self.assertEqual(json.loads(late['first_result'])['reason'], 'QUEUE_WAIT')
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 4}) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            expired = unit.admit(admit_request(token_of(enq)), 100 + limits().token_ttl_ms)
            self.assertEqual(expired['outcome'], 'business_rejected')
            self.assertEqual(json.loads(expired['first_result'])['reason'], 'TOKEN_EXPIRED')

    def test_epoch_isolation_binds_tokens_and_hints(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 2}) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            unit.configure_ga(SHOW, EPOCH + 1, MODE, 1, 2, {'s1': 2}, 110)
            cross = unit.admit(AdmitRequest(SHOW, EPOCH + 1, MODE, 'buyer-1', 'a1',
                                            token_of(enq)), 200)
            self.assertEqual(cross['outcome'], 'business_rejected')
            self.assertEqual(json.loads(cross['first_result'])['reason'], 'TOKEN_BINDING')
            self.assertEqual(self.remaining(tmp), 2)


class ReissueTests(_ClusterCase):
    def test_reissue_preserves_rank_and_identity(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            first = unit.enqueue(enqueue_request(ccid='c1', principal='buyer-1', nonce='n1'), 100)
            unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 110)
            one = json.loads(first['first_result'])
            reissue = unit.reissue(ReissueRequest(
                SHOW, EPOCH, MODE, 'buyer-1', 'r1', one['queueTicketId'], 'n1', 'n9', 's2'), 300)
            self.assertEqual(reissue['outcome'], 'new_success')
            body = json.loads(reissue['first_result'])
            self.assertEqual(body['queueTicketId'], one['queueTicketId'])
            self.assertEqual(body['queuePositionIdentity'], one['queuePositionIdentity'])
            self.assertEqual(body['token']['shardId'], 's2')
            rows = self.side(tmp, 'SELECT seq, position_identity FROM onsale_queue_ticket '
                                  'WHERE queue_ticket_id = %s', (one['queueTicketId'],))
            self.assertEqual(rows[0][0], 1)
            self.assertEqual(rows[0][1], one['queuePositionIdentity'])
            evidence = self.side(tmp, "SELECT old_shard_id, shard_id, sequence FROM onsale_evidence "
                                      "WHERE kind = 'reissue'")
            self.assertEqual(evidence, [('s1', 's2', 2)])
            self.assertEqual(self.remaining(tmp, 's1'), 2)
            self.assertEqual(self.remaining(tmp, 's2'), 2)

    def test_old_and_new_token_race_consumes_capacity_once(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 1, 's2': 1}) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            one = json.loads(enq['first_result'])
            reissue = unit.reissue(ReissueRequest(
                SHOW, EPOCH, MODE, 'buyer-1', 'r1', one['queueTicketId'], 'n1', 'n9', 's2'), 300)
            new_token = token_of(reissue)
            old_attempt = unit.admit(admit_request(token_of(enq), ccid='a-old'), 310)
            self.assertEqual(old_attempt['outcome'], 'business_rejected')
            self.assertEqual(json.loads(old_attempt['first_result'])['reason'], 'TOKEN_REPLACED')
            new_attempt = unit.admit(admit_request(new_token, ccid='a-new'), 320)
            self.assertEqual(new_attempt['outcome'], 'new_success')
            self.assertEqual(self.remaining(tmp, 's1'), 1)
            self.assertEqual(self.remaining(tmp, 's2'), 0)
            self.assertEqual(self.side_count(
                tmp, 'onsale_evidence', "kind = 'admit' AND outcome = 'new_success'"), 1)
            self.assertEqual(self.side_count(tmp, 'onsale_session'), 1)

    def test_reissue_chain_keeps_the_original_position(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            one = json.loads(enq['first_result'])
            ticket = one['queueTicketId']
            second = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', 'r1',
                                                 ticket, 'n1', 'n2', 's2'), 200)
            third = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', 'r2',
                                                ticket, 'n2', 'n3', 's1'), 300)
            for result in (second, third):
                body = json.loads(result['first_result'])
                self.assertEqual(body['queuePositionIdentity'], one['queuePositionIdentity'])
            states = self.side(tmp, 'SELECT state FROM onsale_token_state ORDER BY token_id, seq')
            self.assertEqual([state for (state,) in states].count('REPLACED'), 2)
            self.assertEqual(self.side_count(tmp, 'onsale_queue_ticket'), 1)
            final = unit.admit(admit_request(token_of(third), ccid='a1'), 310)
            self.assertEqual(final['outcome'], 'new_success')

    def test_reissue_refusals(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            one = json.loads(enq['first_result'])
            ticket = one['queueTicketId']
            consumed = unit.admit(admit_request(token_of(enq)), 200)
            self.assertEqual(consumed['outcome'], 'new_success')
            refused = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', 'r1',
                                                  ticket, 'n1', 'n2', 's2'), 300)
            self.assertEqual(json.loads(refused['first_result'])['reason'], 'REISSUE_NOT_ISSUED')
            unknown = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', 'r2',
                                                  'qt-missing', 'n1', 'n2', 's2'), 300)
            self.assertEqual(json.loads(unknown['first_result'])['reason'], 'TICKET_UNKNOWN')
            stranger = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-2', 'r3',
                                                   ticket, 'n1', 'n2', 's2'), 300)
            self.assertEqual(json.loads(stranger['first_result'])['reason'], 'TICKET_UNKNOWN')

    def test_nonce_reuse_and_unknown_shard_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            ticket = json.loads(enq['first_result'])['queueTicketId']
            reuse = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', 'r1',
                                                ticket, 'n1', 'n1', 's2'), 200)
            self.assertEqual(json.loads(reuse['first_result'])['reason'], 'NONCE_REUSE')
            missing = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', 'r2',
                                                  ticket, 'n1', 'n2', 's-missing'), 200)
            self.assertEqual(json.loads(missing['first_result'])['reason'], 'SHARD_UNKNOWN')
            self.assertEqual(self.side_count(tmp, 'onsale_token'), 1)

    def test_expired_token_cannot_be_reissued(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            ticket = json.loads(enq['first_result'])['queueTicketId']
            late = 100 + limits().token_ttl_ms
            refused = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', 'r1',
                                                  ticket, 'n1', 'n2', 's2'), late)
            self.assertEqual(json.loads(refused['first_result'])['reason'], 'TOKEN_EXPIRED')
            self.assertEqual(self.side_count(tmp, 'onsale_token'), 1)

    def test_waiting_room_reissue_routes_and_preserves_rank(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            room = WaitingRoom(unit, HintRouter('power_of_two', random.Random(13)))
            enq = room.enter(show_id=SHOW, inventory_epoch=EPOCH, inventory_mode=MODE,
                             principal='buyer-1', client_command_id='c1', nonce='n1', now_ms=100)
            one = json.loads(enq['first_result'])
            reissue = room.reissue(show_id=SHOW, inventory_epoch=EPOCH, inventory_mode=MODE,
                                   principal='buyer-1', client_command_id='r1',
                                   queue_ticket_id=one['queueTicketId'], old_nonce='n1',
                                   new_nonce='n2', now_ms=300)
            self.assertEqual(reissue['outcome'], 'new_success')
            body = json.loads(reissue['first_result'])
            self.assertEqual(body['queuePositionIdentity'], one['queuePositionIdentity'])
            self.assertTrue(tokens.verify(body['token'], self.key))


class ExpireSweepTests(_ClusterCase):
    def seeded(self, unit, count=3):
        documents = []
        for index in range(count):
            enq = unit.enqueue(enqueue_request(ccid='c%d' % index,
                                               principal='buyer-%d' % index,
                                               nonce='n%d' % index), 100 + index)
            documents.append(token_of(enq))
        return documents

    def test_sweep_expires_only_issued_tokens_past_expiry(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 8}) as unit:
            documents = self.seeded(unit)
            late = 100 + limits().token_ttl_ms + 10
            fresh = unit.enqueue(enqueue_request(ccid='fresh', principal='buyer-f',
                                                 nonce='nf'), late)
            result = unit.expire_sweep(late, 10)
            self.assertEqual(result['expired'], 3)
            self.assertIsNone(result['stopped'])
            states = self.side(tmp, "SELECT COUNT(*) FROM onsale_token_state WHERE state = 'EXPIRED'")
            self.assertEqual(states[0][0], 3)
            self.assertEqual(self.side_count(tmp, 'onsale_evidence', "kind = 'expire'"), 3)
            opens = self.side(tmp, "SELECT COUNT(*) FROM ledger WHERE is_open AND entry_id LIKE 'enq:%'")
            self.assertEqual(opens[0][0], 1)  # only the fresh, unexpired token stays open
            completion = self.side(tmp, "SELECT COUNT(*) FROM ledger WHERE budget_class = 'completion'")
            self.assertEqual(completion[0][0], 3)
            refused = unit.admit(admit_request(documents[0], ccid='a0', principal='buyer-0'), late + 1)
            self.assertEqual(json.loads(refused['first_result'])['reason'], 'TOKEN_EXPIRED')
            still_valid = unit.admit(admit_request(token_of(fresh), ccid='af',
                                                   principal='buyer-f'), late + 1)
            self.assertEqual(still_valid['outcome'], 'new_success')

    def test_sweep_respects_max_count_and_resumes(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 8}) as unit:
            self.seeded(unit)
            late = 100 + limits().token_ttl_ms + 10
            first = unit.expire_sweep(late, 2)
            self.assertEqual((first['expired'], first['stopped']), (2, 'max_count'))
            second = unit.expire_sweep(late, 2)
            self.assertEqual((second['expired'], second['stopped']), (1, None))
            third = unit.expire_sweep(late, 2)
            self.assertEqual(third['expired'], 0)

    def test_sweep_is_bounded_by_the_completion_budget(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 8},
                budget=spec(completion=ClassLimit(count=1, bytes=10_000_000, age_ms=10_000_000))) as unit:
            self.seeded(unit)
            late = 100 + limits().token_ttl_ms + 10
            result = unit.expire_sweep(late, 10)
            self.assertEqual(result['expired'], 1)
            self.assertEqual(result['stopped'], 'capacity')
            self.assertEqual(result['capacity_reason'], 'count')
            self.assertEqual(self.side_count(tmp, 'onsale_evidence', "kind = 'expire'"), 1)

    def test_inflow_saturation_does_not_starve_the_sweep(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 8},
                budget=spec(inflow=ClassLimit(count=3, bytes=10_000_000, age_ms=10_000_000))) as unit:
            self.seeded(unit)
            late = 100 + limits().token_ttl_ms + 10
            saturated = unit.enqueue(enqueue_request(ccid='more', principal='buyer-x',
                                                     nonce='nx'), late)
            self.assertEqual(saturated['outcome'], 'capacity')
            result = unit.expire_sweep(late, 10)
            self.assertEqual(result['expired'], 3)

    def test_sweep_requires_a_positive_bound(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp) as unit:
            for bad in (0, -1, True, 1.5):
                with self.assertRaises(ValueError):
                    unit.expire_sweep(100, bad)


class BudgetTests(_ClusterCase):
    def test_inflow_count_and_bytes_caps_write_nothing(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, budget=spec(inflow=ClassLimit(count=1, bytes=10_000_000, age_ms=10_000_000))) as unit:
            unit.enqueue(enqueue_request(), 100)
            before = unit.table_counts()
            refused = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 110)
            self.assertEqual((refused['outcome'], refused['capacity_reason']), ('capacity', 'count'))
            self.assertEqual(unit.table_counts(), before)
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, budget=spec(inflow=ClassLimit(count=100, bytes=1, age_ms=10_000_000))) as unit:
            refused = unit.enqueue(enqueue_request(), 100)
            self.assertEqual((refused['outcome'], refused['capacity_reason']), ('capacity', 'bytes'))
            self.assertEqual(unit.table_counts()['onsale_command'], 0)

    def test_inflow_age_cap_frees_when_the_completion_sweep_closes_the_entry(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 4},
                budget=spec(inflow=ClassLimit(count=100, bytes=10_000_000, age_ms=100))) as unit:
            enq = unit.enqueue(enqueue_request(), 0)
            refused = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 200)
            self.assertEqual((refused['outcome'], refused['capacity_reason']), ('capacity', 'age'))
            blocked_admit = unit.admit(admit_request(token_of(enq)), 200)
            self.assertEqual((blocked_admit['outcome'], blocked_admit['capacity_reason']),
                             ('capacity', 'age'))
            late = limits().token_ttl_ms + 1
            swept = unit.expire_sweep(late, 10)
            self.assertEqual(swept['expired'], 1)
            freed = unit.enqueue(enqueue_request(ccid='c3', principal='buyer-3', nonce='n3'), late)
            self.assertEqual(freed['outcome'], 'new_success')

    def test_replay_is_not_blocked_by_a_saturated_budget(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, budget=spec(inflow=ClassLimit(count=1, bytes=10_000_000, age_ms=10_000_000))) as unit:
            first = unit.enqueue(enqueue_request(), 100)
            again = unit.enqueue(enqueue_request(), 500)
            self.assertEqual(again['outcome'], 'replayed')
            self.assertEqual(again['first_result'], first['first_result'])

    def test_classes_are_independent_under_saturation(self):
        tight = ClassLimit(count=0, bytes=0, age_ms=0)
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 4}, budget=spec(inflow=tight)) as unit:
            unit.configure_ga(SHOW, EPOCH + 1, MODE, 1, 4, {'s1': 4}, 1)
            refused = unit.enqueue(enqueue_request(), 100)
            self.assertEqual(refused['outcome'], 'capacity')
            self.assertEqual(unit.table_counts()['onsale_command'], 0)
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 4},
                budget=spec(inflow=ClassLimit(count=1, bytes=10_000_000, age_ms=10_000_000),
                            observation=ClassLimit(count=1, bytes=10_000_000, age_ms=10_000_000))) as unit:
            unit.enqueue(enqueue_request(), 100)
            conflict = unit.enqueue(enqueue_request(nonce='different'), 110)
            self.assertEqual(conflict['outcome'], 'conflict_retained')
            self.assertEqual(self.side_count(tmp, 'observation'), 1)

    def test_recovery_works_while_inflow_is_saturated(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(
                tmp, {'s1': 4},
                budget=spec(inflow=ClassLimit(count=1, bytes=10_000_000, age_ms=10_000_000))) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            saturated = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 110)
            self.assertEqual(saturated['outcome'], 'capacity')
            ticket = json.loads(enq['first_result'])['queueTicketId']
            reissue = unit.reissue(ReissueRequest(SHOW, EPOCH, MODE, 'buyer-1', 'r1',
                                                  ticket, 'n1', 'n2', 's1'), 200)
            self.assertEqual(reissue['outcome'], 'new_success')


class CorruptionTests(_ClusterCase):
    MUTATIONS = (
        ('onsale_ga_config', "UPDATE onsale_ga_config SET mode = 'Tampered'"),
        ('onsale_ga_shard', 'UPDATE onsale_ga_shard SET initial_capacity = initial_capacity + 1'),
        ('onsale_queue_ticket', 'UPDATE onsale_queue_ticket SET seq = seq + 100'),
        ('onsale_token', "UPDATE onsale_token SET nonce = 'tampered'"),
        ('onsale_token_state', "UPDATE onsale_token_state SET state = 'TAMPERED'"),
        ('onsale_command', "UPDATE onsale_command SET first_result = 'tampered'"),
        ('onsale_evidence', "UPDATE onsale_evidence SET reason = 'tampered'"),
        ('onsale_session', "UPDATE onsale_session SET shard_id = 'tampered'"),
        ('onsale_hint', 'UPDATE onsale_hint SET version = version + 100'),
    )

    def seed_full(self, unit):
        for index in range(3):
            principal = 'buyer-%d' % index
            enq = unit.enqueue(enqueue_request(ccid='c%d' % index, principal=principal,
                                               nonce='n%d' % index), 100 + index)
            unit.admit(admit_request(token_of(enq), ccid='a%d' % index,
                                     principal=principal), 200 + index)

    def test_every_crc_table_fails_closed_on_tamper(self):
        self.assertEqual(set(table for table, _ in self.MUTATIONS), set(ONSALE_CRC_TABLES))
        for table, statement in self.MUTATIONS:
            with self.subTest(table=table), tempfile.TemporaryDirectory() as tmp:
                with self.configured(tmp, {'s1': 2}) as unit:
                    self.seed_full(unit)
                self.side_exec(tmp, statement)
                with self.assertRaises(StoreError) as refused:
                    with self.unit(tmp):
                        pass
                self.assertEqual(refused.exception.code, 'CHECKSUM_MISMATCH')

    def test_shard_remaining_tamper_fails_closed_at_open(self):
        for statement in (
            'UPDATE onsale_ga_shard SET remaining = remaining + 5',
            'UPDATE onsale_ga_shard SET remaining = -1',
        ):
            with self.subTest(statement=statement), tempfile.TemporaryDirectory() as tmp:
                with self.configured(tmp, {'s1': 2}) as unit:
                    self.enter_and_admit(unit, 'buyer-1', 'c1', 'n1')
                self.side_exec(tmp, statement)
                with self.assertRaises(StoreError) as refused:
                    with self.unit(tmp):
                        pass
                self.assertEqual(refused.exception.code, 'CHECKSUM_MISMATCH')

    def test_reopen_verifies_the_composed_durable_tables_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.configured(tmp, {'s1': 2}) as unit:
                unit.enqueue(enqueue_request(), 100)
                unit.enqueue(enqueue_request(nonce='different'), 110)
            self.side_exec(tmp, "UPDATE observation SET nbytes = nbytes + 1")
            with self.assertRaises(StoreError) as refused:
                with self.unit(tmp):
                    pass
            self.assertEqual(refused.exception.code, 'CHECKSUM_MISMATCH')


class ResultFlagTests(_ClusterCase):
    def test_every_result_carries_the_false_flags(self):
        with tempfile.TemporaryDirectory() as tmp, self.configured(tmp, {'s1': 1}) as unit:
            enq = unit.enqueue(enqueue_request(), 100)
            admit = unit.admit(admit_request(token_of(enq)), 200)
            enq2 = unit.enqueue(enqueue_request(ccid='c2', principal='buyer-2', nonce='n2'), 210)
            sold = unit.admit(admit_request(token_of(enq2), ccid='a2', principal='buyer-2'), 220)
            replay = unit.enqueue(enqueue_request(), 300)
            for result in (enq, admit, enq2, sold, replay):
                self.assertTrue(result['localOnsaleFixtureOnly'])
                for name in ('protocolTruth', 'productionConformance', 'productionReadiness',
                             'productionEndpoint', 'fundsExecuted', 'chainWriter',
                             'delegatedExecution'):
                    self.assertIs(result[name], False, name)
            self.assertEqual(unit.flags()['protocolTruth'], False)


if __name__ == '__main__':
    unittest.main()
