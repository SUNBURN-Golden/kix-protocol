# Feature IR empty stages — local validation

Node/task ID: `plan-feature-ir-empty-stage-tests`. Date: 2026-10-28.
Task input: the supervisor-supplied node specification and read-only design plan in the builder session; no issue or matching `docs/tasks/` document exists. This is not ASTRA program mode. Dependencies named by the input: `plan-plan-feature-semantics-v1-evidence-map` and `plan-plan-feature-ir-validator-matrix-closure`; their existing records and current tests were inspected locally. No external acceptance was verified.

Observed local `origin/main`, base and starting branch HEAD: `d3506262bf6227ab71ea72427e4d1ee996a0c5ef`. Branch: `agent/kix-plan-feature-ir-empty-stage-tests`. No local base delta. Fetch was omitted under the supervisor's explicit no-network instruction; remote freshness is unverified. The task input is supplied outside `docs/tasks/`; no task document or `.aiops/program.json` was created or edited.

Final local HEAD remains `d3506262bf6227ab71ea72427e4d1ee996a0c5ef`. Implementation commit and exact final committed task head: unavailable (uncommitted delivery; supervisor owns Git/GitHub). Exact-head KTX and KIX protocol CI run ID/status/conclusion: unavailable / not run. Merge SHA and post-merge CI: not applicable; no merge. Local READY means ready for supervisor review, not merge-ready. A2 non-author exact-head review and hosted CI remain separate requirements; no historical CI applies to this patch.

## Complete changed paths

- `runtime/crates/kix-feature-ir/tests/empty_stages.rs` — three public-API characterization tests and four nonempty controls.
- `docs/README.md` — one relative validation-record index link.
- `validation/2026-10-28-plan-feature-ir-empty-stage-tests/README.md` — this record.

## Existing coverage mapping (before this patch)

Test paths below are relative to `runtime/crates/kix-feature-ir/`.

| Requirement | Classification and exact existing evidence | Remaining gap before this patch |
|---|---|---|
| Empty plan | Sufficiently covered for reuse: `src/lib.rs::tests::empty_plan_is_rejected` asserts `validate()` returns `EmptyPlan`. | Existing test does not exercise the schema-bound API; no duplication or two-API empty-plan claim. |
| Empty Project returns `EmptyProjection` | Not covered: no existing test asserts this rejection; source guard at `src/validation.rs` is not test coverage. | Exact error on both APIs and unchanged inputs. |
| Empty GroupBy returns `EmptyGroupKeysAndAggregates` | Not covered: existing GroupBy fixtures contain keys or aggregates. | Exact error on both APIs and unchanged inputs. |
| Empty Sort returns `InvalidStage` | Not covered: existing Sort fixtures contain keys. | Exact error on both APIs and unchanged inputs. |
| Nonempty projection and sort controls | Partially covered: `tests/schema_bound.rs::projection_drops_source_columns_and_does_not_allow_sibling_alias_reuse` accepts projection followed by sort; `group_output_contains_only_keys_and_aggregate_results` also accepts sorts. | Isolated single-stage controls through both APIs with full snapshots. |
| Keys-only and aggregate-only GroupBy controls | Partially covered: `tests/schema_bound.rs::only_count_star_can_omit_input` accepts COUNT-only through the schema API; `tests/validator_matrix.rs::aggregate_contract_empty_policy_control_validates` accepts aggregate-only through both APIs; `tests/schema_bound.rs::group_output_contains_only_keys_and_aggregate_results` covers combined keys/aggregate scope. | Keys-only control and both controls paired with the empty-stage fixture and unchanged-input checks. |

## New fixtures

Every plan has exactly one stage and the same valid source/catalog identity at schema version 1, with `ColumnId(1): I64`. Synthetic fixed KixId bytes are used. Each negative fixture has only the named empty-stage defect. Controls add only the required stage contents; explicit policy choices are existing valid fixture values, not product defaults.

| Test in `tests/empty_stages.rs` | Sole negative defect → exact existing error | Nonempty positive controls |
|---|---|---|
| `characterize_empty_projection_rejection` | `Project([])` → `EmptyProjection` | One projection: input column 1 to output 9, I64. |
| `characterize_empty_group_by_rejection` | Both keys and aggregates empty → `EmptyGroupKeysAndAggregates` | Keys-only column 1; aggregate-only COUNT(*), output 9 U64, IGNORE/Zero/Error. All use null keys Include. |
| `characterize_empty_sort_rejection` | Empty `Sort::by` → `InvalidStage` | Sort by column 1. Both use descending false, null order Last, stability Stable. |

