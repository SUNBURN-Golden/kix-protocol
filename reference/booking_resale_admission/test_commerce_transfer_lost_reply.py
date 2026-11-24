"""Replay one lost resale transfer reply across two mock producer outcomes."""

import unittest
from copy import deepcopy
from unittest.mock import patch

from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost
from integration_gate.schema import parse_envelope
from mock_gates import _canonical
from test_commerce_fixture_tuple_conformance import MARKET_RECEIPTS, ROOT, VECTORS, read, snapshot
from test_commerce_journey_receipts import _decode, _pin

FIXTURE = "reference/booking_resale_admission/fixtures/commerce_transfer_lost_reply_v1.json"
GRANT_SELECTION = "sdk/conformance/vectors/producer-grant-selection.vectors.json"
TARGET = "resale-market/market-accept"
PAYMENT = "resale-market/market-pay"


class MissingReply(Exception):
    """The transport delivered no receipt."""


def observe_transfer(envelope, send):
    try:
        send(envelope)
    except MissingReply:
        return {
            "operationId": envelope["operationId"],
            "idempotency_key": envelope["body"]["idempotency_key"],
            "receipt": None,
            "outcome": "UNKNOWN",
        }
    raise AssertionError("expected a missing reply")


def market_views(host, listing_id):
    resale = host.machines["resale"]
    listing = resale.view(listing_id)
    right = resale.view_right(listing["right_id"])["right"]
    return {
        "listing": {key: listing[key] for key in (
            "listing_id", "phase", "payment_ref", "ownership_transferred",
        )},
        "right": {key: right[key] for key in ("right_id", "holder_role", "version")},
    }


class CommerceTransferLostReplyTests(unittest.TestCase):
    def test_both_losses_have_the_same_caller_observation(self):
        fixture = _decode(read(FIXTURE))
        self.assertEqual(fixture["record_schema_version"], "kix-commerce-transfer-lost-reply/1")
        self.assertIs(fixture["normative"], False)
        self.assertEqual([(case["id"], case["fault_point"]) for case in fixture["cases"]], [
            ("loss-before-dispatch", "before_dispatch"),
            ("loss-after-dispatch", "after_dispatch"),
        ])
        self.assertEqual(fixture["recovery_lookup"], "NOT_BOUND")
        self.assertEqual([
            case["expect"] for case in _decode(read(GRANT_SELECTION))["cases"]
            if case["request"]["kind"] == "proposed_recovery"
        ], [{"status": fixture["recovery_lookup"], "vector_id": None}])

        corpus_raw = read(VECTORS)
        corpus_pin = _pin(VECTORS, corpus_raw)
        self.assertEqual(fixture["source_vector"], {**corpus_pin, "id": TARGET})
        market_raw = read(MARKET_RECEIPTS)
        self.assertEqual(fixture["source_market_receipts"], _pin(MARKET_RECEIPTS, market_raw))
        market = _decode(market_raw)
        self.assertEqual(market["fixture"], corpus_pin)
        vectors = {vector["id"]: vector for vector in _decode(corpus_raw)["vectors"]}
        self.assertEqual(vectors[TARGET]["setup"][-1], PAYMENT)

        catalogue = load_catalogue(ROOT)
        paid = fixture["cases"][0]["producer_evidence"]
        paid_views = {name: paid[name] for name in ("listing", "right")}
        for case in fixture["cases"]:
            with self.subTest(fault_point=case["fault_point"]):
                self.replay_case(case, vectors, market["receipts"], catalogue,
                                 paid_views, fixture["expected_caller"])

    def replay_case(self, case, vectors, goldens, catalogue, paid_views, expected_caller):
        host = FsmHost()
        target = vectors[TARGET]
        for vector_id in target["setup"]:
            _, _, action, body = parse_envelope(vectors[vector_id]["envelope"], catalogue.commands)
            self.assertEqual(_canonical(host.call(action, body)), _canonical(goldens[vector_id]),
                             vector_id)

        envelope = target["envelope"]
        listing_id = envelope["body"]["listing_id"]
        self.assertEqual(market_views(host, listing_id), paid_views)
        before = snapshot(host)
        sent = []
        hidden_receipts = []

        def transport(request):
            sent.append(deepcopy(request))
            if case["fault_point"] == "after_dispatch":
                _, _, action, body = parse_envelope(request, catalogue.commands)
                hidden_receipts.append(host.call(action, body))
            raise MissingReply

        with patch.object(host, "call", wraps=host.call) as dispatch:
            observation = observe_transfer(deepcopy(envelope), transport)
        self.assertEqual(sent, [envelope])
        observation["attempts"] = len(sent)
        observation["follow_up_calls"] = len(sent) - 1
        self.assertEqual(_canonical(observation), _canonical(expected_caller))

        receipt_id = None
        if hidden_receipts:
            self.assertEqual([_canonical(receipt) for receipt in hidden_receipts],
                             [_canonical(goldens[TARGET])])
            receipt_id = TARGET

        journal_delta = {}
        appended_entries = {}
        for name, (state, journal) in snapshot(host).items():
            prior_state, prior_journal = before[name]
            self.assertEqual(journal[:len(prior_journal)], prior_journal, name)
            appended = journal[len(prior_journal):]
            journal_delta[name] = len(appended)
            if appended:
                appended_entries[name] = [
                    {key: entry[key] for key in ("op", "subject_id", "idempotency_key")}
                    for entry in appended
                ]
            else:
                self.assertEqual(state, prior_state, name)
        evidence = {
            "dispatches": dispatch.call_count,
            "hidden_receipt_id": receipt_id,
            **market_views(host, listing_id),
            "journal_delta": journal_delta,
            "appended_journal_entries": appended_entries,
        }
        self.assertEqual(_canonical(evidence), _canonical(case["producer_evidence"]))
