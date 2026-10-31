# Local F04 repayment input adapter

This internal, standard-library-only adapter connects caller-selected synthetic
notes to the existing `CreditMachine.repay`. The authority remains
[`CREDIT_ADVANCE_F04.md` §§7.2–7.5](../../docs/contracts/CREDIT_ADVANCE_F04.md).
It follows the existing settlement statement-source adapter pattern.

`RepaymentSource.fetch(advance_id, repay_id)` returns one dict or `None`.
`RepaymentAdapter(machine, source).apply(advance_id=..., repay_id=...,
idempotency_key=...)` fetches exactly once per invocation, including duplicates.
It requires an exact dict with exactly `advance_id`, `repay_id`, `sequence`,
`amount`, and string identities matching the request. It passes sequence, amount
and the caller key unchanged to `repay`, returning its response directly and
propagating its exception unchanged. It invokes no other FSM command.

Missing notes raise `RepaymentNotFound`; malformed shape/text raises
`InvalidRepaymentRecord`; wrong or non-string identities raise
`RepaymentIdentityMismatch`. These derive from local `RepaymentSourceError`,
not protocol error codes. Invalid numeric values in a structurally valid note
reach the FSM, which retains all amount, order, idempotency and journal semantics.
Source failures make zero FSM calls and leave the caller key available. FSM
rejections may retain the key; recovery must respect existing FSM behavior.

`FakeRepaymentSource(recordings=...)` copies a mapping from identity pairs to
JSON text or `SyntheticRepaymentFault.ERROR/TIMEOUT`. Its public recordings are
read-only, each fetch decodes a fresh document, and `calls` returns immutable
tuple snapshots. Fetches do not consume recordings; faults raise immediately.

## Coverage inventory before adding adapter tests

Paths below are within this directory. Existing coverage is source-informed,
builder-authored evidence, not independent review.

| Requirement | Pre-change status | Existing coverage / gap |
|---|---|---|
| Partial, ordered repayment; duplicate and changed note binding | Sufficient for direct FSM; absent through adapter | `test_credit_fsm.py::CreditFsmTests.test_repayment_order_partial_and_double_application`, `test_same_draw_and_repay_notes_do_not_apply_twice` |
| Exposure decreases; reservation remains until explicit zero-exposure close | Sufficient for direct FSM; absent through adapter | `test_offer_approve_draw_repay_and_close_are_mock_ledger_only`, `test_close_rejects_remaining_exposure_before_release` in `test_credit_fsm.py` |
| Caller rejection atomicity and retained rejected keys | Sufficient for direct FSM; adapter integration partial | `test_credit_rejection_atomicity.py` tests `test_repay_sequence_gap_leaves_no_trace`, `test_repay_binding_conflict_leaves_no_trace`, `test_repay_exceeds_outstanding_leaves_no_trace`, `test_restore_forgets_stored_rejections` |
| Journal replay and detached results | Sufficient for direct FSM; adapter integration partial | `test_credit_fsm.py::CreditFsmTests.test_reconcile_replays_the_journal_without_a_second_draw`, `test_credit_properties.py` prefix restore, `test_returned_data_isolation.py` |
| One fetch, exact forwarding, result/error identity and source failure fencing | Not covered | New `test_repayment_adapter.py` |
| Recording, decoded result and call snapshot isolation | Not covered | New `test_repayment_source.py` |

## Example and local verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reference/credit_advance_f04/example_repayment_adapter.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04 -p 'test_repayment*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04
```

The example's `run_example(*, policy)` requires caller-supplied settlement fixture
policy. Script values are explicitly synthetic, not adopted product policy.
Actual local settlement and credit machines perform explicit initiate, authorize,
capture, statement-adapter commit, offer, approve, bind and draw. Three selected
notes reduce exposure `80000 → 50000 → 30000 → 0`; reservation stays `80000`.
A separate explicit `close` then releases it. Receipts, both journals, unchanged
settlement snapshots and source calls are returned for inspection.

## Boundary and non-claims

No sockets, services, funds, credentials, persistence, retries, fallback, derived
sequences, schedules or automatic close. This is a callable input adapter, not
the parked finance session/CLI workbench or pending reconciliation projection.
No new protocol command, catalogue change, FSM semantic change or runtime activation.
`MOCK_CREDIT_F04_ONLY`, `MOCK_SETTLEMENT_ONLY`, `repayment_observed=false` and
`funds_executed=false` remain in force. Synthetic notes are not bank receipts.

APR, fees, schedules, priority and limit policy remain **UNDETERMINED — Astra**.
Legal parties and collateral effectiveness remain **UNDETERMINED — User/I10 legal
owners**. No lending, legal compliance, bank exactly-once, production durability
or chain finality is established. Existing internal-fault characterizations do not
establish general rollback. F04/E06 status and open terms remain unchanged.

Actual builder commands, preservation checks and pending review/CI gates are in
the [validation record](../../validation/2026-10-31-plan-local-credit-repayment-source/README.md).
