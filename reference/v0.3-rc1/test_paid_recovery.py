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

from common import canonical, digest, Rejected
from mock_provider import MockProvider
from paid_integration import PaidCoordinator
from paid_recovery import Recovery, CONTRACT
from storage_receipt import StorageReceipt, directory_fingerprint, write_atomic, sync_directory
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

    def assert_hold_saved(self, result, plan_id, stage):
        self.assertEqual(result['decision'], 'HOLD')
        self.assertEqual(result['holdStage'], stage)
        self.assertEqual(result['attemptedPlanId'], plan_id)
        path=self.r.cases/plan_id/('hold-'+result['holdId']+'.json')
        record=read_json(path)
        self.assertEqual(record['reason'], result['reason'])
        self.assertEqual(record['stage'], stage)
        self.assertEqual(record['attemptedPlanId'], plan_id)
        self.assertEqual(record['holdId'], result['holdId'])
        facts=record['currentPlan']
        self.assertEqual(digest({k:v for k,v in facts.items() if k not in ('observedAt','planId')}),
                         record['currentPlanId'])
        self.assertEqual(record['currentPlanId'], facts['planId'])
        self.assertTrue(self.r.pending.exists())
        return path

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
        held=self.r.apply(plan['planId'])
        self.assertEqual(held['reason'],'STALE_RECOVERY_PLAN')
        self.assert_hold_saved(held,plan['planId'],'BEFORE_INTENT')
        self.assertEqual(directory_fingerprint(self.directory),before)
        self.assertEqual(self.apply_current()['effect']['appliedAmount'],114000)

    def test_stale_plan_rejected_after_cancel_and_absent_payout_not_resent(self):
        self.crash_original('before'); plan=self.r.inspect()
        self.context.update(showOpen=False,objectVersion='3')
        before=directory_fingerprint(self.directory)
        held=self.r.apply(plan['planId'])
        self.assertEqual(held['reason'],'STALE_RECOVERY_PLAN')
        self.assert_hold_saved(held,plan['planId'],'BEFORE_INTENT')
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
atomic_target=target in ('receipt_written','hold_written')
original=write_atomic if atomic_target else getattr(owner,target)
def kill(self,*args,**kwargs):
 if q['method']=='source_status':
  result=original(self,*args,**kwargs)
  if kwargs.get('phase')=='STATUS': os._exit(92)
  return result
 if q['method']=='receipt_written':
  original(self,*args,**kwargs)
  if self.name=='storage-receipt.json': os._exit(92)
  return
 if q['method']=='hold_written':
  is_hold=self.name.startswith('hold-') and self.suffix=='.json'
  if is_hold and not q['after']: os._exit(92)
  original(self,*args,**kwargs)
  if is_hold: os._exit(92)
  return
 if q['after']: original(self,*args,**kwargs)
 os._exit(92)
