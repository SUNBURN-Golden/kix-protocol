"""One explicitly launched, process-local synthetic pool JSONL child.

Reads block without polling or response deadlines. An uncertain exchange fences
this instance permanently; cleanup cannot prove rejection or undo accepted work.
Importing launches nothing. Callers confirm inputs before calling launch/request.
"""

import math
from pathlib import Path
import subprocess
import sys
import threading

from pool_session import (NOTICE, PoolSession, _DISPATCH, decode_opening_balances,
                          read_opening_balances)
from reward_fixture import FixtureError, decode_json, exact_fields, validate_json
from token_reward_model import ALWAYS_FALSE_FLAGS, POOL_NAMES, PROVENANCE, UNIT, _canonical


class PoolClientStateError(RuntimeError):
    """Local rejection before submission: busy, closed or terminal client."""


class PoolTransportUncertainty(RuntimeError):
    """Observed transport evidence, never a business outcome or retry permit."""

    def __init__(self, phase, request, request_bytes, reply_bytes):
        super().__init__(f"local pool {phase} uncertain; client fenced")
        self.phase = phase
        self.request = request
        self.request_bytes = request_bytes
        self.reply_bytes = reply_bytes


def validate_cleanup_timeout(value):
    if (type(value) not in (int, float) or not math.isfinite(value) or value <= 0):
        raise ValueError("cleanup_timeout must be a finite positive number")


