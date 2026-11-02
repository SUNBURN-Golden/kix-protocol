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

The five public methods and all required arguments are:

| Local method selector | Arguments |
|---|---|
| `authorize_admission` | `presentation_id`, `admission_id`, `idempotency_key`, `gate_role`, `expires_ms` |
| `consume` | `presentation_id`, `consume_id`, `idempotency_key`, `gate_role` |
| `view` | `right_id` |
| `view_credential` | `right_id`, `version`, `holder_role` |
| `set_clock` | `subject_id`, `idempotency_key`, `now_ms` |

Python authorization/consumption accept a positional presentation ID and the
remaining arguments as keyword-only, matching the adapter. Views and clock
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
| `list_resale` | `offer_id`, `listing_id` |
| `hold_buy` | `hold_id`, `listing_id`, `buyer_role` |
| `release_hold` | `hold_id`, `buyer_role` |
| `cancel_listing` | `listing_id`, `seller_role` |
| `observe_recorded_payment` | `recording_id`, `listing_id` (optional configured synthetic payment source required) |
| `observe_resale_payment` | `listing_id`, `payment_ref`, `amount`; optional `buyer_role` (default `None`) |
| `bind_settlement` | `listing_id`, `settlement_id` |
| `accept_resale` | `transfer_id`, `listing_id` |
| `close` | `listing_id` |
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
admission reads that same resale machine as its ownership source. Its `.resale`
and `.admission` are the existing sessions, using the existing offer/presentation
adapters. Each construction is a fresh sequential in-memory graph.

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
optional `payments` (documented below).
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

`surface` is exactly `resale` or `admission`. All thirteen resale selectors and five
admission selectors documented above retain their exact arguments, including
optional resale payment `buyer_role`. The existing dispatchers validate them;
cross-surface selectors, setup and a settlement surface are refused. Output adds
`surface` to the existing `operation` plus `receipt`, `view` or `error` envelope.
Domain errors retain `{code}`; local errors retain `{type,message}`. Exit 0 means
all supplied requests succeeded, exit 1 records domain/source refusals, and exit
2 means structural/setup/file/usage failure. Structural request errors stop input;
other refusals allow only the next explicitly supplied line. Duplicate JSON keys,
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
The following are the only local selectors. Python methods take the first
identity argument positionally or by keyword and the rest by keyword only.
All listed arguments are required; extra arguments are rejected.

| Operation | Exact arguments |
| --- | --- |
| `register_show` | `show_id`, `organizer_role`, `capacity`, `gate_roles`, `primary_price`, `resale_cap`, `resale_allowed`, `organizer_bps`, `platform_bps`, `idempotency_key` |
| `set_clock` | `subject_id`, `now_ms`, `idempotency_key` (subject must be `"clock"`) |
| `hold` | `reservation_id`, `show_id`, `slot`, `buyer_role`, `expires_ms`, `idempotency_key` |
| `release` | `reservation_id`, `idempotency_key` |
| `confirm` | `order_id`, `reservation_id`, `amount`, `quote_ref`, `idempotency_key` |
| `cancel` | `reservation_id`, `idempotency_key` |
| `view` | `reservation_id` |
| `view_show` | `show_id` |

A successful explicit `set_clock` **through this session** is required before
other mutations, even when the supplied machine already has a clock. A successful
replay counts as explicit initialization; it does not change current time.
Views require no clock initialization and do not mutate state. The desk requires
`quote_ref` to be a non-null valid existing identifier (opaque text, not a
validated external quote). Missing clock or invalid quote raises local
`BookingInputError` without calling the FSM or retaining the key. Other validation
is delegated unchanged: identifier length 1..100, capacity and gate-role limits
16, reservation window at most the existing synthetic 900000 ms limit, integer
money and bps checks. These fixture bounds are not approved product TTLs or policy.

Success output contains `operation` and unchanged `receipt` (mutations) or `view`.
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
no payment lookup/observation, settlement binding, issuance, admission, persistence,
external calls or runtime activation. The payment–reservation handoff remains
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
