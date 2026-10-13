# kix-kernel-v5

In-memory semantics version 5. This crate forks the locked v4 transition kernel and adds only the stage-2 behavior that the merged design decision and the 2026-10-13 owner decision leave open to code. It is not a durable service, a storage engine, or a production runtime.

Authority: `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md` §5 (option O1) and §6, narrowed by the owner-delegate decision of 2026-10-13 for node `k-stage2-v5-impl`. The v4 crate and its two locked blobs are not modified. A version-4 context is rejected with `UnsupportedSemantics`.

## Implemented

- **Operational termination** (`Kernel::terminate`). One in-memory record per bound operation, replayed by `decision_id`. The only effect is that `mark_payment_unknown` returns `InvalidTransition`. Inventory, the reserved slot, review, and evidence stay. The record is not a durable approval and does not answer "durably approved". Automatic approval scope is 0.
- **Private conflict index.** `conflicts()` keeps vector order. Membership and the reserve-time quarantine rejection match v4's retained-conflict scan on histories that do not use v5-only commands. It is not updated for reclaim or release, which do not exist.
- **Hold references** (`place_hold`, `clear_hold`, `hold`). At most one `HoldRef { id, kind: Legal | Dispute | Erasure, placed_at_ms, placed_by }` per order. A hold never expires by time; only an explicit `clear_hold(id, by)` removes it. Neither call authenticates anyone or releases anything.
- **Read-only reclamation report** (`reclaim_report`, `reclaim_reports`). Takes a caller-supplied monotonic `now_ms` and a `ReclaimPolicy`. It deletes nothing, advances no time, and cannot say an order is eligible.

The normal dependency is `kix-types` only. `kix-kernel` is a dev-dependency used as a regression oracle. The running path does not call v4.

## Reclamation report

Blockers are listed in this fixed order (the derived `Ord` of `Blocker`):

`ActiveOp, ReservedSlot, ReviewRequired, UnboundFence, ReturnObligation, ReplayWindow, Hold, I09, I10, I13`

- `ActiveOp`: no termination record. A termination changes only this one reference (STATE_LIFECYCLE §5.8).
- `ReservedSlot`: the operation's observation slot is still reserved. Slot release does not exist, so a terminated order that has not received a capture keeps it.
- `ReviewRequired`: the sticky `review_required` marker.
- `UnboundFence`: retained conflict evidence names the candidate's operation identity (STATE_LIFECYCLE §6 "retained unbound fence").
- `ReturnObligation`: the order is `ReturnRequired`.
- `ReplayWindow`: `now_ms` is before the command's first result plus the retry-support window.
- `Hold`: an explicit hold is placed, or the order is treated as held. `ReturnRequired` and an open conflict (a quarantined operation or retained conflict evidence) are treated as held with no hold reference; the report names which in `implicit_hold`.
- `I09`, `I10`, `I13`: always last and always present. The input rows are open (see below), so the report has no eligible state.

`reclaim_reports` returns one report per terminated order, sorted by `(terminated_at ascending, order_id ascending)`. It reads a termination index and does per-order lookups that are logarithmic in the number of records.

Defaults in `ReclaimPolicy::default()` (each caller-overridable, none a backend setting):

| Field | Default | Used for |
|---|---|---|
| `retry_support_window_ms` | 15 days | `ReplayWindow` end, from the command's first result |
| `memory_residency_ms` | 72 hours | `memory_residency_ends_at_ms`, from the termination |
| `memory_residency_cap_records` | 10,000 | `over_residency_cap` in the batch: terminated records exceed the cap. No eviction or LRU exists |
| `retention_floor_ms` | 1,827 days (5 years, longest case) | `retention_floor_ends_at_ms`, informational. The legal period is pending I10 |

Evidence hashes are retained indefinitely: nothing in this crate deletes them. The report SLO is 50 ms for 10,000 records, synchronous; see `tests/reclaim_batch.rs` for what is and is not asserted.

The 15-day retry-support default is a KIX value chosen by the owner delegate. It is not the provider's public idempotency-key period and must not be read as that.

## Stopped

No entry point exists for these, by the owner decision of 2026-10-13 (stays stopped). Specs are recorded here and are not activated.

- **One-time reserved-slot release** (I12, I13). Shape pre-authorized but not activated: release only when a termination record exists for the slot, `late_fact_custody = Accepted { capacity_bytes >= 64 KiB, window = 30 days }`, `transfer_blocked = true`, and the original operation and record are still resident. No option for I12 is accepted. Independent review: Astra. Trust-policy approver: JunTae. Until both sign, this is spec only. I13 custody owner is operations/security (JunTae, interim); a budget of 0 bytes means release is blocked.
- **State-changing record or evidence reclamation** (I09, I10, I13). `reclaim_report` is the only surface.
- **Review release.** Redelivery never clears `review_required`. `ReturnRequired` and `review_required` stay orthogonal. Spec for a later node: a conclusion has five required fields: `conflict_cause` (enum), `affected_operation_id`, `resolved_facts: Vec<(fact_id, hash)>`, `authority { approver_id, role, timestamp }`, and `conclusion_id`. Automatic authority limit is 0. Named approvers (not authenticated by the kernel): JunTae primary, Park Myung-woon alternate. A 24-hour post-hoc read-only listing is the batch follow-up.
- **Conflict-index upkeep under reclaim or release.** Gate stays closed until the three transitions above are authorized.

Reserved names for a later node, not added to any wire, OpenAPI or catalogue here: `v5.termination.*`, `v5.reclaim.report`.

## Characterizations

These are not amendments to `docs/contracts/STATE_LIFECYCLE.md`.

- Termination is accepted only for `PaymentUnknown` with a reserved slot, no captured amount, and `review_required == false`.
- A known capture and `ReturnRequired` are rejected on that absence path.
- `OperationSnapshot::observations` and `retained_conflicts` are kernel-wide counts. Any newly retained evidence stales an evaluation that still names the old counts.
- `ActiveOp` is cleared by an operational termination only. An order that ended another way (for example `PaymentConfirmed`) is still listed as active, because the kernel has no other terminal marker.
- `UnboundFence` is read as retained conflict evidence for the candidate's own operation identity.
- A cleared hold leaves no tombstone. A delayed duplicate placement after clearing re-places the hold, which fails closed. Re-placing after clearing needs a new hold identifier to be accepted as new.
- C1–C5 are caller-supplied flags plus hashes. The kernel does not evaluate provider facts, authenticate the principal, or store a limit for automatic approval.

## Non-claims

This crate does not establish durability, distributed fencing, bank exactly-once behavior, chain finality, legal compliance, or production readiness. The v4/v5 differential test is source-informed and is not an independence proof. The retention defaults are not legal periods and do not close I09, I10, or I13. No wire, OpenAPI, or command-catalogue name is added here.
