# Builder evidence for plan-capital-equal-gross-claim-binding

The supervisor-supplied node envelope and design plan are the task input. The
node has no issue or file under `docs/tasks/`. The branch
`agent/kix-plan-capital-equal-gross-claim-binding` started at
`b6a39e66f56a8df2ad792afd5ea811e127bbd823`, which matches the cached
`origin/main` and the design base. The supervisor reserved GitHub access, so
the remote tip was unverified. Builder delivery is an uncommitted worktree.

## Coverage before this change

All test paths in this table are relative to `reference/credit_advance_f04/`.

| Requirement | Existing coverage | Gap closed by this node |
| --- | --- | --- |
| Exact S1 and S2 checkpoint sources | Sufficient for the original pack. `test_settlement_credit_boundary.py::SettlementCreditBoundaryTests.test_pack_files_are_canonical_and_hash_pinned` pins the source files and `test_vector_pack_replays_exactly` replays both histories. | The new pack checks its own pointers to both inclusive prefixes and verifies their delivered committed views. |
| Equal gross and distinct committed claim IDs | Partial. `test_s1_captured_face_is_frozen_when_settlement_commits` and `test_s2_committed_face_is_embedded_without_derivation` inspect separate histories. | The new replay checks the distinct identities, each outer ID and inner claim ID, and the common phase, currency and gross. |
| Matching draw and crossed refusal | Partial. `test_s2_committed_face_is_embedded_without_derivation` covers the S2 face and draw. `test_credit_rejection_atomicity.py::CreditRejectionAtomicityTests.test_draw_settlement_binding_conflict_leaves_no_trace` covers refusal atomicity. | Two fresh machines use the same S2 offer, approval and draw, with the S2 or S1 settlement binding. The replay compares the full envelopes and the credit views and journals before and after. |
| Full offer face and settlement isolation | Partial. `test_settlement_credit_boundary.py::SettlementCreditBoundaryTests.test_credit_journal_stores_the_literal_face` covers the literal face. | The replay checks the same full S2 face on both machines before and after the draw requests and checks both committed views and settlement journals after setup and after each draw. |
| Companion discovery | The equal-gross pair had no entries. Existing comparisons had pointer swap controls. | The index publishes both ordered associations. A detached swap of the two resolving result references fails association validation. |

## Results

