// Requires an ACTUAL Sui localnet, a built package and the fixture artifacts from
// setup-zk.mjs. Executes the expanded kix-rs4-l1-load-v1 workload (load_plan.py
// --expand) against the published kix_rights_scale package and writes
// load-report.json: one measured sample per step (service time, outcome kind,
// gas, digest), fixed-k concurrency probe results, and a chain snapshot per
// path. summarize_load.py reduces the samples; this file asserts nothing about
// rates — closed-loop baseline only, exploration data, no SLO and no
// production claims. No real funds, no mocked RPC, no fabricated receipts:
// every chain outcome comes from executeTransaction effects (or a digest
// lookup after a lost response, RS-C03). Ceremony: single-party local fixture.
import {readFileSync,writeSync} from 'node:fs';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {bcs} from '@mysten/sui/bcs';
import {Transaction} from '@mysten/sui/transactions';
import {groth16} from 'snarkjs';
import * as T from './types.mjs';
import {connect,abortOf,eventsOf,buildPackage,deep,transient,CLOCK_ID,MODULE,ZERO_ID} from './chain-kit.mjs';
import {artifacts,checkVerifier,mintNote,spendWitness,revocationUpdate,domainOf,poseidon,
  noteTreeOf,revocationTreeOf,artifactRoot} from './private-scale.mjs';
import {jsonRpcEventSource,checkpointEventSource,rebuildTreeView} from './chain-witness.mjs';
import {proofBytes,readJSON} from './zk-helpers.mjs';
import * as P from './profile-constants.mjs';

const here=fileURLToPath(new URL('.',import.meta.url));
const out=resolve(process.env.KIX_JOURNEY_DIR??join(here,'../results/load-l1'));
await mkdir(out,{recursive:true});
const scenarioPath=process.env.KIX_LOAD_SCENARIOS??join(out,'load-scenarios.json');
const doc=JSON.parse(readFileSync(scenarioPath,'utf8'));
const DOC_VERSIONS=new Set(['kix-rs4-l1-load-v1','kix-rs4-l2-load-v1']);
if(!DOC_VERSIONS.has(doc.version))throw Error('UNRECOGNIZED_LOAD_DOCUMENT:'+doc.version);
const ACTORS=['issuer','a','b','gate','attester','delegate'];
const refBytes=tag=>Array(32).fill(tag);
const startedAt=new Date().toISOString();
const tRun=Date.now();

// ---- setup: artifacts, actors, publish, verifier -------------------------------------------
const art=await artifacts();
// Several coins per actor: probes submit in parallel (distinct gas objects) and
// the private path's holder signs every shield. Faucet coins are localnet-only.
const kit=await connect(ACTORS,{issuer:16,a:16,b:8,gate:8,attester:8,delegate:8});
const {rpc,addr,resolvedTx,getFields,chainNow}=kit;
const H=await poseidon();
const built=buildPackage(resolve(here,'../sui'));
const published=await kit.submitOne('issuer',t=>{
  const cap=t.publish({modules:built.compiled.modules,dependencies:built.compiled.dependencies});
  t.moveCall({target:'0x2::package::make_immutable',arguments:[cap]});
});
const packageId=(published.effects?.changedObjects??[]).find(x=>x.outputState?.$kind==='PackageWrite'||x.outputState?.PackageWrite)?.objectId
  ??Object.entries(published.objectTypes??{}).find(([,v])=>v==='package')?.[0];
if(!packageId)throw Error('PUBLISHED_PACKAGE_ID_NOT_FOUND_IN_EFFECTS');
const target=(name,mod=MODULE)=>packageId+'::'+mod+'::'+name;
const caps=await kit.listOwned(addr('issuer'),packageId+'::'+MODULE+'::IssuerCap');
if(caps.length!==1)throw Error('EXPECTED_ONE_ISSUER_CAP:'+caps.length);
const issuerCapId=caps[0].objectId;
const createdOfType=(executed,suffix)=>{
  const ids=Object.entries(executed.objectTypes??{}).filter(([,ty])=>typeof ty==='string'&&ty.endsWith(suffix)).map(([id])=>id);
  if(ids.length!==1)throw Error('EXPECTED_ONE_CREATED_TYPE:'+suffix+':'+ids.length);
  return ids[0];
};
// The v1 verifier carries this manifest's real fixture keys (IM-27 pin).
const verifiers={};
{
  const r=await kit.submitOne('issuer',t=>{t.moveCall({target:target('create','zk_gate'),
    arguments:[t.pure.vector('u8',art.mintVK),t.pure.vector('u8',art.spendVK),
      t.pure.vector('u8',Array.from(Buffer.from(art.hash,'hex')))]});});
  if(abortOf(r)!=='ok')throw Error('VERIFIER_INSTALL_FAILED:'+JSON.stringify(abortOf(r)));
  verifiers.v1={id:createdOfType(r,'::zk_gate::Verifier'),manifestHash:art.hash};
}
await checkVerifier(rpc,packageId,verifiers.v1.id,art.hash);

async function view(name,args=()=>[]){
  const tx=new Transaction();
  tx.setSender(addr('issuer'));
  tx.moveCall({target:target(name),arguments:args(tx)});
  const result=await transient(()=>rpc.simulateTransaction({transaction:tx,include:{commandResults:true}}));
  const values=result.commandResults?.[0]?.returnValues;
  if(!values?.length)throw Error('VIEW_CALL_FAILED:'+name);
  return values[0].bcs;
}
const viewU64=async(name,args)=>Number(bcs.u64().parse(await view(name,args)));
const constants={zk_depth:await viewU64('zk_depth'),localnet_root_history_k:await viewU64('localnet_root_history_k'),
  localnet_nullifier_shards:await viewU64('localnet_nullifier_shards'),
  localnet_challenge_shards:await viewU64('localnet_challenge_shards'),
  max_bundle_chain:await viewU64('max_bundle_chain'),profile_version:await viewU64('profile_version'),
  localnet_show_slots:await viewU64('localnet_show_slots'),localnet_page_slots:await viewU64('localnet_page_slots')};
