"""Recording boundary gaps: local JSON only, no services or lifecycle effects."""

import json
import unittest

from fake_resale_offer_source import FakeResaleOfferSource, SyntheticResaleOfferFault
from resale_offer_source import InvalidResaleOfferRecord, ResaleOfferSourceError


class ResaleOfferSourceTests(unittest.TestCase):
    def test_recordings_are_copied_read_only_and_outputs_are_deeply_detached(self):
        body = {"offer_id": "offer", "nested": {"items": [1, {"value": 2}]}}
        recordings = {"offer": json.dumps(body)}
        source = FakeResaleOfferSource(recordings=recordings)
        snapshot = source.calls
        recordings["offer"] = "{}"
        recordings["added"] = "{}"
        with self.assertRaises(TypeError):
            source.recordings["offer"] = "{}"
        with self.assertRaises(TypeError):
            del source.recordings["offer"]
        first = source.fetch("offer")
        first["nested"]["items"][1]["value"] = 99
        first["offer_id"] = "changed"
        self.assertEqual(source.fetch("offer"), body)
        self.assertIsNone(source.fetch("added"))
        self.assertEqual(snapshot, ())
        retained = source.calls
        source.fetch("offer")
        self.assertEqual(retained, ("offer", "offer", "added"))
        self.assertEqual(source.calls, retained + ("offer",))
        self.assertIsInstance(source.calls, tuple)

    def test_missing_records_are_absent_and_each_fetch_is_recorded(self):
        source = FakeResaleOfferSource(recordings={})
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
                source = FakeResaleOfferSource(recordings={"offer": recording})
                for _ in range(2):
                    with self.assertRaises(InvalidResaleOfferRecord):
                        source.fetch("offer")
                self.assertEqual(source.calls, ("offer", "offer"))

    def test_synthetic_faults_are_immediate_and_do_not_retry_or_fall_back(self):
        for fault in SyntheticResaleOfferFault:
            with self.subTest(fault=fault):
                source = FakeResaleOfferSource(recordings={"offer": fault})
                for _ in range(2):
                    with self.assertRaises(ResaleOfferSourceError) as raised:
                        source.fetch("offer")
                    self.assertEqual(str(raised.exception), fault.value)
                    self.assertFalse(hasattr(raised.exception, "code"))
                self.assertEqual(source.calls, ("offer", "offer"))

    def test_constructor_rejects_mutable_recordings_and_nonstring_keys(self):
        for recordings in ({"offer": {}}, {"offer": []}, {"offer": None},
                           {"offer": 1}, {1: "{}"}, {("offer",): "{}"}):
            with self.subTest(recordings=recordings):
                with self.assertRaises(TypeError):
                    FakeResaleOfferSource(recordings=recordings)


if __name__ == "__main__":
    unittest.main()
