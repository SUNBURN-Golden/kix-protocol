# KIX native GPU execution — no Python in the production GPU path

The production GPU path does **not** depend on Python, Polars Python, or `cudf-polars`.

Current upstream reality is useful but not the KIX production boundary: Polars GPU acceleration is exposed to Python Lazy API users through RAPIDS `cudf-polars`. KIX instead uses the lower-level `libcudf` C++ API directly and keeps `cudf-polars` only for conformance, benchmarking, and rapid experiments.

## Architecture

```text
KIX committed facts / Parquet / Arrow
              |
              v
       KIX Feature IR v1
              |
       +------+-------+
       |              |
       v              v
Polars Rust CPU   native GPU backend
 lazy/streaming        |
                       v
             Rust -> stable KIX C ABI
                       |
                       v
                    libcudf
                 CUDA + RMM
                       |
                       v
               ArrowDeviceArray
```

A feature definition is therefore **not** a Polars AST. `kix-feature-ir` is engine-neutral. The same plan is compiled to Polars Rust on CPU and libcudf on GPU.

## Native boundary

`native_gpu/include/kix_gpu.h` is the production ABI. The implementation is a C++/CUDA library linked behind a narrow C ABI. Rust owns the safe wrapper; `unsafe` is confined to that FFI crate when implemented.

Input/output uses Apache Arrow C Device Interface structures. Same-process GPU buffers stay on device whenever the involved Arrow/libcudf types permit zero-copy or view-based interop. CUDA synchronization is represented by Arrow device synchronization semantics rather than by copying data back to the host.

The GPU context is persistent and holds:

- pinned GPU device / NUMA placement;
- RMM device memory resource/pool;
- pinned-host spill pool where benchmarked useful;
- CUDA stream pool;
- reusable compiled/validated feature-plan metadata.

Do not create/destroy CUDA contexts, allocators, or Python interpreters per request.

## Tokio boundary

GPU execution is not run as arbitrary work on Tokio core scheduler threads. Runtime integration uses a bounded GPU executor with one long-lived worker/context per GPU (or benchmarked equivalent). Requests enter through bounded channels/queues and return completion handles without holding PostgreSQL transactions open.

## cudf-polars role

`cudf-polars` remains valuable, but only as:

1. a conformance oracle for supported feature plans;
2. a benchmark target against native libcudf;
3. a rapid research path for new dataframe operations;
4. an optional offline notebook/tooling environment.

It is **not** required to start KIX commerce, to perform production GPU inference preparation, or to execute production feature plans.

For every GPU-supported Feature IR operation, KIX should maintain differential fixtures:

```text
Polars Rust CPU result
        ==
native libcudf result
        ==
cudf-polars result (when supported)
```

Bitwise equality is required for integer/identity fields. Floating-point model features require an explicitly versioned tolerance policy; economic amounts never use floating point.

## Why not make Polars Lazy the canonical IR?

Because that would make the production GPU path dependent on the availability and semantics of the Python-facing GPU planner. Polars remains an excellent CPU execution backend, but KIX owns the logical feature contract so either backend can evolve independently.

## S07/S08 requirements

Before AI production use:

- implement KIX-BCS1 encoding/golden vectors for `FeaturePlanV1`;
- implement the Polars Rust compiler for Feature IR;
- implement the libcudf native bridge behind `kix_gpu.h`;
- add a GPU CI lane on pinned NVIDIA/CUDA/RAPIDS versions;
- benchmark Arrow host/device transfer, RMM pools, streams, batch sizes, and spill;
- fail closed on unsupported native GPU operators rather than silently executing them in Python;
- allow explicit CPU Polars fallback outside the OLTP transaction when policy permits.
