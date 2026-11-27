"""All-or-nothing checks for adopt_issued in the resale and admission machines.

A rejected adopt_issued must leave no gate, right, credential or journal trace
(BOOKING_RESALE_ADMISSION_GATES.md 10.7 and 11.5). Every case compares the
machine that saw the rejected call with a control machine that never did.
Both machines run unbound: no ticket source and reservation_id=None.
"""

import unittest
from unittest import mock

from admission_fsm import AdmissionError, AdmissionMachine
from mock_gates import OFFER_WINDOW_MS
from resale_fsm import ResaleError, ResaleMachine

PAY_A = "ab" * 32
PAY_B = "cd" * 32
PAY_C = "ef" * 32
PRICE = 10_001
T0 = 1_000_000
EXPIRES = T0 + OFFER_WINDOW_MS


def show_kwargs(**changes):
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
    return body


class AtomicityContract:
    machine_cls = None
    error_cls = None

    def fresh(self):
        machine = self.machine_cls()
        machine.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        return machine

    def adopt(self, machine, right, slot, order, pay, key=None, show_id="show-1", **changes):
        body = dict(
            show_id=show_id,
            slot=slot,
            buyer_role="buyer-" + right,
            expires_ms=EXPIRES,
            order_id=order,
            amount=PRICE,
            payment_ref=pay,
        )
        body.update(show_kwargs())
        body.update(changes)
        return machine.adopt_issued(right, idempotency_key=key or "adopt-" + right, **body)

    def code(self, fn):
        try:
            fn()
        except self.error_cls as error:
            return error.code
        raise AssertionError("expected rejection")

    def control(self):
        machine = self.fresh()
        self.adopt(machine, "tix-1", 0, "ord-1", PAY_A)
        return machine

    def assert_same_as(self, machine, control):
        self.assertEqual(machine.state_digest(), control.state_digest())
        self.assertEqual(machine.canonical_state(), control.canonical_state())
        self.assertEqual(machine.export_journal(), control.export_journal())
        restored = self.machine_cls.restore(machine.export_journal())
        self.assertEqual(restored.canonical_state(), machine.canonical_state())
        self.assertEqual(restored.state_digest(), machine.state_digest())

    def test_order_binding_conflict_leaves_no_trace(self):
        machine = self.control()
        control = self.control()
        self.assertEqual(
            self.code(lambda: self.adopt(machine, "tix-2", 1, "ord-1", PAY_B)),
            "ORDER_BINDING_CONFLICT",
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.adopt(machine, "tix-3", 1, "ord-3", PAY_C),
            self.adopt(control, "tix-3", 1, "ord-3", PAY_C),
        )
        self.assert_same_as(machine, control)

    def test_payment_binding_conflict_leaves_no_trace(self):
        machine = self.control()
        control = self.control()
        self.assertEqual(
            self.code(lambda: self.adopt(machine, "tix-2", 1, "ord-2", PAY_A)),
            "PAYMENT_BINDING_CONFLICT",
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.adopt(machine, "tix-3", 1, "ord-3", PAY_C),
            self.adopt(control, "tix-3", 1, "ord-3", PAY_C),
        )
        self.assert_same_as(machine, control)

    def test_rejected_right_can_be_adopted_afterwards(self):
        machine = self.control()
        control = self.control()
        self.code(lambda: self.adopt(machine, "tix-2", 1, "ord-2", PAY_A))
        self.assertEqual(
            self.adopt(machine, "tix-2", 1, "ord-2", PAY_B, key="adopt-retry"),
            self.adopt(control, "tix-2", 1, "ord-2", PAY_B, key="adopt-retry"),
        )
        self.assert_same_as(machine, control)

    def test_rejection_after_show_registration_leaves_no_trace(self):
        machine = self.fresh()
        control = self.fresh()
        self.assertEqual(
            self.code(lambda: self.adopt(machine, "tix-1", 2, "ord-1", PAY_A)),
            "SLOT",
        )
        self.assert_same_as(machine, control)
        terms = show_kwargs(primary_price=PRICE + 1, resale_cap=30_000)
        self.assertEqual(
            self.adopt(machine, "tix-1", 0, "ord-1", PAY_A, key="adopt-terms", amount=PRICE + 1, **terms),
            self.adopt(control, "tix-1", 0, "ord-1", PAY_A, key="adopt-terms", amount=PRICE + 1, **terms),
        )
        self.assert_same_as(machine, control)

    def test_invariant_failure_after_materialize_rolls_back(self):
        # Labelled fault injection: _invariant raises once after the gates ran.
        machine = self.fresh()
        control = self.fresh()
        fault = self.error_cls("MOCK_INVARIANT")
        with mock.patch.object(self.machine_cls, "_invariant", side_effect=[fault]):
            self.assertEqual(
                self.code(lambda: self.adopt(machine, "tix-1", 0, "ord-1", PAY_A)),
                "MOCK_INVARIANT",
            )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.code(lambda: self.view_right(machine, "tix-1")),
            "UNKNOWN_RIGHT",
        )
        self.assertEqual(
            self.adopt(machine, "tix-1", 0, "ord-1", PAY_A),
            self.adopt(control, "tix-1", 0, "ord-1", PAY_A),
        )
        self.assert_same_as(machine, control)


class ResaleAtomicityTests(AtomicityContract, unittest.TestCase):
    machine_cls = ResaleMachine
    error_cls = ResaleError

    def view_right(self, machine, right):
        return machine.view_right(right)


class AdmissionAtomicityTests(AtomicityContract, unittest.TestCase):
    machine_cls = AdmissionMachine
    error_cls = AdmissionError

    def view_right(self, machine, right):
        return machine.view(right)


if __name__ == "__main__":
    unittest.main()
