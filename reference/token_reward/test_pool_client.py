"""Source-informed live pool parity and transport uncertainty boundaries."""

import copy
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from pool_client import PoolClient, PoolClientStateError, PoolTransportUncertainty
from pool_session import PoolSession, dispatch_request, error_reply, initialized_reply
from reward_fixture import FixtureError, decode_json
from test_pool_session import FIXTURE, check_metadata, opening, request
from token_reward_model import ALWAYS_FALSE_FLAGS, MONEY_MAX, POOLS, PROVENANCE, TokenRewardError, _canonical


HERE = Path(__file__).parent


def wire(value):
    return (_canonical(value) + "\n").encode("utf-8")


def direct(session, item):
    try:
        return dispatch_request(session, item)
    except TokenRewardError as error:
        return error_reply(item["operation"], error)


class Child:
    """Only the binary pipe/ownership boundary is faked, never model semantics."""

    def __init__(self, data):
        self.stdin = Mock(wraps=io.BytesIO())
        self.stdout = io.BytesIO(data)
        self.returncode = None
        self.wait = Mock(side_effect=self.finish)
        self.terminate = Mock()
        self.kill = Mock()

    def finish(self, timeout=None):
        self.returncode = 0
        return 0


class PoolClientTests(unittest.TestCase):
    def launch(self, *, stdin_init=False):
        launch = PoolClient.launch_from_balances if stdin_init else lambda **kwargs: PoolClient.launch(FIXTURE, **kwargs)
        client = launch(expected_opening_balances=opening(), cleanup_timeout=1)
        self.addCleanup(client.close)
        return client

    def fake(self, data):
        child = Child(wire(initialized_reply(opening())) + data)
        with patch("pool_client.subprocess.Popen", return_value=child):
            client = self.launch()
        return client, child

    def exchange(self, client, item):
        # Test-only deadline: prove child flushes before stdin EOF, no product polling.
        done, result = threading.Event(), []

        def call():
            try:
                result.append(client.request(item))
            except BaseException as error:
                result.append(error)
            finally:
                done.set()

        thread = threading.Thread(target=call)
        thread.start()
        complete = done.wait(10)
        if not complete:
            client._process.kill()
        thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertTrue(complete, "child reply must precede stdin EOF")
        self.assertFalse(client._process.stdin.closed)
        if isinstance(result[0], BaseException):
            raise result[0]
        return result[0]

    def test_real_incremental_journeys_complete_envelopes_one_child(self):
        for stdin_init, name, status in ((mode, name, code) for mode in (False, True)
                                         for name, code in (("journey", 0), ("boundaries", 1))):
            with self.subTest(name=name, stdin_init=stdin_init), patch("pool_client.subprocess.Popen", wraps=subprocess.Popen) as launch:
                client, session = self.launch(stdin_init=stdin_init), PoolSession(opening())
                self.assertEqual(client.initialized_reply, initialized_reply(opening()))
                changed = client.initialized_reply
                changed["initialized"]["opening_balances"].clear()
                self.assertEqual(client.initialized_reply, initialized_reply(opening()))
                for line in (HERE / f"fixtures/pool_{name}.jsonl").read_text().splitlines():
                    item = decode_json(line)
                    actual = self.exchange(client, item)
                    self.assertEqual(actual, direct(session, item))
                    check_metadata(self, actual)
                self.assertEqual(self.exchange(client, request("view")), direct(session, request("view")))
                self.assertEqual(client.close(), status)
                self.assertEqual(client.close(), status)
                self.assertIsNotNone(client._process.returncode)
                self.assertTrue(client._process.stdout.closed)
                with self.assertRaises(PoolClientStateError):
                    client.request(request("view"))
                startup = ["--init-stdin"] if stdin_init else ["--fixture", str(FIXTURE.resolve())]
                launch.assert_called_once_with(
                    [sys.executable, str((HERE / "pool_cli.py").resolve()), *startup,
                     "--requests", "-"], stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, bufsize=0, shell=False)

    def test_real_domain_types_and_repeated_refs_remain_model_inputs(self):
        for stdin_init in (False, True):
            with self.launch(stdin_init=stdin_init) as client:
                session = PoolSession(opening())
                items = [request("credit", amount=value) for value in (True, 1.0, "1", None, 9007199254740993)]
                items += [request(op, amount=1, ref="same") for op in ("credit", "credit", "spend", "spend", "view")]
                for item in items:
                    self.assertEqual(self.exchange(client, item), direct(session, item))
                view = session.view()
                self.assertEqual(view["credits"][-2:], [request("credit", ref="same")["arguments"]] * 2)
                self.assertEqual(view["spends"], [request("spend", ref="same")["arguments"]] * 2)
                self.assertEqual(client.close(), 1)

    def test_invalid_timeout_fixture_or_confirmed_snapshot_launches_nothing(self):
        with patch("pool_client.subprocess.Popen") as launch:
            for value in (None, True, 0, -1, float("nan"), float("inf"), "1"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    PoolClient.launch(FIXTURE, expected_opening_balances=opening(), cleanup_timeout=value)
            for value in (99, True, 2.0):
                balances = {**opening(), "PROTOCOL_REVENUE": value}
                with self.assertRaises(FixtureError):
                    PoolClient.launch(FIXTURE, expected_opening_balances=balances, cleanup_timeout=1)
            with tempfile.TemporaryDirectory() as tmp:
                fixture = Path(tmp) / "changed.json"
                fixture.write_text('{"fixture_version":true}')
                with self.assertRaises(FixtureError):
                    PoolClient.launch(fixture, expected_opening_balances=opening(), cleanup_timeout=1)
            launch.assert_not_called()

    def test_initialization_failures_reap_without_request_submission(self):
        good = initialized_reply(opening())
        variants = [b"", wire(good)[:-1], b"\xff\n", b'{"operation":1,"operation":2}\n',
                    wire(direct(PoolSession(opening()), request("view"))), wire(error_reply("initialize", ValueError("bad")))]
        for value in (True, 2.0, 99):
            bad = copy.deepcopy(good)
            bad["initialized"]["opening_balances"]["PROTOCOL_REVENUE"] = value
            variants.append(wire(bad))
        for field, value in (("operation", "view"), ("notice", "real"), ("unit", "KRW"),
                             ("provenance", "REAL"), ("initialized", {})):
            variants.append(wire({**good, field: value}))
        for flag in ALWAYS_FALSE_FLAGS:
            for value in (True, 0, None):
                variants.append(wire({**good, flag: value}))
        for stdin_init, data in ((mode, data) for mode in (False, True) for data in variants):
            with self.subTest(data=data, stdin_init=stdin_init):
                child = Child(data)
                with patch("pool_client.subprocess.Popen", return_value=child) as launch, \
                        self.assertRaises(PoolTransportUncertainty) as caught:
                    self.launch(stdin_init=stdin_init)
                error = caught.exception
                self.assertEqual(error.phase, "initialize")
                self.assertIsNone(error.request)
                init_wire = wire({"fixture_version": 1, "provenance": PROVENANCE,
                                  "opening_balances": opening()}) if stdin_init else b""
                self.assertEqual(error.request_bytes, init_wire)
                self.assertEqual(error.reply_bytes, data)
                self.assertIsNotNone(error.__cause__)
                if stdin_init:
                    child.stdin.write.assert_called_once_with(init_wire)
                    child.stdin.flush.assert_called_once()
                else:
                    child.stdin.write.assert_not_called()
                child.stdin.close.assert_called_once()
                self.assertTrue(child.stdout.closed)
                self.assertIsNotNone(child.returncode)
                launch.assert_called_once()

    def test_changed_fixture_at_child_start_fences_acknowledgement(self):
        changed = initialized_reply({**opening(), "PROTOCOL_REVENUE": 3})
        child = Child(wire(changed))
        # Parent preflight sees confirmed file; the child describes different data.
        with patch("pool_client.subprocess.Popen", return_value=child), \
                self.assertRaises(PoolTransportUncertainty):
            self.launch()
        child.stdin.write.assert_not_called()
        child.wait.assert_called_once_with(timeout=1)

    def test_stdin_preflight_rejects_invalid_balances_and_timeout_without_launch(self):
        invalid = [None, [], {}, {**opening(), "OTHER": 0},
                   {k: v for k, v in opening().items() if k != POOLS[0]}]
        invalid += [{**opening(), POOLS[0]: value}
                    for value in (True, 1.0, "1", -1, MONEY_MAX + 1, float("nan"))]
        with patch("pool_client.subprocess.Popen") as launch:
            for balances in invalid:
                with self.subTest(balances=balances), self.assertRaises((FixtureError, TokenRewardError)):
                    PoolClient.launch_from_balances(expected_opening_balances=balances, cleanup_timeout=1)
            for timeout in (None, True, 0, -1, float("inf"), float("nan"), "1"):
                with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                    PoolClient.launch_from_balances(expected_opening_balances=opening(), cleanup_timeout=timeout)
            launch.assert_not_called()

    def test_stdin_initialization_uses_detached_confirmed_snapshot(self):
        balances = opening()
        expected_wire = wire({"fixture_version": 1, "provenance": PROVENANCE,
                              "opening_balances": opening()})
        child = Child(wire(initialized_reply(opening())))

        def spawn(*args, **kwargs):
            balances["PROTOCOL_REVENUE"] = 99
            return child

        with patch("pool_client.subprocess.Popen", side_effect=spawn):
            with PoolClient.launch_from_balances(expected_opening_balances=balances, cleanup_timeout=1) as client:
                self.assertEqual(client.initialized_reply, initialized_reply(opening()))
        child.stdin.write.assert_called_once_with(expected_wire)
        child.stdin.flush.assert_called_once()

    def test_initialization_transport_faults_fence_and_reap_without_retry(self):
        clients = []

        class TrackedClient(PoolClient):
            def __init__(self, *args):
                super().__init__(*args)
                clients.append(self)

        init_wire = wire({"fixture_version": 1, "provenance": PROVENANCE,
                          "opening_balances": opening()})
        for stage in ("broken", "short", "none", "flush", "read", "interrupt"):
            child = Child(b"")
            if stage == "broken":
                child.stdin.write.side_effect = BrokenPipeError("lost initialization")
            elif stage in ("short", "none"):
                child.stdin.write.return_value = 1 if stage == "short" else None
            elif stage == "flush":
                child.stdin.flush.side_effect = OSError("lost flush")
            else:
                child.stdout = Mock()
                child.stdout.read.side_effect = [b"{", KeyboardInterrupt() if stage == "interrupt" else OSError("lost read")]
            with self.subTest(stage=stage), patch("pool_client.subprocess.Popen", return_value=child) as spawn, \
                    self.assertRaises(PoolTransportUncertainty) as caught:
                TrackedClient.launch_from_balances(expected_opening_balances=opening(), cleanup_timeout=1)
            client, error = clients[-1], caught.exception
            self.assertIs(client.uncertainty, error)
            self.assertEqual((error.phase, error.request, error.request_bytes), ("initialize", None, init_wire))
            self.assertEqual(error.reply_bytes, b"{" if stage in ("read", "interrupt") else b"")
            self.assertIsNotNone(error.__cause__)
            with self.assertRaises(PoolClientStateError):
                client.request(request("view"))
            child.stdin.write.assert_called_once_with(init_wire)
            self.assertEqual(child.stdin.flush.call_count, int(stage in ("flush", "read", "interrupt")))
            child.stdin.close.assert_called_once()
            if stage in ("read", "interrupt"):
                child.stdout.close.assert_called_once()
            else:
                self.assertTrue(child.stdout.closed)
            self.assertIsNotNone(child.returncode)
            spawn.assert_called_once()
            self.assertEqual(client.close(), 0)

    def test_invalid_requests_fail_locally_without_fencing_or_coercion(self):
        client, child = self.fake(wire(direct(PoolSession(opening()), request("view"))))
        bad = [None, [], {}, {"operation": "initialize", "arguments": {}},
               {"operation": "view", "arguments": [], "extra": 1},
               request("credit", amount=float("nan")), request("credit", ref="\ud800")]
        for op in ("view", "credit", "spend"):
            item = request(op)
            item["arguments"]["extra"] = 1
            bad.append(item)
        for item in bad:
            with self.subTest(item=repr(item)), self.assertRaises(FixtureError):
                client.request(item)
        child.stdin.write.assert_not_called()
        self.assertIsNone(client.uncertainty)
        self.assertIn("view", client.request(request("view")))

    def test_malformed_response_matrix_fences_with_exact_evidence(self):
        good = direct(PoolSession(opening()), request("view"))
        variants = [b"", b"{}", b"{}\n", b"[]\n", b"\xff\n", b'{"a":1,"a":2}\n',
                    b'{"a":NaN}\n', wire(initialized_reply(opening())),
                    wire({**good, "operation": "credit"}), wire({**good, "extra": 1}),
                    wire({**good, "error": {"code": "NO"}})]
        for field in good:
            bad = copy.deepcopy(good)
            del bad[field]
            variants.append(wire(bad))
        for field, value in (("balances", {}), ("credits", {}), ("spends", [None]),
                             ("credits", [{"pool": "OTHER", "amount": 1, "source_ref": "x"}]),
                             ("credits", [{"pool": "PROTOCOL_REVENUE", "amount": True, "source_ref": "x"}]),
                             ("credits", [{"pool": "PROTOCOL_REVENUE", "amount": 1, "source_ref": 1}])):
            bad = copy.deepcopy(good)
            bad["view"][field] = value
            variants.append(wire(bad))
        for detail in ({}, {"code": 1}, {"type": "X"}, {"type": "X", "message": None}, {"code": "X", "message": "x"}):
            variants.append(wire({k: v for k, v in good.items() if k != "view"} | {"error": detail}))
        for flag in ALWAYS_FALSE_FLAGS:
            for value in (True, 0, None):
                variants.append(wire({**good, flag: value}))
        for data in variants:
            with self.subTest(data=data):
                client, child = self.fake(data)
                item = request("view")
                with self.assertRaises(PoolTransportUncertainty) as caught:
                    client.request(item)
                error = caught.exception
                self.assertIs(error, client.uncertainty)
                self.assertEqual(error.phase, "request")
                self.assertEqual(error.request, item)
                self.assertEqual(error.request_bytes, wire(item))
                self.assertEqual(error.reply_bytes, data)
                self.assertIsNotNone(error.__cause__)
                with self.assertRaises(PoolClientStateError):
                    client.request(item)
                child.stdin.write.assert_called_once_with(wire(item))
                client.close()
                self.assertIs(client.uncertainty, error)

    def test_write_flush_and_partial_read_faults_retain_snapshot_without_retry(self):
        for stage in ("broken", "short", "none", "flush", "read", "interrupt"):
            with self.subTest(stage=stage):
                client, child = self.fake(b"")
                item = request("credit")
                original = copy.deepcopy(item)
                if stage == "broken":
                    def fail_write(data):
                        item["arguments"]["amount"] = 99
                        raise BrokenPipeError("lost pipe")
                    child.stdin.write.side_effect = fail_write
                elif stage in ("short", "none"):
                    child.stdin.write.return_value = 1 if stage == "short" else None
                elif stage == "flush":
                    child.stdin.flush.side_effect = BrokenPipeError("lost flush")
                else:
                    child.stdout = Mock()
                    child.stdout.read.side_effect = [b"{", KeyboardInterrupt() if stage == "interrupt" else OSError("lost read")]
                with self.assertRaises(PoolTransportUncertainty) as caught:
                    client.request(item)
                self.assertEqual(caught.exception.request, original)
                self.assertEqual(caught.exception.request_bytes, wire(original))
                self.assertEqual(caught.exception.reply_bytes, b"{" if stage in ("read", "interrupt") else b"")
                with self.assertRaises(PoolClientStateError):
                    client.request(request("view"))
                self.assertEqual(child.stdin.write.call_count, 1)
                client.close()

    def test_lost_ack_after_real_accepted_mutation_fences_without_rollback(self):
        client = self.launch()
        stream, observed = client._process.stdout, []

        class LostReply:
            def read(self, size):
                observed.append(stream.readline())  # actual child already accepted
                raise OSError("acknowledgement lost")

            def close(self):
                stream.close()

        client._process.stdout = LostReply()
        with self.assertRaises(PoolTransportUncertainty):
            client.request(request("credit", amount=7))
        actual = decode_json(observed[0].decode())
        self.assertEqual(actual["view"]["credits"][-1], request("credit", amount=7)["arguments"])
        with self.assertRaises(PoolClientStateError):
            client.request(request("view"))
        self.assertEqual(len(observed), 1)
        self.assertEqual(client.close(), 0)

    def test_typed_service_error_is_preserved_and_terminal(self):
        reply = error_reply("view", FixtureError("service failed"))
        client, child = self.fake(wire(reply))
        self.assertEqual(client.request(request("view")), reply)
        with self.assertRaises(PoolClientStateError):
            client.request(request("view"))
        child.stdin.write.assert_called_once()

    def test_overlap_rejects_request_and_cleanup_before_second_write(self):
        client, child = self.fake(b"")
        entered, release = threading.Event(), threading.Event()
        source = io.BytesIO(wire(direct(PoolSession(opening()), request("view"))))

        def blocked(size):
            entered.set()
            if not release.wait(10):
                raise OSError("test release absent")
            return source.read(size)

        child.stdout = Mock(read=Mock(side_effect=blocked))
        results = []
        thread = threading.Thread(target=lambda: results.append(client.request(request("view"))))
        thread.start()
        try:
            self.assertTrue(entered.wait(10))
            for call in (lambda: client.request(request("credit")), client.close):
                with self.assertRaises(PoolClientStateError):
                    call()
            child.stdin.write.assert_called_once()
        finally:
            release.set()
            thread.join(10)
        self.assertFalse(thread.is_alive())
        self.assertIn("view", results[0])
        client.close()

    def test_cleanup_escalation_and_interruption_reap_once(self):
        for stage in ("terminate", "kill", "interrupt"):
            with self.subTest(stage=stage):
                client, child = self.fake(b"")
                timeout = subprocess.TimeoutExpired("owned pool child", 1)
                waits = iter([timeout, child.finish] if stage == "terminate" else
                             [timeout, timeout, child.finish] if stage == "kill" else
                             [KeyboardInterrupt(), child.finish])
                def wait(timeout=None):
                    result = next(waits)
                    if isinstance(result, BaseException):
                        raise result
                    return result(timeout)
                child.wait.side_effect = wait
                if stage == "interrupt":
                    with self.assertRaises(KeyboardInterrupt):
                        client.close()
                else:
                    self.assertEqual(client.close(), 0)
                self.assertEqual(client.close(), 0)
                child.stdin.close.assert_called_once()
                self.assertTrue(child.stdout.closed)
                self.assertEqual(child.kill.call_count, int(stage != "terminate"))
                self.assertEqual(child.terminate.call_count, int(stage != "interrupt"))


if __name__ == "__main__":
    unittest.main()
