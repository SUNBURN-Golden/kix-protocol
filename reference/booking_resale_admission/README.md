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
