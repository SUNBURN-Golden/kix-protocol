"""Strict JSONL interface to one synthetic, in-memory AI delegation session."""

import argparse
from contextlib import nullcontext
from pathlib import Path
import sys

from ai_delegation_mock import AiDelegationError, PROVENANCE, _canonical
from delegation_fixture import (FixtureError, decode_json, exact_fields, load_fixture,
                                session_from_fixture, validate_json)
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
    frame = _canonical(value) + "\n"
    if sys.stdout.write(frame) != len(frame):
        raise OSError("short JSON frame write")
    sys.stdout.flush()


def run_requests(session: DelegationSession, lines) -> int:
    rejected = False
    lines = iter(lines)
    while True:
        try:
            line = next(lines)
        except StopIteration:
            return 1 if rejected else 0
        except (OSError, UnicodeError) as error:
            _emit(_error(None, error))
            return 2
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    startup = parser.add_mutually_exclusive_group(required=True)
    startup.add_argument("--fixture", type=Path)
    startup.add_argument("--init-stdin", action="store_true")
    parser.add_argument("--requests", required=True, help="JSONL path, or - for stdin")
    args = parser.parse_args(argv)
    if args.init_stdin and args.requests != "-":
        parser.error("--init-stdin requires --requests -")
    try:
        if args.init_stdin:
            line = sys.stdin.readline()
            if not line.endswith("\n"):
                raise FixtureError("initialization requires one newline-terminated JSON frame")
            fixture = decode_json(line)
            session = session_from_fixture(fixture)
        else:
            session = load_fixture(args.fixture)
        requests = (nullcontext(sys.stdin) if args.requests == "-"
                    else Path(args.requests).open(encoding="utf-8"))
    except (FixtureError, AiDelegationError, OSError, UnicodeError) as error:
        try:
            _emit(_error(None, error))
        except (OSError, UnicodeError):
            pass
        return 2
    # Do not retry output failures (including failure to flush the startup ack).
    try:
        with requests as lines:
            if args.init_stdin:
                _emit({"operation": None, "provenance": PROVENANCE, "initialized": fixture})
            return run_requests(session, lines)
    except (OSError, UnicodeError):
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
