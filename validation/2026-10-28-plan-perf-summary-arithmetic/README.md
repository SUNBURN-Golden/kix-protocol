# plan-perf-summary-arithmetic — local builder evidence

Task input: supervisor-provided node and design plan in the session; no issue or current task document. Historical Task 004 is context only. Approved scope: DEVELOPMENT_PLAN §7, measurement apparatus only.

Branch: `agent/kix-plan-perf-summary-arithmetic`. Cached `origin/main`, starting HEAD and base: `76ba5efbafddec8dd2279b181dda5042550ea180`; local delta zero. Supervisor prohibits network/GitHub actions, so `git fetch origin main` was not run and live-main freshness is unverified. No commit, push, PR, review or merge is authorized in this session.

## Coverage mapping recorded before adding tests

All paths below are under `runtime/crates/kix-kernel/tests/`.

| Requirement | Existing coverage and classification | Planned gap closure |
|---|---|---|
| Fixed independent nearest-rank p99 vectors | Not covered: `performance_harness.rs::outcome_summaries_do_not_label_mixed_p99_as_success` compares shared calculations and labels. | Literal expectations for singleton, unsorted, repeated, large u128 and 99/100/101/199/200/201 sample boundaries. |
| Mixed and per-outcome CSV p99 | Partially covered: `outcome_count_json_keys_are_top_level_per_workload` checks counts; `outcome_summaries_do_not_label_mixed_p99_as_success` checks presence and all-Held equality. | Cumulative-count oracle over raw CSV, both latency columns, report and scoped JSON objects. |
| Empty outcome JSON percentiles | Partially covered: `low_load_uniform_is_distinct_from_hot_seat_retry_and_saturation` and the summary test check selected report options. | Both percentile fields must be literal JSON null for every empty partition. |
| Integer goodput, zero Held and truncation | Partially covered: summary test serializes the same goodput method's result. | Positive-elapsed synthetic reports with fixed expected integers and nonzero replay/rejection/Capacity counts. |
| Labels and non-claims | Sufficiently covered: `outcome_summaries_do_not_label_mixed_p99_as_success`, `assert_separated`, `evidence_binding_records_budgets_toolchain_and_non_claims`. | Retain; compare arithmetic without wall-clock thresholds or SLO claims. |

Before edits, `git hash-object` matched both AGENTS §4 blobs: kernel `69564b166f0c27f9af5d8422f0a466b18d74c20f`, quarantine `b607996c83a119c349f1cc90469ac1ba82764e20`. Reference tree: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. A SHA-256 snapshot of every tracked file outside the authorized edit list is retained locally for final byte comparison.

## Implementation and independently specified expectations

- `performance_harness.rs::nearest_rank_p99_matches_fixed_expectations`: literals cover singleton `[42] → 42`, unsorted `[30,10,40,20] → 40`, 101 copies of 7 → 7, and `[u128::MAX, MAX-2, MAX-1] → MAX`. Descending 1..=99/100/101/199/200/201 expect 99/99/100/198/198/199 respectively. One hundred descending values MAX..MAX-99 expect MAX-1. Expectations do not call any helper or compute a rank.
- `summary_p99_matches_raw_csv_by_outcome`: the harness-local `csv_p99` sorts copied raw samples and selects the first cumulative position satisfying `100 * cumulative_count >= 99 * sample_count`. It neither calls the probe helper nor repeats its rounded index expression. Four existing workloads at (512,128,0), Uniform (32,128,0), HotSeat (16,128,10000), and Conflict (8,128,0) independently reconcile both mixed percentiles and both percentiles for every nonempty outcome against report and JSON. All seven outcome names have exactly one report summary and one JSON object, matching partition counts; every empty partition has both report options None and both JSON fields literal null. The small parser checks five distinct fields per flat object, seven objects and uniqueness by outcome; it is specific to the existing schema, not a general JSON parser. Existing `assert_separated` guards schema labels, totals and non-claims.
- `goodput_matches_fixed_integer_expectations`: synthetic reports have (Held, elapsed_ns, expected goodput) `(0,7,0)`, `(1,1000000000,1)`, `(3,2000000000,1)`, `(1,3,333333333)`, `(1,2000000000,0)`. Each includes 3 replayed, 2 rejected and 4 Capacity outcomes, with consistent counter/summary totals, and checks the method plus top-level JSON goodput/new_held/new_success_count. These reports are direct arithmetic fixtures with no workload execution or raw timing samples.

