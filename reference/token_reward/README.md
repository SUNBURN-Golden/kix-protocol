# Local F4 reward desk

## Local supply console

Run the separate, stdlib-only terminal console from the repository root:

```bash
python3 reference/token_reward/supply_console.py
# Replay a file-free composition journey (no JSON request file required):
python3 reference/token_reward/supply_console.py < reference/token_reward/fixtures/supply_console_match.txt
```

`supply_cli.py` retains its existing file/stdin interface. The console calls the
same `supply_reconciliation.dispatch_request` for each explicitly confirmed
calculation. It keeps selections only in memory; starting a new process starts
with no events, report or comparison selected. The importable entry points are
`run_console(*, input_stream, output_stream, error_stream) -> int` and
`main(argv=None) -> int`. No arguments are required or accepted.

| Menu action | Explicit input / effect |
|---|---|
| `add_event` | Append one complete hypothetical event in entry order |
| `replace_event` | Enter a displayed 1-based position, then all six replacement fields |
| `replace_events` | Enter a nonnegative event count, then every event; `0` deliberately selects `[]` |
| `show` | Display complete selected events, active report and comparison; null means unselected |
| `calculate` | Preview the complete `supply_report` request, then type literal `CALCULATE` to dispatch once |
| `reconcile` | Enter a fresh synthetic `chain_supply`, preview `reconcile_supply` with the exact returned report, then type literal `RECONCILE` to dispatch once |
| `quit` | End the local session |

Every event prompts, in order, for `event_id`, `op`, `amount`, `approved`,
`path_approved`, `program`. IDs are verbatim text, never trimmed or repaired.
Operations are literal `MINT`, `ALLOCATE`, `BURN`, `HOLDER_BURN`. Amounts use
explicit decimal integers and the existing model's positive bound. Both approval
fields require literal `true` or `false`. Programs require an explicit JSON
string (including quotes) or `null`; nothing is defaulted. The existing model
restrictions described below apply. Individual input validation performs no
calculation; aggregate conservation, duplicate IDs and total bounds are checked
only by the confirmed dispatcher call. Entry order is preserved.

Prompts, complete previews, `show` and notices go to stderr. Stdout contains one
complete canonical JSON envelope per result/error, preserving all result fields
and original domain codes. `MOCK_TOKEN_REWARD_ONLY`, `CALCULATION_ONLY` and
`SYNTHETIC_SUPPLY_FIGURE` identify scope. For example, enter these lines at the
prompts (the quantities and program below are synthetic example inputs):

```text
add_event
mint-example
MINT
10
true
true
"synthetic-program"
calculate
CALCULATE
reconcile
10
RECONCILE
show
quit
```

The report contains `minted_total=10` and `layer_supply=10`. The separate
comparison returns `alarm="MATCH"`, `mismatch=false`, `stop_payout=false`, with
both supplied figures displayed. Full executable transcripts for MATCH, holder
burn, unexplained difference, unapproved mint/path, both causes, duplicate
events, conservation failure and declines are in `fixtures/supply_console_*.txt`.
Their [actual output captures and evidence](../../validation/2026-11-09-plan-plan-local-supply-console/README.md)
retain complete envelopes and previews. Both causes retain the class-B
`UNAPPROVED_PATH` characterization from TL-4 §6.B; this sets no policy precedence.

Starting any event edit immediately clears the active report and comparison.
An incomplete edit leaves the previous events selected but cannot restore old
results. `calculate` clears both results before preparation, so a decline or
failure cannot reuse an old report. A successful report is retained whole and
forwarded without repair, filtering, arithmetic or inferred chain supply.
`reconcile` clears the comparison first; a decline, invalid input or failure
retains the report and requires a fresh chain figure on the next attempt.

Use `:cancel` at any prompt to abandon the current action (reserved as a control
line). Any confirmation other than its exact literal declines. Invalid input,
cancellation, EOF or interruption before confirmation dispatches nothing for
that action. No failure automatically retries. Invalid fields emit an error and
return to the menu, retaining the invalidation rules above. EOF, interruption,
encoding/I/O or unexpected dispatcher failure stops the session. Exit status is
`0` on clean quit, sticky `1` after a confirmed domain rejection, or sticky `2`
after invalid input/terminal failure; `2` takes precedence. Pre-confirmation
model validation retains its original code but exits `2`. Alarming results are
successful calculations. `stop_payout` is only a displayed flag.

Supply policy and operational responses remain **UNDETERMINED — Astra/User**.
Hypothetical events perform no minting, burning, allocation, payout control,
chain query, persistence, runtime activation or protocol command. Local checks
are builder evidence; A2 non-author exact-head review and completed/success KTX
and KIX workflows remain delivery gates.

## Local supply reconciliation

`supply_reconciliation.dispatch_request(request)` exposes the unchanged
`token_reward_model.supply_report` and `reconcile_supply` calculations. Put
`reference/token_reward` on the Python import path, as for the other local tools:

```python
from supply_reconciliation import dispatch_request

report = dispatch_request({"operation": "supply_report", "arguments": {"events": []}})["result"]
reply = dispatch_request({"operation": "reconcile_supply", "arguments": {
    "offchain": report, "chain_supply": 0}})
```

These are local selectors, with no new protocol command. Exactly `operation` and
`arguments` are required. `supply_report` takes exactly `events`, an explicit
array (including `[]`). `reconcile_supply` takes exactly `offchain`, the supplied
report itself, and `chain_supply`, a caller-entered synthetic nonnegative integer.
No argument has a default. The tool does not rebuild or repair a supplied report,
fill missing totals, deduplicate events, reorder events or coerce numbers.

Every hypothetical event has exactly `event_id`, `op`, `amount`, `approved`,
`path_approved`, and `program`. The existing model accepts `MINT`, `ALLOCATE`,
`BURN`, and `HOLDER_BURN`. Amounts are positive integers at most `10**12`;
approval fields are booleans. IDs and non-null programs are trimmed, nonempty
strings of at most 100 characters. `MINT` and `ALLOCATE` require a program;
`BURN` allows null; `HOLDER_BURN` requires `approved=false` and `program=null`.
Approval fields are hypothetical assertions, with no authenticated authorization.
The model checks conservation and aggregate bounds. These bounds and fixture
quantities describe implementation/examples, not product policy values.

