"""Source-informed in-process receipt vectors with detached harness evidence."""
from __future__ import annotations

import copy
import unittest

import test_commerce_entry_resale_order_vectors as ordering
import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
import test_commerce_temporal_vectors as temporal
from integration_gate.catalogue import load_catalogue
from scripts.bootstrap_2_fixtures import read_bootstrap_2_input
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import _canonical

ROOT = journey.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_admission_replay_after_resale_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_admission_replay_after_resale_receipts_v1.json"
GOLDEN_PATH = GOLDEN.relative_to(ROOT).as_posix()
SOURCE_PATHS = goldens.SOURCE_PATHS | frozenset({
    ordering.FIXTURE,
    temporal.FIXTURE,
    "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md",
    "reference/booking_resale_admission/test_commerce_entry_resale_order_vectors.py",
    "reference/booking_resale_admission/test_commerce_journey_receipts.py",
    "reference/booking_resale_admission/test_commerce_temporal_vectors.py",
})
CASE = "admission-replay-after-resale"
ORDER = ordering.SETUP + (
    "admission-clock", "admission-adopt", "authorize", "admission-expiry-clock",
    "resale-expiry-clock", "list", "resale-payment", "transfer",
    "replay-authorize", "consume-old-after-resale",
)
MACHINES = {"reservation", "resale", "admission", "settlement", "credit"}
EXPIRY_MS = 1120000
SEMANTIC_STATUS = "HOLD_SEMANTIC"
DIAGNOSTIC_KIND = "TEST_HARNESS_EVIDENCE"


def _read(path):
    return read_bootstrap_2_input(path)


def _step_ref(path, index, field):
    return f"{path}#/cases/0/steps/{index}/{field}"


