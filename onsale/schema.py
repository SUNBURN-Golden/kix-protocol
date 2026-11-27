"""On-sale tables on the composed stage-5 session.

OnsaleSession composes durable.schema.DurableSession unchanged: one connection
to the local unix-socket PostgreSQL, one schema per store directory, one
single-writer FileLock, SERIALIZABLE transactions, CommitUnknown on a failed
COMMIT, the budget ledger and the budget pin. This module adds the onsale_*
DDL in the same schema, per-row CRC over the immutable columns (reusing
durable.schema.row_crc and store_key), and fails closed at open on any
checksum mismatch or any shard whose remaining disagrees with the committed
admission evidence. onsale_ga_shard.remaining is bookkeeping that changes by
design and is outside the row CRC, exactly like ledger.is_open; the derived
invariant below is what detects its tampering.
"""

from __future__ import annotations

from readiness.codec import canonical_json
from readiness.store import StoreError

from durable.schema import DurableSession, row_crc, store_key

ONSALE_DDL = (
    'CREATE TABLE IF NOT EXISTS onsale_ga_config ('
    'show_id text NOT NULL, epoch integer NOT NULL, mode text NOT NULL, '
    'placement_version integer NOT NULL, immutable_total integer NOT NULL, '
    'created_ms bigint NOT NULL, crc bigint NOT NULL, PRIMARY KEY (show_id, epoch))',
    'CREATE TABLE IF NOT EXISTS onsale_ga_shard ('
    'show_id text NOT NULL, epoch integer NOT NULL, shard_id text NOT NULL, '
    'initial_capacity integer NOT NULL, remaining integer NOT NULL, crc bigint NOT NULL, '
    'PRIMARY KEY (show_id, epoch, shard_id))',
    'CREATE TABLE IF NOT EXISTS onsale_queue_ticket ('
    'queue_ticket_id text PRIMARY KEY, show_id text NOT NULL, epoch integer NOT NULL, '
    'principal text NOT NULL, position_identity text NOT NULL, seq integer NOT NULL, '
    'created_ms bigint NOT NULL, crc bigint NOT NULL, UNIQUE (show_id, epoch, seq))',
    'CREATE TABLE IF NOT EXISTS onsale_token ('
    'token_id text PRIMARY KEY, queue_ticket_id text NOT NULL, position_identity text NOT NULL, '
    'show_id text NOT NULL, epoch integer NOT NULL, mode text NOT NULL, '
    'placement_version integer NOT NULL, shard_id text NOT NULL, nonce text NOT NULL, '
    'issued_at_ms bigint NOT NULL, expires_at_ms bigint NOT NULL, signature text NOT NULL, '
    'key_version text NOT NULL, origin_command_id text NOT NULL, ledger_entry_id text NOT NULL, '
    'crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS onsale_token_state ('
    'token_id text NOT NULL, seq integer NOT NULL, state text NOT NULL, reason text NOT NULL, '
    'at_ms bigint NOT NULL, crc bigint NOT NULL, PRIMARY KEY (token_id, seq))',
    'CREATE TABLE IF NOT EXISTS onsale_command ('
    'command_id text PRIMARY KEY, principal text NOT NULL, payload_sha256 text NOT NULL, '
    'first_result text NOT NULL, outcome text NOT NULL, created_ms bigint NOT NULL, '
    'crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS onsale_evidence ('
    'evidence_id text PRIMARY KEY, kind text NOT NULL, show_id text NOT NULL, '
    'epoch integer NOT NULL, queue_ticket_id text NOT NULL, position_identity text NOT NULL, '
    'sequence integer NOT NULL, old_shard_id text, shard_id text, reason text NOT NULL, '
    'issued_at_ms bigint NOT NULL, expires_at_ms bigint NOT NULL, outcome text NOT NULL, '
    'command_id text, at_ms bigint NOT NULL, crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS onsale_session ('
    'session_id text PRIMARY KEY, command_id text NOT NULL UNIQUE, principal text NOT NULL, '
    'show_id text NOT NULL, epoch integer NOT NULL, shard_id text NOT NULL, '
    'created_ms bigint NOT NULL, crc bigint NOT NULL)',
    'CREATE TABLE IF NOT EXISTS onsale_hint ('
    'hint_id text PRIMARY KEY, show_id text NOT NULL, epoch integer NOT NULL, '
    'shard_id text NOT NULL, version integer NOT NULL, source_commit_position bigint NOT NULL, '
    'expires_at_ms bigint NOT NULL, reason text NOT NULL, created_ms bigint NOT NULL, '
    'crc bigint NOT NULL)',
)

# table -> select list in the order the row document is rebuilt. The checksum
# covers every immutable column; onsale_ga_shard.remaining is outside the CRC
# and is checked against the admission evidence at open instead.
ONSALE_COLUMNS = {
    'onsale_ga_config': (
        'show_id', 'epoch', 'mode', 'placement_version', 'immutable_total', 'created_ms',
    ),
    'onsale_ga_shard': ('show_id', 'epoch', 'shard_id', 'initial_capacity'),
    'onsale_queue_ticket': (
        'queue_ticket_id', 'show_id', 'epoch', 'principal', 'position_identity',
        'seq', 'created_ms',
    ),
    'onsale_token': (
        'token_id', 'queue_ticket_id', 'position_identity', 'show_id', 'epoch', 'mode',
        'placement_version', 'shard_id', 'nonce', 'issued_at_ms', 'expires_at_ms',
        'signature', 'key_version', 'origin_command_id', 'ledger_entry_id',
    ),
    'onsale_token_state': ('token_id', 'seq', 'state', 'reason', 'at_ms'),
    'onsale_command': (
        'command_id', 'principal', 'payload_sha256', 'first_result', 'outcome', 'created_ms',
    ),
    'onsale_evidence': (
        'evidence_id', 'kind', 'show_id', 'epoch', 'queue_ticket_id', 'position_identity',
        'sequence', 'old_shard_id', 'shard_id', 'reason', 'issued_at_ms', 'expires_at_ms',
        'outcome', 'command_id', 'at_ms',
    ),
    'onsale_session': (
        'session_id', 'command_id', 'principal', 'show_id', 'epoch', 'shard_id', 'created_ms',
    ),
    'onsale_hint': (
        'hint_id', 'show_id', 'epoch', 'shard_id', 'version', 'source_commit_position',
        'expires_at_ms', 'reason', 'created_ms',
    ),
}
ONSALE_CRC_TABLES = tuple(ONSALE_COLUMNS)


