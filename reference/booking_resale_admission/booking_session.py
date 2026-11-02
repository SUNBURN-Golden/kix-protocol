"""Explicit pre-payment desk over a caller-supplied in-memory reservation FSM."""

from mock_gates import GateError, _ident
from reservation_fsm import ReservationMachine


class BookingInputError(ValueError):
    """Missing local prerequisites; not a protocol rejection or retained FSM key."""


class BookingSession:
    def __init__(self, machine: ReservationMachine):
        self._machine = machine
        self._clock_initialized = False

    def _require_clock(self):
        if not self._clock_initialized:
            raise BookingInputError("explicit successful session set_clock required before mutation")

    def set_clock(self, subject_id: object, *, now_ms: object, idempotency_key: object) -> dict:
        receipt = self._machine.set_clock(subject_id, now_ms=now_ms, idempotency_key=idempotency_key)
        self._clock_initialized = True
        return receipt

    def register_show(self, show_id: object, *, organizer_role: object, capacity: object,
                      gate_roles: object, primary_price: object, resale_cap: object,
                      resale_allowed: object, organizer_bps: object, platform_bps: object,
                      idempotency_key: object) -> dict:
        self._require_clock()
        return self._machine.register_show(
            show_id, organizer_role=organizer_role, capacity=capacity, gate_roles=gate_roles,
            primary_price=primary_price, resale_cap=resale_cap, resale_allowed=resale_allowed,
            organizer_bps=organizer_bps, platform_bps=platform_bps, idempotency_key=idempotency_key,
        )

    def hold(self, reservation_id: object, *, show_id: object, slot: object, buyer_role: object,
             expires_ms: object, idempotency_key: object) -> dict:
        self._require_clock()
        return self._machine.hold(reservation_id, show_id=show_id, slot=slot, buyer_role=buyer_role,
                                  expires_ms=expires_ms, idempotency_key=idempotency_key)

    def release(self, reservation_id: object, *, idempotency_key: object) -> dict:
        self._require_clock()
        return self._machine.release(reservation_id, idempotency_key=idempotency_key)

    def confirm(self, order_id: object, *, reservation_id: object, amount: object,
                quote_ref: object, idempotency_key: object) -> dict:
        self._require_clock()
        try:
            _ident(quote_ref)
        except GateError as error:
            raise BookingInputError(f"explicit valid quote_ref required: {error.code}") from error
        return self._machine.confirm(order_id, reservation_id=reservation_id, amount=amount,
                                     quote_ref=quote_ref, idempotency_key=idempotency_key)

    def cancel(self, reservation_id: object, *, idempotency_key: object) -> dict:
        self._require_clock()
        return self._machine.cancel(reservation_id, idempotency_key=idempotency_key)

    def view(self, reservation_id: object) -> dict:
        return self._machine.view(reservation_id)

    def view_show(self, show_id: object) -> dict:
        return self._machine.view_show(show_id)
