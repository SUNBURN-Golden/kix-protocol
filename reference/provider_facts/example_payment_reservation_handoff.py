"""Deterministic offline primary-payment fixture. Analog, NOT Toss.

Run: python3 reference/provider_facts/example_payment_reservation_handoff.py
"""

import json
from copy import deepcopy
from dataclasses import asdict

import synthetic_documents as fixtures
from fake_payment_lookup import FakePaymentLookup, SyntheticLookupScope
from payment_lookup_router import PaymentLookupRouter
from payment_reservation_handoff import (
    PaymentReservationHandoff, ReservationMachine, SyntheticReservationAssociation,
)
from provider_facts import OperationBindingStore

LIMITATIONS = (
    "Synthetic fixture only; no provider authentication, production identity mapping, "
    "payment completion, funds execution, durability or finality."
)


def prepare_fixture(*, amount: int = 15000) -> tuple:
    """Prepare a confirmed local reservation and its explicitly bound original fake.

    Values are existing mock fixture inputs, not selected product policy values.
    The mock payment reference and key are supplied literally, never derived.
    """
    association = SyntheticReservationAssociation(
        operation_ref=fixtures.OPERATION_REF,
        payment_ref=fixtures.PAYMENT_REF_A,
        reservation_id="local-primary-reservation",
        order_id="local-primary-order",
        mock_payment_ref="ab" * 32,
        idempotency_key="fixture-primary-observation",
    )
    machine = ReservationMachine()
    machine.set_clock("clock", idempotency_key="fixture-clock", now_ms=1_000_000)
    machine.register_show(
        "fixture-show", idempotency_key="fixture-show", organizer_role="organizer",
        capacity=1, gate_roles=["fixture-gate"], primary_price=amount,
        resale_cap=amount, resale_allowed=False, organizer_bps=0, platform_bps=0,
    )
    machine.hold(
        association.reservation_id, idempotency_key="fixture-hold", show_id="fixture-show",
        slot=0, buyer_role="fixture-buyer", expires_ms=1_900_000,
    )
    machine.confirm(
        association.order_id, idempotency_key="fixture-confirm",
        reservation_id=association.reservation_id, amount=amount,
    )
    bindings = OperationBindingStore()
    bindings.bind(association.operation_ref, association.payment_ref)
    scope = SyntheticLookupScope(fixtures.PROVIDER, fixtures.ACCOUNT, fixtures.ENVIRONMENT)
    document = deepcopy(fixtures.PAID)
    document["payment"]["totalAmount"] = amount
    fake = FakePaymentLookup(scope=scope, recordings={association.payment_ref: json.dumps(document)})
    return machine, bindings, fake, association


def example_result() -> dict:
    machine, bindings, fake, association = prepare_fixture()
    router = PaymentLookupRouter(bindings, routes={fake.scope: fake})
    result = PaymentReservationHandoff(router, machine, association=association).submit(association.operation_ref)
    # This fixed fixture must succeed; never make a diagnostic look like success.
    if result.fsm_result is None:
        raise AssertionError(result)
    return {
        "association": asdict(association),
        "lookup_result": asdict(result.lookup_result),
        "item_hashes": result.lookup_result.result.item_hashes(),
        "fsm_result": result.fsm_result,
        "fsm_error": None,
        "reason": result.reason,
        "reservation": machine.view(association.reservation_id),
        "journal": machine.export_journal(),
        "fake_calls": [payment.as_dict() for payment in fake.calls],
        "limitations": LIMITATIONS,
    }


if __name__ == "__main__":
    print(json.dumps(example_result(), ensure_ascii=False, sort_keys=True, allow_nan=False))
