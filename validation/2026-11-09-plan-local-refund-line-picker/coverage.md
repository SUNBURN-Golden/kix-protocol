# Coverage mapped before implementation

Task: `plan-local-refund-line-picker`; immutable input is the supplied node and
design plan (no issue or task document). Paths below are relative to `reference/`.
Console cases are in `booking_resale_admission/test_commerce_calculation_console.py`.

| Requirement | Existing classification and evidence | Picker gap |
|---|---|---|
| Real bundle quote, split plan, refund; exact requests/results/hashes | Partial: `test_bundle_journey_file_parity`, `test_guided_split_refund_journey_and_file_parity` | Guided ID selection and complete JSON-path exchange parity |
| Exact integer amounts, free orders, caller order | Partial: `test_free_and_large_atom_journeys_preserve_wire_strings_and_empty_routes` | Returned row display, multiple selected IDs in entered order |
| No calculation on selection; once on confirmation | Partial: `test_bundle_eof_decline_and_each_confirmation_launch_counts` | Picker preview/confirmation launch counts, parent arithmetic prohibited |
| Invalid/duplicate IDs without repair | Driver sufficient: `v0.3-rc1/test_commerce.py::test_input_mutation_and_unsupported_refund_selection`; console partial | Literal IDs, duplicates, zero count, exact driver refusal parity |
| Replacement clears selection/refund | Partial: `test_changed_or_malformed_line_selection_cannot_reactivate_old_refund` | Identical/different, count/encoding failure, guided/JSON transitions |
| Quote/payment invalidation | Sufficient for JSON: `test_quote_replacement_identical_failed_and_declined_invalidate_dependents`, `test_legs_and_plan_input_changes_invalidate_plan_and_line_selection` | Reuse these scenarios with picker-created state |
| Missing inputs | Not covered for picker | Absent, failed/replaced quote; quote without plan; refund without selection |
| EOF/decline | Partial: existing guided/bundle EOF tests | Every picker prompt initially and after refund; refund confirmation |
| Transport failure, no retry, fencing | Client sufficient: `test_commerce_calculation_client.py`; console partial: `test_guided_plan_uncertainty_fences_after_successful_quote` | Failure at picker-selected refund, malformed reply and launch failure |
| Conservation/arithmetic | Sufficient: frozen `test_every_refund_subset_conserves_original_route_and_discount_shares` | Reuse unchanged; no new arithmetic tests |

This is builder-authored, source-informed evidence, not independent verification.
