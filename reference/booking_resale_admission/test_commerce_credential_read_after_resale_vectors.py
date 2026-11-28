"""Source-informed local-call envelopes at pinned Commerce journey steps."""
from __future__ import annotations

import hashlib
import unittest

import test_commerce_admission_replay_after_resale_vectors as predecessor
import test_commerce_journey_receipts as goldens
from integration_gate.fsm_host import FsmHost
from integration_gate.schema import problems
from mock_gates import _canonical

ROOT = goldens.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_credential_read_after_resale_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_credential_read_after_resale_receipts_v1.json"
QUERY_SCHEMA_REF = "docs/contracts/openapi/kix-protocol.contract-only.openapi.json#/components/schemas/get_credential"
CASE = "credential-read-after-resale"
SEMANTIC_STATUS = "HOLD_SEMANTIC"
QUERY = {
    "action": "get_credential",
    "body": {"holder_role": "buyer-1", "right_id": "issue-1", "version": 1},
}
READ_METADATA = {
    "read_schema_version": "0.1",
    "query": "get_credential",
    "query_digest": "41a806c2bd8f71b1b59aa2a827ed905de3c7d372a3b55a58bbd5586e4fef2165",
    "fixture_mode": "REFERENCE_IN_MEMORY",
    "accepted_through": {"journal_entries": 4, "logical_time_ms": 1120000},
}
CHECKPOINTS = {
    12: ("resale-expiry-clock", "resale_set_clock", True, None),
    13: ("list", "resale_list_resale", False, "LISTING_LOCKED"),
    14: ("resale-payment", "resale_observe_resale_payment", False, "LISTING_LOCKED"),
    15: ("transfer", "resale_accept_resale", False, "STALE_VERSION"),
}


def _bytes(value):
    return _canonical(value).encode("utf-8")


def _step_ref(path, index):
    return f"{path}#/cases/0/steps/{index}"


