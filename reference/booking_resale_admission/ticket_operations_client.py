"""Blocking, single-request client for the synthetic local ticket desk.

Importing launches nothing. No restart, retry, replay, persistence or sockets.
An uncertain exchange fences this instance; cleanup cannot undo accepted work.
"""

import json
import math
from pathlib import Path
import subprocess
import sys
import threading

from admission_fixture import FixtureError, decode_json, exact_fields


class TicketDeskClientStateError(RuntimeError):
    """Local rejection before submission: busy, closed or terminal client."""


class TicketDeskTransportUncertainty(RuntimeError):
    """A submitted request has no trustworthy complete response.

    request is the serialized snapshot, not an inferred business outcome.
    reply_bytes contains bytes observed before the failure. Neither authorizes
    resubmission, even if the desk exits or cleanup terminates it.
    """

    def __init__(self, request, request_bytes, reply_bytes):
        super().__init__("local ticket desk exchange uncertain; client fenced")
        self.request = request
        self.request_bytes = request_bytes
        self.reply_bytes = reply_bytes


class TicketOperationsClient:
    """Own one explicitly launched desk and at most one outstanding request.

    Use launch(), then request() synchronously, and close() or a with block.
    Reads have no response timeout. cleanup_timeout applies only to close().
    close() rejects concurrent use too; interrupt the requesting caller first.
    """

    @classmethod
    def launch(cls, fixture, *, quotes=None, calculated_quotes=None, cleanup_timeout):
        if (isinstance(cleanup_timeout, bool)
                or not isinstance(cleanup_timeout, (int, float))
                or not math.isfinite(cleanup_timeout) or cleanup_timeout <= 0):
            raise ValueError("cleanup_timeout must be a finite positive number")
        if quotes is not None and calculated_quotes is not None:
            raise ValueError("quotes and calculated_quotes are mutually exclusive")
        command = [sys.executable, str(Path(__file__).with_name("ticket_operations_cli.py").resolve()),
                   "--fixture", str(Path(fixture).resolve()), "--requests", "-"]
        for option, path in (("--quotes", quotes), ("--calculated-quotes", calculated_quotes)):
            if path is not None:
                command.extend((option, str(Path(path).resolve())))
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
    def _reply(raw, request):
        if not raw.endswith(b"\n"):
            raise FixtureError("response ended without a newline")
        reply = decode_json(raw.decode("utf-8"))
        if type(reply) is not dict:
            raise FixtureError("response must be an object")
        payload = set(reply) & {"receipt", "view", "quote", "error"}
        if len(payload) != 1:
            raise FixtureError("response requires one payload")
        exact_fields(reply, {"surface", "operation"} | payload, "response")
        key = next(iter(payload))
        if type(reply[key]) is not dict:
            raise FixtureError("response payload must be an object")
        if key == "error":
            error = reply[key]
            if set(error) == {"code"}:
                fields = {"code"}
            else:
                fields = {"type", "message"}
            exact_fields(error, fields, "response error")
            if any(type(error[field]) is not str for field in fields):
                raise FixtureError("response error values must be strings")
        startup = (key == "error" and reply["surface"] is None
                   and reply["operation"] is None)
        for selector in ("surface", "operation"):
            if type(reply[selector]) is not str and not (key == "error" and reply[selector] is None):
                raise FixtureError("invalid response selector")
            expected = request.get(selector)
            expected = expected if type(expected) is str else None
            if not startup and reply[selector] != expected:
                raise FixtureError("response selectors do not match request")
        terminal = startup or (key == "error" and reply[key].get("type") in
                               {"FixtureError", "BookingInputError"})
        return reply, terminal

    def request(self, request: dict) -> dict:
        if not self._guard.acquire(blocking=False):
            raise TicketDeskClientStateError("another request or cleanup is outstanding")
        try:
            if self._closed or self._terminal or self.uncertainty is not None:
                raise TicketDeskClientStateError("client is closed, terminal or uncertain")
            if type(request) is not dict:
                raise TypeError("request must be a dictionary")
            # Fail serialization before submission; retain the actual wire snapshot
            # even if the caller later mutates its dictionary.
            wire = (json.dumps(request, allow_nan=False) + "\n").encode("utf-8")
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
                self.uncertainty = TicketDeskTransportUncertainty(submitted, wire, bytes(raw))
                raise self.uncertainty from error
        finally:
            self._guard.release()

    def close(self) -> int:
        """Close stdin, reap this child, and return its exit code; idempotent.

        After the explicit cleanup deadline, terminate then kill if necessary.
        Previous transport uncertainty remains available on self.uncertainty.
        """
        if not self._guard.acquire(blocking=False):
            raise TicketDeskClientStateError("another request or cleanup is outstanding")
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
