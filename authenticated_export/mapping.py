"""Pinned local type mapping for the stage-5 durable rows (contract §5).

KIX ID = fixed binary(16); asset/hash = fixed binary(32). Here the sha256
columns and the sha256-derived ids are binary(32) carried as lowercase hex,
and the 16-byte event alias is binary(16) carried as lowercase hex; widths are
checked, never widened or truncated. amount_u128 stays decimal text
(Wide128-lossless): never a float, never narrowed to a signed integer.
created_ms / received_ms / at_ms are epoch milliseconds, unit explicit. The
inbox occurred-time text and offset inside fact_json are preserved verbatim;
no time zone is assumed. Fast64 is not used: no execution profile is approved.

This pin is independent of durable/ (which imports psycopg); the PG-bound
suite cross-checks it against durable.schema column-for-column. No Arrow
mapping is materialized in this node; the descriptor below is the pinned
PostgreSQL-to-export mapping version that a later Arrow node must bind.
"""

from __future__ import annotations

import hashlib
import re

from readiness.codec import CodecError, canonical_json, strict_loads

from authenticated_export import TYPE_MAPPING_VERSION
from authenticated_export.errors import ExportError

U128_MAX = (1 << 128) - 1
CRC32_MAX = (1 << 32) - 1

# Column kinds. 'text' is a non-empty string; 'json-text' is a non-empty
# string that parses as strict JSON and is preserved verbatim (never
# re-serialized); 'blob-hex' is lowercase hex of a non-empty byte string.
TEXT = 'text'
JSON_TEXT = 'json-text'
INT = 'int'
BOOL = 'bool'
EPOCH_MS = 'epoch-ms-int'
U128_TEXT = 'u128-decimal-text'
BINARY32_HEX = 'binary(32)-hex'
BINARY16_HEX = 'binary(16)-hex'
BLOB_HEX = 'blob-hex'
VOCAB = 'vocab:'

_HEX32 = re.compile(r'^[0-9a-f]{64}$')
_HEX16 = re.compile(r'^[0-9a-f]{32}$')
_HEX_BLOB = re.compile(r'^(?:[0-9a-f]{2})+$')
# Canonical u128 decimal text: no leading zeros, at most 40 digits.
_AMOUNT = re.compile(r'^(?:0|[1-9][0-9]{0,39})$')

# The stage-5 business tables, in durable.schema.CRC_TABLES order. The pin
# mirrors durable/schema.py; the PG suite asserts the two agree.
TABLES = (
    'command_result', 'slot_hold', 'minimal_order', 'outbox_intent', 'outbox_attempt',
    'observation', 'ledger', 'event_alias', 'inbox_delivery', 'inbox_item', 'inbox_state',
)

PRIMARY_KEYS = {
    'command_result': ('command_id',),
    'slot_hold': ('show_id', 'slot'),
    'minimal_order': ('order_id',),
    'outbox_intent': ('intent_id',),
    'outbox_attempt': ('intent_id', 'attempt_no', 'phase'),
    'observation': ('observation_id',),
    'ledger': ('entry_id',),
    'event_alias': ('scope_key', 'fact_key'),
    'inbox_delivery': ('delivery_id',),
    'inbox_item': ('item_id',),
    'inbox_state': ('item_id', 'seq'),
}

# Vocabulary pins for the stage-5 fixture semantics. These are the values the
# unchanged durable/ layer writes; anything else fails closed.
VOCABULARIES = {
    'outcome': (
        'new_success', 'replayed', 'conflict_retained', 'business_rejected',
        'capacity', 'unknown', 'error',
    ),
    'relation': ('FIRST', 'SAME_FACT', 'CONFLICT'),
    'state': ('RECEIVED', 'APPLIED', 'UNMATCHED', 'DUPLICATE'),
    'phase': ('ATTEMPTING', 'OUTCOME'),
    'budget_class': ('inflow', 'completion', 'observation', 'cancel', 'recovery'),
    'intent_kind': ('FIXTURE_NOT_DISPATCHED',),
}

