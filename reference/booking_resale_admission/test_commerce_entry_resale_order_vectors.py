"""Source-informed, portable §11.4 mock evidence; no golden update mode.

Helper modules are imported without importing TestCase classes. Diagnostic
snapshots are detached Python observations, never published read responses.
"""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
import test_commerce_temporal_vectors as temporal
from integration_gate.catalogue import load_catalogue
from scripts.bootstrap_2_fixtures import read_bootstrap_2_input
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_entry_resale_order_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_entry_resale_order_receipts_v1.json"
SOURCE_PATHS = goldens.SOURCE_PATHS | frozenset({
    "reference/booking_resale_admission/test_commerce_journey_receipts.py",
    "reference/booking_resale_admission/test_commerce_temporal_vectors.py",
    "reference/booking_resale_admission/test_commerce_historical_receipt_vectors.py",
    "reference/booking_resale_admission/test_admission_fsm.py",
    goldens.FIXTURE, str(goldens.GOLDEN.relative_to(ROOT)),
    "reference/booking_resale_admission/fixtures/commerce_temporal_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_temporal_receipts_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_historical_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_historical_receipts_v1.json",
    "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md",
    "docs/contracts/READ_MODEL_QUERIES.md",
})
# Independent literal identities/order and refusal maps; never inferred from JSON.
SETUP = ("reservation-clock", "show", "hold", "confirm", "payment", "issue",
         "resale-clock", "resale-adopt")
ORDERS = {
    "listing-cancel-before-entry": SETUP + (
        "list", "admission-clock", "admission-adopt", "authorize-listed",
        "cancel-list", "authorize-after-cancel", "list-after-authorize"),
    "entry-consumption-before-resale": SETUP + (
        "admission-clock", "admission-adopt", "authorize", "list-authorized",
        "consume", "list-consumed"),
}
REFUSALS = {
    "listing-cancel-before-entry": {
        "authorize-listed": "LISTING_LOCKED", "list-after-authorize": "ADMISSION_LOCKED"},
    "entry-consumption-before-resale": {
        "list-authorized": "ADMISSION_LOCKED", "list-consumed": "ALREADY_CONSUMED"},
}
_assert_paths = temporal._assert_paths


def _read(path):
    return read_bootstrap_2_input(path)


def _views(host, accepted):
    views = {}
    if "reservation_hold" in accepted:
        views["reservation"] = host.machines["reservation"].view("reserve-1")
        views["show"] = host.machines["reservation"].view_show("show-1")
    if "resale_adopt_issued" in accepted:
        views["resale_right"] = host.machines["resale"].view_right("issue-1")
    if "resale_list_resale" in accepted:
        views["listing"] = host.machines["resale"].view("list-1")
    if "admission_adopt_issued" in accepted:
        admission = host.machines["admission"]
        views["credential"] = admission.view("issue-1")
        views["presentation"] = admission.view_credential(
            "issue-1", version=1, holder_role="buyer-1")
    return views


def _snapshot(host, accepted):
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
        keys = set()
        for step in case["steps"]:
            journey._check(("expect" in step) != ("expect_error" in step), "one expectation")
            action, body = step["action"], step["body"]
            journey._check(action in catalogue.fsm_names, "unpublished action")
            spec = catalogue.fsm["commands"][action]
            journey._check(not problems(body, spec["schema"]), "command schema: " + step["id"])
            journey._check(spec["subject_field"] in body and "domain" not in body,
                           "subject/domain")
            key = body["idempotency_key"]
            journey._check(key not in keys, "fresh key required")
            keys.add(key)
            if "expect" in step:
                expect = step["expect"]
                journey._check(expect["duplicate"] is False and expect["applied"] == spec["op"],
                               "accepted expectation")
                journey._check({j["machine"] for j in expect["journal"]} ==
                               {"settlement", "reservation", "resale", "admission", "credit"},
                               "journal expectation coverage")
            if action == "resale_cancel_listing":
                journey._check(set(body) == {"listing_id", "idempotency_key", "seller_role"},
                               "published cancel body")


