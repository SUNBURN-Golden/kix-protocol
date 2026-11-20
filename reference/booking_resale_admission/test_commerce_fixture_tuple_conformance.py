"""Replay the pinned Commerce fixture envelopes against the in-memory producer."""

import copy
import hashlib
import json
import unittest
from collections import Counter, defaultdict

import test_commerce_journey_conformance as journey
from test_commerce_journey_receipts import _decode, _pin
from integration_gate.catalogue import git_blob_id, load_catalogue
from integration_gate.constants import CONTRACT_ONLY_OPENAPI, INTEGRATION_GATE_OPENAPI, LOCAL_CALL_PATH
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import EnvelopeError, parse_envelope
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
TABLE = "docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json"
VECTORS = "sdk/conformance/vectors/commerce-fixture-tuple.vectors.json"
MANIFEST = "sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json"
INPUTS = "reference/booking_resale_admission/fixtures/commerce_journey_conformance_v1.json"
RECEIPTS = "reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json"
MARKET_RECEIPTS = "reference/booking_resale_admission/fixtures/commerce_market_full_receipts_v1.json"
BOOKING_BRANCH_RECEIPTS = "reference/booking_resale_admission/fixtures/commerce_booking_branch_receipts_v1.json"
BOOKING_BRANCH_SCHEMA = "kix-commerce-booking-branch-receipts/1"
BOOKING_BRANCH_STEPS = {
    "booking-resale": {"order-A", "payment-A", "issue-A"},
    "booking-admission": {"reserve-B", "order-B", "payment-B", "issue-B"},
    "booking-refund": {"reserve-C", "order-C", "cancel-C"},
}
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
        cls.corpus_raw = read(VECTORS)
        cls.corpus = _decode(cls.corpus_raw)
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
        for vector in self.vectors:
            with self.subTest(vector=vector["id"], setup=vector["setup"]):
                self.replay_target(vector)

    def replay_target(self, vector):
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
        return receipts

    def check_companion_fixture_pin(self, document):
        fixture = _pin(VECTORS, self.corpus_raw)
        self.assertEqual(document["fixture"], fixture, "companion vector pin drift")
        manifest = _decode(read(MANIFEST))
        manifest_pins = [
            (entry["path"], entry["sha256"]) for entry in manifest["vectors"]
            if entry["name"] == "commerce-fixture-request-to-receipt"
        ]
        self.assertEqual(manifest_pins, [(VECTORS, fixture["sha256"])], "manifest vector pin drift")
        return fixture

    def compare_market_receipts(self, raw):
        expected = _decode(raw)
        fixture = self.check_companion_fixture_pin(expected)
        targets = [
            vector for vector in self.vectors
            if vector["context"] == "resale-market" and vector["expected"]["kind"] == "accept"
        ]
        ids = {vector["id"] for vector in targets}
        self.assertEqual(len(targets), 14)
        self.assertEqual(len(ids), len(targets), "duplicate accepted market vector ID")
        self.assertEqual(set(expected["receipts"]), ids, "market receipt IDs differ")

        receipts = {}
        for vector in targets:
            vid = vector["id"]
            try:
                receipt = self.replay_target(vector)[vid]
                self.assertEqual(
                    _canonical(receipt), _canonical(expected["receipts"][vid]),
                    "canonical market receipt bytes differ",
                )
            except (AssertionError, KeyError) as error:
                error.add_note(f"vector={vid} setup={vector['setup']}")
                raise
            receipts[vid] = receipt
        observed = {
            "record_schema_version": "kix-commerce-market-full-receipts/1",
            "record_kind": "IN_PROCESS_MOCK_RECEIPT_VECTORS",
            "normative": False,
            "fixture": fixture,
            "receipts": receipts,
        }
        self.assertEqual(_canonical(observed).encode("utf-8"), raw, "canonical market companion bytes differ")
        return receipts

    def test_market_full_receipts(self):
        receipts = self.compare_market_receipts(read(MARKET_RECEIPTS))
        for phase, anchor in (("LISTED", "market-list"), ("BUY_HELD", "market-hold")):
            vid = f"resale-market/market-cancel-{phase}"
            vector = self.by_id[vid]
            with self.subTest(vector=vid, setup=vector["setup"]):
                self.assertEqual(vector["market_cancel_from"], phase)
                self.assertEqual(vector["setup"][-1], f"resale-market/{anchor}")
                listing, right = receipts[vid]["listing"], receipts[vid]["right"]
                self.assertEqual(listing["phase"], "CANCELLED")
                self.assertIs(listing["attached"], False)
                self.assertIsNone(right["listing_id"])
                self.assertEqual((right["right_id"], right["holder_role"], right["version"]),
                                 ("issue-1", "buyer-1", 1))

        for step, phase, transferred, holder, version in (
            ("market-pay", "PAYMENT_NOTED", False, "buyer-1", 1),
            ("market-accept", "TRANSFERRED", True, "buyer-2", 2),
        ):
            vid = f"resale-market/{step}"
            with self.subTest(vector=vid, setup=self.by_id[vid]["setup"]):
                listing, right = receipts[vid]["listing"], receipts[vid]["right"]
                self.assertEqual(listing["phase"], phase)
                self.assertIs(listing["ownership_transferred"], transferred)
                self.assertEqual(listing["settlement_gate"], "UNBOUND")
                self.assertEqual((right["right_id"], right["holder_role"], right["version"]),
                                 ("issue-1", holder, version))

    def test_market_receipt_mutations(self):
        raw = read(MARKET_RECEIPTS)
        self.compare_market_receipts(raw)
        pristine = _decode(raw)
        pay = "resale-market/market-pay"
        id_error = "market receipt IDs differ"
        receipt_error = "canonical market receipt bytes differ"
        cases = (
            ("missing ID", id_error, lambda receipts: receipts.pop(pay)),
            ("extra ID", id_error, lambda receipts: receipts.update({"resale-market/extra": receipts[pay]})),
            ("extra field", receipt_error, lambda receipts: receipts[pay]["right"].update(extra=None)),
            ("altered holder", receipt_error, lambda receipts: receipts[pay]["right"].update(holder_role="buyer-2")),
            ("altered type", receipt_error, lambda receipts: receipts[pay]["listing"].update(ownership_transferred=0)),
        )
        for label, message, mutate in cases:
            document = copy.deepcopy(pristine)
            mutate(document["receipts"])
            with self.subTest(mutation=label), self.assertRaisesRegex(AssertionError, message):
                self.compare_market_receipts(_canonical(document).encode("utf-8"))

    def first_acceptances(self):
        listed_ids = {
            vid
            for row in self.table["tuples"]
            for context in row["contexts"]
            for ids in context["steps"].values()
            for vid in ids
        }
        return {
            vid: self.by_id[vid] for vid in sorted(listed_ids)
            if self.by_id[vid]["expected"]["kind"] == "accept"
        }

    def compare_booking_branch_receipts(self, raw):
        document = _decode(raw)
        fixture = self.check_companion_fixture_pin(document)
        targets = {
            vid: vector for vid, vector in self.first_acceptances().items()
            if vector["context"] in BOOKING_BRANCH_STEPS
            and "commerce_step" in vector and "receipt_ref" not in vector["expected"]
        }
        self.assertEqual(Counter(vector["context"] for vector in targets.values()), {
            "booking-resale": 3, "booking-admission": 4, "booking-refund": 3,
        })
        self.assertEqual(set(targets), {
            f"{context}/{step}" for context, steps in BOOKING_BRANCH_STEPS.items() for step in steps
        })
        expected = document["receipts"]
        self.assertEqual(expected.keys(), targets.keys(), "booking receipt IDs differ")

        receipts = {}
        for vid, vector in targets.items():
            try:
                receipt = self.replay_target(vector)[vid]
                self.assertEqual(
                    _canonical(receipt), _canonical(expected[vid]),
                    f"canonical booking receipt bytes differ for {vid}",
                )
            except (AssertionError, KeyError) as error:
                error.add_note(f"vector={vid} setup={vector['setup']}")
                raise
            receipts[vid] = receipt
        observed = {
            "record_schema_version": BOOKING_BRANCH_SCHEMA,
            "record_kind": "IN_PROCESS_MOCK_RECEIPT_VECTORS",
            "normative": False,
            "fixture": fixture,
            "receipts": receipts,
        }
        self.assertEqual(_canonical(observed).encode("utf-8"), raw, "canonical booking companion bytes differ")

    def test_booking_branch_full_receipts(self):
        self.compare_booking_branch_receipts(read(BOOKING_BRANCH_RECEIPTS))

    def test_booking_branch_receipt_mutations(self):
        raw = read(BOOKING_BRANCH_RECEIPTS)
        self.compare_booking_branch_receipts(raw)
        pristine = _decode(raw)
        vid = "booking-admission/order-B"
        receipt = pristine["receipts"][vid]
        self.assertIsNone(receipt["reservation"]["admission_id"])
        self.assertIs(receipt["show"]["open"], True)
        combined_step = self.golden_steps[6]
        self.assertEqual(combined_step["id"], self.by_id[vid]["commerce_step"])

        cases = (
            ("missing field", lambda receipts: receipts[vid]["reservation"].pop("admission_id")),
            ("changed type", lambda receipts: receipts[vid]["show"].update(open=1)),
            ("different history", lambda receipts: receipts.update({vid: combined_step["receipt"]})),
        )
        for label, mutate in cases:
            document = copy.deepcopy(pristine)
            mutate(document["receipts"])
            with self.subTest(mutation=label), self.assertRaisesRegex(
                AssertionError, f"canonical booking receipt bytes differ for {vid}",
            ):
                self.compare_booking_branch_receipts(_canonical(document).encode("utf-8"))

    def test_all_first_acceptances_resolve(self):
        targets = self.first_acceptances()
        direct_ids = {vid for vid, vector in targets.items() if "receipt_ref" in vector["expected"]}
        market = _decode(read(MARKET_RECEIPTS))["receipts"]
        booking = _decode(read(BOOKING_BRANCH_RECEIPTS))["receipts"]
        self.assertEqual(len(targets), 56)
        self.assertEqual((len(direct_ids), len(market), len(booking)), (32, 14, 10))
        self.assertEqual(
            Counter(direct_ids) + Counter(market.keys()) + Counter(booking.keys()),
            Counter(targets.keys()),
            "each first acceptance must have exactly one receipt source",
        )
        companions = market | booking
        for vid, vector in targets.items():
            with self.subTest(vector=vid, setup=vector["setup"]):
                expected = self.resolve_receipt_ref(vector) if vid in direct_ids else companions[vid]
                self.assertEqual(_canonical(self.replay_target(vector)[vid]), _canonical(expected))

    def resolve_receipt_ref(self, vector):
        index = vector["input_index"]
        self.assertEqual(vector["expected"]["receipt_ref"], f"{RECEIPTS}#/steps/{index}/receipt")
        golden = self.golden_steps[index]
        self.assertEqual(golden["action"], vector["envelope"]["action"])
        return golden["receipt"]

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
            self.assertEqual(_canonical(receipt), _canonical(self.resolve_receipt_ref(vector)))
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
