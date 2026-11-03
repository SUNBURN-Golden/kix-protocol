"""Strict JSONL local booking desk; each invocation uses one fresh in-memory FSM."""

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

from admission_fixture import FixtureError, decode_json, exact_fields
from booking_session import BookingInputError, BookingSession
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_fixture import load_fixture
from booking_quote_source import BookingQuoteSourceError
from reservation_fsm import ReservationError, ReservationMachine

# Local selectors for existing FSM operations, not new protocol commands.
_DISPATCH = {
    "bind_settlement": (BookingSession.bind_settlement,
                        {"reservation_id", "settlement_id", "idempotency_key"}, "receipt"),
    "issue": (BookingSession.issue, {"issuance_id", "order_id", "idempotency_key"}, "receipt"),
    "register_show": (BookingSession.register_show,
                      {"show_id", "organizer_role", "capacity", "gate_roles", "primary_price",
                       "resale_cap", "resale_allowed", "organizer_bps", "platform_bps",
                       "idempotency_key"}, "receipt"),
    "set_clock": (BookingSession.set_clock, {"subject_id", "now_ms", "idempotency_key"}, "receipt"),
    "hold": (BookingSession.hold, {"reservation_id", "show_id", "slot", "buyer_role", "expires_ms",
                                    "idempotency_key"}, "receipt"),
    "release": (BookingSession.release, {"reservation_id", "idempotency_key"}, "receipt"),
    "confirm": (BookingSession.confirm, {"order_id", "reservation_id", "amount", "quote_ref",
                                          "idempotency_key"}, "receipt"),
    "cancel": (BookingSession.cancel, {"reservation_id", "idempotency_key"}, "receipt"),
    "reconcile": (BookingSession.reconcile, {"reservation_id", "idempotency_key"}, "receipt"),
    "view": (BookingSession.view, {"reservation_id"}, "view"),
    "view_show": (BookingSession.view_show, {"show_id"}, "view"),
}


def dispatch_request(session: BookingSession, request: dict, *, quote_adapter=None) -> dict:
    exact_fields(request, {"operation", "arguments"}, "request")
    operation = request["operation"]
    if type(operation) is str and operation == "confirm_recorded_quote" and quote_adapter is not None:
        exact_fields(request["arguments"],
                     {"recording_id", "reservation_id", "order_id", "idempotency_key"},
                     "confirm_recorded_quote arguments")
        return {"operation": operation,
                "receipt": quote_adapter.confirm_recorded_quote(**request["arguments"])}
    if type(operation) is not str or operation not in _DISPATCH:
        raise FixtureError("unsupported session operation")
    method, fields, result_key = _DISPATCH[operation]
    exact_fields(request["arguments"], fields, f"{operation} arguments")
    return {"operation": operation, result_key: method(session, **request["arguments"])}


def _error(operation, error):
    detail = ({"code": error.code} if isinstance(error, ReservationError)
              else {"type": type(error).__name__, "message": str(error)})
    return {"operation": operation, "error": detail}


def _emit(value):
    print(json.dumps(value, sort_keys=True, allow_nan=False))


def run_requests(session: BookingSession, lines, *, quote_adapter=None) -> int:
    rejected = False
    for line in lines:
        operation = None
        try:
            request = decode_json(line)
            if type(request) is dict and type(request.get("operation")) is str:
                operation = request["operation"]
            result = dispatch_request(session, request, quote_adapter=quote_adapter)
        except (FixtureError, BookingInputError) as error:
            _emit(_error(operation, error))
            return 2
        except (ReservationError, BookingQuoteSourceError) as error:
            result = _error(operation, error)
            rejected = True
        _emit(result)
    return 1 if rejected else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", required=True, help="JSONL path, or - for stdin")
    parser.add_argument("--quotes", help="synthetic recorded-quote source fixture path")
    args = parser.parse_args(argv)
    try:
        session = BookingSession(ReservationMachine())
        adapter = (BookingQuoteAdapter(session, load_fixture(args.quotes))
                   if args.quotes is not None else None)
        requests = (nullcontext(sys.stdin) if args.requests == "-"
                    else Path(args.requests).open(encoding="utf-8"))
        with requests as lines:
            return run_requests(session, lines, quote_adapter=adapter)
    except (FixtureError, OSError, UnicodeError) as error:
        _emit(_error(None, error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
