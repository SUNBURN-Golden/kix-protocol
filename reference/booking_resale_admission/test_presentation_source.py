"""Synthetic recording isolation and deterministic boundary failures."""

import json
import unittest

from fake_presentation_source import FakePresentationSource, SyntheticPresentationFault
from presentation_source import InvalidPresentationRecord, PresentationSourceError


class PresentationSourceTests(unittest.TestCase):
    def test_recordings_fetch_results_and_call_snapshots_are_isolated(self):
        identity = ("consume", "fixture")
        text = json.dumps({"nested": {"values": [1]}})
        recordings = {identity: text}
        source = FakePresentationSource(recordings=recordings)
        recordings[identity] = "{}"
        recordings.clear()
        self.assertEqual(source.recordings[identity], text)
        with self.assertRaises(TypeError):
            source.recordings[identity] = "{}"
        with self.assertRaises(AttributeError):
            source.recordings = {}
        first = source.fetch("fixture", operation="consume")
        first["nested"]["values"].append(2)
        snapshot = source.calls
        self.assertEqual(source.fetch("fixture", operation="consume"), {"nested": {"values": [1]}})
        self.assertEqual(snapshot, (identity,))
        self.assertEqual(source.calls, (identity, identity))
        self.assertIsNone(source.fetch("fixture", operation="authorize_admission"))
        self.assertIsNone(source.fetch("absent", operation="consume"))
        self.assertEqual(len(source.calls), 4)

    def test_malformed_recordings_are_rejected_on_every_fetch(self):
        for recording in ("{", "[]", "null", '"text"', "1", "true",
                          '{"x":1,"x":2}', '{"x":{"a":1,"a":2}}',
                          '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(recording=recording):
                source = FakePresentationSource(recordings={("consume", "fixture"): recording})
                for _ in range(2):
                    with self.assertRaises(InvalidPresentationRecord):
                        source.fetch("fixture", operation="consume")
                self.assertEqual(source.calls, (("consume", "fixture"),) * 2)

    def test_fault_markers_raise_immediately_and_never_fall_back(self):
        for fault in SyntheticPresentationFault:
            with self.subTest(fault=fault):
                source = FakePresentationSource(recordings={
                    ("consume", "fixture"): fault,
                    ("authorize_admission", "fixture"): "{}",
                })
                for _ in range(2):
                    with self.assertRaises(PresentationSourceError) as caught:
                        source.fetch("fixture", operation="consume")
                    self.assertEqual(str(caught.exception), fault.value)
                self.assertEqual(source.calls, (("consume", "fixture"),) * 2)

    def test_constructor_rejects_mutable_values_and_invalid_keys(self):
        for recordings in ({("consume", "fixture"): {}}, {"fixture": "{}"},
                           {("other", "fixture"): "{}"}, {("consume", 1): "{}"},
                           {("consume",): "{}"}, {("consume", "fixture"): None}):
            with self.subTest(recordings=recordings), self.assertRaises(TypeError):
                FakePresentationSource(recordings=recordings)


if __name__ == "__main__":
    unittest.main()
