# settlement-multi-payee-refund-corpus

Node: `plan-settlement-multi-payee-refund-corpus`. Extends the seeded property suite of `plan-settlement-seeded-property-suite` (record `validation/2026-10-16-settlement-seeded-property-suite/README.md`) with a multi-payee refund corpus for `MockSettlement` and `SettlementMachine`: `reference/settlement_f01_f03/test_settlement_multi_payee_refund.py` plus driver and oracle additions in the existing non-test support module `reference/settlement_f01_f03/settlement_property_support.py`.
Issue: none. Depends on: `settlement-policy-deepening`. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792464145 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head SHA, no final task head SHA, and no KTX kernel verification or KIX protocol verification run ID for a head containing these files.

Observed `origin/main` = branch HEAD = `6f7559470bf2d555bbd80d0ae5d5f8a008e798f7` (local `origin/main` ref; the session ran no `git fetch`, so this records the worktree's stored ref, not a fresh remote check). Branch `agent/kix-plan-settlement-multi-payee-refund-corpus`.

**This corpus is builder-authored. It is not an independent PASS, not an accounting or legal treatment, and not a payment. No grade is raised. It narrows the `fin-multi-payee-refund-proof` register gap inside the MOCK bound and does not implement or close that pending node** (it also depends on `fin-ledger-contract` and `k-stage6-economics-reference`; its register row is untouched). Fixture numbers are synthetic KRW integers, not policy values.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. `mock_settlement.py`, `settlement_fsm.py`, the four existing test files, `docs/contracts/`, `reference/v0.3-rc1/`, `.aiops/`, `.github/`, `docs/tasks/` and `runtime/` are unchanged.

## What the corpus adds

Same harness conventions as the sibling suite: fixed `SEEDS = (1, 2, 3, 5, 8, 13, 21, 34)`, `random.Random(seed)` only, choices from sorted tuples, no wall clock, no `os.urandom`, no network, no file access. Verified identical under `PYTHONHASHSEED` 0, 1, 2 and unset.

- `check_refund_view` (new oracle, typed from contract section 5 and section 7.6/B0, not from the mock's control flow): bearer label is derived only from `refund_face` and the reclass flag (`NONE` / `UNDEFINED` / `FIXTURE_FULL_GROSS_RECLASS`), `distribution_blocked` iff face > 0 without reclass, per-payee `cancelled_unpaid = face - distributed` and `recovery_due = distributed` exactly at a reclass, `recovery_due == distributed_cash` then, `pg_adjustment_outstanding == refund_accepted`.
- `RefundCorpusDriver(MockDriver)`: three claims (`claim-one` tiny, `claim-two` mid, `claim-max` `MONEY_MAX`), each with its own payee label pair (`res-*`/`fee-*`), bps grid including 0 and 10000 (1-line claims) and interior values (2-line claims). `step()` is refund-weighted and adds three ops: `fill` (closes the open receivable in one movement, then often distributes), `partreclass` (confirms cash strictly below the face sum, distributes, binds the first full-gross refund), and `replay` (verbatim re-issue of one known statement/refund/acceptance binding). A top-up branch binds exactly `gross - refund_face` to reach the partial-sum-to-gross predicate. Bearer monotonicity per claim is asserted after every call (only `NONE` may move; `UNDEFINED` and the reclass are absorbing — section 5 makes a reclass impossible once `refund_face` > 0).
- `RefundMachineDriver(MachineDriver)`: `pick()` biased toward `bind_refund`/`observe_mock_cancel_acceptance` at `CAPTURED` and `COMMITTED`; replay branches prefer refund-family keys; every restore checkpoint additionally replays each accepted refund key on a restored machine (`restored-replay:*`).

Seeded coverage guard (`REQUIRED` tuples; counters observed across the 8 seeds): every refund-family code (`REFUND_CEILING` 86, `REFUND_BINDING_CONFLICT` 32, `REFUND_BENEFICIARY_CONFLICT` 4, `REFUND_OBLIGATION_REQUIRED` 11, `REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION` 24, `ACCEPTANCE_BINDING_CONFLICT` 11, `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED` 61, `DISTRIBUTION_ORDER_FROZEN` 5, `CURRENCY_UNSUPPORTED` 5), 1- and 2-line claims (`lines:1` 12, `lines:2` 12), reclass at each distribution level (`reclass@0` 6, `reclass@partial` 3, `reclass@full` 3), `partial-sum-to-gross` 7, mock-level replays (`replay:statement` 25, `replay:refund` 28, `replay:accept` 13), FSM level `ok:bind_refund@CAPTURED` 17 and `@COMMITTED` 18, `replay:bind_refund` 39, `replay:observe_mock_cancel_acceptance` 12, `restored-replay:bind_refund` 177 and `restored-replay:observe_mock_cancel_acceptance` 62, `reject:IDEMPOTENCY_CONFLICT` 71, `reject:TERMINAL_IMMUTABLE` 88, `reject:REFUND_CEILING` 23, `reject:REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION` 4.

| Property | Where |
|---|---|
| (f) per-payee `face = distributed + cancelled_unpaid + outstanding`, faces sum to gross, `distributed <= confirmed cash`, held through every seeded refund sequence including rejected and replayed commands | `WaterfallConservationCorpusTests`: 8 seeds x 120 calls over three claims with per-claim payee labels, `check_claim_view` + `check_refund_view` + bearer monotonicity after every call; directed two-statement/distribute/partial-refund/top-up/acceptance run per seed; distinct-label cash isolation over two claims |
| (g) refund reservation per payee at the first full-gross refund; partial sums never reclassify | `RefundReservationPerPayeeTests`: directed reclass at 0%, partial and full distribution (per-payee `cancelled_unpaid`/`recovery_due` asserted, `recovery_due == distributed_cash`), post-reclass `apply_distribution` applies 0 to every line, two partial refunds summing to gross keep `refund_bearer_policy == "UNDEFINED"` and stay blocked |
| (h) rejection atomicity | driver `call()` snapshots all claim views around every rejected call; directed `test_h_*` name each refund-family code at mock level and require `state_digest`/`export_journal` identical around each rejected FSM command |
| (i) replay of refund commands | `RefundReplayTests`: mock-level verbatim re-issue is `duplicate: true`, `applied: None` after later state changes; FSM replay returns the first result verbatim; same key + different body is `IDEMPOTENCY_CONFLICT`; a rejected key replays its error live and is forgotten by `restore`; `RefundMachineDriver` seeded runs |

## AGENTS.md section 7: existing coverage first

"Sufficiently" means every sentence of the property is held by a cited test whose body I read.

| Property | Class | Existing tests (exact names) | What this corpus adds |
|---|---|---|---|
| (f) split conservation | partially covered | `test_f02_caller_order_selects_shortfall_and_then_freezes`, `test_f02_later_cash_continues_on_the_frozen_order`, `test_claims_do_not_share_cash`, `test_b_c_seeded_sequences_conserve_and_rejections_change_nothing`, `test_b_claims_never_share_cash_even_with_the_same_payee_labels` (fixed cases or same-label shares) | per-claim distinct payee labels, refund-dense interleavings at `MONEY_MAX`, fill/partial-distribution staging that drives each distribution bucket, conservation checked against the independent mirror after every call including replays |
| (g) per-payee reservation | partially covered | `test_f03_full_refund_reclassifies_and_mock_acceptance_is_not_closure` (one fixed partial-distribution case), `test_f03_cash_after_reclass_is_not_applied_or_sent` (reclass then cash) | the same reservation asserted at all three distribution levels, per payee, seeded; `reclass@*` counters guard the corpus reaches each level; post-reclass zero-apply asserted as an `applied` map |
| partial sum to gross | partially covered | `test_f03_partial_refund_blocks_distribution_without_reclassifying` (40,000 + 60,000 on one claim) | a top-up branch reaches `refund_face == gross` across seeds after distributions; bearer stays `UNDEFINED`, blocked, no cancelled or recovery lines |
| (h) atomicity | FSM covered for fixed cases; refund-family density low | `test_illegal_transitions_do_not_move_the_phase`, `test_commit_fault_is_outside_the_journal_and_replay_stays_captured`, property (c) of the sibling suite | every refund-family rejection code named in directed tests at both levels, snapshots of every claim's canonical view plus digest/journal; the seeded corpus raises rejection density 6-7x for the refund family |
| (i) replay | partially covered | `test_same_key_replays_and_a_different_body_is_rejected`, `test_refund_block_survives_replay_and_is_not_a_clawback`, `test_e_rejected_key_is_bound_live_and_forgotten_after_restore`, `test_d_refund_binding`, `test_d_acceptance_binding` | verbatim re-issue of every binding kind after later state changes at mock level; FSM replay returns the first result byte-identical; a rejected `bind_refund` key replays `INVALID_AMOUNT` live, conflicts on a fixed body, and is free after `restore`; restored-machine replay of every refund key |

## Negative controls

`MultiPayeeControlTests` patches attributes in memory only (no source file touched), silences `MockSettlement._invariant` where the mock's guard would mask the oracle, and requires `AssertionError`, not `SettlementError`. Observed first failures:

| Control | First oracle failure |
|---|---|
| `bind_refund` inflates one payee's `recovery_due` by 1 at a reclass | `recovery_due <= distributed` fails inside `check_claim_view` (also the mirror compare) |
| `bind_refund` clears `fixture_reclassified` after the flag is set | mirror/view divergence on `fixture_reclassified` (also `cancelled_unpaid` lines) |
| a rejected `bind_refund` mutates `refund_face` before re-raising | `view changed after a rejected call` |
| `_replay_if_known` mutates the stored settlement view | `replay differs from the first result` / verbatim-replay assert |

Each control restores the patched attribute (`assertIs`).

## AGENTS.md section 8: discrepancy classes

No class C (explicit contract violation) was found. No blocker.

| # | Behaviour | Class | Handling |
|---|---|---|---|
| i | Precedence among simultaneously violated refund preconditions (e.g. an over-ceiling amount on a bound refund id, a wrong beneficiary on an over-ceiling bind). Section 6 lists codes, not precedence. | B | oracle checks set membership only, as in the sibling suite |
| ii | A `distribute` accepted after a reclass applies 0 to every line and still freezes `distribution_order` if it was not frozen. Sections 4 and 5 do not name this combination. | B | `test_g_post_reclass_distribution_applies_zero_to_every_line` asserts the zero `applied` map and conservation only; the freeze itself is not pinned |
| iii | A new-key FSM command repeating an already bound `refund_id`/`source_id` is journaled (`REFUND_BINDING_CONFLICT`/`ACCEPTANCE_BINDING_CONFLICT` arise inside the book, duplicate ids under the same binding stay inert); sections 1 and 9.3 define key replays and binding repeats separately. | B | same treatment as sibling item (i): inertness and atomicity asserted, the journaling combination is a characterization, not a contract reading |

## Changed paths

| Path | Change |
|---|---|
| `reference/settlement_f01_f03/test_settlement_multi_payee_refund.py` | New. 5 test classes, 19 tests (3 corpus/conservation, 5 reservation, 2 rejection atomicity, 5 replay, 4 controls). |
| `reference/settlement_f01_f03/settlement_property_support.py` | Extended: `check_refund_view` oracle, `BEARER_RANK`/`REFUND_OPS` constants, `RefundCorpusDriver`, `RefundMachineDriver`. No existing name changed; the section comment line before the machine constants was preserved. ASCII only, stdlib plus the two modules under test. |
| `validation/2026-10-21-settlement-multi-payee-refund-corpus/README.md` | This record. |
| `docs/README.md` | One index bullet in a new 2026-10-21 section. |
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | EV-SET fixture cell only: `test_settlement_multi_payee_refund` added to the brace list. Grade, sync-basis lines and the `fin-multi-payee-refund-proof` row untouched. |

No workflow edit: the existing loop over `settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward` in `.github/workflows/protocol.yml` discovers the new file.

## Commands actually run

All from the repository root with `PYTHONDONTWRITEBYTECODE=1` unless noted. Results are in the final report of the session; the settlement suite runs 67 tests (48 existing + 19 new) in about 1.5 s on Python 3.13.5 and 3.12.15, under `PYTHONHASHSEED` 0, 1, 2 and unset.

Not run: Cargo steps of `ktx-kernel.yml` and `protocol.yml` (no Rust touched; the locked-blob check is the substitute), Sui, Node and ZK steps — recorded as NOT_RUN, not passed.

## Non-claims

Builder-authored, not an independent PASS. Not accounting, tax or legal treatment. No real payment, bank, PG or KYC call; no durable store; `MOCK_SETTLEMENT_ONLY` stays. It asserts no waterfall numbers, no remainder-unit payee, no resale bps, no tax or reserve rate, no legal debtor, no partial-refund bearer and no external return closure (all UNDETERMINED, contract section 7). It does not implement or close `fin-multi-payee-refund-proof`; the register row is untouched. Random coverage is a fixed corpus of 8 seeds, not exhaustive. A matched restore is equality of this process's journal and views, not bank exactly-once or chain finality.
