"""evidence_hash checks for the offline provider-fact harness.

Synthetic fixture only: the hash is the SHA-256 of the canonical JSON of a
per-item normalized fact, computed over normalized content — never over
raw delivery bytes. It is a logical identity rule, not an operational hash
schema.
"""

import hashlib
import json
import unittest

from provider_facts import (
    PROVENANCE,
    evidence_hash,
    normalize_recorded_document,
)
from synthetic_documents import PAID, PARTIAL_CANCEL, PAYMENT_REF_A


class EvidenceHashTests(unittest.TestCase):
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