The local `assert_both_unchanged` helper snapshots the complete plan and catalog before validation, compares `validate()` and `validate_with_schemas(catalog).map(|_| ())` with the exact expected result, and compares the full inputs after each call. It is applied to all three negatives and all four controls. Only public APIs and types are used; no helper refactor or manifest change.

## Contract classification and uncertainty

Class A: the chosen source/catalog, column types and COUNT(*) control match FEATURE_SEMANTICS_V1 §10 within validator scope; explicit policies match §§2–4. No new normative claim about stage cardinality is made.

Class B: empty Project rejection as `EmptyProjection`, GroupBy with neither keys nor aggregates rejection as `EmptyGroupKeysAndAggregates`, and empty Sort rejection as `InvalidStage` are source-informed characterizations of `src/validation.rs`. FEATURE_SEMANTICS_V1 does not define these empty-stage restrictions or exact error variants. Their normative status remains UNDETERMINED (owner: User). The keys-only and aggregate-only acceptance controls isolate the existing GroupBy boundary; no semantics are invented. The contract's COUNT(empty) rule concerns aggregate input data, not an empty list of aggregate specifications.

Class C: no explicit contract violation found. No validator behavior, contract, protocol command, policy value, backend, dependency, evidence-map status or capability grade changed. No multi-error fixture or precedence assertion.

## Commands actually run

The inspected local equivalents are `.github/workflows/ktx-kernel.yml` (architecture, kernel tests, Clippy, formatting and normal dependencies) and `protocol.yml` (Rust workspace and the complete Stdlib offline document checks block). The new target ran first, then the crate tests and broader checks. Installed versions: rustc/cargo 1.98.1 and Python 3.13.5. All Cargo verification used `CARGO_NET_OFFLINE=true`; the runner set `PYTHONDONTWRITEBYTECODE=1`. No dependencies were downloaded, CI files edited or long jobs backgrounded.

`python3 .local/verification/empty-stages/checks.py` ran in the foreground and exited 0: **72 commands passed**, including **all 63 document invocations in workflow order**. Stage-5 ran only `--self-test`. Logs and machine-readable `results.json` are retained locally under ignored `.local/verification/empty-stages/`; they are not delivery files. Initial target/format/ref inspection output is in the builder tool transcript. All verification commands passed on their first run; no test or semantic fix was needed. Two inspection-only workflow-path lookups (`ktx.yml` and `kernel.yml`) reported missing files; the actual `ktx-kernel.yml` was subsequently read. Those lookup misses were not verification failures.

