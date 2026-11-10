# Coverage mapped before adding tests

Node: plan-local-cart-structure-editor. Task input: user-supplied node specification and read-only design plan; no docs/tasks node document or issue exists.

All tests below are in reference/booking_resale_admission/test_commerce_calculation_console.py unless qualified.

| Requirement | Classification | Existing evidence and gap |
| --- | --- | --- |
| Real subprocess editing, repricing/replanning/refund and complete wire parity | Partial | test_edit_journey_complete_input_parity; test_guided_split_refund_journey_and_file_parity. Structural operations and leg replacement absent. |
| No launch on edits, every calculation confirmed | Partial | test_each_submission_decline_and_eof_send_nothing_further; test_edit_invalidation_history_eof_and_launch_counts. New controls absent. |
| Invalidation including failures; immutable historical bytes | Partial | test_edit_failures_clear_draft_and_dependents; test_guided_replacement_invalidates_plan_refund_and_selection. Structural and leg edit failures absent. |
| Exact amounts, ordered arrays, positional editing, bounds | Partial | test_edit_exact_inputs_and_decimal_parity; test_bundle_literal_strings_caps_and_array_order; test_guided_integer_and_encoding_failures_never_publish_candidate. Insert/remove/move and structural cardinality absent. |
| Literal inputs and unchanged driver refusals | Partial | test_edit_driver_rejections_and_uncertainty; test_guided_driver_refusals_are_visible_without_correction_or_retry. Structural dangling references, duplicate inventory/rules and edited legs absent. |
| EOF, malformed input, output failure, uncertainty | Partial | test_edit_invalidation_history_eof_and_launch_counts; test_output_failure_retains_received_success_and_stops. New prompt paths and previews absent. |
| Client fencing, retained evidence and no retries | Sufficient | test_commerce_calculation_client.py complete transport suite; test_transport_failure_stops_console_without_retry_or_fallback. Reuse; add integration after edits only. |
| Schema/calculation semantics and CALCULATION_ONLY | Sufficient for unchanged driver | reference/v0.3-rc1/test_assets.py, test_commerce.py, test_commerce_driver.py, test_canonical_encoding.py. New editor journey flags require integration assertions. |
| Usage and regression verification | Partial | Existing draft/decimal guide and evidence. New controls/transcripts need documentation and actual local verification. |

Source-informed interface coverage; not independent financial verification.
