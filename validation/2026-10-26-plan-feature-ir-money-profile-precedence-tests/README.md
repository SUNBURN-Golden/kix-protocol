# Feature IR money-profile precedence — local validation

Node/task ID: `plan-plan-feature-ir-money-profile-precedence`.
Task input: supervisor-provided node specification and read-only design plan in the session; no issue or task document under `docs/tasks/` exists for this node. Dependencies: `plan-plan-feature-semantics-v1-evidence-map`, `plan-feature-ir-plan-limit-edge-tests`. Builder-authored evidence only; not A2/non-author review, acceptance or a capability grade change.

Observed local `origin/main` and starting branch HEAD: `118fc28862a6828b80166433bac6f5476037629d`.
Branch: `agent/kix-plan-plan-feature-ir-money-profile-precedence`. No local base delta. Fetch omitted under the supervisor's explicit no-network instruction; remote freshness unverified.
Implementation commit and exact final task head: not created (uncommitted delivery); end-of-session HEAD remains the starting SHA. Merge commit and post-merge verification: not applicable.
Exact-head KTX CI and KIX protocol CI run IDs/status/conclusions: not available / not run. The supervisor owns commits and GitHub delivery. Local READY means ready for supervisor review, not merge-ready; no older CI is inherited.

## Changed paths (complete)

- `runtime/crates/kix-feature-ir/tests/schema_bound.rs` — three public-API regressions; no source changes.
- `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md` — S6-EXPORT-BOUNDARY/G9-4 citations and gaps, append-only node note and class-B characterization.
- `docs/README.md` — validation index bullet.
- `validation/2026-10-26-plan-feature-ir-money-profile-precedence-tests/README.md` — this record.

## Existing coverage mapping (before new tests)

| Requirement | Existing coverage and classification | Gap addressed |
|---|---|---|
| Each identity field wins over simultaneously invalid range | Partially covered: `schema_bound.rs::fast64_rejects_wrong_asset_version_or_hash_at_export` rejects individual identity mismatches only at 1 atom. | No simultaneous failure regression. New `fast64_identity_mismatch_precedes_amount_range_for_each_identity_field` uses matching-identity range controls plus asset/version/hash and all-three mismatches at 101, i64::MAX, i64::MAX+1 and u128::MAX. |
| Inclusive executionMaxAtoms, max+1 and i64 ceiling | Sufficiently covered for max=100 and i64::MAX by that existing export test, including max+1 rejection; `src/lib.rs::fast64_profile_is_bound_to_asset_and_registry_version` rejects checked(i64::MAX+1). | New `fast64_checked_range_is_inclusive_at_claim_and_capped_at_i64_max` adds max=0, 1, i64::MAX-1, public checked(u128::MAX) rejection and mismatched version at the i64 ceiling; existing cases are cited, not duplicated. |
| Claimed range is version-bound and unauthenticated | Partially covered: inline profile test checks the stored key, valid export and oversized claim rejection; existing export test rejects a mismatched version. | New `fast64_checked_claim_is_not_inherited_across_registry_versions` exports against separate wider/narrower claims across versions in both range-growth directions; alternate hash claims construct and self-export, then reject each other's amounts. |
| Registry signature/authority/content authentication | NOT covered. | Remains owned by `k-stage7-authenticated-export`; no authentication implemented or inferred. |

Test paths above are relative to `runtime/crates/kix-feature-ir/`. All added assertions use `Fast64MoneyProfile::checked`, `export_amount(AssetAmount)`, `execution_max_atoms()` and public constructors. Amounts use u128::MAX as the construction bound to reach the export boundary. Fixtures are synthetic claims, not product policy values.

## Classifications and remaining uncertainty

Class A: identity-before-range, inclusive claimed maximum, signed ceiling and version non-inheritance match FEATURE_SEMANTICS_V1 §6 in the tested cases. Identity and range failures have distinct variants.
Class B: asset, registry-version and registry-hash failures all return Fast64IdentityMismatch; the caller cannot identify the failing field or the order of identity checks from that error. The contract does not require per-field errors; no semantics chosen.
Class C: none found. No source fix or contract redefinition was made.

Map counts stay **rows=41 COVERED=1 PARTIAL=23 NOT_COVERED=17**. S6-EXPORT-BOUNDARY and G9-4 stay PARTIAL, owner `k-stage7-authenticated-export`. All five X-* rows stay NOT_COVERED, owner `k-stage7-cpu-analytics-sql-audit`. No grade or capability-register change.

