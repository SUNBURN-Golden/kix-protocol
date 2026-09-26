"""In-memory acceptance machine for resale listing and ownership transfer.

The machine decides which list, hold, payment, and transfer commands are
accepted, then replays that journal deterministically. Listing, price, and
holder predicates stay in mock_gates.py. Reservation lifecycle commands stay
on ReservationMachine. This module does not add protocol_contract commands.

A bound transfer reads an injected settlement machine's view. It does not
call settlement commands and does not move money. The holder and version
change is not a venue credential reissue. `economic_finality_claimed` and
`venue_credential_reissued` stay false.

Provenance remains MOCK_GATE_ONLY. A matched replay is equality of this
process's journal and views, not a marketplace, a bank debit, or chain
finality. Buyer races here are ordered commands in one process.
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
LISTED = "LISTED"
BUY_HELD = "BUY_HELD"
PAYMENT_NOTED = "PAYMENT_NOTED"
TRANSFERRED = "TRANSFERRED"
CLOSED = "CLOSED"
CANCELLED = "CANCELLED"

OPEN_PHASES = frozenset({LISTED, BUY_HELD, PAYMENT_NOTED})
TERMINAL_PHASES = frozenset({CLOSED, CANCELLED})
ISSUED_AUTHORITY = frozenset({"ISSUED", "ADMISSION_AUTHORIZED"})

REPLAYABLE = frozenset(
    {
        "set_clock",
        "adopt_issued",
        "list_resale",
        "hold_buy",
        "release_hold",
        "cancel_listing",
        "observe_resale_payment",
        "bind_settlement",
        "accept_resale",
        "close",
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

_ALLOWED = {
    "hold_buy": frozenset({LISTED}),
    "release_hold": frozenset({BUY_HELD}),
    "cancel_listing": frozenset({LISTED, BUY_HELD}),
    "observe_resale_payment": frozenset({LISTED, BUY_HELD}),
    "bind_settlement": frozenset({LISTED, BUY_HELD, PAYMENT_NOTED}),
    "accept_resale": frozenset({PAYMENT_NOTED}),
    "close": frozenset({TRANSFERRED}),
}

_SPECIFIC = {
    ("cancel_listing", PAYMENT_NOTED): "COMPENSATION_UNDEFINED",
    ("observe_resale_payment", PAYMENT_NOTED): "LISTING_PAYMENT_BOUND",
    ("hold_buy", BUY_HELD): "BUYER_HOLD_LOCKED",
}


class ResaleError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise ResaleError(code)


def _lift(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except GateError as error:
        raise ResaleError(error.code) from error


def _id(value: object, code: str = "INVALID_ID") -> str:
    return _lift(_ident, value, code)


def _copy(value: object) -> object:
    return json.loads(_canonical(value))


def _source_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ResaleError:
        raise
    except Exception as error:
        code = getattr(error, "code", None)
        if type(code) is str:
            raise ResaleError(code) from error
        raise


class ResaleMachine:
    def __init__(self, ticket_source: object | None = None, settlement_source: object | None = None) -> None:
        self._gates = MockGates()
        self._tickets = ticket_source
        self._settlement = settlement_source
        self._now = 0
        self._journal: list[dict] = []
        self._idempotency: dict[str, dict] = {}
        self._rights: dict[str, dict] = {}
        self._listings: dict[str, dict] = {}
        self._holds: dict[str, dict] = {}
        self._transfers: dict[str, str] = {}

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
            canon = _canonical(normalized | {"right_id": normalized["right_id"]})
            current = self._rights.get(normalized["right_id"])
            if current is not None:
                _require(current["canon"] == canon, "ISSUANCE_BINDING_CONFLICT")
                raise ResaleError("ILLEGAL_TRANSITION")
            self._match_authority(normalized)
            self._materialize(normalized)
            ticket = {
                "canon": canon,
                "right_id": normalized["right_id"],
                "reservation_id": normalized["reservation_id"],
                "show_id": normalized["show_id"],
                "slot": normalized["slot"],
                "holder_role": normalized["buyer_role"],
                "version": 1,
                "active_listing_id": None,
                "last_transfer_id": None,
                "subject_ids": [normalized["right_id"]],
            }
            self._rights[normalized["right_id"]] = ticket
            self._invariant()
            body = {name: normalized[name] for name in _ADOPT_FIELDS}
            return self._accept(
                key,
                request,
                "adopt_issued",
                normalized["right_id"],
                body,
                record=ticket,
            )

        return self._call("adopt_issued", right_id, idempotency_key, raw, execute)

    def list_resale(
        self,
        listing_id: object,
        *,
        idempotency_key: object,
        right_id: object,
        version: object,
        seller_role: object,
        recipient_role: object,
        amount: object,
        expires_ms: object,
        reservation_id: object = None,
    ) -> dict:
        raw = {
            "right_id": right_id,
            "version": version,
            "seller_role": seller_role,
            "recipient_role": recipient_role,
            "amount": amount,
            "expires_ms": expires_ms,
            "reservation_id": reservation_id,
        }

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(listing_id)
            right = _id(right_id)
            seller = _id(seller_role)
            recipient = _id(recipient_role)
            price = _lift(_money, amount)
            expires = _lift(_ms, expires_ms, "LISTING_WINDOW")
            listed_version = _lift(_version, version)
            bound_reservation = None if reservation_id is None else _id(reservation_id)
            binding = {
                "listing_id": normalized_id,
                "right_id": right,
                "version": listed_version,
                "seller_role": seller,
                "recipient_role": recipient,
                "amount": price,
                "expires_ms": expires,
                "reservation_id": bound_reservation,
            }
            canon = _canonical(binding)
            current = self._listings.get(normalized_id)
            if current is not None:
                _require(current["canon"] == canon, "LISTING_BINDING_CONFLICT")
                if current["phase"] in TERMINAL_PHASES:
                    raise ResaleError("TERMINAL_IMMUTABLE")
                raise ResaleError("ILLEGAL_TRANSITION")
            ticket = self._rights.get(right)
            authority_id = bound_reservation
            if authority_id is None and ticket is not None:
                authority_id = ticket["reservation_id"]
            if authority_id is not None or self._tickets is not None:
                _require(authority_id is not None, "TICKET_NOT_ISSUED")
                _require(self._tickets is not None, "TICKET_SOURCE_REQUIRED")
                self._require_authority(
                    authority_id,
                    right_id=right,
                    seller_role=seller,
                    version=listed_version,
                )
            _require(ticket is not None, "UNKNOWN_RIGHT")
            if ticket["reservation_id"] is not None and bound_reservation not in (None, ticket["reservation_id"]):
                raise ResaleError("RESERVATION_BINDING_CONFLICT")
            _require(self._live_listing_id(ticket) is None, "RIGHT_SALE_LOCKED")
            _require(seller == ticket["holder_role"], "NOT_HOLDER")
            _require(listed_version == ticket["version"], "STALE_VERSION")
            result = _lift(
                self._gates.list_resale,
                normalized_id,
                right_id=right,
                version=listed_version,
                seller_role=seller,
                recipient_role=recipient,
                amount=price,
                expires_ms=expires,
            )
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            listing = {
                "canon": canon,
                "listing_id": normalized_id,
                "phase": LISTED,
                "right_id": right,
                "show_id": ticket["show_id"],
                "seller_role": seller,
                "recipient_role": recipient,
                "amount": price,
                "expires_ms": expires,
                "version": listed_version,
                "version_after": None,
                "payment_ref": None,
                "hold_id": None,
                "buyer_role": None,
                "settlement_id": None,
                "mock_settlement_commit_observed": False,
                "transfer_id": None,
                "subject_ids": [normalized_id],
            }
            self._listings[normalized_id] = listing
            ticket["active_listing_id"] = normalized_id
            self._invariant()
            return self._accept(
                key,
                request,
                "list_resale",
                normalized_id,
                {name: binding[name] for name in raw},
                record=listing,
            )

        return self._call("list_resale", listing_id, idempotency_key, raw, execute)

    def hold_buy(
        self,
        hold_id: object,
        *,
        idempotency_key: object,
        listing_id: object,
        buyer_role: object,
    ) -> dict:
        raw = {"listing_id": listing_id, "buyer_role": buyer_role}

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(hold_id)
            listing_key = _id(listing_id)
            buyer = _id(buyer_role)
            canon = _canonical({"hold_id": normalized_id, "listing_id": listing_key, "buyer_role": buyer})
            prior = self._holds.get(normalized_id)
            if prior is not None:
                _require(prior["canon"] == canon, "HOLD_BINDING_CONFLICT")
                raise ResaleError("ILLEGAL_TRANSITION")
            listing = self._listing(listing_key)
            self._enter(listing, "hold_buy")
            _require(self._now < listing["expires_ms"], "LISTING_NOT_OPEN")
            _require(buyer == listing["recipient_role"], "RECIPIENT_MISMATCH")
            listing["hold_id"] = normalized_id
            listing["buyer_role"] = buyer
            listing["phase"] = BUY_HELD
            self._holds[normalized_id] = {"canon": canon, "listing_id": listing_key}
            self._invariant()
            return self._accept(
                key,
                request,
                "hold_buy",
                normalized_id,
                {"listing_id": listing_key, "buyer_role": buyer},
                record=listing,
            )

        return self._call("hold_buy", hold_id, idempotency_key, raw, execute)

    def release_hold(self, hold_id: object, *, idempotency_key: object, buyer_role: object) -> dict:
        raw = {"buyer_role": buyer_role}

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(hold_id)
            buyer = _id(buyer_role)
            hold = self._holds.get(normalized_id)
            _require(hold is not None, "UNKNOWN_HOLD")
            listing = self._listing(hold["listing_id"])
            self._enter(listing, "release_hold")
            _require(buyer == listing["buyer_role"], "BUYER_MISMATCH")
            listing["phase"] = LISTED
            listing["hold_id"] = None
            listing["buyer_role"] = None
            self._invariant()
            return self._accept(
                key,
                request,
                "release_hold",
                normalized_id,
                {"buyer_role": buyer},
                record=listing,
            )

        return self._call("release_hold", hold_id, idempotency_key, raw, execute)

    def cancel_listing(self, listing_id: object, *, idempotency_key: object, seller_role: object) -> dict:
        raw = {"seller_role": seller_role}

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(listing_id)
            seller = _id(seller_role)
            listing = self._listing(normalized_id)
            self._enter(listing, "cancel_listing")
            _require(seller == listing["seller_role"], "NOT_HOLDER")
            result = _lift(self._gates.cancel_listing, normalized_id, seller_role=seller)
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            listing["phase"] = CANCELLED
            listing["hold_id"] = None
            listing["buyer_role"] = None
            ticket = self._rights[listing["right_id"]]
            if ticket["active_listing_id"] == normalized_id:
                ticket["active_listing_id"] = None
            self._invariant()
            return self._accept(
                key,
                request,
                "cancel_listing",
                normalized_id,
                {"seller_role": seller},
                record=listing,
            )

        return self._call("cancel_listing", listing_id, idempotency_key, raw, execute)

    def observe_resale_payment(
        self,
        listing_id: object,
        *,
        idempotency_key: object,
        payment_ref: object,
        amount: object,
        buyer_role: object = None,
    ) -> dict:
        raw = {"payment_ref": payment_ref, "amount": amount, "buyer_role": buyer_role}

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(listing_id)
            payment = _lift(_hex32, payment_ref, "PAYMENT_REF")
            price = _lift(_money, amount)
            buyer = None if buyer_role is None else _id(buyer_role)
            listing = self._listing(normalized_id)
            self._enter(listing, "observe_resale_payment")
            if listing["phase"] == BUY_HELD:
                _require(buyer == listing["buyer_role"], "BUYER_MISMATCH")
            elif buyer is not None:
                _require(buyer == listing["recipient_role"], "RECIPIENT_MISMATCH")
            result = _lift(
                self._gates.observe_resale_payment,
                payment,
                listing_id=normalized_id,
                amount=price,
            )
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            listing["payment_ref"] = payment
            listing["phase"] = PAYMENT_NOTED
            self._invariant()
            return self._accept(
                key,
                request,
                "observe_resale_payment",
                normalized_id,
                {"payment_ref": payment, "amount": price, "buyer_role": buyer},
                record=listing,
            )

        return self._call("observe_resale_payment", listing_id, idempotency_key, raw, execute)

    def bind_settlement(
        self,
        listing_id: object,
        *,
        idempotency_key: object,
        settlement_id: object,
    ) -> dict:
        raw = {"settlement_id": settlement_id}

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(listing_id)
            settlement_key = _id(settlement_id)
            listing = self._listing(normalized_id)
            self._enter(listing, "bind_settlement")
            if listing["settlement_id"] is not None:
                _require(listing["settlement_id"] == settlement_key, "SETTLEMENT_BINDING_CONFLICT")
                raise ResaleError("ILLEGAL_TRANSITION")
            listing["settlement_id"] = settlement_key
            self._invariant()
            return self._accept(
                key,
                request,
                "bind_settlement",
                normalized_id,
                {"settlement_id": settlement_key},
                record=listing,
            )

        return self._call("bind_settlement", listing_id, idempotency_key, raw, execute)

    def accept_resale(self, transfer_id: object, *, idempotency_key: object, listing_id: object) -> dict:
        raw = {"listing_id": listing_id}

        def execute(key: str, request: str) -> dict:
            normalized_transfer = _id(transfer_id)
            normalized_listing = _id(listing_id)
            canon = _canonical({"transfer_id": normalized_transfer, "listing_id": normalized_listing})
            prior = self._transfers.get(normalized_transfer)
            if prior is not None:
                _require(prior == canon, "TRANSFER_BINDING_CONFLICT")
            listing = self._listing(normalized_listing)
            self._enter(listing, "accept_resale")
            _require(self._now < listing["expires_ms"], "LISTING_NOT_OPEN")
            ticket = self._rights[listing["right_id"]]
            if ticket["reservation_id"] is not None:
                _require(self._tickets is not None, "TICKET_SOURCE_REQUIRED")
                self._require_authority(
                    ticket["reservation_id"],
                    right_id=listing["right_id"],
                    seller_role=listing["seller_role"],
                    version=listing["version"],
                )
            current = self._public_right(listing["right_id"])
            _require(current["state"] == "ACTIVE", "RIGHT_NOT_ACTIVE")
            _require(current["holder_role"] == listing["seller_role"], "NOT_HOLDER")
            _require(current["version"] == listing["version"], "STALE_VERSION")
            observed = self._settlement_allows(listing)
            result = _lift(self._gates.accept_resale, normalized_transfer, listing_id=normalized_listing)
            _require(result["duplicate"] is False, "MOCK_INVARIANT")
            evidence = dict(result["evidence"])
            _require(evidence["funds_executed"] is False, "MOCK_INVARIANT")
            _require(evidence["chain_owner_current"] is False, "MOCK_INVARIANT")
            _require(evidence["right_id"] == listing["right_id"], "MOCK_INVARIANT")
            _require(evidence["version_after"] == listing["version"] + 1, "MOCK_INVARIANT")
            _require(evidence["from_role"] == listing["seller_role"], "MOCK_INVARIANT")
            _require(evidence["to_role"] == listing["recipient_role"], "MOCK_INVARIANT")
            moved = self._public_right(listing["right_id"])
            _require(moved["generation"] == 1, "MOCK_INVARIANT")
            _require(moved["state"] == "ACTIVE", "MOCK_INVARIANT")
            _require(moved["holder_role"] == listing["recipient_role"], "MOCK_INVARIANT")
            _require(moved["version"] == evidence["version_after"], "MOCK_INVARIANT")
            _require(moved["listing_id"] is None, "MOCK_INVARIANT")
            listing["phase"] = TRANSFERRED
            listing["transfer_id"] = normalized_transfer
            listing["version_after"] = evidence["version_after"]
            listing["mock_settlement_commit_observed"] = observed
            listing["hold_id"] = None
            listing["buyer_role"] = None
            if ticket["active_listing_id"] == normalized_listing:
                ticket["active_listing_id"] = None
            ticket["holder_role"] = moved["holder_role"]
            ticket["version"] = moved["version"]
            ticket["last_transfer_id"] = normalized_transfer
            self._transfers[normalized_transfer] = canon
            self._invariant()
            return self._accept(
                key,
                request,
                "accept_resale",
                normalized_transfer,
                {"listing_id": normalized_listing},
                record=listing,
                evidence=evidence,
            )

        return self._call("accept_resale", transfer_id, idempotency_key, raw, execute)

    def close(self, listing_id: object, *, idempotency_key: object) -> dict:
        def execute(key: str, request: str) -> dict:
            normalized_id = _id(listing_id)
            listing = self._listing(normalized_id)
            self._enter(listing, "close")
            listing["phase"] = CLOSED
            self._invariant()
            return self._accept(key, request, "close", normalized_id, {}, record=listing)

        return self._call("close", listing_id, idempotency_key, {}, execute)

    def reconcile(self, listing_id: object, *, idempotency_key: object) -> dict:
        """Replay the journal and require the views to match.

        The receipt is process-local. restore rebuilds accepted commands and
        does not store this receipt.
        """

        def execute(key: str, request: str) -> dict:
            normalized_id = _id(listing_id)
            listing = self._listing(normalized_id)
            restored = ResaleMachine.restore(
                self.export_journal(),
                ticket_source=self._tickets,
                settlement_source=self._settlement,
            )
            _require(restored.canonical_state() == self.canonical_state(), "MOCK_INVARIANT")
            result = self._envelope(
                applied="reconcile",
                listing=self._listing_view(listing),
                matched=True,
                state_digest=self.state_digest(),
                entry_count=len(self._journal),
            )
            encoded = _canonical(result)
            self._idempotency[key] = {"request": request, "result": encoded, "error": None}
            return json.loads(encoded)

        return self._call("reconcile", listing_id, idempotency_key, {}, execute)

    def reject_external(self, kind: object) -> None:
        """Refuse marketplace transport, KYC, venue reissue, or a live charge.

        The kind is an external-attempt label. This method never dispatches
        list, payment, transfer, or any other accepted command.
        """

        _id(kind)
        raise ResaleError("EXTERNAL_UNSUPPORTED")

    def view(self, listing_id: object) -> dict:
        return self._listing_view(self._listing(_id(listing_id)))

    def view_right(self, right_id: object) -> dict:
        ticket = self._rights.get(_id(right_id))
        _require(ticket is not None, "UNKNOWN_RIGHT")
        return self._envelope(applied="view_right", ticket=self._ticket_view(ticket), right=self._public_right(ticket["right_id"]))

    def view_presentation(self, right_id: object, *, version: object, holder_role: object) -> dict:
        """Report whether a version and holder still match the current right.

        A live listing, a consumed or replaced holder, or a stale version does
        not match. This is not a venue scan and does not reissue a credential.
        """

        normalized = _id(right_id)
        holder = _id(holder_role)
        current_version = _lift(_version, version)
        ticket = self._rights.get(normalized)
        _require(ticket is not None, "UNKNOWN_RIGHT")
        right = self._public_right(normalized)
        matches = (
            right["state"] == "ACTIVE"
            and right["version"] == current_version
            and right["holder_role"] == holder
            and right["listing_id"] is None
        )
        presentation = {
            "right_id": normalized,
            "version": current_version,
            "holder_role": holder,
            "matches_current_right": matches,
            "current_version": right["version"],
            "current_holder_role": right["holder_role"],
            "venue_credential_reissued": False,
            "admission_routing_production": False,
        }
        return self._envelope(applied="view_presentation", presentation=presentation, right=right)

    def export_journal(self) -> list:
        return _copy(self._journal)

    def canonical_state(self) -> str:
        show_ids = sorted({ticket["show_id"] for ticket in self._rights.values()})
        payload = {
            "logical_time_ms": self._now,
            "shows": [self._show_public(show_id) for show_id in show_ids],
            "tickets": [self._ticket_view(self._rights[right_id]) for right_id in sorted(self._rights)],
            "listings": [self._listing_view(self._listings[listing_id]) for listing_id in sorted(self._listings)],
            "journal": self._journal,
        }
        return _canonical(payload)

    def state_digest(self) -> str:
        return hashlib.sha256(self.canonical_state().encode("utf-8")).hexdigest()

    @classmethod
    def restore(
        cls,
        journal: object,
        ticket_source: object | None = None,
        settlement_source: object | None = None,
    ) -> ResaleMachine:
        _require(type(journal) is list, "INVALID_JOURNAL")
        machine = cls(ticket_source, settlement_source)
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
                raise ResaleError("INVALID_JOURNAL") from error
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
        normalized["capacity"] = raw["capacity"]
        normalized["gate_roles"] = gates
        normalized["resale_allowed"] = raw["resale_allowed"]
        normalized["organizer_bps"] = organizer_bps
        normalized["platform_bps"] = platform_bps
        normalized["slot"] = raw["slot"]
        return normalized

    def _materialize(self, normalized: dict) -> None:
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
            normalized["reservation_id"] if normalized["reservation_id"] is not None else normalized["right_id"],
            show_id=normalized["show_id"],
            slot=normalized["slot"],
            buyer_role=normalized["buyer_role"],
            expires_ms=normalized["expires_ms"],
        )
        _require(reserved["duplicate"] is False, "MOCK_INVARIANT")
        ordered = _lift(
            self._gates.bind_order,
            normalized["order_id"],
            reservation_id=normalized["reservation_id"] if normalized["reservation_id"] is not None else normalized["right_id"],
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
        _require(right["listing_id"] is None, "MOCK_INVARIANT")

    def _match_authority(self, normalized: dict) -> None:
        if normalized["reservation_id"] is None and self._tickets is None:
            return
        _require(normalized["reservation_id"] is not None, "TICKET_NOT_ISSUED")
        _require(self._tickets is not None, "TICKET_SOURCE_REQUIRED")
        view = self._require_authority(
            normalized["reservation_id"],
            right_id=normalized["right_id"],
            seller_role=normalized["buyer_role"],
            version=1,
        )
        _require(view.get("show_id") == normalized["show_id"], "SHOW_BINDING_CONFLICT")
        _require(view.get("slot") == normalized["slot"], "RESERVATION_BINDING_CONFLICT")
        _require(view.get("buyer_role") == normalized["buyer_role"], "RESERVATION_BINDING_CONFLICT")
        _require(view.get("expires_ms") == normalized["expires_ms"], "RESERVATION_BINDING_CONFLICT")
        _require(view.get("order_id") == normalized["order_id"], "ORDER_BINDING_CONFLICT")
        _require(view.get("amount") == normalized["amount"], "PRIMARY_PRICE_MISMATCH")
        _require(view.get("quote_ref") == normalized["quote_ref"], "ORDER_BINDING_CONFLICT")
        _require(view.get("payment_ref") == normalized["payment_ref"], "PAYMENT_BINDING_CONFLICT")
        show = _source_call(self._tickets.view_show, normalized["show_id"])
        _require(type(show) is dict and type(show.get("show")) is dict, "UNKNOWN_SHOW")
        snapshot = show["show"]
        for name in (
            "organizer_role",
            "capacity",
            "primary_price",
            "resale_cap",
            "resale_allowed",
            "organizer_bps",
            "platform_bps",
        ):
            _require(snapshot.get(name) == normalized[name], "SHOW_BINDING_CONFLICT")
        _require(list(snapshot.get("gate_roles") or []) == normalized["gate_roles"], "SHOW_BINDING_CONFLICT")

    def _require_authority(
        self,
        reservation_id: str,
        *,
        right_id: str | None = None,
        seller_role: str | None = None,
        version: int | None = None,
    ) -> dict:
        view = _source_call(self._tickets.view, reservation_id)
        _require(type(view) is dict, "TICKET_NOT_ISSUED")
        phase = view.get("phase")
        right = view.get("right")
        if phase == "CANCELLED":
            raise ResaleError("TICKET_CANCELLED")
        if phase == "CONSUMED" or (type(right) is dict and right.get("state") == "CONSUMED"):
            raise ResaleError("ALREADY_CONSUMED")
        if phase not in ISSUED_AUTHORITY:
            raise ResaleError("TICKET_NOT_ISSUED")
        _require(type(right) is dict and right.get("state") == "ACTIVE", "RIGHT_NOT_ACTIVE")
        if view.get("admission_id") is not None:
            raise ResaleError("ADMISSION_LOCKED")
        _require(view.get("economic_finality_claimed") is False, "SETTLEMENT_VIEW_REJECTED")
        _require(view.get("funds_executed") is False, "SETTLEMENT_VIEW_REJECTED")
        if right_id is not None:
            _require(view.get("issuance_id") == right_id and right.get("right_id") == right_id, "UNKNOWN_RIGHT")
        if seller_role is not None:
            _require(right.get("holder_role") == seller_role, "NOT_HOLDER")
        if version is not None:
            _require(type(right.get("version")) is int and right.get("version") == version, "STALE_VERSION")
        return view

    def _settlement_allows(self, listing: dict) -> bool:
        if listing["settlement_id"] is None:
            return False
        _require(self._settlement is not None, "SETTLEMENT_SOURCE_REQUIRED")
        view = _source_call(self._settlement.view, listing["settlement_id"])
        _require(type(view) is dict, "SETTLEMENT_NOT_COMMITTED")
        _require(view.get("phase") == "COMMITTED", "SETTLEMENT_NOT_COMMITTED")
        gross = view.get("gross")
        _require(
            view.get("currency") == "KRW" and type(gross) is int and gross == listing["amount"],
            "SETTLEMENT_AMOUNT_MISMATCH",
        )
        for name in _SETTLEMENT_FINALITY_FLAGS:
            _require(view.get(name) is False, "SETTLEMENT_VIEW_REJECTED")
        return True

    def _enter(self, listing: dict, op: str) -> None:
        phase = listing["phase"]
        specific = _SPECIFIC.get((op, phase))
        if specific is not None:
            raise ResaleError(specific)
        if phase in _ALLOWED[op]:
            return
        if phase in TERMINAL_PHASES:
            raise ResaleError("TERMINAL_IMMUTABLE")
        raise ResaleError("ILLEGAL_TRANSITION")

    def _listing(self, listing_id: str) -> dict:
        listing = self._listings.get(listing_id)
        _require(listing is not None, "UNKNOWN_LISTING")
        return listing

    def _live_listing_id(self, ticket: dict) -> str | None:
        listing_id = ticket["active_listing_id"]
        if listing_id is None:
            return None
        listing = self._listings[listing_id]
        if listing["phase"] in OPEN_PHASES and self._now < listing["expires_ms"]:
            return listing_id
        return None

    def _presentation_current(self, listing: dict, right: dict) -> bool:
        if listing["phase"] in (TRANSFERRED, CLOSED):
            return False
        return (
            right["state"] == "ACTIVE"
            and right["version"] == listing["version"]
            and right["holder_role"] == listing["seller_role"]
        )

    def _call(self, op: str, subject_id: object, idempotency_key: object, raw: dict, execute) -> dict:
        key = _id(idempotency_key)
        request = self._fingerprint(op, subject_id, raw)
        if request is not None:
            replayed = self._replay_if_known(key, request)
            if replayed is not None:
                return replayed
        try:
            return execute(key, request)
        except ResaleError as error:
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
            raise ResaleError(prior["error"])
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
        record: dict | None = None,
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
        if record is not None and subject_id not in record["subject_ids"]:
            record["subject_ids"].append(subject_id)
        if record is not None and "listing_id" in record:
            extra["listing"] = self._listing_view(record)
            extra["right"] = self._public_right(record["right_id"])
        elif record is not None and "right_id" in record:
            extra["ticket"] = self._ticket_view(record)
            extra["right"] = self._public_right(record["right_id"])
        result = self._envelope(applied=op, **extra)
        self._idempotency[key] = {"request": request, "result": _canonical(result), "error": None}
        return _copy(result)

    def _force_non_claims(self, result: dict) -> None:
        result["economic_finality_claimed"] = False
        result["funds_executed"] = False
        result["venue_credential_reissued"] = False
        result["external_marketplace"] = "UNSUPPORTED"
        for name in ("listing", "ticket", "presentation"):
            body = result.get(name)
            if type(body) is dict:
                body["economic_finality_claimed"] = False
                body["funds_executed"] = False
                body["venue_credential_reissued"] = False
        evidence = result.get("evidence")
        if type(evidence) is dict:
            evidence["funds_executed"] = False
            evidence["chain_owner_current"] = False

    def _envelope(self, *, applied: str, **extra: object) -> dict:
        body = {
            "provenance": PROVENANCE,
            "lifecycle_authority": AUTHORITY,
            "duplicate": False,
            "applied": applied,
            "logical_time_ms": self._now,
            "external_marketplace": "UNSUPPORTED",
            "external_payment": "UNSUPPORTED",
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
        body["external_marketplace"] = "UNSUPPORTED"
        body["external_payment"] = "UNSUPPORTED"
        return body

    def _public_right(self, right_id: str) -> dict:
        body = _lift(self._gates.view_right, right_id)
        _require(body["logical_time_ms"] == self._now, "MOCK_INVARIANT")
        return body["right"]

    def _show_public(self, show_id: str) -> dict:
        body = _lift(self._gates.view_show, show_id)
        _require(body["logical_time_ms"] == self._now, "MOCK_INVARIANT")
        return body["show"]

    def _slot_row(self, ticket: dict) -> dict:
        for row in self._show_public(ticket["show_id"])["slots"]:
            if row["slot"] == ticket["slot"]:
                return row
        raise ResaleError("MOCK_INVARIANT")

    def _settlement_gate(self, listing: dict) -> str:
        if listing["mock_settlement_commit_observed"]:
            return "MOCK_COMMIT_OBSERVED"
        if listing["settlement_id"] is None:
            return "UNBOUND"
        return "BOUND"

    def _entry_count(self, subjects: list) -> int:
        wanted = set(subjects)
        return sum(1 for entry in self._journal if entry["subject_id"] in wanted)

    def _ticket_view(self, ticket: dict) -> dict:
        live = self._live_listing_id(ticket)
        view = {
            "provenance": PROVENANCE,
            "lifecycle_authority": AUTHORITY,
            "right_id": ticket["right_id"],
            "sale_phase": None if live is None else self._listings[live]["phase"],
            "eligible": live is None,
            "reservation_id": ticket["reservation_id"],
            "show_id": ticket["show_id"],
            "slot": ticket["slot"],
            "holder_role": ticket["holder_role"],
            "version": ticket["version"],
            "active_listing_id": live,
            "economic_finality_claimed": False,
            "venue_credential_reissued": False,
            "funds_executed": False,
            "external_marketplace": "UNSUPPORTED",
        }
        view.update(NON_CLAIMS)
        view["economic_finality_claimed"] = False
        view["funds_executed"] = False
        view["venue_credential_reissued"] = False
        return view

    def _listing_view(self, listing: dict) -> dict:
        ticket = self._rights[listing["right_id"]]
        right = self._public_right(listing["right_id"])
        row = self._slot_row(ticket)
        expired = listing["phase"] in OPEN_PHASES and self._now >= listing["expires_ms"]
        attached = (
            listing["phase"] in OPEN_PHASES
            and not expired
            and right["listing_id"] == listing["listing_id"]
        )
        transferred = listing["phase"] in (TRANSFERRED, CLOSED)
        view = {
            "provenance": PROVENANCE,
            "lifecycle_authority": AUTHORITY,
            "listing_id": listing["listing_id"],
            "phase": listing["phase"],
            "terminal": listing["phase"] in TERMINAL_PHASES,
            "right_id": listing["right_id"],
            "show_id": listing["show_id"],
            "seller_role": listing["seller_role"],
            "recipient_role": listing["recipient_role"],
            "buyer_role": listing["buyer_role"],
            "hold_id": listing["hold_id"],
            "amount": listing["amount"],
            "currency": "KRW",
            "expires_ms": listing["expires_ms"],
            "expired": expired,
            "attached": attached,
            "version": listing["version"],
            "version_after": listing["version_after"],
            "payment_ref": listing["payment_ref"],
            "settlement_id": listing["settlement_id"],
            "settlement_gate": self._settlement_gate(listing),
            "mock_settlement_commit_observed": listing["mock_settlement_commit_observed"],
            "transfer_id": listing["transfer_id"],
            "ownership_transferred": transferred,
            "prior_presentation_valid": self._presentation_current(listing, right),
            "venue_credential_reissued": False,
            "economic_finality_claimed": False,
            "holder_role": right["holder_role"],
            "current_version": right["version"],
            "generation": right["generation"],
            "slot_state": row["state"],
            "slot_right_id": row["right_id"],
            "accepted_entries": self._entry_count(listing["subject_ids"]),
            "external_marketplace": "UNSUPPORTED",
            "external_payment": "UNSUPPORTED",
        }
        view.update(NON_CLAIMS)
        view["economic_finality_claimed"] = False
        view["funds_executed"] = False
        view["venue_credential_reissued"] = False
        view["chain_owner_current"] = False
        return view

    def _invariant(self) -> None:
        if self._rights:
            sample = sorted(self._rights)[0]
            _require(self._public_right(sample)["right_id"] == sample, "MOCK_INVARIANT")
            show_id = self._rights[sample]["show_id"]
            _require(self._show_public(show_id)["show_id"] == show_id, "MOCK_INVARIANT")
        live_for_right: dict[str, str] = {}
        for listing in self._listings.values():
            ticket = self._rights.get(listing["right_id"])
            _require(ticket is not None, "MOCK_INVARIANT")
            _require(listing["mock_settlement_commit_observed"] is False or listing["settlement_id"] is not None, "MOCK_INVARIANT")
            if listing["phase"] in OPEN_PHASES and self._now < listing["expires_ms"]:
                _require(listing["right_id"] not in live_for_right, "MOCK_INVARIANT")
                live_for_right[listing["right_id"]] = listing["listing_id"]
                _require(ticket["holder_role"] == listing["seller_role"], "MOCK_INVARIANT")
                _require(ticket["version"] == listing["version"], "MOCK_INVARIANT")
                _require(listing["transfer_id"] is None, "MOCK_INVARIANT")
                _require(listing["mock_settlement_commit_observed"] is False, "MOCK_INVARIANT")
            if listing["phase"] == BUY_HELD:
                _require(listing["hold_id"] is not None and listing["buyer_role"] == listing["recipient_role"], "MOCK_INVARIANT")
            if listing["phase"] == LISTED:
                _require(listing["hold_id"] is None and listing["payment_ref"] is None, "MOCK_INVARIANT")
            if listing["phase"] == PAYMENT_NOTED:
                _require(listing["payment_ref"] is not None, "MOCK_INVARIANT")
            if listing["phase"] == CANCELLED:
                _require(listing["payment_ref"] is None and listing["transfer_id"] is None, "MOCK_INVARIANT")
            if listing["phase"] in (TRANSFERRED, CLOSED):
                _require(listing["payment_ref"] is not None and listing["transfer_id"] is not None, "MOCK_INVARIANT")
                _require(listing["version_after"] == listing["version"] + 1, "MOCK_INVARIANT")
                _require(listing["mock_settlement_commit_observed"] is (listing["settlement_id"] is not None), "MOCK_INVARIANT")
                if ticket["last_transfer_id"] == listing["transfer_id"]:
                    _require(ticket["holder_role"] == listing["recipient_role"], "MOCK_INVARIANT")
                    _require(ticket["version"] == listing["version_after"], "MOCK_INVARIANT")
        for ticket in self._rights.values():
            right = self._public_right(ticket["right_id"])
            _require(right["state"] == "ACTIVE" and right["generation"] == 1, "MOCK_INVARIANT")
            _require(right["holder_role"] == ticket["holder_role"], "MOCK_INVARIANT")
            _require(right["version"] == ticket["version"], "MOCK_INVARIANT")
            row = self._slot_row(ticket)
            _require(row["state"] == "ISSUED" and row["right_id"] == ticket["right_id"], "MOCK_INVARIANT")
            live = self._live_listing_id(ticket)
            _require(live == live_for_right.get(ticket["right_id"]), "MOCK_INVARIANT")
            _require(right["listing_id"] == live, "MOCK_INVARIANT")
