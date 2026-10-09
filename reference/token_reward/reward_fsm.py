"""In-memory reward state machine for the token-reward reference model.

The machine decides which observe, hold, eligibility, submit, and effect
commands are accepted, then replays that journal deterministically.
Arithmetic and pool conservation stay in token_reward_model.py.

Commands are mock methods. They are not protocol catalogue entries.
The machine reads settlement, resale, and reservation state only as a
caller-supplied snapshot. It does not call those machines.

Provenance remains MOCK_TOKEN_REWARD_ONLY. A matched replay is equality of
this process's journal and views, not a payout, a bank debit, or chain
finality. approval_ref is a structural human slot. E-1 is open: this machine
does not name an approver and does not present a payout as authorized by a
real person.

The idempotency table follows reference/settlement_f01_f03/settlement_fsm.py.
"""

from __future__ import annotations

import json

from token_reward_model import (
    ALWAYS_FALSE_FLAGS,
    LIFECYCLE,
    PROVENANCE,
    SOURCE_FINALITY_FLAGS,
    SOURCE_KINDS,
    SPENDABLE_POOLS,
    UNIT,
    PoolLedger,
    TokenRewardError,
    _canonical,
    _copy,
    _digest,
    _false_flags,
    _ident,
    _money,
    _require,
    _sha256_text,
    effect_id,
    reward_id,
)

OBSERVED = "OBSERVED"
HELD = "HELD"
ELIGIBLE = "ELIGIBLE"
ISSUING = "ISSUING"
ISSUED = "ISSUED"
UNKNOWN = "UNKNOWN"
REVERSED = "REVERSED"
CLAWBACK_CLAIM = "CLAWBACK_CLAIM"

TOKEN_PHASES = frozenset(
    {OBSERVED, HELD, ELIGIBLE, ISSUING, ISSUED, UNKNOWN, REVERSED, CLAWBACK_CLAIM}
)
PRE_ISSUING = frozenset({OBSERVED, HELD, ELIGIBLE})
TOKEN_TERMINALS = frozenset({REVERSED, CLAWBACK_CLAIM, ISSUED})

KRW_UNPAID = "KRW_UNPAID"
KRW_REFUND_NOTED = "KRW_REFUND_NOTED"
KRW_PHASES = frozenset({KRW_UNPAID, KRW_REFUND_NOTED})

ABUSE_KINDS = frozenset({"SELF_TRADE", "DUPLICATED_ACCOUNTS", "REFERRAL_FARMING"})
TRANSFER_OUTCOMES = frozenset({"SUCCESS", "FAILED", "UNKNOWN"})
RESOLUTIONS = frozenset({"SUCCESS", "FAILED"})

REPLAYABLE = frozenset(
    {
        "observe",
        "hold",
        "mark_eligible",
        "submit",
        "observe_transfer_effects",
        "reconcile_unknown",
        "observe_source_cancel",
        "observe_krw_refund",
        "supersede",
    }
)

_JOURNAL_KEYS = frozenset({"op", "idempotency_key", "reward_id", "body"})
_UNSTORED_REJECTION = frozenset({"MOCK_INVARIANT", "IDEMPOTENCY_CONFLICT", "INVALID_JOURNAL"})
_APPROVAL_FIELDS = frozenset(
    {
        "record_id",
        "generation",
        "authority_id",
        "actor_type",
        "action",
        "scope_ref",
        "evidence_refs",
    }
)


def _reward_key(value: object) -> dict:
    _require(type(value) is dict and set(value) == {"program", "source_op_id", "recipient", "kind"}, "REWARD_KEY_FIELDS")
    return {
        "program": _ident(value["program"]),
        "source_op_id": _ident(value["source_op_id"]),
        "recipient": _ident(value["recipient"]),
        "kind": _ident(value["kind"]),
    }


def _source_kind(value: object) -> str:
    _require(type(value) is str and value in SOURCE_KINDS, "SOURCE_KIND_UNSUPPORTED")
    return value


