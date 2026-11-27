# Commerce companion evidence index v1

The [companion JSON](COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json) is a
**non-normative, builder-authored navigation record** for `kix-commerce-apps`.
It connects fifteen input/outcome pack families (422 steps) to replay tests
and the unchanged [consumer binding index](COMMERCE_CONSUMER_BINDING_INDEX_V1.json).
It adds no contract, protocol interface, adapter, runtime behavior or consumer
integration. The [development plan](../DEVELOPMENT_PLAN.md),
[Model 1 authority decision](../decisions/AUTHORITY_MODEL_1.md) and existing
contracts retain authority.

All fixture paths in the following table are relative to
`reference/booking_resale_admission/fixtures/`. Replay files live in its parent
directory. The JSON records complete repository-relative paths and test symbols.

| Family ID | Input | Outcome | Replay file | Cases / steps |
|---|---|---|---|---|
| `journey` | `commerce_journey_conformance_v1.json` | `commerce_journey_receipts_v1.json` | `test_commerce_journey_receipts.py` | ungrouped / 44 |
| `temporal` | `commerce_temporal_inputs_v1.json` | `commerce_temporal_receipts_v1.json` | `test_commerce_temporal_vectors.py` | 3 / 39 |
| `historical` | `commerce_historical_inputs_v1.json` | `commerce_historical_receipts_v1.json` | `test_commerce_historical_receipt_vectors.py` | 5 / 54 |
| `entry_resale_order` | `commerce_entry_resale_order_inputs_v1.json` | `commerce_entry_resale_order_receipts_v1.json` | `test_commerce_entry_resale_order_vectors.py` | 2 / 29 |
| `bound_issuance` | `commerce_bound_issuance_inputs_v1.json` | `commerce_bound_issuance_receipts_v1.json` | `test_commerce_bound_issuance_vectors.py` | 2 / 25 |
| `bound_resale` | `commerce_bound_resale_inputs_v1.json` | `commerce_bound_resale_receipts_v1.json` | `test_commerce_bound_resale_vectors.py` | 3 / 49 |
| `resale_expiry` | `commerce_resale_expiry_inputs_v1.json` | `commerce_resale_expiry_receipts_v1.json` | `test_commerce_resale_expiry_vectors.py` | 2 / 27 |
| `admission_cancellation` | `commerce_admission_cancellation_inputs_v1.json` | `commerce_admission_cancellation_receipts_v1.json` | `test_commerce_admission_cancellation_vectors.py` | 3 / 26 |
| `hold_release` | `commerce_hold_release_inputs_v1.json` | `commerce_hold_release_receipts_v1.json` | `test_commerce_hold_release_vectors.py` | 2 / 30 |
| `linked_refund` | `commerce_linked_refund_inputs_v1.json` | `commerce_linked_refund_receipts_v1.json` | `test_commerce_linked_refund_vectors.py` | 1 / 18 |
| `late_payment_after_cancel` | `commerce_late_payment_after_cancel_inputs_v1.json` | `commerce_late_payment_after_cancel_receipts_v1.json` | `test_commerce_late_payment_after_cancel_vectors.py` | 1 / 16 |
| `payment_ref_scope` | `commerce_payment_ref_scope_inputs_v1.json` | `commerce_payment_ref_scope_receipts_v1.json` | `test_commerce_payment_ref_scope_vectors.py` | 1 / 16 |
| `resale_buyer_release` | `commerce_resale_buyer_release_inputs_v1.json` | `commerce_resale_buyer_release_receipts_v1.json` | `test_commerce_resale_buyer_release_vectors.py` | 1 / 16 |
| `admission_replay_after_resale` | `commerce_admission_replay_after_resale_inputs_v1.json` | `commerce_admission_replay_after_resale_receipts_v1.json` | `test_commerce_admission_replay_after_resale_vectors.py` | 1 / 18 |
| `replaced_admission_binding` | `commerce_replaced_admission_binding_inputs_v1.json` | `commerce_replaced_admission_binding_receipts_v1.json` | `test_commerce_replaced_admission_binding_vectors.py` | 1 / 15 |

