# Feature IR validator matrices — local validation

Node/task ID: `plan-plan-feature-ir-validator-matrix-closure`.
Task input: supervisor-provided node specification and read-only design plan in the session; no issue or matching `docs/tasks/` document exists. No dependencies. Builder-authored evidence only; not A2/non-author review, acceptance or a capability grade change.

Observed local `origin/main`, starting branch HEAD and end-of-session HEAD: `58dd527ff53097f5231e89f25ebdf3e94586ee65`.
Branch: `agent/kix-plan-plan-feature-ir-validator-matrix-closure`. No local base delta. Fetch omitted under the supervisor's explicit no-network instruction; remote freshness unverified.
Implementation commit and exact final task head: not created (uncommitted delivery). Merge commit and post-merge verification: not applicable.
Exact-head KTX CI and KIX protocol CI run IDs/status/conclusions: unavailable / not run; supervisor owns commits and GitHub delivery. Local READY means ready for supervisor review, not merge-ready. No historical CI is inherited.

## Changed paths (complete)

- `runtime/crates/kix-feature-ir/tests/validator_matrix.rs` — seven public-API regressions.
- `scripts/check_feature_semantics_evidence_map.py` — append new test path to the citation allowlist, preserving existing indices.
- `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md` — only S10-SCHEMA-BOUND, S10-EXPR-RULES and Counts.
- `docs/README.md` — validation index bullet.
- `validation/2026-10-26-plan-feature-ir-validator-matrix-closure/README.md` — this record.

## Existing coverage mapping (before adding tests)

Test paths in this section are relative to `runtime/crates/kix-feature-ir/`.

| Requirement | Existing coverage and classification | Documented gap |
|---|---|---|
| S10-SCHEMA-BOUND: source and join-right identity/version | Partially covered: `tests/schema_bound.rs::catalog_resolution_checks_identity_version_and_duplicates` checks source resolution; `joins_require_existing_matching_keys_and_unambiguous_output_ids` checks join keys/types/collisions. | No explicit join-right identity/version rejection matrix or proof that version selects its own columns. |
| S10-SCHEMA-BOUND: column existence/types, duplicate outputs, keys, F64 input | Sufficiently covered within validator scope: `tests/schema_bound.rs::{missing_columns_are_rejected_in_expressions_aggregates_and_keys,column_types_are_checked_inside_all_operators,duplicate_output_and_key_ids_are_rejected,joins_require_existing_matching_keys_and_unambiguous_output_ids,source_f64_is_rejected_even_for_limit_only_plan}`. | Existing predicates retained and cited, rather than duplicated. |
| S10-EXPR-RULES: root division, recursion and integer types | Partially covered: `tests/schema_bound.rs::{valid_integer_expression_can_feed_terminal_division,nested_f64_in_either_operand_and_boolean_wrappers_is_rejected,column_types_are_checked_inside_all_operators,mixed_signed_unsigned_arithmetic_requires_explicit_future_conversion}`; `tests/audit_regressions.rs` root/nested/filter/type controls cited in the map. | No full I64/U64 division matrix; mixed arithmetic only tests Add in one order. |
| S4: AggregatePolicyMismatch with matching controls | Not covered for rejection: `src/lib.rs::mean_is_terminal_and_empty_is_null` validates MEAN; semantics `aggregate_empty_semantics_are_fixed` and `tests/semantics_v1_edges.rs::aggregate_empty_policy_is_exhaustive_over_aggregate_kind` cover the scalar policy table. | No plan drives AggregatePolicyMismatch. Execution/all-null dataset coverage remains absent. |

## New tests and gaps closed

All tests live in `runtime/crates/kix-feature-ir/tests/validator_matrix.rs`. Only public constructors, validation methods and `output_schema()` are used. The §4 policy table is hardcoded independently of `empty_policy()`.

| New test | Predicate/gap closed |
|---|---|
| `join_right_dataset_identity_and_version_failure_matrix` | All four join kinds: unknown identity, requested v2 absent, catalog-only v2 when requesting v1, invalid zero version and valid controls. Preflight accepts unknown identity/nonzero version without a catalog, as §10 defines. |
| `join_right_version_selects_its_own_schema` | Both versions coexist; v2 rejects v1's key, accepts its own key; Inner/Left outputs include v2's column and exclude v1's column. |
| `divide_to_f64_root_operand_type_matrix` | Full I64/U64 × I64/U64 matrix with independent literal/column/arithmetic operand forms; same-type output is TerminalF64, mixed types fail; literal cases use both validation paths; nested mixed arithmetic cannot hide in either operand. |
| `divide_to_f64_placement_and_output_kind_matrix` | Both integer types: root/output-kind mismatch, non-divide TerminalF64 mismatch, arithmetic nesting in either operand and filter comparison reject F64; root divide followed by Limit validates. |
| `implicit_signed_unsigned_coercion_is_rejected_in_compare_and_arithmetic` | All three arithmetic and six comparison operators in both mixed orders, with direct/Not/And filter forms and same-type controls, through both validation paths. |
| `aggregate_empty_policy_mismatch_is_rejected_for_every_op` | All five aggregate operations reject the wrong empty policy on both validation paths, with valid input/output kinds and no independent defect. |
| `aggregate_contract_empty_policy_control_validates` | Matched §4 controls for all five aggregate operations validate on both paths. |

## Classification, map scope and deviations

Class A: all tested §4/§10 predicates match the contract. Structural preflight accepting unresolved join-right identities/nonzero versions is the explicitly documented §10 boundary, not class B or a defect.
Class C: none found. No validator/contract/semantics changes.
Class B: no new undefined behavior probed or asserted. Error precedence between independent failures and self-join collision behavior were not tested or decided; existing map characterizations remain unchanged.

