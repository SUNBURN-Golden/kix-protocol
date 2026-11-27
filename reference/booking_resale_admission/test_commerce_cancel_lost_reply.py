"""Replay a missing cancellation reply on two fresh in-process hosts."""

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
from test_commerce_issuance_lost_reply import MissingReply, reservation_projection
from test_commerce_journey_receipts import _decode, _pin

FIXTURE = "reference/booking_resale_admission/fixtures/commerce_cancel_lost_reply_v1.json"
TARGET = "booking-refund/cancel-C"
SETUP = [
    "booking-refund/reservation-clock",
    "booking-refund/register-show",
    "booking-refund/reserve-C",
    "booking-refund/order-C",
]


def observe_cancellation(envelope, send):
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


class CommerceCancelLostReplyTests(unittest.TestCase):
    def test_both_losses_have_the_same_caller_observation(self):
        fixture = _decode(read(FIXTURE))
        self.assertEqual(fixture["record_schema_version"], "kix-commerce-cancel-lost-reply/1")
        self.assertIs(fixture["normative"], False)
        self.assertEqual(fixture["recovery_lookup"], "NOT_BOUND")
        self.assertEqual([(case["id"], case["fault_point"]) for case in fixture["cases"]], [
            ("loss-before-dispatch", "before_dispatch"),
            ("loss-after-dispatch", "after_dispatch"),
        ])

        corpus_raw = read(VECTORS)
        corpus_pin = _pin(VECTORS, corpus_raw)
        self.assertEqual(fixture["source_vector"], {**corpus_pin, "id": TARGET})
        booking_raw = read(BOOKING_BRANCH_RECEIPTS)
        self.assertEqual(fixture["source_booking_branch_receipts"],
                         _pin(BOOKING_BRANCH_RECEIPTS, booking_raw))
        booking = _decode(booking_raw)
        self.assertEqual(booking["fixture"], corpus_pin)
        journey_raw = read(RECEIPTS)
        self.assertEqual(fixture["source_journey_receipts"], _pin(RECEIPTS, journey_raw))

        vectors = {vector["id"]: vector for vector in _decode(corpus_raw)["vectors"]}
        target = vectors[TARGET]
        self.assertEqual(target["setup"], SETUP)
        self.assertEqual(target["envelope"]["action"], "reservation_cancel")
        goldens = dict(booking["receipts"])
        journey_steps = _decode(journey_raw)["steps"]
        for index, vector_id in enumerate(SETUP[:2]):
            vector = vectors[vector_id]
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
            observation = observe_cancellation(deepcopy(envelope), transport)
        self.assertEqual(_canonical(sent), _canonical([envelope]))
        observation.update(attempts=len(sent), follow_up_calls=len(sent) - 1)
        self.assertEqual(_canonical(observation), _canonical(expected_caller))

        after = snapshot(host)
        receipt_id = None
        expected_appends = {}
        if after_dispatch:
            self.assertEqual(
                [_canonical(receipt).encode("utf-8") for receipt in hidden_receipts],
                [_canonical(goldens[TARGET]).encode("utf-8")],
            )
            receipt_id = TARGET
            expected_appends["reservation"] = [{
                "op": "cancel",
                "subject_id": "reserve-C",
                "idempotency_key": envelope["body"]["idempotency_key"],
                "body": {},
            }]
        else:
            self.assertEqual(hidden_receipts, [])
            self.assertEqual(after, before)
        self.assertEqual(dispatch.call_count, int(after_dispatch))

        reservation = host.machines["reservation"]
        view = reservation.view("reserve-C")
        self.assertEqual(view["phase"], "CANCELLED" if after_dispatch else "CONFIRMED")
        self.assertEqual(view["show_id"], "show-journey")
        self.assertEqual(view["slot"], 2)
        slot_state, slot_owner = ("FREE", None) if after_dispatch else ("RESERVED", "reserve-C")
        self.assertEqual((view["slot_state"], view["slot_reservation_id"]), (slot_state, slot_owner))
        for field in ("payment_ref", "issuance_id", "right", "slot_right_id"):
            self.assertIsNone(view[field], field)
        show = reservation.view_show("show-journey")["show"]
        self.assertEqual(show["payment_ref_count"], 0)
        self.assertEqual([slot for slot in show["slots"] if slot["slot"] == 2], [{
            "slot": 2, "state": slot_state, "reservation_id": slot_owner, "right_id": None,
        }])
        settlement_state, settlement_journal = after["settlement"]
        self.assertEqual(_decode(settlement_state.encode("utf-8"))["cases"], [])
        self.assertEqual(settlement_journal, [])

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
            if name != "reservation":
                self.assertEqual(state, prior_state, name)
        self.assertEqual(_canonical(appended_entries), _canonical(expected_appends))
        evidence = {
            "dispatches": dispatch.call_count,
            "hidden_receipt_id": receipt_id,
            "reservation": {
                **reservation_projection(view),
                "show_id": view["show_id"],
                "slot_reservation_id": view["slot_reservation_id"],
            },
            "journal_delta": journal_delta,
            "appended_journal_entries": appended_entries,
        }
        self.assertEqual(_canonical(evidence), _canonical(case["producer_evidence"]))
