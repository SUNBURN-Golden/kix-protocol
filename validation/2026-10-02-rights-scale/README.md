# 2026-10-02 document reconciliation and public rights scale

Input: direct user requests to reconcile documents/specifications and implement the Move capacity expansion. No numbered task document was created or rewritten by this executing session. This is not an AIOPS-dispatched node or its completion receipt.

Observed remote main/base: `dd0a501248e092c2a4475088d94d7449b7bd98b5`. Commerce reviewed baseline: `b0217cc9e92cc87813f6ce6724632699d400eb3a`. Private-repo CLI clone was unavailable; the pinned files were read through the connected GitHub API. Changes are applied as a new Git tree over that exact remote base. The local scratch Git snapshot is not the upstream parent. Final delivery SHA and hosted CI belong in the PR, avoiding a self-reference commit loop.

## Executed verification

- Sui archive SHA256 matched toolchains.json: `547b3091e975b8a6b4078473a3868d86e985156b6715a8c4afb7fd7313a36abf`; CLI release mainnet-v1.79.1, framework `808640d9b49aecf29d8e6f46033c15eca236efa7`.
- `sui move --client.config .local/sui-config/client.yaml --build-env mainnet test --path reference/rights-scale-v1/sui --gas-limit 1000000000`: 31 passed, 0 failed. See move-scale.log.
- Same command on `reference/v0.3-rc1/sui` without the gas override: 19 passed, 0 failed. See move-legacy.log. The legacy source/package is not changed by this PR.
- `python3 scripts/run_localnet.py --scale`: passed on an isolated one-validator Sui chain; see localnet.json. Complete ranges at 1,024/16,384/65,536, last-slot issuance, actual failed cross-page PTB rollback, refund/stale rejection/reissue and cancellation rejection. The runner stopped its own node afterward. No deployment to a public chain.
- `python3 -m py_compile scripts/run_localnet.py scripts/verify_runtime.py`; `node --check reference/rights-scale-v1/localnet.mjs`; `git diff --check`: passed.
- Canonical JSON hash comparison: plan and all 67 active-draft node hashes agree with registration manifest. Only roadmap-sync count prose and its two dependent hashes changed; all other node definitions/flags/dependencies unchanged. PENDING pointer retained; no executable .aiops plan.

## Coverage and limits

The old Move tests cover legacy public semantics. The new tests add page/range identity, construction seal, generation fencing, shared reference routing and public lifecycle boundaries. Actual localnet tests exercise new object IDs and PTB rollback rather than a copied Python simulation. Source hashes in source-sha256.json bind the implementation and runners to these results.

Kernel lock blobs are inherited unchanged from the remote base: `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. The published tree must retain these exact values.

These are author-run tests, not independent Astra review. Existing private/ZK journeys and full Rust/SDK/circuit suites were not rerun locally. Hosted CI and independent exact-head review remain pending; a draft skip is not PASS. No measured throughput/latency, concurrent sold-out concert, network fault tolerance, private scale, GA/grant qualification, SDK/UI integration, real payment, mainnet or production readiness is claimed. See RIGHTS_SCALE_PROFILE.md for remaining RS acceptance obligations. Initial local harness failure while identifying the published package was corrected using the SDK objectTypes package entry; the committed driver and shared runner then passed on fresh isolated chains.
