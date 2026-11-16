"""Portable source-informed settlement-bound issuance evidence; no golden writer.

Commands use the unchanged in-process host. Diagnostic views are test-only.
Rejected-key retention is process-local, outside business snapshots/journals.
"""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
import test_commerce_temporal_vectors as temporal
import test_commerce_historical_receipt_vectors as historical
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_bound_issuance_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_bound_issuance_receipts_v1.json"
PRIOR_INPUTS = (
    goldens.FIXTURE,
    "reference/booking_resale_admission/fixtures/commerce_temporal_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_historical_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_entry_resale_order_inputs_v1.json",
)
SOURCE_PATHS = historical.SOURCE_PATHS | frozenset(PRIOR_INPUTS) | frozenset({
    "reference/booking_resale_admission/test_commerce_historical_receipt_vectors.py",
    "reference/booking_resale_admission/fixtures/commerce_historical_receipts_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_entry_resale_order_receipts_v1.json",
})
# Literal independent identities/order and errors; never derived from fixture data.
SETUP = ("reservation-clock", "show", "hold", "confirm", "payment")
ORDERS = {
    "bound-issuance-after-commit": SETUP + (
        "initiate", "settlement-authorize", "bind", "issue-early", "capture",
        "issue-captured", "commit", "replay-issue-early", "issue-committed"),
    "committed-settlement-amount-mismatch": SETUP + (
        "initiate", "settlement-authorize", "capture", "commit", "bind", "issue-mismatch"),
}
REFUSALS = {
    "bound-issuance-after-commit": {
        "issue-early": "SETTLEMENT_NOT_COMMITTED",
        "issue-captured": "SETTLEMENT_NOT_COMMITTED",
        "replay-issue-early": "SETTLEMENT_NOT_COMMITTED"},
    "committed-settlement-amount-mismatch": {
        "issue-mismatch": "SETTLEMENT_AMOUNT_MISMATCH"},
}
MACHINES = {"reservation", "settlement", "resale", "admission", "credit"}
_assert_paths = temporal._assert_paths
_views = historical._views
_snapshot = historical._snapshot
_assert_views = historical._assert_views


