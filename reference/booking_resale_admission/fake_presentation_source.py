"""Immutable JSON recordings with immediate synthetic faults; no I/O or retry."""

import json
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType

from presentation_source import (
    InvalidPresentationRecord,
    PresentationOperation,
    PresentationSourceError,
)


class SyntheticPresentationFault(Enum):
    ERROR = "synthetic_presentation_error"
    TIMEOUT = "synthetic_presentation_timeout"


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidPresentationRecord("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(_value: str) -> None:
    raise InvalidPresentationRecord("recording must use JSON values")


class FakePresentationSource:
    def __init__(
        self, *, recordings: Mapping[tuple[str, str], str | SyntheticPresentationFault],
    ) -> None:
        copied = dict(recordings)
        for identity, recording in copied.items():
            if (type(identity) is not tuple or len(identity) != 2
                    or any(type(part) is not str for part in identity)
                    or identity[0] not in ("authorize_admission", "consume")):
                raise TypeError("recording keys must be (operation, presentation_id) strings")
            if type(recording) not in (str, SyntheticPresentationFault):
                raise TypeError("recordings must be JSON text or SyntheticPresentationFault")
        self._recordings = MappingProxyType(copied)
        self._calls: list[tuple[str, str]] = []

    @property
    def recordings(self) -> Mapping[tuple[str, str], str | SyntheticPresentationFault]:
        return self._recordings

    @property
    def calls(self) -> tuple[tuple[str, str], ...]:
        return tuple(self._calls)

    def fetch(self, presentation_id: str, *, operation: PresentationOperation) -> dict | None:
        self._calls.append((operation, presentation_id))
        recording = self._recordings.get((operation, presentation_id))
        if recording is None:
            return None
        if isinstance(recording, SyntheticPresentationFault):
            raise PresentationSourceError(recording.value)
        try:
            record = json.loads(
                recording, object_pairs_hook=_object, parse_constant=_invalid_constant,
            )
        except (ValueError, RecursionError) as error:
            raise InvalidPresentationRecord("recording must be JSON text") from error
        if type(record) is not dict:
            raise InvalidPresentationRecord("recording must be a JSON object")
        return record
