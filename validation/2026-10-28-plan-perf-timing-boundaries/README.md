# plan-perf-timing-boundaries — local builder evidence

Task input: supervisor-provided node and design plan in this session; no issue or current task document. Historical `docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md` is context only. Scope is DEVELOPMENT_PLAN §7 apparatus regression coverage.

Branch: `agent/kix-plan-perf-timing-boundaries`. Cached `origin/main`, starting HEAD and base: `7e0568593229689a31dc9af020839d09fe305c83`; local delta zero. Fetch is prohibited by the supervisor, so live-main freshness is unverified. No commit or publication is authorized.

## Coverage mapping recorded before implementation

Paths below are under `runtime/crates/kix-kernel/tests/`.

| Requirement | Existing coverage | Gap to address |
|---|---|---|
| Service includes kernel invocation and classification only | Partial: `performance_harness.rs::csv_rows_keep_service_inside_call_window_and_latency_arithmetic` checks nesting inequalities. | Exact independently specified virtual phase durations through the shared loop. |
| Elapsed includes loop bookkeeping and scheduled waits | Partial: `performance_harness.rs::elapsed_ns_covers_every_row_and_scheduled_wait` checks lower bounds and JSON equality. | Exact elapsed values, waits and late-driver behavior. |
| Preparation and report formatting exclusion | Not covered deterministically; source-read only. | Independently vary excluded phases and require identical CSV/JSON timing values. |
| Timing-boundary sensitivity | Not covered. | Include preparation in a test-only faulty origin and require the common expectation checker to reject it. |
| Fixed schedule arithmetic | Sufficient: `scheduled_csv_uses_fixed_origin_i_over_rate`, `csv_rows_keep_service_inside_call_window_and_latency_arithmetic`. | Retain; add deterministic on-time/late controls. |
| Summary arithmetic, outcome separation and schemas | Sufficient: `nearest_rank_p99_matches_fixed_expectations`, `summary_p99_matches_raw_csv_by_outcome`, `goodput_matches_fixed_integer_expectations`, `other_outcomes_count_real_reserve_error_and_applied_capture`, `other_outcomes_json_matches_measured_calls`, plus shared `assert_separated`. | Reuse helpers and assert exact serialized timing values for the new fixtures. |
| Single kernel and workload signatures | Sufficient: `each_workload_and_low_load_run_constructs_exactly_one_kernel`, `smoke_final_remaining_matches_v4_smoke_signature`, replay and injected-other-outcome regressions. | Retain and reuse single-kernel/outcome guards. |

Before edits, locked blobs match: kernel `69564b166f0c27f9af5d8422f0a466b18d74c20f`, quarantine `b607996c83a119c349f1cc90469ac1ba82764e20`. Reference tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. A SHA-256 snapshot of all tracked files is retained under the ignored local verification directory for the final preservation audit.

## Implementation and fixture expectations

The existing `run_probe` algorithm now accepts `ProbeClock`: marks, elapsed reads, waits and phase completion hooks. `InstantClock` retains Instant reads, real sleeps only for positive scheduled delays, and the existing u64::MAX nanosecond clamp. Its phase hooks do nothing. Both real reserve/capture invocation branches retain their classifier logic, and index-based kernel Context::now_ms remains independent of the injected clock. Kernel calls complete before the invocation hook; classification and counters complete before its hook and service/end capture. Reply retention and sample bookkeeping complete before the per-iteration bookkeeping hook. Input construction, vector allocation and diagnostic preparation precede the preparation hook and workload origin. Summary/CSV formatting completes after elapsed capture and before the formatting hook. No second measurement loop was introduced.

The harness-local VirtualClock has independently supplied integer phase costs, read-only clock access, and recorded phases/waits. Its waits only advance integers, never sleep. The test entry point and TimingFault selector are gated by cfg(test) and absent from ordinary example builds. The ordinary `run` signature, workload requests, budgets, kernel logical times, outcome classification and CSV/JSON schema remain unchanged. No timing-equivalence claim follows from the refactor or no-op hooks.

Each fixture uses three Uniform calls and command_limit 128: three Held, remaining inventory 4093, one kernel construction and zero resets. Preparation is 1000 ns and post-loop formatting 2000 ns unless varied independently below. Bookkeeping is 13 ns per iteration. These are synthetic fixture values, not host measurements or performance targets.

| Fixture / test | Invocation / classification costs | Scheduled | Starts | Ends | Service | Scheduled latency | Elapsed | Wait requests | Full virtual total |
|---|---|---|---|---|---|---|---|---|---|
| `timing_boundaries_rate_zero` | 7 / 11 | 0,0,0 | 0,31,62 | 18,49,80 | 18,18,18 | 18,18,18 | 93 | none | 3093 |
| `timing_boundaries_scheduled` (rate 10000000) | 7 / 11 | 0,100,200 | 0,100,200 | 18,118,218 | 18,18,18 | 18,18,18 | 231 | 69,69 | 3231 |
| `timing_boundaries_late_driver` (same rate) | 70 / 50 | 0,100,200 | 0,133,266 | 120,253,386 | 120,120,120 | 120,153,186 | 399 | none | 3399 |

