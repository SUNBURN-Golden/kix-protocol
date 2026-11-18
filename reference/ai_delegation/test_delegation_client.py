"""Source-informed live child and hostile transport tests; no business-model changes."""

from copy import deepcopy
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from ai_delegation_mock import AiDelegationError, FALSE_FLAGS, PROVENANCE, _canonical
from delegation_cli import _error
from delegation_client import DelegationClient, DelegationClientStateError, DelegationTransportUncertainty
from delegation_fixture import FixtureError, decode_json, load_fixture
from test_delegation_session import FIXTURES, requests


FIXTURE = FIXTURES / "delegation_session.json"
ISSUE = requests("lifecycle")[0]
VIEW = {"operation": "view_grant", "arguments": {"grant_id": "g-1"}}


def wire(value):
    return (_canonical(value) + "\n").encode("utf-8")


def direct(session, request):
    """Public session calls, bypassing CLI dispatch/client structural validation."""
    op = request["operation"]
    try:
        value = getattr(session, op)(**request["arguments"])
    except AiDelegationError as error:
        return _error(op, error)
    return {"operation": op, "provenance": PROVENANCE,
            "view" if op.startswith("view_") else "receipt": value}


def exchange(test, client, request):
    """Harness deadline only: a buffered child's reply must arrive before EOF."""
    done, result = threading.Event(), []
    def call():
        try:
            result.append(client.request(request))
        except BaseException as error:
            result.append(error)
        finally:
            done.set()
    thread = threading.Thread(target=call)
    thread.start()
    completed = done.wait(10)
    if not completed:
        client._process.kill()
    thread.join(10)
    test.assertFalse(thread.is_alive(), "test request did not stop")
    test.assertTrue(completed, "reply must arrive before stdin EOF")
    test.assertFalse(client._process.stdin.closed)
    if isinstance(result[0], BaseException):
        raise result[0]
    return result[0]


def fault_worker(test, raw, *, linger=False, stubborn=False, exited=False):
    directory = tempfile.TemporaryDirectory()
    test.addCleanup(directory.cleanup)
    log = Path(directory.name) / "request.jsonl"
    popen = subprocess.Popen
    # Install signal handler before the reply; ordinary buffered Python, no -u.
    code = ("import sys, pathlib, signal, time\n"
            + ("signal.signal(signal.SIGTERM, signal.SIG_IGN)\n" if stubborn else "")
            + f"pathlib.Path({str(log)!r}).write_bytes(sys.stdin.buffer.readline())\n"
            + f"sys.stdout.buffer.write({raw!r}); sys.stdout.buffer.flush()\n"
            + ("time.sleep(60)\n" if linger else "")
            + ("sys.exit(7)\n" if exited else ""))
    def worker(command, **kwargs):
        return popen([sys.executable, "-c", code], **kwargs)
    return log, worker


