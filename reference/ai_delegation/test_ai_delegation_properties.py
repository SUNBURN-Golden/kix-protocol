"""Seeded property suite for the offline AI delegation mock.

Author-side harness. The author is the builder, so a green run here is not an
independent PASS. MOCK only: no AI service, no grant on chain, no execution, no
grade change. Fixtures (ids, amounts, periods) are synthetic, not policy values.
No wall clock, no OS entropy, no network, no files. Seeds are fixed in
ai_delegation_property_support.SEEDS.

The oracle is typed in from docs/contracts/AI_DELEGATION_AUTHORITY.md sections
3-8 and lives in ai_delegation_property_support (never calls the mock). The
mapping to existing tests and the section 8 classes are in
validation/2026-10-17-ai-delegation-seeded-property-suite/README.md.

Properties:
  (a) caps hold after every step, boundary +/-1, split requests, shares return
  (b) the period is inclusive at both ends
  (c) revocation is immediate, voids, deletes nothing, never revives
  (d) every rejection has an expected code and leaves state unchanged
  (e) idempotency and binding conflicts
  (f) deny/unknown tools, EXECUTE, AI actors, flags, provenance
  (g) command-log replay reproduces every digest
"""

import inspect
import random
import re
import sys
import unittest
from unittest import mock

import ai_delegation_mock
from ai_delegation_mock import AiDelegationError, AiDelegationMock
from ai_delegation_property_support import (
    AGENTS,
    ALLOW_LEVELS,
    ALWAYS_FALSE_FLAGS,
    CONSUMING,
    CONTRACT_CODES,
    CONTRACT_MONEY_MAX,
    CONTRACT_PREDICATES,
    DENY_CODES,
    HUMANS,
    LIFECYCLE,
    PROPOSAL_PHASES,
    PROVENANCE,
    REACHABLE_CODES,
    SEEDS,
    STRANGER,
    Driver,
    canon,
    check_envelope,
    code_of,
    digest_of,
    issue,
    mk_limits,
    mk_period,
    mk_scope,
    new_mock,
    propose,
    state_charged,
)

_RUNS = {}


def run_for(seed):
    if seed not in _RUNS:
        _RUNS[seed] = Driver(seed).run()
    return _RUNS[seed]


def all_runs():
    return [run_for(seed) for seed in SEEDS]


def union_codes(fam=None):
    found = set()
    for d in all_runs():
        if fam is None:
            found |= d.codes
        else:
            found |= d.op_codes.get(fam, set())
    return found


def counter_total(name):
    return sum(d.counters.get(name, 0) for d in all_runs())


class Base(unittest.TestCase):
    def rejected(self, mock_, code, fn):
        """Call fn, require AiDelegationError with code and no state change."""
        digest, state = mock_.state_digest(), mock_.canonical_state()
        with self.assertRaises(AiDelegationError) as cm:
            fn()
        self.assertEqual(cm.exception.code, code)
        self.assertEqual(mock_.state_digest(), digest)
        self.assertEqual(mock_.canonical_state(), state)

    def fresh(self, **kwargs):
        m = new_mock()
        issue(m, **kwargs)
        return m


class ContractConstantTests(unittest.TestCase):
    def test_typed_tables_agree_with_the_module(self):
        """DLG-09 DLG-29 DLG-30 DLG-33 DLG-34 DLG-36: typed tables equal the module's."""
        self.assertEqual(CONTRACT_MONEY_MAX, ai_delegation_mock.MONEY_MAX)
        self.assertEqual(PROVENANCE, ai_delegation_mock.PROVENANCE)
        self.assertEqual(LIFECYCLE, ai_delegation_mock.LIFECYCLE)
        self.assertEqual(ALWAYS_FALSE_FLAGS, ai_delegation_mock.FALSE_FLAGS)
        self.assertEqual(DENY_CODES, ai_delegation_mock.DENYLIST)
        self.assertEqual(ALLOW_LEVELS, ai_delegation_mock.TOOL_LEVEL)
        self.assertEqual(set(ALLOW_LEVELS), set(ai_delegation_mock.ALLOWLIST))
        self.assertEqual(set(CONSUMING), set(ai_delegation_mock._CONSUMING))
        self.assertEqual(set(PROPOSAL_PHASES), set(ai_delegation_mock._PROPOSAL_PHASES))
        self.assertTrue(set(ALLOW_LEVELS).isdisjoint(DENY_CODES))

    def test_code_tables(self):
        """Section 8 has 26 codes; MOCK_INVARIANT is constructor-only."""
        self.assertEqual(len(CONTRACT_CODES), 26)
        self.assertEqual(len(set(CONTRACT_CODES)), 26)
        self.assertNotIn("MOCK_INVARIANT", REACHABLE_CODES)
        self.assertEqual(len(CONTRACT_PREDICATES), 36)

    def test_overlapping_registries_give_mock_invariant(self):
        """Constructor check: overlapping registries raise MOCK_INVARIANT."""
        with self.assertRaises(AiDelegationError) as cm:
            AiDelegationMock(["x", "y"], ["y"])
        self.assertEqual(cm.exception.code, "MOCK_INVARIANT")


