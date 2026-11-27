"""Immutable JSON recordings and immediate synthetic faults; no I/O or retry."""

import json
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType

from resale_offer_source import InvalidResaleOfferRecord, ResaleOfferSourceError


class SyntheticResaleOfferFault(Enum):
    ERROR = "synthetic_resale_offer_error"
    TIMEOUT = "synthetic_resale_offer_timeout"


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidResaleOfferRecord("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(_value: str) -> None:
    raise InvalidResaleOfferRecord("recording must use JSON values")


class FakeResaleOfferSource:
    def __init__(
        self, *, recordings: Mapping[str, str | SyntheticResaleOfferFault],
    ) -> None:
        copied = dict(recordings)
        for identity, recording in copied.items():
            if type(identity) is not str:
                raise TypeError("recording keys must be offer_id strings")
            if type(recording) not in (str, SyntheticResaleOfferFault):
                raise TypeError("recordings must be JSON text or SyntheticResaleOfferFault")
        self._recordings = MappingProxyType(copied)
        self._calls: list[str] = []

    @property
    def recordings(self) -> Mapping[str, str | SyntheticResaleOfferFault]:
        return self._recordings

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch(self, offer_id: str) -> dict | None:
        self._calls.append(offer_id)
        recording = self._recordings.get(offer_id)
        if recording is None:
            return None
        if isinstance(recording, SyntheticResaleOfferFault):
            raise ResaleOfferSourceError(recording.value)
        try:
            record = json.loads(
                recording, object_pairs_hook=_object, parse_constant=_invalid_constant,
            )
        except (ValueError, RecursionError) as error:
            raise InvalidResaleOfferRecord("recording must be JSON text") from error
        if type(record) is not dict:
            raise InvalidResaleOfferRecord("recording must be a JSON object")
        return record
