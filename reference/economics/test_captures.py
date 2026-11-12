"""Capture ledger: multiple intents, partial captures, replay, completion outcomes.

Admission reuses the unchanged stage-5 pure decision; these tests prove the
preserved identity / first-result / UNKNOWN / capacity semantics and the
atomic over-capture refusal.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from durable.budgets import BudgetSpec, ClassLimit  # noqa: E402
from reference.economics import CaptureLedger, EconomicsLocalError  # noqa: E402
from reference.economics import support  # noqa: E402


def submit(ledger, capture_id, amount, *, nonce=None, now_ms=1000,
           order='o', group='g', leg='l'):
    return ledger.submit(order_id=order, group_id=group, leg_id=leg,
                         capture_id=capture_id, amount=amount, buyer='buyer-1',
                         nonce=nonce if nonce is not None else 'n-' + capture_id,
                         now_ms=now_ms)


class CaptureLedgerTest(unittest.TestCase):
    def setUp(self):
        self.ledger = CaptureLedger(support.make_budgets())
        self.ledger.add_leg('o', 'g', 'l', 10000)

    def test_multiple_partial_captures_fill_leg(self):
        self.assertEqual(submit(self.ledger, 'c1', 4000)['outcome'], 'new_success')
        self.assertEqual(submit(self.ledger, 'c2', 6000)['outcome'], 'new_success')
        self.ledger.complete('c1', outcome='CONFIRMED', source_id='s1', now_ms=1100)
        self.ledger.complete('c2', outcome='CONFIRMED', source_id='s2', now_ms=1100)
        view = self.ledger.leg_view('o', 'g', 'l')
        self.assertEqual(view['confirmed'], 10000)
        self.assertEqual(view['remaining'], 0)
        self.assertTrue(self.ledger.fully_captured('o', 'g', 'l'))

    def test_replay_returns_immutable_first_result(self):
        first = submit(self.ledger, 'c1', 4000)
        again = submit(self.ledger, 'c1', 4000)
        self.assertEqual(again['outcome'], 'replayed')
        self.assertEqual(again['first_result'], first['first_result'])

    def test_conflicting_payload_retained_once(self):
        submit(self.ledger, 'c1', 4000)
        conflict = submit(self.ledger, 'c1', 4000, nonce='different')
        self.assertEqual(conflict['outcome'], 'conflict_retained')
        again = submit(self.ledger, 'c1', 4000, nonce='different')
        self.assertEqual(again['outcome'], 'conflict_retained')
        conflicts = self.ledger.view()['conflicts']
        self.assertEqual(len(conflicts), 1)

    def test_over_capture_refused_atomically_and_retryable(self):
        submit(self.ledger, 'c1', 4000)
        with self.assertRaises(EconomicsLocalError) as ctx:
            submit(self.ledger, 'c2', 7000)
        self.assertEqual(str(ctx.exception), 'OVER_CAPTURE')
        # Nothing was stored for the refused attempt.
        self.assertNotIn('c2', self.ledger.view()['captures'])
        self.assertEqual(self.ledger.leg_view('o', 'g', 'l')['open'], 4000)
        # A later smaller attempt is a fresh success.
        self.assertEqual(submit(self.ledger, 'c2', 6000)['outcome'], 'new_success')

    def test_confirmed_moves_open_to_confirmed(self):
        submit(self.ledger, 'c1', 4000)
        self.assertEqual(self.ledger.leg_view('o', 'g', 'l')['open'], 4000)
        self.ledger.complete('c1', outcome='CONFIRMED', source_id='s1', now_ms=1100)
        view = self.ledger.leg_view('o', 'g', 'l')
        self.assertEqual(view['open'], 0)
        self.assertEqual(view['confirmed'], 4000)

    def test_failed_releases_open_but_retains_record(self):
        submit(self.ledger, 'c1', 4000)
        self.ledger.complete('c1', outcome='FAILED', source_id='s1', now_ms=1100)
        view = self.ledger.leg_view('o', 'g', 'l')
        self.assertEqual(view['open'], 0)
        self.assertEqual(view['confirmed'], 0)
        self.assertIn('c1', self.ledger.view()['completions'])
        # The released capacity is reusable.
        self.assertEqual(submit(self.ledger, 'c2', 10000)['outcome'], 'new_success')

    def test_unknown_retains_reservation(self):
        submit(self.ledger, 'c1', 4000)
        self.ledger.complete('c1', outcome='UNKNOWN', source_id='s1', now_ms=1100)
        view = self.ledger.leg_view('o', 'g', 'l')
        self.assertEqual(view['open'], 4000)
        self.assertEqual(view['confirmed'], 0)
        # The reservation still blocks an over-capture.
        with self.assertRaises(EconomicsLocalError):
            submit(self.ledger, 'c2', 7000)

    def test_completion_record_immutable(self):
        submit(self.ledger, 'c1', 4000)
        self.ledger.complete('c1', outcome='CONFIRMED', source_id='s1', now_ms=1100)
        replay = self.ledger.complete('c1', outcome='CONFIRMED', source_id='s1', now_ms=1100)
        self.assertEqual(replay['outcome'], 'replayed')
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.ledger.complete('c1', outcome='FAILED', source_id='s1', now_ms=1100)
        self.assertEqual(str(ctx.exception), 'COMPLETION_BINDING_CONFLICT')

    def test_completion_requires_admitted_capture(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.ledger.complete('missing', outcome='CONFIRMED', source_id='s', now_ms=1100)
        self.assertEqual(str(ctx.exception), 'CAPTURE_NOT_ADMITTED')

    def test_unknown_leg_refused_for_new_capture(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            submit(self.ledger, 'c1', 100, leg='missing')
        self.assertEqual(str(ctx.exception), 'UNKNOWN_LEG')

    def test_invalid_time_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            submit(self.ledger, 'c1', 100, now_ms=-1)
        self.assertEqual(str(ctx.exception), 'CAPTURE_TIME_INVALID')

    def test_capacity_writes_nothing(self):
        limit = ClassLimit(1, 1_000_000, 3_600_000)
        ledger = CaptureLedger(BudgetSpec(inflow=limit, observation=limit,
                                          completion=limit, cancel=limit, recovery=limit))
        ledger.add_leg('o', 'g', 'l', 10000)
        self.assertEqual(submit(ledger, 'c1', 4000)['outcome'], 'new_success')
        refused = submit(ledger, 'c2', 4000)
        self.assertEqual(refused['outcome'], 'capacity')
        self.assertNotIn('c2', ledger.view()['captures'])


class CaptureFixtureTest(unittest.TestCase):
    def setUp(self):
        self.fixture = support.load_fixture('capture_plan.json')
        self.session = support.make_session()

    def tearDown(self):
        self.session.close()

    def test_fixture_multiple_intents_and_over_capture(self):
        f = self.fixture
        line = support.krw_line('line-1', f['lineAtoms'])
        leg = support.krw_leg('leg-1', f['legAmount'])
        self.session.create_order(f['orderId'], order_version=f['orderVersion'],
                                  scope=f['scope'], groups=[support.group([line], [leg])],
                                  now_ms=f['nowMs'])
        for capture in f['captures']:
            support.capture_and_confirm(self.session, f['orderId'], 'group-1', 'leg-1',
                                        capture['captureId'], capture['amount'], now_ms=f['nowMs'])
        view = self.session.view()['captures']['legs'][0]
        self.assertEqual(view['confirmed'], f['expected']['legConfirmed'])
        self.assertEqual(view['remaining'], f['expected']['legRemaining'])
        over = f['overCapture']
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.submit_capture(f['orderId'], 'group-1', 'leg-1', over['captureId'],
                                        amount=over['amount'], buyer='buyer-1', nonce='n', now_ms=f['nowMs'])
        self.assertEqual(str(ctx.exception), f['expected']['overCaptureError'])


if __name__ == '__main__':
    unittest.main()