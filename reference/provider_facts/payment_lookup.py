"""Internal operation-bound synthetic lookup service. Analog, NOT Toss.

No authentication, durability, finality or payment-completion claims. No HTTP,
kernel/economic integration, persistence, polling, retry or fallback. Configuration
selects a single local fake; requests carry only an existing OperationRef.
"""

from dataclasses import dataclass, field

from fake_payment_lookup import FakeLookupError, FakePaymentLookup, SyntheticLookupScope
from provider_facts import (
    BINDING_MISMATCH,
    LOOKUP_TIMEOUT,
    PROVENANCE,
    NormalizedPaymentHistory,
    OperationBindingStore,
    OperationRef,
    PaymentRef,
    ProviderFactsError,
    Unresolved,
    normalize_recorded_text,
)

# Local synthetic diagnostics, not protocol errors or policy values.
BINDING_REQUIRED = "BINDING_REQUIRED"
LOOKUP_ERROR = "LOOKUP_ERROR"


@dataclass(frozen=True)
class SyntheticLookupResult:
    operation_ref: OperationRef
    payment_ref: PaymentRef | None
    result: NormalizedPaymentHistory | Unresolved
    provenance: str = field(default=PROVENANCE, init=False)


class PaymentLookupService:
    def __init__(
        self, bindings: OperationBindingStore, *, scope: SyntheticLookupScope,
        fake: FakePaymentLookup,
    ) -> None:
        if type(scope) is not SyntheticLookupScope:
            raise TypeError("scope must be SyntheticLookupScope")
        self._bindings = bindings
        self._scope = scope
        self._fake = fake

    def lookup(self, operation_ref: OperationRef) -> SyntheticLookupResult:
        # Preserve the store's invalid-argument error; no guessing a binding.
        payment_ref = self._bindings.lookup(operation_ref)
        if payment_ref is None:
            result = Unresolved(BINDING_REQUIRED)
        elif not self._scope.matches(payment_ref) or self._fake.scope != self._scope:
            result = Unresolved(BINDING_MISMATCH)
        else:
            try:
                text = self._fake.lookup(payment_ref)
            except TimeoutError:
                result = Unresolved(LOOKUP_TIMEOUT)
            except FakeLookupError:
                result = Unresolved(LOOKUP_ERROR)
            else:
                try:
                    # Fresh parsing on every explicit call prevents mutable
                    # normalized details from aliasing recordings/later results.
                    result = normalize_recorded_text(payment_ref, text)
                except ProviderFactsError as exc:
                    result = Unresolved(exc.code)
        return SyntheticLookupResult(operation_ref, payment_ref, result)
