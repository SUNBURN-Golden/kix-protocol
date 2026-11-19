"""Immutable synthetic JSON recordings; no clocks, retry, I/O or consumption."""

import json
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType

from settlement_claim_source import InvalidSettlementClaimRecord, SettlementClaimSourceError


class SyntheticSettlementClaimFault(Enum):
    ERROR = "synthetic_settlement_claim_error"
    TIMEOUT = "synthetic_settlement_claim_timeout"


class FakeSettlementClaimSource:
    def __init__(
        self, *, recordings: Mapping[str, str | SyntheticSettlementClaimFault],
    ) -> None:
        copied = dict(recordings)
        for identity, recording in copied.items():
            if type(identity) is not str:
                raise TypeError("recording keys must be settlement_id strings")
            if type(recording) not in (str, SyntheticSettlementClaimFault):
                raise TypeError("recordings must be JSON text or SyntheticSettlementClaimFault")
        self._recordings = MappingProxyType(copied)
        self._calls: list[str] = []

    @property
    def recordings(self) -> Mapping[str, str | SyntheticSettlementClaimFault]:
        return self._recordings

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch(self, settlement_id: str) -> dict | None:
        self._calls.append(settlement_id)
        recording = self._recordings.get(settlement_id)
        if recording is None:
            return None
        if isinstance(recording, SyntheticSettlementClaimFault):
            raise SettlementClaimSourceError(recording.value)
        try:
            record = json.loads(recording)
        except json.JSONDecodeError as error:
            raise InvalidSettlementClaimRecord("recording must be JSON text") from error
        if type(record) is not dict:
            raise InvalidSettlementClaimRecord("recording must be a JSON object")
        return record