The only probe change is `#[cfg(test)] percentile_for_test`, delegating to existing `percentile(values, 99)`. Its function-scoped dead-code allowance accounts for the shared example test target; no broad lint suppression was added. The implementation, workload inputs, aggregation, timing windows, serialized schemas and interpretation labels are unchanged. Existing harness bytes are unchanged outside the inserted tests/helpers. No checker adaptations were needed.

Only M-MIXED-P99, M-OUTCOMES and M-GOODPUT change from PARTIAL to COVERED. The current explanations and roll-up reflect:

`Counts: rows=42 COVERED=33 PARTIAL=5 NOT_COVERED=1 NOT_RUN=3`

X-RELEASE-REPRO, X-OUTPUT-FILES and BD-RUN-VALUES remain NOT_RUN; BD-FAIL-CLOSED remains NOT_COVERED. No other row, gap or owner changed.

## Commands actually run and results

Commands ran from the repository root using cached dependencies; Cargo used `CARGO_NET_OFFLINE=true` and explicit `--offline` for dependency resolution. The checker batch used `PYTHONDONTWRITEBYTECODE=1`. Toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)`, `cargo 1.98.1 (797e8a9bc 2026-08-05)`.

Local ignored logs are under `.local/verification/plan-perf-summary-arithmetic/`; `checks.json` records checker commands, exit codes and log paths. The narrow harness result was captured in session tool output. Kernel and workspace output is retained in `kernel-tests.log` and `workspace-tests.log`. Counts below sum the actual successful test-result groups (including zero-test groups), not a claim of independent tests.

| Command | Actual result |
|---|---|
| `git status --short`; `git rev-parse origin/main HEAD`; `git branch --show-current` | Initially clean; both SHAs equal the base above; expected task branch. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs match before edits and at delivery. |
| `git ls-tree HEAD reference/v0.3-rc1` | Tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`; file bytes independently preserved by snapshot. |
| `rustfmt --edition 2024 runtime/crates/kix-kernel/tests/performance_harness.rs` | Exit 0; formatted added Rust code. |
| `python3 scripts/check_cargo_offline_cache.py --require` | Exit 0; 18/18 archives present, missing list empty. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked --offline` | Exit 0; 25 passed, 0 failed, 0 ignored. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 0; 127 passed, 0 failed, 0 ignored across 9 result groups. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 0; 327 passed, 0 failed, 0 ignored across 46 result groups. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 0; No warnings; all workspace targets pass. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; Formatting check passes. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | Exit 0; Only kix-types is a normal dependency of kix-kernel. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; Architecture v5 + KTX-R1 dependency gate OK; no durability/performance certification. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests pass. |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; 42 rows: 33 COVERED, 5 PARTIAL, 1 NOT_COVERED, 3 NOT_RUN. |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; 2 positive controls and 66 negative fixtures pass (in memory only). |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; 25 contracts consistent; textual index only. |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; 16 negative controls pass. |
| `python3 scripts/check_docs_index.py` | Exit 0; scanned=300, indexed=265, allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; All positive/negative controls pass. |
| `python3 scripts/check_class_b_index.py` | Exit 0; rows=216, sources=71, symbols=39; textual index only. |
| `python3 scripts/check_class_b_index.py --self-test` | Exit 0; 20 negative controls pass. |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; scripts=35, plain=34, self_test=35, self_test_only=1, docs=22, citations=99. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; 13 negative controls pass. |
| `python3 scripts/check_ci_test_discovery.py` | Exit 0; reference_suites=6, node_tests=8, modules=4, excluded=3. |
| `python3 scripts/check_ci_test_discovery.py --self-test` | Exit 0; 18 negative controls pass. |
| `python3 scripts/check_cargo_offline_cache.py` | Exit 0; 18/18 archives present; no missing archives. |
| `python3 scripts/check_cargo_offline_cache.py --self-test` | Exit 0; Legacy and tomllib, cache, environment and error-path controls pass. |
| `python3 .local/verification/plan-perf-summary-arithmetic/audit_preservation.py` | Exit 0; 1,076 protected files byte-identical, exact six-file delivery, old harness bytes retained, only wrapper added to probe, only three map rows changed. |
| `git diff --check` | Exit 0; no whitespace errors. |

No test or verification check failed. An exploratory CI-path lookup for nonexistent `.github/workflows/verify.yml` returned exit 2; inspection then used the actual `protocol.yml` and `ktx-kernel.yml` definitions. No CI file was edited.

The Rust, architecture and listed stdlib-document checks match the applicable local portions of those workflows. This is not full hosted protocol CI. Bootstrap, release probe, benchmark campaigns, storage experiments, chain journeys, providers and public endpoints were not invoked. All jobs ran as foreground commands, not detached/background jobs.

## Complete changed-path list

- `runtime/crates/kix-kernel/tests/performance_harness.rs`
- `runtime/crates/kix-kernel/tests/support/perf_probe.rs`
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`
- `docs/status/EVIDENCE_MAP_ROLLUP.md`
- `docs/README.md`
- `validation/2026-10-28-plan-perf-summary-arithmetic/README.md`

