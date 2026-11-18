# Pre-implementation coverage map

Task: plan-commerce-bound-issuance-vectors. Authoritative task input: supervisor node specification/design in session; no node document exists under docs/tasks (Task 005 is historical program context).

| Requirement | Existing coverage | Classification / gap |
|---|---|---|
| AUTHORIZED/CAPTURED refusal, rejected original key after commit, fresh key issuance | reference/booking_resale_admission/test_reservation_fsm.py::ReservationFsmTests.test_settlement_gate_refuses_uncommitted_finality | Sufficient semantics; absent portable reservation-bound history |
| Committed gross mismatch retains PAYMENT_NOTED/no right | same module ::ReservationFsmTests.test_bound_issue_checks_gross_and_replays_only_with_the_commit_view | Sufficient semantics; absent separate portable mismatch history |
| All-machine atomicity, strict bytes/pins, source-informed outputs | test_commerce_historical_receipt_vectors.py and test_commerce_entry_resale_order_vectors.py | Partial: reusable infrastructure, no bound-issuance case |
| Portable settlement-bound issuance histories | fixtures/commerce_journey_conformance_v1.json (44 steps), commerce_temporal_inputs_v1.json, commerce_historical_inputs_v1.json, commerce_entry_resale_order_inputs_v1.json | Not covered: explicit pre-edit scan finds zero reservation_bind_settlement actions in all four input packs; journey SETTLEMENT_NOT_COMMITTED concerns resale acceptance |
| Complete per-step bound receipts/refusals/snapshots/references and mutation sensitivity | None in merged packs | Not covered; new companion pack and test module |

These are source-informed comparisons, not independent consumer acceptance. No existing tests/packs/implementations require changes.
