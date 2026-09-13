import {buildPoseidon} from 'circomlibjs';
import {groth16} from 'snarkjs';
import {randomBytes} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {FR,proofBytes,vkBytes} from './encoding.mjs';
import {sha256,readJSON} from './backup.mjs';
import {requirePhase2Key,requirePhase2Manifest} from './zk-policy.mjs';
const root=resolve(fileURLToPath(new URL('.',import.meta.url)),'../zk/artifacts');
let cached;
async function hash(){if(!cached){const p=await buildPoseidon();cached=xs=>BigInt(p.F.toObject(p(xs.map(BigInt))));}return cached;}
function power(a,b){let n=1n;while(b){if(b&1n)n=n*a%FR;a=a*a%FR;b>>=1n;}return n;}
function randomField(){let x=0n;while(!x)x=BigInt('0x'+randomBytes(32).toString('hex'))%FR;return x;}
export async function artifacts(expectedHash) {
  const bytes=await readFile(join(root,'manifest.json'));
  if(expectedHash && sha256(bytes)!==expectedHash)throw Error('CIRCUIT_MANIFEST_PIN_MISMATCH');
  const manifest=JSON.parse(bytes);
  requirePhase2Manifest(manifest);
  for(const [file,digest] of Object.entries(manifest.files)) {
    const path=resolve(root,file);if(!path.startsWith(root+'/'))throw Error('ARTIFACT_PATH');
    if(sha256(await readFile(path))!==digest)throw Error('CIRCUIT_ARTIFACT_HASH_MISMATCH:'+file);
  }
  for(const name of ['mint','spend']) {
    const key=await readJSON(join(root,name+'.vkey.json'));
    requirePhase2Key(key,name==='mint'?4:6);
    if(!vkBytes(key).equals(await readFile(join(root,name+'.vk.bin'))))throw Error('VERIFIER_ENCODING_MISMATCH');
  }
  return {manifest,hash:sha256(bytes),mintVK:Array.from(await readFile(join(root,'mint.vk.bin'))),spendVK:Array.from(await readFile(join(root,'spend.vk.bin')))};
}
async function prove(name,input,expectedPublic) {
  // Public mintNote/admissionProof calls must also reject legacy or mixed keys,
  // even when a caller did not explicitly invoke checkVerifier first.
  await artifacts();
  const {proof,publicSignals}=await groth16.fullProve(input,join(root,name+'_js',name+'.wasm'),join(root,name+'.zkey'));
  if(JSON.stringify(publicSignals)!==JSON.stringify(expectedPublic.map(String)))throw Error('CIRCUIT_PUBLIC_INPUT_LAYOUT');
  const vk=await readJSON(join(root,name+'.vkey.json'));
  if(!await groth16.verify(vk,publicSignals,proof))throw Error('LOCAL_GROTH16_VERIFICATION_FAILED');
  return {proof:Array.from(proofBytes(proof)),publicSignals};
}
export async function mintNote(show,ticket) {
  const H=await hash(),secret=randomField(),slot=BigInt(ticket.slot),generation=BigInt(ticket.generation),domain=BigInt(show.domain);
  const commitment=H([secret,slot,generation,domain,1]);
  const input=Object.fromEntries(Object.entries({commitment,slot,generation,domain,secret,inverse:power(secret,FR-2n)}).map(([k,v])=>[k,String(v)]));
  const generated=await prove('mint',input,[commitment,slot,generation,domain]);
  return {commitment:String(commitment),proof:generated.proof,note:{secret:String(secret),slot:String(slot),generation:String(generation),domain:String(domain),commitment:String(commitment)}};
}
function pathFor(H,original,index) {
  const leaves=original.map(BigInt);while(leaves.length<16)leaves.push(0n);
  if(leaves.length!==16 || index<0 || index>=16)throw Error('TREE_CAPACITY');
  let row=leaves,pos=index;const bits=[],siblings=[];
  while(row.length>1){bits.push(pos&1);siblings.push(row[pos^1]);const next=[];for(let i=0;i<row.length;i+=2)next.push(H([row[i],row[i+1]]));row=next;pos>>=1;}
  return {root:row[0],bits,siblings};
}
export async function admissionProof(show,note,gate,expiresMs) {
  const H=await hash();const secret=BigInt(note.secret),slot=BigInt(note.slot),generation=BigInt(note.generation),domain=BigInt(note.domain);
  if(!show.open || BigInt(show.domain)!==domain || BigInt(show.generations[Number(slot)])!==generation)throw Error('PRIVATE_NOTE_REVOKED');
  const commitment=H([secret,slot,generation,domain,1]);
  const index=show.notes.findIndex(n=>BigInt(n)===commitment);if(index<0)throw Error('NOTE_NOT_ON_CHAIN');
  const nullifier=H([secret,slot,generation,domain,2]);
  if(show.nullifiers.some(n=>BigInt(n)===nullifier))throw Error('NOTE_ALREADY_SPENT');
  const np=pathFor(H,show.notes,index),rp=pathFor(H,show.generations.map((g,i)=>H([i,g,domain,3])),Number(slot));
  const gateNumber=BigInt(gate),gateLow=gateNumber&((1n<<128n)-1n),gateHigh=gateNumber>>128n;
  const challenge=randomField(),context=H([gateLow,gateHigh,challenge,expiresMs,1]);
  const scalar={noteRoot:np.root,revocationRoot:rp.root,nullifier,context,domain,action:1n,secret,inverse:power(secret,FR-2n),slot,generation,
    gateLow,gateHigh,challenge,expiresMs};
  const input={...Object.fromEntries(Object.entries(scalar).map(([k,v])=>[k,String(v)])),noteBits:np.bits.map(String),noteSiblings:np.siblings.map(String),revocationSiblings:rp.siblings.map(String)};
  const generated=await prove('spend',input,[np.root,rp.root,nullifier,context,domain,1]);
  // This packet can go to a separate gate client. It contains NO note/slot/secret.
  return {nullifier:String(nullifier),challenge:String(challenge),expiresMs:String(expiresMs),proof:generated.proof,publicSignals:generated.publicSignals};
}

export async function checkVerifier(client,verifierId,manifestHash) {
  const {Verifier}=await import('./types.mjs');
  const {object}=await client.rpc.getObject({objectId:verifierId,include:{content:true}});
  if(object.type!==client.packageId+'::zk_gate::Verifier' || object.owner.$kind!=='Immutable')throw Error('VERIFIER_OBJECT_PIN_MISMATCH');
  const v=Verifier.parse(object.content),a=await artifacts(manifestHash);
  if(Buffer.from(v.circuit_manifest_hash).toString('hex')!==manifestHash || sha256(Buffer.from(v.mint_vk))!==sha256(Buffer.from(a.mintVK))
    ||sha256(Buffer.from(v.spend_vk))!==sha256(Buffer.from(a.spendVK)))throw Error('VERIFIER_KEY_PIN_MISMATCH');
  return a;
}
