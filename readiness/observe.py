"""Transport observations for the local readiness wrapper.

These dicts are not protocol events, not a canonical ledger, and not audit
evidence. They never carry a command body or an FSM journal entry.
"""

from __future__ import annotations

_FALSE_FLAGS = (
    'protocolTruth',
    'productionConformance',
    'productionReadiness',
    'productionEndpoint',
)
_BANNED = frozenset({'body', 'entry', 'args', 'limits', 'scope', 'period', 'authority'})


class ObservationError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def boundary_observation(machine, journal_decision, **fields):
    """One in-memory observation of an FSM boundary call.

    ``fields`` may name a fault code or an appended-entry count. It must not
    carry the entry or the call arguments.
    """
    if not isinstance(machine, str) or not machine:
        raise ObservationError('OBSERVATION')
    payload = {
        'component': 'readiness-boundary',
        'machine': machine,
        'journalDecision': journal_decision,
        'fsmDurable': False,
    }
    payload.update(fields)
    return _finish(payload)


def _finish(payload):
    if _BANNED & set(payload):
        raise ObservationError('OBSERVATION_BODY')
    record = {flag: False for flag in _FALSE_FLAGS}
    record.update(payload)
    for flag in _FALSE_FLAGS:
        if record.get(flag) is not False:
            raise ObservationError('OBSERVATION_LABEL')
    if record.get('fsmDurable') is not False:
        raise ObservationError('OBSERVATION_LABEL')
    return record
