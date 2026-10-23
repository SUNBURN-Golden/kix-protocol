# credit-f04-seeded-property-suite

Node: `plan-credit-f04-seeded-property-suite`. Adds a seeded, stdlib-only property suite for `MockCredit` and `CreditMachine`: `reference/credit_advance_f04/test_credit_properties.py` and its non-test support module `reference/credit_advance_f04/credit_property_support.py`.
Issue: none. Depends on: `f04-mock-deepening`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792148545 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files.

Observed `origin/main` = branch HEAD = `9d0860c870e4a06f6b8e876cbee6446f50b22b15` (`git fetch origin main` succeeded; no delta).

**This suite is builder-authored. It is not an independent PASS, not a regulated credit product, and not a loan or payment. MOCK only. No real funds, no collateral or loss treatment. It does not implement or close the pending `fin-credit-exposure-reconciliation` node or the F04 real-funds lock.** Fixture numbers are synthetic KRW integers, not policy values.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. `mock_credit.py`, `credit_fsm.py`, `open_terms.py`, the three existing test files, `docs/contracts/`, `reference/v0.3-rc1/`, `.aiops/`, `.github/`, `docs/tasks/` and `runtime/` are unchanged.

## What the suite does

- Fixed seed list `SEEDS = (1, 2, 3, 5, 8, 13, 21, 34)`, `random.Random(seed)` only. No wall clock, no `os.urandom`, no network, no file access. Same result under `PYTHONHASHSEED` 0, 1, 2 and random.
- Oracles are typed in from `CREDIT_ADVANCE_F04.md` sections 1-4 and 7 (money ceiling, 14 always-false flags, section 4 and 7.8 code tables, section 3 order of checks, section 7.2 phase table, 7.5 gate conditions, 7.6 kind tables) and from the open-terms boundary (`decided_value` None, option A, `UNDETERMINED`, no `apr_bps`/`schedule`). Nothing is imported from the mock or FSM except the objects under test and their exception types. `test_typed_oracles_agree_with_the_modules` compares the typed tables with the modules' private tables, so a drift shows.
- `MockDriver` drives `note_advance`, `release_note`, `attempt_execution` and lookups over three claims (gross 90 000, `MONEY_MAX`, 7) with plain, later-settlement, open-refund and reclassified faces. Its oracle follows the section 3 order exactly.
- `MachineDriver` drives offer, approve, reject, cancel, bind_settlement, draw, repay, close, default, reconcile, `reject_unsupported` and `attempt_execution`, plus key replays, changed-body and cross-op key reuse, and stub ticks. For a rejected call the expected set is the set of violated contract predicates; the raised code must be a member. Precedence among several violated predicates is not asserted (class B).
- The settlement source is `StubSettlementSource` in the support module (test-side): `view()` only, fresh copies, read counter, forward-only phases, COMMITTED sticky. Defective views (failed, wrong claim, gross mismatch, finality flag, bank-debit flag, unregistered id) are fixed per id and never injected after an accepted bound draw, so restore stays valid. It is not a real service and `SettlementMachine` is not imported.
- A coverage guard in each seeded test requires every named op family and the contract codes to occur at least once across the seeds.
- Cash and `recovery_due` in fixtures are large (up to `MONEY_MAX`) so any leak into capacity shows.

| Property | Where |
|---|---|
| (a) bounded non-negative integers, `outstanding + repaid = drawn`, `drawn <= amount`, repayment list = model, sequence gap-free, `reserved <= open_face`, `residual = open_face - reserved` | `check_view` / `check_claim_numbers` after every call in `MockPropertyTests` and `MachinePropertyTests` seeded runs (8 seeds) |
| (b) shared ceiling, cash and `recovery_due` never add capacity | seeded runs with an independent reserved sum; `test_ceiling_boundary_is_exact_and_cash_never_adds_capacity` (+/-1 at 90 000, 7 and `MONEY_MAX`) |
| (c) draw only after COMMITTED; frozen face | `check_gate_matrix` (every stub phase and defect, unregistered id, no source), `test_a_gate_rejected_key_stays_rejected_after_commit_and_a_new_key_succeeds`, `test_the_face_snapshot_stays_frozen_after_later_settlement_changes` |
| (d) open refund blocks, release is not repayment | `test_open_refund_blocks_a_note_and_a_later_settlement_face_is_frozen_out`, `test_release_returns_exactly_the_noted_amount_and_is_not_repayment`, `test_an_open_refund_blocks_a_draw_and_a_release_is_not_a_repayment` |
| (e) close rejected while exposure remains | generic transition oracle (`OUTSTANDING_REMAINS` in the seeded guard); no dedicated test |
| (f) rejected call leaves digest and journal unchanged; key replay returns the first result; changed body rejected | `MachineDriver.call`, `do_replay`, `do_conflict` on every call |
| (g) `restore(export_journal())` reproduces digest and canonical state | every 25 steps for 8 seeds; every journal prefix for seeds 1, 8, 21 against the live digest recorded when each entry was written |
| (h) `reject_unsupported`, `attempt_execution` leave the journal unchanged | `test_unsupported_and_execution_refusals_are_inert_in_every_phase` (all 7 phases plus unknown id, all kinds) and the seeded driver |

