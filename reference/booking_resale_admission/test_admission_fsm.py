"""Lifecycle checks for the in-memory admission machine.

Scanner, transfer, and cancel races are ordered commands in one process.
They are not threads, not a venue, and not offline admission authority.
"""

import json
import sys
import unittest
from pathlib import Path

from admission_fsm import (
    AUTHORIZED,
    CONSUMED,
    ELIGIBLE,
    REPLAYABLE,
    AdmissionError,
    AdmissionMachine,
)
from mock_gates import ADMISSION_WINDOW_MS, NON_CLAIMS, OFFER_WINDOW_MS, PROVENANCE
from reservation_fsm import ReservationError, ReservationMachine
from resale_fsm import ResaleError, ResaleMachine

_SETTLEMENT_DIR = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT_DIR) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT_DIR))

from settlement_fsm import SettlementMachine  # noqa: E402

PAY = "ab" * 32
SALE_PAY = "cd" * 32
REQ = "11" * 32
REQ_B = "22" * 32
PRICE = 10_001
T0 = 1_000_000
EXPIRES = T0 + OFFER_WINDOW_MS
ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "reference" / "v0.3-rc1" / "protocol_contract.json"


def codes(fn):
    try:
        fn()
    except AdmissionError as error:
        return error.code
    raise AssertionError("expected AdmissionError")


def reservation_codes(fn):
    try:
        fn()
    except ReservationError as error:
        return error.code
    raise AssertionError("expected ReservationError")


def resale_codes(fn):
    try:
        fn()
    except ResaleError as error:
        return error.code
    raise AssertionError("expected ResaleError")


def show_kwargs(resale_allowed=True):
    return dict(
        organizer_role="organizer",
        capacity=2,
        gate_roles=["gate-a", "gate-b"],
        primary_price=PRICE,
        resale_cap=20_000,
        resale_allowed=resale_allowed,
        organizer_bps=1,
        platform_bps=1,
    )


def policy():
    return {
        "kind": "PRIMARY_FEE_BPS",
        "fee_bps": 0,
        "residual_payee": "organizer",
        "fee_payee": "platform",
    }


def settlement_at(phase, gross=PRICE, settlement_id="claim-1"):
    book = SettlementMachine()
    book.initiate(
        settlement_id,
        idempotency_key=f"init-{settlement_id}",
        trade_id=f"trade-{settlement_id}",
        gross=gross,
        debtor_role="fixture-merchant",
        policy=policy(),
    )
    if phase == "INITIATED":
        return book
    book.authorize(settlement_id, idempotency_key=f"auth-{settlement_id}")
    if phase == "AUTHORIZED":
        return book
    book.capture(settlement_id, idempotency_key=f"cap-{settlement_id}")
    if phase == "CAPTURED":
        return book
    book.commit(
        settlement_id,
        idempotency_key=f"commit-{settlement_id}",
        movement_id=f"move-{settlement_id}",
        gross=gross,
        amount=gross,
        fee=0,
        tax=0,
        held=0,
        adjustment=0,
    )
    return book


def assert_not_final(test, body):
    test.assertEqual(body["provenance"], PROVENANCE)
    test.assertEqual(body["lifecycle_authority"], "IN_MEMORY_FSM")
    test.assertIs(body["economic_finality_claimed"], False)
    test.assertIs(body["funds_executed"], False)
    test.assertIs(body["venue_credential_reissued"], False)
    test.assertIs(body["offline_admission"], False)
    test.assertIs(body["admission_routing_production"], False)
    test.assertEqual(body["external_admission"], "UNSUPPORTED")
    test.assertEqual(body["external_payment"], "UNSUPPORTED")
    for name, value in NON_CLAIMS.items():
        test.assertIs(body[name], value)


