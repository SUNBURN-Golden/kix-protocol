# Commerce resale read transport handoff

This mapping covers the 13 `NOT_BOUND` rows from Commerce PR #146. Each bound route is an in-memory loopback `POST` under `/x-kix-contract-only/read/`; the value below is its route suffix and integration OpenAPI `operationId`. The local TypeScript SDK still exposes the pinned write catalogue. [Commerce PR #146 rows](https://github.com/SUNBURN-Golden/kix-commerce-apps/blob/9a55fe4e257376f9db3f877a11b65e3ecc43c661/docs/kix-resale-journey-binding-change-requests.md) · [Owner decision](../decisions/COMMERCE_RESALE_READ_TRANSPORT.md)

| Commerce screen need | Local route or disposition | Input besides `actor` |
| --- | --- | --- |
| Open listings | `list_open_listings` | Optional `limit`, `cursor`, `minimum_watermark` |
| Product search | product decision pending | |
| Listing detail | `get_listing` | `listing_id`, optional `minimum_watermark` |
| Product detail | product decision pending | |
| Variant selector | product decision pending | |
| Bid and ask quotes | product decision pending | |
| Offers | product decision pending | |
| Trade history | product decision pending | |
| Price series | product decision pending | |
| Current holder and right version | `get_right` | `right_id`, optional `minimum_watermark` |
| Presentation after transfer | `get_presentation` | `right_id`, `version`, `holder_role`, optional `minimum_watermark` |
| Active settlement | `get_settlement` | `listing_id`, optional `minimum_watermark` |
| Uncertain operation recovery | `get_operation_recovery` | `operation_id` or `trace_id`, `subject` (`action`, `field`, `id`), and either `through` or `request_cut: true` |

For a lost reply or write deadline, call `get_operation_recovery` on the same running gate with the original write's fixture actor, operation ID or request trace, typed subject, and `request_cut: true`. Use `transfer_id` as the subject field for `resale_accept_resale` and `settlement_id` for `settlement_initiate`. A matching retained acceptance returns `CUT_AVAILABLE` with a signed source watermark, even if settlement initiation finished before the listing was bound. Send the same actor, identity and subject with that `accepted_through` verbatim as `through`, omitting `request_cut`. A cut already obtained from a same-source read is also valid if it covers the acceptance. The worker may return `CORE_BUSY` while it is still handling the write. A cut from before acceptance leaves the result `UNKNOWN`. `ACCEPTED` carries the exact first receipt as local fixture evidence. Recovery grants zero retry authority. [Request and response schemas](../contracts/openapi/kix-protocol.integration-gate.openapi.json)

The historical `resale-market/market-accept` receives `settlement_id: null` and `settlement_gate: UNBOUND`. The bound companion replays the qualified setup, initiates, authorizes, captures, and binds `settle-read-1`, then commits the mock settlement before transfer. Its settlement `trade_id` is `list-1`, the listing subject. It checks refusal for a conflicting binding, acceptance before commit, and reads whose binding points to an unrelated trade. The successful transfer receipt, listing read and settlement read agree on the same non-null ID. [Transport vectors](../../reference/read_model/vectors/resale-read-transport.json)

The existing qualified `booking-resale/accept-A` journey binds `listing-A` to `settle-resale` with the distinct trade ID `trade-resale-A`. The HTTP regression replays the original vectors and checks the captured and committed settlement views, organizer and debtor access, and seller refusal. [Qualified Commerce vectors](../../sdk/conformance/vectors/commerce-fixture-tuple.vectors.json)

## Source tuple and supervisor handoff

The archived gate OpenAPI bytes in `sdk/compat/inputs/` verify the historical `bootstrap-2` and `commerce-fixture-8ba7f6c-1` tuples. The historical Commerce test also checks the archived server source against its original pin. The verifier defaults to the current tree's gate bytes. Mixing them with either historical manifest yields `integration_gate bytes drift`. Historical checks explicitly select the archived inputs and verify their original blobs and SHA-256 digests.

The read release manifest binds a producer source commit and tree. The profile can be prepared with `node sdk/generate/generate_resale_read_manifest.mjs --profile-only`. For a review fix to this unpublished tuple, remove the superseded draft manifest and SHA-256 sidecar before committing the producer source. The producer commit contains the code, OpenAPI, SDK evidence and vectors, including the prepared profile. Run these commands offline from that source worktree and include the emitted manifest and sidecar in the same delivery PR. The final delivery tree, with the manifest and sidecar excluded, should match the producer tree. Record CI and review for the final delivery head separately.

```sh
python3.12 -B scripts/check_sdk_client.py
node sdk/generate/generate_resale_read_manifest.mjs --source "$(git rev-parse HEAD)"
node sdk/compat/verify_compat.mjs \
  --manifest sdk/compat/manifests/manifest.commerce-resale-read-transport-1.json \
  --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-resale-read-transport-1
```

This profile covers the local read transport evidence. Expanded HTTP writes still require the applicable exact write qualification and rollout decision. Fixture outcomes do not prove real payment, ownership, admission, production readiness, or consumer acceptance.

## Product follow-up

The seven product rows remain `NOT_BOUND` pending Product / Protocol decisions about product identity and filters, product-to-listing association, variant identifiers, quote sides and expiry, offer visibility and pagination, trade-history visibility, and price-series units and windows. Market matching also needs a product decision and is outside the six local routes.
