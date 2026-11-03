"""Standard-library JSONL interface to one explicitly configured local resale session."""

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

from admission_fixture import FixtureError, decode_json, exact_fields
from reservation_fsm import ReservationError
from resale_fixture import load_fixture
from resale_fsm import ResaleError
from resale_offer_source import ResaleOfferSourceError
from resale_payment_source import ResalePaymentSourceError
from resale_session import ResaleSession
from settlement_fsm import SettlementError

_DOMAIN_ERRORS = (ReservationError, ResaleError, SettlementError)
# Local Python selectors only; this is not a new protocol-command catalogue.
_DISPATCH = {
    "adopt_issued": (ResaleSession.adopt_issued,
                     {"right_id", "idempotency_key", "show_id", "organizer_role", "capacity",
                      "gate_roles", "primary_price", "resale_cap", "resale_allowed", "organizer_bps",
                      "platform_bps", "slot", "buyer_role", "expires_ms", "order_id", "amount",
                      "payment_ref", "reservation_id", "quote_ref"}, "receipt"),
    "list_resale": (ResaleSession.list_resale, {"offer_id", "listing_id", "idempotency_key"}, "receipt"),
    "hold_buy": (ResaleSession.hold_buy,
                 {"hold_id", "listing_id", "buyer_role", "idempotency_key"}, "receipt"),
    "release_hold": (ResaleSession.release_hold, {"hold_id", "buyer_role", "idempotency_key"}, "receipt"),
    "cancel_listing": (ResaleSession.cancel_listing,
                       {"listing_id", "seller_role", "idempotency_key"}, "receipt"),
    "observe_recorded_payment": (ResaleSession.observe_recorded_payment,
                                 {"recording_id", "listing_id", "idempotency_key"}, "receipt"),
    "observe_resale_payment": (ResaleSession.observe_resale_payment,
                               {"listing_id", "payment_ref", "amount", "idempotency_key"}, "receipt"),
    "bind_settlement": (ResaleSession.bind_settlement,
                        {"listing_id", "settlement_id", "idempotency_key"}, "receipt"),
    "accept_resale": (ResaleSession.accept_resale,
                      {"transfer_id", "listing_id", "idempotency_key"}, "receipt"),
    "close": (ResaleSession.close, {"listing_id", "idempotency_key"}, "receipt"),
    "set_clock": (ResaleSession.set_clock, {"subject_id", "now_ms", "idempotency_key"}, "receipt"),
    "reconcile": (ResaleSession.reconcile, {"listing_id", "idempotency_key"}, "receipt"),
    "view": (ResaleSession.view, {"listing_id"}, "view"),
    "view_right": (ResaleSession.view_right, {"right_id"}, "view"),
    "view_presentation": (ResaleSession.view_presentation,
                          {"right_id", "version", "holder_role"}, "view"),
}


def dispatch_request(session: ResaleSession, request: dict) -> dict:
    exact_fields(request, {"operation", "arguments"}, "request")
    operation = request["operation"]
    if type(operation) is not str or operation not in _DISPATCH:
        raise FixtureError("unsupported session operation")
    method, fields, result_key = _DISPATCH[operation]
    arguments = request["arguments"]
    if operation == "observe_resale_payment" and type(arguments) is dict and "buyer_role" in arguments:
        fields = fields | {"buyer_role"}
    exact_fields(arguments, fields, f"{operation} arguments")
    return {"operation": operation, result_key: method(session, **arguments)}


def _error(operation, error):
    detail = ({"code": error.code} if isinstance(error, _DOMAIN_ERRORS)
              else {"type": type(error).__name__, "message": str(error)})
    return {"operation": operation, "error": detail}


def _emit(value):
    print(json.dumps(value, sort_keys=True, allow_nan=False))


def run_requests(session: ResaleSession, lines) -> int:
    rejected = False
    for line in lines:
        operation = None
        try:
            request = decode_json(line)
            if type(request) is dict and type(request.get("operation")) is str:
                operation = request["operation"]
            result = dispatch_request(session, request)
        except FixtureError as error:
            _emit(_error(operation, error))
            return 2
        except (*_DOMAIN_ERRORS, ResaleOfferSourceError, ResalePaymentSourceError) as error:
            # Only another explicitly supplied line can cause another operation.
            result = _error(operation, error)
            rejected = True
        _emit(result)
    return 1 if rejected else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--requests", required=True, help="JSONL path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        session = load_fixture(args.fixture)
        requests = (nullcontext(sys.stdin) if args.requests == "-"
                    else Path(args.requests).open(encoding="utf-8"))
        with requests as lines:
            return run_requests(session, lines)
    except (FixtureError, OSError, UnicodeError, *_DOMAIN_ERRORS) as error:
        _emit(_error(None, error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
