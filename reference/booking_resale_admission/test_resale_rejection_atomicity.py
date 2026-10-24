"""Deterministic, source-informed rejection audit; see the dated validation record.

The ordinary rows fill the control/source/later-command gap in test_resale_fsm
and test_gate_properties (property e). Unbound adoption rollback is already
sufficiently covered by test_adopt_issued_atomicity and is not repeated here.
No imported TestCase classes: discovery must run each existing test only once.
"""

import json
import unittest
from unittest import mock

from mock_gates import ADMISSION_WINDOW_MS, GATE_ROLE_LIMIT, OFFER_WINDOW_MS
from reservation_fsm import ReservationMachine
from resale_fsm import REPLAYABLE, ResaleError, ResaleMachine
from test_resale_fsm import codes, policy, settlement_at, show_kwargs

T0 = 1_000_000
PRICE = 10_001
EXPIRES = T0 + OFFER_WINDOW_MS
PAY = "ab" * 32
SALE_PAY = "cd" * 32
REQ = "11" * 32


class SourceStub:
    """Per-environment fault/answer stub with inspectable, immutable backing state."""

    def __init__(self, source, mode):
        self.source = source
        self.mode = mode

    def __getattr__(self, name):
        return getattr(self.source, name)

    def authorize_admission(self, *args, **kwargs):
        if self.mode == "authorize_down":
            raise RuntimeError("fixture authorize unavailable")
        return self.source.authorize_admission(*args, **kwargs)

    def consume(self, *args, **kwargs):
        if self.mode == "consume_down":
            raise RuntimeError("fixture consume unavailable")
        return self.source.consume(*args, **kwargs)

    def canonical_state(self):
        return (self.mode, self.source.canonical_state())

    def export_journal(self):
        return self.source.export_journal()

    def set_clock(self, *args, **kwargs):
        if self.mode == "clock_down" and kwargs["now_ms"] == T0 + 10:
            raise RuntimeError("fixture clock unavailable")
        return self.source.set_clock(*args, **kwargs)

    def view(self, subject):
        if self.mode == "down":
            raise RuntimeError("fixture view unavailable")
        row = self.source.view(subject)
        if self.mode == "granted":
            row["admission_granted"] = True
        return row

    def view_right(self, subject):
        if self.mode == "down":
            raise RuntimeError("fixture ownership unavailable")
        row = self.source.view_right(subject)
        if self.mode == "inactive":
            row["right"]["state"] = "INACTIVE"
        if self.mode == "consumed":
            row["right"]["state"] = "CONSUMED"
        return row

    def view_presentation(self, *args, **kwargs):
        row = self.source.view_presentation(*args, **kwargs)
        if self.mode == "stale":
            row["presentation"]["matches_current_right"] = False
        return row


