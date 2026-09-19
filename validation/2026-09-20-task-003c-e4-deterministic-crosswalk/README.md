# E-4 deterministic ↔ property/reference-model crosswalk (Task 003-C)

Task: `docs/tasks/TASK_003C_E4_DETERMINISTIC_CROSSWALK.md` (immutable input, not edited).
Requested base: `6332bca0f54cc2114d986b24ab218ace33a5df12`.
Observed `origin/main` after `git fetch origin main`: `6332bca0f54cc2114d986b24ab218ace33a5df12`
(no drift, no rebase, no merge of main).
Task branch: `agent/task-003c-e4-deterministic-crosswalk`, pre-session HEAD
`29ca98fad0cb19f611eac9630f0c7805bc98cc29` (the task document commit; the bootstrap
diff from base was exactly `docs/tasks/TASK_003C_E4_DETERMINISTIC_CROSSWALK.md`).
The implementation head is the commit adding the paths listed below; the exact final
head and its CI are reported in the PR #26 closure comment, not in a commit.

This is a test/evidence-only task. It maps the eight frozen Task 001 deterministic
edge cases onto the Task 003-B relation-aware generated coverage, classifies every
row before adding anything, and adds only observer classes plus a minimal steering of
two existing relation families. No kernel or runtime source, no locked file, no
reference-model semantics (`support/model_v4.rs`), no `contract_edge_cases.rs`, no CI
workflow, no R2/storage/lifecycle/PR #11/live-PG/bank/Sui work is included.

## Governance preconditions

Read from the GitHub Actions API before any file was edited:

| Workflow | Event | Head SHA | Run ID | Status / conclusion |
|---|---|---|---|---|
| KIX protocol verification (Task 003-B closure) | push (main) | 6332bca0f54cc2114d986b24ab218ace33a5df12 | 35448485847 | completed / success |

## Locked blob verification

`git hash-object` before and after the change, both equal to the required values:

| Path | Required blob | Before | After |
|---|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | same | same |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 | same | same |

`git diff --quiet` against the pre-session HEAD confirms
`runtime/crates/kix-kernel/tests/contract_edge_cases.rs`,
`runtime/crates/kix-kernel/tests/support/model_v4.rs` and the task document are
byte-for-byte unchanged.

## Changed paths

- `runtime/crates/kix-kernel/tests/support/coverage_v4.rs` — additive observer
  classes only (listed per row below), a per-trace `first_step` record of the step at which
  each class was first hit (the crosswalk test keeps the first trace in family →
  config → seed order that hits a class), and a `replay_lookup_outranked_by_scope`
  detection that matches the recorded command by principal/request (a foreign scope
  changes the `CommandId`, so the pre-existing merged class, which looked up by full
  id, only ever observed the semantics guard).
  No existing class was renamed, removed or re-defined.
- `runtime/crates/kix-kernel/tests/e4_state_model.rs` — new test
  `task_001_deterministic_edge_cases_are_cross_validated_by_generated_witnesses`
  (eight `CrosswalkRow`s, per-class relation/baseline counts and first witnesses,
  writes `.local/verification/ktx/e4-deterministic-crosswalk.json`, fails if any
  mapped class is unreached by the relation-aware corpus); minimal steering of the
  P1 and P3 relation generators (see "Steering"). Baseline `trace()`, `CASES`,
  `STEPS`, `RELATION_SEEDS`, `RELATION_STEPS`, the required-class gates and the
  sensitivity/shrink tests are unchanged.
- `validation/2026-09-20-task-003c-e4-deterministic-crosswalk/README.md` (this file).

## Step 1 — deterministic corpus, run unchanged

`cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --test contract_edge_cases`
→ `8 passed; 0 failed` (before and after the change).

## Step 2 — pre-modification generated inventory

`cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --test e4_state_model`
on the pre-session HEAD → `8 passed`; relation suite 7 × 4 × 64 × 48 = 86,016 compared
transitions, all Task 003-B required classes reached; baseline 4 × 256 × 128 = 131,072
compared transitions. Pre-modification relation totals for the mapped existing classes
are quoted in the "pre" column of the row tables (taken from
`e4-relation-coverage.json` regenerated from a clean worktree of the pre-session HEAD).

## Step 3 — pre-anchor classification (before any edit)