class CommerceCredentialReadAfterResaleVectorTests(unittest.TestCase):
    def setUp(self):
        self.fixture_raw = goldens._read(FIXTURE)
        self.fixture = goldens._decode(self.fixture_raw)
        source_inputs_raw = goldens._read(predecessor.FIXTURE)
        source_receipts_raw = goldens._read(predecessor.GOLDEN_PATH)
        self.sources = [
            goldens._pin(predecessor.FIXTURE, source_inputs_raw),
            goldens._pin(predecessor.GOLDEN_PATH, source_receipts_raw),
        ]
        self.source_inputs = goldens._decode(source_inputs_raw)
        self.source_receipts = goldens._decode(source_receipts_raw)

    def _checkpoint_inputs(self, source_steps):
        checkpoints = []
        for index, (step_id, action, _, _) in CHECKPOINTS.items():
            source = source_steps[index]
            self.assertEqual((source["id"], source["action"]), (step_id, action))
            checkpoints.append({
                "id": step_id, "action": action, "body": source["body"],
                "source_step_ref": _step_ref(predecessor.FIXTURE, index),
                "source_receipt_ref": _step_ref(predecessor.GOLDEN_PATH, index) + "/receipt",
            })
        return checkpoints

    def _read_checkpoint(self, host, query, fresh, decision):
        before = {name: _bytes(machine.export_journal()) for name, machine in host.machines.items()}
        envelope = host.read(query["action"], query["body"])
        journals = {name: machine.export_journal() for name, machine in host.machines.items()}
        self.assertEqual(set(journals), predecessor.MACHINES)
        journal_digests = {}
        for name, journal in journals.items():
            after = _bytes(journal)
            self.assertEqual(after, before[name], f"{name} journal changed during read")
            journal_digests[name] = {
                "before_sha256": hashlib.sha256(before[name]).hexdigest(),
                "after_sha256": hashlib.sha256(after).hexdigest(),
            }

        admission = host.machines["admission"]
        self.assertEqual(envelope["accepted_through"], admission.accepted_through())
        result = envelope["result"]
        self.assertEqual(_bytes(envelope), _bytes({**READ_METADATA, "result": result}))
        self.assertIs(result["presentation"]["fresh"], fresh)
        self.assertEqual(result["presentation"]["decision"], decision)

        body = query["body"]
        view = admission.view_credential(body["right_id"], version=body["version"], holder_role=body["holder_role"])
        reservation = host.machines["reservation"].view("reserve-1")
        self.assertEqual(_bytes(result), _bytes(view))
        self.assertIsNone(view["credential"]["consume_id"])
        self.assertIsNone(reservation["consume_id"])
        consume_counts = {
            name: sum(entry["op"] == "consume" for entry in journals[name])
            for name in ("admission", "reservation")
        }
        self.assertEqual(consume_counts, {"admission": 0, "reservation": 0})
        return envelope, {
            "journals": journal_digests,
            "consume_counts": consume_counts,
            "views": {"presentation": view, "reservation": reservation},
        }

    def _observe(self):
        source_case, = self.source_inputs["cases"]
        source_outcomes, = self.source_receipts["cases"]
        self.assertEqual(source_case["id"], predecessor.CASE)
        self.assertEqual(source_outcomes["id"], predecessor.CASE)
        self.assertEqual(self.source_receipts["fixture"], self.sources[0])
        source_steps = source_case["steps"]
        checkpoints = self._checkpoint_inputs(source_steps)
        self.assertEqual(self.fixture_raw, _bytes({
            "fixture_version": 1,
            "provenance": "OFFLINE_CONFORMANCE_FIXTURE_ONLY",
            "semantic_consumer_status": SEMANTIC_STATUS,
            "domain": self.source_inputs["domain"],
            "sources": self.sources,
            "query": QUERY,
            "query_schema_ref": QUERY_SCHEMA_REF,
            "cases": [{"id": CASE, "steps": checkpoints}],
        }))
        query = self.fixture["query"]
        schema_path = QUERY_SCHEMA_REF.split("#")[0]
        schema = goldens._decode((ROOT / schema_path).read_bytes())["components"]["schemas"][query["action"]]
        self.assertEqual(problems(query["body"], schema), [])

        host = FsmHost()
        outcomes = []
        for index, step in enumerate(source_steps[:max(CHECKPOINTS) + 1]):
            step_id, action = step["id"], step["action"]
            source = source_outcomes["steps"][index]
            self.assertEqual((source["id"], source["action"]), (step_id, action))
            receipt = host.call(action, step["body"])
            self.assertTrue(_bytes(receipt) == _bytes(source["receipt"]), f"source receipt differs at {step_id}")
            if index in CHECKPOINTS:
                with self.subTest(checkpoint=step_id):
                    _, _, fresh, decision = CHECKPOINTS[index]
                    envelope, snapshot = self._read_checkpoint(host, query, fresh, decision)
                    self.assertEqual(_bytes(envelope["result"]),
                                     _bytes(source["diagnostic_snapshot"]["views"]["presentation"]))
                    if outcomes:
                        first_journals = outcomes[0]["diagnostic_snapshot"]["journals"]
                        self.assertEqual(snapshot["journals"]["admission"], first_journals["admission"])
                    outcomes.append({
                        "id": step_id, "action": action,
                        "input_ref": _step_ref(FIXTURE, len(outcomes)) + "/body",
                        "receipt": receipt, "read_envelope": envelope, "diagnostic_snapshot": snapshot,
                    })

        return {
            "record_schema_version": "kix-commerce-credential-read-after-resale-receipts/1",
            "record_kind": "IN_PROCESS_MOCK_RECEIPT_VECTORS",
            "normative": False,
            "semantic_consumer_status": SEMANTIC_STATUS,
            "diagnostic_snapshot_kind": "TEST_HARNESS_EVIDENCE",
            "fixture": goldens._pin(FIXTURE, self.fixture_raw),
            "sources": self.sources,
            "cases": [{"id": CASE, "steps": outcomes}],
        }

    def _compare_output(self, expected):
        self.assertTrue(_bytes(self._observe()) == expected, "complete canonical receipt and read bytes differ")

    def test_complete_output_bytes_and_references(self):
        self._compare_output(GOLDEN.read_bytes())

    def test_swapped_pre_listing_and_post_transfer_envelopes_fail_comparison(self):
        detached = goldens._decode(GOLDEN.read_bytes())
        before, _, _, transfer = detached["cases"][0]["steps"]
        before["read_envelope"], transfer["read_envelope"] = transfer["read_envelope"], before["read_envelope"]
        with self.assertRaisesRegex(AssertionError, "complete canonical receipt and read bytes differ"):
            self._compare_output(_bytes(detached))
