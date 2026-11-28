# BOOTSTRAP producer-qualification tuple (non-normative identity record)

**This is a non-normative identity record. It does not qualify any surface
semantically, for N/N-1 compatibility, for production, for audit or for User
approval.** The machine-readable record is
[`PRODUCER_QUALIFICATION_TUPLE_V1.json`](PRODUCER_QUALIFICATION_TUPLE_V1.json);
the builder evidence is
[`validation/2026-11-10-plan-producer-qualification-tuple-bundle/README.md`](../../validation/2026-11-10-plan-producer-qualification-tuple-bundle/README.md).

## What is pinned

The record pins the bytes and names of the historical `bootstrap-2` BOOTSTRAP
producer tuple (84-action archived snapshot, distinct from the live 94-action
`read-model-reference-1` catalogue that adds the ten approved point queries):

- the contract-only OpenAPI 3.1 document with 84 local-call operations
  (40 core commands + 44 FSM actions);
- the additive FSM command contract for the five reference machines;
- the non-production loopback integration-gate OpenAPI document;
- the core `protocol_contract.json` source;
- the generated TypeScript SDK catalogue, its generator and `toolchains.json`;
- the `bootstrap-2` compatibility profile, manifest and manifest sidecar;
- the two SDK conformance vector files; and
- the five candidate read-model fixture files and their manifest.

Every command is mapped to its core or FSM source and to the single local-call
gate route. Every surface carries exactly one status.

## Status meanings

| Status | Meaning |
|---|---|
| `BOOTSTRAP_SCHEMA_BOUND` | The recorded bytes are pinned and the command, action and read sets are re-derived from them. This binds schema identity only. |
| `HOLD_SEMANTIC` | The surface is deliberately not qualified for semantic consumption. The profile grants `catalogue-schema-binding only`. |
| `NOT_BOUND` | The surface is named by contract but has no merged implementation, catalogue entry, wire binding or conformance evidence in this tuple. |

## Read queries stay NOT_BOUND

In this historical `bootstrap-2` snapshot, the 13 owner-decided read query names
are listed as `NOT_BOUND` with their candidate vector paths because
`read-model-reference` was not merged in that 84-action tuple. Within this
archived tuple they are **not published**, not added to either archived
84-action catalogue, and the candidate fixtures are not conformance evidence.
Source: [`docs/contracts/READ_MODEL_QUERIES.md`](../contracts/READ_MODEL_QUERIES.md).

## SD1 verifier evidence and ledger status

The pinned tuple's `sd1.status = OPEN` and `sd1.owner = User` record the
October class C stop, when the verifier checked the OpenAPI references,
generator and SDK output before hashing the profile. JunTae authorized option
1 on November 18 (`[pt224u]`). Formal ledger disposition remains with JunTae.
See the [October stop](OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md)
and the [owner decision record](../decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md).

The checked-in verifier now checks the profile byte hash before either
OpenAPI reference, as required by [manifest contract §4](../contracts/sdk/COMPATIBILITY_MANIFEST_V1.md#4-최소-검증기).
See the [profile hash block](../../sdk/compat/verify_compat.mjs#L146-L150)
and the [ordered conformance regression](../../sdk/conformance/conformance.test.mjs#L364-L409).
The §4 interpretation of `extension_profile` remains `UNDETERMINED` with
the User.

The tuple's 18 artifact entries omit the verifier. The handoff records its
exact byte identity and the bootstrap-2 manifest digest so the order result
can be traced to the verifier and manifest tested together.
See the [SD1 handoff validation record](../../validation/2026-11-19-plan-producer-sd1-evidence-handoff/README.md).

On detached copies of `bootstrap-2` and `commerce-fixture-8ba7f6c-1`, the
recorded verifier reported `extension_profile bytes drift` after `profile bytes drift`
in the profile pair and after `sdk_output bytes drift` in the SDK output pair.
The §4 interpretation remains `UNDETERMINED` with JunTae.
See the [verifier identity and six verdicts](../../validation/2026-11-25-plan-producer-extension-order-evidence/README.md).

Semantic SDK consumption remains `HOLD_SEMANTIC`. The BOOTSTRAP profile
binds catalogue/schema bytes only. External consumer acceptance remains
`UNVERIFIED`. See the [consumer binding index](COMMERCE_CONSUMER_BINDING_INDEX_V1.json).

## Checker

```bash
python3 -B scripts/check_producer_qualification_tuple.py
python3 -B scripts/check_producer_qualification_tuple.py --self-test
```

The checker reads the archived `bootstrap-2` inputs (via
`scripts.bootstrap_2_fixtures.read_bootstrap_2_input`), recomputes every
recorded sha256 and Git-blob digest, re-derives the 84/40/44 command counts and
the 44 FSM actions from those pinned artefacts,
derives unique owners and point/list kinds for the 13 read names from the five
pinned fixture bodies, cross-checks fixture/manifest/tuple name sets, the exact
manifest file set, file digests and tuple artifact pins, cross-checks the manifest,
profile, sidecar and toolchain, and refuses drift. It asserts identity only; it
does not qualify anything. `--self-test` mutates in-memory copies and requires
detection of a mutated blob digest, a missing command and a mismatched gate
source pin. Detached record mutations also exercise semantic status/surface
promotion, read query/surface promotion, SD1 status and owner changes, each
forbidden SD1 resolution field, a normative claim, each required non-claim,
missing/duplicate read names, and candidate path/binding/digest drift. Each
false-promotion control requires its specific existing diagnostic; unrelated digest or
count failures cannot satisfy it. The original tuple is revalidated after
the controls.

The checker requires each tuple `candidateVector` to be the unique fixture
containing that query, with kind matching both fixture and manifest. Detached
controls for every query consistently re-pin changed fixture bytes, manifest
file hashes, tuple artifact SHA-256/Git blobs and query fixture hashes. They
reject coordinated path/digest rebinding, missing/duplicate ownership and
fixture/manifest/tuple kind disagreements through specific diagnostics:
`read query association missing`, `duplicate`, `path mismatch` and `kind mismatch`
(with the query name and kind source). These controls also require absence of
incidental digest failures. An association-preserving re-pin must pass, malformed
fixture/manifest inputs must be rejected without throwing, and the original
inputs must remain unchanged and pass afterward. No second ownership table is
hardcoded. See [association coverage and actual local validation
evidence](../../validation/2026-11-17-plan-producer-read-association-check/README.md)
and the preserved [false-promotion control
evidence](../../validation/2026-11-16-plan-producer-hold-negative-controls/README.md).

This closes the coordinated path-and-digest rebinding limitation for the pinned
fixture bodies. It establishes internal identity consistency, not semantic
correctness or authenticity if all source artifacts and pins are rewritten
together. Visibility, pagination limits, cursor lifetime, ordering, open-listing
phases, retention and query-digest policy remain `UNDETERMINED`. Qualification
statuses, SDK verifier behavior and SD1 ownership/status are unchanged.