The shared `assert_timing_report` checks literal full CSV strings including the unchanged header, exact report elapsed/mixed percentiles, top-level JSON elapsed/mixed percentiles and scoped outcome JSON counts/percentiles. Expected mixed and Held p99 pairs are (18,18), (18,18), (120,186); all six empty outcomes have count 0 and both percentiles null. Existing csv_rows, top_level, json_outcome_objects, assert_separated and assert_single_kernel are reused. The clock guard requires exactly preparation, three invocation/classification/bookkeeping triples, formatting, and the stated wait list. The final 13 ns bookkeeping interval is included in elapsed but excluded from service/end.

`timing_boundaries_exclude_setup_and_formatting` runs all three fixtures with (preparation,formatting) costs (0,2000), (9000,2000), (1000,0), (1000,8000), varying one phase at a time against the baseline. Every CSV and full JSON remains identical, and full virtual time equals preparation + expected elapsed + formatting. Repeated calls to the existing immutable JSON serializer preserve measured fields and clock state.

`timing_boundaries_reject_included_preparation` first accepts the ordinary rate-zero virtual result with the common checker. A cfg(test)-only IncludePreparation fault then takes origin before setup and runs the same measurement algorithm: elapsed is 1093 in report and JSON rather than 93, full virtual time remains 3093 and Held/remaining are unchanged. The same expectation checker must panic on that boundary error, caught as the required negative control. No kernel mutation is used.

The map checker adds only in-memory missing-symbol self-tests for the five new regressions and clock entry point, separately targeting each timing row. Validation logic, source/citation rules and all four status locks remain unchanged. Only the Tests, Source and Gap cells of M-SERVICE-NS and M-ELAPSED change; both stay PARTIAL and roll-up counts remain rows=42 COVERED=34 PARTIAL=4 NOT_COVERED=1 NOT_RUN=3. Historical characterization-index quotations are retained verbatim and explicitly labeled historical, followed by dated current findings. X-RELEASE-REPRO, X-OUTPUT-FILES, BD-RUN-VALUES remain NOT_RUN; BD-FAIL-CLOSED remains NOT_COVERED. The docs index links this record.

## Complete changed-path list

