pragma circom 2.1.6;
include "common.circom";

template Mint() {
    signal input commitment;
    signal input slot;
    signal input generation;
    signal input domain;
    signal input secret;
    signal input inverse;
    secret * inverse === 1;
    component slotBits = Num2Bits(4); slotBits.in <== slot;
    component genBits = Num2Bits(64); genBits.in <== generation;
    component h = Poseidon(5);
    h.inputs[0] <== secret; h.inputs[1] <== slot; h.inputs[2] <== generation;
    h.inputs[3] <== domain; h.inputs[4] <== 1;
    commitment === h.out;
}
component main {public [commitment,slot,generation,domain]} = Mint();
