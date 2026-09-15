Generated proving keys, witnesses and WASM remain ignored here.
Run client/setup-zk.mjs to generate fresh single-party fixture parameters with
separate mint/spend phase-2 contributions and key verification. Then run
client/zk-regression.mjs and the actual private Sui localnet journey.

The original 2026-09-11 parameters omitted circuit-specific contributions and
accept compensated forged proofs. They must not be reused. New artifacts also
require a newly created immutable Verifier and Show that pins its ID.
Fresh fixture parameters remain unsuitable for production; no audited or
independent multi-party ceremony is claimed.
