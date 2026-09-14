"""Export evidence bundles for blind local recovery; SYNTHETIC chain + MOCK money."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reference/v0.3-rc1'))
from paid_integration import PaidCoordinator
from storage_receipt import StorageReceipt, directory_fingerprint
from test_paid_recovery import PaidRecoveryTests


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--report',required=True); args=ap.parse_args()
    cases=[]
    for point in ('before','after'):
        t=PaidRecoveryTests('runTest'); t.setUp()
        try:
            t.crash_original(point)
            if point=='after': t.advance(status=True,funds=True)
            plan=t.r.inspect(); result=t.r.apply(plan['planId'])
            assert result['decision']=='RECOVERED', result
            before=directory_fingerprint(t.directory)
            assert t.r.apply(plan['planId'])['replay']
            assert directory_fingerprint(t.directory)==before
            if point=='before':
                q=dict(action='fixture_observe_result')
                with StorageReceipt(t.directory,q) as receipt:
                    receipt.begin(); c=PaidCoordinator(t.directory)
                    key=c.core.snapshot()['effects']['payout']['idempotencyKey']
                    c.provider.advance(key,status=True,funds=True)
                    c.sync_effect('payout'); receipt.finish(c)
            s=t.state(); assert s['effects']['payout']['appliedAmount']==114000
            p=t.provider()
            try:
                provider=[x for x in p.summary() if x['kind']=='PAYOUT'][0]
                assert provider['economicExecutions']==1 and provider['submitCalls']==1
            finally: p.db.close()
            cases.append(dict(injectedFailure=point, recoveryReceivedFailureLabel=False,
                originalRequest=plan['originalRequest'], providerLookup=plan['providerLookup'],
                providerAtInspection=plan['providerResult'], chain=plan['chain'],
                decision=plan['decision'], recovery=result, finalEffect=s['effects']['payout'],
                finalTrade=s['trades']['resale'], finalBalances=s['balances'], providerFinal=provider,
                repeatedRecoveryChangedLedger=False))
        finally: t.doCleanups()
    paths=['reference/v0.3-rc1/'+n for n in ('paid_recovery.py','storage_receipt.py','paid_driver.py',
           'paid_integration.py','test_paid_recovery.py')]+['scripts/verify_paid_recovery.py']
    report=dict(format='kix-s03-evidence-v1',result='PASSED',chain='SYNTHETIC',money='MOCK',
                historicalRootCauseEstablished=False,independentDurabilityEstablished=False,cases=cases,
                sourceSha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    dest=Path(args.report); dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(result='PASSED',cases=len(cases),chain='SYNTHETIC',money='MOCK')))


if __name__=='__main__': main()
