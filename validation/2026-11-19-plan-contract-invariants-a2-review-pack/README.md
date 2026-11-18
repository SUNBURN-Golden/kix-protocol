# Contract invariants A2 review pack validation

Task `plan-plan-contract-invariants-a2-review-pack`. The supervisor's node
specification and owner decision are the immutable task input. The node has
no issue or task file under `docs/tasks/`. Date 2026-11-19.

## Basis and delivery

- Branch `agent/kix-plan-plan-contract-invariants-a2-review-pack`. Starting
  and ending Git HEAD / task base `307f913fece040f3c735304555c3279dfb424f6b`.
  Cached `origin/main` was `5be902b5cd7d314e9e7d05ab919597385896e48f`.
  `git rev-list --left-right --count HEAD...origin/main` reported `0 296`.
  The supervisor prohibited network actions, including fetch. The checked-out
  branch supplied the sources and the base remained fixed. The cached main
  has the same twelve A2 row IDs, with later edits to the test and Gap
  cells for S5-SAFE-REJECT and S5-PRECEDENCE and the text of F-B5 and F-B6.
  An integration against that base requires synchronizing those copies and
  validating the integrated tree.
- The implementation is the uncommitted worktree patch. A committed
  implementation or final delivery SHA, merge SHA, exact-head KTX and KIX
  hosted run IDs/status/conclusions, and post-merge main CI are unavailable in
  this session. The supervisor owns publication and hosted CI.
- Changed paths
  - `docs/status/CONTRACT_INVARIANTS_REVIEW_PACK.md`
  - `scripts/check_contract_invariants_review_pack.py`
  - `.github/workflows/protocol.yml`
  - `docs/README.md`
  - `validation/2026-11-19-plan-contract-invariants-a2-review-pack/README.md`
