"""CLI transcript and one-call stream gaps, over unchanged domain behavior."""

from contextlib import redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ai_delegation_mock import AiDelegationError, FALSE_FLAGS, LIFECYCLE, PROVENANCE, _canonical
from delegation_cli import dispatch_request, run_requests
from delegation_fixture import decode_json, load_fixture
from test_delegation_session import FIXTURES, OPERATIONS, requests


CLI = Path(__file__).with_name("delegation_cli.py")


def envelope():
    return {"provenance": PROVENANCE, "lifecycle_authority": LIFECYCLE,
            **{flag: False for flag in FALSE_FLAGS}}


def grant(**overrides):
    return {**envelope(), "grant_id":"g-1", "generation":1, "issuer":"human-a",
            "agent_id":"agent-a", "authority":["PROPOSE", "QUERY"],
            "scope":{"surfaces":["surface-a"], "subjects":["subject-a"]},
            "limits":{"per_action_max":100, "cumulative_max":150, "count_max":2, "currency":"KRW"},
            "period":{"not_before":10, "not_after":20}, "phase":"ACTIVE",
            "revoked_at_seq":None, "reason":None, **overrides}


def proposal(identifier, **overrides):
    return {**envelope(), "proposal_id":identifier, "grant_id":"g-1", "generation":1,
            "tool":"propose_action", "phase":"PROPOSED", "surface":"surface-a",
            "subject":"subject-a", "amount":25, "kind":"synthetic-kind", "memo":None,
            "decision":None, "effects_executed":False, **overrides}


