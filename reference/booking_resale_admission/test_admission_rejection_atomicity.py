"""Admission control-machine rejection audit, MOCK_GATE_ONLY and source-informed.

Existing code assertions and seeded self-state tests are partially sufficient;
see the validation record for the per-code mapping and A/B/C findings. Shared
unbound adoption rollback tests remain in test_adopt_issued_atomicity.
"""

import json
import unittest
from unittest import mock

from admission_fsm import REPLAYABLE, AdmissionError, AdmissionMachine
from resale_fsm import ResaleMachine
from test_admission_fsm import codes, policy, settlement_at, show_kwargs
from test_resale_rejection_atomicity import (
    ADOPT_VALIDATION, ADMISSION_WINDOW_MS, AuditHarness, EXPIRES, PAY, PRICE,
    REQ, SALE_PAY, SourceStub, T0, install_faults, install_rows,
)


class AdmissionRejectionAtomicityTests(AuditHarness, unittest.TestCase):
    machine_cls = AdmissionMachine
    error_cls = AdmissionError

    def environment(self, fixture="adopted"):
        unbound = fixture.startswith("unbound") or fixture == "no_source"
        book = settlement_at("COMMITTED") if fixture.startswith("settlement_") else None
        tickets = None if unbound else self.reservation(
            fixture.removeprefix("ticket_") if fixture.startswith("ticket_") else "issued", book=book)
        ownership = None if unbound else ResaleMachine(ticket_source=tickets)
        if ownership is not None:
            ownership.set_clock("clock", idempotency_key="owner-clock", now_ms=T0)
            if not fixture.startswith("ticket_"):
                ownership.adopt_issued("issue-1", idempotency_key="owner-adopt", **self.adopt_body())
        if fixture in ("ticket_down", "clock_down", "authorize_down", "consume_down"):
            tickets = SourceStub(tickets, "down" if fixture == "ticket_down" else fixture)
        if fixture in ("ownership_down", "credential_stale", "inactive", "ownership_consumed"):
            mode = {"ownership_down": "down", "credential_stale": "stale",
                    "inactive": "inactive", "ownership_consumed": "consumed"}[fixture]
            ownership = SourceStub(ownership, mode)
        sources = dict(ticket_source=tickets, ownership_source=ownership, settlement_source=book)
        if fixture == "settlement_missing":
            sources["settlement_source"] = None
        if fixture in ("settlement_down", "settlement_granted"):
            sources["settlement_source"] = SourceStub(book, "down" if fixture == "settlement_down" else "granted")
        env = dict(machine=AdmissionMachine(**sources), sources=sources, unbound=unbound,
                   other_sources={"reservation_settlement": book} if book is not None else {})
        self.command(env, "set_clock", key="gate-clock", now_ms=T0)
        fixture = fixture.removeprefix("unbound_")
        if fixture in ("fresh", "no_source", "ticket_down", "clock_down") or fixture.startswith("ticket_"):
            return env
        self.command(env, "adopt_issued", key="adopt-1")
        if fixture in ("authorized", "consumed", "expired", "moved_after_authorize", "consume_down"):
            self.command(env, "authorize_admission", key="admit-1")
        if fixture == "consumed":
            self.command(env, "consume", key="consume-1")
        if fixture == "expired":
            self.command(env, "set_clock", key="expired-clock", now_ms=T0 + ADMISSION_WINDOW_MS)
        if fixture in ("listed", "moved", "moved_after_authorize"):
            if fixture == "moved_after_authorize":
                tickets.set_clock("clock", idempotency_key="ticket-expired", now_ms=T0 + ADMISSION_WINDOW_MS)
            ownership.list_resale("list-1", idempotency_key="list-1", right_id="issue-1", version=1,
                seller_role="buyer-1", recipient_role="buyer-2", amount=PRICE,
                expires_ms=EXPIRES, reservation_id="reserve-1")
            if fixture != "listed":
                ownership.observe_resale_payment("list-1", idempotency_key="sale-pay",
                    payment_ref=SALE_PAY, amount=PRICE, buyer_role="buyer-2")
                ownership.accept_resale("transfer-1", idempotency_key="transfer-1", listing_id="list-1")
        return env

    def views(self, env):
        machine = env["machine"]
        state = json.loads(machine.canonical_state())
        return dict(credentials=[machine.view(row["right_id"]) for row in state["credentials"]],
                    presentations=[machine.view_credential(row["right_id"], version=version, holder_role=holder)
                        for row in state["credentials"] for version, holder in ((1, "buyer-1"), (2, "buyer-2"))])

    def test_char_adopt_issued_admitted_ticket_is_not_issued(self):
        """A: §11.2 requires ISSUED; the admission-id guard is unreachable here."""
        self.run_row(("adopt_issued", "TICKET_NOT_ISSUED", "ticket_admitted", {}, None))

    def test_char_authorize_clock_skew_window(self):
        """B: §11.2 permits skew; §11.3 no-consume clause covers freshness rows.

        A delegated reservation authorization remains after the local window
        rejection. §11.5 only promises omission from this machine's journal.
        """
        env, control = self.environment(), self.environment()
        for side in (env, control):
            side["sources"]["ticket_source"].set_clock(
                "clock", idempotency_key="ticket-skew", now_ms=T0 + ADMISSION_WINDOW_MS)
        before = self.snapshot(env)
        self.reject("ADMISSION_WINDOW", lambda: self.command(env, "authorize_admission",
                    expires_ms=T0 + ADMISSION_WINDOW_MS + 1))
        after = self.snapshot(env)
        self.assertEqual(after[:4], before[:4])
        self.assertNotEqual(after[4], before[4])
        tickets = env["sources"]["ticket_source"]
        self.assertEqual(tickets.view("reserve-1")["phase"], "ADMISSION_AUTHORIZED")
        self.assertEqual(tickets.view("reserve-1")["admission_id"], "admit-1")
        self.assertEqual(control["sources"]["ticket_source"].view("reserve-1")["phase"], "ISSUED")
        self.assertEqual(self.restore_outcome(env), self.restore_outcome(control))
        # Later clocks agree locally; the delegated trace remains observable.
        for side in (env, control):
            self.command(side, "set_clock", key="later-valid", now_ms=T0 + ADMISSION_WINDOW_MS)
        self.assertEqual(env["machine"].canonical_state(), control["machine"].canonical_state())
        self.assertNotEqual(self.source_state(env), self.source_state(control))


