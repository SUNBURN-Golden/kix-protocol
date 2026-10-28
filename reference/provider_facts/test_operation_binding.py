"""Operation -> payment binding checks for the offline harness.

MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY — source-informed synthetic
characterization; Analog, NOT Toss. No provider conformance claim.

Synthetic fixture only: an OperationRef binds at most one PaymentRef. The
same operation carrying a different paymentKey is a binding conflict routed
to review — no new operation, no new order and no new capture is recorded.
"""

import unittest
from copy import deepcopy
from dataclasses import replace

from provider_facts import (
    BOUND,
    CONFLICT,
    REACCEPTED,
    BindingConflict,
    OperationBindingStore,
    OperationRef,
    PaymentRef,
    ProviderFactsError,
    evidence_hash,
    normalize_recorded_document,
)
from synthetic_documents import (
    DIFFERENT_PAYMENT,
    OPERATION_REF,
    PAID,
    PAYMENT_REF_A,
    PAYMENT_REF_B,
)


class OperationBindingTests(unittest.TestCase):
    def _snapshot(self, store, operations):
        # Public APIs only; deep-copy nested capture/review evidence so an
        # in-place mutation cannot change the baseline we compare against.
        return deepcopy({
            "bindings": [(op, store.lookup(op)) for op in operations],
            "binding_count": store.binding_count(),
            "review": store.review,
            "recorded_captures": store.recorded_captures,
        })

    def _assert_rejected_unchanged(self, store, operations, code, call, *args):
        before = self._snapshot(store, operations)
        with self.assertRaises(ProviderFactsError) as caught:
            call(*args)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(self._snapshot(store, operations), before)

    def _assert_capture(self, store, operations, operation, payment, item):
        expected = self._snapshot(store, operations)
        digest = evidence_hash(item)
        expected["recorded_captures"].append({
            "operation": operation.operation,
            "payment_key": payment.payment_key,
            "item_index": item.index,
            "evidence_hash": digest,
        })
        self.assertEqual(store.record_capture(operation, payment, item), digest)
        self.assertEqual(self._snapshot(store, operations), expected)

    def _scope_pairs(self):
        return (
            (OPERATION_REF, PAYMENT_REF_A),
            (OperationRef("other-synthetic", OPERATION_REF.account, OPERATION_REF.operation),
             replace(PAYMENT_REF_A, provider="other-synthetic")),
            (OperationRef(OPERATION_REF.provider, "other-mid", OPERATION_REF.operation),
             replace(PAYMENT_REF_A, account="other-mid")),
            (replace(OPERATION_REF, operation="other-operation"), PAYMENT_REF_B),
        )

    def _operations(self):
        return tuple(op for op, _ in self._scope_pairs()) + (
            replace(OPERATION_REF, operation="unbound-operation"),
        )

    def _item(self, payment):
        document = deepcopy(DIFFERENT_PAYMENT if payment == PAYMENT_REF_B else PAID)
        return normalize_recorded_document(payment, document).items[0]

    def _populated_store(self):
        store = OperationBindingStore()
        operations = self._operations()
        for operation, payment in self._scope_pairs():
            self.assertEqual(store.bind(operation, payment).outcome, BOUND)
            self._assert_capture(store, operations, operation, payment, self._item(payment))
        conflict = store.bind(OPERATION_REF, PAYMENT_REF_B)
        self.assertEqual(conflict.outcome, CONFLICT)
        self.assertEqual(store.review, [BindingConflict(OPERATION_REF, PAYMENT_REF_A, PAYMENT_REF_B)])
        self.assertEqual(store.binding_count(), 4)
        self.assertEqual(len(store.recorded_captures), 4)
        return store, operations

    def test_operation_scope_isolation(self):
        store = OperationBindingStore()
        pairs = self._scope_pairs()
        operations = self._operations()
        # Only the named dimension changes in each OperationRef. Provider and
        # account variants deliberately share the baseline operation string.
        expected_bindings = dict.fromkeys(operations)
        for operation, payment in pairs:
            with self.subTest(insert=operation):
                expected = self._snapshot(store, operations)
                result = store.bind(operation, payment)
                self.assertEqual(result.outcome, BOUND)
                self.assertEqual(result.payment_ref, payment)
                self.assertIsNone(result.conflict)
                expected_bindings[operation] = payment
                expected["bindings"] = list(expected_bindings.items())
                expected["binding_count"] += 1
                self.assertEqual(self._snapshot(store, operations), expected)
                self._assert_capture(store, operations, operation, payment, self._item(payment))

        for operation, payment in pairs:
            with self.subTest(reaccept=operation):
                before = self._snapshot(store, operations)
                result = store.bind(replace(operation), replace(payment))
                self.assertEqual(result.outcome, REACCEPTED)
                self.assertEqual(result.payment_ref, payment)
                self.assertIsNone(result.conflict)
                self.assertEqual(self._snapshot(store, operations), before)

            with self.subTest(conflict=operation):
                incoming = replace(payment, payment_key=payment.payment_key + "_conflict")
                expected = self._snapshot(store, operations)
                conflict = BindingConflict(operation, payment, incoming)
                expected["review"].append(conflict)
                result = store.bind(operation, incoming)
                self.assertEqual(result.outcome, CONFLICT)
                self.assertEqual(result.payment_ref, payment)
                self.assertEqual(result.conflict, conflict)
                self.assertEqual(self._snapshot(store, operations), expected)

    def test_unknown_operation_lookup_preserves_state(self):
        store, operations = self._populated_store()
        before = self._snapshot(store, operations)
        self.assertIsNone(store.lookup(operations[-1]))
        self.assertEqual(self._snapshot(store, operations), before)
        for operation, payment in self._scope_pairs():
            self.assertEqual(store.lookup(operation), payment)
        self.assertEqual(self._snapshot(store, operations), before)

    def test_invalid_reference_arguments_preserve_state(self):
        store, operations = self._populated_store()
        item = self._item(PAYMENT_REF_A)
        for invalid in (None, "operation", {}, PAYMENT_REF_A):
            for method, args in (
                (store.bind, (invalid, PAYMENT_REF_A)),
                (store.lookup, (invalid,)),
                (store.record_capture, (invalid, PAYMENT_REF_A, item)),
            ):
                with self.subTest(method=method.__name__, invalid=invalid):
                    self._assert_rejected_unchanged(
                        store, operations, "INVALID_OPERATION_REF", method, *args,
                    )

        for invalid in (None, "payment", {}, OPERATION_REF):
            with self.subTest(payment=invalid):
                self._assert_rejected_unchanged(
                    store, operations, "INVALID_PAYMENT_REF",
                    store.bind, OPERATION_REF, invalid,
                )
                # Source-informed guard ordering: capture compares the binding
                # first, with no separate PaymentRef type check.
                self._assert_rejected_unchanged(
                    store, operations, "BINDING_REQUIRED",
                    store.record_capture, OPERATION_REF, invalid, item,
                )
        before = self._snapshot(store, operations)
        self.assertEqual(store.bind(OPERATION_REF, PAYMENT_REF_A).outcome, REACCEPTED)
        self.assertEqual(store.lookup(OPERATION_REF), PAYMENT_REF_A)
        self.assertEqual(self._snapshot(store, operations), before)
        self._assert_capture(store, operations, OPERATION_REF, PAYMENT_REF_A, item)

    def test_capture_without_binding_preserves_state(self):
        store, operations = self._populated_store()
        unknown = operations[-1]
        item = self._item(PAYMENT_REF_B)
        self._assert_rejected_unchanged(
            store, operations, "BINDING_REQUIRED",
            store.record_capture, unknown, PAYMENT_REF_B, item,
        )
        expected = self._snapshot(store, operations)
        self.assertEqual(store.bind(unknown, PAYMENT_REF_B).outcome, BOUND)
        expected["bindings"][-1] = (unknown, PAYMENT_REF_B)
        expected["binding_count"] += 1
        self.assertEqual(self._snapshot(store, operations), expected)
        self._assert_capture(store, operations, unknown, PAYMENT_REF_B, item)

    def test_capture_item_mismatch_preserves_state(self):
        store, operations = self._populated_store()
        item = self._item(PAYMENT_REF_A)
        for invalid in (None, "item", item.normalized_fact(), PAYMENT_REF_A, OPERATION_REF):
            with self.subTest(item_type=type(invalid).__name__):
                self._assert_rejected_unchanged(
                    store, operations, "CAPTURE_ITEM_MISMATCH",
                    store.record_capture, OPERATION_REF, PAYMENT_REF_A, invalid,
                )
        for name in ("provider", "account", "environment", "payment_key", "order_id"):
            with self.subTest(field=name):
                other = replace(PAYMENT_REF_A, **{name: getattr(PAYMENT_REF_A, name) + "_other"})
                self.assertIsInstance(other, PaymentRef)
                self._assert_rejected_unchanged(
                    store, operations, "CAPTURE_ITEM_MISMATCH",
                    store.record_capture, OPERATION_REF, PAYMENT_REF_A,
                    replace(item, payment_ref=other),
                )
        self._assert_capture(store, operations, OPERATION_REF, PAYMENT_REF_A, item)

    def test_same_operation_different_payment_key_is_review_conflict_without_new_capture(self):
        store = OperationBindingStore()
        history = normalize_recorded_document(PAYMENT_REF_A, PAID)

        first = store.bind(OPERATION_REF, PAYMENT_REF_A)
        self.assertEqual(first.outcome, BOUND)
        self.assertEqual(store.lookup(OPERATION_REF), PAYMENT_REF_A)
        self.assertEqual(store.binding_count(), 1)

        # Positive control: a bound operation may record an item capture.
        operations = (OPERATION_REF,)
        self._assert_capture(store, operations, OPERATION_REF, PAYMENT_REF_A, history.items[0])
        before = self._snapshot(store, operations)

        # Same operation, same five-field PaymentRef: re-accept, no growth.
        again = store.bind(OPERATION_REF, PAYMENT_REF_A)
        self.assertEqual(again.outcome, REACCEPTED)
        self.assertEqual(store.binding_count(), 1)
        self.assertEqual(len(store.review), 0)
        self.assertEqual(self._snapshot(store, operations), before)

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
        before["review"].append(BindingConflict(OPERATION_REF, PAYMENT_REF_A, PAYMENT_REF_B))
        self.assertEqual(self._snapshot(store, operations), before)

        # The conflicting fact cannot record a capture under this operation.
        self._assert_rejected_unchanged(
            store, operations, "BINDING_REQUIRED",
            store.record_capture, OPERATION_REF, PAYMENT_REF_B, history.items[0],
        )

    def test_reacceptance_requires_the_entire_payment_ref(self):
        for name in ("provider", "account", "environment", "payment_key", "order_id"):
            with self.subTest(field=name):
                store = OperationBindingStore()
                store.bind(OPERATION_REF, PAYMENT_REF_A)
                item = normalize_recorded_document(PAYMENT_REF_A, PAID).items[0]
                operations = (OPERATION_REF,)
                self._assert_capture(store, operations, OPERATION_REF, PAYMENT_REF_A, item)
                expected = self._snapshot(store, operations)
                incoming = replace(PAYMENT_REF_A, **{name: getattr(PAYMENT_REF_A, name) + "_other"})
                result = store.bind(OPERATION_REF, incoming)
                self.assertEqual(result.outcome, CONFLICT)
                self.assertEqual(result.conflict.incoming_payment_ref, incoming)
                self.assertEqual(result.conflict.bound_payment_ref, PAYMENT_REF_A)
                self.assertEqual(store.review, [result.conflict])
                self.assertEqual(store.lookup(OPERATION_REF), PAYMENT_REF_A)
                self.assertEqual(store.binding_count(), 1)
                expected["review"].append(BindingConflict(OPERATION_REF, PAYMENT_REF_A, incoming))
                self.assertEqual(self._snapshot(store, operations), expected)
                self._assert_rejected_unchanged(
                    store, operations, "BINDING_REQUIRED",
                    store.record_capture, OPERATION_REF, incoming, item,
                )
                self.assertEqual(store.bind(OPERATION_REF, replace(PAYMENT_REF_A)).outcome, REACCEPTED)
                self.assertEqual(self._snapshot(store, operations), expected)

    def test_initial_binding_rejects_operation_payment_scope_mismatch(self):
        for name in ("provider", "account"):
            with self.subTest(field=name):
                store, operations = self._populated_store()
                candidate = operations[-1]
                incoming = replace(PAYMENT_REF_A, **{name: getattr(PAYMENT_REF_A, name) + "_other"})
                self._assert_rejected_unchanged(
                    store, operations, "BINDING_MISMATCH",
                    store.bind, candidate, incoming,
                )
                expected = self._snapshot(store, operations)
                self.assertIsNone(store.lookup(candidate))
                self.assertEqual(store.bind(candidate, PAYMENT_REF_A).outcome, BOUND)
                expected["bindings"][-1] = (candidate, PAYMENT_REF_A)
                expected["binding_count"] += 1
                self.assertEqual(self._snapshot(store, operations), expected)
                self._assert_capture(
                    store, operations, candidate, PAYMENT_REF_A, self._item(PAYMENT_REF_A),
                )


if __name__ == "__main__":
    unittest.main()
