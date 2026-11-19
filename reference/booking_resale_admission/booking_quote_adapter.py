"""Validate a selected synthetic record, then delegate once to BookingSession.

No quote generation, price calculation, state inspection, caching or fallback.
Session prerequisites and FSM pricing, expiry, binding and replay remain authoritative.
"""

from booking_quote_source import (
    BookingQuoteNotFound, BookingQuoteRecord, BookingQuoteSource, BookingQuoteSourceError,
    InvalidBookingQuoteRecord,
)
from booking_session import BookingSession
from mock_gates import GateError, _ident, _money


class BookingQuoteAdapter:
    def __init__(self, session: BookingSession, source: BookingQuoteSource) -> None:
        self._session = session
        self._source = source

    def confirm_recorded_quote(self, recording_id: str, *, reservation_id: str,
                               order_id: str, idempotency_key: str) -> dict:
        try:
            for value in (recording_id, reservation_id, order_id, idempotency_key):
                _ident(value)
        except GateError as error:
            raise InvalidBookingQuoteRecord(error.code) from error
        # Fetch on every explicit valid invocation, even replay. Catch only source
        # failures so that session and FSM exceptions retain their identity.
        try:
            record = self._source.fetch(recording_id)
        except BookingQuoteSourceError:
            raise
        except Exception as error:
            raise BookingQuoteSourceError("booking quote fetch failed") from error
        if record is None:
            raise BookingQuoteNotFound(recording_id)
        if type(record) is not dict or set(record) != BookingQuoteRecord.__required_keys__:
            raise InvalidBookingQuoteRecord("quote requires exactly reservation_id, amount, quote_ref")
        record = dict(record)
        try:
            _ident(record["reservation_id"])
            _ident(record["quote_ref"])
            _money(record["amount"])
        except GateError as error:
            raise InvalidBookingQuoteRecord(error.code) from error
        if record["reservation_id"] != reservation_id:
            raise InvalidBookingQuoteRecord("reservation_id does not match expected reservation")
        return self._session.confirm(order_id, idempotency_key=idempotency_key, **record)