for(const [chainName,want] of [['zk_depth',P.DEPTH],['localnet_root_history_k',P.ROOT_HISTORY_K],
    ['localnet_nullifier_shards',P.NULLIFIER_SHARDS],['localnet_challenge_shards',P.CHALLENGE_SHARDS],
    ['max_bundle_chain',8],['profile_version',P.PROFILE_VERSION],
    ['localnet_show_slots',P.SHOW_SLOTS],['localnet_page_slots',doc.settings.show.page_size]]){
  if(constants[chainName]!==want)throw Error('PACKAGE_CONSTANT_MISMATCH:'+chainName+':'+constants[chainName]+'!='+want);
}

const nameOf=Object.fromEntries(ACTORS.map(n=>[addr(n),n]));
const report={packageId,chain:kit.chain,actors:Object.fromEntries(ACTORS.map(n=>[n,addr(n)])),
  verifiers:Object.fromEntries(Object.entries(verifiers).map(([k,v])=>[k,{id:v.id,manifestHash:v.manifestHash}])),
  manifest:{hash:art.hash,format:art.manifest.format,depth:art.manifest.depth,rootHistoryK:art.manifest.rootHistoryK,
    constraints:art.manifest.constraints,ptauPower:art.manifest.phase1.ptauPower,phase1:art.manifest.phase1.source,setup:art.manifest.setup},
  constants,settings:doc.settings,requested:doc.requested,
  scenarioFingerprint:createHash('sha256').update(readFileSync(scenarioPath)).digest('hex'),
  startedAt,samples:[],snapshots:{},actual:{},timings:{}};

// ---- measured submission --------------------------------------------------------------------
// service_ms is the submit->finality window only; build_ms covers kind-build,
// coin resolution and signing. A lost response is reconciled by digest with the
// same signed bytes and never resubmitted (RS-C03). The window is bounded:
// KIX_TX_WAIT_MS caps the submit/wait path, then digest reconciliation polls
// ceil(KIX_TX_RECONCILE_MS/3000) x 3s. Defaults are the L1 record's values; a
// contended host may widen them and the runner records them in host.json.
const TX_WAIT_MS=Number(process.env.KIX_TX_WAIT_MS??60000);
const TX_RECONCILE_POLLS=Math.max(1,Math.ceil(Number(process.env.KIX_TX_RECONCILE_MS??60000)/3000));
async function reconcileByDigest(digest){
  for(let i=0;i<TX_RECONCILE_POLLS;i++){
    try{
      const r=await rpc.getTransaction({digest,include:{effects:true,events:true,objectTypes:true}});
      const executed=r.Transaction??r.FailedTransaction;
      if(executed)return executed;
    }catch{}
    await new Promise(r=>setTimeout(r,3000));
  }
  return null;
}
// A definitive rejection returned by the validator set (version conflict,
// malformed/gasless transaction, equivocation) means the bytes never ran and
// cannot land later: submission_rejected, not unknown. Only messages without
// that verdict take the digest-reconciliation path.
const REJECT_PATTERNS=['rejected as invalid','needs to be rebuilt','not available for consumption',
  'InsufficientGas','equivocat','already consumed','already exists','invalid signature',
  'is not shared','is not an object','Invariant violation'];
function isDefinitiveRejection(message){
  const m=String(message??'');
  return REJECT_PATTERNS.some(p=>m.includes(p));
}
function gasOf(executed){
  const g=executed?.effects?.gasUsed;
  return g?{computation:String(g.computationCost),storage:String(g.storageCost),rebate:String(g.storageRebate)}:null;
}
function outcomeOf(executed,extra={}){
  const o=abortOf(executed);
  const base={executed,gas:gasOf(executed),...extra};
  if(o==='ok')return {outcome_kind:'ok',...base};
  if(o?.abort==='SUBMISSION_REJECTED')return {outcome_kind:'submission_rejected',error:o.detail,...base};
  return {outcome_kind:'abort',abort:o.abort,module:o.module??null,error:o.detail??null,...base};
}
async function submitMeasured(name,build,gasIndex=0){
  const b0=performance.now();
  const {keypair,bytes}=await resolvedTx(name,build,gasIndex);
  const signed=await keypair.signTransaction(bytes);
  const build_ms=Math.round(performance.now()-b0);
  let digest=null;
  try{digest=await Transaction.from(bytes).getDigest();}catch{}
  const t0=performance.now();
  let result;
  try{
    result=await rpc.executeTransaction({transaction:bytes,signatures:[signed.signature],
      include:{effects:true,events:true,objectTypes:true}});
  }catch(e){
    const service_ms=Math.round(performance.now()-t0);
    const message=String(e?.message??e).slice(0,2000);
    if(isDefinitiveRejection(message))
      return {outcome_kind:'submission_rejected',error:message,
        digest,service_ms,build_ms,executed:null,gas:null};
    const recovered=digest?await reconcileByDigest(digest):null;
    if(recovered)return {digest,service_ms,build_ms,recovered:'after_submission_error',
      error:message,...outcomeOf(recovered)};
    // No final answer within the reconcile window: UNKNOWN (RS-C03), never
    // resubmitted with different bytes.
    return {outcome_kind:'unknown',error:message,
      digest,service_ms,build_ms,executed:null,gas:null};
  }
  try{
    await rpc.waitForTransaction({result,timeout:TX_WAIT_MS});
  }catch(e){
    const service_ms=Math.round(performance.now()-t0);
    const recovered=digest?await reconcileByDigest(digest):null;
    if(recovered)return {digest,service_ms,build_ms,recovered:'after_wait_error',
      error:String(e?.message??e).slice(0,2000),...outcomeOf(recovered)};
    // Digest never became visible: UNKNOWN, not "not executed".
    return {outcome_kind:'unknown',error:String(e?.message??e).slice(0,2000),
      digest,service_ms,build_ms,executed:null,gas:null};
  }
  const service_ms=Math.round(performance.now()-t0);
  const executed=result.Transaction??result.FailedTransaction;
  if(!executed)throw Error('UNRECOGNIZED_EXECUTION_RESULT');
  return {digest,service_ms,build_ms,...outcomeOf(executed)};
}

