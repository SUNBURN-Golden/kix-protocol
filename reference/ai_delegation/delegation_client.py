"""Blocking, single-request client for the synthetic local delegation desk.

Importing launches nothing. No automatic restart, retry or replay; no persistence or sockets.
An uncertain exchange fences this instance; cleanup cannot undo accepted work.
"""

import math
from pathlib import Path
import subprocess
import sys
import threading

from delegation_fixture import FixtureError, decode_json, exact_fields, validate_fixture, validate_json
from delegation_cli import _DISPATCH
from ai_delegation_mock import FALSE_FLAGS, LIFECYCLE, PROVENANCE, _canonical


class DelegationClientStateError(RuntimeError):
    """Local rejection before submission: busy, closed or terminal client."""


class DelegationTransportUncertainty(RuntimeError):
    """A submitted request has no trustworthy complete response.

    request is the serialized snapshot, not an inferred business outcome.
    reply_bytes contains bytes observed before the failure. Neither authorizes
    resubmission, even if the desk exits or cleanup terminates it.
    """

    def __init__(self, request, request_bytes, reply_bytes):
        super().__init__("local delegation desk exchange uncertain; client fenced")
        self.request = request
        self.request_bytes = request_bytes
        self.reply_bytes = reply_bytes
        self.last_reply = None


