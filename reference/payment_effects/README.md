# Synthetic local payment effect desk

An importable session and a strict JSONL CLI over the **unchanged**
`reference/v0.3-rc1` Core using only its in-memory database. The desk exposes the
four already-published effect commands:

- `prepare_effect`
- `send_effect`
- `abort_effect`
- `observe_effect`

Operation identifiers, actors, actions and command bodies keep their existing
published meanings. No new protocol command, catalogue entry or policy value is
introduced.

`send_effect` records a **local intent only**. This tool performs no provider,
bank, chain or network transmission. It does not connect a settlement or F04
FSM and does not implement a pending Finance projection.

## Initialization

A session is created only from an explicit synthetic command fixture. The
fixture is validated structurally first, then every setup command is applied
through `Core.execute` on a fresh `:memory:` database:

```json
{
  "fixture_version": 1,
  "provenance": "synthetic",
  "setup": [
    {
      "operationId": "setup-event",
      "actor": "operator",
      "action": "create_event",
      "body": { "...published create_event body...": "..." }
    }
  ]
}
```

Rules:

- top-level fields are exactly `fixture_version`, `provenance`, `setup`;
- `fixture_version` is the integer `1` and `provenance` is `synthetic`;
- `setup` is a nonempty ordered array of `operationId` / `actor` / `action` /
  `body` objects with unique operation identifiers;
- every `action` is one of the existing discovery/lifecycle setup commands used
  by the fixtures (`create_event`, `prepare_trade`, `accept_trade`, `capture`,
  `settle_capture`, `commit_trade`, `cancel_event`, `complete_event`);
- every `body` is an object and is forwarded unchanged, once, to
  `Core.execute`;
- duplicate JSON keys, non-finite numbers, lone surrogates and non-JSON values
  are refused before a Core is created.

A setup command rejected by Core aborts initialization, closes the private
database and publishes no session. There is no test `Harness`, state injection,
file-backed database or inferred default.

Included synthetic fixtures under `fixtures/`:

| Fixture | Initial synthetic state |
|---|---|
| `cash_refund.json` | settled primary trade, event cancelled; confirmed pool cash available |
| `payout.json` | settled primary trade, event completed; payout obligations open |
| `original_cancel.json` | captured but unsettled primary trade, event cancelled; PG original-cancel route |
| `unsettled_refund.json` | captured but unsettled primary trade, event cancelled; no confirmed cash |

## Python session

```python
from reference.payment_effects import load_fixture

with load_fixture("reference/payment_effects/fixtures/cash_refund.json") as session:
    receipt = session.execute(
        "refund-prepare", "operator", "prepare_effect",
        {
            "domain": "kix:fixture:lifecycle:0.3",
            "effectId": "refund-primary",
            "tradeId": "primary",
            "kind": "REFUND",
            "amount": 100000,
            "routeProfile": "CASH_REFUND_FIXTURE",
            "contractRef": "fixture:cash-refund:v1",
            "beneficiaryAccountRef": "fixture-account:A",
        },
    )
    view = session.view(
        effect_ids=["refund-primary"],
        trade_ids=["primary"],
        accounts=["funds:<pool hash>", "refund:primary"],
    )
```

`PaymentEffectSession.execute` forwards only the four effect actions. Receipts,
Core rejections and replay behaviour are returned unchanged. Local misuse of
the wrapper raises `PaymentEffectLocalError`; using a closed session raises
`PaymentEffectSessionClosed`.

### Selected views

`view` returns **detached** copies taken from one `Core.snapshot`:

```json
{
  "effects": {"<effectId>": {"...": "..."} or null},
  "trades": {"<tradeId>": {"...": "..."} or null},
  "balances": {"<account>": 0}
}
```

Only explicitly selected effect identifiers, trade identifiers and account
names are returned. Unknown identifiers are `null`; an unknown account is `0`.
Reads execute no command and mutating the returned value cannot change Core
state.

## JSONL CLI

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m reference.payment_effects.payment_effect_cli \
  --fixture reference/payment_effects/fixtures/cash_refund.json \
  --requests reference/payment_effects/fixtures/cash_refund.jsonl

# stdin instead of a requests file
PYTHONDONTWRITEBYTECODE=1 python3 -B -m reference.payment_effects.payment_effect_cli \
  --fixture reference/payment_effects/fixtures/cash_refund.json --requests -
