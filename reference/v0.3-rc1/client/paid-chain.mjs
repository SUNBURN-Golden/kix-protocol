// Trusted local adapter: all chain facts below are queried from Sui, never
// accepted as a caller-provided success flag. This is NOT checkpoint verification.
import {bcs} from '@mysten/sui/bcs';
import {Transaction} from '@mysten/sui/transactions';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {IndependentClient} from './independent.mjs';
import {Change} from './types.mjs';

const Allocation=bcs.struct('Allocation',{show:bcs.Address,ticket:bcs.Address,payment:bcs.vector(bcs.u8()),
  seller:bcs.Address,total:bcs.u64(),seller_due:bcs.u64(),organizer_due:bcs.u64(),platform_due:bcs.u64()});
const Terms=bcs.struct('Terms',{show:bcs.Address,ticket:bcs.Address,version:bcs.u64(),seller:bcs.Address,buyer:bcs.Address,
  amount:bcs.u64(),expires_ms:bcs.u64(),organizer_bps:bcs.u64(),platform_bps:bcs.u64()});
export const canonical=value=>JSON.stringify(value,(_k,v)=>v && typeof v==='object' && !Array.isArray(v)
  ? Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
export const hash=value=>createHash('sha256').update(canonical(value)).digest('hex');
const hex=v=>Buffer.from(v).toString('hex');
const check=(ok,reason)=>{if(!ok)throw Error(reason);};
export function clientFor(endpoint,binding){
  check(['localhost','127.0.0.1','[::1]'].includes(new URL(endpoint).hostname),'LOCALNET_ONLY');
  return new IndependentClient({endpoint,expectedChain:binding.chain,packageId:binding.packageId});
}
export function policyFor(b){return {primaryPrice:100000,resaleCap:b.resaleCap,primaryFeeBps:500,
  resaleFeeBps:b.platformBps,resaleOrganizerBps:b.organizerBps,resaleAllowed:true,refundProfile:'LATEST_TRADE_UNWIND_FIXTURE'};}
function policyBinding(b){
  check(b.format==='kix-paid-localnet-v1' && b.currency==='KRW' && b.policyHash===hash(policyFor(b)),'POLICY_BINDING_MISMATCH');
  check(Number.isSafeInteger(b.amount) && b.amount>0 && b.amount<=b.resaleCap,'AMOUNT_BINDING_MISMATCH');
}
export async function inspectOffer(endpoint,b){
  policyBinding(b);
  const c=clientFor(endpoint,b),s=await c.right(b.showId,b.ticketId),t=s.ticket,o=t.offer;
  check(b.format==='kix-paid-localnet-v1' && b.currency==='KRW' && b.policyHash===hash(policyFor(b)),'POLICY_BINDING_MISMATCH');
  check(s.valid && Number(t.version)===b.expectedVersion && Number(t.slot)===b.slot && Number(t.generation)===b.generation
    && t.holder===b.seller && s.show.issuer===b.organizer,'RIGHT_BINDING_MISMATCH');
  check(Number(s.show.organizer_bps)===b.organizerBps && Number(s.show.platform_bps)===b.platformBps
    && Number(s.show.resale_cap)===b.resaleCap,'SHOW_POLICY_MISMATCH');
  check(o && o.recipient===b.buyer && Number(o.amount)===b.amount && o.expires_ms===b.expiresMs
    && Number(o.version)===b.expectedVersion && hex(o.terms)===b.termsHash && await c.now()<BigInt(b.expiresMs),'OFFER_BINDING_MISMATCH');
  // Confirm the digest uses exactly Move's BCS Terms, including expiry and bps.
  const {blake2b}=await import('@noble/hashes/blake2.js');
  const terms=Terms.serialize({show:b.showId,ticket:b.ticketId,version:b.expectedVersion,seller:b.seller,buyer:b.buyer,
    amount:b.amount,expires_ms:b.expiresMs,organizer_bps:b.organizerBps,platform_bps:b.platformBps}).toBytes();
  check(hex(blake2b(terms,{dkLen:32}))===b.termsHash,'TERMS_HASH_MISMATCH');
  return {bindingHash:hash(b),state:'VERIFIED_CURRENT_OFFER',source:'ACTUAL_SUI_LOCALNET_TRUSTED_RPC'};
}
export async function inspectClosed(endpoint,b){
  const c=clientFor(endpoint,b),current=await c.right(b.showId,b.ticketId);
  check(!current.show.open,'SHOW_NOT_CLOSED');
  return {state:'SHOW_PERMANENTLY_CLOSED',chain:b.chain,showId:b.showId,bindingHash:hash(b),
    holder:current.ticket.holder,version:current.ticket.version,objectVersion:current.objectVersion,
    source:'ACTUAL_SUI_LOCALNET_TRUSTED_RPC'};
}
export async function inspectOpen(endpoint,b){
  const c=clientFor(endpoint,b),current=await c.right(b.showId,b.ticketId);
  check(current.show.open,'SHOW_CLOSED_PAYOUT_BLOCKED');
  return {state:'SHOW_OPEN_AT_QUERY',chain:b.chain,showId:b.showId,bindingHash:hash(b),
    objectVersion:current.objectVersion,source:'ACTUAL_SUI_LOCALNET_TRUSTED_RPC'};
}
export async function observeSale(endpoint,b,saved){
  policyBinding(b);
  const c=clientFor(endpoint,b);await c.chain();
  check(saved.bindingHash===hash(b) && saved.chain===b.chain && saved.packageId===b.packageId,'SUBMISSION_BINDING_MISMATCH');
  const tx=Transaction.from(Buffer.from(saved.bytes,'base64'));
  check(await tx.getDigest()===saved.digest && tx.getData().sender===b.buyer,'SIGNED_DIGEST_MISMATCH');
  let result;
  try {result=await c.rpc.getTransaction({digest:saved.digest,include:{effects:true,events:true}});}
  catch {return {state:'OUTCOME_UNKNOWN',digest:saved.digest,bindingHash:hash(b)};}
  const r=result.Transaction??result.FailedTransaction;
  check(r?.digest===saved.digest && typeof r.status.success==='boolean','UNRECOGNIZED_CHAIN_RECEIPT');
  const raw={digest:r.digest,status:r.status,events:(r.events??[]).map(e=>({type:e.eventType,bcs:hex(e.bcs)}))};
  const base={digest:r.digest,bindingHash:hash(b),raw,rawHash:hash(raw),source:'ACTUAL_SUI_LOCALNET_TRUSTED_RPC',observedAt:new Date().toISOString()};
  if(!r.status.success){
    const current=await c.right(b.showId,b.ticketId);
    // Closing is irreversible in this Move package. A timeout or generic abort
    // alone does not prove that a different still-live sale cannot execute.
    const fenced=!current.show.open && current.ticket.holder===b.seller && Number(current.ticket.version)===b.expectedVersion;
    return {...base,state:'EXECUTED_FAILURE',compensationFence:fenced?'SHOW_CLOSED_UNTRANSFERRED':null};
  }
  const events=r.events??[];
  const decode=(name,parser)=>events.filter(e=>e.eventType===b.packageId+'::rights::'+name).map(e=>parser.parse(e.bcs));
  const allocations=decode('Allocation',Allocation),changes=decode('Change',Change);
  check(allocations.length===1 && changes.length===1,'SALE_EVENTS_REQUIRED');
  const a=allocations[0],change=changes[0],organizerDue=Number(BigInt(b.amount)*BigInt(b.organizerBps)/10000n),platformDue=Number(BigInt(b.amount)*BigInt(b.platformBps)/10000n);
  check(a.show===b.showId && a.ticket===b.ticketId && hex(a.payment)===saved.paymentRef && a.seller===b.seller
    && Number(a.total)===b.amount && Number(a.organizer_due)===organizerDue && Number(a.platform_due)===platformDue
    && Number(a.seller_due)===b.amount-organizerDue-platformDue,'ALLOCATION_BINDING_MISMATCH');
  check(change.show===b.showId && change.ticket===b.ticketId && change.holder===b.buyer
    && Number(change.version)===b.expectedVersion+1 && change.state===0 && change.kind===1,'TRANSFER_BINDING_MISMATCH');
  return {...base,state:'EXECUTED_SUCCESS',allocation:a,change};
}
export async function recoveryContext(endpoint,b,saved){
  const sale=await observeSale(endpoint,b,saved),c=clientFor(endpoint,b);
  const current=await c.right(b.showId,b.ticketId);
  return {bindingHash:hash(b),sale,showOpen:current.show.open,objectVersion:current.objectVersion,
    holder:current.ticket.holder,version:current.ticket.version,
    source:'ACTUAL_SUI_LOCALNET_TRUSTED_RPC'};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
  const q=JSON.parse(readFileSync(0,'utf8'));
  const result=q.action==='inspect'?await inspectOffer(q.endpoint,q.binding):q.action==='closed'?await inspectClosed(q.endpoint,q.binding):
    q.action==='open'?await inspectOpen(q.endpoint,q.binding):
    q.action==='recovery'?await recoveryContext(q.endpoint,q.binding,q.submission):
    q.action==='observe'?await observeSale(q.endpoint,q.binding,q.submission):(()=>{throw Error('UNKNOWN_CHAIN_QUERY');})();
  console.log(JSON.stringify(result));
}
