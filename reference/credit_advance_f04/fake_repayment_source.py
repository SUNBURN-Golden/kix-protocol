"""Immutable local JSON recordings. No clocks, I/O, retry or consumption."""

import json
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType

from repayment_source import InvalidRepaymentRecord, RepaymentSourceError


class SyntheticRepaymentFault(Enum):
    ERROR = "synthetic_repayment_error"
    TIMEOUT = "synthetic_repayment_timeout"


class FakeRepaymentSource:
    def __init__(
        self, *, recordings: Mapping[tuple[str, str], str | SyntheticRepaymentFault],
    ) -> None:
        copied = dict(recordings)
        for identity, recording in copied.items():
            if (type(identity) is not tuple or len(identity) != 2
                    or any(type(part) is not str for part in identity)):
                raise TypeError("recording keys must be (advance_id, repay_id) strings")
            if type(recording) not in (str, SyntheticRepaymentFault):
                raise TypeError("recordings must be JSON text or SyntheticRepaymentFault")
        self._recordings = MappingProxyType(copied)
        self._calls: list[tuple[str, str]] = []

    @property
    def recordings(self) -> Mapping[tuple[str, str], str | SyntheticRepaymentFault]:
        return self._recordings

    @property
    def calls(self) -> tuple[tuple[str, str], ...]:
        return tuple(self._calls)

    def fetch(self, advance_id: str, repay_id: str) -> dict | None:
        self._calls.append((advance_id, repay_id))
        recording = self._recordings.get((advance_id, repay_id))
        if recording is None:
            return None
        if isinstance(recording, SyntheticRepaymentFault):
            raise RepaymentSourceError(recording.value)
        try:
            record = json.loads(recording)
        except json.JSONDecodeError as error:
            raise InvalidRepaymentRecord("recording must be JSON text") from error
        if type(record) is not dict:
            raise InvalidRepaymentRecord("recording must be a JSON object")
        return record
