"""Standard-library offline statement → settlement → credit fixture journey."""

import json
import sys
from pathlib import Path

from credit_fsm import CreditMachine
from settlement_claim_adapter import SettlementClaimAdapter
from settlement_claim_source import LocalSettlementClaimSource

_SETTLEMENT = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT))

from fake_statement_source import FakeStatementSource  # noqa: E402
from settlement_fsm import SettlementMachine  # noqa: E402
from statement_adapter import StatementAdapter  # noqa: E402


def run_example(*, policy: dict, amount: object, beneficiary_role: object) -> dict:
    """All product-like fixture inputs are explicit, with no policy defaults."""
    settlement = SettlementMachine()
    sid, aid = "fixture-settlement", "fixture-advance"
    statements = FakeStatementSource(recordings={
        (sid, "fixture-movement"): json.dumps(dict(
            settlement_id=sid, movement_id="fixture-movement", gross=100_000,
            amount=93_000, fee=2_000, tax=1_000, held=3_000, adjustment=1_000,
            adjustment_reason="fixture-adjustment",
        )),
    })
    settlement.initiate(
        sid, idempotency_key="fixture-initiate", trade_id="fixture-trade",
        gross=100_000, debtor_role="fixture-merchant", policy=policy,
    )
    settlement.authorize(sid, idempotency_key="fixture-authorize")
    settlement.capture(sid, idempotency_key="fixture-capture")
    committed = StatementAdapter(settlement, statements).apply(
        operation="commit", settlement_id=sid, movement_id="fixture-movement",
        idempotency_key="fixture-commit",
    )
    credit = CreditMachine(settlement)
    offered = SettlementClaimAdapter(credit, LocalSettlementClaimSource(settlement)).offer(
        settlement_id=sid, advance_id=aid, idempotency_key="fixture-offer",
        amount=amount, beneficiary_role=beneficiary_role,
    )
    assert offered["credit"]["phase"] == "OFFERED"
    assert offered["credit"]["drawn_exposure"] == 0
    # Separate, explicit caller actions. The adapter only offers.
    bound = credit.bind_settlement(aid, idempotency_key="fixture-bind", settlement_id=sid)
    approved = credit.approve(aid, idempotency_key="fixture-approve")
    drawn = credit.draw(aid, idempotency_key="fixture-draw", draw_id="fixture-draw-id")
    assert drawn["credit"]["settlement_gate"] == "MOCK_COMMIT_OBSERVED"
    assert settlement.view(sid)["claim"]["distributed_cash"] == 0
    return dict(
        provenance="MOCK_CREDIT_F04_ONLY", durable=False, funds_executed=False,
        chain_finality=False, committed=committed, offered=offered, bound=bound,
        approved=approved, drawn=drawn, settlement=settlement.view(sid),
        settlement_journal=settlement.export_journal(), credit_journal=credit.export_journal(),
        statement_calls=statements.calls,
    )


if __name__ == "__main__":
    print(json.dumps(run_example(
        policy=dict(kind="PRIMARY_FEE_BPS", fee_bps=500,
                    residual_payee="fixture-organizer", fee_payee="fixture-platform"),
        amount=40_000, beneficiary_role="fixture-beneficiary",
    ), indent=2, sort_keys=True))