class AuditHarness:
    """Shared assertions and public-command fixtures, deliberately not a TestCase."""

    machine_cls = ResaleMachine
    error_cls = ResaleError

    def reservation(self, stop="issued", book=None, resale_allowed=True):
        tickets = ReservationMachine(settlement_source=book)
        tickets.set_clock("clock", idempotency_key="clock-1", now_ms=T0)
        tickets.register_show("show-1", idempotency_key="show-1",
                              **show_kwargs(resale_allowed=resale_allowed))
        tickets.hold("reserve-1", idempotency_key="hold-1", show_id="show-1",
                     slot=0, buyer_role="buyer-1", expires_ms=EXPIRES)
        if stop == "held":
            return tickets
        tickets.confirm("order-1", idempotency_key="confirm-1", reservation_id="reserve-1",
                        amount=PRICE, quote_ref="quote-1")
        if stop == "cancelled":
            tickets.cancel("reserve-1", idempotency_key="cancel-1")
            return tickets
        tickets.observe_payment("order-1", idempotency_key="pay-1", payment_ref=PAY, amount=PRICE)
        if stop == "paid":
            return tickets
        if book is not None:
            tickets.bind_settlement("reserve-1", idempotency_key="reserve-bind", settlement_id="claim-1")
        tickets.issue("issue-1", idempotency_key="issue-1", order_id="order-1")
        if stop in ("admitted", "consumed"):
            self.ticket_admit(tickets)
        if stop == "consumed":
            self.ticket_consume(tickets)
        return tickets

    def ticket_admit(self, tickets):
        return tickets.authorize_admission(
            "ticket-admit", idempotency_key="ticket-admit", right_id="issue-1", version=1,
            holder_role="buyer-1", gate_role="gate-a", request=REQ,
            expires_ms=T0 + ADMISSION_WINDOW_MS)

    def ticket_consume(self, tickets):
        return tickets.consume("ticket-consume", idempotency_key="ticket-consume",
                               right_id="issue-1", version=1, gate_role="gate-a", request=REQ)

    def adopt_body(self, **changes):
        body = dict(show_id="show-1", slot=0, buyer_role="buyer-1", expires_ms=EXPIRES,
                    order_id="order-1", amount=PRICE, payment_ref=PAY,
                    reservation_id="reserve-1", quote_ref="quote-1", **show_kwargs())
        body.update(changes)
        return body

    def command(self, env, op, *, subject=None, key="probe", **changes):
        defaults = {
            "set_clock": ("clock", dict(now_ms=T0 + 1)),
            "adopt_issued": ("issue-1", self.adopt_body()),
            "list_resale": ("list-1", dict(right_id="issue-1", version=1,
                seller_role="buyer-1", recipient_role="buyer-2", amount=PRICE,
                expires_ms=EXPIRES, reservation_id="reserve-1")),
            "hold_buy": ("hold-1", dict(listing_id="list-1", buyer_role="buyer-2")),
            "release_hold": ("hold-1", dict(buyer_role="buyer-2")),
            "cancel_listing": ("list-1", dict(seller_role="buyer-1")),
            "observe_resale_payment": ("list-1", dict(payment_ref=SALE_PAY, amount=PRICE,
                buyer_role="buyer-2")),
            "bind_settlement": ("list-1", dict(settlement_id="claim-1")),
            "accept_resale": ("transfer-1", dict(listing_id="list-1")),
            "close": ("list-1", {}),
            "authorize_admission": ("admit-1", dict(right_id="issue-1", version=1,
                holder_role="buyer-1", gate_role="gate-a", request=REQ,
                expires_ms=T0 + ADMISSION_WINDOW_MS)),
            "consume": ("consume-1", dict(right_id="issue-1", version=1,
                gate_role="gate-a", request=REQ)),
        }
        if op == "restore":
            return self.machine_cls.restore(changes.get("journal", [{"op": "tamper"}]), **env["sources"])
        if op == "reject_external":
            return env["machine"].reject_external(subject or "LIVE_HTTP")
        default_subject, body = defaults[op]
        if env.get("unbound") and op in ("adopt_issued", "list_resale"):
            body["reservation_id"] = None
            if op == "adopt_issued":
                body["quote_ref"] = None
        body.update(changes)
        return getattr(env["machine"], op)(default_subject if subject is None else subject,
                                         idempotency_key=key, **body)

    def snapshot(self, env):
        machine = env["machine"]
        return (machine.canonical_state(), machine.state_digest(), machine.export_journal(),
                self.views(env), self.source_state(env))

    def source_state(self, env):
        sources = env["sources"] | env.get("other_sources", {})
        return {name: (source.canonical_state(),
                       source.export_journal() if hasattr(source, "export_journal") else None)
                for name, source in sources.items() if source is not None}

    def restore_outcome(self, env):
        before = self.source_state(env)
        try:
            restored = self.machine_cls.restore(env["machine"].export_journal(), **env["sources"])
            outcome = ("ok", restored.canonical_state(), restored.state_digest())
        except self.error_cls as error:
            outcome = ("error", error.code)
        self.assertEqual(self.source_state(env), before, "restore mutated a live bound source")
        return outcome

    def assert_same_as(self, env, control, *, restore_error=None):
        self.assertEqual(self.snapshot(env), self.snapshot(control))
        actual, expected = self.restore_outcome(env), self.restore_outcome(control)
        self.assertEqual(actual, expected)
        if restore_error is None:
            self.assertEqual(actual, ("ok", env["machine"].canonical_state(), env["machine"].state_digest()))
        else:
            self.assertEqual(actual, ("error", restore_error))

    def later(self, env, control, restore_error=None):
        # A new, valid clock command exercises expiration/invariants and delegation
        # even when a lifecycle rejection cannot be repaired (e.g. consumed ticket).
        now = max(json.loads(side["machine"].canonical_state())["logical_time_ms"]
                  for side in (env, control))
        for side in (env, control):
            for source in side["sources"].values():
                if source is not None:
                    state = source.canonical_state()
                    if isinstance(state, str):
                        now = max(now, json.loads(state).get("logical_time_ms", 0))
        self.assertEqual(self.command(env, "set_clock", key="later-valid", now_ms=now + 1),
                         self.command(control, "set_clock", key="later-valid", now_ms=now + 1))
        self.assert_same_as(env, control, restore_error=restore_error)

    def reject(self, code, fn):
        for _ in range(2):
            with self.assertRaises(self.error_cls) as raised:
                fn()
            self.assertEqual(raised.exception.code, code)

    def run_row(self, row):
        op, code, fixture, changes, restore_error = row
        env, control = self.environment(fixture), self.environment(fixture)
        before = self.snapshot(env)
        self.assert_same_as(env, control, restore_error=restore_error)
        self.reject(code, lambda: self.command(env, op, **changes))
        if op == "set_clock" and code == "INVALID_ID":
            self.reject("INVALID_ID", lambda: self.command(env, op, key=" "))
        self.assertEqual(self.snapshot(env), before)
        self.assert_same_as(env, control, restore_error=restore_error)
        self.later(env, control, restore_error)


    def run_fault_row(self, op, fixture):
        env, control, accepted = (self.environment("unbound_" + fixture) for _ in range(3))
        before = self.snapshot(env)
        with mock.patch.object(self.machine_cls, "_invariant",
                               side_effect=[self.error_cls("MOCK_INVARIANT")]):
            with self.assertRaises(self.error_cls) as raised:
                self.command(env, op)
            self.assertEqual(raised.exception.code, "MOCK_INVARIANT")
        self.command(accepted, op)
        # B: the fault occurs after local mutation and before _accept. Pin the
        # complete public canonical shape against the normally applied command,
        # with the absent journal/receipt count accounted for explicitly.
        expected = json.loads(accepted["machine"].canonical_state())
        expected["journal"] = control["machine"].export_journal()
        for listing in expected.get("listings", []):
            listing["accepted_entries"] -= 1
        self.assertEqual(json.loads(env["machine"].canonical_state()), expected)
        self.assertNotEqual(env["machine"].canonical_state(), before[0])
        self.assertNotEqual(env["machine"].state_digest(), before[1])
        self.assertEqual(env["machine"].export_journal(), before[2])
        self.assertEqual(self.source_state(env), self.source_state(control))
        self.assertEqual(self.restore_outcome(env), self.restore_outcome(control))
        self.assertEqual(self.restore_outcome(env),
                         ("ok", control["machine"].canonical_state(), control["machine"].state_digest()))


