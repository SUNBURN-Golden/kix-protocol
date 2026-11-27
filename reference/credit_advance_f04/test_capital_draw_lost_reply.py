"""Replay two synthetic delivery histories for one matching F04 draw."""

import hashlib
from copy import deepcopy
from pathlib import Path
import unittest

from credit_fsm import CreditMachine
from settlement_credit_boundary_vectors import FIXTURE_PATH, PROVENANCE
from settlement_fsm import SettlementMachine
from test_capital_operation_replay_vectors import dispatch, load, same


ROOT = Path(__file__).resolve().parents[2]
PACK = FIXTURE_PATH.with_name("capital_draw_lost_reply_vectors_v1.json")
SOURCE = FIXTURE_PATH.with_name("capital_equal_gross_claim_binding_vectors_v1.json")
SOURCE_SHA256 = "dcce54255062d391faaf2d0ccc2f1f284fae8b0abbafe620162f33e25c740b34"
SOURCE_REF = SOURCE.relative_to(ROOT).as_posix() + "#"
MATCHING_REF = SOURCE_REF + "/cases/0"
CASES = (("loss-before-dispatch", False), ("loss-after-dispatch", True))


def submit_draw(step, send):
    """The fixture caller can see only its request and the transport reply."""
    reply = send(step)
    if reply is not None:
        raise AssertionError("the caller received a draw reply")
    return {"operation": step["operation"], **step["arguments"],
            "outcome": "UNKNOWN", "receipt": reply}


def replay_history(source, deliver_to_mock):
    original_journals = source["settlement_journals"]
    same(["stl-s1", "stl-s2"], sorted(original_journals))
    settlements = {key: SettlementMachine.restore(deepcopy(journal))
                   for key, journal in original_journals.items()}

    def settlement_journals():
        return {key: machine.export_journal() for key, machine in settlements.items()}

    same(original_journals, settlement_journals())
    credit = CreditMachine(settlement_source=settlements["stl-s2"])
    checkpoint = settlements["stl-s2"].view("stl-s2")
    same(["COMMITTED", "stl-s2"], [checkpoint["phase"], checkpoint["claim"]["claim_id"]])
    offer, approve, bind = source["setup_steps"]
    same(["s2-offer", "s2-approve", "s2-bind"], [step["step_id"] for step in (offer, approve, bind)])
    same(checkpoint["claim"], offer["arguments"]["face"])
    credit.offer(**offer["arguments"])
    credit.approve(**approve["arguments"])
    credit.bind_settlement(**bind["arguments"])
    same(original_journals, settlement_journals())

    # These are the exact draw_step and matching_case_ref fragments in the pack.
    draw = source["draw_step"]
    matching = source["cases"][0]
    same(["matching", "stl-s2"], [matching["case_id"], matching["settlement_id"]])
    advance_id = draw["arguments"]["advance_id"]

    def snapshot():
        return {"view": credit.view(advance_id), "journal": credit.export_journal()}

    before = snapshot()
    same(matching["before"], before)
    same(["offer", "approve", "bind_settlement"], [entry["op"] for entry in before["journal"]])
    submitted_steps, dispatch_results = [], []

    def send(step):
        submitted_steps.append(deepcopy(step))
        if deliver_to_mock:
            dispatch_results.append(dispatch(credit, step))
        return None

    caller = submit_draw(deepcopy(draw), send)
    caller["attempts"] = sum(step == draw for step in submitted_steps)
    caller["follow_up_calls"] = len(submitted_steps[1:])
    same([draw], submitted_steps)
    same({"operation": "draw", "advance_id": "adv-com", "draw_id": "drw-s2",
          "idempotency_key": "s2-draw", "attempts": 1, "outcome": "UNKNOWN",
          "receipt": None, "follow_up_calls": 0}, caller)

    after = snapshot()
    settlements_after = settlement_journals()
    same(original_journals, settlements_after)
    hidden_receipt_ref = None
    view = after["view"]
    exposure_fields = ("phase", "snapshot_frozen", "drawn_exposure", "repaid_exposure", "outstanding_exposure")
    if deliver_to_mock:
        same([matching["expected_result"]], dispatch_results)
        receipt = dispatch_results[0]["ok"]
        same([False, "draw", view], [receipt["duplicate"], receipt["applied"], receipt["credit"]])
        same(["DRAWN", True, 10_000, 0, 10_000], [view[key] for key in exposure_fields])
        same(matching["after"], after)
        same(before["journal"] + [{
            "op": "draw", "advance_id": advance_id,
            "idempotency_key": draw["arguments"]["idempotency_key"],
            "body": {"draw_id": draw["arguments"]["draw_id"]},
        }], after["journal"])
        hidden_receipt_ref = MATCHING_REF + "/expected_result/ok"
    else:
        same([], dispatch_results)
        same(["APPROVED", False, 0, 0, 0], [view[key] for key in exposure_fields])
        same(before, after)

    return caller, {"dispatches": len(dispatch_results), "hidden_receipt_ref": hidden_receipt_ref,
                    "credit_after": after, "settlement_journals": settlements_after}


class CapitalDrawLostReplyTests(unittest.TestCase):
    def test_draw_lost_reply_pair(self):
        pack = load(PACK)
        same(SOURCE_SHA256, hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        same({
            "fixture_version": "capital-draw-lost-reply/1",
            "fixture_kind": "SYNTHETIC_DRAW_LOST_REPLY",
            "synthetic_only": True,
            "provenance": PROVENANCE,
            "source_pins": [{"path": SOURCE.relative_to(ROOT).as_posix(), "sha256": SOURCE_SHA256}],
            "draw_step_ref": SOURCE_REF + "/draw_step",
            "matching_case_ref": MATCHING_REF,
        }, {key: value for key, value in pack.items() if key != "cases"})

        source = load(SOURCE)
        callers = []
        for (case_id, deliver_to_mock), expected in zip(CASES, pack["cases"], strict=True):
            with self.subTest(case=case_id):
                caller, evidence = replay_history(source, deliver_to_mock)
                same(expected, {"case_id": case_id, "expected_caller": caller, "producer_evidence": evidence})
                callers.append(caller)
        if len(callers) == len(CASES):
            same(*callers)
