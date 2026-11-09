"""Confirmation, EOF, failure fencing and real guided pool journeys."""

import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from pool_console import run_console
from pool_session import PoolSession, dispatch_request
from test_pool_session import FIXTURE, check_metadata, opening
from token_reward_model import PoolLedger


HERE = Path(__file__).parent


def replies(text):
    result = []
    for line in text.splitlines():
        start = line.find('{"')
        if start >= 0:
            value = json.loads(line[start:])
            if "provenance" in value:
                result.append(value)
    return result


def console(text, *, output=None, errors=None, source=None):
    output = output if output is not None else io.StringIO()
    errors = errors if errors is not None else io.StringIO()
    status = run_console(opening(), input_stream=source if source is not None else io.StringIO(text),
                         output_stream=output, error_stream=errors)
    return status, output.getvalue(), errors.getvalue()


class PoolConsoleTests(unittest.TestCase):
    def test_initialization_preview_flushed_before_constructor_no_implicit_view(self):
        output = io.StringIO()

        class Input(io.StringIO):
            def readline(inner):
                self.assertIn('"opening_balances":', output.getvalue())
                return super().readline()

        with patch("pool_console.PoolSession", wraps=PoolSession) as constructor, \
                patch.object(PoolLedger, "view", autospec=True, side_effect=PoolLedger.view) as view:
            status, text, err = console("", source=Input("SUBMIT\nquit\n"), output=output)
            self.assertEqual(status, 0)
            constructor.assert_called_once_with(opening())
            view.assert_not_called()
            self.assertEqual(len(replies(text)), 1)
            check_metadata(self, replies(text)[0])
            self.assertEqual(err, "")

    def test_decline_initialization_does_not_construct_any_ledger(self):
        for choice in ("no", "submit", " SUBMIT", "SUBMIT ", ""):
            with self.subTest(choice=choice), patch("pool_session.PoolLedger") as constructor:
                status, text, err = console(choice + "\ncredit\n")
                self.assertEqual(status, 0)
                constructor.assert_not_called()
                self.assertEqual(replies(text), [])
                self.assertEqual(err, "")

    def test_mutation_preview_flush_and_literal_confirmation_then_one_dispatch(self):
        output = io.StringIO()
        flushed = []
        output.flush = lambda: flushed.append(output.getvalue())
        with patch("pool_console.dispatch_request", wraps=dispatch_request) as dispatch:
            class Input(io.StringIO):
                def readline(inner):
                    line = super().readline()
                    if line == "SUBMIT\n" and '"operation":"credit"' in output.getvalue():
                        self.assertEqual(dispatch.call_count, 0)
                        self.assertIn('"source_ref":"source"', flushed[-1])
                        self.assertIn('"amount":2', flushed[-1])
                    return line

            status, text, err = console("", source=Input(
                "SUBMIT\ncredit\nPROTOCOL_REVENUE\n+2\nsource\nSUBMIT\nquit\n"), output=output)
            self.assertEqual(status, 0)
            self.assertEqual(dispatch.call_count, 1)
            self.assertEqual(dispatch.call_args.args[1], {"operation": "credit", "arguments": {
                "pool": "PROTOCOL_REVENUE", "amount": 2, "source_ref": "source"}})
            self.assertEqual(replies(text)[-1]["view"]["balances"]["PROTOCOL_REVENUE"], 4)
            self.assertEqual(err, "")

    def test_declined_mutations_and_eof_at_every_prompt_do_not_dispatch(self):
        fields = ["SUBMIT", "credit", "PROTOCOL_REVENUE", "1", "source", "SUBMIT"]
        for count in range(len(fields)):
            text = "\n".join(fields[:count]) + ("\n" if count else "")
            with self.subTest(count=count), \
                    patch("pool_console.dispatch_request", wraps=dispatch_request) as dispatch, \
                    patch("pool_console.PoolSession", wraps=PoolSession) as constructor:
                status, _, err = console(text)
                self.assertEqual(status, 2)
                self.assertEqual(json.loads(err)["error"]["type"], "EOFError")
                dispatch.assert_not_called()
                self.assertEqual(constructor.call_count, int(count > 0))
        for action in ("credit", "spend"):
            for choice in ("no", "submit", " SUBMIT", "SUBMIT ", ""):
                with self.subTest(action=action, choice=choice), \
                        patch("pool_console.dispatch_request", wraps=dispatch_request) as dispatch:
                    status, text, err = console(
                        f"SUBMIT\n{action}\nPROTOCOL_REVENUE\n1\nref\n{choice}\nview\nquit\n")
                    self.assertEqual(status, 0)
                    self.assertEqual(dispatch.call_count, 1)
                    self.assertEqual(dispatch.call_args.args[1]["operation"], "view")
                    self.assertEqual(replies(text)[-1]["view"], PoolLedger(opening()).view())
                    self.assertEqual(err, "")

    def test_all_mutations_call_selected_model_once(self):
        with patch.object(PoolLedger, "credit", autospec=True, side_effect=PoolLedger.credit) as credit, \
                patch.object(PoolLedger, "spend", autospec=True, side_effect=PoolLedger.spend) as spend, \
                patch.object(PoolLedger, "view", autospec=True, side_effect=PoolLedger.view) as view:
            status, _, _ = console("SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\nref\nSUBMIT\n"
                                   "spend\nTOKEN_TREASURY_REWARD\n1\nref\nSUBMIT\nview\nquit\n")
            self.assertEqual(status, 0)
            self.assertEqual(credit.call_count, 1)
            self.assertEqual(spend.call_count, 1)
            self.assertEqual(view.call_count, 3)  # Model internal reads counted separately.

    def test_invalid_integer_menu_unicode_and_empty_reference(self):
        for raw in ("1.0", "1e0", "true", "null", " 1", "1 ", "", "١", "1" * 5000):
            with self.subTest(raw=raw[:40]), patch("pool_console.dispatch_request") as dispatch:
                status, _, err = console("SUBMIT\ncredit\nPROTOCOL_REVENUE\n" + raw + "\nref\nSUBMIT\n")
                self.assertEqual(status, 2)
                self.assertEqual(json.loads(err)["error"]["type"], "FixtureError")
                dispatch.assert_not_called()
        for text in ("SUBMIT\ntransfer\n", "SUBMIT\ncredit\n\ud800\n"):
            with patch("pool_console.dispatch_request") as dispatch:
                self.assertEqual(console(text)[0], 2)
                dispatch.assert_not_called()
        # Strings are forwarded verbatim, including invalid domain refs; no stripping/defaulting.
        for ref in ("", " bad "):
            status, text, err = console(f"SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\n{ref}\nSUBMIT\nview\nquit\n")
            self.assertEqual(status, 1)
            self.assertEqual(replies(text)[1]["error"], {"code": "INVALID_ID"})
            self.assertEqual(replies(text)[-1]["view"], PoolLedger(opening()).view())
            self.assertEqual(err, "")

    def test_preview_and_confirmation_write_flush_failures_fence_dispatch(self):
        class FailingOutput(io.StringIO):
            def __init__(self, target, flush):
                super().__init__()
                self.target, self.on_flush = target, flush

            def write(inner, value):
                if not inner.on_flush and inner.target in value:
                    raise OSError("preview output failed")
                return super().write(value)

            def flush(inner):
                if inner.on_flush and inner.target in inner.getvalue():
                    raise OSError("preview flush failed")

        for target in ('PREVIEW ', '"operation":"credit"'):
            for flush in (False, True):
                with self.subTest(target=target, flush=flush), \
                        patch("pool_console.dispatch_request") as dispatch, \
                    patch("pool_console.PoolSession", wraps=PoolSession) as constructor:
                    status, _, err = console(
                        "SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\nsource\nSUBMIT\nquit\n",
                        output=FailingOutput(target, flush))
                    self.assertEqual(status, 2)
                    dispatch.assert_not_called()
                    self.assertEqual(constructor.call_count, int('credit' in target))
                    self.assertIn("OSError", err)

    def test_output_failure_after_mutation_does_not_rollback_retry_or_continue(self):
        class Output(io.StringIO):
            def write(inner, value):
                if '"operation":"credit"' in value and '"provenance"' in value:
                    raise BrokenPipeError("after mutation")
                return super().write(value)

        with patch("pool_console.dispatch_request", wraps=dispatch_request) as dispatch:
            status, _, err = console("SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\nref\nSUBMIT\n"
                                     "spend\nPROTOCOL_REVENUE\n1\nref\nSUBMIT\nquit\n", output=Output())
            self.assertEqual(status, 2)
            self.assertEqual(dispatch.call_count, 1)
            session = dispatch.call_args.args[0]
            self.assertEqual(session.view()["balances"]["PROTOCOL_REVENUE"], 3)
            self.assertIn("BrokenPipeError", err)

    def test_confirmation_prompt_failure_and_eof_after_one_action_do_not_dispatch_again(self):
        class Output(io.StringIO):
            def write(inner, value):
                if value.startswith("Literal SUBMIT") and '"operation":"credit"' in inner.getvalue():
                    raise OSError("confirmation prompt failed")
                return super().write(value)

        with patch("pool_console.dispatch_request") as dispatch:
            status, _, _ = console("SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\nref\nSUBMIT\n", output=Output())
            self.assertEqual(status, 2)
            dispatch.assert_not_called()
        with patch("pool_console.dispatch_request", wraps=dispatch_request) as dispatch:
            status, _, err = console("SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\nref\nSUBMIT\n")
            self.assertEqual(status, 2)
            self.assertEqual(dispatch.call_count, 1)
            self.assertEqual(dispatch.call_args.args[0].view()["balances"]["PROTOCOL_REVENUE"], 3)
            self.assertIn("EOFError", err)

    def test_constructor_rejection_and_exact_large_console_amount(self):
        with patch("pool_console.dispatch_request") as dispatch:
            errors = io.StringIO()
            status = run_console({}, input_stream=io.StringIO("SUBMIT\ncredit\n"),
                                 output_stream=io.StringIO(), error_stream=errors)
            self.assertEqual(status, 2)
            self.assertEqual(json.loads(errors.getvalue())["error"], {"code": "POOL_BALANCES_REQUIRED"})
            dispatch.assert_not_called()
        with patch("pool_console.dispatch_request", wraps=dispatch_request) as dispatch:
            status, text, err = console("SUBMIT\ncredit\nPROTOCOL_REVENUE\n9007199254740993\nref\nSUBMIT\nquit\n")
            self.assertEqual(status, 1)
            self.assertEqual(dispatch.call_args.args[1]["arguments"]["amount"], 9007199254740993)
            self.assertIs(type(dispatch.call_args.args[1]["arguments"]["amount"]), int)
            self.assertEqual(replies(text)[-1]["error"], {"code": "INVALID_AMOUNT"})
            self.assertEqual(err, "")

    def test_interruption_read_failure_and_diagnostic_failure_stop(self):
        for error in (KeyboardInterrupt(), OSError("read failed"), UnicodeError("bad input")):
            source = io.StringIO()
            source.readline = Mock(side_effect=["SUBMIT\n", "credit\n", error])
            with patch("pool_console.dispatch_request") as dispatch:
                self.assertEqual(console("", source=source)[0], 2)
                dispatch.assert_not_called()
        errors = io.StringIO()
        errors.write = lambda value: (_ for _ in ()).throw(OSError("diagnostic failed"))
        self.assertEqual(console("", errors=errors)[0], 2)

    def test_real_guided_journey_and_boundaries(self):
        for name, status in (("journey", 0), ("boundaries", 1)):
            path = HERE / f"fixtures/pool_console_{name}.txt"
            process = subprocess.run([sys.executable, str(HERE / "pool_console.py"),
                                      "--fixture", str(FIXTURE)], input=path.read_bytes(),
                                     capture_output=True, timeout=15)
            self.assertEqual(process.returncode, status, process.stderr)
            self.assertEqual(process.stderr, b"")
            output = process.stdout.decode("utf-8")
            actual = replies(output)
            for reply in actual:
                check_metadata(self, reply)
            # Independent CLI process uses exactly the explicitly confirmed requests.
            from test_pool_cli import cli
            direct = cli(requests=HERE / f"fixtures/pool_{name}.jsonl")
            self.assertEqual(actual, [json.loads(line) for line in direct.stdout.splitlines()])
            if name == "boundaries":
                self.assertIn("Request declined; no dispatch.", output)
                self.assertEqual(actual[-1]["view"], PoolLedger(opening()).view())


if __name__ == "__main__":
    unittest.main()
