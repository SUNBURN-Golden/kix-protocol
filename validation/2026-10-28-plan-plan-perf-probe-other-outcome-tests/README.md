# Nonzero perf probe other outcomes — builder validation

Task/node: `plan-plan-perf-probe-other-outcome-tests`. The supervisor-provided node and design plan in the session are the immutable task input; no task issue or current file under `docs/tasks/` exists for this node. Historical Task 004 is context only. This is not ASTRA program mode.

Observed cached `origin/main`, base and starting branch HEAD: `bcfb0d201d35add16a6e1345be0ef27da8ed0709`; local delta zero. Branch: `agent/kix-plan-plan-perf-probe-other-outcome-tests`. No fetch was permitted by the supervisor; live-main freshness is unverified. Implementation/final task commit: not created; delivery is an uncommitted working-tree patch over that SHA. The supervisor owns publication and establishment of the exact final head. Merge SHA and post-merge checks: not applicable.

## Existing coverage mapped before edits

| Requirement | Existing coverage | Gap addressed |
|---|---|---|
| Ordinary workloads keep other zero | Sufficient: `performance_harness.rs::other_stays_zero_for_every_reachable_probe_input` samples all four generated workloads and budget/rate boundaries. | Retained as the zero control; comment clarifies ordinary workloads. |
| Positive non-Capacity error / non-Conflict observation | Not covered: `perf_probe.rs::classify` has both arms, but ordinary inputs reach neither. | New public-API input fixture drives a fresh regressed-time reserve and an applied capture. |
| Counter conservation and serialized other fields | Partial: `assert_separated`, `outcome_count_json_keys_are_top_level_per_workload`, `summary_p99_matches_raw_csv_by_outcome` verify zero-valued other partitions. | Exact positive counts, ordered CSV rows and scoped JSON count/role/percentile checks. |
| Standard workload counts, budgets, retry and construction accounting | Sufficient: `memory_probe_reports_saturation_without_recreating_kernel`, `retry_replays_complete_first_result`, `each_workload_and_low_load_run_constructs_exactly_one_kernel`, `injected_kernel_reconstruction_is_counted_and_reported`. | Existing regressions retained and run; no duplicate workload tests. |

Paths above are under `runtime/crates/kix-kernel/tests/`, with the shared probe in `support/`. Both AGENTS §4 blobs matched before edits: kernel `69564b166f0c27f9af5d8422f0a466b18d74c20f`, quarantine `b607996c83a119c349f1cc90469ac1ba82764e20`. The initial SHA-256 snapshot covers 1,096 tracked files; the preserved reference tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.

## Implementation and acceptance evidence

`perf_probe.rs::run_with_injected_other_outcomes` is test-gated and uses a private fixture selector, following the reconstruction seam. It constructs exactly one kernel through `construct_kernel`, with command limit 128, two samples and rate 0. Before origin/timing, request 1 at time 11 must return its original Held result without replay. The measured inputs are fresh request 2 at time 10 and a matching capture for request 1 at time 11, event 500, evidence hash [60;32]. The fresh identity prevents replay from bypassing the time check: the locked kernel produces ClockRegression; the matching capture produces PaymentConfirmed. Public order queries after elapsed timing confirm request 1 is PaymentConfirmed and request 2 created no order. These are source-informed public-API fixtures, not new semantics.

The report label is `injected-other-outcomes`. Ordinary workload names, their inputs, CLI, budgets, classifier, aggregation and JSON/CSV schemas are retained. Setup and post-state queries occur outside measured samples. No timing-equivalence or performance claim is made from the fixture-selector refactor.

- `other_outcomes_count_real_reserve_error_and_applied_capture` requires total=2, other_error=1, other_observation=1, other=2, other equal to its two subcounts, zero held/replayed/rejected/Capacity/conflict counts, remaining=4095 from setup alone, no first Capacity and no post-Capacity samples. Both captured reserve-reply slots are None. CSV outcomes must be exactly other_error then other_observation. Existing separation/single-kernel guards check conservation, one construction and zero resets.
- `other_outcomes_json_matches_measured_calls` checks top-level samples=2, other_error=1, other_observation=1, other=2, new_held=new_success_count=capacity=conflict_retained=0. Each other outcome has a unique JSON object, count 1 and role unclassified; Held has count 0 and role new-success. Both percentile options and JSON values reconcile to the corresponding raw CSV singleton; empty Held percentiles are None/null. No wall-clock threshold is asserted.

Only M-OTHER changes from PARTIAL to COVERED, with Gap/Owner none. Current counts: `rows=42 COVERED=34 PARTIAL=4 NOT_COVERED=1 NOT_RUN=3`. M-SERVICE-NS, M-ELAPSED, all BD-* and X-* rows retain their existing statuses and owners; release rows remain NOT_RUN pending the open LOCKED_EDGE owner decision. The rollup count cell alone is synchronized. Historical attribution remains preserved. Checker PARTIAL fixtures move to unchanged M-SERVICE-NS; three new in-memory missing-symbol controls detect each new test and the fixture citation. No locked file is mutated by these controls.

## Commands actually run and results

