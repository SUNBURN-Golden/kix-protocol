# ADR-0001 — KTX authority, commit and recovery contracts

Date: 2026-09-15. Status: accepted design direction; production disabled.
Baseline: S07-A `98d5f6372b68f875bcb2b670c5998697ecfb76c1` (PR #9).

This ADR supersedes the PostgreSQL-only authority and execution sequencing in masterplan 2.3 / architecture v4. It does not supersede money conservation, asset/registry/policy binding, CE1 namespace separation, ZK hardening, cancellation currentness, or historical fault evidence. Existing reference code is not modified or promoted to a runtime dependency.

## 1. What is being preserved

Rebuild the economic functions and safety guarantees already tested in Python as Rust runtime behavior. Also implement the persistent models not present in the historical calculation-only and limited paid-resale fixtures. This is neither line-by-line translation nor a claim that a complete Python commerce engine existed. Move remains the chain language; Python may orchestrate tests or independently check vectors but cannot finish a production trade on behalf of Rust.

The common business invariants survive. The trust/finality model is explicitly mode-specific; moving work off-chain must never be described as preserving independent-validator assurance automatically.

## 2. Authority profiles (not switches granting permission)

| Fact | DelegatedExecution target | NativeChainExecution target |
|---|---|---|
| Reservation/minimal purchase commitment | designated replicated KTX shard within a proved exclusive grant | designated KTX shard's local intent; not a chain inventory guarantee |
| Chain right issued/transferred | verified chain execution | verified chain execution |
| External money moved | authenticated provider fact, reduced into KTX obligations | same |
| Query projection | non-authoritative PostgreSQL or another projection | same |
| SQL comparison profile | separate disposable inventory owned only by PostgreSQL | never concurrent writes to a KTX-owned resource |

`DelegatedExecution` is disabled until grant, revocation and non-cooperation protocols are implemented and checked. A configuration label, signature or Raft majority does not create chain-enforced exclusivity or Byzantine independence.

An exclusive grant binds inventory set/quota, immutable configuration, business epoch, execution authority and allowed actions. Withdrawal must stop new commitments at a known source cut, preserve committed-but-unissued obligations, and return only proven-unused inventory. Silence or a timeout is not proof of unused inventory. If the old authority cannot supply evidence, stop/reconcile the affected scope; do not allocate it to a new writer speculatively. Recovery and non-cooperation procedures remain a production gate.

No reservation is described as chain issuance. Public APIs must distinguish reservation, external payment observation, contractual return requirement and verified chain finality.

## 3. Stable command identity and distinct fences

CommandIdentity = stable business scope + authenticated principal + client_command_id.
The stable scope can identify a sale incarnation, but never changes while retrying the same command. Ownership generation, replica leader term, transport attempt number and current routing are NOT key components.

Business request equality/fingerprint is stored separately. Same identity + same business payload returns the original result; same identity + different payload is a conflict. The R1 kernel compares the full immutable typed payload (no caller-provided hash). Future canonical wire hashing may optimize this only without weakening equality/binding.

ExecutionFence identifies the current writer. BusinessFence identifies cancellation/sale currentness. ReplayVersion identifies kernel semantics. These fields have different lifetimes. Before replying to a replay, the ingress must still authenticate the caller and authorize result access. An immutable old successful result is not proof that the HOLD is still live.

Ownership movement must transfer dedupe results, original requests, pending observations, minimal orders and external operation bindings along with inventory. Record eviction requires an explicit replay-retention/tombstone contract; R1 has bounded records and no eviction, so capacity exhaustion backpressures instead of forgetting requests.

## 4. Single-shard commit unit and ACK

The durable unit includes command identity + original payload, inventory reservation/generation, minimal order, immutable quote/policy/asset binding, initial result and stable next execution intent. Never independently ACK an in-memory HOLD then attempt a separate order INSERT.

Target ACK: the declared stable-storage quorum has committed the entry; deterministic application has fixed the result; the result and external intent can be recovered from the persisted log/snapshot. Leader RAM receipt, replica RAM receipt, OS page cache alone, a local `apply()` return or a library progress callback is not this ACK.

Do not require a full state snapshot synchronously for each command when durable log replay reconstructs it. Persist log/hard-state/snapshot and issue messages in the consensus library's required order. The stable-storage implementation, torn writes, truncation, checksums, snapshot installation, membership and replay are separate integration work.

Initial comparison profile: three replicas in independent failure domains within one region; at most one replica unavailable; acknowledged operations survive the profile's declared crash/restart conditions. This is a benchmark/deployment specification, not an implemented guarantee. Whole-region RPO=0 is not claimed; it needs synchronous placement surviving that region and includes WAN delay. Majority loss must not produce successful new writes.

## 5. Replay and upgrades

Ordered input fixes admitted time, validated external observations and all nondeterministic inputs. Replicas never independently expire seats using local wall clocks. Validate supplied time and monotonicity at the ordered boundary; the state machine is not a time oracle. Successful state-command calls advance admitted time even when expiry has not arrived or an observation repeats. Immutable reservation-result lookup is a read-only exception and does not advance time; it still requires caller authentication at ingress.

Log envelopes must separately bind wire schema, kernel semantics version, policy/asset snapshots, ownership generation and application decision. Snapshots identify state version and committed cut. A software upgrade needs a logged activation boundary, old-version replay or a validated state migration, mixed-version admission rules and rollback rules. BCS equality alone does not establish equal business semantics.

R1 accepts semantics version 1 and rejects other versions. Its replay test reconstructs in-memory state from the same ordered inputs. This is NOT disk, upgrade, cluster-replay or leader-crash verification.

## 6. External effects, observations and UNKNOWN

Only committed external intents are executable. Commit an in-flight/UNKNOWN transition before sending. The provider-specific request identity, account scope, endpoint/API version, idempotency retention and reconciliation lookup must be fixed in the adapter contract. A retry of the same external action keeps the original identity. Do not switch PGs to resolve an UNKNOWN action.

Internal fencing stops new internal writes by an old owner; it cannot cancel a request already sent to a provider. Accept validated late facts bound to the original operation even when its submitting owner has changed. The current owner applies those facts under its current execution fence. Rejecting an old command is not the same as discarding an old operation's real success.

Event dedupe and economic-operation dedupe are distinct. Store contradictory evidence, quarantine every order/operation named by both the original and contradictory payloads and avoid overwriting the original fact. An unbound operation named in accepted conflicting evidence cannot later gain a fresh reservation binding. Quarantine blocks a new external-send transition. Later validated facts are still recorded, but a matching amount alone never clears review or automatically authorizes fulfillment. Expiry/cancellation can still establish ReturnRequired while retaining review. Unknown/unbound/oversize events need a bounded durable inbox/quarantine outside the pure kernel; rejection by R1 is not a license to ACK and discard them. Evidence hashes provide integrity, not provenance authentication.

R1 models one full capture operation per positive-priced reservation. Mismatch means review; a matching capture after expiry/cancellation means ReturnRequired, never resurrecting an expired order or releasing inventory now owned by another order. ReturnRequired is a marker, not an authorized refund nor the complete Obligation model. Free orders, multiple intents/captures, partial settlement, refunds and payment allocations remain in the scope of R3.

## 7. Cancellation and ownership movement

Cancellation completion is not file distribution. Bind the barrier to the authority-placement version and inventory scope. Every relevant current shard must apply the cancellation fence or be provably fenced. Split/migration/new ownership inherits pending cancellation generations; an A/B barrier cannot ignore a new C owner.

Distinguish request recorded, new work fenced, chain-side fence verified, old external operations reconciled and refunds completed. A local scope fence does not imply all these states.

Existing Move ShowControl currentness, exact control-id binding and old-epoch rejection remain required. Private proof/nullifier checks are authority prerequisites and cannot be moved to analytics.

R1 `cancel_scope` and `replace_owner` implement local ordered model transitions ONLY. They do not authenticate organizer/administrative authority, coordinate barriers, replicate membership or prove old-process fencing. Only a trusted control adapter may eventually drive them.

## 8. Cells, inventory and limits

Core-local execution shards own multiple logical rows/actual contiguous segments. A segment is not an OS thread or Raft group. On-chain per-seat objects remain a separate partitioning axis. All-or-none selection must handle real aisles, invalid seats, eligibility masks and machine-word boundaries. R1 covers contiguous segment selection and GA capacity; full policy eligibility and arbitrary bundles follow.

Cells isolate execution, queues, memory and storage budgets. Admission is bounded per cell/shard/provider by counts, bytes, age, outstanding operations and recovery load. Completion, cancellation, expiry and reconciliation retain service budgets under new-claim overload. Never allow strict priority to starve another class indefinitely.

Batch by count/bytes/max wait, with low-load deadlines. Bound PG/chain/export backlog and retained WAL; async is not infinite absorption. SOLD negative views carry versions/expiry and must invalidate after refund/reopen. Retry results bypass new-attempt availability hints, not authentication.

Cross-shard transactions require durable prepare and coordinator decision. Prepared participants cannot unilaterally time out after another authority may have committed. Global coupon budgets, user limits and internal balances need explicit authoritative coordination or preallocated escrow, not optimistic local copies.

## 9. Exports and fair comparisons

Each export records the originating shard commit and projection applied watermark separately. A PostgreSQL projection LSN is not a KTX source cut. Cross-shard exports need a consistent cut with coordinator decisions; a list of arbitrary shard cursors is insufficient. File hashes and trusted source authentication are separate requirements.

Keep a SQL-authoritative comparison route on disjoint test inventory. Compare equal ACK/failure/consistency semantics, successful durable goodput, p50/p99/p99.9, low load, hot rows, recovery and background work. Do not count sold-out rejects or in-memory bitmap operations as purchase TPS. No performance threshold or achieved number is asserted by this ADR.

## 10. Implementation status and exits

R0: this ADR + masterplan 2.4 + architecture v5.
R1: pure single-shard Rust transitions and bounded in-memory state; no durable server.
R2: registered command/snapshot schemas + mature storage/consensus integration + actual crash histories; PostgreSQL baseline comparison.
R3: authenticated registry/policy/provider adapters; complete Order/Payment/Obligation/refund/outbox model.
R4: edge/admission, scheduling and cell isolation; bounded fault/load harness.
R5: exclusive delegation/revocation, native chain objects, cross-shard coordination and privacy.
R6: measured NUMA/core pinning/I/O/GPU optimization without weakened guarantees.

The R1 kernel is not the completion of the old S07-B/C nor the end-to-end Python replacement. Historical storage-loss root cause, remote durability, production ZK setup/migration and independent chain verification remain open.

## References

The user's 2026-09-15 maximum-performance architecture review supplies the design basis (baseline 98d5f637). The stable-identity, external-fence, cancellation-placement and replay-version refinements are explicit additions from the follow-up review.

- Raft integration order: https://tikv.github.io/doc/raft/index.html
- Ready/persistence contract: https://tikv.github.io/doc/raft/raw_node/struct.RawNode.html
- Historical plans: ../PROTOCOL_MASTERPLAN_V23.md
- Current execution contract: ../../runtime/ARCHITECTURE.toml
