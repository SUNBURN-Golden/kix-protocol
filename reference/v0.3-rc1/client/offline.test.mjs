import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm,stat} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {seal,unseal,durableJSON,readJSON} from './backup.mjs';
import {FR,fieldBytes,little} from './encoding.mjs';

test('holder and private note backup restores without a KIX service',()=>{
  const b={format:'kix-holder-v1',secretKey:'LOCAL_TEST_SECRET',extra:{noteSecret:'987654321',generation:1}};
  const e=seal(b,'local-test-passphrase-only');
  assert.deepEqual(unseal(e,'local-test-passphrase-only'),b);
  assert.ok(!JSON.stringify(e).includes('LOCAL_TEST_SECRET'));
});
test('wrong password and modified ciphertext cannot become a valid backup',()=>{
  const e=seal({secret:1},'local-test-passphrase-only');
  assert.throws(()=>unseal(e,'other-local-passphrase'));
  const blob=Buffer.from(e.ciphertext,'base64');blob[0]^=1;
  assert.throws(()=>unseal({...e,ciphertext:blob.toString('base64')},'local-test-passphrase-only'));
});
test('signed request journal persists exact payload with private file permissions',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'kix-client-'));
  try {
    const path=join(dir,'tx.json');const tx={digest:'fixed',bytes:'same',signatures:['same']};
    await durableJSON(path,tx);assert.deepEqual(await readJSON(path),tx);
    assert.equal((await stat(path)).mode&0o777,0o600);
  }finally{await rm(dir,{recursive:true});}
});
test('field encoding is fixed-width, little endian and rejects noncanonical values',()=>{
  assert.equal(little(256)[1],1);assert.equal(fieldBytes([1,2]).length,64);
  assert.throws(()=>fieldBytes([FR]));assert.throws(()=>fieldBytes([-1]));
});
