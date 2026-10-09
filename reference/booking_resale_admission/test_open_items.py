"""Draft 0.2 keeps the adopted mock boundary unfilled.

JunTae adopted option A on 2026-10-09. Policy numbers stay UNDETERMINED.
Existing suites already cover price mismatch, the offer-window fixture,
compensation refusal, face-value seller_due, generation 1, and the
protocol_contract command count. This module checks the adoption table
against that behavior and the command names this revision does not add.
"""

import inspect
import json
import unittest
from pathlib import Path

import test_admission_fsm
import test_mock_gates
import test_resale_fsm
import test_reservation_fsm
from admission_fsm import AdmissionError, AdmissionMachine
from mock_gates import (
    ADMISSION_WINDOW_MS,
    NON_CLAIMS,
    OFFER_WINDOW_MS,
    GateError,
    MockGates,
)
from open_items import (
    ADOPTED_OPTION,
    ADOPTION_DATE,
    ADOPTION_DECIDER,
    CONTRACT_VERSION,
    FORBIDDEN_COMMANDS,
    ITEMS,
    MOCK_BOUNDARY,
    POLICY_NUMBER_STATUS,
    REVISION,
    forbidden_commands,
    item,
)
from reservation_fsm import ReservationError, ReservationMachine
from resale_fsm import ResaleError, ResaleMachine

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "contracts" / "BOOKING_RESALE_ADMISSION_GATES.md"
PROTOCOL = ROOT / "reference" / "v0.3-rc1" / "protocol_contract.json"
OPENAPI = ROOT / "docs" / "contracts" / "openapi" / "kix-protocol.contract-only.openapi.json"
FSM = ROOT / "docs" / "contracts" / "openapi" / "fsm-command-contract.json"
PAY = "ab" * 32

SURFACES = (MockGates, ReservationMachine, ResaleMachine, AdmissionMachine)
CITED = {
    "test_mock_gates": test_mock_gates,
    "test_reservation_fsm": test_reservation_fsm,
    "test_resale_fsm": test_resale_fsm,
    "test_admission_fsm": test_admission_fsm,
}


def codes(fn):
    try:
        fn()
    except GateError as error:
        return error.code
    raise AssertionError("expected GateError")


