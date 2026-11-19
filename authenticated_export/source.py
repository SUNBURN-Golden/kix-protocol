"""PG-bound read-only source adapter over the stage-5 durable store.

One own connection, one schema search_path, one BEGIN ISOLATION LEVEL
SERIALIZABLE READ ONLY: every table is read inside that single MVCC snapshot,
so a writer that commits mid-export is invisible to the cut. The snapshot
identity is pg_current_snapshot() (xmin/xmax/xip); pg_current_wal_lsn() is
captured at start and end as provenance only, never as the cut (contract §2).

Before any row is exported, the durable per-row CRCs are re-verified inside
the snapshot (durable.schema.verify_table, unchanged) and the live
information_schema fingerprint of the eleven business tables is compared to
the pin below. Drift fails closed; this module never edits durable/ and never
takes the writer lock. No writes, no CREATE, no public endpoint: the pinned
cluster is unix-socket only.
"""

from __future__ import annotations

import hashlib

import psycopg

from readiness.codec import canonical_json
from readiness.store import StoreError

from durable.cluster import PinnedPostgresCluster  # noqa: F401  (re-export for callers)
from durable.schema import CRC_TABLES, row_document, store_key, verify_table

from authenticated_export import ISOLATION_LEVEL
from authenticated_export.errors import ExportError
from authenticated_export.mapping import PRIMARY_KEYS

# sha256 of the canonical [table, column, data_type] list of the eleven
# business tables (66 columns), measured on PostgreSQL 17.11 from the
# unchanged stage-5 DDL. A durable schema change must re-pin this constant
# in its own node; until then the exporter refuses the drifted store.
SCHEMA_FINGERPRINT = '6b5968825322f1efa3c6c244efea3c20f3022bac65a25f7ab1e17f5d07561a3e'

# The durable CRC column lists, in row_document order (the PG suite asserts
# they equal durable.schema._COLUMNS). Extra columns outside the CRC follow:
# ledger.is_open changes by design; inbox_delivery.raw is bound by sha256.
_SELECT_COLUMNS = {
    'command_result': (
        'command_id', 'payload_sha256', 'first_result', 'outcome', 'amount_u128',
        'admitted_bytes', 'created_ms',
    ),
    'slot_hold': ('show_id', 'slot', 'command_id'),
    'minimal_order': ('order_id', 'command_id', 'amount_u128'),
    'outbox_intent': ('intent_id', 'command_id', 'kind', 'payload_sha256', 'created_ms'),
    'outbox_attempt': ('intent_id', 'attempt_no', 'phase', 'result', 'at_ms'),
    'observation': ('observation_id', 'command_id', 'payload_sha256', 'nbytes', 'created_ms'),
    'ledger': ('entry_id', 'budget_class', 'nbytes', 'created_ms'),
    'event_alias': ('scope_key', 'fact_key', 'event_item_id'),
    'inbox_delivery': (
        'delivery_id', 'scope_key', 'raw_sha256', 'headers_json', 'received_ms',
        'verification_result',
    ),
    'inbox_item': (
        'item_id', 'delivery_id', 'item_index', 'fact_key', 'event_item_id',
        'evidence_hash', 'fact_json', 'relation',
    ),
    'inbox_state': ('item_id', 'seq', 'state', 'at_ms'),
}
_EXTRA_COLUMNS = {'ledger': ('is_open',), 'inbox_delivery': ('raw',)}


def schema_fingerprint(conn, schema_name):
    rows = conn.execute(
        'SELECT table_name, column_name, data_type FROM information_schema.columns '
        'WHERE table_schema = %s AND table_name = ANY(%s) '
        'ORDER BY table_name, ordinal_position',
        (schema_name, list(CRC_TABLES)),
    ).fetchall()
    document = [[row[0], row[1], row[2]] for row in rows]
    return hashlib.sha256(canonical_json(document).encode('utf-8')).hexdigest()


class _Capture:
    """One open SERIALIZABLE READ ONLY snapshot on its own connection."""

    def __init__(self, conn, cluster_id, snapshot_text, lsn_start):
        self._conn = conn
        self.cluster_id = cluster_id
        self.snapshot_id = snapshot_text
        parts = snapshot_text.split(':')
        self.xmin = int(parts[0])
        self.xmax = int(parts[1])
        self.isolation_level = ISOLATION_LEVEL
        self.lsn_start = lsn_start
        self._closed = False

    def tables(self):
        return CRC_TABLES

    def rows(self, table):
        if self._closed:
            raise ExportError('EXPORT_SOURCE')
        columns = _SELECT_COLUMNS[table]
        extras = _EXTRA_COLUMNS.get(table, ())
        select = ', '.join(tuple(columns) + tuple(extras)) + ', crc'
        order = ', '.join(PRIMARY_KEYS[table])
        try:
            rows = self._conn.execute(
                'SELECT %s FROM %s ORDER BY %s' % (select, table, order),
            ).fetchall()
        except psycopg.Error as exc:
            raise ExportError('EXPORT_SOURCE') from exc
        width = len(columns)
        documents = []
        for row in rows:
            document = row_document(table, row[:width])
            for offset, extra in enumerate(extras):
                value = row[width + offset]
                document[extra] = bytes(value) if extra == 'raw' else bool(value)
            document['crc'] = int(row[width + len(extras)])
            documents.append(document)
        return documents

    def lsn_end(self):
        if self._closed:
            raise ExportError('EXPORT_SOURCE')
        try:
            return self._conn.execute('SELECT pg_current_wal_lsn()').fetchone()[0]
        except psycopg.Error as exc:
            raise ExportError('EXPORT_SOURCE') from exc

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self._conn.execute('COMMIT')
        except psycopg.Error:
            pass  # read-only: nothing to commit unknown
        try:
            self._conn.close()
        except psycopg.Error:
            pass


class PostgresExportSource:
    """Read-only export source for one stage-5 store directory."""

    def __init__(self, cluster, directory):
        self.cluster = cluster
        self.directory = directory

    def capture(self):
        try:
            conn = self.cluster.connect()
        except psycopg.Error as exc:
            raise ExportError('EXPORT_SOURCE') from exc
        try:
            name = 'd' + store_key(self.directory)
            known = conn.execute('SELECT to_regnamespace(%s)', (name,)).fetchone()[0]
            if known is None:
                raise ExportError('EXPORT_SOURCE')
            conn.execute('SET search_path TO %s' % name)
            conn.execute('BEGIN ISOLATION LEVEL SERIALIZABLE READ ONLY')
            snapshot_text = conn.execute('SELECT pg_current_snapshot()').fetchone()[0]
            lsn_start = conn.execute('SELECT pg_current_wal_lsn()').fetchone()[0]
            if schema_fingerprint(conn, name) != SCHEMA_FINGERPRINT:
                raise ExportError('EXPORT_SCHEMA')
            for table in CRC_TABLES:
                verify_table(conn, table)
            return _Capture(conn, 'kix-local-durable/' + store_key(self.directory),
                            snapshot_text, lsn_start)
        except StoreError as exc:
            conn.close()
            raise ExportError('EXPORT_CHECKSUM') from exc
        except ExportError:
            conn.close()
            raise
        except psycopg.Error as exc:
            conn.close()
            raise ExportError('EXPORT_SOURCE') from exc