injection=patch('paid_recovery.write_atomic',kill) if atomic_target else patch.object(owner,target,kill)
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
        self.assert_hold_saved(result,plan['planId'],'BEFORE_INSTALL')
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
        self.assert_hold_saved(result,plan['planId'],'BEFORE_SUBMISSION')
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
        self.assert_hold_saved(result,plan['planId'],'BEFORE_INSTALL_READY')
        self.assertEqual(self.state()['effects']['payout']['appliedAmount'],0)
        self.assertEqual(self.apply_current()['effect']['appliedAmount'],114000)

    def test_repeated_hold_reuses_record_and_changed_evidence_keeps_both(self):
        self.crash_original('before'); plan=self.r.inspect()
        self.context.update(showOpen=False,objectVersion='3')
        before=directory_fingerprint(self.directory)
        held=self.r.apply(plan['planId'])
        first=self.assert_hold_saved(held,plan['planId'],'BEFORE_INTENT')
        first_bytes=first.read_bytes()
        repeated=self.r.apply(plan['planId'])
        self.assertEqual(repeated['holdId'],held['holdId'])
        self.assertEqual(first.read_bytes(),first_bytes)
        self.context.update(objectVersion='4')
        later=self.r.apply(plan['planId'])
        second=self.assert_hold_saved(later,plan['planId'],'BEFORE_INTENT')
        self.assertNotEqual(first,second)
        self.assertEqual(first.read_bytes(),first_bytes)
        self.assertEqual(len(list(first.parent.glob('hold-*.json'))),2)
        self.assertEqual(directory_fingerprint(self.directory),before)

    def test_hold_write_failure_keeps_pending_ledger_and_provider_unchanged(self):
        self.crash_original('before'); plan=self.r.inspect()
        self.context.update(showOpen=False,objectVersion='3')
        before=directory_fingerprint(self.directory)
        pending=self.r.pending.read_bytes(); receipt=self.r.receipt.read_bytes()
        with patch('paid_recovery.write_atomic',side_effect=OSError('fixture disk failure')):
            with self.assertRaisesRegex(OSError,'fixture disk failure'):
                self.r.apply(plan['planId'])
        self.assertEqual(directory_fingerprint(self.directory),before)
        self.assertEqual(self.r.pending.read_bytes(),pending)
        self.assertEqual(self.r.receipt.read_bytes(),receipt)
        self.assert_hold_saved(self.r.apply(plan['planId']),plan['planId'],'BEFORE_INTENT')

    def test_changed_hold_evidence_is_rejected_without_overwriting_or_execution(self):
        self.crash_original('before'); plan=self.r.inspect()
        self.context.update(showOpen=False,objectVersion='3')
        held=self.r.apply(plan['planId'])
        path=self.assert_hold_saved(held,plan['planId'],'BEFORE_INTENT')
        record=read_json(path)
        record['currentPlan']['chain']['showOpen']=True
        write_atomic(path,record)
        damaged=path.read_bytes(); before=directory_fingerprint(self.directory)
        with self.assertRaisesRegex(Rejected,'RECOVERY_HOLD_RECORD_CONFLICT'):
            self.r.apply(plan['planId'])
        self.assertEqual(path.read_bytes(),damaged)
        self.assertEqual(directory_fingerprint(self.directory),before)
        self.assertTrue(self.r.pending.exists())

    def test_hold_record_directory_sync_failure_is_retried_before_acknowledging_hold(self):
        self.crash_original('before'); plan=self.r.inspect()
        self.context.update(showOpen=False,objectVersion='3')
        before=directory_fingerprint(self.directory)
        pending=self.r.pending.read_bytes(); receipt=self.r.receipt.read_bytes()
        case=self.r.cases/plan['planId']
        def fail_case_sync(path):
            if path == case: raise OSError('fixture hold directory sync failure')
            return sync_directory(path)
        # Atomic rename succeeds; the following directory sync fails. The
        # visible record alone must not let a later attempt skip that boundary.
        with patch('storage_receipt.sync_directory',side_effect=fail_case_sync):
            with self.assertRaisesRegex(OSError,'fixture hold directory sync failure'):
                self.r.apply(plan['planId'])
        files=list(case.glob('hold-*.json'))
        self.assertEqual(len(files),1)
        saved=files[0].read_bytes()
        with patch('paid_recovery.sync_directory',side_effect=fail_case_sync):
            with self.assertRaisesRegex(OSError,'fixture hold directory sync failure'):
                self.r.apply(plan['planId'])
        with patch('paid_recovery.sync_directory',wraps=sync_directory) as synced:
            result=self.r.apply(plan['planId'])
        synced.assert_any_call(case)
        self.assert_hold_saved(result,plan['planId'],'BEFORE_INTENT')
        self.assertEqual(files[0].read_bytes(),saved)
        self.assertEqual(len(list(case.glob('hold-*.json'))),1)
        self.assertEqual(directory_fingerprint(self.directory),before)
        self.assertEqual(self.r.pending.read_bytes(),pending)
        self.assertEqual(self.r.receipt.read_bytes(),receipt)

    def test_conflict_after_submission_records_hold_without_ledger_application(self):
        self.crash_original('before'); plan=self.r.inspect()
        original=MockProvider.submit
        def conflict(provider,*args,**kwargs):
            result=original(provider,*args,**kwargs)
            row=provider.db.execute("SELECT key,result FROM operations WHERE json_extract(request,'$.kind')='PAYOUT'").fetchone()
            fact=json.loads(row[1]); fact['request']['amount']=1
            provider.db.execute('UPDATE operations SET result=? WHERE key=?',(canonical(fact),row[0]))
            return result
        before=directory_fingerprint(self.directory)['projection.sqlite']
        with patch.object(MockProvider,'submit',conflict):
            result=self.r.apply(plan['planId'])
        self.assertEqual(result['reason'],'PROVIDER_BINDING_CONFLICT')
        path=self.assert_hold_saved(result,plan['planId'],'AFTER_SUBMISSION')
        self.assertEqual(read_json(path)['currentPlan']['providerResult']['economicExecutions'],1)
        self.assertEqual(directory_fingerprint(self.directory)['projection.sqlite'],before)
        repeated=self.r.apply(plan['planId'])
        self.assertEqual(repeated['decision'],'HOLD')
        p=self.provider()
        try:
            rows=[x for x in p.summary() if x['kind']=='PAYOUT']
            self.assertEqual((len(rows),rows[0]['economicExecutions'],rows[0]['submitCalls']),(1,1,1))
        finally: p.db.close()

    def test_death_before_and_after_hold_record_retains_reservations_and_repeats(self):
        for after in (False,True):
            with self.subTest(after_record=after):
                t=PaidRecoveryTests('runTest'); t.setUp()
                try:
                    t.crash_original('before'); plan=t.r.inspect()
                    t.context.update(showOpen=False,objectVersion='3')
                    before=directory_fingerprint(t.directory)
                    pending=t.r.pending.read_bytes(); receipt=t.r.receipt.read_bytes()
                    t.crash_recovery(plan,'hold_written',after=after)
                    prior=list((t.r.cases/plan['planId']).glob('hold-*.json'))
                    self.assertEqual(len(prior),int(after))
                    saved=prior[0].read_bytes() if prior else None
                    result=t.r.apply(plan['planId'])
                    path=t.assert_hold_saved(result,plan['planId'],'BEFORE_INTENT')
                    if saved is not None: self.assertEqual(path.read_bytes(),saved)
                    repeated=t.r.apply(plan['planId'])
                    self.assertEqual(repeated['holdId'],result['holdId'])
                    self.assertEqual(len(list(path.parent.glob('hold-*.json'))),1)
                    self.assertEqual(directory_fingerprint(t.directory),before)
                    self.assertEqual(t.r.pending.read_bytes(),pending)
                    self.assertEqual(t.r.receipt.read_bytes(),receipt)
                finally: t.doCleanups()

    def test_chain_conflict_never_authorizes_new_submission(self):
        self.crash_original('before')
        self.context['sale']=dict(self.final,rawHash='conflicting-fact')
        before=directory_fingerprint(self.directory)
        result=self.apply_current()
        self.assertEqual(result['reason'],'CHAIN_EVIDENCE_UNKNOWN_OR_CONFLICTING')
        self.assertEqual(directory_fingerprint(self.directory),before)


def read_json(path): return json.loads(path.read_text())


if __name__=='__main__': unittest.main()
