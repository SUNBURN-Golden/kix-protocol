"""Synthetic recording isolation and deterministic source behavior."""

import json
import unittest

from fake_repayment_source import FakeRepaymentSource, SyntheticRepaymentFault
from repayment_source import InvalidRepaymentRecord, RepaymentSourceError


class RepaymentSourceTests(unittest.TestCase):
    def test_copied_recordings_fresh_nested_documents_and_call_snapshots(self):
        identity = ("fixture-advance", "fixture-note")
        document = dict(advance_id=identity[0], repay_id=identity[1],
                        sequence=1, amount={"invalid-numeric": [1]})
        text = json.dumps(document)
        recordings = {identity: text}
        source = FakeRepaymentSource(recordings=recordings)
        empty_calls = source.calls
        recordings[identity] = SyntheticRepaymentFault.ERROR
        recordings.clear()
        first = source.fetch(*identity)
        calls = source.calls
        first["amount"]["invalid-numeric"].append(2)
        first.pop("sequence")
        self.assertEqual(source.fetch(*identity), document)
        self.assertEqual(source.recordings, {identity: text})
        self.assertEqual(empty_calls, ())
        self.assertEqual(calls, (identity,))
        self.assertEqual(source.calls, (identity, identity))
        with self.assertRaises(TypeError):
            source.recordings[identity] = "{}"
        with self.assertRaises(AttributeError):
            source.recordings = {}
        with self.assertRaises(AttributeError):
            source.calls = ()

    def test_lookup_uses_both_identities_without_consumption(self):
        source = FakeRepaymentSource(recordings={
            ("a1", "r1"): '{"fixture":1}',
            ("a1", "r2"): '{"fixture":2}',
            ("a2", "r1"): '{"fixture":3}',
        })
        requests = (("a1", "r1"), ("a1", "r2"), ("a2", "r1"), ("a2", "r2"), ("a1", "r1"))
        self.assertEqual([source.fetch(*key) for key in requests],
                         [{"fixture": 1}, {"fixture": 2}, {"fixture": 3}, None, {"fixture": 1}])
        self.assertEqual(source.calls, requests)

    def test_faults_raise_immediately_and_remain_available(self):
        for fault in SyntheticRepaymentFault:
            with self.subTest(fault=fault):
                source = FakeRepaymentSource(recordings={("a", "r"): fault})
                for _ in range(2):
                    with self.assertRaises(RepaymentSourceError) as caught:
                        source.fetch("a", "r")
                    self.assertEqual(str(caught.exception), fault.value)
                self.assertEqual(source.calls, (("a", "r"), ("a", "r")))
                self.assertIs(source.recordings[("a", "r")], fault)

    def test_invalid_json_and_non_object_recordings_are_local_errors(self):
        for text in ("{", "null", "[]", "1", '"repayment"'):
            with self.subTest(text=text):
                source = FakeRepaymentSource(recordings={("a", "r"): text})
                with self.assertRaises(InvalidRepaymentRecord):
                    source.fetch("a", "r")
                self.assertEqual(source.calls, (("a", "r"),))

    def test_mutable_values_and_non_identity_keys_are_refused(self):
        for key, value in (("a", "{}"), (("a",), "{}"), (("a", 1), "{}"),
                           (("a", "r"), {}), (("a", "r"), None)):
            with self.subTest(key=key, value=value):
                with self.assertRaises(TypeError):
                    FakeRepaymentSource(recordings={key: value})