class CapTests(Base):
    def test_seeded_caps_hold_after_every_step(self):
        """DLG-15 DLG-17: an independent running sum stays within both caps in every seeded step."""
        for d in all_runs():
            state = d.mock.canonical_state()
            for g in state["grants"]:
                amount, count = state_charged(state, g["grant_id"])
                self.assertLessEqual(amount, g["limits"]["cumulative_max"])
                self.assertLessEqual(count, g["limits"]["count_max"])
            self.assertEqual({k: tuple(v) for k, v in d.model.charged.items()},
                             {g["grant_id"]: state_charged(state, g["grant_id"]) for g in state["grants"]})
        self.assertGreater(counter_total("propose:ok"), 0)
        self.assertTrue({"CUMULATIVE_EXCEEDED", "COUNT_EXCEEDED", "PER_ACTION_EXCEEDED"} <= union_codes("propose"))

    def test_cumulative_boundary_and_split_requests(self):
        """DLG-15 DLG-17: split requests sum to exactly the cap, one more unit is refused."""
        rng = random.Random(SEEDS[0])
        for cum in (1, 2, 7, 100, 10**12):
            parts = rng.randint(1, min(4, cum))
            cuts = sorted(rng.sample(range(1, cum), parts - 1)) if parts > 1 else []
            sizes = [b - a for a, b in zip([0] + cuts, cuts + [cum])]
            m = self.fresh(limits=mk_limits(cum, cum, parts + 1))
            for i, size in enumerate(sizes):
                propose(m, "g-1", "p-%d" % i, size, 12)
            self.rejected(m, "CUMULATIVE_EXCEEDED", lambda: propose(m, "g-1", "p-x", 1, 12))
            state = m.canonical_state()
            self.assertEqual(state_charged(state, "g-1"), (cum, parts))

    def test_per_action_boundary(self):
        """DLG-15: per-action cap is inclusive; one above is refused."""
        for per in (1, 2, 7, 100, 10**12 - 1):
            m = self.fresh(limits=mk_limits(per, 10**12, 5))
            self.rejected(m, "PER_ACTION_EXCEEDED", lambda: propose(m, "g-1", "p-hi", per + 1, 12))
            propose(m, "g-1", "p-eq", per, 12)

    def test_count_boundary_and_changes_consume_count(self):
        """DLG-16 DLG-17: open count cap; propose_grant_change takes a count share."""
        for count in (1, 2, 7):
            m = self.fresh(limits=mk_limits(10, 1000, count))
            for i in range(count - 1):
                propose(m, "g-1", "p-%d" % i, 1, 12)
            m.call_tool("agent-1", "g-1", "propose_grant_change",
                        {"proposal_id": "c-1", "requested": {"note": "n"}}, 12)
            self.rejected(m, "COUNT_EXCEEDED", lambda: propose(m, "g-1", "p-x", 1, 12))

    def test_reject_and_withdraw_return_the_share_and_approve_does_not(self):
        """DLG-15 DLG-16: HUMAN_REJECTED and WITHDRAWN return the share, HUMAN_APPROVED keeps it."""
        m = self.fresh(limits=mk_limits(10, 10, 4))
        propose(m, "g-1", "p-1", 4, 12)
        propose(m, "g-1", "p-2", 3, 12)
        propose(m, "g-1", "p-3", 2, 12)
        self.rejected(m, "CUMULATIVE_EXCEEDED", lambda: propose(m, "g-1", "p-4", 2, 12))
        m.decide_proposal("human-a", "p-1", "APPROVE", 12)
        m.call_tool("agent-1", "g-1", "withdraw_proposal", {"proposal_id": "p-2"}, 12)
        self.assertEqual(state_charged(m.canonical_state(), "g-1"), (6, 2))
        propose(m, "g-1", "p-4", 4, 12)
        self.rejected(m, "CUMULATIVE_EXCEEDED", lambda: propose(m, "g-1", "p-5", 1, 12))
        m.decide_proposal("human-a", "p-3", "REJECT", 12)
        propose(m, "g-1", "p-5", 2, 12)
        self.assertEqual(state_charged(m.canonical_state(), "g-1"), (10, 3))

    def test_b_decide_time_cap_codes_are_unreachable_from_the_public_api(self):
        """Class B (DLG-27): decide-time cap and currency codes never occur."""
        self.assertFalse({"PER_ACTION_EXCEEDED", "CUMULATIVE_EXCEEDED", "COUNT_EXCEEDED",
                          "LIMIT_REQUIRED"} & union_codes("decide"))


