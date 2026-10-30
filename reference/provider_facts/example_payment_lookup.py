"""Run with python3 reference/provider_facts/example_payment_lookup.py.

Offline synthetic example only; no authentication, durability, finality or
payment-completion claims. Each scenario is a separate fixed recording.
"""

import json

import synthetic_documents as fixtures
from fake_payment_lookup import FakePaymentLookup, SyntheticLookupFault
from payment_lookup import PaymentLookupService, SyntheticLookupScope
from provider_facts import OperationBindingStore, Unresolved

LIMITATIONS = "Synthetic only; no authentication, durability, finality or payment-completion claims."


def example_results() -> list[dict]:
    scope = SyntheticLookupScope(fixtures.PROVIDER, fixtures.ACCOUNT, fixtures.ENVIRONMENT)
    bindings = OperationBindingStore()
    bindings.bind(fixtures.OPERATION_REF, fixtures.PAYMENT_REF_A)
    scenarios = (
        ("PAID", fixtures.PAID),
        ("PARTIAL_CANCEL", fixtures.PARTIAL_CANCEL),
        ("CANCELED_AFTER_DONE", fixtures.CANCELED_AFTER_DONE),
        ("TIMEOUT", SyntheticLookupFault.TIMEOUT),
        ("NOT_FOUND", fixtures.NOT_FOUND),
        ("UNSUPPORTED_METHOD", fixtures.UNSUPPORTED_METHOD),
        ("UNVERIFIED_SOURCE", fixtures.UNVERIFIED_SIGNAL),
    )
    output = []
    for name, recording in scenarios:
        text_or_fault = recording if isinstance(recording, SyntheticLookupFault) else json.dumps(recording)
        fake = FakePaymentLookup(scope=scope, recordings={fixtures.PAYMENT_REF_A: text_or_fault})
        result = PaymentLookupService(bindings, scope=scope, fake=fake).lookup(fixtures.OPERATION_REF)
        history = result.result
        row = {
            "scenario": name,
            "provenance": result.provenance,
            "limitations": LIMITATIONS,
            "operation": result.operation_ref.operation,
            "payment_ref": result.payment_ref.as_dict(),
            "fake_calls": len(fake.calls),
        }
        if isinstance(history, Unresolved):
            row["unresolved"] = history.reason
        else:
            row["facts"] = [item.normalized_fact() for item in history.items]
            row["receipt"] = history.receipt.as_dict()
        output.append(row)
    return output


if __name__ == "__main__":
    for row in example_results():
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
