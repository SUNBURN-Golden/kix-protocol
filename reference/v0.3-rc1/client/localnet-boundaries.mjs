// Actual on-chain negative tests, called only by the localhost-only runner.
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {readFile} from 'node:fs/promises';
import {mintNote,admissionProof} from './private.mjs';
import {compensateNullifier} from './zk-test-utils.mjs';

export async function privateBoundaries({issuer,holder,gate,verifierId,changedId,rejection}) {
  const created=await issuer.call('create_show',t=>[t.pure.u64(3),t.pure.vector('address',[gate.keypair.toSuiAddress()]),
    t.pure.vector('address',[issuer.keypair.toSuiAddress()]),t.pure.u64(150000),t.pure.u64(200),t.pure.u64(300),t.pure.address(verifierId)]);
  const showId=changedId(created,'::rights::Show'),cap=changedId(created,'::rights::IssuerCap');
  const tickets=[],notes=[];
  for(let slot=0;slot<3;slot++) {
    const issued=await issuer.call('issue',t=>[t.object(showId),t.object(cap),t.pure.u64(slot),t.pure.address(holder.keypair.toSuiAddress())]);
    const id=changedId(issued,'::rights::Ticket');tickets.push(id);
    const state=await holder.right(showId,id),m=await mintNote(state.show,state.ticket);notes.push(m.note);
    await holder.call('shield',t=>[t.object(showId),t.object(id),t.pure.u64(1),t.pure.u256(m.commitment),
      t.pure.vector('u8',m.proof),t.object(verifierId),t.object('0x6')]);
  }
  const state=async()=> (await holder.right(showId,tickets[0])).show;
  const proof=async note=>admissionProof(await state(),note,gate.keypair.toSuiAddress(),(await holder.now())+119000n);
  const consume=p=>gate.call('consume_private',t=>[t.object(showId),t.object(verifierId),t.pure.u256(p.nullifier),
    t.pure.u256(p.challenge),t.pure.u64(p.expiresMs),t.pure.vector('u8',p.proof),t.object('0x6')]);
  const revokedProof=await proof(notes[0]),survivorOldProof=await proof(notes[1]);
  const key=JSON.parse(await readFile(fileURLToPath(new URL('../zk/artifacts/spend.vkey.json',import.meta.url)),'utf8'));
  const forged=await compensateNullifier(revokedProof,key);
  const compensated=await rejection(()=>consume(forged),'compensated nullifier','zk_gate',2);
  const revoked=await issuer.call('revoke',t=>[t.object(showId),t.object(cap),t.object(tickets[0])]);
  assert.equal((await state()).generations[0],'2');
  const oldRevoked=await rejection(()=>consume(revokedProof),'proof predating revocation','zk_gate',2);
  const staleRoot=await rejection(()=>consume(survivorOldProof),'unrevoked note with stale root','zk_gate',2);
  await assert.rejects(()=>proof(notes[0]),/PRIVATE_NOTE_REVOKED/);
  const reissue=await rejection(()=>issuer.call('issue',t=>[t.object(showId),t.object(cap),t.pure.u64(0),
    t.pure.address(holder.keypair.toSuiAddress())]),'revoked private slot cannot be reissued','rights',9);
  const fresh=await proof(notes[1]),recovered=await consume(fresh);
  assert.ok((await state()).nullifiers.includes(fresh.nullifier));
  const replay=await rejection(()=>consume(fresh),'fresh proof second consumption','rights',8);
  const cancelProof=await proof(notes[2]);
  const cancelled=await issuer.call('cancel_show',t=>[t.object(showId),t.object(cap)]);
  const afterCancel=await rejection(()=>consume(cancelProof),'valid proof after show cancellation','rights',4);
  const final=await state();
  assert.equal(final.open,false);
  assert.equal(final.nullifiers.length,1);
  return {showId,compensated,revocationDigest:revoked.digest,oldRevoked,staleRoot,reissue,
    unaffectedNoteRecoveredDigest:recovered.digest,replay,cancellationDigest:cancelled.digest,afterCancel,
    finalNullifierCount:final.nullifiers.length,scope:'actual Sui localnet; private reissue remains unsupported'};
}
