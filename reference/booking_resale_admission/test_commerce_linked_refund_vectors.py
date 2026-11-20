"""Replay a settlement-bound purchase and partial refund in the mock host."""
from __future__ import annotations

import copy
import unittest

import test_commerce_entry_resale_order_vectors as ordering
import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
REFERENCE = "reference/booking_resale_admission/"
FIXTURE = REFERENCE + "fixtures/commerce_linked_refund_inputs_v1.json"
GOLDEN = ROOT / (REFERENCE + "fixtures/commerce_linked_refund_receipts_v1.json")
SOURCE_PATHS = goldens.SOURCE_PATHS | {
    REFERENCE + "fixtures/commerce_bound_issuance_inputs_v1.json",
    REFERENCE + "fixtures/commerce_admission_cancellation_inputs_v1.json",
    REFERENCE + "test_commerce_bound_issuance_vectors.py",
    REFERENCE + "test_commerce_admission_cancellation_vectors.py",
    REFERENCE + "test_commerce_entry_resale_order_vectors.py",
    REFERENCE + "test_commerce_journey_receipts.py",
    REFERENCE + "test_commerce_temporal_vectors.py",
    "reference/settlement_f01_f03/test_cancel_acceptance_adapter.py",
    "docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md",
    "docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md",
}

CASE = "linked-purchase-partial-refund"
ORDER = (
    ("reservation-clock", "reservation_set_clock"),
    ("show", "reservation_register_show"),
    ("hold", "reservation_hold"),
    ("confirm", "reservation_confirm"),
    ("payment", "reservation_observe_payment"),
    ("initiate", "settlement_initiate"),
    ("settlement-authorize", "settlement_authorize"),
    ("bind", "reservation_bind_settlement"),
    ("capture", "settlement_capture"),
    ("commit", "settlement_commit"),
    ("issue-committed", "reservation_issue"),
    ("admission-clock", "admission_set_clock"),
    ("admission-adopt", "admission_adopt_issued"),
    ("cancel-issued", "reservation_cancel"),
    ("bind-refund", "settlement_bind_refund"),
    ("observe-mock-acceptance", "settlement_observe_mock_cancel_acceptance"),
    ("authorize", "admission_authorize_admission"),
    ("consume", "admission_consume"),
)
MACHINES = {"reservation", "settlement", "resale", "admission", "credit"}
FALSE_FLAGS = set(NON_CLAIMS) | set(journey.SETTLEMENT_FINALITY_FLAGS) | {
    "economic_finality_claimed", "chain_issued", "venue_credential_reissued", "offline_admission",
}
_assert_paths = ordering._assert_paths
_check = journey._check


def _read(path):
    return (ROOT / path).read_bytes()


def _check_purchase_bodies(bodies):
    for step in ("initiate", "settlement-authorize", "bind", "capture", "commit",
                 "bind-refund", "observe-mock-acceptance"):
        _check(bodies[step]["settlement_id"] == "claim-1", "linked settlement: " + step)
    for step in ("hold", "confirm", "bind", "admission-adopt", "cancel-issued"):
        _check(bodies[step]["reservation_id"] == "reserve-1", "linked reservation: " + step)
    for step in ("confirm", "payment", "issue-committed", "admission-adopt"):
        _check(bodies[step]["order_id"] == "order-1", "linked order: " + step)
    for step in ("admission-adopt", "authorize", "consume"):
        _check(bodies[step]["right_id"] == "issue-1", "linked right: " + step)
    _assert_paths(bodies, {
        "issue-committed.issuance_id": "issue-1", "hold.buyer_role": "buyer-1",
        "bind-refund.beneficiary_role": "buyer-1", "authorize.holder_role": "buyer-1",
        "show.primary_price": 10001, "confirm.amount": 10001, "payment.amount": 10001,
        "initiate.gross": 10001, "commit.gross": 10001, "commit.amount": 10001,
        "bind-refund.amount": 4000, "observe-mock-acceptance.amount": 1500,
        "authorize.admission_id": "admit-1", "consume.consume_id": "consume-1",
    })
    adopt = bodies["admission-adopt"]
    for setup, fields in (
        ("show", ("show_id", "capacity", "primary_price", "organizer_role", "platform_bps",
                  "organizer_bps", "resale_allowed", "resale_cap", "gate_roles")),
        ("hold", ("show_id", "slot", "buyer_role", "expires_ms")),
        ("confirm", ("amount", "quote_ref")),
        ("payment", ("payment_ref",)),
    ):
        _assert_paths(adopt, {field: bodies[setup][field] for field in fields})
    _assert_paths(bodies["consume"], {
        field: bodies["authorize"][field] for field in ("request", "gate_role", "version")
    })


