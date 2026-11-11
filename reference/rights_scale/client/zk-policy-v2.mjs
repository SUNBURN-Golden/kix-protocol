// These checks reject the known uninitialized Groth16 fixture and any manifest that is not
// the extended profile's v2 schema. They do not certify a production ceremony or establish
// independent contributors (the fixture ceremony is single party, RS-5 owns the real one).
import {DEPTH,SLOT_BITS,PROFILE_VERSION,MINT,SPEND} from './profile-constants.mjs';

export const MANIFEST_FORMAT='kix-zk-artifacts-v2';

export function requirePhase2Key(v, expectedPublic) {
  if(v.protocol!=='groth16' || v.curve!=='bn128' || v.nPublic!==expectedPublic || v.IC?.length!==expectedPublic+1)
    throw Error('VK_FORMAT');
  const canonicalPoint=p=>JSON.stringify(p,(_,x)=>typeof x==='string'?BigInt(x).toString():x);
  if(!v.vk_gamma_2 || !v.vk_delta_2 || canonicalPoint(v.vk_gamma_2)===canonicalPoint(v.vk_delta_2))
    throw Error('UNCONTRIBUTED_PHASE2_KEY');
}

/** `expected` pins the profile numbers the caller was built for (default: this package's). */
export function requirePhase2ManifestV2(manifest, expected={}) {
  const want={depth:DEPTH,slotBits:SLOT_BITS,profileVersion:PROFILE_VERSION,...expected};
  if(manifest.format!==MANIFEST_FORMAT) throw Error('CIRCUIT_MANIFEST_FORMAT');
  for(const key of ['depth','slotBits','profileVersion'])
    if(manifest[key]!==want[key]) throw Error('CIRCUIT_MANIFEST_'+key.toUpperCase());
  if(!Number.isInteger(manifest.rootHistoryK) || manifest.rootHistoryK<1) throw Error('CIRCUIT_MANIFEST_ROOT_HISTORY_K');
  if(expected.rootHistoryK!==undefined && manifest.rootHistoryK!==expected.rootHistoryK) throw Error('CIRCUIT_MANIFEST_ROOT_HISTORY_K');
  if(!/^[a-f0-9]{64}$/.test(manifest.phase1?.ptauSha256??'') || !manifest.phase1?.source || !Number.isInteger(manifest.phase1?.ptauPower))
    throw Error('PHASE1_RECORD_MISSING');
  for(const name of [MINT,SPEND]) {
    if(!Number.isInteger(manifest.phase2Contributions?.[name]) || manifest.phase2Contributions[name]<1)
      throw Error('PHASE2_CONTRIBUTION_REQUIRED:'+name);
    if(!Number.isInteger(manifest.constraints?.[name]) || manifest.constraints[name]<1) throw Error('CONSTRAINT_COUNT_MISSING:'+name);
    if(manifest.constraints[name]+1>2**manifest.phase1.ptauPower) throw Error('PTAU_POWER_TOO_SMALL:'+name);
    for(const suffix of ['.r1cs','.zkey','.vkey.json','.vk.bin','_js/'+name+'.wasm']) {
      if(!/^[a-f0-9]{64}$/.test(manifest.files?.[name+suffix]??''))
        throw Error('MISSING_ARTIFACT_HASH:'+name+suffix);
    }
  }
  for(const source of ['common','mint_scale','spend_scale'])
    if(!/^[a-f0-9]{64}$/.test(manifest.circuits?.[source+'.circom']??'')) throw Error('MISSING_CIRCUIT_HASH:'+source);
}
