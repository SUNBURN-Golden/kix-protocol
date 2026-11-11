/// LOCALNET PROTOTYPE, RS-2: the frozen Verifier of the extended rights profile.
///
/// Fixed immutable verifier object, selected once by the show issuer at
/// `create_show_control`. Proof callers CANNOT supply a verifying key. The key pair belongs
/// to the depth-10 circuits (`zk/circuits/{mint_scale,spend_scale}.circom`); `circuit_manifest_hash`
/// is the SHA-256 of the manifest v2 that lists their hashes, so it is bound into the
/// show's `domain` (RS-C11). An independent client must pin this object's ID, the
/// package and the manifest before it accepts a show.
///
/// Separate from the reference profile's `kix::zk_gate` (which stays byte-identical): a
/// reference proof cannot verify here because the keys, the depth and the domain differ.
module kix_rights_scale::zk_gate;
use sui::groth16;

const EBadInputs: u64 = 1;
const EBadProof: u64 = 2;

public struct Verifier has key {
    id: UID,
    circuit_manifest_hash: vector<u8>,
    mint_vk: vector<u8>,
    spend_vk: vector<u8>,
}

public fun create(mint_vk: vector<u8>, spend_vk: vector<u8>, circuit_manifest_hash: vector<u8>, ctx: &mut TxContext) {
    assert!(circuit_manifest_hash.length() == 32, EBadInputs);
    // Reject malformed keys at installation. Only the issuer-selected object is accepted
    // by a show; a self-selected attacker key cannot substitute it.
    let _ = groth16::prepare_verifying_key(&groth16::bn254(), &mint_vk);
    let _ = groth16::prepare_verifying_key(&groth16::bn254(), &spend_vk);
    transfer::freeze_object(Verifier { id: object::new(ctx), circuit_manifest_hash, mint_vk, spend_vk });
}

public fun manifest_hash(v: &Verifier): vector<u8> { v.circuit_manifest_hash }

/// Public input layout [commitment, slot, generation, domain].
public(package) fun mint(v: &Verifier, fields: vector<u256>, proof: vector<u8>) {
    assert!(fields.length() == 4, EBadInputs);
    verify(&v.mint_vk, fields, proof);
}

/// Public input layout [noteRoot, revocationRoot, nullifier, context, domain, action].
public(package) fun spend(v: &Verifier, fields: vector<u256>, proof: vector<u8>) {
    assert!(fields.length() == 6, EBadInputs);
    verify(&v.spend_vk, fields, proof);
}

fun verify(vk: &vector<u8>, fields: vector<u256>, proof: vector<u8>) {
    let mut bytes = vector[];
    let mut i = 0;
    while (i < fields.length()) { bytes.append(std::bcs::to_bytes(&fields[i])); i = i + 1; };
    let key = groth16::prepare_verifying_key(&groth16::bn254(), vk);
    let inputs = groth16::public_proof_inputs_from_bytes(bytes);
    let points = groth16::proof_points_from_bytes(proof);
    assert!(groth16::verify_groth16_proof(&groth16::bn254(), &key, &inputs, &points), EBadProof);
}

/// Unit tests cannot produce a verifying key and proof pair for IDs that do not exist
/// at compile time. This freezes a Verifier with empty keys so tests can exercise every
/// check that runs before proof verification; any call that reaches `verify` aborts.
#[test_only]
public fun freeze_for_testing(circuit_manifest_hash: vector<u8>, ctx: &mut TxContext) {
    assert!(circuit_manifest_hash.length() == 32, EBadInputs);
    transfer::freeze_object(Verifier { id: object::new(ctx), circuit_manifest_hash, mint_vk: vector[], spend_vk: vector[] });
}
