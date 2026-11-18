# Coverage mapped before implementation

Task: plan-plan-commerce-hold-release-vectors; supplied node specification is the task input (no issue/task document exists). Local origin/main and branch HEAD: f315a499b9894ad6af8933461ad7267eb1b1c4ad. Fetch prohibited by supervisor; remote freshness unverified.

| Requirement | Existing coverage | Gap addressed |
|---|---|---|
| Expiry retains RESERVED, refuses confirmation/competition, explicit release/reuse | Sufficient behavior: test_reservation_fsm.py::ReservationFsmTests.test_expiry_does_not_release_until_an_explicit_release and test_overlapping_holds_and_replay_do_not_double_book | Portable boundary and after-boundary histories absent |
| Original-key replay after reuse | Partial: overlap regression and test_commerce_historical_receipt_vectors.py | Complete A hold/release and B hold replay alongside current B occupancy |
| Refusal/replay preserves business state, digest, accepted journal | Sufficient local refusals: test_reservation_rejection_atomicity.py::ReservationRejectionAtomicityTests.test_confirm_expired_leaves_no_trace and test_hold_slot_occupied_leaves_no_trace; partial portable coverage | All-five-machine detached snapshots for each refusal and replay |
| Process-local rejected keys | Sufficient behavior: overlap regression and contract section 9.4 | Repeat B refusal while free and after reuse; changed-binding conflict |
| Canonical pins, complete ordered outcomes | Not covered for new family | Exact UTF-8 bytes, schemas, independent identity/action/error maps and reference resolution |
| Premature freeing, double occupancy, outcome mutation | Not covered for new pack | Detached mutations and test-local injected effects, no source mutation |
| Crossed index references | Existing generic controls; new family absent | Family-specific crossed pins, same-action references, binding and replay symbols |
| Qualification/preservation | Existing index and offline guards | Preserve prior packs/statuses/producer/binding; inventories and checks |

Source-informed in-process evidence only. TTL/policy: UNDETERMINED—Astra/User. Legal effects: UNDETERMINED—User/legal. No consumer acceptance, durable rejected keys, production or independent-review claims.
