"""Deterministic full-state rejection checks through the readiness wrap.

Builder-authored, source-informed, offline tests. Identifiers, amounts, limits
and periods are synthetic fixtures, not product policy. Journal and restore
checks use the existing public wrap, not a harness command log. No execution.
"""

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(1, str(ROOT))  # Keep this suite first for default discovery.

from readiness.ai_delegation_wrap import AiDelegationWrap, WrapError
from ai_delegation_mock import AiDelegationError, FALSE_FLAGS


def grant_args(**overrides):
    args = dict(
        actor="H", grant_id="g-new", agent_id="A",
        authority=["QUERY", "PROPOSE"],
        scope={"surfaces": ["s-a"], "subjects": ["x1"]},
        limits={"per_action_max": 60, "cumulative_max": 100,
                "count_max": 3, "currency": "KRW"},
        period={"not_before": 10, "not_after": 20},
    )
    args.update(overrides)
    return args


def action_args(**overrides):
    args = dict(proposal_id="p-next", surface="s-a", subject="x1",
                amount=1, kind="k")
    args.update(overrides)
    return args


def tool_args(tool="query_grant", args=None, **overrides):
    fields = dict(actor="A", grant_id="g1", tool=tool,
                  args={} if args is None else args, now=15)
    fields.update(overrides)
    return fields


NEXT = ("call_tool", tool_args("propose_action", action_args()))

# One contract code per row, one intentionally violated guard per call. The
# count case alone fills the count before taking the rejection snapshot.
CASES = (
    ("AI_SELF_EXPANSION_FORBIDDEN", "issue_grant", grant_args(actor="A"), None),
    ("AI_CANNOT_DECIDE", "decide_proposal",
     dict(actor="A", proposal_id="p1", decision="APPROVE", now=15), None),
    ("UNKNOWN_ACTOR", "call_tool", tool_args(actor="stranger"), None),
    ("UNKNOWN_GRANT", "revoke_grant",
     dict(actor="H", grant_id="missing", reason="stop"), None),
    ("UNKNOWN_PROPOSAL", "decide_proposal",
     dict(actor="H", proposal_id="missing", decision="APPROVE", now=15), None),
    ("TOOL_NOT_ALLOWED", "call_tool",
     tool_args("propose_action", action_args(), actor="A2", grant_id="g2"), None),
    ("TRANSFER_FORBIDDEN", "call_tool", tool_args("transfer"), None),
    ("REFUND_EXECUTION_FORBIDDEN", "call_tool", tool_args("refund_execution"), None),
    ("SIGNING_FORBIDDEN", "call_tool", tool_args("sign"), None),
    ("MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY", "call_tool", tool_args("pay"), None),
    ("EXECUTE_AUTHORITY_DISABLED", "issue_grant",
     grant_args(actor="H2", agent_id="A2", authority=["EXECUTE"]), None),
    ("DELEGATED_EXECUTION_DISABLED", "attempt_execution",
     dict(actor="A", proposal_id="p1"), None),
    ("GRANT_NOT_CURRENT", "call_tool", tool_args(now=9), None),
    ("GRANT_REVOKED", "call_tool", tool_args(grant_id="g3"), None),
    ("GRANT_EXPIRED", "call_tool", tool_args(now=21), None),
    ("SCOPE_VIOLATION", "call_tool",
     tool_args("propose_action", action_args(surface="s-b")), None),
    ("LIMIT_REQUIRED", "issue_grant",
     grant_args(actor="H2", agent_id="A2", limits={
         "per_action_max": 60, "cumulative_max": 100,
         "count_max": 3, "currency": "USD"}), None),
    ("PER_ACTION_EXCEEDED", "call_tool",
     tool_args("propose_action", action_args(amount=61)), None),
    ("CUMULATIVE_EXCEEDED", "call_tool",
     tool_args("propose_action", action_args(amount=41)), None),
    ("COUNT_EXCEEDED", "call_tool",
     tool_args("propose_action", action_args()),
     ("revoke_grant", dict(actor="H", grant_id="g1", reason="next"))),
    ("INVALID_ID", "call_tool", tool_args(args={"x": 1}), None),
    ("INVALID_AMOUNT", "call_tool",
     tool_args("propose_action", action_args(amount=0)), None),
    ("INVALID_PERIOD", "call_tool", tool_args(now=-1), None),
    ("GRANT_BINDING_CONFLICT", "issue_grant",
     grant_args(grant_id="g1", scope={"surfaces": ["s-b"], "subjects": ["x1"]}), None),
    ("PROPOSAL_BINDING_CONFLICT", "call_tool",
     tool_args("propose_action", action_args(proposal_id="p1", amount=59)), None),
)


