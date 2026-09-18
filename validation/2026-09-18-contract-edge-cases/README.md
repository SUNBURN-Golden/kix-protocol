# Contract edge-case audit over the locked v4 kernel (Devin task 001)

Task: `docs/tasks/DEVIN_FIRST_BATCH_E4_AUDIT.md`.
Base (`origin/main` at session start): `5fffc196be37425366b2a6ec7faeec1db9bbca46`.
PR #20 head before this change: `a4ab8d0119daba974dd59a20d3da05d82bd61118`.
`origin/main` had not moved from the bootstrap base, so the task base is unchanged.
The exact head SHA carrying this note is reported in the PR summary comment.

This is a test-and-evidence record. No kernel semantics, R2, integration (a),
storage/log engine, lifecycle release/GC/index, live PG/bank or live Sui work is
included.

## Locked blob verification

`git hash-object` before and after the change, both equal to the required values:

| Path | Required blob | Observed before | Observed after |
|---|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | same | same |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 | same | same |

Neither file was opened for writing, reformatted or transiently mutated;
`cargo fmt` was run in `--check` mode only.

## Changed paths

- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs` (new, blob `d37ea7df55423c83bedee16bf12bdc8dd61f7cae`)
- `validation/2026-09-18-contract-edge-cases/README.md` (new, this note)

## A. Coverage inventory (existing suite, before this change)

Kernel suite before the change: 59 tests — `transitions.rs` 32,
`observation_slots.rs` 11, `quarantine_capacity.rs` 8 (locked),
`e4_state_model.rs` 4, `contract_invariants.rs` 3, `performance_harness.rs` 1.

| Audit item | Already covered by | Gap taken in this change |
|---|---|---|
| 1. Immutable original result vs current-state query | `transitions.rs::response_loss_retry_returns_original_before_availability_check`, `::expired_hold_retry_keeps_original_result_and_separate_current_state`, `::local_cancellation_blocks_new_reservations_but_not_original_results`, `::ownership_generation_does_not_change_command_identity`, `::accepted_expiry_check_advances_time_but_reservation_result_lookup_does_not`, `contract_invariants.rs` INV-3 | Replay of a **rejected** first result after its cause disappeared (`Unavailable` replays after the blocking hold expired) |
| 2. Same command identity, altered payload | `transitions.rs::identical_id_with_changed_payload_is_a_conflict` (amount only) | Altered `order_id`, `payment.operation`, `expires_at_ms` and `selection`, each under the current context, a stale fence and a regressed clock |
| 3. Contract-significant guard precedence | `transitions.rs::unknown_semantics_and_regressed_time_are_not_applied`, `quarantine_capacity.rs::v3_inputs_are_rejected_before_any_state_change`, `observation_slots.rs::previous_semantics_version_is_rejected_without_silent_replay_change`, `quarantine_capacity.rs::rejected_evidence_that_quarantines_also_advances_logical_time` | The documented reservation-lookup boundary itself: scope and semantics outrank a replay, while fence and clock do not; conflict detection precedes both |
| 4. PaymentUnknown retention across TTL | `transitions.rs::unknown_payment_is_not_released_by_ttl`, `observation_slots.rs::reserved_slot_survives_expiry_check_owner_change_and_cancellation` | UNKNOWN **retry at/after** the deadline is refused with no state change, and the TTL instant (`now_ms == expires_at_ms`) across `reserve` / `expire` / `mark_payment_unknown` / `observe_capture` |
| 5. Late capture after expiry/cancellation, ReturnRequired | `transitions.rs::late_capture_after_expiry_and_resale_does_not_release_new_buyer`, `::late_capture_after_cancellation_creates_return_marker_not_resurrection`, `::reviewed_late_capture_keeps_return_marker_and_review_requirement`, `observation_slots.rs::reserved_slot_survives_expiry_check_owner_change_and_cancellation` | Stability **after** ReturnRequired: a second matching event is a duplicate effect with no second inventory release, and a later mismatching event raises review without erasing the retained fact |
| 6. Bound review/quarantine after matching or conflicting evidence | `transitions.rs::event_conflict_quarantines_both_bound_orders_and_blocks_payment_sending`, `::reviewed_order_preserves_matching_capture_without_normal_confirmation`, `quarantine_capacity.rs::original_event_and_command_replays_never_clear_quarantine`, `::full_evidence_budget_still_quarantines_both_bound_operations` | Stickiness across **ordered transitions**: owner replacement, expiry release and scope cancellation do not clear review or the quarantine set |
| 7. Retained vs unretained unbound conflict identity | `quarantine_capacity.rs::retained_unbound_conflict_blocks_future_binding_without_expanding_bound_set`, `::unretained_unbound_conflict_creates_no_speculative_binding_ban`, `transitions.rs::conflict_naming_unbound_operation_blocks_future_binding_without_changing_replays` | The ban is on the operation identity, not the order row: a **different** `order_id` reusing the retained identity is rejected, while a sibling operation under the same provider/account is not |
| 8. Observation-slot/capacity around the first bound capture | `observation_slots.rs` (all 11), `quarantine_capacity.rs::full_budget_quarantine_preserves_the_already_promised_capture_slot`, `::many_unbound_conflicts_trip_bounded_scope_quarantine_without_losing_slots`, `contract_invariants.rs` INV-2 | None added — existing coverage is adequate; the reserved-slot assertions in the new TTL-retry case reuse this contract rather than duplicating a regression |

No existing regression was duplicated, renamed or moved.

## B. New coverage

`runtime/crates/kix-kernel/tests/contract_edge_cases.rs`, 8 tests, public API only,
no `model_v4` / generator import, whole-kernel `Eq` clones where the contract
requires a call to leave state unchanged:

1. `rejection_replay_stays_immutable_after_the_blocking_hold_is_released`
2. `altered_payload_conflicts_before_fence_and_clock_guards`
3. `replay_lookup_is_guarded_by_scope_and_semantics_only`
4. `expiry_instant_is_treated_consistently_by_every_entry_point`
5. `unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot`
6. `return_required_is_stable_under_further_late_evidence`
7. `bound_quarantine_survives_owner_change_expiry_and_cancellation`
8. `retained_unbound_conflict_bans_the_identity_for_any_future_order`

Derivations used: ADR `0001-ktx-authority-commit-recovery.md` §3/§5/§6,
`docs/contracts/STATE_LIFECYCLE.md` §2/§3/§5, and the kernel README sections
"Implemented meaning" and "Observation reservation and remaining gaps".

## C. Contract/implementation conflicts

None found. All eight cases passed on first execution against the locked kernel,
so no minimal reproduction of a locked-file defect was required and no locked
file needed a change.

One behavior is recorded as a **characterization**, not as a contract violation:
after `ReturnRequired`, a later *mismatching* capture event returns
`ObservationOutcome::Review` and sets `review_required`, while
`Order::state` remains `ReturnRequired`. The documents state that captured facts
are not erased and that matching later evidence never clears review; they do not
state which of the two markers wins in `state`. The test asserts the observed
behavior and the preserved capture, and flags the documentation gap here rather
than redefining the contract.

## Commands actually run and their results

Local machine, `rustc 1.98.1 (48a229cea 2026-09-01)` / `cargo 1.98.1`
(matching `rust-toolchain.toml`), Python 3.12.13 for the architecture gate.

| Command | Result |
|---|---|
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` (before the change) | ok — 59 passed, 0 failed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --test contract_edge_cases` | ok — 8 passed, 0 failed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` (after the change) | ok — 67 passed, 0 failed (contract_edge_cases 8, contract_invariants 3, e4_state_model 4, observation_slots 11, performance_harness 1, quarantine_capacity 8, transitions 32, lib/doc 0) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | ok — 117 passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0, no warnings |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0, no warnings |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 (an initial run flagged only the new file; it was reformatted before commit) |
| `python scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python scripts/test_runtime_architecture.py` | OK — 7 tests |

These are local runs. GitHub Actions results for the exact head are reported in
the PR, not claimed here.

## Not tested / non-claims

- No durability, persistence, crash recovery, replication or checkpoint claim:
  every case is single-process and in-memory.
- No distributed fencing claim: `replace_owner` is exercised only as an ordered
  local transition.
- No bank exactly-once, settlement, refund execution or chain-finality claim;
  `ReturnRequired` is a marker, not an executed refund.
- No concurrency, throughput or latency measurement; the performance harness was
  run only as part of the existing suite.
- Not exhaustive: eight deterministic examples plus the pre-existing generated
  suites do not prove the contract for all inputs.
- The author of these tests has read the kernel source. They are contract-derived
  in their predicates but are **not** clean-room-independent authorship.
- The protocol workflow's Python/Move/TypeScript/localnet/zk stages were not run
  locally; only the Rust boundary and the architecture gate were reproduced.

## Remaining uncertainty

- The `state` versus `review_required` precedence after `ReturnRequired`
  (section C) is undocumented; a contract clarification is proposed as
  follow-up, with no kernel change implied.
- The unmatched-inbox custody gap and the proposed terminal-outcome
  slot-release contract named in the kernel README remain unimplemented and
  untested here; they are outside this task's scope.
