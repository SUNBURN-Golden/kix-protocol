"""One local synthetic collateral calculation: JSON file/stdin or guided input."""

import argparse
from pathlib import Path
import re
import sys

from collateral_assessment import OPERATION, assessment_output, dispatch_request
from reward_fixture import FixtureError, decode_json
from token_reward_model import TokenRewardError, _canonical


def _emit(value):
    print(_canonical(value), flush=True)


def _prompt(label):
    print(label, file=sys.stderr, flush=True)
    line = sys.stdin.readline()
    if not line:
        raise FixtureError("incomplete guided input")
    return line.rstrip("\r\n")


def _integer(label):
    text = _prompt(label)
    if re.fullmatch(r"-?(0|[1-9][0-9]*)", text) is None:
        raise FixtureError("enter an integer in decimal JSON notation")
    try:
        return int(text)
    except ValueError as error:
        raise FixtureError("integer input is too long") from error


def _guided_request():
    """Compose and preview only; no model call before explicit confirmation."""
    print(assessment_output()["notice"], file=sys.stderr, flush=True)
    liability = _integer("Synthetic KRW liability (integer; required):")
    count = _integer("Collateral item count (nonnegative integer; 0 means empty):")
    if count < 0:
        raise FixtureError("collateral item count must be nonnegative")
    items = []
    for index in range(count):
        kind = _prompt(f"Item {index + 1} kind (KRW_GUARANTEE, ESCROW, TOKEN):")
        if not kind:
            raise FixtureError("item kind is required")
        amount = _integer(f"Item {index + 1} amount (integer; required):")
        items.append({"kind": kind, "amount": amount})
    request = {"operation": OPERATION,
               "arguments": {"liability_krw": liability, "collateral_items": items}}
    print("Proposal: " + _canonical(request), file=sys.stderr, flush=True)
    if _prompt("Type CALCULATE to calculate once; anything else discards:") != "CALCULATE":
        return None
    return request


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--request", help="one UTF-8 JSON document path, or - for stdin")
    mode.add_argument("--guided", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.guided:
            if hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(encoding="utf-8", errors="strict")
            request = _guided_request()
            if request is None:
                _emit(assessment_output(cancelled=True))
                return 0
        else:
            if args.request == "-":
                text = (sys.stdin.buffer.read().decode("utf-8")
                        if hasattr(sys.stdin, "buffer") else sys.stdin.read())
            else:
                text = Path(args.request).read_text(encoding="utf-8")
            request = decode_json(text)
        result = dispatch_request(request)
    except TokenRewardError as error:
        _emit(assessment_output(error={"code": error.code}))
        return 1
    except (FixtureError, OSError, UnicodeError, KeyboardInterrupt) as error:
        message = "guided input interrupted" if isinstance(error, KeyboardInterrupt) else str(error)
        # A duplicate malformed JSON key can reach the decoder's error message
        # before Unicode validation. Keep even that diagnostic valid UTF-8.
        message = message.encode("utf-8", errors="backslashreplace").decode("utf-8")
        _emit(assessment_output(error={"type": type(error).__name__, "message": message}))
        return 2
    _emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
