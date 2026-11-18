"""Bundles: several OrderLines in one quote, from a synthetic fixture document."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import support  # noqa: E402


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.fixture = support.load_fixture('bundle_order.json')
        self.session = support.make_session()

    def tearDown(self):
        self.session.close()

    def _create(self):
        f = self.fixture
        return self.session.create_order(
            f['orderId'], order_version=f['orderVersion'], scope=f['scope'],
            groups=f['groups'], now_ms=f['nowMs'])

    def test_bundle_totals_and_line_payable(self):
        view = self._create()
        group = view['orders'][self.fixture['orderId']]['groups']['group-1']
        quote = group['quote']
        expected = self.fixture['expected']
        self.assertEqual(quote['totals']['grossAtoms'], expected['grossAtoms'])
        self.assertEqual(quote['totals']['discountAtoms'], expected['discountAtoms'])
        self.assertEqual(quote['totals']['payableAtoms'], expected['payableAtoms'])
        rows = {row['lineId']: row['payableAtoms'] for row in quote['lines']}
        self.assertEqual(rows, expected['linePayable'])
        self.assertEqual(len(quote['lines']), 3)

    def test_bundle_legs_sum_to_payable(self):
        self._create()
        legs = self.session.view()['captures']['legs']
        self.assertEqual(sum(leg['amount'] for leg in legs), 8900)
        self.assertEqual(len(legs), 2)

    def test_bundle_settles_with_fee_split(self):
        self._create()
        oid, gid = self.fixture['orderId'], 'group-1'
        support.capture_and_confirm(self.session, oid, gid, 'leg-1', 'cap-1', 4900)
        support.capture_and_confirm(self.session, oid, gid, 'leg-2', 'cap-2', 4000)
        result = support.settle(self.session, oid, gid)
        faces = {a['payee']: a['amount'] for a in result['allocations']}
        # 8900 payable, 300 bps fee -> fee 267, residual 8633.
        self.assertEqual(faces, {'organizer-1': 8633, 'platform': 267})
        self.assertEqual(sum(faces.values()), 8900)


if __name__ == '__main__':
    unittest.main()