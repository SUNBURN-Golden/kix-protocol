# Coverage map recorded before implementation

Task input: user-supplied node `plan-local-commerce-draft-editor` and design plan;
no task issue or docs/tasks document exists for this node.
Tests below live in reference/booking_resale_admission unless qualified otherwise.

| Requirement | Existing coverage | Gap addressed by new editor tests |
| --- | --- | --- |
| Complete subprocess quote/edit/recalculate/plan/refund journey | Partial: test_commerce_calculation_console.py::test_bundle_journey_file_parity and test_picker_journey_json_parity | Compare edited full exchanges to complete caller-authored inputs; run real console child |
| Ordered display, positional replacement, explicit metadata | Not covered | Zero-based positions including duplicate IDs; unchanged fields/order; explicit version/expiry |
| Invalidate before input, including failed/abandoned edits | Partial: test_bundle_replacement_clears_input_quote_and_dependents, test_decimal_replacement_invalidates_dependents | Every edit action, EOF at each prompt, invalid positions/structure/encoding, retained historical bytes, retained legs and cleared selection |
| Editing sends no request; explicit confirmation only | Partial: test_each_submission_decline_and_eof_send_nothing_further | Launch counts during display/edit/failure/EOF/decline; no parent calculation/implicit clock |
| Exact strings, complete assets, discount order | Partial: test_decimal_journey_atom_parity, test_bundle_literal_strings_caps_and_array_order | Atom/decimal edit parity above 2^53, null/string caps, literal eligibility, complete metadata |
| Driver refusals and uncertainty | Client transport coverage sufficient: test_commerce_calculation_client.py; editor integration partial | Duplicate IDs, stale eligibility, mixed assets, excessive discounts; malformed reply after edit fences once |
| Calculation-only boundaries | Partial: existing journey tests | CALCULATION_ONLY and executionAuthorized=false on edited journey |

Source-informed interface regression tests, not independent financial verification.
Existing frozen asset parser tests remain the arithmetic evidence; no duplicate
arithmetic model is introduced. Product policy remains UNDETERMINED — Astra/User.

## Added coverage

All new methods are in `test_commerce_calculation_console.py`:

| Method | Documented gap covered |
| --- | --- |
| `test_edit_journey_complete_input_parity` | Four real driver exchanges, separate complete JSON request parity, real console subprocess, parent arithmetic/clock prohibited, calculation-only result fences |
| `test_edit_positions_metadata_and_ordered_display` | First/last positions, duplicate IDs selected by position, original ordering, complete metadata, explicit unchanged/changed/zero/negative version and expiry without inferred bounds |
| `test_edit_invalidation_history_eof_and_launch_counts` | Every editor and EOF prompt, identical replacement invalidation, original exchange byte equality, retained legs, no selection revival, no extra launch on editing/decline, display preserves active state |
| `test_edit_failures_clear_draft_and_dependents` | Invalid positions/tokens, metadata/decimal/encoding failures including buffered conversion discarded on encoding failure, malformed structures, missing prerequisites and empty discounts; no stale draft/state revival |
| `test_edit_exact_inputs_and_decimal_parity` | Exact atom/decimal parity above 2^53 with full explicit asset metadata; literal atom/discount strings, eligibility arrays and caps remain unchanged |
| `test_edit_driver_rejections_and_uncertainty` | Complete-input parity for duplicate IDs, stale eligibility, mixed assets and excessive discounts; malformed reply after edits fences permanently with one attempt |

These tests verify the console/client interface and reuse the frozen calculator;
they do not establish independent arithmetic correctness or execution authority.
