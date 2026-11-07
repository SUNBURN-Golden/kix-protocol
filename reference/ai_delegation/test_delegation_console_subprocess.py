"""Source-informed console/child composition, confirmations and terminal failures."""

from copy import deepcopy
import io
import json
import os
import subprocess
import sys
import threading
import unittest
from unittest.mock import Mock, patch

from delegation_client import DelegationClient, DelegationClientStateError, DelegationTransportUncertainty
from delegation_console import main, run_subprocess_console
from delegation_fixture import load_fixture
import test_delegation_client as client_tests
from test_delegation_console import CONSOLE, FIXTURES, FailingOutput, desk_requests, entered, records


FIXTURE = client_tests.FIXTURE
ISSUE, VIEW = client_tests.ISSUE, client_tests.VIEW
EXECUTE = {"operation": "attempt_execution", "arguments": {"actor": "human-a", "proposal_id": "p-approved"}}


def diagnostics(text):
    return [json.loads(line.removeprefix("FENCED: ")) for line in text.splitlines()]


class DelegationConsoleSubprocessTests(unittest.TestCase):
    def drive(self, text="quit\n", *, source=None, output=None, configure=None, fixture=FIXTURE):
        """One real child; test deadline only, no polling/restart/fallback."""
        output = io.StringIO() if output is None else output
        errors, clients, writes, result = io.StringIO(), [], [], []
        launch = DelegationClient.launch
        def owned(*args, **kwargs):
            client = launch(*args, **kwargs)
            clients.append(client)
            self.addCleanup(client.close)
            write = client._process.stdin.write
            def record(raw):
                writes.append(client_tests.decode_json(raw.decode("utf-8")))
                return write(raw)
            client._process.stdin.write = record
            if configure:
                configure(client)
            return client
        done = threading.Event()
        def run():
            try:
                result.append(run_subprocess_console(fixture, cleanup_timeout=1,
                    input_stream=io.StringIO(text) if source is None else source,
                    output_stream=output, error_stream=errors))
            except BaseException as error:
                result.append(error)
            finally:
                done.set()
        with patch("delegation_console.DelegationClient.launch", side_effect=owned) as launched, patch(
                "delegation_console.load_fixture", side_effect=AssertionError("in-process fixture fallback")), patch(
                "delegation_console.dispatch_request", side_effect=AssertionError("in-process dispatch fallback")), patch(
                "socket.socket", side_effect=AssertionError("socket")), patch(
                "socket.create_connection", side_effect=AssertionError("connection")):
            thread = threading.Thread(target=run)
            thread.start()
            completed = done.wait(10)
            if not completed:
                for client in clients:
                    client._process.kill()
            thread.join(10)
            self.assertFalse(thread.is_alive(), "console did not stop within harness deadline")
            self.assertTrue(completed, "console must receive replies before input EOF")
            launched.assert_called_once_with(fixture, cleanup_timeout=1)
        if isinstance(result[0], BaseException):
            raise result[0]
        self.assertEqual(len(clients), 1)
        process = clients[0]._process
        self.assertIsNotNone(process.returncode)
        self.assertTrue(process.stdin.closed)
        self.assertTrue(process.stdout.closed)
        if os.name == "posix":
            with self.assertRaises(ChildProcessError):
                os.waitpid(process.pid, os.WNOHANG)
        return result[0], writes, output.getvalue(), errors.getvalue(), clients[0]

    def test_real_child_journey_and_replay_match_existing_fixtures(self):
        for name, vector, code in (("journey", "lifecycle", 0), ("replay", "replay", 1)):
            text = (FIXTURES / ("delegation_console_" + name + ".txt")).read_text()
            status, writes, output, errors, client = self.drive(text)
            self.assertEqual((status, errors), (code, ""))
            self.assertEqual(writes, desk_requests(vector))
            expected_session = load_fixture(FIXTURE)
            expected = [client_tests.direct(expected_session, row) for row in writes]
            self.assertEqual(records(output, "desk="), expected)
            self.assertEqual(records(output, "proposed="), writes)
            self.assertEqual(client.last_reply, expected[-1])
            for reply in expected:
                body = reply.get("view") or reply.get("receipt")
                if body:
                    body = body.get("grant") or body.get("proposal") or body
                    for flag in client_tests.FALSE_FLAGS:
                        self.assertIs(body[flag], False)
                    if "effects_executed" in body:
                        self.assertIs(body["effects_executed"], False)

    def test_interactive_response_dependent_reads_and_preview_before_confirmation(self):
        class FlushedOutput(io.StringIO):
            preview_flushed = False
            def write(self, text):
                if "proposed=" in text:
                    self.preview_flushed = False
                return super().write(text)
            def flush(self):
                self.preview_flushed = True
                return super().flush()
        output = FlushedOutput()
        state = {"client": None, "lines": iter(entered(ISSUE).splitlines(True)), "stage": 0}
        def configure(client):
            state["client"] = client
            client.request = Mock(wraps=client.request)
        test = self
        class Interactive:
            def readline(self):
                try:
                    line = next(state["lines"])
                except StopIteration:
                    reply = records(output.getvalue(), "desk=")[-1]
                    if state["stage"] == 0:
                        test.assertFalse(state["client"]._process.stdin.closed)
                        derived = {"operation": "view_grant", "arguments": {
                            "grant_id": reply["receipt"]["grant"]["grant_id"]}}
                        state["lines"], state["stage"] = iter(entered(derived).splitlines(True)), 1
                        line = next(state["lines"])
                    else:
                        return "quit\n"
                if line == "SUBMIT\n":
                    preview = records(output.getvalue(), "proposed=")[-1]
                    test.assertIn(preview["operation"], {"issue_grant", "view_grant"})
                    test.assertTrue(output.preview_flushed)
                    # No request from this preview has yet reached the client.
                    test.assertEqual(state["client"].request.call_count, state["stage"])
                    test.assertEqual(len(records(output.getvalue(), "desk=")), state["stage"])
                return line
        status, writes, text, errors, _ = self.drive(source=Interactive(), output=output, configure=configure)
        self.assertEqual((status, errors), (0, ""))
        self.assertEqual(writes, [ISSUE, VIEW])
        self.assertEqual(records(text, "desk=")[-1]["view"]["grant_id"], "g-1")

    def test_all_seven_selectors_confirm_once_declines_and_invalid_dispatch_nothing(self):
        examples = [ISSUE, desk_requests("lifecycle")[3], desk_requests("lifecycle")[4],
                    desk_requests("lifecycle")[11], VIEW,
                    {"operation": "view_proposal", "arguments": {"proposal_id": "p-approved"}}, EXECUTE]
        self.assertEqual(len({r["operation"] for r in examples}), 7)
        for confirmation in ("no", "", " SUBMIT", "SUBMIT "):
            status, writes, output, errors, _ = self.drive(
                "".join(entered(row, confirmation) for row in examples) + "quit\n")
            self.assertEqual((status, writes, errors), (0, [], ""))
            self.assertEqual(records(output, "proposed="), examples)
            self.assertEqual(records(output, "desk="), [])
        status, writes, output, errors, _ = self.drive(
            "unknown\ncall_tool\nagent-a\ng-1\nquery_subject\n{bad}\n"
            "issue_grant\nhuman-a\ng-1\nagent-a\ntrue\n" +
            "".join(entered(row) for row in examples) + "quit\n")
        self.assertEqual((status, errors), (1, ""))
        self.assertEqual(writes, examples)
        self.assertEqual(records(output, "proposed="), examples)
        self.assertEqual(len(records(output, "desk=")), 7)
        self.assertEqual(records(output, "desk=")[-1]["error"], {"code": "DELEGATED_EXECUTION_DISABLED"})

    def test_default_explicit_and_subprocess_cli_transcripts_are_identical(self):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("PYTHONUNBUFFERED", None)
        for name, code in (("journey", 0), ("replay", 1), ("boundaries", 1)):
            text = (FIXTURES / ("delegation_console_" + name + ".txt")).read_text()
            command = [sys.executable, str(CONSOLE), "--fixture", str(FIXTURE)]
            results = [subprocess.run(command + options, input=text, text=True, capture_output=True,
                                      timeout=15, env=env) for options in (
                [], ["--mode", "in-process"], ["--mode", "subprocess", "--cleanup-timeout", "1"])]
            for result in results:
                self.assertEqual((result.returncode, result.stderr, result.stdout), (code, "", results[0].stdout))

    def test_mode_isolation_and_cleanup_timeout_validation(self):
        with patch("delegation_console.load_fixture") as load, patch(
                "delegation_console.DelegationClient.launch") as launch, patch("sys.stderr", io.StringIO()):
            for options in (["--mode", "subprocess"], ["--cleanup-timeout", "1"], ["--mode", "invalid"]):
                with self.assertRaises(SystemExit) as error:
                    main(["--fixture", str(FIXTURE)] + options)
                self.assertEqual(error.exception.code, 2)
            load.assert_not_called()
            launch.assert_not_called()
        with patch("delegation_client.subprocess.Popen") as popen, patch("sys.stderr", io.StringIO()):
            for timeout in ("0", "-1", "nan", "inf", "-inf", "bad"):
                try:
                    status = main(["--fixture", str(FIXTURE), "--mode", "subprocess", "--cleanup-timeout=" + timeout])
                except SystemExit as error:
                    status = error.code
                self.assertEqual(status, 2)
            popen.assert_not_called()
        for options in ([], ["--mode", "in-process"]):
            with patch("delegation_console.load_fixture", wraps=load_fixture) as load, patch(
                    "delegation_console.DelegationClient.launch") as launch, patch(
                    "sys.stdin", io.StringIO("quit\n")), patch("sys.stdout", io.StringIO()):
                self.assertEqual(main(["--fixture", str(FIXTURE)] + options), 0)
            load.assert_called_once_with(FIXTURE)
            launch.assert_not_called()

    def test_quit_eof_interrupt_preview_and_render_failures_reap(self):
        for ending in ("quit", "eof", "interrupt", "preview", "preview-short", "preview-flush",
                       "render", "render-short", "render-flush"):
            kwargs = {}
            if ending.startswith(("preview", "render")):
                mode = ending.split("-", 1)[1] if "-" in ending else "write"
                kwargs["output"] = FailingOutput("proposed=" if ending.startswith("preview") else "desk=", mode)
            if ending == "interrupt":
                class Interrupted:
                    def readline(self):
                        raise KeyboardInterrupt("input interrupted")
                kwargs["source"] = Interrupted()
            text = entered(ISSUE) + ("quit\n" if ending != "eof" else "")
            status, writes, output, errors, client = self.drive(text, **kwargs)
            self.assertEqual(status, 0 if ending == "quit" else 2)
            self.assertEqual(writes, [] if ending == "interrupt" or ending.startswith("preview") else [ISSUE])
            if ending.startswith("render"):
                self.assertEqual(diagnostics(errors)[0]["last_reply"], client.last_reply)
            if ending == "quit":
                self.assertEqual(errors, "")
        status, writes, _, errors, _ = self.drive(entered(ISSUE).removesuffix("SUBMIT\n"))
        self.assertEqual((status, writes), (2, []))
        self.assertIn("EOFError", errors)

    def test_live_malformed_reply_and_child_exit_stop_queued_sentinel(self):
        raw = b'{"operation":'
        log, worker = client_tests.fault_worker(self, raw, exited=True)
        with patch("delegation_client.subprocess.Popen", side_effect=worker) as launched:
            status, writes, _, errors, client = self.drive(entered(ISSUE) + entered(VIEW) + "quit\n")
        self.assertEqual((status, writes), (2, [ISSUE]))
        self.assertEqual(client.uncertainty.reply_bytes, raw)
        self.assertEqual(diagnostics(errors)[0]["reply_bytes_hex"], raw.hex())
        self.assertEqual(client_tests.decode_json(log.read_text()), ISSUE)
        launched.assert_called_once()

    def test_startup_error_is_terminal_without_fallback(self):
        status, writes, output, errors, client = self.drive(entered(ISSUE) + entered(VIEW) + "quit\n",
            fixture=FIXTURE.with_name("absent-console-fixture.json"))
        self.assertEqual((status, writes), (2, [ISSUE]))
        self.assertEqual(client._process.returncode, 2)
        replies = records(output, "desk=")
        if replies:
            self.assertIsNone(replies[0]["operation"])
            self.assertEqual(replies[0]["error"]["type"], "FileNotFoundError")
            self.assertEqual(diagnostics(errors)[0]["last_reply"], replies[0])
        else:
            self.assertIsNotNone(client.uncertainty)  # Startup may close stdin before the first write.

    def test_terminal_envelopes_and_state_errors_stop_sentinel(self):
        for failure in (DelegationClientStateError("fenced"), KeyboardInterrupt(),
                        {"operation": "issue_grant", "provenance": client_tests.PROVENANCE,
                         "error": {"code": "MOCK_INVARIANT"}},
                        {"operation": "issue_grant", "provenance": client_tests.PROVENANCE,
                         "error": {"type": "FixtureError", "message": "bad"}}):
            client = Mock()
            client.close.return_value = 0
            if isinstance(failure, BaseException):
                client.request.side_effect = failure
            else:
                client.request.return_value = failure
            errors, output = io.StringIO(), io.StringIO()
            with patch("delegation_console.DelegationClient.launch", return_value=client):
                status = run_subprocess_console(FIXTURE, cleanup_timeout=1,
                    input_stream=io.StringIO(entered(ISSUE) + entered(VIEW) + "quit\n"),
                    output_stream=output, error_stream=errors)
            self.assertEqual(status, 2)
            client.request.assert_called_once_with(ISSUE)
            client.close.assert_called_once()
            if isinstance(failure, dict):
                self.assertEqual(records(output.getvalue(), "desk="), [failure])
                self.assertEqual(diagnostics(errors.getvalue())[0]["last_reply"], failure)

    def test_cleanup_failure_keeps_primary_cause_wire_and_last_reply(self):
        prior = client_tests.direct(load_fixture(FIXTURE), ISSUE)
        uncertainty = DelegationTransportUncertainty(deepcopy(VIEW), client_tests.wire(VIEW), b'{\xff')
        uncertainty.__cause__ = OSError("lost response")
        client = Mock()
        client.request.side_effect = [prior, uncertainty]
        client.close.side_effect = OSError("cleanup failed")
        output, errors = io.StringIO(), io.StringIO()
        with patch("delegation_console.DelegationClient.launch", return_value=client) as launch:
            status = run_subprocess_console(FIXTURE, cleanup_timeout=1,
                input_stream=io.StringIO(entered(ISSUE) + entered(VIEW) + entered(EXECUTE) + "quit\n"),
                output_stream=output, error_stream=errors)
        self.assertEqual(status, 2)
        self.assertEqual([call.args[0] for call in client.request.call_args_list], [ISSUE, VIEW])
        first, cleanup = diagnostics(errors.getvalue())
        self.assertEqual(first["last_reply"], prior)
        self.assertEqual(first["reply_bytes_hex"], "7bff")
        self.assertEqual(first["request_bytes_hex"], client_tests.wire(VIEW).hex())
        self.assertEqual(first["exceptions"][-1]["message"], "lost response")
        self.assertEqual(cleanup["last_reply"], prior)
        self.assertEqual(cleanup["exceptions"][0]["message"], "cleanup failed")
        client.close.assert_called_once()
        launch.assert_called_once()

    def test_unexpected_cleanup_exit_is_failure(self):
        for code in (1, 2, 7, -15):
            client = Mock()
            client.close.return_value = code
            errors = io.StringIO()
            with patch("delegation_console.DelegationClient.launch", return_value=client):
                status = run_subprocess_console(FIXTURE, cleanup_timeout=1, input_stream=io.StringIO("quit\n"),
                                               output_stream=io.StringIO(), error_stream=errors)
            self.assertEqual(status, 2)
            self.assertIn(f"exited with status {code}", errors.getvalue())
            client.request.assert_not_called()
            client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
