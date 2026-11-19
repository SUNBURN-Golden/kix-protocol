"""Refunds: authorization, reservation, partial (B5) and full reversal."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError  # noqa: E402
from reference.economics import quotes, support  # noqa: E402
from reference.economics.refunds import reservation_check  # noqa: E402


class RefundTest(unittest.TestCase):
    def setUp(self):
        self.session = support.make_session()
        self.assets = support.make_assets()
        self.fixture = support.load_fixture('partial_refund.json')
        f = self.fixture
        lines = [support.krw_line(row['lineId'], row['atoms']) for row in f['lines']]
        legs = [support.krw_leg('leg-1', f['legAmount'])]
        self.session.create_order(f['orderId'], order_version=f['orderVersion'],
                                  scope=f['scope'], groups=[support.group(lines, legs)],
                                  now_ms=f['nowMs'])
        support.capture_and_confirm(self.session, f['orderId'], 'group-1', 'leg-1', 'cap-1', f['legAmount'])
        support.settle(self.session, f['orderId'], 'group-1')

    def tearDown(self):
        self.session.close()

    def _refund(self, line_ids, **over):
        f = self.fixture['refund']
        group = self.session.view(self.fixture['orderId'])['orders'][self.fixture['orderId']]['groups']['group-1']
        proposal = quotes.propose_line_refund(
            self.assets, group['quote'], group['plan'], line_ids, group['plan']['planHash'])
        kwargs = dict(line_ids=line_ids, refund_id=f['refundId'],
                      authorization=support.authorization(proposal),
                      refund_policy_ref=f['refundPolicyRef'], reason=f['reason'],
                      idempotency_key=f['idempotencyKey'])
        kwargs.update(over)
        return self.session.refund_lines(self.fixture['orderId'], 'group-1', **kwargs)

    def test_partial_refund_b5_requester(self):
        result = self._refund(['line-1'])
        expected = self.fixture['expected']
        self.assertEqual(result['kind'], expected['kind'])
        self.assertEqual(result['bearer'], expected['bearer'])
        self.assertFalse(result['distributionBlocked'])
        self.assertEqual(result['proposal']['customerRefund']['atoms'], expected['customerRefundAtoms'])
        self.assertIsNone(result['effectId'])

    def test_partial_refund_leaves_faces_and_distribution_continues(self):
        self._refund(['line-1'])
        result = self.session.distribute_group(self.fixture['orderId'], 'group-1',
                                               order=['organizer-1', 'platform'], idempotency_key='dist-1')
        self.assertEqual(result['effect'], {'organizer-1': 9700, 'platform': 300})

    def test_full_refund_reclassifies_and_reverses(self):
        result = self._refund(['line-1', 'line-2'], refund_id='refund-full',
                              idempotency_key='ref-full', route_profile='CASH_REFUND_FIXTURE',
                              effect_id='eff-refund')
        self.assertEqual(result['kind'], 'FULL')
        self.assertEqual(result['bearer'], 'FIXTURE_FULL_GROSS_RECLASS')
        self.assertEqual(result['effectId'], 'eff-refund')
        group = self.session.view(self.fixture['orderId'])['orders'][self.fixture['orderId']]['groups']['group-1']
        self.assertEqual(group['phase'], 'REFUNDED')

    def test_line_already_refunded_refused(self):
        self._refund(['line-1'])
        with self.assertRaises(EconomicsLocalError) as ctx:
            self._refund(['line-1'], refund_id='refund-2', idempotency_key='ref-2')
        self.assertTrue(str(ctx.exception).startswith('LINE_ALREADY_REFUNDED'))

    def test_missing_evidence_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self._refund(['line-1'], authorization={})
        self.assertEqual(str(ctx.exception), 'REFUND_EVIDENCE_FIELDS')

    def test_full_refund_requires_route(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self._refund(['line-1', 'line-2'], refund_id='refund-full', idempotency_key='ref-full')
        self.assertEqual(str(ctx.exception), 'REFUND_ROUTE_REQUIRED')

    def test_refund_acceptance_observed(self):
        self._refund(['line-1'])
        result = self.session.observe_refund_acceptance(
            self.fixture['orderId'], 'group-1', source_id='accept-1', amount=6000,
            idempotency_key='accept-key')
        self.assertEqual(result['settlement']['claim']['refund_accepted'], 6000)

    def test_refund_before_settlement_refused(self):
        session = support.make_session()
        try:
            support.primary_order(session, order_id='order-2')
            with self.assertRaises(EconomicsLocalError) as ctx:
                session.refund_lines('order-2', 'group-1', line_ids=['line-1'],
                                     refund_id='r', authorization={}, refund_policy_ref='refund-1',
                                     reason='x', idempotency_key='k')
            self.assertEqual(str(ctx.exception), 'GROUP_NOT_REFUNDABLE')
        finally:
            session.close()


class ReservationGuardTest(unittest.TestCase):
    def test_refund_exceeds_confirmed_refused(self):
        assets, policies = support.make_assets(), support.make_policies()
        request = quotes.quote_request(
            'order-1', order_version=1, scope=support.SCOPE, policy_ref='pricing-1',
            expires_at=support.FAR_FUTURE, lines=[support.krw_line('line-1', 6000)])
        quote = quotes.build_quote(assets, policies, request)
        plan = quotes.plan_payments(assets, quote, [support.krw_leg('leg-1', 6000)], quote['quoteHash'], 1000)
        proposal = quotes.propose_line_refund(assets, quote, plan, ['line-1'], plan['planHash'])
        with self.assertRaises(EconomicsLocalError) as ctx:
            reservation_check(quote, proposal, leg_confirmed={'leg-1': 1000},
                              refund_reserved={}, refunded_lines=set())
        self.assertTrue(str(ctx.exception).startswith('REFUND_EXCEEDS_CAPTURED'))

    def test_reserved_plus_new_exceeds_confirmed_refused(self):
        assets, policies = support.make_assets(), support.make_policies()
        request = quotes.quote_request(
            'order-1', order_version=1, scope=support.SCOPE, policy_ref='pricing-1',
            expires_at=support.FAR_FUTURE, lines=[support.krw_line('line-1', 6000)])
        quote = quotes.build_quote(assets, policies, request)
        plan = quotes.plan_payments(assets, quote, [support.krw_leg('leg-1', 6000)], quote['quoteHash'], 1000)
        proposal = quotes.propose_line_refund(assets, quote, plan, ['line-1'], plan['planHash'])
        with self.assertRaises(EconomicsLocalError) as ctx:
            reservation_check(quote, proposal, leg_confirmed={'leg-1': 6000},
                              refund_reserved={'leg-1': 1000}, refunded_lines=set())
        self.assertTrue(str(ctx.exception).startswith('REFUND_EXCEEDS_CAPTURED'))


if __name__ == '__main__':
    unittest.main()