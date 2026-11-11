"""Run with python3 reference/booking_resale_admission/example_presentation_adapter.py.

All values and policy below are synthetic fixture choices, not product defaults.
Setup, clocks and credential adoption are explicit and outside the adapter.
"""

import json
import sys
from pathlib import Path

from admission_fsm import AdmissionMachine
from fake_presentation_source import FakePresentationSource
from presentation_adapter import PresentationAdapter
from reservation_fsm import ReservationMachine
from resale_fsm import ResaleMachine

_SETTLEMENT_DIR = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT_DIR) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT_DIR))

from settlement_fsm import SettlementMachine  # noqa: E402

FIXTURE_NOW = 1_000_000
FIXTURE_PRICE = 10_001
FIXTURE_PAYMENT = "ab" * 32
FIXTURE_REQUEST = "11" * 32
FIXTURE_AUTH_EXPIRY = FIXTURE_NOW + 60_000


def build_fixture() -> tuple[SettlementMachine, ReservationMachine, ResaleMachine, AdmissionMachine]:
    """Create actual local machines with explicit synthetic settlement bindings."""
    book = SettlementMachine()
    book.initiate(
        "claim-1", idempotency_key="init-claim", trade_id="fixture-trade",
        gross=FIXTURE_PRICE, debtor_role="fixture-merchant",
        policy={"kind": "PRIMARY_FEE_BPS", "fee_bps": 0,
                "residual_payee": "organizer", "fee_payee": "platform"},
    )
    book.authorize("claim-1", idempotency_key="auth-claim")
    book.capture("claim-1", idempotency_key="capture-claim")
    book.commit(
        "claim-1", idempotency_key="commit-claim", movement_id="fixture-movement",
        gross=FIXTURE_PRICE, amount=FIXTURE_PRICE, fee=0, tax=0, held=0, adjustment=0,
    )
    tickets = ReservationMachine(book)
    tickets.set_clock("clock", idempotency_key="ticket-clock", now_ms=FIXTURE_NOW)
    show = dict(
        organizer_role="organizer", capacity=2, gate_roles=["gate-a", "gate-b"],
        primary_price=FIXTURE_PRICE, resale_cap=20_000, resale_allowed=True,
        organizer_bps=1, platform_bps=1,
    )
    tickets.register_show("show-1", idempotency_key="show", **show)
    tickets.hold(
        "reserve-1", idempotency_key="hold", show_id="show-1", slot=0,
        buyer_role="buyer-1", expires_ms=FIXTURE_NOW + 120_000,
    )
    tickets.confirm(
        "order-1", idempotency_key="confirm", reservation_id="reserve-1",
        amount=FIXTURE_PRICE, quote_ref="quote-1",
    )
    tickets.observe_payment(
        "order-1", idempotency_key="payment", payment_ref=FIXTURE_PAYMENT,
        amount=FIXTURE_PRICE,
    )
    tickets.bind_settlement("reserve-1", idempotency_key="bind", settlement_id="claim-1")
    tickets.issue("issue-1", idempotency_key="issue", order_id="order-1")
    adopted = dict(
        show_id="show-1", slot=0, buyer_role="buyer-1",
        expires_ms=FIXTURE_NOW + 120_000, order_id="order-1", amount=FIXTURE_PRICE,
        payment_ref=FIXTURE_PAYMENT, reservation_id="reserve-1", quote_ref="quote-1",
        **show,
    )
    resale = ResaleMachine(ticket_source=tickets)
    resale.set_clock("clock", idempotency_key="resale-clock", now_ms=FIXTURE_NOW)
    resale.adopt_issued("issue-1", idempotency_key="resale-adopt", **adopted)
    admission = AdmissionMachine(
        ticket_source=tickets, ownership_source=resale, settlement_source=book,
    )
    admission.set_clock("clock", idempotency_key="admission-clock", now_ms=FIXTURE_NOW)
    admission.adopt_issued("issue-1", idempotency_key="admission-adopt", **adopted)
    return book, tickets, resale, admission


def run_example() -> dict:
    book, tickets, _resale, admission = build_fixture()
    settlement_before = book.canonical_state()
    common = {"right_id": "issue-1", "version": 1, "request": FIXTURE_REQUEST}
    source = FakePresentationSource(recordings={
        ("authorize_admission", "fixture-ticket"): json.dumps(common | {"holder_role": "buyer-1"}),
        ("consume", "fixture-ticket"): json.dumps(common),
    })
    adapter = PresentationAdapter(admission, source)
    authorized = adapter.authorize_admission(
        "fixture-ticket", admission_id="fixture-admission", idempotency_key="fixture-auth-key",
        gate_role="gate-a", expires_ms=FIXTURE_AUTH_EXPIRY,
    )
    phase_after_authorization = tickets.view("reserve-1")["phase"]
    assert phase_after_authorization == "ADMISSION_AUTHORIZED"
    assert tickets.view("reserve-1")["right"]["version"] == 1
    consumed = adapter.consume(
        "fixture-ticket", consume_id="fixture-consume", idempotency_key="fixture-consume-key",
        gate_role="gate-a",
    )
    journal = admission.export_journal()
    replay = adapter.consume(
        "fixture-ticket", consume_id="fixture-consume", idempotency_key="fixture-consume-key",
        gate_role="gate-a",
    )
    assert replay["duplicate"] is True
    assert admission.export_journal() == journal
    assert tickets.view("reserve-1")["right"]["version"] == 2
    assert book.canonical_state() == settlement_before
    return {
        "phase_after_authorization": phase_after_authorization,
        "authorized": authorized, "consumed": consumed, "replay": replay,
        "source_calls": source.calls,
    }


if __name__ == "__main__":
    print(json.dumps(run_example(), indent=2, sort_keys=True))
