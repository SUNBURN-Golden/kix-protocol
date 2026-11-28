# Commerce optional nullable body fields

Task `plan-producer-nullable-field-conformance` uses the supervisor's node specification and design plan from planner run `1795815309`. The supplied specification is the task document. This node has no issue or `docs/tasks/` file. The planner acceptance was also checked against `/workspace/kix-run/logs/planner_1795815309_codex0.last.md`.

Starting and ending branch `HEAD` and cached `origin/main` resolve to `394a6cb0f64935bec3da183353bfffcff06a3d01` on `agent/kix-plan-producer-nullable-field-conformance`. The supervisor's offline instruction precluded fetching, so remote freshness is unverified. The local refs show no base delta. The implementation is an uncommitted worktree patch. Implementation and final commit SHAs, A2 non-author review, and the exact-head KTX and KIX run IDs, statuses and conclusions await supervisor delivery. Merge and post-merge checks were outside this builder session.

## Pinned inventory

The manifest verifier returned `SEMANTIC_CONFORMANCE` for `commerce-fixture-8ba7f6c-1` with the independent consumer SHA-256 `76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`. Both tests check the independent pin before using the qualification table and resolve the pins for the profile, table and request corpus. They compare the canonical action schema digest with the table and profile for every listed action, then derive the fields whose types are `string` and `null` and whose keys are absent from `required`. Each test compares the complete cross-product of derived positions and representations with the shared cases. The baseline per action is the lexicographically first vector ID from `tuples[].contexts[].steps`. [Consumer procedure](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification) · [Shared cases](../../sdk/conformance/vectors/commerce-nullable-fields.vectors.json)

| Action | Baseline vector ID | Field and original value |
| --- | --- | --- |
| `admission_adopt_issued` | `booking-admission/adopt-B` | `quote_ref` = `"quote-B"`, `reservation_id` = `"reserve-B"` |
| `admission_authorize_admission` | `booking-admission/authorize-B` | `external_dependency` omitted |
| `admission_consume` | `booking-admission/consume-B` | `external_dependency` omitted |
| `resale_adopt_issued` | `booking-resale/adopt-A` | `quote_ref` = `"quote-A"`, `reservation_id` = `"reserve-A"` |
| `resale_list_resale` | `booking-resale/list-A` | `reservation_id` = `"reserve-A"` |
| `resale_observe_resale_payment` | `booking-resale/resale-payment-A` | `buyer_role` = `"buyer-B"` |
| `reservation_confirm` | `booking-admission/order-B` | `quote_ref` = `"quote-B"` |
| `settlement_commit` | `booking-resale/settle-resale-commit` | `adjustment_reason` omitted |

## Coverage and observed results

| Requirement | Existing coverage | Added evidence |
| --- | --- | --- |
| Preserve valid envelope shapes | Partial. `Commerce semantic envelopes preserve the request and stop schema refusals locally` checks the pinned SDK requests. `CommerceJourneyEnvelopeTests.test_every_journey_envelope_is_preserved` checks the gate's validated tuple for original journey requests. | Both tests reconstruct every envelope from the pinned original and compare all fields. For each of 30 valid cases, the SDK recorder and the gate's `perform` mock each receive one call. Typed JSON equality and key membership distinguish omission from explicit null. |
| Refuse a boolean before dispatch | Partial. `Commerce journey envelope faults are rejected before transport` and `CommerceJourneyEnvelopeTests.test_shared_faults_are_rejected_by_the_parser` cover faults in other fields. | All ten booleans yield SDK `WRONG_TYPE` and gate `SCHEMA_REJECTED` with `body.<field>: expected string or null`. Both recorders have zero calls for each rejection. |
| Select only the exact listed evidence | Sufficient for originals. `selects every listed outcome and holds every control-only vector` covers baseline selection. The nullable matrix was uncovered. | Eight original requests select their exact vector IDs. Each matrix request keeps the original producer, route, tuple, context, step, setup order and outcome. Only the envelope varies. The selector uses the independent pin and makes zero transport calls. |

| Representation | SDK and gate schema result per position | SDK grant selector across the ten cases |
| --- | --- | --- |
| Omitted | Accept and forward without the key | 3 `SEMANTIC_CONFORMANCE` with the listed ID, 7 `HOLD_SEMANTIC` with `vector_id: null` |
| Explicit `null` | Accept and forward the present null | 10 `HOLD_SEMANTIC` with `vector_id: null` |
| `"fixture-alternate"` | Accept and forward the string | 10 `HOLD_SEMANTIC` with `vector_id: null` |
| Boolean `true` | Reject before calling the recorder | 10 `HOLD_SEMANTIC` with `vector_id: null` |

The three selecting matrix cases are the omissions already present in the listed envelopes. The companion contains 40 test inputs and is outside the manifest's `vectors[]`.

## Changed paths

- `sdk/conformance/vectors/commerce-nullable-fields.vectors.json`
- `sdk/conformance/conformance.test.mjs`
- `integration_gate/test_offline_limits.py`
- `validation/2026-11-28-plan-producer-nullable-field-conformance/README.md`
- `docs/README.md` for the required validation index link

## Local verification

