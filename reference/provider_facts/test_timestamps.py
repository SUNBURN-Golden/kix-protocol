"""Raw timestamp checks for the offline provider-fact harness.

Synthetic fixture only: raw text and recorded offsets are preserved, an
offset-less createdAt is recorded unresolved and is never assigned a zone,
and occurrence/receipt times are not merged.
"""

import unittest

from provider_facts import (
    AMBIGUOUS_UNRESOLVED,
    OFFSET_RECORDED,
    normalize_recorded_document,
    raw_timestamp,
)
from synthetic_documents import OFFSET_LESS_CREATED_AT, PAID, PAYMENT_REF_A


class TimestampTests(unittest.TestCase):
    def test_ambiguous_timezone_stays_unresolved_and_raw_text_is_preserved(self):
        # Text with an offset records exactly that offset.
        zoned = raw_timestamp("2026-10-01T12:00:00+09:00")
        self.assertEqual(zoned.text, "2026-10-01T12:00:00+09:00")
        self.assertEqual(zoned.offset, "+09:00")
        self.assertEqual(zoned.status, OFFSET_RECORDED)
        zulu = raw_timestamp("2026-10-01T03:00:00Z")
        self.assertEqual(zulu.offset, "Z")
        self.assertEqual(zulu.status, OFFSET_RECORDED)
        # An offset-less timestamp is unresolved, never assigned a zone.
        bare = raw_timestamp("2026-10-01T12:00:01")
        self.assertEqual(bare.text, "2026-10-01T12:00:01")
        self.assertIsNone(bare.offset)
        self.assertEqual(bare.status, AMBIGUOUS_UNRESOLVED)

        history = normalize_recorded_document(PAYMENT_REF_A, OFFSET_LESS_CREATED_AT)
        stamps = history.items[0].detail["timestamps"]
        self.assertEqual(stamps["createdAt"]["text"], "2026-10-01T12:00:01")
        self.assertIsNone(stamps["createdAt"]["offset"])
        self.assertEqual(stamps["createdAt"]["status"], AMBIGUOUS_UNRESOLVED)
        # Offset-bearing fields keep their own raw text and offsets; the
        # ambiguous field is not rewritten to match them.
        self.assertEqual(stamps["requestedAt"]["offset"], "+09:00")
        self.assertEqual(stamps["requestedAt"]["status"], OFFSET_RECORDED)
        self.assertEqual(stamps["approvedAt"]["text"], "2026-10-01T12:00:00+09:00")

        # Occurrence and receipt stay separate times on the history.
        self.assertEqual(history.receipt.text, "2026-10-01T12:00:05+09:00")
        self.assertEqual(history.receipt.offset, "+09:00")
        self.assertNotEqual(history.receipt.text, history.items[0].occurred.text)


if __name__ == "__main__":
    unittest.main()