## Preservation, classification and limitations

Before/after/delivery locked blobs all match AGENTS §4: kernel `69564b166f0c27f9af5d8422f0a466b18d74c20f`, quarantine `b607996c83a119c349f1cc90469ac1ba82764e20`. The SHA-256 before/after audit checks every tracked file outside the edit allowlist: all 1,076 are byte-identical. This includes `reference/v0.3-rc1/**`, `.aiops/**`, `docs/tasks/**`, all contracts, both CI definitions, Cargo manifests/lockfile, historical validation records and release example/pins. The two conditionally authorized checker files are separately equal to HEAD, so checker validation and negative controls were not weakened. The original historical-reference text and every untargeted map row remain byte-identical.

Class A: the tested apparatus arithmetic matches the contract for these fixtures. No class-C explicit contract violation was found; no reproduction requiring implementation changes or DECISION_REQUIRED was needed.

Class B / remaining uncertainty: nonzero other_error/other_observation outcomes remain unexercised; the existing workload inputs expose no such outcomes. Empty helper inputs, zero elapsed_ns and overflow paths are outside this node's positive-elapsed fixtures. Service-window content, elapsed setup/output exclusion and actual release binding collection retain their existing map gaps. The known release-example LOCKED_EDGE mismatch is outside scope; the example and frozen pins are preserved and the refusal path was not run. This source-informed apparatus evidence is not clean-room proof or non-author A2 review.

No wall-clock performance threshold, SLO, throughput result, failure-rate target, acceptable hardware condition or product policy value was chosen. Product TPS/p99/failure-rate values remain UNDETERMINED (owner: User). No full-system, durability, production-readiness, chain-finality, provider/bank exactly-once, legal, backend comparison/selection, release or R2 claim follows from this work.

## Delivery gates and deviations

Implementation and final task commit SHA: not created; the tested output is the uncommitted working-tree patch over starting HEAD `76ba5efbafddec8dd2279b181dda5042550ea180`. The supervisor owns commit/publication and must establish the final exact head. Merge commit and post-merge checks: not applicable, no merge performed.

| Required external gate | Actual state |
|---|---|
| Non-author exact-HEAD A2 review | Pending supervisor; no review claimed. |
| KTX kernel verification at final head | NOT_RUN here; no run ID/status/conclusion available. |
| KIX protocol verification at final head | NOT_RUN here; no run ID/status/conclusion available. |
| Post-merge main/push CI | Not applicable; no merge. |

Deviation from AGENTS §1: fetch omitted under the supervisor's explicit no-network instruction; cached base observations are not fresh-main evidence. No implementation deviation from the supplied design plan. As specified by the node, the supervisor's session input substitutes for a current task document, and there is no task issue. No commits, pushes, branches/tags, PRs, issues, comments or GitHub/network actions were performed. No independent agent was delegated work.

Local builder handoff is READY. This is not merge-ready: non-author exact-head review, both successful exact-head hosted workflows and user merge authorization remain separate requirements. Remaining follow-up candidates are the unchanged map gaps and unrun release procedures; none was started here.