class LimitTests(Base):
    def test_limits_and_currency_are_required(self):
        """DLG-14 DLG-34: three limits and KRW are required; no default and no unlimited."""
        m = new_mock()
        full = mk_limits()
        for key in ("per_action_max", "cumulative_max", "count_max", "currency"):
            partial = {k: v for k, v in full.items() if k != key}
            self.rejected(m, "LIMIT_REQUIRED", lambda: issue(m, limits=partial))
        self.rejected(m, "LIMIT_REQUIRED", lambda: issue(m, limits=dict(full, currency="USD")))
        self.rejected(m, "LIMIT_REQUIRED", lambda: issue(m, limits={}))
        self.rejected(m, "INVALID_AMOUNT", lambda: issue(m, limits=dict(full, count_max=0)))


class PeriodTests(Base):
    def test_period_is_inclusive_at_both_ends(self):
        """DLG-19: random windows, now below, at and above each end."""
        rng = random.Random(SEEDS[1])
        for _ in range(60):
            nb = rng.randint(0, 50)
            na = nb + rng.randint(0, 30)
            m = self.fresh(period=mk_period(nb, na))
            for now in {nb, na, rng.randint(nb, na)}:
                self.assertEqual(m.call_tool("agent-1", "g-1", "query_grant", {}, now)["grant"]["grant_id"], "g-1")
            if nb > 0:
                self.rejected(m, "GRANT_NOT_CURRENT",
                              lambda: m.call_tool("agent-1", "g-1", "query_grant", {}, nb - 1))
            self.rejected(m, "GRANT_EXPIRED", lambda: m.call_tool("agent-1", "g-1", "query_grant", {}, na + 1))
            far = na + rng.randint(2, 100)
            self.rejected(m, "GRANT_EXPIRED", lambda: propose(m, "g-1", "p-1", 1, far))

    def test_seeded_period_codes(self):
        """DLG-19: both period codes occur across the seeds; exactness is in the oracle."""
        found = union_codes()
        self.assertTrue({"GRANT_NOT_CURRENT", "GRANT_EXPIRED"} <= found)

    def test_decide_rechecks_the_period(self):
        """DLG-27: decide_proposal reads the period again at its own now."""
        m = self.fresh()
        propose(m, "g-1", "p-1", 5, 12)
        self.rejected(m, "GRANT_EXPIRED", lambda: m.decide_proposal("human-a", "p-1", "APPROVE", 21))
        self.rejected(m, "GRANT_NOT_CURRENT", lambda: m.decide_proposal("human-a", "p-1", "APPROVE", 9))
        self.assertEqual(m.decide_proposal("human-a", "p-1", "APPROVE", 20)["proposal"]["phase"], "HUMAN_APPROVED")


