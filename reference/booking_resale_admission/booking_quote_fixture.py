"""Strict source-only fixture loader; no FSM construction, setup or clock defaults."""

from pathlib import Path

from admission_fixture import FixtureError, decode_json, exact_fields
from fake_booking_quote_source import FakeBookingQuoteSource, SyntheticBookingQuoteFault
from mock_gates import GateError, _ident


def load_fixture(path: str | Path) -> FakeBookingQuoteSource:
    fixture = decode_json(Path(path).read_text(encoding="utf-8"))
    exact_fields(fixture, {"fixture_version", "provenance", "quotes"}, "quote fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != "MOCK_GATE_ONLY":
        raise FixtureError("fixture provenance must be MOCK_GATE_ONLY")
    if type(fixture["quotes"]) is not list:
        raise FixtureError("quotes must be an array")
    recordings = {}
    for entry in fixture["quotes"]:
        if type(entry) is not dict:
            raise FixtureError("quote must be an object")
        payload = set(entry) & {"recorded_text", "fault"}
        if len(payload) != 1:
            raise FixtureError("quote requires exactly one of recorded_text or fault")
        exact_fields(entry, {"recording_id"} | payload, "quote")
        try:
            identity = _ident(entry["recording_id"])
        except GateError as error:
            raise FixtureError(f"fixture identifier: {error.code}") from error
        if identity in recordings:
            raise FixtureError("duplicate recording_id")
        if "recorded_text" in payload:
            value = entry["recorded_text"]
            if type(value) is not str:
                raise FixtureError("recorded_text must be text")
        else:
            try:
                value = SyntheticBookingQuoteFault(entry["fault"])
            except (ValueError, TypeError) as error:
                raise FixtureError("unsupported synthetic booking quote fault") from error
        recordings[identity] = value
    return FakeBookingQuoteSource(recordings=recordings)
