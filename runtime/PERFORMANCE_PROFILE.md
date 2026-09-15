# KIX runtime performance profile

KIX optimizes end-to-end throughput/latency without weakening economic correctness. Transaction authority, audit, feature execution and GPU acceleration are separate roles.

## 1. OLTP core

Production baseline: Rust + Tokio + PostgreSQL 18.x, prepared/binary direct DB access, narrow typed tables, aggregate-local OCC/CAS.

Forbidden on the commerce hot path:

- Python/Node/SQLite authority;
- DataFrame engines;
- giant mutable JSON/JSONB state;
- global sequence/balance hot rows;
- external RPC while a DB transaction is open;
- microservice hops without measured scaling need.

## 2. On-sale burst performance

Average TPS is not the only target. Benchmark the opening burst explicitly.

Track:

- waiting-room queue latency;
- admitted requests/sec;
- PostgreSQL pool utilization/saturation;
- retry amplification;
- reservation success/failure by inventory mode;
- GA shard imbalance/reissue count;
- preserved queue-position violations = 0.

Reserved seating uses one-seat contention units. GA uses fixed-capacity shards and waiting-room shard routing; chain/inventory capacity remains authority.

## 3. Canonical bytes

Production signing/hash/snapshot identity is KIX-BCS1. JSON/CE1 is compatibility/regression only. Typed in-process calls do not serialize on every function boundary.

Benchmarks: encode/decode/hash throughput, heap allocation count, encoded size, BCS vs legacy JSON.

## 4. IDs and money

- KIX ID: fixed 128-bit.
- Asset/hash identity: fixed 256-bit.
- protocol money: u128 atoms + asset/registry context.
- Fast64 profile key: `(asset_id, registry_version)`.
- Fast64 export invariant: `atoms <= executionMaxAtoms(registryVersion) <= i64::MAX`.
- Wide128 feature arithmetic: unsupported/fail closed in Semantics v1.
- overflow/profile mismatch: reject, never truncate.

## 5. Sui

Rust direct gRPC + streaming checkpoint watcher. Production object topology is immutable ShowConfig, mode-specific inventory, independent right/sale/payment objects and sharded admission/nullifier state. No show-wide mutable hot object/fence.

## 6. Authenticated export

PostgreSQL is economic authority. DuckDB/Polars/libcudf consume authenticated evidence exports.

Full export:
- REPEATABLE READ MVCC snapshot;
- exported/imported snapshot for multi-reader export;
- snapshot identity is not WAL LSN.

Incremental export:
- WAL LSN or equivalent durable cursor;
- explicit cursor boundary semantics;
- stable event identity for replay/dedupe.

Benchmark export completeness and throughput, but never trade away row-count/hash/manifest verification for speed.

## 7. KIX Feature IR + Semantics v1

`kix-feature-ir` defines representation. `kix-feature-semantics` defines engine-independent behavior. Upstream defaults are not semantic authority.

Semantic fixture areas include:

- null filter/join/group behavior;
- sort null order and stability;
- aggregate empty/null/overflow behavior;
- terminal-only finite F64;
- divide-by-zero -> NULL;
- category comparison by decoded logical value;
- registry-version-bound Fast64.

Pure-Rust semantics is the reference. Polars Rust must pass conformance on every version upgrade. Native libcudf must pass the same suite before production enablement.

## 8. Polars Rust CPU backend

Polars Rust lazy/streaming is the default CPU feature/ETL executor over authenticated Arrow/Parquet datasets.

Use for recurring typed ETL and feature generation. Never use it as Order/Payment/Refund mutation authority or economic reconciliation authority.

## 9. DuckDB audit backend

DuckDB executes audit/forensic/reconciliation SQL over **verified ExportManifestV1 datasets**.

```text
PostgreSQL = truth
DuckDB = audit executor over evidence
```

A DuckDB mismatch triggers investigation of export provenance, type mapping and query semantics; it never creates a second economic truth.

## 10. Native libcudf GPU target

The future production GPU backend is native C++ `libcudf` behind `native_gpu/include/kix_gpu.h`. It is not an S07 dependency.

Execution target:

```text
KIX Feature IR + Semantics
 -> Rust safe wrapper
 -> stable KIX C ABI
 -> long-lived libcudf context
 -> CUDA streams + persistent RMM pool
 -> ArrowDeviceArray output
```

Native implementation requires a pinned NVIDIA/CUDA/RAPIDS CI lane and semantics conformance before enablement.

## 11. cudf-polars role

`cudf-polars` is not production infrastructure. Use it as:

- semantics drafting aid by studying its Polars->libcudf translations;
- conformance participant where supported;
- benchmark/crossover proxy;
- rapid prototype/offline research tool.

Use `raise_on_fail` or equivalent no-fallback mode for GPU benchmark work. Silent CPU fallback is never counted as GPU performance.

## 12. GPUCrossoverProfile

There is no global row-count threshold.

Each profile records at least:

```text
featurePlanId / workload family
dataset profile
CPU model / RAM
GPU model / VRAM
PCIe or NVLink topology
Polars version
RAPIDS/libcudf/cudf-polars version
CUDA version
row counts / bytes per scale
wall-clock CPU and GPU
host->device and device->host bytes
fallback count
memory spill/allocation metrics
```

A native GPU implementation is justified only after the same workload family shows GPU wins at **three consecutive scales with fallback count = 0** on a pinned profile. The measured crossover is evidence, not a permanent architecture constant.

## 13. Arrow / Parquet

- CPU interchange: Arrow;
- device interchange target: Arrow C Device;
- durable analytics/training: Parquet;
- UUID: fixed binary(16);
- asset/digest: fixed binary(32);
- Fast64 money: i64 atoms + asset/registry-version columns;
- Wide128: lossless representation only;
- category/dictionary physical encoding is not semantic identity.

Dataset partitioning, row groups, compression and sort order are benchmarked per workload.

## 14. AI realtime

AI never executes inside an open DB transaction. Advisory mode runs after commit. Gated mode commits durable pending/intent state, performs feature/inference work, then enters a new Rust command. Model outputs remain non-authoritative.

## 15. benchmark suite

OLTP: create-order, observation ingest, concurrent refund reservation, journal/outbox append, SQL round trips, allocations.

On-sale: waiting-room latency, admitted RPS, DB pool saturation, retry amplification, reserved-seat contention, GA shard routing/reissue fairness.

Chain: independent sale throughput, shard contention, checkpoint lag.

Export/audit: full-snapshot throughput/consistency, incremental CDC completeness, manifest verification, DuckDB query reproducibility.

Feature: pure-Rust reference vs Polars conformance.

GPU: cudf-polars crossover proxy first; later native libcudf, Arrow device transfer, RMM pool/spill, stream behavior and conformance.

No performance claim is made without pinned hardware, dataset/query profile and reproducible benchmark configuration.
