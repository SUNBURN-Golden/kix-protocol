"""Source-informed session boundary tests using the actual local machine graph."""

import json
import unittest
from unittest.mock import Mock

from admission_fsm import AdmissionError, AdmissionMachine
from admission_session import AdmissionSession
from example_presentation_adapter import FIXTURE_AUTH_EXPIRY, FIXTURE_NOW, FIXTURE_REQUEST, build_fixture
from fake_presentation_source import FakePresentationSource, SyntheticPresentationFault
from mock_gates import NON_CLAIMS
from presentation_source import PresentationSourceError


def source():
    common = dict(right_id="issue-1", version=1, request=FIXTURE_REQUEST)
    return FakePresentationSource(recordings={
        ("authorize_admission", "ticket"): json.dumps(common | {"holder_role": "buyer-1"}),
        ("consume", "ticket"): json.dumps(common),
    })


def call(session, operation):
    if operation == "authorize_admission":
        return session.authorize_admission(
            "ticket", admission_id="entry", idempotency_key="entry-key",
            gate_role="gate-a", expires_ms=FIXTURE_AUTH_EXPIRY,
        )
    return session.consume("ticket", consume_id="consume", idempotency_key="consume-key", gate_role="gate-a")


def assert_flags(test, value):
    for key, expected in NON_CLAIMS.items():
        test.assertIs(value[key], expected, key)
    test.assertEqual(value["provenance"], "MOCK_GATE_ONLY")
    test.assertEqual(value["lifecycle_authority"], "IN_MEMORY_FSM")
    test.assertEqual(value["external_admission"], "UNSUPPORTED")
    for key in ("offline_admission", "venue_credential_reissued", "economic_finality_claimed"):
        test.assertIs(value[key], False, key)


