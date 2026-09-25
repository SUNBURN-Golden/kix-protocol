"""Offline booking, resale, and admission gates.

Deterministic and in-memory. No network, files, payment provider, or chain.
Role labels are not authenticated people. A passed call is not a durable
reservation, a bank fact, or a consume on `kix::rights`.

Contract: docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md
"""

from __future__ import annotations

import json

MONEY_MAX = 10**12
CLOCK_MAX = 10**15
CAPACITY_MAX = 16
GATE_ROLE_LIMIT = 16
OFFER_WINDOW_MS = 900_000
ADMISSION_WINDOW_MS = 120_000
PROVENANCE = "MOCK_GATE_ONLY"
HEX = frozenset("0123456789abcdef")

NON_CLAIMS = {
    "role_authenticated": False,
    "organizer_authenticated": False,
    "chain_grant_current": False,
    "durable": False,
    "quote_policy_approved": False,
    "discount_applied": False,
    "provider_fact_live": False,
    "funds_executed": False,
    "buyer_evidence_available": False,
    "chain_owner_current": False,
    "cross_channel_exclusive": False,
    "admission_routing_production": False,
    "private_proof_verified": False,
    "compensation_defined": False,
}


class GateError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise GateError(code)


def _ident(value: object, code: str = "INVALID_ID") -> str:
    _require(type(value) is str and 0 < len(value) <= 100 and value.strip() == value, code)
    return value


def _money(value: object) -> int:
    _require(type(value) is int and 0 < value <= MONEY_MAX, "INVALID_AMOUNT")
    return value


def _bps(value: object) -> int:
    _require(type(value) is int and 0 <= value <= 10000, "BPS")
    return value


def _ms(value: object, code: str) -> int:
    _require(type(value) is int and 0 <= value <= CLOCK_MAX, code)
    return value


def _hex32(value: object, code: str) -> str:
    _require(type(value) is str and len(value) == 64 and all(char in HEX for char in value), code)
    return value


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _version(value: object) -> int:
    _require(type(value) is int and value >= 0, "VERSION_TYPE")
    return value


def _allocation(amount: int, organizer_bps: int, platform_bps: int) -> tuple[int, int, int]:
    organizer_due = amount * organizer_bps // 10000
    platform_due = amount * platform_bps // 10000
    seller_due = amount - organizer_due - platform_due
    _require(seller_due >= 0 and organizer_due + platform_due + seller_due == amount, "MOCK_INVARIANT")
    return organizer_due, platform_due, seller_due


