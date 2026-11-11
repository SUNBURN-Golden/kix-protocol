"""Cancellation regressions for the synthetic, offline provider-fact harness.

MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY: Analog, NOT Toss. Integer boundaries
characterize representation, not refund eligibility or product policy.
"""

import json
import unittest
from copy import deepcopy

from provider_facts import (
    AMOUNT_RANGE,
    AMOUNT_SCALE,
    AMOUNT_SIGN,
    FLOAT_TOKEN,
    KRW_U128_MAX,
    STATUS_UNSUPPORTED,
    NormalizedPaymentHistory,
    ProviderFactsError,
    Unresolved,
    evidence_hash,
    normalize_recorded_document,
    normalize_recorded_text,
    parse_recorded_document,
)
from synthetic_documents import MULTIPLE_CANCELS, PAID, PARTIAL_CANCEL, PAYMENT_REF_A


MISSING = object()


class CancelBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.fixtures_before = deepcopy((PAID, PARTIAL_CANCEL, MULTIPLE_CANCELS))

    def tearDown(self):
        self.assertEqual((PAID, PARTIAL_CANCEL, MULTIPLE_CANCELS), self.fixtures_before)

    def _with_invalid_cancel(self, field, value, position):
        document = deepcopy(MULTIPLE_CANCELS)
        entry = deepcopy(PARTIAL_CANCEL["payment"]["cancels"][0])
        if value is MISSING:
            del entry[field]
        else:
            entry[field] = value
        document["payment"]["cancels"].insert(position, entry)
        return document

    def _retain_valid_histories(self):
        retained = []
        for fixture in (PAID, PARTIAL_CANCEL, MULTIPLE_CANCELS):
            document = deepcopy(fixture)
            before = deepcopy(document)
            history = normalize_recorded_document(PAYMENT_REF_A, document)
            self.assertIsInstance(history, NormalizedPaymentHistory)
            self.assertEqual(document, before)
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

    def _assert_rejected(self, document, reason, *, text=None, document_entry=True, text_entry=True):
        retained = self._retain_valid_histories()
        before = deepcopy(document)
        if text is None:
            text = json.dumps(document)
        text_before = text
        calls = []
        if document_entry:
            calls.insert(0, (
                "document", lambda: normalize_recorded_document(PAYMENT_REF_A, document)
            ))
        if text_entry:
            calls.append(("text", lambda: normalize_recorded_text(PAYMENT_REF_A, text)))
        for entry_point, call in calls:
            previous = None
            for repetition in range(2):
                with self.subTest(entry_point=entry_point, repetition=repetition):
                    result = call()
                    self.assertEqual(result, Unresolved(reason))
                    self.assertNotIsInstance(result, NormalizedPaymentHistory)
                    self.assertFalse(hasattr(result, "items"), "no partial history returned")
                    if repetition:
                        self.assertEqual(result, previous)
                    previous = result
                    self.assertEqual(document, before)
                    self.assertEqual(text, text_before)
                    self._assert_histories_preserved(retained)

    def test_cancel_amount_types_sign_and_range(self):
        cases = (
            ("true", True, AMOUNT_SCALE),
            ("false", False, AMOUNT_SCALE),
            ("string", "5000", AMOUNT_SCALE),
            ("null", None, AMOUNT_SCALE),
            ("missing", MISSING, AMOUNT_SCALE),
            ("negative_one", -1, AMOUNT_SIGN),
            ("negative_ordinary", -5000, AMOUNT_SIGN),
            ("above_u128", KRW_U128_MAX + 1, AMOUNT_RANGE),
        )
        for label, amount, reason in cases:
            for position in range(3):
                with self.subTest(amount=label, position=position):
                    document = self._with_invalid_cancel("cancelAmount", amount, position)
                    self._assert_rejected(document, reason)

        # Characterize already-materialized floats separately from JSON tokens.
        for position in range(3):
            with self.subTest(amount="python_float", position=position):
                document = self._with_invalid_cancel("cancelAmount", 5000.0, position)
                self._assert_rejected(document, AMOUNT_SCALE, text_entry=False)

    def test_cancel_json_decimal_and_exponent_tokens(self):
        placeholder = "__synthetic_cancel_numeric_token__"
        for token in ("5000.0", "5000.5", "5e3", "5E+3"):
            for position in range(3):
                with self.subTest(token=token, position=position):
                    document = self._with_invalid_cancel("cancelAmount", placeholder, position)
                    before = deepcopy(document)
                    serialized = json.dumps(document)
                    quoted = json.dumps(placeholder)
                    self.assertEqual(serialized.count(quoted), 1)
                    # Insert literal numeric text; never build a Python float
                    # or parse with default json.loads on this rejection path.
                    text = serialized.replace(quoted, token, 1)
                    for _ in range(2):
                        with self.assertRaises(ProviderFactsError) as caught:
                            parse_recorded_document(text)
                        self.assertEqual(caught.exception.code, FLOAT_TOKEN)
                        self.assertEqual(document, before)
                        self.assertEqual(text, serialized.replace(quoted, token, 1))
                    self._assert_rejected(document, FLOAT_TOKEN, text=text, document_entry=False)

    def test_cancel_integer_technical_boundaries(self):
        # Existing representation bounds only. No refund-policy inference,
        # including no cumulative-refund or zero-refund eligibility claim.
        for amount in (0, 1, 2**53 + 1, KRW_U128_MAX - 1, KRW_U128_MAX):
            with self.subTest(amount=amount):
                document = deepcopy(PARTIAL_CANCEL)
                document["payment"]["totalAmount"] = max(15000, amount)
                document["payment"]["cancels"][0]["cancelAmount"] = amount
                before = deepcopy(document)
                text = json.dumps(document)
                text_before = text
                parsed = parse_recorded_document(text)
                self.assertEqual(parsed, before)
                parsed_amount = parsed["payment"]["cancels"][0]["cancelAmount"]
                self.assertIs(type(parsed_amount), int)
                self.assertEqual(parsed_amount, amount)
                direct = normalize_recorded_document(PAYMENT_REF_A, document)
                self.assertEqual(document, before)
                from_text = normalize_recorded_text(PAYMENT_REF_A, text)
                self.assertEqual(text, text_before)
                for history in (direct, from_text):
                    self.assertIsInstance(history, NormalizedPaymentHistory)
                    self.assertEqual(len(history.items), 2)
                    payment, cancel = history.items
                    self.assertEqual(payment.amount, max(15000, amount))
                    self.assertIs(type(cancel.amount), int)
                    self.assertEqual(cancel.amount, amount)
                    self.assertEqual(cancel.normalized_fact()["item"]["amount"], amount)
                    self.assertEqual(history.item_hashes(), [evidence_hash(item) for item in history.items])
                self.assertEqual(direct, from_text)
                self.assertEqual(
                    [item.normalized_fact() for item in direct.items],
                    [item.normalized_fact() for item in from_text.items],
                )
                self.assertEqual(direct.item_hashes(), from_text.item_hashes())
                self.assertEqual(document, before)

    def test_unsupported_cancel_status_positions(self):
        # Broader single-entry status-type coverage lives in
        # NormalizeVerifiedOnlyTests; these isolate mixed-history positions.
        for label, status in (("ready", "READY"), ("missing", MISSING), ("null", None)):
            for position in range(3):
                with self.subTest(status=label, position=position):
                    document = self._with_invalid_cancel("cancelStatus", status, position)
                    self._assert_rejected(document, STATUS_UNSUPPORTED)


if __name__ == "__main__":
    unittest.main()