def _drive(case):
    host = FsmHost()
    accepted, receipts, refusals, snapshots = set(), {}, {}, {}
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
            for journal in expect["journal"]:
                name = journal["machine"]
                journey._check(len(host.machines[name].export_journal()) -
                               len(before["machines"][name]["journal"]) == journal["delta"],
                               "journal delta: " + step["id"] + "/" + name)
            receipts[step["id"]] = copy.deepcopy(receipt)
            accepted.add(step["action"])
        snapshot = _snapshot(host, accepted)
        for node in journey._walk([receipts.get(step["id"], {}), snapshot["views"]]):
            for flag in flags & node.keys():
                journey._check(node[flag] is False, "authority flag: " + flag)
        snapshots[step["id"]] = snapshot
        _assert_views(host, accepted, step.get("observe", {}))
    _assert_views(host, accepted, case["final_expect"]["views"])
    for fact in case["final_expect"]["separate_facts"]:
        _assert_paths(receipts[fact["step"]], {fact["path"]: fact["value"]})
    journey._check(refusals == REFUSALS[case["id"]], "refusals")
    return host, receipts, refusals, snapshots


def _observe(fixture_raw, fixture_pin, sources):
    fixture = goldens._decode(fixture_raw)
    journey._check(_canonical(fixture).encode("utf-8") == fixture_raw, "canonical input bytes differ")
    _validate(fixture)
    cases = []
    for i, case in enumerate(fixture["cases"]):
        _host, receipts, refusals, snapshots = _drive(case)
        ids = {step["id"] for step in case["steps"]}
        journey._check(not receipts.keys() & refusals.keys() and
                       receipts.keys() | refusals.keys() == ids, "outcome coverage")
        steps = []
        for j, step in enumerate(case["steps"]):
            outcome = dict(id=step["id"], action=step["action"],
                           input_ref=FIXTURE + "#/cases/%d/steps/%d/body" % (i, j),
                           diagnostic_snapshot=snapshots[step["id"]])
            key = "receipt" if step["id"] in receipts else "rejection_code"
            outcome[key] = (receipts if key == "receipt" else refusals)[step["id"]]
            steps.append(outcome)
        cases.append(dict(id=case["id"], steps=steps))
    return dict(record_schema_version="kix-commerce-entry-resale-order-receipts/1",
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
    journey._check(_canonical(observed).encode("utf-8") == raw,
                   "complete canonical receipt bytes differ")
    return observed


class CommerceEntryResaleOrderVectorTests(unittest.TestCase):
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
                resolved = self.fixture
                for segment in outcome["input_ref"].split("#/")[1].split("/"):
                    resolved = resolved[int(segment)] if isinstance(resolved, list) else resolved[segment]
                self.assertEqual(_canonical(resolved), _canonical(step["body"]))
                key = "rejection_code" if "expect_error" in step else "receipt"
                self.assertEqual(set(outcome), {"id", "action", "input_ref", key, "diagnostic_snapshot"})
                self.assertEqual(set(outcome["diagnostic_snapshot"]["machines"]),
                                 {"reservation", "resale", "admission", "settlement", "credit"})

    def test_published_schemas_sources_and_unbound_reads(self):
        _validate(self.fixture)
        catalogue, host = load_catalogue(ROOT), FsmHost()
        self.assertEqual(len(journey.READ_MODEL_QUERY_NAMES), 13)
        for name in journey.READ_MODEL_QUERY_NAMES:
            self.assertNotIn(name, catalogue.core_names + catalogue.fsm_names)
            self.assertNotIn(name, host._commands)
        for case in self.fixture["cases"]:
            path, method = case["source_test"].split("::")
            self.assertIn(path, SOURCE_PATHS)
            self.assertIn("def " + method.split(".")[1] + "(", _read(path).decode())
            self.assertIn("docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#11.4",
                          case["contract_predicates"])
            self.assertEqual(case["clocks"]["meaning"], "SYNTHETIC_FIXTURE_INPUTS_ONLY")

    def test_listing_cancel_requires_explicit_authorization(self):
        _host, receipts, refusals, snapshots = _drive(self.fixture["cases"][0])
        self.assertEqual(refusals, REFUSALS["listing-cancel-before-entry"])
        _assert_paths(snapshots["authorize-listed"]["views"], {
            "reservation.phase": "ISSUED", "credential.phase": "ELIGIBLE",
            "presentation.presentation.decision": "LISTING_LOCKED"})
        _assert_paths(snapshots["cancel-list"]["views"], {
            "reservation.phase": "ISSUED", "credential.phase": "ELIGIBLE",
            "credential.admission_id": None, "credential.consume_id": None,
            "listing.phase": "CANCELLED", "resale_right.right.version": 1})
        _assert_paths(receipts["authorize-after-cancel"], {
            "credential.phase": "AUTHORIZED", "credential.admission_id": "admit-after",
            "credential.consume_id": None})
        # Earlier receipt and snapshot retain the live listing after cancellation.
        self.assertEqual(receipts["list"]["listing"]["phase"], "LISTED")
        self.assertEqual(snapshots["list"]["views"]["listing"]["phase"], "LISTED")

    def test_consumption_and_ownership_versions_stay_distinct(self):
        _host, receipts, refusals, snapshots = _drive(self.fixture["cases"][1])
        self.assertEqual(refusals, REFUSALS["entry-consumption-before-resale"])
        _assert_paths(receipts["consume"], {
            "evidence.decision": "CONSUMED_ONCE", "evidence.version_after": 2,
            "credential.consume_id": "consume-1", "credential.admission_id": None})
        for case in self.fixture["cases"]:
            _host, r, _errors, ss = _drive(case)
            _assert_paths(r["payment"], {"reservation.phase": "PAYMENT_NOTED",
                                        "reservation.issuance_id": None, "reservation.right": None})
            _assert_paths(r["issue"], {"reservation.phase": "ISSUED", "evidence.version": 1})
            for snap in ss.values():
                if "resale_right" in snap["views"]:
                    _assert_paths(snap["views"]["resale_right"], {
                        "right.holder_role": "buyer-1", "right.version": 1})
        _assert_paths(snapshots["list-consumed"]["views"], {
            "reservation.phase": "CONSUMED", "reservation.right.version": 2,
            "credential.version_after": 2, "resale_right.right.version": 1})
        self.assertEqual(receipts["authorize"]["credential"]["phase"], "AUTHORIZED")

    def test_all_refusals_preserve_detached_snapshots(self):
        for case in self.fixture["cases"]:
            _host, _receipts, refusals, snapshots = _drive(case)
            for index, step in enumerate(case["steps"]):
                if step["id"] in refusals:
                    previous = snapshots[case["steps"][index - 1]["id"]]
                    self.assertIsNot(previous, snapshots[step["id"]])
                    self.assertEqual(_canonical(previous), _canonical(snapshots[step["id"]]))

    def test_detached_output_mutations_fail_without_pin_changes(self):
        # The outer fixture/source pins remain valid; full semantic bytes fail.
        mutations = (
            lambda s: s[5]["receipt"]["reservation"].update(issuance_id="changed"),
            lambda s: s[5]["receipt"]["reservation"].update(extra=None),
            lambda s: s[5]["receipt"]["reservation"].pop("issuance_id"),
            lambda s: s[5]["receipt"]["evidence"].update(chain_issued=0),
            lambda s: s[11].update(rejection_code="CHANGED"),
            lambda s: s[12]["receipt"]["credential"].update(consume_id="invented"),
            lambda s: s[-1]["diagnostic_snapshot"]["views"]["resale_right"]["right"].update(version=2),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["reservation"].update(state="changed"),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["resale"].update(digest="0" * 64),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["admission"]["journal"].pop(),
            lambda s: s[-1]["diagnostic_snapshot"]["views"]["credential"].update(admission_id="invented"),
        )
        for mutate in mutations:
            document = copy.deepcopy(self.document)
            mutate(document["cases"][1]["steps"])
            with self.subTest(mutate=mutate), self.assertRaisesRegex(
                    AssertionError, "canonical receipt bytes differ"):
                compare_receipts(_canonical(document).encode())

    def test_detached_input_order_errors_and_schema_fail_before_execution(self):
        mutations = (
            ("step order", lambda f: f["cases"][0]["steps"].reverse()),
            ("step order", lambda f: f["cases"][0]["steps"].pop()),
            ("step order", lambda f: f["cases"][0]["steps"].append(f["cases"][0]["steps"][0])),
            ("case order", lambda f: f["cases"].reverse()),
            ("refusal mapping", lambda f: f["cases"][0]["steps"][11].update(expect_error="CHANGED")),
            ("fresh key", lambda f: f["cases"][0]["steps"][13]["body"].update(idempotency_key="authorize-listed")),
            ("command schema", lambda f: f["cases"][0]["steps"][1]["body"].update(capacity=True)),
        )
        for reason, mutate in mutations:
            fixture = copy.deepcopy(self.fixture)
            mutate(fixture)
            raw = _canonical(fixture).encode()
            # Recompute input pin to ensure semantic guards, not the hash, reject it.
            document = copy.deepcopy(self.document)
            document["fixture"] = goldens._pin(FIXTURE, raw)
            def read(path):
                return raw if path == FIXTURE else _read(path)
            with self.subTest(reason=reason), patch(__name__ + ".FsmHost") as host:
                with self.assertRaisesRegex(AssertionError, reason):
                    compare_receipts(_canonical(document).encode(), read=read)
                host.assert_not_called()

    def test_output_order_identity_and_reference_mutations_fail(self):
        mutations = (
            lambda s: s.pop(), lambda s: s.append(copy.deepcopy(s[0])), lambda s: s.reverse(),
            lambda s: s[0].update(input_ref=FIXTURE + "#/cases/1/steps/0/body"),
            lambda s: s[0].update(action="changed"), lambda s: s[0].update(id="changed"),
        )
        for mutate in mutations:
            document = copy.deepcopy(self.document)
            mutate(document["cases"][0]["steps"])
            with self.subTest(mutate=mutate), self.assertRaisesRegex(
                    AssertionError, "canonical receipt bytes differ"):
                compare_receipts(_canonical(document).encode())

    def test_non_mutation_guard_detects_extra_effect_at_every_refusal(self):
        real_call = FsmHost.call
        for case in self.fixture["cases"]:
            for target in (s for s in case["steps"] if "expect_error" in s):
                def corrupting_call(host, action, body):
                    try:
                        return real_call(host, action, body)
                    finally:
                        if action == target["action"] and body == target["body"]:
                            real_call(host, "resale_set_clock", {
                                "subject_id": "clock", "idempotency_key": "extra-effect",
                                "now_ms": 1000001})
                with self.subTest(target=target["id"]), patch.object(FsmHost, "call", corrupting_call):
                    with self.assertRaisesRegex(AssertionError, "mutated state/digest/journal/views"):
                        _drive(case)

    def test_source_and_fixture_pins_fail_before_execution(self):
        mutations = (
            lambda d: d["sources"].pop(), lambda d: d["sources"].append(d["sources"][0]),
            lambda d: d["sources"].reverse(), lambda d: d["sources"][0].update(sha256="0" * 64),
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
        for raw in (_read(FIXTURE) + b"\n", json.dumps(self.fixture, indent=2).encode()):
            with patch(__name__ + ".FsmHost") as host:
                with self.assertRaisesRegex(AssertionError, "canonical input bytes differ"):
                    _observe(raw, {}, [])
                host.assert_not_called()


if __name__ == "__main__":
    unittest.main()
