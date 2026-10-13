// Requires an ACTUAL Sui localnet and a successfully built/published package.
// Replays the expanded operation scenarios (compare_localnet.py --expand) against
// the published kix_rights_scale package and writes chain-report.json: per-step
// observed outcomes, minted ticket objects, a BCS-decoded chain snapshot per
// scenario, and shared-object concurrency probes. compare_localnet.py replays
// the same steps on model.py and asserts agreement. No real funds, no mocked RPC,
// no fabricated receipts: every outcome comes from executeTransaction effects.
import {spawnSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {bcs} from '@mysten/sui/bcs';
import {SuiGrpcClient} from '@mysten/sui/grpc';
import {Ed25519Keypair} from '@mysten/sui/keypairs/ed25519';
import {Transaction} from '@mysten/sui/transactions';
import {ShowControl,InventoryPage,PaymentRefShard,Ticket,IssuancePayment,PaymentEvidence,
  PageClaimed,ShardClaimed,Issuance,Clock} from './types.mjs';

const here=fileURLToPath(new URL('.',import.meta.url));
const endpoint=process.env.KIX_LOCAL_RPC??'http://127.0.0.1:9000';
if(!['127.0.0.1','localhost','[::1]'].includes(new URL(endpoint).hostname))throw Error('LOCALNET_ONLY');
const out=resolve(process.env.KIX_JOURNEY_DIR??join(here,'../results/localnet'));
await mkdir(out,{recursive:true});
const scenarioPath=process.env.KIX_SCENARIOS??join(out,'scenarios.json');
const scenarios=JSON.parse(readFileSync(scenarioPath,'utf8')).scenarios;
if(!Array.isArray(scenarios)||!scenarios.length)throw Error('NO_EXPANDED_SCENARIOS');
// 0.5 SUI: claiming 16 pages of 64 slots in one transaction costs more than 0.1 SUI in storage.
const GAS_BUDGET=500000000;
const MODULE='rights_scale';
const CLOCK_ID='0x6';
const ZERO_ID='0x'+'0'.repeat(64);
const DEFAULT_SENDER={attest_issuance:'attester',attest_payment:'attester',consume:'gate'};
const refBytes=tag=>Array(32).fill(tag);
const deep=v=>v instanceof Uint8Array?Array.from(v):Array.isArray(v)?v.map(deep)
  :v&&typeof v==='object'?Object.fromEntries(Object.entries(v).map(([k,x])=>[k,deep(x)]))
  :typeof v==='bigint'?Number(v):typeof v==='string'&&/^\d+$/.test(v)?Number(v):v; // BCS u64 parses to a decimal string
const hex=b=>Buffer.from(b).toString('hex');

const rpc=new SuiGrpcClient({network:'localnet',baseUrl:endpoint});
const actors={};
for(const name of ['issuer','a','b','gate','attester'])actors[name]=Ed25519Keypair.generate();
const addr=n=>actors[n].toSuiAddress();

async function faucet(address,times=1){
  for(let i=0;i<times;i++){
    const response=await fetch('http://127.0.0.1:9123/v2/gas',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({FixedAmountRequest:{recipient:address}})});
    if(!response.ok)throw Error('LOCAL_FAUCET_FAILED:'+response.status);
  }
}
await Promise.all([faucet(addr('issuer'),4),faucet(addr('a'),2),faucet(addr('b'),2),faucet(addr('gate'),2),faucet(addr('attester'),3)]);
{
  const deadline=Date.now()+30000;
  while(true){
    const balances=await Promise.all(Object.values(actors).map(k=>rpc.getBalance({owner:k.toSuiAddress()})));
    if(balances.every(r=>BigInt(r.balance.balance)>0n))break;
    if(Date.now()>deadline)throw Error('LOCAL_FAUCET_NOT_SETTLED');
    await new Promise(r=>setTimeout(r,300));
  }
}
let chain=await rpc.getChainIdentifier();
if(typeof chain!=='string')chain=chain.chainIdentifier;
if(!chain)throw Error('CHAIN_IDENTIFIER_UNAVAILABLE');

