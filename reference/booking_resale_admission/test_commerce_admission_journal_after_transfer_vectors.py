"""Replay one accepted admission journal against two local ownership checkpoints."""
from __future__ import annotations

import copy
import hashlib
import unittest

import test_commerce_admission_replay_after_resale_vectors as prior
import test_commerce_journey_receipts as goldens
from admission_fsm import AdmissionError, AdmissionMachine
from integration_gate.fsm_host import FsmHost
from mock_gates import _canonical
from reservation_fsm import ReservationMachine

ROOT = goldens.ROOT
PACK = "admission_journal_after_transfer"
FIXTURE = f"reference/booking_resale_admission/fixtures/commerce_{PACK}_inputs_v1.json"
GOLDEN = ROOT / f"reference/booking_resale_admission/fixtures/commerce_{PACK}_receipts_v1.json"
CASE_CHECKPOINTS = (
    ("matching-ownership", 12, "buyer-1", 1),
    ("transferred-ownership", 15, "buyer-2", 2),
)
RIGHT_ID = "issue-1"
RESERVATION_ID = "reserve-1"
DIAGNOSTIC_KIND = "TEST_HARNESS_EVIDENCE"
SEMANTIC_STATUS = "HOLD_SEMANTIC"


def _bytes(value):
    return _canonical(value).encode("utf-8")


def _source_step(path, index):
    return f"{path}#/cases/0/steps/{index}"


def _resolve(documents, reference):
    path, pointer = reference.split("#/")
    node = documents[path]
    for part in pointer.split("/"):
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


