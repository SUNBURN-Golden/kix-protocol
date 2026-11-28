# Commerce fixture grant selection

Task `plan-producer-grant-selection-vectors` uses the supervisor's node specification and design plan from planner run `1795168746`. There is no issue or corresponding `docs/tasks/` input. [Consumer procedure](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification)

Cached `origin/main`, the task base and the starting and ending branch HEAD all resolve to `4208658815d21c99513c739e1a82bb625468c8b5` on `agent/kix-plan-producer-grant-selection-vectors`. Remote freshness is unverified under the supervisor's offline instruction. The implementation is a working-tree patch. The supervisor will establish the implementation and final commit SHAs. KTX kernel CI, KIX protocol CI and A2 non-author review await that exact head. Merge and post-merge CI are inapplicable to this builder run.

## Coverage

| Requirement | Existing coverage before this task | Added evidence |
| --- | --- | --- |
| Match the scoped manifest, producer and schema | Sufficient for verifier, dependency pins and catalogue identity. `Commerce semantic manifest binds the exact fixture scope and vector bytes`, `test_replay_dependency_bytes_and_producer` and `test_inventory_and_edges` check those inputs. | Test-local lookup verifies the requested manifest and compares its pinned evidence with the portable request. Wrong producer tree, schema digest and bootstrap grant yield `HOLD_SEMANTIC`. |
| Distinguish the two cancellation histories | Partial. `test_inventory_and_edges` proves both table edges and `test_vectors` replays both histories on fresh hosts and checks their receipts. Consumer selection was uncovered. | The nine-vector `LISTED` and ten-vector `BUY_HELD` requests select their own IDs. Crossing the histories or reordering the `LISTED` history yields `HOLD_SEMANTIC`. |
| Hold unlisted or mismatched selections | Partial. `test_inventory_rejects_missing_duplicate_and_crossed_evidence` rejects a malformed table. `Commerce semantic envelopes preserve the request and stop schema refusals locally` checks SDK request forwarding. | The lookup holds an unlisted context, unlisted outcome, a changed receipt field type with `kind` still `accept`, and a control vector requested as an unlisted step. Independent edits to `operationId` and `body.idempotency_key` each hold. |
| Keep reads and recovery unbound | Partial. The consumer binding index and its checker cover all 13 reads. The boundary map records proposed recovery as `NOT_BOUND`. The combined lookup verdict was uncovered. | A case for every recorded read, verified by exact name set, and a fixture-only operation/trace, subject and source-cut request for recovery all yield `NOT_BOUND` with a null vector. |
| Select with zero transport calls | Uncovered. The existing journey and envelope tests exercise SDK dispatch. | The test consumer's recording transport fails on use. Every selection and the suite total report zero calls. |

The request and its expected verdict are separate literals in the [portable cases](../../sdk/conformance/vectors/producer-grant-selection.vectors.json). The existing [SDK conformance suite](../../sdk/conformance/conformance.test.mjs) runs the lookup and the existing [Python tuple suite](../../reference/booking_resale_admission/test_commerce_fixture_tuple_conformance.py) runs producer replay. The portable cases are a companion to the `commerce-fixture-8ba7f6c-1` manifest.

## Changed paths

- `sdk/conformance/vectors/producer-grant-selection.vectors.json`
- `sdk/conformance/conformance.test.mjs`
- `docs/README.md`
- `validation/2026-11-20-plan-producer-grant-selection-vectors/README.md`

## Local verification

Node `24.22.1`, Python `3.12.15` and Rust `1.98.1` supplied the pinned toolchains. The Rust commands ran from `runtime/` with `CARGO_NET_OFFLINE=true`. Each checker shown with and without `--self-test` was run both ways.