def _source_view(value: object) -> dict:
    try:
        view = _copy(value)
    except (TypeError, ValueError) as error:
        raise TokenRewardError("SOURCE_VIEW_REJECTED") from error
    _require(type(view) is dict, "SOURCE_VIEW_REJECTED")
    _require(view.get("phase") == "COMMITTED", "SOURCE_NOT_COMMITTED")
    _require(view.get("currency") == "KRW", "CURRENCY_UNSUPPORTED")
    for name in SOURCE_FINALITY_FLAGS:
        _require(view.get(name) is False, "SOURCE_VIEW_REJECTED")
    return view


def _flag(value: object) -> bool:
    _require(type(value) is bool, "FLAG_TYPE")
    return value


def _optional_cap(value: object) -> int | None:
    if value is None:
        return None
    return _money(value, positive=False)


def _approval(value: object) -> dict:
    """Structural human slot. Not a named approver and not a real authorization."""

    _require(type(value) is dict, "APPROVAL_FIELDS")
    extra = set(value) - _APPROVAL_FIELDS
    _require(extra <= {"prior_record"}, "APPROVAL_FIELDS")
    _require(_APPROVAL_FIELDS <= set(value), "APPROVAL_FIELDS")
    actor = value["actor_type"]
    if actor == "AI":
        raise TokenRewardError("AI_APPROVAL_REJECTED")
    _require(actor == "HUMAN", "ACTOR_TYPE_REJECTED")
    generation = value["generation"]
    _require(type(generation) is int and 0 < generation <= 10**12, "APPROVAL_GENERATION")
    evidence = value["evidence_refs"]
    _require(type(evidence) is list and len(evidence) > 0, "APPROVAL_EVIDENCE_REQUIRED")
    cleaned = []
    for item in evidence:
        if item == "UNKNOWN":
            raise TokenRewardError("APPROVAL_EVIDENCE_UNKNOWN")
        cleaned.append(_ident(item))
    prior = value.get("prior_record")
    prior = None if prior is None else _ident(prior)
    return {
        "record_id": _ident(value["record_id"]),
        "generation": generation,
        "authority_id": _ident(value["authority_id"]),
        "actor_type": "HUMAN",
        "action": _ident(value["action"]),
        "scope_ref": _ident(value["scope_ref"]),
        "evidence_refs": cleaned,
        "prior_record": prior,
    }


def _permit(value: object) -> dict | None:
    if value is None:
        return None
    _require(type(value) is dict and set(value) == {"fence_ref", "signed_bytes_digest"}, "RESEND_PERMIT_REQUIRED")
    return {
        "fence_ref": _ident(value["fence_ref"]),
        "signed_bytes_digest": _digest(value["signed_bytes_digest"]),
    }


