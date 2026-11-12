"""Deterministic row files: canonical JSON lines in primary-key order.

One file per stage-5 business table under tables/, plus the pinned type
mapping descriptor as type-mapping.json. Every file is hashed (sha256) and
bound into the manifest with its row count. Reading fails closed on a
truncated line, a duplicate key, a non-standard JSON number or a hash/count
mismatch. The manifest is written last by the exporter, but a consumer never
trusts presence alone: missing, extra or partial files all fail closed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from readiness.codec import CodecError, canonical_json, strict_loads

from authenticated_export.errors import ExportError
from authenticated_export.mapping import PRIMARY_KEYS, TABLES

MAPPING_FILE = 'type-mapping.json'
MANIFEST_FILE = 'manifest.json'


def table_path(table):
    return 'tables/%s.jsonl' % table


def row_pk(table, row):
    try:
        return tuple(row[column] for column in PRIMARY_KEYS[table])
    except (KeyError, TypeError) as exc:
        raise ExportError('EXPORT_ROW') from exc


def sort_rows(table, rows):
    return sorted(rows, key=lambda row: row_pk(table, row))


def file_bytes(rows):
    return ''.join(canonical_json(row) + '\n' for row in rows).encode('utf-8')


def write_table_file(directory, table, rows):
    """Write one sorted row file; return its {path, sha256, rowCount} entry."""
    data = file_bytes(rows)
    path = table_path(table)
    target = Path(directory) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'rowCount': len(rows)}


def write_mapping_file(directory, descriptor):
    data = (canonical_json(descriptor) + '\n').encode('utf-8')
    target = Path(directory) / MAPPING_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {'path': MAPPING_FILE, 'sha256': hashlib.sha256(data).hexdigest(), 'rowCount': 0}


def read_table_file(directory, entry):
    """Read and bind one row file: hash, count, strict parse, PK order/unique."""
    path = Path(directory) / entry['path']
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ExportError('EXPORT_FILE') from exc
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ExportError('EXPORT_HASH')
    if not data:
        rows = []
    else:
        if not data.endswith(b'\n'):
            raise ExportError('EXPORT_FILE')
        rows = []
        for line in data.split(b'\n')[:-1]:
            if not line:
                raise ExportError('EXPORT_FILE')
            try:
                rows.append(strict_loads(line))
            except (ValueError, CodecError) as exc:
                raise ExportError('EXPORT_FILE') from exc
    if len(rows) != entry['rowCount']:
        raise ExportError('EXPORT_FILE')
    table = _table_of(entry['path'])
    seen = set()
    previous = None
    for row in rows:
        if not isinstance(row, dict):
            raise ExportError('EXPORT_ROW')
        pk = row_pk(table, row)
        if pk in seen:
            raise ExportError('EXPORT_ROW')
        seen.add(pk)
        if previous is not None and pk <= previous:
            raise ExportError('EXPORT_ROW')
        previous = pk
    return rows


def _table_of(path):
    for table in TABLES:
        if path == table_path(table):
            return table
    raise ExportError('EXPORT_FILE')


def read_mapping_file(directory, entry):
    path = Path(directory) / entry['path']
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ExportError('EXPORT_FILE') from exc
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ExportError('EXPORT_HASH')
    try:
        document = strict_loads(data)
    except (ValueError, CodecError) as exc:
        raise ExportError('EXPORT_FILE') from exc
    if not isinstance(document, dict):
        raise ExportError('EXPORT_FILE')
    return document


def check_file_set(directory, per_file_hash):
    """Exactly the manifest's files must exist: no missing, no extra."""
    expected = {entry['path'] for entry in per_file_hash}
    present = set()
    root = Path(directory)
    for path in root.rglob('*'):
        if path.is_file():
            present.add(path.relative_to(root).as_posix())
    present.discard(MANIFEST_FILE)
    if present != expected:
        raise ExportError('EXPORT_FILE')
