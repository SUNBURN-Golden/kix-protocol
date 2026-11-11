"""Builder-authored PF-C01 mock boundaries, not an independent PASS.

Synthetic prices only; no 100000/500 fixture or product policy is adopted.
Contract: docs/contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md section 3 PF-C01
and BOOKING_RESALE_ADMISSION_GATES.md sections 1 and 3. Complements
test_mock_gates.GateTests.test_price_binding_rejects_mismatch_and_conflicting_replay
and test_reservation_rejection_atomicity's rejection/control evidence.
These checks cover bind_order only, without chain or payment execution.
"""

import random
import unittest

from mock_gates import OFFER_WINDOW_MS, GateError, MockGates

MONEY_MAX = 10**12


def code_of(fn):
    try:
        fn()
    except GateError as error:
        return error.code
    raise AssertionError("expected GateError")


class PrimaryPriceBindingPfC01Tests(unittest.TestCase):
    def setUp(self):
        self.gate = MockGates()
        self.gate.set_clock(1_000_000)

    def open_show(self, show_id, price):
        self.gate.register_show(
            show_id, organizer_role="organizer", capacity=1, gate_roles=["gate-a"],
            primary_price=price, resale_cap=price, resale_allowed=False,
            organizer_bps=0, platform_bps=0,
        )
        reservation_id = f"{show_id}-reservation"
        self.gate.reserve_slot(
            reservation_id, show_id=show_id, slot=0, buyer_role="fixture-buyer",
            expires_ms=1_000_000 + OFFER_WINDOW_MS,
        )
        return reservation_id

    def check_mismatch_then_exact(self, show_id, price, amount):
        reservation_id = self.open_show(show_id, price)
        order_id = f"{show_id}-order"
        self.assertEqual(code_of(lambda: self.gate.bind_order(
            order_id, reservation_id=reservation_id, amount=amount,
        )), "PRIMARY_PRICE_MISMATCH")
        exact = self.gate.bind_order(order_id, reservation_id=reservation_id, amount=price)
        self.assertEqual(exact["order"]["amount"], price)
        self.assertFalse(exact["duplicate"])

    def test_off_price_amounts_rejected_at_boundaries(self):
        for index, price in enumerate((1, 2, 7_777, MONEY_MAX - 1, MONEY_MAX)):
            candidates = sorted({price - 1, price + 1, 1, MONEY_MAX})
            for case, amount in enumerate(candidates):
                if 1 <= amount <= MONEY_MAX and amount != price:
                    with self.subTest(price=price, amount=amount):
                        self.check_mismatch_then_exact(f"boundary-{index}-{case}", price, amount)

    def test_non_money_amounts_rejected_before_price(self):
        price = 7_777
        for index, amount in enumerate((0, -1, MONEY_MAX + 1, True, False, 1.0, float(price))):
            with self.subTest(amount=amount, input_type=type(amount).__name__):
                reservation_id = self.open_show(f"invalid-{index}", price)
                order_id = f"invalid-{index}-order"
                self.assertEqual(code_of(lambda: self.gate.bind_order(
                    order_id, reservation_id=reservation_id, amount=amount,
                )), "INVALID_AMOUNT")
                exact = self.gate.bind_order(order_id, reservation_id=reservation_id, amount=price)
                self.assertEqual(exact["order"]["amount"], price)

    def test_seeded_prices(self):
        seed = 37
        r = random.Random(seed)
        for index in range(20):
            price = r.randint(1, MONEY_MAX)
            for case, amount in enumerate((price - 1, price + 1)):
                if 1 <= amount <= MONEY_MAX:
                    with self.subTest(seed=seed, price=price, amount=amount):
                        self.check_mismatch_then_exact(f"seeded-{index}-{case}", price, amount)


if __name__ == "__main__":
    unittest.main()
