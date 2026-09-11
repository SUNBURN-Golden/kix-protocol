import {randomBytes, scryptSync, createCipheriv, createDecipheriv, createHash} from 'node:crypto';
import {open, readFile, rename, mkdir} from 'node:fs/promises';
import {dirname} from 'node:path';
const aad = Buffer.from('kix-recovery-v1:aes-256-gcm:scrypt');
export function seal(payload, passphrase) {
  if (typeof passphrase !== 'string' || passphrase.length < 12) throw Error('BACKUP_PASSPHRASE_TOO_SHORT');
  const salt = randomBytes(16), nonce = randomBytes(12);
  const key = scryptSync(passphrase, salt, 32, {N:32768,r:8,p:1,maxmem:64*1024*1024});
  const c = createCipheriv('aes-256-gcm',key,nonce); c.setAAD(aad);
  const ciphertext = Buffer.concat([c.update(JSON.stringify(payload)),c.final()]);
  key.fill(0);
  return {format:'kix-recovery-v1',salt:salt.toString('base64'),nonce:nonce.toString('base64'),
    tag:c.getAuthTag().toString('base64'),ciphertext:ciphertext.toString('base64')};
}
export function unseal(envelope, passphrase) {
  if (envelope.format !== 'kix-recovery-v1') throw Error('BACKUP_FORMAT');
  const salt=Buffer.from(envelope.salt,'base64'), nonce=Buffer.from(envelope.nonce,'base64'),tag=Buffer.from(envelope.tag,'base64');
  if(salt.length!==16 || nonce.length!==12 || tag.length!==16) throw Error('BACKUP_ENCODING');
  const key=scryptSync(passphrase,salt,32,{N:32768,r:8,p:1,maxmem:64*1024*1024});
  const d=createDecipheriv('aes-256-gcm',key,nonce); d.setAAD(aad);d.setAuthTag(tag);
  try { return JSON.parse(Buffer.concat([d.update(Buffer.from(envelope.ciphertext,'base64')),d.final()]).toString()); }
  finally { key.fill(0); }
}
export async function durableJSON(path, value) {
  await mkdir(dirname(path),{recursive:true});
  const temp=path+'.'+randomBytes(8).toString('hex')+'.tmp';
  const f=await open(temp,'wx',0o600);
  try { await f.writeFile(JSON.stringify(value,null,2)+'\n'); await f.sync(); } finally { await f.close(); }
  await rename(temp,path);
  const dir=await open(dirname(path),'r'); try {await dir.sync();} finally {await dir.close();}
}
export async function readJSON(path) {return JSON.parse(await readFile(path,'utf8'));}
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
