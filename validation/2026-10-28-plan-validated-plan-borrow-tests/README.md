# ValidatedFeaturePlan external-consumer boundary evidence

Node: `plan-plan-validated-plan-borrow-tests`. Task input: supervisor-supplied node
specification and design plan; no issue or docs/tasks document exists for this node.
This is not ASTRA program mode. Source-informed builder evidence, not independent
review, catalog authentication or backend admission.

## Existing coverage mapped before adding fixtures

Paths below are relative to runtime/crates/kix-feature-ir/tests/.

| Requirement | Existing evidence | Assessment and action |
|---|---|---|
| Schema validation and accessor values | schema_bound.rs::valid_integer_expression_can_feed_terminal_division; schema_bound.rs::catalog_resolution_checks_identity_version_and_duplicates; existing schema/type rejection tests | Sufficiently covered; reuse without duplicating runtime tests. |
| External validate_with_schemas and shared accessors | Public API calls in schema_bound.rs; no standalone ValidatedFeaturePlan consumer | Partially covered; add a typed positive compilation control. |
| Direct wrapper construction | No external rejection fixture | Not covered; add struct literal rejection (E0451). |
| Original plan borrow until subsequent wrapper use | No external rejection fixture | Not covered; add stages mutation before plan() use (E0502). |
| Original catalog borrow until subsequent wrapper use | No external rejection fixture | Not covered; add catalog mutation before catalog() use (E0502). |
| Shared plan/catalog accessor immutability | Existing accessor value assertions, no rejected writes | Partially covered; add separate plan/catalog mutation rejections (E0596). |
| Output schema accessor immutability | Existing output value assertion, no rejected write | Not covered; add output kind assignment rejection (E0594). |
| Mutation after wrapper last use | No explicit last-use control | Not covered; add a positive consumer using all accessors, then mutating both inputs with the binding still in scope, without drop or inner scope. |
| Unrelated failures cannot pass | api_boundaries.rs::require_success, require_rejection and fast64_external_consumer_api_boundaries | Sufficiently covered by strict shared harness; reuse without weakening checks or adding Fast64 coverage. |

## Implementation evidence and limits

The new `api_boundaries.rs::validated_plan_external_consumer_api_boundaries` reuses
Scratch, compiler, dependency, compile_consumer, require_success and
require_rejection. Only the unchanged fresh-library build loop is extracted into
build_libraries, shared with the existing Fast64 test. Each test invocation builds
fresh local kix_types, kix_feature_semantics and kix_feature_ir rlibs in dependency
order in its own scratch directory. RUSTC is respected; RUSTUP_AUTO_INSTALL=0
prevents provisioning. Consumers use public APIs and --emit=metadata, with no
cached rlibs, dependencies, downloads, implementation-module imports or skips.
Existing Fast64 assertions and strict diagnostic helpers are unchanged.

The minimal synthetic inputs have one Limit stage and one I64 column in a matching
version-1 dataset. They are fixture values, not product policy. The two positive
consumers and six negatives use the same compiler and fresh dependencies.

| Fixture under tests/fixtures/api_boundaries/ | Actual result and gap addressed |
|---|---|
| validated_accessors.rs | Compiled: validate_with_schemas returns an explicitly typed ValidatedFeaturePlan; plan(), catalog() and output_schema() type-check as shared references. |
| validated_mutation_after_last_use.rs | Compiled: all three accessors are used, then both original inputs mutate while the wrapper binding remains in scope and unused; no drop or inner scope. |
| validated_private_construction.rs | Rejected: E0451 naming private plan, catalog and output fields of ValidatedFeaturePlan. |
| validated_plan_borrow.rs | Rejected: E0502 naming candidate.stages and mutable/immutable borrow conflict before subsequent checked.plan(). |
| validated_catalog_borrow.rs | Rejected: E0502 naming schemas and mutable/immutable borrow conflict before subsequent checked.catalog(). |
| validated_plan_accessor_mutation.rs | Rejected: E0596 for mutable borrow through a shared reference from plan(). |
| validated_catalog_accessor_mutation.rs | Rejected: E0596 for mutable borrow through a shared reference from catalog(). |
| validated_output_mutation.rs | Rejected: E0594 for assignment through a shared reference from output_schema(). |

Every negative exited 1 with exactly one substantive error, at that fixture's own
source path, with the expected code and relevant diagnostic fragments. Additional
errors, compiler crashes, missing dependencies, setup failures and diagnostic drift
fail the harness. Positive compilation is required and cannot pass by skipping.
These are source-informed safe-Rust API-boundary checks, not clean-room evidence.
The fixtures compile only; the reused schema_bound tests supply runtime assertions.

S10-CATALOG-AUTH stays PARTIAL, owner k-stage7-authenticated-export. Its existing
schema citation and the gap text "no backend admission or authenticated separate
catalog supply" remain. Only that row's Tests and explanatory Gap cells change.
Counts stay rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17. No other evidence row,
status, owner, capability grade, policy or UNDETERMINED value changes.

No explicit contract violation or new contract-undefined characterization was found.
Catalog authentication, separately trusted catalog supply, backend admission and
backend execution remain open. No actual exporter, Polars/DuckDB/GPU execution,
backend conformance, production readiness, durability, real funds/provider/bank/KYC
or chain execution is established. Existing contract-undefined observations and
UNDETERMINED values/owners remain unchanged; this node chooses no semantics.

## Provenance and delivery gates

