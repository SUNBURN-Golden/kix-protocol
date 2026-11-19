"""Strict synthetic setup for fresh local reservation, settlement and resale FSMs."""

from pathlib import Path

from admission_fixture import (
    FixtureError, _SETUP as _ADMISSION_SETUP, decode_json, exact_fields,
)
from fake_resale_offer_source import FakeResaleOfferSource, SyntheticResaleOfferFault
from fake_resale_payment_source import FakeResalePaymentSource, SyntheticResalePaymentFault
from mock_gates import GateError, _ident
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleMachine
from resale_session import ResaleSession
# admission_fixture installs the existing sibling settlement reference path.
from settlement_fsm import SettlementMachine

# Only the shared setup schema is reused; admission setup/requirements are excluded.
_SETUP = {name: _ADMISSION_SETUP[name] for name in ("settlement", "reservation", "resale")}


def _identifier(value):
    try:
        return _ident(value)
    except GateError as error:
        raise FixtureError(f"fixture identifier: {error.code}") from error


def _validate_setup(setup):
    if type(setup) is not list or not setup:
        raise FixtureError("setup must be a nonempty array")
    clocks, orders, issued, adopted = set(), {}, {}, {}
    for entry in setup:
        exact_fields(entry, {"machine", "operation", "subject_id", "idempotency_key", "body"},
                     "setup entry")
        machine, operation = entry["machine"], entry["operation"]
        if (type(machine) is not str or type(operation) is not str
                or machine not in _SETUP or operation not in _SETUP[machine]):
            raise FixtureError("unsupported setup machine/operation")
        subject = _identifier(entry["subject_id"])
        _identifier(entry["idempotency_key"])
        body = entry["body"]
        exact_fields(body, _SETUP[machine][operation], f"{machine}.{operation} body")
        if operation == "set_clock":
            clocks.add(machine)
        elif machine != "settlement" and machine not in clocks:
            raise FixtureError(f"explicit initial {machine} clock required before setup")
        if machine == "reservation":
            if operation == "confirm":
                orders[subject] = _identifier(body["reservation_id"])
                _identifier(body["quote_ref"])
            elif operation == "issue":
                issued[subject] = _identifier(body["order_id"])
        elif operation == "adopt_issued":
            reservation = _identifier(body["reservation_id"])
            order = _identifier(body["order_id"])
            _identifier(body["quote_ref"])
            if issued.get(subject) != order or orders.get(order) != reservation:
                raise FixtureError("adoption requires matching explicit prior issuance and confirmation")
            adopted[subject] = order
    if clocks != {"reservation", "resale"}:
        raise FixtureError("explicit reservation and resale clocks required")
    if not issued or issued != adopted:
        raise FixtureError("each issued right requires matching resale adoption")


def _recordings(offers):
    if type(offers) is not list:
        raise FixtureError("offers must be an array")
    recordings = {}
    for entry in offers:
        if type(entry) is not dict:
            raise FixtureError("offer must be an object")
        payload = set(entry) & {"recorded_text", "fault"}
        if len(payload) != 1:
            raise FixtureError("offer requires exactly one of recorded_text or fault")
        exact_fields(entry, {"offer_id"} | payload, "offer")
        identity = _identifier(entry["offer_id"])
        if identity in recordings:
            raise FixtureError("duplicate offer identity")
        if "recorded_text" in payload:
            value = entry["recorded_text"]
            if type(value) is not str:
                raise FixtureError("recorded_text must be text")
        else:
            try:
                value = SyntheticResaleOfferFault(entry["fault"])
            except (ValueError, TypeError) as error:
                raise FixtureError("unsupported synthetic fault") from error
        recordings[identity] = value
    return recordings


def _payment_recordings(payments):
    if type(payments) is not list:
        raise FixtureError("payments must be an array")
    recordings = {}
    for entry in payments:
        if type(entry) is not dict:
            raise FixtureError("payment must be an object")
        payload = set(entry) & {"recorded_text", "fault"}
        if len(payload) != 1:
            raise FixtureError("payment requires exactly one of recorded_text or fault")
        exact_fields(entry, {"recording_id"} | payload, "payment")
        identity = _identifier(entry["recording_id"])
        if identity in recordings:
            raise FixtureError("duplicate payment identity")
        if "recorded_text" in payload:
            value = entry["recorded_text"]
            if type(value) is not str:
                raise FixtureError("recorded_text must be text")
        else:
            try:
                value = SyntheticResalePaymentFault(entry["fault"])
            except (ValueError, TypeError) as error:
                raise FixtureError("unsupported synthetic payment fault") from error
        recordings[identity] = value
    return recordings


def load_fixture(path: str | Path) -> ResaleSession:
    """Validate structure first, execute explicit setup, then publish one session.

    Recorded offer/payment text is checked by the existing source/adapter when fetched.
    Setup uses public FSM APIs; failed construction discards the private graph,
    without providing cross-machine rollback or changing FSM rejection semantics.
    Settlement binding is optional for both issuance and transfer.
    """
    fixture = decode_json(Path(path).read_text(encoding="utf-8"))
    fields = {"fixture_version", "provenance", "setup", "offers"}
    if type(fixture) is dict and "payments" in fixture:
        fields.add("payments")
    exact_fields(fixture, fields, "fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != "MOCK_GATE_ONLY":
        raise FixtureError("fixture provenance must be MOCK_GATE_ONLY")
    _validate_setup(fixture["setup"])
    source = FakeResaleOfferSource(recordings=_recordings(fixture["offers"]))
    payments = (FakeResalePaymentSource(recordings=_payment_recordings(fixture["payments"]))
                if "payments" in fixture else None)
    book = SettlementMachine()
    tickets = ReservationMachine(settlement_source=book)
    resale = ResaleMachine(ticket_source=tickets, settlement_source=book)
    machines = {"settlement": book, "reservation": tickets, "resale": resale}
    for entry in fixture["setup"]:
        method = getattr(machines[entry["machine"]], entry["operation"])
        method(entry["subject_id"], idempotency_key=entry["idempotency_key"], **entry["body"])
    return ResaleSession(resale, source, payment_source=payments)