class ResaleRejectionAtomicityTests(AuditHarness, unittest.TestCase):
    def environment(self, fixture="adopted"):
        unbound = fixture.startswith("unbound") or fixture in ("no_source", "unknown_right")
        tickets = None if unbound else self.reservation(
            fixture.removeprefix("ticket_") if fixture.startswith("ticket_") else "issued",
            resale_allowed=fixture != "policy")
        book = None
        if fixture.startswith("settlement_"):
            phase = "AUTHORIZED" if fixture == "settlement_pending" else "COMMITTED"
            book = settlement_at(phase, gross=PRICE + (fixture == "settlement_amount"))
            if fixture == "settlement_granted":
                book = SourceStub(book, "granted")
        env = dict(machine=ResaleMachine(ticket_source=tickets, settlement_source=book),
                   sources=dict(ticket_source=tickets, settlement_source=book), unbound=unbound)
        self.command(env, "set_clock", key="gate-clock", now_ms=T0)
        fixture = fixture.removeprefix("unbound_")
        if fixture in ("fresh", "no_source", "unknown_right") or fixture.startswith("ticket_"):
            return env
        self.command(env, "adopt_issued", key="adopt-1", resale_allowed=fixture != "policy")
        if fixture in ("adopted", "policy", "adopted_admitted", "adopted_consumed"):
            if fixture in ("adopted_admitted", "adopted_consumed"):
                self.ticket_admit(tickets)
                if fixture == "adopted_consumed":
                    self.ticket_consume(tickets)
            return env
        self.command(env, "list_resale", key="list-1")
        if fixture in ("held", "released", "paid_held"):
            self.command(env, "hold_buy", key="hold-1")
        if fixture == "released":
            self.command(env, "release_hold", key="release-1")
        if fixture in ("paid", "paid_held", "bound", "transferred", "closed", "expired_paid", "consumed_paid", "admitted_listing") or fixture.startswith("settlement_"):
            self.command(env, "observe_resale_payment", key="sale-pay")
        if fixture == "bound" or fixture.startswith("settlement_"):
            self.command(env, "bind_settlement", key="bind-1",
                         settlement_id="claim-missing" if fixture == "settlement_unknown" else "claim-1")
        if fixture in ("transferred", "closed"):
            self.command(env, "accept_resale", key="transfer-1")
        if fixture == "closed":
            self.command(env, "close", key="close-1")
        if fixture in ("cancelled", "cancelled_held"):
            if fixture == "cancelled_held":
                self.command(env, "hold_buy", key="hold-1")
            self.command(env, "cancel_listing", key="cancel-1")
        if fixture.startswith("expired"):
            self.command(env, "set_clock", key="expired-clock", now_ms=EXPIRES)
        if fixture in ("admitted_listing", "consumed_paid"):
            self.ticket_admit(tickets)
            if fixture == "consumed_paid":
                self.ticket_consume(tickets)
        return env

    def views(self, env):
        machine = env["machine"]
        state = json.loads(machine.canonical_state())
        return dict(listings=[machine.view(row["listing_id"]) for row in state["listings"]],
                    rights=[machine.view_right(row["right_id"]) for row in state["tickets"]],
                    presentations=[machine.view_presentation(row["right_id"], version=version, holder_role=holder)
                        for row in state["tickets"] for version, holder in ((1, "buyer-1"), (2, "buyer-2"))])


