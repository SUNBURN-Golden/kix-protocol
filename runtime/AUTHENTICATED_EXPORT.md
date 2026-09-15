# KIX authenticated export contract — architecture v5

Authority is scope-assigned under [ADR-0001](../docs/adr/0001-ktx-authority-commit-recovery.md), not unconditionally PostgreSQL. This is a contract, not an implemented exporter. DuckDB/Polars/libcudf never become economic writers.

## 1. Source cut and projection point

A KTX source identifies scope, authority-placement version, shard id, source log/semantics epoch and committed position. A PostgreSQL projection independently records the source position already applied plus its own MVCC snapshot/LSN. Projection LSN alone does not prove a source KTX cut, completeness or global atomicity.

A multi-shard full export needs a consistent cut including cross-shard coordinator decisions and participant effects. Arbitrary shard cursor sets cannot certify it. Until this protocol exists, do not label a multi-shard export globally atomic.

The isolated SQL-authoritative comparison profile may use a PostgreSQL MVCC snapshot as its source. It must be explicitly identified and must not write the same resource as KTX.

## 2. Retained PostgreSQL snapshot/CDC contract

SQL snapshots and WAL LSNs are different. Full projection exports use REPEATABLE READ or stronger and one MVCC snapshot. Multi-reader exports use imported/exported snapshots while the snapshot remains valid. A WAL location is provenance, not a substitute for snapshot identity.

Incremental projections state start/end cursor inclusive/exclusive rules and deduplicate stable source event identities. Record both source progression and projection cursor progression. Gaps, unresolved coordinator decisions and lag must be visible.

## 3. ExportManifestV1 extension requirements

Before a production manifest wire schema is registered, its source contract must include:

```text
exportId / exportMode / executionProfile
sourceClusterId / authorityScope / authorityPlacementVersion
sourceShardCuts[] / consistentCutProofOrDecisionBoundary
sourceSchemaVersion / kernelSemanticsVersions / exportSchemaVersion
projectionAppliedSourceWatermarks[]
fullSnapshot: isolationLevel / snapshotId / fingerprint / xmin / xmax
incremental: cursorKind / startCursor / endCursor / boundarySemantics
provenance: observedLsnAtStart / observedLsnAtEnd / createdAt
content: rowCount / fileCount / perFileHash[] / manifestHash / partitionManifest
```

If a prior registered wire schema exists, extend using a new version; never silently reinterpret the same canonical identity. FULL_SNAPSHOT requires snapshot/cut metadata and INCREMENTAL requires cursor metadata. Do not merge them into one ambiguous commitPosition.

## 4. Integrity and authentication

Hash every file. Bind schema, file list/hash, row counts and source/projection provenance into the manifest. A hash alone proves neither authorized authorship nor latest state. Consumers need a trusted signing/root/registry boundary and anti-rollback policy. Partial/missing uploads or invalid manifests fail closed.

## 5. Type mapping and analysis

KIX ID = fixed binary(16); asset/hash = fixed binary(32). Fast64 carries asset id + registry version + registry hash and validates the execution profile. Wide128 is lossless; no truncation. Timestamp units/timezone and category vocabulary versions are explicit. Pin PostgreSQL-to-Arrow mapping versions without turning JSON blobs into the economic authority.

An audit result traces query → exportId → manifest → exact source cut and projection watermarks → exact files/hashes → schema and semantics versions. If DuckDB differs from a projection/source, investigate boundaries, completeness, mapping and semantics; do not promote a query result to truth.