def call(wrap, command):
    method, kwargs = command
    # Every fixture travels through the same plain-JSON argument surface.
    return getattr(wrap, method)(**json.loads(json.dumps(kwargs)))


def snapshot(wrap):
    state = wrap.canonical_state()
    return dict(
        digest=wrap.state_digest(), state=state, journal=wrap.export_journal(),
        views=dict(
            grants=[wrap.view_grant(row["grant_id"]) for row in state["grants"]],
            proposals=[wrap.view_proposal(row["proposal_id"]) for row in state["proposals"]],
        ),
    )


class RejectionAtomicityTests(unittest.TestCase):
    def build(self, code):
        wrap = AiDelegationWrap()
        opened = wrap.open_registry(["H", "H2"], ["A", "A2"])
        self.assertIs(opened["execution_enabled"], False)
        self.assertIs(opened["durable"], False)
        wrap.issue_grant(**grant_args(grant_id="g1"))
        # Keep cumulative room in the per-action case so only that cap fails.
        amount = 1 if code == "PER_ACTION_EXCEEDED" else 60
        wrap.call_tool(**tool_args("propose_action", action_args(proposal_id="p1", amount=amount)))
        wrap.issue_grant(**grant_args(grant_id="g2", agent_id="A2", authority=["QUERY"]))
        wrap.issue_grant(**grant_args(grant_id="g3", actor="H2"))
        wrap.revoke_grant("H2", "g3", "fixture-stop")
        if code == "COUNT_EXCEEDED":
            # Count-only memos avoid tripping either amount guard first.
            for identifier in ("change-1", "change-2"):
                wrap.call_tool(**tool_args("propose_grant_change", dict(
                    proposal_id=identifier, requested={"note": "fixture-change"})))
        return wrap

    def checked_snapshot(self, wrap):
        observed = snapshot(wrap)
        for kind, views in observed["views"].items():
            for view in views:
                for flag in FALSE_FLAGS:
                    self.assertIs(view[flag], False, (kind, flag))
                if kind == "proposals":
                    self.assertIs(view["effects_executed"], False)
        return observed

    def test_every_aid_code_is_atomic_and_recoverable(self):
        for code, method, kwargs, next_command in CASES:
            with self.subTest(code=code):
                subject = self.build(code)
                control = self.build(code)
                before = self.checked_snapshot(subject)
                self.assertEqual(before, self.checked_snapshot(control))

                with self.assertRaises(AiDelegationError) as caught:
                    call(subject, (method, kwargs))
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(self.checked_snapshot(subject), before)
                self.assertEqual(self.checked_snapshot(subject), self.checked_snapshot(control))

                restored = AiDelegationWrap.restore(subject.export_journal())
                self.assertEqual(self.checked_snapshot(restored), before)

                command = next_command or NEXT
                # Check validity on the independently built, unrejected control.
                expected = call(control, command)
                self.assertIs(expected["duplicate"], False)
                self.assertEqual(call(subject, command), expected)
                self.assertEqual(call(restored, command), expected)
                after = self.checked_snapshot(control)
                self.assertNotEqual(after["state"], before["state"])
                self.assertEqual(len(after["journal"]), len(before["journal"]) + 1)
                self.assertEqual(after["journal"][:-1], before["journal"])
                self.assertEqual(self.checked_snapshot(subject), after)
                self.assertEqual(self.checked_snapshot(restored), after)
                recovered_after_progress = AiDelegationWrap.restore(subject.export_journal())
                self.assertEqual(self.checked_snapshot(recovered_after_progress), after)

    def test_cases_cover_every_contract_code(self):
        contract = (ROOT / "docs/contracts/AI_DELEGATION_AUTHORITY.md").read_text(encoding="utf-8")
        section = contract.split("## 8. 오류 코드와 항상 거짓인 플래그\n", 1)[1].split("\n## 9.", 1)[0]
        table_codes = re.findall(r"^\| `([A-Z][A-Z0-9_]+)` \|", section, re.MULTILINE)
        wanted = set(table_codes) - {"MOCK_INVARIANT"}
        codes = [row[0] for row in CASES]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(set(codes), wanted)
        # Literal code names also expose this corpus to the AST coverage checker.
        self.assertEqual(wanted, {
            "AI_SELF_EXPANSION_FORBIDDEN", "AI_CANNOT_DECIDE", "UNKNOWN_ACTOR",
            "UNKNOWN_GRANT", "UNKNOWN_PROPOSAL", "TOOL_NOT_ALLOWED",
            "TRANSFER_FORBIDDEN", "REFUND_EXECUTION_FORBIDDEN", "SIGNING_FORBIDDEN",
            "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY", "EXECUTE_AUTHORITY_DISABLED",
            "DELEGATED_EXECUTION_DISABLED", "GRANT_NOT_CURRENT", "GRANT_REVOKED",
            "GRANT_EXPIRED", "SCOPE_VIOLATION", "LIMIT_REQUIRED",
            "PER_ACTION_EXCEEDED", "CUMULATIVE_EXCEEDED", "COUNT_EXCEEDED",
            "INVALID_ID", "INVALID_AMOUNT", "INVALID_PERIOD",
            "GRANT_BINDING_CONFLICT", "PROPOSAL_BINDING_CONFLICT",
        })

    def test_unopened_registry_rejection_leaves_no_trace(self):
        """Class B: invalid registry open, empty restore and subsequent valid open."""
        subject, control = AiDelegationWrap(), AiDelegationWrap()
        before = subject.state_digest()
        self.assertEqual(before, control.state_digest())
        with self.assertRaises(AiDelegationError) as caught:
            subject.open_registry([""], [])
        self.assertEqual(caught.exception.code, "INVALID_ID")
        self.assertEqual(subject.export_journal(), [])
        self.assertEqual(subject.state_digest(), before)
        restored = AiDelegationWrap.restore(subject.export_journal())
        for wrap in (subject, control, restored):
            self.assertEqual(wrap.export_journal(), [])
            self.assertEqual(wrap.state_digest(), before)
            with self.assertRaises(WrapError) as unopened:
                wrap.canonical_state()
            self.assertEqual(unopened.exception.code, "NOT_OPEN")
        expected = control.open_registry(["H"], ["A"])
        self.assertIs(expected["execution_enabled"], False)
        self.assertIs(expected["durable"], False)
        for wrap in (subject, restored):
            self.assertEqual(wrap.open_registry(["H"], ["A"]), expected)
            self.assertEqual(self.checked_snapshot(wrap), self.checked_snapshot(control))
        self.assertEqual(len(control.export_journal()), 1)
        self.assertEqual(self.checked_snapshot(AiDelegationWrap.restore(subject.export_journal())),
                         self.checked_snapshot(control))


class SiblingImportPathTests(unittest.TestCase):
    """Import-origin guard (audit #15): this suite's mock, ROOT's readiness wrap."""

    def test_imports_resolve_from_intended_directories(self):
        here = Path(__file__).resolve().parent
        mock_file = Path(sys.modules[AiDelegationError.__module__].__file__).resolve()
        wrap_file = Path(sys.modules[AiDelegationWrap.__module__].__file__).resolve()
        self.assertEqual(mock_file.parent, here)
        self.assertEqual(wrap_file.parent, ROOT / "readiness")


if __name__ == "__main__":
    unittest.main()
