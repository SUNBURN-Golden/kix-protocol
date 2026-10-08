"""Offline AI delegation authority mock.

Deterministic and in-memory. No network, files, bank, payment provider,
signing key, or chain client. A human principal may record a grant. An AI
agent may read or leave an inert proposal memo. Nothing here issues a right,
pays, transfers, refunds, or signs.

EXECUTE is named and rejected. attempt_execution always fails.
The constructor has no switch that turns execution on.

Contract: docs/contracts/AI_DELEGATION_AUTHORITY.md
"""

from __future__ import annotations

import hashlib
import json

MONEY_MAX = 10**12
PROVENANCE = "MOCK_AI_DELEGATION_ONLY"
LIFECYCLE = "IN_MEMORY_FSM"

ALLOWLIST = frozenset(
    {
        "query_grant",
        "query_subject",
        "propose_action",
        "withdraw_proposal",
        "propose_grant_change",
    }
)

DENYLIST = {
    "transfer": "TRANSFER_FORBIDDEN",
    "refund_execution": "REFUND_EXECUTION_FORBIDDEN",
    "sign": "SIGNING_FORBIDDEN",
    "issue": "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY",
    "pay": "MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY",
    "widen_grant": "AI_SELF_EXPANSION_FORBIDDEN",
    "reissue_grant": "AI_SELF_EXPANSION_FORBIDDEN",
    "revive_grant": "AI_SELF_EXPANSION_FORBIDDEN",
}

TOOL_LEVEL = {
    "query_grant": "QUERY",
    "query_subject": "QUERY",
    "propose_action": "PROPOSE",
    "withdraw_proposal": "PROPOSE",
    "propose_grant_change": "PROPOSE",
}

