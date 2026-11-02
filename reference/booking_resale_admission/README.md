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
