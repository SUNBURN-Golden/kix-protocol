// Localnet plumbing shared by the extended-profile private journey. Same submission model as
// localnet.mjs (kind-only build plus manual gas, so deliberately invalid calls are really
// executed and rejected by Move) but kept here so the RS-1 driver stays byte-identical.
// Requires an ACTUAL Sui localnet. No real funds, no public endpoints, no mocked RPC.
import {spawnSync} from 'node:child_process';
import {resolve} from 'node:path';
import {SuiGrpcClient} from '@mysten/sui/grpc';
import {Ed25519Keypair} from '@mysten/sui/keypairs/ed25519';
import {Transaction} from '@mysten/sui/transactions';
import {Clock} from './types.mjs';

export const MODULE='rights_scale';
export const CLOCK_ID='0x6';
export const ZERO_ID='0x'+'0'.repeat(64);
export const GAS_BUDGET=500000000;
export const hex=b=>Buffer.from(b).toString('hex');
export const deep=v=>v instanceof Uint8Array?Array.from(v):Array.isArray(v)?v.map(deep)
  :v&&typeof v==='object'?Object.fromEntries(Object.entries(v).map(([k,x])=>[k,deep(x)]))
  :typeof v==='bigint'?Number(v):typeof v==='string'&&/^\d+$/.test(v)&&v.length<16?Number(v):v;
// u256 fields must stay exact: parsed objects keep them as decimal strings.
export const exact=(parsed)=>JSON.parse(JSON.stringify(parsed,(_,v)=>typeof v==='bigint'?v.toString():v));

export function localEndpoint() {
  const endpoint=process.env.KIX_LOCAL_RPC??'http://127.0.0.1:9000';
  if(!['127.0.0.1','localhost','[::1]'].includes(new URL(endpoint).hostname))throw Error('LOCALNET_ONLY');
  return endpoint;
}

// A transient transport failure is not a chain answer: retry a single call a
// few times before giving up (the driver's digest reconciliation does the same
// for lost submission responses). A persistent failure still throws. `onRetry`
// lets callers record the attempts so a flaky link is visible, not hidden.
export async function transient(call,{tries=5,onRetry}={}) {
  for(let attempt=0;;attempt++) {
    try{return await call();}
    catch(e){
      if(attempt>=tries-1)throw e;
      onRetry?.(e,attempt);
      await new Promise(r=>setTimeout(r,400*(attempt+1)));
    }
  }
}

