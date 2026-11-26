# Commerce readiness refusal verification

Node `plan-producer-commerce-readiness-refusals` uses the supervisor-supplied
task envelope from planner run `1795732059`. This node has no task issue or
separate document under `docs/tasks/`. The branch
`agent/kix-plan-producer-commerce-readiness-refusals` and the preloaded local
`origin/main` both pointed to `212d4c000b69231c26780c0889134c5ea96dd5f9` at
entry. The supervisor reserved GitHub actions, so the base was verified locally.
The implementation is an uncommitted worktree diff.

## Coverage

| Acceptance | Prior coverage | Local evidence for this node |
|---|---|---|
| Validate 28 distinct listed envelopes | Partial for gate dispatch. `CommerceFixtureTupleTests.test_vectors` parses and replays the tuple corpus directly. `CommerceJourneyEnvelopeTests.test_every_journey_envelope_is_preserved` parses an older journey with 27 distinct actions. | `CommerceReadinessTests.test_all_listed_actions_refused` derives 28 unique listed vector IDs, verifies action, context and step against the qualification table, and compares every parsed envelope to the original fields, including `body.idempotency_key`. |
| Refuse before FSM execution or append | Partial. `TransportTests.test_readiness_directory_refuses_fsm_commands` exercises `settlement_initiate` over loopback and checks the imported refusal constant. | In process, all 28 returned 422 with `READINESS_FSM_REFUSED`, `rejected=true` and `journalDecision=not_attempted`. Both spies recorded zero calls after each dispatch. The real temporary readiness journal kept zero records and its initial committed byte count. |
| Hold the exact refusals in the SDK | Uncovered for readiness refusals. The existing SDK suite qualified exact listed outcomes and held mismatches and control-only vectors. | Each refusal returned `HOLD_SEMANTIC` with a null vector ID. Each identical request with its listed outcome returned `SEMANTIC_CONFORMANCE` with the selected vector ID. The selector used the pinned Commerce manifest digest and made zero transport calls. |
| Clock control with readiness disabled | Partial. Direct FSM receipt replay already covered the clock. | `CommerceReadinessTests.test_listed_clock_without_readiness` dispatched `booking-admission/reservation-clock` with empty setup. The fresh host returned 200, called the FSM once with the listed body, reported `journalDecision=inactive` and matched the complete reference receipt with JSON type distinctions. |
| 13 reads retain `NOT_BOUND` | Sufficient. The existing SDK subtest `preserves the unbound reads and proposed recovery lookup` checks the 13 binding index names and the separate recovery lookup. | The existing subtest passed with null vector IDs for all 13 reads. |
| Evidence map and required citations | Partial. `K-READINESS-FSM-REFUSED` cited the single HTTP case and OpenAPI validation. | The row also cites the two socket-free gate tests. The checker self-test rejects deleting or fabricating either citation. |

The [shared test record](../../sdk/conformance/vectors/commerce-readiness-refusals.vectors.json)
lists the 28 observed payloads and exact source vector IDs in action order.
Selection uses the lexicographically smallest listed vector ID for each action
from the [qualification table](../../docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json)
and [request-to-receipt corpus](../../sdk/conformance/vectors/commerce-fixture-tuple.vectors.json).
The clock receipt is the first step in the [journey receipt fixture](../../reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json).

## Verification

Commands ran from the repository root on Python 3.12.15 and Node 24.22.1.
The focused gate tests ran first. A Python heredoc captured the shared test
record by dispatching all 28 parsed vectors under the module socket guard.

