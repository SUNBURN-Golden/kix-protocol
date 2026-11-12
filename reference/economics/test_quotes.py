"""Authenticated quote calculation and the u128 -> fixture-money boundary."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError  # noqa: E402
from reference.economics import quotes, support  # noqa: E402
import commerce  # noqa: E402
from common import Rejected  # noqa: E402


class QuoteAuthenticationTest(unittest.TestCase):
    def setUp(self):
        self.assets = support.make_assets()
        self.policies = support.make_policies()

    def _request(self, atoms='10000'):
        return quotes.quote_request(
            'order-1', order_version=1, scope=support.SCOPE,
            policy_ref='pricing-1', expires_at=support.FAR_FUTURE,
            lines=[quotes.order_line('line-1', 'inv-1', support.KRW_WIRE, atoms)])

    def test_build_quote_authenticated(self):
        quote = quotes.build_quote(self.assets, self.policies, self._request())
        self.assertEqual(quote['evidenceClass'], 'CALCULATION_ONLY')
        self.assertEqual(quote['totals']['payableAtoms'], '10000')
        self.assertEqual(quote['schemaVersion'], commerce.SCHEMA)

    def test_unauthenticated_policy_refused(self):
        request = self._request()
        request['policyRef'] = 'unknown-policy'
        with self.assertRaises(EconomicsLocalError) as ctx:
            quotes.build_quote(self.assets, self.policies, request)
        self.assertEqual(str(ctx.exception), 'POLICY_NOT_AUTHENTICATED')

    def test_unauthenticated_asset_refused(self):
        request = self._request()
        request['lines'] = [quotes.order_line('line-1', 'inv-1', support.token_wire(), '5')]
        with self.assertRaises(EconomicsLocalError) as ctx:
            quotes.build_quote(self.assets, self.policies, request)
        self.assertEqual(str(ctx.exception), 'ASSET_NOT_AUTHENTICATED')

    def test_validate_quote_round_trip(self):
        quote = quotes.build_quote(self.assets, self.policies, self._request())
        rebuilt = quotes.validate_quote(self.assets, self.policies, quote)
        self.assertEqual(rebuilt['quoteHash'], quote['quoteHash'])

    def test_plan_payments_binds_quote_hash(self):
        quote = quotes.build_quote(self.assets, self.policies, self._request())
        legs = [quotes.payment_leg('leg-1', 'provider-1', 'route-card', support.KRW_WIRE, '10000')]
        plan = quotes.plan_payments(self.assets, quote, legs, quote['quoteHash'], 1000)
        self.assertEqual(plan['quoteHash'], quote['quoteHash'])
        self.assertEqual(len(plan['legs']), 1)
        with self.assertRaises(Rejected):
            quotes.plan_payments(self.assets, quote, legs, 'stale-hash', 1000)


class MoneyBoundTest(unittest.TestCase):
    def setUp(self):
        self.assets = support.make_assets()
        self.policies = support.make_policies()

    def test_u128_above_fixture_bound_refused_not_narrowed(self):
        atoms = str(10**12 + 1)
        request = quotes.quote_request(
            'order-1', order_version=1, scope=support.SCOPE,
            policy_ref='pricing-1', expires_at=support.FAR_FUTURE,
            lines=[quotes.order_line('line-1', 'inv-1', support.KRW_WIRE, atoms)])
        quote = quotes.build_quote(self.assets, self.policies, request)
        # The quote stays valid u128 calculation evidence ...
        self.assertEqual(quote['totals']['payableAtoms'], atoms)
        # ... but binding into the fixture money journey is refused, never rounded.
        with self.assertRaises(EconomicsLocalError) as ctx:
            quotes.require_money_bound(quote)
        self.assertEqual(str(ctx.exception), 'AMOUNT_EXCEEDS_FIXTURE_MONEY_BOUND')

    def test_at_bound_accepted(self):
        request = quotes.quote_request(
            'order-1', order_version=1, scope=support.SCOPE,
            policy_ref='pricing-1', expires_at=support.FAR_FUTURE,
            lines=[quotes.order_line('line-1', 'inv-1', support.KRW_WIRE, str(10**12))])
        quote = quotes.build_quote(self.assets, self.policies, request)
        self.assertEqual(quotes.require_money_bound(quote), 10**12)

    def test_create_order_refuses_above_bound(self):
        session = support.make_session(assets=self.assets, policies=self.policies)
        try:
            line = quotes.order_line('line-1', 'inv-1', support.KRW_WIRE, str(10**12 + 1))
            leg = quotes.payment_leg('leg-1', 'provider-1', 'route-card', support.KRW_WIRE, str(10**12 + 1))
            with self.assertRaises(EconomicsLocalError) as ctx:
                session.create_order('order-1', order_version=1, scope=support.SCOPE,
                                     groups=[support.group([line], [leg])], now_ms=1000)
            self.assertEqual(str(ctx.exception), 'AMOUNT_EXCEEDS_FIXTURE_MONEY_BOUND')
        finally:
            session.close()


class FreeDetectionTest(unittest.TestCase):
    def test_is_free_and_line_payable(self):
        assets, policies = support.make_assets(), support.make_policies()
        request = quotes.quote_request(
            'order-1', order_version=1, scope=support.SCOPE,
            policy_ref='pricing-1', expires_at=support.FAR_FUTURE,
            lines=[quotes.order_line('line-1', 'inv-1', support.KRW_WIRE, '0')])
        quote = quotes.build_quote(assets, policies, request)
        self.assertTrue(quotes.is_free(quote))
        self.assertEqual(quotes.line_payable(quote, 'line-1'), 0)
        with self.assertRaises(EconomicsLocalError):
            quotes.line_payable(quote, 'missing')


if __name__ == '__main__':
    unittest.main()