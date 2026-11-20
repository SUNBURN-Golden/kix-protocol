"""Replay late synthetic payment after cancellation and reuse in the in-process host."""
from __future__ import annotations

import copy
import unittest

import test_commerce_admission_cancellation_vectors as cancellation
import test_commerce_hold_release_vectors as hold_release
import test_commerce_journey_conformance as journey
import test_commerce_journey_receipts as goldens
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import problems
from mock_gates import NON_CLAIMS, _canonical

ROOT = journey.ROOT
REFERENCE = "reference/booking_resale_admission/"
FIXTURE = REFERENCE + "fixtures/commerce_late_payment_after_cancel_inputs_v1.json"
GOLDEN = ROOT / (REFERENCE + "fixtures/commerce_late_payment_after_cancel_receipts_v1.json")
SOURCE_PATHS = hold_release.SOURCE_PATHS | {
    cancellation.FIXTURE,
    REFERENCE + "test_commerce_admission_cancellation_vectors.py",
    REFERENCE + "test_commerce_hold_release_vectors.py",
    "docs/contracts/STATE_LIFECYCLE.md",
}

CASE = "late-payment-after-cancel"
ORDER = (
    ("reservation-clock", "reservation_set_clock"),
    ("show", "reservation_register_show"),
    ("hold-a", "reservation_hold"),
    ("confirm-a", "reservation_confirm"),
    ("cancel-a", "reservation_cancel"),
    ("hold-b", "reservation_hold"),
    ("confirm-b", "reservation_confirm"),
    ("late-payment-a", "reservation_observe_payment"),
    ("replay-late-payment-a", "reservation_observe_payment"),
    ("replay-cancel-a", "reservation_cancel"),
    ("payment-b", "reservation_observe_payment"),
    ("issue-b", "reservation_issue"),
    ("admission-clock", "admission_set_clock"),
    ("adopt-b", "admission_adopt_issued"),
    ("authorize-b", "admission_authorize_admission"),
    ("consume-b", "admission_consume"),
)
REPLAYS = {"replay-late-payment-a": "late-payment-a", "replay-cancel-a": "cancel-a"}
REFUSALS = dict.fromkeys(("late-payment-a", "replay-late-payment-a"), "TERMINAL_IMMUTABLE")
PREDICATES = [
    "BOOKING_RESALE_ADMISSION_GATES.md §§9.2–9.3, 9.6",
    "BOOKING_RESALE_ADMISSION_GATES.md §9.4",
    "BOOKING_RESALE_ADMISSION_GATES.md §9.5",
    "BOOKING_RESALE_ADMISSION_GATES.md §§11.2–11.5",
]
MACHINES = {"reservation", "admission", "settlement", "resale", "credit"}
SHARED_ADMISSION_STEPS = {"admission-clock", "authorize-b", "consume-b"}
FALSE_FLAGS = set(NON_CLAIMS) | set(journey.SETTLEMENT_FINALITY_FLAGS) | {
    "economic_finality_claimed", "chain_issued", "venue_credential_reissued", "offline_admission",
}
CANCELLED_A = {
    "reservation_id": "reserve-1", "order_id": "order-1", "buyer_role": "buyer-1",
    "phase": "CANCELLED", "terminal": True, "payment_ref": None, "issuance_id": None,
    "right": None, "compensation_defined": False,
}
_assert_paths = hold_release._assert_paths
_check = journey._check


def _read(path):
    return (ROOT / path).read_bytes()


