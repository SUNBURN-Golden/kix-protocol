"""Internal synthetic command inputs, never identity or currentness authority."""

from typing import Literal, Protocol, TypedDict

PresentationOperation = Literal["authorize_admission", "consume"]


class AuthorizePresentationInput(TypedDict):
    right_id: str
    version: int
    holder_role: str
    request: str


class ConsumePresentationInput(TypedDict):
    right_id: str
    version: int
    request: str


class PresentationSource(Protocol):
    def fetch(self, presentation_id: str, *, operation: PresentationOperation) -> dict | None:
        """Return one synthetic command input or absence, with no FSM effects."""
        ...


class PresentationSourceError(Exception):
    """Local input failure; no protocol error code or lifecycle meaning."""


class PresentationNotFound(PresentationSourceError):
    """The selected synthetic recording is absent."""


class InvalidPresentationRecord(PresentationSourceError):
    """Malformed recording or caller argument; rejected before FSM access."""
