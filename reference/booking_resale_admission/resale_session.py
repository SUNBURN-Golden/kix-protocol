"""Explicit sequential resale actions; all lifecycle decisions belong to the FSM."""

from resale_fsm import ResaleMachine
from resale_offer_adapter import ResaleOfferAdapter
from resale_offer_source import ResaleOfferSource


class ResaleSession:
    def __init__(self, machine: ResaleMachine, source: ResaleOfferSource) -> None:
        self._machine = machine
        self._adapter = ResaleOfferAdapter(machine, source)

    def list_resale(self, offer_id: str, *, listing_id: str, idempotency_key: str) -> dict:
        return self._adapter.list_resale(
            offer_id, listing_id=listing_id, idempotency_key=idempotency_key,
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

    def view(self, listing_id: str) -> dict:
        return self._machine.view(listing_id)

    def view_right(self, right_id: str) -> dict:
        return self._machine.view_right(right_id)

    def view_presentation(self, right_id: str, *, version: int, holder_role: str) -> dict:
        return self._machine.view_presentation(right_id, version=version, holder_role=holder_role)
