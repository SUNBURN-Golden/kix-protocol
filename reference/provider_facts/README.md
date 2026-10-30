# Offline synthetic provider facts and payment lookup

**MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY — Analog, NOT Toss.** This internal Python
reference module has no authentication, durability, finality or payment-completion
claims. Source labels are fixture preconditions, never proof of authentication.

Run from the repository root, with standard-library Python:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 reference/provider_facts/example_payment_lookup.py
PYTHONDONTWRITEBYTECODE=1 python3 reference/provider_facts/example_payment_lookup_router.py
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

## Routing to the original bound synthetic scope

`payment_lookup_router.py::PaymentLookupRouter(bindings, *, routes)` composes
the same service and fake for multiple explicitly registered scopes.
`routes` maps `SyntheticLookupScope` to `FakePaymentLookup`; construction copies
the mapping, requires those exact types, and rejects any key that differs from
its fake's scope with existing `ProviderFactsError("BINDING_MISMATCH")` before
lookups. It retains a read-only mapping of one service per scope, sharing the
binding store. There is no registration/replacement method or default route;
an empty registry is allowed. Scope registration is local immutable fixture
configuration, never provider authentication or merchant authorization.

Using the preceding setup, the internal interface is:

```python
from payment_lookup_router import PaymentLookupRouter

router = PaymentLookupRouter(bindings, routes={scope: fake})
synthetic_result = router.lookup(OPERATION_REF)
```

`lookup(operation_ref)` first reads the existing binding. It selects exactly
the bound payment's `(provider, account, environment)` and returns that service's
result unchanged. All five PaymentRef fields, all three OperationRef fields,
normalized facts/timestamps and fixed synthetic provenance are preserved.
OperationRef has no environment field; environment comes from PaymentRef.
Reused operation strings across provider/account scopes remain distinct.
Requests cannot select account, provider, environment or payment reference.
Changing the caller's registration dictionary cannot alter routing.

Router diagnostic precedence is local synthetic characterization (class B),
not protocol errors or product policy:

| Condition | Result | Calls to any fake |
|---|---|---|
| Invalid operation | Existing `INVALID_OPERATION_REF` error propagates | 0 |
| Missing binding | Existing `Unresolved("BINDING_REQUIRED")`, no PaymentRef | 0 |
| No exact registered provider/account/environment scope | Local `Unresolved("LOOKUP_ROUTE_MISSING")`, complete bound PaymentRef retained | 0 |
| Registered scope | Existing service result unchanged | Exactly 1 to selected fake; 0 to all others |

Timeout, error and not-found stay unresolved in the original scope even when
another fake has a successful recording with identical payment/order strings.
They cause no retry, fallback, rebinding, capture/review mutation or UNKNOWN
release. This synchronous in-memory composition assumes the existing local
binding-store model; it adds no persistence or concurrent/distributed fencing.

The router example prints seven deterministic JSON lines: paid A, paid B,
timeout A, error A, not-found A, missing route and missing binding. Every line
includes full references, per-invocation fake call counts, synthetic provenance
and limitations. It needs no network, credentials or provider SDK.

Provider authentication and merchant scope remain **UNDETERMINED — Toss/User**;
event identity, aliases, domain/schema and policy decisions remain with Astra.
There are no provider mappings, economic application, HTTP endpoints, protocol
commands, SDK changes, real service calls or runtime activation here.
See the [router coverage and actual validation](../../validation/2026-10-30-plan-local-payment-scope-router/README.md).

## Reusable offline lookup CLI

Supply one local UTF-8 JSON fixture and one complete OperationRef:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 reference/provider_facts/payment_lookup_cli.py \
  --fixture reference/provider_facts/fixtures/payment_lookup.synthetic.json \
  --operation-ref '{"provider":"toss-synthetic","account":"mid_synthetic_001","operation":"op_synthetic_0001"}'
