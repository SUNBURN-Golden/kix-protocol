"""Calculate one synthetic supply request from a UTF-8 JSON file or stdin."""

import argparse
from pathlib import Path
import sys

from reward_fixture import FixtureError, decode_json
from supply_reconciliation import OPERATIONS, dispatch_request, supply_output
from token_reward_model import TokenRewardError, _canonical


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True,
                        help="one UTF-8 JSON document path, or - for stdin")
    args = parser.parse_args(argv)
    operation = None
    try:
        if args.request == "-":
            text = (sys.stdin.buffer.read().decode("utf-8")
                    if hasattr(sys.stdin, "buffer") else sys.stdin.read())
        else:
            text = Path(args.request).read_text(encoding="utf-8")
        request = decode_json(text)
        if type(request) is dict:
            candidate = request.get("operation")
            if type(candidate) is str and candidate in OPERATIONS:
                operation = candidate
        output = dispatch_request(request)
        status = 0
    except TokenRewardError as error:
        output = supply_output(operation, error={"code": error.code})
        status = 1
    except (FixtureError, OSError, UnicodeError) as error:
        # Decoder messages can contain duplicate lone-surrogate keys. Keep
        # diagnostics themselves valid UTF-8 JSON, as in collateral_cli.
        message = str(error).encode("utf-8", errors="backslashreplace").decode("utf-8")
        output = supply_output(operation, error={"type": type(error).__name__,
                                                "message": message})
        status = 2
    print(_canonical(output), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
