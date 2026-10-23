// Extended-profile ZK regression (RS-2). Reproduces the known uncontributed-phase-2 forgery on
// the NEW circuit's keys, then requires rejection with the freshly contributed keys, checks the
// manifest-v2 policy, and shows that the depth-10 spend circuit refuses every witness that
// breaks RR-1..RR-3 or a range check. Only public evidence and booleans are written; witnesses
// are never persisted. The reference profile's own regression (reference/v0.3-rc1) is separate.
import assert from 'node:assert/strict';
import {mkdir,writeFile,copyFile,rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,join} from 'node:path';
import {groth16,zKey} from 'snarkjs';
import {FR,readJSON} from './zk-helpers.mjs';
import {requirePhase2Key,requirePhase2ManifestV2} from './zk-policy-v2.mjs';
import {unpackProof,compensateInput,testCurve} from './zk-test-utils.mjs';
import {artifacts,artifactRoot,mintNote,admissionProof,spendWitness,poseidon,noteTreeOf,revocationTreeOf} from './private-scale.mjs';
import {DEPTH,MINT,SPEND} from './profile-constants.mjs';

const here=fileURLToPath(new URL('.',import.meta.url));
const root=resolve(here,'../../..');
const result={checks:[]};
const record=(check,expected,actual)=>{assert.equal(actual,expected,check);result.checks.push({check,expected,actual});};
const quiet={debug(){},info(){},warn(){},error(){}};
async function throwsWith(label,pattern,fn) {
  try{await fn();}catch(e){assert.match(String(e?.message??e),pattern,label);result.checks.push({check:label,rejected:true});return;}
  assert.fail('EXPECTED_REJECTION:'+label);
}
async function verifies(label,expected,key,signals,proof) {
  record(label,expected,await groth16.verify(key,signals,proof));
}

