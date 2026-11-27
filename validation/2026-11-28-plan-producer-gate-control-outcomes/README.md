# Commerce control outcomes at the offline gate

The task input for `plan-producer-gate-control-outcomes` is the supervisor's
node specification and design from planner run `1795791795`. There is no
issue or separate `docs/tasks/` document. Branch
`agent/kix-plan-producer-gate-control-outcomes` and cached `origin/main` both
resolved to `0ac862add494a052ff9da36d3e8ec5aa753a521e`, which matches the
design base. The supervisor's offline instruction precluded `git fetch origin main`.
Remote freshness is unverified. Implementation and final commit SHAs await
the supervisor's commit.

The gate test compares manifest revision `commerce-fixture-8ba7f6c-1` with
the independent consumer SHA-256
`76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`.
It verifies the four manifest vector-file pins, producer equality, and the
qualification table's replay dependency pins before building the inventory.
[Consumer pin](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification) ·
[Manifest](../../sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json) ·
[Qualification table](../../docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json)

## Coverage

| Requirement | Existing coverage | Gate evidence |
| --- | --- | --- |
| Exact control inventory and ordered setup | `CommerceFixtureTupleTests.test_inventory_and_edges` and `test_vectors` sufficiently cover the direct host. `CommerceGateDispatchTests.test_listed_outcomes` covers the 63 listed gate targets. | `test_control_outcomes` checks table membership, action, context, absence of `commerce_step`, unique IDs and complete corpus partition. It uses a fresh gate with `store=None` per target and checks each listed setup call's context, preceding prefix and outcome, including setup refusals. The executed-target counter has multiplicity one for each control. |
| Exact business refusals | Partial at the gate. `CommerceFixtureTupleTests.test_vectors` checks the codes directly. The prior gate test checks the seven listed refusals. | Each control refusal returns the complete typed `(422, {"error": code, "rejected": true})` outcome. Every dispatched control preserves the parsed envelope and has distinct operation and body keys and `journalDecision=inactive`. |
| Historical duplicate consumption | `CommerceFixtureTupleTests.test_vectors` covers the direct host. The historical receipt comparison through gate dispatch was uncovered. | `booking-admission/replay-consume-B` reuses the original action and body with a different `operationId`, after `double-consume` returned `ALREADY_CONSUMED`. Status 200 carries the complete receipt at `commerce_journey_receipts_v1.json#/steps/43/receipt`. It also matches the first consumption returned during setup with `duplicate=true` and `applied=null` substituted. |
| Schema rejection before dispatch | Partial at the gate. `CommerceFixtureTupleTests.test_vectors` checks the parser error. `CommerceJourneyEnvelopeTests.test_shared_faults_are_rejected_by_the_parser` covers other malformed envelopes. | `resale-market/missing-payment-ref` lacks `payment_ref` and raises `EnvelopeError` with `SCHEMA_REJECTED`. Spies record zero target calls to `gate.perform` and `gate.fsm.call`. |
| Full state and journal preservation | Partial at the gate. The direct replay checks control snapshots and the prior gate test checks listed refusals. | For each of 53 controls the test compares complete canonical state and exported accepted journals across reservation, resale, admission, settlement and credit. Failures name the vector and machine. |
| SDK semantic boundary | Sufficient. The `selects every listed outcome and holds every control-only vector` subtest in `sdk/conformance/conformance.test.mjs` checks all 53 controls under unlisted and listed step names. | The existing SDK check passed with `HOLD_SEMANTIC` and a null vector ID for every control. The listed gate replay and both existing gate mutation tests passed. |

| Context | Status 422 | Historical 200 | Parser rejection | Total |
| --- | ---: | ---: | ---: | ---: |
| `booking-resale` | 17 | 0 | 0 | 17 |
| `booking-admission` | 9 | 1 | 0 | 10 |
| `booking-refund` | 12 | 0 | 0 | 12 |
| `resale-market` | 13 | 0 | 1 | 14 |
| Total | 51 | 1 | 1 | 53 |

## Local verification

Python 3.12.15, Node 24.22.1, npm 11.21.1 and Rust/Cargo 1.98.1.
The focused test ran first. The booking discovery command includes an
existing local loopback transport test. The control replay uses the module's
socket guard throughout.

