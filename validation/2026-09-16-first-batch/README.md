# First batch — v4 conformance and measurement evidence

Base: `c8267d1c2bdbcd732aa46401fe059b92d8ae72a6` (PR #12).
Locked kernel: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
Locked quarantine test: `b607996c83a119c349f1cc90469ac1ba82764e20`.
This is the approved first batch, NOT R2 or integration (a).

## First-review provenance correction

The model author read the kernel source, including reserve rejection precedence.
Representation and execution are separate, but this was not a clean-room model
derived only from contracts. The prior 131,072 comparisons demonstrate agreement,
not which implementation is right. Shared errors may survive. The reference
source and original raw evidence remain unchanged.

A model-free checker now tests five contract predicates against one kernel and
its observed history. See [CONTRACT_INVARIANTS.md](../../docs/contracts/CONTRACT_INVARIANTS.md)
for exact source SHA/blob/clause derivations and limits. No new release transition,
R2 or integration (a) is introduced.

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

The oracle-sensitivity test omits full-capacity quarantine only in the separately represented
reference model. The locked kernel with its existing quarantine behavior must disagree, and a shorter trace
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

## Final baseline CI and supplemental records

Full protocol CI **35062501611** for head
`0394a36a655b86bacb568b055d377d4c4fd91185` ended **completed / success**.
Final update: 2026-09-16T06:24:09Z / 15:24:09 Asia/Seoul. The sibling KTX run
35062501720 also succeeded. These are not the results for a later commit.

- Fixed smoke profile: [PERFORMANCE_BASELINE_V4.md](../../docs/contracts/PERFORMANCE_BASELINE_V4.md).
  The 75% Capacity ratios are measured saturation, not a causal GC comparison.
- M-excluded inventory: [PARTIAL_ANCHOR_COUNTS.md](../../docs/status/PARTIAL_ANCHOR_COUNTS.md).
  16/32 rows, 20 associations, 3 unique anchors; no production label upgrade.
- Unresolved inputs/roles/effort: [FIRST_BATCH_OPEN_INPUTS.md](../../docs/contracts/FIRST_BATCH_OPEN_INPUTS.md).
  Actual human effort unrecorded; estimated completed-equivalent 5~8 and remaining
  5~8 person-days. Provider-response and independent-cut research waits excluded.

The new test emits contract-invariants-summary.json, predicate-sensitivity evidence
and its source blob under the existing KTX artifact directory. First execution
44659fa4d3553dec46d709450249d2764fba8d8d / 35067881678 passed tests and Clippy,
but failed formatting; the failure is retained. Only the new file's formatting
is corrected. New exact-head CI results belong in the PR execution record.
