# Decision answer — k-stage2-v5-impl residual stops (final)

JunTae delegate, 2026-10-13. Scope: in-memory `kix-kernel-v5` only. No spend, hardware, mainnet, secrets, or production runtime. Every value below is a kernel constant or caller-supplied parameter with a default; none claims legal or provider authority.

## 1. Reserved-slot release
- **Decision:** stays stopped. No release entry point. Unchanged from merged §5.8.
- **I12 handoff predicate (pre-authorized shape, not activated):** release only when all four hold: termination record exists for the slot, `late_fact_custody = Accepted{capacity_bytes ≥ 64 KiB, window = 30 days}`, `transfer_blocked = true`, original operation and record still resident.
- **I12 option:** none accepted. Independent review assignee: Astra; trust-policy approver: JunTae. Until both sign, predicate is spec-only.
- **I13 custody owner:** operations/security = JunTae (interim); budget placeholder `0 bytes` = release blocked.

## 2. Reclamation
- **Deleting transition:** stays stopped. `Kernel::reclaim_report` remains the only surface.
- **I09 values (kernel defaults, caller-overridable, no backend):**
  - retry-support window: **15 days** from command first result
  - memory-residency: **72 hours** after terminal state, LRU, cap **10,000 records**
  - retention floor for terminated-order records: **5 years** (reconciliation floor; legal period still pending I10)
  - evidence hashes: **retained indefinitely** until I10 clears
  - report SLO: computed synchronously, **≤ 50 ms** for 10,000 records
- **I10 legal/dispute hold:** `hold: Option<HoldRef{id, kind: Legal|Dispute|Erasure, placed_at, placed_by}>`. Any hold ⇒ ineligible. Holds never expire automatically; clearing requires explicit `clear_hold(id, by)`. Default: no hold, but any order with `ReturnRequired` or open conflict is treated as held.
- **Report ordering/visibility:** sort by `(terminated_at ASC, order_id ASC)`; blockers listed in fixed order `[ActiveOp, ReservedSlot, ReviewRequired, UnboundFence, ReturnObligation, ReplayWindow, Hold, I09, I10, I13]`; report is internal-only, no wire exposure.

## 3. Review release
- **Decision:** stays stopped. Redelivery never clears `review_required`. `ReturnRequired` and `review_required` remain orthogonal.
- **Conclusion fields (spec for later node):** `{conflict_cause: enum, affected_operation_id, resolved_facts: Vec<(fact_id, hash)>, authority: {approver_id, role, timestamp}, conclusion_id}`. All five required.
- **I11 automatic authority:** limit **0** (no automatic release). Named approvers JunTae (primary), Park Myung-woon (alternate); kernel does not authenticate them. Batch follow-up: **24-hour** post-hoc listing, read-only.

## 4. Conflict-index upkeep
- Gate stays closed until §§1–3 transitions are authorized. Index preserves v4 membership only.

## Other open values
- Chain-currency time source: **caller-supplied monotonic `now` parameter**; deadlines default **none**. No chain clock stored.
- Automatic-approval limit: **0**.
- Provider facts I02–I05, I08: remain caller flags + hashes; kernel evaluates nothing. Owner Toss contract/technical.
- Wire/OpenAPI/command names: **not added**. Reserved prefix for a later node: `v5.termination.*`, `v5.reclaim.report`.

## Still out of scope
Durable storage, logs/journals, R2, replication, real PG/bank/KYC, public endpoints, Sui testnet/mainnet. Each needs separate authorization.
