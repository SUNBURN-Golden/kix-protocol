"""Named budget and overload decisions for the local readiness wrapper.

The numeric caps are the existing readiness contract values. This module does
not define a product SLO, a queue, or a new error code. Callers still reject
with JOURNAL_BUDGET or OVERLOADED. A rejected attempt is not retained.
"""

from __future__ import annotations

# Same caps as docs/contracts/READINESS_RUNTIME.md and integration_gate.constants.
DEFAULT_MAX_IN_FLIGHT = 8
DEFAULT_MAX_JOURNAL_RECORDS = 4096
DEFAULT_MAX_JOURNAL_BYTES = 8 * 1024 * 1024


def classify_budget(record_count, committed_bytes, extra, max_records, max_bytes):
    """Return ('OK', None) or ('JOURNAL_BUDGET', 'records'|'bytes').

    Record count is tested first, then bytes. Equality with max_bytes is still
    acceptable. This is the same predicate ReadinessStore.can_accept used.
    """
    if record_count >= max_records:
        return 'JOURNAL_BUDGET', 'records'
    if committed_bytes + extra > max_bytes:
        return 'JOURNAL_BUDGET', 'bytes'
    return 'OK', None


class AdmitGate:
    """Bounded in-flight admissions. There is no waiting queue."""

    def __init__(self, max_in_flight=DEFAULT_MAX_IN_FLIGHT):
        if not isinstance(max_in_flight, int) or max_in_flight < 1:
            raise ValueError('REFUSING_LIMITS')
        self.max_in_flight = max_in_flight
        self.admitted = 0

    def try_admit(self):
        if self.admitted >= self.max_in_flight:
            return 'OVERLOADED'
        self.admitted += 1
        return 'OK'

    def release(self):
        if self.admitted > 0:
            self.admitted -= 1

    def view(self):
        return {
            'inFlight': self.admitted,
            'maxInFlight': self.max_in_flight,
            'queued': 0,
        }