- Locked worktree blobs, verified before edits and after the local checks
  - `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
  - `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`
- `DECISION_REQUIRED.md` was absent at the start and close of this build.

## Existing coverage and remaining review questions

The [pack](../../docs/status/CONTRACT_INVARIANTS_REVIEW_PACK.md) maps the
twelve A2-owned table rows and the five verbatim F-B2–F-B6 prose findings per
the owner's decision. The findings supply text and questions. Their source has
no Status or Gap cells.

| Existing coverage | Evidence and boundary |
|---|---|
| Partial — provenance, shared interpretation and retained E-4 regression | E-4 finite traces and the kernel-only predicate suite exercise different paths. The source identity/format diagnostic and finite differential agreement leave specification independence open. |
| Partial — bounded records, immutable first results, observed order IDs and reply probes | Corpus, post-state probes, deterministic examples and observer-copy sensitivity cover public predicates. Private allocation, admitted-time observation and source-informed exact reply semantics retain the map's caveats. |
| Partial — availability, error precedence and finite-corpus vacuity | Held examples and guard pairs exercise the stated cases. The pack carries the source's class B findings, with both versions of the F-B3 context visible through the original finding and narrowed S4-PROBES gap. |
| Not covered / open — exact-head execution and shared-error oracle | Exact-head KTX and KIX run evidence and independently derived specification provenance remain open. |
| Sufficient for checking the source map, missing for the review pack before this node | The existing map and rollup checkers validate the original table and counts. The new stdlib checker checks the pack-owned entries, verbatim excerpts and cells, test declarations and exact commands. Its in-memory self-test covers omissions, additions, source-copy edits, a nonexistent symbol, an incorrect command and inserted verdict words. |

No runtime tests were added. The builder recorded command exits and left all
review questions open. The pack retains the recorded class B characterizations.
The mechanical checks and test executions identified no new explicit contract
violation. Local source comparisons and test results cover the checked-out,
finite in-memory evidence. Non-author review, production behavior, durability,
distributed fencing, chain authority and external provider behavior are outside
the evidence recorded here.

## Cited test commands

Commands ran once per distinct invocation, with `CARGO_NET_OFFLINE=true` and
a scratch `CARGO_TARGET_DIR`. Each reported one passing test, zero failures and
zero ignored. The 51 commands cover 49 v4 and two v5 citations.

| Command | Result |
|---|---|
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked locked_v4_matches_independent_state_model -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked contract_test_source_identity_and_format_diagnostic -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked contract_predicates_reject_corrupted_observations_not_kernel_mutations -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked unrelated_event_flood_cannot_starve_promised_capture -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked bounded_records_backpressure_without_evicting_old_results -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked response_loss_retry_returns_original_before_availability_check -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked rejection_replay_stays_immutable_after_the_blocking_hold_is_released -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked reply_oracle_rejects_deliberately_wrong_expected_replies -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked reservation_has_inventory_order_and_stable_external_intent -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked free_contiguous_range_inside_one_actual_segment_is_held -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked word_crossing_range_inside_one_segment_is_held_between_neighbours -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked seats_and_general_admission_are_held_up_to_exact_remaining_capacity -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked inventory_released_by_expiry_is_reusable_by_a_new_command -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked success_follows_unrelated_rejections_errors_and_replays -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked smallest_positive_price_and_one_millisecond_ttl_are_held -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_before_fence_and_clock_guards -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked replay_lookup_is_guarded_by_scope_and_semantics_only -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_after_local_cancellation -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_at_full_command_capacity -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_when_its_selection_is_unavailable -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_when_its_operation_is_quarantined -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_without_touching_an_unknown_payment -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_records_nothing_after_local_cancellation -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_records_no_unavailable_rejection -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_applies_no_quarantine -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_neither_sends_nor_captures_an_unknown_payment -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_records_nothing_after_local_cancellation -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_after_local_cancellation -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_records_no_unavailable_rejection -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_applies_no_quarantine -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_neither_sends_nor_captures_an_unknown_payment -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_records_no_unavailable_rejection -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_applies_no_quarantine -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_applies_no_capture_to_an_unknown_payment -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_before_an_unavailable_rejection -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_before_a_quarantine_rejection -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked bound_quarantine_survives_owner_change_expiry_and_cancellation -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked late_capture_after_cancellation_creates_return_marker_not_resurrection -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked event_conflict_quarantines_both_bound_orders_and_blocks_payment_sending -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked reviewed_late_capture_keeps_return_marker_and_review_requirement -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked conflict_capacity_failure_keeps_quarantine_and_original_evidence -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked conflict_naming_unbound_operation_blocks_future_binding_without_changing_replays -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked full_observation_budget_blocks_first_unknown_without_state_change -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked conflicting_event_cannot_spend_slot_reserved_for_capture -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked reserved_slot_survives_expiry_check_owner_change_and_cancellation -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked full_budget_new_conflict_quarantines_without_retaining_evidence -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test termination --locked automatic_approval_is_rejected_before_order_checks -- --exact` | Exit 0, 1 passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test termination --locked a_false_condition_wins_over_a_stale_snapshot -- --exact` | Exit 0, 1 passed |

## Local CI equivalents

The narrow pack and acceptance checks ran before the broader CI commands.
The unchanged evidence-map, rollup and docs-index checks also passed at the
initial baseline. Local tools were Python 3.13.5, Cargo 1.98.1 and rustc 1.98.1.
Cargo ran with networking disabled and used a temporary target directory.

| Narrow command | Result |
|---|---|
| `python3 scripts/check_contract_invariants_review_pack.py` | Exit 0, twelve rows and five findings checked |
| `python3 scripts/check_contract_invariants_review_pack.py --self-test` | Exit 0, 11 negative controls detected |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0, 35 checkers and 23 status documents checked |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0, 13 negative controls detected |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0, 27 rows and locked blobs checked |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0, two positive and 66 negative controls |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0, 25 contracts checked |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0, 16 negative controls detected |
| `python3 scripts/check_docs_index.py` | Exit 0, 295 scanned and 260 indexed with 35 allowlisted |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0, seven negative controls detected |

| Architecture and Rust verification command | Result |
|---|---|
| `python3 scripts/verify_runtime_architecture.py` | Exit 0 |
| `python3 scripts/test_runtime_architecture.py` | Exit 0, seven tests ran successfully |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0, 122 passed, 0 failed, 0 ignored |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0, 317 passed, 0 failed, 0 ignored |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0 |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0, kix-types is the only normal dependency |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0, recorded below |

KTX source SHA-256 values

- `runtime/Cargo.lock` `a948a1b687de2727ad717db0f7a0aa4159ecf5258e52e18eccf05cc08329d83e`
- `runtime/crates/kix-kernel/src/lib.rs` `84c8ef6cca3eb3eafc842639b32580c21b88731b34e83490db2fa84eecb1657f`
- `runtime/crates/kix-kernel/tests/transitions.rs` `d404aa9bade8d9997872d0537a40813d49cbff1f6b60bf13bc385d613fc42bae`

### Protocol stdlib step

Ran all 63 commands from the `Stdlib offline document checks` run block in
`.github/workflows/protocol.yml` sequentially. The loopback preflight checked
local ephemeral binds on 127.0.0.1. This run used no external endpoints.

<details>
<summary>Stdlib commands and exits</summary>

| Command | Result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0 |
| `python3 scripts/check_read_model_source_map.py` | Exit 0 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0 |
| `python3 scripts/check_docs_index.py` | Exit 0 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0 |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_contract_error_codes.py` | Exit 0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0 |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0 |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0 |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_contract_invariants_review_pack.py` | Exit 0 |
| `python3 scripts/check_contract_invariants_review_pack.py --self-test` | Exit 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0 |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0 |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0 |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0 |
| `python3 scripts/check_class_b_index.py` | Exit 0 |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0 |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0 |
| `python3 scripts/check_loopback_host.py` | Exit 0 |
| `python3 scripts/check_loopback_host.py --self-test` | Exit 0 |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0 |

</details>

### Worktree verification and deviations

| Command | Result |
|---|---|
| `git status --short --branch` | Requested branch, initial clean worktree, 296 commits behind the cached origin/main ref |
| `git rev-parse HEAD` | Exit 0, `307f913fece040f3c735304555c3279dfb424f6b` before and after |
| `git rev-parse --verify refs/remotes/origin/main` | Exit 0, cached `5be902b5cd7d314e9e7d05ab919597385896e48f` |
| `git diff HEAD origin/main -- docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md` | Exit 0, later map revisions present in cached main |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0, both required blobs matched before edits and after checks |
| `git diff --exit-code --no-ext-diff HEAD -- docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md docs/contracts/CONTRACT_INVARIANTS.md runtime/ reference/ .aiops/ docs/tasks/` | Exit 0, no protected-path diff |
| `git ls-files --others --exclude-standard -- docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md docs/contracts/CONTRACT_INVARIANTS.md runtime/ reference/ .aiops/ docs/tasks/` | Exit 0, no untracked protected paths |
| `git diff --check` | Exit 0 |
| `git diff --no-index --check -- /dev/null <new path>`, once per new file | No whitespace diagnostics. Exit 1 reports the file differs from the empty input |
| `git status --short --untracked-files=all` | Exit 0, the five changed paths listed above |
| `test ! -e DECISION_REQUIRED.md` | Exit 0 |

The design stop was resolved by the owner's decision before implementation.
F-B2–F-B6 are checked against the map as prose findings. The map's narrowed
S4-PROBES Gap and its earlier F-B3 finding are both preserved verbatim for the
reviewer to reconcile. The full hosted workflows, bootstrap, SDK, local chain,
ZK and provider journeys were outside the touched-path local check scope.
Remote main freshness, exact-head CI and non-author review remain open.
