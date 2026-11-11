"""Source-informed synthetic routing characterizations. Analog, NOT Toss.

No provider authentication, durable binding, finality or payment-completion claim.
Normalization expectations remain in the unchanged literal golden-vector tests.
"""

import json
import subprocess
import sys
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import synthetic_documents as fixtures
from example_payment_lookup_router import example_results
from fake_payment_lookup import FakePaymentLookup, SyntheticLookupFault, SyntheticLookupScope
from payment_lookup import PaymentLookupService, SyntheticLookupResult
from payment_lookup_router import PaymentLookupRouter
from provider_facts import (
    NormalizedPaymentHistory, OperationBindingStore, ProviderFactsError, Unresolved,
    normalize_recorded_text,
)


class PaymentLookupRouterTests(unittest.TestCase):
    def setUp(self):
        self.bindings = OperationBindingStore()
        self.operation = fixtures.OPERATION_REF
        self.payment = fixtures.PAYMENT_REF_A
        self.scope = SyntheticLookupScope(fixtures.PROVIDER, fixtures.ACCOUNT, fixtures.ENVIRONMENT)
        self.missing = replace(self.operation, operation="unbound_synthetic_operation")
        self.operations = [self.operation, self.missing]
        self.bindings.bind(self.operation, self.payment)
        # Nonempty historical evidence makes accidental mutations observable.
        item = normalize_recorded_text(self.payment, json.dumps(fixtures.PAID)).items[0]
        self.bindings.record_capture(self.operation, self.payment, item)
        self.bindings.bind(self.operation, fixtures.PAYMENT_REF_B)

    def snapshot(self, fakes):
        return deepcopy({
            "bindings": [(op, self.bindings.lookup(op)) for op in self.operations],
            "count": self.bindings.binding_count(),
            "captures": self.bindings.recorded_captures,
            "review": self.bindings.review,
            "recordings": [dict(fake.recordings) for fake in fakes],
        })

    def fake(self, scope=None, recordings=None):
        return FakePaymentLookup(
            scope=self.scope if scope is None else scope,
            recordings={self.payment: json.dumps(fixtures.PAID)} if recordings is None else recordings,
        )

    def bind(self, operation, payment):
        self.bindings.bind(operation, payment)
        self.operations.append(operation)

    def lookup(self, router, operation, fakes, selected=None):
        before = self.snapshot(fakes)
        calls = [fake.calls for fake in fakes]
        result = router.lookup(operation)
        self.assertEqual(self.snapshot(fakes), before)
        payment = self.bindings.lookup(operation)
        for index, fake in enumerate(fakes):
            self.assertEqual(fake.calls, calls[index] + ((payment,) if index == selected else ()))
        self.assertEqual(result.operation_ref, operation)
        self.assertEqual(result.payment_ref, payment)
        self.assertEqual(result.provenance, "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY")
        return result

    def test_two_scopes_dispatch_only_to_bound_fake(self):
        # Vary each routing dimension independently. Provider/account cases
        # deliberately reuse the entire operation string and payment/order keys.
        for dimension in ("provider", "account", "environment"):
            with self.subTest(dimension=dimension):
                scope_b = replace(self.scope, **{dimension: "other-synthetic"})
                payment_b = replace(self.payment, **{dimension: "other-synthetic"})
                operation_b = (
                    replace(self.operation, operation="other_environment_operation")
                    if dimension == "environment" else replace(self.operation, **{dimension: "other-synthetic"})
                )
                self.bind(operation_b, payment_b)
                fakes = [self.fake(), self.fake(scope_b, {payment_b: json.dumps(fixtures.PAID)})]
                router = PaymentLookupRouter(self.bindings, routes={self.scope: fakes[0], scope_b: fakes[1]})
                for selected, operation in enumerate((self.operation, operation_b)):
                    result = self.lookup(router, operation, fakes, selected)
                    self.assertIsInstance(result.result, NormalizedPaymentHistory)
                    self.assertEqual(result.result.payment_ref, (self.payment, payment_b)[selected])
                self.assertEqual(fakes[0].calls, (self.payment,))
                self.assertEqual(fakes[1].calls, (payment_b,))

    def test_unresolved_scope_never_falls_back(self):
        scope_b = replace(self.scope, account="other-mid-synthetic")
        payment_b = replace(self.payment, account=scope_b.account)
        operation_b = replace(self.operation, account=scope_b.account)
        self.bind(operation_b, payment_b)
        for recording, reason in (
            (SyntheticLookupFault.TIMEOUT, "LOOKUP_TIMEOUT"),
            (SyntheticLookupFault.ERROR, "LOOKUP_ERROR"),
            (None, "LOOKUP_NOT_FOUND"),
        ):
            with self.subTest(reason=reason):
                fakes = [
                    self.fake(recordings={} if recording is None else {self.payment: recording}),
                    self.fake(scope_b, {payment_b: json.dumps(fixtures.PAID)}),
                ]
                router = PaymentLookupRouter(self.bindings, routes={self.scope: fakes[0], scope_b: fakes[1]})
                # B really has a successful recording with the same paymentKey
                # and orderId. A's unresolved outcome must never query it.
                self.assertEqual(self.lookup(router, self.operation, fakes, 0).result, Unresolved(reason))
                self.assertEqual(fakes[1].calls, ())
                self.assertIsInstance(self.lookup(router, operation_b, fakes, 1).result, NormalizedPaymentHistory)
                self.assertEqual(self.lookup(router, self.operation, fakes, 0).result, Unresolved(reason))
                self.assertEqual(fakes[0].calls, (self.payment, self.payment))
                self.assertEqual(fakes[1].calls, (payment_b,))

    def test_missing_binding_and_route_make_zero_calls(self):
        # Even a same-provider/account registration in a different environment
        # is no default route. Check every scope dimension and empty registry.
        for dimension in ("provider", "account", "environment"):
            scope = replace(self.scope, **{dimension: "unrelated-synthetic"})
            fake = self.fake(scope, {})
            router = PaymentLookupRouter(self.bindings, routes={scope: fake})
            with self.subTest(dimension=dimension):
                missing = self.lookup(router, self.missing, [fake])
                self.assertEqual(missing.result, Unresolved("BINDING_REQUIRED"))
                self.assertIsNone(missing.payment_ref)
                self.assertEqual(self.lookup(router, self.operation, [fake]).result, Unresolved("LOOKUP_ROUTE_MISSING"))
        empty = PaymentLookupRouter(self.bindings, routes={})
        self.assertEqual(self.lookup(empty, self.operation, []).result, Unresolved("LOOKUP_ROUTE_MISSING"))
        self.assertEqual(self.lookup(empty, self.missing, []).result, Unresolved("BINDING_REQUIRED"))

    def test_inconsistent_registration_rejected_without_calls(self):
        valid = self.fake()
        for dimension in ("provider", "account", "environment"):
            other = replace(self.scope, **{dimension: "other-synthetic"})
            for key, fake in ((other, self.fake()), (self.scope, self.fake(other, {}))):
                with self.subTest(dimension=dimension, key=key):
                    before = self.snapshot([valid, fake])
                    with self.assertRaises(ProviderFactsError) as caught:
                        PaymentLookupRouter(self.bindings, routes={self.scope: valid, key: fake})
                    self.assertEqual(caught.exception.code, "BINDING_MISMATCH")
                    self.assertEqual(self.snapshot([valid, fake]), before)
                    self.assertEqual((valid.calls, fake.calls), ((), ()))

    def test_invalid_registration_types_make_zero_calls(self):
        fake = self.fake()
        for routes in ({"scope": fake}, {self.scope: object()}, {self.scope: None}):
            with self.subTest(routes=routes), self.assertRaises(TypeError):
                PaymentLookupRouter(self.bindings, routes=routes)
        self.assertEqual(fake.calls, ())

    def test_route_configuration_is_copied_and_immutable(self):
        scope_b = replace(self.scope, account="other-mid-synthetic")
        payment_b = replace(self.payment, account=scope_b.account)
        operation_b = replace(self.operation, account=scope_b.account)
        self.bind(operation_b, payment_b)
        fake_a = self.fake()
        replacement = self.fake(recordings={self.payment: SyntheticLookupFault.ERROR})
        fake_b = self.fake(scope_b, {payment_b: json.dumps(fixtures.PAID)})
        routes = {self.scope: fake_a}
        router = PaymentLookupRouter(self.bindings, routes=routes)
        routes[self.scope] = replacement
        routes[scope_b] = fake_b
        fakes = [fake_a, replacement, fake_b]
        self.assertIsInstance(self.lookup(router, self.operation, fakes, 0).result, NormalizedPaymentHistory)
        self.assertEqual(self.lookup(router, operation_b, fakes).result, Unresolved("LOOKUP_ROUTE_MISSING"))
        routes.clear()
        self.assertIsInstance(self.lookup(router, self.operation, fakes, 0).result, NormalizedPaymentHistory)
        self.assertEqual(self.lookup(router, operation_b, fakes).result, Unresolved("LOOKUP_ROUTE_MISSING"))

    def test_complete_identity_and_outputs_equal_single_scope_service(self):
        # Same payment key, different order IDs must never collapse into one
        # recording, even within a registered scope.
        other_payment = replace(self.payment, order_id="other_order_synthetic")
        other_operation = replace(self.operation, operation="other_order_operation")
        self.bind(other_operation, other_payment)
        other_document = deepcopy(fixtures.PARTIAL_CANCEL)
        other_document["payment"]["orderId"] = other_payment.order_id
        for recording in (
            json.dumps(fixtures.PAID), json.dumps(fixtures.PARTIAL_CANCEL),
            json.dumps(fixtures.CANCELED_AFTER_DONE), json.dumps(fixtures.UNVERIFIED_SIGNAL),
            json.dumps(fixtures.NOT_FOUND), fixtures.FLOAT_AMOUNT_TEXT,
        ):
            with self.subTest(recording=recording):
                recordings = {self.payment: recording, other_payment: json.dumps(other_document)}
                fake = self.fake(recordings=recordings)
                direct_fake = self.fake(recordings=recordings)
                router = PaymentLookupRouter(self.bindings, routes={self.scope: fake})
                service = PaymentLookupService(self.bindings, scope=self.scope, fake=direct_fake)
                for operation in (self.operation, other_operation):
                    actual = self.lookup(router, operation, [fake, direct_fake], 0)
                    before = self.snapshot([fake, direct_fake])
                    self.assertEqual(actual, service.lookup(operation))
                    self.assertEqual(self.snapshot([fake, direct_fake]), before)
                self.assertEqual(fake.calls, (self.payment, other_payment))
                self.assertEqual(direct_fake.calls, fake.calls)

    def test_selected_service_result_is_returned_unchanged(self):
        fake = self.fake()
        router = PaymentLookupRouter(self.bindings, routes={self.scope: fake})
        expected = SyntheticLookupResult(self.operation, self.payment, Unresolved("LOOKUP_TIMEOUT"))
        with patch.object(PaymentLookupService, "lookup", return_value=expected) as selected:
            self.assertIs(router.lookup(self.operation), expected)
            selected.assert_called_once_with(self.operation)

    def test_invalid_operation_and_request_selection_are_rejected_without_calls(self):
        fake = self.fake()
        router = PaymentLookupRouter(self.bindings, routes={self.scope: fake})
        before = self.snapshot([fake])
        for invalid in (None, "operation", {}, self.payment):
            with self.subTest(invalid=invalid), self.assertRaises(ProviderFactsError) as caught:
                router.lookup(invalid)
            self.assertEqual(caught.exception.code, "INVALID_OPERATION_REF")
        for selector in ("provider", "account", "environment", "payment_ref", "url", "credentials"):
            with self.subTest(selector=selector), self.assertRaises(TypeError):
                router.lookup(self.operation, **{selector: "synthetic_untrusted"})
        self.assertEqual(fake.calls, ())
        self.assertEqual(self.snapshot([fake]), before)

    def test_unrelated_programming_error_propagates(self):
        fake = self.fake()
        router = PaymentLookupRouter(self.bindings, routes={self.scope: fake})
        before = self.snapshot([fake])
        bug = RuntimeError("synthetic programming error")
        with patch.object(fake, "lookup", side_effect=bug) as lookup:
            with self.assertRaises(RuntimeError) as caught:
                router.lookup(self.operation)
            self.assertIs(caught.exception, bug)
            lookup.assert_called_once_with(self.payment)
        self.assertEqual(self.snapshot([fake]), before)

    def test_offline_example_is_deterministic_and_synthetic(self):
        rows = example_results()
        self.assertEqual(rows, example_results())
        self.assertEqual([row["scenario"] for row in rows], [
            "PAID_A", "PAID_B", "TIMEOUT_A", "ERROR_A", "NOT_FOUND_A", "MISSING_ROUTE", "MISSING_BINDING",
        ])
        self.assertEqual([row["fake_calls"] for row in rows], [
            {"A": 1, "B": 0}, {"A": 0, "B": 1}, {"A": 1, "B": 0},
            {"A": 1, "B": 0}, {"A": 1, "B": 0}, {"A": 0, "B": 0}, {"A": 0, "B": 0},
        ])
        self.assertEqual([row["unresolved"] for row in rows[2:]], [
            "LOOKUP_TIMEOUT", "LOOKUP_ERROR", "LOOKUP_NOT_FOUND", "LOOKUP_ROUTE_MISSING", "BINDING_REQUIRED",
        ])
        self.assertEqual(rows[0]["operation_ref"]["operation"], rows[1]["operation_ref"]["operation"])
        self.assertNotEqual(rows[0]["payment_ref"]["account"], rows[1]["payment_ref"]["account"])
        for row in rows:
            self.assertEqual(row["provenance"], "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY")
            self.assertEqual(row["limitations"], "Synthetic only; no authentication, durability, finality or payment-completion claims.")
        output = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("example_payment_lookup_router.py"))],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual([json.loads(line) for line in output.stdout.splitlines()], rows)
        self.assertEqual(output.stderr, "")


if __name__ == "__main__":
    unittest.main()
