"""Asset and policy authentication: fail-closed registration and binding.

Hash binding is calculation integrity, not source authentication; these tests
prove the local registry refuses unregistered or altered documents before any
economics operation may use them.
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError  # noqa: E402
from reference.economics.authentication import (  # noqa: E402
    AssetAuthentication, PolicyAuthentication,
)
from reference.economics import support  # noqa: E402


class AssetAuthenticationTest(unittest.TestCase):
    def setUp(self):
        self.assets = AssetAuthentication()

    def test_register_then_authenticate(self):
        self.assets.register(support.KRW_WIRE)
        spec = self.assets.authenticate(support.KRW_WIRE)
        self.assertEqual(spec.to_dict(), support.KRW_WIRE)

    def test_equal_reregistration_is_idempotent(self):
        first = self.assets.register(support.KRW_WIRE)
        second = self.assets.register(support.KRW_WIRE)
        self.assertEqual(first, second)
        self.assertEqual(len(self.assets.view()), 1)

    def test_unregistered_asset_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.assets.authenticate(support.token_wire())
        self.assertEqual(str(ctx.exception), 'ASSET_NOT_AUTHENTICATED')

    def test_altered_asset_refused(self):
        self.assets.register(support.KRW_WIRE)
        altered = dict(support.KRW_WIRE, decimals=2)
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.assets.authenticate(altered)
        self.assertEqual(str(ctx.exception), 'ASSET_NOT_AUTHENTICATED')

    def test_invalid_wire_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.assets.register({'namespace': 'fiat'})
        self.assertEqual(str(ctx.exception), 'ASSET_WIRE_INVALID')

    def test_view_is_detached(self):
        self.assets.register(support.KRW_WIRE)
        view = self.assets.view()
        view[0]['decimals'] = 99
        self.assertEqual(self.assets.authenticate(support.KRW_WIRE).decimals, 0)


class PolicyAuthenticationTest(unittest.TestCase):
    def setUp(self):
        self.policies = PolicyAuthentication()

    def test_register_then_authenticate(self):
        doc = {'document': {'synthetic': True}}
        self.policies.register('pricing-1', 'QUOTE_PRICING', doc)
        self.assertEqual(self.policies.authenticate('pricing-1', 'QUOTE_PRICING'), doc)

    def test_unregistered_policy_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.policies.authenticate('missing', 'QUOTE_PRICING')
        self.assertEqual(str(ctx.exception), 'POLICY_NOT_AUTHENTICATED')

    def test_kind_mismatch_refused(self):
        self.policies.register('refund-1', 'REFUND_FROZEN_LINE_PRICE', {})
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.policies.authenticate('refund-1', 'QUOTE_PRICING')
        self.assertEqual(str(ctx.exception), 'POLICY_KIND_MISMATCH')

    def test_binding_conflict_refused(self):
        self.policies.register('p1', 'QUOTE_PRICING', {'document': {'a': 1}})
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.policies.register('p1', 'QUOTE_PRICING', {'document': {'a': 2}})
        self.assertEqual(str(ctx.exception), 'POLICY_BINDING_CONFLICT')

    def test_unknown_kind_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.policies.register('p1', 'NOT_A_KIND', {})
        self.assertEqual(str(ctx.exception), 'POLICY_KIND_UNKNOWN')

    def test_invalid_ref_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.policies.register('', 'QUOTE_PRICING', {'document': {}})
        self.assertEqual(str(ctx.exception), 'POLICY_REF_INVALID')

    def test_primary_fee_policy_uses_settlement_validator(self):
        good = {'kind': 'PRIMARY_FEE_BPS', 'fee_bps': 300,
                'residual_payee': 'organizer-1', 'fee_payee': 'platform'}
        self.policies.register('fee-1', 'PRIMARY_FEE_BPS', good)
        self.assertEqual(self.policies.authenticate('fee-1', 'PRIMARY_FEE_BPS'), good)
        bad = dict(good, fee_bps=20000)
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.policies.register('fee-bad', 'PRIMARY_FEE_BPS', bad)
        self.assertTrue(str(ctx.exception).startswith('POLICY_SETTLEMENT_INVALID'))

    def test_primary_fee_payee_collision_refused(self):
        bad = {'kind': 'PRIMARY_FEE_BPS', 'fee_bps': 300,
               'residual_payee': 'same', 'fee_payee': 'same'}
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.policies.register('fee-bad', 'PRIMARY_FEE_BPS', bad)
        self.assertTrue(str(ctx.exception).startswith('POLICY_SETTLEMENT_INVALID'))

    def test_resale_split_basis_bound(self):
        self.policies.register('resale-1', 'RESALE_SPLIT_BPS',
                               {'organizer_bps': 500, 'platform_bps': 300})
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.policies.register('resale-bad', 'RESALE_SPLIT_BPS',
                                   {'organizer_bps': 6000, 'platform_bps': 5000})
        self.assertEqual(str(ctx.exception), 'POLICY_SPLIT_EXCEEDS_BASIS')

    def test_authenticate_returns_detached_copy(self):
        self.policies.register('pricing-1', 'QUOTE_PRICING', {'document': {'a': 1}})
        doc = self.policies.authenticate('pricing-1', 'QUOTE_PRICING')
        doc['document']['a'] = 99
        self.assertEqual(
            self.policies.authenticate('pricing-1', 'QUOTE_PRICING')['document']['a'], 1)


if __name__ == '__main__':
    unittest.main()