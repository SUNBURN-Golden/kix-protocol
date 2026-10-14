Generated proving keys, witnesses and WASM remain ignored here.

# Fixture ceremony of the extended rights profile (RS-2)

**This is not an operational ceremony.** `client/setup-zk.mjs` runs a single-party,
locally generated fixture setup for the depth-10 circuits (`zk/circuits/mint_scale.circom`,
`spend_scale.circom`). No audited or independent multi-party ceremony, no circuit audit and no
anonymity claim exist. Those are conditions of RS-5, not of RS-2. The manifest says so itself:
`setup: INSECURE_SINGLE_PARTY_LOCAL_FIXTURE`.

Run, from the repository root:

    npm --prefix reference/rights_scale/client run setup:zk   # compile, phase 1, phase 2, manifest v2
    npm --prefix reference/rights_scale/client run test:zk    # forgery rejection with the fresh keys
    .venv/bin/python scripts/run_localnet_rights_scale_private.py

What the setup does and records (`manifest.json`, format `kix-zk-artifacts-v2`):

- **Power of Tau.** Phase 1 is circuit independent. The power is chosen from the recounted
  constraints (at least 14; `constraints + public inputs + 1 <= 2^power` is checked, and a cached
  phase-1 file below that power is ignored). The measured counts and the power are in the
  manifest (`constraints`, `phase1.ptauPower`) and in
  `validation/2026-10-14-rs-2-private-path/README.md`.
- **Phase-1 reuse.** Setting `KIX_ZK_PHASE1_PTAU` to an earlier `pot-final.ptau` reuses only
  that circuit-independent phase 1. The mint and spend phase-2 contributions and `zkey verify`
  always run fresh, and `manifest.json` records the phase-1 source (`REUSED_CACHED_LOCAL_FIXTURE`
  or `FRESH_SINGLE_PARTY_LOCAL_FIXTURE`) and its SHA-256.
- **Phase 2.** One contribution per circuit, `snarkjs zkey verify`, and `requirePhase2Key`, which
  rejects a key whose gamma equals delta (an uncontributed key accepts compensated forgeries;
  `zk-regression.mjs` reproduces that on these circuits and then requires rejection with the
  contributed keys).
- **Manifest v2** adds, to the reference manifest: the tree `depth`, `slotBits`,
  `profileVersion`, `rootHistoryK` (test-only fixture value, operational value UNDETERMINED),
  the phase-1 record, constraint counts, the public-input layouts and the circuit source hashes.
  Its SHA-256 is the `circuit_manifest_hash` of the on-chain `zk_gate::Verifier` and therefore
  part of every show's `domain` (RS-C11).

A new `Verifier` object and a new show are needed for new artifacts: a show pins its Verifier
at creation. Shows of the 16-slot reference profile keep their own verifier and keys
(`reference/v0.3-rc1`), which this directory never touches.
