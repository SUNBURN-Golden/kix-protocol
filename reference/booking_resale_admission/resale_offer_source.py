"""Local synthetic listing inputs, never ownership or marketplace authority."""

from typing import NotRequired, Protocol, TypedDict


class ResaleOfferRecord(TypedDict):
    offer_id: str
    right_id: str
    version: int
    seller_role: str
    recipient_role: str
    amount: int
    expires_ms: int
    reservation_id: NotRequired[str | None]


class ResaleOfferSource(Protocol):
    def fetch(self, offer_id: str) -> dict | None:
        """Return one synthetic offer or absence, without FSM effects."""
        ...


class ResaleOfferSourceError(Exception):
    """Local input failure, with no protocol code or lifecycle meaning."""


class ResaleOfferNotFound(ResaleOfferSourceError):
    """The selected synthetic offer is absent."""


class InvalidResaleOfferRecord(ResaleOfferSourceError):
    """Malformed recording or caller identity; refused before FSM access."""