export async function connect(actorNames,faucetTimes={}) {
  const endpoint=localEndpoint();
  const rpc=new SuiGrpcClient({network:'localnet',baseUrl:endpoint});
  const actors={};
  for(const name of actorNames)actors[name]=Ed25519Keypair.generate();
  const addr=n=>actors[n].toSuiAddress();
  await Promise.all(actorNames.map(async name=>{
    for(let i=0;i<(faucetTimes[name]??2);i++) {
      const response=await fetch('http://127.0.0.1:9123/v2/gas',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({FixedAmountRequest:{recipient:addr(name)}})});
      if(!response.ok)throw Error('LOCAL_FAUCET_FAILED:'+response.status);
    }
  }));
  const deadline=Date.now()+30000;
  while(true) {
    const balances=await Promise.all(Object.values(actors).map(k=>transient(()=>rpc.getBalance({owner:k.toSuiAddress()}))));
    if(balances.every(r=>BigInt(r.balance.balance)>0n))break;
    if(Date.now()>deadline)throw Error('LOCAL_FAUCET_NOT_SETTLED');
    await new Promise(r=>setTimeout(r,300));
  }
  let chain=await transient(()=>rpc.getChainIdentifier());
  if(typeof chain!=='string')chain=chain.chainIdentifier;
  if(!chain)throw Error('CHAIN_IDENTIFIER_UNAVAILABLE');

  let referenceGasPrice=null;
  async function resolvedTx(name,build,gasIndex=0) {
    const tx=new Transaction();
    build(tx);
    const keypair=actors[name];
    tx.setSender(keypair.toSuiAddress());
    tx.setGasBudget(GAS_BUDGET);
    const kind=await transient(()=>tx.build({client:rpc,onlyTransactionKind:true}));
    const resolved=Transaction.fromKind(kind);
    resolved.setSender(keypair.toSuiAddress());
    resolved.setGasBudget(GAS_BUDGET);
    referenceGasPrice??=(await transient(()=>rpc.getReferenceGasPrice())).referenceGasPrice;
    resolved.setGasPrice(referenceGasPrice);
    const {objects}=await transient(()=>rpc.listCoins({owner:keypair.toSuiAddress(),limit:50}));
    const usable=objects.filter(c=>BigInt(c.balance)>=BigInt(GAS_BUDGET));
    const gas=usable[gasIndex]??usable[0];
    if(!gas)throw Error('LOCAL_TEST_GAS_NOT_FOUND');
    resolved.setGasPayment([{objectId:gas.objectId,version:gas.version,digest:gas.digest}]);
    return {keypair,bytes:await resolved.build()};
  }
  async function submitSigned({keypair,bytes}) {
    const signed=await keypair.signTransaction(bytes);
    let result;
    try{
      result=await transient(async()=>{
        const r=await rpc.executeTransaction({transaction:bytes,signatures:[signed.signature],
          include:{effects:true,events:true,objectTypes:true}});
        await rpc.waitForTransaction({result:r,timeout:30000});
        return r;
      });
    }catch(e){
      // Submission-level rejection is itself an observed outcome: recorded, never hidden.
      return {status:{success:false},submissionRejected:String(e?.message??e)};
    }
    const executed=result.Transaction??result.FailedTransaction;
    if(!executed)throw Error('UNRECOGNIZED_EXECUTION_RESULT');
    return executed;
  }
  const submitOne=async(name,build,gasIndex=0)=>submitSigned(await resolvedTx(name,build,gasIndex));
  async function getFields(id,parser) {
    const {object}=await transient(()=>rpc.getObject({objectId:id,include:{content:true}}));
    return exact(parser.parse(object.content));
  }
  async function chainNow(){return Number((await getFields(CLOCK_ID,Clock)).timestamp_ms);}
  async function listOwned(owner,type) {
    const all=[];let cursor=null;
    do{
      const page=await transient(()=>rpc.listOwnedObjects({owner,type,limit:50,cursor,include:{content:true}}));
      all.push(...page.objects);cursor=page.hasNextPage?page.cursor:null;
    }while(cursor);
    return all;
  }
  return {endpoint,rpc,actors,addr,chain,resolvedTx,submitSigned,submitOne,getFields,chainNow,listOwned};
}

/** Maps an execution result to 'ok' or a comparable abort record. */
export function abortOf(executed) {
  if(executed.status?.success)return 'ok';
  if(executed.submissionRejected)return {abort:'SUBMISSION_REJECTED',detail:executed.submissionRejected.slice(0,2000)};
  const a=executed.status?.error?.MoveAbort;
  if(!a)return {abort:'NON_ABORT_FAILURE',detail:deep(executed.status?.error)};
  const mod=String(a.location?.module??'');
  if(mod.endsWith('derived_object'))return {abort:'EObjectAlreadyExists'};
  if(mod.endsWith(MODULE))return {abort:Number(a.abortCode)};
  // The verifier module aborts with code 2 when Groth16 rejects the proof.
  if(mod.endsWith('zk_gate'))return {abort:'zk_gate:'+a.abortCode};
  return {abort:'FOREIGN_ABORT',module:mod,code:String(a.abortCode)};
}

export function eventsOf(executed,name,parser) {
  return (executed.events??[]).filter(e=>e.eventType.endsWith('::'+MODULE+'::'+name)).map(e=>exact(parser.parse(e.bcs)));
}

export function buildPackage(moveDir) {
  const configArgs=process.env.KIX_SUI_CONFIG?['--client.config',process.env.KIX_SUI_CONFIG]:[];
  // --build-env selects framework address resolution only; publishing uses the local RPC.
  const build=spawnSync('sui',['move',...configArgs,'--build-env','mainnet','build','--path',resolve(moveDir),
    '--dump-bytecode-as-base64'],{encoding:'utf8'});
  if(build.status!==0)throw Error('MOVE_BUILD_FAILED:'+String(build.stderr).slice(-2000));
  return {compiled:JSON.parse(build.stdout),log:{status:build.status,stderr:build.stderr}};
}
