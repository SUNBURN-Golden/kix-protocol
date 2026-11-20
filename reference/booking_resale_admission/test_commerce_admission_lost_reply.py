"""Replay the same missing admission receipt across two producer outcomes."""

import hashlib
import json
import unittest
from copy import deepcopy
from unittest.mock import patch

import test_commerce_fixture_tuple_conformance as tuple_replay
from integration_gate.catalogue import load_catalogue
from integration_gate.fsm_host import FsmHost
from integration_gate.schema import parse_envelope
from mock_gates import _canonical

FIXTURE = "reference/booking_resale_admission/fixtures/commerce_admission_lost_reply_v1.json"


class MissingReply(Exception):
    """The transport did not deliver an admission receipt."""


def observe_consume(envelope, transport):
    try:
        transport(envelope)
    except MissingReply:
        return {
            "operationId": envelope["operationId"],
            "idempotency_key": envelope["body"]["idempotency_key"],
            "receipt": None,
            "outcome": "UNKNOWN",
        }
    raise AssertionError("expected the transport to signal a missing reply")


def admission_views(host):
    admission = host.machines["admission"].view("issue-B")
    reservation = host.machines["reservation"].view("reserve-B")
    return {
        "admission": {key: admission[key] for key in ("phase", "admission_id", "state", "version")},
        "reservation": {
            "phase": reservation["phase"],
            "admission_id": reservation["admission_id"],
            "state": reservation["right"]["state"],
            "version": reservation["right"]["version"],
        },
    }


class CommerceAdmissionLostReplyTests(unittest.TestCase):
    def test_loss_before_dispatch(self):
        self.replay_case("before_dispatch")

    def test_loss_after_dispatch(self):
        self.replay_case("after_dispatch")

    def replay_case(self, fault_point):
        fixture = json.loads(tuple_replay.read(FIXTURE))
        self.assertEqual(fixture["record_schema_version"], "kix-commerce-admission-lost-reply/1")
        self.assertEqual([(case["id"], case["fault_point"]) for case in fixture["cases"]], [
            ("loss-before-dispatch", "before_dispatch"),
            ("loss-after-dispatch", "after_dispatch"),
        ])
        cases = {case["fault_point"]: case["producer_evidence"] for case in fixture["cases"]}
        source = fixture["source_vector"]
        self.assertEqual(source["path"], tuple_replay.VECTORS)
        raw = tuple_replay.read(source["path"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), source["sha256"])
        self.assertEqual(source["id"], "booking-admission/consume-B")
        vectors = {row["id"]: row for row in json.loads(raw)["vectors"]}
        target = vectors[source["id"]]

        catalogue = load_catalogue(tuple_replay.ROOT)
        host = FsmHost()
        for vector_id in target["setup"]:
            _, _, action, body = parse_envelope(vectors[vector_id]["envelope"], catalogue.commands)
            receipt = host.call(action, body)
            self.assertIs(receipt["duplicate"], False, vector_id)
            self.assertEqual(receipt["applied"], catalogue.fsm["commands"][action]["op"], vector_id)
        before = tuple_replay.snapshot(host)
        self.assertEqual(admission_views(host), {
            name: cases["before_dispatch"][name] for name in ("admission", "reservation")
        })

        envelope = target["envelope"]
        calls = []

        def transport(request):
            calls.append(deepcopy(request))
            if fault_point == "after_dispatch":
                _, _, action, body = parse_envelope(request, catalogue.commands)
                path, pointer = target["expected"]["receipt_ref"].split("#", 1)
                self.assertEqual(pointer, "/steps/29/receipt")
                golden_step = json.loads(tuple_replay.read(path))["steps"][29]
                self.assertEqual(action, golden_step["action"])
                self.assertEqual(
                    _canonical(host.call(action, body)), _canonical(golden_step["receipt"])
                )
            raise MissingReply("admission receipt missing")

        with patch.object(host, "call", wraps=host.call) as dispatch:
            observation = observe_consume(deepcopy(envelope), transport)
        self.assertEqual(calls, [envelope])
        self.assertEqual(envelope["operationId"], "op-booking-admission-consume-B")
        self.assertEqual(envelope["body"]["idempotency_key"], "key-consume-B")
        observation["attempts"] = len(calls)
        observation["follow_up_calls"] = len(calls) - 1
        self.assertEqual(observation, fixture["expected_caller"])

        journal_delta = {}
        appended_entries = {}
        for name, (state, journal) in tuple_replay.snapshot(host).items():
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
        self.assertEqual({
            "dispatches": dispatch.call_count,
            **admission_views(host),
            "journal_delta": journal_delta,
            "appended_journal_entries": appended_entries,
        }, cases[fault_point])
