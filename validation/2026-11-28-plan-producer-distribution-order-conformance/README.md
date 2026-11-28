# Commerce distribution-order conformance

The task document for `plan-producer-distribution-order-conformance` is the
supervisor's node specification and design plan. The acceptance text matches
planner run `1795823722` in `/workspace/kix-run/logs/planner_1795823722_codex0.last.md`.
There is no issue or `docs/tasks/` document for this node.

The starting and ending branch HEAD and cached `origin/main` were
`4a01955fa195214e6160b87e40908784931055ab` on
`agent/kix-plan-producer-distribution-order-conformance`. The two refs agree.
Remote freshness is unverified under the supervisor's no-network instruction.
The implementation is an uncommitted worktree patch. Implementation and final
commit SHAs and the A2 non-author review await supervisor delivery. Exact-head
KTX and KIX workflow run IDs, statuses and conclusions are unavailable at
this stage. Merge SHA and post-merge CI are inapplicable to this session.

## Coverage and outcomes

The five shared cases reconstruct the pinned `booking-resale/distribute-resale`
envelope and substitute only `body.order`. Each gate case replays all 18 setup
vectors on a fresh in-process host with readiness disabled. The replay includes
the pre-commit refusal and the final resale acceptance. The commit receipt
reports `COMMITTED` and a null distribution order. The selector uses the
independent consumer manifest digest and the original producer, schema digest,
setup and outcome for all five requests. The companion sits outside the
manifest's `vectors[]`. [Shared cases](../../sdk/conformance/vectors/commerce-distribution-order.vectors.json) · [Consumer procedure](../../docs/status/CONSUMER_SURFACE_BOUNDARY_MAP.md#scoped-commerce-fixture-qualification)

| Case | SDK calls and result | Gate dispatch / FSM calls and result | Grant selection |
| --- | --- | --- | --- |
| Original | 1, exact envelope forwarded | 1 / 1, 200, full typed receipt and one settlement journal append | `SEMANTIC_CONFORMANCE`, `booking-resale/distribute-resale` |
| String | 0, `WRONG_TYPE` | 0 / 0, `SCHEMA_REJECTED` with `body.order: expected array` | `HOLD_SEMANTIC`, null vector ID |
| Duplicate payee | 1, exact envelope forwarded | 1 / 1, 422, `DISTRIBUTION_ORDER_DUPLICATE` | `HOLD_SEMANTIC`, null vector ID |
| Missing payee | 1, exact envelope forwarded | 1 / 1, 422, `DISTRIBUTION_ORDER_MISMATCH` | `HOLD_SEMANTIC`, null vector ID |
| Unknown payee | 1, exact envelope forwarded | 1 / 1, 422, `DISTRIBUTION_ORDER_MISMATCH` | `HOLD_SEMANTIC`, null vector ID |