# Each row becomes a separately named unittest, not an opaque subtest loop.
# (command, code, valid prefix, changed arguments, expected restore error).
ROWS = []


def row(op, code, fixture="adopted", restore_error=None, **changes):
    ROWS.append((op, code, fixture, changes, restore_error))


row("set_clock", "INVALID_ID", subject="other")
row("set_clock", "CLOCK_REGRESSION", now_ms=T0 - 1)
for code, fixture in (("TICKET_NOT_ISSUED", "ticket_paid"), ("TICKET_CANCELLED", "ticket_cancelled"),
                      ("ALREADY_CONSUMED", "ticket_consumed"), ("ADMISSION_LOCKED", "ticket_admitted"),
                      ("TICKET_SOURCE_REQUIRED", "no_source")):
    row("adopt_issued", code, fixture, **(dict(reservation_id="reserve-1") if fixture == "no_source" else {}))
    row("list_resale", code, {"ticket_admitted": "adopted_admitted", "ticket_consumed": "adopted_consumed"}.get(fixture, fixture),
        restore_error=code if fixture in ("ticket_admitted", "ticket_consumed") else None,
        **(dict(reservation_id="reserve-1") if fixture == "no_source" else {}))
row("adopt_issued", "ISSUANCE_BINDING_CONFLICT", amount=PRICE + 1, primary_price=PRICE + 1)
row("adopt_issued", "ILLEGAL_TRANSITION")
row("adopt_issued", "SHOW_BINDING_CONFLICT", "fresh", resale_cap=30_000)
row("adopt_issued", "RESERVATION_BINDING_CONFLICT", "fresh", slot=1)
row("adopt_issued", "ORDER_BINDING_CONFLICT", "fresh", order_id="other-order")
row("adopt_issued", "PAYMENT_BINDING_CONFLICT", "fresh", payment_ref=SALE_PAY)
row("list_resale", "UNKNOWN_RIGHT", "unknown_right", reservation_id=None)
row("list_resale", "NOT_HOLDER", seller_role="buyer-9")
row("list_resale", "STALE_VERSION", version=2)
row("list_resale", "RIGHT_SALE_LOCKED", "listed", subject="list-2")
row("list_resale", "RESALE_POLICY_REJECTED", "policy")
row("list_resale", "RECIPIENT_IS_HOLDER", recipient_role="buyer-1")
row("list_resale", "RESALE_CAP", amount=20_001)
row("list_resale", "LISTING_WINDOW", expires_ms=T0)
row("list_resale", "LISTING_BINDING_CONFLICT", "listed", recipient_role="buyer-3")
row("list_resale", "ILLEGAL_TRANSITION", "listed")
row("list_resale", "TERMINAL_IMMUTABLE", "cancelled")
# Different reservation id on an unbound adopted right is permitted; a genuine
# conflicting bound reservation cannot name the same issuance through public APIs.
row("hold_buy", "UNKNOWN_LISTING", "adopted")
row("hold_buy", "RECIPIENT_MISMATCH", "listed", buyer_role="buyer-3")
row("hold_buy", "BUYER_HOLD_LOCKED", "held", subject="hold-2")
row("hold_buy", "HOLD_BINDING_CONFLICT", "held", buyer_role="buyer-3")
row("hold_buy", "LISTING_NOT_OPEN", "expired_listed")
row("hold_buy", "TERMINAL_IMMUTABLE", "cancelled")
row("hold_buy", "ILLEGAL_TRANSITION", "released")
row("release_hold", "UNKNOWN_HOLD", "listed")
row("release_hold", "BUYER_MISMATCH", "held", buyer_role="buyer-3")
row("release_hold", "ILLEGAL_TRANSITION", "released")
row("cancel_listing", "NOT_HOLDER", "listed", seller_role="buyer-3")
row("cancel_listing", "COMPENSATION_UNDEFINED", "paid")
row("cancel_listing", "LISTING_NOT_OPEN", "expired_listed")
row("cancel_listing", "TERMINAL_IMMUTABLE", "cancelled")
row("observe_resale_payment", "BUYER_MISMATCH", "held", buyer_role="buyer-3")
row("observe_resale_payment", "RECIPIENT_MISMATCH", "listed", buyer_role="buyer-3")
row("observe_resale_payment", "RESALE_AMOUNT_MISMATCH", "listed", amount=PRICE - 1)
row("observe_resale_payment", "PAYMENT_BINDING_CONFLICT", "listed", payment_ref=PAY)
row("observe_resale_payment", "LISTING_PAYMENT_BOUND", "paid")
row("observe_resale_payment", "LISTING_NOT_OPEN", "expired_listed")
row("observe_resale_payment", "PAYMENT_REF", "listed", payment_ref="bad")
row("bind_settlement", "SETTLEMENT_BINDING_CONFLICT", "bound", settlement_id="claim-2")
row("bind_settlement", "ILLEGAL_TRANSITION", "bound")
row("accept_resale", "ILLEGAL_TRANSITION", "listed")
row("accept_resale", "LISTING_NOT_OPEN", "expired_paid")
row("accept_resale", "TRANSFER_BINDING_CONFLICT", "transferred", listing_id="list-2")
row("accept_resale", "ALREADY_CONSUMED", "consumed_paid", restore_error="ALREADY_CONSUMED")
row("accept_resale", "ADMISSION_LOCKED", "admitted_listing", restore_error="ADMISSION_LOCKED")
row("accept_resale", "SETTLEMENT_SOURCE_REQUIRED", "bound")
for code, fixture in (("UNKNOWN_SETTLEMENT", "settlement_unknown"),
                      ("SETTLEMENT_NOT_COMMITTED", "settlement_pending"),
                      ("SETTLEMENT_AMOUNT_MISMATCH", "settlement_amount"),
                      ("SETTLEMENT_VIEW_REJECTED", "settlement_granted")):
    row("accept_resale", code, fixture)
