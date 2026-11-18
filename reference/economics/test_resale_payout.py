"""Resale seller payout: BRA faces == Core RESALE allocations == paid effects."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError  # noqa: E402
from reference.economics import support  # noqa: E402
from resale_fsm import ResaleError  # noqa: E402


class ResalePayoutTest(unittest.TestCase):
    def setUp(self):
        self.fixture = support.load_fixture('resale_journey.json')
        self.session = support.make_session()

    def tearDown(self):
        self.session.close()

    def _run(self, journey=None, now_ms=None):
        journey = journey if journey is not None else self.fixture['journey']
        now_ms = now_ms if now_ms is not None else self.fixture['nowMs']
        return self.session.resale_payout(journey, now_ms=now_ms)

    def test_faces_match_and_payouts_done(self):
        result = self._run()
        self.assertEqual(result['faces'], self.fixture['expected']['faces'])
        self.assertTrue(result['facesMatch'])
        for payout in result['payouts']:
            self.assertEqual(payout['state'], 'DONE')
        self.assertEqual(sum(p['amount'] for p in result['payouts']), 15000)

    def test_bra_evidence_is_face_not_funds(self):
        result = self._run()
        self.assertFalse(result['braEvidence']['funds_executed'])
        self.assertFalse(result['braEvidence']['chain_owner_current'])
        self.assertEqual(result['braEvidence']['seller_due'], 13800)

    def test_core_allocations_equal_faces(self):
        result = self._run()
        allocations = {a['payee']: a['amount'] for a in result['coreAllocations']}
        self.assertEqual(allocations, self.fixture['expected']['faces'])

    def test_duplicate_journey_refused(self):
        self._run()
        with self.assertRaises(EconomicsLocalError) as ctx:
            self._run()
        self.assertEqual(str(ctx.exception), 'JOURNEY_EXISTS')

    def test_payout_exceeds_face_refused(self):
        journey = copy.deepcopy(self.fixture['journey'])
        journey['payouts'][0]['amount'] = 13801
        with self.assertRaises(EconomicsLocalError) as ctx:
            self._run(journey)
        self.assertEqual(str(ctx.exception), 'JOURNEY_PAYOUT_EXCEEDS_FACE')

    def test_roles_not_distinct_refused(self):
        journey = copy.deepcopy(self.fixture['journey'])
        journey['resale']['buyerRole'] = journey['primary']['sellerRole']
        with self.assertRaises(EconomicsLocalError) as ctx:
            self._run(journey)
        self.assertEqual(str(ctx.exception), 'JOURNEY_ROLES_NOT_DISTINCT')

    def test_resale_exceeds_cap_refused(self):
        journey = copy.deepcopy(self.fixture['journey'])
        journey['resale']['amount'] = 20001
        with self.assertRaises(EconomicsLocalError) as ctx:
            self._run(journey)
        self.assertEqual(str(ctx.exception), 'JOURNEY_RESALE_EXCEEDS_CAP')

    def test_zero_faces_have_no_allocation(self):
        journey = copy.deepcopy(self.fixture['journey'])
        journey['show']['organizerBps'] = 0
        journey['show']['platformBps'] = 0
        journey['payouts'] = [{'effectId': 'eff-seller', 'payee': 'seller-1', 'amount': 15000}]
        result = self._run(journey)
        self.assertEqual(result['faces'], {'seller-1': 15000, 'organizer-1': 0, 'platform': 0})
        allocations = {a['payee']: a['amount'] for a in result['coreAllocations']}
        self.assertEqual(allocations, {'seller-1': 15000})

    def test_expiry_outside_bra_window_refused(self):
        journey = copy.deepcopy(self.fixture['journey'])
        journey['resale']['expiresMs'] = 10**12
        journey['resale']['rightExpiresMs'] = 10**12
        with self.assertRaises(ResaleError) as ctx:
            self._run(journey)
        self.assertEqual(ctx.exception.code, 'RESERVATION_WINDOW')


if __name__ == '__main__':
    unittest.main()