"""Seeded conservation properties and rejection atomicity.

These are characterization properties of the composed calculation and money
layers over synthetic inputs: amounts conserve exactly (integer atoms, no
rounding loss), and a refused operation writes nothing.
"""
from __future__ import annotations

from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError  # noqa: E402
from reference.economics import quotes, support  # noqa: E402


def _split(total, parts, rng):
    """Split a positive integer into ``parts`` positive integers (exact sum)."""
    if parts <= 1 or total < parts:
        return [total]
    cuts = sorted(rng.sample(range(1, total), parts - 1))
    bounds = [0] + cuts + [total]
    return [bounds[i + 1] - bounds[i] for i in range(parts)]


class CalculationConservationTest(unittest.TestCase):
    def test_seeded_quote_and_refund_conservation(self):
        assets, policies = support.make_assets(), support.make_policies()
        for seed in range(100):
            rng = random.Random(seed)
            n = rng.randint(1, 5)
            lines = [support.krw_line('line-%d' % i, rng.randint(1, 50000)) for i in range(n)]
            bps = rng.randint(0, 5000)
            rule = quotes.discount_rule('rule-1', 'sponsor-1', 'BPS', str(bps),
                                        [line['lineId'] for line in lines])
            request = quotes.quote_request(
                'order-%d' % seed, order_version=1, scope=support.SCOPE,
                policy_ref='pricing-1', expires_at=support.FAR_FUTURE,
                lines=lines, discounts=[rule])
            quote = quotes.build_quote(assets, policies, request)
            gross = int(quote['totals']['grossAtoms'])
            discount = int(quote['totals']['discountAtoms'])
            payable = int(quote['totals']['payableAtoms'])
            self.assertEqual(gross - discount, payable, seed)
            self.assertEqual(sum(int(r['payableAtoms']) for r in quote['lines']), payable, seed)
            self.assertEqual(sum(int(r['grossAtoms']) for r in quote['lines']), gross, seed)
            parts = _split(payable, rng.randint(1, 3), rng)
            legs = [support.krw_leg('leg-%d' % i, amount) for i, amount in enumerate(parts)]
            plan = quotes.plan_payments(assets, quote, legs, quote['quoteHash'], 1000)
            self.assertEqual(sum(int(leg['amount']['atoms']) for leg in plan['legs']), payable, seed)
            proposal = quotes.propose_line_refund(
                assets, quote, plan, [line['lineId'] for line in lines], plan['planHash'])
            customer = int(proposal['customerRefund']['atoms'])
            burden = sum(int(v) for v in proposal['discountBurdenReversal'].values())
            reversed_gross = int(proposal['grossReversed']['atoms'])
            self.assertEqual(customer + burden, reversed_gross, seed)
            self.assertEqual(reversed_gross, gross, seed)
            self.assertEqual(customer, payable, seed)


class FaceConservationTest(unittest.TestCase):
    def test_seeded_settlement_faces_conserve(self):
        for seed in range(20):
            rng = random.Random(1000 + seed)
            payable = rng.randint(1, 10**9)
            fee_bps = rng.randint(0, 10000)
            policies = support.make_policies()
            policies.register('fee-x', 'PRIMARY_FEE_BPS', {
                'kind': 'PRIMARY_FEE_BPS', 'fee_bps': fee_bps,
                'residual_payee': 'organizer-1', 'fee_payee': 'platform'})
            session = support.make_session(policies=policies)
            try:
                member = support.group([support.krw_line('line-1', payable)],
                                       [support.krw_leg('leg-1', payable)],
                                       settlementPolicyRef='fee-x')
                session.create_order('order-1', order_version=1, scope=support.SCOPE,
                                     groups=[member], now_ms=1000)
                support.capture_and_confirm(session, 'order-1', 'group-1', 'leg-1', 'cap-1', payable)
                result = support.settle(session, 'order-1', 'group-1')
                faces = {a['payee']: a['amount'] for a in result['allocations']}
                self.assertEqual(sum(faces.values()), payable, seed)
                fee = payable * fee_bps // 10000
                self.assertEqual(faces.get('platform', 0), fee, seed)
                self.assertEqual(faces.get('organizer-1', 0), payable - fee, seed)
            finally:
                session.close()


class RejectionAtomicityTest(unittest.TestCase):
    def test_refused_create_order_writes_nothing(self):
        session = support.make_session()
        try:
            bad = support.group([support.krw_line('line-1', 10000)],
                                [support.krw_leg('leg-1', 9999)])  # legs != payable
            with self.assertRaises(Exception):
                session.create_order('order-1', order_version=1, scope=support.SCOPE,
                                     groups=[bad], now_ms=1000)
            self.assertEqual(session.view()['orders'], {})
            self.assertEqual(session.view()['captures']['legs'], [])
        finally:
            session.close()

    def test_refused_refund_writes_no_reservation(self):
        session = support.make_session()
        try:
            support.primary_order(session)
            support.capture_and_confirm(session, 'order-1', 'group-1', 'leg-1', 'cap-1', 10000)
            support.settle(session, 'order-1', 'group-1')
            with self.assertRaises(EconomicsLocalError):
                session.refund_lines('order-1', 'group-1', line_ids=['line-1'],
                                     refund_id='r', authorization={}, refund_policy_ref='refund-1',
                                     reason='x', idempotency_key='k')
            group = session.view('order-1')['orders']['order-1']['groups']['group-1']
            self.assertEqual(group['refundedLines'], [])
            self.assertEqual(group['refundReserved'], {})
        finally:
            session.close()

    def test_over_capture_writes_nothing(self):
        session = support.make_session()
        try:
            support.primary_order(session)
            session.submit_capture('order-1', 'group-1', 'leg-1', 'cap-1',
                                   amount=10000, buyer='buyer-1', nonce='n', now_ms=1000)
            with self.assertRaises(EconomicsLocalError):
                session.submit_capture('order-1', 'group-1', 'leg-1', 'cap-2',
                                       amount=1, buyer='buyer-1', nonce='n', now_ms=1000)
            self.assertNotIn('cap-2', session.view()['captures']['captures'])
        finally:
            session.close()


if __name__ == '__main__':
    unittest.main()