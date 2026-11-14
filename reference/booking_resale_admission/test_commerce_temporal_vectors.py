"""Source-informed portable temporal evidence; in-process, no golden writer.

Import helper modules rather than TestCase classes to keep discovery unique.
All commands use the published FSM bodies; views are test observations only.
"""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_temporal_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_temporal_receipts_v1.json"
SOURCE_PATHS = goldens.SOURCE_PATHS | frozenset({
    "reference/booking_resale_admission/test_commerce_journey_receipts.py",
    goldens.FIXTURE,
    str(goldens.GOLDEN.relative_to(ROOT)),
    "reference/booking_resale_admission/test_reservation_fsm.py",
    "reference/booking_resale_admission/test_admission_fsm.py",
    "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md",
    "docs/contracts/READ_MODEL_QUERIES.md",
})
# Fixed case/step identities and order, independent of the JSON being checked.
SETUP = ("reservation-clock", "show", "hold", "confirm", "payment")
ORDERS = {
    "paid-reservation-expiry": SETUP + (
        "cancel-paid", "reservation-expire", "issue-late", "cancel-late"),
    "transfer-stale-presentations": SETUP + (
        "issue", "resale-clock", "resale-adopt", "list", "resale-payment",
        "transfer", "admission-clock", "admission-adopt", "authorize-old",
        "authorize-transferred"),
    "expired-authorization-replacement": SETUP + (
        "issue", "admission-clock", "admission-adopt", "authorize",
        "admission-expire", "consume-late", "replace", "consume",
        "replay-consume", "consume-again"),
}
REFUSALS = {
    "paid-reservation-expiry": {
        "cancel-paid": "COMPENSATION_UNDEFINED", "issue-late": "RESERVATION_EXPIRED",
        "cancel-late": "COMPENSATION_UNDEFINED"},
    "transfer-stale-presentations": {
        "authorize-old": "STALE_VERSION", "authorize-transferred": "STALE_VERSION"},
    "expired-authorization-replacement": {
        "consume-late": "ADMISSION_EXPIRED", "consume-again": "ALREADY_CONSUMED"},
}


def _read(path):
    return (ROOT / path).read_bytes()


def _assert_paths(value, paths):
    for path, expected in paths.items():
        actual = journey._resolve(value, path)
        journey._check(journey._same(actual, expected) and
                       _canonical(actual) == _canonical(expected),
                       "%s: %r != %r" % (path, actual, expected))


def _views(host, accepted):
    views = {}
    if "reservation_hold" in accepted:
        views["reservation"] = host.machines["reservation"].view("reserve-1")
        views["show"] = host.machines["reservation"].view_show("show-1")
    if "resale_adopt_issued" in accepted:
        views["resale_right"] = host.machines["resale"].view_right("issue-1")
    if "admission_adopt_issued" in accepted:
        admission = host.machines["admission"]
        views["credential"] = admission.view("issue-1")
        for name, version, holder in (("old_presentation", 1, "buyer-1"),
                                      ("new_presentation", 2, "buyer-2")):
            views[name] = admission.view_credential(
                "issue-1", version=version, holder_role=holder)
    return views


def _snapshot(host, accepted):
    # Detach every value: a later in-place mutation cannot rewrite the baseline.
    return copy.deepcopy({
        "machines": {name: {
            "state": machine.canonical_state(), "digest": machine.state_digest(),
            "journal": machine.export_journal(),
        } for name, machine in host.machines.items()},
        "views": _views(host, accepted),
    })


def _assert_views(host, accepted, expected):
    views = _views(host, accepted)
    for name, paths in expected.items():
        _assert_paths(views[name], paths)


