# KIX Task 003-C — Task 001 deterministic ↔ property cross-validation

## Status

- Task ID: `003-C`
- Execution session: new session required
- Task document: immutable once execution starts
- Repository-wide rules: follow root `AGENTS.md`

## Objective

Complete the E-4 audit sequence by mapping the eight deterministic Task 001 edge-case regressions to the explicit reference-model/property coverage merged in Tasks 003-A and 003-B.

This task must:

1. build an exact predicate-level crosswalk for all eight deterministic cases;
2. prove which predicates are already exercised and asserted by the merged P1–P7 generated property suite;
3. identify only genuine semantic gaps;
4. add the smallest cross-validation anchors needed for those gaps;
5. leave existing deterministic regressions intact and avoid duplicating them as fixed copies.

This is a **test/evidence cross-validation task only**. It must not change production/runtime semantics.

## Base

- Requested base SHA: `6332bca0f54cc2114d986b24ab218ace33a5df12`
- This is the ordinary merge commit for Task 003-B.
- At session start run `git fetch origin main`.
- Record exact `origin/main` and report any drift.
- Do not silently rebase, merge main into the task branch, or change the base.

### Task 003-B post-merge gate — mandatory before any execution output edit

Before changing any Task 003-C output file, independently verify through GitHub/gh API:

- current `origin/main` is exactly `6332bca0f54cc2114d986b24ab218ace33a5df12`;
- the push/main **KIX protocol verification** run whose exact `head_sha` is
  `6332bca0f54cc2114d986b24ab218ace33a5df12`
  is terminal `completed / success`;
- record its exact run ID, event, status and conclusion;
- KTX is PR-triggered only; applicable reviewed-content KTX evidence is
  run `35441862244` = completed / success;