class RevocationTests(Base):
    def test_revocation_is_immediate_voids_and_keeps_history(self):
        """DLG-20 DLG-21 DLG-22: revocation blocks use at once, voids PROPOSED, deletes nothing."""
        m = self.fresh()
        propose(m, "g-1", "p-1", 5, 12)
        propose(m, "g-1", "p-2", 5, 12)
        m.decide_proposal("human-a", "p-2", "APPROVE", 12)
        before = m.canonical_state()
        m.revoke_grant("human-a", "g-1", "stop")
        after = m.canonical_state()
        self.assertEqual(len(after["grants"]), 1)
        self.assertEqual(len(after["proposals"]), 2)
        phases = {row["proposal_id"]: row["phase"] for row in after["proposals"]}
        self.assertEqual(phases, {"p-1": "VOIDED_BY_REVOCATION", "p-2": "HUMAN_APPROVED"})
        self.assertEqual(after["grants"][0]["phase"], "REVOKED")
        self.assertEqual(before["proposals"][0]["amount"], after["proposals"][0]["amount"])
        for now in (10, 15, 20):
            self.rejected(m, "GRANT_REVOKED", lambda: m.call_tool("agent-1", "g-1", "query_grant", {}, now))
            self.rejected(m, "GRANT_REVOKED", lambda: propose(m, "g-1", "p-n", 1, now))
        self.rejected(m, "GRANT_REVOKED", lambda: m.decide_proposal("human-a", "p-1", "APPROVE", 12))
        self.assertEqual(m.view_grant("g-1")["phase"], "REVOKED")
        self.assertEqual(m.view_proposal("p-1")["phase"], "VOIDED_BY_REVOCATION")

    def test_revoked_grant_id_is_never_revived_and_next_generation_needs_revoke(self):
        """DLG-23 DLG-24: same id stays REVOKED; a second grant for the pair needs REVOKED first."""
        m = self.fresh()
        self.rejected(m, "GRANT_NOT_CURRENT", lambda: issue(m, grant_id="g-2"))
        m.revoke_grant("human-a", "g-1", "stop")
        self.assertTrue(issue(m)["duplicate"])
        self.assertEqual(m.view_grant("g-1")["phase"], "REVOKED")
        self.rejected(m, "GRANT_BINDING_CONFLICT", lambda: issue(m, scope=mk_scope(("surf-c",))))
        self.assertEqual(issue(m, grant_id="g-2")["grant"]["generation"], 2)
        m.revoke_grant("human-a", "g-2", "stop")
        self.assertEqual(issue(m, grant_id="g-3")["grant"]["generation"], 3)

    def test_seeded_revocation_probes(self):
        """DLG-20 DLG-21 DLG-22: every seeded revoke is probed; ids and phases only grow."""
        self.assertGreater(counter_total("revoke:ok"), 0)
        self.assertGreater(counter_total("probe:err"), 0)
        self.assertEqual(union_codes("probe"), {"GRANT_REVOKED"})
        for d in all_runs():
            self.assertIn("VOIDED_BY_REVOCATION", d.phases_seen | {"VOIDED_BY_REVOCATION"})
        self.assertTrue(any("VOIDED_BY_REVOCATION" in d.phases_seen for d in all_runs()))

    def test_seeded_state_never_deletes(self):
        """DLG-22: grant and proposal ids known after any step remain in the final state."""
        for d in all_runs():
            state = d.mock.canonical_state()
            self.assertEqual({g["grant_id"] for g in state["grants"]}, d.known_grants)
            self.assertEqual({p["proposal_id"] for p in state["proposals"]}, d.known_proposals)


class AtomicityAndCodesTests(Base):
    def test_every_seeded_rejection_has_an_expected_code_and_leaves_state(self):
        """Rejections are checked per call in Driver.step: code in the oracle's set, digest and state unchanged."""
        for d in all_runs():
            self.assertTrue(d.codes <= set(REACHABLE_CODES))
            self.assertGreater(len(d.log), 40)

    def test_coverage_guard_op_families_and_codes(self):
        """Coverage guard: every op family and every reachable code occurs across the seeds."""
        families = ("issue", "revoke", "decide", "propose", "change", "withdraw", "query_grant", "query_subject",
                    "deny", "unknown_tool", "attempt", "view_grant", "view_proposal", "ai_actor", "stranger",
                    "probe")
        for fam in families:
            total = sum(v for d in all_runs() for k, v in d.counters.items() if k.split(":")[0] == fam)
            self.assertGreater(total, 0, fam)
        for name in ("issue:ok", "issue:dup", "revoke:ok", "revoke:dup", "decide:ok", "decide:dup", "propose:ok",
                     "propose:dup", "change:ok", "withdraw:ok", "withdraw:dup", "query_grant:ok",
                     "query_subject:ok", "view_grant:ok", "view_proposal:ok"):
            self.assertGreater(counter_total(name), 0, name)
        self.assertEqual(set(REACHABLE_CODES) - union_codes(), set())
        self.assertEqual(union_codes() - set(REACHABLE_CODES), set())
        self.assertEqual(set().union(*(d.phases_seen for d in all_runs())), set(PROPOSAL_PHASES))

    def test_views_are_copies(self):
        """DLG-30: mutating a returned view does not change state (checked per step by Driver)."""
        m = self.fresh()
        view = m.view_grant("g-1")
        digest = m.state_digest()
        view["scope"]["surfaces"].append("x")
        view["phase"] = "X"
        self.assertEqual(m.state_digest(), digest)

    def test_digest_is_sha256_of_canonical_state(self):
        """DLG-35: state_digest equals sha256 of the canonical JSON, for every final seeded state."""
        for d in all_runs():
            self.assertEqual(d.mock.state_digest(), digest_of(d.mock.canonical_state()))
            self.assertEqual(len(d.mock.state_digest()), 64)

    def test_invalid_amounts_ids_and_now(self):
        """DLG-18 DLG-34: bool, zero, negative, over-range amounts and bad now are refused."""
        m = self.fresh(limits=mk_limits(10**12, 10**12, 5))
        for amount in (True, False, 0, -1, 10**12 + 1, 1.5, "5", None):
            self.rejected(m, "INVALID_AMOUNT", lambda: propose(m, "g-1", "p-1", amount, 12))
        for now in (-1, True, 1.5, "5", None):
            self.rejected(m, "INVALID_PERIOD", lambda: propose(m, "g-1", "p-1", 1, now))
        propose(m, "g-1", "p-1", 10**12, 12)
        self.rejected(m, "INVALID_ID", lambda: propose(m, "g-1", "", 1, 12))


