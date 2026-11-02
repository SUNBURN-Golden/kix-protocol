"""Fetch once, validate local input, then delegate only list_resale to the FSM.

Ownership, version currency, price policy, clock/expiry, admission and listing
locks, and first-result semantics remain exclusively with ResaleMachine.
"""

from mock_gates import GateError, _ident, _money, _ms, _version
from resale_fsm import ResaleMachine
from resale_offer_source import (
    InvalidResaleOfferRecord,
    ResaleOfferNotFound,
    ResaleOfferRecord,
    ResaleOfferSource,
    ResaleOfferSourceError,
)


class ResaleOfferAdapter:
    def __init__(self, machine: ResaleMachine, source: ResaleOfferSource) -> None:
        self._machine = machine
        self._source = source

    def list_resale(self, offer_id: str, *, listing_id: str, idempotency_key: str) -> dict:
        # Each explicit invocation fetches, including replay and invalid callers.
        # Catch only fetch failures: FSM exceptions must propagate unchanged.
        try:
            record = self._source.fetch(offer_id)
        except ResaleOfferSourceError:
            raise
        except Exception as error:
            raise ResaleOfferSourceError("resale offer fetch failed") from error
        if record is None:
            raise ResaleOfferNotFound(offer_id)
        required = ResaleOfferRecord.__required_keys__
        allowed = required | ResaleOfferRecord.__optional_keys__
        if type(record) is not dict or not required <= record.keys() <= allowed:
            raise InvalidResaleOfferRecord("offer must contain exactly the listing input fields")
        # Detach validated scalar inputs from the source's dictionary.
        record = dict(record)
        try:
            for value in (offer_id, listing_id, idempotency_key, record["offer_id"],
                          record["right_id"], record["seller_role"], record["recipient_role"]):
                _ident(value)
            _version(record["version"])
            _money(record["amount"])
            _ms(record["expires_ms"], "LISTING_WINDOW")
            reservation = record.get("reservation_id")
            if reservation is not None:
                _ident(reservation)
        except GateError as error:
            raise InvalidResaleOfferRecord(error.code) from error
        if record.pop("offer_id") != offer_id:
            raise InvalidResaleOfferRecord("offer_id does not match requested identity")
        record["reservation_id"] = reservation
        return self._machine.list_resale(listing_id, idempotency_key=idempotency_key, **record)
