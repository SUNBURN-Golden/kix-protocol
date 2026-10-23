# settlement-seeded-property-suite

Node: `plan-settlement-seeded-property-suite`. Adds a seeded, stdlib-only property suite for `MockSettlement` and `SettlementMachine`: `reference/settlement_f01_f03/test_settlement_properties.py` and its non-test support module `reference/settlement_f01_f03/settlement_property_support.py`.
Issue: none. Depends on: `settlement-policy-deepening`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792148545 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files.

Observed `origin/main` = branch HEAD = `9f0177ab45cf3ca704ecf5a152b3c1785c8f22a7` (`git fetch origin main` succeeded; no delta). Branch `agent/kix-plan-settlement-seeded-property-suite`.

**This suite is builder-authored. It is not an independent PASS, not an accounting or legal treatment, and not a payment. No grade is raised. It does not implement or close the pending `fin-multi-payee-refund-proof` node.** Fixture numbers are synthetic KRW integers, not policy values.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. `mock_settlement.py`, `settlement_fsm.py`, the three existing test files, `docs/contracts/`, `reference/v0.3-rc1/`, `.aiops/`, `.github/`, `docs/tasks/` and `runtime/` are unchanged.

## What the suite does

- Fixed seed list `SEEDS = (1, 2, 3, 5, 8, 13, 21, 34)`, `random.Random(seed)` only, choices from sorted tuples. No wall clock, no `os.urandom`, no network, no file access. Same result under `PYTHONHASHSEED` 0, 1, 2 and random.
- Oracles are typed in from `SETTLEMENT_DISTRIBUTION_F01_F03.md` sections 1-6 and 9 (money ceiling, six always-false flags, the section 6 code table, the section 9.2 phase table). Nothing is imported from the mock except the objects under test. The split is `Fraction` floor; distribution uses prefix-clipped takes, not the mock's running remainder.
- `Mirror` tallies each claim only from the arguments of calls that succeeded. For a rejected call the expected-violation set comes from the contract preconditions; the raised code must be a member of that set. Precedence among several violated preconditions is not asserted (class B, below).
- A coverage guard in each seeded test requires every named code family and operation to occur at least once across the seeds, and at least one first full-gross refund, so a run cannot pass vacuously.

| Property | Where |
|---|---|
| (a) faces sum to gross, fee is the floor | `SplitPropertyTests`: 12 gross x 6 bps grid, 320 seeded draws, out-of-range inputs open no claim |
| (b) `face = distributed + cancelled_unpaid + outstanding`, `outstanding >= 0`, `distributed <= confirmed cash`, claims share no cash | `ConservationPropertyTests`: 8 seeds x 120 random calls over three claims (gross tiny, mid, `MONEY_MAX`) plus unknown ids; directed `MONEY_MAX` run |
| (c) a `SettlementError` leaves every claim view byte-identical (canonical JSON) | same driver, snapshot of all views before every call |
| (d) identical repeat is `duplicate True`, `applied None`, no change; changed field raises its own `*_BINDING_CONFLICT`, no change | `BindingPropertyTests`: claim, statement, refund, acceptance, one field at a time |
| (e) rejected FSM command leaves `state_digest` and journal unchanged; `restore(export_journal())` reproduces `state_digest` and `canonical_state`; a replayed key returns the first result | `MachinePropertyTests`: 8 seeds x 80 commands over three settlement ids, restore every 10 steps and at the end, every journal prefix of three seeds |

## AGENTS.md section 7: existing coverage first

"Sufficiently" means every sentence of the property is held by a cited test whose body I read.

| Property | Class | Existing tests (exact names) | What this suite adds |
|---|---|---|---|
| (a) split sum and fee floor | partially covered | `test_f01_fee_floor_zero_fee_and_rejected_policies` (gross 1, bps 0 and 10000, rejected policies), `test_f01_split_opens_obligations_without_cash_or_legal_binding`, `test_adopted_policy_posture` (gross 3 at 5000) | bps 1 and 9999, `MONEY_MAX` and `MONEY_MAX - 1`, seeded gross and bps, the floor as an inequality, out-of-range bps and gross opening no claim |
| (b) line identity, `outstanding >= 0`, no over-distribution, no shared cash | partially covered | `test_f02_later_cash_continues_on_the_frozen_order`, `test_f02_caller_order_selects_shortfall_and_then_freezes`, `test_f03_full_refund_reclassifies_and_mock_acceptance_is_not_closure`, `test_f03_partial_after_distribution_does_not_claw_back`, `test_claims_do_not_share_cash`, `test_later_statement_stays_on_commit_and_cases_do_not_share_cash` (fixed cases) | the identity checked on every line after every call in seeded interleavings of all five operations, three claims with identical payee labels, `MONEY_MAX` boundary, an independent contract model compared field by field |
| (c) rejected call leaves state identical | FSM level sufficiently covered for fixed cases; mock level not covered | FSM: `test_illegal_transitions_do_not_move_the_phase`, `test_terminal_fail_and_cancel_are_immutable`, `test_commit_fault_is_outside_the_journal_and_replay_stays_captured`, `test_external_payment_attempts_leave_the_journal_unchanged`. Mock level: none compares a whole view around a rejected call | whole-view canonical-JSON comparison at mock level, for every rejection code the generator reaches (the guarded list in `ConservationPropertyTests.REQUIRED`) |
| (d) duplicate and conflict | partially covered | `test_f01_split_opens_obligations_without_cash_or_legal_binding`, `test_f02_statement_does_not_infer_fee_or_shrink_faces`, `test_f03_full_refund_reclassifies_and_mock_acceptance_is_not_closure` | `REFUND_BINDING_CONFLICT` had no test (the code occurs only at `mock_settlement.py:255`); per-field mutations for all four bindings; unchanged view after each conflict and each duplicate |
| (e) restore, digest, key replay | partially covered | `test_same_key_replays_and_a_different_body_is_rejected`, `test_reconcile_matches_restore_and_does_not_enter_the_economic_journal`, `test_refund_block_survives_replay_and_is_not_a_clawback`, `test_happy_path_posts_mock_economics_without_external_execution` | seeded sequences including invalid commands, restore at every 10th step and at every prefix, replay of accepted keys live and after restore, replay of rejected keys, changed-body conflict, phase table and no-backwards-phase checked on every accepted or rejected command |