class RewardMachine:
    def __init__(self, opening_balances: object) -> None:
        self._pools = PoolLedger(opening_balances)
        self._rewards: dict[str, dict] = {}
        self._journal: list[dict] = []
        self._idempotency: dict[str, dict] = {}
        self._approval_ids: set[str] = set()

    def observe(
        self,
        reward_key: object,
        *,
        idempotency_key: object,
        source_view: object,
        rule_version: object,
        amount: object,
        source_kind: object,
    ) -> dict:
        raw = {
            "reward_key": reward_key,
            "source_view": source_view,
            "rule_version": rule_version,
            "amount": amount,
            "source_kind": source_kind,
        }

        def execute(key: str, request: str) -> dict:
            parsed = _reward_key(reward_key)
            derived = reward_id(**parsed)
            view = _source_view(source_view)
            version = _ident(rule_version, "INVALID_RULE_VERSION")
            points = _money(amount, positive=True)
            origin = _source_kind(source_kind)
            existing = self._rewards.get(derived)
            if existing is not None:
                if existing["rule_version"] != version:
                    raise TokenRewardError("RULE_VERSION_REPAY_FORBIDDEN")
                raise TokenRewardError("REWARD_ALREADY_OBSERVED")
            body = {
                "reward_key": parsed,
                "source_view": view,
                "rule_version": version,
                "amount": points,
                "source_kind": origin,
            }
            reward = {
                "reward_id": derived,
                "program": parsed["program"],
                "source_op_id": parsed["source_op_id"],
                "recipient": parsed["recipient"],
                "kind": parsed["kind"],
                "rule_version": version,
                "amount": points,
                "source_kind": origin,
                "source_view": view,
                "phase": OBSERVED,
                "token_outcome": "NONE",
                "token_effect_id": None,
                "krw_effect_id": effect_id(derived, "krw", 0),
                "krw_phase": KRW_UNPAID,
                "signed_bytes_digest": None,
                "effects_digest": None,
                "clawback_claim": False,
                "payout_effects": [],
                "supersessions": [],
                "approval_ref": None,
                "abuse_clear": None,
                "abuse_kind": None,
                "non_transferable_until_chargeback_end": True,
                "token_effect_closed": False,
                "successor_open": False,
                "spend_pool": None,
                "resend_count": 0,
            }
            self._rewards[derived] = reward
            self._invariant(reward)
            return self._accept(key, request, "observe", reward, body, effect=None)

        return self._call("observe", reward_key, idempotency_key, raw, execute)

    def hold(self, reward_id_value: object, *, idempotency_key: object) -> dict:
        def execute(key: str, request: str) -> dict:
            reward = self._reward(reward_id_value)
            self._enter(reward, frozenset({OBSERVED}))
            reward["phase"] = HELD
            self._invariant(reward)
            return self._accept(key, request, "hold", reward, {}, effect=None)

        return self._call("hold", reward_id_value, idempotency_key, {}, execute)

    def mark_eligible(
        self,
        reward_id_value: object,
        *,
        idempotency_key: object,
        window_closed: object,
        source_view: object,
        abuse_clear: object,
        abuse_kind: object = None,
        recipient_cap: object = None,
        program_cap: object = None,
    ) -> dict:
        raw = {
            "window_closed": window_closed,
            "source_view": source_view,
            "abuse_clear": abuse_clear,
            "abuse_kind": abuse_kind,
            "recipient_cap": recipient_cap,
            "program_cap": program_cap,
        }

        def execute(key: str, request: str) -> dict:
            closed = _flag(window_closed)
            view = _source_view(source_view)
            clear = _flag(abuse_clear)
            kind = self._abuse_kind(clear, abuse_kind)
            recipient_limit = _optional_cap(recipient_cap)
            program_limit = _optional_cap(program_cap)
            reward = self._reward(reward_id_value)
            self._enter(reward, frozenset({HELD}))
            if not closed:
                raise TokenRewardError("WINDOW_OPEN")
            if not clear:
                raise TokenRewardError("ABUSE_BLOCKED")
            self._apply_caps(reward, recipient_limit, program_limit)
            body = {
                "window_closed": True,
                "source_view": view,
                "abuse_clear": True,
                "abuse_kind": kind,
                "recipient_cap": recipient_limit,
                "program_cap": program_limit,
            }
            reward["phase"] = ELIGIBLE
            reward["source_view"] = view
            reward["abuse_clear"] = True
            reward["abuse_kind"] = kind
            self._invariant(reward)
            return self._accept(key, request, "mark_eligible", reward, body, effect=None)

        return self._call("mark_eligible", reward_id_value, idempotency_key, raw, execute)

    def submit(
        self,
        reward_id_value: object,
        *,
        idempotency_key: object,
        approval_ref: object,
        signed_bytes_digest: object,
        spend_pool: object,
        budget_ceiling: object = None,
        execution_permit: object = None,
    ) -> dict:
        """Preserve the signed-bytes digest, then open one token effect.

        A later submit while UNKNOWN is a same-bytes resend. It runs only
        when execution_permit carries a fence slot and the same digest.
        Without that permit the machine stays on the query path
        (reconcile_unknown). The permit is not a kernel fence.
        """

        raw = {
            "approval_ref": approval_ref,
            "signed_bytes_digest": signed_bytes_digest,
            "spend_pool": spend_pool,
            "budget_ceiling": budget_ceiling,
            "execution_permit": execution_permit,
        }

        def execute(key: str, request: str) -> dict:
            approval = _approval(approval_ref)
            digest = _digest(signed_bytes_digest)
            ceiling = _optional_cap(budget_ceiling)
            permit = _permit(execution_permit)
            reward = self._reward(reward_id_value)
            if reward["phase"] == UNKNOWN:
                pool = self._spend_pool_name(spend_pool)
                return self._resend(key, request, reward, approval, digest, pool, ceiling, permit)
            self._enter(reward, frozenset({ELIGIBLE}))
            pool = self._spend_pool_name(spend_pool)
            _require(permit is None, "PERMIT_UNEXPECTED")
            _require(approval["record_id"] not in self._approval_ids, "APPROVAL_RECORD_REUSED")
            if ceiling is not None and reward["amount"] > ceiling:
                raise TokenRewardError("BUDGET_EXCEEDED_PAUSED")
            generation = len(reward["supersessions"])
            token_effect = effect_id(reward["reward_id"], "token", generation)
            _require(token_effect != reward["krw_effect_id"], "MOCK_INVARIANT")
            body = {
                "approval_ref": approval,
                "signed_bytes_digest": digest,
                "spend_pool": pool,
                "budget_ceiling": ceiling,
                "execution_permit": None,
            }
            self._approval_ids.add(approval["record_id"])
            reward["approval_ref"] = approval
            reward["signed_bytes_digest"] = digest
            reward["spend_pool"] = pool
            reward["token_effect_id"] = token_effect
            reward["token_outcome"] = "PENDING"
            reward["token_effect_closed"] = False
            reward["successor_open"] = False
            reward["phase"] = ISSUING
            self._invariant(reward)
            effect = {"token_effect_id": token_effect, "signed_bytes_digest": digest}
            return self._accept(key, request, "submit", reward, body, effect=effect)

        return self._call("submit", reward_id_value, idempotency_key, raw, execute)

    def observe_transfer_effects(
        self,
        reward_id_value: object,
        *,
        idempotency_key: object,
        effects_digest: object,
        outcome: object,
    ) -> dict:
        raw = {"effects_digest": effects_digest, "outcome": outcome}

        def execute(key: str, request: str) -> dict:
            digest = _digest(effects_digest)
            _require(type(outcome) is str and outcome in TRANSFER_OUTCOMES, "OUTCOME_UNSUPPORTED")
            reward = self._reward(reward_id_value)
            self._enter(reward, frozenset({ISSUING}))
            _require(not reward["token_effect_closed"], "TOKEN_EFFECT_CLOSED")
            body = {"effects_digest": digest, "outcome": outcome}
            effect = self._apply_outcome(reward, digest, outcome)
            self._invariant(reward)
            return self._accept(key, request, "observe_transfer_effects", reward, body, effect=effect)

        return self._call("observe_transfer_effects", reward_id_value, idempotency_key, raw, execute)

    def reconcile_unknown(
        self,
        reward_id_value: object,
        *,
        idempotency_key: object,
        same_digest: object,
        resolution: object,
    ) -> dict:
        raw = {"same_digest": same_digest, "resolution": resolution}

        def execute(key: str, request: str) -> dict:
            digest = _digest(same_digest)
            _require(type(resolution) is str and resolution in RESOLUTIONS, "OUTCOME_UNSUPPORTED")
            reward = self._reward(reward_id_value)
            self._enter(reward, frozenset({UNKNOWN}))
            _require(digest == reward["signed_bytes_digest"], "DIGEST_MISMATCH")
            before_ids = list(self._rewards)
            body = {"same_digest": digest, "resolution": resolution}
            if resolution == "SUCCESS":
                effect = self._apply_outcome(reward, reward["effects_digest"] or digest, "SUCCESS")
            else:
                reward["token_outcome"] = "FAILED"
                reward["token_effect_closed"] = True
                reward["phase"] = ISSUING
                effect = {"token_effect_id": reward["token_effect_id"], "outcome": "FAILED"}
            _require(list(self._rewards) == before_ids, "MOCK_INVARIANT")
            self._invariant(reward)
            return self._accept(key, request, "reconcile_unknown", reward, body, effect=effect)

        return self._call("reconcile_unknown", reward_id_value, idempotency_key, raw, execute)

    def observe_source_cancel(
        self,
        reward_id_value: object,
        *,
        idempotency_key: object,
        source_view: object,
        reason: object,
    ) -> dict:
        raw = {"source_view": source_view, "reason": reason}

        def execute(key: str, request: str) -> dict:
            view = _source_view(source_view)
            why = _ident(reason)
            reward = self._reward(reward_id_value)
            _require(reward["phase"] not in {REVERSED, CLAWBACK_CLAIM}, "TERMINAL_IMMUTABLE")
            body = {"source_view": view, "reason": why}
            reward["source_view"] = view
            if reward["phase"] in PRE_ISSUING:
                reward["phase"] = REVERSED
                reward["clawback_claim"] = False
            else:
                reward["phase"] = CLAWBACK_CLAIM
                reward["clawback_claim"] = True
            self._invariant(reward)
            return self._accept(key, request, "observe_source_cancel", reward, body, effect=None)

        return self._call("observe_source_cancel", reward_id_value, idempotency_key, raw, execute)

    def observe_krw_refund(
        self,
        reward_id_value: object,
        *,
        idempotency_key: object,
        source_view: object,
        reason: object,
    ) -> dict:
        """Record a KRW-side refund effect without moving the token phase.

        Mock-internal. Not a protocol command. krw_paid stays false.
        """

        raw = {"source_view": source_view, "reason": reason}

        def execute(key: str, request: str) -> dict:
            view = _source_view(source_view)
            why = _ident(reason)
            reward = self._reward(reward_id_value)
            token_phase = reward["phase"]
            token_outcome = reward["token_outcome"]
            _require(reward["krw_phase"] == KRW_UNPAID, "KRW_EFFECT_ALREADY_NOTED")
            body = {"source_view": view, "reason": why}
            reward["krw_phase"] = KRW_REFUND_NOTED
            _require(reward["phase"] == token_phase, "MOCK_INVARIANT")
            _require(reward["token_outcome"] == token_outcome, "MOCK_INVARIANT")
            self._invariant(reward)
            effect = {"krw_effect_id": reward["krw_effect_id"], "krw_phase": KRW_REFUND_NOTED}
            return self._accept(key, request, "observe_krw_refund", reward, body, effect=effect)

        return self._call("observe_krw_refund", reward_id_value, idempotency_key, raw, execute)

    def supersede(
        self,
        reward_id_value: object,
        *,
        idempotency_key: object,
        approval_ref: object,
        rule_version: object,
    ) -> dict:
        raw = {"approval_ref": approval_ref, "rule_version": rule_version}

        def execute(key: str, request: str) -> dict:
            approval = _approval(approval_ref)
            version = _ident(rule_version, "INVALID_RULE_VERSION")
            reward = self._reward(reward_id_value)
            self._enter(reward, frozenset({ISSUED}))
            _require(not reward["clawback_claim"], "TERMINAL_IMMUTABLE")
            _require(approval["record_id"] not in self._approval_ids, "APPROVAL_RECORD_REUSED")
            _require(version != reward["rule_version"], "RULE_VERSION_UNCHANGED")
            _require(len(reward["payout_effects"]) >= 1, "MOCK_INVARIANT")
            body = {"approval_ref": approval, "rule_version": version}
            self._approval_ids.add(approval["record_id"])
            reward["supersessions"].append(
                {
                    "approval_ref": approval,
                    "prior_rule_version": reward["rule_version"],
                    "rule_version": version,
                }
            )
            reward["rule_version"] = version
            reward["approval_ref"] = approval
            reward["phase"] = ELIGIBLE
            reward["token_outcome"] = "NONE"
            reward["token_effect_id"] = None
            reward["token_effect_closed"] = False
            reward["signed_bytes_digest"] = None
            reward["effects_digest"] = None
            reward["successor_open"] = True
            reward["spend_pool"] = None
            self._invariant(reward)
            return self._accept(key, request, "supersede", reward, body, effect=None)

        return self._call("supersede", reward_id_value, idempotency_key, raw, execute)

    def reject_external(self, kind: object) -> None:
        """Refuse an external execution attempt. This method journals nothing."""

        _ident(kind)
        raise TokenRewardError("EXTERNAL_EXECUTION_UNSUPPORTED")

    def view(self, reward_id_value: object) -> dict:
        return self._view(self._reward(reward_id_value))

    def reward_ids(self) -> list:
        return sorted(self._rewards)

    def pool_view(self) -> dict:
        return self._pools.view()

    def export_journal(self) -> list:
        return _copy(self._journal)

    def canonical_state(self) -> str:
        payload = {
            "journal": self._journal,
            "pools": self._pools.view(),
            "rewards": [self._view(self._rewards[rid]) for rid in sorted(self._rewards)],
        }
        return _canonical(payload)

    def state_digest(self) -> str:
        return _sha256_text(self.canonical_state())

    @classmethod
    def restore(cls, journal: object, *, opening_balances: object) -> RewardMachine:
        _require(type(journal) is list, "INVALID_JOURNAL")
        try:
            journal = _copy(journal)
        except (TypeError, ValueError) as error:
            raise TokenRewardError("INVALID_JOURNAL") from error
        machine = cls(opening_balances)
        for entry in journal:
            _require(type(entry) is dict and set(entry) == _JOURNAL_KEYS, "INVALID_JOURNAL")
            op = entry["op"]
            _require(type(op) is str and op in REPLAYABLE, "INVALID_JOURNAL")
            body = entry["body"]
            _require(type(body) is dict, "INVALID_JOURNAL")
            try:
                if op == "observe":
                    replay_body = dict(body)
                    parsed_key = replay_body.pop("reward_key")
                    expected = reward_id(**_reward_key(parsed_key))
                    _require(entry["reward_id"] == expected, "INVALID_JOURNAL")
                    machine.observe(parsed_key, idempotency_key=entry["idempotency_key"], **replay_body)
                else:
                    _ident(entry["reward_id"])
                    method = getattr(machine, op)
                    method(entry["reward_id"], idempotency_key=entry["idempotency_key"], **body)
            except TypeError as error:
                raise TokenRewardError("INVALID_JOURNAL") from error
        return machine

    def _resend(
        self,
        key: str,
        request: str,
        reward: dict,
        approval: dict,
        digest: str,
        pool: str,
        ceiling: int | None,
        permit: dict | None,
    ) -> dict:
        if permit is None:
            raise TokenRewardError("RESEND_PERMIT_REQUIRED")
        _require(permit["signed_bytes_digest"] == reward["signed_bytes_digest"], "DIGEST_MISMATCH")
        _require(digest == reward["signed_bytes_digest"], "DIGEST_MISMATCH")
        _require(pool == reward["spend_pool"], "SPEND_POOL_CONFLICT")
        if ceiling is not None and reward["amount"] > ceiling:
            raise TokenRewardError("BUDGET_EXCEEDED_PAUSED")
        _require(approval["actor_type"] == "HUMAN", "MOCK_INVARIANT")
        payouts = len(reward["payout_effects"])
        token_effect = reward["token_effect_id"]
        body = {
            "approval_ref": approval,
            "signed_bytes_digest": digest,
            "spend_pool": pool,
            "budget_ceiling": ceiling,
            "execution_permit": permit,
        }
        reward["resend_count"] += 1
        _require(reward["phase"] == UNKNOWN, "MOCK_INVARIANT")
        _require(reward["token_effect_id"] == token_effect, "MOCK_INVARIANT")
        _require(len(reward["payout_effects"]) == payouts, "MOCK_INVARIANT")
        _require(reward["reward_id"] in self._rewards and len(self._rewards) >= 1, "MOCK_INVARIANT")
        self._invariant(reward)
        return self._accept(key, request, "submit", reward, body, effect=None)

    def _apply_outcome(self, reward: dict, effects_digest: str | None, outcome: str) -> dict:
        if outcome == "SUCCESS":
            _require(reward["token_effect_id"] is not None, "MOCK_INVARIANT")
            _require(reward["spend_pool"] in SPENDABLE_POOLS, "POOL_FORBIDDEN_FOR_TOKEN_SPEND")
            self._pools.spend(reward["spend_pool"], reward["amount"], reward["program"])
            already_paid = len(reward["payout_effects"])
            # A success is a supersession only when a supersede record opened
            # this cycle. The first payout has no supersede record yet.
            supersession = len(reward["supersessions"]) > 0 and already_paid == len(reward["supersessions"])
            reward["token_outcome"] = "SUCCESS"
            reward["phase"] = ISSUED
            reward["effects_digest"] = effects_digest
            reward["token_effect_closed"] = True
            effect = {
                "effect_id": reward["token_effect_id"],
                "outcome": "SUCCESS",
                "rule_version": reward["rule_version"],
                "supersession": supersession,
            }
            reward["payout_effects"].append(effect)
            return _copy(effect)
        if outcome == "FAILED":
            reward["token_outcome"] = "FAILED"
            reward["effects_digest"] = effects_digest
            reward["token_effect_closed"] = True
            return {"token_effect_id": reward["token_effect_id"], "outcome": "FAILED"}
        reward["token_outcome"] = "UNKNOWN"
        reward["effects_digest"] = effects_digest
        reward["phase"] = UNKNOWN
        return {"token_effect_id": reward["token_effect_id"], "outcome": "UNKNOWN"}

    def _apply_caps(self, reward: dict, recipient_cap: int | None, program_cap: int | None) -> None:
        if recipient_cap is not None:
            used = self._paid_amount(recipient=reward["recipient"])
            _require(used + reward["amount"] <= 10**12, "INVALID_AMOUNT")
            _require(used + reward["amount"] <= recipient_cap, "CAP_EXHAUSTED_PAUSED")
        if program_cap is not None:
            used = self._paid_amount(program=reward["program"])
            _require(used + reward["amount"] <= 10**12, "INVALID_AMOUNT")
            _require(used + reward["amount"] <= program_cap, "CAP_EXHAUSTED_PAUSED")

    def _paid_amount(self, *, recipient: str | None = None, program: str | None = None) -> int:
        total = 0
        for reward in self._rewards.values():
            if recipient is not None and reward["recipient"] != recipient:
                continue
            if program is not None and reward["program"] != program:
                continue
            total += reward["amount"] * len(reward["payout_effects"])
        _require(total <= 10**12, "MOCK_INVARIANT")
        return total

    def _abuse_kind(self, clear: bool, abuse_kind: object) -> str | None:
        if clear:
            _require(abuse_kind is None, "ABUSE_KIND_UNEXPECTED")
            return None
        _require(type(abuse_kind) is str and abuse_kind in ABUSE_KINDS, "ABUSE_KIND_UNSUPPORTED")
        return abuse_kind

    def _spend_pool_name(self, pool: object) -> str:
        _require(type(pool) is str, "POOL_UNKNOWN")
        _require(pool in {"CUSTOMER_DEPOSIT", "ORGANIZER_SETTLEMENT", "REFUND_RESERVE", "PROTOCOL_REVENUE", "TOKEN_TREASURY_REWARD"}, "POOL_UNKNOWN")
        _require(pool in SPENDABLE_POOLS, "POOL_FORBIDDEN_FOR_TOKEN_SPEND")
        return pool

    def _reward(self, reward_id_value: object) -> dict:
        normalized = _ident(reward_id_value)
        reward = self._rewards.get(normalized)
        _require(reward is not None, "UNKNOWN_REWARD")
        return reward

    def _enter(self, reward: dict, allowed: frozenset) -> None:
        if reward["phase"] in allowed:
            return
        if reward["phase"] in TOKEN_TERMINALS:
            raise TokenRewardError("TERMINAL_IMMUTABLE")
        raise TokenRewardError("ILLEGAL_TRANSITION")

    def _call(self, op: str, subject: object, idempotency_key: object, raw: dict, execute) -> dict:
        key = _ident(idempotency_key)
        request = self._fingerprint(op, subject, raw)
        if request is not None:
            replayed = self._replay_if_known(key, request)
            if replayed is not None:
                return replayed
        try:
            return execute(key, request)
        except TokenRewardError as error:
            if request is not None and error.code not in _UNSTORED_REJECTION and key not in self._idempotency:
                self._idempotency[key] = {"request": request, "result": None, "error": error.code}
            raise

    def _fingerprint(self, op: str, subject: object, body: dict) -> str | None:
        try:
            return _canonical({"body": body, "op": op, "subject": subject})
        except (TypeError, ValueError):
            return None

    def _replay_if_known(self, key: str, request: str) -> dict | None:
        prior = self._idempotency.get(key)
        if prior is None:
            return None
        _require(prior["request"] == request, "IDEMPOTENCY_CONFLICT")
        if prior["error"] is not None:
            raise TokenRewardError(prior["error"])
        result = json.loads(prior["result"])
        result["duplicate"] = True
        result["applied"] = None
        return result

    def _accept(self, key: str, request: str, op: str, reward: dict, body: dict, *, effect: object) -> dict:
        self._journal.append(
            {
                "op": op,
                "idempotency_key": key,
                "reward_id": reward["reward_id"],
                "body": _copy(body),
            }
        )
        result = {
            "duplicate": False,
            "applied": op,
            "effect": effect,
            "provenance": PROVENANCE,
            "lifecycle": LIFECYCLE,
            "external_execution": "UNSUPPORTED",
            "unit": UNIT,
        }
        result.update(_false_flags())
        result["reward"] = self._view(reward)
        self._idempotency[key] = {"request": request, "result": _canonical(result), "error": None}
        return _copy(result)

    def _view(self, reward: dict) -> dict:
        token_ids = [effect["effect_id"] for effect in reward["payout_effects"]]
        current = reward["token_effect_id"]
        if current is not None and current not in token_ids:
            token_ids.append(current)
        view = {
            "provenance": PROVENANCE,
            "lifecycle": LIFECYCLE,
            "unit": UNIT,
            "reward_id": reward["reward_id"],
            "program": reward["program"],
            "source_op_id": reward["source_op_id"],
            "recipient": reward["recipient"],
            "kind": reward["kind"],
            "rule_version": reward["rule_version"],
            "amount": reward["amount"],
            "source_kind": reward["source_kind"],
            "source_view": _copy(reward["source_view"]),
            "phase": reward["phase"],
            "krw_phase": reward["krw_phase"],
            "token_outcome": reward["token_outcome"],
            "token_effect_id": reward["token_effect_id"],
            "krw_effect_id": reward["krw_effect_id"],
            "token_effect_ids": token_ids,
            "payout_effects": _copy(reward["payout_effects"]),
            "payout_effect_count": len(reward["payout_effects"]),
            "signed_bytes_digest": reward["signed_bytes_digest"],
            "effects_digest": reward["effects_digest"],
            "clawback_claim": reward["clawback_claim"],
            "supersessions": _copy(reward["supersessions"]),
            "supersession_count": len(reward["supersessions"]),
            "abuse_clear": reward["abuse_clear"],
            "abuse_kind": reward["abuse_kind"],
            "non_transferable_until_chargeback_end": True,
            "spend_pool": reward["spend_pool"],
            "resend_count": reward["resend_count"],
            "approval_ref": _copy(reward["approval_ref"]) if reward["approval_ref"] is not None else None,
            "accepted_entries": sum(1 for entry in self._journal if entry["reward_id"] == reward["reward_id"]),
        }
        view.update(_false_flags())
        return view

    def _invariant(self, reward: dict) -> None:
        _require(reward["phase"] in TOKEN_PHASES, "MOCK_INVARIANT")
        _require(reward["krw_phase"] in KRW_PHASES, "MOCK_INVARIANT")
        _require(reward["non_transferable_until_chargeback_end"] is True, "MOCK_INVARIANT")
        _require(reward["clawback_claim"] is (reward["phase"] == CLAWBACK_CLAIM), "MOCK_INVARIANT")
        _require(reward["krw_effect_id"] != reward["token_effect_id"], "MOCK_INVARIANT")
        _require(all(effect["outcome"] == "SUCCESS" for effect in reward["payout_effects"]), "MOCK_INVARIANT")
        for name in ALWAYS_FALSE_FLAGS:
            _require(self._view(reward)[name] is False, "MOCK_INVARIANT")
        self._pools.view()
