"""Console gaps: real desk transcripts, confirmation and terminal stream failures.

Expectations use pre-existing desk fixtures and literal lifecycle/error predicates,
independently of the console's prompt tables. This is source-informed verification.
"""

import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from ai_delegation_mock import AiDelegationError, FALSE_FLAGS, LIFECYCLE, PROVENANCE, _canonical
from delegation_cli import dispatch_request
from delegation_console import main, run_console
from delegation_fixture import FixtureError, load_fixture


FIXTURES = Path(__file__).with_name("fixtures")
CONSOLE = Path(__file__).with_name("delegation_console.py")


def session():
    return load_fixture(FIXTURES / "delegation_session.json")


def desk_requests(name):
    return [json.loads(line) for line in (FIXTURES / (name + ".jsonl")).read_text().splitlines()]


def entered(request, confirmation="SUBMIT"):
    # Independent specification order; never read console implementation tables.
    a = request["arguments"]
    op = request["operation"]
    if op == "issue_grant":
        values = [a["actor"], a["grant_id"], a["agent_id"], _canonical(a["authority"]),
                  _canonical(a["scope"]), _canonical(a["limits"]), _canonical(a["period"])]
    elif op == "call_tool":
        values = [a["actor"], a["grant_id"], a["tool"], _canonical(a["args"]), _canonical(a["now"])]
    elif op == "decide_proposal":
        values = [a["actor"], a["proposal_id"], a["decision"], _canonical(a["now"])]
    elif op == "revoke_grant":
        values = [a["actor"], a["grant_id"], a["reason"]]
    elif op == "attempt_execution":
        values = [a["actor"], a["proposal_id"]]
    else:
        values = [a["grant_id"] if op == "view_grant" else a["proposal_id"]]
    return "\n".join([op, *values, confirmation]) + "\n"


def guided_value(name, value, *, tool=None):
    """Test input renderer from the documented schema, never console field tables.

    Expected envelopes always come from literal requests / pre-existing desk vectors.
    """
    def items(values):
        return [str(len(values)), *values]

    def optional(obj, key):
        return ["include", *nested(key, obj[key])] if key in obj else ["omit"]

    def nested(key, item):
        if key in {"authority", "scope", "limits", "period", "requested"}:
            return guided_value(key, item)
        return [_canonical(item) if key == "amount" else item]

    if name == "authority":
        lines = items(value)
    elif name == "scope":
        lines = items(value["surfaces"])
        lines += ["include", *items(value["subjects"])] if "subjects" in value else ["omit"]
    elif name == "limits":
        lines = [str(value[k]) for k in ("per_action_max", "cumulative_max", "count_max")]
        lines += [value["currency"]]
    elif name == "period":
        lines = [str(value["not_before"]), str(value["not_after"])]
    elif name == "requested":
        lines = []
        for key in ("authority", "scope", "limits", "period", "note"):
            lines += optional(value, key)
    elif tool == "query_grant":
        lines = []
    elif tool == "query_subject":
        lines = [value["surface"], *optional(value, "subject")]
    elif tool == "propose_action":
        lines = [value["proposal_id"], value["surface"], str(value["amount"]), value["kind"],
                 *optional(value, "subject")]
    elif tool == "withdraw_proposal":
        lines = [value["proposal_id"]]
    elif tool == "propose_grant_change":
        lines = [value["proposal_id"], *guided_value("requested", value["requested"])]
    else:
        return [_canonical(value)]  # Denied/unknown tools keep raw JSON input.
    return [":guided", *lines]


def guided_entered(request, confirmation="SUBMIT"):
    a, op = request["arguments"], request["operation"]
    if op == "issue_grant":
        lines = [op, a["actor"], a["grant_id"], a["agent_id"]]
        for name in ("authority", "scope", "limits", "period"):
            lines += guided_value(name, a[name])
    elif op == "call_tool":
        lines = [op, a["actor"], a["grant_id"], a["tool"],
                 *guided_value("args", a["args"], tool=a["tool"]), str(a["now"])]
    else:
        return entered(request, confirmation)
    return "\n".join([*lines, confirmation]) + "\n"


