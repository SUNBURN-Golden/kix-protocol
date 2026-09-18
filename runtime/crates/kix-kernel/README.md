# kix-kernel: KTX-R1

An I/O-free deterministic transition model using only `kix-types` and Rust std collections. This is the first replacement execution kernel, not a production replicated engine.

## Published review baseline

Implementation commit: `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631` (PR #12).
Locked kernel Git blob: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
Locked quarantine-test Git blob: `b607996c83a119c349f1cc90469ac1ba82764e20`.
The published implementation is semantics version 4. This 2026-09-16
correction changes documentation only, not the kernel or tests.

## Implemented meaning

- Stable `(scope, principal, request)` command identity; exact original typed request comparison.
- Immutable original outcome replay before new-attempt availability checks. Current order state is a separate query.
- Bounded commands/orders/observations; no dedupe eviction. Completion records have a separate cap from new reservations.
- All-or-none contiguous selection inside real segments, crossing a 64-bit word when appropriate but never crossing an aisle. GA capacity cannot overdraw.
- One transition applies reservation, minimal order, quote/policy/asset binding, stable external operation and result without whole-state JSON or state cloning.
- Local execution/business fences and explicit ordered time/semantics version.
- PaymentUnknown is retained past TTL. Authenticated late bound facts may arrive after ownership change.
- Capture event and economic operation deduplication are distinct. Quarantine every already bound operation named by a conflict before checking evidence capacity. An unbound identity blocks future binding only if the conflict evidence is retained. Matching later evidence never clears a bound order's review automatically.
- Before authorizing the first external send, `mark_payment_unknown` reserves one first-capture observation slot for that operation or returns `Capacity` without changing the order. UNKNOWN retries reuse the reservation. Unrelated events and conflicting evidence cannot spend it.
- Matching capture after expiry/cancellation creates ReturnRequired without reviving the old reservation or releasing another order's seats.
- ReturnRequired stays the order's state once it exists; `review_required` is an orthogonal sticky marker that can coexist with it. Later mismatching evidence may return the `Review` outcome and set review, but it keeps ReturnRequired and the retained capture and releases no inventory (STATE_LIFECYCLE 0.6 §5.7.1).

## Hard boundaries

No socket, filesystem, real clock, random generator, PG, SQLite, Python, chain client, cryptographic registry/provider authentication, consensus, durable ACK or deployment. Method inputs are trusted ordered adapter input, not an exposed client API. The adapter must authenticate principal/control/provider source and authorize access even to replayed results. Hash equality is not source authentication.

`replace_owner` only models an ordered owner-state replacement; it is not old-process fencing, membership or state transfer. `cancel_scope` is only a local fence, not a distributed cancellation barrier. Snapshots/log serialization and upgrades are not implemented. A cloned in-memory state or repeated input sequence is not recovery evidence.

The initial fixture accepts positive-price orders, one entire capture operation, and either one contiguous seat bundle or GA units. Free orders, multiple intents/captures/assets, partial allocation, refunds, current paid-order cancellation settlement and general composite policies are required follow-on commerce work, not deleted requirements. ReturnRequired is not refund authorization or execution. Unknown/unbound/conflicting external payloads need a bounded durable adapter inbox/quarantine before a provider delivery can be acknowledged.

Memory admission is bounded by configured record counts with fixed-width inputs and maximum seat/segment/bundle lengths. History never silently disappears; retention/GC/checkpoints are future work, so a full kernel stops new work rather than forgetting dedupe. This is not a fixed-pool zero-allocation engine and has no published throughput/floor number.

## Observation reservation and remaining gaps

The budget includes stored event records, stored conflicts and outstanding reserved slots. A fresh bound capture converts its own reserved slot into retained evidence in the same transition, even if its amount is wrong or it arrives after cancellation/expiry/owner change. Those state changes never free the slot first. A conflicting reuse of an existing event does not apply a capture and cannot consume the first-capture reservation.

This protects one first bound capture per authorized operation, not every future external fact. A NEW conflict at full capacity returns `Capacity` after quarantining bound operations and advancing ordered time; new evidence and unbound identities are not retained. The explicit quarantine set contains only bound operations and cannot exceed the actual order count. Unbound quarantine is derived from retained conflicts at reservation time, using the full provider/account/operation identity, and is bounded separately by retained evidence. The prior scope-wide overflow latch and mass review assignment are removed. Unrelated orders remain unaffected by arbitrary identities in rejected evidence. A fresh unbound operation still returns `UnknownOperation` without storage (or `Capacity` if already full), and an unretained unbound identity can later bind because the kernel lacks its evidence. That custody gap is not implemented by this patch. The adapter inbox named above is a requirement, not an implementation in this crate. Do not acknowledge provider receipt or claim universal external-success preservation based on these return values.

The revised A patch uses **semantics version 4**: a conflicting event can quarantine bound orders even when returning Capacity, but unbound quarantine requires retained evidence. Earlier contexts are rejected, and there is no replay migration in this patch. This reviewed v4 implementation was published in PR #12 at `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631`. Subsequent documentation-only corrections do not change the locked source. PR #11 is a separate semantics-v1 local-journal experiment, not an integrated v4 recovery path; its preservation does not lift the R2 hold. See the ADR review addendum for the decided unmatched-inbox responsibility and the proposed (unimplemented) terminal-outcome slot-release contract. Batch webhook delivery IDs require stable item-level normalization in the adapter; this patch does not implement it.

## Verification

At the published implementation commit, KTX CI `34957674101` and full protocol
CI `34957674135` both finished **completed / success**. The kernel total is
**51 tests**: `transitions.rs` 32, `observation_slots.rs` 11 and
`quarantine_capacity.rs` 8. The implementation submission reports 101 workspace
tests separately; a repeated clean-target run is not an additional unique test.
The old v2/93-test report is historical evidence, not the current acceptance
record. Exact source blobs, run links, artifact identity and unchanged historical
records are in [the validation record](../../../validation/2026-09-15-r1-observation-slots/README.md).
No new Rust run is claimed by this documentation correction. Later heads require
separate CI status reporting.

`tests/transitions.rs` contains 32 deterministic regression cases after the R1 audit fixes. Successful state commands advance admitted time, including no-op expiry and duplicate observations; immutable reservation-result lookup remains read-only. Conflict evidence Capacity now also preserves safety quarantine and its ordered time. Actual compilation and run evidence belongs to the exact PR head/CI run, not this count. They test local transitions, not multithreaded competition, disks or a replica cluster.

The observation-slot regressions also check failed-send atomicity, retry reuse, reserved capacity isolation, conflicts, late observations and explicit version-1 refusal. These are business-logic tests and supply no evidence for choosing KTX over another durable backend.

Fixed regressions cover full-budget bound quarantine, reserved-slot preservation, rejected unbound floods without scope-wide effects, retained versus unretained unbound binding, time ordering, replay stickiness and prior-version refusal. The old overflow-named test is retained by name with corrected isolation expectations. No property test or slot-release/inbox implementation is added.
