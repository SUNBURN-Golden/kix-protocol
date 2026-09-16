# KIX Runtime — 구현 범위와 검증 입구

**현행 승인·진행 정본은 [docs/DEVELOPMENT_PLAN.md](../docs/DEVELOPMENT_PLAN.md)입니다.** 모델 1은 [권위 결정서](../docs/decisions/AUTHORITY_MODEL_1.md), 현재 작업 기준은 [commit·태그 표](../docs/status/BASELINES.md)를 따릅니다. V24는 역사적 계획이며 자동 R2 진행을 승인하지 않습니다. ADR-0001의 안전 관계와 기존 architecture v5 설정은 실제 구현 범위를 설명하는 근거이지 금지된 저장·복제 구현의 착수 허가가 아닙니다.

## Implemented

- `kix-types`: fixed-width IDs, versioned asset-bound u128 money and headers.
- `kix-bcs1`: actual canonical codec and fixed S07-A golden vector.
- `kix-feature-ir` / `kix-feature-semantics`: analytical-plan verification and reference semantics, not transaction authority.
- `kix-kernel`: locked v4 deterministic in-memory transitions, bounded records, stable command identity, seat/GA reservations, minimal order, UNKNOWN, capture, promised observation slots and quarantine.
- Separate tests/examples: source-informed differential model, contract-derived single-kernel predicates and a memory-only performance apparatus. Their success is not durable-operation or production-performance proof.

## Not implemented or not authorized

The kernel has no persistence, network, cryptographic input authentication, durable ACK, consensus, distributed fencing/membership/state transfer or chain client. `replace_owner` and `cancel_scope` are local state operations. ReturnRequired is not an executed refund. Slots and evidence have no completed lifecycle reclamation implementation.

Model 1 assigns original inventory/right authority to the chain, but the actual exclusive grant, revocation and independent verification are not implemented. General commerce, production rights and storage selection remain open. Historical replicated-cell or PostgreSQL diagrams are not a decision to start R2. **R2 and integration (a) remain prohibited.**

PR #11's v1 wire/local journal exists only as a preserved, unmerged experiment: [location and cold-build results](../docs/status/PR11_PRESERVATION.md). Do not add its replay evidence to this v4 runtime's implementation status.

## Locks and tests

Do not alter the kernel or `tests/quarantine_capacity.rs`, including comments/formatting. Exact blobs and existing CI assertion path: [LOCK_ENFORCEMENT.md](../docs/status/LOCK_ENFORCEMENT.md).

```bash
python scripts/verify_runtime_architecture.py
cargo test --manifest-path runtime/Cargo.toml --workspace --locked
cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings
```

These are existing verification commands, not authorization to implement new transitions. Historical Python/Node/SQLite and shared-Show Move under `reference/` remain regression/fault fixtures. The source-informed comparison model is not a clean-room specification; see [CONTRACT_INVARIANTS.md](../docs/contracts/CONTRACT_INVARIANTS.md).

KTX is a historical code label, not a defined acronym. The bulk rename to KIX Runtime remains deferred to separately approved stage-3 schema/SDK work; existing identifiers, source and configuration are unchanged.
