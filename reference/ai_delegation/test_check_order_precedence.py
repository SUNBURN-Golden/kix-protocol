"""Source-informed §7 order evidence; synthetic fixtures, no execution.

CHECKS comes from AI_DELEGATION_AUTHORITY.md §§7–8. All 28 check pairs have
buildable cases. The matrix accounts separately for unreachable variants and
variants that return the same code. §3 malformed-input precedence remains class B.
"""

from itertools import combinations, product
import unittest

from ai_delegation_property_support import (
    AGENTS, DENY_CODES, HUMANS, STRANGER, code_of, issue, mk_limits,
    mk_period, mk_scope, new_mock, propose,
)

CHECKS = {
    1: {"unregistered": "UNKNOWN_ACTOR", "other_agent": "UNKNOWN_ACTOR"},
    2: {**{"deny:" + tool: code for tool, code in DENY_CODES.items()},
        "unknown_tool": "TOOL_NOT_ALLOWED"},
    3: {"unknown_grant": "UNKNOWN_GRANT", "revoked": "GRANT_REVOKED"},
    4: {"before": "GRANT_NOT_CURRENT", "after": "GRANT_EXPIRED"},
    5: {"no_propose": "TOOL_NOT_ALLOWED"},
    6: {"surface": "SCOPE_VIOLATION", "subject": "SCOPE_VIOLATION"},
    7: {"per_action": "PER_ACTION_EXCEEDED"},
    8: {"cumulative": "CUMULATIVE_EXCEEDED", "count": "COUNT_EXCEEDED"},
}


def cells():
    for i, j in combinations(CHECKS, 2):
        for vi, vj in product(CHECKS[i], CHECKS[j]):
            yield i, j, vi, vj


def category(variants):
    # Without the grant, binding/scope/limits etc. cannot be evaluated. Do not
    # pretend a request violates exactly two predicates of a nonexistent grant.
    if "unknown_grant" in variants:
        return "unbuildable"
    # Immutable QUERY-only grants cannot accumulate proposals through public APIs.
    if {"no_propose", "count"} <= variants:
        return "unbuildable"
    if {"unknown_tool", "no_propose"} <= variants:
        return "same_code"
    return "contract"


def build(variants=()):
    """Grant config, prior proposals, revocation, then the request; public APIs only.

    A revoked+count case retains HUMAN_APPROVED shares (DLG-15); pending
    proposals alone would be voided and would not violate the count check.
    A non-revoked non-ACTIVE generation is not constructible (DLG-24).
    """
    variants = set(variants)
    mock = new_mock()
    issue(mock, authority=("QUERY",) if "no_propose" in variants else ("QUERY", "PROPOSE"),
          scope=mk_scope(subjects=("sub-1",)), period=mk_period(10, 20),
          limits=mk_limits(per=50 if "per_action" in variants else 100,
                           cum=50 if "cumulative" in variants else 500, count=3))
    if "count" in variants:
        for n in range(3):
            pid = "prior-%d" % n
            propose(mock, "g-1", pid, 1, 15, subject="sub-1")
            if "revoked" in variants:
                mock.decide_proposal(HUMANS[0], pid, "APPROVE", 15)
    if "revoked" in variants:
        mock.revoke_grant(HUMANS[0], "g-1", "stop")
    call = dict(actor=STRANGER if "unregistered" in variants else
                AGENTS[1] if "other_agent" in variants else AGENTS[0],
                grant_id="missing-grant" if "unknown_grant" in variants else "g-1",
                tool="no_such_tool" if "unknown_tool" in variants else "propose_action",
                args=dict(proposal_id="candidate", surface="surf-z" if "surface" in variants else "surf-a",
                          subject="sub-z" if "subject" in variants else "sub-1", amount=80, kind="kind-a"),
                now=5 if "before" in variants else 25 if "after" in variants else 15)
    for variant in variants:
        if variant.startswith("deny:"):
            call["tool"] = variant.split(":", 1)[1]
    return mock, call


def violated_checks(mock, call):
    """Independent predicates over public state, before any rejection masks them.

    For an invalid tool name, later predicates describe the otherwise unchanged
    intended propose_action payload. This tests the shared call_tool entry gate.
    """
    state = mock.canonical_state()
    grant = next(g for g in state["grants"] if g["grant_id"] == call["grant_id"])
    args, limits = call["args"], grant["limits"]
    consuming = [p for p in state["proposals"] if p["grant_id"] == grant["grant_id"]
                 and p["phase"] in ("PROPOSED", "HUMAN_APPROVED")]
    current = [g for g in state["grants"] if g["issuer"] == grant["issuer"]
               and g["agent_id"] == grant["agent_id"] and g["phase"] == "ACTIVE"]
    predicates = {
        1: call["actor"] in AGENTS and call["actor"] == grant["agent_id"],
        2: call["tool"] == "propose_action",  # all fixtures use this intent
        3: grant["phase"] != "REVOKED" and grant in current,
        4: grant["period"]["not_before"] <= call["now"] <= grant["period"]["not_after"],
        5: "PROPOSE" in grant["authority"],
        6: args["surface"] in grant["scope"]["surfaces"] and
           args["subject"] in grant["scope"]["subjects"],
        7: args["amount"] <= limits["per_action_max"],
        8: sum(p["amount"] or 0 for p in consuming) + args["amount"] <= limits["cumulative_max"]
           and len(consuming) + 1 <= limits["count_max"],
    }
    return {i for i, satisfied in predicates.items() if not satisfied}


