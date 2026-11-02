"""Sequential in-memory admission workflow; lifecycle and receipts belong to FSMs."""

from admission_fsm import AdmissionMachine
from presentation_adapter import PresentationAdapter
from presentation_source import PresentationSource


class AdmissionSession:
    def __init__(self, machine: AdmissionMachine, source: PresentationSource) -> None:
        self._machine = machine
        self._adapter = PresentationAdapter(machine, source)

    def authorize_admission(
        self, presentation_id: str, *, admission_id: str, idempotency_key: str,
        gate_role: str, expires_ms: int,
    ) -> dict:
        return self._adapter.authorize_admission(
            presentation_id, admission_id=admission_id, idempotency_key=idempotency_key,
            gate_role=gate_role, expires_ms=expires_ms,
        )

    def consume(
        self, presentation_id: str, *, consume_id: str, idempotency_key: str,
        gate_role: str,
    ) -> dict:
        return self._adapter.consume(
            presentation_id, consume_id=consume_id, idempotency_key=idempotency_key,
            gate_role=gate_role,
        )

    def view(self, right_id: str) -> dict:
        return self._machine.view(right_id)

    def view_credential(self, right_id: str, *, version: int, holder_role: str) -> dict:
        return self._machine.view_credential(right_id, version=version, holder_role=holder_role)

    def set_clock(self, subject_id: str, *, idempotency_key: str, now_ms: int) -> dict:
        # AdmissionMachine delegates to reservation, but does not advance resale.
        return self._machine.set_clock(subject_id, idempotency_key=idempotency_key, now_ms=now_ms)
