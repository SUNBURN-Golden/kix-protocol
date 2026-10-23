pragma circom 2.1.6;
include "common.circom";

// Extended-profile private admission (RR-1..RR-6 of docs/contracts/RIGHTS_SCALE_PROFILE.md).
// Public layout is unchanged from the reference spend circuit:
// [noteRoot, revocationRoot, nullifier, context, domain, action].
//
// Note tree: append-only incremental tree, leaf = note commitment, index = insertion
// order (witness bits are private). Revocation tree: sparse tree indexed by SLOT, default
// leaf 0 (never revoked), leaf = the highest revoked generation of that slot (RR-2). The
// note is valid iff its generation is strictly greater than that leaf, so issuance and
// refund never change the revocation root; only `revoke` does.
template SpendScale(depth) {
    signal input noteRoot;
    signal input revocationRoot;
    signal input nullifier;
    signal input context;
    signal input domain;
    signal input action;
    signal input secret;
    signal input inverse;
    signal input slot;
    signal input generation;
    signal input noteSiblings[depth];
    signal input noteBits[depth];
    signal input revocationSiblings[depth];
    signal input revokedMaxGeneration;
    signal input gateLow;
    signal input gateHigh;
    signal input challenge;
    signal input expiresMs;
    secret * inverse === 1;
    action === 1; // Admission ONLY; this circuit must not authorize transfer/refund.
    component slotBits = Num2Bits(depth); slotBits.in <== slot;
    component genBits = Num2Bits(64); genBits.in <== generation;
    component revBits = Num2Bits(64); revBits.in <== revokedMaxGeneration;
    component loBits = Num2Bits(128); loBits.in <== gateLow;
    component hiBits = Num2Bits(128); hiBits.in <== gateHigh;
    component timeBits = Num2Bits(64); timeBits.in <== expiresMs;
    // RR-2: the note's generation must exceed the revoked maximum of its slot.
    component newer = LessThan(64); newer.in[0] <== revokedMaxGeneration; newer.in[1] <== generation;
    newer.out === 1;
    component note = Poseidon(5);
    note.inputs[0] <== secret; note.inputs[1] <== slot; note.inputs[2] <== generation;
    note.inputs[3] <== domain; note.inputs[4] <== 1;
    component nf = Poseidon(5);
    nf.inputs[0] <== secret; nf.inputs[1] <== slot; nf.inputs[2] <== generation;
    nf.inputs[3] <== domain; nf.inputs[4] <== 2;
    nullifier === nf.out;
    component npath = Inclusion(depth); npath.leaf <== note.out;
    component rpath = Inclusion(depth); rpath.leaf <== revokedMaxGeneration;
    for (var i=0; i<depth; i++) {
        npath.bits[i] <== noteBits[i]; npath.siblings[i] <== noteSiblings[i];
        rpath.bits[i] <== slotBits.out[i]; rpath.siblings[i] <== revocationSiblings[i];
    }
    npath.root === noteRoot; rpath.root === revocationRoot;
    component ctx = Poseidon(5);
    ctx.inputs[0] <== gateLow; ctx.inputs[1] <== gateHigh; ctx.inputs[2] <== challenge;
    ctx.inputs[3] <== expiresMs; ctx.inputs[4] <== action;
    context === ctx.out;
}
component main {public [noteRoot,revocationRoot,nullifier,context,domain,action]} = SpendScale(10);
