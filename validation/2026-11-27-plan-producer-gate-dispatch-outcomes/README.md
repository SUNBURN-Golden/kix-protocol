# Commerce outcomes at the offline gate

Node `plan-producer-gate-dispatch-outcomes` uses the supervisor's node specification
and design plan from planner run `1795774962`. The node has no issue or separate
`docs/tasks/` document. The branch `agent/kix-plan-producer-gate-dispatch-outcomes`
and cached `origin/main` both resolved to `dcbfef2826908985fc223ed0e2e07653105e9aa3`.
The supervisor's offline instruction precluded `git fetch origin main`.
The cached ref matched the requested base. Remote freshness is unverified.
The worktree diff has no implementation or final commit SHA.

The [qualification table](../../docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json)
binds Commerce fixture source `9a55fe4e257376f9db3f877a11b65e3ecc43c661` and
Protocol producer `8ba7f6c36373ac0ec49246f51f7471c164ac3a28` with tree
`d3f5412ef84f64fe83c5d3a3d3ada173921bfbf9`. The
[consumer pin](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification)
for manifest revision `commerce-fixture-8ba7f6c-1` is
`76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`.

## Coverage

| Requirement | Existing coverage | Gate evidence |
| --- | --- | --- |
| Verify bytes and enumerate listed outcomes | Sufficient for the direct replay. `CommerceFixtureTupleTests.test_inventory_and_edges` binds the action and context edges. `test_replay_dependency_bytes_and_producer` checks the table's file pins. The SDK's Commerce semantic manifest test checks the scope and vector bytes. | Before dispatch, the gate tests verify the independent manifest SHA-256, all four manifest vector-file pins, all 37 table file pins by SHA-256 and Git blob, producer equality and both receipt companions' corpus pins. They walk the table's listed edges for 28 actions. |
| Exact first success receipts and journal deltas | Partial at the gate. `CommerceFixtureTupleTests.test_all_first_acceptances_resolve` checks all 56 full receipts at the FSM host. `CommerceFixtureTupleTests.test_vectors` checks journal deltas. `CommerceReadinessTests.test_listed_clock_without_readiness` compares one full receipt at dispatch. | `CommerceGateDispatchTests.test_listed_outcomes` uses a fresh gate per target and checks every ordered setup call. It compares all 56 HTTP-style 200 payloads as complete canonical JSON and checks recorded deltas and retained journal prefixes across the five FSMs. The primary append must carry the recorded operation, subject and body idempotency key. |
| Exact business refusals with state and journal preservation | Partial at the gate. `CommerceFixtureTupleTests.test_vectors` checks direct-FSM refusals and preservation. `CommerceReadinessTests.test_all_listed_actions_refused` exercises the readiness-enabled refusal path. | All seven listed business refusals return 422 with the complete typed error payload. All five FSMs preserve their canonical state and exported journal on refusal. This includes the setup refusal before resale settlement commit. |
| Detect a swapped receipt or refusal code | Uncovered at gate dispatch. The direct replay's market and booking companion mutation tests cover other receipt changes. | `CommerceGateDispatchTests.test_swapped_outcomes_fail` checks genuine responses first. It exchanges the two market cancellation receipts and the `SLOT` and `SLOT_OCCUPIED` refusal codes in detached memory. The same outcome assertion fails in both directions for each pair. |

| Context | 200 | 422 |
| --- | ---: | ---: |
| Booking resale | 18 | 4 |
| Booking admission | 10 | 2 |
| Booking refund | 14 | 1 |
| Resale market | 14 | 0 |
| Total | 56 | 7 |

The receipt sources supply 32 direct journey references, 14 market companion
receipts and 10 booking companion receipts. Both market cancellation branches
are listed targets. The after-payment market cancellation is a control. Every
setup and target envelope passes through `parse_envelope` and
`GateServer.perform` with `store=None`, and each response reports
`journalDecision=inactive`. The test checks identity and typed body equality
after parsing. The shared helpers preserve direct-FSM replay coverage,
including the control vectors and companion mutations.

## Local verification

Python 3.12.15, Node 24.22.1, npm 11.21.1 and Rust/Cargo 1.98.1.
The focused gate tests ran first. Python checks used
`PYTHONDONTWRITEBYTECODE=1`, and Cargo used `CARGO_NET_OFFLINE=true`.

