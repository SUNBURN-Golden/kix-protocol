"""Lifecycle checks for the in-memory reservation and ticketing machine."""

import sys
import unittest
from pathlib import Path

from mock_gates import ADMISSION_WINDOW_MS, NON_CLAIMS, OFFER_WINDOW_MS, PROVENANCE
from reservation_fsm import (
    ADMISSION_AUTHORIZED,
    CANCELLED,
    CONFIRMED,
    CONSUMED,
    HELD,
    ISSUED,
    PAYMENT_NOTED,
    RELEASED,
    REPLAYABLE,
    ReservationError,
    ReservationMachine,
)

_SETTLEMENT_DIR = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT_DIR) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT_DIR))

from settlement_fsm import COMMITTED, SettlementMachine  # noqa: E402

PAY = "ab" * 32
REQ = "11" * 32
REQ_B = "22" * 32
PRICE = 10_001
T0 = 1_000_000


def codes(fn):
    try:
        fn()
    except ReservationError as error:
        return error.code
    raise AssertionError("expected ReservationError")


def policy():
    return {
        "kind": "PRIMARY_FEE_BPS",
        "fee_bps": 0,
        "residual_payee": "organizer",
        "fee_payee": "platform",
    }


def settlement_at(phase, gross=PRICE, settlement_id="claim-1", machine=None):
    book = SettlementMachine() if machine is None else machine
    suffix = settlement_id
    book.initiate(
        settlement_id,
        idempotency_key=f"init-{suffix}",
        trade_id=f"trade-{suffix}",
        gross=gross,
        debtor_role="fixture-merchant",
        policy=policy(),
    )
    if phase == "INITIATED":
        return book
    book.authorize(settlement_id, idempotency_key=f"auth-{suffix}")
    if phase == "AUTHORIZED":
        return book
    book.capture(settlement_id, idempotency_key=f"cap-{suffix}")
    if phase == "CAPTURED":
        return book
    book.commit(
        settlement_id,
        idempotency_key=f"commit-{suffix}",
        movement_id=f"move-{suffix}",
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
    test.assertEqual(body["external_payment"], "UNSUPPORTED")
    test.assertEqual(body["external_admission"], "UNSUPPORTED")
    for name, value in NON_CLAIMS.items():
        test.assertIs(body[name], value)


class ReservationFsmTests(unittest.TestCase):
    def setUp(self):
        self.machine = ReservationMachine()

    def clock(self, now=T0, key="clock-1"):
        return self.machine.set_clock("clock", idempotency_key=key, now_ms=now)

    def show(self, show_id="show-1", key="show-1", **changes):
        body = dict(
            organizer_role="organizer",
            capacity=2,
            gate_roles=["gate-a", "gate-b"],
            primary_price=PRICE,
            resale_cap=20_000,
            resale_allowed=True,
            organizer_bps=1,
            platform_bps=1,
        )
        body.update(changes)
        return self.machine.register_show(show_id, idempotency_key=key, **body)

    def hold(self, reservation="reserve-1", slot=0, buyer="buyer-1", expires=None, key=None, show_id="show-1"):
        if expires is None:
            expires = self.machine.view_show(show_id)["logical_time_ms"] + OFFER_WINDOW_MS
        if key is None:
            key = f"hold-{reservation}"
        return self.machine.hold(
            reservation,
            idempotency_key=key,
            show_id=show_id,
            slot=slot,
            buyer_role=buyer,
            expires_ms=expires,
        )

    def confirm(self, order="order-1", reservation="reserve-1", amount=PRICE, key=None, quote_ref="quote-1"):
        if key is None:
            key = f"confirm-{order}"
        return self.machine.confirm(
            order,
            idempotency_key=key,
            reservation_id=reservation,
            amount=amount,
            quote_ref=quote_ref,
        )

    def pay(self, order="order-1", ref=PAY, amount=PRICE, key=None):
        if key is None:
            key = f"pay-{order}"
        return self.machine.observe_payment(
            order,
            idempotency_key=key,
            payment_ref=ref,
            amount=amount,
        )

    def issue(self, issuance="issue-1", order="order-1", key=None):
        if key is None:
            key = f"issue-{issuance}"
        return self.machine.issue(issuance, idempotency_key=key, order_id=order)

    def open_paid(self, **show_changes):
        self.clock()
        self.show(**show_changes)
        self.hold()
        self.confirm()
        return self.pay()

    def test_unbound_issue_is_memory_evidence_without_economic_finality(self):
        self.clock()
        opened = self.show()
        assert_not_final(self, opened)
        self.assertEqual(opened["show"]["slots"][0]["state"], "FREE")
        self.assertTrue(self.machine.register_show(
            "show-1",
            idempotency_key="show-1",
            organizer_role="organizer",
            capacity=2,
            gate_roles=["gate-a", "gate-b"],
            primary_price=PRICE,
            resale_cap=20_000,
            resale_allowed=True,
            organizer_bps=1,
            platform_bps=1,
        )["duplicate"])
        self.assertEqual(
            codes(lambda: self.show(key="show-2", gate_roles=["gate-b", "gate-a"])),
            "SHOW_BINDING_CONFLICT",
        )
        held = self.hold()
        self.assertEqual(held["reservation"]["phase"], HELD)
        self.assertEqual(held["reservation"]["slot_state"], "RESERVED")
        self.assertIs(held["reservation"]["economic_finality_claimed"], False)
        self.assertEqual(codes(lambda: self.confirm(amount=PRICE - 1, key="confirm-cheap")), "PRIMARY_PRICE_MISMATCH")
        self.assertEqual(self.machine.view("reserve-1")["phase"], HELD)
        ordered = self.confirm()
        self.assertEqual(ordered["reservation"]["phase"], CONFIRMED)
        self.assertEqual(ordered["reservation"]["amount"], PRICE)
        self.assertEqual(ordered["reservation"]["currency"], "KRW")
        self.assertIsNone(ordered["reservation"]["payment_ref"])
        paid = self.pay()
        self.assertEqual(paid["reservation"]["phase"], PAYMENT_NOTED)
        self.assertEqual(paid["show"]["payment_ref_count"], 1)
        self.assertIs(paid["funds_executed"], False)
        issued = self.issue()
        assert_not_final(self, issued)
        evidence = issued["evidence"]
        self.assertEqual(evidence["kind"], 1)
        self.assertEqual(evidence["version"], 1)
        self.assertIs(evidence["chain_issued"], False)
        self.assertIs(evidence["buyer_evidence_available"], False)
        self.assertNotIn("seller_due", evidence)
        reservation = issued["reservation"]
        self.assertEqual(reservation["phase"], ISSUED)
        self.assertEqual(reservation["settlement_gate"], "UNBOUND")
        self.assertIs(reservation["mock_settlement_commit_observed"], False)
        self.assertIs(reservation["economic_finality_claimed"], False)
        self.assertIs(reservation["chain_issued"], False)
        self.assertEqual(reservation["slot_state"], "ISSUED")
        self.assertEqual(reservation["right"]["state"], "ACTIVE")
        self.assertEqual(reservation["right"]["version"], 1)
        self.assertEqual(reservation["right"]["holder_role"], "buyer-1")
        self.assertIsNone(reservation["right"]["listing_id"])
        replay = self.issue()
        self.assertTrue(replay["duplicate"])
        self.assertIsNone(replay["applied"])
        self.assertEqual(replay["evidence"]["version"], 1)
        self.assertIs(replay["economic_finality_claimed"], False)
        self.assertEqual(
            codes(lambda: self.issue(issuance="issue-2", key="issue-other")),
            "ORDER_ALREADY_ISSUED",
        )
        self.assertEqual(self.machine.view("reserve-1")["right"]["version"], 1)

    def test_overlapping_holds_and_replay_do_not_double_book(self):
        self.clock()
        self.show(capacity=1, gate_roles=["gate-a"])
        first = self.hold()
        self.assertEqual(first["reservation"]["slot_state"], "RESERVED")
        journal = self.machine.export_journal()
        self.assertEqual(
            codes(lambda: self.hold(reservation="reserve-2", buyer="buyer-2", key="hold-b")),
            "SLOT_OCCUPIED",
        )
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(self.machine.view("reserve-1")["phase"], HELD)
        self.assertEqual(codes(lambda: self.machine.view("reserve-2")), "UNKNOWN_RESERVATION")
        again = self.hold()
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["reservation"]["phase"], HELD)
        self.assertEqual(
            codes(lambda: self.hold(buyer="buyer-9", key="hold-reserve-1")),
            "IDEMPOTENCY_CONFLICT",
        )
        self.assertEqual(self.machine.view("reserve-1")["buyer_role"], "buyer-1")
        self.machine.release("reserve-1", idempotency_key="release-1")
        self.assertEqual(
            codes(lambda: self.hold(reservation="reserve-2", buyer="buyer-2", key="hold-b")),
            "SLOT_OCCUPIED",
        )
        second = self.hold(reservation="reserve-2", buyer="buyer-2", key="hold-b2")
        self.assertEqual(second["reservation"]["phase"], HELD)
        self.assertEqual(second["reservation"]["slot_reservation_id"], "reserve-2")
        show = self.machine.view_show("show-1")["show"]
        self.assertEqual(show["slots"][0]["state"], "RESERVED")
        self.assertEqual(show["slots"][0]["reservation_id"], "reserve-2")
        self.assertEqual(
            codes(lambda: self.hold(key="hold-again")),
            "TERMINAL_IMMUTABLE",
        )
        restored = ReservationMachine.restore(self.machine.export_journal())
        self.assertEqual(restored.canonical_state(), self.machine.canonical_state())
        self.assertEqual(restored.view("reserve-2")["phase"], HELD)
        self.assertEqual(restored.view("reserve-1")["phase"], RELEASED)
        self.assertEqual(restored.view_show("show-1")["show"]["slots"][0]["reservation_id"], "reserve-2")

    def test_expiry_does_not_release_until_an_explicit_release(self):
        self.clock()
        self.show()
        short = T0 + 1_000
        self.hold(reservation="reserve-c", slot=1, buyer="buyer-c", expires=short, key="hold-c")
        self.hold()
        self.machine.set_clock("clock", idempotency_key="clock-short", now_ms=short)
        current = self.machine.view("reserve-c")
        self.assertTrue(current["expired"])
        self.assertEqual(current["phase"], HELD)
        self.assertEqual(current["slot_state"], "RESERVED")
        self.assertFalse(self.machine.view("reserve-1")["expired"])
        self.assertEqual(
            codes(lambda: self.confirm(order="order-c", reservation="reserve-c", key="confirm-c")),
            "RESERVATION_EXPIRED",
        )
        self.assertEqual(self.machine.view("reserve-c")["phase"], HELD)
        self.assertEqual(
            codes(lambda: self.hold(reservation="reserve-d", slot=1, buyer="buyer-d", key="hold-d")),
            "SLOT_OCCUPIED",
        )
        released = self.machine.release("reserve-c", idempotency_key="release-c")
        self.assertEqual(released["reservation"]["phase"], RELEASED)
        self.assertEqual(released["reservation"]["slot_state"], "FREE")
        moved = self.hold(
            reservation="reserve-d",
            slot=1,
            buyer="buyer-d",
            key="hold-d2",
            expires=short + OFFER_WINDOW_MS,
        )
        self.assertEqual(moved["reservation"]["phase"], HELD)
        self.assertEqual(moved["show"]["slots"][1]["reservation_id"], "reserve-d")
        later = T0 + OFFER_WINDOW_MS
        self.machine.set_clock("clock", idempotency_key="clock-a", now_ms=later)
        self.assertTrue(self.machine.view("reserve-1")["expired"])
        self.assertEqual(self.machine.view("reserve-1")["slot_state"], "RESERVED")
        self.assertEqual(
            codes(lambda: self.hold(reservation="reserve-b", buyer="buyer-b", key="hold-b", expires=later + OFFER_WINDOW_MS)),
            "SLOT_OCCUPIED",
        )
        self.machine.release("reserve-1", idempotency_key="release-a")
        taken = self.hold(
            reservation="reserve-b",
            buyer="buyer-b",
            key="hold-b2",
            expires=later + OFFER_WINDOW_MS,
        )
        self.assertEqual(taken["reservation"]["slot_reservation_id"], "reserve-b")
        self.assertEqual(self.machine.view("reserve-1")["phase"], RELEASED)
        restored = ReservationMachine.restore(self.machine.export_journal())
        self.assertEqual(restored.view("reserve-1")["phase"], RELEASED)
        self.assertEqual(restored.view("reserve-b")["phase"], HELD)
        self.assertEqual(restored.view_show("show-1")["logical_time_ms"], later)

    def test_cancel_before_payment_frees_and_payment_blocks_compensation(self):
        self.clock()
        self.show()
        self.hold()
        self.confirm()
        cancelled = self.machine.cancel("reserve-1", idempotency_key="cancel-1")
        self.assertEqual(cancelled["reservation"]["phase"], CANCELLED)
        self.assertEqual(cancelled["reservation"]["slot_state"], "FREE")
        self.assertIs(cancelled["compensation_defined"], False)
        self.assertEqual(
            codes(lambda: self.machine.cancel("reserve-1", idempotency_key="cancel-2")),
            "TERMINAL_IMMUTABLE",
        )
        replay = self.machine.cancel("reserve-1", idempotency_key="cancel-1")
        self.assertTrue(replay["duplicate"])
        self.hold(reservation="reserve-2", buyer="buyer-2", key="hold-2")
        self.confirm(order="order-2", reservation="reserve-2", key="confirm-2")
        self.pay(order="order-2", key="pay-2")
        journal = self.machine.export_journal()
        digest = self.machine.state_digest()
        self.assertEqual(
            codes(lambda: self.machine.cancel("reserve-2", idempotency_key="cancel-paid")),
            "COMPENSATION_UNDEFINED",
        )
        self.assertEqual(
            codes(lambda: self.machine.release("reserve-2", idempotency_key="release-paid")),
            "ILLEGAL_TRANSITION",
        )
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(self.machine.state_digest(), digest)
        self.assertEqual(self.machine.view("reserve-2")["phase"], PAYMENT_NOTED)
        self.assertEqual(self.machine.view("reserve-2")["slot_state"], "RESERVED")
        self.machine.set_clock("clock", idempotency_key="clock-expire", now_ms=T0 + OFFER_WINDOW_MS)
        self.assertEqual(
            codes(lambda: self.issue(issuance="issue-2", order="order-2", key="issue-late")),
            "RESERVATION_EXPIRED",
        )
        late = self.machine.view("reserve-2")
        self.assertEqual(late["phase"], PAYMENT_NOTED)
        self.assertIsNone(late["right"])
        self.assertIsNone(late["slot_right_id"])
        self.assertEqual(late["slot_state"], "RESERVED")
        self.assertIs(late["economic_finality_claimed"], False)
        self.assertEqual(
            codes(lambda: self.machine.cancel("reserve-2", idempotency_key="cancel-late")),
            "COMPENSATION_UNDEFINED",
        )

    def test_cancel_after_issue_and_duplicate_consume(self):
        self.open_paid()
        self.issue()
        digest = self.machine.state_digest()
        journal = self.machine.export_journal()
        self.assertEqual(
            codes(lambda: self.machine.cancel("reserve-1", idempotency_key="cancel-issued")),
            "CANCEL_AFTER_ISSUE",
        )
        self.assertEqual(
            codes(lambda: self.machine.release("reserve-1", idempotency_key="release-issued")),
            "ILLEGAL_TRANSITION",
        )
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(self.machine.state_digest(), digest)
        self.assertEqual(self.machine.view("reserve-1")["slot_state"], "ISSUED")
        self.assertEqual(
            codes(lambda: self.machine.consume(
                "consume-0",
                idempotency_key="consume-0",
                right_id="issue-1",
                version=1,
                gate_role="gate-a",
                request=REQ,
            )),
            "ADMISSION_REQUIRED",
        )
        self.assertEqual(self.machine.view("reserve-1")["phase"], ISSUED)
        authorized = self.machine.authorize_admission(
            "admit-1",
            idempotency_key="admit-1",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ,
            expires_ms=T0 + ADMISSION_WINDOW_MS,
        )
        assert_not_final(self, authorized)
        self.assertEqual(authorized["reservation"]["phase"], ADMISSION_AUTHORIZED)
        self.assertEqual(authorized["reservation"]["admission_id"], "admit-1")
        self.assertFalse(authorized["reservation"]["admission_expired"])
        self.assertEqual(
            codes(lambda: self.machine.authorize_admission(
                "admit-2",
                idempotency_key="admit-2",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-b",
                request=REQ_B,
                expires_ms=T0 + ADMISSION_WINDOW_MS,
            )),
            "ADMISSION_LOCKED",
        )
        self.assertEqual(
            codes(lambda: self.machine.consume(
                "consume-wrong",
                idempotency_key="consume-wrong",
                right_id="issue-1",
                version=1,
                gate_role="gate-b",
                request=REQ,
            )),
            "GATE_MISMATCH",
        )
        consumed = self.machine.consume(
            "consume-1",
            idempotency_key="consume-1",
            right_id="issue-1",
            version=1,
            gate_role="gate-a",
            request=REQ,
        )
        self.assertEqual(consumed["evidence"]["decision"], "CONSUMED_ONCE")
        self.assertIs(consumed["evidence"]["admission_routing_production"], False)
        self.assertIs(consumed["evidence"]["private_proof_verified"], False)
        self.assertEqual(consumed["reservation"]["phase"], CONSUMED)
        self.assertTrue(consumed["reservation"]["terminal"])
        self.assertEqual(consumed["reservation"]["right"]["version"], 2)
        self.assertEqual(consumed["reservation"]["slot_state"], "ISSUED")
        self.assertIs(consumed["economic_finality_claimed"], False)
        self.assertEqual(
            codes(lambda: self.machine.consume(
                "consume-2",
                idempotency_key="consume-2",
                right_id="issue-1",
                version=2,
                gate_role="gate-a",
                request=REQ,
            )),
            "ALREADY_CONSUMED",
        )
        self.assertEqual(self.machine.view("reserve-1")["right"]["version"], 2)
        replay = self.machine.consume(
            "consume-1",
            idempotency_key="consume-1",
            right_id="issue-1",
            version=1,
            gate_role="gate-a",
            request=REQ,
        )
        self.assertTrue(replay["duplicate"])
        self.assertEqual(replay["evidence"]["version_after"], 2)
        self.assertIs(replay["economic_finality_claimed"], False)
        frozen = self.issue()
        self.assertTrue(frozen["duplicate"])
        self.assertEqual(frozen["evidence"]["version"], 1)
        self.assertEqual(frozen["reservation"]["phase"], ISSUED)
        self.assertEqual(self.machine.view("reserve-1")["phase"], CONSUMED)
        self.assertEqual(
            codes(lambda: self.machine.cancel("reserve-1", idempotency_key="cancel-consumed")),
            "CANCEL_AFTER_ISSUE",
        )
        self.assertEqual(
            codes(lambda: self.machine.authorize_admission(
                "admit-late",
                idempotency_key="admit-late",
                right_id="issue-1",
                version=2,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=T0 + ADMISSION_WINDOW_MS,
            )),
            "RIGHT_NOT_ACTIVE",
        )
        self.assertIsNone(self.machine.view("reserve-1")["right"]["listing_id"])

    def test_expired_admission_can_be_replaced_and_consumed_once(self):
        self.open_paid()
        self.issue()
        self.machine.authorize_admission(
            "admit-1",
            idempotency_key="admit-1",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ,
            expires_ms=T0 + ADMISSION_WINDOW_MS,
        )
        opened = T0 + ADMISSION_WINDOW_MS
        self.machine.set_clock("clock", idempotency_key="clock-admit", now_ms=opened)
        self.assertTrue(self.machine.view("reserve-1")["admission_expired"])
        self.assertIsNone(self.machine.view("reserve-1")["admission_id"])
        self.assertEqual(
            codes(lambda: self.machine.consume(
                "consume-late",
                idempotency_key="consume-late",
                right_id="issue-1",
                version=1,
                gate_role="gate-a",
                request=REQ,
            )),
            "ADMISSION_EXPIRED",
        )
        self.assertEqual(self.machine.view("reserve-1")["phase"], ADMISSION_AUTHORIZED)
        self.assertEqual(self.machine.view("reserve-1")["right"]["state"], "ACTIVE")
        self.assertEqual(self.machine.view("reserve-1")["right"]["version"], 1)
        replaced = self.machine.authorize_admission(
            "admit-2",
            idempotency_key="admit-2",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-b",
            request=REQ_B,
            expires_ms=opened + ADMISSION_WINDOW_MS,
        )
        self.assertEqual(replaced["reservation"]["admission_id"], "admit-2")
        self.assertFalse(replaced["reservation"]["admission_expired"])
        consumed = self.machine.consume(
            "consume-2",
            idempotency_key="consume-2",
            right_id="issue-1",
            version=1,
            gate_role="gate-b",
            request=REQ_B,
        )
        self.assertEqual(consumed["reservation"]["phase"], CONSUMED)
        self.assertEqual(consumed["reservation"]["right"]["version"], 2)
        restored = ReservationMachine.restore(self.machine.export_journal())
        self.assertEqual(restored.canonical_state(), self.machine.canonical_state())
        self.assertEqual(restored.view("reserve-1")["phase"], CONSUMED)
        self.assertEqual(restored.view("reserve-1")["right"]["version"], 2)

    def test_restore_replays_a_lost_success_and_omits_rejections(self):
        self.open_paid()
        issued = self.issue()
        journal = self.machine.export_journal()
        before = self.machine.canonical_state()
        self.assertEqual(
            codes(lambda: self.pay(amount=PRICE - 1, key="pay-bad")),
            "ILLEGAL_TRANSITION",
        )
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(self.machine.canonical_state(), before)
        detached = self.machine.export_journal()
        detached.clear()
        self.assertEqual(len(self.machine.export_journal()), len(journal))
        restored = ReservationMachine.restore(journal)
        self.assertEqual(restored.canonical_state(), before)
        self.assertEqual(restored.state_digest(), self.machine.state_digest())
        lost = restored.issue("issue-1", idempotency_key="issue-issue-1", order_id="order-1")
        self.assertTrue(lost["duplicate"])
        self.assertEqual(lost["evidence"], issued["evidence"])
        self.assertIs(lost["economic_finality_claimed"], False)
        self.assertEqual(restored.view("reserve-1")["accepted_entries"], self.machine.view("reserve-1")["accepted_entries"])
        tampered = self.machine.export_journal()
        tampered.append({"op": "tamper"})
        self.assertEqual(codes(lambda: ReservationMachine.restore(tampered)), "INVALID_JOURNAL")
        self.assertEqual(codes(lambda: ReservationMachine.restore({"op": "hold"})), "INVALID_JOURNAL")
        self.assertEqual(
            codes(lambda: self.machine.set_clock("not-clock", idempotency_key="clock-bad", now_ms=T0 + 1)),
            "INVALID_ID",
        )
        self.assertEqual(self.machine.view_show("show-1")["logical_time_ms"], T0)

    def test_settlement_gate_refuses_uncommitted_finality(self):
        book = settlement_at("AUTHORIZED")
        self.machine = ReservationMachine(book)
        self.open_paid()
        self.machine.bind_settlement(
            "reserve-1",
            idempotency_key="bind-1",
            settlement_id="claim-1",
        )
        self.assertEqual(self.machine.view("reserve-1")["settlement_gate"], "BOUND")
        self.assertIs(self.machine.view("reserve-1")["mock_settlement_commit_observed"], False)
        settlement_before = book.canonical_state()
        journal = self.machine.export_journal()
        self.assertEqual(
            codes(lambda: self.issue(key="issue-early")),
            "SETTLEMENT_NOT_COMMITTED",
        )
        self.assertEqual(
            codes(lambda: self.issue(key="issue-early")),
            "SETTLEMENT_NOT_COMMITTED",
        )
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(book.canonical_state(), settlement_before)
        self.assertIs(book.view("claim-1")["admission_granted"], False)
        self.assertEqual(book.view("claim-1")["phase"], "AUTHORIZED")
        current = self.machine.view("reserve-1")
        self.assertEqual(current["phase"], PAYMENT_NOTED)
        self.assertIsNone(current["right"])
        self.assertIs(current["economic_finality_claimed"], False)
        self.assertEqual(current["slot_state"], "RESERVED")
        book.capture("claim-1", idempotency_key="cap-claim-1")
        self.assertEqual(codes(lambda: self.issue(key="issue-captured")), "SETTLEMENT_NOT_COMMITTED")
        book.commit(
            "claim-1",
            idempotency_key="commit-claim-1",
            movement_id="move-claim-1",
            gross=PRICE,
            amount=PRICE,
            fee=0,
            tax=0,
            held=0,
            adjustment=0,
        )
        self.assertEqual(book.view("claim-1")["phase"], COMMITTED)
        self.assertEqual(codes(lambda: self.issue(key="issue-early")), "SETTLEMENT_NOT_COMMITTED")
        after_commit = book.canonical_state()
        issued = self.issue(key="issue-committed")
        self.assertEqual(book.canonical_state(), after_commit)
        self.assertIs(book.view("claim-1")["admission_granted"], False)
        self.assertIs(book.view("claim-1")["funds_executed"], False)
        assert_not_final(self, issued)
        self.assertEqual(issued["reservation"]["phase"], ISSUED)
        self.assertEqual(issued["reservation"]["settlement_gate"], "MOCK_COMMIT_OBSERVED")
        self.assertIs(issued["reservation"]["mock_settlement_commit_observed"], True)
        self.assertIs(issued["reservation"]["economic_finality_claimed"], False)
        self.assertEqual(issued["evidence"]["kind"], 1)
        self.assertIs(issued["evidence"]["chain_issued"], False)
        self.assertNotIn("seller_due", issued["evidence"])
        self.assertIs(issued["reservation"]["right"]["listing_id"], None)

    def test_bound_issue_checks_gross_and_replays_only_with_the_commit_view(self):
        book = settlement_at(COMMITTED, gross=PRICE, settlement_id="claim-ok")
        settlement_at(COMMITTED, gross=PRICE - 1, settlement_id="claim-off", machine=book)
        self.machine = ReservationMachine(book)
        self.open_paid()
        self.machine.bind_settlement("reserve-1", idempotency_key="bind-off", settlement_id="claim-off")
        self.assertEqual(codes(lambda: self.issue(key="issue-off")), "SETTLEMENT_AMOUNT_MISMATCH")
        self.assertIsNone(self.machine.view("reserve-1")["right"])
        self.assertEqual(self.machine.view("reserve-1")["phase"], PAYMENT_NOTED)
        self.clock()
        self.show(show_id="show-2", key="show-2")
        self.hold(reservation="reserve-2", show_id="show-2", key="hold-2")
        self.confirm(order="order-2", reservation="reserve-2", key="confirm-2")
        self.pay(order="order-2", ref="cd" * 32, key="pay-2")
        self.machine.bind_settlement("reserve-2", idempotency_key="bind-ok", settlement_id="claim-ok")
        issued = self.issue(issuance="issue-2", order="order-2", key="issue-ok")
        self.assertEqual(issued["reservation"]["settlement_gate"], "MOCK_COMMIT_OBSERVED")
        self.assertIs(issued["economic_finality_claimed"], False)
        reservation_journal = self.machine.export_journal()
        settlement_journal = book.export_journal()
        revived_book = SettlementMachine.restore(settlement_journal)
        revived = ReservationMachine.restore(reservation_journal, settlement_source=revived_book)
        self.assertEqual(revived.canonical_state(), self.machine.canonical_state())
        self.assertEqual(revived.view("reserve-2")["settlement_gate"], "MOCK_COMMIT_OBSERVED")
        self.assertIs(revived.view("reserve-2")["economic_finality_claimed"], False)
        self.assertEqual(
            codes(lambda: ReservationMachine.restore(reservation_journal, settlement_source=SettlementMachine())),
            "UNKNOWN_SETTLEMENT",
        )
        bare = ReservationMachine()
        bare.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        bare.register_show(
            "show-9",
            idempotency_key="show-9",
            organizer_role="organizer",
            capacity=1,
            gate_roles=["gate-a"],
            primary_price=PRICE,
            resale_cap=20_000,
            resale_allowed=False,
            organizer_bps=0,
            platform_bps=0,
        )
        bare.hold(
            "reserve-9",
            idempotency_key="hold-9",
            show_id="show-9",
            slot=0,
            buyer_role="buyer-9",
            expires_ms=T0 + OFFER_WINDOW_MS,
        )
        bare.confirm("order-9", idempotency_key="confirm-9", reservation_id="reserve-9", amount=PRICE, quote_ref=None)
        bare.observe_payment("order-9", idempotency_key="pay-9", payment_ref="ef" * 32, amount=PRICE)
        bare.bind_settlement("reserve-9", idempotency_key="bind-9", settlement_id="claim-missing")
        self.assertEqual(
            codes(lambda: bare.issue("issue-9", idempotency_key="issue-9", order_id="order-9")),
            "SETTLEMENT_SOURCE_REQUIRED",
        )
        self.assertEqual(bare.view("reserve-9")["phase"], PAYMENT_NOTED)

        class Claiming:
            def view(self, settlement_id):
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

        claiming = ReservationMachine(Claiming())
        claiming.set_clock("clock", idempotency_key="clock-c", now_ms=T0)
        claiming.register_show(
            "show-c",
            idempotency_key="show-c",
            organizer_role="organizer",
            capacity=1,
            gate_roles=["gate-a"],
            primary_price=PRICE,
            resale_cap=20_000,
            resale_allowed=False,
            organizer_bps=0,
            platform_bps=0,
        )
        claiming.hold(
            "reserve-c",
            idempotency_key="hold-c",
            show_id="show-c",
            slot=0,
            buyer_role="buyer-c",
            expires_ms=T0 + OFFER_WINDOW_MS,
        )
        claiming.confirm(
            "order-c",
            idempotency_key="confirm-c",
            reservation_id="reserve-c",
            amount=PRICE,
            quote_ref=None,
        )
        claiming.observe_payment(
            "order-c",
            idempotency_key="pay-c",
            payment_ref="12" * 32,
            amount=PRICE,
        )
        claiming.bind_settlement("reserve-c", idempotency_key="bind-c", settlement_id="claim-c")
        self.assertEqual(
            codes(lambda: claiming.issue("issue-c", idempotency_key="issue-c", order_id="order-c")),
            "SETTLEMENT_VIEW_REJECTED",
        )
        self.assertIsNone(claiming.view("reserve-c")["right"])
        self.assertIs(claiming.view("reserve-c")["economic_finality_claimed"], False)

    def test_external_attempts_do_not_journal_and_resale_is_absent(self):
        self.open_paid()
        before = self.machine.canonical_state()
        journal = self.machine.export_journal()
        for kind in ("PG_CHARGE", "BANK_DEBIT", "VENUE_SCAN", "LIVE_HTTP", "PAYOUT"):
            self.assertEqual(codes(lambda kind=kind: self.machine.reject_external(kind)), "EXTERNAL_UNSUPPORTED")
        self.assertEqual(codes(lambda: self.machine.reject_external(" ")), "INVALID_ID")
        self.assertEqual(self.machine.canonical_state(), before)
        self.assertEqual(self.machine.export_journal(), journal)
        absent = {
            "list_resale",
            "cancel_listing",
            "observe_resale_payment",
            "accept_resale",
            "note_advance",
            "bind_refund",
            "distribute",
        }
        self.assertTrue(REPLAYABLE.isdisjoint(absent))
        for name in absent:
            self.assertFalse(hasattr(ReservationMachine, name))
        report = self.machine.reconcile("reserve-1", idempotency_key="recon-1")
        self.assertTrue(report["matched"])
        self.assertEqual(report["entry_count"], len(journal))
        self.assertEqual(len(report["state_digest"]), 64)
        self.assertIs(report["economic_finality_claimed"], False)
        self.assertEqual(self.machine.export_journal(), journal)
        replay = self.machine.reconcile("reserve-1", idempotency_key="recon-1")
        self.assertTrue(replay["duplicate"])
        self.assertEqual(replay["state_digest"], report["state_digest"])
        self.assertEqual(
            codes(lambda: self.machine.reconcile("reserve-2", idempotency_key="recon-1")),
            "IDEMPOTENCY_CONFLICT",
        )
        restored = ReservationMachine.restore(journal)
        self.assertEqual(restored.canonical_state(), self.machine.canonical_state())
        again = restored.reconcile("reserve-1", idempotency_key="recon-1")
        self.assertFalse(again["duplicate"])
        self.assertTrue(again["matched"])
        self.assertEqual(again["state_digest"], report["state_digest"])
        self.assertEqual(restored.export_journal(), journal)

    def test_same_key_conflict_does_not_move_phase(self):
        self.clock()
        self.show()
        self.hold()
        self.assertEqual(self.machine.view("reserve-1")["phase"], HELD)
        self.assertEqual(
            codes(lambda: self.machine.confirm(
                "order-1",
                idempotency_key="confirm-order-1",
                reservation_id="reserve-1",
                amount=True,
            )),
            "INVALID_AMOUNT",
        )
        self.assertEqual(
            codes(lambda: self.machine.confirm(
                "order-1",
                idempotency_key="confirm-order-1",
                reservation_id="reserve-1",
                amount=PRICE,
            )),
            "IDEMPOTENCY_CONFLICT",
        )
        self.assertEqual(self.machine.view("reserve-1")["phase"], HELD)
        self.confirm(key="confirm-ok")
        self.assertEqual(
            codes(lambda: self.confirm(order="order-2", key="confirm-2")),
            "RESERVATION_ALREADY_ORDERED",
        )
        self.assertEqual(self.machine.view("reserve-1")["order_id"], "order-1")
        self.assertEqual(self.machine.view("reserve-1")["phase"], CONFIRMED)
