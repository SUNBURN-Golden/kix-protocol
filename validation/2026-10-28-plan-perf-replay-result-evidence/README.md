# Complete first-result replay — local builder validation

Builder-authored evidence only; not non-author A2 review, acceptance, capability increase or merge readiness.

## Basis

Node: `plan-perf-replay-result-evidence`; planner run `1793150511`.
Dependencies: `plan-plan-perf-harness-map-json-csv-closure-2` and `plan-plan-perf-harness-kernel-construction-co`.
The immutable task input is the supervisor-provided node and design plan in this session; no issue or current task document under `docs/tasks/` exists for this node. This is not ASTRA program mode; `.aiops/program.json` is unchanged.

Branch: `agent/kix-plan-perf-replay-result-evidence`.
Observed cached `origin/main`, starting task HEAD and implementation base: `d0b56bda97f9470fa882591773f631d8f6920774`; local delta zero.
The supervisor prohibits network actions, so `git fetch origin main` is NOT_RUN and live-main freshness is unverified. This explicit task instruction takes precedence over AGENTS §1's fetch step.
Delivery is an uncommitted working-tree patch. The supervisor establishes the final committed task head and exact-head CI. No merge or post-merge evidence exists here.

## Existing coverage

Mapped before adding tests; paths below are under `runtime/crates/kix-kernel/tests/`.

| Requirement | Existing evidence | Classification before work |
|---|---|---|
| Retry counts and outcome separation | `performance_harness.rs::memory_probe_reports_saturation_without_recreating_kernel`, `low_load_uniform_is_distinct_from_hot_seat_retry_and_saturation` | Sufficiently covered |
| Retry inventory and JSON | `performance_harness.rs::smoke_final_remaining_matches_v4_smoke_signature`, `outcome_count_json_keys_are_top_level_per_workload` | Sufficiently covered |
| Complete original-result replay through the harness | `transitions.rs::response_loss_retry_returns_original_before_availability_check` checks the kernel directly; `support/perf_probe.rs::classify` discards the actual reply after reading the replay flag | Partially covered |
| Corrupted captured reply rejected through the harness | `contract_invariants.rs::inv3_replay_predicate_rejects_corrupted_observer_views_not_kernel_mutations` exercises a different observer | Not covered here |
| Timing arithmetic and construction count | `performance_harness.rs::csv_rows_keep_service_inside_call_window_and_latency_arithmetic`, `each_workload_and_low_load_run_constructs_exactly_one_kernel`, `injected_kernel_reconstruction_is_counted_and_reported`, `perf_probe_routes_kernel_new_through_one_helper` | Sufficiently covered for existing predicates; exact timing-window contents remain source-inspected |

## Changes and schema preservation

Complete changed-path list:

