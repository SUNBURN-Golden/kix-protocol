"""Live child and hostile transport coverage; synthetic, source-informed evidence."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from reward_client import RewardClient, RewardClientStateError, RewardTransportUncertainty
from reward_cli import _error
from reward_fixture import FixtureError, decode_json, load_fixture
from test_reward_cli import invalid_initializations
from test_reward_session import FIXTURES, OPERATIONS, requests
from tl4_support import human_approval
from token_reward_model import ALWAYS_FALSE_FLAGS, PROVENANCE, TokenRewardError, _canonical


HERE = Path(__file__).parent
FIXTURE = FIXTURES / "reward_session.json"
OBSERVE = requests("participation")[0]
POOL = {"operation": "pool_view", "arguments": {}}
IDS = {"operation": "reward_ids", "arguments": {}}
VIEW = requests("participation")[-3]


def direct(session, request):
    """Public session calls, bypassing CLI dispatch and client validation."""
    operation = request["operation"]
    try:
        value = getattr(session, operation)(**request["arguments"])
    except TokenRewardError as error:
        return _error(operation, error)
    key = operation if operation in ("view", "reward_ids", "pool_view") else "receipt"
    return {"operation": operation, "provenance": PROVENANCE, key: value}


def wire(reply):
    return (_canonical(reply) + "\n").encode("utf-8")


class RewardClientTests(unittest.TestCase):
    def launch(self, fixture=FIXTURE, cleanup_timeout=1):
        client = RewardClient.launch(fixture, cleanup_timeout=cleanup_timeout)
        self.addCleanup(client.close)
        return client

    def exchange(self, client, request):
        # A test deadline proves the ordinary buffered child flushed before EOF.
        # No product response timeout, sleep, polling or retry.
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
        self.assertFalse(thread.is_alive(), "test request failed to stop")
        self.assertTrue(completed, "reply must arrive before stdin EOF")
        self.assertFalse(client._process.stdin.closed)
        if isinstance(result[0], BaseException):
            raise result[0]
        return result[0]

    def assert_synthetic(self, reply):
        self.assertEqual(reply["provenance"], PROVENANCE)
        reward = reply.get("view") or reply.get("receipt", {}).get("reward")
        for value in (reward, reply.get("receipt")):
            if value:
                for flag in ALWAYS_FALSE_FLAGS:
                    self.assertIs(value[flag], False)
        if reward:
            self.assertTrue(reward["non_transferable_until_chargeback_end"])

    def test_live_participation_before_eof_and_response_derived_reads(self):
        environment = dict(os.environ)
        environment.pop("PYTHONUNBUFFERED", None)
        with patch.dict(os.environ, environment, clear=True), \
                patch("reward_client.subprocess.Popen", wraps=subprocess.Popen) as launched:
            client, session = self.launch(), load_fixture(FIXTURE)
            self.assertEqual(self.exchange(client, IDS)["reward_ids"], [])
            rows = []
            for request in requests("participation"):
                reply = self.exchange(client, request)
                self.assertEqual(reply, direct(session, request))
                self.assert_synthetic(reply)
                rows.append(reply)
                if "receipt" in reply:
                    derived = {"operation": "view", "arguments": {
                        "reward_id_value": reply["receipt"]["reward"]["reward_id"]}}
                    self.assertEqual(self.exchange(client, derived), direct(session, derived))
            for original, replay in ((0, 5), (3, 6), (4, 7)):
                self.assertEqual(rows[replay]["receipt"],
                                 rows[original]["receipt"] | {"duplicate": True, "applied": None})
            self.assertEqual(rows[8]["view"]["phase"], "ISSUED")
            self.assertEqual(rows[9]["reward_ids"], [rows[8]["view"]["reward_id"]])
            pool = rows[-1]["pool_view"]
            self.assertEqual(pool["balances"]["TOKEN_TREASURY_REWARD"], 475)
            self.assertEqual(pool["spends"], [{"pool": "TOKEN_TREASURY_REWARD", "amount": 25,
                                                "program_ref": "synthetic-program"}])
            self.assertEqual(client.close(), 0)
            self.assertEqual(client.close(), 0)
            launched.assert_called_once()
            command = launched.call_args.args[0]
            self.assertEqual(command, [sys.executable, str((HERE / "reward_cli.py").resolve()),
                                      "--fixture", str(FIXTURE.resolve()), "--requests", "-"])
            self.assertFalse(launched.call_args.kwargs["shell"])
            self.assertNotIn("stderr", launched.call_args.kwargs)
            self.assertTrue(client._process.stdout.closed)

    def test_live_unknown_requires_separately_supplied_resolution(self):
        client, session = self.launch(), load_fixture(FIXTURE)
        replies = []
        for request in requests("unknown_pending"):
            reply = self.exchange(client, request)
            self.assertEqual(reply, direct(session, request))
            replies.append(reply)
        views = [row["view"] for row in replies if "view" in row]
        self.assertEqual([v["phase"] for v in views], ["UNKNOWN", "UNKNOWN"])
        self.assertEqual(views[-1]["resend_count"], 1)
        self.assertEqual(replies[-1]["pool_view"]["spends"], [])
        current = {"operation": "view", "arguments": {"reward_id_value": views[-1]["reward_id"]}}
        for request in (current, POOL, current):
            self.assertEqual(self.exchange(client, request), direct(session, request))
        self.assertEqual(self.exchange(client, current)["view"]["phase"], "UNKNOWN")
        resolved = []
        for request in requests("unknown_resolution"):
            reply = self.exchange(client, request)
            self.assertEqual(reply, direct(session, request))
            resolved.append(reply)
        self.assertTrue(resolved[1]["receipt"]["duplicate"])
        self.assertEqual(resolved[-2]["view"]["phase"], "ISSUED")
        self.assertEqual(len(resolved[-1]["pool_view"]["spends"]), 1)
        self.assertEqual(client.close(), 1)  # earlier domain refusals stay sticky

    def test_live_cancellation_and_krw_refund_are_distinct(self):
        client, session = self.launch(), load_fixture(FIXTURE)
        rows = []
        for request in requests("cancellation"):
            reply = self.exchange(client, request)
            self.assertEqual(reply, direct(session, request))
            self.assert_synthetic(reply)
            rows.append(reply)
        self.assertEqual([r["view"]["phase"] for r in rows if "view" in r],
                         ["REVERSED", "CLAWBACK_CLAIM"])
        refund = next(r["receipt"] for r in rows if r["operation"] == "observe_krw_refund")
        self.assertEqual(refund["reward"]["phase"], "ISSUED")
        self.assertEqual(refund["reward"]["krw_phase"], "KRW_REFUND_NOTED")
        self.assertNotEqual(refund["effect"]["krw_effect_id"], refund["reward"]["token_effect_id"])
        self.assertEqual(len(rows[-1]["pool_view"]["spends"]), 1)
        self.assertEqual(client.close(), 0)

    def test_live_boundary_refusals_allow_only_explicit_continuation(self):
        client, session = self.launch(), load_fixture(FIXTURE)
        for request in requests("boundaries"):
            self.assertEqual(self.exchange(client, request), direct(session, request))
        self.assertEqual(self.exchange(client, POOL)["pool_view"]["spends"], [])
        self.assertEqual(client.close(), 1)

    def test_all_operations_supersession_and_exact_caller_inputs(self):
        seen = set()
        for nulls in (False, True):
            client, session = self.launch(), load_fixture(FIXTURE)
            rows = deepcopy(requests("participation")[:5])
            if nulls:
                rows[2]["arguments"].update(abuse_kind=None, recipient_cap=None, program_cap=None)
                rows[3]["arguments"].update(budget_ceiling=None, execution_permit=None)
                rows[3]["arguments"]["approval_ref"]["prior_record"] = None
            else:
                for name in ("recipient_cap", "program_cap"):
                    rows[2]["arguments"].pop(name)
                rows[3]["arguments"].pop("budget_ceiling")
            rows.append({"operation": "supersede", "arguments": {
                "reward_id_value": VIEW["arguments"]["reward_id_value"],
                "idempotency_key": "explicit-supersede", "approval_ref": human_approval("supersession"),
                "rule_version": "synthetic-v2"}})
            original = deepcopy(rows)
            write_original = client._process.stdin.write
            with patch.object(client._process.stdin, "write", wraps=write_original) as write:
                for request in rows:
                    self.assertEqual(self.exchange(client, request), direct(session, request))
                    seen.add(request["operation"])
                submitted = [decode_json(call.args[0].decode()) for call in write.call_args_list]
            self.assertEqual(submitted, original)
            self.assertEqual(rows, original)
            self.assertEqual(client.close(), 0)
        for journey in ("unknown_pending", "cancellation", "participation"):
            seen.update(row["operation"] for row in requests(journey))
        self.assertEqual(seen, set(OPERATIONS))

    def fault_worker(self, reply, *, exited=False, linger=False, stubborn=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        log = Path(temporary.name) / "received"
        script = Path(temporary.name) / "worker.py"
        script.write_text("import os, sys, signal\nfrom pathlib import Path\n"
            + ("signal.signal(signal.SIGTERM, signal.SIG_IGN)\n" if stubborn else "")
            + "line = sys.stdin.buffer.readline()\n"
            + f"log = Path({str(log)!r})\nlog.write_bytes(line)\n"
            + ("os._exit(7)\n" if exited else
               f"sys.stdout.buffer.write({reply!r})\nsys.stdout.buffer.flush()\nos.close(1)\n")
            + ("while True: signal.pause()\n" if linger or stubborn else
               "log.write_bytes(line + sys.stdin.buffer.read())\n"))
        popen = subprocess.Popen
        def worker(command, **kwargs):
            return popen([sys.executable, str(script)], **kwargs)
        return log, worker

    def assert_fenced(self, client):
        for request in (POOL, OBSERVE, requests("unknown_resolution")[0]):
            with self.assertRaises(RewardClientStateError):
                client.request(request)

    def test_malformed_mismatched_incomplete_and_exited_children_fence(self):
        valid = direct(load_fixture(FIXTURE), OBSERVE)
        faults = [b"", b"{", wire(valid).rstrip(b"\n"), b"\xff\n", b"[]\n", b"null\n",
                  b"NaN\n", b"1e999\n", b'{"operation":"observe","operation":"observe"}\n',
                  wire(valid).replace(b'"reward_id":', b'"reward_id":"duplicate","reward_id":', 1),
                  wire(valid | {"operation": "view"}), wire(valid | {"operation": None}),
                  wire(valid | {"operation": []}), wire(valid | {"provenance": "LIVE"}),
                  wire(valid | {"error": {"code": "X"}}), wire(valid | {"extra": None}),
                  wire({k: v for k, v in valid.items() if k != "provenance"}),
                  wire({"operation": "observe", "provenance": PROVENANCE}),
                  wire(valid | {"receipt": []}), wire(valid | {"receipt": {}}),
                  wire(valid | {"receipt": {"reward": {"reward_id": 1}}})]
        for error in (None, [], {}, {"code": 2}, {"code": "X", "extra": 1},
                      {"type": "X"}, {"type": "X", "message": 2},
                      {"type": "X", "message": "bad", "code": "X"}):
            faults.append(wire({"operation": "observe", "provenance": PROVENANCE, "error": error}))
        faults.append(wire(valid).replace(b'"MOCK_TOKEN_REWARD_ONLY"', b'"\\ud800"'))
        for raw, exited in [(raw, False) for raw in faults] + [(b"", True)]:
            with self.subTest(raw=raw, exited=exited):
                log, worker = self.fault_worker(raw, exited=exited)
                with patch("reward_client.subprocess.Popen", side_effect=worker) as launched:
                    client = self.launch()
                    supplied = deepcopy(OBSERVE)
                    with self.assertRaises(RewardTransportUncertainty) as caught:
                        self.exchange(client, supplied)
                    uncertainty = caught.exception
                    self.assertEqual(uncertainty.reply_bytes, raw)
                    self.assertEqual(decode_json(uncertainty.request_bytes.decode()), OBSERVE)
                    supplied["arguments"]["amount"] = 999
                    self.assertEqual(uncertainty.request, OBSERVE)
                    self.assert_fenced(client)
                    self.assertEqual(client.close(), 7 if exited else 0)
                    self.assertEqual(log.read_bytes(), uncertainty.request_bytes)
                    self.assertIs(client.uncertainty, uncertainty)
                    launched.assert_called_once()

    def test_operation_specific_payload_shapes_and_reward_id_arrays(self):
        pool = load_fixture(FIXTURE).pool_view()
        malformed = [(IDS, "reward_ids", value) for value in (None, {}, "x", [1], [None], [["x"]])]
        malformed += [(VIEW, "view", value) for value in (None, [], {}, {"reward_id": 1})]
        malformed += [(POOL, "pool_view", value) for value in (
            None, [], {}, pool | {"extra": 1}, pool | {"balances": {}},
            pool | {"balances": pool["balances"] | {"CUSTOMER_DEPOSIT": True}},
            pool | {"credits": {}}, pool | {"spends": [None]},
            pool | {"credits": [{"pool": "OTHER", "amount": 1, "source_ref": "OPENING"}]},
            pool | {"spends": [{"pool": "PROTOCOL_REVENUE", "amount": 1, "program_ref": 7}]},
            pool | {"credits": [{"pool": "PROTOCOL_REVENUE", "amount": False, "source_ref": "OPENING"}]},
            pool | {"spends": [{"pool": "PROTOCOL_REVENUE", "amount": 1}]} )]
        malformed += [(row, key, value) for row, key, value in (
            (OBSERVE, "view", {"reward_id": "x"}), (VIEW, "receipt", {"reward": {"reward_id": "x"}}),
            (IDS, "pool_view", pool), (POOL, "reward_ids", []))]
        for request, key, value in malformed:
            with self.subTest(operation=request["operation"], key=key, value=value):
                raw = wire({"operation": request["operation"], "provenance": PROVENANCE, key: value})
                log, worker = self.fault_worker(raw)
                with patch("reward_client.subprocess.Popen", side_effect=worker) as launched:
                    client = self.launch()
                    with self.assertRaises(RewardTransportUncertainty):
                        self.exchange(client, request)
                    self.assert_fenced(client)
                    client.close()
                    self.assertEqual(decode_json(log.read_text()), request)
                    launched.assert_called_once()
        for ids in ([], ["caller-id", "another-id"]):
            reply = {"operation": "reward_ids", "provenance": PROVENANCE, "reward_ids": ids}
            _, worker = self.fault_worker(wire(reply))
            with patch("reward_client.subprocess.Popen", side_effect=worker):
                client = self.launch()
                self.assertEqual(self.exchange(client, IDS), reply)
                self.assertEqual(client.close(), 0)

    def test_startup_and_typed_errors_are_terminal_without_uncertainty(self):
        for operation, error in ((None, {"code": "INVALID_AMOUNT"}),
                                 (None, {"type": "OSError", "message": "setup failed"}),
                                 ("observe", {"type": "FixtureError", "message": "bad shape"}),
                                 ("observe", {"type": "OSError", "message": "write failed"})):
            reply = {"operation": operation, "provenance": PROVENANCE, "error": error}
            _, worker = self.fault_worker(wire(reply))
            with patch("reward_client.subprocess.Popen", side_effect=worker):
                client = self.launch()
                self.assertEqual(self.exchange(client, OBSERVE), reply)
                self.assert_fenced(client)
                self.assertIsNone(client.uncertainty)
                client.close()
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "invalid.json"
            fixture.write_text("{}")
            client = self.launch(fixture)
            try:
                reply = self.exchange(client, OBSERVE)
            except RewardTransportUncertainty as error:
                self.assertIsInstance(error.__cause__, BrokenPipeError)
            else:
                self.assertIsNone(reply["operation"])
                self.assertEqual(reply["error"]["type"], "FixtureError")
            self.assert_fenced(client)
            self.assertEqual(client.close(), 2)

    def test_pre_submission_validation_launch_limits_and_context_cleanup(self):
        with patch("reward_client.subprocess.Popen") as launched:
            for timeout in (0, -1, True, None, "1", float("inf"), float("nan")):
                with self.assertRaises(ValueError):
                    RewardClient.launch(FIXTURE, cleanup_timeout=timeout)
            with self.assertRaises(TypeError):
                RewardClient.launch(FIXTURE)
            launched.assert_not_called()
        client = self.launch()
        bad_rows = [[], OBSERVE | {"extra": 1}, OBSERVE | {"operation": "new-command"},
                    OBSERVE | {"operation": []}, OBSERVE | {"arguments": {}},
                    OBSERVE | {"arguments": OBSERVE["arguments"] | {"source_view": []}},
                    OBSERVE | {"arguments": OBSERVE["arguments"] | {"reward_key": {}}}]
        for value in (float("nan"), object(), (1,), {1: "key"}, "\ud800"):
            bad_rows.append(OBSERVE | {"arguments": OBSERVE["arguments"] | {"source_view": {"bad": value}}})
        submit = requests("participation")[3]
        for args in ({"approval_ref": {}}, {"execution_permit": {}},
                     {"approval_ref": submit["arguments"]["approval_ref"] | {"evidence_refs": {}}}):
            bad_rows.append(submit | {"arguments": submit["arguments"] | args})
        with patch.object(client._process.stdin, "write", wraps=client._process.stdin.write) as write:
            for request in bad_rows:
                with self.assertRaises((ValueError, TypeError)):
                    client.request(request)
            write.assert_not_called()
        self.assertEqual(self.exchange(client, OBSERVE), direct(load_fixture(FIXTURE), OBSERVE))
        with self.assertRaisesRegex(RuntimeError, "caller failure"):
            with client:
                raise RuntimeError("caller failure")
        self.assertEqual(client.close(), 0)
        self.assert_fenced(client)
        self.assertTrue(client._process.stdin.closed)
        self.assertTrue(client._process.stdout.closed)

    def test_short_write_broken_pipe_flush_and_interruption_never_retry(self):
        for fault in ("short", "none", "broken", "write_interrupt", "flush", "read", "interrupt"):
            with self.subTest(fault=fault):
                client = self.launch()
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
                with patch.object(stream, method, **options) as transport:
                    with self.assertRaises(RewardTransportUncertainty) as caught:
                        client.request(OBSERVE)
                    self.assertEqual(transport.call_count, 2 if method == "read" else 1)
                    self.assert_fenced(client)
                self.assertEqual(caught.exception.reply_bytes, b"{" if method == "read" else b"")
                self.assertEqual(caught.exception.request, OBSERVE)
                client.close()
                self.assertIs(client.uncertainty, caught.exception)

    def test_overlapping_request_and_close_are_rejected_before_write(self):
        client = self.launch()
        entered, release = threading.Event(), threading.Event()
        read = client._process.stdout.read
        def held_read(size):
            if not entered.is_set():
                entered.set()
                if not release.wait(10):
                    raise AssertionError("test release deadline")
            return read(size)
        results = []
        def call():
            try:
                results.append(client.request(OBSERVE))
            except BaseException as error:
                results.append(error)
        with patch.object(client._process.stdout, "read", side_effect=held_read), \
                patch.object(client._process.stdin, "write", wraps=client._process.stdin.write) as write:
            thread = threading.Thread(target=call)
            thread.start()
            try:
                self.assertTrue(entered.wait(10))
                with self.assertRaises(RewardClientStateError):
                    client.request(POOL)
                with self.assertRaises(RewardClientStateError):
                    client.close()
                self.assertEqual(write.call_count, 1)
            finally:
                release.set()
                thread.join(10)
                if thread.is_alive():
                    client._process.kill()
                    thread.join(10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(results, [direct(load_fixture(FIXTURE), OBSERVE)])
        self.assertEqual(len(self.exchange(client, IDS)["reward_ids"]), 1)

    @unittest.skipUnless(os.name == "posix", "POSIX child signal/reaping evidence")
    def test_cleanup_terminates_or_kills_only_owned_child_and_reaps(self):
        for stubborn in (False, True):
            with self.subTest(stubborn=stubborn):
                _, worker = self.fault_worker(wire(direct(load_fixture(FIXTURE), OBSERVE)),
                                              linger=True, stubborn=stubborn)
                with patch("reward_client.subprocess.Popen", side_effect=worker) as launched:
                    client = self.launch(cleanup_timeout=0.1)
                    self.exchange(client, OBSERVE)  # handler installed before reply
                    with patch.object(client._process, "terminate", wraps=client._process.terminate) as terminate, \
                            patch.object(client._process, "kill", wraps=client._process.kill) as kill:
                        self.assertEqual(client.close(), -9 if stubborn else -15)
                        self.assertEqual(client.close(), -9 if stubborn else -15)
                        terminate.assert_called_once()
                        self.assertEqual(kill.call_count, int(stubborn))
                    launched.assert_called_once()
                    with self.assertRaises(ChildProcessError):
                        os.waitpid(client._process.pid, os.WNOHANG)
                    self.assertTrue(client._process.stdin.closed)
                    self.assertTrue(client._process.stdout.closed)

    def test_import_safety_and_runnable_example_derived_ids_and_error_stop(self):
        probe = subprocess.run([sys.executable, "-c",
            'from unittest.mock import patch\n'
            'with patch("subprocess.Popen", side_effect=AssertionError("import launched")):\n'
            ' import reward_client\n'], cwd=HERE, capture_output=True, timeout=10)
        self.assertEqual((probe.returncode, probe.stdout, probe.stderr), (0, b"", b""))
        command = [sys.executable, str(HERE / "example_reward_client.py"), "--fixture", str(FIXTURE),
                   "--requests", str(FIXTURES / "participation.jsonl"), "--cleanup-timeout", "1"]
        result = subprocess.run(command, capture_output=True, timeout=10)
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        session, expected = load_fixture(FIXTURE), []
        for row in requests("participation"):
            reply = direct(session, row)
            expected.append(reply)
            if "receipt" in reply:
                expected.append(direct(session, {"operation": "view", "arguments": {
                    "reward_id_value": reply["receipt"]["reward"]["reward_id"]}}))
        self.assertEqual([decode_json(line) for line in result.stdout.decode().splitlines()], expected)
        command[command.index(str(FIXTURES / "participation.jsonl"))] = str(FIXTURES / "boundaries.jsonl")
        result = subprocess.run(command, capture_output=True, timeout=10)
        self.assertEqual((result.returncode, result.stderr), (1, b""))
        rows = [decode_json(line) for line in result.stdout.decode().splitlines()]
        self.assertEqual(rows[-1]["error"], {"code": "WINDOW_OPEN"})
        self.assertEqual(len(rows), 5)  # observe/view, hold/view, first refusal


class RewardInitializationClientTests(unittest.TestCase):
    fault_worker = RewardClientTests.fault_worker
    exchange = RewardClientTests.exchange
    assert_fenced = RewardClientTests.assert_fenced
    assert_synthetic = RewardClientTests.assert_synthetic

    def setUp(self):
        self.fixture = decode_json(FIXTURE.read_text())
        self.ack = {"operation": "initialize", "provenance": PROVENANCE,
                    "initialized": self.fixture}
        self.clients = []
        clients = self.clients
        class TrackedClient(RewardClient):
            def __init__(self, *args):
                super().__init__(*args)
                clients.append(self)
        self.client_type = TrackedClient

    def test_live_confirmed_input_is_detached_and_matches_file_mode(self):
        original = deepcopy(self.fixture)
        with patch("reward_client.subprocess.Popen", wraps=subprocess.Popen) as launched:
            client = self.client_type.launch_from_fixture(self.fixture, cleanup_timeout=1)
            self.addCleanup(client.close)
            launched.assert_called_once_with(
                [sys.executable, str(HERE.joinpath("reward_cli.py").resolve()),
                 "--init-stdin", "--requests", "-"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0, shell=False)
        self.fixture["opening_balances"]["PROTOCOL_REVENUE"] = 1
        acknowledged = client.initialized_reply
        acknowledged["initialized"]["opening_balances"].clear()
        self.assertEqual(client.initialized_reply["initialized"], original)
        file_client = RewardClient.launch(FIXTURE, cleanup_timeout=1)
        self.addCleanup(file_client.close)
        self.assertIsNone(file_client.initialized_reply)
        for row in requests("participation"):
            reply = self.exchange(client, row)
            self.assertEqual(reply, self.exchange(file_client, row))
            self.assert_synthetic(reply)
        self.assertEqual(client.close(), 0)
        self.assertEqual(file_client.close(), 0)

    def test_invalid_confirmed_input_and_cleanup_timeout_spawn_nothing(self):
        with patch("reward_client.subprocess.Popen") as launched:
            for record in invalid_initializations():
                with self.subTest(record=record):
                    with self.assertRaises((FixtureError, TokenRewardError)):
                        self.client_type.launch_from_fixture(decode_json(record), cleanup_timeout=1)
            for timeout in (0, -1, True, None, "1", float("nan"), float("inf")):
                with self.assertRaises(ValueError):
                    self.client_type.launch_from_fixture(self.fixture, cleanup_timeout=timeout)
            with self.assertRaises(TypeError):
                self.client_type.launch_from_fixture(self.fixture)
            launched.assert_not_called()

    def assert_startup_fenced_and_reaped(self, error, raw):
        self.assertEqual(len(self.clients), 1)
        client = self.clients.pop()
        self.assertIs(client.uncertainty, error)
        self.assertEqual(error.phase, "initialize")
        self.assertEqual(error.reply_bytes, raw)
        self.assertEqual(error.request, self.fixture)
        self.assertEqual(error.request_bytes, wire(self.fixture))
        self.assertIsNotNone(error.__cause__)
        self.assert_fenced(client)
        self.assertTrue(client._closed)
        self.assertIsNotNone(client._process.returncode)
        self.assertTrue(client._process.stdin.closed)
        self.assertTrue(client._process.stdout.closed)
        self.assertIsNone(client.initialized_reply)
        if os.name == "posix":
            with self.assertRaises(ChildProcessError):
                os.waitpid(client._process.pid, os.WNOHANG)

    def test_bad_missing_and_mismatched_acknowledgements_never_allow_business_requests(self):
        valid = wire(self.ack)
        faults = [b"", b"{", b"\xff\n", b"[]\n", b"null\n", b"NaN\n", valid[:-1],
                  wire(self.ack | {"operation": "pool_view"}),
                  wire(self.ack | {"operation": None}), wire(self.ack | {"provenance": "LIVE"}),
                  wire(self.ack | {"extra": None}), wire(self.ack | {"initialized": {}}),
                  wire({k: v for k, v in self.ack.items() if k != "initialized"}),
                  wire({"operation": None, "provenance": PROVENANCE, "error": {"code": "X"}}),
                  valid.replace(b'"operation":', b'"operation":"initialize","operation":'),
                  valid.replace(b'"CUSTOMER_DEPOSIT":0', b'"CUSTOMER_DEPOSIT":0,"CUSTOMER_DEPOSIT":0')]
        for value in (False, 0.0, 1):
            changed = deepcopy(self.fixture)
            changed["opening_balances"]["CUSTOMER_DEPOSIT"] = value
            faults.append(wire(self.ack | {"initialized": changed}))
        for raw in faults:
            with self.subTest(raw=raw):
                log, worker = self.fault_worker(raw)
                with patch("reward_client.subprocess.Popen", side_effect=worker) as launched:
                    with self.assertRaises(RewardTransportUncertainty) as caught:
                        self.client_type.launch_from_fixture(self.fixture, cleanup_timeout=1)
                    self.assert_startup_fenced_and_reaped(caught.exception, raw)
                    self.assertEqual(log.read_bytes(), wire(self.fixture))
                    launched.assert_called_once()

    def test_startup_short_write_flush_failure_and_interrupt_reap_without_retry(self):
        for fault in ("short", "none", "broken", "write_interrupt", "flush", "read", "interrupt"):
            with self.subTest(fault=fault):
                log, worker = self.fault_worker(wire(self.ack))
                parent = self.client_type
                class FaultyClient(parent):
                    def __init__(child, *args):
                        super().__init__(*args)
                        stream, method = child._process.stdin, "write"
                        if fault in ("read", "interrupt"):
                            stream, method = child._process.stdout, "read"
                            options = {"side_effect": [b"{", KeyboardInterrupt() if fault == "interrupt" else OSError()]}
                        elif fault == "flush":
                            method, options = "flush", {"side_effect": OSError()}
                        elif fault in ("short", "none"):
                            options = {"return_value": 1 if fault == "short" else None}
                        else:
                            options = {"side_effect": KeyboardInterrupt() if fault == "write_interrupt" else BrokenPipeError()}
                        injected = patch.object(stream, method, **options)
                        injected.start()
                        self.addCleanup(injected.stop)
                with patch("reward_client.subprocess.Popen", side_effect=worker) as launched:
                    with self.assertRaises(RewardTransportUncertainty) as caught:
                        FaultyClient.launch_from_fixture(self.fixture, cleanup_timeout=1)
                    self.assert_startup_fenced_and_reaped(caught.exception,
                                                         b"{" if fault in ("read", "interrupt") else b"")
                    self.assertEqual(log.read_bytes(), wire(self.fixture) if fault in ("flush", "read", "interrupt") else b"")
                    launched.assert_called_once()


if __name__ == "__main__":
    unittest.main()
