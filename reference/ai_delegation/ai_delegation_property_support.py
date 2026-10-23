"""Support for the seeded AI delegation property suite. Not a test module.

Author-side harness, builder-authored, not an independent PASS. MOCK only: no AI
service, no grant on chain, no execution. Fixtures (ids, amounts, periods) are
synthetic, not policy values. No wall clock, no OS entropy, no network, no
files. Seeds are fixed in SEEDS and every random choice comes from
random.Random(seed) over lists in a fixed order.

The oracle (Model) is typed in from docs/contracts/AI_DELEGATION_AUTHORITY.md
sections 3-8. Nothing is imported from the mock except the objects under test
and their exception type. The constants and tables below are re-typed, not
imported; test_ai_delegation_properties.ContractConstantTests compares them with
the module so a drift shows.

Where the contract orders checks (section 7, propose_action) the oracle follows
that order. Where it does not, the oracle accepts the set of codes of every
violated predicate (class B in the validation record).
"""

import copy
import hashlib
import json
import random

from ai_delegation_mock import AiDelegationError, AiDelegationMock

SEEDS = (1, 2, 3, 5, 8, 13, 21, 34)
CONTRACT_MONEY_MAX = 10**12
PROVENANCE = "MOCK_AI_DELEGATION_ONLY"
LIFECYCLE = "IN_MEMORY_FSM"

ALWAYS_FALSE_FLAGS = (
    "execution_enabled",
    "funds_executed",
    "issued",
    "paid",
    "signed",
    "transferred",
    "refund_executed",
    "chain_grant_confirmed",
    "revocation_cut_confirmed",
    "durable",
    "legal_authority",
)

# Section 5: allow list with the level each tool needs, and the deny table.
ALLOW_LEVELS = {
    "query_grant": "QUERY",
    "query_subject": "QUERY",
    "propose_action": "PROPOSE",
    "withdraw_proposal": "PROPOSE",
    "propose_grant_change": "PROPOSE",
}
DENY_CODES = {
    "transfer": "TRANSFER_FORBIDDEN",
    "refund_execution": "REFUND_EXECUTION_FORBIDDEN",
    "sign": "SIGNING_FORBIDDEN",
    "issue": "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY",
    "pay": "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY",
    "widen_grant": "AI_SELF_EXPANSION_FORBIDDEN",
    "reissue_grant": "AI_SELF_EXPANSION_FORBIDDEN",
    "revive_grant": "AI_SELF_EXPANSION_FORBIDDEN",
}

# Section 7: PROPOSED and HUMAN_APPROVED hold a share of the caps.
CONSUMING = ("PROPOSED", "HUMAN_APPROVED")
PROPOSAL_PHASES = ("PROPOSED", "HUMAN_APPROVED", "HUMAN_REJECTED", "WITHDRAWN", "VOIDED_BY_REVOCATION")

# Section 8 (26 codes). MOCK_INVARIANT comes only from the constructor
# (overlapping registries) and has a directed check.
CONTRACT_CODES = (
    "AI_SELF_EXPANSION_FORBIDDEN",
    "AI_CANNOT_DECIDE",
    "UNKNOWN_ACTOR",
    "UNKNOWN_GRANT",
    "UNKNOWN_PROPOSAL",
    "TOOL_NOT_ALLOWED",
    "TRANSFER_FORBIDDEN",
    "REFUND_EXECUTION_FORBIDDEN",
    "SIGNING_FORBIDDEN",
    "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY",
    "EXECUTE_AUTHORITY_DISABLED",
    "DELEGATED_EXECUTION_DISABLED",
    "GRANT_NOT_CURRENT",
    "GRANT_REVOKED",
    "GRANT_EXPIRED",
    "SCOPE_VIOLATION",
    "LIMIT_REQUIRED",
    "PER_ACTION_EXCEEDED",
    "CUMULATIVE_EXCEEDED",
    "COUNT_EXCEEDED",
    "INVALID_ID",
    "INVALID_AMOUNT",
    "INVALID_PERIOD",
    "GRANT_BINDING_CONFLICT",
    "PROPOSAL_BINDING_CONFLICT",
    "MOCK_INVARIANT",
)
REACHABLE_CODES = tuple(code for code in CONTRACT_CODES if code != "MOCK_INVARIANT")

# Section 6 ids.
CONTRACT_PREDICATES = tuple("DLG-%02d" % n for n in range(1, 37))

HUMANS = ("human-a", "human-b")
AGENTS = ("agent-1", "agent-2", "agent-3")
STRANGER = "stranger-x"
SURFACES = ("surf-a", "surf-b", "surf-c", "surf-d")
OUTSIDE_SURFACE = "surf-z"
SUBJECTS = ("sub-1", "sub-2", "sub-3")
OUTSIDE_SUBJECT = "sub-z"
KINDS = ("kind-a", "kind-b")
REASONS = ("stop", "rotate", "audit")
LIMIT_KEYS = ("per_action_max", "cumulative_max", "count_max")

STEPS = 300


def fail(message):
    raise AssertionError(message)


