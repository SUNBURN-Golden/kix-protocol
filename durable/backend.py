"""Conformance adapter for the adopted local PostgreSQL backend.

Surface of readiness/CONFORMANCE.md: open_store, open_boundary, fault_error.
The record store and the FSM boundary are the stage-4 local PostgreSQL ones,
reused unchanged (docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md §7:
"5단계는 이 로컬 어댑터를 업무 범위로 재사용한다. 새 저장 엔진이 아니다").
open_unit adds the stage-5 durable layer: business unit, inbox and outbox.
"""

from __future__ import annotations

import psycopg

from readiness.store import ReadinessFault, StoreError

from exploration.stage4.adapters import PostgresAdapter

from durable.schema import CRC_TABLES, store_key
from durable.unit import DurableUnit


class DurablePostgresBackend(PostgresAdapter):
    fault_error = ReadinessFault

    def open_unit(self, directory, spec):
        return DurableUnit(self.cluster, directory, spec)

    def corrupt_unit_table(self, directory, table):
        """Test hook: break one row checksum of a durable table."""
        if table not in CRC_TABLES:
            raise StoreError('JOURNAL_RECORD')
        conn = self.cluster.connect()
        try:
            conn.execute('SET search_path TO d%s' % store_key(directory))
            updated = conn.execute('UPDATE %s SET crc = crc + 1' % table).rowcount
            if updated < 1:
                raise StoreError('JOURNAL_CORRUPT')
        except psycopg.Error as exc:
            raise StoreError('JOURNAL_CORRUPT') from exc
        finally:
            conn.close()
