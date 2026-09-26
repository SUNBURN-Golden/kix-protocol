"""Lifecycle checks for the in-memory resale machine.

Buyer and seller races are ordered commands in one process. They are not
threads, not a live marketplace, and not cross-channel exclusion.
"""

import sys
import unittest
from pathlib import Path

from mock_gates import ADMISSION_WINDOW_MS, NON_CLAIMS, OFFER_WINDOW_MS, PROVENANCE
from reservation_fsm import REPLAYABLE as RESERVATION_OPS
from reservation_fsm import ReservationMachine
from resale_fsm import (
    BUY_HELD,
    CANCELLED,
    CLOSED,
    LISTED,
    PAYMENT_NOTED,
    REPLAYABLE,
    TRANSFERRED,
    ResaleError,
    ResaleMachine,
)

_SETTLEMENT_DIR = Path(__file__).resolve().parents[1] / "settlement_f01_f03"
if str(_SETTLEMENT_DIR) not in sys.path:
    sys.path.insert(1, str(_SETTLEMENT_DIR))

from settlement_fsm import FAILED, SettlementMachine  # noqa: E402

PAY = "ab" * 32
SALE_PAY = "cd" * 32
REQ = "11" * 32
PRICE = 10_001
SALE = 8_000
T0 = 1_000_000
EXPIRES = T0 + OFFER_WINDOW_MS


def codes(fn):
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


def settlement_at(phase, gross=SALE, settlement_id="claim-1", machine=None):
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
    if phase in ("INITIATED", FAILED):
        if phase == FAILED:
            book.fail(settlement_id, idempotency_key=f"fail-{suffix}", reason="fixture-fail")
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
    test.assertIs(body["venue_credential_reissued"], False)
    test.assertEqual(body["external_marketplace"], "UNSUPPORTED")
    test.assertEqual(body["external_payment"], "UNSUPPORTED")
    for name, value in NON_CLAIMS.items():
        test.assertIs(body[name], value)


