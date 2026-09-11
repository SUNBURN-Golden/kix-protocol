/// Fixed immutable verifier object, selected once by the Show issuer.
/// Proof callers CANNOT supply a VK. The independent client must pin this
/// object's ID, circuit artifact hashes and the package before accepting a Show.
module kix::zk_gate;
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
    // Reject malformed keys at installation. Only the issuer-selected object
    // is accepted by a Show; a self-selected attacker VK cannot substitute it.
    let _ = groth16::prepare_verifying_key(&groth16::bn254(), &mint_vk);
    let _ = groth16::prepare_verifying_key(&groth16::bn254(), &spend_vk);
    transfer::freeze_object(Verifier { id: object::new(ctx), circuit_manifest_hash, mint_vk, spend_vk });
}

public(package) fun mint(v: &Verifier, fields: vector<u256>, proof: vector<u8>) {
    assert!(fields.length() == 4, EBadInputs);
    verify(&v.mint_vk, fields, proof);
}

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
