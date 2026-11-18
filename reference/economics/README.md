# Economics reference model (Track K stage 6, R-10)

Synthetic-money economics as a **reference model**: one explicit, sequential,
in-memory session that composes unchanged published layers. It is an internal
Python API only — no wire names, no catalogue entries, no new protocol error
codes. Every rate, cap, TTL, budget and expiry is caller-supplied synthetic
fixture input; nothing here defaults a product policy value.

`evidenceClass` is `SYNTHETIC_REFERENCE`. Every execution flag is false
(`protocolTruth`, `productionConformance`, `productionReadiness`,
`productionEndpoint`, `fundsExecuted`, `chainWriter`, `fsmDurable`,
`localDurableData`). This is not production readiness, not bank exactly-once,
not chain finality, not durable fencing and not a storage engine.

## Composed layers (all unchanged)

| Layer | Path | Role |
| --- | --- | --- |
| Commerce `kix:commerce:2` | `reference/v0.3-rc1/commerce.py` | OrderLine, quote, payment plan, line-refund calculation (`CALCULATION_ONLY`). |
| Frozen lifecycle/finance Core | `reference/v0.3-rc1/` | Synthetic event/trade journey, allocations, published effect commands. |
| Stage-5 admission | `durable/model.py`, `durable/budgets.py` | Pure capture decision + five-class budgets; optional local-PG binding. |
| Settlement FSM | `reference/settlement_f01_f03/` | SET-POLICY-DRAFT-0.4 (L0, W0, R0, S0, T0, B5 REQUESTER, P0). |
| Payment effects | `reference/payment_effects/` | Four published effect commands over the unchanged Core. |
| Resale FSM | `reference/booking_resale_admission/resale_fsm.py` | `seller_due` face (option A mock boundary). |

The package bootstraps these directories onto `sys.path` (disjoint module
names); it never copies or edits them.

## Modules

- `authentication.py` — fail-closed asset/policy registries. Hash binding is
  calculation integrity, not source authentication; a document must be
  registered before use and must equal the registered one exactly.
- `quotes.py` — authenticated commerce wrappers and the u128 → fixture-money
  boundary (`require_money_bound` refuses, never narrows).
- `captures.py` — per-leg capture ledger over the pure stage-5 decision;
  `DurableCaptureLedger` persists admission through the unchanged `DurableUnit`.
- `refunds.py` — proposal → authorization → reservation → settlement binding;
  full refunds additionally reverse the Core event and send one REFUND intent.
- `payouts.py` — W0 distribution, allocation-bound PAYOUT effects, and the
  composed resale seller-payout journey.
- `session.py` — `EconomicsSession`, the composition root.

## Coverage map (AGENTS.md §7)

Layer-internal behaviour is already covered by the existing suites and is
**not** re-tested here: commerce (`scripts/verify_commerce.py`,
`reference/v0.3-rc1` tests), settlement (`reference/settlement_f01_f03/test_*`),
stage-5 admission (`durable/test_*`), effects (`reference/payment_effects/test_*`),
resale (`reference/booking_resale_admission/test_*`). The tests below cover the
**composition** gaps this node adds.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Asset & policy authentication | covered | `test_authentication.py` |
| OrderLine | covered | `test_quotes.py`, `test_bundles.py` |
| Immutable quotes | covered | `test_quotes.py` (validate round trip, stale-hash refusal) |
| Free orders | covered | `test_free_orders.py`, `fixtures/free_order.json` |
| Discounts | covered | `test_discounts.py` |
| Bundles | covered | `test_bundles.py`, `fixtures/bundle_order.json` |
| Multiple intents & captures | covered | `test_captures.py`, `fixtures/capture_plan.json` |
| Allocation | covered | `test_allocation.py` |
| Refunds | covered | `test_refunds.py`, `fixtures/partial_refund.json` |
| Payouts | covered | `test_payouts.py` |
| Resale seller payout | covered | `test_resale_payout.py`, `fixtures/resale_journey.json` |
| Multiple assets | covered | `test_multi_asset.py`, `fixtures/multi_asset_order.json` |
| Conservation & rejection atomicity | covered | `test_conservation.py` (seeded) |
| Durable capture binding (local PG) | partial / local-only | `durable/test_economics_binding.py` (not CI-wired; needs pinned local PostgreSQL) |

## Composition boundaries (characterizations, not new semantics)

- The fixture money layers (Core, settlement FSM, effects) are **KRW-only** and
  cap at `10**12`. u128 quotes above the bound are refused, never narrowed.
  Non-KRW asset groups compose quote/plan/capture admission and refund
  calculation; their settlement binding is refused (`FIXTURE_MONEY_KRW_ONLY`),
  never converted. There is no FX.
- The Core journey binds **per order group** (one synthetic event/trade carrying
  the group payable), not per line; per-line rights issuance is booking-layer
  scope. The settlement policy's residual payee must equal the event organizer
  and its fee payee must be `platform`, so FSM obligation faces and Core PRIMARY
  allocations are the same faces (verified fail-closed at settlement).
- **Partial refunds** compose at the settlement FSM (B5 REQUESTER bearer, faces
  untouched, distribution continues). **Full refunds** additionally reverse the
  Core event (`cancel_event`) and send one published REFUND intent
  (`CASH_REFUND_FIXTURE` or `PG_ORIGINAL_CANCEL_FIXTURE`). The published Core
  REFUND route is funded by a full-trade reversal liability, which would block
  the continuing distribution B5 requires — hence partial refunds do not use it.
- Capture admission uses `slot = capture_id`, so several captures may share one
  leg but never one slot; the stage-5 `business_rejected` (slot-collision)
  outcome is therefore not reachable through this API. Leg accounting and
  completion records are process-local fixture bookkeeping in this revision.
  For a new attempt the leg existence and remainder are checked **before** the
  admission decision — in the optional durable binding, before the admission
  transaction — so an `OVER_CAPTURE` refusal writes nothing and takes
  precedence over an inflow-capacity refusal; replay/conflict resolves first
  through a read-only stored-row probe (database-backed after a reopen).
- The resale journey's `primary.slot` is a 0-based integer (BRA gate seat
  index); the Core seat string is `str(slot)`. Caller expiries must fall inside
  the unchanged BRA offer window (`now < expires <= now + 900000` ms).
- Cross-machine atomicity is **not** claimed. Every readable precondition is
  checked before the first write; a failure after a write is a blocker for
  manual review, never an automatic retry. The Core clock stays 0.

## Non-claims

No real funds, no real PG/bank/KYC calls, no public endpoints, no Sui
testnet/mainnet, no R2 or own replication/consensus/storage engine, no new
coin/TIX module, no secrets, no production runtime. Product policy values and
new protocol commands stay `DECISION_REQUIRED · Astra`; legal/tax/accounting and
provider-dependent values stay `UNDETERMINED` with their owners.

## Run

```sh
# Narrow suite (the CI offline-suite entry):
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/economics -t reference/economics

# Optional local-PG durable binding (default off; needs the pinned local PostgreSQL):
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest durable.test_economics_binding
```