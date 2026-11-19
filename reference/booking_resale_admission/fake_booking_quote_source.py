"""Immutable JSON recordings and immediate synthetic faults; no I/O or retry."""

from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType

from admission_fixture import FixtureError, decode_json
from booking_quote_source import BookingQuoteSourceError, InvalidBookingQuoteRecord


class SyntheticBookingQuoteFault(Enum):
    ERROR = "synthetic_booking_quote_error"
    TIMEOUT = "synthetic_booking_quote_timeout"


class FakeBookingQuoteSource:
    def __init__(self, *, recordings: Mapping[str, str | SyntheticBookingQuoteFault]) -> None:
        copied = dict(recordings)
        for identity, recording in copied.items():
            if type(identity) is not str:
                raise TypeError("recording keys must be recording_id strings")
            if type(recording) not in (str, SyntheticBookingQuoteFault):
                raise TypeError("recordings must be JSON text or SyntheticBookingQuoteFault")
        self._recordings = MappingProxyType(copied)
        self._calls: list[str] = []

    @property
    def recordings(self) -> Mapping[str, str | SyntheticBookingQuoteFault]:
        return self._recordings

    @property
    def calls(self) -> tuple[str, ...]:
        return tuple(self._calls)

    def fetch(self, recording_id: str) -> dict | None:
        self._calls.append(recording_id)
        recording = self._recordings.get(recording_id)
        if recording is None:
            return None
        if isinstance(recording, SyntheticBookingQuoteFault):
            raise BookingQuoteSourceError(recording.value)
        try:
            record = decode_json(recording)
        except FixtureError as error:
            raise InvalidBookingQuoteRecord(str(error)) from error
        if type(record) is not dict:
            raise InvalidBookingQuoteRecord("recording must be a JSON object")
        return record
