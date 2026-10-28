"""Seeded synthetic recorded payment documents.

These are literal offline fixtures shaped like recorded payment lookup
documents. They are not Toss responses, were never returned by a provider,
and prove nothing about provider behavior. The "source" label is a fixture
precondition: SOURCE_AUTHENTICATED_LOOKUP marks a document the fixture
declares to be a recorded authenticated-lookup body, while
SOURCE_UNVERIFIED_SIGNAL marks a signal that must never normalize.

The operation/payment identity values are synthetic, not real MIDs,
paymentKeys, orderIds or idempotency keys.
"""

from provider_facts import (
    SOURCE_AUTHENTICATED_LOOKUP,
    SOURCE_UNVERIFIED_SIGNAL,
    OperationRef,
    PaymentRef,
)

PROVIDER = "toss-synthetic"
ACCOUNT = "mid_synthetic_001"
ENVIRONMENT = "test-synthetic"
OPERATION = "op_synthetic_0001"

PAYMENT_REF_A = PaymentRef(
    provider=PROVIDER,
    account=ACCOUNT,
    environment=ENVIRONMENT,
    payment_key="pay_synthetic_001",
    order_id="order_synthetic_001",
)
PAYMENT_REF_B = PaymentRef(
    provider=PROVIDER,
    account=ACCOUNT,
    environment=ENVIRONMENT,
    payment_key="pay_synthetic_999",
    order_id="order_synthetic_999",
)
OPERATION_REF = OperationRef(provider=PROVIDER, account=ACCOUNT, operation=OPERATION)


def _payment(**overrides):
    payment = {
        "paymentKey": "pay_synthetic_001",
        "orderId": "order_synthetic_001",
        "method": "카드",
        "currency": "KRW",
        "totalAmount": 15000,
        "status": "DONE",
        "requestedAt": "2026-10-01T11:59:00+09:00",
        "approvedAt": "2026-10-01T12:00:00+09:00",
        "lastTransactionKey": "txkey_synthetic_001",
        "cancels": [],
    }
    payment.update(overrides)
    return payment


def recorded_document(payment=None, outcome="document", source=SOURCE_AUTHENTICATED_LOOKUP, recorded_at="2026-10-01T12:00:05+09:00"):
    document = {
        "source": source,
        "outcome": outcome,
        "recorded_at": recorded_at,
        "payment": payment if payment is not None else _payment(),
    }
    return document


PAID = recorded_document()

PARTIAL_CANCEL = recorded_document(
    _payment(
        status="PARTIAL_CANCELED",
        cancels=[
            {
                "cancelAmount": 5000,
                "cancelReason": "synthetic partial cancel",
                "cancelStatus": "DONE",
                "canceledAt": "2026-10-02T09:00:00+09:00",
                "transactionKey": "txkey_synthetic_cancel_001",
            }
        ],
    )
)

CANCELED_AFTER_DONE = recorded_document(
    _payment(
        status="CANCELED",
        cancels=[
            {
                "cancelAmount": 15000,
                "cancelReason": "synthetic full cancel",
                "cancelStatus": "DONE",
                "canceledAt": "2026-10-03T09:00:00+09:00",
                "transactionKey": "txkey_synthetic_cancel_002",
            }
        ],
    )
)

OFFSET_LESS_CREATED_AT = recorded_document(
    _payment(createdAt="2026-10-01T12:00:01")
)

TIMEOUT = recorded_document(outcome="timeout")
NOT_FOUND = recorded_document(outcome="not_found")

UNSUPPORTED_METHOD = recorded_document(_payment(method="간편결제"))
NON_KRW = recorded_document(_payment(currency="USD"))
NEGATIVE_AMOUNT = recorded_document(_payment(totalAmount=-500))
OVER_RANGE_AMOUNT = recorded_document(_payment(totalAmount=2**128))
MAX_KRW_AMOUNT = recorded_document(_payment(totalAmount=2**128 - 1))

UNVERIFIED_SIGNAL = {
    "source": SOURCE_UNVERIFIED_SIGNAL,
    "outcome": "document",
    "recorded_at": "2026-10-01T12:00:05+09:00",
    "payment": _payment(),
}

DIFFERENT_PAYMENT = recorded_document(
    _payment(paymentKey="pay_synthetic_999", orderId="order_synthetic_999")
)

# Raw text variants that only exist to exercise the non-f64 JSON parse path.
# A Python dict cannot express the lexeme the parse path must reject.
FLOAT_AMOUNT_TEXT = (
    '{"source": "synthetic_authenticated_lookup_fixture", "outcome": "document",'
    ' "recorded_at": "2026-10-01T12:00:05+09:00", "payment": {'
    '"paymentKey": "pay_synthetic_001", "orderId": "order_synthetic_001",'
    '"method": "카드", "currency": "KRW", "totalAmount": 1500.0,'
    '"status": "DONE", "requestedAt": "2026-10-01T11:59:00+09:00",'
    '"approvedAt": "2026-10-01T12:00:00+09:00",'
    '"lastTransactionKey": "txkey_synthetic_001", "cancels": []}}'
)
EXPONENT_AMOUNT_TEXT = FLOAT_AMOUNT_TEXT.replace("1500.0", "1.5e3")
FRACTION_AMOUNT_TEXT = FLOAT_AMOUNT_TEXT.replace("1500.0", "1500.5")
FLOAT_AMOUNT_OBJECT = recorded_document(_payment(totalAmount=1500.0))
