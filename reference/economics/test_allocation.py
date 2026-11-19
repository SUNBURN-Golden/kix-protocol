"""Allocation: settlement faces, W0 caller-order distribution, payout caps."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError, PolicyAuthentication  # noqa: E402
from reference.economics import support  # noqa: E402
from mock_settlement import SettlementError  # noqa: E402


class AllocationTest(unittest.TestCase):
    def setUp(self):
        self.session = support.make_session()
        support.primary_order(self.session)
        support.capture_and_confirm(self.session, 'order-1', 'group-1', 'leg-1', 'cap-1', 10000)

    def tearDown(self):
        self.session.close()

    def test_faces_match_fsm_and_core_and_conserve(self):
        result = support.settle(self.session, 'order-1', 'group-1')
        faces = {a['payee']: a['amount'] for a in result['allocations']}
        self.assertEqual(faces, {'organizer-1': 9700, 'platform': 300})
        self.assertEqual(sum(faces.values()), 10000)
        claim = result['settlement']['claim']
        obligation_faces = {row['payee']: row['face'] for row in claim['obligations']}
        self.assertEqual(obligation_faces, faces)
        self.assertEqual(claim['confirmed_cash'], 10000)

    def test_settle_requires_all_captures_confirmed(self):
        session = support.make_session()
        try:
            support.primary_order(session, order_id='order-2')
            session.submit_capture('order-2', 'group-1', 'leg-1', 'cap-1',
                                   amount=10000, buyer='buyer-1', nonce='n', now_ms=1000)
            with self.assertRaises(EconomicsLocalError) as ctx:
                support.settle(session, 'order-2', 'group-1')
            self.assertEqual(str(ctx.exception), 'CAPTURES_INCOMPLETE')
        finally:
            session.close()

    def test_distribution_w0_caller_order(self):
        support.settle(self.session, 'order-1', 'group-1')
        result = self.session.distribute_group('order-1', 'group-1',
                                               order=['platform', 'organizer-1'],
                                               idempotency_key='dist-1')
        self.assertEqual(result['effect'], {'platform': 300, 'organizer-1': 9700})
        claim = result['settlement']['claim']
        self.assertEqual(claim['distribution_order'], ['platform', 'organizer-1'])
        self.assertEqual(claim['undistributed_cash'], 0)

    def test_distribution_payee_set_must_match(self):
        support.settle(self.session, 'order-1', 'group-1')
        with self.assertRaises(SettlementError) as ctx:
            self.session.distribute_group('order-1', 'group-1',
                                          order=['organizer-1'], idempotency_key='dist-1')
        self.assertEqual(ctx.exception.code, 'DISTRIBUTION_ORDER_MISMATCH')

    def test_distribute_once_only(self):
        support.settle(self.session, 'order-1', 'group-1')
        self.session.distribute_group('order-1', 'group-1',
                                      order=['organizer-1', 'platform'], idempotency_key='dist-1')
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.distribute_group('order-1', 'group-1',
                                          order=['organizer-1', 'platform'], idempotency_key='dist-2')
        self.assertEqual(str(ctx.exception), 'GROUP_NOT_SETTLED')

    def test_zero_fee_single_obligation(self):
        policies = support.make_policies()
        policies.register('fee-0', 'PRIMARY_FEE_BPS', {
            'kind': 'PRIMARY_FEE_BPS', 'fee_bps': 0,
            'residual_payee': 'organizer-1', 'fee_payee': 'platform'})
        session = support.make_session(policies=policies)
        try:
            member = support.group([support.krw_line('line-1', 10000)],
                                   [support.krw_leg('leg-1', 10000)],
                                   settlementPolicyRef='fee-0')
            session.create_order('order-1', order_version=1, scope=support.SCOPE,
                                 groups=[member], now_ms=1000)
            support.capture_and_confirm(session, 'order-1', 'group-1', 'leg-1', 'cap-1', 10000)
            result = support.settle(session, 'order-1', 'group-1')
            faces = {a['payee']: a['amount'] for a in result['allocations']}
            self.assertEqual(faces, {'organizer-1': 10000})
            session.distribute_group('order-1', 'group-1', order=['organizer-1'],
                                     idempotency_key='dist-1')
        finally:
            session.close()


class PayoutCapTest(unittest.TestCase):
    def setUp(self):
        self.session = support.make_session()
        support.primary_order(self.session)
        support.capture_and_confirm(self.session, 'order-1', 'group-1', 'leg-1', 'cap-1', 10000)
        support.settle(self.session, 'order-1', 'group-1')
        self.session.distribute_group('order-1', 'group-1',
                                      order=['organizer-1', 'platform'], idempotency_key='dist-1')
        self.session.complete_group('order-1', 'group-1')

    def tearDown(self):
        self.session.close()

    def test_payout_requires_distribution(self):
        session = support.make_session()
        try:
            support.primary_order(session, order_id='order-2')
            support.capture_and_confirm(session, 'order-2', 'group-1', 'leg-1', 'cap-1', 10000)
            support.settle(session, 'order-2', 'group-1')
            session.complete_group('order-2', 'group-1')
            with self.assertRaises(EconomicsLocalError) as ctx:
                session.prepare_payout('order-2', 'group-1', effect_id='e', payee='organizer-1', amount=1)
            self.assertEqual(str(ctx.exception), 'PAYOUT_NOT_DISTRIBUTED')
        finally:
            session.close()

    def test_payout_exceeds_distributed_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.prepare_payout('order-1', 'group-1', effect_id='e',
                                        payee='organizer-1', amount=9701)
        self.assertEqual(str(ctx.exception), 'PAYOUT_EXCEEDS_DISTRIBUTED')

    def test_payout_unknown_payee_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.prepare_payout('order-1', 'group-1', effect_id='e',
                                        payee='stranger', amount=1)
        self.assertEqual(str(ctx.exception), 'PAYOUT_PAYEE_UNKNOWN')

    def test_partial_payouts_accumulate_to_face(self):
        self.session.prepare_payout('order-1', 'group-1', effect_id='e1', payee='organizer-1', amount=5000)
        self.session.prepare_payout('order-1', 'group-1', effect_id='e2', payee='organizer-1', amount=4700)
        with self.assertRaises(EconomicsLocalError):
            self.session.prepare_payout('order-1', 'group-1', effect_id='e3', payee='organizer-1', amount=1)


if __name__ == '__main__':
    unittest.main()