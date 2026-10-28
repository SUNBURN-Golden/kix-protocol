"""Normalize-only-verified-facts checks for the offline harness.

Synthetic fixture only: timeout, not-found and unsupported stay
Unresolved, an unverified signal is never a fact, and a cancel never
erases the original payment item. Nothing unresolved infers absence.
"""

import unittest
from copy import deepcopy

from provider_facts import (
    BINDING_MISMATCH,
    CURRENCY_UNSUPPORTED,
    ITEM_CANCEL,
    ITEM_PAYMENT,
    LOOKUP_NOT_FOUND,
    LOOKUP_TIMEOUT,
    METHOD_UNSUPPORTED,
    UNVERIFIED_SOURCE,
    Unresolved,
    evidence_hash,
    normalize_recorded_document,
)
from synthetic_documents import (
    CANCELED_AFTER_DONE,
    DIFFERENT_PAYMENT,
    NON_KRW,
    PARTIAL_CANCEL,
    NOT_FOUND,
    PAID,
    PAYMENT_REF_A,
    TIMEOUT,
    UNSUPPORTED_METHOD,
    UNVERIFIED_SIGNAL,
)


class NormalizeVerifiedOnlyTests(unittest.TestCase):
    def test_missing_or_unsupported_payment_and_cancel_statuses_stay_unresolved(self):
        missing = object()
        for target in ("payment", "cancel"):
            for status in (missing, None, "", "UNKNOWN_SYNTHETIC_STATUS", "READY", 1, [], {}):
                with self.subTest(target=target, status=status):
                    document = deepcopy(PARTIAL_CANCEL if target == "cancel" else PAID)
                    item = document["payment"]
                    field = "status"
                    if target == "cancel":
                        item = item["cancels"][0]
                        field = "cancelStatus"
                        # A generic status cannot stand in for the required
                        # cancelStatus field of a supported cancel fixture.
                        item["status"] = "DONE"
                    if status is missing:
                        del item[field]
                    else:
                        item[field] = status
                    result = normalize_recorded_document(PAYMENT_REF_A, document)
                    self.assertEqual(result, Unresolved("STATUS_UNSUPPORTED"))
                    self.assertEqual(normalize_recorded_document(PAYMENT_REF_A, document), result)

    def test_timeout_not_found_and_unsupported_stay_unresolved(self):
        cases = (
            (TIMEOUT, LOOKUP_TIMEOUT),
            (NOT_FOUND, LOOKUP_NOT_FOUND),
            (UNSUPPORTED_METHOD, METHOD_UNSUPPORTED),
            (NON_KRW, CURRENCY_UNSUPPORTED),
            (UNVERIFIED_SIGNAL, UNVERIFIED_SOURCE),
            (DIFFERENT_PAYMENT, BINDING_MISMATCH),
        )
        for document, reason in cases:
            result = normalize_recorded_document(PAYMENT_REF_A, document)
            self.assertEqual(result, Unresolved(reason))
            # Terminal and stable: re-normalizing yields the same value and
            # never infers absence or success.
            self.assertEqual(normalize_recorded_document(PAYMENT_REF_A, document), result)

    def test_cancel_does_not_erase_the_original_payment_item(self):
        paid = normalize_recorded_document(PAYMENT_REF_A, PAID)
        original_hash = evidence_hash(paid.items[0])
        history = normalize_recorded_document(PAYMENT_REF_A, CANCELED_AFTER_DONE)
        self.assertEqual(len(history.items), 2)
        payment_item, cancel_item = history.items
        self.assertEqual(payment_item.kind, ITEM_PAYMENT)
        self.assertEqual(cancel_item.kind, ITEM_CANCEL)
        # DONE -> CANCELED is a new item, not a rewrite of the earlier item:
        # the recorded status text differs, so its normalized fact differs.
        self.assertEqual(payment_item.status_text, "CANCELED")
        self.assertEqual(cancel_item.status_text, "DONE")
        self.assertEqual(cancel_item.amount, 15000)
        self.assertNotEqual(evidence_hash(payment_item), evidence_hash(cancel_item))
        self.assertNotEqual(original_hash, evidence_hash(payment_item))
        # The earlier item's hash is recomputed from its own document only;
        # the later cancel evidence never rewrites it.
        repaid = normalize_recorded_document(PAYMENT_REF_A, PAID)
        self.assertEqual(evidence_hash(repaid.items[0]), original_hash)


if __name__ == "__main__":
    unittest.main()
