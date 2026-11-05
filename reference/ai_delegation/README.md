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

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_session test_delegation_serialization test_delegation_cli
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation
```

The [builder evidence](../../validation/2026-11-05-plan-local-ai-delegation-desk/README.md)
maps reused coverage and the new [session](test_delegation_session.py),
[serialization](test_delegation_serialization.py) and [CLI](test_delegation_cli.py)
tests, actual commands, transcripts and limitations. A2 non-author exact-final-head
review and completed/success exact-head KTX/KIX CI remain separate publication
gates. Builder readiness grants no merge authority.
