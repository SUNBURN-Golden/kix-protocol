"""Standard-library JSONL interface to one explicit local admission session."""

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

from admission_fixture import FixtureError, decode_json, exact_fields, load_fixture
from admission_fsm import AdmissionError
from admission_session import AdmissionSession
from presentation_source import PresentationSourceError
from reservation_fsm import ReservationError
from resale_fsm import ResaleError
from settlement_fsm import SettlementError

_DOMAIN_ERRORS = (AdmissionError, ReservationError, ResaleError, SettlementError)
# Local Python method selectors; no new wire commands or read catalogue.
_DISPATCH = {
    "authorize_admission": (AdmissionSession.authorize_admission,
                            {"presentation_id", "admission_id", "idempotency_key", "gate_role", "expires_ms"},
                            "receipt"),
    "consume": (AdmissionSession.consume,
                {"presentation_id", "consume_id", "idempotency_key", "gate_role"}, "receipt"),
    "view": (AdmissionSession.view, {"right_id"}, "view"),
    "view_credential": (AdmissionSession.view_credential,
                        {"right_id", "version", "holder_role"}, "view"),
    "set_clock": (AdmissionSession.set_clock, {"subject_id", "idempotency_key", "now_ms"}, "receipt"),
}


def dispatch_request(session: AdmissionSession, request: dict) -> dict:
    exact_fields(request, {"operation", "arguments"}, "request")
    operation = request["operation"]
    if type(operation) is not str or operation not in _DISPATCH:
        raise FixtureError("unsupported session operation")
    method, fields, result_key = _DISPATCH[operation]
    exact_fields(request["arguments"], fields, f"{operation} arguments")
    return {"operation": operation, result_key: method(session, **request["arguments"])}


def _error(operation, error):
    detail = ({"code": error.code} if isinstance(error, _DOMAIN_ERRORS)
              else {"type": type(error).__name__, "message": str(error)})
    return {"operation": operation, "error": detail}


def _emit(value):
    print(json.dumps(value, sort_keys=True, allow_nan=False))


def run_requests(session: AdmissionSession, lines) -> int:
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
        except (*_DOMAIN_ERRORS, PresentationSourceError) as error:
            # Only the next supplied line can cause another operation.
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
