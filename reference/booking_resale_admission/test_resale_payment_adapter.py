"""Source-informed payment boundary gaps; reuse existing FSM contract evidence."""

import json
import unittest
from unittest.mock import Mock, patch

from example_resale_offer_adapter import FIXTURE_EXPIRY, FIXTURE_PRICE, build_fixture
from example_resale_payment_adapter import FIXTURE_RESALE_PAYMENT, run_example
from fake_resale_payment_source import FakeResalePaymentSource, SyntheticResalePaymentFault
from mock_gates import MONEY_MAX
from resale_fsm import ResaleError
from resale_payment_adapter import ResalePaymentAdapter
from resale_payment_source import (
    InvalidResalePaymentRecord, ResalePaymentNotFound, ResalePaymentSourceError,
)
from test_resale_fsm import assert_not_final


def record(**changes):
    return dict(listing_id="list-1", payment_ref=FIXTURE_RESALE_PAYMENT,
                amount=FIXTURE_PRICE, buyer_role="buyer-2") | changes


def source_for(body=None):
    return FakeResalePaymentSource(recordings={"record-1": json.dumps(record() if body is None else body)})


def invoke(adapter, **changes):
    caller = dict(listing_id="list-1", idempotency_key="payment-key") | changes
    return adapter.observe_resale_payment(caller.pop("recording_id", "record-1"), **caller)


def direct(machine, body=None, **changes):
    arguments = (record() if body is None else body) | dict(idempotency_key="payment-key") | changes
    return machine.observe_resale_payment(**arguments)


def snapshot(*machines):
    return tuple((m.canonical_state(), m.state_digest(), m.export_journal()) for m in machines)


def opened(*, held=False):
    tickets, machine = build_fixture()
    machine.list_resale(
        "list-1", idempotency_key="list-key", right_id="issue-1", version=1,
        seller_role="buyer-1", recipient_role="buyer-2", amount=FIXTURE_PRICE,
        expires_ms=FIXTURE_EXPIRY, reservation_id="reserve-1",
    )
    if held:
        machine.hold_buy("buy-hold", listing_id="list-1", buyer_role="buyer-2",
                         idempotency_key="hold-key")
    return tickets, machine


class NoMachineAccess:
    def __getattribute__(self, name):
        raise AssertionError(f"boundary failure accessed FSM attribute {name}")