try {
  const a=await artifacts();result.artifactManifestHash=a.hash;
  result.constraints=a.manifest.constraints;result.ptauPower=a.manifest.phase1.ptauPower;result.phase1=a.manifest.phase1.source;

  // ---- 1. Manifest v2 policy: wrong schema, depth, profile, missing records are refused.
  const good=structuredClone(a.manifest);
  requirePhase2ManifestV2(good);
  await throwsWith('v1 manifest refused',/CIRCUIT_MANIFEST_FORMAT/,()=>requirePhase2ManifestV2({...good,format:'kix-zk-artifacts-v1'}));
  await throwsWith('depth-4 manifest refused',/CIRCUIT_MANIFEST_DEPTH/,()=>requirePhase2ManifestV2({...good,depth:4}));
  await throwsWith('slotBits mismatch refused',/CIRCUIT_MANIFEST_SLOTBITS/,()=>requirePhase2ManifestV2({...good,slotBits:4}));
  await throwsWith('other profile version refused',/CIRCUIT_MANIFEST_PROFILEVERSION/,()=>requirePhase2ManifestV2({...good,profileVersion:2}));
  await throwsWith('missing K refused',/ROOT_HISTORY_K/,()=>requirePhase2ManifestV2({...good,rootHistoryK:undefined}));
  await throwsWith('missing phase-1 record refused',/PHASE1_RECORD_MISSING/,()=>requirePhase2ManifestV2({...good,phase1:undefined}));
  await throwsWith('missing phase-2 contribution refused',/PHASE2_CONTRIBUTION_REQUIRED/,()=>requirePhase2ManifestV2({...good,phase2Contributions:{[MINT]:1,[SPEND]:0}}));
  await throwsWith('ptau too small for the circuit refused',/PTAU_POWER_TOO_SMALL/,()=>requirePhase2ManifestV2({...good,phase1:{...good.phase1,ptauPower:13}}));
  await throwsWith('missing artifact hash refused',/MISSING_ARTIFACT_HASH/,()=>{const m=structuredClone(good);delete m.files['spend_scale.zkey'];requirePhase2ManifestV2(m);});
  await throwsWith('K pin mismatch refused',/ROOT_HISTORY_K/,()=>requirePhase2ManifestV2(good,{rootHistoryK:good.rootHistoryK+1}));

  // ---- 2. The archived vulnerability, reproduced on this circuit: a key whose phase 2 was
  // never contributed accepts compensated forgeries; the policy refuses to install it.
  const H=await poseidon();
  const domain='7';
  const tree={domain,noteLeaves:[],revoked:new Map([[3,2n]])};
  const m=await mintNote(domain,{slot:'0',generation:'1'});tree.noteLeaves.push(BigInt(m.commitment));
  const gate='0x1234';const expires=String(Date.now()+90000);
  const spend=await admissionProof(tree,m.note,gate,expires);
  {
    const scratch=join(root,'.local/zk-regression');await mkdir(scratch,{recursive:true});
    const bad=join(scratch,'mint_scale.uncontributed.zkey');
    await zKey.newZKey(join(artifactRoot,MINT+'.r1cs'),join(artifactRoot,'pot-final.ptau'),bad,quiet);
    const weak=await zKey.exportVerificationKey(bad,quiet);
    await throwsWith('uncontributed phase-2 key refused',/UNCONTRIBUTED_PHASE2_KEY/,()=>requirePhase2Key(weak,4));
    const {proof,publicSignals}=await groth16.fullProve({commitment:m.commitment,slot:'0',generation:'1',domain,
      secret:m.note.secret,inverse:String(modInverse(BigInt(m.note.secret)))},join(artifactRoot,MINT+'_js',MINT+'.wasm'),bad);
    await verifies('uncontributed mint original',true,weak,publicSignals,proof);
    const forged=await compensateInput(weak,proof,publicSignals,3,(BigInt(publicSignals[3])+1n)%FR);
    await verifies('uncontributed mint input-only forgery',false,weak,forged.publicSignals,proof);
    await verifies('uncontributed mint compensated forgery ACCEPTED (the vulnerability)',true,weak,forged.publicSignals,forged.proof);
    await rm(scratch,{recursive:true,force:true});
  }

  // ---- 3. Contributed keys: every single-input change is rejected, compensated or not.
  for(const [name,bytes,signals] of [
    [MINT,m.proof,[m.commitment,'0','1',domain]],[SPEND,spend.proof,spend.publicSignals],
  ]) {
    const key=await readJSON(join(artifactRoot,name+'.vkey.json'));
    requirePhase2Key(key,signals.length);
    const proof=await unpackProof(bytes);
    await verifies('contributed '+name+' original',true,key,signals,proof);
    for(let index=0;index<signals.length;index++) {
      const forged=await compensateInput(key,proof,signals,index,(BigInt(signals[index])+1n)%FR);
      await verifies('contributed '+name+' input-only '+index,false,key,forged.publicSignals,proof);
      await verifies('contributed '+name+' compensated '+index,false,key,forged.publicSignals,forged.proof);
    }
  }

  // ---- 4. The spend circuit refuses witnesses that break the root rules.
  // circom prints an "Error in template" diagnostic for every witness it refuses; each one below is expected.
  console.log('Section 4 expects circom assertion diagnostics on stderr: one per refused witness.');
  const full=async(input)=>groth16.fullProve(input,join(artifactRoot,SPEND+'_js',SPEND+'.wasm'),join(artifactRoot,SPEND+'.zkey'));
  const witness=async(t,note,opts)=>(await spendWitness(t,note,gate,expires,opts)).input;
  const second=await mintNote(domain,{slot:'3',generation:'2'});
  const view={domain,noteLeaves:[BigInt(m.commitment),BigInt(second.commitment)],revoked:new Map([[3,2n]])};
  // RR-2: slot 3 was revoked at generation 2, so a note of generation 2 on it has no witness.
  await throwsWith('RR-2 revoked generation == note generation',/Assert Failed/,async()=>full(await witness(view,second.note,{allowRevoked:true})));
  await throwsWith('RR-2 client refuses a revoked note first',/PRIVATE_NOTE_REVOKED/,async()=>witness(view,second.note));
  const newer=await mintNote(domain,{slot:'3',generation:'3'});
  const view2={domain,noteLeaves:[BigInt(m.commitment),BigInt(second.commitment),BigInt(newer.commitment)],revoked:new Map([[3,2n]])};
  record('RR-2 a newer generation on a revoked slot is provable',true,(await full(await witness(view2,newer.note))).publicSignals.length===6);
  const base=await witness(view2,newer.note);
  const mutate=(changes)=>({...base,...changes});
  await throwsWith('RR-2 revoked leaf lowered without changing the root',/Assert Failed/,()=>full(mutate({revokedMaxGeneration:'1'})));
  await throwsWith('RR-2 revocation path of another slot',/Assert Failed/,async()=>{
    const other=revocationTreeOf(H,view2.revoked).path(4);return full(mutate({revocationSiblings:other.siblings.map(String)}));});
  await throwsWith('RR-1 note not in the tree (wrong note root)',/Assert Failed/,()=>full(mutate({noteRoot:'12345'})));
  await throwsWith('RR-1 note path with a wrong sibling',/Assert Failed/,()=>full(mutate({noteSiblings:base.noteSiblings.map((v,i)=>i===2?'1':v)})));
  await throwsWith('RR-3 revocation root other than the tree root',/Assert Failed/,()=>full(mutate({revocationRoot:'12345'})));
  await throwsWith('action other than admission',/Assert Failed/,()=>full(mutate({action:'2'})));
  await throwsWith('nullifier not derived from the note',/Assert Failed/,()=>full(mutate({nullifier:'12345'})));
  await throwsWith('context not bound to the gate and challenge',/Assert Failed/,()=>full(mutate({challenge:String(BigInt(base.challenge)+1n)})));
  await throwsWith('domain of another show or profile',/Assert Failed/,()=>full(mutate({domain:'8'})));
  await throwsWith('slot outside the 10-bit range',/Assert Failed/,()=>full(mutate({slot:'1024'})));
  await throwsWith('generation outside 64 bits',/Assert Failed/,()=>full(mutate({generation:String(2n**64n)})));
  await throwsWith('zero secret',/Assert Failed/,()=>full(mutate({secret:'0'})));
  await throwsWith('note bit that is not binary',/Assert Failed/,()=>full(mutate({noteBits:base.noteBits.map((v,i)=>i===0?'2':v)})));
  // The mint circuit has the same slot range and note binding.
  const mintFull=input=>groth16.fullProve(input,join(artifactRoot,MINT+'_js',MINT+'.wasm'),join(artifactRoot,MINT+'.zkey'));
  const mintInput={commitment:m.commitment,slot:'0',generation:'1',domain,secret:m.note.secret,inverse:String(modInverse(BigInt(m.note.secret)))};
  await throwsWith('mint: slot outside the 10-bit range',/Assert Failed/,()=>mintFull({...mintInput,slot:'1024'}));
  await throwsWith('mint: commitment of another domain',/Assert Failed/,()=>mintFull({...mintInput,domain:'8'}));

  result.status='PASSED';
  result.scope='MANIFEST_V2_POLICY_UNCONTRIBUTED_REPRODUCTION_FRESH_KEYS_AND_ROOT_RULE_WITNESSES';
  const out=join(root,'.local/verification');await mkdir(out,{recursive:true});
  await writeFile(join(out,'zk-regression-scale.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({status:result.status,checks:result.checks.length,constraints:result.constraints,ptauPower:result.ptauPower},null,2));
} finally {
  await (await testCurve()).terminate();
}
function modInverse(a){let n=1n,b=FR-2n;a%=FR;while(b){if(b&1n)n=n*a%FR;a=a*a%FR;b>>=1n;}return n;}
// circomlibjs/snarkjs may retain workers from another curve instance. All
// verification and result writes are awaited before ending this CLI process.
await new Promise(resolve=>process.stdout.write('',resolve));
process.exit(0);
