"""Deterministic checks for the offline AI delegation mock.

Amounts, periods, and identifiers in this file are fixtures.
They are not product limits, period lengths, or a named AI service.
"""

import ast
import hashlib
import inspect
import json
import re
import unittest
from pathlib import Path

from ai_delegation_mock import (
    ALLOWLIST,
    DENYLIST,
    FALSE_FLAGS,
    LIFECYCLE,
    PROVENANCE,
    AiDelegationError,
    AiDelegationMock,
)

HUMAN = "human-issuer"
OTHER = "human-other"
AGENT = "agent-1"
ROOT = Path(__file__).resolve().parents[2]


def limits(per=100, cum=1_000, count=5):
    return {
        "per_action_max": per,
        "cumulative_max": cum,
        "count_max": count,
        "currency": "KRW",
    }


def scope(surfaces=("surface-a", "delegate"), subjects=None):
    body = {"surfaces": list(surfaces)}
    if subjects is not None:
        body["subjects"] = list(subjects)
    return body


def period(start=10, end=20):
    return {"not_before": start, "not_after": end}


class AiDelegationMockTests(unittest.TestCase):
    def setUp(self):
        self.book = AiDelegationMock([HUMAN, OTHER], [AGENT, "agent-2"])

    def fails(self, fn):
        before = self.book.state_digest()
        try:
            fn()
        except AiDelegationError as error:
            self.assertEqual(self.book.state_digest(), before)
            return error.code
        self.fail("expected AiDelegationError")

    def issue(self, **overrides):
        args = {
            "actor": HUMAN,
            "grant_id": "g1",
            "agent_id": AGENT,
            "authority": ["QUERY", "PROPOSE"],
            "scope": scope(),
            "limits": limits(),
            "period": period(),
        }
        args.update(overrides)
        return self.book.issue_grant(**args)

    def propose(self, proposal_id="p1", amount=10, now=10, surface="surface-a", kind="fixture-kind", subject=None, grant_id="g1"):
        args = {"proposal_id": proposal_id, "surface": surface, "amount": amount, "kind": kind}
        if subject is not None:
            args["subject"] = subject
        return self.book.call_tool(AGENT, grant_id, "propose_action", args, now)

    def test_query_does_not_change_state_and_propose_is_a_memo(self):
        """DLG-01 DLG-02 DLG-30. Query and views leave the digest alone. A proposal adds only a memo."""
        self.issue()
        before = self.book.state_digest()
        state = self.book.canonical_state()
        viewed = self.book.view_grant("g1")
        self.assertEqual(viewed["provenance"], PROVENANCE)
        self.assertEqual(viewed["lifecycle_authority"], LIFECYCLE)
        queried = self.book.call_tool(AGENT, "g1", "query_grant", {}, 10)
        self.assertEqual(queried["grant"]["provenance"], PROVENANCE)
        found = self.book.call_tool(AGENT, "g1", "query_subject", {"surface": "delegate"}, 15)
        self.assertEqual(found["provenance"], PROVENANCE)
        self.assertEqual(found["lifecycle_authority"], LIFECYCLE)
        self.assertTrue(found["match"]["in_scope"])
        self.assertFalse(found["execution_enabled"])
        self.assertEqual(self.book.state_digest(), before)
        self.assertEqual(self.book.canonical_state(), state)
        viewed["phase"] = "REVOKED"
        self.assertEqual(self.book.view_grant("g1")["phase"], "ACTIVE")
        proposed = self.propose(amount=5)
        self.assertEqual(proposed["proposal"]["phase"], "PROPOSED")
        self.assertFalse(proposed["proposal"]["effects_executed"])
        self.assertIs(proposed["proposal"]["issued"], False)
        self.assertIs(proposed["proposal"]["paid"], False)
        self.assertNotEqual(self.book.state_digest(), before)
        self.assertEqual(self.book.canonical_state()["grants"], state["grants"])

    def test_execute_authority_and_attempt_are_disabled(self):
        """DLG-03 DLG-04 DLG-31. EXECUTE cannot be granted, and execution cannot be switched on."""
        params = list(inspect.signature(AiDelegationMock.__init__).parameters)
        self.assertEqual(params, ["self", "human_principals", "ai_agents"])
        with self.assertRaises(TypeError):
            AiDelegationMock([HUMAN], [AGENT], execution_enabled=True)
        self.assertEqual(
            self.fails(lambda: self.issue(authority=["QUERY", "EXECUTE"])),
            "EXECUTE_AUTHORITY_DISABLED",
        )
        self.issue()
        self.propose()
        digest = self.book.state_digest()
        self.assertEqual(self.fails(lambda: self.book.attempt_execution(AGENT, "p1")), "DELEGATED_EXECUTION_DISABLED")
        self.assertEqual(self.fails(lambda: self.book.attempt_execution(None, None)), "DELEGATED_EXECUTION_DISABLED")
        self.assertEqual(self.book.state_digest(), digest)
        self.assertEqual(self.book.view_proposal("p1")["phase"], "PROPOSED")

    def test_ai_cannot_issue_widen_reissue_or_revive(self):
        """DLG-06 DLG-23 DLG-32. An AI cannot mint, revoke, or revive a generation."""
        self.issue()
        self.assertEqual(
            self.fails(lambda: self.book.issue_grant(AGENT, "g2", AGENT, ["QUERY"], scope(), limits(), period())),
            "AI_SELF_EXPANSION_FORBIDDEN",
        )
        self.assertEqual(self.fails(lambda: self.book.revoke_grant(AGENT, "g1", "nope")), "AI_SELF_EXPANSION_FORBIDDEN")
        self.assertEqual(
            self.fails(lambda: self.book.call_tool(AGENT, "g1", "widen_grant", {}, 10)),
            "AI_SELF_EXPANSION_FORBIDDEN",
        )
        self.assertEqual(
            self.fails(lambda: self.book.call_tool(AGENT, "g1", "reissue_grant", {}, 10)),
            "AI_SELF_EXPANSION_FORBIDDEN",
        )
        self.book.revoke_grant(HUMAN, "g1", "stop")
        self.assertEqual(
            self.fails(lambda: self.book.call_tool(AGENT, "g1", "revive_grant", {}, 10)),
            "AI_SELF_EXPANSION_FORBIDDEN",
        )
        self.assertEqual(
            self.fails(
                lambda: self.book.issue_grant(
                    AGENT, "g1", AGENT, ["QUERY", "PROPOSE"], scope(), limits(), period()
                )
            ),
            "AI_SELF_EXPANSION_FORBIDDEN",
        )
        replay = self.issue()
        self.assertTrue(replay["duplicate"])
        self.assertEqual(replay["grant"]["phase"], "REVOKED")
        self.assertEqual(self.book.view_grant("g1")["generation"], 1)

    def test_ai_cannot_decide_and_strangers_are_rejected(self):
        """DLG-07 DLG-32. Decisions and grant writes stay with the human issuer."""
        self.issue()
        self.propose()
        self.assertEqual(
            self.fails(lambda: self.book.decide_proposal(AGENT, "p1", "APPROVE", 10)),
            "AI_CANNOT_DECIDE",
        )
        self.assertEqual(self.fails(lambda: self.book.call_tool(HUMAN, "g1", "query_grant", {}, 10)), "UNKNOWN_ACTOR")
        self.assertEqual(self.fails(lambda: self.book.decide_proposal(OTHER, "p1", "APPROVE", 10)), "UNKNOWN_ACTOR")
        self.assertEqual(
            self.fails(lambda: self.book.issue_grant("stranger", "g9", AGENT, ["QUERY"], scope(), limits(), period())),
            "UNKNOWN_ACTOR",
        )
        with self.assertRaises(AiDelegationError) as caught:
            AiDelegationMock(["same"], ["same"])
        self.assertEqual(caught.exception.code, "MOCK_INVARIANT")

    def test_grant_change_memo_does_not_widen_the_grant(self):
        """DLG-08. A change request is stored and the issued grant body stays put."""
        self.issue(limits=limits(per=10, cum=10, count=3))
        before = self.book.view_grant("g1")
        result = self.book.call_tool(
            AGENT,
            "g1",
            "propose_grant_change",
            {
                "proposal_id": "chg",
                "requested": {
                    "limits": limits(per=10**12, cum=10**12, count=10),
                    "authority": ["PROPOSE", "QUERY"],
                    "note": "fixture-ask",
                },
            },
            10,
        )
        self.assertEqual(result["proposal"]["phase"], "PROPOSED")
        self.assertEqual(result["proposal"]["kind"], "GRANT_CHANGE")
        self.assertFalse(result["proposal"]["effects_executed"])
        after = self.book.view_grant("g1")
        for key in ("authority", "limits", "scope", "period", "generation", "phase"):
            self.assertEqual(after[key], before[key])
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="too-big", amount=11)), "PER_ACTION_EXCEEDED")
        self.assertEqual(
            self.fails(
                lambda: self.book.call_tool(
                    AGENT,
                    "g1",
                    "propose_grant_change",
                    {"proposal_id": "nope", "requested": {"authority": ["EXECUTE"]}},
                    10,
                )
            ),
            "EXECUTE_AUTHORITY_DISABLED",
        )
        approved = self.book.decide_proposal(HUMAN, "chg", "APPROVE", 10)
        self.assertEqual(approved["proposal"]["phase"], "HUMAN_APPROVED")
        self.assertFalse(approved["proposal"]["effects_executed"])
        self.assertEqual(self.book.view_grant("g1")["limits"], before["limits"])

    def test_denylist_and_unknown_tools(self):
        """DLG-09 DLG-05 DLG-36. Transfer, refund execution, signing, issue, and pay are refused."""
        self.issue()
        cases = {
            "transfer": "TRANSFER_FORBIDDEN",
            "refund_execution": "REFUND_EXECUTION_FORBIDDEN",
            "sign": "SIGNING_FORBIDDEN",
            "issue": "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY",
            "pay": "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY",
            "mystery-tool": "TOOL_NOT_ALLOWED",
        }
        for tool, expected in cases.items():
            self.assertEqual(
                self.fails(lambda tool=tool: self.book.call_tool(AGENT, "g1", tool, {}, 10)),
                expected,
            )
        self.assertTrue(ALLOWLIST.isdisjoint(DENYLIST))

    def test_allowlist_is_disjoint_from_protocol_commands(self):
        """DLG-10 DLG-12. The mock does not call delegate or close_delegation."""
        payload = json.loads((ROOT / "reference/v0.3-rc1/protocol_contract.json").read_text())
        commands = set(payload["commands"])
        self.assertTrue(ALLOWLIST.isdisjoint(commands))
        self.assertIn("delegate", commands)
        self.assertIn("close_delegation", commands)
        self.issue()
        for command in ("delegate", "close_delegation"):
            self.assertEqual(
                self.fails(lambda command=command: self.book.call_tool(AGENT, "g1", command, {}, 10)),
                "TOOL_NOT_ALLOWED",
            )

    def test_mock_has_no_v03_import(self):
        """DLG-11 DLG-12. The mock module does not import the ticket reference."""
        path = Path(__file__).resolve().parent / "ai_delegation_mock.py"
        text = path.read_text()
        tree = ast.parse(text)
        self.assertNotIn("v0.3-rc1", text)
        self.assertNotIn("close_delegation", text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("v0.3", alias.name)
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn("v0.3", node.module or "")

    def test_scope_checks_membership_only(self):
        """DLG-13. Surface and subject ids are opaque membership tests."""
        self.issue(scope=scope(surfaces=("delegate", "surface-a"), subjects=("subj-1",)))
        noted = self.propose(surface="delegate", subject="subj-1")
        self.assertEqual(noted["proposal"]["surface"], "delegate")
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="out", surface="other-surface")), "SCOPE_VIOLATION")
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="who", subject="nope")), "SCOPE_VIOLATION")
        other = AiDelegationMock([HUMAN], [AGENT])
        other.issue_grant(
            HUMAN,
            "g-open",
            AGENT,
            ["PROPOSE"],
            {"surfaces": ["surface-a"], "subjects": []},
            limits(),
            period(),
        )
        with self.assertRaises(AiDelegationError) as caught:
            other.call_tool(
                AGENT,
                "g-open",
                "propose_action",
                {"proposal_id": "s", "surface": "surface-a", "subject": "anything", "amount": 1, "kind": "fixture-kind"},
                10,
            )
        self.assertEqual(caught.exception.code, "SCOPE_VIOLATION")
        open_subject = other.call_tool(
            AGENT,
            "g-open",
            "propose_action",
            {"proposal_id": "s", "surface": "surface-a", "amount": 1, "kind": "fixture-kind"},
            10,
        )
        self.assertEqual(open_subject["proposal"]["subject"], None)

    def test_limits_are_required_fixture_bounds(self):
        """DLG-14 DLG-34. All three caps and KRW are required. The integer bound is a fixture."""
        self.assertEqual(
            self.fails(lambda: self.issue(limits={"per_action_max": 1, "count_max": 1, "currency": "KRW"})),
            "LIMIT_REQUIRED",
        )
        self.assertEqual(self.fails(lambda: self.issue(limits={**limits(), "currency": "USD"})), "LIMIT_REQUIRED")
        self.assertEqual(self.fails(lambda: self.issue(limits={**limits(), "count_max": 0})), "INVALID_AMOUNT")
        self.assertEqual(self.fails(lambda: self.issue(limits={**limits(), "per_action_max": True})), "INVALID_AMOUNT")
        granted = self.issue(limits=limits(per=10**12, cum=10**12, count=10**12))
        self.assertEqual(granted["grant"]["limits"]["currency"], "KRW")
        self.assertEqual(granted["grant"]["limits"]["per_action_max"], 10**12)

    def test_caps_count_open_proposals_and_release_on_reject_or_withdraw(self):
        """DLG-15 DLG-16 DLG-17 DLG-18. Splits, bool amounts, and released shares."""
        self.issue(limits=limits(per=60, cum=100, count=4))
        self.propose(proposal_id="split-a", amount=60)
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="split-b", amount=60)), "CUMULATIVE_EXCEEDED")
        self.propose(proposal_id="split-b", amount=40)
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="zero", amount=0)), "INVALID_AMOUNT")
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="bool", amount=True)), "INVALID_AMOUNT")
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="bool2", amount=False)), "INVALID_AMOUNT")
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="huge", amount=10**12 + 1)), "INVALID_AMOUNT")
        self.book.decide_proposal(HUMAN, "split-a", "REJECT", 10)
        self.propose(proposal_id="after-reject", amount=60)
        self.book.call_tool(AGENT, "g1", "withdraw_proposal", {"proposal_id": "after-reject"}, 100)
        self.assertEqual(self.book.view_proposal("after-reject")["phase"], "WITHDRAWN")
        self.propose(proposal_id="after-withdraw", amount=60)
        self.book.decide_proposal(HUMAN, "after-withdraw", "APPROVE", 12)
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="still", amount=50)), "CUMULATIVE_EXCEEDED")

        fresh = AiDelegationMock([HUMAN], [AGENT])
        fresh.issue_grant(HUMAN, "g1", AGENT, ["PROPOSE"], scope(), limits(per=100, cum=1_000, count=1), period())
        fresh.call_tool(
            AGENT,
            "g1",
            "propose_action",
            {"proposal_id": "one", "surface": "surface-a", "amount": 100, "kind": "fixture-kind"},
            10,
        )
        with self.assertRaises(AiDelegationError) as caught:
            fresh.call_tool(
                AGENT,
                "g1",
                "propose_action",
                {"proposal_id": "two", "surface": "surface-a", "amount": 1, "kind": "fixture-kind"},
                10,
            )
        self.assertEqual(caught.exception.code, "COUNT_EXCEEDED")
        edge = fresh.call_tool(
            AGENT,
            "g1",
            "propose_action",
            {"proposal_id": "one", "surface": "surface-a", "amount": 100, "kind": "fixture-kind"},
            10,
        )
        self.assertTrue(edge["duplicate"])

    def test_per_action_boundary(self):
        """DLG-15 DLG-18. The per-action cap is inclusive at the fixture maximum."""
        self.issue(limits=limits(per=100, cum=100, count=2))
        self.propose(proposal_id="exact", amount=100)
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="over", amount=101)), "PER_ACTION_EXCEEDED")

    def test_period_boundaries(self):
        """DLG-19. Both endpoints are inside the period. Outside is not in force."""
        self.issue()
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="early", now=9)), "GRANT_NOT_CURRENT")
        self.propose(proposal_id="start", now=10, amount=1)
        self.propose(proposal_id="end", now=20, amount=1)
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="late", now=21)), "GRANT_EXPIRED")
        self.assertEqual(
            self.fails(lambda: self.issue(grant_id="bad-period", period={"not_before": 5, "not_after": 4})),
            "INVALID_PERIOD",
        )
        self.assertEqual(
            self.fails(lambda: self.issue(grant_id="missing-end", period={"not_before": 1})),
            "INVALID_PERIOD",
        )
        self.assertEqual(self.fails(lambda: self.book.call_tool(AGENT, "g1", "query_grant", {}, True)), "INVALID_PERIOD")
        self.book.call_tool(AGENT, "g1", "query_grant", {}, 10)
        self.book.call_tool(AGENT, "g1", "query_grant", {}, 20)

    def test_revocation_is_immediate_and_keeps_history(self):
        """DLG-20 DLG-21 DLG-22. Revocation stops use, voids pending proposals, and deletes nothing."""
        self.issue(limits=limits(per=10, cum=10, count=2))
        self.propose(proposal_id="pending", amount=4)
        self.propose(proposal_id="kept", amount=2)
        self.book.decide_proposal(HUMAN, "kept", "APPROVE", 10)
        revoked = self.book.revoke_grant(HUMAN, "g1", "stop")
        self.assertFalse(revoked["duplicate"])
        self.assertEqual(revoked["grant"]["phase"], "REVOKED")
        self.assertEqual(revoked["grant"]["revoked_at_seq"], 1)
        self.assertEqual(revoked["grant"]["reason"], "stop")
        self.assertEqual(self.book.view_proposal("pending")["phase"], "VOIDED_BY_REVOCATION")
        self.assertEqual(self.book.view_proposal("kept")["phase"], "HUMAN_APPROVED")
        self.assertFalse(self.book.view_proposal("kept")["effects_executed"])
        self.assertEqual(self.fails(lambda: self.book.call_tool(AGENT, "g1", "query_grant", {}, 10)), "GRANT_REVOKED")
        self.assertEqual(self.fails(lambda: self.book.decide_proposal(HUMAN, "pending", "APPROVE", 10)), "GRANT_REVOKED")
        again = self.book.revoke_grant(HUMAN, "g1", "other-reason")
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["grant"]["reason"], "stop")
        state = self.book.canonical_state()
        self.assertEqual({row["proposal_id"] for row in state["proposals"]}, {"pending", "kept"})
        self.assertEqual(self.book.view_grant("g1")["generation"], 1)
        nxt = self.issue(grant_id="g2")
        self.assertEqual(nxt["grant"]["generation"], 2)
        self.propose(proposal_id="next-gen", amount=10, grant_id="g2")
        self.assertEqual(self.book.view_proposal("pending")["phase"], "VOIDED_BY_REVOCATION")

    def test_next_generation_requires_revoke(self):
        """DLG-24. A second grant id is refused while the pair still has an ACTIVE generation."""
        self.issue()
        self.assertEqual(self.fails(lambda: self.issue(grant_id="g2")), "GRANT_NOT_CURRENT")
        self.assertEqual(self.fails(lambda: self.book.view_grant("g2")), "UNKNOWN_GRANT")
        self.book.revoke_grant(HUMAN, "g1", "rotate")
        nxt = self.issue(grant_id="g2")
        self.assertEqual(nxt["grant"]["generation"], 2)
        self.assertEqual(nxt["grant"]["phase"], "ACTIVE")
        self.assertEqual(self.book.view_grant("g1")["phase"], "REVOKED")

    def test_grant_idempotency(self):
        """DLG-25. The same grant binding replays. A different binding conflicts."""
        first = self.issue()
        self.assertFalse(first["duplicate"])
        second = self.issue()
        self.assertTrue(second["duplicate"])
        self.assertEqual(second["grant"]["grant_id"], "g1")
        self.assertEqual(
            self.fails(lambda: self.issue(limits=limits(per=9, cum=9, count=1))),
            "GRANT_BINDING_CONFLICT",
        )
        self.assertEqual(self.fails(lambda: self.book.view_grant("missing")), "UNKNOWN_GRANT")

    def test_proposal_idempotency(self):
        """DLG-26. The same proposal binding replays, including after revocation."""
        self.issue()
        first = self.propose(amount=4)
        self.assertFalse(first["duplicate"])
        second = self.propose(amount=4)
        self.assertTrue(second["duplicate"])
        self.assertEqual(self.fails(lambda: self.propose(amount=5)), "PROPOSAL_BINDING_CONFLICT")
        self.book.revoke_grant(HUMAN, "g1", "stop")
        replay = self.propose(amount=4)
        self.assertTrue(replay["duplicate"])
        self.assertEqual(replay["proposal"]["phase"], "VOIDED_BY_REVOCATION")

    def test_decide_rechecks_grant_and_approval_does_not_execute(self):
        """DLG-27 DLG-28. Approval is a memo. The grant is read again at decision time."""
        self.issue(limits=limits(per=50, cum=50, count=2))
        self.propose(proposal_id="p", amount=40)
        self.assertEqual(self.fails(lambda: self.book.decide_proposal(HUMAN, "p", "APPROVE", 9)), "GRANT_NOT_CURRENT")
        self.assertEqual(self.book.view_proposal("p")["phase"], "PROPOSED")
        self.assertEqual(self.fails(lambda: self.book.decide_proposal(HUMAN, "p", "APPROVE", 21)), "GRANT_EXPIRED")
        self.assertEqual(self.book.view_proposal("p")["phase"], "PROPOSED")
        decided = self.book.decide_proposal(HUMAN, "p", "APPROVE", 10)
        self.assertEqual(decided["proposal"]["phase"], "HUMAN_APPROVED")
        self.assertEqual(decided["proposal"]["decision"], "APPROVE")
        self.assertIs(decided["proposal"]["effects_executed"], False)
        self.assertIs(decided["proposal"]["issued"], False)
        self.assertIs(decided["proposal"]["paid"], False)
        replay = self.book.decide_proposal(HUMAN, "p", "APPROVE", 99)
        self.assertTrue(replay["duplicate"])
        self.assertEqual(self.fails(lambda: self.book.decide_proposal(HUMAN, "p", "REJECT", 10)), "PROPOSAL_BINDING_CONFLICT")
        self.assertEqual(self.fails(lambda: self.propose(proposal_id="extra", amount=11)), "CUMULATIVE_EXCEEDED")
        digest = self.book.state_digest()
        self.assertEqual(self.fails(lambda: self.book.attempt_execution(HUMAN, "p")), "DELEGATED_EXECUTION_DISABLED")
        self.assertEqual(self.book.state_digest(), digest)

    def test_flags_remain_false(self):
        """DLG-29 DLG-05. Grant records and approved memos do not issue or pay."""
        self.issue()
        self.propose()
        self.book.decide_proposal(HUMAN, "p1", "APPROVE", 10)
        for row in (self.book.view_grant("g1"), self.book.view_proposal("p1")):
            for flag in FALSE_FLAGS:
                self.assertIs(row[flag], False)
            self.assertEqual(row["provenance"], PROVENANCE)
            self.assertEqual(row["lifecycle_authority"], LIFECYCLE)

    def test_tool_level_follows_the_grant(self):
        """DLG-33. Query tools need QUERY. Propose tools need PROPOSE."""
        self.issue(authority=["QUERY"])
        self.assertEqual(self.fails(lambda: self.propose()), "TOOL_NOT_ALLOWED")
        digest = self.book.state_digest()
        queried = self.book.call_tool(AGENT, "g1", "query_grant", {}, 10)
        self.assertEqual(queried["grant"]["authority"], ["QUERY"])
        self.assertEqual(self.book.state_digest(), digest)
        propose_only = AiDelegationMock([HUMAN], [AGENT])
        propose_only.issue_grant(HUMAN, "g1", AGENT, ["PROPOSE"], scope(), limits(), period())
        with self.assertRaises(AiDelegationError) as caught:
            propose_only.call_tool(AGENT, "g1", "query_grant", {}, 10)
        self.assertEqual(caught.exception.code, "TOOL_NOT_ALLOWED")

    def test_digest_is_sha256_of_canonical_json(self):
        """DLG-35. The digest is a hex sha256, not a signature."""
        self.issue()
        self.propose(amount=3)
        raw = json.dumps(
            self.book.canonical_state(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        self.assertEqual(self.book.state_digest(), hashlib.sha256(raw.encode("utf-8")).hexdigest())
        self.assertEqual(len(self.book.state_digest()), 64)

    def test_every_contract_predicate_is_named_in_a_docstring(self):
        """Contract DLG ids are traceable from test docstrings."""
        contract = (ROOT / "docs/contracts/AI_DELEGATION_AUTHORITY.md").read_text()
        wanted = set(re.findall(r"DLG-\d+", contract))
        tree = ast.parse(Path(__file__).read_text())
        docs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                if doc:
                    docs.append(doc)
        cited = set(re.findall(r"DLG-\d+", "\n".join(docs)))
        self.assertEqual(sorted(wanted - cited), [])
        self.assertGreaterEqual(len(wanted), 36)
