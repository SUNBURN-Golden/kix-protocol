# Local F4 reward desk

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
the existing nested schemas above. At `reward_key` or `approval_ref`, literal
`:guided` optionally collects the same object field by field. Raw JSON remains
available independently at every selection, including `submit` and `supersede`.

Guided `reward_key` asks for `program`, `source_op_id`, `recipient`, `kind` in
that order. Guided `approval_ref` asks for `record_id`, `generation`,
`authority_id`, `actor_type`, `action`, `scope_ref`, then `evidence_refs` and
`prior_record`. All string fields are verbatim lines: only line endings are
removed, with no trimming, Unicode normalization, delimiter splitting or default
actor. `generation` requires a JSON integer excluding booleans, with no float
conversion or console policy limit. The existing FSM decides acceptable values.

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
