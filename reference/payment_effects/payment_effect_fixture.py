"""Strict synthetic fixture input for the local payment effect desk.

A fixture is an explicit, ordered list of already-published Core commands. It is
validated structurally before any Core is created, then every command is applied
through ``Core.execute``. No test ``Harness`` defaults, state injection or value
inference is used.
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

if __package__:
    from .payment_effect_session import Core, PaymentEffectSession
else:
    from payment_effect_session import Core, PaymentEffectSession


class FixtureError(ValueError):
    """Malformed local input; not a protocol/domain error code."""


# Only the lifecycle commands needed to construct the documented synthetic
# balances, tickets, trades and effect obligations. Nothing is dispatched.
SETUP_ACTIONS = frozenset(
    {
        "create_event",
        "prepare_trade",
        "accept_trade",
        "capture",
        "settle_capture",
        "commit_trade",
        "cancel_event",
        "complete_event",
    }
)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _finite_float(value):
    # Even JSON exponent syntax can overflow Python's float into infinity.
    number = float(value)
    if not math.isfinite(number):
        raise FixtureError("non-finite JSON number")
    return number


def _constant(value):
    raise FixtureError(f"non-finite JSON constant: {value}")


def validate_json(value):
    """Reject non-JSON Python values, lone surrogates and excessive nesting."""

    def walk(item):
        if item is None or type(item) in (bool, int):
            return
        if type(item) is str:
            # Reject lone surrogates before hashing or emitting UTF-8.
            item.encode("utf-8")
            return
        if type(item) is float and math.isfinite(item):
            return
        if type(item) is list:
            for child in item:
                walk(child)
            return
        if type(item) is dict and all(type(key) is str for key in item):
            for key, child in item.items():
                walk(key)
                walk(child)
            return
        raise FixtureError("value must be finite JSON data")

    try:
        walk(value)
    except (RecursionError, UnicodeError) as error:
        raise FixtureError("invalid JSON nesting or Unicode") from error


def decode_json(text):
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object,
            parse_constant=_constant,
            parse_float=_finite_float,
        )
        validate_json(value)
        return value
    except FixtureError:
        raise
    except (ValueError, TypeError, RecursionError) as error:
        raise FixtureError(str(error)) from error


def exact_fields(value, required, context, optional=()):
    if (
        type(value) is not dict
        or not set(required) <= set(value)
        or not set(value) <= set(required) | set(optional)
    ):
        raise FixtureError(
            f"{context} requires: {', '.join(sorted(required))}; "
            f"optional: {', '.join(sorted(optional))}"
        )


def validate_fixture(fixture):
    """Check the local document shape without creating a Core or session."""
    validate_json(fixture)
    exact_fields(fixture, {"fixture_version", "provenance", "setup"}, "fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != "synthetic":
        raise FixtureError("fixture provenance must be synthetic")

    setup = fixture["setup"]
    if type(setup) is not list or not setup:
        raise FixtureError("setup must be a nonempty array")
    operation_ids = set()
    for position, command in enumerate(setup):
        exact_fields(
            command, {"operationId", "actor", "action", "body"}, "setup command"
        )
        for field in ("operationId", "actor", "action"):
            if type(command[field]) is not str:
                raise FixtureError(f"setup command {position} {field} must be a string")
        if command["action"] not in SETUP_ACTIONS:
            raise FixtureError("unsupported setup action: " + command["action"])
        if type(command["body"]) is not dict:
            raise FixtureError("setup command body must be an object")
        if command["operationId"] in operation_ids:
            raise FixtureError(
                "duplicate setup operationId: " + command["operationId"]
            )
        operation_ids.add(command["operationId"])


def session_from_fixture(fixture):
    """Build a fresh real Core, publish it only after every setup command succeeds."""
    validate_fixture(fixture)
    core = Core(":memory:")
    try:
        for command in fixture["setup"]:
            core.execute(
                command["operationId"],
                command["actor"],
                command["action"],
                copy.deepcopy(command["body"]),
            )
    except BaseException:
        core.db.close()
        raise
    return PaymentEffectSession(core)


def load_fixture(path):
    """Read one UTF-8 fixture and return an initialized local session."""
    text = Path(path).read_text(encoding="utf-8")
    return session_from_fixture(decode_json(text))
