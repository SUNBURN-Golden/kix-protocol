"""Bounded guard deletions in disposable copies. Not a mutation coverage score."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
T='test_v02.ReviewRegressions.'
MUTATIONS=[
 ('M01','core.py','presentation holder/version guard',
  '        require(b["holder"]==t["owner"] and b["expectedVersion"]==t["rightsVersion"] and b["admissionEpoch"]==t["admissionEpoch"],"STALE_OR_WRONG_PRESENTATION")',
  '        pass # omit presentation guard','test_core.LifecycleTests.test_original_qr_invalid_after_resale'),
 ('M02','core.py','admission exclusion during reservation',
  'and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_ADMISSIBLE")',
  'and t["state"]=="ACTIVE","RIGHT_NOT_ADMISSIBLE")','test_core.LifecycleTests.test_resale_lock_blocks_admission_and_second_resale'),
 ('M03','finance.py','funds are not provider success',
  '            x["fundsAmount"]+=n',
  '            x["fundsAmount"]+=n; x["confirmedAmount"]=x["amount"]','test_core.LifecycleTests.test_funds_before_status_debits_cash_without_claiming_refund_done'),
 ('M04','finance.py','effect beneficiary binding',
  ' and b["beneficiary"]==x["beneficiary"] and b["paymentId"]==x["paymentId"]',
  ' and b["paymentId"]==x["paymentId"]','test_core.LifecycleTests.test_source_scope_and_recipient_binding'),
 ('M05','lifecycle.py','revocation disables consent',
  'allowed=b["allowed"],version=prior["version"]+1',
  'allowed=True,version=prior["version"]+1','test_core.LifecycleTests.test_marketing_consent_and_revocation_and_finance_minimization'),
 ('M06','core.py','event lifecycle guard independent of stale gate configuration',
  'self.event(t["event"])["status"]=="OPEN" and t["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_ADMISSIBLE")',
  't["state"]=="ACTIVE" and t["lock"] is None,"RIGHT_NOT_ADMISSIBLE")',T+'test_completed_event_guard_survives_stale_gate_configuration'),
 ('M07','lifecycle.py','request rights version at preparation',
  '        require(type(b["expectedVersion"]) is int and t["rightsVersion"]==b["expectedVersion"],"STALE_RIGHTS_VERSION")',
  '        pass # omit prepare version guard',T+'test_stale_resale_version_rejected_at_prepare'),
 ('M08','core.py','trade commit authority',
  '        self.role("operator"); tid=b["tradeId"]; r=self.trade(tid); t=self.ticket(r["ticket"]); e=self.event(r["event"])',
  '        tid=b["tradeId"]; r=self.trade(tid); t=self.ticket(r["ticket"]); e=self.event(r["event"])',T+'test_non_operator_cannot_commit_paid_trade'),
 ('M09','core.py','refund current holder authority',
  '    def _refund_ticket(self,b):\n        t=self.ticket(b["ticketId"]); self.role(t["owner"])',
  '    def _refund_ticket(self,b):\n        t=self.ticket(b["ticketId"])',T+'test_stranger_cannot_refund_current_right'),
 ('M10','core.py','delegation final log provenance',
  ' and b.get("provenance")=="synthetic_final_controller_log"',
  '',T+'test_delegation_requires_actual_final_fixture_marker'),
 ('M11','finance.py','send rechecks allocation version',
  ' and x["allocationVersion"]==r["allocationVersion"]',
  '',T+'test_send_boundary_checks_allocation_version_even_without_cancel'),
 ('M12','observations.py','rejected raw retained',
  '        except (Rejected,ValueError,TypeError,KeyError) as exc:',
  '        except (Rejected,ValueError,TypeError,KeyError) as exc:\n            self.db.execute("DELETE FROM raw_inbox WHERE id=?",(observation_id,))',
  'test_v02.InboxAndRecoveryTests.test_second_capture_is_preserved_and_deduplicated_under_review'),
 ('M13','lifecycle.py','causal consent version guard',
  '        require(type(b["expectedConsentVersion"]) is int and b["expectedConsentVersion"]==prior["version"],"STALE_CONSENT_VERSION")',
  '        pass # omit consent CAS',T+'test_old_consent_new_id_is_rejected_and_new_intent_is_accepted'),
 ('M14','finance.py','shared refund route obligation reservation',
  '        require(n<=-self.balance(owed)-reserved,"OBLIGATION_ALREADY_RESERVED")',
  '        pass # omit common obligation reservation',T+'test_pg_and_cash_routes_share_same_refund_limit'),
]


def run(output=None):
    output=output or ROOT/'results'; output.mkdir(parents=True,exist_ok=True)
    logs=output/'mutation_logs'; logs.mkdir(exist_ok=True)
    results=[]
    for mid,filename,description,before,after,test in MUTATIONS:
        source=(ROOT/filename).read_text()
        if source.count(before)!=1: raise RuntimeError(f'{mid}: expected one mutation anchor, got {source.count(before)}')
        baseline=subprocess.run([sys.executable,'-m','unittest',test,'-q'],cwd=ROOT,capture_output=True,text=True)
        if baseline.returncode: raise RuntimeError(f'{mid}: baseline test failed: {baseline.stderr}')
        with tempfile.TemporaryDirectory(prefix='kix-mutant-') as temp:
            clone=Path(temp)/'model'
            shutil.copytree(ROOT,clone,ignore=shutil.ignore_patterns('__pycache__','results','*.db','*.db-wal','*.db-shm'))
            (clone/filename).write_text(source.replace(before,after,1))
            proc=subprocess.run([sys.executable,'-m','unittest',test,'-q'],cwd=clone,capture_output=True,text=True)
            log=proc.stdout+proc.stderr; (logs/(mid+'.txt')).write_text(log)
            # Import errors and syntax errors do not establish behavioral detection.
            killed=proc.returncode!=0 and 'FAIL:' in log and 'ERROR:' not in log
            results.append(dict(id=mid,file=filename,guard=description,test=test,baselinePassed=True,
                detected=killed,returncode=proc.returncode,fixtureNote='stale independent gate configuration injected' if mid=='M06' else 'allocation revision injected at boundary' if mid=='M11' else None))
    report=dict(scope='14 selected deletions, not exhaustive mutation coverage',results=results,
                allDetected=all(r['detected'] for r in results))
    (output/'mutation_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    report=run(); print(json.dumps(dict(detected=sum(r['detected'] for r in report['results']),total=len(report['results']),allDetected=report['allDetected'])))
    sys.exit(0 if report['allDetected'] else 1)
