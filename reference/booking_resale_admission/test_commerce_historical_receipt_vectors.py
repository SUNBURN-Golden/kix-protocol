"""Source-informed portable historical receipt evidence; in-process, no golden writer.

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
import test_commerce_temporal_vectors as temporal
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_historical_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_historical_receipts_v1.json"
SOURCE_PATHS = goldens.SOURCE_PATHS | frozenset({
    "reference/booking_resale_admission/test_commerce_journey_receipts.py",
    "reference/booking_resale_admission/test_commerce_temporal_vectors.py",
    goldens.FIXTURE,
    str(goldens.GOLDEN.relative_to(ROOT)),
    "reference/booking_resale_admission/fixtures/commerce_temporal_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_temporal_receipts_v1.json",
    "reference/booking_resale_admission/test_reservation_fsm.py",
    "reference/booking_resale_admission/test_resale_fsm.py",
    "reference/settlement_f01_f03/test_settlement_fsm.py",
    "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md",
    "docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md",
    "docs/contracts/READ_MODEL_QUERIES.md",
})
# Independent, fixed case/step identities and order, not inferred from fixtures.
SETUP = ("reservation-clock", "show", "hold", "confirm", "payment", "issue")
SETTLEMENT = ("initiate", "settlement-authorize", "capture", "commit")
ORDERS = {
    "issuance-after-consumption": SETUP + ("authorize", "consume", "replay-issue"),
    "transfer-after-closure": SETTLEMENT + SETUP + (
        "resale-clock", "resale-adopt", "list", "resale-hold", "resale-payment",
        "bind-resale", "transfer", "close", "replay-transfer"),
    "distribution-after-partial-refund": SETTLEMENT + (
        "distribute", "partial-refund", "replay-distribute", "distribute-second",
        "replay-distribute-second"),
    "refund-after-mock-acceptance": SETTLEMENT + (
        "distribute", "full-refund", "mock-acceptance", "replay-distribute",
        "replay-full-refund", "replay-mock-acceptance"),
    "settlement-key-conflicts": (
        "initiate", "changed-initiate", "settlement-authorize", "capture",
        "bad-commit", "replay-bad-commit", "corrected-commit"),
}
REFUSALS = {name: {} for name in ORDERS}
REFUSALS["settlement-key-conflicts"] = {
    "changed-initiate": "IDEMPOTENCY_CONFLICT",
    "bad-commit": "SETTLEMENT_COMPONENT_MISMATCH",
    "replay-bad-commit": "SETTLEMENT_COMPONENT_MISMATCH",
    "corrected-commit": "IDEMPOTENCY_CONFLICT",
}


def _read(path):
    return (ROOT / path).read_bytes()


_assert_paths = temporal._assert_paths

def _views(host, accepted):
    views = {}
    if "reservation_hold" in accepted:
        views["reservation"] = host.machines["reservation"].view("reserve-1")
        views["show"] = host.machines["reservation"].view_show("show-1")
    if "resale_adopt_issued" in accepted:
        views["resale_right"] = host.machines["resale"].view_right("issue-1")
    if "resale_list_resale" in accepted:
        views["listing"] = host.machines["resale"].view("list-1")
    if "settlement_initiate" in accepted:
        views["settlement"] = host.machines["settlement"].view("claim-1")
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
                journey._check(_canonical(journey._without_replay_keys(receipt)) ==
                               _canonical(journey._without_replay_keys(first)), "immutable replay result")
                journey._check(_canonical(before) == _canonical(_snapshot(host, accepted)),
                               "replay mutated state/digest/journal/views")
            receipts[step["id"]] = receipt
            accepted.add(step["action"])
        for node in journey._walk(_views(host, accepted)):
            for flag in flags & node.keys():
                journey._check(node[flag] is False, "view authority flag: " + flag)
        _assert_views(host, accepted, step.get("observe", {}))
    _assert_views(host, accepted, case["final_expect"]["views"])
    for fact in case["final_expect"]["separate_facts"]:
        _assert_paths(receipts[fact["step"]], {fact["path"]: fact["value"]})
    journey._check(refusals == REFUSALS[case["id"]], "refusals")
    return host, receipts, refusals


def _observe(fixture_raw, fixture_pin, sources):
    fixture = goldens._decode(fixture_raw)
    journey._check(_canonical(fixture).encode("utf-8") == fixture_raw,
                   "canonical input bytes differ")
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
    return dict(record_schema_version="kix-commerce-historical-receipts/1",
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


class CommerceHistoricalReceiptVectorTests(unittest.TestCase):
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
            for source in [case["source_test"], *case.get("related_source_tests", [])]:
                path, method = source.split("::")
                self.assertIn(path, SOURCE_PATHS)
                self.assertIn("def " + method.split(".")[1] + "(", _read(path).decode())
            self.assertTrue(case["contract_predicates"])
            self.assertEqual(case["clocks"]["meaning"], "SYNTHETIC_FIXTURE_INPUTS_ONLY")

    def test_issuance_after_consumption(self):
        host, receipts, refusals = _drive(self.fixture["cases"][0])
        self.assertFalse(refusals)
        self.assertEqual(receipts["replay-issue"]["reservation"]["phase"], "ISSUED")
        self.assertEqual(receipts["replay-issue"]["reservation"]["right"]["version"], 1)
        self.assertEqual(host.machines["reservation"].view("reserve-1")["phase"], "CONSUMED")
        self.assertEqual(host.machines["reservation"].view("reserve-1")["right"]["version"], 2)

    def test_transfer_after_closure(self):
        host, receipts, refusals = _drive(self.fixture["cases"][1])
        self.assertFalse(refusals)
        self.assertEqual(receipts["replay-transfer"]["listing"]["phase"], "TRANSFERRED")
        self.assertEqual(host.machines["resale"].view("list-1")["phase"], "CLOSED")
        self.assertEqual(host.machines["resale"].view("list-1")["current_version"], 2)
        self.assertEqual(receipts["replay-transfer"]["right"]["holder_role"], "buyer-2")

    def test_distribution_after_partial_refund(self):
        host, receipts, refusals = _drive(self.fixture["cases"][2])
        self.assertFalse(refusals)
        self.assertEqual(receipts["replay-distribute"]["settlement"]["claim"]["refund_outstanding"], 0)
        current = host.machines["settlement"].view("claim-1")["claim"]
        self.assertEqual(current["refund_outstanding"], 40000)
        self.assertEqual(current["refund_bearer_policy"], "REQUESTER")
        self.assertEqual(current["distributed_cash"], 97000)
        for name in ("distribute-second", "replay-distribute-second"):
            self.assertEqual(receipts[name]["effect"], {"platform": 0, "organizer": 0})

    def test_refund_after_mock_acceptance(self):
        host, receipts, refusals = _drive(self.fixture["cases"][3])
        self.assertFalse(refusals)
        self.assertEqual(receipts["replay-full-refund"]["settlement"]["claim"]["refund_outstanding"], 100000)
        current = host.machines["settlement"].view("claim-1")
        self.assertEqual(current["claim"]["refund_outstanding"], 0)
        self.assertEqual(current["claim"]["pg_adjustment_outstanding"], 100000)
        self.assertIs(current["external_return_closed"], False)
        self.assertIs(current["claim"]["external_return_closed"], False)
        self.assertIs(current["bank_debit_observed"], False)

    def test_settlement_key_conflicts(self):
        host, receipts, refusals = _drive(self.fixture["cases"][4])
        self.assertEqual(refusals, REFUSALS["settlement-key-conflicts"])
        self.assertEqual(host.machines["settlement"].view("claim-1")["phase"], "CAPTURED")
        self.assertEqual(len(host.machines["settlement"].export_journal()), 3)
        self.assertEqual(set(receipts), {"initiate", "settlement-authorize", "capture"})

    def test_output_mutations_fail_comparison(self):
        original = [_drive(c) for c in self.fixture["cases"]]
        mutations = (
            (0, lambda r, f: r["issue"]["reservation"].update(issuance_id="changed")),
            (0, lambda r, f: r["issue"]["reservation"].update(extra=None)),
            (0, lambda r, f: r["issue"]["reservation"].pop("issuance_id")),
            (0, lambda r, f: r["issue"]["evidence"].update(chain_issued=0)),
            (0, lambda r, f: r["replay-issue"].update(applied="issue")),
            (1, lambda r, f: r["replay-transfer"]["listing"].update(phase="CLOSED")),
            (2, lambda r, f: r["replay-distribute"]["effect"].update(platform=0)),
            (2, lambda r, f: r["replay-distribute-second"]["effect"].update(platform=False)),
            (3, lambda r, f: r["replay-full-refund"]["settlement"]["claim"].update(refund_outstanding=0)),
            (4, lambda r, f: f.update({"bad-commit": "CHANGED"})),
        )
        for index, mutate in mutations:
            results = list(original)
            host, receipts, refusals = results[index]
            receipts, refusals = copy.deepcopy(receipts), copy.deepcopy(refusals)
            results[index] = (host, receipts, refusals)
            mutate(receipts, refusals)
            with self.subTest(index=index, mutate=mutate), patch(__name__ + "._drive", side_effect=results):
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

    def test_non_mutation_guard_detects_extra_effects(self):
        real_call = FsmHost.call
        for case_index, target in ((0, "replay-issue"), (4, "bad-commit")):
            case = self.fixture["cases"][case_index]
            target_step = next(s for s in case["steps"] if s["id"] == target)

            target_calls = 0

            def corrupting_call(host, action, body):
                nonlocal target_calls
                try:
                    return real_call(host, action, body)
                finally:
                    if action == target_step["action"] and body == target_step["body"]:
                        target_calls += 1
                    if target_calls == (2 if case_index == 0 else 1):
                        # Public, unrelated-machine effect: business state and
                        # journal must both be unchanged across replay/refusal.
                        real_call(host, "resale_set_clock", {
                            "subject_id": "clock", "idempotency_key": "extra-effect",
                            "now_ms": 77,
                        })

            with self.subTest(target=target), patch.object(FsmHost, "call", corrupting_call):
                with self.assertRaisesRegex(AssertionError, "mutated state/digest/journal/views"):
                    _drive(case)

    def test_input_binding_and_encoding_mutations_fail_before_execution(self):
        mutations = (
            lambda f: f["cases"][0]["steps"][-1].update(replay_of="payment"),
            lambda f: f["cases"][0]["steps"][-1]["body"].update(order_id="wrong-order"),
            lambda f: f["cases"][0]["steps"][1]["body"].update(capacity=True),
            lambda f: f["cases"][4]["steps"][-1].update(conflict_of="capture"),
            lambda f: f["cases"][4]["steps"][-2]["body"].update(amount=2),
        )
        for mutate in mutations:
            fixture = copy.deepcopy(self.fixture)
            mutate(fixture)
            with self.subTest(mutate=mutate), patch(__name__ + ".FsmHost") as host:
                with self.assertRaises(AssertionError):
                    _observe(_canonical(fixture).encode(), {}, [])
                host.assert_not_called()
        for raw in (_read(FIXTURE) + b"\n", json.dumps(self.fixture, indent=2).encode()):
            with self.subTest(encoding=raw[-20:]), patch(__name__ + ".FsmHost") as host:
                with self.assertRaisesRegex(AssertionError, "canonical input bytes differ"):
                    _observe(raw, {}, [])
                host.assert_not_called()

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
