# Feature Semantics v1 clause-to-test evidence map — local validation

Node/task ID: `plan-plan-feature-semantics-v1-evidence-map`.
Task input: supervisor-provided node specification and read-only design plan in the session; no issue and no task document under `docs/tasks/` exists for this node. Dependency: `plan-plan-ci-checker-wiring-guard`. Builder-authored evidence only; not A2/non-author review or acceptance.

Observed local `origin/main`, starting branch HEAD and end-of-session HEAD: `412e1ed7bc740599227567f60bf315bb7ecab818`.
Branch: `agent/kix-plan-plan-feature-semantics-v1-evidence-map`. No local base delta.
Remote freshness was not checked: `git fetch origin main` was omitted because the supervisor explicitly prohibited all network actions.
Implementation commit SHA and exact final task head: **not created** (uncommitted delivery).
Merge commit: not applicable. No commit, push, PR, issue or comment action was performed.
Exact-head KTX CI and KIX protocol CI run IDs/status/conclusions: **not available / not run**. Post-merge main CI: not applicable. These local results are not exact-head hosted CI or merge authorization; the supervisor owns Git/GitHub delivery and final-head evidence.

## Changed paths (complete)

- `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md` — 41 clause/gate/execution rows, named gaps and owners, current test citations, characterizations and non-claims.
- `scripts/check_feature_semantics_evidence_map.py` — stdlib-only offline checker and in-memory negative fixtures.
- `.github/workflows/protocol.yml` — exactly two added invocation lines in the existing unguarded stdlib step, after the performance-map pair and before the wiring guard; no other workflow change.
- `docs/README.md` — index bullet linking the map and this record.
- `validation/2026-10-26-plan-feature-semantics-v1-evidence-map/README.md` — this record.

No runtime, contract, capability-register grade, reference, task-document or .aiops file changes. The register itself is unchanged. No CI change was made to bypass a failure.

## Locked blobs and protected bytes

| Path | Required Git blob | Before (working file) | After (HEAD and working file) |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

The final audit read NUL-delimited `git ls-tree -rz HEAD -- runtime reference/v0.3-rc1 .aiops docs/tasks docs/status/CURRENT_CAPABILITY_REGISTER.md`, calculated Git blob SHA-1 from each working file's bytes, and compared every result with HEAD: **189 tracked files byte-identical**, including every tracked `reference/v0.3-rc1/**` file. It also combined `git diff --name-only HEAD` and `git ls-files --others --exclude-standard` and asserted exactly the five delivery paths above. `git diff --numstat HEAD -- .github` is exactly `2 / 0 / .github/workflows/protocol.yml`. Final-merge blob verification is not applicable (no merge).

## Existing coverage mapping and new evidence

The [map](../../docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md) starts from the [2026-10-17 table](../2026-10-17-feature-semantics-v1-edge-fixtures/README.md), with assertions and full symbols re-read in the current tree. It covers every §1–§10 heading and all six numbered §9 gates.

Counts: **41 rows; COVERED=1, PARTIAL=23, NOT_COVERED=17**. The COVERED row is explicitly bounded to scalar I64 division predicates. Group, sort, aggregate and join execution and dataset/backend conformance remain NOT_COVERED, owner `k-stage7-cpu-analytics-sql-audit`. Authentication gaps retain `k-stage7-authenticated-export`; open policy/convention gaps retain User. No test count is used as a completion criterion.

No new runtime tests were added. The checker closes a document-maintenance gap: heading/row/gate completeness, fixed contract anchors, valid statuses and counts, owner vocabulary, required owners/statuses, citation grammar and #[test] function existence (including in-source tests), non-claims, class-B citations, and both locked blobs. It never runs Cargo. Self-tests use an injected positive test and **77 negative controls**, each required to produce its own diagnostic: missing/duplicate/invented rows and headings, section coverage, numbered gate drift, bad symbols (including ordinary and nested helpers), paths, missing/non-UTF8 files, status/gap/owner invariants, count mismatch, execution pins, characterization pins/citations, non-claims, contract anchor drift and each locked-blob mismatch. Locked/Rust inputs are never mutated on disk.

## Commands actually run and results