Remaining gaps: compile-fail API/privacy fixture and authenticated registry snapshots/export/catalog; execution and backend conformance remain open with the map's owners. No MoneyWide128, evaluator, new IR type or protocol command was added. No production readiness, durability, distributed fencing, bank exactly-once, chain finality, legal compliance, independent clean-room result, Sui/network, real funds or provider/bank/KYC execution is claimed. Release-mode execution was not separately tested.

## Commands actually run and results

The closest local CI equivalents for the touched paths are the complete **Stdlib offline document checks** run block from `.github/workflows/protocol.yml`, its Rust production runtime boundary (workspace tests/fmt/Clippy), and the architecture/kernel checks in `.github/workflows/ktx-kernel.yml`. A foreground Python runner extracted the stdlib commands in workflow order and ran each with subprocess argument arrays, saving actual exit codes/output. All **53 stdlib invocations** passed, followed by both architecture invocations (**55 total**). Stage-5 remained self-test-only. Cargo ran offline; no shell background jobs or network actions.

No product/checker/test failure required a fix or retry. Full hosted bootstrap, Move/localnet, SDK and ZK jobs were not run: they do not exercise these changed tests/documents and bootstrap/network actions are prohibited. This is local evidence, not a claim of full hosted protocol verification.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; local refs both 118fc28862a6828b80166433bac6f5476037629d; branch as recorded above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required hashes match before work. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --test schema_bound --locked` | Exit 0; 21 tests passed, 0 failed. Narrow run first. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir -p kix-feature-semantics --locked` | Exit 0; 58 tests passed, 0 failed/ignored (8 test/doc-test result groups). |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 268 tests passed, 0 failed/ignored (42 test/doc-test result groups). |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; formatting clean; check-only, no locked file mutation. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-feature-ir --all-targets --locked -- -D warnings` | Exit 0; all targets clean with warnings denied. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0; all targets clean with warnings denied. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 86 tests passed, 0 failed/ignored (9 test/doc-test result groups). |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0; all targets clean with warnings denied. |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0; kix-kernel normal dependency is kix-types only. |
| `python3 .local/verification/money-profile-precedence/audit.py` | Exit 0; 1,027 other tracked blobs byte-identical to HEAD, including 108 reference/v0.3-rc1 blobs, both locks, all .aiops, docs/tasks, CI, source/contract and capability-register bytes; exactly four delivery paths; map statuses/owners unchanged and five X-* pins intact. |
| `git diff --check`; `git diff --stat`; `git diff -- runtime/crates/kix-feature-ir/tests/schema_bound.rs docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md docs/README.md`; `git status --short` | Exit 0; no whitespace errors; only the three tracked edits and new validation README listed above. |

The complete stdlib/architecture invocation results follow. Self-tests' final pass lines summarize their actual in-memory negative/positive controls, not a retry of an external operation.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=273 indexed=238 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0; ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0; self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0; lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0; self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0; BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=22 PARTIAL=15 NOT_COVERED=2 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; feature semantics evidence map ok: Counts: rows=41 COVERED=1 PARTIAL=23 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; self-test: pass (77 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0; integration gate contract evidence map ok: Counts: rows=54 COVERED=35 PARTIAL=18 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0; self-test: pass (83 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=64 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed. |

The protected-byte audit enumerated `git ls-tree -rz HEAD`, read each non-delivery blob from the working tree, reconstructed its Git SHA-1 (blob header plus bytes) and compared it with HEAD. It also verified both pinned lock hashes, unchanged local refs, all map statuses/owners, the five X-* pins, and the union of tracked/untracked delivery paths. The audit uses NUL-delimited filenames and never modifies protected files. Final-merge blob checks are not applicable (no merge).

## Locked blobs and protected bytes

| Path | Required Git blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match (HEAD and working bytes) |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match (HEAD and working bytes) |

## Deviations

- Session-start fetch omitted under the supervisor's explicit no-network override. The locally recorded origin/main equals the task base; remote freshness remains unverified.
- No commits, pushes, PRs, issues, comments, merges or hosted exact-head CI; these belong to the supervisor.
- No implementation-scope deviation from the design plan. A matching-hash success control was added for the alternate claim so that cross-hash rejection cannot be mistaken for an unusable profile.