- locked blobs on the merge commit are still:
  - `runtime/crates/kix-kernel/src/lib.rs` =
    `69564b166f0c27f9af5d8422f0a466b18d74c20f`
  - `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
    `b607996c83a119c349f1cc90469ac1ba82764e20`

If the post-merge protocol run is not terminal success, or main drift exists, **stop before editing Task 003-C outputs and report the exact blocker**.

## Mandatory task-specific reading

Follow root `AGENTS.md`, then read:

- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
- `runtime/crates/kix-kernel/tests/e4_state_model.rs`
- `runtime/crates/kix-kernel/tests/support/model_v4.rs`
- `runtime/crates/kix-kernel/tests/support/coverage_v4.rs`
- `runtime/crates/kix-kernel/tests/observation_slots.rs`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
- `runtime/crates/kix-kernel/tests/transitions.rs`
- `docs/contracts/STATE_LIFECYCLE.md` 0.6 §5.7.1
- `docs/contracts/CONTRACT_INVARIANTS.md`
- `validation/2026-09-18-contract-edge-cases/README.md`
- `validation/2026-09-19-task-003a-e4-model-schema/README.md`
- `validation/2026-09-19-task-003b-e4-property-expansion/README.md`

## The eight Task 001 deterministic anchors

Crosswalk these exact tests, at **predicate level**, not merely by test name:

1. `rejection_replay_stays_immutable_after_the_blocking_hold_is_released`
2. `altered_payload_conflicts_before_fence_and_clock_guards`
3. `replay_lookup_is_guarded_by_scope_and_semantics_only`
4. `expiry_instant_is_treated_consistently_by_every_entry_point`
5. `unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot`
6. `return_required_is_stable_under_further_late_evidence`
7. `bound_quarantine_survives_owner_change_expiry_and_cancellation`
8. `retained_unbound_conflict_bans_the_identity_for_any_future_order`

Do not edit or rename `contract_edge_cases.rs`.

## Candidate crosswalk to audit, not blindly assume

The following is an initial mapping hypothesis. The executing agent must verify actual predicates and generated reachability rather than simply copying this table.

### Anchor 1 — rejected replay after cause disappears

Likely related merged property classes:

- P1 `replay_exact`
- P1 `replay_of_rejected_first_result`
- P1 `replay_after_state_changed`
- P2 `rejected_no_binding`

Potential uncovered predicate to verify:

- the **specific rejection cause disappears** after another order releases inventory,
  yet the original rejected command still replays unchanged and a **new command identity**
  can use the now-available inventory without the rejected command becoming an order.

### Anchor 2 — altered payload before fence/clock guards

Likely directly covered by P1:

- `altered_payload_conflict`
- `altered_payload_conflict_under_stale_context`
- `altered_field_order_id`
- `altered_field_operation`
- `altered_field_expiry`
- `altered_field_selection`

Verify no hidden predicate from the deterministic case is omitted.

### Anchor 3 — replay lookup guarded by scope/semantics only

Likely directly covered by P1:

- `replay_exact`
- `replay_under_stale_context`
- `replay_lookup_outranked_by_scope_or_semantics`

Verify the distinction:
- scope/semantics reject before replay;
- fence/clock do not prevent identical replay;
- replay stays read-only.

### Anchor 4 — exact expiry instant across every entry point

Related merged classes include:

- P3 `held_order_expired`
- P3 `unknown_order_not_released_by_ttl`
- P6 `return_required_past_deadline`
- applicable reserve/send rejection observations

Potential uncovered predicate to verify:

At **exact equality** `now_ms == expires_at_ms`, all four public paths agree on the boundary:

- new reserve with expiry equal to now is rejected invalid;
- expire releases a Held order;
- send/mark-PaymentUnknown authorization is rejected;
- matching capture is classified ReturnRequired.

Do not treat generic “past deadline” reachability as proof of the equality boundary unless generated evidence actually includes equality.

### Anchor 5 — UNKNOWN retry after deadline keeps reservation/slot

Related merged classes include:

- P3 `unknown_retry_reuses_reservation`
- P3 `expiry_check_keeps_reservation`
- P3 `unknown_order_not_released_by_ttl`
- P3 `capture_consumes_own_reservation`
- P7 reservation/budget classes

Potential uncovered predicate to verify:

- retrying `mark_payment_unknown` **at/after deadline** returns InvalidTransition;
- order remains PaymentUnknown;
- inventory remains owned;
- the reserved observation slot remains;
- later accepted capture consumes that same slot and yields ReturnRequired.

### Anchor 6 — ReturnRequired stable under later evidence

Likely directly covered through P4/P6:

- `same_operation_new_event_identity`
- `duplicate_economic_effect`
- `later_mismatch_raises_review`
- `late_matching_capture_return_required`
- `duplicate_effect_after_return_required`
- `no_second_inventory_release`
- `mismatch_after_return_required_keeps_phase`
- `retained_capture_preserved_under_mismatch`
- `review_set_while_return_required_persists`
- `review_predicate_sticky_across_step`

Verify against STATE_LIFECYCLE 0.6 §5.7.1.

### Anchor 7 — bound quarantine survives ordered transitions

Likely directly covered through P5:

- `bound_conflict_quarantines_order`
- `bound_quarantine_survives_owner_replacement`
- `bound_quarantine_survives_expiry_check`
- `bound_quarantine_survives_scope_cancellation`
- `reviewed_order_cannot_send`

Verify conflict evidence is still retained and review remains sticky.

### Anchor 8 — retained-unbound identity ban applies to future order identity

Likely directly covered through P2/P5:

- `retained_unbound_evidence_present`
- `retained_unbound_operation_refused`
- `retained_unbound_blocks_binding`
- `retained_unbound_ban_coexists_with_bound_sibling`
- `sibling_operation_bound_independently`

Verify the generated/property evidence really demonstrates:
- the ban is on `provider/account/operation`, not one order row;
- a different future order identity cannot bind the blocked operation;
- a sibling operation under the same provider/account remains usable.

## Required work

### A. Build a predicate-level crosswalk

Produce one auditable matrix with one row per material deterministic predicate.

Columns should include at least:

- Task 001 test name;
- deterministic predicate;
- contract/README authority;
- existing P-family;
- exact property class(es);
- evidence that generated corpus actually reaches it;
- classification: `covered`, `partial`, or `missing`;
- if partial/missing, exact reason.

Do not mark a predicate covered merely because a broadly related family has nonzero counts.

### B. Add only missing cross-validation anchors

For every predicate classified `partial` or `missing`:

1. first determine whether an existing generated trace already reaches the exact predicate but the observer does not classify/assert it;
   - if so, add only the smallest observer/counter/assertion needed;
2. otherwise add the smallest deterministic-seeded **property/generator anchor** that exercises the predicate;
3. do not copy-paste the Task 001 fixed test as a second fixed regression;
4. prefer parameterized/seeded/model-aware cross-validation over a duplicate hard-coded scenario;
5. preserve failure reproducibility and useful shrink/minimization where applicable.

If all predicates are already directly and correctly covered, it is valid for this task to add **no new behavioral test** and only add machine-checkable crosswalk/evidence. Do not manufacture test count.

### C. Machine-check the crosswalk where practical

The crosswalk should not be a prose-only claim if a lightweight test can verify it.

Preferred pattern:

- define stable anchor identifiers for the eight Task 001 cases;
- associate each anchor predicate with property class identifiers;
- assert required mapped classes are actually reached by the corpus or by a narrowly added anchor runner;
- fail clearly if a mapped property disappears in future edits.

Do not couple the test to volatile absolute hit counts unless the exact count is itself contract-significant. Nonzero reachability plus predicate assertion is usually sufficient.

### D. Preserve existing assets

The following must remain reproducible:

- Task 001 `contract_edge_cases.rs` eight tests;
- Task 003-A explicit model relation checks;
- Task 003-B historical baseline corpus;
- Task 003-B relation-aware P1–P7 corpus;
- existing oracle-sensitivity and relation-property sensitivity tests.

Do not retune the broad generator merely to make the crosswalk convenient.

## Authorized scope

Expected paths:

- `runtime/crates/kix-kernel/tests/e4_state_model.rs`
- `runtime/crates/kix-kernel/tests/support/coverage_v4.rs`
- optionally one narrowly scoped new support file under
  `runtime/crates/kix-kernel/tests/support/` for crosswalk metadata/helpers
- one new validation note under `validation/`

No production/runtime source may change.

The executing agent must not modify this Task document.

## Out of scope

Do not:

- modify `runtime/crates/kix-kernel/src/lib.rs`;
- modify `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`;
- modify `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`;
- change kernel/runtime semantics;
- add review resolution, ReturnRequired discharge, slot release, GC/index;
- implement R2 or PR #11 integration (a);
- add storage/log engines;
- perform live PG/bank/Sui work;
- turn this into another broad generator expansion;
- increase raw seed/step counts as a substitute for cross-validation;
- claim formal proof, exhaustive correctness, or clean-room independence.

## Verification

At minimum:

1. run Task 001 `contract_edge_cases` unchanged;
2. run the E-4 state-model/property suite;
3. run any new crosswalk/anchor test;
4. verify the historical baseline and P1–P7 relation-aware corpus still pass;
5. verify existing oracle-sensitivity tests still pass;
6. run full kernel tests;
7. run runtime workspace tests;
8. run `cargo fmt --check`;
9. run kernel/workspace Clippy with `-D warnings`;
10. run architecture gate/tests where practical;
11. verify both locked blobs before and after;
12. verify exact final-head KTX and full KIX protocol CI.

## Acceptance criteria

- [ ] Task 003-B post-merge main/push protocol run for exact merge SHA is verified completed/success before output edits.
- [ ] base/current main relationship is explicitly recorded.
- [ ] Task 003-C document remains unchanged by executing agent.
- [ ] both locked blobs remain exact.
- [ ] all eight Task 001 tests are mapped at predicate level.
- [ ] no predicate is marked covered based only on broad thematic similarity.
- [ ] every partial/missing predicate has the smallest justified cross-validation anchor, or a documented reason no code addition is needed.
- [ ] no deterministic Task 001 test is duplicated verbatim.
- [ ] broad baseline and P1–P7 generator parameters are not gratuitously retuned.
- [ ] Task 001 eight tests remain unchanged and green.
- [ ] Task 003-A relation checker remains green.
- [ ] Task 003-B baseline/property corpora remain green.
- [ ] existing sensitivity tests remain green.
- [ ] exact final-head KTX CI completed/success.
- [ ] exact final-head KIX protocol CI completed/success.
- [ ] evidence/non-claims and remaining uncertainty are recorded.
- [ ] PR remains unmerged until explicit human merge approval after review.

## Evidence requirements

Final report must include:

- exact base / observed main / pre-session branch head / final head;
- exact Task 003-B post-merge protocol run ID used to open this task;
- complete changed-path list;
- locked blobs before/after;
- full eight-test predicate crosswalk;
- exact list of predicates already covered vs partial/missing;
- every new cross-validation anchor added and why;
- any candidate gap that proved already covered and therefore required no new test;
- baseline and P1–P7 corpus preservation evidence;
- local command results;
- exact-head CI run IDs/status/conclusion;
- contract violations or undefined behavior found;
- explicit non-claims.

## Non-claims

Task 003-C does not establish:

- formal or exhaustive correctness;
- clean-room independence;
- durability/persistence/crash recovery;
- distributed fencing;
- chain finality/authority;
- bank/PG exactly-once;
- refund execution;
- concurrency or production performance;
- lifecycle release/GC/index correctness.

## Closure

Task 003-C is the final planned split of the current E-4 edge-case/property cross-validation sequence.

A later new task may address any newly discovered contract defect or deliberately expand to currently out-of-scope lifecycle release/retention work, but such work must not be smuggled into Task 003-C.
