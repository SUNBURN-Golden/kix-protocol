"""Source-informed boundary/parity gaps; existing FSM lifecycle audits are reused."""

import json
import unittest
from unittest.mock import Mock, patch

from example_resale_offer_adapter import (
    FIXTURE_EXPIRY, FIXTURE_NOW, FIXTURE_PRICE, build_fixture, run_example,
)
from fake_resale_offer_source import FakeResaleOfferSource, SyntheticResaleOfferFault
from mock_gates import ADMISSION_WINDOW_MS, CLOCK_MAX, MONEY_MAX
from resale_fsm import ResaleError
from resale_offer_adapter import ResaleOfferAdapter
from resale_offer_source import (
    InvalidResaleOfferRecord, ResaleOfferNotFound, ResaleOfferSourceError,
)
from test_resale_fsm import assert_not_final


def record(**changes):
    return dict(offer_id="offer-1", right_id="issue-1", version=1,
                seller_role="buyer-1", recipient_role="buyer-2", amount=FIXTURE_PRICE,
                expires_ms=FIXTURE_EXPIRY, reservation_id="reserve-1") | changes


def source_for(body=None):
    body = record() if body is None else body
    return FakeResaleOfferSource(recordings={body["offer_id"]: json.dumps(body)})


def invoke(adapter, **changes):
    caller = dict(listing_id="list-1", idempotency_key="list-key") | changes
    return adapter.list_resale(caller.pop("offer_id", "offer-1"), **caller)


def direct(machine, body=None, **changes):
    body = dict(record() if body is None else body)
    body.pop("offer_id")
    return machine.list_resale(**(dict(listing_id="list-1", idempotency_key="list-key")
                                  | changes | body))


def snapshot(*machines):
    return tuple((machine.canonical_state(), machine.state_digest(), machine.export_journal())
                 for machine in machines)


class NoMachineAccess:
    def __getattribute__(self, name):
        raise AssertionError(f"boundary failure accessed FSM attribute {name}")


class ResaleOfferAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tickets, self.machine = build_fixture()

    def assert_code(self, code, fn):
        with self.assertRaises(ResaleError) as raised:
            fn()
        self.assertEqual(raised.exception.code, code)

    def test_exact_forwarding_and_receipt_and_error_identity(self):
        machine = Mock(spec=["list_resale"])
        receipt = {"receipt": object()}
        machine.list_resale.return_value = receipt
        source = source_for()
        adapter = ResaleOfferAdapter(machine, source)
        self.assertIs(invoke(adapter), receipt)
        body = record()
        body.pop("offer_id")
        machine.list_resale.assert_called_once_with("list-1", idempotency_key="list-key", **body)
        self.assertEqual(len(machine.mock_calls), 1)
        for error in (ResaleError("FIXTURE_ERROR"), RuntimeError("synthetic internal fault")):
            machine.list_resale.side_effect = error
            with self.assertRaises(type(error)) as raised:
                invoke(adapter)
            self.assertIs(raised.exception, error)
        self.assertEqual(source.calls, ("offer-1",) * 3)

    def test_accepted_replay_key_conflict_competing_and_expired_replay_parity(self):
        tickets, machine = build_fixture()
        source = FakeResaleOfferSource(recordings={
            selector: json.dumps(record(offer_id=selector))
            for selector in ("offer-1", "same-input")
        })
        adapter = ResaleOfferAdapter(self.machine, source)
        tickets_before = snapshot(self.tickets)
        first = invoke(adapter)
        self.assertEqual(first, direct(machine))
        assert_not_final(self, first)
        self.assertFalse(first["duplicate"])
        self.assertEqual(snapshot(self.tickets, self.machine), snapshot(tickets, machine))
        first_copy = json.loads(json.dumps(first))
        first["listing"]["amount"] = 999
        replay = invoke(adapter, offer_id="same-input")
        self.assertEqual(replay, direct(machine))
        self.assertEqual(replay, first_copy | {"duplicate": True, "applied": None})
        for code, caller in (
            ("IDEMPOTENCY_CONFLICT", dict(listing_id="list-2")),
            ("RIGHT_SALE_LOCKED", dict(listing_id="list-2", idempotency_key="competing")),
        ):
            self.assert_code(code, lambda: invoke(adapter, **caller))
            self.assert_code(code, lambda: direct(machine, **caller))
            self.assertEqual(snapshot(self.tickets, self.machine), snapshot(tickets, machine))
        for resale in (self.machine, machine):
            resale.set_clock("clock", idempotency_key="later", now_ms=FIXTURE_EXPIRY)
        self.assertEqual(invoke(adapter), direct(machine))
        self.assertEqual(invoke(adapter), first_copy | {"duplicate": True, "applied": None})
        self.assertEqual(snapshot(self.tickets, self.machine), snapshot(tickets, machine))
        self.assertEqual(snapshot(self.tickets), tickets_before)
        self.assertEqual(source.calls, ("offer-1", "same-input") + ("offer-1",) * 4)

    def test_rejected_offers_match_direct_errors_states_digests_and_journals(self):
        cases = [
            ("NOT_HOLDER", dict(seller_role="buyer-9")),
            ("STALE_VERSION", dict(version=2)),
            ("STALE_VERSION", dict(version=0)),
            ("RESALE_CAP", dict(amount=20_001)),
            ("LISTING_WINDOW", dict(expires_ms=FIXTURE_NOW)),
            ("LISTING_WINDOW", dict(expires_ms=0)),
            ("LISTING_WINDOW", dict(expires_ms=FIXTURE_EXPIRY + 1)),
            ("RECIPIENT_IS_HOLDER", dict(recipient_role="buyer-1")),
            ("UNKNOWN_RESERVATION", dict(reservation_id="missing")),
        ]
        for code, change in cases:
            with self.subTest(code=code, change=change):
                tickets, machine = build_fixture()
                adapted_tickets, adapted = build_fixture()
                before = snapshot(adapted_tickets, adapted)
                source = source_for(record(**change))
                adapter = ResaleOfferAdapter(adapted, source)
                for _ in range(2):
                    self.assert_code(code, lambda: invoke(adapter))
                    self.assert_code(code, lambda: direct(machine, record(**change)))
                    self.assertEqual(snapshot(adapted_tickets, adapted), before)
                    self.assertEqual(snapshot(adapted_tickets, adapted), snapshot(tickets, machine))
                # A serializable FSM rejection retains its key even though it is unjournaled.
                self.assert_code("IDEMPOTENCY_CONFLICT", lambda: invoke(
                    ResaleOfferAdapter(adapted, source_for())))
                self.assert_code("IDEMPOTENCY_CONFLICT", lambda: direct(machine))
                self.assertEqual(source.calls, ("offer-1", "offer-1"))
                self.assertEqual(snapshot(adapted_tickets, adapted), snapshot(tickets, machine))

    def test_admission_lock_and_retained_refusal_after_lock_expiry_parity(self):
        tickets, machine = build_fixture()
        for book in (self.tickets, tickets):
            book.authorize_admission(
                "admit-1", idempotency_key="admit", right_id="issue-1", version=1,
                holder_role="buyer-1", gate_role="gate-a", request="11" * 32,
                expires_ms=FIXTURE_NOW + ADMISSION_WINDOW_MS,
            )
        source = source_for()
        adapter = ResaleOfferAdapter(self.machine, source)
        self.assert_code("ADMISSION_LOCKED", lambda: invoke(adapter))
        self.assert_code("ADMISSION_LOCKED", lambda: direct(machine))
        for book in (self.tickets, tickets):
            book.set_clock("clock", idempotency_key="later", now_ms=FIXTURE_NOW + ADMISSION_WINDOW_MS)
        self.assert_code("ADMISSION_LOCKED", lambda: invoke(adapter))
        self.assert_code("ADMISSION_LOCKED", lambda: direct(machine))
        self.assertEqual(invoke(adapter, idempotency_key="fresh-key"),
                         direct(machine, idempotency_key="fresh-key"))
        self.assertEqual(snapshot(self.tickets, self.machine), snapshot(tickets, machine))
        self.assertEqual(source.calls, ("offer-1",) * 3)

    def test_optional_reservation_omitted_and_null_are_forwarded_as_none(self):
        for omitted in (True, False):
            with self.subTest(omitted=omitted):
                body = record(reservation_id=None)
                if omitted:
                    body.pop("reservation_id")
                spy = Mock(spec=["list_resale"])
                invoke(ResaleOfferAdapter(spy, source_for(body)))
                self.assertIsNone(spy.list_resale.call_args.kwargs["reservation_id"])
                tickets, machine = build_fixture()
                adapted_tickets, adapted = build_fixture()
                self.assertEqual(invoke(ResaleOfferAdapter(adapted, source_for(body))),
                                 direct(machine, body))
                self.assertEqual(snapshot(adapted_tickets, adapted), snapshot(tickets, machine))

    def test_invalid_record_shapes_and_scalars_fetch_once_without_machine_access(self):
        valid = record()
        malformed = [[], "text", 1, False]
        malformed += [{k: v for k, v in valid.items() if k != field}
                      for field in valid if field != "reservation_id"]
        for extra in ("listing_id", "idempotency_key", "payment_ref", "funds_executed",
                      "role_authenticated", "extra"):
            malformed.append(valid | {extra: "injected"})
        for field in ("offer_id", "right_id", "seller_role", "recipient_role", "reservation_id"):
            for value in ("", " bad ", "x" * 101, True, 1, [], {}):
                malformed.append(valid | {field: value})
        for field, values in (
            ("version", (True, -1, 1.0, "1", None, [])),
            ("amount", (True, 0, -1, MONEY_MAX + 1, 1.0, "1", None, {})),
            ("expires_ms", (True, -1, CLOCK_MAX + 1, 1.0, "1", None, [])),
        ):
            malformed += [valid | {field: value} for value in values]
        malformed.append(valid | {"offer_id": "different-offer"})
        for body in malformed:
            with self.subTest(body=body):
                source = Mock()
                source.fetch.return_value = body
                with self.assertRaises(InvalidResaleOfferRecord):
                    invoke(ResaleOfferAdapter(NoMachineAccess(), source))
                source.fetch.assert_called_once_with("offer-1")

    def test_invalid_caller_identifiers_still_fetch_once(self):
        for field in ("offer_id", "listing_id", "idempotency_key"):
            for value in ("", " bad ", "x" * 101, None, True, 1, [], {}):
                with self.subTest(field=field, value=value):
                    source = Mock()
                    source.fetch.return_value = record()
                    with self.assertRaises(InvalidResaleOfferRecord):
                        invoke(ResaleOfferAdapter(NoMachineAccess(), source), **{field: value})
                    source.fetch.assert_called_once_with(value if field == "offer_id" else "offer-1")

    def test_absent_malformed_mismatched_and_fault_records_touch_no_fsm_or_keys(self):
        cases = [None, "{", "[]", '{"x":1,"x":2}', '{"x":NaN}',
                 json.dumps(record(offer_id="different")), json.dumps(record(version=True)),
                 json.dumps(record(payment_ref="injected")),
                 SyntheticResaleOfferFault.ERROR, SyntheticResaleOfferFault.TIMEOUT]
        for value in cases:
            with self.subTest(value=value):
                tickets, machine = build_fixture()
                before = snapshot(tickets, machine)
                source = FakeResaleOfferSource(recordings={} if value is None else {"offer-1": value})
                for target in (NoMachineAccess(), machine):
                    with patch.object(machine, "list_resale", wraps=machine.list_resale) as method:
                        with self.assertRaises(ResaleOfferSourceError):
                            invoke(ResaleOfferAdapter(target, source))
                        method.assert_not_called()
                    self.assertEqual(snapshot(tickets, machine), before)
                self.assertEqual(source.calls, ("offer-1", "offer-1"))
                accepted = invoke(ResaleOfferAdapter(machine, source_for()))
                self.assertFalse(accepted["duplicate"])

    def test_arbitrary_source_fault_is_wrapped_and_local_error_is_preserved(self):
        for cause in (TimeoutError("synthetic only"), ResaleOfferSourceError("local failure")):
            with self.subTest(cause=cause):
                source = Mock()
                source.fetch.side_effect = cause
                before = snapshot(self.tickets, self.machine)
                with patch.object(self.machine, "list_resale", wraps=self.machine.list_resale) as method:
                    with self.assertRaises(ResaleOfferSourceError) as raised:
                        invoke(ResaleOfferAdapter(self.machine, source))
                    method.assert_not_called()
                if isinstance(cause, ResaleOfferSourceError):
                    self.assertIs(raised.exception, cause)
                else:
                    self.assertIs(raised.exception.__cause__, cause)
                source.fetch.assert_called_once_with("offer-1")
                self.assertEqual(snapshot(self.tickets, self.machine), before)
        self.assertFalse(invoke(ResaleOfferAdapter(self.machine, source_for()))["duplicate"])

    def test_fetch_failure_after_acceptance_never_returns_cached_receipt(self):
        source = Mock()
        source.fetch.side_effect = [record(), None, TimeoutError("synthetic"), record()]
        adapter = ResaleOfferAdapter(self.machine, source)
        invoke(adapter)
        before = snapshot(self.tickets, self.machine)
        with self.assertRaises(ResaleOfferNotFound):
            invoke(adapter)
        with self.assertRaises(ResaleOfferSourceError):
            invoke(adapter)
        self.assertTrue(invoke(adapter)["duplicate"])
        self.assertEqual(snapshot(self.tickets, self.machine), before)
        self.assertEqual(source.fetch.call_count, 4)

    def test_scalar_upper_bounds_are_shape_valid_and_left_to_fsm(self):
        body = record(amount=MONEY_MAX, expires_ms=CLOCK_MAX, version=10**100)
        spy = Mock(spec=["list_resale"])
        invoke(ResaleOfferAdapter(spy, source_for(body)))
        self.assertEqual(spy.list_resale.call_args.kwargs["amount"], MONEY_MAX)
        self.assertEqual(spy.list_resale.call_args.kwargs["expires_ms"], CLOCK_MAX)

    def test_example_uses_actual_machines_lists_and_explicitly_refuses_competitor(self):
        result = run_example()
        assert_not_final(self, result["listed"])
        self.assertEqual(result["listed"]["listing"]["phase"], "LISTED")
        self.assertEqual(result["competing_refusal"], "RIGHT_SALE_LOCKED")
        self.assertEqual(result["source_calls"], ("offer-1", "offer-1"))


if __name__ == "__main__":
    unittest.main()
