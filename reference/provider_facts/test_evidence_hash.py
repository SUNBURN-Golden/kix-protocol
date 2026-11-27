"""evidence_hash checks for the offline provider-fact harness.

Synthetic fixture only: the hash is the SHA-256 of the canonical JSON of a
per-item normalized fact, computed over normalized content — never over
raw delivery bytes. It is a logical identity rule, not an operational hash
schema.
"""

import hashlib
import json
import unittest
from copy import deepcopy

from provider_facts import (
    PROVENANCE,
    evidence_hash,
    normalize_recorded_document,
)
from synthetic_documents import MULTIPLE_CANCELS, PAID, PARTIAL_CANCEL, PAYMENT_REF_A


class EvidenceHashTests(unittest.TestCase):
    def test_cancel_hashes_ignore_snapshot_order_and_receipt_metadata(self):
        original = normalize_recorded_document(PAYMENT_REF_A, MULTIPLE_CANCELS)
        reordered = deepcopy(MULTIPLE_CANCELS)
        reordered["payment"]["cancels"].reverse()
        reordered["recorded_at"] = "2026-10-04T09:00:00+09:00"
        repeated = normalize_recorded_document(PAYMENT_REF_A, reordered)
        self.assertEqual(len(original.items), 3)
        self.assertNotEqual(original.receipt, repeated.receipt)
        # Pair fixture entries directly, without choosing a ProviderFactKey
        # or deriving an EventItemId from a provider field or array position.
        for before, after in zip(original.items[1:], reversed(repeated.items[1:])):
            self.assertNotEqual(before.index, after.index)
            self.assertEqual(before.normalized_fact(), after.normalized_fact())
            self.assertEqual(evidence_hash(before), evidence_hash(after))
        self.assertEqual(evidence_hash(original.items[0]), evidence_hash(repeated.items[0]))
        self.assertNotEqual(evidence_hash(original.items[1]), evidence_hash(original.items[2]))
        changed = deepcopy(MULTIPLE_CANCELS)
        changed["payment"]["cancels"][0]["cancelAmount"] += 1
        changed_history = normalize_recorded_document(PAYMENT_REF_A, changed)
        self.assertNotEqual(evidence_hash(original.items[1]), evidence_hash(changed_history.items[1]))
        self.assertEqual(evidence_hash(original.items[2]), evidence_hash(changed_history.items[2]))

    def test_evidence_hash_is_sha256_of_canonical_normalized_fact(self):
        history = normalize_recorded_document(PAYMENT_REF_A, PARTIAL_CANCEL)
        self.assertEqual(len(history.items), 2)
        for item in history.items:
            canonical = json.dumps(
                item.normalized_fact(),
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            )
            expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            self.assertEqual(evidence_hash(item), expected)
            self.assertEqual(item.normalized_fact()["provenance"], PROVENANCE)
            self.assertEqual(item.normalized_fact()["payment_ref"], PAYMENT_REF_A.as_dict())
        # Independent per item: the later cancel fact hashes differently and
        # never rewrites the payment item's hash.
        self.assertNotEqual(history.item_hashes()[0], history.item_hashes()[1])
        # Deterministic across re-normalization of the same recorded document.
        again = normalize_recorded_document(PAYMENT_REF_A, PARTIAL_CANCEL)
        self.assertEqual(again.item_hashes(), history.item_hashes())
        # A changed recorded amount changes the fact hash — content change,
        # not a re-delivery of the same fact.
        mutated = dict(PAID)
        payment = dict(mutated["payment"])
        payment["totalAmount"] = 15001
        mutated["payment"] = payment
        other = normalize_recorded_document(PAYMENT_REF_A, mutated)
        paid = normalize_recorded_document(PAYMENT_REF_A, PAID)
        self.assertNotEqual(evidence_hash(other.items[0]), evidence_hash(paid.items[0]))


if __name__ == "__main__":
    unittest.main()
