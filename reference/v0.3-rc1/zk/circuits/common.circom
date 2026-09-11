pragma circom 2.1.6;
include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/bitify.circom";

template Inclusion(depth) {
    signal input leaf;
    signal input siblings[depth];
    signal input bits[depth];
    signal output root;
    signal nodes[depth+1];
    signal left[depth];
    signal right[depth];
    component h[depth];
    nodes[0] <== leaf;
    for (var i=0; i<depth; i++) {
        bits[i]*(bits[i]-1) === 0;
        left[i] <== nodes[i] + bits[i]*(siblings[i]-nodes[i]);
        right[i] <== siblings[i] + bits[i]*(nodes[i]-siblings[i]);
        h[i] = Poseidon(2);
        h[i].inputs[0] <== left[i]; h[i].inputs[1] <== right[i];
        nodes[i+1] <== h[i].out;
    }
    root <== nodes[depth];
}
