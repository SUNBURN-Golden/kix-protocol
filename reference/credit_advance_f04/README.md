# Local settlement claim adapter

`SettlementClaimAdapter` is an importable, offline bridge from one explicitly
selected settlement view to the unchanged `CreditMachine.offer`. It performs one
source read and at most one offer per invocation, including replay. It does not
bind, approve, draw, distribute, refresh a face or observe repayments.

## Coverage inventory (before adding adapter tests)

Paths below are relative to `reference/`. Existing FSM predicates are reused;
the new tests exercise the adapter boundary and parity, not new credit policy.

| Requirement | Existing coverage classification | Existing evidence / gap |
|---|---|---|
| Statement-backed claim → OFFERED, zero exposure | Partially covered | `settlement_f01_f03/test_statement_adapter.py::StatementExampleTests.test_example_uses_actual_fsm_and_requires_explicit_fixture_policy_order`; `credit_advance_f04/test_credit_fsm.py::CreditFsmTests.test_offer_approve_draw_repay_and_close_are_mock_ledger_only`; composition missing |
| Separate binding/approval and COMMITTED draw gate | Sufficiently covered for FSM | `test_credit_fsm.py::CreditFsmTests.test_bound_draw_waits_for_mock_commit_and_does_not_claim_finality` |
| Direct/adapted receipts, errors, journal/state parity | Not covered | New adapter differential tests needed |
| Missing claims, identity/envelope validation, source faults | Not covered | New source/adapter tests needed |
| Detachment, exactly one read, at most one offer | Partially covered | Existing `test_returned_data_isolation.py`; source boundary missing |
| Unchanged replay, changed snapshot conflicts, no refresh | Partially covered | `test_credit_properties.py::MachinePropertyTests.test_the_face_snapshot_stays_frozen_after_later_settlement_changes`; adapter replay missing |
| Refund rejection, shared capacity, FACE_SNAPSHOT_FROZEN | Sufficiently covered for FSM | `test_credit_fsm.py::CreditFsmTests.test_refund_freeze_and_bad_inputs_follow_the_wave5_predicate`, `test_limit_race_is_ordered_and_cash_is_not_capacity`; adapter forwarding missing |
| False funds/authority/durability flags and open terms | Sufficiently covered for FSM | `test_credit_fsm.py::assert_not_lending`, `test_open_terms.py`; reuse assertions on adapted receipts |
| Runnable example, discovery/docs/architecture checks | Partially covered | Existing discovery includes this directory; new example and indexed evidence needed |

Existing clause maps: [credit](../../docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md)
and [settlement](../../docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md).

## Interface and errors

Use the repository's sibling-module import convention (add this directory to
`PYTHONPATH`, or run the example directly). All caller inputs are required:

```python
from settlement_claim_source import LocalSettlementClaimSource
from settlement_claim_adapter import SettlementClaimAdapter

adapter = SettlementClaimAdapter(credit, LocalSettlementClaimSource(settlement))
offered = adapter.offer(
    settlement_id="fixture-settlement", advance_id="fixture-advance",
    idempotency_key="fixture-offer", amount=40_000,
    beneficiary_role="fixture-beneficiary",
)
```

`SettlementClaimSource.fetch(settlement_id)` returns a settlement **view** dict or
`None`, never a receipt wrapper. `LocalSettlementClaimSource` calls injected
`view` once and deep-copies its result, without importing settlement code.
Actual view exceptions (including UNKNOWN_SETTLEMENT) propagate unchanged.
`FakeSettlementClaimSource(recordings=...)` accepts string IDs mapped to immutable
JSON strings or `SyntheticSettlementClaimFault.ERROR/TIMEOUT`. Its read-only
recordings and tuple call snapshots are deterministic; faults raise immediately,
without retries, clocks or consumption.

The adapter requires `settlement_id`, `provenance`, `lifecycle_authority`, `claim`
and literal False flags: `provider_authorization_executed`, `legal_debtor_bound`,
`admission_granted`, `right_cancelled`, `bank_debit_observed`,
`external_return_closed`, `funds_executed`, `durable`. Identity must match the
explicit string selector; provenance is `MOCK_SETTLEMENT_ONLY` and authority is
`IN_MEMORY_FSM`. A present claim must be a dict with matching string `claim_id`.
Extra view fields are allowed. No COMMITTED requirement is imposed at offer.

Local exceptions inherit `SettlementClaimSourceError`: `SettlementClaimNotFound`
for absent record/claim, `InvalidSettlementClaimRecord` for malformed envelopes,
and `SettlementClaimIdentityMismatch` for identity mismatches. They are internal
diagnostics, not catalogue codes. Failures before offer cannot bind a credit key.
The entire claim is deep-copied, retaining extra fields and original values.
Claim provenance, flags, arithmetic, amount and beneficiary validation remain in
the existing offer; its receipt and exceptions pass through unchanged.

Each replay reads again. A changed claim under an accepted key gives the existing
`IDEMPOTENCY_CONFLICT`; a new key for that advance gives
`ADVANCE_BINDING_CONFLICT`. Returning to the original snapshot replays the first
receipt even after later transitions. No caching or existing-face update occurs.
The first accepted draw freezes the shared face; capacity and
`FACE_SNAPSHOT_FROZEN` remain draw-time checks. Binding a settlement, approval and
draw are separate caller actions; a bound draw still requires COMMITTED.

## Example and verification

`example_settlement_claim_adapter.py::run_example(policy=..., amount=...,
beneficiary_role=...)` requires explicit synthetic fixture inputs. It uses the
existing statement adapter and actual settlement/credit machines. The command
below supplies labeled fixture values, commits a synthetic statement, offers with
zero exposure, then explicitly binds, approves and draws. There is no automatic
distribution or finance session/CLI.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 reference/credit_advance_f04/example_settlement_claim_adapter.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p 'test_settlement_claim*.py'
```

Actual full verification commands/results and remaining gates are in the
[builder validation record](../../validation/2026-11-04-plan-local-settlement-credit-face-adapter/README.md).

## Unresolved terms and limits

Product terms remain **UNDETERMINED — Astra/User**. Legal parties, accounting and
collateral effects remain **UNDETERMINED — designated external owners** (see the
contracts' named ownership routes). Fixture integers/roles decide no policy.
Mock provenance and false flags do not authenticate a source or grant authority.
No funds, bank/PG/KYC calls, persistence, sockets, external services, new protocol
commands, runtime activation, legal effect, finality or production readiness is
implemented or established. Evidence is source-informed builder testing, not
independent review. Non-author exact-head A2 review and required KTX/KIX CI remain
separate merge gates.
