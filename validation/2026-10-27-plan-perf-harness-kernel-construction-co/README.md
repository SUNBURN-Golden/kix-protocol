# Perf harness kernel-construction counter — local builder validation

Builder-authored evidence only; not non-author A2 review, acceptance, capability increase or merge readiness.

## Basis

Node: `plan-plan-perf-harness-kernel-construction-co`; planner run `1793068858`; loop-proposed node, not in `.aiops/program.json`; no dependencies.
The immutable task input is the supervisor-provided node and design plan in this session. There is no issue or current task document under `docs/tasks/` for this node. This is not ASTRA program mode.

Observed `origin/main` after `git fetch origin main`, and starting task HEAD: `70b976c0b8db686b1d21ff0831c275abf77a3d0a`.
Branch: `agent/kix-plan-plan-perf-harness-kernel-construction-co`. Base/HEAD delta: zero. Implementation is an uncommitted working-tree patch; the supervisor will establish the committed final task head and its exact-head CI.

Locked blob verification before and after work:

| Path | Before | After |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Complete changed-path list:

- `runtime/crates/kix-kernel/tests/support/perf_probe.rs`:
  - `construct_kernel` is the only kernel construction site, and it counts each call.
  - `run` delegates to the private `run_probe`. The test-only `run_with_injected_reconstruction` is `#[allow(dead_code)]` because the example never calls it.
  - New field `Report.kernel_constructions` and new method `Report::kernel_resets_during_workload`.
  - Report JSON `kernel_resets_during_workload` is now derived from the count. `evidence_binding_json` is unchanged.
