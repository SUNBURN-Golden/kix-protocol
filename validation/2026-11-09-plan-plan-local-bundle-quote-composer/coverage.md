# Coverage mapped before implementation

Paths below are relative to `reference/`. Console tests are in
`booking_resale_admission/test_commerce_calculation_console.py`.

| Requirement | Existing coverage classification | Gap to address |
|---|---|---|
| File-free multi-line quote, split plan and selected refund | Partial: `test_guided_split_refund_journey_and_file_parity` guides legs only | Guided quote journey through real children, complete exchange equality with file journey |
| Request bytes, hashes, original refund routes | Partial: console parity above and `test_commerce_calculation_client.py` exact-byte journeys | Compare entire guided/file exchange sequences |
| Large atoms, null/string caps, empty discounts, caller ordering | Partial: `test_free_and_large_atom_journeys_preserve_wire_strings_and_empty_routes`; file decoding tests | Guided precision/free parity, explicit cap syntax and array order |
| Duplicate identities, invalid eligibility, mixed assets, excessive discounts | Arithmetic sufficient: `v0.3-rc1/test_commerce.py` tests `test_invalid_discount_duplicates_and_scope_are_rejected`, `test_mixed_assets_and_aggregate_overflow_are_rejected` | Real-child guided refusals, unmodified inputs, one dispatch each |
| Ordered discount/cap arithmetic and route conservation | Sufficient: frozen `test_discount_order_eligibility_and_cap_are_bound_and_observable`, `test_every_refund_subset_conserves_original_route_and_discount_shares` | Reuse; no copied arithmetic tests |
| Replacement invalidation including failure/EOF | Partial: `test_quote_replacement_identical_failed_and_declined_invalidate_dependents`, guided-leg invalidation/EOF tests | Composition clears quote/input/dependents before reading, including all early exits |
| No calculation on composition/decline; once on confirmation | Partial: existing consent and guided-leg tests | Count actual Popen launches and prohibit in-process quote calculations |
| Terminal uncertainty fencing | Sufficient: existing console transport/plan uncertainty tests and client tests | Retain existing tests unchanged |
| CE1 integer and encoding refusal | Partial: existing file and guided-leg tests | Shared integer parser at every quote integer prompt, typed JSON eligibility/caps, whole-candidate encoding failure |

This is builder-authored, source-informed coverage mapping. It does not establish
independent arithmetic verification or non-author A2 review.
