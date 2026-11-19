"""Strict local JSON input; registry semantics belong to the existing mock."""

import json
import math
from pathlib import Path

from delegation_session import DelegationSession
from ai_delegation_mock import PROVENANCE


class FixtureError(ValueError):
    """Malformed local input; not a protocol/domain error code."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise FixtureError("non-finite JSON number")
    return number


def _constant(value):
    raise FixtureError(f"non-finite JSON constant: {value}")


def validate_json(value):
    """Also protect importable dispatch from non-JSON Python values."""
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
        value = json.loads(text, object_pairs_hook=_object, parse_constant=_constant,
                           parse_float=_finite_float)
        validate_json(value)
        return value
    except (ValueError, TypeError, RecursionError) as error:
        raise FixtureError(str(error)) from error


def exact_fields(value, required, context, optional=()):
    if (type(value) is not dict or not set(required) <= set(value)
            or not set(value) <= set(required) | set(optional)):
        raise FixtureError(
            f"{context} requires: {', '.join(sorted(required))}; "
            f"optional: {', '.join(sorted(optional))}")


def validate_fixture(fixture):
    """Transport shape only; registry semantics remain in AiDelegationMock."""
    validate_json(fixture)
    exact_fields(fixture, {"fixture_version", "provenance", "human_principals", "ai_agents"}, "fixture")
    if type(fixture["fixture_version"]) is not int or fixture["fixture_version"] != 1:
        raise FixtureError("unsupported fixture_version")
    if fixture["provenance"] != PROVENANCE:
        raise FixtureError(f"fixture provenance must be {PROVENANCE}")


def session_from_fixture(fixture) -> DelegationSession:
    validate_fixture(fixture)
    return DelegationSession(fixture["human_principals"], fixture["ai_agents"])


def load_fixture(path: str | Path) -> DelegationSession:
    return session_from_fixture(decode_json(Path(path).read_text(encoding="utf-8")))
