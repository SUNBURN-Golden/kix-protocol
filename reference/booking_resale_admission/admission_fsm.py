"""In-memory acceptance machine for admission credential checks.

The machine decides which issued ticket may be authorized and consumed, then
replays that journal deterministically. Slot, price, and one-time consume
predicates stay in mock_gates.py. Reservation and resale commands stay on
their own machines. This module does not add protocol_contract commands.

A bound ticket source is re-read at authorize and consume. When that check
passes, the same command is also applied to the reservation machine so a
later resale read sees ADMISSION_LOCKED or ALREADY_CONSUMED. A bound
ownership source is read only. A transfer or a live listing invalidates the
presented credential. This machine does not reissue a venue credential.

An external venue-identity or revocation source is never treated as an allow.
If one is configured, or a command names that dependency, the command fails
closed and does not consume. `admission_routing_production` stays false.

Provenance remains MOCK_GATE_ONLY. A matched replay is equality of this
process's journal and local views, not a venue scan, offline trust, or chain
finality. Scanner races here are ordered commands in one process.
"""

from __future__ import annotations

import hashlib
import json

from mock_gates import (
    CAPACITY_MAX,
    GATE_ROLE_LIMIT,
    NON_CLAIMS,
    PROVENANCE,
    GateError,
    MockGates,
    _bps,
    _canonical,
    _hex32,
    _ident,
    _money,
    _ms,
    _version,
)

AUTHORITY = "IN_MEMORY_FSM"

ELIGIBLE = "ELIGIBLE"
AUTHORIZED = "AUTHORIZED"
CONSUMED = "CONSUMED"

ISSUED_PHASES = frozenset({"ISSUED", "ADMISSION_AUTHORIZED"})
FRESH_PHASES = frozenset({"ISSUED", "ADMISSION_AUTHORIZED", "CONSUMED"})

REPLAYABLE = frozenset(
    {
        "set_clock",
        "adopt_issued",
        "authorize_admission",
        "consume",
    }
)

_JOURNAL_KEYS = frozenset({"op", "idempotency_key", "subject_id", "body"})
_UNSTORED_REJECTION = frozenset({"MOCK_INVARIANT", "IDEMPOTENCY_CONFLICT", "INVALID_JOURNAL"})
_SETTLEMENT_FLAGS = (
    "funds_executed",
    "admission_granted",
    "bank_debit_observed",
    "legal_debtor_bound",
    "durable",
    "external_return_closed",
    "right_cancelled",
)
_ADOPT_FIELDS = (
    "show_id",
    "organizer_role",
    "capacity",
    "gate_roles",
    "primary_price",
    "resale_cap",
    "resale_allowed",
    "organizer_bps",
    "platform_bps",
    "reservation_id",
    "slot",
    "buyer_role",
    "expires_ms",
    "order_id",
    "amount",
    "quote_ref",
    "payment_ref",
)
_SHOW_FIELDS = (
    "organizer_role",
    "capacity",
    "primary_price",
    "resale_cap",
    "resale_allowed",
    "organizer_bps",
    "platform_bps",
)


class AdmissionError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise AdmissionError(code)


