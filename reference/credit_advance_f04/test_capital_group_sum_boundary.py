"""Replay the synthetic F04 group sum above the per-view amount ceiling."""

from copy import deepcopy
from pathlib import Path
import unittest

from credit_fixture import decode_json, exact_fields
from credit_fsm import CreditMachine
from mock_settlement import MockSettlement
from shared_exposure import SharedExposureError, canonical, observe_shared_exposure
from test_shared_exposure_contract import POLICY, _draw


ROOT = Path(__file__).resolve().parents[2]
PACK = "reference/credit_advance_f04/fixtures/capital_group_sum_boundary_vectors_v1.json"
CEILING = 1_000_000_000_000
TOTAL = 1_000_000_000_001


class CapitalGroupSumBoundaryTests(unittest.TestCase):
    def test_group_sum_boundary(self):
        raw = (ROOT / PACK).read_bytes()
        pack = decode_json(raw.decode("utf-8"))
        exact_fields(pack, {
            "fixture_version", "fixture_kind", "synthetic_only", "contract",
            "group_id", "policy", "debtor_role", "beneficiary_role", "setup",
            "credit_views", "cases",
        }, "group sum boundary pack")
        self.assertEqual(canonical(pack), raw)
        self.assertEqual(pack["fixture_version"], "capital-group-sum-boundary/1")
        self.assertEqual(pack["fixture_kind"], "SYNTHETIC_GROUP_SUM_BOUNDARY")
        self.assertIs(pack["synthetic_only"], True)
        self.assertEqual(pack["contract"], "docs/contracts/CREDIT_ADVANCE_F04.md#7.12")
        self.assertEqual(pack["group_id"], "pool-group-sum")
        self.assertEqual(canonical(pack["policy"]), canonical(POLICY))
        self.assertEqual(pack["debtor_role"], "fixture-debtor")
        self.assertEqual(pack["beneficiary_role"], "fixture-lender")

        settlement = MockSettlement()
        machine = CreditMachine()
        setup = pack["setup"]
        for row, amount in zip(setup, (CEILING, 1), strict=True):
            exact_fields(row, {"claim_id", "trade_id", "advance_id", "gross", "amount"},
                         "group sum setup row")
            self.assertEqual(canonical([row["gross"], row["amount"]]),
                             canonical([amount, amount]))
            settlement.recognize_claim(
                row["claim_id"], trade_id=row["trade_id"], gross=row["gross"],
                debtor_role=pack["debtor_role"], policy=pack["policy"],
            )
            _draw(machine, row["advance_id"], settlement.view(row["claim_id"]), row["amount"])
        for key in ("claim_id", "trade_id", "advance_id"):
            self.assertNotEqual(setup[0][key], setup[1][key], key)

        views = [machine.view(row["advance_id"]) for row in setup]
        self.assertEqual(canonical(views), canonical(pack["credit_views"]))
        for view, row in zip(views, setup, strict=True):
            for key in ("claim_id", "trade_id", "advance_id", "amount"):
                self.assertEqual(view[key], row[key], key)
            self.assertEqual(view["phase"], "DRAWN")
            self.assertIs(view["snapshot_frozen"], True)
            self.assertEqual(view["provenance"], "MOCK_CREDIT_F04_ONLY")
            self.assertEqual(view["exposure_ledger"], "MOCK_EXPOSURE")
            self.assertEqual(view["currency"], "KRW")

        claims = [{
            "claim_id": row["claim_id"],
            "trade_id": row["trade_id"],
            "advance_ids": [row["advance_id"]],
            "open_face": row["gross"],
            "reserved_open": row["amount"],
            "residual_unreserved": 0,
        } for row in sorted(setup, key=lambda row: row["claim_id"])]
        observable = {
            "group_drawn_exposure": TOTAL,
            "group_outstanding_exposure": TOTAL,
            "group_open_face": TOTAL,
            "group_reserved_open": TOTAL,
            "group_repaid_exposure": 0,
            "group_residual_unreserved": 0,
        }
        view_refs = [f"{PACK}#/credit_views/{i}" for i in range(len(views))]
        cases = (
            ("at_total", TOTAL, True),
            ("one_below", CEILING, False),
            ("single_view_overflow", TOTAL, None),
        )
        for case, (case_id, limit, within_limit) in zip(pack["cases"], cases, strict=True):
            with self.subTest(case=case_id):
                overflow = case_id == "single_view_overflow"
                fields = {"case_id", "view_refs", "limit", "expected_result"}
                if overflow:
                    fields.add("overrides")
                exact_fields(case, fields, case_id)
                self.assertEqual(case["case_id"], case_id)
                self.assertIs(type(case["limit"]), int)
                self.assertEqual(case["limit"], limit)
                self.assertEqual(case["view_refs"], view_refs[:1] if overflow else view_refs)

                inputs = views
                if overflow:
                    overrides = dict.fromkeys((
                        "amount", "open_face", "reserved_open", "drawn_exposure",
                        "outstanding_exposure",
                    ), TOTAL)
                    self.assertEqual(canonical(case["overrides"]), canonical(overrides))
                    detached = deepcopy(views[0])
                    detached.update(case["overrides"])
                    self.assertEqual(detached["outstanding_exposure"],
                                     detached["drawn_exposure"] - detached["repaid_exposure"])
                    self.assertEqual(detached["residual_unreserved"],
                                     detached["open_face"] - detached["reserved_open"])
                    inputs = [detached]

                args = (pack["group_id"], inputs)
                kwargs = {"limit": case["limit"]}
                before = canonical([args, kwargs])
                try:
                    result = {"ok": observe_shared_exposure(*args, **kwargs)}
                except SharedExposureError as error:
                    result = {"error": {"type": type(error).__name__, "code": error.code}}
                finally:
                    self.assertEqual(canonical([args, kwargs]), before)
                self.assertEqual(canonical(result), canonical(case["expected_result"]))
                if overflow:
                    self.assertEqual(result, {
                        "error": {"type": "SharedExposureError", "code": "VIEW_INVALID"},
                    })
                    continue

                record = result["ok"]
                self.assertEqual(record["group_id"], pack["group_id"])
                self.assertEqual(canonical(record["limit"]), canonical(limit))
                self.assertEqual(canonical([record["advance_count"], record["claim_count"]]),
                                 canonical([2, 2]))
                self.assertEqual(canonical(record["claims"]), canonical(claims))
                self.assertEqual(canonical(record["observable"]), canonical(observable))
                self.assertIs(record["within_limit"], within_limit)
                self.assertIs(record["fail_closed"], True)
                for flag in ("authorizes_exposure", "mutates_state", "legal_debtor_bound"):
                    self.assertIs(record[flag], False, flag)
                self.assertEqual(record["refund_component"], "NOT_BOUND")
                self.assertEqual(record["mapping"], {
                    "code": "SHARED_EXPOSURE_NOT_BOUND",
                    "contract_status": "NOT_BOUND",
                    "repair": "NONE",
                })

        self.assertEqual(canonical(views), canonical(pack["credit_views"]))
        self.assertEqual(canonical([machine.view(row["advance_id"]) for row in setup]),
                         canonical(pack["credit_views"]))
