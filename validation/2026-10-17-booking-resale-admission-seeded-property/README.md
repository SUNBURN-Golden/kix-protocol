# booking-resale-admission-seeded-property

Node: `plan-booking-resale-admission-seeded-property`. Resumed 2026-10-23 from the uncommitted 2026-10-17 draft; the directory date is retained to continue that draft. Adds `reference/booking_resale_admission/test_gate_properties.py` (17 tests, no skips or expected failures) and the support module `reference/booking_resale_admission/bra_property_support.py`. No existing file in the package, no contract, no CI file and no register row changed.
Issue: none. Depends on: `booking-resale-admission-deepening`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792148545 (loop-proposed node, not in `.aiops/program.json`).

Task input is the supervisor's node specification, design plan, resume note and owner decision in the session prompt; no node-specific document exists under `docs/tasks/`, and issue is none. The contract is [BOOKING_RESALE_ADMISSION_GATES.md](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md), including the adopted section 7 draft. The session read the repository entry documents and locks before editing. This session did not commit, push, open a pull request, create or close an issue, or comment.

Task branch/base HEAD = `9f0177ab45cf3ca704ecf5a152b3c1785c8f22a7` (`agent/kix-plan-booking-resale-admission-seeded-property`), also the design plan's `9f0177a`. Locally observed `origin/main` on resume = `fc28ad4eda7e49f34324d46253dfd950533740db`, 129 commits ahead (`git rev-list --count HEAD..origin/main`). This is a cached remote-tracking reference, not a fresh remote observation: the supervisor's explicit no-network rule overrides the AGENTS.md section 1 fetch. No fetch, sync, rebase or merge was performed. The earlier draft reported a fetch observing `9d0860c870e4a06f6b8e876cbee6446f50b22b15`; that is inherited history, not a command rerun in this resumed session.

The local main delta includes atomic-adopt changes in `resale_fsm.py` and `admission_fsm.py` and additional regression tests (nine booking package paths differ). `git diff HEAD origin/main --` those two modules shows `_commit_adopt` copying and rolling back gates. This worktree lacks those changes. The owner explicitly authorized a test-only characterization of residual divergence and completion with `STATUS: READY`; no implementation fix or decision request is needed in this node. The characterization below records the limitation rather than asserting universal atomicity.

**Builder-authored, not independent. Ready for supervisor handoff under that owner decision; no merge-ready claim.** Implementation/final task head SHA: not created (uncommitted work). KTX kernel CI run ID/status/conclusion and KIX protocol CI run ID/status/conclusion: not run/not available for this change. Merge SHA and post-merge CI: not applicable. Exact-head CI and non-author review remain the supervisor's gates.

Complete changed-path list:

- `reference/booking_resale_admission/test_gate_properties.py` (new tests)
- `reference/booking_resale_admission/bra_property_support.py` (new test support)
- `validation/2026-10-17-booking-resale-admission-seeded-property/README.md` (new validation record, resumed draft)
- `docs/README.md` (one pointer line)

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Nothing under `runtime/`, `reference/v0.3-rc1/`, `.aiops/`, `.github/`, `docs/tasks/`, `docs/contracts/` or `docs/decisions/` changed. The EV-BRA row in `docs/status/CURRENT_CAPABILITY_REGISTER.md` names `reference/booking_resale_admission/test_*.py` as a glob, which already matches the new file, so the register is unchanged and no grade moved.

## What the suite does

- Oracles are written from `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md` sections 2-5, 9.3-9.6, 10.6-10.8 and 11.4-11.6. They read a ledger fed only by accepted results, and public views (`view_show`, `view_right`, `view`, `view_presentation`, `canonical_state`). They do not call the machines' private `_invariant`.
- Four script families (`GateScript` on `MockGates`, `ReservationScript`, `ResaleScript`, `AdmissionScript`) run 12 fixed seeds (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233) of 80 steps each. The capacity cycles through 1, 2, 3, 4, 8, 16. Three buyer roles and two gate roles. The organizer and platform bps pair cycles through six pairs that include (10000, 0), (5000, 5000), (1, 1) and (0, 0). Valid candidates interleave with deliberately invalid variants (occupied slot, stale version, wrong holder, cap + 1, bps sum 10001, expired window, unpaid issue, second consume, external dependency).
- Only existing commands are used. `bind_settlement` is not generated and no settlement, ticket, ownership, venue or revocation source is injected. There is no wall clock, `urandom`, `uuid` or set iteration in the harness; synthetic `set_clock` inputs are deterministic. Choices come from tuples and sorted lists. Discovery is rerun under `PYTHONHASHSEED` 0 and 1 below.
- Coverage minima are asserted per family so a pass is not vacuous (for example `SLOT_OCCUPIED`, `STALE_VERSION`, `RESALE_CAP`, `ALREADY_CONSUMED`, `PAYMENT_FACT_REQUIRED` rejections, replay and changed-body probes, and a version above 2 reached through a resale chain).
- `MockGates` has no digest or journal. `GateScript` snapshots `_canonical(vars(gates))`; that is implementation-state characterization, labelled as such. Other oracles use public results/views; deliberate negative controls also access private state to inject faults.

