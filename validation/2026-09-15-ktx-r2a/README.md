# KTX-R2-A: registered wire and local restart evidence

Base: R1 audit-fix commit `bf460b1f7724c5ad7d561b19a64959383fcec6a8`.

## Implemented

- `kix-ktx-wire`: one sealed registry declaration generates the accepted types and the registration table. Genesis, command and result IDs are 1/1/1, 1/2/1 and 1/3/1. Fixed golden bytes/hash are independent of the existing S07-A fixture; the old fixture is unchanged.
- `kix-journal-local`: immutable genesis, bounded append frames, sequence/previous-hash/checksum checks, local exclusive file locking, file and creation-directory synchronization, fsync-before-apply, poisoned-handle refusal, complete-log deterministic reconstruction.
- Architecture v6 keeps production/delegation/quorum ACK disabled and distinguishes the local replay harness. Its checker requires the actual registry and recovery test files; the KTX workflow executes both new crates using the committed lockfile.

## Verification

Rust 1.98.1, committed dependency lock, fmt and warnings-denied clippy. The workspace contains **105 passing runtime tests and one passing compile-fail doctest** after this change. Two subprocess helper tests are ignored as standalone tests and explicitly launched by their parent recovery tests. The architecture checker suite has seven methods and now includes 19 contract mutations plus missing registry/recovery evidence checks.

The local journal contributes 13 filesystem/process integration tests and one Linux I/O-error unit test. The latter uses a test-only descriptor pointing at `/dev/full` to trigger an actual failed write without filling storage; the handle refuses subsequent queries and execution. There is no production failure-injection API.

Recovery tests cover full Kernel equality, original reservation result, rejected command replay, UNKNOWN, late capture after resale, quarantined operations, local owner change, process lock exclusion, process death after local synchronization, every partial cut inside the last frame, checksum/reordering/oversize rejection, record/byte caps and ordered time. Test subprocesses use isolated temporary directories and are reaped by their parent.

```sh
cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline
cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings
cargo fmt --manifest-path runtime/Cargo.toml --all -- --check
python scripts/test_runtime_architecture.py
```

## Review and limits

Independent review found a reopen boundary: complete bytes left in page cache after a writer dies must not be exposed as recovered local state before synchronization. `open()` now validates/replays, syncs the file and parent directory, and only then returns the handle.

SIGKILL is not power failure. Advisory same-file locking is not distributed fencing. Checksums are not authentication and cannot detect replacement by a complete valid earlier prefix. A complete but unacknowledged command can survive and be adopted. A torn tail is not silently removed.

No real PG/bank/Sui call occurs. No Raft cluster, state snapshot, compaction, membership or quorum ACK is implemented; no throughput superiority is claimed. These are R2-B requirements, not completed by this baseline. Registry governance and Rust/Move production conformance also remain separate.

The exact published head and its KTX/protocol Actions runs are recorded on the draft PR. Old CI is not promoted to new-head evidence.