// --- transactions -----------------------------------------------------------
// Kind-only build plus manual gas for every submission, so deliberately invalid
// calls are actually executed and rejected by Move instead of being stopped by
// SDK-side simulation. All inputs must already exist or already be known.
async function prepared(name,build){
  const tx=new Transaction();
  build(tx);
  const keypair=actors[name];
  tx.setSender(keypair.toSuiAddress());
  tx.setGasBudget(GAS_BUDGET);
  const kind=await tx.build({client:rpc,onlyTransactionKind:true});
  return {keypair,kind};
}
let referenceGasPrice=null;
async function resolvedTx({keypair,kind},gasIndex=0){
  const resolved=Transaction.fromKind(kind);
  resolved.setSender(keypair.toSuiAddress());
  resolved.setGasBudget(GAS_BUDGET);
  referenceGasPrice??=(await rpc.getReferenceGasPrice()).referenceGasPrice;
  resolved.setGasPrice(referenceGasPrice);
  const {objects}=await rpc.listCoins({owner:keypair.toSuiAddress(),limit:50});
  const usable=objects.filter(c=>BigInt(c.balance)>=BigInt(GAS_BUDGET));
  const gas=usable[gasIndex]??usable[0];
  if(!gas)throw Error('LOCAL_TEST_GAS_NOT_FOUND');
  resolved.setGasPayment([{objectId:gas.objectId,version:gas.version,digest:gas.digest}]);
  return {keypair,bytes:await resolved.build()};
}
async function submitSigned({keypair,bytes}){
  const signed=await keypair.signTransaction(bytes);
  let result;
  try{
    result=await rpc.executeTransaction({transaction:bytes,signatures:[signed.signature],
      include:{effects:true,events:true,objectTypes:true}});
    await rpc.waitForTransaction({result,timeout:30000});
  }catch(e){
    // Submission-level rejection (e.g. an owned input already locked by another
    // transaction) is itself an observed outcome — recorded, never hidden.
    return {status:{success:false},submissionRejected:String(e?.message??e)};
  }
  const executed=result.Transaction??result.FailedTransaction;
  if(!executed)throw Error('UNRECOGNIZED_EXECUTION_RESULT');
  return executed;
}
const submitOne=async(name,build,gasIndex=0)=>submitSigned(await resolvedTx(await prepared(name,build),gasIndex));

function abortOf(executed){
  if(executed.status?.success)return 'ok';
  if(executed.submissionRejected)return {abort:'SUBMISSION_REJECTED',detail:executed.submissionRejected.slice(0,2000)};
  const a=executed.status?.error?.MoveAbort;
  if(!a)return {abort:'NON_ABORT_FAILURE',detail:deep(executed.status?.error)};
  const mod=String(a.location?.module??'');
  if(mod.endsWith('derived_object'))return {abort:'EObjectAlreadyExists'};
  if(mod.endsWith(MODULE))return {abort:Number(a.abortCode)};
  return {abort:'FOREIGN_ABORT',module:mod,code:a.abortCode};
}

let packageId;
const target=name=>packageId+'::'+MODULE+'::'+name;

