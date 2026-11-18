"""Portable source-informed settlement-bound resale evidence; no golden writer.

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
FIXTURE = "reference/booking_resale_admission/fixtures/commerce_bound_resale_inputs_v1.json"
GOLDEN = ROOT / "reference/booking_resale_admission/fixtures/commerce_bound_resale_receipts_v1.json"
PRIOR_INPUTS = (
    goldens.FIXTURE,
    "reference/booking_resale_admission/fixtures/commerce_temporal_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_historical_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_entry_resale_order_inputs_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_bound_issuance_inputs_v1.json",
)
SOURCE_PATHS = historical.SOURCE_PATHS | frozenset(PRIOR_INPUTS) | frozenset({
    "reference/booking_resale_admission/test_commerce_historical_receipt_vectors.py",
    "reference/booking_resale_admission/test_commerce_bound_issuance_vectors.py",
    "reference/booking_resale_admission/test_commerce_entry_resale_order_vectors.py",
    "reference/booking_resale_admission/fixtures/commerce_historical_receipts_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_entry_resale_order_receipts_v1.json",
    "reference/booking_resale_admission/fixtures/commerce_bound_issuance_receipts_v1.json",
})
# Independent identities, order and errors; never derived from fixture data.
SETUP = ("reservation-clock", "show", "hold", "confirm", "payment", "issue",
         "resale-clock", "resale-adopt", "list", "resale-payment")
ORDERS = {
    "committed-resale-amount-mismatch": SETUP + (
        "initiate", "settlement-authorize", "capture", "commit", "bind-resale", "transfer-mismatch"),
    "failed-settlement-blocks-transfer": SETUP + (
        "initiate", "fail", "bind-resale", "transfer-failed"),
    "rejected-transfer-after-commit": SETUP + (
        "initiate", "settlement-authorize", "bind-resale", "transfer-early", "capture", "commit",
        "replay-transfer-early", "transfer-fresh", "replay-transfer-fresh"),
}
REFUSALS = {
    "committed-resale-amount-mismatch": {"transfer-mismatch": "SETTLEMENT_AMOUNT_MISMATCH"},
    "failed-settlement-blocks-transfer": {"transfer-failed": "SETTLEMENT_NOT_COMMITTED"},
    "rejected-transfer-after-commit": {
        "transfer-early": "SETTLEMENT_NOT_COMMITTED",
        "replay-transfer-early": "SETTLEMENT_NOT_COMMITTED"},
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
            journey._check(key not in keys or "refusal_of" in step or "replay_of" in step, "fresh key required")
            keys.add(key)
            if "expect" in step:
                journey._check(len(step["expect"]["journal"]) == 5 and
                               {j["machine"] for j in step["expect"]["journal"]} == MACHINES,
                               "journal expectation coverage")
                journey._check(all(type(j["delta"]) is int and j["delta"] in (0, 1)
                                   for j in step["expect"]["journal"]), "journal scalar type")
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


    steps = {s["id"]: s for s in fixture["cases"][2]["steps"]}
    journey._check(steps["replay-transfer-early"].get("refusal_of") == "transfer-early",
                   "explicit original rejected key")
    journey._check(steps["replay-transfer-fresh"].get("replay_of") == "transfer-fresh",
                   "explicit accepted replay")
    original, fresh = steps["transfer-early"]["body"], steps["transfer-fresh"]["body"]
    journey._check(fresh["idempotency_key"] != original["idempotency_key"] and
                   {k: v for k, v in fresh.items() if k != "idempotency_key"} ==
                   {k: v for k, v in original.items() if k != "idempotency_key"},
                   "explicit fresh transfer key/body")


def _assert_semantics(case, receipts, snapshots):
    _assert_paths(receipts["payment"], {
        "reservation.phase": "PAYMENT_NOTED", "reservation.payment_ref": "ab" * 32,
        "reservation.right": None, "reservation.issuance_id": None})
    _assert_paths(receipts["issue"], {
        "reservation.phase": "ISSUED", "reservation.issuance_id": "issue-1",
        "evidence.right_id": "issue-1", "evidence.version": 1, "evidence.chain_issued": False})
    transferred = False
    for step in case["steps"]:
        views = snapshots[step["id"]]["views"]
        if step["id"] == "transfer-fresh":
            transferred = True
        if "reservation" in views:
            _assert_paths(views["reservation"], {"admission_id": None, "consume_id": None})
        if "listing" in views and step["id"] != "list":
            bound = step["id"] not in ("resale-payment", "initiate", "settlement-authorize",
                                        "capture", "commit", "fail")
            # Mismatch/failure cases bind after commit/fail; the retained-key case binds before capture.
            if case["id"] == "rejected-transfer-after-commit" and step["id"] in ("capture", "commit"):
                bound = True
            _assert_paths(views["listing"], {
                "amount": 8000, "payment_ref": "cd" * 32,
                "phase": "TRANSFERRED" if transferred else "PAYMENT_NOTED",
                "holder_role": "buyer-2" if transferred else "buyer-1",
                "current_version": 2 if transferred else 1,
                "ownership_transferred": transferred, "generation": 1,
                "slot_state": "ISSUED", "slot_right_id": "issue-1",
                "mock_settlement_commit_observed": transferred,
                "settlement_gate": "MOCK_COMMIT_OBSERVED" if transferred else ("BOUND" if bound else "UNBOUND")})
            _assert_paths(views["resale_right"], {
                "right.right_id": "issue-1", "right.version": 2 if transferred else 1,
                "right.holder_role": "buyer-2" if transferred else "buyer-1",
                "right.generation": 1, "right.admission_id": None})
        if "settlement" in views:
            gross = 10001 if case["id"] == "committed-resale-amount-mismatch" else 8000
            _assert_paths(views["settlement"], {"gross": gross, "funds_executed": False,
                                               "admission_granted": False, "durable": False})
    if transferred:
        first, replay = receipts["transfer-fresh"], receipts["replay-transfer-fresh"]
        duplicate = copy.deepcopy(first)
        duplicate.update(duplicate=True, applied=None)
        journey._check(_canonical(duplicate) == _canonical(replay), "first receipt changed on replay")


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
        # Each command may affect only its catalogue machine. In particular,
        # settlement commit cannot transfer ownership; binding/transfer only read settlement.
        target = host._commands[step["action"]]["machine"]
        for name in MACHINES - {target}:
            journey._check(_canonical(before["machines"][name]) ==
                           _canonical(snapshot["machines"][name]), "unrelated machine changed: " + name)
        if step.get("replay_of"):
            journey._check(_canonical(before) == _canonical(snapshot), "accepted replay added effects")
        snapshots[step["id"]] = snapshot
        _assert_views(host, accepted, step.get("observe", {}))
    _assert_views(host, accepted, case["final_expect"]["views"])
    for fact in case["final_expect"]["separate_facts"]:
        _assert_paths(receipts[fact["step"]], {fact["path"]: fact["value"]})
    journey._check(refusals == REFUSALS[case["id"]], "refusals")
    _assert_semantics(case, receipts, snapshots)
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
    return dict(record_schema_version="kix-commerce-bound-resale-receipts/1",
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


class CommerceBoundResaleVectorTests(unittest.TestCase):
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

    def test_existing_coverage_and_portable_gaps(self):
        for path in PRIOR_INPUTS:
            fixture = goldens._decode(_read(path))
            cases = fixture.get("cases", [fixture])
            for case in cases:
                self.assertNotIn(case.get("id"), ORDERS)
                rejected = [s for s in case["steps"] if s["action"] == "resale_accept_resale"
                            and "expect_error" in s]
                if path == goldens.FIXTURE:
                    self.assertEqual([(s["id"], s["expect_error"]) for s in rejected],
                                     [("accept-A-before-commit", "SETTLEMENT_NOT_COMMITTED")])
                    ids = [s["id"] for s in case["steps"]]
                    self.assertLess(ids.index("accept-A-before-commit"), ids.index("settle-resale-commit"))
                    self.assertLess(ids.index("settle-resale-commit"), ids.index("accept-A"))
                else:
                    self.assertEqual(rejected, [], path)
        _validate(self.fixture)
        catalogue, host = load_catalogue(ROOT), FsmHost()
        self.assertEqual(len(journey.READ_MODEL_QUERY_NAMES), 13)
        for name in journey.READ_MODEL_QUERY_NAMES:
            self.assertNotIn(name, catalogue.names)
            self.assertNotIn(name, host._commands)
        for case in self.fixture["cases"]:
            path, method = case["source_test"].split("::")
            self.assertIn(path, SOURCE_PATHS)
            self.assertEqual(method, "ResaleFsmTests.test_bound_transfer_waits_for_mock_commit_and_reconciles")
            self.assertIn("def " + method.split(".")[1] + "(", _read(path).decode())
            self.assertEqual(case["contract_predicates"], [
                "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#10.5",
                "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#10.6",
                "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#10.7",
                "docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md#9"])
            self.assertEqual(case["clocks"], {"meaning": "SYNTHETIC_FIXTURE_INPUTS_ONLY",
                                             "now_ms": 1000000, "expires_ms": 1900000})

    def test_commit_retains_rejection_until_explicit_fresh_key(self):
        _host, receipts, errors, snapshots = _drive(self.fixture["cases"][2])
        self.assertEqual(errors, REFUSALS["rejected-transfer-after-commit"])
        for name, phase in (("transfer-early", "AUTHORIZED"), ("capture", "CAPTURED"),
                            ("commit", "COMMITTED"), ("replay-transfer-early", "COMMITTED")):
            _assert_paths(snapshots[name]["views"], {
                "settlement.phase": phase, "listing.phase": "PAYMENT_NOTED",
                "listing.holder_role": "buyer-1", "listing.current_version": 1,
                "listing.mock_settlement_commit_observed": False,
                "listing.settlement_gate": "BOUND", "listing.transfer_id": None})
        _assert_paths(receipts["transfer-fresh"], {
            "duplicate": False, "applied": "accept_resale", "listing.phase": "TRANSFERRED",
            "listing.settlement_gate": "MOCK_COMMIT_OBSERVED",
            "listing.mock_settlement_commit_observed": True,
            "right.right_id": "issue-1", "right.generation": 1,
            "right.holder_role": "buyer-2", "right.version": 2,
            "right.admission_id": None, "evidence.amount": 8000})
        self.assertEqual(len(snapshots["transfer-fresh"]["machines"]["resale"]["journal"]),
                         len(snapshots["commit"]["machines"]["resale"]["journal"]) + 1)
        self.assertEqual(_canonical(snapshots["transfer-fresh"]),
                         _canonical(snapshots["replay-transfer-fresh"]))

    def test_refusals_preserve_all_machines(self):
        for case in self.fixture["cases"]:
            _host, _receipts, errors, snapshots = _drive(case)
            self.assertEqual(errors, REFUSALS[case["id"]])
            for index, step in enumerate(case["steps"]):
                if step["id"] in errors:
                    previous = snapshots[case["steps"][index - 1]["id"]]
                    self.assertIsNot(previous, snapshots[step["id"]])
                    self.assertEqual(_canonical(previous), _canonical(snapshots[step["id"]]))
                    _assert_paths(snapshots[step["id"]]["views"], {
                        "listing.phase": "PAYMENT_NOTED", "listing.current_version": 1,
                        "listing.holder_role": "buyer-1", "listing.settlement_id": "claim-1",
                        "listing.payment_ref": "cd" * 32, "reservation.payment_ref": "ab" * 32})

    def test_separate_facts_and_non_claims(self):
        for case in self.fixture["cases"]:
            _host, receipts, _errors, snapshots = _drive(case)
            _assert_semantics(case, receipts, snapshots)
            for step in case["steps"]:
                if step["id"] in SETUP[6:]:
                    _assert_paths(snapshots[step["id"]]["views"], {
                        "reservation.phase": "ISSUED", "reservation.issuance_id": "issue-1",
                        "reservation.right.version": 1, "reservation.right.holder_role": "buyer-1"})
            # Reservation issuance remains its own fact even after resale ownership transfer.
            _assert_paths(snapshots[case["steps"][-1]["id"]]["views"], {
                "reservation.right.version": 1, "reservation.right.holder_role": "buyer-1",
                "reservation.admission_id": None, "reservation.consume_id": None})

    def test_output_receipt_error_snapshot_reference_mutations(self):
        mutations = (
            lambda s: s[4]["receipt"]["reservation"].update(payment_ref="changed"),
            lambda s: s[5]["receipt"]["evidence"].update(chain_issued=0),
            lambda s: s[5]["receipt"]["evidence"].update(version=True),
            lambda s: s[-1]["receipt"]["right"].update(version=3),
            lambda s: s[-1]["receipt"]["listing"].update(extra=None),
            lambda s: s[-1]["receipt"].pop("evidence"),
            lambda s: s[13].update(rejection_code="SETTLEMENT_AMOUNT_MISMATCH"),
            lambda s: s[16].update(rejection_code="CHANGED"),
            lambda s: s[15]["diagnostic_snapshot"]["views"]["listing"].update(holder_role="buyer-2"),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["resale"].update(state="changed"),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["settlement"].update(digest="0" * 64),
            lambda s: s[-1]["diagnostic_snapshot"]["machines"]["resale"]["journal"].pop(),
            lambda s: s[0].update(input_ref=FIXTURE + "#/cases/1/steps/0/body"),
            lambda s: s[0].update(action="changed"), lambda s: s[0].update(id="changed"),
            lambda s: s.reverse(), lambda s: s.pop(), lambda s: s.append(copy.deepcopy(s[0])),
        )
        for index, mutate in enumerate(mutations):
            document = copy.deepcopy(self.document)
            mutate(document["cases"][2]["steps"])
            with self.subTest(index=index), self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                compare_receipts(_canonical(document).encode())

    def test_semantic_controls_with_recomputed_input_pins(self):
        mutations = (
            ("step order", lambda f: f["cases"][2]["steps"].reverse()),
            ("step order", lambda f: f["cases"][2]["steps"].pop()),
            ("step order", lambda f: f["cases"][2]["steps"].append(f["cases"][2]["steps"][0])),
            ("case order", lambda f: f["cases"].reverse()),
            ("refusal mapping", lambda f: f["cases"][2]["steps"][13].update(expect_error="CHANGED")),
            ("fresh key", lambda f: f["cases"][2]["steps"][17]["body"].update(idempotency_key="transfer-early")),
            ("body binding", lambda f: f["cases"][2]["steps"][16]["body"].update(transfer_id="other")),
            ("key binding", lambda f: f["cases"][2]["steps"][16].update(refusal_of="issue")),
            ("fresh transfer", lambda f: [f["cases"][2]["steps"][i]["body"].update(transfer_id="other") for i in (17, 18)]),
            ("command schema", lambda f: f["cases"][0]["steps"][1]["body"].update(capacity=True)),
            ("journal expectation", lambda f: f["cases"][0]["steps"][0]["expect"]["journal"].pop()),
            ("journal scalar", lambda f: f["cases"][0]["steps"][0]["expect"]["journal"][0].update(delta=False)),
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

    def test_non_mutation_guard_detects_extra_effect_at_every_refusal(self):
        real_call = FsmHost.call
        for case in self.fixture["cases"]:
            for target in (s for s in case["steps"] if "expect_error" in s):
                target_count = 2 if target["id"] == "replay-transfer-early" else 1
                calls = 0
                def corrupting_call(host, action, body):
                    nonlocal calls
                    try:
                        return real_call(host, action, body)
                    finally:
                        if action == target["action"] and body == target["body"]:
                            calls += 1
                            if calls == target_count:
                                real_call(host, "reservation_set_clock", {
                                    "subject_id": "clock", "idempotency_key": "extra-effect",
                                    "now_ms": 1000001})
                with self.subTest(case=case["id"], target=target["id"]), patch.object(FsmHost, "call", corrupting_call):
                    with self.assertRaisesRegex(AssertionError, "mutated state/digest/journal/views"):
                        _drive(case)

    def test_commit_cannot_automatically_transfer(self):
        case = self.fixture["cases"][2]
        fresh = next(s for s in case["steps"] if s["id"] == "transfer-fresh")
        real_call = FsmHost.call
        def premature_transfer(host, action, body):
            receipt = real_call(host, action, body)
            if action == "settlement_commit":
                real_call(host, fresh["action"], copy.deepcopy(fresh["body"]))
            return receipt
        with patch.object(FsmHost, "call", premature_transfer):
            with self.assertRaisesRegex(AssertionError, "journal delta: commit/resale|unrelated machine changed: resale"):
                _drive(case)

    def test_replay_cannot_add_an_effect(self):
        case = self.fixture["cases"][2]
        real_call = FsmHost.call
        def extra_effect(host, action, body):
            receipt = real_call(host, action, body)
            if action == "resale_accept_resale" and receipt["duplicate"]:
                real_call(host, "resale_set_clock", {
                    "subject_id": "clock", "idempotency_key": "extra-effect", "now_ms": 1000001})
            return receipt
        with patch.object(FsmHost, "call", extra_effect):
            with self.assertRaisesRegex(AssertionError, "journal delta|accepted replay added effects"):
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
