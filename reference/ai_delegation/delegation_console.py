"""Guide explicit human inputs through one synthetic, in-memory delegation desk."""

import argparse
from pathlib import Path
import sys

from ai_delegation_mock import AiDelegationError, _canonical
from delegation_cli import _error, dispatch_request
from delegation_fixture import FixtureError, decode_json, exact_fields, load_fixture, validate_json


# Presentation and structural input checks only; domain predicates stay in the mock.
_FIELDS = {
    "issue_grant": ("actor", "grant_id", "agent_id", "authority", "scope", "limits", "period"),
    "call_tool": ("actor", "grant_id", "tool", "args", "now"),
    "decide_proposal": ("actor", "proposal_id", "decision", "now"),
    "revoke_grant": ("actor", "grant_id", "reason"),
    "view_grant": ("grant_id",),
    "view_proposal": ("proposal_id",),
    "attempt_execution": ("actor", "proposal_id"),
}
_TOOLS = {
    "query_grant": (set(), set()),
    "query_subject": ({"surface"}, {"subject"}),
    "propose_action": ({"proposal_id", "surface", "amount", "kind"}, {"subject"}),
    "withdraw_proposal": ({"proposal_id"}, set()),
    "propose_grant_change": ({"proposal_id", "requested"}, set()),
}
_HINTS = {
    "authority": 'JSON array of strings; QUERY / PROPOSE; EXECUTE is refused',
    "scope": 'JSON object: surfaces array, optional subjects array',
    "limits": 'JSON object: per_action_max, cumulative_max, count_max integers, currency string',
    "period": 'JSON object: not_before, not_after logical integers',
    "args": 'JSON object matching the selected tool; see README schemas',
    "now": 'JSON integer; caller logical time, no wall clock',
    "decision": 'APPROVE / REJECT; approval records an inert memo only',
}


def _type(value, expected, name):
    if type(value) is not expected:
        raise FixtureError(f"{name} requires {expected.__name__}")


def _structure(name, value):
    """Reject missing fields and wrong JSON types, without inventing policy values."""
    if name == "authority":
        _type(value, list, name)
        for item in value:
            _type(item, str, name + " item")
    elif name == "scope":
        exact_fields(value, {"surfaces"}, name, {"subjects"})
        for key, items in value.items():
            _type(items, list, key)
            for item in items:
                _type(item, str, key + " item")
    elif name == "limits":
        exact_fields(value, {"per_action_max", "cumulative_max", "count_max", "currency"}, name)
        for key, item in value.items():
            _type(item, str if key == "currency" else int, key)
    elif name == "period":
        exact_fields(value, {"not_before", "not_after"}, name)
        for key, item in value.items():
            _type(item, int, key)
    elif name == "requested":
        exact_fields(value, set(), name, {"authority", "scope", "limits", "period", "note"})
        for key, item in value.items():
            _structure(key, item)
    else:
        _type(value, int if name in {"amount", "now"} else str, name)


def _tool_args(tool, value):
    _type(value, dict, "args")
    # Denied/unknown tool names are passed to the existing domain refusal path.
    if tool in _TOOLS:
        required, optional = _TOOLS[tool]
        exact_fields(value, required, tool + " args", optional)
        for name, item in value.items():
            _structure(name, item)


def _write(stream, text):
    if stream.write(text) != len(text):
        raise OSError("short console write; no further submissions")
    stream.flush()


def _diagnostic(error, stream, *, operation=None, last_reply=None):
    try:
        _write(stream, "FENCED: " + _canonical({
            "failure": _error(operation, error), "last_reply": last_reply}) + "\n")
    except (Exception, KeyboardInterrupt):
        pass  # A failed diagnostic never re-enters the action loop.


def run_console(session, *, input_stream, output_stream, error_stream) -> int:
    """Confirm and dispatch once per explicit action; terminal failures never retry."""
    last_reply = None
    operation = None
    rejected = False

    def say(text):
        _write(output_stream, text + "\n")

    def prompt(label):
        _write(output_stream, label + ": ")
        line = input_stream.readline()
        if line == "":
            raise EOFError("input ended; no further submissions")
        return line.removesuffix("\n").removesuffix("\r")

    try:
        say("Local delegation console — MOCK_AI_DELEGATION_ONLY; one synthetic in-memory session.\n"
            "All execution/effect flags remain false. Human approval is an inert memo.\n"
            "Product limits/surfaces: UNDETERMINED — Astra; identity: Astra/User; legal: User/legal.\n"
            "Duplicate grants/proposals return CURRENT records; revocation keeps its first reason.\n"
            "Replay by explicitly re-entering and confirming; no automatic retries or model service.")
        while True:
            operation = None
            say("Actions: " + ", ".join(_FIELDS) + ", quit\n"
                "attempt_execution is always refused; views also require confirmation.")
            selection = prompt("action")
            if selection == "quit":
                return int(rejected)
            if selection not in _FIELDS:
                say("Unknown action; no request sent.")
                continue
            operation = selection
            try:
                arguments = {}
                for name in _FIELDS[operation]:
                    if name == "tool":
                        say("Supported tools: " + ", ".join(_TOOLS))
                    raw = prompt(name + (" (" + _HINTS[name] + ")" if name in _HINTS else ""))
                    if name in {"authority", "scope", "limits", "period", "args", "now"}:
                        value = decode_json(raw)
                    else:
                        if not raw or raw != raw.strip():
                            raise FixtureError(name + " requires an explicit value without surrounding whitespace")
                        value = raw
                    validate_json(value)
                    if name == "args":
                        _tool_args(arguments["tool"], value)
                    else:
                        _structure(name, value)
                    arguments[name] = value
                request = {"operation": operation, "arguments": arguments}
                say("\nproposed=" + _canonical(request))
                if prompt("Type literal SUBMIT to send once; anything else declines") != "SUBMIT":
                    say("Declined; no request sent.")
                    continue
            except FixtureError as error:
                say("input_error=" + _canonical(_error(operation, error)))
                continue
            terminal = None
            try:
                reply = dispatch_request(session, request)
            except AiDelegationError as error:
                reply = _error(operation, error)
                rejected = True
                if error.code == "MOCK_INVARIANT":
                    terminal = error
            except FixtureError as error:
                reply = _error(operation, error)
                terminal = error
            last_reply = reply  # Retain the unchanged complete envelope before output can fail.
            say("\ndesk=" + _canonical(reply))
            if terminal is not None:
                raise terminal
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, error_stream, operation=operation, last_reply=last_reply)
        return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True,
                        help="explicit synthetic registry fixture; no default")
    args = parser.parse_args(argv)
    try:
        session = load_fixture(args.fixture)
    except (Exception, KeyboardInterrupt) as error:
        _diagnostic(error, sys.stderr)
        return 2
    return run_console(session, input_stream=sys.stdin, output_stream=sys.stdout, error_stream=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