// ---- per-path show state ---------------------------------------------------------------------
function newShow(cfg){
  const seatedPages=cfg.seated===0?0:Math.ceil(cfg.seated/cfg.page_size);
  return {cfg,controlId:null,pages:{},shards:{},grants:{},labels:{},tickets:{},offers:{},
    tree:null,revocation:null,nullifierShards:[],challengeShards:[],domain:0n,
    view:{noteLeaves:[],revoked:new Map()},notes:[],proofs:{},
    pageFor(slot){
      const index=slot<cfg.seated?Math.floor(slot/cfg.page_size)
        :seatedPages+Math.floor((slot-cfg.seated)/cfg.page_size);
      const id=this.pages[index];
      if(!id)throw Error('NO_PAGE_FOR_SLOT:'+slot);
      return id;
    }};
}
async function routedIndex(controlId,paymentRef){
  const raw=await view('shard_index_for_ref',t=>[t.object(controlId),t.pure.vector('u8',paymentRef)]);
  return Number(bcs.u64().parse(raw));
}
async function shardFor(show,ref){
  const index=await routedIndex(show.controlId,ref);
  return show.shards[index]??Object.values(show.shards)[0];
}
// `ref_shard` steps need a reference routed to a chosen shard; the scan is
// deterministic per branch index so branches never collide on bytes.
async function refFor(show,step,branchIndex=0){
  if(step.ref_shard===undefined){
    const b=Buffer.alloc(32);b[0]=0x4b;b.writeBigUInt64LE(BigInt(step.ref),1);return b;
  }
  for(let k=branchIndex;k<branchIndex+65536;k+=8){
    const b=Buffer.alloc(32);b[0]=0x52;b.writeBigUInt64LE(BigInt(k),1);
    if(await routedIndex(show.controlId,[...b])===step.ref_shard)return b;
  }
  throw Error('NO_REF_ROUTES_TO_SHARD:'+step.ref_shard);
}
async function paymentFor(show,ownerName,slot){
  // listOwned can lag the effects we just waited on. A missing object is retried;
  // a present object returns on the first pass.
  for(let attempt=0;attempt<8;attempt++){
    for(const o of await kit.listOwned(addr(ownerName),packageId+'::'+MODULE+'::IssuancePayment')){
      const p=T.IssuancePayment.parse(o.content);
      if(p.show===show.controlId&&Number(p.slot)===slot)return {id:o.objectId,fields:deep(p)};
    }
    await new Promise(r=>setTimeout(r,250));
  }
  return null;
}
async function shardIndex(show,family,value){
  const name=family==='nullifier'?'nullifier_shard_index':'challenge_shard_index';
  return Number(bcs.u64().parse(await view(name,t=>[t.object(show.controlId),t.pure.u256(BigInt(value))])));
}
// Split-timed admission proof: witness_ms is spendWitness (public-data witness
// build incl. tree paths), proof_ms is groth16.fullProve plus local verify.
async function proveAdmission(tree,note,gate,expiresMs,options={}){
  const w0=performance.now();
  const w=await spendWitness(tree,note,gate,expiresMs,options);
  const witness_ms=Math.round(performance.now()-w0);
  const p0=performance.now();
  const wasmPath=join(artifactRoot,P.SPEND+'_js',P.SPEND+'.wasm'),zkeyPath=join(artifactRoot,P.SPEND+'.zkey');
  const {proof,publicSignals}=await groth16.fullProve(w.input,wasmPath,zkeyPath);
  if(JSON.stringify(publicSignals)!==JSON.stringify(w.publicSignals.map(String)))throw Error('CIRCUIT_PUBLIC_INPUT_LAYOUT');
  const vk=await readJSON(join(artifactRoot,P.SPEND+'.vkey.json'));
  if(!await groth16.verify(vk,publicSignals,proof))throw Error('LOCAL_GROTH16_VERIFICATION_FAILED');
  const proof_ms=Math.round(performance.now()-p0);
  return {packet:{noteRoot:String(w.publicSignals[0]),revocationRoot:String(w.publicSignals[1]),
    nullifier:String(w.publicSignals[2]),challenge:String(w.challenge),expiresMs:String(w.expires),
    proof:Array.from(proofBytes(proof)),publicSignals},witness_ms,proof_ms};
}

function recordMints(show,executed){
  for(const m of eventsOf(executed,'Issuance',T.Issuance)){
    show.tickets[m.slot]={id:m.ticket,generation:Number(m.generation),
      holder:nameOf[m.holder]??m.holder,version:1};
  }
}
function bumpVersion(show,slot){
  if(show.tickets[slot])show.tickets[slot].version+=1;
}

