# Commerce fixture tuple conformance

The [qualification table](COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json) records
`SEMANTIC_CONFORMANCE` for 28 actions on
`POST /x-kix-contract-only/local-call`. It applies to the listed fixture
steps and outcomes from Commerce `9a55fe4e257376f9db3f877a11b65e3ecc43c661`
against Protocol `8ba7f6c36373ac0ec49246f51f7471c164ac3a28`
(tree `d3f5412ef84f64fe83c5d3a3d3ada173921bfbf9`).

## Consumer handoff

After this evidence merges, Commerce can replay and bind manifest revision
`commerce-fixture-8ba7f6c-1` in its own consumer change. First compare the
verifier's `manifest_sha256` with the independently held consumer pin using
step 1 of the [scoped qualification procedure](CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification).
On a match, check the producer and file pins, then match the method, path,
action, machine, operation, subject field, schema digest, context, step and
outcome in the fixture evidence. The manifest carries the full 84-command
catalogue for identity verification. Its grant covers the 28 listed actions
only. `bootstrap-2` continues to grant schema binding.

| Context | Qualified behavior |
| --- | --- |
| Booking resale | Primary reservation to issuance, resale adoption to payment, settlement binding, a refusal before mock commit, then transfer and mock distribution. Cancellation after primary payment is a refusal. |
| Booking admission | Primary reservation to issuance, credential adoption, authorization and one consumption. Fresh repeat consumption and cancellation after primary payment are refusals. |
| Booking refund | Confirmed unpaid reservation cancellation, separate mock settlement cancel and fail, and a captured settlement's refund binding and mock acceptance. Issuance after reservation cancellation is a refusal. |
| Resale market | Primary reservation to issuance, listing, buyer hold, payment and transfer with settlement `UNBOUND`. Listing cancellation is covered from both `LISTED` and `BUY_HELD`. After payment it is a refusal. |

The [full market receipts](../../reference/booking_resale_admission/fixtures/commerce_market_full_receipts_v1.json)
give `kix-commerce-apps` the complete producer output for each of the 14
accepted `resale-market` vectors. In the companion JSON, use the vector ID as
the key in `receipts`, for example `receipts["resale-market/market-pay"]`.
The companion pins the source corpus and supplements manifest revision
`commerce-fixture-8ba7f6c-1`.

The [booking branch receipts](../../reference/booking_resale_admission/fixtures/commerce_booking_branch_receipts_v1.json)
provide the complete producer output for three booking resale, four booking
admission and three booking refund vectors. Use the full vector ID, for example
`receipts["booking-admission/order-B"]`. The 32 direct `receipt_ref` entries for
first acceptances, 14 market receipts and ten booking branch receipts cover all
56 listed first acceptances. Both companions are non-normative. External
Commerce acceptance remains `UNVERIFIED`.

The payment-observation lost-reply pair replays `booking-admission/payment-B`
after the same order confirmation on two fresh in-process hosts. Commerce
records the same operation ID and body idempotency key, one attempt, `UNKNOWN`,
and no receipt in both histories. If the request is dropped before dispatch,
the reservation stays `CONFIRMED` with no payment reference or journal append.
If the successful reply is withheld, the reservation reaches `PAYMENT_NOTED`
with the pinned payment reference and one reservation journal append. Both
histories leave the slot `RESERVED` with no right or admission credential.
The harness resolves the hidden receipt as `receipts["booking-admission/payment-B"]`
in the pinned booking branch receipts. With recovery `NOT_BOUND`, Commerce
keeps the unresolved write fenced with zero follow-up calls. The pair supplies
companion evidence for `commerce-fixture-8ba7f6c-1`.
[Payment-observation lost-reply fixture](../../reference/booking_resale_admission/fixtures/commerce_payment_observation_lost_reply_v1.json) ·
[Focused payment-observation replay](../../reference/booking_resale_admission/test_commerce_payment_observation_lost_reply.py)

The issuance lost-reply pair replays `booking-admission/issue-B` on two fresh
in-process hosts after the same recorded mock payment. Commerce sees the
same `UNKNOWN` after one attempt in both histories. The producer remains
`PAYMENT_NOTED` when the request is dropped, and reaches `ISSUED` with a
version-1 mock right when the successful reply is withheld. Resolve the
second history's `hidden_receipt_id` as
`receipts["booking-admission/issue-B"]` in the pinned booking branch receipts.
That receipt is harness evidence. Commerce must keep the write fenced, with
zero follow-up calls, because the missing reply leaves issuance unresolved
and operation recovery is `NOT_BOUND`. The pair supplements the existing
manifest grant. [Issuance lost-reply fixture](../../reference/booking_resale_admission/fixtures/commerce_issuance_lost_reply_v1.json) ·
[Focused replay](../../reference/booking_resale_admission/test_commerce_issuance_lost_reply.py)

The refund acceptance lost-reply pair replays
`booking-refund/observe-mock-acceptance` after the same refund binding on two
fresh in-process hosts. Commerce records the same operation ID and body
idempotency key, one attempt, `UNKNOWN`, and no receipt in both cases. Before
dispatch, the refund stays 12,000 KRW outstanding with zero accepted. When
the successful reply is withheld, the host records 12,000 KRW accepted,
zero outstanding, and one new settlement journal entry. Both settlements
remain `CAPTURED` with `funds_executed=false` and `external_return_closed=false`.
The hidden receipt at `commerce_journey_receipts_v1.json#/steps/38/receipt`
is harness evidence. With recovery `NOT_BOUND`, Commerce must keep the write
fenced with zero follow-up calls. [Refund acceptance lost-reply fixture](../../reference/booking_resale_admission/fixtures/commerce_refund_acceptance_lost_reply_v1.json) ·
[Focused refund acceptance replay](../../reference/booking_resale_admission/test_commerce_refund_acceptance_lost_reply.py)

