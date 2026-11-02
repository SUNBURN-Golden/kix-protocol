"""Source-informed boundary gaps from the booking desk validation coverage map."""

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from booking_session import BookingInputError, BookingSession
from mock_gates import CAPACITY_MAX, GATE_ROLE_LIMIT, OFFER_WINDOW_MS
from reservation_fsm import ReservationError, ReservationMachine
from test_reservation_fsm import assert_not_final

HERE = Path(__file__).resolve().parent


def requests(name="booking_confirm"):
    return [json.loads(line) for line in (HERE / "fixtures" / f"{name}.jsonl").read_text().splitlines()]


def snapshot(machine):
    return machine.canonical_state(), machine.state_digest(), machine.export_journal()


def invoke(target, request):
    try:
        return getattr(target, request["operation"])(**request["arguments"])
    except ReservationError as error:
        return {"error": error.code}


class BookingSessionTests(unittest.TestCase):
    def test_actual_machine_histories_match_direct_receipts_errors_state_digest_and_journal(self):
        for name in ("booking_confirm", "booking_cancel", "booking_boundaries"):
            with self.subTest(transcript=name):
                wrapped, direct = ReservationMachine(), ReservationMachine()
                session = BookingSession(wrapped)
                for index, request in enumerate(requests(name)):
                    with self.subTest(line=index + 1):
                        result = invoke(session, request)
                        self.assertEqual(result, invoke(direct, request))
                        self.assertEqual(snapshot(wrapped), snapshot(direct))
                        if "error" not in result:
                            assert_not_final(self, result)

    def test_only_one_requested_call_with_exact_arguments_and_unchanged_receipt_or_error(self):
        # Every allowed method, including local prerequisites, forwards exactly once.
        rows = requests("booking_boundaries")
        examples = {row["operation"]: row for row in rows}
        examples["view"] = requests()[4]
        examples["reconcile"] = requests("booking_reconcile")[4]
        for operation, row in examples.items():
            machine = Mock(spec=ReservationMachine)
            session = BookingSession(machine)
            machine.assert_not_called()
            self.assertEqual(machine.mock_calls, [])
            session.set_clock("clock", now_ms=7, idempotency_key="explicit-init")
            machine.reset_mock()
            expected = {"untouched": operation}
            method = getattr(machine, operation)
            method.return_value = expected
            args = deepcopy(row["arguments"])
            original = deepcopy(args)
            self.assertIs(getattr(session, operation)(**args), expected)
            self.assertEqual(args, original)
            identity = {"set_clock": "subject_id", "register_show": "show_id", "hold": "reservation_id",
                        "confirm": "order_id", "view_show": "show_id"}.get(operation, "reservation_id")
            subject = args.pop(identity)
            method.assert_called_once_with(subject, **args)
            self.assertEqual(len(machine.mock_calls), 1)
            error = ReservationError("SYNTHETIC_TEST_FAILURE")
            method.side_effect = error
            machine.reset_mock()
            with self.assertRaises(ReservationError) as caught:
                getattr(session, operation)(**original)
            self.assertIs(caught.exception, error)
            self.assertEqual(len(machine.mock_calls), 1)

    def test_clock_requires_success_through_this_session_and_local_failure_binds_no_key(self):
        machine = ReservationMachine()
        machine.set_clock("clock", now_ms=7, idempotency_key="outside-clock")
        session = BookingSession(machine)
        before = snapshot(machine)
        for row in requests("booking_boundaries"):
            if row["operation"] not in ("set_clock", "view", "view_show"):
                with self.assertRaises(BookingInputError):
                    getattr(session, row["operation"])(**row["arguments"])
                self.assertEqual(snapshot(machine), before)
        with self.assertRaises(ReservationError):
            session.set_clock("wrong", now_ms=7, idempotency_key="failed-clock")
        with self.assertRaises(BookingInputError):
            session.register_show(**requests()[1]["arguments"])
        session.set_clock("clock", now_ms=7, idempotency_key="outside-clock")  # explicit replay counts
        session.register_show(**requests()[1]["arguments"])  # previously local-rejected key is free
        self.assertEqual(machine.view_show("show-1")["logical_time_ms"], 7)
        session.set_clock("clock", now_ms=8, idempotency_key="later-clock")
        with self.assertRaises(ReservationError):
            session.set_clock("clock", now_ms=6, idempotency_key="regression")
        # A failed update doesn't undo initialization; expiry is explicit for this clock.
        session.hold(**(requests()[2]["arguments"] | {"expires_ms": 900008}))

    def test_quote_mandatory_valid_identifier_and_rejection_does_not_bind_key(self):
        for quote in (None, "", " bad ", "x" * 101, [], True, 1):
            machine = ReservationMachine()
            session = BookingSession(machine)
            for row in requests()[:3]:
                invoke(session, row)
            before = snapshot(machine)
            args = requests()[3]["arguments"]
            with self.subTest(quote=quote), self.assertRaises(BookingInputError):
                session.confirm(**(args | {"quote_ref": quote}))
            self.assertEqual(snapshot(machine), before)
            result = session.confirm(**args)
            self.assertEqual(result["reservation"]["phase"], "CONFIRMED")
        with self.assertRaises(TypeError):
            session.confirm("order-missing", reservation_id="reserve-1", amount=10001,
                            idempotency_key="missing-quote")

    def test_fixture_limits_and_invalid_values_remain_fsm_owned(self):
        variants = [requests()[1] | {"arguments": requests()[1]["arguments"] | change}
                    for change in ({"capacity": CAPACITY_MAX + 1}, {"capacity": True},
                                   {"gate_roles": [f"gate-{n}" for n in range(GATE_ROLE_LIMIT + 1)]},
                                   {"primary_price": True}, {"resale_allowed": 1},
                                   {"organizer_bps": 10001}, {"organizer_role": None})]
        variants += [requests()[2] | {"arguments": requests()[2]["arguments"] | change}
                     for change in ({"expires_ms": 1000000 + OFFER_WINDOW_MS + 1},
                                    {"slot": True}, {"buyer_role": None}, {"idempotency_key": None})]
        for row in variants:
            with self.subTest(row=row):
                wrapped, direct = ReservationMachine(), ReservationMachine()
                session = BookingSession(wrapped)
                for setup in requests()[:2 if row["operation"] == "hold" else 1]:
                    self.assertEqual(invoke(session, setup), invoke(direct, setup))
                result = invoke(session, row)
                self.assertIn("error", result)
                self.assertEqual(result, invoke(direct, row))
                self.assertEqual(snapshot(wrapped), snapshot(direct))

    def test_views_without_session_clock_are_nonmutating_and_detached(self):
        machine = ReservationMachine()
        for row in requests()[:4]:
            invoke(machine, row)
        session = BookingSession(machine)
        before = snapshot(machine)
        view = session.view("reserve-1")
        show = session.view_show("show-1")
        view["phase"] = "corrupt"
        show.clear()
        self.assertEqual(snapshot(machine), before)
        self.assertEqual(session.view("reserve-1")["phase"], "CONFIRMED")
        for field in ("payment_ref", "issuance_id", "settlement_id", "right"):
            self.assertIsNone(session.view("reserve-1")[field])
        self.assertEqual(machine.export_journal()[-1]["op"], "confirm")

    def test_reconciliation_matches_direct_fsm_and_preserves_business_state(self):
        from test_ticket_operations_session import check_reconcile_history
        machine, direct = ReservationMachine(), ReservationMachine()
        session = BookingSession(machine)
        results = check_reconcile_history(
            self, requests('booking_reconcile'), (machine,), (direct,),
            lambda row: getattr(session, row['operation'])(**row['arguments']),
            lambda row: getattr(direct, row['operation'])(**row['arguments']))
        self.assertEqual(results[6]['reservation']['phase'], 'CONFIRMED')
        self.assertEqual(results[7]['phase'], 'CANCELLED')
        self.assertNotEqual(results[6]['state_digest'], machine.state_digest())

    def test_reconcile_requires_no_session_clock_and_forwards_opaque_values_once(self):
        machine = ReservationMachine()
        for row in requests()[:4]:
            invoke(machine, row)
        before = snapshot(machine)
        session = BookingSession(machine)  # clock initialized outside this session
        self.assertTrue(session.reconcile('reserve-1', idempotency_key='recon')['matched'])
        self.assertEqual(snapshot(machine), before)
        with self.assertRaises(BookingInputError):
            session.cancel('reserve-1', idempotency_key='cancel')
        spy = Mock(spec=ReservationMachine)
        subject, key = object(), object()
        receipt = {'opaque': object()}
        spy.reconcile.return_value = receipt
        self.assertIs(BookingSession(spy).reconcile(subject, idempotency_key=key), receipt)
        spy.reconcile.assert_called_once_with(subject, idempotency_key=key)
        self.assertEqual(len(spy.mock_calls), 1)
        spy.reset_mock()
        error = RuntimeError('unexpected failure')
        spy.reconcile.side_effect = error
        with self.assertRaises(RuntimeError) as caught:
            BookingSession(spy).reconcile(subject, idempotency_key=key)
        self.assertIs(caught.exception, error)
        spy.reconcile.assert_called_once_with(subject, idempotency_key=key)
