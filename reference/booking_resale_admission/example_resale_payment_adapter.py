"""Actual local session: observe synthetic payment, then explicitly transfer.

Run: python3 reference/booking_resale_admission/example_resale_payment_adapter.py
All values are synthetic fixture choices, never approved product policy.
"""

import json

from example_resale_offer_adapter import FIXTURE_EXPIRY, FIXTURE_PRICE, build_fixture
from fake_resale_offer_source import FakeResaleOfferSource
from fake_resale_payment_source import FakeResalePaymentSource
from resale_session import ResaleSession

FIXTURE_RESALE_PAYMENT = "cd" * 32  # Existing opaque mock representation, not a derived ref.


def run_example(*, hold: bool = True) -> dict:
    tickets, machine = build_fixture()
    offer = dict(
        offer_id="offer-1", right_id="issue-1", version=1, seller_role="buyer-1",
        recipient_role="buyer-2", amount=FIXTURE_PRICE, expires_ms=FIXTURE_EXPIRY,
        reservation_id="reserve-1",
    )
    payments = FakeResalePaymentSource(recordings={"payment-record-1": json.dumps(dict(
        listing_id="list-1", payment_ref=FIXTURE_RESALE_PAYMENT,
        amount=FIXTURE_PRICE, buyer_role="buyer-2",
    ))})
    session = ResaleSession(
        machine, FakeResaleOfferSource(recordings={"offer-1": json.dumps(offer)}),
        payment_source=payments,
    )
    session.list_resale("offer-1", listing_id="list-1", idempotency_key="list-key")
    if hold:
        session.hold_buy("buy-hold", listing_id="list-1", buyer_role="buyer-2",
                         idempotency_key="hold-key")
    before = session.view_right("issue-1")["right"]
    tickets_before = (tickets.canonical_state(), tickets.state_digest(), tickets.export_journal())
    journal = machine.export_journal()

    # Request 1 stops at an observation. It performs no transfer or settlement.
    payment = session.observe_recorded_payment(
        "payment-record-1", listing_id="list-1", idempotency_key="payment-key",
    )
    paused = session.view("list-1")
    after = session.view_right("issue-1")["right"]
    assert paused["phase"] == "PAYMENT_NOTED"
    assert (after["holder_role"], after["version"]) == (before["holder_role"], before["version"])
    assert paused["settlement_id"] is None and paused["settlement_gate"] == "UNBOUND"
    assert [row["op"] for row in machine.export_journal()[len(journal):]] == ["observe_resale_payment"]

    # Request 2 is a separate caller action; it changes only local resale ownership.
    transfer = session.accept_resale(
        "transfer-1", listing_id="list-1", idempotency_key="transfer-key",
    )
    assert transfer["listing"]["phase"] == "TRANSFERRED"
    assert transfer["right"]["holder_role"] == "buyer-2"
    assert transfer["right"]["version"] == before["version"] + 1
    assert (tickets.canonical_state(), tickets.state_digest(), tickets.export_journal()) == tickets_before
    return dict(payment=payment, paused=paused, transfer=transfer, source_calls=payments.calls)


if __name__ == "__main__":
    print(json.dumps(run_example(), indent=2, sort_keys=True))
