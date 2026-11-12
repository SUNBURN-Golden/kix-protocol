"""The on-sale admission unit on the adopted local PostgreSQL.

One SERIALIZABLE transaction commits the command identity, payload sha256,
first result, queue ticket, token, token-state transition, shard remaining
decrement, append-only evidence, negative hint and budget ledger entry
together. Replay returns the stored first result and adds no row. A conflicting
payload is retained once as observation evidence. Capacity writes nothing. A
COMMIT that fails after it was sent is outcome "unknown"; the next apply of the
same command id reads the truth from the database (contract §5, ADR-0001).

The shard remaining decrement is the only capacity authority here: the router
and its hints never write. The signing key is caller-supplied, used in memory
only and never stored; the keyVersion label is pinned at open. Every limit is a
required caller argument (contract §10); fixture numbers live only in tests.
"""

from __future__ import annotations

import psycopg

from readiness.store import StoreError

from durable.budgets import BudgetSpec
from durable.errors import CommitUnknown
from durable.schema import row_crc as durable_row_crc

import onsale
from onsale import tokens
from onsale.model import (
    AdmitRequest, AdmitSnapshot, EnqueueRequest, EnqueueSnapshot, OnsaleLimits,
    ReissueRequest, ReissueSnapshot, command_id, decide_admit, decide_enqueue,
    decide_reissue, negative_hint_document, payload_nbytes, payload_sha256,
    validate_ga_config,
)
from onsale.schema import (
    ONSALE_COLUMNS, OnsaleSession, insert_row, row_crc, row_document,
)


def _command_of(request):
    return command_id(request.show_id, request.inventory_epoch,
                      request.inventory_mode, request.principal,
                      request.client_command_id)


def _now(now_ms):
    if isinstance(now_ms, bool) or not isinstance(now_ms, int) or now_ms < 0:
        raise StoreError('JOURNAL_RECORD')
    return now_ms


def _non_empty_str(value, label):
    if not isinstance(value, str) or not value:
        raise ValueError('%s must be a non-empty string' % label)
    return value