_COLUMNS = {
    'command_result': {
        'command_id': TEXT, 'payload_sha256': BINARY32_HEX, 'first_result': JSON_TEXT,
        'outcome': VOCAB + 'outcome', 'amount_u128': U128_TEXT, 'admitted_bytes': INT,
        'created_ms': EPOCH_MS, 'crc': INT,
    },
    'slot_hold': {
        'show_id': TEXT, 'slot': TEXT, 'command_id': TEXT, 'crc': INT,
    },
    'minimal_order': {
        'order_id': TEXT, 'command_id': TEXT, 'amount_u128': U128_TEXT, 'crc': INT,
    },
    'outbox_intent': {
        'intent_id': TEXT, 'command_id': TEXT, 'kind': VOCAB + 'intent_kind',
        'payload_sha256': BINARY32_HEX, 'created_ms': EPOCH_MS, 'crc': INT,
    },
    'outbox_attempt': {
        'intent_id': TEXT, 'attempt_no': INT, 'phase': VOCAB + 'phase',
        'result': JSON_TEXT, 'at_ms': EPOCH_MS, 'crc': INT,
    },
    'observation': {
        'observation_id': TEXT, 'command_id': TEXT, 'payload_sha256': BINARY32_HEX,
        'nbytes': INT, 'created_ms': EPOCH_MS, 'crc': INT,
    },
    'ledger': {
        'entry_id': TEXT, 'budget_class': VOCAB + 'budget_class', 'nbytes': INT,
        'created_ms': EPOCH_MS, 'is_open': BOOL, 'crc': INT,
    },
    'event_alias': {
        'scope_key': TEXT, 'fact_key': TEXT, 'event_item_id': BINARY16_HEX, 'crc': INT,
    },
    'inbox_delivery': {
        'delivery_id': BINARY32_HEX, 'scope_key': TEXT, 'raw': BLOB_HEX,
        'raw_sha256': BINARY32_HEX, 'headers_json': JSON_TEXT, 'received_ms': EPOCH_MS,
        'verification_result': TEXT, 'crc': INT,
    },
    'inbox_item': {
        'item_id': BINARY32_HEX, 'delivery_id': BINARY32_HEX, 'item_index': INT,
        'fact_key': TEXT, 'event_item_id': BINARY16_HEX, 'evidence_hash': BINARY32_HEX,
        'fact_json': JSON_TEXT, 'relation': VOCAB + 'relation', 'crc': INT,
    },
    'inbox_state': {
        'item_id': BINARY32_HEX, 'seq': INT, 'state': VOCAB + 'state',
        'at_ms': EPOCH_MS, 'crc': INT,
    },
}


