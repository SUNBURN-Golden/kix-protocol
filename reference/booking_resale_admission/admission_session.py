"""Sequential in-memory admission workflow; lifecycle and receipts belong to FSMs."""

from admission_fsm import AdmissionMachine
from presentation_adapter import PresentationAdapter
from presentation_source import PresentationSource


class AdmissionSession:
    def __init__(self, machine: AdmissionMachine, source: PresentationSource) -> None:
        self._machine = machine
        self._adapter = PresentationAdapter(machine, source)

    def adopt_issued(
        self, right_id: object, *, idempotency_key: object, show_id: object,
        organizer_role: object, capacity: object, gate_roles: object,
        primary_price: object, resale_cap: object, resale_allowed: object,
        organizer_bps: object, platform_bps: object, slot: object, buyer_role: object,
        expires_ms: object, order_id: object, amount: object, payment_ref: object,
        reservation_id: object, quote_ref: object,
    ) -> dict:
        return self._machine.adopt_issued(
            right_id, idempotency_key=idempotency_key, show_id=show_id,
            organizer_role=organizer_role, capacity=capacity, gate_roles=gate_roles,
            primary_price=primary_price, resale_cap=resale_cap, resale_allowed=resale_allowed,
            organizer_bps=organizer_bps, platform_bps=platform_bps, slot=slot,
            buyer_role=buyer_role, expires_ms=expires_ms, order_id=order_id, amount=amount,
            payment_ref=payment_ref, reservation_id=reservation_id, quote_ref=quote_ref,
        )

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

    def reconcile(self, right_id: object, *, idempotency_key: object) -> dict:
        return self._machine.reconcile(right_id, idempotency_key=idempotency_key)

    def view(self, right_id: str) -> dict:
        return self._machine.view(right_id)

    def view_credential(self, right_id: str, *, version: int, holder_role: str) -> dict:
        return self._machine.view_credential(right_id, version=version, holder_role=holder_role)

    def set_clock(self, subject_id: str, *, idempotency_key: str, now_ms: int) -> dict:
        # AdmissionMachine delegates to reservation, but does not advance resale.
        return self._machine.set_clock(subject_id, idempotency_key=idempotency_key, now_ms=now_ms)
