"""Integer-KRW amount checks for the offline provider-fact harness.

Synthetic fixture only: JSON number text is never parsed through an f64
path and out-of-scale, out-of-sign and out-of-range amounts stay
unresolved. The u128 ceiling is the locked kernel's bound, not a product
policy value.
"""

import unittest

from provider_facts import (
    AMOUNT_RANGE,
    AMOUNT_SCALE,
    AMOUNT_SIGN,
    FLOAT_TOKEN,
    KRW_U128_MAX,
    ProviderFactsError,
    Unresolved,
    normalize_recorded_document,
    normalize_recorded_text,
    parse_recorded_document,
)
from synthetic_documents import (
    EXPONENT_AMOUNT_TEXT,
    FLOAT_AMOUNT_OBJECT,
    FLOAT_AMOUNT_TEXT,
    FRACTION_AMOUNT_TEXT,
    MAX_KRW_AMOUNT,
    NEGATIVE_AMOUNT,
    OVER_RANGE_AMOUNT,
    PAID,
    PAYMENT_REF_A,
)


class IntegerKrwTests(unittest.TestCase):
    def test_integer_krw_rejects_float_scale_sign_and_range_paths(self):
        # No lexeme ever reaches an f64: JSON float tokens fail at parse.
        for text in (FLOAT_AMOUNT_TEXT, EXPONENT_AMOUNT_TEXT, FRACTION_AMOUNT_TEXT):
            with self.assertRaises(ProviderFactsError) as caught:
                parse_recorded_document(text)
            self.assertEqual(caught.exception.code, FLOAT_TOKEN)
            # The normalize helper records the same fact as unresolved.
            self.assertEqual(normalize_recorded_text(PAYMENT_REF_A, text), Unresolved(FLOAT_TOKEN))
        # A programmatic float/bool/string amount is out of scale.
        for bad in (FLOAT_AMOUNT_OBJECT,):
            self.assertEqual(normalize_recorded_document(PAYMENT_REF_A, bad), Unresolved(AMOUNT_SCALE))
        for mutated in (True, "1500"):
            document = dict(PAID)
            payment = dict(document["payment"])
            payment["totalAmount"] = mutated
            document["payment"] = payment
            self.assertEqual(
                normalize_recorded_document(PAYMENT_REF_A, document),
                Unresolved(AMOUNT_SCALE),
            )
        # Sign and range.
        self.assertEqual(normalize_recorded_document(PAYMENT_REF_A, NEGATIVE_AMOUNT), Unresolved(AMOUNT_SIGN))
        self.assertEqual(normalize_recorded_document(PAYMENT_REF_A, OVER_RANGE_AMOUNT), Unresolved(AMOUNT_RANGE))
        # Positive controls: ordinary and kernel-boundary integer amounts.
        self.assertEqual(normalize_recorded_document(PAYMENT_REF_A, PAID).items[0].amount, 15000)
        boundary = normalize_recorded_document(PAYMENT_REF_A, MAX_KRW_AMOUNT)
        self.assertEqual(boundary.items[0].amount, KRW_U128_MAX)
        # Zero is not an out-of-sign amount in this synthetic harness.
        zero = dict(PAID)
        payment = dict(zero["payment"])
        payment["totalAmount"] = 0
        zero["payment"] = payment
        self.assertEqual(normalize_recorded_document(PAYMENT_REF_A, zero).items[0].amount, 0)


if __name__ == "__main__":
    unittest.main()
