# Contract invariants review pack

Builder-authored evidence and questions for the non-author A2 reviewer.

## 0. Basis

- Node `plan-plan-contract-invariants-a2-review-pack`. The supervisor's node specification and owner decision are the task input.
- The [evidence map](CONTRACT_INVARIANTS_EVIDENCE_MAP.md) and [contract](../contracts/CONTRACT_INVARIANTS.md) are quoted from task base `307f913fece040f3c735304555c3279dfb424f6b`. The [validation record](../../validation/2026-11-19-plan-contract-invariants-a2-review-pack/README.md) records the base delta, locked blobs and local command exits.
- Run `scripts/check_contract_invariants_review_pack.py` through the protocol workflow's stdlib step, or run it locally with `python3` in plain and `--self-test` mode. It checks source copies, test citations and pack structure. Rust execution is recorded separately.
- Answer each numbered question against the exact delivery commit. Record the cited source or execution evidence for each answer and identify any evidence still needed.

**Map provenance caveat**

```text
Test cells are literal none or comma-separated backticked repo-relative path::symbol citations to existing #[test] fns. Contract-path permits the v4 contract_invariants, contract_edge_cases, transitions and observation_slots test files, and v5 test files except lifecycle_model and v4_differential. Source-informed permits only v4 e4_state_model and v5 lifecycle_model/v4_differential. As contract §1 says, this is an “independent oracle PATH”; the split describes the oracle path, not authorship. The author knew the kernel source. This map makes no clean-room or independence claim. Historical symbols containing independent are literal identifiers only.
```

## 1. A2-owned map rows

### S1-MODEL-PROVENANCE

**Contract clauses**

```text
The author read the kernel source while writing `tests/support/model_v4.rs`.
Its reserve guard order, including original-result lookup before execution/time
checks, follows that implementation. Data representation is separate (owner array
and Vec rather than the kernel bitmap/maps), and it does not call Kernel for an
expected result, but this is NOT independently derived specification provenance.
The 131,072 prior comparisons establish finite-trace agreement, not which side
is correct. A shared misunderstanding can survive both. The old source and raw
results are preserved rather than rewritten to appear independent.
```

**Status**

PARTIAL

**Gap**

Finite-trace agreement only; shared misunderstanding can survive (F-B4)

**Test evidence**

- Source-informed `runtime/crates/kix-kernel/tests/e4_state_model.rs::locked_v4_matches_independent_state_model`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked locked_v4_matches_independent_state_model -- --exact`

**Caveat**

The map provenance caveat applies to E-4. Its separate representation and finite trace comparisons leave common guard-order and specification errors possible.

**Reviewer questions**

1. Which reserve guards or transitions are interpreted from the same source on both sides of the comparison?
2. Which conclusions about the finite traces can the reviewer reproduce from the model and corpus provenance?

### S1-ORACLE-PATH

**Contract clauses**

```text
The new `tests/contract_invariants.rs` imports neither model_v4 nor its generator,
replies or guard-order logic. It feeds one kernel, observes its public history and
checks contract predicates. Its author still knows the kernel source; this is an
independent oracle PATH, not a claim of clean-room authorship or formal proof.
```

**Status**

PARTIAL

**Gap**

Author knew kernel source; source identity/format diagnostic establishes neither authorship separation nor semantic coverage

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::contract_test_source_identity_and_format_diagnostic`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked contract_test_source_identity_and_format_diagnostic -- --exact`

**Caveat**

The map provenance caveat distinguishes the kernel-only observation path from the source-informed author. The source diagnostic checks identity and format.

**Reviewer questions**

1. Does the kernel-only predicate path derive its expected observations without calling or importing the E-4 model, generator or guard-order logic?
2. Which checks establish source identity or format, and which assert observable semantics?

### INV-2

**Contract clauses**

```text
| INV-2 | Observation budget includes stored events + conflicts + reserved slots and stays bounded | Checked sum of three public counters <= configured bound. order_count and quarantine count checked; observed distinct completed commands <= command cap. | A §8; L §2; R Observation reservation |
```

**Status**

PARTIAL

**Gap**

Private command-map allocation unmeasured; completed commands are observed through public replies only

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::contract_predicates_reject_corrupted_observations_not_kernel_mutations`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked contract_predicates_reject_corrupted_observations_not_kernel_mutations -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::unrelated_event_flood_cannot_starve_promised_capture`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked unrelated_event_flood_cannot_starve_promised_capture -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::bounded_records_backpressure_without_evicting_old_results`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked bounded_records_backpressure_without_evicting_old_results -- --exact`

**Caveat**

The map scopes bounded counts to public counters and order/reply observations. A common source interpretation can survive a finite predicate check.

**Reviewer questions**

1. Do the cited tests account for stored events, conflicts, reserved observation slots, quarantines and bounded order and command records at the public boundary stated in §3?
2. Which conclusions about private allocation or unobserved commands would require evidence beyond these public counts and replies?

### INV-3

**Contract clauses**

```text
| INV-3 | A completed command's first result cannot change | Save the first observed typed payload/result, then re-request it after every main step with its original context; require replayed=true and same original. An Eq clone only detects mutation by the read-only probe, not recovery. | A §3/§5; L §2 command row |
```

**Status**

PARTIAL

**Gap**

Corrupted-view sensitivity added (F-B2 narrowed); admitted time has no public accessor and is witnessed only by the whole-kernel Eq sentinel; fixture is source-informed

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::response_loss_retry_returns_original_before_availability_check`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked response_loss_retry_returns_original_before_availability_check -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::rejection_replay_stays_immutable_after_the_blocking_hold_is_released`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked rejection_replay_stays_immutable_after_the_blocking_hold_is_released -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations -- --exact`

