# Commerce published read bindings by transport

The task document is the supervisor-supplied node `plan-producer-read-binding-by-transport`
from planner run `1795850668`. The node has no GitHub task issue or file under
`docs/tasks/`. The cached `origin/main`, base, and task branch HEAD at entry
were all `621f2e262ebb309e9c5534711a207007e3274aee` on
`agent/kix-plan-producer-read-binding-by-transport`.

The companion record uses `(manifest_sha256, method, path, query)` as its
lookup key. Each `request_schema_ref` points to the local-call `body` schema
or to the full resale request schema. The local-call query is the envelope's `action`.
`request_subject` is a field path from the request root.
`null` denotes the list query, which requires an actor and addresses no single
entity. `response_envelope` lists one entry per published response shape.
Recovery entries include the status and retry flag, with both fields at the
top level for `UNKNOWN`. The references point to the observed point-query
response keys and to the wire schema of each resale fixture HTTP 200 response.
[Companion record](../../docs/status/COMMERCE_READ_BINDING_BY_TRANSPORT_V1.json)

## Coverage

| Requirement | Existing coverage | Added evidence |
|---|---|---|
| Ten point queries and six fixture routes | Sufficient for fixture behavior. `ReadQueryLoopbackTests.test_admission_path_then_all_point_queries` and `ResaleReadTransportTests` in `integration_gate/test_http_gate.py` cover point views, fixture scope, pagination, recovery and nonmutation. Cross-manifest discovery was uncovered. | `published read binding lookup` in `sdk/conformance/conformance.test.mjs` derives both sets from the verified artifacts, resolves the schema pointers and checks all 16 lookups across 12 names. |
| Shared names, settlement subjects and response envelopes | Partially covered. `ResaleReadTransportTests.test_bound_companion_visibility_freshness_and_nonmutation` and `test_qualified_settlement_binding_preserves_distinct_trade_id` exercise settlement by listing. The point-query test obtains it by settlement ID. | Resolves `get_listing`, `get_right`, `get_presentation` and `get_settlement` on both transports and asserts the settlement subjects and distinct payload keys. Checks all three recovery response variants. |
| Manifest and route swaps | Partially covered. SDK compatibility tests already reject gate byte drift. Lookup key mismatches were uncovered. | Rejects individual manifest, method and route substitutions for each shared name in both directions, and a different valid resale suffix with the original query. |
| Historical scope, current grants and pending reads | Sufficient for historical scope. The existing consumer binding checker and `Commerce grant lookup` cover the historical 84-action records. The new index and product rows were uncovered. | Verifies the historical index digest, both manifest and profile pairs, each grant, the local `HOLD_SEMANTIC` and all seven `NOT_BOUND` product rows. Rejects a broadened grant and a promoted pending read. |
| Capability register and compatibility | Partially covered by the status register, docs index and SDK checks. | Checks the new link in the K3 row and verifies both producer manifests during lookup. `verify-compat` selects the local-call manifest. |

## Local results

Verification used Node 24.22.1, Python 3.12.15 and Rust 1.98.1.