The original replay symbol is
`CommerceJourneyReceiptTests.test_complete_output_bytes`. Later replay classes
use `test_complete_output_bytes_and_references`. Each pack's `replay_test`
contains the exact `path` and `Class.method` `symbol`; the validator checks the
Python AST without importing TestCase classes into the new suite.

## Reading the record

`record_schema_version` (`kix-commerce-companion-evidence-index/1`) describes
only this local evidence metadata. `record_kind` is
`NON_NORMATIVE_COMPANION_EVIDENCE_INDEX`, `normative` is false and `consumer` is
`kix-commerce-apps`. These fields define no protocol encoding or wire schema.

`binding_index`, `producer_tuple`, and every pack's `input`/`output` contain
`path`, `sha256` and `gitBlob`. Both digests are computed from raw file bytes;
the Git blob digest includes the Git blob header. They identify bytes, without
asserting authenticity, durability, finality or production readiness.

The ordered `packs` contain `id`, input/output pins, `replay_test`,
`limitations` and ordered `entries`. Each entry records:

- `case_id`: exact existing case ID, or JSON null for the original ungrouped journey.
- `step_id` and `action`: exact source identities, checked against the outcome,
  published FSM catalogue and binding entry.
- `input_ref`: repository-relative input path plus JSON pointer ending in
  `/steps/<j>/body` or `/cases/<i>/steps/<j>/body`.
- `outcome_ref`: paired outcome path plus pointer to the complete step object,
  including its existing `input_ref`; `outcome_kind` is `receipt` or `rejection_code`.
- `binding_ref`: unchanged binding index path plus `#/commands/items/<k>`;
  `binding_status` copies that entry's existing status exactly.

The validator checks fixed input/output pairings independently of this record,
ordered one-to-one case/step coverage, digests, reference resolution and replay
symbol existence. Detached negative controls reject omissions, duplicates,
crossed associations (including valid alternate digests and same-action steps
in different cases), changed published actions and false qualification claims.
Existing replay suites verify outcome behavior and bytes; this companion does
not replace their tests or regenerate their vectors.

## Qualification and evidence limitations

The original binding index and
[producer tuple](PRODUCER_QUALIFICATION_TUPLE_V1.json) remain byte-identical.
Later evidence does not upgrade an original **BOOTSTRAP_SCHEMA_BOUND** command
to **MOCK_EVIDENCE**. BOOTSTRAP is not consumer acceptance.

Semantic consumption remains **HOLD_SEMANTIC**. All **13 reads remain NOT_BOUND**.
Diagnostic snapshots and local views are observations, not published read APIs.
SD1 remains **OPEN, User-owned and unresolved**; no option, waiver or verifier
order is chosen. External `kix-commerce-apps` acceptance is **UNVERIFIED**: its
adapter is outside this repository and was not invoked.

Historical receipts preserve first results and can differ from later state.
Replaying one grants no new execution authority. Rejected-key retention is
process-local, outside business snapshots/journals, and proves no durable
recovery. Reservation confirmation, payment observation, settlement commitment,
issuance, transfer and admission remain separate facts.

Clocks, prices, fees and other fixture constants are synthetic examples, not
approved defaults. Product policy values stay **UNDETERMINED** with existing
Astra/User owners; legal, accounting and provider questions retain their
recorded owners. These source-informed mock histories prove no real funds,
PG/bank/KYC calls, venue acceptance, chain finality, legal compliance,
distributed fencing or production readiness. No public endpoint, Sui
testnet/mainnet or production runtime is involved.

[Coverage, actual commands, byte preservation and limitations](../../validation/2026-11-17-plan-commerce-companion-evidence-index/README.md)
record this builder's local work. Local success is not clean-room independence,
A2 non-author exact-final-head review or hosted exact-head KTX/KIX CI. Those
remain supervisor delivery gates.

## Resale expiry extension

The seventh family adds two complete ordered histories through the existing
in-process `FsmHost`: unpaid expiry rejects payment with `LISTING_NOT_OPEN`;
paid expiry preserves `PAYMENT_NOTED` and the observed payment reference/amount,
rejects transfer with `LISTING_NOT_OPEN`, and rejects seller cancellation with
`COMPENSATION_UNDEFINED`. Holder `buyer-1` and version `1` remain unchanged.
Expiry is diagnostic, not a phase. The pack introduces no compensation, refund,
automatic relisting or transfer behavior.