// Builds {sender, call, post} for a step. `call(t)` fills the Transaction; post
// applies chain-confirmed state effects (mints, version bumps, note tracking).
function stepCall(show,step){
  switch(step.op){
    case 'create_show':{
      const cfg={seated:step.seated,ga:step.ga,page_size:step.page_size,shards:step.shards};
      Object.assign(show.cfg,cfg);
      const verifier=step.verifier?verifiers[step.verifier].id:ZERO_ID;
      return {sender:'issuer',build:t=>{t.moveCall({target:target('create_show_control'),
        arguments:[t.object(issuerCapId),t.pure.u64(cfg.seated),t.pure.u64(cfg.ga),t.pure.u64(cfg.page_size),
          t.pure.u64(cfg.shards),t.pure.vector('address',[addr('gate')]),t.pure.vector('address',[addr('attester')]),
          t.pure.u64(150000),t.pure.u64(200),t.pure.u64(300),t.pure.id(verifier)]});},
      post:r=>{show.controlId=Object.entries(r.objectTypes??{}).find(([,ty])=>typeof ty==='string'&&ty.endsWith('::'+MODULE+'::ShowControl'))?.[0];
        if(!show.controlId)throw Error('SHOW_CONTROL_ID_NOT_FOUND_IN_EFFECTS');}};
    }
    case 'claim_pages':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('claim_pages'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.u64(step.from),t.pure.u64(step.count)]});},
      post:r=>{for(const e of eventsOf(r,'PageClaimed',T.PageClaimed))show.pages[e.index]=e.page;}};
    case 'claim_shards':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('claim_shards'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.u64(step.from),t.pure.u64(step.count)]});},
      post:r=>{for(const e of eventsOf(r,'ShardClaimed',T.ShardClaimed))show.shards[e.index]=e.shard;}};
    case 'claim_zk':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('claim_zk'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.object(verifiers[step.verifier].id)]});},
      post:async r=>{
        const [e]=eventsOf(r,'ZkClaimed',T.ZkClaimed);
        show.tree=e.note_tree;show.revocation=e.revocation;
        show.nullifierShards=e.nullifier_shards;show.challengeShards=e.challenge_shards;
        show.domain=BigInt(e.domain);
        const want=await domainOf(show.controlId,P.PROFILE_VERSION,verifiers[step.verifier].manifestHash);
        if(want!==show.domain)throw Error('DOMAIN_JS_DIFFERS_FROM_CHAIN');}};
    case 'seal':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('seal'),
        arguments:[t.object(show.controlId),t.object(issuerCapId)]});}};
    case 'cancel_show':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('cancel_show'),
        arguments:[t.object(show.controlId),t.object(issuerCapId)]});}};
    case 'issue':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('issue'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(issuerCapId),
          t.pure.u64(step.slot),t.pure.u64(step.gen),t.pure.address(addr(step.holder))]});},
      post:r=>recordMints(show,r)};
    case 'bundle':{
      const slots=step.slots;
      return {sender:'issuer',build:t=>{
        const b=t.moveCall({target:target('begin_bundle'),arguments:[t.object(show.controlId),t.pure.u64(slots.length)]});
        for(const slot of slots)t.moveCall({target:target('bundle_issue'),
          arguments:[b,t.object(show.controlId),t.object(show.pageFor(slot)),t.object(issuerCapId),
            t.pure.u64(slot),t.pure.u64(step.gen??0),t.pure.address(addr(step.holder))]});
        t.moveCall({target:target('finish_bundle'),arguments:[b]});},
      post:r=>recordMints(show,r)};
    }
    case 'attest_issuance':{
      return {sender:'attester',async:async(branchIndex=0)=>{
        const ref=await refFor(show,step,branchIndex);
        const shard=await shardFor(show,ref);
        return {build:t=>{t.moveCall({target:target('attest_issuance'),
          arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
            t.pure.u64(step.slot),t.pure.u64(step.gen),t.pure.address(addr(step.buyer)),
            t.pure.u64(step.amount),t.pure.vector('u8',[...ref])]});},detail:{payment_ref:Buffer.from(ref).toString('hex')}};
      }};
    }
    case 'issue_paid':{
      return {sender:'issuer',async:async()=>{
        const payment=await paymentFor(show,'issuer',step.slot);
        if(!payment)return {client:'DRIVER_NO_PAYMENT_OBJECT'};
        const shard=await shardFor(show,Array.from(payment.fields.payment_ref));
        return {build:t=>{t.moveCall({target:target('issue_paid'),
          arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
            t.object(issuerCapId),t.object(payment.id)]});}};
      },post:r=>recordMints(show,r)};
    }
    case 'cancel_issuance':{
      return {sender:'issuer',async:async()=>{
        const payment=await paymentFor(show,'issuer',step.slot);
        if(!payment)return {client:'DRIVER_NO_PAYMENT_OBJECT'};
        const shard=await shardFor(show,Array.from(payment.fields.payment_ref));
        return {build:t=>{t.moveCall({target:target('cancel_issuance'),
          arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
            t.object(issuerCapId),t.object(payment.id)]});}};
      }};
    }
    case 'offer':{
      const ticket=show.tickets[step.slot];
      return {sender:ticket.holder,build:t=>{t.moveCall({target:target('offer'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(ticket.id),
          t.pure.u64(ticket.version),t.pure.address(addr(step.to)),t.pure.u64(step.amount),
          t.pure.u64(step.expires_ms??0),t.object(CLOCK_ID)]});},
      pre:async()=>{step.expires_ms=(await chainNow())+step.ttl_ms;show.offers[step.slot]=step.to;}};
    }
    case 'accept_gift':{
      const ticket=show.tickets[step.slot];
      return {sender:show.offers[step.slot]??'b',build:t=>{t.moveCall({target:target('accept_gift'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(ticket.id),
          t.object(CLOCK_ID)]});},
      post:()=>{ticket.version+=1;ticket.holder=show.offers[step.slot];}};
    }
    case 'authorize':{
      const ticket=show.tickets[step.slot];
      return {sender:ticket.holder,build:t=>{t.moveCall({target:target('authorize_admission'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(ticket.id),
          t.pure.u64(ticket.version),t.pure.address(addr(step.gate)),t.pure.vector('u8',refBytes(1)),
          t.pure.u64(step.expires_ms??0),t.object(CLOCK_ID)]});},
      pre:async()=>{step.expires_ms=(await chainNow())+step.ttl_ms;}};
    }
    case 'consume':{
      const ticket=show.tickets[step.slot];
      return {sender:'gate',build:t=>{t.moveCall({target:target('consume'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(ticket.id),
          t.pure.u64(ticket.version),t.pure.vector('u8',refBytes(1)),t.object(CLOCK_ID)]});},
      post:()=>bumpVersion(show,step.slot)};
    }
    case 'refund':{
      const ticket=show.tickets[step.slot];
      if(!ticket)return {sender:'a',build:()=>{},client:'DRIVER_NO_TICKET'};
      return {sender:ticket.holder,build:t=>{t.moveCall({target:target('refund'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(ticket.id),
          t.pure.u64(ticket.version),t.object(CLOCK_ID)]});},
      post:()=>bumpVersion(show,step.slot)};
    }
    case 'revoke':{
      const ticket=show.tickets[step.slot];
      return {sender:'issuer',build:t=>{t.moveCall({target:target('revoke'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(issuerCapId),
          t.object(ticket.id)]});},
      post:()=>bumpVersion(show,step.slot)};
    }
    case 'revoke_with_root':{
      const ticket=show.tickets[step.slot];
      return {sender:'issuer',async:async()=>{
        const update=await revocationUpdate(show.view.revoked,step.slot);
        return {build:t=>{t.moveCall({target:target('revoke_with_root'),
          arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(show.revocation),
            t.object(issuerCapId),t.object(ticket.id),t.pure.u64(BigInt(update.priorRevoked)),
            t.pure.vector('u256',update.siblings.map(BigInt))]});},detail:{prior_revoked:update.priorRevoked}};
      },post:r=>{
        for(const e of eventsOf(r,'RevocationLeaf',T.RevocationLeaf)){
          const g=BigInt(e.generation);
          if(g>(show.view.revoked.get(Number(e.slot))??0n))show.view.revoked.set(Number(e.slot),g);
        }
        bumpVersion(show,step.slot);}};
    }
    case 'shield':{
      const ticket=show.tickets[step.slot];
      return {sender:ticket.holder,async:async()=>{
        const p0=performance.now();
        const m=await mintNote(show.domain,{slot:step.slot,generation:ticket.generation});
        const proof_ms=Math.round(performance.now()-p0);
        return {build:t=>{t.moveCall({target:target('shield'),
          arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(show.tree),
            t.object(ticket.id),t.pure.u64(ticket.version),t.pure.u256(BigInt(m.commitment)),
            t.pure.vector('u8',m.proof),t.object(verifiers[show.verifierLabel??'v1'].id),t.object(CLOCK_ID)]});},
        proof_ms,note:m.note};},
      post:r=>{
        const [added]=eventsOf(r,'NoteAdded',T.NoteAdded);
        show.view.noteLeaves.push(BigInt(added.commitment));
        show.pendingNoteIndex=Number(added.index);
        bumpVersion(show,step.slot);}};
    }
    case 'preprove':{
      return {sender:'gate',async:async()=>{
        const note=show.notes[step.note];
        if(!note)return {client:'DRIVER_NO_NOTE:'+step.note};
        const expires=(await chainNow())+90000;
        const {packet,witness_ms,proof_ms}=await proveAdmission(
          {domain:show.domain,noteLeaves:show.view.noteLeaves,revoked:show.view.revoked},
          note,addr('gate'),expires);
        show.proofs[step.label]=packet;
        return {witness_ms,proof_ms,noTx:true,detail:{noteRoot:packet.noteRoot,revocationRoot:packet.revocationRoot}};
      }};
    }
    case 'consume_private':{
      return {sender:'gate',async:async()=>{
        let packet,witness_ms=null,proof_ms=null,allowRevoked=!!step.allow_revoked;
        if(step.proof!==undefined){
          packet=show.proofs[step.proof];
          if(!packet)return {client:'DRIVER_NO_PROOF:'+step.proof};
        }else{
          const note=show.notes[step.note];
          if(!note)return {client:'DRIVER_NO_NOTE:'+step.note};
          const expires=(await chainNow())+90000;
          let w;
          try{
            w=await proveAdmission({domain:show.domain,noteLeaves:show.view.noteLeaves,
              revoked:show.view.revoked},note,addr('gate'),expires,{allowRevoked});
          }catch(e){
            return {client:String(e.message)};
          }
          packet=w.packet;witness_ms=w.witness_ms;proof_ms=w.proof_ms;
        }
        const ni=await shardIndex(show,'nullifier',packet.nullifier);
        const ci=await shardIndex(show,'challenge',packet.challenge);
        return {build:t=>{t.moveCall({target:target('consume_private'),
          arguments:[t.object(show.controlId),t.object(show.tree),t.object(show.revocation),
            t.object(show.nullifierShards[ni]),t.object(show.challengeShards[ci]),
            t.object(verifiers[show.verifierLabel??'v1'].id),t.pure.u256(BigInt(packet.noteRoot)),
            t.pure.u256(BigInt(packet.nullifier)),t.pure.u256(BigInt(packet.challenge)),
            t.pure.u64(BigInt(packet.expiresMs)),t.pure.vector('u8',packet.proof),t.object(CLOCK_ID)]});},
          witness_ms,proof_ms,detail:{preproved:step.proof??null}};
      },post:r=>{
        if(!eventsOf(r,'PrivateAdmission',T.PrivateAdmission).length)
          throw Error('PRIVATE_ADMISSION_EVENT_MISSING');}};
    }
    case 'reconstruct':{
      return {sender:'gate',async:async()=>{
        const source=step.source==='grpc'?scanSource:rpcSource;
        const w0=performance.now();
        const rebuilt=await rebuildTreeView({source,packageId,controlId:show.controlId,
          treeId:show.tree,revocationId:show.revocation,domain:show.domain,getFields});
        return {noTx:true,witness_ms:Math.round(performance.now()-w0),
          detail:{source:rebuilt.source,noteEvents:rebuilt.noteEvents,
            revocationEvents:rebuilt.revocationEvents,
            transport_retries:source.retries?source.retries():0}};
      }};
    }
    case 'create_grant':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('create_grant'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.address(addr(step.delegate))]});},
      post:r=>{for(const e of eventsOf(r,'GrantCreated',T.GrantCreated)){
        show.labels[step.label]=e.grant;show.grants[e.grant]=step.label;}}};
    case 'revoke_grant':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('revoke_grant'),
        arguments:[t.object(show.labels[step.grant]),t.object(issuerCapId)]});}};
    case 'delegate_page':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('delegate_page'),
        arguments:[t.object(show.controlId),t.object(show.pages[step.page]),t.object(show.labels[step.grant]),
          t.object(issuerCapId)]});}};
    case 'undelegate_page':
      return {sender:'issuer',build:t=>{t.moveCall({target:target('undelegate_page'),
        arguments:[t.object(show.controlId),t.object(show.pages[step.page]),t.object(show.labels[step.grant]),
          t.object(issuerCapId)]});}};
    case 'issue_delegated':
      return {sender:'delegate',build:t=>{t.moveCall({target:target('issue_delegated'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(show.labels[step.grant]),
          t.pure.u64(step.slot),t.pure.u64(step.gen),t.pure.address(addr(step.holder))]});},
      post:r=>recordMints(show,r)};
    case 'bundle_delegated':{
      const slots=step.slots;
      return {sender:'delegate',build:t=>{
        const b=t.moveCall({target:target('begin_bundle'),arguments:[t.object(show.controlId),t.pure.u64(slots.length)]});
        for(const slot of slots)t.moveCall({target:target('bundle_issue_delegated'),
          arguments:[b,t.object(show.controlId),t.object(show.pageFor(slot)),t.object(show.labels[step.grant]),
            t.pure.u64(slot),t.pure.u64(step.gen??0),t.pure.address(addr(step.holder))]});
        t.moveCall({target:target('finish_bundle'),arguments:[b]});},
      post:r=>recordMints(show,r)};
    }
    case 'attest_issuance_delegated':
      return {sender:'delegate',async:async(branchIndex=0)=>{
        const ref=await refFor(show,step,branchIndex);
        const shard=await shardFor(show,ref);
        return {build:t=>{t.moveCall({target:target('attest_issuance_delegated'),
          arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
            t.object(show.labels[step.grant]),t.pure.u64(step.slot),t.pure.u64(step.gen),
            t.pure.address(addr(step.buyer)),t.pure.u64(step.amount),t.pure.vector('u8',[...ref])]});},
          detail:{payment_ref:Buffer.from(ref).toString('hex')}};
      }};
    case 'issue_paid_delegated':
      return {sender:'delegate',async:async()=>{
        const payment=await paymentFor(show,'delegate',step.slot);
        if(!payment)return {client:'DRIVER_NO_PAYMENT_OBJECT'};
        const shard=await shardFor(show,Array.from(payment.fields.payment_ref));
        return {build:t=>{t.moveCall({target:target('issue_paid_delegated'),
          arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
            t.object(show.labels[step.grant]),t.object(payment.id)]});}};
      },post:r=>recordMints(show,r)};
    case 'cancel_issuance_delegated':
      return {sender:'delegate',async:async()=>{
        const payment=await paymentFor(show,'delegate',step.slot);
        if(!payment)return {client:'DRIVER_NO_PAYMENT_OBJECT'};
        const shard=await shardFor(show,Array.from(payment.fields.payment_ref));
        return {build:t=>{t.moveCall({target:target('cancel_issuance_delegated'),
          arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
            t.object(show.labels[step.grant]),t.object(payment.id)]});}};
      }};
    case 'refund_delegated':{
      const ticket=show.tickets[step.slot];
      return {sender:ticket.holder,build:t=>{t.moveCall({target:target('refund_delegated'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(show.labels[step.grant]),
          t.object(ticket.id),t.pure.u64(ticket.version),t.object(CLOCK_ID)]});},
      post:()=>bumpVersion(show,step.slot)};
    }
    default:
      return {sender:'issuer',build:()=>{},client:'DRIVER_UNKNOWN_OP'};
  }
}

