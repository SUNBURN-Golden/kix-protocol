"""In-memory acceptance machine for reservation and ticketing.

The machine decides which hold, confirm, issue, and consume commands are
accepted, then replays that journal deterministically. Slot, price, payment-fact,
and admission predicates stay in mock_gates.py. Resale and credit commands are
not on this machine.

A bound issuance reads an injected settlement machine's view. It does not call
settlement commands and does not move money. Ticket evidence is not economic
finality. `economic_finality_claimed` stays false.

Provenance remains MOCK_GATE_ONLY. A matched replay is equality of this
process's journal and views, not admission routing or chain finality.
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

HELD = "HELD"
RELEASED = "RELEASED"
CONFIRMED = "CONFIRMED"
CANCELLED = "CANCELLED"
PAYMENT_NOTED = "PAYMENT_NOTED"
ISSUED = "ISSUED"
ADMISSION_AUTHORIZED = "ADMISSION_AUTHORIZED"
CONSUMED = "CONSUMED"

TERMINAL_PHASES = frozenset({RELEASED, CANCELLED, CONSUMED})
PRE_ISSUE = frozenset({HELD, CONFIRMED, PAYMENT_NOTED})
POST_ISSUE = frozenset({ISSUED, ADMISSION_AUTHORIZED, CONSUMED})
OCCUPYING = PRE_ISSUE | POST_ISSUE

REPLAYABLE = frozenset(
    {
        "set_clock",
        "register_show",
        "hold",
        "release",
        "confirm",
        "cancel",
        "observe_payment",
        "bind_settlement",
        "issue",
        "authorize_admission",
        "consume",
    }
)

_JOURNAL_KEYS = frozenset({"op", "idempotency_key", "subject_id", "body"})
_UNSTORED_REJECTION = frozenset({"MOCK_INVARIANT", "IDEMPOTENCY_CONFLICT", "INVALID_JOURNAL"})
_SETTLEMENT_FINALITY_FLAGS = (
    "funds_executed",
    "admission_granted",
    "bank_debit_observed",
    "legal_debtor_bound",
    "durable",
    "external_return_closed",
    "right_cancelled",
)

_ALLOWED = {
    "release": frozenset({HELD}),
    "confirm": frozenset({HELD}),
    "cancel": frozenset({CONFIRMED}),
    "observe_payment": frozenset({CONFIRMED}),
    "bind_settlement": frozenset({CONFIRMED, PAYMENT_NOTED}),
    "issue": frozenset({PAYMENT_NOTED}),
    "authorize_admission": frozenset({ISSUED, ADMISSION_AUTHORIZED, CONSUMED}),
    "consume": frozenset({ISSUED, ADMISSION_AUTHORIZED}),
}

_SPECIFIC = {
    ("confirm", CONFIRMED): "RESERVATION_ALREADY_ORDERED",
    ("confirm", PAYMENT_NOTED): "RESERVATION_ALREADY_ORDERED",
    ("confirm", ISSUED): "RESERVATION_ALREADY_ORDERED",
    ("confirm", ADMISSION_AUTHORIZED): "RESERVATION_ALREADY_ORDERED",
    ("confirm", CONSUMED): "RESERVATION_ALREADY_ORDERED",
    ("cancel", PAYMENT_NOTED): "COMPENSATION_UNDEFINED",
    ("cancel", ISSUED): "CANCEL_AFTER_ISSUE",
    ("cancel", ADMISSION_AUTHORIZED): "CANCEL_AFTER_ISSUE",
    ("cancel", CONSUMED): "CANCEL_AFTER_ISSUE",
    ("issue", ISSUED): "ORDER_ALREADY_ISSUED",
    ("issue", ADMISSION_AUTHORIZED): "ORDER_ALREADY_ISSUED",
    ("issue", CONSUMED): "ORDER_ALREADY_ISSUED",
    ("consume", CONSUMED): "ALREADY_CONSUMED",
}


class ReservationError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise ReservationError(code)


def _lift(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except GateError as error:
        raise ReservationError(error.code) from error


def _id(value: object, code: str = "INVALID_ID") -> str:
    return _lift(_ident, value, code)


def _amount(value: object) -> int:
    return _lift(_money, value)


def _copy(value: object) -> object:
    return json.loads(_canonical(value))


def _roles(value: object) -> list[str]:
    _require(type(value) is list, "GATES_TYPE")
    _require(len(value) > 0, "GATES_EMPTY")
    _require(len(value) <= GATE_ROLE_LIMIT, "GATES_LIMIT")
    roles = [_id(item) for item in value]
    _require(len(set(roles)) == len(roles), "GATES_DUPLICATE")
    return roles


class ReservationMachine:
    def __init__(self, settlement_source: object | None = None) -> None:
        self._gates = MockGates()
        self._settlement = settlement_source
        self._now = 0
        self._journal: list[dict] = []
        self._idempotency: dict[str, dict] = {}
        self._shows: dict[str, dict] = {}
        self._cases: dict[str, dict] = {}
        self._orders: dict[str, dict] = {}
        self._issuances: dict[str, dict] = {}
        self._admissions: dict[str, str] = {}
        self._consumes: dict[str, str] = {}

    def set_clock(self, subject_id: object, *, idempotency_key: object, now_ms: object) -> dict:
        raw = {"now_ms": now_ms}

        def execute(key: str, request: str) -> dict:
            _require(subject_id == "clock", "INVALID_ID")
            now = _lift(_ms, now_ms, "CLOCK")
            result = _lift(self._gates.set_clock, now)
            _require(result["duplicate"] is False and result["logical_time_ms"] == now, "MOCK_INVARIANT")
            self._now = now
            self._invariant()
            return self._accept(key, request, "set_clock", "clock", {"now_ms": now})

        return self._call("set_clock", subject_id, idempotency_key, raw, execute)

    def register_show(
        self,
        show_id: object,
        *,
        idempotency_key: object,
        organizer_role: object,
        capacity: object,
        gate_roles: object,
        primary_price: object,
        resale_cap: object,
        resale_allowed: object,
        organizer_bps: object,
        platform_bps: object,
    ) -> dict:
        raw = {
            "organizer_role": organizer_role,
            "capacity": capacity,
            "gate_roles": gate_roles,
            "primary_price": primary_price,
            "resale_cap": resale_cap,
            "resale_allowed": resale_allowed,
            "organizer_bps": organizer_bps,
            "platform_bps": platform_bps,
        }

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(show_id)
            organizer = _id(organizer_role)
            _require(type(capacity) is int and 1 <= capacity <= CAPACITY_MAX, "CAPACITY")
            gates = _roles(gate_roles)
            price = _amount(primary_price)
            cap = _amount(resale_cap)
            _require(type(resale_allowed) is bool, "POLICY_FLAG")
            organizer_fee = _lift(_bps, organizer_bps)
            platform_fee = _lift(_bps, platform_bps)
            _require(organizer_fee + platform_fee <= 10000, "BPS_SUM")
            binding = {
                "show_id": normalized_id,
                "organizer_role": organizer,
                "capacity": capacity,
                "gate_roles": gates,
                "primary_price": price,
                "resale_cap": cap,
                "resale_allowed": resale_allowed,
                "organizer_bps": organizer_fee,
                "platform_bps": platform_fee,
            }
            canon = _canonical(binding)
            current = self._shows.get(normalized_id)
            if current is not None:
                _require(current["canon"] == canon, "SHOW_BINDING_CONFLICT")
                raise ReservationError("ILLEGAL_TRANSITION")
            result = _lift(
                self._gates.register_show,
                normalized_id,
                organizer_role=organizer,
                capacity=capacity,
                gate_roles=gates,
                primary_price=price,
                resale_cap=cap,
                resale_allowed=resale_allowed,
                organizer_bps=organizer_fee,
                platform_bps=platform_fee,
            )
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            self._shows[normalized_id] = {"canon": canon}
            self._invariant()
            return self._accept(
                key,
                request,
                "register_show",
                normalized_id,
                {name: binding[name] for name in raw},
                show=self._show_snapshot(normalized_id),
            )

        return self._call("register_show", show_id, idempotency_key, raw, execute)

    def hold(
        self,
        reservation_id: object,
        *,
        idempotency_key: object,
        show_id: object,
        slot: object,
        buyer_role: object,
        expires_ms: object,
    ) -> dict:
        raw = {
            "show_id": show_id,
            "slot": slot,
            "buyer_role": buyer_role,
            "expires_ms": expires_ms,
        }

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(reservation_id)
            show = _id(show_id)
            buyer = _id(buyer_role)
            _require(type(slot) is int, "SLOT")
            expires = _lift(_ms, expires_ms, "RESERVATION_WINDOW")
            binding = {
                "reservation_id": normalized_id,
                "show_id": show,
                "slot": slot,
                "buyer_role": buyer,
                "expires_ms": expires,
            }
            canon = _canonical(binding)
            current = self._cases.get(normalized_id)
            if current is not None:
                _require(current["canon"] == canon, "RESERVATION_BINDING_CONFLICT")
                if current["phase"] in TERMINAL_PHASES:
                    raise ReservationError("TERMINAL_IMMUTABLE")
                raise ReservationError("ILLEGAL_TRANSITION")
            _require(show in self._shows, "UNKNOWN_SHOW")
            result = _lift(
                self._gates.reserve_slot,
                normalized_id,
                show_id=show,
                slot=slot,
                buyer_role=buyer,
                expires_ms=expires,
            )
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            self._cases[normalized_id] = self._new_case(binding, canon)
            self._invariant()
            return self._accept(
                key,
                request,
                "hold",
                normalized_id,
                {"show_id": show, "slot": slot, "buyer_role": buyer, "expires_ms": expires},
                reservation_id=normalized_id,
            )

        return self._call("hold", reservation_id, idempotency_key, raw, execute)

    def release(self, reservation_id: object, *, idempotency_key: object) -> dict:
        def execute(key: str, request: str) -> dict:
            normalized_id = _id(reservation_id)
            case = self._case(normalized_id)
            self._enter(case, "release")
            result = _lift(self._gates.cancel_reservation, normalized_id)
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            case["phase"] = RELEASED
            self._invariant()
            return self._accept(key, request, "release", normalized_id, {}, reservation_id=normalized_id)

        return self._call("release", reservation_id, idempotency_key, {}, execute)

    def confirm(
        self,
        order_id: object,
        *,
        idempotency_key: object,
        reservation_id: object,
        amount: object,
        quote_ref: object = None,
    ) -> dict:
        raw = {"reservation_id": reservation_id, "amount": amount, "quote_ref": quote_ref}

        def execute(key: str, request: str) -> dict:
            normalized_order = _id(order_id)
            normalized_reservation = _id(reservation_id)
            price = _amount(amount)
            quoted = None if quote_ref is None else _id(quote_ref)
            binding = {
                "order_id": normalized_order,
                "reservation_id": normalized_reservation,
                "amount": price,
                "quote_ref": quoted,
            }
            canon = _canonical(binding)
            prior = self._orders.get(normalized_order)
            if prior is not None:
                _require(prior["canon"] == canon, "ORDER_BINDING_CONFLICT")
                raise ReservationError("ILLEGAL_TRANSITION")
            case = self._case(normalized_reservation)
            self._enter(case, "confirm")
            result = _lift(
                self._gates.bind_order,
                normalized_order,
                reservation_id=normalized_reservation,
                amount=price,
                quote_ref=quoted,
            )
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            case["order_id"] = normalized_order
            case["amount"] = price
            case["quote_ref"] = quoted
            case["phase"] = CONFIRMED
            self._orders[normalized_order] = {"canon": canon, "reservation_id": normalized_reservation}
            self._invariant()
            return self._accept(
                key,
                request,
                "confirm",
                normalized_order,
                {
                    "reservation_id": normalized_reservation,
                    "amount": price,
                    "quote_ref": quoted,
                },
                reservation_id=normalized_reservation,
            )

        return self._call("confirm", order_id, idempotency_key, raw, execute)

    def cancel(self, reservation_id: object, *, idempotency_key: object) -> dict:
        def execute(key: str, request: str) -> dict:
            normalized_id = _id(reservation_id)
            case = self._case(normalized_id)
            self._enter(case, "cancel")
            result = _lift(self._gates.abort_order, case["order_id"])
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            case["phase"] = CANCELLED
            self._invariant()
            return self._accept(key, request, "cancel", normalized_id, {}, reservation_id=normalized_id)

        return self._call("cancel", reservation_id, idempotency_key, {}, execute)

    def observe_payment(
        self,
        order_id: object,
        *,
        idempotency_key: object,
        payment_ref: object,
        amount: object,
    ) -> dict:
        raw = {"payment_ref": payment_ref, "amount": amount}

        def execute(key: str, request: str) -> dict:
            normalized_order = _id(order_id)
            payment = _lift(_hex32, payment_ref, "PAYMENT_REF")
            price = _amount(amount)
            order = self._orders.get(normalized_order)
            _require(order is not None, "UNKNOWN_ORDER")
            case = self._case(order["reservation_id"])
            self._enter(case, "observe_payment")
            result = _lift(
                self._gates.observe_payment_fact,
                payment,
                order_id=normalized_order,
                amount=price,
            )
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            case["payment_ref"] = payment
            case["phase"] = PAYMENT_NOTED
            self._invariant()
            return self._accept(
                key,
                request,
                "observe_payment",
                normalized_order,
                {"payment_ref": payment, "amount": price},
                reservation_id=case["reservation_id"],
            )

        return self._call("observe_payment", order_id, idempotency_key, raw, execute)

    def bind_settlement(
        self,
        reservation_id: object,
        *,
        idempotency_key: object,
        settlement_id: object,
    ) -> dict:
        raw = {"settlement_id": settlement_id}

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(reservation_id)
            settlement_id_norm = _id(settlement_id)
            case = self._case(normalized_id)
            self._enter(case, "bind_settlement")
            if case["settlement_id"] is not None:
                _require(case["settlement_id"] == settlement_id_norm, "SETTLEMENT_BINDING_CONFLICT")
                raise ReservationError("ILLEGAL_TRANSITION")
            case["settlement_id"] = settlement_id_norm
            self._invariant()
            return self._accept(
                key,
                request,
                "bind_settlement",
                normalized_id,
                {"settlement_id": settlement_id_norm},
                reservation_id=normalized_id,
            )

        return self._call("bind_settlement", reservation_id, idempotency_key, raw, execute)

    def issue(self, issuance_id: object, *, idempotency_key: object, order_id: object) -> dict:
        raw = {"order_id": order_id}

        def execute(key: str, request: str) -> dict:
            normalized_issue = _id(issuance_id)
            normalized_order = _id(order_id)
            canon = _canonical({"issuance_id": normalized_issue, "order_id": normalized_order})
            prior = self._issuances.get(normalized_issue)
            if prior is not None:
                _require(prior["canon"] == canon, "ISSUANCE_BINDING_CONFLICT")
                raise ReservationError("ILLEGAL_TRANSITION")
            order = self._orders.get(normalized_order)
            _require(order is not None, "UNKNOWN_ORDER")
            case = self._case(order["reservation_id"])
            self._enter(case, "issue")
            observed = self._settlement_allows_issue(case)
            result = _lift(self._gates.issue, normalized_issue, order_id=normalized_order)
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            evidence = dict(result["evidence"])
            _require(evidence["kind"] == 1 and evidence["chain_issued"] is False, "MOCK_INVARIANT")
            _require("seller_due" not in evidence, "MOCK_INVARIANT")
            case["issuance_id"] = normalized_issue
            case["right_id"] = normalized_issue
            case["mock_settlement_commit_observed"] = observed
            case["phase"] = ISSUED
            self._issuances[normalized_issue] = {
                "canon": canon,
                "reservation_id": case["reservation_id"],
            }
            self._invariant()
            return self._accept(
                key,
                request,
                "issue",
                normalized_issue,
                {"order_id": normalized_order},
                reservation_id=case["reservation_id"],
                evidence=evidence,
            )

        return self._call("issue", issuance_id, idempotency_key, raw, execute)

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
    ) -> dict:
        raw = {
            "right_id": right_id,
            "version": version,
            "holder_role": holder_role,
            "gate_role": gate_role,
            "request": request,
            "expires_ms": expires_ms,
        }

        def execute(key: str, request_fp: str) -> dict:
            normalized_admission = _id(admission_id)
            right = _id(right_id)
            holder = _id(holder_role)
            gate = _id(gate_role)
            ticket = _lift(_hex32, request, "ADMISSION_REQUEST")
            expires = _lift(_ms, expires_ms, "ADMISSION_WINDOW")
            current_version = _lift(_version, version)
            binding = {
                "admission_id": normalized_admission,
                "right_id": right,
                "version": current_version,
                "holder_role": holder,
                "gate_role": gate,
                "request": ticket,
                "expires_ms": expires,
            }
            canon = _canonical(binding)
            prior = self._admissions.get(normalized_admission)
            if prior is not None:
                _require(prior == canon, "ADMISSION_BINDING_CONFLICT")
                raise ReservationError("ILLEGAL_TRANSITION")
            case = self._case_by_right(right)
            self._enter(case, "authorize_admission")
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
            case["admission_id"] = normalized_admission
            case["admission_expires_ms"] = expires
            case["phase"] = ADMISSION_AUTHORIZED
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
                },
                reservation_id=case["reservation_id"],
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
    ) -> dict:
        raw = {
            "right_id": right_id,
            "version": version,
            "gate_role": gate_role,
            "request": request,
        }

        def execute(key: str, request_fp: str) -> dict:
            normalized_consume = _id(consume_id)
            right = _id(right_id)
            gate = _id(gate_role)
            ticket = _lift(_hex32, request, "ADMISSION_REQUEST")
            current_version = _lift(_version, version)
            canon = _canonical(
                {
                    "consume_id": normalized_consume,
                    "right_id": right,
                    "version": current_version,
                    "gate_role": gate,
                    "request": ticket,
                }
            )
            case = self._case_by_right(right)
            self._enter(case, "consume")
            prior = self._consumes.get(normalized_consume)
            if prior is not None:
                _require(prior == canon, "CONSUME_BINDING_CONFLICT")
                raise ReservationError("ILLEGAL_TRANSITION")
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
            case["consume_id"] = normalized_consume
            case["admission_id"] = None
            case["admission_expires_ms"] = None
            case["version_after"] = evidence["version_after"]
            case["phase"] = CONSUMED
            self._consumes[normalized_consume] = canon
            self._invariant()
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
                },
                reservation_id=case["reservation_id"],
                evidence=evidence,
            )

        return self._call("consume", consume_id, idempotency_key, raw, execute)

    def reconcile(self, reservation_id: object, *, idempotency_key: object) -> dict:
        """Replay the journal and require the views to match.

        The receipt is process-local. restore rebuilds accepted commands and
        does not store this receipt.
        """

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(reservation_id)
            case = self._case(normalized_id)
            restored = ReservationMachine.restore(
                self.export_journal(),
                settlement_source=self._settlement,
            )
            _require(restored.canonical_state() == self.canonical_state(), "MOCK_INVARIANT")
            result = self._envelope(
                applied="reconcile",
                reservation=self._view(case),
                matched=True,
                state_digest=self.state_digest(),
                entry_count=len(self._journal),
            )
            encoded = _canonical(result)
            self._idempotency[key] = {"request": request, "result": encoded, "error": None}
            return json.loads(encoded)

        return self._call("reconcile", reservation_id, idempotency_key, {}, execute)

    def reject_external(self, kind: object) -> None:
        """Refuse a live payment, venue, or HTTP attempt.

        The kind is an external-attempt label. This method never dispatches
        hold, issue, consume, or any other accepted command.
        """

        _id(kind)
        raise ReservationError("EXTERNAL_UNSUPPORTED")

    def view(self, reservation_id: object) -> dict:
        return self._view(self._case(_id(reservation_id)))

    def view_show(self, show_id: object) -> dict:
        normalized = _id(show_id)
        _require(normalized in self._shows, "UNKNOWN_SHOW")
        return self._envelope(applied="view_show", show=self._show_snapshot(normalized))

    def export_journal(self) -> list:
        return _copy(self._journal)

    def canonical_state(self) -> str:
        payload = {
            "logical_time_ms": self._now,
            "shows": [self._show_snapshot(show_id) for show_id in sorted(self._shows)],
            "reservations": [self._view(self._cases[rid]) for rid in sorted(self._cases)],
            "journal": self._journal,
        }
        return _canonical(payload)

    def state_digest(self) -> str:
        return hashlib.sha256(self.canonical_state().encode("utf-8")).hexdigest()

    @classmethod
    def restore(cls, journal: object, settlement_source: object | None = None) -> ReservationMachine:
        _require(type(journal) is list, "INVALID_JOURNAL")
        machine = cls(settlement_source)
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
                raise ReservationError("INVALID_JOURNAL") from error
        return machine

    def _new_case(self, binding: dict, canon: str) -> dict:
        return {
            "canon": canon,
            "reservation_id": binding["reservation_id"],
            "phase": HELD,
            "show_id": binding["show_id"],
            "slot": binding["slot"],
            "buyer_role": binding["buyer_role"],
            "expires_ms": binding["expires_ms"],
            "order_id": None,
            "amount": None,
            "quote_ref": None,
            "payment_ref": None,
            "issuance_id": None,
            "right_id": None,
            "admission_id": None,
            "admission_expires_ms": None,
            "consume_id": None,
            "version_after": None,
            "settlement_id": None,
            "mock_settlement_commit_observed": False,
            "economic_finality_claimed": False,
            "subject_ids": [binding["reservation_id"]],
        }

    def _enter(self, case: dict, op: str) -> None:
        phase = case["phase"]
        specific = _SPECIFIC.get((op, phase))
        if specific is not None:
            raise ReservationError(specific)
        if phase in _ALLOWED[op]:
            return
        if phase in TERMINAL_PHASES:
            raise ReservationError("TERMINAL_IMMUTABLE")
        raise ReservationError("ILLEGAL_TRANSITION")

    def _case(self, reservation_id: str) -> dict:
        case = self._cases.get(reservation_id)
        _require(case is not None, "UNKNOWN_RESERVATION")
        return case

    def _case_by_right(self, right_id: str) -> dict:
        issuance = self._issuances.get(right_id)
        _require(issuance is not None, "UNKNOWN_RIGHT")
        return self._case(issuance["reservation_id"])

    def _settlement_allows_issue(self, case: dict) -> bool:
        if case["settlement_id"] is None:
            return False
        _require(self._settlement is not None, "SETTLEMENT_SOURCE_REQUIRED")
        try:
            view = self._settlement.view(case["settlement_id"])
        except Exception as error:
            code = getattr(error, "code", None)
            if type(code) is str:
                raise ReservationError(code) from error
            raise
        _require(type(view) is dict, "SETTLEMENT_NOT_COMMITTED")
        _require(view.get("phase") == "COMMITTED", "SETTLEMENT_NOT_COMMITTED")
        gross = view.get("gross")
        _require(
            view.get("currency") == "KRW" and type(gross) is int and gross == case["amount"],
            "SETTLEMENT_AMOUNT_MISMATCH",
        )
        for name in _SETTLEMENT_FINALITY_FLAGS:
            _require(view.get(name) is False, "SETTLEMENT_VIEW_REJECTED")
        return True

    def _call(self, op: str, subject_id: object, idempotency_key: object, raw: dict, execute) -> dict:
        key = _id(idempotency_key)
        request = self._fingerprint(op, subject_id, raw)
        if request is not None:
            replayed = self._replay_if_known(key, request)
            if replayed is not None:
                return replayed
        try:
            return execute(key, request)
        except ReservationError as error:
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
            raise ReservationError(prior["error"])
        result = json.loads(prior["result"])
        result["duplicate"] = True
        result["applied"] = None
        result["economic_finality_claimed"] = False
        result["funds_executed"] = False
        reservation = result.get("reservation")
        if type(reservation) is dict:
            reservation["economic_finality_claimed"] = False
            reservation["funds_executed"] = False
        return result

    def _accept(
        self,
        key: str,
        request: str,
        op: str,
        subject_id: str,
        body: dict,
        *,
        reservation_id: str | None = None,
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
        reservation = None
        if reservation_id is not None:
            case = self._cases[reservation_id]
            if subject_id not in case["subject_ids"]:
                case["subject_ids"].append(subject_id)
            reservation = self._view(case)
            extra.setdefault("show", self._show_snapshot(case["show_id"]))
        result = self._envelope(applied=op, reservation=reservation, **extra)
        self._idempotency[key] = {"request": request, "result": _canonical(result), "error": None}
        return _copy(result)

    def _envelope(self, *, applied: str, reservation: dict | None = None, **extra: object) -> dict:
        body = {
            "provenance": PROVENANCE,
            "lifecycle_authority": AUTHORITY,
            "duplicate": False,
            "applied": applied,
            "logical_time_ms": self._now,
            "external_payment": "UNSUPPORTED",
            "external_admission": "UNSUPPORTED",
            "economic_finality_claimed": False,
        }
        body.update(NON_CLAIMS)
        if reservation is not None:
            body["reservation"] = reservation
        body.update(extra)
        body["provenance"] = PROVENANCE
        body["lifecycle_authority"] = AUTHORITY
        body["duplicate"] = False
        body["applied"] = applied
        body["economic_finality_claimed"] = False
        body["funds_executed"] = False
        body["external_payment"] = "UNSUPPORTED"
        body["external_admission"] = "UNSUPPORTED"
        return body

    def _show_snapshot(self, show_id: str) -> dict:
        return _lift(self._gates.view_show, show_id)["show"]

    def _right_snapshot(self, right_id: str) -> dict:
        return _lift(self._gates.view_right, right_id)["right"]

    def _live_admission_id(self, case: dict) -> str | None:
        expires = case["admission_expires_ms"]
        if case["phase"] != ADMISSION_AUTHORIZED or expires is None or self._now >= expires:
            return None
        return case["admission_id"]

    def _entry_count(self, case: dict) -> int:
        subjects = set(case["subject_ids"])
        return sum(1 for entry in self._journal if entry["subject_id"] in subjects)

    def _settlement_gate(self, case: dict) -> str:
        if case["mock_settlement_commit_observed"]:
            return "MOCK_COMMIT_OBSERVED"
        if case["settlement_id"] is None:
            return "UNBOUND"
        return "BOUND"

    def _view(self, case: dict) -> dict:
        phase = case["phase"]
        row = self._slot_row(case)
        right = None if case["right_id"] is None else self._right_snapshot(case["right_id"])
        expired = phase in PRE_ISSUE and self._now >= case["expires_ms"]
        view = {
            "provenance": PROVENANCE,
            "lifecycle_authority": AUTHORITY,
            "reservation_id": case["reservation_id"],
            "phase": phase,
            "terminal": phase in TERMINAL_PHASES,
            "show_id": case["show_id"],
            "slot": case["slot"],
            "buyer_role": case["buyer_role"],
            "expires_ms": case["expires_ms"],
            "expired": expired,
            "order_id": case["order_id"],
            "amount": case["amount"],
            "currency": None if case["amount"] is None else "KRW",
            "quote_ref": case["quote_ref"],
            "payment_ref": case["payment_ref"],
            "issuance_id": case["issuance_id"],
            "admission_id": self._live_admission_id(case),
            "admission_expired": (
                case["phase"] == ADMISSION_AUTHORIZED
                and case["admission_expires_ms"] is not None
                and self._now >= case["admission_expires_ms"]
            ),
            "consume_id": case["consume_id"],
            "settlement_id": case["settlement_id"],
            "settlement_gate": self._settlement_gate(case),
            "mock_settlement_commit_observed": case["mock_settlement_commit_observed"],
            "economic_finality_claimed": False,
            "slot_state": row["state"],
            "slot_reservation_id": row["reservation_id"],
            "slot_right_id": row["right_id"],
            "right": right,
            "accepted_entries": self._entry_count(case),
            "external_payment": "UNSUPPORTED",
            "external_admission": "UNSUPPORTED",
        }
        view.update(NON_CLAIMS)
        view["economic_finality_claimed"] = False
        view["funds_executed"] = False
        view["chain_issued"] = False
        return view

    def _slot_row(self, case: dict) -> dict:
        for row in self._show_snapshot(case["show_id"])["slots"]:
            if row["slot"] == case["slot"]:
                return row
        raise ReservationError("MOCK_INVARIANT")

    def _invariant(self) -> None:
        if self._shows:
            sample = sorted(self._shows)[0]
            _require(self._show_envelope_time(sample) == self._now, "MOCK_INVARIANT")
        occupants: dict[tuple[str, int], dict] = {}
        for case in self._cases.values():
            _require(case["show_id"] in self._shows, "MOCK_INVARIANT")
            _require(case["economic_finality_claimed"] is False, "MOCK_INVARIANT")
            _require(case["phase"] in OCCUPYING or case["phase"] in TERMINAL_PHASES, "MOCK_INVARIANT")
            if case["settlement_id"] is None:
                _require(case["mock_settlement_commit_observed"] is False, "MOCK_INVARIANT")
            if case["phase"] in POST_ISSUE and case["settlement_id"] is not None:
                _require(case["mock_settlement_commit_observed"] is True, "MOCK_INVARIANT")
            if case["phase"] in (HELD, RELEASED):
                _require(case["order_id"] is None and case["payment_ref"] is None, "MOCK_INVARIANT")
            if case["phase"] == CONFIRMED:
                _require(case["order_id"] is not None and case["payment_ref"] is None, "MOCK_INVARIANT")
            if case["phase"] == CANCELLED:
                _require(case["order_id"] is not None and case["payment_ref"] is None, "MOCK_INVARIANT")
            if case["phase"] == PAYMENT_NOTED or case["phase"] in POST_ISSUE:
                _require(case["order_id"] is not None and case["payment_ref"] is not None, "MOCK_INVARIANT")
            if case["order_id"] is not None:
                _require(type(case["amount"]) is int and case["amount"] > 0, "MOCK_INVARIANT")
            if case["phase"] in OCCUPYING:
                key = (case["show_id"], case["slot"])
                _require(key not in occupants, "MOCK_INVARIANT")
                occupants[key] = case
            if case["phase"] in PRE_ISSUE:
                _require(case["right_id"] is None, "MOCK_INVARIANT")
            if case["phase"] in POST_ISSUE:
                right = self._right_snapshot(case["right_id"])
                _require(right["generation"] == 1, "MOCK_INVARIANT")
                _require(right["holder_role"] == case["buyer_role"], "MOCK_INVARIANT")
                _require(right["listing_id"] is None, "MOCK_INVARIANT")
                if case["phase"] == CONSUMED:
                    _require(right["state"] == "CONSUMED", "MOCK_INVARIANT")
                    _require(right["version"] == 2 and case["version_after"] == 2, "MOCK_INVARIANT")
                    _require(right["admission_id"] is None, "MOCK_INVARIANT")
                else:
                    _require(right["state"] == "ACTIVE" and right["version"] == 1, "MOCK_INVARIANT")
                if case["phase"] == ADMISSION_AUTHORIZED:
                    live = self._live_admission_id(case)
                    _require(right["admission_id"] == live, "MOCK_INVARIANT")
        for show_id in self._shows:
            for row in self._show_snapshot(show_id)["slots"]:
                owner = occupants.get((show_id, row["slot"]))
                if row["state"] == "FREE":
                    _require(owner is None and row["reservation_id"] is None and row["right_id"] is None, "MOCK_INVARIANT")
                elif row["state"] == "RESERVED":
                    _require(owner is not None and owner["phase"] in PRE_ISSUE, "MOCK_INVARIANT")
                    _require(row["reservation_id"] == owner["reservation_id"] and row["right_id"] is None, "MOCK_INVARIANT")
                elif row["state"] == "ISSUED":
                    _require(owner is not None and owner["phase"] in POST_ISSUE, "MOCK_INVARIANT")
                    _require(row["reservation_id"] == owner["reservation_id"], "MOCK_INVARIANT")
                    _require(row["right_id"] == owner["right_id"], "MOCK_INVARIANT")
                else:
                    _require(False, "MOCK_INVARIANT")

    def _show_envelope_time(self, show_id: str) -> int:
        return _lift(self._gates.view_show, show_id)["logical_time_ms"]
