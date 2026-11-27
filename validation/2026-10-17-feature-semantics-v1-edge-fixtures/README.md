# feature-semantics-v1-edge-fixtures

Node: `plan-feature-semantics-v1-edge-fixtures`. Scalar edge fixtures for the pure-Rust helpers in
`runtime/crates/kix-feature-semantics`, named as the authority by `runtime/FEATURE_SEMANTICS_V1.md`.
Issue: none. Depends on: `plan-feature-ir-plan-limit-edge-tests`. Audit floor A2. `astra_gate: None`,
`user_merge: false`. Loop-proposed node, not in `.aiops/program.json`. No ASTRA markers were posted.

This session did not commit, push, open a pull request, create or close an issue, or comment.
There is no implementation commit SHA and no final task head SHA. Local results below are not
exact-head CI. Exact-head CI for the final head is not recorded in the commit (AGENTS §11); it
belongs in the PR closure report.

Observed `origin/main` and branch HEAD at session start: `5eb95eabcac8b71e0c6c92b4fb322a0e4fe5bb45`
(merge of PR #203). `git fetch origin main` left it unchanged (no delta).

## Locks

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

No change to `runtime/crates/kix-feature-semantics/src/lib.rs`, `Cargo.toml`, `runtime/Cargo.lock`,
`runtime/ARCHITECTURE.toml`, `reference/v0.3-rc1/**`, `.aiops/`, `.github/` or `docs/tasks/`.

## New tests (`runtime/crates/kix-feature-semantics/tests/semantics_v1_edges.rs`)

| Test | Gap closed |
|---|---|
| `filter_keeps_table_matches_section_2` | full `Option<bool>` table |
| `nullable_keys_equal_table_covers_all_null_combinations_under_both_policies` | all 2x2 null combinations x both `NullEquality` values (8 rows) |
| `aggregate_empty_policy_is_exhaustive_over_aggregate_kind` | wildcard-free match over `AggregateKind`; a new variant breaks the build |
| `divide_yields_none_for_zero_or_null_operand` | `None` for zero or null on either side over the boundary set |
| `divide_matches_independent_f64_expression_over_boundary_set` | `Some(finite)` equal to `n as f64 / d as f64` for {MIN, -1, 0, 1, MAX} x nonzero denominators |
| `divide_boundary_rows_have_pinned_values` | `MIN/-1`, `MAX/MIN`, `MIN/MAX`, `MIN/1`, `MAX/1`, `1/MAX` exact values |
| `characterize_zero_over_negative_denominator_is_negative_zero` | class B, see below |
| `validate_terminal_f64_rejects_non_finite_values` | NaN of both signs, +inf, -inf |
| `validate_terminal_f64_accepts_finite_extremes_and_zeros` | `f64::MAX`, `f64::MIN`, `MIN_POSITIVE`, a subnormal, +0.0, -0.0 (bit-identical) |
| `category_value_equality_and_hash_ignore_dictionary_position` | equal values collapse in a `HashSet` in three insertion orders; equal values hash equally |
| `category_value_differs_by_vocabulary_id_or_semantic_code` | differing `vocabulary_id` or code is unequal |

## Section-to-test map (AGENTS §7)

Existing inline tests are in `runtime/crates/kix-feature-semantics/src/lib.rs`.

| FEATURE_SEMANTICS_V1 | New tests | Existing tests | Coverage |
|---|---|---|---|
| §2 Filter NULL dropped | `filter_keeps_table_matches_section_2` | `filter_null_is_dropped` | sufficiently |
| §2 Join `nullEquality` | `nullable_keys_equal_table_…` | `null_join_semantics_are_explicit` (3 of 8 rows) | sufficiently for the helper; join execution not covered |
| §2 GroupBy null keys, Sort null order, aggregate IGNORE | none | none (the enums have no functions) | not covered |
| §4 Empty aggregates | `aggregate_empty_policy_is_exhaustive_over_aggregate_kind` | `aggregate_empty_semantics_are_fixed` | sufficiently for the policy table; aggregate execution not covered |
| §4 Integer overflow ERROR, no float money aggregates | none | none (`OverflowPolicy` is an enum only) | not covered |
| §5 `DIVIDE_TO_F64` and finite | the four `divide_*` tests, `characterize_zero_…`, both `validate_terminal_f64_*` tests | `divide_by_zero_and_null_produce_null`, `non_finite_terminal_values_are_rejected` | sufficiently at scalar level |
| §5 MEAN path, F64 key and follow-on prohibitions | none | `kix-feature-ir/tests/schema_bound.rs`: `terminal_mean_can_only_be_followed_by_limits`, `nested_f64_in_either_operand_and_boolean_wrappers_is_rejected`, `source_f64_is_rejected_even_for_limit_only_plan`; `kix-feature-ir/tests/audit_regressions.rs`: `audit_a02_filter_must_reject_nonterminal_f64`, `audit_a03_terminal_divide_must_reject_nested_divide` | partially (validator level); execution not covered |
| §7 Category identity | two `category_value_*` tests | `category_equality_is_semantic_not_dictionary_position` (one equality assert) | partially (decoded scalar identity; no dictionary type exists) |
| §9(3) null/join/group/sort/aggregate edge fixtures | filter, nullable-key and empty-policy tests | none | partially; group, sort and aggregate execution and join execution not covered (no evaluator; belongs to `k-stage7-cpu-analytics-sql-audit`) |
| §9(4) Fast64 registry version | none (cited, not duplicated) | `kix-feature-ir/tests/schema_bound.rs` `fast64_rejects_wrong_asset_version_or_hash_at_export`; `kix-feature-ir/src/lib.rs` `fast64_profile_is_bound_to_asset_and_registry_version` | sufficiently for the identity/version/range predicate; registry authentication (S07-D) not covered |
| §9(5) NaN/Inf rejection | `validate_terminal_f64_rejects_non_finite_values` | `non_finite_terminal_values_are_rejected` | partially; the scalar validator only; adapter/export failure not covered |
| §9(6) dictionary re-encoding | `category_value_equality_and_hash_ignore_dictionary_position` | none | partially; no backend or dictionary fixture |

## AGENTS §8 classification

- **Class A (contract-defined and matching):** Filter NULL dropped; empty-aggregate table; divide by zero or null is NULL; non-finite rejection; category identity by vocabulary and code.
- **Class B (contract undefined), characterization only, no fix, no normalisation chosen:**
  1. *Negative zero.* `divide_i64_to_terminal_f64(Some(0), Some(d))` with `d` = `-1` or `i64::MIN` returns `-0.0` (bits `0x8000000000000000`, sign bit set); with `d` = `1` or `i64::MAX` it returns `+0.0` (bits `0`). `validate_terminal_f64` accepts and returns `-0.0` bit-identically. The contract says only finite plus a versioned tolerance policy.
  2. *i64 to f64 precision.* The conversion is lossy above 2^53. `i64::MAX as f64 == 9223372036854775808.0` (2^63), so `MAX/MIN == -1.0`, `MIN/MAX == -1.0`, `MAX/1 == 9223372036854775808.0` (above `i64::MAX`), and `MIN/-1 == 9223372036854775808.0` (integer `MIN/-1` would overflow; the f64 path does not). The contract is silent on precision.
  3. *Helper scope.* `nullable_keys_equal(false, false, _)` is `true` under both policies: the helper decides only the null component and never compares key values.
- **Class C (explicit violation):** none found; all tests pass on unmodified `src/`.

The pinned rows in `divide_boundary_rows_have_pinned_values` and the negative-zero test intentionally break
if `src/` later changes; that is intended and not a contract assertion.

## Commands actually run

See the final session report for the evidence table; results recorded there are the actual outputs.

## Non-claims

- Scalar helpers only, in-memory. Not a Polars, DuckDB or GPU result.
- Not an authenticated-export or wire-parser result.
- No f64 tolerance policy, zero normalisation or i64-to-f64 precision rule is chosen.
- Group, sort, aggregate and join execution are not covered: no evaluator exists.
- Integer-overflow ERROR, the MEAN path and any Arrow/dictionary type are not covered.
- Release-mode behaviour is untested; `divide_i64_to_terminal_f64` has a `debug_assert!` active only in debug builds.
- Test count is not a completion criterion.

## Remaining uncertainty and follow-ups

- Negative-zero handling and a versioned tolerance policy need a separate explicit decision.
- Execution-level fixtures belong to `k-stage7-cpu-analytics-sql-audit`.