// ---- step execution --------------------------------------------------------------------------
const rpcSource=jsonRpcEventSource(kit.endpoint);
const scanSource=checkpointEventSource(rpc);

function expectMet(expect,result){
  if(result.outcome_kind==='driver_error')return false;
  if(expect==='ok')return result.outcome_kind==='ok';
  if(expect==='any')return true;
  if(expect==='one_wins')return result.branches?.filter(b=>b.outcome_kind==='ok').length===1;
  if(expect==='both_ok')return result.branches?.every(b=>b.outcome_kind==='ok')??false;
  if(typeof expect==='object'&&expect!==null){
    if('abort' in expect)return result.outcome_kind==='abort'
      &&(expect.abort==='*'||result.abort===expect.abort);
    if('client' in expect)return result.outcome_kind==='client_refused'
      &&(expect.client==='*'||result.error===expect.client);
  }
  return false;
}

async function runStep(pathName,show,step){
  const sample={path:pathName,phase:step.phase,seq:step.seq,op:step.op,
    expect:step.expect,scheduled_ms:null};
  const t0=performance.now();
  try{
    if(step.op==='parallel'){
      const wall0=performance.now();
      const prepared=[];
      for(let i=0;i<step.of.length;i++){
        const sub=step.of[i];
        const call=stepCall(show,sub);
        if(call.client){prepared.push({client:call.client,sub,call});continue;}
        if(call.pre)await call.pre();
        let build=call.build,detail=null;
        if(call.async){
          const r=await call.async(i);
          if(r.client){prepared.push({client:r.client,sub,call});continue;}
          build=r.build??build;detail=r.detail??null;
        }
        const {keypair,bytes}=await resolvedTx(call.sender,build,i);
        prepared.push({keypair,bytes,sub,call,detail});
      }
      const results=await Promise.all(prepared.map(async(p)=>{
        if(p.client)return {sub:p.sub,signer:p.call?.sender??null,
          outcome_kind:'client_refused',error:p.client};
        const b0=performance.now();
        const signed=await p.keypair.signTransaction(p.bytes);
        let digest=null;
        try{digest=await Transaction.from(p.bytes).getDigest();}catch{}
        const tS=performance.now();
        try{
          const result=await rpc.executeTransaction({transaction:p.bytes,signatures:[signed.signature],
            include:{effects:true,events:true,objectTypes:true}});
          await rpc.waitForTransaction({result,timeout:TX_WAIT_MS});
          const executed=result.Transaction??result.FailedTransaction;
          const out=outcomeOf(executed);
          return {sub:p.sub,signer:p.call?.sender??null,digest,
            service_ms:Math.round(performance.now()-tS),build_ms:Math.round(tS-b0),
            detail:p.detail,...out};
        }catch(e){
          const service_ms=Math.round(performance.now()-tS);
          const message=String(e?.message??e).slice(0,1000);
          if(isDefinitiveRejection(message))
            return {sub:p.sub,signer:p.call?.sender??null,digest,service_ms,
              outcome_kind:'submission_rejected',error:message};
          const recovered=digest?await reconcileByDigest(digest):null;
          if(recovered)return {sub:p.sub,signer:p.call?.sender??null,digest,service_ms,
            recovered:true,error:message,...outcomeOf(recovered)};
          return {sub:p.sub,signer:p.call?.sender??null,digest,service_ms,
            outcome_kind:'unknown',error:message};
        }
      }));
      for(const [i,r] of results.entries()){
        const p=prepared[i];
        if(r.outcome_kind==='ok'&&p?.call?.post)await p.call.post(r.executed);
      }
      sample.outcome_kind='probe';
      sample.parallel_k=step.of.length;
      sample.congestion_reject_count=results.filter(r=>r.outcome_kind==='submission_rejected'
        &&/ongestion|ExecutionCancelled/i.test(String(r.error??''))).length;
      sample.service_ms=Math.round(performance.now()-wall0);
      sample.branches=results.map(r=>({op:r.sub.op,slot:r.sub.slot??null,slots:r.sub.slots??null,
        signer:r.signer,outcome_kind:r.outcome_kind,abort:r.abort??null,error:r.error??null,
        service_ms:r.service_ms??null,build_ms:r.build_ms??null,digest:r.digest??null,
        gas:r.gas??null,detail:r.detail??null,recovered:r.recovered??null}));
      sample.step_ms=Math.round(performance.now()-t0);
      sample.signer=null;
    }else{
      const call=stepCall(show,step);
      sample.signer=call.sender??null;
      if(call.client){
        sample.outcome_kind='client_refused';sample.error=call.client;
      }else{
        if(call.pre)await call.pre();
        let build=call.build,extra={};
        if(call.async){
          const r=await call.async(0);
          if(r.client){sample.outcome_kind='client_refused';sample.error=r.client;}
          else if(r.noTx){
            sample.outcome_kind='ok';
            if(r.witness_ms!=null)sample.witness_ms=r.witness_ms;
            if(r.proof_ms!=null)sample.proof_ms=r.proof_ms;
            if(r.detail)sample.detail=r.detail;
            sample.service_ms=r.service_ms??Math.round(performance.now()-t0);
          }else{build=r.build??build;extra=r;}
        }
        if(sample.outcome_kind===undefined){
          const r=await submitMeasured(call.sender,build);
          Object.assign(sample,{outcome_kind:r.outcome_kind,abort:r.abort,module:r.module,
            error:r.error,digest:r.digest,service_ms:r.service_ms,build_ms:r.build_ms,
            gas:r.gas,recovered:r.recovered??null});
          if(extra.proof_ms!=null)sample.proof_ms=extra.proof_ms;
          if(extra.witness_ms!=null)sample.witness_ms=extra.witness_ms;
          if(extra.detail)sample.detail=extra.detail;
          if(r.outcome_kind==='ok'&&call.post)await call.post(r.executed);
          if(step.op==='shield'&&r.outcome_kind==='ok'&&extra.note)
            show.notes.push({...extra.note,index:show.pendingNoteIndex});
        }
      }
      sample.step_ms=Math.round(performance.now()-t0);
    }
  }catch(e){
    sample.outcome_kind='driver_error';sample.error=String(e?.stack??e).slice(0,2000);
    sample.step_ms=Math.round(performance.now()-t0);
  }
  sample.expect_mismatch=!expectMet(sample.expect,sample);
  return sample;
}

