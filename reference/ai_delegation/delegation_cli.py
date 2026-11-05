"""Strict JSONL interface to one synthetic, in-memory AI delegation session."""

import argparse
from contextlib import nullcontext
from pathlib import Path
import sys

from ai_delegation_mock import AiDelegationError, PROVENANCE, _canonical
from delegation_fixture import FixtureError, decode_json, exact_fields, load_fixture, validate_json
from delegation_session import DelegationSession


# Explicit local selectors, not protocol commands or arbitrary attribute access.
# Method, required argument fields, result field. All arguments are required.
_DISPATCH = {
    "issue_grant": (DelegationSession.issue_grant,
                    {"actor", "grant_id", "agent_id", "authority", "scope", "limits", "period"},
                    "receipt"),
    "revoke_grant": (DelegationSession.revoke_grant, {"actor", "grant_id", "reason"}, "receipt"),
    "decide_proposal": (DelegationSession.decide_proposal,
                        {"actor", "proposal_id", "decision", "now"}, "receipt"),
    "call_tool": (DelegationSession.call_tool, {"actor", "grant_id", "tool", "args", "now"},
                  "receipt"),
    "attempt_execution": (DelegationSession.attempt_execution, {"actor", "proposal_id"}, "receipt"),
    "view_grant": (DelegationSession.view_grant, {"grant_id"}, "view"),
    "view_proposal": (DelegationSession.view_proposal, {"proposal_id"}, "view"),
}


def dispatch_request(session: DelegationSession, request: dict) -> dict:
    """Validate transport shape, then forward nested domain inputs unchanged once."""
    validate_json(request)
    exact_fields(request, {"operation", "arguments"}, "request")
    operation = request["operation"]
    if type(operation) is not str or operation not in _DISPATCH:
        raise FixtureError("unsupported session operation")
    method, required, result_key = _DISPATCH[operation]
    arguments = request["arguments"]
    exact_fields(arguments, required, f"{operation} arguments")
    return {"operation": operation, "provenance": PROVENANCE,
            result_key: method(session, **arguments)}


def _error(operation, error):
    detail = ({"code": error.code} if isinstance(error, AiDelegationError)
              else {"type": type(error).__name__, "message": str(error)})
    return {"operation": operation, "provenance": PROVENANCE, "error": detail}


def _emit(value):
    print(_canonical(value))


def run_requests(session: DelegationSession, lines) -> int:
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
        except AiDelegationError as error:
            # Only a subsequent supplied line causes another call.
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
    except (FixtureError, AiDelegationError, OSError, UnicodeError) as error:
        _emit(_error(None, error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