Witness notation: `family/config/seed/step` = relation-aware corpus family tag,
configuration index into `relation_cases()`, seed (1-based), 0-based step of the first
hit in the whole corpus (`BTreeMap` iteration order: family, config, seed). The
`e4-deterministic-crosswalk.json` artefact carries the same fields per class.

| # | Deterministic test | Pre-anchor strength | Exact semantic distinction not proved by existing classes |
|---|---|---|---|
| 1 | `rejection_replay_stays_immutable_after_the_blocking_hold_is_released` | partial | `replay_of_rejected_first_result` / `replay_after_state_changed` prove that a rejected first result replays after *some* state change, but not that the rejection was `Unavailable`, that its blocking hold has since been released (selection free again) and that only a *new* identity can take the seat. |
| 2 | `altered_payload_conflicts_before_fence_and_clock_guards` | partial | `altered_payload_conflict_under_stale_context` merges fence and clock; no class shows the conflict winning over a stale fence alone or a regressed clock alone. |
| 3 | `replay_lookup_is_guarded_by_scope_and_semantics_only` | partial | `replay_lookup_outranked_by_scope_or_semantics` merges the two guards and, because it looked up by full `CommandId`, never observed the foreign-scope case (relation 0, baseline 0). `replay_under_stale_context` merges fence and clock for the read-only replay. |
| 4 | `expiry_instant_is_treated_consistently_by_every_entry_point` | missing | No class pins `now == expires_at` for any entry point; `held_order_expired`, `send_refused_*`, `return_required_past_deadline` are strict-past or unqualified. |
| 5 | `unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot` | partial | `unknown_retry_reuses_reservation` covers the pre-deadline retry; `unknown_order_not_released_by_ttl` / `expiry_check_keeps_reservation` cover the expiry check. Not proved: the retry *at/after* the deadline is `InvalidTransition` and keeps phase, inventory and the slot, and that the slot is later consumed into ReturnRequired. |
| 6 | `return_required_is_stable_under_further_late_evidence` | partial | Duplicate/mismatch/review persistence exist (`duplicate_effect_after_return_required`, `no_second_inventory_release`, `mismatch_after_return_required_keeps_phase`, `retained_capture_preserved_under_mismatch`, `review_set_while_return_required_persists`). Not proved: an external send on a ReturnRequired order is refused without state change. |
| 7 | `bound_quarantine_survives_owner_change_expiry_and_cancellation` | partial | Owner replacement and cancellation are covered; not proved: quarantine (and review) survives an expiry that *actually releases* the Held order, and the quarantined order cannot send afterwards. |
| 8 | `retained_unbound_conflict_bans_the_identity_for_any_future_order` | partial | Ban and refusal are covered (`retained_unbound_evidence_present`, `retained_unbound_operation_refused`, `retained_unbound_ban_coexists_with_bound_sibling`); not proved: a sibling operation of the same provider/account *binds* while the banned identity is refused. |

## Step 4 — anchors added (observer classes only, plus two steering points)

All anchors are P1–P7 observer classes in `coverage_v4.rs` computed from the model's
pre/post state and the kernel result. None is a fixture; no Task 001 trace was copied.

| Row | Anchor class(es) added | Remedy tier |
|---|---|---|
| 1 | `P1:rejected_replay_after_unavailable_cause_cleared`, `P1:new_identity_holds_selection_rejected_earlier` | 2 (observer) + 3 (steering: P1 arm 6 now also asks for an owned selection → `Unavailable`, and expires a Held order at its deadline so the hold is released) |
| 2 | `P1:altered_payload_conflict_under_stale_fence`, `P1:altered_payload_conflict_under_regressed_clock` | 2 + 3 (P1 arm 3–5 may regress the clock instead of only the fence) |
| 3 | `P1:replay_lookup_outranked_by_scope`, `P1:replay_lookup_outranked_by_semantics`, `P1:replay_under_stale_fence`, `P1:replay_under_regressed_clock` | 2 + 3 (P1 arm 0–2 may replay a known identity under scope `id(999)`) |
| 4 | `P3:held_order_expired_at_exact_instant`, `P3:reservation_refused_at_exact_expiry_instant`, `P3:send_refused_at_exact_deadline`, `P6:return_required_at_exact_deadline` | 2 + 3 (P3 arm 8 reserves with `expires_at_ms == now`) |
| 5 | `P3:unknown_retry_refused_past_deadline_keeps_reservation` (`now >= expires_at`), `P3:unknown_retry_refused_at_exact_deadline_keeps_reservation` (`now == expires_at`), `P3:unknown_retry_refused_strictly_after_deadline_keeps_reservation` (`now > expires_at`), `P3:send_refused_past_deadline`, `P3:late_capture_converts_reservation_to_return_required` | 2 |
| 6 | `P6:return_required_order_cannot_send` | 2 |
| 7 | `P5:bound_quarantine_survives_expiry_release`, `P5:quarantined_order_cannot_send_after_expiry_or_cancellation` | 2 |
| 8 | `P5:sibling_of_retained_unbound_ban_bound_independently` | 2 |

