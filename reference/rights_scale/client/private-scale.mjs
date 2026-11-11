// Prover-side and witness-side code of the extended rights profile (RS-2): depth-10 trees,
// note and admission proofs, and verifier/manifest pinning. Everything a witness needs
// beyond the holder's own note is rebuilt from PUBLIC tree data (RR-4); a backup holds
// only secret, slot, generation, domain and the note's insertion index.
import {buildPoseidon} from 'circomlibjs';
import {groth16} from 'snarkjs';
import {randomBytes} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {FR,proofBytes,vkBytes,sha256,readJSON} from './zk-helpers.mjs';
import {requirePhase2Key,requirePhase2ManifestV2} from './zk-policy-v2.mjs';
import {DEPTH,MINT,SPEND} from './profile-constants.mjs';

export const artifactRoot=resolve(fileURLToPath(new URL('.',import.meta.url)),'../zk/artifacts');
let cached;
export async function poseidon(){if(!cached){const p=await buildPoseidon();cached=xs=>BigInt(p.F.toObject(p(xs.map(BigInt))));}return cached;}
function power(a,b){let n=1n;while(b){if(b&1n)n=n*a%FR;a=a*a%FR;b>>=1n;}return n;}
export function randomField(){let x=0n;while(!x)x=BigInt('0x'+randomBytes(32).toString('hex'))%FR;return x;}

/**
 * Sparse Poseidon tree: leaf index -> value, default leaf 0, node = H(left, right). The note
 * tree is the case "leaves 0..n-1 inserted in order"; the revocation tree is the case
 * "slot -> highest revoked generation". Matches the on-chain frontier insertion
 * (`tree_insert`) and sparse update (`sparse_root`) and the circuit's `Inclusion(depth)`.
 */
export class SparseTree {
  constructor(H,depth,entries=new Map()) {
    this.depth=depth;this.zeros=[0n];
    for(let l=0;l<depth;l++)this.zeros.push(H([this.zeros[l],this.zeros[l]]));
    this.levels=[new Map([...entries].map(([i,v])=>{
      if(!Number.isInteger(i)||i<0||i>=2**depth)throw Error('TREE_CAPACITY');
      return [i,BigInt(v)];
    }))];
    for(let l=0;l<depth;l++) {
      const next=new Map();
      for(const i of this.levels[l].keys()) {
        const parent=i>>1;if(next.has(parent))continue;
        next.set(parent,H([this.levels[l].get(2*parent)??this.zeros[l],this.levels[l].get(2*parent+1)??this.zeros[l]]));
      }
      this.levels.push(next);
    }
    this.root=this.levels[depth].get(0)??this.zeros[depth];
  }
  path(index) {
    if(!Number.isInteger(index)||index<0||index>=2**this.depth)throw Error('TREE_CAPACITY');
    const bits=[],siblings=[];
    for(let l=0;l<this.depth;l++){bits.push((index>>l)&1);siblings.push(this.levels[l].get((index>>l)^1)??this.zeros[l]);}
    return {root:this.root,bits,siblings};
  }
}
export const noteTreeOf=(H,leaves,depth=DEPTH)=>new SparseTree(H,depth,new Map(leaves.map((v,i)=>[i,BigInt(v)])));
export const revocationTreeOf=(H,revoked,depth=DEPTH)=>new SparseTree(H,depth,
  new Map([...revoked].map(([slot,generation])=>[Number(slot),BigInt(generation)])));

/** RS-C11: the on-chain `domain_of`. Both 32-byte inputs are read big-endian modulo FR. */
export async function domainOf(showId,profileVersion,manifestHashHex) {
  const H=await poseidon();
  return H([BigInt(showId)%FR,BigInt(profileVersion),BigInt('0x'+manifestHashHex)%FR]);
}

export async function artifacts(expectedHash) {
  const bytes=await readFile(join(artifactRoot,'manifest.json'));
  if(expectedHash && sha256(bytes)!==expectedHash)throw Error('CIRCUIT_MANIFEST_PIN_MISMATCH');
  const manifest=JSON.parse(bytes);
  requirePhase2ManifestV2(manifest);
  for(const [file,digest] of Object.entries(manifest.files)) {
    const path=resolve(artifactRoot,file);if(!path.startsWith(artifactRoot+'/'))throw Error('ARTIFACT_PATH');
    if(sha256(await readFile(path))!==digest)throw Error('CIRCUIT_ARTIFACT_HASH_MISMATCH:'+file);
  }
  for(const name of [MINT,SPEND]) {
    const key=await readJSON(join(artifactRoot,name+'.vkey.json'));
    requirePhase2Key(key,name===MINT?4:6);
    if(!vkBytes(key).equals(await readFile(join(artifactRoot,name+'.vk.bin'))))throw Error('VERIFIER_ENCODING_MISMATCH');
  }
  return {manifest,hash:sha256(bytes),mintVK:Array.from(await readFile(join(artifactRoot,MINT+'.vk.bin'))),
    spendVK:Array.from(await readFile(join(artifactRoot,SPEND+'.vk.bin')))};
}

async function prove(name,input,expectedPublic) {
  // Public mintNote/admissionProof calls must also reject legacy or mixed keys, even when
  // a caller did not explicitly invoke checkVerifier first.
  await artifacts();
  const {proof,publicSignals}=await groth16.fullProve(input,join(artifactRoot,name+'_js',name+'.wasm'),join(artifactRoot,name+'.zkey'));
  if(JSON.stringify(publicSignals)!==JSON.stringify(expectedPublic.map(String)))throw Error('CIRCUIT_PUBLIC_INPUT_LAYOUT');
  const vk=await readJSON(join(artifactRoot,name+'.vkey.json'));
  if(!await groth16.verify(vk,publicSignals,proof))throw Error('LOCAL_GROTH16_VERIFICATION_FAILED');
  return {proof:Array.from(proofBytes(proof)),publicSignals};
}
const stringify=o=>Object.fromEntries(Object.entries(o).map(([k,v])=>[k,String(v)]));

