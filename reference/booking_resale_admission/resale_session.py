"""Explicit sequential resale actions; all lifecycle decisions belong to the FSM."""

from resale_fsm import ResaleMachine
from resale_offer_adapter import ResaleOfferAdapter
from resale_offer_source import ResaleOfferSource
from resale_payment_adapter import ResalePaymentAdapter
from resale_payment_source import ResalePaymentSource, ResalePaymentSourceError


class ResaleSession:
    def __init__(self, machine: ResaleMachine, source: ResaleOfferSource, *,
                 payment_source: ResalePaymentSource | None = None) -> None:
        self._machine = machine
        self._adapter = ResaleOfferAdapter(machine, source)
        self._payment_adapter = (None if payment_source is None
                                 else ResalePaymentAdapter(machine, payment_source))

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

    def observe_recorded_payment(
        self, recording_id: str, *, listing_id: str, idempotency_key: str,
    ) -> dict:
        if self._payment_adapter is None:
            raise ResalePaymentSourceError("no resale payment source configured")
        return self._payment_adapter.observe_resale_payment(
            recording_id, listing_id=listing_id, idempotency_key=idempotency_key,
        )

    def list_resale(self, offer_id: str, *, listing_id: str, idempotency_key: str) -> dict:
        return self._adapter.list_resale(
            offer_id, listing_id=listing_id, idempotency_key=idempotency_key,
        )

    def list_resale_inputs(
        self, listing_id: object, *, right_id: object, version: object,
        seller_role: object, recipient_role: object, amount: object,
        expires_ms: object, idempotency_key: object, reservation_id: object,
    ) -> dict:
        return self._machine.list_resale(
            listing_id, right_id=right_id, version=version,
            seller_role=seller_role, recipient_role=recipient_role,
            amount=amount, expires_ms=expires_ms,
            idempotency_key=idempotency_key, reservation_id=reservation_id,
        )

    def hold_buy(self, hold_id: str, *, listing_id: str, buyer_role: str,
                 idempotency_key: str) -> dict:
        return self._machine.hold_buy(
            hold_id, listing_id=listing_id, buyer_role=buyer_role, idempotency_key=idempotency_key,
        )

    def release_hold(self, hold_id: str, *, buyer_role: str, idempotency_key: str) -> dict:
        return self._machine.release_hold(
            hold_id, buyer_role=buyer_role, idempotency_key=idempotency_key,
        )

    def cancel_listing(self, listing_id: str, *, seller_role: str, idempotency_key: str) -> dict:
        return self._machine.cancel_listing(
            listing_id, seller_role=seller_role, idempotency_key=idempotency_key,
        )

    def observe_resale_payment(self, listing_id: str, *, payment_ref: str, amount: int,
                               idempotency_key: str, buyer_role: str | None = None) -> dict:
        return self._machine.observe_resale_payment(
            listing_id, payment_ref=payment_ref, amount=amount, buyer_role=buyer_role,
            idempotency_key=idempotency_key,
        )

    def bind_settlement(self, listing_id: str, *, settlement_id: str, idempotency_key: str) -> dict:
        return self._machine.bind_settlement(
            listing_id, settlement_id=settlement_id, idempotency_key=idempotency_key,
        )

    def accept_resale(self, transfer_id: str, *, listing_id: str, idempotency_key: str) -> dict:
        return self._machine.accept_resale(
            transfer_id, listing_id=listing_id, idempotency_key=idempotency_key,
        )

    def close(self, listing_id: str, *, idempotency_key: str) -> dict:
        return self._machine.close(listing_id, idempotency_key=idempotency_key)

    def set_clock(self, subject_id: str, *, now_ms: int, idempotency_key: str) -> dict:
        # This clock belongs only to resale; reservation time is independent.
        return self._machine.set_clock(subject_id, now_ms=now_ms, idempotency_key=idempotency_key)

    def reconcile(self, listing_id: object, *, idempotency_key: object) -> dict:
        return self._machine.reconcile(listing_id, idempotency_key=idempotency_key)

    def view(self, listing_id: str) -> dict:
        return self._machine.view(listing_id)

    def view_right(self, right_id: str) -> dict:
        return self._machine.view_right(right_id)

    def view_presentation(self, right_id: str, *, version: int, holder_role: str) -> dict:
        return self._machine.view_presentation(right_id, version=version, holder_role=holder_role)
