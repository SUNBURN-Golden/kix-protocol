# Commerce fixture tuple conformance validation

Task `kix-commerce-fixture-tuple-conformance` uses the supervisor-supplied node
specification and implementation plan. The node has no issue or standalone
task document. The task branch and cached Protocol `origin/main` started at
`ed086b3621b6a4f8dd55ffcb5d1f8d163387a250`. The qualification target is the
earlier Protocol `8ba7f6c36373ac0ec49246f51f7471c164ac3a28`, tree
`d3f5412ef84f64fe83c5d3a3d3ada173921bfbf9`. The branch base and qualification
target serve different purposes. The supervisor owns publication and GitHub
verification. The worktree changes have no implementation or final commit SHA
during the builder session.

## Coverage

| Requirement | Earlier coverage | Evidence added |
| --- | --- | --- |
| Exact inventory and bytes | Partial. `scripts/check_producer_qualification_tuple.py` establishes expanded catalogue identity. | Compare 28 declared actions with the implemented fixture paths in the cached Commerce `origin/main` at `9a55fe4e257376f9db3f877a11b65e3ecc43c661`. Record source digests and reachable branch and alternative step IDs. Check dispatch metadata, schema digests, dependency bytes and table edges. |
| Booking acceptances and refusals | Partial. `test_commerce_journey_receipts.py` pins a shared 44-step transcript with 27 actions. `test_commerce_bound_resale_vectors.py` covers withheld transfer before mock commit and retained rejection. `test_reservation_fsm.py::test_cancel_before_payment_frees_and_payment_blocks_compensation` covers paid cancellation. | Replay individual Commerce booking branches with actual before/after decline placements, both paid-cancellation refusals and one schema-valid business refusal for each action in each context. Reuse 33 full receipt references when bytes match and the pinned booking expectations otherwise. |
| Market | Partial. `test_resale_fsm.py::test_buy_hold_is_optional_and_cancel_order_decides_the_race` covers cancellation phases, and the earlier market source fixtures supply synthetic setup. | Replay exact market envelopes, both reachable cancellation positions, after-payment refusal and the unbound transfer. Check version, holder, payment reference and settlement facts. |
| Portable envelope and qualification manifest | Partial. `sdk/conformance/conformance.test.mjs` covers catalogue schemas, booking envelopes and BOOTSTRAP pin failures. | Verify the scoped manifest and shared envelopes, including a schema refusal before transport, a mixed profile, a mixed vector digest and substitution of BOOTSTRAP. |
| Consumer handoff | Missing scoped semantic grant. The existing binding and companion indexes record BOOTSTRAP scope and sources. | Provide a separate manifest-v1 profile, table and consumer note. |

The 116 vectors contain 56 first acceptances, 58 FSM business refusals,
one duplicate and one schema refusal. Ordered setup is explicit. The producer
test checks typed receipts, exact refusal codes, unchanged business state and
journals on rejection or duplicate, and journal append and subject invariants
on first acceptance. The published vectors are source-informed.

## Pin comparison

Local Git object reads compared the table's producer byte pins with the pinned
Protocol tree and the working bytes before replay. The Commerce `origin/main`
fixture sources and the matching vendored OpenAPI and SDK artifacts were read
from the cached Commerce Git object. The 33 receipt references point to
separately pinned evidence added after the qualification target and checked
against the pinned behavior. The SDK verifier used for the local run is the
current `sdk/compat/verify_compat.mjs` with SHA-256
`8628518c41b4110f0adf9a5d841240ae06dc6c1fa5d5c4974f00d96a718c5de6`.
The target's verifier, which matches Commerce's vendored verifier, has SHA-256
`b1ed26b977666f796a68c5de0a108e5558ca3c98486dc188d385b220a448cf89`.
The change between these verifier versions moves the profile digest check
earlier. The producer FSM replay uses the historical dependency bytes.

No contract violation or new undefined FSM characterization was found in
the tested scope. `COMPENSATION_UNDEFINED` is a specified refusal.
Product values and reads listed in the consumer note remain open.
The evidence covers synthetic in-memory execution and SDK envelope dispatch.
Consumer integration, browser behavior, production, live providers, real
funds, durability, chain authority and N/N−1 are outside this run.

## Local results

Python 3.12.15, Node 24.22.1 and Rust/Cargo 1.98.1. Cargo used
`CARGO_NET_OFFLINE=true` and a target directory under `/tmp`.

