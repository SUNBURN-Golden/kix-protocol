"""Real pool CLI processes and strict stream boundaries."""

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from pool_cli import main, run_requests
from pool_session import PoolSession
from test_pool_session import FIXTURE, check_metadata, opening, request
from token_reward_model import MONEY_MAX, POOLS, PROVENANCE, PoolLedger, _canonical


HERE = Path(__file__).parent


def cli(data=b"", *, fixture=FIXTURE, requests="-", env=None, stdin_init=False):
    startup = ["--init-stdin"] if stdin_init else ["--fixture", str(fixture)]
    return subprocess.run([sys.executable, str(HERE / "pool_cli.py"), *startup,
                           "--requests", str(requests)], input=data, capture_output=True,
                          env=env, timeout=15)


class PoolCliTests(unittest.TestCase):
    def test_stdin_initialization_matches_complete_fixture_envelopes(self):
        init = (_canonical({"fixture_version": 1, "provenance": PROVENANCE,
                            "opening_balances": opening()}) + "\n").encode()
        records = [(HERE / f"fixtures/pool_{name}.jsonl").read_bytes()
                   for name in ("journey", "boundaries")]
        records += [b"", b"{}\n" + (_canonical(request("view")) + "\n").encode()]
        for data in records:
            with self.subTest(data=data):
                expected, actual = cli(data), cli(init + data, stdin_init=True)
                self.assertEqual((actual.returncode, actual.stdout, actual.stderr),
                                 (expected.returncode, expected.stdout, expected.stderr))
                self.replies(actual)

    def test_invalid_stdin_initialization_never_acknowledges_or_dispatches(self):
        good = {"fixture_version": 1, "provenance": PROVENANCE, "opening_balances": opening()}
        invalid = [b"\n", b"{\n", b"\xff\n", b"[]\n", b"null\n",
                   b'{"fixture_version":1,"fixture_version":1}\n',
                   (_canonical(good).replace('"CUSTOMER_DEPOSIT":20',
                                            '"CUSTOMER_DEPOSIT":20,"CUSTOMER_DEPOSIT":20') + "\n").encode()]
        values = [{k: v for k, v in good.items() if k != missing} for missing in good]
        values += [{**good, "extra": 1}, {**good, "fixture_version": True},
                   {**good, "fixture_version": 1.0}, {**good, "fixture_version": 2},
                   {**good, "provenance": "REAL"}]
        values += [{**good, "opening_balances": balances} for balances in
                   ({}, None, [], {**opening(), "OTHER": 0},
                    {k: v for k, v in opening().items() if k != POOLS[0]})]
        values += [{**good, "opening_balances": {**opening(), POOLS[0]: value}}
                   for value in (True, 1.0, "1", -1, MONEY_MAX + 1)]
        invalid += [(_canonical(value) + "\n").encode() for value in values]
        invalid += [(_canonical(good).replace('20', value, 1) + "\n").encode()
                    for value in ('NaN', '"\\ud800"')]
        following = (_canonical(request("credit")) + "\n").encode()
        for data in invalid:
            with self.subTest(data=data):
                result = cli(data + following, stdin_init=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                check_metadata(self, json.loads(result.stderr))
        for data in (b"", _canonical(good).encode(), (_canonical(good) + "\r").encode()):
            result = cli(data, stdin_init=True)
            self.assertEqual((result.returncode, result.stdout), (2, b""))
            self.assertEqual(json.loads(result.stderr)["error"]["type"], "FixtureError")

    def test_initialization_options_reject_before_consuming_stdin(self):
        invalid = [["--requests", "-"], ["--fixture", str(FIXTURE), "--init-stdin", "--requests", "-"],
                   ["--init-stdin", "--requests", str(HERE / "fixtures/pool_journey.jsonl")]]
        source = Mock()
        with patch("sys.stdin", source), patch("sys.stderr", io.StringIO()):
            for args in invalid:
                with self.subTest(args=args), self.assertRaises(SystemExit) as caught:
                    main(args)
                self.assertEqual(caught.exception.code, 2)
        source.readline.assert_not_called()

    def replies(self, process):
        replies = [json.loads(line) for line in process.stdout.decode("utf-8").splitlines()]
        for reply in replies:
            check_metadata(self, reply)
        return replies

    def test_real_file_and_stdin_journey_match_direct_model(self):
        path = HERE / "fixtures/pool_journey.jsonl"
        for process in (cli(path.read_bytes()), cli(requests=path)):
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stderr, b"")
            replies = self.replies(process)
            self.assertEqual(replies[0]["initialized"]["opening_balances"], opening())
            ledger = PoolLedger(opening())
            for item, reply in zip(map(json.loads, path.read_text().splitlines()), replies[1:]):
                expected = getattr(ledger, item["operation"])(**item["arguments"])
                self.assertEqual(reply["view"], expected)
            self.assertEqual(len(replies), 8)
            self.assertEqual(len(replies[-1]["view"]["credits"]), 7)
            self.assertEqual(len(replies[-1]["view"]["spends"]), 3)

    def test_real_boundaries_keep_state_and_original_codes(self):
        process = cli(requests=HERE / "fixtures/pool_boundaries.jsonl")
        self.assertEqual(process.returncode, 1, process.stderr)
        self.assertEqual(process.stderr, b"")
        replies = self.replies(process)
        self.assertEqual([reply["error"]["code"] for reply in replies[1:-1]],
                         ["POOL_FORBIDDEN_FOR_TOKEN_SPEND"] * 3 + ["POOL_EXHAUSTED_PAUSED"])
        self.assertEqual(replies[-1]["view"], PoolLedger(opening()).view())

    def test_malformed_json_stops_before_next_supplied_request(self):
        junk = [b"", b"{", b"[]", b"null", b"{}", b"true", b"\xff",
                b'{"operation":"view","operation":"view","arguments":{}}',
                b'{"operation":"credit","arguments":{"pool":"PROTOCOL_REVENUE",'
                b'"amount":1,"amount":2,"source_ref":"ref"}}',
                b'{"operation":"view","arguments":{},"extra":1}',
                b'{"operation":"view","arguments":[]}',
                b'{"operation":"spend","arguments":{}}',
                b'{"operation":"spend","arguments":{"pool":"PROTOCOL_REVENUE",'
                b'"amount":1,"program_ref":"ref","extra":0}}',
                b'{"operation":"transfer","arguments":{}}']
        for value in ("NaN", "Infinity", "-Infinity", "1e400", '"\\ud800"', '"\\udfff"'):
            junk.append(('{"operation":"credit","arguments":{"pool":"PROTOCOL_REVENUE",'
                         '"amount":' + value + ',"source_ref":"ref"}}').encode())
        following = _canonical(request("credit")).encode() + b"\n"
        for data in junk:
            with self.subTest(data=data):
                process = cli(data + b"\n" + following)
                self.assertEqual(process.returncode, 2)
                replies = self.replies(process)
                self.assertFalse(any("view" in reply for reply in replies))
                errors = [reply for reply in replies if "error" in reply]
                errors += [json.loads(line) for line in process.stderr.decode().splitlines()]
                self.assertEqual(len(errors), 1)
                check_metadata(self, errors[0])
                self.assertIn("type", errors[0]["error"])

    def test_finite_wrong_types_preserve_model_codes_and_sticky_refusal(self):
        records = [request("credit", amount=value) for value in (True, False, None, 1.0, "1", 9007199254740993)]
        records += [request("view")]
        process = cli(("\n".join(map(_canonical, records)) + "\n").encode())
        self.assertEqual(process.returncode, 1)
        replies = self.replies(process)
        self.assertEqual([r["error"]["code"] for r in replies[1:-1]], ["INVALID_AMOUNT"] * 6)
        self.assertEqual(replies[-1]["view"], PoolLedger(opening()).view())

    def test_empty_eof_no_implicit_view_and_fresh_process_has_no_persistence(self):
        first = cli((_canonical(request("credit")) + "\n").encode())
        self.assertEqual(first.returncode, 0)
        empty = cli()
        self.assertEqual(empty.returncode, 0)
        self.assertEqual(len(self.replies(empty)), 1)
        second = cli((_canonical(request("view")) + "\n").encode())
        self.assertEqual(self.replies(second)[-1]["view"], PoolLedger(opening()).view())

    def test_fixture_setup_and_io_errors_are_status_two(self):
        cases = [b'{', b'\xff',
                 b'{"fixture_version":1,"fixture_version":1,"provenance":"MOCK_TOKEN_REWARD_ONLY","opening_balances":{}}',
                 b'{"fixture_version":1,"provenance":"MOCK_TOKEN_REWARD_ONLY","opening_balances":{}}']
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "fixture.json"
            for data in cases:
                fixture.write_bytes(data)
                process = cli(fixture=fixture)
                self.assertEqual(process.returncode, 2)
                self.assertEqual(process.stdout, b"")
                reply = json.loads(process.stderr)
                check_metadata(self, reply)
            self.assertEqual(json.loads(process.stderr)["error"], {"code": "POOL_BALANCES_REQUIRED"})
            process = cli(fixture=Path(tmp) / "absent")
            self.assertEqual(process.returncode, 2)
            self.assertEqual(json.loads(process.stderr)["error"]["type"], "FileNotFoundError")
            process = cli(requests=Path(tmp) / "absent")
            self.assertEqual(process.returncode, 2)

    def test_utf8_is_explicit_even_with_ascii_locale(self):
        env = {**os.environ, "LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}
        data = (_canonical(request("credit", ref="합성")) + "\n").encode("utf-8")
        process = cli(data, env=env)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(self.replies(process)[1]["view"]["credits"][-1]["source_ref"], "합성")

    def test_output_failure_never_retries_or_consumes_next_record(self):
        class BrokenOutput(io.StringIO):
            def write(self, value):
                raise BrokenPipeError("output closed")

        session = PoolSession(opening())
        lines = iter([_canonical(request("credit")), _canonical(request("spend"))])
        with patch.object(PoolLedger, "credit", autospec=True, side_effect=PoolLedger.credit) as credit, \
                patch.object(PoolLedger, "spend") as spend:
            with self.assertRaises(BrokenPipeError):
                run_requests(session, lines, output_stream=BrokenOutput())
            self.assertEqual(credit.call_count, 1)
            spend.assert_not_called()
            self.assertEqual(session.view()["balances"]["PROTOCOL_REVENUE"], 3)
            self.assertEqual(next(lines), _canonical(request("spend")))
        with patch("sys.stdout", BrokenOutput()), patch("sys.stderr", io.StringIO()) as errors, \
                patch("sys.stdin", io.StringIO(_canonical(request("credit")))), \
                patch.object(PoolLedger, "credit") as credit:
            self.assertEqual(main(["--fixture", str(FIXTURE), "--requests", "-"]), 2)
            credit.assert_not_called()  # Initialization output failed first.
            check_metadata(self, json.loads(errors.getvalue()))


if __name__ == "__main__":
    unittest.main()
