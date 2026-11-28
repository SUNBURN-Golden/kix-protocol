"""Compare F04 draws bound to distinct committed claims of equal gross."""

import hashlib
from pathlib import Path
import unittest

from credit_fsm import CreditMachine
from settlement_credit_boundary_vectors import (
    FIXTURE_PATH,
    PROVENANCE,
    VECTORS_PATH,
    canonical,
    load_fixture,
    load_vectors,
    replay_scenario_with_state,
)
from test_capital_operation_replay_vectors import dispatch, load, same


ROOT = Path(__file__).resolve().parents[2]
PACK = FIXTURE_PATH.with_name("capital_equal_gross_claim_binding_vectors_v1.json")
CHECKPOINTS = (
    ("stl-s1", "S1_captured_face_no_derivation", "s1-commit", ("settlement",)),
    ("stl-s2", "S2_committed_face_no_derivation", "s2-settlement-committed", ()),
)
SETUP_STEPS = ("s2-offer", "s2-approve", "s2-bind")
EXPOSURE_FIELDS = ("drawn_exposure", "repaid_exposure", "outstanding_exposure")


class CapitalEqualGrossClaimBindingTests(unittest.TestCase):
    def test_equal_gross_claim_binding(self):
        pack = load(PACK)
        replay_fields = {"checkpoints", "setup_steps", "draw_step", "settlement_journals", "cases"}
        same({
            "fixture_version": "capital-equal-gross-claim-binding/1",
            "fixture_kind": "SYNTHETIC_EQUAL_GROSS_CLAIM_BINDING",
            "synthetic_only": True,
            "provenance": PROVENANCE,
            "source_pins": [
                {"path": path.relative_to(ROOT).as_posix(),
                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for path in (FIXTURE_PATH, VECTORS_PATH)
            ],
        }, {key: value for key, value in pack.items() if key not in replay_fields})

        inputs = load_fixture(FIXTURE_PATH)["scenarios"]
        results = load_vectors(VECTORS_PATH)["scenarios"]
        results_path = VECTORS_PATH.relative_to(ROOT).as_posix()
        settlements, committed_views = {}, {}
        checkpoints = []
        for index, (settlement_id, scenario_id, step_id, suffix) in enumerate(CHECKPOINTS):
            with self.subTest(checkpoint=step_id):
                scenario, delivered = inputs[index], results[index]
                self.assertEqual(scenario["scenario_id"], scenario_id)
                self.assertEqual(delivered["scenario_id"], scenario_id)
                stop = next(i for i, step in enumerate(scenario["steps"]) if step["step_id"] == step_id) + 1
                prefix, settlement, _ = replay_scenario_with_state(
                    {**scenario, "steps": scenario["steps"][:stop]},
                )
                self.assertEqual(canonical(delivered["steps"][:stop]), canonical(prefix))
                expected_view = delivered["steps"][stop - 1]["result"]["ok"]
                view_ref = f"{results_path}#/scenarios/{index}/steps/{stop - 1}/result/ok"
                for field in suffix:
                    expected_view = expected_view[field]
                    view_ref += "/" + field
                view = settlement.view(settlement_id)
                same(expected_view, view)
                same([settlement_id, "COMMITTED", "KRW", 100_000],
                     [view[key] for key in ("settlement_id", "phase", "currency", "gross")])
                same([settlement_id, "KRW", 100_000],
                     [view["claim"][key] for key in ("claim_id", "currency", "gross")])
                settlements[settlement_id] = settlement
                committed_views[settlement_id] = view
                checkpoints.append({"scenario_id": scenario_id, "through_step_id": step_id,
                                    "view_ref": view_ref})

        same(checkpoints, pack["checkpoints"])
        self.assertNotEqual(committed_views["stl-s1"]["claim"]["claim_id"],
                            committed_views["stl-s2"]["claim"]["claim_id"])
        s2_steps = {step["step_id"]: step for step in inputs[1]["steps"]}
        s2_results = {step["step_id"]: step["result"] for step in results[1]["steps"]}
        offer, approve, bind = pack["setup_steps"]
        same([s2_steps[key] for key in SETUP_STEPS], pack["setup_steps"])
        draw = pack["draw_step"]
        same(s2_steps["s2-draw"], draw)
        advance_id = draw["arguments"]["advance_id"]
        face = committed_views["stl-s2"]["claim"]
        same(face, offer["arguments"]["face"])
        same(10_000, offer["arguments"]["amount"])

        def settlement_journals():
            return {key: machine.export_journal() for key, machine in settlements.items()}

        def assert_settlements_unchanged():
            same(pack["settlement_journals"], settlement_journals())
            same(committed_views, {key: machine.view(key) for key, machine in settlements.items()})

        def snapshot(credit):
            return {"view": credit.view(advance_id), "journal": credit.export_journal()}

        assert_settlements_unchanged()
        branches = []
        for case_id, settlement_id in (("matching", "stl-s2"), ("crossed", "stl-s1")):
            credit = CreditMachine(settlement_source=settlements[settlement_id])
            same(s2_results["s2-offer"], {"ok": credit.offer(**offer["arguments"])})
            same(s2_results["s2-approve"], {"ok": credit.approve(**approve["arguments"])})
            bound = credit.bind_settlement(**{**bind["arguments"], "settlement_id": settlement_id})
            same([False, "bind_settlement"], [bound["duplicate"], bound["applied"]])
            before = snapshot(credit)
            same(bound["credit"], before["view"])
            same(["offer", "approve", "bind_settlement"], [entry["op"] for entry in before["journal"]])
            same(face, before["journal"][0]["body"]["face"])
            view = before["view"]
            same(["APPROVED", settlement_id, None, None, False, 0, 0, 0],
                 [view[key] for key in ("phase", "settlement_id", "draw_id", "note_status",
                                        "snapshot_frozen", *EXPOSURE_FIELDS)])
            branches.append((case_id, settlement_id, credit, before))

        assert_settlements_unchanged()
        cases = []
        for case_id, settlement_id, credit, before in branches:
            with self.subTest(case=case_id):
                result = dispatch(credit, draw)
                assert_settlements_unchanged()
                after = snapshot(credit)
                same(face, after["journal"][0]["body"]["face"])
                if case_id == "matching":
                    same(s2_results["s2-draw"], result)
                    receipt = result["ok"]
                    same([False, "draw"], [receipt["duplicate"], receipt["applied"]])
                    view = after["view"]
                    same(receipt["credit"], view)
                    draw_id = draw["arguments"]["draw_id"]
                    same(["DRAWN", draw_id, "NOTED", True, 10_000, 0, 10_000],
                         [view[key] for key in ("phase", "draw_id", "note_status",
                                                "snapshot_frozen", *EXPOSURE_FIELDS)])
                    same(before["journal"] + [{
                        "op": "draw", "advance_id": advance_id,
                        "idempotency_key": draw["arguments"]["idempotency_key"],
                        "body": {"draw_id": draw_id},
                    }], after["journal"])
                else:
                    same({"error": {"type": "CreditError", "code": "SETTLEMENT_BINDING_CONFLICT"}}, result)
                    same(before, after)
                cases.append({"case_id": case_id, "settlement_id": settlement_id, "before": before,
                              "expected_result": result, "after": after})
        same(pack["cases"], cases)
