// Regenerates the known-answer constants embedded in sui/tests/root_math_tests.move with
// circomlibjs (the circuit-side Poseidon). Prints Move constants; commit the result by hand.
// `node gen-move-vectors.mjs --check` fails when the committed test file disagrees.
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {poseidon,SparseTree,domainOf} from './private-scale.mjs';

const H=await poseidon();
const out={};
const empty=new SparseTree(H,10);
out.ZERO_1=empty.zeros[1];out.ZERO_2=empty.zeros[2];out.ZERO_9=empty.zeros[9];out.EMPTY_ROOT_10=empty.zeros[10];
// Depth 3, three leaves 11,22,33 (small enough to check by hand).
const small=new SparseTree(H,3,new Map([[0,11n],[1,22n],[2,33n]]));
out.ROOT_3_AFTER_1=new SparseTree(H,3,new Map([[0,11n]])).root;
out.ROOT_3_AFTER_2=new SparseTree(H,3,new Map([[0,11n],[1,22n]])).root;
out.ROOT_3_AFTER_3=small.root;
// Depth 10, leaves 101..105: root after each insert.
for(let n=1;n<=5;n++)out['ROOT_10_AFTER_'+n]=new SparseTree(H,10,new Map(Array.from({length:n},(_,i)=>[i,BigInt(101+i)]))).root;
// Sparse revocation: slot 5 revoked at generation 3, then slot 700 at generation 9.
const revoke5=new SparseTree(H,10,new Map([[5,3n]]));
const revoke5b=new SparseTree(H,10,new Map([[5,3n],[700,9n]]));
out.REV_ROOT_SLOT5_GEN3=revoke5.root;
out.REV_ROOT_SLOT5_GEN3_SLOT700_GEN9=revoke5b.root;
// Sibling path the issuer would send to revoke slot 700 after slot 5.
out.REV_SIBLINGS_700=revoke5.path(700).siblings;
out.REV_SIBLINGS_5=empty.path(5).siblings;
// The same shapes with the generations the Move scenarios really revoke (first issue = generation 1).
const g1=new SparseTree(H,10,new Map([[5,1n]]));
out.REV_ROOT_SLOT5_GEN1=g1.root;
out.REV_ROOT_SLOT5_GEN1_SLOT6_GEN1=new SparseTree(H,10,new Map([[5,1n],[6,1n]])).root;
out.REV_SIBLINGS_6_AFTER_5=g1.path(6).siblings;
// Domain known answers.
out.DOMAIN_SHOW_0xA_V1=await domainOf('0xa',1,'11'.repeat(32));
out.DOMAIN_SHOW_0xA_V2=await domainOf('0xa',2,'11'.repeat(32));
out.DOMAIN_SHOW_0xB_V1=await domainOf('0xb',1,'11'.repeat(32));
out.DOMAIN_SHOW_0xA_V1_OTHER_HASH=await domainOf('0xa',1,'22'.repeat(32));
const entries=Object.entries(out).map(([k,v])=>[k,Array.isArray(v)?v.map(String):String(v)]);
const text=JSON.stringify(Object.fromEntries(entries),null,1);
if(process.argv.includes('--check')) {
  const file=await readFile(resolve(fileURLToPath(new URL('.',import.meta.url)),'../sui/tests/root_math_tests.move'),'utf8');
  const missing=[];
  for(const [k,v] of entries) for(const x of (Array.isArray(v)?v:[v])) if(!file.includes(x))missing.push(k+'='+x);
  if(missing.length){console.error('MOVE_VECTORS_OUT_OF_DATE',missing);process.exit(1);}
  console.log('Move known-answer constants match circomlibjs: '+entries.length+' vectors');
} else console.log(text);
process.exit(0);