// ---- snapshots --------------------------------------------------------------------------------
async function snapshot(show){
  const control=await getFields(show.controlId,T.ShowControl);
  const pages=[];
  for(const index of Object.keys(show.pages).map(Number).sort((x,y)=>x-y)){
    const f=await getFields(show.pages[index],T.InventoryPage);
    pages.push({index:Number(f.index),start:Number(f.start),end:Number(f.end),mode:Number(f.mode),
      issuances:Number(f.issuances),free:Number(f.free),reserved:Number(f.reserved),
      issued:Number(f.issued),retired:Number(f.retired),
      occupied:f.occupied.filter(Boolean).length,
      generations:f.generations,delegated_to:f.delegated_to??null});
  }
  const grants=[];
  for(const [id,label] of Object.entries(show.grants)){
    const f=await getFields(id,T.GrantControl);
    grants.push({label:id&&show.grants[id],id,delegate:nameOf[f.delegate]??f.delegate,
      generation:Number(f.generation),open:f.open});
  }
  const snap={control:{open:control.open,sealed:control.sealed,
    cancel_generation:Number(control.cancel_generation),claimed_pages:Number(control.claimed_pages),
    claimed_shards:Number(control.claimed_shards),claim_sequence:Number(control.claim_sequence),
    shard_count:Number(control.shard_count),domain:String(control.domain)},pages,grants};
  // Ticket spot-checks: a bounded deterministic sample, not the full list.
  const samples={};
  const wanted=[...new Set(Object.keys(show.tickets).map(Number)
    .filter((_,i,a)=>i%Math.max(1,Math.floor(a.length/8))===0))];
  for(const slot of wanted.slice(0,8)){
    const t=show.tickets[slot];if(!t)continue;
    const f=await getFields(t.id,T.Ticket);
    samples[slot]={id:t.id,slot:Number(f.slot),generation:Number(f.generation),
      holder:nameOf[f.holder]??f.holder,version:Number(f.version),state:Number(f.state)};
  }
  snap.ticketSamples=samples;
  if(show.tree){
    const tree=await getFields(show.tree,T.NoteTree),rev=await getFields(show.revocation,T.RevocationState);
    let nullifiers=0,challenges=0;const spread={nullifier:[],challenge:[]};
    for(const id of show.nullifierShards){const s=await getFields(id,T.NullifierShard);
      nullifiers+=Number(s.spent.size);spread.nullifier.push(Number(s.spent.size));}
    for(const id of show.challengeShards){const s=await getFields(id,T.ChallengeShard);
      challenges+=Number(s.used.size);spread.challenge.push(Number(s.used.size));}
    const leafRoot=String(noteTreeOf(H,show.view.noteLeaves).root);
    const revRoot=String(revocationTreeOf(H,show.view.revoked).root);
    snap.private={zk_enabled:true,leaf_count:Number(tree.leaf_count),
      history_len:tree.roots.length,revocations:Number(rev.revocations),
      nullifiers,challenges,shardSpread:spread,noteRoot:String(tree.root),
      revocationRoot:String(rev.root),
      cacheNoteRootMatch:leafRoot===String(tree.root),cacheRevocationRootMatch:revRoot===String(rev.root)};
  }else{
    snap.private={zk_enabled:false};
  }
  return snap;
}