def _validate(fixture):
    catalogue = load_catalogue(ROOT)
    _assert_paths(fixture, {
        "fixture_version": 1, "domain": catalogue.fsm_domain,
        "provenance": "OFFLINE_CONFORMANCE_FIXTURE_ONLY",
    })
    _check([case["id"] for case in fixture["cases"]] == [CASE], "case order")
    case, = fixture["cases"]
    _check(tuple((s["id"], s["action"]) for s in case["steps"]) == ORDER, "step/action order")
    _check({s["id"]: s["expect_error"] for s in case["steps"] if "expect_error" in s} ==
           {"cancel-issued": "CANCEL_AFTER_ISSUE"}, "refusal mapping")
    keys = set()
    for step in case["steps"]:
        _check(("expect" in step) != ("expect_error" in step), "one expectation")
        action, body = step["action"], step["body"]
        _check(action in catalogue.fsm_names, "unpublished action")
        spec = catalogue.fsm["commands"][action]
        _check(not problems(body, spec["schema"]), "command schema: " + step["id"])
        _check(body["idempotency_key"] not in keys, "fresh idempotency key")
        keys.add(body["idempotency_key"])
        if "expect" in step:
            expect = step["expect"]
            _assert_paths(expect, {"duplicate": False, "applied": spec["op"]})
            journal = expect["journal"]
            _check(len(journal) == len(MACHINES) and {j["machine"] for j in journal} == MACHINES,
                   "journal expectation coverage")
    _check_purchase_bodies({step["id"]: step["body"] for step in case["steps"]})
    return case


def _snapshot(host, accepted):
    snapshot = ordering._snapshot(host, accepted)
    if "settlement_initiate" in accepted:
        snapshot["views"]["settlement"] = copy.deepcopy(host.machines["settlement"].view("claim-1"))
    return snapshot


def _drive(case):
    host = FsmHost()
    accepted = set()
    before = _snapshot(host, accepted)
    outcomes = []
    for index, step in enumerate(case["steps"]):
        name, action = step["id"], step["action"]
        outcome = dict(id=name, action=action, input_ref=f"{FIXTURE}#/cases/0/steps/{index}/body")
        try:
            receipt = host.call(action, copy.deepcopy(step["body"]))
        except FsmRejected as exc:
            _check(exc.code == step.get("expect_error"), "unexpected refusal: " + exc.code)
            outcome["rejection_code"] = exc.code
        else:
            _check("expect" in step, "expected refusal was accepted")
            expect = step["expect"]
            _assert_paths(receipt, {"duplicate": expect["duplicate"], "applied": expect["applied"],
                                    **expect["paths"]})
            outcome["receipt"] = copy.deepcopy(receipt)
            accepted.add(action)
        after = _snapshot(host, accepted)
        if "rejection_code" in outcome:
            _check(_canonical(after) == _canonical(before), "refusal mutated state/digest/journal/views")
        else:
            for entry in expect["journal"]:
                machine, delta = entry["machine"], entry["delta"]
                previous, current = before["machines"][machine], after["machines"][machine]
                count = len(previous["journal"])
                _check(len(current["journal"]) == count + delta, f"journal delta: {name}/{machine}")
                _check(_canonical(current["journal"][:count]) == _canonical(previous["journal"]),
                       f"journal prefix changed: {name}/{machine}")
                if delta == 0:
                    _check(_canonical(previous) == _canonical(current), f"machine changed: {name}/{machine}")
        for node in journey._walk([outcome.get("receipt", {}), after["views"]]):
            for flag in FALSE_FLAGS & node.keys():
                _check(node[flag] is False, "authority flag: " + flag)
        outcome["diagnostic_snapshot"] = after
        outcomes.append(outcome)
        before = after
    _assert_paths(before["views"], case["final_expect"]["views"])
    return outcomes


