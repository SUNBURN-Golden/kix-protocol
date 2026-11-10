"""Consumer-facing offline conformance transcript for one commerce journey.

This module drives one show through the published FSM catalogue only, using
the in-process ``integration_gate.fsm_host.FsmHost`` and the deterministic
fixture ``fixtures/commerce_journey_conformance_v1.json``. Coverage is one
ordered journey through reservation, primary payment observation, issuance,
resale listing and ownership transfer, admission, settlement distribution,
cancellation, failure and refund, plus five adverse refusals.

The evidence is the command receipt returned by each published action. This
module adds no command, route, console, read API, authentication, retry,
real-funds path, policy value or production endpoint. The 13 read-query names
stay ``NOT_BOUND``: the fixture lists them and the test requires their absence
from both catalogue pins and the in-process host.

Everything here is MOCK_GATE_ONLY / MOCK_SETTLEMENT_ONLY, in one process, with
caller-supplied fixture constants. A receipt is not a payment, a venue
credential, chain ownership, economic finality, durability or production
admission. The always-false flags are asserted, not relaxed.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from integration_gate.catalogue import load_catalogue
from integration_gate.constants import FSM_COMMAND_COUNT
from integration_gate.fsm_host import FsmHost, FsmRejected
from mock_gates import NON_CLAIMS

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "commerce_journey_conformance_v1.json"
)

# docs/contracts/READ_MODEL_QUERIES.md section 1 (User decision, 2026-10-08).
# These names have no catalogue entry, wire binding or read API in this tree.
READ_MODEL_QUERY_NAMES = (
    "list_shows",
    "get_show",
    "get_booking",
    "list_bookings",
    "get_right",
    "get_presentation",
    "list_open_listings",
    "get_listing",
    "get_admission",
    "get_credential",
    "get_settlement",
    "get_credit_advance",
    "get_credit_claim",
)

# The published actions one primary journey (non-adverse steps) must bind.
PRIMARY_ACTIONS = frozenset(
    {
        "reservation_set_clock",
        "reservation_register_show",
        "reservation_hold",
        "reservation_confirm",
        "reservation_observe_payment",
        "reservation_issue",
        "reservation_cancel",
        "resale_set_clock",
        "resale_adopt_issued",
        "resale_list_resale",
        "resale_hold_buy",
        "resale_observe_resale_payment",
        "resale_bind_settlement",
        "resale_accept_resale",
        "admission_set_clock",
        "admission_adopt_issued",
        "admission_authorize_admission",
        "admission_consume",
        "settlement_initiate",
        "settlement_authorize",
        "settlement_capture",
        "settlement_commit",
        "settlement_distribute",
        "settlement_cancel",
        "settlement_fail",
        "settlement_bind_refund",
        "settlement_observe_mock_cancel_acceptance",
    }
)

ADVERSE_REFUSALS = {
    "hold-over-capacity": "SLOT",
    "hold-occupied-slot": "SLOT_OCCUPIED",
    "issue-cancelled": "TERMINAL_IMMUTABLE",
    "double-consume": "ALREADY_CONSUMED",
    "accept-A-before-commit": "SETTLEMENT_NOT_COMMITTED",
}

SETTLEMENT_FINALITY_FLAGS = (
    "funds_executed",
    "legal_debtor_bound",
    "bank_debit_observed",
    "external_return_closed",
    "right_cancelled",
    "admission_granted",
    "provider_authorization_executed",
)

_REPLAY_IGNORED_KEYS = frozenset({"duplicate", "applied"})


def _check(condition, message):
    if not condition:
        raise AssertionError(message)


def _resolve(receipt, path):
    value = receipt
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise AssertionError("receipt has no path %r" % path)
        value = value[part]
    return value


def _same(actual, expected):
    # JSON booleans are asserted by identity so 0/1 cannot pass for False/True.
    if isinstance(expected, bool):
        return actual is expected
    return actual == expected


def _without_replay_keys(receipt):
    return {
        key: value
        for key, value in receipt.items()
        if key not in _REPLAY_IGNORED_KEYS
    }


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _drive(fixture):
    """Execute the fixture in order. Return host, receipts and refusals."""
    host = FsmHost()
    receipts = {}
    refusals = {}
    for step in fixture["steps"]:
        step_id = step["id"]
        before = {
            name: len(machine.export_journal())
            for name, machine in host.machines.items()
        }
        try:
            receipt = host.call(step["action"], step["body"])
        except FsmRejected as exc:
            _check(
                "expect_error" in step,
                "%s: unexpected refusal %s" % (step_id, exc.code),
            )
            _check(
                exc.code == step["expect_error"],
                "%s: refusal %s, expected %s"
                % (step_id, exc.code, step["expect_error"]),
            )
            for name, machine in host.machines.items():
                after = len(machine.export_journal())
                _check(
                    after == before[name],
                    "%s: refusal appended to the %s journal" % (step_id, name),
                )
            refusals[step_id] = exc.code
            continue
        if "expect_error" in step:
            raise AssertionError(
                "%s: expected refusal %s but the call was accepted"
                % (step_id, step["expect_error"])
            )
        expect = step["expect"]
        _check(
            receipt.get("duplicate") is expect["duplicate"],
            "%s: duplicate is %r, expected %r"
            % (step_id, receipt.get("duplicate"), expect["duplicate"]),
        )
        _check(
            receipt.get("applied") == expect["applied"],
            "%s: applied is %r, expected %r"
            % (step_id, receipt.get("applied"), expect["applied"]),
        )
        for path, expected in expect.get("paths", {}).items():
            actual = _resolve(receipt, path)
            _check(
                _same(actual, expected),
                "%s: %s is %r, expected %r"
                % (step_id, path, actual, expected),
            )
        for journal in expect.get("journal", []):
            machine = journal["machine"]
            after = len(host.machines[machine].export_journal())
            delta = after - before[machine]
            _check(
                delta == journal["delta"],
                "%s: %s journal grew by %d, expected %d"
                % (step_id, machine, delta, journal["delta"]),
            )
        receipts[step_id] = receipt
    return host, receipts, refusals


class CommerceJourneyConformanceTests(unittest.TestCase):
    """One deterministic transcript; every assertion is offline and local."""

    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.catalogue = load_catalogue(ROOT)
        cls.host, cls.receipts, cls.refusals = _drive(cls.fixture)

    def _steps(self):
        return self.fixture["steps"]

    def test_every_step_binds_a_published_action_and_body(self):
        names = self.catalogue.fsm_names
        self.assertEqual(len(names), FSM_COMMAND_COUNT)
        self.assertEqual(len(set(names)), FSM_COMMAND_COUNT)
        self.assertEqual(
            self.fixture["final_expect"]["fsm_command_count"], FSM_COMMAND_COUNT
        )
        seen = [step["id"] for step in self._steps()]
        self.assertEqual(len(seen), len(set(seen)))
        for step in self._steps():
            action = step["action"]
            self.assertIn(action, names, step["id"])
            command = self.catalogue.fsm["commands"][action]
            schema = command["schema"]
            body = step["body"]
            self.assertIn(command["subject_field"], body, step["id"])
            self.assertLessEqual(set(schema["required"]), set(body), step["id"])
            self.assertLessEqual(set(body), set(schema["properties"]), step["id"])
            self.assertNotIn("domain", body, step["id"])
            if "expect_error" in step:
                self.assertIsInstance(step["expect_error"], str, step["id"])
            elif "replay_of" in step:
                self.assertIsNone(step["expect"]["applied"], step["id"])
            else:
                self.assertEqual(
                    step["expect"]["applied"], command["op"], step["id"]
                )

    def test_one_show_covers_the_whole_published_journey(self):
        show = self.fixture["show"]
        primary = set()
        for step in self._steps():
            body = step["body"]
            if "show_id" in body:
                self.assertEqual(body["show_id"], show["show_id"], step["id"])
            if step["group"] != "adverse":
                primary.add(step["action"])
        self.assertEqual(primary, set(PRIMARY_ACTIONS))

        self.assertEqual(self.refusals, ADVERSE_REFUSALS)
        self.assertEqual(
            set(self.receipts) | set(self.refusals),
            {step["id"] for step in self._steps()},
        )
        # Every accepted receipt is the receipt of the action the fixture bound.
        by_id = {step["id"]: step for step in self._steps()}
        for step_id, receipt in self.receipts.items():
            step = by_id[step_id]
            if "replay_of" in step:
                continue
            action = step["action"]
            self.assertEqual(
                receipt["applied"], self.catalogue.fsm["commands"][action]["op"]
            )

        # The show binding is repeated exactly on both adopt commands.
        for step_id in ("adopt-A", "adopt-B"):
            body = by_id[step_id]["body"]
            for field in (
                "show_id",
                "organizer_role",
                "capacity",
                "gate_roles",
                "primary_price",
                "resale_cap",
                "resale_allowed",
                "organizer_bps",
                "platform_bps",
            ):
                self.assertEqual(body[field], show[field], (step_id, field))

    def test_payment_issuance_and_admission_are_separate_facts(self):
        final = self.fixture["final_expect"]
        identifiers = final["distinct_identifiers"]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        for fact in final["separate_facts"]:
            receipt = self.receipts[fact["step"]]
            self.assertEqual(
                _resolve(receipt, fact["path"]), fact["value"], fact["fact"]
            )

        payment = self.receipts["payment-B"]
        issuance = self.receipts["issue-B"]
        authorize = self.receipts["authorize-B"]
        consume = self.receipts["consume-B"]

        # A payment observation is not an issuance and does not carry either
        # later identity.
        self.assertEqual(payment["reservation"]["phase"], "PAYMENT_NOTED")
        self.assertIsNone(payment["reservation"]["issuance_id"])
        self.assertIsNone(payment["reservation"]["admission_id"])
        # Issuance is its own receipt and right identity.
        self.assertEqual(issuance["reservation"]["phase"], "ISSUED")
        self.assertEqual(issuance["evidence"]["right_id"], "issue-B")
        self.assertIs(issuance["evidence"]["chain_issued"], False)
        # Admission authorization and consume are separate receipt facts.
        self.assertEqual(authorize["credential"]["phase"], "AUTHORIZED")
        self.assertEqual(authorize["credential"]["admission_id"], "admit-B")
        self.assertEqual(consume["credential"]["phase"], "CONSUMED")
        self.assertEqual(consume["credential"]["consume_id"], "consume-B")

        facts = (
            payment["reservation"]["payment_ref"],
            issuance["reservation"]["issuance_id"],
            authorize["credential"]["admission_id"],
            consume["credential"]["consume_id"],
        )
        self.assertEqual(len(set(facts)), len(facts))
        self.assertEqual(set(facts), {"b2" * 32, "issue-B", "admit-B", "consume-B"})
        self.assertIsNot(payment, issuance)
        self.assertIsNot(authorize, consume)

    def test_flags_and_non_claims_stay_false(self):
        final = self.fixture["final_expect"]
        flags = set(final["always_false_flags"])
        self.assertLessEqual(set(NON_CLAIMS), flags)
        for step_id, receipt in self.receipts.items():
            for node in _walk(receipt):
                for flag in flags:
                    if flag in node:
                        self.assertIs(
                            node[flag], False, "%s: %s" % (step_id, flag)
                        )
            for key, expected in final["receipt_invariants"].items():
                self.assertIn(key, receipt, step_id)
                self.assertEqual(receipt[key], expected, step_id)

        for step_id in (
            "settle-resale-commit",
            "distribute-resale",
            "bind-refund",
            "observe-mock-acceptance",
            "settle-cancel",
            "settle-fail",
        ):
            settlement = self.receipts[step_id]["settlement"]
            for flag in SETTLEMENT_FINALITY_FLAGS:
                self.assertIs(settlement[flag], False, (step_id, flag))

    def test_read_queries_remain_not_bound(self):
        names = tuple(READ_MODEL_QUERY_NAMES)
        self.assertEqual(len(names), 13)
        self.assertEqual(len(set(names)), 13)
        self.assertEqual(
            tuple(self.fixture["final_expect"]["read_queries"]), names
        )
        core_names = set(self.catalogue.core_names)
        fsm_names = set(self.catalogue.fsm_names)
        self.assertFalse(fsm_names & set(names))
        for name in names:
            self.assertNotIn(name, core_names)
            self.assertNotIn(name, fsm_names)
            self.assertNotIn(name, self.catalogue.names)
            self.assertNotIn(name, self.host._commands)

    def test_replay_returns_the_existing_duplicate_result(self):
        replays = [step for step in self._steps() if "replay_of" in step]
        self.assertEqual([step["id"] for step in replays], ["replay-consume-B"])
        for step in replays:
            original = self.receipts[step["replay_of"]]
            replay = self.receipts[step["id"]]
            self.assertIs(replay["duplicate"], True)
            self.assertIsNone(replay["applied"])
            self.assertEqual(
                _without_replay_keys(replay), _without_replay_keys(original)
            )
            self.assertEqual(step["expect"]["journal"][0]["delta"], 0)


if __name__ == "__main__":
    unittest.main()
