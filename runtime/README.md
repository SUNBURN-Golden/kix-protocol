# KIX production runtime — KTX-R0/R1

Current authority: [masterplan 2.4](../docs/PROTOCOL_MASTERPLAN_V24.md), [ADR-0001](../docs/adr/0001-ktx-authority-commit-recovery.md), and architecture contract v5. The PostgreSQL-only design in 2.3 is historical/comparison scope, not the mandatory path for every future transaction.

## Implemented

- `kix-types`: fixed-width IDs, versioned asset-bound u128 money and headers.
- `kix-bcs1`: actual canonical codec and fixed S07-A golden vector, unchanged.
- `kix-feature-ir` / `kix-feature-semantics`: validated analytical plans and reference semantics, not transaction authority.
- `kix-kernel`: pure deterministic single-shard transitions, bounded records, stable command identity, segment/GA reservations, minimal order/external intent, local fences, UNKNOWN and capture observation model.

## Not implemented

The kernel has no persistence, network, cryptographic input authentication, durable ACK, consensus integration, cluster handoff, deployment, or performance evidence. `replace_owner` and `cancel_scope` are local state-model operations, not distributed protocols. ReturnRequired is not refund execution. The kernel models one positive-priced full-capture operation per order; general commerce remains R3 work.

## Target

Regional transaction cells contain core-local shards with replicated durable commits. Delegated inventory requires a proved exclusive grant and remains disabled. Native chain rights still wait for actual chain finality. PostgreSQL can serve projections/control data or an isolated SQL-authoritative comparison profile; never dual-write the same authority scope.

Adapters authenticate registry/policy/provider/chain facts and submit ordered commands. They perform external I/O outside the kernel. Analytics/GPU/export have separate resource budgets. Native libcudf remains a measured future backend, never a Python dependency in the commerce path.

## Tests

```bash
python scripts/verify_runtime_architecture.py
cargo test --manifest-path runtime/Cargo.toml --workspace --locked
cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings
```

Historical Python/Node/SQLite and shared-Show Move under `reference/` remain regression/fault fixtures only. A Python test runner is not a Python production engine. Preserve its safety guarantees in Rust, not its storage topology.