def _check_bindings(bodies):
    clocks = cancellation.CLOCKS
    _assert_paths(bodies, {
        "reservation-clock.now_ms": clocks["T0"], "admission-clock.now_ms": clocks["T0"],
        "show.show_id": "show-1", "show.primary_price": clocks["amount"],
        "cancel-a.reservation_id": "reserve-1", "issue-b.order_id": "order-2",
        "issue-b.issuance_id": "issue-2", "adopt-b.right_id": "issue-2",
        "authorize-b.right_id": "issue-2", "authorize-b.holder_role": "buyer-2",
        "authorize-b.admission_id": "admit-2", "authorize-b.version": 1,
        "authorize-b.gate_role": "gate-a", "authorize-b.request": "11" * 32,
        "authorize-b.expires_ms": clocks["authorization_expires_ms"],
        "consume-b.consume_id": "consume-2",
    })
    for side, number, payment_step, payment in (
        ("a", 1, "late-payment-a", "ab" * 32),
        ("b", 2, "payment-b", "cd" * 32),
    ):
        _assert_paths(bodies[f"hold-{side}"], {
            "reservation_id": f"reserve-{number}", "buyer_role": f"buyer-{number}",
            "show_id": "show-1", "slot": 0, "expires_ms": clocks["reservation_expires_ms"],
        })
        _assert_paths(bodies[f"confirm-{side}"], {
            "reservation_id": f"reserve-{number}", "order_id": f"order-{number}",
            "quote_ref": f"quote-{number}", "amount": clocks["amount"],
        })
        _assert_paths(bodies[payment_step], {
            "order_id": f"order-{number}", "payment_ref": payment, "amount": clocks["amount"],
        })
    for step, fields in (
        ("show", ("show_id", "capacity", "primary_price", "organizer_role", "platform_bps",
                  "organizer_bps", "resale_allowed", "resale_cap", "gate_roles")),
        ("hold-b", ("reservation_id", "buyer_role", "slot", "expires_ms")),
        ("confirm-b", ("order_id", "quote_ref", "amount")),
        ("payment-b", ("payment_ref",)),
    ):
        _assert_paths(bodies["adopt-b"], {field: bodies[step][field] for field in fields})
    _assert_paths(bodies["consume-b"], {
        field: bodies["authorize-b"][field] for field in ("right_id", "version", "gate_role", "request")
    })


def _validate(fixture):
    catalogue = load_catalogue(ROOT)
    _assert_paths(fixture, {
        "fixture_version": 1, "domain": catalogue.fsm_domain,
        "provenance": "OFFLINE_CONFORMANCE_FIXTURE_ONLY",
    })
    _check([case["id"] for case in fixture["cases"]] == [CASE], "case order")
    case, = fixture["cases"]
    _assert_paths(case, {"clocks": cancellation.CLOCKS, "contract_predicates": PREDICATES})
    steps = case["steps"]
    _check(tuple((s["id"], s["action"]) for s in steps) == ORDER, "step/action order")
    _check({s["id"]: s["expect_error"] for s in steps if "expect_error" in s} == REFUSALS, "refusal mapping")
    _check({s["id"]: s["replay_of"] for s in steps if "replay_of" in s} == REPLAYS, "replay mapping")
    bodies, keys = {}, set()
    for step in steps:
        name, action, body = step["id"], step["action"], step["body"]
        _check(("expect" in step) != ("expect_error" in step), "one expectation")
        spec = catalogue.fsm["commands"][action]
        _check(not problems(body, spec["schema"]), "command schema: " + name)
        key = body["idempotency_key"]
        if name in REPLAYS:
            _check(_canonical(body) == _canonical(bodies[REPLAYS[name]]), "exact replay body: " + name)
        else:
            _check(key not in keys, "fresh key: " + name)
        bodies[name] = body
        keys.add(key)
        if "expect" in step:
            replay = name in REPLAYS
            expect = step["expect"]
            _assert_paths(expect, {"duplicate": replay, "applied": None if replay else spec["op"]})
            journal = expect["journal"]
            changing = set() if replay else {spec["machine"]}
            if name in SHARED_ADMISSION_STEPS:
                changing.add("reservation")
            _check(len(journal) == len(MACHINES) and {j["machine"] for j in journal} == MACHINES,
                   "journal expectation coverage")
            for entry in journal:
                _assert_paths(entry, {"delta": int(entry["machine"] in changing)})
    _check_bindings(bodies)
    return case


