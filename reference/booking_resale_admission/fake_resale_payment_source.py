"""Immutable JSON recordings and immediate synthetic faults; no I/O or retry."""

import json
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType

from resale_payment_source import InvalidResalePaymentRecord, ResalePaymentSourceError


class SyntheticResalePaymentFault(Enum):
    ERROR = "synthetic_resale_payment_error"
    TIMEOUT = "synthetic_resale_payment_timeout"


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidResalePaymentRecord("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(_value: str) -> None:
    raise InvalidResalePaymentRecord("recording must use JSON values")


class FakeResalePaymentSource:
    def __init__(
        self, *, recordings: Mapping[str, str | SyntheticResalePaymentFault],
    ) -> None:
        copied = dict(recordings)
        for identity, recording in copied.items():
            if type(identity) is not str:
                raise TypeError("recording keys must be recording_id strings")
            if type(recording) not in (str, SyntheticResalePaymentFault):
                raise TypeError("recordings must be JSON text or SyntheticResalePaymentFault")
        self._recordings = MappingProxyType(copied)
        self._calls: list[str] = []

    @property
    def recordings(self) -> Mapping[str, str | SyntheticResalePaymentFault]:
        return self._recordings

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch(self, recording_id: str) -> dict | None:
        self._calls.append(recording_id)
        recording = self._recordings.get(recording_id)
        if recording is None:
            return None
        if isinstance(recording, SyntheticResalePaymentFault):
            raise ResalePaymentSourceError(recording.value)
        try:
            record = json.loads(
                recording, object_pairs_hook=_object, parse_constant=_invalid_constant,
            )
        except (ValueError, RecursionError) as error:
            raise InvalidResalePaymentRecord("recording must be JSON text") from error
        if type(record) is not dict:
            raise InvalidResalePaymentRecord("recording must be a JSON object")
        return record