class DelegationClientTests(unittest.TestCase):
    def test_initialized_live_client_parity_and_detached_snapshots(self):
        fixture = decode_json(FIXTURE.read_text())
        expected_fixture = deepcopy(fixture)
        with patch("delegation_client.subprocess.Popen", wraps=subprocess.Popen) as launched, patch(
                "delegation_fixture.DelegationSession", side_effect=AssertionError("parent domain preflight")):
            initialized = DelegationClient.launch_from_fixture(fixture, cleanup_timeout=1)
        self.addCleanup(initialized.close)
        self.assertEqual(launched.call_args.args[0][-3:], ["--init-stdin", "--requests", "-"])
        launched.assert_called_once()
        fixture["human_principals"].clear()
        ack = initialized.initialized_reply
        self.assertEqual(ack, {"operation": None, "provenance": PROVENANCE, "initialized": expected_fixture})
        ack["initialized"]["ai_agents"].reverse()
        self.assertEqual(initialized.initialized_reply["initialized"], expected_fixture)
        file_client = self.launch()
        self.assertIsNone(file_client.initialized_reply)
        for row in requests("lifecycle") + requests("boundaries") + requests("replay"):
            reply = exchange(self, initialized, row)
            self.assertEqual(reply, exchange(self, file_client, row))
            self.assert_synthetic(reply)
        self.assertEqual(initialized.close(), file_client.close())

    def test_startup_ack_failure_fences_and_reaps_without_retry(self):
        fixture = decode_json(FIXTURE.read_text())
        ack = {"operation": None, "provenance": PROVENANCE, "initialized": fixture}
        malformed = [b"", b"{", b"\xff\n", b"{}\n", b"[]\n", wire(ack)[:-1],
                     b'{"operation":null,"operation":null}\n', wire({**ack, "extra": True}),
                     wire({**ack, "operation": "issue_grant"}), wire({**ack, "provenance": "REAL"}),
                     wire(_error(None, OSError("complete setup failure"))),
                     wire(_error(None, AiDelegationError("INVALID_ID")))]
        for key, value in (("fixture_version", True), ("fixture_version", 1.0), ("fixture_version", 2),
                           ("provenance", "REAL"), ("human_principals", []), ("ai_agents", None),
                           ("ai_agents", ["agent-b", "agent-a"])):
            malformed.append(wire({**ack, "initialized": {**fixture, key: value}}))
        for raw in malformed:
            with self.subTest(raw=raw):
                process = Mock(stdin=io.BytesIO(), stdout=io.BytesIO(raw), returncode=0)
                write = Mock(wraps=process.stdin.write)
                process.stdin.write = write
                clients = []
                original = DelegationClient.__init__
                def capture(client, *args):
                    original(client, *args)
                    clients.append(client)
                with patch("delegation_client.subprocess.Popen", return_value=process) as launched, patch.object(
                        DelegationClient, "__init__", capture):
                    with self.assertRaises(DelegationTransportUncertainty) as caught:
                        DelegationClient.launch_from_fixture(fixture, cleanup_timeout=1)
                self.assertEqual(caught.exception.request_bytes, wire(fixture))
                self.assertEqual(caught.exception.reply_bytes, raw)
                self.assertIsNotNone(caught.exception.__cause__)
                self.assert_fenced(clients[0])
                write.assert_called_once_with(wire(fixture))
                launched.assert_called_once()
                process.wait.assert_called_once_with(timeout=1)
                self.assertTrue(process.stdin.closed)
                self.assertTrue(process.stdout.closed)
                if b'complete setup failure' in raw:
                    self.assertEqual(caught.exception.last_reply, decode_json(raw))

    def test_startup_io_interruptions_and_cleanup_failure_preserve_primary(self):
        fixture = decode_json(FIXTURE.read_text())
        for fault in ("short", "none", "broken", "write_interrupt", "flush", "read", "interrupt", "cleanup"):
            with self.subTest(fault=fault):
                process = Mock(stdin=io.BytesIO(), stdout=io.BytesIO(), returncode=0)
                if fault in {"short", "none"}:
                    process.stdin.write = Mock(return_value=1 if fault == "short" else None)
                elif fault in {"broken", "write_interrupt"}:
                    process.stdin.write = Mock(side_effect=BrokenPipeError("write failed") if fault == "broken"
                                               else KeyboardInterrupt("write interrupted"))
                elif fault == "flush":
                    process.stdin.flush = Mock(side_effect=OSError("flush failed"))
                else:
                    process.stdout.read = Mock(side_effect=[b"{", KeyboardInterrupt("read interrupted")
                                                           if fault == "interrupt" else OSError("read failed")])
                if fault == "cleanup":
                    process.wait.side_effect = OSError("cleanup failed")
                with patch("delegation_client.subprocess.Popen", return_value=process) as launched:
                    with self.assertRaises(DelegationTransportUncertainty) as caught:
                        DelegationClient.launch_from_fixture(fixture, cleanup_timeout=1)
                self.assertEqual(caught.exception.request, fixture)
                self.assertEqual(caught.exception.reply_bytes, b"{" if fault in {"read", "interrupt", "cleanup"} else b"")
                if fault == "cleanup":
                    self.assertEqual(str(caught.exception.__cause__), "read failed")
                    self.assertEqual(str(caught.exception.cleanup_error), "cleanup failed")
                launched.assert_called_once()

    def test_startup_real_rejections_and_hostile_child_cleanup(self):
        fixture = decode_json(FIXTURE.read_text())
        for humans, agents, code in ((None, [], "INVALID_ID"), (["a", "a"], [], "INVALID_ID"),
                                     (["same"], ["same"], "MOCK_INVARIANT")):
            with self.assertRaises(DelegationTransportUncertainty) as caught:
                DelegationClient.launch_from_fixture({**fixture, "human_principals": humans, "ai_agents": agents},
                                                      cleanup_timeout=1)
            self.assertEqual(caught.exception.last_reply["error"], {"code": code})
        log, worker = fault_worker(self, b'{"wrong":true}\n', linger=True, stubborn=os.name == "posix")
        processes = []
        def capture(*args, **kwargs):
            processes.append(worker(*args, **kwargs))
            return processes[-1]
        with patch("delegation_client.subprocess.Popen", side_effect=capture) as launched:
            with self.assertRaises(DelegationTransportUncertainty):
                DelegationClient.launch_from_fixture(fixture, cleanup_timeout=0.1)
        self.assertEqual(decode_json(log.read_text()), fixture)
        launched.assert_called_once()
        self.assertEqual(processes[0].returncode, -9 if os.name == "posix" else -15)
        if os.name == "posix":
            with self.assertRaises(ChildProcessError):
                os.waitpid(processes[0].pid, os.WNOHANG)

    def test_startup_shape_and_timeout_validation_launch_nothing(self):
        fixture = decode_json(FIXTURE.read_text())
        with patch("delegation_client.subprocess.Popen") as launched:
            for bad in ({}, {**fixture, "fixture_version": True}, {**fixture, "human_principals": ["\ud800"]}):
                with self.assertRaises(FixtureError):
                    DelegationClient.launch_from_fixture(bad, cleanup_timeout=1)
            for timeout in (0, -1, True, None, "1", float("inf"), float("nan")):
                with self.assertRaises(ValueError):
                    DelegationClient.launch_from_fixture(fixture, cleanup_timeout=timeout)
            launched.assert_not_called()

    def test_startup_ack_requires_registry_types_even_if_echo_matches(self):
        fixture = decode_json(FIXTURE.read_text())
        for registry in (None, "agent-a", [1], [False], [{}]):
            submitted = {**fixture, "ai_agents": registry}
            raw = wire({"operation": None, "provenance": PROVENANCE, "initialized": submitted})
            process = Mock(stdin=io.BytesIO(), stdout=io.BytesIO(raw), returncode=0)
            with patch("delegation_client.subprocess.Popen", return_value=process) as launched:
                with self.assertRaises(DelegationTransportUncertainty) as caught:
                    DelegationClient.launch_from_fixture(submitted, cleanup_timeout=1)
            self.assertIsInstance(caught.exception.__cause__, FixtureError)
            self.assertEqual(caught.exception.reply_bytes, raw)
            launched.assert_called_once()
            process.wait.assert_called_once_with(timeout=1)

    def launch(self, fixture=FIXTURE, cleanup_timeout=1):
        client = DelegationClient.launch(fixture, cleanup_timeout=cleanup_timeout)
        self.addCleanup(client.close)
        return client

    def assert_fenced(self, client):
        with patch.object(client._process.stdin, "write", wraps=client._process.stdin.write) as write:
            with self.assertRaises(DelegationClientStateError):
                client.request(VIEW)
            write.assert_not_called()

    def assert_synthetic(self, reply):
        self.assertEqual(reply["provenance"], PROVENANCE)
        body = reply.get("view") or reply.get("receipt")
        if body:
            body = body.get("grant") or body.get("proposal") or body
            for flag in FALSE_FLAGS:
                self.assertIs(body[flag], False)
            if "effects_executed" in body:
                self.assertIs(body["effects_executed"], False)

    def test_live_lifecycle_before_eof(self):
        environment = dict(os.environ)
        environment.pop("PYTHONUNBUFFERED", None)
        with patch.dict(os.environ, environment, clear=True), patch(
                "delegation_client.subprocess.Popen", wraps=subprocess.Popen) as launched:
            client, session = self.launch(), load_fixture(FIXTURE)
            replies = []
            for request in requests("lifecycle"):
                reply = exchange(self, client, request)
                self.assertEqual(reply, direct(session, request))
                self.assert_synthetic(reply)
                replies.append(reply)
                # Subsequent explicit reads derive IDs from replies while stdin stays open.
                for kind in ("grant", "proposal"):
                    if kind in reply.get("receipt", {}):
                        row = {"operation": "view_" + kind, "arguments": {
                            kind + "_id": reply["receipt"][kind][kind + "_id"]}}
                        self.assertEqual(exchange(self, client, row), direct(session, row))
            self.assertEqual(replies[4]["receipt"]["proposal"]["phase"], "HUMAN_APPROVED")
            self.assertEqual(replies[12]["view"]["phase"], "VOIDED_BY_REVOCATION")
            self.assertEqual(client.close(), 0)
            command = launched.call_args.args[0]
            self.assertEqual(command, [sys.executable, str(Path(__file__).with_name("delegation_cli.py").resolve()),
                                      "--fixture", str(FIXTURE.resolve()), "--requests", "-"])
            self.assertIs(launched.call_args.kwargs["shell"], False)
            self.assertNotIn("stderr", launched.call_args.kwargs)
            launched.assert_called_once()

    def test_replay_current_records_and_explicit_disabled_execution(self):
        client, session = self.launch(), load_fixture(FIXTURE)
        replies = []
        for request in requests("replay"):
            reply = exchange(self, client, request)
            self.assertEqual(reply, direct(session, request))
            self.assert_synthetic(reply)
            replies.append(reply)
        self.assertEqual(replies[6]["receipt"]["proposal"]["phase"], "HUMAN_APPROVED")
        self.assertEqual(replies[13]["receipt"]["proposal"]["phase"], "WITHDRAWN")
        self.assertEqual(replies[18]["receipt"]["proposal"]["phase"], "VOIDED_BY_REVOCATION")
        self.assertEqual(replies[16]["receipt"]["grant"]["reason"], "first-reason")
        denied = {"operation": "attempt_execution", "arguments": {"actor": "human-a", "proposal_id": "p-approved"}}
        self.assertEqual(exchange(self, client, denied)["error"], {"code": "DELEGATED_EXECUTION_DISABLED"})
        self.assertEqual(exchange(self, client, VIEW), direct(session, VIEW))
        self.assertEqual(client.close(), 1)

    def test_invalid_local_requests_write_nothing_and_client_remains_usable(self):
        client = self.launch()
        bad = [[], ISSUE | {"extra": True}, ISSUE | {"operation": "delegate"},
               ISSUE | {"operation": []}, ISSUE | {"arguments": {}},
               ISSUE | {"arguments": ISSUE["arguments"] | {"extra": None}}]
        for value in (float("nan"), float("inf"), "\ud800", object(), (1,), {1: "key"}):
            bad.append(ISSUE | {"arguments": ISSUE["arguments"] | {"scope": value}})
        with patch.object(client._process.stdin, "write", wraps=client._process.stdin.write) as write:
            for request in bad:
                with self.subTest(request=repr(request)), self.assertRaises((FixtureError, TypeError)):
                    client.request(request)
            write.assert_not_called()
        self.assertEqual(exchange(self, client, ISSUE), direct(load_fixture(FIXTURE), ISSUE))
        # Nested invalid business inputs are sent unchanged and produce ordinary domain errors.
        bad_domain = ISSUE | {"arguments": ISSUE["arguments"] | {"limits": {}}}
        self.assertEqual(exchange(self, client, bad_domain)["error"], {"code": "LIMIT_REQUIRED"})
        self.assertIn("view", exchange(self, client, VIEW))

    def test_strict_frames_and_response_shapes_fence_with_raw_evidence(self):
        grant = direct(load_fixture(FIXTURE), ISSUE)
        session = load_fixture(FIXTURE)
        direct(session, ISSUE)
        proposal_request = requests("lifecycle")[3]
        proposal = direct(session, proposal_request)
        subject_request = requests("lifecycle")[2]
        subject = direct(session, subject_request)
        malformed = [(ISSUE, raw) for raw in (
            b"", b"\n", b"{}", b"{", b"\xff\n", b"[]\n", b"{} {}\n",
            b'{"operation":"issue_grant","operation":"issue_grant"}\n',
            b'{"x":NaN}\n', b'{"x":Infinity}\n', b'{"x":1e999}\n', b'{"x":"\\ud800"}\n')]
        def changed(request, template, path, value):
            reply = deepcopy(template)
            target = reply
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            malformed.append((request, wire(reply)))
        for path, value in ((["operation"], "view_grant"), (["operation"], None),
                            (["provenance"], "REAL"), (["extra"], True), (["view"], {}),
                            (["receipt", "duplicate"], 0), (["receipt", "extra"], False),
                            (["receipt", "grant", "grant_id"], "other"),
                            (["receipt", "grant", "issuer"], "other"),
                            (["receipt", "grant", "agent_id"], "other"),
                            (["receipt", "grant", "generation"], True),
                            (["receipt", "grant", "scope", "subjects"], {}),
                            (["receipt", "grant", "scope", "surfaces"], [1]),
                            (["receipt", "grant", "limits", "count_max"], False),
                            (["receipt", "grant", "period", "not_after"], 1.0),
                            (["receipt", "grant", "authority"], [1]),
                            (["receipt", "grant", "reason"], 0),
                            (["receipt", "grant", "revoked_at_seq"], False),
                            (["receipt", "grant", "lifecycle_authority"], "CHAIN"),
                            (["receipt", "grant", "provenance"], "REAL")):
            changed(ISSUE, grant, path, value)
        for flag in FALSE_FLAGS:
            for value in (True, 0):
                changed(ISSUE, grant, ["receipt", "grant", flag], value)
        missing = deepcopy(grant)
        del missing["receipt"]["grant"]["reason"]
        malformed.append((ISSUE, wire(missing)))
        for path, value in ((["receipt", "proposal", "effects_executed"], True),
                            (["receipt", "proposal", "effects_executed"], 0),
                            (["receipt", "proposal", "proposal_id"], "other"),
                            (["receipt", "proposal", "grant_id"], "other"),
                            (["receipt", "proposal", "amount"], False),
                            (["receipt", "proposal", "decision"], 0),
                            (["receipt", "proposal", "memo"], {"unknown": "x"}),
                            (["receipt", "proposal", "memo"], {"note": 1})):
            changed(proposal_request, proposal, path, value)
        for path, value in ((["receipt", "match", "surface"], "other"),
                            (["receipt", "match", "subject"], "other"),
                            (["receipt", "match", "in_scope"], 0)):
            changed(subject_request, subject, path, value)
        query_grant_request = requests("lifecycle")[1]
        query_grant = direct(session, query_grant_request)
        changed(query_grant_request, query_grant, ["receipt", "grant", "agent_id"], "other")
        revoke_request = requests("lifecycle")[11]
        revoked = direct(session, revoke_request)
        changed(revoke_request, revoked, ["receipt", "grant", "issuer"], "other")
        changed(VIEW, {"operation": "view_grant", "provenance": PROVENANCE,
                       "view": revoked["receipt"]["grant"]}, ["view", "grant_id"], "other")
        proposal_view_request = {"operation": "view_proposal", "arguments": {"proposal_id": "p-approved"}}
        changed(proposal_view_request, {"operation": "view_proposal", "provenance": PROVENANCE,
                                       "view": proposal["receipt"]["proposal"]}, ["view", "proposal_id"], "other")
        malformed.append((VIEW, wire(grant | {"operation": "view_grant"})))  # wrong payload kind
        execute = {"operation": "attempt_execution", "arguments": {"actor": "human-a", "proposal_id": "p"}}
        malformed.append((execute, wire(proposal | {"operation": "attempt_execution"})))
        for error in ({}, {"code": 1}, {"code": "X", "type": "X"}, {"type": "X", "message": 1}):
            malformed.append((ISSUE, wire({"operation": "issue_grant", "provenance": PROVENANCE, "error": error})))
        for request, raw in malformed:
            with self.subTest(raw=raw):
                # Deterministic injected pipes test the same read/write path; live
                # hostile workers below separately verify ownership and reaping.
                class Process:
                    stdin, stdout = io.BytesIO(), io.BytesIO(raw)
                client = DelegationClient(Process(), 1)
                with self.assertRaises(DelegationTransportUncertainty) as caught:
                    client.request(request)
                self.assertEqual(caught.exception.reply_bytes, raw)
                self.assertEqual(caught.exception.request_bytes, wire(request))
                self.assertIsNotNone(caught.exception.__cause__)
                self.assert_fenced(client)

    def test_terminal_complete_errors_are_retained(self):
        for op, detail in ((None, {"type": "OSError", "message": "setup failed"}),
                           (None, {"code": "MOCK_INVARIANT"}),
                           ("issue_grant", {"code": "MOCK_INVARIANT"}),
                           ("issue_grant", {"type": "FixtureError", "message": "bad shape"})):
            reply = {"operation": op, "provenance": PROVENANCE, "error": detail}
            log, worker = fault_worker(self, wire(reply))
            with patch("delegation_client.subprocess.Popen", side_effect=worker) as launch:
                client = self.launch()
                self.assertEqual(exchange(self, client, ISSUE), reply)
                self.assertEqual(client.last_reply, reply)
                self.assertIsNone(client.uncertainty)
                self.assert_fenced(client)
                self.assertEqual(client.close(), 0)
                self.assertEqual(decode_json(log.read_text()), ISSUE)
                launch.assert_called_once()

    def test_hostile_live_children_and_startup_failures_no_replacement(self):
        for raw in (b'{"operation":', b'{}\n', b'', wire(direct(load_fixture(FIXTURE), ISSUE) | {"operation": "view_grant"})):
            log, worker = fault_worker(self, raw, exited=True)
            with patch("delegation_client.subprocess.Popen", side_effect=worker) as launched:
                client = self.launch()
                with self.assertRaises(DelegationTransportUncertainty) as caught:
                    exchange(self, client, ISSUE)
                self.assertEqual(caught.exception.reply_bytes, raw)
                self.assert_fenced(client)
                self.assertEqual(client.close(), 7)
                self.assertEqual(decode_json(log.read_text()), ISSUE)
                launched.assert_called_once()
        client = self.launch(FIXTURE.with_name("absent-client-fixture.json"))
        try:
            reply = exchange(self, client, ISSUE)
        except DelegationTransportUncertainty as error:
            self.assertIsInstance(error.__cause__, BrokenPipeError)
        else:
            self.assertIsNone(reply["operation"])
            self.assertEqual(reply["error"]["type"], "FileNotFoundError")
        self.assert_fenced(client)
        self.assertEqual(client.close(), 2)

    def test_short_write_broken_pipe_flush_and_interruptions_retain_diagnostics(self):
        for fault in ("short", "none", "broken", "write_interrupt", "flush", "read", "interrupt"):
            with self.subTest(fault=fault):
                client = self.launch()
                first = exchange(self, client, ISSUE)
                first["receipt"]["grant"]["grant_id"] = "caller mutation"
                saved = deepcopy(client.last_reply)
                stream, method = client._process.stdin, "write"
                if fault in ("read", "interrupt"):
                    stream, method = client._process.stdout, "read"
                    options = {"side_effect": [b"{", KeyboardInterrupt() if fault == "interrupt" else OSError()]}
                elif fault == "flush":
                    method, options = "flush", {"side_effect": OSError()}
                elif fault in ("short", "none"):
                    options = {"return_value": 1 if fault == "short" else None}
                else:
                    options = {"side_effect": KeyboardInterrupt() if fault == "write_interrupt" else BrokenPipeError()}
                request = deepcopy(VIEW)
                with patch.object(stream, method, **options) as transport:
                    with self.assertRaises(DelegationTransportUncertainty) as caught:
                        client.request(request)
                    self.assertEqual(transport.call_count, 2 if method == "read" else 1)
                    self.assert_fenced(client)
                request["arguments"]["grant_id"] = "mutated after failure"
                self.assertEqual(caught.exception.request, VIEW)
                self.assertEqual(caught.exception.last_reply, saved)
                self.assertEqual(saved["receipt"]["grant"]["grant_id"], "g-1")
                self.assertEqual(caught.exception.reply_bytes, b"{" if method == "read" else b"")
                client.close()
                self.assertIs(client.uncertainty, caught.exception)

    def test_overlapping_request_and_cleanup_rejected_before_write(self):
        client = self.launch()
        entered, release = threading.Event(), threading.Event()
        read = client._process.stdout.read
        def held_read(size):
            entered.set()
            if not release.wait(10):
                raise AssertionError("harness release deadline")
            return read(size)
        result = []
        def call():
            try:
                result.append(client.request(ISSUE))
            except BaseException as error:
                result.append(error)
        with patch.object(client._process.stdout, "read", side_effect=held_read), patch.object(
                client._process.stdin, "write", wraps=client._process.stdin.write) as write:
            thread = threading.Thread(target=call)
            thread.start()
            try:
                self.assertTrue(entered.wait(10))
                with self.assertRaises(DelegationClientStateError):
                    client.request(VIEW)
                with self.assertRaises(DelegationClientStateError):
                    client.close()
                self.assertEqual(write.call_count, 1)
            finally:
                release.set()
                thread.join(10)
                if thread.is_alive():
                    client._process.kill()
                    thread.join(10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(result, [direct(load_fixture(FIXTURE), ISSUE)])
        self.assertIn("view", exchange(self, client, VIEW))

    def test_launch_validation_import_safety_and_context_cleanup(self):
        with patch("delegation_client.subprocess.Popen") as launch:
            for timeout in (0, -1, True, None, "1", float("inf"), float("nan")):
                with self.assertRaises(ValueError):
                    DelegationClient.launch(FIXTURE, cleanup_timeout=timeout)
            with self.assertRaises(TypeError):
                DelegationClient.launch(FIXTURE)
            launch.assert_not_called()
        result = subprocess.run([sys.executable, "-c", 'from unittest.mock import patch\n'
            'with patch("subprocess.Popen", side_effect=AssertionError("import launched")):\n'
            ' import delegation_client\n'], cwd=Path(__file__).parent, capture_output=True, timeout=10)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        client = self.launch()
        with self.assertRaisesRegex(RuntimeError, "caller failed"):
            with client:
                raise RuntimeError("caller failed")
        self.assertEqual(client.close(), 0)
        self.assert_fenced(client)
        self.assertTrue(client._process.stdin.closed)
        self.assertTrue(client._process.stdout.closed)

    @unittest.skipUnless(os.name == "posix", "POSIX signal/reaping evidence")
    def test_bounded_cleanup_terminates_kills_and_reaps_owned_child(self):
        for stubborn in (False, True):
            _, worker = fault_worker(self, wire(direct(load_fixture(FIXTURE), ISSUE)), linger=True, stubborn=stubborn)
            with patch("delegation_client.subprocess.Popen", side_effect=worker) as launched:
                client = self.launch(cleanup_timeout=0.1)
                exchange(self, client, ISSUE)
                with patch.object(client._process, "terminate", wraps=client._process.terminate) as terminate, patch.object(
                        client._process, "kill", wraps=client._process.kill) as kill:
                    self.assertEqual(client.close(), -9 if stubborn else -15)
                    self.assertEqual(client.close(), -9 if stubborn else -15)
                    terminate.assert_called_once()
                    self.assertEqual(kill.call_count, int(stubborn))
                launched.assert_called_once()
                with self.assertRaises(ChildProcessError):
                    os.waitpid(client._process.pid, os.WNOHANG)


if __name__ == "__main__":
    unittest.main()