## AGENTS.md section 7: existing coverage per property

Counted before this change: 47 tests in the package (`test_mock_gates` 11, `test_reservation_fsm` 11, `test_resale_fsm` 7, `test_admission_fsm` 14, `test_open_items` 4). "Sufficient" means a deterministic regression for the single path; the suite adds the seeded interleavings.

| Property | Existing coverage | Class | What the new suite adds |
|---|---|---|---|
| (a) one holder and one right per slot, held + issued <= capacity | `test_mock_gates.py::test_slot_release_before_payment_and_exclusivity`; `test_reservation_fsm.py::test_overlapping_holds_and_replay_do_not_double_book`, `::test_expiry_does_not_release_until_an_explicit_release` (scripted, capacity 1-2) | partially covered | Release, cancel, issue and adopt interleavings at capacity 1 to 16; ledger and view-row agreement after every accepted step |
| (b) issuance needs a bound order with an observed payment fact; a payment fact is not funds | `test_mock_gates.py::test_payment_fact_is_not_funds_and_expiry_does_not_compensate`; `test_reservation_fsm.py::test_unbound_issue_is_memory_evidence_without_economic_finality`, `::test_cancel_before_payment_frees_and_payment_blocks_compensation` | partially covered (single paths) | Every accepted issue checked against a ledger order and payment ref across random orders; unpaid, wrong-amount and reused-ref attempts; adopt carries the payment ref |
| (c) one consume per right version, version bump on transfer or consume, stale presentation rejected | `test_mock_gates.py::test_admission_consume_once`, `::test_stale_presentation_after_transfer_cannot_enter`; `test_admission_fsm.py::test_transfer_then_entry_rejects_both_presentations`; `test_reservation_fsm.py::test_cancel_after_issue_and_duplicate_consume` | sufficient for a single transition, partially covered for chains | Multi-hop version chains, stale and over-new versions for list, authorize and consume, `view_presentation` after each transfer |
| (d) resale price <= cap, bps sum <= 10000 | `test_mock_gates.py::test_resale_locks_and_policy_rejections`, `::test_show_registration_bounds` | sufficient at the boundaries | Ride-along oracle only: accepted listing <= cap, allocation parts non-negative and summing to the amount, bps in every show view. No standalone test |
| (e) a raising command leaves `state_digest` unchanged | none for rejected `adopt_issued`; other rejections are only spot-checked | partially covered | Digest and journal compared around every rejected command in every family, plus the isolated reproduction in section 4 |
| (f) `restore(export_journal())` at every prefix; same key returns the first result, changed body rejected | `test_reservation_fsm.py::test_restore_replays_a_lost_success_and_omits_rejections`; `test_resale_fsm.py::test_restore_replays_one_transfer_and_omits_rejections`; `test_admission_fsm.py::test_restart_replays_journal_and_retry_is_duplicate` (final state only) | partially covered | `restore(journal[:k])` compared with both canonical state and digest recorded at every prefix k, including empty; replay of an older accepted command after intervening transitions; repeated stored rejection; changed body (`IDEMPOTENCY_CONFLICT`) |
| (g) `reject_external` leaves the journal unchanged | `test_reservation_fsm.py::test_external_attempts_do_not_journal_and_resale_is_absent`; `test_resale_fsm.py::test_external_attempts_do_not_journal`; `test_admission_fsm.py::test_external_sources_fail_closed_without_being_read`; `test_open_items.py::test_live_refusals_match_the_unfilled_table` | sufficiently covered for fixed labels, partially covered mid-sequence | Mid-sequence checks over every label in `forbidden_commands()`, PG/venue labels and both external dependency kinds (`REVOCATION`, `VENUE_IDENTITY`) on all three machines |

