"""Local-only binding of economics capture admission to the stage-5 DurableUnit.

Needs the pinned local PostgreSQL 17.11 (/usr/lib/postgresql/17/bin) and
psycopg. Unlike the stage-5 conformance run, this composition test skips
gracefully when the backend is absent so it can live alongside the offline
suite without requiring a database. It is NOT wired into CI.

It proves three things about ``DurableCaptureLedger`` / ``EconomicsSession.
over_durable``: admission outcomes match the in-memory pure-decision ledger
(differential, including atomic over-capture refusal and fresh retry), a
refused over-capture writes nothing to the database, and a replay after
reopen returns the stored first result from the database. Budget numbers are
synthetic fixtures, not product policy.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

POSTGRES = '/usr/lib/postgresql/17/bin/postgres'
INITDB = '/usr/lib/postgresql/17/bin/initdb'

try:
    import psycopg  # noqa: F401
    HAVE_PSYCOPG = True
except ImportError:
    HAVE_PSYCOPG = False

HAVE_BACKEND = HAVE_PSYCOPG and os.path.exists(POSTGRES) and os.path.exists(INITDB)

if HAVE_BACKEND:
    from durable.backend import DurablePostgresBackend
    from durable.budgets import BudgetSpec, ClassLimit
    from durable.cluster import PinnedPostgresCluster
    from reference.economics import (
        CaptureLedger, DurableCaptureLedger, EconomicsLocalError, EconomicsSession,
    )
    from reference.economics import support


def _spec():
    limit = ClassLimit(1000, 1_000_000, 3_600_000)
    return BudgetSpec(inflow=limit, observation=limit, completion=limit,
                      cancel=ClassLimit(100, 100_000, 3_600_000),
                      recovery=ClassLimit(100, 100_000, 3_600_000))


@unittest.skipUnless(HAVE_BACKEND, 'pinned local PostgreSQL 17.11 / psycopg not available')
class EconomicsDurableBindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix='kix-econ-bind-')
        cls.cluster = PinnedPostgresCluster(cls.root)
        cls.cluster.start()
        cls.backend = DurablePostgresBackend(cls.cluster)

    @classmethod
    def tearDownClass(cls):
        cls.cluster.stop()
        shutil.rmtree(cls.root, ignore_errors=True)

    def _unit(self, directory):
        return self.backend.open_unit(directory, _spec())

    def test_differential_admission_matches_in_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = self._unit(tmp)
            try:
                memory = CaptureLedger(_spec())
                durable = DurableCaptureLedger(unit)
                for ledger in (memory, durable):
                    ledger.add_leg('o', 'g', 'l', 10000)
                def run_step(capture_id, amount, nonce, expected):
                    outcomes = []
                    for ledger in (memory, durable):
                        try:
                            result = ledger.submit(order_id='o', group_id='g', leg_id='l',
                                                   capture_id=capture_id, amount=amount,
                                                   buyer='buyer-1', nonce=nonce, now_ms=1000)
                        except EconomicsLocalError as exc:
                            outcomes.append(('refused', str(exc)))
                        else:
                            outcomes.append(('returned', result['outcome'],
                                             result['first_result']))
                    self.assertEqual(outcomes[0], outcomes[1], capture_id)
                    self.assertEqual(outcomes[0][1], expected, capture_id)

                sequence = [
                    ('c1', 4000, 'n1', 'new_success'),
                    ('c1', 4000, 'n1', 'replayed'),
                    ('c1', 4000, 'other', 'conflict_retained'),
                    ('c1', 4000, 'other', 'conflict_retained'),
                    ('c2', 6000, 'n2', 'new_success'),
                    # The leg is full (4000 + 6000 open): a new capture must
                    # be refused atomically on both paths, before any write,
                    # and the identical retry must be refused again.
                    ('c3', 1, 'n3', 'OVER_CAPTURE'),
                    ('c3', 1, 'n3', 'OVER_CAPTURE'),
                ]
                for capture_id, amount, nonce, expected in sequence:
                    run_step(capture_id, amount, nonce, expected)
                # Confirmed amounts block too; a FAILED release frees the leg
                # and the refused capture id retries as a fresh attempt —
                # never a replay of a durable admission written by mistake.
                for ledger in (memory, durable):
                    ledger.complete('c1', outcome='CONFIRMED', source_id='s1', now_ms=1100)
                run_step('c3', 1, 'n3', 'OVER_CAPTURE')
                for ledger in (memory, durable):
                    ledger.complete('c2', outcome='FAILED', source_id='s2', now_ms=1200)
                run_step('c3', 6000, 'n3', 'new_success')
            finally:
                unit.close()

    def test_over_capture_writes_nothing_durable_and_retry_is_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = self._unit(tmp)
            try:
                ledger = DurableCaptureLedger(unit)
                ledger.add_leg('o', 'g', 'l', 10000)
                ledger.add_leg('o', 'g', 'l2', 10000)
                first = ledger.submit(order_id='o', group_id='g', leg_id='l',
                                      capture_id='c1', amount=10000, buyer='buyer-1',
                                      nonce='n1', now_ms=1000)
                self.assertEqual(first['outcome'], 'new_success')
                ledger.complete('c1', outcome='CONFIRMED', source_id='s1', now_ms=1100)
                # Leg fully confirmed: a 1-atom capture must be refused
                # before the admission transaction, not after it.
                before = unit.table_counts()
                for _ in range(2):
                    with self.assertRaises(EconomicsLocalError) as ctx:
                        ledger.submit(order_id='o', group_id='g', leg_id='l',
                                      capture_id='c2', amount=1, buyer='buyer-1',
                                      nonce='n2', now_ms=1200)
                    self.assertEqual(str(ctx.exception), 'OVER_CAPTURE')
                    self.assertEqual(unit.table_counts(), before)
                self.assertNotIn('c2', ledger.view()['captures'])
                # Open reservations block too; after a FAILED release the
                # same capture id is a fresh success and can complete.
                open_cap = ledger.submit(order_id='o', group_id='g', leg_id='l2',
                                         capture_id='c3', amount=10000, buyer='buyer-1',
                                         nonce='n3', now_ms=1300)
                self.assertEqual(open_cap['outcome'], 'new_success')
                before = unit.table_counts()
                with self.assertRaises(EconomicsLocalError) as ctx:
                    ledger.submit(order_id='o', group_id='g', leg_id='l2',
                                  capture_id='c4', amount=1, buyer='buyer-1',
                                  nonce='n4', now_ms=1400)
                self.assertEqual(str(ctx.exception), 'OVER_CAPTURE')
                self.assertEqual(unit.table_counts(), before)
                ledger.complete('c3', outcome='FAILED', source_id='s3', now_ms=1500)
                retry = ledger.submit(order_id='o', group_id='g', leg_id='l2',
                                      capture_id='c4', amount=1, buyer='buyer-1',
                                      nonce='n4', now_ms=1600)
                self.assertEqual(retry['outcome'], 'new_success')
                done = ledger.complete('c4', outcome='CONFIRMED', source_id='s4', now_ms=1700)
                self.assertEqual(done['outcome'], 'completed')
                self.assertEqual(ledger.leg_view('o', 'g', 'l2')['confirmed'], 1)
            finally:
                unit.close()

    def test_replay_after_reopen_returns_stored_first_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = self._unit(tmp)
            try:
                ledger = DurableCaptureLedger(unit)
                ledger.add_leg('o', 'g', 'l', 10000)
                first = ledger.submit(order_id='o', group_id='g', leg_id='l',
                                      capture_id='c1', amount=4000, buyer='buyer-1',
                                      nonce='n1', now_ms=1000)
                self.assertEqual(first['outcome'], 'new_success')
            finally:
                unit.close()
            # Reopen the same directory: admission state lives in the database.
            reopened = self._unit(tmp)
            try:
                ledger = DurableCaptureLedger(reopened)
                # Replay resolves from the database before any availability
                # check, even before the process-local leg is re-added.
                early = ledger.submit(order_id='o', group_id='g', leg_id='l',
                                      capture_id='c1', amount=4000, buyer='buyer-1',
                                      nonce='n1', now_ms=1000)
                self.assertEqual(early['outcome'], 'replayed')
                self.assertEqual(early['first_result'], first['first_result'])
                ledger.add_leg('o', 'g', 'l', 10000)
                again = ledger.submit(order_id='o', group_id='g', leg_id='l',
                                      capture_id='c1', amount=4000, buyer='buyer-1',
                                      nonce='n1', now_ms=1000)
                self.assertEqual(again['outcome'], 'replayed')
                self.assertEqual(again['first_result'], first['first_result'])
            finally:
                reopened.close()

    def test_over_durable_session_settles(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit = self._unit(tmp)
            try:
                session = EconomicsSession.over_durable(
                    unit, assets=support.make_assets(), policies=support.make_policies())
                try:
                    support.primary_order(session)
                    result = session.submit_capture('order-1', 'group-1', 'leg-1', 'cap-1',
                                                    amount=10000, buyer='buyer-1', nonce='n', now_ms=1000)
                    self.assertEqual(result['outcome'], 'new_success')
                    session.complete_capture('cap-1', outcome='CONFIRMED', source_id='s', now_ms=1100)
                    settled = support.settle(session, 'order-1', 'group-1')
                    faces = {a['payee']: a['amount'] for a in settled['allocations']}
                    self.assertEqual(faces, {'organizer-1': 9700, 'platform': 300})
                finally:
                    session.close()
            finally:
                unit.close()


if __name__ == '__main__':
    unittest.main()