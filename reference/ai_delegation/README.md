# Local AI delegation desk

`DelegationSession` exposes the existing `AiDelegationMock` through seven explicit
methods. Each CLI process owns one fresh, sequential, synthetic, in-memory session.
Receipts, views, domain errors and current-record replay behavior come from the
unchanged [mock](ai_delegation_mock.py) and
[authority contract](../../docs/contracts/AI_DELEGATION_AUTHORITY.md).
Local operation selectors add no protocol commands or authority semantics.

## Importable session

Put `reference/ai_delegation` on `PYTHONPATH`, following the reference-module
convention, then supply every actor, identifier, authority, scope, limit and time:

```python
from delegation_session import DelegationSession

session = DelegationSession(["human-a"], ["agent-a", "agent-b"])
receipt = session.issue_grant(
    actor="human-a", grant_id="g-1", agent_id="agent-a",
    authority=["QUERY", "PROPOSE"],
    scope={"surfaces": ["surface-a"], "subjects": ["subject-a"]},
    limits={"per_action_max": 100, "cumulative_max": 150,
            "count_max": 2, "currency": "KRW"},
    period={"not_before": 10, "not_after": 20})
print(session.view_grant("g-1"))
```

The amounts and names above are synthetic inputs, not product policy or actual
identity designations. The constructor delegates registry validation to the mock.
Method signatures match the mock, including positional and keyword calling.
Each method calls its selected mock method once. There are no implicit views,
preflights, retries, polling, generated IDs or inferred defaults. Generations retain
the mock's existing meaning: a local counter for each `(issuer, agent_id)` pair.
`canonical_state`, `state_digest`, restoration and persistence are not exposed.

## Schemas

The fixture has exactly four keys; version is integer `1`, excluding boolean:

```json
{"fixture_version":1,"provenance":"MOCK_AI_DELEGATION_ONLY","human_principals":["human-a"],"ai_agents":["agent-a","agent-b"]}
```

Registries alone initialize the session. Grants and proposals cannot be restored
through the fixture. Each JSONL request has exactly `operation` and `arguments`:

```json
{"operation":"view_grant","arguments":{"grant_id":"g-1"}}
```

| Operation | Required arguments (no optional method arguments) |
|---|---|
| `issue_grant` | `actor`, `grant_id`, `agent_id`, `authority`, `scope`, `limits`, `period` |
| `revoke_grant` | `actor`, `grant_id`, `reason` |
| `decide_proposal` | `actor`, `proposal_id`, `decision`, `now` |
| `call_tool` | `actor`, `grant_id`, `tool`, `args`, `now` |
| `attempt_execution` | `actor`, `proposal_id` |
| `view_grant` | `grant_id` |
| `view_proposal` | `proposal_id` |

Nested domain values pass unchanged to the mock, whose validation and error codes
apply. `authority` is a nonempty subset of `QUERY` and `PROPOSE`; `EXECUTE` yields
`EXECUTE_AUTHORITY_DISABLED`. `scope` requires `surfaces`, optionally `subjects`.
`limits` requires `per_action_max`, `cumulative_max`, `count_max` and `currency`;
only `KRW` is accepted, and amounts/counts use the existing integer fixture range
`1..10**12` excluding boolean. `period` requires logical `not_before` and
`not_after`; caller-supplied `now` uses that same logical time axis, not wall time.
Decisions are `APPROVE` or `REJECT`. Reasons and other identifiers remain opaque.

| `call_tool.tool` | `args` |
|---|---|
| `query_grant` | `{}` |
| `query_subject` | required `surface`; optional `subject` |
| `propose_action` | required `proposal_id`, `surface`, `amount`, `kind`; optional `subject` |
| `withdraw_proposal` | required `proposal_id` |
| `propose_grant_change` | required `proposal_id`, `requested` |