class ResaleFsmTests(unittest.TestCase):
    def setUp(self):
        self.machine = ResaleMachine()

    def clock(self, now=T0, key="clock-1"):
        return self.machine.set_clock("clock", idempotency_key=key, now_ms=now)

    def adopt(self, right="issue-1", key="adopt-1", reservation_id=None, **changes):
        body = dict(
            show_id="show-1",
            slot=0,
            buyer_role="buyer-1",
            expires_ms=EXPIRES,
            order_id="order-1",
            amount=PRICE,
            payment_ref=PAY,
            reservation_id=reservation_id,
            quote_ref="quote-1" if reservation_id is not None else None,
        )
        body.update(show_kwargs())
        body.update(changes)
        return self.machine.adopt_issued(right, idempotency_key=key, **body)

    def sell(
        self,
        listing="list-1",
        right="issue-1",
        seller="buyer-1",
        recipient="buyer-2",
        amount=PRICE,
        version=1,
        expires=EXPIRES,
        key=None,
        reservation_id=None,
    ):
        if key is None:
            key = f"list-{listing}"
        return self.machine.list_resale(
            listing,
            idempotency_key=key,
            right_id=right,
            version=version,
            seller_role=seller,
            recipient_role=recipient,
            amount=amount,
            expires_ms=expires,
            reservation_id=reservation_id,
        )

    def hold(self, hold="hold-1", listing="list-1", buyer="buyer-2", key=None):
        if key is None:
            key = f"hold-{hold}"
        return self.machine.hold_buy(hold, idempotency_key=key, listing_id=listing, buyer_role=buyer)

    def pay(self, listing="list-1", ref=SALE_PAY, amount=PRICE, buyer=None, key=None):
        if key is None:
            key = f"pay-{listing}"
        return self.machine.observe_resale_payment(
            listing,
            idempotency_key=key,
            payment_ref=ref,
            amount=amount,
            buyer_role=buyer,
        )

    def transfer(self, transfer="transfer-1", listing="list-1", key=None):
        if key is None:
            key = f"transfer-{transfer}"
        return self.machine.accept_resale(transfer, idempotency_key=key, listing_id=listing)

    def opened(self, amount=PRICE):
        self.clock()
        self.adopt()
        return self.sell(amount=amount)

    def reservation(self, stop="issued"):
        machine = ReservationMachine()
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
        machine.issue("issue-1", idempotency_key="issue-1", order_id="order-1")
        if stop == "consumed":
            machine.authorize_admission(
                "admit-1",
                idempotency_key="admit-1",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=T0 + ADMISSION_WINDOW_MS,
            )
            machine.consume(
                "consume-1",
                idempotency_key="consume-1",
                right_id="issue-1",
                version=1,
                gate_role="gate-a",
                request=REQ,
            )
        return machine

    def test_transfer_is_idempotent_and_does_not_reissue_a_credential(self):
        listed = self.opened()
        assert_not_final(self, listed)
        self.assertEqual(listed["listing"]["phase"], LISTED)
        self.assertTrue(listed["listing"]["attached"])
        self.assertTrue(listed["listing"]["prior_presentation_valid"])
        self.assertIs(listed["listing"]["ownership_transferred"], False)
        self.assertEqual(listed["listing"]["settlement_gate"], "UNBOUND")
        self.assertEqual(listed["right"]["version"], 1)
        self.assertEqual(listed["right"]["generation"], 1)
        self.assertIs(self.machine.view_right("issue-1")["ticket"]["eligible"], False)
        held_back = self.machine.view_presentation("issue-1", version=1, holder_role="buyer-1")
        self.assertIs(held_back["presentation"]["matches_current_right"], False)
        self.assertIs(held_back["presentation"]["venue_credential_reissued"], False)
        self.assertEqual(codes(lambda: self.transfer(key="transfer-early")), "ILLEGAL_TRANSITION")
        self.assertEqual(self.machine.view("list-1")["phase"], LISTED)
        paid = self.pay()
        self.assertEqual(paid["listing"]["phase"], PAYMENT_NOTED)
        self.assertIs(paid["funds_executed"], False)
        self.assertEqual(paid["listing"]["payment_ref"], SALE_PAY)
        transferred = self.transfer()
        assert_not_final(self, transferred)
        evidence = transferred["evidence"]
        self.assertEqual(evidence["from_role"], "buyer-1")
        self.assertEqual(evidence["to_role"], "buyer-2")
        self.assertEqual(evidence["right_id"], "issue-1")
        self.assertEqual(evidence["version_after"], 2)
        self.assertEqual(evidence["organizer_due"], 1)
        self.assertEqual(evidence["platform_due"], 1)
        self.assertEqual(evidence["seller_due"], 9_999)
        self.assertEqual(evidence["organizer_due"] + evidence["platform_due"] + evidence["seller_due"], PRICE)
        self.assertIs(evidence["funds_executed"], False)
        self.assertIs(evidence["chain_owner_current"], False)
        listing = transferred["listing"]
        self.assertEqual(listing["phase"], TRANSFERRED)
        self.assertIs(listing["terminal"], False)
        self.assertIs(listing["ownership_transferred"], True)
        self.assertIs(listing["prior_presentation_valid"], False)
        self.assertIs(listing["venue_credential_reissued"], False)
        self.assertIs(listing["economic_finality_claimed"], False)
        self.assertEqual(listing["holder_role"], "buyer-2")
        self.assertEqual(listing["current_version"], 2)
        self.assertEqual(listing["generation"], 1)
        self.assertEqual(listing["slot_state"], "ISSUED")
        self.assertEqual(listing["slot_right_id"], "issue-1")
        self.assertIs(listing["mock_settlement_commit_observed"], False)
        self.assertIsNone(transferred["right"]["listing_id"])
        replay = self.transfer()
        self.assertTrue(replay["duplicate"])
        self.assertIsNone(replay["applied"])
        self.assertEqual(replay["evidence"]["version_after"], 2)
        self.assertIs(replay["economic_finality_claimed"], False)
        self.assertIs(replay["venue_credential_reissued"], False)
        self.assertEqual(self.machine.view("list-1")["current_version"], 2)
        self.assertEqual(codes(lambda: self.transfer(transfer="transfer-2", key="transfer-again")), "ILLEGAL_TRANSITION")
        self.assertEqual(self.machine.view("list-1")["current_version"], 2)
        self.assertEqual(codes(lambda: self.sell(key="reopen")), "ILLEGAL_TRANSITION")
        self.assertEqual(
            codes(lambda: self.sell(listing="list-1", seller="buyer-2", recipient="buyer-3", version=2, key="rebind")),
            "LISTING_BINDING_CONFLICT",
        )
        old = self.machine.view_presentation("issue-1", version=1, holder_role="buyer-1")
        self.assertIs(old["presentation"]["matches_current_right"], False)
        current = self.machine.view_presentation("issue-1", version=2, holder_role="buyer-2")
        self.assertIs(current["presentation"]["matches_current_right"], True)
        self.assertIs(current["admission_routing_production"], False)
        again = self.sell(listing="list-2", seller="buyer-2", recipient="buyer-3", version=2, key="list-2")
        self.assertEqual(again["listing"]["phase"], LISTED)
        self.assertEqual(self.machine.view("list-1")["phase"], TRANSFERRED)
        closed = self.machine.close("list-1", idempotency_key="close-1")
        self.assertEqual(closed["listing"]["phase"], CLOSED)
        self.assertTrue(closed["listing"]["terminal"])
        self.assertIs(closed["listing"]["prior_presentation_valid"], False)
        self.assertEqual(codes(lambda: self.machine.close("list-1", idempotency_key="close-2")), "TERMINAL_IMMUTABLE")
        self.assertEqual(codes(lambda: self.sell(key="reopen-closed")), "TERMINAL_IMMUTABLE")
        self.assertIs(self.machine.view_right("issue-1")["ticket"]["eligible"], False)

    def test_buy_hold_is_optional_and_cancel_order_decides_the_race(self):
        self.opened()
        self.assertEqual(codes(lambda: self.hold(buyer="buyer-3", key="hold-other")), "RECIPIENT_MISMATCH")
        self.assertEqual(self.machine.view("list-1")["phase"], LISTED)
        held = self.hold()
        self.assertEqual(held["listing"]["phase"], BUY_HELD)
        self.assertEqual(held["listing"]["buyer_role"], "buyer-2")
        self.assertIs(held["cross_channel_exclusive"], False)
        self.assertEqual(codes(lambda: self.hold(hold="hold-2", buyer="buyer-3", key="hold-2")), "BUYER_HOLD_LOCKED")
        self.assertEqual(
            codes(lambda: self.sell(listing="list-2", recipient="buyer-3", key="list-2")),
            "RIGHT_SALE_LOCKED",
        )
        self.assertEqual(codes(lambda: self.pay(buyer="buyer-3", key="pay-wrong")), "BUYER_MISMATCH")
        self.assertEqual(self.machine.view("list-1")["phase"], BUY_HELD)
        self.assertIsNone(self.machine.view("list-1")["payment_ref"])
        self.assertEqual(
            codes(lambda: self.machine.cancel_listing("list-1", idempotency_key="cancel-buyer", seller_role="buyer-2")),
            "NOT_HOLDER",
        )
        released = self.machine.release_hold("hold-1", idempotency_key="release-1", buyer_role="buyer-2")
        self.assertEqual(released["listing"]["phase"], LISTED)
        self.assertIsNone(released["listing"]["buyer_role"])
        self.assertEqual(codes(lambda: self.hold(key="hold-again")), "ILLEGAL_TRANSITION")
        self.hold(hold="hold-3", key="hold-3")
        cancelled = self.machine.cancel_listing("list-1", idempotency_key="cancel-seller", seller_role="buyer-1")
        self.assertEqual(cancelled["listing"]["phase"], CANCELLED)
        self.assertTrue(cancelled["listing"]["terminal"])
        self.assertIs(cancelled["compensation_defined"], False)
        self.assertIs(self.machine.view_right("issue-1")["ticket"]["eligible"], True)
        self.assertEqual(codes(lambda: self.hold(hold="hold-4", key="hold-4")), "TERMINAL_IMMUTABLE")
        self.assertEqual(codes(lambda: self.pay(key="pay-after-cancel")), "TERMINAL_IMMUTABLE")
        relisted = self.sell(listing="list-2", recipient="buyer-3", key="list-b")
        self.assertEqual(relisted["listing"]["phase"], LISTED)
        self.assertEqual(relisted["listing"]["recipient_role"], "buyer-3")

        other = ResaleMachine()
        self.machine = other
        self.opened()
        self.machine.cancel_listing("list-1", idempotency_key="cancel-first", seller_role="buyer-1")
        self.assertEqual(codes(lambda: self.hold(key="hold-late")), "TERMINAL_IMMUTABLE")
        self.assertEqual(other.view("list-1")["phase"], CANCELLED)

        paid = ResaleMachine()
        self.machine = paid
        self.opened()
        self.hold()
        self.pay(buyer="buyer-2")
        journal = paid.export_journal()
        self.assertEqual(
            codes(lambda: paid.cancel_listing("list-1", idempotency_key="cancel-paid", seller_role="buyer-1")),
            "COMPENSATION_UNDEFINED",
        )
        self.assertEqual(paid.export_journal(), journal)
        self.assertEqual(paid.view("list-1")["phase"], PAYMENT_NOTED)
        self.assertEqual(paid.view("list-1")["holder_role"], "buyer-1")
        skipped = ResaleMachine()
        self.machine = skipped
        self.opened()
        direct = self.pay()
        self.assertEqual(direct["listing"]["phase"], PAYMENT_NOTED)
        self.assertIsNone(direct["listing"]["hold_id"])
        moved = self.transfer()
        self.assertEqual(moved["listing"]["phase"], TRANSFERRED)
        self.assertEqual(moved["listing"]["current_version"], 2)

    def test_stale_listing_policy_and_expiry_do_not_transfer(self):
        self.clock()
        self.adopt()
        self.assertEqual(codes(lambda: self.sell(seller="buyer-9", key="seller-wrong")), "NOT_HOLDER")
        self.assertEqual(codes(lambda: self.sell(version=2, key="version-wrong")), "STALE_VERSION")
        self.assertEqual(codes(lambda: self.sell(recipient="buyer-1", key="self-recipient")), "RECIPIENT_IS_HOLDER")
        self.assertEqual(codes(lambda: self.sell(amount=20_001, key="cap")), "RESALE_CAP")
        self.sell()
        self.assertEqual(codes(lambda: self.sell(listing="list-2", key="second-live")), "RIGHT_SALE_LOCKED")
        self.assertEqual(self.machine.view("list-1")["phase"], LISTED)
        self.assertEqual(codes(lambda: self.pay(ref=PAY, key="pay-reuse")), "PAYMENT_BINDING_CONFLICT")
        self.assertEqual(self.machine.view("list-1")["phase"], LISTED)
        self.pay()
        self.clock(EXPIRES, key="clock-expire")
        self.assertTrue(self.machine.view("list-1")["expired"])
        self.assertEqual(self.machine.view("list-1")["phase"], PAYMENT_NOTED)
        self.assertEqual(codes(lambda: self.transfer(key="transfer-late")), "LISTING_NOT_OPEN")
        self.assertEqual(self.machine.view("list-1")["holder_role"], "buyer-1")
        self.assertEqual(self.machine.view("list-1")["current_version"], 1)
        self.assertEqual(
            codes(lambda: self.machine.cancel_listing("list-1", idempotency_key="cancel-late", seller_role="buyer-1")),
            "COMPENSATION_UNDEFINED",
        )
        self.assertIs(self.machine.view_right("issue-1")["ticket"]["eligible"], True)
        relisted = self.sell(listing="list-late", expires=EXPIRES + OFFER_WINDOW_MS, key="list-late")
        self.assertEqual(relisted["listing"]["phase"], LISTED)
        self.assertEqual(self.machine.view("list-1")["phase"], PAYMENT_NOTED)
        self.assertTrue(self.machine.view("list-1")["expired"])
        self.assertEqual(self.machine.view("list-1")["current_version"], 1)
        blocked = ResaleMachine()
        blocked.set_clock("clock", idempotency_key="clock-b", now_ms=T0)
        blocked.adopt_issued(
            "issue-b",
            idempotency_key="adopt-b",
            show_id="show-b",
            slot=0,
            buyer_role="buyer-b",
            expires_ms=EXPIRES,
            order_id="order-b",
            amount=PRICE,
            payment_ref="ee" * 32,
            reservation_id=None,
            quote_ref=None,
            **show_kwargs(resale_allowed=False),
        )
        self.assertEqual(
            codes(lambda: blocked.list_resale(
                "list-b",
                idempotency_key="list-b",
                right_id="issue-b",
                version=1,
                seller_role="buyer-b",
                recipient_role="buyer-c",
                amount=PRICE,
                expires_ms=EXPIRES,
            )),
            "RESALE_POLICY_REJECTED",
        )
        self.assertEqual(codes(lambda: blocked.view("list-b")), "UNKNOWN_LISTING")
        self.assertIs(blocked.view_right("issue-b")["ticket"]["eligible"], True)

    def test_bound_transfer_waits_for_mock_commit_and_reconciles(self):
        book = settlement_at("AUTHORIZED", gross=SALE)
        self.machine = ResaleMachine(settlement_source=book)
        self.clock()
        self.adopt()
        self.sell(amount=SALE)
        self.pay(amount=SALE)
        self.machine.bind_settlement("list-1", idempotency_key="bind-1", settlement_id="claim-1")
        self.assertEqual(self.machine.view("list-1")["settlement_gate"], "BOUND")
        self.assertIs(self.machine.view("list-1")["mock_settlement_commit_observed"], False)
        before = book.canonical_state()
        journal = self.machine.export_journal()
        self.assertEqual(codes(lambda: self.transfer(key="transfer-early")), "SETTLEMENT_NOT_COMMITTED")
        self.assertEqual(codes(lambda: self.transfer(key="transfer-early")), "SETTLEMENT_NOT_COMMITTED")
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(book.canonical_state(), before)
        self.assertEqual(book.view("claim-1")["phase"], "AUTHORIZED")
        self.assertIs(book.view("claim-1")["funds_executed"], False)
        self.assertIs(book.view("claim-1")["admission_granted"], False)
        self.assertEqual(self.machine.view("list-1")["phase"], PAYMENT_NOTED)
        self.assertEqual(self.machine.view("list-1")["current_version"], 1)
        book.capture("claim-1", idempotency_key="cap-claim-1")
        self.assertEqual(codes(lambda: self.transfer(key="transfer-captured")), "SETTLEMENT_NOT_COMMITTED")
        book.commit(
            "claim-1",
            idempotency_key="commit-claim-1",
            movement_id="move-claim-1",
            gross=SALE,
            amount=SALE,
            fee=0,
            tax=0,
            held=0,
            adjustment=0,
        )
        self.assertEqual(codes(lambda: self.transfer(key="transfer-early")), "SETTLEMENT_NOT_COMMITTED")
        frozen = book.canonical_state()
        transferred = self.transfer(key="transfer-committed")
        self.assertEqual(book.canonical_state(), frozen)
        assert_not_final(self, transferred)
        self.assertEqual(transferred["listing"]["phase"], TRANSFERRED)
        self.assertEqual(transferred["listing"]["settlement_gate"], "MOCK_COMMIT_OBSERVED")
        self.assertIs(transferred["listing"]["mock_settlement_commit_observed"], True)
        self.assertIs(transferred["listing"]["economic_finality_claimed"], False)
        self.assertEqual(transferred["listing"]["current_version"], 2)
        self.assertIs(transferred["evidence"]["funds_executed"], False)
        report = self.machine.reconcile("list-1", idempotency_key="recon-1")
        self.assertTrue(report["matched"])
        self.assertEqual(report["entry_count"], len(self.machine.export_journal()))
        self.assertIs(report["economic_finality_claimed"], False)
        self.assertEqual(len(self.machine.export_journal()), len(journal) + 1)
        failed = settlement_at(FAILED, gross=SALE, settlement_id="claim-bad")
        blocked = ResaleMachine(settlement_source=failed)
        blocked.set_clock("clock", idempotency_key="clock-f", now_ms=T0)
        blocked.adopt_issued(
            "issue-f",
            idempotency_key="adopt-f",
            show_id="show-f",
            slot=0,
            buyer_role="buyer-f",
            expires_ms=EXPIRES,
            order_id="order-f",
            amount=PRICE,
            payment_ref="ef" * 32,
            **show_kwargs(),
        )
        blocked.list_resale(
            "list-f",
            idempotency_key="list-f",
            right_id="issue-f",
            version=1,
            seller_role="buyer-f",
            recipient_role="buyer-g",
            amount=SALE,
            expires_ms=EXPIRES,
        )
        blocked.observe_resale_payment(
            "list-f",
            idempotency_key="pay-f",
            payment_ref="ba" * 32,
            amount=SALE,
        )
        blocked.bind_settlement("list-f", idempotency_key="bind-f", settlement_id="claim-bad")
        self.assertEqual(
            codes(lambda: blocked.accept_resale("transfer-f", idempotency_key="transfer-f", listing_id="list-f")),
            "SETTLEMENT_NOT_COMMITTED",
        )
        self.assertEqual(blocked.view("list-f")["phase"], PAYMENT_NOTED)
        self.assertEqual(blocked.view("list-f")["current_version"], 1)
        failed_report = blocked.reconcile("list-f", idempotency_key="recon-f")
        self.assertTrue(failed_report["matched"])
        self.assertEqual(failed.view("claim-bad")["phase"], FAILED)

        mismatch = settlement_at("COMMITTED", gross=PRICE, settlement_id="claim-off")
        self.machine = ResaleMachine(settlement_source=mismatch)
        self.clock()
        self.adopt(right="issue-m", key="adopt-m", show_id="show-m", order_id="order-m", payment_ref="12" * 32)
        self.sell(listing="list-m", right="issue-m", amount=SALE, key="list-m")
        self.pay(listing="list-m", ref="34" * 32, amount=SALE, key="pay-m")
        self.machine.bind_settlement("list-m", idempotency_key="bind-m", settlement_id="claim-off")
        self.assertEqual(codes(lambda: self.transfer(transfer="transfer-m", listing="list-m", key="transfer-m")), "SETTLEMENT_AMOUNT_MISMATCH")
        self.assertEqual(self.machine.view("list-m")["phase"], PAYMENT_NOTED)

        bare = ResaleMachine()
        bare.set_clock("clock", idempotency_key="clock-bare", now_ms=T0)
        bare.adopt_issued(
            "issue-bare",
            idempotency_key="adopt-bare",
            show_id="show-bare",
            slot=0,
            buyer_role="buyer-bare",
            expires_ms=EXPIRES,
            order_id="order-bare",
            amount=PRICE,
            payment_ref="56" * 32,
            **show_kwargs(),
        )
        bare.list_resale(
            "list-bare",
            idempotency_key="list-bare",
            right_id="issue-bare",
            version=1,
            seller_role="buyer-bare",
            recipient_role="buyer-next",
            amount=SALE,
            expires_ms=EXPIRES,
        )
        bare.observe_resale_payment("list-bare", idempotency_key="pay-bare", payment_ref="78" * 32, amount=SALE)
        bare.bind_settlement("list-bare", idempotency_key="bind-bare", settlement_id="claim-missing")
        self.assertEqual(
            codes(lambda: bare.accept_resale("transfer-bare", idempotency_key="transfer-bare", listing_id="list-bare")),
            "SETTLEMENT_SOURCE_REQUIRED",
        )

        class Claiming:
            def view(self, settlement_id):
                return {
                    "phase": "COMMITTED",
                    "currency": "KRW",
                    "gross": SALE,
                    "funds_executed": True,
                    "admission_granted": False,
                    "bank_debit_observed": False,
                    "legal_debtor_bound": False,
                    "durable": False,
                    "external_return_closed": False,
                    "right_cancelled": False,
                }

        claiming = ResaleMachine(settlement_source=Claiming())
        claiming.set_clock("clock", idempotency_key="clock-c", now_ms=T0)
        claiming.adopt_issued(
            "issue-c",
            idempotency_key="adopt-c",
            show_id="show-c",
            slot=0,
            buyer_role="buyer-c",
            expires_ms=EXPIRES,
            order_id="order-c",
            amount=PRICE,
            payment_ref="9a" * 32,
            **show_kwargs(),
        )
        claiming.list_resale(
            "list-c",
            idempotency_key="list-c",
            right_id="issue-c",
            version=1,
            seller_role="buyer-c",
            recipient_role="buyer-d",
            amount=SALE,
            expires_ms=EXPIRES,
        )
        claiming.observe_resale_payment("list-c", idempotency_key="pay-c", payment_ref="9b" * 32, amount=SALE)
        claiming.bind_settlement("list-c", idempotency_key="bind-c", settlement_id="claim-c")
        self.assertEqual(
            codes(lambda: claiming.accept_resale("transfer-c", idempotency_key="transfer-c", listing_id="list-c")),
            "SETTLEMENT_VIEW_REJECTED",
        )
        self.assertEqual(claiming.view("list-c")["current_version"], 1)
        self.assertIs(claiming.view("list-c")["economic_finality_claimed"], False)

    def test_restore_replays_one_transfer_and_omits_rejections(self):
        book = settlement_at("COMMITTED", gross=PRICE, settlement_id="claim-ok")
        self.machine = ResaleMachine(settlement_source=book)
        self.opened()
        self.hold()
        self.pay(buyer="buyer-2")
        self.machine.bind_settlement("list-1", idempotency_key="bind-1", settlement_id="claim-ok")
        transferred = self.transfer()
        self.machine.close("list-1", idempotency_key="close-1")
        journal = self.machine.export_journal()
        before = self.machine.canonical_state()
        self.assertEqual(codes(lambda: self.pay(amount=PRICE - 1, key="pay-bad")), "TERMINAL_IMMUTABLE")
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(self.machine.canonical_state(), before)
        revived_book = SettlementMachine.restore(book.export_journal())
        revived = ResaleMachine.restore(journal, settlement_source=revived_book)
        self.assertEqual(revived.canonical_state(), before)
        self.assertEqual(revived.state_digest(), self.machine.state_digest())
        lost = revived.accept_resale("transfer-1", idempotency_key="transfer-transfer-1", listing_id="list-1")
        self.assertTrue(lost["duplicate"])
        self.assertEqual(lost["evidence"], transferred["evidence"])
        self.assertEqual(revived.view("list-1")["current_version"], 2)
        self.assertEqual(revived.view("list-1")["phase"], CLOSED)
        self.assertIs(revived.view("list-1")["economic_finality_claimed"], False)
        self.assertEqual(
            codes(lambda: ResaleMachine.restore(journal, settlement_source=SettlementMachine())),
            "UNKNOWN_SETTLEMENT",
        )
        tampered = self.machine.export_journal()
        tampered.append({"op": "tamper"})
        self.assertEqual(
            codes(lambda: ResaleMachine.restore(tampered, settlement_source=book)),
            "INVALID_JOURNAL",
        )
        self.assertEqual(codes(lambda: ResaleMachine.restore({"op": "list_resale"})), "INVALID_JOURNAL")

    def test_reservation_fsm_rejects_unissued_consumed_and_cancelled_tickets(self):
        absent = {
            "adopt_issued",
            "list_resale",
            "hold_buy",
            "release_hold",
            "observe_resale_payment",
            "accept_resale",
            "close",
        }
        self.assertTrue(RESERVATION_OPS.isdisjoint(absent))
        for name in absent:
            self.assertFalse(hasattr(ReservationMachine, name))

        cancelled = self.reservation("cancelled")
        resale = ResaleMachine(ticket_source=cancelled)
        resale.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        self.assertEqual(
            codes(lambda: resale.list_resale(
                "list-1",
                idempotency_key="list-1",
                right_id="issue-1",
                version=1,
                seller_role="buyer-1",
                recipient_role="buyer-2",
                amount=PRICE,
                expires_ms=EXPIRES,
                reservation_id="reserve-1",
            )),
            "TICKET_CANCELLED",
        )
        self.assertEqual(resale.export_journal(), [{"op": "set_clock", "idempotency_key": "clock-1", "subject_id": "clock", "body": {"now_ms": T0}}])

        held = self.reservation("held")
        early = ResaleMachine(ticket_source=held)
        early.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        self.assertEqual(
            codes(lambda: early.list_resale(
                "list-1",
                idempotency_key="list-1",
                right_id="issue-1",
                version=1,
                seller_role="buyer-1",
                recipient_role="buyer-2",
                amount=PRICE,
                expires_ms=EXPIRES,
                reservation_id="reserve-1",
            )),
            "TICKET_NOT_ISSUED",
        )

        consumed = self.reservation("consumed")
        blocked = ResaleMachine(ticket_source=consumed)
        blocked.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        self.assertEqual(
            codes(lambda: blocked.adopt_issued(
                "issue-1",
                idempotency_key="adopt-1",
                show_id="show-1",
                slot=0,
                buyer_role="buyer-1",
                expires_ms=EXPIRES,
                order_id="order-1",
                amount=PRICE,
                payment_ref=PAY,
                reservation_id="reserve-1",
                quote_ref="quote-1",
                **show_kwargs(),
            )),
            "ALREADY_CONSUMED",
        )
        self.assertEqual(
            codes(lambda: blocked.list_resale(
                "list-1",
                idempotency_key="list-1",
                right_id="issue-1",
                version=1,
                seller_role="buyer-1",
                recipient_role="buyer-2",
                amount=PRICE,
                expires_ms=EXPIRES,
                reservation_id="reserve-1",
            )),
            "ALREADY_CONSUMED",
        )

        issued = self.reservation("issued")
        self.machine = ResaleMachine(ticket_source=issued)
        self.clock()
        adopted = self.adopt(reservation_id="reserve-1")
        assert_not_final(self, adopted)
        self.assertEqual(adopted["right"]["holder_role"], "buyer-1")
        self.assertEqual(adopted["right"]["state"], "ACTIVE")
        self.assertEqual(adopted["ticket"]["reservation_id"], "reserve-1")
        issued.authorize_admission(
            "admit-1",
            idempotency_key="admit-1",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ,
            expires_ms=T0 + ADMISSION_WINDOW_MS,
        )
        self.assertEqual(codes(lambda: self.sell(reservation_id="reserve-1")), "ADMISSION_LOCKED")
        issued.set_clock("clock", idempotency_key="clock-admit", now_ms=T0 + ADMISSION_WINDOW_MS)
        listed = self.sell(reservation_id="reserve-1", key="list-after-expiry")
        self.assertEqual(listed["listing"]["phase"], LISTED)
        self.assertEqual(issued.view("reserve-1")["phase"], "ADMISSION_AUTHORIZED")
        self.assertIsNone(issued.view("reserve-1")["admission_id"])
        fresh = self.reservation("issued")
        sibling = ResaleMachine(ticket_source=fresh)
        sibling.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        sibling.adopt_issued(
            "issue-1",
            idempotency_key="adopt-1",
            show_id="show-1",
            slot=0,
            buyer_role="buyer-1",
            expires_ms=EXPIRES,
            order_id="order-1",
            amount=PRICE,
            payment_ref=PAY,
            reservation_id="reserve-1",
            quote_ref="quote-1",
            **show_kwargs(),
        )
        sibling.list_resale(
            "list-1",
            idempotency_key="list-1",
            right_id="issue-1",
            version=1,
            seller_role="buyer-1",
            recipient_role="buyer-2",
            amount=PRICE,
            expires_ms=EXPIRES,
            reservation_id="reserve-1",
        )
        sibling.observe_resale_payment(
            "list-1",
            idempotency_key="pay-1",
            payment_ref=SALE_PAY,
            amount=PRICE,
            buyer_role="buyer-2",
        )
        fresh.authorize_admission(
            "admit-1",
            idempotency_key="admit-1",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ,
            expires_ms=T0 + ADMISSION_WINDOW_MS,
        )
        fresh.consume(
            "consume-1",
            idempotency_key="consume-1",
            right_id="issue-1",
            version=1,
            gate_role="gate-a",
            request=REQ,
        )
        self.assertEqual(fresh.view("reserve-1")["phase"], "CONSUMED")
        journal = sibling.export_journal()
        self.assertEqual(
            codes(lambda: sibling.accept_resale("transfer-1", idempotency_key="transfer-1", listing_id="list-1")),
            "ALREADY_CONSUMED",
        )
        self.assertEqual(sibling.export_journal(), journal)
        self.assertEqual(sibling.view("list-1")["phase"], PAYMENT_NOTED)
        self.assertEqual(sibling.view("list-1")["holder_role"], "buyer-1")
        self.assertEqual(sibling.view("list-1")["current_version"], 1)
        self.assertTrue(all(entry["op"] not in absent for entry in fresh.export_journal()))

    def test_external_attempts_do_not_journal(self):
        self.opened()
        before = self.machine.canonical_state()
        journal = self.machine.export_journal()
        for kind in ("MARKETPLACE", "LIVE_HTTP", "KYC", "VENUE_REISSUE", "PG_CHARGE"):
            self.assertEqual(codes(lambda kind=kind: self.machine.reject_external(kind)), "EXTERNAL_UNSUPPORTED")
        self.assertEqual(codes(lambda: self.machine.reject_external(" ")), "INVALID_ID")
        self.assertEqual(self.machine.canonical_state(), before)
        self.assertEqual(self.machine.export_journal(), journal)
        self.assertEqual(
            codes(lambda: self.sell(amount=True, key="bad-amount")),
            "INVALID_AMOUNT",
        )
        self.assertEqual(
            codes(lambda: self.sell(amount=PRICE, key="bad-amount")),
            "IDEMPOTENCY_CONFLICT",
        )
        self.assertEqual(self.machine.view("list-1")["phase"], LISTED)
        self.assertEqual(self.machine.export_journal(), journal)
        self.pay()
        self.transfer()
        journal = self.machine.export_journal()
        report = self.machine.reconcile("list-1", idempotency_key="recon-1")
        self.assertTrue(report["matched"])
        self.assertEqual(len(report["state_digest"]), 64)
        self.assertEqual(self.machine.export_journal(), journal)
        replay = self.machine.reconcile("list-1", idempotency_key="recon-1")
        self.assertTrue(replay["duplicate"])
        restored = ResaleMachine.restore(journal)
        self.assertEqual(restored.canonical_state(), self.machine.canonical_state())
        again = restored.reconcile("list-1", idempotency_key="recon-1")
        self.assertFalse(again["duplicate"])
        self.assertTrue(again["matched"])
