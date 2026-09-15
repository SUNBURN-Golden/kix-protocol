# KTX-R2-A local journal and replay

This is an executable **single-host storage test harness** for the registered KTX schemas. It is not the production replicated backend, a new consensus algorithm, or an implementation of ADR-0001's quorum ACK. `LocalReceipt` deliberately names only the local synchronization boundary. The production and delegated-execution gates remain disabled.

## Boundary

Creation validates and persists one immutable registered GenesisV1 containing scope, initial owner/business epoch, exact inventory segments/capacity, record limits and semantics version. It uses create-new, an exclusive advisory file lock, file sync and parent-directory sync. Opening an existing file requires the same lock, validates every frame, reconstructs the kernel and synchronizes again before exposing recovered state. A complete unacknowledged tail can be adopted on recovery; a torn tail is an error.

Each append contains a registered CommandV1. Length, sequence, previous frame hash and bytes are covered by a domain-separated SHA-256 checksum. Lengths are checked before bounded frame allocation. The file is synchronized **before** applying the command. The pinned deterministic kernel reconstructs the original reservation outcome, rejection, inventory, order, provider binding, captured facts, quarantine and execution intent from genesis plus the ordered log. No entire-state clone or per-command snapshot is used. Registered CommandResult bytes are available for receipts/evidence; results are reconstructed from the log rather than independently committed in a second file.

An I/O error poisons the handle. It cannot provide state or process more commands until reopened and recovered. Capacity and time-admission errors occur before append. Configured log-entry and total-byte limits stop admission rather than evicting history. Logged inputs use nondecreasing admitted time; caller authentication and real-time admissibility remain ingress responsibilities.

## File format v1

- File magic: eight bytes `KTXLOG1\0`.
- Genesis frame: sequence 0, all-zero previous hash, canonical GenesisV1 payload.
- Command frames: consecutive u64 sequences starting at 1 and canonical CommandV1 payloads.
- Frame: payload length u32 LE; sequence u64 LE; previous hash [u8;32]; payload bytes; checksum [u8;32].
- Checksum: SHA-256 of `KTX-LOCAL-FRAME-v1\0` followed by every preceding byte of that frame, including its length and sequence.

Checksums detect accidental corruption/reordering; they do not authenticate an operator or detect replacement by a completely valid earlier prefix. No repair/truncation policy is guessed. A reported complete-prefix rollback requires an independent committed checkpoint/quorum, which is R2-B work.

## What this does not prove

Process-kill tests exercise process death and response loss, not electrical power loss, truthful device caches or regional durability. Locks coordinate cooperating processes on the same file; they are not distributed fencing and do not stop a privileged writer from ignoring the lock or replacing paths. Use a trusted local filesystem and a private test directory.

There is no replicated log, network membership, leader election, quorum-loss handling, state snapshot/compaction, operator-independent checkpoint, state-version migration or real provider execution. Control/observation actions are ordered internal driver inputs, not a complete idempotent public command API. Reservation identity and provider-event/operation replay follow the kernel contract.

R2-B must integrate a mature consensus/storage backend, committed-index/hard-state recovery, snapshot installation, old-writer and membership histories, and the actual stable-storage quorum ACK. This harness is a reproducible comparison/fault-test baseline, not a reason to omit those requirements. No throughput/floor superiority is claimed.
