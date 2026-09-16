"""Real filesystem/process-loss tests; money and chain fixtures are labelled."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from common import canonical, Rejected
from mock_provider import MockProvider
from paid_integration import PaidCoordinator
from paid_recovery import Recovery
from paid_archive import (Archive, ArchiveStore, restore, reconcile, ro, sql_copy,
                          BINDING, POINTER, RESTORED, state_of, read_json)
from storage_receipt import StorageReceipt, StorageFault, connection_fingerprint
import test_paid_recovery as fixture

HERE = Path(__file__).resolve().parent


class PaidArchiveTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture.PaidRecoveryTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.other = tempfile.TemporaryDirectory(prefix='kix-vault-test-', dir='/dev/shm')
        self.addCleanup(self.other.cleanup)
        self.root = Path(self.other.name)/'archive'; self.root.mkdir()
        self.provider = Path(self.other.name)/'live-provider.sqlite'
        self.source = self.f.directory
        sql_copy(self.source/'mock-provider.sqlite', self.provider)
        (self.source/'mock-provider.sqlite').unlink()
        (self.source/'mock-provider.sqlite').symlink_to(self.provider)
        self.config = dict(root=str(self.root), stream='fixture-one')
        self.f.command['archive'] = self.config
        self.target = self.source.parent/'restored'

    def archive(self):
        return Archive.for_source(self.source)

    def latest(self):
        return ArchiveStore(**self.config).latest()[0]

    def provider_state(self):
        db = ro(self.provider)
        try: return connection_fingerprint(db)
        finally: db.close()

    def advance(self):
        provider = MockProvider(str(self.provider))
        try:
            row = next(x for x in provider.summary() if x['kind'] == 'PAYOUT')
            provider.advance(row['key'], status=True, funds=True)
        finally: provider.db.close()

    def lose_and_restore(self):
        head = self.latest()
        shutil.rmtree(self.source)
        self.assertFalse(self.source.exists())
        result = restore(**self.config, target=self.target, checkpoint=head['checkpoint'])
        self.assertEqual(result['decision'], 'RESTORED_READ_ONLY')
        self.assertFalse(self.source.exists())
        return head

    def test_before_call_loss_restores_original_request_and_holds_without_dispatch(self):
        self.f.crash_original('before')
        head = self.lose_and_restore()
        before = self.provider_state()
        result = reconcile(self.target, self.provider)
        self.assertEqual(result['decision'], 'HOLD', result)
        self.assertEqual(result['reason'], 'RESTORED_WRITER_NOT_AUTHORIZED')
        self.assertEqual(result['plan']['originalCommand'], self.f.command)
        self.assertEqual(result['plan']['ledger']['effect']['amount'], 114000)
        self.assertEqual(result['checkpoint'], head)
        self.assertEqual(self.provider_state(), before)
        self.assertEqual(reconcile(self.target, self.provider)['reportHash'], result['reportHash'])

    def test_after_call_loss_uses_live_debit_and_cancel_to_rebuild_obligations(self):
        self.f.crash_original('after')
        self.advance()
        self.f.context.update(showOpen=False, objectVersion='3')
        self.lose_and_restore()
        before = self.provider_state()
        result = reconcile(self.target, self.provider)
        self.assertEqual(result['decision'], 'RECONCILED_VIEW', result)
        self.assertEqual(result['view']['effect']['appliedAmount'],114000)
        self.assertEqual(result['view']['remainingDuties']['customerRefund'],120000)
        self.assertEqual(result['view']['remainingDuties']['recoveryReceivables'], {'recoverable:resale-0':114000})
        self.assertEqual(self.provider_state(),before)
        p=MockProvider(str(self.provider))
        try:
            rows=[x for x in p.summary() if x['kind']=='PAYOUT']
            self.assertEqual([(x['economicExecutions'],x['submitCalls']) for x in rows],[(1,1)])
        finally: p.db.close()

    def test_old_valid_checkpoint_is_rejected_against_live_archive_head(self):
        self.f.crash_original('before')
        store=ArchiveStore(**self.config)
        head,item=store.latest()
        self.assertIsNotNone(item['previous'])
        with self.assertRaisesRegex(Rejected,'STALE_ARCHIVE_CHECKPOINT'):
            restore(**self.config,target=self.target,checkpoint=item['previous'])
        self.assertFalse(self.target.exists())

    def test_corrupt_latest_never_falls_back_to_older_good_checkpoint(self):
        self.f.crash_original('before')
        store=ArchiveStore(**self.config); head=self.latest()
        (store.directory/(head['checkpoint']+'.json')).write_text('{}')
        with self.assertRaises((Rejected,KeyError)):
            restore(**self.config,target=self.target)
        self.assertFalse(self.target.exists())

    def test_same_filesystem_archive_is_rejected_before_any_new_command(self):
        bad=dict(root=str(self.source.parent),stream='wrong-device')
        with StorageReceipt(self.source,dict(action='summary',archive=bad)) as receipt:
            with self.assertRaisesRegex(StorageFault,'SEPARATE_FILESYSTEM'):
                receipt.begin()
        self.assertFalse((self.source/BINDING).exists())

    def test_full_local_rollback_including_receipt_and_pointer_is_detected(self):
        with StorageReceipt(self.source,dict(action='summary',archive=self.config)) as receipt:
            receipt.begin(); c=PaidCoordinator(self.source); receipt.finish(c)
        older=self.source.parent/'older'
        shutil.copytree(self.source,older,symlinks=True)
        with StorageReceipt(self.source,dict(action='another-summary')) as receipt:
            receipt.begin(); c=PaidCoordinator(self.source); receipt.finish(c)
        shutil.rmtree(self.source); shutil.copytree(older,self.source,symlinks=True)
        with StorageReceipt(self.source,dict(action='summary')) as receipt:
            with self.assertRaisesRegex(Rejected,'ARCHIVE_POINTER_DIVERGED'):
                receipt.begin()

    def test_archive_outage_before_payout_preserves_pending_and_never_calls_provider(self):
        original=Archive.publish
        def unavailable(archive,boundary,**kwargs):
            if boundary=='BEFORE_PROVIDER_CALL': raise OSError('fixture archive unavailable')
            return original(archive,boundary,**kwargs)
        with StorageReceipt(self.source,self.f.command) as receipt:
            receipt.begin(); c=PaidCoordinator(self.source); c.before_effect_submit=receipt.before_effect_submit
            try:
                with patch.object(c,'_query',return_value={'state':'SYNTHETIC_OPEN'}), \
                     patch.object(Archive,'publish',unavailable), patch.object(c.provider,'submit') as submitted:
                    with self.assertRaisesRegex(StorageFault,'ARCHIVE_CHECKPOINT_REQUIRED'):
                        c.send_effect('payout')
                    submitted.assert_not_called()
            finally: c.close()
        self.assertTrue((self.source/'storage-command-pending.json').exists())

    def test_missing_archive_for_enrolled_source_does_not_create_empty_replacement(self):
        with StorageReceipt(self.source,dict(action='summary',archive=self.config)) as receipt:
            receipt.begin(); c=PaidCoordinator(self.source); receipt.finish(c)
        shutil.rmtree(self.root/'fixture-one')
        with StorageReceipt(self.source,dict(action='summary')) as receipt:
            with self.assertRaisesRegex(StorageFault,'ARCHIVE_UNAVAILABLE'):
                receipt.begin()
        self.assertFalse((self.root/'fixture-one').exists())

    def test_restored_workspace_blocks_normal_cli_and_s03_apply(self):
        self.f.crash_original('before'); self.lose_and_restore()
        with StorageReceipt(self.target,self.f.command) as receipt:
            with self.assertRaisesRegex(StorageFault,'RECONCILIATION_ONLY'): receipt.begin()
        with self.assertRaisesRegex(StorageFault,'RECONCILIATION_ONLY'):
            Recovery(self.target).apply('a'*64)

    def test_archive_provider_snapshot_is_never_accepted_as_live_authority(self):
        self.f.crash_original('after'); self.lose_and_restore()
        with self.assertRaisesRegex(Rejected,'LIVE_PROVIDER_MUST_BE_EXTERNAL'):
            reconcile(self.target,self.target/'mock-provider.sqlite')

    def test_changed_restored_ledger_is_rejected_without_reblessing(self):
        self.f.crash_original('before'); self.lose_and_restore()
        c=PaidCoordinator(self.target)
        try: c._save('changed',{'value':1})
        finally: c.close()
        with self.assertRaisesRegex(Rejected,'RESTORED_SOURCE_CHANGED'):
            reconcile(self.target,self.provider)

    def test_wrong_live_provider_preserves_unresolved_obligations(self):
        self.f.crash_original('after'); self.lose_and_restore()
        wrong=Path(self.other.name)/'wrong-provider.sqlite'
        p=MockProvider(str(wrong)); p.db.close()
        result=reconcile(self.target,wrong)
        self.assertEqual(result['decision'],'HOLD')
        self.assertEqual(result['reason'],'UNRELATED_PROVIDER_STATE_CHANGED')

    def test_restore_process_dies_before_or_after_install_and_can_be_repeated(self):
        self.f.crash_original('after')
        shutil.rmtree(self.source)
        code='''
import json,os,sys
from unittest.mock import patch
import paid_archive
q=json.load(sys.stdin); original=paid_archive.os.rename
def kill(*args,**kwargs):
 if q['point']=='after': original(*args,**kwargs)
 os._exit(93)
with patch('paid_archive.os.rename',side_effect=kill):
 paid_archive.restore(q['root'],q['stream'],q['target'])
'''
        for point in ('before','after'):
            with self.subTest(point=point):
                target=self.target.with_name('restore-'+point)
                child=subprocess.run([sys.executable,'-c',code],input=canonical(dict(**self.config,target=str(target),point=point)),
                                     text=True,capture_output=True,cwd=HERE,timeout=20)
                self.assertEqual(child.returncode,93,child.stderr)
                restore(**self.config,target=target)
                self.assertTrue(restore(**self.config,target=target)['repeated'])
                self.assertEqual(reconcile(target,self.provider)['decision'],'RECONCILED_VIEW')

    def test_checkpoint_provider_snapshot_contains_no_post_call_result(self):
        self.f.crash_original('after'); self.advance(); self.lose_and_restore()
        original=MockProvider(str(self.target/'mock-provider.sqlite'))
        try: self.assertFalse(any(x['kind']=='PAYOUT' for x in original.summary()))
        finally: original.db.close()
        result=reconcile(self.target,self.provider)
        self.assertEqual(result['view']['effect']['appliedAmount'],114000)

    def test_source_recovery_ack_is_archived_before_reported_complete(self):
        self.f.crash_original('after'); self.advance()
        plan=self.f.r.inspect(); self.assertEqual(plan['decision'],'LINK_EXISTING')
        result=self.f.r.apply(plan['planId'])
        self.assertEqual(result['decision'],'RECOVERED')
        self.archive().check()
        with StorageReceipt(self.source,{'action':'summary'}) as receipt:
            receipt.begin(); c=PaidCoordinator(self.source); receipt.finish(c)

    def test_lost_local_archive_ack_still_restores_the_newest_durable_request(self):
        import paid_archive
        original=paid_archive.write_atomic
        def lost_ack(path,value):
            if path.name==POINTER and value['sequence']==3:
                raise OSError('lost local archive acknowledgement')
            return original(path,value)
        with StorageReceipt(self.source,self.f.command) as receipt:
            receipt.begin(); c=PaidCoordinator(self.source); c.before_effect_submit=receipt.before_effect_submit
            try:
                with patch.object(c,'_query',return_value={'state':'SYNTHETIC_OPEN'}), \
                     patch.object(paid_archive,'write_atomic',lost_ack),patch.object(c.provider,'submit') as submit:
                    with self.assertRaisesRegex(StorageFault,'ARCHIVE_CHECKPOINT_REQUIRED'):
                        c.send_effect('payout')
                    submit.assert_not_called()
            finally:c.close()
        self.lose_and_restore()
        result=reconcile(self.target,self.provider)
        self.assertEqual(result['reason'],'RESTORED_WRITER_NOT_AUTHORIZED')
        self.assertEqual(result['plan']['originalRequest']['amount'],114000)

    def test_provider_change_while_rebuilding_view_requires_new_reconciliation(self):
        self.f.crash_original('after'); self.lose_and_restore()
        original=PaidCoordinator.sync_effect
        def late(c,eid):
            result=original(c,eid);self.advance();return result
        with patch.object(PaidCoordinator,'sync_effect',late):
            with self.assertRaisesRegex(Rejected,'LIVE_PROVIDER_CHANGED_RECONCILE_AGAIN'):
                reconcile(self.target,self.provider)
        result=reconcile(self.target,self.provider)
        self.assertEqual(result['view']['effect']['appliedAmount'],114000)

    def test_chain_change_while_rebuilding_view_requires_new_reconciliation(self):
        self.f.crash_original('after'); self.lose_and_restore()
        original=PaidCoordinator.sync_effect
        def late(c,eid):
            result=original(c,eid);self.f.context.update(showOpen=False,objectVersion='3');return result
        with patch.object(PaidCoordinator,'sync_effect',late):
            with self.assertRaisesRegex(Rejected,'STALE_RECONCILIATION_PLAN'):
                reconcile(self.target,self.provider)

    def test_s03_cannot_resume_a_rolled_back_source_against_newer_archive(self):
        self.f.crash_original('before'); plan=self.f.r.inspect()
        older=self.source.parent/'older-pending'
        shutil.copytree(self.source,older,symlinks=True)
        provider_before=self.source.parent/'provider-before.sqlite'
        sql_copy(self.provider,provider_before)
        self.assertEqual(self.f.r.apply(plan['planId'])['decision'],'RECOVERED')
        head=self.latest()
        shutil.rmtree(self.source);shutil.copytree(older,self.source,symlinks=True)
        # Deliberate fault: even the mock provider is rolled back. The separate
        # archive head must prevent authorizing the old first-send request.
        self.provider.unlink();sql_copy(provider_before,self.provider)
        before=self.provider_state()
        with patch.object(MockProvider,'submit') as submitted:
            with self.assertRaisesRegex(Rejected,'ARCHIVE_POINTER_DIVERGED'):
                self.f.r.apply(plan['planId'])
            submitted.assert_not_called()
        self.assertEqual(self.f.r.inspect()['reason'],'ARCHIVE_POINTER_DIVERGED')
        self.assertEqual(self.provider_state(),before)
        self.assertEqual(self.latest(),head)


if __name__ == '__main__':
    unittest.main()
