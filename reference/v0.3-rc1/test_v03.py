"""Behavioral regressions for the supplied independent v0.2 counterexamples."""
import copy
import itertools
import tempfile
import unittest
from pathlib import Path
from common import inventory_id, digest
from core import Core, Rejected
from test_core import Harness, POLICY
from test_v02 import raw


class V03Regressions(unittest.TestCase):
    def setUp(self):
        self.h=Harness(); self.addCleanup(self.h.c.db.close)

    def refund(self):
        h=self.h; h.event(); h.purchase(); h.run('cancel_event',eventId='show')
        h.effect('pg','primary','REFUND',100000,routeProfile='PG_ORIGINAL_CANCEL_FIXTURE')

    def payout(self):
        h=self.h; h.event(); h.purchase(); h.run('complete_event',eventId='show')
        h.effect('p','primary','PAYOUT',95000,'primary-0')

    def partial(self):
        self.payout(); h=self.h
        h.observe('p','STATUS','SUCCESS',amount=40000); h.observe('p','FUNDS',amount=40000)

    def final(self,**changes):
        b=dict(effectId='p',providerOperationId='provider-p',paymentId='pay-primary',beneficiary='organizer',
            amount=40000,unexecutedAmount=55000,currency='KRW',sourceId='final-p',fenceRef='closed-remaining-p',
            sourceCursor='fixture-final:1',observedAt=0,contractRef='fixture:partial-final:v1')
        b.update(changes); return self.h.source('finalize_effect',**b)

    def statement(self,amount=100000):
        return raw('settle_capture',tradeId='primary',paymentId='pay-primary',amount=amount,grossAmount=100000,
            feeAmount=100000-amount,taxAmount=0,heldAmount=0,adjustmentAmount=0,feeBearer='platform',
            currency='KRW',contractRef='fixture:settlement:v1',movementId='early')

    def test_R01_resolved_statement_not_counted_unposted(self):
        h=self.h; h.event(); h.prepare()
        self.assertEqual(h.c.ingest('early',self.statement(),fixture_authenticated=True)['state'],'REVIEW')
        h.capture(settle=False)
        h.c.apply_observation('early',fixture_authenticated=True)
        f=h.c.inbox_summary('show')
        self.assertEqual((f['observedMovementAmountUnderReview'],f['eventReviewFacts']),(0,0))
        self.assertEqual(h.c.snapshot()['trades']['primary']['settled'],100000)
        self.assertEqual(h.c.db.execute("SELECT resolution FROM review_facts WHERE action='settle_capture'").fetchone()[0],'RESOLVED')

    def test_statement_ledger_and_resolution_rollback_together(self):
        h=self.h; h.event(); h.prepare(); h.c.ingest('early',self.statement(),fixture_authenticated=True); h.capture(settle=False)
        with self.assertRaises(RuntimeError): h.c.apply_observation('early',fixture_authenticated=True,fail_before_apply_commit=True)
        self.assertEqual(h.c.snapshot()['trades']['primary']['settled'],0)
        self.assertEqual(h.c.inbox_summary('show')['observedMovementAmountUnderReview'],100000)
        h.c.apply_observation('early',fixture_authenticated=True)
        self.assertEqual(h.c.inbox_summary('show')['observedMovementAmountUnderReview'],0)

    def test_one_applied_variant_does_not_resolve_conflicting_statement(self):
        h=self.h; h.event(); h.prepare()
        h.c.ingest('early',self.statement(),fixture_authenticated=True)
        h.c.ingest('changed',self.statement(97000),fixture_authenticated=True)
        h.capture(settle=False); h.c.apply_observation('early',fixture_authenticated=True)
        f=h.c.inbox_summary('show'); self.assertEqual(f['conflictingReviewFacts'],1)
        self.assertEqual(f['observedMovementAmountUnderReview'],0)
        self.assertEqual(h.c.db.execute("SELECT resolution FROM review_facts WHERE action='settle_capture'").fetchone()[0],'CONFLICT')

    def test_R02_R07_credit_and_fence_both_orders_block_new_refund(self):
        for order in itertools.permutations(('CUSTOMER_CREDIT_CONFIRMED','FENCED_FAILURE')):
            with self.subTest(order=order):
                if self.h.c.snapshot()['events']:
                    self.h=Harness(); self.addCleanup(self.h.c.db.close)
                self.refund(); h=self.h
                for phase in order:
                    extra=dict(fenceRef='fence',fenceProvenance='synthetic_final_provider_fence') if phase=='FENCED_FAILURE' else {}
                    h.observe('pg',phase,**extra)
                x=h.c.snapshot()['effects']['pg']; self.assertEqual(x['state'],'EVIDENCE_CONFLICT')
                self.assertEqual(x['customerCreditConfirmed'],100000)
                with self.assertRaisesRegex(Rejected,'OBLIGATION_EVIDENCE_CONFLICT'):
                    h.effect('cash','primary','REFUND',100000)

    def test_late_positive_fact_stops_prepared_replacement(self):
        self.refund(); h=self.h
        h.observe('pg','FENCED_FAILURE',fenceRef='fence',fenceProvenance='synthetic_final_provider_fence')
        h.run('prepare_effect',effectId='cash',tradeId='primary',kind='REFUND',amount=100000)
        h.observe('pg','CUSTOMER_CREDIT_CONFIRMED')
        self.assertEqual(h.c.snapshot()['effects']['cash']['state'],'ABORTED')
        self.assertEqual(h.run('send_effect',effectId='cash')['result']['dispatchDecision'],'BLOCKED')

    def test_R03_partial_final_releases_only_unexecuted_and_classifies(self):
        self.partial(); h=self.h; h.run('cancel_event',eventId='show')
        self.assertEqual(h.c.view('finance-adapter','show','finance')['refundUnclassified'],100000)
        self.final(); f=h.c.view('finance-adapter','show','finance')
        self.assertEqual((f['payoutOutcomeUnknown'],f['refundUnclassified'],f['organizerRecoveryOutstanding']),(0,0,40000))
        self.assertEqual(h.c.snapshot()['effects']['p']['unexecutedFinalAmount'],55000)

    def test_partial_fence_requires_matched_total_and_correct_remainder(self):
        self.partial()
        for changes in (dict(amount=50000,unexecutedAmount=45000),dict(unexecutedAmount=55001),dict(observedAt=1)):
            with self.assertRaises(Rejected): self.final(**changes)
        self.assertEqual(self.h.c.snapshot()['effects']['p']['state'],'OUTCOME_UNKNOWN')

    def test_R04_return_applied_fragment_before_and_after_finalization(self):
        for finalize_first in (False,True):
            with self.subTest(finalize_first=finalize_first):
                if self.h.c.snapshot()['events']:
                    self.h=Harness(); self.addCleanup(self.h.c.db.close)
                self.partial(); h=self.h; h.run('cancel_event',eventId='show')
                if finalize_first: self.final()
                h.source('observe_return',effectId='p',paymentId='pay-primary',payer='organizer',amount=40000,currency='KRW',movementId='return')
                if not finalize_first: self.final()
                self.assertEqual(h.c.view('finance-adapter','show','finance')['organizerRecoveryOutstanding'],0)
                self.assertEqual(h.c.snapshot()['effects']['p']['returned'],40000)
                with self.assertRaisesRegex(Rejected,'EXCESS_RETURN'):
                    h.source('observe_return',effectId='p',paymentId='pay-primary',payer='organizer',amount=1,currency='KRW',movementId='extra')

    def test_late_execution_after_partial_fence_is_conflict(self):
        self.partial(); self.final(); h=self.h
        h.observe('p','STATUS','SUCCESS',amount=95000,source_id='late')
        self.assertEqual(h.c.snapshot()['effects']['p']['state'],'EVIDENCE_CONFLICT')
        self.assertEqual(h.c.snapshot()['effects']['p']['appliedAmount'],40000)

    def claim(self,worker='w'):
        return self.h.run('claim_effect',effectId='p',workerId=worker,leaseSeconds=30)['result']['claimGeneration']

    def dispatch(self,g,**fault):
        h=self.h; return h.c.execute('dispatch-'+str(h.seq+1),'operator','dispatch_effect',
            dict(domain=Core.DOMAIN,effectId='p',workerId='w',claimGeneration=g),**fault)['result']

    def test_R05_first_intent_response_loss_can_be_claimed_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            h=Harness(Core(str(Path(td)/'db'))); self.h=h; self.addCleanup(h.c.db.close)
            h.event(); h.purchase(); h.run('complete_event',eventId='show')
            h.run('prepare_effect',effectId='p',tradeId='primary',kind='PAYOUT',amount=95000,allocationId='primary-0')
            with self.assertRaises(ConnectionError): h.c.execute('lost','operator','send_effect',dict(domain=Core.DOMAIN,effectId='p'),lose_response=True)
            h.c.db.close(); h.c=Core(str(Path(td)/'db')); self.addCleanup(h.c.db.close)
            g=self.claim(); out=self.dispatch(g)
            self.assertEqual(out['dispatchDecision'],'SUBMIT_SAME_REQUEST')
            self.assertEqual(out['requestHash'],digest(h.c.snapshot()['effects']['p']['request']))

    def test_dispatch_loss_requires_stable_key_lookup_before_resubmit(self):
        self.payout(); h=self.h; g=self.claim()
        with self.assertRaises(ConnectionError): self.dispatch(g,lose_response=True)
        with self.assertRaisesRegex(Rejected,'SOURCE_LOOKUP_REQUIRED'):
            h.run('dispatch_effect',effectId='p',workerId='w',claimGeneration=g)
        x=h.c.snapshot()['effects']['p']
        h.source('observe_dispatch_lookup',effectId='p',idempotencyKey=x['idempotencyKey'],requestHash=x['requestHash'],result='NOT_FOUND_REPLAY_SAFE',lookupRef='lookup-1',observedAt=0)
        out=h.run('dispatch_effect',effectId='p',workerId='w',claimGeneration=g)['result']
        self.assertEqual((out['idempotencyKey'],out['requestBytes']),(x['idempotencyKey'],x['requestBytes']))
        with self.assertRaisesRegex(Rejected,'SOURCE_LOOKUP_REQUIRED'): h.run('dispatch_effect',effectId='p',workerId='w',claimGeneration=g)

    def test_cancel_stale_worker_and_expired_window_block_dispatch(self):
        self.payout(); h=self.h; g=self.claim()
        h.run('advance_clock',now=30); self.claim('new-worker')
        with self.assertRaisesRegex(Rejected,'STALE_DISPATCH_CLAIM'): h.run('dispatch_effect',effectId='p',workerId='w',claimGeneration=g)
        h.run('advance_clock',now=3600); g=self.claim()
        with self.assertRaisesRegex(Rejected,'IDEMPOTENCY_WINDOW_EXPIRED'): h.run('dispatch_effect',effectId='p',workerId='w',claimGeneration=g)
        h.run('cancel_event',eventId='show')
        with self.assertRaisesRegex(Rejected,'DISPATCH_OBLIGATION_CHANGED'): h.run('dispatch_effect',effectId='p',workerId='w',claimGeneration=g)

    def test_R06_raw_conflict_changes_global_digest(self):
        h=self.h; h.event(); h.c.ingest('same',b'one'); a=h.c.inbox_summary('show')
        with self.assertRaises(Rejected): h.c.ingest('same',b'two')
        b=h.c.inbox_summary('show'); self.assertNotEqual(a['evidenceDigest'],b['evidenceDigest'])
        self.assertEqual(b['globalRawConflictCount'],1); self.assertFalse(b['completenessAttested'])

    def test_R08_listing_day_is_not_checkout_day(self):
        h=self.h; h.event(); h.purchase()
        r=h.run('create_listing','A',listingId='L',ticketId=h.right(),expectedVersion=1,amount=120000,expiresAt=86400)['result']
        with self.assertRaisesRegex(Rejected,'INVALID_RESERVATION_EXPIRY'):
            h.run('reserve_listing','B',listingId='L',listingHash=r['termsHash'],tradeId='r',expiresAt=86400)
        h.run('reserve_listing','B',listingId='L',listingHash=r['termsHash'],tradeId='r',expiresAt=900)
        h.run('advance_clock',now=900); h.capture('r')
        with self.assertRaisesRegex(Rejected,'TRADE_NOT_COMMITTABLE'): h.run('commit_trade',tradeId='r')

    def test_R09_collision_pairs_get_distinct_inventory(self):
        h=self.h; h.event('a',['b/c']); h.event('a/b',['c'])
        self.assertEqual(len(h.c.snapshot()['inventory']),2)
        self.assertNotEqual(inventory_id('organizer','a','main','b/c'),inventory_id('organizer','a/b','main','c'))
        self.assertNotEqual(inventory_id('one','a','main','c'),inventory_id('two','a','main','c'))
        self.assertNotEqual(inventory_id('one','a','main','c'),inventory_id('one','a','next','c'))

    def test_conflict_and_resolved_evidence_survive_rebuild(self):
        self.refund(); h=self.h
        h.observe('pg','CUSTOMER_CREDIT_CONFIRMED')
        h.observe('pg','FENCED_FAILURE',fenceRef='fence',fenceProvenance='synthetic_final_provider_fence')
        x=h.c.export_replay(); c=Core.rebuild_fixture(x); self.addCleanup(c.db.close)
        self.assertEqual(c.snapshot(),h.c.snapshot())
        self.assertEqual(c.inbox_summary('show'),h.c.inbox_summary('show'))

if __name__=='__main__': unittest.main()
