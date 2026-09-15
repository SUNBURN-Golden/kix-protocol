# kix-kernel: KTX-R1

An I/O-free deterministic transition model using only `kix-types` and Rust std collections. This is the first replacement execution kernel, not a production replicated engine.

## Implemented meaning

- Stable `(scope, principal, request)` command identity; exact original typed request comparison.
- Immutable original outcome replay before new-attempt availability checks. Current order state is a separate query.
- Bounded commands/orders/observations; no dedupe eviction. Completion records have a separate cap from new reservations.
- All-or-none contiguous selection inside real segments, crossing a 64-bit word when appropriate but never crossing an aisle. GA capacity cannot overdraw.
- One transition applies reservation, minimal order, quote/policy/asset binding, stable external operation and result without whole-state JSON or state cloning.
- Local execution/business fences and explicit ordered time/semantics version.
- PaymentUnknown is retained past TTL. Authenticated late bound facts may arrive after ownership change.
- Capture event and economic operation deduplication are distinct. Preserve conflict evidence and quarantine both named operations, including an operation not yet bound to an order. Quarantine blocks later binding and external-send authorization; matching later evidence never clears review automatically.
- Matching capture after expiry/cancellation creates ReturnRequired without reviving the old reservation or releasing another order's seats.

## Hard boundaries

No socket, filesystem, real clock, random generator, PG, SQLite, Python, chain client, cryptographic registry/provider authentication, consensus, durable ACK or deployment. Method inputs are trusted ordered adapter input, not an exposed client API. The adapter must authenticate principal/control/provider source and authorize access even to replayed results. Hash equality is not source authentication.

`replace_owner` only models an ordered owner-state replacement; it is not old-process fencing, membership or state transfer. `cancel_scope` is only a local fence, not a distributed cancellation barrier. Snapshots/log serialization and upgrades are not implemented. A cloned in-memory state or repeated input sequence is not recovery evidence.

The initial fixture accepts positive-price orders, one entire capture operation, and either one contiguous seat bundle or GA units. Free orders, multiple intents/captures/assets, partial allocation, refunds, current paid-order cancellation settlement and general composite policies are required follow-on commerce work, not deleted requirements. ReturnRequired is not refund authorization or execution. Unknown/unbound/conflicting external payloads need a bounded durable adapter inbox/quarantine before a provider delivery can be acknowledged.

Memory admission is bounded by configured record counts with fixed-width inputs and maximum seat/segment/bundle lengths. History never silently disappears; retention/GC/checkpoints are future work, so a full kernel stops new work rather than forgetting dedupe. This is not a fixed-pool zero-allocation engine and has no published throughput/floor number.

## Verification

`tests/transitions.rs` contains 32 deterministic regression cases after the R1 audit fixes. Successful state commands advance admitted time, including no-op expiry and duplicate observations; immutable reservation-result lookup remains read-only. Actual compilation and run evidence belongs to the exact PR head/CI run, not this count. They test local transitions, not multithreaded competition, disks or a replica cluster.

Next: registered versioned command/snapshot envelopes, mature storage/consensus integration, explicit stable-storage ACK, crash/torn-write/snapshot/leader histories, then real authenticated economic adapters. See ADR-0001 and masterplan 2.4.
