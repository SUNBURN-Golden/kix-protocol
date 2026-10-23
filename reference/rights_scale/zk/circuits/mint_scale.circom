pragma circom 2.1.6;
include "common.circom";

// Extended-profile shield proof. Public layout is unchanged from the reference mint
// circuit: [commitment, slot, generation, domain]. The slot range check is
// `slotBits` bits wide (10 for the 1,024-slot profile) instead of 4.
template MintScale(slotBits) {
    signal input commitment;
    signal input slot;
    signal input generation;
    signal input domain;
    signal input secret;
    signal input inverse;
    secret * inverse === 1;
    component slotRange = Num2Bits(slotBits); slotRange.in <== slot;
    component genBits = Num2Bits(64); genBits.in <== generation;
    component h = Poseidon(5);
    h.inputs[0] <== secret; h.inputs[1] <== slot; h.inputs[2] <== generation;
    h.inputs[3] <== domain; h.inputs[4] <== 1;
    commitment === h.out;
}
component main {public [commitment,slot,generation,domain]} = MintScale(10);
