"""Strict fixture boundary and runnable CLI; no new economics or protocol schema."""

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from local_finance_cli import FixtureError, decode_fixture, execute_fixture, validate_fixture
from local_finance_session import LocalFinanceSession

HERE = Path(__file__).resolve().parent


def fixture(name="journey"):
    return decode_fixture((HERE / "fixtures" / ("finance_" + name + ".synthetic.json")).read_text())


class LocalFinanceCliTests(unittest.TestCase):
    def cli(self, path):
        return subprocess.run([sys.executable, str(HERE / "local_finance_cli.py"), "--fixture", str(path)],
                              cwd=tempfile.gettempdir(), capture_output=True, text=True,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=30)

    def test_subprocess_fixtures_preserve_receipts_views_and_source_snapshots(self):
        for name in ("journey", "isolation"):
            run = self.cli(HERE / "fixtures" / ("finance_" + name + ".synthetic.json"))
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(run.stderr, "")
            report = json.loads(run.stdout)
            expected, status = execute_fixture(fixture(name))
            self.assertEqual((report, status), (json.loads(json.dumps(expected)), 0))
            self.assertTrue(all(r["expectation_met"] for r in report["results"]))
            if name == "journey":
                rows = report["results"]
                self.assertEqual([rows[i]["error"]["code"] for i in (7, 9)], ["SETTLEMENT_NOT_COMMITTED"] * 2)
                self.assertEqual(rows[10]["receipt"]["credit"]["phase"], "DRAWN")
                self.assertEqual(rows[13]["view"]["outstanding_exposure"], 25000)
                self.assertEqual(rows[-1]["view"]["phase"], "CLOSED")
                self.assertEqual(rows[16]["receipt"]["credit"]["phase"], "DRAWN")
                self.assertTrue(rows[16]["receipt"]["duplicate"])
                self.assertEqual(rows[17]["receipt"]["settlement"]["claim"]["confirmed_cash"], 55000)
                self.assertEqual(rows[18]["view"]["claim"]["confirmed_cash"], 93000)
                self.assertEqual(len(report["source_calls"]), 3)
                for row in rows:
                    if "receipt" in row:
                        self.assertIs(row["receipt"]["funds_executed"], False)
                        view = row["receipt"].get("settlement", row["receipt"].get("credit"))
                        self.assertIs(view["bank_debit_observed"], False)
                        if "economic_finality_claimed" in row["receipt"]:
                            self.assertIs(row["receipt"]["economic_finality_claimed"], False)

    def test_saved_snapshot_reuse_and_offer_replay_after_later_statement(self):
        value = fixture()
        replay = copy.deepcopy(value["steps"][4])
        second = copy.deepcopy(replay)
        second["advance_id"] = "second-credit"
        second["idempotency_key"] = "explicit-second-offer"
        changed = copy.deepcopy(replay)
        changed["body"]["amount"] += 1
        changed["expect_error"] = dict(type="CreditError",code="IDEMPOTENCY_CONFLICT")
        value["steps"].extend([replay,second,changed])
        report, status = execute_fixture(value)
        self.assertEqual(status,0,report)
        replayed = report["results"][-3]["receipt"]
        self.assertTrue(replayed["duplicate"])
        self.assertEqual(replayed["credit"]["phase"],"OFFERED")
        self.assertEqual(report["results"][-2]["receipt"]["credit"]["confirmed_cash_on_face"],0)
        self.assertEqual(report["results"][-1]["error"]["code"],"IDEMPOTENCY_CONFLICT")

    def test_full_validation_rejects_invalid_late_steps_before_session_creation(self):
        base = fixture()
        cases = []
        def changed(edit):
            value = copy.deepcopy(base)
            edit(value)
            cases.append(value)
        changed(lambda f: f.update(extra=True))
        for version in (True, 1.0, "1", 2):
            changed(lambda f, version=version: f.update(fixture_version=version))
        for synthetic in (False, 1, "true"):
            changed(lambda f, synthetic=synthetic: f.update(synthetic=synthetic))
        changed(lambda f: f.update(steps={}))
        changed(lambda f: f.update(statements={}))
        for field, value in (("target", "bank"), ("operation", "attempt_execution"), ("operation", []),
                             ("advance_id", 1), ("body", {}), ("idempotency_key", "new"), ("extra", None)):
            changed(lambda f, field=field, value=value: f["steps"][-1].update({field: value}))
        changed(lambda f: f["steps"][-1].pop("advance_id"))
        changed(lambda f: f["steps"].append(dict(target="credit", operation="draw", advance_id="a", idempotency_key="k", body={})))
        changed(lambda f: f["steps"][8]["body"].update(amount=1))
        for amount in (True, 1.0, "1", None, {}):
            changed(lambda f, amount=amount: f["steps"][12]["body"].update(amount=amount))
            changed(lambda f, amount=amount: f["statements"][-1]["record"].update(amount=amount))
        changed(lambda f: f["steps"][0]["body"]["policy"].update(fee_bps=False))
        changed(lambda f: f["steps"][0]["body"]["policy"].update(extra=0))
        changed(lambda f: f["steps"][0]["body"].pop("policy"))
        changed(lambda f: f["steps"][4].update(face_ref="future"))
        changed(lambda f: f["steps"][4]["body"].update(face={}))
        changed(lambda f: f["steps"].append(dict(target="settlement", operation="view", settlement_id="s", save_claim_as="journey-settlement-face")))
        changed(lambda f: f["steps"][7]["expect_error"].update(type="RuntimeError"))
        changed(lambda f: f["steps"][7]["expect_error"].update(code=1))
        changed(lambda f: f["statements"].append(copy.deepcopy(f["statements"][0])))
        changed(lambda f: f["statements"][0].update(fault="synthetic_statement_timeout"))
        changed(lambda f: f["statements"][0]["record"].pop("tax"))
        changed(lambda f: f["statements"][0]["record"].update(extra=0))
        changed(lambda f: f["statements"][0].pop("record"))
        changed(lambda f: f["statements"].append(dict(settlement_id="s",movement_id="fault",fault="real-provider")))
        for index, value in enumerate(cases):
            with self.subTest(case=index), patch("local_finance_cli.LocalFinanceSession") as constructor:
                with self.assertRaises(FixtureError):
                    execute_fixture(value)
                constructor.assert_not_called()

    def test_strict_decoding_duplicate_fields_nonfinite_and_invalid_json(self):
        for text in ('{"fixture_version":1,"fixture_version":1}', '{"a":{"x":1,"x":2}}',
                     '{"amount":NaN}', '{"amount":Infinity}', '{"amount":-Infinity}', '{'):
            with self.subTest(text=text), self.assertRaises(FixtureError):
                decode_fixture(text)

    def test_integer_boundaries_roundtrip_and_range_errors_remain_fsm_errors(self):
        value = fixture()
        value["statements"] = []
        first = copy.deepcopy(value["steps"][0])
        first["body"]["gross"] = 9007199254740993
        first["expect_error"] = dict(type="SettlementError",code="INVALID_AMOUNT")
        second = copy.deepcopy(first)
        second["body"]["gross"] -= 1
        second["expect_error"]["code"] = "IDEMPOTENCY_CONFLICT"
        third = copy.deepcopy(first)
        third.pop("expect_error")
        third["idempotency_key"] = "explicit-boundary-key"
        third["body"]["gross"] = 10**12
        value["steps"] = [first, second, third, dict(target="settlement",operation="view",settlement_id=first["settlement_id"])]
        decoded = decode_fixture(json.dumps(value))
        self.assertEqual(decoded["steps"][0]["body"]["gross"], 9007199254740993)
        report, status = execute_fixture(decoded)
        self.assertEqual(status, 0, report)
        receipt = json.loads(json.dumps(report))["results"][2]["receipt"]
        self.assertIs(type(receipt["settlement"]["gross"]), int)
        self.assertEqual(receipt["settlement"]["gross"], 10**12)

    def test_unexpected_outcome_stops_once_and_retains_earlier_effects(self):
        value = fixture()
        value["steps"][7].pop("expect_error")
        recordings, _ = validate_fixture(value)
        session = LocalFinanceSession(recordings=recordings)
        original = session.credit
        with patch("local_finance_cli.LocalFinanceSession", return_value=session), patch.object(session, "credit", wraps=original) as calls:
            report, status = execute_fixture(value)
        self.assertEqual(status, 1)
        self.assertEqual(len(report["results"]), 8)
        self.assertEqual(calls.call_count, 4)  # offer, bind, approve, exactly one draw
        self.assertEqual(calls.call_args.kwargs, dict(idempotency_key="rejected-key",draw_id="journey-credit-draw"))
        self.assertEqual(session.settlement_view("journey-settlement")["phase"], "CAPTURED")
        self.assertEqual(session.credit_view("journey-credit")["phase"], "APPROVED")
        self.assertEqual(session.statement_source.calls, ())
        # Probe the stored rejection, including exact request fingerprint, publicly.
        with self.assertRaisesRegex(Exception, "SETTLEMENT_NOT_COMMITTED"):
            original("draw", "journey-credit", idempotency_key="rejected-key", draw_id="journey-credit-draw")
        with self.assertRaisesRegex(Exception, "IDEMPOTENCY_CONFLICT"):
            original("draw", "journey-credit", idempotency_key="rejected-key", draw_id="changed")

    def test_expected_source_errors_continue_once_internal_errors_never_continue(self):
        value = dict(fixture_version=1, synthetic=True, statements=[dict(settlement_id="s",movement_id="m",fault="synthetic_statement_timeout")], steps=[
            dict(target="settlement",operation="commit",settlement_id="s",idempotency_key="k",body=dict(movement_id="m"),expect_error=dict(type="StatementSourceError")),
            dict(target="credit",operation="view",advance_id="missing",expect_error=dict(type="CreditError",code="UNKNOWN_ADVANCE")),
        ])
        report, status = execute_fixture(value)
        self.assertEqual((status,len(report["results"]),report["source_calls"]), (0,2,[("s","m")]))
        with patch.object(LocalFinanceSession, "settlement", side_effect=RuntimeError("internal")) as call:
            report, status = execute_fixture(value)
        self.assertEqual((status,len(report["results"])), (1,1))
        self.assertEqual(report["results"][0]["error"]["type"], "RuntimeError")
        call.assert_called_once()

    def test_expected_error_that_succeeds_and_null_snapshot_stop(self):
        value = fixture()
        value["steps"][0]["expect_error"] = dict(type="SettlementError")
        report, status = execute_fixture(value)
        self.assertEqual((status,len(report["results"])), (1,1))
        self.assertIn("receipt",report["results"][0])
        value = fixture()
        value["steps"] = [value["steps"][0], value["steps"][3]]
        report, status = execute_fixture(value)
        self.assertEqual(status,1)
        self.assertEqual(report["results"][-1]["error"]["type"],"ClaimSnapshotError")

    def test_subprocess_exit_one_and_two_with_json_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            value = fixture()
            value["steps"][7].pop("expect_error")
            path.write_text(json.dumps(value))
            run = self.cli(path)
            self.assertEqual(run.returncode,1,run.stdout+run.stderr)
            self.assertEqual(len(json.loads(run.stdout)["results"]),8)
            for text in ('{"x":1,"x":2}', '{', '[]'):
                path.write_text(text)
                run = self.cli(path)
                self.assertEqual(run.returncode,2,run.stdout+run.stderr)
                self.assertEqual(json.loads(run.stdout)["error"]["type"],"FixtureError")
            path.write_bytes(b'\xff')
            self.assertEqual(self.cli(path).returncode,2)
            self.assertEqual(self.cli(Path(directory)/"missing").returncode,2)


if __name__ == "__main__":
    unittest.main()
