# Local settlement and F04 finance workbench

Standard-library Python tooling for synthetic, in-memory journeys. It composes
one existing `SettlementMachine`, `FakeStatementSource`, `StatementAdapter` and
`CreditMachine(settlement_source=...)` in a reusable `LocalFinanceSession`.
It supplies no product policy: values in the fixtures are synthetic inputs.
Product policy remains **UNDETERMINED** under `SET-POLICY-DRAFT-0.3` and
`F04-MOCK-TERMS-DRAFT-0.2`, with Astra/User and the existing legal, tax and
accounting owners.

## Run without editing Python

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reference/credit_advance_f04/local_finance_cli.py --fixture reference/credit_advance_f04/fixtures/finance_journey.synthetic.json
PYTHONDONTWRITEBYTECODE=1 python3 reference/credit_advance_f04/local_finance_cli.py --fixture reference/credit_advance_f04/fixtures/finance_isolation.synthetic.json
```

Copy a fixture and change its IDs, keys, amounts, policy inputs, recordings or
explicit operations. Each invocation starts a fresh process-local session.
The journey captures a claim snapshot, offers/binds/approves credit, rejects a
draw before COMMITTED, commits a statement, repeats the rejected key unchanged,
and succeeds only when the fixture explicitly supplies a new key. It then
observes another statement, repays part, repays the remainder and closes. Replays
at the end expose the first receipt snapshots alongside the current views.
The isolation fixture uses two settlements with the same movement label but
separate cash and credit reservations. Its distribution is a separate explicit
caller action; statement observation never distributes.

Stdout is a single JSON object with `fixture_version`, `synthetic`, `ok`,
`results` and `source_calls`. Each zero-based result has `step_index`, `target`,
`operation`, an unchanged `receipt` or `view` (or an `error` with exception `type`,
`message` and `code` when present), `expectation_met`, and a detached cumulative
`source_calls` snapshot. These are local source requests, including explicit
statement replays, not provider observations. No flags or provenance inside FSM
results are removed or relabelled.

| Exit | Meaning |
|---|---|
| 0 | Every explicit step met its stated expectation |
| 1 | Unexpected domain/internal error, missing claim snapshot, or expected error did not occur; stopped at that step |
| 2 | Invalid fixture/JSON, file read failure, or CLI usage error; no dispatch |

Only an exactly named, explicitly expected existing domain error permits the
next step. Optional expected `code` must also match. An unexpected internal
failure always stops. Earlier successful effects remain; there is no rollback.

## Reusable API

Use the same sibling import convention as the existing reference machines.
For example, from the repository root:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("reference/credit_advance_f04").resolve()))
from local_finance_session import LocalFinanceSession

session = LocalFinanceSession(recordings={
    ("synthetic-settlement", "synthetic-movement"): json.dumps({
        "settlement_id": "synthetic-settlement", "movement_id": "synthetic-movement",
        "gross": 100000, "amount": 97000, "fee": 3000, "tax": 0,
        "held": 0, "adjustment": 0, "adjustment_reason": None,
    }),
})
receipt = session.settlement(
    "initiate", "synthetic-settlement", idempotency_key="caller-init",
    trade_id="synthetic-trade", gross=100000, debtor_role="synthetic-merchant",
    policy={"kind": "PRIMARY_FEE_BPS", "fee_bps": 500,
            "residual_payee": "synthetic-organizer", "fee_payee": "synthetic-platform"},
)
view = session.settlement_view("synthetic-settlement")
```

API methods:

- `settlement(operation, settlement_id, *, idempotency_key, **body)`
- `credit(operation, advance_id, *, idempotency_key, **body)`
- `settlement_view(settlement_id)`, `credit_view(advance_id)`, `credit_claim_view(claim_id)`

The session returns underlying objects directly and propagates underlying domain
exceptions unchanged. API body values go unchanged to the FSM, whose validation
and rejection-key rules apply. Unsupported operations fail before dispatch;
malformed statement call signatures fail before fetching. There is no session
idempotency table. The owned machines, source and adapter are available as
`settlement_machine`, `credit_machine`, `statement_source`, `statement_adapter`
for local inspection. The CLI always calls through the session facade.

## Internal fixture format, version 1

Root fields are exactly `fixture_version: 1`, `synthetic: true`, `statements`
(array), and `steps` (array). This format is not a protocol schema, SDK input,
read model or new protocol command.

A statement has `settlement_id`, `movement_id`, and exactly one of:

