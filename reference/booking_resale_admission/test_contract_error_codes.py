"""Negative tests for contract error codes (section 6) that no other test names.

Added by plan-contract-error-code-coverage. Each test expects one code from the
offline gates mock; synthetic ids only, fixtures follow test_mock_gates.py.
"""

import unittest

from mock_gates import ADMISSION_WINDOW_MS, OFFER_WINDOW_MS, GateError, MockGates

PAY = "ab" * 32
PAY_B = "cd" * 32
PAY_C = "ef" * 32
REQ = "11" * 32
REQ_B = "22" * 32
NOW = 1_000_000


def codes(fn):
    try:
        fn()
    except GateError as error:
        return error.code
    raise AssertionError("expected GateError")


class GateErrorCodeGapTests(unittest.TestCase):
    def setUp(self):
        self.gate = MockGates()
        self.gate.set_clock(NOW)

    def show(self):
        return self.gate.register_show(
            "show-1",
            organizer_role="organizer",
            capacity=2,
            gate_roles=["gate-a", "gate-b"],
            primary_price=10_001,
            resale_cap=20_000,
            resale_allowed=True,
            organizer_bps=1,
            platform_bps=1,
        )

    def hold(self, reservation="reserve-1", slot=0, buyer="buyer-1"):
        return self.gate.reserve_slot(
            reservation, show_id="show-1", slot=slot, buyer_role=buyer, expires_ms=NOW + OFFER_WINDOW_MS
        )

    def order(self, order_id="order-1", reservation="reserve-1"):
        return self.gate.bind_order(order_id, reservation_id=reservation, amount=10_001, quote_ref="quote-1")

    def pay(self, ref=PAY, order_id="order-1", amount=10_001):
        return self.gate.observe_payment_fact(ref, order_id=order_id, amount=amount)

    def issued(self):
        self.show()
        self.hold()
        self.order()
        self.pay()
        return self.gate.issue("issue-1", order_id="order-1")

    def sell(self, listing_id="list-1", expires=NOW + OFFER_WINDOW_MS, version=1):
        return self.gate.list_resale(
            listing_id,
            right_id="issue-1",
            version=version,
            seller_role="buyer-1",
            recipient_role="buyer-2",
            amount=10_001,
            expires_ms=expires,
        )

    def admit(self, admission="admit-1", request=REQ):
        return self.gate.authorize_admission(
            admission,
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=request,
            expires_ms=NOW + ADMISSION_WINDOW_MS,
        )

    def test_bad_version_is_version_type(self):
        self.issued()
        before = self.gate.view_right("issue-1")
        for bad in (-1, "1", True):
            self.assertEqual(codes(lambda: self.sell(version=bad)), "VERSION_TYPE")
        self.assertEqual(self.gate.view_right("issue-1"), before)

    def test_bad_clock_value_is_clock(self):
        for bad in (-1, "1", None, True):
            self.assertEqual(codes(lambda: self.gate.set_clock(bad)), "CLOCK")

    def test_listing_expiry_outside_window_is_listing_window(self):
        self.issued()
        self.assertEqual(codes(lambda: self.sell(expires=-1)), "LISTING_WINDOW")
        self.assertEqual(codes(lambda: self.sell(expires=NOW)), "LISTING_WINDOW")
        self.assertEqual(codes(lambda: self.sell(expires=NOW + OFFER_WINDOW_MS + 1)), "LISTING_WINDOW")

    def test_unregistered_show_is_unknown_show(self):
        self.assertEqual(
            codes(lambda: self.gate.reserve_slot(
                "reserve-1", show_id="show-x", slot=0, buyer_role="buyer-1", expires_ms=NOW + OFFER_WINDOW_MS
            )),
            "UNKNOWN_SHOW",
        )
        self.assertEqual(codes(lambda: self.gate.view_show("show-x")), "UNKNOWN_SHOW")

    def test_unregistered_order_is_unknown_order(self):
        self.show()
        self.assertEqual(codes(lambda: self.pay(order_id="order-x")), "UNKNOWN_ORDER")
        self.assertEqual(codes(lambda: self.gate.issue("issue-1", order_id="order-x")), "UNKNOWN_ORDER")
        self.assertEqual(codes(lambda: self.gate.abort_order("order-x")), "UNKNOWN_ORDER")

    def test_same_reservation_id_other_slot_is_reservation_binding_conflict(self):
        self.show()
        self.hold()
        before = self.gate.view_show("show-1")
        self.assertEqual(codes(lambda: self.hold(slot=1)), "RESERVATION_BINDING_CONFLICT")
        self.assertEqual(codes(lambda: self.hold(buyer="buyer-2")), "RESERVATION_BINDING_CONFLICT")
        self.assertEqual(self.gate.view_show("show-1"), before)

    def test_order_on_cancelled_reservation_is_reservation_not_open(self):
        self.show()
        self.hold()
        self.gate.cancel_reservation("reserve-1")
        self.assertEqual(codes(self.order), "RESERVATION_NOT_OPEN")

    def test_payment_or_issue_on_aborted_order_is_order_not_open(self):
        self.show()
        self.hold()
        self.order()
        self.gate.abort_order("order-1")
        self.assertEqual(codes(self.pay), "ORDER_NOT_OPEN")
        self.assertEqual(codes(lambda: self.gate.issue("issue-1", order_id="order-1")), "ORDER_NOT_OPEN")

    def test_abort_of_issued_order_is_order_not_abortable(self):
        self.issued()
        before = self.gate.view_right("issue-1")
        self.assertEqual(codes(lambda: self.gate.abort_order("order-1")), "ORDER_NOT_ABORTABLE")
        self.assertEqual(self.gate.view_right("issue-1"), before)

    def test_second_payment_ref_on_paid_order_is_order_payment_bound(self):
        self.show()
        self.hold()
        self.order()
        self.pay()
        self.assertEqual(codes(lambda: self.pay(ref=PAY_B)), "ORDER_PAYMENT_BOUND")

    def test_wrong_primary_payment_amount_is_payment_amount_mismatch(self):
        self.show()
        self.hold()
        self.order()
        self.assertEqual(codes(lambda: self.pay(amount=10_000)), "PAYMENT_AMOUNT_MISMATCH")
        self.assertEqual(codes(lambda: self.gate.issue("issue-1", order_id="order-1")), "PAYMENT_FACT_REQUIRED")

    def test_same_issuance_id_other_order_is_issuance_binding_conflict(self):
        self.issued()
        before = self.gate.view_right("issue-1")
        self.assertEqual(
            codes(lambda: self.gate.issue("issue-1", order_id="order-2")), "ISSUANCE_BINDING_CONFLICT"
        )
        self.assertEqual(self.gate.view_right("issue-1"), before)

    def test_same_transfer_id_other_listing_is_transfer_binding_conflict(self):
        self.issued()
        self.sell()
        self.gate.observe_resale_payment(PAY_B, listing_id="list-1", amount=10_001)
        self.gate.accept_resale("transfer-1", listing_id="list-1")
        self.assertEqual(
            codes(lambda: self.gate.accept_resale("transfer-1", listing_id="list-2")),
            "TRANSFER_BINDING_CONFLICT",
        )

    def test_same_admission_id_other_request_is_admission_binding_conflict(self):
        self.issued()
        self.admit()
        self.assertEqual(codes(lambda: self.admit(request=REQ_B)), "ADMISSION_BINDING_CONFLICT")

    def test_same_consume_id_other_request_is_consume_binding_conflict(self):
        self.issued()
        self.admit()
        self.gate.consume_admission("consume-1", right_id="issue-1", version=1, gate_role="gate-a", request=REQ)
        self.assertEqual(
            codes(lambda: self.gate.consume_admission(
                "consume-1", right_id="issue-1", version=1, gate_role="gate-a", request=REQ_B
            )),
            "CONSUME_BINDING_CONFLICT",
        )

    def test_second_resale_payment_ref_is_listing_payment_bound(self):
        self.issued()
        self.sell()
        self.gate.observe_resale_payment(PAY_B, listing_id="list-1", amount=10_001)
        self.assertEqual(
            codes(lambda: self.gate.observe_resale_payment(PAY_C, listing_id="list-1", amount=10_001)),
            "LISTING_PAYMENT_BOUND",
        )

    def test_wrong_resale_payment_amount_is_resale_amount_mismatch(self):
        self.issued()
        self.sell()
        self.assertEqual(
            codes(lambda: self.gate.observe_resale_payment(PAY_B, listing_id="list-1", amount=10_000)),
            "RESALE_AMOUNT_MISMATCH",
        )
        self.assertEqual(
            codes(lambda: self.gate.accept_resale("transfer-1", listing_id="list-1")), "PAYMENT_FACT_REQUIRED"
        )

    def test_consume_with_other_request_is_admission_request_mismatch(self):
        self.issued()
        self.admit()
        before = self.gate.view_right("issue-1")
        self.assertEqual(
            codes(lambda: self.gate.consume_admission(
                "consume-1", right_id="issue-1", version=1, gate_role="gate-a", request=REQ_B
            )),
            "ADMISSION_REQUEST_MISMATCH",
        )
        self.assertEqual(self.gate.view_right("issue-1"), before)


if __name__ == "__main__":
    unittest.main()
