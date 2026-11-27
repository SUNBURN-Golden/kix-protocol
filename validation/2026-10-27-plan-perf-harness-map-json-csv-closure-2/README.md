# Perf harness map JSON/CSV closure 2 — local builder validation

Builder-authored evidence only; not non-author A2 review, acceptance, capability increase or merge readiness.

## Basis

Node: `plan-plan-perf-harness-map-json-csv-closure-2`; planner run `1793059450`; depends on `plan-plan-perf-harness-map-partial-closure` and `plan-plan-evidence-map-rollup-check`.
The immutable task input is the supervisor-provided node and design plan in this session. There is no issue or current task document under `docs/tasks/` for this node. This is not ASTRA program mode.

Observed cached `origin/main` and starting task HEAD: `eb1caf8285c174697d78834246a304ffe9006427`.
Branch: `agent/kix-plan-plan-perf-harness-map-json-csv-closure-2`.
Local base/HEAD delta: zero. Live-main freshness and delta are unverified: the supervisor prohibited network actions, so `git fetch origin main` was not run. No base change occurred. Implementation is an uncommitted working-tree patch; the supervisor will establish the committed final task head.

Locked blob verification before and after tests:

| Path | Before | After |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Complete changed-path list:

- `runtime/crates/kix-kernel/tests/performance_harness.rs`: six new tests and one private CSV row parser helper; existing tests and helpers unchanged.
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`: ten row citations/statuses/gaps, Counts line, one dated §0 basis paragraph and §4 characterization notes; four pinned rows, §3 and §5 unchanged.
- `docs/status/EVIDENCE_MAP_ROLLUP.md`: PERFORMANCE_MEASUREMENT Counts cell copied verbatim; the PERFORMANCE_BASELINE_V4 row's line citation `PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:79` updated to `:81`, because the new §0 paragraph shifted the historical reference line by two.
- `docs/README.md`: one record pointer under the 2026-10-27 index.
- `validation/2026-10-27-plan-perf-harness-map-json-csv-closure-2/README.md`: this record.

No probe, example, kernel, contract, checker, CI, task document, `.aiops/` or `reference/v0.3-rc1/` changes.

## Existing coverage and new tests

Before this node, the outcome rows asserted Rust report counts and, for HotSeat, one `business_rejected` JSON value, but not the top-level JSON keys `new_held`, `replayed` or `conflict_retained`. No test parsed CSV timing columns, the `scheduled_ns` formula, workload-report parameter fields or elapsed_ns. The synthetic binding test omitted tree, probe_blob, toolchain, host_uname, os/arch, inventory_seats and output_files.

Every new test is in the allowed harness file and calls the existing probe, which calls public kernel APIs. Expected counts come from the contract JSON keys and the V4-SMOKE-001 logical signature; budgets come from the contract (`[4096]` seats, orders 4096, observations 128). Source inspection informed which values are observable. These are not clean-room independent tests. No assertion compares a duration with a constant.

| Row | New test function | Gap addressed | Before → after |
|---|---|---|---|
| M-NEW-SUCCESS | `outcome_count_json_keys_are_top_level_per_workload` | Top-level `new_held` and `new_success_count` equal 128/1/1/0/1/32/0 across four smoke workloads, the scheduled control and two under-budget controls; Retry has 1 despite 511 replays; equal to outcome summary and CSV outcome tally. | PARTIAL → COVERED |
| M-REPLAYED | `outcome_count_json_keys_are_top_level_per_workload` | Top-level `replayed` 511 for Retry, 0 elsewhere. Returning the stored first result is not observable through the probe. | PARTIAL → PARTIAL (narrower) |
| M-BUSINESS-REJECTED | `outcome_count_json_keys_are_top_level_per_workload` | Top-level `business_rejected` 127 (HotSeat 512) and 15 (scheduled HotSeat), 0 elsewhere. | PARTIAL → COVERED |
| M-CONFLICT-RETAINED | `outcome_count_json_keys_are_top_level_per_workload` | Top-level `conflict_retained` 127 and 8 for Conflict, 0 elsewhere, with top-level `other` 0. | PARTIAL → COVERED |
| M-SERVICE-NS | `csv_rows_keep_service_inside_call_window_and_latency_arithmetic` | Every row: start_ns ≤ end_ns, service_ns ≤ end_ns − start_ns, start_ns ≥ previous end_ns. Exact window content remains source-read. | PARTIAL → PARTIAL (narrower) |
| M-SCHEDULED-LATENCY | `csv_rows_keep_service_inside_call_window_and_latency_arithmetic` | rate=0: scheduled_ns 0, latency end_ns − start_ns; rate>0: scheduled_ns ≤ start_ns, latency end_ns − scheduled_ns; six runs. | PARTIAL → COVERED |
| M-ELAPSED | `elapsed_ns_covers_every_row_and_scheduled_wait` | elapsed_ns ≥ final end_ns and final scheduled_ns; JSON equals report. Setup/file-output exclusion remains source-read. | NOT_COVERED → PARTIAL |
| I-PARAMS-IN-JSON | `workload_report_json_names_budgets_samples_and_rate` | Workload-report JSON command_limit, commands_budget, orders_limit, observations_limit, inventory_seats, samples and rate for four workloads, three command limits (all ≥ 2) and two rates. | PARTIAL → COVERED |
| R-RATE-FIXED-ORIGIN | `scheduled_csv_uses_fixed_origin_i_over_rate` | CSV scheduled_ns = i*1000000000/rate for rates 10000, 250000 and 1000000 (each divides 1e9); JSON rate and rate_meaning. | PARTIAL → COVERED |
| BD-FIELDS | `evidence_binding_serializes_tree_probe_toolchain_host_and_files` | Each listed binding field appears exactly once with its synthetic value, including the four-blob object, tree, probe/harness/example blobs, toolchain, host_uname, os/arch, inventory_seats and output_files; tree and host_uname render null when absent. Real collection is not exercised. | PARTIAL → PARTIAL (narrower) |

Total before: `Counts: rows=42 COVERED=22 PARTIAL=15 NOT_COVERED=2 NOT_RUN=3`.
Total after: `Counts: rows=42 COVERED=28 PARTIAL=10 NOT_COVERED=1 NOT_RUN=3`.
The four checker-pinned rows are byte-identical to origin/main: X-RELEASE-REPRO, X-OUTPUT-FILES and BD-RUN-VALUES stay NOT_RUN; BD-FAIL-CLOSED stays NOT_COVERED.

## Commands and actual results

Inspected `.github/workflows/ktx-kernel.yml` and the stdlib/Rust blocks of `.github/workflows/protocol.yml`. The commands below are the closest local equivalents for these touched paths, plus the node's acceptance checks. Unrelated network, SDK, Move/localnet, ZK and storage workflow steps were not run; this is not a full hosted protocol-CI result.

All Cargo checks used `CARGO_NET_OFFLINE=true` and locked cached dependencies; Python checks used `PYTHONDONTWRITEBYTECODE=1`. Commands ran sequentially in the foreground. Local logs under `/tmp/kix-json-csv-2/` are not delivery files. Rustfmt targeted only the allowed harness file; workspace formatting was check-only. No test or Rust check failed. The only failure was the expected `check_docs_index.py --self-test` exit 1 for the index link written before this record existed; it passed after this file was written.

| Command | Actual result |
|---|---|
| `git status --short` (before) | Empty; clean worktree. |
| `git rev-parse origin/main HEAD` | Both eb1caf8285c174697d78834246a304ffe9006427. |
| `git branch --show-current` | agent/kix-plan-plan-perf-harness-map-json-csv-closure-2. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before/after) | Both match the locked values in the table above. |
| `rustfmt --edition 2024 runtime/crates/kix-kernel/tests/performance_harness.rs` | Exit 0; no output. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked` | Exit 0; 17 passed, 0 failed, 0 ignored. |
| Same narrow test, `-q`, ten sequential repetitions | All ten: 17 passed; 0 failed. |
| `rustc --version` / `cargo --version` | rustc 1.98.1 (48a229cea 2026-09-01) / cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 93 passed; 0 failed across 9 result groups. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 282 passed; 0 failed across 43 result groups. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0; Finished `dev` profile. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0; Finished `dev` profile. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; no output. |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=28 PARTIAL=10 NOT_COVERED=1 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test: pass (16 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=31 plain=30 self_test=31 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; OK. |
| `python3 scripts/check_docs_index.py --self-test` (before this record existed) | Exit 1; broken index link: validation/2026-10-27-plan-perf-harness-map-json-csv-closure-2/README.md (expected; record not yet written). |

The final docs-index, all-checker sweep, diff guards and pinned-row comparison ran after this file was written; their results are in the builder's final report, not committed here, so that recording them does not create a new head (AGENTS §11).

## Findings, deviations and non-claims

Class A: new assertions match PERFORMANCE_MEASUREMENT and the V4-SMOKE-001 logical signature. No class C explicit contract violation or failing reproduction was found. No contract or runtime behavior changed.

Class B/source-informed characterizations and uncertainties:

- M-REPLAYED cannot reach COVERED through the probe: `classify` reads only the replayed flag. Also, the checker self-test uses M-REPLAYED as its PARTIAL fixture, so COVERED would fail `--self-test`; the checker was not changed.
- The CSV ordering assertions rest on a monotonic clock, exact nanosecond durations and `thread::sleep` lasting at least the requested time. Rates dividing 1e9 and command limits ≥ 2 avoid the probe's integer floor and `max(2)`, so no rounding or clamping semantics are assumed.
- BD-FIELDS shows serialization only; actual collection is BD-RUN-VALUES, still NOT_RUN.

Design deviations: the optional M-ELAPSED test was implemented. The outcome test also tallies CSV outcome names, and the binding test covers the whole BD-FIELDS list (commit, four-blob object, harness/example blobs, build mode, samples, command limit, rate), not only the fields the plan named. The roll-up's line citation `:79` was updated to `:81`; the plan named only the Counts cell, but the new §0 paragraph would otherwise leave that citation stale. Supervisor restrictions supersede the fetch, publication and hosted-CI steps.

Explicit non-claims: debug, memory-only apparatus verification. No TPS, p99, goodput or benchmark values are reported; no timing thresholds are asserted. No release probe was run. Historical V4-SMOKE-001 remains historical, not current measurement. No production durability, chain finality, provider/bank exactly-once, legal compliance, production readiness, full-system measurement, backend selection, independent conformance, A2 review or capability-grade increase is established.

Exact-head KTX and KIX protocol CI run IDs: unavailable; no committed delivery head exists for this local builder delivery. No older CI result is transferred. No git commit/push/reset, GitHub action, issue/comment, branch/tag mutation or merge was performed.

Remaining follow-up candidates: the map's 10 PARTIAL gaps, 1 NOT_COVERED row and 3 NOT_RUN release rows. No hardware, money, credentials, endpoint, Sui execution, storage engine, policy value, protocol command or production runtime was needed.