- `record`: exactly the existing `StatementRecord` fields: `settlement_id`,
  `movement_id`, `gross`, `amount`, `fee`, `tax`, `held`, `adjustment`,
  `adjustment_reason` (a string or null). Identity matching remains the adapter's
  check, so a structurally valid mismatched recording yields its existing error.
- `fault`: `synthetic_statement_error` or `synthetic_statement_timeout`.
  These are the existing `SyntheticStatementFault` values. Timeout is a marker;
  it performs no waiting. An unrecorded identity produces `StatementNotFound`.

A mutation has `target` (`settlement` or `credit`), `operation`, the corresponding
`settlement_id` or `advance_id`, `idempotency_key`, and `body` (an object, including
`{}` for operations with no body arguments). Operation/body allowlists:

| Target | Operation | Required body; optional fields in parentheses |
|---|---|---|
| settlement | initiate | trade_id, gross, debtor_role, policy; (currency) |
| settlement | authorize, capture, reconcile | empty |
| settlement | commit, observe_statement | movement_id only; all components come from the source |
| settlement | distribute | order (explicit array of payee strings) |
| settlement | bind_refund | refund_id, amount, beneficiary_role, reason |
| settlement | observe_mock_cancel_acceptance | source_id, amount |
| settlement | fail, cancel | reason |
| credit | offer | face, amount, beneficiary_role; (product) |
| credit | bind_settlement | settlement_id |
| credit | approve, close, reconcile | empty |
| credit | reject, cancel, default | reason |
| credit | draw | draw_id |
| credit | repay | repay_id, sequence, amount |

`policy` has exactly `kind`, `fee_bps`, `residual_payee`, `fee_payee`. There is no
default policy or distribution order. `product` retains the FSM's existing
undefined-product rejection; specifying it cannot activate a credit product.

A read uses `operation: "view"`, target and corresponding ID, without a body or
key. Credit `operation: "view_claim"` uses `claim_id`. Settlement `view` may
include `save_claim_as`, which saves a detached non-null `claim`. Names cannot
be overwritten. Credit `offer` may use top-level `face_ref` instead of
`body.face`, referring only to an earlier save. This snapshot is never refreshed
after later statements. A missing or null claim stops execution.
An explicit `body.face` is an existing FSM snapshot; its provenance, flags and
semantic shape remain the FSM's responsibility.

Any step may include `expect_error: {"type": "CreditError", "code": "..."}`
(`code` optional). Allowed types are `CreditError`, `SettlementError`,
`StatementSourceError`, `StatementNotFound`, `InvalidStatementRecord`, and
`StatementIdentityMismatch`. Internal exceptions cannot be configured as expected.

The entire fixture is checked before constructing a session: exact structural
fields, duplicate JSON fields/recordings, selectors, method arguments, reference
ordering, field types and integer encoding. Money, bps and repayment sequence
fields must use JSON integers: floats, booleans and numeric strings are rejected
without coercion. Python integers are preserved exactly, including out-of-range
values; range, conservation, phase, snapshot semantics and economic validation
remain in the FSM and produce their existing errors. A malformed late step
therefore prevents every dispatch, while a structurally valid rejected call
retains the FSM's existing first-result behavior.

## Coverage and limits

The [pre-test coverage inventory and execution evidence](../../validation/2026-10-31-plan-local-finance-workbench/README.md)
classify each requirement and point to both existing contract evidence maps.
`test_local_finance_session.py` adds actual-machine per-step parity, settlement
inertness around every credit step, separate cash/exposure, forwarding identity,
and no-retry/source-key probes. `test_local_finance_cli.py` adds subprocess
fixtures, validation-before-dispatch, exact integer round trips, saved-face/replay
checks, errors and stopping behavior. Both are discovered by the existing credit
suite; no CI change is needed.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p 'test_local_finance*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04
```

This is source-informed local parity, not independent verification. Existing
rejection retention, internal-fault behavior and UNKNOWN boundaries are not
redefined. There are no automatic transitions, retries, replacement keys,
cross-machine atomicity, persistence, new economic calculations, provider calls,
real funds, credentials, endpoints, chain execution or runtime activation.
It establishes no durability, legal/accounting treatment, lending decision,
bank exactly-once, chain finality, production readiness or P04 closure.
Authoritative contracts, catalogue, SDK, gate, task inputs and protected trees
remain unchanged. Non-author exact-head review and completed/success KTX/KIX
hosted gates remain required after supervisor commit/publication.