Verification ran in the foreground with Node `24.22.1`, npm `11.21.1`, Python `3.12.15` and pinned Rust `1.98.1`. Test runs set `PYTHONDONTWRITEBYTECODE=1`. Cargo used `CARGO_NET_OFFLINE=true`.

| Command | Actual result |
| --- | --- |
| `node --test --test-name-pattern='Commerce grant lookup' sdk/conformance/conformance.test.mjs` | 14 passed, including `nullable body fields`. |
| `node --test --test-name-pattern='Commerce grant lookup' --test-skip-pattern='requires the consumer\|selects only\|holds when\|selects every\|holds the readiness\|selects grants\|holds every\|preserves the unbound\|checks table-pinned' sdk/conformance/conformance.test.mjs` | The nullable-field subtest and its parent passed in isolation. An earlier fully anchored name filter selected only the file and produced no subtest evidence. |
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits.CommerceGateDispatchTests.test_nullable_body_fields` | 1 passed, covering all 40 subtests. |
| `npm --prefix sdk run conformance` | 31 passed. |
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits` | 18 passed, including the active socket guard. |
| `npm --prefix sdk run verify-compat` | `ok: true` for `BOOTSTRAP` revision `bootstrap-2`. |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | `ok: true` before implementation and again in the full local checks. The verdict digest matched the consumer's independent pin. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and `--self-test` | Both passed. 84 catalogue commands and 13 reads. |
| `python3.12 -B scripts/check_sdk_client.py` and `--self-test` | Both passed. 84 pinned actions. |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Both passed. 40 core and 44 FSM commands. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both passed. 84 commands and public and production flags false. |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both passed. 481 scanned, 446 indexed, 35 allowlisted. |
| `python3.12 -B scripts/check_sdk_compat_manifest_evidence_map.py` and `--self-test` | Both passed. |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py` and `--self-test` | Both passed. |
| `python3.12 -B scripts/check_ci_checker_wiring.py` and `--self-test` | Both passed. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_commerce_fixture_tuple_conformance.py -v` | 10 passed. |
| `python3.12 -B scripts/verify_canonical.py --report <scratch>/canonical.json` | `PASS` for CE1 and Commerce schema 2. The temporary report was removed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture and dependency gate passed. 7 tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 101 before compilation. The offline index lacks `duckdb`, which the workspace resolves for `kix-analytics-audit`. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101 at the same dependency resolution step. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 101 at the same dependency resolution step. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 101 at the same dependency resolution step. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 101 at the same dependency resolution step. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` and `--self-test` | Cache inspection exited 1. It found 16 of 378 archives and confirmed `duckdb` was missing. Self-test passed. |
| `cargo generate-lockfile --manifest-path <scratch>/Cargo.toml --offline` | Passed for the temporary `kix-kernel` and `kix-types` workspace. Both resulting package entries matched `runtime/Cargo.lock`. The workspace symlinked the original crate sources and tests and was removed after verification. |
| `cargo test --manifest-path <scratch>/Cargo.toml -p kix-kernel --locked` | 139 passed in the temporary workspace. |
| `cargo clippy --manifest-path <scratch>/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Passed in the temporary workspace. |
| `cargo tree --manifest-path <scratch>/Cargo.toml -p kix-kernel --edges normal --locked` | Passed in the temporary workspace. `kix-types` is the sole normal dependency. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Source digest evidence generated for all three inputs. |

## Preservation and limits

| Command | Actual result |
| --- | --- |
| `git rev-parse HEAD refs/remotes/origin/main` and `git status --short --branch --untracked-files=all` | Both refs resolve to the starting SHA. Status lists exactly the five deliverable paths. |
| `git diff --check` and `git diff --no-index --check /dev/null <new-file>` | No whitespace diagnostics. |
| `git diff --exit-code HEAD -- .aiops docs/tasks .github/workflows runtime reference/v0.3-rc1 sdk/compat sdk/src sdk/generated sdk/conformance/vectors/commerce-fixture-tuple.vectors.json docs/status/COMMERCE_FIXTURE_TUPLE_CONFORMANCE_V1.json` | Empty diff. |
| Python byte check using `git ls-tree -rz HEAD`, `git hash-object --no-filters` and `git ls-files --others` | Before and after work the 108 tracked files under `reference/v0.3-rc1/` matched their HEAD blobs and had no added files. Its Git tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `git hash-object --no-filters` for both locked files | `runtime/crates/kix-kernel/src/lib.rs` matched `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` matched `b607996c83a119c349f1cc90469ac1ba82764e20` before and after work. |

`docs/README.md` gained one link to satisfy the validation index checker. The full Rust workspace tests and Clippy await an offline cache with the locked dependencies. The closest local kernel equivalent ran in the temporary workspace. Hosted workflows, HTTP listeners, Move, ZK, chain execution and storage probes are outside this local evidence.

The matrix exercises schema handling and exact fixture lookup. Variant business outcomes, durability, chain finality and production behavior are untested. No contract violations or contract-undefined behavior were observed within the exercised boundaries. External Commerce acceptance is `UNVERIFIED`, product policy is `UNDETERMINED`, and the 13 reads and proposed recovery lookup are `NOT_BOUND`.