At the pinned checkpoints, both settlements are `COMMITTED` at 100,000
synthetic KRW gross. Their claim IDs are `stl-s1` and `stl-s2`. The same
S2 claim remains in each branch's offer journal. The `stl-s2` binding
accepts one mock draw and records 10,000 KRW drawn and outstanding. The
`stl-s1` binding returns `SETTLEMENT_BINDING_CONFLICT`, remains `APPROVED`
with zero exposure and appends no draw. Both settlement journals match their
pre-draw baselines. The companion validator checks 21 families, 480 entries,
130 supplemental observations and 12 supporting entries.
[Vector pack](../../reference/credit_advance_f04/fixtures/capital_equal_gross_claim_binding_vectors_v1.json) · [Replay test](../../reference/credit_advance_f04/test_capital_equal_gross_claim_binding.py) · [Companion index](../../docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md#equal-gross-claim-binding)

## Commands and results

Python test runs used `PYTHONDONTWRITEBYTECODE=1` and `-B`. Cargo runs used
`CARGO_NET_OFFLINE=true`. The focused runs preceded the two full suites.
In the table, `$f04` means `reference/credit_advance_f04`.

| Command | Actual result |
| --- | --- |
| `git status --short --branch`, `git rev-parse origin/main HEAD` | Clean node branch at startup. Both local refs matched the design base. |
| Inline `PYTHONPATH=reference/credit_advance_f04 python3.12 -B -` | Replayed both pinned prefixes, matched the S2 draw to the delivered envelope and the S1-bound refusal to the contract code, and wrote the canonical vector. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_equal_gross_claim_binding.py -v` | 1 passed. |
| `python3.12 -B -m unittest discover -s "$f04" -t "$f04" -p test_capital_companion_evidence_index.py -v` | 21 passed, including the detached pointer swap. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for `credit_advance_f04` and `settlement_f01_f03` | 337 and 224 passed, respectively. |
| `python3.12 -B scripts/check_$check.py` and the same with `--self-test`, for `docs_index`, `ci_test_discovery`, `ci_checker_wiring`, `credit_evidence_map`, `settlement_evidence_map`, `openapi_contract` and `integration_gate_openapi` | All 14 invocations passed. The docs index counted 475 scanned, 440 indexed and 35 allowlisted. Test discovery reached 35 F04 test files. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 13 passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py`, `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed. All 7 architecture tests passed. |
| `python3.12 -B scripts/check_cargo_offline_cache.py` and the same with `--self-test` | Both exited 0. Cache report listed 14 of 378 archives present and showed `duckdb` missing. |
| `cargo test -p kix-kernel --locked --offline`, `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings`, `cargo tree -p kix-kernel --edges normal --locked --offline` in `runtime/` | All exited 101 before compilation. Workspace member `kix-analytics-audit` needs the missing `duckdb` registry entry. |
| `cargo test --workspace --locked --offline`, `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` in `runtime/` | Both exited 101 with the same missing registry entry. |
| `cargo fmt --all -- --check` in `runtime/` | Passed. |
| Inline `CARGO_NET_OFFLINE=true python3.12 -B -` with a temporary workspace under `runtime/target/` | Copied `kix-kernel` and `kix-types`. Both `diff -qr` checks and `cargo generate-lockfile --offline` passed. |
| Isolated `cargo test -p kix-kernel --locked --offline --quiet`, and the same kernel Clippy and dependency-tree commands as above | All passed. Kernel tests counted 139 passes. The tree listed `kix-types` as the sole normal dependency. |
| `git hash-object`, `sha256sum`, and sorted SHA-256 manifests of `reference/v0.3-rc1/` compared with `cmp` | Both locked blobs and both source pins matched before and after. The 108-file frozen manifest matched byte for byte. |
| `git diff --check`, scoped `git diff --exit-code HEAD`, `git status --short --untracked-files=all`, inline offline index and artifact checks | Eight changed paths, protected paths and earlier index rows preserved, pack SHA-256 and Git blob verified. |

## Protected bytes

| Artifact | Verified before and after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/**` | 108 files, sorted manifest SHA-256 `45ec1688d8af35fe409e17a59980d80754704731b67420fb7c1bdbed9618193b` |
| `settlement_credit_boundary_v1.json` | SHA-256 `16088b7f1170d322c0a0441e159c44151e68a31a24c46cad6c5fd0ded70b0803` |
| `settlement_credit_boundary_vectors_v1.json` | SHA-256 `f4e44f4a2f54c53de63f9fc7f94933c35453f9826992aadcd912a45fef0f26ce` |

The new vector pack has SHA-256
`dcce54255062d391faaf2d0ccc2f1f284fae8b0abbafe620162f33e25c740b34` and Git blob
`c3b425ff42bef595bb9f3a8e1a631794f8fc3117`.

## Changed files

- `reference/credit_advance_f04/fixtures/capital_equal_gross_claim_binding_vectors_v1.json`
- `reference/credit_advance_f04/test_capital_equal_gross_claim_binding.py`
- `reference/credit_advance_f04/test_capital_companion_evidence_index.py`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.json`
- `docs/status/CAPITAL_COMPANION_EVIDENCE_INDEX_V1.md`
- `docs/status/ECONOMICS_CREDIT_CONSUMER_FIELD_GUIDE.md`
- `docs/README.md`
- `validation/2026-11-27-plan-capital-equal-gross-claim-binding/README.md`

## Deviations

The supervisor's no-network rule superseded the startup fetch. The offline
Cargo cache required an isolated kernel workspace. The full Rust workspace
remains locally unverified. The local protocol checks used the touched-path
F04 and settlement suites, associated documentation and contract checks, and
offline integration limits. CI provisioning, SDK, Move, chain and ZK stages
remain outside this local run.

## Scope and delivery gates

The observed outcomes match F04 §7.5. There were zero contract violations
or contract-undefined characterizations. Evidence is source-informed and
limited to process-local mocks. External Capital acceptance is `UNVERIFIED`.
Product limits and financial terms are `UNDETERMINED` with Astra. Legal
responsibility is `UNDETERMINED` with User/legal.

A2 non-author exact-head review and exact-head CI are pending supervisor
delivery gates. The builder session has no implementation or final delivery
commit, hosted KTX or KIX run IDs or results, or merge commit and post-merge
verification.