**Caveat**

F-B2 records a source-informed observer-copy fixture and the whole-kernel Eq sentinel for admitted time. Replay probes cover the observed command result path.

**Reviewer questions**

1. Do the probes and deterministic examples require the original typed first result for Held and Rejected after later state changes?
2. Does the sensitivity test exercise the corpus replay predicate and what state can the public observations and Eq sentinel each establish?

### S3-OBS-BOUNDARY

**Contract clauses**

```text
All attempted order IDs are recorded, including rejected ones, and their observed
order count must agree with the kernel's public count. This prevents silently
ignoring a known created order. Private maps/bitmap are not exposed or changed;
physical command-map allocation beyond the public boundary is not measured.
The observed-command limit is not a claim to inspect the private commands map.
```

**Status**

PARTIAL

**Gap**

Physical private-map/bitmap allocation unmeasured; observed-command limit is only a public boundary

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact`

**Caveat**

The observed order IDs and public counts define this evidence boundary. Physical allocation remains outside the cited observation.

**Reviewer questions**

1. Does the harness retain all attempted order IDs, including rejected ones, and reconcile the observed orders with the public order count?
2. Which public-state conclusions follow from the observed-command records, and which would require private allocation inspection?

### S4-PROBES

**Contract clauses**

```text
Read-only replay probes are reported separately and are not counted as new
commands or successful purchases. Every reply, including Err(Capacity), is checked.
```

**Status**

PARTIAL

**Gap**

All non-reserve replies asserted; exact reply encodings, send precedence/TTL retry refusal and owner/cancel admission remain source-informed class B characterizations (F-B3 narrowed); see validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::reply_oracle_rejects_deliberately_wrong_expected_replies`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked reply_oracle_rejects_deliberately_wrong_expected_replies -- --exact`

**Caveat**

The copied Gap records source-informed class B reply details and the narrowing of F-B3. The verbatim F-B3 finding retains its earlier wording.

**Reviewer questions**

1. Are ordered corpus calls and replay probes counted separately, and are the post-state predicates applied after every main reply including errors?
2. Which typed reply values does the cited oracle now assert, and where do encodings, precedence or admission remain class B?

### S4-CI-HEAD

**Contract clauses**

```text
Execution results are attached to their exact later CI head, not implied here.
```

**Status**

NOT_COVERED

**Gap**

Local working-tree checks do not establish final-head hosted CI; no committed delivery head yet

**Test evidence**

None.

**Caveat**

The map defines a provenance gap for hosted execution. A working-tree exit or source-informed comparison supplies no hosted run identity.

**Reviewer questions**

1. What exact delivery commit and KTX and KIX run IDs, statuses and conclusions establish the execution provenance required by §4?
2. Do the run records identify that commit and show that the relevant verification steps actually executed?

### S5-SAFE-REJECT

**Contract clauses**

```text
These five predicates detect visible overlap/accounting breaks, over-budget state,
changed first outcomes, duplicate operation capture and capture loss without a
reference state machine. They can still miss incorrect but safe rejections, wrong
error precedence, an unnecessarily sticky hold, and exact phase/review semantics
not expressed by a predicate. A full transition oracle or explicit contract-based
example is needed for those questions. The current source-informed model can
expose DIFFERENCES on them; it cannot resolve shared errors by itself.
```

**Status**

PARTIAL

**Gap**

Explicit contract-based success examples cover single-segment and word-crossing seat ranges, seat and GA requests up to exact remaining capacity, expiry reuse, the last command/order slots, the smallest positive price with a 1 ms TTL, and success after unrelated rejections, errors and replays on seat and GA fixtures; finite source-informed examples and model agreement do not establish availability over all valid inputs; cancellation reuse, ReturnRequired reuse, the bundle maximum, inclusive limits and exact variants remain class B (F-B5)

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::reservation_has_inventory_order_and_stable_external_intent`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked reservation_has_inventory_order_and_stable_external_intent -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::free_contiguous_range_inside_one_actual_segment_is_held`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked free_contiguous_range_inside_one_actual_segment_is_held -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::word_crossing_range_inside_one_segment_is_held_between_neighbours`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked word_crossing_range_inside_one_segment_is_held_between_neighbours -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::seats_and_general_admission_are_held_up_to_exact_remaining_capacity`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked seats_and_general_admission_are_held_up_to_exact_remaining_capacity -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::inventory_released_by_expiry_is_reusable_by_a_new_command`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked inventory_released_by_expiry_is_reusable_by_a_new_command -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::success_follows_unrelated_rejections_errors_and_replays`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked success_follows_unrelated_rejections_errors_and_replays -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::smallest_positive_price_and_one_millisecond_ttl_are_held`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked smallest_positive_price_and_one_millisecond_ttl_are_held -- --exact`
- Source-informed `runtime/crates/kix-kernel/tests/e4_state_model.rs::locked_v4_matches_independent_state_model`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked locked_v4_matches_independent_state_model -- --exact`