row("close", "ILLEGAL_TRANSITION", "listed")
row("close", "TERMINAL_IMMUTABLE", "closed")
row("set_clock", "IDEMPOTENCY_CONFLICT", key="gate-clock")
row("reject_external", "EXTERNAL_UNSUPPORTED")
row("reject_external", "INVALID_ID", subject=" ")
row("restore", "INVALID_JOURNAL")

# Shared mock validation codes reachable before any lifecycle mutation. SLOT,
# unbound order/payment conflicts and adopt MOCK_INVARIANT use existing tests.
ADOPT_VALIDATION = {
    "INVALID_ID": dict(show_id=" "), "INVALID_AMOUNT": dict(amount=0),
    "RESERVATION_WINDOW": dict(expires_ms=-1), "PAYMENT_REF": dict(payment_ref="bad"),
    "CAPACITY": dict(capacity=0), "GATES_TYPE": dict(gate_roles=()),
    "GATES_EMPTY": dict(gate_roles=[]),
    "GATES_LIMIT": dict(gate_roles=[f"gate-{i}" for i in range(GATE_ROLE_LIMIT + 1)]),
    "GATES_DUPLICATE": dict(gate_roles=["gate-a", "gate-a"]),
    "POLICY_FLAG": dict(resale_allowed=1), "BPS": dict(organizer_bps=-1),
    "BPS_SUM": dict(organizer_bps=6000, platform_bps=6000),
    "PRIMARY_PRICE_MISMATCH": dict(amount=PRICE + 1),
}
for code, changes in ADOPT_VALIDATION.items():
    row("adopt_issued", code, "fresh", **changes)
