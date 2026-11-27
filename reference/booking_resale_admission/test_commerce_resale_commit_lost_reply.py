"""Replay a missing resale settlement commit reply on two fresh hosts."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import parse_envelope
from mock_gates import _canonical
from test_commerce_fixture_tuple_conformance import (
    BOOKING_BRANCH_RECEIPTS, RECEIPTS, ROOT, VECTORS, read, snapshot,
)
from test_commerce_journey_receipts import _decode, _pin
from test_commerce_transfer_lost_reply import GRANT_SELECTION, MissingReply
from test_commerce_withheld_resale_refusal import bound_views, observe_resale_attempt

FIXTURE = "reference/booking_resale_admission/fixtures/commerce_resale_commit_lost_reply_v1.json"
TARGET = "booking-resale/settle-resale-commit"
PRE_COMMIT_REFUSAL = "booking-resale/accept-A-before-commit"
BOOKING_IDS = {"booking-resale/order-A", "booking-resale/payment-A", "booking-resale/issue-A"}


class CommerceResaleCommitLostReplyTests(unittest.TestCase):
    def test_both_losses_have_the_same_caller_observation(self):
        fixture = _decode(read(FIXTURE))
        self.assertEqual(fixture["record_schema_version"], "kix-commerce-resale-commit-lost-reply/1")
        self.assertIs(fixture["normative"], False)
        self.assertEqual([(case["id"], case["fault_point"]) for case in fixture["cases"]], [
            ("loss-before-dispatch", "before_dispatch"),
            ("loss-after-dispatch", "after_dispatch"),
        ])
        self.assertEqual(fixture["recovery_lookup"], "NOT_BOUND")
        recovery = _decode(read(GRANT_SELECTION))["cases"][27]
        self.assertEqual(recovery["id"], "proposed-uncertain-operation-recovery")
        self.assertEqual(recovery["request"]["kind"], "proposed_recovery")
        self.assertEqual(recovery["expect"], {"status": fixture["recovery_lookup"], "vector_id": None})

        vectors_raw = read(VECTORS)
        booking_raw = read(BOOKING_BRANCH_RECEIPTS)
        journey_raw = read(RECEIPTS)
        vector_pin = _pin(VECTORS, vectors_raw)
        self.assertEqual(fixture["source_vector"], {**vector_pin, "id": TARGET})
        self.assertEqual(fixture["source_booking_branch_receipts"], _pin(BOOKING_BRANCH_RECEIPTS, booking_raw))
        self.assertEqual(fixture["source_journey_receipts"], _pin(RECEIPTS, journey_raw))
        booking = _decode(booking_raw)
        self.assertEqual(booking["fixture"], vector_pin)

        vectors = _decode(vectors_raw)["vectors"]
        by_id = {vector["id"]: vector for vector in vectors}
        target = vectors[19]
        self.assertEqual(target["id"], TARGET)
        self.assertEqual(target["envelope"]["action"], "settlement_commit")
        self.assertEqual(target["input_index"], 23)
        self.assertEqual(len(target["setup"]), 16)
        self.assertEqual(len(set(target["setup"])), 16)
        self.assertEqual(set(target["setup"]) & booking["receipts"].keys(), BOOKING_IDS)
        self.assertEqual(target["setup"][-1], PRE_COMMIT_REFUSAL)

        journey_steps = _decode(journey_raw)["steps"]
        commands = load_catalogue(ROOT).commands
        setup = []
        for position, vector_id in enumerate(target["setup"][:-1]):
            vector = by_id[vector_id]
            self.assertEqual(vector["setup"], target["setup"][:position], vector_id)
            _, _, action, body = parse_envelope(vector["envelope"], commands)
            if vector_id in BOOKING_IDS:
                receipt = booking["receipts"][vector_id]
            else:
                receipt = self.journey_receipt(vector, journey_steps)
            setup.append((vector_id, action, body, receipt))

        refused_vector = by_id[PRE_COMMIT_REFUSAL]
        self.assertEqual(refused_vector["setup"], target["setup"][:-1])
        self.assertEqual(refused_vector["input_index"], 22)
        _, _, refused_action, refused_body = parse_envelope(refused_vector["envelope"], commands)
        golden_refusal = journey_steps[22]
        self.assertEqual(golden_refusal["id"], refused_vector["commerce_step"])
        self.assertEqual(golden_refusal["action"], refused_action)
        code = golden_refusal["rejection_code"]
        self.assertEqual(code, "SETTLEMENT_NOT_COMMITTED")
        self.assertEqual(refused_vector["expected"], {"kind": "business-reject", "code": code})

        golden_commit = self.journey_receipt(target, journey_steps)
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                host = FsmHost()
                for vector_id, action, body, receipt in setup:
                    actual = host.call(action, deepcopy(body))
                    self.assertEqual(_canonical(actual), _canonical(receipt), vector_id)
                before = snapshot(host)
                with self.assertRaises(FsmRejected) as rejected:
                    host.call(refused_action, deepcopy(refused_body))
                self.assertEqual(rejected.exception.code, code)
                self.assertEqual(snapshot(host), before)

                observation, evidence = self.replay_commit(
                    host, commands, target, case["fault_point"], before, refused_body["listing_id"],
                    golden_commit,
                )
                self.assertEqual(_canonical(observation), _canonical(fixture["expected_caller"]))
                self.assertEqual(_canonical(evidence), _canonical(case["producer_evidence"]))

    def journey_receipt(self, vector, steps):
        index = vector["input_index"]
        golden = steps[index]
        self.assertEqual(vector["expected"]["receipt_ref"], f"{RECEIPTS}#/steps/{index}/receipt")
        self.assertEqual(golden["id"], vector["commerce_step"])
        self.assertEqual(golden["action"], vector["envelope"]["action"])
        return golden["receipt"]

    def replay_commit(self, host, commands, target, fault_point, before, listing_id, golden):
        envelope = target["envelope"]
        after_dispatch = fault_point == "after_dispatch"
        sent = []
        hidden_receipts = []
        expected_dispatches = []
        receipt_ref = None

        def transport(request):
            sent.append(deepcopy(request))
            if after_dispatch:
                _, _, action, body = parse_envelope(request, commands)
                hidden_receipts.append(host.call(action, body))
            raise MissingReply

        with patch.object(host, "call", wraps=host.call) as dispatch:
            observation = observe_resale_attempt(deepcopy(envelope), transport)
        self.assertEqual(_canonical(sent), _canonical([envelope]))
        observation.update(attempts=len(sent), follow_up_calls=len(sent) - 1)

        after = snapshot(host)
        if after_dispatch:
            expected_dispatches = [call("settlement_commit", envelope["body"])]
            self.assertEqual(
                [_canonical(receipt).encode("utf-8") for receipt in hidden_receipts],
                [_canonical(golden).encode("utf-8")],
            )
            receipt_ref = target["expected"]["receipt_ref"]
        else:
            self.assertEqual(hidden_receipts, [])
            self.assertEqual(after, before)
        self.assertEqual(dispatch.call_args_list, expected_dispatches)

        journal_delta = {}
        appended_entries = {}
        for name, (state, journal) in after.items():
            prior_state, prior_journal = before[name]
            self.assertEqual(journal[:len(prior_journal)], prior_journal, name)
            appended = journal[len(prior_journal):]
            journal_delta[name] = len(appended)
            if appended:
                appended_entries[name] = appended
            if name != "settlement":
                self.assertEqual(state, prior_state, name)

        views = bound_views(host, listing_id)
        settlement = host.machines["settlement"].view(envelope["body"]["settlement_id"])
        self.assertEqual(views["settlement"]["settlement_id"], settlement["settlement_id"])
        views["settlement"]["claim"] = {"distributed_cash": settlement["claim"]["distributed_cash"]}
        return observation, {
            "dispatches": dispatch.call_count,
            "hidden_receipt_ref": receipt_ref,
            **views,
            "journal_delta": journal_delta,
            "appended_journal_entries": appended_entries,
        }