**Caveat**

The examples are finite and source-informed even where their expected outcomes are traced to clauses. E-4 agreement leaves shared availability errors possible.

**Reviewer questions**

1. Which clauses require the successes asserted by each cited availability example?
2. Which additional valid-input rejections could remain undetected, and which cited boundary observations are class B under F-B5?

### S5-PRECEDENCE

**Contract clauses**

```text
These five predicates detect visible overlap/accounting breaks, over-budget state,
changed first outcomes, duplicate operation capture and capture loss without a
reference state machine. They can still miss incorrect but safe rejections, wrong
error precedence, an unnecessarily sticky hold, and exact phase/review semantics
not expressed by a predicate. A full transition oracle or explicit contract-based
example is needed for those questions. The current source-informed model can
expose DIFFERENCES on them; it cannot resolve shared errors by itself.
```

**Status**

PARTIAL

**Gap**

Validation pair matrix tests or cites every guard pair whose order ADR §§3/5/6 or STATE_LIFECYCLE §§2–4 define; contract-undefined pairs and sub-pairs remain class B characterizations (F-B6); triples, other entry-point combinations and shared source interpretation remain

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_before_fence_and_clock_guards`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_before_fence_and_clock_guards -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::replay_lookup_is_guarded_by_scope_and_semantics_only`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked replay_lookup_is_guarded_by_scope_and_semantics_only -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_after_local_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_after_local_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_at_full_command_capacity`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_at_full_command_capacity -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_when_its_selection_is_unavailable`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_when_its_selection_is_unavailable -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_when_its_operation_is_quarantined`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_when_its_operation_is_quarantined -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_without_touching_an_unknown_payment`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_without_touching_an_unknown_payment -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::unsupported_semantics_records_nothing_after_local_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_records_nothing_after_local_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::unsupported_semantics_records_no_unavailable_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_records_no_unavailable_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::unsupported_semantics_applies_no_quarantine`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_applies_no_quarantine -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::unsupported_semantics_neither_sends_nor_captures_an_unknown_payment`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_neither_sends_nor_captures_an_unknown_payment -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::regressed_time_records_nothing_after_local_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_records_nothing_after_local_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::full_command_capacity_backpressures_after_local_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_after_local_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::stale_execution_fence_records_no_unavailable_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_records_no_unavailable_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::stale_execution_fence_applies_no_quarantine`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_applies_no_quarantine -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::stale_execution_fence_neither_sends_nor_captures_an_unknown_payment`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_neither_sends_nor_captures_an_unknown_payment -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::regressed_time_records_no_unavailable_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_records_no_unavailable_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::regressed_time_applies_no_quarantine`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_applies_no_quarantine -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::regressed_time_applies_no_capture_to_an_unknown_payment`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_applies_no_capture_to_an_unknown_payment -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::full_command_capacity_backpressures_before_an_unavailable_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_before_an_unavailable_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::full_command_capacity_backpressures_before_a_quarantine_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_before_a_quarantine_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::bound_quarantine_survives_owner_change_expiry_and_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked bound_quarantine_survives_owner_change_expiry_and_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::late_capture_after_cancellation_creates_return_marker_not_resurrection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked late_capture_after_cancellation_creates_return_marker_not_resurrection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::event_conflict_quarantines_both_bound_orders_and_blocks_payment_sending`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked event_conflict_quarantines_both_bound_orders_and_blocks_payment_sending -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::reviewed_late_capture_keeps_return_marker_and_review_requirement`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked reviewed_late_capture_keeps_return_marker_and_review_requirement -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::conflict_capacity_failure_keeps_quarantine_and_original_evidence`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked conflict_capacity_failure_keeps_quarantine_and_original_evidence -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::conflict_naming_unbound_operation_blocks_future_binding_without_changing_replays`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked conflict_naming_unbound_operation_blocks_future_binding_without_changing_replays -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::full_observation_budget_blocks_first_unknown_without_state_change`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked full_observation_budget_blocks_first_unknown_without_state_change -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::unrelated_event_flood_cannot_starve_promised_capture`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked unrelated_event_flood_cannot_starve_promised_capture -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::conflicting_event_cannot_spend_slot_reserved_for_capture`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked conflicting_event_cannot_spend_slot_reserved_for_capture -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::reserved_slot_survives_expiry_check_owner_change_and_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked reserved_slot_survives_expiry_check_owner_change_and_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::full_budget_new_conflict_quarantines_without_retaining_evidence`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked full_budget_new_conflict_quarantines_without_retaining_evidence -- --exact`
- Contract path `runtime/crates/kix-kernel-v5/tests/termination.rs::automatic_approval_is_rejected_before_order_checks`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test termination --locked automatic_approval_is_rejected_before_order_checks -- --exact`
- Contract path `runtime/crates/kix-kernel-v5/tests/termination.rs::a_false_condition_wins_over_a_stale_snapshot`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test termination --locked a_false_condition_wins_over_a_stale_snapshot -- --exact`
- Source-informed `runtime/crates/kix-kernel/tests/e4_state_model.rs::locked_v4_matches_independent_state_model`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked locked_v4_matches_independent_state_model -- --exact`

