"""One explicit settlement claim read, then at most one existing credit offer."""

from copy import deepcopy

from credit_fsm import CreditMachine
from settlement_claim_source import (
    InvalidSettlementClaimRecord,
    SettlementClaimIdentityMismatch,
    SettlementClaimNotFound,
    SettlementClaimSource,
)

_FALSE_FLAGS = (
    "provider_authorization_executed", "legal_debtor_bound", "admission_granted",
    "right_cancelled", "bank_debit_observed", "external_return_closed",
    "funds_executed", "durable",
)
_REQUIRED_FIELDS = frozenset(("settlement_id", "provenance", "lifecycle_authority", "claim"))


class SettlementClaimAdapter:
    def __init__(self, machine: CreditMachine, source: SettlementClaimSource) -> None:
        self._machine = machine
        self._source = source

    def offer(
        self, *, settlement_id: str, advance_id: object, idempotency_key: object,
        amount: object, beneficiary_role: object,
    ) -> dict:
        record = self._source.fetch(settlement_id)
        if record is None:
            raise SettlementClaimNotFound(settlement_id)
        if type(record) is not dict or not _REQUIRED_FIELDS.issubset(record):
            raise InvalidSettlementClaimRecord("source must return a settlement view")
        if (type(settlement_id) is not str
                or type(record["settlement_id"]) is not str
                or record["settlement_id"] != settlement_id):
            raise SettlementClaimIdentityMismatch(settlement_id)
        if (record["provenance"] != "MOCK_SETTLEMENT_ONLY"
                or record["lifecycle_authority"] != "IN_MEMORY_FSM"
                or any(record.get(flag) is not False for flag in _FALSE_FLAGS)):
            raise InvalidSettlementClaimRecord("source must retain mock provenance and false flags")
        claim = record["claim"]
        if claim is None:
            raise SettlementClaimNotFound(settlement_id)
        if type(claim) is not dict:
            raise InvalidSettlementClaimRecord("claim must be a dictionary")
        if type(claim.get("claim_id")) is not str or claim["claim_id"] != settlement_id:
            raise SettlementClaimIdentityMismatch(settlement_id)
        return self._machine.offer(
            advance_id, idempotency_key=idempotency_key, face=deepcopy(claim),
            amount=amount, beneficiary_role=beneficiary_role,
        )