// Late reconcile. A sample left 'unknown' means only that its digest was not
// visible inside the per-step window — not that the signed bytes never ran.
// Once every path's steps are done, before any end-state snapshot freezes the
// record, each still-unknown digest gets one more bounded lookup while the
// localnet is up. A digest found now is recorded with its true landed outcome
// and recovered='late_reconcile' (the original window error is kept); a digest
// still absent stays 'unknown' — the stronger claim, and the expected-page
// check then compares a chain the transaction provably never touched. Nothing
// is resubmitted (RS-C03) and expect_mismatch is recomputed from the final
// outcomes.
let reconciledLate=0;
async function reconcileUnknowns(){
  for(const sample of report.samples){
    let touched=false;
    if(sample.outcome_kind==='unknown'&&sample.digest){
      const r=await reconcileByDigest(sample.digest);
      if(r){sample.recovered='late_reconcile';Object.assign(sample,outcomeOf(r));
        reconciledLate++;touched=true;}
    }
    for(const b of sample.branches??[]){
      if(b.outcome_kind!=='unknown'||!b.digest)continue;
      const r=await reconcileByDigest(b.digest);
      if(r){b.recovered='late_reconcile';Object.assign(b,outcomeOf(r));
        reconciledLate++;touched=true;}
    }
    if(touched)sample.expect_mismatch=!expectMet(sample.expect,sample);
  }
}

