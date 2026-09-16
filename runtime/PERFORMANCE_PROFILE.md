# KIX runtime performance profile — KTX v5

No measured KTX throughput or floor is claimed. R1 is a pure single-shard transition kernel; it has no durable storage, deployed cells, or performance harness. This document defines R2/R4/R6 acceptance, not completed results. Authority/finality follows [ADR-0001](../docs/adr/0001-ktx-authority-commit-recovery.md).

## 1. Equal-guarantee comparison

Compare the replicated KTX target with an isolated SQL-authoritative PostgreSQL 18 profile on disjoint inventory. Do not serialize both engines in one purchase or run two writers against the same resource. Use the same business invariants, stable command identity, external UNKNOWN semantics, successful ACK meaning, failure domain, stable-storage policy, authentication work, workload and reporting windows.

A three-replica single-region profile must not claim whole-region RPO=0. Majority loss cannot produce new successful writes. RAM/page-cache ACK performance is not durable-commit performance. NativeChainExecution includes required chain finality; delegated contractual completion is reported separately.

Prohibited hot path: Python/Node/SQLite authority, DataFrame mutation, giant mutable JSON, global sequence/balance hot rows, external RPC inside open DB transactions, microservice hops without measured need.

## 2. Metrics and workload

Ceiling = sustained correct durable goodput within latency objectives. Floor = defined low-load, hotspot, burst, background-recovery and provider-delay scenarios, not availability under arbitrary majority failure.

Record scheduled arrival and actual completion with open-loop generation plus user-behavior replay. Report successful reservation/payment/issuance, rejection, queueing and retry separately. Preserve raw histograms and failure times. Do not hide overload by allowing the generator to wait for responses and reduce offered load.

Pin CPU/RAM/NUMA/NIC, kernel/runtime/compiler, dependencies, storage/fsync mode, replica placement, workload distribution, object sizes, batch count/bytes/max wait and raw measurement configuration. Runtime lockfile is required. Dependency pinning does not make a shared hosted CI runner a stable performance machine.

## 3. Mandatory fault/load matrix

| Scenario | Required observation |
|---|---|
| 1–4 seat bundles, aisles, word boundary | no overlap; all-or-none in declared commit unit |
| same command/payload and altered payload | original result vs explicit conflict |
| owner movement with response loss | same command identity; transfer dedupe/intents |
| ACK then leader crash/restart | recovered original result under declared failure model |
| snapshot install/compaction/catchup/torn write | evidence-preserving recovery and bounded foreground impact |
| low load and saturated batching | latency floor as well as durable goodput |
| hot row plus unrelated show/shard | locality of contention and failure impact |
| provider delay, duplicates, late success | UNKNOWN preserved, one economic effect, obligations retained |
| cancellation and authority split/movement | placement-bound barrier and no missed writer |
| refund/reopen and old edge | invalidation and no permanent SOLD negative cache |
| cross-shard coordinator failure | durable decision, no unsafe unilateral abort |
| PG/chain/export prolonged delay | bounded backlog/retained WAL; scoped admission reduction |

A semantic unit test is not an actual process crash, disk corruption, network partition or linearizability-history test. Enable a dedicated controlled performance/fault runner only once the harness exists. Current CI must not fabricate a performance pass.

## 4. Resource budgets

Track cell/shard/provider queue count/bytes/age, active sessions, HOLD count, uncertain external operations, observation lag, outbox age, source log retention, projection lag and recovery I/O. Reserve service for completion/cancel/expiry/reconciliation without permanently starving new work. Limit telemetry cardinality while retaining mandatory economic evidence.

## 5. Canonical bytes, identity and money

KIX-BCS1 signing/hash/snapshot identity is preserved; JSON/CE1 stays compatibility/regression. In-process calls are typed and need not serialize at every function boundary. Compare encoder/decoder/hash CPU, copies, allocations and sizes. Use canonical_bytes_and_hash where appropriate; never change golden bytes/hash for an optimization without an explicit new schema.

IDs remain fixed 128-bit, asset/hash 256-bit, money u128 plus registry identity. Fast64 requires `(asset_id, registry_version)` and `atoms <= executionMaxAtoms(registryVersion) <= i64::MAX`, with registry hash checked. Wide128 analytical arithmetic stays unsupported/fail-closed in Semantics v1. Never truncate out-of-profile input.

## 6. Chain and export

Rust gRPC/checkpoint adapters replace Node subprocess in production. Independent inventory/right/sale/payment objects and sharded nullifier state replace shared-Show fixture topology. Private proof/nullifier authority prerequisites remain synchronous with permission, not analytics.

Exports use source-consistent cuts and projection-applied source watermarks. PostgreSQL MVCC snapshot and LSN remain distinct. A projection LSN is not KTX source finality. Benchmark complete/authenticated export throughput; never remove manifest hashes/row counts/source authentication to improve speed. Cross-shard cuts include coordinator decisions.

## 7. Preserved analytical semantics

FeatureIR is representation; pure-Rust Feature Semantics v1 is the engine-independent reference. Retain null filter/join/group behavior, sort null/stability, aggregate empty/null/overflow, finite terminal-only F64, divide-by-zero NULL, logical decoded category equality and version-bound Fast64. Polars Rust conformance is required on upgrades; native libcudf must pass the same meaning before enablement.

Polars lazy/streaming handles CPU ETL over authenticated Arrow/Parquet. DuckDB handles audit/forensic SQL over verified manifests. Neither query results nor DataFrame mutations create economic truth. Trace discrepancies to source cuts, projection lag, export completeness, mapping and query semantics.

## 8. Native GPU crossover gate

The target remains native libcudf behind the KIX C ABI and Arrow C Device, with long-lived contexts, streams and RMM pools. Python cudf-polars is drafting/conformance/benchmark tooling only, with raise_on_fail/no fallback. It is not a commerce runtime dependency.

GPUCrossoverProfile pins workload/dataset, CPU/RAM, GPU/VRAM, PCIe/NVLink, Polars/RAPIDS/libcudf/cudf-polars/CUDA versions, row counts/bytes, CPU/GPU wall time, host/device transfers, fallback count and allocation/spill. Native work is justified when one workload family wins at three consecutive scales with zero fallback. No global row-count crossover constant.

CPU interchange is Arrow, durable analytical data Parquet, device interchange Arrow C Device. Fixed binary widths, timestamps/timezone, category vocabulary and Wide128 lossless representation remain explicit. Row groups/compression/sort order are workload-specific measurements.

## 9. AI and optimization

Advisory AI runs after commit. Gated inference uses durable pending intent, external feature/inference work and a new validated kernel command. Model output is never authority. Analytics/GPU/backup/recovery resources are budgeted separately.

Only after correctness and fault-history gates pass compare core pinning, NUMA, io_uring, batching/allocation and NIC/DPDK options under the same guarantees. Maximum in-memory loop rate is not end-to-end purchased-right throughput.
