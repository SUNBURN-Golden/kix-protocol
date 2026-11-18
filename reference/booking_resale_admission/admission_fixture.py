"""Strict synthetic fixture input; no policy, keys, clocks or setup defaults."""

import json
import math
import sys
from pathlib import Path

from admission_fsm import AdmissionMachine
from admission_session import AdmissionSession
from fake_presentation_source import FakePresentationSource, SyntheticPresentationFault
from mock_gates import GateError, _ident
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleMachine

_SETTLEMENT_DIR = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT_DIR) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT_DIR))

from settlement_fsm import SettlementMachine  # noqa: E402


class FixtureError(ValueError):
    """Invalid local input, not a protocol error code."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _finite_float(value):
    # Even JSON exponent syntax can overflow Python's float into infinity.
    number = float(value)
    if not math.isfinite(number):
        raise FixtureError("non-finite JSON number")
    return number


def _constant(value):
    raise FixtureError(f"non-finite JSON constant: {value}")


def decode_json(text):
    try:
        return json.loads(text, object_pairs_hook=_object, parse_constant=_constant,
                          parse_float=_finite_float)
    except (ValueError, RecursionError) as error:
        raise FixtureError(str(error)) from error


def exact_fields(value, fields, context):
    if type(value) is not dict or set(value) != set(fields):
        raise FixtureError(f"{context} requires exactly: {', '.join(sorted(fields))}")


def _identifier(value):
    try:
        return _ident(value)
    except GateError as error:
        raise FixtureError(f"fixture identifier: {error.code}") from error


_SHOW = frozenset(("organizer_role", "capacity", "gate_roles", "primary_price",
                   "resale_cap", "resale_allowed", "organizer_bps", "platform_bps"))
_ADOPT = _SHOW | {"show_id", "slot", "buyer_role", "expires_ms", "order_id", "amount",
                  "payment_ref", "reservation_id", "quote_ref"}
# Explicit local setup method selectors, never a protocol-command catalogue.
_SETUP = {
    "settlement": {
        "initiate": {"trade_id", "gross", "debtor_role", "policy", "currency"},
        "authorize": set(), "capture": set(),
        "commit": {"movement_id", "gross", "amount", "fee", "tax", "held",
                   "adjustment", "adjustment_reason"},
    },
    "reservation": {
        "set_clock": {"now_ms"}, "register_show": _SHOW,
        "hold": {"show_id", "slot", "buyer_role", "expires_ms"},
        "confirm": {"reservation_id", "amount", "quote_ref"},
        "observe_payment": {"payment_ref", "amount"},
        "bind_settlement": {"settlement_id"}, "issue": {"order_id"},
    },
    "resale": {"set_clock": {"now_ms"}, "adopt_issued": _ADOPT},
    "admission": {"set_clock": {"now_ms"}, "adopt_issued": _ADOPT},
}


def _validate_setup(setup):
    if type(setup) is not list or not setup:
        raise FixtureError("setup must be a nonempty array")
    clocks = set()
    issued = {}
    orders = {}
    bound = set()
    adopted = {"resale": set(), "admission": set()}
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
        if operation in ("confirm", "adopt_issued"):
            _identifier(body["reservation_id"])
            _identifier(body["quote_ref"])
        if machine == "reservation":
            if operation == "confirm":
                orders[subject] = body["reservation_id"]
            elif operation == "bind_settlement":
                bound.add(subject)
            elif operation == "issue":
                issued[subject] = _identifier(body["order_id"])
        elif operation == "adopt_issued":
            adopted[machine].add(subject)
    if clocks != {"reservation", "resale", "admission"}:
        raise FixtureError("explicit reservation, resale and admission clocks required")
    if not issued or any(set(issued) != rights for rights in adopted.values()):
        raise FixtureError("each issued right requires both resale and admission adoption")
    if any(order not in orders or orders[order] not in bound for order in issued.values()):
        raise FixtureError("each issuance requires an explicit confirmed reservation settlement binding")


def _recordings(presentations):
    if type(presentations) is not list:
        raise FixtureError("presentations must be an array")
    recordings = {}
    for entry in presentations:
        if type(entry) is not dict:
            raise FixtureError("presentation must be an object")
        payload = set(entry) & {"recorded_text", "fault"}
        if len(payload) != 1:
            raise FixtureError("presentation requires exactly one of recorded_text or fault")
        exact_fields(entry, {"operation", "presentation_id"} | payload, "presentation")
        operation = entry["operation"]
        if type(operation) is not str or operation not in ("authorize_admission", "consume"):
            raise FixtureError("unsupported presentation operation")
        identity = (operation, _identifier(entry["presentation_id"]))
        if identity in recordings:
            raise FixtureError("duplicate presentation identity")
        if "recorded_text" in payload:
            value = entry["recorded_text"]
            if type(value) is not str:
                raise FixtureError("recorded_text must be text")
        else:
            try:
                value = SyntheticPresentationFault(entry["fault"])
            except (ValueError, TypeError) as error:
                raise FixtureError("unsupported synthetic fault") from error
        recordings[identity] = value
    return recordings


def load_fixture(path: str | Path) -> AdmissionSession:
    """Build fresh real local machines, exposing a session only after all setup succeeds.

    Fixture structure is checked before construction. FSM setup rejections propagate
    unchanged; the discarded local graph is not a cross-machine rollback mechanism.
    Presentation text is deliberately validated only by the source on fetch.
    """
    fixture = decode_json(Path(path).read_text(encoding="utf-8"))
    exact_fields(fixture, {"fixture_version", "provenance", "setup", "presentations"}, "fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != "MOCK_GATE_ONLY":
        raise FixtureError("fixture provenance must be MOCK_GATE_ONLY")
    _validate_setup(fixture["setup"])
    source = FakePresentationSource(recordings=_recordings(fixture["presentations"]))
    book = SettlementMachine()
    tickets = ReservationMachine(settlement_source=book)
    resale = ResaleMachine(ticket_source=tickets)
    admission = AdmissionMachine(ticket_source=tickets, ownership_source=resale, settlement_source=book)
    machines = {"settlement": book, "reservation": tickets, "resale": resale, "admission": admission}
    for entry in fixture["setup"]:
        method = getattr(machines[entry["machine"]], entry["operation"])
        method(entry["subject_id"], idempotency_key=entry["idempotency_key"], **entry["body"])
    return AdmissionSession(admission, source)