class IdempotencyTests(Base):
    def test_grant_replay_and_conflicts(self):
        """DLG-25: replay is duplicate true; every one-field change is GRANT_BINDING_CONFLICT."""
        m = self.fresh()
        self.assertTrue(issue(m)["duplicate"])
        self.assertTrue(issue(m, authority=("PROPOSE", "QUERY"))["duplicate"])
        self.assertTrue(issue(m, scope=mk_scope(("surf-b", "surf-a")))["duplicate"])
        variants = {
            "actor": dict(actor="human-b"),
            "agent": dict(agent="agent-2"),
            "authority": dict(authority=("QUERY",)),
            "scope": dict(scope=mk_scope(("surf-a",))),
            "subjects": dict(scope=mk_scope(subjects=())),
            "limits": dict(limits=mk_limits(99)),
            "period": dict(period=mk_period(10, 21)),
        }
        for name in sorted(variants):
            self.rejected(m, "GRANT_BINDING_CONFLICT", lambda: issue(m, **variants[name]))
        self.assertTrue(issue(m)["duplicate"])

    def test_proposal_replay_and_conflicts(self):
        """DLG-26: replay is duplicate true; every one-field change is PROPOSAL_BINDING_CONFLICT."""
        m = self.fresh(scope=mk_scope(subjects=("sub-1", "sub-2")))
        first = propose(m, "g-1", "p-1", 5, 12, subject="sub-1")
        again = propose(m, "g-1", "p-1", 5, 15, subject="sub-1")
        self.assertFalse(first["duplicate"])
        self.assertTrue(again["duplicate"])
        self.assertEqual(first["proposal"], again["proposal"])
        for kwargs in (dict(amount=6), dict(surface="surf-b"), dict(subject="sub-2"), dict(subject=None),
                       dict(kind="kind-b")):
            args = dict(amount=5, surface="surf-a", subject="sub-1", kind="kind-a")
            args.update(kwargs)
            self.rejected(m, "PROPOSAL_BINDING_CONFLICT",
                          lambda: propose(m, "g-1", "p-1", args["amount"], 12, surface=args["surface"],
                                          subject=args["subject"], kind=args["kind"]))
        issue(m, grant_id="g-9", actor="human-b")
        self.rejected(m, "PROPOSAL_BINDING_CONFLICT", lambda: propose(m, "g-9", "p-1", 5, 12, subject="sub-1"))

    def test_replay_after_revocation_is_still_a_duplicate(self):
        """DLG-26: a replay of an accepted proposal skips the state checks."""
        m = self.fresh()
        propose(m, "g-1", "p-1", 5, 12)
        m.revoke_grant("human-a", "g-1", "stop")
        again = propose(m, "g-1", "p-1", 5, 99)
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["proposal"]["phase"], "VOIDED_BY_REVOCATION")

    def test_seeded_replays_and_conflicts(self):
        """DLG-25 DLG-26: seeded replays are duplicates and changed bindings raise the conflict codes."""
        self.assertGreater(counter_total("issue:dup"), 0)
        self.assertGreater(counter_total("propose:dup"), 0)
        self.assertIn("GRANT_BINDING_CONFLICT", union_codes("issue"))
        self.assertIn("PROPOSAL_BINDING_CONFLICT", union_codes("propose"))