A complete report has `events`, `minted_total`, `unapproved_mint`,
`allocated_total`, `burned_total`, `holder_burn_outside_layer`, `layer_supply`,
and `figure`. Allocation does not change layer supply. Holder burn is recorded
outside that layer. Reconciliation compares six numeric totals with recomputed
events; it does not authenticate reports or validate every metadata field.
Do not treat numeric equality as report authenticity or independent chain evidence.

Run one UTF-8 JSON request from a file or stdin:

```bash
python3 reference/token_reward/supply_cli.py --request reference/token_reward/fixtures/supply_report.json
python3 reference/token_reward/supply_cli.py --request - < reference/token_reward/fixtures/supply_match.json
```

The `supply_*.json` fixtures also demonstrate holder burn, unexplained difference,
unapproved mint, unapproved path, both causes, duplicate events and tampered
totals. Reconciliation fixtures contain complete supplied reports. One JSON
document is required; duplicate keys at any depth, non-finite numbers, invalid
UTF-8/Unicode, trailing documents and missing/extra envelope/argument fields
are rejected. Nested domain validation remains in the existing functions.

Stdout contains one canonical JSON envelope: `operation`,
`provenance="MOCK_TOKEN_REWARD_ONLY"`, `evidence_class="CALCULATION_ONLY"`,
`notice`, and either the complete unchanged `result` or `error`.
Reconciliation retains exactly `alarm`, `mismatch`, `stop_payout`,
`offchain_supply`, `chain_supply`, and `figure`; results preserve
`SYNTHETIC_SUPPLY_FIGURE`. A supported operation identified before rejection
is retained; otherwise `operation` is null. The dispatcher raises original
domain exceptions or `FixtureError` for malformed local inputs.

| Exit | Meaning |
|---|---|
| 0 | Calculation completed, including alarming reconciliation results |
| 1 | Domain rejection: `error={"code":"<original code>"}` |
| 2 | Input/I/O/encoding failure: `error` has `type` and `message` |

