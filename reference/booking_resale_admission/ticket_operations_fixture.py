"""Strict combined synthetic fixture; recordings are validated on explicit fetch."""

from pathlib import Path

from admission_fixture import FixtureError, _recordings as _presentations, decode_json, exact_fields
from fake_presentation_source import FakePresentationSource
from fake_resale_offer_source import FakeResaleOfferSource
from fake_resale_payment_source import FakeResalePaymentSource
from resale_fixture import _identifier, _payment_recordings, _recordings as _offers
from ticket_operations_session import TicketOperationsSession
from fake_cancel_acceptance_source import FakeCancelAcceptanceSource, SyntheticCancelAcceptanceFault
from fake_statement_source import FakeStatementSource, SyntheticStatementFault


def _statement_recordings(entries):
    if type(entries) is not list:
        raise FixtureError("statements must be an array")
    recordings = {}
    for entry in entries:
        if type(entry) is not dict:
            raise FixtureError("statement must be an object")
        payload = set(entry) & {"recorded_text", "fault"}
        if len(payload) != 1:
            raise FixtureError("statement requires exactly one of recorded_text or fault")
        exact_fields(entry, {"settlement_id", "movement_id"} | payload, "statement")
        identity = (_identifier(entry["settlement_id"]), _identifier(entry["movement_id"]))
        if identity in recordings:
            raise FixtureError("duplicate statement identity")
        if "recorded_text" in payload:
            value = entry["recorded_text"]
            if type(value) is not str:
                raise FixtureError("recorded_text must be text")
        else:
            try:
                value = SyntheticStatementFault(entry["fault"])
            except (ValueError, TypeError) as error:
                raise FixtureError("unsupported synthetic statement fault") from error
        recordings[identity] = value
    return recordings


def _cancel_acceptance_recordings(entries):
    if type(entries) is not list:
        raise FixtureError("cancel_acceptances must be an array")
    recordings = {}
    for entry in entries:
        if type(entry) is not dict:
            raise FixtureError("cancel acceptance must be an object")
        payload = set(entry) & {"recorded_text", "fault"}
        if len(payload) != 1:
            raise FixtureError("cancel acceptance requires exactly one of recorded_text or fault")
        exact_fields(entry, {"settlement_id", "source_id"} | payload, "cancel acceptance")
        identity = (_identifier(entry["settlement_id"]), _identifier(entry["source_id"]))
        if identity in recordings:
            raise FixtureError("duplicate cancel acceptance identity")
        if "recorded_text" in payload:
            value = entry["recorded_text"]
            if type(value) is not str:
                raise FixtureError("recorded_text must be text")
        else:
            try:
                value = SyntheticCancelAcceptanceFault(entry["fault"])
            except (ValueError, TypeError) as error:
                raise FixtureError("unsupported synthetic cancel acceptance fault") from error
        recordings[identity] = value
    return recordings


def load_fixture(path: str | Path) -> TicketOperationsSession:
    fixture = decode_json(Path(path).read_text(encoding="utf-8"))
    fields = {"fixture_version", "provenance", "setup", "offers", "presentations"}
    if type(fixture) is dict:
        fields.update({"payments", "cancel_acceptances", "statements"} & set(fixture))
    exact_fields(fixture, fields, "fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != "MOCK_GATE_ONLY":
        raise FixtureError("fixture provenance must be MOCK_GATE_ONLY")
    offers = FakeResaleOfferSource(recordings=_offers(fixture["offers"]))
    presentations = FakePresentationSource(recordings=_presentations(fixture["presentations"]))
    payments = (FakeResalePaymentSource(recordings=_payment_recordings(fixture["payments"]))
                if "payments" in fixture else None)
    cancellations = (FakeCancelAcceptanceSource(
        recordings=_cancel_acceptance_recordings(fixture["cancel_acceptances"]))
        if "cancel_acceptances" in fixture else None)
    statements = (FakeStatementSource(recordings=_statement_recordings(fixture["statements"]))
                  if "statements" in fixture else None)
    return TicketOperationsSession(setup=fixture["setup"], offer_source=offers,
                                   presentation_source=presentations, payment_source=payments,
                                   cancel_acceptance_source=cancellations,
                                   statement_source=statements)
