"""Deterministic fixture encoding. Not a cross-language signing standard."""
import hashlib
import json


class Rejected(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Rejected(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def positive(n):
    require(type(n) is int and 0 < n <= 10**12, "INVALID_AMOUNT")
    return n


def nonnegative(n):
    require(type(n) is int and 0 <= n <= 10**12, "INVALID_NONNEGATIVE_AMOUNT")
    return n


def ident(value):
    require(isinstance(value, str) and 0 < len(value) <= 100 and value.strip() == value, "INVALID_ID")
    return value


def external_id(value):
    require(isinstance(value, str) and 0 < len(value) <= 200 and value.strip() == value, "INVALID_EXTERNAL_ID")
    return value
