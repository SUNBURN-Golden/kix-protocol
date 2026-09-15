# KIX 개발계획 2.3 — Greenfield production protocol

작성일: 2026-09-15. 과거 검증/사고 기록은 보존하지만 Python/SQLite/CE1/shared-Show를 production 제약으로 두지 않는다. Production 설계권한은 Rust runtime, KIX-BCS1, typed PostgreSQL, mode-specific Sui inventory topology와 이 계획이다.

## 1. 목표

고성능 권리·주문·결제·정산 프로토콜을 Rust-first로 구현한다. correctness, replay/unknown-outcome 안전성, 감사 가능성을 유지하면서 transaction path와 AI/data path를 각각 가장 적합한 엔진에 배치한다.

## 2. 전체 권위 구조

```text
Client
 -> Waiting Room / Admission Control
 -> Rust KIX / Tokio modular monolith
     -> Rust kernel
     -> PostgreSQL 18 OLTP  ===== economic authority
     -> Executor -> Sui gRPC / PG / Bank / FX
     -> observations -> Rust reducer

PostgreSQL
 -> authenticated full snapshot / incremental CDC export
 -> ExportManifestV1 + Arrow/Parquet
      -> DuckDB audit/forensic
      -> KIX Feature Semantics v1
           -> pure-Rust reference semantics
           -> Polars Rust CPU
           -> native libcudf GPU (later)
      -> AI/ML -> proposal -> Rust kernel gate
```

Python/Node/SQLite rc1은 historical regression/fault fixture다.

## 3. Canonical contract

Production signing/hash/snapshot identity는 KIX-BCS1을 사용한다: versioned/domain-separated BCS envelope, fixed-width identity where possible, u128 money semantics. CE1은 compatibility/regression only다. S07-A에서 Rust codec과 golden vectors를 구현하고 필요한 경우 Rust↔Move equality를 검증한다.

## 4. OLTP와 돈

PostgreSQL 18 typed narrow tables, direct prepared/binary access와 aggregate-local OCC/CAS를 사용한다.

Core objects:

```text
AssetRegistryVersion / Asset
PolicyVersion / QuoteSnapshot
Order / OrderLine
PaymentIntent / PaymentObservation / PaymentAllocation
IssuanceOutcome
Obligation
RefundReservation / RefundExecution
ExecutionIntent / ExecutionObservation
JournalEntry / Outbox
```

금지: global sequence/balance hot row, giant mutable JSON authority, DataFrame mutation authority, external call을 포함한 open DB transaction.

Protocol money는 u128 atoms다. Feature/SQL fast lane은 자산이 아니라 `(asset_id, registry_version)`별 execution profile에 묶는다.

```text
Fast64 allowed iff
atoms <= executionMaxAtoms(registryVersion) <= i64::MAX
```

Wide128은 lossless export만 허용하고 v1 feature arithmetic은 fail closed 한다.

## 5. Sui inventory topology

Inventory mode를 지금 분리한다.

### ReservedSeating

- seat 하나가 하나의 contention cell/owned reservation unit가 되도록 설계.
- 여러 인기 좌석을 일반 mutable shard에 묶지 않는다.

### GeneralAdmissionSharded

- fixed-capacity shard 여러 개.
- `sum(initialShardCapacity) == immutableTotalCapacity`.
- waiting room이 GA shard routing을 담당하지만 chain capacity가 authority다.
- shard가 실제로 full이면 새 token은 **동일 queue position을 보존하고 shard만 교체**한다.

Shared Show fixture는 production에 이식하지 않는다. Immutable ShowConfig + independent Right + per-sale SaleIntent + PaymentEvidence + sharded admission/nullifier state를 사용한다. Per-sale `EXECUTED xor CANCELLED`가 show-wide compensation fence를 대체한다.

## 6. Feature semantics / Data / AI

KIX owns:

- `KIX Feature IR v1` — 표현
- `KIX Feature Semantics v1` — 의미론
- pure-Rust scalar/reference semantics — upstream-independent reference

CPU backend는 Polars Rust lazy/streaming이다. GPU production target은 native libcudf지만 S07 dependency가 아니다. cudf-polars는 semantics drafting aid, conformance participant, benchmark/crossover proxy다.

Semantic v1 핵심:

- Filter NULL predicate -> drop.
- Join null equality explicit.
- GroupBy null-key policy explicit.
- Sort null order/stability explicit.
- integer overflow -> error.
- `COUNT(empty)=0`; `SUM/MIN/MAX/MEAN(empty/all-null)=NULL`.
- F64는 terminal-only. 생성 경로는 `MEAN` 또는 `DIVIDE_TO_F64`만.
- divide numerator/denominator NULL 또는 divisor 0 -> NULL.
- NaN/Inf는 bug/fail closed.
- F64는 join/group/sort/identity key로 금지.
- dictionary/category conformance는 physical index가 아니라 decoded logical value로 비교.

AI/model output은 경제적 authority가 아니며 Rust kernel gate를 다시 통과해야 한다.

## 7. Authenticated export와 audit

