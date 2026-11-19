# CPU analytics / SQL semantics audit

This is a local audit harness, not a production analytics backend or an economic
writer. All execution/production flags in `analytics_audit/__init__.py` are false.
Authority is `runtime/FEATURE_SEMANTICS_V1.md`, then pure Rust reference semantics;
Polars and DuckDB agreement alone is insufficient. The harness is source-informed.

Use the owner-provisioned free offline bundle, C++ compiler, Rust 1.98.1 and local
PostgreSQL 17.11. No engine downloads, extensions, external data connections or
public endpoints are used. Missing engines fail the explicit acceptance run.

```bash
export RUSTUP_TOOLCHAIN=1.98.1 CARGO_BUILD_JOBS=1 CXXFLAGS=-g0 POLARS_MAX_THREADS=2
python3 -m unittest authenticated_export.test_pure analytics_audit.test_admission analytics_audit.test_report
cargo test --manifest-path runtime/Cargo.toml -p kix-analytics-audit --features engines --test conformance --offline --locked
cargo test --manifest-path runtime/Cargo.toml -p kix-analytics-audit --features engines --test conformance --release --offline --locked
python3 -m unittest analytics_audit.test_source
```

To retain query/plan/expected/Rust/Polars/DuckDB observations, set
`KIX_AUDIT_RESULTS` to a scratch directory. Each case writes a separate JSON file
for deterministic aggregation without concurrent append races. The PostgreSQL
suite sets `KIX_AUDIT_SOURCE=postgres` and repeats the complete engine suite.
`python3 -m analytics_audit.report --results <debug-directory> --results
<release-directory> --results <postgres-directory> --output <report.json>`
assembles the observations and rejects incomplete matrices, failed cases or
incorrect engine metadata.

Default workspace CI omits the optional `engines` feature and reports an explicit
ignored-test reason; it cannot certify this local engine acceptance. No CI file
is changed. The feature-gated dependencies use the owner's exact Polars/DuckDB
versions. Polars adds `round_series` for the U64 multiplication guard's integer
floor division; it resolves offline, as permitted by the bundle decision.
DuckDB uses the exact `bundled` feature.

`prepare_export.admit` copies into a private directory without following symlinks,
then requires FULL_SNAPSHOT, signature, versions, all file hashes and row counts,
rollback sequence and a keyed trace. Loading rechecks file hashes inside that
private copy. No engine receives a mutable export path. The public fixture HMAC
key is reused from the exporter tests. It supplies no production authentication.

The harness catalog (`kix-local-export-types/1`, local binding v1) enumerates
verified table/column names lexically and assigns dataset IDs `[tableIndex+1;16]`
and global ColumnIds `tableIndex*100+columnIndex+1`. This is a harness-local
binding, not a registered schema. `int` maps to U64, epoch milliseconds to I64,
bool to Bool, vocabularies to Category with decoded vocabulary name/version/value,
and remaining lossless fields to Bytes. Opaque UTF-8 identifiers and canonical
u128 decimal strings stay UTF-8 bytes; fixed binary identifiers decode checked
hex with their existing 16/32-byte widths. No identifier is invented or widened.
Timestamps retain their epoch-ms unit; nested occurred-time text/offset remains
verbatim. The frozen verified descriptor is authoritative; query-supplied catalogs
are never accepted. Both engines require `ValidatedFeaturePlan`.

Only the audited IR subset is compiled: integer comparisons, arithmetic with
ERROR overflow, project, filter with NULL dropped, Inner/Left/Semi/Anti joins with
explicit null equality, group keys INCLUDE/EXCLUDE, COUNT(*)/COUNT(column),
SUM/MIN/MAX/MEAN, stable sorting with direction/null placement, and limit.
Other expressions fail closed. F64 means use exactly representable fixture
results only; general tolerance and normalization remain UNDETERMINED, owned by
the User through Astra. Fast64 adoption also remains UNDETERMINED. Wide128
arithmetic and narrowing fail before either compiler. Money roundtrips preserve
canonical decimal text and validate with Rust u128, never float arithmetic.

Polars uses Int128 intermediates with strict conversion back to the declared
integer width. U64 multiplication uses an engine expression division guard to
avoid overflowing even its intermediate. SUM uses a widened intermediate with a
strict result conversion and explicit NULL-on-empty. DuckDB uses checked typed
integer operators and casts widened SUM back to the declared width. Stages are
materialized independently so optimization cannot suppress an earlier ERROR.
Unordered results use duplicate-preserving multisets; ordered rows compare exactly.
The comparator has deliberate value/duplicate/null/overflow mutations.

Synthetic boundary datasets explicitly characterize NULLs and integer extremes.
The exported-data cases consume every table/column, use a legitimate left join
to obtain NULLs, and trace back to authenticated files and the exact source cut.
Monotone overflow fixtures avoid the undefined cancellation/intermediate-order
question; no aggregate ordering policy is invented.
Nullable arithmetic is separately labeled Class B characterization: the harness
and pinned engines propagate NULL, but v1 has no explicit arithmetic propagation
rule. This observation does not adopt a new feature semantics policy.

See [the validation report](../validation/2026-11-13-k-stage7-cpu-analytics-sql-audit/README.md)
for prerequisite evidence, coverage, actual commands, discrepancies and limitations.
No production durability, replication, multi-shard consistency, incremental
catch-up, economic writes, Fast64 permission, GPU execution or performance target
is tested or claimed. A2 non-author review and exact-head CI remain supervisor gates.