| Command | Result |
| --- | --- |
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits.CommerceGateDispatchTests` | Passed, 2 tests. |
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits` | Passed, 15 tests. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -p 'test_commerce_fixture_tuple_conformance.py'` | Passed, 9 tests. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Passed, 1,097 tests. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0 and the exact consumer digest above. |
| `npm --prefix sdk run conformance` | Passed, 30 tests. |
| `python3.12 -B scripts/check_openapi_contract.py`, with and without `--self-test` | Both passed. The catalogue lists 40 core and 44 FSM actions. |
| `python3.12 -B scripts/check_integration_gate_openapi.py`, with and without `--self-test` | Both passed. |
| `python3.12 -B scripts/check_sdk_client.py`, with and without `--self-test` | Both passed. |
| `python3.12 -B scripts/check_ci_test_discovery.py`, with and without `--self-test` | Both passed. The existing workflow reaches both suites. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py`, with and without `--self-test` | Both passed. |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py`, with and without `--self-test` | Both passed, including 106 negative controls. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`, with and without `--self-test` | Both passed, including 10 negative controls. |
| `npm --prefix sdk run verify-compat` | Passed, `BOOTSTRAP` profile `bootstrap-2`. |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Passed the architecture and KTX-R1 dependency checks. |
| `python3.12 -B scripts/test_runtime_architecture.py` | Passed, 7 tests. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed in the original workspace. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 101 before compilation. The offline index lacked `duckdb` for `kix-analytics-audit`. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101 during the same workspace resolution. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 101 during the same workspace resolution. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. Hashes in order are `ab1228db16a7ef37ecd9ef3aad88110685cb867349ad04cbd2b76ff8cb0539c5`, `84c8ef6cca3eb3eafc842639b32580c21b88731b34e83490db2fa84eecb1657f`, and `d404aa9bade8d9997872d0537a40813d49cbff1f6b60bf13bc385d613fc42bae`. |

For the offline KTX equivalent, an ignored scratch workspace contained copies
of `kix-kernel` and its sole dependency `kix-types`. The commands below ran
from that workspace except the crate and lock comparisons, which ran from
the repository root. The scratch workspace was removed after verification.

| Command | Result |
| --- | --- |
| `diff -qr` between each original crate and its scratch copy | Both passed. |
| `cargo generate-lockfile --manifest-path runtime/Cargo.toml --offline` and a `python3.12 -B` TOML comparison against the repository lock | Passed. Both package entries match their entries in the repository lock. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Passed, 139 tests. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Passed. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Passed. The sole normal dependency is `kix-types`. |

## Changed paths and preservation

| Path | Change |
| --- | --- |
| [`integration_gate/test_offline_limits.py`](../../integration_gate/test_offline_limits.py) | Socket-free gate replay and outcome mutation checks. |
| [`reference/booking_resale_admission/commerce_tuple_assertions.py`](../../reference/booking_resale_admission/commerce_tuple_assertions.py) | Shared fixture paths, snapshot, receipt reference and journal checks. |
| [`reference/booking_resale_admission/test_commerce_fixture_tuple_conformance.py`](../../reference/booking_resale_admission/test_commerce_fixture_tuple_conformance.py) | Use shared assertions in the direct-FSM replay. |
| `validation/2026-11-27-plan-producer-gate-dispatch-outcomes/README.md` | Builder validation. |

| Check | Result |
| --- | --- |
| `git rev-parse refs/remotes/origin/main HEAD` | Both matched the recorded base at entry and completion. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Matched both locks before and after work, `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git rev-parse HEAD:reference/v0.3-rc1` and a Python byte audit using `git ls-tree -rz HEAD -- reference/v0.3-rc1` | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` at entry and completion. All 108 tracked worktree blobs match HEAD. |
| Scoped `git diff --exit-code HEAD` and `git status --porcelain=v1 --ignored --untracked-files=all` | Protected files, task inputs, fixture and SDK bytes, and workflows passed the preservation checks. |
| `git diff --check` and a Python whitespace check of the four deliverables | Passed. |

## Limits and delivery

This is source-informed evidence for synthetic in-memory FSM dispatch.
External Commerce acceptance is `UNVERIFIED`. The 13 reads and operation
recovery remain `NOT_BOUND`, and unresolved writes stay fenced. Product TTLs,
fees, compensation, market visibility, matching, pagination and legal,
accounting and provider terms remain `UNDETERMINED`. The tested dispatch
exposed no contract violation or undefined behavior. `COMPENSATION_UNDEFINED`
is a recorded business refusal.

Local verification is scoped to the touched paths and their dependencies.
The booking discovery step exercised an existing local loopback test.
The dedicated HTTP transport, browser, Move, chain, ZK and storage suites
are outside this run. The evidence covers neither production behavior nor
live funds, provider integrations, authentication or distributed durability.
The supervisor owns publication. The independent A2 review and exact-head
KTX kernel and KIX protocol CI run IDs, statuses and conclusions are pending.
No merge or post-merge CI applies to this worktree diff.
