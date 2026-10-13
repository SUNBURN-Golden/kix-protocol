"""In-process hosts for the five catalogue FSM machines.

Wired the way the FSM tests wire a successful call: the settlement machine is
the settlement source, the reservation machine is the ticket source, and the
resale machine is the admission ownership source. Calls run on the gate's
single core worker. This host does not open a journal and does not attach a
payment, KYC, venue, or bank adapter.

Real-funds credit kinds stay refusals inside the existing credit machine.
"""
from __future__ import annotations

import hashlib
import sys

from integration_gate.fsm_contract import MACHINE_TABLE, ROOT, load_fsm


class FsmRejected(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _load_classes():
    for spec in MACHINE_TABLE:
        directory = str(ROOT / spec['sysPath'])
        if directory not in sys.path:
            sys.path.insert(0, directory)
    from admission_fsm import AdmissionError, AdmissionMachine
    from credit_fsm import CreditError, CreditMachine
    from reservation_fsm import ReservationError, ReservationMachine, _canonical
    from resale_fsm import ResaleError, ResaleMachine
    from settlement_fsm import SettlementError, SettlementMachine
    return {
        'AdmissionError': AdmissionError,
        'AdmissionMachine': AdmissionMachine,
        'CreditError': CreditError,
        'CreditMachine': CreditMachine,
        'ReservationError': ReservationError,
        'ReservationMachine': ReservationMachine,
        'ResaleError': ResaleError,
        'ResaleMachine': ResaleMachine,
        'SettlementError': SettlementError,
        'SettlementMachine': SettlementMachine,
        '_canonical': _canonical,
    }


class FsmHost:
    def __init__(self, root=None):
        classes = _load_classes()
        document, _bytes = load_fsm(root)
        settlement = classes['SettlementMachine']()
        reservation = classes['ReservationMachine'](settlement)
        resale = classes['ResaleMachine'](
            ticket_source=reservation,
            settlement_source=settlement,
        )
        admission = classes['AdmissionMachine'](
            ticket_source=reservation,
            ownership_source=resale,
            settlement_source=settlement,
        )
        credit = classes['CreditMachine'](settlement_source=settlement)
        self.machines = {
            'settlement': settlement,
            'reservation': reservation,
            'resale': resale,
            'admission': admission,
            'credit': credit,
        }
        self._errors = (
            classes['SettlementError'],
            classes['ReservationError'],
            classes['ResaleError'],
            classes['AdmissionError'],
            classes['CreditError'],
        )
        self._commands = document['commands']
        self._queries = document['queries']
        self._canonical = classes['_canonical']

    def call(self, action, body):
        spec = self._commands[action]
        method = getattr(self.machines[spec['machine']], spec['op'])
        subject = body[spec['subject_field']]
        kwargs = {
            key: value
            for key, value in body.items()
            if key != spec['subject_field']
        }
        try:
            return method(subject, **kwargs)
        except self._errors as exc:
            raise FsmRejected(exc.code) from exc

    def read(self, action, body):
        """Dispatch one approved point query. Does not append a journal entry."""
        spec = self._queries[action]
        machine = self.machines[spec['machine']]
        method = getattr(machine, spec['method'])
        subject = body[spec['subject_field']]
        kwargs = {
            key: value
            for key, value in body.items()
            if key != spec['subject_field']
        }
        try:
            result = method(subject, **kwargs)
        except self._errors as exc:
            raise FsmRejected(exc.code) from exc
        digest = hashlib.sha256(
            self._canonical({'action': action, 'body': body}).encode('utf-8')
        ).hexdigest()
        return {
            'read_schema_version': '0.1',
            'query': action,
            'query_digest': digest,
            'fixture_mode': 'REFERENCE_IN_MEMORY',
            'accepted_through': machine.accepted_through(),
            'result': result,
        }
