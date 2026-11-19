"""One synthetic fetch and shape/binding checks, then unchanged FSM delegation.

Buyer eligibility, amount equality, existence, expiry and first-result semantics
remain ResaleMachine decisions. No transfer or settlement request is generated.
"""

from mock_gates import GateError, _hex32, _ident, _money
from resale_fsm import ResaleMachine
from resale_payment_source import (
    InvalidResalePaymentRecord,
    ResalePaymentNotFound,
    ResalePaymentRecord,
    ResalePaymentSource,
    ResalePaymentSourceError,
)


class ResalePaymentAdapter:
    def __init__(self, machine: ResaleMachine, source: ResalePaymentSource) -> None:
        self._machine = machine
        self._source = source

    def observe_resale_payment(
        self, recording_id: str, *, listing_id: str, idempotency_key: str,
    ) -> dict:
        # Fetch even on replay/invalid caller input; catch only fetch exceptions.
        try:
            record = self._source.fetch(recording_id)
        except ResalePaymentSourceError:
            raise
        except Exception as error:
            raise ResalePaymentSourceError("resale payment fetch failed") from error
        if record is None:
            raise ResalePaymentNotFound(recording_id)
        if type(record) is not dict or record.keys() != ResalePaymentRecord.__required_keys__:
            raise InvalidResalePaymentRecord("payment must contain exactly the observation fields")
        record = dict(record)
        try:
            for value in (recording_id, listing_id, idempotency_key,
                          record["listing_id"], record["buyer_role"]):
                _ident(value)
            _money(record["amount"])
            _hex32(record["payment_ref"], "PAYMENT_REF")
        except GateError as error:
            raise InvalidResalePaymentRecord(error.code) from error
        if record["listing_id"] != listing_id:
            raise InvalidResalePaymentRecord("listing_id does not match requested listing")
        return self._machine.observe_resale_payment(
            listing_id, idempotency_key=idempotency_key,
            payment_ref=record["payment_ref"], amount=record["amount"],
            buyer_role=record["buyer_role"],
        )
