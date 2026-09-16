// Destructive actions here target only directories created for this fixture.
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync,existsSync,statSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const here=fileURLToPath(new URL('.',import.meta.url));
export function createArchiveFixture(out,scenario,python,endpoint){
  const vault=mkdtempSync('/dev/shm/kix-s05-');
  const root=join(vault,'archive');mkdirSync(root);
  const directory=join(out,scenario);mkdirSync(directory,{recursive:true});
  assert.notEqual(statSync(root).dev,statSync(directory).dev);
  const provider=join(vault,'live-provider.sqlite');writeFileSync(provider,'',{mode:0o600});
  const config={root,stream:'paid-fixture'};
  const invoke=(script,q)=>{
    const p=spawnSync(python,[resolve(here,'../'+script)],{input:JSON.stringify(q),encoding:'utf8',timeout:60000});
    assert.equal(p.status,0,p.stderr+p.stdout);const r=JSON.parse(p.stdout);assert.equal(r.ok,true,JSON.stringify(r));return r.result;
  };
  const external=advance=>{
    const code=`import json,sys\nfrom mock_provider import MockProvider\np=MockProvider(sys.argv[1])\ntry:\n if sys.argv[2]=='advance':\n  row=next(x for x in p.summary() if x['kind']=='PAYOUT');p.advance(row['key'],status=True,funds=True)\n print(json.dumps(p.summary()))\nfinally:p.db.close()`;
    const p=spawnSync(python,['-c',code,provider,advance?'advance':'read'],{cwd:resolve(here,'..'),encoding:'utf8',timeout:15000});
    assert.equal(p.status,0,p.stderr);return JSON.parse(p.stdout);
  };
  return {directory,config,vault,provider,
    moveProvider(){
      // A closed consistent copy in a separate filesystem remains the live
      // authority. The original working directory contains only its link.
      const code=`import sys,os\nfrom paid_archive import sql_copy\nsql_copy(sys.argv[1],sys.argv[2])\nos.unlink(sys.argv[1])\nos.symlink(sys.argv[2],sys.argv[1])`;
      const p=spawnSync(python,['-c',code,join(directory,'mock-provider.sqlite'),provider],{cwd:resolve(here,'..'),encoding:'utf8',timeout:15000});
      assert.equal(p.status,0,p.stderr);
    },
    async loseRestoreAndReconcile(after,cancel){
      const target=join(out,scenario+'-restored');
      rmSync(directory,{recursive:true,force:true});assert.equal(existsSync(directory),false);
      const restored=invoke('archive_driver.py',{action:'restore',...config,target});
      assert.equal(restored.decision,'RESTORED_READ_ONLY');
      assert.equal(invoke('archive_driver.py',{action:'restore',...config,target}).repeated,true);
      let cancellationDigest=null;
      if(after){cancellationDigest=await cancel();external(true);}
      const providerBefore=external(false);
      const report=invoke('archive_driver.py',{action:'reconcile',target,providerDatabase:provider});
      const repeated=invoke('archive_driver.py',{action:'reconcile',target,providerDatabase:provider});
      assert.equal(repeated.reportHash,report.reportHash);assert.deepEqual(external(false),providerBefore);
      const payouts=providerBefore.filter(x=>x.kind==='PAYOUT');
      if(after){
        assert.equal(report.decision,'RECONCILED_VIEW');
        assert.equal(report.view.effect.appliedAmount,114000);
        assert.equal(report.view.remainingDuties.customerRefund,120000);
        assert.deepEqual(Object.values(report.view.remainingDuties.recoveryReceivables),[114000]);
        assert.equal(payouts.length,1);assert.equal(payouts[0].economicExecutions,1);assert.equal(payouts[0].submitCalls,1);
      }else{
        assert.equal(report.decision,'HOLD');assert.equal(report.reason,'RESTORED_WRITER_NOT_AUTHORIZED');assert.equal(payouts.length,0);
      }
      const blocked=spawnSync(python,[resolve(here,'../paid_driver.py')],{encoding:'utf8',timeout:15000,
        input:JSON.stringify({directory:target,endpoint,action:'send_effect',params:{eid:report.plan.effectId}})});
      assert.equal(blocked.status,2);assert.match(JSON.parse(blocked.stdout).error,/RECONCILIATION_ONLY/);
      assert.equal(existsSync(directory),false);
      return {cancellationDigest,restore:restored,reconciliation:report,provider:providerBefore,
        originalWorkingDirectoryRemoved:true,separateFilesystem:true,repeatedReconciliationChangedProvider:false,
        restoredMoneyExecutionBlocked:true,wholeHostLossTested:false};
    },
    cleanup(){rmSync(vault,{recursive:true,force:true});}
  };
}
