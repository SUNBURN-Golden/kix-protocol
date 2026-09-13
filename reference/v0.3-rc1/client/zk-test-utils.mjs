// Adversarial-test helpers only. Never used to accept a holder's proof.
import assert from 'node:assert/strict';
import {curves} from 'snarkjs';
import {FR,proofBytes} from './encoding.mjs';

export const testCurve=()=>curves.getCurveFromName('bn128');
const json=value=>JSON.parse(JSON.stringify(value,(_,v)=>typeof v==='bigint'?v.toString():v));
const big=value=>Array.isArray(value)?value.map(big):BigInt(value);
const little=bytes=>BigInt('0x'+Buffer.from(bytes).reverse().toString('hex'));

function decompress(group,bytes) {
  const b=Buffer.from(bytes),negative=!!(b[b.length-1]&128);
  assert.equal(b[b.length-1]&64,0,'fixture point must not be infinity');
  b[b.length-1]&=63;
  const F=group.F;
  const x=F.fromObject(b.length===32?little(b):[little(b.subarray(0,32)),little(b.subarray(32))]);
  const rhs=F.add(F.mul(F.square(x),x),group.b);
  assert.ok(F.isSquare(rhs),'fixture point must be on curve');
  let y=F.sqrt(rhs);
  const a=[F.toObject(y)].flat(),n=[F.toObject(F.neg(y))].flat();
  let greater=false;
  for(let i=a.length-1;i>=0;i--)if(a[i]!==n[i]){greater=a[i]>n[i];break;}
  if(greater!==negative)y=F.neg(y);
  return group.fromObject([F.toObject(x),F.toObject(y),F.toObject(F.one)]);
}

export async function unpackProof(bytes) {
  assert.equal(bytes.length,128);
  const c=await testCurve(),b=Buffer.from(bytes);
  const proof=json({protocol:'groth16',curve:'bn128',
    pi_a:c.G1.toObject(decompress(c.G1,b.subarray(0,32))),
    pi_b:c.G2.toObject(decompress(c.G2,b.subarray(32,96))),
    pi_c:c.G1.toObject(decompress(c.G1,b.subarray(96,128)))});
  assert.deepEqual(proofBytes(proof),b,'Arkworks fixture round trip');
  return proof;
}

export async function compensateInput(key,proof,signals,index,value) {
  const c=await testCurve();
  const change=(BigInt(value)-BigInt(signals[index])+FR)%FR;
  const correction=c.G1.timesScalar(c.G1.fromObject(big(key.IC[index+1])),change);
  const adjusted=c.G1.toAffine(c.G1.add(c.G1.fromObject(big(proof.pi_c)),c.G1.neg(correction)));
  const publicSignals=[...signals];publicSignals[index]=String(value);
  return {proof:json({...proof,pi_c:c.G1.toObject(adjusted)}),publicSignals};
}

export async function compensateNullifier(presentation,key) {
  const next=(BigInt(presentation.nullifier)%(FR-1n))+1n;
  const result=await compensateInput(key,await unpackProof(presentation.proof),presentation.publicSignals,2,next);
  return {...presentation,nullifier:String(next),publicSignals:result.publicSignals,proof:Array.from(proofBytes(result.proof))};
}
