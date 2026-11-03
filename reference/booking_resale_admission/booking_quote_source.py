"""Caller-selected synthetic inputs, never authenticated quotes or price policy."""

from typing import Protocol, TypedDict


class BookingQuoteRecord(TypedDict):
    reservation_id: str
    amount: int
    quote_ref: str


class BookingQuoteSource(Protocol):
    def fetch(self, recording_id: str) -> dict | None:
        """Return one detached synthetic recording or absence, without FSM effects."""
        ...


class BookingQuoteSourceError(Exception):
    """Local input failure, without a protocol code or lifecycle meaning."""


class BookingQuoteNotFound(BookingQuoteSourceError):
    """The explicitly selected recording is absent."""


class InvalidBookingQuoteRecord(BookingQuoteSourceError):
    """Malformed caller/record input or reservation mismatch; no delegation."""
