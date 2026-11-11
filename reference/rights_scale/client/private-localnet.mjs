// Requires an ACTUAL Sui localnet, a built package and the fixture artifacts from setup-zk.mjs.
// Replays vectors/private_path.json against the published kix_rights_scale package with real
// Groth16 proofs, and writes private-report.json: per-step observed outcomes and a chain snapshot
// per show. compare_private.py replays the same steps on model.py and asserts agreement.
// Every outcome comes from executeTransaction effects: no mocked RPC, no fabricated receipts,
// no real funds. The ceremony behind the keys is a single-party local fixture.
import {readFileSync} from 'node:fs';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {bcs} from '@mysten/sui/bcs';
import {ShowControl,InventoryPage,Ticket,NoteTree,RevocationState,NullifierShard,ChallengeShard,
  PageClaimed,ShardClaimed,Issuance,NoteAdded,RevocationLeaf,PrivateAdmission,ZkClaimed} from './types.mjs';
import {connect,abortOf,eventsOf,buildPackage,deep,CLOCK_ID,MODULE} from './chain-kit.mjs';
import {artifacts,checkVerifier,mintNote,admissionProof,revocationUpdate,domainOf,poseidon,noteTreeOf,revocationTreeOf} from './private-scale.mjs';
import {jsonRpcEventSource,checkpointEventSource,rebuildTreeView} from './chain-witness.mjs';
import {FR} from './zk-helpers.mjs';
import * as P from './profile-constants.mjs';

const here=fileURLToPath(new URL('.',import.meta.url));
const out=resolve(process.env.KIX_JOURNEY_DIR??join(here,'../results/private-localnet'));
await mkdir(out,{recursive:true});
const doc=JSON.parse(readFileSync(process.env.KIX_PRIVATE_SCENARIOS??join(here,'../vectors/private_path.json'),'utf8'));
const scenarios=doc.scenarios;
const ACTORS=['issuer','a','b','gate','gate2','attester'];
const refBytes=tag=>Array(32).fill(tag);
const timings={mintProofMs:[],spendProofMs:[],stepMs:{}};
const gasLog={};

const art=await artifacts();
const kit=await connect(ACTORS,{issuer:8,a:3,b:3,gate:3,gate2:3,attester:2});
const {rpc,addr,submitOne,getFields,chainNow}=kit;
const H=await poseidon();