| Command | Result |
| --- | --- |
| `node --test --test-name-pattern='Commerce grant lookup' sdk/conformance/conformance.test.mjs` | Initial run failed when the strict canonical parser encountered whitespace in the existing binding index. After using its existing JSON reader, all 3 tests passed. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -p 'test_commerce_fixture_tuple_conformance.py'` | 4 tests passed. |
| `npm --prefix sdk run conformance` | 20 tests passed. |
| `npm --prefix sdk run verify-compat` | Passed. The verifier returned `ok: true` for `BOOTSTRAP` revision `bootstrap-2`. |
| `python3.12 -B scripts/check_sdk_client.py` and `--self-test` | Both passed. 84 pinned commands. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and `--self-test` | Both passed. 84 commands and 13 reads. |
| `python3.12 -B scripts/check_sdk_compat_manifest_evidence_map.py` and `--self-test` | Both passed. 51 evidence rows and 71 negative fixtures plus the positive control. |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both passed. 454 scanned, 419 indexed and 35 allowlisted. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and `--self-test` | Both passed. 13 `NOT_BOUND` reads and 10 negative controls. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 1,073 tests passed. Includes the existing admission regression on `127.0.0.1`. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 11 tests passed. |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Both passed. 84 commands. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both passed. 84 commands and public/production flags false. |
| `python3.12 -B scripts/verify_canonical.py --report "$report_dir/canonical.json"` | `PASS` for Python/TypeScript canonical agreement. The temporary report was removed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Architecture and declared dependency checks passed. |
| `python3.12 -B scripts/test_runtime_architecture.py` | 7 tests passed. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Respectively `ab1228db16a7ef37ecd9ef3aad88110685cb867349ad04cbd2b76ff8cb0539c5`, `84c8ef6cca3eb3eafc842639b32580c21b88731b34e83490db2fa84eecb1657f`, and `d404aa9bade8d9997872d0537a40813d49cbff1f6b60bf13bc385d613fc42bae`. |
| `cargo test -p kix-kernel --locked` | 139 tests passed. |
| `cargo clippy -p kix-kernel --all-targets --locked -- -D warnings` | Passed. |
| `cargo tree -p kix-kernel --edges normal --locked` | Passed. The only normal dependency is `kix-types`. |
| `cargo fmt --all -- --check` | Passed. |
| `cargo test --workspace --locked` | Passed with the CPU/SQL acceptance test ignored by default. |
| `cargo clippy --workspace --all-targets --locked -- -D warnings` | Passed. |
| `git diff --check` and `git status --short --untracked-files=all` | Diff check passed. Status listed exactly the four deliverable paths. |

## Preservation and delivery scope

| Command | Result |
| --- | --- |
| `git rev-parse origin/main HEAD` | Both refs were `4208658815d21c99513c739e1a82bb625468c8b5` before and after. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Locked blobs matched before and after. `lib.rs` is `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `quarantine_capacity.rs` is `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git rev-parse HEAD:reference/v0.3-rc1` and Python Git-blob comparison using `git ls-tree -rz HEAD reference/v0.3-rc1` | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` before and after. All 108 tracked working-tree files match their HEAD blobs after verification. |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 .aiops docs/tasks sdk/compat sdk/generated sdk/conformance/vectors/commerce-fixture-tuple.vectors.json docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json docs/status/COMMERCE_CONSUMER_BINDING_INDEX_V1.json reference/booking_resale_admission/fixtures` | Empty diff. |

The broader Booking workflow equivalent included an existing localhost HTTP regression. Subprocesses also generated Python bytecode caches, which were removed before the final preservation check. The focused lookup itself recorded zero transport calls. Local verification covered the touched SDK and documentation paths and the Rust workflow equivalents. Full hosted workflows, Move, ZK, local-chain and storage probes are outside this local result. Exact-head KTX and KIX run IDs, statuses and conclusions are pending a supervisor delivery commit.

Contract violations and undefined characterizations found in scope are both zero. The evidence covers source-informed selection and replay at the pinned fixture producer, with a grant range of the listed steps across 28 actions. The other 56 catalogue actions carry `HOLD_SEMANTIC`. External Commerce acceptance is `UNVERIFIED`. Product TTLs, fees, compensation, market visibility, matching, pagination and legal, accounting and provider terms are `UNDETERMINED`. Production behavior, durability, N/N−1 compatibility and chain finality remain unverified by this work.
