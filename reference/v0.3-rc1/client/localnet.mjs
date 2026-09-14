// Requires an ACTUAL Sui localnet and a successfully built/published package.
// No SQLite/Core import, fabricated chain receipt, or mocked RPC is permitted.
import {spawnSync} from 'node:child_process';
import {randomBytes} from 'node:crypto';
import {resolve,join} from 'node:path';
import {mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {Ed25519Keypair} from '@mysten/sui/keypairs/ed25519';
import {Transaction} from '@mysten/sui/transactions';
import {IndependentClient,challengeBytes} from './independent.mjs';
import {durableJSON,readJSON,seal,unseal} from './backup.mjs';
import {Show,Ticket} from './types.mjs';

const here=fileURLToPath(new URL('.',import.meta.url));
const mode=process.argv[2]??'run';
const endpoint=process.env.KIX_LOCAL_RPC??'http://127.0.0.1:9000';
if(!['127.0.0.1','localhost','[::1]'].includes(new URL(endpoint).hostname))throw Error('LOCALNET_ONLY');
const out=resolve(process.env.KIX_JOURNEY_DIR??join(here,'../results/localnet'));
await mkdir(out,{recursive:true});
const cfg=(keypair,packageId,chain,name)=>({endpoint,keypair,packageId,expectedChain:chain,journal:join(out,'signed',name)});
// Test-only path: fully resolve kind and gas before signing, so deliberately
// invalid calls are actually executed and rejected by Move instead of being
// stopped by the SDK's gas-resolution simulation. This file permits localhost only.
class LocalExecutionClient extends IndependentClient {
  async transactionBytes(tx) {
    const kind=await tx.build({client:this.rpc,onlyTransactionKind:true});
    const resolved=Transaction.fromKind(kind);
    resolved.setSender(this.keypair.toSuiAddress());
    resolved.setGasBudget(100000000);
    const {referenceGasPrice}=await this.rpc.getReferenceGasPrice();
    resolved.setGasPrice(referenceGasPrice);
    const {objects}=await this.rpc.listCoins({owner:this.keypair.toSuiAddress()});
    const gas=objects.find(c=>BigInt(c.balance)>=100000000n);
    if(!gas)throw Error('LOCAL_TEST_GAS_NOT_FOUND');
    resolved.setGasPayment([{objectId:gas.objectId,version:gas.version,digest:gas.digest}]);
    return resolved.build();
  }
}
async function rejection(fn,reason,module,code) {
  try{await fn();}catch(e){
    const abort=e.receipt?.status?.error?.MoveAbort;
    if(!e.receipt?.digest || !abort || abort.location?.module!==module || String(abort.abortCode)!==String(code))throw e;
    return {reason,result:'ONCHAIN_REJECTED',digest:e.receipt.digest,module,abortCode:String(code)};
  }
  throw Error('EXPECTED_ONCHAIN_REJECTION:'+reason);
}
async function faucet(address) {
  const response=await fetch('http://127.0.0.1:9123/v2/gas',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({FixedAmountRequest:{recipient:address}})});
  if(!response.ok)throw Error('LOCAL_FAUCET_FAILED:'+response.status);
  return response.json();
}
async function gasReady(c) {
  const deadline=Date.now()+20000;
  while(Date.now()<deadline){const r=await c.rpc.getBalance({owner:c.keypair.toSuiAddress()});if(BigInt(r.balance.balance)>0n)return;await new Promise(r=>setTimeout(r,300));}
  throw Error('LOCAL_FAUCET_NOT_SETTLED');
}
function changedId(receipt,typeSuffix) {
  const pairs=Object.entries(receipt.objectTypes??{}).filter(([,type])=>typeof type==='string'&&type.endsWith(typeSuffix));
  if(pairs.length!==1)throw Error('EXPECTED_ONE_CREATED_TYPE:'+typeSuffix);
  return pairs[0][0];
}
if(mode==='setup') {
  const issuer=Ed25519Keypair.generate(),a=Ed25519Keypair.generate(),b=Ed25519Keypair.generate(),gate=Ed25519Keypair.generate();
  const bootstrap=new IndependentClient(cfg(issuer,'0x0',undefined,'issuer'));
  const chain=await bootstrap.chain();bootstrap.expectedChain=chain;
  await Promise.all([issuer,a,b,gate].map(k=>faucet(k.toSuiAddress())));
  await gasReady(bootstrap);
  const configArgs=process.env.KIX_SUI_CONFIG?['--client.config',process.env.KIX_SUI_CONFIG]:[];
  // This selects framework address resolution only; publishing uses the local RPC above.
  const build=spawnSync('sui',['move',...configArgs,'--build-env','mainnet','build','--path',resolve(here,'../sui'),'--dump-bytecode-as-base64'],{encoding:'utf8'});
  await durableJSON(join(out,'move-build.json'),{status:build.status,stdout:build.stdout,stderr:build.stderr,error:build.error?String(build.error):null});
  if(build.status!==0)throw Error('MOVE_BUILD_FAILED');
  const compiled=JSON.parse(build.stdout); const tx=new Transaction();
  const cap=tx.publish({modules:compiled.modules,dependencies:compiled.dependencies});
  tx.moveCall({target:'0x2::package::make_immutable',arguments:[cap]});
  const pub=await bootstrap.submit(tx,'publish-local-prototype');
  const change=(pub.effects?.changedObjects??[]).find(x=>x.outputState?.$kind==='PackageWrite'||x.outputState?.PackageWrite);
  const packageId=change?.objectId??Object.entries(pub.objectTypes??{}).find(([,v])=>v==='package')?.[0];
  if(!packageId)throw Error('PUBLISHED_PACKAGE_ID_NOT_FOUND_IN_EFFECTS');
  bootstrap.packageId=packageId;
  let verifierId='0x0',alternateVerifierId=null,manifestHash=null;
  if(process.env.KIX_PRIVATE==='1') {
    const {artifacts}=await import('./private.mjs'); const a=await artifacts();manifestHash=a.hash;
    const tx=new Transaction();tx.moveCall({target:packageId+'::zk_gate::create',arguments:[tx.pure.vector('u8',a.mintVK),tx.pure.vector('u8',a.spendVK),tx.pure.vector('u8',Array.from(Buffer.from(a.hash,'hex')))]});
    verifierId=changedId(await bootstrap.submit(tx,'install-verifier'),'::zk_gate::Verifier');
    const alternate=new Transaction();alternate.moveCall({target:packageId+'::zk_gate::create',arguments:[alternate.pure.vector('u8',a.spendVK),alternate.pure.vector('u8',a.mintVK),alternate.pure.vector('u8',Array.from(Buffer.alloc(32)))]});
    alternateVerifierId=changedId(await bootstrap.submit(alternate,'alternate-verifier-negative-fixture'),'::zk_gate::Verifier');
  }
  const issued=await bootstrap.call('create_show',t=>[t.pure.u64(2),t.pure.vector('address',[gate.toSuiAddress()]),t.pure.vector('address',[issuer.toSuiAddress()]),
    t.pure.u64(150000),t.pure.u64(200),t.pure.u64(300),t.pure.address(verifierId)]);
  const showId=changedId(issued,'::rights::Show'),issuerCap=changedId(issued,'::rights::IssuerCap');
  const made=await bootstrap.call('issue',t=>[t.object(showId),t.object(issuerCap),t.pure.u64(0),t.pure.address(a.toSuiAddress())]);
  const ticketId=changedId(made,'::rights::Ticket');
  const ca=new IndependentClient(cfg(a,packageId,chain,'A')),cb=new IndependentClient(cfg(b,packageId,chain,'B'));
  await ca.backup(join(out,'a-backup.json'),process.env.KIX_BACKUP_PASSPHRASE,showId,ticketId);
  await ca.offer(showId,ticketId,1,b.toSuiAddress(),0,(await ca.now())+600000n);
  const accepted=await cb.acceptGift(showId,ticketId);
  let extra={};
  if(process.env.KIX_PRIVATE==='1') {
    const {mintNote,checkVerifier}=await import('./private.mjs');
    await checkVerifier(cb,verifierId,manifestHash);
    const state=await cb.right(showId,ticketId);const m=await mintNote(state.show,state.ticket);
    await cb.call('shield',t=>[t.object(showId),t.object(ticketId),t.pure.u64(2),t.pure.u256(m.commitment),t.pure.vector('u8',m.proof),t.object(verifierId),t.object('0x6')]);
    extra={note:m.note,verifierId,manifestHash};
  }
  await cb.backup(join(out,'b-backup.json'),process.env.KIX_BACKUP_PASSPHRASE,showId,ticketId,extra);
  await durableJSON(join(out,'gate-backup.json'),seal({secretKey:gate.getSecretKey(),chain,packageId},process.env.KIX_BACKUP_PASSPHRASE));
  let privateBoundaryResults=null;
  if(process.env.KIX_PRIVATE==='1') {
    const {privateBoundaries}=await import('./localnet-boundaries.mjs');
    privateBoundaryResults=await privateBoundaries({
      issuer:new LocalExecutionClient(cfg(issuer,packageId,chain,'boundary-issuer')),
      holder:new LocalExecutionClient(cfg(b,packageId,chain,'boundary-holder')),
      gate:new LocalExecutionClient(cfg(gate,packageId,chain,'boundary-gate')),
      verifierId,changedId,rejection});
  }
  let paidIntegration=null;
  if(process.env.KIX_PAID==='1'){
    const {paidJourney}=await import('./localnet-paid.mjs');
    paidIntegration=await paidJourney({issuer:new LocalExecutionClient(cfg(issuer,packageId,chain,'paid-issuer')),
      a:new LocalExecutionClient(cfg(a,packageId,chain,'paid-seller')),b:new LocalExecutionClient(cfg(b,packageId,chain,'paid-buyer')),
      chain,packageId,endpoint,out,changedId});
  }
  await durableJSON(join(out,'journey-context.json'),{chain,packageId,showId,ticketId,gate:gate.toSuiAddress(),acceptedDigest:accepted.digest,private:process.env.KIX_PRIVATE==='1',verifierId,alternateVerifierId,manifestHash,privateBoundaryResults,paidIntegration});
  // Process exits here: issuer key, coordinator memory and its clients disappear.
} else if(mode==='recover') {
  const context=await readJSON(join(out,'journey-context.json'));
  const {client:b,current,backup}=await IndependentClient.restore(join(out,'b-backup.json'),process.env.KIX_BACKUP_PASSPHRASE,{endpoint,journal:join(out,'independent-b')});
  if(context.private ? current.ticket.state!==3 || current.ticket.version!=='3' : !current.valid || current.ticket.version!=='2')throw Error('RECOVERED_RIGHT_NOT_CURRENT');
  const g=unseal(await readJSON(join(out,'gate-backup.json')),process.env.KIX_BACKUP_PASSPHRASE);
  const gate=new LocalExecutionClient(cfg(Ed25519Keypair.fromSecretKey(g.secretKey),g.packageId,g.chain,'independent-gate'));
  const old=unseal(await readJSON(join(out,'a-backup.json')),process.env.KIX_BACKUP_PASSPHRASE);
  const a=new LocalExecutionClient(cfg(Ed25519Keypair.fromSecretKey(old.secretKey),old.packageId,old.chain,'old-A'));
  const request=challengeBytes();
  const oldOwner=await rejection(()=>a.authorize(context.showId,context.ticketId,current.ticket.version,context.gate,request,BigInt(Date.now())+60000n),'previous holder','rights',context.private?1:2);
  let used,replay,privacy=null;
  if(context.private) {
    const {admissionProof,checkVerifier}=await import('./private.mjs');
    await checkVerifier(b,backup.extra.verifierId,backup.extra.manifestHash);
    const p=await admissionProof(current.show,backup.extra.note,context.gate,(await b.now())+90000n);
    await durableJSON(join(out,'gate-presentation.json'),p);
    const consume=p=>gate.call('consume_private',t=>[t.object(context.showId),t.object(context.verifierId),t.pure.u256(p.nullifier),t.pure.u256(p.challenge),t.pure.u64(p.expiresMs),t.pure.vector('u8',p.proof),t.object('0x6')]);
    const changedContext=await rejection(()=>consume({...p,challenge:String(BigInt(p.challenge)+1n)}),'changed proof context','zk_gate',2);
    const wrongKey=await rejection(()=>gate.call('consume_private',t=>[t.object(context.showId),t.object(context.alternateVerifierId),t.pure.u256(p.nullifier),t.pure.u256(p.challenge),t.pure.u64(p.expiresMs),t.pure.vector('u8',p.proof),t.object('0x6')]),'wrong verifier object','rights',4);
    used=await consume(p);replay=await rejection(()=>consume(p),'private second consumption','rights',8);
    const after=await b.right(context.showId,context.ticketId);
    if(!after.show.nullifiers.some(n=>BigInt(n)===BigInt(p.nullifier)))throw Error('NULLIFIER_NOT_RECORDED');
    privacy={mintAndSpendProofsAccepted:true,nullifier:p.nullifier,changedContext,wrongKey,
      limitations:['16-slot demo anonymity set','shield transition and holder address remain public','no private resale/refund/unshield/key rotation','RPC is trusted']};
  } else {
    await b.authorize(context.showId,context.ticketId,2,context.gate,request,(await b.now())+60000n);
    used=await gate.consume(context.showId,context.ticketId,2,request);
    replay=await rejection(()=>gate.consume(context.showId,context.ticketId,2,request),'second admission','rights',1);
    const final=await b.right(context.showId,context.ticketId);if(final.ticket.state!==1)throw Error('NOT_CONSUMED');
  }
  await durableJSON(join(out,'journey-result.json'),{status:'PASSED_ACTUAL_LOCALNET',chain:context.chain,packageId:context.packageId,
    authority:'SUI_MOVE',coordinatorSetupProcessExited:true,kixServicesCalled:0,independentProcessRecovered:true,
    zk:context.private,ownGas:true,oldOwner,replay,consumeDigest:used.digest,privacy,privateBoundaryResults:context.privateBoundaryResults,paidIntegration:context.paidIntegration,
    limitation:'RPC is trusted; validator/checkpoint proof verification and production KIX shutdown are not implemented.'});
} else if(mode==='run') {
  const pass=randomBytes(32).toString('base64');
  const env={...process.env,KIX_BACKUP_PASSPHRASE:pass,KIX_JOURNEY_DIR:out};
  for(const phase of ['setup','recover']) {
    const r=spawnSync(process.execPath,[fileURLToPath(import.meta.url),phase],{env,stdio:'inherit'});
    if(r.status!==0)throw Error('JOURNEY_PHASE_FAILED:'+phase);
  }
  // Test-only backup passphrase is not persisted. Real holders supply and retain theirs.
  console.log(JSON.stringify(await readJSON(join(out,'journey-result.json')),null,2));
} else {throw Error('UNKNOWN_PHASE');}

// snarkjs/ffjavascript can retain worker threads after awaited proof work.
// Each test phase must really exit before the next independent process starts.
// All durable writes above are awaited; flush stdout before terminating workers.
await new Promise(resolve=>process.stdout.write('',resolve));
process.exit(0);