// ---- publish the package and install the verifiers ---------------------------------------
const built=buildPackage(resolve(here,'../sui'));
const published=await submitOne('issuer',t=>{
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
const bytesArg=hexString=>Array.from(Buffer.from(hexString,'hex'));
// v1: the real fixture verifier. v2: the same keys under a different manifest hash, a deliberate
// negative fixture whose only difference is the circuit manifest hash the domain binds (RS-C11).
const altHash=createHash('sha256').update('KIX-rs-2-alternate-circuit-manifest-fixture').digest('hex');
const verifiers={};
for(const [label,hash] of [['v1',art.hash],['v2',altHash]]) {
  const r=await submitOne('issuer',t=>{t.moveCall({target:target('create','zk_gate'),
    arguments:[t.pure.vector('u8',art.mintVK),t.pure.vector('u8',art.spendVK),t.pure.vector('u8',bytesArg(hash))]});});
  if(abortOf(r)!=='ok')throw Error('VERIFIER_INSTALL_FAILED:'+label+JSON.stringify(abortOf(r)));
  verifiers[label]={id:createdOfType(r,'::zk_gate::Verifier'),manifestHash:hash};
}
// IM-27: the client pins the real verifier object, package, manifest and key bytes before use.
await checkVerifier(rpc,packageId,verifiers.v1.id,art.hash);
let pinMismatch='NOT_TESTED';
try{await checkVerifier(rpc,packageId,verifiers.v2.id,art.hash);pinMismatch='NOT_DETECTED';}catch(e){pinMismatch=String(e.message);}
if(pinMismatch!=='VERIFIER_KEY_PIN_MISMATCH')throw Error('ALTERNATE_VERIFIER_NOT_REFUSED_BY_THE_PIN:'+pinMismatch);

// ---- the package's constants must equal the client's and the model's -----------------------
async function view(name,args=()=>[]) {
  const tx=new (await import('@mysten/sui/transactions')).Transaction();
  tx.setSender(addr('issuer'));
  tx.moveCall({target:target(name),arguments:args(tx)});
  const result=await rpc.simulateTransaction({transaction:tx,include:{commandResults:true}});
  const values=result.commandResults?.[0]?.returnValues;
  if(!values?.length)throw Error('VIEW_CALL_FAILED:'+name);
  return values[0].bcs;
}
const viewU64=async(name,args)=>Number(bcs.u64().parse(await view(name,args)));
const constants={zk_depth:await viewU64('zk_depth'),localnet_root_history_k:await viewU64('localnet_root_history_k'),
  localnet_nullifier_shards:await viewU64('localnet_nullifier_shards'),localnet_challenge_shards:await viewU64('localnet_challenge_shards'),
  profile_version:await viewU64('profile_version')};
for(const [chainName,want] of [['zk_depth',P.DEPTH],['localnet_root_history_k',P.ROOT_HISTORY_K],['localnet_nullifier_shards',P.NULLIFIER_SHARDS],
  ['localnet_challenge_shards',P.CHALLENGE_SHARDS],['profile_version',P.PROFILE_VERSION]]) {
  if(constants[chainName]!==want)throw Error('PACKAGE_CONSTANT_MISMATCH:'+chainName+':'+constants[chainName]+'!='+want);
}
if(art.manifest.rootHistoryK!==constants.localnet_root_history_k)throw Error('MANIFEST_K_NOT_THE_PACKAGE_K');

const report={packageId,chain:kit.chain,actors:Object.fromEntries(ACTORS.map(n=>[n,addr(n)])),
  verifiers:Object.fromEntries(Object.entries(verifiers).map(([k,v])=>[k,{id:v.id,manifestHash:v.manifestHash}])),
  manifest:{hash:art.hash,format:art.manifest.format,depth:art.manifest.depth,rootHistoryK:art.manifest.rootHistoryK,
    constraints:art.manifest.constraints,ptauPower:art.manifest.phase1.ptauPower,phase1:art.manifest.phase1.source,setup:art.manifest.setup},
  constants,alternateVerifierPinCheck:pinMismatch,scenarios:[],measurements:{},timings,gas:gasLog};

// ---- helpers -------------------------------------------------------------------------------
const actorName=address=>Object.entries(report.actors).find(([,a])=>a===address)?.[0]??address;
function recordGas(op,executed) {
  const g=executed.effects?.gasUsed;
  if(!g)return;
  (gasLog[op]??=[]).push({computationCost:String(g.computationCost),storageCost:String(g.storageCost),storageRebate:String(g.storageRebate)});
}
async function createShow(name,cfg) {
  const r=await submitOne('issuer',t=>{t.moveCall({target:target('create_show_control'),
    arguments:[t.object(issuerCapId),t.pure.u64(cfg.seated),t.pure.u64(cfg.ga),t.pure.u64(cfg.page_size),t.pure.u64(cfg.shards),
      t.pure.vector('address',doc.gates.map(g=>addr(g))),t.pure.vector('address',[addr('attester')]),
      t.pure.u64(150000),t.pure.u64(200),t.pure.u64(300),t.pure.id(verifiers[cfg.verifier].id)]});});
  if(abortOf(r)!=='ok')throw Error('CREATE_SHOW_FAILED:'+name+JSON.stringify(abortOf(r)));
  const controlId=createdOfType(r,'::'+MODULE+'::ShowControl');
  const seatedPages=cfg.seated===0?0:Math.ceil(cfg.seated/cfg.page_size);
  return {name,cfg,controlId,pages:{},shards:{},tree:null,revocation:null,nullifierShards:[],challengeShards:[],domain:null,
    labels:{},mints:[],view:{noteLeaves:[],revoked:new Map()},
    pageFor(slot){
      const index=slot<cfg.seated?Math.floor(slot/cfg.page_size):seatedPages+Math.floor((slot-cfg.seated)/cfg.page_size);
      return this.pages[index]??Object.values(this.pages)[0];
    }};
}
// Rebuilds the cache assertion: the roots stored on chain must be the roots of the cached public data.
async function assertCacheMatchesChain(show) {
  if(!show.tree)return;
  const tree=await getFields(show.tree,NoteTree),rev=await getFields(show.revocation,RevocationState);
  if(String(noteTreeOf(H,show.view.noteLeaves).root)!==String(tree.root)||show.view.noteLeaves.length!==Number(tree.leaf_count))
    throw Error('CACHED_NOTE_ROOT_DIFFERS_FROM_CHAIN:'+show.name);
  if(String(revocationTreeOf(H,show.view.revoked).root)!==String(rev.root))throw Error('CACHED_REVOCATION_ROOT_DIFFERS_FROM_CHAIN:'+show.name);
}
// One scan source for the whole run: it reads each checkpoint once and keeps what it read.
const scanSource=checkpointEventSource(rpc);
const rpcSource=jsonRpcEventSource(kit.endpoint);
async function eventsView(show) {
  const args={packageId,controlId:show.controlId,treeId:show.tree,revocationId:show.revocation,domain:show.domain,getFields};
  const viaRpc=await rebuildTreeView({source:rpcSource,...args});
  const viaScan=await rebuildTreeView({source:scanSource,...args});
  const same=JSON.stringify([viaRpc.noteLeaves.map(String),[...viaRpc.revoked].map(([k,v])=>[k,String(v)])])
    ===JSON.stringify([viaScan.noteLeaves.map(String),[...viaScan.revoked].map(([k,v])=>[k,String(v)])]);
  const cached=JSON.stringify([show.view.noteLeaves.map(String),[...show.view.revoked].sort((x,y)=>x[0]-y[0]).map(([k,v])=>[k,String(v)])]);
  const rebuilt=JSON.stringify([viaRpc.noteLeaves.map(String),[...viaRpc.revoked].sort((x,y)=>x[0]-y[0]).map(([k,v])=>[k,String(v)])]);
  if(!same)throw Error('EVENT_SOURCES_DISAGREE');
  if(cached!==rebuilt)throw Error('REBUILT_VIEW_DIFFERS_FROM_THE_DRIVER_CACHE');
  return {view:viaRpc,sources:[viaRpc.source,viaScan.source],noteEvents:viaRpc.noteEvents,revocationEvents:viaRpc.revocationEvents};
}
async function shardIndex(show,family,value) {
  const name=family==='nullifier'?'nullifier_shard_index':'challenge_shard_index';
  return Number(bcs.u64().parse(await view(name,t=>[t.object(show.controlId),t.pure.u256(BigInt(value))])));
}
const baseCount=(show,spec)=>{
  const n=show.view.noteLeaves.length;
  if(!spec)return n;
  if(spec.count!==undefined)return spec.count;
  if(spec.age!==undefined)return n-spec.age;
  if(spec.current)return n;
  throw Error('UNKNOWN_ROOT_SPEC');
};

// ---- one step ------------------------------------------------------------------------------
async function runStep(world,step,record) {
  const op=step.op;
  const proofRef=op==='consume_private'?world.proofs[step.proof]:null;
  const show=world.shows[step.show??(proofRef?.showName)??(op==='prove'?world.notes[step.note]?.show:null)??world.first];
  const sender=step.sender??(op==='consume_private'?'gate':'issuer');
  const pageOf=ticket=>show.pageFor(ticket.slot);
  switch(op) {
    case 'claim_pages': {
      const r=await submitOne('issuer',t=>{t.moveCall({target:target('claim_pages'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.u64(step.from),t.pure.u64(step.count)]});});
      const o=abortOf(r);
      if(o==='ok'){for(const e of eventsOf(r,'PageClaimed',PageClaimed))show.pages[e.index]=e.page;recordGas('claim_pages',r);}
      return o;
    }
    case 'claim_shards': {
      const r=await submitOne('issuer',t=>{t.moveCall({target:target('claim_shards'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.pure.u64(step.from),t.pure.u64(step.count)]});});
      const o=abortOf(r);
      if(o==='ok')for(const e of eventsOf(r,'ShardClaimed',ShardClaimed))show.shards[e.index]=e.shard;
      return o;
    }
    case 'claim_zk': {
      const label=step.verifier??show.cfg.verifier;
      const r=await submitOne('issuer',t=>{t.moveCall({target:target('claim_zk'),
        arguments:[t.object(show.controlId),t.object(issuerCapId),t.object(verifiers[label].id)]});});
      const o=abortOf(r);
      if(o==='ok') {
        const [e]=eventsOf(r,'ZkClaimed',ZkClaimed);
        show.tree=e.note_tree;show.revocation=e.revocation;show.nullifierShards=e.nullifier_shards;show.challengeShards=e.challenge_shards;
        show.domain=BigInt(e.domain);
        // The circuit-side Poseidon (circomlibjs) must give the chain's domain (RS-C11).
        const want=await domainOf(show.controlId,P.PROFILE_VERSION,verifiers[label].manifestHash);
        if(want!==show.domain)throw Error('DOMAIN_JS_DIFFERS_FROM_CHAIN');
        // RR-5/RR-6: exactly one note tree and one aggregated revocation root per show.
        record.structure[show.name]={noteTrees:1,revocationRoots:1,nullifierShards:e.nullifier_shards.length,
          challengeShards:e.challenge_shards.length,depth:Number(e.depth),historyK:Number(e.history_k)};
        recordGas('claim_zk',r);
      }
      return o;
    }
    case 'seal':
      return abortOf(await submitOne('issuer',t=>{t.moveCall({target:target('seal'),arguments:[t.object(show.controlId),t.object(issuerCapId)]});}));
    case 'cancel_show':
      return abortOf(await submitOne('issuer',t=>{t.moveCall({target:target('cancel_show'),arguments:[t.object(show.controlId),t.object(issuerCapId)]});}));
    case 'issue': {
      const r=await submitOne('issuer',t=>{t.moveCall({target:target('issue'),
        arguments:[t.object(show.controlId),t.object(show.pageFor(step.slot)),t.object(issuerCapId),t.pure.u64(step.slot),
          t.pure.u64(step.gen),t.pure.address(addr(step.holder))]});});
      const o=abortOf(r);
      if(o==='ok')for(const m of eventsOf(r,'Issuance',Issuance)) {
        show.mints.push({ticket:m.ticket,slot:m.slot,generation:m.generation,holder:step.holder,kind:m.kind});
        if(step.label)show.labels[step.label]={id:m.ticket,slot:Number(m.slot),generation:Number(m.generation)};
      }
      return o;
    }
    case 'refund': {
      const ticket=show.labels[step.ticket];
      return abortOf(await submitOne(step.sender,t=>{t.moveCall({target:target('refund'),
        arguments:[t.object(show.controlId),t.object(pageOf(ticket)),t.object(ticket.id),t.pure.u64(step.version),t.object(CLOCK_ID)]});}));
    }
    case 'offer': {
      const ticket=show.labels[step.ticket];
      const expires=(await chainNow())+step.ttl_ms;
      return abortOf(await submitOne(step.sender,t=>{t.moveCall({target:target('offer'),
        arguments:[t.object(show.controlId),t.object(pageOf(ticket)),t.object(ticket.id),t.pure.u64(step.version),
          t.pure.address(addr(step.recipient)),t.pure.u64(step.amount),t.pure.u64(expires),t.object(CLOCK_ID)]});}));
    }
    case 'authorize': {
      const ticket=show.labels[step.ticket];
      const expires=(await chainNow())+step.ttl_ms;
      return abortOf(await submitOne(step.sender,t=>{t.moveCall({target:target('authorize_admission'),
        arguments:[t.object(show.controlId),t.object(pageOf(ticket)),t.object(ticket.id),t.pure.u64(step.version),
          t.pure.address(addr('gate')),t.pure.vector('u8',refBytes(1)),t.pure.u64(expires),t.object(CLOCK_ID)]});}));
    }
    case 'revoke_plain': {
      const ticket=show.labels[step.ticket];
      return abortOf(await submitOne('issuer',t=>{t.moveCall({target:target('revoke'),
        arguments:[t.object(show.controlId),t.object(pageOf(ticket)),t.object(issuerCapId),t.object(ticket.id)]});}));
    }
    case 'revoke': {
      // RR-2/RR-4: the issuer rebuilds the sibling path from public leaves; 'stale' sends the
      // path of the empty tree, which only matches while nothing has been revoked.
      const ticket=show.labels[step.ticket];
      const revoked=step.witness==='stale'?new Map():show.view.revoked;
      const update=await revocationUpdate(revoked,ticket.slot);
      const r=await submitOne('issuer',t=>{t.moveCall({target:target('revoke_with_root'),
        arguments:[t.object(show.controlId),t.object(pageOf(ticket)),t.object(show.revocation),t.object(issuerCapId),t.object(ticket.id),
          t.pure.u64(BigInt(update.priorRevoked)),t.pure.vector('u256',update.siblings.map(BigInt))]});});
      const o=abortOf(r);
      if(o==='ok') {
        for(const e of eventsOf(r,'RevocationLeaf',RevocationLeaf)) {
          const g=BigInt(e.generation);
          if(g>(show.view.revoked.get(Number(e.slot))??0n))show.view.revoked.set(Number(e.slot),g);
        }
        await assertCacheMatchesChain(show);
        recordGas('revoke_with_root',r);
      }
      return o;
    }
    case 'shield': {
      const ticket=show.labels[step.ticket];
      const started=Date.now();
      const domain=step.bad==='foreign_domain'?(show.domain+1n)%FR:show.domain;
      const m=await mintNote(domain,{slot:ticket.slot,generation:ticket.generation});
      timings.mintProofMs.push(Date.now()-started);
      const commitment=step.bad==='wrong_commitment'?(BigInt(m.commitment)+1n)%FR:BigInt(m.commitment);
      const r=await submitOne(step.sender,t=>{t.moveCall({target:target('shield'),
        arguments:[t.object(show.controlId),t.object(pageOf(ticket)),t.object(show.tree),t.object(ticket.id),t.pure.u64(step.version),
          t.pure.u256(commitment),t.pure.vector('u8',m.proof),t.object(verifiers[show.cfg.verifier].id),t.object(CLOCK_ID)]});});
      const o=abortOf(r);
      if(o==='ok') {
        const [added]=eventsOf(r,'NoteAdded',NoteAdded);
        if(Number(added.index)!==show.view.noteLeaves.length)throw Error('NOTE_INDEX_NOT_SEQUENTIAL');
        show.view.noteLeaves.push(BigInt(added.commitment));
        await assertCacheMatchesChain(show);
        world.notes[step.note]={...m.note,show:show.name,index:Number(added.index)};
        recordGas('shield',r);
      }
      return o;
    }
    case 'prove': {
      const note=world.notes[step.note];
      if(!note)return {client:'NOTE_NOT_ON_CHAIN'};
      let source=show.view,sourceName='driver-cache';
      if(step.source==='events') {
        // RR-4: no local cache; the witness comes from chain events only.
        const rebuilt=await eventsView(show);
        source=rebuilt.view;sourceName=rebuilt.sources.join('+');
        record.reconstructions.push({step:record.outcomes.length,note:step.note,sources:rebuilt.sources,
          noteEvents:rebuilt.noteEvents,revocationEvents:rebuilt.revocationEvents});
      }
      const count=baseCount(show,step.root);
      const ttl=step.ttl_ms??90000;
      const started=Date.now();
      try{
        const packet=await admissionProof({domain:show.domain,noteLeaves:source.noteLeaves,noteCount:count,revoked:source.revoked},
          note,addr(step.gate??'gate'),(await chainNow())+ttl,{challenge:step.challenge});
        timings.spendProofMs.push(Date.now()-started);
        world.proofs[step.label]={packet,showName:show.name,ttl,gate:step.gate??'gate',source:sourceName};
        return 'ok';
      }catch(e){
        const code=String(e.message);
        if(['PRIVATE_NOTE_REVOKED','NOTE_NOT_ON_CHAIN'].includes(code))return {client:code};
        throw e;
      }
    }
    case 'reconstruct': {
      for(const s of Object.values(world.shows)) {
        if(!s.tree)continue;
        const rebuilt=await eventsView(s);
        record.reconstructions.push({step:record.outcomes.length,show:s.name,sources:rebuilt.sources,
          noteEvents:rebuilt.noteEvents,revocationEvents:rebuilt.revocationEvents,agreeWithCache:true});
      }
      return 'ok';
    }
    case 'consume_private': {
      const {packet}=proofRef;
      let noteRoot=BigInt(packet.noteRoot);
      if(step.note_root) {
        noteRoot=step.note_root.current?BigInt((await getFields(show.tree,NoteTree)).root)
          :noteTreeOf(H,show.view.noteLeaves.slice(0,step.note_root.count)).root;
      }
      const expires=step.ttl_ms===undefined?BigInt(packet.expiresMs):BigInt((await chainNow())+step.ttl_ms);
      const ni=await shardIndex(show,'nullifier',packet.nullifier),ci=await shardIndex(show,'challenge',packet.challenge);
      const wrongN=step.wrong_shard==='nullifier'?(ni+1)%P.NULLIFIER_SHARDS:ni;
      const wrongC=step.wrong_shard==='challenge'?(ci+1)%P.CHALLENGE_SHARDS:ci;
      const verifierId=verifiers[step.verifier??show.cfg.verifier].id;
      const r=await submitOne(sender,t=>{t.moveCall({target:target('consume_private'),
        arguments:[t.object(show.controlId),t.object(show.tree),t.object(show.revocation),t.object(show.nullifierShards[wrongN]),
          t.object(show.challengeShards[wrongC]),t.object(verifierId),t.pure.u256(noteRoot),t.pure.u256(BigInt(packet.nullifier)),
          t.pure.u256(BigInt(packet.challenge)),t.pure.u64(expires),t.pure.vector('u8',packet.proof),t.object(CLOCK_ID)]});});
      const o=abortOf(r);
      if(o==='ok') {
        const [e]=eventsOf(r,'PrivateAdmission',PrivateAdmission);
        if(String(e.nullifier)!==packet.nullifier||e.gate!==addr(sender))throw Error('PRIVATE_ADMISSION_EVENT_MISMATCH');
        recordGas('consume_private',r);
      }
      return o;
    }
    default:
      return {abort:'DRIVER_UNKNOWN_OP'};
  }
}

async function snapshot(show) {
  const control=await getFields(show.controlId,ShowControl);
  const pages=[];
  for(const index of Object.keys(show.pages).map(Number).sort((x,y)=>x-y)) {
    const f=deep(await getFields(show.pages[index],InventoryPage));
    pages.push({index:f.index,start:f.start,end:f.end,mode:f.mode,generations:f.generations,occupied:f.occupied,
      issuances:f.issuances,free:f.free,reserved:f.reserved,issued:f.issued,retired:f.retired,
      delegated_to:f.delegated_to??null});
  }
  const tickets={};
  for(const m of show.mints) {
    const f=deep(await getFields(m.ticket,Ticket));
    tickets[m.ticket]={slot:f.slot,generation:f.generation,holder:actorName(f.holder),version:f.version,state:f.state,last_amount:f.last_amount};
  }
  const snap={control:{open:control.open,sealed:control.sealed,cancel_generation:Number(control.cancel_generation),
    claimed_pages:Number(control.claimed_pages),claimed_shards:Number(control.claimed_shards),claim_sequence:Number(control.claim_sequence)},pages,tickets};
  if(!show.tree) return {...snap,private:{zk_enabled:false},domain:control.domain};
  const tree=await getFields(show.tree,NoteTree),rev=await getFields(show.revocation,RevocationState);
  let nullifiers=0,challenges=0;const spread={nullifier:[],challenge:[]};
  for(const id of show.nullifierShards){const s=await getFields(id,NullifierShard);nullifiers+=Number(s.spent.size);spread.nullifier.push(Number(s.spent.size));}
  for(const id of show.challengeShards){const s=await getFields(id,ChallengeShard);challenges+=Number(s.used.size);spread.challenge.push(Number(s.used.size));}
  // Roots recomputed with circomlibjs from the public data must be the roots stored on chain.
  await assertCacheMatchesChain(show);
  return {...snap,domain:String(control.domain),private:{zk_enabled:control.domain!=='0',leaf_count:Number(tree.leaf_count),
    history_len:tree.roots.length,revocations:Number(rev.revocations),
    revoked:Object.fromEntries([...show.view.revoked].sort((x,y)=>x[0]-y[0]).map(([k,v])=>[String(k),Number(v)])),
    nullifiers,challenges},shardSpread:spread,noteRoot:String(tree.root),revocationRoot:String(rev.root),roots:tree.roots};
}

for(const scenario of scenarios) {
  const world={shows:{},notes:{},proofs:{},first:Object.keys(scenario.shows)[0]};
  for(const [name,cfg] of Object.entries(scenario.shows))world.shows[name]=await createShow(name,cfg);
  const record={name:scenario.name,controlIds:Object.fromEntries(Object.entries(world.shows).map(([n,s])=>[n,s.controlId])),
    outcomes:[],structure:{},reconstructions:[],shows:{}};
  const started=Date.now();
  for(const step of scenario.steps) {
    let outcome;
    try{
      outcome=await runStep(world,step,record);
    }catch(e){
      outcome={abort:'DRIVER_ERROR',detail:String(e?.stack??e).slice(0,2000)};
    }
    record.outcomes.push(outcome);
    // A driver fault or an unscripted result stops the run early with the step named.
    const want=step.expect??'ok';
    if(JSON.stringify(outcome)!==JSON.stringify(want)) {
      console.error('STEP_OUTCOME_DIFFERS_FROM_SCRIPT '+scenario.name+' #'+(record.outcomes.length-1)+' '+JSON.stringify(step)+' got '+JSON.stringify(outcome)+' want '+JSON.stringify(want));
      record.scriptMismatch=record.scriptMismatch??[];
      record.scriptMismatch.push({step:record.outcomes.length-1,got:outcome,want});
    }
  }
  timings.stepMs[scenario.name]=Date.now()-started;
  for(const [name,show] of Object.entries(world.shows)) {
    record.shows[name]={controlId:show.controlId,mints:show.mints,snapshot:await snapshot(show)};
  }
  report.scenarios.push(record);
}

// ---- domain separation evidence (RS-C11) -----------------------------------------------------
{
  const c=report.scenarios.find(s=>s.name==='cross_show_and_cross_manifest_proofs');
  if(c) {
    const d=name=>c.shows[name].snapshot.domain;
    report.measurements.domains={S1:d('S1'),S2:d('S2'),S3:d('S3')};
    if(new Set([d('S1'),d('S2'),d('S3')]).size!==3)throw Error('DOMAINS_NOT_DISTINCT');
  }
}
await writeFile(join(out,'private-report.json'),JSON.stringify(report,null,2)+'\n');
console.log('private-report written: '+join(out,'private-report.json'));
const bad=report.scenarios.flatMap(s=>s.scriptMismatch??[]);
await new Promise(resolve=>process.stdout.write('',resolve));
process.exit(bad.length?2:0);
