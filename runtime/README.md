# KIX production runtime

`runtime/` is the S07+ production design authority. Historical Python/Node/SQLite and the shared-Show Move code under `reference/` remain regression/fault fixtures only.

## Core production path

- Rust modular monolith + Tokio.
- PostgreSQL 18 typed OLTP authority.
- KIX-BCS1 for canonical signing/hash/snapshot identity.
- Direct Sui gRPC observation/execution boundaries.
- Immutable ShowConfig + independent inventory/right/sale/payment objects + sharded admission state.
- No Python/Node/SQLite/DataFrame engine in the commerce hot path.

## Data / AI path

The analytical plane is columnar but is not transaction authority.

```text
Arrow/Parquet -> KIX Feature IR v1
                  |            |
                  v            v
        Polars Rust CPU    libcudf native GPU
                                |
                         Arrow C Device
```

`cudf-polars` is conformance/benchmark/prototyping tooling only. Production GPU execution is native libcudf through the stable KIX C ABI described in `NATIVE_GPU_EXECUTION.md`.

## crates

- `kix-types` — binary-first KIX IDs, asset/hash identity, registry-bound money, KIX-BCS1 headers/counters.
- `kix-feature-ir` — engine-neutral feature/query plan shared by Polars Rust and libcudf backends.
- `kix-kernel` — S07 deterministic commerce state machine (next).
- `kix-store-postgres` — S07 typed PostgreSQL transactions/OCC/journal/outbox (next).
- `kix-executor`, `kix-sui`, `kix-provider`, `kix-api` — follow-on runtime boundaries.

Production hot path forbids giant mutable JSON state, global sequence/balance hot rows, external RPC inside DB transactions, and microservice hops without measured need.