ROWS = []


def row(op, code, fixture="adopted", restore_error=None, **changes):
    ROWS.append((op, code, fixture, changes, restore_error))


row("set_clock", "INVALID_ID", subject="other")
row("set_clock", "CLOCK_REGRESSION", now_ms=T0 - 1)
row("set_clock", "TICKET_SOURCE_UNAVAILABLE", "clock_down", now_ms=T0 + 10)
for code, fixture in (("TICKET_NOT_ISSUED", "ticket_paid"), ("TICKET_CANCELLED", "ticket_cancelled"),
                      ("TICKET_SOURCE_REQUIRED", "no_source"), ("TICKET_SOURCE_UNAVAILABLE", "ticket_down"),
                      ("ALREADY_CONSUMED", "ticket_consumed")):
    row("adopt_issued", code, fixture, **(dict(reservation_id="reserve-1") if fixture == "no_source" else {}))
row("adopt_issued", "ISSUANCE_BINDING_CONFLICT", resale_cap=30_000)
row("adopt_issued", "ILLEGAL_TRANSITION")
row("adopt_issued", "NOT_HOLDER", "fresh", buyer_role="buyer-9")
row("adopt_issued", "SHOW_BINDING_CONFLICT", "fresh", resale_cap=30_000)
row("adopt_issued", "RESERVATION_BINDING_CONFLICT", "fresh", slot=1)
row("adopt_issued", "ORDER_BINDING_CONFLICT", "fresh", order_id="other-order")
row("adopt_issued", "PAYMENT_BINDING_CONFLICT", "fresh", payment_ref=SALE_PAY)
row("authorize_admission", "UNKNOWN_RIGHT", "fresh")
row("authorize_admission", "TICKET_SOURCE_UNAVAILABLE", "authorize_down")
row("consume", "TICKET_SOURCE_UNAVAILABLE", "consume_down")
for code, dependency in (("VENUE_SOURCE_UNAVAILABLE", "VENUE_IDENTITY"),
                         ("REVOCATION_SOURCE_UNAVAILABLE", "REVOCATION"),
                         ("EXTERNAL_UNSUPPORTED", "OTHER")):
    row("authorize_admission", code, external_dependency=dependency)
    row("consume", code, "authorized", external_dependency=dependency)
