"""Synthetic deterministic fake and runnable example; Analog, NOT Toss."""

import json
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import synthetic_documents as fixtures
from example_payment_lookup import example_results
from fake_payment_lookup import FakeLookupError, FakePaymentLookup, SyntheticLookupFault
from normalization_golden_vectors import GOLDEN_VECTORS
from payment_lookup import SyntheticLookupScope
from provider_facts import ProviderFactsError


class FakePaymentLookupTests(unittest.TestCase):
    def setUp(self):
        self.scope = SyntheticLookupScope(fixtures.PROVIDER, fixtures.ACCOUNT, fixtures.ENVIRONMENT)
        self.text = json.dumps(fixtures.PAID, ensure_ascii=False, indent=2)

    def test_recordings_are_copied_read_only_and_calls_are_snapshots(self):
        recordings = {fixtures.PAYMENT_REF_A: self.text}
        fake = FakePaymentLookup(scope=self.scope, recordings=recordings)
        recordings.clear()
        snapshot = fake.calls
        for _ in range(2):
            self.assertEqual(fake.lookup(fixtures.PAYMENT_REF_A), self.text)
        self.assertEqual(snapshot, ())
        self.assertEqual(fake.calls, (fixtures.PAYMENT_REF_A,) * 2)
        self.assertEqual(dict(fake.recordings), {fixtures.PAYMENT_REF_A: self.text})
        with self.assertRaises(TypeError):
            fake.recordings[fixtures.PAYMENT_REF_A] = "replacement"
        with self.assertRaises(AttributeError):
            fake.scope = replace(self.scope, account="other")
        with self.assertRaises(FrozenInstanceError):
            self.scope.account = "other"

    def test_complete_reference_keys_and_direct_scope_guard(self):
        fake = FakePaymentLookup(scope=self.scope, recordings={fixtures.PAYMENT_REF_A: self.text})
        for field in ("payment_key", "order_id", "provider", "account", "environment"):
            other = replace(fixtures.PAYMENT_REF_A, **{field: getattr(fixtures.PAYMENT_REF_A, field) + "_other"})
            with self.subTest(field=field):
                if field in ("payment_key", "order_id"):
                    self.assertEqual(json.loads(fake.lookup(other)), {
                        "source": "synthetic_authenticated_lookup_fixture", "outcome": "not_found",
                    })
                else:
                    with self.assertRaises(FakeLookupError):
                        fake.lookup(other)
        self.assertEqual(fake.lookup(fixtures.PAYMENT_REF_A), self.text)

    def test_fault_markers_repeat_without_consuming_recordings(self):
        for marker, error in ((SyntheticLookupFault.TIMEOUT, TimeoutError), (SyntheticLookupFault.ERROR, FakeLookupError)):
            with self.subTest(marker=marker):
                fake = FakePaymentLookup(scope=self.scope, recordings={fixtures.PAYMENT_REF_A: marker})
                for _ in range(2):
                    with self.assertRaises(error):
                        fake.lookup(fixtures.PAYMENT_REF_A)
                self.assertEqual(fake.calls, (fixtures.PAYMENT_REF_A,) * 2)
                self.assertEqual(dict(fake.recordings), {fixtures.PAYMENT_REF_A: marker})

    def test_configuration_rejects_mutable_recordings_and_invalid_references(self):
        for invalid in ({}, [], TimeoutError(), None):
            with self.subTest(invalid=invalid), self.assertRaises(TypeError):
                FakePaymentLookup(scope=self.scope, recordings={fixtures.PAYMENT_REF_A: invalid})
        with self.assertRaises(TypeError):
            FakePaymentLookup(scope=self.scope, recordings={"payment key alone": self.text})
        with self.assertRaises(TypeError):
            FakePaymentLookup(scope=None, recordings={})
        for dimension in ("provider", "account", "environment"):
            with self.subTest(dimension=dimension), self.assertRaises(ProviderFactsError) as caught:
                replace(self.scope, **{dimension: " "})
            self.assertEqual(caught.exception.code, "INVALID_SYNTHETIC_SCOPE")
        fake = FakePaymentLookup(scope=self.scope, recordings={})
        with self.assertRaises(ProviderFactsError) as caught:
            fake.lookup("payment key alone")
        self.assertEqual(caught.exception.code, "INVALID_PAYMENT_REF")
        self.assertEqual(fake.calls, ())

    def test_offline_example_is_runnable_deterministic_and_synthetic_labelled(self):
        example = Path(__file__).with_name("example_payment_lookup.py")
        run = subprocess.run([sys.executable, str(example)], check=True, capture_output=True, text=True)
        rows = [json.loads(line) for line in run.stdout.splitlines()]
        self.assertEqual(run.stderr, "")
        self.assertEqual(rows, example_results())
        self.assertEqual(rows, example_results())
        self.assertEqual([row["scenario"] for row in rows], [
            "PAID", "PARTIAL_CANCEL", "CANCELED_AFTER_DONE", "TIMEOUT",
            "NOT_FOUND", "UNSUPPORTED_METHOD", "UNVERIFIED_SOURCE",
        ])
        for row in rows:
            self.assertEqual(row["provenance"], "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY")
            self.assertEqual(row["limitations"], "Synthetic only; no authentication, durability, finality or payment-completion claims.")
            self.assertEqual(row["fake_calls"], 1)
        self.assertEqual(rows[0]["facts"], [GOLDEN_VECTORS[0]["expected_fact"]])
        self.assertEqual(rows[1]["facts"], [v["expected_fact"] for v in GOLDEN_VECTORS[1:3]])
        self.assertEqual([item["item"]["amount"] for item in rows[2]["facts"]], [15000, 15000])
        self.assertEqual([row["unresolved"] for row in rows[3:]], [
            "LOOKUP_TIMEOUT", "LOOKUP_NOT_FOUND", "METHOD_UNSUPPORTED", "UNVERIFIED_SOURCE",
        ])


if __name__ == "__main__":
    unittest.main()
