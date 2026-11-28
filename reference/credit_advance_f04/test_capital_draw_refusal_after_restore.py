"""Compare a stored S1 draw refusal with restoration of its accepted journal."""

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
PACK = FIXTURE_PATH.with_name("capital_draw_refusal_after_restore_vectors_v1.json")
SCENARIO = "S1_captured_face_no_derivation"
CHECKPOINT = "s1-commit"
DIAGNOSTIC = "s1-draw-early"


class CapitalDrawRefusalAfterRestoreTests(unittest.TestCase):
    def test_draw_refusal_pair(self):
        pack = load(PACK)
        same(
            {
                "fixture_version": "capital-draw-refusal-after-restore/1",
                "fixture_kind": "SYNTHETIC_DRAW_REFUSAL_AFTER_RESTORE",
                "synthetic_only": True,
                "provenance": PROVENANCE,
                "source_pins": [
                    {"path": path.relative_to(ROOT).as_posix(),
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                    for path in (FIXTURE_PATH, VECTORS_PATH)
                ],
                "scenario_id": SCENARIO,
                "through_step_id": CHECKPOINT,
                "diagnostic_step_id": DIAGNOSTIC,
            },
            {key: value for key, value in pack.items() if key not in {"before", "cases"}},
        )

        scenario = next(s for s in load_fixture(FIXTURE_PATH)["scenarios"]
                        if s["scenario_id"] == SCENARIO)
        delivered = next(s for s in load_vectors(VECTORS_PATH)["scenarios"]
                         if s["scenario_id"] == SCENARIO)
        step_ids = [step["step_id"] for step in scenario["steps"]]
        stop = step_ids.index(CHECKPOINT) + 1
        self.assertEqual(step_ids[stop], "s1-draw-late")
        diagnostic_index = step_ids.index(DIAGNOSTIC)
        self.assertLess(diagnostic_index, stop - 1)
        early_draw = scenario["steps"][diagnostic_index]
        same({"step_id": DIAGNOSTIC, "target": "credit", "operation": "draw",
              "arguments": {"advance_id": "adv-cap", "draw_id": "drw-s1-early",
                            "idempotency_key": "s1-draw-early"}}, early_draw)

        prefix, settlement, original = replay_scenario_with_state(
            {**scenario, "steps": scenario["steps"][:stop]},
        )
        self.assertEqual(len(prefix), stop)
        for expected, actual in zip(delivered["steps"][:stop], prefix, strict=True):
            with self.subTest(step=expected["step_id"]):
                self.assertEqual(canonical(expected), canonical(actual))
        by_step = {step["step_id"]: step["result"] for step in prefix}

        def settlement_snapshot():
            return canonical([
                settlement.view("stl-s1"), settlement.export_journal(),
                settlement.canonical_state(), settlement.state_digest(),
            ])

        committed = settlement_snapshot()
        committed_view = settlement.view("stl-s1")
        same(by_step[CHECKPOINT]["ok"]["settlement"], committed_view)
        same(["COMMITTED", 97_000], [committed_view["phase"], committed_view["claim"]["confirmed_cash"]])

        advance_id = early_draw["arguments"]["advance_id"]
        view = original.view(advance_id)
        journal = original.export_journal()
        original_state = original.canonical_state()
        original_digest = original.state_digest()
        restored = CreditMachine.restore(journal, settlement_source=settlement)
        self.assertEqual(settlement_snapshot(), committed)
        self.assertIsNot(original, restored)

        same({"view": view, "journal": journal}, pack["before"])
        same(by_step["s1-view-approved"]["ok"], view)
        same(view, restored.view(advance_id))
        same(journal, restored.export_journal())
        self.assertEqual(original_state, restored.canonical_state())
        self.assertEqual(original_digest, restored.state_digest())
        self.assertEqual([entry["op"] for entry in journal], ["offer", "approve", "bind_settlement"])
        exposure_fields = ("drawn_exposure", "repaid_exposure", "outstanding_exposure")
        same(["APPROVED", None, 0, 0, 0],
             [view["phase"], view["draw_id"], *(view[field] for field in exposure_fields)])

        captured = by_step["s1-settlement-captured"]["ok"]["claim"]
        same([0, 100_000], [captured["confirmed_cash"], captured["receivable_open"]])
        same(captured, journal[0]["body"]["face"])

        original_result = dispatch(original, early_draw)
        self.assertEqual(settlement_snapshot(), committed)
        same({"error": {"type": "CreditError", "code": "SETTLEMENT_NOT_COMMITTED"}}, original_result)
        same(by_step[DIAGNOSTIC], original_result)

        restored_result = dispatch(restored, early_draw)
        self.assertEqual(settlement_snapshot(), committed)
        receipt = restored_result["ok"]
        same([False, "draw"], [receipt["duplicate"], receipt["applied"]])
        drawn = restored.view(advance_id)
        same(drawn, receipt["credit"])
        same(["DRAWN", "drw-s1-early", True, 0, 10_000, 0, 10_000],
             [drawn["phase"], drawn["draw_id"], drawn["snapshot_frozen"],
              drawn["confirmed_cash_on_face"], *(drawn[field] for field in exposure_fields)])
        same([True, False, False, False],
             [drawn["mock_settlement_commit_observed"], drawn["funds_executed"],
              drawn["bank_debit_observed"], drawn["economic_finality_claimed"]])

        appended = [{"op": "draw", "advance_id": advance_id, "idempotency_key": DIAGNOSTIC,
                     "body": {"draw_id": early_draw["arguments"]["draw_id"]}}]
        same(journal + appended, restored.export_journal())
        same(journal, original.export_journal())
        same(view, original.view(advance_id))
        self.assertEqual(original.canonical_state(), original_state)
        self.assertEqual(original.state_digest(), original_digest)
        same([
            {"case_id": "original", "expected_result": original_result,
             "after_view": original.view(advance_id), "journal_append": []},
            {"case_id": "restored", "expected_result": restored_result,
             "after_view": drawn, "journal_append": appended},
        ], pack["cases"])