| Command | Result |
|---|---|
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits.CommerceReadinessTests` | Passed twice, 2 tests each run, including 28 refusal subcases. |
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits` | Passed twice, 13 tests each run. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -p 'test_commerce_fixture_tuple_conformance.py'` | Passed, 9 tests. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Passed, 1,096 tests. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest readiness.test_faults` | Passed, 98 tests. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Passed, manifest SHA-256 `76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`. |
| `npm --prefix sdk run conformance` | First run failed with `StrictJsonError: whitespace` on the formatted test record. The rerun passed all 30 tests after using the SDK suite's JSON loader pattern for formatted test data. |
| `npm --prefix sdk run verify-compat` | Passed for `bootstrap-2`. |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py` | Passed twice, 54 rows, 37 covered, 16 partial, 1 not covered. |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py --self-test` | Passed, 106 negative controls and the positive controls. |
| `python3.12 -B scripts/check_evidence_map_rollup.py` and with `--self-test` | Both passed, including 16 negative controls. |
| `python3.12 -B scripts/check_openapi_contract.py` and with `--self-test` | Both passed. The contract pin lists 40 core and 44 FSM actions. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and with `--self-test` | Both passed. |
| `python3.12 -B scripts/check_sdk_client.py` and with `--self-test` | Both passed. |
| `python3.12 -B scripts/check_ci_checker_wiring.py` and with `--self-test` | Both passed, including 13 negative controls. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and with `--self-test` | Both passed, including 18 negative controls. |

The KTX equivalents used Rust 1.98.1 and `CARGO_NET_OFFLINE=true`.
The workspace resolver required uncached `duckdb` metadata for
`kix-analytics-audit`. For the kernel fallback, `$ktx_manifest` points to an
ignored temporary workspace containing byte-identical copies of `kix-kernel`
and its sole dependency `kix-types`. The temporary workspace was removed
after the run.

| Command | Result |
|---|---|
| `python3.12 -B scripts/verify_runtime_architecture.py` | Passed the architecture and KTX-R1 dependency gate. |
| `python3.12 -B scripts/test_runtime_architecture.py` | Passed, 7 tests. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 101 during workspace resolution, before compilation. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101 during workspace resolution. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 101 during workspace resolution. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed for the original workspace. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Exit 0, emitted all three hashes. |
| `diff -qr` for each copied crate, `cargo generate-lockfile --manifest-path "$ktx_manifest"` and a `python3.12 -B` TOML comparison | Passed. Both crate copies and both lock entries matched the source inputs. |
| `cargo test --manifest-path "$ktx_manifest" -p kix-kernel --locked` | Passed, 139 tests. |
| `cargo clippy --manifest-path "$ktx_manifest" -p kix-kernel --all-targets --locked -- -D warnings` | Passed. |
| `cargo tree --manifest-path "$ktx_manifest" -p kix-kernel --edges normal --locked` | Passed, sole normal dependency `kix-types`. |

## Protected paths

| Check | Before and after |
|---|---|
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git rev-parse HEAD:reference/v0.3-rc1` | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 .aiops docs/tasks` and scoped `git status --porcelain --untracked-files=all` | No tracked or untracked changes. |
| `git diff --check` and `git status --short` | Whitespace check passed. Six intended deliverable paths. |
| Final `python3.12 -B` blob and whitespace audit using `git ls-tree -rz HEAD -- reference/v0.3-rc1` | All 108 tracked reference files matched HEAD byte for byte. Both new files passed whitespace checks. |

The booking discovery step also exercised an existing local loopback test.
Its child processes wrote ignored Python bytecode, which was removed after
the run. The focused gate coverage ran with socket creation disabled. The
dedicated HTTP gate, chain and proving suites were outside the local
verification for this node.

## Limits

The evidence is source-informed and exercises schema validation and dispatch
on one thread under the socket guard. `K-READINESS-FSM-REFUSED` remains
`PARTIAL` with 16 other FSM actions and broader HTTP coverage open. Astra owns
the refusal spelling. The existing Commerce fixture acceptance remains
`UNVERIFIED` externally. Product TTLs, fees, compensation, market visibility,
matching, pagination, and legal, accounting, and provider terms remain
`UNDETERMINED`.

This node supplied no production, public endpoint, live funds, live provider,
chain, distributed durability, or authentication evidence. The observed
behavior matched the contract. The work exposed no contract-undefined
behavior. Independent review at audit floor A2 and exact-head CI are pending
supervisor publication. KTX kernel and KIX protocol CI run IDs, statuses and
conclusions are unavailable for this uncommitted diff. No merge took place.
