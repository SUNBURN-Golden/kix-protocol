# Fast64 external-consumer API boundary evidence

Node: `plan-feature-ir-api-boundary-tests`. Task document: supervisor-supplied node specification and design plan in this session; no issue or file under docs/tasks exists for this node. This is not ASTRA program mode. Builder evidence only, pending non-author exact-head review and delivery CI; no merge readiness or capability-grade claim.

Observed cached origin/main, initial task HEAD and comparison base: `6191e5d45e6d0be654e35a14714103ea354ec15b` on `agent/kix-plan-feature-ir-api-boundary-tests`. The supervisor prohibits network/GitHub actions, so AGENTS §1 fetch was omitted; remote freshness is unverified. No base change, commit, push, PR, issue, comment or merge was made. Implementation and final delivery commit SHAs are not assigned by this builder: the supervisor owns publication. Exact-head KTX kernel verification and KIX protocol verification run IDs/statuses/conclusions are unavailable, not passing; both must complete successfully at the supervisor's exact delivery head, together with non-author review. Merge/post-merge SHA and CI: not applicable.

## Existing coverage mapped before fixtures

| Requirement | Prior coverage | Assessment and action |
|---|---|---|
| Checked construction, identity and export bounds | runtime/crates/kix-feature-ir/src/lib.rs::fast64_profile_is_bound_to_asset_and_registry_version; runtime/crates/kix-feature-ir/tests/schema_bound.rs::fast64_rejects_wrong_asset_version_or_hash_at_export | Sufficient runtime coverage; reuse, no duplicate runtime tests. |
| Identity before range, inclusive claimed range, i64 ceiling and version/hash isolation | schema_bound.rs::fast64_identity_mismatch_precedes_amount_range_for_each_identity_field; schema_bound.rs::fast64_checked_range_is_inclusive_at_claim_and_capped_at_i64_max; schema_bound.rs::fast64_checked_claim_is_not_inherited_across_registry_versions | Sufficient runtime coverage; reuse. |
| Valid external checked construction and typed export | Existing integration tests call the public API, but no paired standalone compilation control | Partially covered; add checked_export.rs using the same compiler and dependencies as negatives. |
| Struct-literal construction, direct key/hash reads and writes rejected | No external-consumer compilation fixtures | Not covered; add private_construction.rs (E0451), read_key.rs, overwrite_key.rs, read_registry_hash.rs and overwrite_registry_hash.rs (E0616). |
| Raw u128 export rejected | Existing calls use AssetAmount; no rejection fixture | Not covered; add raw_u128_export.rs (E0308, expected AssetAmount/found u128). |
| Compiler/dependency/setup failures cannot pass | No compilation harness | Not covered; every subprocess must run, local libraries and positive control must succeed, negatives must exit 1 with exactly their intended error at their own source path. No skip/install/download/retry path. |
| Harness citation accepted; invalid citations rejected | Existing allowlist/symbol/missing-file self-tests cover prior test paths | Partially covered; append harness allowlist entry and add its accepted citation plus missing-file, fabricated-symbol, non-test-helper and nested-fixture-path negative controls. |

## New evidence and limits

`runtime/crates/kix-feature-ir/tests/api_boundaries.rs::fast64_external_consumer_api_boundaries` builds fresh rlibs from the unchanged local kix-types, kix-feature-semantics and kix-feature-ir sources (Rust 2024), then compiles each fixture as a separate consumer crate. It uses only std and the installed rustc (RUSTC override respected), explicit extern paths, a newly created process/time-specific temporary directory and cleanup restricted to that directory. It selects no cached rlib. The positive control type-checks checked construction, all three public accessors and AssetAmount export as Result<i64, FeatureIrError>. Negative checks match error code, fixture location and relevant field/type fragments, rejecting additional errors rather than accepting unrelated failure. Compiler diagnostic drift fails visibly. Fixtures are nested below tests/fixtures so Cargo discovers only the harness; fixture formatting is checked explicitly.

S6-EXPORT-BOUNDARY remains PARTIAL, owner k-stage7-authenticated-export. Registry signature/authority/content authentication remains absent. Counts remain rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17. No new contract violation or undefined behavior was found. Existing class B identity-error granularity remains unchanged; no per-field error order is chosen. Tolerance policy values remain UNDETERMINED (owner: User).