class PoolClient:
    """Own one child and one exchange; use launch()/launch_from_balances() and with.

    expected_opening_balances is the caller's confirmed snapshot. Startup inputs
    are checked before launch and the acknowledgement before any request.
    cleanup_timeout bounds cleanup waits only; it is a required caller input.
    """

    @classmethod
    def launch(cls, fixture, *, expected_opening_balances, cleanup_timeout):
        validate_cleanup_timeout(cleanup_timeout)
        validate_json(expected_opening_balances)
        expected = _canonical(expected_opening_balances)
        fixture = Path(fixture).resolve()
        if _canonical(read_opening_balances(fixture)) != expected:
            raise FixtureError("fixture opening balances differ from confirmed snapshot")
        command = [sys.executable, str(Path(__file__).with_name("pool_cli.py").resolve()),
                   "--fixture", str(fixture), "--requests", "-"]
        return cls._launch(command, cleanup_timeout, expected, b"")

    @classmethod
    def launch_from_balances(cls, *, expected_opening_balances, cleanup_timeout):
        """Send a detached confirmed snapshot once, before ordinary request JSONL."""
        validate_cleanup_timeout(cleanup_timeout)
        validate_json(expected_opening_balances)
        record = _canonical({"fixture_version": 1, "provenance": PROVENANCE,
                             "opening_balances": expected_opening_balances})
        opening = decode_opening_balances(record)
        PoolSession(opening)  # Disposable domain preflight; no local operations.
        command = [sys.executable, str(Path(__file__).with_name("pool_cli.py").resolve()),
                   "--init-stdin", "--requests", "-"]
        return cls._launch(command, cleanup_timeout, _canonical(opening),
                           (record + "\n").encode("utf-8"))

    @classmethod
    def _launch(cls, command, cleanup_timeout, expected, initialization_wire):
        # Binary unbuffered pipes; stderr inherited, never mixed with JSONL.
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   bufsize=0, shell=False)
        client = cls(process, cleanup_timeout)
        try:
            client._initialized_reply = client._exchange(None, initialization_wire, expected)
        except BaseException as error:
            try:
                client.close()
            except BaseException as cleanup_error:
                error.add_note(f"child cleanup raised {type(cleanup_error).__name__}: {cleanup_error}")
            raise
        return client

    def __init__(self, process, cleanup_timeout):
        self._process = process
        self._cleanup_timeout = cleanup_timeout
        self._guard = threading.Lock()
        self._terminal = False
        self._closed = False
        self._returncode = None
        self._initialized_reply = None
        self._domain_refused = False
        self.uncertainty = None

    @property
    def initialized_reply(self):
        # Callers cannot alter the retained acknowledgement through this view.
        return decode_json(_canonical(self._initialized_reply))

    @property
    def domain_refused(self):
        return self._domain_refused

    @staticmethod
    def _validate_request(request):
        validate_json(request)
        exact_fields(request, {"operation", "arguments"}, "request")
        operation = request["operation"]
        if type(operation) is not str or operation not in _DISPATCH:
            raise FixtureError("unsupported pool operation")
        exact_fields(request["arguments"], _DISPATCH[operation][1], f"{operation} arguments")

    @staticmethod
    def _balances(value):
        exact_fields(value, POOL_NAMES, "pool balances")
        if any(type(amount) is not int for amount in value.values()):
            raise FixtureError("pool balances must be integers")

    @staticmethod
    def _view(value):
        exact_fields(value, {"balances", "credits", "spends"}, "pool view")
        PoolClient._balances(value["balances"])
        for entries, ref in (("credits", "source_ref"), ("spends", "program_ref")):
            if type(value[entries]) is not list:
                raise FixtureError("pool entries must be arrays")
            for entry in value[entries]:
                exact_fields(entry, {"pool", "amount", ref}, "pool entry")
                if (type(entry["pool"]) is not str or entry["pool"] not in POOL_NAMES
                        or type(entry["amount"]) is not int or type(entry[ref]) is not str):
                    raise FixtureError("invalid pool entry shape")

    @staticmethod
    def _reply(raw, operation, expected):
        if not raw.endswith(b"\n"):
            raise FixtureError("response ended without a newline")
        reply = decode_json(raw.decode("utf-8"))
        if type(reply) is not dict:
            raise FixtureError("response must be an object")
        payload = set(reply) & {"initialized", "view", "error"}
        if len(payload) != 1:
            raise FixtureError("response requires one payload")
        exact_fields(reply, {"operation", "provenance", "unit", "notice"}
                     | set(ALWAYS_FALSE_FLAGS) | payload, "response")
        if (reply["operation"] != operation or reply["provenance"] != PROVENANCE
                or reply["unit"] != UNIT or reply["notice"] != NOTICE
                or any(reply[flag] is not False for flag in ALWAYS_FALSE_FLAGS)):
            raise FixtureError("invalid response operation or synthetic metadata")
        key = next(iter(payload))
        if expected is not None:
            if key != "initialized":
                raise FixtureError("initialization acknowledgement required")
            exact_fields(reply[key], {"opening_balances"}, "initialized")
            PoolClient._balances(reply[key]["opening_balances"])
            if _canonical(reply[key]["opening_balances"]) != expected:
                raise FixtureError("acknowledged balances differ from confirmed snapshot")
        elif key == "view":
            PoolClient._view(reply[key])
        elif key == "error":
            error = reply[key]
            fields = {"code"} if type(error) is dict and set(error) == {"code"} else {"type", "message"}
            exact_fields(error, fields, "response error")
            if any(type(error[field]) is not str for field in fields):
                raise FixtureError("response error values must be strings")
        else:
            raise FixtureError("unexpected initialization acknowledgement")
        return reply

    def _exchange(self, submitted, wire, expected=None):
        phase = "initialize" if expected is not None else "request"
        raw = bytearray()
        try:
            if wire:
                written = self._process.stdin.write(wire)
                if written != len(wire):
                    raise OSError("short request write")
                self._process.stdin.flush()
            while True:
                chunk = self._process.stdout.read(1)
                if not chunk:
                    break
                raw.extend(chunk)
                if chunk == b"\n":
                    break
            reply = self._reply(bytes(raw), "initialize" if expected is not None
                                else submitted["operation"], expected)
            if "error" in reply:
                self._terminal = "type" in reply["error"]
                self._domain_refused |= "code" in reply["error"]
            return reply
        except BaseException as error:
            self._terminal = True
            self.uncertainty = PoolTransportUncertainty(phase, submitted, wire, bytes(raw))
            raise self.uncertainty from error

    def request(self, request):
        if not self._guard.acquire(blocking=False):
            raise PoolClientStateError("another request or cleanup is outstanding")
        try:
            if self._closed or self._terminal:
                raise PoolClientStateError("client is closed, terminal or uncertain")
            self._validate_request(request)
            wire = (_canonical(request) + "\n").encode("utf-8")
            submitted = decode_json(wire.decode("utf-8"))
            return self._exchange(submitted, wire)
        finally:
            self._guard.release()

    def close(self):
        """Close stdin, terminate/kill only if needed, reap; idempotent status.

        Interrupt the requesting caller before cleanup; overlapping calls reject.
        Uncertainty remains retained after cleanup and never permits resubmission.
        """
        if not self._guard.acquire(blocking=False):
            raise PoolClientStateError("another request or cleanup is outstanding")
        try:
            if self._closed:
                return self._returncode
            self._terminal = True
            try:
                try:
                    self._process.stdin.close()
                except OSError:
                    pass
                try:
                    self._process.wait(timeout=self._cleanup_timeout)
                except subprocess.TimeoutExpired:
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=self._cleanup_timeout)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                        self._process.wait()
            except BaseException:
                # Even interruption during cleanup must not abandon the child.
                self._process.kill()
                self._process.wait()
                raise
            finally:
                self._process.stdout.close()
                self._returncode = self._process.returncode
                self._closed = self._returncode is not None
            return self._returncode
        finally:
            self._guard.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
