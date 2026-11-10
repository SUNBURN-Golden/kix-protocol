"""Strict UTF-8 JSONL interface to one synthetic POINT_F4 pool session."""

import argparse
from contextlib import nullcontext
from pathlib import Path
import sys

from pool_session import (PoolSession, decode_opening_balances, dispatch_request, error_reply,
                          initialized_reply, read_opening_balances)
from reward_fixture import FixtureError, decode_json
from token_reward_model import TokenRewardError, _canonical


def emit(value, stream):
    print(_canonical(value), file=stream, flush=True)


def diagnostic(error, stream):
    """Best effort on a separate stream; never retry a request or failed output."""
    try:
        emit(error_reply(None, error), stream)
    except (Exception, KeyboardInterrupt):
        pass


def run_requests(session, lines, *, output_stream):
    rejected = False
    for line in lines:
        operation = None
        try:
            request = decode_json(line)
            if type(request) is dict and type(request.get("operation")) is str:
                operation = request["operation"]
            result = dispatch_request(session, request)
        except FixtureError as error:
            emit(error_reply(operation, error), output_stream)
            return 2
        except TokenRewardError as error:
            result = error_reply(operation, error)
            rejected = True
        emit(result, output_stream)
    return 1 if rejected else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    startup = parser.add_mutually_exclusive_group(required=True)
    startup.add_argument("--fixture", type=Path)
    startup.add_argument("--init-stdin", action="store_true",
                         help="read one fixture-shaped initialization record before requests")
    parser.add_argument("--requests", required=True, help="UTF-8 JSONL path, or - for stdin")
    args = parser.parse_args(argv)
    if args.init_stdin and args.requests != "-":
        parser.error("--init-stdin requires --requests -")
    try:
        if args.init_stdin:
            # Read raw framing before TextIO's universal-newline conversion.
            record = getattr(sys.stdin, "buffer", sys.stdin).readline()
            if isinstance(record, bytes):
                record = record.decode("utf-8")
            if not record.endswith("\n"):
                raise FixtureError("initialization record requires a terminating newline")
            opening = decode_opening_balances(record)
        else:
            opening = read_opening_balances(args.fixture)
        session = PoolSession(opening)
        requests = (nullcontext(sys.stdin) if args.requests == "-"
                    else Path(args.requests).open(encoding="utf-8"))
        with requests as lines:
            emit(initialized_reply(opening), sys.stdout)
            return run_requests(session, lines, output_stream=sys.stdout)
    except (Exception, KeyboardInterrupt) as error:
        diagnostic(error, sys.stderr)
        return 2


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8", errors="strict")
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    raise SystemExit(main())