/** Shield-side: a fresh note for a ticket. `domain` is the show's on-chain domain. */
export async function mintNote(domain,ticket) {
  const H=await poseidon(),secret=randomField(),slot=BigInt(ticket.slot),generation=BigInt(ticket.generation),d=BigInt(domain);
  const commitment=H([secret,slot,generation,d,1]);
  const generated=await prove(MINT,stringify({commitment,slot,generation,domain:d,secret,inverse:power(secret,FR-2n)}),[commitment,slot,generation,d]);
  // The note is the holder's backup: no path, no root.
  return {commitment:String(commitment),proof:generated.proof,
    note:{secret:String(secret),slot:String(slot),generation:String(generation),domain:String(d),commitment:String(commitment)}};
}

/**
 * The circuit input of an admission, from PUBLIC tree data only. `tree.noteLeaves` are in
 * insertion order, `tree.noteCount` chooses which root to prove against (default: all
 * leaves, the current root), `tree.revoked` maps slot -> highest revoked generation.
 * `allowRevoked` skips the early client-side refusal so tests can show that the CIRCUIT
 * rejects a revoked note (the sole use of the flag).
 */
export async function spendWitness(tree,note,gate,expiresMs,{challenge,allowRevoked=false}={}) {
  const H=await poseidon();
  const secret=BigInt(note.secret),slot=BigInt(note.slot),generation=BigInt(note.generation),domain=BigInt(note.domain);
  if(BigInt(tree.domain)!==domain)throw Error('NOTE_DOMAIN_MISMATCH');
  const commitment=H([secret,slot,generation,domain,1]);
  if(String(commitment)!==String(note.commitment))throw Error('NOTE_COMMITMENT_MISMATCH');
  const noteCount=tree.noteCount??tree.noteLeaves.length;
  const index=tree.noteLeaves.slice(0,noteCount).findIndex(n=>BigInt(n)===commitment);if(index<0)throw Error('NOTE_NOT_ON_CHAIN');
  const revokedMax=BigInt((tree.revoked??new Map()).get(Number(slot))??0n);
  if(revokedMax>=generation && !allowRevoked)throw Error('PRIVATE_NOTE_REVOKED');
  const nullifier=H([secret,slot,generation,domain,2]);
  const np=noteTreeOf(H,tree.noteLeaves.slice(0,noteCount)).path(index);
  const rp=revocationTreeOf(H,tree.revoked??new Map()).path(Number(slot));
  const gateNumber=BigInt(gate),gateLow=gateNumber&((1n<<128n)-1n),gateHigh=gateNumber>>128n;
  const chosen=challenge===undefined?randomField():BigInt(challenge),expires=BigInt(expiresMs);
  const context=H([gateLow,gateHigh,chosen,expires,1]);
  const scalar={noteRoot:np.root,revocationRoot:rp.root,nullifier,context,domain,action:1n,secret,inverse:power(secret,FR-2n),slot,generation,
    revokedMaxGeneration:revokedMax,gateLow,gateHigh,challenge:chosen,expiresMs:expires};
  const input={...stringify(scalar),noteBits:np.bits.map(String),noteSiblings:np.siblings.map(String),revocationSiblings:rp.siblings.map(String)};
  return {input,publicSignals:[np.root,rp.root,nullifier,context,domain,1n].map(String),challenge:chosen,expires};
}

/** Builds an admission packet (see `spendWitness`) and proves it. */
export async function admissionProof(tree,note,gate,expiresMs,options={}) {
  const w=await spendWitness(tree,note,gate,expiresMs,options);
  const generated=await prove(SPEND,w.input,w.publicSignals);
  // This packet can go to a separate gate client. It contains NO note/slot/secret.
  return {noteRoot:w.publicSignals[0],revocationRoot:w.publicSignals[1],nullifier:w.publicSignals[2],challenge:String(w.challenge),
    expiresMs:String(w.expires),proof:generated.proof,publicSignals:generated.publicSignals};
}

/** Sibling path for the next `revoke_with_root`: the issuer rebuilds it from public data too. */
export async function revocationUpdate(revoked,slot) {
  const H=await poseidon();
  const before=revocationTreeOf(H,revoked),priorRevoked=BigInt(revoked.get(Number(slot))??0n);
  return {priorRevoked:String(priorRevoked),siblings:before.path(Number(slot)).siblings.map(String),rootBefore:String(before.root)};
}

/**
 * IM-27: pin the verifier object. It must be the package's own immutable `zk_gate::Verifier`
 * carrying this manifest's hash and exactly this ceremony's key bytes.
 */
export async function checkVerifier(rpc,packageId,verifierId,manifestHash) {
  const {Verifier}=await import('./types.mjs');
  const {object}=await rpc.getObject({objectId:verifierId,include:{content:true}});
  if(object.type!==packageId+'::zk_gate::Verifier' || object.owner.$kind!=='Immutable')throw Error('VERIFIER_OBJECT_PIN_MISMATCH');
  const v=Verifier.parse(object.content),a=await artifacts(manifestHash);
  if(Buffer.from(v.circuit_manifest_hash).toString('hex')!==manifestHash || sha256(Buffer.from(v.mint_vk))!==sha256(Buffer.from(a.mintVK))
    ||sha256(Buffer.from(v.spend_vk))!==sha256(Buffer.from(a.spendVK)))throw Error('VERIFIER_KEY_PIN_MISMATCH');
  return a;
}