Steering. Before steering (observer anchors only, generators unchanged) five anchor
classes were unreached by the relation corpus: rows 1 (both), 2 (regressed clock),
3 (scope), 4 (reservation at exact instant). Each was reached by the unchanged
baseline corpus except `replay_lookup_outranked_by_scope`, whose first detector still
looked the command up by full id (see above) and was corrected in the same change. The three P1 and one P3 generator edits above are the smallest
that make every anchor reachable; P2/P4–P7 generators are untouched. Because the P1/P3
RNG streams changed, per-class *counts* for those families differ from Task 003-B's
recorded numbers; every Task 003-B required class is still reached and its gate test
still passes (see Step 6).

## Step 5 — complete crosswalk (post-anchor)

Counts are relation-corpus hits (86,016 transitions) unless marked `base` (131,072
baseline transitions, generator unchanged). `pre` is the pre-modification relation
count of the same class (— = class did not exist).

### Row 1 — `rejection_replay_stays_immutable_after_the_blocking_hold_is_released` — **sufficient**
Predicate: a rejected first result replays read-only even after the blocking hold was
released and the selection is free again; only a new command identity can take the seat.
Families: P1.

| Class | Anchor | pre | relation | first witness | base |
|---|---|---|---|---|---|
| `replay_of_rejected_first_result` | | 2971 | 1830 | P1/0/1/14 | 5638 |
| `replay_after_state_changed` | | 4466 | 3966 | P1/0/1/4 | 8129 |
| `rejected_replay_after_unavailable_cause_cleared` | yes | — | 58 | P1/0/3/37 | 67 |
| `new_identity_holds_selection_rejected_earlier` | yes | — | 12 | P1/0/24/44 | 150 |

### Row 2 — `altered_payload_conflicts_before_fence_and_clock_guards` — **sufficient**
Predicate: same identity, altered payload → `CommandConflict`, state unchanged, even
under a stale fence or a regressed clock; the unchanged payload still replays. Families: P1.

| Class | Anchor | pre | relation | first witness | base |
|---|---|---|---|---|---|
| `altered_payload_conflict` | | 3899 | 4097 | P1/0/1/8 | 14710 |
| `altered_field_order_id` | | 914 | 905 | P1/0/1/8 | 0 |
| `altered_field_operation` | | 912 | 886 | P1/0/1/9 | 2188 |
| `altered_field_expiry` | | 938 | 893 | P1/0/1/27 | 7716 |
| `altered_field_selection` | | 354 | 517 | P1/0/1/23 | 7346 |
| `altered_payload_conflict_under_stale_fence` | yes | — | 920 | P1/0/1/11 | 614 |
| `altered_payload_conflict_under_regressed_clock` | yes | — | 1000 | P1/0/1/9 | 573 |
| `replay_exact` | | 4466 | 3966 | P1/0/1/4 | 8129 |

### Row 3 — `replay_lookup_is_guarded_by_scope_and_semantics_only` — **sufficient**
Predicate: known identity under a foreign scope → `WrongScope`; under another
semantics version → `UnsupportedSemantics`; no state change; a regressed clock or a
stale fence does not stop the read-only replay. Families: P1.

| Class | Anchor | pre | relation | first witness | base |
|---|---|---|---|---|---|
| `replay_lookup_outranked_by_scope` | yes | — | 393 | P1/0/1/46 | 1672 |
| `replay_lookup_outranked_by_semantics` | yes | — | 388 | P1/0/1/24 | 946 |
| `replay_under_regressed_clock` | yes | — | 442 | P1/0/1/32 | 330 |
| `replay_under_stale_fence` | yes | — | 418 | P1/0/2/2 | 318 |

