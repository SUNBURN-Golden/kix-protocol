"""Source-informed parity with direct BookingSession confirmation and local boundaries."""

from copy import deepcopy
import json
import unittest
from unittest.mock import Mock, patch

from booking_quote_adapter import BookingQuoteAdapter
from booking_quote_source import BookingQuoteNotFound, BookingQuoteSourceError, InvalidBookingQuoteRecord
from booking_session import BookingInputError, BookingSession
from fake_booking_quote_source import FakeBookingQuoteSource, SyntheticBookingQuoteFault
from mock_gates import MONEY_MAX
from reservation_fsm import ReservationError, ReservationMachine
from test_booking_quote_source import record, source_for
from test_booking_session import invoke, requests, snapshot
from test_reservation_fsm import assert_not_final


def build():
    machine = ReservationMachine()
    session = BookingSession(machine)
    for row in requests()[:3]:
        invoke(session, row)
    return machine, session


def confirm(adapter, **changes):
    return adapter.confirm_recorded_quote(**(dict(recording_id="record-1", reservation_id="reserve-1",
                                                 order_id="order-1", idempotency_key="confirm-1") | changes))


def outcome(call):
    try:
        return call()
    except ReservationError as error:
        return {"error": error.code}


class BookingQuoteAdapterTests(unittest.TestCase):
    def test_exact_single_delegation_receipt_and_session_exception_identity(self):
        session = Mock(spec=BookingSession)
        source = source_for()
        adapter = BookingQuoteAdapter(session, source)
        self.assertEqual(source.calls, ())
        self.assertEqual(session.mock_calls, [])
        receipt = {"opaque": object()}
        session.confirm.return_value = receipt
        self.assertIs(confirm(adapter), receipt)
        session.confirm.assert_called_once_with("order-1", idempotency_key="confirm-1", **record())
        self.assertEqual(len(session.mock_calls), 1)
        for error in (BookingInputError("clock"), ReservationError("TEST"), RuntimeError("internal")):
            session.reset_mock()
            session.confirm.side_effect = error
            with self.assertRaises(type(error)) as caught:
                confirm(adapter)
            self.assertIs(caught.exception, error)
            self.assertEqual(len(session.mock_calls), 1)
        self.assertEqual(source.calls, ("record-1",) * 4)

    def test_histories_match_receipts_errors_state_digest_journal_after_every_step(self):
        # Cover each new adapter path, leaving underlying FSM contract tests in place.
        for name in ("booking_confirm", "booking_cancel", "booking_boundaries"):
            machine, direct_machine = ReservationMachine(), ReservationMachine()
            session, direct = BookingSession(machine), BookingSession(direct_machine)
            recordings = {}
            for i, row in enumerate(requests(name)):
                if row["operation"] == "confirm":
                    recordings[f"record-{i}"] = json.dumps({
                        k: row["arguments"][k] for k in ("reservation_id", "amount", "quote_ref")})
            source = FakeBookingQuoteSource(recordings=recordings)
            adapter = BookingQuoteAdapter(session, source)
            calls = []
            for i, row in enumerate(requests(name)):
                with self.subTest(transcript=name, line=i + 1):
                    if row["operation"] == "confirm":
                        args = row["arguments"]
                        actual = outcome(lambda: confirm(adapter, recording_id=f"record-{i}",
                                         **{k: args[k] for k in ("reservation_id", "order_id", "idempotency_key")}))
                        calls.append(f"record-{i}")
                    else:
                        actual = invoke(session, row)
                    self.assertEqual(actual, invoke(direct, row))
                    self.assertEqual(snapshot(machine), snapshot(direct_machine))
                    self.assertEqual(source.calls, tuple(calls))
                    if "error" not in actual:
                        assert_not_final(self, actual)

    def test_replay_alias_changed_quote_amount_order_and_binding_parity(self):
        machine, session = build()
        direct_machine, direct = build()
        bodies = {"record-1": record(), "alias": record(), "quote": record(quote_ref="changed"),
                  "amount": record(amount=10000)}
        source = FakeBookingQuoteSource(recordings={k: json.dumps(v) for k, v in bodies.items()})
        adapter = BookingQuoteAdapter(session, source)
        cases = [("record-1", {}, None), ("alias", {}, None),
                 ("quote", {}, "IDEMPOTENCY_CONFLICT"), ("amount", {}, "IDEMPOTENCY_CONFLICT"),
                 ("record-1", {"order_id": "other"}, "IDEMPOTENCY_CONFLICT"),
                 ("quote", {"idempotency_key": "new-quote"}, "ORDER_BINDING_CONFLICT"),
                 ("record-1", {"idempotency_key": "new-key"}, "ILLEGAL_TRANSITION")]
        first = None
        for selector, caller, code in cases:
            actual = outcome(lambda: confirm(adapter, recording_id=selector, **caller))
            expected = outcome(lambda: direct.confirm(caller.get("order_id", "order-1"),
                               idempotency_key=caller.get("idempotency_key", "confirm-1"), **bodies[selector]))
            self.assertEqual(actual, expected)
            if code:
                self.assertEqual(actual, {"error": code})
            elif first is None:
                first = deepcopy(actual)
                actual["reservation"].clear()  # returned receipt cannot corrupt replay
            self.assertEqual(snapshot(machine), snapshot(direct_machine))
        for side in (session, direct):
            side.set_clock("clock", now_ms=1900000, idempotency_key="later")
        self.assertEqual(confirm(adapter), direct.confirm("order-1", idempotency_key="confirm-1", **record()))
        for side in (session, direct):
            side.cancel("reserve-1", idempotency_key="cancel")
        self.assertEqual(confirm(adapter), first | {"duplicate": True, "applied": None})
        self.assertEqual(confirm(adapter), direct.confirm("order-1", idempotency_key="confirm-1", **record()))
        self.assertEqual(snapshot(machine), snapshot(direct_machine))
        self.assertEqual(source.calls, tuple(c[0] for c in cases) + ("record-1",) * 3)

    def test_retained_price_and_expiry_refusals_match_direct_session(self):
        for expired, expected_code in ((False, "PRIMARY_PRICE_MISMATCH"), (True, "RESERVATION_EXPIRED")):
            machine, session = build()
            direct_machine, direct = build()
            if expired:
                for side in (session, direct):
                    side.set_clock("clock", now_ms=1900000, idempotency_key="expiry")
            bad = record() if expired else record(amount=10000)
            source = source_for(bad)
            adapter = BookingQuoteAdapter(session, source)
            before = snapshot(machine)
            for _ in range(2):
                self.assertEqual(outcome(lambda: confirm(adapter)), {"error": expected_code})
                self.assertEqual(outcome(lambda: direct.confirm("order-1", idempotency_key="confirm-1", **bad)),
                                 {"error": expected_code})
                self.assertEqual(snapshot(machine), before)
                self.assertEqual(snapshot(machine), snapshot(direct_machine))
            changed = record(quote_ref="changed")
            self.assertEqual(outcome(lambda: confirm(BookingQuoteAdapter(session, source_for(changed)))),
                             {"error": "IDEMPOTENCY_CONFLICT"})
            self.assertEqual(outcome(lambda: direct.confirm("order-1", idempotency_key="confirm-1", **changed)),
                             {"error": "IDEMPOTENCY_CONFLICT"})
            self.assertEqual(snapshot(machine), snapshot(direct_machine))
            self.assertEqual(source.calls, ("record-1", "record-1"))

    def test_session_clock_prerequisite_is_preserved_without_key_binding(self):
        machine = ReservationMachine()
        session = BookingSession(machine)
        source = source_for()
        adapter = BookingQuoteAdapter(session, source)
        before = snapshot(machine)
        with self.assertRaises(BookingInputError):
            confirm(adapter)
        self.assertEqual(snapshot(machine), before)
        for row in requests()[:3]:
            invoke(session, row)
        self.assertFalse(confirm(adapter)["duplicate"])
        self.assertEqual(source.calls, ("record-1", "record-1"))

    def test_invalid_callers_refused_before_fetch_or_session_access(self):
        for field in ("recording_id", "reservation_id", "order_id", "idempotency_key"):
            for value in (None, True, 1, 1.0, [], {}, "", " bad ", "x" * 101):
                with self.subTest(field=field, value=value):
                    source, session = Mock(), Mock(spec=BookingSession)
                    with self.assertRaises(InvalidBookingQuoteRecord):
                        confirm(BookingQuoteAdapter(session, source), **{field: value})
                    self.assertEqual(source.mock_calls, [])
                    self.assertEqual(session.mock_calls, [])

    def test_invalid_record_shapes_scalars_and_binding_never_delegate_or_bind_key(self):
        valid = record()
        bad = [[], True, 1, 1.0, "text", {}, valid | {"extra": 1}]
        bad += [{k: v for k, v in valid.items() if k != field} for field in valid]
        bad += [valid | {field: v} for field in ("reservation_id", "quote_ref")
                for v in (None, True, 1, 1.0, [], {}, "", " bad ", "x" * 101)]
        bad += [valid | {"amount": v} for v in (None, True, 0, -1, MONEY_MAX + 1, 1.0, "1", [], {})]
        bad += [record(reservation_id="different")]
        for body in bad:
            with self.subTest(body=body):
                machine, session = build()
                before = snapshot(machine)
                source = Mock()
                source.fetch.return_value = body
                with patch.object(session, "confirm", wraps=session.confirm) as method:
                    with self.assertRaises(InvalidBookingQuoteRecord):
                        confirm(BookingQuoteAdapter(session, source))
                    method.assert_not_called()
                source.fetch.assert_called_once_with("record-1")
                self.assertEqual(snapshot(machine), before)
                self.assertFalse(confirm(BookingQuoteAdapter(session, source_for()))["duplicate"])
        spy = Mock(spec=BookingSession)
        confirm(BookingQuoteAdapter(spy, source_for(record(amount=MONEY_MAX))))
        self.assertEqual(spy.confirm.call_args.kwargs["amount"], MONEY_MAX)

    def test_missing_bad_json_and_faults_no_fsm_call_or_key_binding(self):
        cases = [None, "{", "[]", '{"amount":1,"amount":2}', *SyntheticBookingQuoteFault]
        for value in cases:
            machine, session = build()
            before = snapshot(machine)
            source = FakeBookingQuoteSource(recordings={} if value is None else {"record-1": value})
            with patch.object(machine, "confirm", wraps=machine.confirm) as method:
                with self.assertRaises(BookingQuoteSourceError):
                    confirm(BookingQuoteAdapter(session, source))
                method.assert_not_called()
            self.assertEqual(source.calls, ("record-1",))
            self.assertEqual(snapshot(machine), before)
            self.assertFalse(confirm(BookingQuoteAdapter(session, source_for()))["duplicate"])

    def test_source_failure_after_success_never_falls_back_to_retained_receipt(self):
        machine, session = build()
        source = Mock()
        cause = TimeoutError("synthetic")
        local = BookingQuoteSourceError("synthetic local")
        source.fetch.side_effect = [record(), None, cause, local, record()]
        adapter = BookingQuoteAdapter(session, source)
        with patch.object(session, "confirm", wraps=session.confirm) as method:
            confirm(adapter)
            before = snapshot(machine)
            with self.assertRaises(BookingQuoteNotFound):
                confirm(adapter)
            with self.assertRaises(BookingQuoteSourceError) as caught:
                confirm(adapter)
            self.assertIs(caught.exception.__cause__, cause)
            with self.assertRaises(BookingQuoteSourceError) as caught:
                confirm(adapter)
            self.assertIs(caught.exception, local)
            self.assertEqual(method.call_count, 1)
            self.assertTrue(confirm(adapter)["duplicate"])
            self.assertEqual(method.call_count, 2)
        self.assertEqual(source.fetch.call_count, 5)
        self.assertEqual(snapshot(machine), before)
