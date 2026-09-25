"""Deterministic checks for the booking, resale, and admission gates."""

import unittest

from mock_gates import (
    ADMISSION_WINDOW_MS,
    NON_CLAIMS,
    OFFER_WINDOW_MS,
    PROVENANCE,
    GateError,
    MockGates,
)

PAY = "ab" * 32
PAY_B = "cd" * 32
REQ = "11" * 32
REQ_B = "22" * 32


def codes(fn):
    try:
        fn()
    except GateError as error:
        return error.code
    raise AssertionError("expected GateError")


def assert_flags(test, body):
    test.assertEqual(body["provenance"], PROVENANCE)
    test.assertFalse(body["duplicate"])
    for name, value in NON_CLAIMS.items():
        test.assertIs(body[name], value)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.gate = MockGates()
        self.gate.set_clock(1_000_000)

    def show(self, **changes):
        body = dict(
            organizer_role="organizer",
            capacity=2,
            gate_roles=["gate-a", "gate-b"],
            primary_price=10_001,
            resale_cap=20_000,
            resale_allowed=True,
            organizer_bps=1,
            platform_bps=1,
        )
        body.update(changes)
        return self.gate.register_show("show-1", **body)

    def hold(self, reservation="reserve-1", slot=0, buyer="buyer-1", expires=None):
        if expires is None:
            expires = 1_000_000 + OFFER_WINDOW_MS
        return self.gate.reserve_slot(
            reservation, show_id="show-1", slot=slot, buyer_role=buyer, expires_ms=expires
        )

    def order(self, order_id="order-1", reservation="reserve-1", amount=10_001, quote_ref="quote-1"):
        return self.gate.bind_order(order_id, reservation_id=reservation, amount=amount, quote_ref=quote_ref)

    def pay(self, ref=PAY, order_id="order-1", amount=10_001):
        return self.gate.observe_payment_fact(ref, order_id=order_id, amount=amount)

    def issue(self):
        return self.gate.issue("issue-1", order_id="order-1")

    def sell(
        self,
        listing_id="list-1",
        right_id="issue-1",
        amount=10_001,
        expires=None,
        version=1,
        seller="buyer-1",
        recipient="buyer-2",
    ):
        if expires is None:
            expires = self.gate.view_right(right_id)["logical_time_ms"] + OFFER_WINDOW_MS
        return self.gate.list_resale(
            listing_id,
            right_id=right_id,
            version=version,
            seller_role=seller,
            recipient_role=recipient,
            amount=amount,
            expires_ms=expires,
        )

    def test_primary_reservation_order_and_issuance_evidence(self):
        registered = self.show()
        assert_flags(self, registered)
        self.assertEqual(registered["show"]["slots"][0]["state"], "FREE")
        self.assertIs(registered["show"]["open"], True)
        held = self.hold()
        self.assertEqual(held["reservation"]["state"], "OPEN")
        self.assertIsNone(held["reservation"]["order_id"])
        ordered = self.order()
        self.assertEqual(ordered["order"]["amount"], 10_001)
        self.assertEqual(ordered["order"]["quote_ref"], "quote-1")
        self.assertEqual(ordered["order"]["currency"], "KRW")
        self.assertIsNone(ordered["order"]["payment_ref"])
        paid = self.pay()
        self.assertEqual(paid["show"]["payment_ref_count"], 1)
        issued = self.issue()
        evidence = issued["evidence"]
        self.assertEqual(evidence["kind"], 1)
        self.assertEqual(evidence["generation"], 1)
        self.assertEqual(evidence["version"], 1)
        self.assertEqual(evidence["holder_role"], "buyer-1")
        self.assertEqual(evidence["payment_ref"], PAY)
        self.assertIs(evidence["buyer_evidence_available"], False)
        self.assertIs(evidence["chain_issued"], False)
        self.assertNotIn("seller_due", evidence)
        self.assertEqual(issued["right"]["state"], "ACTIVE")
        self.assertEqual(issued["show"]["slots"][0]["state"], "ISSUED")
        again = self.gate.issue("issue-1", order_id="order-1")
        self.assertTrue(again["duplicate"])
        self.assertIsNone(again["applied"])
        self.assertEqual(again["right"]["version"], 1)
        self.assertEqual(codes(lambda: self.hold(reservation="reserve-2", slot=0, buyer="buyer-2")), "SLOT_OCCUPIED")

    def test_slot_release_before_payment_and_exclusivity(self):
        self.show()
        self.hold()
        self.assertEqual(codes(lambda: self.hold(reservation="reserve-2", buyer="buyer-2")), "SLOT_OCCUPIED")
        cancelled = self.gate.cancel_reservation("reserve-1")
        self.assertEqual(cancelled["reservation"]["state"], "CANCELLED")
        self.assertEqual(cancelled["show"]["slots"][0]["state"], "FREE")
        again = self.gate.cancel_reservation("reserve-1")
        self.assertTrue(again["duplicate"])
        self.hold(reservation="reserve-2", buyer="buyer-2")
        self.order(order_id="order-2", reservation="reserve-2")
        self.assertEqual(codes(lambda: self.gate.cancel_reservation("reserve-2")), "ORDER_BOUND")
        aborted = self.gate.abort_order("order-2")
        self.assertEqual(aborted["order"]["state"], "ABORTED")
        self.assertEqual(aborted["show"]["slots"][0]["state"], "FREE")
        self.assertTrue(self.gate.abort_order("order-2")["duplicate"])
        self.hold(reservation="reserve-3", buyer="buyer-3")
        self.gate.set_clock(1_000_000 + OFFER_WINDOW_MS)
        released = self.gate.cancel_reservation("reserve-3")
        self.assertEqual(released["show"]["slots"][0]["state"], "FREE")

    def test_price_binding_rejects_mismatch_and_conflicting_replay(self):
        self.show()
        self.hold()
        self.assertEqual(codes(lambda: self.order(amount=10_000)), "PRIMARY_PRICE_MISMATCH")
        self.assertEqual(codes(lambda: self.order(amount=True)), "INVALID_AMOUNT")
        placed = self.order()
        self.assertEqual(placed["order"]["amount"], 10_001)
        self.assertEqual(
            codes(lambda: self.order(quote_ref="quote-2")),
            "ORDER_BINDING_CONFLICT",
        )
        self.assertTrue(self.order()["duplicate"])
        self.assertEqual(codes(lambda: self.order(order_id="order-2")), "RESERVATION_ALREADY_ORDERED")
        later = 1_000_000 + OFFER_WINDOW_MS
        self.gate.set_clock(later)
        self.hold(reservation="reserve-9", slot=1, buyer="buyer-9", expires=later + OFFER_WINDOW_MS)
        self.gate.set_clock(later + OFFER_WINDOW_MS)
        self.assertEqual(codes(lambda: self.order(order_id="order-9", reservation="reserve-9")), "RESERVATION_EXPIRED")

    def test_payment_fact_is_not_funds_and_expiry_does_not_compensate(self):
        self.show()
        self.hold()
        self.order()
        self.assertEqual(codes(lambda: self.issue()), "PAYMENT_FACT_REQUIRED")
        self.assertEqual(codes(lambda: self.pay(ref="AB" * 32)), "PAYMENT_REF")
        self.pay()
        self.assertTrue(self.pay()["duplicate"])
        self.assertEqual(codes(lambda: self.pay(amount=10_000)), "PAYMENT_BINDING_CONFLICT")
        other = self.gate.register_show(
            "show-2",
            organizer_role="organizer",
            capacity=1,
            gate_roles=["gate-a"],
            primary_price=10_001,
            resale_cap=20_000,
            resale_allowed=False,
            organizer_bps=0,
            platform_bps=0,
        )
        self.assertEqual(other["show"]["payment_ref_count"], 0)
        self.gate.reserve_slot(
            "reserve-b",
            show_id="show-2",
            slot=0,
            buyer_role="buyer-b",
            expires_ms=1_000_000 + OFFER_WINDOW_MS,
        )
        self.gate.bind_order("order-b", reservation_id="reserve-b", amount=10_001)
        reused = self.gate.observe_payment_fact(PAY, order_id="order-b", amount=10_001)
        self.assertFalse(reused["duplicate"])
        self.assertEqual(reused["show"]["show_id"], "show-2")
        self.gate.set_clock(1_000_000 + OFFER_WINDOW_MS)
        self.assertTrue(self.pay()["duplicate"])
        self.assertEqual(codes(lambda: self.issue()), "RESERVATION_EXPIRED")
        show = self.gate.view_show("show-1")["show"]
        self.assertEqual(show["slots"][0]["state"], "RESERVED")
        self.assertIsNone(show["slots"][0]["right_id"])
        self.assertEqual(codes(lambda: self.gate.abort_order("order-1")), "COMPENSATION_UNDEFINED")
        self.assertEqual(codes(lambda: self.gate.cancel_reservation("reserve-1")), "ORDER_BOUND")

    def test_resale_listing_transfer_records_allocation_face_only(self):
        self.show()
        self.hold()
        self.order()
        self.pay()
        self.issue()
        listed = self.sell()
        assert_flags(self, listed)
        self.assertEqual(listed["listing"]["state"], "LISTED")
        self.assertTrue(listed["listing"]["attached"])
        self.assertEqual(listed["right"]["listing_id"], "list-1")
        self.gate.observe_resale_payment(PAY_B, listing_id="list-1", amount=10_001)
        transferred = self.gate.accept_resale("transfer-1", listing_id="list-1")
        evidence = transferred["evidence"]
        self.assertEqual(evidence["from_role"], "buyer-1")
        self.assertEqual(evidence["to_role"], "buyer-2")
        self.assertEqual(evidence["version_after"], 2)
        self.assertEqual(evidence["organizer_due"], 1)
        self.assertEqual(evidence["platform_due"], 1)
        self.assertEqual(evidence["seller_due"], 9_999)
        self.assertEqual(evidence["organizer_due"] + evidence["platform_due"] + evidence["seller_due"], 10_001)
        self.assertIs(evidence["funds_executed"], False)
        self.assertIs(evidence["chain_owner_current"], False)
        self.assertEqual(transferred["right"]["holder_role"], "buyer-2")
        self.assertEqual(transferred["right"]["version"], 2)
        self.assertIsNone(transferred["right"]["listing_id"])
        self.assertEqual(transferred["listing"]["state"], "ACCEPTED")
        self.assertEqual(self.gate.view_show("show-1")["show"]["payment_ref_count"], 2)
        again = self.gate.accept_resale("transfer-1", listing_id="list-1")
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["right"]["version"], 2)

    def test_resale_locks_and_policy_rejections(self):
        self.show()
        self.hold()
        self.order()
        self.pay()
        self.issue()
        self.sell()
        self.assertEqual(
            codes(lambda: self.gate.list_resale(
                "list-2",
                right_id="issue-1",
                version=1,
                seller_role="buyer-1",
                recipient_role="buyer-3",
                amount=10_001,
                expires_ms=1_000_000 + OFFER_WINDOW_MS,
            )),
            "RIGHT_SALE_LOCKED",
        )
        self.assertEqual(codes(lambda: self.sell(seller="buyer-2")), "LISTING_BINDING_CONFLICT")
        self.assertEqual(codes(lambda: self.gate.cancel_listing("list-1", seller_role="buyer-2")), "NOT_HOLDER")
        self.gate.observe_resale_payment(PAY_B, listing_id="list-1", amount=10_001)
        self.assertEqual(
            codes(lambda: self.gate.cancel_listing("list-1", seller_role="buyer-1")),
            "COMPENSATION_UNDEFINED",
        )
        self.gate.accept_resale("transfer-1", listing_id="list-1")
        self.assertEqual(
            codes(lambda: self.sell(
                listing_id="list-stale", version=1, seller="buyer-2", recipient="buyer-3"
            )),
            "STALE_VERSION",
        )
        blocked = self.gate.register_show(
            "show-3",
            organizer_role="organizer",
            capacity=1,
            gate_roles=["gate-a"],
            primary_price=5_000,
            resale_cap=5_000,
            resale_allowed=False,
            organizer_bps=0,
            platform_bps=0,
        )
        self.assertFalse(blocked["show"]["resale_allowed"])
        self.gate.reserve_slot(
            "reserve-c",
            show_id="show-3",
            slot=0,
            buyer_role="buyer-c",
            expires_ms=1_000_000 + OFFER_WINDOW_MS,
        )
        self.gate.bind_order("order-c", reservation_id="reserve-c", amount=5_000)
        self.gate.observe_payment_fact("ee" * 32, order_id="order-c", amount=5_000)
        self.gate.issue("issue-c", order_id="order-c")
        self.assertEqual(
            codes(lambda: self.gate.list_resale(
                "list-c",
                right_id="issue-c",
                version=1,
                seller_role="buyer-c",
                recipient_role="buyer-d",
                amount=5_000,
                expires_ms=1_000_000 + OFFER_WINDOW_MS,
            )),
            "RESALE_POLICY_REJECTED",
        )
        self.assertEqual(
            codes(lambda: self.sell(
                listing_id="list-d", version=2, seller="buyer-2", recipient="buyer-2"
            )),
            "RECIPIENT_IS_HOLDER",
        )
        self.assertEqual(
            codes(lambda: self.sell(
                listing_id="list-e", version=2, seller="buyer-2", recipient="buyer-3", amount=20_001
            )),
            "RESALE_CAP",
        )

    def test_admission_consume_once(self):
        self.show()
        self.hold()
        self.order()
        self.pay()
        issued = self.issue()
        self.assertEqual(
            codes(lambda: self.gate.consume_admission(
                "consume-0", right_id="issue-1", version=1, gate_role="gate-a", request=REQ
            )),
            "ADMISSION_REQUIRED",
        )
        authorized = self.gate.authorize_admission(
            "admit-1",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ,
            expires_ms=1_000_000 + ADMISSION_WINDOW_MS,
        )
        assert_flags(self, authorized)
        self.assertTrue(authorized["admission"]["attached"])
        self.assertEqual(authorized["right"]["admission_id"], "admit-1")
        self.assertEqual(
            codes(lambda: self.gate.consume_admission(
                "consume-1", right_id="issue-1", version=1, gate_role="gate-b", request=REQ
            )),
            "GATE_MISMATCH",
        )
        consumed = self.gate.consume_admission(
            "consume-1", right_id="issue-1", version=1, gate_role="gate-a", request=REQ
        )
        self.assertEqual(consumed["evidence"]["decision"], "CONSUMED_ONCE")
        self.assertIs(consumed["evidence"]["private_proof_verified"], False)
        self.assertIs(consumed["evidence"]["admission_routing_production"], False)
        self.assertEqual(consumed["right"]["state"], "CONSUMED")
        self.assertEqual(consumed["right"]["version"], 2)
        self.assertIsNone(consumed["right"]["admission_id"])
        self.assertEqual(
            codes(lambda: self.gate.consume_admission(
                "consume-2", right_id="issue-1", version=2, gate_role="gate-a", request=REQ
            )),
            "ALREADY_CONSUMED",
        )
        replay = self.gate.consume_admission(
            "consume-1", right_id="issue-1", version=1, gate_role="gate-a", request=REQ
        )
        self.assertTrue(replay["duplicate"])
        self.assertEqual(replay["right"]["version"], 2)
        issuance = self.gate.issue("issue-1", order_id="order-1")
        self.assertTrue(issuance["duplicate"])
        self.assertEqual(issuance["evidence"]["version"], 1)
        self.assertEqual(issuance["right"]["state"], "CONSUMED")
        self.assertEqual(codes(lambda: self.sell()), "RIGHT_NOT_ACTIVE")
        self.assertEqual(issued["evidence"]["kind"], 1)

    def test_listing_and_admission_exclude_each_other(self):
        self.show()
        self.hold()
        self.order()
        self.pay()
        self.issue()
        self.sell()
        self.assertEqual(
            codes(lambda: self.gate.authorize_admission(
                "admit-1",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=1_000_000 + ADMISSION_WINDOW_MS,
            )),
            "LISTING_LOCKED",
        )
        self.gate.cancel_listing("list-1", seller_role="buyer-1")
        self.gate.authorize_admission(
            "admit-1",
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ,
            expires_ms=1_000_000 + ADMISSION_WINDOW_MS,
        )
        self.assertEqual(
            codes(lambda: self.sell(listing_id="list-2")),
            "ADMISSION_LOCKED",
        )
        opened = 1_000_000 + ADMISSION_WINDOW_MS
        self.gate.set_clock(opened)
        self.assertEqual(
            codes(lambda: self.gate.consume_admission(
                "consume-1", right_id="issue-1", version=1, gate_role="gate-a", request=REQ
            )),
            "ADMISSION_EXPIRED",
        )
        listed = self.sell(listing_id="list-2", expires=opened + OFFER_WINDOW_MS)
        self.assertEqual(listed["listing"]["state"], "LISTED")
        self.assertIsNone(listed["right"]["admission_id"])
        self.assertEqual(codes(lambda: self.gate.accept_resale("transfer-x", listing_id="list-2")), "PAYMENT_FACT_REQUIRED")
        self.gate.observe_resale_payment(PAY_B, listing_id="list-2", amount=10_001)
        self.gate.set_clock(opened + OFFER_WINDOW_MS)
        self.assertEqual(codes(lambda: self.gate.accept_resale("transfer-x", listing_id="list-2")), "LISTING_NOT_OPEN")
        self.assertEqual(self.gate.view_right("issue-1")["right"]["holder_role"], "buyer-1")

    def test_show_registration_bounds(self):
        self.assertEqual(codes(lambda: self.show(capacity=0)), "CAPACITY")
        self.assertEqual(codes(lambda: self.show(capacity=17)), "CAPACITY")
        self.assertEqual(codes(lambda: self.show(capacity=True)), "CAPACITY")
        self.assertEqual(codes(lambda: self.show(gate_roles=[])), "GATES_EMPTY")
        self.assertEqual(codes(lambda: self.show(gate_roles="gate-a")), "GATES_TYPE")
        self.assertEqual(codes(lambda: self.show(gate_roles=["gate-a", "gate-a"])), "GATES_DUPLICATE")
        self.assertEqual(codes(lambda: self.show(gate_roles=[f"g{i}" for i in range(17)])), "GATES_LIMIT")
        self.assertEqual(codes(lambda: self.show(organizer_bps=10001)), "BPS")
        self.assertEqual(codes(lambda: self.show(organizer_bps=6000, platform_bps=6000)), "BPS_SUM")
        self.assertEqual(codes(lambda: self.show(resale_allowed=1)), "POLICY_FLAG")
        self.assertEqual(codes(lambda: self.show(resale_cap=0)), "INVALID_AMOUNT")
        self.assertEqual(codes(lambda: self.show(organizer_role=" organizer")), "INVALID_ID")
        self.assertEqual(codes(lambda: self.gate.set_clock(999_999)), "CLOCK_REGRESSION")
        opened = self.show(capacity=16, gate_roles=["gate-a"])
        self.assertEqual(opened["show"]["capacity"], 16)
        self.assertTrue(self.show(capacity=16, gate_roles=["gate-a"])["duplicate"])
        self.assertEqual(codes(lambda: self.show(capacity=16, gate_roles=["gate-b"])), "SHOW_BINDING_CONFLICT")
        self.assertEqual(codes(lambda: self.hold(expires=1_000_000 + OFFER_WINDOW_MS + 1)), "RESERVATION_WINDOW")
        self.hold()
        self.order()
        self.pay()
        self.issue()
        self.assertEqual(
            codes(lambda: self.gate.authorize_admission(
                "admit-wide",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=1_000_000 + ADMISSION_WINDOW_MS + 1,
            )),
            "ADMISSION_WINDOW",
        )
        self.assertEqual(
            codes(lambda: self.gate.authorize_admission(
                "admit-gate",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="missing",
                request=REQ,
                expires_ms=1_000_000 + ADMISSION_WINDOW_MS,
            )),
            "GATE_UNKNOWN",
        )
        self.assertEqual(
            codes(lambda: self.gate.authorize_admission(
                "admit-req",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request="ZZ" * 32,
                expires_ms=1_000_000 + ADMISSION_WINDOW_MS,
            )),
            "ADMISSION_REQUEST",
        )

    def test_duplicate_reserve_ignores_a_later_clock(self):
        self.show()
        first = self.hold()
        self.assertFalse(first["reservation"]["expired"])
        self.gate.set_clock(1_000_000 + OFFER_WINDOW_MS)
        replay = self.hold()
        self.assertTrue(replay["duplicate"])
        self.assertTrue(replay["reservation"]["expired"])
        self.assertEqual(replay["reservation"]["state"], "OPEN")
        self.assertEqual(replay["show"]["slots"][0]["state"], "RESERVED")

    def test_stale_presentation_after_transfer_cannot_enter(self):
        self.show()
        self.hold()
        self.order()
        self.pay()
        self.issue()
        self.sell()
        self.gate.observe_resale_payment(PAY_B, listing_id="list-1", amount=10_001)
        self.gate.accept_resale("transfer-1", listing_id="list-1")
        self.assertEqual(
            codes(lambda: self.gate.authorize_admission(
                "admit-old",
                right_id="issue-1",
                version=1,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=1_000_000 + ADMISSION_WINDOW_MS,
            )),
            "STALE_VERSION",
        )
        self.assertEqual(
            codes(lambda: self.gate.authorize_admission(
                "admit-holder",
                right_id="issue-1",
                version=2,
                holder_role="buyer-1",
                gate_role="gate-a",
                request=REQ,
                expires_ms=1_000_000 + ADMISSION_WINDOW_MS,
            )),
            "NOT_HOLDER",
        )
        self.gate.authorize_admission(
            "admit-new",
            right_id="issue-1",
            version=2,
            holder_role="buyer-2",
            gate_role="gate-b",
            request=REQ_B,
            expires_ms=1_000_000 + ADMISSION_WINDOW_MS,
        )
        entered = self.gate.consume_admission(
            "consume-new", right_id="issue-1", version=2, gate_role="gate-b", request=REQ_B
        )
        self.assertEqual(entered["evidence"]["decision"], "CONSUMED_ONCE")
        self.assertEqual(entered["right"]["holder_role"], "buyer-2")
        self.assertIs(entered["cross_channel_exclusive"], False)