**Caveat**

The pair matrix leaves shared interpretation, triples and contract-undefined pairs open. The termination citations are v5 examples. The E-4 comparison remains source-informed.

**Reviewer questions**

1. Does each asserted guard ordering in the pair matrix follow from the named ADR or lifecycle clauses, and do the cited tests exercise both guards?
2. Which conclusions are limited to v5, and which undefined pairs, sub-pairs or higher-order combinations remain outside the coverage?

### S5-SHARED-ERROR

**Contract clauses**

```text
These five predicates detect visible overlap/accounting breaks, over-budget state,
changed first outcomes, duplicate operation capture and capture loss without a
reference state machine. They can still miss incorrect but safe rejections, wrong
error precedence, an unnecessarily sticky hold, and exact phase/review semantics
not expressed by a predicate. A full transition oracle or explicit contract-based
example is needed for those questions. The current source-informed model can
expose DIFFERENCES on them; it cannot resolve shared errors by itself.
```

**Status**

OPEN

**Gap**

UNDETERMINED: no independently derived specification oracle

**Test evidence**

None.

**Caveat**

The map records no independently derived specification oracle. E-4 agreement and a source-informed contract path can preserve a shared interpretation error.

**Reviewer questions**

1. What shared interpretation risks remain after considering the predicates and E-4 comparison together?
2. What evidence would establish independently derived specification provenance for this gap?

### S5-FINITE

**Contract clauses**

