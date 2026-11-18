"""Durable outbox. External intents are committed with the business result
(see unit.py). A dispatch attempt is recorded before the dispatcher is called,
and its outcome is recorded after. An attempt without a recorded outcome, or
with an UNKNOWN outcome, is never converted to "not sent". The stable
operation identity is the intent id; a retry reuses it.

The default dispatcher is a fixture that does not call anything. Wiring a real
provider call is outside this node (locks in PROGRAM_DECISIONS_20260928 §5).
"""

from __future__ import annotations

import json

import psycopg

from readiness.codec import canonical_json
from readiness.store import StoreError

from durable.errors import Backpressure, CommitUnknown
from durable.schema import row_crc, row_document

FIXTURE_DISPATCH_KIND = 'FIXTURE_NOT_DISPATCHED'


def fixture_dispatcher(_intent):
    return {'dispatched': False, 'kind': FIXTURE_DISPATCH_KIND}


def _valid_result(result):
    return (
        isinstance(result, dict)
        and isinstance(result.get('dispatched'), bool)
        and isinstance(result.get('kind'), str)
        and bool(result['kind'])
    )


class Outbox:
    def __init__(self, session):
        self.session = session

    def pending(self):
        """Intents whose last known state is not DISPATCHED, oldest first."""
        s = self.session
        with s.guard:
            rows = s.conn.execute(
                'SELECT intent_id, command_id, kind, payload_sha256, created_ms, crc '
                'FROM outbox_intent ORDER BY created_ms, intent_id'
            ).fetchall()
            pending = []
            for row in rows:
                intent = self._intent_from_row(row)
                state = self._state(intent['intentId'])
                if state['state'] != 'DISPATCHED':
                    intent.update(state)
                    pending.append(intent)
            return pending

    def status(self, intent_id):
        s = self.session
        with s.guard:
            self._intent(intent_id)
            return self._state(intent_id)

    def record_attempt(self, intent_id, now_ms, dispatcher=fixture_dispatcher):
        s = self.session
        if isinstance(now_ms, bool) or not isinstance(now_ms, int):
            raise StoreError('JOURNAL_RECORD')
        with s.guard:
            intent = self._intent(intent_id)
            state = self._state(intent_id)
            if state['state'] == 'DISPATCHED':
                return {'duplicate': True, 'state': 'DISPATCHED', 'attemptNo': state['attempts']}
            attempt_no = state['attempts'] + 1
            budget_class = 'completion' if attempt_no == 1 else 'recovery'
            entry_id = 'attempt:%s:%d' % (intent_id, attempt_no)
            attempting = canonical_json({'intentId': intent_id, 'attemptNo': attempt_no})
            self._write_attempt(
                intent_id, attempt_no, 'ATTEMPTING', attempting, now_ms,
                budget_class=budget_class, entry_id=entry_id, nbytes=len(attempting.encode()),
            )
            call = dict(intent)
            call['attemptNo'] = attempt_no
            call['previousState'] = state['state']
            try:
                result = dispatcher(call)
                if not _valid_result(result):
                    raise ValueError('dispatcher result shape')
                outcome = {'dispatched': result['dispatched'], 'kind': result['kind'], 'unknown': False}
            except Exception as exc:
                outcome = {
                    'dispatched': False, 'kind': 'DISPATCHER_EXCEPTION', 'unknown': True,
                    'error': type(exc).__name__,
                }
            try:
                self._write_attempt(
                    intent_id, attempt_no, 'OUTCOME', canonical_json(outcome), now_ms,
                    close_entry=(entry_id, intent['commandId']) if outcome['dispatched'] else None,
                )
            except (psycopg.Error, CommitUnknown) as exc:
                raise StoreError('OUTBOX_OUTCOME_NOT_RECORDED') from exc
            return {
                'duplicate': False, 'attemptNo': attempt_no, 'budgetClass': budget_class,
                'state': self._state_of_outcome(outcome),
            }

    def _write_attempt(self, intent_id, attempt_no, phase, result, now_ms, *,
                       budget_class=None, entry_id=None, nbytes=0, close_entry=None):
        s = self.session
        with s.transaction() as tx:
            if budget_class is not None:
                usage = s.usage()[budget_class]
                code, reason = s.spec.check(
                    budget_class, used_count=usage.count, used_bytes=usage.nbytes,
                    oldest_open_ms=usage.oldest_open_ms, now_ms=now_ms, extra_bytes=nbytes,
                )
                if code != 'OK':
                    tx.abort()
                    raise Backpressure('OUTBOX_CAPACITY', budget_class, reason)
            document = {
                'intent_id': intent_id, 'attempt_no': attempt_no, 'phase': phase,
                'result': result, 'at_ms': now_ms,
            }
            s.conn.execute(
                'INSERT INTO outbox_attempt (intent_id, attempt_no, phase, result, at_ms, crc) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (intent_id, attempt_no, phase, result, now_ms,
                 row_crc('outbox_attempt', document)),
            )
            if budget_class is not None:
                s.ledger_insert(entry_id, budget_class, nbytes, now_ms)
            if close_entry is not None:
                s.ledger_close(close_entry[0])
                s.ledger_close('cmd:' + close_entry[1])

    def _intent(self, intent_id):
        row = self.session.conn.execute(
            'SELECT intent_id, command_id, kind, payload_sha256, created_ms, crc '
            'FROM outbox_intent WHERE intent_id = %s', (intent_id,),
        ).fetchone()
        if row is None:
            raise StoreError('UNKNOWN_INTENT')
        return self._intent_from_row(row)

    @staticmethod
    def _intent_from_row(row):
        document = row_document('outbox_intent', row[:5])
        if row_crc('outbox_intent', document) != int(row[5]):
            raise StoreError('CHECKSUM_MISMATCH')
        return {
            'intentId': document['intent_id'],
            'commandId': document['command_id'],
            'kind': document['kind'],
            'payloadSha256': document['payload_sha256'],
        }

    def _state(self, intent_id):
        rows = self.session.conn.execute(
            'SELECT intent_id, attempt_no, phase, result, at_ms, crc FROM outbox_attempt '
            'WHERE intent_id = %s ORDER BY attempt_no, phase', (intent_id,),
        ).fetchall()
        attempts = 0
        last = None
        for row in rows:
            document = row_document('outbox_attempt', row[:5])
            if row_crc('outbox_attempt', document) != int(row[5]):
                raise StoreError('CHECKSUM_MISMATCH')
            attempts = max(attempts, int(document['attempt_no']))
            last = document
        if last is None:
            return {'state': 'PENDING', 'attempts': 0}
        if last['phase'] == 'ATTEMPTING':
            return {'state': 'ATTEMPTING', 'attempts': attempts}
        return {'state': self._state_of_outcome(json.loads(last['result'])), 'attempts': attempts}

    @staticmethod
    def _state_of_outcome(outcome):
        if outcome['dispatched']:
            return 'DISPATCHED'
        if outcome['unknown']:
            return 'UNKNOWN'
        return 'NOT_DISPATCHED'
