// LOCAL FIXTURE CEREMONY ONLY. Not a production trusted setup.
import {execFileSync} from 'node:child_process';
import {randomBytes} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {vkBytes} from './encoding.mjs';
import {sha256,durableJSON} from './backup.mjs';
const here=fileURLToPath(new URL('.',import.meta.url));
const out=resolve(here,'../zk/artifacts');await mkdir(out,{recursive:true});
const bin=n=>join(here,'node_modules/.bin',n);
const run=(cmd,args)=>execFileSync(bin(cmd),args,{cwd:here,stdio:'inherit',timeout:600000});
for(const name of ['mint','spend'])run('circom2',[resolve(here,'../zk/circuits',name+'.circom'),'--r1cs','--wasm','--sym','-l',join(here,'node_modules'),'-o',out]);
run('snarkjs',['powersoftau','new','bn128','14',join(out,'pot-initial.ptau')]);
run('snarkjs',['powersoftau','contribute',join(out,'pot-initial.ptau'),join(out,'pot-one.ptau'),'--name=KIX-single-party-local-fixture','-e='+randomBytes(64).toString('hex')]);
run('snarkjs',['powersoftau','prepare','phase2',join(out,'pot-one.ptau'),join(out,'pot-final.ptau')]);
const files={};
for(const name of ['mint','spend']) {
  run('snarkjs',['groth16','setup',join(out,name+'.r1cs'),join(out,'pot-final.ptau'),join(out,name+'.zkey')]);
  run('snarkjs',['zkey','export','verificationkey',join(out,name+'.zkey'),join(out,name+'.vkey.json')]);
  const v=JSON.parse(await readFile(join(out,name+'.vkey.json'),'utf8'));
  await writeFile(join(out,name+'.vk.bin'),vkBytes(v));
  for(const file of [name+'.r1cs',name+'.zkey',name+'.vkey.json',name+'.vk.bin',name+'_js/'+name+'.wasm'])files[file]=sha256(await readFile(join(out,file)));
}
const circuits={};for(const name of ['common','mint','spend'])circuits[name+'.circom']=sha256(await readFile(resolve(here,'../zk/circuits',name+'.circom')));
await durableJSON(join(out,'manifest.json'),{format:'kix-zk-artifacts-v1',setup:'INSECURE_SINGLE_PARTY_LOCAL_FIXTURE',
  curve:'BN254',depth:4,circuits,files,suiSerializationVerified:false});
console.log('Fixture artifacts generated. Actual Sui acceptance and negative proof tests remain required.');