## AGENTS.md section 7: existing coverage first

"Sufficiently" means every sentence of the property is held by a cited test whose body I read (I read the bodies of the limit-race, close, bound-draw, reconcile and duplicate-draw tests; the others by name and assertions listed in the grep of their bodies).

| Property | Class | Existing tests (exact names) | What this suite adds |
|---|---|---|---|
| (a) relations | partially covered | `test_offer_approve_draw_repay_and_close_are_mock_ledger_only` (five fixed points) | the relations on every view after every call in seeded interleavings, `MONEY_MAX` claim, model compared field by field |
| (b) shared ceiling, cash is not capacity | partially covered | `test_limit_race_is_ordered_and_cash_is_not_capacity` (one gross, fixed amounts), `test_confirmed_cash_and_recovery_are_not_capacity`, `test_claims_do_not_share_a_ceiling_and_the_snapshot_stays_frozen` | boundary +/-1 over three grosses incl. `MONEY_MAX` with cash and `recovery_due` at `MONEY_MAX`; seeded reservations with an independent sum |
| (c) COMMITTED gate, frozen face | partially covered | `test_bound_draw_waits_for_mock_commit_and_does_not_claim_finality` (CAPTURED, FAILED, COMMITTED), `test_adopted_boundary_does_not_price_rank_or_recalculate` (frozen) | INITIATED and AUTHORIZED, each defect class, `UNKNOWN_SETTLEMENT`, rejected claim stays unregistered, rejected key stays rejected after COMMITTED (section 7.3), stub unchanged and read only on draw/reconcile |
| (d) refund blocks, release is not repayment | mock level sufficiently covered; machine level partially | `test_open_refund_blocks_and_release_is_not_repayment`, `test_refund_freeze_and_bad_inputs_follow_the_wave5_predicate` | machine-level close/release flow with `repaid_exposure` equal to the repay sum; reclassified face (open_face 0) in the seeded runs |
| (e) close while exposure remains | sufficiently covered for the fixed case | `test_close_rejects_remaining_exposure_before_release` | nothing dedicated; the seeded oracle applies it on every close |
| (f) inert rejection, key replay, changed body | partially covered | `test_same_draw_and_repay_notes_do_not_apply_twice` and the per-test `codes(...)` checks | whole-state digest and journal comparison around every rejection for every code the generator reaches; replay of accepted and rejected keys; cross-op and cross-advance key reuse |
| (g) restore reproduces | partially covered | `test_reconcile_replays_the_journal_without_a_second_draw` (one final state) | seeded sequences, every prefix against the live digest, restore every 25 steps |
| (h) unsupported / execution refusals | partially covered | `test_unsupported_product_and_real_funds_do_not_change_state`, `test_execution_attempts_do_not_change_the_note` | every phase and unknown id, all 20 kinds and non-kinds, journal and digest and stub compared |

## Negative controls

In `NegativeControlTests`, each control patches an attribute in memory with `unittest.mock.patch.object` (source files are never edited), runs the same drivers and requires `AssertionError`, not `CreditError`. After each control the patched attribute is the original again (`assertIs`). Observed first failure messages:

| Control | First oracle failure |
|---|---|
| mock `_require` no-op for `ADVANCE_EXCEEDS_OPEN_FACE`, `MockCredit._invariant` silenced | mock driver: `note_advance accepted but the contract says ADVANCE_EXCEEDS_OPEN_FACE` |
| same, `CreditMachine._invariant` also silenced | machine driver: `draw was accepted but violates {'ADVANCE_EXCEEDS_OPEN_FACE'}` |
| `credit_fsm._require` no-op for `SETTLEMENT_NOT_COMMITTED` | gate matrix: `draw gave None, expected SETTLEMENT_NOT_COMMITTED`; seeded: `draw raised ADVANCE_EXCEEDS_OPEN_FACE, expected ('err', {'SETTLEMENT_NOT_COMMITTED'})` |
| rejected `repay` writes a label field before re-raising | digest changed after a rejected call |
| `export_journal` drops its last entry | journal growth is not one |
| `restore` skips `repay` entries | restore or reconcile disagrees with the live machine |

