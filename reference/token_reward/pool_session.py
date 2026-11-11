"""Process-local synthetic POINT_F4 accounting over the unchanged PoolLedger."""

from pathlib import Path

from reward_fixture import FixtureError, decode_json, exact_fields, validate_json
from token_reward_model import ALWAYS_FALSE_FLAGS, PROVENANCE, UNIT, PoolLedger, TokenRewardError


NOTICE = "Synthetic POINT_F4 simulation only; process-local, non-transferable; exit loses state."


class PoolSession:
    """One ledger; references are model inputs, never deduplication keys."""

    def __init__(self, opening_balances):
        self._ledger = PoolLedger(opening_balances)

    def credit(self, pool, amount, source_ref):
        return self._ledger.credit(pool, amount, source_ref)

    def spend(self, pool, amount, program_ref):
        return self._ledger.spend(pool, amount, program_ref)

    def view(self):
        return self._ledger.view()


# Local selectors, not protocol commands. No arbitrary attribute dispatch.
_DISPATCH = {
    "credit": (PoolSession.credit, {"pool", "amount", "source_ref"}),
    "spend": (PoolSession.spend, {"pool", "amount", "program_ref"}),
    "view": (PoolSession.view, set()),
}


def envelope(operation, key, value):
    return {"operation": operation, "provenance": PROVENANCE, "unit": UNIT,
            "notice": NOTICE, **{flag: False for flag in ALWAYS_FALSE_FLAGS}, key: value}


def error_reply(operation, error):
    detail = ({"code": error.code} if isinstance(error, TokenRewardError)
              else {"type": type(error).__name__, "message": str(error)})
    return envelope(operation, "error", detail)


def initialized_reply(opening_balances):
    # No implicit view; the acknowledgement describes caller inputs only.
    return envelope("initialize", "initialized", {"opening_balances": opening_balances})


def decode_opening_balances(text):
    """Decode a fixture record; domain validation remains in the constructor."""
    fixture = decode_json(text)
    exact_fields(fixture, {"fixture_version", "provenance", "opening_balances"}, "fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != PROVENANCE:
        raise FixtureError(f"fixture provenance must be {PROVENANCE}")
    # Five-pool shape and all amounts belong to the unchanged constructor.
    return fixture["opening_balances"]


def read_opening_balances(path):
    """Read only; never construct reward machinery or a ledger before confirmation."""
    return decode_opening_balances(Path(path).read_text(encoding="utf-8"))


def dispatch_request(session, request):
    """Validate the whole envelope, then call exactly one selected session method."""
    validate_json(request)
    exact_fields(request, {"operation", "arguments"}, "request")
    operation = request["operation"]
    if type(operation) is not str or operation not in _DISPATCH:
        raise FixtureError("unsupported pool operation")
    method, fields = _DISPATCH[operation]
    arguments = request["arguments"]
    exact_fields(arguments, fields, f"{operation} arguments")
    return envelope(operation, "view", method(session, **arguments))
