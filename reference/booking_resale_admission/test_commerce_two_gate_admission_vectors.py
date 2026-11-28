"""Replay two sequential gate orders from the same offline adoption checkpoint."""
from __future__ import annotations

import copy
import unittest

import test_commerce_journey_receipts as goldens
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import parse_envelope
from mock_gates import _canonical
from reference.booking_resale_admission.commerce_tuple_assertions import (
    BOOKING_BRANCH_RECEIPTS, RECEIPTS, VECTORS, check_journal, resolve_receipt_ref, snapshot,
)
from test_commerce_temporal_vectors import _assert_paths

ROOT = goldens.ROOT
BRA = "reference/booking_resale_admission"
FIXTURE = f"{BRA}/fixtures/commerce_two_gate_admission_inputs_v1.json"
GOLDEN = ROOT / f"{BRA}/fixtures/commerce_two_gate_admission_receipts_v1.json"
FULL_RECEIPT_INDEX = "docs/status/COMMERCE_FULL_RECEIPT_INDEX_V1.json"
SOURCE_PATHS = sorted((
    VECTORS, FULL_RECEIPT_INDEX, RECEIPTS, BOOKING_BRANCH_RECEIPTS,
    "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md",
))
CONTEXT = "booking-admission"
CHECKPOINT = {
    "vector_id": CONTEXT + "/adopt-B",
    "vector_source": VECTORS,
    "receipt_index": FULL_RECEIPT_INDEX,
    "payment_receipt_ref": BOOKING_BRANCH_RECEIPTS + "#/receipts/booking-admission~1payment-B",
    "issuance_receipt_ref": BOOKING_BRANCH_RECEIPTS + "#/receipts/booking-admission~1issue-B",
    "adoption_receipt_ref": RECEIPTS + "#/steps/27/receipt",
    "clock_ms": 1000000,
}
MACHINES = {"admission", "reservation", "resale", "settlement", "credit"}
BOUND_DELTAS = {"admission": 1, "reservation": 1}
SEMANTIC_STATUS = "HOLD_SEMANTIC"


def _bytes(value):
    return _canonical(value).encode("utf-8")


def _expected_cases(vectors):
    presentations = {}
    for command, subject in (("authorize", "admission_id"), ("consume", "consume_id")):
        step_id = f"{command}-B"
        gate_1 = {"id": step_id, **vectors[f"{CONTEXT}/{step_id}"]["envelope"]}
        gate_2 = copy.deepcopy(gate_1)
        suffix = "-gate-2"
        gate_2["id"] += suffix
        gate_2["operationId"] += suffix
        gate_2["body"][subject] += suffix
        gate_2["body"]["idempotency_key"] += suffix
        gate_2["body"].update(gate_role="gate-2", request="22" * 32)
        presentations[command] = {"gate-1": gate_1, "gate-2": gate_2}

    authorize, consume = presentations["authorize"], presentations["consume"]
    return [
        {
            "id": f"{winner}-first",
            "steps": [
                {**authorize[winner], "expect": {"duplicate": False, "applied": "authorize_admission"}},
                {**authorize[loser], "expect_error": "ADMISSION_LOCKED"},
                {**consume[loser], "expect_error": "GATE_MISMATCH"},
                {**consume[winner], "expect": {"duplicate": False, "applied": "consume"}},
            ],
        }
        for winner, loser in (("gate-1", "gate-2"), ("gate-2", "gate-1"))
    ]


