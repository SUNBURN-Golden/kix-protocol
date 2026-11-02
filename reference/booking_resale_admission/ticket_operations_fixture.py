"""Strict combined synthetic fixture; recordings are validated on explicit fetch."""

from pathlib import Path

from admission_fixture import FixtureError, _recordings as _presentations, decode_json, exact_fields
from fake_presentation_source import FakePresentationSource
from fake_resale_offer_source import FakeResaleOfferSource
from fake_resale_payment_source import FakeResalePaymentSource
from resale_fixture import _payment_recordings, _recordings as _offers
from ticket_operations_session import TicketOperationsSession


def load_fixture(path: str | Path) -> TicketOperationsSession:
    fixture = decode_json(Path(path).read_text(encoding="utf-8"))
    fields = {"fixture_version", "provenance", "setup", "offers", "presentations"}
    if type(fixture) is dict and "payments" in fixture:
        fields.add("payments")
    exact_fields(fixture, fields, "fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != "MOCK_GATE_ONLY":
        raise FixtureError("fixture provenance must be MOCK_GATE_ONLY")
    offers = FakeResaleOfferSource(recordings=_offers(fixture["offers"]))
    presentations = FakePresentationSource(recordings=_presentations(fixture["presentations"]))
    payments = (FakeResalePaymentSource(recordings=_payment_recordings(fixture["payments"]))
                if "payments" in fixture else None)
    return TicketOperationsSession(setup=fixture["setup"], offer_source=offers,
                                   presentation_source=presentations, payment_source=payments)