def descriptor():
    """The pinned mapping document exported as type-mapping.json."""
    return {
        'version': TYPE_MAPPING_VERSION,
        'timestampUnit': 'epoch-milliseconds',
        'timezonePolicy': (
            'inbox occurredAtText and occurredOffset preserved verbatim; '
            'no time zone is assumed'
        ),
        'moneyPolicy': (
            'amount_u128 is u128 decimal text, Wide128-lossless; '
            'never float, never narrowed'
        ),
        'fast64': 'not used: no approved execution profile',
        'arrow': 'not materialized in this node; this descriptor is the pin',
        'tables': {
            table: {
                'primaryKey': list(PRIMARY_KEYS[table]),
                'columns': dict(_COLUMNS[table]),
            }
            for table in TABLES
        },
        'vocabularies': {name: list(values) for name, values in VOCABULARIES.items()},
    }


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _check_value(table, column, kind, value):
    if kind == TEXT:
        if not isinstance(value, str) or not value:
            raise ExportError('EXPORT_TYPE')
    elif kind == JSON_TEXT:
        if not isinstance(value, str) or not value:
            raise ExportError('EXPORT_TYPE')
        try:
            strict_loads(value.encode('utf-8'))
        except (ValueError, UnicodeEncodeError, CodecError) as exc:
            raise ExportError('EXPORT_TYPE') from exc
    elif kind == INT:
        if not _is_int(value) or value < 0:
            raise ExportError('EXPORT_TYPE')
        if column == 'crc' and value > CRC32_MAX:
            raise ExportError('EXPORT_TYPE')
        if column in ('attempt_no', 'seq') and value < 1:
            raise ExportError('EXPORT_TYPE')
    elif kind == BOOL:
        if not isinstance(value, bool):
            raise ExportError('EXPORT_TYPE')
    elif kind == EPOCH_MS:
        if not _is_int(value) or value < 0:
            raise ExportError('EXPORT_TYPE')
    elif kind == U128_TEXT:
        if not isinstance(value, str) or _AMOUNT.fullmatch(value) is None:
            raise ExportError('EXPORT_TYPE')
        if int(value) > U128_MAX:
            raise ExportError('EXPORT_TYPE')
    elif kind == BINARY32_HEX:
        if not isinstance(value, str) or _HEX32.fullmatch(value) is None:
            raise ExportError('EXPORT_TYPE')
    elif kind == BINARY16_HEX:
        if not isinstance(value, str) or _HEX16.fullmatch(value) is None:
            raise ExportError('EXPORT_TYPE')
    elif kind == BLOB_HEX:
        if not isinstance(value, str) or _HEX_BLOB.fullmatch(value) is None:
            raise ExportError('EXPORT_TYPE')
    elif kind.startswith(VOCAB):
        if value not in VOCABULARIES[kind[len(VOCAB):]]:
            raise ExportError('EXPORT_VOCAB')
    else:  # pragma: no cover - the pin above is closed
        raise ExportError('EXPORT_MAPPING')


def _check_fact_json(value):
    """The inbox occurred-time text/offset survive verbatim (contract §5)."""
    try:
        fact = strict_loads(value.encode('utf-8'))
    except (ValueError, UnicodeEncodeError, CodecError) as exc:
        raise ExportError('EXPORT_TYPE') from exc
    if not isinstance(fact, dict):
        raise ExportError('EXPORT_TYPE')
    occurred = fact.get('occurredAtText')
    offset = fact.get('occurredOffset')
    if not isinstance(occurred, str) or not occurred:
        raise ExportError('EXPORT_TYPE')
    if offset is not None and not isinstance(offset, str):
        raise ExportError('EXPORT_TYPE')


def map_row(table, document):
    """Validate one raw source row and return its exported document.

    The input is the durable column document; for inbox_delivery it must also
    carry 'raw' as bytes, which is exported as lowercase hex bound by its
    sha256. The crc column is exported unchanged: it is part of the stored row
    and the content hash binds it. No value is re-typed except the blob.
    """
    if table not in _COLUMNS:
        raise ExportError('EXPORT_MAPPING')
    if not isinstance(document, dict):
        raise ExportError('EXPORT_ROW')
    mapped = dict(document)
    if table == 'inbox_delivery':
        raw = mapped.get('raw')
        if not isinstance(raw, (bytes, bytearray)) or not raw:
            raise ExportError('EXPORT_TYPE')
        mapped['raw'] = bytes(raw).hex()
    return _validate_mapped(table, mapped)


def _validate_mapped(table, mapped):
    columns = _COLUMNS[table]
    if set(mapped) != set(columns):
        raise ExportError('EXPORT_ROW')
    for column, kind in columns.items():
        _check_value(table, column, kind, mapped[column])
    if table == 'inbox_delivery':
        digest = hashlib.sha256(bytes.fromhex(mapped['raw'])).hexdigest()
        if digest != mapped['raw_sha256']:
            raise ExportError('EXPORT_HASH')
    if table == 'inbox_item':
        _check_fact_json(mapped['fact_json'])
    return {column: mapped[column] for column in columns}


def check_mapped_row(table, row):
    """Consumer-side re-check of an already exported row document."""
    if table not in _COLUMNS:
        raise ExportError('EXPORT_MAPPING')
    if not isinstance(row, dict):
        raise ExportError('EXPORT_ROW')
    return _validate_mapped(table, row)