### Row 4 — `expiry_instant_is_treated_consistently_by_every_entry_point` — **sufficient**
Predicate: at `now == expires_at` the expiry check releases a Held order, a reservation
expiring now is `InvalidRequest`, an external send is `InvalidTransition` without state
change, and a matching capture is `ReturnRequired`. Families: P3, P6.

| Class | Anchor | pre | relation | first witness | base |
|---|---|---|---|---|---|
| `P3:held_order_expired_at_exact_instant` | yes | — | 688 | P1/0/1/41 | 46 |
| `P3:reservation_refused_at_exact_expiry_instant` | yes | — | 263 | P3/0/1/3 | 1206 |
| `P3:send_refused_at_exact_deadline` | yes | — | 47 | P1/0/2/36 | 47 |
| `P6:return_required_at_exact_deadline` | yes | — | 110 | P2/0/35/37 | 19 |

### Row 5 — `unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot` — **sufficient**
Predicate: UNKNOWN send retry at/after the deadline → `InvalidTransition`, phase,
inventory and reserved slot kept; expiry check does not release the UNKNOWN order; a
later matching capture consumes that slot into ReturnRequired. Families: P3.

| Class | Anchor | pre | relation | first witness | base |
|---|---|---|---|---|---|
| `unknown_retry_refused_past_deadline_keeps_reservation` (`>=`) | yes | — | 46 | P1/0/2/36 | 251 |
| `unknown_retry_refused_at_exact_deadline_keeps_reservation` (`==`) | yes | — | 10 | P1/0/2/36 | 7 |
| `unknown_retry_refused_strictly_after_deadline_keeps_reservation` (`>`) | yes | — | 36 | P2/1/1/19 | 244 |
| `unknown_order_not_released_by_ttl` | | 135 | 132 | P2/0/6/41 | 270 |
| `expiry_check_keeps_reservation` | | 232 | 230 | P1/0/1/20 | 569 |
| `late_capture_converts_reservation_to_return_required` | yes | — | 171 | P2/0/2/36 | 217 |

### Row 6 — `return_required_is_stable_under_further_late_evidence` — **sufficient**
Predicate: after ReturnRequired a duplicate matching event is `DuplicateEffect` with no
second inventory release, a mismatch is `Review` that sets review while phase and
retained capture persist, and an external send is refused without state change.
Families: P6.

| Class | Anchor | pre | relation | first witness | base |
|---|---|---|---|---|---|
| `duplicate_effect_after_return_required` | | 488 | 459 | P1/0/18/18 | 76 |
| `no_second_inventory_release` | | 488 | 459 | P1/0/18/18 | 76 |
| `mismatch_after_return_required_keeps_phase` | | 203 | 203 | P4/0/6/28 | 13 |
| `retained_capture_preserved_under_mismatch` | | 203 | 203 | P4/0/6/28 | 13 |
| `review_set_while_return_required_persists` | | 372 | 372 | P2/0/2/39 | 213 |
| `return_required_order_cannot_send` | yes | — | 769 | P1/0/22/36 | 475 |

### Row 7 — `bound_quarantine_survives_owner_change_expiry_and_cancellation` — **sufficient**
Predicate: a conflict naming two bound operations quarantines both orders; owner
replacement, an expiry that actually releases the order, and scope cancellation keep
the quarantine set and review; the quarantined order still cannot send. Families: P4, P5.

| Class | Anchor | pre | relation | first witness | base |
|---|---|---|---|---|---|
| `P4:conflict_names_two_bound_operations` | | 1505 | 1505 | P2/0/1/28 | 2005 |
| `P5:bound_quarantine_survives_owner_replacement` | | 2586 | 2586 | P2/0/1/13 | 3438 |
| `P5:bound_quarantine_survives_expiry_release` | yes | — | 141 | P2/0/6/25 | 195 |
| `P5:bound_quarantine_survives_scope_cancellation` | | 691 | 691 | P5/0/1/21 | 392 |
| `P5:quarantined_order_cannot_send_after_expiry_or_cancellation` | yes | — | 892 | P2/1/33/43 | 600 |

### Row 8 — `retained_unbound_conflict_bans_the_identity_for_any_future_order` — **sufficient**
Predicate: a retained conflict naming a bound and an unbound operation quarantines only
the bound order; any future order reusing the unbound identity is
`OperationQuarantined` without creating an order or binding; a sibling operation of the
same provider/account still binds. Families: P2, P4, P5.