All commands below ran locally. Cargo commands used `CARGO_NET_OFFLINE=true` to obey the no-network instruction; no long jobs were launched with shell backgrounding. Narrow map checks ran before Rust crate tests, followed by the full stdlib step and broader Rust checks. Final map checks and compilation ran again after the checker formatting and final map prose changes. No product/test failure required a runtime fix.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git rev-parse --abbrev-ref HEAD` | Initially clean; both refs equal the SHA above; task branch as above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blob hashes match before work. |
| `git rev-parse HEAD:runtime/FEATURE_SEMANTICS_V1.md` | `4428d2bbd00a1e43bf0b61dd402c6ad0fc67bb39`. |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; 41 rows, 1 COVERED / 23 PARTIAL / 17 NOT_COVERED; initial, stdlib-step and final runs passed. |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; 77 negative controls detected and injected positive accepted; initial, stdlib-step and final runs passed. |
| `python3 -m py_compile scripts/check_feature_semantics_evidence_map.py` | Exit 0; initial and final compilation passed. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-feature-semantics -p kix-feature-ir --locked` | Exit 0; 55 tests passed (IR inline 5, audit 8, plan limits 7, schema-bound 18, semantics inline 6, scalar edges 11); 0 failures. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 257 tests passed, 0 failed/ignored across 42 reported test/doc-test result groups. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0; warnings denied, no failure. |
| Inline Python audit using non-NUL `git ls-tree -r HEAD` | Exit 1 in audit harness: quoted Unicode reference path caused FileNotFoundError. No protected file was written. Corrected to NUL-delimited enumeration below. |
| `python3 /tmp/feature-map-final-audit.py` | Exit 0; both locks match HEAD/working bytes; all 189 protected tracked blobs identical; exactly five changed paths; workflow delta exactly +2/-0; local refs unchanged. Audit algorithm documented above. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git diff -- .github/workflows/protocol.yml`; `git diff --numstat` | Only two requested workflow lines and docs index additions among tracked changes; new files enumerated separately by final audit. |

The closest local equivalent for the touched Python/document/CI paths is the complete **Stdlib offline document checks** run block in `protocol.yml`. A foreground Python runner extracted its standalone commands in order and ran each with subprocess argument arrays, capturing the real exit code/output: **51 invocations, all exit 0**, listed below. Stage-5 remains self-test-only exactly as in CI. Commands/results are not inferred from checker existence or older CI.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=263 indexed=228 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0; ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0; self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0; lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0; self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0; BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=17 PARTIAL=20 NOT_COVERED=2 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; feature semantics evidence map ok: Counts: rows=41 COVERED=1 PARTIAL=23 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; self-test: pass (77 negative controls, injected positive control) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=29 plain=28 self_test=29 self_test_only=1 docs=20 citations=26 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

## Classifications, uncertainty and non-claims

Class C explicit contract violations found: **none** in this mapping; no new runtime reproduction or contract/source change.
Class B retained: depth calculation (root = 0), negative zero, lossy i64→f64 precision and the null-component-only scope of nullable_keys_equal. No semantics were chosen. AggregatePolicyMismatch has no existing driving test; it remains a coverage gap.

No Polars, DuckDB, GPU, dataset/backend conformance, authenticated export/catalog, wire parser, MoneyWide128, release-mode measurement, Sui network or real funds/provider/bank/KYC execution was verified. No tolerance/zero-normalization/precision/depth policy value, new protocol command, production readiness, grade change, independent clean-room result, A2 review or upgrade acceptance is claimed. Full hosted protocol/localnet/ZK/bootstrap jobs were not run: they do not exercise the changed checker/documents, and network/bootstrap/public-service actions were prohibited. Existing Rust crates/workspace, architecture, formatting and Clippy were verified locally as additional checks.

Follow-ups are precisely the named PARTIAL/NOT_COVERED gaps in the map. This node supplies traceability and maintenance checks; it does not close runtime or product-policy gaps.

## Deviations

- Session-start fetch omitted under the explicit supervisor no-network override; only the existing local origin/main ref is observed. No branch/base/history operation performed.
- The design plan says five plan-limit tests; the current tree has seven, all cited. It also describes four divide edge tests; the tree has three divide-prefixed edge tests plus the inline division test, with the negative-zero characterization cited separately.
- Added separate rows for the §6 export API boundary and §10 structural-only/catalog-trust boundaries so grouped clauses retain explicit gaps/owners. This changes no semantics.
- The initial byte-audit harness needed NUL-delimited Unicode filenames; corrected and passed. No delivery checker/test failures occurred.
- No commits or hosted exact-head CI were produced, as required by the supervisor. READY means locally validated builder delivery for supervisor review, not merge-ready.
