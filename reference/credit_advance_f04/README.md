# Local F04 credit desk

`CreditSession` exposes the existing in-memory `CreditMachine` in one fresh,
synthetic session. The JSONL CLI accepts explicit local requests and embeds the
FSM's receipts, views and domain error codes unchanged. Provenance is always
`MOCK_CREDIT_F04_ONLY`; the exposure ledger is `MOCK_EXPOSURE`.

This is the mock boundary in [CREDIT_ADVANCE_F04.md](../../docs/contracts/CREDIT_ADVANCE_F04.md).
Local method selectors are not additions to the protocol catalogue or OpenAPI.

## Importable session

Use the existing module-directory convention (put `reference/credit_advance_f04`
on your Python import path):

```python
from credit_session import CreditSession

# Caller-owned synthetic inputs; these numbers establish no product policy.
session = CreditSession()
print(session.view("adv-1"))
```

`CreditSession(settlement_source=None, ownership_source=None)` forwards the nine
mutating methods and three reads below with the existing FSM signatures and
errors. An optional `settlement_source` (for example a real local
`SettlementMachine` from `reference/settlement_f01_f03`) is read by the machine's
existing bound-draw `COMMITTED` gate; `ownership_source` is only compared through
`canonical_state`, exactly as the machine already does. The session supplies no
policy values, faces, approvals or automation. It has no journal export/import,
restoration, persistence or external-execution interface. Returned snapshots
retain the FSM's existing copy behavior.

## Schemas

The fixture has exactly these fields; `settlement_setup` is `null` (no source)
or an array replayed in order onto one fresh real `SettlementMachine`:

```json
{"fixture_version":1,"provenance":"MOCK_CREDIT_F04_ONLY","settlement_setup":null}
```

Each setup entry has exactly `operation`, `settlement_id`, `idempotency_key` and
`body`, whitelisted to `initiate` (`trade_id`, `gross`, `debtor_role`, `policy`,
optional `currency`), `authorize`/`capture` (`{}`), `commit` (`movement_id`,
`gross`, `amount`, `fee`, `tax`, `held`, `adjustment`, optional
`adjustment_reason`), `fail` (`reason`) and `cancel` (`reason`). Setup FSM
rejections propagate with their unchanged codes; no synthetic settlement source,
claim-snapshot adapter or repayment-note source is constructed.

Each JSONL line has exactly `operation` and `arguments`. Every mutating operation
requires `advance_id` and `idempotency_key`; the reads do not take idempotency
keys.

| Operation | Other required arguments | Optional arguments (existing default `None`) |
|---|---|---|
| `offer` | `face`, `amount`, `beneficiary_role` | `product` |
| `approve`, `close`, `reconcile` | none | none |
| `reject`, `cancel`, `default` | `reason` | none |
| `bind_settlement` | `settlement_id` | none |
| `draw` | `draw_id` | none |
| `repay` | `repay_id`, `sequence`, `amount` | none |
| `view` | `advance_id` only | none |
| `view_claim` | `claim_id` only | none |

`face` must be a JSON object; the FSM's existing `_parse_face` retains all face
predicates (mock provenance, KRW, obligation arithmetic, frozen flags, refund
bearer states). The desk never derives a face from the settlement source: callers
embed a snapshot themselves, for example `book.view(id)["claim"]` from the same
local book. `product` is forwarded unchanged; any non-null value is the FSM's
existing `CREDIT_PRODUCT_UNDEFINED` refusal. No amounts, identities, reasons,
sequences or terms are inferred or defaulted. `open_terms` stays `UNDETERMINED`
under adopted option A.

## Commands and journeys

Run from the repository root, using only the Python standard library:

```bash
python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/committed.json --requests reference/credit_advance_f04/fixtures/lifecycle.jsonl
python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/committed.json --requests reference/credit_advance_f04/fixtures/settlement_gates.jsonl
python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/captured.json --requests reference/credit_advance_f04/fixtures/gate.jsonl
python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/unbound.json --requests reference/credit_advance_f04/fixtures/decline.jsonl
python3 reference/credit_advance_f04/credit_cli.py --fixture reference/credit_advance_f04/fixtures/unbound.json --requests reference/credit_advance_f04/fixtures/boundaries.jsonl
```

`lifecycle` runs offer → approve → bind → draw → repay → repay → close on the
committed book, then replays historical requests. Replayed receipts retain their
historical snapshots with the FSM's `duplicate=true`, `applied=null`; reconcile
returns `matched=true`, `entry_count` and the deterministic `state_digest`.

`settlement_gates` exercises the committed book's binding predicates: mismatched
face gross (`SETTLEMENT_AMOUNT_MISMATCH`), a settlement id unknown to the source
(`UNKNOWN_SETTLEMENT`), a committed claim that is not the face's claim
(`SETTLEMENT_BINDING_CONFLICT`) and rebinding conflicts. `gate` shows a bound
draw on a merely captured claim rejected `SETTLEMENT_NOT_COMMITTED` while an
unbound draw succeeds with `settlement_gate:"UNBOUND"`. `decline` covers reject,
cancel and default terminal paths. `boundaries` is a code matrix over one
session, including `IDEMPOTENCY_CONFLICT`, `REPAYMENT_ORDER`,
`FACE_SNAPSHOT_FROZEN` and `SETTLEMENT_SOURCE_REQUIRED`. No request is retried,
repaired or reconciled automatically.

## Output and errors

Each output is deterministic sorted JSON containing `operation`, synthetic
`provenance`, and exactly one of `receipt`, `view`, `claim`, `error`. Domain
errors are `{"code":"<unchanged CreditError code>"}`; settlement setup
rejections keep their `SettlementError` code. Format/setup/I/O errors use a
distinct `type` and `message`. Command-line usage errors follow argparse on
stderr.

Exit codes: **0** all accepted; **1** at least one domain rejection; **2** malformed
input, setup or I/O failure. Domain rejection continues only to the next supplied
line. Malformed input stops immediately; earlier accepted requests remain applied.
Empty streams succeed; blank lines are malformed JSON.

Duplicate keys at every depth, non-finite constants and exponent overflow,
invalid JSON/Unicode, wrong object/array structures, missing/extra fields and
unsupported selectors are rejected before dispatch. The FSM retains all value,
lifecycle, idempotency and face predicates.

## Live local subprocess client

`CreditClient` uses only the Python standard library. Importing it launches
nothing. `CreditClient.launch(fixture, cleanup_timeout=...)` explicitly launches
one fresh `credit_cli.py` child using the current interpreter, an absolute local
fixture path, binary stdin/stdout pipes and inherited stderr. The CLI flushes
each JSONL reply, so sequential requests can depend on replies while stdin
remains open. The child alone loads the fixture and owns the business session.

```python
from credit_client import CreditClient

with CreditClient.launch("reference/credit_advance_f04/fixtures/committed.json",
                         cleanup_timeout=1) as client:
    # An explicit read, returning the existing UNKNOWN_ADVANCE domain error.
    reply = client.request({"operation": "view",
                            "arguments": {"advance_id": "caller-selected-id"}})
    print(reply)
```

`request(dict) -> dict` preserves the envelopes above, integer amounts and nested
business payloads. It validates finite JSON data before writing; the existing
CLI/FSM still decides operation, argument and value acceptance. Replies require
newline-terminated strict UTF-8 JSON, exact envelope fields, synthetic provenance,
matching operation and the corresponding object payload. Duplicate keys,
non-finite numbers, mismatches and incomplete output are transport failures.

Only one request or cleanup may run at a time. Concurrent/reentrant calls raise
`CreditClientStateError` before writing. Matching `error.code` domain rejections
permit another explicitly supplied request. Typed fatal errors and startup
errors (`operation:null`) make the client terminal. A startup broken-pipe race
is transport uncertainty, never an inferred domain rejection.