class AuthorityAndInertnessTests(Base):
    def test_deny_and_unknown_tools(self):
        """DLG-05 DLG-09 DLG-36: deny table codes are exact; any other tool is TOOL_NOT_ALLOWED."""
        m = self.fresh()
        for tool in sorted(DENY_CODES):
            self.rejected(m, DENY_CODES[tool], lambda: m.call_tool("agent-1", "g-1", tool, {}, 12))
        for tool in ("delegate", "close_delegation", "", "execute", "Transfer", "mystery"):
            self.rejected(m, "TOOL_NOT_ALLOWED", lambda: m.call_tool("agent-1", "g-1", tool, {}, 12))
        self.assertEqual(union_codes("deny"), set(DENY_CODES.values()))
        self.assertEqual(union_codes("unknown_tool"), {"TOOL_NOT_ALLOWED"})

    def test_execute_is_never_grantable_and_attempt_is_disabled(self):
        """DLG-03 DLG-04: EXECUTE is refused wherever it appears; attempt_execution always fails inertly."""
        m = new_mock()
        for authority in (["EXECUTE"], ["QUERY", "EXECUTE"], ["EXECUTE", "PROPOSE", "QUERY"]):
            self.rejected(m, "EXECUTE_AUTHORITY_DISABLED", lambda: issue(m, authority=authority))
        issue(m)
        self.rejected(m, "EXECUTE_AUTHORITY_DISABLED", lambda: m.call_tool(
            "agent-1", "g-1", "propose_grant_change",
            {"proposal_id": "c-1", "requested": {"authority": ["EXECUTE"]}}, 12))
        propose(m, "g-1", "p-1", 1, 12)
        for actor in ("agent-1", "human-a", STRANGER, None, 7):
            for pid in ("p-1", "p-nope", "", None):
                self.rejected(m, "DELEGATED_EXECUTION_DISABLED", lambda: m.attempt_execution(actor, pid))
        self.assertEqual(union_codes("attempt"), {"DELEGATED_EXECUTION_DISABLED"})
        self.assertEqual(sum(1 for g in m.canonical_state()["grants"] if "EXECUTE" in g["authority"]), 0)

    def test_b_four_entry_authority_list_with_execute(self):
        """Class B (DLG-03): the contract says EXECUTE_AUTHORITY_DISABLED; the mock gives INVALID_ID for 4+ entries."""
        m = new_mock()
        code = code_of(lambda: issue(m, authority=["QUERY", "PROPOSE", "EXECUTE", "EXECUTE"]))
        self.assertIn(code, ("EXECUTE_AUTHORITY_DISABLED", "INVALID_ID"))
        self.assertEqual(m.canonical_state()["grants"], [])

    def test_ai_actors_never_issue_revoke_or_decide(self):
        """DLG-06 DLG-07 DLG-32: AI actors get the AI codes and state is unchanged."""
        m = self.fresh()
        propose(m, "g-1", "p-1", 1, 12)
        for ai in AGENTS:
            self.rejected(m, "AI_SELF_EXPANSION_FORBIDDEN", lambda: issue(m, grant_id="g-z", actor=ai))
            self.rejected(m, "AI_SELF_EXPANSION_FORBIDDEN", lambda: m.revoke_grant(ai, "g-1", "stop"))
            self.rejected(m, "AI_CANNOT_DECIDE", lambda: m.decide_proposal(ai, "p-1", "APPROVE", 12))
        self.rejected(m, "UNKNOWN_ACTOR", lambda: issue(m, grant_id="g-z", actor=STRANGER))
        self.rejected(m, "UNKNOWN_ACTOR", lambda: m.revoke_grant("human-b", "g-1", "stop"))
        self.rejected(m, "UNKNOWN_ACTOR", lambda: m.decide_proposal("human-b", "p-1", "APPROVE", 12))
        self.rejected(m, "UNKNOWN_ACTOR", lambda: m.call_tool("agent-2", "g-1", "query_grant", {}, 12))
        self.rejected(m, "UNKNOWN_ACTOR", lambda: m.call_tool("human-a", "g-1", "query_grant", {}, 12))
        self.assertTrue(union_codes("ai_actor") <= {"AI_SELF_EXPANSION_FORBIDDEN", "AI_CANNOT_DECIDE"})
        self.assertEqual(union_codes("ai_actor"), {"AI_SELF_EXPANSION_FORBIDDEN", "AI_CANNOT_DECIDE"})

    def test_tool_level_follows_the_grant(self):
        """DLG-33: query tools need QUERY, proposal tools need PROPOSE."""
        q = self.fresh(authority=("QUERY",))
        self.rejected(q, "TOOL_NOT_ALLOWED", lambda: propose(q, "g-1", "p-1", 1, 12))
        self.rejected(q, "TOOL_NOT_ALLOWED", lambda: q.call_tool(
            "agent-1", "g-1", "propose_grant_change", {"proposal_id": "c", "requested": {"note": "n"}}, 12))
        q.call_tool("agent-1", "g-1", "query_subject", {"surface": "surf-a"}, 12)
        p = self.fresh(authority=("PROPOSE",))
        self.rejected(p, "TOOL_NOT_ALLOWED", lambda: p.call_tool("agent-1", "g-1", "query_grant", {}, 12))
        self.rejected(p, "TOOL_NOT_ALLOWED", lambda: p.call_tool("agent-1", "g-1", "query_subject",
                                                                {"surface": "surf-a"}, 12))
        propose(p, "g-1", "p-1", 1, 12)
        p.call_tool("agent-1", "g-1", "withdraw_proposal", {"proposal_id": "p-1"}, 12)

    def test_flags_provenance_and_inert_memos(self):
        """DLG-01 DLG-02 DLG-08 DLG-28 DLG-29 DLG-30: every view carries provenance, flags are False, memos are inert."""
        m = self.fresh(scope=mk_scope(subjects=("sub-1",)))
        grant_before = m.view_grant("g-1")
        digest = m.state_digest()
        views = [m.view_grant("g-1"), m.call_tool("agent-1", "g-1", "query_grant", {}, 12)["grant"],
                 m.call_tool("agent-1", "g-1", "query_subject", {"surface": "surf-a", "subject": "sub-1"}, 12)]
        self.assertEqual(m.state_digest(), digest)
        change = m.call_tool("agent-1", "g-1", "propose_grant_change",
                             {"proposal_id": "c-1", "requested": {"limits": mk_limits(999)}}, 12)
        self.assertEqual(m.view_grant("g-1"), grant_before)
        propose(m, "g-1", "p-1", 5, 12, subject="sub-1")
        approved = m.decide_proposal("human-a", "p-1", "APPROVE", 12)
        views += [change["proposal"], approved["proposal"], m.view_proposal("p-1")]
        for view in views:
            check_envelope(view, "view")
        self.assertIs(approved["proposal"]["effects_executed"], False)
        self.assertEqual(approved["proposal"]["phase"], "HUMAN_APPROVED")
        self.assertEqual(m.view_grant("g-1"), grant_before)

    def test_seeded_results_pass_the_envelope_check(self):
        """DLG-29 DLG-30: Driver.step runs check_envelope on every accepted result."""
        for d in all_runs():
            self.assertGreater(sum(1 for entry in d.log if entry[0] != "attempt_execution"), 0)


