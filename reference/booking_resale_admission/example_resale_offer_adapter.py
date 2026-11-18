"""Run with python3 reference/booking_resale_admission/example_resale_offer_adapter.py.

All values are synthetic fixture choices, never approved product policy.
Setup injects an already-observed primary-payment fact; it sends no payment.
"""

import json

from fake_resale_offer_source import FakeResaleOfferSource
from mock_gates import OFFER_WINDOW_MS
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleError, ResaleMachine
from resale_offer_adapter import ResaleOfferAdapter

FIXTURE_NOW = 1_000_000
FIXTURE_PRICE = 10_001
FIXTURE_EXPIRY = FIXTURE_NOW + OFFER_WINDOW_MS
FIXTURE_PAYMENT = "ab" * 32


def build_fixture() -> tuple[ReservationMachine, ResaleMachine]:
    """Register, issue and adopt through actual public local-machine APIs."""
    tickets = ReservationMachine()
    tickets.set_clock("clock", idempotency_key="ticket-clock", now_ms=FIXTURE_NOW)
    show = dict(
        organizer_role="organizer", capacity=2, gate_roles=["gate-a", "gate-b"],
        primary_price=FIXTURE_PRICE, resale_cap=20_000, resale_allowed=True,
        organizer_bps=1, platform_bps=1,
    )
    tickets.register_show("show-1", idempotency_key="show", **show)
    tickets.hold(
        "reserve-1", idempotency_key="hold", show_id="show-1", slot=0,
        buyer_role="buyer-1", expires_ms=FIXTURE_EXPIRY,
    )
    tickets.confirm(
        "order-1", idempotency_key="confirm", reservation_id="reserve-1",
        amount=FIXTURE_PRICE, quote_ref="quote-1",
    )
    tickets.observe_payment(
        "order-1", idempotency_key="payment", payment_ref=FIXTURE_PAYMENT, amount=FIXTURE_PRICE,
    )
    tickets.issue("issue-1", idempotency_key="issue", order_id="order-1")
    resale = ResaleMachine(ticket_source=tickets)
    resale.set_clock("clock", idempotency_key="resale-clock", now_ms=FIXTURE_NOW)
    resale.adopt_issued(
        "issue-1", idempotency_key="resale-adopt", show_id="show-1", slot=0,
        buyer_role="buyer-1", expires_ms=FIXTURE_EXPIRY, order_id="order-1",
        amount=FIXTURE_PRICE, payment_ref=FIXTURE_PAYMENT, reservation_id="reserve-1",
        quote_ref="quote-1", **show,
    )
    return tickets, resale


def run_example() -> dict:
    tickets, resale = build_fixture()
    tickets_before = tickets.canonical_state()
    right_before = resale.view_right("issue-1")["right"]
    journal_before = resale.export_journal()
    offer = dict(
        offer_id="offer-1", right_id="issue-1", version=1, seller_role="buyer-1",
        recipient_role="buyer-2", amount=FIXTURE_PRICE, expires_ms=FIXTURE_EXPIRY,
        reservation_id="reserve-1",
    )
    source = FakeResaleOfferSource(recordings={"offer-1": json.dumps(offer)})
    adapter = ResaleOfferAdapter(resale, source)
    listed = adapter.list_resale("offer-1", listing_id="list-1", idempotency_key="list-key")
    try:
        adapter.list_resale("offer-1", listing_id="list-2", idempotency_key="competing-key")
    except ResaleError as error:
        refusal = error.code
    else:
        raise AssertionError("competing listing must be refused")
    assert refusal == "RIGHT_SALE_LOCKED"
    assert tickets.canonical_state() == tickets_before
    right_after = resale.view_right("issue-1")["right"]
    assert (right_after["holder_role"], right_after["version"]) == (
        right_before["holder_role"], right_before["version"],
    )
    assert [row["op"] for row in resale.export_journal()[len(journal_before):]] == ["list_resale"]
    return {"listed": listed, "competing_refusal": refusal, "source_calls": source.calls}


if __name__ == "__main__":
    print(json.dumps(run_example(), indent=2, sort_keys=True))