## AGENTS.md section 8: discrepancy classes

No class C (explicit contract violation) was found. No blocker. Each item below was reproduced in this session.

| # | Behaviour | Class | Handling |
|---|---|---|---|
| i | `attempt_execution` on a case with no note (OFFERED, APPROVED, REJECTED, CANCELLED) raises `UNKNOWN_ADVANCE`. Contract sections 3 and 7.6 order id, kind, note existence, then the refusal code, and say the machine's call is section 3 as is. | A (matches section 3); recorded because it reads oddly | oracle exact; a kind outside the list still gives `EXECUTION_KIND` first |
| ii | The draw gate reads phase, ids, currency, gross and the listed flags only. A settlement view carrying `refund_face` does not block an approved draw; a refund is visible to the machine only through the face snapshot given at offer. Contract section 7.5 lists the conditions and does not name refund fields. | B | `test_b_the_gate_does_not_read_refund_fields_of_the_settlement_view` |
| iii | The frozen claim face is not cleared after every note on the claim is released. Contract sections 2 and 7.2 say the first accepted note freezes the claim and do not speak of un-freezing. | B | `test_b_the_frozen_face_is_not_cleared_when_every_note_is_released` |
| iv | After a case is terminal, a draw or repay resent under a new key with the same `draw_id` / `repay_id` and binding returns a duplicate (journal unchanged); a different `draw_id` gives `TERMINAL_IMMUTABLE`. Contract section 7.2 gives duplicate and terminal rules separately and not their combination. | B | `test_b_a_terminal_case_still_answers_a_resent_draw_and_repay_as_duplicates` |
| v | A not-yet-noted case whose face differs from its claim's frozen face reports the claim-level `open_face` in `view` (reproduced: 80 000 against its own face's 0). | B | not asserted; checks use the case view only when the faces match |
| vi | Which code is raised when several preconditions are violated at once. Sections 4 and 7.8 list codes, not precedence (except the section 3 order and the section 7.5 gate-before-note rule, which are asserted exactly). | B | set membership only |
| vii | A rejection whose code is `INVALID_ID` is stored against its key by the implementation. Contract 7.3 says only that a bad key format does not hold the key. | B | the replay history never replays `INVALID_ID` rejections |

## Changed paths

| Path | Change |
|---|---|
| `reference/credit_advance_f04/test_credit_properties.py` | New. 5 test classes, 22 tests (1 constants, 4 mock, 8 machine, 3 class B, 6 negative controls); 48 in the package, 26 existing. |
| `reference/credit_advance_f04/credit_property_support.py` | New non-test support: seeds, contract literals, faces, stub, oracles, `MockDriver`, `MachineDriver`, gate matrix. ASCII only, stdlib plus the modules under test. |
| `validation/2026-10-17-credit-f04-seeded-property-suite/README.md` | This record. |
| `docs/README.md` | One index bullet. |
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | EV-CREDIT fixture cell only: `test_credit_properties` added to the brace list. Grade, sync-basis lines, the dated "20 tests" record and the `fin-credit-exposure-reconciliation` row untouched. |

No workflow edit: the existing loop over `settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward` in `.github/workflows/protocol.yml` discovers the new file. Module names are unique (`credit_property_support`), because `readiness/conformance.py` puts several reference directories on `sys.path`.

## Commands actually run

All from the repository root with `PYTHONDONTWRITEBYTECODE=1`. The credit package runs 48 tests (26 existing + 22 new) in about 7 s on Python 3.13.5 and 3.12.15, under `PYTHONHASHSEED` 0, 1, 2 and random. The other suites in the CI loop, `integration_gate.test_http_gate`, `readiness.test_faults` and the seven check scripts (plain and `--self-test`) stayed green. The per-command results are in the final report of the session.

Not run: Cargo steps of `ktx-kernel.yml` and `protocol.yml` (no Rust touched; the locked-blob check is the substitute), Sui, Node and ZK steps.

## Non-claims

Builder-authored, not an independent PASS. MOCK only; not a regulated credit product, loan, underwriting, KYC or payment. No real funds, bank, PG or KYC call; no collateral, perfection, loss or write-off treatment; no durable store. It asserts no APR, fee, rank, party, perfection or limit-recalculation formula (all `UNDETERMINED`). It does not implement or close `fin-credit-exposure-reconciliation` or the F04 real-funds lock (`F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md` stays proposed). Random coverage is a fixed corpus of 8 seeds, not exhaustive. A matched restore is equality of this process's journal and views, not bank exactly-once or chain finality. The settlement stub is a test double, not a `SettlementMachine`.
