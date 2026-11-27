"""Source-informed mock evidence for three presentations of one replacement."""
from __future__ import annotations

import copy
import unittest

import test_commerce_journey_receipts as goldens
import test_commerce_temporal_vectors as temporal
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import _canonical

ROOT = goldens.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_replaced_admission_binding_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_replaced_admission_binding_receipts_v1.json"
TEMPORAL_RECEIPTS = temporal.GOLDEN.relative_to(ROOT).as_posix()
SOURCE_PATHS = goldens.SOURCE_PATHS | frozenset({
    temporal.FIXTURE,
    TEMPORAL_RECEIPTS,
    "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md",
    "reference/booking_resale_admission/test_commerce_journey_receipts.py",
    "reference/booking_resale_admission/test_commerce_temporal_vectors.py",
})
CASE = "replaced-admission-binding"
SEMANTIC_STATUS = "HOLD_SEMANTIC"
MACHINES = {"reservation", "resale", "admission", "settlement", "credit"}
CROSSED_PRESENTATIONS = (
    ("consume-old-gate", "gate-a", "22" * 32, "GATE_MISMATCH"),
    ("consume-old-request", "gate-b", "11" * 32, "ADMISSION_REQUEST_MISMATCH"),
)


class CommerceReplacedAdmissionBindingVectorTests(unittest.TestCase):
    def _validate_inputs(self, fixture):
        catalogue = load_catalogue(ROOT)
        temporal_case = goldens._decode((ROOT / temporal.FIXTURE).read_bytes())["cases"][2]
        self.assertEqual(temporal_case["id"], "expired-authorization-replacement")
        self.assertIs(type(fixture["fixture_version"]), int)
        self.assertEqual(fixture["fixture_version"], 1)
        self.assertEqual(fixture["provenance"], "OFFLINE_CONFORMANCE_FIXTURE_ONLY")
        self.assertEqual(fixture["domain"], catalogue.fsm_domain)
        self.assertEqual(fixture["semantic_consumer_status"], SEMANTIC_STATUS)
        case, = fixture["cases"]
        self.assertEqual(case["id"], CASE)
        self.assertEqual(_canonical(case["clocks"]), _canonical(temporal_case["clocks"]))

        steps = case["steps"]
        self.assertEqual(len(steps), 15)
        source_steps = temporal_case["steps"]
        self.assertEqual(steps[11]["id"], "replace")
        self.assertEqual(_canonical(steps[:12]), _canonical(source_steps[:12]))
        self.assertEqual(_canonical(steps[14]), _canonical(source_steps[12]))
        self.assertEqual(steps[14]["body"], {
            "consume_id": "consume-2", "idempotency_key": "consume",
            "right_id": "issue-1", "version": 1, "gate_role": "gate-b", "request": "22" * 32,
        })
        for step, (identity, gate, request, code) in zip(steps[12:14], CROSSED_PRESENTATIONS):
            self.assertEqual(step, {
                "id": identity, "action": "admission_consume", "expect_error": code,
                "body": {
                    "consume_id": identity, "idempotency_key": identity,
                    "right_id": "issue-1", "version": 1, "gate_role": gate, "request": request,
                },
            })

        keys, consume_ids = set(), set()
        for step in steps:
            with self.subTest(step=step["id"]):
                action, body = step["action"], step["body"]
                self.assertIn(action, catalogue.fsm_names)
                self.assertEqual(problems(body, catalogue.fsm["commands"][action]["schema"]), [])
                self.assertNotIn(body["idempotency_key"], keys)
                keys.add(body["idempotency_key"])
                if action == "admission_consume":
                    self.assertNotIn(body["consume_id"], consume_ids)
                    consume_ids.add(body["consume_id"])

    def _observe(self, case):
        host = FsmHost()
        accepted = set()
        outcomes = []
        for index, step in enumerate(case["steps"]):
            action = step["action"]
            outcome = {
                "id": step["id"], "action": action,
                "input_ref": f"{FIXTURE}#/cases/0/steps/{index}/body",
            }
            try:
                receipt = host.call(action, copy.deepcopy(step["body"]))
            except FsmRejected as exc:
                self.assertEqual(exc.code, step.get("expect_error"), step["id"])
                outcome["rejection_code"] = exc.code
            else:
                self.assertIn("expect", step, step["id"])
                expect = step["expect"]
                temporal._assert_paths(receipt, {
                    "duplicate": expect["duplicate"], "applied": expect["applied"], **expect["paths"],
                })
                outcome["receipt"] = copy.deepcopy(receipt)
                accepted.add(action)
            after = temporal._snapshot(host, accepted)
            if "rejection_code" in outcome:
                before = outcomes[-1]["diagnostic_snapshot"]
                self.assertTrue(_canonical(before) == _canonical(after), step["id"])
            for view, paths in step.get("observe", {}).items():
                temporal._assert_paths(after["views"][view], paths)
            outcome["diagnostic_snapshot"] = after
            outcomes.append(outcome)
        return {"id": case["id"], "steps": outcomes}

    def _assert_presentations(self, steps, consume):
        temporal._assert_paths(steps[11]["receipt"], {
            "admission.admission_id": "admit-2", "admission.gate_role": "gate-b",
            "admission.request": "22" * 32, "admission.expires_ms": 1240000,
        })
        for step in steps[11:14]:
            snapshot = step["diagnostic_snapshot"]
            self.assertEqual(set(snapshot["machines"]), MACHINES)
            temporal._assert_paths(snapshot["views"], {
                "credential.right_id": "issue-1", "credential.version": 1,
                "credential.phase": "AUTHORIZED", "credential.admission_id": "admit-2",
                "credential.gate_role": "gate-b", "credential.admission_expired": False,
                "credential.consume_id": None, "reservation.consume_id": None,
                "reservation.phase": "ADMISSION_AUTHORIZED", "reservation.right.version": 1,
                "reservation.right.right_id": "issue-1", "reservation.admission_id": "admit-2",
            })

        last = steps[14]
        temporal._assert_paths(last["receipt"], {
            "duplicate": False, "applied": "consume", "evidence.decision": "CONSUMED_ONCE",
            "evidence.consume_id": "consume-2",
        })
        snapshot = last["diagnostic_snapshot"]
        temporal._assert_paths(snapshot["views"], {
            "credential.phase": "CONSUMED", "credential.version": 2, "credential.version_after": 2,
            "credential.admission_id": None, "credential.consume_id": "consume-2",
            "reservation.phase": "CONSUMED", "reservation.right.version": 2,
            "reservation.admission_id": None, "reservation.consume_id": "consume-2",
            "reservation.slot_state": "ISSUED",
        })
        previous = steps[13]["diagnostic_snapshot"]
        for machine in ("admission", "reservation"):
            for state_at_step in (steps[11]["diagnostic_snapshot"], snapshot):
                state = goldens._decode(state_at_step["machines"][machine]["state"].encode("utf-8"))
                self.assertEqual(state["logical_time_ms"], 1120000)
            binding = {field: consume[field] for field in ("right_id", "version", "gate_role", "request")}
            if machine == "admission":
                binding["external_dependency"] = None
            journal = snapshot["machines"][machine]["journal"]
            prior_journal = previous["machines"][machine]["journal"]
            entry = {
                "op": "consume", "subject_id": "consume-2",
                "idempotency_key": consume["idempotency_key"], "body": binding,
            }
            self.assertEqual(_canonical(journal), _canonical(prior_journal + [entry]), machine)
            self.assertEqual(sum(row["op"] == "consume" for row in journal), 1, machine)

    def _assert_evidence_refs(self, case, steps):
        refs = case["evidence_refs"]
        self.assertEqual(refs, {
            "payment_receipt": TEMPORAL_RECEIPTS + "#/cases/2/steps/4/receipt",
            "issuance_receipt": TEMPORAL_RECEIPTS + "#/cases/2/steps/5/receipt",
        })
        source = goldens._decode((ROOT / TEMPORAL_RECEIPTS).read_bytes())
        self.assertEqual(source["cases"][2]["id"], "expired-authorization-replacement")
        for label, index in (("payment_receipt", 4), ("issuance_receipt", 5)):
            _, pointer = refs[label].split("#/")
            resolved = source
            for part in pointer.split("/"):
                resolved = resolved[int(part)] if isinstance(resolved, list) else resolved[part]
            self.assertEqual(_canonical(resolved), _canonical(steps[index]["receipt"]), label)

        payment, issuance = steps[4]["receipt"], steps[5]["receipt"]
        temporal._assert_paths(payment, {
            "reservation.phase": "PAYMENT_NOTED", "reservation.right": None,
        })
        temporal._assert_paths(issuance, {
            "reservation.phase": "ISSUED", "reservation.right.right_id": "issue-1",
            "reservation.right.version": 1, "reservation.payment_ref": payment["reservation"]["payment_ref"],
        })

    def test_complete_output_bytes_and_references(self):
        fixture_raw = (ROOT / FIXTURE).read_bytes()
        raw = GOLDEN.read_bytes()
        golden = goldens._decode(raw)
        fixture_pin = goldens._pin(FIXTURE, fixture_raw)
        sources = [goldens._pin(path, (ROOT / path).read_bytes()) for path in sorted(SOURCE_PATHS)]
        self.assertEqual(golden["fixture"], fixture_pin)
        self.assertEqual(golden["sources"], sources)

        fixture = goldens._decode(fixture_raw)
        self.assertTrue(_canonical(fixture).encode("utf-8") == fixture_raw, "non-canonical input bytes")
        self._validate_inputs(fixture)
        case, = fixture["cases"]
        observed = self._observe(case)
        self._assert_presentations(observed["steps"], case["steps"][14]["body"])
        self._assert_evidence_refs(case, observed["steps"])
        record = {
            "record_schema_version": "kix-commerce-replaced-admission-binding-receipts/1",
            "record_kind": "IN_PROCESS_MOCK_RECEIPT_VECTORS",
            "normative": False,
            "semantic_consumer_status": SEMANTIC_STATUS,
            "diagnostic_snapshot_kind": "TEST_HARNESS_EVIDENCE",
            "fixture": fixture_pin, "sources": sources, "cases": [observed],
        }
        self.assertTrue(_canonical(record).encode("utf-8") == raw, "complete canonical receipt bytes differ")


if __name__ == "__main__":
    unittest.main()
