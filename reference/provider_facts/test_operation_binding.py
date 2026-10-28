"""Operation -> payment binding checks for the offline harness.

Synthetic fixture only: an OperationRef binds at most one PaymentRef. The
same operation carrying a different paymentKey is a binding conflict routed
to review — no new operation, no new order and no new capture is recorded.
"""

import unittest
from dataclasses import replace

from provider_facts import (
    BOUND,
    CONFLICT,
    REACCEPTED,
    BindingConflict,
    OperationBindingStore,
    ProviderFactsError,
    normalize_recorded_document,
)
from synthetic_documents import (
    OPERATION_REF,
    PAID,
    PAYMENT_REF_A,
    PAYMENT_REF_B,
)


class OperationBindingTests(unittest.TestCase):
    def test_same_operation_different_payment_key_is_review_conflict_without_new_capture(self):
        store = OperationBindingStore()
        history = normalize_recorded_document(PAYMENT_REF_A, PAID)

        first = store.bind(OPERATION_REF, PAYMENT_REF_A)
        self.assertEqual(first.outcome, BOUND)
        self.assertEqual(store.lookup(OPERATION_REF), PAYMENT_REF_A)
        self.assertEqual(store.binding_count(), 1)

        # Positive control: a bound operation may record an item capture.
        digest = store.record_capture(OPERATION_REF, PAYMENT_REF_A, history.items[0])
        self.assertEqual(len(store.recorded_captures), 1)
        self.assertEqual(store.recorded_captures[0]["evidence_hash"], digest)
        captures_before = len(store.recorded_captures)

        # Same operation, same five-field PaymentRef: re-accept, no growth.
        again = store.bind(OPERATION_REF, PAYMENT_REF_A)
        self.assertEqual(again.outcome, REACCEPTED)
        self.assertEqual(store.binding_count(), 1)
        self.assertEqual(len(store.review), 0)

        # Same operation, different paymentKey: review conflict. No new
        # operation binding, no new order, no new capture.
        conflicted = store.bind(OPERATION_REF, PAYMENT_REF_B)
        self.assertEqual(conflicted.outcome, CONFLICT)
        self.assertIsInstance(conflicted.conflict, BindingConflict)
        self.assertEqual(conflicted.conflict.operation_ref, OPERATION_REF)
        self.assertEqual(conflicted.conflict.bound_payment_ref, PAYMENT_REF_A)
        self.assertEqual(conflicted.conflict.incoming_payment_ref, PAYMENT_REF_B)
        self.assertEqual(store.review, [conflicted.conflict])
        self.assertEqual(store.lookup(OPERATION_REF), PAYMENT_REF_A)
        self.assertEqual(store.binding_count(), 1)
        self.assertEqual(len(store.recorded_captures), captures_before)

        # The conflicting fact cannot record a capture under this operation.
        with self.assertRaises(ProviderFactsError) as caught:
            store.record_capture(OPERATION_REF, PAYMENT_REF_B, history.items[0])
        self.assertEqual(caught.exception.code, "BINDING_REQUIRED")
        self.assertEqual(len(store.recorded_captures), captures_before)

    def test_reacceptance_requires_the_entire_payment_ref(self):
        for name in ("provider", "account", "environment", "payment_key", "order_id"):
            with self.subTest(field=name):
                store = OperationBindingStore()
                store.bind(OPERATION_REF, PAYMENT_REF_A)
                item = normalize_recorded_document(PAYMENT_REF_A, PAID).items[0]
                store.record_capture(OPERATION_REF, PAYMENT_REF_A, item)
                captures_before = list(store.recorded_captures)
                incoming = replace(PAYMENT_REF_A, **{name: getattr(PAYMENT_REF_A, name) + "_other"})
                result = store.bind(OPERATION_REF, incoming)
                self.assertEqual(result.outcome, CONFLICT)
                self.assertEqual(result.conflict.incoming_payment_ref, incoming)
                self.assertEqual(result.conflict.bound_payment_ref, PAYMENT_REF_A)
                self.assertEqual(store.review, [result.conflict])
                self.assertEqual(store.lookup(OPERATION_REF), PAYMENT_REF_A)
                self.assertEqual(store.binding_count(), 1)
                with self.assertRaises(ProviderFactsError) as caught:
                    store.record_capture(OPERATION_REF, incoming, item)
                self.assertEqual(caught.exception.code, "BINDING_REQUIRED")
                self.assertEqual(store.recorded_captures, captures_before)
                self.assertEqual(store.bind(OPERATION_REF, replace(PAYMENT_REF_A)).outcome, REACCEPTED)

    def test_initial_binding_rejects_operation_payment_scope_mismatch(self):
        for name in ("provider", "account"):
            with self.subTest(field=name):
                store = OperationBindingStore()
                incoming = replace(PAYMENT_REF_A, **{name: getattr(PAYMENT_REF_A, name) + "_other"})
                with self.assertRaises(ProviderFactsError) as caught:
                    store.bind(OPERATION_REF, incoming)
                self.assertEqual(caught.exception.code, "BINDING_MISMATCH")
                self.assertIsNone(store.lookup(OPERATION_REF))
                self.assertEqual(store.binding_count(), 0)
                self.assertEqual(store.recorded_captures, [])
                self.assertEqual(store.bind(OPERATION_REF, PAYMENT_REF_A).outcome, BOUND)


if __name__ == "__main__":
    unittest.main()
