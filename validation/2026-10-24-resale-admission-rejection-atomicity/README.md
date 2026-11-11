# Resale and admission rejection-atomicity audit — 2026-10-24

Task: `plan-plan-resale-admission-rejection-atomicit`. Builder-authored,
source-informed, deterministic offline MOCK_GATE_ONLY evidence. No grade change.
The task input is the supervisor's node envelope and read-only design in the
session; no corresponding `docs/tasks/` node document or issue exists. Historical
Task 005 is context, not a new implementation authorization.

Local implementation is awaiting supervisor publication, exact-head CI and
non-author review. This record does not propose merge.

## Base, boundaries and protected content

- Branch: `agent/kix-plan-plan-resale-admission-rejection-atomicit`.
- Locally observed `origin/main`, initial implementation HEAD and final uncommitted
  task HEAD: `99f30c2d641646d653b62383b213452fd0a0498b` (no local delta).
  Fresh remote main is unverified: the supervisor explicitly prohibited network
  actions, so `git fetch origin main` was NOT_RUN, overriding AGENTS.md §1.
- No commit, push, PR, issue, comment, merge or GitHub operation performed.
  Final delivery commit and merge SHA: N/A, supervisor-owned.
- Locked blobs before and after: `runtime/crates/kix-kernel/src/lib.rs` =
  `69564b166f0c27f9af5d8422f0a466b18d74c20f`;
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
  `b607996c83a119c349f1cc90469ac1ba82764e20`.