def canon(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest_of(state):
    return hashlib.sha256(canon(state).encode("utf-8")).hexdigest()


def new_mock(humans=HUMANS, agents=AGENTS):
    return AiDelegationMock(list(humans), list(agents))


# ---------------------------------------------------------------- fixtures


def mk_limits(per=100, cum=1_000, count=5):
    return {"per_action_max": per, "cumulative_max": cum, "count_max": count, "currency": "KRW"}


def mk_scope(surfaces=("surf-a", "surf-b"), subjects=None):
    body = {"surfaces": list(surfaces)}
    if subjects is not None:
        body["subjects"] = list(subjects)
    return body


def mk_period(start=10, end=20):
    return {"not_before": start, "not_after": end}


def issue(mock, grant_id="g-1", actor="human-a", agent="agent-1", authority=("QUERY", "PROPOSE"),
          scope=None, limits=None, period=None):
    return mock.issue_grant(actor, grant_id, agent, list(authority),
                            mk_scope() if scope is None else scope,
                            mk_limits() if limits is None else limits,
                            mk_period() if period is None else period)


def propose(mock, grant_id, proposal_id, amount, now, surface="surf-a", subject=None, kind="kind-a",
            actor="agent-1"):
    args = {"proposal_id": proposal_id, "surface": surface, "amount": amount, "kind": kind}
    if subject is not None:
        args["subject"] = subject
    return mock.call_tool(actor, grant_id, "propose_action", args, now)


def code_of(fn):
    """Return the AiDelegationError code, or None when the call succeeds."""
    try:
        fn()
    except AiDelegationError as error:
        return error.code
    return None


def state_charged(state, grant_id):
    """Independent running sum from a canonical_state dict: (amount, count)."""
    amount = count = 0
    for row in state["proposals"]:
        if row["grant_id"] == grant_id and row["phase"] in CONSUMING:
            amount += row["amount"] or 0
            count += 1
    return amount, count


# ------------------------------------------------------------------- oracle


def ident_ok(value):
    return type(value) is str and 0 < len(value) <= 100 and value.strip() == value


def money_ok(value):
    return type(value) is int and 0 < value <= CONTRACT_MONEY_MAX


def logical_ok(value):
    return type(value) is int and value >= 0


def parse_authority(value):
    """Section 3. Returns (codes, normalized). A list with EXECUTE gives
    EXECUTE_AUTHORITY_DISABLED; with four or more entries the contract is
    silent on the shape error, so INVALID_ID is accepted too (class B)."""
    if type(value) is not list or not value or any(type(item) is not str for item in value):
        return {"INVALID_ID"}, None
    if "EXECUTE" in value:
        return ({"EXECUTE_AUTHORITY_DISABLED", "INVALID_ID"} if len(value) > 3
                else {"EXECUTE_AUTHORITY_DISABLED"}), None
    if len(value) > 3 or len(set(value)) != len(value) or not set(value) <= {"QUERY", "PROPOSE"}:
        return {"INVALID_ID"}, None
    return set(), sorted(value)


def _id_list(value, empty_ok):
    # Not a list or duplicate entries: section 8 does not say SCOPE_VIOLATION
    # or INVALID_ID, so both are accepted (class B).
    if type(value) is not list:
        return {"INVALID_ID", "SCOPE_VIOLATION"}, None
    if not empty_ok and not value:
        return {"SCOPE_VIOLATION"}, None
    if any(not ident_ok(item) for item in value):
        return {"INVALID_ID"}, None
    if len(set(value)) != len(value):
        return {"INVALID_ID", "SCOPE_VIOLATION"}, None
    return set(), sorted(value)


def parse_scope(value):
    if type(value) is not dict or "surfaces" not in value or not set(value) <= {"surfaces", "subjects"}:
        return {"SCOPE_VIOLATION"}, None
    codes, surfaces = _id_list(value["surfaces"], False)
    subjects = None
    if "subjects" in value:
        more, subjects = _id_list(value["subjects"], True)
        if more:
            codes = codes | more
    if codes:
        return codes, None
    return set(), {"surfaces": surfaces, "subjects": subjects}


def parse_limits(value):
    if type(value) is not dict or set(value) != {"per_action_max", "cumulative_max", "count_max", "currency"}:
        return {"LIMIT_REQUIRED"}, None
    codes = set()
    if value["currency"] != "KRW":
        codes.add("LIMIT_REQUIRED")
    if not all(money_ok(value[key]) for key in LIMIT_KEYS):
        codes.add("INVALID_AMOUNT")
    if codes:
        return codes, None
    return set(), {key: value[key] for key in LIMIT_KEYS} | {"currency": "KRW"}


def parse_period(value):
    if type(value) is not dict or set(value) != {"not_before", "not_after"}:
        return {"INVALID_PERIOD"}, None
    start, end = value["not_before"], value["not_after"]
    if not (logical_ok(start) and logical_ok(end) and start <= end):
        return {"INVALID_PERIOD"}, None
    return set(), {"not_before": start, "not_after": end}


def parse_request(value):
    """Section 5: the requested memo of propose_grant_change."""
    if type(value) is not dict or not value or not set(value) <= {"authority", "scope", "limits", "period", "note"}:
        return {"INVALID_ID"}, None
    codes, memo = set(), {}
    for key, parse in (("authority", parse_authority), ("scope", parse_scope),
                       ("limits", parse_limits), ("period", parse_period)):
        if key in value:
            more, norm = parse(value[key])
            codes |= more
            memo[key] = norm
    if "note" in value:
        if ident_ok(value["note"]):
            memo["note"] = value["note"]
        else:
            codes.add("INVALID_ID")
    return (codes, None) if codes else (set(), memo)


def envelope():
    body = {"provenance": PROVENANCE, "lifecycle_authority": LIFECYCLE}
    body.update({flag: False for flag in ALWAYS_FALSE_FLAGS})
    return body


def err(codes):
    return ("err", frozenset(codes))


class Model:
    """Contract model: grants, proposals and the revoke counter, with running
    cap shares kept incrementally (added on accept, returned on reject,
    withdraw and void)."""

    def __init__(self, humans, agents):
        self.humans = frozenset(humans)
        self.agents = frozenset(agents)
        self.grants = {}
        self.proposals = {}
        self.charged = {}
        self.seq = 0

    # --- views and state
    def stored_grant(self, g):
        return {
            "grant_id": g["grant_id"], "generation": g["generation"], "issuer": g["issuer"],
            "agent_id": g["agent_id"], "authority": list(g["authority"]),
            "scope": copy.deepcopy(g["scope"]), "limits": dict(g["limits"]), "period": dict(g["period"]),
            "phase": g["phase"], "revoked_at_seq": g["revoked_at_seq"], "reason": g["reason"],
        }

    def stored_proposal(self, pr):
        return {
            "proposal_id": pr["proposal_id"], "grant_id": pr["grant_id"], "generation": pr["generation"],
            "tool": pr["tool"], "phase": pr["phase"], "surface": pr["surface"], "subject": pr["subject"],
            "amount": pr["amount"], "kind": pr["kind"], "memo": copy.deepcopy(pr["memo"]),
            "decision": pr["decision"], "effects_executed": False,
        }

    def grant_view(self, g):
        body = envelope()
        body.update(self.stored_grant(g))
        return body

    def proposal_view(self, pr):
        body = envelope()
        body.update(self.stored_proposal(pr))
        return body

    def expected_state(self):
        return {
            "grants": [self.stored_grant(self.grants[key]) for key in sorted(self.grants)],
            "proposals": [self.stored_proposal(self.proposals[key]) for key in sorted(self.proposals)],
            "revoke_seq": self.seq,
        }

    # --- helpers
    def human_codes(self, actor, ai_code):
        if type(actor) is not str:
            return {"UNKNOWN_ACTOR"}
        if actor in self.agents:
            return {ai_code}
        if actor not in self.humans:
            return {"UNKNOWN_ACTOR"}
        return set()

    def active_id(self, issuer, agent):
        for g in self.grants.values():
            if g["issuer"] == issuer and g["agent_id"] == agent and g["phase"] == "ACTIVE":
                return g["grant_id"]
        return None

    def state_codes(self, g, now, level=None, surface=None, subject=None, amount=None, add_count=0,
                    scope=False, caps=False):
        """Section 7 steps 3-8 in order; returns the codes of the first
        stage with a violation. Inputs that are not well formed are skipped."""
        if g["phase"] == "REVOKED":
            return {"GRANT_REVOKED"}
        if logical_ok(now):
            if now < g["period"]["not_before"]:
                return {"GRANT_NOT_CURRENT"}
            if now > g["period"]["not_after"]:
                return {"GRANT_EXPIRED"}
        if level is not None and level not in g["authority"]:
            return {"TOOL_NOT_ALLOWED"}
        if scope:
            if surface is not None and surface not in g["scope"]["surfaces"]:
                return {"SCOPE_VIOLATION"}
            subjects = g["scope"]["subjects"]
            if subjects is not None and subject is not None and subject not in subjects:
                return {"SCOPE_VIOLATION"}
        if caps:
            limits = g["limits"]
            if amount is not None and amount > limits["per_action_max"]:
                return {"PER_ACTION_EXCEEDED"}
            held_amount, held_count = self.charged[g["grant_id"]]
            codes = set()
            if amount is not None and held_amount + amount > limits["cumulative_max"]:
                codes.add("CUMULATIVE_EXCEEDED")
            if held_count + add_count > limits["count_max"]:
                codes.add("COUNT_EXCEEDED")
            return codes
        return set()

    def release(self, pr):
        share = self.charged[pr["grant_id"]]
        share[0] -= pr["amount"] or 0
        share[1] -= 1

    # --- prediction (mutates only on an accepted call)
    def predict(self, method, p):
        return getattr(self, "predict_" + method)(p)

    def predict_issue_grant(self, p):
        actor, gid, agent = p["actor"], p["grant_id"], p["agent_id"]
        codes = self.human_codes(actor, "AI_SELF_EXPANSION_FORBIDDEN")
        human_ok = not codes
        if not ident_ok(gid):
            codes.add("INVALID_ID")
        agent_ok = False
        if not ident_ok(agent):
            codes.add("INVALID_ID")
        elif agent not in self.agents:
            codes.add("UNKNOWN_ACTOR")
        else:
            agent_ok = True
        norms = {}
        for key, parse in (("authority", parse_authority), ("scope", parse_scope),
                           ("limits", parse_limits), ("period", parse_period)):
            more, norms[key] = parse(p[key])
            codes |= more
        if codes:
            if human_ok and agent_ok and ident_ok(gid) and gid not in self.grants and self.active_id(actor, agent):
                codes.add("GRANT_NOT_CURRENT")
            return err(codes)
        binding = canon({"grant_id": gid, "issuer": actor, "agent_id": agent, **norms})
        current = self.grants.get(gid)
        if current is not None:
            if current["binding"] != binding:
                return err({"GRANT_BINDING_CONFLICT"})
            return ("dup", {"duplicate": True, "grant": self.grant_view(current)})
        if self.active_id(actor, agent) is not None:
            return err({"GRANT_NOT_CURRENT"})
        generations = [g["generation"] for g in self.grants.values()
                       if g["issuer"] == actor and g["agent_id"] == agent]
        row = {"binding": binding, "grant_id": gid, "generation": 1 + max(generations) if generations else 1,
               "issuer": actor, "agent_id": agent, "phase": "ACTIVE", "revoked_at_seq": None, "reason": None,
               **norms}
        self.grants[gid] = row
        self.charged[gid] = [0, 0]
        return ("ok", {"duplicate": False, "grant": self.grant_view(row)})

    def predict_revoke_grant(self, p):
        actor, gid, reason = p["actor"], p["grant_id"], p["reason"]
        codes = self.human_codes(actor, "AI_SELF_EXPANSION_FORBIDDEN")
        human_ok = not codes
        if not ident_ok(gid):
            codes.add("INVALID_ID")
        if not ident_ok(reason):
            codes.add("INVALID_ID")
        g = None
        if ident_ok(gid):
            g = self.grants.get(gid)
            if g is None:
                codes.add("UNKNOWN_GRANT")
            elif human_ok and g["issuer"] != actor:
                codes.add("UNKNOWN_ACTOR")
        if codes:
            return err(codes)
        if g["phase"] == "REVOKED":
            return ("dup", {"duplicate": True, "grant": self.grant_view(g)})
        self.seq += 1
        g["phase"], g["revoked_at_seq"], g["reason"] = "REVOKED", self.seq, reason
        for pr in self.proposals.values():
            if pr["grant_id"] == gid and pr["phase"] == "PROPOSED":
                pr["phase"] = "VOIDED_BY_REVOCATION"
                self.release(pr)
        return ("ok", {"duplicate": False, "grant": self.grant_view(g)})

    def predict_decide_proposal(self, p):
        actor, pid, decision, now = p["actor"], p["proposal_id"], p["decision"], p["now"]
        codes = self.human_codes(actor, "AI_CANNOT_DECIDE")
        human_ok = not codes
        if not ident_ok(pid):
            codes.add("INVALID_ID")
        if not (type(decision) is str and decision in ("APPROVE", "REJECT")):
            codes.add("INVALID_ID")
        if not logical_ok(now):
            codes.add("INVALID_PERIOD")
        pr = None
        if ident_ok(pid):
            pr = self.proposals.get(pid)
            if pr is None:
                codes.add("UNKNOWN_PROPOSAL")
            elif human_ok and self.grants[pr["grant_id"]]["issuer"] != actor:
                codes.add("UNKNOWN_ACTOR")
        if codes:
            return err(codes)
        phase = pr["phase"]
        if (phase, decision) in (("HUMAN_APPROVED", "APPROVE"), ("HUMAN_REJECTED", "REJECT")):
            return ("dup", {"duplicate": True, "proposal": self.proposal_view(pr)})
        if phase == "VOIDED_BY_REVOCATION":
            return err({"GRANT_REVOKED"})
        if phase != "PROPOSED":
            return err({"PROPOSAL_BINDING_CONFLICT"})
        g = self.grants[pr["grant_id"]]
        # Section 7: currency, revocation, period and the three caps are read
        # again. The caps cannot be violated here (class B, see the record).
        codes = self.state_codes(g, now)
        if codes:
            return err(codes)
        pr["phase"] = "HUMAN_APPROVED" if decision == "APPROVE" else "HUMAN_REJECTED"
        pr["decision"] = decision
        if decision == "REJECT":
            self.release(pr)
        return ("ok", {"duplicate": False, "proposal": self.proposal_view(pr)})

    def predict_attempt_execution(self, p):
        return err({"DELEGATED_EXECUTION_DISABLED"})

    def predict_view_grant(self, p):
        if not ident_ok(p["grant_id"]):
            return err({"INVALID_ID"})
        g = self.grants.get(p["grant_id"])
        return err({"UNKNOWN_GRANT"}) if g is None else ("ok", self.grant_view(g))

    def predict_view_proposal(self, p):
        if not ident_ok(p["proposal_id"]):
            return err({"INVALID_ID"})
        pr = self.proposals.get(p["proposal_id"])
        return err({"UNKNOWN_PROPOSAL"}) if pr is None else ("ok", self.proposal_view(pr))

    def predict_call_tool(self, p):
        actor, gid, tool, args, now = p["actor"], p["grant_id"], p["tool"], p["args"], p["now"]
        codes = set()
        if not (type(actor) is str and actor in self.agents):
            codes.add("UNKNOWN_ACTOR")
        if not ident_ok(gid):
            codes.add("INVALID_ID")
        if type(tool) is not str:
            codes.add("INVALID_ID")
        if codes:
            return err(codes)
        if tool in DENY_CODES:
            return err({DENY_CODES[tool]})
        if tool not in ALLOW_LEVELS:
            return err({"TOOL_NOT_ALLOWED"})
        if not logical_ok(now):
            codes.add("INVALID_PERIOD")
        if type(args) is not dict:
            codes.add("INVALID_ID")
        g = self.grants.get(gid)
        if g is None:
            codes.add("UNKNOWN_GRANT")
        elif g["agent_id"] != actor:
            codes.add("UNKNOWN_ACTOR")
        if codes:
            return err(codes)
        return getattr(self, "tool_" + tool)(g, args, now)

    def tool_query_grant(self, g, args, now):
        codes = {"INVALID_ID"} if args else set()
        codes |= self.state_codes(g, now, "QUERY")
        if codes:
            return err(codes)
        return ("ok", {"duplicate": False, "grant": self.grant_view(g)})

    def tool_query_subject(self, g, args, now):
        codes = set()
        if not (set(args) <= {"surface", "subject"} and "surface" in args):
            codes.add("INVALID_ID")
        surface = args.get("surface")
        subject = args.get("subject")
        if "surface" in args and not ident_ok(surface):
            codes.add("INVALID_ID")
            surface = None
        if "subject" in args and not ident_ok(subject):
            codes.add("INVALID_ID")
            subject = None
        codes |= self.state_codes(g, now, "QUERY", surface=surface, subject=subject, scope=True)
        if codes:
            return err(codes)
        body = envelope()
        body.update({"duplicate": False, "match": {"surface": surface, "subject": subject, "in_scope": True}})
        return ("ok", body)

    def tool_propose_action(self, g, args, now):
        codes = set()
        if not (set(args) <= {"proposal_id", "surface", "subject", "amount", "kind"}
                and {"proposal_id", "surface", "amount", "kind"} <= set(args)):
            codes.add("INVALID_ID")
        pid, surface, subject, amount, kind = (args.get(key) for key in
                                               ("proposal_id", "surface", "subject", "amount", "kind"))
        for key, value in (("proposal_id", pid), ("surface", surface), ("subject", subject), ("kind", kind)):
            if key in args and not ident_ok(value):
                codes.add("INVALID_ID")
                if key == "surface":
                    surface = None
                if key == "subject":
                    subject = None
        if "amount" in args and not money_ok(amount):
            codes.add("INVALID_AMOUNT")
            amount = None
        elif "amount" not in args:
            amount = None
        existing = self.proposals.get(pid) if ident_ok(pid) else None
        if not codes and existing is not None:
            binding = canon({"proposal_id": pid, "grant_id": g["grant_id"], "tool": "propose_action",
                             "surface": surface, "subject": subject, "amount": amount, "kind": kind, "memo": None})
            if existing["binding"] == binding:
                return ("dup", {"duplicate": True, "proposal": self.proposal_view(existing)})
            codes.add("PROPOSAL_BINDING_CONFLICT")
        codes |= self.state_codes(g, now, "PROPOSE", surface=surface, subject=subject, amount=amount,
                                  add_count=1, scope=True, caps=True)
        if codes:
            return err(codes)
        binding = canon({"proposal_id": pid, "grant_id": g["grant_id"], "tool": "propose_action",
                         "surface": surface, "subject": subject, "amount": amount, "kind": kind, "memo": None})
        return self.admit(g, pid, "propose_action", surface, subject, amount, kind, None, binding)

    def tool_propose_grant_change(self, g, args, now):
        codes = set()
        if set(args) != {"proposal_id", "requested"}:
            codes.add("INVALID_ID")
        pid = args.get("proposal_id")
        if "proposal_id" in args and not ident_ok(pid):
            codes.add("INVALID_ID")
        memo = None
        if "requested" in args:
            more, memo = parse_request(args["requested"])
            codes |= more
        existing = self.proposals.get(pid) if ident_ok(pid) else None
        binding = None
        if not codes:
            binding = canon({"proposal_id": pid, "grant_id": g["grant_id"], "tool": "propose_grant_change",
                             "surface": None, "subject": None, "amount": None, "kind": "GRANT_CHANGE",
                             "memo": memo})
            if existing is not None:
                if existing["binding"] == binding:
                    return ("dup", {"duplicate": True, "proposal": self.proposal_view(existing)})
                codes.add("PROPOSAL_BINDING_CONFLICT")
        codes |= self.state_codes(g, now, "PROPOSE", add_count=1, caps=True)
        if codes:
            return err(codes)
        return self.admit(g, pid, "propose_grant_change", None, None, None, "GRANT_CHANGE", memo, binding)

    def admit(self, g, pid, tool, surface, subject, amount, kind, memo, binding):
        row = {"binding": binding, "proposal_id": pid, "grant_id": g["grant_id"], "generation": g["generation"],
               "tool": tool, "phase": "PROPOSED", "surface": surface, "subject": subject, "amount": amount,
               "kind": kind, "memo": memo, "decision": None}
        self.proposals[pid] = row
        share = self.charged[g["grant_id"]]
        share[0] += amount or 0
        share[1] += 1
        return ("ok", {"duplicate": False, "proposal": self.proposal_view(row)})

    def tool_withdraw_proposal(self, g, args, now):
        codes = set()
        if g["phase"] == "REVOKED":
            codes.add("GRANT_REVOKED")
        if "PROPOSE" not in g["authority"]:
            codes.add("TOOL_NOT_ALLOWED")
        if set(args) != {"proposal_id"}:
            codes.add("INVALID_ID")
        pid = args.get("proposal_id")
        pr = None
        if "proposal_id" in args:
            if not ident_ok(pid):
                codes.add("INVALID_ID")
            else:
                pr = self.proposals.get(pid)
                if pr is None:
                    codes.add("UNKNOWN_PROPOSAL")
                elif pr["grant_id"] != g["grant_id"]:
                    codes.add("PROPOSAL_BINDING_CONFLICT")
                elif pr["phase"] == "VOIDED_BY_REVOCATION":
                    codes.add("GRANT_REVOKED")
                elif pr["phase"] not in ("PROPOSED", "WITHDRAWN"):
                    codes.add("PROPOSAL_BINDING_CONFLICT")
        if codes:
            return err(codes)
        if pr["phase"] == "WITHDRAWN":
            return ("dup", {"duplicate": True, "proposal": self.proposal_view(pr)})
        pr["phase"] = "WITHDRAWN"
        self.release(pr)
        return ("ok", {"duplicate": False, "proposal": self.proposal_view(pr)})


# ------------------------------------------------------------ state auditing


def check_envelope(body, where):
    if body.get("provenance") != PROVENANCE or body.get("lifecycle_authority") != LIFECYCLE:
        fail("%s lacks provenance or lifecycle_authority" % where)
    for flag in ALWAYS_FALSE_FLAGS:
        if body.get(flag) is not False:
            fail("%s: flag %s is not False" % (where, flag))
    if "effects_executed" in body and body["effects_executed"] is not False:
        fail("%s: effects_executed is not False" % where)


def check_result_envelopes(result, where):
    if "provenance" in result:
        check_envelope(result, where)
    for key in ("grant", "proposal"):
        if key in result:
            check_envelope(result[key], where + "." + key)


def audit_state(state):
    """Contract invariants read from a canonical_state dict alone. Returns
    {grant_id: (amount, count)} summed independently of the model."""
    grants = {row["grant_id"]: row for row in state["grants"]}
    sums = {key: [0, 0] for key in grants}
    for row in state["proposals"]:
        if row["grant_id"] not in grants:
            fail("proposal %s names an unknown grant" % row["proposal_id"])
        if row["phase"] not in PROPOSAL_PHASES or row["effects_executed"] is not False:
            fail("proposal %s has phase %s or ran an effect" % (row["proposal_id"], row["phase"]))
        if row["phase"] in CONSUMING:
            sums[row["grant_id"]][0] += row["amount"] or 0
            sums[row["grant_id"]][1] += 1
    active, generations = set(), {}
    for key, row in grants.items():
        if sums[key][0] > row["limits"]["cumulative_max"]:
            fail("cumulative cap broken on %s: %d > %d" % (key, sums[key][0], row["limits"]["cumulative_max"]))
        if sums[key][1] > row["limits"]["count_max"]:
            fail("count cap broken on %s: %d > %d" % (key, sums[key][1], row["limits"]["count_max"]))
        if "EXECUTE" in row["authority"] or not set(row["authority"]) <= {"QUERY", "PROPOSE"}:
            fail("grant %s carries an unexpected authority" % key)
        pair = (row["issuer"], row["agent_id"])
        generations.setdefault(pair, []).append(row["generation"])
        if row["phase"] == "ACTIVE":
            if pair in active:
                fail("two ACTIVE grants for %s" % (pair,))
            active.add(pair)
    for pair, gens in generations.items():
        if sorted(gens) != list(range(1, len(gens) + 1)):
            fail("generations of %s are %s" % (pair, sorted(gens)))
    return {key: tuple(value) for key, value in sums.items()}


_TERMINAL = ("HUMAN_APPROVED", "HUMAN_REJECTED", "WITHDRAWN", "VOIDED_BY_REVOCATION")


def scribble(value):
    """Mutate a returned object in place; the mock must hold its own copy."""
    if isinstance(value, dict):
        for key in list(value):
            scribble(value[key])
            value[key] = "scribbled"
    elif isinstance(value, list):
        for item in value:
            scribble(item)
        value.clear()


# -------------------------------------------------------------------- driver


class Driver:
    """Seeded interleaving of every public operation against the mock and the
    contract model. Each step carries at most one deliberate defect."""

    def __init__(self, seed):
        self.seed = seed
        self.rng = random.Random(seed)
        self.mock = new_mock()
        self.model = Model(HUMANS, AGENTS)
        self.counters = {}
        self.codes = set()
        self.op_codes = {}
        self.phases_seen = set()
        self.log = []
        self.digests = [self.mock.state_digest()]
        self.issued = {}
        self.proposed = {}
        self.next_g = 0
        self.next_p = 0
        self.next_probe = 0
        self.known_grants = set()
        self.known_proposals = set()
        self.grant_memory = {}
        self.proposal_phase = {}

    # --- bookkeeping
    def bump(self, name):
        self.counters[name] = self.counters.get(name, 0) + 1

    def run(self, steps=STEPS):
        ops = (
            ("issue", 9), ("issue_replay", 3), ("issue_conflict", 3), ("revoke", 4), ("revoke_replay", 2),
            ("decide", 9), ("decide_replay", 3), ("propose", 24), ("propose_replay", 5),
            ("propose_conflict", 4), ("change", 6), ("withdraw", 6), ("query_grant", 3), ("query_subject", 4),
            ("deny", 3), ("unknown_tool", 2), ("attempt", 2), ("view", 4), ("ai_actor", 5), ("stranger", 4),
        )
        names = [name for name, weight in ops for _ in range(weight)]
        for _ in range(steps):
            getattr(self, "do_" + self.rng.choice(names))()
        return self

    def step(self, fam, method, params):
        mock = self.mock
        before_digest = mock.state_digest()
        before_state = mock.canonical_state()
        verdict = self.model.predict(method, copy.deepcopy(params))
        try:
            result = getattr(mock, method)(**copy.deepcopy(params))
        except AiDelegationError as exc:
            code = exc.code
            if verdict[0] != "err":
                fail("%s raised %s but the contract says %s is accepted" % (method, code, verdict[0]))
            if code not in REACHABLE_CODES:
                fail("%s raised %s, which is not a reachable section 8 code" % (method, code))
            if code not in verdict[1]:
                fail("%s raised %s, expected one of %s" % (method, code, sorted(verdict[1])))
            if mock.state_digest() != before_digest or mock.canonical_state() != before_state:
                fail("rejected %s (%s) changed state_digest or canonical_state" % (method, code))
            self.codes.add(code)
            self.op_codes.setdefault(fam, set()).add(code)
            self.bump(fam + ":err")
            return ("err", code)
        except Exception as exc:
            fail("%s raised %s, not AiDelegationError" % (method, type(exc).__name__))
        if verdict[0] == "err":
            fail("%s accepted but the contract says %s" % (method, "/".join(sorted(verdict[1]))))
        if result != verdict[1]:
            fail("%s result differs from the contract model: %s != %s" % (method, canon(result), canon(verdict[1])))
        check_result_envelopes(result, method)
        state = mock.canonical_state()
        digest = mock.state_digest()
        if state != self.model.expected_state():
            fail("canonical_state after %s differs from the contract model" % method)
        if digest != digest_of(state):
            fail("state_digest after %s is not sha256 of the canonical JSON" % method)
        read_only = method.startswith("view_") or (
            method == "call_tool" and params["tool"] in ("query_grant", "query_subject"))
        if (read_only or verdict[0] == "dup") and digest != before_digest:
            fail("%s (%s) changed state_digest" % (method, "read-only" if read_only else "duplicate"))
        self.audit(state)
        self.log.append((method, copy.deepcopy(params), digest, canon(result)))
        self.digests.append(digest)
        scribble(result)
        if mock.state_digest() != digest:
            fail("mutating a result of %s changed the state_digest" % method)
        self.bump(fam + ":" + verdict[0])
        return (verdict[0], result)

    def audit(self, state):
        sums = audit_state(state)
        for key, share in self.model.charged.items():
            if tuple(share) != sums[key]:
                fail("running share of %s is %s but the state sums to %s" % (key, tuple(share), sums[key]))
        ids = {row["grant_id"] for row in state["grants"]}
        if not self.known_grants <= ids:
            fail("a grant id disappeared")
        self.known_grants = ids
        pids = {row["proposal_id"] for row in state["proposals"]}
        if not self.known_proposals <= pids:
            fail("a proposal id disappeared")
        self.known_proposals = pids
        for row in state["grants"]:
            key = row["grant_id"]
            if key in self.grant_memory:
                old = self.grant_memory[key]
                if old["phase"] == "REVOKED" and row != old:
                    fail("revoked grant %s changed or was revived" % key)
                for field in ("generation", "issuer", "agent_id", "authority", "scope", "limits", "period"):
                    if row[field] != old[field]:
                        fail("grant %s changed its %s" % (key, field))
            self.grant_memory[key] = row
        for row in state["proposals"]:
            key, phase = row["proposal_id"], row["phase"]
            self.phases_seen.add(phase)
            old = self.proposal_phase.get(key)
            if old in _TERMINAL and phase != old:
                fail("proposal %s left %s for %s" % (key, old, phase))
            self.proposal_phase[key] = phase

    # --- random helpers
    def pick(self, items):
        return copy.deepcopy(self.rng.choice(list(items)))

    def chance(self, p):
        return self.rng.random() < p

    def pick_grant(self, active_bias=0.8):
        ids = list(self.model.grants)
        if not ids:
            return None
        active = [key for key in ids if self.model.grants[key]["phase"] == "ACTIVE"]
        return self.rng.choice(active if active and self.chance(active_bias) else ids)

    def now_for(self, g):
        nb, na = g["period"]["not_before"], g["period"]["not_after"]
        roll = self.rng.random()
        if roll < 0.55:
            return self.rng.randint(nb, na)
        if roll < 0.9:
            return max(0, self.rng.choice([nb - 1, nb, nb + 1, na - 1, na, na + 1]))
        return self.rng.randint(0, na + 10)

    def fresh_grant_id(self):
        self.next_g += 1
        return "g-%d" % self.next_g

    def fresh_proposal_id(self):
        self.next_p += 1
        return "p-%d" % self.next_p

    def rand_scope(self):
        r = self.rng
        body = {"surfaces": r.sample(SURFACES, r.randint(1, 3))}
        roll = r.random()
        if roll < 0.5:
            body["subjects"] = r.sample(SUBJECTS, r.randint(0, 3))
        return body

    def rand_limits(self):
        r = self.rng
        per = r.choice([1, 2, 5, 10, 25, 60, 10**12])
        return mk_limits(per, r.choice([3, 10, 30, 100, 200]), r.choice([1, 2, 3, 5]))

    def rand_period(self):
        start = self.rng.randint(0, 15)
        return mk_period(start, start + self.rng.randint(0, 25))

    def rand_authority(self):
        return self.pick([["QUERY", "PROPOSE"], ["PROPOSE", "QUERY"], ["PROPOSE"], ["PROPOSE"], ["QUERY"]])

    def fresh_issue(self):
        r = self.rng
        free = [(h, a) for h in HUMANS for a in AGENTS if self.model.active_id(h, a) is None]
        actor, agent = r.choice(free) if free and self.chance(0.85) else (r.choice(HUMANS), r.choice(AGENTS))
        return {"actor": actor, "grant_id": self.fresh_grant_id(), "agent_id": agent,
                "authority": self.rand_authority(), "scope": self.rand_scope(),
                "limits": self.rand_limits(), "period": self.rand_period()}

    # --- defects: one wrong field per step
    def defect_issue(self, p):
        r = self.rng
        field = r.choice(["actor", "grant_id", "agent_id", "authority", "scope", "limits", "period"])
        bad = {
            "actor": [None, 7, STRANGER, "agent-1", "", "human-a "],
            "grant_id": [None, 5, "", " g", "g ", "x" * 101],
            "agent_id": [None, "", "agent-unknown", "human-a", " agent-1"],
            "authority": [None, "QUERY", [], ["EXECUTE"], ["QUERY", "EXECUTE"], ["PROPOSE", "QUERY", "EXECUTE"],
                          ["QUERY", "PROPOSE", "EXECUTE", "EXECUTE"], ["TRANSFER"], [1]],
            "scope": [None, [], {}, {"surfaces": []}, {"surfaces": ["surf-a"], "extra": ["x"]},
                      {"surfaces": [""]}, {"subjects": ["sub-1"]}, {"surfaces": ["surf-a"], "subjects": [" "]},
                      {"surfaces": "surf-a"}],
            "limits": [None, {}, {"per_action_max": 1, "cumulative_max": 2, "currency": "KRW"},
                       dict(mk_limits(), currency="USD"), dict(mk_limits(), currency=None),
                       dict(mk_limits(), per_action_max=0), dict(mk_limits(), per_action_max=True),
                       dict(mk_limits(), cumulative_max=-1), dict(mk_limits(), cumulative_max=10**12 + 1),
                       dict(mk_limits(), count_max=1.5), dict(mk_limits(), count_max="3")],
            "period": [None, {}, {"not_before": 1}, {"not_before": 5, "not_after": 4},
                       {"not_before": -1, "not_after": 4}, {"not_before": True, "not_after": 4},
                       {"not_before": 1.0, "not_after": 4}, {"not_before": 1, "not_after": 4, "extra": 1}],
        }
        p[field] = self.pick(bad[field])
        return p

    def bad_now(self):
        return self.pick([-1, True, False, 1.5, "5", None])

    def bad_id(self):
        return self.pick([None, 5, "", " x", "x ", "y" * 101])

    # --- operations
    def do_issue(self):
        p = self.fresh_issue()
        if self.chance(0.22):
            p = self.defect_issue(p)
        kind, _ = self.step("issue", "issue_grant", p)
        if kind == "ok":
            self.issued[p["grant_id"]] = copy.deepcopy(p)

    def do_issue_replay(self):
        if not self.issued:
            return self.do_issue()
        p = copy.deepcopy(self.issued[self.rng.choice(list(self.issued))])
        self.step("issue", "issue_grant", p)

    def do_issue_conflict(self):
        if not self.issued:
            return self.do_issue()
        p = copy.deepcopy(self.issued[self.rng.choice(list(self.issued))])
        field = self.rng.choice(["actor", "agent_id", "authority", "scope", "limits", "period"])
        if field == "actor":
            p["actor"] = [h for h in HUMANS if h != p["actor"]][0]
        elif field == "agent_id":
            p["agent_id"] = [a for a in AGENTS if a != p["agent_id"]][0]
        elif field == "authority":
            p["authority"] = ["QUERY"] if p["authority"] != ["QUERY"] else ["PROPOSE"]
        elif field == "scope":
            p["scope"]["surfaces"] = list(p["scope"]["surfaces"]) + [OUTSIDE_SURFACE]
        elif field == "limits":
            key = self.rng.choice(list(LIMIT_KEYS))
            p["limits"][key] = p["limits"][key] - 1 if p["limits"][key] > 1 else 2
        else:
            p["period"]["not_after"] += 1
        self.step("issue", "issue_grant", p)

    def do_revoke(self):
        key = self.pick_grant(0.9)
        if key is None:
            return self.do_issue()
        g = self.model.grants[key]
        actor = g["issuer"] if self.chance(0.85) else self.pick(list(HUMANS) + [STRANGER])
        p = {"actor": actor, "grant_id": key, "reason": self.pick(REASONS)}
        if self.chance(0.12):
            field = self.rng.choice(["actor", "grant_id", "reason"])
            p[field] = self.pick({"actor": [None, 9, STRANGER, "agent-2"],
                                  "grant_id": [None, "", "g-nope"], "reason": [None, "", " r", 5]}[field])
        kind, _ = self.step("revoke", "revoke_grant", p)
        if kind == "ok":
            self.probe_revoked(key)

    def do_revoke_replay(self):
        revoked = [key for key, g in self.model.grants.items() if g["phase"] == "REVOKED"]
        if not revoked:
            return self.do_revoke()
        key = self.rng.choice(revoked)
        self.step("revoke", "revoke_grant", {"actor": self.model.grants[key]["issuer"], "grant_id": key,
                                             "reason": self.pick(REASONS)})

    def probe_revoked(self, key):
        """DLG-20/21: right after a revoke every use of that generation fails."""
        g = self.model.grants[key]
        mid = (g["period"]["not_before"] + g["period"]["not_after"]) // 2
        for now in (g["period"]["not_before"], mid, g["period"]["not_after"]):
            self.next_probe += 1
            self.step("probe", "call_tool", {"actor": g["agent_id"], "grant_id": key, "tool": "query_grant",
                                             "args": {}, "now": now})
            self.step("probe", "call_tool", {
                "actor": g["agent_id"], "grant_id": key, "tool": "propose_action",
                "args": {"proposal_id": "probe-%d" % self.next_probe, "surface": g["scope"]["surfaces"][0],
                         "amount": 1, "kind": "kind-a"}, "now": now})
        for pid in sorted(self.model.proposals):
            if self.model.proposals[pid]["grant_id"] == key and \
                    self.model.proposals[pid]["phase"] == "VOIDED_BY_REVOCATION":
                self.step("probe", "decide_proposal", {"actor": g["issuer"], "proposal_id": pid,
                                                       "decision": "APPROVE", "now": mid})

    def do_decide(self):
        if not self.model.proposals:
            return self.do_propose()
        pid = self.rng.choice(list(self.model.proposals))
        g = self.model.grants[self.model.proposals[pid]["grant_id"]]
        actor = g["issuer"] if self.chance(0.85) else self.pick(list(HUMANS) + [STRANGER])
        p = {"actor": actor, "proposal_id": pid, "decision": self.pick(["APPROVE", "REJECT", "REJECT"]),
             "now": self.now_for(g)}
        if self.chance(0.12):
            field = self.rng.choice(["actor", "proposal_id", "decision", "now"])
            p[field] = self.pick({"actor": [None, 9, STRANGER], "proposal_id": [None, "", "p-nope"],
                                  "decision": [None, "MAYBE", "approve", 1]}.get(field) or [self.bad_now()])
        self.step("decide", "decide_proposal", p)

    def do_decide_replay(self):
        decided = [key for key, pr in self.model.proposals.items()
                   if pr["phase"] in ("HUMAN_APPROVED", "HUMAN_REJECTED")]
        if not decided:
            return self.do_decide()
        pid = self.rng.choice(decided)
        pr = self.model.proposals[pid]
        g = self.model.grants[pr["grant_id"]]
        decision = pr["decision"] if self.chance(0.7) else ("APPROVE" if pr["decision"] == "REJECT" else "REJECT")
        self.step("decide", "decide_proposal", {"actor": g["issuer"], "proposal_id": pid, "decision": decision,
                                                "now": self.now_for(g)})

    def tool_params(self, key, tool, args, now=None, actor=None):
        g = self.model.grants[key]
        return {"actor": actor or g["agent_id"], "grant_id": key, "tool": tool, "args": args,
                "now": self.now_for(g) if now is None else now}

    def propose_args(self, key, pid=None):
        g = self.model.grants[key]
        r = self.rng
        held = self.model.charged[key][0]
        limits = g["limits"]
        room = limits["cumulative_max"] - held
        per = limits["per_action_max"]
        amount = r.choice([room, room - 1, room + 1, per, per - 1, per + 1, 1, 2, r.randint(1, per + 3)])
        amount = min(CONTRACT_MONEY_MAX, max(1, amount))
        surface = r.choice(g["scope"]["surfaces"]) if self.chance(0.88) else OUTSIDE_SURFACE
        args = {"proposal_id": pid or self.fresh_proposal_id(), "surface": surface, "amount": amount,
                "kind": r.choice(KINDS)}
        if self.chance(0.4):
            subjects = g["scope"]["subjects"]
            args["subject"] = r.choice(subjects) if subjects and self.chance(0.7) else \
                r.choice(SUBJECTS + (OUTSIDE_SUBJECT,))
        return args

    def defect_args(self, args):
        r = self.rng
        roll = r.randrange(7)
        if roll == 0:
            del args[r.choice(["proposal_id", "surface", "amount", "kind"])]
        elif roll == 1:
            args["extra"] = 1
        elif roll == 2:
            args["amount"] = self.pick([0, -1, True, False, 1.5, "5", None, 10**12 + 1])
        elif roll == 3:
            args["proposal_id"] = self.bad_id()
        elif roll == 4:
            args["surface"] = self.bad_id()
        elif roll == 5:
            args["kind"] = self.bad_id()
        else:
            args["subject"] = self.bad_id()
        return args

    def defect_call(self, p):
        r = self.rng
        roll = r.randrange(5)
        if roll == 0:
            p["actor"] = self.pick([None, 3, "human-a", STRANGER, "agent-1"])
        elif roll == 1:
            p["grant_id"] = self.pick([None, "", "g-nope"])
        elif roll == 2:
            p["now"] = self.bad_now()
        elif roll == 3:
            p["args"] = self.pick([None, [], "x", 5])
        else:
            p["tool"] = self.pick([None, 5, "", "pay"])
        return p

    def do_propose(self):
        key = self.pick_grant()
        if key is None:
            return self.do_issue()
        reuse = self.chance(0.2) and self.model.proposals
        pid = self.rng.choice(list(self.model.proposals)) if reuse else None
        args = self.propose_args(key, pid)
        if self.chance(0.1):
            args = self.defect_args(args)
        p = self.tool_params(key, "propose_action", args)
        if self.chance(0.08):
            p = self.defect_call(p)
        kind, _ = self.step("propose", "call_tool", p)
        if kind == "ok":
            self.proposed[args["proposal_id"]] = copy.deepcopy(p)

    def do_propose_replay(self):
        if not self.proposed:
            return self.do_propose()
        p = copy.deepcopy(self.proposed[self.rng.choice(list(self.proposed))])
        p["now"] = self.now_for(self.model.grants[p["grant_id"]])
        self.step("propose", "call_tool", p)

    def do_propose_conflict(self):
        if not self.proposed:
            return self.do_propose()
        p = copy.deepcopy(self.proposed[self.rng.choice(list(self.proposed))])
        args = p["args"]
        p["now"] = self.now_for(self.model.grants[p["grant_id"]])
        if p["tool"] == "propose_grant_change":
            args["requested"] = {"note": "other-note"}
        else:
            field = self.rng.choice(["amount", "surface", "kind", "subject"])
            if field == "amount":
                args["amount"] = args["amount"] + 1 if args["amount"] < CONTRACT_MONEY_MAX else 1
            elif field == "surface":
                args["surface"] = OUTSIDE_SURFACE
            elif field == "kind":
                args["kind"] = "kind-other"
            else:
                args["subject"] = OUTSIDE_SUBJECT if args.get("subject") != OUTSIDE_SUBJECT else "sub-1"
        if self.chance(0.25):
            others = [key for key in self.model.grants if key != p["grant_id"]]
            if others:
                p["grant_id"] = self.rng.choice(others)
                p["actor"] = self.model.grants[p["grant_id"]]["agent_id"]
        self.step("propose", "call_tool", p)

    def rand_request(self):
        r = self.rng
        keys = [k for k in ("authority", "scope", "limits", "period", "note") if self.chance(0.5)] or ["note"]
        parts = {"authority": self.rand_authority(), "scope": self.rand_scope(), "limits": self.rand_limits(),
                 "period": self.rand_period(), "note": "note-%d" % r.randint(0, 3)}
        return {k: parts[k] for k in keys}

    def do_change(self):
        key = self.pick_grant()
        if key is None:
            return self.do_issue()
        args = {"proposal_id": self.fresh_proposal_id(), "requested": self.rand_request()}
        roll = self.rng.random()
        if roll < 0.14:
            args["requested"] = self.pick([{}, {"bogus": 1}, {"authority": ["EXECUTE"]}, {"authority": []},
                                           {"limits": {}}, {"period": {"not_before": 3, "not_after": 1}},
                                           {"scope": {"surfaces": []}}, {"note": ""}, [], None])
        elif roll < 0.2:
            self.rng.choice([lambda: args.pop("requested"), lambda: args.update(extra=1),
                             lambda: args.update(proposal_id=self.bad_id())])()
        p = self.tool_params(key, "propose_grant_change", args)
        kind, _ = self.step("change", "call_tool", p)
        if kind == "ok":
            self.proposed[args["proposal_id"]] = copy.deepcopy(p)

    def do_withdraw(self):
        if not self.model.proposals:
            return self.do_propose()
        open_ids = [k for k, pr in self.model.proposals.items() if pr["phase"] == "PROPOSED"]
        pid = self.rng.choice(open_ids if open_ids and self.chance(0.75) else list(self.model.proposals))
        key = self.model.proposals[pid]["grant_id"]
        if self.chance(0.1):
            key = self.pick_grant(0.5)
        args = {"proposal_id": pid}
        if self.chance(0.08):
            args = self.pick([{}, {"proposal_id": pid, "extra": 1}, {"proposal_id": "p-nope"},
                              {"proposal_id": self.bad_id()}])
        self.step("withdraw", "call_tool", self.tool_params(key, "withdraw_proposal", args))

    def do_query_grant(self):
        key = self.pick_grant(0.7)
        if key is None:
            return self.do_issue()
        args = {} if self.chance(0.92) else {"surface": "surf-a"}
        self.step("query_grant", "call_tool", self.tool_params(key, "query_grant", args))

    def do_query_subject(self):
        key = self.pick_grant(0.7)
        if key is None:
            return self.do_issue()
        g = self.model.grants[key]
        args = {"surface": self.rng.choice(g["scope"]["surfaces"]) if self.chance(0.85) else OUTSIDE_SURFACE}
        if self.chance(0.5):
            args["subject"] = self.rng.choice(SUBJECTS + (OUTSIDE_SUBJECT,))
        if self.chance(0.08):
            args = self.pick([{}, {"subject": "sub-1"}, {"surface": ""}, {"surface": "surf-a", "x": 1}])
        self.step("query_subject", "call_tool", self.tool_params(key, "query_subject", args))

    def do_deny(self):
        key = self.pick_grant(0.6) or "g-none"
        tool = self.pick(sorted(DENY_CODES))
        args = self.pick([{}, {"amount": 5}, {"surface": "surf-a"}])
        now = self.rng.randint(0, 40)
        actor = self.pick(AGENTS)
        if key in self.model.grants and self.chance(0.7):
            actor = self.model.grants[key]["agent_id"]
        self.step("deny", "call_tool", {"actor": actor, "grant_id": key, "tool": tool, "args": args, "now": now})

    def do_unknown_tool(self):
        key = self.pick_grant(0.6) or "g-none"
        tool = self.pick(["delegate", "close_delegation", "mystery-tool", "Transfer", " transfer", "TRANSFER",
                          "execute", "approve", "decide_proposal", "revoke_grant", "attempt_execution", ""])
        actor = self.model.grants[key]["agent_id"] if key in self.model.grants else self.pick(AGENTS)
        self.step("unknown_tool", "call_tool", {"actor": actor, "grant_id": key, "tool": tool,
                                                "args": self.pick([{}, {"amount": 1}]),
                                                "now": self.rng.randint(0, 40)})

    def do_attempt(self):
        pid = self.pick(list(self.model.proposals) + ["p-nope", "", None, 4])
        actor = self.pick(list(AGENTS) + list(HUMANS) + [STRANGER, None, 7])
        self.step("attempt", "attempt_execution", {"actor": actor, "proposal_id": pid})

    def do_view(self):
        if self.chance(0.5):
            pool = list(self.model.grants) + ["g-nope", "", None]
            self.step("view_grant", "view_grant", {"grant_id": self.pick(pool)})
        else:
            pool = list(self.model.proposals) + ["p-nope", "", None]
            self.step("view_proposal", "view_proposal", {"proposal_id": self.pick(pool)})

    def do_ai_actor(self):
        ai = self.pick(AGENTS)
        roll = self.rng.randrange(3)
        if roll == 0:
            p = self.fresh_issue()
            p["actor"] = ai
            self.step("ai_actor", "issue_grant", p)
        elif roll == 1:
            key = self.pick_grant(0.5)
            if key is None:
                return self.do_issue()
            self.step("ai_actor", "revoke_grant", {"actor": ai, "grant_id": key, "reason": "stop"})
        else:
            if not self.model.proposals:
                return self.do_propose()
            pid = self.rng.choice(list(self.model.proposals))
            self.step("ai_actor", "decide_proposal", {"actor": ai, "proposal_id": pid,
                                                      "decision": self.pick(["APPROVE", "REJECT"]),
                                                      "now": self.rng.randint(0, 40)})

    def do_stranger(self):
        roll = self.rng.randrange(4)
        if roll == 0:
            p = self.fresh_issue()
            p["actor"] = STRANGER
            self.step("stranger", "issue_grant", p)
        elif roll == 1:
            key = self.pick_grant(0.5)
            if key is None:
                return self.do_issue()
            other = [h for h in HUMANS if h != self.model.grants[key]["issuer"]][0]
            self.step("stranger", "revoke_grant", {"actor": other, "grant_id": key, "reason": "stop"})
        elif roll == 2:
            if not self.model.proposals:
                return self.do_propose()
            pid = self.rng.choice(list(self.model.proposals))
            other = [h for h in HUMANS if h != self.model.grants[self.model.proposals[pid]["grant_id"]]["issuer"]][0]
            self.step("stranger", "decide_proposal", {"actor": other, "proposal_id": pid, "decision": "APPROVE",
                                                      "now": self.rng.randint(0, 40)})
        else:
            key = self.pick_grant(0.5)
            if key is None:
                return self.do_issue()
            g = self.model.grants[key]
            wrong = self.pick([a for a in AGENTS if a != g["agent_id"]] + [g["issuer"], STRANGER])
            self.step("stranger", "call_tool", {"actor": wrong, "grant_id": key, "tool": "query_grant",
                                                "args": {}, "now": self.now_for(g)})

    # --- results
    def fingerprint(self):
        return hashlib.sha256(canon([self.digests, sorted(self.counters.items())]).encode("utf-8")).hexdigest()

    def replay(self, humans=HUMANS, agents=AGENTS):
        """Command-log replay on a fresh mock: every intermediate digest and
        every result must reproduce. The mock has no journal or restore."""
        fresh = new_mock(humans, agents)
        if fresh.state_digest() != self.digests[0]:
            fail("an empty mock has a different digest")
        for index, (method, params, digest, result) in enumerate(self.log, start=1):
            got = getattr(fresh, method)(**copy.deepcopy(params))
            if canon(got) != result:
                fail("replay of command %d (%s) returned a different result" % (index, method))
            if fresh.state_digest() != digest:
                fail("replay of command %d (%s) reached a different state_digest" % (index, method))
        return fresh
