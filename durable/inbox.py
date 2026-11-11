"""Adapter durable inbox (docs/adr/0001-ktx-authority-commit-recovery.md Appendix B).

Order of one receive:
  1. the raw bytes, scope, raw hash and verification result are committed;
  2. the injected authenticated lookup yields items, each normalized to one
     fact and evidence_hash, and the item rows plus durable event aliases are
     committed;
  3. only then the injected apply hook (the kernel/FSM call) runs per item;
  4. the receipt ACK is returned.
Failure to persist or a full budget raises Backpressure and no ACK exists.
UnknownOperation keeps the item UNMATCHED: it is never deleted and never marked
applied. The same event key with a different fact is stored as separate
conflict evidence; nothing is overwritten. UNMATCHED and CONFLICT are contract
terms here, not kernel enums.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager

import psycopg

from readiness.codec import canonical_json
from readiness.store import StoreError

from durable.errors import Backpressure, CommitUnknown, UnknownOperation
from durable.normalize import normalize_items, resolve_alias
from durable.schema import row_crc, row_document

RECEIVED = 'RECEIVED'
APPLIED = 'APPLIED'
UNMATCHED = 'UNMATCHED'
DUPLICATE = 'DUPLICATE'

FIRST = 'FIRST'
SAME_FACT = 'SAME_FACT'
CONFLICT = 'CONFLICT'


class SqlAliasStore:
    """Durable alias table: external key -> EventItemId, conflict-checked."""

    def __init__(self, conn):
        self.conn = conn

    def get(self, scope_key, fact_key):
        row = self.conn.execute(
            'SELECT scope_key, fact_key, event_item_id, crc FROM event_alias '
            'WHERE scope_key = %s AND fact_key = %s', (scope_key, fact_key),
        ).fetchone()
        return self._checked(row)

    def get_by_id(self, scope_key, event_item_id):
        row = self.conn.execute(
            'SELECT scope_key, fact_key, event_item_id, crc FROM event_alias '
            'WHERE scope_key = %s AND event_item_id = %s', (scope_key, event_item_id),
        ).fetchone()
        if row is None:
            return None
        self._checked(row)
        return row[1]

    def put(self, scope_key, fact_key, event_item_id):
        document = {'scope_key': scope_key, 'fact_key': fact_key, 'event_item_id': event_item_id}
        self.conn.execute(
            'INSERT INTO event_alias (scope_key, fact_key, event_item_id, crc) '
            'VALUES (%s, %s, %s, %s)',
            (scope_key, fact_key, event_item_id, row_crc('event_alias', document)),
        )

    @staticmethod
    def _checked(row):
        if row is None:
            return None
        document = row_document('event_alias', row[:3])
        if row_crc('event_alias', document) != int(row[3]):
            raise StoreError('CHECKSUM_MISMATCH')
        return document['event_item_id']


def _int(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StoreError('JOURNAL_RECORD')
    return value


@contextmanager
def _persisting(code):
    """Persistence failure or an unknown commit means no ACK."""
    try:
        yield
    except CommitUnknown as exc:
        raise Backpressure(code + '_UNKNOWN') from exc
    except psycopg.Error as exc:
        raise Backpressure(code + '_FAILED') from exc


class DurableInbox:
    def __init__(self, session):
        self.session = session

    def receive(self, scope, raw, *, verification_result, received_ms, now_ms,
                lookup_fn, apply_fn, headers=None):
        """Persist, normalize, apply, then ACK. Returns the ACK record.

        The session guard is held for the whole call, so one process cannot
        offer the same item to the apply hook twice at once.
        """
        with self.session.guard:
            return self._receive(
                scope, raw, verification_result, received_ms, now_ms, lookup_fn, apply_fn, headers,
            )

    def _receive(self, scope, raw, verification_result, received_ms, now_ms,
                 lookup_fn, apply_fn, headers):
        delivery_id, is_new = self.persist_raw(
            scope, raw, verification_result=verification_result,
            received_ms=received_ms, now_ms=now_ms, headers=headers,
        )
        if not self.items_of(delivery_id):
            provider_items = lookup_fn(bytes(raw))
            self.persist_items(delivery_id, scope, normalize_items(scope, provider_items), now_ms)
        self.process_delivery(delivery_id, apply_fn, now_ms)
        items = self.items_of(delivery_id)
        return {
            'ack': True,
            'deliveryId': delivery_id,
            'newDelivery': is_new,
            'items': [
                {
                    'itemId': item['itemId'],
                    'eventItemId': item['eventItemId'],
                    'relation': item['relation'],
                    'state': item['state'],
                }
                for item in items
            ],
        }

    def persist_raw(self, scope, raw, *, verification_result, received_ms, now_ms, headers=None):
        if not isinstance(raw, (bytes, bytearray)) or not raw:
            raise StoreError('JOURNAL_RECORD')
        if not isinstance(verification_result, str) or not verification_result:
            raise StoreError('JOURNAL_RECORD')
        _int(received_ms)
        _int(now_ms)
        raw = bytes(raw)
        raw_sha256 = hashlib.sha256(raw).hexdigest()
        scope_key = scope.key()
        delivery_id = hashlib.sha256(
            canonical_json([scope_key, raw_sha256]).encode('utf-8')
        ).hexdigest()
        headers_json = canonical_json(headers or {})
        s = self.session
        with _persisting('INBOX_PERSIST'):
            with s.transaction() as tx:
                known = s.conn.execute(
                    'SELECT 1 FROM inbox_delivery WHERE delivery_id = %s', (delivery_id,),
                ).fetchone()
                if known is not None:
                    tx.abort()
                    return delivery_id, False
                usage = s.usage()['inflow']
                code, reason = s.spec.check(
                    'inflow', used_count=usage.count, used_bytes=usage.nbytes,
                    oldest_open_ms=usage.oldest_open_ms, now_ms=now_ms, extra_bytes=len(raw),
                )
                if code != 'OK':
                    tx.abort()
                    raise Backpressure('INBOX_CAPACITY', 'inflow', reason)
                document = {
                    'delivery_id': delivery_id, 'scope_key': scope_key, 'raw_sha256': raw_sha256,
                    'headers_json': headers_json, 'received_ms': received_ms,
                    'verification_result': verification_result,
                }
                s.conn.execute(
                    'INSERT INTO inbox_delivery (delivery_id, scope_key, raw, raw_sha256, '
                    'headers_json, received_ms, verification_result, crc) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (delivery_id, scope_key, raw, raw_sha256, headers_json, received_ms,
                     verification_result, row_crc('inbox_delivery', document, raw)),
                )
                s.ledger_insert('inbox:' + delivery_id, 'inflow', len(raw), now_ms)
        return delivery_id, True

    def persist_items(self, delivery_id, scope, normalized, now_ms):
        """Commit the per-item rows and aliases of one delivery, once."""
        _int(now_ms)
        s = self.session
        with _persisting('INBOX_PERSIST'):
            with s.transaction() as tx:
                if self._item_count(delivery_id):
                    tx.abort()
                    return
                alias_store = SqlAliasStore(s.conn)
                first_in_delivery = {}
                plan = []
                for index, fact in enumerate(normalized):
                    event_item_id = resolve_alias(alias_store, fact.scope_key, fact.fact_key)
                    first_hash = first_in_delivery.get(event_item_id)
                    if first_hash is None:
                        row = s.conn.execute(
                            'SELECT i.evidence_hash FROM inbox_item i '
                            'JOIN inbox_delivery d ON i.delivery_id = d.delivery_id '
                            'WHERE d.scope_key = %s AND i.event_item_id = %s AND i.relation = %s',
                            (fact.scope_key, event_item_id, FIRST),
                        ).fetchone()
                        first_hash = None if row is None else row[0]
                    if first_hash is None:
                        relation = FIRST
                        first_in_delivery[event_item_id] = fact.evidence_hash
                    elif first_hash == fact.evidence_hash:
                        relation = SAME_FACT
                    else:
                        relation = CONFLICT
                    plan.append((index, fact, event_item_id, relation))
                evidence = [(fact, rel) for _i, fact, _e, rel in plan if rel != FIRST]
                if evidence:
                    usage = s.usage()['observation']
                    code, reason = s.spec.check(
                        'observation', used_count=usage.count, used_bytes=usage.nbytes,
                        oldest_open_ms=usage.oldest_open_ms, now_ms=now_ms,
                        extra_count=len(evidence),
                        extra_bytes=sum(len(f.fact_json.encode('utf-8')) for f, _r in evidence),
                    )
                    if code != 'OK':
                        raise Backpressure('INBOX_CAPACITY', 'observation', reason)
                for index, fact, event_item_id, relation in plan:
                    item_id = hashlib.sha256(
                        canonical_json([delivery_id, index]).encode('utf-8')
                    ).hexdigest()
                    document = {
                        'item_id': item_id, 'delivery_id': delivery_id, 'item_index': index,
                        'fact_key': fact.fact_key, 'event_item_id': event_item_id,
                        'evidence_hash': fact.evidence_hash, 'fact_json': fact.fact_json,
                        'relation': relation,
                    }
                    s.conn.execute(
                        'INSERT INTO inbox_item (item_id, delivery_id, item_index, fact_key, '
                        'event_item_id, evidence_hash, fact_json, relation, crc) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (item_id, delivery_id, index, fact.fact_key, event_item_id,
                         fact.evidence_hash, fact.fact_json, relation,
                         row_crc('inbox_item', document)),
                    )
                    self._append_state(item_id, 1, DUPLICATE if relation == SAME_FACT else RECEIVED, now_ms)
                    if relation != FIRST:
                        s.ledger_insert(
                            'evidence:' + item_id, 'observation',
                            len(fact.fact_json.encode('utf-8')), now_ms,
                        )

    def process_delivery(self, delivery_id, apply_fn, now_ms):
        """Apply every item still RECEIVED. UnknownOperation leaves UNMATCHED."""
        for item in self.items_of(delivery_id):
            if item['state'] == RECEIVED:
                self._apply_item(item, apply_fn, now_ms)

    def reconcile(self, apply_fn, now_ms):
        """Re-run UNMATCHED items with their stored raw once a binding exists.

        Items that carry no operation reference are not offered to apply_fn.
        Returns the item ids that moved to APPLIED.
        """
        moved = []
        for item in self.items(state=UNMATCHED):
            if item['fact']['operation'] is None:
                continue
            if self._apply_item(item, apply_fn, now_ms) == APPLIED:
                moved.append(item['itemId'])
        return moved

    def items_of(self, delivery_id):
        return self._views('i.delivery_id = %s', (delivery_id,))

    def items(self, state=None, relation=None):
        found = self._views('1 = 1', ())
        if state is not None:
            found = [item for item in found if item['state'] == state]
        if relation is not None:
            found = [item for item in found if item['relation'] == relation]
        return found

    def state_log(self, item_id):
        s = self.session
        with s.guard:
            rows = s.conn.execute(
                'SELECT item_id, seq, state, at_ms, crc FROM inbox_state '
                'WHERE item_id = %s ORDER BY seq', (item_id,),
            ).fetchall()
            log = []
            for row in rows:
                document = row_document('inbox_state', row[:4])
                if row_crc('inbox_state', document) != int(row[4]):
                    raise StoreError('CHECKSUM_MISMATCH')
                log.append((int(document['seq']), document['state']))
            return log

    def _apply_item(self, item, apply_fn, now_ms):
        if item['fact']['operation'] is None:
            outcome = UNMATCHED
        else:
            try:
                apply_fn(item)
                outcome = APPLIED
            except UnknownOperation:
                outcome = UNMATCHED
        with _persisting('INBOX_STATE'):
            self._set_state(item['itemId'], item['deliveryId'], outcome, now_ms)
        return outcome

    def _set_state(self, item_id, delivery_id, state, now_ms):
        s = self.session
        with s.transaction() as tx:
            latest = s.conn.execute(
                'SELECT seq, state FROM inbox_state WHERE item_id = %s ORDER BY seq DESC LIMIT 1',
                (item_id,),
            ).fetchone()
            if latest[1] == state or latest[1] == APPLIED:
                tx.abort()
                return
            self._append_state(item_id, int(latest[0]) + 1, state, now_ms)
            if self._delivery_settled(delivery_id):
                s.ledger_close('inbox:' + delivery_id)

    def _delivery_settled(self, delivery_id):
        rows = self.session.conn.execute(
            'SELECT item_id FROM inbox_item WHERE delivery_id = %s', (delivery_id,),
        ).fetchall()
        for (item_id,) in rows:
            latest = self.session.conn.execute(
                'SELECT state FROM inbox_state WHERE item_id = %s ORDER BY seq DESC LIMIT 1',
                (item_id,),
            ).fetchone()
            if latest[0] in (RECEIVED, UNMATCHED):
                return False
        return True

    def _append_state(self, item_id, seq, state, now_ms):
        document = {'item_id': item_id, 'seq': seq, 'state': state, 'at_ms': now_ms}
        self.session.conn.execute(
            'INSERT INTO inbox_state (item_id, seq, state, at_ms, crc) VALUES (%s, %s, %s, %s, %s)',
            (item_id, seq, state, now_ms, row_crc('inbox_state', document)),
        )

    def _item_count(self, delivery_id):
        return int(self.session.conn.execute(
            'SELECT COUNT(*) FROM inbox_item WHERE delivery_id = %s', (delivery_id,),
        ).fetchone()[0])

    def _views(self, where, params):
        s = self.session
        with s.guard:
            rows = s.conn.execute(
                'SELECT i.item_id, i.delivery_id, i.item_index, i.fact_key, i.event_item_id, '
                'i.evidence_hash, i.fact_json, i.relation, i.crc, d.raw, d.raw_sha256, '
                'd.verification_result, d.scope_key FROM inbox_item i '
                'JOIN inbox_delivery d ON i.delivery_id = d.delivery_id WHERE ' + where +
                ' ORDER BY i.delivery_id, i.item_index', params or None,
            ).fetchall()
            views = []
            for row in rows:
                document = row_document('inbox_item', row[:8])
                if row_crc('inbox_item', document) != int(row[8]):
                    raise StoreError('CHECKSUM_MISMATCH')
                latest = s.conn.execute(
                    'SELECT state FROM inbox_state WHERE item_id = %s ORDER BY seq DESC LIMIT 1',
                    (row[0],),
                ).fetchone()
                views.append({
                    'itemId': row[0],
                    'deliveryId': row[1],
                    'itemIndex': int(row[2]),
                    'factKey': row[3],
                    'eventItemId': row[4],
                    'evidenceHash': row[5],
                    'fact': json.loads(row[6]),
                    'relation': row[7],
                    'raw': bytes(row[9]),
                    'rawSha256': row[10],
                    'verificationResult': row[11],
                    'scopeKey': row[12],
                    'state': None if latest is None else latest[0],
                })
            return views