// ---- main loop ---------------------------------------------------------------------------------
let printed=0;
const shows={};
for(const pathName of Object.keys(doc.paths)){
  const steps=doc.paths[pathName];
  const cfg={seated:doc.settings.show.seated,ga:doc.settings.show.ga,
    page_size:doc.settings.show.page_size,shards:doc.settings.shards[pathName]};
  const show=newShow(cfg);
  shows[pathName]=show;
  const tPath=Date.now();
  for(const step of steps){
    const sample=await runStep(pathName,show,step);
    report.samples.push(sample);
    if(sample.outcome_kind==='driver_error')
      console.error('DRIVER_ERROR '+pathName+' seq='+step.seq+' '+JSON.stringify(sample.error).slice(0,400));
    if(sample.expect_mismatch)
      console.error('EXPECT_MISMATCH '+pathName+' seq='+step.seq+' op='+step.op
        +' want '+JSON.stringify(step.expect)+' got '+sample.outcome_kind
        +(sample.abort!=null?' abort='+JSON.stringify(sample.abort):'')
        +(sample.error?' '+String(sample.error).slice(0,200):''));
    if(report.samples.length%256===0){
      await writeFile(join(out,'load-report.json'),JSON.stringify(report)+'\n');
    }
    if(report.samples.length-printed>=64){
      printed=report.samples.length;
      writeSync(1,'progress '+pathName+' seq='+step.seq+' op='+step.op+' samples='+report.samples.length
        +' elapsed_s='+Math.round((Date.now()-tRun)/1000)+'\n');
    }
  }
  report.timings[pathName+'_ms']=Date.now()-tPath;
}
// Settle every pending digest first so the snapshots and the expected
// end-state compare the same finalized chain. Each path runs its own show,
// so deferring all three snapshots changes only how much has landed, never
// what is measured.
await reconcileUnknowns();
report.endOfRunReconcile={rescued:reconciledLate,
  stillUnknown:report.samples.filter(s=>s.outcome_kind==='unknown'
    ||s.branches?.some(b=>b.outcome_kind==='unknown')).length};
for(const pathName of Object.keys(doc.paths)){
  const show=shows[pathName];
  report.snapshots[pathName]=await snapshot(show);
  report.actual[pathName]={steps:doc.paths[pathName].length,
    samples:report.samples.filter(s=>s.path===pathName).length,
    ok:report.samples.filter(s=>s.path===pathName&&s.outcome_kind==='ok').length,
    shielded:show.notes.length,notes:show.notes.length};
}
report.timings.total_ms=Date.now()-tRun;
report.endedAt=new Date().toISOString();
await writeFile(join(out,'load-report.json'),JSON.stringify(report,null,1)+'\n');
const mismatches=report.samples.filter(s=>s.expect_mismatch).length;
const unknowns=report.samples.filter(s=>s.outcome_kind==='unknown'
  ||s.branches?.some(b=>b.outcome_kind==='unknown')).length;
writeSync(1,'load-report written: '+join(out,'load-report.json')
  +' samples='+report.samples.length+' mismatches='+mismatches+' unknowns='+unknowns+'\n');
await new Promise(resolve=>process.stdout.write('',resolve));
process.exit(mismatches?2:0);
