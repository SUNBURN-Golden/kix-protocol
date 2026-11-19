"""Explicit in-memory primary-payment fixture composition. Analog, NOT Toss.

The association is caller configuration, not a production identity mapping.
Only observe_payment is invoked; lifecycle/idempotency decisions stay in the
unchanged reservation FSM. No retry, fallback, generated keys or adapter cache.
"""

from dataclasses import dataclass
from pathlib import Path
import sys

from payment_lookup import SyntheticLookupResult
from payment_lookup_router import PaymentLookupRouter
from provider_facts import (
    ITEM_PAYMENT, PROVENANCE, NormalizedItem, NormalizedPaymentHistory,
    OperationRef, PaymentRef, Unresolved,
)

_BOOKING_DIR = Path(__file__).resolve().parents[1] / "booking_resale_admission"
if str(_BOOKING_DIR) not in sys.path:
    sys.path.insert(1, str(_BOOKING_DIR))

from reservation_fsm import (  # noqa: E402
    ReservationError, ReservationMachine, _amount, _hex32, _id, _lift,
)


@dataclass(frozen=True)
class SyntheticReservationAssociation:
    """Complete, explicit fixture pairing; local/provider order IDs may differ."""

    operation_ref: OperationRef
    payment_ref: PaymentRef
    reservation_id: str
    order_id: str
    mock_payment_ref: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if type(self.operation_ref) is not OperationRef:
            raise TypeError("operation_ref must be OperationRef")
        if type(self.payment_ref) is not PaymentRef:
            raise TypeError("payment_ref must be PaymentRef")
        for value in (self.reservation_id, self.order_id, self.idempotency_key):
            _id(value)
        _lift(_hex32, self.mock_payment_ref, "PAYMENT_REF")


@dataclass(frozen=True)
class SyntheticReservationHandoffResult:
    lookup_result: SyntheticLookupResult | None = None
    fsm_result: dict | None = None
    fsm_error: ReservationError | None = None
    reason: str | None = None


class PaymentReservationHandoff:
    def __init__(
        self, router: PaymentLookupRouter, machine: ReservationMachine, *,
        association: SyntheticReservationAssociation,
    ) -> None:
        if type(association) is not SyntheticReservationAssociation:
            raise TypeError("association must be SyntheticReservationAssociation")
        self._router = router
        self._machine = machine
        self._association = association

    def submit(self, operation_ref: OperationRef) -> SyntheticReservationHandoffResult:
        association = self._association
        # Diagnostics here are internal synthetic characterizations, not new
        # protocol error codes or policy decisions.
        if type(operation_ref) is not OperationRef or operation_ref != association.operation_ref:
            return SyntheticReservationHandoffResult(reason="OPERATION_MISMATCH")
        lookup = self._router.lookup(operation_ref)
        if isinstance(lookup.result, Unresolved):
            return SyntheticReservationHandoffResult(lookup_result=lookup, reason=lookup.result.reason)
        history = lookup.result
        payment = association.payment_ref
        if (
            lookup.provenance != PROVENANCE
            or lookup.operation_ref != association.operation_ref
            or lookup.payment_ref != payment
            or operation_ref.provider != payment.provider
            or operation_ref.account != payment.account
            or type(history) is not NormalizedPaymentHistory
            or history.payment_ref != payment
            or any(type(item) is not NormalizedItem or item.payment_ref != payment for item in history.items)
        ):
            return SyntheticReservationHandoffResult(lookup_result=lookup, reason="LOOKUP_IDENTITY_MISMATCH")
        if len(history.items) != 1 or (
            history.items[0].kind != ITEM_PAYMENT or history.items[0].status_text != "DONE"
        ):
            return SyntheticReservationHandoffResult(lookup_result=lookup, reason="PRIMARY_PAYMENT_REQUIRED")
        item = history.items[0]
        try:
            _amount(item.amount)  # Preserve the existing reservation range; no rounding/clamping.
        except ReservationError:
            return SyntheticReservationHandoffResult(lookup_result=lookup, reason="PAYMENT_AMOUNT_MISMATCH")
        try:
            view = self._machine.view(association.reservation_id)
        except ReservationError as error:
            return SyntheticReservationHandoffResult(lookup_result=lookup, fsm_error=error)
        if view["reservation_id"] != association.reservation_id or view["order_id"] != association.order_id:
            return SyntheticReservationHandoffResult(lookup_result=lookup, reason="RESERVATION_IDENTITY_MISMATCH")
        if (
            item.currency != "KRW" or view["currency"] != "KRW"
            or type(view["amount"]) is not int or view["amount"] != item.amount
        ):
            return SyntheticReservationHandoffResult(lookup_result=lookup, reason="PAYMENT_AMOUNT_MISMATCH")
        # No phase precondition: the FSM must retain first-result replay even
        # after separately initiated later transitions.
        try:
            result = self._machine.observe_payment(
                association.order_id,
                idempotency_key=association.idempotency_key,
                payment_ref=association.mock_payment_ref,
                amount=item.amount,
            )
        except ReservationError as error:
            return SyntheticReservationHandoffResult(lookup_result=lookup, fsm_error=error)
        return SyntheticReservationHandoffResult(lookup_result=lookup, fsm_result=result)