The 200 receipt is the full golden receipt at `#/steps/25/receipt`. Business
refusals return only the error code and `rejected: true`, with
`journalDecision: inactive`. All four refusals preserve the canonical business
state and complete exported accepted journals of reservation, resale, admission,
settlement and credit. The selector makes zero transport calls. [Golden receipts](../../reference/booking_resale_admission/fixtures/commerce_journey_receipts_v1.json) · [Settlement contract §4](../../docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md#4-f02--분할-배정과-호출자-순서)

| Requirement | Existing coverage | Added evidence |
| --- | --- | --- |
| Exact listed receipt and selection | Sufficient. `CommerceGateDispatchTests.test_listed_outcomes` and the SDK's `selects every listed outcome and holds every control-only vector`. [Gate suite](../../integration_gate/test_offline_limits.py) · [SDK suite](../../sdk/conformance/conformance.test.mjs) | Uses the same baseline in the shared matrix, checks its covered receipt and journal delta, and counts its calls. |
| String order rejected before dispatch | Partial. `Commerce journey envelope faults are rejected before transport` and `CommerceJourneyEnvelopeTests.test_shared_faults_are_rejected_by_the_parser` cover other fields. [SDK suite](../../sdk/conformance/conformance.test.mjs) · [Gate suite](../../integration_gate/test_offline_limits.py) | Checks the order-specific SDK error, gate error and detail, and zero target calls. |
| Array refusals and atomicity | Partial. `SettlementRejectionAtomicityTests.test_distribute_order_duplicate_leaves_no_trace` and `test_distribute_order_mismatch_leaves_no_trace` cover direct machine duplicate and missing orders. [Settlement regression suite](../../reference/settlement_f01_f03/test_settlement_rejection_atomicity.py) | Tests duplicate, missing and unknown payees through actual dispatch from the pinned checkpoint, checks exact payloads, and compares all five machines' state and accepted journals for every refusal. |
| Hold all four altered orders | Uncovered. Existing exact-selection tests cover other envelope differences. | Changes only the order field on the verified request and checks each altered grant decision. |

## Changed paths

- `sdk/conformance/vectors/commerce-distribution-order.vectors.json`
- `sdk/conformance/conformance.test.mjs`
- `integration_gate/test_offline_limits.py`
- `validation/2026-11-28-plan-producer-distribution-order-conformance/README.md`
- `docs/README.md`

## Local verification

The toolchain was Node `24.22.1`, npm `11.21.1`, Python `3.12.15` and
Rust `1.98.1`. Test runs used `PYTHONDONTWRITEBYTECODE=1` or Python's `-B`
flag. Cargo ran with `CARGO_NET_OFFLINE=true`.

| Command | Actual result |
| --- | --- |
| `node sdk/compat/verify_compat.mjs --manifest sdk/compat/manifests/manifest.commerce-fixture-8ba7f6c-1.json --expect-kind SEMANTIC_CONFORMANCE --expect-revision commerce-fixture-8ba7f6c-1` | Exit 0 at entry and after implementation. `ok: true`, expected kind and revision, and SHA-256 `76ea72c6249ec0f90cb426dfbb8efda8308610f79c4f0ac6ff0a2445cab59a4f`. |
| `node --test --test-name-pattern='Commerce grant lookup' sdk/conformance/conformance.test.mjs` | 15 passed. |
| `python3.12 -B -m unittest -v integration_gate.test_offline_limits.CommerceGateDispatchTests.test_distribution_order` | 1 passed with all five cases. |
| `npm --prefix sdk run conformance` | 32 passed. |
| `python3.12 -B -m unittest integration_gate.test_offline_limits` | 19 passed, including the module socket guard. |
| `python3.12 -B -m unittest readiness.test_faults` | 98 passed. |
| `npm --prefix sdk run verify-compat` | Exit 0, `ok: true` for `BOOTSTRAP` and `bootstrap-2`. |
| `python3.12 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 224 passed. |
| `python3.12 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 1,105 passed, including the suite's existing local loopback test. |
| `python3.12 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 341 passed. |
| `python3.12 -B -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | 182 passed. |
| `python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | 397 passed. |
| `python3.12 -B -m unittest discover -s reference/provider_facts -t reference/provider_facts` | 86 passed. |
| `python3.12 -B -m unittest discover -s reference/payment_effects -t reference/payment_effects` | 28 passed. |
| `python3.12 -B -m unittest discover -s reference/economics -t reference/economics` | 99 passed. |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Both passed, 40 core and 44 FSM commands. |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both passed, 84 commands. |
| `python3.12 -B scripts/check_sdk_client.py` and `--self-test` | Both passed, 84 pinned actions. |
| `python3.12 -B scripts/check_producer_qualification_tuple.py` and `--self-test` | Both passed, 84 commands and 13 reads. |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both passed, 484 scanned, 449 indexed and 35 allowlisted. |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both passed. |
| `python3.12 -B scripts/check_ci_checker_wiring.py` and `--self-test` | Both passed. |
| `python3.12 -B scripts/check_sdk_compat_manifest_evidence_map.py` and `--self-test` | Both passed. |
| `python3.12 -B scripts/check_integration_gate_contract_evidence_map.py` and `--self-test` | Both passed. |
| `python3.12 -B validation/2026-11-10-plan-commerce-consumer-binding-index/check_consumer_binding_index.py` and `--self-test` | Both passed. |
| `python3.12 -B scripts/verify_canonical.py --report <scratch>/canonical.json` | `PASS` for canonical encoding 1 and Commerce schema 2. The temporary report was removed. |
| `python3.12 -B scripts/verify_runtime_architecture.py` and `python3.12 -B scripts/test_runtime_architecture.py` | Architecture and dependency gate passed. All 7 tests passed. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Passed. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 101 at workspace dependency resolution. The offline index lacks `duckdb`. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 101 at the same dependency resolution step. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 101 at the same dependency resolution step. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 101 at the same dependency resolution step. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 101 at the same dependency resolution step. |
| `python3.12 -B scripts/check_cargo_offline_cache.py --require` and `--self-test` | Cache check exited 1 with 16 of 378 archives present. Self-test passed. |
| `cargo generate-lockfile --manifest-path <scratch>/Cargo.toml --offline` | Passed in a temporary workspace containing only `kix-kernel` and `kix-types`, with the original sources and tests symlinked. Both package entries matched the repository lockfile. |
| `cargo test --manifest-path <scratch>/Cargo.toml -p kix-kernel --locked` | 139 passed in the temporary workspace. |
| `cargo clippy --manifest-path <scratch>/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Passed in the temporary workspace. |
| `cargo tree --manifest-path <scratch>/Cargo.toml -p kix-kernel --edges normal --locked` | Passed in the temporary workspace. `kix-types` was the sole normal dependency. |
| `sha256sum runtime/Cargo.lock runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/transitions.rs` | Printed SHA-256 source digests for all three inputs. |

An auxiliary test-count probe hit a Python module-name collision when it
discovered multiple reference suites in one interpreter. Repeating the count
with one interpreter per suite succeeded. The actual CI discovery commands
above each ran in their own interpreter and passed.

## Preservation and limits

The two required Git blobs matched at entry and exit.

| Path | Verified Git blob |
| --- | --- |
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

| Command | Actual result |
| --- | --- |
| `git rev-parse HEAD refs/remotes/origin/main` and `git status --short --branch --untracked-files=all` | Refs match the entry SHA and status lists the five deliverable paths. |
| `git hash-object --no-filters` for the two locked files | Returned the required blob IDs above. |
| Python comparison using `git ls-tree -rz HEAD`, raw Git blob hashes and `git ls-files --others` | All 474 protected files matched HEAD byte-for-byte at entry and exit, with no added files. Includes all 108 historical reference files and the pinned profile, manifest, catalogue, grant and replay corpus. The historical reference tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `git diff --check` and `git diff --no-index --check /dev/null <new-file>` for both new files | No whitespace diagnostics. The two no-index comparisons returned 1 for file differences. |

## Deviations and limits

The implementation follows the supplied design. Local Rust verification used
the isolated kernel workspace because the full-workspace dependency resolution
requires a populated offline cache.

The scope is synthetic settlement and fixture lookup. No contract violations
or contract-undefined behavior were observed in these cases. Payout priority,
waterfall terms and legal or accounting treatment remain `UNDETERMINED`.
External Commerce acceptance remains `UNVERIFIED`. Durability, live funds,
provider integration, chain finality and production behavior were outside
verification. The hosted workflows, separate gate HTTP suite, toolchain
bootstrap, Move, ZK, Sui localnet and storage probes were outside the local
equivalents for the affected tests.