class DelegationClient:
    """Own one explicitly launched desk and at most one outstanding request.

    Use launch(), then request() synchronously, and close() or a with block.
    Reads have no response timeout. cleanup_timeout applies only to close().
    close() rejects concurrent use too; interrupt the requesting caller first.
    """

    @classmethod
    def launch(cls, fixture, *, cleanup_timeout):
        cls._validate_cleanup_timeout(cleanup_timeout)
        return cls._launch(["--fixture", str(Path(fixture).resolve())], cleanup_timeout)

    @staticmethod
    def _validate_cleanup_timeout(cleanup_timeout):
        if (isinstance(cleanup_timeout, bool)
                or not isinstance(cleanup_timeout, (int, float))
                or not math.isfinite(cleanup_timeout) or cleanup_timeout <= 0):
            raise ValueError("cleanup_timeout must be a finite positive number")

    @classmethod
    def _launch(cls, startup, cleanup_timeout):
        command = [sys.executable, str(Path(__file__).with_name("delegation_cli.py").resolve()),
                   *startup, "--requests", "-"]
        # Child buffering is ordinary Python buffering. stderr is inherited,
        # never mixed with JSONL stdout or left in an undrained pipe.
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   bufsize=0, shell=False)
        return cls(process, cleanup_timeout)

    @classmethod
    def launch_from_fixture(cls, fixture, *, cleanup_timeout):
        """Submit one explicit startup snapshot and require a correlated ack.

        No domain-session preflight, replacement child, fallback or retry.
        A failed launch retains wire evidence on the raised uncertainty and
        closes/reaps its owned child before returning control to the caller.
        """
        cls._validate_cleanup_timeout(cleanup_timeout)
        validate_fixture(fixture)
        wire = (_canonical(fixture) + "\n").encode("utf-8")
        submitted = decode_json(wire.decode("utf-8"))
        client = cls._launch(["--init-stdin"], cleanup_timeout)
        raw = bytearray()
        try:
            client._write_frame(wire)
            client._read_frame(raw)
            reply = cls._initialization_reply(bytes(raw), submitted)
            client._initialized_reply = decode_json(_canonical(reply))
            return client
        except BaseException as error:
            client._terminal = True
            failure = DelegationTransportUncertainty(submitted, wire, bytes(raw))
            failure.last_reply = client.last_reply
            # A complete error is useful evidence, never an initialization ack.
            try:
                failure.last_reply = decode_json(bytes(raw).decode("utf-8"))
            except (ValueError, UnicodeError):
                pass
            client.uncertainty = failure
            try:
                client.close()
            except BaseException as cleanup_error:
                failure.cleanup_error = cleanup_error
                failure.add_note(f"startup cleanup failed: {type(cleanup_error).__name__}: {cleanup_error}")
            raise failure from error

    @property
    def initialized_reply(self):
        """Detached accepted startup envelope; None in fixture-file mode."""
        if self._initialized_reply is None:
            return None
        return decode_json(_canonical(self._initialized_reply))

    @staticmethod
    def _initialization_reply(raw, submitted):
        if not raw.endswith(b"\n") or b"\n" in raw[:-1]:
            raise FixtureError("initialization response requires one newline-terminated JSON frame")
        reply = decode_json(raw.decode("utf-8"))
        exact_fields(reply, {"operation", "provenance", "initialized"}, "initialization response")
        if reply["operation"] is not None or reply["provenance"] != PROVENANCE:
            raise FixtureError("invalid initialization response operation/provenance")
        validate_fixture(reply["initialized"])
        for name in ("human_principals", "ai_agents"):
            registry = reply["initialized"][name]
            if type(registry) is not list or any(type(item) is not str for item in registry):
                raise FixtureError("initialization response requires string registries")
        if _canonical(reply["initialized"]) != _canonical(submitted):
            raise FixtureError("initialization response does not match submitted fixture")
        return reply

    def __init__(self, process, cleanup_timeout):
        self._process = process
        self._cleanup_timeout = cleanup_timeout
        self._guard = threading.Lock()
        self._terminal = False
        self._closed = False
        self._returncode = None
        self.uncertainty = None
        self.last_reply = None
        self._initialized_reply = None

    def _write_frame(self, wire):
        if self._process.stdin.write(wire) != len(wire):
            raise OSError("short request write")
        self._process.stdin.flush()

    def _read_frame(self, raw):
        # Retain every observed byte, including on caller interruption.
        while True:
            chunk = self._process.stdout.read(1)
            if not chunk:
                break
            raw.extend(chunk)
            if chunk == b"\n":
                break

    @staticmethod
    def _validate_request(request):
        # Share the existing selector/signature table; no session or model call.
        validate_json(request)
        exact_fields(request, {"operation", "arguments"}, "request")
        operation = request["operation"]
        if type(operation) is not str or operation not in _DISPATCH:
            raise FixtureError("unsupported session operation")
        _, required, _ = _DISPATCH[operation]
        exact_fields(request["arguments"], required, f"{operation} arguments")
        # Nested inputs are deliberately left to the unchanged mock.

    @staticmethod
    def _types(value, fields):
        for name, allowed in fields.items():
            if type(value[name]) not in allowed:
                raise FixtureError(f"invalid response field type: {name}")

    @staticmethod
    def _scope(value):
        exact_fields(value, {"surfaces", "subjects"}, "response scope")
        for key in value:
            items = value[key]
            if key == "subjects" and items is None:
                continue
            if type(items) is not list or any(type(item) is not str for item in items):
                raise FixtureError("scope requires string arrays or nullable subjects")

    @staticmethod
    def _structured(value, name):
        if name == "scope":
            DelegationClient._scope(value)
        elif name == "authority":
            if type(value) is not list or any(type(item) is not str for item in value):
                raise FixtureError("authority requires a string array")
        elif name == "limits":
            exact_fields(value, {"per_action_max", "cumulative_max", "count_max", "currency"}, name)
            DelegationClient._types(value, {key: (str,) if key == "currency" else (int,) for key in value})
        elif name == "period":
            exact_fields(value, {"not_before", "not_after"}, name)
            DelegationClient._types(value, {key: (int,) for key in value})
        elif type(value) is not str:
            raise FixtureError("memo note requires a string")

    @staticmethod
    def _common(value, fields):
        exact_fields(value, {"provenance", "lifecycle_authority", *FALSE_FLAGS, *fields}, "response record")
        if value["provenance"] != PROVENANCE or value["lifecycle_authority"] != LIFECYCLE:
            raise FixtureError("invalid record provenance/lifecycle")
        if any(value[flag] is not False for flag in FALSE_FLAGS):
            raise FixtureError("effect flags must remain false")
        DelegationClient._types(value, fields)

    @staticmethod
    def _record(value, kind, request):
        nullable_str = (str, type(None))
        if kind == "grant":
            DelegationClient._common(value, {
                "grant_id": (str,), "generation": (int,), "issuer": (str,), "agent_id": (str,),
                "authority": (list,), "scope": (dict,), "limits": (dict,), "period": (dict,),
                "phase": (str,), "revoked_at_seq": (int, type(None)), "reason": nullable_str})
            for name in ("authority", "scope", "limits", "period"):
                DelegationClient._structured(value[name], name)
        else:
            DelegationClient._common(value, {
                "proposal_id": (str,), "grant_id": (str,), "generation": (int,),
                "tool": (str,), "phase": (str,), "surface": nullable_str, "subject": nullable_str,
                "amount": (int, type(None)), "kind": (str,), "memo": (dict, type(None)),
                "decision": nullable_str, "effects_executed": (bool,)})
            if value["effects_executed"] is not False:
                raise FixtureError("proposal effects must remain false")
            if value["memo"] is not None:
                memo = value["memo"]
                exact_fields(memo, set(), "response memo", {"authority", "scope", "limits", "period", "note"})
                for name in memo:
                    DelegationClient._structured(memo[name], name)
        # Correlate identifiers only; do not recompute authorization, bindings,
        # limits, phases, generations, decisions or replay predicates.
        args = request["arguments"]
        for name in ("grant_id", "proposal_id"):
            if name in args and name in value and value[name] != args[name]:
                raise FixtureError(f"response {name} does not match request")
        if kind == "grant":
            if request["operation"] in {"issue_grant", "revoke_grant"} and value["issuer"] != args["actor"]:
                raise FixtureError("grant issuer does not match request")
            if request["operation"] == "issue_grant" and value["agent_id"] != args["agent_id"]:
                raise FixtureError("grant agent does not match request")
            if request["operation"] == "call_tool" and value["agent_id"] != args["actor"]:
                raise FixtureError("queried grant agent does not match request")
        if request["operation"] == "call_tool" and kind == "proposal":
            if value["proposal_id"] != args["args"].get("proposal_id"):
                raise FixtureError("response proposal_id does not match tool request")

    @staticmethod
    def _reply(raw, request):
        if not raw.endswith(b"\n") or b"\n" in raw[:-1]:
            raise FixtureError("response requires one newline-terminated JSON frame")
        reply = decode_json(raw.decode("utf-8"))
        if type(reply) is not dict:
            raise FixtureError("response must be an object")
        payload = set(reply) & {"receipt", "view", "error"}
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
            DelegationClient._types(error, {field: (str,) for field in fields})
        startup = key == "error" and reply["operation"] is None
        if not startup and reply["operation"] != request["operation"]:
            raise FixtureError("response operation does not match request")
        if key != "error":
            op, args = request["operation"], request["arguments"]
            if op == "attempt_execution":
                raise FixtureError("execution success is forbidden")
            if key != _DISPATCH[op][2]:
                raise FixtureError("response payload does not match operation")
            value = reply[key]
            if key == "view":
                DelegationClient._record(value, "grant" if op == "view_grant" else "proposal", request)
            elif op == "call_tool" and args["tool"] == "query_subject":
                DelegationClient._common(value, {"duplicate": (bool,), "match": (dict,)})
                match = value["match"]
                exact_fields(match, {"surface", "subject", "in_scope"}, "response match")
                DelegationClient._types(match, {"surface": (str,), "subject": (str, type(None)), "in_scope": (bool,)})
                if match["surface"] != args["args"].get("surface") or match["subject"] != args["args"].get("subject"):
                    raise FixtureError("response match does not match request")
            else:
                kind = ("grant" if op in {"issue_grant", "revoke_grant"}
                        or (op == "call_tool" and args["tool"] == "query_grant") else "proposal")
                # An unsupported tool cannot legitimately return a receipt.
                if op == "call_tool" and args["tool"] not in {
                        "query_grant", "propose_action", "propose_grant_change", "withdraw_proposal"}:
                    raise FixtureError("unexpected tool receipt")
                exact_fields(value, {"duplicate", kind}, "response receipt")
                DelegationClient._types(value, {"duplicate": (bool,)})
                DelegationClient._record(value[kind], kind, request)
        return reply, startup or (key == "error" and (
            "type" in reply[key] or reply[key].get("code") == "MOCK_INVARIANT"))

    def request(self, request: dict) -> dict:
        if not self._guard.acquire(blocking=False):
            raise DelegationClientStateError("another request or cleanup is outstanding")
        try:
            if self._closed or self._terminal or self.uncertainty is not None:
                raise DelegationClientStateError("client is closed, terminal or uncertain")
            if type(request) is not dict:
                raise TypeError("request must be a dictionary")
            # Fail serialization before submission; retain the actual wire snapshot
            # even if the caller later mutates its dictionary.
            self._validate_request(request)
            wire = (_canonical(request) + "\n").encode("utf-8")
            submitted = decode_json(wire.decode("utf-8"))
            raw = bytearray()
            try:
                self._write_frame(wire)
                self._read_frame(raw)
                reply, terminal = self._reply(bytes(raw), submitted)
                self.last_reply = decode_json(_canonical(reply))
                self._terminal = terminal
                return reply
            except BaseException as error:
                # Includes caller interruption after submission has begun. Never
                # interpret missing evidence as a business rejection or rollback.
                self._terminal = True
                self.uncertainty = DelegationTransportUncertainty(submitted, wire, bytes(raw))
                self.uncertainty.last_reply = self.last_reply
                raise self.uncertainty from error
        finally:
            self._guard.release()

    def close(self) -> int:
        """Close stdin, reap this child, and return its exit code; idempotent.

        After the explicit cleanup deadline, terminate then kill if necessary.
        Previous transport uncertainty remains available on self.uncertainty.
        """
        if not self._guard.acquire(blocking=False):
            raise DelegationClientStateError("another request or cleanup is outstanding")
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
                        self._process.wait(timeout=self._cleanup_timeout)
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
