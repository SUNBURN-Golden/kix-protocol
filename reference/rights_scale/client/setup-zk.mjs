// LOCAL FIXTURE CEREMONY ONLY. Single party, not an operational or audited trusted setup.
// Builds the depth-10 extended-profile circuits, contributes a fresh phase 2 for each, and
// writes manifest v2 (docs/contracts/RIGHTS_SCALE_PROFILE.md IM-16, IM-17).
import {execFileSync} from 'node:child_process';
import {randomBytes} from 'node:crypto';
import {copyFile,mkdir,readFile,writeFile,rm} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {r1cs} from 'snarkjs';
import {vkBytes,sha256,durableJSON,ptauPower} from './zk-helpers.mjs';
import {compileCircuits,CIRCUITS,CIRCUIT_SOURCES} from './compile-circuits.mjs';
import {requirePhase2Key,requirePhase2ManifestV2,MANIFEST_FORMAT} from './zk-policy-v2.mjs';
import {DEPTH,SLOT_BITS,PROFILE_VERSION,ROOT_HISTORY_K,MINT,SPEND,MINT_PUBLIC,SPEND_PUBLIC} from './profile-constants.mjs';
const here=fileURLToPath(new URL('.',import.meta.url));
const out=resolve(here,'../zk/artifacts');await mkdir(out,{recursive:true});
// An interrupted setup must not leave an old manifest advertising mixed keys.
await rm(join(out,'manifest.json'),{force:true});
const bin=n=>join(here,'node_modules/.bin',n);
const run=(cmd,args)=>execFileSync(bin(cmd),args,{cwd:here,stdio:'inherit',timeout:600000});
await compileCircuits();
// The ceremony power is chosen from the recounted constraints, not copied from the
// reference profile: groth16 setup needs constraints + public inputs + 1 <= 2^power.
const constraints={},publicCount={[MINT]:MINT_PUBLIC.length,[SPEND]:SPEND_PUBLIC.length};
const quiet={debug(){},info(){},warn(){},error(){}};
for(const name of CIRCUITS)constraints[name]=(await r1cs.info(join(out,name+'.r1cs'),quiet)).nConstraints;
// The smallest power the larger circuit needs, but never below 14: the reference profile's
// phase-1 file (power 14) is what CI caches, and the depth-10 circuit fits it with room to spare.
const need=Math.max(...CIRCUITS.map(name=>Math.ceil(Math.log2(constraints[name]+publicCount[name]+1))));
const POWER=Math.max(14,need);
// Phase 1 is circuit-independent and dominates setup time. CI may pass a phase-1
// file it generated earlier; phase 2 below is always freshly contributed. A cached file
// whose power is too small for these circuits is ignored and a fresh phase 1 is made.
let cachedPhase1=process.env.KIX_ZK_PHASE1_PTAU;
if(cachedPhase1 && ptauPower(await readFile(resolve(cachedPhase1)))<POWER) {
  console.log('Cached phase 1 is below power '+POWER+'; generating a fresh one.');
  cachedPhase1=undefined;
}
if(cachedPhase1) {
  await copyFile(resolve(cachedPhase1),join(out,'pot-final.ptau'));
} else {
  run('snarkjs',['powersoftau','new','bn128',String(POWER),join(out,'pot-initial.ptau')]);
  run('snarkjs',['powersoftau','contribute',join(out,'pot-initial.ptau'),join(out,'pot-one.ptau'),'--name=KIX-single-party-local-fixture','-e='+randomBytes(64).toString('hex')]);
  run('snarkjs',['powersoftau','prepare','phase2',join(out,'pot-one.ptau'),join(out,'pot-final.ptau')]);
}
const ptau=await readFile(join(out,'pot-final.ptau'));
const power=ptauPower(ptau);
for(const name of CIRCUITS)if(constraints[name]+publicCount[name]+1>2**power)throw Error('PTAU_POWER_TOO_SMALL:'+name+':power'+power);
const phase1={source:cachedPhase1?'REUSED_CACHED_LOCAL_FIXTURE':'FRESH_SINGLE_PARTY_LOCAL_FIXTURE',
  ptauSha256:sha256(ptau),ptauPower:power};
const files={};
for(const name of CIRCUITS) {
  const initial=join(out,name+'.initial.zkey');
  run('snarkjs',['groth16','setup',join(out,name+'.r1cs'),join(out,'pot-final.ptau'),initial]);
  // Powers of Tau contribution does not replace this circuit-specific phase.
  run('snarkjs',['zkey','contribute',initial,join(out,name+'.zkey'),
    '--name=KIX-single-party-local-fixture-'+name,'-e='+randomBytes(64).toString('hex')]);
  run('snarkjs',['zkey','verify',join(out,name+'.r1cs'),join(out,'pot-final.ptau'),join(out,name+'.zkey')]);
  run('snarkjs',['zkey','export','verificationkey',join(out,name+'.zkey'),join(out,name+'.vkey.json')]);
  const v=JSON.parse(await readFile(join(out,name+'.vkey.json'),'utf8'));
  requirePhase2Key(v,publicCount[name]);
  await rm(initial);
  await writeFile(join(out,name+'.vk.bin'),vkBytes(v));
  for(const file of [name+'.r1cs',name+'.zkey',name+'.vkey.json',name+'.vk.bin',name+'_js/'+name+'.wasm'])files[file]=sha256(await readFile(join(out,file)));
}
const circuits={};for(const name of CIRCUIT_SOURCES)circuits[name+'.circom']=sha256(await readFile(resolve(here,'../zk/circuits',name+'.circom')));
const manifest={format:MANIFEST_FORMAT,setup:'INSECURE_SINGLE_PARTY_LOCAL_FIXTURE',curve:'BN254',depth:DEPTH,slotBits:SLOT_BITS,
  profileVersion:PROFILE_VERSION,rootHistoryK:ROOT_HISTORY_K,phase1,phase2Contributions:{[MINT]:1,[SPEND]:1},constraints,
  publicInputs:{[MINT]:MINT_PUBLIC,[SPEND]:SPEND_PUBLIC},circuits,files,suiSerializationVerified:false};
requirePhase2ManifestV2(manifest);
await durableJSON(join(out,'manifest.json'),manifest);
console.log('Fixture artifacts generated: '+JSON.stringify({constraints,ptauPower:power,phase1:phase1.source}));
console.log('Actual Sui acceptance and negative proof tests remain required. This is not an operational ceremony.');
// snarkjs/ffjavascript can retain worker threads after awaited work (r1cs.info starts a
// curve). Every durable write above is awaited; flush stdout before ending the CLI.
await new Promise(resolve=>process.stdout.write('',resolve));
process.exit(0);
