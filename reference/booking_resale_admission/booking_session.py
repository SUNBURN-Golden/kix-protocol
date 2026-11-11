"""Explicit booking and fulfillment desk over a caller-supplied in-memory reservation FSM."""

from mock_gates import GateError, _ident
from reservation_fsm import ReservationMachine
from booking_quote_source import BookingQuoteSourceError, InvalidBookingQuoteRecord
from calculated_booking_quote_source import calculate_booking_quote


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

    def preview_calculated_quote(self, request_text: str) -> dict:
        """Return a calculation only, without consulting reservation state."""
        try:
            return calculate_booking_quote(request_text)
        except BookingQuoteSourceError:
            raise
        except Exception as error:
            raise BookingQuoteSourceError("booking quote fetch failed") from error

    def confirm_calculated_quote(self, request_text: str, *, reservation_id: str,
                                 order_id: str, idempotency_key: str) -> dict:
        """Calculate caller text once, then use ordinary mock confirmation validation."""
        try:
            for value in (reservation_id, order_id, idempotency_key):
                _ident(value)
        except GateError as error:
            raise InvalidBookingQuoteRecord(error.code) from error
        # Recalculate on every valid invocation, including replay. Only calculation
        # failures are source errors; session and FSM exceptions pass through.
        try:
            quote = calculate_booking_quote(request_text)
        except BookingQuoteSourceError:
            raise
        except Exception as error:
            raise BookingQuoteSourceError("booking quote fetch failed") from error
        return self.confirm(order_id, reservation_id=reservation_id,
                            amount=int(quote["totals"]["payableAtoms"]),
                            quote_ref=quote["quoteHash"], idempotency_key=idempotency_key)

    def cancel(self, reservation_id: object, *, idempotency_key: object) -> dict:
        self._require_clock()
        return self._machine.cancel(reservation_id, idempotency_key=idempotency_key)

    def bind_settlement(self, reservation_id: object, *, settlement_id: object,
                        idempotency_key: object) -> dict:
        self._require_clock()
        return self._machine.bind_settlement(
            reservation_id, settlement_id=settlement_id, idempotency_key=idempotency_key,
        )

    def issue(self, issuance_id: object, *, order_id: object, idempotency_key: object) -> dict:
        self._require_clock()
        return self._machine.issue(issuance_id, order_id=order_id, idempotency_key=idempotency_key)

    def reconcile(self, reservation_id: object, *, idempotency_key: object) -> dict:
        return self._machine.reconcile(reservation_id, idempotency_key=idempotency_key)

    def view(self, reservation_id: object) -> dict:
        return self._machine.view(reservation_id)

    def view_show(self, show_id: object) -> dict:
        return self._machine.view_show(show_id)
