"""Runnable synthetic repayment journey; all caller actions are explicit."""

import json
from pathlib import Path
import sys

_SETTLEMENT = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT))

from credit_fsm import CreditMachine  # noqa: E402
from fake_repayment_source import FakeRepaymentSource  # noqa: E402
from fake_statement_source import FakeStatementSource  # noqa: E402
from repayment_adapter import RepaymentAdapter  # noqa: E402
from settlement_fsm import SettlementMachine  # noqa: E402
from statement_adapter import StatementAdapter  # noqa: E402


def run_example(*, policy: dict) -> dict:
    """The caller supplies settlement fixture policy, never credit policy."""
    settlement = SettlementMachine()
    sid, aid = "fixture-settlement", "fixture-advance"
    statement_source = FakeStatementSource(recordings={
        (sid, "fixture-statement"): json.dumps(dict(
            settlement_id=sid, movement_id="fixture-statement", gross=100_000,
            amount=97_000, fee=3_000, tax=0, held=0, adjustment=0,
            adjustment_reason=None,
        )),
    })
    initiated = settlement.initiate(
        sid, idempotency_key="fixture-initiate", trade_id="fixture-trade",
        gross=100_000, debtor_role="fixture-merchant", policy=policy,
    )
    authorized = settlement.authorize(sid, idempotency_key="fixture-authorize")
    captured = settlement.capture(sid, idempotency_key="fixture-capture")
    committed = StatementAdapter(settlement, statement_source).apply(
        operation="commit", settlement_id=sid, movement_id="fixture-statement",
        idempotency_key="fixture-commit",
    )
    settlement_before = settlement.canonical_state()
    settlement_journal_before = settlement.export_journal()
    machine = CreditMachine(settlement)
    offered = machine.offer(
        aid, idempotency_key="fixture-offer", face=settlement.view(sid)["claim"],
        amount=80_000, beneficiary_role="fixture-beneficiary",
    )
    approved = machine.approve(aid, idempotency_key="fixture-approve")
    bound = machine.bind_settlement(aid, idempotency_key="fixture-bind", settlement_id=sid)
    drawn = machine.draw(aid, idempotency_key="fixture-draw", draw_id="fixture-draw")
    source = FakeRepaymentSource(recordings={
        (aid, "fixture-note-1"): json.dumps(dict(
            advance_id=aid, repay_id="fixture-note-1", sequence=1, amount=30_000)),
        (aid, "fixture-note-2"): json.dumps(dict(
            advance_id=aid, repay_id="fixture-note-2", sequence=2, amount=20_000)),
        (aid, "fixture-note-3"): json.dumps(dict(
            advance_id=aid, repay_id="fixture-note-3", sequence=3, amount=30_000)),
    })
    adapter = RepaymentAdapter(machine, source)
    partial = adapter.apply(advance_id=aid, repay_id="fixture-note-1",
                            idempotency_key="fixture-repay-1")
    second = adapter.apply(advance_id=aid, repay_id="fixture-note-2",
                           idempotency_key="fixture-repay-2")
    paid = adapter.apply(advance_id=aid, repay_id="fixture-note-3",
                         idempotency_key="fixture-repay-3")
    before_close = machine.view(aid)
    assert before_close["phase"] == "DRAWN"
    assert before_close["reserved_open"] == 80_000
    assert before_close["outstanding_exposure"] == 0

    # Separate explicit caller action, never chosen by the repayment adapter.
    closed = machine.close(aid, idempotency_key="fixture-close")
    assert settlement.canonical_state() == settlement_before
    assert settlement.export_journal() == settlement_journal_before
    return dict(
        provenance="MOCK_CREDIT_F04_ONLY", settlement_provenance="MOCK_SETTLEMENT_ONLY",
        fixture_policy_only=True, repayment_observed=False, funds_executed=False,
        durable=False, chain_finality=False,
        settlement_receipts=[initiated, authorized, captured, committed],
        offered=offered, approved=approved, bound=bound, drawn=drawn,
        repayments=[partial, second, paid], before_close=before_close, closed=closed,
        settlement_before=settlement_before, settlement_after=settlement.canonical_state(),
        settlement_journal_before=settlement_journal_before,
        settlement_journal=settlement.export_journal(), credit_journal=machine.export_journal(),
        statement_source_calls=statement_source.calls, repayment_source_calls=source.calls,
    )


if __name__ == "__main__":
    # Synthetic settlement fixture values only; no APR, fee schedule or credit policy.
    print(json.dumps(run_example(policy=dict(
        kind="PRIMARY_FEE_BPS", fee_bps=500,
        residual_payee="fixture-organizer", fee_payee="fixture-platform",
    )), indent=2, sort_keys=True))