The cancellation lost-reply pair replays `booking-refund/cancel-C` after
confirming the same unpaid reservation on two fresh in-process hosts. Commerce
records the original operation ID and body idempotency key, one attempt,
`UNKNOWN`, a null receipt and zero follow-up calls in both histories. A drop
before dispatch leaves `reserve-C` `CONFIRMED` and slot 2 `RESERVED` with no
journal append. Withholding the successful reply leaves `reserve-C` `CANCELLED`
and slot 2 `FREE` with one reservation journal append. Both histories end
without recording payment, issuance or refund. The harness compares the hidden
receipt with `receipts["booking-refund/cancel-C"]` in the pinned booking branch
receipts. Slot availability remains unresolved for Commerce, so it keeps the
cancellation fenced with recovery `NOT_BOUND`.
[Cancellation lost-reply fixture](../../reference/booking_resale_admission/fixtures/commerce_cancel_lost_reply_v1.json) ·
[Focused cancellation replay](../../reference/booking_resale_admission/test_commerce_cancel_lost_reply.py) ·
[Delivery evidence index](COMMERCE_DELIVERY_EVIDENCE_INDEX_V1.json)

The resale settlement commit pair replays `booking-resale/settle-resale-commit`
after the pinned pre-commit transfer refusal on two fresh in-process hosts. A
drop before dispatch leaves `settle-resale` `CAPTURED` with zero new journal
entries. Withholding the successful reply leaves it `COMMITTED` with one
settlement `commit` entry and a hidden receipt matching the pinned journey
receipt at `#/steps/23/receipt`. Both histories retain the recorded resale
payment and seller ownership at right version 1 and end before transfer or
distribution. Commerce records the original operation ID and body idempotency
key, one attempt, `UNKNOWN`, a null receipt and zero follow-up calls in both
histories. The SDK selector returns `HOLD_SEMANTIC` for each observation.
Recovery remains `NOT_BOUND`.
[Resale settlement commit lost-reply fixture](../../reference/booking_resale_admission/fixtures/commerce_resale_commit_lost_reply_v1.json) ·
[Focused commit replay](../../reference/booking_resale_admission/test_commerce_resale_commit_lost_reply.py) ·
[Delivery evidence index](COMMERCE_DELIVERY_EVIDENCE_INDEX_V1.json)

An unlisted tuple or context is outside the grant. Keep unresolved `UNKNOWN`
outcomes fenced. The market, settlement and operation-recovery reads remain
`NOT_BOUND`. [PR #146 change requests](https://github.com/SUNBURN-Golden/kix-commerce-apps/blob/9a55fe4e257376f9db3f877a11b65e3ecc43c661/docs/kix-resale-journey-binding-change-requests.md)

TTLs, fees and amounts in the pack are synthetic inputs. Product TTLs, fees,
compensation, market visibility, matching, pagination and legal, accounting
and provider terms remain `UNDETERMINED`.

## Replay offline

```sh
node sdk/compat/verify_compat.mjs \
  --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json \
  --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1 \
  --integration-gate-input sdk/compat/inputs/integration-gate.bootstrap-2.openapi.json
python3.12 -B -m unittest discover -s reference/booking_resale_admission \
  -p 'test_commerce_fixture_tuple_conformance.py'
npm --prefix sdk run conformance
```

For the full market receipt comparison and its mutation checks, run

```sh
python3.12 -B -m unittest discover -s reference/booking_resale_admission \
  -p 'test_commerce_fixture_tuple_conformance.py' -k market -v
```

For the booking branch receipt comparison and its mutation checks, run

```sh
python3.12 -B -m unittest discover -s reference/booking_resale_admission \
  -p 'test_commerce_fixture_tuple_conformance.py' -k booking_branch -v
```

For the paired cancellation and resale settlement commit replays and delivery
index checks, run

```sh
PYTHONPATH=reference/booking_resale_admission python3.12 -B -m unittest -v \
  test_commerce_cancel_lost_reply test_commerce_resale_commit_lost_reply \
  test_commerce_delivery_evidence_index
```

Use the manifest and vectors with their referenced files. For each target,
start a fresh in-memory host, replay its `setup` vector IDs in order, then
submit its `envelope` verbatim. Keep the envelope's `operationId` separate from
its body's `idempotency_key`. `commerce_step` names an actual fixture step and
`control_vector_ids` identify additional evidence. On booking vectors,
`input_index` traces the envelope body to the prior input file's `steps` array.
[Manifest](../../sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json) ·
[Vectors](../../sdk/conformance/vectors/commerce-fixture-tuple.vectors.json)

Check the exact business or schema refusal code, or compare typed
`receipt_fields` by dotted path and the full receipt at `receipt_ref` when
present. A receipt reference is a repository path followed by a JSON
Pointer. A successful first call checks the `journal_delta` by machine.
Refusals and duplicate replay preserve business state and journals.
`replay_of` identifies deliberate offline replay controls using the original
body key. The SDK test checks the shared envelopes through a recording
transport. The Python test checks producer outcomes with the pinned parser
and FSM host.

The scope is source-informed conformance for synthetic in-memory fixtures.
Production, durability, real payment, chain authority, browser enablement,
N/N−1 compatibility and consumer acceptance are outside this evidence.
