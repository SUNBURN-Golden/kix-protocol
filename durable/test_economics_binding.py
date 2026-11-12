"""Local-only binding of economics capture admission to the stage-5 DurableUnit.

Needs the pinned local PostgreSQL 17.11 (/usr/lib/postgresql/17/bin) and
psycopg. Unlike the stage-5 conformance run, this composition test skips
gracefully when the backend is absent so it can live alongside the offline
suite without requiring a database. It is NOT wired into CI.

It proves two things about ``DurableCaptureLedger`` / ``EconomicsSession.
over_durable``: admission outcomes match the in-memory pure-decision ledger
(differential), and a replay after reopen returns the stored first result from
the database. Budget numbers are synthetic fixtures, not product policy.
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
        CaptureLedger, DurableCaptureLedger, EconomicsSession,
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
                sequence = [
                    ('c1', 4000, 'n1', 'new_success'),
                    ('c1', 4000, 'n1', 'replayed'),
                    ('c1', 4000, 'other', 'conflict_retained'),
                    ('c1', 4000, 'other', 'conflict_retained'),
                    ('c2', 6000, 'n2', 'new_success'),
                ]
                for capture_id, amount, nonce, expected in sequence:
                    results = []
                    for ledger in (memory, durable):
                        result = ledger.submit(order_id='o', group_id='g', leg_id='l',
                                               capture_id=capture_id, amount=amount,
                                               buyer='buyer-1', nonce=nonce, now_ms=1000)
                        results.append(result)
                    self.assertEqual(results[0]['outcome'], expected, capture_id)
                    self.assertEqual(results[1]['outcome'], expected, capture_id)
                    self.assertEqual(results[0]['first_result'], results[1]['first_result'], capture_id)
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