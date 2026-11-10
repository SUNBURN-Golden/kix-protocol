# Coverage mapped before implementation/interface tests

Task input: user-supplied node plan-local-commerce-decimal-entry; no docs/tasks document or issue exists. Source planner run 1794268560. Branch agent/kix-plan-local-commerce-decimal-entry. Initial HEAD and locally observed origin/main: e5b7927bca2ec78a0a6618d4ac3d1d5611a0b95d (no local delta). Fetch prohibited by supervisor; remote freshness unverified.

| Requirement | Existing coverage | Gap to address |
| --- | --- | --- |
| Exact arithmetic, precision 0..38, metadata and overflow | Sufficient: reference/v0.3-rc1/test_assets.py: test_precision_is_exact_from_zero_to_38_places, test_decimal_parser_rejects_float_exponent_rounding_and_noncanonical_text, test_asset_metadata_rejects_ambiguous_identifiers_and_invalid_limits, test_asset_wire_requires_string_limit_and_no_implicit_schema_fields | Decimal console interface absent; reuse parser unchanged |
| Real quote, split plan, line refund; exact request/result/hash parity | Partial: test_commerce_calculation_console.py: test_bundle_journey_file_parity, test_guided_split_refund_journey_and_file_parity, test_picker_journey_json_parity | Compare decimal/atom combinations using real subprocess exchanges |
| Zero, fractional assets, >2^53, declared precision limits | Parser sufficient; console partial: test_free_and_large_atom_journeys_preserve_wire_strings_and_empty_routes | Exercise decimal interface at precision 0, 2, 6, 18, 38 and declared limits |
| Exponent, whitespace, excess precision, malformed metadata, overflow | Parser sufficient; console absent for decimals | Interface refusals must launch nothing and publish no partial previews/candidates |
| Mixed assets and aggregate overflow | Partial: test_commerce.py test_mixed_assets_and_aggregate_overflow_are_rejected; bundle/guided driver refusal tests | Decimal conversion preserves driver-owned validation and explicit submission |
| EOF and decline submit nothing | Partial: test_bundle_eof_decline_and_each_confirmation_launch_counts; guided EOF tests | Decimal prompt truncation and each submission confirmation |
| Edit invalidation | Partial: test_bundle_replacement_clears_input_quote_and_dependents, test_guided_replacement_invalidates_plan_refund_and_selection | Atom/decimal transitions, identical/changed/malformed/interrupted replacements |
| Preview ordering, unchanged discounts, no in-process commerce | Partial: test_bundle_journey_file_parity, test_bundle_literal_strings_caps_and_array_order | Conversion records before composed candidate and consent, never in requests/hashes |
| Documentation, architecture, preservation | Existing checkers and workflow definitions inspected | Run applicable local checks, compare before/after protected manifests; review/CI deferred to supervisor |
