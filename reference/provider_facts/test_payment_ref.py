"""PaymentRef tuple checks for the offline provider-fact harness.

Synthetic fixture only: the tuple is the contract's payment identity, never
an event ID. No provider call, no Toss evidence.
"""

import unittest

from provider_facts import PaymentRef, ProviderFactsError, normalize_recorded_document
from synthetic_documents import PARTIAL_CANCEL, PAYMENT_REF_A


class PaymentRefTests(unittest.TestCase):
    def test_payment_ref_is_the_five_field_tuple(self):
        ref = PaymentRef(
            provider="toss-synthetic",
            account="mid_synthetic_001",
            environment="test-synthetic",
            payment_key="pay_synthetic_001",
            order_id="order_synthetic_001",
        )
        self.assertEqual(
            (ref.provider, ref.account, ref.environment, ref.payment_key, ref.order_id),
            ("toss-synthetic", "mid_synthetic_001", "test-synthetic", "pay_synthetic_001", "order_synthetic_001"),
        )
        self.assertEqual(
            ref.as_dict(),
            {
                "provider": "toss-synthetic",
                "account": "mid_synthetic_001",
                "environment": "test-synthetic",
                "payment_key": "pay_synthetic_001",
                "order_id": "order_synthetic_001",
            },
        )
        # One PaymentRef is payment identity shared by many history items;
        # it is not per-item event identity.
        history = normalize_recorded_document(PAYMENT_REF_A, PARTIAL_CANCEL)
        self.assertEqual(len(history.items), 2)
        self.assertTrue(all(item.payment_ref == ref for item in history.items))
        self.assertNotEqual(history.items[0].kind, history.items[1].kind)
        # Every field is required and non-empty.
        for field_name in ("provider", "account", "environment", "payment_key", "order_id"):
            bad = dict(ref.as_dict())
            bad[field_name] = ""
            with self.assertRaises(ProviderFactsError) as caught:
                PaymentRef(**bad)
            self.assertEqual(caught.exception.code, "INVALID_PAYMENT_REF")
            bad[field_name] = "  padded"
            with self.assertRaises(ProviderFactsError):
                PaymentRef(**bad)


if __name__ == "__main__":
    unittest.main()
