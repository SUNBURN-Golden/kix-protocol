"""Real local CLI journeys plus instrumented proof of no early calculations."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import collateral_cli
from collateral_assessment import NOTICE, OPERATION
from reward_fixture import decode_json
from token_reward_model import PROVENANCE, collateral_recognized


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"


class CollateralCliTests(unittest.TestCase):
    def run_cli(self, *args, data=None):
        return subprocess.run([sys.executable, str(ROOT / "collateral_cli.py"), *args],
                              input=data, capture_output=True,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=10)

    def output(self, process, status):
        self.assertEqual(process.returncode, status, process.stderr)
        output = json.loads(process.stdout)
        self.assertEqual(output["operation"], OPERATION)
        self.assertEqual(output["provenance"], PROVENANCE)
        self.assertEqual(output["evidence_class"], "CALCULATION_ONLY")
        self.assertEqual(output["notice"], NOTICE)
        return output

    def test_every_json_fixture_file_stdin_parity_and_determinism(self):
        for name in ("guarantee", "escrow", "mixed", "empty", "token_only", "valuation"):
            with self.subTest(name=name):
                path = FIXTURES / f"collateral_{name}.json"
                status = 1 if name in ("token_only", "valuation") else 0
                file_run = self.run_cli("--request", str(path))
                stdin_run = self.run_cli("--request", "-", data=path.read_bytes())
                self.assertEqual(file_run.stdout, stdin_run.stdout)
                self.assertEqual(file_run.stdout, self.run_cli("--request", str(path)).stdout)
                self.assertEqual(file_run.stderr, b"")
                output = self.output(file_run, status)
                self.output(stdin_run, status)
                if status:
                    self.assertEqual(output["error"], {"code": {
                        "token_only": "TOKEN_ONLY_COLLATERAL_REJECTED",
                        "valuation": "PRICE_SOURCE_UNDEFINED"}[name]})
                    self.assertNotIn("result", output)
                else:
                    expected = collateral_recognized(**decode_json(path.read_text())["arguments"])
                    self.assertEqual(output["result"], expected)

    def test_guided_complete_empty_decline_and_incomplete_fixtures(self):
        for name, status in (("mixed", 0), ("empty", 0), ("decline", 0), ("incomplete", 2)):
            with self.subTest(name=name):
                process = self.run_cli("--guided", data=(FIXTURES / f"collateral_guided_{name}.txt").read_bytes())
                output = self.output(process, status)
                self.assertIn(b"Synthetic", process.stderr)
                if name in ("mixed", "empty"):
                    args = decode_json((FIXTURES / f"collateral_{name}.json").read_text())["arguments"]
                    self.assertEqual(output["result"], collateral_recognized(**args))
                    preview = next(line for line in process.stderr.decode().splitlines()
                                   if line.startswith("Proposal: "))
                    self.assertEqual(json.loads(preview.removeprefix("Proposal: "))["arguments"], args)
                else:
                    self.assertNotIn("result", output)
                if name == "decline":
                    self.assertTrue(output["cancelled"])

    def instrument(self, lines, expected_status, calls=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, "stdin", io.StringIO(lines)), redirect_stdout(stdout), redirect_stderr(stderr):
            with patch("collateral_assessment.collateral_recognized",
                       wraps=collateral_recognized) as calculate:
                status = collateral_cli.main(["--guided"])
        self.assertEqual(status, expected_status)
        self.assertEqual(calculate.call_count, calls)
        output = json.loads(stdout.getvalue())
        if calls == 0:
            self.assertNotIn("result", output)
        return output

    def test_eof_at_every_prompt_and_declines_never_calculate(self):
        lines = ["100", "2", "KRW_GUARANTEE", "30", "TOKEN", "999", "CALCULATE"]
        for count in range(len(lines)):
            with self.subTest(eof_before=count):
                self.instrument("\n".join(lines[:count]) + ("\n" if count else ""), 2)
        for confirmation in ("NO", "calculate", " CALCULATE", ""):
            self.instrument("\n".join(lines[:-1] + [confirmation]) + "\n", 0)
        self.instrument("\n".join(lines) + "\n", 0, calls=1)
        self.instrument("100\n0\nCALCULATE\n", 0, calls=1)

    def test_malformed_guided_inputs_never_calculate(self):
        for lines in ("\n", "1.0\n", "true\n", "100\n\n", "100\n-1\n",
                      "100\n1e0\n", "100\n1\n\n", "100\n1\nESCROW\n\n",
                      "100\n1\nESCROW\n1.0\n", "100\n1\nESCROW\n9007199254740993.0\n"):
            with self.subTest(lines=lines):
                self.instrument(lines, 2)

    def test_interrupt_at_every_prompt_never_calculates(self):
        lines = ["100", "1", "ESCROW", "25", "CALCULATE"]
        for count in range(len(lines)):
            with self.subTest(count=count), patch("collateral_cli._prompt", side_effect=lines[:count] + [KeyboardInterrupt]):
                self.instrument("", 2)

    def test_confirmed_guided_domain_rejection_calls_once(self):
        output = self.instrument("100\n1\nTOKEN\n999\nCALCULATE\n", 1, calls=1)
        self.assertEqual(output["error"], {"code": "TOKEN_ONLY_COLLATERAL_REJECTED"})

    def test_strict_decoding_failures_never_calculate(self):
        valid = (FIXTURES / "collateral_empty.json").read_text()
        invalid = ["", "{} {}", "[]", '{"operation":"x","operation":"y"}',
                   valid.replace('"liability_krw": 100', '"liability_krw": 100,"liability_krw": 1'),
                   valid.replace('"collateral_items": []',
                                 '"collateral_items": [{"kind":"TOKEN","amount":1,"amount":2}]'),
                   valid.replace("100", "NaN"), valid.replace("100", "Infinity"),
                   valid.replace("100", "1e999"), valid.replace("100", '"\\ud800"'),
                   valid.replace('"collateral_items": []', '"extra": []')]
        for data in invalid:
            with self.subTest(data=data), patch.object(sys, "stdin", io.StringIO(data)):
                stdout = io.StringIO()
                with redirect_stdout(stdout), patch("collateral_assessment.collateral_recognized") as calculate:
                    self.assertEqual(collateral_cli.main(["--request", "-"]), 2)
                calculate.assert_not_called()
                self.assertNotIn("result", json.loads(stdout.getvalue()))

    def test_invalid_utf8_file_and_stdin_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_bytes(b"\xff")
            for process in (self.run_cli("--request", str(path)),
                            self.run_cli("--request", "-", data=b"\xff"),
                            self.run_cli("--request", str(path.with_name("absent.json"))),
                            self.run_cli("--guided", data=b"\xff\n")):
                output = self.output(process, 2)
                self.assertNotIn("result", output)
                self.assertIn("type", output["error"])
                self.assertNotIn("code", output["error"])

    def test_duplicate_surrogate_key_rejection_has_utf8_json_diagnostic(self):
        process = self.run_cli("--request", "-", data=b'{"\\ud800":1,"\\ud800":2}')
        output = self.output(process, 2)
        self.assertEqual(output["error"]["type"], "FixtureError")
        self.assertEqual(process.stderr, b"")
        self.assertNotIn("result", output)
        # The response itself must pass the shared strict Unicode validator.
        decode_json(process.stdout.decode("utf-8"))

    def test_exactly_one_input_mode(self):
        for args in ((), ("--guided", "--request", "-")):
            process = self.run_cli(*args)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(process.stdout, b"")


if __name__ == "__main__":
    unittest.main()
