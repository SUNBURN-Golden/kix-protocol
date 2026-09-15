// Reproduce the archived vulnerability, then require rejection with fresh keys.
// Only public evidence and boolean results are written; never persist witnesses.
import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {resolve,join} from 'node:path';
import {groth16} from 'snarkjs';
import {FR} from './encoding.mjs';
import {requirePhase2Key,requirePhase2Manifest} from './zk-policy.mjs';
import {unpackProof,compensateInput,testCurve} from './zk-test-utils.mjs';

const here=fileURLToPath(new URL('.',import.meta.url));
const root=resolve(here,'../../..'),old=join(root,'validation/2026-09-11');
const read=async path=>JSON.parse(await readFile(path,'utf8'));
const result={baselineCommit:'2658a43aefa792ff783457188814f8598a62f5b0',checks:[]};
async function check(label,expected,key,signals,proof) {
  const actual=await groth16.verify(key,signals,proof);
  assert.equal(actual,expected,label);
  result.checks.push({check:label,accepted:actual,expected});
}
try {
  const key=await read(join(old,'spend-verification-key.json'));
  const p=await read(join(old,'private-public-inputs-and-proof.json'));
  const proof=await unpackProof(p.proof);
  assert.throws(()=>requirePhase2Key(key,6),/UNCONTRIBUTED_PHASE2_KEY/);
  const oldManifest=await read(join(old,'fixture-zk-artifact-manifest.json'));
  assert.throws(()=>requirePhase2Manifest(oldManifest),/PHASE2_CONTRIBUTION_REQUIRED/);
  await check('archived original',true,key,p.publicSignals,proof);
  for(const [index,value,label] of [[2,(BigInt(p.nullifier)+1n)%FR,'nullifier'],[5,2n,'forbidden action']]) {
    const forged=await compensateInput(key,proof,p.publicSignals,index,value);
    await check('archived input-only '+label,false,key,forged.publicSignals,proof);
    await check('archived compensated '+label,true,key,forged.publicSignals,forged.proof);
  }
  if(!process.argv.includes('--baseline-only')) {
    const {artifacts,mintNote,admissionProof}=await import('./private.mjs');
    const a=await artifacts();result.artifactManifestHash=a.hash;
    const show={open:true,domain:'7',generations:Array(16).fill('0'),notes:[],nullifiers:[]};
    show.generations[0]='1';
    const m=await mintNote(show,{slot:'0',generation:'1'});show.notes.push(m.commitment);
    const p=await admissionProof(show,m.note,'0x1',String(Date.now()+90000));
    for(const [name,bytes,signals] of [
      ['mint',m.proof,[m.commitment,'0','1','7']],['spend',p.proof,p.publicSignals],
    ]) {
      const key=await read(resolve(here,'../zk/artifacts',name+'.vkey.json'));
      const proof=await unpackProof(bytes);
      await check('contributed '+name+' original',true,key,signals,proof);
      for(let index=0;index<signals.length;index++) {
        const forged=await compensateInput(key,proof,signals,index,(BigInt(signals[index])+1n)%FR);
        await check('contributed '+name+' input-only '+index,false,key,forged.publicSignals,proof);
        await check('contributed '+name+' compensated '+index,false,key,forged.publicSignals,forged.proof);
      }
    }
  }
  result.status='PASSED';result.scope=process.argv.includes('--baseline-only')?'ARCHIVED_REPRODUCTION_ONLY':'ARCHIVED_AND_FRESH_KEYS';
  const out=join(root,'.local/verification');await mkdir(out,{recursive:true});
  await writeFile(join(out,process.argv.includes('--baseline-only')?'zk-baseline.json':'zk-regression.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
} finally {
  await (await testCurve()).terminate();
}
// circomlibjs/snarkjs may retain workers from another curve instance. All
// verification and result writes are awaited before ending this CLI process.
await new Promise(resolve=>process.stdout.write('',resolve));
process.exit(0);