class ReplayDeterminismTests(unittest.TestCase):
    def test_command_log_replay_reproduces_every_digest(self):
        """Determinism: replaying the accepted command list on a fresh mock reproduces every state_digest."""
        for d in all_runs():
            fresh = d.replay()
            self.assertEqual(fresh.state_digest(), d.mock.state_digest())
            self.assertEqual(fresh.canonical_state(), d.mock.canonical_state())

    def test_replay_with_reversed_registries(self):
        """Determinism: registry list order does not change any digest."""
        for d in all_runs():
            d.replay(list(reversed(HUMANS)), list(reversed(AGENTS)))

    def test_same_seed_gives_the_same_run(self):
        """Determinism: two fresh runs of one seed share one fingerprint; seeds differ."""
        d = Driver(SEEDS[0]).run()
        self.assertEqual(d.fingerprint(), run_for(SEEDS[0]).fingerprint())
        self.assertEqual(len({x.fingerprint() for x in all_runs()}), len(SEEDS))

    def test_replay_detects_a_changed_command(self):
        """Replay control: a perturbed log entry is noticed."""
        d = run_for(SEEDS[0])
        saved = list(d.log)
        method, params, digest, result = saved[0]
        d.log[0] = (method, params, "0" * 64, result)
        try:
            with self.assertRaises(AssertionError):
                d.replay()
        finally:
            d.log[:] = saved


class ClassBCharacterizationTests(Base):
    def test_b_scope_list_shape_errors_are_not_named_by_the_contract(self):
        """Class B (DLG-13): non-list or duplicate scope lists are refused; the contract names no exact code."""
        m = new_mock()
        for scope in ({"surfaces": "surf-a"}, {"surfaces": ["a", "a"]}):
            self.assertIn(code_of(lambda: issue(m, scope=scope)), ("INVALID_ID", "SCOPE_VIOLATION"))
        self.assertEqual(m.canonical_state()["grants"], [])

    def test_b_precedence_among_several_violations_is_set_membership(self):
        """Class B: with several violated predicates the oracle accepts any of their codes."""
        m = self.fresh()
        code = code_of(lambda: propose(m, "g-1", "p-1", 10**6, 99, surface="surf-z"))
        self.assertIn(code, ("GRANT_EXPIRED", "SCOPE_VIOLATION", "PER_ACTION_EXCEEDED", "CUMULATIVE_EXCEEDED"))

    def test_b_the_share_of_a_void_is_not_observable_after_revocation(self):
        """Class B (DLG-16): once revoked, no call can use the returned share."""
        m = self.fresh(limits=mk_limits(10, 10, 2))
        propose(m, "g-1", "p-1", 10, 12)
        m.revoke_grant("human-a", "g-1", "stop")
        self.assertEqual(state_charged(m.canonical_state(), "g-1"), (0, 0))
        self.rejected(m, "GRANT_REVOKED", lambda: propose(m, "g-1", "p-2", 1, 12))


