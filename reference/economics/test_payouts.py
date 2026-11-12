"""Payouts: published BANK_PAYOUT_FIXTURE intent and explicit observations."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reference.economics import EconomicsLocalError  # noqa: E402
from reference.economics import support  # noqa: E402


class PayoutLifecycleTest(unittest.TestCase):
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

    def test_send_is_stored_local_intent_not_transmission(self):
        self.session.prepare_payout('order-1', 'group-1', effect_id='eff-1',
                                    payee='organizer-1', amount=9700)
        sent = self.session.send_effect('eff-1')
        self.assertEqual(sent['dispatchDecision'], 'FIRST_SEND_INTENT')
        self.assertTrue(sent['requiresWorkerClaim'])
        effect = self.session.view()['effects']['eff-1']
        self.assertEqual(effect['state'], 'OUTCOME_UNKNOWN')

    def test_full_observation_reaches_done(self):
        self.session.prepare_payout('order-1', 'group-1', effect_id='eff-1',
                                    payee='organizer-1', amount=9700)
        self.session.send_effect('eff-1')
        self.session.observe_effect('eff-1', phase='STATUS', source_id='st-1',
                                    amount=9700, status='SUCCESS')
        final = self.session.observe_effect('eff-1', phase='FUNDS', source_id='fn-1',
                                            amount=9700, movement_id='mv-out-1')
        self.assertEqual(final['state'], 'DONE')
        effect = self.session.view()['effects']['eff-1']
        self.assertEqual(effect['appliedAmount'], 9700)

    def test_observe_unbound_effect_refused(self):
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.observe_effect('missing', phase='STATUS', source_id='s',
                                        amount=1, status='SUCCESS')
        self.assertEqual(str(ctx.exception), 'EFFECT_NOT_BOUND')

    def test_payout_after_full_refund_refused(self):
        assets = support.make_assets()
        group = self.session.view('order-1')['orders']['order-1']['groups']['group-1']
        from reference.economics import quotes
        proposal = quotes.propose_line_refund(assets, group['quote'], group['plan'],
                                              ['line-1'], group['plan']['planHash'])
        self.session.refund_lines('order-1', 'group-1', line_ids=['line-1'],
                                  refund_id='r', authorization=support.authorization(proposal),
                                  refund_policy_ref='refund-1', reason='full',
                                  idempotency_key='ref', route_profile='CASH_REFUND_FIXTURE',
                                  effect_id='eff-refund')
        with self.assertRaises(EconomicsLocalError) as ctx:
            self.session.prepare_payout('order-1', 'group-1', effect_id='eff-2',
                                        payee='organizer-1', amount=9700)
        self.assertEqual(str(ctx.exception), 'GROUP_NOT_COMPLETED')

    def test_all_flags_false_and_evidence_class(self):
        result = self.session.prepare_payout('order-1', 'group-1', effect_id='eff-1',
                                             payee='organizer-1', amount=9700)
        view = self.session.view()
        self.assertEqual(view['evidenceClass'], 'SYNTHETIC_REFERENCE')
        for flag in ('protocolTruth', 'productionConformance', 'productionReadiness',
                     'productionEndpoint', 'fundsExecuted', 'chainWriter', 'fsmDurable',
                     'localDurableData'):
            self.assertFalse(view[flag], flag)
        self.assertEqual(result['payee'], 'organizer-1')


if __name__ == '__main__':
    unittest.main()