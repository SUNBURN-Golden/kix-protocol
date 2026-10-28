"""Offline provider-fact normalization reference.

Deterministic and in-memory. No network, files, payment provider, or chain.
It operates only on synthetic recorded payment documents carried by
synthetic_documents.py. A recorded document is a fixture label for "what an
authenticated lookup would have returned"; it is not a live Toss response,
not a webhook, and not evidence of any provider behavior.

This module implements only the contract-defined, decision-free parts of
docs/contracts/ADAPTER_EVENT_IDENTITY.md draft 0.1 and
docs/contracts/PG_TOSS_CARD_PROFILE.md:

- the five-field PaymentRef tuple (provider, account/MID, environment,
  paymentKey, orderId) as payment identity, never an event ID;
- integer-KRW JSON parsing that rejects f64 paths and out-of-scale,
  out-of-sign and out-of-range amounts;
- raw timestamp text preservation, with an offset-less createdAt recorded
  as unresolved rather than assigned a zone;
- normalize-only-verified-facts: timeout, not-found and unsupported stay
  Unresolved; a cancel never erases the original payment item;
- SHA-256 evidence_hash over the canonical normalized fact of each item;
- one Payment plus cancels[] as one payment's history of many event items,
  never a batch of independent payments;
- at-most-one operation -> payment binding: the same operation with a
  different paymentKey is a review conflict and records no new capture.

It does not mint EventItemId values or aliases, does not choose a
ProviderFactKey, does not assign domain/schema ids, and does not implement
an adapter, inbox, lookup client or durable store. KRW_U128_MAX is the
locked kernel's u128 amount bound, not a product policy value.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

PROVENANCE = "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY"
KRW_U128_MAX = 2**128 - 1

SOURCE_AUTHENTICATED_LOOKUP = "synthetic_authenticated_lookup_fixture"
SOURCE_UNVERIFIED_SIGNAL = "synthetic_unverified_signal"

# Unresolved reasons. Terminal; re-normalizing the same recorded document
# yields the same Unresolved value. None of them infers absence.
LOOKUP_TIMEOUT = "LOOKUP_TIMEOUT"
LOOKUP_NOT_FOUND = "LOOKUP_NOT_FOUND"
METHOD_UNSUPPORTED = "METHOD_UNSUPPORTED"
CURRENCY_UNSUPPORTED = "CURRENCY_UNSUPPORTED"
STATUS_UNSUPPORTED = "STATUS_UNSUPPORTED"
UNVERIFIED_SOURCE = "UNVERIFIED_SOURCE"
FLOAT_TOKEN = "FLOAT_TOKEN"
AMOUNT_SCALE = "AMOUNT_SCALE"
AMOUNT_SIGN = "AMOUNT_SIGN"
AMOUNT_RANGE = "AMOUNT_RANGE"
BINDING_MISMATCH = "BINDING_MISMATCH"

# Timestamp statuses. An offset-less timestamp is recorded as ambiguous and
# is never assigned a zone.
OFFSET_RECORDED = "OFFSET_RECORDED"
AMBIGUOUS_UNRESOLVED = "AMBIGUOUS_UNRESOLVED"

# Binding outcomes for OperationBindingStore.bind.
BOUND = "bound"
REACCEPTED = "reaccepted"
CONFLICT = "conflict"

ITEM_PAYMENT = "payment"
ITEM_CANCEL = "cancel"

# Only these recorded states are exercised by the synthetic corpus. This
# support boundary assigns no finality, absence, refund or release meaning
# to any provider status; all other states remain unresolved.
_SUPPORTED_PAYMENT_STATUSES = ("DONE", "PARTIAL_CANCELED", "CANCELED")
_SUPPORTED_CANCEL_STATUSES = ("DONE",)

_OFFSET = re.compile(r"(Z|[+-]\d{2}:\d{2})$")


class ProviderFactsError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise ProviderFactsError(code)


def _ident(value: object, code: str = "INVALID_ID") -> str:
    _require(type(value) is str and 0 < len(value) <= 100 and value.strip() == value, code)
    return value


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _reject_float(token: str) -> object:
    raise ProviderFactsError(FLOAT_TOKEN)


def _reject_constant(token: str) -> object:
    raise ProviderFactsError("UNEXPECTED_CONSTANT")


@dataclass(frozen=True)
class PaymentRef:
    """The five-field payment identity. Not an event ID (contract §2)."""

    provider: str
    account: str
    environment: str
    payment_key: str
    order_id: str

    def __post_init__(self) -> None:
        for name in ("provider", "account", "environment", "payment_key", "order_id"):
            _ident(getattr(self, name), "INVALID_PAYMENT_REF")

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "account": self.account,
            "environment": self.environment,
            "payment_key": self.payment_key,
            "order_id": self.order_id,
        }


@dataclass(frozen=True)
class OperationRef:
    """Kernel-shaped ProviderOperation {provider, account, operation}."""

    provider: str
    account: str
    operation: str

    def __post_init__(self) -> None:
        for name in ("provider", "account", "operation"):
            _ident(getattr(self, name), "INVALID_OPERATION_REF")


@dataclass(frozen=True)
class RawTimestamp:
    """Provider timestamp: raw text plus the offset only if the text has one."""

    text: str
    offset: str | None
    status: str

    def as_dict(self) -> dict:
        return {"text": self.text, "offset": self.offset, "status": self.status}


def raw_timestamp(text: object) -> RawTimestamp:
    """Preserve raw timestamp text; record offset presence, never assign one."""
    _require(type(text) is str and text.strip() == text and len(text) > 0, "TIMESTAMP_TYPE")
    match = _OFFSET.search(text)
    if match:
        return RawTimestamp(text=text, offset=match.group(1), status=OFFSET_RECORDED)
    return RawTimestamp(text=text, offset=None, status=AMBIGUOUS_UNRESOLVED)


@dataclass(frozen=True)
class NormalizedItem:
    """One item of a payment's history: the payment item or one cancels[] entry.

    Status strings and provider key fields are recorded evidence, never an
    item identity and never a termination verdict. index is snapshot-local
    positional metadata, excluded from the normalized fact and its hash.
    """

    payment_ref: PaymentRef
    index: int
    kind: str
    amount: int
    currency: str
    status_text: str
    occurred: RawTimestamp
    detail: dict = field(default_factory=dict, compare=True)

    def normalized_fact(self) -> dict:
        return {
            "provenance": PROVENANCE,
            "payment_ref": self.payment_ref.as_dict(),
            "item": {
                "kind": self.kind,
                "amount": self.amount,
                "currency": self.currency,
                "status_text": self.status_text,
                "occurred": self.occurred.as_dict(),
                "detail": self.detail,
            },
        }


def evidence_hash(item: NormalizedItem) -> str:
    """SHA-256 hexdigest of the canonical per-item normalized fact."""
    return hashlib.sha256(_canonical(item.normalized_fact()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NormalizedPaymentHistory:
    """One payment's history: the payment item plus one item per cancels[] entry.

    The recorded receipt text is custody metadata only; it is kept out of the
    per-item normalized fact and out of evidence_hash.
    """

    payment_ref: PaymentRef
    receipt: RawTimestamp
    items: tuple

    def item_hashes(self) -> list:
        return [evidence_hash(item) for item in self.items]


@dataclass(frozen=True)
class Unresolved:
    """Terminal non-result. Never inferred as absence of the payment."""

    reason: str


def parse_recorded_document(text: object) -> dict:
    """Parse recorded JSON without ever taking an f64 path."""
    _require(type(text) is str, "DOCUMENT_TYPE")
    try:
        value = json.loads(text, parse_float=_reject_float, parse_constant=_reject_constant)
    except ProviderFactsError:
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        raise ProviderFactsError("DOCUMENT_JSON") from exc
    _require(type(value) is dict, "DOCUMENT_TYPE")
    return value


def _amount(value: object) -> int | Unresolved:
    """Integer KRW won only: no float, no bool, no negative, no >u128."""
    if type(value) is not int:
        return Unresolved(AMOUNT_SCALE)
    if value < 0:
        return Unresolved(AMOUNT_SIGN)
    if value > KRW_U128_MAX:
        return Unresolved(AMOUNT_RANGE)
    return value


def _amount_or_unresolved(value: object) -> tuple[bool, object]:
    checked = _amount(value)
    if isinstance(checked, Unresolved):
        return False, checked
    return True, checked


def _text_field(document: dict, name: str) -> str:
    value = document.get(name)
    return value if type(value) is str else ""


def normalize_recorded_document(payment_ref: PaymentRef, recorded: dict) -> object:
    """Normalize a synthetic authenticated-lookup recording.

    Returns a NormalizedPaymentHistory for a verified in-scope document and
    Unresolved otherwise. A signal-labelled document is never a fact.
    """
    _require(type(payment_ref) is PaymentRef, "INVALID_PAYMENT_REF")
    _require(type(recorded) is dict, "DOCUMENT_TYPE")
    if recorded.get("source") != SOURCE_AUTHENTICATED_LOOKUP:
        return Unresolved(UNVERIFIED_SOURCE)
    outcome = recorded.get("outcome")
    if outcome == "timeout":
        return Unresolved(LOOKUP_TIMEOUT)
    if outcome == "not_found":
        return Unresolved(LOOKUP_NOT_FOUND)
    _require(outcome == "document", "RECORDED_OUTCOME_UNKNOWN")
    payment = recorded.get("payment")
    _require(type(payment) is dict, "DOCUMENT_TYPE")
    if payment.get("paymentKey") != payment_ref.payment_key or (
        payment.get("orderId") != payment_ref.order_id
    ):
        return Unresolved(BINDING_MISMATCH)
    if payment.get("method") != "카드":
        return Unresolved(METHOD_UNSUPPORTED)
    if payment.get("currency") != "KRW":
        return Unresolved(CURRENCY_UNSUPPORTED)
    payment_status = payment.get("status")
    if payment_status not in _SUPPORTED_PAYMENT_STATUSES:
        return Unresolved(STATUS_UNSUPPORTED)
    ok, total = _amount_or_unresolved(payment.get("totalAmount"))
    if not ok:
        return total
    receipt = raw_timestamp(recorded.get("recorded_at"))
    occurred_names = ("approvedAt", "requestedAt", "createdAt")
    occurred = None
    for name in occurred_names:
        if type(payment.get(name)) is str and payment.get(name):
            occurred = raw_timestamp(payment[name])
            break
    _require(occurred is not None, "TIMESTAMP_MISSING")
    payment_item = NormalizedItem(
        payment_ref=payment_ref,
        index=0,
        kind=ITEM_PAYMENT,
        amount=total,
        currency="KRW",
        status_text=payment_status,
        occurred=occurred,
        detail={
            "method_text": _text_field(payment, "method"),
            "last_transaction_key_text": _text_field(payment, "lastTransactionKey"),
            "timestamps": {
                name: raw_timestamp(payment[name]).as_dict()
                for name in ("requestedAt", "approvedAt", "createdAt")
                if type(payment.get(name)) is str and payment.get(name)
            },
        },
    )
    items = [payment_item]
    cancels = payment.get("cancels")
    _require(cancels is None or type(cancels) is list, "CANCELS_TYPE")
    for entry in cancels or []:
        _require(type(entry) is dict, "CANCEL_ITEM_TYPE")
        cancel_status = entry.get("cancelStatus")
        if cancel_status not in _SUPPORTED_CANCEL_STATUSES:
            return Unresolved(STATUS_UNSUPPORTED)
        ok, cancel_amount = _amount_or_unresolved(entry.get("cancelAmount"))
        if not ok:
            return cancel_amount
        items.append(
            NormalizedItem(
                payment_ref=payment_ref,
                index=len(items),
                kind=ITEM_CANCEL,
                amount=cancel_amount,
                currency="KRW",
                status_text=cancel_status,
                occurred=raw_timestamp(entry.get("canceledAt")),
                detail={
                    "reason_text": _text_field(entry, "cancelReason"),
                    "transaction_key_text": _text_field(entry, "transactionKey"),
                },
            )
        )
    return NormalizedPaymentHistory(
        payment_ref=payment_ref,
        receipt=receipt,
        items=tuple(items),
    )


def normalize_recorded_text(payment_ref: PaymentRef, text: object) -> object:
    """Parse then normalize. A float token in the text stays unresolved."""
    try:
        recorded = parse_recorded_document(text)
    except ProviderFactsError as exc:
        if exc.code == FLOAT_TOKEN:
            return Unresolved(FLOAT_TOKEN)
        raise
    return normalize_recorded_document(payment_ref, recorded)


@dataclass(frozen=True)
class BindingConflict:
    """Same operation carrying a different PaymentRef: routed to review.

    No new operation, no new order and no new capture is created for it.
    """

    operation_ref: OperationRef
    bound_payment_ref: PaymentRef
    incoming_payment_ref: PaymentRef


@dataclass(frozen=True)
class BindingOutcome:
    outcome: str
    payment_ref: PaymentRef
    conflict: BindingConflict | None


class OperationBindingStore:
    """In-memory at-most-one operation -> payment binding check.

    Not the durable §6.2 record and not a kernel command surface. The review
    list and recorded_captures are evidence fixtures: a conflict lands on
    review and never appends a capture.
    """

    def __init__(self) -> None:
        self._bindings: dict = {}
        self.review: list = []
        self.recorded_captures: list = []

    def bind(self, operation_ref: OperationRef, payment_ref: PaymentRef) -> BindingOutcome:
        _require(type(operation_ref) is OperationRef, "INVALID_OPERATION_REF")
        _require(type(payment_ref) is PaymentRef, "INVALID_PAYMENT_REF")
        key = (operation_ref.provider, operation_ref.account, operation_ref.operation)
        existing = self._bindings.get(key)
        if existing is None:
            _require(
                operation_ref.provider == payment_ref.provider
                and operation_ref.account == payment_ref.account,
                BINDING_MISMATCH,
            )
            self._bindings[key] = payment_ref
            return BindingOutcome(BOUND, payment_ref, None)
        if existing == payment_ref:
            return BindingOutcome(REACCEPTED, existing, None)
        conflict = BindingConflict(operation_ref, existing, payment_ref)
        self.review.append(conflict)
        return BindingOutcome(CONFLICT, existing, conflict)

    def lookup(self, operation_ref: OperationRef) -> PaymentRef | None:
        _require(type(operation_ref) is OperationRef, "INVALID_OPERATION_REF")
        key = (operation_ref.provider, operation_ref.account, operation_ref.operation)
        return self._bindings.get(key)

    def binding_count(self) -> int:
        return len(self._bindings)

    def record_capture(self, operation_ref: OperationRef, payment_ref: PaymentRef, item: NormalizedItem) -> str:
        """Record an item as a capture only against an existing matching binding."""
        _require(self.lookup(operation_ref) == payment_ref, "BINDING_REQUIRED")
        _require(type(item) is NormalizedItem and item.payment_ref == payment_ref, "CAPTURE_ITEM_MISMATCH")
        digest = evidence_hash(item)
        self.recorded_captures.append(
            {
                "operation": operation_ref.operation,
                "payment_key": payment_ref.payment_key,
                "item_index": item.index,
                "evidence_hash": digest,
            }
        )
        return digest