class AdmissionFsmTests(unittest.TestCase):
    def setUp(self):
        self.tickets = self.reservation("issued")
        self.resale = ResaleMachine(ticket_source=self.tickets)
        self.resale.set_clock("clock", idempotency_key="resale-clock", now_ms=T0)
        self.machine = AdmissionMachine(ticket_source=self.tickets, ownership_source=self.resale)

    def reservation(self, stop="issued", book=None, settlement_id=None):
        machine = ReservationMachine(book)
        machine.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        machine.register_show("show-1", idempotency_key="show-1", **show_kwargs())
        machine.hold(
            "reserve-1",
            idempotency_key="hold-1",
            show_id="show-1",
            slot=0,
            buyer_role="buyer-1",
            expires_ms=EXPIRES,
        )
        if stop == "held":
            return machine
        machine.confirm(
            "order-1",
            idempotency_key="confirm-1",
            reservation_id="reserve-1",
            amount=PRICE,
            quote_ref="quote-1",
        )
        if stop == "cancelled":
            machine.cancel("reserve-1", idempotency_key="cancel-1")
            return machine
        if stop == "confirmed":
            return machine
        machine.observe_payment("order-1", idempotency_key="pay-1", payment_ref=PAY, amount=PRICE)
        if stop == "paid":
            return machine
        if settlement_id is not None:
            machine.bind_settlement("reserve-1", idempotency_key="bind-1", settlement_id=settlement_id)
        if stop == "bound":
            return machine
        machine.issue("issue-1", idempotency_key="issue-1", order_id="order-1")
        return machine

    def adopt_body(self, **changes):
        body = dict(
            show_id="show-1",
            slot=0,
            buyer_role="buyer-1",
            expires_ms=EXPIRES,
            order_id="order-1",
            amount=PRICE,
            payment_ref=PAY,
            reservation_id="reserve-1",
            quote_ref="quote-1",
        )
        body.update(show_kwargs())
        body.update(changes)
        return body

    def clock(self, now=T0, key="gate-clock"):
        return self.machine.set_clock("clock", idempotency_key=key, now_ms=now)

    def adopt(self, key="adopt-1", **changes):
        return self.machine.adopt_issued("issue-1", idempotency_key=key, **self.adopt_body(**changes))

    def sell(self, listing="list-1", key="list-1"):
        return self.resale.list_resale(
            listing,
            idempotency_key=key,
            right_id="issue-1",
            version=1,
            seller_role="buyer-1",
            recipient_role="buyer-2",
            amount=PRICE,
            expires_ms=EXPIRES,
            reservation_id="reserve-1",
        )

    def transfer(self):
        self.resale.observe_resale_payment(
            "list-1",
            idempotency_key="sale-pay",
            payment_ref=SALE_PAY,
            amount=PRICE,
            buyer_role="buyer-2",
        )
        return self.resale.accept_resale("transfer-1", idempotency_key="transfer-1", listing_id="list-1")

    def authorize(self, admission="admit-1", key="admit-1", gate="gate-a", request=REQ, version=1, holder="buyer-1", expires=None, external=None):
        if expires is None:
            expires = T0 + ADMISSION_WINDOW_MS
        return self.machine.authorize_admission(
            admission,
            idempotency_key=key,
            right_id="issue-1",
            version=version,
            holder_role=holder,
            gate_role=gate,
            request=request,
            expires_ms=expires,
            external_dependency=external,
        )

    def consume(self, consume_id="consume-1", key="consume-1", gate="gate-a", request=REQ, version=1, external=None):
        return self.machine.consume(
            consume_id,
            idempotency_key=key,
            right_id="issue-1",
            version=version,
            gate_role=gate,
            request=request,
            external_dependency=external,
        )

    def test_issued_credential_is_consumed_once_and_replay_does_not_bump_version(self):
        self.clock()
        adopted = self.adopt()
        assert_not_final(self, adopted)
        self.assertEqual(adopted["credential"]["phase"], ELIGIBLE)
        self.assertEqual(adopted["right"]["version"], 1)
        self.assertEqual(adopted["right"]["state"], "ACTIVE")
        self.assertIs(adopted["credential"]["offline_admission"], False)
        opened = self.authorize()
        assert_not_final(self, opened)
        self.assertEqual(opened["credential"]["phase"], AUTHORIZED)
        self.assertEqual(opened["admission"]["state"], "AUTHORIZED")
        self.assertEqual(self.tickets.view("reserve-1")["phase"], "ADMISSION_AUTHORIZED")
        self.assertEqual(self.tickets.view("reserve-1")["admission_id"], "admit-1")
        self.assertEqual(
            codes(lambda: self.authorize(admission="admit-2", key="admit-2", gate="gate-b", request=REQ_B)),
            "ADMISSION_LOCKED",
        )
        self.assertEqual(self.machine.view("issue-1")["phase"], AUTHORIZED)
        consumed = self.consume()
        self.assertEqual(consumed["evidence"]["decision"], "CONSUMED_ONCE")
        self.assertEqual(consumed["evidence"]["version_after"], 2)
        self.assertIs(consumed["evidence"]["admission_routing_production"], False)
        self.assertIs(consumed["evidence"]["private_proof_verified"], False)
        self.assertEqual(consumed["credential"]["phase"], CONSUMED)
        self.assertTrue(consumed["credential"]["terminal"])
        self.assertEqual(self.tickets.view("reserve-1")["phase"], "CONSUMED")
        self.assertEqual(self.tickets.view("reserve-1")["right"]["version"], 2)
        digest = self.machine.state_digest()
        for index in range(8):
            self.assertEqual(
                codes(lambda index=index: self.consume(consume_id=f"consume-extra-{index}", key=f"extra-{index}", version=2)),
                "ALREADY_CONSUMED",
            )
        self.assertEqual(self.machine.view("issue-1")["version"], 2)
        self.assertEqual(self.machine.state_digest(), digest)
        replay = self.consume()
        self.assertTrue(replay["duplicate"])
        self.assertIsNone(replay["applied"])
        self.assertEqual(replay["evidence"]["version_after"], 2)
        self.assertIs(replay["offline_admission"], False)
        frozen = self.authorize()
        self.assertTrue(frozen["duplicate"])
        self.assertEqual(frozen["credential"]["phase"], AUTHORIZED)
        self.assertEqual(self.machine.view("issue-1")["phase"], CONSUMED)
        self.assertEqual(
            codes(lambda: self.machine.reject_external("venue-scanner")),
            "EXTERNAL_UNSUPPORTED",
        )
        self.assertEqual(self.machine.state_digest(), digest)
        self.assertTrue(REPLAYABLE.isdisjoint({"admit", "open_admission", "consume_admission"}))

    def test_transfer_then_entry_rejects_both_presentations(self):
        self.resale.adopt_issued("issue-1", idempotency_key="resale-adopt", **self.adopt_body())
        self.sell()
        self.transfer()
        self.assertEqual(self.resale.view_right("issue-1")["right"]["version"], 2)
        self.assertEqual(self.resale.view_right("issue-1")["right"]["holder_role"], "buyer-2")
        self.assertIs(self.resale.view_presentation("issue-1", version=1, holder_role="buyer-1")["presentation"]["venue_credential_reissued"], False)
        self.clock()
        self.adopt()
        digest = self.machine.state_digest()
        ticket_digest = self.tickets.state_digest()
        stale = self.machine.view_credential("issue-1", version=1, holder_role="buyer-1")
        self.assertIs(stale["presentation"]["fresh"], False)
        self.assertEqual(stale["presentation"]["decision"], "STALE_VERSION")
        self.assertIs(stale["presentation"]["offline_admission"], False)
        self.assertEqual(codes(lambda: self.authorize()), "STALE_VERSION")
        moved = self.machine.view_credential("issue-1", version=2, holder_role="buyer-2")
        self.assertIs(moved["presentation"]["fresh"], False)
        self.assertEqual(moved["presentation"]["decision"], "STALE_VERSION")
        self.assertEqual(
            codes(lambda: self.authorize(version=2, holder="buyer-2", key="admit-new", admission="admit-new")),
            "STALE_VERSION",
        )
        self.assertEqual(self.machine.view("issue-1")["phase"], ELIGIBLE)
        self.assertEqual(self.tickets.view("reserve-1")["phase"], "ISSUED")
        self.assertEqual(self.tickets.view("reserve-1")["right"]["version"], 1)
        self.assertEqual(self.machine.state_digest(), digest)
        self.assertEqual(self.tickets.state_digest(), ticket_digest)
        self.assertIs(self.machine.view("issue-1")["venue_credential_reissued"], False)

    def test_entry_then_transfer_consumes_before_resale_can_move(self):
        self.resale.adopt_issued("issue-1", idempotency_key="resale-adopt", **self.adopt_body())
        self.clock()
        self.adopt()
        self.authorize()
        self.assertEqual(resale_codes(lambda: self.sell()), "ADMISSION_LOCKED")
        self.consume()
        self.assertEqual(self.tickets.view("reserve-1")["phase"], "CONSUMED")
        self.assertEqual(resale_codes(lambda: self.sell(key="list-after")), "ALREADY_CONSUMED")
        self.assertEqual(self.resale.view_right("issue-1")["right"]["holder_role"], "buyer-1")
        self.assertEqual(self.resale.view_right("issue-1")["right"]["version"], 1)

    def test_listing_and_cancel_order_against_entry(self):
        self.resale.adopt_issued("issue-1", idempotency_key="resale-adopt", **self.adopt_body())
        self.sell()
        self.clock()
        self.adopt()
        listed = self.machine.view_credential("issue-1", version=1, holder_role="buyer-1")
        self.assertEqual(listed["presentation"]["decision"], "LISTING_LOCKED")
        self.assertEqual(codes(lambda: self.authorize()), "LISTING_LOCKED")
        self.assertEqual(self.tickets.view("reserve-1")["phase"], "ISSUED")
        self.resale.cancel_listing("list-1", idempotency_key="cancel-list", seller_role="buyer-1")
        self.authorize(admission="admit-after", key="admit-after")
        self.assertEqual(self.machine.view("issue-1")["phase"], AUTHORIZED)
        self.assertEqual(resale_codes(lambda: self.sell(listing="list-2", key="list-2")), "ADMISSION_LOCKED")

    def test_cancel_before_issue_blocks_entry_and_cancel_after_issue_does_not_void_it(self):
        cancelled = self.reservation("cancelled")
        blocked = AdmissionMachine(ticket_source=cancelled)
        blocked.set_clock("clock", idempotency_key="gate-clock", now_ms=T0)
        self.assertEqual(
            codes(lambda: blocked.adopt_issued("issue-1", idempotency_key="adopt-1", **self.adopt_body())),
            "TICKET_CANCELLED",
        )
        paid = self.reservation("paid")
        early = AdmissionMachine(ticket_source=paid)
        early.set_clock("clock", idempotency_key="gate-clock", now_ms=T0)
        self.assertEqual(
            codes(lambda: early.adopt_issued("issue-1", idempotency_key="adopt-1", **self.adopt_body())),
            "TICKET_NOT_ISSUED",
        )
        self.clock()
        self.adopt()
        self.assertEqual(
            reservation_codes(lambda: self.tickets.cancel("reserve-1", idempotency_key="cancel-issued")),
            "CANCEL_AFTER_ISSUE",
        )
        self.authorize()
        self.consume()
        self.assertEqual(self.machine.view("issue-1")["phase"], CONSUMED)
        self.assertEqual(
            reservation_codes(lambda: self.tickets.cancel("reserve-1", idempotency_key="cancel-consumed")),
            "CANCEL_AFTER_ISSUE",
        )

    def test_external_sources_fail_closed_without_being_read(self):
        class Boom:
            def __getattr__(self, name):
                raise AssertionError(name)

        self.clock()
        self.adopt()
        digest = self.machine.state_digest()
        journal = self.machine.export_journal()
        self.assertEqual(codes(lambda: self.authorize(external="VENUE_IDENTITY")), "VENUE_SOURCE_UNAVAILABLE")
        self.assertEqual(codes(lambda: self.authorize(external="VENUE_IDENTITY")), "VENUE_SOURCE_UNAVAILABLE")
        self.assertEqual(codes(lambda: self.consume(external="REVOCATION")), "REVOCATION_SOURCE_UNAVAILABLE")
        self.assertEqual(codes(lambda: self.authorize(external="public-endpoint", key="admit-public", admission="admit-public")), "EXTERNAL_UNSUPPORTED")
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(self.machine.state_digest(), digest)
        self.assertEqual(self.machine.view("issue-1")["phase"], ELIGIBLE)
        configured = AdmissionMachine(ticket_source=self.tickets, venue_source=Boom(), revocation_source=Boom())
        configured.set_clock("clock", idempotency_key="gate-clock-2", now_ms=T0)
        configured.adopt_issued("issue-1", idempotency_key="adopt-configured", **self.adopt_body())
        self.assertEqual(
            codes(lambda: configured.authorize_admission(
                "admit-ext",
                idempotency_key="admit-ext",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=T0 + ADMISSION_WINDOW_MS,
            )),
            "VENUE_SOURCE_UNAVAILABLE",
        )
        observed = configured.view_credential("issue-1", version=1, holder_role="buyer-1")
        self.assertIs(observed["presentation"]["fresh"], False)
        self.assertEqual(observed["presentation"]["decision"], "VENUE_SOURCE_UNAVAILABLE")
        self.assertEqual(configured.view("issue-1")["phase"], ELIGIBLE)

    def test_unavailable_ownership_or_revocation_does_not_admit(self):
        class Down:
            def view_right(self, _right_id):
                raise RuntimeError("ownership down")

            def view_presentation(self, *_args, **_kwargs):
                raise RuntimeError("ownership down")

        self.clock()
        down = AdmissionMachine(ticket_source=self.tickets, ownership_source=Down())
        down.set_clock("clock", idempotency_key="gate-clock-down", now_ms=T0)
        down.adopt_issued("issue-1", idempotency_key="adopt-down", **self.adopt_body())
        self.assertEqual(
            codes(lambda: down.authorize_admission(
                "admit-down",
                idempotency_key="admit-down",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=T0 + ADMISSION_WINDOW_MS,
            )),
            "OWNERSHIP_SOURCE_UNAVAILABLE",
        )
        self.assertEqual(self.tickets.view("reserve-1")["phase"], "ISSUED")
        self.assertEqual(down.view("issue-1")["phase"], ELIGIBLE)

    def test_settlement_commit_is_not_entry_and_a_granted_flag_rejects(self):
        book = settlement_at("COMMITTED")
        tickets = self.reservation("issued", book=book, settlement_id="claim-1")
        before = book.canonical_state()
        gate = AdmissionMachine(ticket_source=tickets, settlement_source=book)
        gate.set_clock("clock", idempotency_key="gate-clock", now_ms=T0)
        adopted = gate.adopt_issued("issue-1", idempotency_key="adopt-1", **self.adopt_body())
        self.assertEqual(adopted["credential"]["phase"], ELIGIBLE)
        self.assertIs(book.view("claim-1")["admission_granted"], False)
        gate.authorize_admission(
            "admit-1",
            idempotency_key="admit-1",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ,
            expires_ms=T0 + ADMISSION_WINDOW_MS,
        )
        gate.consume(
            "consume-1",
            idempotency_key="consume-1",
            right_id="issue-1",
            version=1,
            gate_role="gate-a",
            request=REQ,
        )
        self.assertEqual(book.canonical_state(), before)
        self.assertIs(book.view("claim-1")["admission_granted"], False)
        self.assertEqual(gate.view("issue-1")["phase"], CONSUMED)
        self.assertEqual(tickets.view("reserve-1")["phase"], "CONSUMED")

        class Granted:
            def view(self, _settlement_id):
                return {
                    "phase": "COMMITTED",
                    "currency": "KRW",
                    "gross": PRICE,
                    "funds_executed": False,
                    "admission_granted": True,
                    "bank_debit_observed": False,
                    "legal_debtor_bound": False,
                    "durable": False,
                    "external_return_closed": False,
                    "right_cancelled": False,
                }

        book_two = settlement_at("COMMITTED", settlement_id="claim-2")
        clean = self.reservation("issued", book=book_two, settlement_id="claim-2")
        refused = AdmissionMachine(ticket_source=clean, settlement_source=Granted())
        refused.set_clock("clock", idempotency_key="gate-clock-granted", now_ms=T0)
        refused.adopt_issued("issue-1", idempotency_key="adopt-granted", **self.adopt_body())
        journal = clean.export_journal()
        self.assertEqual(
            codes(lambda: refused.authorize_admission(
                "admit-granted",
                idempotency_key="admit-granted",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=T0 + ADMISSION_WINDOW_MS,
            )),
            "SETTLEMENT_VIEW_REJECTED",
        )
        self.assertEqual(clean.export_journal(), journal)
        self.assertEqual(clean.view("reserve-1")["phase"], "ISSUED")
        missing = AdmissionMachine(ticket_source=clean, settlement_source=None)
        missing.set_clock("clock", idempotency_key="gate-clock-missing", now_ms=T0)
        missing.adopt_issued("issue-1", idempotency_key="adopt-missing", **self.adopt_body())
        self.assertEqual(
            codes(lambda: missing.authorize_admission(
                "admit-missing",
                idempotency_key="admit-missing",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=T0 + ADMISSION_WINDOW_MS,
            )),
            "SETTLEMENT_SOURCE_REQUIRED",
        )

    def test_restart_replays_journal_and_retry_is_duplicate(self):
        self.resale.adopt_issued("issue-1", idempotency_key="resale-adopt", **self.adopt_body())
        ticket_base = self.tickets.export_journal()
        resale_base = self.resale.export_journal()
        self.clock()
        self.adopt()
        self.authorize()
        consumed = self.consume()
        self.assertEqual(
            codes(lambda: self.authorize(gate="gate-b", request=REQ_B)),
            "IDEMPOTENCY_CONFLICT",
        )
        journal = self.machine.export_journal()
        digest = self.machine.state_digest()
        revived_tickets = ReservationMachine.restore(ticket_base)
        revived_resale = ResaleMachine.restore(resale_base, ticket_source=revived_tickets)
        revived = AdmissionMachine.restore(
            journal,
            ticket_source=revived_tickets,
            ownership_source=revived_resale,
        )
        self.assertEqual(revived.canonical_state(), self.machine.canonical_state())
        self.assertEqual(revived.state_digest(), digest)
        self.assertEqual(revived.view("issue-1")["phase"], CONSUMED)
        self.assertEqual(revived_tickets.view("reserve-1")["phase"], "CONSUMED")
        self.assertEqual(revived_tickets.export_journal(), self.tickets.export_journal())
        retry = revived.consume(
            "consume-1",
            idempotency_key="consume-1",
            right_id="issue-1",
            version=1,
            gate_role="gate-a",
            request=REQ,
        )
        self.assertTrue(retry["duplicate"])
        self.assertEqual(retry["evidence"]["version_after"], consumed["evidence"]["version_after"])
        matched = revived.reconcile("issue-1", idempotency_key="recon-1")
        self.assertTrue(matched["matched"])
        self.assertIs(matched["economic_finality_claimed"], False)
        again = revived.reconcile("issue-1", idempotency_key="recon-1")
        self.assertTrue(again["duplicate"])
        self.assertEqual(codes(lambda: AdmissionMachine.restore([{"op": "tamper"}])), "INVALID_JOURNAL")
        self.assertEqual(codes(lambda: AdmissionMachine.restore({"op": "consume"})), "INVALID_JOURNAL")
        shadow = ReservationMachine.restore(ticket_base)
        shadow_resale = ResaleMachine.restore(resale_base, ticket_source=shadow)
        trailed = json.loads(json.dumps(journal))
        trailed.append({"op": "tamper"})
        self.assertEqual(
            codes(lambda: AdmissionMachine.restore(
                trailed,
                ticket_source=shadow,
                ownership_source=shadow_resale,
            )),
            "INVALID_JOURNAL",
        )

    def test_unbound_mock_gate_still_rejects_a_second_scanner(self):
        gate = AdmissionMachine()
        gate.set_clock("clock", idempotency_key="gate-clock", now_ms=T0)
        body = self.adopt_body(reservation_id=None, quote_ref=None)
        gate.adopt_issued("issue-1", idempotency_key="adopt-1", **body)
        gate.authorize_admission(
            "admit-1",
            idempotency_key="admit-1",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ,
            expires_ms=T0 + ADMISSION_WINDOW_MS,
        )
        self.assertEqual(
            codes(lambda: gate.authorize_admission(
                "admit-b",
                idempotency_key="admit-b",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-b",
                request=REQ_B,
                expires_ms=T0 + ADMISSION_WINDOW_MS,
            )),
            "ADMISSION_LOCKED",
        )
        gate.consume(
            "consume-1",
            idempotency_key="consume-1",
            right_id="issue-1",
            version=1,
            gate_role="gate-a",
            request=REQ,
        )
        self.assertEqual(
            codes(lambda: gate.consume(
                "consume-b",
                idempotency_key="consume-b",
                right_id="issue-1",
                version=1,
                gate_role="gate-b",
                request=REQ_B,
            )),
            "ALREADY_CONSUMED",
        )
        restored = AdmissionMachine.restore(gate.export_journal())
        self.assertEqual(restored.canonical_state(), gate.canonical_state())
        self.assertEqual(restored.view("issue-1")["phase"], CONSUMED)

    def test_expired_authorization_is_replaced_once(self):
        self.clock()
        self.adopt()
        self.authorize()
        opened = T0 + ADMISSION_WINDOW_MS
        self.clock(now=opened, key="gate-clock-expire")
        self.assertTrue(self.machine.view("issue-1")["admission_expired"])
        self.assertIsNone(self.machine.view("issue-1")["admission_id"])
        self.assertEqual(
            codes(lambda: self.consume(consume_id="consume-late", key="consume-late")),
            "ADMISSION_EXPIRED",
        )
        self.assertEqual(self.machine.view("issue-1")["phase"], AUTHORIZED)
        self.assertEqual(self.tickets.view("reserve-1")["phase"], "ADMISSION_AUTHORIZED")
        self.assertEqual(self.tickets.view("reserve-1")["right"]["version"], 1)
        replaced = self.authorize(
            admission="admit-2",
            key="admit-2",
            gate="gate-b",
            request=REQ_B,
            expires=opened + ADMISSION_WINDOW_MS,
        )
        self.assertEqual(replaced["credential"]["admission_id"], "admit-2")
        self.assertFalse(replaced["credential"]["admission_expired"])
        consumed = self.consume(consume_id="consume-2", key="consume-2", gate="gate-b", request=REQ_B)
        self.assertEqual(consumed["credential"]["phase"], CONSUMED)
        self.assertEqual(consumed["evidence"]["version_after"], 2)
        self.assertEqual(self.tickets.view("reserve-1")["phase"], "CONSUMED")

    def test_restore_fails_closed_when_ownership_moves(self):
        self.resale.adopt_issued("issue-1", idempotency_key="resale-adopt", **self.adopt_body())
        self.clock()
        self.adopt()
        self.authorize()
        journal = self.machine.export_journal()
        self.tickets.set_clock("clock", idempotency_key="clock-expire-direct", now_ms=T0 + ADMISSION_WINDOW_MS)
        self.sell()
        self.transfer()
        shadow = ReservationMachine.restore(self.tickets.export_journal())
        self.assertEqual(
            codes(lambda: AdmissionMachine.restore(
                journal,
                ticket_source=shadow,
                ownership_source=self.resale,
            )),
            "STALE_VERSION",
        )

    def test_catalogue_has_no_new_admission_command(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        names = set(contract["commands"])
        self.assertNotIn("authorize_admission", names)
        self.assertNotIn("consume_admission", names)
        self.assertIn("admit", names)
        self.assertIn("open_admission", names)
        self.assertEqual(len(names), 40)

    def test_loopback_rejects_fsm_names_and_matches_published_admit(self):
        if str(ROOT) not in sys.path:
            sys.path.append(str(ROOT))
        from integration_gate.catalogue import load_catalogue, reference_types
        from integration_gate.constants import HEALTH_PATH
        from integration_gate.test_http_gate import exchange, parse_json, post_call, run_with_server

        catalogue = load_catalogue(ROOT)
        domain = catalogue.domain
        Core, Rejected = reference_types()
        admit = {
            "domain": domain,
            "ticketId": "missing",
            "holder": "A",
            "expectedVersion": 0,
            "admissionEpoch": 0,
        }

        def run(_httpd, port):
            status, raw, headers = exchange(port, "GET", HEALTH_PATH)
            self.assertEqual(status, 200)
            health = parse_json(raw)
            self.assertIs(health["production"], False)
            self.assertIs(health["publicHost"], False)
            self.assertEqual(headers.get("x-kix-production-endpoint"), "false")
            for action in ("authorize_admission", "consume_admission"):
                status, payload, _headers = post_call(port, "op-" + action, "operator", action, {"domain": domain})
                self.assertEqual(status, 400, action)
                self.assertEqual(payload["error"], "UNKNOWN_ACTION")
                self.assertIs(payload["rejected"], True)
            core = Core()
            try:
                with self.assertRaises(Rejected) as caught:
                    core.execute("op-admit", "venue", "admit", admit)
                local = str(caught.exception)
            finally:
                core.db.close()
            status, payload, _headers = post_call(port, "op-admit", "venue", "admit", admit)
            self.assertEqual(local, "TICKET_NOT_FOUND")
            self.assertEqual(status, 422)
            self.assertEqual(payload["error"], "TICKET_NOT_FOUND")
            self.assertIs(payload["rejected"], True)

        run_with_server(run)