def _validate(fixture):
    journey._check(type(fixture["fixture_version"]) is int and fixture["fixture_version"] == 1,
                   "fixture version")
    journey._check(fixture["provenance"] == "OFFLINE_CONFORMANCE_FIXTURE_ONLY", "provenance")
    catalogue = load_catalogue(ROOT)
    journey._check(fixture["domain"] == catalogue.fsm_domain, "fixture domain")
    journey._check(tuple(c["id"] for c in fixture["cases"]) == tuple(ORDERS), "case order")
    for case in fixture["cases"]:
        ids = tuple(s["id"] for s in case["steps"])
        journey._check(ids == ORDERS[case["id"]] and len(set(ids)) == len(ids), "step order")
        errors = {s["id"]: s["expect_error"] for s in case["steps"] if "expect_error" in s}
        journey._check(errors == REFUSALS[case["id"]], "refusal mapping")
        seen = {}
        for step in case["steps"]:
            journey._check(("expect" in step) != ("expect_error" in step), "one expectation")
            action, body = step["action"], step["body"]
            journey._check(action in catalogue.fsm_names, "unpublished action")
            spec = catalogue.fsm["commands"][action]
            journey._check(not problems(body, spec["schema"]), "command schema: " + step["id"])
            journey._check(spec["subject_field"] in body and "idempotency_key" in body and
                           "domain" not in body, "subject/key/domain")
            if "replay_of" in step:
                first = seen[step["replay_of"]]
                journey._check(action == first["action"] and body == first["body"], "replay binding")
                journey._check(step["expect"]["duplicate"] is True and
                               step["expect"]["applied"] is None, "replay expectation")
            elif "expect" in step:
                journey._check(step["expect"]["duplicate"] is False and
                               step["expect"]["applied"] == spec["op"], "accepted expectation")
            seen[step["id"]] = step


def _drive(case):
    host = FsmHost()
    accepted, receipts, refusals = set(), {}, {}
    flags = set(NON_CLAIMS) | set(journey.SETTLEMENT_FINALITY_FLAGS) | {
        "economic_finality_claimed", "chain_issued", "venue_credential_reissued", "offline_admission"}
    for step in case["steps"]:
        before = _snapshot(host, accepted)
        try:
            receipt = host.call(step["action"], copy.deepcopy(step["body"]))
        except FsmRejected as exc:
            journey._check(exc.code == step.get("expect_error"), "unexpected refusal: " + exc.code)
            journey._check(_canonical(before) == _canonical(_snapshot(host, accepted)),
                           "refusal mutated state/digest/journal/views")
            refusals[step["id"]] = exc.code
        else:
            journey._check("expect" in step, "expected refusal was accepted")
            expect = step["expect"]
            _assert_paths(receipt, {"duplicate": expect["duplicate"], "applied": expect["applied"],
                                    **expect["paths"]})
            for node in journey._walk(receipt):
                for flag in flags & node.keys():
                    journey._check(node[flag] is False, "authority flag: " + flag)
            for journal in expect.get("journal", []):
                name = journal["machine"]
                journey._check(len(host.machines[name].export_journal()) -
                               len(before["machines"][name]["journal"]) == journal["delta"],
                               "journal delta")
            if "replay_of" in step:
                first = receipts[step["replay_of"]]
                journey._check(journey._without_replay_keys(receipt) ==
                               journey._without_replay_keys(first), "immutable replay result")
                journey._check(_canonical(before) == _canonical(_snapshot(host, accepted)),
                               "replay mutated state/digest/journal/views")
            receipts[step["id"]] = receipt
            accepted.add(step["action"])
        _assert_views(host, accepted, step.get("observe", {}))
    _assert_views(host, accepted, case["final_expect"]["views"])
    for fact in case["final_expect"]["separate_facts"]:
        _assert_paths(receipts[fact["step"]], {fact["path"]: fact["value"]})
    journey._check(refusals == REFUSALS[case["id"]], "refusals")
    return host, receipts, refusals


def _observe(fixture_raw, fixture_pin, sources):
    fixture = goldens._decode(fixture_raw)
    _validate(fixture)
    cases = []
    for i, case in enumerate(fixture["cases"]):
        _host, receipts, refusals = _drive(case)
        ids = {step["id"] for step in case["steps"]}
        journey._check(not receipts.keys() & refusals.keys() and
                       receipts.keys() | refusals.keys() == ids, "outcome coverage")
        steps = []
        for j, step in enumerate(case["steps"]):
            outcome = dict(id=step["id"], action=step["action"],
                           input_ref=FIXTURE + "#/cases/%d/steps/%d/body" % (i, j))
            key = "receipt" if step["id"] in receipts else "rejection_code"
            outcome[key] = (receipts if key == "receipt" else refusals)[step["id"]]
            steps.append(outcome)
        cases.append(dict(id=case["id"], steps=steps))
    return dict(record_schema_version="kix-commerce-temporal-receipts/1",
                record_kind="IN_PROCESS_MOCK_RECEIPT_VECTORS", normative=False,
                fixture=fixture_pin, sources=sources, cases=cases)


