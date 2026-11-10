# New evidence and gaps addressed

All eight new methods are in `reference/booking_resale_admission/test_commerce_calculation_console.py`.
Existing coverage and classification were recorded in [coverage-before.md](coverage-before.md) before edits/tests were added.

| New test | Gap addressed |
| --- | --- |
| `test_structure_journey_parity` | All structural controls in a real console/driver journey; independently authored complete final inputs; equality of complete requests, responses and child return codes; explicit repricing/replanning/refund; parent arithmetic/implicit clocks trapped; CALCULATION_ONLY and executionAuthorized=false. |
| `test_structure_positions_order_and_no_launch` | Every valid insertion/removal/source/destination position for sample arrays; both directions and identical moves; duplicate IDs remain positional; ordered leg display; empty arrays; no child launch. |
| `test_structure_precision_and_literal_fields` | Atom/decimal insertion and leg replacement parity above 2^53; exact asset metadata, whitespace, leading zero strings, discount caps/eligibility and duplicate entries preserved without repair. |
| `test_structure_invalidation_history_and_confirmations` | Every new mutation invalidates dependents; leg edits retain quote; identical edits invalidate; complete historical bytes remain; EOF at every new prompt; display preserves active state; reprice/replan retains stored legs and requires a new refund selection; all three submission confirmations independently decline/EOF. |
| `test_structure_malformed_attempts_clear_dependents` | Every mutation with active prior successes fails without restoring selections; retained quote on leg failure; invalid CE1 position/destination grammar; missing drafts; malformed eligibility/caps; noncanonical Unicode; failed decimal entry and buffered conversion discard. |
| `test_structure_cardinality_and_encoding_bounds` | 300 lines/64 discounts/16 legs, append to limit, overflow refusal, move/remove at limit without truncation; final-line/empty-array refusal; real CE1 byte/depth limits on detached candidates. |
| `test_structure_driver_refusals_and_wire_parity` | Exact complete input/reply/exit parity for UNKNOWN_DISCOUNT_LINE, DUPLICATE_LINE, DUPLICATE_INVENTORY, DUPLICATE_DISCOUNT_RULE, MIXED_QUOTE_ASSETS, DUPLICATE_PAYMENT_LEG, PAYMENT_ASSET_MISMATCH, PAYMENT_TOTAL_MISMATCH; one child per confirmation; no correction or retry. |
| `test_structure_output_failure_and_uncertainty_stop` | Failure during draft/leg display, edited preview, proposed request, confirmation prompt and received reply; received evidence retained; malformed transport after quote or leg edits fences, stops and reaps without retry/fallback. |

These are source-informed synthetic interface checks, not clean-room financial verification.
Existing complete commerce-client tests continue to supply transport/hash/CE1/fencing regression coverage. Frozen asset/commerce/driver/canonical tests cover unchanged calculation semantics. No production or external-provider behavior is tested.
