# Synthetic local admission presentations

`PresentationAdapter` connects synthetic command inputs to an existing,
caller-configured `AdmissionMachine`. The machine retains its reservation,
ownership and settlement checks from
[BOOKING_RESALE_ADMISSION_GATES.md §11](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#11-검표-자격-수락-상태-기계).
No FSM, contract, protocol command, HTTP, SDK or catalogue changes are involved.

## Interfaces

`PresentationSource.fetch(presentation_id, *, operation)` returns a dictionary
or `None`. `operation` is `authorize_admission` or `consume`, naming existing
Python methods, not new wire commands. Exact record fields are:

| Operation | Fields |
|---|---|
| authorize_admission | right_id, version, holder_role, request |
| consume | right_id, version, request |

`PresentationAdapter(machine, source)` provides two separate explicit methods:

```python
adapter.authorize_admission(
    presentation_id, admission_id=admission_id, idempotency_key=authorization_key,
    gate_role=gate_role, expires_ms=expires_ms,
)
adapter.consume(
    presentation_id, consume_id=consume_id, idempotency_key=consumption_key,
    gate_role=gate_role,
)
```

All caller parameters are mandatory. Each invocation fetches exactly once,
including replay. Missing input raises `PresentationNotFound`; malformed input
or caller scalar shapes raise `InvalidPresentationRecord`; source faults raise
`PresentationSourceError`. These are local exceptions with no protocol codes.
Validation finishes before accessing the FSM or binding its idempotency key.
Fetch exceptions are caught only around fetch. Delegation returns the FSM's
receipt and propagates its errors unchanged. The presentation selector never
enters FSM arguments or fingerprints. There is no retry, fallback, receipt cache,
automatic consume, clock setting or credential adoption in the adapter.

`FakePresentationSource(recordings=...)` copies a mapping keyed by
`(operation, presentation_id)` with JSON-text or `SyntheticPresentationFault`
values. Its recordings are read-only; calls are tuple snapshots; each fetch
parses a detached object. Malformed JSON, duplicate keys, non-JSON constants and
non-object roots are rejected. ERROR and TIMEOUT markers fail immediately with
no sleeping, I/O or external calls.

## Coverage before adding tests

The following mapping was recorded before adding adapter/source tests. Existing
coverage was inspected in `test_admission_fsm.py`, `test_returned_data_isolation.py`,
`test_admission_rejection_atomicity.py` and the
[clause map](../../docs/status/BRA_CONTRACT_EVIDENCE_MAP.md).

| Requirement | Existing coverage classification | Gap addressed by new evidence |
|---|---|---|
| Explicit authorize then one consume; duplicate has no effect | Sufficient FSM coverage: `AdmissionFsmTests.test_issued_credential_is_consumed_once_and_replay_does_not_bump_version` | Partial overall: adapter delegation and runnable journey |
| Receipts, errors, first-result replay and key conflicts | Sufficient FSM coverage: same test, `test_returned_data_isolation.py` and rejection atomicity tests | Partial overall: adapter/direct equivalence and exception identity |
| Stale holder/version, transferred credentials | Sufficient FSM coverage: `test_transfer_then_entry_rejects_both_presentations`, refusal/atomicity cases | Partial overall: same refusals through source inputs |
| Live listing and expired authorization | Sufficient FSM coverage: `test_listing_and_cancel_order_against_entry`, `test_expired_authorization_is_replaced_once` | Partial overall: adapter path |
| Configured authorities and mock-only false flags | Sufficient scoped FSM coverage: `test_external_sources_fail_closed_without_being_read`, `test_settlement_commit_is_not_entry_and_a_granted_flag_rejects`, `test_open_items.py` | Partial overall: delegation preserves bindings/flags |
| Exactly one fetch, no retry/fallback/cache | Not covered | Source call counts for both operations and every outcome |
| Immutable recordings and detached fetch/history | Not covered | Constructor mutation, fetched mutation, read-only mapping and history snapshots |
| Missing/malformed/fault rejection before FSM access/key binding | Not covered | Zero-call spy, unchanged real-machine states/journals and same-key valid acceptance |
| Discovery and documentation wiring | Existing checkers cover repository structure | New test modules discovered and documentation indexed |

New `test_presentation_source.py` and `test_presentation_adapter.py` are
source-informed local regression evidence, not independent verification.

## Example and verification

From repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 reference/booking_resale_admission/example_presentation_adapter.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/reference/booking_resale_admission" \
  python3 -m unittest test_presentation_source test_presentation_adapter
```

The example constructs actual local settlement, reservation, resale and admission
machines, injects clocks, records synthetic payment, commits mock settlement,
issues and adopts a ticket. It explicitly authorizes, checks that consumption has
not happened, consumes and repeats the consume. Fixture amounts, fee policy,
gate labels and expiry are illustrative choices, not product defaults.

The [execution record](../../validation/2026-10-31-plan-local-admission-presentation-adapter/README.md)
records selected socket-free admission regressions and applicable CI equivalents.
Workflow discovery includes `test_*.py`; the unchanged HTTP suite remains required
in normal exact-final-head CI. No local full-suite success is claimed.

## Limitations

P03 remains **설계중**. Production policy, identity, revocation, independent
currentness and approved admission timing remain **UNDETERMINED**, with
Astra/User and existing contract owners. The source only supplies synthetic
command inputs; it cannot authorize venue identity, revocation or currentness.
Old and transferred credentials are both refused without reissuance. Receipts
retain `MOCK_GATE_ONLY`, `IN_MEMORY_FSM`, `NON_CLAIMS`, false offline/reissue/
production flags and `external_admission="UNSUPPORTED"`.

Existing class-B clock-skew and post-mutation fault characterizations remain;
pre-delegation validation does not establish general cross-machine atomicity.
This is in-memory, sequential mock evidence: no persistence, hardware, credentials,
external calls, production runtime, funds, chain finality, venue exactly-once or
runtime activation. Non-author exact-head review and KTX/KIX checks are separate
supervisor steps, not builder self-assessments.

## Reusable admission session and JSONL CLI

`AdmissionSession(machine, source)` is importable with this directory on
`PYTHONPATH`. It delegates to the merged adapter and the caller's actual
`AdmissionMachine`, preserving its configured sources, exceptions and receipts.
It has no receipt cache or independent lifecycle. Each call performs only the
requested operation. This is a sequential local session, not a delegated venue
credential or a protocol session command.

```python
from admission_fixture import load_fixture

session = load_fixture("reference/booking_resale_admission/fixtures/admission_session.json")
receipt = session.authorize_admission(
    "ticket-1", admission_id="entry-1", idempotency_key="entry-key-1",
    gate_role="gate-a", expires_ms=1_060_000,
)
assert session.view("issue-1")["version"] == 1
# A separate caller request is necessary to consume.
consumed = session.consume(
    "ticket-1", consume_id="consume-1", idempotency_key="consume-key-1", gate_role="gate-a",
)
```

The nine public methods and all required arguments are:

| Local method selector | Arguments |
|---|---|
| `adopt_issued` | Complete explicit adoption input listed in [fulfillment](#explicit-ticket-fulfillment-on-the-shared-desk), including `idempotency_key` |
| `authorize_admission` | `presentation_id`, `admission_id`, `idempotency_key`, `gate_role`, `expires_ms` |
| `consume` | `presentation_id`, `consume_id`, `idempotency_key`, `gate_role` |
| `authorize_admission_inputs` | `admission_id`, `idempotency_key`, `right_id`, `version`, `holder_role`, `gate_role`, `request`, `expires_ms` |
| `consume_inputs` | `consume_id`, `idempotency_key`, `right_id`, `version`, `gate_role`, `request` |
| `view` | `right_id` |
| `view_credential` | `right_id`, `version`, `holder_role` |
| `reconcile` | `right_id`, `idempotency_key` |
| `set_clock` | `subject_id`, `idempotency_key`, `now_ms` |

Recorded Python authorization/consumption accept a positional presentation ID and the
remaining arguments as keyword-only, matching the adapter. Views, reconciliation and clock
changes delegate directly to the existing machine. `set_clock` retains the
machine's reservation clock delegation and does not advance the resale clock.
No wall clock is consulted. A duplicate first-result receipt may still say
`AUTHORIZED` after a fresh `view` says `CONSUMED`; the session does not replace
one with the other.

### Fixture input

`admission_fixture.load_fixture(path)` strictly decodes the caller's JSON and
constructs fresh `SettlementMachine()`, `ReservationMachine(settlement_source=book)`,
`ResaleMachine(ticket_source=tickets)` and
`AdmissionMachine(ticket_source=tickets, ownership_source=resale, settlement_source=book)`.
It returns the session only after every explicit setup operation succeeds.
The fixture is synthetic setup input, not saved session state or persistence.

The top-level object requires exactly `fixture_version: 1`,
`provenance: "MOCK_GATE_ONLY"`, `setup` and `presentations`. Unknown fields,
duplicate JSON keys, non-finite numbers, wrong shapes and unsupported versions
are rejected with `FixtureError`, a local exception without a protocol code.
The [complete fixture](fixtures/admission_session.json) supplies every value;
none is an approved product default.

`setup` is a nonempty ordered array of objects with exactly `machine`,
`operation`, `subject_id`, `idempotency_key` and `body`. Each body must include
exactly the existing method's keyword parameters other than `idempotency_key`,
including normally optional `currency`, `adjustment_reason`, `reservation_id`
and `quote_ref`. The subject ID is passed as the method's first argument.
Only these explicit setup operations are accepted:

| Machine | Setup operations |
|---|---|
| settlement | `initiate`, `authorize`, `capture`, `commit` |
| reservation | `set_clock`, `register_show`, `hold`, `confirm`, `observe_payment`, `bind_settlement`, `issue` |
| resale | `set_clock`, `adopt_issued` |
| admission | `set_clock`, `adopt_issued` |

Every timed machine requires its own explicit initial clock before its other
setup operations. Every issued right requires both resale and admission
adoption, a confirmed reservation and an explicit settlement binding.
Adoption and confirmation require non-null reservation and quote identifiers
for this fixture interface. The FSMs validate the actual setup order, bindings,
amounts, clocks and policies; their rejections propagate unchanged. Invalid
setup discards the local graph without exposing a partial session. This does
not add cross-machine rollback semantics.

`presentations` is an array of objects with `operation`, `presentation_id` and
exactly one of `recorded_text` or `fault`. The first two fields form the unique
recording identity. `operation` is `authorize_admission` or `consume`.
`recorded_text` is JSON **text** using the adapter's record fields above; it is
preserved for source validation at fetch time. `fault` is one of
`synthetic_presentation_error` or `synthetic_presentation_timeout`, the existing
immediate synthetic fault markers. Missing recordings remain missing. The
loader never manufactures presentations, identifiers, keys, policy or clocks.

### Runnable transcript

From repository root:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/reference/booking_resale_admission"
python3.12 reference/booking_resale_admission/admission_cli.py \
  --fixture reference/booking_resale_admission/fixtures/admission_session.json \
  --requests reference/booking_resale_admission/fixtures/admission_requests.jsonl
# Expected exit: 1, because the transcript contains three explicit rejections.
```

`--requests -` reads JSONL from stdin in the same process. Each line requires
exactly `{"operation": METHOD, "arguments": {...}}`, with all arguments in the
table above. These are local method selectors, not wire commands or a read
catalogue. Blank lines, unknown fields/methods and missing arguments are
malformed input. No request or key is generated implicitly.

One JSON object is emitted per supplied request, containing `operation` and
`receipt`, `view` or `error`. Domain errors retain `error.code`; local exceptions
use `error.type` and `error.message`, without an invented protocol code.
A domain or presentation rejection permits processing the next explicitly
supplied line, with no retry or follow-up request. Malformed JSON/schema stops
processing immediately; earlier explicit operations in that process may
already have occurred. Setup failures produce one error and process no requests.
Exit codes are 0 for all-success input, 1 for request rejections, and 2 for
malformed input/setup or input-file errors. Unexpected programming failures
remain visible as exceptions.

The fixture transcript produces these observable results:

| Line | Request | Expected result |
|---|---|---|
| 1 | view ticket 1 | `ELIGIBLE`, version 1 |
| 2–4 | authorize; view; view credential | `AUTHORIZED`, version 1; fresh presentation, no consumption |
| 5 | explicit consume | `CONSUMED_ONCE`, version 2 |
| 6 | same consume and key | duplicate receipt, no new journal entry/effect |
| 7–8 | same authorization; current view | first `AUTHORIZED` receipt versus current `CONSUMED` view |
| 9 | authorization key with a different gate | `IDEMPOTENCY_CONFLICT` |
| 10 | ticket 2 stale version | `STALE_VERSION` |
| 11–12 | authorize ticket 2; explicitly advance admission clock | authorization then its expiry boundary |
| 13–14 | consume ticket 2; view | `ADMISSION_EXPIRED`; version 1, still unconsumed |

### Session coverage and validation

The [execution record](../../validation/2026-11-02-plan-local-admission-session-cli/README.md)
contains the requirement-by-requirement coverage mapping recorded before new
tests, commands/results and the exact socket-free admission selection.
`test_admission_session.py` fills session delegation, source-failure/no-follow-up,
clock forwarding, first-receipt/current-view and retained flag gaps.
`test_admission_cli.py` fills strict fixture/input validation, reusable loading,
CLI subprocess/stdin, transcript/replay and exit-status gaps. These tests use
actual configured local FSMs, plus boundary spies and immediate synthetic faults.

```bash
python3.12 -m unittest test_admission_session test_admission_cli
python3.12 -m unittest test_presentation_source test_presentation_adapter
```

Normal non-author exact-final-head review/A2 and completed/success KTX and KIX
workflows, including the unchanged HTTP suite, remain necessary before merge.
Local results do not claim full booking-suite success. The limitations above
remain: P03 is **설계중**; production timing, identity, revocation and independent
currentness remain **UNDETERMINED**, owned by Astra/User and contract owners.
No automatic consume, retry, polling, reissue, persistence, HTTP, frontend,
protocol command, read catalogue, runtime activation or policy decision is added.

## Request-time admission inputs

A running `AdmissionSession` also accepts synthetic presentation data directly,
without a startup recording. These two local Python selectors call the existing
public FSM once each; they add no protocol commands. Recorded
`authorize_admission` / `consume` keep their adapter and source-fetch behavior.

```python
from admission_fixture import load_fixture

session = load_fixture("reference/booking_resale_admission/fixtures/admission_request_inputs_session.json")
authorized = session.authorize_admission_inputs(
    "entry-1", idempotency_key="entry-key", right_id="issue-1", version=1,
    holder_role="buyer-1", gate_role="gate-a", request="11" * 32, expires_ms=1060000,
)
# Authorization leaves version 1; consuming requires this separate call.
consumed = session.consume_inputs(
    "consume-1", idempotency_key="consume-key", right_id="issue-1", version=1,
    gate_role="gate-a", request="11" * 32,
)
```

The signatures take `admission_id` or `consume_id` first, followed by mandatory
keyword-only fields listed in the admission method table. All values are
forwarded unchanged. The FSM validates identifiers/roles, integer version/expiry
(excluding bool) and the opaque lowercase 64-hex-character `request`; there is
no credential issuance or cryptographic verification here. No `presentation_id`
or `external_dependency` is accepted by these selectors.

Each standalone JSONL line has exactly `operation` and `arguments`:

```json
{"operation":"authorize_admission_inputs","arguments":{"admission_id":"entry-1","idempotency_key":"entry-key","right_id":"issue-1","version":1,"holder_role":"buyer-1","gate_role":"gate-a","request":"1111111111111111111111111111111111111111111111111111111111111111","expires_ms":1060000}}
{"operation":"consume_inputs","arguments":{"consume_id":"consume-1","idempotency_key":"consume-key","right_id":"issue-1","version":1,"gate_role":"gate-a","request":"1111111111111111111111111111111111111111111111111111111111111111"}}
```

The shared desk accepts the same lines with exactly one extra envelope field,
`"surface":"admission"`; its Python methods are
`desk.admission.authorize_admission_inputs(...)` and
`desk.admission.consume_inputs(...)`. Both selectors emit `receipt` and retain
the supplied selector in `operation`. Domain errors retain their existing
`error.code`, including malformed semantic input; they are not adapter
`InvalidPresentationRecord` errors. Unknown/missing fields, wrong shapes,
duplicate keys and nonfinite JSON stop with exit 2. Domain refusals continue
only on supplied lines and yield exit 1; all-success streams yield exit 0.

The [standalone fixture](fixtures/admission_request_inputs_session.json) and
[shared fixture](fixtures/ticket_operations_admission_inputs_session.json) use
fixture version 1, `MOCK_GATE_ONLY`, complete bound setup and `presentations: []`.
The shared fixture also has `offers: []`. The clocks, amounts and expiry values
are synthetic examples, never product defaults. From repository root:

```bash
export PYTHONDONTWRITEBYTECODE=1
for pair in admission:admission_request_inputs ticket_operations:ticket_operations_admission_inputs; do
  desk="${pair%%:*}"
  transcript="${pair#*:}"
  python3.12 "reference/booking_resale_admission/${desk}_cli.py" \
    --fixture "reference/booking_resale_admission/fixtures/${transcript}_session.json" \
    --requests "reference/booking_resale_admission/fixtures/${transcript}.jsonl"
  python3.12 "reference/booking_resale_admission/${desk}_cli.py" \
    --fixture "reference/booking_resale_admission/fixtures/${transcript}_session.json" \
    --requests - < "reference/booking_resale_admission/fixtures/${transcript}.jsonl"
done
```

Both transcripts intentionally exit 1. The standalone 15-line stream includes
consume-before-authorization, wrong gate/request, separate consumption, replay
of both first receipts, a changed-input conflict, fresh competing consumption,
and explicit clock advancement followed by expired consumption. The shared
19-line stream lists and cancels explicitly, retains the first `LISTING_LOCKED`
refusal, authorizes with a fresh key, consumes separately and replays. It then
transfers the second right through explicit resale operations and refuses old
version/holder and moved-credential admission inputs without reissuance.

No presentation is fetched, identity/version inferred or refreshed, clock
changed, view treated as admission authority, or next operation invoked by the
direct methods. Bound reservation, ownership and settlement checks remain in
the FSM. Replay shares the recorded path's first-result identity and returns
historical receipts; views remain observations. Product policy stays
**UNDETERMINED — Astra/User**; legal effects stay **UNDETERMINED — User/legal**.
P03 remains design-stage. No network, hardware, credentials, persistence or
activation is added. See the [validation record](../../validation/2026-11-04-plan-local-admission-request-inputs/README.md)
for source-informed coverage, local results and outstanding review/CI gates.

## Synthetic local resale offers

`ResaleOfferSource.fetch(offer_id)` supplies one dictionary or `None`.
`ResaleOfferAdapter(machine, source)` accepts a caller-configured
`ResaleMachine` and exposes only this explicit listing operation:

```python
adapter.list_resale(offer_id, listing_id="list-1", idempotency_key="list-key")
```

The exact `ResaleOfferRecord` schema is:

| Field | Shape |
|---|---|
| `offer_id` | Required identifier equal to the requested selector |
| `right_id`, `seller_role`, `recipient_role` | Required identifiers |
| `version` | Required nonnegative integer, excluding bool |
| `amount` | Required positive integer within existing `_money` bounds |
| `expires_ms` | Required integer within existing `_ms` bounds |
| `reservation_id` | Optional identifier or null; omission forwards `None` |

Identifiers use the existing `_ident` bounds. Unknown fields are refused,
including listing IDs, idempotency keys, payment fields and authority flags.
Listing identity and key always come from the caller. The offer selector is
local metadata and never enters FSM arguments or fingerprints.

Each explicit invocation fetches exactly once, including replay and malformed
caller arguments. Missing input raises `ResaleOfferNotFound`; malformed records,
mismatched selectors and invalid caller shapes raise `InvalidResaleOfferRecord`;
source faults raise `ResaleOfferSourceError`. These local exceptions carry no
protocol codes. Validation finishes before accessing any FSM method or binding
its key. Fetch exceptions are caught only around fetch; FSM receipts are returned
directly and FSM exceptions propagate unchanged. There is no retry, polling,
cache or fallback. A source failure on replay remains a source failure.

The adapter checks scalar shape, not ownership, version currency, price cap,
expiry against a clock, live listings or admission locks. Those decisions and
retained first-result semantics belong to the existing FSM
([contract §10](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#10-리셀-수락-상태-기계)).
A valid record can therefore be refused by the FSM and retain a rejection key;
a malformed record never reaches that boundary. Omitted and null reservation
bindings both forward `None`, leaving authority resolution to the FSM.

`FakeResaleOfferSource(recordings=...)` copies a mapping from offer IDs to
immutable JSON strings or `SyntheticResaleOfferFault.ERROR/TIMEOUT` markers.
The mapping is read-only; each fetch decodes a detached object; `calls` returns
a tuple snapshot. Duplicate JSON keys, non-finite constants, malformed JSON and
non-object roots are refused. Synthetic faults raise immediately without I/O.

### Resale coverage and example

Coverage was mapped before adding the new tests:

| Requirement | Existing coverage | New gap evidence |
|---|---|---|
| Ownership/version/price/expiry and competing listing | Sufficient scoped FSM behavior: `test_resale_fsm.py::ResaleFsmTests.test_stale_listing_policy_and_expiry_do_not_transfer`, `test_buy_hold_is_optional_and_cancel_order_decides_the_race` | Partial overall: `test_resale_offer_adapter.py` compares direct and adapted receipts/errors, states, digests and journals |
| Replay, rejection atomicity, admission locks and mock flags | Sufficient scoped FSM behavior: `test_restore_replays_one_transfer_and_omits_rejections`, `test_external_attempts_do_not_journal`, generated `ResaleRejectionAtomicityTests.test_list_resale_*_leaves_no_trace` | Partial overall: exact forwarding, exception identity, replay after expiry and retained rejections through the adapter |
| Single fetch, immutable recordings, detached outputs | Not covered for resale source | `test_resale_offer_source.py` and adapter call-count/fault tests |
| Missing/malformed/mismatched/fault inputs touch no FSM or key | Not covered for resale source | No-access guard, real-machine snapshots/journals, zero method calls and valid acceptance with the same key |
| Runnable listing boundary | Not covered | `example_resale_offer_adapter.py` and its regression test |

From repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3.12 reference/booking_resale_admission/example_resale_offer_adapter.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/reference/booking_resale_admission" \
  python3.12 -m unittest test_resale_offer_source test_resale_offer_adapter
```

The example constructs actual `ReservationMachine` and `ResaleMachine`
instances, registers a synthetic show, issues and adopts a ticket, then explicitly
lists and separately attempts a competing listing, displaying `RIGHT_SALE_LOCKED`.
Setup injects an already-observed primary-payment fact; it initiates no payment.
After setup the journey performs no hold, resale-payment or transfer command,
and leaves holder/version unchanged. All amounts, expiry and role labels are
synthetic fixture choices, not approved policy. Actual checks and limitations
are in the [resale execution record](../../validation/2026-11-02-plan-local-resale-offer-source/README.md).

R01/R05 remain partial and **설계중**. Product policy stays **UNDETERMINED** with
Astra/User; legal/privacy inputs retain User and legal/privacy owners, tax and
accounting retain User and tax/accounting owners, and Toss inputs retain User
and the named Toss technical/sales owners in
[§7.1](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#71-이-노드가-분류하는-항목).
This source-informed single-process mock adds no payment lookup handoff,
automatic hold/payment/transfer, seller payout, marketplace authentication,
external calls or persistence. Existing Class B internal-fault and clock-skew
characterizations remain; no general rollback guarantee is added. No real funds,
provider/chain verification, independent currentness, cross-channel exclusion,
legal compliance or production readiness is claimed. Non-author exact-final-head
review and successful KTX/KIX CI remain required before merge.

## Reusable resale session and JSONL CLI

`ResaleSession(machine, source)` is importable with this directory on
`PYTHONPATH`. Supply an existing configured `ResaleMachine` and
`ResaleOfferSource`. Only `list_resale` calls the existing offer adapter, once
per explicit invocation, including replay. Every other method forwards to the
configured machine and returns its receipts/views unchanged. No session receipt
cache, generated identifiers, automatic retries or implicit lifecycle actions
are added. The caller explicitly chooses every mutation's idempotency key.

| Session method / local CLI selector | Arguments besides mandatory `idempotency_key` on mutations |
|---|---|
| `adopt_issued` | Complete explicit adoption input listed in [fulfillment](#explicit-ticket-fulfillment-on-the-shared-desk) |
| `list_resale` | `offer_id`, `listing_id` |
| `list_resale_inputs` | `listing_id`, `right_id`, `version`, `seller_role`, `recipient_role`, `amount`, `expires_ms`, `reservation_id` (explicit value or `None` / JSON `null`) |
| `hold_buy` | `hold_id`, `listing_id`, `buyer_role` |
| `release_hold` | `hold_id`, `buyer_role` |
| `cancel_listing` | `listing_id`, `seller_role` |
| `observe_recorded_payment` | `recording_id`, `listing_id` (optional configured synthetic payment source required) |
| `observe_resale_payment` | `listing_id`, `payment_ref`, `amount`; optional `buyer_role` (default `None`) |
| `bind_settlement` | `listing_id`, `settlement_id` |
| `accept_resale` | `transfer_id`, `listing_id` |
| `close` | `listing_id` |
| `reconcile` | `listing_id`; mandatory caller key, process-local receipt bookkeeping |
| `set_clock` | `subject_id` (`"clock"`), `now_ms`; advances resale only |
| `view` | `listing_id`; no key |
| `view_right` | `right_id`; no key |
| `view_presentation` | `right_id`, `version`, `holder_role`; no key |

These are existing Python method selectors, not new protocol commands or a
read catalogue. FSM scalar validation and existing errors remain authoritative.
In Python the first identity may be positional, and the remaining arguments
are keyword-only. For example:

```python
from resale_fixture import load_fixture

session = load_fixture("reference/booking_resale_admission/fixtures/resale_session.json")
receipt = session.list_resale("offer-1", listing_id="list-1", idempotency_key="list-key")
current = session.view("list-1")
```

### Request-time resale inputs

`session.list_resale_inputs(listing_id, *, right_id, version, seller_role,
recipient_role, amount, expires_ms, idempotency_key, reservation_id)` lists an
already-adopted right using the caller's complete inputs. All nine fields are
mandatory, including `reservation_id`: supply an explicit binding or `None`
(`null` in JSON). The method forwards values unchanged in exactly one
`ResaleMachine.list_resale` call. It fetches no offer or payment recording and
performs no preflight, coercion, clock advancement, retry or follow-up.
Ownership, version, reservation authority, price limits, expiry, admission/sale
locks and retained first-result replay stay FSM-owned. A null binding is passed
literally; any authority resolution belongs to the FSM.

Standalone JSONL uses exactly this envelope and these argument fields:

```json
{"operation":"list_resale_inputs","arguments":{"listing_id":"request-list-1","right_id":"issue-1","version":1,"seller_role":"buyer-1","recipient_role":"buyer-2","amount":8000,"expires_ms":1120000,"idempotency_key":"request-list-key","reservation_id":null}}
```

For `ticket_operations_cli.py`, add exactly `"surface":"resale"` to the outer
object. Missing/extra fields (including `offer_id`) and non-object envelopes or
arguments are rejected before dispatch. Scalar semantics remain FSM-owned.
Results contain `operation` and `receipt`; the shared desk also returns
`surface`. Errors and exit conventions are unchanged: **0** for all success,
**1** for domain/source refusals (only supplied later lines continue), **2** for
structural/input failures (stop immediately). The existing recorded-offer
`list_resale(offer_id, ...)` method remains available; identical FSM inputs and
keys share its replay identity. This local selector adds no protocol command.

The new fixtures contain `offers: []` and explicit synthetic issuance/adoption.
Each transcript lists, replays, explicitly holds/releases/cancels, replays the
original listing receipt and reads current state. From the repository root:

```bash
export PYTHONDONTWRITEBYTECODE=1
for desk in resale ticket_operations; do
  python3 "reference/booking_resale_admission/${desk}_cli.py" \
    --fixture "reference/booking_resale_admission/fixtures/${desk}_request_inputs_session.json" \
    --requests "reference/booking_resale_admission/fixtures/${desk}_request_inputs.jsonl"
  python3 "reference/booking_resale_admission/${desk}_cli.py" \
    --fixture "reference/booking_resale_admission/fixtures/${desk}_request_inputs_session.json" \
    --requests - < "reference/booking_resale_admission/fixtures/${desk}_request_inputs.jsonl"
done
```

Both journeys exit **0**. Every subsequent payment, transfer, settlement or close
requires its own explicit request. There are no services, credentials,
persistence, authentication, external execution, activation or policy defaults.
Fixture amounts/times/roles are synthetic examples, not product policy.
Product policy remains **UNDETERMINED — Astra/User**; legal effects remain
**UNDETERMINED — User/legal**. The [validation record](../../validation/2026-11-04-plan-local-resale-request-inputs/README.md)
maps existing coverage and records local evidence, limitations and pending review/CI.

### Synthetic resale fixture schema

`resale_fixture.load_fixture(path)` accepts exactly `fixture_version: 1`,
`provenance: "MOCK_GATE_ONLY"`, `setup`, and `offers`, plus optional `payments`
(documented below). No policy values or clocks
are defaulted. Setup entries have exactly `machine`, `operation`, `subject_id`,
`idempotency_key`, `body`. The setup allowlist is:

- `settlement`: `initiate`, `authorize`, `capture`, `commit`.
- `reservation`: `set_clock`, `register_show`, `hold`, `confirm`,
  `observe_payment`, `bind_settlement`, `issue`.
- `resale`: `set_clock`, `adopt_issued`.

Body fields exactly match the corresponding `admission_fixture._SETUP` schema
for those three machines; no admission setup is accepted. The complete
[synthetic fixture](fixtures/resale_session.json) shows every field. Both
reservation and resale clocks must be explicitly set before their other setup
operations. Each issued right needs matching prior confirmation/issuance and
resale adoption with non-null reservation/quote identifiers; the actual FSM
checks show, slot, price, payment and issuance equality. Settlement binding is
optional for issuance and resale. No settlement setup is required for UNBOUND
flows. `PRIMARY_FEE_BPS` (`kind`, `fee_bps`, `residual_payee`, `fee_payee`) is
caller-supplied synthetic settlement policy, never derived from resale allocation.

Each offer entry has `offer_id` plus exactly one of `recorded_text` or `fault`.
Duplicate offer identities are refused. `recorded_text` is JSON text with the
existing offer fields documented above; validation on fetch belongs to the
existing source/adapter. Supported immediate fault values are
`synthetic_resale_offer_error` and `synthetic_resale_offer_timeout`.

Structure is validated before construction. The loader builds fresh actual
`SettlementMachine`, `ReservationMachine(settlement_source=book)` and
`ResaleMachine(ticket_source=tickets, settlement_source=book)` instances and
executes setup sequentially through public APIs. It publishes a session only
after setup succeeds. This private construction is not cross-machine rollback.
It does not change existing rejection behavior or clock-skew characterizations.

### Runnable resale transcript

From repository root:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/reference/booking_resale_admission"
python3 reference/booking_resale_admission/resale_cli.py \
  --fixture reference/booking_resale_admission/fixtures/resale_session.json \
  --requests reference/booking_resale_admission/fixtures/resale_requests.jsonl
python3 -m unittest test_resale_session test_resale_cli
```

Use `--requests -` for stdin. Each line has exactly this shape:

```json
{"operation":"hold_buy","arguments":{"hold_id":"buy-hold","listing_id":"list-1","buyer_role":"buyer-2","idempotency_key":"buy-key"}}
```

The included transcript emits twelve rows, exits 0 and explicitly lists, holds,
records synthetic payment, binds the preconfigured committed mock settlement,
transfers, repeats transfer, closes, repeats transfer again and reads all three
views. Only one transfer is journaled; current version is 2, generation stays 1.
Replay after closure still returns the first `TRANSFERRED` snapshot with
`duplicate: true`, `applied: null`; current `view` says `CLOSED`. The old holder's
presentation no longer matches; the new holder/version matches the local right.
That match does not reissue a venue credential.

Payment observation never binds or commits settlement and never transfers.
Binding never observes payment, calls settlement commands or transfers. Transfer
never closes. UNBOUND transfer remains supported with
`mock_settlement_commit_observed: false`. Bound uncommitted settlement fails with
`SETTLEMENT_NOT_COMMITTED`, leaving settlement and ownership unchanged. To
exercise it, omit only the `settlement` `commit` setup entry in a separate caller
fixture, then supply the transcript through its first transfer. Competing
listings, stale holder/version, expiry and cancellation after payment retain
`RIGHT_SALE_LOCKED`, `NOT_HOLDER`, `STALE_VERSION`, `LISTING_NOT_OPEN` and
`COMPENSATION_UNDEFINED` respectively.

Output is one JSON object per request: `{"operation": ..., "receipt": ...}`,
`{"operation": ..., "view": ...}` or `{"operation": ..., "error": ...}`.
Domain errors preserve `{"code": error.code}`; fixture/source failures use
`{"type": ..., "message": ...}`. Exit 0 means all requests succeeded; exit 1
means a domain/source rejection occurred, with later operations possible only
from later explicit input lines. Structural/fixture/file/usage failure exits 2;
a malformed request stops the stream immediately. Unknown selectors, extra or
missing arguments, invalid roots, duplicate keys at every depth, malformed JSON,
nonfinite constants and exponent overflow are refused. Optional payment
`buyer_role` may be omitted or null; all other documented arguments are required.
Unexpected programming exceptions surface as failures. Views neither fetch offers
nor change any machine.

### Resale session coverage and limits

The [validation record](../../validation/2026-11-02-plan-local-resale-session-cli/README.md)
maps existing coverage before the new suites, gives actual commands/results and
records remaining exact-head gates. `test_resale_session.py` covers delegation,
explicit effects, source faults, historical/current views and isolation.
`test_resale_cli.py` covers strict fixtures and requests, fresh actual graphs,
importability, stdin/file execution, error continuation and uncommitted settlement.
Existing resale FSM/source/adapter and HTTP tests remain unchanged.

All values are synthetic. R01–R04 remain **설계중** and retain their existing
status. Product TTLs, authentication, compensation, seller payout, legal treatment
and provider authority remain **UNDETERMINED**, owned by Astra/User and the
User/legal/privacy/tax/accounting/Toss owners in contract §7.1. Provenance remains
`MOCK_GATE_ONLY`; every existing mock/non-claim flag is preserved. No persistence,
sockets, HTTP, SDK, external service, credential, real money, provider/chain call,
runtime activation or new protocol command is added. No durability, economic
finality, bank exactly-once, independent currentness, legal compliance or
production readiness is claimed. Non-author A2 exact-final-head review and both
required workflows, including unchanged HTTP coverage, remain gates before merge.

## Shared local ticket operations desk

`ticket_operations_session.TicketOperationsSession` constructs one settlement,
reservation, resale and admission machine. Reservation, resale and admission
share the settlement source; resale and admission share the reservation source;
admission reads that same resale machine as its ownership source. Its `.booking`
is the existing `BookingSession` over that exact reservation machine. Its `.resale`
and `.admission` offer both recorded adapters and explicit request-input methods. Each construction is a fresh sequential in-memory graph.

With this directory on `PYTHONPATH`, callers can supply their own synthetic setup
and sources:

```python
import json
from pathlib import Path
from fake_presentation_source import FakePresentationSource
from fake_resale_offer_source import FakeResaleOfferSource
from ticket_operations_session import TicketOperationsSession

value = json.loads(Path("reference/booking_resale_admission/fixtures/ticket_operations_session.json").read_text())
desk = TicketOperationsSession(
    setup=value["setup"],
    offer_source=FakeResaleOfferSource(recordings={e["offer_id"]: e["recorded_text"] for e in value["offers"]}),
    presentation_source=FakePresentationSource(recordings={
        (e["operation"], e["presentation_id"]): e["recorded_text"] for e in value["presentations"]}),
)
desk.resale.list_resale("offer-1", listing_id="list-1", idempotency_key="my-list")
desk.resale.cancel_listing("list-1", seller_role="buyer-1", idempotency_key="my-cancel")
desk.admission.authorize_admission("ticket-1", admission_id="entry-1",
    idempotency_key="my-entry", gate_role="gate-a", expires_ms=1060000)
```

Alternatively `ticket_operations_fixture.load_fixture(path)` returns a configured
desk. Its JSON object requires exactly `fixture_version` (integer `1`),
`provenance` (`"MOCK_GATE_ONLY"`), `setup`, `offers` and `presentations`, plus
optional `payments`, `cancel_acceptances` and `statements` (documented below).
Every setup row requires exactly `machine`, `operation`, `subject_id`,
`idempotency_key`, `body`, using the existing admission fixture's exact schemas:

| Machine | Setup selectors |
| --- | --- |
| `settlement` | `initiate`, `authorize`, `capture`, `commit` |
| `reservation` | `set_clock`, `register_show`, `hold`, `confirm`, `observe_payment`, `bind_settlement`, `issue` |
| `resale`, `admission` | `set_clock`, `adopt_issued` |

Explicit initial clocks, confirmed/issued rights, primary settlement binding and
adoption into both surfaces are required by this fixture format. All policy,
time, identity, quote, payment and settlement values are caller-supplied synthetic
inputs. Resale settlement binding remains optional and explicit. Setup runs
sequentially through public methods; only successful construction exposes the
sessions. Discarding failed construction provides no cross-machine rollback.

Offer rows require `offer_id` and exactly one of `recorded_text` or `fault`.
Presentation rows require `operation`, `presentation_id` and exactly one payload.
Their schemas and synthetic faults are unchanged from the individual fixtures;
duplicate identities are refused. Record text is validated on fetch, including
on replay, rather than during construction.

The CLI accepts requests with exactly `surface`, `operation`, `arguments`:

```json
{"surface":"resale","operation":"view","arguments":{"listing_id":"list-1"}}
{"surface":"admission","operation":"view","arguments":{"right_id":"issue-1"}}
```

`surface` is exactly `booking`, `resale`, `admission` or `settlement`. The eleven booking selectors
and exact required arguments are listed in [the booking table](#local-booking-desk-session-and-jsonl-cli).
All sixteen resale selectors and nine admission selectors documented above retain
their exact arguments, including
optional resale payment `buyer_role`. The existing dispatchers validate them;
Only each surface's documented selectors are accepted. Primary payment observation remains
setup-only. The settlement selectors and their required arguments are documented
[below](#explicit-settlement-controls-on-the-shared-ticket-desk); other settlement operations are refused. Booking retains its existing `register_show` selector without adding
organizer lifecycle operations. Output adds
`surface` to the existing `operation` plus `receipt`, `view` or `error` envelope.
Domain errors retain `{code}`; local errors retain `{type,message}`. Exit 0 means
all supplied requests succeeded, exit 1 records domain/source refusals, and exit
2 means structural/setup/file/usage or booking prerequisite failure. Structural
request errors and `BookingInputError` stop input; other refusals allow only the next explicitly supplied line. Duplicate JSON keys,
nonfinite numbers and exponent overflow are refused. Unexpected programming errors
propagate. Earlier accepted operations stay applied if a later request fails.

From the repository root, run each scenario against a fresh fixture:

```bash
for scenario in cancel admission transfer; do
  python3.12 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
    --requests "reference/booking_resale_admission/fixtures/ticket_operations_${scenario}.jsonl"
done
```

Use `--requests -` for stdin. Each supplied scenario deliberately exits **1**:

| Scenario | Expected rows and behavior |
| --- | --- |
| `cancel` | 6 rows: listing blocks entry with `LISTING_LOCKED`; explicit cancellation succeeds; same admission key retains `LISTING_LOCKED`; fresh key authorizes admission. |
| `admission` | 7 rows: authorization blocks listing with `ADMISSION_LOCKED`; explicit consumption blocks a fresh listing with `ALREADY_CONSUMED`; replay returns first authorization/consume receipts while current view is `CONSUMED`. |
| `transfer` | 16 rows: explicit listing, hold, synthetic payment, binding and transfer, then replay/close/current views; old and unreissued recipient authorization both return `STALE_VERSION`. Reservation remains version 1 while resale is version 2; venue credential reissuance stays false. |

No request triggers an implicit follow-up, retry, key rewrite, clock synchronization
or settlement orchestration. Admission `set_clock` keeps its existing reservation
delegation; resale time remains independent. First-result semantics, current views,
refusal codes, source failures and all mock-only flags belong to the existing FSMs
and adapters. The existing Class B clock-skew partial effects remain unchanged.

Product timing, authentication, independent currentness and credential reissuance
remain **UNDETERMINED**, owned by Astra/User and the existing contract owners.
This adds no payment lookup handoff, reissuance, HTTP, persistence, frontend,
protocol commands, SDK/catalogue changes or runtime activation. No rollback,
economic finality, bank exactly-once, legal compliance or production readiness is
claimed. See the [validation record](../../validation/2026-11-02-plan-local-ticket-operations-desk/README.md)
for coverage, actual commands/results and remaining non-author A2 review and
exact-final-head CI gates. Existing HTTP coverage is preserved for normal CI.

### Booking on the shared desk

Fixture clocks do **not** initialize `.booking`. Call `.booking.set_clock`
explicitly before registration, hold, release, confirm or cancel; a successful
replay of a fixture clock counts. A failed initialization does not count. Views
and reconciliation need no session clock. Confirm requires an explicit valid
`quote_ref`. Missing clock or invalid quote emits local `BookingInputError`, stops
at that line with exit 2 and binds no FSM key. Earlier accepted effects remain.
Booking calls fetch no recordings and perform no payment observation,
settlement orchestration or automatic admission operation. Issuance requires the
separate explicit `booking.issue` request described below.

For example, after loading the existing fixture:

```python
desk.booking.view("reserve-1")  # ISSUED on the same reservation graph
desk.booking.set_clock("clock", now_ms=1000000, idempotency_key="ticket-clock")
desk.booking.hold("reserve-2", show_id="show-1", slot=1, buyer_role="buyer-2",
                  expires_ms=1120000, idempotency_key="booking-hold")
```

Run both shared booking journeys through file input and stdin from repository root:

```bash
for scenario in booking booking_admission; do
  python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
    --requests "reference/booking_resale_admission/fixtures/ticket_operations_${scenario}.jsonl"
  python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
    --requests - < "reference/booking_resale_admission/fixtures/ticket_operations_${scenario}.jsonl"
done
```

Both journeys intentionally exit **1**. `booking` has 21 lines: an already-issued
slot refuses a competing hold with `SLOT_OCCUPIED`; a second slot is explicitly
held, confirmed and cancelled, returning to `FREE`. Replayed confirmation and
reconciliation retain historical `CONFIRMED` snapshots while current views show
`CANCELLED`. Changed arguments/subjects, cross-operation keys and fixture-key
collisions conflict; a retained missing-reservation refusal replays unchanged.
`booking_admission` has 13 lines: booking views observe the original reservation
as `ISSUED` → `ADMISSION_AUTHORIZED` → `CONSUMED` only after explicit admission
calls. Its right version advances to 2; the slot stays `ISSUED`. Historical
booking reconciliation stays `ISSUED`; fresh reconciliation sees current state.
Delegated admission keys collide in the shared reservation namespace.

This advances local B02/B05/P03 composition evidence without changing capability
grades. Product timing and authority remain **UNDETERMINED — Astra/User**; legal
effects remain **UNDETERMINED — User/legal**. Shared keys and clocks are passed
unchanged: no namespacing, clock synchronization, retries or rollback guarantee.
See the [booking composition evidence](../../validation/2026-11-03-plan-plan-local-ticket-desk-booking-surface/README.md)
for coverage and actual local results, the exact HTTP exclusion, preservation
checks and pending non-author A2/exact-head KTX and KIX gates.

## Local booking desk session and JSONL CLI

`booking_session.BookingSession(machine)` exposes the existing §9 reservation
operations through the caller's actual `ReservationMachine`. Construction makes
no calls. Import it with this directory on `PYTHONPATH`:

```python
from booking_session import BookingSession
from reservation_fsm import ReservationMachine
session = BookingSession(ReservationMachine())
session.set_clock("clock", now_ms=1000000, idempotency_key="my-clock-1")
```

All numbers and identities here and in the transcripts are **synthetic caller
inputs**, never product defaults. Supply every policy field, identity, key,
expiry, amount and quote explicitly. For a complete runnable organizer and buyer
journey, from the repository root:

```bash
python3 reference/booking_resale_admission/booking_cli.py --requests reference/booking_resale_admission/fixtures/booking_confirm.jsonl
python3 reference/booking_resale_admission/booking_cli.py --requests reference/booking_resale_admission/fixtures/booking_cancel.jsonl
python3 reference/booking_resale_admission/booking_cli.py --requests - < reference/booking_resale_admission/fixtures/booking_boundaries.jsonl
```

Each invocation creates a fresh sequential in-memory `ReservationMachine()` with
no settlement source. All setup is ordinary explicit JSONL; the desk does not
load admission/resale fixtures or initialize payment, issuance or other machines.
For example:

```json
{"operation":"set_clock","arguments":{"subject_id":"clock","idempotency_key":"clock-1","now_ms":1000000}}
```

Every line must be an object with **exactly** `operation` and `arguments`.
Without a quote adapter, the following are the only local selectors. Python methods take the first
identity argument positionally or by keyword and the rest by keyword only.
All listed arguments are required; extra arguments are rejected.

| Operation | Exact arguments |
| --- | --- |
| `register_show` | `show_id`, `organizer_role`, `capacity`, `gate_roles`, `primary_price`, `resale_cap`, `resale_allowed`, `organizer_bps`, `platform_bps`, `idempotency_key` |
| `set_clock` | `subject_id`, `now_ms`, `idempotency_key` (subject must be `"clock"`) |
| `hold` | `reservation_id`, `show_id`, `slot`, `buyer_role`, `expires_ms`, `idempotency_key` |
| `release` | `reservation_id`, `idempotency_key` |
| `confirm` | `order_id`, `reservation_id`, `amount`, `quote_ref`, `idempotency_key` |
| `preview_calculated_quote` | `request_text` only; returns `quote`, requires no clock or reservation |
| `cancel` | `reservation_id`, `idempotency_key` |
| `bind_settlement` | `reservation_id`, `settlement_id`, `idempotency_key` |
| `issue` | `issuance_id`, `order_id`, `idempotency_key` |
| `reconcile` | `reservation_id`, `idempotency_key` |
| `view` | `reservation_id` |
| `view_show` | `show_id` |

A successful explicit `set_clock` **through this session** is required before
registration, hold, release, confirm, cancel, settlement binding and issuance, even when the supplied machine
already has a clock. A successful
replay counts as explicit initialization; it does not change current time.
Views require no clock initialization and do not mutate state. Reconciliation
also requires no session clock initialization, preserving direct FSM parity,
but retains process-local receipt or rejection bookkeeping. The desk requires
`quote_ref` to be a non-null valid existing identifier (opaque text, not a
validated external quote). Missing clock or invalid quote raises local
`BookingInputError` without calling the FSM or retaining the key. Other validation
is delegated unchanged: identifier length 1..100, capacity and gate-role limits
16, reservation window at most the existing synthetic 900000 ms limit, integer
money and bps checks. These fixture bounds are not approved product TTLs or policy.

Success output contains `operation` and unchanged `receipt` (business operations or reconciliation) or `view`.
FSM rejection contains `error: {"code": "..."}`; local input/file errors contain
`error.type` and `error.message`, introducing no protocol codes. Domain rejection
continues only with subsequent supplied lines. Malformed JSON, duplicate keys at
any depth, nonfinite numbers, blank lines, invalid roots, unsupported selectors,
missing/extra fields or local prerequisite failure stop input immediately.
Earlier accepted calls remain applied in memory. Exit status is 0 if all supplied
requests succeed (including empty input), 1 if any FSM rejection occurs, and 2
for input/structural/file failure (which takes precedence). Argument-parser usage
errors use stderr; request responses use JSONL stdout. No keys, IDs, clock changes,
retries, releases or follow-up operations are generated.

Expected transcript outcomes:

| Transcript | Outcome |
| --- | --- |
| `booking_confirm.jsonl` | 6 successes, exit 0; organizer registration, buyer hold and `CONFIRMED`, then current views. Payment, issuance, settlement and right remain null. |
| `booking_cancel.jsonl` | 8 successes, exit 0; explicit pre-payment cancellation frees the slot. Replaying the confirmation key returns the historical `CONFIRMED` receipt; current view is `CANCELLED`. |
| `booking_boundaries.jsonl` | 23 responses, exit 1; errors in order: `SLOT_OCCUPIED`, `SLOT_OCCUPIED`, `IDEMPOTENCY_CONFLICT`, `PRIMARY_PRICE_MISMATCH`, `RESERVATION_EXPIRED`, `SLOT_OCCUPIED`. Explicit release permits buyer 2's fresh-key hold; rejected key stays rejected. At exact expiry, buyer 3 remains `HELD` with `expired: true` and slot `RESERVED` until caller-directed release; buyer 4 then succeeds with an explicit fresh key. |

Confirmation is a reservation agreement, separate from payment and issuance.
This desk is a local service, not an authenticated organizer interface. It exposes
no payment lookup/observation, admission, persistence, external calls or runtime activation.
Settlement binding and issuance are explicit forwarding calls; they require caller-prepared
synthetic payment/settlement facts. The standalone CLI has no payment setup interface
and no settlement source; a configured Python session or the shared fixture supplies those facts. The payment–reservation handoff remains
blocked. `MOCK_GATE_ONLY`, `IN_MEMORY_FSM`, false non-claim flags and B01/B02/B04
status remain unchanged. Authentication, approved product TTLs, discounts, provider
authority and compensation remain `UNDETERMINED` under the existing
[§7.1 owners](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md).
See the [builder validation record](../../validation/2026-11-02-plan-local-booking-desk-cli/README.md)
for coverage, commands and outstanding review/CI gates.

## Synthetic local resale payment source

`ResalePaymentSource.fetch(recording_id)` returns one caller-selected synthetic
record or `None`. `ResalePaymentRecord` requires exactly these four fields:

| Field | Shape |
|---|---|
| `listing_id` | Existing identifier shape, equal to the caller's listing ID |
| `payment_ref` | Existing opaque mock reference: 64 lowercase hexadecimal characters |
| `amount` | Existing `_money` positive integer range; bool is invalid |
| `buyer_role` | Explicit non-null role identifier; a label without authentication |

`FakeResalePaymentSource(recordings=...)` copies JSON-text recordings into a
read-only mapping keyed by local recording ID. Fetch parses a detached object
anew; duplicate JSON keys, non-finite constants, malformed JSON and non-object
roots are refused. `SyntheticResalePaymentFault.ERROR` and `.TIMEOUT` fail
immediately without I/O or sleeping. `calls` exposes immutable tuple snapshots.
The fake only decodes; the adapter checks the four-field observation schema.

```python
adapter = ResalePaymentAdapter(machine, payment_source)
receipt = adapter.observe_resale_payment(
    recording_id, listing_id=listing_id, idempotency_key=payment_key,
)
# Or inject the source into the existing session:
session = ResaleSession(machine, offer_source, payment_source=payment_source)
session.observe_recorded_payment(
    recording_id, listing_id=listing_id, idempotency_key=payment_key,
)
# Separate caller request, if desired:
session.accept_resale(transfer_id, listing_id=listing_id, idempotency_key=transfer_key)
```

Import from `resale_payment_source`, `fake_resale_payment_source`,
`resale_payment_adapter` and `resale_session` using this directory on `PYTHONPATH`,
following the existing sibling-module convention. Existing direct session
`observe_resale_payment` is unchanged. The helper is also exposed by the local
CLI selector and optional fixture field documented below; it adds no catalogue
entry, protocol command or `REPLAYABLE` operation. A session without a payment source raises `ResalePaymentSourceError`
before FSM access when this helper is invoked.

Each adapter request fetches exactly once, including replay and invalid caller
inputs. Missing records raise `ResalePaymentNotFound`; malformed records/callers
or mismatched listing bindings raise `InvalidResalePaymentRecord`; fetch faults
raise `ResalePaymentSourceError`. These are local exceptions without protocol
codes. Validation completes before FSM access or key binding. The adapter then
forwards the recorded `payment_ref`, `amount`, explicit `buyer_role` and caller's
listing ID/key unchanged to `ResaleMachine.observe_resale_payment`. The recording
selector never enters FSM arguments, fingerprints or journals. FSM receipts and
exceptions propagate unchanged; valid-shaped wrong buyers/amounts reach its
existing refusal and retained-key semantics. There is no state precheck, retry,
fallback, cached receipt, automatic hold, settlement, transfer, admission or payout.

The [coverage and execution record](../../validation/2026-11-02-plan-local-resale-payment-source/README.md)
maps existing coverage before the new tests: FSM payment/transfer/replay and
false-flag coverage is sufficient; adapter parity and actual-session sequencing
were partial overall; immutable payment recordings, one-fetch behavior and
pre-delegation refusal were uncovered at this boundary. New
`test_resale_payment_source.py`, `test_resale_payment_adapter.py` and source-backed
cases in `test_resale_session.py` address those gaps. They are source-informed
regression evidence, not independent verification.

From repository root:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/reference/booking_resale_admission"
python3 -m unittest test_resale_payment_source test_resale_payment_adapter
python3 -m unittest test_resale_fsm test_resale_session test_resale_cli
python3 reference/booking_resale_admission/example_resale_payment_adapter.py
```

The runnable example uses actual local machines and `ResaleSession`, lists
through the existing offer source, optionally holds, and records payment. Its
`paused` output shows `PAYMENT_NOTED`, unchanged holder/version and UNBOUND
settlement before a separate explicit transfer request. `run_example(hold=False)`
also demonstrates observation directly from LISTED. All amounts, labels, times,
references and keys are synthetic fixture choices. MOCK provenance and false
funds/authority/durability/finality flags remain unchanged.

[BOOKING_RESALE_ADMISSION_GATES.md §§7 and 10](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#10-리셀-수락-상태-기계)
remain authoritative. Product values remain **UNDETERMINED — Astra/User**;
provider authority remains with User/Toss technical owners, resale merchant
eligibility with User/Toss sales, and compensation/payout obligations with their
existing legal/accounting/tax owners. This code derives no reference from
provider tuples or evidence hashes, interprets no cancellation history, and
implements no reservation handoff. It supplies no external authority, live
payment, funds execution, persistence, admission or production readiness.
Full exact-head KTX/KIX CI and non-author A2 review remain required before merge.


## Recorded payments in both local ticket desks

The standalone resale CLI and the shared ticket operations CLI expose the existing
`ResaleSession.observe_recorded_payment` helper as a local selector. It uses the
same resale machine that the shared admission desk reads as its ownership source.
No FSM, protocol, contract, OpenAPI, SDK or HTTP binding changes are involved.

Both version-1 fixture formats accept one optional top-level `payments` array.
All existing required fields remain required and all other extra fields are
rejected. Omission leaves the source unconfigured; `[]` configures an empty fake
source. Each entry contains exactly `recording_id` and one payload:

```json
{"recording_id":"payment-1","recorded_text":"{\"listing_id\":\"list-1\",\"payment_ref\":\"cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd\",\"amount\":8000,\"buyer_role\":\"buyer-2\"}"}
{"recording_id":"timeout-1","fault":"synthetic_resale_payment_timeout"}
```

Identities must pass the existing identifier validator and be unique. Text must
be a string; its JSON and existing four-field observation schema are validated
only on fetch. The other supported immediate fault is
`synthetic_resale_payment_error`. Unknown faults, duplicate identities, absent or
both payloads, extra fields and non-array payment lists fail before any machine
is constructed. These are synthetic observations without provider authority.

Standalone requests contain exactly `operation` and `arguments`; shared requests
add `surface: "resale"`:

```json
{"operation":"observe_recorded_payment","arguments":{"recording_id":"payment-1","listing_id":"list-1","idempotency_key":"payment-key"}}
{"surface":"resale","operation":"observe_recorded_payment","arguments":{"recording_id":"payment-1","listing_id":"list-1","idempotency_key":"payment-key"}}
```

Those three arguments are exact and required. The record supplies explicit
`buyer_role`; direct `observe_resale_payment` still accepts its optional
`buyer_role`. Each structurally valid dispatched observation fetches once,
including replay, and invokes the existing adapter once. Structural request
errors fetch zero times. There is no retry, automatic next step or cached fallback.
The recording ID does not enter FSM operation identities or journals.

The [standalone fixture](fixtures/resale_payment_session.json) and
[shared fixture](fixtures/ticket_operations_payment_session.json) preserve explicit
setup and clocks. Run both LISTED and BUY_HELD paths from repository root:

```bash
for phase in listed held; do
  python3 reference/booking_resale_admission/resale_cli.py \
    --fixture reference/booking_resale_admission/fixtures/resale_payment_session.json \
    --requests "reference/booking_resale_admission/fixtures/resale_payment_${phase}.jsonl"
  python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_payment_session.json \
    --requests "reference/booking_resale_admission/fixtures/ticket_operations_payment_${phase}.jsonl"
done
```

Use `--requests -` for stdin. Standalone transcripts exit 0; shared transcripts
exit 1 because both separately requested admission authorizations return
`STALE_VERSION`: the former holder/version 1 and unreissued recipient/version 2.
Observation ends at `PAYMENT_NOTED`, with holder/version unchanged and no
settlement command or transfer. The next view exposes this pause. Alias replay
and replay after separate transfer/close retain the first observation receipt;
transfer itself is another explicit request. Admission remains separate and no
credential is reissued.

Output retains `operation`, `receipt` (or `error`) and shared `surface`. Missing
configuration/recordings, malformed or mismatched recordings and synthetic faults
produce local `{type,message}` errors, exit 1, with no FSM mutation or key binding.
A subsequent explicit line can use the same key with a valid recording. Valid
records that reach an FSM semantic refusal retain its existing `{code}` error and
key behavior. Structural/setup errors exit 2; a malformed request stops input.
Unexpected programming errors propagate as before.

The [payment-desk validation record](../../validation/2026-11-02-plan-local-resale-payment-desk/README.md)
maps existing coverage and records socket-denied source, adapter, session,
fixture/CLI tests, file/stdin subprocess transcripts and local verification limits.
All authority, funds, durability and finality flags remain false. This is local
source-informed regression evidence, not provider authenticity, real funds,
production durability or chain finality evidence. No compensation, settlement
execution, reservation-payment handoff, reissuance or runtime activation is added.
Product values remain **UNDETERMINED — Astra/User**; provider authority remains
with User/Toss technical owners, merchant eligibility with User/Toss sales,
and payout obligations with the existing legal/accounting/tax owners.


## Explicit reconciliation in local ticket desks

Booking, resale and admission sessions now expose their existing FSM `reconcile`
method directly, once per explicit request. The caller supplies the subject
identity and idempotency key unchanged. There is no source recording fetch,
pre-read, generated key, clock update or automatic follow-up. The shared ticket
operations desk uses its existing resale/admission routing; booking remains its
separate desk. These selectors add no protocol command, read catalogue or export.

Standalone JSONL requests have exactly `operation` and `arguments`; shared
requests add exactly `surface`:

```json
{"operation":"reconcile","arguments":{"reservation_id":"reserve-1","idempotency_key":"booking-recon"}}
{"operation":"reconcile","arguments":{"listing_id":"list-1","idempotency_key":"resale-recon"}}
{"operation":"reconcile","arguments":{"right_id":"issue-1","idempotency_key":"admission-recon"}}
{"surface":"resale","operation":"reconcile","arguments":{"listing_id":"list-1","idempotency_key":"resale-recon"}}
{"surface":"admission","operation":"reconcile","arguments":{"right_id":"issue-1","idempotency_key":"admission-recon"}}
```

Results contain `operation`, unchanged `receipt` and shared `surface` where
applicable. `matched`, `state_digest`, `entry_count`, subject snapshots,
provenance and false non-claim flags remain those of the FSM. Domain errors keep
`{code}`; local input errors keep `{type,message}`. Existing exit codes 0/1/2
and stream continuation/stopping rules still apply.

Reconciliation compares replayed accepted journals with local business state.
It preserves those journals and ticket/payment state, while retaining the FSM's
process-local receipt or rejection under the supplied key. It is a stateful
operation, not a read-only query. Same-key replay returns the original snapshot
with `duplicate: true`, `applied: null`; the current `view` may differ. Changed
subjects or cross-operation key reuse retain `IDEMPOTENCY_CONFLICT`. Reconcile
receipts and rejected calls are absent from accepted journals and are not
restored as durable evidence. A digest is not a signature or authenticated audit.
`matched` does not establish independent currentness or grant permission to act.

Bound-source checks retain their existing failure semantics. The shared journey
explicitly authorizes admission, reconciles successfully, advances the admission
clock to that authorization's synthetic expiry, and separately lists, pays,
binds, transfers and closes through resale. Replaying the old reconciliation key
still returns its historical success; a fresh admission reconciliation key
returns `STALE_VERSION` when authorization replay encounters the moved ownership.
The failed key repeats that refusal. No credential is repaired or reissued.
All clock values, prices, roles and keys are synthetic caller inputs.

Run each transcript from repository root (each intentionally exits **1** because
it contains explicit domain refusals):

```bash
python3 reference/booking_resale_admission/booking_cli.py --requests reference/booking_resale_admission/fixtures/booking_reconcile.jsonl
for desk in resale admission ticket_operations; do
  python3 "reference/booking_resale_admission/${desk}_cli.py" \
    --fixture "reference/booking_resale_admission/fixtures/${desk}_session.json" \
    --requests "reference/booking_resale_admission/fixtures/${desk}_reconcile.jsonl"
done
```

Use `--requests -` with the same transcript on stdin. Booking shows historical
`CONFIRMED` versus current `CANCELLED`; resale shows historical `LISTED` versus
current `CLOSED`; admission shows historical `AUTHORIZED` versus current
`CONSUMED`. Existing transcripts remain compatible.

P03, R01–R05 and P06 retain their existing status. Currentness, operational policy
and retention values remain **UNDETERMINED** with existing Astra/User and contract
owners. This is no durable recovery, authenticated audit, payment lookup, retry,
automatic repair, transfer, consumption, funds execution or production activation.
The [builder evidence](../../validation/2026-11-03-plan-local-ticket-desk-reconciliation/README.md)
records coverage, actual commands and local limits. Normal CI still requires the
unchanged HTTP suite; non-author exact-head A2 review and completed/success KTX
and KIX workflows remain required before merge.

## Synthetic recorded booking quotes

`BookingQuoteSource.fetch(recording_id)` supplies caller-selected, unauthenticated
synthetic inputs. `FakeBookingQuoteSource(recordings=...)` copies a map of JSON
strings or `SyntheticBookingQuoteFault.ERROR/TIMEOUT`, exposes a read-only
`recordings` map and tuple snapshot `calls`, and decodes a detached dictionary on
each fetch. Missing recordings return `None`; faults raise immediately without
sleep or retry. Construction and import do not fetch or initialize a clock.

`BookingQuoteAdapter(session, source).confirm_recorded_quote(recording_id,
reservation_id=..., order_id=..., idempotency_key=...)` validates all four caller
identifiers before fetching once, including every replay invocation. A record
must be an ordinary dictionary with exactly `reservation_id`, positive integer
`amount` (the existing mock money bound), and nonempty identifier `quote_ref`.
Booleans, floats, nulls, containers, missing fields and unknown fields are refused.
Recorded reservation must equal the caller's expected reservation. The adapter
copies the record and delegates once to the existing `BookingSession.confirm`,
returning its receipt unchanged. The selector never enters the FSM fingerprint
or journal; two selectors containing identical inputs replay the same key.

Missing, malformed, mismatched or failed fetches cause no session/FSM call or key
binding. `BookingQuoteNotFound` and `InvalidBookingQuoteRecord` derive from local
`BookingQuoteSourceError`; unexpected fetch exceptions are wrapped in that base
error. Session/FSM exceptions propagate unchanged. There is no state inspection,
receipt cache, fallback, retry, discount calculation or quote generation. Missing
session clock, primary-price mismatch, expiry, order binding and immutable
first-result behavior remain governed by the existing session and FSM. Even after
a successful confirmation, a subsequent source failure returns a local error,
never a cached success.

`booking_quote_fixture.load_fixture(path)` builds only a source. Its exact schema:

```json
{"fixture_version":1,"provenance":"MOCK_GATE_ONLY","quotes":[{"recording_id":"record-1","recorded_text":"{\"reservation_id\":\"reserve-1\",\"amount\":10001,\"quote_ref\":\"quote-1\"}"}]}
```

Each entry requires `recording_id` and exactly one of `recorded_text` (string) or
`fault` (`synthetic_booking_quote_error` / `synthetic_booking_quote_timeout`).
Duplicate selectors, duplicate JSON keys at any depth, unknown fields, unsupported
versions/faults and invalid scalar shapes are rejected. Embedded record text is
validated on fetch, including duplicate keys and nonfinite numbers. An empty
`quotes` array is allowed and supplies no recordings. Loading does no FSM setup.

The standalone booking CLI opts in using `--quotes PATH` and accepts this additional
local selector only when a source is supplied:

```json
{"operation":"confirm_recorded_quote","arguments":{"recording_id":"record-1","reservation_id":"reserve-1","order_id":"order-1","idempotency_key":"confirm-1"}}
```

All four arguments are required, with no extra fields. `dispatch_request` and
`run_requests` also accept keyword-only `quote_adapter=None` for explicit local
injection. Existing CLI operations and behavior without a source are preserved.
The [shared ticket desk](#recorded-booking-quotes-on-the-shared-desk) supports the
same explicit composition through `--quotes` or Python injection. This
helper is not a new protocol command or an HTTP/OpenAPI operation.

```bash
PYTHONDONTWRITEBYTECODE=1 python3.12 reference/booking_resale_admission/booking_cli.py --quotes reference/booking_resale_admission/fixtures/booking_quotes.json --requests reference/booking_resale_admission/fixtures/booking_recorded_confirm.jsonl
PYTHONDONTWRITEBYTECODE=1 python3.12 reference/booking_resale_admission/booking_cli.py --quotes reference/booking_resale_admission/fixtures/booking_quotes.json --requests - < reference/booking_resale_admission/fixtures/booking_recorded_boundaries.jsonl
```

The confirmation transcript has 7 successes, exit 0: explicit clock, registration,
hold, confirmation, replay through an alias and two views. The boundary transcript
has 20 responses, exit 1, exercising absence, malformed/mismatched recordings,
both immediate faults, price mismatch and retained refusal, success, source
failure after success, conflicting replay, explicit cancellation, historical
confirmation replay and expiry of a second hold. Source errors use
`error.type/message`, contribute exit 1 and continue only through subsequent
explicit lines. FSM errors retain `error.code`. Structural/setup/file failures
and `BookingInputError` stop with exit 2. Invalid caller identifier scalars are
local `InvalidBookingQuoteRecord` errors (exit 1), rejected before fetching.

Both transcripts reach `CONFIRMED`; payment, settlement, issuance and right remain
absent. No payment handoff or automatic follow-up occurs. All existing false
non-claim flags remain false. B03/B04 remain partial mock capabilities; price,
discount and quote-authority policy remain **UNDETERMINED — Astra/User**. There
is no authenticated quote, pricing engine, persistence, network, paid dependency,
credentials or production activation. See the [coverage and execution record](../../validation/2026-11-03-plan-plan-local-booking-quote-source/README.md)
for existing coverage reuse, new boundary tests and outstanding review/CI gates.

### Recorded booking quotes on the shared desk

The shared `ticket_operations_cli.py` accepts optional `--quotes PATH` alongside
required `--fixture PATH` and `--requests PATH|-`. It reuses
`booking_quote_fixture.load_fixture` and its exact source-only schema above,
then binds `BookingQuoteAdapter` to the shared session's existing `.booking`.
The shared setup fixture has no additional fields. It still contains synthetic
issued inventory; the new examples register a separate show and reservation.
No additional reservation machine, clock initialization or quote fetch occurs
when composing the adapter.

Both shared Python entry points accept keyword-only `quote_adapter=None`:
`dispatch_request(session, request, *, quote_adapter=None)` returns one result;
`run_requests(session, lines, *, quote_adapter=None)` prints JSONL and returns
the exit status. Only the booking surface receives this adapter. Explicit Python
composition from the repository root (with `reference/booking_resale_admission`
on `PYTHONPATH`) is:

```python
import json
from pathlib import Path
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_fixture import load_fixture as load_quotes
from ticket_operations_fixture import load_fixture
from ticket_operations_cli import dispatch_request, run_requests

fixtures = Path("reference/booking_resale_admission/fixtures")
desk = load_fixture(fixtures / "ticket_operations_session.json")
quotes = load_quotes(fixtures / "ticket_operations_booking_quotes.json")
adapter = BookingQuoteAdapter(desk.booking, quotes)
rows = (fixtures / "ticket_operations_recorded_confirm.jsonl").read_text().splitlines()
# Explicit clock, separate show registration, hold and recorded confirmation.
for line in rows[:4]:
    result = dispatch_request(desk, json.loads(line), quote_adapter=adapter)
    print(json.dumps(result, sort_keys=True))
status = run_requests(desk, rows[4:], quote_adapter=adapter)
assert status == 0
assert quotes.calls == ("desk-record-1", "desk-alias")
```

The existing selector keeps all four required arguments and the shared envelope:

```json
{"surface":"booking","operation":"confirm_recorded_quote","arguments":{"recording_id":"desk-record-1","reservation_id":"desk-reserve-1","order_id":"desk-order-1","idempotency_key":"desk-confirm-1"}}
```

Without `--quotes` or an injected adapter, this selector remains unsupported
(`FixtureError`, exit 2); every existing booking/resale/admission operation keeps
its prior behavior. Results retain `surface`, `operation` and unchanged `receipt`
or `view`. Domain refusals use `error.code`; source failures use
`error.type/message`, contribute exit 1 and allow only explicitly supplied later
lines to run. Malformed input, fixture/file errors and `BookingInputError` stop
with exit 2, including after earlier exit-1 refusals. All-success input exits 0.
Unexpected programming exceptions propagate.

Run both examples through files and stdin from the repository root:

```bash
for scenario in recorded_confirm recorded_boundaries; do
  PYTHONDONTWRITEBYTECODE=1 python3.12 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
    --quotes reference/booking_resale_admission/fixtures/ticket_operations_booking_quotes.json \
    --requests "reference/booking_resale_admission/fixtures/ticket_operations_${scenario}.jsonl"
  echo "file exit: $?"
  PYTHONDONTWRITEBYTECODE=1 python3.12 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
    --quotes reference/booking_resale_admission/fixtures/ticket_operations_booking_quotes.json \
    --requests - < "reference/booking_resale_admission/fixtures/ticket_operations_${scenario}.jsonl"
  echo "stdin exit: $?"
done
```

`recorded_confirm` emits 7 rows and exits 0: explicit clock, registration, hold,
confirmation, alias replay and current reservation/show views. `recorded_boundaries`
emits 20 rows and exits 1: missing/malformed/mismatched records, both source faults,
price refusal, conflicting replay of that refusal, confirmation, source failure
after success, conflicting quote replay, cancellation, historical confirmation
replay and a second hold's expiry. That historical receipt remains `CONFIRMED`
with `duplicate: true` and `applied: null`; the current view is `CANCELLED`.
The confirmation example's current view is `CONFIRMED`. Both show zero payments
for the new show and null payment, settlement, issuance and right fields for the
new reservation. Existing settlement/resale/admission state stays unchanged.

Every identifier-valid confirmation invocation fetches exactly once, including
replay. Invalid callers never fetch; rejected source data never reaches the
session or binds the key. There is no retry, fallback to an earlier receipt,
payment-reservation handoff or automatic settlement/issuance. The scope remains
synthetic, in-memory Track P service composition. Pricing, discounts and
quote-authority policy remain **UNDETERMINED — Astra/User**. No catalogue/SDK,
protocol command, persistence, network or runtime activation is added.

`test_ticket_operations_quotes.py` compares shared dispatch with direct adapter
execution on an independently constructed equivalent graph after every step,
including errors, digests and journals. It checks source rejection/key reuse,
shared key collisions, fetch accounting, file/stdin outputs and exits 0/1/2,
and compatibility of all existing shared journeys. This is source-informed local
evidence; full HTTP coverage, non-author A2 exact-head review and exact-final-head
KTX/KIX workflow success remain delivery gates. See the
[coverage and actual command record](../../validation/2026-11-03-plan-local-ticket-desk-quotes/README.md).


## Explicit ticket fulfillment on the shared desk

Four explicit local selectors expose existing FSM methods (§§9–11); they add no
protocol commands. `booking.bind_settlement(reservation_id, *, settlement_id,
idempotency_key)` records a binding without running any settlement operation.
`booking.issue(issuance_id, *, order_id, idempotency_key)` returns the FSM's
issuance receipt. Both require a successful session `set_clock`, including a
successful replay; fixture initialization alone is insufficient. Unbound issuance
still returns memory evidence with `settlement_gate: UNBOUND`. Bound issuance
requires the existing synthetic committed settlement view and matching amount.

`resale.adopt_issued` and `admission.adopt_issued` each take `right_id` as the
positional-or-keyword subject and all these keyword-only required arguments:
`idempotency_key`, `show_id`, `organizer_role`, `capacity`, `gate_roles`,
`primary_price`, `resale_cap`, `resale_allowed`, `organizer_bps`, `platform_bps`,
`slot`, `buyer_role`, `expires_ms`, `order_id`, `amount`, `payment_ref`,
`reservation_id`, `quote_ref`. The CLI requires exactly the same complete input.
Explicit nulls are forwarded unchanged where the FSM permits them; the desk adds
no policy defaults or values inferred from views. Each call returns the original
receipt or raises the original error. Neither issuance nor either adoption
performs another action, fetches a recording, lists a ticket or admits anyone.

The new fixture retains the existing already-issued anchor, clocks, binding and
both adoptions. Its second reservation uses slot 1, separate IDs and a distinct
synthetic payment reference. Its hold, confirmation, payment observation and
settlement initiate/authorize/capture/commit are explicit existing setup entries.
Its binding, issuance and adoptions are deliberately absent from setup. Existing
fixture validation still requires at least one issued anchor and both adoptions
for every ticket issued during setup.

From repository root (each command intentionally exits **1**):

```bash
python3 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json \
  --requests reference/booking_resale_admission/fixtures/ticket_operations_fulfillment.jsonl
python3 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json \
  --requests - < reference/booking_resale_admission/fixtures/ticket_operations_fulfillment.jsonl
```

The 18 requests explicitly initialize booking time, bind the prepared settlement,
issue the second ticket, separately adopt it into resale and admission, list it,
and attempt admission (`LISTING_LOCKED`). Cancellation is explicit. Replaying the
refused authorization still returns `LISTING_LOCKED`; an explicitly supplied fresh
key authorizes, then a separate consume advances reservation/admission version
to 2. Replayed issuance/adoption receipts retain their original snapshots
(issuance version 1); final views show current state. Resale's local version stays
1; no synchronization is introduced. Exit codes remain 0 for successes, 1 for
continued domain/source refusals and 2 for stopping input/setup failures.

`test_ticket_fulfillment.py` compares each request's receipts/errors, canonical
states, digests and journals against a separately constructed direct-FSM graph,
checks unrelated journals and fetch histories, and covers strict arguments,
retained refusals, conflicts, expiry and bound/unbound issuance. This is
source-informed local composition evidence, not clean-room verification or full
HTTP-suite success. See [actual validation and limits](../../validation/2026-11-03-plan-local-ticket-fulfillment-desk/README.md).

Policy values remain **UNDETERMINED — Astra/User**; legal and provider facts retain
their existing named owners. No payment lookup/handoff, automatic actions,
persistence, frontend, funds execution, chain issuance/finality, production
runtime, legal compliance or production readiness is claimed. Non-author A2
exact-head review and successful exact-head KTX/KIX workflows remain delivery gates.


### Explicit settlement controls on the shared ticket desk

`desk.settlement` wraps the exact settlement machine shared by booking, resale and
admission. These five local selectors expose existing FSM operations only. Each
forwards once, returning the original receipt/view or raising the original FSM
error. Construction performs no settlement call beyond caller-supplied setup.
Each method accepts `settlement_id` positionally or by keyword; every other
argument is required and keyword-only. There are no generated keys or defaults.

| Operation | Exact required `arguments` fields |
| --- | --- |
| `initiate` | `settlement_id`, `idempotency_key`, `trade_id`, `gross`, `debtor_role`, `policy`, `currency` |
| `authorize` | `settlement_id`, `idempotency_key` |
| `capture` | `settlement_id`, `idempotency_key` |
| `commit` | `settlement_id`, `idempotency_key`, `movement_id`, `gross`, `amount`, `fee`, `tax`, `held`, `adjustment`, `adjustment_reason` |
| `view` | `settlement_id` |

Supply currency explicitly (`KRW` is the existing FSM's accepted currency).
Supply policy unchanged with its existing `kind`, `fee_bps`, `residual_payee` and
`fee_payee` fields; the FSM owns policy validation and domain errors. Resale
allocations do not supply settlement policy. Every statement component is
explicit, including `adjustment_reason: null` for zero adjustment. Example:

```json
{"surface":"settlement","operation":"authorize","arguments":{"settlement_id":"claim-2","idempotency_key":"authorize-2"}}
```

Output is `{surface, operation, receipt}` or `{surface, operation, view}`. Domain
refusals retain `{error:{code}}` and continue only to the next supplied line,
producing exit 1. Structural errors (missing/extra/duplicate fields, unsupported
selectors or nonfinite numbers) stop with exit 2. All-success input exits 0.

From repository root, each complete journey deliberately exits **1**:

```bash
python3 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_session.json \
  --requests reference/booking_resale_admission/fixtures/ticket_operations_settlement_booking.jsonl
python3 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_session.json \
  --requests - < reference/booking_resale_admission/fixtures/ticket_operations_settlement_resale.jsonl
```

Both transcripts work as files or stdin. The version-1 fixture retains the issued
anchor, committed settlement, both adoptions and explicit clocks. A separately
prepared paid reservation occupies slot 1 without issuance. The 13-line booking
journey explicitly initializes the booking clock, initiates and binds settlement,
then issuance refuses `SETTLEMENT_NOT_COMMITTED`. Explicit authorize, capture and
commit permit a separately requested issuance with the caller's fresh key. Replay
of the earlier refused key still refuses. The 16-line resale journey explicitly
lists the anchor and observes the merged synthetic recorded-payment source before
initiating/binding settlement. Acceptance pauses, retains its refusal after commit,
and transfers only on the separately supplied fresh acceptance key. Historical
initiate receipts remain `INITIATED` while current settlement views are `COMMITTED`.

The base settlement actions above never observe payments, issue, adopt,
transfer or consume rights, fetch recordings or advance ticket journals. Refund
controls, recorded statements and explicit distribution are documented below. F04,
reward coupling, primary-payment handoff and standalone finance tooling remain
excluded. Existing false funds/finality/durability/
production flags remain false. No network, persistence, chain execution, credentials
or runtime activation is added. Product policy remains **UNDETERMINED — Astra/User**;
legal/accounting treatment remains **UNDETERMINED — User/designated external reviewers**.
See the [coverage and actual validation record](../../validation/2026-11-03-plan-local-ticket-settlement-controls/README.md).


### Explicit refund controls on the shared ticket desk

Two additional local selectors and importable methods use the same shared
`SettlementMachine`. `bind_refund` forwards once to its existing FSM operation;
`observe_recorded_cancel_acceptance` calls the unchanged `CancelAcceptanceAdapter`
once. This selector observes an existing synthetic fact through
`observe_mock_cancel_acceptance`; it is not a new protocol command or an execution
of cancellation. Construction never fetches. All fields below are required;
`settlement_id` can be positional in Python and the other fields are keyword-only.

| Operation | Exact required `arguments` fields |
| --- | --- |
| `bind_refund` | `settlement_id`, `idempotency_key`, `refund_id`, `amount`, `beneficiary_role`, `reason` |
| `observe_recorded_cancel_acceptance` | `settlement_id`, `source_id`, `idempotency_key` |

```python
desk.settlement.bind_refund(
    "claim-1", idempotency_key="refund-bind-1", refund_id="refund-1",
    amount=4000, beneficiary_role="fixture-buyer-1", reason="fixture-caller-request")
desk.settlement.observe_recorded_cancel_acceptance(
    "claim-1", source_id="acceptance-1", idempotency_key="accept-1")
```

`TicketOperationsSession(..., cancel_acceptance_source=source)` and
`TicketSettlementSession(machine, cancel_acceptance_source=source)` accept an
optional caller-supplied source. Old fixtures and callers remain compatible.
Without a configured source, explicit observation raises
`CancelAcceptanceSourceError`. Version-1 fixture files optionally contain
`cancel_acceptances`, an array of exact entries:

```json
{"settlement_id":"claim-1","source_id":"acceptance-1","recorded_text":"{\"settlement_id\":\"claim-1\",\"source_id\":\"acceptance-1\",\"amount\":1000}"}
```

Each entry requires both identities and exactly one of `recorded_text` or `fault`.
Both identifiers use the existing fixture identifier rules; duplicate identity
pairs, unknown fields, wrong containers and unsupported faults are structural
errors. The only fault strings are `synthetic_cancel_acceptance_error` and
`synthetic_cancel_acceptance_timeout`, both immediate synthetic exceptions.
Recording text is kept raw until fetch. The unchanged source/adapter decodes and
checks a payload with exactly `settlement_id`, `source_id`, `amount`; identities
must match the explicit request and the FSM validates economic amounts.

Each explicit observation fetches exactly once, including replay. Missing,
malformed or mismatched recordings and synthetic faults preserve source error
`{type,message}` diagnostics; domain refusals preserve `{code}`. Source failures
never reach the FSM or consume an idempotency key. No retry, follow-up or new key
is generated. The CLI continues to the next explicit line and exits **1** after
source/domain refusals. Structural failures stop with **2**; success exits **0**.
FSM refusals such as `REFUND_OBLIGATION_REQUIRED` and
`REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION` remain unchanged. Accepted replays return
historical first receipts with `duplicate: true`, `applied: null`; refused keys
retain their first refusal even after later progress.

From repository root, run each example through files and stdin (all exit **0**):

```bash
for scenario in partial full replay; do
  python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_refund_session.json \
    --requests "reference/booking_resale_admission/fixtures/ticket_operations_refund_${scenario}.jsonl"
  python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_refund_session.json \
    --requests - < "reference/booking_resale_admission/fixtures/ticket_operations_refund_${scenario}.jsonl"
done
```

The fixture preserves explicit issuance, both adoptions and clocks. Its amounts,
identities, beneficiary, reason and keys are examples supplied by the caller,
not product defaults. `partial` binds 4000 and observes 1000 then 500; outstanding
refund becomes 2500 and open PG adjustment 1500. `full` binds one initial gross
refund of 10001, then records its full acceptance: refund outstanding becomes 0
and adjustment outstanding 10001. Confirmed cash remains 10001 throughout both
journeys, and `external_return_closed` remains false. `replay` repeats the first
binding and observation after later acceptance, preserving historical receipts.

Both CAPTURED and COMMITTED permit these existing operations. Fully accepting a
partial obligation does not select a burden rule. Partial bindings, even when
they sum to gross, keep `refund_bearer_policy = UNDEFINED` and the existing
`DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED` refusal. A single initial gross
binding retains `FIXTURE_FULL_GROSS_RECLASS`, a fixture reclassification without
legal liability determination. Repeating an accepted source under a new explicit
key retains the existing economically inert journal-entry characterization.

Refund actions do not cancel bookings, revoke tickets, transfer ownership,
consume admission, synchronize views or execute a return. Existing mock-only
flags remain unchanged. Product policy remains **UNDETERMINED — Astra/User**;
legal refund liability remains **UNDETERMINED — User/legal through I10**. There
is no HTTP/SDK/catalogue change, persistence, external service, F04, reward
coupling, primary-payment handoff, standalone finance tool or runtime activation.
See the [coverage and actual validation record](../../validation/2026-11-03-plan-plan-local-ticket-refund-controls/README.md).


### Recorded statements and explicit distribution on the shared ticket desk

Both `TicketOperationsSession` and `TicketSettlementSession` accept optional
`statement_source: StatementSource | None = None`. The existing `StatementAdapter`
uses the same settlement instance shared with booking, resale and admission.
Construction never fetches. Old fixtures work without a source; an explicit
recorded request then raises `StatementSourceError` before calling the FSM.

| Operation / Python method | Exact required `arguments` fields | Existing delegation |
| --- | --- | --- |
| `commit_recorded_statement` | `settlement_id`, `movement_id`, `idempotency_key` | `StatementAdapter.apply(operation="commit", ...)` |
| `observe_recorded_statement` | `settlement_id`, `movement_id`, `idempotency_key` | `StatementAdapter.apply(operation="observe_statement", ...)` |
| `distribute` | `settlement_id`, `idempotency_key`, `order` | `SettlementMachine.distribute` |

These are local selectors for existing operations. Python permits positional
`settlement_id`; all other arguments are required keyword-only. Direct `commit`
and both refund controls remain available. The caller selects commit or later
observation explicitly and supplies every request key and distribution order.
No phase inference, sorting, default order, generated key, automatic distribution,
receipt caching or retry occurs. Every recorded request, including replay,
fetches once. Distribution fetches nothing.

The shared version-1 `MOCK_GATE_ONLY` fixture accepts optional `statements`:

```json
"statements": [
  {"settlement_id":"claim-2","movement_id":"statement-1","recorded_text":"{\"settlement_id\":\"claim-2\", ...}"},
  {"settlement_id":"claim-2","movement_id":"timeout","fault":"synthetic_statement_timeout"}
]
```

Every entry has exactly the two identities and one of `recorded_text` or `fault`.
Identity pairs must be unique, using the existing 1–100 character, unpadded
identifier rules. Both `synthetic_statement_error` and
`synthetic_statement_timeout` are supported immediate synthetic failures; neither
waits for a clock or observes an external provider. Raw recorded text stays
undecoded until requested. The ellipsis above abbreviates a record; runnable
complete records are in `fixtures/ticket_operations_statement_session.json`.

A fetched document has exactly `settlement_id`, `movement_id`, `gross`, `amount`,
`fee`, `tax`, `held`, `adjustment`, `adjustment_reason`. Missing recordings,
malformed documents, missing/extra fields, mismatched identities and source
faults make no FSM call and bind no key. Properly shaped records with invalid
economic components reach unchanged FSM validation and retain its refusal keys.
Source failures produce `{error:{type,message}}`; domain refusals produce
`{error:{code}}`. Both continue to the next explicit line and exit 1. Structural
fixture/request errors stop with exit 2; all-success transcripts exit 0.

From repository root, run each transcript using files and stdin:

```bash
for scenario in distribution boundaries; do
  python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_statement_session.json \
    --requests "reference/booking_resale_admission/fixtures/ticket_operations_statement_${scenario}.jsonl"
  python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_statement_session.json \
    --requests - < "reference/booking_resale_admission/fixtures/ticket_operations_statement_${scenario}.jsonl"
done
```

`distribution` exits **0**. Its fixture preserves the issued anchor, both
adoptions and explicit clocks, and prepares a separate paid ticket bound to
`claim-2`. The transcript commits statement 1, explicitly issues that ticket,
distributes, observes statement 2, then distributes again. Synthetic gross 10001
and 500 fee bps give obligation faces 500 platform / 9501 organizer. Statement 1
has gross 6000, cash 5500, fee 200, tax 100, held 100 and adjustment 100 with an
explicit reason. Statement 2 has gross 4001, cash 3801, fee 200 and zero other
components. Both distributions explicitly supply `["platform", "organizer"]`.
The first allocates 500 / 5000; the second allocates 0 / 3801. Final confirmed and
distributed cash is 9301, non-cash accounting and outstanding obligations are
700, and open receivable is zero. Tax and held stay non-cash. Statements never
change distribution totals by themselves.

`boundaries` exits **1**, continuing through explicit replay, conflicting keys,
non-list/duplicate/missing/unknown order refusals, a changed frozen order and a
partial-refund distribution refusal. Historical receipts remain first snapshots;
accepted replay does not apply money again. Partial refunds retain
`refund_bearer_policy: UNDEFINED`, block further distribution and preserve prior
allocations. Repeating a movement under a fresh observation key remains the
existing economically inert journal-entry characterization.

All amounts, rates and role labels are caller-supplied synthetic examples.
Waterfall values remain **UNDETERMINED — User/accounting**; recipient-priority
policy remains **UNDETERMINED — Astra**; refund liability remains
**UNDETERMINED — User/legal**. No policy, protocol command, catalogue/SDK, F04,
persistence, external service or production runtime is added. Mock provenance
and false funds/finality/durability flags remain. In-memory replay does not prove
durability, bank exactly-once, chain finality or cross-machine rollback.
See the [coverage and actual verification record](../../validation/2026-11-03-plan-local-ticket-statement-distribution/README.md).

### Settlement failure, cancellation and reconciliation on the shared ticket desk

`desk.settlement` also exposes three direct, single-call forwards to the existing
`SettlementMachine`. No wrapper validation, defaults, cache, source fetch, retry
or inferred compensation is added. Receipts and exceptions propagate unchanged.
In Python, `settlement_id` may be positional; every other parameter is required
and keyword-only. The JSONL envelope remains exactly `surface`, `operation`,
`arguments`, with `surface: "settlement"` and these exact argument fields:

| Operation | Required arguments | Output |
|---|---|---|
| `fail` | `settlement_id`, `idempotency_key`, `reason` | `receipt` |
| `cancel` | `settlement_id`, `idempotency_key`, `reason` | `receipt` |
| `reconcile` | `settlement_id`, `idempotency_key` | `receipt` |

```python
desk.settlement.fail("claim", idempotency_key="decline", reason="synthetic-decline")
desk.settlement.reconcile("claim", idempotency_key="local-check")
```

Failure and cancellation accept `INITIATED` and `AUTHORIZED`, refuse after
`CAPTURED` or `COMMITTED` with `ILLEGAL_TRANSITION`, and produce terminal
`FAILED` or `CANCELLED` respectively. Fresh-key terminal mutation refuses with
`TERMINAL_IMMUTABLE`. An exact accepted replay returns the first snapshot with
`duplicate: true`, `applied: null`; changed operation, settlement identity or
body under a bound key yields `IDEMPOTENCY_CONFLICT`. Historical receipts do
not become current views. The FSM's validation order and retained refusals apply.

Reconciliation works in every existing phase, including terminal phases. Its
receipt includes `matched`, `state_digest`, `entry_count`, `settlement` and
existing provenance/execution flags. It compares this process's journal replay
with its state, adds no economic journal entry and performs no repair. The same
key returns the historical reconciliation snapshot; an explicit fresh key sees
current state. In-memory journal restoration forgets reconciliation receipts
and retained refusals; this is process-local idempotency, not durable closure
or bank reconciliation. These are local selectors, with no new protocol command.

Run either transcript as a file or stdin from the repository root:

```sh
for scenario in exceptions reconciliation; do
  PYTHONDONTWRITEBYTECODE=1 python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_exceptions_session.json \
    --requests "reference/booking_resale_admission/fixtures/ticket_operations_settlement_${scenario}.jsonl"
  PYTHONDONTWRITEBYTECODE=1 python3 reference/booking_resale_admission/ticket_operations_cli.py \
    --fixture reference/booking_resale_admission/fixtures/ticket_operations_settlement_exceptions_session.json \
    --requests - < "reference/booking_resale_admission/fixtures/ticket_operations_settlement_${scenario}.jsonl"
done
```

The exception journey exits 1 after explicit successes/refusals and continues
through every line. The reconciliation journey exits 0, explicitly capturing,
committing/observing recorded statements, distributing, binding a refund and
observing synthetic acceptance between historical and fresh reports. Structural
JSON/schema errors exit 2 immediately; domain refusals exit 1 and continue.
Fixture version 1 is unchanged. The issued anchor, both adoptions and explicit
clocks are retained; `reserve-2` is bound to a pre-capture `claim-2`.

These controls never automatically cancel reservations, release inventory,
change ownership, refund money or close external returns. Legal termination
and refund effects remain **UNDETERMINED — User/legal**. No real PG/bank/KYC,
network, funds, chain execution, persistence or runtime activation is involved.
See the [coverage and actual verification record](../../validation/2026-11-03-plan-local-ticket-settlement-exceptions/README.md).

## Locally calculated booking quotes

`--calculated-quotes PATH` opts either booking desk into a synthetic calculation
source. It is mutually exclusive with the unchanged `--quotes PATH` recorded
source. Both feed the existing `BookingQuoteAdapter` and
`confirm_recorded_quote` selector; the shared selector keeps `surface="booking"`.
No source is enabled by default.

The source-only fixture has exactly these fields (the complete runnable requests
are in [calculated_booking_quotes.json](fixtures/calculated_booking_quotes.json)):

```json
{
  "fixture_version": 1,
  "provenance": "CALCULATION_ONLY",
  "calculations": [
    {
      "recording_id": "calc-1",
      "reservation_id": "reserve-1",
      "request_text": "<complete kix:commerce:2 request JSON text>"
    }
  ]
}
```

Version is integer `1`; recording IDs must be unique and all booking identifiers
must be explicit and valid. An empty `calculations` array provides no requests.
Loading checks structure only: it does not calculate, fetch, initialize a clock,
register a show or hold inventory. Embedded text is decoded afresh on fetch using
unchanged bounded CE1 decoding, preserving number tokens (including rejection of
fractions, exponents, negative zero, duplicate fields and nonfinite numbers).

The complete commerce request requires `schemaVersion`, `orderId`, `orderVersion`,
`scope`, `policyRef`, `expiresAt`, `lines`, `discounts`. Scope requires `issuerId`,
`eventId`, `performanceId`. The single line requires `lineId`, `inventoryId`,
`gross`; gross requires `asset`, `atoms`. The only accepted asset is the complete
existing KRW specification: `namespace="fiat"`, `reference="KRW"`, integer
`decimals=0`, `maxAtoms="340282366920938463463374607431768211455"`.
Atoms are canonical unsigned decimal strings, with booking amount `1..10**12`.
`discounts` must be `[]`, including rejection of zero-effect rules; zero or
multiple lines and alternate asset metadata are refused. There is no asset
conversion, rounding, line selection or price adjustment.

`calculate_booking_quote(request_text)` returns the complete detached unchanged
`commerce.build_quote` calculation with `evidenceClass="CALCULATION_ONLY"`.
`CalculatedBookingQuoteSource(requests={recording_id: {"reservation_id": ...,
"request_text": ...}})` copies entries into immutable storage and exposes detached
fetch results and tuple call snapshots. Fetch returns exactly `reservation_id`,
`amount=int(totals.payableAtoms)` and opaque `quote_ref=quoteHash`, or `None` for
absence. The calculator loads lazily from the repository without adding a
calculator import path. Only modules are retained, never calculation successes.

Run from the repository root with supported Python 3.12 and no bytecode writes:

```bash
export PYTHONDONTWRITEBYTECODE=1
python3.12 reference/booking_resale_admission/booking_cli.py \
  --calculated-quotes reference/booking_resale_admission/fixtures/calculated_booking_quotes.json \
  --requests reference/booking_resale_admission/fixtures/booking_calculated_confirm.jsonl
python3.12 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
  --calculated-quotes reference/booking_resale_admission/fixtures/calculated_booking_quotes.json \
  --requests - < reference/booking_resale_admission/fixtures/ticket_operations_calculated_confirm.jsonl
```

The [booking](fixtures/booking_calculated_confirm.jsonl) and
[shared](fixtures/ticket_operations_calculated_confirm.jsonl) confirm journeys
explicitly set the clock, register a show, hold a slot and confirm using the
calculated amount/hash, then replay and view. The separate
[booking boundaries](fixtures/booking_calculated_boundaries.jsonl) and
[shared boundaries](fixtures/ticket_operations_calculated_boundaries.jsonl)
exercise refusals, changed-input conflicts, cancellation/historical replay and
reservation expiry. Expected exits are `0` for confirm and `1` for boundaries;
structural/file/session-prerequisite failures exit `2`. Source refusals continue.
The shared fixture already contains unrelated synthetic issued inventory; these
journeys use a separate show/reservation and leave other surfaces unchanged.

Every identifier-valid explicit selector fetches once, including replay. Invalid
caller identifiers fetch zero times. No retry, polling, cached-success fallback
or FSM/key mutation occurs on source rejection. Reservation primary-price
equality, expiry and immutable first results remain FSM-owned. Calculation
`orderId`, scope, policy reference and `expiresAt` are hash-bound caller metadata,
not authenticated booking order/show/expiry authority. The sample intentionally
uses calculation expiry `1` separately from the explicit reservation clock/expiry;
this adapter is not the commerce payment-planning expiry gate.

Calculation provenance does not replace booking receipts' unchanged
`MOCK_GATE_ONLY` provenance or false `quote_policy_approved` / `discount_applied`
flags. Pricing, discounts and quote authority remain **UNDETERMINED — Astra/User**;
tax/accounting treatment remains **UNDETERMINED — User and designated advisers**.
This supplies no authenticated quote authority, payment handoff, settlement,
issuance, persistence, network call, protocol/catalogue/SDK change or runtime
activation. See the [builder evidence and remaining delivery gates](../../validation/2026-11-03-plan-local-calculated-booking-quotes/README.md).

## Source-backed issued ticket handoff on the shared desk

`issued_ticket_adapter.IssuedTicketAdapter(source, *, resale, admission)` reads
`source.view(reservation_id)` and `source.view_show(show_id)` on each explicit
`apply(*, surface, reservation_id, right_id, idempotency_key)` invocation. The
shared `TicketOperationsSession.adopt_issued_from_booking` uses the same
reservation machine as booking, resale and admission. Construction adds no reads
or mutations. Only `resale` and `admission` are accepted targets.

After a separate explicit booking `issue` request, adopt on each desired surface
with separate requests. No show, booking, policy or payment fields are resupplied:

```json
{"surface":"resale","operation":"adopt_issued_from_booking","arguments":{"reservation_id":"reserve-2","right_id":"issue-2","idempotency_key":"second-resale-adopt"}}
{"surface":"admission","operation":"adopt_issued_from_booking","arguments":{"reservation_id":"reserve-2","right_id":"issue-2","idempotency_key":"second-admission-adopt"}}
```

Each invocation forwards exactly once to the selected session's existing
`adopt_issued`, returning its receipt unchanged. The explicit expected right must
match the recorded issuance and right; reservation/show/slot identities must
agree. Unrelated view fields are allowed. Required source fields and scalar
bounds are checked without coercion or defaults. Explicit `quote_ref: null` is
preserved; `gate_roles` is copied in its recorded order.

| Read | Forwarded fields |
|---|---|
| Reservation view | `reservation_id`, `show_id`, `slot`, `buyer_role`, `expires_ms`, `order_id`, `amount`, `quote_ref`, `payment_ref` |
| Show snapshot | `organizer_role`, `capacity`, `gate_roles`, `primary_price`, `resale_cap`, `resale_allowed`, `organizer_bps`, `platform_bps` |
| Caller | `right_id`, `idempotency_key` |

The buyer and payment are the original booking values. Current ownership, right
version, listing state and later payment/amount fields never replace them.
Missing issuance is a local extraction refusal. Phase, consumption, eligibility,
expiry and existing target key semantics remain the FSM's decisions; there is no
`ISSUED` phase precheck that could suppress historical replay after consumption.

`IssuedTicketSourceError` wraps read failures and
`InvalidIssuedTicketRecord` identifies missing/malformed/mismatched source data
or invalid adapter selectors/identifiers. These local exceptions are not protocol
error codes. Extraction failures invoke no target mutation and bind no target
key, so a later explicit corrected request can use that key. Target refusals pass
through unchanged, including retained refusals and changed-body key conflicts.
Every invocation rereads the source; no cache, retry or fallback is added.

The selector exists only in the shared local desk. Standalone CLIs and manual
`adopt_issued` retain their existing complete schemas. Structural JSON/schema
errors stop the stream with exit 2; source/domain refusals continue and yield
exit 1; an all-success stream exits 0.

Run either transcript with file input or stdin (both intentionally exit 1):

```bash
python3 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json \
  --requests reference/booking_resale_admission/fixtures/ticket_operations_issued_handoff.jsonl
python3 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_fulfillment_session.json \
  --requests - < reference/booking_resale_admission/fixtures/ticket_operations_issued_handoff_boundaries.jsonl
```

The lifecycle transcript keeps issuance, both adoptions, listing, authorization
and consumption separate and replays historical receipts after consumption. The
boundary transcript demonstrates missing/unissued/mismatched sources, explicit
issuance and recovery using the same keys, then target refusals and key conflicts.
No automatic second adoption, listing, payment observation, authorization,
consumption, clock change or credential reissuance occurs. Mock-only flags and
fixture prerequisites remain unchanged. This is in-memory synthetic input
plumbing, without persistence, network/provider integration, funds, chain or
runtime activation. Product policy remains **UNDETERMINED — Astra/User**; legal
effects remain **UNDETERMINED — User/legal**. See the
[validation record](../../validation/2026-11-03-plan-local-issued-ticket-handoff/README.md)
for source-informed coverage, actual commands and pending delivery gates.
# Initiating settlement from local ticket records

The shared `TicketOperationsSession` exposes two explicit Python methods and
matching `surface: "settlement"` JSONL selectors:

| Selector | Required arguments |
|---|---|
| `initiate_from_booking` | `settlement_id`, `reservation_id`, `idempotency_key`, `trade_id`, `debtor_role`, `policy` |
| `initiate_from_resale` | `settlement_id`, `listing_id`, `idempotency_key`, `trade_id`, `debtor_role`, `policy` |

`settlement_id` may be positional in Python; all other arguments are required
keywords. `policy` is the existing complete object with `kind`, `fee_bps`,
`residual_payee` and `fee_payee`. Values below are synthetic caller inputs,
not product policy or inferred legal roles:

```python
from ticket_operations_fixture import load_fixture

desk = load_fixture("reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json")
desk.settlement.initiate_from_booking(
    "claim-2", reservation_id="reserve-2", idempotency_key="booking-input",
    trade_id="explicit-booking-trade", debtor_role="explicit-debtor",
    policy={"kind": "PRIMARY_FEE_BPS", "fee_bps": 500,
            "residual_payee": "organizer", "fee_payee": "platform"})
# Binding, authorization, capture, statements and distribution are separate calls.
```

```json
{"surface":"settlement","operation":"initiate_from_resale","arguments":{"settlement_id":"resale-claim","listing_id":"list-1","idempotency_key":"resale-input","trade_id":"explicit-resale-trade","debtor_role":"explicit-debtor","policy":{"kind":"PRIMARY_FEE_BPS","fee_bps":500,"residual_payee":"organizer","fee_payee":"platform"}}}
```

The resale example requires an existing listing (see the runnable transcript).
Each request, including replay, reads the selected reservation/listing `view`
once from the same session graph. It requires matching valid source identity,
positive non-boolean integer `amount` in `1..10**12` and exact `"KRW"` currency.
Booking also requires a valid recorded `order_id`; its current phase need not
be `CONFIRMED`. Other source view fields are allowed. No auxiliary show/right
lookup, coercion, fallback, cache, polling or retry is added by the adapter.
After source validation it calls the unchanged `SettlementMachine.initiate`
once, copying amount/currency and forwarding all caller target inputs unchanged.
The target validates settlement/trade identities, debtor role and complete policy.

Unavailable/faulting source reads raise local `SettlementInputSourceError`;
malformed/mismatched records raise its `InvalidSettlementInputRecord` subclass.
These failures perform zero settlement mutations and leave the target key free.
Target errors and first receipts propagate unchanged. Source identity is absent
from the existing target fingerprint/journal: identical extracted target bodies,
even from different sources, retain manual/source replay equivalence. Changed
target bodies keep the existing `IDEMPOTENCY_CONFLICT` behavior. No source-to-trade
binding or source eligibility rule is established. Manual `initiate` remains available.

CLI arguments must match exactly; `gross`/`currency` overrides are structural
errors. Output retains `{surface,operation,receipt}` or `error:{type,message}`
for local source errors and `error:{code}` for FSM refusals. Exit 0 means all
requests succeeded, 1 means source/domain refusal with explicit-line continuation,
and 2 means a structural error that stops input. No follow-up is automatic.

Runnable file and stdin transcripts, from repository root:

```bash
fixture=reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_session.json
for scenario in booking resale boundaries; do
  requests="reference/booking_resale_admission/fixtures/ticket_operations_settlement_inputs_${scenario}.jsonl"
  python3 reference/booking_resale_admission/ticket_operations_cli.py --fixture "$fixture" --requests "$requests"
  python3 reference/booking_resale_admission/ticket_operations_cli.py --fixture "$fixture" --requests - < "$requests"
done
```

Booking and resale exit 0; boundaries exits 1. Each begins with fresh synthetic
setup, preserving the issued anchor. Booking uses its existing setup-only payment
observation. Resale explicitly lists, initiates before payment, binds, authorizes,
captures, commits one recorded statement, distributes, observes a later statement,
distributes again, observes recorded payment and transfers. Booking separately
binds and issues. Replay returns the initial receipt after those later operations.
Boundaries demonstrates absent sources, same-key repair, exact replay, changed
trade and retained invalid-policy conflicts. See [builder evidence](../../validation/2026-11-04-plan-local-ticket-settlement-inputs/README.md).

Initiation does not bind tickets, observe payment, authorize, capture, distribute,
issue or transfer. Mock provenance and false execution/durability flags remain.
Product policy is **UNDETERMINED — Astra/User**; legal debtor and accounting
treatment are **UNDETERMINED — User/legal/accounting**. This is sequential,
in-memory synthetic integration; it establishes no authority, production runtime,
cross-machine rollback, durable funds execution or bank/chain finality.

## Request-time calculated booking confirmation

A running `BookingSession` accepts complete calculation text directly, without
preloading a quote recording:

```python
receipt = session.confirm_calculated_quote(
    request_text, reservation_id="reserve-1", order_id="order-1",
    idempotency_key="confirm-1",
)
# On the shared graph: desk.booking.confirm_calculated_quote(...)
```

The caller must explicitly set the session clock, register the show and hold the
reservation first. The three booking identifiers are validated before calculation.
Every valid invocation, including replay, calls `calculate_booking_quote` once,
then `self.confirm` once with the exact integer payable amount and opaque quote
hash. Its receipt is returned unchanged. No calculation result is cached; no
recording ID, source construction/fetch, clock advance, retry, payment,
settlement binding or issuance is introduced.

Both JSONL desks accept the strict local selector below without `--quotes` or
`--calculated-quotes`. Shared requests additionally require `"surface":"booking"`.
This is local composition of existing confirmation, not a new protocol command.

```json
{"operation":"confirm_calculated_quote","arguments":{"request_text":"<complete kix:commerce:2 request JSON text>","reservation_id":"reserve-1","order_id":"order-1","idempotency_key":"confirm-1"}}
```

No extra or missing envelope/argument fields are accepted. The full inner text
uses the [unchanged calculation schema and limits](#locally-calculated-booking-quotes):
`schemaVersion="kix:commerce:2"`, `orderId`, `orderVersion`, `scope` (`issuerId`,
`eventId`, `performanceId`), `policyRef`, `expiresAt`, exactly one `lines` entry
(`lineId`, `inventoryId`, `gross` with complete KRW `asset` and canonical decimal
string `atoms`), and `discounts=[]`. Booking amounts remain `1..10**12`, with exact
arithmetic and primary-price equality. Bounded CE1 decoding rejects malformed
text, duplicate fields and unsupported numeric forms/assets/discount rules.

Calculation `orderId`, scope and `expiresAt` are hash-bound metadata; they are
not equated with booking identities or the reservation expiry clock. Equivalent
JSON formatting preserves the hash and replay binding. Existing confirmation
owns price equality, reservation expiry, key conflicts, retained refusals and
immutable first results. Replay can return a historical confirmed receipt while
the current view shows cancellation.

Calculation/input failures use `InvalidBookingQuoteRecord` (or existing
`BookingQuoteSourceError` normalization for an unexpected calculator exception).
They never invoke confirmation or bind its key, even after an earlier success.
Source/domain refusals emit existing error shapes, continue through subsequent
lines and exit 1. Structural errors and missing explicit session prerequisites
stop immediately with exit 2; successful transcripts exit 0. Confirmation
exceptions retain their existing identity/classification. Results keep
`{operation, receipt}` and shared `surface` envelopes.

From the repository root, run the complete file and stdin examples without a
startup quote source:

```bash
PYTHONDONTWRITEBYTECODE=1 python3.12 reference/booking_resale_admission/booking_cli.py \
  --requests reference/booking_resale_admission/fixtures/booking_calculation_inputs_confirm.jsonl
PYTHONDONTWRITEBYTECODE=1 python3.12 reference/booking_resale_admission/ticket_operations_cli.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
  --requests - < reference/booking_resale_admission/fixtures/ticket_operations_calculation_inputs_confirm.jsonl
```

The [booking confirm](fixtures/booking_calculation_inputs_confirm.jsonl) and
[shared confirm](fixtures/ticket_operations_calculation_inputs_confirm.jsonl)
journeys explicitly clock/show/hold, calculate/confirm, replay and view. The
[booking boundaries](fixtures/booking_calculation_inputs_boundaries.jsonl) and
[shared boundaries](fixtures/ticket_operations_calculation_inputs_boundaries.jsonl)
journeys reject malformed text/assets/discounts/multiple lines, retain price and
expiry refusals, reject changed-input keys, cancel and replay historical results.
They intentionally exit 1. Shared identities are separate from fixture history.

`test_booking_calculation_inputs.py` covers method call counts, source rejection
atomicity/key reuse, invalid identifiers, error identity, changed-input conflicts,
price endpoints and opaque metadata. `test_booking_calculation_inputs_cli.py`
compares each journey step's receipts/errors/state/digests/journals with the
existing calculated-source/adapter path; it also covers strict envelopes,
file/stdin exits, source-free startup and unchanged other shared machines/source
calls. Existing calculator/FSM/adapter regressions supply the underlying
coverage; see the [coverage map and actual evidence](../../validation/2026-11-04-plan-local-booking-calculation-inputs/README.md).

Calculation `evidenceClass="CALCULATION_ONLY"` remains distinct from receipt
`provenance="MOCK_GATE_ONLY"`. All authority, finality and durability flags remain
false. Pricing and quote authority remain **UNDETERMINED — Astra/User**;
tax/accounting treatment remains **UNDETERMINED — User/designated advisers**.
B03/B05 remain partial mock capabilities; this is no operational activation or
production durability, distributed fencing, bank exactly-once or chain-finality
evidence.

## Calculation-only booking quote preview

`BookingSession.preview_calculated_quote(request_text)` returns the complete,
unchanged `calculate_booking_quote` result. The shared graph exposes the same
method as `desk.booking.preview_calculated_quote(request_text)`. Each invocation
calculates once and returns a fresh result; modifying a returned quote does not
affect later previews or confirmation.

Both local JSONL booking desks accept:

```json
{"operation":"preview_calculated_quote","arguments":{"request_text":"<complete kix:commerce:2 request JSON text>"}}
```

Shared requests additionally require `"surface":"booking"`. Standalone responses
contain exactly `{operation, quote}`; shared responses contain
`{surface, operation, quote}`. No startup quote-source flag is required. This is a
local calculation selector, with no new protocol command or catalogue query.

The inner request uses the existing strict CE1 schema:

```json
{
  "schemaVersion": "kix:commerce:2",
  "orderId": "calculation-order",
  "orderVersion": 1,
  "scope": {"issuerId": "fixture-issuer", "eventId": "fixture-event", "performanceId": "fixture-performance"},
  "policyRef": "fixture-policy",
  "expiresAt": 1,
  "lines": [{"lineId": "L1", "inventoryId": "fixture-inventory", "gross": {
    "asset": {"namespace": "fiat", "reference": "KRW", "decimals": 0, "maxAtoms": "340282366920938463463374607431768211455"},
    "atoms": "10001"
  }}],
  "discounts": []
}
```

The result `quote` has exactly `schemaVersion`, `evidenceClass`, `request`, `asset`,
`lines`, `totals` and `quoteHash`. `evidenceClass` is `"CALCULATION_ONLY"`.
`request` contains the complete calculation input, and `asset` retains the complete
KRW metadata above. Each result line has `lineId`, `inventoryId`, `grossAtoms`,
`discountAtoms`, `payableAtoms` and `discounts`. `totals` has `grossAtoms`,
`discountAtoms` and `payableAtoms`. Every atom amount remains an exact decimal
string. For this example those three amounts are `"10001"`, `"0"`, `"10001"`,
respectively, in both the line and totals; `quoteHash` is the unchanged
calculator's hash. No receipt flags or integer conversions are added to preview.

The boundary remains exactly one line, the complete existing KRW asset,
`discounts=[]` (even zero-valued discount rules are refused), and payable amount
`1..10**12`. Preview uses the existing calculator's bounded decoding and rejection
rules without an additional inner parser. Calculation `orderId`, scope and
`expiresAt` remain hash-bound metadata. Preview establishes no reservation
validity, quote currentness, price approval or authenticated quote authority.

Preview neither accesses reservation state nor changes any shared FSM, journal,
clock or source-call history. It needs no session mutation clock, reservation ID
or idempotency key. Extra arguments including those fields are structural errors.
Confirmation remains a separate explicit operation:

```python
quote = session.preview_calculated_quote(request_text)  # works before setup
# Explicitly set_clock, register_show and hold before confirming.
receipt = session.confirm_calculated_quote(
    request_text, reservation_id="reserve-1", order_id="order-1",
    idempotency_key="confirm-1",
)
# receipt["reservation"]["amount"] == int(quote["totals"]["payableAtoms"])
# receipt["reservation"]["quote_ref"] == quote["quoteHash"]
```

Confirmation recalculates the supplied text and retains existing primary-price,
reservation-expiry, key-conflict, retained-refusal and historical-replay checks.
Preview does not reserve inventory or automatically confirm, pay, bind settlement
or issue a right. Source/calculation exceptions retain their existing classes;
unexpected calculator exceptions use the existing `BookingQuoteSourceError`
normalization. Success exits 0; calculation/domain refusals continue and exit 1;
malformed envelopes (including duplicate keys) stop immediately with exit 2.
Invalid inner calculation text is a calculation refusal, not an outer-envelope
error. A later explicit confirmation still needs its session clock.

Run the file and stdin examples from the repository root:

```bash
for scenario in confirm boundaries; do
  requests="reference/booking_resale_admission/fixtures/booking_quote_preview_${scenario}.jsonl"
  python3.12 -B reference/booking_resale_admission/booking_cli.py --requests "$requests"
  python3.12 -B reference/booking_resale_admission/booking_cli.py --requests - < "$requests"
  requests="reference/booking_resale_admission/fixtures/ticket_operations_quote_preview_${scenario}.jsonl"
  fixture=reference/booking_resale_admission/fixtures/ticket_operations_session.json
  python3.12 -B reference/booking_resale_admission/ticket_operations_cli.py --fixture "$fixture" --requests "$requests"
  python3.12 -B reference/booking_resale_admission/ticket_operations_cli.py --fixture "$fixture" --requests - < "$requests"
done
```

The [booking](fixtures/booking_quote_preview_confirm.jsonl) and
[shared](fixtures/ticket_operations_quote_preview_confirm.jsonl) confirmation
transcripts preview before any session clock, then explicitly set up, preview,
confirm, replay and view. The [booking boundary](fixtures/booking_quote_preview_boundaries.jsonl)
and [shared boundary](fixtures/ticket_operations_quote_preview_boundaries.jsonl)
transcripts preserve calculator and confirmation refusals, cancellation and
historical replay. Confirmation transcripts exit 0; boundary transcripts exit 1.
Shared booking identities remain separate from the existing fixture history.

`test_booking_quote_preview.py` and `test_booking_quote_preview_cli.py` cover the
preview integration gaps; see the [coverage map and actual validation evidence](../../validation/2026-11-04-plan-local-booking-quote-preview/README.md).
These are source-informed local tests. B03/B05 remain partial mock capabilities.
Pricing/quote authority remains **UNDETERMINED — Astra/User**; tax/accounting
remains **UNDETERMINED — User/designated advisers**. No production, durability,
bank exactly-once, distributed fencing, legal-compliance or chain-finality claim
is made.

## Request-time synthetic settlement facts

`TicketSettlementSession` on the shared desk accepts these complete caller inputs:

```python
desk.settlement.observe_statement(
    settlement_id, idempotency_key=key, movement_id=movement_id,
    gross=gross, amount=amount, fee=fee, tax=tax, held=held,
    adjustment=adjustment, adjustment_reason=adjustment_reason,
)
desk.settlement.observe_mock_cancel_acceptance(
    settlement_id, idempotency_key=key, source_id=source_id, amount=amount,
)
```

Every parameter is required; parameters after `settlement_id` are keyword-only.
Each call forwards once to the identically named existing public settlement FSM
method and returns its receipt or raises its error unchanged. No recording source
is required or fetched. Manual `commit`, recorded observations, distribution,
refund binding, exception controls and reconciliation remain available.

The shared JSONL envelope is exactly `{surface, operation, arguments}` with
`surface: "settlement"`. Required argument fields are:

| Operation | Exact arguments |
|---|---|
| `observe_statement` | `settlement_id`, `idempotency_key`, `movement_id`, `gross`, `amount`, `fee`, `tax`, `held`, `adjustment`, `adjustment_reason` |
| `observe_mock_cancel_acceptance` | `settlement_id`, `idempotency_key`, `source_id`, `amount` |

For example, after an explicit partial commit on `claim-2`:

```json
{"surface":"settlement","operation":"observe_statement","arguments":{"settlement_id":"claim-2","idempotency_key":"later","movement_id":"later","gross":4001,"amount":3801,"fee":200,"tax":0,"held":0,"adjustment":0,"adjustment_reason":null}}
{"surface":"settlement","operation":"observe_mock_cancel_acceptance","arguments":{"settlement_id":"claim-2","idempotency_key":"accept","source_id":"accept","amount":1000}}
```

Include `adjustment_reason: null` explicitly when adjustment is zero. Malformed
JSON, duplicate keys, nonfinite numbers, wrong containers and missing/extra fields
stop before delegation. Well-shaped domain-invalid values reach the unchanged
FSM; its retained refusal and idempotency semantics apply. Identical direct and
recorded facts share one key space and replay the first receipt even after later
state changes. Changed bodies, settlement IDs or operations with a used key
conflict; fresh keys do not bypass movement/source binding. Responses retain
`{surface, operation, receipt}` or the existing error envelope. Exit 0 means all
requests succeeded; exit 1 means domain refusals occurred and subsequent explicit
lines ran; exit 2 means structural failure stopped processing.

From repository root, run both file and stdin journeys:

```bash
fixture=reference/booking_resale_admission/fixtures/ticket_operations_settlement_fact_inputs_session.json
for scenario in journey boundaries; do
  requests="reference/booking_resale_admission/fixtures/ticket_operations_settlement_fact_inputs_${scenario}.jsonl"
  python3 reference/booking_resale_admission/ticket_operations_cli.py --fixture "$fixture" --requests "$requests"
  python3 reference/booking_resale_admission/ticket_operations_cli.py --fixture "$fixture" --requests - < "$requests"
done
```

The version-1 `MOCK_GATE_ONLY` fixture retains the issued anchor and explicit
clock/adoption setup; all five recording arrays are empty. Optional `statements`
and `cancel_acceptances` may also be omitted. The journey (exit 0) explicitly
commits `6000 = 5500 + 200 + 100 + 100 + 100`, observes the later
`4001 = 3801 + 200`, distributes in caller order, binds a 4000 refund and observes
1000 synthetic acceptance. Cash stays 9301, refund outstanding becomes 3000 and
PG adjustment outstanding becomes 1000. These values and distribution order are
synthetic examples, not policy. Boundaries (exit 1) demonstrates retained phase
and refund refusals, replay, changed bodies, identity conflicts and overflows.

Observation performs no automatic distribution, refund binding/completion, ticket
mutation, retry or clock adjustment. `MOCK_SETTLEMENT_ONLY`, `IN_MEMORY_FSM`,
unsupported external payment and false funds/bank/return-closure/right-cancellation/
durability flags remain, even after full synthetic acceptance. Distribution
priorities and refund-burden policy remain **UNDETERMINED — Astra/User**;
legal/accounting effects remain **UNDETERMINED — User/designated advisers**.
No persistence, provider calls or production capability is delivered. See the
[coverage and actual builder evidence](../../validation/2026-11-04-plan-local-settlement-fact-inputs/README.md).

## Live local subprocess client

[`ticket_operations_client.py`](ticket_operations_client.py) is an importable,
standard-library client for the existing shared JSONL desk. Importing it launches
nothing. `TicketOperationsClient.launch(fixture, *, quotes=None,
calculated_quotes=None, cleanup_timeout=...)` explicitly starts one child using
`sys.executable`; quote fixture options are mutually exclusive. The child uses
ordinary Python buffering and flushes every complete response. Its in-memory
service graph stays alive until closed; it does not persist across launches.

Set `PYTHONPATH` to `reference/booking_resale_admission` when importing from the
repository root. For example, using the repository's synthetic fixtures:

```python
from ticket_operations_client import TicketOperationsClient

with TicketOperationsClient.launch(
    "reference/booking_resale_admission/fixtures/ticket_operations_session.json",
    cleanup_timeout=1,  # caller's cleanup budget, not a response deadline
) as desk:
    listed = desk.request({
        "surface": "resale", "operation": "list_resale",
        "arguments": {"offer_id": "offer-1", "listing_id": "list-1",
                      "idempotency_key": "caller-list"},
    })
    # Inspect the returned envelope before explicitly deciding the next request.
    if "receipt" in listed:
        listing = listed["receipt"]["listing"]
        current = desk.request({
            "surface": "resale", "operation": "view",
            "arguments": {"listing_id": listing["listing_id"]},
        })
```

Run the complete listing → view → cancellation → view example:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 reference/booking_resale_admission/example_ticket_operations_client.py \
  --fixture reference/booking_resale_admission/fixtures/ticket_operations_session.json \
  --offer-id offer-1 --listing-id list-1 --list-key caller-list --cancel-key caller-cancel \
  --cleanup-timeout 1
```

All identities and the cleanup budget above are synthetic caller choices, not
policy defaults. The example derives the listing identity and seller from the
first receipt, stops on errors, and prints unmodified envelopes with all mock
labels. Example exits: 0 for the completed journey, 1 for a desk error, 2 for
local transport uncertainty. Desk batch exits remain 0/1/2 as before.

`request(dict)` submits one UTF-8 JSONL line once and blocks for one complete
response before returning its decoded envelope. Only one request may be
outstanding. Concurrent/reentrant calls and concurrent cleanup fail locally with
`TicketDeskClientStateError` before writing. Serialization failures also occur
before writing. Arguments are still validated by the existing desk dispatchers;
no selectors, protocol commands or SDK/catalogue entries are added.

Domain `{code}` and source `{type,message}` errors return unchanged and allow
another explicit caller request. `FixtureError`, `BookingInputError` and startup
error envelopes are terminal: they return unchanged and fence further requests.
A startup error may race a broken pipe; only a fully received valid error
envelope is a known desk result.

Once submission begins, EOF, short writes, broken pipes, truncated lines,
malformed UTF-8/JSON/envelopes, selector mismatches or caller interruption raise
`TicketDeskTransportUncertainty` and permanently fence the client. Its `request`,
`request_bytes` and `reply_bytes` retain the submitted snapshot and observed
reply bytes in memory; `client.uncertainty` retains that same exception after
cleanup. No business failure, rollback or permission to resend follows from
uncertainty. There is no automatic retry, replay, restart or replacement child.

Reads have no response timeout. Caller interruption fences an interrupted
exchange; it does not establish what the desk accepted. Finish or interrupt the
requesting caller before cleanup. `close()` closes stdin, waits for the owned
child and returns its actual exit code; repeated calls return the retained code.
The required finite positive `cleanup_timeout` bounds each graceful/termination
wait during cleanup only. Cleanup terminates then kills/reaps if needed, closes
descriptors, preserves uncertainty and cannot undo accepted operations. Context
manager exit runs the same cleanup, including on caller exceptions.

This remains **MOCK_GATE_ONLY**, in-memory, local and non-production. No sockets,
frontend, storage, external providers or funds are used. Product timing,
authentication, pricing, distribution and refund policy remain
**UNDETERMINED — Astra/User**. Source-informed parity is not independent review,
durability, chain finality or production readiness evidence. See the
[coverage and actual builder evidence](../../validation/2026-11-04-plan-local-ticket-stdio-client/README.md).