Execution date: 2026-10-28. Branch:
`agent/kix-plan-plan-validated-plan-borrow-tests`.
Observed cached origin/main, initial task HEAD and comparison base all equal
`dacb7d2bb38c101a860a40a3873f1eac1d5a1442`; there is no local base delta.
The supervisor's no-network instruction overrides AGENTS §1 fetch. Remote freshness
is unverified. No task branch/base or history was changed.

Implementation and final delivery commit SHAs are unassigned: these are uncommitted
worktree edits and the supervisor owns git/GitHub publication. Builder HEAD remains
the initial SHA above. No commit, push, PR, issue, comment, marker or merge was made.
KTX kernel verification and KIX protocol verification exact-delivery-head run IDs,
statuses and conclusions are unavailable, not passing. Non-author exact-head review
at audit floor A2 and both required workflows completed/success at the exact
supervisor delivery head are required before merge readiness. This record is builder
evidence only. Merge SHA, final-merge blob check and post-merge main CI: not
applicable, no merge performed. READY in the handoff means local builder completion.

## Commands actually run and results

Installed rustc 1.98.1 (48a229cea 2026-09-01), cargo 1.98.1
(797e8a9bc 2026-08-05), matching the workflows' Rust version. Cargo verification
used CARGO_NET_OFFLINE=true and RUSTUP_AUTO_INSTALL=0; Python checker execution
used PYTHONDONTWRITEBYTECODE=1. Commands ran as foreground subprocesses, with no
background jobs, installs or downloads. Narrow checks preceded broader Rust checks.

| Command | Result |
|---|---|
| `rustc --version`; `cargo --version` | Versions above; both exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --test api_boundaries --locked` | Exit 0; 2 passed, 0 failed. New ValidatedFeaturePlan and existing Fast64 harnesses pass. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --locked` | Exit 0; 50 passed, 0 failed: lib 5, api_boundaries 2, audit_regressions 8, plan_limits 7, schema_bound 21, validator_matrix 7; 0 doc-tests. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 319 passed, 0 failed across 45 test targets (including doc-test targets). |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; clean. |
| `rustfmt --edition 2024 --check runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/*.rs` | Exit 0; every nested fixture explicitly checked. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests, OK. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 122 passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0; no warnings. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0; kix-kernel -> kix-types only. |
| `git diff --check` | Exit 0; clean. |

The following 63 commands from protocol.yml's Stdlib offline document checks block
were extracted and executed verbatim, in workflow order; all exited 0. This includes
the five requested feature-semantics/rollup/index/CI checkers and their self-tests.
check_stage5_host ran --self-test only, as CI specifies. The loopback host report is
host-context evidence only, not host selection or permission. The offline Cargo cache
report found all 18 locked registry packages present, missing=[]; it installs nothing.

| Command | Result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=452 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=296 indexed=261 allowlisted=35 |
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
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; self-test: pass (81 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0; integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0; self-test: pass (85 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test: pass (16 negative controls) |
| `python3 scripts/check_class_b_index.py` | Exit 0; class B index ok: rows=216 sources=71 symbols=39; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0; self-test: pass (20 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; ci test discovery ok: reference_suites=6 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; self-test: pass (18 negative controls) |
| `python3 scripts/check_loopback_host.py` | Exit 0; Host report emitted; permission_granted=false (no host selected). |
| `python3 scripts/check_loopback_host.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0; All 18 registry packages present; missing=[]. |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Only the closest CI equivalents for the touched Rust tests and documents ran.
Specialized Move/Sui/ZK jobs, localnet journeys, storage probes, SDK conformance and
venv runtime/commerce/canonical pipelines were not run. They remain subject to the
required delivery workflows; local results do not imply full CI success.

## Protected files and complete changed-path list

Before and after implementation, `git hash-object` reports:

| Protected file | Before and after Git blob |
|---|---|
| runtime/crates/kix-kernel/src/lib.rs | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The recorded base reference/v0.3-rc1 tree is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
`git diff --exit-code dacb7d2bb38c101a860a40a3873f1eac1d5a1442 -- runtime/crates/kix-feature-ir/src/ runtime/FEATURE_SEMANTICS_V1.md .github/ .aiops/ docs/tasks/ docs/contracts/ reference/`
exited 0, with no differences. Final protected-path status is empty, including
untracked paths. A separate Python comparison enumerated the base with
`git ls-tree -r -z dacb7d2bb38c101a860a40a3873f1eac1d5a1442 -- reference/v0.3-rc1/`
and checked each on-disk file with `git hash-object --stdin`: all 108 tracked
files were byte-identical, with no untracked reference files. Kernel blobs match; reference/v0.3-rc1/**, runtime implementation,
contracts, workflows, .aiops/** and docs/tasks/** remain unchanged. No transient
edits were made to protected files.

Complete changed paths (13):

- runtime/crates/kix-feature-ir/tests/api_boundaries.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/support.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/validated_accessors.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/validated_mutation_after_last_use.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/validated_private_construction.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/validated_plan_borrow.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/validated_catalog_borrow.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/validated_plan_accessor_mutation.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/validated_catalog_accessor_mutation.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/validated_output_mutation.rs
- docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md
- docs/README.md
- validation/2026-10-28-plan-validated-plan-borrow-tests/README.md

Deviations: fetch and publication/exact-head hosted CI are left to the supervisor
under its explicit no-network/no-publication instructions. No implementation design
change, policy decision or scope expansion was needed. Remaining follow-ups are
the delivery review/CI gates and the unchanged authentication/backend gaps with
their existing owners.