```text
No finite test proves all inputs. A kernel that incorrectly rejects many valid
inputs may satisfy safety properties; the seeded initialization guards only some
trivial vacuity, not general availability. Single-process tests do not establish
persistence, independent fencing or chain authority. The original E-4 differential
suite is retained as a complementary regression asset, not relabelled as proof.
```

**Status**

PARTIAL

**Gap**

Captured-fact initialization prevents some vacuity; explicit success examples after recorded rejections, errors, replays and at the last record slots guard only selected trivial-rejection vacuity; general availability and all input histories remain unverified (F-B5)

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::success_follows_unrelated_rejections_errors_and_replays`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked success_follows_unrelated_rejections_errors_and_replays -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection -- --exact`

**Caveat**

The map scopes the finite corpus to some vacuity guards, even after adding success examples following unrelated failures and under final-slot conditions.

**Reviewer questions**

1. Which capture-preservation and availability checks are made non-vacuous by the seeded initialization and explicit success examples?
2. Which availability and transition cases can still evade this finite corpus and its source-informed expectations?

### S5-E4-RETAINED

**Contract clauses**

```text
No finite test proves all inputs. A kernel that incorrectly rejects many valid
inputs may satisfy safety properties; the seeded initialization guards only some
trivial vacuity, not general availability. Single-process tests do not establish
persistence, independent fencing or chain authority. The original E-4 differential
suite is retained as a complementary regression asset, not relabelled as proof.
```

**Status**

PARTIAL

**Gap**

Complementary finite regression agreement only; source-informed provenance and shared-error boundary remain (F-B4)

**Test evidence**

- Source-informed `runtime/crates/kix-kernel/tests/e4_state_model.rs::locked_v4_matches_independent_state_model`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked locked_v4_matches_independent_state_model -- --exact`

**Caveat**

The map retains E-4 as finite regression evidence and points to F-B4 for source-informed provenance and shared error.

**Reviewer questions**

1. Which regressions does the retained E-4 comparison exercise beyond the kernel-only predicates?
2. Does the description of this retained asset keep its historical naming and shared-error limits visible?

## 2. A2-owned findings

### F-B2

**Contract clauses**

```text
| INV-3 | A completed command's first result cannot change | Save the first observed typed payload/result, then re-request it after every main step with its original context; require replayed=true and same original. An Eq clone only detects mutation by the read-only probe, not recovery. | A §3/§5; L §2 command row |
```

```text
Separate predicate sensitivity feeds deliberately corrupted COPIES OF OBSERVED
VIEWS (overlap, exceeded budget, missing capture, double transition count) to the
checker. Neither the locked kernel nor model_v4 is mutated. These are checker
sensitivity tests, not production fault injection or proof of complete detection.
Execution results are attached to their exact later CI head, not implied here.
```

**Map finding**

```text
- **F-B2 — class B, INV-3 sensitivity boundary (narrowed).** The new inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations test rejects observer copies with (a) altered replay replies, (b) changed public state or a false Eq sentinel, and (c) rewritten first results after later state changes, for both Held and Rejected first results. Unmodified observations pass. The generated corpus uses the same check_replay predicate. Remaining boundaries: admitted time has no public accessor and is witnessed only through whole-kernel Eq, and the fixture author knew the kernel source. Contract §4 still names four corruptions; this extra sensitivity dimension is not a contract violation. Owner: kernel contract owner/non-author A2 reviewer.
```

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::response_loss_retry_returns_original_before_availability_check`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked response_loss_retry_returns_original_before_availability_check -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::rejection_replay_stays_immutable_after_the_blocking_hold_is_released`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked rejection_replay_stays_immutable_after_the_blocking_hold_is_released -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations -- --exact`

**Caveat**

The source-informed fixture mutates observer copies. Whole-kernel Eq is the admitted-time sentinel at the public observation boundary.

**Reviewer questions**

1. Do all three corruptions exercise the same predicate as the corpus for both Held and Rejected first results?
2. What remains uncertain about admitted time or replay behavior after the observer-copy checks?

### F-B3

**Contract clauses**

```text
Read-only replay probes are reported separately and are not counted as new
commands or successful purchases. Every reply, including Err(Capacity), is checked.
```

**Map finding**