async function view(sender,name,args){
  const tx=new Transaction();
  tx.setSender(addr(sender));
  tx.moveCall({target:target(name),arguments:args(tx)});
  const result=await rpc.simulateTransaction({transaction:tx,include:{commandResults:true}});
  const values=result.commandResults?.[0]?.returnValues;
  if(!values?.length)throw Error('VIEW_CALL_FAILED:'+name);
  return values[0].bcs;
}
async function routedIndex(controlId,paymentRef){
  const raw=await view('issuer','shard_index_for_ref',t=>[t.object(controlId),t.pure.vector('u8',paymentRef)]);
  return Number(bcs.u64().parse(raw));
}
async function getFields(id,parser){
  const {object}=await rpc.getObject({objectId:id,include:{content:true}});
  return deep(parser.parse(object.content));
}
async function chainNow(){
  return Number((await getFields(CLOCK_ID,Clock)).timestamp_ms);
}
async function listOwned(owner,typeSuffix){
  const all=[];
  let cursor=null;
  do{
    const page=await rpc.listOwnedObjects({owner,type:packageId+'::'+MODULE+'::'+typeSuffix,limit:50,cursor,include:{content:true}});
    all.push(...page.objects);
    cursor=page.hasNextPage?page.cursor:null;
  }while(cursor);
  return all;
}
async function dynamicFieldNames(parentId){
  const names=[];
  let cursor=null;
  do{
    const page=await rpc.listDynamicFields({parentId,limit:50,cursor});
    for(const f of page.dynamicFields)names.push(f.name);
    cursor=page.hasNextPage?page.cursor:null;
  }while(cursor);
  return names;
}
const byteVector=bcs.vector(bcs.u8());
function nameBytes(name){
  // gRPC dynamic-field names arrive as {type:'vector<u8>', bcs:<serialized key>}.
  if(name?.bcs&&name.type==='vector<u8>')return hex(byteVector.parse(Uint8Array.from(Object.values(name.bcs))));
  const v=name?.value;
  if(Array.isArray(v))return hex(v);
  if(typeof v==='string'){
    if(/^[0-9a-fA-F]{64}$/.test(v))return v.toLowerCase();
    return Buffer.from(v,'base64').toString('hex');
  }
  throw Error('UNRECOGNIZED_DYNAMIC_FIELD_NAME:'+JSON.stringify(name));
}
function events(executed,name,parser){
  return (executed.events??[]).filter(e=>e.eventType.endsWith('::'+MODULE+'::'+name)).map(e=>deep(parser.parse(e.bcs)));
}
async function paymentFor(ownerName,controlId,slot){
  for(const o of await listOwned(addr(ownerName),'IssuancePayment')){
    const p=IssuancePayment.parse(o.content);
    if(p.show===controlId&&Number(p.slot)===slot)return {id:o.objectId,fields:deep(p)};
  }
  return null;
}
async function evidenceFor(ownerName,controlId,ticketId){
  for(const o of await listOwned(addr(ownerName),'PaymentEvidence')){
    const p=PaymentEvidence.parse(o.content);
    if(p.show===controlId&&p.ticket===ticketId)return o.objectId;
  }
  return null;
}

// --- publish ----------------------------------------------------------------
const configArgs=process.env.KIX_SUI_CONFIG?['--client.config',process.env.KIX_SUI_CONFIG]:[];
// --build-env selects framework address resolution only; publishing uses the local RPC.
const build=spawnSync('sui',['move',...configArgs,'--build-env','mainnet','build','--path',resolve(here,'../sui'),
  '--dump-bytecode-as-base64'],{encoding:'utf8'});
await writeFile(join(out,'move-build.json'),JSON.stringify({status:build.status,stdout:build.stdout,
  stderr:build.stderr,error:build.error?String(build.error):null},null,2));
if(build.status!==0)throw Error('MOVE_BUILD_FAILED');
const compiled=JSON.parse(build.stdout);
const published=await submitOne('issuer',t=>{
  const cap=t.publish({modules:compiled.modules,dependencies:compiled.dependencies});
  t.moveCall({target:'0x2::package::make_immutable',arguments:[cap]});
});
packageId=(published.effects?.changedObjects??[]).find(x=>x.outputState?.$kind==='PackageWrite'||x.outputState?.PackageWrite)?.objectId
  ??Object.entries(published.objectTypes??{}).find(([,v])=>v==='package')?.[0];
if(!packageId)throw Error('PUBLISHED_PACKAGE_ID_NOT_FOUND_IN_EFFECTS');
const caps=await listOwned(addr('issuer'),'IssuerCap');
if(caps.length!==1)throw Error('EXPECTED_ONE_ISSUER_CAP:'+caps.length);
const issuerCapId=caps[0].objectId;

