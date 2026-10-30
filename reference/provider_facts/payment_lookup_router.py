"""Internal synchronous synthetic lookup router. Analog, NOT Toss.

Fixed fixture registration only: no authentication, default route, fallback,
retry, rebinding, persistence or economic application.
"""

from collections.abc import Mapping
from types import MappingProxyType

from fake_payment_lookup import FakePaymentLookup, SyntheticLookupScope
from payment_lookup import BINDING_REQUIRED, PaymentLookupService, SyntheticLookupResult
from provider_facts import (
    BINDING_MISMATCH, OperationBindingStore, OperationRef, ProviderFactsError, Unresolved,
)

# Local synthetic diagnostic, not a protocol error or product policy value.
LOOKUP_ROUTE_MISSING = "LOOKUP_ROUTE_MISSING"


class PaymentLookupRouter:
    def __init__(
        self, bindings: OperationBindingStore, *,
        routes: Mapping[SyntheticLookupScope, FakePaymentLookup],
    ) -> None:
        copied = dict(routes)
        for scope, fake in copied.items():
            if type(scope) is not SyntheticLookupScope:
                raise TypeError("route keys must be SyntheticLookupScope")
            if type(fake) is not FakePaymentLookup:
                raise TypeError("route values must be FakePaymentLookup")
            if scope != fake.scope:
                raise ProviderFactsError(BINDING_MISMATCH)
        self._bindings = bindings
        self._services = MappingProxyType({
            scope: PaymentLookupService(bindings, scope=scope, fake=fake)
            for scope, fake in copied.items()
        })

    def lookup(self, operation_ref: OperationRef) -> SyntheticLookupResult:
        # Operation identity has no environment. Only its existing complete
        # PaymentRef binding supplies the scope; requests select nothing else.
        payment_ref = self._bindings.lookup(operation_ref)
        if payment_ref is None:
            return SyntheticLookupResult(operation_ref, None, Unresolved(BINDING_REQUIRED))
        scope = SyntheticLookupScope(
            payment_ref.provider, payment_ref.account, payment_ref.environment,
        )
        service = self._services.get(scope)
        if service is None:
            return SyntheticLookupResult(operation_ref, payment_ref, Unresolved(LOOKUP_ROUTE_MISSING))
        return service.lookup(operation_ref)