class CheckOrderPrecedenceTests(unittest.TestCase):
    def rejected(self, mock, call, expected):
        before, digest = mock.canonical_state(), mock.state_digest()
        self.assertEqual(code_of(lambda: mock.call_tool(**call)), expected)
        self.assertEqual(mock.canonical_state(), before)
        self.assertEqual(mock.state_digest(), digest)

    def test_valid_baseline_and_each_isolated_variant(self):
        """DLG-19 DLG-20 DLG-33: controls establish individually violated predicates."""
        mock, call = build()
        self.assertEqual(violated_checks(mock, call), set())
        self.assertFalse(mock.call_tool(**call)["duplicate"])
        for check, variants in CHECKS.items():
            for variant, expected in variants.items():
                with self.subTest(check=check, variant=variant):
                    mock, call = build({variant})
                    if variant != "unknown_grant":
                        self.assertEqual(violated_checks(mock, call), {check})
                    self.rejected(mock, call, expected)

    def test_contract_pairs_reject_with_the_lower_check(self):
        """§7 items 1–8 (DLG-19, DLG-20, DLG-33): check every distinguishable, buildable cell."""
        seen = set()
        for i, j, vi, vj in cells():
            if category({vi, vj}) != "contract":
                continue
            with self.subTest(i=i, j=j, vi=vi, vj=vj):
                mock, call = build({vi, vj})
                self.assertEqual(violated_checks(mock, call), {i, j})
                self.rejected(mock, call, CHECKS[i][vi])
                seen.add((i, j))
        self.assertEqual(seen, set(combinations(range(1, 9), 2)))

    def test_actor_binding_precedes_tool_lists(self):
        """§7 items 1–2 (DLG-33): a registered agent cannot use another agent's grant."""
        for tool_variant in ("deny:transfer", "unknown_tool"):
            with self.subTest(tool=tool_variant):
                mock, call = build({"other_agent", tool_variant})
                self.rejected(mock, call, "UNKNOWN_ACTOR")

    def test_b_unknown_tool_and_missing_level_share_a_code(self):
        """Same-code observation, not proof of precedence; denied variants distinguish 2<5 (DLG-33)."""
        mock, call = build({"unknown_tool", "no_propose"})
        self.assertEqual(violated_checks(mock, call), {2, 5})
        self.assertEqual(CHECKS[2]["unknown_tool"], CHECKS[5]["no_propose"])
        self.rejected(mock, call, "TOOL_NOT_ALLOWED")

    def test_b_unknown_grant_cannot_evaluate_actor_binding(self):
        """Class B: no grant means no agent_id to compare; not an isolated 1+3 pair."""
        mock, call = build({"other_agent", "unknown_grant"})
        self.assertNotIn(call["grant_id"], {g["grant_id"] for g in mock.canonical_state()["grants"]})
        self.rejected(mock, call, "UNKNOWN_GRANT")

    def test_tool_lists_precede_missing_grant_rejection(self):
        """§7 items 2–3 (DLG-33): looking up the binding preserves missing-grant precedence."""
        for tool_variant, expected in CHECKS[2].items():
            with self.subTest(tool=tool_variant):
                mock, call = build({"unknown_grant", tool_variant})
                self.rejected(mock, call, expected)

    def test_decide_duplicate_precedes_recheck(self):
        """§7, DLG-19 DLG-20 DLG-27: same decision survives period failure and revocation."""
        for decision in ("APPROVE", "REJECT"):
            with self.subTest(decision=decision):
                mock, call = build()
                mock.call_tool(**call)
                first = mock.decide_proposal(HUMANS[0], "candidate", decision, 15)
                mock.revoke_grant(HUMANS[0], "g-1", "stop")
                for now in (5, 25):
                    before, digest = mock.canonical_state(), mock.state_digest()
                    again = mock.decide_proposal(HUMANS[0], "candidate", decision, now)
                    self.assertTrue(again["duplicate"])
                    self.assertEqual(again["proposal"], first["proposal"])
                    self.assertEqual(mock.canonical_state(), before)
                    self.assertEqual(mock.state_digest(), digest)

    def test_decide_voided_proposal_precedes_period_recheck(self):
        """§§7–8 (DLG-20, DLG-27): a voided proposal returns GRANT_REVOKED outside the period."""
        mock, call = build()
        mock.call_tool(**call)
        mock.revoke_grant(HUMANS[0], "g-1", "stop")
        self.assertEqual(mock.view_proposal("candidate")["phase"], "VOIDED_BY_REVOCATION")
        before, digest = mock.canonical_state(), mock.state_digest()
        for now in (5, 25):
            with self.subTest(now=now):
                self.assertEqual(code_of(lambda: mock.decide_proposal(
                    HUMANS[0], "candidate", "APPROVE", now)), "GRANT_REVOKED")
                self.assertEqual(mock.canonical_state(), before)
                self.assertEqual(mock.state_digest(), digest)

    def test_matrix_size_is_recorded(self):
        """Count variant cells separately from the 28 check pairs."""
        counts = {kind: 0 for kind in ("contract", "same_code", "unbuildable")}
        for _, _, vi, vj in cells():
            counts[category({vi, vj})] += 1
        # Filled from the initial actual enumeration; see validation record.
        self.assertEqual(len(set((i, j) for i, j, _, _ in cells())), EXPECTED_PAIRS)
        self.assertEqual(counts, EXPECTED_COUNTS)
        self.assertEqual(sum(counts.values()), EXPECTED_CASES)


EXPECTED_PAIRS = 28
EXPECTED_COUNTS = {"contract": 148, "same_code": 1, "unbuildable": 20}
EXPECTED_CASES = 169

if __name__ == "__main__":
    unittest.main()