- `HEAD:reference/v0.3-rc1` tree before/after =
  `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; working-tree diff empty.
  Final merge lock verification: N/A (not merged).
- Complete changed paths: `reference/booking_resale_admission/test_resale_rejection_atomicity.py`,
  `reference/booking_resale_admission/test_admission_rejection_atomicity.py`,
  this validation record, and one link in `docs/README.md`.
  FSMs, mocks, contracts, error-code coverage document, capability register,
  `.aiops/`, `docs/tasks/`, CI and frozen reference remain unchanged.

## Coverage mapping made before adding tests

| Requirement / existing evidence | Initial coverage | Action |
|---|---|---|
| `test_resale_fsm.py::ResaleFsmTests` code assertions and selected journal/digest checks | partially covered | Add per-command/code control, source, views, restore and later-command comparisons below |
| `test_admission_fsm.py::AdmissionFsmTests` freshness, lifecycle and fail-closed assertions | partially covered | Same comparison gap |
| `test_gate_properties.py::SeededSequenceTests.test_resale_seeded_sequences` and `test_admission_seeded_sequences`, property (e) | partially covered | Seeded, unbound self-state checks do not cover bound sources and independent later-command equality |
| `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` BRA-RES / BRA-ADM rows | partially covered | Static raise/assert citations prove code presence, not atomicity; table below adds behavioral evidence |
| `test_adopt_issued_atomicity.py::ResaleAtomicityTests` and `AdmissionAtomicityTests`, `test_order_binding_conflict_leaves_no_trace`, `test_payment_binding_conflict_leaves_no_trace`, `test_rejection_after_show_registration_leaves_no_trace` | sufficiently covered for unbound adoption | Cite; no duplicate unbound ORDER_BINDING_CONFLICT / PAYMENT_BINDING_CONFLICT / SLOT tests |
| Same classes, `test_invariant_failure_after_materialize_rolls_back` | sufficiently covered for adopt MOCK_INVARIANT | Cite; exclude adopt from new fault rows |
| Bound command rejection control/source comparisons and the clock-skew window probe | not covered by those existing comparisons | New evidence below |

The existing raise/assert sites per code remain inspectable in the unchanged
[coverage table](../../docs/status/CONTRACT_ERROR_CODE_COVERAGE.md). Mock §6 codes
reachable through these two machines are included below. Reservation-only and
direct-MockGates-only commands are outside this node.

## Comparison method

Each ordinary row builds two independent environments through the same valid
prefix. It snapshots the rejecting machine before the call and compares after
both the initial rejection and its identical-key replay: `canonical_state`,
`state_digest`, journal export, all present listing/right/credential views, and
old/current presentation views. The snapshots also include each bound source's
canonical state and journal where available. No snapshot includes the private
idempotency map: stored rejection receipts are allowed by §10.7/§11.5.

Both sides then restore using their own live sources. The helper asserts those
sources did not change even on failed restore. Restore normally reproduces the
machine canonical state and digest. Explicit expected failures are used when
sources no longer satisfy the original commands: resale `ADMISSION_LOCKED` /
`ALREADY_CONSUMED` (§10.3/§10.7), admission `STALE_VERSION` (§11.4 last row/§11.5).
The later valid command is a fresh clock advance on both sides, with full
snapshot and restore comparisons again. This tests continued clock/expiration,
invariants and admission delegation; it does not prove every later lifecycle
continuation. All clocks use existing fixture values and distinct reservation,
ownership and admission idempotency keys.

Rows are data-driven but registered as individually named unittest methods.
Only functions (never TestCase classes) are imported from the existing FSM tests.
No existing test is rediscovered via class imports.

## Per-code / command evidence

All ordinary new rows below are A: contract-defined rejection behavior matching
§10.2–§10.8 / §11.2–§11.6 and the inherited §6 validators. Each row's test name
is the actual separately registered method. `new` means the existing coverage
was partial, or this particular predicate/source combination lacked evidence.

Existing-sufficient rows apply independently to both machines:

| Command | Code | Status | Class | Existing test in `test_adopt_issued_atomicity.py` |
|---|---|---|---|---|
| adopt_issued (unbound) | ORDER_BINDING_CONFLICT | existing-sufficient | A | `test_order_binding_conflict_leaves_no_trace` |
| adopt_issued (unbound) | PAYMENT_BINDING_CONFLICT | existing-sufficient | A | `test_payment_binding_conflict_leaves_no_trace` |
| adopt_issued (unbound) | SLOT | existing-sufficient | A | `test_rejection_after_show_registration_leaves_no_trace` |
| adopt_issued (unbound fault) | MOCK_INVARIANT | existing-sufficient | B, injected internal failure | `test_invariant_failure_after_materialize_rolls_back` |

### Resale

Methods in [test_resale_rejection_atomicity.py](../../reference/booking_resale_admission/test_resale_rejection_atomicity.py)::ResaleRejectionAtomicityTests.

| Command | Code | Status | Class | Test | Expected restore error |
|---|---|---|---|---|---|
| accept_resale | ADMISSION_LOCKED | new | A | `test_accept_resale_admission_locked_leaves_no_trace` | ADMISSION_LOCKED |
| accept_resale | ALREADY_CONSUMED | new | A | `test_accept_resale_already_consumed_leaves_no_trace` | ALREADY_CONSUMED |
| accept_resale | ILLEGAL_TRANSITION | new | A | `test_accept_resale_illegal_transition_leaves_no_trace` | none |
| accept_resale | INVALID_ID | new | A | `test_accept_resale_invalid_id_leaves_no_trace` | none |
| accept_resale | LISTING_NOT_OPEN | new | A | `test_accept_resale_listing_not_open_leaves_no_trace` | none |
| accept_resale | SETTLEMENT_AMOUNT_MISMATCH | new | A | `test_accept_resale_settlement_amount_mismatch_leaves_no_trace` | none |
| accept_resale | SETTLEMENT_NOT_COMMITTED | new | A | `test_accept_resale_settlement_not_committed_leaves_no_trace` | none |
| accept_resale | SETTLEMENT_SOURCE_REQUIRED | new | A | `test_accept_resale_settlement_source_required_leaves_no_trace` | none |
| accept_resale | SETTLEMENT_VIEW_REJECTED | new | A | `test_accept_resale_settlement_view_rejected_leaves_no_trace` | none |
| accept_resale | TERMINAL_IMMUTABLE | new | A | `test_accept_resale_terminal_immutable_leaves_no_trace` | none |
| accept_resale | TRANSFER_BINDING_CONFLICT | new | A | `test_accept_resale_transfer_binding_conflict_leaves_no_trace` | none |
| accept_resale | UNKNOWN_LISTING | new | A | `test_accept_resale_unknown_listing_leaves_no_trace` | none |
| accept_resale | UNKNOWN_SETTLEMENT | new | A | `test_accept_resale_unknown_settlement_leaves_no_trace` | none |
| adopt_issued | ADMISSION_LOCKED | new | A | `test_adopt_issued_admission_locked_leaves_no_trace` | none |
| adopt_issued | ALREADY_CONSUMED | new | A | `test_adopt_issued_already_consumed_leaves_no_trace` | none |
| adopt_issued | BPS | new | A | `test_adopt_issued_bps_leaves_no_trace` | none |
| adopt_issued | BPS_SUM | new | A | `test_adopt_issued_bps_sum_leaves_no_trace` | none |
| adopt_issued | CAPACITY | new | A | `test_adopt_issued_capacity_leaves_no_trace` | none |
| adopt_issued | GATES_DUPLICATE | new | A | `test_adopt_issued_gates_duplicate_leaves_no_trace` | none |
| adopt_issued | GATES_EMPTY | new | A | `test_adopt_issued_gates_empty_leaves_no_trace` | none |
| adopt_issued | GATES_LIMIT | new | A | `test_adopt_issued_gates_limit_leaves_no_trace` | none |
| adopt_issued | GATES_TYPE | new | A | `test_adopt_issued_gates_type_leaves_no_trace` | none |
| adopt_issued | ILLEGAL_TRANSITION | new | A | `test_adopt_issued_illegal_transition_leaves_no_trace` | none |
| adopt_issued | INVALID_AMOUNT | new | A | `test_adopt_issued_invalid_amount_leaves_no_trace` | none |
| adopt_issued | INVALID_ID | new | A | `test_adopt_issued_invalid_id_leaves_no_trace` | none |
| adopt_issued | ISSUANCE_BINDING_CONFLICT | new | A | `test_adopt_issued_issuance_binding_conflict_leaves_no_trace` | none |
| adopt_issued | NOT_HOLDER | new | A | `test_adopt_issued_not_holder_leaves_no_trace` | none |
| adopt_issued | ORDER_BINDING_CONFLICT | new | A | `test_adopt_issued_order_binding_conflict_leaves_no_trace` | none |
| adopt_issued | PAYMENT_BINDING_CONFLICT | new | A | `test_adopt_issued_payment_binding_conflict_leaves_no_trace` | none |
| adopt_issued | PAYMENT_REF | new | A | `test_adopt_issued_payment_ref_leaves_no_trace` | none |
| adopt_issued | POLICY_FLAG | new | A | `test_adopt_issued_policy_flag_leaves_no_trace` | none |
| adopt_issued | PRIMARY_PRICE_MISMATCH | new | A | `test_adopt_issued_primary_price_mismatch_leaves_no_trace` | none |
| adopt_issued | RESERVATION_BINDING_CONFLICT | new | A | `test_adopt_issued_reservation_binding_conflict_leaves_no_trace` | none |
| adopt_issued | RESERVATION_WINDOW | new | A | `test_adopt_issued_reservation_window_leaves_no_trace` | none |
| adopt_issued | SHOW_BINDING_CONFLICT | new | A | `test_adopt_issued_show_binding_conflict_leaves_no_trace` | none |
| adopt_issued | SLOT_OCCUPIED | new | A | `test_adopt_issued_slot_occupied_leaves_no_trace` | none |
| adopt_issued | TICKET_CANCELLED | new | A | `test_adopt_issued_ticket_cancelled_leaves_no_trace` | none |
| adopt_issued | TICKET_NOT_ISSUED | new | A | `test_adopt_issued_ticket_not_issued_leaves_no_trace` | none |
| adopt_issued | TICKET_SOURCE_REQUIRED | new | A | `test_adopt_issued_ticket_source_required_leaves_no_trace` | none |
| adopt_issued | UNKNOWN_RESERVATION | new | A | `test_adopt_issued_unknown_reservation_leaves_no_trace` | none |
| adopt_issued | UNKNOWN_RIGHT | new | A | `test_adopt_issued_unknown_right_leaves_no_trace` | none |
| bind_settlement | ILLEGAL_TRANSITION | new | A | `test_bind_settlement_illegal_transition_leaves_no_trace` | none |
| bind_settlement | INVALID_ID | new | A | `test_bind_settlement_invalid_id_leaves_no_trace` | none |
| bind_settlement | SETTLEMENT_BINDING_CONFLICT | new | A | `test_bind_settlement_settlement_binding_conflict_leaves_no_trace` | none |
| bind_settlement | TERMINAL_IMMUTABLE | new | A | `test_bind_settlement_terminal_immutable_leaves_no_trace` | none |
| bind_settlement | UNKNOWN_LISTING | new | A | `test_bind_settlement_unknown_listing_leaves_no_trace` | none |
| cancel_listing | COMPENSATION_UNDEFINED | new | A | `test_cancel_listing_compensation_undefined_leaves_no_trace` | none |
| cancel_listing | ILLEGAL_TRANSITION | new | A | `test_cancel_listing_illegal_transition_leaves_no_trace` | none |
| cancel_listing | INVALID_ID | new | A | `test_cancel_listing_invalid_id_leaves_no_trace` | none |
| cancel_listing | LISTING_NOT_OPEN | new | A | `test_cancel_listing_listing_not_open_leaves_no_trace` | none |
| cancel_listing | NOT_HOLDER | new | A | `test_cancel_listing_not_holder_leaves_no_trace` | none |
| cancel_listing | TERMINAL_IMMUTABLE | new | A | `test_cancel_listing_terminal_immutable_leaves_no_trace` | none |
| cancel_listing | UNKNOWN_LISTING | new | A | `test_cancel_listing_unknown_listing_leaves_no_trace` | none |
| close | ILLEGAL_TRANSITION | new | A | `test_close_illegal_transition_leaves_no_trace` | none |
| close | INVALID_ID | new | A | `test_close_invalid_id_leaves_no_trace` | none |
| close | TERMINAL_IMMUTABLE | new | A | `test_close_terminal_immutable_leaves_no_trace` | none |
| close | UNKNOWN_LISTING | new | A | `test_close_unknown_listing_leaves_no_trace` | none |
| hold_buy | BUYER_HOLD_LOCKED | new | A | `test_hold_buy_buyer_hold_locked_leaves_no_trace` | none |
| hold_buy | HOLD_BINDING_CONFLICT | new | A | `test_hold_buy_hold_binding_conflict_leaves_no_trace` | none |
| hold_buy | ILLEGAL_TRANSITION | new | A | `test_hold_buy_illegal_transition_leaves_no_trace` | none |
| hold_buy | INVALID_ID | new | A | `test_hold_buy_invalid_id_leaves_no_trace` | none |
| hold_buy | LISTING_NOT_OPEN | new | A | `test_hold_buy_listing_not_open_leaves_no_trace` | none |
| hold_buy | RECIPIENT_MISMATCH | new | A | `test_hold_buy_recipient_mismatch_leaves_no_trace` | none |
| hold_buy | TERMINAL_IMMUTABLE | new | A | `test_hold_buy_terminal_immutable_leaves_no_trace` | none |
| hold_buy | UNKNOWN_LISTING | new | A | `test_hold_buy_unknown_listing_leaves_no_trace` | none |
| list_resale | ADMISSION_LOCKED | new | A | `test_list_resale_admission_locked_leaves_no_trace` | ADMISSION_LOCKED |
| list_resale | ALREADY_CONSUMED | new | A | `test_list_resale_already_consumed_leaves_no_trace` | ALREADY_CONSUMED |
| list_resale | ILLEGAL_TRANSITION | new | A | `test_list_resale_illegal_transition_leaves_no_trace` | none |
| list_resale | INVALID_AMOUNT | new | A | `test_list_resale_invalid_amount_leaves_no_trace` | none |
| list_resale | INVALID_ID | new | A | `test_list_resale_invalid_id_leaves_no_trace` | none |
| list_resale | LISTING_BINDING_CONFLICT | new | A | `test_list_resale_listing_binding_conflict_leaves_no_trace` | none |
| list_resale | LISTING_WINDOW | new | A | `test_list_resale_listing_window_leaves_no_trace` | none |
| list_resale | NOT_HOLDER | new | A | `test_list_resale_not_holder_leaves_no_trace` | none |
| list_resale | RECIPIENT_IS_HOLDER | new | A | `test_list_resale_recipient_is_holder_leaves_no_trace` | none |
| list_resale | RESALE_CAP | new | A | `test_list_resale_resale_cap_leaves_no_trace` | none |
| list_resale | RESALE_POLICY_REJECTED | new | A | `test_list_resale_resale_policy_rejected_leaves_no_trace` | none |
| list_resale | RIGHT_SALE_LOCKED | new | A | `test_list_resale_right_sale_locked_leaves_no_trace` | none |
| list_resale | STALE_VERSION | new | A | `test_list_resale_stale_version_leaves_no_trace` | none |
| list_resale | TERMINAL_IMMUTABLE | new | A | `test_list_resale_terminal_immutable_leaves_no_trace` | none |
| list_resale | TICKET_CANCELLED | new | A | `test_list_resale_ticket_cancelled_leaves_no_trace` | none |
| list_resale | TICKET_NOT_ISSUED | new | A | `test_list_resale_ticket_not_issued_leaves_no_trace` | none |
| list_resale | TICKET_SOURCE_REQUIRED | new | A | `test_list_resale_ticket_source_required_leaves_no_trace` | none |
| list_resale | UNKNOWN_RESERVATION | new | A | `test_list_resale_unknown_reservation_leaves_no_trace` | none |
| list_resale | UNKNOWN_RIGHT | new | A | `test_list_resale_unknown_right_leaves_no_trace` | none |
| list_resale | VERSION_TYPE | new | A | `test_list_resale_version_type_leaves_no_trace` | none |
| observe_resale_payment | BUYER_MISMATCH | new | A | `test_observe_resale_payment_buyer_mismatch_leaves_no_trace` | none |
| observe_resale_payment | ILLEGAL_TRANSITION | new | A | `test_observe_resale_payment_illegal_transition_leaves_no_trace` | none |
| observe_resale_payment | INVALID_AMOUNT | new | A | `test_observe_resale_payment_invalid_amount_leaves_no_trace` | none |
| observe_resale_payment | INVALID_ID | new | A | `test_observe_resale_payment_invalid_id_leaves_no_trace` | none |
| observe_resale_payment | LISTING_NOT_OPEN | new | A | `test_observe_resale_payment_listing_not_open_leaves_no_trace` | none |
| observe_resale_payment | LISTING_PAYMENT_BOUND | new | A | `test_observe_resale_payment_listing_payment_bound_leaves_no_trace` | none |
| observe_resale_payment | PAYMENT_BINDING_CONFLICT | new | A | `test_observe_resale_payment_payment_binding_conflict_leaves_no_trace` | none |
| observe_resale_payment | PAYMENT_REF | new | A | `test_observe_resale_payment_payment_ref_leaves_no_trace` | none |
| observe_resale_payment | RECIPIENT_MISMATCH | new | A | `test_observe_resale_payment_recipient_mismatch_leaves_no_trace` | none |
| observe_resale_payment | RESALE_AMOUNT_MISMATCH | new | A | `test_observe_resale_payment_resale_amount_mismatch_leaves_no_trace` | none |
| observe_resale_payment | TERMINAL_IMMUTABLE | new | A | `test_observe_resale_payment_terminal_immutable_leaves_no_trace` | none |
| observe_resale_payment | UNKNOWN_LISTING | new | A | `test_observe_resale_payment_unknown_listing_leaves_no_trace` | none |
| reject_external | EXTERNAL_UNSUPPORTED | new | A | `test_reject_external_external_unsupported_leaves_no_trace` | none |
| reject_external | INVALID_ID | new | A | `test_reject_external_invalid_id_leaves_no_trace` | none |
| release_hold | BUYER_MISMATCH | new | A | `test_release_hold_buyer_mismatch_leaves_no_trace` | none |
| release_hold | ILLEGAL_TRANSITION | new | A | `test_release_hold_illegal_transition_leaves_no_trace` | none |
| release_hold | INVALID_ID | new | A | `test_release_hold_invalid_id_leaves_no_trace` | none |
| release_hold | TERMINAL_IMMUTABLE | new | A | `test_release_hold_terminal_immutable_leaves_no_trace` | none |
| release_hold | UNKNOWN_HOLD | new | A | `test_release_hold_unknown_hold_leaves_no_trace` | none |
| restore | INVALID_JOURNAL | new | A | `test_restore_invalid_journal_leaves_no_trace` | none |
| set_clock | CLOCK | new | A | `test_set_clock_clock_leaves_no_trace` | none |
| set_clock | CLOCK_REGRESSION | new | A | `test_set_clock_clock_regression_leaves_no_trace` | none |
| set_clock | IDEMPOTENCY_CONFLICT | new | A | `test_set_clock_idempotency_conflict_leaves_no_trace` | none |
| set_clock | INVALID_ID | new | A | `test_set_clock_invalid_id_leaves_no_trace` | none |
### Admission

Methods in [test_admission_rejection_atomicity.py](../../reference/booking_resale_admission/test_admission_rejection_atomicity.py)::AdmissionRejectionAtomicityTests.

| Command | Code | Status | Class | Test | Expected restore error |
|---|---|---|---|---|---|
| adopt_issued | ALREADY_CONSUMED | new | A | `test_adopt_issued_already_consumed_leaves_no_trace` | none |
| adopt_issued | BPS | new | A | `test_adopt_issued_bps_leaves_no_trace` | none |
| adopt_issued | BPS_SUM | new | A | `test_adopt_issued_bps_sum_leaves_no_trace` | none |
| adopt_issued | CAPACITY | new | A | `test_adopt_issued_capacity_leaves_no_trace` | none |
| adopt_issued | GATES_DUPLICATE | new | A | `test_adopt_issued_gates_duplicate_leaves_no_trace` | none |
| adopt_issued | GATES_EMPTY | new | A | `test_adopt_issued_gates_empty_leaves_no_trace` | none |
| adopt_issued | GATES_LIMIT | new | A | `test_adopt_issued_gates_limit_leaves_no_trace` | none |
| adopt_issued | GATES_TYPE | new | A | `test_adopt_issued_gates_type_leaves_no_trace` | none |
| adopt_issued | ILLEGAL_TRANSITION | new | A | `test_adopt_issued_illegal_transition_leaves_no_trace` | none |
| adopt_issued | INVALID_AMOUNT | new | A | `test_adopt_issued_invalid_amount_leaves_no_trace` | none |
| adopt_issued | INVALID_ID | new | A | `test_adopt_issued_invalid_id_leaves_no_trace` | none |
| adopt_issued | ISSUANCE_BINDING_CONFLICT | new | A | `test_adopt_issued_issuance_binding_conflict_leaves_no_trace` | none |
| adopt_issued | NOT_HOLDER | new | A | `test_adopt_issued_not_holder_leaves_no_trace` | none |
| adopt_issued | ORDER_BINDING_CONFLICT | new | A | `test_adopt_issued_order_binding_conflict_leaves_no_trace` | none |
| adopt_issued | PAYMENT_BINDING_CONFLICT | new | A | `test_adopt_issued_payment_binding_conflict_leaves_no_trace` | none |
| adopt_issued | PAYMENT_REF | new | A | `test_adopt_issued_payment_ref_leaves_no_trace` | none |
| adopt_issued | POLICY_FLAG | new | A | `test_adopt_issued_policy_flag_leaves_no_trace` | none |
| adopt_issued | PRIMARY_PRICE_MISMATCH | new | A | `test_adopt_issued_primary_price_mismatch_leaves_no_trace` | none |
| adopt_issued | RESERVATION_BINDING_CONFLICT | new | A | `test_adopt_issued_reservation_binding_conflict_leaves_no_trace` | none |
| adopt_issued | RESERVATION_WINDOW | new | A | `test_adopt_issued_reservation_window_leaves_no_trace` | none |
| adopt_issued | SHOW_BINDING_CONFLICT | new | A | `test_adopt_issued_show_binding_conflict_leaves_no_trace` | none |
| adopt_issued | SLOT_OCCUPIED | new | A | `test_adopt_issued_slot_occupied_leaves_no_trace` | none |
| adopt_issued | TICKET_CANCELLED | new | A | `test_adopt_issued_ticket_cancelled_leaves_no_trace` | none |
| adopt_issued | TICKET_NOT_ISSUED | new | A | `test_adopt_issued_ticket_not_issued_leaves_no_trace` | none |
| adopt_issued | TICKET_SOURCE_REQUIRED | new | A | `test_adopt_issued_ticket_source_required_leaves_no_trace` | none |
| adopt_issued | TICKET_SOURCE_UNAVAILABLE | new | A | `test_adopt_issued_ticket_source_unavailable_leaves_no_trace` | none |
| adopt_issued | UNKNOWN_RESERVATION | new | A | `test_adopt_issued_unknown_reservation_leaves_no_trace` | none |
| adopt_issued | UNKNOWN_RIGHT | new | A | `test_adopt_issued_unknown_right_leaves_no_trace` | none |
| authorize_admission | ADMISSION_BINDING_CONFLICT | new | A | `test_authorize_admission_admission_binding_conflict_leaves_no_trace` | none |
| authorize_admission | ADMISSION_LOCKED | new | A | `test_authorize_admission_admission_locked_leaves_no_trace` | none |
| authorize_admission | ADMISSION_REQUEST | new | A | `test_authorize_admission_admission_request_leaves_no_trace` | none |
| authorize_admission | ADMISSION_WINDOW | new | A | `test_authorize_admission_admission_window_leaves_no_trace` | none |
| authorize_admission | ALREADY_CONSUMED | new | A | `test_authorize_admission_already_consumed_leaves_no_trace` | none |
| authorize_admission | CREDENTIAL_STALE | new | A | `test_authorize_admission_credential_stale_leaves_no_trace` | none |
| authorize_admission | EXTERNAL_UNSUPPORTED | new | A | `test_authorize_admission_external_unsupported_leaves_no_trace` | none |
| authorize_admission | GATE_UNKNOWN | new | A | `test_authorize_admission_gate_unknown_leaves_no_trace` | none |
| authorize_admission | ILLEGAL_TRANSITION | new | A | `test_authorize_admission_illegal_transition_leaves_no_trace` | none |
| authorize_admission | INVALID_ID | new | A | `test_authorize_admission_invalid_id_leaves_no_trace` | none |
| authorize_admission | LISTING_LOCKED | new | A | `test_authorize_admission_listing_locked_leaves_no_trace` | none |
| authorize_admission | NOT_HOLDER | new | A | `test_authorize_admission_not_holder_leaves_no_trace` | none |
| authorize_admission | OWNERSHIP_SOURCE_UNAVAILABLE | new | A | `test_authorize_admission_ownership_source_unavailable_leaves_no_trace` | none |
| authorize_admission | REVOCATION_SOURCE_UNAVAILABLE | new | A | `test_authorize_admission_revocation_source_unavailable_leaves_no_trace` | none |
| authorize_admission | RIGHT_NOT_ACTIVE | new | A | `test_authorize_admission_right_not_active_leaves_no_trace` | none |
| authorize_admission | SETTLEMENT_SOURCE_REQUIRED | new | A | `test_authorize_admission_settlement_source_required_leaves_no_trace` | none |
| authorize_admission | SETTLEMENT_SOURCE_UNAVAILABLE | new | A | `test_authorize_admission_settlement_source_unavailable_leaves_no_trace` | none |
| authorize_admission | SETTLEMENT_VIEW_REJECTED | new | A | `test_authorize_admission_settlement_view_rejected_leaves_no_trace` | none |
| authorize_admission | STALE_VERSION | new | A | `test_authorize_admission_stale_version_leaves_no_trace` | none |
| authorize_admission | TICKET_SOURCE_UNAVAILABLE | new | A | `test_authorize_admission_ticket_source_unavailable_leaves_no_trace` | none |
| authorize_admission | UNKNOWN_RIGHT | new | A | `test_authorize_admission_unknown_right_leaves_no_trace` | none |
| authorize_admission | VENUE_SOURCE_UNAVAILABLE | new | A | `test_authorize_admission_venue_source_unavailable_leaves_no_trace` | none |
| authorize_admission | VERSION_TYPE | new | A | `test_authorize_admission_version_type_leaves_no_trace` | none |
| consume | ADMISSION_EXPIRED | new | A | `test_consume_admission_expired_leaves_no_trace` | none |
| consume | ADMISSION_REQUEST | new | A | `test_consume_admission_request_leaves_no_trace` | none |
| consume | ADMISSION_REQUEST_MISMATCH | new | A | `test_consume_admission_request_mismatch_leaves_no_trace` | none |
| consume | ADMISSION_REQUIRED | new | A | `test_consume_admission_required_leaves_no_trace` | none |
| consume | ALREADY_CONSUMED | new | A | `test_consume_already_consumed_leaves_no_trace` | none |
| consume | CONSUME_BINDING_CONFLICT | new | A | `test_consume_consume_binding_conflict_leaves_no_trace` | none |
| consume | CREDENTIAL_STALE | new | A | `test_consume_credential_stale_leaves_no_trace` | none |
| consume | EXTERNAL_UNSUPPORTED | new | A | `test_consume_external_unsupported_leaves_no_trace` | none |
| consume | GATE_MISMATCH | new | A | `test_consume_gate_mismatch_leaves_no_trace` | none |
| consume | GATE_UNKNOWN | new | A | `test_consume_gate_unknown_leaves_no_trace` | none |
| consume | ILLEGAL_TRANSITION | new | A | `test_consume_illegal_transition_leaves_no_trace` | none |
| consume | INVALID_ID | new | A | `test_consume_invalid_id_leaves_no_trace` | none |
| consume | LISTING_LOCKED | new | A | `test_consume_listing_locked_leaves_no_trace` | none |
| consume | OWNERSHIP_SOURCE_UNAVAILABLE | new | A | `test_consume_ownership_source_unavailable_leaves_no_trace` | none |
| consume | REVOCATION_SOURCE_UNAVAILABLE | new | A | `test_consume_revocation_source_unavailable_leaves_no_trace` | none |
| consume | RIGHT_NOT_ACTIVE | new | A | `test_consume_right_not_active_leaves_no_trace` | none |
| consume | SETTLEMENT_SOURCE_REQUIRED | new | A | `test_consume_settlement_source_required_leaves_no_trace` | none |
| consume | SETTLEMENT_SOURCE_UNAVAILABLE | new | A | `test_consume_settlement_source_unavailable_leaves_no_trace` | none |
| consume | SETTLEMENT_VIEW_REJECTED | new | A | `test_consume_settlement_view_rejected_leaves_no_trace` | none |
| consume | STALE_VERSION | new | A | `test_consume_stale_version_leaves_no_trace` | STALE_VERSION |
| consume | TICKET_SOURCE_UNAVAILABLE | new | A | `test_consume_ticket_source_unavailable_leaves_no_trace` | none |
| consume | UNKNOWN_RIGHT | new | A | `test_consume_unknown_right_leaves_no_trace` | none |
| consume | VENUE_SOURCE_UNAVAILABLE | new | A | `test_consume_venue_source_unavailable_leaves_no_trace` | none |
| consume | VERSION_TYPE | new | A | `test_consume_version_type_leaves_no_trace` | none |
| reject_external | EXTERNAL_UNSUPPORTED | new | A | `test_reject_external_external_unsupported_leaves_no_trace` | none |
| reject_external | INVALID_ID | new | A | `test_reject_external_invalid_id_leaves_no_trace` | none |
| restore | INVALID_JOURNAL | new | A | `test_restore_invalid_journal_leaves_no_trace` | none |
| set_clock | CLOCK | new | A | `test_set_clock_clock_leaves_no_trace` | none |
| set_clock | CLOCK_REGRESSION | new | A | `test_set_clock_clock_regression_leaves_no_trace` | none |
| set_clock | IDEMPOTENCY_CONFLICT | new | A | `test_set_clock_idempotency_conflict_leaves_no_trace` | none |
| set_clock | INVALID_ID | new | A | `test_set_clock_invalid_id_leaves_no_trace` | none |
| set_clock | TICKET_SOURCE_UNAVAILABLE | new | A | `test_set_clock_ticket_source_unavailable_leaves_no_trace` | none |

## Characterizations and reachability

| Finding | Class | Evidence / observed shape |
|---|---|---|
| Delegated authorization survives local window rejection with skewed clocks | B | `AdmissionRejectionAtomicityTests.test_char_authorize_clock_skew_window`: reservation advances directly to T0+120000, admission stays T0, expiry T0+120001. The reservation accepts, then local ADMISSION_WINDOW rejects. Local canonical state/views/digest/journal stay unchanged; only that side's reservation becomes ADMISSION_AUTHORIZED with admit-1. Restore preserves both sources and reproduces local state. A later valid clock agrees locally; the reservation trace remains. |
| Injected post-mutation `_invariant` failures, excluding adopt | B | One named `test_char_fault_<command>` per row below; journal matches untouched control and restore equals control, while live canonical state/digest differ. Exact canonical shape equals a separately successful application with the omitted journal entry and listing accepted_entries count removed. This is a source-informed fault characterization, not rollback coverage. |
| Admission adopt on an already authorized public reservation | A | `test_char_adopt_issued_admitted_ticket_is_not_issued` compares controls, sources, restore and later command; returns TICKET_NOT_ISSUED, not ADMISSION_LOCKED. |

The skew finding is B because §11.2 allows a reservation clock ahead of the local
clock; §11.3's no-consume clause applies to its fifteen freshness predicates,
not local window validation after delegation. §11.5 promises omission from this
machine's journal. No explicit cross-machine all-or-nothing window contract was
found. Internal MOCK_INVARIANT is explicitly an implementation fault rather than
a caller-adjustable rejection (§6); arbitrary injected exceptions have no
contract-defined rollback promise. No class C violation was found. No source fix
or contract reinterpretation was made.

Fault rows (all `new`, B; `MOCK_INVARIANT`), asserted independently:

| Machine | Command | Test |
|---|---|---|
| Resale | accept_resale | `test_char_fault_accept_resale` |
| Resale | bind_settlement | `test_char_fault_bind_settlement` |
| Resale | cancel_listing | `test_char_fault_cancel_listing` |
| Resale | close | `test_char_fault_close` |
| Resale | hold_buy | `test_char_fault_hold_buy` |
| Resale | list_resale | `test_char_fault_list_resale` |
| Resale | observe_resale_payment | `test_char_fault_observe_resale_payment` |
| Resale | release_hold | `test_char_fault_release_hold` |
| Resale | set_clock | `test_char_fault_set_clock` |
| Admission | authorize_admission | `test_char_fault_authorize_admission` |
| Admission | consume | `test_char_fault_consume` |
| Admission | set_clock | `test_char_fault_set_clock` |

Both modules' `test_char_fault_rows_cover_replayable_commands` require the
fault-row set to equal `REPLAYABLE - {"adopt_issued"}`. Gate-level faults are
not exercised. Unbound fault fixtures deliberately avoid bound-source claims.

Not applicable / design reachability corrections:

- Admission `adopt_issued / ADMISSION_LOCKED`: a public authorization changes
  reservation phase to ADMISSION_AUTHORIZED. `_match_issued` checks phase ==
  ISSUED first, so TICKET_NOT_ISSUED masks its later admission-id guard. The
  characterization above proves the public fixture result. Reaching that guard
  needs an inconsistent/stubbed ISSUED-plus-live-admission answer.
- Resale `list_resale / RESERVATION_BINDING_CONFLICT`: `_require_authority`
  first requires the named reservation's issuance_id and right.right_id to equal
  the command's right. Another real reservation cannot own the same issuance;
  a missing reservation is UNKNOWN_RESERVATION (new regression), and another
  issuance is UNKNOWN_RIGHT. The later local binding guard needs an inconsistent
  ticket-source answer, not a valid public ReservationMachine history.
- Resale local RIGHT_NOT_ACTIVE / accept NOT_HOLDER / STALE_VERSION / stale
  payment guards cannot be independently driven while preserving its own public
  FSM invariants: resale has no local consume command, a transfer clears the
  listing and changes its phase first. Bound-source consumed/holder/version
  rejections that are reachable are tested. Arbitrary contradictory source
  answers and arbitrary source-provided error strings are not an exhaustive
  rejection universe.

## Executed verification

Commands are run from repository root unless the command includes a directory.
Python version and final command results are recorded below. CI pins Python 3.12;
the local interpreter may differ. Failed development runs are retained here as
fixture diagnostics, never reported as contract failures or passing runs.

- Initial resale narrow discovery: 91 tests, 3 failures (no_source accidentally
  removed reservation_id; admission-locked transfer fixture had no payment).
  Corrected fixtures; no source change.
- Initial admission discovery: import failed on a duplicate generated row name;
  then 70 tests, 3 failures (unreachable adopt admission-lock guard, admission id
  reuse binding precedence, consumed presentation version precedence).
  Removed duplicate rows, documented public guard reachability, and corrected
  command inputs; no source change.
- Intermediate combined `-p '*rejection_atomicity.py'` discovery: 234 tests OK
  (includes the pre-existing reservation module; not the final new-module count).
- Subsequent narrow module runs: resale 114 then 119 tests OK; admission 76,
  86 then 88 tests OK as documented gaps were added. Final counts below.
- Scratch stdin sanity script, importing each new TestCase only in the scratch
  process: a unilateral successful set_clock trace caused each `assert_same_as`
  helper to raise AssertionError as expected. No scratch file committed.

All commands below used `PYTHONDONTWRITEBYTECODE=1`.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | PASS, exit 0; capability register ok: paths=349 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | PASS, exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | PASS, exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | PASS, exit 0; docs index ok: scanned=224 indexed=189 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | PASS, exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | PASS, exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | PASS, exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | PASS, exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | PASS, exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | PASS, exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | PASS, exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | PASS, exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | PASS, exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 --version` | Python 3.13.5 |
| `python3 -m unittest discover -s reference/booking_resale_admission -p test_resale_rejection_atomicity.py` | PASS, exit 0; 119 tests |
| `python3 -m unittest discover -s reference/booking_resale_admission -p test_admission_rejection_atomicity.py` | PASS, exit 0; 89 tests |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS, exit 0; 184 tests |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS, exit 0; 395 tests |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS, exit 0; 146 tests |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS, exit 0; 74 tests |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS, exit 0; 163 tests |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | FAIL, exit 1; 100 tests; 1 startup error (CORE_UNAVAILABLE); 170.091s |
| `python3 scripts/check_openapi_contract.py` | PASS, exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | PASS, exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS, exit 0; self-test: pass |
| `python3 -m unittest discover -s reference/booking_resale_admission -p test_resale_rejection_atomicity.py` | PASS, exit 0; 119 tests |
| `python3 -m unittest discover -s reference/booking_resale_admission -p test_admission_rejection_atomicity.py` | PASS, exit 0; 89 tests |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS, exit 0; 395 tests |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS, exit 0; 100 tests |
| `python3 -m unittest integration_gate.test_http_gate.BrowserAccessTests.test_subprocess_flag_serves_the_opt_in_preflight` | PASS; 1 test, 0.194s; existing ResourceWarning for an unclosed subprocess stream |
| `python3 -` (stdin diagnostic: build loopback server, recover_now, close) | PASS; core initialized with browser origin enabled; no server served requests |
| `python3 -` (stdin sanity: successful unilateral clock injection) | PASS; both comparison helpers detected the trace via expected AssertionError |
| `git rev-parse HEAD origin/main HEAD:reference/v0.3-rc1` | Values recorded above; initial and final HEAD unchanged |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS before/after; exact required blobs recorded above |
| `git diff --check` | PASS; no whitespace errors |
| `git diff --exit-code -- runtime reference/v0.3-rc1 .aiops docs/tasks .github docs/status/CONTRACT_ERROR_CODE_COVERAGE.md reference/booking_resale_admission/resale_fsm.py reference/booking_resale_admission/admission_fsm.py reference/booking_resale_admission/mock_gates.py reference/booking_resale_admission/reservation_fsm.py` | PASS; no differences |
| `git status --short` | Only the four authorized paths changed; no Git publication |