class DelegationCliTests(unittest.TestCase):
    def invoke(self, text=None, path=None, fixture=None):
        return subprocess.run(
            [sys.executable, str(CLI), "--fixture", str(fixture or FIXTURES / "delegation_session.json"),
             "--requests", str(path) if path else "-"],
            input=text, capture_output=True, text=True, encoding="utf-8", timeout=20,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE":"1"})

    def output(self, completed, status):
        self.assertEqual(completed.returncode, status, completed.stderr + completed.stdout)
        self.assertEqual(completed.stderr, "")
        rows = [decode_json(line) for line in completed.stdout.splitlines()]
        self.assertEqual(completed.stdout, "".join(_canonical(row) + "\n" for row in rows))
        for row in rows:
            self.assertEqual(row["provenance"], PROVENANCE)
            self.assertEqual(len(row), 3)
            self.assertEqual(len(set(row) & {"receipt", "view", "error"}), 1)
            body = row.get("view") or row.get("receipt")
            if body:
                view = body.get("grant") or body.get("proposal") or body
                self.assertEqual(view["provenance"], PROVENANCE)
                self.assertEqual(view["lifecycle_authority"], LIFECYCLE)
                self.assertEqual(len(FALSE_FLAGS), 11)
                for flag in FALSE_FLAGS:
                    self.assertIs(view[flag], False)
                if "effects_executed" in view:
                    self.assertIs(view["effects_executed"], False)
        return rows

    def test_file_stdin_and_repeated_process_transcripts_are_identical(self):
        for name, status in (("lifecycle", 0), ("boundaries", 1), ("replay", 1)):
            with self.subTest(name=name):
                path = FIXTURES / (name + ".jsonl")
                first = self.invoke(path=path)
                rows = self.output(first, status)
                self.assertEqual(len(rows), len(requests(name)))
                by_stdin = self.invoke(text=path.read_text(encoding="utf-8"))
                self.output(by_stdin, status)
                self.assertEqual(by_stdin.stdout, first.stdout)
                repeated = self.invoke(path=path)
                self.output(repeated, status)
                self.assertEqual(repeated.stdout, first.stdout)
        self.assertEqual(self.output(self.invoke(text=""), 0), [])

    def test_lifecycle_complete_receipts_retained_views_and_inert_change_memo(self):
        rows = self.output(self.invoke(path=FIXTURES / "lifecycle.jsonl"), 0)
        self.assertEqual(rows[0], {"operation":"issue_grant", "provenance":PROVENANCE,
                                   "receipt":{"duplicate":False, "grant":grant()}})
        self.assertEqual(rows[1]["receipt"], {"duplicate":False, "grant":grant()})
        self.assertEqual(rows[2]["receipt"], {**envelope(), "duplicate":False,
                         "match":{"surface":"surface-a", "subject":"subject-a", "in_scope":True}})
        for index, expected in ((3, proposal("p-approved")),
                                (4, proposal("p-approved", phase="HUMAN_APPROVED", decision="APPROVE")),
                                (5, proposal("p-rejected")),
                                (6, proposal("p-rejected", phase="HUMAN_REJECTED", decision="REJECT")),
                                (7, proposal("p-withdrawn")),
                                (8, proposal("p-withdrawn", phase="WITHDRAWN"))):
            self.assertEqual(rows[index]["receipt"], {"duplicate":False, "proposal":expected})
        memo = requests("lifecycle")[9]["arguments"]["args"]["requested"]
        memo["scope"]["subjects"] = None  # Existing mock normalization in stored memos.
        change = proposal("p-change", tool="propose_grant_change", surface=None, subject=None,
                          amount=None, kind="GRANT_CHANGE", memo=memo)
        self.assertEqual(rows[9]["receipt"], {"duplicate":False, "proposal":change})
        self.assertEqual(rows[10]["view"], grant())
        revoked = grant(phase="REVOKED", revoked_at_seq=1, reason="synthetic-stop")
        self.assertEqual(rows[11]["receipt"], {"duplicate":False, "grant":revoked})
        self.assertEqual(rows[12]["view"], {**change, "phase":"VOIDED_BY_REVOCATION"})
        for index, expected in ((13, proposal("p-approved", phase="HUMAN_APPROVED", decision="APPROVE")),
                                (14, proposal("p-rejected", phase="HUMAN_REJECTED", decision="REJECT")),
                                (15, proposal("p-withdrawn", phase="WITHDRAWN")), (16, revoked)):
            self.assertEqual(rows[index]["view"], expected)
        self.assertEqual(rows[17]["receipt"], {"duplicate":False, "grant":grant(
            grant_id="g-2", generation=2, scope={"surfaces":["surface-a"], "subjects":None})})
        self.assertEqual(rows[18]["receipt"], {**envelope(), "duplicate":False,
                         "match":{"surface":"surface-a", "subject":None, "in_scope":True}})

    def test_boundary_error_codes_are_domain_codes_including_disabled_execution(self):
        rows = self.output(self.invoke(path=FIXTURES / "boundaries.jsonl"), 1)
        expected = [
            "UNKNOWN_ACTOR", "AI_SELF_EXPANSION_FORBIDDEN", "EXECUTE_AUTHORITY_DISABLED",
            "LIMIT_REQUIRED", "INVALID_PERIOD", "SCOPE_VIOLATION", "INVALID_AMOUNT",
            "GRANT_NOT_CURRENT", "UNKNOWN_ACTOR", "UNKNOWN_ACTOR", "UNKNOWN_GRANT",
            "TRANSFER_FORBIDDEN", "REFUND_EXECUTION_FORBIDDEN", "SIGNING_FORBIDDEN",
            "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY", "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY",
            "AI_SELF_EXPANSION_FORBIDDEN", "AI_SELF_EXPANSION_FORBIDDEN", "AI_SELF_EXPANSION_FORBIDDEN",
            "TOOL_NOT_ALLOWED", "TOOL_NOT_ALLOWED", "TOOL_NOT_ALLOWED",
            "GRANT_NOT_CURRENT", "GRANT_EXPIRED", "INVALID_PERIOD", "INVALID_ID",
            "SCOPE_VIOLATION", "SCOPE_VIOLATION", "EXECUTE_AUTHORITY_DISABLED",
            "PER_ACTION_EXCEEDED", "INVALID_AMOUNT", "CUMULATIVE_EXCEEDED", "COUNT_EXCEEDED",
            "AI_CANNOT_DECIDE", "UNKNOWN_PROPOSAL", "INVALID_ID", "GRANT_EXPIRED",
            "DELEGATED_EXECUTION_DISABLED", "DELEGATED_EXECUTION_DISABLED", "UNKNOWN_PROPOSAL",
            "GRANT_REVOKED", "GRANT_REVOKED", "TOOL_NOT_ALLOWED", "TOOL_NOT_ALLOWED"]
        self.assertEqual([r["error"] for r in rows if "error" in r], [{"code":c} for c in expected])
        retained = next(r["view"] for r in rows if r["operation"] == "view_proposal" and "view" in r)
        self.assertEqual(retained, proposal("p-1", amount=100, phase="VOIDED_BY_REVOCATION"))

    def test_replay_returns_current_records_and_preserves_first_revocation_reason(self):
        rows = self.output(self.invoke(path=FIXTURES / "replay.jsonl"), 1)
        self.assertEqual([r["error"] for r in rows if "error" in r], [
            {"code":"PROPOSAL_BINDING_CONFLICT"}, {"code":"PROPOSAL_BINDING_CONFLICT"},
            {"code":"GRANT_BINDING_CONFLICT"}, {"code":"PROPOSAL_BINDING_CONFLICT"}])
        for original, duplicate in ((0,1), (2,3), (4,5), (4,6), (11,12), (11,13),
                                    (15,16), (15,17), (20,21), (23,24)):
            self.assertEqual(rows[duplicate]["receipt"], {**rows[original]["receipt"], "duplicate":True})
        self.assertEqual(rows[6]["receipt"], {"duplicate":True, "proposal":proposal(
            "p-approved", phase="HUMAN_APPROVED", decision="APPROVE")})
        self.assertEqual(rows[18]["receipt"], {"duplicate":True, "proposal":proposal(
            "p-void", phase="VOIDED_BY_REVOCATION")})
        self.assertEqual(rows[18]["receipt"]["proposal"], rows[19]["view"])
        self.assertEqual(rows[16]["receipt"]["grant"]["reason"], "first-reason")
        self.assertEqual(rows[22]["view"], rows[27]["view"])
        self.assertEqual(rows[24]["receipt"]["grant"]["generation"], 2)
        self.assertEqual(rows[26]["view"]["phase"], "HUMAN_APPROVED")

    def test_one_selected_call_per_line_with_no_implicit_views_or_retries(self):
        examples = {r["operation"]:r for name in ("lifecycle", "boundaries") for r in requests(name)}
        self.assertEqual(set(examples), set(OPERATIONS))
        session = load_fixture(FIXTURES / "delegation_session.json")
        for operation, request in examples.items():
            with self.subTest(operation=operation), patch.object(session, "_mock") as mock:
                selected = getattr(mock, operation)
                selected.return_value = {"opaque":False}
                with redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(run_requests(session, [_canonical(request)]), 0)
                self.assertEqual(len(mock.mock_calls), 1)
                self.assertEqual(mock.mock_calls[0][0], operation)
                self.assertEqual(len(output.getvalue().splitlines()), 1)
                mock.reset_mock()
                selected.side_effect = AiDelegationError("DELEGATED_EXECUTION_DISABLED")
                with redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(run_requests(session, [_canonical(request)] * 2), 1)
                self.assertEqual(len(mock.mock_calls), 2)
                self.assertEqual(mock.mock_calls[0], mock.mock_calls[1])
                self.assertEqual(len(output.getvalue().splitlines()), 2)

    def test_malformed_stops_before_dispatch_and_does_not_consume_proposal_id(self):
        session = load_fixture(FIXTURES / "delegation_session.json")
        issue, proposal_request = requests("lifecycle")[0], requests("lifecycle")[3]
        malformed = copy.deepcopy(proposal_request)
        malformed["arguments"]["extra"] = True
        with patch.object(session._mock, "call_tool", wraps=session._mock.call_tool) as method:
            with redirect_stdout(io.StringIO()) as output:
                self.assertEqual(run_requests(session, map(_canonical, (issue, malformed, proposal_request))), 2)
            method.assert_not_called()
            rows = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[-1]["error"]["type"], "FixtureError")
            self.assertFalse(dispatch_request(session, proposal_request)["receipt"]["duplicate"])
            method.assert_called_once()

    def test_domain_rejection_advances_only_to_explicit_supplied_line(self):
        issued = _canonical(requests("lifecycle")[0])
        execution = _canonical({"operation":"attempt_execution", "arguments":{
            "actor":"human-a", "proposal_id":"missing"}})
        view = _canonical({"operation":"view_grant", "arguments":{"grant_id":"g-1"}})
        rows = self.output(self.invoke(text="\n".join((issued, execution, view))), 1)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]["error"], {"code":"DELEGATED_EXECUTION_DISABLED"})
        self.assertEqual(rows[2]["view"], grant())
        rows = self.output(self.invoke(text=execution + '\n{bad}\n' + issued), 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["error"]["type"], "FixtureError")

    def test_malformed_setup_unicode_and_io_failures_exit_two_without_tracebacks(self):
        for text in ('\n', '{bad}\n', '{"operation":"view_grant","arguments":{},"arguments":{}}\n',
                     '{"operation":"view_grant","arguments":{"grant_id":1e9999}}\n',
                     '{"operation":"view_grant","arguments":{"grant_id":"\\ud800"}}\n'):
            rows = self.output(self.invoke(text=text + _canonical(requests("lifecycle")[0])), 2)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["error"]["type"], "FixtureError")
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            for result in (self.invoke(path=missing), self.invoke(text="", fixture=missing)):
                rows = self.output(result, 2)
                self.assertEqual(rows[0]["error"]["type"], "FileNotFoundError")
            invalid = Path(directory) / "bad.jsonl"
            invalid.write_bytes(b'\xff\n')
            self.assertEqual(self.output(self.invoke(path=invalid), 2)[0]["error"]["type"], "UnicodeDecodeError")
            fixture = Path(directory) / "fixture.json"
            fixture.write_text('{"fixture_version":true}', encoding="utf-8")
            self.assertEqual(self.output(self.invoke(text="", fixture=fixture), 2)[0]["error"]["type"], "FixtureError")
            fixture.write_text(json.dumps({"fixture_version":1, "provenance":PROVENANCE,
                                          "human_principals":["same"], "ai_agents":["same"]}), encoding="utf-8")
            self.assertEqual(self.output(self.invoke(text="", fixture=fixture), 2)[0]["error"],
                             {"code":"MOCK_INVARIANT"})


if __name__ == "__main__":
    unittest.main()