Commands run from the repository root, offline, as foreground work. Toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)` and `cargo 1.98.1 (797e8a9bc 2026-08-05)`. Ignored local logs and machine-readable command outcomes are under `.local/verification/plan-plan-perf-probe-other-outcome-tests/`. Narrow harness output is recorded in session tool output. Result-group totals count actual passed tests across the emitted groups; they do not imply independence.

| Command | Actual result |
|---|---|
| `git status --short; git rev-parse origin/main HEAD; git branch --show-current` | Exit 0; initially clean; cached origin/main and HEAD both equal base above; expected branch. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before edits and at delivery; both locked blobs match the required hashes. |
| `git ls-tree HEAD reference/v0.3-rc1` | Exit 0; tree a6ecb124dc2b2267ca6be19e39fbe2aef143074b; all reference bytes preserved by the snapshot audit. |
| `rustc --version; cargo --version` | Exit 0; toolchain versions recorded above. |
| `python3 scripts/check_cargo_offline_cache.py --require` | Exit 0; 18/18 archives present, missing list empty; no dependency download. |
| `rustfmt --edition 2024 runtime/crates/kix-kernel/tests/support/perf_probe.rs runtime/crates/kix-kernel/tests/performance_harness.rs` | Exit 0; formatted only the two authorized Rust files. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked --offline` | Exit 0; 27 passed, 0 failed, 0 ignored, including both new nonzero tests. |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; rows=42 COVERED=34 PARTIAL=4 NOT_COVERED=1 NOT_RUN=3. |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; 2 positive controls and 69 negative fixtures pass; all mutations in memory only. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 134 passed across 9 groups; 0 failed, 0 ignored. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 334 passed across 46 groups; 0 failed, 0 ignored. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; All workspace targets pass with -D warnings. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; Workspace formatting check passes. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 architecture gate tests pass. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; Only kix-types is a normal dependency of kix-kernel. |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test: pass (16 negative controls) |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=304 indexed=269 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_class_b_index.py` | Exit 0; class B index ok: rows=217 sources=72 symbols=45; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0; self-test: pass (20 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; self-test: pass (18 negative controls) |
| `python3 .local/verification/plan-plan-perf-probe-other-outcome-tests/audit_preservation.py` | Exit 0; 1,090 protected tracked files byte-identical; both locks match; exact seven-path delivery; only M-OTHER map row changes; historical attribution, classifier and other rollup cells preserved. |
| `git diff --check` | Exit 0; no whitespace errors. |

No test or verification check failed. The initial tracked-file SHA-256 snapshot was collected with a Python stdlib script via stdin before edits and stored in `/tmp/kix-other-before.json`; the audit above compares it against delivery bytes. No retries or automatic downloads occurred.

## Complete changed-path list

- `runtime/crates/kix-kernel/tests/support/perf_probe.rs`
- `runtime/crates/kix-kernel/tests/performance_harness.rs`
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`
- `scripts/check_performance_measurement_evidence_map.py`
- `docs/status/EVIDENCE_MAP_ROLLUP.md`
- `docs/README.md`
- `validation/2026-10-28-plan-plan-perf-probe-other-outcome-tests/README.md`

## Preservation, classification and non-claims

Before/after/delivery locked blobs match the required hashes above. The byte-preservation audit confirms all 1,090 tracked files outside the six existing authorized edit paths remain byte-identical, including both locks, every `reference/v0.3-rc1/**` file, `.aiops/**`, `docs/tasks/**`, contracts, Cargo configuration/lockfile, workflows, release example/frozen pins and historical validation records. It also requires the exact seven-path delivery, compares every untargeted map row, preserves historical-reference text verbatim, checks classifier bytes unchanged and checks that the rollup differs only in its performance count cell. A final commit/merge blob check is not available because no commit or merge was authorized here.

Class A: these apparatus outcomes and their accounting match PERFORMANCE_MEASUREMENT. No explicit class-C contract violation was found. Class B/source-informed characterization: the driven time regression and matching capture exercise only these two other categories; this is not exhaustive coverage of every non-Capacity error or every non-Conflict observation. No contract-undefined behavior is newly assigned semantics. Service-window content and elapsed setup/output exclusions retain their source-read gaps. Actual release binding collection and refusal paths remain unrun. The known LOCKED_EDGE owner decision remains open; the release example and frozen pins are unchanged.

No release example, product benchmark, paid service, credentials, public endpoint, provider/bank/KYC call, real funds, chain journey, Sui testnet/mainnet, production runtime, storage engine, replication, R2, new protocol command or product policy value was needed or invoked. No numeric perf threshold, budget or contract value changed. Product TPS/p99/failure-rate targets remain UNDETERMINED (owner: User). This in-memory debug apparatus evidence does not establish full-system performance, durability, chain finality, bank exactly-once, legal compliance, production readiness, backend comparison/selection, clean-room independence or A2 review.

## Delivery gates and deviations

| Gate | Actual state |
|---|---|
| Non-author exact-final-head A2 review | Pending supervisor; not performed or claimed. |
| Exact-head KTX kernel verification | NOT_RUN here; no run ID/status/conclusion available. |
| Exact-head KIX protocol verification | NOT_RUN here; no run ID/status/conclusion available. |
| Post-merge main/push CI | Not applicable; no merge. |

Deviation: AGENTS §1 fetch omitted under the explicit supervisor no-network rule. No implementation deviation from the supplied design plan. The session node input substitutes for a current task file as specified. No git commit/push/reset, gh, GitHub/network action, issue, PR, comment, ASTRA marker, branch/tag change or delegated agent work occurred. Local verification covers the applicable Rust, architecture and document-check portions of `ktx-kernel.yml` and `protocol.yml`; full hosted protocol CI and final-head review remain supervisor gates.

Local READY means builder handoff only, not merge-ready. Follow-up candidates remain the unchanged map gaps and the release owner decision; none was started here.
