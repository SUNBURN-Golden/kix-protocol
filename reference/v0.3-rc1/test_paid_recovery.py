"""Blind recovery tests: crash labels exist ONLY in the fault injector.

Recovery receives pending/request evidence and independently queried provider /
chain facts. No fault-position parameter, environment variable, or marker is
passed to Recovery. All money and chain context in these unit tests are fixtures.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common import canonical, digest
from mock_provider import MockProvider
from paid_integration import PaidCoordinator
from paid_recovery import Recovery, CONTRACT
from storage_receipt import StorageReceipt, directory_fingerprint, write_atomic
from test_storage_receipt import seed

HERE = Path(__file__).resolve().parent


class PaidRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)/'state'
        self.final = dict(state='EXECUTED_SUCCESS', digest='fixture-signed-digest', rawHash='fixture-raw-hash',
                          allocation=dict(seller_due=114000, organizer_due=2400, platform_due=3600))
        self.command = dict(action='send_effect', params=dict(eid='payout'),
                            directory=str(self.directory), endpoint='http://127.0.0.1:9000')
        with StorageReceipt(self.directory, {'action':'seed'}) as receipt:
            receipt.begin()
            c = PaidCoordinator(self.directory)
            self.binding = seed(c)
            c.core.db.execute('UPDATE integration_final SET body=? WHERE trade_id=?', (canonical(self.final),'resale'))
            c._save('submission-resale', dict(digest=self.final['digest'], bindingHash=digest(self.binding)))
            receipt.finish(c)
        self.context = dict(bindingHash=digest(self.binding), sale=self.final,
                            showOpen=True, objectVersion='2', source='SYNTHETIC_CHAIN_TEST')
        self.reader = patch('paid_recovery.chain_context', side_effect=lambda *_: self.context.copy())
        self.reader.start()
        self.addCleanup(self.reader.stop)
        self.r = Recovery(self.directory)

    def crash_original(self, point):
        # The point argument is consumed by this injector. It is never persisted
        # in the command, witness, provider request, or recovery plan.
        code = '''
import json,os,sys
from unittest.mock import patch
from paid_integration import PaidCoordinator
from storage_receipt import StorageReceipt
q=json.loads(sys.stdin.read()); point=sys.argv[1]
with StorageReceipt(q['directory'],q) as receipt:
 receipt.begin(); c=PaidCoordinator(q['directory']); c.before_effect_submit=receipt.before_effect_submit
 original=c.provider.submit
 def kill(*args,**kwargs):
  if point=='after': original(*args,**kwargs)
  os._exit(91)
 with patch.object(c,'_query',return_value={'state':'SYNTHETIC_OPEN'}),patch.object(c.provider,'submit',side_effect=kill):
  c.send_effect('payout')
'''
        r = subprocess.run([sys.executable,'-c',code,point], input=canonical(self.command),
                           text=True,capture_output=True,cwd=HERE,timeout=15)
        self.assertEqual(r.returncode,91,r.stderr)

    def provider(self):
        return MockProvider(str(self.directory/'mock-provider.sqlite'))

    def advance(self, **flags):
        p = self.provider()
        try:
            rows = [x for x in p.summary() if x['kind']=='PAYOUT']
            p.advance(rows[0]['key'],**flags)
        finally:
            p.db.close()

    def state(self):
        c=PaidCoordinator(self.directory)
        try: return c.core.snapshot()
        finally: c.close()

    def apply_current(self):
        plan=self.r.inspect()
        return self.r.apply(plan['planId'])

    def test_before_call_replays_same_request_then_repeat_does_nothing(self):
        self.crash_original('before')
        before=directory_fingerprint(self.directory)
        plan=self.r.inspect()
        self.assertEqual(directory_fingerprint(self.directory),before)
        self.assertEqual(plan['decision'],'REPLAY_SAME_REQUEST',plan)
        result=self.r.apply(plan['planId'])
        self.assertEqual(result['decision'],'RECOVERED',result)
        self.assertEqual(result['effect']['appliedAmount'],0)
        self.assertIsNotNone(result['effect']['providerOperationId'])
        saved=directory_fingerprint(self.directory)
        replay=self.r.apply(plan['planId'])
        self.assertTrue(replay['replay'])
        self.assertEqual(directory_fingerprint(self.directory),saved)
        p=self.provider()
        try:
            found=[x for x in p.summary() if x['kind']=='PAYOUT']
            self.assertEqual((len(found),found[0]['economicExecutions'],found[0]['submitCalls']),(1,1,1))
        finally: p.db.close()

    def test_after_call_links_existing_full_result_exactly_once(self):
        self.crash_original('after'); self.advance(status=True,funds=True)
        plan=self.r.inspect()
        self.assertEqual(plan['decision'],'LINK_EXISTING',plan)
        result=self.r.apply(plan['planId'])
        self.assertEqual(result['effect']['appliedAmount'],114000)
        saved=directory_fingerprint(self.directory)
        self.r.apply(plan['planId'])
        self.assertEqual(directory_fingerprint(self.directory),saved)
        self.assertEqual(result['providerResult']['economicExecutions'],1)

    def test_status_without_debit_is_not_completed(self):
        self.crash_original('after'); self.advance(status=True)
        result=self.apply_current()
        self.assertEqual(result['effect']['confirmedAmount'],114000)
        self.assertEqual(result['effect']['appliedAmount'],0)
        self.assertEqual(result['effect']['fundsAmount'],0)

    def test_absent_without_contract_keeps_pending_and_reservations(self):
        self.crash_original('before')
        before=directory_fingerprint(self.directory)
        with patch.dict(CONTRACT,replaySafe=False):
            result=self.apply_current()
        self.assertEqual(result['decision'],'HOLD')
        self.assertEqual(result['reason'],'NOT_FOUND_DOES_NOT_ESTABLISH_SAFE_REPLAY')
        self.assertEqual(directory_fingerprint(self.directory),before)
        self.assertTrue(self.r.pending.exists())

    def test_stale_plan_rejected_after_late_payment_and_fresh_plan_links(self):
        self.crash_original('after'); plan=self.r.inspect()
        self.advance(status=True,funds=True)
        before=directory_fingerprint(self.directory)
        self.assertEqual(self.r.apply(plan['planId'])['reason'],'STALE_RECOVERY_PLAN')
        self.assertEqual(directory_fingerprint(self.directory),before)
        self.assertEqual(self.apply_current()['effect']['appliedAmount'],114000)

    def test_stale_plan_rejected_after_cancel_and_absent_payout_not_resent(self):
        self.crash_original('before'); plan=self.r.inspect()
        self.context.update(showOpen=False,objectVersion='3')
        before=directory_fingerprint(self.directory)
        self.assertEqual(self.r.apply(plan['planId'])['reason'],'STALE_RECOVERY_PLAN')
        self.assertEqual(self.apply_current()['reason'],'PAYOUT_NO_LONGER_ALLOWED')
        self.assertEqual(directory_fingerprint(self.directory),before)

    def test_cancelled_show_existing_debit_creates_recovery_and_refund_duties(self):
        self.crash_original('after'); self.advance(status=True,funds=True)
        self.context.update(showOpen=False,objectVersion='3')
        result=self.apply_current()
        self.assertEqual(result['effect']['appliedAmount'],114000)
        self.assertEqual(result['balances']['recoverable:resale-0'],114000)
        self.assertEqual((result['trade']['refundDue'],result['trade']['refunded']),(120000,0))

    def test_conflicting_provider_request_is_preserved_and_blocked(self):
        self.crash_original('after')
        p=self.provider()
        row=p.db.execute("SELECT key,result FROM operations WHERE json_extract(request,'$.kind')='PAYOUT'").fetchone()
        fact=json.loads(row[1]); fact['request']['amount']=1
        p.db.execute('UPDATE operations SET result=? WHERE key=?',(canonical(fact),row[0])); p.db.close()
        before=directory_fingerprint(self.directory)
        result=self.apply_current()
        self.assertEqual(result['reason'],'PROVIDER_BINDING_CONFLICT')
        self.assertEqual(directory_fingerprint(self.directory),before)

    def test_ledger_change_and_missing_witness_are_not_adopted(self):
        self.crash_original('before')
        p=read_json(self.r.pending)
        p.pop('execution'); write_atomic(self.r.pending,p)
        self.assertEqual(self.apply_current()['reason'],'PRE_CALL_WITNESS_MISSING')

    def test_rollback_after_witness_stays_quarantined(self):
        self.crash_original('before')
        c=PaidCoordinator(self.directory)
        c._save('unexplained-change',{'value':1}); c.close()
        self.assertEqual(self.apply_current()['reason'],'PROJECTION_DIVERGED_FROM_WITNESS')

    def crash_recovery(self, plan, method, after=False):
        code='''
import json,os,sys
from unittest.mock import patch
from paid_recovery import Recovery
from paid_integration import PaidCoordinator
from paid_recovery import write_atomic
q=json.loads(sys.stdin.read()); r=Recovery(q['directory'])
target=q['method']; owner=Recovery
if target=='source_status': owner=PaidCoordinator; target='_source'
original=getattr(owner,target) if target!='receipt_written' else write_atomic
def kill(self,*args,**kwargs):
 if q['method']=='source_status':
  result=original(self,*args,**kwargs)
  if kwargs.get('phase')=='STATUS': os._exit(92)
  return result
 if q['method']=='receipt_written':
  original(self,*args,**kwargs)
  if self.name=='storage-receipt.json': os._exit(92)
  return
 if q['after']: original(self,*args,**kwargs)
 os._exit(92)
injection=patch('paid_recovery.write_atomic',kill) if target=='receipt_written' else patch.object(owner,target,kill)
with patch('paid_recovery.chain_context',return_value=q['context']),injection:
 r.apply(q['planId'])
'''
        r=subprocess.run([sys.executable,'-c',code],input=canonical(dict(directory=str(self.directory),
                         method=method,after=after,context=self.context,planId=plan['planId'])),
                         text=True,capture_output=True,cwd=HERE,timeout=15)
        self.assertEqual(r.returncode,92,r.stderr)

    def test_recovery_dies_before_install_then_repeats_without_duplicate(self):
        self.crash_original('after'); self.advance(status=True,funds=True)
        plan=self.r.inspect(); self.crash_recovery(plan,'_install')
        self.assertEqual(self.state()['effects']['payout']['appliedAmount'],0)
        result=self.r.apply(plan['planId'])
        self.assertEqual(result['effect']['appliedAmount'],114000)
        saved=directory_fingerprint(self.directory)
        self.r.apply(plan['planId']); self.assertEqual(directory_fingerprint(self.directory),saved)

    def test_recovery_dies_after_install_before_receipt_then_finishes(self):
        self.crash_original('after'); self.advance(status=True,funds=True)
        plan=self.r.inspect(); self.crash_recovery(plan,'_acknowledge')
        self.assertEqual(self.state()['effects']['payout']['appliedAmount'],114000)
        self.assertTrue(self.r.pending.exists())
        result=self.r.apply(plan['planId'])
        self.assertEqual(result['effect']['appliedAmount'],114000)
        self.assertFalse(self.r.pending.exists())

    def test_recovery_dies_after_receipt_then_repeat_recognizes_record(self):
        self.crash_original('after')
        plan=self.r.inspect(); self.crash_recovery(plan,'_done')
        self.assertFalse(self.r.pending.exists())
        result=self.r.apply(plan['planId'])
        self.assertEqual(result['decision'],'RECOVERED')

    def test_cancel_between_install_plan_and_restart_requires_new_plan(self):
        self.crash_original('after'); plan=self.r.inspect(); self.crash_recovery(plan,'_install')
        self.context.update(showOpen=False,objectVersion='3')
        result=self.r.apply(plan['planId'])
        self.assertEqual(result['reason'],'STALE_RECOVERY_PLAN')
        self.assertTrue(self.r.pending.exists())
        self.assertEqual(self.apply_current()['trade']['refundDue'],120000)

    def test_both_original_crashes_survive_recovery_crash_matrix(self):
        # Each independent environment contains the same original request. Only
        # provider facts distinguish the two original failures to Recovery.
        for original in ('before','after'):
            for method in ('_prepare_install','source_status','_install','_acknowledge','receipt_written','_done'):
                with self.subTest(original=original,recovery=method):
                    t=PaidRecoveryTests('runTest'); t.setUp()
                    try:
                        t.crash_original(original)
                        if original=='after': t.advance(status=True,funds=True)
                        plan=t.r.inspect(); t.crash_recovery(plan,method)
                        result=t.r.apply(plan['planId'])
                        if result.get('reason')=='STALE_RECOVERY_PLAN':
                            result=t.r.apply(result['currentPlan']['planId'])
                        self.assertEqual(result['decision'],'RECOVERED',result)
                        final=directory_fingerprint(t.directory)
                        self.assertTrue(t.r.apply(result['recoveryId'])['replay'])
                        self.assertEqual(directory_fingerprint(t.directory),final)
                        p=t.provider()
                        try:
                            rows=[x for x in p.summary() if x['kind']=='PAYOUT']
                            self.assertEqual((len(rows),rows[0]['economicExecutions'],rows[0]['submitCalls']),(1,1,1))
                        finally: p.db.close()
                    finally: t.doCleanups()

    def test_recheck_immediately_before_provider_call(self):
        self.crash_original('before'); plan=self.r.inspect()
        real=write_atomic
        def cancel_on_intent(path,value):
            real(path,value)
            if path.name=='journal.json' and value.get('phase')=='INTENT':
                self.context.update(showOpen=False,objectVersion='3')
        with patch('paid_recovery.write_atomic',side_effect=cancel_on_intent):
            result=self.r.apply(plan['planId'])
        self.assertEqual(result['reason'],'STALE_RECOVERY_PLAN')
        self.assertTrue(self.r.pending.exists())
        p=self.provider()
        try: self.assertFalse(any(x['kind']=='PAYOUT' for x in p.summary()))
        finally: p.db.close()

    def test_replay_expiry_is_not_overridden_by_plan(self):
        self.crash_original('before'); plan=self.r.inspect()
        with patch('paid_recovery.time.time',return_value=plan['replayUntil']+1):
            result=self.r.apply(plan['planId'])
            self.assertEqual(result['reason'],'STALE_RECOVERY_PLAN')
            self.assertEqual(result['currentPlan']['reason'],'REPLAY_WINDOW_EXPIRED')

    def test_late_result_during_candidate_build_rejects_installation(self):
        self.crash_original('after'); plan=self.r.inspect()
        original=PaidCoordinator.sync_effect
        def late(c,eid):
            result=original(c,eid)
            self.advance(status=True,funds=True)
            return result
        with patch.object(PaidCoordinator,'sync_effect',late):
            result=self.r.apply(plan['planId'])
        self.assertEqual(result['reason'],'STALE_RECOVERY_PLAN')
        self.assertEqual(self.state()['effects']['payout']['appliedAmount'],0)
        self.assertEqual(self.apply_current()['effect']['appliedAmount'],114000)

    def test_chain_conflict_never_authorizes_new_submission(self):
        self.crash_original('before')
        self.context['sale']=dict(self.final,rawHash='conflicting-fact')
        before=directory_fingerprint(self.directory)
        result=self.apply_current()
        self.assertEqual(result['reason'],'CHAIN_EVIDENCE_UNKNOWN_OR_CONFLICTING')
        self.assertEqual(directory_fingerprint(self.directory),before)


def read_json(path): return json.loads(path.read_text())


if __name__=='__main__': unittest.main()
