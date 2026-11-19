"""Discounts: caller FIXED/BPS rules, caps, bearers and proportional split."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import quotes, support  # noqa: E402
from common import Rejected  # noqa: E402


class DiscountTest(unittest.TestCase):
    def setUp(self):
        self.assets = support.make_assets()
        self.policies = support.make_policies()

    def _quote(self, lines, discounts):
        request = quotes.quote_request(
            'order-1', order_version=1, scope=support.SCOPE,
            policy_ref='pricing-1', expires_at=support.FAR_FUTURE,
            lines=lines, discounts=discounts)
        return quotes.build_quote(self.assets, self.policies, request)

    def test_fixed_discount_reduces_payable_and_records_bearer(self):
        lines = [support.krw_line('line-1', 10000)]
        rule = quotes.discount_rule('rule-1', 'sponsor-1', 'FIXED', '1000', ['line-1'])
        quote = self._quote(lines, [rule])
        self.assertEqual(quote['totals']['payableAtoms'], '9000')
        self.assertEqual(quote['totals']['discountAtoms'], '1000')
        row = quote['lines'][0]
        self.assertEqual(row['discounts'], [{'ruleId': 'rule-1', 'bearerRef': 'sponsor-1', 'atoms': '1000'}])

    def test_bps_discount_with_cap(self):
        lines = [support.krw_line('line-1', 10000)]
        rule = quotes.discount_rule('rule-1', 'platform', 'BPS', '5000', ['line-1'], cap_atoms='1000')
        quote = self._quote(lines, [rule])
        # 50% of 10000 = 5000, capped to 1000.
        self.assertEqual(quote['totals']['discountAtoms'], '1000')
        self.assertEqual(quote['totals']['payableAtoms'], '9000')

    def test_discount_exceeds_payable_refused(self):
        lines = [support.krw_line('line-1', 1000)]
        rule = quotes.discount_rule('rule-1', 'sponsor-1', 'FIXED', '2000', ['line-1'])
        with self.assertRaises(Rejected) as ctx:
            self._quote(lines, [rule])
        self.assertEqual(str(ctx.exception), 'DISCOUNT_EXCEEDS_PAYABLE')

    def test_proportional_split_largest_remainder(self):
        lines = [support.krw_line('line-a', 5000), support.krw_line('line-b', 3000)]
        rule = quotes.discount_rule('rule-1', 'sponsor-1', 'FIXED', '1000', ['line-a', 'line-b'])
        quote = self._quote(lines, [rule])
        rows = {row['lineId']: row for row in quote['lines']}
        self.assertEqual(rows['line-a']['discountAtoms'], '625')
        self.assertEqual(rows['line-b']['discountAtoms'], '375')
        self.assertEqual(quote['totals']['payableAtoms'], '7000')

    def test_refund_reverses_discount_burden_to_bearer(self):
        lines = [support.krw_line('line-1', 10000)]
        rule = quotes.discount_rule('rule-1', 'sponsor-1', 'FIXED', '1000', ['line-1'])
        quote = self._quote(lines, [rule])
        legs = [support.krw_leg('leg-1', 9000)]
        plan = quotes.plan_payments(self.assets, quote, legs, quote['quoteHash'], 1000)
        proposal = quotes.propose_line_refund(self.assets, quote, plan, ['line-1'], plan['planHash'])
        # customer refund is the payable; the discount burden reverses to the bearer.
        self.assertEqual(proposal['customerRefund']['atoms'], '9000')
        self.assertEqual(proposal['grossReversed']['atoms'], '10000')
        self.assertEqual(proposal['discountBurdenReversal'], {'sponsor-1': '1000'})
        self.assertFalse(proposal['executionAuthorized'])


if __name__ == '__main__':
    unittest.main()