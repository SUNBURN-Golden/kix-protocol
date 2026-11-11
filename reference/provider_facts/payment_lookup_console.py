"""One-shot terminal guide to an explicitly selected synthetic payment fixture.

Analog, NOT Toss. Observations only; no payment decision or economic application.
"""

import argparse
import json
import sys
from dataclasses import asdict

import payment_lookup_cli
from provider_facts import PROVENANCE, OperationRef


def _write(stream, text):
    if stream.write(text) != len(text):
        raise OSError("short terminal write")
    stream.flush()


def _json(value):
    # Escape terminal controls and preserve decoded strings and integer precision.
    return json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False)


def _diagnostic(error, stream):
    try:
        _write(stream, "console_error=" + _json({
            "type": type(error).__name__, "message": str(error),
        }) + "\nSession ended; no automatic lookup or retry.\n")
    except (Exception, KeyboardInterrupt):
        pass


def run_console(bindings, routes, *, input_stream, output_stream, error_stream) -> int:
    """Preview a binding locally, then forward at most one literal submission."""
    def prompt(label):
        _write(output_stream, label + "\n")
        line = input_stream.readline()
        if line == "":
            raise EOFError("terminal input ended")
        # Remove only one line ending. Whitespace in identifiers is never trimmed.
        if line.endswith("\n"):
            line = line[:-1]
            if line.endswith("\r"):
                line = line[:-1]
        return line

    try:
        _write(output_stream, PROVENANCE + " — Analog, NOT Toss.\n"
               + payment_lookup_cli.LIMITATIONS + "\n"
               "Provider authentication and merchant scope: UNDETERMINED — Toss/User.\n"
               "Observations do not decide payment/refund completion, issuance or UNKNOWN release.\n")
        operation = OperationRef(
            provider=prompt("provider"), account=prompt("account"), operation=prompt("operation"),
        )
        payment = bindings.lookup(operation)
        _write(output_stream, "preview=" + _json({
            "operation_ref": asdict(operation),
            "payment_ref": payment.as_dict() if payment is not None else None,
        }) + "\n")
        if prompt("Type literal SUBMIT to look up once; anything else declines") != "SUBMIT":
            _write(output_stream, "Declined; no lookup performed.\n")
            return 0
        result = payment_lookup_cli.lookup_once(bindings, routes, operation)
        # Retain the complete returned dictionary before any rendering can fail.
        _write(output_stream, "result=" + _json(result) + "\n")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, error_stream)
        return 2


def main(argv=None) -> int:
    try:
        parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
        parser.add_argument("--fixture", required=True, action="append",
                            help="explicit local synthetic JSON fixture; no default")
        args = parser.parse_args(argv)
        if len(args.fixture) != 1:
            parser.error("--fixture must appear exactly once")
        bindings, routes = payment_lookup_cli.load_fixture(args.fixture[0])
        return run_console(bindings, routes, input_stream=sys.stdin,
                           output_stream=sys.stdout, error_stream=sys.stderr)
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