```text
- **F-B3 — class B, reply observation boundary.** “Every reply” in §4 means public post-state predicates run after every reply. Non-reserve reply values are only read via is_ok(); expected business replies are not predicted. Reserve replay has stronger typed-result assertions. Owner: kernel contract owner/non-author A2 reviewer.
```

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::five_contract_invariants_on_kernel_only_generated_histories`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked five_contract_invariants_on_kernel_only_generated_histories -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_invariants.rs::reply_oracle_rejects_deliberately_wrong_expected_replies`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_invariants --locked reply_oracle_rejects_deliberately_wrong_expected_replies -- --exact`

**Caveat**

The verbatim finding and the narrowed S4-PROBES Gap describe different points in the reply-oracle history. The reply follow-up is source-informed.

**Reviewer questions**

1. Which statements in the verbatim finding still describe the current oracle after the reply assertions follow-up?
2. Do the negative controls distinguish wrong typed replies from wrong public post-state, and which exact reply expectations remain class B?

### F-B4

**Contract clauses**

```text
The author read the kernel source while writing `tests/support/model_v4.rs`.
Its reserve guard order, including original-result lookup before execution/time
checks, follows that implementation. Data representation is separate (owner array
and Vec rather than the kernel bitmap/maps), and it does not call Kernel for an
expected result, but this is NOT independently derived specification provenance.
The 131,072 prior comparisons establish finite-trace agreement, not which side
is correct. A shared misunderstanding can survive both. The old source and raw
results are preserved rather than rewritten to appear independent.
```

```text
No finite test proves all inputs. A kernel that incorrectly rejects many valid
inputs may satisfy safety properties; the seeded initialization guards only some
trivial vacuity, not general availability. Single-process tests do not establish
persistence, independent fencing or chain authority. The original E-4 differential
suite is retained as a complementary regression asset, not relabelled as proof.
```

**Map finding**

```text
- **F-B4 — class B, historical model naming.** The e4 module description and locked_v4_matches_independent_state_model identifier use independent language, while contract §1 corrects the provenance. E4 is source-informed in this map. Representation separation and finite agreement do not establish specification independence. Owner: contract owner/non-author A2 reviewer.
```

**Test evidence**

- Source-informed `runtime/crates/kix-kernel/tests/e4_state_model.rs::locked_v4_matches_independent_state_model`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked locked_v4_matches_independent_state_model -- --exact`

**Caveat**

The E-4 identifier is historical. The shared source caveat applies to the model even though its representation differs from the kernel.

**Reviewer questions**

1. Where do module wording and the test identifier imply independence, and how does §1 qualify each instance?
2. What conclusion is justified by representation separation and the observed finite agreement alone?

### F-B5

**Contract clauses**

```text
These five predicates detect visible overlap/accounting breaks, over-budget state,
changed first outcomes, duplicate operation capture and capture loss without a
reference state machine. They can still miss incorrect but safe rejections, wrong
error precedence, an unnecessarily sticky hold, and exact phase/review semantics
not expressed by a predicate. A full transition oracle or explicit contract-based
example is needed for those questions. The current source-informed model can
expose DIFFERENCES on them; it cannot resolve shared errors by itself.
```

```text
No finite test proves all inputs. A kernel that incorrectly rejects many valid
inputs may satisfy safety properties; the seeded initialization guards only some
trivial vacuity, not general availability. Single-process tests do not establish
persistence, independent fencing or chain authority. The original E-4 differential
suite is retained as a complementary regression asset, not relabelled as proof.
```

**Map finding**

