"""Explicit child mode, confirmation boundaries, compatibility and cleanup."""

import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from pool_client import PoolClient, PoolTransportUncertainty
from pool_console import main, run_console
from pool_session import initialized_reply
from test_pool_console import console, replies
from test_pool_session import FIXTURE, opening, request


HERE = Path(__file__).parent


def live(text, *, output=None, source=None):
    output = output if output is not None else io.StringIO()
    errors = io.StringIO()
    status = run_console(opening(), fixture=FIXTURE, cleanup_timeout=1,
                         input_stream=source if source is not None else io.StringIO(text),
                         output_stream=output, error_stream=errors)
    return status, output.getvalue(), errors.getvalue()


class PoolConsoleSubprocessTests(unittest.TestCase):
    def test_real_console_modes_have_identical_complete_journeys(self):
        for name, expected_status in (("journey", 0), ("boundaries", 1)):
            data = (HERE / f"fixtures/pool_console_{name}.txt").read_bytes()
            expected = console(data.decode())
            for options in ([], ["--mode", "in-process"],
                            ["--mode", "subprocess", "--cleanup-timeout", "1"]):
                with self.subTest(name=name, options=options):
                    result = subprocess.run([sys.executable, str(HERE / "pool_console.py"),
                                             "--fixture", str(FIXTURE), *options], input=data,
                                            capture_output=True, timeout=15)
                    self.assertEqual(result.returncode, expected_status, result.stderr)
                    self.assertEqual(result.stdout.decode(), expected[1])
                    self.assertEqual(result.stderr.decode(), expected[2])

    def test_launch_and_mutation_follow_flushed_confirmation_only(self):
        output = io.StringIO()
        original_launch, original_request = PoolClient.launch, PoolClient.request
        clients, sent = [], []

        def launch(*args, **kwargs):
            self.assertIn('"operation":"initialize"', output.getvalue())
            self.assertIn("Literal SUBMIT confirms", output.getvalue())
            self.assertEqual(kwargs["expected_opening_balances"], opening())
            client = original_launch(*args, **kwargs)
            clients.append(client)
            return client

        def submit(client, item):
            sent.append(item)
            if item["operation"] != "view":
                self.assertIn('"operation":"credit"', output.getvalue())
            return original_request(client, item)

        text = ("SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\nref\nno\n"
                "spend\nPROTOCOL_REVENUE\n1\nref\nsubmit\n"
                "credit\nPROTOCOL_REVENUE\n1\nref\nSUBMIT\nview\nquit\n")
        with patch("pool_console.PoolClient.launch", side_effect=launch) as launched, \
                patch.object(PoolClient, "request", autospec=True, side_effect=submit):
            result = live(text, output=output)
        self.assertEqual(result[0], 0, result[2])
        launched.assert_called_once()
        self.assertEqual(sent, [request("credit"), request("view")])
        self.assertEqual(len(replies(result[1])), 3)  # init and two explicit requests
        self.assertEqual(len(clients), 1)
        self.assertIsNotNone(clients[0]._process.returncode)
        self.assertTrue(clients[0]._process.stdout.closed)

    def test_declined_eof_or_interrupted_initialization_launches_nothing(self):
        class BrokenInput:
            def __init__(self, error):
                self.error = error

            def readline(self):
                raise self.error

        with patch("pool_console.PoolClient.launch") as launch:
            for choice in ("no\n", "submit\n", "\n", ""):
                result = live(choice)
                self.assertEqual(result[0], 2 if choice == "" else 0)
            for error in (KeyboardInterrupt(), OSError("input lost")):
                self.assertEqual(live("", source=BrokenInput(error))[0], 2)
            launch.assert_not_called()

    def test_confirmed_opening_is_detached_before_preview(self):
        balances = opening()

        class ChangingInput(io.StringIO):
            def readline(self):
                balances["PROTOCOL_REVENUE"] = 99
                return super().readline()

        client = Mock(initialized_reply=initialized_reply(opening()), domain_refused=False)
        client.close.return_value = 0
        with patch("pool_console.PoolClient.launch", return_value=client) as launch:
            status = run_console(balances, fixture=FIXTURE, cleanup_timeout=1,
                                 input_stream=ChangingInput("SUBMIT\nquit\n"),
                                 output_stream=io.StringIO(), error_stream=io.StringIO())
        self.assertEqual(status, 0)
        self.assertEqual(launch.call_args.kwargs["expected_opening_balances"], opening())

    def test_initialization_preview_and_confirmation_output_failures_launch_nothing(self):
        class BrokenOutput(io.StringIO):
            def __init__(self, target, flush):
                super().__init__()
                self.target, self.fail_flush = target, flush
                self.hit = False

            def write(self, value):
                if self.target in value:
                    self.hit = True
                    if not self.fail_flush:
                        raise OSError("output lost")
                return super().write(value)

            def flush(self):
                if self.hit and self.fail_flush:
                    raise OSError("flush lost")
                return super().flush()

        for target in ("Synthetic POINT_F4", "PREVIEW", "Literal SUBMIT"):
            for flush in (False, True):
                with self.subTest(target=target, flush=flush), patch("pool_console.PoolClient.launch") as launch:
                    self.assertEqual(live("SUBMIT\nview\nquit\n", output=BrokenOutput(target, flush))[0], 2)
                    launch.assert_not_called()

    def test_every_post_launch_terminal_path_closes_and_stops(self):
        class BrokenInput:
            def __init__(self, prefix, error):
                self.prefix, self.error = iter(prefix.splitlines(True)), error

            def readline(self):
                try:
                    return next(self.prefix)
                except StopIteration:
                    raise self.error

        cases = ["SUBMIT\n", "SUBMIT\nunknown\n", "SUBMIT\ncredit\n", "SUBMIT\ncredit\nP\n",
                 "SUBMIT\ncredit\nP\n1\n", "SUBMIT\ncredit\nP\n1\nref\n",
                 "SUBMIT\ncredit\nP\n1.0\n", "SUBMIT\ncredit\nP\n1\nref\nno\n"]
        sources = [io.StringIO(text) for text in cases]
        sources += [BrokenInput("SUBMIT\n", error) for error in (KeyboardInterrupt(), OSError("lost input"))]
        for source in sources:
            with self.subTest(source=source):
                client = Mock(initialized_reply=initialized_reply(opening()), domain_refused=False)
                client.close.return_value = 0
                with patch("pool_console.PoolClient.launch", return_value=client):
                    self.assertEqual(live("", source=source)[0], 2)
                client.close.assert_called_once()
                client.request.assert_not_called()

    def test_failed_output_after_real_mutation_closes_without_next_dispatch(self):
        class BrokenOutput(io.StringIO):
            def write(self, value):
                if '"operation":"credit"' in value and not value.startswith("PREVIEW"):
                    raise OSError("response display lost")
                return super().write(value)

        clients, sent = [], []
        launch, submit = PoolClient.launch, PoolClient.request

        def start(*args, **kwargs):
            client = launch(*args, **kwargs)
            clients.append(client)
            return client

        def send(client, item):
            sent.append(item)
            return submit(client, item)

        with patch("pool_console.PoolClient.launch", side_effect=start), \
                patch.object(PoolClient, "request", autospec=True, side_effect=send):
            status, _, error = live("SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\nref\nSUBMIT\nview\nquit\n",
                                    output=BrokenOutput())
        self.assertEqual(status, 2, error)
        self.assertEqual(sent, [request("credit")])
        self.assertEqual(clients[0]._process.returncode, 0)

    def test_post_launch_output_failure_before_mutation_sends_nothing(self):
        class BrokenOutput(io.StringIO):
            def __init__(self, target, fail_flush):
                super().__init__()
                self.target, self.fail_flush, self.hit = target, fail_flush, False

            def write(self, value):
                if self.target in value:
                    self.hit = True
                    if not self.fail_flush:
                        raise OSError("display lost")
                return super().write(value)

            def flush(self):
                if self.hit and self.fail_flush:
                    raise OSError("flush lost")

        for target in ('"initialized":', 'PREVIEW {"arguments":{"amount":', 'source_ref (verbatim string)'):
            for flush in (False, True):
                client = Mock(initialized_reply=initialized_reply(opening()), domain_refused=False)
                client.close.return_value = 0
                with self.subTest(target=target, flush=flush), \
                        patch("pool_console.PoolClient.launch", return_value=client):
                    status = live("SUBMIT\ncredit\nPROTOCOL_REVENUE\n1\nref\nSUBMIT\nquit\n",
                                  output=BrokenOutput(target, flush))[0]
                self.assertEqual(status, 2)
                client.request.assert_not_called()
                client.close.assert_called_once()

    def test_transport_and_typed_errors_stop_and_close(self):
        for failure in (PoolTransportUncertainty("request", request("view"), b"x", b"{"),
                        KeyboardInterrupt(), OSError("lost")):
            client = Mock(initialized_reply=initialized_reply(opening()), domain_refused=False)
            client.request.side_effect = failure
            client.close.return_value = 0
            with self.subTest(failure=failure), patch("pool_console.PoolClient.launch", return_value=client):
                self.assertEqual(live("SUBMIT\nview\nview\nquit\n")[0], 2)
            client.request.assert_called_once_with(request("view"))
            client.close.assert_called_once()
        client = Mock(initialized_reply=initialized_reply(opening()), domain_refused=False)
        client.request.return_value = {"error": {"type": "FixtureError", "message": "bad"}}
        client.close.return_value = 2
        with patch("pool_console.PoolClient.launch", return_value=client):
            self.assertEqual(live("SUBMIT\nview\nquit\n")[0], 2)
        client.close.assert_called_once()
        client.request.assert_called_once()

    def test_unexpected_exit_and_cleanup_failure_are_terminal(self):
        for code, refused, expected in ((0, False, 0), (1, False, 2), (1, True, 0), (2, False, 2), (-9, False, 2)):
            client = Mock(initialized_reply=initialized_reply(opening()), domain_refused=refused)
            client.close.return_value = code
            with self.subTest(code=code, refused=refused), patch("pool_console.PoolClient.launch", return_value=client):
                self.assertEqual(live("SUBMIT\nquit\n")[0], expected)
            client.close.assert_called_once()
        client.close.side_effect = OSError("cleanup failed")
        with patch("pool_console.PoolClient.launch", return_value=client):
            self.assertEqual(live("SUBMIT\nquit\n")[0], 2)

    def test_option_combinations_reject_before_launch(self):
        invalid = [["--mode", "subprocess", "--guided-init", "--cleanup-timeout", "1"],
                   ["--mode", "in-process", "--fixture", str(FIXTURE), "--cleanup-timeout", "1"],
                   ["--mode", "subprocess", "--fixture", str(FIXTURE)]]
        invalid += [["--mode", "subprocess", "--fixture", str(FIXTURE), "--cleanup-timeout", value]
                    for value in ("0", "-1", "nan", "inf")]
        with patch("pool_console.PoolClient.launch") as launch, patch("sys.stderr", io.StringIO()):
            for args in invalid:
                with self.subTest(args=args):
                    self.assertEqual(main(args), 2)
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
