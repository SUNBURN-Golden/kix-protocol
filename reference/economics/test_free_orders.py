"""Free orders: zero payable, zero legs, no money pipeline, completed at creation."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError  # noqa: E402
from reference.economics import support  # noqa: E402


class FreeOrderTest(unittest.TestCase):
    def setUp(self):
        self.fixture = support.load_fixture('free_order.json')
        self.session = support.make_session()

    def tearDown(self):
        self.session.close()

    def _create(self):
        f = self.fixture
        return self.session.create_order(
            f['orderId'], order_version=f['orderVersion'], scope=f['scope'],
            groups=f['groups'], now_ms=f['nowMs'])

    def test_free_order_completes_at_creation(self):
        view = self._create()
        group = view['orders'][self.fixture['orderId']]['groups']['group-1']
        self.assertEqual(group['phase'], self.fixture['expected']['phase'])
        self.assertTrue(group['free'])
        self.assertEqual(group['payable'], 0)
        self.assertIsNone(group['settlementId'])
        self.assertIsNone(group['eventId'])

    def test_free_order_plans_zero_legs(self):
        self._create()
        legs = self.session.view()['captures']['legs']
        self.assertEqual(len(legs), self.fixture['expected']['legCount'])

    def test_capture_on_free_order_refused(self):
        self._create()
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.submit_capture(
                self.fixture['orderId'], 'group-1', 'leg-1', 'cap-1',
                amount=1, buyer='buyer-1', nonce='n', now_ms=1000)
        self.assertEqual(str(ctx.exception), 'UNKNOWN_LEG')

    def test_settle_free_order_refused(self):
        self._create()
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.settle_group(self.fixture['orderId'], 'group-1',
                                      movement_id='mv', idempotency_key='k')
        self.assertEqual(str(ctx.exception), 'FREE_ORDER_NO_SETTLEMENT')

    def test_refund_free_order_refused(self):
        self._create()
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.refund_lines(
                self.fixture['orderId'], 'group-1', line_ids=['line-1'],
                refund_id='r', authorization={}, refund_policy_ref='refund-1',
                reason='x', idempotency_key='k')
        self.assertEqual(str(ctx.exception), 'FREE_ORDER_NO_REFUND')

    def test_money_fields_on_free_order_refused(self):
        f = self.fixture
        bad = dict(f['groups'][0], settlementPolicyRef='fee-1')
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.create_order(f['orderId'], order_version=1, scope=f['scope'],
                                      groups=[bad], now_ms=f['nowMs'])
        self.assertEqual(str(ctx.exception), 'FREE_ORDER_MONEY_FIELDS')


if __name__ == '__main__':
    unittest.main()