`requested` is a nonempty memo containing any of `authority`, `scope`, `limits`,
`period`, `note`. Structured fields use the same existing mock predicates. It
never changes the issued grant. Tool names pass through unchanged; transfers,
refund execution, signing, issue/pay and self-expansion receive the mock's
existing refusal codes. Unknown names, including `delegate` and
`close_delegation`, yield `TOOL_NOT_ALLOWED`.

## Runnable journeys

Run from the repository root with the Python standard library:

```bash
python3 reference/ai_delegation/delegation_cli.py --fixture reference/ai_delegation/fixtures/delegation_session.json --requests reference/ai_delegation/fixtures/lifecycle.jsonl
python3 reference/ai_delegation/delegation_cli.py --fixture reference/ai_delegation/fixtures/delegation_session.json --requests reference/ai_delegation/fixtures/boundaries.jsonl
python3 reference/ai_delegation/delegation_cli.py --fixture reference/ai_delegation/fixtures/delegation_session.json --requests reference/ai_delegation/fixtures/replay.jsonl
python3 reference/ai_delegation/delegation_cli.py --fixture reference/ai_delegation/fixtures/delegation_session.json --requests - < reference/ai_delegation/fixtures/lifecycle.jsonl
```

`lifecycle` (exit 0) covers both query tools, action proposals, human approval and
rejection, withdrawal after expiry, an inert grant-change memo, revocation,
retained views and a new generation. `boundaries` (exit 1) covers actor, authority,
scope, amount, cumulative/count/period limits, denylisted/unknown tools and disabled
execution. `replay` (exit 1) explicitly repeats requests and changes bindings.
No request is generated by model output.

Identical grant/proposal bindings return `duplicate=true` with the **current**
record, including later decisions, withdrawal and revocation. Changed bindings
yield `GRANT_BINDING_CONFLICT` or `PROPOSAL_BINDING_CONFLICT`. Repeated revocation
retains the first reason. These are the existing delegation replay semantics.
Each explicit view fetches once; process exit loses all state.

## Output and errors

Every response is canonical sorted JSON containing `operation`,
`provenance="MOCK_AI_DELEGATION_ONLY"` and exactly one of `receipt`, `view`, `error`.
Returned dictionaries are embedded unchanged. Domain errors are
`{"code":"<unchanged AiDelegationError.code>"}`. `attempt_execution` always reports
`DELEGATED_EXECUTION_DISABLED`, regardless of actor/proposal values. Transport
and I/O errors use separate `type`/`message` fields. Setup domain errors also
retain their code. Errors before a selector can be read have `operation=null`.
Command-line usage errors follow argparse on stderr.

Exit codes: **0** accepted stream; **1** one or more domain rejections;
**2** malformed input, setup or I/O failure. A domain rejection continues only to
another supplied line. Malformed input stops immediately; earlier accepted calls
remain applied. Empty streams succeed; blank lines fail. Duplicate keys at all
depths, non-finite numbers (including exponent overflow), invalid JSON/Unicode,
unsupported selectors, invalid envelopes and missing/extra method arguments fail
before dispatch. Nested domain validation remains the mock's responsibility.

## A5 and non-claims