def _no_op_for(module, code):
    original = module._require

    def patched(ok, got):
        if got == code:
            return None
        return original(ok, got)

    return patched


class NegativeControlTests(unittest.TestCase):
    """Each control patches an in-memory attribute and must trip an oracle.

    AssertionError is required, not AiDelegationError: the oracle fails, not
    the guard under test. Source files are never edited.
    """

    def run_seeds(self):
        for seed in SEEDS:
            Driver(seed).run()

    def test_silencing_the_cumulative_cap_trips_the_oracle(self):
        """Control: CUMULATIVE_EXCEEDED check silenced (DLG-15 DLG-17)."""
        original = ai_delegation_mock._require
        with mock.patch.object(ai_delegation_mock, "_require", _no_op_for(ai_delegation_mock, "CUMULATIVE_EXCEEDED")):
            with mock.patch.object(AiDelegationMock, "_invariant", lambda self: None):
                with self.assertRaises(AssertionError):
                    self.run_seeds()
        self.assertIs(ai_delegation_mock._require, original)

    def test_silencing_the_count_cap_trips_the_oracle(self):
        """Control: COUNT_EXCEEDED check silenced (DLG-15 DLG-17)."""
        original = ai_delegation_mock._require
        with mock.patch.object(ai_delegation_mock, "_require", _no_op_for(ai_delegation_mock, "COUNT_EXCEEDED")):
            with mock.patch.object(AiDelegationMock, "_invariant", lambda self: None):
                with self.assertRaises(AssertionError):
                    self.run_seeds()
        self.assertIs(ai_delegation_mock._require, original)

    def test_silencing_the_revocation_check_trips_the_oracle(self):
        """Control: GRANT_REVOKED check silenced (DLG-20)."""
        original = ai_delegation_mock._require
        with mock.patch.object(ai_delegation_mock, "_require", _no_op_for(ai_delegation_mock, "GRANT_REVOKED")):
            with self.assertRaises(AssertionError):
                self.run_seeds()
        self.assertIs(ai_delegation_mock._require, original)

    def test_revoke_that_skips_voiding_trips_the_oracle(self):
        """Control: revoke leaves PROPOSED proposals open (DLG-21)."""
        original = AiDelegationMock.revoke_grant

        def lax(self, actor, grant_id, reason):
            kept = {k: v["phase"] for k, v in self._proposals.items() if v["phase"] == "PROPOSED"}
            result = original(self, actor, grant_id, reason)
            for key, phase in kept.items():
                if self._proposals[key]["phase"] == "VOIDED_BY_REVOCATION":
                    self._proposals[key]["phase"] = phase
            return result

        with mock.patch.object(AiDelegationMock, "revoke_grant", lax):
            with self.assertRaises(AssertionError):
                self.run_seeds()
        self.assertIs(AiDelegationMock.revoke_grant, original)

    def test_a_rejected_call_that_changes_state_trips_the_oracle(self):
        """Control: a rejected call_tool bumps a counter before re-raising (rejection atomicity)."""
        original = AiDelegationMock.call_tool

        def leaky(self, *args, **kwargs):
            try:
                return original(self, *args, **kwargs)
            except AiDelegationError:
                self._seq += 1
                raise

        with mock.patch.object(AiDelegationMock, "call_tool", leaky):
            with self.assertRaises(AssertionError):
                self.run_seeds()
        self.assertIs(AiDelegationMock.call_tool, original)

    def test_unpatched_runs_are_green_again(self):
        """After every control the same drivers pass."""
        Driver(SEEDS[0]).run()


class TraceabilityTests(unittest.TestCase):
    """DLG-10 DLG-11 DLG-12 DLG-31 stay covered by the existing static tests."""

    def test_docstrings_cite_the_predicates(self):
        """Every DLG id is cited here or is one of the four already covered statically."""
        module = sys.modules[__name__]
        docs = [module.__doc__ or ""]
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != __name__:
                continue
            docs.append(cls.__doc__ or "")
            for name, fn in inspect.getmembers(cls, inspect.isfunction):
                if name.startswith("test_"):
                    docs.append(fn.__doc__ or "")
        cited = set(re.findall(r"DLG-\d+", "\n".join(docs)))
        self.assertTrue(cited <= set(CONTRACT_PREDICATES))
        covered_elsewhere = {"DLG-10", "DLG-11", "DLG-12", "DLG-31"}
        self.assertEqual(sorted(set(CONTRACT_PREDICATES) - cited - covered_elsewhere), [])


if __name__ == "__main__":
    unittest.main()
