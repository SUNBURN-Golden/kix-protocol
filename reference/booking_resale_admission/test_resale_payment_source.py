"""Recording boundary gaps: local JSON only, no services or lifecycle effects."""

import json
import unittest

from fake_resale_payment_source import FakeResalePaymentSource, SyntheticResalePaymentFault
from resale_payment_source import InvalidResalePaymentRecord, ResalePaymentSourceError


class ResalePaymentSourceTests(unittest.TestCase):
    def test_recordings_are_copied_read_only_and_outputs_are_deeply_detached(self):
        body = {"listing_id": "recording", "nested": {"items": [1, {"value": 2}]}}
        recordings = {"recording": json.dumps(body)}
        source = FakeResalePaymentSource(recordings=recordings)
        snapshot = source.calls
        recordings["recording"] = "{}"
        recordings["added"] = "{}"
        with self.assertRaises(TypeError):
            source.recordings["recording"] = "{}"
        with self.assertRaises(TypeError):
            del source.recordings["recording"]
        first = source.fetch("recording")
        first["nested"]["items"][1]["value"] = 99
        first["listing_id"] = "changed"
        self.assertEqual(source.fetch("recording"), body)
        self.assertIsNone(source.fetch("added"))
        self.assertEqual(snapshot, ())
        retained = source.calls
        source.fetch("recording")
        self.assertEqual(retained, ("recording", "recording", "added"))
        self.assertEqual(source.calls, retained + ("recording",))
        self.assertIsInstance(source.calls, tuple)

    def test_missing_records_are_absent_and_each_fetch_is_recorded(self):
        source = FakeResalePaymentSource(recordings={})
        self.assertIsNone(source.fetch("missing"))
        self.assertIsNone(source.fetch("missing"))
        self.assertEqual(source.calls, ("missing", "missing"))

    def test_strict_json_rejects_bad_roots_duplicates_and_nonfinite_constants(self):
        malformed = ["{", "[]", "null", "false", "1", '"text"',
                     '{"x": 1, "x": 2}', '{"nested": {"x": 1, "x": 2}}',
                     '{"x": NaN}', '{"x": Infinity}', '{"x": -Infinity}',
                     '{"x": [NaN]}', '{"x": 1} trailing', "[" * 2000]
        for recording in malformed:
            with self.subTest(recording=recording[:100]):
                source = FakeResalePaymentSource(recordings={"recording": recording})
                for _ in range(2):
                    with self.assertRaises(InvalidResalePaymentRecord):
                        source.fetch("recording")
                self.assertEqual(source.calls, ("recording", "recording"))

    def test_synthetic_faults_are_immediate_and_do_not_retry_or_fall_back(self):
        for fault in SyntheticResalePaymentFault:
            with self.subTest(fault=fault):
                source = FakeResalePaymentSource(recordings={"recording": fault})
                for _ in range(2):
                    with self.assertRaises(ResalePaymentSourceError) as raised:
                        source.fetch("recording")
                    self.assertEqual(str(raised.exception), fault.value)
                    self.assertFalse(hasattr(raised.exception, "code"))
                self.assertEqual(source.calls, ("recording", "recording"))

    def test_constructor_rejects_mutable_recordings_and_nonstring_keys(self):
        for recordings in ({"recording": {}}, {"recording": []}, {"recording": None},
                           {"recording": 1}, {1: "{}"}, {("recording",): "{}"}):
            with self.subTest(recordings=recordings):
                with self.assertRaises(TypeError):
                    FakeResalePaymentSource(recordings=recordings)


if __name__ == "__main__":
    unittest.main()