class AdmissionSessionTests(unittest.TestCase):
    def test_actual_session_explicit_effects_first_receipt_and_current_views(self):
        book, tickets, resale, machine = build_fixture()
        presentations = source()
        session = AdmissionSession(machine, presentations)
        other_before = (book.canonical_state(), resale.canonical_state())
        first = call(session, "authorize_admission")
        self.assertEqual(session.view("issue-1")["phase"], "AUTHORIZED")
        self.assertEqual(tickets.view("reserve-1")["right"]["version"], 1)
        self.assertEqual(tickets.view("reserve-1")["phase"], "ADMISSION_AUTHORIZED")
        consumed = call(session, "consume")
        journal = machine.export_journal(), tickets.export_journal()
        duplicate = call(session, "consume")
        self.assertEqual(duplicate, consumed | {"duplicate": True, "applied": None})
        self.assertEqual((machine.export_journal(), tickets.export_journal()), journal)
        replay = call(session, "authorize_admission")
        self.assertEqual(replay, first | {"duplicate": True, "applied": None})
        self.assertEqual(replay["credential"]["phase"], "AUTHORIZED")
        view = session.view("issue-1")
        current = session.view_credential("issue-1", version=1, holder_role="buyer-1")
        self.assertEqual(view["phase"], "CONSUMED")
        self.assertEqual(view["version"], 2)
        self.assertFalse(current["presentation"]["fresh"])
        for result in (first, consumed, duplicate, replay, view, current):
            assert_flags(self, result)
            if "credential" in result:
                assert_flags(self, result["credential"])
        self.assertEqual((book.canonical_state(), resale.canonical_state()), other_before)
        self.assertEqual(len(presentations.calls), 4)  # views fetch no presentation

    def test_consume_does_not_authorize_and_fault_never_uses_cached_receipt(self):
        for operation in ("authorize_admission", "consume"):
            with self.subTest(operation=operation):
                book, tickets, resale, machine = build_fixture()
                if operation == "consume":
                    session = AdmissionSession(machine, source())
                    with self.assertRaises(AdmissionError) as caught:
                        call(session, operation)
                    self.assertEqual(caught.exception.code, "ADMISSION_REQUIRED")
                    self.assertEqual(session.view("issue-1")["phase"], "ELIGIBLE")
                    call(session, "authorize_admission")
                    # Use a fresh key after the intentionally retained first rejection.
                    operation_id = "fresh-consume"
                else:
                    operation_id = "entry"
                recordings = source()
                broken = Mock()
                broken.fetch.side_effect = [recordings.fetch("ticket", operation=operation),
                                            PresentationSourceError("synthetic")]
                spy = Mock(wraps=machine)
                session = AdmissionSession(spy, broken)
                def invoke():
                    if operation == "consume":
                        return session.consume("ticket", consume_id=operation_id,
                                               idempotency_key=operation_id, gate_role="gate-a")
                    return call(session, operation)
                invoke()
                before = tuple(m.canonical_state() for m in (book, tickets, resale, machine))
                spy.reset_mock()
                with self.assertRaises(PresentationSourceError):
                    invoke()
                self.assertEqual(spy.mock_calls, [])
                self.assertEqual(broken.fetch.call_count, 2)
                self.assertEqual(tuple(m.canonical_state() for m in (book, tickets, resale, machine)), before)

    def test_presentation_faults_fetch_once_without_any_machine_access(self):
        for operation in ("authorize_admission", "consume"):
            for fault in SyntheticPresentationFault:
                with self.subTest(operation=operation, fault=fault):
                    machine = Mock()
                    presentations = FakePresentationSource(recordings={(operation, "ticket"): fault})
                    with self.assertRaises(PresentationSourceError):
                        call(AdmissionSession(machine, presentations), operation)
                    self.assertEqual(presentations.calls, ((operation, "ticket"),))
                    self.assertEqual(machine.mock_calls, [])

    def test_each_configured_authority_fault_has_one_failed_read_and_no_followup(self):
        for operation in ("authorize_admission", "consume"):
            for authority, method, code in (
                ("ticket_source", "view", "TICKET_SOURCE_UNAVAILABLE"),
                ("ownership_source", "view_right", "OWNERSHIP_SOURCE_UNAVAILABLE"),
                ("settlement_source", "view", "SETTLEMENT_SOURCE_UNAVAILABLE"),
            ):
                with self.subTest(operation=operation, authority=authority):
                    book, tickets, resale, original = build_fixture()
                    if operation == "consume":
                        call(AdmissionSession(original, source()), "authorize_admission")
                    sources = {"ticket_source": Mock(wraps=tickets),
                               "ownership_source": Mock(wraps=resale),
                               "settlement_source": Mock(wraps=book)}
                    machine = AdmissionMachine.restore(original.export_journal(), **sources)
                    for proxy in sources.values():
                        proxy.reset_mock()
                    failing = getattr(sources[authority], method)
                    failing.side_effect = TimeoutError("synthetic authority fault")
                    spy = Mock(wraps=machine)
                    presentations = source()
                    before = tuple(m.canonical_state() for m in (book, tickets, resale, machine))
                    with self.assertRaises(AdmissionError) as caught:
                        call(AdmissionSession(spy, presentations), operation)
                    self.assertEqual(caught.exception.code, code)
                    self.assertEqual(failing.call_count, 1)
                    self.assertEqual(len(spy.mock_calls), 1)
                    self.assertEqual(spy.mock_calls[0][0], operation)
                    self.assertEqual(presentations.calls, ((operation, "ticket"),))
                    sources["ticket_source"].authorize_admission.assert_not_called()
                    sources["ticket_source"].consume.assert_not_called()
                    self.assertEqual(tuple(m.canonical_state() for m in (book, tickets, resale, machine)), before)

    def test_clock_delegates_to_reservation_without_advancing_resale(self):
        book, tickets, resale, machine = build_fixture()
        before = book.canonical_state(), resale.canonical_state()
        presentations = source()
        receipt = AdmissionSession(machine, presentations).set_clock(
            "clock", idempotency_key="session-clock", now_ms=FIXTURE_NOW + 1)
        self.assertEqual(receipt["logical_time_ms"], FIXTURE_NOW + 1)
        self.assertEqual(json.loads(tickets.canonical_state())["logical_time_ms"], FIXTURE_NOW + 1)
        self.assertEqual((book.canonical_state(), resale.canonical_state()), before)
        self.assertEqual(presentations.calls, ())

    def test_direct_delegation_preserves_return_and_exception_identity(self):
        for name, arguments in (
            ("view", dict(right_id="right")),
            ("view_credential", dict(right_id="right", version=1, holder_role="holder")),
            ("set_clock", dict(subject_id="clock", idempotency_key="key", now_ms=42)),
            ("authorize_admission", dict(presentation_id="ticket", admission_id="entry",
                                        idempotency_key="key", gate_role="gate-a", expires_ms=42)),
            ("consume", dict(presentation_id="ticket", consume_id="consume",
                             idempotency_key="key", gate_role="gate-a")),
        ):
            with self.subTest(name=name):
                machine = Mock()
                session = AdmissionSession(machine, source())
                method = getattr(machine, name)
                receipt = {"opaque": object()}
                method.return_value = receipt
                self.assertIs(getattr(session, name)(**arguments), receipt)
                self.assertEqual(len(machine.mock_calls), 1)
                error = AdmissionError("SYNTHETIC")
                method.side_effect = error
                with self.assertRaises(AdmissionError) as caught:
                    getattr(session, name)(**arguments)
                self.assertIs(caught.exception, error)
                self.assertEqual(len(machine.mock_calls), 2)
