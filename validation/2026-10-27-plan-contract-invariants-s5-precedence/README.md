# S5-PRECEDENCE guard-pair error-precedence matrix

Task ID: `plan-plan-contract-invariants-s5-precedence-m`. Task document: the
supervisor-supplied node specification and read-only design plan in this session;
there is no issue or corresponding file under `docs/tasks/`. No task input edited.
Date: 2026-10-27. State: implemented and locally verified; publication, non-author
A2 review and exact-head hosted CI belong to the supervisor. This is not merge-ready.

## Basis and protected content

- Branch: `agent/kix-plan-plan-contract-invariants-s5-precedence-m`.
- Observed local `origin/main`, task base and initial branch HEAD:
  `d016caee4ae40f28f531809359ee77ac22db0073` (identical; no local base delta). The
  dependency node `plan-plan-contract-invariants-s5-availability` is merged in that
  base: `contract_edge_cases.rs` contains
  `success_follows_unrelated_rejections_errors_and_replays`.
- No fetch was performed: the supervisor explicitly prohibits all network actions.
  Remote freshness is unverified. No commit, push, PR, issue or comment was made.
- Implementation is the uncommitted working-tree patch, not the unchanged HEAD.
  A final committed implementation/task SHA does not exist in this builder session.
- Merge SHA, exact-head KTX/KIX run IDs/status/conclusions and post-merge main CI:
  not applicable / not run. No earlier CI is attributed to this patch.