Argparse usage errors use stderr and emit no JSON. Duplicate events retain
`SUPPLY_EVENT_DUPLICATE`; altered numeric totals retain `SUPPLY_REPORT_MISMATCH`.
Both causes currently select `UNAPPROVED_PATH` before `UNAPPROVED_MINT`.
This is the existing class-B characterization in
[TL-4 §6.B](../../docs/decisions/TL4_THREAT_MODEL_20261009.md#b-계약이-정의하지-않음-성격만-기록),
with no new contractual precedence.

Events describe hypothetical inputs. The tool never mints, allocates, burns,
queries a chain or controls payouts. `stop_payout=true` is a **reported model
flag**, and executes no stop. Supply policy and operational responses remain
**UNDETERMINED — Astra/User**. No sockets, chain client, dependencies, persistence,
runtime activation or V1–V5 implementation are introduced. The
[builder evidence and transcripts](../../validation/2026-11-09-plan-local-supply-reconciliation-tool/README.md)
map reused model coverage and interface checks; A2 non-author exact-head review
and both required workflows remain delivery gates.

## Local collateral assessment

The stdlib-only `collateral_assessment.dispatch_request(request)` exposes the
existing `token_reward_model.collateral_recognized` calculation for synthetic
U2/TK-12 assessment. Use the existing module-directory import convention
(`reference/token_reward` on your Python import path). It returns the complete
existing model result unchanged inside `result`:

```python
from collateral_assessment import dispatch_request

output = dispatch_request({
    "operation": "collateral_recognized",
    "arguments": {
        "liability_krw": 100,
        "collateral_items": [
            {"kind": "KRW_GUARANTEE", "amount": 30},
            {"kind": "ESCROW", "amount": 25},
            {"kind": "TOKEN", "amount": 999},
        ],
    },
})
# output["result"] == {"liability_krw": 100, "recognized_krw": 55,
#                      "token_recognized": 0, "currency": "KRW"}
```

Exactly `operation` and `arguments` are required. Arguments must contain exactly
`liability_krw` and `collateral_items`; neither has a default. An explicit `[]`
recognizes zero. Item kinds and fields are validated by the unchanged model;
each item has `kind` and `amount`. The local selector adds no protocol command.
The existing implementation requires positive integer liability and item amounts
at most `MONEY_MAX = 10**12`, and bounds the recognized sum by the same constant.
These are implementation limits, not approved product limits. Integers are never
converted to floats, rounded or accepted from strings. Fractional/exponent JSON
numbers and booleans are rejected as amounts. Synthetic examples set no policy.

Run from the repository root:

```bash
python3 reference/token_reward/collateral_cli.py --request reference/token_reward/fixtures/collateral_mixed.json
python3 reference/token_reward/collateral_cli.py --request - < reference/token_reward/fixtures/collateral_empty.json
python3 reference/token_reward/collateral_cli.py --guided
python3 reference/token_reward/collateral_cli.py --guided < reference/token_reward/fixtures/collateral_guided_mixed.txt
```

Select exactly one mode. File/stdin mode consumes one UTF-8 JSON document,
rejecting duplicate keys at every depth, non-finite numbers, invalid Unicode,
trailing documents, and missing/extra envelope or argument fields. Guided mode
requires liability, an explicit nonnegative item count, and every item's kind
and integer amount, in decimal JSON notation. Zero count explicitly means empty.
It prints the complete proposal to stderr, then requires literal `CALCULATE`.
No calculation occurs during composition/preview. Any other confirmation
discards it with `cancelled: true`; EOF, interruption and malformed/incomplete
input discard it with an input error. There is no retry or retained selection.

Stdout is one deterministic JSON response. Every response carries `operation`,
`provenance: "MOCK_TOKEN_REWARD_ONLY"`, `evidence_class: "CALCULATION_ONLY"`
and a fixed synthetic scope notice. Success adds `result`; domain rejection
adds `error: {"code": "..."}`; input/I/O failures add `error` with `type` and
`message`. The importable dispatcher raises `FixtureError` or the original
`TokenRewardError` instead of wrapping exceptions.

| Exit | Meaning |
|---|---|
| 0 | Calculated, or explicitly declined (no `result` on decline) |
| 1 | Existing model rejected the input |
| 2 | Malformed/incomplete input, interruption, I/O failure or argument usage error |

Argument usage errors use argparse's stderr help and have no JSON response.
Domain codes stay unchanged: `INVALID_AMOUNT`, `COLLATERAL_TYPE`,
`COLLATERAL_KIND_UNSUPPORTED`, `COLLATERAL_FIELDS`,
`TOKEN_ONLY_COLLATERAL_REJECTED`, `PRICE_SOURCE_UNDEFINED`. A `valuation` key
on any item reaches the model and is refused; the tool never strips it.
The model's check ordering determines which code wins for multiple errors.

This calculates no adequacy/eligibility threshold and grants no loan or legal
approval. Asset selection and collateral ratios remain **UNDETERMINED —
Astra/User**; legal enforceability remains **UNDETERMINED — User/legal**.
There is no custody, F04 connection, external service, token package or runtime
activation. Existing `CollateralTests` and TL-4 remain author-side evidence;
see [interface coverage, actual CLI transcripts and local verification](../../validation/2026-11-08-plan-local-collateral-assessment-tool/README.md).

## Reward desk scope

`RewardSession` exposes the existing TL-3 off-chain `RewardMachine` in one
fresh, in-memory session. The JSONL CLI accepts explicit local requests and
embeds the FSM's receipts, views and domain error codes unchanged. Provenance
is always `MOCK_TOKEN_REWARD_ONLY`; units are synthetic `POINT_F4`.

This is the U3/F4 scope in [TOKEN_ROLE_AND_SUPPLY.md](../../docs/contracts/TOKEN_ROLE_AND_SUPPLY.md)
and [TOKEN_AUTHORITY_AND_LIFECYCLE.md](../../docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md).
Local method selectors are not additions to the protocol catalogue or OpenAPI.

## Importable session

Use the existing module-directory convention (put `reference/token_reward`
on your Python import path):

```python
from reward_session import RewardSession

# Caller-owned synthetic inputs; these numbers establish no product policy.
session = RewardSession({
    "CUSTOMER_DEPOSIT": 0,
    "ORGANIZER_SETTLEMENT": 0,
    "REFUND_RESERVE": 0,
    "PROTOCOL_REVENUE": 500,
    "TOKEN_TREASURY_REWARD": 500,
})
print(session.pool_view())
```

All five opening balances are required. The session forwards the nine lifecycle
methods below and the three reads, with the existing FSM signatures and errors.
It has no journal export/import, restoration, persistence or external-execution
interface. Returned snapshots retain the FSM's existing copy behavior.

## Schemas

The fixture has exactly these fields:

```json
{"fixture_version":1,"provenance":"MOCK_TOKEN_REWARD_ONLY","opening_balances":{"CUSTOMER_DEPOSIT":0,"ORGANIZER_SETTLEMENT":0,"REFUND_RESERVE":0,"PROTOCOL_REVENUE":500,"TOKEN_TREASURY_REWARD":500}}
```

Each JSONL line has exactly `operation` and `arguments`. Every mutating operation
requires `idempotency_key`. Every operation except `observe` and the two empty
reads uses `reward_id_value`; reads do not take idempotency keys.

| Operation | Other required arguments | Optional arguments (existing default `None`) |
|---|---|---|
| `observe` | `reward_key`, `source_view`, `rule_version`, `amount`, `source_kind` | none |
| `hold` | none | none |
| `mark_eligible` | `window_closed`, `source_view`, `abuse_clear` | `abuse_kind`, `recipient_cap`, `program_cap` |
| `submit` | `approval_ref`, `signed_bytes_digest`, `spend_pool` | `budget_ceiling`, `execution_permit` |
| `observe_transfer_effects` | `effects_digest`, `outcome` | none |
| `reconcile_unknown` | `same_digest`, `resolution` | none |
| `observe_source_cancel` | `source_view`, `reason` | none |
| `observe_krw_refund` | `source_view`, `reason` | none |
| `supersede` | `approval_ref`, `rule_version` | none |
| `view` | none | none |
| `reward_ids`, `pool_view` | no arguments: `{}` | none |

`reward_key` has exactly `program`, `source_op_id`, `recipient`, `kind`.
Use the existing `token_reward_model.reward_id(**reward_key)` helper for the
stable ID, or read it from the observe receipt. Identities are caller supplied;
the CLI does not substitute aliases or generate identities.

`source_view` must be an object. The FSM requires `phase="COMMITTED"`,
`currency="KRW"`, and `funds_executed`, `bank_debit_observed`,
`legal_debtor_bound`, `external_return_closed`, `durable` all explicitly false.
The same snapshot convention applies to cancellation and refund observations.
Additional finite JSON metadata is preserved opaquely; it is not authenticated.
`source_kind` is an existing `SETTLEMENT`, `RESALE` or `RESERVATION` selector;
no source machine is connected.

`approval_ref` has exactly `record_id`, `generation`, `authority_id`,
`actor_type`, `action`, `scope_ref`, `evidence_refs`, with optional `prior_record`.
`evidence_refs` is an array. The CLI never inserts `prior_record`, generates
approval records or treats their structural validity as a person's authorization.
AI approval is rejected by the FSM. `execution_permit` is null or exactly
`fence_ref` and `signed_bytes_digest`; a fence slot is not distributed fencing.

Omitted optionals keep the FSM's existing `None` behavior; explicit null is
passed through. No amounts, caps, budgets, time windows or approvals are inferred.
Supplying `window_closed=true` is a caller assertion, never a clock calculation.

## Commands and journeys

Run from the repository root, using only the Python standard library:

```bash
python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/participation.jsonl
python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/cancellation.jsonl
python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/boundaries.jsonl
python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/unknown_pending.jsonl
cat reference/token_reward/fixtures/unknown_pending.jsonl reference/token_reward/fixtures/unknown_resolution.jsonl | python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests -
```

Participation runs observe → hold → eligibility → submit → effect observation,
then explicitly replays historical requests. Replayed receipts retain their
historical reward snapshots, with the FSM's `duplicate=true`, `applied=null`;
the later view remains ISSUED and only one pool spend exists.

Cancellation reverses one reward before issuance and creates a CLAWBACK_CLAIM
after issuance for another. A KRW refund observation has a separate effect ID
and does not change the token phase; cancelling does not replenish the pool.

UNKNOWN pending ends unresolved, even after rejected reconciliation, rejected
resends and a separately requested valid same-bytes resend. The resolution file
is separate explicit input: concatenate it into the **same process** to resolve.
Running it alone starts a fresh session and reports `UNKNOWN_REWARD`.
No request is retried or reconciled automatically. Boundary requests demonstrate
open-window, forbidden obligation-pool and AI-approval rejections.

## Live subprocess client

`reward_client.RewardClient` uses only the Python standard library and owns one
explicitly launched `reward_cli.py --fixture <absolute-path> --requests -` child.
Importing starts nothing. Supply the fixture and a finite positive
`cleanup_timeout`; there are no opening-balance or policy defaults:

```python
from reward_client import RewardClient

with RewardClient.launch("reference/token_reward/fixtures/reward_session.json",
                         cleanup_timeout=1) as client:
    reply = client.request({"operation": "reward_ids", "arguments": {}})
    print(reply["reward_ids"])
```

Use the module-directory import path described above. `request(dict) -> dict`
sends exactly one JSONL request and blocks for one complete validated reply while
stdin stays open. All twelve operations in the schema table are supported.
The client supplies no balances, source facts, identities, approvals, budgets,
reconciliation or subsequent operations. Optional omission and explicit null
remain distinct on the wire. Structural validation and serialization happen
before submission; local validation errors leave the client usable. Business
predicates remain in the unchanged FSM.

The client checks strict UTF-8/JSON, newline completion, exact envelope fields,
matching operation, `MOCK_TOKEN_REWARD_ONLY` provenance and operation-specific
payload shapes. Mutations require a receipt with `reward.reward_id` as a string;
`view` requires an object with a string `reward_id`; `reward_ids` requires an
array of strings (including an empty array); `pool_view` requires all five integer
balances and the existing credit/spend entry shapes. It returns the business
payload unchanged, without recalculating lifecycle or accounting decisions.
Provenance validation is a synthetic label check, not authentication.

Errors and lifetime:

- Matching `error={"code": str}` domain refusals are returned unchanged and allow
  the next explicitly supplied request. The CLI's eventual exit code remains 1.
- A valid null-operation setup error, or a typed `{"type": str, "message": str}`
  fatal error, is returned unchanged and terminates the client. Later requests
  raise `RewardClientStateError` before writing.
- Once submission starts, short writes, broken pipes, read/write failures,
  interruptions, EOF and invalid or mismatched replies raise
  `RewardTransportUncertainty` and permanently fence the instance. Its detached
  `request`, `request_bytes` and observed `reply_bytes` are diagnostic evidence.
  A startup failure may race the first write and appear as broken-pipe uncertainty.
  An applied mutation may have lost its reply; cleanup establishes no rollback.
- Busy, closed, terminal and uncertain clients reject requests with
  `RewardClientStateError`. One nonblocking lock also rejects overlapping cleanup.
  The owner must interrupt a blocked requester before closing; there is no product
  response timeout. No retry, replacement child, compensation or automatic
  reconciliation follows any error.
- `close() -> int` closes stdin and reaps only the owned child, then closes stdout.
  It waits up to `cleanup_timeout`, terminates on expiry, waits up to that timeout
  again, then kills and reaps if necessary. It is idempotent and retains any
  uncertainty. A context manager calls it even when the caller raises an exception.
  Stderr is inherited, separate from JSONL stdout. Exit loses all in-memory state.

Run the response-dependent example from the repository root:

```bash
python3 reference/token_reward/example_reward_client.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/participation.jsonl --cleanup-timeout 1
```

The example sends each caller-selected transcript request once. After each
successful receipt it explicitly derives the **next** request from that reply:

```python
{"operation": "view",
 "arguments": {"reward_id_value": reply["receipt"]["reward"]["reward_id"]}}
```

It then continues the supplied transcript, including its explicit `reward_ids`
and `pool_view` reads, and stops at the first error. These added reads belong to
the example; the client inserts none. Receipts, including duplicate receipts,
are historical action snapshots; reads observe current session state. UNKNOWN
requires a separately supplied reconciliation request in the same live child.
Cancellation and a KRW refund remain separate observations and effects.

The [client evidence record](../../validation/2026-11-06-plan-local-reward-stdio-client/README.md)
maps reused lifecycle vectors, live-child and fault coverage, actual checks and
pending review/CI gates. Reward policy remains **UNDETERMINED — Astra/User**;
legal effects remain **UNDETERMINED — User/legal**. All synthetic and Class B
limitations below apply. No settlement-source connection, parked settlement-reward
adapter, coin/TIX module, persistence, protocol command or execution activation
is introduced.

## Guided local reward console

Run one fresh in-process session with the same explicit opening-balance fixture:

```bash
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json
```

To use one live local synthetic desk child for the entire interaction, explicitly
select subprocess mode and a finite positive cleanup timeout in seconds:

```bash
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1
```

`--mode in-process` is the default and preserves the importable
`run_console(session, *, input_stream, output_stream, error_stream)` interface.
Both modes require `--fixture`. Subprocess mode requires `--cleanup-timeout`;
supplying it in in-process mode is a usage error. The timeout is caller selected,
with no default, and applies only to reclaiming the owned child. Response reads
remain blocking with no product response deadline.

Subprocess mode uses the existing `RewardClient` and unchanged `reward_cli.py`.
It launches once, keeps stdin open between selections, and performs each confirmed
mutation or explicit read in that same service session. It constructs no local
fallback session. Importing the console launches nothing. Quit, EOF, interruption,
rendering failure and dispatch failure all close/reap the owned child. Cleanup
closes stdin, waits up to the supplied timeout, then terminates and, if needed,
kills and reaps the child as described in the client section. This is resource
reclamation and establishes no rollback; exiting loses the synthetic session.

Choose one of the twelve operations in the schema table above, or local `quit`.
There is no startup read. Each selection collects every field again, even for a
deliberate replay. Prompt order is:

1. `reward_id_value` for every operation except `observe`, `reward_ids`, `pool_view`.
2. The other required arguments in the table's order. For `observe` these are
   `reward_key`, `source_view`, `rule_version`, `amount`, `source_kind`.
3. For `mark_eligible` or `submit`, one JSON object of optional arguments. Only
   the table's optional names are allowed. `{}` omits all; `null` on a named field
   remains explicitly supplied. For example, `{"recipient_cap":null}` supplies
   that key while omitting `abuse_kind` and `program_cap`. This prompt adds no
   wrapper field to the request.
4. For mutations, fresh `idempotency_key`, then confirmation. Reads have neither.

Enter `reward_key`, `source_view`, `approval_ref` as strict JSON objects using
the existing nested schemas above. At `reward_key`, `source_view` or `approval_ref`, literal
`:guided` optionally collects the same object field by field. Raw JSON remains
available independently at every selection, including `submit` and `supersede`.

Guided `reward_key` asks for `program`, `source_op_id`, `recipient`, `kind` in
that order. Guided `approval_ref` asks for `record_id`, `generation`,
`authority_id`, `actor_type`, `action`, `scope_ref`, then `evidence_refs` and
`prior_record`. All string fields are verbatim lines: only line endings are
removed, with no trimming, Unicode normalization, delimiter splitting or default
actor. `generation` requires a JSON integer excluding booleans, with no float
conversion or console policy limit. The existing FSM decides acceptable values.

Guided `source_view` asks, in order, for verbatim `phase`, verbatim `currency`,
then explicit JSON booleans `funds_executed`, `bank_debit_observed`,
`legal_debtor_bound`, `external_return_closed`, `durable`, and finally
`additional source fields`, an explicit JSON object (`{}` supplies none).
Booleans cannot be blank, null, numbers or strings. Additional fields cannot
collide with any of those seven prompted names, even if the values agree.
Nested names remain opaque. For example,
`{"metadata":{"sequence":9007199254740993,"phase":null},"label":"참여"}`
adds exactly those top-level fields, preserving integers, Unicode, nulls and
array order; no metadata wrapper is introduced.

This choice is available independently for `observe`, `mark_eligible`,
`observe_source_cancel` and `observe_krw_refund`. The console never supplies
COMMITTED, KRW, false flags, window closure, source identity or `source_kind`.
Blank/whitespace-bearing domain strings and true booleans reach the existing
FSM refusal path unchanged. Raw JSON also forwards incomplete source objects
to that path. The FSM currently requires COMMITTED, KRW and all five flags
false for all four operations: cancellation does not imply a CANCELLED snapshot.
A refund records its separate KRW effect without changing the token phase.
Snapshots are synthetic caller assertions, with no settlement-machine connection
or authentication. Legal effects remain **UNDETERMINED — User/legal**.

For `evidence_refs`, enter an explicit nonnegative JSON integer count followed
by exactly that many verbatim strings. Order and duplicates are preserved; zero
produces `[]` for the FSM's existing evidence-required refusal. No evidence is
inferred from a source snapshot or earlier reply. For `prior_record`, enter
literal `omit` to leave the key absent, or `include` followed by an explicit
JSON string or `null`. Omission, null and a supplied identifier stay distinct in
the request. Invalid composition discards the selection without dispatch; EOF
fences the session. Both paths use the existing structural validation before
preview and the same single-use `SUBMIT` confirmation.

These approval records are caller-entered **synthetic assertions**. Composition
provides no signature, credential, authentication or real approver provisioning.
Actual approver designation remains User-owned and E-1 remains open. Amounts,
caps, budgets, durations and approval policy remain **UNDETERMINED — Astra/User**.
Source snapshots, eligibility assertions, digests and outcomes are entered
separately; composition never fills them from an approval or earlier action.

Enter `window_closed`, `abuse_clear` as JSON
`true` or `false`. `amount` is an explicit decimal integer (optional minus sign;
no plus, exponent, decimal point or surrounding whitespace). Optional values use
JSON, including null or the complete `execution_permit` object. All remaining
fields are unquoted text without surrounding whitespace. Blank lines supply no
defaults. Source metadata and caller approval records pass through unchanged;
the console supplies no source phase, currency, flags, prior record or identity.
The FSM decides economic and lifecycle predicates, including negative amounts,
caps, pool restrictions, approval actors and unsupported selector values.

Before every mutation, the console prints and flushes complete canonical
`proposed={"operation":...,"arguments":...}`. Only literal `SUBMIT` sends that
request once; line endings are stripped, other whitespace is significant.
Anything else declines and discards the selection. A confirmation authorizes
one dispatch. There are no automatic reads, retries, reconciliation, subsequent
transitions, downstream actions or compensation. To inspect current state, choose
`view`, `reward_ids` or `pool_view` explicitly. UNKNOWN stays unresolved until
the caller separately selects and confirms a permitted action; a terminal
failure cannot resume dispatch in that session.

Complete `desk=<envelope>` output preserves provenance, receipts, reads and error
codes. Receipts are **historical action snapshots**, including replayed receipts;
explicit reads are **current session observations**. An old OBSERVED receipt
does not mean an ISSUED reward moved backward. `ISSUED` is synthetic and all seven
production flags remain false. Nothing authenticates the supplied source facts,
window closure or human approval slot. Policy values and approver designation
remain with the owners identified below.

Console statuses:

- **0:** explicit `quit` with no domain refusal. Declines, unknown menu choices
  and recoverable `input_error=` field syntax errors do not change status.
- **1:** any matching domain `error={"code":...}` / `TokenRewardError`; sticky
  through later explicitly selected accepted actions and reads.
- **2:** setup/dispatch-format failure, EOF (including at confirmation), interrupt,
  unexpected exception or I/O failure. Stop immediately, without rollback claims.
  Null-operation setup errors and typed service error envelopes are printed
  unchanged and stop immediately. Client-state failure, transport uncertainty,
  unexpected child exit or cleanup failure also exit 2. A normal child exit 1
  preserves domain-refusal status; cleanup cannot downgrade a failure.
  `FENCED:` diagnostics retain the last envelope when available and the exception
  chain. Transport uncertainty additionally preserves the detached `request`,
  lossless `request_bytes_hex` and observed `reply_bytes_hex`. Cleanup errors have
  separate diagnostics so the primary failure remains visible. Failure to write
  a diagnostic cannot authorize another call. Earlier mutations may be applied.
  No error permits automatic retry, child restart or in-process fallback.

Reproduce both console transcripts from the repository root:

```bash
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json < reference/token_reward/fixtures/reward_console_journey.txt
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json < reference/token_reward/fixtures/reward_console_boundaries.txt
```

Run the same transcripts against a live child:

```bash
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_journey.txt
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_boundaries.txt
```

The success transcript exits 0 after observe → hold → eligibility → submit →
effects, explicit historical replays and reads. The boundary transcript exits 1
after open-window, forbidden-pool and AI-approval refusals followed by successful
actions/reads. Both end with `quit`; EOF is not a clean exit.

Source-guided observation/eligibility and separate cancellation/refund journeys
reuse the existing `participation.jsonl` and `cancellation.jsonl` vectors:

```bash
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_source_journey.txt
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_source_cancellation.txt
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_source_boundaries.txt
```

Omit `--mode subprocess --cleanup-timeout 1` to replay in-process. The first two
exit 0; boundaries exits 1 after confirmed refusals, also demonstrating metadata
collision, malformed composition and decline without dispatch. Full captures,
coverage mapping and commands are in the [source composer evidence](../../validation/2026-11-09-plan-local-reward-source-composer/README.md).
This advances [token blueprint §9](../../docs/blueprints/optional-native-token-v1/README.md#9-거래-결합)
and the capability register's TL-3 offchain surface only; capability grades,
activation locks and A2 non-author exact-head review / KTX / KIX CI gates remain.

The [console evidence record](../../validation/2026-11-05-plan-local-reward-console/README.md)
contains captured stdout, coverage mapping and actual local checks. The console
has no child processes in in-process mode. Subprocess mode owns one local desk
child; neither mode uses sockets, external services, dependencies or
settlement/reward FSM coupling. The [live console evidence record](../../validation/2026-11-07-plan-plan-local-reward-live-console/README.md)
records composition coverage, captured transcripts and local checks. All
synthetic limitations and Class B observations below still apply.

Reproduce the guided journey (exit 0) and boundaries (exit 1, including three
discarded malformed selections, a decline and confirmed domain refusals):

```bash
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json < reference/token_reward/fixtures/reward_console_guided_journey.txt
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json < reference/token_reward/fixtures/reward_console_guided_boundaries.txt
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_guided_journey.txt
python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_guided_boundaries.txt
```

The [approval composer evidence](../../validation/2026-11-08-plan-local-reward-approval-composer/README.md)
records coverage, exact child-write parity, captured transcripts and actual local
checks. U3/F4 and TL-3 offchain boundaries and capability grades are unchanged.

## JSONL output and errors

Each output is deterministic sorted JSON containing `operation`, synthetic
`provenance`, and exactly one of `receipt`, `view`, `reward_ids`, `pool_view`,
`error`. Domain errors are `{"code":"<unchanged TokenRewardError.code>"}`;
format/setup/I/O errors use a distinct `type` and `message` (setup domain errors
also retain their code). Command-line usage errors follow argparse on stderr.

Exit codes: **0** all accepted; **1** at least one domain rejection; **2** malformed
input, setup or I/O failure. Domain rejection continues only to the next supplied
line. Malformed input stops immediately; earlier accepted requests remain applied.
Empty streams succeed; blank lines are malformed JSON.

Duplicate keys at every depth, non-finite constants and exponent overflow,
invalid JSON/Unicode, wrong object/array structures, missing/extra fields and
unsupported selectors are rejected before dispatch. The FSM retains all value,
approval, lifecycle and economic predicates.

## Synthetic limitations and Class B

`ISSUED` is an in-memory phase. All seven flags remain false: `token_issued`,
`onchain_recorded`, `funds_executed`, `krw_paid`, `chain_finality`, `durable`,
`legal_authority`. Non-transferability remains true through every exposed phase.
There are no external calls, funds, credentials, persistence, production runtime,
settlement/readiness connections, settlement-reward adapter, token modules or
Wave7 marketing. Process exit loses the session.

Policy amounts, caps, budgets and durations remain **UNDETERMINED with Astra/User**;
chargeback timing remains with the payment provider and actual approver designation
with User. Synthetic fixture numbers and human slots establish none of them.

Existing behavior is preserved, including these contract-undefined characterizations:

- Late injected invariant/pool failures have no rollback and can leave unjournaled
  mutations. Stored rejections are forgotten by FSM restoration. UNKNOWN resends
  do not consume approval records. See the existing [rejection-atomicity record](../../validation/2026-10-20-token-reward-rejection-atomicity/README.md).
- Approval normalization adds `prior_record=None` inside the FSM; restoring a
  normalized journal can change the original request fingerprint when the caller
  omitted that field. The desk does not normalize caller records or expose restore.
  See [snapshot isolation](test_snapshot_isolation.py) and its explicit prior-record fixture.
- Non-canonical `effect_id` arguments can raise `TypeError`; TL-4's
  [§6.B characterization](../../docs/decisions/TL4_THREAT_MODEL_20261009.md)
  is unchanged. This helper is outside CLI dispatch. Complete historical-envelope
  replay and detached-copy behavior remain source-informed Class B observations.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward
```

The [local evidence record](../../validation/2026-11-02-plan-local-reward-desk/README.md)
maps reused lifecycle coverage and new session/serialization/CLI tests, records
actual checks and transcripts, and states remaining gates. Builder checks do not
replace A2 non-author exact-final-head review or completed/success KTX and KIX
exact-final-head CI. No merge authorization is implied.

## Local pool accounting workbench

This separate process-local **synthetic POINT_F4 simulation** exposes only the
unchanged `token_reward_model.PoolLedger` constructor, `credit`, `spend` and
`view`. It has no connection to RewardMachine, settlement, credit, bank accounts
or token issuance. Pure JSON helpers are imported from `reward_fixture`; its
reward-session loader is never called. Process exit loses all state.

Pool balances, funding policy and approval values remain **UNDETERMINED —
Astra/User**. Accounting and legal treatment remain **UNDETERMINED —
User/designated advisers**. Example quantities are caller-provided synthetic
inputs, never defaults, recommended balances, funding policy or approval values.

`pool_cli.py` requires `--fixture PATH`. The console requires exactly one of
`--fixture PATH` or `--guided-init`. Fixture mode retains exactly these fields:

```json
{"fixture_version":1,"provenance":"MOCK_TOKEN_REWARD_ONLY","opening_balances":{"CUSTOMER_DEPOSIT":20,"ORGANIZER_SETTLEMENT":20,"REFUND_RESERVE":20,"PROTOCOL_REVENUE":2,"TOKEN_TREASURY_REWARD":9}}
```

All five opening balances are explicit. Version must be integer `1`; provenance
must match. The model rejects missing/extra pools with `POOL_BALANCES_REQUIRED`
and invalid opening amounts with its original codes. Its existing numeric bound
is `10**12` per balance; this is an implementation predicate, not product policy.

Put `reference/token_reward` on `PYTHONPATH` for the importable interface:

```python
from pool_session import PoolSession, read_opening_balances, dispatch_request

session = PoolSession(read_opening_balances("reference/token_reward/fixtures/pool_session.json"))
credited = session.credit("PROTOCOL_REVENUE", 5, "synthetic-source")
spent = session.spend("PROTOCOL_REVENUE", 3, "synthetic-program")
current = session.view()
reply = dispatch_request(session, {"operation": "view", "arguments": {}})
```

Session methods return model snapshots with `balances`, `credits` and `spends`.
Returned snapshots are detached. Domain errors raise unchanged `TokenRewardError`.
The session constructs exactly one ledger and forwards each selected call once.

JSONL records require exactly `operation` and `arguments`. The only local
selectors and their exact argument fields are:

| Selector | Argument fields |
|---|---|
| `credit` | `pool`, `amount`, `source_ref` |
| `spend` | `pool`, `amount`, `program_ref` |
| `view` | Empty object `{}` |

For example:

```jsonl
{"operation":"credit","arguments":{"pool":"PROTOCOL_REVENUE","amount":5,"source_ref":"synthetic-source"}}
{"operation":"spend","arguments":{"pool":"PROTOCOL_REVENUE","amount":3,"program_ref":"synthetic-program"}}
{"operation":"view","arguments":{}}
```

Amounts and references are always explicit. JSON values are never coerced:
booleans, floats, null and numeric strings reach the model unchanged and retain
its original amount rejection codes. Integers remain exact, including values
above binary-float precision. Missing/unknown fields, unsupported selectors,
duplicate keys, malformed JSON/UTF-8, invalid Unicode and non-finite numbers are
interface errors before dispatch. A blank JSONL line is malformed; empty EOF
ends normally. Local selectors add no protocol commands.

```bash
python3 reference/token_reward/pool_cli.py --fixture reference/token_reward/fixtures/pool_session.json --requests reference/token_reward/fixtures/pool_journey.jsonl
python3 reference/token_reward/pool_cli.py --fixture reference/token_reward/fixtures/pool_session.json --requests - < reference/token_reward/fixtures/pool_boundaries.jsonl
python3 reference/token_reward/pool_console.py --fixture reference/token_reward/fixtures/pool_session.json < reference/token_reward/fixtures/pool_console_journey.txt
python3 reference/token_reward/pool_console.py --fixture reference/token_reward/fixtures/pool_session.json < reference/token_reward/fixtures/pool_console_boundaries.txt
python3 reference/token_reward/pool_console.py --guided-init
python3 reference/token_reward/pool_console.py --guided-init < reference/token_reward/fixtures/pool_console_opening_journey.txt
python3 reference/token_reward/pool_console.py --guided-init < reference/token_reward/fixtures/pool_console_opening_boundaries.txt
```

Each JSONL output has `operation`, `provenance`, `unit: "POINT_F4"`, a synthetic
notice and all seven false flags listed above. It contains exactly one of
`initialized`, `view`, or `error`. The initialization acknowledgement describes
the supplied opening balances without an implicit view. Successful actions
preserve the complete model snapshot unchanged under `view`; there are no
receipts. Domain errors retain `{"code":"<original code>"}`; interface/setup/I/O
errors use `type` and `message` (constructor domain errors retain their code).
Setup/I/O diagnostics go to stderr; request errors appear in the JSONL stream.
Argparse usage errors use its normal stderr help.

The guided console is also importable as
`pool_console.run_console(opening_balances, input_stream=..., output_stream=..., error_stream=...)`.
Omitting the positional opening balances selects guided entry; explicitly passing
`None`, `{}` or another invalid fixture value retains constructor validation.
Guided entry prompts for `CUSTOMER_DEPOSIT`, `ORGANIZER_SETTLEMENT`,
`REFUND_RESERVE`, `PROTOCOL_REVENUE`, then `TOKEN_TREASURY_REWARD`. Every prompt
requires a separate explicit signed ASCII decimal integer (`[+-]?[0-9]+`).
No balance is suggested, defaulted, trimmed, rounded, clamped or retried.
Blank input, decimals, exponents, booleans, whitespace and Unicode digits are
lexical errors. All five values are collected without constructing a ledger.
The complete initialization then uses the same preview, confirmation and result
envelopes as fixture mode. Zero and `10**12` are accepted opening amounts;
negative and over-limit integers reach the unchanged model after confirmation,
retaining `INVALID_NONNEGATIVE`, `operation: null` and exit `2`. Credit/spend
amount validation separately retains `INVALID_AMOUNT`.

It displays and flushes the complete initialization proposal before constructing
a ledger. Only literal `SUBMIT` constructs it. A decline exits without construction.
After initialization, select `credit`, `spend`, `view` or local `quit`. Enter the
mutation fields in table order; strings are verbatim, and amount input is a
signed decimal integer (`+2`, `2`, `-2` are parsed exactly, then model-validated).
Each mutation prints and flushes a complete request preview and requires another
literal `SUBMIT`. Any other confirmation discards that request. `view` performs
one explicitly selected read. No other implicit reads or actions occur.

For a file-free journey, run `--guided-init` and enter all the lines in
`fixtures/pool_console_opening_journey.txt` at its prompts. The first five lines
are explicitly entered synthetic example balances; the remaining lines confirm
initialization and perform credit, spend and view in the same process. Decline
exits `0`; incomplete input, EOF, interruption or terminal failure before
confirmation exits `2` without constructing a ledger. Later terminal failure
stops further dispatch without rollback or automatic retry. The
[opening composer evidence and captured transcripts](../../validation/2026-11-09-plan-local-pool-opening-composer/README.md)
include a here-document invocation requiring no fixture or input file. Local
results retain A2 non-author exact-final-head review and both required CI gates.

Only `PROTOCOL_REVENUE` and `TOKEN_TREASURY_REWARD` permit spends. All three
obligation pools reject spending with `POOL_FORBIDDEN_FOR_TOKEN_SPEND`.
Insufficient funds produce `POOL_EXHAUSTED_PAUSED` without borrowing from another
pool. Ordinary domain refusals preserve state. **Repeated source/program
references are not deduplication keys**: another accepted call appends another
entry and changes the balance again, exactly as a direct model call does.

Exit codes: **0** clean completion/quit or initialization decline; **1** any
confirmed domain refusal; **2** malformed input, setup, EOF in the console,
interruption or I/O failure. Domain refusal continues only to the next explicitly
supplied record or console selection. Malformed input stops. Terminal failure
stops further dispatch. Output failure after a mutation does not roll it back;
there is no retry. Console prompts are human text, while replies are JSON.

There is no polling, retry, restoration, persistence, external call, transfer or
funding automation. `token_issued`, `onchain_recorded`, `funds_executed`, `krw_paid`,
`chain_finality`, `durable` and `legal_authority` remain false. These tests establish
no bank execution, chain finality, durability, accounting/legal conclusion or
production readiness. The [pool workbench validation record](../../validation/2026-11-09-plan-plan-local-pool-accounting-workbench/README.md)
contains the coverage map, real transcripts, actual commands and protected-byte
checks. A2 non-author exact-head review and required KTX/KIX CI remain delivery gates.

## Live pool subprocess client

`pool_client.PoolClient` owns one synchronous `pool_cli.py` child using binary
UTF-8 JSONL pipes, with separate inherited stderr. Importing launches nothing.
The caller confirms its synthetic opening snapshot before launch and confirms
each mutation before calling `request`. Put `reference/token_reward` on
`PYTHONPATH`, then, after that confirmation:

```python
from pool_client import PoolClient
from pool_session import read_opening_balances

fixture = "reference/token_reward/fixtures/pool_session.json"  # caller-selected
confirmed = read_opening_balances(fixture)  # preview and confirm before launch
with PoolClient.launch(fixture, expected_opening_balances=confirmed,
                       cleanup_timeout=1) as client:  # caller-selected cleanup seconds
    acknowledgement = client.initialized_reply
    # After separately confirming these complete mutation requests:
    credited = client.request({"operation": "credit", "arguments": {
        "pool": "PROTOCOL_REVENUE", "amount": 5, "source_ref": "synthetic-source"}})
    spent = client.request({"operation": "spend", "arguments": {
        "pool": "PROTOCOL_REVENUE", "amount": 3, "program_ref": "synthetic-program"}})
    current = client.request({"operation": "view", "arguments": {}})
```

The console has an explicit live mode using a caller-selected fixture:

```bash
python3 reference/token_reward/pool_console.py --mode subprocess --cleanup-timeout 1 --fixture reference/token_reward/fixtures/pool_session.json < reference/token_reward/fixtures/pool_console_journey.txt
```

`--mode in-process` remains the default and supports both `--fixture PATH` and
`--guided-init`. Subprocess mode requires `--fixture PATH` and a caller-selected
finite positive `--cleanup-timeout SECONDS`; it rejects `--guided-init`.
In-process mode rejects a cleanup timeout. These combinations are checked before
launch. Importable `run_console` selects subprocess mode with the additional
`fixture=PATH, cleanup_timeout=SECONDS` keyword arguments and an explicit opening
snapshot. Both modes share the same complete flushed previews, literal `SUBMIT`
and action loop. Declining initialization launches nothing; declining a mutation
writes nothing. `view` is one explicit request, with no confirmation or hidden read.

Before launching, the client checks the fixture against the confirmed snapshot.
Before permitting requests, it validates the existing initialization acknowledgement
and compares its five balances with that snapshot, distinguishing integers from
booleans/floats. A change between preview and startup fails closed. Initialization
is an existing service acknowledgement, never an added wire request. The client
validates strict JSONL framing, UTF-8/duplicate keys, selector correlation, complete
payload shapes, synthetic provenance, unit/notice and literal false execution
flags. It returns each complete decoded service envelope, without recomputing
balances, removing entries or changing refusal codes. Wrong finite domain values
still reach the unchanged model. A valid domain refusal permits only another
explicit request; a typed service error fences the client.

One exchange may be outstanding. Overlapping request/cleanup calls and use after
fencing/close raise `PoolClientStateError` before another write. Local request
shape failures submit nothing and leave the client usable. Broken pipes, short
writes, malformed/truncated replies, lost acknowledgements and interruption
raise `PoolTransportUncertainty`, permanently fencing this instance. The exception
(and `client.uncertainty`) retains `phase`, detached `request`, `request_bytes`,
`reply_bytes` observed before failure and a chained cause. Initialization uncertainty
has no submitted request and empty request bytes. A mutation may already have been
accepted when its acknowledgement is lost. No retry, replacement, rollback or
rejection is inferred. Startup failure cleans up the child before raising.

`close()` is idempotent and returns the reaped child exit status. It closes stdin,
waits, and terminates then kills only the owned child when necessary. The required
cleanup timeout applies to cleanup waits only. Reads remain blocking and
interruptible, with no polling or response deadline. Console cleanup runs after
every post-launch exit; observed domain refusals explain child status `1`, while
unexpected child exits are terminal failures. Console exits remain `0` clean or
declined initialization, sticky `1` for confirmed domain refusal, and `2` for
terminal failure. Cleanup loses process-local state and proves no rollback.

Repeated references still append repeated accepted entries. No deduplication,
receipts, reward coupling, sockets, services, dependencies, persistence or protocol
commands are added. Pool balances/funding policy remain caller-supplied synthetic
inputs / **UNDETERMINED — Astra/User**; accounting treatment remains
**UNDETERMINED — User/designated advisers**. No funds, issuance, chain finality,
durability, legal authority, runtime activation or production readiness is claimed.
[Builder coverage, transcripts and local validation](../../validation/2026-11-09-plan-local-pool-live-console/README.md)
are separate from A2 non-author exact-final-head review and required KTX/KIX CI.
