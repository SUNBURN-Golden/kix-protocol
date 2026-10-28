"""Existing structural rejection paths in the offline provider-fact harness.

MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY — Analog, NOT Toss. Exact error codes,
timestamp selection and all-or-exception behavior are source-informed fixture
characterizations, not provider or product policy. Duplicate-key handling and
timestamp-calendar semantics remain undecided.
"""

import json
import unittest
from copy import deepcopy

from provider_facts import (
    ITEM_CANCEL,
    ITEM_PAYMENT,
    NormalizedPaymentHistory,
    ProviderFactsError,
    normalize_recorded_document,
    normalize_recorded_text,
    parse_recorded_document,
    raw_timestamp,
)
from synthetic_documents import (
    MULTIPLE_CANCELS,
    OFFSET_LESS_CREATED_AT,
    PAID,
    PARTIAL_CANCEL,
    PAYMENT_REF_A,
)


MISSING = object()
FIXTURES = (PAID, PARTIAL_CANCEL, MULTIPLE_CANCELS, OFFSET_LESS_CREATED_AT)
OCCURRENCE_FIELDS = ("approvedAt", "requestedAt", "createdAt")
INVALID_TIMESTAMPS = (None, False, 1, [], {}, "", " ", "\t\n", " padded ")


class StructuralRejectionTests(unittest.TestCase):
    def setUp(self):
        self.fixtures_before = deepcopy(FIXTURES)

    def tearDown(self):
        self.assertEqual(FIXTURES, self.fixtures_before)

    def _set_field(self, target, field, value):
        if value is MISSING:
            target.pop(field, None)
        else:
            target[field] = deepcopy(value)

    def _valid_history(self, document):
        before = deepcopy(document)
        text = json.dumps(document)
        text_before = text
        self.assertEqual(parse_recorded_document(text), before)
        direct = normalize_recorded_document(PAYMENT_REF_A, document)
        self.assertEqual(document, before)
        from_text = normalize_recorded_text(PAYMENT_REF_A, text)
        self.assertEqual(text, text_before)
        for history in (direct, from_text):
            self.assertIsInstance(history, NormalizedPaymentHistory)
            self.assertEqual(history.payment_ref, PAYMENT_REF_A)
            cancel_count = len(document["payment"].get("cancels") or [])
            self.assertEqual(len(history.items), 1 + cancel_count)
            self.assertEqual(
                [item.kind for item in history.items],
                [ITEM_PAYMENT] + [ITEM_CANCEL] * cancel_count,
            )
            self.assertTrue(all(item.payment_ref == PAYMENT_REF_A for item in history.items))
        self.assertEqual(direct, from_text)
        self.assertEqual(
            [item.normalized_fact() for item in direct.items],
            [item.normalized_fact() for item in from_text.items],
        )
        self.assertEqual(direct.item_hashes(), from_text.item_hashes())
        self.assertEqual(document, before)
        return direct

    def _retain_valid_histories(self):
        retained = []
        for fixture in FIXTURES:
            document = deepcopy(fixture)
            before = deepcopy(document)
            history = self._valid_history(document)
            retained.append({
                "document": document,
                "before": before,
                "history": history,
                "snapshot": deepcopy(history),
                "facts": deepcopy([item.normalized_fact() for item in history.items]),
                "hashes": history.item_hashes(),
            })
        return retained

    def _assert_histories_preserved(self, retained):
        for saved in retained:
            history = saved["history"]
            self.assertEqual(history, saved["snapshot"])
            self.assertEqual([item.normalized_fact() for item in history.items], saved["facts"])
            self.assertEqual(history.item_hashes(), saved["hashes"])
            for fresh in (
                normalize_recorded_document(PAYMENT_REF_A, saved["document"]),
                normalize_recorded_text(PAYMENT_REF_A, json.dumps(saved["document"])),
            ):
                self.assertEqual(fresh, saved["snapshot"])
                self.assertEqual([item.normalized_fact() for item in fresh.items], saved["facts"])
                self.assertEqual(fresh.item_hashes(), saved["hashes"])
            self.assertEqual(saved["document"], saved["before"])

    def _assert_rejected(self, code, calls, inputs):
        retained = self._retain_valid_histories()
        before = deepcopy(inputs)
        for entry_point, call in calls:
            with self.subTest(entry_point=entry_point):
                sentinel = object()
                result = sentinel
                with self.assertRaises(ProviderFactsError) as caught:
                    result = call()
                self.assertEqual(caught.exception.code, code)
                # Assignment never completes, including when malformed
                # cancellation entries follow valid entries: no partial return.
                self.assertIs(result, sentinel)
                self.assertEqual(inputs, before)
                self._assert_histories_preserved(retained)

    def _assert_text_rejected(self, text, code):
        self._assert_rejected(code, (
            ("parse", lambda: parse_recorded_document(text)),
            ("text", lambda: normalize_recorded_text(PAYMENT_REF_A, text)),
        ), (text,))

    def _assert_document_rejected(self, document, code):
        before = deepcopy(document)
        text = json.dumps(document)
        # Valid JSON object structure parses; the error belongs to normalization.
        self.assertEqual(parse_recorded_document(text), before)
        self.assertEqual(document, before)
        self._assert_rejected(code, (
            ("document", lambda: normalize_recorded_document(PAYMENT_REF_A, document)),
            ("text", lambda: normalize_recorded_text(PAYMENT_REF_A, text)),
        ), (document, text))

    def test_malformed_json(self):
        for text in ("", '{"source":', '{"source": 1,}', json.dumps(PAID) + " garbage"):
            with self.subTest(text=text):
                self._assert_text_rejected(text, "DOCUMENT_JSON")

    def test_document_type(self):
        for value in (None, [], "document", 1, True, False):
            with self.subTest(root=value):
                text = json.dumps(value)
                self._assert_rejected("DOCUMENT_TYPE", (
                    ("parse", lambda: parse_recorded_document(text)),
                    ("text", lambda: normalize_recorded_text(PAYMENT_REF_A, text)),
                    ("document", lambda: normalize_recorded_document(PAYMENT_REF_A, value)),
                ), (value, text))
        # Materialized objects and bytes are not JSON text arguments.
        for value in (None, {}, [], 1, True, b"{}"):
            with self.subTest(non_string_argument=value):
                self._assert_text_rejected(value, "DOCUMENT_TYPE")

    def test_nonfinite_constants(self):
        placeholder = "__synthetic_nonfinite_constant__"
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                document = deepcopy(PAID)
                document["payment"]["totalAmount"] = placeholder
                before = deepcopy(document)
                serialized = json.dumps(document)
                quoted = json.dumps(placeholder)
                self.assertEqual(serialized.count(quoted), 1)
                # Insert the literal token without constructing non-finite floats.
                text = serialized.replace(quoted, token, 1)
                self._assert_text_rejected(text, "UNEXPECTED_CONSTANT")
                self.assertEqual(document, before)

    def test_recorded_outcome(self):
        for outcome in (MISSING, None, "", "unknown_synthetic_outcome", 1, False, [], {}):
            with self.subTest(outcome=outcome):
                document = deepcopy(PAID)
                self._set_field(document, "outcome", outcome)
                self._assert_document_rejected(document, "RECORDED_OUTCOME_UNKNOWN")

    def test_payment_type(self):
        for payment in (MISSING, None, [], "payment", 1, True, False):
            with self.subTest(payment=payment):
                document = deepcopy(PAID)
                self._set_field(document, "payment", payment)
                self._assert_document_rejected(document, "DOCUMENT_TYPE")

    def test_timestamp_type(self):
        for value in INVALID_TIMESTAMPS:
            with self.subTest(raw_timestamp=value):
                self._assert_rejected("TIMESTAMP_TYPE", (
                    ("raw_timestamp", lambda: raw_timestamp(value)),
                ), (value,))
        for value in (MISSING,) + INVALID_TIMESTAMPS:
            with self.subTest(recorded_at=value):
                document = deepcopy(PAID)
                self._set_field(document, "recorded_at", value)
                self._assert_document_rejected(document, "TIMESTAMP_TYPE")

        # A nonempty whitespace field reaches raw_timestamp. Exercise each
        # field both as the selected occurrence and as retained detail text.
        for field in OCCURRENCE_FIELDS:
            for selected in (True, False):
                for value in (" ", "\t\n", " 2026-10-01T12:00:00+09:00"):
                    with self.subTest(field=field, selected=selected, value=value):
                        document = deepcopy(PAID)
                        payment = document["payment"]
                        if selected:
                            for name in OCCURRENCE_FIELDS:
                                payment.pop(name, None)
                        elif field == "approvedAt":
                            # approvedAt always wins selection; it cannot be
                            # a non-selected retained field in this fixture.
                            continue
                        payment[field] = value
                        self._assert_document_rejected(document, "TIMESTAMP_TYPE")

    def test_timestamp_missing(self):
        # All candidates are absent or skipped; none is coerced to text.
        for value in (MISSING, None, False, 1, [], {}, ""):
            with self.subTest(all_occurrence_fields=value):
                document = deepcopy(PAID)
                for field in OCCURRENCE_FIELDS:
                    self._set_field(document["payment"], field, value)
                self._assert_document_rejected(document, "TIMESTAMP_MISSING")

    def test_timestamp_fallback_controls(self):
        # Source-informed priority/fallback controls using valid timestamp text.
        for index, selected in enumerate(OCCURRENCE_FIELDS):
            for skipped in (MISSING, None, False, 1, [], {}, ""):
                with self.subTest(selected=selected, skipped=skipped):
                    document = deepcopy(OFFSET_LESS_CREATED_AT)
                    payment = document["payment"]
                    for field in OCCURRENCE_FIELDS[:index]:
                        self._set_field(payment, field, skipped)
                    history = self._valid_history(document)
                    self.assertEqual(history.items[0].occurred, raw_timestamp(payment[selected]))
                    expected = {
                        name: raw_timestamp(payment[name]).as_dict()
                        for name in OCCURRENCE_FIELDS[index:]
                    }
                    self.assertEqual(history.items[0].detail["timestamps"], expected)

    def test_cancels_type(self):
        for cancels in ({}, "cancels", 1, True, False):
            with self.subTest(cancels=cancels):
                document = deepcopy(PAID)
                document["payment"]["cancels"] = deepcopy(cancels)
                self._assert_document_rejected(document, "CANCELS_TYPE")

    def test_missing_null_and_empty_cancels_controls(self):
        # Current acceptance only; not a new nullable-provider schema contract.
        baseline = self._valid_history(deepcopy(PAID))
        for cancels in (MISSING, None, []):
            with self.subTest(cancels=cancels):
                document = deepcopy(PAID)
                self._set_field(document["payment"], "cancels", cancels)
                history = self._valid_history(document)
                self.assertEqual(history, baseline)
                self.assertEqual(history.item_hashes(), baseline.item_hashes())

    def test_cancel_item_type(self):
        for entry in (None, [], "cancel", 1, True, False):
            for position in range(3):
                with self.subTest(entry=entry, position=position):
                    document = deepcopy(MULTIPLE_CANCELS)
                    document["payment"]["cancels"].insert(position, deepcopy(entry))
                    self._assert_document_rejected(document, "CANCEL_ITEM_TYPE")

    def test_cancel_timestamp_rejections(self):
        for value in (MISSING,) + INVALID_TIMESTAMPS:
            for position in range(3):
                with self.subTest(canceledAt=value, position=position):
                    document = deepcopy(MULTIPLE_CANCELS)
                    entry = deepcopy(PARTIAL_CANCEL["payment"]["cancels"][0])
                    self._set_field(entry, "canceledAt", value)
                    document["payment"]["cancels"].insert(position, entry)
                    self._assert_document_rejected(document, "TIMESTAMP_TYPE")


if __name__ == "__main__":
    unittest.main()