| Command | Actual result | Log/output location |
|---|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; both refs d3506262bf6227ab71ea72427e4d1ee996a0c5ef; expected branch. | Builder transcript |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before and after implementation; both required blobs match. | Builder transcript |
| Read-only `cat`, `sed`, `rg`, file listings and Git diff/ref inspection | Governance, contracts, prior evidence, public APIs, existing coverage and both actual CI definitions read; two incorrect workflow names reported absent as described above. | Builder transcript |
| Starting protected-file SHA-256 snapshot (inline Python) | Exit 0; 121 protected files, including 108 reference files. | `/tmp/kix-empty-stage-verification/protected-before.json` |
| `rustfmt --edition 2024 runtime/crates/kix-feature-ir/tests/empty_stages.rs` | Exit 0; only new test formatted. | Builder transcript |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --test empty_stages --locked` | Exit 0; 3 passed, 0 failed/ignored. | Builder transcript; also included in 01.log and 02.log below |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --locked` | Exit 0; 53 passed, 0 failed, 0 ignored across 8 result groups. | `01.log` |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 322 passed, 0 failed, 0 ignored across 46 result groups. | `02.log` |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0; Clippy passed with warnings denied. | `03.log` |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; workspace formatting check passed. | `04.log` |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. | `05.log` |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 architecture tests passed. | `06.log` |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 122 passed, 0 failed, 0 ignored across 9 result groups. | `07.log` |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0; Clippy passed with warnings denied. | `08.log` |
| `CARGO_NET_OFFLINE=true cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0; kix-types is the only normal dependency. | `09.log` |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=452 ev_ids=15 original32=32. | `10.log` |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass. | `11.log` |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47. | `12.log` |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass. | `13.log` |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145. | `14.log` |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass. | `15.log` |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=297 indexed=262 allowlisted=35. | `16.log` |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass. | `17.log` |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14. | `18.log` |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass. | `19.log` |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6. | `20.log` |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass. | `21.log` |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2. | `22.log` |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass. | `23.log` |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2. | `24.log` |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass. | `25.log` |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7. | `26.log` |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass. | `27.log` |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0. | `28.log` |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass. | `29.log` |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. | `30.log` |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass. | `31.log` |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0. | `32.log` |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass. | `33.log` |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9. | `34.log` |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass. | `35.log` |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8. | `36.log` |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; self-test: pass (33 negative controls). | `37.log` |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2. | `38.log` |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls). | `39.log` |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3. | `40.log` |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; self-test: pass (55 negative controls). | `41.log` |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5. | `42.log` |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; self-test: pass (76 negative controls). | `43.log` |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0; ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1. | `44.log` |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0; self-test: pass (86 negative controls). | `45.log` |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0; lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK. | `46.log` |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0; self-test: positive injected citation and 49 negative fixtures passed (memory only). | `47.log` |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK. | `48.log` |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only). | `49.log` |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK. | `50.log` |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only). | `51.log` |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0; BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17. | `52.log` |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 50 negative fixtures). | `53.log` |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3. | `54.log` |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only). | `55.log` |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17. | `56.log` |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; self-test: pass (81 negative controls, injected positive control). | `57.log` |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0; integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1. | `58.log` |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0; self-test: pass (85 negative controls; injected positive and valid status controls). | `59.log` |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only. | `60.log` |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test: pass (16 negative controls). | `61.log` |
| `python3 scripts/check_class_b_index.py` | Exit 0; class B index ok: rows=216 sources=71 symbols=39; textual index only. | `62.log` |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0; self-test: pass (20 negative controls). | `63.log` |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99. | `64.log` |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls). | `65.log` |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; ci test discovery ok: reference_suites=6 node_tests=8 modules=4 excluded=3. | `66.log` |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; self-test: pass (18 negative controls). | `67.log` |
| `python3 scripts/check_loopback_host.py` | Exit 0; all_ok=true; loopback port-0 probes succeeded; host_selected=false, gate_suite_run=false. | `68.log` |
| `python3 scripts/check_loopback_host.py --self-test` | Exit 0; self-test: pass. | `69.log` |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0; 18/18 registry archives present; missing=[] (presence only, not integrity authentication). | `70.log` |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | Exit 0; self-test: pass. | `71.log` |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass. | `72.log` |
| `PYTHONDONTWRITEBYTECODE=1 python3 .local/verification/empty-stages/audit.py` | Exit 0; 121 protected files and their path set unchanged; 1,078 tracked files outside allowlist byte-identical to HEAD; exactly three delivery paths; locked hashes and refs match. | Builder transcript |
| `git diff --check` | Exit 0; no whitespace errors. | Builder transcript and integrity audit |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` (after completing this record) | Exit 0; scanned=297 indexed=262 allowlisted=35. | Builder transcript |

The numbered log names above are relative to `.local/verification/empty-stages/`. Crate/workspace totals are actual Cargo test/doc-test result totals, not semantic completeness criteria. Full hosted CI was not run.

## Protected-file verification

Before editing, the working-file Git blobs matched both required values:

| Path | Required and observed before/after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The before/after SHA-256 comparison covers 121 protected files, including all 108 files under `reference/v0.3-rc1/**`, both locks, `.aiops/` and `docs/tasks/`: every byte and the full path set match, with no additions/deletions. The integrity audit also recalculates Git blobs for all 1,078 tracked files outside the delivery allowlist and compares them to starting HEAD; all match. Exactly the three delivery paths listed above are changed/new (ignored local verification scratch excluded). No formatter or mutation command targeted these files; only the new test was formatted, with workspace formatting check-only.

## Deviations and non-claims

The explicit no-network instruction overrides AGENTS §1 fetch for this session. The supplied session task specification replaces a matching task document, which does not exist. No other design deviation. The local fixture helpers are specialized to the single required dataset/schema instead of carrying unused generic parameters; their behavior follows the supplied design.

This is builder-authored evidence, not A2/non-author review or acceptance. No backend execution, dataset conformance, catalog authentication, authenticated export, wire/parser behavior, release-mode result, clean-room independence, production readiness, durability, distributed fencing, bank exactly-once, chain finality or legal compliance is claimed. Hosted bootstrap/Move/SDK/ZK and unrelated service jobs are outside these scoped local CI equivalents. No funds, real provider/bank/KYC call, public endpoint, Sui network, hardware, paid service, secret, storage engine, new coin/TIX module, product policy value, new protocol command or production runtime is needed or used. User owns any future normative empty-stage decision; supervisor owns commit/publication, final-head CI and non-author review follow-up. Existing execution/authentication gaps and owners remain unchanged.
