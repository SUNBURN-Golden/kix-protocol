"""KIX Canonical Encoding v1 (CE1), independent of legacy common.digest.

CE1 encodes compact UTF-8 JSON with lexically sorted visible ASCII object keys
(1..128 characters); arrays retain order. Strings use the pinned Unicode 15.0
assigned scalar repertoire and must already be NFC: normalization is never
implicit. Unassigned scalars and noncharacters are excluded so host Unicode
version upgrades cannot change acceptance. Only safe JSON integers are
numbers; monetary atoms remain canonical decimal strings in their schemas.

Hashes are SHA-256(b"KIX-CE1\\0" + ASCII(domain) + b"\\0" + CE1(value)).
Domains and machine identifiers use the same bounded ASCII grammar. CE1 is an
encoding/hash contract, not a signature, provenance or execution authorization.
"""
import hashlib
import json
from bisect import bisect_right
from pathlib import Path
import re
import unicodedata

from common import Rejected, require


VERSION = "kix:canonical-encoding:1"
UNICODE_VERSION = "15.0.0"
UNICODE_TABLE_SHA256 = "7a4a0f8ea869cca7bc3d88d93d85d3f104b52a807bb4c112171c8d232c09f90c"
MAX_SAFE_INTEGER = 2**53 - 1
MAX_INPUT_BYTES = 256 * 1024
MAX_DEPTH = 64
HASH_PREFIX = b"KIX-CE1\x00"
_MACHINE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9:_./-]*\Z")
_REPERTOIRE_BYTES = (Path(__file__).resolve().parent
                     / "fixtures/unicode15_assigned_ranges.json").read_bytes()
if hashlib.sha256(_REPERTOIRE_BYTES).hexdigest() != UNICODE_TABLE_SHA256:
    raise RuntimeError("CE1 Unicode repertoire integrity mismatch")
_REPERTOIRE = json.loads(_REPERTOIRE_BYTES)
if _REPERTOIRE["unicodeVersion"] != UNICODE_VERSION:
    raise RuntimeError("Unsupported CE1 Unicode repertoire")
_RANGES = _REPERTOIRE["ranges"]
_RANGE_STARTS = [start for start, _end in _RANGES]
if tuple(map(int, unicodedata.unidata_version.split("."))) < (15, 0, 0):
    raise RuntimeError("CE1 requires Unicode normalization tables >= 15.0.0")


def _assigned_scalar(codepoint):
    index = bisect_right(_RANGE_STARTS, codepoint) - 1
    return index >= 0 and codepoint <= _RANGES[index][1]


def machine_id(value, max_length=128):
    require(type(max_length) is int and 1 <= max_length <= 256, "INVALID_ID_BOUND")
    require(type(value) is str and 1 <= len(value) <= max_length
            and _MACHINE_ID.fullmatch(value), "INVALID_CANONICAL_ID")
    return value


def _string(value):
    require(not any(0xD800 <= ord(char) <= 0xDFFF for char in value),
            "INVALID_UNICODE_SCALAR")
    require(all(_assigned_scalar(ord(char)) for char in value),
            "OUTSIDE_CE1_UNICODE_REPERTOIRE")
    require(unicodedata.normalize("NFC", value) == value, "NON_NFC_STRING")
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _encode(value, depth):
    require(depth <= MAX_DEPTH, "MAX_CANONICAL_DEPTH")
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        require(abs(value) <= MAX_SAFE_INTEGER, "UNSAFE_JSON_INTEGER")
        return str(value)
    if type(value) is str:
        return _string(value)
    if type(value) is list:
        return "[" + ",".join(_encode(item, depth + 1) for item in value) + "]"
    if type(value) is dict:
        for key in value:
            require(type(key) is str and 1 <= len(key) <= 128
                    and all(0x21 <= ord(char) <= 0x7E for char in key),
                    "INVALID_CANONICAL_KEY")
        return "{" + ",".join(_string(key) + ":" + _encode(value[key], depth + 1)
                                for key in sorted(value)) + "}"
    raise Rejected("INVALID_CANONICAL_VALUE")


def canonical(value):
    try:
        result = _encode(value, 0)
    except RecursionError as exc:
        raise Rejected("MAX_CANONICAL_DEPTH") from exc
    require(len(result.encode("utf-8")) <= MAX_INPUT_BYTES, "INPUT_TOO_LARGE")
    return result


def canonical_bytes(value):
    return canonical(value).encode("utf-8")


def digest(domain, value):
    machine_id(domain)
    return hashlib.sha256(HASH_PREFIX + domain.encode("ascii") + b"\x00"
                          + canonical_bytes(value)).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _integer_token(token):
    require(token != "-0", "NEGATIVE_ZERO_JSON_NUMBER")
    require(len(token.lstrip("-")) <= 16, "UNSAFE_JSON_INTEGER")
    result = int(token)
    require(abs(result) <= MAX_SAFE_INTEGER, "UNSAFE_JSON_INTEGER")
    return result


def _reject_float(_token):
    raise Rejected("NON_INTEGER_JSON_NUMBER")


def _reject_constant(_token):
    raise Rejected("NONFINITE_JSON_NUMBER")


def decode_json(payload):
    """Parse bounded UTF-8 JSON without lossy integers, duplicate keys or -0.

    Whitespace and equivalent JSON escapes are accepted on input. The returned
    value is validated against CE1; callers hash canonical_bytes, never input.
    Object-specific nullability and fields belong to the consuming schema.
    """
    require(type(payload) is bytes, "INPUT_MUST_BE_BYTES")
    require(len(payload) <= MAX_INPUT_BYTES, "INPUT_TOO_LARGE")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_int=_integer_token, parse_float=_reject_float,
                           parse_constant=_reject_constant)
        canonical(value)
        return value
    except Rejected:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Rejected("INVALID_JSON") from exc
