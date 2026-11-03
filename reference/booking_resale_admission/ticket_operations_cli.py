"""Strict JSONL booking, resale and admission requests on one shared local graph."""

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

from admission_cli import _DOMAIN_ERRORS, dispatch_request as _admission
from admission_fixture import FixtureError, decode_json, exact_fields
from booking_cli import dispatch_request as _booking
from booking_session import BookingInputError
from presentation_source import PresentationSourceError
from resale_cli import dispatch_request as _resale
from resale_offer_source import ResaleOfferSourceError
from resale_payment_source import ResalePaymentSourceError
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketOperationsSession


def dispatch_request(session: TicketOperationsSession, request: dict) -> dict:
    exact_fields(request, {"surface", "operation", "arguments"}, "request")
    surface = request["surface"]
    if type(surface) is not str or surface not in ("booking", "resale", "admission"):
        raise FixtureError("surface must be booking, resale or admission")
    nested = {"operation": request["operation"], "arguments": request["arguments"]}
    if surface == "booking":
        result = _booking(session.booking, nested)
    elif surface == "resale":
        result = _resale(session.resale, nested)
    else:
        result = _admission(session.admission, nested)
    return {"surface": surface, **result}


def _error(surface, operation, error):
    detail = ({"code": error.code} if isinstance(error, _DOMAIN_ERRORS)
              else {"type": type(error).__name__, "message": str(error)})
    return {"surface": surface, "operation": operation, "error": detail}


def _emit(value):
    print(json.dumps(value, sort_keys=True, allow_nan=False))


def run_requests(session: TicketOperationsSession, lines) -> int:
    rejected = False
    for line in lines:
        surface = operation = None
        try:
            request = decode_json(line)
            if type(request) is dict:
                if type(request.get("surface")) is str:
                    surface = request["surface"]
                if type(request.get("operation")) is str:
                    operation = request["operation"]
            result = dispatch_request(session, request)
        except (FixtureError, BookingInputError) as error:
            _emit(_error(surface, operation, error))
            return 2
        except (*_DOMAIN_ERRORS, ResaleOfferSourceError, PresentationSourceError,
                ResalePaymentSourceError) as error:
            result = _error(surface, operation, error)
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
        _emit(_error(None, None, error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