def _observe(fixture_raw, fixture_pin, sources):
    fixture = goldens._decode(fixture_raw)
    _check(_canonical(fixture).encode("utf-8") == fixture_raw, "canonical input bytes differ")
    case = _validate(fixture)
    return dict(record_schema_version="kix-commerce-linked-refund-receipts/1",
                record_kind="IN_PROCESS_MOCK_RECEIPT_VECTORS", normative=False,
                fixture=fixture_pin, sources=sources, cases=[dict(id=case["id"], steps=_drive(case))])


def compare_receipts(raw):
    expected = goldens._decode(raw)
    fixture_raw = _read(FIXTURE)
    fixture_pin = goldens._pin(FIXTURE, fixture_raw)
    sources = [goldens._pin(path, _read(path)) for path in sorted(SOURCE_PATHS)]
    _check(expected["fixture"] == fixture_pin, "fixture pin drift")
    _check(expected["sources"] == sources, "source pin drift/set/order")
    observed = _observe(fixture_raw, fixture_pin, sources)
    _check(_canonical(observed).encode("utf-8") == raw, "complete canonical receipt bytes differ")
    return observed


class CommerceLinkedRefundVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = GOLDEN.read_bytes()
        cls.fixture = goldens._decode(_read(FIXTURE))

    def test_complete_output_bytes_and_references(self):
        case, = compare_receipts(self.raw)["cases"]
        self.assertEqual(case["id"], CASE)
        for index, (step, outcome) in enumerate(zip(self.fixture["cases"][0]["steps"],
                                                    case["steps"], strict=True)):
            with self.subTest(step=step["id"]):
                path, pointer = outcome["input_ref"].split("#")
                self.assertEqual(path, FIXTURE)
                self.assertEqual(pointer, f"/cases/0/steps/{index}/body")
                resolved = self.fixture
                for segment in pointer[1:].split("/"):
                    resolved = resolved[int(segment)] if isinstance(resolved, list) else resolved[segment]
                self.assertEqual(_canonical(resolved), _canonical(step["body"]))
                kind = "rejection_code" if "expect_error" in step else "receipt"
                self.assertEqual(set(outcome), {"id", "action", "input_ref", kind, "diagnostic_snapshot"})
                self.assertEqual(set(outcome["diagnostic_snapshot"]["machines"]), MACHINES)

    def test_purchase_stages_and_partial_acceptance(self):
        outcomes = {step["id"]: step for step in _drive(_validate(self.fixture))}
        snapshots = {name: step["diagnostic_snapshot"] for name, step in outcomes.items()}
        _assert_paths(outcomes["payment"]["receipt"], {
            "reservation.phase": "PAYMENT_NOTED", "reservation.settlement_id": None,
            "reservation.payment_ref": "ab" * 32, "reservation.right": None,
        })
        self.assertNotIn("settlement", snapshots["payment"]["views"])
        _assert_paths(snapshots["commit"]["views"], {
            "reservation.phase": "PAYMENT_NOTED", "reservation.settlement_id": "claim-1",
            "reservation.settlement_gate": "BOUND", "reservation.right": None,
            "settlement.settlement_id": "claim-1", "settlement.phase": "COMMITTED",
            "settlement.claim.confirmed_cash": 10001, "settlement.claim.refund_face": 0,
        })
        issued = outcomes["issue-committed"]["receipt"]["reservation"]
        _assert_paths(issued, {
            "phase": "ISSUED", "settlement_id": "claim-1", "settlement_gate": "MOCK_COMMIT_OBSERVED",
            "mock_settlement_commit_observed": True, "right.right_id": "issue-1",
            "right.holder_role": "buyer-1", "right.state": "ACTIVE", "right.version": 1,
        })
        self.assertEqual(outcomes["cancel-issued"]["rejection_code"], "CANCEL_AFTER_ISSUE")
        self.assertEqual(_canonical(snapshots["admission-adopt"]), _canonical(snapshots["cancel-issued"]))

        before = snapshots["bind-refund"]
        after = snapshots["observe-mock-acceptance"]
        for snapshot, accepted, outstanding, adjustment in ((before, 0, 4000, 0), (after, 1500, 2500, 1500)):
            views = snapshot["views"]
            _assert_paths(views, {
                "settlement.settlement_id": "claim-1", "settlement.phase": "COMMITTED",
                "settlement.external_return_closed": False, "settlement.right_cancelled": False,
                "settlement.claim.claim_id": "claim-1", "settlement.claim.confirmed_cash": 10001,
                "settlement.claim.refund_face": 4000, "settlement.claim.refund_beneficiary": "buyer-1",
                "settlement.claim.refund_accepted": accepted, "settlement.claim.refund_outstanding": outstanding,
                "settlement.claim.pg_adjustment_outstanding": adjustment,
                "settlement.claim.external_return_closed": False, "settlement.claim.right_cancelled": False,
                "reservation.right": issued["right"], "credential.phase": "ELIGIBLE",
            })
        before_view = before["views"]["settlement"]
        self.assertEqual(_canonical(after["views"]["settlement"]), _canonical(dict(
            before_view, accepted_entries=before_view["accepted_entries"] + 1,
            claim=dict(before_view["claim"], refund_accepted=1500, refund_outstanding=2500,
                       pg_adjustment_outstanding=1500))))
        self.assertTrue(before["machines"]["admission"]["journal"])
        for machine in MACHINES - {"settlement"}:
            self.assertEqual(_canonical(after["machines"][machine]), _canonical(before["machines"][machine]))
        journal = after["machines"]["settlement"]["journal"]
        self.assertEqual(journal[:-1], before["machines"]["settlement"]["journal"])
        _assert_paths(journal[-1], {
            "op": "observe_mock_cancel_acceptance", "settlement_id": "claim-1", "body.amount": 1500,
        })

    def test_explicit_authorization_and_consumption_preserve_settlement(self):
        outcomes = {step["id"]: step for step in _drive(_validate(self.fixture))}
        _assert_paths(outcomes["authorize"]["receipt"], {
            "applied": "authorize_admission", "credential.phase": "AUTHORIZED", "credential.version": 1,
            "credential.right_id": "issue-1", "credential.admission_id": "admit-1", "credential.consume_id": None,
        })
        _assert_paths(outcomes["consume"]["receipt"], {
            "applied": "consume", "credential.phase": "CONSUMED", "credential.version": 2,
            "credential.right_id": "issue-1", "credential.consume_id": "consume-1",
            "evidence.decision": "CONSUMED_ONCE", "evidence.version_after": 2, "right.version": 2,
        })
        accepted = outcomes["observe-mock-acceptance"]["diagnostic_snapshot"]
        for name in ("authorize", "consume"):
            snapshot = outcomes[name]["diagnostic_snapshot"]
            for key in ("machines", "views"):
                self.assertEqual(_canonical(snapshot[key]["settlement"]), _canonical(accepted[key]["settlement"]))

    def test_crossed_input_and_changed_receipt_do_not_compare(self):
        for field in ("input_ref", "receipt"):
            document = goldens._decode(self.raw)
            steps = {step["id"]: step for step in document["cases"][0]["steps"]}
            target = steps["observe-mock-acceptance"]
            if field == "input_ref":
                target["input_ref"] = steps["bind-refund"]["input_ref"]
            else:
                target["receipt"]["settlement"]["claim"]["refund_accepted"] = 1501
            with self.subTest(field=field), self.assertRaisesRegex(AssertionError, "canonical receipt bytes differ"):
                compare_receipts(_canonical(document).encode("utf-8"))

    def test_fixture_rejects_crossed_settlement_and_malformed_command(self):
        for field, value, diagnostic in (("settlement_id", "other-claim", "linked settlement"),
                                         ("amount", True, "command schema")):
            fixture = copy.deepcopy(self.fixture)
            step = next(s for s in fixture["cases"][0]["steps"] if s["id"] == "observe-mock-acceptance")
            step["body"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(AssertionError, diagnostic):
                _validate(fixture)


if __name__ == "__main__":
    unittest.main()
