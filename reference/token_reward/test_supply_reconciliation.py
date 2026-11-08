"""Interface gaps only; SupplyTests and TL-4 own model arithmetic coverage."""

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from reward_fixture import FixtureError, decode_json
from supply_reconciliation import NOTICE, dispatch_request
from token_reward_model import PROVENANCE, TokenRewardError, reconcile_supply, supply_report


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture(name):
    return decode_json((FIXTURES / f"supply_{name}.json").read_text(encoding="utf-8"))


def direct(request):
    args = request["arguments"]
    if request["operation"] == "supply_report":
        return supply_report(args["events"])
    return reconcile_supply(args["offchain"], args["chain_supply"])


class SupplyDispatchTests(unittest.TestCase):
    def test_complete_result_parity_forwarding_and_input_preservation(self):
        for name in ("report", "match", "holder_burn", "unexplained",
                     "unapproved_mint", "unapproved_path", "both_causes"):
            with self.subTest(name=name):
                value = fixture(name)
                before = deepcopy(value)
                expected = direct(value)
                with patch("supply_reconciliation.supply_report", wraps=supply_report) as report, \
                        patch("supply_reconciliation.reconcile_supply", wraps=reconcile_supply) as reconcile:
                    output = dispatch_request(value)
                args = value["arguments"]
                if value["operation"] == "supply_report":
                    report.assert_called_once_with(args["events"])
                    self.assertIs(report.call_args.args[0], args["events"])
                    reconcile.assert_not_called()
                else:
                    reconcile.assert_called_once_with(args["offchain"], args["chain_supply"])
                    self.assertIs(reconcile.call_args.args[0], args["offchain"])
                    report.assert_not_called()
                self.assertEqual(value, before)
                self.assertEqual(output, {"operation": value["operation"], "provenance": PROVENANCE,
                                         "evidence_class": "CALCULATION_ONLY", "notice": NOTICE,
                                         "result": expected})
                self.assertEqual(output["result"]["figure"], "SYNTHETIC_SUPPLY_FIGURE")
                if name == "both_causes":
                    # Characterization only: TL4_THREAT_MODEL §6.B leaves precedence undefined.
                    self.assertEqual(output["result"]["alarm"], "UNAPPROVED_PATH")
                    self.assertIs(output["result"]["stop_payout"], True)

    def test_domain_exceptions_forward_unchanged_and_never_repair_reports(self):
        duplicate_report = fixture("match")
        duplicate_report["arguments"]["offchain"]["events"].append(
            deepcopy(duplicate_report["arguments"]["offchain"]["events"][0]))
        missing_total = fixture("match")
        del missing_total["arguments"]["offchain"]["minted_total"]
        cases = [(fixture("duplicate"), "SUPPLY_EVENT_DUPLICATE"),
                 (duplicate_report, "SUPPLY_EVENT_DUPLICATE"),
                 (fixture("tampered"), "SUPPLY_REPORT_MISMATCH"),
                 (missing_total, "SUPPLY_REPORT_MISMATCH")]
        for value, code in cases:
            with self.subTest(code=code, value=value):
                before = deepcopy(value)
                with self.assertRaises(TokenRewardError) as expected:
                    direct(value)
                with patch("supply_reconciliation.supply_report", wraps=supply_report) as report, \
                        patch("supply_reconciliation.reconcile_supply", wraps=reconcile_supply) as reconcile:
                    with self.assertRaises(TokenRewardError) as caught:
                        dispatch_request(value)
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(caught.exception.code, expected.exception.code)
                self.assertEqual(value, before)
                if value["operation"] == "reconcile_supply":
                    report.assert_not_called()
                    reconcile.assert_called_once_with(value["arguments"]["offchain"],
                                                      value["arguments"]["chain_supply"])
                    self.assertIs(reconcile.call_args.args[0], value["arguments"]["offchain"])
        error = TokenRewardError("SUPPLY_REPORT_MISMATCH")
        with patch("supply_reconciliation.reconcile_supply", side_effect=error):
            with self.assertRaises(TokenRewardError) as caught:
                dispatch_request(fixture("match"))
        self.assertIs(caught.exception, error)

    def test_nested_metadata_is_delegated_without_normalization(self):
        # The model checks six totals, not every metadata field; no authentication claim.
        value = fixture("match")
        value["arguments"]["offchain"]["figure"] = "caller annotation"
        value["arguments"]["offchain"]["extra"] = {"caller": "한글"}
        before = deepcopy(value)
        self.assertEqual(dispatch_request(value)["result"], direct(value))
        self.assertEqual(value, before)

    def test_numeric_inputs_are_never_coerced(self):
        for invalid in (True, False, "7", 7.0, 7.5, None, -1, 2**53 + 1):
            value = fixture("match")
            value["arguments"]["chain_supply"] = invalid
            with self.subTest(invalid=invalid):
                with self.assertRaises(TokenRewardError) as caught:
                    dispatch_request(decode_json(json.dumps(value)))
                self.assertEqual(caught.exception.code, "INVALID_NONNEGATIVE")
        for invalid in (True, "10", 10.0, None, 0):
            value = fixture("report")
            value["arguments"]["events"][0]["amount"] = invalid
            with self.subTest(invalid=invalid):
                with self.assertRaises(TokenRewardError) as caught:
                    dispatch_request(value)
                self.assertEqual(caught.exception.code, "INVALID_AMOUNT")
        self.assertEqual(dispatch_request({"operation": "supply_report",
                                          "arguments": {"events": []}})["result"], supply_report([]))

    def test_invalid_envelopes_never_invoke_either_model_function(self):
        values = [None, [], {}, {"operation": "supply_report"},
                  {"operation": "other", "arguments": {}},
                  {"operation": [], "arguments": {}},
                  {"operation": "supply_report", "arguments": []}]
        for name in ("report", "match"):
            value = fixture(name)
            values.append({**value, "extra": 1})
            for field in value["arguments"]:
                missing = deepcopy(value)
                del missing["arguments"][field]
                values.append(missing)
            extra = deepcopy(value)
            extra["arguments"]["default"] = None
            values.append(extra)
        for invalid in (float("inf"), float("nan"), {1}, b"bytes", (1,), {1: 2}, "\ud800"):
            value = fixture("report")
            value["arguments"]["events"] = invalid
            values.append(value)
        for value in values:
            with self.subTest(value=repr(value)), patch("supply_reconciliation.supply_report") as report, \
                    patch("supply_reconciliation.reconcile_supply") as reconcile:
                with self.assertRaises(FixtureError):
                    dispatch_request(value)
                report.assert_not_called()
                reconcile.assert_not_called()


if __name__ == "__main__":
    unittest.main()
