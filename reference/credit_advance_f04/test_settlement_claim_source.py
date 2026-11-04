"""Source-informed offline source isolation and deterministic fault evidence."""

from copy import deepcopy
import json
import unittest
from unittest.mock import Mock

from fake_settlement_claim_source import FakeSettlementClaimSource, SyntheticSettlementClaimFault
from settlement_claim_source import (
    InvalidSettlementClaimRecord, LocalSettlementClaimSource, SettlementClaimSourceError,
)
from test_credit_fsm import settlement_book
from settlement_fsm import SettlementError


class SettlementClaimSourceTests(unittest.TestCase):
    def test_local_source_one_view_detaches_nested_data_and_propagates_faults(self):
        document = {"claim": {"nested": [1]}}
        view = Mock()
        view.view.return_value = document
        source = LocalSettlementClaimSource(view)
        first = source.fetch("chosen")
        view.view.assert_called_once_with("chosen")
        first["claim"]["nested"].append(2)
        self.assertEqual(document["claim"]["nested"], [1])
        document["claim"]["nested"].append(3)
        self.assertEqual(first["claim"]["nested"], [1, 2])
        fault = RuntimeError("fixture-source-fault")
        view.view.side_effect = fault
        with self.assertRaises(RuntimeError) as caught:
            source.fetch("chosen")
        self.assertIs(caught.exception, fault)
        self.assertEqual(view.view.call_count, 2)

    def test_actual_local_machine_old_snapshot_survives_later_commit(self):
        book, _face = settlement_book("CAPTURED")
        source = LocalSettlementClaimSource(book)
        before = book.canonical_state()
        old = source.fetch("claim-1")
        self.assertEqual(book.canonical_state(), before)
        saved = deepcopy(old)
        book.commit("claim-1", idempotency_key="commit", movement_id="move",
                    gross=100_000, amount=90_000, fee=10_000, tax=0, held=0, adjustment=0)
        current = source.fetch("claim-1")
        self.assertEqual(old, saved)
        self.assertEqual(old["phase"], "CAPTURED")
        self.assertEqual(current["phase"], "COMMITTED")
        self.assertEqual(current["claim"]["confirmed_cash"], 90_000)
        current["claim"]["obligations"][0]["outstanding"] = -1
        self.assertNotEqual(current, source.fetch("claim-1"))
        with self.assertRaises(SettlementError) as caught:
            source.fetch("missing")
        self.assertEqual(caught.exception.code, "UNKNOWN_SETTLEMENT")

    def test_fake_copies_recordings_detaches_fetches_and_snapshots_calls(self):
        text = json.dumps({"claim": {"nested": [1]}})
        recordings = {"chosen": text}
        source = FakeSettlementClaimSource(recordings=recordings)
        recordings["chosen"] = "{}"
        recordings["later"] = "{}"
        with self.assertRaises(TypeError):
            source.recordings["chosen"] = "{}"
        self.assertEqual(dict(source.recordings), {"chosen": text})
        calls = source.calls
        first = source.fetch("chosen")
        first["claim"]["nested"].append(2)
        self.assertEqual(source.fetch("chosen"), {"claim": {"nested": [1]}})
        self.assertIsNone(source.fetch("missing"))
        self.assertEqual(calls, ())
        self.assertEqual(source.calls, ("chosen", "chosen", "missing"))

    def test_fake_faults_and_malformed_json_are_immediate_and_repeatable(self):
        for recording, error in (
            (SyntheticSettlementClaimFault.ERROR, SettlementClaimSourceError),
            (SyntheticSettlementClaimFault.TIMEOUT, SettlementClaimSourceError),
            ("{", InvalidSettlementClaimRecord),
            ("[]", InvalidSettlementClaimRecord),
            ("null", InvalidSettlementClaimRecord),
        ):
            with self.subTest(recording=recording):
                source = FakeSettlementClaimSource(recordings={"chosen": recording})
                for _ in range(2):
                    with self.assertRaises(error):
                        source.fetch("chosen")
                self.assertEqual(source.calls, ("chosen", "chosen"))
                self.assertEqual(source.recordings["chosen"], recording)

    def test_fake_rejects_mutable_recordings_and_non_string_keys(self):
        for recordings in ({1: "{}"}, {("chosen",): "{}"}, {"chosen": {}}, {"chosen": None}):
            with self.subTest(recordings=recordings), self.assertRaises(TypeError):
                FakeSettlementClaimSource(recordings=recordings)
