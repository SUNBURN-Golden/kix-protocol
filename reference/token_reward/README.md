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

## Output and errors

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