```

One JSON object per input line, one canonical JSON frame per output line.

Command request:

```json
{"operationId":"cash-1-prepare","actor":"operator","action":"prepare_effect","body":{"...":"..."}}
```

View request:

```json
{"view":{"effectIds":["refund-primary"],"tradeIds":["primary"],"accounts":["refund:primary"]}}
```

Accepted command frame:

```json
{"evidenceClass":"synthetic","notice":"Synthetic local payment effect desk. ...","receipt":{...}}
```

Accepted view frame carries the same `evidenceClass` and `notice` plus `view`.
Every accepted frame states that `send_effect` is a local intent and that no
provider, bank, chain or network transmission occurs.

Core rejection frame (text preserved unchanged, no envelope relabelling):

```json
{"error":"INSUFFICIENT_CONFIRMED_FUNDS","rejected":true}
```

Local malformed-input frame:

```json
{"localError":{"type":"FixtureError","message":"..."}}
```

Exit codes:

| Code | Meaning |
|---|---|
| `0` | every request was accepted |
| `1` | at least one Core rejection occurred; later lines were still processed |
| `2` | local fixture/framing/transport error; processing stopped |

Requests and fixtures are UTF-8 JSON with duplicate keys, non-finite numbers
and lone surrogates refused. A malformed request stops the stream; a Core
rejection does not.

## Journey transcripts

`fixtures/*.jsonl` are real requests processed by the CLI against the matching
fixture:

| Journey | Demonstrates |
|---|---|
| `cash_refund.jsonl` | prepare, send, STATUS → FUNDS, cash debit, refund completion |
| `payout.jsonl` | prepare, send, FUNDS → STATUS, allocation payout completion |
| `original_cancel.jsonl` | PG cancellation accepted separately from customer credit confirmation |

The original-cancel journey shows that `PG_CANCELLED` completes the local
effect and changes `originalCancelled`/`pg_cancel_due`, while
`customerCreditConfirmed` remains `0`; a later
`CUSTOMER_CREDIT_CONFIRMED` observation raises that field to `100000` without
changing any account balance.

## Existing coverage and new tests

Existing deterministic Core coverage was mapped first:

| Behaviour | Existing sufficient coverage |
|---|---|
| STATUS/FUNDS order and duplicate facts | `test_core.py::test_effect_observation_orders_and_duplicate_facts` |
| FUNDS before STATUS | `test_core.py::test_funds_before_status_debits_cash_without_claiming_refund_done` |
| captured-but-unsettled cash is not confirmed funds | `test_core.py::test_capture_is_not_available_cash` |
| partial, separately bounded refund effects | `test_core.py::test_partial_refunds_are_separate_bounded_effects` |
| sent unknown effect cannot be released | `test_core.py::test_unknown_outcome_never_releases_reservation` |
| replay and conflicting operation body | `test_core.py::test_response_loss_and_conflicting_id_after_restart` |
| full refund / exact payout lifecycles | `test_core.py::test_full_chain_refund_before_payout`, `test_purchase_resale_admission_and_exact_payouts` |
| original cancellation versus customer credit | `test_v02.py::test_pg_cancel_before_settlement_needs_no_cash_and_separate_credit` |

The new tests cover the wrapper gaps these Core tests do not exercise:

- explicit fixture-only initialization through `Core.execute`, with no Harness
  defaults, and no session published after malformed or Core-rejected setup;
- complete receipt and selected-state parity between the session and a direct
  Core replay;
- real subprocess JSONL journeys for cash refund, payout and original-payment
  cancellation, including file/stdin equivalence;
- strict fixture/request validation, framing stop/continue rules, exit codes,
  UTF-8 failures and broken-output detection;
- detached non-mutating views, session closure on success and framing failure,
  and idempotent close;
- duplicate observations, conflicting operation/body evidence, insufficient
  confirmed funds, partial observations and refusal to abort a sent effect,
  all asserted through the local API rather than re-implemented Core semantics.

The local action allow-list and view selectors are wrapper behaviour, not
protocol contract. Core rejections are passed through unchanged.

## Local verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s reference/payment_effects -t reference/payment_effects

PYTHONPATH=reference/v0.3-rc1 python3 -m unittest test_core test_v02 test_v03
```

The suite is wired into the existing offline-suite loop in
`.github/workflows/protocol.yml`. That wiring only adds test discovery; it
changes no workflow semantics.

## Non-claims

This is a synthetic, in-memory local product-usability surface only. It does
not establish provider or bank authentication, transmission, payment
completion, settlement or F04 execution, pending Finance projections,
durability, restart recovery, exactly-once execution, chain finality,
production readiness or legal/accounting treatment. Product values remain
UNDETERMINED — Astra/User; provider facts remain UNDETERMINED —
provider/User; legal/accounting treatment remains UNDETERMINED —
User/designated advisers.