```text
- **F-B5 — class B, availability example boundary.** The seven S5 success examples assert Held only where ADR §§3/4/6/8, STATE_LIFECYCLE §2/§5.7 or the kernel README require a reservation to succeed. Left undefined and therefore not asserted as required: (a) reuse after cancel_scope, because ADR §7 makes cancellation a sticky local business fence and no contract defines reopening; (b) reuse of inventory released when a late capture produces ReturnRequired; (c) the bundle maximum value and whether record-count limits are inclusive, since the README names maximum bundle lengths and configured record counts without values, so the MAX_BUNDLE and last-slot cases are labelled characterizations; (d) the exact Rejection and KernelError variants and cross-kind selection handling on the unrelated-rejection steps. The author knew the locked kernel source when choosing boundaries. Owner: kernel contract owner/non-author A2 reviewer.
```

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::reservation_has_inventory_order_and_stable_external_intent`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked reservation_has_inventory_order_and_stable_external_intent -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::free_contiguous_range_inside_one_actual_segment_is_held`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked free_contiguous_range_inside_one_actual_segment_is_held -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::word_crossing_range_inside_one_segment_is_held_between_neighbours`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked word_crossing_range_inside_one_segment_is_held_between_neighbours -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::seats_and_general_admission_are_held_up_to_exact_remaining_capacity`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked seats_and_general_admission_are_held_up_to_exact_remaining_capacity -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::inventory_released_by_expiry_is_reusable_by_a_new_command`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked inventory_released_by_expiry_is_reusable_by_a_new_command -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::success_follows_unrelated_rejections_errors_and_replays`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked success_follows_unrelated_rejections_errors_and_replays -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked last_command_and_order_slots_admit_a_reservation_after_a_recorded_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::smallest_positive_price_and_one_millisecond_ttl_are_held`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked smallest_positive_price_and_one_millisecond_ttl_are_held -- --exact`
- Source-informed `runtime/crates/kix-kernel/tests/e4_state_model.rs::locked_v4_matches_independent_state_model`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked locked_v4_matches_independent_state_model -- --exact`

**Caveat**

The map limits the source-informed success examples to clause-backed predicates and records distinct class B observations for unresolved boundaries. Finite agreement leaves shared errors possible.

**Reviewer questions**

1. Can each of the seven Held assertions be traced to the ADR, lifecycle contract or kernel README clause named by the finding?
2. Which statements about cancellation, ReturnRequired, bundle or record limits and exact variants are observations of the locked kernel?

### F-B6

**Contract clauses**

```text
These five predicates detect visible overlap/accounting breaks, over-budget state,
changed first outcomes, duplicate operation capture and capture loss without a
reference state machine. They can still miss incorrect but safe rejections, wrong
error precedence, an unnecessarily sticky hold, and exact phase/review semantics
not expressed by a predicate. A full transition oracle or explicit contract-based
example is needed for those questions. The current source-informed model can
expose DIFFERENCES on them; it cannot resolve shared errors by itself.
```

**Map finding**

```text
- **F-B6 — class B, error-precedence pairs no contract orders.** The nineteen S5-PRECEDENCE tests assert a winner only where ADR §3 (conflict on the same identity, backpressure instead of forgetting), ADR §5 (other semantics versions rejected, time validated at the ordered boundary), ADR §6 (old-owner writes stopped, facts applied under the current fence, quarantine) or STATE_LIFECYCLE §2 (recorded rejections, UNKNOWN and slot lifetimes) decide it. Observed and not semantics, on the locked kernel: payload conflict with another version gives UnsupportedSemantics, and a foreign scope reusing principal and request gives WrongScope; another version wins over a stale fence, regressed time and full records or budget, and over an unbound operation (UnsupportedSemantics); a foreign scope wins over cancellation, a stale fence, regressed time, full command records, unavailable inventory and quarantine (WrongScope); a stale fence wins over regressed time, full records or budget and an unbound operation (ExecutionFenced); regressed time wins over a cancelled send, full records or budget, a reviewed send, an UNKNOWN retry after the deadline and an unbound operation (ClockRegression); on a cancelled scope a send at full budget, an UNKNOWN send retry and a reviewed send give InvalidTransition, an unreserved capture at full budget gives Capacity, and reserve records BusinessFenced over Unavailable and OperationQuarantined and gives Capacity when only order records are full; full order records alone give Capacity over Unavailable; a reviewed send at full budget gives InvalidTransition; an unbound capture at full budget gives Capacity, as the kernel README documents but the named contracts do not; taken seats with a quarantined operation record OperationQuarantined; and taken seats with an UNKNOWN-bound operation record OperationAlreadyBound. Exact error variants stay under F-B5. Triples were not explored. The author knew the locked kernel source. Owner: kernel contract owner/non-author A2 reviewer.
```

**Test evidence**

- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_before_fence_and_clock_guards`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_before_fence_and_clock_guards -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::replay_lookup_is_guarded_by_scope_and_semantics_only`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked replay_lookup_is_guarded_by_scope_and_semantics_only -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_after_local_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_after_local_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_at_full_command_capacity`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_at_full_command_capacity -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_when_its_selection_is_unavailable`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_when_its_selection_is_unavailable -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_when_its_operation_is_quarantined`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_when_its_operation_is_quarantined -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::altered_payload_conflicts_without_touching_an_unknown_payment`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked altered_payload_conflicts_without_touching_an_unknown_payment -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::unsupported_semantics_records_nothing_after_local_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_records_nothing_after_local_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::unsupported_semantics_records_no_unavailable_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_records_no_unavailable_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::unsupported_semantics_applies_no_quarantine`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_applies_no_quarantine -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::unsupported_semantics_neither_sends_nor_captures_an_unknown_payment`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked unsupported_semantics_neither_sends_nor_captures_an_unknown_payment -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::regressed_time_records_nothing_after_local_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_records_nothing_after_local_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::full_command_capacity_backpressures_after_local_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_after_local_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::stale_execution_fence_records_no_unavailable_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_records_no_unavailable_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::stale_execution_fence_applies_no_quarantine`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_applies_no_quarantine -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::stale_execution_fence_neither_sends_nor_captures_an_unknown_payment`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked stale_execution_fence_neither_sends_nor_captures_an_unknown_payment -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::regressed_time_records_no_unavailable_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_records_no_unavailable_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::regressed_time_applies_no_quarantine`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_applies_no_quarantine -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::regressed_time_applies_no_capture_to_an_unknown_payment`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked regressed_time_applies_no_capture_to_an_unknown_payment -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::full_command_capacity_backpressures_before_an_unavailable_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_before_an_unavailable_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::full_command_capacity_backpressures_before_a_quarantine_rejection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked full_command_capacity_backpressures_before_a_quarantine_rejection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::bound_quarantine_survives_owner_change_expiry_and_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test contract_edge_cases --locked bound_quarantine_survives_owner_change_expiry_and_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::late_capture_after_cancellation_creates_return_marker_not_resurrection`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked late_capture_after_cancellation_creates_return_marker_not_resurrection -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::event_conflict_quarantines_both_bound_orders_and_blocks_payment_sending`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked event_conflict_quarantines_both_bound_orders_and_blocks_payment_sending -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::reviewed_late_capture_keeps_return_marker_and_review_requirement`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked reviewed_late_capture_keeps_return_marker_and_review_requirement -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::conflict_capacity_failure_keeps_quarantine_and_original_evidence`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked conflict_capacity_failure_keeps_quarantine_and_original_evidence -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/transitions.rs::conflict_naming_unbound_operation_blocks_future_binding_without_changing_replays`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test transitions --locked conflict_naming_unbound_operation_blocks_future_binding_without_changing_replays -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::full_observation_budget_blocks_first_unknown_without_state_change`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked full_observation_budget_blocks_first_unknown_without_state_change -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::unrelated_event_flood_cannot_starve_promised_capture`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked unrelated_event_flood_cannot_starve_promised_capture -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::conflicting_event_cannot_spend_slot_reserved_for_capture`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked conflicting_event_cannot_spend_slot_reserved_for_capture -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::reserved_slot_survives_expiry_check_owner_change_and_cancellation`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked reserved_slot_survives_expiry_check_owner_change_and_cancellation -- --exact`
- Contract path `runtime/crates/kix-kernel/tests/observation_slots.rs::full_budget_new_conflict_quarantines_without_retaining_evidence`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test observation_slots --locked full_budget_new_conflict_quarantines_without_retaining_evidence -- --exact`
- Contract path `runtime/crates/kix-kernel-v5/tests/termination.rs::automatic_approval_is_rejected_before_order_checks`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test termination --locked automatic_approval_is_rejected_before_order_checks -- --exact`
- Contract path `runtime/crates/kix-kernel-v5/tests/termination.rs::a_false_condition_wins_over_a_stale_snapshot`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test termination --locked a_false_condition_wins_over_a_stale_snapshot -- --exact`
- Source-informed `runtime/crates/kix-kernel/tests/e4_state_model.rs::locked_v4_matches_independent_state_model`
  - `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked locked_v4_matches_independent_state_model -- --exact`

**Caveat**

The recorded undefined pairs describe observations of the locked kernel by a source-informed author. The v5 citations and E-4 comparison retain their row-specific scope.

**Reviewer questions**

1. Which of the listed guard pairs can be traced to a clause that orders them and which remain class B observations?
2. What remains untested among the guard combinations, including triples and entry points outside the pair matrix?