class CommerceAdmissionReplayAfterResaleVectorTests(unittest.TestCase):
    def _validate_inputs(self, fixture):
        self.assertIs(type(fixture["fixture_version"]), int)
        self.assertEqual(fixture["fixture_version"], 1)
        self.assertEqual(fixture["provenance"], "OFFLINE_CONFORMANCE_FIXTURE_ONLY")
        self.assertEqual(fixture["semantic_consumer_status"], SEMANTIC_STATUS)
        catalogue = load_catalogue(ROOT)
        self.assertEqual(fixture["domain"], catalogue.fsm_domain)
        case, = fixture["cases"]
        self.assertEqual(case["id"], CASE)
        self.assertEqual(case["clocks"], {
            "meaning": "SYNTHETIC_FIXTURE_INPUTS_ONLY",
            "start_ms": 1000000, "authorization_expiry_ms": EXPIRY_MS,
        })
        steps = case["steps"]
        self.assertEqual(tuple(step["id"] for step in steps), ORDER)
        self.assertEqual(
            {step["id"]: step["expect_error"] for step in steps if "expect_error" in step},
            {"consume-old-after-resale": "STALE_VERSION"},
        )
        self.assertEqual(
            {step["id"]: step["replay_of"] for step in steps if "replay_of" in step},
            {"replay-authorize": "authorize"},
        )

        prefix = goldens._decode(_read(ordering.FIXTURE))["cases"][1]
        self.assertEqual(prefix["id"], "entry-consumption-before-resale")
        temporal_case = next(case for case in goldens._decode(_read(temporal.FIXTURE))["cases"]
                             if case["id"] == "transfer-stale-presentations")
        resale_steps = {step["id"]: step for step in temporal_case["steps"]}
        for step, source in zip(steps[:11] + steps[13:16],
                                prefix["steps"][:11] + [resale_steps[key] for key in ORDER[13:16]]):
            self.assertEqual(step["action"], source["action"])
            self.assertEqual(_canonical(step["body"]), _canonical(source["body"]))

        original, replay, consume = steps[10], steps[16], steps[17]
        self.assertEqual(replay["action"], original["action"])
        self.assertEqual(_canonical(replay["body"]), _canonical(original["body"]))
        self.assertEqual(consume["action"], "admission_consume")
        self.assertTrue(all(consume["body"][field] == original["body"][field]
                            for field in ("right_id", "version", "gate_role", "request")))
        self.assertEqual(consume["body"]["consume_id"], "consume-old-after-resale")
        for step, action in zip(steps[11:13], ("admission_set_clock", "resale_set_clock")):
            self.assertEqual(step["action"], action)
            self.assertEqual(step["body"]["now_ms"], original["body"]["expires_ms"])

        keys = set()
        for step in steps:
            with self.subTest(step=step["id"]):
                self.assertNotEqual("expect" in step, "expect_error" in step)
                action, body = step["action"], step["body"]
                self.assertIn(action, catalogue.fsm_names)
                spec = catalogue.fsm["commands"][action]
                self.assertEqual(problems(body, spec["schema"]), [])
                self.assertIn(spec["subject_field"], body)
                self.assertNotIn("domain", body)
                key = body["idempotency_key"]
                self.assertEqual(key in keys, "replay_of" in step)
                keys.add(key)
                if "expect" in step:
                    expect = step["expect"]
                    self.assertIs(expect["duplicate"], "replay_of" in step)
                    self.assertEqual(expect["applied"], None if expect["duplicate"] else spec["op"])
                    self.assertCountEqual([item["machine"] for item in expect["journal"]], MACHINES)

    def _observe(self, case):
        host = FsmHost()
        accepted = set()
        outcomes = []
        before = ordering._snapshot(host, accepted)
        for index, step in enumerate(case["steps"]):
            action = step["action"]
            outcome = {
                "id": step["id"], "action": action,
                "input_ref": _step_ref(FIXTURE, index, "body"),
            }
            try:
                receipt = host.call(action, copy.deepcopy(step["body"]))
            except FsmRejected as exc:
                self.assertEqual(exc.code, step.get("expect_error"), step["id"])
                outcome["rejection_code"] = exc.code
            else:
                self.assertIn("expect", step, step["id"])
                expect = step["expect"]
                self.assertIs(receipt["duplicate"], expect["duplicate"], step["id"])
                self.assertEqual(receipt["applied"], expect["applied"], step["id"])
                temporal._assert_paths(receipt, expect["paths"])
                outcome["receipt"] = copy.deepcopy(receipt)
                accepted.add(action)

            after = ordering._snapshot(host, accepted)
            if "receipt" in outcome:
                for item in step["expect"]["journal"]:
                    name = item["machine"]
                    delta = len(after["machines"][name]["journal"]) - len(before["machines"][name]["journal"])
                    self.assertEqual(delta, item["delta"], f"{step['id']}: {name}")
            outcome["diagnostic_snapshot"] = after
            outcomes.append(outcome)
            before = after
        return {"id": case["id"], "steps": outcomes}

    def _assert_history(self, outcomes):
        steps = {step["id"]: step for step in outcomes}
        first = steps["authorize"]["receipt"]
        replay = steps["replay-authorize"]["receipt"]
        temporal._assert_paths(first, {
            "admission.admission_id": "admit-1", "admission.expired": False,
            "admission.expires_ms": EXPIRY_MS, "admission.gate_role": "gate-a",
            "right.holder_role": "buyer-1", "right.version": 1,
        })
        self.assertIs(replay["duplicate"], True)
        self.assertIsNone(replay["applied"])
        self.assertEqual(_canonical(journey._without_replay_keys(first)),
                         _canonical(journey._without_replay_keys(replay)))
        self.assertEqual(steps["consume-old-after-resale"]["rejection_code"], "STALE_VERSION")

        for step_id, resale_ms in (("admission-expiry-clock", 1000000), ("resale-expiry-clock", EXPIRY_MS)):
            snapshot = steps[step_id]["diagnostic_snapshot"]
            for machine, now in (("admission", EXPIRY_MS), ("reservation", EXPIRY_MS), ("resale", resale_ms)):
                state = goldens._decode(snapshot["machines"][machine]["state"].encode("utf-8"))
                self.assertEqual(state["logical_time_ms"], now, f"{step_id}: {machine}")
            temporal._assert_paths(snapshot["views"], {
                "credential.admission_expired": True, "credential.admission_id": None,
                "reservation.admission_expired": True, "reservation.admission_id": None,
            })

        payment = steps["resale-payment"]["receipt"]
        transfer = steps["transfer"]["receipt"]
        self.assertNotEqual(payment["listing"]["payment_ref"],
                            steps["payment"]["receipt"]["reservation"]["payment_ref"])
        self.assertEqual(transfer["evidence"]["payment_ref"], payment["listing"]["payment_ref"])
        temporal._assert_paths(payment, {
            "listing.phase": "PAYMENT_NOTED", "listing.transfer_id": None,
            "right.holder_role": "buyer-1", "right.version": 1,
        })
        temporal._assert_paths(transfer, {"evidence.transfer_id": "transfer-1"})

        previous = None
        for step_id in ("transfer", "replay-authorize", "consume-old-after-resale"):
            snapshot = steps[step_id]["diagnostic_snapshot"]
            self.assertEqual(set(snapshot["machines"]), MACHINES)
            temporal._assert_paths(snapshot["views"], {
                "resale_right.right.right_id": "issue-1", "resale_right.right.holder_role": "buyer-2",
                "resale_right.right.version": 2, "credential.consume_id": None, "reservation.consume_id": None,
            })
            if previous is not None:
                self.assertEqual(_canonical(snapshot), _canonical(previous), step_id)
            previous = snapshot

    def test_complete_output_bytes_and_references(self):
        fixture_raw = _read(FIXTURE)
        raw = GOLDEN.read_bytes()
        golden = goldens._decode(raw)
        fixture_pin = goldens._pin(FIXTURE, fixture_raw)
        sources = [goldens._pin(path, _read(path)) for path in sorted(SOURCE_PATHS)]
        self.assertEqual(golden["fixture"], fixture_pin)
        self.assertEqual(golden["sources"], sources)

        fixture = goldens._decode(fixture_raw)
        self.assertEqual(_canonical(fixture).encode("utf-8"), fixture_raw)
        self._validate_inputs(fixture)
        case, = fixture["cases"]
        observed = self._observe(case)
        self._assert_history(observed["steps"])
        self.assertTrue(_canonical({
            "record_schema_version": "kix-commerce-admission-replay-after-resale-receipts/1",
            "record_kind": "IN_PROCESS_MOCK_RECEIPT_VECTORS",
            "normative": False,
            "semantic_consumer_status": SEMANTIC_STATUS,
            "diagnostic_snapshot_kind": DIAGNOSTIC_KIND,
            "fixture": fixture_pin, "sources": sources, "cases": [observed],
        }).encode("utf-8") == raw, "complete canonical receipt bytes differ")

        references = {}
        for label, index, field in (
            ("authorize_request", 10, "body"), ("authorize_receipt", 10, "receipt"),
            ("replay_request", 16, "body"), ("replay_receipt", 16, "receipt"),
            ("consume_request", 17, "body"), ("consume_refusal", 17, "rejection_code"),
        ):
            path = FIXTURE if field == "body" else GOLDEN_PATH
            ref = _step_ref(path, index, field)
            references[label] = ref
            self.assertEqual(case["evidence_refs"][label], ref)
            target_path, pointer = case["evidence_refs"][label].split("#", 1)
            resolved = {FIXTURE: fixture, GOLDEN_PATH: golden}[target_path]
            for part in pointer[1:].split("/"):
                resolved = resolved[int(part)] if isinstance(resolved, list) else resolved[part]
            expected_step = (case if field == "body" else observed)["steps"][index]
            self.assertEqual(_canonical(resolved), _canonical(expected_step[field]))
        self.assertEqual(case["evidence_refs"], references)


if __name__ == "__main__":
    unittest.main()