Map counts: **rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17**. The two maintainer-owned §10 rows now have cited assertions for their listed predicates within validator scope. Other rows, including every k-stage7/User/Astra-owned row, are byte-identical to HEAD.

Scope resolution follows the supplied design: S4-EMPTY-AGGREGATES stays unchanged because acceptance freezes its k-stage7 owner. The new AggregatePolicyMismatch evidence is recorded here; adding these citations/removing the rejection-gap text there is an owner follow-up. The map's statement about no existing *cited* AggregatePolicyMismatch test remains true. No map status or execution gap for S4 is changed.

The checker allowlist append and docs index bullet are necessary to cite the required new test file and index this record. The no-fetch instruction overrides AGENTS §1 for this session. No other design deviation.

## Commands actually run and results

The relevant workflow definitions were inspected: `.github/workflows/protocol.yml` (Stdlib offline document checks and Rust production runtime boundary) and `.github/workflows/ktx-kernel.yml` (architecture, kernel tests/Clippy/fmt and dependency boundary). All **53 stdlib document invocations** ran in workflow order, followed by both architecture commands. Stage-5 ran only its self-test as CI specifies. Cargo used `CARGO_NET_OFFLINE=true` and `--locked` where applicable. The foreground runner set `PYTHONDONTWRITEBYTECODE=1`; no background jobs or network actions.

No test/check failure required a fix or retry. Closest local equivalents passed; full hosted bootstrap/Move/SDK/ZK jobs were not run. This is not full hosted CI evidence. Source/governance/coverage inspection used read-only `cat`, `sed`, `rg` and git diff/ref queries.

| Command | Actual result |
|---|---|
| `git status --short; git rev-parse HEAD; git rev-parse origin/main; git branch --show-current` | Initially clean; both refs 58dd527ff53097f5231e89f25ebdf3e94586ee65; branch as recorded above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before work; both required hashes match (see Integrity). |
| `rustfmt --edition 2024 runtime/crates/kix-feature-ir/tests/validator_matrix.rs` | Exit 0; only new file formatted. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --test validator_matrix --locked` | Exit 0; 7 passed, 0 failed/ignored; narrow run first. |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17; preliminary check before broad verification. |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; 77 negative controls and injected positive control; preliminary check. |
| `python3 .local/verification/validator-matrix/checks.py` | Exit 0; foreground runner, 63 commands below passed, actual output/exit codes saved under ignored .local/verification/validator-matrix/. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir -p kix-feature-semantics --locked` | exit 0; 65 passed, 0 failed, 0 ignored; 9 result groups |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0; 275 passed, 0 failed, 0 ignored; 43 result groups |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-feature-ir --all-targets --locked -- -D warnings` | exit 0 |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0; 86 passed, 0 failed, 0 ignored; 9 result groups |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0 |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | exit 0; kix-types is the only normal dependency |
| `python3 scripts/check_status_register.py` | exit 0 |
| `python3 scripts/check_status_register.py --self-test` | exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` | exit 0 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | exit 0 |
| `python3 scripts/check_read_model_source_map.py` | exit 0 |
| `python3 scripts/check_read_model_source_map.py --self-test` | exit 0 |
| `python3 scripts/check_docs_index.py` | exit 0 |
| `python3 scripts/check_docs_index.py --self-test` | exit 0 |
| `python3 scripts/check_i12_proof_ids.py` | exit 0 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` | exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` | exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_contract_error_codes.py` | exit 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | exit 0 |
| `python3 scripts/check_adapter_identity_map.py` | exit 0 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` | exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_readiness_evidence_map.py` | exit 0 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_settlement_evidence_map.py` | exit 0 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_bra_evidence_map.py` | exit 0 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_credit_evidence_map.py` | exit 0 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | exit 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py` | exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | exit 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py` | exit 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | exit 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_bcs1_evidence_map.py` | exit 0 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py` | exit 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py` | exit 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | exit 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` | exit 0 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0 |
| `python3 scripts/check_stage5_host.py --self-test` | exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0 |
| `python3 scripts/test_runtime_architecture.py` | exit 0 |
| `python3 .local/verification/validator-matrix/audit.py` | Exit 0 before and after final record: 1,028 tracked files outside allowlist byte-identical to HEAD, including all 108 reference/v0.3-rc1 files; both locked hashes match; all other map lines unchanged; exactly five authorized changed paths. |
| `git diff --check` | Exit 0; no whitespace errors, including final check. |
| `git status --short` | Only the five paths listed above changed/new, including final check. |
| `git rev-parse HEAD origin/main` | Both remain 58dd527ff53097f5231e89f25ebdf3e94586ee65 at final verification. |
| `python3 scripts/check_docs_index.py` | Exit 0 after final record; docs index consistent. |

## Integrity and non-claims

The locked blobs before and after work match:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The final integrity audit compares every tracked file outside the allowlist to HEAD, including all `reference/v0.3-rc1/**`, locked files, source, contracts, workflows, `.aiops/` and `docs/tasks/`. No locked file was transiently mutated; rustfmt was applied only to the new file, workspace formatting was check-only.

No execution/evaluator/backend conformance, authenticated catalog/export, tolerance/depth/negative-zero policy, capability/grade change, independent clean-room proof, production readiness/durability/distributed fencing/bank exactly-once/chain finality/legal compliance is claimed. No money, real provider/bank/KYC calls, Sui network, hardware, secrets, new command or storage engine. Release mode, hosted bootstrap, Move/SDK/ZK and network jobs were not run; they do not exercise the changed tests/checker/docs, and network actions are prohibited. Local checks do not replace final-head CI or non-author review, which remain supervisor follow-ups.
