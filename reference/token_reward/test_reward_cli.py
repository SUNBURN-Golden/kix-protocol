"""Subprocess journeys and JSONL stream boundaries; no lifecycle reimplementation."""

from contextlib import redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from reward_cli import dispatch_request, run_requests
from reward_fixture import decode_json, load_fixture
from test_reward_session import FIXTURES, requests
from token_reward_model import ALWAYS_FALSE_FLAGS, PROVENANCE, _canonical


CLI = Path(__file__).with_name("reward_cli.py")


class RewardCliTests(unittest.TestCase):
    def invoke(self, text=None, path=None, fixture=None):
        return subprocess.run(
            [sys.executable, str(CLI), "--fixture", str(fixture or FIXTURES / "reward_session.json"),
             "--requests", str(path) if path else "-"],
            input=text, capture_output=True, text=True, encoding="utf-8", timeout=20,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})

    def output(self, completed, status):
        self.assertEqual(completed.returncode, status, completed.stderr + completed.stdout)
        self.assertEqual(completed.stderr, "")
        result = [decode_json(line) for line in completed.stdout.splitlines()]
        for row in result:
            self.assertEqual(row["provenance"], PROVENANCE)
            self.assertEqual(set(row) - {"operation", "provenance"},
                             {next(k for k in row if k not in ("operation", "provenance"))})
            view = row.get("view") or row.get("receipt", {}).get("reward")
            if view:
                self.assertTrue(view["non_transferable_until_chargeback_end"])
                for flag in ALWAYS_FALSE_FLAGS:
                    self.assertIs(view[flag], False)
            if "receipt" in row:
                for flag in ALWAYS_FALSE_FLAGS:
                    self.assertIs(row["receipt"][flag], False)
        return result

    def test_every_fixture_file_stdin_and_repeat_transcripts_are_identical(self):
        statuses = {"participation": 0, "cancellation": 0, "boundaries": 1,
                    "unknown_pending": 1, "unknown_resolution": 1}
        for name, status in statuses.items():
            with self.subTest(name=name):
                path = FIXTURES / (name + ".jsonl")
                first = self.invoke(path=path)
                rows = self.output(first, status)
                self.assertEqual(len(rows), len(path.read_text().splitlines()))
                by_stdin = self.invoke(text=path.read_text())
                self.output(by_stdin, status)
                self.assertEqual(by_stdin.stdout, first.stdout)
                repeated = self.invoke(path=path)
                self.output(repeated, status)
                self.assertEqual(repeated.stdout, first.stdout)
        self.assertEqual(self.output(self.invoke(text=""), 0), [])

    def test_participation_historical_receipts_and_one_pool_spend(self):
        rows = self.output(self.invoke(path=FIXTURES / "participation.jsonl"), 0)
        self.assertEqual([row["receipt"]["reward"]["phase"] for row in rows[:5]],
                         ["OBSERVED", "HELD", "ELIGIBLE", "ISSUING", "ISSUED"])
        for original, replay in ((0, 5), (3, 6), (4, 7)):
            expected = {**rows[original]["receipt"], "duplicate": True, "applied": None}
            self.assertEqual(rows[replay]["receipt"], expected)
        self.assertEqual(rows[8]["view"]["phase"], "ISSUED")
        self.assertEqual(rows[9]["reward_ids"], [rows[8]["view"]["reward_id"]])
        self.assertEqual(rows[-1]["pool_view"]["spends"], [{
            "pool": "TOKEN_TREASURY_REWARD", "amount": 25, "program_ref": "synthetic-program"}])
        self.assertEqual(rows[-1]["pool_view"]["balances"]["TOKEN_TREASURY_REWARD"], 475)

    def test_cancellation_and_krw_effect_remain_separate(self):
        rows = self.output(self.invoke(path=FIXTURES / "cancellation.jsonl"), 0)
        views = [row["view"] for row in rows if "view" in row]
        self.assertEqual([v["phase"] for v in views], ["REVERSED", "CLAWBACK_CLAIM"])
        self.assertEqual([v["payout_effect_count"] for v in views], [0, 1])
        refund = next(row["receipt"] for row in rows if row["operation"] == "observe_krw_refund")
        self.assertEqual(refund["reward"]["phase"], "ISSUED")
        self.assertEqual(refund["reward"]["krw_phase"], "KRW_REFUND_NOTED")
        self.assertNotEqual(refund["effect"]["krw_effect_id"], refund["reward"]["token_effect_id"])
        self.assertEqual(len(rows[-1]["pool_view"]["spends"]), 1)

    def test_unknown_remains_pending_until_separate_explicit_resolution_in_same_session(self):
        pending = (FIXTURES / "unknown_pending.jsonl").read_text()
        resolution = (FIXTURES / "unknown_resolution.jsonl").read_text()
        rows = self.output(self.invoke(text=pending), 1)
        views = [row["view"] for row in rows if "view" in row]
        self.assertEqual([view["phase"] for view in views], ["UNKNOWN", "UNKNOWN"])
        self.assertEqual(views[-1]["resend_count"], 1)
        self.assertEqual(rows[-1]["pool_view"]["spends"], [])
        self.assertEqual([row["error"]["code"] for row in rows if "error" in row],
                         ["OUTCOME_UNSUPPORTED", "DIGEST_MISMATCH", "RESEND_PERMIT_REQUIRED", "DIGEST_MISMATCH"])
        combined = pending + resolution
        result = self.invoke(text=combined)
        resolved = self.output(result, 1)  # Earlier explicit rejections remain reflected in exit status.
        self.assertEqual(resolved[:len(rows)], rows)
        self.assertEqual(resolved[-2]["view"]["phase"], "ISSUED")
        self.assertEqual(resolved[-2]["view"]["reward_id"], views[-1]["reward_id"])
        self.assertEqual(resolved[-2]["view"]["payout_effect_count"], 1)
        self.assertEqual(len(resolved[-1]["pool_view"]["spends"]), 1)
        self.assertTrue(resolved[-3]["receipt"]["duplicate"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "combined.jsonl"
            path.write_text(combined)
            by_file = self.invoke(path=path)
            self.output(by_file, 1)
            self.assertEqual(by_file.stdout, result.stdout)
        self.assertEqual(self.invoke(text=combined).stdout, result.stdout)

    def test_semantic_refusals_retain_machine_error_codes(self):
        rows = self.output(self.invoke(path=FIXTURES / "boundaries.jsonl"), 1)
        self.assertEqual([row["error"]["code"] for row in rows if "error" in row],
                         ["WINDOW_OPEN"] + ["POOL_FORBIDDEN_FOR_TOKEN_SPEND"] * 3 + ["AI_APPROVAL_REJECTED"])
        self.assertEqual(rows[-2]["view"]["phase"], "ELIGIBLE")
        self.assertEqual(rows[-1]["pool_view"]["spends"], [])

    def test_malformed_stops_without_dispatch_or_idempotency_consumption(self):
        session = load_fixture(FIXTURES / "reward_session.json")
        observed, hold = requests("participation")[:2]
        malformed = copy.deepcopy(hold)
        malformed["arguments"]["extra"] = "bad"
        with patch.object(session._machine, "hold", wraps=session._machine.hold) as method:
            with redirect_stdout(io.StringIO()) as output:
                code = run_requests(session, [_canonical(r) for r in (observed, malformed, hold)])
            self.assertEqual(code, 2)
            method.assert_not_called()
            rows = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[-1]["error"]["type"], "FixtureError")
            self.assertEqual(session.view(hold["arguments"]["reward_id_value"])["phase"], "OBSERVED")
            receipt = dispatch_request(session, hold)["receipt"]
            self.assertFalse(receipt["duplicate"])
            method.assert_called_once()

    def test_bad_stream_setup_and_io_exit_two_without_tracebacks(self):
        for text in ('\n', '{bad}\n', '{"operation":"reward_ids","arguments":{},"arguments":{}}\n',
                     '{"operation":"observe","arguments":{"source_view":{"x":1e9999}}}\n'):
            rows = self.output(self.invoke(text=text + _canonical(requests("participation")[0])), 2)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["error"]["type"], "FixtureError")
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            self.output(self.invoke(path=missing), 2)
            self.output(self.invoke(text="", fixture=missing), 2)
            invalid = Path(directory) / "bad.jsonl"
            invalid.write_bytes(b'\xff\n')
            self.output(self.invoke(path=invalid), 2)
            fixture = Path(directory) / "bad.json"
            fixture.write_text('{"fixture_version":true}')
            self.output(self.invoke(text="", fixture=fixture), 2)
            value = json.loads((FIXTURES / "reward_session.json").read_text())
            value["opening_balances"]["PROTOCOL_REVENUE"] = -1
            fixture.write_text(json.dumps(value))
            rows = self.output(self.invoke(text="", fixture=fixture), 2)
            self.assertEqual(rows[0]["error"]["code"], "INVALID_NONNEGATIVE")


if __name__ == "__main__":
    unittest.main()
