"""Bounded, read-only JSON calculation gateway for a future operations agent.

This process never sends money, submits a chain transaction, or writes a ledger.
Its output is a calculation, not provider evidence or execution permission.
"""
import json
import sys

import commerce
from common import Rejected, canonical, require


MAX_INPUT_BYTES = 256 * 1024
EVIDENCE_CLASS = "CALCULATION_ONLY"
ACTION_FIELDS = {
    # simulate_quote passes args directly as the quote request; commerce owns
    # that request's complete schema, including nested policy fields.
    "simulate_quote": None,
    "plan_payments": {
        "quote": dict,
        "legs": list,
        "expected_quote_hash": str,
        "now": int,
    },
    "propose_line_refund": {
        "quote": dict,
        "payment_plan": dict,
        "line_ids": list,
        "expected_plan_hash": str,
    },
}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_constant(_value):
    raise Rejected("NONFINITE_JSON_NUMBER")


def decode_request(payload):
    """Decode exactly one UTF-8 JSON value without ambiguous duplicate keys."""
    require(type(payload) is bytes, "INPUT_MUST_BE_BYTES")
    require(len(payload) <= MAX_INPUT_BYTES, "INPUT_TOO_LARGE")
    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except Rejected:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Rejected("INVALID_JSON") from exc


def dispatch(envelope):
    """Validate a typed request and return a deterministic calculation only."""
    require(type(envelope) is dict, "INVALID_ENVELOPE")
    require(set(envelope) == {"action", "args"}, "INVALID_ENVELOPE_FIELDS")
    action, args = envelope["action"], envelope["args"]
    require(type(action) is str and action in ACTION_FIELDS, "ACTION_NOT_ALLOWED")
    require(type(args) is dict, "INVALID_ARGUMENTS")
    # Enforce the same bound for direct Python callers as for the CLI. The
    # caller cannot send non-JSON values to a lower-level calculation either.
    try:
        encoded = canonical(envelope).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise Rejected("INVALID_JSON_VALUE") from exc
    require(len(encoded) <= MAX_INPUT_BYTES, "INPUT_TOO_LARGE")
    fields = ACTION_FIELDS[action]
    if fields is not None:
        require(set(args) == set(fields), "INVALID_ARGUMENT_FIELDS")
        for name, expected_type in fields.items():
            require(type(args[name]) is expected_type, "INVALID_ARGUMENT_TYPE")
    if action == "simulate_quote":
        result = commerce.build_quote(args)
    elif action == "plan_payments":
        result = commerce.plan_payments(**args)
    else:
        result = commerce.propose_line_refund(**args)
    return {"ok": True, "evidenceClass": EVIDENCE_CLASS, "result": result}


def main():
    try:
        # Read one byte beyond the bound to distinguish oversized input without
        # consuming an unbounded pipe. There is one request per invocation.
        response = dispatch(decode_request(sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)))
        status = 0
    except Rejected as exc:
        response = {"ok": False, "evidenceClass": EVIDENCE_CLASS, "error": str(exc)}
        status = 2
    sys.stdout.write(canonical(response) + "\n")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
