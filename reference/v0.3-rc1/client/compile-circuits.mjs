// Keep WASI includes inside one staging directory. circom2 cannot consistently
// resolve sibling source/include paths when launched from the client directory.
import {execFileSync} from 'node:child_process';
import {cp, mkdir, mkdtemp, rm} from 'node:fs/promises';
import {join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

export async function compileCircuits() {
  const here=fileURLToPath(new URL('.',import.meta.url));
  const out=resolve(here,'../zk/artifacts');
  await mkdir(out,{recursive:true});
  const staging=await mkdtemp(join(out,'.compile-'));
  try {
    for(const name of ['common','mint','spend']) {
      await cp(resolve(here,'../zk/circuits',name+'.circom'),join(staging,name+'.circom'));
    }
    await cp(join(here,'node_modules/circomlib/circuits'),join(staging,'circomlib/circuits'),{recursive:true});
    for(const name of ['mint','spend']) {
      execFileSync(process.execPath,[join(here,'node_modules/circom2/cli.js'),name+'.circom',
        '--r1cs','--wasm','--sym','-o',out],{cwd:staging,stdio:'inherit',timeout:120000});
    }
  } finally {
    await rm(staging,{recursive:true,force:true});
  }
}

if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url))await compileCircuits();
