"""Synthetic service composition characterizations; Analog, NOT Toss.

Expected facts/bytes/hashes come from test-owned literals, never normalization.
No authentication, durability, finality or payment-completion claim.
"""

import json
import unittest
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

import synthetic_documents as fixtures
from fake_payment_lookup import FakePaymentLookup, SyntheticLookupFault
from normalization_golden_vectors import GOLDEN_VECTORS
from payment_lookup import PaymentLookupService, SyntheticLookupResult, SyntheticLookupScope
from provider_facts import (
    NormalizedPaymentHistory, OperationBindingStore, ProviderFactsError, Unresolved,
    evidence_hash, normalize_recorded_text,
)


class PaymentLookupTests(unittest.TestCase):
    def setUp(self):
        self.scope = SyntheticLookupScope(fixtures.PROVIDER, fixtures.ACCOUNT, fixtures.ENVIRONMENT)
        self.bindings = OperationBindingStore()
        self.operation = fixtures.OPERATION_REF
        self.payment = fixtures.PAYMENT_REF_A
        self.other_operation = replace(self.operation, operation="other_synthetic_operation")
        self.missing = replace(self.operation, operation="missing_synthetic_operation")
        self.bindings.bind(self.operation, self.payment)
        self.bindings.bind(self.other_operation, fixtures.PAYMENT_REF_B)
        # Seed historical custody with the existing helper, not an expected
        # service result. Tests below compare complete public state snapshots.
        paid = normalize_recorded_text(self.payment, json.dumps(fixtures.PAID))
        self.bindings.record_capture(self.operation, self.payment, paid.items[0])
        self.bindings.bind(self.operation, fixtures.PAYMENT_REF_B)
        self.fixture_snapshot = deepcopy({
            name: value for name, value in vars(fixtures).items()
            if name.isupper() and type(value) is dict
        })
        self.golden_snapshot = deepcopy(GOLDEN_VECTORS)

    def tearDown(self):
        for name, before in self.fixture_snapshot.items():
            self.assertEqual(getattr(fixtures, name), before)
        self.assertEqual(GOLDEN_VECTORS, self.golden_snapshot)

    def snapshot(self):
        return deepcopy({
            "bindings": [(op, self.bindings.lookup(op)) for op in (
                self.operation, self.other_operation, self.missing,
            )],
            "count": self.bindings.binding_count(),
            "captures": self.bindings.recorded_captures,
            "review": self.bindings.review,
        })

    def service(self, recording, *, scope=None, fake_scope=None, missing_recording=False):
        text = json.dumps(recording) if type(recording) is dict else recording
        fake = FakePaymentLookup(
            scope=fake_scope or scope or self.scope,
            recordings={} if missing_recording else {self.payment: text},
        )
        return PaymentLookupService(self.bindings, scope=scope or self.scope, fake=fake), fake

    def lookup_preserving_state(self, service, fake, *, operation=None, calls=1):
        operation = operation or self.operation
        before = self.snapshot()
        recordings_before = dict(fake.recordings)
        result = service.lookup(operation)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(dict(fake.recordings), recordings_before)
        self.assertEqual(fake.calls, (self.payment,) * calls)
        self.assertEqual(result.provenance, "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY")
        self.assertEqual(result.operation_ref, operation)
        self.assertEqual(result.payment_ref, self.bindings.lookup(operation))
        return result.result

    def test_missing_binding_makes_zero_calls(self):
        service, fake = self.service(fixtures.PAID, fake_scope=replace(self.scope, account="other"))
        result = self.lookup_preserving_state(service, fake, operation=self.missing, calls=0)
        self.assertEqual(result, Unresolved("BINDING_REQUIRED"))

    def test_scope_mismatch_makes_zero_calls(self):
        for dimension in ("provider", "account", "environment"):
            changed = replace(self.scope, **{dimension: getattr(self.scope, dimension) + "_other"})
            for scope, fake_scope in ((changed, changed), (self.scope, changed)):
                with self.subTest(dimension=dimension, scope=scope, fake_scope=fake_scope):
                    service, fake = self.service(fixtures.PAID, scope=scope, fake_scope=fake_scope)
                    self.assertEqual(
                        self.lookup_preserving_state(service, fake, calls=0),
                        Unresolved("BINDING_MISMATCH"),
                    )

    def test_accepted_lookup_calls_fake_once_with_complete_bound_ref(self):
        service, fake = self.service(fixtures.PAID)
        history = self.lookup_preserving_state(service, fake)
        self.assertIsInstance(history, NormalizedPaymentHistory)
        self.assertEqual(history.payment_ref, self.payment)
        self.assertEqual(len(history.items), 1)
        self.assertEqual(history.items[0].normalized_fact(), GOLDEN_VECTORS[0]["expected_fact"])
        self.assertEqual(history.receipt.as_dict(), {
            "text": "2026-10-01T12:00:05+09:00", "offset": "+09:00", "status": "OFFSET_RECORDED",
        })

    def test_all_existing_golden_vectors_through_service(self):
        for vector in GOLDEN_VECTORS:
            with self.subTest(case=vector["case"]):
                service, fake = self.service(getattr(fixtures, vector["fixture"]))
                history = self.lookup_preserving_state(service, fake)
                item = history.items[vector["item_position"]]
                self.assertEqual(item.normalized_fact(), vector["expected_fact"])
                actual_bytes = json.dumps(
                    item.normalized_fact(), sort_keys=True, ensure_ascii=False,
                    separators=(",", ":"), allow_nan=False,
                ).encode("utf-8")
                self.assertEqual(actual_bytes, vector["canonical_utf8"])
                self.assertEqual(evidence_hash(item), vector["sha256_hex"])
                self.assertIs(type(item.amount), int)

    def test_full_cancellation_preserves_capture_and_has_independent_expected_history(self):
        service, fake = self.service(fixtures.CANCELED_AFTER_DONE)
        history = self.lookup_preserving_state(service, fake)
        # Payment fields are identical to paid except the literal status;
        # the cancel expectation is transcribed separately from implementation.
        payment_fact = deepcopy(GOLDEN_VECTORS[0]["expected_fact"])
        payment_fact["item"]["status_text"] = "CANCELED"
        cancel_fact = {
            "provenance": "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY",
            "payment_ref": deepcopy(payment_fact["payment_ref"]),
            "item": {
                "kind": "cancel", "amount": 15000, "currency": "KRW", "status_text": "DONE",
                "occurred": {
                    "text": "2026-10-03T09:00:00+09:00", "offset": "+09:00", "status": "OFFSET_RECORDED",
                },
                "detail": {
                    "reason_text": "synthetic full cancel",
                    "transaction_key_text": "txkey_synthetic_cancel_002",
                },
            },
        }
        self.assertEqual([item.normalized_fact() for item in history.items], [payment_fact, cancel_fact])
        self.assertEqual([item.index for item in history.items], [0, 1])
        self.assertEqual(self.bindings.recorded_captures[0]["evidence_hash"], GOLDEN_VECTORS[0]["sha256_hex"])

    def test_unresolved_boundaries_preserve_state_and_make_one_call(self):
        missing_time = deepcopy(fixtures.PAID)
        del missing_time["payment"]["requestedAt"]
        del missing_time["payment"]["approvedAt"]
        unsupported_status = deepcopy(fixtures.PAID)
        unsupported_status["payment"]["status"] = "READY"
        cases = (
            (fixtures.TIMEOUT, "LOOKUP_TIMEOUT"),
            (fixtures.NOT_FOUND, "LOOKUP_NOT_FOUND"),
            (fixtures.UNSUPPORTED_METHOD, "METHOD_UNSUPPORTED"),
            (fixtures.NON_KRW, "CURRENCY_UNSUPPORTED"),
            (fixtures.UNVERIFIED_SIGNAL, "UNVERIFIED_SOURCE"),
            (fixtures.DIFFERENT_PAYMENT, "BINDING_MISMATCH"),
            (fixtures.FLOAT_AMOUNT_TEXT, "FLOAT_TOKEN"),
            (unsupported_status, "STATUS_UNSUPPORTED"),
            (missing_time, "TIMESTAMP_MISSING"),
            ("not JSON", "DOCUMENT_JSON"),
            ("[]", "DOCUMENT_TYPE"),
        )
        for recording, reason in cases:
            with self.subTest(reason=reason):
                service, fake = self.service(recording)
                self.assertEqual(self.lookup_preserving_state(service, fake), Unresolved(reason))
        service, fake = self.service(None, missing_recording=True)
        self.assertEqual(self.lookup_preserving_state(service, fake), Unresolved("LOOKUP_NOT_FOUND"))

    def test_timeout_and_error_do_not_retry_or_fallback(self):
        for fault, reason in (
            (SyntheticLookupFault.TIMEOUT, "LOOKUP_TIMEOUT"),
            (SyntheticLookupFault.ERROR, "LOOKUP_ERROR"),
        ):
            with self.subTest(fault=fault):
                fake = FakePaymentLookup(scope=self.scope, recordings={
                    self.payment: fault,
                    fixtures.PAYMENT_REF_B: json.dumps(fixtures.DIFFERENT_PAYMENT),
                })
                service = PaymentLookupService(self.bindings, scope=self.scope, fake=fake)
                with patch("payment_lookup.normalize_recorded_text", side_effect=AssertionError("must not normalize fault")):
                    self.assertEqual(self.lookup_preserving_state(service, fake), Unresolved(reason))

    def test_invalid_operation_and_request_selection_are_rejected_without_calls(self):
        service, fake = self.service(fixtures.PAID)
        before = self.snapshot()
        for invalid in (None, "operation", {}, self.payment):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ProviderFactsError) as caught:
                    service.lookup(invalid)
                self.assertEqual(caught.exception.code, "INVALID_OPERATION_REF")
        for key in ("url", "credentials", "account", "provider", "payment_ref"):
            with self.subTest(key=key), self.assertRaises(TypeError):
                service.lookup(self.operation, **{key: "synthetic_untrusted_value"})
        self.assertEqual(fake.calls, ())
        self.assertEqual(self.snapshot(), before)

    def test_unrelated_programming_error_is_not_hidden(self):
        service, fake = self.service(fixtures.PAID)
        before = self.snapshot()
        bug = RuntimeError("synthetic programming error")
        with patch.object(fake, "lookup", side_effect=bug) as lookup:
            with self.assertRaises(RuntimeError) as caught:
                service.lookup(self.operation)
            self.assertIs(caught.exception, bug)
            lookup.assert_called_once_with(self.payment)
        self.assertEqual(self.snapshot(), before)

    def test_repeat_explicit_lookup_is_fresh_and_cannot_relabel_provenance(self):
        service, fake = self.service(fixtures.PARTIAL_CANCEL)
        result = self.lookup_preserving_state(service, fake)
        result.items[0].detail["timestamps"]["approvedAt"]["text"] = "caller mutation"
        result.items[1].detail.clear()
        again = self.lookup_preserving_state(service, fake, calls=2)
        for position, vector in enumerate(GOLDEN_VECTORS[1:3]):
            self.assertEqual(again.items[position].normalized_fact(), vector["expected_fact"])
        labelled = service.lookup(self.operation)
        with self.assertRaises(FrozenInstanceError):
            labelled.provenance = "provider verified"
        with self.assertRaises(TypeError):
            SyntheticLookupResult(self.operation, self.payment, result, provenance="provider verified")


if __name__ == "__main__":
    unittest.main()
