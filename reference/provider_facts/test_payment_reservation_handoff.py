"""Source-informed offline composition tests. Analog, NOT Toss.

These test fixture association and application boundaries, not authentication,
production identity mapping, durability, bank exactly-once or chain finality.
"""

import json
import subprocess
import sys
import unittest
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import patch

import synthetic_documents as fixtures
from example_payment_reservation_handoff import example_result, prepare_fixture
from fake_payment_lookup import FakePaymentLookup, SyntheticLookupFault
from payment_lookup import SyntheticLookupResult
from payment_lookup_router import PaymentLookupRouter
from payment_reservation_handoff import (
    PaymentReservationHandoff, ReservationError,
)
from provider_facts import (
    KRW_U128_MAX, OperationBindingStore, Unresolved, normalize_recorded_text,
)
from mock_gates import NON_CLAIMS


class PaymentReservationHandoffTests(unittest.TestCase):
    def setUp(self):
        self.machine, self.bindings, self.fake, self.association = prepare_fixture()
        self.operation = self.association.operation_ref
        self.payment = self.association.payment_ref
        self.router = PaymentLookupRouter(self.bindings, routes={self.fake.scope: self.fake})
        # Nonempty capture/review records detect accidental evidence mutation.
        self.bindings.record_capture(
            self.operation, self.payment,
            normalize_recorded_text(self.payment, json.dumps(fixtures.PAID)).items[0],
        )
        self.bindings.bind(self.operation, fixtures.PAYMENT_REF_B)

    def evidence_snapshot(self, fakes):
        return deepcopy((
            self.bindings.lookup(self.operation), self.bindings.binding_count(),
            self.bindings.recorded_captures, self.bindings.review,
            [dict(fake.recordings) for fake in fakes],
        ))

    def submit(self, *, router=None, association=None, observe_calls=0, unchanged=True, fakes=None):
        router = self.router if router is None else router
        association = self.association if association is None else association
        fakes = [self.fake] if fakes is None else fakes
        before = self.machine.canonical_state()
        evidence = self.evidence_snapshot(fakes)
        looked_up, responses, errors = [], [], []
        original_lookup = router.lookup
        original_observe = self.machine.observe_payment

        def lookup(operation):
            result = original_lookup(operation)
            looked_up.append(result)
            return result

        def observe(*args, **kwargs):
            try:
                result = original_observe(*args, **kwargs)
            except ReservationError as error:
                errors.append(error)
                raise
            responses.append(result)
            return result

        with patch.object(router, "lookup", side_effect=lookup) as lookup_spy, patch.object(
            self.machine, "observe_payment", side_effect=observe,
        ) as observe_spy:
            result = PaymentReservationHandoff(router, self.machine, association=association).submit(self.operation)
        lookup_spy.assert_called_once_with(self.operation)
        self.assertIs(result.lookup_result, looked_up[0])
        self.assertEqual(observe_spy.call_count, observe_calls)
        if observe_calls:
            observe_spy.assert_called_once_with(
                association.order_id, idempotency_key=association.idempotency_key,
                payment_ref=association.mock_payment_ref, amount=15000,
            )
        else:
            self.assertIsNone(result.fsm_result)
        if responses:
            self.assertIs(result.fsm_result, responses[0])
            self.assertIsNone(result.fsm_error)
        if errors:
            self.assertIs(result.fsm_error, errors[0])
            self.assertIsNone(result.fsm_result)
        if unchanged:
            self.assertEqual(self.machine.canonical_state(), before)
        self.assertEqual(self.evidence_snapshot(fakes), evidence)
        return result

    def router_with(self, recording):
        fake = FakePaymentLookup(scope=self.fake.scope, recordings={self.payment: recording})
        return PaymentLookupRouter(self.bindings, routes={fake.scope: fake}), fake

    def test_primary_payment_handoff(self):
        self.assertEqual(self.machine.view(self.association.reservation_id)["phase"], "CONFIRMED")
        self.assertNotEqual(self.association.order_id, self.payment.order_id)
        before = self.machine.export_journal()
        result = self.submit(observe_calls=1, unchanged=False)
        self.assertIsNone(result.reason)
        self.assertEqual(self.fake.calls, (self.payment,))
        self.assertEqual(result.lookup_result.provenance, "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY")
        self.assertEqual(result.fsm_result["provenance"], "MOCK_GATE_ONLY")
        view = self.machine.view(self.association.reservation_id)
        self.assertEqual(view["phase"], "PAYMENT_NOTED")
        self.assertEqual(view["payment_ref"], self.association.mock_payment_ref)
        self.assertEqual(view["slot_state"], "RESERVED")
        self.assertEqual(view["slot_reservation_id"], self.association.reservation_id)
        self.assertIsNone(view["issuance_id"])
        self.assertIsNone(view["right"])
        self.assertIsNone(view["settlement_id"])
        for name in (*NON_CLAIMS, "economic_finality_claimed", "chain_issued"):
            self.assertIs(view[name], False, name)
        self.assertEqual(self.machine.export_journal(), before + [{
            "op": "observe_payment", "subject_id": self.association.order_id,
            "idempotency_key": self.association.idempotency_key,
            "body": {"payment_ref": self.association.mock_payment_ref, "amount": 15000},
        }])

    def test_association_validation_and_frozen_configuration(self):
        for field, value in (
            ("operation_ref", "operation"), ("payment_ref", "payment"),
        ):
            with self.subTest(field=field), self.assertRaises(TypeError):
                replace(self.association, **{field: value})
        for field in ("reservation_id", "order_id", "idempotency_key"):
            for value in (None, True, "", " padded ", "x" * 101):
                with self.subTest(field=field, value=value), self.assertRaises(ReservationError) as caught:
                    replace(self.association, **{field: value})
                self.assertEqual(caught.exception.code, "INVALID_ID")
        for value in (None, True, "AB" * 32, "g" * 64, "a" * 63, "a" * 65):
            with self.subTest(value=value), self.assertRaises(ReservationError) as caught:
                replace(self.association, mock_payment_ref=value)
            self.assertEqual(caught.exception.code, "PAYMENT_REF")
        with self.assertRaises(FrozenInstanceError):
            self.association.idempotency_key = "replacement"
        with self.assertRaises(TypeError):
            PaymentReservationHandoff(self.router, self.machine, association=None)
        self.assertEqual(self.fake.calls, ())

    def test_every_submitted_operation_dimension_requires_exact_match(self):
        before = self.machine.canonical_state()
        for incoming in [None, "operation", *(
            replace(self.operation, **{field: "different-synthetic"})
            for field in ("provider", "account", "operation")
        )]:
            with self.subTest(incoming=incoming), patch.object(self.router, "lookup") as lookup, patch.object(
                self.machine, "observe_payment",
            ) as observe:
                result = PaymentReservationHandoff(
                    self.router, self.machine, association=self.association,
                ).submit(incoming)
                self.assertEqual(result.reason, "OPERATION_MISMATCH")
                self.assertIsNone(result.lookup_result)
                lookup.assert_not_called()
                observe.assert_not_called()
        self.assertEqual(self.machine.canonical_state(), before)

    def test_every_associated_payment_dimension_requires_exact_match(self):
        for field in ("provider", "account", "environment", "payment_key", "order_id"):
            association = replace(self.association, payment_ref=replace(self.payment, **{field: "different"}))
            with self.subTest(field=field):
                self.assertEqual(self.submit(association=association).reason, "LOOKUP_IDENTITY_MISMATCH")

    def test_lookup_envelope_history_and_item_identities_are_checked(self):
        lookup = self.router.lookup(self.operation)
        history = lookup.result
        wrong_results = []
        for field in ("provider", "account", "operation"):
            wrong_results.append(replace(lookup, operation_ref=replace(self.operation, **{field: "other"})))
        for field in ("provider", "account", "environment", "payment_key", "order_id"):
            wrong = replace(self.payment, **{field: "other"})
            wrong_results.extend((
                replace(lookup, payment_ref=wrong),
                replace(lookup, result=replace(history, payment_ref=wrong)),
                replace(lookup, result=replace(history, items=(replace(history.items[0], payment_ref=wrong),))),
            ))
        wrong_results.append(replace(lookup, payment_ref=None))
        for wrong in wrong_results:
            with self.subTest(wrong=wrong), patch.object(self.router, "lookup", return_value=wrong):
                result = self.submit()
                self.assertIs(result.lookup_result, wrong)
                self.assertEqual(result.reason, "LOOKUP_IDENTITY_MISMATCH")

    def test_inconsistent_association_scope_cannot_apply_even_consistent_lookup(self):
        for field in ("provider", "account"):
            payment = replace(self.payment, **{field: "other"})
            association = replace(self.association, payment_ref=payment)
            history = normalize_recorded_text(payment, json.dumps(fixtures.PAID))
            lookup = SyntheticLookupResult(self.operation, payment, history)
            with self.subTest(field=field), patch.object(self.router, "lookup", return_value=lookup):
                self.assertEqual(self.submit(association=association).reason, "LOOKUP_IDENTITY_MISMATCH")

    def test_local_order_and_reservation_are_explicit(self):
        wrong_order = replace(self.association, order_id=self.payment.order_id)
        self.assertEqual(self.submit(association=wrong_order).reason, "RESERVATION_IDENTITY_MISMATCH")
        missing = replace(self.association, reservation_id="missing-local-reservation")
        self.assertEqual(self.submit(association=missing).fsm_error.code, "UNKNOWN_RESERVATION")
        # A valid reservation belonging to a different order must also fail.
        self.machine.register_show(
            "other-show", idempotency_key="other-show", organizer_role="organizer",
            capacity=1, gate_roles=["gate"], primary_price=15000, resale_cap=15000,
            resale_allowed=False, organizer_bps=0, platform_bps=0,
        )
        self.machine.hold(
            "other-reservation", idempotency_key="other-hold", show_id="other-show",
            slot=0, buyer_role="fixture-buyer", expires_ms=1_900_000,
        )
        self.machine.confirm(
            "other-order", idempotency_key="other-confirm", reservation_id="other-reservation", amount=15000,
        )
        other_reservation = replace(self.association, reservation_id="other-reservation")
        self.assertEqual(self.submit(association=other_reservation).reason, "RESERVATION_IDENTITY_MISMATCH")
        view = self.machine.view(self.association.reservation_id)
        with patch.object(self.machine, "view", return_value=dict(view, reservation_id="other")):
            self.assertEqual(self.submit().reason, "RESERVATION_IDENTITY_MISMATCH")

    def test_amount_mismatch_and_provider_reservation_range_boundary(self):
        for amount in (0, 14999, 15001, 10**12 + 1, 2**53 + 1, KRW_U128_MAX):
            document = deepcopy(fixtures.PAID)
            document["payment"]["totalAmount"] = amount
            router, fake = self.router_with(json.dumps(document))
            with self.subTest(amount=amount):
                result = self.submit(router=router, fakes=[fake])
                self.assertEqual(result.reason, "PAYMENT_AMOUNT_MISMATCH")
                self.assertEqual(result.lookup_result.result.items[0].amount, amount)
                self.assertEqual(fake.calls, (self.payment,))
        for amount in (1, 10**12):
            machine, bindings, fake, association = prepare_fixture(amount=amount)
            router = PaymentLookupRouter(bindings, routes={fake.scope: fake})
            with self.subTest(amount=amount), patch.object(machine, "observe_payment", wraps=machine.observe_payment) as observe:
                result = PaymentReservationHandoff(router, machine, association=association).submit(self.operation)
                self.assertEqual(result.fsm_result["reservation"]["amount"], amount)
                self.assertEqual(observe.call_args.kwargs["amount"], amount)
                self.assertEqual(type(observe.call_args.kwargs["amount"]), int)

    def test_currency_and_noninteger_defense_before_observation(self):
        lookup = self.router.lookup(self.operation)
        for changes in ({"currency": "USD"}, {"amount": True}, {"amount": 15000.0}, {"amount": "15000"}):
            item = replace(lookup.result.items[0], **changes)
            wrong = replace(lookup, result=replace(lookup.result, items=(item,)))
            with self.subTest(changes=changes), patch.object(self.router, "lookup", return_value=wrong):
                self.assertEqual(self.submit().reason, "PAYMENT_AMOUNT_MISMATCH")
        view = self.machine.view(self.association.reservation_id)
        for changes in ({"currency": "USD"}, {"amount": True}, {"amount": 15000.0}):
            with self.subTest(view=changes), patch.object(self.machine, "view", return_value=dict(view, **changes)):
                self.assertEqual(self.submit().reason, "PAYMENT_AMOUNT_MISMATCH")

    def test_unresolved_and_missing_configuration_preserve_state_without_fallback(self):
        alternate_scope = replace(self.fake.scope, account="other-synthetic-mid")
        alternate_payment = replace(self.payment, account=alternate_scope.account)
        alternate = FakePaymentLookup(scope=alternate_scope, recordings={alternate_payment: json.dumps(fixtures.PAID)})
        alternate_operation = replace(self.operation, account=alternate_scope.account)
        self.bindings.bind(alternate_operation, alternate_payment)
        alternate_bindings = self.bindings.lookup(alternate_operation)
        for recording, reason in (
            (SyntheticLookupFault.TIMEOUT, "LOOKUP_TIMEOUT"),
            (SyntheticLookupFault.ERROR, "LOOKUP_ERROR"),
            (None, "LOOKUP_NOT_FOUND"),
            (json.dumps(fixtures.TIMEOUT), "LOOKUP_TIMEOUT"),
            (json.dumps(fixtures.NOT_FOUND), "LOOKUP_NOT_FOUND"),
            (json.dumps(fixtures.UNVERIFIED_SIGNAL), "UNVERIFIED_SOURCE"),
            (fixtures.FLOAT_AMOUNT_TEXT, "FLOAT_TOKEN"),
        ):
            fake = FakePaymentLookup(scope=self.fake.scope, recordings={} if recording is None else {self.payment: recording})
            router = PaymentLookupRouter(self.bindings, routes={fake.scope: fake, alternate.scope: alternate})
            with self.subTest(reason=reason):
                for _ in range(2):  # explicit submissions only, each calls the original fake once
                    calls = len(fake.calls)
                    result = self.submit(router=router, fakes=[fake, alternate])
                    self.assertEqual(result.lookup_result.result, Unresolved(reason))
                    self.assertEqual(len(fake.calls), calls + 1)
                self.assertEqual(alternate.calls, ())
        missing_binding = PaymentLookupRouter(OperationBindingStore(), routes={self.fake.scope: self.fake})
        missing_route = PaymentLookupRouter(self.bindings, routes={alternate.scope: alternate})
        calls = self.fake.calls
        for router, reason in ((missing_binding, "BINDING_REQUIRED"), (missing_route, "LOOKUP_ROUTE_MISSING")):
            result = self.submit(router=router, fakes=[self.fake, alternate])
            self.assertEqual(result.lookup_result.result, Unresolved(reason))
        self.assertEqual(self.fake.calls, calls)
        self.assertEqual(self.bindings.lookup(alternate_operation), alternate_bindings)
        self.assertEqual(alternate.calls, ())
        # Show the alternate fixture really can succeed, after all no-fallback assertions.
        self.assertEqual(PaymentLookupRouter(self.bindings, routes={alternate.scope: alternate}).lookup(
            alternate_operation,
        ).result.items[0].amount, 15000)

    def test_cancellation_histories_are_retained_intact(self):
        documents = [fixtures.PARTIAL_CANCEL, fixtures.CANCELED_AFTER_DONE, fixtures.MULTIPLE_CANCELS]
        for status in ("CANCELED", "PARTIAL_CANCELED"):
            document = deepcopy(fixtures.PAID)
            document["payment"]["status"] = status
            documents.append(document)
        done_with_cancel = deepcopy(fixtures.PARTIAL_CANCEL)
        done_with_cancel["payment"]["status"] = "DONE"
        documents.append(done_with_cancel)
        for document in documents:
            text = json.dumps(document)
            expected = normalize_recorded_text(self.payment, text)
            router, fake = self.router_with(text)
            with self.subTest(status=document["payment"]["status"], count=len(expected.items)):
                result = self.submit(router=router, fakes=[fake])
                self.assertEqual(result.reason, "PRIMARY_PAYMENT_REQUIRED")
                self.assertEqual(result.lookup_result.result, expected)
                self.assertEqual(result.lookup_result.result.item_hashes(), expected.item_hashes())
                self.assertEqual(fake.calls, (self.payment,))

    def test_nonprimary_histories_are_not_applied(self):
        lookup = self.router.lookup(self.operation)
        item = lookup.result.items[0]
        for items in ((), (item, item), (replace(item, kind="cancel"),), (replace(item, status_text="WAITING"),)):
            wrong = replace(lookup, result=replace(lookup.result, items=items))
            with self.subTest(items=items), patch.object(self.router, "lookup", return_value=wrong):
                self.assertEqual(self.submit().reason, "PRIMARY_PAYMENT_REQUIRED")

    def test_raw_timestamp_receipt_details_and_hashes_survive(self):
        router, fake = self.router_with(json.dumps(fixtures.OFFSET_LESS_CREATED_AT))
        result = self.submit(router=router, fakes=[fake], observe_calls=1, unchanged=False)
        history = result.lookup_result.result
        self.assertEqual(history.receipt.text, "2026-10-01T12:00:05+09:00")
        self.assertEqual(history.items[0].occurred.text, "2026-10-01T12:00:00+09:00")
        self.assertEqual(history.items[0].detail["timestamps"]["createdAt"], {
            "text": "2026-10-01T12:00:01", "offset": None, "status": "AMBIGUOUS_UNRESOLVED",
        })
        expected = normalize_recorded_text(self.payment, json.dumps(fixtures.OFFSET_LESS_CREATED_AT))
        self.assertEqual(history, expected)
        self.assertEqual(history.item_hashes(), expected.item_hashes())

    def test_explicit_success_replay_and_replay_after_separate_issue(self):
        handoff = PaymentReservationHandoff(self.router, self.machine, association=self.association)
        first = handoff.submit(self.operation).fsm_result
        expected = dict(first, duplicate=True, applied=None)
        after_payment = self.machine.canonical_state()
        self.assertEqual(handoff.submit(self.operation).fsm_result, expected)
        self.assertEqual(self.machine.canonical_state(), after_payment)
        self.machine.issue("separately-issued", idempotency_key="explicit-issue", order_id=self.association.order_id)
        after_issue = self.machine.canonical_state()
        self.assertEqual(handoff.submit(self.operation).fsm_result, expected)
        self.assertEqual(self.machine.canonical_state(), after_issue)
        self.assertEqual(self.machine.view(self.association.reservation_id)["phase"], "ISSUED")
        self.assertEqual(self.fake.calls, (self.payment,) * 3)
        self.assertEqual(sum(e["op"] == "observe_payment" for e in self.machine.export_journal()), 1)

    def test_rejection_is_retained_after_separate_transition(self):
        self.machine.set_clock("clock", idempotency_key="expire", now_ms=1_900_000)
        first = self.submit(observe_calls=1)
        self.assertEqual(first.fsm_error.code, "RESERVATION_EXPIRED")
        self.machine.cancel(self.association.reservation_id, idempotency_key="explicit-cancel")
        self.assertEqual(self.submit(observe_calls=1).fsm_error.code, "RESERVATION_EXPIRED")
        fresh_key = replace(self.association, idempotency_key="explicit-other-key")
        self.assertEqual(self.submit(association=fresh_key, observe_calls=1).fsm_error.code, "TERMINAL_IMMUTABLE")
        self.assertEqual(sum(e["op"] == "observe_payment" for e in self.machine.export_journal()), 0)

    def test_conflicting_key_is_not_replaced(self):
        self.submit(observe_calls=1, unchanged=False)
        association = replace(self.association, mock_payment_ref="cd" * 32)
        self.assertEqual(self.submit(association=association, observe_calls=1).fsm_error.code, "IDEMPOTENCY_CONFLICT")
        self.assertEqual(self.machine.view(association.reservation_id)["payment_ref"], self.association.mock_payment_ref)
        self.assertTrue(self.submit(observe_calls=1).fsm_result["duplicate"])

    def test_returned_mutable_evidence_does_not_change_later_explicit_results(self):
        first = self.submit(observe_calls=1, unchanged=False)
        first.lookup_result.result.items[0].detail["timestamps"].clear()
        first.fsm_result["reservation"]["amount"] = -1
        replay = self.submit(observe_calls=1)
        self.assertEqual(replay.fsm_result["reservation"]["amount"], 15000)
        self.assertIn("approvedAt", replay.lookup_result.result.items[0].detail["timestamps"])

    def test_only_reservation_errors_are_enveloped(self):
        error = ReservationError("fixture-rejection")
        with patch.object(self.machine, "observe_payment", side_effect=error):
            result = PaymentReservationHandoff(self.router, self.machine, association=self.association).submit(self.operation)
            self.assertIs(result.fsm_error, error)
        for target, method in ((self.router, "lookup"), (self.machine, "view"), (self.machine, "observe_payment")):
            error = RuntimeError("programming-error")
            with self.subTest(method=method), patch.object(target, method, side_effect=error):
                with self.assertRaises(RuntimeError) as caught:
                    PaymentReservationHandoff(self.router, self.machine, association=self.association).submit(self.operation)
                self.assertIs(caught.exception, error)

    def test_offline_example_callable_and_subprocess_agree(self):
        path = Path(__file__).with_name("example_payment_reservation_handoff.py")
        completed = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, check=True)
        self.assertEqual(completed.stderr, "")
        row = json.loads(completed.stdout)
        # JSON encodes the history tuple as an array.
        self.assertEqual(row, json.loads(json.dumps(example_result())))
        self.assertEqual(row["reservation"]["phase"], "PAYMENT_NOTED")
        self.assertEqual(len(row["fake_calls"]), 1)
        self.assertIsNone(row["reservation"]["right"])
        self.assertIsNone(row["reservation"]["issuance_id"])


if __name__ == "__main__":
    unittest.main()