- `runtime/crates/kix-kernel/tests/support/perf_probe.rs`
- `runtime/crates/kix-kernel/tests/performance_harness.rs`
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`
- `scripts/check_performance_measurement_evidence_map.py`
- `docs/README.md`
- `validation/2026-10-28-plan-perf-timing-boundaries/README.md`

## Classification, limitations and gates

Class A: the tested apparatus boundary predicates match the contract for these synthetic fixtures. No explicit class-C contract violation was found, and no kernel reproduction or owner decision is required. Class B: phase placement is source-informed apparatus instrumentation; virtual time is not a proof of host-clock accuracy, sleep precision, exhaustive I/O absence or file-output exclusion. Real I/O by callers and actual metadata collection/release outputs remain untested. Both timing rows remain PARTIAL. The known release-example LOCKED_EDGE mismatch remains outside scope and is not repaired or exercised; frozen pins and example bytes remain unchanged.

Product TPS/p99/failure-rate values remain UNDETERMINED (owner: User). No benchmark, throughput, production-performance, durability, distributed fencing, provider/bank exactly-once, chain-finality, legal, production-readiness, backend-selection/comparison, independent clean-room proof or owner-decision claim is made. No release example, dedicated hardware campaign, paid service, provider call, public endpoint, chain execution or storage engine was invoked.

Implementation/final task commit SHA: not created; output is the uncommitted patch over starting HEAD `7e0568593229689a31dc9af020839d09fe305c83`. Supervisor owns commits/publication and must establish the final head. Merge commit and post-merge checks are not applicable.

| External gate | Actual state |
|---|---|
| Non-author exact-HEAD A2 review | Pending supervisor; no review claimed. |
| KTX kernel verification at final head | NOT_RUN here; no run ID/status/conclusion available. |
| KIX protocol verification at final head | NOT_RUN here; no run ID/status/conclusion available. |
| Post-merge main/push CI | Not applicable; no merge. |

Deviation from AGENTS §1: fetch omitted because the supervisor explicitly prohibits network actions; cached main is not evidence of fresh main. No implementation deviation from the supplied design. The node input substitutes for a current task document; historical Task 004 is context only. No commits, pushes, branch/tag operations, PRs, issues, comments, GitHub/network actions, background jobs or delegated agents were used.

Local builder readiness is separate from merge readiness. Non-author exact-head review, both exact-head hosted workflows and user merge authorization remain outstanding external gates. Follow-up candidates are the unchanged PARTIAL/NOT_COVERED gaps and unrun release procedures; no follow-up task was started.

## Commands actually run and results

Commands ran from the repository root using existing cached dependencies. Broad verification used CARGO_NET_OFFLINE=true and PYTHONDONTWRITEBYTECODE=1; all Cargo dependency resolution used explicit --offline. The initial narrow result is recorded in session tool output. The foreground batch invocation was `python3 .local/verification/plan-perf-timing-boundaries/run_checks.py`; every subprocess command and exit code is in ignored `checks.json` with its `check-NN.log`. No detached/background jobs were used. Toolchain versions appear in the table below. Counts sum actual successful result groups, including zero-test groups; they are not counts of independent proofs.

| Command | Actual result |
|---|---|
| `git status --short; git rev-parse origin/main HEAD; git branch --show-current` | Exit 0; initially clean, both SHAs equal base above; expected branch. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0; both required blobs match before and after work. |
| `git ls-tree HEAD reference/v0.3-rc1` | Exit 0; tree a6ecb124dc2b2267ca6be19e39fbe2aef143074b; file bytes separately audited. |
| `rustfmt --edition 2024 --config skip_children=true runtime/crates/kix-kernel/tests/support/perf_probe.rs runtime/crates/kix-kernel/tests/performance_harness.rs` | Exit 0; only the two authorized Rust files formatted. |
| `python3 scripts/check_cargo_offline_cache.py --require` | Exit 0; 18/18 archives present, missing list empty. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness timing_boundaries --locked --offline` | Exit 0; 5 passed, 0 failed, 0 ignored; 27 filtered out. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked --offline` | Exit 0; test groups=1 passed=32 failed=0 ignored=0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; test groups=9 passed=139 failed=0 ignored=0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; test groups=46 passed=339 failed=0 ignored=0 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; All workspace targets pass; no warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; Formatting check passes. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests pass. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; └── kix-types v0.0.0 (/workspace/kix-run/wt/plan-perf-timing-boundaries/runtime/crates/kix-types) |
| `rustc --version` | Exit 0; rustc 1.98.1 (48a229cea 2026-09-01) |
| `cargo --version` | Exit 0; cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=34 PARTIAL=4 NOT_COVERED=1 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 81 negative fixtures; memory only) |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test: pass (16 negative controls) |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=305 indexed=270 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_class_b_index.py` | Exit 0; class B index ok: rows=217 sources=72 symbols=45; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0; self-test: pass (20 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; self-test: pass (18 negative controls) |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0; 18/18 cached archives present; missing list empty. |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | Exit 0; Legacy/tomllib, cache, environment and error-path controls pass. |
| `python3 .local/verification/plan-perf-timing-boundaries/audit_preservation.py` | Exit 0; 1,092 protected tracked files byte-identical; exactly six changed paths; serialized code and old harness bytes preserved; only two map rows changed; checker validation unchanged. |
| `git diff --check` | Exit 0; no whitespace errors. |

No test or verification command failed. The initial performance map check and its self-test also passed before the complete verification batch; the batch independently captured their logs. The new negative control's caught assertion is intentional and its test passes. Closest applicable local portions of `.github/workflows/ktx-kernel.yml` and `protocol.yml` were run: kernel/workspace tests, all-targets Clippy, format, architecture/dependency checks and affected offline document checkers with self-tests. This is not full hosted protocol CI. The release example was compiled by applicable test/lint targets but never executed.

## Final preservation audit

Before/after locked blobs match AGENTS §4: kernel `69564b166f0c27f9af5d8422f0a466b18d74c20f`, quarantine `b607996c83a119c349f1cc90469ac1ba82764e20`. Final byte comparison against the before-edit SHA-256 snapshot covers all 1,092 tracked files outside the edit allowlist: none changed. This includes every tracked file under `reference/v0.3-rc1/**`, `.aiops/**` and `docs/tasks/**`, all contracts/historical records/frozen inputs, Cargo manifests/lockfile, CI workflows and release example/pins. The audit also verifies exact six-path scope, unchanged Report structure and all serializer code, unchanged preexisting harness bytes, unchanged untargeted map rows/statuses/owners/historical-reference section and unchanged checker validation/main logic. No dependency or CI adaptation was required.

Final HEAD remains the starting SHA; no final implementation commit, exact-head hosted CI or merge evidence is manufactured. Final document rechecks and preservation audit are recorded in `final-checks.json` under the ignored verification directory. Local builder handoff: READY, subject to the separate review/publication/CI gates above.
