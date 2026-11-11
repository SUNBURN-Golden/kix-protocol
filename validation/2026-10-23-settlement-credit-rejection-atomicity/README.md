# settlement-credit-rejection-atomicity

Node: `plan-plan-settlement-credit-rejection-atomici`. Adds `reference/settlement_f01_f03/test_settlement_rejection_atomicity.py` (113 tests) and `reference/credit_advance_f04/test_credit_rejection_atomicity.py` (94 tests). They apply the merged `test_reservation_rejection_atomicity.py` (#219) and `test_reward_rejection_atomicity.py` (#228) pattern to `SettlementMachine`/`MockSettlement` and `CreditMachine`/`MockCredit`. For every REPLAYABLE command each deterministic rejection code is driven against a machine and compared with an untouched control on `state_digest`, `canonical_state`, `export_journal`, the `restore(export_journal())` round trip (credit: with each side's own settlement source, and the injected settlement book's `canonical_state` where it has one) and the result of one later valid command on both sides. A test-owned fault-injection harness (`mock.patch.object` on `SettlementMachine._phase_book_invariant`, `MockSettlement._invariant`, `CreditMachine._invariant`, `MockCredit._invariant`, plus a drifting ownership witness stub) pins what a late failure leaves. Issue: none (loop-proposed node, not in `.aiops/program.json`; KIX planner run 1792670909). Depends on: `plan-bra-reservation-rejection-atomicity`, `plan-token-reward-rejection-atomicity`, `plan-settlement-seeded-property-suite`, `plan-credit-f04-seeded-property-suite`. Audit floor A2. Not an ASTRA program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head or final task head SHA and no exact-head CI run for this work; those belong in the pull request closure report (AGENTS.md §11).

The record directory is dated 2026-10-23 because the node names it so; the session ran on 2026-10-22. `docs/README.md` therefore carries a 2026-10-23 index section.

Observed `origin/main` = branch HEAD = `d84cc50f78a37420ca9d12752ac23f9f9b51c5fc` (merge of #258). One read-only `git fetch origin main` was run at session start (AGENTS.md §1) and returned that SHA; no other network action was taken.

**This record is a builder-authored reading, not an independent review. No grade is raised and nothing is claimed for production.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `git rev-parse HEAD:reference/v0.3-rc1` = `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` before and after.

## Changed paths

| Path | Change |
|---|---|
| `reference/settlement_f01_f03/test_settlement_rejection_atomicity.py` | New test module. Audit cases only; imports `SettlementMachine`, `MockSettlement`, `SettlementError` and the `codes`/`policy` helpers of `test_settlement_fsm.py`. |
| `reference/credit_advance_f04/test_credit_rejection_atomicity.py` | New test module. Audit cases only; imports `CreditMachine`, `MockCredit` and the `codes`/`settlement_book` helpers of `test_credit_fsm.py`. |
| `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md` | This record. |
| `docs/README.md` | New 2026-10-23 index section with one bullet. |
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | EV-SET and EV-CREDIT fixture cells cite the new modules and this record; one baseline sentence names the two rows. No grade change, no other row. |

No `mock_settlement.py`, `settlement_fsm.py`, `mock_credit.py`, `credit_fsm.py`, `open_terms.py`, contract, `CONTRACT_ERROR_CODE_COVERAGE.md`, plan, `.aiops`, `docs/tasks`, workflow, `runtime/` or `reference/v0.3-rc1` change. Findings are recorded, not fixed.

## How a row is checked

`check(code, pair, attempt, later)` builds a machine and a control through the same valid prefix, calls the rejected command on the machine only (twice: the second call replays the stored rejection, the only trace a rejection may leave, and it sits outside `canonical_state`), asserts the machine equals the control on digest, canonical state, journal and restore round trip, runs the same later valid command on both, asserts equal results, and compares again. The harness was sanity-checked against injected traces (a rejection path that appended a journal entry, and one that wrote a case field): both made the corresponding row fail, so the comparison is not vacuous. Those scratch injections ran as one-off stdin scripts and wrote no file.

Mutation boundaries (the point after which a deterministic rejection can no longer fire):

- Settlement `initiate`: `_cases[id]` insert, then `_phase_book_invariant`, then `_accept`. `authorize`/`fail`/`cancel`: flag or reason and phase write, then `_phase_book_invariant`, `_accept`. `capture`: `recognize_claim` (its own `_invariant` runs before the claim insert), phase write, `_phase_book_invariant`, `_accept`. `commit`: `observe_settlement_statement` (statement insert, then its `_invariant`), `commit_movement_id` and phase write, `_phase_book_invariant`, `_accept`. `observe_statement`, `distribute`, `bind_refund`, `observe_mock_cancel_acceptance`: one mock mutation each, then the mock `_invariant`, `_phase_book_invariant`, `_accept`.
- Credit `offer`: `_cases[id]` insert, `_invariant`, `_accept`; `offer` never touches `MockCredit`. `approve`/`reject`/`cancel`/`bind_settlement`/`default`: field and phase write, `_invariant`, `_accept`. `draw`: read-only source read, `note_advance` (claim freeze and note insert, then its `_invariant`), case write, `_invariant`, `_accept`. `repay`: note/order writes and counters, `_invariant`, `_accept`. `close`: `release_note` (status write, then its `_invariant`), phase write, `_invariant`, `_accept`.

Every deterministic rejection code listed below is raised before the first mutation of its command. After that point only the `MOCK_INVARIANT` checks remain, and no caller input reaches them, so they are covered by the fault rows (next sections), not by deterministic rows.

## Command enumeration: settlement (94 deterministic rows)

Column 2 names the first mutation the rejection precedes. Each row is one test in `test_settlement_rejection_atomicity.py`.

| Command | First mutation the rejection precedes | Rejection code | Test |
|---|---|---|---|
| `initiate` | `_cases[id]` insert | `INVALID_ID` | `test_initiate_invalid_settlement_id_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `INVALID_ID` | `test_initiate_invalid_trade_id_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `INVALID_ID` | `test_initiate_invalid_debtor_id_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `CURRENCY_UNSUPPORTED` | `test_initiate_currency_unsupported_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `INVALID_AMOUNT` | `test_initiate_invalid_amount_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `POLICY_TYPE` | `test_initiate_policy_type_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `POLICY_FIELDS` | `test_initiate_policy_fields_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `POLICY_KIND` | `test_initiate_policy_kind_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `POLICY_FEE_BPS` | `test_initiate_policy_fee_bps_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `POLICY_PAYEE` | `test_initiate_policy_payee_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `POLICY_PAYEE_COLLISION` | `test_initiate_policy_payee_collision_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `ILLEGAL_TRANSITION` | `test_initiate_illegal_transition_leaves_no_trace` |
| `initiate` | `_cases[id]` insert | `TERMINAL_IMMUTABLE` | `test_initiate_terminal_immutable_leaves_no_trace` |
| `authorize` | `mock_authorized` + phase write | `INVALID_ID` | `test_authorize_invalid_settlement_id_leaves_no_trace` |
| `authorize` | `mock_authorized` + phase write | `UNKNOWN_SETTLEMENT` | `test_authorize_unknown_settlement_leaves_no_trace` |
| `authorize` | `mock_authorized` + phase write | `TERMINAL_IMMUTABLE` | `test_authorize_terminal_immutable_leaves_no_trace` |
| `authorize` | `mock_authorized` + phase write | `ILLEGAL_TRANSITION` | `test_authorize_illegal_transition_leaves_no_trace` |
| `capture` | `recognize_claim` claim insert | `INVALID_ID` | `test_capture_invalid_settlement_id_leaves_no_trace` |
| `capture` | `recognize_claim` claim insert | `UNKNOWN_SETTLEMENT` | `test_capture_unknown_settlement_leaves_no_trace` |
| `capture` | `recognize_claim` claim insert | `TERMINAL_IMMUTABLE` | `test_capture_terminal_immutable_leaves_no_trace` |
| `capture` | `recognize_claim` claim insert | `ILLEGAL_TRANSITION` | `test_capture_illegal_transition_before_authorize_leaves_no_trace` |
| `capture` | `recognize_claim` claim insert | `ILLEGAL_TRANSITION` | `test_capture_illegal_transition_after_commit_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `INVALID_ID` | `test_commit_invalid_settlement_id_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `INVALID_ID` | `test_commit_invalid_movement_id_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `INVALID_AMOUNT` | `test_commit_invalid_amount_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `INVALID_NONNEGATIVE` | `test_commit_invalid_nonnegative_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `ADJUSTMENT_REASON_REQUIRED` | `test_commit_adjustment_reason_required_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `ADJUSTMENT_REASON_UNEXPECTED` | `test_commit_adjustment_reason_unexpected_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `SETTLEMENT_COMPONENT_MISMATCH` | `test_commit_component_mismatch_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `UNKNOWN_SETTLEMENT` | `test_commit_unknown_settlement_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `TERMINAL_IMMUTABLE` | `test_commit_terminal_immutable_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `ILLEGAL_TRANSITION` | `test_commit_illegal_transition_before_capture_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `ILLEGAL_TRANSITION` | `test_commit_illegal_transition_after_commit_leaves_no_trace` |
| `commit` | `observe_settlement_statement` insert | `SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE` | `test_commit_exceeds_open_receivable_leaves_no_trace` |
| `fail` | `failure_reason` + phase write | `INVALID_ID` | `test_fail_invalid_settlement_id_leaves_no_trace` |
| `fail` | `failure_reason` + phase write | `INVALID_ID` | `test_fail_invalid_reason_leaves_no_trace` |
| `fail` | `failure_reason` + phase write | `UNKNOWN_SETTLEMENT` | `test_fail_unknown_settlement_leaves_no_trace` |
| `fail` | `failure_reason` + phase write | `TERMINAL_IMMUTABLE` | `test_fail_terminal_immutable_leaves_no_trace` |
| `fail` | `failure_reason` + phase write | `ILLEGAL_TRANSITION` | `test_fail_illegal_transition_after_capture_leaves_no_trace` |
| `fail` | `failure_reason` + phase write | `ILLEGAL_TRANSITION` | `test_fail_illegal_transition_after_commit_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `INVALID_ID` | `test_cancel_invalid_settlement_id_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `INVALID_ID` | `test_cancel_invalid_reason_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `UNKNOWN_SETTLEMENT` | `test_cancel_unknown_settlement_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `TERMINAL_IMMUTABLE` | `test_cancel_terminal_immutable_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `ILLEGAL_TRANSITION` | `test_cancel_illegal_transition_after_capture_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `ILLEGAL_TRANSITION` | `test_cancel_illegal_transition_after_commit_leaves_no_trace` |
| `observe_statement` | mock statement insert | `INVALID_ID` | `test_observe_statement_invalid_settlement_id_leaves_no_trace` |
| `observe_statement` | mock statement insert | `INVALID_ID` | `test_observe_statement_invalid_movement_id_leaves_no_trace` |
| `observe_statement` | mock statement insert | `INVALID_AMOUNT` | `test_observe_statement_invalid_amount_leaves_no_trace` |
| `observe_statement` | mock statement insert | `INVALID_NONNEGATIVE` | `test_observe_statement_invalid_nonnegative_leaves_no_trace` |
| `observe_statement` | mock statement insert | `ADJUSTMENT_REASON_REQUIRED` | `test_observe_statement_adjustment_reason_required_leaves_no_trace` |
| `observe_statement` | mock statement insert | `ADJUSTMENT_REASON_UNEXPECTED` | `test_observe_statement_adjustment_reason_unexpected_leaves_no_trace` |
| `observe_statement` | mock statement insert | `SETTLEMENT_COMPONENT_MISMATCH` | `test_observe_statement_component_mismatch_leaves_no_trace` |
| `observe_statement` | mock statement insert | `UNKNOWN_SETTLEMENT` | `test_observe_statement_unknown_settlement_leaves_no_trace` |
| `observe_statement` | mock statement insert | `TERMINAL_IMMUTABLE` | `test_observe_statement_terminal_immutable_leaves_no_trace` |
| `observe_statement` | mock statement insert | `ILLEGAL_TRANSITION` | `test_observe_statement_illegal_transition_leaves_no_trace` |
| `observe_statement` | mock statement insert | `STATEMENT_BINDING_CONFLICT` | `test_observe_statement_binding_conflict_leaves_no_trace` |
| `observe_statement` | mock statement insert | `SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE` | `test_observe_statement_exceeds_open_receivable_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `DISTRIBUTION_ORDER_TYPE` | `test_distribute_order_type_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `INVALID_ID` | `test_distribute_invalid_settlement_id_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `INVALID_ID` | `test_distribute_invalid_payee_id_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `UNKNOWN_SETTLEMENT` | `test_distribute_unknown_settlement_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `TERMINAL_IMMUTABLE` | `test_distribute_terminal_immutable_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `ILLEGAL_TRANSITION` | `test_distribute_illegal_transition_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `DISTRIBUTION_ORDER_DUPLICATE` | `test_distribute_order_duplicate_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `DISTRIBUTION_ORDER_MISMATCH` | `test_distribute_order_mismatch_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `DISTRIBUTION_ORDER_FROZEN` | `test_distribute_order_frozen_leaves_no_trace` |
| `distribute` | mock `distribution_order` + line writes | `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED` | `test_distribute_blocked_refund_bearer_undefined_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `INVALID_ID` | `test_bind_refund_invalid_settlement_id_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `INVALID_ID` | `test_bind_refund_invalid_refund_id_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `INVALID_ID` | `test_bind_refund_invalid_beneficiary_id_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `INVALID_ID` | `test_bind_refund_invalid_reason_id_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `INVALID_AMOUNT` | `test_bind_refund_invalid_amount_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `UNKNOWN_SETTLEMENT` | `test_bind_refund_unknown_settlement_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `TERMINAL_IMMUTABLE` | `test_bind_refund_terminal_immutable_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `ILLEGAL_TRANSITION` | `test_bind_refund_illegal_transition_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `REFUND_BINDING_CONFLICT` | `test_bind_refund_binding_conflict_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `REFUND_CEILING` | `test_bind_refund_ceiling_leaves_no_trace` |
| `bind_refund` | mock refund insert (+ full-gross reclass) | `REFUND_BENEFICIARY_CONFLICT` | `test_bind_refund_beneficiary_conflict_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `INVALID_ID` | `test_acceptance_invalid_settlement_id_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `INVALID_ID` | `test_acceptance_invalid_source_id_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `INVALID_AMOUNT` | `test_acceptance_invalid_amount_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `UNKNOWN_SETTLEMENT` | `test_acceptance_unknown_settlement_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `TERMINAL_IMMUTABLE` | `test_acceptance_terminal_immutable_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `ILLEGAL_TRANSITION` | `test_acceptance_illegal_transition_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `ACCEPTANCE_BINDING_CONFLICT` | `test_acceptance_binding_conflict_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `REFUND_OBLIGATION_REQUIRED` | `test_acceptance_refund_obligation_required_leaves_no_trace` |
| `observe_mock_cancel_acceptance` | mock acceptance insert | `REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION` | `test_acceptance_exceeds_obligation_leaves_no_trace` |
| `reconcile` | none (receipt only, not journaled) | `UNKNOWN_SETTLEMENT` | `test_reconcile_unknown_settlement_leaves_no_trace` |
| `reconcile` | none (receipt only, not journaled) | `INVALID_ID` | `test_reconcile_invalid_settlement_id_leaves_no_trace` |
| `reject_external` | none (no `_call`) | `EXTERNAL_PAYMENT_UNSUPPORTED`, `INVALID_ID` | `test_reject_external_leaves_no_trace` |
| generic `_call` | none (`_call` key check) | `INVALID_ID` | `test_invalid_idempotency_key_leaves_no_trace` |
| generic `_call` | none (`_call` replay check) | `IDEMPOTENCY_CONFLICT` | `test_idempotency_conflict_leaves_no_trace` |
| generic `_call` | none (`_call`, nothing stored) | `INVALID_AMOUNT` | `test_unfingerprintable_rejection_leaves_no_trace` |

Not-applicable rows: `view`, `export_journal`, `canonical_state`, `state_digest` are read-only. `CLAIM_BINDING_CONFLICT` inside `capture` is unreachable (a claim exists only in CAPTURED/COMMITTED and `capture` runs once, from AUTHORIZED). The `duplicate is False` `MOCK_INVARIANT` checks in `capture` and `commit` have no caller input and are covered by the fault rows. `restore` is a classmethod and gets its own rows below.

Restore and idempotency rows (no deterministic code beyond `INVALID_JOURNAL`):

| Row | Test |
|---|---|
| `restore` rejects a non-list journal, non-dict entries, extra keys, an unknown op, a non-journaled op (`reconcile`), a non-string op, a non-dict body and an unexpected body key with `INVALID_JOURNAL` | `test_restore_invalid_journal_variants` |
| A stored rejection is not journaled; after `restore` the same key re-executes (class B) | `test_restore_forgets_stored_rejections` |

## Command enumeration: credit (78 deterministic rows)

Each row is one test in `test_credit_rejection_atomicity.py`.

| Command | First mutation the rejection precedes | Rejection code | Test |
|---|---|---|---|
| `offer` | `_cases[id]` insert | `CREDIT_PRODUCT_UNDEFINED` | `test_offer_product_undefined_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `INVALID_ID` | `test_offer_invalid_advance_id_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `INVALID_ID` | `test_offer_invalid_beneficiary_id_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `INVALID_AMOUNT` | `test_offer_invalid_amount_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `SETTLEMENT_FACE_TYPE` | `test_offer_face_type_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `SETTLEMENT_FACE_FIELDS` | `test_offer_face_fields_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `SETTLEMENT_FACE_NOT_MOCK` | `test_offer_face_not_mock_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `CURRENCY_UNSUPPORTED` | `test_offer_currency_unsupported_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `INVALID_ID` | `test_offer_invalid_face_id_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `SETTLEMENT_FACE_MISMATCH` | `test_offer_face_mismatch_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `REFUND_OBLIGATION_OPEN` | `test_offer_refund_obligation_open_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `ADVANCE_BINDING_CONFLICT` | `test_offer_advance_binding_conflict_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `ILLEGAL_TRANSITION` | `test_offer_illegal_transition_leaves_no_trace` |
| `offer` | `_cases[id]` insert | `ILLEGAL_TRANSITION` | `test_offer_terminal_reoffer_is_illegal_transition_leaves_no_trace` |
| `approve` | phase write | `INVALID_ID` | `test_approve_invalid_advance_id_leaves_no_trace` |
| `approve` | phase write | `UNKNOWN_ADVANCE` | `test_approve_unknown_advance_leaves_no_trace` |
| `approve` | phase write | `ILLEGAL_TRANSITION` | `test_approve_illegal_transition_leaves_no_trace` |
| `approve` | phase write | `TERMINAL_IMMUTABLE` | `test_approve_terminal_immutable_leaves_no_trace` |
| `reject` | `reject_reason` + phase write | `INVALID_ID` | `test_reject_invalid_advance_id_leaves_no_trace` |
| `reject` | `reject_reason` + phase write | `INVALID_ID` | `test_reject_invalid_reason_leaves_no_trace` |
| `reject` | `reject_reason` + phase write | `UNKNOWN_ADVANCE` | `test_reject_unknown_advance_leaves_no_trace` |
| `reject` | `reject_reason` + phase write | `ILLEGAL_TRANSITION` | `test_reject_illegal_transition_leaves_no_trace` |
| `reject` | `reject_reason` + phase write | `TERMINAL_IMMUTABLE` | `test_reject_terminal_immutable_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `INVALID_ID` | `test_cancel_invalid_advance_id_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `INVALID_ID` | `test_cancel_invalid_reason_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `UNKNOWN_ADVANCE` | `test_cancel_unknown_advance_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `ILLEGAL_TRANSITION` | `test_cancel_illegal_transition_leaves_no_trace` |
| `cancel` | `cancel_reason` + phase write | `TERMINAL_IMMUTABLE` | `test_cancel_terminal_immutable_leaves_no_trace` |
| `bind_settlement` | `settlement_id` write | `INVALID_ID` | `test_bind_settlement_invalid_advance_id_leaves_no_trace` |
| `bind_settlement` | `settlement_id` write | `INVALID_ID` | `test_bind_settlement_invalid_settlement_id_leaves_no_trace` |
| `bind_settlement` | `settlement_id` write | `UNKNOWN_ADVANCE` | `test_bind_settlement_unknown_advance_leaves_no_trace` |
| `bind_settlement` | `settlement_id` write | `TERMINAL_IMMUTABLE` | `test_bind_settlement_terminal_immutable_leaves_no_trace` |
| `bind_settlement` | `settlement_id` write | `ILLEGAL_TRANSITION` | `test_bind_settlement_illegal_transition_after_draw_leaves_no_trace` |
| `bind_settlement` | `settlement_id` write | `ILLEGAL_TRANSITION` | `test_bind_settlement_rebind_leaves_no_trace` |
| `bind_settlement` | `settlement_id` write | `SETTLEMENT_BINDING_CONFLICT` | `test_bind_settlement_binding_conflict_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `INVALID_ID` | `test_draw_invalid_advance_id_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `UNKNOWN_ADVANCE` | `test_draw_unknown_advance_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `INVALID_ID` | `test_draw_invalid_draw_id_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `DUPLICATE_DRAW` | `test_draw_duplicate_draw_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `TERMINAL_IMMUTABLE` | `test_draw_terminal_immutable_after_draw_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `TERMINAL_IMMUTABLE` | `test_draw_terminal_immutable_without_draw_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `ILLEGAL_TRANSITION` | `test_draw_illegal_transition_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `SETTLEMENT_SOURCE_REQUIRED` | `test_draw_settlement_source_required_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `UNKNOWN_SETTLEMENT` | `test_draw_unknown_settlement_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `SETTLEMENT_NOT_COMMITTED` | `test_draw_settlement_not_committed_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `SETTLEMENT_BINDING_CONFLICT` | `test_draw_settlement_binding_conflict_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `SETTLEMENT_AMOUNT_MISMATCH` | `test_draw_settlement_amount_mismatch_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `SETTLEMENT_VIEW_REJECTED` | `test_draw_settlement_view_rejected_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `FACE_SNAPSHOT_FROZEN` | `test_draw_face_snapshot_frozen_leaves_no_trace` |
| `draw` | source read, then `note_advance` note insert | `ADVANCE_EXCEEDS_OPEN_FACE` | `test_draw_advance_exceeds_open_face_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `INVALID_ID` | `test_repay_invalid_advance_id_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `UNKNOWN_ADVANCE` | `test_repay_unknown_advance_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `INVALID_ID` | `test_repay_invalid_repay_id_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `INVALID_AMOUNT` | `test_repay_invalid_amount_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `REPAYMENT_ORDER` | `test_repay_sequence_type_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `REPAYMENT_ORDER` | `test_repay_sequence_gap_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `REPAY_BINDING_CONFLICT` | `test_repay_binding_conflict_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `TERMINAL_IMMUTABLE` | `test_repay_terminal_immutable_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `ILLEGAL_TRANSITION` | `test_repay_illegal_transition_leaves_no_trace` |
| `repay` | `repay_notes`/`repay_order` writes | `REPAYMENT_EXCEEDS_OUTSTANDING` | `test_repay_exceeds_outstanding_leaves_no_trace` |
| `close` | `release_note` status write | `INVALID_ID` | `test_close_invalid_advance_id_leaves_no_trace` |
| `close` | `release_note` status write | `UNKNOWN_ADVANCE` | `test_close_unknown_advance_leaves_no_trace` |
| `close` | `release_note` status write | `ILLEGAL_TRANSITION` | `test_close_illegal_transition_leaves_no_trace` |
| `close` | `release_note` status write | `TERMINAL_IMMUTABLE` | `test_close_terminal_immutable_leaves_no_trace` |
| `close` | `release_note` status write | `OUTSTANDING_REMAINS` | `test_close_outstanding_remains_leaves_no_trace` |
| `default` | `default_reason` + phase write | `INVALID_ID` | `test_default_invalid_advance_id_leaves_no_trace` |
| `default` | `default_reason` + phase write | `INVALID_ID` | `test_default_invalid_reason_leaves_no_trace` |
| `default` | `default_reason` + phase write | `UNKNOWN_ADVANCE` | `test_default_unknown_advance_leaves_no_trace` |
| `default` | `default_reason` + phase write | `ILLEGAL_TRANSITION` | `test_default_illegal_transition_leaves_no_trace` |
| `default` | `default_reason` + phase write | `TERMINAL_IMMUTABLE` | `test_default_terminal_immutable_leaves_no_trace` |
| `default` | `default_reason` + phase write | `DEFAULT_REQUIRES_EXPOSURE` | `test_default_requires_exposure_leaves_no_trace` |
| `reconcile` | none (receipt only, not journaled) | `UNKNOWN_ADVANCE` | `test_reconcile_unknown_advance_leaves_no_trace` |
| `reconcile` | none (receipt only, not journaled) | `INVALID_ID` | `test_reconcile_invalid_advance_id_leaves_no_trace` |
| `reject_unsupported` | none (self-guarded) | `REAL_FUNDS_FORBIDDEN`, `CREDIT_PRODUCT_UNDEFINED`, `EXECUTION_KIND` | `test_reject_unsupported_leaves_no_trace` |
| `attempt_execution` | none (self-guarded) | `REAL_FUNDS_FORBIDDEN`, `CREDIT_PRODUCT_UNDEFINED`, `EXECUTION_KIND`, `UNKNOWN_ADVANCE`, `INVALID_ID` | `test_attempt_execution_leaves_no_trace` |
| generic `_call` | none (`_call` key check) | `INVALID_ID` | `test_invalid_idempotency_key_leaves_no_trace` |
| generic `_call` | none (`_call` replay check) | `IDEMPOTENCY_CONFLICT` | `test_idempotency_conflict_leaves_no_trace` |
| generic `_call` | none (`_call`, nothing stored) | `INVALID_AMOUNT` | `test_unfingerprintable_rejection_leaves_no_trace` |

Not-applicable rows: `view`, `view_claim`, `export_journal`, `canonical_state`, `state_digest` are read-only. In `draw`, the `note_advance` codes `REFUND_OBLIGATION_OPEN`, `ADVANCE_BINDING_CONFLICT` and the face-parse codes are unreachable (`offer` parsed the same face and a note is inserted once); the post-`note_advance` flag checks and the `release_note` flag checks have no caller input. Mock-only codes on the same paths (`FACE_SNAPSHOT_FROZEN`, `ADVANCE_EXCEEDS_OPEN_FACE`) are reached through two advances on one claim.

Restore and idempotency rows:

| Row | Test |
|---|---|
| `restore` rejects a non-list journal, non-dict entries, extra keys, an unknown op, a non-journaled op, a non-string op, a non-dict body and an unexpected body key with `INVALID_JOURNAL` | `test_restore_invalid_journal_variants` |
| A stored rejection is not journaled; after `restore` the same key re-executes (class B) | `test_restore_forgets_stored_rejections` |

## Fault rows (late-failure seams, class B characterizations)

None of the four hooks has a rollback wrapper. These tests inject a `MOCK_INVARIANT` at one hook with `mock.patch.object(..., side_effect=[error])` (exactly one hook call per `with` block) and pin what is left. They show what the code does when the hook fails, not that a caller can make it fail.

Settlement, `SettlementMachine._phase_book_invariant` (10 rows, one per REPLAYABLE command): the mutation stays applied and unjournaled — journal equal to the control, `canonical_state`/`state_digest` divergent, `restore(export_journal())` equal to the control and unequal to the machine, `reconcile` returns `MOCK_INVARIANT`.

| Command | Test | What a retry meets |
|---|---|---|
| `initiate` | `test_fault_initiate_late_rejection_leaves_unapplied_mutation` | `ILLEGAL_TRANSITION` (INITIATED case exists, never journaled) |
| `authorize` | `test_fault_authorize_late_rejection_leaves_unapplied_mutation` | `ILLEGAL_TRANSITION` |
| `capture` | `test_fault_capture_late_rejection_leaves_unapplied_mutation` | `ILLEGAL_TRANSITION` (claim recognized, case CAPTURED) |
| `commit` | `test_fault_commit_late_rejection_leaves_unapplied_mutation` | `ILLEGAL_TRANSITION` (statement posted, `confirmed_cash` 97000) |
| `fail` | `test_fault_fail_late_rejection_leaves_unapplied_mutation` | `TERMINAL_IMMUTABLE` |
| `cancel` | `test_fault_cancel_late_rejection_leaves_unapplied_mutation` | `TERMINAL_IMMUTABLE` |
| `observe_statement` | `test_fault_observe_statement_late_rejection_leaves_unapplied_mutation` | `SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE` for a different statement (`receivable_open` already 0) |
| `distribute` | `test_fault_distribute_late_rejection_leaves_unapplied_mutation` | `DISTRIBUTION_ORDER_FROZEN` for the other order (97000 already distributed) |
| `bind_refund` | `test_fault_bind_refund_late_rejection_leaves_unapplied_mutation` | `REFUND_BINDING_CONFLICT` for a different amount (`refund_face` already 30000) |
| `observe_mock_cancel_acceptance` | `test_fault_acceptance_late_rejection_leaves_unapplied_mutation` | `ACCEPTANCE_BINDING_CONFLICT` for a different amount |
| (all) | `test_fault_covers_every_replayable_command` | guard: the ten rows above equal `REPLAYABLE` |

Settlement, `MockSettlement._invariant` (6 rows):

| Command | Test | Observed |
|---|---|---|
| `capture` | `test_mock_fault_capture_rolls_back` | no trace: `recognize_claim` runs `_invariant` before its claim insert, and the case phase is written after; control comparison, restore and the later `capture` all match (the only fault row that is a `_rolls_back` shape) |
| `commit` | `test_mock_fault_commit_leaves_unapplied_mutation` | statement posted in the mock, case stays CAPTURED, journal equal to control. The same commit retried meets the recorded statement as a duplicate, which the commit path treats as `MOCK_INVARIANT`; a different `movement_id` gets `SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE`. The case cannot commit again; by the phase table `fail`/`cancel` are not allowed from CAPTURED |
| `observe_statement` | `test_mock_fault_observe_statement_leaves_unapplied_mutation` | statement posted, unjournaled; the same retry is accepted as a duplicate and journaled, after which machine and control converge |
| `distribute` | `test_mock_fault_distribute_leaves_unapplied_mutation` | cash and `distribution_order` moved, unjournaled; the retry is journaled but reports `{"organizer": 0, "platform": 0}` while the control's first call reports `{"organizer": 95000, "platform": 2000}`; states converge, the effect the caller sees differs |
| `bind_refund` | `test_mock_fault_bind_refund_leaves_unapplied_mutation` | refund recorded, unjournaled; retry accepted as duplicate and journaled; converge |
| `observe_mock_cancel_acceptance` | `test_mock_fault_acceptance_leaves_unapplied_mutation` | acceptance recorded, unjournaled; retry accepted as duplicate and journaled; converge |

Credit, `CreditMachine._invariant` (9 rows, one per REPLAYABLE command): same unapplied-mutation shape as above (journal equal to control, `canonical_state` divergent, restore equals control, `reconcile` returns `MOCK_INVARIANT`).

| Command | Test | What a retry meets |
|---|---|---|
| `offer` | `test_fault_offer_late_rejection_leaves_unapplied_mutation` | `ILLEGAL_TRANSITION`; the control has no such advance (`UNKNOWN_ADVANCE`) |
| `approve` | `test_fault_approve_late_rejection_leaves_unapplied_mutation` | `ILLEGAL_TRANSITION` |
| `reject` | `test_fault_reject_late_rejection_leaves_unapplied_mutation` | `TERMINAL_IMMUTABLE` |
| `cancel` | `test_fault_cancel_late_rejection_leaves_unapplied_mutation` | `TERMINAL_IMMUTABLE` |
| `bind_settlement` | `test_fault_bind_settlement_late_rejection_leaves_unapplied_mutation` | `ILLEGAL_TRANSITION`; gate BOUND vs control UNBOUND |
| `draw` | `test_fault_draw_late_rejection_leaves_unapplied_mutation` | the same `draw_id` returns `duplicate: true` and journals nothing, so the draw never enters the journal; the note is NOTED and the case DRAWN only in the live machine |
| `repay` | `test_fault_repay_late_rejection_leaves_unapplied_mutation` | the same `repay_id` returns `duplicate: true`, no journal entry; a new `repay_id` at sequence 1 gets `REPAYMENT_ORDER` |
| `close` | `test_fault_close_late_rejection_leaves_unapplied_mutation` | `TERMINAL_IMMUTABLE`; note RELEASED vs control NOTED |
| `default` | `test_fault_default_late_rejection_leaves_unapplied_mutation` | `TERMINAL_IMMUTABLE` |
| (all) | `test_fault_covers_every_replayable_command` | guard: the nine rows above equal `REPLAYABLE` |

Credit, `MockCredit._invariant` and `_guard` (4 rows):

| Seam | Test | Observed |
|---|---|---|
| `draw` → `note_advance` | `test_mock_fault_draw_leaves_unapplied_note` | note inserted (NOTED) while the case stays APPROVED, journal equal to control. The same draw now meets the note as a duplicate, which draw treats as `MOCK_INVARIANT`. The machine's own `_invariant` then expects no note for a non-drawn case, so a following `cancel` returns `MOCK_INVARIANT` and itself leaves an unjournaled CANCELLED case |
| `close` → `release_note` | `test_mock_fault_close_leaves_unapplied_release` | note RELEASED while the case stays DRAWN; the same close then meets the release as a duplicate and returns `MOCK_INVARIANT` |
| `_guard` after `_accept` | `test_guard_drift_after_accept_reports_rejection_for_a_journaled_command` | with a drifting ownership witness the `offer` is applied and journaled (equal to a control that accepted it) although the caller sees `MOCK_INVARIANT` |
| `_guard` on a rejection | `test_guard_drift_replaces_a_deterministic_rejection_code` | the guard's `MOCK_INVARIANT` replaces the deterministic code; state equals the control |

## AGENTS.md §7: existing coverage

| Requirement | Existing | Status |
|---|---|---|
| Deterministic rejection codes raised | `test_settlement_fsm.py`, `test_mock_settlement.py`, `test_contract_error_codes.py` (settlement); `test_credit_fsm.py`, `test_mock_credit.py` (credit) assert most codes | partially covered: same-machine canonical/journal comparison only; no control, no restore round trip, no later-command check |
| Rejected command leaves canonical state and journal equal to an untouched control | none | not covered → every `*_leaves_no_trace` row |
| `restore(export_journal())` cannot reproduce a post-rejection machine | success-path checks only: `test_settlement_fsm.py::test_reconcile_matches_restore_and_does_not_enter_the_economic_journal`, `test_credit_fsm.py::test_reconcile_replays_the_journal_without_a_second_draw`, and the seeded property suites | partially covered: restore compared on both sides of every row here |
| Late failure after mutation but before journal append | none (no existing test patches a hook; `grep` for `patch`/`MOCK_INVARIANT` in the five existing test files finds no match) | not covered → `test_fault_*`, `test_mock_fault_*`, `test_guard_*` characterizations |

## Class A / B / C

- Class A (contract-defined, matched): none for the atomicity property itself. `SETTLEMENT_DISTRIBUTION_F01_F03.md` and `CREDIT_ADVANCE_F04.md` define the error codes, and the contract-code coverage checker already cites asserting sites for them; neither states a rejection-atomicity clause for these machines. `BOOKING_RESALE_ADMISSION_GATES.md` §9.4 covers the reservation machine only. Every deterministic row still passed: all 94 settlement and 78 credit rows leave `state_digest`, `canonical_state`, `export_journal` and the restore round trip identical to the control, and the one later valid command returns equal results on both sides.
- Class B (contract does not define; observed characterizations):
  - Umbrella: rejection atomicity for both machines is contract-undefined but implemented for every caller-reachable code; a stored rejection under the caller's key is the only allowed trace.
  - `test_fault_*` (19 rows) and the `MockSettlement`/`MockCredit` rows that leave a mutation: neither machine has a rollback wrapper, so a `MOCK_INVARIANT` after a mutation leaves it applied and unjournaled. `restore(export_journal())` then reproduces the control, not the live machine. `reconcile` is the one command that notices (returns `MOCK_INVARIANT`).
  - Credit `draw` after either fault: a machine-level fault leaves a DRAWN case with no journal entry, and a retry with the same `draw_id` returns `duplicate: true` without ever journaling; a mock-level fault leaves a NOTED note under an APPROVED case that the machine's `_invariant` rejects from then on (observed: the same draw and `cancel`), and `cancel` leaves a further unjournaled write.
  - Settlement `commit` after a mock-level fault: the case stays CAPTURED with the statement already posted; the same commit retried returns `MOCK_INVARIANT` and a different `movement_id` returns `SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE`, so it cannot reach COMMITTED.
  - Settlement `distribute` after a mock-level fault: the journaled retry reports zero applied amounts.
  - `test_mock_fault_capture_rolls_back`: the one fault seam that leaves nothing (the mock checks its invariant before inserting the claim).
  - `test_guard_drift_*` (2 rows): the credit `_guard` runs after `_accept` and in a `finally`, so a changed ownership witness yields `MOCK_INVARIANT` for a command that was already journaled, and replaces a deterministic rejection code. The witness here is a test stub; no claim is made that a real ownership source can drift.
  - `test_offer_terminal_reoffer_is_illegal_transition_leaves_no_trace`: re-offering the same binding after a terminal phase returns `ILLEGAL_TRANSITION`, not `TERMINAL_IMMUTABLE`, because `offer` has no terminal branch.
  - `test_restore_forgets_stored_rejections` (both modules): `_idempotency` is outside `canonical_state` and stored rejections are not journaled; after `restore` the same key under different canonical arguments re-executes to acceptance instead of `IDEMPOTENCY_CONFLICT`.
- Class C: none found. No deterministic rejection diverged from its control, and no written contract clause was found that the observed behavior violates; the merge path is not stopped.

## Commands run and results

| Command | Result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD` | both `d84cc50f78a37420ca9d12752ac23f9f9b51c5fc` |
| `git hash-object` on the two locked files (before and after) | match the required blobs |
| `git rev-parse HEAD:reference/v0.3-rc1` (before and after) | `a6ecb124…` both times |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_settlement_rejection_atomicity` (in `reference/settlement_f01_f03`) | 113 tests OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_credit_rejection_atomicity` (in `reference/credit_advance_f04`) | 94 tests OK |
| `python3 -m unittest discover -s reference/<suite> -t reference/<suite>` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward` | 180 / 162 / 142 / 70 / 156 tests OK (settlement 180 = 67 existing + 113 new; credit 142 = 48 existing + 94 new; no existing test file edited) |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 82 tests OK |
| `check_contract_error_codes.py`, plain and `--self-test` | exit 0 / 0 |
| `check_status_register.py`, `check_docs_index.py`, plain and `--self-test` | exit 0 for all 4 runs (failed before this record existed: the register and index pointed at the missing path) |
| `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`, `check_tl_predicate_evidence_map.py`, `check_adapter_identity_map.py`, `check_v5_transition_evidence_map.py`, `check_readiness_evidence_map.py`, each plain and `--self-test` | exit 0 for all 20 runs |
| `check_openapi_contract.py`; `check_integration_gate_openapi.py` | exit 0 / 0 |
| `check_sdk_client.py`, `check_stage5_host.py` | NOT_RUN: no `sdk` or stage-5 path changed; SDK check needs node 24 hosted |
| cargo, clippy, fmt | NOT_RUN: nothing under `runtime/` changed; they run hosted |
| exact-head KTX and KIX CI | NOT_RUN locally: belongs to the PR head per §10 |

Local python is 3.13.5; the workflow pins 3.12. The new modules use no 3.13-only constructs.

## Non-claims

No real payment, PG, bank, KYC, chain, or public-endpoint call; `MOCK_SETTLEMENT_ONLY` and `MOCK_CREDIT_F04_ONLY` provenance and the false execution flags are untouched. The `_phase_book_invariant`/`_invariant` faults and the drifting witness are `unittest.mock` injections and a stub inside test code; they do not claim that a real `MOCK_INVARIANT` can be reached by caller input. `canonical_state`/`state_digest` equality is an in-process comparison, not durability, bank exactly-once or chain finality. The class B rows are recorded characterizations, not proposed contract text; no contract semantics were invented and no non-test source was edited.

## Remaining uncertainty / follow-up candidates

- Whether the unapplied-mutation seams should gain a rollback wrapper (the `test_adopt_issued_atomicity.py` precedent added one to the reservation path) is a contract/design question outside this node: it would be a non-test source change needing its own authorization. The credit mock-level `draw` seam is the most consequential observed shape (the machine fails its own invariant afterwards); the settlement `commit` seam is the other one that leaves a case unable to progress.
- The audit covers one fault per command at each of the hooks, one command per `with` block. Combinations of faults, a fault inside `reconcile`/`restore`, and the settlement `MockSettlement._invariant` hook inside `initiate`/`authorize`/`fail`/`cancel` (which never reach it) were not exercised.
- Deterministic rows pick one representative prefix per code; rows such as `ILLEGAL_TRANSITION` from further phases beyond those named in the table were not enumerated.
- The register carries a baseline sentence for the two rows it touches; the TL/RS evidence maps, `CONTRACT_ERROR_CODE_COVERAGE.md` and `DEVELOPMENT_PLAN.md` were not changed and do not name the new files.