class ResalePaymentAdapterTests(unittest.TestCase):
    def assert_code(self, code, fn):
        with self.assertRaises(ResaleError) as raised:
            fn()
        self.assertEqual(raised.exception.code, code)

    def test_exact_forwarding_receipt_and_exception_identity(self):
        machine = Mock(spec=["observe_resale_payment"])
        receipt = {"unchanged": object()}
        machine.observe_resale_payment.return_value = receipt
        source = source_for()
        adapter = ResalePaymentAdapter(machine, source)
        self.assertIs(invoke(adapter), receipt)
        body = record()
        body.pop("listing_id")
        machine.observe_resale_payment.assert_called_once_with(
            "list-1", idempotency_key="payment-key", **body)
        self.assertEqual(len(machine.mock_calls), 1)
        for error in (ResaleError("FIXTURE_ERROR"), RuntimeError("synthetic fault")):
            machine.observe_resale_payment.side_effect = error
            with self.assertRaises(type(error)) as raised:
                invoke(adapter)
            self.assertIs(raised.exception, error)
        self.assertEqual(source.calls, ("record-1",) * 3)

    def test_payment_and_replay_parity_from_listed_and_held_then_explicit_transfer(self):
        for held in (False, True):
            with self.subTest(held=held):
                tickets, machine = opened(held=held)
                other_tickets, other = opened(held=held)
                source = FakeResalePaymentSource(recordings={
                    selector: json.dumps(record()) for selector in ("record-1", "alias")
                })
                adapter = ResalePaymentAdapter(machine, source)
                before_tickets = snapshot(tickets)
                before_right = machine.view_right("issue-1")["right"]
                journal = machine.export_journal()
                first = invoke(adapter)
                self.assertEqual(first, direct(other))
                assert_not_final(self, first)
                self.assertEqual(first["listing"]["phase"], "PAYMENT_NOTED")
                self.assertIsNone(first["listing"]["settlement_id"])
                self.assertEqual(first["listing"]["settlement_gate"], "UNBOUND")
                self.assertEqual(machine.view_right("issue-1")["right"], before_right)
                self.assertEqual([r["op"] for r in machine.export_journal()[len(journal):]],
                                 ["observe_resale_payment"])
                first_copy = json.loads(json.dumps(first))
                first["listing"]["phase"] = "fake"
                first["right"]["version"] = 999
                replay = invoke(adapter, recording_id="alias")
                self.assertEqual(replay, direct(other))
                self.assertEqual(replay, first_copy | {"duplicate": True, "applied": None})
                self.assertEqual(snapshot(tickets, machine), snapshot(other_tickets, other))
                # Observation must not generate transfer; this separate request does.
                for m in (machine, other):
                    m.accept_resale("transfer", listing_id="list-1", idempotency_key="transfer-key")
                    m.close("list-1", idempotency_key="close-key")
                self.assertEqual(invoke(adapter), direct(other))
                self.assertEqual(invoke(adapter), first_copy | {"duplicate": True, "applied": None})
                self.assertEqual(machine.view("list-1")["phase"], "CLOSED")
                self.assertEqual(machine.view_right("issue-1")["right"]["version"], 2)
                self.assertEqual(snapshot(tickets), before_tickets)
                self.assertEqual(snapshot(tickets, machine), snapshot(other_tickets, other))
                self.assertEqual(source.calls, ("record-1", "alias", "record-1", "record-1"))

    def test_conflicting_observations_match_direct_fsm(self):
        tickets, machine = opened()
        other_tickets, other = opened()
        adapter = ResalePaymentAdapter(machine, source_for())
        self.assertEqual(invoke(adapter), direct(other))
        for body in (record(payment_ref="ef" * 32), record(amount=FIXTURE_PRICE - 1),
                     record(buyer_role="other"), record(listing_id="missing")):
            with self.subTest(body=body):
                adapter = ResalePaymentAdapter(machine, source_for(body))
                self.assert_code("IDEMPOTENCY_CONFLICT", lambda: invoke(adapter, listing_id=body["listing_id"]))
                self.assert_code("IDEMPOTENCY_CONFLICT", lambda: direct(other, body))
                self.assertEqual(snapshot(tickets, machine), snapshot(other_tickets, other))
                self.assertEqual(adapter._source.calls, ("record-1",))

    def test_semantic_rejections_and_retained_keys_match_direct_fsm(self):
        cases = [
            (False, record(buyer_role="wrong"), "RECIPIENT_MISMATCH"),
            (True, record(buyer_role="wrong"), "BUYER_MISMATCH"),
            (False, record(amount=FIXTURE_PRICE - 1), "RESALE_AMOUNT_MISMATCH"),
            (True, record(amount=FIXTURE_PRICE + 1), "RESALE_AMOUNT_MISMATCH"),
            (False, record(payment_ref="ab" * 32), "PAYMENT_BINDING_CONFLICT"),
            (False, record(listing_id="missing"), "UNKNOWN_LISTING"),
        ]
        for held, body, code in cases:
            with self.subTest(held=held, code=code):
                tickets, machine = opened(held=held)
                other_tickets, other = opened(held=held)
                before = snapshot(tickets, machine)
                source = source_for(body)
                adapter = ResalePaymentAdapter(machine, source)
                for _ in range(2):
                    self.assert_code(code, lambda: invoke(adapter, listing_id=body["listing_id"]))
                    self.assert_code(code, lambda: direct(other, body))
                    self.assertEqual(snapshot(tickets, machine), before)
                    self.assertEqual(snapshot(tickets, machine), snapshot(other_tickets, other))
                valid_adapter = ResalePaymentAdapter(machine, source_for())
                self.assert_code("IDEMPOTENCY_CONFLICT", lambda: invoke(valid_adapter))
                self.assert_code("IDEMPOTENCY_CONFLICT", lambda: direct(other))
                self.assertEqual(invoke(valid_adapter, idempotency_key="fresh"),
                                 direct(other, idempotency_key="fresh"))
                self.assertEqual(snapshot(tickets, machine), snapshot(other_tickets, other))
                self.assertEqual(source.calls, ("record-1",) * 2)

    def test_expiry_is_left_to_fsm_and_rejection_is_retained(self):
        tickets, machine = opened()
        other_tickets, other = opened()
        for m in (machine, other):
            m.set_clock("clock", now_ms=FIXTURE_EXPIRY, idempotency_key="expire")
        adapter = ResalePaymentAdapter(machine, source_for())
        for _ in range(2):
            self.assert_code("LISTING_NOT_OPEN", lambda: invoke(adapter))
            self.assert_code("LISTING_NOT_OPEN", lambda: direct(other))
            self.assertEqual(snapshot(tickets, machine), snapshot(other_tickets, other))
        self.assertEqual(adapter._source.calls, ("record-1",) * 2)

    def test_invalid_shapes_and_scalars_fetch_once_before_machine_access(self):
        valid = record()
        malformed = [[], "text", 1, False]
        malformed += [{k: v for k, v in valid.items() if k != field} for field in valid]
        for extra in ("idempotency_key", "recording_id", "provider", "evidence_hash", "funds_executed"):
            malformed.append(valid | {extra: "injected"})
        for field in ("listing_id", "buyer_role"):
            malformed += [valid | {field: v} for v in ("", " bad ", "x" * 101, None, True, 1, [], {})]
        malformed += [valid | {"amount": v} for v in (True, 0, -1, MONEY_MAX + 1, 1.0, "1", None, {})]
        malformed += [valid | {"payment_ref": v} for v in (
            "", "cd" * 31, "cd" * 33, "CD" * 32, "gg" * 32, " " + "cd" * 32,
            None, True, 1, [], {}, {"provider": "toss"},
        )]
        malformed.append(record(listing_id="another-listing"))
        for body in malformed:
            with self.subTest(body=body):
                source = Mock()
                source.fetch.return_value = body
                with self.assertRaises(InvalidResalePaymentRecord):
                    invoke(ResalePaymentAdapter(NoMachineAccess(), source))
                source.fetch.assert_called_once_with("record-1")
        spy = Mock(spec=["observe_resale_payment"])
        invoke(ResalePaymentAdapter(spy, source_for(record(amount=MONEY_MAX))))
        self.assertEqual(spy.observe_resale_payment.call_args.kwargs["amount"], MONEY_MAX)

    def test_invalid_callers_still_fetch_exactly_once(self):
        for field in ("recording_id", "listing_id", "idempotency_key"):
            for value in ("", " bad ", "x" * 101, None, True, 1, [], {}):
                with self.subTest(field=field, value=value):
                    source = Mock()
                    source.fetch.return_value = record()
                    with self.assertRaises(InvalidResalePaymentRecord):
                        invoke(ResalePaymentAdapter(NoMachineAccess(), source), **{field: value})
                    source.fetch.assert_called_once_with(value if field == "recording_id" else "record-1")

    def test_boundary_failures_touch_no_fsm_and_leave_key_available(self):
        cases = [None, "{", "[]", '{"x":1,"x":2}', '{"x":NaN}',
                 json.dumps(record(listing_id="different")), json.dumps(record(amount=True)),
                 json.dumps(record(buyer_role=None)), json.dumps(record(provider="injected")),
                 SyntheticResalePaymentFault.ERROR, SyntheticResalePaymentFault.TIMEOUT]
        for value in cases:
            with self.subTest(value=value):
                tickets, machine = opened()
                before = snapshot(tickets, machine)
                source = FakeResalePaymentSource(recordings={} if value is None else {"record-1": value})
                for target in (NoMachineAccess(), machine):
                    with patch.object(machine, "observe_resale_payment", wraps=machine.observe_resale_payment) as method:
                        with self.assertRaises(ResalePaymentSourceError):
                            invoke(ResalePaymentAdapter(target, source))
                        method.assert_not_called()
                    self.assertEqual(snapshot(tickets, machine), before)
                self.assertEqual(source.calls, ("record-1",) * 2)
                self.assertFalse(invoke(ResalePaymentAdapter(machine, source_for()))["duplicate"])

    def test_fetch_errors_preserve_local_error_or_wrap_cause_without_fsm_access(self):
        for cause in (TimeoutError("synthetic"), ResalePaymentSourceError("local failure")):
            with self.subTest(cause=cause):
                source = Mock()
                source.fetch.side_effect = cause
                with self.assertRaises(ResalePaymentSourceError) as raised:
                    invoke(ResalePaymentAdapter(NoMachineAccess(), source))
                if isinstance(cause, ResalePaymentSourceError):
                    self.assertIs(raised.exception, cause)
                else:
                    self.assertIs(raised.exception.__cause__, cause)
                source.fetch.assert_called_once_with("record-1")

    def test_fetch_failure_after_acceptance_has_no_receipt_cache_or_fallback(self):
        tickets, machine = opened()
        source = Mock()
        source.fetch.side_effect = [record(), None, TimeoutError("synthetic"), record()]
        adapter = ResalePaymentAdapter(machine, source)
        invoke(adapter)
        before = snapshot(tickets, machine)
        with self.assertRaises(ResalePaymentNotFound):
            invoke(adapter)
        with self.assertRaises(ResalePaymentSourceError):
            invoke(adapter)
        self.assertTrue(invoke(adapter)["duplicate"])
        self.assertEqual(snapshot(tickets, machine), before)
        self.assertEqual(source.fetch.call_count, 4)

    def test_runnable_example_pauses_then_explicitly_transfers(self):
        for held in (False, True):
            with self.subTest(held=held):
                result = run_example(hold=held)
                for key in ("payment", "paused", "transfer"):
                    assert_not_final(self, result[key])
                self.assertEqual(result["paused"]["phase"], "PAYMENT_NOTED")
                self.assertEqual(result["paused"]["current_version"], 1)
                self.assertEqual(result["transfer"]["right"]["version"], 2)
                self.assertEqual(result["source_calls"], ("payment-record-1",))


if __name__ == "__main__":
    unittest.main()
