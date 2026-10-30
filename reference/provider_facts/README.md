# Offline synthetic provider facts and payment lookup

**MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY — Analog, NOT Toss.** This internal Python
reference module has no authentication, durability, finality or payment-completion
claims. Source labels are fixture preconditions, never proof of authentication.

Run from the repository root, with standard-library Python:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 reference/provider_facts/example_payment_lookup.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/provider_facts -t reference/provider_facts
```

The example prints seven deterministic JSON lines: paid, partial cancellation,
full cancellation after DONE, timeout, not found, unsupported method and unverified
source. Every line carries synthetic provenance and limitations. Each scenario
uses a separate fixed recording; there is no response queue or polling sequence.
Cancellation history includes the payment and cancel items; it never updates
historical captures or interprets cancellation as payment absence/refund completion.

`provider_facts.py` retains the existing normalization helpers and result types.
`payment_lookup.py::PaymentLookupService` composes them with an existing
`OperationBindingStore` and one `fake_payment_lookup.py::FakePaymentLookup`.
Imports follow this directory's existing sibling-module convention. For example,
from this directory (the following also uses only the local synthetic fixtures):

```python
import json
from fake_payment_lookup import FakePaymentLookup
from payment_lookup import PaymentLookupService, SyntheticLookupScope
from provider_facts import OperationBindingStore
from synthetic_documents import (
    PROVIDER, ACCOUNT, ENVIRONMENT, OPERATION_REF, PAYMENT_REF_A, PAID,
)

scope = SyntheticLookupScope(PROVIDER, ACCOUNT, ENVIRONMENT)
bindings = OperationBindingStore()
bindings.bind(OPERATION_REF, PAYMENT_REF_A)  # setup; lookup itself never binds
fake = FakePaymentLookup(scope=scope, recordings={PAYMENT_REF_A: json.dumps(PAID)})
service = PaymentLookupService(bindings, scope=scope, fake=fake)
synthetic_result = service.lookup(OPERATION_REF)
assert synthetic_result.provenance == "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY"
assert fake.calls == (PAYMENT_REF_A,)
```

`SyntheticLookupScope(provider, account, environment)` is frozen configuration,
defined alongside the fake and re-exported by `payment_lookup`. It is not an
account authorization. `lookup` accepts only `OperationRef`; it cannot receive a
URL, credential, payment key, alternate account, provider selector or fallback.
The service resolves the existing binding, compares its complete scope and the
fake's scope to its own configuration, and calls that fake exactly once. The
normalizer receives its recorded text unchanged, preserving integer amounts,
raw timestamps, fact/hash representation and existing unresolved reasons.

`SyntheticLookupResult` carries `operation_ref`, optional `payment_ref`, existing
`NormalizedPaymentHistory | Unresolved` in `result`, and fixed non-init provenance.
Normalized item detail dictionaries remain caller-mutable as in the existing
helper; each explicit lookup parses fresh text, isolating later results and
recordings. The fake copies the caller's recording map and exposes read-only
recordings plus an immutable `calls` snapshot. Keys are complete `PaymentRef`
values; absent keys yield a synthetic not-found body. Direct fake calls outside
its scope raise `FakeLookupError`. Recordings are text or immutable
`SyntheticLookupFault.TIMEOUT` / `.ERROR` markers; no clock, sleep or timeout
threshold is introduced. Repeated explicit calls are deterministic and do not
consume recordings.

The diagnostic precedence is local synthetic characterization (class B), not a
protocol error catalogue or product policy:

| Condition | Result | Fake calls per service invocation |
|---|---|---|
| Invalid operation argument | Existing `ProviderFactsError("INVALID_OPERATION_REF")` propagates | 0 |
| Missing binding | `Unresolved("BINDING_REQUIRED")`, no PaymentRef | 0 |
| Bound or fake scope differs from configured scope | Existing `Unresolved("BINDING_MISMATCH")` | 0 |
| Explicit fake timeout / lookup error | `LOOKUP_TIMEOUT` / local `LOOKUP_ERROR` unresolved | 1 |
| Parser/normalizer `ProviderFactsError` | Unresolved with its existing code | 1 |
| Not found / unsupported / unverified source | Existing unresolved reason | 1 |
| Accepted synthetic document | Existing normalized history | 1 |

Unrelated programming errors propagate. Nothing retries, falls back, clears
UNKNOWN or infers absence from a non-result. Lookup only reads binding/capture/
review state; it does not call `bind`, `record_capture` or an economic engine.

There is no HTTP binding, OpenAPI/SDK change, new command, kernel integration,
persistence, polling, real provider/bank/KYC/Sui call, event identity derivation,
ProviderFactKey choice, alias table, authentication or production runtime here.
All existing owner-policy values remain UNDETERMINED with their owners: TM04 and
I04/TM05 provider authentication/key stability, I02/I03 scope, I05 termination,
I08 retention, I12 independent cut, and Astra's source/alias/domain/schema and
waiting-policy decisions. The existing contract and evidence maps remain the
owner authority; the fake resolves none of these inputs.

See the [coverage, executed commands and delivery gates](../../validation/2026-10-30-plan-local-payment-lookup-adapter/README.md).
