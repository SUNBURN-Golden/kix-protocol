"""Caller-selected dispatch to the unchanged local credit repayment FSM."""

from credit_fsm import CreditMachine
from repayment_source import (
    InvalidRepaymentRecord,
    RepaymentIdentityMismatch,
    RepaymentNotFound,
    RepaymentRecord,
    RepaymentSource,
)


class RepaymentAdapter:
    def __init__(self, machine: CreditMachine, source: RepaymentSource) -> None:
        self._machine = machine
        self._source = source

    def apply(self, *, advance_id: str, repay_id: str, idempotency_key: str) -> dict:
        record = self._source.fetch(advance_id, repay_id)
        if record is None:
            raise RepaymentNotFound((advance_id, repay_id))
        if type(record) is not dict or set(record) != RepaymentRecord.__required_keys__:
            raise InvalidRepaymentRecord("repayment must contain exactly the existing FSM fields")
        if (type(record["advance_id"]) is not str
                or type(record["repay_id"]) is not str
                or record["advance_id"] != advance_id
                or record["repay_id"] != repay_id):
            raise RepaymentIdentityMismatch((advance_id, repay_id))
        return self._machine.repay(
            advance_id, idempotency_key=idempotency_key,
            repay_id=record["repay_id"], sequence=record["sequence"], amount=record["amount"],
        )
