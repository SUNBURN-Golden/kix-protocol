"""Offline readiness-wrap replay probes; source-informed, synthetic fixtures.

AI_DELEGATION_AUTHORITY DLG-25/26 and READINESS_RUNTIME restart replay define
same-binding duplicate paths (A). Omission has no explicit equivalent value
in the scope schema: omitted/[]/null distinctions are characterizations (B).
Owner policy values stay UNDETERMINED; no execution is enabled.
"""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(1, str(ROOT))  # Keep this suite first for default discovery.

from readiness.ai_delegation_wrap import AiDelegationWrap, WrapError
from ai_delegation_mock import AiDelegationError

DUPLICATE = ("ok", True, None)
INVALID = ("error", "INVALID_ID")
SCOPE_VARIANTS = ({"surfaces": ["s-a"]},
                  {"surfaces": ["s-a"], "subjects": []},
                  {"surfaces": ["s-a"], "subjects": ["x1"]},
                  {"surfaces": ["s-a"], "subjects": None})


def grant_body(grant_id="g-open", actor="H", agent="A", scope=None):
    return dict(actor=actor, grant_id=grant_id, agent_id=agent,
                authority=["QUERY", "PROPOSE"],
                scope=deepcopy(SCOPE_VARIANTS[0] if scope is None else scope),
                limits={"per_action_max": 60, "cumulative_max": 100,
                        "count_max": 8, "currency": "KRW"},
                period={"not_before": 10, "not_after": 20})


def tool_body(tool, args, listed=False):
    return dict(actor="A2" if listed else "A", grant_id="g-list" if listed else "g-open",
                tool=tool, args=deepcopy(args), now=15)


def call(wrap, command):
    op, fields = command
    return getattr(wrap, op)(**json.loads(json.dumps(fields)))


def outcome(fn):
    try:
        result = fn()
    except (AiDelegationError, WrapError) as error:
        return ("error", error.code)
    return ("ok", result["duplicate"], result.get("applied"))


def registry():
    wrap = AiDelegationWrap()
    wrap.open_registry(["H", "H2"], ["A", "A2"])
    return wrap


def fixture():
    wrap = registry()
    wrap.issue_grant(**grant_body())
    wrap.issue_grant(**grant_body("g-list", "H2", "A2", SCOPE_VARIANTS[2]))
    return wrap


def probe(test, factory, first, retries):
    wrap = factory()
    test.assertEqual(outcome(lambda: call(wrap, first)), ("ok", False, None))
    state, journal = wrap.canonical_state(), wrap.export_journal()
    for retry, expected in retries:
        with test.subTest(first=first, retry=retry):
            test.assertEqual(outcome(lambda: call(wrap, retry)), expected)
            test.assertEqual(wrap.canonical_state(), state)
            test.assertEqual(wrap.export_journal(), journal)
            restored = AiDelegationWrap.restore(deepcopy(journal))
            test.assertEqual(restored.canonical_state(), state)
            test.assertEqual(restored.state_digest(), wrap.state_digest())
            test.assertEqual(outcome(lambda: call(restored, retry)), expected)
            test.assertEqual(restored.canonical_state(), state)
            test.assertEqual(restored.export_journal(), journal)


def scope_commands(op):
    if op == "issue_grant":
        return [(op, grant_body("g-probe", scope=scope)) for scope in SCOPE_VARIANTS]
    return [("call_tool", tool_body("propose_grant_change",
             dict(proposal_id="p-change", requested={"scope": scope})))
            for scope in SCOPE_VARIANTS]


def action_commands():
    base = dict(proposal_id="p-action", surface="s-a", amount=1, kind="k")
    return [("call_tool", tool_body("propose_action", args))
            for args in (base, dict(base, subject="x1"), dict(base, subject=None))]


class AiDelegationRestoreFingerprintClassATests(unittest.TestCase):
    """DLG-25/26, §7; READINESS_RUNTIME file journal restart replay."""

    def test_same_grant_binding_replays(self):
        for first in scope_commands("issue_grant")[:3]:
            probe(self, registry, first, [(first, DUPLICATE)])

    def test_same_requested_scope_binding_replays(self):
        for first in scope_commands("propose_grant_change")[:3]:
            probe(self, fixture, first, [(first, DUPLICATE)])

    def test_same_action_subject_binding_replays(self):
        for first in action_commands()[:2]:
            probe(self, fixture, first, [(first, DUPLICATE)])

    def test_query_subject_is_not_journalled(self):
        """DLG-01/§7 step 6: query is read-only; omitted scope subjects unrestricted."""
        wrap = fixture()
        state, journal = wrap.canonical_state(), wrap.export_journal()
        for listed in (False, True):
            for args in ({"surface": "s-a"}, {"surface": "s-a", "subject": "x1"}):
                cmd = ("call_tool", tool_body("query_subject", args, listed))
                # §5 explicitly makes subject optional, including on g-list.
                expected = ("ok", False, None)
                restored = AiDelegationWrap.restore(deepcopy(journal))
                for target in (wrap, restored):
                    self.assertEqual(target.canonical_state(), state)
                    self.assertEqual(outcome(lambda: call(target, cmd)), expected)
                    if expected[0] == "ok":
                        self.assertEqual(call(target, cmd)["match"],
                                         dict(surface="s-a", subject=args.get("subject"), in_scope=True))
                    self.assertEqual(target.canonical_state(), state)
                    self.assertEqual(target.export_journal(), journal)


class AiDelegationRestoreFingerprintCharacterizationTests(unittest.TestCase):
    """Contract undefined (B): omitted versus explicit scope/subject binding/parse."""

    def test_scope_subject_variants(self):
        for op in ("issue_grant", "propose_grant_change"):
            commands = scope_commands(op)
            conflict = ("error", "GRANT_BINDING_CONFLICT" if op == "issue_grant"
                        else "PROPOSAL_BINDING_CONFLICT")
            for index, first in enumerate(commands[:3]):
                retries = [(retry, INVALID if n == 3 else conflict)
                           for n, retry in enumerate(commands) if n != index]
                probe(self, registry if op == "issue_grant" else fixture, first, retries)

    def test_action_subject_variants(self):
        commands = action_commands()
        for index, first in enumerate(commands[:2]):
            retries = [(retry, INVALID if n == 2 else ("error", "PROPOSAL_BINDING_CONFLICT"))
                       for n, retry in enumerate(commands) if n != index]
            probe(self, fixture, first, retries)


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