// --- per-scenario execution ---------------------------------------------------
const report={packageId,chain,actors:Object.fromEntries(Object.entries(actors).map(([n,k])=>[n,k.toSuiAddress()])),
  scenarios:[],probes:{},measurements:{}};

function recordMints(show,executed,record,step){
  const minted=events(executed,'Issuance',Issuance);
  for(const m of minted){
    record.mints.push({ticket:m.ticket,slot:m.slot,generation:m.generation,
      holder:Object.entries(report.actors).find(([,a])=>a===m.holder)?.[0]??m.holder,kind:m.kind});
    show.ticketSlot[m.ticket]=m.slot;
  }
  if(step.label&&minted.length)show.labels[step.label]=minted[0].ticket;
}
// Counts the objects a claim transaction created, from effects. Objects created and deleted
// inside one transaction are not visible here, so this is a lower bound on new IDs.
function newIdCount(executed,claims,what){
  const changed=executed.effects?.changedObjects??[];
  const kind=x=>x.idOperation?.$kind??x.idOperation;
  const created=changed.filter(x=>kind(x)==='Created');
  return {claims,what,changedObjects:changed.length,createdObjects:created.length,
    createdPerClaim:created.length/claims,idOperations:[...new Set(changed.map(kind))],
    note:'created objects in effects per claimed '+what+': the '+what+' plus its derived_object Claimed marker'
      +(what==='shard'?' (an empty Table adds no object until it has entries)':'')+'; measured, a lower bound on new IDs'};
}
async function createShow(create){
  const r=await submitOne('issuer',t=>{t.moveCall({target:target('create_show_control'),
    arguments:[t.object(issuerCapId),t.pure.u64(create.seated),t.pure.u64(create.ga),
      t.pure.u64(create.page_size),t.pure.u64(create.shards),t.pure.vector('address',[addr('gate')]),
      t.pure.vector('address',[addr('attester')]),t.pure.u64(150000),t.pure.u64(200),t.pure.u64(300),
      t.pure.id(ZERO_ID)]});});
  const controlId=Object.entries(r.objectTypes??{}).find(([,ty])=>typeof ty==='string'&&ty.endsWith('::'+MODULE+'::ShowControl'))?.[0];
  if(!controlId)throw Error('SHOW_CONTROL_ID_NOT_FOUND_IN_EFFECTS');
  return controlId;
}
function newShow(create,controlId){
  const seatedPages=create.seated===0?0:Math.ceil(create.seated/create.page_size);
  return {
    create,controlId,pages:{},shards:{},labels:{},ticketSlot:{},pageOverride:null,
    pageIndex(slot){
      if(slot<create.seated)return Math.floor(slot/create.page_size);
      return seatedPages+Math.floor((slot-create.seated)/create.page_size);
    },
    pageFor(slot){
      const index=this.pageOverride??this.pageIndex(slot);
      return this.pages[index]??Object.values(this.pages)[0];
    },
    async shardFor(ref){
      const index=await routedIndex(this.controlId,ref);
      return this.shards[index]??Object.values(this.shards)[0];
    },
  };
}
async function runStep(show,step,sender,record){
  switch(step.op){
    case 'claim_pages':{
      const r=await submitOne(sender,t=>{t.moveCall({target:target('claim_pages'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.u64(step.from),t.pure.u64(step.count)]});});
      const out0=abortOf(r);
      if(out0==='ok'){
        for(const e of events(r,'PageClaimed',PageClaimed))show.pages[e.index]=e.page;
        if(step.count>0&&!report.measurements.claimPages)report.measurements.claimPages=newIdCount(r,step.count,'page');
      }
      return out0;
    }
    case 'claim_shards':{
      const r=await submitOne(sender,t=>{t.moveCall({target:target('claim_shards'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.u64(step.from),t.pure.u64(step.count)]});});
      const out0=abortOf(r);
      if(out0==='ok'){
        for(const e of events(r,'ShardClaimed',ShardClaimed))show.shards[e.index]=e.shard;
        if(step.count>0&&!report.measurements.claimShards)report.measurements.claimShards=newIdCount(r,step.count,'shard');
      }
      return out0;
    }
    case 'seal':
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('seal'),
        arguments:[t.object(show.controlId),t.object(issuerCapId)]});}));
    case 'cancel_show':
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('cancel_show'),
        arguments:[t.object(show.controlId),t.object(issuerCapId)]});}));
    case 'issue':{
      const r=await submitOne(sender,t=>{t.moveCall({target:target('issue'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(issuerCapId),
          t.pure.u64(step.slot),t.pure.u64(step.gen),t.pure.address(addr(step.holder))]});});
      const out0=abortOf(r);
      if(out0==='ok')recordMints(show,r,record,step);
      return out0;
    }
    case 'bundle':{
      const r=await submitOne(sender,t=>{
        const b=t.moveCall({target:target('begin_bundle'),arguments:[t.object(show.controlId),t.pure.u64(step.declared)]});
        for(let i=0;i<step.issues;i++){
          const slot=step.first+i;
          t.moveCall({target:target('bundle_issue'),arguments:[b,t.object(show.controlId),
            t.object(show.pageFor(slot)),t.object(issuerCapId),t.pure.u64(slot),t.pure.u64(0),
            t.pure.address(addr(step.holder))]});
        }
        t.moveCall({target:target('finish_bundle'),arguments:[b]});
      });
      const out0=abortOf(r);
      if(out0==='ok')recordMints(show,r,record,step);
      return out0;
    }
    case 'attest_issuance':{
      const ref=refBytes(step.ref);
      const shard=await show.shardFor(ref);
      const r=await submitOne(sender,t=>{t.moveCall({target:target('attest_issuance'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
          t.pure.u64(step.slot),t.pure.u64(step.gen),t.pure.address(addr(step.buyer)),
          t.pure.u64(step.amount),t.pure.vector('u8',ref)]});});
      return abortOf(r);
    }
    case 'issue_paid':{
      const payment=await paymentFor('issuer',show.controlId,step.slot);
      if(!payment)return {abort:'DRIVER_NO_PAYMENT_OBJECT'};
      const shard=await show.shardFor(Array.from(payment.fields.payment_ref));
      const r=await submitOne(sender,t=>{t.moveCall({target:target('issue_paid'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
          t.object(issuerCapId),t.object(payment.id)]});});
      const out0=abortOf(r);
      if(out0==='ok')recordMints(show,r,record,step);
      return out0;
    }
    case 'cancel_issuance':{
      const payment=await paymentFor('issuer',show.controlId,step.slot);
      if(!payment)return {abort:'DRIVER_NO_PAYMENT_OBJECT'};
      const shard=await show.shardFor(Array.from(payment.fields.payment_ref));
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('cancel_issuance'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(shard),
          t.object(issuerCapId),t.object(payment.id)]});}));
    }
    case 'offer':{
      const expires=(await chainNow())+step.ttl_ms;
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('offer'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(show.ticketSlot[show.labels[step.ticket]])),
          t.object(show.labels[step.ticket]),t.pure.u64(step.version),t.pure.address(addr(step.recipient)),
          t.pure.u64(step.amount),t.pure.u64(expires),t.object(CLOCK_ID)]});}));
    }
    case 'accept_gift':
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('accept_gift'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(show.ticketSlot[show.labels[step.ticket]])),
          t.object(show.labels[step.ticket]),t.object(CLOCK_ID)]});}));
    case 'attest_payment':{
      const ref=refBytes(step.ref);
      const shard=await show.shardFor(ref);
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('attest_payment'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(show.ticketSlot[show.labels[step.ticket]])),
          t.object(shard),t.object(show.labels[step.ticket]),t.pure.vector('u8',ref),t.object(CLOCK_ID)]});}));
    }
    case 'accept_sale':{
      const ticketId=show.labels[step.ticket];
      const evidence=await evidenceFor(sender,show.controlId,ticketId);
      if(!evidence)return {abort:'DRIVER_NO_EVIDENCE_OBJECT'};
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('accept_sale'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(show.ticketSlot[ticketId])),
          t.object(ticketId),t.object(evidence),t.object(CLOCK_ID)]});}));
    }
    case 'authorize':{
      const expires=(await chainNow())+step.ttl_ms;
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('authorize_admission'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(show.ticketSlot[show.labels[step.ticket]])),
          t.object(show.labels[step.ticket]),t.pure.u64(step.version),t.pure.address(addr('gate')),
          t.pure.vector('u8',refBytes(1)),t.pure.u64(expires),t.object(CLOCK_ID)]});}));
    }
    case 'consume':
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('consume'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(show.ticketSlot[show.labels[step.ticket]])),
          t.object(show.labels[step.ticket]),t.pure.u64(step.version),t.pure.vector('u8',refBytes(1)),
          t.object(CLOCK_ID)]});}));
    case 'refund':
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('refund'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(show.ticketSlot[show.labels[step.ticket]])),
          t.object(show.labels[step.ticket]),t.pure.u64(step.version),t.object(CLOCK_ID)]});}));
    case 'revoke':
      return abortOf(await submitOne(sender,t=>{t.moveCall({target:target('revoke'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(show.ticketSlot[show.labels[step.ticket]])),
          t.object(issuerCapId),t.object(show.labels[step.ticket])]});}));
    default:
      return {abort:'DRIVER_UNKNOWN_OP'};
  }
}
async function snapshot(show){
  const control=await getFields(show.controlId,ShowControl);
  const pages=[];
  for(const index of Object.keys(show.pages).map(Number).sort((x,y)=>x-y)){
    const f=await getFields(show.pages[index],InventoryPage);
    pages.push({index:f.index,start:f.start,end:f.end,mode:f.mode,generations:f.generations,
      occupied:f.occupied,issuances:f.issuances,free:f.free,reserved:f.reserved,issued:f.issued,retired:f.retired});
  }
  const shards=[];
  for(const index of Object.keys(show.shards).map(Number).sort((x,y)=>x-y)){
    const f=await getFields(show.shards[index],PaymentRefShard);
    const names=await dynamicFieldNames(f.refs);
    shards.push({index:f.index,refs:names.map(nameBytes).sort()});
  }
  const tickets={};
  for(const m of show_mints(show)){
    const f=await getFields(m.ticket,Ticket);
    tickets[m.ticket]={slot:f.slot,generation:f.generation,
      holder:Object.entries(report.actors).find(([,a])=>a===f.holder)?.[0]??f.holder,
      version:f.version,state:f.state,last_amount:f.last_amount};
  }
  const payments=[];
  for(const o of await listOwned(addr('issuer'),'IssuancePayment')){
    const p=deep(IssuancePayment.parse(o.content));
    if(p.show===show.controlId)payments.push({slot:p.slot,expected_generation:p.expected_generation,
      buyer:Object.entries(report.actors).find(([,a])=>a===p.buyer)?.[0]??p.buyer,amount:p.amount,payment_ref:hex(p.payment_ref)});
  }
  const evidence=[];
  for(const name of Object.keys(actors)){
    for(const o of await listOwned(addr(name),'PaymentEvidence')){
      const p=deep(PaymentEvidence.parse(o.content));
      if(p.show===show.controlId)evidence.push({ticket:p.ticket,version:p.version,
        buyer:Object.entries(report.actors).find(([,a])=>a===p.buyer)?.[0]??p.buyer,
        seller:Object.entries(report.actors).find(([,a])=>a===p.seller)?.[0]??p.seller,
        amount:p.amount,payment_ref:hex(p.payment_ref)});
    }
  }
  return {control:{open:control.open,sealed:control.sealed,cancel_generation:control.cancel_generation,
    claimed_pages:control.claimed_pages,claimed_shards:control.claimed_shards,claim_sequence:control.claim_sequence},
    pages,shards,tickets,payments,evidence};
}
const mintRegistry=new Map(); // controlId -> mint list accumulated across recordMints
function show_mints(show){return mintRegistry.get(show.controlId)??[];}