class CommerceTwoGateAdmissionVectorTests(unittest.TestCase):
    def _call(self, host, envelope):
        _, _, action, body = parse_envelope(copy.deepcopy(envelope), self.catalogue.commands)
        return host.call(action, body)

    def _checkpoint_receipt(self, vector, documents):
        vid = vector["id"]
        indexed = documents[FULL_RECEIPT_INDEX]["receipts"][vid]
        if "receipt_ref" in vector["expected"]:
            self.assertEqual(indexed, {"source_kind": "direct", "receipt_ref": vector["expected"]["receipt_ref"]})
            return resolve_receipt_ref(self, vector, documents[RECEIPTS]["steps"])

        token = vid.replace("~", "~0").replace("/", "~1")
        self.assertEqual(indexed, {
            "source_kind": "booking_branch_companion",
            "receipt_ref": f"{BOOKING_BRANCH_RECEIPTS}#/receipts/{token}",
        })
        return documents[BOOKING_BRANCH_RECEIPTS]["receipts"][vid]

    def _diagnostics(self, host, machines):
        self.assertEqual(set(machines), MACHINES)
        for name in BOUND_DELTAS:
            state = goldens._decode(machines[name][0].encode("utf-8"))
            self.assertEqual(state["logical_time_ms"], CHECKPOINT["clock_ms"], name)
        return {
            "machines": {name: {"state": state, "journal": journal}
                         for name, (state, journal) in machines.items()},
            "views": {
                "reservation": host.machines["reservation"].view("reserve-B"),
                "credential": host.machines["admission"].view("issue-B"),
            },
        }

    def _replay_checkpoint(self, history, documents):
        host = FsmHost()
        for vector in history:
            with self.subTest(vector=vector["id"]):
                self.assertEqual(vector["expected"]["kind"], "accept")
                receipt = self._call(host, vector["envelope"])
                self.assertTrue(_bytes(receipt) == _bytes(self._checkpoint_receipt(vector, documents)),
                                "complete checkpoint receipt differs")

        payment = self._checkpoint_receipt(history[4], documents)["reservation"]
        self.assertEqual(history[4]["id"], CONTEXT + "/payment-B")
        _assert_paths(payment, {"phase": "PAYMENT_NOTED", "right": None})
        checkpoint = self._diagnostics(host, snapshot(host))
        _assert_paths(checkpoint["views"], {
            "reservation.reservation_id": "reserve-B", "reservation.phase": "ISSUED",
            "reservation.payment_ref": payment["payment_ref"], "reservation.amount": payment["amount"],
            "reservation.slot": 1, "reservation.slot_state": "ISSUED", "reservation.slot_right_id": "issue-B",
            "reservation.right.state": "ACTIVE", "reservation.right.right_id": "issue-B",
            "reservation.right.version": 1, "reservation.right.admission_id": None,
            "reservation.admission_id": None, "reservation.consume_id": None,
            "credential.right_id": "issue-B", "credential.version": 1, "credential.phase": "ELIGIBLE",
            "credential.admission_id": None, "credential.consume_id": None,
        })
        return host, checkpoint

    def _assert_authorized(self, receipt, views, body):
        _assert_paths(receipt, {
            "admission.admission_id": body["admission_id"], "admission.gate_role": body["gate_role"],
            "admission.request": body["request"], "admission.expires_ms": body["expires_ms"],
            "admission.attached": True, "admission.expired": False,
        })
        _assert_paths(views, {
            "credential.phase": "AUTHORIZED", "credential.version": 1,
            "credential.admission_id": body["admission_id"], "credential.gate_role": body["gate_role"],
            "credential.consume_id": None, "reservation.phase": "ADMISSION_AUTHORIZED",
            "reservation.admission_id": body["admission_id"], "reservation.right.version": 1,
            "reservation.consume_id": None,
        })

    def _assert_consumed(self, receipt, diagnostics, body):
        _assert_paths(receipt, {
            "evidence.decision": "CONSUMED_ONCE", "evidence.consume_id": body["consume_id"],
            "evidence.right_id": body["right_id"], "evidence.gate_role": body["gate_role"],
            "evidence.request": body["request"], "evidence.version_after": 2,
            "right.state": "CONSUMED", "right.version": 2, "right.admission_id": None,
        })
        _assert_paths(diagnostics["views"], {
            "credential.phase": "CONSUMED", "credential.version": 2, "credential.version_after": 2,
            "credential.admission_id": None, "credential.consume_id": body["consume_id"],
            "reservation.phase": "CONSUMED", "reservation.right.state": "CONSUMED",
            "reservation.right.version": 2, "reservation.right.admission_id": None,
            "reservation.admission_id": None, "reservation.consume_id": body["consume_id"],
            "reservation.slot_state": "ISSUED", "reservation.slot_right_id": body["right_id"],
        })
        binding = {field: body[field] for field in ("gate_role", "request", "right_id", "version")}
        for name, journal_body in (("reservation", binding), ("admission", {**binding, "external_dependency": None})):
            consumes = [row for row in diagnostics["machines"][name]["journal"] if row["op"] == "consume"]
            self.assertEqual(_bytes(consumes), _bytes([{
                "op": "consume", "subject_id": body["consume_id"],
                "idempotency_key": body["idempotency_key"], "body": journal_body,
            }]), name)

    def _replay_case(self, host, case, case_index):
        outcomes = []
        for step_index, step in enumerate(case["steps"]):
            with self.subTest(case=case["id"], step=step["id"]):
                envelope = {field: step[field] for field in ("operationId", "actor", "action", "body")}
                action, body = step["action"], step["body"]
                outcome = {"id": step["id"], "action": action,
                           "input_ref": f"{FIXTURE}#/cases/{case_index}/steps/{step_index}/body"}
                before = snapshot(host)
                if "expect_error" in step:
                    with self.assertRaises(FsmRejected) as error:
                        self._call(host, envelope)
                    outcome["rejection_code"] = error.exception.code
                    self.assertEqual(outcome["rejection_code"], step["expect_error"])
                    after = snapshot(host)
                    self.assertTrue(_bytes(before) == _bytes(after), "refusal changed state or an accepted journal")
                    diagnostics = self._diagnostics(host, after)
                    self.assertTrue(_bytes(diagnostics) == _bytes(outcomes[-1]["diagnostic_snapshot"]),
                                    "refusal changed diagnostics from the winning authorization")
                else:
                    receipt = self._call(host, envelope)
                    _assert_paths(receipt, step["expect"])
                    after = snapshot(host)
                    spec = self.catalogue.fsm["commands"][action]
                    check_journal(self, spec, body, before, after, BOUND_DELTAS)
                    diagnostics = self._diagnostics(host, after)
                    if spec["op"] == "consume":
                        self._assert_consumed(receipt, diagnostics, body)
                    else:
                        self._assert_authorized(receipt, diagnostics["views"], body)
                    outcome["receipt"] = copy.deepcopy(receipt)
                outcome["diagnostic_snapshot"] = diagnostics
                outcomes.append(outcome)
        return {"id": case["id"], "steps": outcomes}

    def _observe(self):
        raw = (ROOT / FIXTURE).read_bytes()
        fixture = goldens._decode(raw)
        self.assertTrue(_bytes(fixture) == raw, "non-canonical input bytes")
        source_bytes = {path: (ROOT / path).read_bytes() for path in SOURCE_PATHS}
        sources = [goldens._pin(path, data) for path, data in source_bytes.items()]
        self.assertEqual(fixture["sources"], sources)
        self.assertEqual(fixture["checkpoint"], CHECKPOINT)
        self.catalogue = load_catalogue(ROOT)
        _assert_paths(fixture, {
            "fixture_version": 1, "domain": self.catalogue.fsm_domain,
            "provenance": "OFFLINE_CONFORMANCE_FIXTURE_ONLY", "semantic_consumer_status": SEMANTIC_STATUS,
        })
        documents = {path: goldens._decode(data) for path, data in source_bytes.items() if path.endswith(".json")}
        indexed = documents[FULL_RECEIPT_INDEX]
        for path in (RECEIPTS, BOOKING_BRANCH_RECEIPTS):
            self.assertIn(goldens._pin(path, source_bytes[path]), indexed["sources"])
        vectors = {vector["id"]: vector for vector in documents[VECTORS]["vectors"]}
        adoption = vectors[CHECKPOINT["vector_id"]]
        self.assertEqual(len(adoption["setup"]), 7)
        history = [vectors[vid] for vid in [*adoption["setup"], adoption["id"]]]
        for step, label in (("payment-B", "payment"), ("issue-B", "issuance"), ("adopt-B", "adoption")):
            self.assertEqual(indexed["receipts"][f"{CONTEXT}/{step}"]["receipt_ref"],
                             CHECKPOINT[f"{label}_receipt_ref"])
        self.assertEqual(_bytes(fixture["cases"]), _bytes(_expected_cases(vectors)))

        cases, checkpoints = [], []
        for case_index, case in enumerate(fixture["cases"]):
            envelopes = [vector["envelope"] for vector in history] + case["steps"]
            operations = {envelope["operationId"] for envelope in envelopes}
            keys = {envelope["body"]["idempotency_key"] for envelope in envelopes}
            self.assertEqual(len(operations), len(envelopes))
            self.assertEqual(len(keys), len(envelopes))
            self.assertTrue(operations.isdisjoint(keys))
            host, checkpoint = self._replay_checkpoint(history, documents)
            checkpoints.append(checkpoint)
            cases.append(self._replay_case(host, case, case_index))
        first, second = checkpoints
        self.assertTrue(_bytes(first) == _bytes(second), "fresh hosts began at different checkpoints")
        return {
            "record_schema_version": "kix-commerce-two-gate-admission-receipts/1",
            "record_kind": "IN_PROCESS_MOCK_RECEIPT_VECTORS",
            "normative": False,
            "semantic_consumer_status": SEMANTIC_STATUS,
            "diagnostic_snapshot_kind": "TEST_HARNESS_EVIDENCE",
            "fixture": goldens._pin(FIXTURE, raw),
            "sources": sources,
            "checkpoint": {**CHECKPOINT, "diagnostic_snapshot": first},
            "cases": cases,
        }

    def _compare_receipts(self, raw):
        self.assertTrue(_bytes(self._observe()) == raw, "complete canonical two-gate admission outcomes differ")

    def test_complete_output_bytes_and_references(self):
        self._compare_receipts(GOLDEN.read_bytes())

    def test_swapped_winning_consume_receipts_fail_comparison(self):
        detached = goldens._decode(GOLDEN.read_bytes())
        first, second = (case["steps"][-1] for case in detached["cases"])
        first["receipt"], second["receipt"] = second["receipt"], first["receipt"]
        with self.assertRaisesRegex(AssertionError, "complete canonical two-gate admission outcomes differ"):
            self._compare_receipts(_bytes(detached))


if __name__ == "__main__":
    unittest.main()
