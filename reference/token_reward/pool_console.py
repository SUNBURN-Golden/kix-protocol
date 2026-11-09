"""Guided, explicitly confirmed synthetic POINT_F4 pool accounting."""

import argparse
from pathlib import Path
import re
import sys

from pool_cli import diagnostic, emit
from pool_session import (NOTICE, PoolSession, dispatch_request, error_reply,
                          initialized_reply, read_opening_balances)
from reward_fixture import FixtureError, validate_json
from token_reward_model import TokenRewardError, _canonical


_FIELDS = {"credit": ("pool", "amount", "source_ref"),
           "spend": ("pool", "amount", "program_ref"), "view": ()}


def run_console(opening_balances, *, input_stream, output_stream, error_stream):
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
        validate_json(opening_balances)
        print(NOTICE + "\n"
              "token_issued, onchain_recorded, funds_executed, krw_paid, chain_finality, "
              "durable, legal_authority remain false.\n"
              "Pool balances, funding policy and approval values: UNDETERMINED — Astra/User.\n"
              "Accounting and legal treatment: UNDETERMINED — User/designated advisers.\n"
              "Repeated references append again when accepted; no deduplication or receipts.",
              file=output_stream, flush=True)
        if not preview({"operation": "initialize", "arguments": {"opening_balances": opening_balances}}):
            print("Initialization declined; no session constructed.", file=output_stream, flush=True)
            return 0
        session = PoolSession(opening_balances)
        emit(initialized_reply(opening_balances), output_stream)
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
                    if re.fullmatch(r"[+-]?[0-9]+", raw) is None:
                        raise FixtureError("amount requires an explicit decimal integer")
                    try:
                        arguments[name] = int(raw)
                    except ValueError as error:
                        raise FixtureError("amount integer is too long") from error
                else:
                    arguments[name] = raw
            request = {"operation": action, "arguments": arguments}
            if action != "view" and not preview(request):
                print("Request declined; no dispatch.", file=output_stream, flush=True)
                continue
            try:
                result = dispatch_request(session, request)
            except TokenRewardError as error:
                result = error_reply(action, error)
                rejected = True
            emit(result, output_stream)
    except (Exception, KeyboardInterrupt) as error:
        diagnostic(error, error_stream)
        return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        opening = read_opening_balances(args.fixture)
    except (Exception, KeyboardInterrupt) as error:
        diagnostic(error, sys.stderr)
        return 2
    return run_console(opening, input_stream=sys.stdin, output_stream=sys.stdout, error_stream=sys.stderr)


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8", errors="strict")
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
    raise SystemExit(main())
