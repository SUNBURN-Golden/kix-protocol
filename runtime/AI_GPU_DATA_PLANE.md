# KIX AI / GPU data plane

KIX AI/analytics uses a **KIX-owned Feature IR + Arrow/Parquet interchange**. Production transaction authority remains Rust kernel + PostgreSQL; production GPU execution is native `libcudf`, not Python `cudf-polars`.

## 1. Data flow

```text
PostgreSQL committed facts
        |
        v
Arrow RecordBatch / Parquet
        |
        v
KIX Feature IR v1
        |
   +----+------------------+
   |                       |
   v                       v
Polars Rust             libcudf C++
CPU lazy/streaming      native GPU + RMM
   |                       |
   +----------+------------+
              v
      versioned features
              |
          AI / model
              |
     InferenceRecord/Proposal
              |
              v
        Rust kernel gate
```

`cudf-polars` remains a third execution path only for conformance, benchmarks, and rapid prototyping. It is not a production dependency.

## 2. Why KIX owns Feature IR

Making Polars Lazy the canonical IR would couple KIX GPU execution to the Python-facing GPU planner. Instead, `kix-feature-ir` defines the logical operations once. Backends compile the same IR to:

- Polars Rust lazy/streaming on CPU;
- libcudf native C++/CUDA on GPU;
- DuckDB SQL only where useful for validation/reconciliation;
- cudf-polars in conformance tests when the operator set overlaps.

The initial IR covers typed scans/sources, filters, projections, joins, group-by/aggregates, sort and limit. Window/time-series operators are added only with explicit versioning and differential tests.

## 3. Native GPU boundary

Rust talks to a long-lived native GPU context through `native_gpu/include/kix_gpu.h`. The boundary is a narrow C ABI. Data crosses as Arrow C Device structures, not Python objects.

libcudf currently supports direct ArrowDeviceArray interop and accepts CUDA stream and RMM memory-resource parameters. KIX therefore keeps GPU data on device when possible, reuses a persistent RMM pool, and avoids Python interpreter/GIL/orchestration dependencies.

GPU work runs on bounded dedicated executors, not inside PostgreSQL transactions and not as unbounded work on Tokio scheduler threads.

## 4. Polars role

Polars remains strategically important:

- default CPU feature/ETL backend;
- fast lazy/streaming transformations over Arrow/Parquet;
- development reference for feature semantics;
- one side of differential CPU↔GPU correctness tests.

This is deliberately different from making Polars the OLTP state machine or the canonical feature-plan syntax.

## 5. DuckDB role

DuckDB remains the embedded SQL/reconciliation engine over Arrow/Parquet:

- forensic and ad-hoc SQL;
- provider observation ↔ journal ↔ order cross-checks;
- selective Parquet scans;
- validation of feature outputs.

DuckDB is never Order/Payment authority.

## 6. cuDF roles

### Production

Native `libcudf` via the KIX C ABI. This is the no-Python path.

### Conformance / research

`cudf-polars` executes equivalent supported plans for comparison and rapid experimentation. Silent CPU fallback is not accepted as evidence of GPU performance; benchmark runs must report fallback/operator coverage.

### Extreme optimization

If the C ABI wrapper becomes measurable overhead, KIX may link a thinner C++ bridge or specialize hot feature kernels while preserving Feature IR semantics and Arrow device interchange.

## 7. Schema and point-in-time correctness

Feature datasets are versioned Arrow schemas and durable Parquet datasets. IDs use fixed-width binary where possible; economic amounts keep atoms + asset/registry identity and never become floats.

`FeatureSnapshot` binds at least:

```text
featureSnapshotId
featureSchemaVersion
featurePlanVersion/planDigest
asOfObservationCursor
asOfCommitPosition
sourceDatasetVersions
policyVersionIds
assetRegistryVersionIds
featureHash
```

Training and backtests must not join future observations into past feature rows.

## 8. Model output

Model/agent output is non-authoritative evidence:

```text
InferenceRecord
- inferenceId
- modelId/version/digest
- featureSnapshotId/hash
- purpose
- output/score/reason codes
- executionAuthorized = false
```

Any refund/retry/hold/action proposal re-enters the Rust kernel and current authority/reservation checks.

## 9. Required future GPU CI

A dedicated NVIDIA runner must pin CUDA/RAPIDS versions and verify:

1. Feature IR -> Polars Rust result.
2. Feature IR -> native libcudf result.
3. Supported subset -> cudf-polars result.
4. integer/fixed-width columns exactly match.
5. unsupported libcudf operators fail closed or explicitly route to the CPU backend outside OLTP.
6. ArrowDeviceArray lifetime/sync-event handling is valid.
7. RMM pool/stream reuse avoids per-request allocator setup.
8. host-device transfer and spill metrics are captured.