| Class | Anchor | pre | relation | first witness | base |
|---|---|---|---|---|---|
| `P4:conflict_names_bound_and_unbound` | | 2685 | 2685 | P2/0/1/18 | 1072 |
| `P5:retained_unbound_evidence_present` | | 879 | 879 | P2/0/1/18 | 372 |
| `P2:retained_unbound_operation_refused` | | 418 | 418 | P2/0/1/20 | 0 |
| `P5:retained_unbound_ban_coexists_with_bound_sibling` | | 418 | 418 | P2/0/1/20 | 0 |
| `P5:sibling_of_retained_unbound_ban_bound_independently` | yes | — | 688 | P2/0/1/23 | 657 |

`unreached_in_relation_corpus` in `e4-deterministic-crosswalk.json` is `[]`.

## Step 6 — verification actually run (post-change, at the implementation head)

| Command | Result |
|---|---|
| `cargo test … -p kix-kernel --locked --test contract_edge_cases` | 8 passed |
| `cargo test … -p kix-kernel --locked --test e4_state_model` | 9 passed (`locked_v4_matches_independent_state_model` baseline 131,072; `relation_aware_generated_traces_reach_every_property_family` 86,016, all P1–P7 required classes; `baseline_corpus_relation_coverage_is_inventoried_not_retuned`; `oracle_sensitivity_detects_and_shrinks_missing_full_budget_quarantine`; `relation_properties_detect_model_only_quarantine_omission_and_shrink`; new crosswalk test) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | all crates ok; kix-kernel: contract_edge_cases 8, contract_invariants 3, e4_state_model 9, observation_slots 11, performance_harness 1, quarantine_capacity 8, transitions 32; 0 failed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | clean |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | clean |
| `python3.12 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3.12 scripts/test_runtime_architecture.py` | 7 tests OK |

Baseline `required_classes_not_reached_by_baseline` is unchanged in content for
pre-existing classes (`P1:altered_field_order_id`, `P2:reuse_of_bound_operation_rejected`,
and the P2/P5 retained-unbound classes); the baseline corpus was not retuned.

Exact-head KTX kernel and KIX protocol CI for the final task head are recorded in the
PR #26 closure comment (AGENTS.md §11).

### Independent-review correction (PR #26 comment 5745761933)

The first implementation head mapped row 5 only to the merged `>=` bucket
`unknown_retry_refused_past_deadline_keeps_reservation` (46 relation / 251 baseline
hits), which does not machine-prove that both timing regions the deterministic test
asserts (`now == expires_at` and `now > expires_at`) were reached. The bucket was
split into two additional precise classes (the merged class is kept unchanged); row 5
now requires all three to be reached by the relation corpus. Both regions were already
reached by the existing generators — no further steering was needed:
`==` 10 relation hits (first P1/0/2/36; baseline 7, first 0/14/91),
`>` 36 relation hits (first P2/1/1/19; baseline 244, first 0/4/54). All other counts
in this file are unchanged by the split.

## Contract findings

- Explicit contract violations: none. Every mapped class agrees between the kernel and
  the source-informed reference model on all 86,016 + 131,072 compared transitions.
- Contract-undefined characterizations: none new. The exact-instant semantics
  (`now == expires_at` counts as expired at every entry point) is asserted by
  `contract_edge_cases.rs` and is now also observed generatively (row 4); its
  contract wording remains that of `STATE_LIFECYCLE.md`.

## Non-claims and remaining uncertainty

- Generated witnesses prove reachability of the named predicates in the configured
  corpora and kernel/model agreement on them; they do not prove completeness,
  formal correctness or clean-room independence (the model is source-informed).
- Rows are `sufficient` in the sense that every material distinction of the
  deterministic predicate has an observer class with a reproducible witness; they do
  not claim the generated corpus explores the same *sequence* as the deterministic
  trace, and no deterministic trace was copied.
- `new_identity_holds_selection_rejected_earlier` has the thinnest generated
  evidence (12 relation hits, 150 baseline hits); it is reached deterministically
  and reproducibly, but a future task may prefer a larger margin.
- Steering changed the P1/P3 RNG streams; Task 003-B per-class counts are therefore
  historical for those families. Gates, corpus sizes and the baseline are preserved.
- Nothing here concerns durability, replication, bank exactly-once, chain finality or
  production readiness.