def _read(path):
    return (ROOT / path).read_bytes()


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
        keys = set()
        for step in case["steps"]:
            journey._check(("expect" in step) != ("expect_error" in step), "one expectation")
            action, body = step["action"], step["body"]
            journey._check(action in catalogue.fsm_names, "unpublished action")
            spec = catalogue.fsm["commands"][action]
            journey._check(not problems(body, spec["schema"]), "command schema: " + step["id"])
            journey._check(spec["subject_field"] in body and "idempotency_key" in body and
                           "domain" not in body, "subject/key/domain")
            key = body["idempotency_key"]
            journey._check(key not in keys or "refusal_of" in step, "fresh key required")
            keys.add(key)
            if "expect" in step:
                journey._check(len(step["expect"]["journal"]) == 5 and
                               {j["machine"] for j in step["expect"]["journal"]} == MACHINES,
                               "journal expectation coverage")
            if "replay_of" in step:
                first = seen[step["replay_of"]]
                journey._check(action == first["action"] and
                               _canonical(body) == _canonical(first["body"]), "replay binding")
                journey._check(step["expect"]["duplicate"] is True and
                               step["expect"]["applied"] is None, "replay expectation")
            elif "refusal_of" in step or "conflict_of" in step:
                reference = step.get("refusal_of", step.get("conflict_of"))
                first = seen[reference]
                journey._check(action == first["action"] and
                               body["idempotency_key"] == first["body"]["idempotency_key"],
                               "refusal/conflict key binding")
                same = _canonical(body) == _canonical(first["body"])
                journey._check(same is ("refusal_of" in step), "refusal/conflict body binding")
                journey._check(step["expect_error"] == (
                    first["expect_error"] if same else "IDEMPOTENCY_CONFLICT"), "refusal/conflict code")
            elif "expect" in step:
                journey._check(step["expect"]["duplicate"] is False and
                               step["expect"]["applied"] == spec["op"], "accepted expectation")
            seen[step["id"]] = step


    first = {s["id"]: s for s in fixture["cases"][0]["steps"]}
    journey._check(first["replay-issue-early"].get("refusal_of") == "issue-early",
                   "explicit original rejected key")
    original = first["issue-early"]["body"]
    for name in ("issue-captured", "issue-committed"):
        body = first[name]["body"]
        journey._check(body["idempotency_key"] != original["idempotency_key"] and
                       {k: v for k, v in body.items() if k != "idempotency_key"} ==
                       {k: v for k, v in original.items() if k != "idempotency_key"},
                       "explicit fresh issuance key/body")


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
        # Binding/issuance only observe settlement. Unused machines never move.
        for name in ("resale", "admission", "credit"):
            journey._check(_canonical(before["machines"][name]) ==
                           _canonical(snapshot["machines"][name]), "unused machine changed")
        if step["action"] in {"reservation_bind_settlement", "reservation_issue"}:
            journey._check(_canonical(before["machines"]["settlement"]) ==
                           _canonical(snapshot["machines"]["settlement"]),
                           "binding/issuance changed settlement")
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
    return dict(record_schema_version="kix-commerce-bound-issuance-receipts/1",
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


class CommerceBoundIssuanceVectorTests(unittest.TestCase):
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

    def test_existing_coverage_and_portable_gap(self):
        for path in PRIOR_INPUTS:
            fixture = goldens._decode(_read(path))
            for case in fixture.get("cases", [fixture]):
                self.assertFalse(any(s["action"] == "reservation_bind_settlement"
                                     for s in case["steps"]), path)
        _validate(self.fixture)
        catalogue, host = load_catalogue(ROOT), FsmHost()
        self.assertEqual(len(journey.READ_MODEL_QUERY_NAMES), 13)
        for name in journey.READ_MODEL_QUERY_NAMES:
            self.assertNotIn(name, catalogue.names)
            self.assertNotIn(name, host._commands)
        for case in self.fixture["cases"]:
            path, method = case["source_test"].split("::")
            self.assertIn(path, SOURCE_PATHS)
            self.assertIn("def " + method.split(".")[1] + "(", _read(path).decode())
            self.assertIn("docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#9.5",
                          case["contract_predicates"])
            self.assertEqual(case["clocks"], {"meaning": "SYNTHETIC_FIXTURE_INPUTS_ONLY",
                                             "now_ms": 1000000, "expires_ms": 1900000})

    def test_commit_is_separate_from_explicit_fresh_key_issuance(self):
        _host, receipts, refusals, snapshots = _drive(self.fixture["cases"][0])
        self.assertEqual(refusals, REFUSALS["bound-issuance-after-commit"])
        for name, phase in (("issue-early", "AUTHORIZED"), ("issue-captured", "CAPTURED"),
                            ("commit", "COMMITTED"), ("replay-issue-early", "COMMITTED")):
            _assert_paths(snapshots[name]["views"], {
                "settlement.phase": phase, "reservation.phase": "PAYMENT_NOTED",
                "reservation.settlement_gate": "BOUND",
                "reservation.mock_settlement_commit_observed": False,
                "reservation.issuance_id": None, "reservation.right": None,
                "reservation.slot_state": "RESERVED", "reservation.slot_right_id": None})
        _assert_paths(receipts["issue-committed"], {
            "duplicate": False, "applied": "issue", "reservation.phase": "ISSUED",
            "reservation.settlement_gate": "MOCK_COMMIT_OBSERVED",
            "reservation.mock_settlement_commit_observed": True,
            "reservation.issuance_id": "issue-1", "reservation.slot_right_id": "issue-1",
            "reservation.right.state": "ACTIVE", "reservation.right.version": 1,
            "evidence.right_id": "issue-1", "evidence.version": 1,
            "evidence.chain_issued": False})
        self.assertEqual(len(snapshots["issue-committed"]["machines"]["reservation"]["journal"]), 7)

    def test_committed_mismatch_preserves_paid_reservation(self):
        _host, _receipts, refusals, snapshots = _drive(self.fixture["cases"][1])
        self.assertEqual(refusals, {"issue-mismatch": "SETTLEMENT_AMOUNT_MISMATCH"})
        for name in ("commit", "bind", "issue-mismatch"):
            _assert_paths(snapshots[name]["views"], {
                "settlement.phase": "COMMITTED", "settlement.gross": 10000,
                "reservation.amount": 10001, "reservation.payment_ref": "ab" * 32,
                "reservation.phase": "PAYMENT_NOTED", "reservation.slot_state": "RESERVED",
                "reservation.issuance_id": None, "reservation.right": None,
                "reservation.slot_right_id": None,
                "reservation.mock_settlement_commit_observed": False})
        _assert_paths(snapshots["issue-mismatch"]["views"], {
            "reservation.settlement_gate": "BOUND", "reservation.settlement_id": "claim-1"})

    def test_payment_issuance_and_admission_remain_separate(self):
        for case in self.fixture["cases"]:
            _host, receipts, _errors, snapshots = _drive(case)
            _assert_paths(receipts["payment"], {
                "reservation.phase": "PAYMENT_NOTED", "reservation.payment_ref": "ab" * 32,
                "reservation.right": None, "reservation.issuance_id": None,
                "reservation.settlement_id": None, "reservation.settlement_gate": "UNBOUND"})
            for snapshot in snapshots.values():
                views = snapshot["views"]
                if "reservation" in views:
                    _assert_paths(views["reservation"], {"admission_id": None, "consume_id": None})
                if "settlement" in views:
                    _assert_paths(views["settlement"], {"admission_granted": False,
                                                       "funds_executed": False, "durable": False})

    def test_all_refusals_preserve_detached_snapshots(self):
        for case in self.fixture["cases"]:
            _host, _receipts, refusals, snapshots = _drive(case)
            for index, step in enumerate(case["steps"]):
                if step["id"] in refusals:
                    previous = snapshots[case["steps"][index - 1]["id"]]
                    self.assertIsNot(previous, snapshots[step["id"]])
                    self.assertEqual(_canonical(previous), _canonical(snapshots[step["id"]]))

    def test_detached_output_mutations_fail_without_pin_changes(self):
        mutations = (
            lambda s: s[4]["receipt"]["reservation"].update(payment_ref="changed"),
            lambda s: s[-1]["receipt"]["reservation"].update(issuance_id="changed"),
            lambda s: s[-1]["receipt"]["reservation"].update(extra=None),
            lambda s: s[-1]["receipt"]["reservation"].pop("issuance_id"),
            lambda s: s[-1]["receipt"]["evidence"].update(chain_issued=0),
            lambda s: s[-1]["receipt"]["evidence"].update(version=True),
            lambda s: s[8].update(rejection_code="CHANGED"),
            lambda s: s[12].update(rejection_code="SETTLEMENT_AMOUNT_MISMATCH"),
            lambda s: s[11]["diagnostic_snapshot"]["views"]["reservation"].update(right={}),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["reservation"].update(state="changed"),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["settlement"].update(digest="0" * 64),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["reservation"]["journal"].pop(),
        )
        for mutate in mutations:
            document = copy.deepcopy(self.document)
            mutate(document["cases"][0]["steps"])
            with self.subTest(mutate=mutate), self.assertRaisesRegex(
                    AssertionError, "canonical receipt bytes differ"):
                compare_receipts(_canonical(document).encode())

    def test_input_semantic_controls_with_recomputed_pins(self):
        mutations = (
            ("step order", lambda f: f["cases"][0]["steps"].reverse()),
            ("step order", lambda f: f["cases"][0]["steps"].pop()),
            ("step order", lambda f: f["cases"][0]["steps"].append(f["cases"][0]["steps"][0])),
            ("case order", lambda f: f["cases"].reverse()),
            ("refusal mapping", lambda f: f["cases"][0]["steps"][8].update(expect_error="CHANGED")),
            ("fresh key", lambda f: f["cases"][0]["steps"][-1]["body"].update(idempotency_key="issue-early")),
            ("body binding", lambda f: f["cases"][0]["steps"][12]["body"].update(order_id="other")),
            ("key binding", lambda f: f["cases"][0]["steps"][12].update(refusal_of="issue-captured")),
            ("fresh issuance", lambda f: f["cases"][0]["steps"][-1]["body"].update(issuance_id="other")),
            ("command schema", lambda f: f["cases"][0]["steps"][1]["body"].update(capacity=True)),
            ("journal expectation", lambda f: f["cases"][0]["steps"][0]["expect"]["journal"].pop()),
        )
        for reason, mutate in mutations:
            fixture = copy.deepcopy(self.fixture)
            mutate(fixture)
            raw = _canonical(fixture).encode()
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
                target_count = 2 if target["id"] == "replay-issue-early" else 1
                calls = 0
                def corrupting_call(host, action, body):
                    nonlocal calls
                    try:
                        return real_call(host, action, body)
                    finally:
                        if action == target["action"] and body == target["body"]:
                            calls += 1
                        if calls == target_count:
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
