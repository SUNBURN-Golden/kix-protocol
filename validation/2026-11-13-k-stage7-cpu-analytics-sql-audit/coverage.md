# Existing coverage mapped before adding audit tests (AGENTS §7)

| Requirement | Prior classification | Existing evidence | Gap addressed here |
|---|---|---|---|
| Authenticated export | partial | `authenticated_export/test_pure.py` FullExportTests, IntegrityTests, RollbackTests, AuditTraceTests; `test_export.py` ExportPostgresTests | consumer admission, replacement after verify, actual engine consumption |
| Nulls | partial | `kix-feature-semantics/src/lib.rs`: filter_null_is_dropped, null_join_semantics_are_explicit, aggregate_empty_semantics_are_fixed | dataset filters, joins, group keys, aggregates |
| Ordering | partial | `kix-feature-ir/tests/schema_bound.rs` and `validator_matrix.rs` validate policies | ASC/DESC, FIRST/LAST and stable duplicate ordering in engines |
| Joins | partial | same schema validator tests; scalar nullable helper only checks nullness | actual non-null equality, duplicate-preserving Inner/Left/Semi/Anti |
| Overflow | not covered in engines | Feature Semantics §4 contract; IR validates Error policy | I64/U64 arithmetic and SUM checked execution, debug/release |
| Money identity/range/version | sufficient for scalar conversion | `kix-feature-ir/tests/schema_bound.rs`: fast64_rejects_wrong_asset_version_or_hash_at_export, fast64_identity_mismatch_precedes_amount_range_for_each_identity_field, fast64_checked_range_is_inclusive_at_claim_and_capped_at_i64_max, fast64_checked_claim_is_not_inherited_across_registry_versions | reuse unchanged; no approved Fast64 execution profile |
| Money lossless export | partial | `test_pure.py` TypeMappingTests | engine binary roundtrip including >2^53 and u128 max; unsupported arithmetic rejection |
| IR schema versions | sufficient for validator, partial at engines | `schema_bound.rs`, `validator_matrix.rs`, export version checks | admission and adapter rejection before execution |
| Comparator correctness | not covered | none | mutations to values, duplicates, ordering, errors |

The new harness is source-informed, not clean-room independence. Historical
feature-semantics maps and checkers remain unchanged.

New executable coverage (test-only, not a production compiler):

- `analytics_audit.test_admission.AdmissionTests`: full/keyed trace + replay,
  incremental/partial/missing/extra/tampered/key negatives, signed version
  rejection, replacement after verification, symlink rejection.
- `kix-analytics-audit/tests/conformance.rs`: `null_semantics`,
  `ordering_semantics`, `join_semantics`, `overflow_semantics`, `export_binding`,
  `money_roundtrip_and_version_rejection`, `comparator_sensitivity`,
  `engine_versions`. See the case IDs in results.json for each contract predicate.
- `analytics_audit.test_source.LocalSourceTests`: mandatory, non-skipping
  PostgreSQL source run of the full Rust/Polars/DuckDB suite.

General F64 tolerance and cancellation-sensitive aggregate overflow order are
not covered or defined here. GroupBy emission order is compared as a multiset;
no implicit ordering guarantee is added.

Resumed-builder inspection found two remaining partial predicates in the draft:
arithmetic NULL propagation (Class B characterization, no explicit v1 rule) and
ERROR preservation when a later Limit(0) would
otherwise discard every result. The added `nullable-*` and
`overflow-before-limit` cases exercise these gaps in the same conformance suite.

Report assembly gap addressed in `analytics_audit.test_report`: a partial PASS
file set, substituted engine version, enabled extension download flag, or missing
production flag cannot be promoted to a complete acceptance report. The final
aggregation also validates the actual full matrices from every recorded run.
