"""Versioned readiness-journal migrations.

Schema 1 is the only readable version. ``migrate`` is the identity function
for version 1. A later schema is not applied by guessing, renaming fields, or
dropping unknown keys. It becomes readable only when this module gains an
explicit function for that source version and ``migrate`` calls it. Unknown
versions fail closed.
"""

from __future__ import annotations

SCHEMA_VERSION = 1


class MigrationError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def migrate(source_version, records):
    """Return records at SCHEMA_VERSION.

    Version 1 returns a new list of the same records. Any other source version
    raises MigrationError('UNSUPPORTED_SCHEMA').
    """
    if source_version == 1 and SCHEMA_VERSION == 1:
        if not isinstance(records, list):
            raise MigrationError('UNSUPPORTED_SCHEMA')
        return list(records)
    raise MigrationError('UNSUPPORTED_SCHEMA')
