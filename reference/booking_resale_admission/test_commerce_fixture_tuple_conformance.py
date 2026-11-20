"""Replay the pinned Commerce fixture envelopes against the in-memory producer."""

import hashlib
import json
import unittest
from collections import Counter, defaultdict

import test_commerce_journey_conformance as journey
from integration_gate.catalogue import git_blob_id, load_catalogue
from integration_gate.constants import CONTRACT_ONLY_OPENAPI, INTEGRATION_GATE_OPENAPI, LOCAL_CALL_PATH
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import EnvelopeError, parse_envelope
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
TABLE = "docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json"
VECTORS = "sdk/conformance/vectors/commerce-fixture-tuple.vectors.json"
INPUTS = "reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json"
RECEIPTS = "reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json"
PRODUCER = "8ba7f6c36373ac0ec49246f51f7471c164ac3a28"
TREE = "d3f5412ef84f64fe83c5d3a3d3ada173921bfbf9"
COMMERCE = "9a55fe4e257376f9db3f877a11b65e3ecc43c661"
LEVEL = "SEMANTIC_CONFORMANCE"
FALSE_FLAGS = set(NON_CLAIMS) | set(journey.SETTLEMENT_FINALITY_FLAGS) | {
    "chain_issued", "economic_finality_claimed", "venue_credential_reissued",
    "offline_admission", "production_endpoint", "production_conformance",
}
EXTERNAL_FLAGS = {"external_payment", "external_admission", "external_marketplace"}


def read(path):
    return (ROOT / path).read_bytes()


def snapshot(host):
    return {
        name: (machine.canonical_state(), machine.export_journal())
        for name, machine in host.machines.items()
    }


class CommerceFixtureTupleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = json.loads(read(TABLE))
        cls.corpus = json.loads(read(VECTORS))
        cls.vectors = cls.corpus["vectors"]
        cls.by_id = {vector["id"]: vector for vector in cls.vectors}
        cls.catalogue = load_catalogue(ROOT)
        cls.openapi = json.loads(read(CONTRACT_ONLY_OPENAPI))
        cls.gate = json.loads(read(INTEGRATION_GATE_OPENAPI))
        cls.source_steps = json.loads(read(INPUTS))["steps"]
        cls.golden_steps = json.loads(read(RECEIPTS))["steps"]

    def check_scope(self, tuples):
        inventory = self.table["commerce_source"]
        subjects = inventory["command_subjects"]
        self.assertEqual(set(subjects), journey.PRIMARY_ACTIONS | {"resale_cancel_listing"})
        self.assertEqual(Counter(row["action"] for row in tuples), Counter(subjects.keys()))
        self.assertIn("post", self.gate["paths"][LOCAL_CALL_PATH])
        gate_operations = {row["action"]: row for row in self.gate["x-kix-local-call-operations"]}
        self.assertEqual(len(self.by_id), len(self.vectors), "duplicate vector ID")
        self.assertEqual(
            len({v["envelope"]["operationId"] for v in self.vectors}), len(self.vectors)
        )
        self.assertEqual(set(inventory["contexts"]), {
            "booking-resale", "booking-admission", "booking-refund", "resale-market",
        })
        vectors_by_action = defaultdict(list)
        declared_steps = defaultdict(list)
        for vector in self.vectors:
            self.assertEqual(vector["id"].split("/")[0], vector["context"])
            self.assertIn(vector["context"], inventory["contexts"])
            action = vector["envelope"]["action"]
            vectors_by_action[action].append(vector["id"])
            if "commerce_step" in vector:
                declared_steps[(vector["context"], vector["commerce_step"])].append(vector)
        required_steps = set()
        for context, plan in inventory["contexts"].items():
            for index, step in enumerate(plan["steps"]):
                key = (context, step)
                required_steps.add(key)
                self.assertEqual(len(declared_steps[key]), 1, key)
                row = declared_steps[key][0]
                self.assertEqual(row["expected"]["kind"], "accept", key)
                self.assertEqual(self.accepted_setup_steps(row), plan["steps"][:index], key)
            for when in ("alternatives_before", "alternatives_after"):
                for anchor, step in plan[when].items():
                    key = (context, step)
                    required_steps.add(key)
                    index = plan["steps"].index(anchor) + (when == "alternatives_after")
                    matching = [
                        v for v in declared_steps[key]
                        if self.accepted_setup_steps(v) == plan["steps"][:index]
                    ]
                    self.assertEqual(len(matching), 1, (key, anchor))
                    outcome = "accept" if step == "market-cancel" else "business-reject"
                    self.assertEqual(matching[0]["expected"]["kind"], outcome, key)
        self.assertEqual(set(declared_steps), required_steps)
        market_cancels = declared_steps[("resale-market", "market-cancel")]
        self.assertEqual(len(market_cancels), 2)
        self.assertEqual({v["market_cancel_from"] for v in market_cancels}, {"LISTED", "BUY_HELD"})

        for row in tuples:
            action = row["action"]
            spec = self.catalogue.fsm["commands"][action]
            self.assertEqual(row["method"], "POST")
            self.assertEqual(row["path"], LOCAL_CALL_PATH)
            self.assertEqual(row["source_authentication"], "FIXTURE_ONLY")
            self.assertEqual(row["level"], LEVEL)
            self.assertTrue(row["reason"].strip())
            for key in ("machine", "op", "subject_field"):
                self.assertEqual(row[key], spec[key])
            self.assertEqual(row["subject_field"], subjects[action])
            self.assertEqual(self.openapi["components"]["schemas"][action], spec["schema"])
            transport = gate_operations[action]
            self.assertEqual(transport["requestBodySchema"],
                             f"kix-protocol.contract-only.openapi.json#/components/schemas/{action}")
            self.assertEqual(transport["localCallParameters"], ["operationId", "actor", "action", "body"])
            self.assertIs(transport["x-kix-production-endpoint"], False)
            digest = hashlib.sha256(_canonical(spec["schema"]).encode()).hexdigest()
            self.assertEqual(row["body_schema_sha256"], digest)

            expected_contexts = defaultdict(lambda: {"steps": defaultdict(list), "controls": []})
            expected_ids = vectors_by_action[action]
            self.assertEqual(row["vector_ids"], sorted(expected_ids))
            kinds = set()
            for vid in expected_ids:
                vector = self.by_id[vid]
                scope = expected_contexts[vector["context"]]
                kinds.add(vector["expected"]["kind"])
                if "commerce_step" in vector:
                    scope["steps"][vector["commerce_step"]].append(vid)
                else:
                    scope["controls"].append(vid)
            self.assertTrue({"accept", "business-reject"} <= kinds)
            self.assertEqual(Counter(c["context"] for c in row["contexts"]),
                             Counter(expected_contexts.keys()))
            for context in row["contexts"]:
                scope = expected_contexts[context["context"]]
                self.assertTrue(scope["steps"], context["context"])
                self.assertEqual(context["steps"], scope["steps"])
                self.assertEqual(context["control_vector_ids"], sorted(scope["controls"]))
                context_ids = [vid for ids in context["steps"].values() for vid in ids]
                context_ids += context["control_vector_ids"]
                self.assertIn("business-reject", {
                    self.by_id[vid]["expected"]["kind"] for vid in context_ids
                })

    def accepted_setup_steps(self, vector):
        return [
            entry["commerce_step"] for vid in vector["setup"]
            if (entry := self.by_id[vid])["expected"]["kind"] == "accept"
        ]

    def test_inventory_and_edges(self):
        self.assertEqual(self.table["record_schema_version"], "kix-commerce-fixture-tuple-conformance/1")
        self.assertEqual(self.corpus["record_schema_version"], "kix-commerce-fixture-vectors/1")
        self.assertEqual(_canonical(self.table).encode(), read(TABLE))
        self.assertEqual(_canonical(self.corpus).encode(), read(VECTORS))
        self.assertEqual(self.catalogue.fsm["sourceAuthentication"], "FIXTURE_ONLY")
        self.check_scope(self.table["tuples"])

    def test_inventory_rejects_missing_duplicate_and_crossed_evidence(self):
        tuples = self.table["tuples"]
        malformed = (
            tuples[1:],
            [tuples[0], *tuples],
            [{**tuples[0], "vector_ids": tuples[1]["vector_ids"]}, *tuples[1:]],
            [{**tuples[0], "contexts": []}, *tuples[1:]],
        )
        for rows in malformed:
            with self.assertRaises(AssertionError):
                self.check_scope(rows)

    def test_replay_dependency_bytes_and_producer(self):
        self.assertEqual(self.table["producer"]["source_commit"], PRODUCER)
        self.assertEqual(self.table["producer"]["source_tree"], TREE)
        self.assertEqual(self.table["commerce_source"]["commit"], COMMERCE)
        pins = self.table["pins"]
        paths = [pin["path"] for group in pins.values() for pin in group]
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual([pin["path"] for pin in pins["earlier_evidence"]], [RECEIPTS])
        self.assertTrue({
            CONTRACT_ONLY_OPENAPI, INTEGRATION_GATE_OPENAPI, INPUTS,
            "docs/contracts/openapi/fsm-command-contract.json",
            "reference/v0.3-rc1/protocol_contract.json",
            "sdk/generated/catalogue.ts", "sdk/generate/generate_client.mjs",
            "sdk/compat/manifests/manifest.bootstrap-2.json",
            "sdk/compat/profiles/bootstrap-2.profile.json",
            "integration_gate/catalogue.py", "integration_gate/schema.py",
            "integration_gate/fsm_host.py",
        } <= set(paths))
        for group in pins.values():
            for ref in group:
                with self.subTest(path=ref["path"]):
                    raw = read(ref["path"])
                    self.assertEqual(git_blob_id(raw), ref["gitBlob"])
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), ref["sha256"])

    def test_vectors(self):
        # Treat every target as a separate replay so a previous test cannot supply setup.
        for vector in self.vectors:
            with self.subTest(vector=vector["id"]):
                host = FsmHost()
                receipts = {}
                setup = vector["setup"]
                self.assertEqual(len(set(setup)), len(setup))
                self.assertNotIn(vector["id"], setup)
                for index, vid in enumerate(setup):
                    entry = self.by_id[vid]
                    self.assertEqual(entry["context"], vector["context"])
                    self.assertEqual(entry["setup"], setup[:index])
                    self.replay(host, entry, receipts)
                self.replay(host, vector, receipts)

    def replay(self, host, vector, receipts):
        envelope = vector["envelope"]
        self.assertEqual(envelope["actor"], "commerce-journey-fixture")
        self.assertNotEqual(envelope["operationId"], envelope["body"]["idempotency_key"])
        expected = vector["expected"]
        kind = expected["kind"]
        before = snapshot(host)
        if kind == "schema-reject":
            with self.assertRaises(EnvelopeError) as error:
                parse_envelope(envelope, self.catalogue.commands)
            self.assertEqual(error.exception.error, expected["code"])
            self.assertEqual(snapshot(host), before)
            return

        operation, actor, action, body = parse_envelope(envelope, self.catalogue.commands)
        self.assertEqual((operation, actor, action, body), (
            envelope["operationId"], envelope["actor"], envelope["action"], envelope["body"],
        ))
        if "input_index" in vector:
            from_input = self.source_steps[vector["input_index"]]
            self.assertEqual((from_input["id"], from_input["action"], from_input["body"]),
                             (vector.get("commerce_step", "replay-consume-B"), action, body))
            if kind == "business-reject":
                self.assertEqual(expected["code"], from_input["expect_error"])
            else:
                for path, value in from_input["expect"]["paths"].items():
                    self.assertEqual(_canonical(expected["receipt_fields"][path]), _canonical(value))
        if "replay_of" in vector:
            original = self.by_id[vector["replay_of"]]["envelope"]
            self.assertIn(vector["replay_of"], vector["setup"])
            self.assertNotEqual(operation, original["operationId"])
            self.assertEqual((action, body), (original["action"], original["body"]))
        if "market_cancel_from" in vector:
            listing = host.machines["resale"].view(body["listing_id"])
            self.assertEqual(listing["phase"], vector["market_cancel_from"])

        if kind == "business-reject":
            with self.assertRaises(FsmRejected) as error:
                host.call(action, body)
            self.assertEqual(error.exception.code, expected["code"])
            self.assertEqual(snapshot(host), before)
            return

        self.assertIn(kind, {"accept", "duplicate"})
        receipt = host.call(action, body)
        spec = self.catalogue.fsm["commands"][action]
        machine = spec["machine"]
        self.assertIs(receipt["duplicate"], kind == "duplicate")
        self.assertEqual(receipt["applied"], spec["op"] if kind == "accept" else None)
        self.assertEqual(receipt["provenance"],
                         "MOCK_SETTLEMENT_ONLY" if machine == "settlement" else "MOCK_GATE_ONLY")
        self.assertIs(receipt["funds_executed"], False)
        for node in journey._walk(receipt):
            for key in node.keys() & FALSE_FLAGS:
                self.assertIs(node[key], False, key)
            for key in node.keys() & EXTERNAL_FLAGS:
                self.assertEqual(node[key], "UNSUPPORTED", key)
        for path, value in expected["receipt_fields"].items():
            self.assertEqual(_canonical(journey._resolve(receipt, path)), _canonical(value), path)
        if "receipt_ref" in expected:
            index = vector["input_index"]
            self.assertEqual(expected["receipt_ref"], f"{RECEIPTS}#/steps/{index}/receipt")
            golden = self.golden_steps[index]
            self.assertEqual(golden["action"], action)
            self.assertEqual(_canonical(receipt), _canonical(golden["receipt"]))
        if kind == "duplicate":
            self.assertEqual(snapshot(host), before)
            first = receipts[vector["replay_of"]]
            self.assertEqual(_canonical(receipt), _canonical({**first, "duplicate": True, "applied": None}))
        else:
            self.check_journal(host, spec, body, before, expected["journal_delta"])
        receipts[vector["id"]] = receipt

    def check_journal(self, host, spec, body, before, deltas):
        machine = spec["machine"]
        self.assertEqual(deltas.get(machine), 1)
        after = snapshot(host)
        self.assertTrue(deltas.keys() <= after.keys())
        for name, (state, journal) in after.items():
            old_state, old_journal = before[name]
            self.assertEqual(len(journal) - len(old_journal), deltas.get(name, 0), name)
            self.assertEqual(journal[:len(old_journal)], old_journal, name)
            if name not in deltas:
                self.assertEqual(state, old_state, name)
        entry = after[machine][1][-1]
        self.assertEqual(entry["op"], spec["op"])
        self.assertEqual(entry["idempotency_key"], body["idempotency_key"])
        subject_key = "settlement_id" if machine == "settlement" else "subject_id"
        self.assertEqual(entry[subject_key], body[spec["subject_field"]])
