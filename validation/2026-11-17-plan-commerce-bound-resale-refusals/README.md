# Settlement-bound resale refusal companion pack — builder evidence

Node: `plan-commerce-bound-resale-refusals`; no issue. Task input is the
supervisor-provided node specification and read-only design plan in the user
request, not a newly created `docs/tasks/` document. This is not ASTRA program
mode. Scope is test replay, new fixtures, consumer guidance and validation.

Local observed `origin/main`, base and branch HEAD at start:
`d26f12657d84146886055ac78492cf2df81cd529` on
`agent/kix-plan-commerce-bound-resale-refusals`. No base delta locally.
The supervisor explicitly prohibited GitHub/network actions, so `git fetch`
was not run; currency against remote main is unverified. No commit, push,
branch creation, issue, PR, comment or merge is performed in this builder
session. Implementation/final committed head and merge SHA are not assigned.

See the [consumer guide](../../reference/booking_resale_admission/README.md#commerce-settlement-bound-resale-refusal-vectors),
[coverage mapping](coverage.md), [exact commands/results](commands.json),
[new artifact identities](artifacts.json), [changed-path inventory](changed-paths.txt),
and [before](preservation-before.json)/[after](preservation-after.json)
preservation inventories. Each command record links its complete stdout/stderr
log and actual exit code. An initial focused run detected two mutation-control
assertion-message mismatches; the controls already detected the injected faults.
The expected messages/input mutation were corrected locally and the focused
suite rerun. No FSM fix was required.

Both kernel locks matched before editing:
`runtime/crates/kix-kernel/src/lib.rs` → `69564b166f0c27f9af5d8422f0a466b18d74c20f`;
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs` →
`b607996c83a119c349f1cc90469ac1ba82764e20`.
The preservation inventory covers every initially tracked file except the two
authorized README edits, including all `reference/v0.3-rc1/**`, FSMs, contracts,
catalogue, SDK, prior packs, consumer binding index, CI, `.aiops/` and task docs.
Final verification: both locked blobs match after work, all 3,924 inventoried
existing tracked files match their before identities, including all 108 frozen
reference files. The two README edits are the only changed pre-existing paths.
The after inventory is complete. `check_preservation.py` performs a read-only
recheck of identities and the node's changed-path allowlist.

KTX exact-head hosted CI: not requested/observed; run ID/status/conclusion N/A.
KIX exact-head hosted CI: not requested/observed; run ID/status/conclusion N/A.
A2 non-author exact-head review: outstanding, not performed by the builder.
Post-merge main checks and locked blob checks: N/A, no merge. Local results do
not establish merge readiness or satisfy the hosted gates.

No prohibited resources or policy decisions were needed. Existing source
contracts match observations; no contract violation found. Rejected keys remain
process-local outside accepted journals; restoration is not tested or claimed.
All 13 reads remain NOT_BOUND, semantic SDK consumption HOLD_SEMANTIC, SD1
OPEN/User-owned and policy values UNDETERMINED with existing owners. No automatic
retry or new command, external call, production runtime, real funds/provider,
chain execution, storage engine, durability, legal compliance, independent
consumer qualification or production-readiness claim.

Deviations: the no-network supervisor instruction replaces AGENTS.md's fetch;
remote currency remains unverified. The last design paragraph's planning-session
read-only caveat does not constrain this explicitly write-authorized builder
session. The new suite additionally enforces unrelated-machine preservation at
every command and effect-free accepted replay. The full protocol workflow's
installation, local-chain, ZK and storage jobs are outside the touched test/doc
paths and were not run. No workflow edits were made.


## Final local results

All required local checks passed after correcting the two mutation-control
message/input mismatches documented above. Focused resale: 9 tests; new vector
suite: 12 tests; all Commerce suites: 128 tests. Kernel tests: 139 passed across
seven integration binaries, plus zero-test library/doc targets; Clippy and
formatting passed. Runtime architecture verification and its 7 tests passed.
The additional offline-limit suite passed 9 tests. The 67 literal document
commands extracted from `protocol.yml` passed, including normal/self-test
producer, consumer-binding, document, OpenAPI-related evidence and discovery
checks. The OpenAPI contract and integration-gate OpenAPI checkers passed in
both normal and self-test modes, separately from that document block.

| Offline reference suite (workflow order) | Actual tests passed |
|---|---:|
| `settlement_f01_f03` | 224 |
| `booking_resale_admission` | 1018 |
| `credit_advance_f04` | 270 |
| `ai_delegation` | 169 |
| `token_reward` | 397 |
| `provider_facts` | 86 |
| `payment_effects` | 28 |
| `economics` | 99 |

The broad reference suites include existing local loopback tests. The new
vectors themselves call only the unchanged in-process host. Plain loopback-host
and cargo-cache reports describe this host/cache only, not production readiness.
No tests were skipped or left unavailable within the selected local check set.
Full workflow installation, chain/ZK/storage jobs were not selected for these
Python test/fixture/document changes; hosted CI remains unobserved.

## Actual command evidence

All command rows below are actual executions. Complete stdout/stderr is linked;
`commands.json`, `docs-commands.json`, `ktx-commands.json`, `limits-commands.json`
and `final-commands.json` preserve the machine-readable results and durations.
The single initial failure is retained rather than overwritten.

| Command | Actual result | Log |
|---|---|---|
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_resale_fsm.py -v` | PASS (exit 0) | [001.log](001.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_bound_resale_vectors.py -v` | INITIAL FAIL (exit 1); corrected and rerun | [002.log](002.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_bound_resale_vectors.py -v` | PASS (exit 0) | [003.log](003.log) |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p 'test_commerce_*.py' -v` | PASS (exit 0) | [004.log](004.log) |
| `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward provider_facts payment_effects economics; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" \|\| exit $?; done` | PASS (exit 0) | [005.log](005.log) |
| `python3 -B scripts/check_openapi_contract.py` | PASS (exit 0) | [006.log](006.log) |
| `python3 -B scripts/check_openapi_contract.py --self-test` | PASS (exit 0) | [007.log](007.log) |
| `python3 -B scripts/check_integration_gate_openapi.py` | PASS (exit 0) | [008.log](008.log) |
| `python3 -B scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0) | [009.log](009.log) |
| `python3 -B scripts/check_status_register.py` | PASS (exit 0) | [docs-001.log](docs-001.log) |
| `python3 -B scripts/check_status_register.py --self-test` | PASS (exit 0) | [docs-002.log](docs-002.log) |
| `python3 -B scripts/check_producer_qualification_tuple.py` | PASS (exit 0) | [docs-003.log](docs-003.log) |
| `python3 -B scripts/check_producer_qualification_tuple.py --self-test` | PASS (exit 0) | [docs-004.log](docs-004.log) |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` | PASS (exit 0) | [docs-005.log](docs-005.log) |
| `python3 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py --self-test` | PASS (exit 0) | [docs-006.log](docs-006.log) |
| `python3 -B scripts/check_rs_profile_traceability.py` | PASS (exit 0) | [docs-007.log](docs-007.log) |
| `python3 -B scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0) | [docs-008.log](docs-008.log) |
| `python3 -B scripts/check_read_model_source_map.py` | PASS (exit 0) | [docs-009.log](docs-009.log) |
| `python3 -B scripts/check_read_model_source_map.py --self-test` | PASS (exit 0) | [docs-010.log](docs-010.log) |
| `python3 -B scripts/check_docs_index.py` | PASS (exit 0) | [docs-011.log](docs-011.log) |
| `python3 -B scripts/check_docs_index.py --self-test` | PASS (exit 0) | [docs-012.log](docs-012.log) |
| `python3 -B scripts/check_i12_proof_ids.py` | PASS (exit 0) | [docs-013.log](docs-013.log) |
| `python3 -B scripts/check_i12_proof_ids.py --self-test` | PASS (exit 0) | [docs-014.log](docs-014.log) |
| `python3 -B scripts/check_delegation_layer_matrix.py` | PASS (exit 0) | [docs-015.log](docs-015.log) |
| `python3 -B scripts/check_delegation_layer_matrix.py --self-test` | PASS (exit 0) | [docs-016.log](docs-016.log) |
| `python3 -B scripts/check_rs_predicate_evidence_map.py` | PASS (exit 0) | [docs-017.log](docs-017.log) |
| `python3 -B scripts/check_rs_predicate_evidence_map.py --self-test` | PASS (exit 0) | [docs-018.log](docs-018.log) |
| `python3 -B scripts/check_rs_im_evidence_map.py` | PASS (exit 0) | [docs-019.log](docs-019.log) |
| `python3 -B scripts/check_rs_im_evidence_map.py --self-test` | PASS (exit 0) | [docs-020.log](docs-020.log) |
| `python3 -B scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0) | [docs-021.log](docs-021.log) |
| `python3 -B scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0) | [docs-022.log](docs-022.log) |
| `python3 -B scripts/check_contract_error_codes.py` | PASS (exit 0) | [docs-023.log](docs-023.log) |
| `python3 -B scripts/check_contract_error_codes.py --self-test` | PASS (exit 0) | [docs-024.log](docs-024.log) |
| `python3 -B scripts/check_adapter_identity_map.py` | PASS (exit 0) | [docs-025.log](docs-025.log) |
| `python3 -B scripts/check_adapter_identity_map.py --self-test` | PASS (exit 0) | [docs-026.log](docs-026.log) |
| `python3 -B scripts/check_v5_transition_evidence_map.py` | PASS (exit 0) | [docs-027.log](docs-027.log) |
| `python3 -B scripts/check_v5_transition_evidence_map.py --self-test` | PASS (exit 0) | [docs-028.log](docs-028.log) |
| `python3 -B scripts/check_readiness_evidence_map.py` | PASS (exit 0) | [docs-029.log](docs-029.log) |
| `python3 -B scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0) | [docs-030.log](docs-030.log) |
| `python3 -B scripts/check_settlement_evidence_map.py` | PASS (exit 0) | [docs-031.log](docs-031.log) |
| `python3 -B scripts/check_settlement_evidence_map.py --self-test` | PASS (exit 0) | [docs-032.log](docs-032.log) |
| `python3 -B scripts/check_bra_evidence_map.py` | PASS (exit 0) | [docs-033.log](docs-033.log) |
| `python3 -B scripts/check_bra_evidence_map.py --self-test` | PASS (exit 0) | [docs-034.log](docs-034.log) |
| `python3 -B scripts/check_credit_evidence_map.py` | PASS (exit 0) | [docs-035.log](docs-035.log) |
| `python3 -B scripts/check_credit_evidence_map.py --self-test` | PASS (exit 0) | [docs-036.log](docs-036.log) |
| `python3 -B scripts/check_primary_price_fee_evidence_map.py` | PASS (exit 0) | [docs-037.log](docs-037.log) |
| `python3 -B scripts/check_primary_price_fee_evidence_map.py --self-test` | PASS (exit 0) | [docs-038.log](docs-038.log) |
| `python3 -B scripts/check_ai_delegation_evidence_map.py` | PASS (exit 0) | [docs-039.log](docs-039.log) |
| `python3 -B scripts/check_ai_delegation_evidence_map.py --self-test` | PASS (exit 0) | [docs-040.log](docs-040.log) |
| `python3 -B scripts/check_lifecycle_adr_evidence_map.py` | PASS (exit 0) | [docs-041.log](docs-041.log) |
| `python3 -B scripts/check_lifecycle_adr_evidence_map.py --self-test` | PASS (exit 0) | [docs-042.log](docs-042.log) |
| `python3 -B scripts/check_contract_invariants_evidence_map.py` | PASS (exit 0) | [docs-043.log](docs-043.log) |
| `python3 -B scripts/check_contract_invariants_evidence_map.py --self-test` | PASS (exit 0) | [docs-044.log](docs-044.log) |
| `python3 -B scripts/check_toss_card_profile_evidence_map.py` | PASS (exit 0) | [docs-045.log](docs-045.log) |
| `python3 -B scripts/check_toss_card_profile_evidence_map.py --self-test` | PASS (exit 0) | [docs-046.log](docs-046.log) |
| `python3 -B scripts/check_bcs1_evidence_map.py` | PASS (exit 0) | [docs-047.log](docs-047.log) |
| `python3 -B scripts/check_bcs1_evidence_map.py --self-test` | PASS (exit 0) | [docs-048.log](docs-048.log) |
| `python3 -B scripts/check_performance_measurement_evidence_map.py` | PASS (exit 0) | [docs-049.log](docs-049.log) |
| `python3 -B scripts/check_performance_measurement_evidence_map.py --self-test` | PASS (exit 0) | [docs-050.log](docs-050.log) |
| `python3 -B scripts/check_feature_semantics_evidence_map.py` | PASS (exit 0) | [docs-051.log](docs-051.log) |
| `python3 -B scripts/check_feature_semantics_evidence_map.py --self-test` | PASS (exit 0) | [docs-052.log](docs-052.log) |
| `python3 -B scripts/check_integration_gate_contract_evidence_map.py` | PASS (exit 0) | [docs-053.log](docs-053.log) |
| `python3 -B scripts/check_integration_gate_contract_evidence_map.py --self-test` | PASS (exit 0) | [docs-054.log](docs-054.log) |
| `python3 -B scripts/check_evidence_map_rollup.py` | PASS (exit 0) | [docs-055.log](docs-055.log) |
| `python3 -B scripts/check_evidence_map_rollup.py --self-test` | PASS (exit 0) | [docs-056.log](docs-056.log) |
| `python3 -B scripts/check_class_b_index.py` | PASS (exit 0) | [docs-057.log](docs-057.log) |
| `python3 -B scripts/check_class_b_index.py --self-test` | PASS (exit 0) | [docs-058.log](docs-058.log) |
| `python3 -B scripts/check_ci_checker_wiring.py` | PASS (exit 0) | [docs-059.log](docs-059.log) |
| `python3 -B scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0) | [docs-060.log](docs-060.log) |
| `python3 -B scripts/check_ci_test_discovery.py` | PASS (exit 0) | [docs-061.log](docs-061.log) |
| `python3 -B scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0) | [docs-062.log](docs-062.log) |
| `python3 -B scripts/check_loopback_host.py` | PASS (exit 0) | [docs-063.log](docs-063.log) |
| `python3 -B scripts/check_loopback_host.py --self-test` | PASS (exit 0) | [docs-064.log](docs-064.log) |
| `python3 -B scripts/check_cargo_offline_cache.py` | PASS (exit 0) | [docs-065.log](docs-065.log) |
| `python3 -B scripts/check_cargo_offline_cache.py --self-test` | PASS (exit 0) | [docs-066.log](docs-066.log) |
| `python3 -B scripts/check_stage5_host.py --self-test` | PASS (exit 0) | [docs-067.log](docs-067.log) |
| `python3 -B scripts/verify_runtime_architecture.py` | PASS (exit 0) | [ktx-001.log](ktx-001.log) |
| `python3 -B scripts/test_runtime_architecture.py` | PASS (exit 0) | [ktx-002.log](ktx-002.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | PASS (exit 0) | [ktx-003.log](ktx-003.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | PASS (exit 0) | [ktx-004.log](ktx-004.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) | [ktx-005.log](ktx-005.log) |
| `python3 -B -m unittest integration_gate.test_offline_limits` | PASS (exit 0) | [limits-001.log](limits-001.log) |
| `python3.12 -B validation/2026-11-17-plan-commerce-bound-resale-refusals/check_preservation.py` | PASS (exit 0) | [final-001.log](final-001.log) |
| `git diff --check` | PASS (exit 0) | [final-002.log](final-002.log) |
| `python3 -B scripts/check_docs_index.py` | PASS (exit 0) | [final-003.log](final-003.log) |
| `python3 -B scripts/check_docs_index.py --self-test` | PASS (exit 0) | [final-004.log](final-004.log) |
| `python3.12 -B validation/2026-11-17-plan-commerce-bound-resale-refusals/check_preservation.py` | PASS (exit 0) | [final-005.log](final-005.log) |
| `git diff --check` | PASS (exit 0) | [final-006.log](final-006.log) |
| `git rev-parse origin/main HEAD` | PASS (exit 0) | [final-007.log](final-007.log) |
