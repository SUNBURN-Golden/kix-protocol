# Consumer surface boundary map

## Basis and precedence

**Non-normative, builder-authored inventory, 2026-11-10.** This is navigation to
existing contracts and observed local interfaces, not a new consumer contract,
schema, alias table, adapter or qualification result. The
[development plan](../DEVELOPMENT_PLAN.md),
[Model 1 authority decision](../decisions/AUTHORITY_MODEL_1.md) and cited
contracts retain precedence. Policy values stay **UNDETERMINED** with their
recorded owners. Unsupported bindings stay **NOT_BOUND**. Semantic SDK
consumption stays **HOLD_SEMANTIC** outside the scoped Commerce fixture grant.

Task: `audit29-consumer-surface-boundary-map`, supplied by the supervisor with
its read-only design plan; no issue or corresponding `docs/tasks/` document.
Source: audit #29 finding 2, external input
`/workspace/kix-run/audits/audit_29_20261110.md` (audit basis `8a8a0fc`, not this
builder's base). Observed cached `origin/main`, base and starting branch HEAD:
`508c65e690a8eaf035bfc282f263f3198c103600`, branch
`agent/kix-audit29-consumer-surface-boundary-map`. Fetch was NOT_RUN under the
supervisor's no-network instruction; remote freshness is unverified. No local
base delta was observed. These observations describe that tree plus this
documentation patch, not a future delivery commit.

[Builder validation](../../validation/2026-11-10-audit29-consumer-surface-boundary-map/README.md)
records coverage, commands, preservation and unavailable delivery evidence.

## Surface inventory

Each table describes an existing surface. Field names and selectors are copied
from its cited dispatcher; sharing a word such as `consume`, `view` or `submit`
does not bind the surfaces together.

### HTTP core and FSM commands

| Boundary | Existing interface |
|---|---|
| Entry points and contracts | [Gate server](../../integration_gate/server.py), [envelope/schema validation](../../integration_gate/schema.py), [FSM host](../../integration_gate/fsm_host.py), [core](../../reference/v0.3-rc1/core.py); [contract-only OpenAPI](../contracts/openapi/kix-protocol.contract-only.openapi.json), [integration-gate OpenAPI](../contracts/openapi/kix-protocol.integration-gate.openapi.json), [FSM command pin](../contracts/openapi/fsm-command-contract.json) and [guide](../contracts/openapi/README.md). |
| Transport and lifetime | Explicitly started, non-production loopback HTTP process on `127.0.0.1`; one worker hosts the reference core and five in-process FSMs. Default state/replay is process-local. Contract-only OpenAPI supplies no live server/base URL. |
| Request and response | `POST /x-kix-contract-only/local-call` takes exactly `{operationId, actor, action, body}`. `body` must match the selected published schema. Accepted core calls return the receipt fields `domain`, `operationId`, `sequence`, `action`, `result`; accepted FSM calls return the selected machine's receipt, including its provenance, duplicate/applied markers and operation-specific snapshots. Envelope/schema failures are 4xx; domain rejections are 422 with `error` and `rejected=true`; startup/transport failures remain distinct. There is no calculator `evidenceClass` wrapper here. |
| Action namespace | 40 core actions plus 44 `<machine>_<op>` FSM actions, 84 total. Examples: `admission_consume` and `reservation_authorize_admission` are distinct catalogue entries. Envelope `operationId` is the caller's operation identity, not the OpenAPI operation name or `action`. Bare ticket selectors are not HTTP aliases. |
| Identity and replay | Core replay uses `operationId` plus the fingerprint of `actor`, `action`, `body`; a changed fingerprint yields `OPERATION_ID_CONFLICT`. FSM replay uses the machine's body `idempotency_key` and subject/body rules; the host does not copy envelope `operationId` into that key. HTTP `Idempotency-Key` is ignored. A replayed first receipt is not a new current-state view. |
| Prerequisites and authority | Pin the existing catalogue/schema bytes; start the local gate explicitly and satisfy machine setup, logical-clock and source prerequisites. `actor` is a fixture string, not authenticated `actorContext`. `/health` and `/ready` report local process/reference availability, not production readiness. Browser access is opt-in as described in the guide, not authentication. |
| Evidence and qualification | The HTTP tests and pin checks provide source-informed, non-production gate evidence. Apply the [scoped Commerce fixture qualification](#scoped-commerce-fixture-qualification) to the listed tuples, contexts and steps. [HTTP tests](../../integration_gate/test_http_gate.py), including `test_http_idempotency_key_header_is_not_consulted` and `test_fsm_idempotency_key_replays_without_using_operation_id`. [Contract evidence map](INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md). |
| Unavailable bindings | No public service, provider authentication or published ticket read API. Optional `--readiness-dir` is bounded local core-call replay, not production durability; this server refuses FSM calls with `READINESS_FSM_REFUSED` while that journal is active. See [readiness limits](../contracts/READINESS_RUNTIME.md). |

### TypeScript SDK

| Boundary | Existing interface |
|---|---|
| Entry points and contracts | [SDK guide](../../sdk/README.md), [client](../../sdk/src/client.ts), [generated catalogue](../../sdk/generated/catalogue.ts), [manifest contract](../contracts/sdk/COMPATIBILITY_MANIFEST_V1.md), [bootstrap-2 profile](../../sdk/compat/profiles/bootstrap-2.profile.json). |
| Transport and lifetime | `createLocalCallClient({ transport })` is a synchronous local-call wrapper around caller-supplied transport. It supplies no base URL, authentication, connection startup, process lifecycle or automatic retry. |
| Request and response | `client.invoke({operationId, actor, action, body})` validates the existing envelope/body and returns the supplied transport's result unchanged (`unknown`); it does not create a unified response schema for other tools. |
| Action namespace | The same 84 pinned catalogue actions, not commerce calculator actions or ticket/reward/pool local selectors. |
| Identity and replay | Validation preserves caller identities and invokes transport once. Server/core/FSM replay rules above still apply; SDK validation is not an idempotency service or an authority check. |
| Prerequisites and authority | Pinned OpenAPI, generator, catalogue, manifest/profile/vector tuple; Node 24 for existing tooling. Caller supplies transport. `actor` remains a fixture string. `bootstrap-1` is the preserved historical 40-command pin; current generated output uses `bootstrap-2`. |
| Evidence and qualification | `bootstrap-2` grants catalogue and schema binding for 84 commands. Use the separate [scoped Commerce fixture qualification](#scoped-commerce-fixture-qualification) for semantic evidence. Other semantic consumption remains **HOLD_SEMANTIC**. [Conformance tests](../../sdk/conformance/conformance.test.mjs), [SDK byte checker](../../scripts/check_sdk_client.py). |
| SD1 verifier evidence | After JunTae's November 18 option 1 authorization (`[pt224u]`), the checked-in verifier checks the profile byte hash before the OpenAPI references. The ordered §4 regression exercises the sequence. [Owner decision record](../decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md), [profile hash block](../../sdk/compat/verify_compat.mjs#L146-L150), [ordered regression](../../sdk/conformance/conformance.test.mjs#L364-L409). |

### Scoped Commerce fixture qualification

`bootstrap-2` binds catalogue schemas for 84 commands (40 core and 44 FSM).
`commerce-fixture-8ba7f6c-1` grants `SEMANTIC_CONFORMANCE` for the listed steps
and outcomes across 28 actions at the pinned producer. The other 56 actions,
unlisted contexts or steps and any mismatched tuple remain `HOLD_SEMANTIC`.
External `kix-commerce-apps` acceptance remains `UNVERIFIED`.
[Qualification table](COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json) ·
[Semantic manifest](../../sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json)

Before consuming the fixture evidence, `kix-commerce-apps` selects the grant
as follows.

1. Verify the manifest with its [SHA-256 sidecar](../../sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json.sha256)
   and [profile](../../sdk/compat/profiles/commerce-fixture-8ba7f6c-1.profile.json).
   Require `manifest_schema_version = kix-compat-manifest/1`, verifier exit 0,
   and a verdict with `ok: true`, `profile_kind: "SEMANTIC_CONFORMANCE"` and
   `profile_revision: "commerce-fixture-8ba7f6c-1"`. Before looking up the
   qualification table, compare the verdict's `manifest_sha256` with the
   consumer's expected digest
   `76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`.
   Store the pin independently of the candidate manifest and sidecar, and
   compare it on every selection. A missing or different expected digest
   yields `HOLD_SEMANTIC` with `vector_id: null`. The profile's
   `catalogue.schema_digests` identifies all 84 schemas. Its `grants` points to
   the qualification table for the narrower semantic scope.
   [Verifier invocation](../../sdk/README.md#scoped-commerce-fixture-qualification)
2. Follow the manifest's `vectors[]` entry `commerce-fixture-qualification-table`
   and require `record_schema_version = kix-commerce-fixture-tuple-conformance/1`.
   Match the complete `producer` object across the manifest, the table and
   the producer being qualified. Compare `repository`, `source_commit`,
   `source_tree`, `protocol_domain` and `contract_schema_version`. The pin is
   `SUNBURN-Golden/kix-protocol` commit `8ba7f6c36373ac0ec49246f51f7471c164ac3a28`,
   tree `d3f5412ef84f64fe83c5d3a3d3ada173921bfbf9`. Check the referenced file
   digests and the table's `pins` for the replay dependencies. The table's
   `commerce_source.commit` identifies Commerce fixture source
   `9a55fe4e257376f9db3f877a11b65e3ecc43c661`.
3. In `tuples[]`, match `method = POST`, `path = /x-kix-contract-only/local-call`,
   `action`, `machine`, `op`, `subject_field` and `body_schema_sha256`.
   Compare the SHA-256 of the canonical body schema and read the subject from
   the named field in `body`. Match `contexts[].context` (`booking-resale`,
   `booking-admission`, `booking-refund` or `resale-market`), then look up the
   fixture step in that entry's `steps[step]`. Resolve its vector IDs and match
   the recorded setup and outcome. For example, `resale-market` / `market-cancel`
   has distinct vectors for `LISTED` and `BUY_HELD`. `control_vector_ids` supply
   additional evidence for the listed tuple and context.
   [Request-to-receipt vectors](../../sdk/conformance/vectors/commerce-fixture-tuple.vectors.json)
4. For each selected vector, start a fresh in-memory host, apply the `setup`
   vectors in order and submit the `envelope` verbatim. Keep `operationId`
   distinct from `body.idempotency_key`. Check the exact schema or business
   refusal code, or compare typed `receipt_fields` and the full receipt at
   `receipt_ref` when present. Check the recorded journal expectations. Missing
   or mismatched evidence leaves the step `HOLD_SEMANTIC`.
   Fence unresolved `UNKNOWN` outcomes without polling, retry or replacement
   writes. [Offline replay handoff](COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md#replay-offline)

The delivery fixtures replay pinned envelopes on fresh in-process hosts.
Producer evidence comes from the replay harness.

| Vector and delivery case | Commerce observation | Producer evidence |
|---|---|---|
| `booking-resale/accept-A-before-commit` · refusal delivered | `business-reject` with `SETTLEMENT_NOT_COMMITTED` | One refused dispatch. |
| `booking-resale/accept-A-before-commit` · request dropped before dispatch | `UNKNOWN` with a null receipt | Zero dispatches. |
| `booking-resale/accept-A-before-commit` · refusal withheld after dispatch | The same `UNKNOWN` record as the pre-dispatch drop | One refused dispatch with `SETTLEMENT_NOT_COMMITTED`. |
| `booking-resale/settle-resale-commit` · reply lost | `UNKNOWN` with a null receipt in both histories. The selector returns `HOLD_SEMANTIC`. | Zero dispatches leave settlement `CAPTURED` with no journal append. One successful dispatch leaves it `COMMITTED` with one settlement journal append. Both retain the recorded payment and seller at version 1, with zero cash distributed. |
| `resale-market/market-accept` · reply lost | `UNKNOWN` with a null receipt whether the request was dropped or the successful reply was withheld | Zero dispatches leave the seller at version 1. One successful dispatch transfers ownership to the buyer at version 2. |
| `booking-refund/cancel-C` · reply lost | `UNKNOWN` with a null receipt in both histories | Zero dispatches leave the unpaid reservation `CONFIRMED` and slot 2 `RESERVED`. One successful dispatch leaves it `CANCELLED` and the slot `FREE`. |

The non-normative delivery evidence index covers 17 cases across eight fixtures,
with 16 `UNKNOWN` outcomes and one delivered refusal. The fixtures cover payment
observation, issuance, transfer, admission consumption, refund acceptance,
the pre-commit resale refusal, reservation cancellation and resale settlement
commit. Follow `caller_observation_ref` for what Commerce received. Use
`producer_evidence_ref` for offline replay diagnostics only.
[Delivery evidence index](COMMERCE_DELIVERY_EVIDENCE_INDEX_V1.json)

Both pre-commit losses keep the original `operationId` and body
`idempotency_key`, with one attempt and zero follow-up calls. All three
pre-commit cases preserve the recorded resale payment, seller ownership,
right version 1 and all five accepted journals. Recovery remains `NOT_BOUND`.
[Pre-commit refusal fixture](../../reference/booking_resale_admission/fixtures/commerce_withheld_resale_refusal_v1.json) ·
[Pre-commit refusal replay](../../reference/booking_resale_admission/test_commerce_withheld_resale_refusal.py) ·
[Transfer lost-reply fixture](../../reference/booking_resale_admission/fixtures/commerce_transfer_lost_reply_v1.json) ·
[Transfer lost-reply replay](../../reference/booking_resale_admission/test_commerce_transfer_lost_reply.py) ·
[Recovery boundary](#unavailable-consumer-bindings)

Commerce keeps `cancel-C` fenced with the original operation ID and body key,
one attempt and zero follow-up calls. The slot state is available to the
offline harness, and recovery remains `NOT_BOUND`.
[Cancellation lost-reply fixture](../../reference/booking_resale_admission/fixtures/commerce_cancel_lost_reply_v1.json) ·
[Cancellation lost-reply replay](../../reference/booking_resale_admission/test_commerce_cancel_lost_reply.py)

Commerce keeps `settle-resale-commit` fenced with the original operation ID
and body key, one attempt and zero follow-up calls. Recovery remains
`NOT_BOUND`. Both histories end before transfer or distribution.
[Commit lost-reply fixture](../../reference/booking_resale_admission/fixtures/commerce_resale_commit_lost_reply_v1.json) ·
[Commit lost-reply replay](../../reference/booking_resale_admission/test_commerce_resale_commit_lost_reply.py)

The grant covers source-informed, synthetic in-memory evidence. N/N−1
compatibility, production qualification and stable SDK release remain outside
its scope. Product TTLs, fees, compensation, market visibility, matching,
pagination and legal, accounting and provider terms remain `UNDETERMINED`
with their recorded owners.

### Commerce calculator

| Boundary | Existing interface |
|---|---|
| Entry points and contracts | [Frozen driver](../../reference/v0.3-rc1/commerce_driver.py), [commerce calculation contract](../COMMERCE_CONTRACTS.md), [CE1](../CANONICAL_ENCODING_V1.md), [S06.1 boundary](../FOUNDATION_S061.md), [client](../../reference/booking_resale_admission/commerce_calculation_client.py) and [console guide](../../reference/booking_resale_admission/README.md#commerce-calculation-console). |
| Transport and lifetime | One bounded CE1 JSON request on stdin and one response per driver process. The reusable calculator client starts a fresh fixed local child per calculation; construction starts nothing. This is not HTTP or a persistent ticket graph. |
| Request and response | Exactly `{action,args}`. Replies contain `ok`, `evidenceClass="CALCULATION_ONLY"`, and `result` or `error`. Amounts are exact atom strings; CE1 rejects lossy numeric encodings. Driver rejection exits 2 with its calculation error; client distinguishes known refusal from transport uncertainty. |
| Action namespace | Only `simulate_quote` (quote request as `args`), `plan_payments` (`quote`, `legs`, `expected_quote_hash`, `now`) and `propose_line_refund` (`quote`, `payment_plan`, `line_ids`, `expected_plan_hash`). These are not additions to the 84 HTTP actions. |
| Identity and replay | Caller supplies full order/version/scope/policy/asset/line/leg identities. Quote/plan hashes bind calculation inputs and results; they provide neither authentication nor execution/idempotency authorization. Repeated calculation neither reserves refund capacity nor prevents repeat payment. No operation-result journal is provided. |
| Prerequisites and authority | Explicit schema-2 quote, complete asset metadata, ordered discounts, payment legs, expected hashes and synthetic `now` as applicable. Console input/composition is separate from explicit `SUBMIT_QUOTE`, `SUBMIT_PLAN`, `SUBMIT_REFUND`. Policy remains **UNDETERMINED — Astra/User**; legal/accounting treatment remains **UNDETERMINED — User/designated advisers**. |
| Evidence and qualification | [Client tests](../../reference/booking_resale_admission/test_commerce_calculation_client.py), especially `test_real_driver_journey_exact_bytes_and_detached_snapshots` and `test_plan_and_refund_bindings_checked_even_with_rehashed_replies`; [driver tests](../../reference/v0.3-rc1/test_commerce_driver.py); [decimal console evidence](../../validation/2026-11-10-plan-local-commerce-decimal-entry/README.md). Source-informed calculation/interface parity only. |
| Unavailable bindings | No booking confirmation, observed payment, refund execution, approved assets or authenticated provider/chain state. Refund proposals retain `executionAuthorized=false`. Booking's separately documented calculated-quote path does not turn this standalone console into booking/payment handoff or an SDK binding. |

### Ticket sessions and consoles

| Boundary | Existing interface |
|---|---|
| Entry points and contracts | [Shared session](../../reference/booking_resale_admission/ticket_operations_session.py), [shared dispatcher/CLI](../../reference/booking_resale_admission/ticket_operations_cli.py), [client](../../reference/booking_resale_admission/ticket_operations_client.py), [combined fixture loader](../../reference/booking_resale_admission/ticket_operations_fixture.py); standalone [booking](../../reference/booking_resale_admission/booking_cli.py), [resale](../../reference/booking_resale_admission/resale_cli.py), [admission](../../reference/booking_resale_admission/admission_cli.py) dispatchers; [booking/resale/admission contract](../contracts/BOOKING_RESALE_ADMISSION_GATES.md) and [settlement contract](../contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md). |
| Transport and lifetime | Importable synchronous sessions or strict JSONL CLI. One shared session/retained local child owns one sequential in-memory settlement/reservation/resale/admission graph. Standalone tools have their documented separate setup/lifetime; console navigation does not submit a command. Exit loses local state. |
| Request and response | Shared: exactly `{surface,operation,arguments}`, with `surface` in `booking`, `resale`, `admission`, `settlement`. Standalone: `{operation,arguments}`. Shared replies retain `surface`, `operation` and the selected `receipt`, `view`, `quote` or `error`; errors retain domain `code` or local exception `type`/`message`. They are not HTTP local-call envelopes. |
| Action namespace | Explicit dispatcher allowlists. Recorded `offer_id` and `presentation_id` selectors (e.g. `list_resale`, `authorize_admission`, `consume`) fetch local synthetic records; `_inputs` methods accept explicit adapter inputs. Neither form is an alias for a prefixed HTTP action. Source-backed issuance, payment, statement and cancellation selectors likewise retain their own prerequisites. |
| Identity and replay | Caller supplies subject IDs and mutation `idempotency_key`. Underlying machines preserve historical first-result receipts (`duplicate=true`, `applied=null`); fresh views can have later phases. Recorded-source paths fetch through the configured source again on replay: a prior success does not bypass a later missing/faulting source. No console cache makes old input current. |
| Prerequisites and authority | Shared fixtures require `fixture_version=1`, `provenance="MOCK_GATE_ONLY"`, explicit ordered `setup`, `offers`, `presentations`; optional `payments`, `cancel_acceptances`, `statements` supply only their documented paths. Timed machines need explicit clocks; issuance/adoption and settlement bindings follow fixture/machine validation. Record entries retain selector identity and exactly one `recorded_text` or `fault`. Missing sources remain errors. Standalone booking starts fresh and requires explicit setup requests; recorded/calculated quote paths require their selected source. Standalone resale/admission require their fixture loaders' setup. No policy, role, expiry, identity or currentness is inferred. |
| Evidence and qualification | [Shared session tests](../../reference/booking_resale_admission/test_ticket_operations_session.py), especially `test_booking_journeys_history_current_state_and_shared_keys` and `test_replay_fetch_failure_and_key_conflicts_leave_shared_graph_unchanged`; [recorded console evidence](../../validation/2026-11-09-plan-local-recorded-ticket-console/README.md); [guide](../../reference/booking_resale_admission/README.md#recorded-offers-and-presentations-in-the-ticket-console). Synthetic source-informed composition; `MOCK_GATE_ONLY`, `IN_MEMORY_FSM` and existing false authority/production flags remain. |
| Unavailable bindings | No authenticated ticket-holder/gate identity, venue admission, chain finality or public read API. Source snapshots and payment observations are assertions, not authenticated facts. Existing clock-skew/post-mutation-fault characterizations do not establish general cross-machine atomicity or rollback. Product policy remains **UNDETERMINED — Astra/User**; legal effects remain **UNDETERMINED — User/legal**. |

### Reward tools

| Boundary | Existing interface |
|---|---|
| Entry points and contracts | [Session](../../reference/token_reward/reward_session.py), [fixture](../../reference/token_reward/reward_fixture.py), [dispatcher](../../reference/token_reward/reward_cli.py), [FSM](../../reference/token_reward/reward_fsm.py), [role/supply contract](../contracts/TOKEN_ROLE_AND_SUPPLY.md), [authority/lifecycle contract](../contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md), [guide](../../reference/token_reward/README.md#reward-desk-scope). |
| Transport and lifetime | Importable session or JSONL CLI; reward subprocess client retains one local child and one in-memory `RewardMachine`. Console also has its documented in-process mode. No automatic restore or external execution. |
| Request and response | `{operation,arguments}`; replies contain `operation`, synthetic `provenance`, and one of `receipt`, `view`, `reward_ids`, `pool_view`, `error`. Domain errors retain codes; malformed local input has separate exception detail. |
| Action namespace | `observe`, `hold`, `mark_eligible`, `submit`, `observe_transfer_effects`, `reconcile_unknown`, `observe_source_cancel`, `observe_krw_refund`, `supersede`; reads `view`, `reward_ids`, `pool_view`. These are local selectors outside the HTTP catalogue. |
| Identity and replay | Mutations require `idempotency_key`; `reward_key` is exactly `program`, `source_op_id`, `recipient`, `kind`. Existing `reward_id` helper derives stable identity; no alias is substituted. Replays return historical receipts, separately from current views. UNKNOWN reconciliation/same-bytes resend requires explicit caller action under existing predicates; no automatic retry. |
| Prerequisites and authority | Fixture version 1, `MOCK_TOKEN_REWARD_ONLY`, all five opening balances; explicit rule, amount, source and approval inputs. `source_view` is caller-supplied (no source FSM is connected), including `COMMITTED`/`KRW` and explicitly false finality flags. `approval_ref`, `signed_bytes_digest`, effects digests, `window_closed` and composed snapshots are synthetic assertions, not authenticated source facts, a real person's approval or observed chain effects. AI approval remains refused. |
| Evidence and qualification | [Session tests](../../reference/token_reward/test_reward_session.py), [FSM tests](../../reference/token_reward/test_reward_fsm.py), [guide's Class B limits](../../reference/token_reward/README.md#synthetic-limitations-and-class-b), [desk evidence](../../validation/2026-11-02-plan-local-reward-desk/README.md). Source-informed mock behavior only; `ISSUED` is an in-memory phase. `token_issued`, `onchain_recorded`, `funds_executed`, `krw_paid`, `chain_finality`, `durable`, `legal_authority` remain false. |
| Unavailable bindings | No settlement-reward binding, token issuance, payout, real approval identity, distributed fence or marketing activation. Amounts/caps/budgets/durations remain **UNDETERMINED — Astra/User**; chargeback timing stays with the payment provider and actual approver designation with User. Existing restore/fingerprint and injected late-failure/no-rollback characterizations remain unresolved. |

### Pool tools

**Repeated accepted references append and change balances again. `source_ref`
and `program_ref` are non-idempotent inputs, not deduplication keys.**

| Boundary | Existing interface |
|---|---|
| Entry points and contracts | [Session/dispatcher](../../reference/token_reward/pool_session.py), [CLI](../../reference/token_reward/pool_cli.py), [client](../../reference/token_reward/pool_client.py), [PoolLedger](../../reference/token_reward/token_reward_model.py), [guide](../../reference/token_reward/README.md#local-pool-accounting-workbench); token contracts linked above provide scope, not an HTTP binding. |
| Transport and lifetime | Importable `PoolSession` or JSONL CLI, one process-local ledger; the client retains one local child. Console fixture/guided initialization and each mutation require explicit confirmation. Exit loses state. |
| Request and response | `{operation,arguments}`. Startup acknowledgement contains `operation="initialize"` and `initialized.opening_balances`, describing caller input without an implicit view. Operation replies contain `operation`, `provenance`, `unit`, `notice`, existing false non-claim flags and `view` or `error`. Successful credit/spend return full balance/credit/spend snapshots, **not transaction receipts**. |
| Action namespace | `credit` with `pool`, `amount`, `source_ref`; `spend` with `pool`, `amount`, `program_ref`; `view` with `{}`. No `idempotency_key` field or reward lifecycle operation. |
| Identity and replay | References are validated model input labels. Repeated accepted `credit`/`spend` calls append another entry and change balances again, subject to ordinary validation/capacity/balance rules. A returned snapshot does not confer first-result/replay protection. Do not transplant HTTP/FSM/reward idempotency assumptions here. |
| Prerequisites and authority | Initialization requires exactly `fixture_version=1`, `provenance="MOCK_TOKEN_REWARD_ONLY"`, `opening_balances` with all five pools: `CUSTOMER_DEPOSIT`, `ORGANIZER_SETTLEMENT`, `REFUND_RESERVE`, `PROTOCOL_REVENUE`, `TOKEN_TREASURY_REWARD`. No inferred balances. File startup or one newline-terminated stdin initialization precedes requests. Only the last two pools are spendable for token simulation. Units are synthetic, non-transferable `POINT_F4`. |
| Evidence and qualification | [Pool tests](../../reference/token_reward/test_pool_session.py), particularly `PoolSessionTests.test_repeated_refs_match_direct_model_and_append_again`; [client tests](../../reference/token_reward/test_pool_client.py); [initialization evidence](../../validation/2026-11-10-plan-local-pool-guided-live-init/README.md). Existing deterministic source-informed model/transport coverage, not a financial-ledger qualification. |
| Unavailable bindings | No RewardMachine, settlement, credit, bank account or token issuance connection. This standalone ledger does not spend reward-session balances. Funding/approval/product balances remain **UNDETERMINED — Astra/User**; accounting/legal treatment remains **UNDETERMINED — User/designated advisers**. No durable receipt, authenticated funding source or consumer finance binding. |

### Supply and collateral tools

| Boundary | Existing interface |
|---|---|
| Entry points and contracts | [Supply dispatcher](../../reference/token_reward/supply_reconciliation.py), [supply client](../../reference/token_reward/supply_client.py), [collateral dispatcher](../../reference/token_reward/collateral_assessment.py), [underlying calculations](../../reference/token_reward/token_reward_model.py), [supply guide](../../reference/token_reward/README.md#local-supply-reconciliation), [collateral guide](../../reference/token_reward/README.md#local-collateral-assessment); token contracts above. |
| Transport and lifetime | Importable pure dispatch/calculation, one-shot CLI input or guided console. Supply's reusable client starts one local CLI child per calculation; the console explicitly selects in-process or subprocess mode. No retained ticket/reward/pool graph is implied. |
| Request and response | `{operation,arguments}`. Replies retain `operation`, `provenance="MOCK_TOKEN_REWARD_ONLY"`, `evidence_class="CALCULATION_ONLY"`, `notice`, and `result` or diagnostic `error` (console cancellation has its documented output). This snake-case label is distinct from the commerce driver's `evidenceClass`; there is no common envelope adapter. |
| Action namespace | Supply: `supply_report` with `events`; `reconcile_supply` with `offchain`, `chain_supply`. Collateral: `collateral_recognized` with `liability_krw`, `collateral_items`. Local selectors, not HTTP commands. |
| Identity and replay | Caller supplies event identities and full reports/items; model validation/duplicate-event rules remain at the source. No external operation identity, transaction receipt, execution deduplication or current-state query is supplied. Recalculation does not mutate a ledger or execute a control. |
| Prerequisites and authority | Explicit synthetic events or the complete supplied offchain report plus `chain_supply`; explicit liability and every collateral item. `chain_supply` is caller-supplied, not queried/authenticated chain supply. `stop_payout` is a reported model flag and executes nothing. No coercion, inferred asset approval, collateral ratio or legal treatment. |
| Evidence and qualification | [Supply dispatch tests](../../reference/token_reward/test_supply_reconciliation.py), [collateral dispatch tests](../../reference/token_reward/test_collateral_assessment.py), [supply client evidence](../../validation/2026-11-10-plan-local-supply-live-console/README.md). Source-informed parity/input/error/fencing evidence only. |
| Unavailable bindings | No mint, burn, payout control, custody, collateral adequacy/eligibility/loan approval, chain query or F04 connection. Supply policy and operational responses remain **UNDETERMINED — Astra/User**; collateral asset selection/ratios remain **UNDETERMINED — Astra/User**, legal enforceability **UNDETERMINED — User/legal**. |

## Identity, replay and uncertainty

The HTTP `operationId`, FSM/reward `idempotency_key`, recorded-source selector,
calculation hash and pool reference occupy different roles. Copying a value
between them creates no binding. Historical receipts describe the first accepted
result; an explicit current `view` can differ (for example `LISTED` versus
`CANCELLED`, or `AUTHORIZED` versus `CONSUMED`). Views cannot authenticate the
source or authorize a new effect. Recorded-ticket replay still fetches its source.

“Live” in these guides means **local subprocess operation**. Ticket/reward/pool
clients retain one child; calculator/supply clients launch per calculation.
See the [ticket client guide](../../reference/booking_resale_admission/README.md#live-local-subprocess-client),
[reward client guide](../../reference/token_reward/README.md#live-subprocess-client),
[pool client guide](../../reference/token_reward/README.md#live-pool-subprocess-client)
and [supply client guide](../../reference/token_reward/README.md#reusable-supply-subprocess-client).
Uncertain exchanges fence the client. They do not authorize automatic retries,
replacement children, alternate identities or a claim that nothing applied.
Known domain refusal and transport uncertainty remain separate. Fencing and
discarding a failed private fixture construction do not prove rollback.

## Authority and prerequisites

[Model 1](../decisions/AUTHORITY_MODEL_1.md) separates chain rights authority,
offchain delegated execution, provider money facts and reservation commitments.
Reservation confirmation, payment observation, rights issuance and admission are
separate facts. Synthetic fixture labels, role strings, source snapshots,
approval records and hashes authenticate none of them. Local successful results
retain their existing provenance and non-claim flags.

Use the linked fixture/setup instructions for the selected interface. Missing
source, clock, policy, quote, identity or approval input is not supplied by this
map. Existing fixture numbers are examples, not product defaults. Source-informed
parity and deterministic replay tests remain local evidence; they do not become
clean-room independence, A2 review or exact-head consumer qualification.

Related local surfaces have their own guides:
[payment lookup](../../reference/provider_facts/README.md),
[credit](../../reference/credit_advance_f04/README.md) and
[AI delegation](../../reference/ai_delegation/README.md). Their local services,
recordings and consoles do not become catalogue bindings by being linked here.
Synthetic payment lookup is explicitly “Analog, NOT Toss”; UNKNOWN/not-found
observations do not authorize a replacement payment. Existing credit/delegation
authority and unresolved decision boundaries remain at their contracts.

## Unavailable consumer bindings

| Gap | Present evidence and boundary | Prerequisite / recorded owner |
|---|---|---|
| Published ticket/finance reads | All 13 approved read names remain **NOT_BOUND** and absent from both command pins. `query_digest`, visibility, modeled cursor error codes and the open-listing phase predicate remain **NOT_BOUND** where recorded. [Read-query draft](../contracts/READ_MODEL_QUERIES.md), [source map](../contracts/READ_MODEL_SOURCE_MAP.md), [candidate fixtures](../../reference/read_model/README.md). | Read-model implementation/publication and applicable producer/consumer qualification are still required. Visibility, limits/defaults, cursor lifetime, sort keys, open phases and retention/history values stay **UNDETERMINED — Astra** as recorded in the source map. Do not send a write as a substitute read. |
| Proposed uncertain-operation recovery lookup | The proposed lookup by operation/trace, subject and source cut remains **NOT_BOUND**. It has no approved query name or route and is separate from the 13 approved reads. [Commerce handoff](COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md#consumer-handoff). | Keep unresolved `UNKNOWN` fenced without polling, retry or replacement writes. |
| Semantic SDK handoff outside the grant | The 56 other actions, unlisted contexts or steps and mismatched tuples remain **HOLD_SEMANTIC**. External consumer acceptance remains **UNVERIFIED**. [Scoped Commerce fixture qualification](#scoped-commerce-fixture-qualification). | Applicable exact tuple qualification and independent consumer evidence. |
| Authenticated observations and durable effects | Local receipts, views, digests and “live” subprocesses supply no authenticated provider/chain source, durable economic transaction or distributed execution authority. | Existing [open inputs](../contracts/FIRST_BATCH_OPEN_INPUTS.md) retain their named User, provider and designated legal/accounting owners; [program locks](../decisions/PROGRAM_DECISIONS_20260928.md) §5 remain. No policy value is selected here. |
| Finance projection/export and Capital ownership | [Finance completion design](../aiops/FINANCE_COMPLETION_DESIGN_KO.md) is **PENDING / unadopted / execution prohibited**. It proposes protocol finance logic here and financial screens in Commerce, explicitly no third repository/program. Separate Capital product/repository ownership was not established in this worktree; neither consumer repository was inspected. Pool/supply/collateral tools do not implement that architecture or a finance ledger. Unsupported consumer methods remain **NOT_BOUND**, release readiness **HOLD**. | **User/Astra** must reconcile any separate Capital interpretation and adopt applicable contracts/dependencies before integration. Accounting/legal classifications remain with User and designated advisers; no adoption, projection/export completion or consumer verification is claimed. |

## Machine-readable consumer binding index

The [machine-readable consumer binding index](COMMERCE_CONSUMER_BINDING_INDEX_V1.json)
is a non-normative navigation record for `kix-commerce-apps`. It binds all 84
published local-call commands (40 core + 44 FSM) and the 13 owner-decided read
names to their pinned source, body-schema reference, gate envelope, offline
journey evidence and exactly one status:

- 40 core commands: **BOOTSTRAP_SCHEMA_BOUND**.
- 44 FSM commands: 27 **MOCK_EVIDENCE** (exercised by the 44-step
  `commerce_journey_conformance_v1.json` fixture) and 17
  **BOOTSTRAP_SCHEMA_BOUND**.
- 13 read names: **NOT_BOUND**; `read-model-reference` is not merged and the
  candidate vectors are not conformance evidence.

The binding index records `catalogue-schema-binding only` and retains its
original **HOLD_SEMANTIC** status. `MOCK_EVIDENCE` covers offline fixtures only.
Use the separate [scoped Commerce fixture qualification](#scoped-commerce-fixture-qualification)
for the listed steps and outcomes. External `kix-commerce-apps` acceptance
stays **UNVERIFIED**. N/N−1 compatibility, production qualification, audit and
User approval each require their own evidence.

The [checker](../../validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py)
re-derives the sets, recomputes every pin, cross-checks the producer tuple and
journey fixture, and refuses drift, an unknown or missing command, a read query
upgraded from `NOT_BOUND` or a semantic claim. It is validation evidence, not a
second contract. This section extends the boundary map; it does not replace any
row or statement above.

The [Commerce companion evidence index](COMMERCE_COMPANION_EVIDENCE_INDEX_V1.md)
and [companion JSON](COMMERCE_COMPANION_EVIDENCE_INDEX_V1.json) connect fourteen
Commerce input/outcome pack families (407 steps) to exact case/step/action
identities, byte pins, outcome references and replay locations. They supplement
navigation within the existing binding index and producer tuple. Use the
[scoped Commerce fixture qualification](#scoped-commerce-fixture-qualification)
to determine which steps have semantic evidence. Other steps remain
`HOLD_SEMANTIC`. The 13 approved reads and the proposed recovery lookup remain
`NOT_BOUND`, SD1 is `OPEN` and User-owned, and external consumer acceptance
remains `UNVERIFIED`.
[Linked refund replay](../../reference/booking_resale_admission/test_commerce_linked_refund_vectors.py)

The admission replay after resale pack carries `HOLD_SEMANTIC`. The original
key returns the historical authorization with `duplicate: true` and
`applied: null`. The fresh version-1 consume returns `STALE_VERSION`. The
current resale owner and the unchanged accepted journals are detached
test-harness observations. The right stays with `buyer-2` at version 2 and no
consumption is recorded.
[Replay guide and command](../../reference/booking_resale_admission/README.md#commerce-admission-replay-after-resale-vectors)

The late-payment pack covers synthetic command refusal, historical cancellation
replay after slot reuse, and the replacement booking's separate payment,
issuance, authorization and consumption. Compensation is `UNDETERMINED` with
Astra and JunTae. Actual provider facts remain subject to the state lifecycle
contract.
[Late payment replay](../../reference/booking_resale_admission/test_commerce_late_payment_after_cancel_vectors.py) ·
[State lifecycle §3](../contracts/STATE_LIFECYCLE.md#3-lc-fact--늦은-사실-보존)

The payment-reference scope pack records a same-show resale conflict, a
distinct resale payment and explicit transfer, and a second-show primary
payment using the original reference bytes. Both shows run in the same
in-memory host. [Payment-reference replay](../../reference/booking_resale_admission/test_commerce_payment_ref_scope_vectors.py) ·
[Builder validation](../../validation/2026-11-20-plan-commerce-payment-ref-scope/README.md)

The resale buyer-hold release pack records the `BUYER_MISMATCH` refusal,
release back to `LISTED`, and historical release replay after the same buyer
acquires a fresh hold. Payment observation and transfer have separate receipts.
The `resale_release_hold` binding remains `BOOTSTRAP_SCHEMA_BOUND`, and the pack
carries `HOLD_SEMANTIC` as non-normative mock evidence.
[Buyer-hold release replay](../../reference/booking_resale_admission/test_commerce_resale_buyer_release_vectors.py) ·
[Builder validation](../../validation/2026-11-20-plan-commerce-resale-buyer-release/README.md)

## Evidence and non-claims

Behavioral statements above cite existing contracts, dispatchers and tests;
historical validation links retain their original dates and scope. The
[boundary map validation record](../../validation/2026-11-10-audit29-consumer-surface-boundary-map/README.md)
records the original map's checks. Existing class B uncertainty remains
characterization.

The tuple's `OPEN` / `User` entry records the October SD1 stop. The handoff
records the November verifier evidence, and JunTae owns formal ledger
disposition. See the [October stop](OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md)
and the [SD1 handoff validation record](../../validation/2026-11-19-plan-producer-sd1-evidence-handoff/README.md).

No new schema, alias, adapter, protocol command, policy value, finance architecture,
production runtime, real funds/provider call, public endpoint, Sui testnet/mainnet,
storage engine, replication/consensus or coin/TIX module. No claim of production
readiness, durability, bank exactly-once, chain finality, legal compliance or
protocol completeness. A2 non-author exact-final-head review and exact-head KTX/KIX
CI remain separate delivery gates; this document is not a merge-ready verdict.
