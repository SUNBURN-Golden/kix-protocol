"""Run with python3 reference/provider_facts/example_payment_lookup_router.py.

Deterministic offline fixture routing only. Analog, NOT Toss.
"""

import json
from dataclasses import asdict, replace

import synthetic_documents as fixtures
from fake_payment_lookup import FakePaymentLookup, SyntheticLookupFault, SyntheticLookupScope
from payment_lookup_router import PaymentLookupRouter
from provider_facts import OperationBindingStore, Unresolved

LIMITATIONS = "Synthetic only; no authentication, durability, finality or payment-completion claims."


def example_results() -> list[dict]:
    bindings = OperationBindingStore()
    scope_a = SyntheticLookupScope(fixtures.PROVIDER, fixtures.ACCOUNT, fixtures.ENVIRONMENT)
    scope_b = replace(scope_a, account="mid_synthetic_002")
    paid_a = fixtures.PAYMENT_REF_A
    paid_b = replace(paid_a, account=scope_b.account)
    timeout = replace(paid_a, payment_key="pay_synthetic_timeout")
    error = replace(paid_a, payment_key="pay_synthetic_error")
    not_found = replace(paid_a, payment_key="pay_synthetic_missing")
    unrouted = replace(paid_a, environment="unregistered-synthetic")
    fake_a = FakePaymentLookup(scope=scope_a, recordings={
        paid_a: json.dumps(fixtures.PAID),
        timeout: SyntheticLookupFault.TIMEOUT,
        error: SyntheticLookupFault.ERROR,
    })
    fake_b = FakePaymentLookup(scope=scope_b, recordings={paid_b: json.dumps(fixtures.PAID)})
    router = PaymentLookupRouter(bindings, routes={scope_a: fake_a, scope_b: fake_b})
    scenarios = (
        ("PAID_A", fixtures.OPERATION_REF, paid_a),
        ("PAID_B", replace(fixtures.OPERATION_REF, account=scope_b.account), paid_b),
        ("TIMEOUT_A", replace(fixtures.OPERATION_REF, operation="op_synthetic_timeout"), timeout),
        ("ERROR_A", replace(fixtures.OPERATION_REF, operation="op_synthetic_error"), error),
        ("NOT_FOUND_A", replace(fixtures.OPERATION_REF, operation="op_synthetic_missing"), not_found),
        ("MISSING_ROUTE", replace(fixtures.OPERATION_REF, operation="op_synthetic_unrouted"), unrouted),
        ("MISSING_BINDING", replace(fixtures.OPERATION_REF, operation="op_synthetic_unbound"), None),
    )
    output = []
    for name, operation, payment in scenarios:
        if payment is not None:
            bindings.bind(operation, payment)  # fixture setup, never performed by lookup
        before = (len(fake_a.calls), len(fake_b.calls))
        result = router.lookup(operation)
        row = {
            "scenario": name,
            "provenance": result.provenance,
            "limitations": LIMITATIONS,
            "operation_ref": asdict(result.operation_ref),
            "payment_ref": result.payment_ref.as_dict() if result.payment_ref else None,
            "fake_calls": {"A": len(fake_a.calls) - before[0], "B": len(fake_b.calls) - before[1]},
        }
        if isinstance(result.result, Unresolved):
            row["unresolved"] = result.result.reason
        else:
            row["facts"] = [item.normalized_fact() for item in result.result.items]
            row["receipt"] = result.result.receipt.as_dict()
        output.append(row)
    return output


if __name__ == "__main__":
    for row in example_results():
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