## Negative controls

In `NegativeControlTests`, each control patches an attribute in memory with `unittest.mock.patch.object` (source files are never edited), silences `MockSettlement._invariant` for the two arithmetic controls so the mock's own `MOCK_INVARIANT` guard cannot mask the oracle, runs the same drivers, and requires `AssertionError` (not `SettlementError`). Observed failure messages, first failing seed:

| Control | First oracle failure |
|---|---|
| `_split` drops one won from the larger line | seed 1: `faces do not sum to gross`; the grid check `check_split(1000, 500)` also fails |
| `_outstanding` ignores `cancelled_unpaid` | seed 2: line identity broken after a full-gross refund (`cancelled_unpaid` 1, `outstanding` not 0) |
| rejected `observe_settlement_statement` mutates `confirmed_cash` before re-raising | `view changed after a rejected call` |
| `export_journal` drops its last entry | seed 1: `initiate: journal grew by other than one entry` |
| `restore` clears the idempotency table (fifth control) | `restored machine rejected the replay of <key>` |

After each control the patched attribute is the original again (`assertIs`).

## AGENTS.md section 8: discrepancy classes

No class C (explicit contract violation) was found. No blocker.

| # | Behaviour | Class | Handling |
|---|---|---|---|
| i | The FSM accepts and journals `observe_statement`, `bind_refund` or `observe_mock_cancel_acceptance` under a new key when the book already holds that binding (`duplicate False` at FSM level, `applied` = the op, journal +1, economics unchanged). Reproduced. Contract sections 1 and 9.3 define key replays and binding repeats, not this combination. | B | `test_e_characterization_new_key_repeat_of_a_bound_statement_is_economically_inert` asserts only that the claim view is unchanged and restore reproduces the digest. |
| ii | Which code is raised when several preconditions are violated at once. Section 6 lists codes, not precedence. | B | Oracle checks set membership only. |
| iii | A `commit` with `amount = 0` followed by `distribute` is accepted, applies 0 to every line and freezes the order (reproduced). Contract section 9.2 says (translated) that the zero-cash order freeze remains a predicate of direct ledger calls and is not in this machine's accept path. I read that sentence as descriptive, not as a requirement to reject. | B, reviewer to confirm | `test_e_characterization_zero_cash_commit_then_distribute_conserves` asserts conservation only and does not pin the freeze. If the reviewer reads the sentence as normative, this becomes class C: no change to the mock or FSM, report as a blocker, this record is then not a merge-ready claim. |
| iv | A rejected key stays bound to its error for the life of the process and is forgotten by `restore`. | A | Contract sections 9.3 and 9.4. `test_e_rejected_key_is_bound_live_and_forgotten_after_restore`. |

## Changed paths

| Path | Change |
|---|---|
| `reference/settlement_f01_f03/test_settlement_properties.py` | New. 5 test classes, 21 tests. |
| `reference/settlement_f01_f03/settlement_property_support.py` | New non-test support: seeds, contract literals, oracles, `Mirror`, `MockDriver`, `MachineDriver`. ASCII only, stdlib plus the two modules under test. |
| `validation/2026-10-16-settlement-seeded-property-suite/README.md` | This record. |
| `docs/README.md` | One index bullet. |
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | EV-SET fixture cell only: `test_settlement_properties` added to the brace list. Grade, sync-basis lines and the `fin-multi-payee-refund-proof` row untouched. The cell now post-dates the register's 2026-10-12 basis line. |

No workflow edit: the existing loop over `settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward` in `.github/workflows/protocol.yml` discovers the new file.

## Commands actually run

All from the repository root with `PYTHONDONTWRITEBYTECODE=1`. Results are in the final report of the session; the settlement suite ran 43 tests (22 existing + 21 new) in about 1 s on Python 3.13.5 and 3.12, under four `PYTHONHASHSEED` values.

Not run: Cargo steps of `ktx-kernel.yml` and `protocol.yml` (no Rust touched; the locked-blob check is the substitute), Sui, Node and ZK steps.

## Non-claims

Builder-authored, not an independent PASS. Not accounting, tax or legal treatment. No real payment, bank, PG or KYC call; no durable store; `MOCK_SETTLEMENT_ONLY` stays. It asserts no waterfall, remainder-unit payee, resale bps, tax or reserve rate, legal debtor or refund bearer (all UNDETERMINED, contract section 7). It does not implement or close `fin-multi-payee-refund-proof` (capability register row stays as is). Random coverage is a fixed corpus of 8 seeds, not exhaustive. A matched restore is equality of this process's journal and views, not bank exactly-once or chain finality.