The existing class-C **A5** check-order discrepancy remains attributed to
[October 26's addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure)
and [October 27's closure](../../docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md).
The mock checks actor registration, then tool lists, then grant-agent binding;
contract §7 specifies grant-agent binding before tool lists. A registered wrong
agent combined with a denied/unknown tool is the unresolved precedence case.
A5 is not a dependency of this desk. This delivery neither repairs nor claims
conformance for that case; new normative transcripts exclude it. Resolution belongs
to Astra as contract/design authority, with User authorization of resulting
scope/contract changes and User merge. Missing-grant binding remains UNDETERMINED
with that same owner. Existing broader simultaneous-error characterizations are
not promoted to ordered-precedence evidence.

Views retain `lifecycle_authority="IN_MEMORY_FSM"`. All eleven flags stay false:
`execution_enabled`, `funds_executed`, `issued`, `paid`, `signed`, `transferred`,
`refund_executed`, `chain_grant_confirmed`, `revocation_cut_confirmed`, `durable`,
`legal_authority`. Proposal `effects_executed` stays false even after approval.
Human approval is an inert memo, not legal or payment authorization.

Product limits/aggregation and permitted business surfaces remain **UNDETERMINED
with Astra**; identity policy with **Astra/User**; authoritative time and chain
cuts with **k1-cut-proof / RS-3a**; legal authority with **legal review / User**,
as recorded in contract §9. No fixture supplies these decisions. No persistence,
readiness integration, model-driven actions, execution enablement, runtime,
external funds/provider/chain calls, credentials or protocol changes are added.
No durability, distributed fencing, bank exactly-once, chain finality, compliance,
capability-grade increase or production readiness is claimed.

## Interactive console

[delegation_console.py](delegation_console.py) guides the same seven operations
through `delegation_cli.dispatch_request` by default, in one fresh session per
process. Explicit subprocess mode uses the same prompts and envelopes via one
owned local desk child:

```bash
python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json
python3 reference/ai_delegation/delegation_console.py --mode subprocess --cleanup-timeout 1 --fixture reference/ai_delegation/fixtures/delegation_session.json
```

Importable interface:
`run_console(session, *, input_stream, output_stream, error_stream) -> int`;
`run_subprocess_console(fixture, *, cleanup_timeout, input_stream, output_stream,
error_stream) -> int`; `main(argv=None) -> int`. `--mode in-process` is the default.
`--cleanup-timeout` is required only in subprocess mode and rejected in in-process
mode; it bounds child cleanup, never response reads. Standard library only,
synchronous, no model or
execution service. The required registry fixture is the exact four-key schema
above; no fixture default, restore, persistence or opening grant is supplied.

Choose a menu operation, then enter **one line per argument**, in this order:

| Operation | Console prompt order |
|---|---|
| `issue_grant` | `actor`, `grant_id`, `agent_id`, `authority`, `scope`, `limits`, `period` |
| `call_tool` | `actor`, `grant_id`, `tool`, `args`, `now` |
| `decide_proposal` | `actor`, `proposal_id`, `decision`, `now` |
| `revoke_grant` | `actor`, `grant_id`, `reason` |
| `view_grant` | `grant_id` |
| `view_proposal` | `proposal_id` |
| `attempt_execution` (always refused) | `actor`, `proposal_id` |
| `quit` (local only) | none |

Plain text fields are explicit nonempty strings without surrounding whitespace.
No actor, identifier, authority, scope, amount, limit or logical time is inferred.
`authority`, `scope`, `limits`, `period` and `args` accept strict JSON or literal
`:guided` for the composition prompts below. `now` always uses strict JSON:

| Field | Structural checks before preview/dispatch |
|---|---|
| `authority` | array of strings |
| `scope` | object with `surfaces` array of strings; optional `subjects` array of strings |
| `limits` | exact object with integer `per_action_max`, `cumulative_max`, `count_max` and string `currency` |
| `period` | exact object with integer `not_before`, `not_after` |
| `now` | integer; booleans/floats excluded |
| `args` | object matching the five supported tool schemas above |
| `args.requested` | object with only `authority`, `scope`, `limits`, `period`, `note`; structured fields checked as above, `note` a string |

Duplicate JSON keys, non-finite numbers, invalid Unicode, missing/extra fields and
wrong structural types abandon the current action with `input_error=<CLI error
envelope>` and zero dispatch. The next line selects a fresh action; do not supply
the abandoned action's remaining fields. Unknown menu selections also dispatch
nothing. Arrays, identifiers, ranges, currency, authority membership, scope,
period validity and record binding are otherwise validated by the unchanged mock.
An empty `requested` object is structurally valid and receives the mock's refusal
if confirmed. Denied/unknown tool names accept an object for `args` and forward
unchanged to the domain refusal path; this adds no supported tool or command.

For guided entry, supply one line at each prompt. There are no prefilled values:

| Guided value | Prompt sequence |
|---|---|
| `authority` | nonnegative JSON integer item count, then that many verbatim string items |
| `scope` | `surfaces` count/items; literal `include` or `omit` for `subjects`; if included, its count/items |
| `limits` | JSON integers `per_action_max`, `cumulative_max`, `count_max`; verbatim `currency` |
| `period` | JSON integers `not_before`, `not_after` |
| `query_grant` args | no fields; composes `{}` and still requires final confirmation |
| `query_subject` args | `surface`; `include`/`omit` for `subject`; if included, its verbatim value |
| `propose_action` args | `proposal_id`, `surface`, JSON integer `amount`, `kind`; optional `subject` as above |
| `withdraw_proposal` args | `proposal_id` |
| `propose_grant_change` args | `proposal_id`, then `requested` as JSON or `:guided` |
| `requested` | a separate `include`/`omit` choice for each of `authority`, `scope`, `limits`, `period`, `note`, in that order; included structured fields accept JSON or `:guided`, and included `note` is verbatim text |

Counts and include/omit choices never enter the request. Blank choices are errors.
Omitted keys differ from included empty lists or strings. List order and duplicates
are preserved in the request; the existing desk may normalize its records.
Nested strings preserve spaces, commas, Unicode and literal `:guided` without
trimming or splitting; only line terminators are removed. Top-level identifiers
keep their existing nonempty/no-surrounding-whitespace checks. Integers remain
exact, including values above `2**53`; booleans and floats are input errors.
No value is rounded, clamped, generated or chosen from the fixture.

Empty authority, empty `requested`, unsupported currency, out-of-range integers
and `EXECUTE` still reach the unchanged mock refusal path only after confirmation.
Guided args for denied/unknown tools are input errors; their raw JSON object
entry remains available. A malformed composition discards the action; enter a
fresh menu action next. EOF at any composition prompt stops the console.
Composition performs no desk reads or writes. The same complete preview and
literal `SUBMIT` below govern both JSON and guided input; no composition metadata
appears in the unchanged request envelope.

Every request, **including views**, prints and flushes its entire canonical
`proposed={"arguments":...,"operation":...}` preview before asking for literal
`SUBMIT`. Every other confirmation, including blank input or surrounding spaces,
discards that request. Preview and decline perform no session reads or writes.
Each confirmed request dispatches exactly once, using the exact previewed values;
there are no preflight views, hidden actions, retries or cleanup mutations.
Complete unchanged replies appear as `desk=<canonical CLI envelope>` on their own
lines amid prompts. The reply is retained before rendering for failure diagnostics.

### Runnable console transcripts

From the repository root:

```bash
python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json < reference/ai_delegation/fixtures/delegation_console_journey.txt
python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json < reference/ai_delegation/fixtures/delegation_console_replay.txt
python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json < reference/ai_delegation/fixtures/delegation_console_boundaries.txt
```

[Journey](fixtures/delegation_console_journey.txt) exits 0: grant issuance, all
five supported tools, human approve/reject, withdrawal after expiry, inert grant
change, revocation, retained views and a new generation. Its requests match the
existing desk lifecycle fixture. [Replay](fixtures/delegation_console_replay.txt)
exits 1: explicitly confirmed duplicates and binding conflicts, including current
approved/withdrawn/voided proposals and a revoked grant; first revocation reason
is retained. Its requests match the existing desk replay fixture.
[Boundaries](fixtures/delegation_console_boundaries.txt) exits 1: malformed and
declined input sends no requests, followed by separately confirmed scope,
expiration, amount, transfer and disabled-execution refusals and retained views.
New transcripts exclude A5's simultaneous-error case.

Guided equivalents also run through one real local child:

```bash
python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_guided_journey.txt
python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_guided_boundaries.txt
```

[Guided journey](fixtures/delegation_console_guided_journey.txt) exits 0 and sends
the exact existing lifecycle envelopes, including all five tools, human decisions
and revocation. [Guided boundaries](fixtures/delegation_console_guided_boundaries.txt)
exits 1: four malformed compositions and two declines send nothing; confirmed
requests match the existing boundary transcript plus an `EXECUTE` authority refusal.
The `1` second cleanup timeout is explicit synthetic transport configuration.
The [composer builder evidence](../../validation/2026-11-08-plan-local-delegation-input-composer/README.md)
records coverage, actual commands and captured subprocess transcripts. Product
limits, permitted surfaces and proposal kinds remain **UNDETERMINED — Astra**;
identity policy **UNDETERMINED — Astra/User**; legal effects **UNDETERMINED —
User/legal**. A5 remains unresolved; A2 non-author exact-head review and required
KTX/KIX CI remain separate gates.

### Console output, exits and replay

Exit **0** means clean `quit` with no ordinary domain refusal; invalid or declined
input alone does not change this status. Exit **1** is sticky after any ordinary
`AiDelegationError` refusal, even if later actions succeed. Exit **2** means EOF
(including at confirmation), read/write/short-write/flush failure, unexpected
error, interruption, setup failure or `MOCK_INVARIANT`; no later action runs and
nothing is retried. Best-effort stderr `FENCED:` diagnostics include a CLI failure
envelope and the last complete reply, when available. Diagnostic failure also
stops immediately. Command-line usage follows argparse on stderr.

A failure after dispatch may follow an already applied mutation. A missing reply
is not evidence of non-application. Output failure fences the process without
resubmission. State is process-local and disappears on exit.

Replay is explicit re-entry of an existing operation followed by a fresh `SUBMIT`;
there is no replay command. Duplicate grants/proposals return **current records**,
including decisions, withdrawal or revocation; they are not historical receipts.
Repeated revocation keeps the first reason. The mock's binding conflicts and
current-record replay semantics above remain unchanged. Approval executes nothing;
all eleven flags and proposal `effects_executed` remain false. The existing A5
class-C discrepancy, missing-grant uncertainty and Astra/User ownership in
[A5 and non-claims](#a5-and-non-claims) remain unresolved. No ordered-precedence
conformance is claimed. Product limits and permitted surfaces remain
**UNDETERMINED — Astra**, identity policy **UNDETERMINED — Astra/User**, and legal
authority **UNDETERMINED — User/legal**; synthetic input values do not decide them.

The [console builder evidence](../../validation/2026-11-06-plan-plan-local-delegation-console/README.md)
maps existing coverage before the new [console tests](test_delegation_console.py),
actual commands and limitations. Run its narrow tests before full discovery:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_console
```

## Reusable local subprocess client

[delegation_client.py](delegation_client.py) uses only the standard library.
Importing it launches nothing. Put this directory on `PYTHONPATH`, then:

```python
from delegation_client import DelegationClient

with DelegationClient.launch(
        "reference/ai_delegation/fixtures/delegation_session.json",
        cleanup_timeout=1) as client:
    # A caller supplies every value; the existing lifecycle fixture is synthetic.
    from delegation_fixture import decode_json
    from pathlib import Path
    issue = decode_json(Path("reference/ai_delegation/fixtures/lifecycle.jsonl")
                        .read_text(encoding="utf-8").splitlines()[0])
    reply = client.request(issue)
    if "receipt" in reply:
        # A subsequent explicit read depends on the response, before stdin EOF.
        grant_id = reply["receipt"]["grant"]["grant_id"]
        print(client.request({"operation": "view_grant",
                              "arguments": {"grant_id": grant_id}}))
    else:
        print(reply)
```

`DelegationClient.launch(fixture, *, cleanup_timeout)` owns exactly one fresh
sequential session, launched with `sys.executable`, the absolute `delegation_cli.py`
path, `--fixture <absolute path> --requests -`, `shell=False`, binary stdin/stdout
pipes and inherited stderr. The child uses ordinary buffering, without `-u`.
The CLI flushes each complete canonical JSONL reply so requests and
response-dependent reads can be interleaved without closing stdin.
`request(request: dict) -> dict` sends one explicit request, using the seven
selectors and exact required argument sets above. It validates finite JSON and
serializes fully before writing; invalid local envelopes/selectors/arguments write
nothing and leave the client usable. Nested business values pass unchanged to the
mock. There is no duplicate implementation of authorization, limits, phase
transitions, binding or replay predicates.

Only one request or cleanup may be outstanding. Busy, closed or terminal use raises
`DelegationClientStateError` before writing. Reads block without polling or a
response deadline. The mandatory finite positive `cleanup_timeout` bounds each
cleanup wait, in seconds; it is caller-selected transport cleanup input, not a
product duration or policy value. `close() -> int` closes stdin and reaps only the
owned child, escalating wait → terminate → kill as needed. It is idempotent after
successful cleanup. Context manager exit calls `close()`; after an exceptional
cleanup, the client remains terminal and cleanup can be explicitly completed.

Each reply must be a newline-terminated UTF-8 JSON object with strict decoding:
blank/truncated frames, duplicate keys, non-finite numbers, invalid Unicode and
multiple objects in one frame fail. The client checks the exact envelope,
operation correlation (except an explicit startup `operation=null` error),
provenance, payload kind, grant/proposal/query structural variants, nullable fields,
normalized `scope.subjects`, returned identifiers, nested provenance and
`IN_MEMORY_FSM`. All eleven flags must be strictly `false`, as must proposal
`effects_executed`. A successful `attempt_execution` reply is invalid. These are
transport checks against the existing response shapes, not independent domain
conformance or authentication of an untrusted executable.

Ordinary correlated `{code: ...}` domain refusals allow a later explicit request.
Typed `{type, message}` errors, startup errors and `MOCK_INVARIANT` are terminal;
the complete envelope is returned and retained on `client.last_reply`. The console
renders that envelope, then exits 2. Ordinary domain refusal is sticky exit 1.
`client.last_reply` also retains a detached copy of the last validated reply before
rendering. Malformed/mismatched replies, child exit during an exchange, short or
broken writes, I/O failures and caller interruptions raise
`DelegationTransportUncertainty` and permanently fence the client. The exception
and `client.uncertainty` retain detached `request`, exact `request_bytes`, observed
`reply_bytes`, exception cause and `last_reply`. Cleanup preserves this evidence.
No retry, replacement child or in-process fallback occurs. Missing evidence never
establishes non-application or permits resubmission. Diagnostic stderr `FENCED:`
records include the exception chain and wire bytes as hex; cleanup failures get a
separate diagnostic preserving the primary failure and last complete reply.

Both console modes require a flushed preview and literal `SUBMIT` for **every**
action, including views. Declines send nothing. Quit closes the child without a
hidden read or mutation. Execution remains disabled; human approval is an inert
memo. The [A5 discrepancy and owners](#a5-and-non-claims) remain unchanged.
Product limits/surfaces are **UNDETERMINED — Astra**, identity **UNDETERMINED —
Astra/User**, legal effects **UNDETERMINED — User/legal**. This local service mode
adds no model service, socket, credential, persistence, public endpoint, production
runtime, chain call or protocol command.

The [live client/console builder evidence](../../validation/2026-11-07-plan-plan-local-delegation-live-console/README.md)
contains the initial coverage map, commands/results, preservation manifests and
captured transcripts. It is source-informed builder evidence; A2 non-author
exact-final-head review and completed/success exact-head KTX/KIX CI remain gates.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_client test_delegation_console_subprocess test_delegation_console test_delegation_cli test_delegation_serialization test_delegation_session
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation
```

The [builder evidence](../../validation/2026-11-05-plan-local-ai-delegation-desk/README.md)
maps reused coverage and the new [session](test_delegation_session.py),
[serialization](test_delegation_serialization.py) and [CLI](test_delegation_cli.py)
tests, actual commands, transcripts and limitations. A2 non-author exact-final-head
review and completed/success exact-head KTX/KIX CI remain separate publication
gates. Builder readiness grants no merge authority.