for(const scenario of scenarios){
  const controlId=await createShow(scenario.create);
  const show=newShow(scenario.create,controlId);
  mintRegistry.set(controlId,[]);
  const record={name:scenario.name,controlId,create:scenario.create,outcomes:[],mints:mintRegistry.get(controlId),labels:{}};
  for(const step of scenario.steps){
    show.pageOverride=step.page??null;
    const sender=step.sender??DEFAULT_SENDER[step.op]??'issuer';
    let outcome;
    try{
      outcome=await runStep(show,step,sender,record);
    }catch(e){
      outcome={abort:'DRIVER_ERROR',detail:String(e?.message??e)};
    }
    record.outcomes.push(outcome==='ok'?'ok':outcome);
  }
  show.pageOverride=null;
  record.labels=show.labels;
  record.snapshot=await snapshot(show);
  report.scenarios.push(record);
}

// --- concurrency probes (C01/C04/C06 + IssuerCap serialization) ---------------
{
  const probe={seated:16,ga:0,page_size:4,shards:2};
  const controlId=await createShow(probe);
  const show=newShow(probe,controlId);
  const r1=await submitOne('issuer',t=>{t.moveCall({target:target('claim_pages'),
    arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.u64(0),t.pure.u64(4)]});});
  for(const e of events(r1,'PageClaimed',PageClaimed))show.pages[e.index]=e.page;
  const r2=await submitOne('issuer',t=>{t.moveCall({target:target('claim_shards'),
    arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.u64(0),t.pure.u64(2)]});});
  for(const e of events(r2,'ShardClaimed',ShardClaimed))show.shards[e.index]=e.shard;
  await submitOne('issuer',t=>{t.moveCall({target:target('seal'),arguments:[t.object(show.controlId),t.object(issuerCapId)]});});
  const parallel=async(name,b1,b2)=>{
    const [p1,p2]=await Promise.all([
      resolvedTx(await prepared(name,b1),0),
      resolvedTx(await prepared(name,b2),1),
    ]);
    const [x1,x2]=await Promise.all([submitSigned(p1),submitSigned(p2)]);
    return [x1,x2];
  };
  // C03a/C05 evidence: two concurrent direct issues on different slots sharing one
  // &IssuerCap. Recorded, not asserted: serialization mechanism is a measured fact.
  {
    const [x,y]=await parallel('issuer',
      t=>{t.moveCall({target:target('issue'),arguments:[t.object(show.controlId),t.object(show.pageFor(0)),
        t.object(issuerCapId),t.pure.u64(0),t.pure.u64(0),t.pure.address(addr('a'))]});},
      t=>{t.moveCall({target:target('issue'),arguments:[t.object(show.controlId),t.object(show.pageFor(1)),
        t.object(issuerCapId),t.pure.u64(1),t.pure.u64(0),t.pure.address(addr('b'))]});});
    report.probes.issuerCap={a:abortOf(x),b:abortOf(y),
      note:'two concurrent issuer-signed issues sharing &IssuerCap; outcome recorded, not assumed'};
  }
  // C01: two concurrent attester submissions on the same slot, no owned input.
  {
    const shard0=await show.shardFor(refBytes(80)),shard1=await show.shardFor(refBytes(81));
    const [x,y]=await parallel('attester',
      t=>{t.moveCall({target:target('attest_issuance'),arguments:[t.object(show.controlId),
        t.object(show.pageFor(2)),t.object(shard0),t.pure.u64(2),t.pure.u64(0),t.pure.address(addr('a')),
        t.pure.u64(1000),t.pure.vector('u8',refBytes(80))]});},
      t=>{t.moveCall({target:target('attest_issuance'),arguments:[t.object(show.controlId),
        t.object(show.pageFor(2)),t.object(shard1),t.pure.u64(2),t.pure.u64(0),t.pure.address(addr('a')),
        t.pure.u64(1000),t.pure.vector('u8',refBytes(81))]});});
    report.probes.duplicateSlotRace={a:abortOf(x),b:abortOf(y)};
    // exactly one must land; the loser leaves no reservation behind
    const okCount=[x,y].filter(r=>r.status?.success).length;
    report.probes.duplicateSlotRace.exactlyOneSucceeded=okCount===1;
    if(okCount!==1)throw Error('DUPLICATE_SLOT_RACE_NOT_EXACTLY_ONE');
  }
  // C04: two overlapping bundles concurrently; the loser must leave no issuance.
  {
    const bundle=(first)=>t=>{
      const b=t.moveCall({target:target('begin_bundle'),arguments:[t.object(show.controlId),t.pure.u64(3)]});
      for(let i=0;i<3;i++)t.moveCall({target:target('bundle_issue'),arguments:[b,t.object(show.controlId),
        t.object(show.pageFor(first+i)),t.object(issuerCapId),t.pure.u64(first+i),t.pure.u64(0),
        t.pure.address(addr('a'))]});
      t.moveCall({target:target('finish_bundle'),arguments:[b]});
    };
    const [x,y]=await parallel('issuer',bundle(4),bundle(5));
    report.probes.bundleRace={a:abortOf(x),b:abortOf(y)};
    const okCount=[x,y].filter(r=>r.status?.success).length;
    report.probes.bundleRace.exactlyOneSucceeded=okCount===1;
    if(okCount!==1)throw Error('BUNDLE_RACE_NOT_EXACTLY_ONE');
  }
  // C06/C07: cancel_show racing a direct issue on a fresh slot. Either serial
  // order is consistent: issue first (both ok), cancel first (issue EClosed), or
  // an owned-input lock rejects the loser at submission (still total order).
  {
    const [x,y]=await parallel('issuer',
      t=>{t.moveCall({target:target('issue'),arguments:[t.object(show.controlId),t.object(show.pageFor(8)),
        t.object(issuerCapId),t.pure.u64(8),t.pure.u64(0),t.pure.address(addr('a'))]});},
      t=>{t.moveCall({target:target('cancel_show'),arguments:[t.object(show.controlId),t.object(issuerCapId)]});});
    const issueOutcome=abortOf(x),cancelOutcome=abortOf(y);
    const lost=o=>o==='ok'?false:(o?.abort===1||o?.abort==='SUBMISSION_REJECTED');
    const consistent=(issueOutcome==='ok'&&cancelOutcome==='ok')
      ||(cancelOutcome==='ok'&&lost(issueOutcome))
      ||(issueOutcome==='ok'&&lost(cancelOutcome));
    report.probes.cancelVersusIssue={issue:issueOutcome,cancel:cancelOutcome,serialConsistent:consistent};
    if(!consistent)throw Error('CANCEL_VERSUS_ISSUE_NOT_SERIAL_CONSISTENT');
    // Close the probe show if the race loser was the cancel (lost-response retry path).
    if(cancelOutcome!=='ok'){
      const retry=await submitOne('issuer',t=>{t.moveCall({target:target('cancel_show'),
        arguments:[t.object(show.controlId),t.object(issuerCapId)]});});
      report.probes.cancelVersusIssue.cancelRetry=abortOf(retry);
      if(abortOf(retry)!=='ok')throw Error('CANCEL_RETRY_FAILED');
    }
  }
  // Conservation still holds on the probe show after the races.
  {
    const snap=await snapshot(show);
    for(const p of snap.pages){
      if(p.free+p.reserved+p.issued+p.retired!==p.end-p.start)throw Error('PROBE_PAGE_NOT_CONSERVED:'+p.index);
    }
    report.probes.probeShowConserved=true;
  }
}

await writeFile(join(out,'chain-report.json'),JSON.stringify(report,null,2)+'\n');
console.log('chain-report written: '+join(out,'chain-report.json'));
await new Promise(resolve=>process.stdout.write('',resolve));
process.exit(0);
