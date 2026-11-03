"""Strict JSONL booking, resale, admission and settlement on one local graph."""

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

from admission_cli import _DOMAIN_ERRORS, dispatch_request as _admission
from admission_fixture import FixtureError, decode_json, exact_fields
from booking_cli import dispatch_request as _booking
from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_fixture import load_fixture as load_quote_fixture
from booking_quote_source import BookingQuoteSourceError
from booking_session import BookingInputError
from presentation_source import PresentationSourceError
from resale_cli import dispatch_request as _resale
from resale_offer_source import ResaleOfferSourceError
from resale_payment_source import ResalePaymentSourceError
from ticket_operations_fixture import load_fixture
from ticket_operations_session import TicketOperationsSession, TicketSettlementSession
from cancel_acceptance_source import CancelAcceptanceSourceError
from statement_source import StatementSourceError


# Local selectors for existing FSM operations; no policy or statement defaults.
_SETTLEMENT_DISPATCH = {
    "initiate": (TicketSettlementSession.initiate,
                 {"settlement_id", "idempotency_key", "trade_id", "gross",
                  "debtor_role", "policy", "currency"}, "receipt"),
    "authorize": (TicketSettlementSession.authorize,
                  {"settlement_id", "idempotency_key"}, "receipt"),
    "capture": (TicketSettlementSession.capture,
                {"settlement_id", "idempotency_key"}, "receipt"),
    "fail": (TicketSettlementSession.fail,
             {"settlement_id", "idempotency_key", "reason"}, "receipt"),
    "cancel": (TicketSettlementSession.cancel,
               {"settlement_id", "idempotency_key", "reason"}, "receipt"),
    "reconcile": (TicketSettlementSession.reconcile,
                  {"settlement_id", "idempotency_key"}, "receipt"),
    "commit": (TicketSettlementSession.commit,
               {"settlement_id", "idempotency_key", "movement_id", "gross", "amount",
                "fee", "tax", "held", "adjustment", "adjustment_reason"}, "receipt"),
    "commit_recorded_statement": (TicketSettlementSession.commit_recorded_statement,
                                  {"settlement_id", "movement_id", "idempotency_key"}, "receipt"),
    "observe_recorded_statement": (TicketSettlementSession.observe_recorded_statement,
                                   {"settlement_id", "movement_id", "idempotency_key"}, "receipt"),
    "distribute": (TicketSettlementSession.distribute,
                   {"settlement_id", "idempotency_key", "order"}, "receipt"),
    "bind_refund": (TicketSettlementSession.bind_refund,
                    {"settlement_id", "idempotency_key", "refund_id", "amount",
                     "beneficiary_role", "reason"}, "receipt"),
    "observe_recorded_cancel_acceptance": (TicketSettlementSession.observe_recorded_cancel_acceptance,
                                           {"settlement_id", "source_id", "idempotency_key"}, "receipt"),
    "view": (TicketSettlementSession.view, {"settlement_id"}, "view"),
}


def dispatch_request(session: TicketOperationsSession, request: dict, *, quote_adapter=None) -> dict:
    exact_fields(request, {"surface", "operation", "arguments"}, "request")
    surface = request["surface"]
    if type(surface) is not str or surface not in ("booking", "resale", "admission", "settlement"):
        raise FixtureError("surface must be booking, resale, admission or settlement")
    nested = {"operation": request["operation"], "arguments": request["arguments"]}
    if surface == "booking":
        result = _booking(session.booking, nested, quote_adapter=quote_adapter)
    elif surface == "resale":
        result = _resale(session.resale, nested)
    elif surface == "admission":
        result = _admission(session.admission, nested)
    else:
        operation = request["operation"]
        if type(operation) is not str or operation not in _SETTLEMENT_DISPATCH:
            raise FixtureError("unsupported settlement operation")
        method, fields, key = _SETTLEMENT_DISPATCH[operation]
        exact_fields(request["arguments"], fields, f"{operation} arguments")
        result = {"operation": operation, key: method(session.settlement, **request["arguments"])}
    return {"surface": surface, **result}


def _error(surface, operation, error):
    detail = ({"code": error.code} if isinstance(error, _DOMAIN_ERRORS)
              else {"type": type(error).__name__, "message": str(error)})
    return {"surface": surface, "operation": operation, "error": detail}


def _emit(value):
    print(json.dumps(value, sort_keys=True, allow_nan=False))


def run_requests(session: TicketOperationsSession, lines, *, quote_adapter=None) -> int:
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
            result = dispatch_request(session, request, quote_adapter=quote_adapter)
        except (FixtureError, BookingInputError) as error:
            _emit(_error(surface, operation, error))
            return 2
        except (*_DOMAIN_ERRORS, ResaleOfferSourceError, PresentationSourceError,
                ResalePaymentSourceError, BookingQuoteSourceError, CancelAcceptanceSourceError,
                StatementSourceError) as error:
            result = _error(surface, operation, error)
            rejected = True
        _emit(result)
    return 1 if rejected else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--quotes", type=Path, help="synthetic recorded-quote source fixture path")
    parser.add_argument("--requests", required=True, help="JSONL path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        session = load_fixture(args.fixture)
        adapter = (BookingQuoteAdapter(session.booking, load_quote_fixture(args.quotes))
                   if args.quotes is not None else None)
        requests = (nullcontext(sys.stdin) if args.requests == "-"
                    else Path(args.requests).open(encoding="utf-8"))
        with requests as lines:
            return run_requests(session, lines, quote_adapter=adapter)
    except (FixtureError, OSError, UnicodeError, *_DOMAIN_ERRORS) as error:
        _emit(_error(None, None, error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
