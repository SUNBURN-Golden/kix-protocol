# KTX-R1 audit fixes

Review base: `d236cfc69e21b88a74caef8879e7ea08008628aa` (PR #10).

## Corrected boundaries

- A contradictory provider/account/event payload now quarantines both named operations and any orders already bound to them. Unbound named operations cannot be attached to a future reservation.
- Reviewed orders cannot authorize external transmission. Valid historical facts remain recordable; they do not silently restore fulfillment authority. Expiry/cancellation still produces ReturnRequired while retaining review.
- Successful expiry checks and repeated observations advance admitted logical time. Immutable reservation outcome replay remains read-only and still needs authenticated/authorized ingress.
- The AI/GPU document now follows source authority plus projection watermarks. Locked CI completion is tracked separately from schema registration.

## Regression evidence

The initial seven new regressions produced **six failures and one pass** on the original kernel. The additional future-binding regression also failed on the intermediate kernel, which still permitted a Held result for the quarantined operation. After the fixes, **all 32 kernel tests pass**. Tests cover both affected orders, repeated conflicts, accepted late facts, expiry/cancellation while reviewed, no partial quarantine mutation at capacity, monotonic time and future binding.

Local toolchain: Rust 1.98.1. Commands:

```sh
cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline
cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings
cargo fmt --manifest-path runtime/Cargo.toml --all -- --check
python scripts/test_runtime_architecture.py
```

This fixes the in-memory R1 contract. It does not implement production adapters, authentication, distributed ownership, quorum commit, snapshots or performance guarantees. The exact published commit's Actions runs provide remote regression evidence; earlier CI is not inherited as proof.
