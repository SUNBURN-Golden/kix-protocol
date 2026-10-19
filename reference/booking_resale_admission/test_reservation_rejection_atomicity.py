"""Rejection-atomicity audit for the reservation machine.

Existing coverage map (test_reservation_fsm.py): every rejection code is
already exercised — SLOT_OCCUPIED, RESERVATION_EXPIRED, the
*_BINDING_CONFLICT family, COMPENSATION_UNDEFINED, CANCEL_AFTER_ISSUE,
ADMISSION_LOCKED, GATE_MISMATCH, ALREADY_CONSUMED, ADMISSION_EXPIRED,
ADMISSION_REQUIRED, IDEMPOTENCY_CONFLICT, INVALID_JOURNAL,
PRIMARY_PRICE_MISMATCH, RESERVATION_ALREADY_ORDERED, the §9.5
settlement-gate codes and the replay checks. Those tests compare the
journal or digest of the rejecting machine against itself; the
capability register (docs/status/CURRENT_CAPABILITY_REGISTER.md, EV-BRA
row) marks the control-machine atomicity audit for ReservationMachine
as not covered — the audit test_adopt_issued_atomicity.py added for the
resale and admission machines. This file closes that gap for every
mutation boundary a reservation command can reach
(BOOKING_RESALE_ADMISSION_GATES.md §9.4: a rejected command does not
enter the journal; the same key replays the same error).

Each case compares the machine that saw the rejected call with an
untouched control: canonical_state, state_digest, export_journal, the
restore(export_journal()) round trip and the result of a later valid
operation. A stored rejection (same key, same error) is the only trace
§9.4 allows; it is not part of canonical state.

The *_rolls_back cases inject a one-time failure after the mock gates
have already mutated — machine-level through ReservationMachine._invariant,
gate-level through MockGates._invariant — covering the late-failure
boundary that no deterministic input reaches.
"""

import unittest
from unittest import mock

from mock_gates import ADMISSION_WINDOW_MS, OFFER_WINDOW_MS, GateError, MockGates
from reservation_fsm import ReservationError, ReservationMachine
from test_reservation_fsm import codes, settlement_at

PAY_A = "ab" * 32
PAY_B = "cd" * 32
PAY_C = "ef" * 32
REQ_A = "11" * 32
REQ_B = "22" * 32
PRICE = 10_001
T0 = 1_000_000
EXPIRES = T0 + OFFER_WINDOW_MS
ADMIT_EXPIRES = T0 + ADMISSION_WINDOW_MS