NOT_RUN / not applicable:

- `git fetch origin main`: supervisor's no-network instruction; cached main only.
- `ktx-kernel.yml`, cargo workspace/crate tests, fmt, clippy: runtime paths untouched.
- SDK, localnet, ZK, paid-storage and production checks: untouched surfaces;
  this node runs the offline stdlib protocol steps only. Hosted full verification
  remains a supervisor/PR gate; no hosted result is claimed here.
- Exact-head KTX CI and KIX protocol CI: run ID/status/conclusion NOT_RUN;
  no final delivery commit or PR exists in this builder session.
- Post-merge main CI: N/A, not merged.

The first HTTP/readiness run had one existing subprocess startup failure:
`BrowserAccessTests.test_subprocess_flag_serves_the_opt_in_preflight` returned
CORE_UNAVAILABLE; the other 99 tests did not error. Inspection traced that label
to `GateServer.recover_now` / unpublished core initialization, not an assertion
in the touched tests. A diagnostic core recovery and the single test both passed.
One subsequent full HTTP/readiness run passed all 100 in 6.277s. No transport,
core, timeout, CI or environment source was changed. The initial startup failure's
underlying cause remains unproven; success on recheck does not erase it.

Final narrow runs: 119 resale + 89 admission tests, including 12 fault rows,
2 fault-set guards, the clock-skew probe and the adopt reachability probe.
Full booking discovery: 395 tests. Other reference discoveries: 184 settlement,
146 credit, 74 AI delegation, 163 token reward. All 27 document checks and four
OpenAPI checks passed. Local Python is 3.13.5, different from CI's 3.12.

## Deviations, limits and follow-up

The design's two unreachable public guard rows are documented above rather than
manufactured by corrupting private state. Extra inherited mock-validator,
unknown-entity and transition rows fill reachable gaps exposed while reading
sources. Shared fixture/assertion helpers live in the resale test module to
avoid another changed path. Tests use independently instantiated inspectable
stub sources only for explicit unavailable/malformed-answer predicates. Fault
rows pin observed partial mutation instead of asserting rollback. The root
DECISION_REQUIRED file is unnecessary: no hardware, money, credentials, public
endpoint, production runtime, new command or policy value is needed.

Evidence is author-side, in-process and source-informed, with ordered commands,
not independent clean-room validation or concurrency. No durability, bank
exactly-once, distributed fencing, chain finality, credential reissue, venue
admission, cross-channel exclusion, legal compliance or production claim. No
performance number or evidence grade increase. Remaining uncertainty: cross-
machine atomicity under clock skew, gate-level/internal fault semantics and
external source trust need separate contract decisions and separately scoped
work. No implementation change is authorized by these characterizations.
