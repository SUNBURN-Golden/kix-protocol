// These checks reject the known uninitialized Groth16 fixture. They do not
// certify a production ceremony or establish independent contributors.
export function requirePhase2Key(v, expectedPublic) {
  if(v.protocol!=='groth16' || v.curve!=='bn128' || v.nPublic!==expectedPublic || v.IC?.length!==expectedPublic+1)
    throw Error('VK_FORMAT');
  const canonicalPoint=p=>JSON.stringify(p,(_,x)=>typeof x==='string'?BigInt(x).toString():x);
  if(!v.vk_gamma_2 || !v.vk_delta_2 || canonicalPoint(v.vk_gamma_2)===canonicalPoint(v.vk_delta_2))
    throw Error('UNCONTRIBUTED_PHASE2_KEY');
}

export function requirePhase2Manifest(manifest) {
  if(manifest.format!=='kix-zk-artifacts-v1' || manifest.depth!==4)
    throw Error('CIRCUIT_MANIFEST_FORMAT');
  for(const name of ['mint','spend']) {
    if(!Number.isInteger(manifest.phase2Contributions?.[name]) || manifest.phase2Contributions[name]<1)
      throw Error('PHASE2_CONTRIBUTION_REQUIRED:'+name);
    for(const suffix of ['.r1cs','.zkey','.vkey.json','.vk.bin','_js/'+name+'.wasm']) {
      if(!/^[a-f0-9]{64}$/.test(manifest.files?.[name+suffix]??''))
        throw Error('MISSING_ARTIFACT_HASH:'+name+suffix);
    }
  }
}
