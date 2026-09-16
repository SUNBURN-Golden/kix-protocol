# R1 v4 observation-slot and quarantine acceptance evidence

Documentation correction: 2026-09-16. Scope: document alignment only; no kernel,
wire, journal, test, dependency, workflow or architecture-code change.

## Published implementation baseline

- PR: [#12](https://github.com/BeautifulMind-JT/kix-protocol/pull/12).
- Implementation commit: `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631`.
- Implementation tree: `24b925955ae17942ab25b68b1e5a9111d6983501`.
- PR test merge: `4584c9ad2a8c886acc3cd0b1e021a5802e6424f3`; same tree.
- Kernel semantics: **4**, not 2.

| File | Full Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `runtime/crates/kix-kernel/tests/observation_slots.rs` | `9dd1413f060a420b3a97896b9451c82574f56d08` |
| `runtime/crates/kix-kernel/tests/transitions.rs` | `ae5fd6aee210007b2f1ca7f96809c76348aadae4` |

The first two files remain locked. A later documentation-only head is not a new
kernel version. Its CI status must be reported against that head separately.

## Current v4 behavior

Before the first successful `mark_payment_unknown`, the kernel reserves one
first-capture slot by complete provider/account/operation identity. UNKNOWN
retries reuse it. Stored events, retained conflicts and reserved slots share the
observation budget; unrelated observations and new conflicts cannot spend an
operation's promised slot. A supported first bound capture converts its slot
into retained evidence. This is not lifecycle reclamation: the total budget used
does not decrease simply because reserved becomes stored.

**A new conflicting event at full evidence capacity quarantines the bound
operations it names and advances ordered time, even when returning
`Err(KernelError::Capacity)`.** New evidence and unbound identities are not
retained in that case. Do not interpret every `Err` as a rolled-back state
transition. The explicit quarantine set contains bound operations only; future
binding of an unbound operation is blocked only by retained conflict evidence.
There is no scope-wide overflow latch and no mass review of unrelated orders.

Fresh unbound observations still return `UnknownOperation` without storage, or
`Capacity` when the budget gate takes precedence. Rejected evidence is not a
provider-receipt ACK. Durable inbox, source authentication, terminal failure/void
slot release, review resolution and history reclamation remain unimplemented.

## Verification at the published implementation commit

| Run | Actual head SHA | Final state |
|---|---|---|
| [KTX kernel verification 34957674101](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/34957674101) | `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631` | completed / success |
| [KIX protocol verification 34957674135](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/34957674135) | `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631` | completed / success |

The full protocol run reached its final state at 2026-09-15 10:37:23 UTC
(19:37:23 Asia/Seoul). It is no longer in progress.

The preserved KTX CI log reports **51 kernel tests**: 32 transition tests,
11 observation-slot tests and 8 quarantine-capacity tests. The implementation
submission separately reports **101 workspace tests** and a clean-target rerun
of the 8 quarantine tests. Do not call 51 the workspace count, add the rerun to
the unique-test count, or treat that local report as a new run in this
2026-09-16 documentation correction. The implementation submission's 20,000-input
isolation experiment is not a TPS benchmark and was not rerun for this correction.

The KTX job passed its architecture/dependency checks, locked tests,
warnings-denied Clippy and workspace formatting. Its artifact is
`10391369595`, ZIP SHA-256
`b863c7a2b41d34a1a9655112c81739962b45f240dacae8011764bd8dc2a6d9b8`.
It contains the tested commit, source SHA-256 values, dependency tree and raw test
log. The full protocol CI includes historical Python/SDK/Move/circuit, storage,
public Sui, actual Sui with mock PG/bank, ZK artifact/compensated-proof rejection,
and private Sui checks. It does not establish real-money operation, quorum
persistence, independent state-model conformance or production performance.

## Historical baseline and v2 records — not current acceptance evidence

The former version of this README is preserved byte-for-byte at
[`history/baseline_v2_384c935010a3.md`](history/baseline_v2_384c935010a3.md).
Its full Git blob is `384c935010a33c160ccdb26b568ebc7454777f09`.
It records baseline PR #10 `bf460b1f7724c5ad7d561b19a64959383fcec6a8`
and the intermediate v2 experiment, including the original raw outputs and the
93-test workspace report. Those historical statements are not v4 behavior or
v4 acceptance results. In particular, "without quarantine" at full capacity
and "SEMANTICS_VERSION is now 2" are historical, superseded descriptions.

No historical logs were edited to look like v4 output. The current correction
reclassifies the records; it does not claim to rerun the historical experiments.

## PR #11 and the R2 hold

PR #11 at `55a3df4968f5684bb4cb9e3c9781ab5f00165235` is an existing, separate
semantics-v1 registered-wire/local-journal experiment. It is not included in this
branch. Its successful replay tests do not prove v4 slot/quarantine recovery.
Preserving the experiment does not authorize R2 continuation or integration.
No rebase, main merge, tag, kernel change or R2 implementation is part of this
correction. Basic v4 lifecycle work and independent E-4 remain open.
