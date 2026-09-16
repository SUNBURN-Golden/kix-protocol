# First batch — v4 conformance and measurement evidence

Base: `c8267d1c2bdbcd732aa46401fe059b92d8ae72a6` (PR #12).
Locked kernel: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
Locked quarantine test: `b607996c83a119c349f1cc90469ac1ba82764e20`.
This is the approved first batch, NOT R2 or integration (a).

## E-4 scope

The reference uses individual seat owners and linear histories, not Kernel calls,
bitmaps or the kernel's BTreeMap state. Shared public request/result types only
encode the comparison boundary. Per command it compares the reply, every known
order, remaining inventory, event/slot/quarantine counts and retained conflicts.
Private bitmap layout and cluster durability are not directly verified.

Four inventory/budget configurations, seeds 1..256, and 128 actions per sequence
cover current v4 only. Generation uses explicit deterministic seeds; failures are
replayed from scratch and deletion-shrunk. Shrinking does not minimize numeric
parameters or configurations. It does not invent a GC/slot-release transition.

The oracle-sensitivity test omits full-capacity quarantine only in the independent
reference model. The unchanged correct kernel must disagree, and a shorter trace
must remain failing. This is not a production-code mutation campaign.

## First execution (not the final submitted head)

Initial code commit: `7f480fa4e3f18db83605a59cab4ae9b2e405478f`.
KTX run `35061116217`: compilation/tests and Clippy passed; formatting failed on
new files. Do not label that overall run successful. Artifact `10432557145`,
SHA-256 `5c0d2290a6d672a5866eee095e8e2601fcd7073ac9d4adaa322e97623d3efca9`.

Raw e4-summary: 1024 sequences / 131072 compared transitions / zero mismatches.
Action counts (Reserve, Send, Expire, Capture, Owner, Cancel):
55753, 20884, 15946, 30522, 7325, 642.
Oracle-side missing-quarantine control was detected; 6 steps shrank to 3.
The command-limit-2 sequence actually returned Held, Rejected(Unavailable),
Ok(true) expiry with remaining=1, and Err(Capacity) for the new command.
This reproduces the existing limit; it does not fix retention.

All new sources were identified by Git blob in first-batch-source-blobs.txt.
The test emitted rustfmt diagnostic copies into the artifact without changing
repository source; those copies are used to correct only the new files. Existing
CI still checks committed formatting. No locked file/Cargo/CI/lint configuration
was formatted or edited. Later head results must be reported separately.

## Performance smoke

The same artifact contains four 512-call CSV/JSON pairs and 16 scheduled calls.
Uniform: 128 new Held + 384 Capacity.
Hot-seat: 1 Held + 127 business rejections + 384 Capacity.
Retry: 1 Held + 511 replays, no Capacity.
Conflict growth: 127 retained conflicts + 385 Capacity.
All are memory-only debug apparatus checks, not durable throughput or release
latency claims. No kernel reset occurs within a workload.

## First-batch completion is not claimed

The lifecycle document is a draft with provider terminality, retention windows,
independent cutoff evidence and authority actors still open. The performance
contract has no approved product TPS/p99 target. This first PR provides an initial
E-4 model, evidence apparatus and documents, not all work estimated at 10–16 days.

No kernel, locked test, index, wire, local journal, Cargo/lockfile, workflow,
production lint config, existing branch cleanup, tag, merge or deployment change.
