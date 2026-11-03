"""Internal offline settlement-view source; no concrete settlement imports."""

from copy import deepcopy
from typing import Protocol


class SettlementViewSource(Protocol):
    def view(self, settlement_id: str) -> dict:
        ...


class SettlementClaimSource(Protocol):
    def fetch(self, settlement_id: str) -> dict | None:
        """Read one selected synthetic view, or return absence."""
        ...


class SettlementClaimSourceError(Exception):
    """Internal source diagnostic, with no external funds/absence meaning."""


class SettlementClaimNotFound(SettlementClaimSourceError):
    """The selected view or its claim is absent."""


class InvalidSettlementClaimRecord(SettlementClaimSourceError):
    """Malformed synthetic view envelope or recording."""


class SettlementClaimIdentityMismatch(SettlementClaimSourceError):
    """The returned view or claim belongs to another settlement."""


class LocalSettlementClaimSource:
    def __init__(self, machine: SettlementViewSource) -> None:
        self._machine = machine

    def fetch(self, settlement_id: str) -> dict | None:
        # Preserve source exceptions. Absence is never inferred from a fault.
        return deepcopy(self._machine.view(settlement_id))