class OpenItemDraftTests(unittest.TestCase):
    def test_revision_is_unfilled_and_named_in_the_contract(self):
        text = CONTRACT.read_text(encoding="utf-8")
        section = text.split("## 7. 초안 0.2", 1)[1].split("## 8. 비청구", 1)[0]
        self.assertEqual(REVISION, "BRA-OPEN-ITEMS-DRAFT-0.2")
        self.assertEqual(CONTRACT_VERSION, "0.2")
        self.assertEqual(MOCK_BOUNDARY, "UNFILLED")
        self.assertEqual(ADOPTED_OPTION, "A")
        self.assertEqual(ADOPTION_DECIDER, "JunTae")
        self.assertEqual(ADOPTION_DATE, "2026-10-09")
        self.assertEqual(POLICY_NUMBER_STATUS, "UNDETERMINED")
        self.assertIn(REVISION, text)
        self.assertIn("계약 버전 `0.2`", text)
        self.assertIn("2026-10-09 소유자 결정(JunTae)이 선택지 A를 목 경계로 채택했다", text)
        self.assertNotIn("DECISION_REQUIRED", section)
        self.assertEqual(
            [row["id"] for row in ITEMS],
            [
                "actor-authentication-revocation",
                "durable-show-config",
                "approved-reservation-ttl",
                "discounts-and-coupons",
                "payment-attesters-authority",
                "compensation-after-payment-fact",
                "resale-failure-compensation-seller-payout",
                "refund-revoke-shield-gift-cancel-show",
                "consume-private-delegated-sessions",
            ],
        )
        for row in ITEMS:
            self.assertIn("`%s`" % row["id"], text)
            self.assertIsNone(row["decided_value"])
            self.assertEqual(row["mock_boundary"], "UNFILLED")
            self.assertEqual(row["adopted_option"], "A")
            self.assertEqual(row["adoption_decider"], "JunTae")
            self.assertEqual(row["adoption_date"], "2026-10-09")
            self.assertEqual(row["policy_number_status"], "UNDETERMINED")
            self.assertEqual(row["recommendation"], "A")
            self.assertEqual(set(row["options"]), {"A", "B", "C"})
            self.assertNotIn("decided_value", row["options"]["A"])
            for pending in row["undetermined"]:
                self.assertEqual(pending["status"], "UNDETERMINED")
                self.assertGreater(len(pending["owner"].strip()), 0)
                self.assertIn(pending["owner"], text)
        self.assertEqual(item("durable-show-config")["undetermined"], ())

    def test_cited_tests_exist_and_fixtures_are_not_approvals(self):
        for row in ITEMS:
            for ref in row["covered_by"]:
                module_name, class_name, method_name = ref.split(".")
                owner = getattr(CITED[module_name], class_name)
                self.assertTrue(callable(getattr(owner, method_name)))
        ttl = item("approved-reservation-ttl")["observed_fixture"]
        self.assertEqual(ttl["reservation_window_ms"], 900_000)
        self.assertEqual(ttl["admission_window_ms"], 120_000)
        self.assertEqual(OFFER_WINDOW_MS, ttl["reservation_window_ms"])
        self.assertEqual(ADMISSION_WINDOW_MS, ttl["admission_window_ms"])
        self.assertIs(ttl["approved"], False)
        self.assertIs(item("payment-attesters-authority")["observed_fixture"]["register_show_accepts_payment_attesters"], False)
        self.assertIs(item("resale-failure-compensation-seller-payout")["observed_fixture"]["seller_due_is_payout"], False)
        self.assertEqual(item("refund-revoke-shield-gift-cancel-show")["observed_fixture"]["generation"], 1)
        for name, value in NON_CLAIMS.items():
            self.assertIs(value, False)
            if any(name in row["non_claim_flags"] for row in ITEMS):
                self.assertIn(name, CONTRACT.read_text(encoding="utf-8"))

    def test_command_surface_does_not_grow(self):
        names = forbidden_commands()
        self.assertEqual(names, FORBIDDEN_COMMANDS)
        for surface in SURFACES:
            public = {name for name in dir(surface) if not name.startswith("_")}
            self.assertTrue(names.isdisjoint(public), surface.__name__)
        catalogue = json.loads(PROTOCOL.read_text(encoding="utf-8"))
        self.assertEqual(len(catalogue["commands"]), 40)
        self.assertTrue(names.isdisjoint(catalogue["commands"]))
        openapi = json.loads(OPENAPI.read_text(encoding="utf-8"))
        fsm = json.loads(FSM.read_text(encoding="utf-8"))
        wire = set(openapi["x-kix-action-body-map"])
        for machine, body in fsm["machines"].items():
            for op in body["replayable"]:
                wire.add(op)
                wire.add("%s_%s" % (machine, op))
        self.assertTrue(names.isdisjoint(wire))
        self.assertNotIn("payment_attesters", inspect.signature(MockGates.register_show).parameters)

    def test_live_refusals_match_the_unfilled_table(self):
        gate = MockGates()
        gate.set_clock(1_000_000)
        registered = gate.register_show(
            "show-1",
            organizer_role="organizer",
            capacity=2,
            gate_roles=["gate-a"],
            primary_price=10_001,
            resale_cap=20_000,
            resale_allowed=True,
            organizer_bps=1,
            platform_bps=1,
        )
        for row in ITEMS:
            for flag in row["non_claim_flags"]:
                self.assertIs(registered[flag], False)
        with self.assertRaises(TypeError):
            gate.register_show(
                "show-2",
                organizer_role="organizer",
                capacity=1,
                gate_roles=["gate-a"],
                primary_price=10_001,
                resale_cap=20_000,
                resale_allowed=True,
                organizer_bps=0,
                platform_bps=0,
                payment_attesters=("attester",),
            )
        self.assertEqual(
            codes(lambda: gate.reserve_slot(
                "reserve-window",
                show_id="show-1",
                slot=0,
                buyer_role="buyer-1",
                expires_ms=1_000_000 + OFFER_WINDOW_MS + 1,
            )),
            "RESERVATION_WINDOW",
        )
        self.assertIn("RESERVATION_WINDOW", item("approved-reservation-ttl")["current_refusal"])
        gate.reserve_slot(
            "reserve-1",
            show_id="show-1",
            slot=0,
            buyer_role="buyer-1",
            expires_ms=1_000_000 + OFFER_WINDOW_MS,
        )
        self.assertEqual(
            codes(lambda: gate.bind_order("order-1", reservation_id="reserve-1", amount=10_000)),
            "PRIMARY_PRICE_MISMATCH",
        )
        self.assertEqual(item("discounts-and-coupons")["current_refusal"], ("PRIMARY_PRICE_MISMATCH",))
        gate.bind_order("order-1", reservation_id="reserve-1", amount=10_001)
        gate.observe_payment_fact(PAY, order_id="order-1", amount=10_001)
        self.assertEqual(codes(lambda: gate.abort_order("order-1")), "COMPENSATION_UNDEFINED")
        self.assertIn("COMPENSATION_UNDEFINED", item("compensation-after-payment-fact")["current_refusal"])
        self.assertIs(gate.view_show("show-1")["compensation_defined"], False)
        self.assertIs(gate.view_show("show-1")["funds_executed"], False)

        reservation = ReservationMachine()
        resale = ResaleMachine()
        admission = AdmissionMachine()
        labels = (
            "authenticate",
            "revoke",
            "refund",
            "shield",
            "gift",
            "cancel_show",
            "consume_private",
            "delegate_session",
        )
        for label in labels:
            with self.assertRaises(ReservationError) as reservation_error:
                reservation.reject_external(label)
            self.assertEqual(reservation_error.exception.code, "EXTERNAL_UNSUPPORTED")
            with self.assertRaises(ResaleError) as resale_error:
                resale.reject_external(label)
            self.assertEqual(resale_error.exception.code, "EXTERNAL_UNSUPPORTED")
            with self.assertRaises(AdmissionError) as admission_error:
                admission.reject_external(label)
            self.assertEqual(admission_error.exception.code, "EXTERNAL_UNSUPPORTED")
        self.assertEqual(reservation.export_journal(), [])
        self.assertEqual(resale.export_journal(), [])
        self.assertEqual(admission.export_journal(), [])