def _check_journals(before, after, expectations, step):
    for entry in expectations:
        machine, delta = entry["machine"], entry["delta"]
        previous, current = before["machines"][machine], after["machines"][machine]
        count = len(previous["journal"])
        _check(len(current["journal"]) == count + delta, f"journal delta: {step}/{machine}")
        _check(_canonical(current["journal"][:count]) == _canonical(previous["journal"]),
               f"journal prefix changed: {step}/{machine}")
        if delta == 0:
            _check(_canonical(previous) == _canonical(current), f"machine changed: {step}/{machine}")


def _drive(case):
    host = FsmHost()
    before = hold_release._snapshot(host)
    outcomes = []
    for index, step in enumerate(case["steps"]):
        name, action = step["id"], step["action"]
        outcome = dict(id=name, action=action, input_ref=f"{FIXTURE}#/cases/0/steps/{index}/body")
        try:
            receipt = host.call(action, copy.deepcopy(step["body"]))
        except FsmRejected as exc:
            _check(exc.code == step.get("expect_error"), f"unexpected refusal: {name}/{exc.code}")
            outcome["rejection_code"] = exc.code
        else:
            _check("expect" in step, "expected refusal was accepted: " + name)
            expect = step["expect"]
            _assert_paths(receipt, {"duplicate": expect["duplicate"], "applied": expect["applied"],
                                    **expect["paths"]})
            outcome["receipt"] = copy.deepcopy(receipt)

        after = hold_release._snapshot(host)
        if "rejection_code" in outcome or name in REPLAYS:
            _check(_canonical(before) == _canonical(after), "snapshot changed: " + name)
        if "expect" in step:
            _check_journals(before, after, expect["journal"], name)
        for node in journey._walk([outcome.get("receipt", {}), after["views"]]):
            for flag in FALSE_FLAGS & node.keys():
                _check(node[flag] is False, "authority flag: " + flag)
        outcome["diagnostic_snapshot"] = after
        outcomes.append(outcome)
        before = after
    _assert_paths(before["views"], case["final_expect"]["views"])
    return outcomes


def _observe():
    fixture_raw = _read(FIXTURE)
    fixture = goldens._decode(fixture_raw)
    _check(_canonical(fixture).encode("utf-8") == fixture_raw, "canonical input bytes differ")
    case = _validate(fixture)
    return dict(
        record_schema_version="kix-commerce-late-payment-after-cancel-receipts/1",
        record_kind="IN_PROCESS_MOCK_RECEIPT_VECTORS", normative=False,
        fixture=goldens._pin(FIXTURE, fixture_raw),
        sources=[goldens._pin(path, _read(path)) for path in sorted(SOURCE_PATHS)],
        cases=[dict(id=case["id"], steps=_drive(case))],
    )


class CommerceLatePaymentAfterCancelVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observed = _observe()
        cls.outcomes = {step["id"]: step for step in cls.observed["cases"][0]["steps"]}

    def test_complete_output_bytes_and_references(self):
        self.assertEqual(_canonical(self.observed).encode("utf-8"), GOLDEN.read_bytes())
        fixture = goldens._decode(_read(FIXTURE))
        steps = fixture["cases"][0]["steps"]
        for index, (step, outcome) in enumerate(zip(steps, self.outcomes.values(), strict=True)):
            with self.subTest(step=step["id"]):
                path, pointer = outcome["input_ref"].split("#")
                self.assertEqual(path, FIXTURE)
                self.assertEqual(pointer, f"/cases/0/steps/{index}/body")
                resolved = fixture
                for part in pointer[1:].split("/"):
                    resolved = resolved[int(part)] if isinstance(resolved, list) else resolved[part]
                self.assertEqual(_canonical(resolved), _canonical(step["body"]))
                kind = "rejection_code" if "expect_error" in step else "receipt"
                self.assertEqual(set(outcome), {"id", "action", "input_ref", kind, "diagnostic_snapshot"})
                self.assertEqual(set(outcome["diagnostic_snapshot"]["machines"]), MACHINES)

    def test_late_payment_and_replay_preserve_state(self):
        before = self.outcomes["confirm-b"]["diagnostic_snapshot"]
        for name in REFUSALS:
            with self.subTest(step=name):
                refused = self.outcomes[name]
                self.assertEqual(refused["rejection_code"], "TERMINAL_IMMUTABLE")
                self.assertEqual(_canonical(refused["diagnostic_snapshot"]), _canonical(before))
        _assert_paths(before["views"]["reservations"]["reserve-1"], CANCELLED_A)
        _assert_paths(before["views"]["reservations"]["reserve-2"], {
            "order_id": "order-2", "buyer_role": "buyer-2", "phase": "CONFIRMED",
            "slot_state": "RESERVED", "slot_reservation_id": "reserve-2", "payment_ref": None, "right": None,
        })
        _assert_paths(before["views"]["show"]["show"]["slots"][0], {
            "slot": 0, "state": "RESERVED", "reservation_id": "reserve-2", "right_id": None,
        })

    def test_cancel_replay_returns_historical_slot(self):
        first = self.outcomes["cancel-a"]["receipt"]
        replay = self.outcomes["replay-cancel-a"]
        _assert_paths(replay["receipt"], {
            "duplicate": True, "applied": None, "reservation.slot_state": "FREE",
            "reservation.slot_reservation_id": None,
        })
        _assert_paths(replay["receipt"]["show"]["slots"][0], {
            "slot": 0, "state": "FREE", "reservation_id": None, "right_id": None,
        })
        self.assertEqual(_canonical(journey._without_replay_keys(replay["receipt"])),
                         _canonical(journey._without_replay_keys(first)))
        before = self.outcomes["replay-late-payment-a"]["diagnostic_snapshot"]
        self.assertEqual(_canonical(replay["diagnostic_snapshot"]), _canonical(before))
        _assert_paths(replay["diagnostic_snapshot"]["views"]["reservations"]["reserve-2"],
                      {"slot_state": "RESERVED", "slot_reservation_id": "reserve-2"})

    def test_replacement_payment_issue_authorize_and_consume(self):
        _assert_paths(self.outcomes["payment-b"]["receipt"], {
            "applied": "observe_payment", "reservation.phase": "PAYMENT_NOTED",
            "reservation.order_id": "order-2", "reservation.payment_ref": "cd" * 32,
            "reservation.issuance_id": None, "reservation.right": None,
        })
        _assert_paths(self.outcomes["issue-b"]["receipt"], {
            "applied": "issue", "reservation.phase": "ISSUED", "reservation.issuance_id": "issue-2",
            "reservation.settlement_gate": "UNBOUND", "reservation.mock_settlement_commit_observed": False,
            "reservation.right.right_id": "issue-2", "reservation.right.holder_role": "buyer-2",
            "reservation.right.state": "ACTIVE", "reservation.right.version": 1,
        })
        _assert_paths(self.outcomes["authorize-b"]["receipt"], {
            "applied": "authorize_admission", "credential.phase": "AUTHORIZED", "credential.version": 1,
            "credential.right_id": "issue-2", "credential.admission_id": "admit-2", "credential.consume_id": None,
        })
        consumed = self.outcomes["consume-b"]
        _assert_paths(consumed["receipt"], {
            "applied": "consume", "credential.phase": "CONSUMED", "credential.version": 2,
            "credential.right_id": "issue-2", "credential.consume_id": "consume-2",
            "right.right_id": "issue-2", "right.version": 2,
            "evidence.decision": "CONSUMED_ONCE", "evidence.version_after": 2,
        })
        final = consumed["diagnostic_snapshot"]
        _assert_paths(final["views"]["reservations"]["reserve-1"], CANCELLED_A)
        self.assertEqual(final["machines"]["settlement"]["journal"], [])


if __name__ == "__main__":
    unittest.main()
