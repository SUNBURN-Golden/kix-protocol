"""Versioned readiness-journal migrations.

Schema 1 is the only version ``migrate`` will read. That function calls
``migrate_v1_to_v1`` and no other migrator. A file header of any other
version, including 2, stays UNSUPPORTED_SCHEMA.

``migrate_explicit`` is the only caller of the schema-2 functions. It copies
records. It does not rename fields, drop unknown keys, invent missing
identity fields, or run when a journal file is opened.
"""

from __future__ import annotations

import json

from readiness.codec import CodecError, canonical_json

SCHEMA_VERSION = 1
SCHEMA_V2 = 2

_V1_FALSE = ('protocolTruth', 'productionConformance')
_V2_STAMPS = (
    ('productionReadiness', False),
    ('productionEndpoint', False),
)


class MigrationError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def migrate(source_version, records):
    """Return records at SCHEMA_VERSION.

    Version 1 returns a new list of the same records. Any other source version
    raises MigrationError('UNSUPPORTED_SCHEMA'). This read path does not call
    ``migrate_v1_to_v2``.
    """
    if source_version == 1 and SCHEMA_VERSION == 1:
        return migrate_v1_to_v1(records)
    raise MigrationError('UNSUPPORTED_SCHEMA')


def migrate_explicit(source_version, target_version, records):
    """Apply one named migrator. There is no 2-to-1 function."""
    if source_version == 1 and target_version == 1:
        return migrate_v1_to_v1(records)
    if source_version == 1 and target_version == SCHEMA_V2:
        return migrate_v1_to_v2(records)
    if source_version == SCHEMA_V2 and target_version == SCHEMA_V2:
        return migrate_v2_to_v2(records)
    raise MigrationError('UNSUPPORTED_SCHEMA')


def migrate_v1_to_v1(records):
    if not isinstance(records, list):
        raise MigrationError('UNSUPPORTED_SCHEMA')
    return list(records)


def migrate_v1_to_v2(records):
    """Copy schema-1 records and stamp the two contract constants.

    Missing kind, machine, or the schema-1 false labels fail closed. Unknown
    keys are kept. A contradictory readiness or endpoint label is not coerced.
    """
    if not isinstance(records, list):
        raise MigrationError('UNSUPPORTED_SCHEMA')
    migrated = []
    for record in records:
        migrated.append(_v1_record_to_v2(record))
    return migrated


def migrate_v2_to_v2(records):
    if not isinstance(records, list):
        raise MigrationError('UNSUPPORTED_SCHEMA')
    copied = []
    for record in records:
        copied.append(_require_v2(record))
    return copied


def _v1_record_to_v2(record):
    if not isinstance(record, dict):
        raise MigrationError('UNSUPPORTED_SCHEMA')
    if record.get('schema') != 1:
        raise MigrationError('UNSUPPORTED_SCHEMA')
    for name in _V1_FALSE:
        if record.get(name) is not False:
            raise MigrationError('UNSUPPORTED_SCHEMA')
    if not isinstance(record.get('kind'), str) or not record['kind']:
        raise MigrationError('UNSUPPORTED_SCHEMA')
    if not isinstance(record.get('machine'), str) or not record['machine']:
        raise MigrationError('UNSUPPORTED_SCHEMA')
    for name, required in _V2_STAMPS:
        if name in record and record[name] is not required:
            raise MigrationError('UNSUPPORTED_SCHEMA')
    copied = _detach(record)
    copied['schema'] = SCHEMA_V2
    for name, required in _V2_STAMPS:
        if name not in copied:
            copied[name] = required
    return copied


def _require_v2(record):
    if not isinstance(record, dict) or record.get('schema') != SCHEMA_V2:
        raise MigrationError('UNSUPPORTED_SCHEMA')
    for name in _V1_FALSE:
        if record.get(name) is not False:
            raise MigrationError('UNSUPPORTED_SCHEMA')
    for name, required in _V2_STAMPS:
        if record.get(name) is not required:
            raise MigrationError('UNSUPPORTED_SCHEMA')
    if not isinstance(record.get('kind'), str) or not record['kind']:
        raise MigrationError('UNSUPPORTED_SCHEMA')
    if not isinstance(record.get('machine'), str) or not record['machine']:
        raise MigrationError('UNSUPPORTED_SCHEMA')
    return _detach(record)


def _detach(record):
    try:
        return json.loads(canonical_json(record))
    except CodecError as exc:
        raise MigrationError('UNSUPPORTED_SCHEMA') from exc