After submission begins, a short write, broken pipe, malformed reply, EOF or
interruption raises `CreditTransportUncertainty` and permanently fences that
instance. `client.uncertainty` retains the submitted `request` snapshot,
`request_bytes` and observed `reply_bytes`. No retry, restart, replay,
compensation or automatic reconciliation occurs. Uncertainty proves neither
rejection nor rollback; earlier work may already have applied.

Reads block without a product response deadline. The caller must supply a finite
positive `cleanup_timeout` (booleans are rejected); it applies only to process
cleanup. `close() -> int` closes stdin, waits, then terminates/kills and reaps
only the owned child if needed. Repeated close returns the same exit code and
preserves uncertainty. A `with` block always calls close, including on caller
exceptions. `client.close()` is process cleanup; a request with
`operation:"close"` is the existing credit-domain transition.

Run the caller-configured example from the repository root:

```bash
python3 reference/credit_advance_f04/example_credit_client.py --fixture reference/credit_advance_f04/fixtures/committed.json --requests reference/credit_advance_f04/fixtures/lifecycle.jsonl --cleanup-timeout 1
```

The example submits the supplied transcript and prints replies plus additional
reads using returned `receipt.credit.advance_id` and `claim_id`. A claim read
starts once `snapshot_frozen` reports a noted claim; before the first draw the
existing machine has no claim to read. The example stops at the first error and
always cleans up. It invents no approval, amount, identifier or policy value.
This is a runnable local example, with no credit console, new adapter,
persistence, sockets, protocol command, SDK/catalogue change or real lending.
Product policy remains **UNDETERMINED — Astra/User**; legal terms remain
**UNDETERMINED — User/legal**.

## Synthetic limitations and Class B

Draw and repay are in-memory mock exposure-ledger transitions. All flags remain
false: `funds_executed`, `bank_debit_observed`, `repayment_observed`,
`economic_finality_claimed`, `interest_defined`, `underwriting_executed`,
`kyc_executed`, `legal_debtor_bound`, `collateral_perfected`, `priority_bound`
and the remaining mock flags. `external_credit` stays `UNSUPPORTED`, ownership
is never mutated and ticket ownership is never authoritative. `default` is a
recorded reason, not a workout; there is no interest, APR, rank, perfection or
recalculation. There are no external calls, funds, credentials, persistence,
production runtime, bank/PG/KYC connections or Wave7 work. Process exit loses
the session.

Existing behavior is preserved, including these contract-undefined
characterizations:

- Stored rejections are not journaled; a later `reconcile` still matches
  journal and views. `MOCK_INVARIANT`, `IDEMPOTENCY_CONFLICT` and
  `INVALID_JOURNAL` rejections are never stored and cannot be replayed as
  first results. See the existing [rejection-atomicity coverage](test_credit_rejection_atomicity.py)
  and the [F04 contract evidence map](../../docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md).
- `reconcile` restores into a second machine that shares the same injected
  sources; it is a determinism witness, not durable recovery.
- `draw` reads the bound settlement view at call time only; no settlement
  commands are issued and later settlement movement does not rewrite the
  stored `mock_settlement_commit_observed` observation.
- The desk does not expose `export_journal`, `restore`, `canonical_state`,
  `state_digest`, `reject_unsupported` or `attempt_execution`; those remain
  machine-level surfaces covered by their existing tests.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04
```

The [local evidence record](../../validation/2026-11-05-plan-local-credit-desk/README.md)
maps reused lifecycle coverage and new session/fixture/CLI tests, records
actual checks and transcripts, and states remaining gates. Builder checks do not
replace A2 non-author exact-final-head review or completed/success KTX and KIX
exact-final-head CI. No merge authorization is implied.

The [client evidence record](../../validation/2026-11-06-plan-local-credit-stdio-client/README.md)
adds live-child parity, transport failure/fencing, import and cleanup coverage.