class CommerceAdmissionJournalAfterTransferVectorTests(unittest.TestCase):
    def _assert_unconsumed(self, admission, *tickets):
        for machine in (admission, *tickets):
            self.assertEqual(sum(entry["op"] == "consume" for entry in machine.export_journal()), 0)
        self.assertIsNone(admission.view(RIGHT_ID)["consume_id"])
        for ticket in tickets:
            self.assertIsNone(ticket.view(RESERVATION_ID)["consume_id"])

    def _observe_case(self, case, index, checkpoint, steps, outcomes, ticket_bytes, journal_bytes):
        host = FsmHost()
        admission = host.machines["admission"]
        reservation = host.machines["reservation"]
        resale = host.machines["resale"]
        settlement = host.machines["settlement"]
        for position, (step, outcome) in enumerate(zip(steps[:checkpoint + 1], outcomes)):
            receipt = host.call(step["action"], copy.deepcopy(step["body"]))
            self.assertEqual(_bytes(receipt), _bytes(outcome["receipt"]), step["id"])
            if position == 7:
                self.assertEqual(reservation.view(RESERVATION_ID)["phase"], "ISSUED")
                self.assertEqual(_bytes(reservation.export_journal()), ticket_bytes)
            if position == 14:
                self.assertEqual(receipt["listing"]["phase"], "PAYMENT_NOTED")
                right = resale.view_right(RIGHT_ID)["right"]
                self.assertEqual((right["holder_role"], right["version"]), ("buyer-1", 1))

        if checkpoint == 15:
            self.assertEqual(receipt["evidence"]["transfer_id"], "transfer-1")
        self.assertEqual(_bytes(admission.export_journal()), journal_bytes)
        pinned = outcomes[checkpoint]["diagnostic_snapshot"]["machines"]["admission"]
        self.assertEqual(admission.canonical_state(), pinned["state"])
        self.assertEqual(admission.state_digest(), pinned["digest"])
        self.assertIs(admission.view(RIGHT_ID)["admission_expired"], True)

        ticket = ReservationMachine.restore(goldens._decode(ticket_bytes), settlement_source=settlement)
        self._assert_unconsumed(admission, reservation, ticket)
        before = {name: machine.canonical_state() for name, machine in host.machines.items()}
        try:
            restored = AdmissionMachine.restore(
                goldens._decode(journal_bytes), ticket_source=ticket,
                ownership_source=resale, settlement_source=settlement,
            )
        except AdmissionError as exc:
            restore_result = {"rejection_code": exc.code}
        else:
            self.assertEqual(restored.canonical_state(), pinned["state"])
            self.assertEqual(_bytes(restored.export_journal()), journal_bytes)
            self._assert_unconsumed(restored, ticket)
            restore_result = {"state_digest": restored.state_digest()}
        self._assert_unconsumed(admission, reservation, ticket)
        self.assertEqual({name: machine.canonical_state() for name, machine in host.machines.items()}, before)

        try:
            reconciliation = admission.reconcile(RIGHT_ID, idempotency_key=case["reconcile_idempotency_key"])
        except AdmissionError as exc:
            reconcile_result = {"rejection_code": exc.code}
        else:
            reconcile_result = {key: reconciliation[key] for key in (
                "matched", "duplicate", "state_digest", "entry_count",
            )}
        self._assert_unconsumed(admission, reservation, ticket)
        self.assertEqual({name: machine.canonical_state() for name, machine in host.machines.items()}, before)
        right = resale.view_right(RIGHT_ID)["right"]
        self.assertEqual(right["right_id"], RIGHT_ID)
        return {
            "id": case["id"],
            "steps": [{
                "id": steps[checkpoint]["id"],
                "action": steps[checkpoint]["action"],
                "input_ref": f"{FIXTURE}#/cases/{index}/steps/0/body",
                "receipt": receipt,
            }],
            "diagnostic_snapshot": {
                "restore": restore_result,
                "reconcile": reconcile_result,
                "holder_role": right["holder_role"],
                "version": right["version"],
                "new_consumptions": 0,
            },
        }

    def _validate_diagnostics(self, cases, digest):
        self.assertEqual([case["id"] for case in cases], [entry[0] for entry in CASE_CHECKPOINTS])
        for case, (_, _, holder, version) in zip(cases, CASE_CHECKPOINTS):
            diagnostic = case["diagnostic_snapshot"]
            self.assertEqual(_bytes(diagnostic["version"]), _bytes(version))
            self.assertEqual(diagnostic["holder_role"], holder)
            self.assertEqual(_bytes(diagnostic["new_consumptions"]), b"0")
            if case["id"] == "transferred-ownership":
                for name in ("restore", "reconcile"):
                    self.assertNotIn("matched", diagnostic[name], f"stale {name} cannot report matched")
                    self.assertEqual(diagnostic[name], {"rejection_code": "STALE_VERSION"})
            else:
                self.assertEqual(diagnostic["restore"], {"state_digest": digest})
                self.assertEqual(_bytes(diagnostic["reconcile"]), _bytes({
                    "matched": True, "duplicate": False, "state_digest": digest, "entry_count": 4,
                }))

    def _verify_receipts(self, raw):
        fixture_raw = goldens._read(FIXTURE)
        fixture = goldens._decode(fixture_raw)
        expected = goldens._decode(raw)
        self.assertEqual(_bytes(fixture), fixture_raw)
        self.assertEqual(_bytes(fixture["fixture_version"]), b"1")
        self.assertEqual(fixture["provenance"], "OFFLINE_CONFORMANCE_FIXTURE_ONLY")
        self.assertEqual(fixture["semantic_consumer_status"], SEMANTIC_STATUS)
        fixture_pin = goldens._pin(FIXTURE, fixture_raw)
        self.assertEqual(expected["fixture"], fixture_pin)
        source_bytes = {path: goldens._read(path) for path in (prior.FIXTURE, prior.GOLDEN_PATH)}
        sources = [goldens._pin(path, data) for path, data in source_bytes.items()]
        self.assertEqual(fixture["sources"], sources)
        self.assertEqual(expected["sources"], sources)

        documents = {path: goldens._decode(data) for path, data in source_bytes.items()}
        source_case = documents[prior.FIXTURE]["cases"][0]
        outcome_case = documents[prior.GOLDEN_PATH]["cases"][0]
        self.assertEqual(source_case["id"], prior.CASE)
        self.assertEqual(outcome_case["id"], prior.CASE)
        self.assertEqual(fixture["domain"], documents[prior.FIXTURE]["domain"])
        refs = fixture["source_step_refs"]
        self.assertEqual(refs, [_source_step(prior.FIXTURE, index) for index in range(16)])
        steps = [_resolve(documents, ref) for ref in refs]
        self.assertEqual(tuple(step["id"] for step in steps), prior.ORDER[:16])
        outcomes = outcome_case["steps"][:len(steps)]
        self.assertEqual(len(outcomes), len(steps))
        for step, outcome, ref in zip(steps, outcomes, refs):
            self.assertEqual((outcome["id"], outcome["action"]), (step["id"], step["action"]))
            self.assertEqual(outcome["input_ref"], ref + "/body")
            self.assertEqual(_bytes(_resolve(documents, outcome["input_ref"])), _bytes(step["body"]))

        snapshot = "/diagnostic_snapshot/machines/"
        self.assertEqual(fixture["journal_ref"], _source_step(prior.GOLDEN_PATH, 12) + snapshot + "admission/journal")
        journal = _resolve(documents, fixture["journal_ref"])
        self.assertEqual([entry["op"] for entry in journal],
                         ["set_clock", "adopt_issued", "authorize_admission", "set_clock"])
        journal_bytes = _bytes(journal)
        self.assertEqual(len(journal_bytes), 1009)
        self.assertEqual(hashlib.sha256(journal_bytes).hexdigest(), fixture["journal_sha256"])
        self.assertEqual(fixture["ticket_journal_ref"],
                         _source_step(prior.GOLDEN_PATH, 7) + snapshot + "reservation/journal")
        ticket_bytes = _bytes(_resolve(documents, fixture["ticket_journal_ref"]))

        self._validate_diagnostics(expected["cases"], outcomes[12]["diagnostic_snapshot"]["machines"]["admission"]["digest"])
        cases = fixture["cases"]
        self.assertEqual([case["id"] for case in cases], [entry[0] for entry in CASE_CHECKPOINTS])
        keys = {step["body"]["idempotency_key"] for step in steps}
        observed = []
        for index, (case, (_, checkpoint, _, _)) in enumerate(zip(cases, CASE_CHECKPOINTS)):
            step = steps[checkpoint]
            self.assertEqual(_bytes(case["steps"]), _bytes([{
                "id": step["id"], "action": step["action"], "body": step["body"],
                "source_step_ref": refs[checkpoint],
            }]))
            key = case["reconcile_idempotency_key"]
            self.assertNotIn(key, keys)
            keys.add(key)
            observed.append(self._observe_case(case, index, checkpoint, steps, outcomes, ticket_bytes, journal_bytes))
        self._validate_diagnostics(observed, outcomes[12]["diagnostic_snapshot"]["machines"]["admission"]["digest"])
        self.assertEqual(_bytes({
            "record_schema_version": "kix-commerce-admission-journal-after-transfer-receipts/1",
            "record_kind": "IN_PROCESS_MOCK_RECEIPT_VECTORS",
            "normative": False,
            "semantic_consumer_status": SEMANTIC_STATUS,
            "diagnostic_snapshot_kind": DIAGNOSTIC_KIND,
            "fixture": fixture_pin, "sources": sources, "cases": observed,
        }), raw, "complete canonical receipt bytes differ")

    def test_complete_output_bytes_and_references(self):
        self._verify_receipts(GOLDEN.read_bytes())

    def test_rejects_stale_case_labeled_matched(self):
        import test_commerce_companion_evidence_index as companion

        path = GOLDEN.relative_to(ROOT).as_posix()
        for name in ("restore", "reconcile"):
            with self.subTest(diagnostic=name):
                altered = goldens._decode(GOLDEN.read_bytes())
                altered["cases"][1]["diagnostic_snapshot"][name]["matched"] = True
                altered_raw = _bytes(altered)
                index = goldens._decode(goldens._read(companion.INDEX))
                pack = next(pack for pack in index["packs"] if pack["id"] == PACK)
                pack["output"] = goldens._pin(path, altered_raw)
                self.assertEqual(companion.validate_index(
                    index, read=lambda candidate: altered_raw if candidate == path else goldens._read(candidate),
                ), companion.TOTAL_ENTRIES)
                with self.assertRaisesRegex(AssertionError, f"stale {name} cannot report matched"):
                    self._verify_receipts(altered_raw)


if __name__ == "__main__":
    unittest.main()