- Both initial and post-test `git hash-object` checks returned:
  - `runtime/crates/kix-kernel/src/lib.rs`:
    `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
  - `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`:
    `b607996c83a119c349f1cc90469ac1ba82764e20`.
- The protected-path diff against local `origin/main` is empty, including
  `reference/v0.3-rc1/**`, both locks, kernel source, contracts, ADRs, the kernel
  README, task documents, `.aiops/`, `.github/`, scripts, `tests/support/model_v4.rs`,
  `e4_state_model.rs` and `docs/status/EVIDENCE_MAP_ROLLUP.md`.

Complete changed paths:

1. `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
2. `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md`
3. `docs/README.md`
4. `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md`

In the test file every existing test and helper is byte-unchanged. The module doc
gains one paragraph, and a `CONTRACT_INVARIANTS §5 error-precedence pairs
(S5-PRECEDENCE)` section is appended: helpers `old_semantics`, `next_fence`,
`ctx_under`, `seat_limits`, `refused`, `recorded`, `quarantine_pair` and 19 tests.
They use only the public kernel API and observable state, and import neither
`model_v4`, the e4 model nor any generator.

Map edits: the S5-PRECEDENCE contract-path cell keeps its four citations and adds
the 19 new tests plus the 11 "already covered" citations below from
`contract_edge_cases.rs`, `transitions.rs` and `observation_slots.rs`. The locked
`quarantine_capacity.rs` is cited only here, because the checker's contract-path
set excludes it. The Gap text is narrowed. The row stays PARTIAL. A §0 follow-up
bullet, finding F-B6 and the §5 non-claims are added. No status changed, so the
Counts line and its roll-up copy in `docs/status/EVIDENCE_MAP_ROLLUP.md` are
recomputed as unchanged and not edited:

`Counts: rows=27 COVERED=10 PARTIAL=12 NOT_COVERED=3 OPEN=2`

## Guard families and classification rule

Entry points: R = `reserve`, S = `mark_payment_unknown`, O = `observe_capture`.
`expire`, `cancel_scope` and `replace_owner` are setup transitions here.

| Code | Public rejection guard |
|---|---|
| PC | Payload conflict: `CommandConflict` (R) |
| SV | Semantics version: `UnsupportedSemantics` (R, S, O). Scope: `WrongScope` (R) |
| FC | (e) Execution fence: `ExecutionFenced`. (c) Local cancellation: `Rejected(BusinessFenced)` on R, `InvalidTransition` on S, ReturnRequired on O |
| RT | Regressed time: `ClockRegression` |
| CB | Capacity: command/order records on R (`Capacity`), observation budget on S/O (`Capacity`) |
| IU | Inventory unavailable: `Rejected(Unavailable)` (R) |
| QR | Quarantine/review: `Rejected(OperationQuarantined)` on R, a reviewed order's `InvalidTransition` on S, an event conflict on O |
| UO | UNKNOWN: a PaymentUnknown order and its reserved slot (S/O), and `UnknownOperation` for an unbound capture (O) |

A pair is **contract-defined** only where a named clause decides which guard's
observable outcome wins:

- **L (lookup first).** ADR §3: same identity with a different payload is a conflict,
  and capacity "backpressures instead of forgetting". ADR §5: the result lookup is a
  read-only exception. ADR §8 and kernel README: retry results bypass new-attempt
  availability checks. STATE_LIFECYCLE §2: one recorded first result per command.
- **V (version).** ADR §5: v4 "rejects other versions", so nothing is applied or
  recorded under another version.
- **F (fence).** ADR §3/§6: internal fencing stops new internal writes by an old
  owner; the current owner applies late facts under its current execution fence.
- **T (time).** ADR §5: supplied time and monotonicity are validated at the ordered
  boundary, so a regressed input is not admitted.
- **B (bounded records).** STATE_LIFECYCLE §2 records business rejections as first
  results; ADR §3 bounded records backpressure instead of forgetting. A recorded
  rejection therefore needs a command slot.
- **Q (quarantine).** ADR §6 and addendum A: quarantine blocks new sends and fresh
  bindings, survives cancellation, expiry and owner change, and is applied before
  the evidence-capacity check.

Where two guards each lead to a no-state-change error, or each lead to a recorded
rejection, and no clause orders them, the pair is AGENTS §8 class B: the observed
outcome is recorded below and no test asserts it. Exact error and rejection variants
remain the F-B5 (d) characterization; the tests fix which guard's effect wins
(recorded or applied versus refused with a whole-kernel `Eq` check).

## Pair matrix

All 28 unordered pairs of the eight families are labelled. Labels: **T** = new test
in this patch (by number, below), **C** = already covered (exact citation), **B** =
class B (observed outcome, not semantics). Every combination was built against the
locked kernel; "not co-occurring" is not used. Paths below are under
`runtime/crates/kix-kernel/tests/`.

| # | Pair | Label |
|---|---|---|
| 1 | PC×SV | B: altered payload under another version → `UnsupportedSemantics`; a foreign scope reusing principal/request with an altered payload → `WrongScope` (a different identity by ADR §3) |
| 2 | PC×FC | (e) C: `contract_edge_cases.rs::altered_payload_conflicts_before_fence_and_clock_guards` (ADR §3). (c) T1 |
| 3 | PC×RT | C: `contract_edge_cases.rs::altered_payload_conflicts_before_fence_and_clock_guards` (ADR §3/§5) |
| 4 | PC×CB | T2 |
| 5 | PC×IU | T3 |
| 6 | PC×QR | T4 |
| 7 | PC×UO | T5 |
| 8 | SV×FC | version × (c): T6. Version × (e) R/S/O: B, `UnsupportedSemantics`. Scope × (e) and scope × (c): B, `WrongScope` |
| 9 | SV×RT | B: version → `UnsupportedSemantics` (R/S/O); scope → `WrongScope` |
| 10 | SV×CB | B: version at full command records or full observation budget → `UnsupportedSemantics` (R/S/O); scope at full command records → `WrongScope` |
| 11 | SV×IU | version: T7. Scope: B, `WrongScope` (nothing recorded) |
| 12 | SV×QR | version: T8. Scope: B, `WrongScope` |
| 13 | SV×UO | version × PaymentUnknown/slot: T9. Version × `UnknownOperation`: B, `UnsupportedSemantics` (the locked `quarantine_capacity.rs::v3_inputs_are_rejected_before_any_state_change` also exhibits a v3 capture of an unbound operation refused this way) |
| 14 | FC×RT | (c) R/O: T10. (e) R/S/O: B, `ExecutionFenced`. (c) S cancelled + regressed: B, `ClockRegression` |
| 15 | FC×CB | (c) R at full command records: T11. (e) at full records/budget R/S/O: B, `ExecutionFenced`. (c) S on a Held order at full budget: B, `InvalidTransition`. (c) O unreserved capture at full budget: B, `Capacity`. (c) R with only order records full: B, `Capacity` |
| 16 | FC×IU | (e): T12. (c): B, records `Rejected(BusinessFenced)` over `Unavailable` |
| 17 | FC×QR | (e): T13. (c) O: C (ADR §6 "Expiry/cancellation can still establish ReturnRequired while retaining review"), `transitions.rs::reviewed_late_capture_keeps_return_marker_and_review_requirement`. (c) S: C (ADR §6 quarantine blocks a new send; both guards refuse unchanged with the same error), `contract_edge_cases.rs::bound_quarantine_survives_owner_change_expiry_and_cancellation`. (c) R: B, records `Rejected(BusinessFenced)` over `OperationQuarantined` |
| 18 | FC×UO | (e) S/O: T14. (c) O: C (ADR §6, STATE_LIFECYCLE §2 slot row), `transitions.rs::late_capture_after_cancellation_creates_return_marker_not_resurrection` and `observation_slots.rs::reserved_slot_survives_expiry_check_owner_change_and_cancellation`. (c) S retry of UNKNOWN: B, `InvalidTransition` (ADR §6 "A retry of the same external action keeps the original identity" does not say whether cancellation fences it). (e) × `UnknownOperation`: B, `ExecutionFenced` |
| 19 | RT×CB | B: regressed at full command records (R), full budget (S) or an unrelated capture at full budget (O) → `ClockRegression`. The conflict-at-capacity path, where Capacity does change state (addendum A), is T16 |
| 20 | RT×IU | T15 |
| 21 | RT×QR | R and O conflict: T16. S on a reviewed order: B, `ClockRegression` (also exhibited by locked `quarantine_capacity.rs::rejected_evidence_that_quarantines_also_advances_logical_time`) |
| 22 | RT×UO | PaymentUnknown capture: T17. S retry after the deadline: B, `ClockRegression`. `UnknownOperation`: B, `ClockRegression` |
| 23 | CB×IU | full command records: T18. Only order records full: B, `Capacity` (no order slot is needed to record an Unavailable rejection; no contract decides) |
| 24 | CB×QR | R: T19. O conflict at full budget: C (addendum A), `transitions.rs::conflict_capacity_failure_keeps_quarantine_and_original_evidence` and `observation_slots.rs::full_budget_new_conflict_quarantines_without_retaining_evidence`. S on a reviewed order at full budget: B, `InvalidTransition` |
| 25 | CB×UO | C (STATE_LIFECYCLE §2 slot row; README "Observation reservation"): `observation_slots.rs::unrelated_event_flood_cannot_starve_promised_capture` and `observation_slots.rs::full_observation_budget_blocks_first_unknown_without_state_change`. `UnknownOperation` at full budget: B, `Capacity` with no state change (documented by the kernel README, not by the named contracts) |
| 26 | IU×QR | B: taken seats + quarantined operation → records `Rejected(OperationQuarantined)` |
| 27 | IU×UO | B: taken seats + an operation bound to an UNKNOWN order → records `Rejected(OperationAlreadyBound)` |
| 28 | QR×UO | C (ADR §6 "An unbound operation named in accepted conflicting evidence cannot later gain a fresh reservation binding"; addendum A): `transitions.rs::conflict_naming_unbound_operation_blocks_future_binding_without_changing_replays` (a reused event ID naming an unbound operation is a retained `Conflict`, not `UnknownOperation`). Send side, C (ADR §6 "Quarantine blocks a new external-send transition"): `transitions.rs::event_conflict_quarantines_both_bound_orders_and_blocks_payment_sending` (PaymentUnknown variant). Capture side, C: `observation_slots.rs::conflicting_event_cannot_spend_slot_reserved_for_capture` |

The 28 rows are the 28 pairs (PC×7, SV×6, FC×5, RT×4, CB×3, IU×2, QR×1). Pair
counts: 19 pairs have a new test (one each), 7 have an existing citation and 20 have
at least one class B sub-pair; most pairs carry more than one label.

## New tests and the clause each names

All in `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`. Each `///` doc
comment names "CONTRACT_INVARIANTS §5 / S5-PRECEDENCE", the pair and its clause.
Every test arms both guards on one call, asserts the contract-required outcome with
a whole-kernel `Eq` check on rejection (`refused`), and shows the losing guard is
live: on a clone, on a twin with free slots, or by the same input under a valid
context producing that guard's outcome (`replayed == false` for reserve).

| # | Test | Pair | Clause | Required outcome / live competitor |
|---|---|---|---|---|
| 1 | `altered_payload_conflicts_after_local_cancellation` | PC×FC(c) | L; ADR §7 | `CommandConflict`, Eq / fresh id records BusinessFenced; original replays |
| 2 | `altered_payload_conflicts_at_full_command_capacity` | PC×CB | L, B | `CommandConflict`, Eq / fresh id gets `Capacity`; original replays |
| 3 | `altered_payload_conflicts_when_its_selection_is_unavailable` | PC×IU | L | `CommandConflict`, Eq / fresh id records Unavailable |
| 4 | `altered_payload_conflicts_when_its_operation_is_quarantined` | PC×QR | L; ADR §6 | `CommandConflict`, Eq, order unreviewed / fresh id records OperationQuarantined |
| 5 | `altered_payload_conflicts_without_touching_an_unknown_payment` | PC×UO | L; ADR §6, STATE_LIFECYCLE §2 | after the deadline: `CommandConflict`, Eq, PaymentUnknown and slot kept / fresh id records OperationAlreadyBound |
| 6 | `unsupported_semantics_records_nothing_after_local_cancellation` | SV×FC(c) | V | R and O `UnsupportedSemantics`, Eq / v4 records BusinessFenced and applies ReturnRequired |
| 7 | `unsupported_semantics_records_no_unavailable_rejection` | SV×IU | V | `UnsupportedSemantics`, Eq / v4 records Unavailable |
| 8 | `unsupported_semantics_applies_no_quarantine` | SV×QR | V, Q | O and R `UnsupportedSemantics`, Eq, no quarantine / v4 Conflict and OperationQuarantined |
| 9 | `unsupported_semantics_neither_sends_nor_captures_an_unknown_payment` | SV×UO | V | S and O `UnsupportedSemantics`, Eq, Held/slot 0 then slot kept / v4 PaymentUnknown, PaymentConfirmed |
| 10 | `regressed_time_records_nothing_after_local_cancellation` | RT×FC(c) | T | R and O `ClockRegression`, Eq / valid time BusinessFenced, ReturnRequired |
| 11 | `full_command_capacity_backpressures_after_local_cancellation` | CB×FC(c) | B | `Capacity`, Eq / twin with free slots records BusinessFenced |
| 12 | `stale_execution_fence_records_no_unavailable_rejection` | FC(e)×IU | F | `ExecutionFenced`, Eq / current owner records Unavailable |
| 13 | `stale_execution_fence_applies_no_quarantine` | FC(e)×QR | F; ADR §6 | O and R `ExecutionFenced`, Eq, no quarantine / current owner Conflict and OperationQuarantined |
| 14 | `stale_execution_fence_neither_sends_nor_captures_an_unknown_payment` | FC(e)×UO | F; ADR §6, STATE_LIFECYCLE §2 | S and O `ExecutionFenced`, Eq, slot kept / current owner retries and gets PaymentConfirmed |
| 15 | `regressed_time_records_no_unavailable_rejection` | RT×IU | T | `ClockRegression`, Eq / valid time records Unavailable |
| 16 | `regressed_time_applies_no_quarantine` | RT×QR (+CB) | T, Q; addendum A | O and R `ClockRegression`, Eq, no quarantine, with free and with full evidence budget / valid time Conflict or state-changing Capacity, then OperationQuarantined |
| 17 | `regressed_time_applies_no_capture_to_an_unknown_payment` | RT×UO | T; STATE_LIFECYCLE §2 | `ClockRegression`, Eq, slot kept, nothing captured / valid time PaymentConfirmed |
| 18 | `full_command_capacity_backpressures_before_an_unavailable_rejection` | CB×IU | B | `Capacity`, Eq / twin records Unavailable |
| 19 | `full_command_capacity_backpressures_before_a_quarantine_rejection` | CB×QR (R) | B; ADR §6 | `Capacity`, Eq / twin records OperationQuarantined |

Command times strictly increase on every admitted call, so admitting equal times is
not relied on. The two existing pair tests named by the node
(`altered_payload_conflicts_before_fence_and_clock_guards`,
`replay_lookup_is_guarded_by_scope_and_semantics_only`) are cited, not duplicated.

## Existing coverage mapping (inspected before adding tests)

| Requirement | Prior classification and exact evidence | Gap addressed here |
|---|---|---|
| Payload conflict versus fence/time | Sufficiently covered: `contract_edge_cases.rs::altered_payload_conflicts_before_fence_and_clock_guards` | none (cited) |
| Replay versus scope/semantics/fence/time | Sufficiently covered: `contract_edge_cases.rs::replay_lookup_is_guarded_by_scope_and_semantics_only` | none (cited; replay is not a rejection guard) |
| Payload conflict versus cancellation, capacity, inventory, quarantine, UNKNOWN | Partially covered: `transitions.rs::identical_id_with_changed_payload_is_a_conflict`, `transitions.rs::response_loss_retry_returns_original_before_availability_check` (single guards) | T1–T5 |
| Version versus business guards | Partially covered: `transitions.rs::unknown_semantics_and_regressed_time_are_not_applied`, `observation_slots.rs::previous_semantics_version_is_rejected_without_silent_replay_change` (empty-state or single-guard) | T6–T9 |
| Fence/time versus business guards | Partially covered: `transitions.rs::historical_capture_after_owner_change_is_not_discarded`, `quarantine_capacity.rs::rejected_evidence_that_quarantines_also_advances_logical_time` | T10, T12–T17 |
| Record capacity versus recorded rejections | Partially covered: `transitions.rs::bounded_records_backpressure_without_evicting_old_results` (Capacity alone) | T11, T18, T19 |
| Cancellation/capacity versus quarantine and UNKNOWN on S/O | Covered by the C citations in rows 17, 18, 24, 25 and 28 | none (cited) |

## Class B characterizations (F-B6; observed, not semantics)

Observed against the locked kernel by a temporary, assertion-free probe test
(`runtime/crates/kix-kernel/tests/zz_tmp_s5_precedence_probe.rs`), run once with
`--nocapture` and deleted before the final verification; it is not part of the
patch. Every listed error left the whole kernel `Eq`-unchanged; recorded rejections
added only the command record. One probe initially reused event ID 1 for the
`UnknownOperation` × full-budget case, which exercised the conflict path instead;
it was re-run with a fresh event ID (result below).

- Version wins (`UnsupportedSemantics`) over: an altered payload; a stale fence
  (R/S/O); regressed time (R/S/O); full command records (R); a full observation
  budget (S/O); an unbound capture.
- A foreign scope wins (`WrongScope`) over: an altered payload under the same
  principal/request; a stale fence; cancellation; regressed time; full command
  records; taken seats; a quarantined operation.
- A stale fence wins (`ExecutionFenced`) over: regressed time (R/S/O); full command
  records (R); a full observation budget (S/O); an unbound capture.
- Regressed time wins (`ClockRegression`) over: a cancelled S; full command records
  (R); a full observation budget (S, and an unrelated O); a reviewed S; an UNKNOWN
  S retry after the deadline; an unbound capture.
- Cancellation: an S on a Held order at full budget → `InvalidTransition`; an
  unreserved O at full budget → `Capacity`; an UNKNOWN S retry → `InvalidTransition`;
  R records `BusinessFenced` over `Unavailable` and over `OperationQuarantined`;
  R with only order records full → `Capacity`.
- Only order records full, taken seats → `Capacity`.
- Reviewed S at full budget → `InvalidTransition`.
- Unbound O at full budget → `Capacity` (kernel README only).
- Taken seats + quarantined operation → records `OperationQuarantined`.
- Taken seats + operation bound to an UNKNOWN order → records `OperationAlreadyBound`.

Triples and combinations with `expire`, `cancel_scope` or `replace_owner` as the
guarded call were not explored. No class C violation was found: every pair the
contracts order produced the required outcome on the first run.

## Commands actually run and results

Commands run from the repository root unless noted; Cargo commands ran from `runtime/`.
Rust toolchain observed: rustc 1.98.1 / cargo 1.98.1. All Cargo verification uses the
offline lockfile. Every command ran in the foreground; no background long job.
Test totals are aggregated from the `test result` lines in the logs under
`.local/verification/s5p/` (ignored local artifacts, not tracked paths).

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse HEAD origin/main` | Initially clean; both SHAs as recorded above |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before editing and after all verification) | Exit 0; both required blobs match |
| `cargo fmt -p kix-kernel` (formatting the appended section), then `cargo test -p kix-kernel --locked --offline --test contract_edge_cases` | Exit 0; 34 passed (15 existing, 19 new), 0 failed, first run |
| `cargo test -p kix-kernel --locked --offline --test zz_tmp_s5_precedence_probe -- --nocapture` (temporary probe, twice; file deleted) | Exit 0 both times; class B observations as listed above |
| `cargo fmt -p kix-kernel -- --check` | Exit 0 |
| `cargo test -p kix-kernel --locked --offline --test contract_edge_cases` | Exit 0; 34 passed, 0 failed |
| `cargo clippy -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `cargo test -p kix-kernel --locked --offline` | Exit 0; 119 passed, 0 failed (9 result groups) |
| `cargo test --workspace --locked --offline` | Exit 0; 308 passed, 0 failed (43 result groups) |
| `cargo clippy --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; no warnings |
| `cargo fmt --all -- --check` | Exit 0 |
| `cargo tree -p kix-kernel --edges normal --locked --offline` | Exit 0; kernel depends only on kix-types |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; 2 positive controls and 66 negative fixtures |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; contracts=25; Counts copy matches |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; 16 negative controls |
| All 55 `python3` commands extracted in order from the `Stdlib offline document checks` run block in `.github/workflows/protocol.yml` | All exit 0 (55 commands, 0 failures); includes `check_docs_index.py` (scanned=283 indexed=248 allowlisted=35); log at `.local/verification/s5p/stdlib-document-checks.log` |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK |
| `python3 scripts/test_runtime_architecture.py` | Exit 0 |
| `git diff --exit-code --stat origin/main -- reference/v0.3-rc1 runtime/crates/kix-kernel/src runtime/crates/kix-kernel/tests/quarantine_capacity.rs runtime/crates/kix-kernel/README.md runtime/crates/kix-kernel/tests/support runtime/crates/kix-kernel/tests/e4_state_model.rs docs/contracts docs/adr docs/tasks docs/status/EVIDENCE_MAP_ROLLUP.md .aiops .github scripts` | Exit 0; empty protected-path diff |
| `git ls-files --others --exclude-standard -- reference/v0.3-rc1` | Exit 0; empty output |
| `git diff -U0 origin/main -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | Two hunks only: module doc paragraph, appended tail; existing tests unchanged |
| `git diff --check` | Exit 0 |

Closest CI equivalents inspected: `.github/workflows/ktx-kernel.yml` (architecture, kernel
tests, Clippy, formatting, dependency tree) and `protocol.yml` (workspace Rust boundary
and the stdlib document checks). Unrelated Move, TypeScript, local-chain, ZK and storage
jobs were not run for this test/map patch. No verification failure or repair retry occurred.

## Deviations and non-claims

- No fetch, publication, commits or hosted CI: explicit supervisor restrictions
  override the normal session-start fetch and final-head delivery workflow.
- The plan's `refused(k, call, want)` helper takes `want` before the closure, and two
  helpers were added (`seat_limits`, `recorded`) to keep the tests short. The plan's
  `quarantine_bound` helper is named `quarantine_pair`, avoiding the kernel's
  private method name.
- T1 alters the expected business epoch to the new epoch, so the altered payload
  would pass the business fence as a new command. T5's competing guard is the
  OperationAlreadyBound binding of the UNKNOWN operation, shown on a fresh identity.
  T16 runs with a free and with a full evidence budget, so the regressed conflict is
  checked against both the Conflict and the state-changing Capacity outcomes
  (RT×CB×QR); the plan placed that path under T16.
- The plan listed QR×CB as a repeat line of CB×QR; the matrix lists each of the 28
  pairs once.
- `r1_perf_probe` and the e4 summary record the blob of `contract_edge_cases.rs` at
  run time; that recorded value changes with this file and is not pinned anywhere.
- No complete precedence order: 19 finite examples order only the contract-defined
  pairs. Class B orders are not semantics. Source-informed authorship: the author
  read the locked kernel source, so this is not clean-room evidence. No capability
  grade change, no kernel, contract, ADR, kernel README, checker or `model_v4` change.
- No production readiness, durability, distributed fencing, bank exactly-once,
  chain finality or real-money claims. No external provider, production runtime,
  public endpoint, secret or Sui network was used.
- Follow-up candidates: contract-owner decisions on F-B6, chiefly whether a cancelled
  scope fences an UNKNOWN send retry, whether order-record exhaustion should block a
  recorded rejection that needs no order, and the relative order of recorded
  business rejections.
