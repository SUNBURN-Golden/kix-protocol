# Performance measurement clause evidence map — local builder record

Builder-authored map and checker, not A2 review, acceptance, capability increase or merge readiness.

Task/node: `plan-plan-performance-measurement-clause-evid`, planner run `1792977654`.
Task document: immutable supervisor-provided node and design plan in the session. No issue or current task file under `docs/tasks/` exists for this node; `docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md` was read as historical context, not current authorization. This is not an ASTRA program-mode session.

Observed local `origin/main`, starting branch HEAD, implementation-base HEAD and final local HEAD: `1f01a9321c641c7a7fafa2a33e4350a2fa711730`.
Branch: `agent/kix-plan-plan-performance-measurement-clause-evid`.
No commit was made; implementation is the five-file working-tree patch below. The supervisor will establish the committed final task head. The local base/HEAD delta is zero. Live-main freshness/delta is unverified: the supervisor explicitly prohibited network actions, so `git fetch origin main` was not run. No rebase or base change occurred.

Contract: `docs/contracts/PERFORMANCE_MEASUREMENT.md`, Git blob `8b88ba7176a98faf64565434d05e44d97dc3cf8f`.
Actual toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)`; `cargo 1.98.1 (797e8a9bc 2026-08-05)`.
All Cargo verification used `CARGO_NET_OFFLINE=true`; cached locked dependencies were sufficient. Commands ran sequentially in foreground subprocesses, without shell background jobs. Python batch checks used `PYTHONDONTWRITEBYTECODE=1`.

Complete changed-path list:

- `.github/workflows/protocol.yml`: exactly two checker invocations immediately after BCS1 self-test and before stage-5 host self-test; no other workflow line changed.
- `docs/README.md`: one index bullet linking the map and this record.
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`: new 42-clause map, historical attribution, characterizations and non-claims.
- `scripts/check_performance_measurement_evidence_map.py`: new standalone stdlib checker and memory-only self-tests, adapted from the BCS1 checker helpers.
- `validation/2026-10-26-plan-performance-measurement-clause-evid/README.md`: this record.

Existing coverage was inspected before adding checker tests. The [map](../../docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md) classifies 17 sufficiently covered fixture predicates (COVERED), 20 partially covered, 2 not covered and 3 release procedures NOT_RUN. Every COVERED/PARTIAL row cites existing tests; source citations identify existing functions/constants/types in the probe support/example, with the historical baseline file allowed only on the historical-counts row.

| Existing test path | Existing functions and relevant assertions |
|---|---|
| `runtime/crates/kix-kernel/tests/performance_harness.rs` | memory_probe_reports_saturation_without_recreating_kernel: four 512-call workloads and 16 scheduled calls, outcome counts, Capacity positions, CSV headers/row preservation via assert_separated, JSON meanings/non-claims. |
| Same path | low_load_uniform_is_distinct_from_hot_seat_retry_and_saturation: 32/min-budget low-load controls, under-budget hot-seat/retry/history-growth, counts and phase flags. |
| Same path | outcome_summaries_do_not_label_mixed_p99_as_success: separated counts/service p99 presence, mixed-key names/non-success labels, all-Held equality and same-helper goodput serialization. |
| Same path | evidence_binding_records_budgets_toolchain_and_non_claims: synthetic binding, four blob strings, some metadata/budgets/rate, product_slo null, non-claims. |

No Rust test, harness, contract or benchmark was added. The new checker evidence fills document-integrity gaps only: IDs are complete and unique, section anchors remain present, every allowed citation resolves, statuses/gaps/owners obey grammar, the three NOT_RUN rows and fail-closed NOT_COVERED row stay pinned, historical attribution/counts/non-claims persist, and both locked blobs plus example lock constants match. The checker does not prove cited assertions' semantics. Two positive controls (actual map and injected valid test) and 66 negative fixtures pass; fabricated citations fail both alone and mixed with valid tests, and helper functions cannot masquerade as tests. An additional in-memory fabricated-test check independently confirmed the specific diagnostic. All mutations are in memory; no locked file was transiently edited.

Actual local evidence follows; all exit codes were zero. Narrow checker/self-tests ran before performance_harness; crate tests, Clippy, formatting, workspace tests and the full stdlib step followed. Additional workspace Clippy and architecture/dependency checks reflect the inspected workflow commands. All 47 stdlib commands were extracted from the edited protocol.yml run block and executed in order via `python3 /tmp/verify_perf_node.py stdlib`; `/tmp` runners/results are local utilities, not delivery files. There were no test/check failures or corrective retries.

