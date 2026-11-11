"""The durable business unit.

One serializable PostgreSQL transaction commits the command identity, payload
sha256, first result, reservation slot, minimal order, external intent (the
outbox row) and its budget ledger entry together. Replay returns the stored
first result and adds no row. Capacity writes nothing. A COMMIT that fails
after it was sent is reported as outcome "unknown"; the next apply of the same
command id reads the truth from the database.
"""

from __future__ import annotations

import psycopg

from readiness.store import StoreError

from durable.errors import CommitUnknown
from durable.inbox import DurableInbox
from durable.model import INTENT_KIND, Snapshot, decide, payload_sha256
from durable.outbox import Outbox
from durable.schema import DurableSession, row_crc, row_document

_FLAGS = {
    'protocolTruth': False,
    'productionConformance': False,
    'productionReadiness': False,
    'productionEndpoint': False,
    'fundsExecuted': False,
    'chainWriter': False,
    'fsmDurable': False,
}


def _now(now_ms):
    if isinstance(now_ms, bool) or not isinstance(now_ms, int) or now_ms < 0:
        raise StoreError('JOURNAL_RECORD')
    return now_ms


class DurableUnit:
    def __init__(self, cluster, directory, spec):
        self.spec = spec
        self.session = DurableSession(cluster, directory, spec)
        self.inbox = DurableInbox(self.session)
        self.outbox = Outbox(self.session)

    def flags(self):
        return dict(_FLAGS)

    def apply(self, command, now_ms):
        now_ms = _now(now_ms)
        s = self.session
        decision = None
        try:
            with s.transaction() as tx:
                snapshot = self._snapshot(command)
                decision = decide(snapshot, command, self.spec, now_ms)
                if not decision.writes:
                    tx.abort()
                else:
                    self._write(command, decision, now_ms)
        except CommitUnknown:
            return self._failure('unknown', 'COMMIT_UNKNOWN')
        except psycopg.Error as exc:
            return self._failure('error', exc.__class__.__name__)
        return self._result(decision)

    def read_amount(self, command_id):
        s = self.session
        with s.guard:
            row = self._command_row(command_id)
            return None if row is None else row['amount_u128']

    def table_counts(self):
        with self.session.guard:
            return self.session.table_counts()

    def usage(self):
        with self.session.guard:
            return self.session.usage()

    def close(self):
        self.session.close()

    def _command_row(self, command_id):
        row = self.session.conn.execute(
            'SELECT command_id, payload_sha256, first_result, outcome, amount_u128, '
            'admitted_bytes, created_ms, crc FROM command_result WHERE command_id = %s',
            (command_id,),
        ).fetchone()
        if row is None:
            return None
        document = row_document('command_result', row[:7])
        if row_crc('command_result', document) != int(row[7]):
            raise StoreError('CHECKSUM_MISMATCH')
        return document

    def _snapshot(self, command):
        conn = self.session.conn
        existing = self._command_row(command.command_id)
        slot_holder = None
        slot = conn.execute(
            'SELECT show_id, slot, command_id, crc FROM slot_hold WHERE show_id = %s AND slot = %s',
            (command.show_id, command.slot),
        ).fetchone()
        if slot is not None:
            document = row_document('slot_hold', slot[:3])
            if row_crc('slot_hold', document) != int(slot[3]):
                raise StoreError('CHECKSUM_MISMATCH')
            slot_holder = document['command_id']
        retained = False
        if existing is not None and existing['payload_sha256'] != payload_sha256(command):
            retained = conn.execute(
                'SELECT 1 FROM observation WHERE observation_id = %s',
                ('obs-' + command.command_id + '-' + payload_sha256(command),),
            ).fetchone() is not None
        return Snapshot(
            existing=existing, slot_holder=slot_holder, conflict_retained=retained,
            usage=self.session.usage(),
        )

    def _write(self, command, decision, now_ms):
        s = self.session
        conn = s.conn
        digest = payload_sha256(command)
        if decision.store_command:
            outcome = decision.outcome
            document = {
                'command_id': command.command_id, 'payload_sha256': digest,
                'first_result': decision.first_result, 'outcome': outcome,
                'amount_u128': command.amount_u128, 'admitted_bytes': decision.nbytes,
                'created_ms': now_ms,
            }
            conn.execute(
                'INSERT INTO command_result (command_id, payload_sha256, first_result, outcome, '
                'amount_u128, admitted_bytes, created_ms, crc) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (command.command_id, digest, decision.first_result, outcome, command.amount_u128,
                 decision.nbytes, now_ms, row_crc('command_result', document)),
            )
            # An entry stays open while its external intent can still be dispatched.
            s.ledger_insert(
                'cmd:' + command.command_id, decision.budget_class, decision.nbytes, now_ms,
                is_open=decision.store_intent,
            )
        if decision.store_slot:
            document = {'show_id': command.show_id, 'slot': command.slot, 'command_id': command.command_id}
            conn.execute(
                'INSERT INTO slot_hold (show_id, slot, command_id, crc) VALUES (%s, %s, %s, %s)',
                (command.show_id, command.slot, command.command_id, row_crc('slot_hold', document)),
            )
        if decision.store_order:
            document = {
                'order_id': decision.order_id, 'command_id': command.command_id,
                'amount_u128': command.amount_u128,
            }
            conn.execute(
                'INSERT INTO minimal_order (order_id, command_id, amount_u128, crc) '
                'VALUES (%s, %s, %s, %s)',
                (decision.order_id, command.command_id, command.amount_u128,
                 row_crc('minimal_order', document)),
            )
        if decision.store_intent:
            document = {
                'intent_id': decision.intent_id, 'command_id': command.command_id,
                'kind': INTENT_KIND, 'payload_sha256': digest, 'created_ms': now_ms,
            }
            conn.execute(
                'INSERT INTO outbox_intent (intent_id, command_id, kind, payload_sha256, '
                'created_ms, crc) VALUES (%s, %s, %s, %s, %s, %s)',
                (decision.intent_id, command.command_id, INTENT_KIND, digest, now_ms,
                 row_crc('outbox_intent', document)),
            )
        if decision.store_observation:
            document = {
                'observation_id': decision.observation_id, 'command_id': command.command_id,
                'payload_sha256': digest, 'nbytes': decision.nbytes, 'created_ms': now_ms,
            }
            conn.execute(
                'INSERT INTO observation (observation_id, command_id, payload_sha256, nbytes, '
                'created_ms, crc) VALUES (%s, %s, %s, %s, %s, %s)',
                (decision.observation_id, command.command_id, digest, decision.nbytes, now_ms,
                 row_crc('observation', document)),
            )
            s.ledger_insert('obs:' + decision.observation_id, 'observation', decision.nbytes, now_ms)

    def _result(self, decision):
        return {
            'outcome': decision.outcome,
            'first_result': decision.first_result,
            'order_id': decision.order_id,
            'intent_id': decision.intent_id,
            'capacity_class': decision.capacity_class,
            'capacity_reason': decision.capacity_reason,
            'localDurableData': True,
        }

    @staticmethod
    def _failure(outcome, error):
        return {
            'outcome': outcome,
            'first_result': '',
            'order_id': None,
            'intent_id': None,
            'capacity_class': None,
            'capacity_reason': None,
            'error': error,
            'localDurableData': True,
        }
