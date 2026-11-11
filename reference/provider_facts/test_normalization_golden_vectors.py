"""Literal oracle checks: synthetic fixture representation; Analog, NOT Toss.

Expectations are source-informed but specified separately from normalization
and its canonicalization helper. No operational hash-schema adoption follows.
"""

import hashlib
import json
import unittest
from copy import deepcopy

import synthetic_documents as fixtures
from normalization_golden_vectors import GOLDEN_VECTORS
from provider_facts import (
    NormalizedPaymentHistory,
    PaymentRef,
    evidence_hash,
    normalize_recorded_document,
    normalize_recorded_text,
)


def canonical_utf8(fact):
    # Serialize the actual result for comparison to independently transcribed
    # literal bytes. Never use this helper to manufacture a golden expectation.
    return json.dumps(
        fact, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def reverse_keys(value):
    if isinstance(value, dict):
        return {key: reverse_keys(value[key]) for key in reversed(value)}
    if isinstance(value, list):
        return [reverse_keys(item) for item in value]
    return value


class NormalizationGoldenVectorTests(unittest.TestCase):
    def setUp(self):
        self.vectors_before = deepcopy(GOLDEN_VECTORS)
        self.fixtures_before = {
            vector["fixture"]: deepcopy(getattr(fixtures, vector["fixture"]))
            for vector in GOLDEN_VECTORS
        }

    def tearDown(self):
        self.assertEqual(GOLDEN_VECTORS, self.vectors_before)
        for name, before in self.fixtures_before.items():
            self.assertEqual(getattr(fixtures, name), before)

    def assert_golden_item(self, history, vector):
        self.assertIsInstance(history, NormalizedPaymentHistory)
        item = history.items[vector["item_position"]]
        self.assertEqual(item.normalized_fact(), vector["expected_fact"])
        self.assertEqual(canonical_utf8(item.normalized_fact()), vector["canonical_utf8"])
        self.assertEqual(evidence_hash(item), vector["sha256_hex"])

    def test_literal_facts_bytes_and_digests(self):
        for vector in GOLDEN_VECTORS:
            with self.subTest(case=vector["case"]):
                literal = vector["canonical_utf8"]
                self.assertEqual(json.loads(literal.decode("utf-8")), vector["expected_fact"])
                self.assertRegex(vector["sha256_hex"], r"\A[0-9a-f]{64}\Z")
                self.assertEqual(hashlib.sha256(literal).hexdigest(), vector["sha256_hex"])
                document = deepcopy(getattr(fixtures, vector["fixture"]))
                for history in (
                    normalize_recorded_document(fixtures.PAYMENT_REF_A, document),
                    normalize_recorded_text(fixtures.PAYMENT_REF_A, json.dumps(document)),
                ):
                    self.assert_golden_item(history, vector)

    def test_json_whitespace_and_key_order_invariance(self):
        for vector in GOLDEN_VECTORS:
            document = deepcopy(getattr(fixtures, vector["fixture"]))
            variants = (
                json.dumps(document, ensure_ascii=False, separators=(",", ":")),
                json.dumps(document, ensure_ascii=False, indent=4),
                json.dumps(reverse_keys(document), ensure_ascii=False, indent=2),
            )
            for variant, text in enumerate(variants):
                with self.subTest(case=vector["case"], variant=variant):
                    self.assert_golden_item(
                        normalize_recorded_text(fixtures.PAYMENT_REF_A, text), vector
                    )

    def test_included_fields_change_fact_and_hash(self):
        # Both items have a complete literal baseline in PARTIAL_CANCEL.
        vectors = tuple(v for v in GOLDEN_VECTORS if v["fixture"] == "PARTIAL_CANCEL")
        cases = (
            "provider", "account", "environment", "payment_key", "order_id",
            "payment_amount", "cancel_amount", "payment_occurrence", "cancel_occurrence",
        )
        for field in cases:
            document = deepcopy(fixtures.PARTIAL_CANCEL)
            expected = [deepcopy(v["expected_fact"]) for v in vectors]
            reference = deepcopy(expected[0]["payment_ref"])
            if field in reference:
                value = reference[field] + "_changed"
                reference[field] = value
                for fact in expected:
                    fact["payment_ref"][field] = value
                document_field = {"payment_key": "paymentKey", "order_id": "orderId"}.get(field)
                if document_field:
                    document["payment"][document_field] = value
                affected = (0, 1)
            elif field == "payment_amount":
                document["payment"]["totalAmount"] = 15001
                expected[0]["item"]["amount"] = 15001
                affected = (0,)
            elif field == "cancel_amount":
                document["payment"]["cancels"][0]["cancelAmount"] = 5001
                expected[1]["item"]["amount"] = 5001
                affected = (1,)
            elif field == "payment_occurrence":
                # Equivalent instant and same offset; raw spelling still matters.
                value = "2026-10-01T12:00:00.000+09:00"
                document["payment"]["approvedAt"] = value
                expected[0]["item"]["occurred"]["text"] = value
                expected[0]["item"]["detail"]["timestamps"]["approvedAt"]["text"] = value
                affected = (0,)
            else:
                value = "2026-10-02T09:00:00.000+09:00"
                document["payment"]["cancels"][0]["canceledAt"] = value
                expected[1]["item"]["occurred"]["text"] = value
                affected = (1,)
            payment_ref = PaymentRef(**reference)
            for entry, history in (
                ("document", normalize_recorded_document(payment_ref, document)),
                ("text", normalize_recorded_text(payment_ref, json.dumps(document))),
            ):
                with self.subTest(field=field, entry=entry):
                    self.assertIsInstance(history, NormalizedPaymentHistory)
                    self.assertEqual(len(history.items), 2)
                    for position, (item, vector, fact) in enumerate(zip(history.items, vectors, expected)):
                        self.assertEqual(item.normalized_fact(), fact)
                        if position in affected:
                            self.assertNotEqual(item.normalized_fact(), vector["expected_fact"])
                            self.assertNotEqual(evidence_hash(item), vector["sha256_hex"])
                        else:
                            self.assert_golden_item(history, vector)


if __name__ == "__main__":
    unittest.main()