| Command | Actual result |
|---|---|
| `git status --short` (before) | Empty: initially clean. |
| `git rev-parse HEAD` and `git rev-parse origin/main` (before); `git rev-parse origin/main HEAD` (after) | Both refs are 1f01a9321c641c7a7fafa2a33e4350a2fa711730 throughout. |
| `git branch --show-current` | agent/kix-plan-plan-performance-measurement-clause-evid. |
| `git hash-object docs/contracts/PERFORMANCE_MEASUREMENT.md` | 8b88ba7176a98faf64565434d05e44d97dc3cf8f. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | 69564b166f0c27f9af5d8422f0a466b18d74c20f; b607996c83a119c349f1cc90469ac1ba82764e20; both match. |
| `python3 -m py_compile scripts/check_performance_measurement_evidence_map.py` | Pass; no output. |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Counts: rows=42 COVERED=17 PARTIAL=20 NOT_COVERED=2 NOT_RUN=3. |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Pass: 2 positive controls, 66 negative fixtures; memory only. |
| `python3 -` (import checker, _with_cell M-NEW-SUCCESS Tests to fabricated_test, assert find_problems diagnostic) | Fabricated citation rejected in memory: performance_harness.rs::fabricated_test is not a test function. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked` | 4 passed; 0 failed; 0 ignored. |
| `rustc --version` | Exit 0; rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo --version` | Exit 0; cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 78 passed; 0 failed across 9 result groups (including zero-test groups). |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0; Finished dev profile [unoptimized + debuginfo] target(s) in 0.60s |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; (no output) |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 257 passed; 0 failed across 42 result groups (including zero-test groups). |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0; Finished dev profile [unoptimized + debuginfo] target(s) in 1.82s |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed; OK. |
| `rg -n check_performance_measurement .github/workflows/protocol.yml` | Plain invocation line 255; self-test line 256, within stdlib run block. |
| `git diff --quiet origin/main -- runtime reference/v0.3-rc1 .aiops docs/tasks docs/contracts` | Exit 0; protected trees unchanged. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git status --short`, `git diff --name-only origin/main`, `git ls-files --others --exclude-standard` | Exactly the five delivery paths above. |

Full protocol stdlib document-check block (all 47 commands, in workflow order):

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=258 indexed=223 allowlisted=35 |
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
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Both locked blobs matched before and after all verification. `runtime/**`, `reference/v0.3-rc1/**`, `.aiops/**`, `docs/tasks/**` and `docs/contracts/**` remain byte-identical to the observed base. No kernel, harness or example mutation, even transient, was performed. Formatting was check-only.

Discrepancy classification: no explicit class-C contract violation found by source/assertion inspection; no reproduction required. Source-informed class-B apparatus characterizations/uncertainties are recorded in map §4: kernel_resets_during_workload is a literal 0, not an instrumented counter; the example freezes four blobs while AGENTS §4 locks two; nearest-rank percentile arithmetic has no fixed-vector test. These do not establish independent coverage or change semantics. The example's mismatch-before-write behavior is source-read only and remains NOT_COVERED.

Deviations: supervisor restrictions superseded fetch/publication/hosted-CI steps; no live-main comparison was possible. The session node text is the task input rather than a nonexistent current docs/tasks file. On inspecting the assertions, two proposed COVERED rows were conservatively marked PARTIAL: M-NEW-SUCCESS lacks a new_held JSON-key/value assertion, and M-OUTCOMES lacks scheduled p99/JSON-null/independent percentile assertions. Other PARTIAL gaps were made precise (including both null/non-null first_capacity_index JSON, and additional unasserted binding metadata). Workspace Clippy and architecture checks were added to match relevant Rust CI. There were no consequential scope changes, product decisions or STOP conditions; DECISION_REQUIRED.md was not needed.

Exact-head KTX CI run ID/status/conclusion: unavailable, not requested or queried. Exact-head KIX protocol CI run ID/status/conclusion: unavailable, not requested or queried. No committed delivery head, PR, merge SHA or post-merge main CI exists for this local builder delivery. Final committed-head CI and non-author A2 review remain supervisor responsibilities; no older SHA's success is transferred. No network/GitHub action, commit, push, issue, comment, branch/tag mutation or merge was performed.

Explicit non-claims: no product TPS, p99 or failure-rate value; UNDETERMINED (owner: User). No benchmark claim. Release probe NOT_RUN: `cargo run ... --example r1_perf_probe --release` was not invoked. V4-SMOKE-001 logical counts are historical, not current measurement, and no historical latency is re-used. Debug test outputs under ignored .local/ are apparatus artifacts only. No real funds/provider/KYC calls, public endpoint, Sui execution, new coin/TIX module, secret, storage engine, policy value, protocol command or production runtime was needed or introduced. No durability, finality, bank exactly-once, readiness, legal compliance, backend superiority/selection, full-system measurement, independent-conformance proof or capability increase is inferred. Unrelated bootstrap, network, SDK, Move/localnet, ZK and storage workflow steps were not run; these local checks do not claim full hosted protocol CI.

Remaining uncertainties/follow-up candidates: the map's 20 PARTIAL gaps, elapsed-loop timing boundaries and release-example fail-closed tests (2 NOT_COVERED), and 3 NOT_RUN release procedures. Dedicated repeated release measurements, approved product targets and equivalent-condition backend comparison are absent from this evidence. Harness refactoring/injectable refusal tests or any measurement campaign need separate task scope. Live-main freshness and future committed-head CI/review remain unverified. Candidate owners in the map do not assign or authorize follow-up work.

Local builder delivery: READY; merge-ready is not claimed.