def compare_receipts(raw, read=_read):
    expected = goldens._decode(raw)
    fixture_raw = read(FIXTURE)
    fixture_pin = goldens._pin(FIXTURE, fixture_raw)
    sources = [goldens._pin(path, read(path)) for path in sorted(SOURCE_PATHS)]
    journey._check(expected["fixture"] == fixture_pin, "fixture pin drift")
    journey._check(expected["sources"] == sources, "source pin drift/set/order")
    observed = _observe(fixture_raw, fixture_pin, sources)
    journey._check(_canonical(observed).encode("utf-8") == raw, "complete canonical receipt bytes differ")
    return observed


class CommerceTemporalVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = GOLDEN.read_bytes()
        cls.document = goldens._decode(cls.raw)
        cls.fixture = goldens._decode(_read(FIXTURE))

    def test_complete_output_bytes_and_references(self):
        observed = compare_receipts(self.raw)
        for i, (case, vector) in enumerate(zip(self.fixture["cases"], observed["cases"])):
            self.assertEqual(case["id"], vector["id"])
            for j, (step, outcome) in enumerate(zip(case["steps"], vector["steps"])):
                self.assertEqual(outcome["input_ref"], FIXTURE + "#/cases/%d/steps/%d/body" % (i, j))
                resolved = goldens._decode(_read(FIXTURE))
                for segment in outcome["input_ref"].split("#/")[1].split("/"):
                    resolved = resolved[int(segment)] if isinstance(resolved, list) else resolved[segment]
                self.assertEqual(resolved, step["body"])
                key = "rejection_code" if "expect_error" in step else "receipt"
                self.assertEqual(set(outcome), {"id", "action", "input_ref", key})

    def test_published_schemas_and_unbound_reads(self):
        _validate(self.fixture)
        catalogue, host = load_catalogue(ROOT), FsmHost()
        for name in journey.READ_MODEL_QUERY_NAMES:
            self.assertNotIn(name, catalogue.names)
            self.assertNotIn(name, host._commands)
        self.assertEqual(len(journey.READ_MODEL_QUERY_NAMES), 13)
        for case in self.fixture["cases"]:
            path, method = case["source_test"].split("::")
            self.assertIn(path, SOURCE_PATHS)
            self.assertIn("def " + method.split(".")[1] + "(", _read(path).decode())
            self.assertTrue(case["contract_predicates"])
            self.assertEqual(case["clocks"]["meaning"], "SYNTHETIC_FIXTURE_INPUTS_ONLY")

    def test_paid_reservation_expiry(self):
        _host, receipts, refusals = _drive(self.fixture["cases"][0])
        self.assertEqual(refusals, REFUSALS["paid-reservation-expiry"])
        self.assertNotIn("issue-late", receipts)
        self.assertIsNone(receipts["payment"]["reservation"]["issuance_id"])

    def test_transfer_stale_presentations(self):
        _host, receipts, refusals = _drive(self.fixture["cases"][1])
        self.assertEqual(refusals, REFUSALS["transfer-stale-presentations"])
        self.assertEqual(receipts["transfer"]["evidence"]["transfer_id"], "transfer-1")

    def test_expired_authorization_replacement(self):
        host, receipts, _refusals = _drive(self.fixture["cases"][2])
        self.assertEqual(receipts["authorize"]["admission"]["expires_ms"], 1120000)
        self.assertEqual(receipts["replace"]["admission"]["expires_ms"], 1240000)
        self.assertIs(receipts["replay-consume"]["duplicate"], True)
        self.assertIsNone(receipts["replay-consume"]["applied"])
        self.assertEqual(host.machines["reservation"].view("reserve-1")["right"]["version"], 2)

    def test_output_mutations_fail_comparison(self):
        original = [_drive(c) for c in self.fixture["cases"]]
        mutations = (
            lambda r, f: r["issue"]["reservation"].update(issuance_id="changed"),
            lambda r, f: r["issue"]["reservation"].update(extra=None),
            lambda r, f: r["issue"]["reservation"].pop("issuance_id"),
            lambda r, f: r["issue"]["evidence"].update(chain_issued=0),
            lambda r, f: r["replay-consume"].update(applied="consume"),
            lambda r, f: f.update({"consume-again": "CHANGED"}),
        )
        for mutate in mutations:
            host, receipts, refusals = original[2]
            receipts, refusals = copy.deepcopy(receipts), copy.deepcopy(refusals)
            mutate(receipts, refusals)
            with self.subTest(mutate=mutate), patch(__name__ + "._drive", side_effect=[
                    original[0], original[1], (host, receipts, refusals)]):
                with self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                    compare_receipts(self.raw)

    def test_order_and_mapping_mutations_fail(self):
        mutations = (
            lambda s: s.pop(), lambda s: s.append(copy.deepcopy(s[0])),
            lambda s: s.reverse(), lambda s: s[0].update(input_ref=FIXTURE + "#/cases/1/steps/0/body"),
            lambda s: s[0].update(action="changed"), lambda s: s[0].update(id="changed"),
        )
        for mutate in mutations:
            document = copy.deepcopy(self.document)
            mutate(document["cases"][0]["steps"])
            with self.subTest(mutate=mutate), self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                compare_receipts(_canonical(document).encode())
        for mutate in (lambda s: s.pop(), lambda s: s.append(s[0]), lambda s: s.reverse()):
            fixture = copy.deepcopy(self.fixture)
            mutate(fixture["cases"][0]["steps"])
            with self.subTest(input=mutate), patch(__name__ + ".FsmHost") as host:
                with self.assertRaisesRegex(AssertionError, "step order"):
                    _observe(_canonical(fixture).encode(), {}, [])
                host.assert_not_called()
        for mutate in (lambda c: c.pop(), lambda c: c.append(c[0]), lambda c: c.reverse()):
            document = copy.deepcopy(self.document)
            mutate(document["cases"])
            with self.subTest(case=mutate), self.assertRaises(AssertionError):
                compare_receipts(_canonical(document).encode())

    def test_pins_fail_before_execution(self):
        mutations = (
            lambda d: d["sources"].pop(), lambda d: d["sources"].append(d["sources"][0]),
            lambda d: d["sources"].reverse(),
            lambda d: d["sources"][0].update(sha256="0" * 64),
            lambda d: d["sources"][0].update(gitBlob="0" * 40),
            lambda d: d["fixture"].update(sha256="0" * 64),
        )
        for mutate in mutations:
            document = copy.deepcopy(self.document)
            mutate(document)
            with self.subTest(mutate=mutate), patch(__name__ + "._drive") as drive:
                with self.assertRaisesRegex(AssertionError, "pin drift"):
                    compare_receipts(_canonical(document).encode())
                drive.assert_not_called()
        for path in (FIXTURE, *sorted(SOURCE_PATHS)):
            def drifted_read(candidate):
                return _read(candidate) + (b"\n" if candidate == path else b"")
            with self.subTest(path=path), patch(__name__ + "._drive") as drive:
                with self.assertRaisesRegex(AssertionError, "pin drift"):
                    compare_receipts(self.raw, read=drifted_read)
                drive.assert_not_called()

    def test_strict_serialization(self):
        for raw in (b'{', b'\xff', b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',
                    b'{"x":-Infinity}', b'{"x":1e999}', self.raw + b'{}'):
            with self.subTest(raw=raw[:40]), self.assertRaises((ValueError, UnicodeError)):
                compare_receipts(raw)
        for raw in (self.raw + b"\n", json.dumps(self.document, indent=2).encode()):
            with self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                compare_receipts(raw)


if __name__ == "__main__":
    unittest.main()