```

Each argument must appear exactly once. Unknown arguments and abbreviated options
are rejected. There is no environment, payment-key, URL or credential selector.
Write another fixture to use different synthetic identities without editing Python.
The supplied fixture includes two merchant scopes and operations `op_synthetic_partial`,
`op_synthetic_full`, `op_synthetic_timeout` and `op_synthetic_error` in account
`mid_synthetic_001`. The second account is `mid_synthetic_002` and reuses the
original operation/payment/order strings with a distinct complete identity.

### Fixture structure

This versioned format is internal tooling, not a protocol command or public API.
Every object requires exactly the documented keys:

```text
{
  "fixture_version": 1,
  "provenance": "MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY",
  "bindings": [
    {"operation_ref": OperationRef, "payment_ref": PaymentRef}
  ],
  "routes": [
    {"scope": SyntheticLookupScope, "recordings": [
      {"payment_ref": PaymentRef, "recorded_text": string}
      OR {"payment_ref": PaymentRef, "fault": string}
    ]}
  ]
}
```

- OperationRef: `provider`, `account`, `operation`.
- PaymentRef: `provider`, `account`, `environment`, `payment_key`, `order_id`.
- SyntheticLookupScope: `provider`, `account`, `environment`.
- Reference/scope values: strings accepted by the existing validators (1–100
  characters, no leading/trailing whitespace).
- Fault: exactly `synthetic_timeout` or `synthetic_lookup_error`.

Use JSON string escaping for `recorded_text`; see the runnable fixture for full
response text. The loader retains the decoded string exactly, including whitespace,
Unicode, number lexemes and the original source label. It never parses, trims or
re-encodes that text. Faults are explicit markers without clocks or timeout policy.
Empty arrays, bindings without routes and routes without matching recordings are
valid; they exercise existing unresolved behavior. Multiple operations may bind
the same complete payment. Multiple distinct complete references may share keys.

### JSON output and exit behavior

A successful invocation writes exactly one JSON object plus a newline to stdout.
Both histories and unresolved results exit `0`; unresolved never means absence,
final failure, refund completion or permission to release UNKNOWN.

| JSON field | Value |
|---|---|
| `provenance` | Fixed `MOCK_SYNTHETIC_PROVIDER_FACTS_ONLY` |
| `limitations` | `Synthetic only; no authentication, durability, finality or payment-completion claims.` |
| `operation_ref` | Complete supplied OperationRef |
| `payment_ref` | Complete original bound PaymentRef, or `null` for missing binding |
| `facts` (history only) | Ordered items from existing `normalized_fact()` |
| `receipt` (history only) | Existing raw receipt timestamp via `as_dict()` |
| `item_hashes` (history only) | Ordered existing SHA-256 item hashes via `item_hashes()`, outside facts |
| `unresolved` (non-history only) | Unchanged existing reason string |
| `fake_calls` | Scope-sorted array of `{"scope": SyntheticLookupScope, "payment_refs": [PaymentRef, ...]}` |

`fake_calls` contains snapshots of actual calls to every registered fake, including
empty lists for unused scopes. Fresh CLI processes show zero total calls for missing
binding/route, or exactly one complete reference in the bound scope. Alternate
successful recordings are never fallback routes. JSON uses `ensure_ascii=False`,
`sort_keys=True`, `allow_nan=False`; integer amounts (including u128 maximum) remain
JSON integers. Consumers must preserve their precision.

Usage, configuration and local file-reading/UTF-8 errors exit `2`, write a concise
`error:` diagnostic to stderr, and leave stdout empty. `--help` exits `0` and prints
usage. Unexpected programming errors propagate as failures.

### Validation precedence and reusable functions

Argument/OperationRef validation precedes fixture loading. The entire fixture,
including unused trailing routes, is validated before constructing bindings or
performing lookup. Duplicate JSON keys, identical or conflicting repeated
operation bindings, duplicate scopes, duplicate complete recording references,
unknown/missing fields, wrong types, unsupported version/provenance, scope
mismatches and invalid recording/fault alternatives are configuration errors.
An invalid fixture cannot be hidden by a missing binding or an earlier valid route.
Malformed **recorded response text** is allowed configuration and produces the
existing lookup-time unresolved result (for example `DOCUMENT_JSON`, `FLOAT_TOKEN`
or `UNVERIFIED_SOURCE`) after one fake call.

Using the existing sibling-module imports, `load_fixture(path)` returns a fresh
`(OperationBindingStore, scope_to_fake_mapping)`. `lookup_once(bindings, routes,
operation_ref)` invokes `PaymentLookupRouter.lookup` once and returns a JSON-ready
dictionary. Reusing those objects reports cumulative actual fake-call snapshots;
each explicit invocation still adds at most one call. Bindings, recorded text,
captures and reviews are preserved. `main(argv=None)` supplies the CLI boundary.

### Synthetic limitations

This supports E01/B04 local adapter exploration without changing capability grades.
Provider authentication and merchant scope remain **UNDETERMINED — Toss/User**;
event identity, aliases and operational domain/schema choices remain
**UNDETERMINED — Astra**. The tool adds no economic application, event-ID derivation,
persistence, retries, polling, network access, credentials, SDK/OpenAPI change,
provider conformance or runtime activation.

See the [CLI coverage, actual commands and pending delivery gates](../../validation/2026-10-30-plan-local-payment-lookup-cli/README.md).
