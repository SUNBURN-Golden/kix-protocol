// Real Sui transactions + a separate durable MOCK money ledger.
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {Transaction} from '@mysten/sui/transactions';
import {durableJSON} from './backup.mjs';
import {hash,policyFor,inspectOffer,observeSale} from './paid-chain.mjs';
import {createArchiveFixture} from './archive-fixture.mjs';

const here=fileURLToPath(new URL('.',import.meta.url));
export async function paidJourney({issuer,a,b,chain,packageId,endpoint,out,changedId}){
  const ordinaryDirectory=join(out,'paid');let directory=ordinaryDirectory;let processCount=0;
  const python=process.env.KIX_PYTHON??resolve(here,'../../../.venv/bin/python');
  function command(action,params={},expectedError=null){
    const result=spawnSync(python,[resolve(here,'../paid_driver.py')],{encoding:'utf8',timeout:60000,
      input:JSON.stringify({directory,endpoint,action,params})});processCount++;
    if(!result.stdout)throw Error('PAID_DRIVER_FAILED:'+result.stderr+String(result.error??''));
    const r=JSON.parse(result.stdout);
    if(expectedError){assert.equal(r.ok,false);assert.match(r.error,new RegExp(expectedError));return r.error;}
    if(!r.ok || result.status!==0)throw Error('PAID_DRIVER_REJECTED:'+action+':'+JSON.stringify(r)+result.stderr);return r.result;
  }
  const summary=tid=>command('summary',{tid});
  const advance=(key,rest)=>command('fixture_advance_provider',{key,...rest});
  const advanceCapture=tid=>{advance(summary(tid).provider.find(p=>p.operationId===summary(tid).trade.paymentId).key,{settlement:true});return command('sync_capture',{tid});};
  const advanceEffect=(tid,eid,rest)=>advance(summary(tid).effects[eid].idempotencyKey,rest);
  const sameLedger=(before,after)=>{assert.deepEqual(after.balances,before.balances);assert.equal(after.journalEntries,before.journalEntries);};
  const results=[];
  for(const scenario of ['success-response-loss','cancel-before-transfer','cancel-during-payout','recovery-before-call','recovery-after-call','archive-before-call','archive-after-call']){
    const archiveScenario=scenario.startsWith('archive-');
    const archiveFixture=archiveScenario?createArchiveFixture(out,scenario,python,endpoint):null;
    directory=archiveFixture?.directory??ordinaryDirectory;
    const recoveryScenario=scenario.startsWith('recovery-');
    const cancelledPayout=['cancel-during-payout','recovery-after-call'].includes(scenario);
    const tid='paid-'+scenario;
    const made=await issuer.call('create_show',t=>[t.pure.u64(1),t.pure.vector('address',[issuer.keypair.toSuiAddress()]),
      t.pure.vector('address',[issuer.keypair.toSuiAddress()]),t.pure.u64(150000),t.pure.u64(200),t.pure.u64(300),t.pure.address('0x0')]);
    const showId=changedId(made,'::rights::Show'),capId=changedId(made,'::rights::IssuerCap');
    const issued=await issuer.call('issue',t=>[t.object(showId),t.object(capId),t.pure.u64(0),t.pure.address(a.keypair.toSuiAddress())]);
    const ticketId=changedId(issued,'::rights::Ticket');
    await a.offer(showId,ticketId,1,b.keypair.toSuiAddress(),120000,(await a.now())+600000n);
    const current=await a.right(showId,ticketId);
    const binding={format:'kix-paid-localnet-v1',tradeId:tid,chain,packageId,showId,ticketId,slot:0,generation:1,expectedVersion:1,
      seller:a.keypair.toSuiAddress(),buyer:b.keypair.toSuiAddress(),amount:120000,currency:'KRW',expiresMs:current.ticket.offer.expires_ms,
      termsHash:Buffer.from(current.ticket.offer.terms).toString('hex'),organizer:issuer.keypair.toSuiAddress(),organizerBps:200,platformBps:300,resaleCap:150000};
    binding.policyHash=hash(policyFor(binding));
    await inspectOffer(endpoint,binding);
    command('prepare',{b:binding});
    command('prepare',{b:{...binding,amount:120001}},'TRADE_ID_CONFLICT');
    assert.equal(command('capture',{tid,lose_response:true}).state,'CAPTURE_OUTCOME_UNKNOWN');
    assert.equal(summary(tid).trade.captured,false);
    const payment=command('sync_capture',{tid});assert.equal(payment.cashAvailable,false);
    const beforeDuplicate=summary(tid);command('capture',{tid});sameLedger(beforeDuplicate,summary(tid));
    const attested=await issuer.call('attest_payment',t=>[t.object(showId),t.object(ticketId),t.pure.vector('u8',Array.from(Buffer.from(payment.paymentRef,'hex'))),t.object('0x6')]);
    const paymentId=changedId(attested,'::rights::PaymentEvidence');
    // Recheck the frozen offer immediately before signing. Sign exactly once;
    // both journal and coordinator intent commit BEFORE the RPC call.
    await inspectOffer(endpoint,binding);
    const tx=new Transaction();tx.moveCall({target:packageId+'::rights::accept_sale',arguments:[tx.object(showId),tx.object(ticketId),tx.object(paymentId),tx.object('0x6')]});
    const bytes=await b.transactionBytes(tx),signed=await b.keypair.signTransaction(bytes),digest=await Transaction.from(bytes).getDigest();
    const saved={chain,packageId,bindingHash:hash(binding),paymentRef:payment.paymentRef,digest,bytes:Buffer.from(bytes).toString('base64'),signatures:[signed.signature]};
    await durableJSON(join(directory,tid+'-signed.json'),saved);
    command('record_submission',{tid,submission:saved});
    command('record_submission',{tid,submission:{...saved,paymentRef:'00'.repeat(32)}},'SUBMISSION_BINDING_MISMATCH');
    assert.equal(command('reconcile_chain',{tid}).state,'OUTCOME_UNKNOWN');
    command('cancel',{tid},'CHAIN_UNRESOLVED_NO_COMPENSATION');
    assert.equal(summary(tid).trade.refundDue,0);assert.equal(summary(tid).trade.allocations.length,0);
    let cancellationDigest=null;
    if(scenario==='cancel-before-transfer'){
      cancellationDigest=(await issuer.call('cancel_show',t=>[t.object(showId),t.object(capId)])).digest;
    }
    const execution=await b.rpc.executeTransaction({transaction:bytes,signatures:saved.signatures,include:{effects:true,events:true}});
    await b.rpc.waitForTransaction({result:execution,timeout:20000});
    // Fault injection: execution completed, but its result is discarded at the
    // application boundary. A fresh Python + Node process must query the digest.
    const recovered=command('reconcile_chain',{tid});
    assert.equal(recovered.digest,digest);
    if(scenario==='cancel-before-transfer'){
      assert.equal(recovered.state,'EXECUTED_FAILURE');
      assert.equal(recovered.raw.status.error.MoveAbort.location.module,'rights');
      assert.equal(recovered.raw.status.error.MoveAbort.abortCode,'1');
      assert.equal(recovered.compensationFence,'SHOW_CLOSED_UNTRANSFERRED');
      assert.equal(summary(tid).trade.allocations.length,0);
      command('cancel',{tid});assert.equal(summary(tid).trade.refundDue,120000);
      command('prepare_effect',{tid,eid:tid+'-refund',kind:'REFUND',amount:120000},'INSUFFICIENT_CONFIRMED_FUNDS');
      advanceCapture(tid);
      const eid=tid+'-refund';command('prepare_effect',{tid,eid,kind:'REFUND',amount:120000});
      command('send_effect',{eid,lose_response:true});command('send_effect',{eid});
      advanceEffect(tid,eid,{status:true,funds:true});command('sync_effect',{eid});
      const end=summary(tid);assert.equal(end.trade.refunded,120000);assert.equal(end.right.state,'VOID');
      assert.equal(end.trade.allocations.length,0);
      results.push({scenario,transferDigest:digest,cancellationDigest,chainState:recovered.state,final:end});continue;
    }
    assert.equal(recovered.state,'EXECUTED_SUCCESS');
    assert.deepEqual(summary(tid).trade.allocations.map(a=>a.amount),[114000,2400,3600]);
    assert.equal(summary(tid).right.owner,binding.buyer);
    const posted=summary(tid);command('reconcile_chain',{tid});sameLedger(posted,summary(tid));
    if(scenario==='success-response-loss'){
      // Use the real successful receipt when testing misbinding, not mock events.
      const mutations=[['chain','bad-chain'],['packageId','0x'+'01'.repeat(32)],['ticketId','0x'+'02'.repeat(32)],
        ['showId','0x'+'03'.repeat(32)],['seller',binding.buyer],['buyer',binding.seller],['amount',120001],['currency','USD'],['policyHash','00'.repeat(32)]];
      for(const [key,value] of mutations){
        const changed={...binding,[key]:value};
        await assert.rejects(()=>observeSale(endpoint,changed,{...saved,bindingHash:hash(changed)}));
      }
    }
    advanceCapture(tid);command('fixture_complete_performance',{tid});
    const allocations=summary(tid).trade.allocations;
    const eid=tid+'-seller';
    command('prepare_effect',{tid,eid,kind:'PAYOUT',amount:114000,allocation_id:allocations[0].id});
    if(archiveScenario){
      archiveFixture.moveProvider();
      const point=scenario==='archive-before-call'?'before':'after';
      const killed=spawnSync(python,[resolve(here,'../../../scripts/fault_paid_call.py'),point],{
        encoding:'utf8',timeout:60000,input:JSON.stringify({directory,endpoint,action:'send_effect',params:{eid},archive:archiveFixture.config})});
      processCount++;assert.equal(killed.status,91,killed.stderr+killed.stdout);
      try{
        const archiveEvidence=await archiveFixture.loseRestoreAndReconcile(point==='after',async()=>
          (await issuer.call('cancel_show',t=>[t.object(showId),t.object(capId)])).digest);
        results.push({scenario,transferDigest:digest,chainState:recovered.state,archiveEvidence});
      }finally{archiveFixture.cleanup();}
      continue;
    }
    let recoveryEvidence=null;
    if(recoveryScenario){
      const point=scenario==='recovery-before-call'?'before':'after';
      // Fault location is an argument to the injector only, never to recovery.
      const killed=spawnSync(python,[resolve(here,'../../../scripts/fault_paid_call.py'),point],{
        encoding:'utf8',timeout:60000,input:JSON.stringify({directory,endpoint,action:'send_effect',params:{eid}})});
      processCount++;assert.equal(killed.status,91,killed.stderr);
      command('send_effect',{eid},'UNFINISHED_COMMAND');
      let plan=command('recovery_inspect');
      assert.equal(plan.decision,point==='before'?'REPLAY_SAME_REQUEST':'LINK_EXISTING');
      if(point==='after'){
        cancellationDigest=(await issuer.call('cancel_show',t=>[t.object(showId),t.object(capId)])).digest;
        assert.equal(command('recovery_apply',{planId:plan.planId}).reason,'STALE_RECOVERY_PLAN');
        plan=command('recovery_inspect');assert.equal(plan.decision,'LINK_EXISTING');
      }
      const recoveredPayout=command('recovery_apply',{planId:plan.planId});
      assert.equal(recoveredPayout.decision,'RECOVERED');
      assert.equal(recoveredPayout.effect.appliedAmount,0);
      const beforeReplay=summary(tid);
      assert.equal(command('recovery_apply',{planId:plan.planId}).replay,true);
      sameLedger(beforeReplay,summary(tid));
      recoveryEvidence={authorization:plan.decision,originalRequest:plan.originalRequest,
        providerBefore:plan.providerResult,chain:plan.chain,result:recoveredPayout};
    }else{
      assert.equal(command('send_effect',{eid,lose_response:true}).state,'OUTCOME_UNKNOWN');
    }
    command('send_effect',{eid});
    // The recovery-after-call scenario already closed the show while pending.
    // That guard precedes the reservation check; both must continue to reject.
    command('prepare_effect',{tid,eid:tid+'-duplicate',kind:'PAYOUT',amount:114000,allocation_id:allocations[0].id},
      cancellationDigest?'SHOW_CLOSED_PAYOUT_BLOCKED':'OBLIGATION_ALREADY_RESERVED');
    if(cancelledPayout){
      if(!cancellationDigest)cancellationDigest=(await issuer.call('cancel_show',t=>[t.object(showId),t.object(capId)])).digest;
      command('prepare_effect',{tid,eid:tid+'-closed-payout',kind:'PAYOUT',amount:2400,allocation_id:allocations[1].id},'SHOW_CLOSED_PAYOUT_BLOCKED');
      command('cancel',{tid});
      assert.equal(summary(tid).trade.refundDue,120000);assert.equal(summary(tid).trade.reversalPlanned,false);
      command('prepare_effect',{tid,eid:tid+'-refund',kind:'REFUND',amount:120000},'INSUFFICIENT_CONFIRMED_FUNDS');
    }
    advanceEffect(tid,eid,{status:true});command('sync_effect',{eid});
    assert.equal(summary(tid).trade.allocations[0].paid,0);
    advanceEffect(tid,eid,{funds:true});command('sync_effect',{eid});
    assert.equal(summary(tid).trade.allocations[0].paid,114000);
    const paid=summary(tid);command('sync_effect',{eid});sameLedger(paid,summary(tid));
    if(!cancelledPayout){
      for(const a of allocations.slice(1)){
        const eid=a.id;command('prepare_effect',{tid,eid,kind:'PAYOUT',amount:a.amount,allocation_id:a.id});
        command('send_effect',{eid});advanceEffect(tid,eid,{status:true,funds:true});command('sync_effect',{eid});
      }
      assert.equal(summary(tid).trade.allocations.reduce((sum,a)=>sum+a.paid,0),120000);
    }else{
      assert.equal(summary(tid).balances['recoverable:'+allocations[0].id],114000);
      assert.equal(summary(tid).trade.refunded,0);
      command('prepare_effect',{tid,eid:tid+'-refund',kind:'REFUND',amount:120000},'INSUFFICIENT_CONFIRMED_FUNDS');
    }
    results.push({scenario,transferDigest:digest,cancellationDigest,chainState:recovered.state,recoveryEvidence,final:summary(tid)});
  }
  directory=ordinaryDirectory;
  const final=summary('paid-cancel-during-payout');
  assert.equal(final.provider.filter(x=>x.kind==='CAPTURE').length,5);
  assert.ok(final.provider.every(x=>x.economicExecutions===1));
  assert.ok(final.provider.filter(x=>x.kind!=='CAPTURE').every(x=>x.submitCalls===1));
  const result={status:'PASSED_ACTUAL_SUI_MOCK_MONEY',chain,packageId,coordinatorProcesses:processCount,
    rightsAuthority:'ACTUAL_SUI_LOCALNET_TRUSTED_RPC',moneyAuthority:'INDEPENDENT_SQLITE_MOCK_PROVIDER',results,
    limitations:['existing public rights; one tracked resale per show; no paid primary issuance',
      'mock PG/bank and injected performance completion; no real money or public authentication',
      'RPC is trusted; no checkpoint verification',
      'explicit recovery supports witnessed interrupted first payouts only; missing witness or unsafe replay remains held',
      'separate-filesystem archive tests working-directory loss; restored views cannot submit money; whole-host loss is untested',
      'late payout cancellation leaves 114000 KRW recovery and 120000 KRW refund duty unresolved',
      'no private resale, clean-host ZK recovery, key migration, partial bank movements or returns in this integration']};
  await durableJSON(join(out,'paid-integration-result.json'),result);return result;
}