def _epoch(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('inventory_epoch must be a non-negative integer')
    return value


class AdmissionUnit:
    def __init__(self, cluster, directory, spec, limits, key, key_version):
        if not isinstance(spec, BudgetSpec):
            raise ValueError('spec must be a durable BudgetSpec with all five classes')
        if not isinstance(limits, OnsaleLimits):
            raise ValueError('limits must be OnsaleLimits with every bound supplied')
        if not isinstance(key, bytes) or not key:
            raise ValueError('key must be non-empty caller-supplied bytes')
        _non_empty_str(key_version, 'key_version')
        self.spec = spec
        self.limits = limits
        self.key = key
        self.key_version = key_version
        self.session = OnsaleSession(cluster, directory, spec, limits.document(), key_version)

    # -- public surface -------------------------------------------------------
    def flags(self):
        return {
            'localOnsaleFixtureOnly': onsale.LOCAL_ONSALE_FIXTURE_ONLY,
            'protocolTruth': onsale.PROTOCOL_TRUTH,
            'productionConformance': onsale.PRODUCTION_CONFORMANCE,
            'productionReadiness': onsale.PRODUCTION_READINESS,
            'productionEndpoint': onsale.PRODUCTION_ENDPOINT,
            'fundsExecuted': onsale.FUNDS_EXECUTED,
            'chainWriter': onsale.CHAIN_WRITER,
            'delegatedExecution': onsale.DELEGATED_EXECUTION,
        }

    def configure_ga(self, show_id, inventory_epoch, inventory_mode,
                     placement_version, total_capacity, shard_capacities, now_ms):
        """Contract §1: validate the sum, pin the immutable config and shards.

        Idempotent for identical values; different values for an existing
        (show, epoch) are a store integrity error, never a silent reconfigure.
        This is setup, not a business command: no command row, no budget entry.
        """
        now_ms = _now(now_ms)
        _non_empty_str(show_id, 'show_id')
        _epoch(inventory_epoch)
        _non_empty_str(inventory_mode, 'inventory_mode')
        if isinstance(placement_version, bool) or not isinstance(placement_version, int) or placement_version < 0:
            raise ValueError('placement_version must be a non-negative integer')
        capacities = validate_ga_config(total_capacity, shard_capacities)
        s = self.session
        try:
            with s.transaction() as tx:
                existing = self._config_row(show_id, inventory_epoch)
                if existing is not None:
                    same = (
                        existing['mode'] == inventory_mode
                        and existing['placement_version'] == placement_version
                        and existing['immutable_total'] == total_capacity
                    )
                    if same:
                        for shard_id, capacity in capacities.items():
                            row = self._shard_row(show_id, inventory_epoch, shard_id)
                            if row is None or row['initial_capacity'] != capacity:
                                same = False
                                break
                        count = int(s.conn.execute(
                            'SELECT COUNT(*) FROM onsale_ga_shard WHERE show_id = %s AND epoch = %s',
                            (show_id, inventory_epoch),
                        ).fetchone()[0])
                        same = same and count == len(capacities)
                    if not same:
                        raise StoreError('JOURNAL_RECORD')
                    tx.abort()
                    return self._result_fields('replayed', configured=False)
                insert_row(s.conn, 'onsale_ga_config', {
                    'show_id': show_id, 'epoch': inventory_epoch, 'mode': inventory_mode,
                    'placement_version': placement_version, 'immutable_total': total_capacity,
                    'created_ms': now_ms,
                })
                for shard_id, capacity in sorted(capacities.items()):
                    document = {
                        'show_id': show_id, 'epoch': inventory_epoch, 'shard_id': shard_id,
                        'initial_capacity': capacity,
                    }
                    s.conn.execute(
                        'INSERT INTO onsale_ga_shard '
                        '(show_id, epoch, shard_id, initial_capacity, remaining, crc) '
                        'VALUES (%s, %s, %s, %s, %s, %s)',
                        (show_id, inventory_epoch, shard_id, capacity, capacity,
                         row_crc('onsale_ga_shard', document)),
                    )
        except CommitUnknown:
            return self._failure('unknown', 'COMMIT_UNKNOWN')
        except psycopg.Error as exc:
            return self._failure('error', exc.__class__.__name__)
        return self._result_fields('new_success', configured=True)

    def enqueue(self, request, now_ms):
        if not isinstance(request, EnqueueRequest):
            raise ValueError('request must be an EnqueueRequest')
        return self._apply(request, now_ms, self._snapshot_enqueue, decide_enqueue,
                           needs_key_version=True)

    def admit(self, request, now_ms):
        if not isinstance(request, AdmitRequest):
            raise ValueError('request must be an AdmitRequest')
        return self._apply(request, now_ms, self._snapshot_admit, decide_admit,
                           needs_key_version=False)

    def reissue(self, request, now_ms):
        if not isinstance(request, ReissueRequest):
            raise ValueError('request must be a ReissueRequest')
        return self._apply(request, now_ms, self._snapshot_reissue, decide_reissue,
                           needs_key_version=True)

    def expire_sweep(self, now_ms, max_count):
        """Service operation (no command row): terminal EXPIRED for issued
        tokens past their expiry, bounded by max_count and the completion
        budget. One transaction; a partial sweep commits what it finished."""
        now_ms = _now(now_ms)
        if isinstance(max_count, bool) or not isinstance(max_count, int) or max_count < 1:
            raise ValueError('max_count must be a positive integer supplied by the caller')
        s = self.session
        expired = 0
        stopped = None
        capacity_reason = None
        try:
            with s.transaction():
                usage = s.usage()
                used = usage.get('completion')
                added_count = 0
                added_bytes = 0
                rows = s.conn.execute(
                    'SELECT t.token_id, t.queue_ticket_id, t.position_identity, t.show_id, '
                    't.epoch, t.shard_id, t.issued_at_ms, t.expires_at_ms, t.ledger_entry_id, st.seq '
                    'FROM onsale_token t JOIN onsale_token_state st ON st.token_id = t.token_id '
                    'WHERE st.seq = (SELECT MAX(seq) FROM onsale_token_state WHERE token_id = t.token_id) '
                    "AND st.state = 'ISSUED' AND t.expires_at_ms <= %s "
                    'ORDER BY t.expires_at_ms, t.token_id LIMIT %s',
                    (now_ms, max_count),
                ).fetchall()
                for row in rows:
                    (tid, ticket_id, position, show_id, epoch, shard_id,
                     issued_at, expires_at, ledger_entry, state_seq) = row
                    evidence = {
                        'evidence_id': 'ev-exp-' + tid, 'kind': 'expire', 'show_id': show_id,
                        'epoch': epoch, 'queue_ticket_id': ticket_id,
                        'position_identity': position,
                        'sequence': self._ticket_evidence_count(ticket_id) + 1,
                        'old_shard_id': None, 'shard_id': shard_id, 'reason': 'expired',
                        'issued_at_ms': issued_at, 'expires_at_ms': expires_at,
                        'outcome': 'business_rejected', 'command_id': None, 'at_ms': now_ms,
                    }
                    nbytes = payload_nbytes(evidence)
                    code, why = self.spec.check(
                        'completion', used_count=used.count + added_count,
                        used_bytes=used.nbytes + added_bytes,
                        oldest_open_ms=used.oldest_open_ms, now_ms=now_ms, extra_bytes=nbytes,
                    )
                    if code != 'OK':
                        stopped = 'capacity'
                        capacity_reason = why
                        break
                    insert_row(s.conn, 'onsale_token_state', {
                        'token_id': tid, 'seq': state_seq + 1, 'state': 'EXPIRED',
                        'reason': 'expired', 'at_ms': now_ms,
                    })
                    s.ledger_close(ledger_entry)
                    insert_row(s.conn, 'onsale_evidence', evidence)
                    s.ledger_insert('exp:' + tid, 'completion', nbytes, now_ms, is_open=False)
                    expired += 1
                    added_count += 1
                    added_bytes += nbytes
                else:
                    if len(rows) == max_count:
                        stopped = 'max_count'
        except CommitUnknown:
            return self._failure('unknown', 'COMMIT_UNKNOWN')
        except psycopg.Error as exc:
            return self._failure('error', exc.__class__.__name__)
        result = self._result_fields('new_success')
        result.update({'expired': expired, 'stopped': stopped,
                       'capacity_reason': capacity_reason})
        return result

    def read_result(self, command_id, principal):
        """Durable proof read with an authorization check (contract §5)."""
        _non_empty_str(command_id, 'command_id')
        _non_empty_str(principal, 'principal')
        with self.session.guard:
            row = self._command_row(command_id)
        if row is None:
            return None
        if row['principal'] != principal:
            raise StoreError('FORBIDDEN')
        return {
            'commandId': row['command_id'], 'outcome': row['outcome'],
            'firstResult': row['first_result'], 'payloadSha256': row['payload_sha256'],
        }

    def queue_artifact(self, show_id, inventory_epoch, now_ms):
        """Coarse versioned waiting-room artifact (contract §2): counts and a
        version only. No seat stream, no per-user or per-seat labels."""
        now_ms = _now(now_ms)
        _non_empty_str(show_id, 'show_id')
        _epoch(inventory_epoch)
        s = self.session
        with s.guard:
            version = s.commit_position()
            waiting = int(s.conn.execute(
                'SELECT COUNT(*) FROM onsale_token t JOIN onsale_token_state st '
                'ON st.token_id = t.token_id WHERE t.show_id = %s AND t.epoch = %s '
                'AND st.seq = (SELECT MAX(seq) FROM onsale_token_state WHERE token_id = t.token_id) '
                "AND st.state = 'ISSUED' AND t.expires_at_ms > %s",
                (show_id, inventory_epoch, now_ms),
            ).fetchone()[0])
            admitted = int(s.conn.execute(
                'SELECT COUNT(*) FROM onsale_session WHERE show_id = %s AND epoch = %s',
                (show_id, inventory_epoch),
            ).fetchone()[0])
        result = self.flags()
        result.update({
            'artifactVersion': version, 'sourceCommitPosition': version,
            'showId': show_id, 'inventoryEpoch': inventory_epoch,
            'waiting': waiting, 'admitted': admitted,
        })
        return result

    def session_view(self, session_id, principal):
        """Bounded admitted-session snapshot (contract §2). Authorization is
        checked against the stored principal; there is no seat stream."""
        _non_empty_str(session_id, 'session_id')
        _non_empty_str(principal, 'principal')
        s = self.session
        with s.guard:
            row = s.conn.execute(
                'SELECT session_id, command_id, principal, show_id, epoch, shard_id, '
                'created_ms, crc FROM onsale_session WHERE session_id = %s',
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        document = row_document('onsale_session', row[:7])
        if row_crc('onsale_session', document) != int(row[7]):
            raise StoreError('CHECKSUM_MISMATCH')
        if document['principal'] != principal:
            raise StoreError('FORBIDDEN')
        result = self.flags()
        result.update({
            'sessionId': document['session_id'], 'commandId': document['command_id'],
            'showId': document['show_id'], 'inventoryEpoch': document['epoch'],
            'shardId': document['shard_id'], 'createdAtMs': document['created_ms'],
            'state': 'ADMITTED',
        })
        return result

    def shard_hints(self, show_id, inventory_epoch, now_ms):
        """Read-only routing observations (contract §3). effectiveRemaining is
        a hint; the commit-time shard check remains the authority."""
        now_ms = _now(now_ms)
        _non_empty_str(show_id, 'show_id')
        _epoch(inventory_epoch)
        s = self.session
        with s.guard:
            shards = s.conn.execute(
                'SELECT shard_id, remaining FROM onsale_ga_shard '
                'WHERE show_id = %s AND epoch = %s ORDER BY shard_id',
                (show_id, inventory_epoch),
            ).fetchall()
            observations = []
            for shard_id, remaining in shards:
                outstanding = self._outstanding(show_id, inventory_epoch, shard_id, now_ms)
                hint = self._latest_hint(show_id, inventory_epoch, shard_id)
                observations.append({
                    'shardId': shard_id,
                    'observedRemaining': int(remaining),
                    'outstandingUnexpiredTokens': outstanding,
                    'effectiveRemaining': max(0, int(remaining) - outstanding),
                    'negativeHint': hint,
                })
        return observations

    def negative_hint(self, show_id, inventory_epoch, shard_id, now_ms):
        """The latest valid versioned negative view, or None. Never permanent."""
        now_ms = _now(now_ms)
        with self.session.guard:
            hint = self._latest_hint(show_id, inventory_epoch, shard_id)
        if hint is None or hint['expiresAtMs'] <= now_ms:
            return None
        return hint

    def table_counts(self):
        with self.session.guard:
            return self.session.table_counts()

    def usage(self):
        with self.session.guard:
            return self.session.usage()

    def close(self):
        self.session.close()

    # -- command pipeline ------------------------------------------------------
    def _apply(self, request, now_ms, snapshot_fn, decide_fn, *, needs_key_version):
        now_ms = _now(now_ms)
        s = self.session
        decision = None
        try:
            with s.transaction() as tx:
                snapshot = snapshot_fn(request, now_ms)
                if needs_key_version:
                    decision = decide_fn(snapshot, request, self.limits, self.spec,
                                         self.key, self.key_version, now_ms)
                else:
                    decision = decide_fn(snapshot, request, self.limits, self.spec,
                                         self.key, now_ms)
                if not decision.writes:
                    tx.abort()
                else:
                    self._write(_command_of(request), request.principal,
                                payload_sha256(request.payload()), decision, now_ms)
        except CommitUnknown:
            return self._failure('unknown', 'COMMIT_UNKNOWN')
        except psycopg.Error as exc:
            return self._failure('error', exc.__class__.__name__)
        return self._result(decision)

    def _write(self, command, principal, digest, decision, now_ms):
        s = self.session
        conn = s.conn
        if decision.store_command:
            insert_row(conn, 'onsale_command', {
                'command_id': command, 'principal': principal, 'payload_sha256': digest,
                'first_result': decision.first_result, 'outcome': decision.outcome,
                'created_ms': now_ms,
            })
        if decision.store_observation:
            document = {
                'observation_id': decision.observation_id, 'command_id': command,
                'payload_sha256': digest, 'nbytes': decision.nbytes, 'created_ms': now_ms,
            }
            conn.execute(
                'INSERT INTO observation (observation_id, command_id, payload_sha256, nbytes, '
                'created_ms, crc) VALUES (%s, %s, %s, %s, %s, %s)',
                (decision.observation_id, command, digest, decision.nbytes, now_ms,
                 durable_row_crc('observation', document)),
            )
            s.ledger_insert('obs:' + decision.observation_id, 'observation',
                            decision.nbytes, now_ms)
        if decision.ticket is not None:
            insert_row(conn, 'onsale_queue_ticket', decision.ticket)
        if decision.token is not None:
            insert_row(conn, 'onsale_token', decision.token)
        if decision.issue_state is not None:
            insert_row(conn, 'onsale_token_state', decision.issue_state)
        if decision.terminal is not None:
            insert_row(conn, 'onsale_token_state', decision.terminal)
            s.ledger_close(decision.terminal['ledger_entry_id'])
        if decision.shard_decrement is not None:
            show_id, epoch, shard_id = decision.shard_decrement
            updated = conn.execute(
                'UPDATE onsale_ga_shard SET remaining = remaining - 1 '
                'WHERE show_id = %s AND epoch = %s AND shard_id = %s AND remaining > 0',
                (show_id, epoch, shard_id),
            )
            if updated.rowcount != 1:
                raise StoreError('JOURNAL_RECORD')
        if decision.session is not None:
            insert_row(conn, 'onsale_session', decision.session)
        if decision.evidence is not None:
            insert_row(conn, 'onsale_evidence', decision.evidence)
        if decision.hint is not None:
            insert_row(conn, 'onsale_hint', decision.hint)
        if decision.ledger is not None:
            entry_id, budget_class, nbytes, is_open = decision.ledger
            s.ledger_insert(entry_id, budget_class, nbytes, now_ms, is_open=is_open)
        if decision.ledger_close is not None and decision.terminal is None:
            s.ledger_close(decision.ledger_close)

    def _result(self, decision):
        result = self._result_fields(decision.outcome)
        result.update({
            'first_result': decision.first_result,
            'reason': decision.reason,
            'budget_class': decision.budget_class,
            'capacity_reason': decision.capacity_reason,
            'sold_hint': decision.sold_hint,
        })
        return result

    def _result_fields(self, outcome, **extra):
        result = self.flags()
        result['outcome'] = outcome
        result.update(extra)
        return result

    def _failure(self, outcome, error):
        result = self._result_fields(outcome)
        result.update({
            'first_result': '', 'reason': None, 'budget_class': None,
            'capacity_reason': None, 'sold_hint': None, 'error': error,
        })
        return result

    # -- snapshot readers (fail closed on any checksum mismatch) ---------------
    def _read_row(self, table, where, params):
        columns = ', '.join(ONSALE_COLUMNS[table])
        row = self.session.conn.execute(
            'SELECT %s, crc FROM %s WHERE %s' % (columns, table, where), params,
        ).fetchone()
        if row is None:
            return None
        width = len(row) - 1
        document = row_document(table, row[:width])
        if row_crc(table, document) != int(row[width]):
            raise StoreError('CHECKSUM_MISMATCH')
        return document

    def _command_row(self, command_id):
        return self._read_row('onsale_command', 'command_id = %s', (command_id,))

    def _config_row(self, show_id, epoch):
        return self._read_row('onsale_ga_config', 'show_id = %s AND epoch = %s',
                              (show_id, epoch))

    def _shard_row(self, show_id, epoch, shard_id):
        row = self._read_row('onsale_ga_shard',
                             'show_id = %s AND epoch = %s AND shard_id = %s',
                             (show_id, epoch, shard_id))
        if row is None:
            return None
        remaining = self.session.conn.execute(
            'SELECT remaining FROM onsale_ga_shard '
            'WHERE show_id = %s AND epoch = %s AND shard_id = %s',
            (show_id, epoch, shard_id),
        ).fetchone()[0]
        row['remaining'] = int(remaining)
        return row

    def _ticket_row(self, ticket_id):
        return self._read_row('onsale_queue_ticket', 'queue_ticket_id = %s', (ticket_id,))

    def _token_row(self, ticket_id, nonce):
        tid = tokens.token_id(ticket_id, nonce)
        return self._read_row('onsale_token', 'token_id = %s', (tid,))

    def _latest_state(self, token_id):
        row = self.session.conn.execute(
            'SELECT state, seq FROM onsale_token_state WHERE token_id = %s '
            'ORDER BY seq DESC LIMIT 1',
            (token_id,),
        ).fetchone()
        return (None, 0) if row is None else (row[0], int(row[1]))

    def _conflict_retained(self, command_id, digest):
        return self.session.conn.execute(
            'SELECT 1 FROM observation WHERE observation_id = %s',
            ('obs-' + command_id + '-' + digest,),
        ).fetchone() is not None

    def _ticket_evidence_count(self, ticket_id):
        return int(self.session.conn.execute(
            'SELECT COUNT(*) FROM onsale_evidence WHERE queue_ticket_id = %s',
            (ticket_id,),
        ).fetchone()[0])

    def _outstanding(self, show_id, epoch, shard_id, now_ms):
        return int(self.session.conn.execute(
            'SELECT COUNT(*) FROM onsale_token t JOIN onsale_token_state st '
            'ON st.token_id = t.token_id WHERE t.show_id = %s AND t.epoch = %s '
            'AND t.shard_id = %s '
            'AND st.seq = (SELECT MAX(seq) FROM onsale_token_state WHERE token_id = t.token_id) '
            "AND st.state = 'ISSUED' AND t.expires_at_ms > %s",
            (show_id, epoch, shard_id, now_ms),
        ).fetchone()[0])

    def _outstanding_total(self, show_id, epoch, now_ms):
        return int(self.session.conn.execute(
            'SELECT COUNT(*) FROM onsale_token t JOIN onsale_token_state st '
            'ON st.token_id = t.token_id WHERE t.show_id = %s AND t.epoch = %s '
            'AND st.seq = (SELECT MAX(seq) FROM onsale_token_state WHERE token_id = t.token_id) '
            "AND st.state = 'ISSUED' AND t.expires_at_ms > %s",
            (show_id, epoch, now_ms),
        ).fetchone()[0])

    def _latest_hint(self, show_id, epoch, shard_id):
        row = self.session.conn.execute(
            'SELECT version, source_commit_position, expires_at_ms, reason '
            'FROM onsale_hint WHERE show_id = %s AND epoch = %s AND shard_id = %s '
            'ORDER BY version DESC LIMIT 1',
            (show_id, epoch, shard_id),
        ).fetchone()
        if row is None:
            return None
        return negative_hint_document(
            shard_id=shard_id, inventory_epoch=epoch, version=int(row[0]),
            source_commit_position=int(row[1]), expires_at_ms=int(row[2]), reason=row[3],
        )

    def _snapshot_enqueue(self, request, now_ms):
        command = _command_of(request)
        digest = payload_sha256(request.payload())
        now_outstanding = self._outstanding_total(
            request.show_id, request.inventory_epoch, now_ms)
        next_seq = int(self.session.conn.execute(
            'SELECT COALESCE(MAX(seq), 0) + 1 FROM onsale_queue_ticket '
            'WHERE show_id = %s AND epoch = %s',
            (request.show_id, request.inventory_epoch),
        ).fetchone()[0])
        return EnqueueSnapshot(
            existing=self._command_row(command),
            conflict_retained=self._conflict_retained(command, digest),
            config=self._config_row(request.show_id, request.inventory_epoch),
            shard=self._shard_row(request.show_id, request.inventory_epoch, request.shard_id),
            outstanding=now_outstanding,
            next_seq=next_seq,
            usage=self.session.usage(),
        )

    def _snapshot_admit(self, request, now_ms):
        command = _command_of(request)
        digest = payload_sha256(request.payload())
        presented = request.token
        ticket_id = presented.get('queueTicketId')
        nonce = presented.get('nonce')
        token = None
        state, state_seq = (None, 0)
        ticket = None
        ticket_sequence = 0
        if isinstance(ticket_id, str) and ticket_id and isinstance(nonce, str) and nonce:
            token = self._token_row(ticket_id, nonce)
            ticket = self._ticket_row(ticket_id)
            if token is not None:
                state, state_seq = self._latest_state(token['token_id'])
            if ticket is not None:
                ticket_sequence = self._ticket_evidence_count(ticket_id)
        shard_id = token['shard_id'] if token is not None else presented.get('shardId')
        hint_version = 0
        if isinstance(shard_id, str) and shard_id:
            row = self.session.conn.execute(
                'SELECT COALESCE(MAX(version), 0) FROM onsale_hint '
                'WHERE show_id = %s AND epoch = %s AND shard_id = %s',
                (request.show_id, request.inventory_epoch, shard_id),
            ).fetchone()
            hint_version = int(row[0])
        session_count = int(self.session.conn.execute(
            'SELECT COUNT(*) FROM onsale_session WHERE show_id = %s AND epoch = %s',
            (request.show_id, request.inventory_epoch),
        ).fetchone()[0])
        return AdmitSnapshot(
            existing=self._command_row(command),
            conflict_retained=self._conflict_retained(command, digest),
            config=self._config_row(request.show_id, request.inventory_epoch),
            shard=(self._shard_row(request.show_id, request.inventory_epoch, shard_id)
                   if isinstance(shard_id, str) and shard_id else None),
            token=token, token_state=state, token_state_seq=state_seq,
            ticket=ticket, ticket_sequence=ticket_sequence,
            session_count=session_count, hint_version=hint_version,
            commit_position=self.session.commit_position(),
            usage=self.session.usage(),
        )

    def _snapshot_reissue(self, request, now_ms):
        command = _command_of(request)
        digest = payload_sha256(request.payload())
        ticket = self._ticket_row(request.queue_ticket_id)
        old_token = self._token_row(request.queue_ticket_id, request.old_nonce)
        old_state, old_state_seq = (None, 0)
        if old_token is not None:
            old_state, old_state_seq = self._latest_state(old_token['token_id'])
        new_tid = tokens.token_id(request.queue_ticket_id, request.new_nonce)
        new_exists = self.session.conn.execute(
            'SELECT 1 FROM onsale_token WHERE token_id = %s', (new_tid,),
        ).fetchone() is not None
        return ReissueSnapshot(
            existing=self._command_row(command),
            conflict_retained=self._conflict_retained(command, digest),
            config=self._config_row(request.show_id, request.inventory_epoch),
            old_token=old_token, old_state=old_state, old_state_seq=old_state_seq,
            ticket=ticket,
            ticket_sequence=(self._ticket_evidence_count(request.queue_ticket_id)
                             if ticket is not None else 0),
            new_shard=self._shard_row(request.show_id, request.inventory_epoch,
                                      request.new_shard_id),
            new_token_exists=new_exists,
            outstanding=self._outstanding_total(
                request.show_id, request.inventory_epoch, now_ms),
            usage=self.session.usage(),
        )


__all__ = ['AdmissionUnit']
