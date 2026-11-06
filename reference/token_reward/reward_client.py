"""Blocking, single-request client for the synthetic local reward desk.

Importing launches nothing. No restart, retry, replay, persistence or sockets.
An uncertain exchange fences this instance; cleanup cannot undo accepted work.
"""

import math
from pathlib import Path
import subprocess
import sys
import threading

from reward_fixture import FixtureError, decode_json, exact_fields, validate_json
from reward_cli import _APPROVAL, _DISPATCH
from token_reward_model import POOL_NAMES, PROVENANCE, _canonical


class RewardClientStateError(RuntimeError):
    """Local rejection before submission: busy, closed or terminal client."""


class RewardTransportUncertainty(RuntimeError):
    """A submitted request has no trustworthy complete response.

    request is the serialized snapshot, not an inferred business outcome.
    reply_bytes contains bytes observed before the failure. Neither authorizes
    resubmission, even if the desk exits or cleanup terminates it.
    """

    def __init__(self, request, request_bytes, reply_bytes):
        super().__init__("local reward desk exchange uncertain; client fenced")
        self.request = request
        self.request_bytes = request_bytes
        self.reply_bytes = reply_bytes


class RewardClient:
    """Own one explicitly launched desk and at most one outstanding request.

    Use launch(), then request() synchronously, and close() or a with block.
    Reads have no response timeout. cleanup_timeout applies only to close().
    close() rejects concurrent use too; interrupt the requesting caller first.
    """

    @classmethod
    def launch(cls, fixture, *, cleanup_timeout):
        if (isinstance(cleanup_timeout, bool)
                or not isinstance(cleanup_timeout, (int, float))
                or not math.isfinite(cleanup_timeout) or cleanup_timeout <= 0):
            raise ValueError("cleanup_timeout must be a finite positive number")
        command = [sys.executable, str(Path(__file__).with_name("reward_cli.py").resolve()),
                   "--fixture", str(Path(fixture).resolve()), "--requests", "-"]
        # Child buffering is ordinary Python buffering. stderr is inherited,
        # never mixed with JSONL stdout or left in an undrained pipe.
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   bufsize=0, shell=False)
        return cls(process, cleanup_timeout)

    def __init__(self, process, cleanup_timeout):
        self._process = process
        self._cleanup_timeout = cleanup_timeout
        self._guard = threading.Lock()
        self._terminal = False
        self._closed = False
        self._returncode = None
        self.uncertainty = None

    @staticmethod
    def _validate_request(request):
        # Share the existing selector/signature table; no session or model call.
        validate_json(request)
        exact_fields(request, {"operation", "arguments"}, "request")
        operation = request["operation"]
        if type(operation) is not str or operation not in _DISPATCH:
            raise FixtureError("unsupported session operation")
        _, required, optional, _ = _DISPATCH[operation]
        arguments = request["arguments"]
        exact_fields(arguments, required, f"{operation} arguments", optional)
        if "reward_key" in arguments:
            exact_fields(arguments["reward_key"],
                         {"program", "source_op_id", "recipient", "kind"}, "reward_key")
        if "source_view" in arguments and type(arguments["source_view"]) is not dict:
            raise FixtureError("source_view must be an object")
        if "approval_ref" in arguments:
            approval = arguments["approval_ref"]
            exact_fields(approval, _APPROVAL, "approval_ref", {"prior_record"})
            if type(approval["evidence_refs"]) is not list:
                raise FixtureError("approval evidence_refs must be an array")
        if arguments.get("execution_permit") is not None:
            exact_fields(arguments["execution_permit"],
                         {"fence_ref", "signed_bytes_digest"}, "execution_permit")

    @staticmethod
    def _pool_payload(pool):
        exact_fields(pool, {"balances", "credits", "spends"}, "pool_view")
        exact_fields(pool["balances"], POOL_NAMES, "pool balances")
        if any(type(amount) is not int for amount in pool["balances"].values()):
            raise FixtureError("pool balances must be integers")
        for entries, reference in (("credits", "source_ref"), ("spends", "program_ref")):
            if type(pool[entries]) is not list:
                raise FixtureError("pool entries must be arrays")
            for entry in pool[entries]:
                exact_fields(entry, {"pool", "amount", reference}, "pool entry")
                if (type(entry["pool"]) is not str or entry["pool"] not in POOL_NAMES
                        or type(entry["amount"]) is not int
                        or type(entry[reference]) is not str):
                    raise FixtureError("invalid pool entry shape")

    @staticmethod
    def _reply(raw, request):
        if not raw.endswith(b"\n"):
            raise FixtureError("response ended without a newline")
        reply = decode_json(raw.decode("utf-8"))
        if type(reply) is not dict:
            raise FixtureError("response must be an object")
        payload = set(reply) & {"receipt", "view", "reward_ids", "pool_view", "error"}
        if len(payload) != 1:
            raise FixtureError("response requires one payload")
        exact_fields(reply, {"operation", "provenance"} | payload, "response")
        if reply["provenance"] != PROVENANCE:
            raise FixtureError("invalid response provenance")
        key = next(iter(payload))
        if key == "error":
            error = reply[key]
            fields = {"code"} if type(error) is dict and set(error) == {"code"} else {"type", "message"}
            exact_fields(error, fields, "response error")
            if any(type(error[field]) is not str for field in fields):
                raise FixtureError("response error values must be strings")
        startup = key == "error" and reply["operation"] is None
        if not startup and (type(reply["operation"]) is not str
                            or reply["operation"] != request["operation"]):
            raise FixtureError("response operation does not match request")
        if key != "error":
            if key != _DISPATCH[request["operation"]][3]:
                raise FixtureError("response payload does not match operation")
            value = reply[key]
            if key == "reward_ids":
                if type(value) is not list or any(type(item) is not str for item in value):
                    raise FixtureError("reward_ids must be an array of strings")
            elif key == "pool_view":
                RewardClient._pool_payload(value)
            else:
                if type(value) is not dict:
                    raise FixtureError("response payload must be an object")
                reward = value.get("reward") if key == "receipt" else value
                if type(reward) is not dict or type(reward.get("reward_id")) is not str:
                    raise FixtureError("response reward must contain a string reward_id")
        # Domain refusals alone permit another explicit request. Every typed
        # CLI error and every null-operation setup error terminates this child.
        return reply, startup or (key == "error" and "type" in reply[key])

    def request(self, request: dict) -> dict:
        if not self._guard.acquire(blocking=False):
            raise RewardClientStateError("another request or cleanup is outstanding")
        try:
            if self._closed or self._terminal or self.uncertainty is not None:
                raise RewardClientStateError("client is closed, terminal or uncertain")
            if type(request) is not dict:
                raise TypeError("request must be a dictionary")
            # Fail serialization before submission; retain the actual wire snapshot
            # even if the caller later mutates its dictionary.
            self._validate_request(request)
            wire = (_canonical(request) + "\n").encode("utf-8")
            submitted = decode_json(wire.decode("utf-8"))
            raw = bytearray()
            try:
                written = self._process.stdin.write(wire)
                if written != len(wire):
                    raise OSError("short request write")
                self._process.stdin.flush()
                # Retain partial diagnostic bytes even on caller interruption.
                while True:
                    chunk = self._process.stdout.read(1)
                    if not chunk:
                        break
                    raw.extend(chunk)
                    if chunk == b"\n":
                        break
                reply, terminal = self._reply(bytes(raw), submitted)
                self._terminal = terminal
                return reply
            except BaseException as error:
                # Includes caller interruption after submission has begun. Never
                # interpret missing evidence as a business rejection or rollback.
                self._terminal = True
                self.uncertainty = RewardTransportUncertainty(submitted, wire, bytes(raw))
                raise self.uncertainty from error
        finally:
            self._guard.release()

    def close(self) -> int:
        """Close stdin, reap this child, and return its exit code; idempotent.

        After the explicit cleanup deadline, terminate then kill if necessary.
        Previous transport uncertainty remains available on self.uncertainty.
        """
        if not self._guard.acquire(blocking=False):
            raise RewardClientStateError("another request or cleanup is outstanding")
        try:
            if self._closed:
                return self._returncode
            self._terminal = True
            try:
                try:
                    self._process.stdin.close()
                except (BrokenPipeError, OSError):
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
                self._returncode = self._process.returncode
                self._closed = True
                return self._returncode
            finally:
                self._process.stdout.close()
        finally:
            self._guard.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