def records(output, prefix):
    return [json.loads(line[len(prefix):]) for line in output.splitlines() if line.startswith(prefix)]


class FailingOutput(io.StringIO):
    def __init__(self, marker, mode):
        super().__init__()
        self.marker, self.mode, self.armed = marker, mode, False

    def write(self, text):
        if self.marker in text:
            if self.mode == "write":
                raise OSError("output unavailable")
            if self.mode == "short":
                return len(text) - 1
            self.armed = True
        return super().write(text)

    def flush(self):
        if self.armed:
            raise OSError("flush unavailable")
        return super().flush()


class ConsoleTests(unittest.TestCase):
    def run_input(self, text, *, target=None, output=None, errors=None, source=None):
        output = output if output is not None else io.StringIO()
        errors = errors if errors is not None else io.StringIO()
        target = target if target is not None else session()
        with patch("delegation_console.dispatch_request", wraps=dispatch_request) as dispatch:
            status = run_console(target, input_stream=source if source is not None else io.StringIO(text),
                                 output_stream=output, error_stream=errors)
        return status, output.getvalue(), errors.getvalue(), dispatch

    def assert_envelopes(self, rows):
        for row in rows:
            self.assertEqual(row["provenance"], PROVENANCE)
            self.assertEqual(len(row), 3)
            self.assertEqual(len(set(row) & {"receipt", "view", "error"}), 1)
            body = row.get("view") or row.get("receipt")
            if body is not None:
                body = body.get("grant") or body.get("proposal") or body
                self.assertEqual(body["provenance"], PROVENANCE)
                self.assertEqual(body["lifecycle_authority"], LIFECYCLE)
                self.assertEqual(len(FALSE_FLAGS), 11)
                for flag in FALSE_FLAGS:
                    self.assertIs(body[flag], False)
                if "effects_executed" in body:
                    self.assertIs(body["effects_executed"], False)

    def transcript(self, name, expected_requests, expected_status):
        text = (FIXTURES / ("delegation_console_" + name + ".txt")).read_text()
        target = session()
        with patch.object(target, "_mock", Mock(wraps=target._mock)) as domain:
            status, output, errors, spy = self.run_input(text, target=target)
        self.assertEqual(len(domain.mock_calls), len(expected_requests))
        self.assertEqual([call[0] for call in domain.mock_calls],
                         [request["operation"] for request in expected_requests])
        self.assertEqual(status, expected_status, errors + output)
        self.assertEqual(errors, "")
        previews, replies = records(output, "proposed="), records(output, "desk=")
        self.assertEqual(previews, expected_requests)
        self.assertEqual([c.args[1] for c in spy.call_args_list], expected_requests)
        self.assertEqual(spy.call_count, len(expected_requests))
        direct, expected = session(), []
        for request in expected_requests:
            try:
                expected.append(dispatch_request(direct, request))
            except AiDelegationError as error:
                expected.append({"operation":request["operation"], "provenance":PROVENANCE,
                                 "error":{"code":error.code}})
        self.assertEqual(replies, expected)
        self.assert_envelopes(replies)
        return replies

    def assert_guided_raw_parity(self, requests, *, expected_status=None):
        outcomes = []
        for render in (entered, guided_entered):
            status, output, errors, spy = self.run_input(
                "".join(render(r) for r in requests) + "quit\n")
            self.assertEqual(errors, "")
            self.assertEqual(records(output, "proposed="), requests)
            self.assertEqual([c.args[1] for c in spy.call_args_list], requests)
            self.assertEqual(spy.call_count, len(requests))
            replies = records(output, "desk=")
            self.assert_envelopes(replies)
            outcomes.append((status, replies))
        self.assertEqual(*outcomes)
        if expected_status is not None:
            self.assertEqual(outcomes[0][0], expected_status)
        return outcomes[0][1]

    def test_guided_raw_envelope_parity(self):
        rows = self.assert_guided_raw_parity(desk_requests("lifecycle"), expected_status=0)
        self.assertEqual(rows[4]["receipt"]["proposal"]["phase"], "HUMAN_APPROVED")
        self.assertEqual(rows[12]["view"]["phase"], "VOIDED_BY_REVOCATION")

    def test_guided_optionals_exact_integers_and_verbatim_strings(self):
        issue = desk_requests("lifecycle")[0]
        # Each independent literal input must survive preview and dispatch, even if
        # the unchanged mock refuses it. No composer-derived expected field tables.
        variants = [
            ("scope", {"surfaces": ["표면,opaque", "surface-a", "surface-a"]}),
            ("scope", {"surfaces": ["surface-a"], "subjects": []}),
            ("scope", {"surfaces": []}),
            ("authority", ["PROPOSE", "QUERY", "QUERY"]),
            ("authority", []), ("authority", ["EXECUTE"]),
            ("authority", [" QUERY ", "", ":guided"]),
            ("grant_id", "불투명:001,/id"),
            ("limits", {"per_action_max": 9007199254740993, "cumulative_max": 10**12,
                        "count_max": -1, "currency": " caller currency "}),
            ("limits", {"per_action_max": 1, "cumulative_max": 10**12,
                        "count_max": 10**12, "currency": "KRW"}),
            ("period", {"not_before": -9007199254740993, "not_after": 9007199254740993}),
        ]
        for key, value in variants:
            request = copy.deepcopy(issue)
            request["arguments"][key] = value
            with self.subTest(key=key, value=value):
                self.assert_guided_raw_parity([request])
        for args in ({"surface": "surface-a"}, {"surface": "surface-a", "subject": ""},
                     {"surface": "  표면,opaque  ", "subject": ":guided"}):
            request = {"operation": "call_tool", "arguments": {
                "actor": "agent-a", "grant_id": "g-1", "tool": "query_subject", "args": args, "now": 15}}
            self.assert_guided_raw_parity([issue, request])
        for amount in (0, -1, 1, 10**12, 10**12 + 1, 9007199254740993):
            request = copy.deepcopy(desk_requests("lifecycle")[3])
            request["arguments"]["args"]["amount"] = amount
            self.assert_guided_raw_parity([issue, request])
        for requested in ({}, {"note": ""}, {"note": "  메모,opaque  "},
                          {"authority": []}, {"scope": {"surfaces": [], "subjects": []}},
                          {"authority": ["EXECUTE"]}):
            request = {"operation": "call_tool", "arguments": {"actor": "agent-a", "grant_id": "g-1",
                "tool": "propose_grant_change", "args": {"proposal_id": "요청:001", "requested": requested},
                "now": 15}}
            self.assert_guided_raw_parity([issue, request])

    def test_guided_requested_allows_mixed_raw_structured_entry(self):
        request = desk_requests("lifecycle")[9]
        text = guided_entered(request)
        for key, value in request["arguments"]["args"]["requested"].items():
            if key != "note":
                text = text.replace("\n".join(guided_value(key, value)) + "\n", _canonical(value) + "\n", 1)
        status, output, errors, spy = self.run_input(text + "quit\n")
        self.assertEqual((status, errors, spy.call_count), (1, "", 1))  # no grant; composition still exact
        self.assertEqual(records(output, "proposed="), [request])
        self.assertEqual(spy.call_args.args[1], request)

    def test_guided_decline_and_eof_at_every_new_prompt_send_nothing(self):
        examples = [r for r in desk_requests("lifecycle") if r["operation"] in {"issue_grant", "call_tool"}]
        for request in examples:
            text = guided_entered(request)
            for count in range(len(text.splitlines(True))):
                with self.subTest(op=request["operation"], count=count, request=request):
                    status, _, errors, spy = self.run_input("".join(text.splitlines(True)[:count]))
                    self.assertEqual(status, 2)
                    self.assertIn("EOFError", errors)
                    spy.assert_not_called()
            for confirmation in ("", "no", "submit", " SUBMIT", "SUBMIT "):
                status, output, errors, spy = self.run_input(guided_entered(request, confirmation) + "quit\n")
                self.assertEqual((status, errors), (0, ""))
                self.assertEqual(records(output, "proposed="), [request])
                spy.assert_not_called()

    def test_guided_malformed_composition_discards_action(self):
        issue = "issue_grant\nhuman-a\ng-1\nagent-a\n"
        tool = "call_tool\nagent-a\ng-1\n"
        prefixes = []
        for invalid in ("-1", "true", "1.0", "null", "", "bad", "NaN", "1e9999", "[]"):
            prefixes += [issue + ":guided\n" + invalid + "\n",
                         issue + '[]\n:guided\n' + invalid + "\n",
                         issue + '[]\n:guided\n0\ninclude\n' + invalid + "\n"]
        for invalid in ("", "yes", "Include", " include", "omit "):
            prefixes += [issue + '[]\n:guided\n0\n' + invalid + "\n",
                         tool + 'query_subject\n:guided\ns\n' + invalid + "\n"]
            for earlier in range(5):
                prefixes += [tool + 'propose_grant_change\n:guided\np\n:guided\n' +
                             'omit\n' * earlier + invalid + "\n"]
        for invalid in ("true", "1.0", "null", "bad", "", "NaN"):
            for before in ([], ["1"], ["1", "2"]):
                prefixes += [issue + '[]\n{"surfaces":[]}\n:guided\n' +
                             "\n".join([*before, invalid]) + "\n"]
            for before in ([], ["0"]):
                prefixes += [issue + '[]\n{"surfaces":[]}\n' +
                    '{"per_action_max":1,"cumulative_max":2,"count_max":1,"currency":"KRW"}\n:guided\n' +
                    "\n".join([*before, invalid]) + "\n"]
            prefixes += [tool + 'propose_action\n:guided\np\ns\n' + invalid + "\n"]
        prefixes += [tool + name + "\n:guided\n" for name in ("transfer", "unknown", "delegate")]
        prefixes += [tool + 'propose_grant_change\n:guided\np\nnull\n',
                     tool + 'propose_grant_change\n:guided\np\n:guided\ninclude\nnull\n' + 'omit\n'*4,
                     issue + ':guided\n1\n\ud800\n{}\n{}\n{}\n']
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                status, output, errors, spy = self.run_input(prefix + "quit\n")
                self.assertEqual((status, errors), (0, ""))
                self.assertIn("input_error=", output)
                self.assertEqual(records(output, "proposed="), [])
                spy.assert_not_called()

    def test_guided_preview_and_prompt_output_failures_fence_sentinel(self):
        request = desk_requests("lifecycle")[0]
        text = guided_entered(request) + entered(request) + "quit\n"
        for marker, count in (("item count", 0), ("item 1", 0), ("include / omit", 0),
                              ("per_action_max (", 0), ("proposed=", 0), ("Type literal", 0), ("desk=", 1)):
            for mode in ("write", "short", "flush"):
                with self.subTest(marker=marker, mode=mode):
                    status, _, _, spy = self.run_input(text, output=FailingOutput(marker, mode))
                    self.assertEqual(status, 2)
                    self.assertEqual(spy.call_count, count)

    def test_console_journey(self):
        rows = self.transcript("journey", desk_requests("lifecycle"), 0)
        self.assertEqual(rows[4]["receipt"]["proposal"]["phase"], "HUMAN_APPROVED")
        self.assertIs(rows[4]["receipt"]["proposal"]["effects_executed"], False)
        self.assertEqual(rows[6]["receipt"]["proposal"]["phase"], "HUMAN_REJECTED")
        self.assertEqual(rows[8]["receipt"]["proposal"]["phase"], "WITHDRAWN")
        self.assertEqual(rows[10]["view"], rows[0]["receipt"]["grant"])
        self.assertEqual(rows[12]["view"]["phase"], "VOIDED_BY_REVOCATION")
        self.assertEqual([rows[i]["view"]["phase"] for i in (13, 14, 15, 16)],
                         ["HUMAN_APPROVED", "HUMAN_REJECTED", "WITHDRAWN", "REVOKED"])
        self.assertEqual(rows[17]["receipt"]["grant"]["generation"], 2)
        self.assertEqual({r["arguments"]["tool"] for r in desk_requests("lifecycle")
                          if r["operation"] == "call_tool"},
                         {"query_grant", "query_subject", "propose_action", "withdraw_proposal",
                          "propose_grant_change"})

    def test_console_replay(self):
        rows = self.transcript("replay", desk_requests("replay"), 1)
        for index, phase in ((6,"HUMAN_APPROVED"), (13,"WITHDRAWN"), (18,"VOIDED_BY_REVOCATION")):
            self.assertIs(rows[index]["receipt"]["duplicate"], True)
            self.assertEqual(rows[index]["receipt"]["proposal"]["phase"], phase)
        self.assertEqual(rows[17]["receipt"]["grant"]["phase"], "REVOKED")
        self.assertIs(rows[17]["receipt"]["duplicate"], True)
        self.assertEqual(rows[16]["receipt"]["grant"]["reason"], "first-reason")
        self.assertEqual([r["error"]["code"] for r in rows if "error" in r],
                         ["PROPOSAL_BINDING_CONFLICT", "PROPOSAL_BINDING_CONFLICT",
                          "GRANT_BINDING_CONFLICT", "PROPOSAL_BINDING_CONFLICT"])

    def test_console_boundaries(self):
        text = (FIXTURES / "delegation_console_boundaries.txt").read_text()
        status, output, errors, spy = self.run_input(text)
        self.assertEqual((status, errors), (1, ""))
        rows = records(output, "desk=")
        self.assertEqual(spy.call_count, 9)
        self.assertEqual(len(records(output, "proposed=")), 11)
        self.assertEqual(output.count("input_error="), 2)
        self.assertEqual([r["error"]["code"] for r in rows if "error" in r],
                         ["SCOPE_VIOLATION", "GRANT_EXPIRED", "PER_ACTION_EXCEEDED",
                          "TRANSFER_FORBIDDEN", "DELEGATED_EXECUTION_DISABLED", "GRANT_REVOKED"])
        self.assertEqual(rows[0]["receipt"]["grant"]["phase"], "ACTIVE")
        self.assertEqual(rows[-1]["view"]["phase"], "REVOKED")
        self.assert_envelopes(rows)

    def test_preview_is_complete_and_flushed_before_confirmation_without_session_calls(self):
        request = desk_requests("lifecycle")[0]
        target = session()
        class RecordingOutput(io.StringIO):
            flushed = ""
            def flush(inner):
                inner.flushed = inner.getvalue()
                super().flush()
        output = RecordingOutput()
        class CheckingInput(io.StringIO):
            def readline(inner):
                if inner.tell() == len(entered(request).removesuffix("SUBMIT\n")):
                    self.assertIn("proposed=" + _canonical(request) + "\n", output.flushed)
                    self.assertEqual(spy.call_count, 0)
                    domain.assert_not_called()
                    self.assertEqual(domain.mock_calls, [])
                return super().readline()
        with patch("delegation_console.dispatch_request", wraps=dispatch_request) as spy, patch.object(
                target, "_mock", Mock(wraps=target._mock)) as domain:
            self.assertEqual(run_console(target, input_stream=CheckingInput(entered(request) + "quit\n"),
                                         output_stream=output, error_stream=io.StringIO()), 0)
        spy.assert_called_once()
        self.assertEqual(spy.call_args.args[1], request)
        self.assertEqual(len(domain.mock_calls), 1)

    def test_declined_every_operation_has_no_dispatch_or_implicit_views(self):
        examples = {r["operation"]:r for r in desk_requests("lifecycle")}
        examples["attempt_execution"] = {"operation":"attempt_execution", "arguments":{
            "actor":"human-a", "proposal_id":"p-approved"}}
        for request in examples.values():
            for confirmation in ("no", "submit", " SUBMIT", "SUBMIT ", ""):
                with self.subTest(op=request["operation"], confirmation=confirmation):
                    status, output, errors, spy = self.run_input(entered(request, confirmation) + "quit\n")
                    self.assertEqual((status, errors), (0, ""))
                    spy.assert_not_called()
                    self.assertEqual(records(output, "proposed="), [request])
                    self.assertEqual(records(output, "desk="), [])

    def test_invalid_console_shapes_dispatch_zero_and_return_to_menu(self):
        issue = "issue_grant\nhuman-a\ng\nagent-a\n"
        tool = "call_tool\nagent-a\ng\n"
        prefixes = ["nonsense\n", "view_grant\n\n", "view_grant\n x\n", "view_grant\n\ud800\n",
                    issue + 'null\n', issue + '[1]\n', issue + '["QUERY","QUERY":1]\n',
                    issue + '["QUERY"]\n{}\n', issue + '["QUERY"]\n{"surfaces":"s"}\n',
                    issue + '["QUERY"]\n{"surfaces":[1]}\n',
                    issue + '["QUERY"]\n{"surfaces":[],"subjects":null}\n',
                    tool + 'query_grant\n{"extra":1}\n', tool + 'query_subject\n{}\n',
                    tool + 'query_subject\n{"surface":4}\n', tool + 'query_grant\n[]\n',
                    tool + 'propose_action\n{"proposal_id":"p","surface":"s","amount":true,"kind":"k"}\n',
                    tool + 'propose_grant_change\n{"proposal_id":"p","requested":{"extra":1}}\n',
                    tool + 'propose_grant_change\n{"proposal_id":"p","requested":{"period":{}}}\n',
                    tool + 'propose_grant_change\n{"proposal_id":"p","requested":{"note":false}}\n',
                    tool + 'query_grant\n{}\ntrue\n', tool + 'query_grant\n{}\n1.0\n']
        valid = entered(desk_requests("lifecycle")[0]).splitlines(keepends=True)
        for bad in ('{}', '{"per_action_max":1,"cumulative_max":2,"count_max":true,"currency":"KRW"}'):
            prefixes.append(''.join(valid[:6]) + bad + '\n')
        for bad in ('{}', '{"not_before":false,"not_after":2}', '{"not_before":0,"not_after":2,"x":1}'):
            prefixes.append(''.join(valid[:7]) + bad + '\n')
        for raw in ('{bad}', '{"surface":"s","surface":"s"}', '{"surface":NaN}',
                    '{"surface":1e9999}', '{"surface":"\\ud800"}'):
            prefixes.append(tool + 'query_subject\n' + raw + '\n')
        for text in prefixes:
            with self.subTest(text=text):
                status, output, errors, spy = self.run_input(text + "quit\n")
                self.assertEqual((status, errors), (0, ""))
                spy.assert_not_called()
                self.assertEqual(records(output, "proposed="), [])

    def test_confirmed_value_refusals_belong_to_mock_and_dispatch_once(self):
        issue = desk_requests("lifecycle")[0]
        for field, value, code in (("authority", ["EXECUTE"], "EXECUTE_AUTHORITY_DISABLED"),
                                    ("authority", [], "INVALID_ID"),
                                    ("actor", "unknown", "UNKNOWN_ACTOR"),
                                    ("period", {"not_before":20,"not_after":10}, "INVALID_PERIOD"),
                                    ("limits", {"per_action_max":0,"cumulative_max":2,
                                                "count_max":1,"currency":"KRW"}, "INVALID_AMOUNT")):
            request = copy.deepcopy(issue)
            request["arguments"][field] = value
            with self.subTest(field=field, value=value):
                status, output, errors, spy = self.run_input(entered(request) + "quit\n")
                self.assertEqual((status, errors, spy.call_count), (1, "", 1))
                self.assertEqual(records(output, "desk=")[0]["error"], {"code":code})

    def test_eof_at_each_grant_prompt_or_confirmation_never_dispatches(self):
        lines = entered(desk_requests("lifecycle")[0]).splitlines(keepends=True)
        for count in range(len(lines)):
            with self.subTest(count=count):
                status, _, errors, spy = self.run_input(''.join(lines[:count]))
                self.assertEqual(status, 2)
                spy.assert_not_called()
                self.assertIn('EOFError', errors)

    def test_input_errors_and_interruptions_fence_sentinel(self):
        text = entered(desk_requests("lifecycle")[0]) + "view_grant\ng-1\nSUBMIT\nquit\n"
        for error in (OSError("read failed"), UnicodeError("decode failed"),
                      RuntimeError("unexpected read"), KeyboardInterrupt()):
            for at in (0, 8, 9):
                class FailedInput(io.StringIO):
                    count = 0
                    def readline(inner):
                        inner.count += 1
                        if inner.count == at + 1:
                            raise error
                        return super().readline()
                with self.subTest(error=type(error).__name__, at=at):
                    status, _, _, spy = self.run_input("", source=FailedInput(text))
                    self.assertEqual(status, 2)
                    self.assertEqual(spy.call_count, int(at == 9))

    def test_output_write_short_write_and_flush_failures_fence_sentinel(self):
        request = desk_requests("lifecycle")[0]
        text = entered(request) + "view_grant\ng-1\nSUBMIT\nquit\n"
        for marker, count in (("Local delegation",0), ("actor: ",0), ("proposed=",0),
                              ("Type literal",0), ("desk=",1), ("Actions:",0)):
            for mode in ("write", "short", "flush"):
                with self.subTest(marker=marker, mode=mode):
                    target = session()
                    status, _, errors, spy = self.run_input(text, target=target,
                                                           output=FailingOutput(marker, mode))
                    self.assertEqual(status, 2)
                    self.assertEqual(spy.call_count, count)
                    if count:
                        diagnostic = json.loads(errors.removeprefix("FENCED: "))
                        self.assertEqual(diagnostic["last_reply"], {
                            "operation":"issue_grant", "provenance":PROVENANCE,
                            "receipt":{"duplicate":False, "grant":target.view_grant("g-1")}})
                        self.assertEqual(target.view_grant("g-1")["phase"], "ACTIVE")

    def test_unexpected_dispatch_errors_invariant_and_bad_diagnostic_stop_without_retry(self):
        request = desk_requests("lifecycle")[0]
        text = entered(request) + entered(request) + "quit\n"
        for error in (RuntimeError("unexpected dispatch"), FixtureError("internal transport"),
                      AiDelegationError("MOCK_INVARIANT"), KeyboardInterrupt()):
            for bad_diagnostic in (False, True):
                output = io.StringIO()
                errors = FailingOutput("FENCED:", "write") if bad_diagnostic else io.StringIO()
                target = session()
                def applied_then_failed(s, r):
                    dispatch_request(s, r)
                    raise error
                with self.subTest(error=type(error).__name__, bad_diagnostic=bad_diagnostic), patch(
                        "delegation_console.dispatch_request", side_effect=applied_then_failed) as spy:
                    self.assertEqual(run_console(target, input_stream=io.StringIO(text),
                                                 output_stream=output, error_stream=errors), 2)
                    spy.assert_called_once()
                    self.assertEqual(target.view_grant("g-1")["phase"], "ACTIVE")
                    if isinstance(error, AiDelegationError):
                        self.assertEqual(records(output.getvalue(), "desk=")[0]["error"],
                                         {"code":"MOCK_INVARIANT"})

    def test_executable_transcripts_and_fresh_processes(self):
        for name, status in (("journey",0), ("replay",1), ("boundaries",1)):
            text = (FIXTURES / ("delegation_console_" + name + ".txt")).read_text()
            outputs = []
            for _ in range(2):
                result = subprocess.run([sys.executable, str(CONSOLE), "--fixture",
                                         str(FIXTURES / "delegation_session.json")],
                                        input=text, capture_output=True, text=True, timeout=20,
                                        env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
                self.assertEqual((result.returncode, result.stderr), (status, ""))
                self.assert_envelopes(records(result.stdout, "desk="))
                outputs.append(result.stdout)
            self.assertEqual(*outputs)

    def test_setup_failure_never_dispatches_and_preserves_error_envelope(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "fixture.json"
            for content in (None, '{"fixture_version":true}', _canonical({
                    "fixture_version":1,"provenance":PROVENANCE,
                    "human_principals":["same"],"ai_agents":["same"]})):
                if content is not None:
                    fixture.write_text(content)
                errors = io.StringIO()
                with patch("delegation_console.sys.stderr", errors), patch(
                        "delegation_console.dispatch_request") as spy:
                    self.assertEqual(main(["--fixture", str(fixture)]), 2)
                spy.assert_not_called()
                diagnostic = json.loads(errors.getvalue().removeprefix("FENCED: "))
                self.assertIsNone(diagnostic["failure"]["operation"])
                self.assertEqual(diagnostic["failure"]["provenance"], PROVENANCE)
                if content is not None and "same" in content:
                    self.assertEqual(diagnostic["failure"]["error"], {"code":"MOCK_INVARIANT"})


if __name__ == "__main__":
    unittest.main()