| Command run from repository root | Result |
|---|---|
| `node --test --test-name-pattern='published read binding lookup\|Commerce grant lookup' sdk/conformance/conformance.test.mjs` | Initial run had 15 passes and one failure because the canonical parser rejected formatted OpenAPI JSON. After switching the formatted documents to the repository's `JSON.parse` convention, all 16 passed. Canonical profiles still use `parseStrict`. |
| `python3.12 -B -m unittest integration_gate.test_http_gate.ReadQueryLoopbackTests integration_gate.test_http_gate.ResaleReadTransportTests` | 16 passed. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py`, with and without `--self-test` | Both passed as part of the workflow document checks. |
| All Python invocations under **Stdlib offline document checks** in `.github/workflows/protocol.yml`, run as `python3.12 -B` | 69 of 69 passed, including `check_status_register.py` and `check_docs_index.py` and their self-tests. |
| `python3.12 -B scripts/check_sdk_client.py`, with and without `--self-test` | Both passed. The catalogue pin covers 94 actions. |
| `python3.12 -B scripts/check_sdk_client.py --verify-source` | Passed. The read-model producer source commit, tree and input bytes matched. |
| `npm --prefix sdk run verify-compat` | Passed. The `read-model-reference-1` digest matched `3b4b8dafb0c9339f4a4e82866b1fb79d55fa61d4e73b0f9923a0e13aef6b2da8`. The new lookup test also verified `commerce-resale-read-transport-1` at `a3fe9d4a96ee4d27881423f88de104aa77e44000c14890e75662e76f7d205bbe`. |
| `npm --prefix sdk run conformance` | 33 passed. |
| `python3.12 -B -m unittest integration_gate.test_http_gate readiness.test_faults` | 156 passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -B -m unittest discover -s "reference/$suite" -t "reference/$suite"`, for the eight reference suites from the protocol workflow | All eight passed. `settlement_f01_f03` 225, `booking_resale_admission` 1,109, `credit_advance_f04` 342, `ai_delegation` 182, `token_reward` 397, `provider_facts` 86, `payment_effects` 28 and `economics` 99. Total 2,468. |
| `python3.12 -B scripts/check_openapi_contract.py` and `python3.12 -B scripts/check_integration_gate_openapi.py`, each with and without `--self-test` | All four passed. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 19 passed. |
| `python3.12 -B scripts/verify_commerce.py --report "$report_dir/commerce.json"` and `python3.12 -B scripts/verify_canonical.py --report "$report_dir/canonical.json"`, with a temporary report directory | Both passed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture gate passed, including seven regression tests. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. |
| `cargo test --offline --manifest-path runtime/Cargo.toml <scope> --locked` and `cargo clippy --offline --manifest-path runtime/Cargo.toml <scope> --all-targets --locked -- -D warnings`, each with `-p kix-kernel` and `--workspace` | All four exited 101 resolving the uncached `duckdb` dependency of `kix-analytics-audit`. |
| `cargo tree --offline --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 101 for the same dependency. |
| `python3.12 -B scripts/check_cargo_offline_cache.py` | The archive inventory reported 16 present and 362 missing from the workspace lockfile. |
| `cargo test --offline --manifest-path <subset>/Cargo.toml -p kix-kernel --locked`, `cargo clippy --offline --manifest-path <subset>/Cargo.toml -p kix-kernel --locked --all-targets -- -D warnings`, and `cargo tree --offline --manifest-path <subset>/Cargo.toml -p kix-kernel --locked --edges normal` | Byte-identical copies of `kix-kernel` and `kix-types`, confirmed with `diff -qr`, in a temporary workspace with those two package entries from the repository lockfile. All 139 tests passed, Clippy passed and the normal dependency tree contained only `kix-types` below the kernel. |
| `cargo test --offline --manifest-path <subset>/runtime/Cargo.toml --workspace --locked` and `cargo clippy --offline --manifest-path <subset>/runtime/Cargo.toml --workspace --locked --all-targets -- -D warnings` | In a second temporary workspace with byte-identical copies and lock entries for the six crates with only workspace dependencies, 332 tests passed and Clippy passed. `kix-analytics-audit` and `kix-bcs1` were outside this workspace. |
| `git hash-object` on both kernel locks before editing and `git hash-object --no-filters` after editing | `runtime/crates/kix-kernel/src/lib.rs` matched `69564b166f0c27f9af5d8422f0a466b18d74c20f`. `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` matched `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git diff --check HEAD`, `git diff --exit-code HEAD -- .aiops docs/tasks .github/workflows sdk/compat sdk/conformance/fixtures/bootstrap-2-inputs.json.gz docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json reference/v0.3-rc1`, and a raw Git blob comparison against `git ls-tree -r -z HEAD -- reference/v0.3-rc1` | Whitespace check passed. The listed paths had no diff. All 108 frozen reference files matched the base bytes. |

## Changed paths

- `docs/README.md`
- `docs/status/COMMERCE_READ_BINDING_BY_TRANSPORT_V1.json`
- `docs/status/CURRENT_CAPABILITY_REGISTER.md`
- `sdk/conformance/conformance.test.mjs`
- `validation/2026-11-28-plan-producer-read-binding-by-transport/README.md`

## Delivery scope

The supervisor prohibited network and GitHub actions, so the base comparison
used the cached `origin/main` ref. The builder's patch is in the worktree.
The implementation, final task and merge commit SHAs are pending with the
supervisor. Both exact-head workflows, KTX kernel verification and KIX protocol
verification, have no run ID, status or conclusion for this uncommitted patch.
Post-merge verification and non-author A2 review are pending delivery.

No contract violation or contract-undefined behavior was found in the indexed
surfaces. The 94-action profile has `grants: "none"` and `HOLD_SEMANTIC`.
The resale profile grants `local fixture resale reads only`. Product policy,
legal, privacy, accounting and provider facts remain `UNDETERMINED`, and external
Commerce acceptance remains `UNVERIFIED`. The evidence covers offline lookup
and synthetic loopback behavior. Full-workspace Cargo, hosted workflows, and the
Move, local-chain and proving stages remain outside the local results. Those
stages require their offline dependencies or the supervisor's CI environment.