| Command | Result |
| --- | --- |
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits.CommerceGateDispatchTests.test_control_outcomes` | Passed. One test covering 53 targets. |
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits` | 17 tests passed. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -p 'test_commerce_fixture_tuple_conformance.py'` | 9 tests passed. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 1,099 tests passed. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0. The verifier returned the exact consumer digest above. |
| `npm --prefix sdk run conformance` | 30 tests passed, including the control-only grant check. |
| `npm --prefix sdk run verify-compat` | Passed for `BOOTSTRAP` revision `bootstrap-2`. |
| `python3.12 -B scripts/check_openapi_contract.py`, plain and `--self-test` | Both passed. The pin covers 84 commands. |
| `python3.12 -B scripts/check_integration_gate_openapi.py`, plain and `--self-test` | Both passed. |
| `python3.12 -B scripts/check_sdk_client.py`, plain and `--self-test` | Both passed. |
| `python3.12 -B scripts/check_ci_test_discovery.py`, plain and `--self-test` | Both passed, including 18 negative controls. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py`, plain and `--self-test` | Both passed. The identity check reports 84 commands and 13 reads. |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py`, plain and `--self-test` | Both passed, including 106 negative controls. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`, plain and `--self-test` | Both passed, including 10 negative controls. |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Architecture and KTX-R1 dependency check passed. |
| `python3.12 -B scripts/test_runtime_architecture.py` | 7 tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed in the original workspace. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 101 before compilation. The offline registry index lacked `duckdb`, required by `kix-analytics-audit`. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101 at the same workspace resolution step. |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 101 at the same workspace resolution step. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0. SHA-256 values in order are `ab1228db16a7ef37ecd9ef3aad88110685cb867349ad04cbd2b76ff8cb0539c5`, `84c8ef6cca3eb3eafc842639b32580c21b88731b34e83490db2fa84eecb1657f`, and `d404aa9bade8d9997872d0537a40813d49cbff1f6b60bf13bc385d613fc42bae`. |

The KTX fallback followed the preceding gate node's documented approach. A
temporary ignored workspace under `.local/` used copies of only `kix-kernel`
and `kix-types`. The harness removed the scratch workspace after use.
[Preceding gate validation](../2026-11-27-plan-producer-gate-dispatch-outcomes/README.md#local-verification)

| Command | Result |
| --- | --- |
| `diff -qr` on each original crate against its scratch copy | Both passed. |
| `CARGO_NET_OFFLINE=true cargo generate-lockfile --manifest-path runtime/Cargo.toml --offline` and Python 3.12 TOML comparison against the repository lock | Passed. Lock version and both package entries match the repository lock. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 139 tests passed in the isolated workspace. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Passed in the isolated workspace. |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Passed in the isolated workspace. The only normal dependency is `kix-types`. |

## Changed paths and preservation

- [`integration_gate/test_offline_limits.py`](../../integration_gate/test_offline_limits.py) adds the control replay and shares inventory, parsing, dispatch and setup checks with the listed replay.
- `validation/2026-11-28-plan-producer-gate-control-outcomes/README.md` records the builder's evidence.

| Command | Result |
| --- | --- |
| `git rev-parse origin/main HEAD` | Both refs match the supplied base before and after work. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both locks match before and after work. The blobs are `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `python3.12 -B -` byte audit using `git ls-tree -rz` at the base SHA | All 108 archive Git blobs matched at entry and on both final checks. The first final check failed because five generated bytecode files were present. The repeat check passed with zero extra files. |
| `python3.12 -B -` generated cache cleanup with timestamp and `git ls-files` checks | Removed 45 ignored Python 3.12 bytecode files created by the booking discovery's child processes, including the five archive extras. |
| `git diff --check`, scoped `git diff --exit-code HEAD`, and `git status --short --ignored --untracked-files=all` | Whitespace and protected-path checks passed. Worktree changes match the two listed paths. |

## Scope and delivery

The replay exposed zero contract discrepancies or undefined behaviors.
This source-informed evidence covers the parser and in-process gate for the
pinned synthetic fixtures. Dedicated HTTP, browser, Move, chain, ZK, storage
and production verification are outside this run. External Commerce
acceptance is `UNVERIFIED`. The 13 reads and operation recovery are
`NOT_BOUND`. Product TTLs, fees, compensation, market visibility, matching,
pagination and legal, accounting and provider terms are `UNDETERMINED`.

The independent A2 review and exact-head KTX kernel and KIX protocol CI run
IDs, statuses and conclusions are pending supervisor publication. Merge SHA
and post-merge CI are inapplicable to this worktree delivery.