for op in sorted(REPLAYABLE - {"adopt_issued"}):
    fixture = "held" if op == "release_hold" else "paid" if op == "accept_resale" else "transferred" if op == "close" else "listed"
    row(op, "INVALID_ID", fixture, key=" ") if op != "set_clock" else None
for op, changes in (("list_resale", dict(amount=object())),
                    ("observe_resale_payment", dict(amount=object()))):
    row(op, "INVALID_AMOUNT", "listed", **changes)

# Stage guards and shared validators reachable on the remaining commands.
row("set_clock", "CLOCK", now_ms=-1)
row("list_resale", "VERSION_TYPE", version=-1)
for op in ("cancel_listing", "observe_resale_payment", "bind_settlement", "accept_resale", "close"):
    row(op, "UNKNOWN_LISTING", "adopted")
for op in ("observe_resale_payment", "bind_settlement", "accept_resale"):
    row(op, "TERMINAL_IMMUTABLE", "cancelled")
row("release_hold", "TERMINAL_IMMUTABLE", "cancelled_held")
row("cancel_listing", "ILLEGAL_TRANSITION", "transferred")
row("observe_resale_payment", "ILLEGAL_TRANSITION", "transferred")
row("adopt_issued", "NOT_HOLDER", "fresh", buyer_role="buyer-9")
row("adopt_issued", "UNKNOWN_RIGHT", "fresh", subject="issue-missing")
row("adopt_issued", "UNKNOWN_RESERVATION", "fresh", reservation_id="reserve-missing")
row("list_resale", "UNKNOWN_RESERVATION", reservation_id="reserve-missing")
row("adopt_issued", "SLOT_OCCUPIED", "unbound_adopted", subject="issue-2",
    order_id="order-2", payment_ref=SALE_PAY, buyer_role="buyer-2")
# Invalid key on clock is distinct from its valid-key/invalid-subject row.
# The same row checks both boundaries without creating duplicate test names.
FAULT_ROWS = {
    "set_clock": "fresh", "list_resale": "adopted", "hold_buy": "listed",
    "release_hold": "held", "cancel_listing": "listed", "observe_resale_payment": "listed",
    "bind_settlement": "listed", "accept_resale": "paid", "close": "transferred",
}


def install_faults(cls, rows, replayable):
    def guard(self):
        self.assertEqual(set(rows), replayable - {"adopt_issued"})
    cls.test_char_fault_rows_cover_replayable_commands = guard
    for op, fixture in rows.items():
        def test(self, command=op, prefix=fixture):
            self.run_fault_row(command, prefix)
        test.__name__ = f"test_char_fault_{op}"
        test.__doc__ = "B: injected internal invariant failure; no caller-rejection rollback claim."
        setattr(cls, test.__name__, test)


def install_rows(cls, rows):
    for item in rows:
        op, code, _, _, restore_error = item
        name = f"test_{op}_{code.lower()}_leaves_no_trace"
        if hasattr(cls, name):
            raise AssertionError(f"duplicate audit row: {name}")

        def test(self, case=item):
            self.run_row(case)

        test.__name__ = name
        test.__doc__ = (f"Class A: {op} / {code}; " +
            (f"restore fails {restore_error} per contract §10.3 or §11.4 last row / §11.5."
             if restore_error else "contract §10.7 / §11.5 rejection and replay."))
        setattr(cls, name, test)


install_rows(ResaleRejectionAtomicityTests, ROWS)
install_faults(ResaleRejectionAtomicityTests, FAULT_ROWS, REPLAYABLE)

if __name__ == "__main__":
    unittest.main()
