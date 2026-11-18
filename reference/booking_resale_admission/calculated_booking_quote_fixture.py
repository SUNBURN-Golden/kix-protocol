"""Strict source-only fixtures; loading never calculates, fetches or sets clocks."""

from pathlib import Path

from admission_fixture import FixtureError, decode_json, exact_fields
from calculated_booking_quote_source import CalculatedBookingQuoteSource
from mock_gates import GateError, _ident


def load_fixture(path: str | Path) -> CalculatedBookingQuoteSource:
    fixture = decode_json(Path(path).read_text(encoding="utf-8"))
    exact_fields(fixture, {"fixture_version", "provenance", "calculations"}, "calculation fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != "CALCULATION_ONLY":
        raise FixtureError("fixture provenance must be CALCULATION_ONLY")
    if type(fixture["calculations"]) is not list:
        raise FixtureError("calculations must be an array")
    requests = {}
    for entry in fixture["calculations"]:
        exact_fields(entry, {"recording_id", "reservation_id", "request_text"}, "calculation")
        try:
            identity = _ident(entry["recording_id"])
            _ident(entry["reservation_id"])
        except GateError as error:
            raise FixtureError(f"fixture identifier: {error.code}") from error
        if identity in requests:
            raise FixtureError("duplicate recording_id")
        if type(entry["request_text"]) is not str:
            raise FixtureError("request_text must be text")
        requests[identity] = {key: entry[key] for key in ("reservation_id", "request_text")}
    return CalculatedBookingQuoteSource(requests=requests)
