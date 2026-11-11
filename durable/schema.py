"""Schema, per-row checksums, single-writer lock and the PostgreSQL session.

One session is one connection to the local unix-socket PostgreSQL, one schema
per store directory, and one file lock. Transactions are SERIALIZABLE. A commit
call that fails after it was sent is CommitUnknown, never "not applied".
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import re
import threading
import zlib
from contextlib import contextmanager
from pathlib import Path

import psycopg

from readiness.codec import canonical_json
from readiness.store import StoreError

from durable.budgets import CLASSES
from durable.errors import CommitUnknown
from durable.model import Usage

_SCHEMA_NAME = re.compile(r'^d[0-9a-f]{16}$')

DDL = (
    'CREATE TABLE IF NOT EXISTS meta (key text PRIMARY KEY, value text NOT NULL)',
    'CREATE TABLE IF NOT EXISTS command_result ('
    'command_id text PRIMARY KEY, payload_sha256 text NOT NULL, first_result text NOT NULL, '
    'outcome text NOT NULL, amount_u128 text NOT NULL, admitted_bytes integer NOT NULL, '
    'created_ms bigint NOT NULL, crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS slot_hold ('
    'show_id text NOT NULL, slot text NOT NULL, command_id text NOT NULL, crc bigint NOT NULL, '
    'PRIMARY KEY (show_id, slot))',
    'CREATE TABLE IF NOT EXISTS minimal_order ('
    'order_id text PRIMARY KEY, command_id text NOT NULL UNIQUE, amount_u128 text NOT NULL, '
    'crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS outbox_intent ('
    'intent_id text PRIMARY KEY, command_id text NOT NULL UNIQUE, kind text NOT NULL, '
    'payload_sha256 text NOT NULL, created_ms bigint NOT NULL, crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS outbox_attempt ('
    'intent_id text NOT NULL, attempt_no integer NOT NULL, phase text NOT NULL, '
    'result text NOT NULL, at_ms bigint NOT NULL, crc bigint NOT NULL, '
    'PRIMARY KEY (intent_id, attempt_no, phase))',
    'CREATE TABLE IF NOT EXISTS observation ('
    'observation_id text PRIMARY KEY, command_id text NOT NULL, payload_sha256 text NOT NULL, '
    'nbytes integer NOT NULL, created_ms bigint NOT NULL, crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS ledger ('
    'entry_id text PRIMARY KEY, budget_class text NOT NULL, nbytes integer NOT NULL, '
    'created_ms bigint NOT NULL, is_open boolean NOT NULL, crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS event_alias ('
    'scope_key text NOT NULL, fact_key text NOT NULL, event_item_id text NOT NULL, '
    'crc bigint NOT NULL, PRIMARY KEY (scope_key, fact_key), UNIQUE (scope_key, event_item_id))',
    'CREATE TABLE IF NOT EXISTS inbox_delivery ('
    'delivery_id text PRIMARY KEY, scope_key text NOT NULL, raw bytea NOT NULL, '
    'raw_sha256 text NOT NULL, headers_json text NOT NULL, received_ms bigint NOT NULL, '
    'verification_result text NOT NULL, crc bigint NOT NULL, UNIQUE (scope_key, raw_sha256))',
    'CREATE TABLE IF NOT EXISTS inbox_item ('
    'item_id text PRIMARY KEY, delivery_id text NOT NULL, item_index integer NOT NULL, '
    'fact_key text NOT NULL, event_item_id text NOT NULL, evidence_hash text NOT NULL, '
    'fact_json text NOT NULL, relation text NOT NULL, crc bigint NOT NULL, '
    'UNIQUE (delivery_id, item_index))',
    'CREATE TABLE IF NOT EXISTS inbox_state ('
    'item_id text NOT NULL, seq integer NOT NULL, state text NOT NULL, at_ms bigint NOT NULL, '
    'crc bigint NOT NULL, PRIMARY KEY (item_id, seq))',
)

# table -> (select list in the order the row document is rebuilt, document builder)
# The checksum covers every immutable column. ledger.is_open and the inbox state
# log are bookkeeping that changes by design; ledger.is_open is outside the crc.
CRC_TABLES = (
    'command_result', 'slot_hold', 'minimal_order', 'outbox_intent', 'outbox_attempt',
    'observation', 'ledger', 'event_alias', 'inbox_delivery', 'inbox_item', 'inbox_state',
)
_COLUMNS = {
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
_BLOB_TABLES = {'inbox_delivery': 'raw'}


def row_document(table, row):
    return dict(zip(_COLUMNS[table], row))


def row_crc(table, document, blob=None):
    """CRC-32 of the canonical document; a raw blob is bound by its sha256."""
    body = dict(document)
    if blob is not None:
        body['rawBlobSha256'] = hashlib.sha256(bytes(blob)).hexdigest()
    return zlib.crc32(canonical_json([table, body]).encode('utf-8')) & 0xFFFFFFFF


def verify_table(conn, table):
    """Fail closed on any row whose checksum does not match."""
    columns = ', '.join(_COLUMNS[table])
    blob = _BLOB_TABLES.get(table)
    extra = ', %s' % blob if blob else ''
    rows = conn.execute('SELECT %s, crc%s FROM %s' % (columns, extra, table)).fetchall()
    width = len(_COLUMNS[table])
    for row in rows:
        document = row_document(table, row[:width])
        stored = int(row[width])
        data = row[width + 1] if blob else None
        if row_crc(table, document, data) != stored:
            raise StoreError('CHECKSUM_MISMATCH')
    return len(rows)


def store_key(directory):
    return hashlib.sha256(os.path.realpath(directory).encode()).hexdigest()[:16]


class FileLock:
    """Single writer for one store directory."""

    def __init__(self, directory):
        root = Path(directory)
        root.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(root / 'durable.lock', os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self._fd)
            self._fd = None
            raise StoreError('JOURNAL_LOCKED') from exc

    def release(self):
        if self._fd is None:
            return
        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(self._fd)
        self._fd = None


class _Tx:
    aborted = False

    def abort(self):
        self.aborted = True


class DurableSession:
    """Connection, schema, lock and transaction helpers shared by the facets."""

    def __init__(self, cluster, directory, spec):
        self.cluster = cluster
        self.directory = directory
        self.spec = spec
        self.guard = threading.RLock()
        self.broken = False
        self.conn = None
        self._lock = FileLock(directory)
        try:
            self.conn = cluster.connect()
            name = 'd' + store_key(directory)
            if _SCHEMA_NAME.fullmatch(name) is None:
                raise StoreError('JOURNAL_PATH')
            self.conn.execute('CREATE SCHEMA IF NOT EXISTS %s' % name)
            self.conn.execute('SET search_path TO %s' % name)
            for statement in DDL:
                self.conn.execute(statement)
            self._ensure_budget_pin()
            self.verify()
        except Exception:
            self.close()
            raise

    def verify(self):
        counts = {}
        for table in CRC_TABLES:
            counts[table] = verify_table(self.conn, table)
        return counts

    def table_counts(self):
        return {
            table: int(self.conn.execute('SELECT COUNT(*) FROM %s' % table).fetchone()[0])
            for table in CRC_TABLES
        }

    def begin(self, read_only=False):
        self._check_open()
        self.conn.execute('BEGIN')
        mode = 'READ ONLY' if read_only else 'READ WRITE'
        try:
            self.conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE ' + mode)
        except BaseException:
            self.rollback()
            raise

    def commit(self):
        """COMMIT. A failure here leaves the effect unknown and closes the session."""
        try:
            self.conn.execute('COMMIT')
        except Exception as exc:
            self.broken = True
            raise CommitUnknown() from exc

    @contextmanager
    def transaction(self, read_only=False):
        """One SERIALIZABLE transaction under the session guard.

        Any exception rolls back and propagates. A normal exit commits unless
        the block called tx.abort(). A failing COMMIT raises CommitUnknown.
        """
        with self.guard:
            self.begin(read_only)
            tx = _Tx()
            try:
                yield tx
            except BaseException:
                self.rollback()
                raise
            if tx.aborted:
                self.rollback()
            else:
                self.commit()

    def rollback(self):
        if self.conn is None:
            return
        try:
            self.conn.execute('ROLLBACK')
        except psycopg.Error:
            pass

    def usage(self):
        """Per-class retained count, bytes and oldest still-open created_ms."""
        usage = {name: Usage() for name in CLASSES}
        rows = self.conn.execute(
            'SELECT budget_class, COUNT(*), COALESCE(SUM(nbytes), 0), '
            'MIN(CASE WHEN is_open THEN created_ms END) FROM ledger GROUP BY budget_class'
        ).fetchall()
        for budget_class, count, nbytes, oldest in rows:
            usage[budget_class] = Usage(
                count=int(count), nbytes=int(nbytes),
                oldest_open_ms=None if oldest is None else int(oldest),
            )
        return usage

    def ledger_insert(self, entry_id, budget_class, nbytes, now_ms, is_open=True):
        document = {
            'entry_id': entry_id, 'budget_class': budget_class,
            'nbytes': nbytes, 'created_ms': now_ms,
        }
        self.conn.execute(
            'INSERT INTO ledger (entry_id, budget_class, nbytes, created_ms, is_open, crc) '
            'VALUES (%s, %s, %s, %s, %s, %s)',
            (entry_id, budget_class, nbytes, now_ms, is_open, row_crc('ledger', document)),
        )

    def ledger_close(self, entry_id):
        self.conn.execute('UPDATE ledger SET is_open = %s WHERE entry_id = %s', (False, entry_id))

    def close(self):
        conn, self.conn = self.conn, None
        if conn is not None:
            try:
                conn.close()
            except psycopg.Error:
                pass
        lock, self._lock = self._lock, None
        if lock is not None:
            lock.release()

    def _check_open(self):
        if self.conn is None or self.broken:
            raise StoreError('JOURNAL_CLOSED')

    def _ensure_budget_pin(self):
        encoded = canonical_json(self.spec.document())
        row = self.conn.execute("SELECT value FROM meta WHERE key = 'budget'").fetchone()
        if row is None:
            self.conn.execute('INSERT INTO meta (key, value) VALUES (%s, %s)', ('budget', encoded))
            return
        if row[0] != encoded:
            raise StoreError('JOURNAL_RECORD')
