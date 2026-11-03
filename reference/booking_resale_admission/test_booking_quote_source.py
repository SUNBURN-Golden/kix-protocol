"""Synthetic source isolation, decoding and immediate failure boundaries."""

import json
import unittest
from unittest.mock import patch

from booking_quote_source import BookingQuoteSourceError, InvalidBookingQuoteRecord
from fake_booking_quote_source import FakeBookingQuoteSource, SyntheticBookingQuoteFault


def record(**changes):
    return dict(reservation_id="reserve-1", amount=10001, quote_ref="quote-1") | changes


def source_for(body=None):
    return FakeBookingQuoteSource(recordings={"record-1": json.dumps(record() if body is None else body)})


class BookingQuoteSourceTests(unittest.TestCase):
    def test_immutable_recordings_detached_fetches_and_call_snapshots(self):
        recordings = {"record-1": json.dumps(record())}
        source = FakeBookingQuoteSource(recordings=recordings)
        self.assertEqual(source.calls, ())
        recordings.clear()
        with self.assertRaises(TypeError):
            source.recordings["record-1"] = "{}"
        first = source.fetch("record-1")
        calls = source.calls
        first.clear()
        self.assertEqual(source.fetch("record-1"), record())
        self.assertEqual(calls, ("record-1",))
        self.assertIsNone(source.fetch("absent"))
        self.assertEqual(source.calls, ("record-1", "record-1", "absent"))

    def test_constructor_rejects_mutable_or_invalid_recording_types_without_fetch(self):
        for recordings in ({1: "{}"}, {"x": {}}, {"x": None}, {"x": True}, {"x": []}):
            with self.subTest(recordings=recordings), self.assertRaises(TypeError):
                FakeBookingQuoteSource(recordings=recordings)

    def test_strict_json_rejects_duplicate_keys_nonfinite_and_invalid_roots(self):
        texts = ["{", "", "[]", "null", "true", '"text"', "1", "1.2",
                 '{"amount":1,"amount":2}', '{"nested":{"x":1,"x":2}}',
                 '{"amount":NaN}', '{"amount":Infinity}', '{"amount":-Infinity}',
                 '{"amount":1e999}']
        for text in texts:
            source = FakeBookingQuoteSource(recordings={"record-1": text})
            with self.subTest(text=text), self.assertRaises(InvalidBookingQuoteRecord):
                source.fetch("record-1")
            self.assertEqual(source.calls, ("record-1",))

    def test_faults_are_immediate_without_sleep_retry_or_decode(self):
        for fault in SyntheticBookingQuoteFault:
            source = FakeBookingQuoteSource(recordings={"record-1": fault})
            with patch("time.sleep", side_effect=AssertionError("no sleep")), \
                    patch("fake_booking_quote_source.decode_json") as decode:
                with self.assertRaises(BookingQuoteSourceError) as caught:
                    source.fetch("record-1")
                self.assertEqual(str(caught.exception), fault.value)
                decode.assert_not_called()
            self.assertEqual(source.calls, ("record-1",))
