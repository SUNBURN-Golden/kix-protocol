# Commerce companion evidence index v1

The [companion JSON](COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json) is a
**non-normative, builder-authored navigation record** for `kix-commerce-apps`.
It connects eight input/outcome pack families (293 steps) to replay tests
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