class MockGates:
    def __init__(self) -> None:
        self._now = 0
        self._shows: dict[str, dict] = {}
        self._reservations: dict[str, dict] = {}
        self._orders: dict[str, dict] = {}
        self._issuances: dict[str, dict] = {}
        self._rights: dict[str, dict] = {}
        self._listings: dict[str, dict] = {}
        self._transfers: dict[str, dict] = {}
        self._admissions: dict[str, dict] = {}
        self._consumes: dict[str, dict] = {}

    def set_clock(self, now_ms: object) -> dict:
        now_ms = _ms(now_ms, "CLOCK")
        _require(now_ms >= self._now, "CLOCK_REGRESSION")
        self._now = now_ms
        return self._env(applied="set_clock")

    def register_show(
        self,
        show_id: object,
        *,
        organizer_role: object,
        capacity: object,
        gate_roles: object,
        primary_price: object,
        resale_cap: object,
        resale_allowed: object,
        organizer_bps: object,
        platform_bps: object,
    ) -> dict:
        show_id = _ident(show_id)
        organizer_role = _ident(organizer_role)
        _require(type(capacity) is int and 1 <= capacity <= CAPACITY_MAX, "CAPACITY")
        gates = self._gate_roles(gate_roles)
        primary_price = _money(primary_price)
        resale_cap = _money(resale_cap)
        _require(type(resale_allowed) is bool, "POLICY_FLAG")
        organizer_bps = _bps(organizer_bps)
        platform_bps = _bps(platform_bps)
        _require(organizer_bps + platform_bps <= 10000, "BPS_SUM")
        binding = {
            "show_id": show_id,
            "organizer_role": organizer_role,
            "capacity": capacity,
            "gate_roles": gates,
            "primary_price": primary_price,
            "resale_cap": resale_cap,
            "resale_allowed": resale_allowed,
            "organizer_bps": organizer_bps,
            "platform_bps": platform_bps,
        }
        canon = _canonical(binding)
        current = self._shows.get(show_id)
        if current is not None:
            _require(current["canon"] == canon, "SHOW_BINDING_CONFLICT")
            return self._env(duplicate=True, show=self._show_view(current))
        show = {
            "canon": canon,
            "show_id": show_id,
            "organizer_role": organizer_role,
            "capacity": capacity,
            "gate_roles": gates,
            "primary_price": primary_price,
            "resale_cap": resale_cap,
            "resale_allowed": resale_allowed,
            "organizer_bps": organizer_bps,
            "platform_bps": platform_bps,
            "open": True,
            "slots": {
                slot: {"state": "FREE", "reservation_id": None, "right_id": None}
                for slot in range(capacity)
            },
            "payment_facts": {},
        }
        self._shows[show_id] = show
        self._invariant()
        return self._env(applied="register_show", show=self._show_view(show))

    def reserve_slot(
        self,
        reservation_id: object,
        *,
        show_id: object,
        slot: object,
        buyer_role: object,
        expires_ms: object,
    ) -> dict:
        reservation_id = _ident(reservation_id)
        show_id = _ident(show_id)
        buyer_role = _ident(buyer_role)
        expires_ms = _ms(expires_ms, "RESERVATION_WINDOW")
        _require(type(slot) is int, "SLOT")
        binding = {
            "reservation_id": reservation_id,
            "show_id": show_id,
            "slot": slot,
            "buyer_role": buyer_role,
            "expires_ms": expires_ms,
        }
        canon = _canonical(binding)
        current = self._reservations.get(reservation_id)
        if current is not None:
            _require(current["canon"] == canon, "RESERVATION_BINDING_CONFLICT")
            return self._reservation_env(current, duplicate=True)
        show = self._show(show_id)
        slot = self._slot(slot, show)
        self._window(expires_ms, OFFER_WINDOW_MS, "RESERVATION_WINDOW")
        row = show["slots"][slot]
        _require(row["state"] == "FREE", "SLOT_OCCUPIED")
        reservation = {
            "canon": canon,
            "reservation_id": reservation_id,
            "show_id": show_id,
            "slot": slot,
            "buyer_role": buyer_role,
            "expires_ms": expires_ms,
            "state": "OPEN",
            "order_id": None,
        }
        row["state"] = "RESERVED"
        row["reservation_id"] = reservation_id
        self._reservations[reservation_id] = reservation
        self._invariant()
        return self._reservation_env(reservation, applied="reserve_slot")

    def cancel_reservation(self, reservation_id: object) -> dict:
        reservation = self._reservation(reservation_id)
        if reservation["state"] == "CANCELLED":
            return self._reservation_env(reservation, duplicate=True)
        _require(reservation["state"] == "OPEN", "RESERVATION_NOT_OPEN")
        _require(reservation["order_id"] is None, "ORDER_BOUND")
        reservation["state"] = "CANCELLED"
        self._free_slot(reservation)
        self._invariant()
        return self._reservation_env(reservation, applied="cancel_reservation")

    def bind_order(
        self,
        order_id: object,
        *,
        reservation_id: object,
        amount: object,
        quote_ref: object = None,
    ) -> dict:
        order_id = _ident(order_id)
        reservation_id = _ident(reservation_id)
        amount = _money(amount)
        if quote_ref is not None:
            quote_ref = _ident(quote_ref)
        binding = {
            "order_id": order_id,
            "reservation_id": reservation_id,
            "amount": amount,
            "quote_ref": quote_ref,
        }
        canon = _canonical(binding)
        current = self._orders.get(order_id)
        if current is not None:
            _require(current["canon"] == canon, "ORDER_BINDING_CONFLICT")
            return self._order_env(current, duplicate=True)
        reservation = self._reservation(reservation_id)
        _require(reservation["state"] == "OPEN", "RESERVATION_NOT_OPEN")
        _require(self._now < reservation["expires_ms"], "RESERVATION_EXPIRED")
        _require(reservation["order_id"] is None, "RESERVATION_ALREADY_ORDERED")
        show = self._show(reservation["show_id"])
        _require(amount == show["primary_price"], "PRIMARY_PRICE_MISMATCH")
        order = {
            "canon": canon,
            "order_id": order_id,
            "reservation_id": reservation_id,
            "buyer_role": reservation["buyer_role"],
            "amount": amount,
            "currency": "KRW",
            "quote_ref": quote_ref,
            "state": "OPEN",
            "payment_ref": None,
            "issuance_id": None,
        }
        reservation["order_id"] = order_id
        self._orders[order_id] = order
        self._invariant()
        return self._order_env(order, applied="bind_order")

    def abort_order(self, order_id: object) -> dict:
        order = self._order(order_id)
        if order["state"] == "ABORTED":
            return self._order_env(order, duplicate=True)
        _require(order["state"] == "OPEN", "ORDER_NOT_ABORTABLE")
        _require(order["payment_ref"] is None, "COMPENSATION_UNDEFINED")
        reservation = self._reservation(order["reservation_id"])
        _require(reservation["state"] == "OPEN", "MOCK_INVARIANT")
        order["state"] = "ABORTED"
        reservation["state"] = "CANCELLED"
        self._free_slot(reservation)
        self._invariant()
        return self._order_env(order, applied="abort_order")

    def observe_payment_fact(self, payment_ref: object, *, order_id: object, amount: object) -> dict:
        payment_ref = _hex32(payment_ref, "PAYMENT_REF")
        order_id = _ident(order_id)
        amount = _money(amount)
        canon = _canonical({"kind": "PRIMARY", "payment_ref": payment_ref, "order_id": order_id, "amount": amount})
        order = self._order(order_id)
        show = self._show_of_reservation(order["reservation_id"])
        if self._replay_payment(show, payment_ref, canon):
            return self._order_env(order, duplicate=True)
        _require(order["state"] == "OPEN", "ORDER_NOT_OPEN")
        reservation = self._reservation(order["reservation_id"])
        _require(reservation["state"] == "OPEN", "RESERVATION_NOT_OPEN")
        _require(self._now < reservation["expires_ms"], "RESERVATION_EXPIRED")
        _require(amount == order["amount"], "PAYMENT_AMOUNT_MISMATCH")
        _require(order["payment_ref"] is None, "ORDER_PAYMENT_BOUND")
        show["payment_facts"][payment_ref] = canon
        order["payment_ref"] = payment_ref
        self._invariant()
        return self._order_env(order, applied="observe_payment_fact")

    def issue(self, issuance_id: object, *, order_id: object) -> dict:
        issuance_id = _ident(issuance_id)
        order_id = _ident(order_id)
        canon = _canonical({"issuance_id": issuance_id, "order_id": order_id})
        current = self._issuances.get(issuance_id)
        if current is not None:
            _require(current["canon"] == canon, "ISSUANCE_BINDING_CONFLICT")
            return self._issue_env(current, duplicate=True)
        order = self._order(order_id)
        _require(order["state"] == "OPEN", "ORDER_NOT_OPEN")
        _require(order["payment_ref"] is not None, "PAYMENT_FACT_REQUIRED")
        _require(order["issuance_id"] is None, "ORDER_ALREADY_ISSUED")
        reservation = self._reservation(order["reservation_id"])
        _require(reservation["state"] == "OPEN", "RESERVATION_NOT_OPEN")
        _require(self._now < reservation["expires_ms"], "RESERVATION_EXPIRED")
        show = self._show(reservation["show_id"])
        row = show["slots"][reservation["slot"]]
        _require(row["state"] == "RESERVED" and row["reservation_id"] == reservation["reservation_id"], "MOCK_INVARIANT")
        evidence = {
            "issuance_id": issuance_id,
            "right_id": issuance_id,
            "show_id": show["show_id"],
            "slot": reservation["slot"],
            "holder_role": order["buyer_role"],
            "kind": 1,
            "generation": 1,
            "version": 1,
            "amount": order["amount"],
            "currency": "KRW",
            "payment_ref": order["payment_ref"],
            "quote_ref": order["quote_ref"],
            "buyer_evidence_available": False,
            "chain_issued": False,
        }
        right = {
            "right_id": issuance_id,
            "show_id": show["show_id"],
            "slot": reservation["slot"],
            "holder_role": order["buyer_role"],
            "state": "ACTIVE",
            "version": 1,
            "generation": 1,
            "listing_id": None,
            "admission_id": None,
            "last_payment": order["payment_ref"],
            "last_amount": order["amount"],
            "last_payer": order["buyer_role"],
        }
        issuance = {"canon": canon, "evidence": evidence, "right_id": issuance_id}
        order["state"] = "ISSUED"
        order["issuance_id"] = issuance_id
        reservation["state"] = "ISSUED"
        row["state"] = "ISSUED"
        row["right_id"] = issuance_id
        self._issuances[issuance_id] = issuance
        self._rights[issuance_id] = right
        self._invariant()
        return self._issue_env(issuance, applied="issue")

    def list_resale(
        self,
        listing_id: object,
        *,
        right_id: object,
        version: object,
        seller_role: object,
        recipient_role: object,
        amount: object,
        expires_ms: object,
    ) -> dict:
        listing_id = _ident(listing_id)
        right_id = _ident(right_id)
        seller_role = _ident(seller_role)
        recipient_role = _ident(recipient_role)
        amount = _money(amount)
        expires_ms = _ms(expires_ms, "LISTING_WINDOW")
        version = _version(version)
        binding = {
            "listing_id": listing_id,
            "right_id": right_id,
            "version": version,
            "seller_role": seller_role,
            "recipient_role": recipient_role,
            "amount": amount,
            "expires_ms": expires_ms,
        }
        canon = _canonical(binding)
        current = self._listings.get(listing_id)
        if current is not None:
            _require(current["canon"] == canon, "LISTING_BINDING_CONFLICT")
            return self._listing_env(current, duplicate=True)
        right = self._right(right_id)
        show = self._show(right["show_id"])
        _require(right["state"] == "ACTIVE", "RIGHT_NOT_ACTIVE")
        _require(version == right["version"], "STALE_VERSION")
        _require(seller_role == right["holder_role"], "NOT_HOLDER")
        _require(show["resale_allowed"], "RESALE_POLICY_REJECTED")
        _require(recipient_role != right["holder_role"], "RECIPIENT_IS_HOLDER")
        _require(amount <= show["resale_cap"], "RESALE_CAP")
        self._window(expires_ms, OFFER_WINDOW_MS, "LISTING_WINDOW")
        _require(self._live_admission(right) is None, "ADMISSION_LOCKED")
        _require(self._live_listing(right) is None, "RIGHT_SALE_LOCKED")
        right["admission_id"] = None
        listing = {
            "canon": canon,
            "listing_id": listing_id,
            "right_id": right_id,
            "show_id": show["show_id"],
            "seller_role": seller_role,
            "recipient_role": recipient_role,
            "amount": amount,
            "expires_ms": expires_ms,
            "version": version,
            "state": "LISTED",
            "payment_ref": None,
        }
        right["listing_id"] = listing_id
        self._listings[listing_id] = listing
        self._invariant()
        return self._listing_env(listing, applied="list_resale")

    def cancel_listing(self, listing_id: object, *, seller_role: object) -> dict:
        seller_role = _ident(seller_role)
        listing = self._listing(listing_id)
        _require(seller_role == listing["seller_role"], "NOT_HOLDER")
        if listing["state"] == "CANCELLED":
            return self._listing_env(listing, duplicate=True)
        _require(listing["state"] == "LISTED" and self._now < listing["expires_ms"], "LISTING_NOT_OPEN")
        _require(listing["payment_ref"] is None, "COMPENSATION_UNDEFINED")
        listing["state"] = "CANCELLED"
        right = self._right(listing["right_id"])
        if right["listing_id"] == listing["listing_id"]:
            right["listing_id"] = None
        self._invariant()
        return self._listing_env(listing, applied="cancel_listing")

    def observe_resale_payment(self, payment_ref: object, *, listing_id: object, amount: object) -> dict:
        payment_ref = _hex32(payment_ref, "PAYMENT_REF")
        listing_id = _ident(listing_id)
        amount = _money(amount)
        canon = _canonical({"kind": "RESALE", "payment_ref": payment_ref, "listing_id": listing_id, "amount": amount})
        listing = self._listing(listing_id)
        show = self._show(listing["show_id"])
        if self._replay_payment(show, payment_ref, canon):
            return self._listing_env(listing, duplicate=True)
        _require(listing["state"] == "LISTED" and self._now < listing["expires_ms"], "LISTING_NOT_OPEN")
        _require(amount == listing["amount"], "RESALE_AMOUNT_MISMATCH")
        _require(listing["payment_ref"] is None, "LISTING_PAYMENT_BOUND")
        right = self._right(listing["right_id"])
        _require(right["state"] == "ACTIVE" and right["version"] == listing["version"], "STALE_VERSION")
        _require(right["holder_role"] == listing["seller_role"], "NOT_HOLDER")
        show["payment_facts"][payment_ref] = canon
        listing["payment_ref"] = payment_ref
        self._invariant()
        return self._listing_env(listing, applied="observe_resale_payment")

    def accept_resale(self, transfer_id: object, *, listing_id: object) -> dict:
        transfer_id = _ident(transfer_id)
        listing_id = _ident(listing_id)
        canon = _canonical({"transfer_id": transfer_id, "listing_id": listing_id})
        current = self._transfers.get(transfer_id)
        if current is not None:
            _require(current["canon"] == canon, "TRANSFER_BINDING_CONFLICT")
            return self._transfer_env(current, duplicate=True)
        listing = self._listing(listing_id)
        _require(listing["state"] == "LISTED" and self._now < listing["expires_ms"], "LISTING_NOT_OPEN")
        _require(listing["payment_ref"] is not None, "PAYMENT_FACT_REQUIRED")
        right = self._right(listing["right_id"])
        _require(right["state"] == "ACTIVE", "RIGHT_NOT_ACTIVE")
        _require(right["version"] == listing["version"], "STALE_VERSION")
        _require(right["holder_role"] == listing["seller_role"], "NOT_HOLDER")
        _require(right["listing_id"] == listing["listing_id"], "RIGHT_SALE_LOCKED")
        show = self._show(right["show_id"])
        organizer_due, platform_due, seller_due = _allocation(
            listing["amount"], show["organizer_bps"], show["platform_bps"]
        )
        right["holder_role"] = listing["recipient_role"]
        right["version"] += 1
        right["listing_id"] = None
        right["admission_id"] = None
        right["last_payment"] = listing["payment_ref"]
        right["last_amount"] = listing["amount"]
        right["last_payer"] = listing["recipient_role"]
        listing["state"] = "ACCEPTED"
        evidence = {
            "transfer_id": transfer_id,
            "right_id": right["right_id"],
            "show_id": show["show_id"],
            "from_role": listing["seller_role"],
            "to_role": listing["recipient_role"],
            "version_after": right["version"],
            "amount": listing["amount"],
            "currency": "KRW",
            "payment_ref": listing["payment_ref"],
            "seller_due": seller_due,
            "organizer_due": organizer_due,
            "platform_due": platform_due,
            "funds_executed": False,
            "chain_owner_current": False,
        }
        transfer = {"canon": canon, "evidence": evidence, "right_id": right["right_id"], "listing_id": listing_id}
        self._transfers[transfer_id] = transfer
        self._invariant()
        return self._transfer_env(transfer, applied="accept_resale")

    def authorize_admission(
        self,
        admission_id: object,
        *,
        right_id: object,
        version: object,
        holder_role: object,
        gate_role: object,
        request: object,
        expires_ms: object,
    ) -> dict:
        admission_id = _ident(admission_id)
        right_id = _ident(right_id)
        holder_role = _ident(holder_role)
        gate_role = _ident(gate_role)
        request = _hex32(request, "ADMISSION_REQUEST")
        expires_ms = _ms(expires_ms, "ADMISSION_WINDOW")
        version = _version(version)
        binding = {
            "admission_id": admission_id,
            "right_id": right_id,
            "version": version,
            "holder_role": holder_role,
            "gate_role": gate_role,
            "request": request,
            "expires_ms": expires_ms,
        }
        canon = _canonical(binding)
        current = self._admissions.get(admission_id)
        if current is not None:
            _require(current["canon"] == canon, "ADMISSION_BINDING_CONFLICT")
            return self._admission_env(current, duplicate=True)
        right = self._right(right_id)
        show = self._show(right["show_id"])
        _require(right["state"] == "ACTIVE", "RIGHT_NOT_ACTIVE")
        _require(version == right["version"], "STALE_VERSION")
        _require(holder_role == right["holder_role"], "NOT_HOLDER")
        _require(gate_role in show["gate_roles"], "GATE_UNKNOWN")
        self._window(expires_ms, ADMISSION_WINDOW_MS, "ADMISSION_WINDOW")
        _require(self._live_listing(right) is None, "LISTING_LOCKED")
        _require(self._live_admission(right) is None, "ADMISSION_LOCKED")
        right["listing_id"] = None
        admission = {
            "canon": canon,
            "admission_id": admission_id,
            "right_id": right_id,
            "gate_role": gate_role,
            "request": request,
            "expires_ms": expires_ms,
            "version": version,
            "state": "AUTHORIZED",
        }
        right["admission_id"] = admission_id
        self._admissions[admission_id] = admission
        self._invariant()
        return self._admission_env(admission, applied="authorize_admission")

    def consume_admission(
        self,
        consume_id: object,
        *,
        right_id: object,
        version: object,
        gate_role: object,
        request: object,
    ) -> dict:
        consume_id = _ident(consume_id)
        right_id = _ident(right_id)
        gate_role = _ident(gate_role)
        request = _hex32(request, "ADMISSION_REQUEST")
        version = _version(version)
        canon = _canonical({
            "consume_id": consume_id,
            "right_id": right_id,
            "version": version,
            "gate_role": gate_role,
            "request": request,
        })
        current = self._consumes.get(consume_id)
        if current is not None:
            _require(current["canon"] == canon, "CONSUME_BINDING_CONFLICT")
            return self._consume_env(current, duplicate=True)
        right = self._right(right_id)
        show = self._show(right["show_id"])
        _require(right["state"] != "CONSUMED", "ALREADY_CONSUMED")
        _require(right["state"] == "ACTIVE", "RIGHT_NOT_ACTIVE")
        _require(version == right["version"], "STALE_VERSION")
        _require(gate_role in show["gate_roles"], "GATE_UNKNOWN")
        _require(right["admission_id"] is not None, "ADMISSION_REQUIRED")
        admission = self._admissions[right["admission_id"]]
        _require(admission["state"] == "AUTHORIZED", "ADMISSION_REQUIRED")
        _require(admission["version"] == version, "STALE_VERSION")
        _require(admission["gate_role"] == gate_role, "GATE_MISMATCH")
        _require(admission["request"] == request, "ADMISSION_REQUEST_MISMATCH")
        _require(self._now < admission["expires_ms"], "ADMISSION_EXPIRED")
        right["state"] = "CONSUMED"
        right["version"] += 1
        right["admission_id"] = None
        admission["state"] = "CONSUMED"
        evidence = {
            "consume_id": consume_id,
            "right_id": right_id,
            "show_id": show["show_id"],
            "gate_role": gate_role,
            "request": request,
            "version_after": right["version"],
            "decision": "CONSUMED_ONCE",
            "admission_routing_production": False,
            "private_proof_verified": False,
        }
        consume = {"canon": canon, "evidence": evidence, "right_id": right_id}
        self._consumes[consume_id] = consume
        self._invariant()
        return self._consume_env(consume, applied="consume_admission")

    def view_show(self, show_id: object) -> dict:
        return self._env(applied="view_show", show=self._show_view(self._show(show_id)))

    def view_right(self, right_id: object) -> dict:
        right = self._right(right_id)
        return self._env(applied="view_right", right=self._right_view(right), show=self._show_view(self._show(right["show_id"])))

    def _gate_roles(self, value: object) -> list[str]:
        _require(type(value) is list, "GATES_TYPE")
        _require(len(value) > 0, "GATES_EMPTY")
        _require(len(value) <= GATE_ROLE_LIMIT, "GATES_LIMIT")
        roles = [_ident(item) for item in value]
        _require(len(set(roles)) == len(roles), "GATES_DUPLICATE")
        return roles

    def _window(self, expires_ms: int, limit: int, code: str) -> None:
        _require(self._now < expires_ms <= self._now + limit, code)

    def _slot(self, value: object, show: dict) -> int:
        _require(type(value) is int and 0 <= value < show["capacity"], "SLOT")
        return value

    def _show(self, show_id: object) -> dict:
        show_id = _ident(show_id)
        show = self._shows.get(show_id)
        _require(show is not None, "UNKNOWN_SHOW")
        return show

    def _reservation(self, reservation_id: object) -> dict:
        reservation_id = _ident(reservation_id)
        reservation = self._reservations.get(reservation_id)
        _require(reservation is not None, "UNKNOWN_RESERVATION")
        return reservation

    def _order(self, order_id: object) -> dict:
        order_id = _ident(order_id)
        order = self._orders.get(order_id)
        _require(order is not None, "UNKNOWN_ORDER")
        return order

    def _right(self, right_id: object) -> dict:
        right_id = _ident(right_id)
        right = self._rights.get(right_id)
        _require(right is not None, "UNKNOWN_RIGHT")
        return right

    def _listing(self, listing_id: object) -> dict:
        listing_id = _ident(listing_id)
        listing = self._listings.get(listing_id)
        _require(listing is not None, "UNKNOWN_LISTING")
        return listing

    def _show_of_reservation(self, reservation_id: str) -> dict:
        return self._show(self._reservation(reservation_id)["show_id"])

    def _replay_payment(self, show: dict, payment_ref: str, canon: str) -> bool:
        previous = show["payment_facts"].get(payment_ref)
        if previous is None:
            return False
        _require(previous == canon, "PAYMENT_BINDING_CONFLICT")
        return True

    def _free_slot(self, reservation: dict) -> None:
        show = self._show(reservation["show_id"])
        row = show["slots"][reservation["slot"]]
        _require(row["state"] == "RESERVED" and row["reservation_id"] == reservation["reservation_id"], "MOCK_INVARIANT")
        _require(row["right_id"] is None, "MOCK_INVARIANT")
        row["state"] = "FREE"
        row["reservation_id"] = None

    def _live_listing(self, right: dict) -> dict | None:
        listing_id = right["listing_id"]
        if listing_id is None:
            return None
        listing = self._listings[listing_id]
        if listing["state"] == "LISTED" and self._now < listing["expires_ms"]:
            return listing
        return None

    def _live_admission(self, right: dict) -> dict | None:
        admission_id = right["admission_id"]
        if admission_id is None:
            return None
        admission = self._admissions[admission_id]
        if admission["state"] == "AUTHORIZED" and self._now < admission["expires_ms"]:
            return admission
        return None

    def _env(self, *, applied: str | None = None, duplicate: bool = False, **parts: object) -> dict:
        body = {
            "provenance": PROVENANCE,
            "duplicate": duplicate,
            "applied": applied,
            "logical_time_ms": self._now,
            **NON_CLAIMS,
        }
        body.update(parts)
        return body

    def _show_view(self, show: dict) -> dict:
        slots = []
        for slot in range(show["capacity"]):
            row = show["slots"][slot]
            slots.append({
                "slot": slot,
                "state": row["state"],
                "reservation_id": row["reservation_id"],
                "right_id": row["right_id"],
            })
        return {
            "show_id": show["show_id"],
            "organizer_role": show["organizer_role"],
            "currency": "KRW",
            "capacity": show["capacity"],
            "primary_price": show["primary_price"],
            "resale_cap": show["resale_cap"],
            "resale_allowed": show["resale_allowed"],
            "organizer_bps": show["organizer_bps"],
            "platform_bps": show["platform_bps"],
            "gate_roles": list(show["gate_roles"]),
            "open": show["open"],
            "slots": slots,
            "payment_ref_count": len(show["payment_facts"]),
        }

    def _reservation_view(self, reservation: dict) -> dict:
        return {
            "reservation_id": reservation["reservation_id"],
            "show_id": reservation["show_id"],
            "slot": reservation["slot"],
            "buyer_role": reservation["buyer_role"],
            "expires_ms": reservation["expires_ms"],
            "state": reservation["state"],
            "expired": reservation["state"] == "OPEN" and self._now >= reservation["expires_ms"],
            "order_id": reservation["order_id"],
        }

    def _order_view(self, order: dict) -> dict:
        return {
            "order_id": order["order_id"],
            "reservation_id": order["reservation_id"],
            "buyer_role": order["buyer_role"],
            "amount": order["amount"],
            "currency": order["currency"],
            "quote_ref": order["quote_ref"],
            "state": order["state"],
            "payment_ref": order["payment_ref"],
            "issuance_id": order["issuance_id"],
        }

    def _right_view(self, right: dict) -> dict:
        listing = self._live_listing(right)
        admission = self._live_admission(right)
        return {
            "right_id": right["right_id"],
            "show_id": right["show_id"],
            "slot": right["slot"],
            "holder_role": right["holder_role"],
            "state": right["state"],
            "version": right["version"],
            "generation": right["generation"],
            "listing_id": None if listing is None else listing["listing_id"],
            "admission_id": None if admission is None else admission["admission_id"],
            "last_payment": right["last_payment"],
            "last_amount": right["last_amount"],
            "last_payer": right["last_payer"],
        }

    def _listing_view(self, listing: dict) -> dict:
        right = self._rights[listing["right_id"]]
        expired = listing["state"] == "LISTED" and self._now >= listing["expires_ms"]
        attached = (
            listing["state"] == "LISTED"
            and not expired
            and right["listing_id"] == listing["listing_id"]
        )
        return {
            "listing_id": listing["listing_id"],
            "right_id": listing["right_id"],
            "seller_role": listing["seller_role"],
            "recipient_role": listing["recipient_role"],
            "amount": listing["amount"],
            "expires_ms": listing["expires_ms"],
            "version": listing["version"],
            "state": listing["state"],
            "expired": expired,
            "attached": attached,
            "payment_ref": listing["payment_ref"],
        }

    def _admission_view(self, admission: dict) -> dict:
        right = self._rights[admission["right_id"]]
        expired = admission["state"] == "AUTHORIZED" and self._now >= admission["expires_ms"]
        attached = (
            admission["state"] == "AUTHORIZED"
            and not expired
            and right["admission_id"] == admission["admission_id"]
        )
        return {
            "admission_id": admission["admission_id"],
            "right_id": admission["right_id"],
            "gate_role": admission["gate_role"],
            "request": admission["request"],
            "expires_ms": admission["expires_ms"],
            "version": admission["version"],
            "state": admission["state"],
            "expired": expired,
            "attached": attached,
        }

    def _reservation_env(self, reservation: dict, **flags: object) -> dict:
        show = self._show(reservation["show_id"])
        return self._env(
            show=self._show_view(show),
            reservation=self._reservation_view(reservation),
            **flags,
        )

    def _order_env(self, order: dict, **flags: object) -> dict:
        reservation = self._reservation(order["reservation_id"])
        return self._env(
            show=self._show_view(self._show(reservation["show_id"])),
            reservation=self._reservation_view(reservation),
            order=self._order_view(order),
            **flags,
        )

    def _issue_env(self, issuance: dict, **flags: object) -> dict:
        right = self._right(issuance["right_id"])
        return self._env(
            evidence=dict(issuance["evidence"]),
            right=self._right_view(right),
            show=self._show_view(self._show(right["show_id"])),
            **flags,
        )

    def _listing_env(self, listing: dict, **flags: object) -> dict:
        right = self._right(listing["right_id"])
        return self._env(
            listing=self._listing_view(listing),
            right=self._right_view(right),
            **flags,
        )

    def _transfer_env(self, transfer: dict, **flags: object) -> dict:
        right = self._right(transfer["right_id"])
        listing = self._listing(transfer["listing_id"])
        return self._env(
            evidence=dict(transfer["evidence"]),
            listing=self._listing_view(listing),
            right=self._right_view(right),
            **flags,
        )

    def _admission_env(self, admission: dict, **flags: object) -> dict:
        right = self._right(admission["right_id"])
        return self._env(
            admission=self._admission_view(admission),
            right=self._right_view(right),
            **flags,
        )

    def _consume_env(self, consume: dict, **flags: object) -> dict:
        right = self._right(consume["right_id"])
        return self._env(
            evidence=dict(consume["evidence"]),
            right=self._right_view(right),
            **flags,
        )

    def _invariant(self) -> None:
        issued_ids = set()
        for show in self._shows.values():
            seen_refs = set(show["payment_facts"])
            _require(len(seen_refs) == len(show["payment_facts"]), "MOCK_INVARIANT")
            for slot, row in show["slots"].items():
                _require(0 <= slot < show["capacity"], "MOCK_INVARIANT")
                if row["state"] == "FREE":
                    _require(row["reservation_id"] is None and row["right_id"] is None, "MOCK_INVARIANT")
                elif row["state"] == "RESERVED":
                    reservation = self._reservations.get(row["reservation_id"])
                    _require(reservation is not None and reservation["state"] == "OPEN", "MOCK_INVARIANT")
                    _require(reservation["slot"] == slot and row["right_id"] is None, "MOCK_INVARIANT")
                elif row["state"] == "ISSUED":
                    right = self._rights.get(row["right_id"])
                    reservation = self._reservations.get(row["reservation_id"])
                    _require(right is not None and right["slot"] == slot and right["show_id"] == show["show_id"], "MOCK_INVARIANT")
                    _require(reservation is not None and reservation["state"] == "ISSUED", "MOCK_INVARIANT")
                    issued_ids.add(right["right_id"])
                else:
                    _require(False, "MOCK_INVARIANT")
            _require(show["organizer_bps"] + show["platform_bps"] <= 10000, "MOCK_INVARIANT")
        _require(issued_ids == set(self._rights), "MOCK_INVARIANT")
        for order in self._orders.values():
            if order["state"] == "ISSUED":
                _require(order["issuance_id"] in self._rights and order["payment_ref"] is not None, "MOCK_INVARIANT")
            if order["payment_ref"] is not None:
                _require(order["state"] in ("OPEN", "ISSUED"), "MOCK_INVARIANT")
        for listing in self._listings.values():
            if listing["state"] == "ACCEPTED":
                _require(listing["payment_ref"] is not None, "MOCK_INVARIANT")
        for right in self._rights.values():
            _require(right["generation"] == 1, "MOCK_INVARIANT")
            _require(right["state"] in ("ACTIVE", "CONSUMED"), "MOCK_INVARIANT")
