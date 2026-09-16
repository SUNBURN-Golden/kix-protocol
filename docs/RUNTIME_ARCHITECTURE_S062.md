> **현행 계획 폐기 표시 — 이 문서는 역사 자료이며 현재 작업 승인이 아닙니다.**
> 이 문서의 다음 단계·즉시 실행·자동 진행 지시는 현행 승인으로 사용하지 않습니다.
> 특히 자동 R2 진행은 현재 금지이며, (a) 통합은 보류, 위생 일괄 실행도 금지입니다.
> **현행 정본: `docs/DEVELOPMENT_PLAN.md` — [현재 승인·금지 범위](DEVELOPMENT_PLAN.md).**
> 본문은 S06.2 당시 실행 구조·후속 순서의 기록으로 보존합니다. 과거 검증·실패·안전 조건을 삭제하거나 무효라고 판정하는 표시가 아닙니다.
> 표시 전 원문: commit `d5b9f2d67b5532fa35464c8557e88f70be300888`, Git blob `faf41fca3ac0a4ed838ae269816dbc53510cbbd9`. 아래 원문 바이트는 변경하지 않았습니다.

# S06.2 — Greenfield production architecture reset before S07

작성 기준: 2026-09-15. 기존 Python/SQLite/CE1/shared-Show 구현을 production 설계권한으로 유지하지 않는다. 과거 코드는 regression/fault fixture다.

## 1. Production topology

```text
Client
  -> Rust KIX modular monolith / Tokio
       -> deterministic Rust kernel
       -> PostgreSQL 18 typed OLTP
       -> bounded Executor -> Sui gRPC / PG / Bank / FX
       -> observation stream -> Rust reducer

committed facts
  -> Arrow / Parquet
  -> KIX Feature IR v1
       -> Polars Rust lazy/streaming CPU
       -> native libcudf C++/CUDA GPU
  -> DuckDB SQL for ad-hoc/reconciliation
  -> AI/ML -> non-authoritative proposal -> Rust kernel gate
```

Production GPU execution has **no Python dependency**. Python `cudf-polars` is conformance/benchmark/prototyping tooling only.

## 2. Rust-first OLTP

Production state machines are implemented directly in Rust. PostgreSQL uses typed relations for Order, PaymentObservation, Allocation, Obligation, RefundReservation, ExecutionIntent/Observation, Journal and Outbox.

Global sequence/balance hot rows, giant mutable JSON, external RPC inside DB transactions and DataFrame transaction authority are forbidden.

External effects follow:

```text
validate/reserve
-> ExecutionIntent + outbox
-> COMMIT
-> external call/query
-> raw Observation
-> deterministic Rust apply
-> journal/state
```

## 3. KIX-BCS1

Signing/hash/snapshot identity uses KIX-BCS1: versioned, domain-separated BCS application envelopes. JSON and Protobuf may be edge/transport representations but are not signing identity. CE1 is legacy compatibility/regression only.

## 4. IDs / money / registry

- KIX generated IDs: fixed 128-bit.
- AssetId/hash: fixed 256-bit.
- amount: u128 atoms + authenticated asset/registry context.
- PostgreSQL BIGINT lane only for registry-approved profiles.
- PolicyVersion/AssetRegistryVersion immutable and authenticated before Order creation.

## 5. Sui production object model

```text
Immutable ShowConfig
  +-- InventoryCell / InventoryShard[N]
  +-- independent owned Right
  +-- per-sale SaleIntent
  |     +-- PaymentEvidence
  |     +-- EXECUTED xor CANCELLED
  +-- AdmissionEpochConfig
        +-- AdmissionShard[N]
```

Independent sales should not mutate the same show-wide object. Show-wide payment/nullifier vectors and show-wide compensation fences are fixture-only.

## 6. Engine-neutral Feature IR

Feature/ETL semantics are owned by KIX, not by Polars Python or cuDF APIs.

`kix-feature-ir` defines FeaturePlanV1 and a versioned operator set. The same logical plan is compiled to:

```text
CPU -> Polars Rust lazy/streaming
GPU -> native libcudf
SQL validation/investigation -> DuckDB where appropriate
```

This is the key to removing Python from the production GPU path without giving up Polars as the high-performance CPU engine.

## 7. Native GPU execution

Rust integrates a long-lived C++/CUDA backend through a stable KIX C ABI. The ABI receives KIX-BCS1 Feature IR plus Arrow C Device inputs and returns ArrowDeviceArray outputs.

`libcudf` owns GPU columnar execution. Persistent RMM memory resources and CUDA streams are reused. Same-process device buffers remain on GPU when supported. No Python interpreter is created per worker or request.

GPU calls are dispatched to bounded dedicated GPU executors; PostgreSQL transactions are already committed before GPU work begins.

Detailed contract: [`../runtime/NATIVE_GPU_EXECUTION.md`](../runtime/NATIVE_GPU_EXECUTION.md).

## 8. Polars / DuckDB / cudf-polars roles

**Polars Rust**: primary CPU feature/ETL backend.

**DuckDB**: Parquet/Arrow SQL, reconciliation, forensic/ad-hoc analysis, backend validation.

**cudf-polars**: conformance/benchmark/prototyping only. It is not required for production GPU execution and Python outages cannot affect commerce or native GPU features.

## 9. Arrow / Parquet

S07 typed facts must project losslessly to versioned Arrow schemas. Parquet is the durable analytical/training format. IDs and digests use fixed binary widths where possible; money remains atoms + asset/registry fields. Event time and commit/observation ordering are retained for point-in-time feature reconstruction.

## 10. AI boundary

Model outputs are `InferenceRecord`/`DecisionProposal` with `executionAuthorized=false`. Any refund/retry/hold/action must re-enter Rust authority/current-state/reservation checks. GPU/AI outages do not make the core commerce path unavailable.

## 11. S07 gates

S07 must implement:

1. KIX-BCS1 Rust codec + golden vectors.
2. Rust kernel + PostgreSQL Order/Observation/Allocation/Obligation/RefundReservation.
3. authenticated Asset/Policy versions.
4. duplicate observation one-economic-effect semantics.
5. atomic concurrent refund reservation.
6. durable execution intent/outbox/recovery.
7. Arrow export schema/cursors.
8. `kix-feature-ir` remains engine-neutral and no Python dependency enters production runtime.
9. production chain APIs do not depend on legacy shared Show.
10. OLTP and columnar/GPU benchmark baselines are recorded separately.

## 12. Later GPU implementation gate

Before AI/GPU production use, add a pinned NVIDIA/CUDA/RAPIDS CI lane implementing `kix_gpu.h`, native libcudf backend, Polars Rust backend compiler, Arrow C Device lifetime/synchronization tests, and differential outputs against cudf-polars where supported.

Historical storage-loss root cause, remote durability, real PG credentials, production ZK ceremony/key migration and independent checkpoint verification remain separately unresolved.
