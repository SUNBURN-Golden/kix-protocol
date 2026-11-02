"""Synthetic payment observations, never provider, funds or buyer authority."""

from typing import Protocol, TypedDict


class ResalePaymentRecord(TypedDict):
    listing_id: str
    payment_ref: str
    amount: int
    buyer_role: str


class ResalePaymentSource(Protocol):
    def fetch(self, recording_id: str) -> dict | None:
        """Return one selected synthetic recording or absence, without FSM effects."""
        ...


class ResalePaymentSourceError(Exception):
    """Local input failure without a protocol code or lifecycle meaning."""


class ResalePaymentNotFound(ResalePaymentSourceError):
    """The selected recording is absent."""


class InvalidResalePaymentRecord(ResalePaymentSourceError):
    """Malformed recording or caller identity, refused before FSM access."""
