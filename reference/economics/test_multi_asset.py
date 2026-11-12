"""Multiple assets: per-asset groups, KRW-only money binding, no FX."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError  # noqa: E402
from reference.economics import quotes, support  # noqa: E402
from common import Rejected  # noqa: E402


class MultiAssetTest(unittest.TestCase):
    def setUp(self):
        self.fixture = support.load_fixture('multi_asset_order.json')
        self.session = support.make_session(
            assets=support.make_assets(*self.fixture['assets']))
        f = self.fixture
        self.session.create_order(f['orderId'], order_version=f['orderVersion'],
                                  scope=f['scope'], groups=f['groups'], now_ms=f['nowMs'])

    def tearDown(self):
        self.session.close()

    def test_krw_executable_token_not(self):
        groups = self.session.view(self.fixture['orderId'])['orders'][self.fixture['orderId']]['groups']
        expected = self.fixture['expected']['krwExecutable']
        self.assertEqual(groups['group-krw']['krwExecutable'], expected['group-krw'])
        self.assertEqual(groups['group-token']['krwExecutable'], expected['group-token'])
        self.assertIsNone(groups['group-token']['settlementId'])

    def test_token_quote_stays_in_token_atoms_no_fx(self):
        groups = self.session.view(self.fixture['orderId'])['orders'][self.fixture['orderId']]['groups']
        token_quote = groups['group-token']['quote']
        self.assertEqual(token_quote['totals']['payableAtoms'], self.fixture['expected']['tokenPayableAtoms'])
        self.assertEqual(token_quote['asset']['reference'], 'fixture-token')

    def test_token_capture_admission_works(self):
        result = self.session.submit_capture(self.fixture['orderId'], 'group-token', 'leg-1',
                                             'cap-tok', amount=500, buyer='buyer-1', nonce='n', now_ms=1000)
        self.assertEqual(result['outcome'], 'new_success')
        self.session.complete_capture('cap-tok', outcome='CONFIRMED', source_id='s', now_ms=1100)
        legs = {(leg['orderId'], leg['groupId']): leg for leg in self.session.view()['captures']['legs']}
        self.assertEqual(legs[(self.fixture['orderId'], 'group-token')]['confirmed'], 500)

    def test_token_settlement_refused_krw_only(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.settle_group(self.fixture['orderId'], 'group-token',
                                      movement_id='mv', idempotency_key='k')
        self.assertEqual(str(ctx.exception), 'FIXTURE_MONEY_KRW_ONLY')

    def test_token_refund_refused_krw_only(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.refund_lines(self.fixture['orderId'], 'group-token', line_ids=['line-1'],
                                      refund_id='r', authorization={}, refund_policy_ref='refund-1',
                                      reason='x', idempotency_key='k')
        self.assertEqual(str(ctx.exception), 'FIXTURE_MONEY_KRW_ONLY')

    def test_krw_group_settles_independently(self):
        support.capture_and_confirm(self.session, self.fixture['orderId'], 'group-krw', 'leg-1', 'cap-krw', 10000)
        result = support.settle(self.session, self.fixture['orderId'], 'group-krw')
        faces = {a['payee']: a['amount'] for a in result['allocations']}
        self.assertEqual(faces, {'organizer-1': 9700, 'platform': 300})

    def test_mixed_asset_single_quote_refused(self):
        token = self.fixture['assets'][0]
        lines = [support.krw_line('line-1', 100),
                 quotes.order_line('line-2', 'inv-2', token, '100')]
        request = quotes.quote_request('order-x', order_version=1, scope=support.SCOPE,
                                       policy_ref='pricing-1', expires_at=support.FAR_FUTURE, lines=lines)
        assets = support.make_assets(*self.fixture['assets'])
        with self.assertRaises(Rejected) as ctx:
            quotes.build_quote(assets, support.make_policies(), request)
        self.assertEqual(str(ctx.exception), 'MIXED_QUOTE_ASSETS')


if __name__ == '__main__':
    unittest.main()