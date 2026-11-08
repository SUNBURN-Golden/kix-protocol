"""Real subprocess file/stdin and serialization/error integration coverage."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from reward_fixture import decode_json
import supply_cli
from supply_reconciliation import NOTICE
from test_supply_reconciliation import direct, fixture
from token_reward_model import PROVENANCE, _canonical


ROOT = Path(__file__).resolve().parent


class SupplyCliTests(unittest.TestCase):
    def run_cli(self, *args, data=None):
        return subprocess.run([sys.executable, str(ROOT / "supply_cli.py"), *args],
                              input=data, capture_output=True, timeout=10,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def output(self, process, status, operation):
        self.assertEqual(process.returncode, status, process.stderr)
        self.assertEqual(process.stderr, b"")
        value = decode_json(process.stdout.decode("utf-8"))
        self.assertEqual(process.stdout.decode("utf-8"), _canonical(value) + "\n")
        self.assertEqual(set(value), {"operation", "provenance", "evidence_class", "notice",
                                      "result" if status == 0 else "error"})
        self.assertEqual(value["operation"], operation)
        self.assertEqual(value["provenance"], PROVENANCE)
        self.assertEqual(value["evidence_class"], "CALCULATION_ONLY")
        self.assertEqual(value["notice"], NOTICE)
        return value

    def test_every_fixture_file_stdin_parity_and_direct_results(self):
        alarms = {"match": "MATCH", "holder_burn": "HOLDER_BURN_OUTSIDE_LAYER",
                  "unexplained": "UNEXPLAINED", "unapproved_mint": "UNAPPROVED_MINT",
                  "unapproved_path": "UNAPPROVED_PATH", "both_causes": "UNAPPROVED_PATH"}
        errors = {"duplicate": "SUPPLY_EVENT_DUPLICATE", "tampered": "SUPPLY_REPORT_MISMATCH"}
        for name in ("report", *alarms, *errors):
            with self.subTest(name=name):
                path = ROOT / "fixtures" / f"supply_{name}.json"
                request = fixture(name)
                status = 1 if name in errors else 0
                file_run = self.run_cli("--request", str(path))
                stdin_run = self.run_cli("--request", "-", data=path.read_bytes())
                self.assertEqual(file_run.stdout, stdin_run.stdout)
                output = self.output(file_run, status, request["operation"])
                self.output(stdin_run, status, request["operation"])
                if status:
                    self.assertEqual(output["error"], {"code": errors[name]})
                else:
                    self.assertEqual(output["result"], direct(request))
                    if name in alarms:
                        self.assertEqual(output["result"]["alarm"], alarms[name])

    def test_duplicate_inside_supplied_report_rejects_without_repair(self):
        request = fixture("match")
        events = request["arguments"]["offchain"]["events"]
        events.append(dict(events[0]))
        process = self.run_cli("--request", "-", data=json.dumps(request).encode())
        output = self.output(process, 1, "reconcile_supply")
        self.assertEqual(output["error"], {"code": "SUPPLY_EVENT_DUPLICATE"})

    def test_numeric_serialization_and_unicode(self):
        for spelling in ("true", '"7"', "7.0", "7e0", "9007199254740993"):
            request = json.dumps(fixture("match")).replace('"chain_supply": 7', '"chain_supply": ' + spelling)
            output = self.output(self.run_cli("--request", "-", data=request.encode()),
                                 1, "reconcile_supply")
            self.assertEqual(output["error"], {"code": "INVALID_NONNEGATIVE"})
        request = fixture("report")
        request["arguments"]["events"][0]["event_id"] = "합성-민팅"
        process = self.run_cli("--request", "-", data=json.dumps(request, ensure_ascii=False).encode())
        self.assertEqual(self.output(process, 0, "supply_report")["result"], direct(request))
        self.assertIn("합성-민팅", process.stdout.decode())

    def test_malformed_json_and_envelopes_never_calculate(self):
        valid = json.dumps(fixture("report"))
        cases = [(text, None) for text in (
            "", "{} {}", "[]", '{"operation":"x","operation":"y"}',
            valid.replace('"amount": 10', '"amount":10,"amount":11'),
            valid.replace('"amount": 10', '"amount":NaN'),
            valid.replace('"amount": 10', '"amount":Infinity'),
            valid.replace('"amount": 10', '"amount":1e999'),
            valid.replace('"mint-1"', '"\\ud800"'),
            '{"\\ud800":1,"\\ud800":2}',
            '{"operation":[],"arguments":{}}',
            '{"operation":"unknown","arguments":{}}')]
        cases += [('{"operation":"supply_report","arguments":{}}', "supply_report"),
                  ('{"operation":"supply_report","arguments":{"events":[],"extra":0}}', "supply_report"),
                  ('{"operation":"reconcile_supply","arguments":{"offchain":{}}}', "reconcile_supply"),
                  (valid[:-1] + ',"extra":0}', "supply_report")]
        for text, operation in cases:
            with self.subTest(text=text):
                process = self.run_cli("--request", "-", data=text.encode())
                self.assertEqual(self.output(process, 2, operation)["error"]["type"], "FixtureError")
                stdout = io.StringIO()
                with patch.object(sys, "stdin", io.StringIO(text)), redirect_stdout(stdout), \
                        patch("supply_reconciliation.supply_report") as report, \
                        patch("supply_reconciliation.reconcile_supply") as reconcile:
                    self.assertEqual(supply_cli.main(["--request", "-"]), 2)
                report.assert_not_called()
                reconcile.assert_not_called()

    def test_invalid_utf8_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_bytes(b"\xff")
            for process, kind in ((self.run_cli("--request", str(path)), "UnicodeDecodeError"),
                                  (self.run_cli("--request", "-", data=b"\xff"), "UnicodeDecodeError"),
                                  (self.run_cli("--request", str(path.with_name("absent"))), "FileNotFoundError")):
                self.assertEqual(self.output(process, 2, None)["error"]["type"], kind)

    def test_usage_errors_are_stderr_without_json_and_import_starts_nothing(self):
        for args in ((), ("--guided",), ("--request", "-", "--extra")):
            process = self.run_cli(*args)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(process.stdout, b"")
            self.assertIn(b"usage:", process.stderr)
        process = subprocess.run([sys.executable, "-c", "import supply_cli, supply_reconciliation"],
                                 cwd=ROOT, capture_output=True, timeout=10,
                                 env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual((process.returncode, process.stdout, process.stderr), (0, b"", b""))


if __name__ == "__main__":
    unittest.main()