class ReservationRejectionAtomicityTests(unittest.TestCase):
    def fresh(self, settlement=None):
        machine = ReservationMachine(settlement)
        machine.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        return machine

    def show(self, machine, show_id="show-1", key=None, **changes):
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
        return machine.register_show(show_id, idempotency_key=key or "show-" + show_id, **body)

    def hold(self, machine, reservation="reserve-1", key=None, **changes):
        body = dict(show_id="show-1", slot=0, buyer_role="buyer-1", expires_ms=EXPIRES)
        body.update(changes)
        return machine.hold(reservation, idempotency_key=key or "hold-" + reservation, **body)

    def confirm(self, machine, order="order-1", key=None, **changes):
        body = dict(reservation_id="reserve-1", amount=PRICE, quote_ref="quote-1")
        body.update(changes)
        return machine.confirm(order, idempotency_key=key or "confirm-" + order, **body)

    def pay(self, machine, order="order-1", key=None, **changes):
        body = dict(payment_ref=PAY_A, amount=PRICE)
        body.update(changes)
        return machine.observe_payment(order, idempotency_key=key or "pay-" + order, **body)

    def bind(self, machine, settlement_id="claim-1", key="bind-1"):
        return machine.bind_settlement(
            "reserve-1", idempotency_key=key, settlement_id=settlement_id
        )

    def issue(self, machine, issuance="issue-1", order="order-1", key=None):
        return machine.issue(issuance, idempotency_key=key or "issue-" + issuance, order_id=order)

    def admit(self, machine, admission="admit-1", key=None, **changes):
        body = dict(
            right_id="issue-1",
            version=1,
            holder_role="buyer-1",
            gate_role="gate-a",
            request=REQ_A,
            expires_ms=ADMIT_EXPIRES,
        )
        body.update(changes)
        return machine.authorize_admission(
            admission, idempotency_key=key or "admit-" + admission, **body
        )

    def consume(self, machine, consume_id="consume-1", key=None, **changes):
        body = dict(right_id="issue-1", version=1, gate_role="gate-a", request=REQ_A)
        body.update(changes)
        return machine.consume(
            consume_id, idempotency_key=key or "consume-" + consume_id, **body
        )

    def shown_pair(self):
        machine, control = self.fresh(), self.fresh()
        for side in (machine, control):
            self.show(side)
        return machine, control

    def held_pair(self):
        machine, control = self.shown_pair()
        for side in (machine, control):
            self.hold(side)
        return machine, control

    def confirmed_pair(self):
        machine, control = self.held_pair()
        for side in (machine, control):
            self.confirm(side)
        return machine, control

    def paid_pair(self):
        machine, control = self.confirmed_pair()
        for side in (machine, control):
            self.pay(side)
        return machine, control

    def issued_pair(self):
        machine, control = self.paid_pair()
        for side in (machine, control):
            self.issue(side)
        return machine, control

    def admitted_pair(self):
        machine, control = self.issued_pair()
        for side in (machine, control):
            self.admit(side)
        return machine, control

    def consumed_pair(self):
        machine, control = self.admitted_pair()
        for side in (machine, control):
            self.consume(side)
        return machine, control

    def second_leg(self, machine, through="confirm"):
        self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2")
        if through == "hold":
            return
        self.confirm(machine, "order-2", reservation_id="reserve-2")
        if through == "confirm":
            return
        self.pay(machine, "order-2", payment_ref=PAY_B)
        if through == "pay":
            return
        self.issue(machine, "issue-2", order="order-2")
        if through == "issue":
            return
        self.admit(
            machine,
            "admit-2",
            right_id="issue-2",
            holder_role="buyer-2",
            gate_role="gate-b",
            request=REQ_B,
        )

    def assert_same_as(self, machine, control, machine_source=None, control_source=None):
        self.assertEqual(machine.state_digest(), control.state_digest())
        self.assertEqual(machine.canonical_state(), control.canonical_state())
        self.assertEqual(machine.export_journal(), control.export_journal())
        restored = ReservationMachine.restore(
            machine.export_journal(), settlement_source=machine_source
        )
        self.assertEqual(restored.canonical_state(), machine.canonical_state())
        self.assertEqual(restored.state_digest(), machine.state_digest())
        control_restored = ReservationMachine.restore(
            control.export_journal(), settlement_source=control_source
        )
        self.assertEqual(control_restored.canonical_state(), control.canonical_state())

    def reject(self, code, fn):
        self.assertEqual(codes(fn), code)
        # §9.4: the same key with the same canonical arguments raises the
        # same stored error; that record is the only allowed trace.
        self.assertEqual(codes(fn), code)

    def fault(self, target, code="MOCK_INVARIANT"):
        if target is MockGates:
            error = GateError(code)
        else:
            error = ReservationError(code)
        return mock.patch.object(target, "_invariant", side_effect=[error])

    # --- set_clock -----------------------------------------------------

    def test_set_clock_invalid_subject_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject(
            "INVALID_ID",
            lambda: machine.set_clock("wall", idempotency_key="clock-bad", now_ms=T0 + 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.set_clock("clock", idempotency_key="clock-2", now_ms=T0 + 1),
            control.set_clock("clock", idempotency_key="clock-2", now_ms=T0 + 1),
        )
        self.assert_same_as(machine, control)

    def test_set_clock_regression_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject(
            "CLOCK_REGRESSION",
            lambda: machine.set_clock("clock", idempotency_key="clock-back", now_ms=T0 - 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.set_clock("clock", idempotency_key="clock-2", now_ms=T0 + 1),
            control.set_clock("clock", idempotency_key="clock-2", now_ms=T0 + 1),
        )
        self.assert_same_as(machine, control)

    # --- register_show -------------------------------------------------

    def test_register_show_capacity_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject("CAPACITY", lambda: self.show(machine, capacity=0))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.show(machine, key="show-ok"), self.show(control, key="show-ok")
        )
        self.assert_same_as(machine, control)

    def test_register_show_bps_sum_leaves_no_trace(self):
        machine, control = self.fresh(), self.fresh()
        self.reject(
            "BPS_SUM",
            lambda: self.show(machine, organizer_bps=6_000, platform_bps=6_000),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.show(machine, key="show-ok"), self.show(control, key="show-ok")
        )
        self.assert_same_as(machine, control)

    def test_register_show_binding_conflict_leaves_no_trace(self):
        machine, control = self.shown_pair()
        self.reject(
            "SHOW_BINDING_CONFLICT",
            lambda: self.show(machine, key="show-again", capacity=3),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.show(machine, "show-2"),
            self.show(control, "show-2"),
        )
        self.assert_same_as(machine, control)

    def test_register_show_replay_binding_leaves_no_trace(self):
        machine, control = self.shown_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.show(machine, key="show-again"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-1"),
            self.hold(control, "reserve-1"),
        )
        self.assert_same_as(machine, control)

    # --- hold ----------------------------------------------------------

    def test_hold_unknown_show_leaves_no_trace(self):
        machine, control = self.shown_pair()
        self.reject(
            "UNKNOWN_SHOW",
            lambda: self.hold(machine, show_id="show-9"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, key="hold-valid"),
            self.hold(control, key="hold-valid"),
        )
        self.assert_same_as(machine, control)

    def test_hold_window_leaves_no_trace(self):
        machine, control = self.shown_pair()
        self.reject(
            "RESERVATION_WINDOW",
            lambda: self.hold(machine, expires_ms=EXPIRES + 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, key="hold-valid"),
            self.hold(control, key="hold-valid"),
        )
        self.assert_same_as(machine, control)

    def test_hold_slot_occupied_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "SLOT_OCCUPIED",
            lambda: self.hold(machine, "reserve-2", buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-3", slot=1, buyer_role="buyer-3"),
            self.hold(control, "reserve-3", slot=1, buyer_role="buyer-3"),
        )
        self.assert_same_as(machine, control)

    def test_hold_binding_conflict_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "RESERVATION_BINDING_CONFLICT",
            lambda: self.hold(machine, buyer_role="buyer-9", key="hold-conflict"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    def test_hold_existing_reservation_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.hold(machine, key="hold-again"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    def test_hold_terminal_immutable_leaves_no_trace(self):
        machine, control = self.held_pair()
        for side in (machine, control):
            side.release("reserve-1", idempotency_key="release-1")
        self.reject("TERMINAL_IMMUTABLE", lambda: self.hold(machine, key="hold-again"))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", buyer_role="buyer-2"),
            self.hold(control, "reserve-2", buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    # --- release -------------------------------------------------------

    def test_release_unknown_reservation_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "UNKNOWN_RESERVATION",
            lambda: machine.release("ghost", idempotency_key="release-ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.release("reserve-1", idempotency_key="release-1"),
            control.release("reserve-1", idempotency_key="release-1"),
        )
        self.assert_same_as(machine, control)

    def test_release_illegal_transition_leaves_no_trace(self):
        machine, control = self.confirmed_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: machine.release("reserve-1", idempotency_key="release-1"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.cancel("reserve-1", idempotency_key="cancel-1"),
            control.cancel("reserve-1", idempotency_key="cancel-1"),
        )
        self.assert_same_as(machine, control)

    # --- confirm -------------------------------------------------------

    def test_confirm_price_mismatch_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "PRIMARY_PRICE_MISMATCH",
            lambda: self.confirm(machine, amount=PRICE - 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.confirm(machine, key="confirm-ok"),
            self.confirm(control, key="confirm-ok"),
        )
        self.assert_same_as(machine, control)

    def test_confirm_expired_leaves_no_trace(self):
        machine, control = self.shown_pair()
        for side in (machine, control):
            self.hold(side, expires_ms=T0 + 1_000)
            side.set_clock("clock", idempotency_key="clock-2", now_ms=T0 + 1_000)
        self.reject("RESERVATION_EXPIRED", lambda: self.confirm(machine))
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.release("reserve-1", idempotency_key="release-1"),
            control.release("reserve-1", idempotency_key="release-1"),
        )
        self.assert_same_as(machine, control)

    def test_confirm_already_ordered_leaves_no_trace(self):
        machine, control = self.confirmed_pair()
        self.reject(
            "RESERVATION_ALREADY_ORDERED",
            lambda: self.confirm(machine, "order-2"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.pay(machine), self.pay(control))
        self.assert_same_as(machine, control)

    def test_confirm_replay_binding_leaves_no_trace(self):
        machine, control = self.confirmed_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.confirm(machine, key="confirm-again"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.pay(machine), self.pay(control))
        self.assert_same_as(machine, control)

    def test_confirm_order_binding_conflict_leaves_no_trace(self):
        machine, control = self.confirmed_pair()
        for side in (machine, control):
            self.second_leg(side, through="hold")
        self.reject(
            "ORDER_BINDING_CONFLICT",
            lambda: self.confirm(machine, key="confirm-cross", reservation_id="reserve-2"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.confirm(machine, "order-2", reservation_id="reserve-2"),
            self.confirm(control, "order-2", reservation_id="reserve-2"),
        )
        self.assert_same_as(machine, control)

    # --- cancel --------------------------------------------------------

    def test_cancel_on_held_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: machine.cancel("reserve-1", idempotency_key="cancel-1"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.confirm(machine), self.confirm(control))
        self.assert_same_as(machine, control)

    def test_cancel_compensation_undefined_leaves_no_trace(self):
        machine, control = self.paid_pair()
        self.reject(
            "COMPENSATION_UNDEFINED",
            lambda: machine.cancel("reserve-1", idempotency_key="cancel-1"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.issue(machine), self.issue(control))
        self.assert_same_as(machine, control)

    def test_cancel_after_issue_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject(
            "CANCEL_AFTER_ISSUE",
            lambda: machine.cancel("reserve-1", idempotency_key="cancel-1"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.admit(machine), self.admit(control))
        self.assert_same_as(machine, control)

    # --- observe_payment -----------------------------------------------

    def test_observe_payment_unknown_order_leaves_no_trace(self):
        machine, control = self.confirmed_pair()
        self.reject(
            "UNKNOWN_ORDER",
            lambda: self.pay(machine, "ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.pay(machine, key="pay-ok"), self.pay(control, key="pay-ok")
        )
        self.assert_same_as(machine, control)

    def test_observe_payment_amount_mismatch_leaves_no_trace(self):
        machine, control = self.confirmed_pair()
        self.reject(
            "PAYMENT_AMOUNT_MISMATCH",
            lambda: self.pay(machine, amount=PRICE + 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.pay(machine, key="pay-ok"), self.pay(control, key="pay-ok")
        )
        self.assert_same_as(machine, control)

    def test_observe_payment_binding_conflict_leaves_no_trace(self):
        machine, control = self.paid_pair()
        for side in (machine, control):
            self.second_leg(side, through="confirm")
        self.reject(
            "PAYMENT_BINDING_CONFLICT",
            lambda: self.pay(machine, "order-2", key="pay-conflict"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.pay(machine, "order-2", key="pay-ok", payment_ref=PAY_B),
            self.pay(control, "order-2", key="pay-ok", payment_ref=PAY_B),
        )
        self.assert_same_as(machine, control)

    def test_observe_payment_after_issue_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.pay(machine, key="pay-late", payment_ref=PAY_C),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.admit(machine), self.admit(control))
        self.assert_same_as(machine, control)

    # --- bind_settlement -----------------------------------------------

    def test_bind_settlement_on_held_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.bind(machine),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.confirm(machine), self.confirm(control))
        self.assert_same_as(machine, control)

    def test_bind_settlement_conflict_leaves_no_trace(self):
        machine, control = self.paid_pair()
        for side in (machine, control):
            self.bind(side)
        self.reject(
            "SETTLEMENT_BINDING_CONFLICT",
            lambda: self.bind(machine, settlement_id="claim-2", key="bind-2"),
        )
        self.assert_same_as(machine, control)
        for side in (machine, control):
            self.second_leg(side, through="hold")
        self.assert_same_as(machine, control)

    def test_bind_settlement_rebind_same_leaves_no_trace(self):
        machine, control = self.paid_pair()
        for side in (machine, control):
            self.bind(side)
        self.reject(
            "ILLEGAL_TRANSITION",
            lambda: self.bind(machine, key="bind-again"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    def test_bind_settlement_after_issue_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject("ILLEGAL_TRANSITION", lambda: self.bind(machine))
        self.assert_same_as(machine, control)
        self.assertEqual(self.admit(machine), self.admit(control))
        self.assert_same_as(machine, control)

    # --- issue ---------------------------------------------------------

    def test_issue_unknown_order_leaves_no_trace(self):
        machine, control = self.paid_pair()
        self.reject(
            "UNKNOWN_ORDER",
            lambda: self.issue(machine, order="ghost"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.issue(machine, key="issue-ok"),
            self.issue(control, key="issue-ok"),
        )
        self.assert_same_as(machine, control)

    def test_issue_expired_leaves_no_trace(self):
        machine, control = self.shown_pair()
        for side in (machine, control):
            self.hold(side, expires_ms=T0 + 1_000)
            self.confirm(side)
            self.pay(side)
            side.set_clock("clock", idempotency_key="clock-2", now_ms=T0 + 1_000)
        self.reject("RESERVATION_EXPIRED", lambda: self.issue(machine))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    def test_issue_already_issued_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject(
            "ORDER_ALREADY_ISSUED",
            lambda: self.issue(machine, "issue-2"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.admit(machine), self.admit(control))
        self.assert_same_as(machine, control)

    def test_issue_binding_conflict_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject(
            "ISSUANCE_BINDING_CONFLICT",
            lambda: self.issue(machine, key="issue-cross", order="order-9"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.admit(machine), self.admit(control))
        self.assert_same_as(machine, control)

    def test_issue_uncommitted_settlement_leaves_no_trace(self):
        machine_book, control_book = settlement_at("AUTHORIZED"), settlement_at("AUTHORIZED")
        machine, control = self.fresh(machine_book), self.fresh(control_book)
        for side in (machine, control):
            self.show(side)
            self.hold(side)
            self.confirm(side)
            self.pay(side)
            self.bind(side)
        self.reject("SETTLEMENT_NOT_COMMITTED", lambda: self.issue(machine))
        self.assert_same_as(machine, control, machine_book, control_book)
        self.assertEqual(machine_book.canonical_state(), control_book.canonical_state())
        commit = dict(
            movement_id="move-claim-1",
            gross=PRICE,
            amount=PRICE,
            fee=0,
            tax=0,
            held=0,
            adjustment=0,
        )
        for book in (machine_book, control_book):
            book.capture("claim-1", idempotency_key="cap-claim-1")
            book.commit("claim-1", idempotency_key="commit-claim-1", **commit)
        self.assertEqual(
            self.issue(machine, key="issue-after"),
            self.issue(control, key="issue-after"),
        )
        self.assert_same_as(machine, control, machine_book, control_book)

    def test_issue_amount_mismatch_leaves_no_trace(self):
        machine_book = settlement_at("COMMITTED", gross=PRICE - 1)
        control_book = settlement_at("COMMITTED", gross=PRICE - 1)
        machine, control = self.fresh(machine_book), self.fresh(control_book)
        for side in (machine, control):
            self.show(side)
            self.hold(side)
            self.confirm(side)
            self.pay(side)
            self.bind(side)
        self.reject("SETTLEMENT_AMOUNT_MISMATCH", lambda: self.issue(machine))
        self.assert_same_as(machine, control, machine_book, control_book)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control, machine_book, control_book)

    def test_issue_unknown_settlement_leaves_no_trace(self):
        machine_book, control_book = settlement_at("COMMITTED"), settlement_at("COMMITTED")
        machine, control = self.fresh(machine_book), self.fresh(control_book)
        for side in (machine, control):
            self.show(side)
            self.hold(side)
            self.confirm(side)
            self.pay(side)
            self.bind(side, settlement_id="claim-9")
        self.reject("UNKNOWN_SETTLEMENT", lambda: self.issue(machine))
        self.assert_same_as(machine, control, machine_book, control_book)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control, machine_book, control_book)

    def test_issue_missing_settlement_source_leaves_no_trace(self):
        machine, control = self.paid_pair()
        for side in (machine, control):
            self.bind(side, settlement_id="claim-9")
        self.reject("SETTLEMENT_SOURCE_REQUIRED", lambda: self.issue(machine))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    # --- authorize_admission --------------------------------------------

    def test_authorize_admission_stale_version_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject("STALE_VERSION", lambda: self.admit(machine, version=0))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.admit(machine, key="admit-ok"),
            self.admit(control, key="admit-ok"),
        )
        self.assert_same_as(machine, control)

    def test_authorize_admission_unknown_gate_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject("GATE_UNKNOWN", lambda: self.admit(machine, gate_role="gate-z"))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.admit(machine, key="admit-ok"),
            self.admit(control, key="admit-ok"),
        )
        self.assert_same_as(machine, control)

    def test_authorize_admission_not_holder_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject("NOT_HOLDER", lambda: self.admit(machine, holder_role="buyer-9"))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.admit(machine, key="admit-ok"),
            self.admit(control, key="admit-ok"),
        )
        self.assert_same_as(machine, control)

    def test_authorize_admission_window_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject(
            "ADMISSION_WINDOW",
            lambda: self.admit(machine, expires_ms=ADMIT_EXPIRES + 1),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.admit(machine, key="admit-ok"),
            self.admit(control, key="admit-ok"),
        )
        self.assert_same_as(machine, control)

    def test_authorize_admission_locked_leaves_no_trace(self):
        machine, control = self.admitted_pair()
        self.reject(
            "ADMISSION_LOCKED",
            lambda: self.admit(machine, "admit-2", gate_role="gate-b", request=REQ_B),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.consume(machine), self.consume(control))
        self.assert_same_as(machine, control)

    def test_authorize_admission_binding_conflict_leaves_no_trace(self):
        machine, control = self.admitted_pair()
        self.reject(
            "ADMISSION_BINDING_CONFLICT",
            lambda: self.admit(machine, key="admit-cross", request=REQ_B),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.consume(machine), self.consume(control))
        self.assert_same_as(machine, control)

    def test_authorize_admission_on_consumed_leaves_no_trace(self):
        machine, control = self.consumed_pair()
        self.reject(
            "RIGHT_NOT_ACTIVE",
            lambda: self.admit(machine, "admit-2", version=2, gate_role="gate-b", request=REQ_B),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    # --- consume --------------------------------------------------------

    def test_consume_requires_admission_leaves_no_trace(self):
        machine, control = self.issued_pair()
        self.reject("ADMISSION_REQUIRED", lambda: self.consume(machine))
        self.assert_same_as(machine, control)
        self.assertEqual(self.admit(machine), self.admit(control))
        self.assert_same_as(machine, control)

    def test_consume_gate_mismatch_leaves_no_trace(self):
        machine, control = self.admitted_pair()
        self.reject(
            "GATE_MISMATCH",
            lambda: self.consume(machine, gate_role="gate-b"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.consume(machine, key="consume-ok"),
            self.consume(control, key="consume-ok"),
        )
        self.assert_same_as(machine, control)

    def test_consume_request_mismatch_leaves_no_trace(self):
        machine, control = self.admitted_pair()
        self.reject(
            "ADMISSION_REQUEST_MISMATCH",
            lambda: self.consume(machine, request=REQ_B),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.consume(machine, key="consume-ok"),
            self.consume(control, key="consume-ok"),
        )
        self.assert_same_as(machine, control)

    def test_consume_stale_version_leaves_no_trace(self):
        machine, control = self.admitted_pair()
        self.reject("STALE_VERSION", lambda: self.consume(machine, version=0))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.consume(machine, key="consume-ok"),
            self.consume(control, key="consume-ok"),
        )
        self.assert_same_as(machine, control)

    def test_consume_expired_admission_leaves_no_trace(self):
        machine, control = self.admitted_pair()
        for side in (machine, control):
            side.set_clock("clock", idempotency_key="clock-2", now_ms=ADMIT_EXPIRES)
        self.reject("ADMISSION_EXPIRED", lambda: self.consume(machine))
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.admit(
                machine,
                "admit-2",
                gate_role="gate-b",
                request=REQ_B,
                expires_ms=ADMIT_EXPIRES + ADMISSION_WINDOW_MS,
            ),
            self.admit(
                control,
                "admit-2",
                gate_role="gate-b",
                request=REQ_B,
                expires_ms=ADMIT_EXPIRES + ADMISSION_WINDOW_MS,
            ),
        )
        self.assert_same_as(machine, control)

    def test_consume_already_consumed_leaves_no_trace(self):
        machine, control = self.consumed_pair()
        self.reject(
            "ALREADY_CONSUMED",
            lambda: self.consume(machine, "consume-2", version=2),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    def test_consume_binding_conflict_leaves_no_trace(self):
        machine, control = self.admitted_pair()
        for side in (machine, control):
            self.second_leg(side, through="admit")
            self.consume(side)
        self.reject(
            "CONSUME_BINDING_CONFLICT",
            lambda: self.consume(
                machine,
                key="consume-cross",
                right_id="issue-2",
                gate_role="gate-b",
                request=REQ_B,
            ),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.consume(
                machine,
                "consume-2",
                right_id="issue-2",
                gate_role="gate-b",
                request=REQ_B,
            ),
            self.consume(
                control,
                "consume-2",
                right_id="issue-2",
                gate_role="gate-b",
                request=REQ_B,
            ),
        )
        self.assert_same_as(machine, control)

    # --- idempotency boundaries -----------------------------------------

    def test_idempotency_conflict_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "IDEMPOTENCY_CONFLICT",
            lambda: self.hold(machine, buyer_role="buyer-9"),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.hold(machine, "reserve-2", slot=1, buyer_role="buyer-2"),
            self.hold(control, "reserve-2", slot=1, buyer_role="buyer-2"),
        )
        self.assert_same_as(machine, control)

    def test_unfingerprintable_rejection_leaves_no_trace(self):
        machine, control = self.held_pair()
        self.reject(
            "INVALID_AMOUNT",
            lambda: self.confirm(machine, amount=object()),
        )
        self.assert_same_as(machine, control)
        self.assertEqual(self.confirm(machine), self.confirm(control))
        self.assert_same_as(machine, control)

    # --- late-failure rollback (machine-level fault injection) ----------

    def test_fault_set_clock_rolls_back(self):
        machine, control = self.fresh(), self.fresh()
        with self.fault(ReservationMachine):
            self.assertEqual(
                codes(lambda: machine.set_clock(
                    "clock", idempotency_key="clock-2", now_ms=T0 + 1)),
                "MOCK_INVARIANT",
            )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.set_clock("clock", idempotency_key="clock-3", now_ms=T0 + 1),
            control.set_clock("clock", idempotency_key="clock-3", now_ms=T0 + 1),
        )
        self.assert_same_as(machine, control)

    def test_fault_register_show_rolls_back(self):
        machine, control = self.fresh(), self.fresh()
        with self.fault(ReservationMachine):
            self.assertEqual(codes(lambda: self.show(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.show(machine), self.show(control))
        self.assert_same_as(machine, control)

    def test_fault_hold_rolls_back(self):
        machine, control = self.shown_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(codes(lambda: self.hold(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.hold(machine), self.hold(control))
        self.assert_same_as(machine, control)

    def test_fault_release_rolls_back(self):
        machine, control = self.held_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(
                codes(lambda: machine.release("reserve-1", idempotency_key="release-1")),
                "MOCK_INVARIANT",
            )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.release("reserve-1", idempotency_key="release-2"),
            control.release("reserve-1", idempotency_key="release-2"),
        )
        self.assert_same_as(machine, control)

    def test_fault_confirm_rolls_back(self):
        machine, control = self.held_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(codes(lambda: self.confirm(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.confirm(machine), self.confirm(control))
        self.assert_same_as(machine, control)

    def test_fault_cancel_rolls_back(self):
        machine, control = self.confirmed_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(
                codes(lambda: machine.cancel("reserve-1", idempotency_key="cancel-1")),
                "MOCK_INVARIANT",
            )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.cancel("reserve-1", idempotency_key="cancel-2"),
            control.cancel("reserve-1", idempotency_key="cancel-2"),
        )
        self.assert_same_as(machine, control)

    def test_fault_observe_payment_rolls_back(self):
        machine, control = self.confirmed_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(codes(lambda: self.pay(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.pay(machine), self.pay(control))
        self.assert_same_as(machine, control)

    def test_fault_bind_settlement_rolls_back(self):
        machine, control = self.paid_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(codes(lambda: self.bind(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(
            self.bind(machine, key="bind-2"),
            self.bind(control, key="bind-2"),
        )
        self.assert_same_as(machine, control)

    def test_fault_issue_rolls_back(self):
        machine, control = self.paid_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(codes(lambda: self.issue(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.issue(machine), self.issue(control))
        self.assert_same_as(machine, control)

    def test_fault_authorize_admission_rolls_back(self):
        machine, control = self.issued_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(codes(lambda: self.admit(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.admit(machine), self.admit(control))
        self.assert_same_as(machine, control)

    def test_fault_consume_rolls_back(self):
        machine, control = self.admitted_pair()
        with self.fault(ReservationMachine):
            self.assertEqual(codes(lambda: self.consume(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.consume(machine), self.consume(control))
        self.assert_same_as(machine, control)

    # --- late-failure rollback (gate-level fault injection) -------------

    def test_gate_fault_register_show_rolls_back(self):
        machine, control = self.fresh(), self.fresh()
        with self.fault(MockGates):
            self.assertEqual(codes(lambda: self.show(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.show(machine), self.show(control))
        self.assert_same_as(machine, control)

    def test_gate_fault_hold_rolls_back(self):
        machine, control = self.shown_pair()
        with self.fault(MockGates):
            self.assertEqual(codes(lambda: self.hold(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.hold(machine), self.hold(control))
        self.assert_same_as(machine, control)

    def test_gate_fault_release_rolls_back(self):
        machine, control = self.held_pair()
        with self.fault(MockGates):
            self.assertEqual(
                codes(lambda: machine.release("reserve-1", idempotency_key="release-1")),
                "MOCK_INVARIANT",
            )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.release("reserve-1", idempotency_key="release-2"),
            control.release("reserve-1", idempotency_key="release-2"),
        )
        self.assert_same_as(machine, control)

    def test_gate_fault_confirm_rolls_back(self):
        machine, control = self.held_pair()
        with self.fault(MockGates):
            self.assertEqual(codes(lambda: self.confirm(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.confirm(machine), self.confirm(control))
        self.assert_same_as(machine, control)

    def test_gate_fault_cancel_rolls_back(self):
        machine, control = self.confirmed_pair()
        with self.fault(MockGates):
            self.assertEqual(
                codes(lambda: machine.cancel("reserve-1", idempotency_key="cancel-1")),
                "MOCK_INVARIANT",
            )
        self.assert_same_as(machine, control)
        self.assertEqual(
            machine.cancel("reserve-1", idempotency_key="cancel-2"),
            control.cancel("reserve-1", idempotency_key="cancel-2"),
        )
        self.assert_same_as(machine, control)

    def test_gate_fault_observe_payment_rolls_back(self):
        machine, control = self.confirmed_pair()
        with self.fault(MockGates):
            self.assertEqual(codes(lambda: self.pay(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.pay(machine), self.pay(control))
        self.assert_same_as(machine, control)

    def test_gate_fault_issue_rolls_back(self):
        machine, control = self.paid_pair()
        with self.fault(MockGates):
            self.assertEqual(codes(lambda: self.issue(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.issue(machine), self.issue(control))
        self.assert_same_as(machine, control)

    def test_gate_fault_authorize_admission_rolls_back(self):
        machine, control = self.issued_pair()
        with self.fault(MockGates):
            self.assertEqual(codes(lambda: self.admit(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.admit(machine), self.admit(control))
        self.assert_same_as(machine, control)

    def test_gate_fault_consume_rolls_back(self):
        machine, control = self.admitted_pair()
        with self.fault(MockGates):
            self.assertEqual(codes(lambda: self.consume(machine)), "MOCK_INVARIANT")
        self.assert_same_as(machine, control)
        self.assertEqual(self.consume(machine), self.consume(control))
        self.assert_same_as(machine, control)


if __name__ == "__main__":
    unittest.main()
