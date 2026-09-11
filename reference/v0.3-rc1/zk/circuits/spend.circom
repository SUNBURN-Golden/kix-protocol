pragma circom 2.1.6;
include "common.circom";

template Spend() {
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
    signal input noteSiblings[4];
    signal input noteBits[4];
    signal input revocationSiblings[4];
    signal input gateLow;
    signal input gateHigh;
    signal input challenge;
    signal input expiresMs;
    secret * inverse === 1;
    action === 1; // Admission ONLY; this circuit must not authorize transfer/refund.
    component slotBits = Num2Bits(4); slotBits.in <== slot;
    component genBits = Num2Bits(64); genBits.in <== generation;
    component loBits = Num2Bits(128); loBits.in <== gateLow;
    component hiBits = Num2Bits(128); hiBits.in <== gateHigh;
    component timeBits = Num2Bits(64); timeBits.in <== expiresMs;
    component note = Poseidon(5);
    note.inputs[0] <== secret; note.inputs[1] <== slot; note.inputs[2] <== generation;
    note.inputs[3] <== domain; note.inputs[4] <== 1;
    component nf = Poseidon(5);
    nf.inputs[0] <== secret; nf.inputs[1] <== slot; nf.inputs[2] <== generation;
    nf.inputs[3] <== domain; nf.inputs[4] <== 2;
    nullifier === nf.out;
    component rev = Poseidon(4);
    rev.inputs[0] <== slot; rev.inputs[1] <== generation; rev.inputs[2] <== domain; rev.inputs[3] <== 3;
    component npath = Inclusion(4); npath.leaf <== note.out;
    component rpath = Inclusion(4); rpath.leaf <== rev.out;
    for (var i=0; i<4; i++) {
        npath.bits[i] <== noteBits[i]; npath.siblings[i] <== noteSiblings[i];
        rpath.bits[i] <== slotBits.out[i]; rpath.siblings[i] <== revocationSiblings[i];
    }
    npath.root === noteRoot; rpath.root === revocationRoot;
    component ctx = Poseidon(5);
    ctx.inputs[0] <== gateLow; ctx.inputs[1] <== gateHigh; ctx.inputs[2] <== challenge;
    ctx.inputs[3] <== expiresMs; ctx.inputs[4] <== action;
    context === ctx.out;
}
component main {public [noteRoot,revocationRoot,nullifier,context,domain,action]} = Spend();