- `runtime/crates/kix-kernel/tests/support/perf_probe.rs`: `Report.applied_reservations: Vec<Option<AppliedReservation>>` is a nonserialized diagnostic with a field-scoped dead-code allowance for the shared example. Private `classify` returns `(OutcomeKind, Option<AppliedReservation>)` from one kernel invocation. Successful reserves retain the actual reply; reserve errors and capture calls retain `None`. Entries correspond to measured call indices; conflict prefill is excluded. Capacity is allocated before `origin`. Each iteration invokes/classifies once, updates its existing counter, records service duration and call end, then appends the diagnostic outside both windows.
- `runtime/crates/kix-kernel/tests/performance_harness.rs`: two regressions and shared `check_retry_original_results` comparison helper, described below. Existing separation, single-kernel and top-level JSON helpers are reused; existing counter, inventory, CSV and JSON regressions remain.
- `scripts/check_performance_measurement_evidence_map.py`: four negative fixtures (`partial without tests/gap/owner`, `empty gap`) now target unchanged PARTIAL M-OTHER. Expected diagnostics, validation rules, `MUST_STATUS` and release-status negative controls are unchanged.
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`: M-REPLAYED becomes COVERED with Gap/Owner `none`; current characterization, dated provenance and counts updated.
- `docs/status/EVIDENCE_MAP_ROLLUP.md`: matching performance counts; historical citation moves from line 83 to 85. Maintainer remains the open-row owner for other gaps.
- `docs/README.md`: link to this record, preserving earlier index entries.
- `validation/2026-10-28-plan-perf-replay-result-evidence/README.md`: this record.

Current counts in both map and roll-up: `Counts: rows=42 COVERED=30 PARTIAL=8 NOT_COVERED=1 NOT_RUN=3` (previously 29 COVERED / 9 PARTIAL).

Source comparison with the recorded starting commit verifies byte-identical JSON serializers, `EvidenceBinding`, CSV header/formatting, workload generation, schedules, budgets and timing-definition constants. The CSV remains:

```text
index,scheduled_ns,start_ns,end_ns,service_ns,scheduled_latency_ns,outcome
```

Appending diagnostics is outside service/call windows but contributes to workload-loop `elapsed_ns`. Returning the classified reply also changes the apparatus code in the timed invocation. No numerical timing equivalence, speedup, unchanged latency, memory-footprint or benchmark claim follows from preserving timing definitions and serialized schemas. M-SERVICE-NS stays PARTIAL: the existing inequality test checks nesting, while exact window contents remain source-inspected.

## Acceptance evidence

| Regression | Gap addressed / observed result |
|---|---|
| `retry_replays_complete_first_result` | Runs the existing Retry workload with 512 calls, command limit 128, rate 0. Requires 512 captured entries; first reply is present, `replayed=false`, `original=Held(_)`; every subsequent reply is present, `replayed=true`, and its complete original equals the first, including the KixId. Verifies Held=1, replay=511, remaining=4095, zero rejected/Capacity/conflict/other, outcome separation, one kernel and top-level new-success/replay/inventory JSON values. Passes. |
| `retry_comparison_rejects_corrupted_captured_original` | Validates actual captured replies, clones only the diagnostic vector, replaces one replay's Held payload with a verified different KixId while keeping `replayed=true`, and requires exactly `Err("replay original differs from first result")`. Revalidates unchanged actual replies. No kernel mutation or second reserve call is used to fabricate evidence. Passes. |

The shared helper rejects an empty sequence, missing first/replay replies, a replayed or non-Held first reply, a subsequent reply without its replay flag, and original-result mismatch. Only the recorded positive and corrupted-payload controls are claimed as tested helper branches.

## Commands and actual results

Inspected `.github/workflows/ktx-kernel.yml` and the stdlib/Rust sections of `.github/workflows/protocol.yml`. These are closest local equivalents for touched paths, not full hosted protocol CI. All verification commands ran sequentially in the foreground. Cargo uses `CARGO_NET_OFFLINE=true` and `--locked --offline` where applicable; Python uses `PYTHONDONTWRITEBYTECODE=1`. Rustfmt modified only the two authorized test files; workspace formatting was check-only. No dependencies were installed or downloaded.

| Command | Actual result |
|---|---|
| `git status --short`; `git branch --show-current`; `git rev-parse HEAD`; `git rev-parse origin/main` | Initially clean; branch and identical cached base/HEAD recorded above. |
| `git fetch origin main` | NOT_RUN: supervisor no-network instruction. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before work: both match required blobs; after/delivery checks also match below. |
| Python SHA-256 starting snapshot over `git ls-files -z` | 1082 starting tracked files snapshotted before edits. |
| `python3 scripts/check_cargo_offline_cache.py --require` | Exit 0; 18/18 archives present, missing list empty. Cache presence alone is not integrity verification. |
| `rustc --version`; `cargo --version` | rustc 1.98.1 (48a229cea 2026-09-01); cargo 1.98.1 (797e8a9bc 2026-08-05), matching CI's version. |
| `rustfmt --edition 2024 runtime/crates/kix-kernel/tests/performance_harness.rs runtime/crates/kix-kernel/tests/support/perf_probe.rs` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked --offline` | Exit 0; 22 passed, 0 failed, 0 ignored. Narrow tests ran first. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 124 passed, 0 failed, 0 ignored across 9 result groups. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 324 passed, 0 failed, 0 ignored across 46 result groups. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; includes kernel tests and shared example compilation. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; no output. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; kix-kernel → kix-types only. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; OK. |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; rows=42 COVERED=30 PARTIAL=8 NOT_COVERED=1 NOT_RUN=3. |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; 2 positive controls, 66 negative fixtures, including retargeted PARTIAL and all release-status controls; memory only. |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; contracts=25; textual index only. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; 16 negative controls. |
| `python3 scripts/check_docs_index.py`; same command with `--self-test` | Both exit 0; scanned=299 indexed=264 allowlisted=35; self-test pass. Rechecked after completing this record. |
| `python3 scripts/check_ci_checker_wiring.py`; same command with `--self-test` | Both exit 0; scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99; 13 negative controls. |
| `python3 scripts/check_ci_test_discovery.py`; same command with `--self-test` | Both exit 0; reference_suites=6 node_tests=8 modules=4 excluded=3; 18 negative controls. |
| `python3 .local/plan-perf-replay-result-evidence/verify_preservation.py` | Exit 0; source/snapshot checks described below. Rechecked at delivery. |
| `git diff --check` | Exit 0; rechecked at delivery. |
| `git diff --quiet HEAD -- runtime/crates/kix-kernel/src runtime/crates/kix-kernel/tests/quarantine_capacity.rs runtime/crates/kix-kernel/examples .github docs/contracts docs/tasks .aiops reference/v0.3-rc1` | Exit 0; excluded tracked paths unchanged. |