No exporter, authenticated registry/catalog, dataset/backend conformance, MoneyWide128, production readiness, durability, actual funds/provider/bank/KYC/chain execution or clean-room independence is claimed. Fixtures are source-informed API checks and compile only; existing runtime tests provide execution coverage. Full hosted CI, Move/Sui/ZK, SDK and storage-probe jobs are not run for this test/document-only node. Required delivery review and both exact-head workflows remain supervisor follow-up gates.

## Commands and results

Execution date: 2026-10-28. Installed rustc 1.98.1 (48a229cea 2026-09-01), cargo 1.98.1 (797e8a9bc 2026-08-05), matching CI. Cargo verification uses CARGO_NET_OFFLINE=true and --locked. All commands ran in the foreground; no downloads were needed and none occurred.

| Command | Result |
|---|---|
| `cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --test api_boundaries --locked` | 1 passed, 0 failed (`fast64_external_consumer_api_boundaries` ok). Inside it: all three local rlibs built, the positive control compiled, and each negative fixture exited 1 with exactly its intended diagnostic — E0451 (private_construction), E0616 (read_key, overwrite_key, read_registry_hash, overwrite_registry_hash), E0308 expected `AssetAmount`/found `u128` (raw_u128_export). |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --locked` | 49 passed, 0 failed (lib 5, api_boundaries 1, audit_regressions 8, plan_limits 7, schema_bound 21, validator_matrix 7; 0 doc-tests). |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | 318 passed, 0 failed across 45 test targets. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Clean; the api_boundaries target was rechecked after touch with no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Clean. |
| `rustfmt --edition 2024 --check runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/*.rs` | Clean (fixtures are not Cargo targets; checked explicitly). |
| `python3 scripts/check_feature_semantics_evidence_map.py` and `--self-test` | `feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17`; self-test pass with 81 negative controls plus injected positive, including the four new boundary controls (missing harness file, fabricated symbol, non-test helper, fixture path outside allowlist) and the accepted harness citation. |
| `python3 scripts/check_evidence_map_rollup.py` and `--self-test` | `evidence map roll-up ok: contracts=25; textual index only`; self-test pass (16 negative controls). |
| `python3 scripts/check_docs_index.py` and `--self-test` | `docs index ok: scanned=295 indexed=260 allowlisted=35`; self-test pass. The validation record is indexed from docs/README.md. |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | `ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99`; self-test pass. |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | `ci test discovery ok: reference_suites=6 node_tests=8 modules=4 excluded=3`; self-test pass. Cargo test execution above establishes Rust harness discovery. |
| All remaining Stdlib offline document checks in protocol.yml (30 checker scripts, plain + --self-test; check_stage5_host --self-test only) | All passed, zero failures. |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | 7 tests, OK. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 122 passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Clean. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | kix-kernel -> kix-types only; no dependency change. |

Not run locally (hosted/specialized or out of scope for this node, and unchanged by it): Move/Sui suites, ZK artifact generation, storage probes, localnet journeys, SDK conformance, `scripts/verify_runtime.py`/`verify_commerce.py`/`verify_canonical.py` venv pipelines. These remain required exact-head CI gates for the delivery head; no local result is claimed as CI equivalence for them.

## Protected-file verification and changed paths

Before edits, git hash-object reported runtime/crates/kix-kernel/src/lib.rs = `69564b166f0c27f9af5d8422f0a466b18d74c20f` and runtime/crates/kix-kernel/tests/quarantine_capacity.rs = `b607996c83a119c349f1cc90469ac1ba82764e20`. After all work, git hash-object reports the identical values for both paths. `git status --porcelain reference/ .aiops/` is empty and `git diff --stat HEAD -- reference/ .aiops/` is empty, so reference/v0.3-rc1/** and .aiops/** are byte-identical to the recorded base. The changed-path list below is the complete diff surface.

Changed paths:

- runtime/crates/kix-feature-ir/tests/api_boundaries.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/support.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/checked_export.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/private_construction.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/read_key.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/overwrite_key.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/read_registry_hash.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/overwrite_registry_hash.rs
- runtime/crates/kix-feature-ir/tests/fixtures/api_boundaries/raw_u128_export.rs
- scripts/check_feature_semantics_evidence_map.py
- docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md
- docs/README.md
- validation/2026-10-28-plan-feature-ir-api-boundary-tests/README.md

Deviations: fetch and publication/exact-head CI left to the supervisor under its explicit instructions. No implementation/contract/dependency/workflow change or scope expansion.