Not generated, and left to the existing tests: settlement-bound `issue` and `accept_resale`, the injected ticket and ownership sources, and the composite Admission + Reservation + Resale topology. `test_restart_replays_journal_and_retry_is_duplicate` and `test_restore_fails_closed_when_ownership_moves` stay the coverage there.

## Negative controls

Each runs the same scripted scenario on a clean `MockGates` (the oracle passes and the guard rejects) and on a test-scoped in-memory copy (the oracle fails). The copies are a `unittest.mock.patch.object` of `mock_gates._require` that skips one code, or a `MockGates` subclass; nothing is written to disk and the patch is undone on exit.

| Control | Guard removed | Oracle that fails |
|---|---|---|
| `test_control_double_holder` | `SLOT_OCCUPIED` | "two active holders" |
| `test_control_double_consume` | single-consume guard (a consumed right accepts again) | "consumed twice" |
| `test_control_issue_without_payment` | `PAYMENT_FACT_REQUIRED` and the private invariant backstop | "without an observed payment fact" |
| `test_control_resale_cap` | `RESALE_CAP` | "exceeds the show's resale cap" |
| `test_control_rejection_mutates_state` | a `ReservationMachine` copy that applies `release` and then raises | digest and journal comparison |
| `test_seeded_sequences_find_each_removed_guard` | the seeded `GateScript` run over copies with `SLOT_OCCUPIED`, `RESALE_CAP`, `STALE_VERSION` and the consume guard removed | the random interleavings reach the same oracles; the clean copy raises nothing |

## Findings (AGENTS.md section 8)

### Residual class C/B: rejected `adopt_issued` on this branch base

Reproduction (isolated in `RejectedAdoptCharacterizationTests`, not generated by seeded sequences, which use fresh order IDs/payment refs when adopting):

1. Adopt `tix-1` in slot 0 with `order_id = ord-1` (accepted).
2. Adopt `tix-2` in slot 1 with the same `order_id = ord-1` and a fresh payment ref. It is rejected with `ORDER_BINDING_CONFLICT`.
3. `ResaleMachine`: `state_digest()` differs from step 1 even though the journal did not change; `restore(export_journal()).canonical_state()` differs from `canonical_state()`. `AdmissionMachine`: the digest and restore agree, because `canonical_state` does not render the gate slots.
4. Both machines: a later valid adopt of `tix-3` in slot 1 with a fresh order is rejected with `SLOT_OCCUPIED`, and a machine restored from the journal accepts it.

Cause, read from the code and confirmed by the reproduction: `_materialize` in `resale_fsm.py` and `admission_fsm.py` calls `reserve_slot`, then `bind_order`, then `observe_payment_fact` on the private `MockGates`. When a later step raises, the earlier gate mutation (slot `RESERVED`) is not rolled back. A reused `payment_ref` (`PAYMENT_BINDING_CONFLICT`) leaves the same residue.

Contract reading: the contract states that a rejected command does not enter the journal, and that `restore` of the same journal gives the same `canonical_state` and `state_digest` (sections 10.7 and 11.5 as read). For `ResaleMachine` the second sentence is violated. For `AdmissionMachine` the equal digest hides a slot that stays occupied in the live machine only, so live and restored machines diverge in later behaviour; the contract does not say that a rejection leaves slots untouched, so I record that half as class B and the Resale half as class C.

The reproduction also runs with a fresh order ID but reused payment ref, expecting `PAYMENT_BINDING_CONFLICT`. Both machines exhibit the same follow-up slot refusal. No `expectedFailure` hides the result: the tests explicitly verify this known legacy outcome, including the visible Resale digest divergence and hidden Admission residue. On atomic code the same tests instead require unchanged digest/canonical state and equal successful follow-up state between live and restored machines. This compatibility characterization accepts those two documented outcomes only; it is not a guard against reintroducing the legacy defect on a fixed base. Main's dedicated atomicity regressions remain necessary.

