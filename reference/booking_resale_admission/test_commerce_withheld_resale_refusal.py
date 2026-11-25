"""Replay a settlement-bound resale refusal at three delivery boundaries."""

import unittest
from copy import deepcopy
from unittest.mock import patch

from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost, FsmRejected
from integration_gate.schema import parse_envelope
from mock_gates import _canonical
from test_commerce_fixture_tuple_conformance import (
    BOOKING_BRANCH_RECEIPTS, RECEIPTS, ROOT, VECTORS, read, snapshot,
)
from test_commerce_journey_receipts import _decode, _pin
from test_commerce_transfer_lost_reply import GRANT_SELECTION, MissingReply, market_views

FIXTURE = "reference/booking_resale_admission/fixtures/commerce_withheld_resale_refusal_v1.json"
TARGET = "booking-resale/accept-A-before-commit"


def observe_resale_attempt(envelope, send):
    observation = {
        "operationId": envelope["operationId"],
        "idempotency_key": envelope["body"]["idempotency_key"],
        "receipt": None,
    }
    try:
        send(envelope)
    except MissingReply:
        return {**observation, "outcome": "UNKNOWN"}
    except FsmRejected as error:
        return {**observation, "outcome": "business-reject", "rejection_code": error.code}
    raise AssertionError("expected a refusal or a missing reply")


def bound_views(host, listing_id):
    views = market_views(host, listing_id)
    listing = host.machines["resale"].view(listing_id)
    settlement = host.machines["settlement"].view(listing["settlement_id"])
    views["listing"].update(amount=listing["amount"], settlement_gate=listing["settlement_gate"])
    views["settlement"] = {key: settlement[key] for key in ("settlement_id", "phase")}
    return views


class CommerceWithheldResaleRefusalTests(unittest.TestCase):
    def test_delivery_controls_the_caller_observation(self):
        fixture = _decode(read(FIXTURE))
        self.assertEqual(fixture["record_schema_version"], "kix-commerce-withheld-resale-refusal/1")
        self.assertIs(fixture["normative"], False)
        self.assertEqual([(case["id"], case["fault_point"]) for case in fixture["cases"]], [
            ("refusal-delivered", "none"),
            ("loss-before-dispatch", "before_dispatch"),
            ("refusal-withheld-after-dispatch", "after_dispatch"),
        ])
        self.assertEqual(fixture["recovery_lookup"], "NOT_BOUND")
        self.assertEqual([
            (case["request"]["kind"], case["expect"])
            for case in _decode(read(GRANT_SELECTION))["cases"]
            if case["id"] == "proposed-uncertain-operation-recovery"
        ], [("proposed_recovery", {"status": fixture["recovery_lookup"], "vector_id": None})])

        vector_raw = read(VECTORS)
        journey_raw = read(RECEIPTS)
        booking_raw = read(BOOKING_BRANCH_RECEIPTS)
        vector_pin = _pin(VECTORS, vector_raw)
        self.assertEqual(fixture["source_vector"], {**vector_pin, "id": TARGET})
        self.assertEqual(fixture["source_journey_receipts"], _pin(RECEIPTS, journey_raw))
        self.assertEqual(fixture["source_booking_branch_receipts"], _pin(BOOKING_BRANCH_RECEIPTS, booking_raw))
        booking = _decode(booking_raw)
        self.assertEqual(booking["fixture"], vector_pin)

        vectors = {vector["id"]: vector for vector in _decode(vector_raw)["vectors"]}
        journey_steps = _decode(journey_raw)["steps"]
        target = vectors[fixture["source_vector"]["id"]]
        self.assertEqual(target["input_index"], 22)
        golden_refusal = journey_steps[22]
        self.assertEqual(golden_refusal["id"], target["commerce_step"])
        self.assertEqual(golden_refusal["action"], target["envelope"]["action"])
        code = golden_refusal["rejection_code"]
        self.assertEqual(code, "SETTLEMENT_NOT_COMMITTED")
        self.assertEqual(target["expected"], {"kind": "business-reject", "code": code})
        self.assertEqual(len(target["setup"]), 15)
        self.assertEqual(target["setup"][-1], "booking-resale/bind-resale")

        setup = []
        booking_ids = set()
        for vector_id in target["setup"]:
            vector = vectors[vector_id]
            receipt_ref = vector["expected"].get("receipt_ref")
            if receipt_ref is None:
                booking_ids.add(vector_id)
                receipt = booking["receipts"][vector_id]
            else:
                index = vector["input_index"]
                self.assertEqual(receipt_ref, f"{RECEIPTS}#/steps/{index}/receipt")
                golden = journey_steps[index]
                self.assertEqual(golden["id"], vector["commerce_step"])
                self.assertEqual(golden["action"], vector["envelope"]["action"])
                receipt = golden["receipt"]
            setup.append((vector, receipt))
        self.assertEqual(booking_ids, {"booking-resale/order-A", "booking-resale/payment-A", "booking-resale/issue-A"})

        commands = load_catalogue(ROOT).commands
        observations = []
        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                observation = self.replay_case(case, setup, target["envelope"], commands)
                self.assertEqual(_canonical(observation), _canonical(case["expected_caller"]))
                self.assertIsNone(observation["receipt"])
                if case["fault_point"] == "none":
                    self.assertEqual(observation["outcome"], "business-reject")
                    self.assertEqual(observation["rejection_code"], code)
                else:
                    self.assertEqual(observation["outcome"], "UNKNOWN")
                    self.assertEqual(set(observation), {
                        "operationId", "idempotency_key", "receipt", "outcome", "attempts", "follow_up_calls",
                    })
                    observations.append(_canonical(observation))
        if len(observations) == 2:
            self.assertEqual(observations[0], observations[1])

    def replay_case(self, case, setup, envelope, commands):
        host = FsmHost()
        for vector, golden in setup:
            _, _, action, body = parse_envelope(vector["envelope"], commands)
            self.assertEqual(_canonical(host.call(action, body)), _canonical(golden), vector["id"])

        listing_id = envelope["body"]["listing_id"]
        views_before = bound_views(host, listing_id)
        before = snapshot(host)
        self.assertEqual(set(before), {"reservation", "resale", "settlement", "admission", "credit"})
        sent = []
        refusal_codes = []

        def transport(request):
            sent.append(deepcopy(request))
            if case["fault_point"] == "before_dispatch":
                raise MissingReply
            _, _, action, body = parse_envelope(request, commands)
            try:
                host.call(action, body)
            except FsmRejected as error:
                refusal_codes.append(error.code)
                if case["fault_point"] == "none":
                    raise
            else:
                raise AssertionError("producer unexpectedly accepted the transfer")
            # Raise outside the handler so the missing reply does not carry the refusal.
            raise MissingReply

        with patch.object(host, "call", wraps=host.call) as dispatch:
            observation = observe_resale_attempt(deepcopy(envelope), transport)
        self.assertEqual(_canonical(sent), _canonical([envelope]))
        observation.update(attempts=len(sent), follow_up_calls=len(sent) - 1)

        after = snapshot(host)
        self.assertEqual(_canonical(after), _canonical(before))
        views_after = bound_views(host, listing_id)
        self.assertEqual(_canonical(views_after), _canonical(views_before))
        evidence = {
            "dispatches": dispatch.call_count,
            "refusal_codes": refusal_codes,
            **views_after,
            "journal_delta": {name: len(after[name][1]) - len(journal) for name, (_, journal) in before.items()},
        }
        self.assertEqual(_canonical(evidence), _canonical(case["producer_evidence"]))
        return observation
