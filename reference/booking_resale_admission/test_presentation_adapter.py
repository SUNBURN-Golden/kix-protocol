"""Source-informed adapter gaps; no HTTP, hardware or external services."""

import json
import unittest
from unittest.mock import Mock

from admission_fsm import AdmissionError, AdmissionMachine
from example_presentation_adapter import (
    FIXTURE_AUTH_EXPIRY, FIXTURE_NOW, FIXTURE_PRICE, FIXTURE_REQUEST,
    build_fixture, run_example,
)
from fake_presentation_source import FakePresentationSource, SyntheticPresentationFault
from mock_gates import CLOCK_MAX
from presentation_adapter import PresentationAdapter
from presentation_source import (
    InvalidPresentationRecord, PresentationNotFound, PresentationSourceError,
)
from test_admission_fsm import assert_not_final


def record(operation, **changes):
    body = dict(right_id="issue-1", version=1, request=FIXTURE_REQUEST)
    if operation == "authorize_admission":
        body["holder_role"] = "buyer-1"
    return body | changes


def source_for(operation, body=None, presentation_id="fixture"):
    return FakePresentationSource(recordings={
        (operation, presentation_id): json.dumps(record(operation) if body is None else body),
    })


def invoke(adapter, operation, **changes):
    caller = dict(idempotency_key=f"key-{operation}", gate_role="gate-a")
    if operation == "authorize_admission":
        caller.update(admission_id="admit-1", expires_ms=FIXTURE_AUTH_EXPIRY)
    else:
        caller["consume_id"] = "consume-1"
    caller.update(changes)
    presentation_id = caller.pop("presentation_id", "fixture")
    return getattr(adapter, operation)(presentation_id, **caller)


class PresentationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.book, self.tickets, self.resale, self.machine = build_fixture()

    def snapshot(self):
        return tuple((machine.canonical_state(), machine.export_journal())
                     for machine in (self.book, self.tickets, self.resale, self.machine))

    def authorize(self):
        return invoke(PresentationAdapter(self.machine, source_for("authorize_admission")),
                      "authorize_admission")

    def assert_code(self, code, fn):
        with self.assertRaises(AdmissionError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def test_receipts_replay_and_effects_match_direct_fsm(self):
        direct_book, direct_tickets, direct_resale, direct = build_fixture()
        source = FakePresentationSource(recordings={
            (operation, selector): json.dumps(record(operation))
            for operation in ("authorize_admission", "consume")
            for selector in ("fixture", "same-input")
        })
        adapter = PresentationAdapter(self.machine, source)
        book_before = self.book.canonical_state()
        for operation in ("authorize_admission", "consume"):
            caller = dict(idempotency_key=f"key-{operation}", gate_role="gate-a")
            if operation == "authorize_admission":
                caller["expires_ms"] = FIXTURE_AUTH_EXPIRY
            subject = "admit-1" if operation == "authorize_admission" else "consume-1"
            expected = getattr(direct, operation)(subject, **caller, **record(operation))
            actual = invoke(adapter, operation)
            self.assertEqual(actual, expected)
            assert_not_final(self, actual)
            for left, right in ((self.machine, direct), (self.tickets, direct_tickets),
                                (self.resale, direct_resale), (self.book, direct_book)):
                self.assertEqual(left.canonical_state(), right.canonical_state())
                self.assertEqual(left.export_journal(), right.export_journal())
            if operation == "authorize_admission":
                self.assertEqual(self.tickets.view("reserve-1")["phase"], "ADMISSION_AUTHORIZED")
                self.assertEqual(self.tickets.view("reserve-1")["right"]["version"], 1)
                first_authorization = json.loads(json.dumps(actual))
            else:
                self.assertEqual(actual["evidence"]["decision"], "CONSUMED_ONCE")
                self.assertEqual(actual["evidence"]["version_after"], 2)
                self.assertIs(actual["evidence"]["private_proof_verified"], False)
                self.assertIs(actual["evidence"]["admission_routing_production"], False)
            before_replay = self.snapshot()
            # Corrupt the caller's receipt; first-result snapshots must stay detached.
            actual["credential"]["phase"] = "corrupted"
            replay = invoke(adapter, operation, presentation_id="same-input")
            self.assertEqual(replay, getattr(direct, operation)(subject, **caller, **record(operation)))
            self.assertTrue(replay["duplicate"])
            self.assertEqual(self.snapshot(), before_replay)
        before = self.snapshot()
        frozen = invoke(adapter, "authorize_admission")
        self.assertEqual(frozen, first_authorization | {"duplicate": True, "applied": None})
        self.assertEqual(frozen["credential"]["phase"], "AUTHORIZED")
        self.assertEqual(self.machine.view("issue-1")["phase"], "CONSUMED")
        self.assert_code("ALREADY_CONSUMED", lambda: invoke(
            adapter, "consume", consume_id="another-consume", idempotency_key="another-key"))
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.book.canonical_state(), book_before)
        self.assertEqual(len(source.calls), 6)

    def test_exact_forwarding_receipt_and_exception_identity_for_both_methods(self):
        for operation in ("authorize_admission", "consume"):
            with self.subTest(operation=operation):
                machine = Mock()
                source = source_for(operation)
                adapter = PresentationAdapter(machine, source)
                receipt = {"receipt": object()}
                method = getattr(machine, operation)
                method.return_value = receipt
                self.assertIs(invoke(adapter, operation), receipt)
                expected = dict(idempotency_key=f"key-{operation}", gate_role="gate-a",
                                **record(operation))
                if operation == "authorize_admission":
                    expected["expires_ms"] = FIXTURE_AUTH_EXPIRY
                method.assert_called_once_with(
                    "admit-1" if operation == "authorize_admission" else "consume-1", **expected)
                self.assertEqual(len(machine.mock_calls), 1)
                error = AdmissionError("FIXTURE_ERROR")
                method.side_effect = error
                with self.assertRaises(AdmissionError) as caught:
                    invoke(adapter, operation)
                self.assertIs(caught.exception, error)
                self.assertEqual(len(source.calls), 2)

    def test_missing_malformed_faults_precede_all_machine_access(self):
        for operation in ("authorize_admission", "consume"):
            valid = record(operation)
            cases = [None, "{", "[]", '{"version":1,"version":2}',
                     SyntheticPresentationFault.ERROR, SyntheticPresentationFault.TIMEOUT]
            malformed = [valid | {"extra": True}, valid | {"admission_routing_production": False},
                         valid | {"external_dependency": "VENUE_IDENTITY"},
                         valid | {"right_id": " bad "}, valid | {"version": True},
                         valid | {"version": -1}, valid | {"request": "AA" * 32}]
            malformed += [{k: v for k, v in valid.items() if k != field} for field in valid]
            if operation == "authorize_admission":
                malformed += [valid | {"holder_role": ""}]
            else:
                malformed += [valid | {"holder_role": "buyer-1"}]
            cases += [json.dumps(body) for body in malformed]
            for value in cases:
                with self.subTest(operation=operation, value=value):
                    recordings = {} if value is None else {(operation, "fixture"): value}
                    source = FakePresentationSource(recordings=recordings)
                    machine = Mock()
                    with self.assertRaises(PresentationSourceError):
                        invoke(PresentationAdapter(machine, source), operation)
                    self.assertEqual(machine.mock_calls, [])
                    self.assertEqual(source.calls, ((operation, "fixture"),))

    def test_invalid_caller_shapes_fetch_once_and_precede_machine_access(self):
        for operation in ("authorize_admission", "consume"):
            subject = "admission_id" if operation == "authorize_admission" else "consume_id"
            changes = [{subject: ""}, {subject: 1}, {"idempotency_key": " "},
                       {"idempotency_key": "k" * 101}, {"gate_role": None},
                       {"presentation_id": " bad "}]
            if operation == "authorize_admission":
                changes += [{"expires_ms": value} for value in (True, -1, CLOCK_MAX + 1, "1")]
            for change in changes:
                with self.subTest(operation=operation, change=change):
                    source = source_for(operation, presentation_id=change.get("presentation_id", "fixture"))
                    machine = Mock()
                    with self.assertRaises(InvalidPresentationRecord):
                        invoke(PresentationAdapter(machine, source), operation, **change)
                    self.assertEqual(machine.mock_calls, [])
                    self.assertEqual(len(source.calls), 1)

    def test_bad_inputs_do_not_bind_real_keys_then_same_key_accepts(self):
        for operation in ("authorize_admission", "consume"):
            if operation == "consume":
                self.authorize()
            before = self.snapshot()
            for value in (None, "{", json.dumps(record(operation, version=True)),
                          SyntheticPresentationFault.ERROR, SyntheticPresentationFault.TIMEOUT):
                recordings = {} if value is None else {(operation, "fixture"): value}
                source = FakePresentationSource(recordings=recordings)
                with self.assertRaises(PresentationSourceError):
                    invoke(PresentationAdapter(self.machine, source), operation)
                self.assertEqual(len(source.calls), 1)
                self.assertEqual(self.snapshot(), before)
            source = source_for(operation)
            with self.assertRaises(InvalidPresentationRecord):
                invoke(PresentationAdapter(self.machine, source), operation, gate_role="")
            self.assertEqual(self.snapshot(), before)
            accepted = invoke(PresentationAdapter(self.machine, source), operation)
            self.assertFalse(accepted["duplicate"])

    def test_arbitrary_source_failures_and_non_dict_records(self):
        for operation in ("authorize_admission", "consume"):
            for value in ([], "text", 1, False):
                with self.subTest(operation=operation, value=value):
                    source = Mock()
                    source.fetch.return_value = value
                    machine = Mock()
                    with self.assertRaises(InvalidPresentationRecord):
                        invoke(PresentationAdapter(machine, source), operation)
                    source.fetch.assert_called_once_with("fixture", operation=operation)
                    self.assertEqual(machine.mock_calls, [])
            source = Mock()
            cause = TimeoutError("synthetic only")
            source.fetch.side_effect = cause
            machine = Mock()
            with self.assertRaises(PresentationSourceError) as caught:
                invoke(PresentationAdapter(machine, source), operation)
            self.assertIs(caught.exception.__cause__, cause)
            source.fetch.assert_called_once_with("fixture", operation=operation)
            self.assertEqual(machine.mock_calls, [])

    def test_failure_after_success_does_not_return_cached_receipt(self):
        for operation in ("authorize_admission", "consume"):
            with self.subTest(operation=operation):
                if operation == "consume":
                    self.authorize()
                source = Mock()
                source.fetch.side_effect = [record(operation), None, TimeoutError("synthetic")]
                adapter = PresentationAdapter(self.machine, source)
                invoke(adapter, operation)
                before = self.snapshot()
                with self.assertRaises(PresentationNotFound):
                    invoke(adapter, operation)
                with self.assertRaises(PresentationSourceError):
                    invoke(adapter, operation)
                self.assertEqual(source.fetch.call_count, 3)
                self.assertEqual(self.snapshot(), before)

    def test_stale_version_holder_and_conflicting_keys(self):
        before = self.snapshot()
        for body, code in ((record("authorize_admission", version=2), "STALE_VERSION"),
                           (record("authorize_admission", holder_role="buyer-2"), "NOT_HOLDER")):
            source = source_for("authorize_admission", body)
            adapter = PresentationAdapter(self.machine, source)
            self.assert_code(code, lambda: invoke(adapter, "authorize_admission", idempotency_key=code))
            self.assert_code(code, lambda: invoke(adapter, "authorize_admission", idempotency_key=code))
            self.assertEqual(len(source.calls), 2)
            self.assertEqual(self.snapshot(), before)
        self.assert_code("IDEMPOTENCY_CONFLICT", lambda: invoke(
            PresentationAdapter(self.machine, source_for("authorize_admission")),
            "authorize_admission", idempotency_key="STALE_VERSION"))

    def test_successful_key_conflicts_and_consume_never_auto_authorizes(self):
        before = self.snapshot()
        source = source_for("consume")
        self.assert_code("ADMISSION_REQUIRED", lambda: invoke(
            PresentationAdapter(self.machine, source), "consume", idempotency_key="early-consume"))
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(source.calls), 1)
        self.authorize()
        before = self.snapshot()
        self.assert_code("IDEMPOTENCY_CONFLICT", lambda: invoke(
            PresentationAdapter(self.machine, source_for("authorize_admission")),
            "authorize_admission", gate_role="gate-b"))
        self.assertEqual(self.snapshot(), before)
        adapter = PresentationAdapter(self.machine, source_for("consume"))
        invoke(adapter, "consume")
        before = self.snapshot()
        self.assert_code("IDEMPOTENCY_CONFLICT", lambda: invoke(adapter, "consume", gate_role="gate-b"))
        self.assertEqual(self.snapshot(), before)

    def test_rejected_key_stays_rejected_after_listing_cancelled(self):
        self.list_resale()
        adapter = PresentationAdapter(self.machine, source_for("authorize_admission"))
        before = self.snapshot()
        self.assert_code("LISTING_LOCKED", lambda: invoke(adapter, "authorize_admission"))
        self.assertEqual(self.snapshot(), before)
        self.resale.cancel_listing("list-1", idempotency_key="cancel-list", seller_role="buyer-1")
        before = self.snapshot()
        self.assert_code("LISTING_LOCKED", lambda: invoke(adapter, "authorize_admission"))
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(invoke(adapter, "authorize_admission", idempotency_key="fresh-auth")["duplicate"])

    def list_resale(self):
        self.resale.list_resale(
            "list-1", idempotency_key="list", right_id="issue-1", version=1,
            seller_role="buyer-1", recipient_role="buyer-2", amount=FIXTURE_PRICE,
            expires_ms=FIXTURE_NOW + 120_000, reservation_id="reserve-1",
        )

    def test_transfer_refuses_old_and_transferred_presentations_without_reissue(self):
        self.list_resale()
        self.resale.observe_resale_payment(
            "list-1", idempotency_key="resale-payment", payment_ref="cd" * 32,
            amount=FIXTURE_PRICE, buyer_role="buyer-2",
        )
        self.resale.accept_resale("transfer-1", idempotency_key="transfer", listing_id="list-1")
        before = self.snapshot()
        for version, holder in ((1, "buyer-1"), (2, "buyer-2")):
            adapter = PresentationAdapter(self.machine, source_for(
                "authorize_admission", record("authorize_admission", version=version, holder_role=holder)))
            self.assert_code("STALE_VERSION", lambda: invoke(
                adapter, "authorize_admission", idempotency_key=f"transfer-auth-{version}"))
        self.assertEqual(self.snapshot(), before)
        self.assertIs(self.machine.view("issue-1")["venue_credential_reissued"], False)

    def test_expired_authorization_cannot_consume_or_change_state(self):
        self.authorize()
        self.machine.set_clock("clock", idempotency_key="expire", now_ms=FIXTURE_AUTH_EXPIRY)
        before = self.snapshot()
        source = source_for("consume")
        self.assert_code("ADMISSION_EXPIRED", lambda: invoke(
            PresentationAdapter(self.machine, source), "consume"))
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(source.calls), 1)

    def test_bound_external_sources_are_refused_without_reading(self):
        class Unreadable:
            def __getattr__(self, name):
                raise AssertionError(name)

        journal = self.machine.export_journal()
        for attribute, code in (("venue_source", "VENUE_SOURCE_UNAVAILABLE"),
                                ("revocation_source", "REVOCATION_SOURCE_UNAVAILABLE")):
            self.machine = AdmissionMachine.restore(
                journal, ticket_source=self.tickets, ownership_source=self.resale,
                settlement_source=self.book, **{attribute: Unreadable()},
            )
            for operation in ("authorize_admission", "consume"):
                before = self.snapshot()
                adapter = PresentationAdapter(self.machine, source_for(operation))
                self.assert_code(code, lambda: invoke(adapter, operation, idempotency_key=f"{attribute}-{operation}"))
                self.assertEqual(self.snapshot(), before)

    def test_settlement_flags_are_still_checked_for_each_operation(self):
        source = Mock(wraps=self.book)
        self.machine = AdmissionMachine.restore(
            self.machine.export_journal(), ticket_source=self.tickets,
            ownership_source=self.resale, settlement_source=source,
        )
        real_view = self.book.view
        for operation in ("authorize_admission", "consume"):
            if operation == "consume":
                source.view.side_effect = real_view
                self.authorize()
            source.view.side_effect = lambda identity: real_view(identity) | {"admission_granted": True}
            before = self.snapshot()
            adapter = PresentationAdapter(self.machine, source_for(operation))
            self.assert_code("SETTLEMENT_VIEW_REJECTED", lambda: invoke(
                adapter, operation, idempotency_key=f"rejected-{operation}"))
            self.assertEqual(self.snapshot(), before)

    def test_runnable_example_uses_separate_authorization_and_consume(self):
        result = run_example()
        self.assertEqual(result["phase_after_authorization"], "ADMISSION_AUTHORIZED")
        self.assertEqual(result["authorized"]["credential"]["phase"], "AUTHORIZED")
        self.assertEqual(result["consumed"]["credential"]["phase"], "CONSUMED")
        self.assertEqual(result["replay"]["evidence"]["version_after"], 2)
        self.assertEqual(result["source_calls"], (("authorize_admission", "fixture-ticket"),
                                                ("consume", "fixture-ticket"), ("consume", "fixture-ticket")))
        for name in ("authorized", "consumed", "replay"):
            assert_not_final(self, result[name])


if __name__ == "__main__":
    unittest.main()
