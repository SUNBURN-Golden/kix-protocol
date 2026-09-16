"""S05 evidence: real working-directory removal, synthetic chain/mock money."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference/v0.3-rc1'))
from test_paid_archive import PaidArchiveTests
from paid_archive import reconcile, restore


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report',required=True);args=parser.parse_args()
    cases=[]
    for point in ('before','after'):
        t=PaidArchiveTests('runTest');t.setUp()
        try:
            t.f.crash_original(point)
            devices=dict(source=t.source.stat().st_dev,archive=t.root.stat().st_dev,provider=t.provider.stat().st_dev)
            assert devices['source']!=devices['archive']
            if point=='after':
                t.advance();t.f.context.update(showOpen=False,objectVersion='3')
            head=t.lose_and_restore(); before=t.provider_state()
            result=reconcile(t.target,t.provider)
            again=reconcile(t.target,t.provider)
            assert result['reportHash']==again['reportHash'] and t.provider_state()==before
            if point=='before':assert result['decision']=='HOLD' and result['reason']=='RESTORED_WRITER_NOT_AUTHORIZED'
            else:
                assert result['decision']=='RECONCILED_VIEW'
                assert result['view']['remainingDuties']['customerRefund']==120000
                assert result['view']['remainingDuties']['recoveryReceivables']=={'recoverable:resale-0':114000}
            cases.append(dict(injectedFailure=point,sourceRemoved=not t.source.exists(),
                separateFilesystem=True,deviceIds=devices,latestCheckpoint=head,report=result,
                repeatedRestore=restore(**t.config,target=t.target)['repeated'],
                repeatedReconciliationChangedProvider=False,moneyExecutionAllowed=False))
        finally:t.doCleanups()
    paths=['reference/v0.3-rc1/'+x for x in ('paid_archive.py','archive_driver.py','storage_receipt.py',
           'paid_recovery.py','test_paid_archive.py','client/archive-fixture.mjs','client/localnet-paid.mjs')]
    paths+=['scripts/verify_paid_archive.py']
    report=dict(format='kix-s05-evidence-v1',result='PASSED',chain='SYNTHETIC',money='MOCK',
                protectedFailure='ORIGINAL_WORKING_DIRECTORY_LOSS',wholeHostLossTested=False,
                historicalRootCauseEstablished=False,archiveRollbackProtectionEstablished=False,cases=cases,
                sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    dest=Path(args.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(result='PASSED',cases=len(cases),chain='SYNTHETIC',money='MOCK')))


if __name__=='__main__':main()