FALSE_FLAGS = (
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

_CONSUMING = frozenset({"PROPOSED", "HUMAN_APPROVED"})
_PROPOSAL_PHASES = frozenset(
    {"PROPOSED", "HUMAN_APPROVED", "HUMAN_REJECTED", "WITHDRAWN", "VOIDED_BY_REVOCATION"}
)


class AiDelegationError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise AiDelegationError(code)


def _ident(value: object, code: str = "INVALID_ID") -> str:
    _require(type(value) is str and 0 < len(value) <= 100 and value.strip() == value, code)
    return value


def _money(value: object) -> int:
    _require(type(value) is int and 0 < value <= MONEY_MAX, "INVALID_AMOUNT")
    return value


def _logical(value: object) -> int:
    _require(type(value) is int and 0 <= value <= MONEY_MAX, "INVALID_PERIOD")
    return value


def _canonical(value: object) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        raise AiDelegationError("MOCK_INVARIANT") from None


def _flags() -> dict:
    return {flag: False for flag in FALSE_FLAGS}


def _copy(value: dict) -> dict:
    return json.loads(_canonical(value))


def _registry(value: object, code: str) -> frozenset[str]:
    _require(type(value) is list, code)
    found = []
    for item in value:
        found.append(_ident(item))
    _require(len(found) == len(set(found)), code)
    return frozenset(found)


def _id_list(value: object, *, empty_ok: bool) -> list[str]:
    _require(type(value) is list, "INVALID_ID")
    if not empty_ok:
        _require(len(value) > 0, "SCOPE_VIOLATION")
    names = [_ident(item) for item in value]
    _require(len(names) == len(set(names)), "INVALID_ID")
    return sorted(names)


def _parse_authority(value: object) -> list[str]:
    _require(type(value) is list and 0 < len(value) <= 3, "INVALID_ID")
    _require(all(type(item) is str for item in value), "INVALID_ID")
    if "EXECUTE" in value:
        raise AiDelegationError("EXECUTE_AUTHORITY_DISABLED")
    _require(len(value) == len(set(value)), "INVALID_ID")
    _require(set(value) <= {"QUERY", "PROPOSE"}, "INVALID_ID")
    return sorted(value)


def _parse_scope(value: object) -> dict:
    _require(type(value) is dict, "SCOPE_VIOLATION")
    _require("surfaces" in value and set(value) <= {"surfaces", "subjects"}, "SCOPE_VIOLATION")
    surfaces = _id_list(value["surfaces"], empty_ok=False)
    subjects = None
    if "subjects" in value:
        subjects = _id_list(value["subjects"], empty_ok=True)
    return {"surfaces": surfaces, "subjects": subjects}


def _parse_limits(value: object) -> dict:
    _require(type(value) is dict, "LIMIT_REQUIRED")
    required = {"per_action_max", "cumulative_max", "count_max", "currency"}
    _require(set(value) == required, "LIMIT_REQUIRED")
    _require(value["currency"] == "KRW", "LIMIT_REQUIRED")
    return {
        "per_action_max": _money(value["per_action_max"]),
        "cumulative_max": _money(value["cumulative_max"]),
        "count_max": _money(value["count_max"]),
        "currency": "KRW",
    }


def _parse_period(value: object) -> dict:
    _require(type(value) is dict, "INVALID_PERIOD")
    _require(set(value) == {"not_before", "not_after"}, "INVALID_PERIOD")
    start = _logical(value["not_before"])
    end = _logical(value["not_after"])
    _require(start <= end, "INVALID_PERIOD")
    return {"not_before": start, "not_after": end}


class AiDelegationMock:
    def __init__(self, human_principals: object, ai_agents: object) -> None:
        humans = _registry(human_principals, "INVALID_ID")
        agents = _registry(ai_agents, "INVALID_ID")
        _require(humans.isdisjoint(agents), "MOCK_INVARIANT")
        self._humans = humans
        self._agents = agents
        self._grants: dict[str, dict] = {}
        self._proposals: dict[str, dict] = {}
        self._seq = 0

    def issue_grant(
        self,
        actor: object,
        grant_id: object,
        agent_id: object,
        authority: object,
        scope: object,
        limits: object,
        period: object,
    ) -> dict:
        actor = self._human(actor, "AI_SELF_EXPANSION_FORBIDDEN")
        grant_id = _ident(grant_id)
        agent_id = _ident(agent_id)
        _require(agent_id in self._agents, "UNKNOWN_ACTOR")
        parsed_authority = _parse_authority(authority)
        parsed_scope = _parse_scope(scope)
        parsed_limits = _parse_limits(limits)
        parsed_period = _parse_period(period)
        binding = _canonical(
            {
                "grant_id": grant_id,
                "issuer": actor,
                "agent_id": agent_id,
                "authority": parsed_authority,
                "scope": parsed_scope,
                "limits": parsed_limits,
                "period": parsed_period,
            }
        )
        current = self._grants.get(grant_id)
        if current is not None:
            _require(current["binding"] == binding, "GRANT_BINDING_CONFLICT")
            return {"duplicate": True, "grant": self._view_grant(current)}
        _require(self._active_id(actor, agent_id) is None, "GRANT_NOT_CURRENT")
        row = {
            "binding": binding,
            "grant_id": grant_id,
            "generation": self._next_generation(actor, agent_id),
            "issuer": actor,
            "agent_id": agent_id,
            "authority": parsed_authority,
            "scope": parsed_scope,
            "limits": parsed_limits,
            "period": parsed_period,
            "phase": "ACTIVE",
            "revoked_at_seq": None,
            "reason": None,
        }
        self._grants[grant_id] = row
        self._invariant()
        return {"duplicate": False, "grant": self._view_grant(row)}

    def revoke_grant(self, actor: object, grant_id: object, reason: object) -> dict:
        actor = self._human(actor, "AI_SELF_EXPANSION_FORBIDDEN")
        grant_id = _ident(grant_id)
        reason = _ident(reason)
        row = self._grants.get(grant_id)
        _require(row is not None, "UNKNOWN_GRANT")
        _require(row["issuer"] == actor, "UNKNOWN_ACTOR")
        if row["phase"] == "REVOKED":
            return {"duplicate": True, "grant": self._view_grant(row)}
        self._seq += 1
        row["phase"] = "REVOKED"
        row["revoked_at_seq"] = self._seq
        row["reason"] = reason
        for proposal in self._proposals.values():
            if proposal["grant_id"] == grant_id and proposal["phase"] == "PROPOSED":
                proposal["phase"] = "VOIDED_BY_REVOCATION"
        self._invariant()
        return {"duplicate": False, "grant": self._view_grant(row)}

    def decide_proposal(self, actor: object, proposal_id: object, decision: object, now: object) -> dict:
        actor = self._human(actor, "AI_CANNOT_DECIDE")
        proposal_id = _ident(proposal_id)
        _require(type(decision) is str and decision in ("APPROVE", "REJECT"), "INVALID_ID")
        now = _logical(now)
        proposal = self._proposals.get(proposal_id)
        _require(proposal is not None, "UNKNOWN_PROPOSAL")
        grant = self._grants[proposal["grant_id"]]
        _require(grant["issuer"] == actor, "UNKNOWN_ACTOR")
        if proposal["phase"] == "HUMAN_APPROVED" and decision == "APPROVE":
            return {"duplicate": True, "proposal": self._view_proposal(proposal)}
        if proposal["phase"] == "HUMAN_REJECTED" and decision == "REJECT":
            return {"duplicate": True, "proposal": self._view_proposal(proposal)}
        if proposal["phase"] == "VOIDED_BY_REVOCATION":
            raise AiDelegationError("GRANT_REVOKED")
        _require(proposal["phase"] == "PROPOSED", "PROPOSAL_BINDING_CONFLICT")
        self._require_in_force(grant, now)
        self._require_room(grant, add_amount=0, add_count=0, action_amount=proposal["amount"])
        _require(grant["limits"]["currency"] == "KRW", "LIMIT_REQUIRED")
        proposal["phase"] = "HUMAN_APPROVED" if decision == "APPROVE" else "HUMAN_REJECTED"
        proposal["decision"] = decision
        proposal["effects_executed"] = False
        self._invariant()
        return {"duplicate": False, "proposal": self._view_proposal(proposal)}

    def call_tool(self, actor: object, grant_id: object, tool: object, args: object, now: object) -> dict:
        _require(type(actor) is str and actor in self._agents, "UNKNOWN_ACTOR")
        grant_id = _ident(grant_id)
        _require(type(tool) is str, "INVALID_ID")
        if tool in DENYLIST:
            raise AiDelegationError(DENYLIST[tool])
        _require(tool in ALLOWLIST, "TOOL_NOT_ALLOWED")
        now = _logical(now)
        _require(type(args) is dict, "INVALID_ID")
        grant = self._grants.get(grant_id)
        _require(grant is not None, "UNKNOWN_GRANT")
        _require(grant["agent_id"] == actor, "UNKNOWN_ACTOR")
        if tool == "withdraw_proposal":
            return self._withdraw(grant, args)
        if tool == "propose_action":
            return self._propose_action(grant, args, now)
        if tool == "propose_grant_change":
            return self._propose_change(grant, args, now)
        self._require_in_force(grant, now)
        _require(TOOL_LEVEL[tool] in grant["authority"], "TOOL_NOT_ALLOWED")
        if tool == "query_grant":
            _require(set(args) == set(), "INVALID_ID")
            return {"duplicate": False, "grant": self._view_grant(grant)}
        surface, subject = self._surface_subject(args)
        self._require_scope(grant, surface, subject)
        body = self._envelope()
        body.update(
            {
                "duplicate": False,
                "match": {"surface": surface, "subject": subject, "in_scope": True},
            }
        )
        return _copy(body)

    def attempt_execution(self, actor: object, proposal_id: object) -> None:
        del actor, proposal_id
        raise AiDelegationError("DELEGATED_EXECUTION_DISABLED")

    def view_grant(self, grant_id: object) -> dict:
        grant_id = _ident(grant_id)
        row = self._grants.get(grant_id)
        _require(row is not None, "UNKNOWN_GRANT")
        return self._view_grant(row)

    def view_proposal(self, proposal_id: object) -> dict:
        proposal_id = _ident(proposal_id)
        row = self._proposals.get(proposal_id)
        _require(row is not None, "UNKNOWN_PROPOSAL")
        return self._view_proposal(row)

    def canonical_state(self) -> dict:
        grants = [self._stored_grant(row) for row in self._grants.values()]
        proposals = [self._stored_proposal(row) for row in self._proposals.values()]
        body = {
            "grants": sorted(grants, key=lambda item: item["grant_id"]),
            "proposals": sorted(proposals, key=lambda item: item["proposal_id"]),
            "revoke_seq": self._seq,
        }
        return json.loads(_canonical(body))

    def state_digest(self) -> str:
        payload = _canonical(self.canonical_state()).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _human(self, actor: object, ai_code: str) -> str:
        _require(type(actor) is str, "UNKNOWN_ACTOR")
        if actor in self._agents:
            raise AiDelegationError(ai_code)
        _require(actor in self._humans, "UNKNOWN_ACTOR")
        return actor

    def _active_id(self, issuer: str, agent_id: str) -> str | None:
        for row in self._grants.values():
            if row["issuer"] == issuer and row["agent_id"] == agent_id and row["phase"] == "ACTIVE":
                return row["grant_id"]
        return None

    def _next_generation(self, issuer: str, agent_id: str) -> int:
        generations = [
            row["generation"]
            for row in self._grants.values()
            if row["issuer"] == issuer and row["agent_id"] == agent_id
        ]
        return 1 + max(generations) if generations else 1

    def _require_in_force(self, grant: dict, now: int) -> None:
        _require(grant["phase"] != "REVOKED", "GRANT_REVOKED")
        _require(self._active_id(grant["issuer"], grant["agent_id"]) == grant["grant_id"], "GRANT_NOT_CURRENT")
        period = grant["period"]
        _require(now >= period["not_before"], "GRANT_NOT_CURRENT")
        _require(now <= period["not_after"], "GRANT_EXPIRED")
        _require(grant["limits"]["currency"] == "KRW", "LIMIT_REQUIRED")

    def _charged(self, grant_id: str) -> tuple[int, int]:
        amount = 0
        count = 0
        for proposal in self._proposals.values():
            if proposal["grant_id"] != grant_id or proposal["phase"] not in _CONSUMING:
                continue
            count += 1
            if proposal["amount"] is not None:
                amount += proposal["amount"]
        return amount, count

    def _require_room(self, grant: dict, *, add_amount: int, add_count: int, action_amount: int | None) -> None:
        limits = grant["limits"]
        if action_amount is not None:
            _require(action_amount <= limits["per_action_max"], "PER_ACTION_EXCEEDED")
        charged_amount, charged_count = self._charged(grant["grant_id"])
        _require(charged_amount + add_amount <= limits["cumulative_max"], "CUMULATIVE_EXCEEDED")
        _require(charged_count + add_count <= limits["count_max"], "COUNT_EXCEEDED")

    def _require_scope(self, grant: dict, surface: str, subject: str | None) -> None:
        _require(surface in grant["scope"]["surfaces"], "SCOPE_VIOLATION")
        subjects = grant["scope"]["subjects"]
        if subjects is None or subject is None:
            return
        _require(subject in subjects, "SCOPE_VIOLATION")

    def _surface_subject(self, args: dict) -> tuple[str, str | None]:
        _require(set(args) <= {"surface", "subject"} and "surface" in args, "INVALID_ID")
        surface = _ident(args["surface"])
        subject = _ident(args["subject"]) if "subject" in args else None
        return surface, subject

    def _open_for_write(self, grant: dict, now: int, level: str) -> None:
        self._require_in_force(grant, now)
        _require(level in grant["authority"], "TOOL_NOT_ALLOWED")

    def _propose_action(self, grant: dict, args: dict, now: int) -> dict:
        allowed = {"proposal_id", "surface", "subject", "amount", "kind"}
        _require(set(args) <= allowed and {"proposal_id", "surface", "amount", "kind"} <= set(args), "INVALID_ID")
        proposal_id = _ident(args["proposal_id"])
        surface = _ident(args["surface"])
        subject = _ident(args["subject"]) if "subject" in args else None
        amount = _money(args["amount"])
        kind = _ident(args["kind"])
        memo = None
        binding = self._proposal_binding(
            proposal_id, grant["grant_id"], "propose_action", surface, subject, amount, kind, memo
        )
        existing = self._proposals.get(proposal_id)
        if existing is not None:
            _require(existing["binding"] == binding, "PROPOSAL_BINDING_CONFLICT")
            return {"duplicate": True, "proposal": self._view_proposal(existing)}
        self._open_for_write(grant, now, "PROPOSE")
        self._require_scope(grant, surface, subject)
        self._require_room(grant, add_amount=amount, add_count=1, action_amount=amount)
        row = self._new_proposal(
            proposal_id, grant, "propose_action", surface, subject, amount, kind, memo, binding
        )
        self._proposals[proposal_id] = row
        self._invariant()
        return {"duplicate": False, "proposal": self._view_proposal(row)}

    def _propose_change(self, grant: dict, args: dict, now: int) -> dict:
        _require(set(args) == {"proposal_id", "requested"}, "INVALID_ID")
        proposal_id = _ident(args["proposal_id"])
        memo = self._parse_request(args["requested"])
        binding = self._proposal_binding(
            proposal_id, grant["grant_id"], "propose_grant_change", None, None, None, "GRANT_CHANGE", memo
        )
        existing = self._proposals.get(proposal_id)
        if existing is not None:
            _require(existing["binding"] == binding, "PROPOSAL_BINDING_CONFLICT")
            return {"duplicate": True, "proposal": self._view_proposal(existing)}
        self._open_for_write(grant, now, "PROPOSE")
        self._require_room(grant, add_amount=0, add_count=1, action_amount=None)
        row = self._new_proposal(
            proposal_id, grant, "propose_grant_change", None, None, None, "GRANT_CHANGE", memo, binding
        )
        self._proposals[proposal_id] = row
        self._invariant()
        return {"duplicate": False, "proposal": self._view_proposal(row)}

    def _withdraw(self, grant: dict, args: dict) -> dict:
        _require(grant["phase"] != "REVOKED", "GRANT_REVOKED")
        _require(TOOL_LEVEL["withdraw_proposal"] in grant["authority"], "TOOL_NOT_ALLOWED")
        _require(set(args) == {"proposal_id"}, "INVALID_ID")
        proposal_id = _ident(args["proposal_id"])
        proposal = self._proposals.get(proposal_id)
        _require(proposal is not None, "UNKNOWN_PROPOSAL")
        _require(proposal["grant_id"] == grant["grant_id"], "PROPOSAL_BINDING_CONFLICT")
        if proposal["phase"] == "WITHDRAWN":
            return {"duplicate": True, "proposal": self._view_proposal(proposal)}
        if proposal["phase"] == "VOIDED_BY_REVOCATION":
            raise AiDelegationError("GRANT_REVOKED")
        _require(proposal["phase"] == "PROPOSED", "PROPOSAL_BINDING_CONFLICT")
        proposal["phase"] = "WITHDRAWN"
        self._invariant()
        return {"duplicate": False, "proposal": self._view_proposal(proposal)}

    def _parse_request(self, value: object) -> dict:
        _require(type(value) is dict, "INVALID_ID")
        _require(set(value) <= {"authority", "scope", "limits", "period", "note"}, "INVALID_ID")
        _require(len(value) > 0, "INVALID_ID")
        memo: dict = {}
        if "authority" in value:
            memo["authority"] = _parse_authority(value["authority"])
        if "scope" in value:
            memo["scope"] = _parse_scope(value["scope"])
        if "limits" in value:
            memo["limits"] = _parse_limits(value["limits"])
        if "period" in value:
            memo["period"] = _parse_period(value["period"])
        if "note" in value:
            memo["note"] = _ident(value["note"])
        return memo

    def _proposal_binding(
        self,
        proposal_id: str,
        grant_id: str,
        tool: str,
        surface: str | None,
        subject: str | None,
        amount: int | None,
        kind: str,
        memo: dict | None,
    ) -> str:
        return _canonical(
            {
                "proposal_id": proposal_id,
                "grant_id": grant_id,
                "tool": tool,
                "surface": surface,
                "subject": subject,
                "amount": amount,
                "kind": kind,
                "memo": memo,
            }
        )

    def _new_proposal(
        self,
        proposal_id: str,
        grant: dict,
        tool: str,
        surface: str | None,
        subject: str | None,
        amount: int | None,
        kind: str,
        memo: dict | None,
        binding: str,
    ) -> dict:
        return {
            "binding": binding,
            "proposal_id": proposal_id,
            "grant_id": grant["grant_id"],
            "generation": grant["generation"],
            "tool": tool,
            "phase": "PROPOSED",
            "surface": surface,
            "subject": subject,
            "amount": amount,
            "kind": kind,
            "memo": memo,
            "decision": None,
            "effects_executed": False,
        }

    def _envelope(self) -> dict:
        body = {"provenance": PROVENANCE, "lifecycle_authority": LIFECYCLE}
        body.update(_flags())
        return body

    def _view_grant(self, row: dict) -> dict:
        body = self._envelope()
        body.update(self._stored_grant(row))
        return _copy(body)

    def _view_proposal(self, row: dict) -> dict:
        body = self._envelope()
        body.update(self._stored_proposal(row))
        return _copy(body)

    def _stored_grant(self, row: dict) -> dict:
        return {
            "grant_id": row["grant_id"],
            "generation": row["generation"],
            "issuer": row["issuer"],
            "agent_id": row["agent_id"],
            "authority": list(row["authority"]),
            "scope": {
                "surfaces": list(row["scope"]["surfaces"]),
                "subjects": None if row["scope"]["subjects"] is None else list(row["scope"]["subjects"]),
            },
            "limits": dict(row["limits"]),
            "period": dict(row["period"]),
            "phase": row["phase"],
            "revoked_at_seq": row["revoked_at_seq"],
            "reason": row["reason"],
        }

    def _stored_proposal(self, row: dict) -> dict:
        return {
            "proposal_id": row["proposal_id"],
            "grant_id": row["grant_id"],
            "generation": row["generation"],
            "tool": row["tool"],
            "phase": row["phase"],
            "surface": row["surface"],
            "subject": row["subject"],
            "amount": row["amount"],
            "kind": row["kind"],
            "memo": row["memo"],
            "decision": row["decision"],
            "effects_executed": False,
        }

    def _invariant(self) -> None:
        active: set[tuple[str, str]] = set()
        generations: dict[tuple[str, str], set[int]] = {}
        for grant in self._grants.values():
            _require(grant["phase"] in ("ACTIVE", "REVOKED"), "MOCK_INVARIANT")
            _require(grant["limits"]["currency"] == "KRW", "MOCK_INVARIANT")
            _require(set(grant["authority"]) <= {"QUERY", "PROPOSE"}, "MOCK_INVARIANT")
            _require("EXECUTE" not in grant["authority"], "MOCK_INVARIANT")
            key = (grant["issuer"], grant["agent_id"])
            generations.setdefault(key, set()).add(grant["generation"])
            if grant["phase"] == "ACTIVE":
                _require(key not in active, "MOCK_INVARIANT")
                active.add(key)
                _require(grant["revoked_at_seq"] is None and grant["reason"] is None, "MOCK_INVARIANT")
            else:
                _require(type(grant["revoked_at_seq"]) is int and grant["revoked_at_seq"] > 0, "MOCK_INVARIANT")
                _require(type(grant["reason"]) is str, "MOCK_INVARIANT")
            charged_amount, charged_count = self._charged(grant["grant_id"])
            _require(0 <= charged_amount <= grant["limits"]["cumulative_max"], "MOCK_INVARIANT")
            _require(0 <= charged_count <= grant["limits"]["count_max"], "MOCK_INVARIANT")
        for key, gens in generations.items():
            del key
            _require(gens == set(range(1, len(gens) + 1)), "MOCK_INVARIANT")
        seen_seq = [row["revoked_at_seq"] for row in self._grants.values() if row["phase"] == "REVOKED"]
        _require(len(seen_seq) == len(set(seen_seq)), "MOCK_INVARIANT")
        _require(self._seq == (max(seen_seq) if seen_seq else 0), "MOCK_INVARIANT")
        for proposal in self._proposals.values():
            _require(proposal["grant_id"] in self._grants, "MOCK_INVARIANT")
            _require(proposal["phase"] in _PROPOSAL_PHASES, "MOCK_INVARIANT")
            _require(proposal["effects_executed"] is False, "MOCK_INVARIANT")
            if proposal["amount"] is not None:
                _require(type(proposal["amount"]) is int and 0 < proposal["amount"] <= MONEY_MAX, "MOCK_INVARIANT")