Owner decision in the task input: “if any residual divergence remains, Option 1/2 is authorized: keep the test-only change with documented characterization so the seeded property suite is green, remove DECISION_REQUIRED.md, and finish with STATUS: READY.” This specifically overrides the earlier blocked disposition for this residual path. `DECISION_REQUIRED.md` is absent (already absent on resume). No non-test package file was changed, and no broader atomicity claim is made. The cached main fixes were inspected, not executed or imported into this checkout. The supervisor must validate the final integrated base.

### Class B (contract undefined, recorded, no semantic change)

- Whether a rejected command must leave the private gate state untouched is not stated; only the journal and the restore-equality are.
- The private serialization used for `MockGates` rejection snapshots is an implementation-state characterization. No canonical digest API is specified there; it must not be generalized to durability or external state.
- The contract leaves product TTLs, authentication/revocation authority, payment attesters, compensation, seller payout, real provider facts and cross-channel currentness undefined or `UNDETERMINED` (adopted section 7). This suite adds no semantics or values for them.

Two replay distinctions are contract-defined (class A), not new class B semantics: sections 9.4/10.7/11.5 repeat stored rejections for the same key and body; section 1 allows direct `MockGates` duplicates to expose current views. The harness compares FSM first-response snapshots, but only immutable evidence for direct gate duplicates.

### Class A

Properties (a)-(e) hold on sampled direct-gate sequences; all (a)-(g) applicable to each FSM hold on its sampled sequences. Every accepted FSM journal prefix reproduces both canonical state and digest. The isolated legacy adopt path is the documented exception to (e)/(f); passing samples do not establish those properties for every possible command.

## Commands actually run and results

Run from the worktree root on resume (Python 3.13.5). Wall times are Bash's `time`; tests do not read it. The closest local CI scope is protocol.yml's offline-reference discovery, integration/readiness, offline-document checks and API pins. The CI discovery loop already includes this package. KTX's Rust workflow and the unrelated Sui/ZK/SDK jobs are not local equivalents for these test-only Python paths and were not run. CI uses Python 3.12, so that version remains untested locally.

