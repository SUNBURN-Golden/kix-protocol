# Coverage recorded before adding tests

Node: plan-plan-commerce-admission-cancellation-vec. Task input is the supervisor-supplied node specification/design in this session; no new docs/tasks input exists. Historical Task 005 is context, not this node authorization.

| Requirement | Existing coverage | Portable gap / addition |
|---|---|---|
| Cancellation ordering | Sufficient: reference/booking_resale_admission/test_admission_fsm.py::AdmissionFsmTests.test_cancel_before_issue_blocks_entry_and_cancel_after_issue_does_not_void_it; BOOKING_RESALE_ADMISSION_GATES.md §11.4 agrees | Missing: three portable published-action histories, 26 ordered steps |
| Explicit issuance/adoption/authorization/consumption | Sufficient: cited regression, test_commerce_entry_resale_order_vectors.py::CommerceEntryResaleOrderVectorTests.test_consumption_and_ownership_versions_stay_distinct and journey conformance | Missing in cancellation pack: independent phase/identity expectations |
| Refusal atomicity | Sufficient behavior: test_admission_rejection_atomicity.py rows for ticket_cancelled and ticket_paid; partially covered host-wide cancellation evidence | Missing: all five machines canonical_state/state_digest/export_journal and detached views before/after each refusal; injected effect detection |
| Portable bytes, provenance, references | Partially covered: test_commerce_journey_receipts.py and existing vector helpers | Missing for this family: complete canonical receipts, source pins, exact input references |
| Negative controls | Sufficient reusable patterns in entry/resale-order and resale-expiry suites | Missing for new pack: wrong codes/types/receipts, order/omission/duplicate/crossed references, stale pins, repinned malformed inputs before execution |
| Companion navigation/preservation | Sufficient existing seven-family index validator and original binding checker | Append eighth family; retain original seven packs/267 entries and qualification metadata |
| Qualification boundaries | Sufficient producer/binding checks and companion qualification controls | Retain HOLD_SEMANTIC, 13 NOT_BOUND, SD1 OPEN/User-owned, acceptance UNVERIFIED |

Rejected-key retention is process-local bookkeeping, excluded from business state/digest/journals; no claim of unchanged internal memory or restart retention. No producer, contract or policy change is authorized.
