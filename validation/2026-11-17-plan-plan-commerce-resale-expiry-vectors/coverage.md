# Coverage mapping before adding tests

Task: `plan-plan-commerce-resale-expiry-vectors`; task input is the supervisor-provided node specification and read-only design in this session, not a new docs/tasks document.

| Requirement | Existing coverage | Gap addressed |
|---|---|---|
| Unpaid expiry payment refusal | Sufficient unit coverage: `reference/booking_resale_admission/test_resale_rejection_atomicity.py::ResaleRejectionAtomicityTests.test_observe_resale_payment_listing_not_open_leaves_no_trace` (dynamically installed row) | Portable ordered history not covered |
| Paid expiry preserves payment, holder/version and refuses transfer/cancel | Sufficient unit coverage: `reference/booking_resale_admission/test_resale_fsm.py::ResaleFsmTests.test_stale_listing_policy_and_expiry_do_not_transfer`; rejection atomicity accept/cancel rows | Portable paid history not covered |
| Original-key replay after time advancement | Partially covered by `test_commerce_temporal_vectors.py` and `test_commerce_historical_receipt_vectors.py` | Listing/payment first receipts versus current expiry |
| Complete bodies, outcomes, diagnostics, pins | Partially covered by journey/historical/entry-order infrastructure | New pack and exact-byte replay |
| Refusal/replay non-mutation | Sufficient unit coverage in resale atomicity and generic historical replay | Detached checkpoints for all five host machines in this pack |
| Corruption detection | New pack not covered | Detached error/fact/diagnostic/order/omission/duplicate/reference mutations; injected effects |
| Companion exact coverage | Partially covered by six-family validator | Seventh family with 27 entries; previous 240 entries unchanged |
| Qualification | Sufficient existing companion/producer/binding checks | Preserve 13 NOT_BOUND reads, HOLD_SEMANTIC, SD1 OPEN/User-owned, external acceptance UNVERIFIED |

Contract basis: BOOKING_RESALE_ADMISSION_GATES.md §§10.1–10.4 and immutable first-result §10.7. Source-informed local evidence only. Synthetic TTL is not product policy. Product TTL/compensation remain UNDETERMINED with Astra/User and existing legal/accounting owners.