def _lift(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except GateError as error:
        raise AdmissionError(error.code) from error


def _id(value: object, code: str = "INVALID_ID") -> str:
    try:
        return _ident(value, code)
    except GateError as error:
        raise AdmissionError(error.code) from error


def _copy(value: object) -> object:
    return json.loads(_lift(_canonical, value))


def _remote(fn, *args, unavailable: str, **kwargs):
    try:
        return fn(*args, **kwargs)
    except AdmissionError:
        raise
    except Exception as error:
        code = getattr(error, "code", None)
        if type(code) is str and code:
            raise AdmissionError(code) from error
        raise AdmissionError(unavailable) from error


class AdmissionMachine:
    def __init__(
        self,
        ticket_source: object | None = None,
        ownership_source: object | None = None,
        settlement_source: object | None = None,
        venue_source: object | None = None,
        revocation_source: object | None = None,
    ) -> None:
        self._gates = MockGates()
        self._tickets = ticket_source
        self._ownership = ownership_source
        self._settlement = settlement_source
        self._venue = venue_source
        self._revocation = revocation_source
        self._now = 0
        self._journal: list[dict] = []
        self._idempotency: dict[str, dict] = {}
        self._credentials: dict[str, dict] = {}
        self._admissions: dict[str, str] = {}
        self._consumes: dict[str, str] = {}
        self._replaying = False

    def set_clock(self, subject_id: object, *, idempotency_key: object, now_ms: object) -> dict:
        raw = {"now_ms": now_ms}

        def execute(key: str, request: str) -> dict:
            _require(subject_id == "clock", "INVALID_ID")
            now = _lift(_ms, now_ms, "CLOCK")
            if self._tickets is not None:
                try:
                    _remote(
                        self._tickets.set_clock,
                        "clock",
                        unavailable="TICKET_SOURCE_UNAVAILABLE",
                        idempotency_key=key,
                        now_ms=now,
                    )
                except AdmissionError as error:
                    if not (self._replaying and error.code == "CLOCK_REGRESSION"):
                        raise
            result = _lift(self._gates.set_clock, now)
            _require(result["logical_time_ms"] == now, "MOCK_INVARIANT")
            self._now = now
            self._invariant()
            return self._accept(key, request, "set_clock", "clock", {"now_ms": now})

        return self._call("set_clock", subject_id, idempotency_key, raw, execute)

    def adopt_issued(
        self,
        right_id: object,
        *,
        idempotency_key: object,
        show_id: object,
        organizer_role: object,
        capacity: object,
        gate_roles: object,
        primary_price: object,
        resale_cap: object,
        resale_allowed: object,
        organizer_bps: object,
        platform_bps: object,
        slot: object,
        buyer_role: object,
        expires_ms: object,
        order_id: object,
        amount: object,
        payment_ref: object,
        reservation_id: object = None,
        quote_ref: object = None,
    ) -> dict:
        raw = {
            "show_id": show_id,
            "organizer_role": organizer_role,
            "capacity": capacity,
            "gate_roles": gate_roles,
            "primary_price": primary_price,
            "resale_cap": resale_cap,
            "resale_allowed": resale_allowed,
            "organizer_bps": organizer_bps,
            "platform_bps": platform_bps,
            "reservation_id": reservation_id,
            "slot": slot,
            "buyer_role": buyer_role,
            "expires_ms": expires_ms,
            "order_id": order_id,
            "amount": amount,
            "quote_ref": quote_ref,
            "payment_ref": payment_ref,
        }

        def execute(key: str, request: str) -> dict:
            normalized = self._normalize_adopt(right_id, raw)
            canon = _lift(_canonical, normalized | {"right_id": normalized["right_id"]})
            current = self._credentials.get(normalized["right_id"])
            if current is not None:
                _require(current["canon"] == canon, "ISSUANCE_BINDING_CONFLICT")
                raise AdmissionError("ILLEGAL_TRANSITION")
            self._match_issued(normalized)
            self._materialize(normalized)
            credential = {
                "canon": canon,
                "right_id": normalized["right_id"],
                "reservation_id": normalized["reservation_id"],
                "show_id": normalized["show_id"],
                "slot": normalized["slot"],
                "holder_role": normalized["buyer_role"],
                "phase": ELIGIBLE,
                "admission_id": None,
                "admission_expires_ms": None,
                "gate_role": None,
                "request": None,
                "consume_id": None,
                "version_after": None,
                "subject_ids": [normalized["right_id"]],
            }
            self._credentials[normalized["right_id"]] = credential
            self._invariant()
            body = {name: normalized[name] for name in _ADOPT_FIELDS}
            return self._accept(
                key,
                request,
                "adopt_issued",
                normalized["right_id"],
                body,
                credential=credential,
            )

        return self._call("adopt_issued", right_id, idempotency_key, raw, execute)

    def authorize_admission(
        self,
        admission_id: object,
        *,
        idempotency_key: object,
        right_id: object,
        version: object,
        holder_role: object,
        gate_role: object,
        request: object,
        expires_ms: object,
        external_dependency: object = None,
    ) -> dict:
        raw = {
            "right_id": right_id,
            "version": version,
            "holder_role": holder_role,
            "gate_role": gate_role,
            "request": request,
            "expires_ms": expires_ms,
            "external_dependency": external_dependency,
        }

        def execute(key: str, request_fp: str) -> dict:
            normalized_admission = _id(admission_id)
            right = _id(right_id)
            holder = _id(holder_role)
            gate = _id(gate_role)
            ticket = _lift(_hex32, request, "ADMISSION_REQUEST")
            expires = _lift(_ms, expires_ms, "ADMISSION_WINDOW")
            current_version = _lift(_version, version)
            dependency = self._external_label(external_dependency)
            binding = {
                "admission_id": normalized_admission,
                "right_id": right,
                "version": current_version,
                "holder_role": holder,
                "gate_role": gate,
                "request": ticket,
                "expires_ms": expires,
            }
            canon = _lift(_canonical, binding)
            prior = self._admissions.get(normalized_admission)
            if prior is not None:
                _require(prior == canon, "ADMISSION_BINDING_CONFLICT")
                raise AdmissionError("ILLEGAL_TRANSITION")
            credential = self._credential(right)
            self._assert_external(dependency)
            self._assert_ownership(right, current_version, holder, "authorize_admission")
            self._assert_reservation(credential, current_version, holder, "authorize_admission")
            self._assert_settlement(credential)
            self._delegate_authorize(
                normalized_admission,
                key,
                right,
                current_version,
                holder,
                gate,
                ticket,
                expires,
            )
            result = _lift(
                self._gates.authorize_admission,
                normalized_admission,
                right_id=right,
                version=current_version,
                holder_role=holder,
                gate_role=gate,
                request=ticket,
                expires_ms=expires,
            )
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            _require(result["admission"]["state"] == "AUTHORIZED", "MOCK_INVARIANT")
            credential["admission_id"] = normalized_admission
            credential["admission_expires_ms"] = expires
            credential["gate_role"] = gate
            credential["request"] = ticket
            credential["phase"] = AUTHORIZED
            self._admissions[normalized_admission] = canon
            self._invariant()
            return self._accept(
                key,
                request_fp,
                "authorize_admission",
                normalized_admission,
                {
                    "right_id": right,
                    "version": current_version,
                    "holder_role": holder,
                    "gate_role": gate,
                    "request": ticket,
                    "expires_ms": expires,
                    "external_dependency": dependency,
                },
                credential=credential,
                admission=dict(result["admission"]),
            )

        return self._call("authorize_admission", admission_id, idempotency_key, raw, execute)

    def consume(
        self,
        consume_id: object,
        *,
        idempotency_key: object,
        right_id: object,
        version: object,
        gate_role: object,
        request: object,
        external_dependency: object = None,
    ) -> dict:
        raw = {
            "right_id": right_id,
            "version": version,
            "gate_role": gate_role,
            "request": request,
            "external_dependency": external_dependency,
        }

        def execute(key: str, request_fp: str) -> dict:
            normalized_consume = _id(consume_id)
            right = _id(right_id)
            gate = _id(gate_role)
            ticket = _lift(_hex32, request, "ADMISSION_REQUEST")
            current_version = _lift(_version, version)
            dependency = self._external_label(external_dependency)
            canon = _lift(
                _canonical,
                {
                    "consume_id": normalized_consume,
                    "right_id": right,
                    "version": current_version,
                    "gate_role": gate,
                    "request": ticket,
                },
            )
            prior = self._consumes.get(normalized_consume)
            if prior is not None:
                _require(prior == canon, "CONSUME_BINDING_CONFLICT")
                raise AdmissionError("ILLEGAL_TRANSITION")
            credential = self._credential(right)
            holder = credential["holder_role"]
            self._assert_external(dependency)
            self._assert_ownership(right, current_version, holder, "consume")
            self._assert_reservation(credential, current_version, holder, "consume")
            self._assert_settlement(credential)
            self._delegate_consume(
                normalized_consume,
                key,
                right,
                current_version,
                gate,
                ticket,
            )
            result = _lift(
                self._gates.consume_admission,
                normalized_consume,
                right_id=right,
                version=current_version,
                gate_role=gate,
                request=ticket,
            )
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            evidence = dict(result["evidence"])
            _require(evidence["decision"] == "CONSUMED_ONCE", "MOCK_INVARIANT")
            _require(evidence["private_proof_verified"] is False, "MOCK_INVARIANT")
            _require(evidence["admission_routing_production"] is False, "MOCK_INVARIANT")
            credential["consume_id"] = normalized_consume
            credential["admission_id"] = None
            credential["admission_expires_ms"] = None
            credential["version_after"] = evidence["version_after"]
            credential["phase"] = CONSUMED
            self._consumes[normalized_consume] = canon
            self._invariant()
            if self._tickets is not None and not self._replaying:
                remote = self._reservation_view(credential["reservation_id"])
                _require(remote.get("phase") == CONSUMED, "MOCK_INVARIANT")
                _require(remote.get("right", {}).get("version") == evidence["version_after"], "MOCK_INVARIANT")
            return self._accept(
                key,
                request_fp,
                "consume",
                normalized_consume,
                {
                    "right_id": right,
                    "version": current_version,
                    "gate_role": gate,
                    "request": ticket,
                    "external_dependency": dependency,
                },
                credential=credential,
                evidence=evidence,
            )

        return self._call("consume", consume_id, idempotency_key, raw, execute)

    def reconcile(self, right_id: object, *, idempotency_key: object) -> dict:
        """Replay the journal and require the local views to match.

        Bound sources are read again. A later transfer or an unavailable
        external source fails closed. The receipt is not part of the journal.
        """

        def execute(key: str, request: str) -> dict:
            normalized = _id(right_id)
            self._credential(normalized)
            restored = AdmissionMachine.restore(
                self.export_journal(),
                ticket_source=self._tickets,
                ownership_source=self._ownership,
                settlement_source=self._settlement,
                venue_source=self._venue,
                revocation_source=self._revocation,
            )
            _require(restored.canonical_state() == self.canonical_state(), "MOCK_INVARIANT")
            result = self._envelope(
                applied="reconcile",
                credential=self._credential_view(self._credential(normalized)),
                matched=True,
                state_digest=self.state_digest(),
                entry_count=len(self._journal),
            )
            self._idempotency[key] = {"request": request, "result": _canonical(result), "error": None}
            return json.loads(_canonical(result))

        return self._call("reconcile", right_id, idempotency_key, {}, execute)

    def reject_external(self, kind: object) -> None:
        """Refuse a venue scanner, offline admit, public bind, or live issuer.

        The kind is an external-attempt label. This method never authorizes
        or consumes a credential.
        """

        _id(kind)
        raise AdmissionError("EXTERNAL_UNSUPPORTED")

    def view(self, right_id: object) -> dict:
        return self._credential_view(self._credential(_id(right_id)))

    def view_credential(self, right_id: object, *, version: object, holder_role: object) -> dict:
        """Report whether this presentation is fresh. Does not admit.

        `fresh` is false when the bound lifecycle or an external dependency
        would refuse entry. That is not an offline allow and not a venue scan.
        """

        normalized = _id(right_id)
        holder = _id(holder_role)
        current_version = _lift(_version, version)
        credential = self._credential(normalized)
        decision = None
        fresh = True
        try:
            self._assert_external(None)
            self._assert_ownership(normalized, current_version, holder, "authorize_admission")
            self._assert_reservation(credential, current_version, holder, "authorize_admission")
            self._assert_settlement(credential)
        except AdmissionError as error:
            fresh = False
            decision = error.code
        body = {
            "right_id": normalized,
            "version": current_version,
            "holder_role": holder,
            "fresh": fresh,
            "decision": decision,
            "offline_admission": False,
            "venue_credential_reissued": False,
            "admission_routing_production": False,
            "external_admission": "UNSUPPORTED",
        }
        return self._envelope(applied="view_credential", credential=self._credential_view(credential), presentation=body)

    def export_journal(self) -> list:
        return _copy(self._journal)

    def canonical_state(self) -> str:
        payload = {
            "logical_time_ms": self._now,
            "credentials": [self._credential_view(self._credentials[right_id]) for right_id in sorted(self._credentials)],
            "journal": self._journal,
        }
        return _lift(_canonical, payload)

    def state_digest(self) -> str:
        return hashlib.sha256(self.canonical_state().encode("utf-8")).hexdigest()

    @classmethod
    def restore(
        cls,
        journal: object,
        ticket_source: object | None = None,
        ownership_source: object | None = None,
        settlement_source: object | None = None,
        venue_source: object | None = None,
        revocation_source: object | None = None,
    ) -> AdmissionMachine:
        _require(type(journal) is list, "INVALID_JOURNAL")
        machine = cls(
            ticket_source,
            ownership_source,
            settlement_source,
            venue_source=venue_source,
            revocation_source=revocation_source,
        )
        machine._replaying = True
        try:
            for entry in journal:
                _require(type(entry) is dict and set(entry) == _JOURNAL_KEYS, "INVALID_JOURNAL")
                op = entry["op"]
                _require(type(op) is str and op in REPLAYABLE, "INVALID_JOURNAL")
                body = entry["body"]
                _require(type(body) is dict, "INVALID_JOURNAL")
                method = getattr(machine, op)
                try:
                    method(entry["subject_id"], idempotency_key=entry["idempotency_key"], **body)
                except TypeError as error:
                    raise AdmissionError("INVALID_JOURNAL") from error
        finally:
            machine._replaying = False
        return machine

    def _normalize_adopt(self, right_id: object, raw: dict) -> dict:
        normalized = {
            "right_id": _id(right_id),
            "show_id": _id(raw["show_id"]),
            "organizer_role": _id(raw["organizer_role"]),
            "reservation_id": None if raw["reservation_id"] is None else _id(raw["reservation_id"]),
            "buyer_role": _id(raw["buyer_role"]),
            "order_id": _id(raw["order_id"]),
            "quote_ref": None if raw["quote_ref"] is None else _id(raw["quote_ref"]),
            "primary_price": _lift(_money, raw["primary_price"]),
            "resale_cap": _lift(_money, raw["resale_cap"]),
            "amount": _lift(_money, raw["amount"]),
            "expires_ms": _lift(_ms, raw["expires_ms"], "RESERVATION_WINDOW"),
            "payment_ref": _lift(_hex32, raw["payment_ref"], "PAYMENT_REF"),
        }
        _require(type(raw["capacity"]) is int and 1 <= raw["capacity"] <= CAPACITY_MAX, "CAPACITY")
        _require(type(raw["gate_roles"]) is list, "GATES_TYPE")
        _require(len(raw["gate_roles"]) > 0, "GATES_EMPTY")
        _require(len(raw["gate_roles"]) <= GATE_ROLE_LIMIT, "GATES_LIMIT")
        gates = [_id(item) for item in raw["gate_roles"]]
        _require(len(set(gates)) == len(gates), "GATES_DUPLICATE")
        _require(type(raw["resale_allowed"]) is bool, "POLICY_FLAG")
        _require(type(raw["slot"]) is int, "SLOT")
        organizer_bps = _lift(_bps, raw["organizer_bps"])
        platform_bps = _lift(_bps, raw["platform_bps"])
        _require(organizer_bps + platform_bps <= 10000, "BPS_SUM")
        _require(normalized["amount"] == normalized["primary_price"], "PRIMARY_PRICE_MISMATCH")
        if normalized["reservation_id"] is None and self._tickets is not None:
            raise AdmissionError("TICKET_NOT_ISSUED")
        if normalized["reservation_id"] is not None and self._tickets is None:
            raise AdmissionError("TICKET_SOURCE_REQUIRED")
        normalized["capacity"] = raw["capacity"]
        normalized["gate_roles"] = gates
        normalized["resale_allowed"] = raw["resale_allowed"]
        normalized["organizer_bps"] = organizer_bps
        normalized["platform_bps"] = platform_bps
        normalized["slot"] = raw["slot"]
        return normalized

    def _materialize(self, normalized: dict) -> None:
        local_reservation = normalized["reservation_id"] if normalized["reservation_id"] is not None else normalized["right_id"]
        opened = _lift(
            self._gates.register_show,
            normalized["show_id"],
            organizer_role=normalized["organizer_role"],
            capacity=normalized["capacity"],
            gate_roles=normalized["gate_roles"],
            primary_price=normalized["primary_price"],
            resale_cap=normalized["resale_cap"],
            resale_allowed=normalized["resale_allowed"],
            organizer_bps=normalized["organizer_bps"],
            platform_bps=normalized["platform_bps"],
        )
        _require(opened["show"]["show_id"] == normalized["show_id"], "MOCK_INVARIANT")
        reserved = _lift(
            self._gates.reserve_slot,
            local_reservation,
            show_id=normalized["show_id"],
            slot=normalized["slot"],
            buyer_role=normalized["buyer_role"],
            expires_ms=normalized["expires_ms"],
        )
        _require(reserved["duplicate"] is False, "MOCK_INVARIANT")
        ordered = _lift(
            self._gates.bind_order,
            normalized["order_id"],
            reservation_id=local_reservation,
            amount=normalized["amount"],
            quote_ref=normalized["quote_ref"],
        )
        _require(ordered["duplicate"] is False, "MOCK_INVARIANT")
        paid = _lift(
            self._gates.observe_payment_fact,
            normalized["payment_ref"],
            order_id=normalized["order_id"],
            amount=normalized["amount"],
        )
        _require(paid["duplicate"] is False, "MOCK_INVARIANT")
        issued = _lift(self._gates.issue, normalized["right_id"], order_id=normalized["order_id"])
        _require(issued["duplicate"] is False, "MOCK_INVARIANT")
        evidence = issued["evidence"]
        right = issued["right"]
        _require(evidence["kind"] == 1 and evidence["chain_issued"] is False, "MOCK_INVARIANT")
        _require("seller_due" not in evidence, "MOCK_INVARIANT")
        _require(right["state"] == "ACTIVE" and right["version"] == 1 and right["generation"] == 1, "MOCK_INVARIANT")
        _require(right["holder_role"] == normalized["buyer_role"], "MOCK_INVARIANT")
        _require(right["listing_id"] is None and right["admission_id"] is None, "MOCK_INVARIANT")

    def _match_issued(self, normalized: dict) -> None:
        if normalized["reservation_id"] is None:
            return
        view = self._reservation_view(normalized["reservation_id"])
        phase = view.get("phase")
        right = view.get("right")
        advanced = self._replaying and phase in ("ADMISSION_AUTHORIZED", "CONSUMED")
        if phase == "CANCELLED":
            raise AdmissionError("TICKET_CANCELLED")
        if not advanced:
            if phase == "CONSUMED" or (type(right) is dict and right.get("state") == "CONSUMED"):
                raise AdmissionError("ALREADY_CONSUMED")
            if phase != "ISSUED":
                raise AdmissionError("TICKET_NOT_ISSUED")
            if view.get("admission_id") is not None:
                raise AdmissionError("ADMISSION_LOCKED")
            _require(type(right) is dict and right.get("state") == "ACTIVE", "RIGHT_NOT_ACTIVE")
            _require(right.get("version") == 1, "STALE_VERSION")
        else:
            _require(phase in FRESH_PHASES, "TICKET_NOT_ISSUED")
            _require(type(right) is dict, "TICKET_NOT_ISSUED")
        _require(view.get("issuance_id") == normalized["right_id"], "UNKNOWN_RIGHT")
        _require(right.get("right_id") == normalized["right_id"], "UNKNOWN_RIGHT")
        _require(view.get("buyer_role") == normalized["buyer_role"], "NOT_HOLDER")
        _require(right.get("holder_role") == normalized["buyer_role"], "NOT_HOLDER")
        _require(view.get("show_id") == normalized["show_id"], "SHOW_BINDING_CONFLICT")
        _require(view.get("slot") == normalized["slot"], "RESERVATION_BINDING_CONFLICT")
        _require(view.get("expires_ms") == normalized["expires_ms"], "RESERVATION_BINDING_CONFLICT")
        _require(view.get("order_id") == normalized["order_id"], "ORDER_BINDING_CONFLICT")
        _require(view.get("amount") == normalized["amount"], "PRIMARY_PRICE_MISMATCH")
        _require(view.get("quote_ref") == normalized["quote_ref"], "ORDER_BINDING_CONFLICT")
        _require(view.get("payment_ref") == normalized["payment_ref"], "PAYMENT_BINDING_CONFLICT")
        _require(view.get("economic_finality_claimed") is False, "SETTLEMENT_VIEW_REJECTED")
        _require(view.get("funds_executed") is False, "SETTLEMENT_VIEW_REJECTED")
        _require(view.get("admission_routing_production") is False, "MOCK_INVARIANT")
        show = _remote(self._tickets.view_show, normalized["show_id"], unavailable="TICKET_SOURCE_UNAVAILABLE")
        _require(type(show) is dict and type(show.get("show")) is dict, "UNKNOWN_SHOW")
        snapshot = show["show"]
        for name in _SHOW_FIELDS:
            _require(snapshot.get(name) == normalized[name], "SHOW_BINDING_CONFLICT")
        _require(list(snapshot.get("gate_roles") or []) == normalized["gate_roles"], "SHOW_BINDING_CONFLICT")

    def _assert_external(self, dependency: str | None) -> None:
        if self._venue is not None:
            raise AdmissionError("VENUE_SOURCE_UNAVAILABLE")
        if self._revocation is not None:
            raise AdmissionError("REVOCATION_SOURCE_UNAVAILABLE")
        if dependency == "VENUE_IDENTITY":
            raise AdmissionError("VENUE_SOURCE_UNAVAILABLE")
        if dependency == "REVOCATION":
            raise AdmissionError("REVOCATION_SOURCE_UNAVAILABLE")
        if dependency is not None:
            raise AdmissionError("EXTERNAL_UNSUPPORTED")

    def _external_label(self, value: object) -> str | None:
        if value is None:
            return None
        if type(value) is not str:
            raise AdmissionError("EXTERNAL_UNSUPPORTED")
        return _id(value)

    def _assert_ownership(self, right_id: str, version: int, holder: str, command: str) -> None:
        if self._ownership is None:
            return
        viewed = self._ownership_view(right_id)
        if viewed is None:
            return
        right = viewed.get("right") if type(viewed) is dict else None
        if type(right) is not dict:
            raise AdmissionError("OWNERSHIP_SOURCE_UNAVAILABLE")
        if right.get("state") == "CONSUMED":
            raise AdmissionError("ALREADY_CONSUMED")
        if right.get("state") != "ACTIVE":
            raise AdmissionError("RIGHT_NOT_ACTIVE")
        if right.get("version") != version:
            raise AdmissionError("STALE_VERSION")
        if right.get("holder_role") != holder:
            raise AdmissionError("NOT_HOLDER")
        if right.get("listing_id") is not None:
            raise AdmissionError("LISTING_LOCKED")
        presentation = _remote(
            self._ownership.view_presentation,
            right_id,
            unavailable="OWNERSHIP_SOURCE_UNAVAILABLE",
            version=version,
            holder_role=holder,
        )
        row = presentation.get("presentation") if type(presentation) is dict else None
        if type(row) is not dict or row.get("matches_current_right") is not True:
            raise AdmissionError("CREDENTIAL_STALE")
        if row.get("venue_credential_reissued") is not False or row.get("admission_routing_production") is not False:
            raise AdmissionError("CREDENTIAL_STALE")
        if command not in ("authorize_admission", "consume"):
            raise AdmissionError("MOCK_INVARIANT")

    def _assert_reservation(self, credential: dict, version: int, holder: str, command: str) -> None:
        if credential["reservation_id"] is None:
            return
        view = self._reservation_view(credential["reservation_id"])
        phase = view.get("phase")
        right = view.get("right") if type(view.get("right")) is dict else None
        if phase == "CANCELLED":
            raise AdmissionError("TICKET_CANCELLED")
        if phase == "CONSUMED" or (right is not None and right.get("state") == "CONSUMED"):
            if self._replaying:
                return
            if command == "consume":
                raise AdmissionError("ALREADY_CONSUMED")
            raise AdmissionError("RIGHT_NOT_ACTIVE")
        if phase not in ISSUED_PHASES:
            raise AdmissionError("TICKET_NOT_ISSUED")
        if right is None or right.get("state") != "ACTIVE":
            raise AdmissionError("RIGHT_NOT_ACTIVE")
        if right.get("version") != version:
            raise AdmissionError("STALE_VERSION")
        if right.get("holder_role") != holder:
            raise AdmissionError("NOT_HOLDER")
        if view.get("economic_finality_claimed") is not False or view.get("funds_executed") is not False:
            raise AdmissionError("SETTLEMENT_VIEW_REJECTED")

    def _assert_settlement(self, credential: dict) -> None:
        if credential["reservation_id"] is None or self._tickets is None:
            return
        view = self._reservation_view(credential["reservation_id"])
        settlement_id = view.get("settlement_id")
        if settlement_id is None:
            return
        if self._settlement is None:
            raise AdmissionError("SETTLEMENT_SOURCE_REQUIRED")
        settlement = _remote(self._settlement.view, settlement_id, unavailable="SETTLEMENT_SOURCE_UNAVAILABLE")
        if type(settlement) is not dict:
            raise AdmissionError("SETTLEMENT_SOURCE_UNAVAILABLE")
        for name in _SETTLEMENT_FLAGS:
            if settlement.get(name) is not False:
                raise AdmissionError("SETTLEMENT_VIEW_REJECTED")

    def _delegate_authorize(
        self,
        admission_id: str,
        key: str,
        right_id: str,
        version: int,
        holder: str,
        gate: str,
        request: str,
        expires_ms: int,
    ) -> None:
        if self._tickets is None:
            return
        result = _remote(
            self._tickets.authorize_admission,
            admission_id,
            unavailable="TICKET_SOURCE_UNAVAILABLE",
            idempotency_key=key,
            right_id=right_id,
            version=version,
            holder_role=holder,
            gate_role=gate,
            request=request,
            expires_ms=expires_ms,
        )
        if result.get("duplicate") and not self._replaying:
            raise AdmissionError("MOCK_INVARIANT")
        if not self._replaying:
            _require(result.get("reservation", {}).get("phase") == "ADMISSION_AUTHORIZED", "MOCK_INVARIANT")
            _require(result.get("reservation", {}).get("admission_routing_production") is False, "MOCK_INVARIANT")

    def _delegate_consume(
        self,
        consume_id: str,
        key: str,
        right_id: str,
        version: int,
        gate: str,
        request: str,
    ) -> None:
        if self._tickets is None:
            return
        result = _remote(
            self._tickets.consume,
            consume_id,
            unavailable="TICKET_SOURCE_UNAVAILABLE",
            idempotency_key=key,
            right_id=right_id,
            version=version,
            gate_role=gate,
            request=request,
        )
        if result.get("duplicate") and not self._replaying:
            raise AdmissionError("MOCK_INVARIANT")
        evidence = result.get("evidence") if type(result) is dict else None
        if not self._replaying:
            _require(type(evidence) is dict and evidence.get("decision") == "CONSUMED_ONCE", "MOCK_INVARIANT")
            _require(evidence.get("admission_routing_production") is False, "MOCK_INVARIANT")

    def _ownership_view(self, right_id: str) -> dict | None:
        try:
            viewed = self._ownership.view_right(right_id)
        except Exception as error:
            code = getattr(error, "code", None)
            if code == "UNKNOWN_RIGHT":
                return None
            if type(code) is str and code:
                raise AdmissionError(code) from error
            raise AdmissionError("OWNERSHIP_SOURCE_UNAVAILABLE") from error
        if type(viewed) is not dict:
            raise AdmissionError("OWNERSHIP_SOURCE_UNAVAILABLE")
        return viewed

    def _reservation_view(self, reservation_id: str) -> dict:
        view = _remote(self._tickets.view, reservation_id, unavailable="TICKET_SOURCE_UNAVAILABLE")
        if type(view) is not dict:
            raise AdmissionError("TICKET_SOURCE_UNAVAILABLE")
        return view

    def _credential(self, right_id: str) -> dict:
        credential = self._credentials.get(right_id)
        _require(credential is not None, "UNKNOWN_RIGHT")
        return credential

    def _call(self, op: str, subject_id: object, idempotency_key: object, raw: dict, execute) -> dict:
        key = _id(idempotency_key)
        request = self._fingerprint(op, subject_id, raw)
        if request is not None:
            replayed = self._replay_if_known(key, request)
            if replayed is not None:
                return replayed
        try:
            return execute(key, request)
        except AdmissionError as error:
            if (
                request is not None
                and error.code not in _UNSTORED_REJECTION
                and key not in self._idempotency
            ):
                self._idempotency[key] = {"request": request, "result": None, "error": error.code}
            raise

    def _fingerprint(self, op: str, subject_id: object, body: dict) -> str | None:
        try:
            return _canonical({"body": body, "op": op, "subject_id": subject_id})
        except (TypeError, ValueError):
            return None

    def _replay_if_known(self, key: str, request: str) -> dict | None:
        prior = self._idempotency.get(key)
        if prior is None:
            return None
        _require(prior["request"] == request, "IDEMPOTENCY_CONFLICT")
        if prior["error"] is not None:
            raise AdmissionError(prior["error"])
        result = json.loads(prior["result"])
        result["duplicate"] = True
        result["applied"] = None
        self._force_non_claims(result)
        return result

    def _accept(
        self,
        key: str,
        request: str,
        op: str,
        subject_id: str,
        body: dict,
        *,
        credential: dict | None = None,
        **extra: object,
    ) -> dict:
        _require(request is not None, "MOCK_INVARIANT")
        self._journal.append(
            {
                "op": op,
                "idempotency_key": key,
                "subject_id": subject_id,
                "body": _copy(body),
            }
        )
        if credential is not None and subject_id not in credential["subject_ids"]:
            credential["subject_ids"].append(subject_id)
        if credential is not None:
            extra["credential"] = self._credential_view(credential)
            extra["right"] = self._local_right(credential["right_id"])
        result = self._envelope(applied=op, **extra)
        self._idempotency[key] = {"request": request, "result": _lift(_canonical, result), "error": None}
        return _copy(result)

    def _force_non_claims(self, result: dict) -> None:
        result["economic_finality_claimed"] = False
        result["funds_executed"] = False
        result["venue_credential_reissued"] = False
        result["offline_admission"] = False
        result["external_admission"] = "UNSUPPORTED"
        result["admission_routing_production"] = False
        for name in ("credential", "presentation"):
            body = result.get(name)
            if type(body) is dict:
                body["economic_finality_claimed"] = False
                body["funds_executed"] = False
                body["venue_credential_reissued"] = False
                body["offline_admission"] = False
                body["admission_routing_production"] = False
        evidence = result.get("evidence")
        if type(evidence) is dict:
            evidence["admission_routing_production"] = False
            evidence["private_proof_verified"] = False

    def _envelope(self, *, applied: str, **extra: object) -> dict:
        body = {
            "provenance": PROVENANCE,
            "lifecycle_authority": AUTHORITY,
            "duplicate": False,
            "applied": applied,
            "logical_time_ms": self._now,
            "external_admission": "UNSUPPORTED",
            "external_payment": "UNSUPPORTED",
            "offline_admission": False,
            "venue_credential_reissued": False,
            "economic_finality_claimed": False,
        }
        body.update(NON_CLAIMS)
        body.update(extra)
        body["provenance"] = PROVENANCE
        body["lifecycle_authority"] = AUTHORITY
        body["duplicate"] = False
        body["applied"] = applied
        body["economic_finality_claimed"] = False
        body["funds_executed"] = False
        body["venue_credential_reissued"] = False
        body["offline_admission"] = False
        body["external_admission"] = "UNSUPPORTED"
        body["external_payment"] = "UNSUPPORTED"
        body["admission_routing_production"] = False
        return body

    def _local_right(self, right_id: str) -> dict:
        body = _lift(self._gates.view_right, right_id)
        _require(body["logical_time_ms"] == self._now, "MOCK_INVARIANT")
        return body["right"]

    def _local_show(self, show_id: str) -> dict:
        body = _lift(self._gates.view_show, show_id)
        _require(body["logical_time_ms"] == self._now, "MOCK_INVARIANT")
        return body["show"]

    def _credential_view(self, credential: dict) -> dict:
        right = self._local_right(credential["right_id"])
        show = self._local_show(credential["show_id"])
        slot = None
        for row in show["slots"]:
            if row["slot"] == credential["slot"]:
                slot = row
                break
        _require(slot is not None, "MOCK_INVARIANT")
        expired = (
            credential["phase"] == AUTHORIZED
            and credential["admission_expires_ms"] is not None
            and self._now >= credential["admission_expires_ms"]
        )
        view = {
            "provenance": PROVENANCE,
            "lifecycle_authority": AUTHORITY,
            "right_id": credential["right_id"],
            "reservation_id": credential["reservation_id"],
            "phase": credential["phase"],
            "terminal": credential["phase"] == CONSUMED,
            "show_id": credential["show_id"],
            "slot": credential["slot"],
            "holder_role": credential["holder_role"],
            "version": right["version"],
            "issued_version": 1,
            "generation": right["generation"],
            "state": right["state"],
            "admission_id": right["admission_id"],
            "admission_expired": expired,
            "consume_id": credential["consume_id"],
            "version_after": credential["version_after"],
            "gate_role": credential["gate_role"],
            "slot_state": slot["state"],
            "slot_right_id": slot["right_id"],
            "economic_finality_claimed": False,
            "venue_credential_reissued": False,
            "offline_admission": False,
            "external_admission": "UNSUPPORTED",
            "admission_routing_production": False,
        }
        view.update(NON_CLAIMS)
        view["economic_finality_claimed"] = False
        view["funds_executed"] = False
        view["venue_credential_reissued"] = False
        view["offline_admission"] = False
        view["admission_routing_production"] = False
        view["external_admission"] = "UNSUPPORTED"
        return view

    def _invariant(self) -> None:
        if self._credentials:
            sample = sorted(self._credentials)[0]
            _require(self._local_right(sample)["right_id"] == sample, "MOCK_INVARIANT")
        for credential in self._credentials.values():
            right = self._local_right(credential["right_id"])
            _require(right["generation"] == 1, "MOCK_INVARIANT")
            _require(right["holder_role"] == credential["holder_role"], "MOCK_INVARIANT")
            _require(credential["phase"] in (ELIGIBLE, AUTHORIZED, CONSUMED), "MOCK_INVARIANT")
            if credential["phase"] == CONSUMED:
                _require(right["state"] == "CONSUMED" and right["version"] == 2, "MOCK_INVARIANT")
                _require(right["admission_id"] is None, "MOCK_INVARIANT")
                _require(credential["consume_id"] is not None, "MOCK_INVARIANT")
                _require(credential["version_after"] == 2, "MOCK_INVARIANT")
            else:
                _require(right["state"] == "ACTIVE" and right["version"] == 1, "MOCK_INVARIANT")
            if credential["phase"] == AUTHORIZED:
                live = right["admission_id"]
                if self._now < credential["admission_expires_ms"]:
                    _require(live == credential["admission_id"], "MOCK_INVARIANT")
                else:
                    _require(live is None, "MOCK_INVARIANT")
            if credential["phase"] == ELIGIBLE:
                _require(right["admission_id"] is None and credential["admission_id"] is None, "MOCK_INVARIANT")