| Command | Result |
| --- | --- |
| `git rev-parse origin/main HEAD`, `git rev-parse 8ba7f6c 8ba7f6c^{tree}`, `git -C /workspace/commerce-run/repo rev-parse origin/main` | Cached refs and producer commit/tree matched the pins above. |
| `PYTHONPATH=.:reference/booking_resale_admission python3.12 -B /tmp/kix-commerce-tuples-build.py` | One-off local authoring script compared Git blobs, generated the canonical pack and observed 116 vectors with 33 matching full receipt references. The initial probe exposed a reservation journal append during admission clock setup, which was added to the expected delta before rerunning. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -p 'test_commerce_fixture_tuple_conformance.py'` | 4 passed. Early harness runs exposed a control classified as a reachable step, an incorrect shape assumption for the OpenAPI operations list and an extra key lookup on the listing view. Those harness errors were corrected before the passing run. |
| `node --test --test-name-pattern='Commerce semantic' sdk/conformance/conformance.test.mjs` | 2 passed. The initial run found a null-prototype comparison issue in the recording transport assertion. The corrected test compares canonical envelope bytes. |
| `python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward`, `provider_facts`, `payment_effects`, `economics` | 2,383 passed across all eight suites (224, 1,062, 305, 182, 397, 86, 28 and 99 respectively). |
| `python3.12 -B -m unittest integration_gate.test_offline_limits integration_gate.test_http_gate readiness.test_faults` | 150 passed. Existing loopback tests emitted a subprocess file `ResourceWarning` and completed successfully. |
| `npm --prefix sdk run conformance` and `npm --prefix sdk run verify-compat` | 12 SDK tests passed and the BOOTSTRAP verifier passed. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | PASS, manifest SHA-256 `76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`. The same invocation passed in a temporary tree using verifier bytes read by `git show 8ba7f6c:sdk/compat/verify_compat.mjs`. |
| `python3.12 -B scripts/check_<name>.py` plain and with `--self-test` for `openapi_contract`, `integration_gate_openapi`, `sdk_client`, `producer_qualification_tuple`, `docs_index`, `ci_test_discovery`, `sdk_compat_manifest_evidence_map`, `ci_checker_wiring` | All passed. The discovery checker reached the booking directory through the existing protocol workflow. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed and 7 architecture tests passed. |
| `python3.12 -B scripts/verify_commerce.py --report /tmp/kix-commerce-tuple-commerce.json` and `python3.12 -B scripts/verify_canonical.py --report /tmp/kix-commerce-tuple-canonical.json` | Both passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` and `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Kernel tests and Clippy passed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` and `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Workspace tests and Clippy passed. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` and `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Both dependency evidence commands succeeded. |

## Protected files and delivery

`git hash-object` matched both locks before and after work.

- `runtime/crates/kix-kernel/src/lib.rs` — `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` — `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --exit-code 8ba7f6c -- reference/v0.3-rc1` confirmed the checked-in
reference bytes. The protected paths also passed the worktree comparison
against `HEAD`.

| Changed path | Purpose |
| --- | --- |
| `docs/README.md` | Index the handoff and validation. |
| `docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json` | Qualification table, exact pins and coverage edges. |
| `docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md` | Consumer handoff and replay instructions. |
| `reference/booking_resale_admission/test_commerce_fixture_tuple_conformance.py` | Producer replay and inventory controls. |
| `sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json` | Scoped manifest. |
| `sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json.sha256` | Manifest digest. |
| `sdk/compat/profiles/commerce-fixture-8ba7f6c-1.profile.json` | Fixture-only grant with the unchanged catalogue identity. |
| `sdk/conformance/conformance.test.mjs` | SDK transport and manifest controls. |
| `sdk/conformance/vectors/commerce-fixture-tuple.vectors.json` | Portable envelopes, setup and expected outcomes. |
| `validation/2026-11-20-kix-commerce-fixture-tuple-conformance/README.md` | Builder evidence. |

The supervisor's offline rule took precedence over `git fetch origin main`.
Some child processes in the broad local tests wrote ignored Python bytecode.
Those caches were removed before the final protected-path check.
Hosted CI, non-author exact-head review and merge are supervisor-side work.
There are no exact-head KTX or KIX run IDs, implementation/final commit SHAs
or merge commit SHA for this worktree delivery. The hosted dependency bootstrap,
Move, Sui localnet and ZK workflows are outside the local checks for these paths.
