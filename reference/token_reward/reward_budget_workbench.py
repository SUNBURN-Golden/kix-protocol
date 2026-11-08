"""Local, synthetic reward-budget calculations using caller-supplied inputs."""

import argparse
from pathlib import Path
import sys

from reward_fixture import FixtureError, decode_json, exact_fields, validate_json
from token_reward_model import (
    PROVENANCE, UNIT, TokenRewardError, _canonical,
    net_residual_revenue, reward_budget,
)


# Local calculation selectors only; no session or protocol registration.
# Field order also defines the guided prompts. Every field is required.
_DISPATCH = {
    "net_residual_revenue": (
        net_residual_revenue,
        ("gross_revenue", "refundable_window_revenue", "customer_deposit_outlay",
         "organizer_settlement_outlay", "refund_reserve_outlay", "operating_cost",
         "loss_provision"),
        "net_residual",
    ),
    "reward_budget": (
        reward_budget,
        ("cap", "ratio_numerator", "ratio_denominator", "net_residual", "periods"),
        "budget_ceiling",
    ),
}


def dispatch_request(request: dict) -> dict:
    """Validate the envelope, then call the unchanged model exactly once.

    Amounts and types are passed through. Model errors propagate unchanged.
    Local JSON/shape errors raise FixtureError instead.
    """
    validate_json(request)
    exact_fields(request, {"operation", "arguments"}, "request")
    operation = request["operation"]
    if type(operation) is not str or operation not in _DISPATCH:
        raise FixtureError("unsupported calculation operation")
    function, fields, result_key = _DISPATCH[operation]
    exact_fields(request["arguments"], fields, f"{operation} arguments")
    result = function(**request["arguments"])
    return {"operation": operation, "provenance": PROVENANCE, "unit": UNIT,
            "result": {result_key: result}}


def _emit(value, stream):
    print(_canonical(value), file=stream, flush=True)


def _error(operation, error, stream):
    detail = ({"code": error.code} if isinstance(error, TokenRewardError)
              else {"type": type(error).__name__, "message": str(error)})
    _emit({"operation": operation, "provenance": PROVENANCE, "unit": UNIT,
           "error": detail}, stream)
    return 1 if isinstance(error, TokenRewardError) else 2


def run_guided(*, input_stream, output_stream, error_stream) -> int:
    """Collect a complete request and explicit confirmation without retries."""
    operation = None

    def prompt(label):
        print(label, file=output_stream, flush=True)
        line = input_stream.readline()
        if line == "":
            raise FixtureError("incomplete guided input (EOF)")
        return line.removesuffix("\n").removesuffix("\r")

    def calculate(selected, supplied):
        arguments = dict(supplied)
        for field in _DISPATCH[selected][1]:
            if field not in arguments:
                value = decode_json(prompt(f"{field} (JSON scalar):"))
                if type(value) in (dict, list):
                    raise FixtureError(f"{field} requires a JSON scalar")
                arguments[field] = value
        request = {"operation": selected, "arguments": arguments}
        print("Request: " + _canonical(request), file=output_stream, flush=True)
        if prompt("Enter CALCULATE to confirm; any other line declines:") != "CALCULATE":
            print("Declined; no calculation dispatched.", file=output_stream, flush=True)
            return None
        result = dispatch_request(request)
        _emit(result, output_stream)
        return result

    try:
        print("Synthetic POINT_F4 calculations only. All inputs are caller-supplied.\n"
              "Product values: UNDETERMINED — Astra/User.\n"
              "Accounting treatment: UNDETERMINED — User/designated advisers.\n"
              "net_residual already aggregates the selected periods; periods is not a multiplier.",
              file=output_stream, flush=True)
        operation = prompt("Select net_residual_revenue or reward_budget:")
        if operation not in _DISPATCH:
            raise FixtureError("unsupported calculation operation")
        result = calculate(operation, {})
        if result is None or operation != "net_residual_revenue":
            return 0
        choice = prompt("Enter USE_RESIDUAL to copy the displayed residual into a budget; "
                        "any other line ends:")
        if choice != "USE_RESIDUAL":
            print("Ended; no budget calculation dispatched.", file=output_stream, flush=True)
            return 0
        operation = "reward_budget"
        calculate(operation, {"net_residual": result["result"]["net_residual"]})
        return 0
    except (FixtureError, TokenRewardError, OSError, UnicodeError) as error:
        return _error(operation, error, error_stream)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--request", help="one complete JSON document from PATH, or - for stdin")
    modes.add_argument("--guided", action="store_true", help="prompt for all calculation inputs")
    args = parser.parse_args(argv)
    if args.guided:
        return run_guided(input_stream=sys.stdin, output_stream=sys.stdout,
                          error_stream=sys.stderr)
    operation = None
    try:
        document = (sys.stdin.read() if args.request == "-"
                    else Path(args.request).read_text(encoding="utf-8"))
        request = decode_json(document)
        if type(request) is dict and type(request.get("operation")) is str:
            operation = request["operation"]
        _emit(dispatch_request(request), sys.stdout)
        return 0
    except (FixtureError, TokenRewardError, OSError, UnicodeError) as error:
        return _error(operation, error, sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
