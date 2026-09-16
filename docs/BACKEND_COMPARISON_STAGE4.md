# Stage 4 backend comparison — retry behavior at storage capacity

Added: 2026-09-16. Document-only comparison item requested during branch hygiene.
This supplements **stage 4: 실행·저장 기반 선택** in the proposal
`KIX_DEVELOPMENT_PLAN_20260915.md` (§5 and §9). That proposal is not a previously
published GitHub masterplan. This focused item does not adopt a backend, lift the
R2 hold, merge PR #11, or change any kernel/wire/journal code.

## Observed implementation order, not a new execution result

Source: PR #11, commit `55a3df4968f5684bb4cb9e3c9781ab5f00165235`,
`runtime/crates/kix-journal-local/src/lib.rs`, full Git blob
`40d904318b58d1ccfd2e86e77e6b290856ec95a7`.

`LocalJournal::execute()` checks the poisoned handle, admitted time, encoding,
next sequence and max_entries/max_bytes before appending, syncing and applying
the command to the kernel. Therefore an unchanged, already completed Reserve
retry can hit the journal capacity gate before the kernel's immutable result
lookup. Before capacity is reached, that retry still appends and syncs a new
frame. The following is a source-derived scenario, not a newly run transcript:

1. With max_entries=1 and sufficient byte capacity, the first Reserve is logged,
   synced and returns Held.
2. The response is lost and the same command is retried.
3. Proposed sequence 2 exceeds the journal limit: JournalError::Capacity is
   returned before kernel result lookup. Do not report this as seat unavailability.

The local test harness is not a production service. Kernel-level dedupe alone
does not prove the full driver's retry contract.

## Item added to stage 4 comparison

For each shortlisted backend, record whether a **proven completed command's
original result remains retrievable at the new-write count/byte limit**, whether
that retry consumes another WAL/log entry, fsync or write-budget unit, and whether
same-ID/different-payload requests still conflict. Distinguish new writes,
verified prior-result reads and unresolved operations. Compare this under the
same original-result, durability, authentication and failure semantics; do not
count retries as new economic effects.

The comparison includes the already discussed response-loss/restart case and
both entry and byte limits. A stale cache miss is not proof of non-execution.
A poisoned or unrecovered journal must not expose an unverified result or bypass
recovery. Report latency and resource use separately from new-command goodput.
No measurement was run and no new numerical performance threshold is introduced.

## Correction direction only — not implemented

A verified, read-only prior-command lookup belongs before **new-write capacity
admission**, but after the checks required to trust and authorize that result.
It must match the original typed payload, return the original result on a match,
and reject a same-ID mismatch. Do not call mutating `reserve()` as a lookup probe:
it can reserve new inventory on a miss. Do not substitute `order()` lookup: some
recorded rejected commands have no order. Do not fake a new LocalReceipt sequence
or entry hash for a read-only replay; the original durable provenance must remain
identifiable. The exact lookup surface is a future implementation decision.

Only genuinely new work then needs new log budget and log-before-apply. A pure
result read must not advance the ordered-driver time watermark without a durable
record; that would change behavior across restart. This does not generalize to
v4 conflict Err(Capacity), which is a state-changing operation and must be
preserved and replayed rather than filtered out as a read-only error.

PR #11 should be preserved as an experiment for now. A future approved integration
may adapt its wire/journal above locked v4, but original v1 evidence must remain
separate and no v1 input may be silently relabelled v4. Local fsync remains
separate from quorum ACK. No code, rollout, tag or integration is authorized by
this document.