Kernel/workspace logs and local checker output are under ignored `.local/plan-perf-replay-result-evidence/`; existing debug smoke artifacts remain under ignored `.local/verification/ktx/`. These are apparatus outputs, not a release measurement or transaction journal.

## Locked/preserved paths

| Locked path | Before / after / delivery Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The local preservation script compares SHA-256 against the pre-edit snapshot: 1076 of 1082 starting tracked files are byte-identical, with only the six allowed existing paths changed. This record is the sole new deliverable. In particular `reference/v0.3-rc1/**`, kernel source, the quarantine test, release example, all contracts and frozen pins, historical validation records, CI, task documents and `.aiops/` are unchanged.

Additional source checks verify the actual diagnostic capacity allocation precedes `origin`, and append follows both duration/end recording; unchanged workload input construction and post-classification CSV/summary code; unchanged serializer tail and timing constants. M-OTHER and all four release-related map rows are byte-identical. Map §3 historical text is unchanged. Checker validation code before `self_test`, including `MUST_STATUS`, is byte-identical.

The release locks remain X-RELEASE-REPRO NOT_RUN, X-OUTPUT-FILES NOT_RUN, BD-RUN-VALUES NOT_RUN and BD-FAIL-CLOSED NOT_COVERED. Their negative controls still pass.

## Contract classifications

Class A: the existing memory-only Retry fixture returns the first Held original on all 511 replays, produces one new success and consumes one seat, matching the measured replay contract. No class-C explicit contract violation was found; no locked-source reproduction or fix is needed.

Class B / source-informed apparatus observations: diagnostics allocate outside the loop timing origin and append after service/call end; they still contribute to elapsed loop time and change resource use. Exact window contents remain source-inspected rather than independently established by arithmetic tests. This task invents no protocol semantics or policy values. Other existing map uncertainties remain open.

## Non-claims and remaining uncertainty

Product TPS, p99 and failure-rate targets remain UNDETERMINED (owner: User). Release probe NOT_RUN; the known example-specific LOCKED_EDGE mismatch and frozen-pin repair remain a separate owner decision. No release example invocation or measurement campaign ran.

No timing, speedup, product performance, production readiness, durability, provider/bank exactly-once, chain finality, independent proof, A2 review, capability increase or merge-readiness claim is made. The finite fixture and corrupted observer copy do not establish completeness or kernel mutation sensitivity. No real funds, provider/KYC calls, endpoints, Sui, storage engine, coin/TIX, secrets or production runtime were involved. Unrelated SDK/Move/ZK/storage/network hosted workflow steps were not run.

Exact-head KTX CI run ID/status/conclusion: NOT_RUN / unavailable. Exact-head KIX protocol CI run ID/status/conclusion: NOT_RUN / unavailable. Post-merge main CI and merge SHA: not applicable; no merge. No implementation commit or final committed task head was created; HEAD at delivery remains `d0b56bda97f9470fa882591773f631d8f6920774`, which does not identify the uncommitted patch. The supervisor owns commit/publication and subsequent exact-head CI/non-author A2 review. No old CI result is transferred.

Deviations: only the explicit no-network override of AGENTS §1's fetch requirement. No implementation deviation from the supplied design was needed. The remaining PARTIAL/NOT_COVERED/NOT_RUN rows and release-pin decision are follow-up candidates requiring separate scope. READY means local builder delivery only.
