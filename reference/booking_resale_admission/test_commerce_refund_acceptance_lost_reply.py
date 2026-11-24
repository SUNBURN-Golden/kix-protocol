"""Replay a missing mock refund acceptance reply across two producer histories."""

import unittest
from copy import deepcopy
from unittest.mock import patch

from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost
from integration_gate.schema import parse_envelope
from mock_gates import _canonical
from test_commerce_fixture_tuple_conformance import (
    BOOKING_BRANCH_RECEIPTS,
    RECEIPTS,
    ROOT,
    VECTORS,
    read,
    snapshot,
)
from test_commerce_journey_receipts import _decode, _pin

FIXTURE = "reference/booking_resale_admission/fixtures/commerce_refund_acceptance_lost_reply_v1.json"
GRANT_SELECTION = "sdk/conformance/vectors/producer-grant-selection.vectors.json"
TARGET = "booking-refund/observe-mock-acceptance"
TARGET_RECEIPT = f"{RECEIPTS}#/steps/38/receipt"
BRANCH_SETUP = {f"booking-refund/{step}" for step in ("reserve-C", "order-C", "cancel-C")}


class MissingReply(Exception):
    """The transport delivered no receipt."""


def observe_acceptance(envelope, send):
    try:
        send(envelope)
    except MissingReply:
        return {
            "operationId": envelope["operationId"],
            "idempotency_key": envelope["body"]["idempotency_key"],
            "outcome": "UNKNOWN",
            "receipt": None,
        }
    raise AssertionError("expected a missing reply")


class CommerceRefundAcceptanceLostReplyTests(unittest.TestCase):
    def test_both_losses_have_the_same_caller_observation(self):
        fixture = _decode(read(FIXTURE))
        self.assertEqual(fixture["record_schema_version"], "kix-commerce-refund-acceptance-lost-reply/1")
        self.assertIs(fixture["normative"], False)
        self.assertEqual([(case["id"], case["fault_point"]) for case in fixture["cases"]], [
            ("loss-before-dispatch", "before_dispatch"),
            ("loss-after-dispatch", "after_dispatch"),
        ])
        self.assertEqual(fixture["recovery_lookup"], "NOT_BOUND")
        self.assertEqual([
            (case["request"]["kind"], case["expect"])
            for case in _decode(read(GRANT_SELECTION))["cases"]
            if case["id"] == "proposed-uncertain-operation-recovery"
        ], [("proposed_recovery", {"status": fixture["recovery_lookup"], "vector_id": None})])

        corpus_raw = read(VECTORS)
        corpus_pin = _pin(VECTORS, corpus_raw)
        self.assertEqual(fixture["source_vector"], {**corpus_pin, "id": TARGET})
        journey_raw = read(RECEIPTS)
        self.assertEqual(fixture["source_journey_receipts"], _pin(RECEIPTS, journey_raw))
        booking_raw = read(BOOKING_BRANCH_RECEIPTS)
        self.assertEqual(fixture["source_booking_branch_receipts"],
                         _pin(BOOKING_BRANCH_RECEIPTS, booking_raw))
        booking = _decode(booking_raw)
        self.assertEqual(booking["fixture"], corpus_pin)

        vectors = {vector["id"]: vector for vector in _decode(corpus_raw)["vectors"]}
        target = vectors[TARGET]
        self.assertEqual(len(target["setup"]), 13)
        self.assertEqual(target["setup"][-1], "booking-refund/bind-refund")
        self.assertEqual(target["expected"]["receipt_ref"], TARGET_RECEIPT)
        journey_steps = _decode(journey_raw)["steps"]
        goldens = {}
        for vector_id in [*target["setup"], TARGET]:
            vector = vectors[vector_id]
            self.assertEqual(vector["expected"]["kind"], "accept", vector_id)
            if vector_id in BRANCH_SETUP:
                self.assertNotIn("receipt_ref", vector["expected"], vector_id)
                goldens[vector_id] = booking["receipts"][vector_id]
            else:
                index = vector["input_index"]
                self.assertEqual(vector["expected"]["receipt_ref"], f"{RECEIPTS}#/steps/{index}/receipt")
                self.assertEqual(journey_steps[index]["action"], vector["envelope"]["action"])
                goldens[vector_id] = journey_steps[index]["receipt"]

        commands = load_catalogue(ROOT).commands
        for case in fixture["cases"]:
            with self.subTest(fault_point=case["fault_point"]):
                self.replay_case(case, vectors, goldens, commands, fixture["expected_caller"])

    def replay_case(self, case, vectors, goldens, commands, expected_caller):
        host = FsmHost()
        target = vectors[TARGET]
        for vector_id in target["setup"]:
            _, _, action, body = parse_envelope(vectors[vector_id]["envelope"], commands)
            self.assertEqual(_canonical(host.call(action, body)), _canonical(goldens[vector_id]),
                             vector_id)
        before = snapshot(host)
        envelope = target["envelope"]
        after_dispatch = case["fault_point"] == "after_dispatch"
        sent = []
        hidden_receipts = []

        def transport(request):
            sent.append(deepcopy(request))
            if after_dispatch:
                _, _, action, body = parse_envelope(request, commands)
                hidden_receipts.append(host.call(action, body))
            raise MissingReply

        with patch.object(host, "call", wraps=host.call) as dispatch:
            observation = observe_acceptance(deepcopy(envelope), transport)
        self.assertEqual(_canonical(sent), _canonical([envelope]))
        observation["attempts"] = len(sent)
        observation["follow_up_calls"] = len(sent) - 1
        self.assertEqual(_canonical(observation), _canonical(expected_caller))

        after = snapshot(host)
        if after_dispatch:
            self.assertEqual(_canonical(hidden_receipts), _canonical([goldens[TARGET]]))
        else:
            self.assertEqual(hidden_receipts, [])
            self.assertEqual(_canonical(after), _canonical(before))

        journal_delta = {}
        appended_entries = {}
        for name, (state, journal) in after.items():
            prior_state, prior_journal = before[name]
            self.assertEqual(_canonical(journal[:len(prior_journal)]), _canonical(prior_journal),
                             name)
            appended = journal[len(prior_journal):]
            journal_delta[name] = len(appended)
            if appended:
                appended_entries[name] = appended
            if name != "settlement":
                self.assertEqual(state, prior_state, name)

        view = host.machines["settlement"].view("settle-refund")
        claim = view["claim"]
        self.assertEqual(view["phase"], "CAPTURED")
        for record in (view, claim):
            self.assertIs(record["funds_executed"], False)
            self.assertIs(record["external_return_closed"], False)
        settlement = {key: view[key] for key in (
            "settlement_id", "phase", "currency", "funds_executed", "external_return_closed",
        )}
        settlement["claim"] = {key: claim[key] for key in (
            "currency", "refund_outstanding", "refund_accepted", "funds_executed", "external_return_closed",
        )}
        evidence = {
            "dispatches": dispatch.call_count,
            "hidden_receipt_ref": TARGET_RECEIPT if after_dispatch else None,
            "settlement": settlement,
            "journal_delta": journal_delta,
            "appended_journal_entries": appended_entries,
        }
        self.assertEqual(_canonical(evidence), _canonical(case["producer_evidence"]))
