# ADR-0001 — KTX authority, commit and recovery contracts

Date: 2026-09-15. Status: accepted design direction; production disabled.
Baseline: S07-A `98d5f6372b68f875bcb2b670c5998697ecfb76c1` (PR #9).

2026-09-17 scope clarification, base main `94376835ea4fc818619fc79e2be4df7d4947496a`:
this ADR preserves safety relationships, not an automatic implementation order.
The accepted authority choice is [model 1](../decisions/AUTHORITY_MODEL_1.md), and
[DEVELOPMENT_PLAN](../DEVELOPMENT_PLAN.md) is the current approval/sequence authority.
R2 and integration (a) remain prohibited; no kernel or adapter change is made here.

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

The R1 A revision was published at `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631` and is included in main `94376835ea4fc818619fc79e2be4df7d4947496a`; locked kernel blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`. It accepts semantics version 4 and rejects other versions: bound-operation quarantine applies before conflict capacity checks, while unbound quarantine requires retained evidence; see the review addendum below. Its replay test reconstructs in-memory state from the same ordered inputs. This is NOT disk, upgrade, cluster-replay or leader-crash verification.

## 6. External effects, observations and UNKNOWN

Provider selection update 2026-09-17: Toss Payments is provisional, ordinary domestic KRW card payments only for payment-method phase 1. Merchant scope for resale/finance and general payment-webhook signature remain unconfirmed. [PG_TOSS_CARD_PROFILE](../contracts/PG_TOSS_CARD_PROFILE.md) records official observations and proposed boundaries; [STATE_LIFECYCLE](../contracts/STATE_LIFECYCLE.md) retains the common definitions. No adapter implementation is authorized. Provider/MID/environment/API-contract version/product/payment-method/operation-kind bind the interpretation of evidence; a card terminal state is not a universal finality rule.

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

> **Historical sequence as of 2026-09-15, not current authorization.** The R0–R6 list below preserves the earlier plan. In particular R2 is now prohibited and integration (a) is deferred. References to R3/R5 elsewhere in this ADR are historical destination labels, not authorization to start them. Current stages and approved first-batch work are defined in [DEVELOPMENT_PLAN §§1/5](../DEVELOPMENT_PLAN.md). PR #11 is a separately [tag-preserved v1 experiment](../status/PR11_PRESERVATION.md), not part of the locked v4 runtime.

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

## R1 review addendum: quarantine, reserved capacity and unmatched facts

This addendum is limited to R1 business rules. It neither selects a storage engine nor authorizes R2 implementation.

### A — safety quarantine before evidence retention

A conflicting provider/account/event identity quarantines every already bound operation named by the original and incoming facts before checking whether the conflicting evidence fits the observation budget. Capacity in this path means the new evidence and any unbound identity were not retained; bound-order quarantine and ordered time remain applied. It is not a no-state-change result and must not be treated as a rolled-back safety transition or provider receipt ACK.

The earlier A working copy had an unsafe scope-wide overflow latch: arbitrary unbound identities in rejected evidence could permanently fence unrelated orders. The revised patch removes that field, all scope-wide overflow checks and mass review assignment. The explicit quarantine set now contains bound operations only, so its size cannot exceed the actual order count. No overflow release transition is needed for the removed mechanism; individual review resolution and record reclamation remain unimplemented.

An unbound identity blocks future reservation only if its conflicting evidence was actually retained. Before a new binding or inventory mutation, reserve checks the complete provider/account/operation identity against retained conflicts as well as bound quarantine. Unbound quarantine is derived from those records, with at most one distinct incoming identity per retained conflict, and is bounded by the evidence budget rather than by order count. Rejected evidence creates no speculative identity entry. Consequently an identity from unretained evidence can still bind later; the kernel alone cannot detect a fact it did not retain. The adapter inbox reconciliation contract remains required and unimplemented. Semantics version 4 separates this behavior from the prior A working copy; no old-state migration is implemented.

Event identity must describe one canonical observation in this kernel. An adapter for a batch webhook must use a stable per-item identity rather than blindly reuse its delivery event ID for different operations. Exact same-payload replay is not a conflict. Removing overflow does not implement or verify provider-specific batch normalization.

### B — decided responsibility: adapter durable inbox (not implemented here)

인증된 제공자 관측의 수신 원문, provider/account/event/operation 식별자, 원문 해시와 검증 결과는 커널 호출 및 제공자 수신 ACK 이전에 어댑터의 durable inbox에 내구성 있게 보존해야 한다. 커널의 Err(UnknownOperation)은 업무 적용 보류를 뜻한다. 해당 inbox 항목은 UNMATCHED로 유지하며 삭제하거나 처리 완료로 표시하지 않는다. 권위 있는 operation-order 결합을 확인한 뒤 동일 원문으로 대사·재처리하며, 주문을 임의 생성하거나 취소·만료된 권리를 부활시키지 않는다. 동일 이벤트 식별자의 다른 원문은 덮어쓰지 않고 별도 상충 증거로 보존한다. 인박스 보존 실패·용량 부족 시 수신 ACK를 보내지 않고 명시적으로 역압력을 적용한다.

The kernel can return UnknownOperation without storing that payload. The inbox contract is the required custody location, not evidence that an inbox already exists. This patch adds no durable inbox, provider authentication, storage, or ACK implementation. End-to-end external-success preservation remains unimplemented until that responsibility is satisfied and tested.

### Reserved observation release — proposal only; no release transition implemented

Current reservation removal occurs only when a supported new-event bound capture is retained. Capture converts reserved capacity into stored-evidence occupancy and does not reclaim the total evidence budget. Expiry/cancellation/owner movement alone never releases an UNKNOWN operation's slot.

Proposed release requires authenticated, operation-scoped terminal failure or final void evidence under a provider contract that rules out later execution, together with proof that no executable attempt remains and a fence against retransmission of the closed operation. A network error, one failed attempt, a cancellation request, a single not-found response, or elapsed time is insufficient.

Terminal outcome, stable operation identity, evidence reference and an idempotent closed-operation marker must be preserved before/in the same authoritative transition that releases the reservation exactly once. Anomalous late facts remain the inbox's reconciliation responsibility and must not reopen an expired order or re-enable sending. If those finality conditions cannot be established, the slot remains UNKNOWN and the scope applies backpressure. A separate retained-evidence lifecycle is also required for reclaiming total observation capacity; deleting a reservation alone does not solve retained-record exhaustion.

This section is a proposed release contract only. No failure/void command, release method, garbage collection, inbox handoff implementation or timeout-based release is introduced.
