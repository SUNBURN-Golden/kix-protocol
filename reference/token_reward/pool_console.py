"""Guided, explicitly confirmed synthetic POINT_F4 pool accounting."""

import argparse
from pathlib import Path
import re
import sys

from pool_cli import diagnostic, emit
from pool_client import PoolClient, validate_cleanup_timeout
from pool_session import (NOTICE, PoolSession, dispatch_request, error_reply,
                          initialized_reply, read_opening_balances)
from reward_fixture import FixtureError, decode_json, validate_json
from token_reward_model import POOLS, TokenRewardError, _canonical


_FIELDS = {"credit": ("pool", "amount", "source_ref"),
           "spend": ("pool", "amount", "program_ref"), "view": ()}
_GUIDED = object()


def _parse_amount(raw):
    if re.fullmatch(r"[+-]?[0-9]+", raw) is None:
        raise FixtureError("amount requires an explicit decimal integer")
    try:
        return int(raw)
    except ValueError as error:
        raise FixtureError("amount integer is too long") from error


def _interact(opening_balances, *, input_stream, output_stream, error_stream, start, dispatch):
    """Preview and flush before construction/mutation; terminal failures fence use.

    A model mutation can have completed before an output failure. No rollback or
    automatic retry is implied. A decline is any confirmation other than SUBMIT.
    """
    rejected = False

    def prompt(label):
        print(label + ": ", end="", file=output_stream, flush=True)
        line = input_stream.readline()
        if line == "":
            raise EOFError("input ended; no further dispatch")
        raw = line.removesuffix("\n").removesuffix("\r")
        validate_json(raw)
        return raw

    def preview(request):
        print("PREVIEW " + _canonical(request), file=output_stream, flush=True)
        return prompt("Literal SUBMIT confirms; anything else declines") == "SUBMIT"

    try:
        if opening_balances is not _GUIDED:
            validate_json(opening_balances)
            opening_balances = decode_json(_canonical(opening_balances))
        print(NOTICE + "\n"
              "token_issued, onchain_recorded, funds_executed, krw_paid, chain_finality, "
              "durable, legal_authority remain false.\n"
              "Pool balances, funding policy and approval values: UNDETERMINED — Astra/User.\n"
              "Accounting and legal treatment: UNDETERMINED — User/designated advisers.\n"
              "Repeated references append again when accepted; no deduplication or receipts.",
              file=output_stream, flush=True)
        if opening_balances is _GUIDED:
            opening_balances = {
                pool: _parse_amount(prompt(pool + " opening balance (signed decimal integer)"))
                for pool in POOLS
            }
        if not preview({"operation": "initialize", "arguments": {"opening_balances": opening_balances}}):
            print("Initialization declined; no session constructed.", file=output_stream, flush=True)
            return 0
        session, acknowledgement = start(opening_balances)
        emit(acknowledgement, output_stream)
        while True:
            action = prompt("Action (credit, spend, view, quit)")
            if action == "quit":
                return 1 if rejected else 0
            if action not in _FIELDS:
                raise FixtureError("unsupported pool operation")
            arguments = {}
            for name in _FIELDS[action]:
                raw = prompt(name + (" (signed decimal integer)" if name == "amount" else " (verbatim string)"))
                if name == "amount":
                    arguments[name] = _parse_amount(raw)
                else:
                    arguments[name] = raw
            request = {"operation": action, "arguments": arguments}
            if action != "view" and not preview(request):
                print("Request declined; no dispatch.", file=output_stream, flush=True)
                continue
            try:
                result = dispatch(session, request)
            except TokenRewardError as error:
                result = error_reply(action, error)
                rejected = True
            emit(result, output_stream)
            if "error" in result:
                if "type" in result["error"]:
                    return 2
                rejected = True
    except (Exception, KeyboardInterrupt) as error:
        diagnostic(error, error_stream)
        return 2


def run_console(opening_balances=_GUIDED, *, input_stream, output_stream, error_stream,
                fixture=None, cleanup_timeout=None):
    """Use a child only when explicitly selected by fixture and cleanup_timeout.

    All preview/confirmation paths share _interact; start runs only after SUBMIT.
    Every post-launch exit closes the owned child, including output failures.
    """
    client = None

    def start(balances):
        nonlocal client
        if fixture is None:
            return PoolSession(balances), initialized_reply(balances)
        client = PoolClient.launch(fixture, expected_opening_balances=balances,
                                   cleanup_timeout=cleanup_timeout)
        return client, client.initialized_reply

    def dispatch(session, request):
        return session.request(request) if fixture is not None else dispatch_request(session, request)

    status = 2
    try:
        if fixture is not None:
            if opening_balances is _GUIDED:
                raise FixtureError("subprocess mode requires fixture opening balances")
            validate_cleanup_timeout(cleanup_timeout)
        elif cleanup_timeout is not None:
            raise FixtureError("cleanup_timeout requires subprocess mode")
        status = _interact(opening_balances, input_stream=input_stream, output_stream=output_stream,
                           error_stream=error_stream, start=start, dispatch=dispatch)
    except (Exception, KeyboardInterrupt) as error:
        diagnostic(error, error_stream)
    finally:
        if client is not None:
            try:
                code = client.close()
                if status != 2 and code != (1 if client.domain_refused else 0):
                    raise RuntimeError(f"unexpected pool child exit: {code}")
            except (Exception, KeyboardInterrupt) as error:
                diagnostic(error, error_stream)
                status = 2
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fixture", type=Path)
    mode.add_argument("--guided-init", action="store_true",
                      help="explicitly enter all five synthetic opening balances")
    parser.add_argument("--mode", choices=("in-process", "subprocess"), default="in-process")
    parser.add_argument("--cleanup-timeout", type=float, help="subprocess cleanup only, finite positive seconds")
    args = parser.parse_args(argv)
    try:
        if args.mode == "subprocess":
            if args.guided_init:
                raise FixtureError("subprocess mode requires --fixture")
            validate_cleanup_timeout(args.cleanup_timeout)
        elif args.cleanup_timeout is not None:
            raise FixtureError("--cleanup-timeout requires --mode subprocess")
        opening = _GUIDED if args.guided_init else read_opening_balances(args.fixture)
    except (Exception, KeyboardInterrupt) as error:
        diagnostic(error, sys.stderr)
        return 2
    return run_console(opening, input_stream=sys.stdin, output_stream=sys.stdout, error_stream=sys.stderr,
                       fixture=args.fixture if args.mode == "subprocess" else None,
                       cleanup_timeout=args.cleanup_timeout)


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8", errors="strict")
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    raise SystemExit(main())