for code, fixture in (("OWNERSHIP_SOURCE_UNAVAILABLE", "ownership_down"),
                      ("CREDENTIAL_STALE", "credential_stale"),
                      ("ALREADY_CONSUMED", "ownership_consumed"), ("LISTING_LOCKED", "listed"),
                      ("SETTLEMENT_SOURCE_REQUIRED", "settlement_missing"),
                      ("SETTLEMENT_SOURCE_UNAVAILABLE", "settlement_down"),
                      ("SETTLEMENT_VIEW_REJECTED", "settlement_granted")):
    row("authorize_admission", code, fixture)
row("authorize_admission", "STALE_VERSION", "moved")
row("authorize_admission", "NOT_HOLDER", holder_role="buyer-9")
row("authorize_admission", "GATE_UNKNOWN", gate_role="gate-z")
row("authorize_admission", "ADMISSION_WINDOW", expires_ms=T0 + ADMISSION_WINDOW_MS + 1)
row("authorize_admission", "ADMISSION_LOCKED", "authorized", subject="admit-2")
row("authorize_admission", "ADMISSION_BINDING_CONFLICT", "authorized", gate_role="gate-b")
row("authorize_admission", "ILLEGAL_TRANSITION", "authorized")
row("authorize_admission", "RIGHT_NOT_ACTIVE", "consumed", subject="admit-2")
row("consume", "ADMISSION_REQUIRED")
row("consume", "GATE_MISMATCH", "authorized", gate_role="gate-b")
row("consume", "ADMISSION_REQUEST_MISMATCH", "authorized", request="22" * 32)
row("consume", "ADMISSION_EXPIRED", "expired")
row("consume", "ALREADY_CONSUMED", "consumed", subject="consume-2")
row("consume", "CONSUME_BINDING_CONFLICT", "consumed", gate_role="gate-b")
row("consume", "ILLEGAL_TRANSITION", "consumed")
row("consume", "STALE_VERSION", "moved_after_authorize", restore_error="STALE_VERSION")
row("set_clock", "IDEMPOTENCY_CONFLICT", key="gate-clock")
row("reject_external", "EXTERNAL_UNSUPPORTED")
row("reject_external", "INVALID_ID", subject=" ")
row("restore", "INVALID_JOURNAL")
for code, changes in ADOPT_VALIDATION.items():
    row("adopt_issued", code, "fresh", **(dict(amount=object()) if code == "INVALID_AMOUNT" else changes))
for op in ("authorize_admission", "consume"):
    fixture = "authorized" if op == "consume" else "adopted"
    row(op, "INVALID_ID", fixture, key=" ")
    row(op, "VERSION_TYPE", fixture, version=-1)
    row(op, "ADMISSION_REQUEST", fixture, request="bad")


row("adopt_issued", "UNKNOWN_RIGHT", "fresh", subject="issue-missing")
row("adopt_issued", "UNKNOWN_RESERVATION", "fresh", reservation_id="reserve-missing")
row("adopt_issued", "SLOT_OCCUPIED", "unbound_adopted", subject="issue-2",
    order_id="order-2", payment_ref=SALE_PAY, buyer_role="buyer-2")
for code, fixture in (("OWNERSHIP_SOURCE_UNAVAILABLE", "ownership_down"),
                      ("CREDENTIAL_STALE", "credential_stale"), ("RIGHT_NOT_ACTIVE", "inactive"),
                      ("LISTING_LOCKED", "listed"), ("SETTLEMENT_SOURCE_REQUIRED", "settlement_missing"),
                      ("SETTLEMENT_SOURCE_UNAVAILABLE", "settlement_down"),
                      ("SETTLEMENT_VIEW_REJECTED", "settlement_granted")):
    row("consume", code, fixture)
row("set_clock", "CLOCK", now_ms=-1)
row("consume", "UNKNOWN_RIGHT", "fresh")
row("consume", "GATE_UNKNOWN", "authorized", gate_role="gate-z")
FAULT_ROWS = {"set_clock": "fresh", "authorize_admission": "adopted", "consume": "authorized"}

install_rows(AdmissionRejectionAtomicityTests, ROWS)
install_faults(AdmissionRejectionAtomicityTests, FAULT_ROWS, REPLAYABLE)

if __name__ == "__main__":
    unittest.main()