Original-key listing/payment replay after clock advancement returns the first
receipt (`expired: false`), while current diagnostics retain `expired: true`.
The new outcome schema `kix-commerce-resale-expiry-receipts/1` contains the
fixture pin, sorted source pins and ordered cases/steps. Each step has `id`,
`action`, `input_ref`, exactly one of `receipt`/`rejection_code`, and a detached
`diagnostic_snapshot` of local views. Full machine state, digest and journals
are checked for rejection/replay non-mutation in memory; these are not read APIs.
The published listing amount and the accepted payment journal retain the amount;
there is no invented `payment_amount` view field.

The original six packs and all qualification metadata are preserved. Product TTL
and compensation policy remain **UNDETERMINED** with Astra/User and existing
legal/accounting owners. [Extension coverage and actual local verification](../../validation/2026-11-17-plan-plan-commerce-resale-expiry-vectors/README.md)
provide builder evidence only; no external consumer acceptance or A2 review is claimed.

## Admission cancellation extension

The eighth family adds three independent histories (26 steps) through unchanged
`FsmHost`, based on [§11.4](../contracts/BOOKING_RESALE_ADMISSION_GATES.md#114-순서)
and `AdmissionFsmTests.test_cancel_before_issue_blocks_entry_and_cancel_after_issue_does_not_void_it`.
Cancellation before payment/issuance rejects adoption with `TICKET_CANCELLED`;
payment observation without issuance rejects it with `TICKET_NOT_ISSUED`.
Cancellation after issuance and after consumption returns `CANCEL_AFTER_ISSUE`.
The issued credential remains usable through explicit adoption (`ELIGIBLE`),
authorization (`AUTHORIZED`) and consumption (`CONSUMED`, version 2).
Cancellation of `PAYMENT_NOTED` belongs to the separate compensation boundary,
covered by prior temporal vectors; this pack defines no refund or compensation.

`kix-commerce-admission-cancellation-receipts/1` records the input pin, sorted
source pins, ordered cases and complete receipts or refusal codes with exact
`input_ref` pointers. Each detached diagnostic snapshot includes all five
machines' canonical business state, digest and accepted journals plus local
views. Every refusal preserves those observations. Rejected-key retention is
separately checked as process-local bookkeeping via repeated rejection and
changed-binding conflict; these snapshots exclude it and prove no restart
persistence. They are not published read responses.

The original seven packs and 267 entries are preserved, as are all qualification
metadata and original binding statuses. Product policy values remain
**UNDETERMINED—Astra/User**; legal effects remain **UNDETERMINED—User/legal**.
[Coverage and actual local verification](../../validation/2026-11-18-plan-plan-commerce-admission-cancellation-vec/README.md)
are source-informed builder evidence, not A2 independent review, hosted
exact-head CI or external consumer acceptance.

## Expired hold release and slot reuse extension

The ninth family adds two 15-step histories through `FsmHost` at a synthetic
hold's expiry boundary and one millisecond later. A stays `HELD` with its slot
`RESERVED` after expiry. Confirmation returns `RESERVATION_EXPIRED` and B's
competing hold returns `SLOT_OCCUPIED`. Explicit `reservation_release` makes A
`RELEASED` and the slot `FREE`. Retrying B's rejected key while free still
returns `SLOT_OCCUPIED`. An otherwise identical fresh-key hold allocates B.
Repeated rejected keys after reuse retain their original codes. Changing the
buyer under B's rejected key returns `IDEMPOTENCY_CONFLICT`.
[Reservation contract §§9.2–9.4](../contracts/BOOKING_RESALE_ADMISSION_GATES.md#92-전이)

Original A hold/release and successful B hold keys replay their complete first
receipts, with only replay metadata changed. A's historical hold says `HELD`
and its historical release says `FREE`, while current diagnostics show A
`RELEASED`, B `HELD`, and the slot occupied by B. A's current slot fields refer
to B. The reservation machine derives the `expired` diagnostic for pre-issue phases.

`kix-commerce-hold-release-receipts/1` contains raw-byte fixture/source pins,
ordered outcomes and exact input pointers. Each `diagnostic_snapshot` includes
all five machines' business state, digest and accepted journals plus available
reservation and show views. Every rejection and replay preserves those
observations. Rejected-key retention is process-local and outside the diagnostic
snapshot. Detached controls reject premature freeing, double occupancy, changed
outcomes and crossed references. Test-local journal effects exercise the
non-mutation guard.

`HOLD_SEMANTIC`, all 13 reads `NOT_BOUND`, SD1 `OPEN` and User-owned, and external
acceptance `UNVERIFIED` remain. TTL and policy values remain
**UNDETERMINED—Astra/User**. Legal effects remain **UNDETERMINED—User/legal**.
Hosted exact-head CI and A2 non-author review remain supervisor delivery gates.
[Coverage and local verification](../../validation/2026-11-18-plan-plan-commerce-hold-release-vectors/README.md)

## Linked purchase and partial refund

`linked_refund` appends 18 associations to the preceding nine packs and 323
associations. The history binds `reserve-1` to `claim-1`, commits the mock
settlement and issues `issue-1` explicitly. After adoption, reservation
cancellation yields `CANCEL_AFTER_ISSUE` with identical business snapshots.
The ensuing refund obligation and partial mock cancellation acceptance both use
`claim-1`. The acceptance leaves the active right and populated admission journal
intact. Separate receipts record `AUTHORIZED` and `CONSUMED_ONCE`.
[Replay guide](../../reference/booking_resale_admission/README.md#commerce-linked-purchase-and-partial-refund-vectors)

Compensation policy is **UNDETERMINED** with Astra and JunTae. Legal refund
liability is **UNDETERMINED** with JunTae and legal counsel. The index retains
`HOLD_SEMANTIC`, 13 reads `NOT_BOUND`, SD1 `OPEN` and User-owned, and external
acceptance `UNVERIFIED`.
[Replay](../../reference/booking_resale_admission/test_commerce_linked_refund_vectors.py) ·
[Coverage and local verification](../../validation/2026-11-20-plan-commerce-linked-refund-vectors/README.md)

## Late payment after booking cancellation

`late_payment_after_cancel` appends 16 associations. A confirmed unpaid
`order-1` is cancelled, and buyer 2 confirms a replacement booking for the same
slot. The late synthetic payment for `order-1` and its original-key replay both
return `TERMINAL_IMMUTABLE` with identical machine states, digests and accepted
journals. The original cancellation key returns the historical `FREE` slot in
its receipt while the current slot stays reserved for buyer 2. The replacement
has separate receipts for its own payment, issuance, authorization and
consumption. [Replay guide](../../reference/booking_resale_admission/README.md#commerce-late-payment-after-booking-cancellation-vectors)

Compensation is **UNDETERMINED** with Astra and JunTae. Refund liability and
actual late-fact custody are outside this history. Actual provider facts remain
subject to the state lifecycle contract. The pack carries `HOLD_SEMANTIC`,
all 13 reads are `NOT_BOUND`, SD1 is `OPEN` and User-owned, and external
acceptance is `UNVERIFIED`.
[State lifecycle §3](../contracts/STATE_LIFECYCLE.md#3-lc-fact--늦은-사실-보존) ·
[Coverage and local verification](../../validation/2026-11-20-plan-commerce-late-payment-after-cancel/README.md)

## Show-scoped payment references

`payment_ref_scope` records one 16-step history across two shows in the same
in-memory host. Reusing the primary reference for a resale on `show-1` returns
`PAYMENT_BINDING_CONFLICT` and preserves the unpaid listing, seller's right
version, and all five business journals. A fresh key with a distinct reference
records the resale payment. A separate command transfers the right. The
primary payment for `show-2` records the original reference while `show-1`
retains its primary payment. [Contract §§3–4](../contracts/BOOKING_RESALE_ADMISSION_GATES.md) ·
[Replay guide](../../reference/booking_resale_admission/README.md#commerce-payment-reference-scope-vectors) ·
[Builder validation](../../validation/2026-11-20-plan-commerce-payment-ref-scope/README.md)

This history carries `HOLD_SEMANTIC`, 13 `NOT_BOUND` reads, SD1 `OPEN` and
User-owned, and external acceptance `UNVERIFIED`. The semantic grant for
`commerce-fixture-8ba7f6c-1` covers the steps and outcomes listed in its
qualification table. [Scoped fixture qualification](COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md)

## Resale buyer-hold release

`resale_buyer_release` records one 16-step history. A wrong-buyer release
returns `BUYER_MISMATCH` and preserves state, accepted journals and views. The
named buyer releases `hold-1`, returning `list-1` to `LISTED` with the seller
still holding `issue-1` at version 1 and no resale payment recorded. The same
recipient acquires `hold-2`. Replaying the original release key returns its
historical `LISTED` receipt with `duplicate: true` and `applied: null` while the
current listing remains `BUY_HELD` under `hold-2`. A separate payment observation
records `PAYMENT_NOTED`, and the explicit transfer moves `issue-1` to `buyer-2`
at version 2.
[Resale transitions §10.2](../contracts/BOOKING_RESALE_ADMISSION_GATES.md#102-전이) ·
[Replay guide](../../reference/booking_resale_admission/README.md#commerce-resale-buyer-hold-release-vectors)

The pack is non-normative mock evidence under `HOLD_SEMANTIC`. All three
release calls retain `BOOTSTRAP_SCHEMA_BOUND`. The exact replay symbol is
`CommerceResaleBuyerReleaseVectorTests.test_complete_output_bytes_and_references`.
[Replay suite](../../reference/booking_resale_admission/test_commerce_resale_buyer_release_vectors.py) ·
[Coverage and local verification](../../validation/2026-11-20-plan-commerce-resale-buyer-release/README.md)

## Admission replay after resale

The authorization for `buyer-1` at version 1 expires before the resale
payment and transfer. After `buyer-2` acquires the right at version 2,
the same authorization key and body return the first `admit-1` receipt with
`duplicate: true` and `applied: null`. The fresh version-1 consume returns
`STALE_VERSION`. Neither call appends to an accepted journal or records
consumption. The current mock resale holder stays `buyer-2` at version 2.

The pack carries `HOLD_SEMANTIC`. Its current-state observations are
test-harness evidence. The exact replay symbol is
`CommerceAdmissionReplayAfterResaleVectorTests.test_complete_output_bytes_and_references`.
[Inputs and evidence pointers](../../reference/booking_resale_admission/fixtures/commerce_admission_replay_after_resale_inputs_v1.json) ·
[Complete outcomes](../../reference/booking_resale_admission/fixtures/commerce_admission_replay_after_resale_receipts_v1.json) ·
[Replay guide and command](../../reference/booking_resale_admission/README.md#commerce-admission-replay-after-resale-vectors) ·
[Coverage and local verification](../../validation/2026-11-26-plan-commerce-admission-replay-after-resale/README.md)

## Replacement admission binding

`replaced_admission_binding` follows the temporal case through replacement
and presents three fresh consumes for the same paid, issued right. The old
gate with the replacement request returns `GATE_MISMATCH`. The replacement
gate with the old request returns `ADMISSION_REQUEST_MISMATCH`. Each refusal
preserves `admit-2`, right version 1 and every accepted journal. The matching
pair returns `CONSUMED_ONCE`, detaches the authorization and advances the
right to version 2. The bound admission and reservation journals each append
one consume and the slot stays `ISSUED`.

All three presentations carry the `admission_consume` binding
`MOCK_EVIDENCE`. The pack carries `HOLD_SEMANTIC` and links the original
payment and issuance receipts separately. The replay symbol is
`CommerceReplacedAdmissionBindingVectorTests.test_complete_output_bytes_and_references`.
[Inputs and receipt pointers](../../reference/booking_resale_admission/fixtures/commerce_replaced_admission_binding_inputs_v1.json) ·
[Complete outcomes](../../reference/booking_resale_admission/fixtures/commerce_replaced_admission_binding_receipts_v1.json) ·
[Replay command](../../reference/booking_resale_admission/README.md#commerce-replacement-admission-binding-vectors) ·
[Coverage and local verification](../../validation/2026-11-27-plan-commerce-replaced-admission-binding/README.md)
