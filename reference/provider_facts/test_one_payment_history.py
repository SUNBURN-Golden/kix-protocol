"""One-payment-history checks for the offline provider-fact harness.

Synthetic fixture only: one Payment plus its cancels[] is one payment's
history of many event items, never a batch of independent payments. Every
item carries the same PaymentRef; paymentKey survives the status change.
"""

import unittest

from provider_facts import (
    ITEM_CANCEL,
    ITEM_PAYMENT,
    NormalizedPaymentHistory,
    normalize_recorded_document,
)
from synthetic_documents import (
    CANCELED_AFTER_DONE,
    PAID,
    PARTIAL_CANCEL,
    PAYMENT_REF_A,
)


class OnePaymentHistoryTests(unittest.TestCase):
    def test_cancels_are_items_of_one_payment_not_a_batch(self):
        for document, items, cancel_count in (
            (PAID, 1, 0),
            (PARTIAL_CANCEL, 2, 1),
            (CANCELED_AFTER_DONE, 2, 1),
        ):
            history = normalize_recorded_document(PAYMENT_REF_A, document)
            self.assertIsInstance(history, NormalizedPaymentHistory)
            self.assertEqual(history.payment_ref, PAYMENT_REF_A)
            self.assertEqual(len(history.items), items)
            self.assertEqual(history.items[0].kind, ITEM_PAYMENT)
            # Not a batch: every item is one history entry of the same
            # payment identity, never an independent payment.
            self.assertTrue(all(item.payment_ref == PAYMENT_REF_A for item in history.items))
            self.assertTrue(all(item.payment_ref.payment_key == "pay_synthetic_001" for item in history.items))
            self.assertEqual([item.index for item in history.items], list(range(items)))
            cancels = [item for item in history.items if item.kind == ITEM_CANCEL]
            self.assertEqual(len(cancels), cancel_count)
            for cancel in cancels:
                # A cancel is a return-kind item coexisting with the payment
                # item, never absorbed into it.
                self.assertEqual(cancel.payment_ref.payment_key, "pay_synthetic_001")
                self.assertGreater(cancel.index, 0)


if __name__ == "__main__":
    unittest.main()
