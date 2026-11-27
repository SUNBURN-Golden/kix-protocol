// Constraint counts of the extended-profile circuits at several depths, for the RS-2 record
// ("constraints per depth and the ptau power"). Compiles throwaway main files in a temporary
// directory with the committed templates; writes nothing to the repository.
// Usage: node measure-constraints.mjs [depth ...]   (default 4 6 8 10 12 14)
import {execFileSync} from 'node:child_process';
import {cp,mkdir,mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {r1cs} from 'snarkjs';

const here=fileURLToPath(new URL('.',import.meta.url));
const depths=process.argv.slice(2).map(Number);
if(!depths.length)depths.push(4,6,8,10,12,14);
const quiet={debug(){},info(){},warn(){},error(){}};
const work=await mkdtemp(join(tmpdir(),'rs2-constraints-'));
const rows=[];
try {
  await cp(join(here,'node_modules/circomlib/circuits'),join(work,'circomlib/circuits'),{recursive:true});
  for(const name of ['common','mint_scale','spend_scale'])await cp(resolve(here,'../zk/circuits',name+'.circom'),join(work,name+'.circom'));
  for(const depth of depths) {
    const row={depth,leaves:2**depth};
    for(const [name,template,publicInputs] of [['mint_scale','MintScale',4],['spend_scale','SpendScale',6]]) {
      // The committed file instantiates depth 10; swap only that instantiation.
      const source=(await readFile(join(work,name+'.circom'),'utf8')).replace(/= (MintScale|SpendScale)\(\d+\);/,`= ${template}(${depth});`);
      const file=name+'_d'+depth;
      await writeFile(join(work,file+'.circom'),source);
      execFileSync(process.execPath,[join(here,'node_modules/circom2/cli.js'),file+'.circom','--r1cs','-o',work],
        {cwd:work,stdio:'ignore',timeout:240000});
      const info=await r1cs.info(join(work,file+'.r1cs'),quiet);
      row[name]=info.nConstraints;
      row[name+'_ptauPower']=Math.ceil(Math.log2(info.nConstraints+publicInputs+1));
    }
    rows.push(row);
  }
} finally {
  await rm(work,{recursive:true,force:true});
}
console.log(JSON.stringify({tool:'measure-constraints.mjs',circom:'circom2 0.2.22',rows},null,2));
await new Promise(resolve=>process.stdout.write('',resolve));
process.exit(0);
