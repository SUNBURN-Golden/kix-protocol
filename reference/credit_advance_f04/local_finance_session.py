"""Explicit local composition of the existing synthetic settlement and credit FSMs.

No persistence, retries, replacement keys, economic calculations or implicit
transitions. Receipts, views and domain exceptions belong to the machines.
"""

import inspect
import sys
from pathlib import Path

_SETTLEMENT = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT))

from credit_fsm import CreditMachine
from fake_statement_source import FakeStatementSource
from settlement_fsm import SettlementMachine
from statement_adapter import StatementAdapter


# Unbound methods form an explicit allowlist, shared with fixture validation.
SETTLEMENT_OPERATIONS = {
    "initiate": SettlementMachine.initiate,
    "authorize": SettlementMachine.authorize,
    "capture": SettlementMachine.capture,
    "distribute": SettlementMachine.distribute,
    "bind_refund": SettlementMachine.bind_refund,
    "observe_mock_cancel_acceptance": SettlementMachine.observe_mock_cancel_acceptance,
    "fail": SettlementMachine.fail,
    "cancel": SettlementMachine.cancel,
    "reconcile": SettlementMachine.reconcile,
}
CREDIT_OPERATIONS = {
    "offer": CreditMachine.offer,
    "bind_settlement": CreditMachine.bind_settlement,
    "approve": CreditMachine.approve,
    "reject": CreditMachine.reject,
    "cancel": CreditMachine.cancel,
    "draw": CreditMachine.draw,
    "repay": CreditMachine.repay,
    "close": CreditMachine.close,
    "default": CreditMachine.default,
    "reconcile": CreditMachine.reconcile,
}
STATEMENT_OPERATIONS = frozenset({"commit", "observe_statement"})


def _statement_arguments(self, settlement_id, *, idempotency_key, movement_id):
    """Signature only: statement components must come from the source."""


def operation_method(target, operation):
    """Select only supported calls; never look up an arbitrary attribute."""
    if type(operation) is not str:
        raise ValueError("unsupported operation")
    if target == "settlement":
        if operation in STATEMENT_OPERATIONS:
            return _statement_arguments
        table = SETTLEMENT_OPERATIONS
    elif target == "credit":
        table = CREDIT_OPERATIONS
    else:
        raise ValueError("unsupported target")
    if type(operation) is not str or operation not in table:
        raise ValueError("unsupported operation")
    return table[operation]


class LocalFinanceSession:
    def __init__(self, *, recordings):
        """Recordings use FakeStatementSource's (ID, movement) -> JSON/fault map."""
        self.settlement_machine = SettlementMachine()
        self.statement_source = FakeStatementSource(recordings=recordings)
        self.statement_adapter = StatementAdapter(self.settlement_machine, self.statement_source)
        self.credit_machine = CreditMachine(settlement_source=self.settlement_machine)

    def settlement(self, operation, settlement_id, *, idempotency_key, **body):
        method = operation_method("settlement", operation)
        # Reject malformed signatures before an adapter fetch or FSM dispatch.
        inspect.signature(method).bind(
            self.settlement_machine, settlement_id, idempotency_key=idempotency_key, **body,
        )
        if operation in STATEMENT_OPERATIONS:
            return self.statement_adapter.apply(
                operation=operation, settlement_id=settlement_id,
                idempotency_key=idempotency_key, **body,
            )
        return method(self.settlement_machine, settlement_id, idempotency_key=idempotency_key, **body)

    def credit(self, operation, advance_id, *, idempotency_key, **body):
        method = operation_method("credit", operation)
        return method(self.credit_machine, advance_id, idempotency_key=idempotency_key, **body)

    def settlement_view(self, settlement_id):
        return self.settlement_machine.view(settlement_id)

    def credit_view(self, advance_id):
        return self.credit_machine.view(advance_id)

    def credit_claim_view(self, claim_id):
        return self.credit_machine.view_claim(claim_id)