PostgreSQL이 경제적 정본이다. DuckDB는 authenticated export에 대한 audit/forensic engine이다.

### Full export

- REPEATABLE READ MVCC snapshot 기준.
- multi-reader이면 exported/imported snapshot.
- snapshot identity와 WAL LSN을 같은 필드로 뭉개지 않는다.

### Incremental export

- WAL LSN 또는 동등 durable cursor 기준.
- stable event identity로 retry/dedupe.

`ExportManifestV1`에는 snapshot/cursor provenance, source/export schema version, row count, file count, per-file hash, manifest hash가 있어야 한다. Partial export는 fail closed 한다.

## 8. Stages

### S06.2 — architecture gate

- Rust-first production boundary.
- KIX-BCS1 architecture.
- ReservedSeating / GeneralAdmissionSharded topology contract.
- waiting-room admission + GA shard routing + queue-position-preserving reissue contract.
- KIX Feature IR v1 + Feature Semantics v1 + pure-Rust semantics primitives.
- PostgreSQL authority / authenticated export / DuckDB audit hierarchy.
- Polars Rust CPU / native libcudf future GPU roles.
- CI fail-closed architecture guard.
- legacy regression suite green.

### S07-A — KIX-BCS1 codec

- Rust encoder/decoder/hash.
- domain/schema registry.
- golden vectors.
- malformed/version/domain mutation rejection.

### S07-B — Order / Payment vertical slice

- authenticated AssetRegistryVersion / PolicyVersion.
- Order/OrderLine/QuoteSnapshot.
- PaymentIntent/PaymentObservation/PaymentAllocation.
- client command idempotency.
- duplicate/late/conflicting observations.
- waiting-room/admission boundary contract for burst entry.
- Postgres connection-pool/admission-control baseline.

### S07-C — Obligation / Refund / crash-concurrency

- IssuanceOutcome / Obligation.
- atomic RefundReservation.
- ExecutionIntent/outbox/executor/Observation.
- concurrent reservation contention.
- crash after reservation/commit.
- response-loss/restart/exactly-one economic effect.

### S07-D — Authenticated export + CPU semantics

- ExportManifestV1.
- REPEATABLE READ full export.
- LSN/cursor incremental export.
- Arrow/Parquet mapping rules.
- pure-Rust semantics fixture suite.
- Polars Rust conformance suite.
- DuckDB audit queries over verified exports.

### S08 — Production Sui Rights / Sale

- immutable ShowConfig.
- ReservedSeating seat-cell topology.
- GeneralAdmission fixed-capacity shards.
- waiting-room shard assignment token binding.
- queue-position-preserving shard reissue.
- independent Right.
- per-sale SaleIntent + terminal fence.
- independent PaymentEvidence.
- first paid issuance + repeated resale.
- concurrency/burst benchmark and Rust↔Move KIX-BCS1 commitments.

### S09 — Admission / privacy scale

- admission/nullifier deterministic sharding.
- root epoch/history strategy.
- liveness improvement for unrelated activity.
- production ZK setup/key migration plan.
- admission throughput benchmark.

### S10 — Native AI/GPU operations

- expand KIX Feature Semantics reference evaluator.
- implement Feature IR -> Polars Rust compiler for production feature workloads.
- run cudf-polars `raise_on_fail` crossover experiments on pinned workload/hardware/version profiles.
- native libcudf implementation only after `GPUCrossoverProfile` gate is met.
- `kix_gpu.h` bridge + pinned NVIDIA/CUDA/RAPIDS CI lane.
- Arrow C Device lifetime/sync-event tests.
- RMM pool/stream/spill benchmarks.
- native libcudf conformance against KIX semantics.
- FeatureSnapshot/model registry.
- AgentGrant / ActionPermit / DecisionRecord.

Native GPU enable gate is not one global row-count constant. For a pinned workload family/hardware/version profile, GPU must beat CPU at three consecutive scales with zero fallback before production-native work is justified.

### S11+ — Financial/FX/scale-out

FXQuote/FXExecution, FinanceAgreement/ClaimAllocation, measured PostgreSQL sharding, remote evidence durability and independent chain verification.

## 9. Unresolved independent work

Historical working-directory loss root cause, whole-host/remote durability, real PG/bank credentials/contracts, production ZK ceremony and independent checkpoint verification remain unresolved until separately proven.

## 10. Performance evaluation

- On-sale: queue latency, admitted RPS, retry amplification, DB pool saturation, reservation success.
- OLTP: p50/p95/p99, throughput, contention, SQL round trips, allocations.
- BCS: encode/decode/hash/size.
- Sui: reserved-seat contention, GA shard routing, parallel independent sales/admission.
- Export: snapshot consistency, CDC completeness, Arrow/Parquet throughput and manifest verification.
- Semantics: pure-Rust reference vs Polars; later native libcudf/cudf-polars where supported.
- GPU crossover: workload/hardware/version-specific `GPUCrossoverProfile`, not one global threshold.

No engine is selected by branding alone. DataFrames are not used to implement transaction-state authority.