| Command | Result |
|---|---|
| `git status --short`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git branch --show-current`, `git rev-list --count HEAD..origin/main` | Existing draft found; branch/base and cached main SHA above; 129-commit delta. No network action |
| `git diff HEAD origin/main -- reference/booking_resale_admission/resale_fsm.py reference/booking_resale_admission/admission_fsm.py` | Cached main contains `_commit_adopt` rollback in both; branch base does not |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_gate_properties.py -v` | Initial inherited draft: 17 tests OK, expected failures=2. Intermediate revision: 2 errors from an incorrectly invoked test-side `reconcile()`; removed that unnecessary assertion. Subsequent runs: 17 tests OK, no skips/expected failures. Timed narrow run: 4.926 s wall |
| `/usr/bin/time -p env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Timing wrapper unavailable (exit 127); no tests started. Switched to Bash `time` |
| `time PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 64 tests (47 existing + 17 new), OK with no skips/expected failures; 6.510 s wall, under 30 s. Earlier full run: 4.091 s wall, also OK |
| `for seed in 0 1; do time PYTHONHASHSEED="$seed" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission 2>&1 \| tail -n 5; done` (with `set -o pipefail`) | Both runs: 64 tests OK, no skips/expected failures; 7.959 s and 6.763 s wall respectively |
| `for suite in settlement_f01_f03 credit_advance_f04 ai_delegation token_reward; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" \|\| exit "$?"; done` | All OK: 22, 26, 22, 61 tests respectively |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest integration_gate.test_http_gate readiness.test_faults 2>&1 \| tail -n 8` (with `set -o pipefail`) | 58 tests OK, 6.803 s unittest time. HTTP fixtures use local loopback only |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py` and same with `--self-test` | Both exit 0; paths=231, ev_ids=15, original32=32; self-test pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` and same with `--self-test` | Both exit 0; scanned=147, indexed=112, allowlisted=35; self-test pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_openapi_contract.py` and same with `--self-test` | Both exit 0; commands=84 (core=40, fsm=44); self-test pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_integration_gate_openapi.py` and same with `--self-test` | Both exit 0; commands=84, productionEndpoint=false, publicHost=false; self-test pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_profile_traceability.py` and same with `--self-test` | Both exit 0; blueprint=47, profile=47; self-test pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_read_model_source_map.py` and same with `--self-test` | Both exit 0; queries=13, anchors=128, catalogues=2, citations=145; self-test pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_i12_proof_ids.py` and same with `--self-test` | Both exit 0; proof_headings=4, proof_keys=10, pack_keys=14; self-test pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_delegation_layer_matrix.py` and same with `--self-test` | Both exit 0; rows=36; self-test pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py` and same with `--self-test` | Both exit 0; rows=23; self-test pass |
| `git diff --check` | Exit 0; no whitespace errors in the tracked diff. New Python files also inspected |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 runtime .aiops .github docs/tasks docs/contracts docs/status/CURRENT_CAPABILITY_REGISTER.md` | Exit 0; protected paths and register unchanged from branch HEAD |
| `git status --short` and local path enumeration | Only the four changed paths listed above; no `DECISION_REQUIRED.md` present |
| `PYTHONDONTWRITEBYTECODE=1 python3 -` (inline stdlib scope/syntax audit) | Exit 0: `git status --porcelain --untracked-files=all` exactly matches the four-path whitelist; all four files end in newline without trailing whitespace; both new Python files compile in memory; existing package files have no diff; decision file absent |

Also run: the four script families directly with an inline stdlib Python coverage summary (exit 0). Accepted effects across the 12 seeds were Gate: 20 issues, 9 transfers, 6 consumes; Reservation: 25 issues, 16 consumes; Resale: 42 adopts, 18 transfers; Admission: 49 adopts, 35 consumes. Release/cancel paths and invalid-command probes were reached. These are fixture coverage observations, not performance measures. Later expanded external-label probes do not change random command choices.

## Deviations and remaining work

- No fetch or base synchronization: supervisor prohibited GitHub/network actions and branch changes. Cached main is ahead; local results apply only to the branch base plus this uncommitted patch.
- The design's 40-step suggestion was retained from the earlier draft as 80 steps per seed; the measured suite stays under 30 s and reaches multi-hop resale chains. There are more negative controls than the minimum two.
- Replaced the design's two `expectedFailure` reproductions with the owner's authorized precise legacy/atomic characterization. Residual class C/B behavior is recorded, not fixed. The seeded generators use unique order IDs/payment refs for adopts and do not claim coverage of that residual path under the strict atomicity oracle.
- The validation directory keeps the initial draft's date; the pointer identifies the resume date. EV-BRA already uses `test_*.py`, so no register edit or grade change was needed.
- No implementation/final commit, exact-head CI, non-author audit, merge, or post-merge verification performed. The supervisor owns those stages and testing after base integration. Settlement-bound issuance/transfer and injected-source topologies remain covered by existing examples rather than these sequences.

## Non-claims

- Builder-authored, not independent. The oracles read implementation outputs, so an error shared with the contract reading is possible.
- Fixed seeds are a sample, not exhaustive. Passing 12 seeds is not a proof of any property.
- MOCK only (`MOCK_GATE_ONLY`). No chain currentness, no durable reservation, no real payment or provider fact, no bank, PG, KYC, Sui or public endpoint.
- No new command, flag, limit, policy value or protocol surface. Fixture values (capacities, `PRICE = 10_001`, `RESALE_CAP = 20_000`, bps pairs, windows) are synthetic and not policy.
- No grade change and no performance claim beyond the local under-30-second acceptance check. This is a local supervisor handoff under the owner's exception, not independent review or merge authorization.

## 2026-10-23 paused-merge resolution and integrated-tree validation

This addendum records the supervisor-requested resolution of the already-paused
merge. It supersedes the earlier checkout/base limitations for the integrated
working tree; the preceding results and findings remain historical evidence.
The task input is the supervisor's conflict-resolution request in this session,
with no node-specific task document or issue. This is not ASTRA program mode.

Task/implementation HEAD remains `047d08e34659a5c392a0a0b08883846253c2aef8`.
Cached `origin/main` and `MERGE_HEAD` are both
`fc28ad4eda7e49f34324d46253dfd950533740db` (129 main-side commits beyond HEAD).
No fetch was performed because the supervisor expressly prohibited network
operations. The merge was already in progress at session start; it was not
restarted, aborted, rebased or committed. Final task/merge SHA does not yet exist.

The sole conflict was `docs/README.md`. Its resolved content is byte-for-byte
main's index plus this node's existing pointer, placed under the October 17
heading to match the validation directory. All newer main sections, lists,
links and wording remain intact. Session-edited paths are exactly
`docs/README.md` and this validation record. The other staged changes were
already supplied by the supervisor's merge; no production, package, workflow,
contract, task-document or policy source was edited in this resolution.

The original AGENTS.md section 7 property mapping above remains the pre-addition
coverage map; no new tests were needed for this conflict resolution. Main now
also contributes `test_adopt_issued_atomicity.py`: its inherited order-binding,
payment-binding, retry and rollback regressions all pass in full discovery.
The earlier legacy class C/B finding concerns the old branch base; main's atomic
implementation is now present and tested. No new contract violation or undefined
semantic choice was found. The existing class B uncertainties and all MOCK
non-claims remain. The compatibility characterization is still not a substitute
for main's strict atomicity regressions.

Commands below ran on the resolved integrated working tree, using Python 3.13.5.
All required local suites and documentation checks exited 0. CI's Python 3.12 was not tested here.

| Command | Result |
|---|---|
| `git status --short`; `git rev-parse HEAD origin/main MERGE_HEAD`; `git branch --show-current`; `git rev-list --count HEAD..MERGE_HEAD` | Correct task branch; hashes and main-side delta recorded above; one initial unmerged path, `docs/README.md` |
| Inline stdlib resolver comparing the result with `git show MERGE_HEAD:docs/README.md` | Exact main content plus one node pointer; moved into the matching October 17 section |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_gate_properties.py -v` | 17 tests OK in 4.765 s, including the double-holder and double-consume negative controls; no skips or expected failures |
| `time PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 179 tests OK in 5.668 s; 5.832 s wall, below 30 s |
| `for suite in settlement_f01_f03 credit_advance_f04 ai_delegation token_reward; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" \|\| exit "$?"; done` | All OK: settlement 184, credit 146, AI delegation 70, token reward 156 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest integration_gate.test_http_gate readiness.test_faults` (output redirected to `/tmp/bra-merge-integration-tests.log`) | 96 tests OK in 5.534 s; local loopback fixtures only |
| `for checker in check_status_register check_docs_index check_openapi_contract check_integration_gate_openapi; do PYTHONDONTWRITEBYTECODE=1 python3 "scripts/$checker.py" \|\| exit "$?"; PYTHONDONTWRITEBYTECODE=1 python3 "scripts/$checker.py" --self-test \|\| exit "$?"; done` | All four plain checks and all four self-tests pass. Register: paths=331, ev_ids=15, original32=32. Index: scanned=213, indexed=178, allowlisted=35. API: commands=84; productionEndpoint=false, publicHost=false |
| `git diff --check`; `git diff --cached --check` | No whitespace errors |
| Inline stdlib byte-preservation and marker scan using `git ls-tree -rz`, `git show HEAD:<path>` and `git ls-files -z` | All 121 protected tracked files match HEAD bytes, no protected untracked additions, no conflict markers in tracked working files, and main index preserved plus exactly one node pointer. Initial non-NUL path listing failed on Git-quoted Korean filename (exit 1); corrected NUL-delimited scan passed (exit 0) |
| `git add docs/README.md validation/2026-10-17-booking-resale-admission-seeded-property/README.md` | Could not stage: Git metadata is mounted read-only; creation of `index.lock` was refused (exit 128). Resolved working files remain in place; supervisor must stage them before committing |

Locked kernel blobs were verified before and after resolution against the two
required hashes in the Locks section above. All tracked `reference/v0.3-rc1/`
files, both locked kernel files, `.aiops/` and `docs/tasks/` remain byte-identical
to task HEAD; no untracked files were added in those paths. Final preservation
and conflict-marker checks are reported in the supervisor handoff. The index still
contains the three original conflict stages for `docs/README.md` because the
read-only Git metadata prevents staging; this is a mechanical supervisor step,
not an unresolved content or product decision.

No commit, push, GitHub action, external post, merge abort, or reset was performed.
KTX and KIX exact-head CI run IDs/status/conclusions, non-author review and
post-merge checks are unavailable in this no-network uncommitted session and
remain supervisor gates. READY here means the conflict resolution and required
local checks are ready for supervisor handoff; it is not merge authorization.
Builder-authored, not independent; MOCK only; no chain currentness, durable
reservation, real payment/provider fact, new command or policy value claimed.
