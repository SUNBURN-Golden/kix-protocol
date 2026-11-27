# Commerce payment-observation lost-reply validation

`plan-commerce-payment-observation-lost-reply` uses the node specification and
design plan supplied in the builder brief from planner run `1795569040`. The
node has no issue or `docs/tasks/` document.

The cached `origin/main` and starting `HEAD` on
`agent/kix-plan-commerce-payment-observation-lost-reply` both resolved to
`e7f3eb92d4f78f954f96848cb29f9ee2f0e7296b`.
[Consumer handoff](../../docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md#consumer-handoff)

## Coverage

| Requirement | Existing coverage | Evidence in this change |
| --- | --- | --- |
| Exact setup and successful receipt | Sufficient. `CommerceFixtureTupleTests.test_booking_branch_full_receipts` and `test_booking_branch_receipt_mutations` cover complete booking receipts and detect changes. | Both fresh hosts replay the four setup calls in order and match their complete receipts. The hidden receipt matches canonical `booking-admission/payment-B` bytes. |
| Caller observation | Partial. `CommerceIssuanceLostReplyTests.test_both_losses_have_the_same_caller_observation` covers the loss pattern for `issue-B`. | `CommercePaymentObservationLostReplyTests.test_both_losses_have_the_same_caller_observation` binds both histories to the same original `payment-B` envelope and records identical operation and body keys, one attempt, `UNKNOWN`, null receipt and zero follow-up calls. |
| Request dropped before dispatch | Gap for `payment-B`. | All five state and journal snapshots match their baseline after `order-B`. The reservation remains `CONFIRMED` with a null payment reference. |
| Successful reply withheld | Partial. Booking branch tests cover the ordinary delivered receipt. | One dispatch reaches `PAYMENT_NOTED` with the pinned reference and creates exactly one reservation journal entry. The test preserves all journal prefixes and the other four machines' states. |
| Right and credential | Partial. The normal booking receipt covers the reservation and slot's right fields. | Slot 1 remains `RESERVED`, all show slots retain null right IDs, and the reservation carries no issuance, right, admission or consumption IDs. The admission credential list and journal are empty. |
| Recovery lookup | Sufficient. `proposed-uncertain-operation-recovery` in the grant-selection corpus expects `NOT_BOUND` and a null vector ID. | The replay checks the grant-selection vector and uses zero recovery or other follow-up calls. |

[Commerce tuple suite](../../reference/booking_resale_admission/test_commerce_fixture_tuple_conformance.py) ·
[Issuance replay](../../reference/booking_resale_admission/test_commerce_issuance_lost_reply.py) ·
[Payment-observation replay](../../reference/booking_resale_admission/test_commerce_payment_observation_lost_reply.py) ·
[Grant-selection vectors](../../sdk/conformance/vectors/producer-grant-selection.vectors.json)

## Source pins

| Input | SHA-256 | Git blob |
| --- | --- | --- |
| [Commerce tuple vectors](../../sdk/conformance/vectors/commerce-fixture-tuple.vectors.json) | `c9fbeee6a04da371dd054a325c9435a401b9694a1619ac9939de38f257495e22` | `0095e53801921e87c5417dd86920a625c2fede78` |
| [Booking branch receipts](../../reference/booking_resale_admission/fixtures/commerce_booking_branch_receipts_v1.json) | `1268382cdce28c931e160e253a6cafdac0f74de4124a53df1c78bd625f4b82c4` | `ab98cce8492b21b29871c4c1ad4ccda1a722d9ed` |
| [Journey receipts](../../reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json) | `6819d46a7b86e1a16bae83be90666560bb45aa66d3d6f0d5e050e03e7a952998` | `e9f34b8f35ed7f6a0867f1d2036bda521ee15eab` |

## Local verification

Commands ran from the repository root with Python 3.12.15, Node 24.22.1 and
Rust 1.98.1. `python3` used for the architecture gate was 3.13.5. In the table,
`$bra` is `reference/booking_resale_admission` and `$scratch` is the temporary
six-crate workspace's `runtime/Cargo.toml`.

| Command | Result |
| --- | --- |
| `git status --short --branch` and `git rev-parse origin/main HEAD` | Exit 0. Clean initial worktree on the expected branch with the cached base matching the plan. |
| `sha256sum` and `git hash-object` on the corpus and the two receipt goldens | Exit 0. Matched all three source pins listed above. |
| `python3.12 -B -m unittest discover -s "$bra" -t "$bra" -p "test_commerce_${suite}.py" -v` | Exit 0 for `payment_observation_lost_reply` (1 test, both fault points), `issuance_lost_reply` (1 test, both fault points) and `fixture_tuple_conformance` (9 tests). |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -` discovering `$bra` with `unittest` | Exit 0. All 1,085 offline tests passed. The filter excluded only `AdmissionFsmTests.test_loopback_rejects_fsm_names_and_matches_published_admit`, which opens a loopback socket. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"` | All seven invocations exited 0. `settlement_f01_f03` passed 224 tests, `credit_advance_f04` 328, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99. |
| `python3.12 -B -` running the `Stdlib offline document checks` commands extracted from `.github/workflows/protocol.yml` | All 68 invocations exited 0. This included `check_docs_index.py`, `check_ci_test_discovery.py`, `check_producer_qualification_tuple.py` and `check_consumer_binding_index.py`, each plain and with `--self-test`. The plain loopback socket probe was excluded. |
| `python3.12 -B` on `scripts/check_openapi_contract.py`, `scripts/check_integration_gate_openapi.py` and `scripts/check_sdk_client.py`, plain and with `--self-test` | All six invocations exited 0. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits readiness.test_faults` | Exit 0. All 109 tests passed. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. Verified manifest SHA-256 `76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`. |
| `npm_config_offline=true npm --prefix sdk run conformance` | Exit 0. All 27 tests passed, including the unbound recovery lookup. |
| `npm_config_offline=true npm --prefix sdk run verify-compat` | Exit 0. Verified `bootstrap-2`. |
| `python3.12 -B scripts/verify_commerce.py --report .local/verification/commerce-payment-observation.json` and `python3.12 -B scripts/verify_canonical.py --report .local/verification/canonical-payment-observation.json` | Both exited 0. The Commerce calculation and Python/TypeScript canonical agreement checks passed. |
| `python3 -B scripts/verify_runtime_architecture.py` and `python3 -B scripts/test_runtime_architecture.py` | Both exited 0. The architecture gate and all seven self-tests passed. |
| `cargo +1.98.1 fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo +1.98.1 test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 101 before compilation. The offline index lacked `duckdb` for `kix-analytics-audit`. |
| `cargo +1.98.1 clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` and `cargo +1.98.1 tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Both exited 101 with the same missing cache entry. |
| `cargo +1.98.1 test --manifest-path runtime/Cargo.toml --workspace --locked --offline` and `cargo +1.98.1 clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Both exited 101 with the same missing cache entry. |
| `python3.12 -B scripts/check_cargo_offline_cache.py` | Exit 0 in reporting mode. It found 14 of 378 locked registry packages cached. |
| `cargo +1.98.1 generate-lockfile --manifest-path <seven-crate workspace manifest> --offline` after copying the workspace without `kix-analytics-audit` and running `diff -qr` on each copied crate | All seven copies matched. Cargo exited 101 because the offline index also lacked `bcs` for `kix-bcs1`. |
| `cargo +1.98.1 generate-lockfile --manifest-path "$scratch" --offline` after copying the workspace without `kix-analytics-audit` and `kix-bcs1` and running `diff -qr` on each copied crate | Exit 0. All six copies matched and all selected package pins matched `runtime/Cargo.lock`. |
| `cargo +1.98.1 test --manifest-path "$scratch" --offline -p kix-kernel --locked --quiet` and `cargo +1.98.1 test --manifest-path "$scratch" --offline --workspace --locked --quiet` | Both exited 0. All 139 kernel tests and all 332 six-crate workspace tests passed. |
| `cargo +1.98.1 clippy --manifest-path "$scratch" --offline <scope> --all-targets --locked -- -D warnings` with `-p kix-kernel` and `--workspace` | Both exited 0. |
| `cargo +1.98.1 tree --manifest-path "$scratch" --offline -p kix-kernel --edges normal --locked` | Exit 0. The normal dependency was `kix-types`. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Recorded the KTX workflow input hashes. |
| `git rev-parse HEAD:reference/v0.3-rc1`, `git hash-object` on both kernel locks, `git diff HEAD --exit-code` and `git ls-files --others` on protected paths | Exit 0. Both locked blobs and the frozen tree matched. The protected-path check found zero differences or additions. |
| `python3.12 -B -` checking frozen paths against `git ls-tree -rz HEAD` and resolving the four new documentation links | All 108 frozen files matched. The initial link check exited 1 because it included the neighboring refund list item. The corrected link selector resolved all four targets and exited 0. |
| `git diff --check` and `python3.12 -B -` checking whitespace in the three new files | Both passed. |

## Preservation and delivery

| Protected input | Identity verified before and after |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | Git blob `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Git blob `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/` | Git tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` |

The supervisor's offline rule superseded the routine fetch. Remote freshness
is unverified. The changes are in the worktree and the implementation and
final task commit SHAs are pending. The A2 non-author review and exact-head
KTX and KIX workflow run IDs, statuses and conclusions are pending supervisor
delivery. Merge SHA and post-merge CI are inapplicable.

The original-workspace Rust tests and Clippy remain unverified because of the
missing cache entries. Socket-based HTTP checks, dependency bootstrap, local
chain, Move, ZK and storage probes were outside the offline checks for these
paths.

## Changed paths

- `docs/README.md`
- `docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.md`
- `reference/booking_resale_admission/fixtures/commerce_payment_observation_lost_reply_v1.json`
- `reference/booking_resale_admission/test_commerce_payment_observation_lost_reply.py`
- `validation/2026-11-25-plan-commerce-payment-observation-lost-reply/README.md`

## Scope

The replay exercises source-informed, synthetic in-process behavior. It found
zero contract violations or undefined behaviors. Recovery is `NOT_BOUND`,
and external Commerce acceptance is `UNVERIFIED`. Real funds, PG, bank, KYC,
production execution, chain finality, durability and distributed fencing are
outside this evidence. Product TTLs, fees, compensation and provider, legal
and accounting terms are `UNDETERMINED` with their existing owners.
[Reservation state machine](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md#9-예약발행-수락-상태-기계) ·
[Consumer recovery boundary](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#unavailable-consumer-bindings)
