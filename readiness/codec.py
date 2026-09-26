"""Canonical JSON for the readiness journal. Not a protocol encoding."""

from __future__ import annotations

import hashlib
import json


class CodecError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def canonical_json(value):
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CodecError('JOURNAL_RECORD') from exc


def receipt_digest(receipt):
    return hashlib.sha256(canonical_json(receipt).encode('utf-8')).hexdigest()


def strict_loads(payload):
    try:
        text = payload.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise CodecError('JOURNAL_CORRUPT') from exc
    if text.startswith('\ufeff'):
        raise CodecError('JOURNAL_CORRUPT')
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise CodecError('JOURNAL_CORRUPT') from exc


class _DuplicateKey(ValueError):
    pass


def _reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise _DuplicateKey()
        obj[key] = value
    return obj


def _reject_constant(_value):
    raise ValueError('non-standard JSON number')