- `runtime/crates/kix-kernel/tests/performance_harness.rs`: three new tests and one guard helper `assert_single_kernel`, which `assert_separated` now also calls.
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`: the B-ZERO-KERNEL-REBUILD row, the Counts line, one dated §0 paragraph, and one replaced §4 bullet. M-REPLAYED, the four checker-pinned rows, §3 and §5 are unchanged.
- `docs/status/EVIDENCE_MAP_ROLLUP.md`:
  - The PERFORMANCE_MEASUREMENT Counts cell is copied verbatim.
  - The PERFORMANCE_BASELINE_V4 row cited `PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:81`; it now cites `:83`, because the new §0 paragraph moved the historical reference line down by two.
- `docs/README.md`: one record pointer under the 2026-10-27 index.
- `validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md`: this record.

These have no changes: `examples/r1_perf_probe.rs`, the kernel, the contracts, the checkers and their self-test fixtures, CI, task documents, `.aiops/` and `reference/v0.3-rc1/`.

## Schema compatibility

The report JSON format string differs from `origin/main` in one token only. The literal `"kernel_resets_during_workload":0` became `"kernel_resets_during_workload":{resets}`, where `resets` is `kernel_constructions − 1`. This was checked by comparing the two format strings with that token masked.

Key, integer type and position all stay the same: the key still sits between `goodput_interpretation` and `outcomes`. For a correct run the value is 0, so the bytes are identical. The CSV header and rows are not touched.

Existing shape assertions still pass unchanged:
- the literal-key check in `assert_separated`;
- `outcome_count_json_keys_are_top_level_per_workload`;
- `workload_report_json_names_budgets_samples_and_rate`.

## Existing coverage and new tests

Before this node, B-ZERO-KERNEL-REBUILD cited `memory_probe_reports_saturation_without_recreating_kernel`, which asserted only the literal JSON constant. Kernel construction was not instrumented, so the gap was "not covered" for counting and "partially covered" for the JSON field.

The new tests use the probe, which calls public kernel APIs. Source inspection informed the expected injected-run counts. These are not clean-room independent tests, and no duration is compared with a constant.

| New test | Gap addressed |
|---|---|
| `each_workload_and_low_load_run_constructs_exactly_one_kernel` | Covers Uniform, HotSeat, Retry and Conflict at 512/128/rate 0, the low-load control (`low_load_sample_count(128)`, asserted `low_load()`) and scheduled HotSeat 16/128/10000. For each run it asserts: `kernel_constructions == 1`; derived resets 0; top-level JSON value `0`; the exact position fragment `goodput_interpretation … kernel_resets_during_workload:0,"outcomes":[`; and an unchanged CSV header. |
| `injected_kernel_reconstruction_is_counted_and_reported` | Negative sensitivity. A second construction is injected at index 128 (the first Capacity index of the correct run), inside the support layer and before that call's timing window. Results: `kernel_constructions == 2`, derived resets 1, top-level JSON `1`, and no literal `:0`. The reset hides exhaustion: (held, capacity, first_capacity) goes from the correct run's (128, 384, Some(128)) to (256, 256, Some(256)), confirmed by running. The shared guard `assert_single_kernel` panics on this report, observed with `catch_unwind`. |
| `perf_probe_routes_kernel_new_through_one_helper` | Labelled textual source characterization: `Kernel::new(` appears once in the probe, `fn construct_kernel(` once, and `kernel.clone()` never. |

`assert_separated` now calls `assert_single_kernel`, so every existing test that uses it also checks one construction.

Map row: B-ZERO-KERNEL-REBUILD goes from PARTIAL to COVERED. This is allowed because the row is not in the checker's `MUST_STATUS`, and COVERED needs tests, Gap `none` and Owner `none`.
Total before: `Counts: rows=42 COVERED=28 PARTIAL=10 NOT_COVERED=1 NOT_RUN=3`.
Total after: `Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3`.

## Characterizations (AGENTS §8)

- Class A: the counted construction matches the contract clause "zero kernel recreation during workload; no reset to hide exhaustion" for every cited run. No class-C violation was found.
- Class B: the binding JSON (`evidence_binding_json`) keeps a literal `kernel_resets_during_workload:0`. `EvidenceBinding` is built by the out-of-bounds example and describes a whole invocation, not a single run, so making it per-run would change the example's interface.
- Class B: `Kernel` derives `Clone`. The single-site and no-clone guards are textual, not a semantic proof that no other kernel value can exist.
- Class B: the injection hook costs one `Option` comparison per loop iteration in every build, including release, and it sits outside the service and call windows. No timing effect is claimed or measured.

## Commands and actual results

Inspected `.github/workflows/ktx-kernel.yml` and the stdlib/Rust blocks of `.github/workflows/protocol.yml`. The commands below are the closest local equivalents for the touched paths, plus the node's acceptance checks.

Unrelated network, SDK, Move/localnet, ZK and storage workflow steps were not run, so this is not a full hosted protocol-CI result.

How the commands ran:
- Cargo used `CARGO_NET_OFFLINE=true` and locked cached dependencies. Python used `PYTHONDONTWRITEBYTECODE=1`.
- Everything ran sequentially in the foreground.
- Rustfmt targeted only the two allowed test files; workspace formatting was check-only.

| Command | Actual result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD` | Both 70b976c0b8db686b1d21ff0831c275abf77a3d0a. |
| `git branch --show-current`; `git status --short` (before) | agent/kix-plan-plan-perf-harness-kernel-construction-co; empty. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before/after) | Both match the locked values above. |
| `rustfmt --edition 2024` on the two allowed test files | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked` | Exit 0; 20 passed, 0 failed, 0 ignored. |
| Same narrow test, `-q`, five sequential repetitions | All five: 20 passed; 0 failed. |
| `rustc --version` / `cargo --version` | rustc 1.98.1 (48a229cea 2026-09-01) / cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 122 passed; 0 failed across 9 result groups. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 311 passed; 0 failed across 43 result groups. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0; Finished `dev` profile (includes the example sharing `perf_probe.rs`). |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0; Finished `dev` profile. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; no output. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; OK |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_evidence_map_rollup.py` | Exit 0; evidence map roll-up ok: contracts=25; textual index only |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | Exit 0; self-test: pass (16 negative controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=31 plain=30 self_test=31 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_docs_index.py` and `--self-test` | Exit 0; docs index ok: scanned=284 indexed=249 allowlisted=35 / Exit 0; self-test: pass |
| Every other `python3 scripts/check_*.py` step listed in `protocol.yml`, plain and `--self-test` as listed | Run as a sequential loop over 62 unique `python3 scripts/*.py [--self-test]` invocations extracted from `protocol.yml`; 59 exit 0. Three failures are environmental or invocation-related and do not read the touched paths: `check_sdk_client.py` plain and `--self-test` exit 1 with "node 20.19.2 does not match toolchains.json nodeMajor 24" (CI pins Node 24); `verify_paid_archive.py` exit 2 because the extraction dropped its required `--report` argument, whose input is produced by an earlier CI step not run here. |
| `git diff --quiet origin/main -- runtime/crates/kix-kernel/examples scripts .github docs/contracts docs/tasks .aiops reference/v0.3-rc1 runtime/crates/kix-kernel/src` | Exit 0; no difference. |

## Non-claims

- Release probe NOT_RUN. No `examples/r1_perf_probe.rs` invocation, no benchmark, and no latency, goodput or TPS value is reported.
- No production, durability, full-system or product p99/TPS claim is made. Product TPS, p99 and failure-rate targets remain UNDETERMINED (owner: User).
- No A2 review, acceptance, capability increase or merge readiness is claimed.
- Exact-head KTX and KIX protocol CI were not run here. They belong in the supervisor's closure report for the committed final head (AGENTS §10–§11).

## Remaining uncertainty and follow-up candidates

- A per-run binding reset count would need an `EvidenceBinding`/example change, which needs separate scope.
- The other PARTIAL/NOT_COVERED/NOT_RUN rows in the map are unchanged by this node.