def row_document(table, row):
    return dict(zip(ONSALE_COLUMNS[table], row))


def verify_table(conn, table):
    """Fail closed on any row whose checksum does not match."""
    columns = ', '.join(ONSALE_COLUMNS[table])
    rows = conn.execute('SELECT %s, crc FROM %s' % (columns, table)).fetchall()
    width = len(ONSALE_COLUMNS[table])
    for row in rows:
        document = row_document(table, row[:width])
        if row_crc(table, document) != int(row[width]):
            raise StoreError('CHECKSUM_MISMATCH')
    return len(rows)


def insert_row(conn, table, document):
    """Insert one immutable row with its CRC. Columns come from the document."""
    columns = ONSALE_COLUMNS[table]
    missing = [name for name in columns if name not in document]
    if missing:
        raise StoreError('JOURNAL_RECORD')
    values = [document[name] for name in columns]
    conn.execute(
        'INSERT INTO %s (%s, crc) VALUES (%s, %%s)' % (
            table, ', '.join(columns), ', '.join(['%s'] * len(columns)),
        ),
        (*values, row_crc(table, {name: document[name] for name in columns})),
    )


class OnsaleSession:
    """The composed stage-5 session plus the on-sale tables and pins."""

    def __init__(self, cluster, directory, spec, limits_document, key_version):
        self.session = DurableSession(cluster, directory, spec)
        try:
            conn = self.session.conn
            for statement in ONSALE_DDL:
                conn.execute(statement)
            self._ensure_pin('onsale_limits', canonical_json(limits_document))
            self._ensure_pin('onsale_key_version', canonical_json(key_version))
            self.verify()
        except Exception:
            self.close()
            raise

    # -- delegation to the unchanged durable session -------------------------
    @property
    def conn(self):
        return self.session.conn

    @property
    def guard(self):
        return self.session.guard

    @property
    def broken(self):
        return self.session.broken

    def begin(self, read_only=False):
        self.session.begin(read_only)

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def transaction(self, read_only=False):
        return self.session.transaction(read_only)

    def usage(self):
        return self.session.usage()

    def ledger_insert(self, entry_id, budget_class, nbytes, now_ms, is_open=True):
        self.session.ledger_insert(entry_id, budget_class, nbytes, now_ms, is_open)

    def ledger_close(self, entry_id):
        self.session.ledger_close(entry_id)

    def close(self):
        self.session.close()

    # -- on-sale verification -------------------------------------------------
    def verify(self):
        counts = self.session.verify()
        for table in ONSALE_CRC_TABLES:
            counts[table] = verify_table(self.session.conn, table)
        self._verify_shard_invariant()
        return counts

    def table_counts(self):
        counts = self.session.table_counts()
        for table in ONSALE_CRC_TABLES:
            counts[table] = int(self.session.conn.execute(
                'SELECT COUNT(*) FROM %s' % table,
            ).fetchone()[0])
        return counts

    def commit_position(self):
        """Monotone local commit counter: every state-changing commit appends
        at least one ticket, token-state or evidence row. This is a local
        observation position, never a chain source cut (ADR-0001 §9)."""
        conn = self.session.conn
        total = 0
        for table in ('onsale_queue_ticket', 'onsale_token_state', 'onsale_evidence'):
            total += int(conn.execute('SELECT COUNT(*) FROM %s' % table).fetchone()[0])
        return total

    def _verify_shard_invariant(self):
        """remaining == initial_capacity - committed successful admissions."""
        conn = self.session.conn
        rows = conn.execute(
            'SELECT show_id, epoch, shard_id, initial_capacity, remaining FROM onsale_ga_shard',
        ).fetchall()
        for show_id, epoch, shard_id, initial, remaining in rows:
            consumed = int(conn.execute(
                "SELECT COUNT(*) FROM onsale_evidence WHERE kind = 'admit' "
                "AND outcome = 'new_success' AND show_id = %s AND epoch = %s AND shard_id = %s",
                (show_id, epoch, shard_id),
            ).fetchone()[0])
            if int(remaining) < 0 or int(remaining) != int(initial) - consumed:
                raise StoreError('CHECKSUM_MISMATCH')

    def _ensure_pin(self, key, encoded):
        conn = self.session.conn
        row = conn.execute('SELECT value FROM meta WHERE key = %s', (key,)).fetchone()
        if row is None:
            conn.execute('INSERT INTO meta (key, value) VALUES (%s, %s)', (key, encoded))
            return
        if row[0] != encoded:
            raise StoreError('JOURNAL_RECORD')


__all__ = [
    'ONSALE_DDL', 'ONSALE_COLUMNS', 'ONSALE_CRC_TABLES', 'OnsaleSession',
    'insert_row', 'row_crc', 'row_document', 'store_key', 'verify_table',
]
