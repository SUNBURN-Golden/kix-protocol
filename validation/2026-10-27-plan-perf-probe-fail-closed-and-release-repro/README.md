# Perf probe frozen-blob gate and local release reproduction

## Basis

The task input is the supervisor-provided node `plan-perf-probe-fail-closed-and-release-repro` from planner run `1793078707` and the 2026-11-18 owner decision (`pt224u`). The node has no issue or task file. [Task 004](../../docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md) supplies the historical procedure. [Performance measurement contract](../../docs/contracts/PERFORMANCE_MEASUREMENT.md#실행과-자료).

| Ref | SHA |
|---|---|
| Task branch HEAD and base | `9ed15a7adc93359e99bb5c3512a3ca20c77cb264` |
| Task branch HEAD tree | `10b5d52abd0be088877bddc69a442ed41836b9c7` |
| Local `origin/main` ref | `5be902b5cd7d314e9e7d05ab919597385896e48f` |

The supplied branch `agent/kix-plan-perf-probe-fail-closed-and-release-repro` was 308 commits behind the local `origin/main` ref and had no branch-only commits. The supervisor prohibited a fresh fetch and reserved Git and GitHub publication. The branch base stayed at the supplied SHA. The local `origin/main` snapshot has a different edge blob, `16b3c667e162b716da06a2852f227114f679066a`, and the same model blob. Integration onto that snapshot requires reconciling the edge pin and verifying against the integrated sources. This record covers the uncommitted patch on the supplied worktree. Final implementation and task-head commit IDs, the merge commit, and both exact-head workflow run IDs, statuses and conclusions are unavailable in this session.

## Frozen blobs and owner decision

`git hash-object` returned the following worktree values at resume, before and after the release run, and at final verification. The first two rows are the AGENTS §4 locks.

| Path under `runtime/crates/kix-kernel/` | Worktree blob |
|---|---|
| `src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `tests/contract_edge_cases.rs` | `8533d6419077d6a073d16ca2fce3a7d461a4de5b` |
| `tests/support/model_v4.rs` | `f020860b86933bf7511befccdb833b0c532b3629` |

**Owner-approved pin update.** `LOCKED_EDGE` changed from `d37ea7df55423c83bedee16bf12bdc8dd61f7cae` to the worktree hash above. `LOCKED_MODEL` already matched `f020860b86933bf7511befccdb833b0c532b3629`. The pin update is the one-line constant change in the example. Its read-only regression test checks both example-specific pins.

The earlier draft recorded that the example exited 1 at the gate with `Error: "frozen blob mismatch; refusing to write unbound performance evidence"` and the output directory was absent. In this session, the new drift test independently reproduced the pin mismatch before the update, without running the example or changing either frozen fixture. The draft's stop condition was resolved by the owner decision.

## Coverage and behavior

| Requirement | Earlier coverage | Evidence added here |
|---|---|---|
| BD-FAIL-CLOSED comparison | Absent | `frozen_blob_gate_accepts_only_exact_four_pin_match` accepts equivalent synthetic strings. `frozen_blob_gate_refuses_a_mismatch_on_each_of_the_four_pins` checks each single mismatch, all four together, and near misses such as case, whitespace and length. |
| BD-FAIL-CLOSED call order | Absent | `example_runs_frozen_blob_gate_before_any_output` checks the example source text for the gate after all four hash reads and before workloads, file writes and output. This is a source characterization. |
| Edge and model pin drift | Absent. `locked_sources_and_new_harness_sources_are_identified` checks the two AGENTS locks and records the model hash. | `release_probe_extra_pins_match_worktree_blobs` checks the actual edge and model worktree hashes against the example constants with read-only `git hash-object`. It caught the stale edge pin before the update. |
| BD-FIELDS and BD-RUN-VALUES binding | Partial. `evidence_binding_records_budgets_toolchain_and_non_claims` and `evidence_binding_serializes_tree_probe_toolchain_host_and_files` check serialization with synthetic inputs. | A successful local release run supplies the actual binding and permits checking it against Git. |
| X-RELEASE-REPRO and X-OUTPUT-FILES | Absent for release. `memory_probe_reports_saturation_without_recreating_kernel` exercises the debug smoke. | The archived run produced all eleven files declared by the example. |

The three synthetic and source-order tests have no runtime filesystem access. The example still collects the four hashes, compares them exactly and returns the same error on any mismatch. It calls the gate before running the probe or creating the output directory. The original output set and write order are preserved.

## Local release run

Ran once after the authorized pin update, with the output directory absent beforehand. The run began at 14:01:18 UTC on 2026-11-18 and exited **0**. The release build completed and stderr contained the ordinary Cargo compile and run messages. The command was run from the worktree root with `CARGO_NET_OFFLINE=true` and the log directory already created.

```bash
cargo run --manifest-path runtime/Cargo.toml -p kix-kernel --example r1_perf_probe --release --locked -- .local/perf/plan-perf-probe-fail-closed-and-release-repro 8192 4096 1000 >.local/verification/perf-probe-release/stdout.log 2>.local/verification/perf-probe-release/stderr.log
```

The following files were present in the local output directory and matched both the example's `OUTPUT_FILES` and the binding's `output_files` list. The links point to byte-identical copies prepared for the supervisor under this validation record, as authorized by the 2026-11-18 owner decision. The timing data in these files characterizes a single local, in-memory probe run.

| Output | Archived files | CSV sample rows |
|---|---|---:|
| Uniform | [uniform.csv](release/uniform.csv), [uniform.json](release/uniform.json) | 8192 |
| Hot seat | [hot-seat.csv](release/hot-seat.csv), [hot-seat.json](release/hot-seat.json) | 8192 |
| Same-command retry | [same-command-retry.csv](release/same-command-retry.csv), [same-command-retry.json](release/same-command-retry.json) | 8192 |
| Retained conflict growth | [retained-conflict-growth.csv](release/retained-conflict-growth.csv), [retained-conflict-growth.json](release/retained-conflict-growth.json) | 8192 |
| Low-load uniform | [low-load-uniform.csv](release/low-load-uniform.csv), [low-load-uniform.json](release/low-load-uniform.json) | 32 |
| Binding | [binding.json](release/binding.json) | |

Each of the five workload JSON files had the same sorted top-level key set.

```text
budget_phase, build_mode, business_rejected, capacity, command_limit,
commands_budget, conflict_retained, debug_assertions, elapsed_ns,
first_capacity_index, goodput_interpretation, history_growth, hot_seat,
inventory_seats, kernel_resets_during_workload, low_load,
memory_only_new_held_per_elapsed_s, mixed_result_p99_scheduled_latency_ns,
mixed_result_p99_service_ns, new_held, new_success_count, non_claims,
observations_limit, orders_limit, other, other_error, other_observation,
outcomes, p99_interpretation, rate, rate_meaning, remaining, replayed,
same_command_retry, samples, samples_after_first_capacity, saturation,
scheduled_latency_ns_meaning, scope, service_ns_meaning, target_arch,
target_os, workload, workload_shape
```

The table lists every `binding.json` top-level field. `commit` and `tree` identify Git HEAD. The three source hashes identify the actual patched worktree bytes used for the run, which were independently checked against the emitted values.

| Field | Run value |
|---|---|
| `build_mode`, `debug_assertions` | `release`, `false` |
| `command_limit`, `orders_limit`, `observations_limit`, `inventory_seats` | `4096`, `4096`, `128`, `4096` |
| `commit`, `tree` | `9ed15a7adc93359e99bb5c3512a3ca20c77cb264`, `10b5d52abd0be088877bddc69a442ed41836b9c7` |
| `evidence_class` | `local apparatus binding; not a product performance result` |
| `example_blob` | `5865af6571303c7fa7bef5d179e4074600458686` |
| `harness_blob` | `72f120048aac5841f40058b0fff1b28b2ca7c4bd` |
| `probe_blob` | `ca7fd57ab6dd820868dbce7300ee3b31f2eb7be4` |
| `host_uname` | `Linux 6.12.113+ #1 SMP PREEMPT_DYNAMIC Mon Nov  9 20:07:52 UTC 2026 x86_64` |
| `kernel_resets_during_workload` | `0` |
| `locked_blobs` | `kernel`, `quarantine_capacity`, `contract_edge_cases` and `model_v4` map to the respective hashes in the frozen-blobs table. |
| `samples`, `low_load_samples` | `8192`, `32` |
| `non_claims` | Exact statement preserved in the archived binding. |
| `output_files` | In order, uniform CSV/JSON, hot-seat CSV/JSON, same-command-retry CSV/JSON, retained-conflict-growth CSV/JSON, low-load-uniform CSV/JSON, binding.json. |
| `product_slo` | `null` |
| `rate`, `rate_meaning` | `1000`, `fixed-origin i/rate schedule; a late driver does not shift the origin` |
| `target_arch`, `target_os` | `x86_64`, `linux` |
| `toolchain` | `rustc 1.98.1 (48a229cea 2026-09-01)` |

## Changed paths

- `runtime/crates/kix-kernel/examples/r1_perf_probe.rs`
- `runtime/crates/kix-kernel/tests/support/perf_probe.rs`
- `runtime/crates/kix-kernel/tests/performance_harness.rs`
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-27-plan-perf-probe-fail-closed-and-release-repro/README.md`
- The eleven files named in the output table under `validation/2026-10-27-plan-perf-probe-fail-closed-and-release-repro/release/`.

The evidence map documents the local findings in BD-FAIL-CLOSED, X-RELEASE-REPRO, X-OUTPUT-FILES and BD-RUN-VALUES. Its checker requires the existing statuses and empty Tests cells, so the recomputed line stays `Counts: rows=42 COVERED=29 PARTIAL=9 NOT_COVERED=1 NOT_RUN=3`. The index pointer and in-place map wording connect these rows to the validation record. The historical line-83 anchor used by the rollup is preserved.

## Verification

All commands below ran in the foreground from the worktree root. Cargo ran offline and used the existing lockfile. Python commands ran with bytecode generation disabled or in isolated mode for output inspection.

| Command | Result |
|---|---|
| `git status --short --branch`, `git rev-parse origin/main HEAD`, `git merge-base HEAD origin/main`, `git rev-list --left-right --count HEAD...origin/main` | Supplied branch and ref SHAs recorded above, with delta `0 308`. |
| `git hash-object` on all four frozen inputs | The recorded hashes matched at resume, before and after release, and at final verification. |
| `git log -6 --oneline -- runtime/crates/kix-kernel/tests/contract_edge_cases.rs runtime/crates/kix-kernel/tests/support/model_v4.rs` | The branch history shows edge-file changes in `7ba8003` and `41abd14`. |
| `cargo fetch --manifest-path runtime/Cargo.toml --offline --locked` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked release_probe_extra_pins_match_worktree_blobs -- --exact` | Before the authorized pin update, exit 101 on the expected `LOCKED_EDGE` mismatch. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked` | Exit 0, 24 passed. |
| Release `cargo run` above and preceding `test ! -e` for its output directory | Both exit 0. The directory was initially absent and the run produced eleven files. |
| `python3 -I -` with local output inspection and archival | Exit 0. Verified file inventory, JSON keys, CSV row counts, Git binding values and byte-identical archival copies. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0, 126 passed across 9 suites. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0, 321 passed across 44 suites. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked` | Exit 0. The kernel's normal dependency is `kix-types`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. Architecture and declared dependency gate passed. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0, 7 passed. |
| 55 `python3 scripts/check_*.py` invocations in the `Stdlib offline document checks` block of `.github/workflows/protocol.yml` | 53 passed on the first run. The performance map checker failed in both modes because §5 omitted its required `no benchmark claim` phrase. Restored the phrase and reran the affected checks below. |
| `python3 scripts/check_performance_measurement_evidence_map.py`, plain and `--self-test` | Both exit 0 after the wording fix. The checker reports 42 rows and the expected counts. |
| `python3 scripts/check_evidence_map_rollup.py`, plain and `--self-test` | Both exit 0 on the final map. |
| `python3 scripts/check_docs_index.py`, plain and `--self-test` | Both exit 0 on the final map and linked record. |
| `python3 scripts/check_ci_checker_wiring.py`, plain and `--self-test` | Both exit 0 on the final map. |
| `git diff --check`, `git diff --quiet HEAD --` over protected paths, and `git diff --cached --quiet` | Exit 0. The protected paths match the supplied base and the index has no staged changes. |

## Characterizations and limits

- Class A (§8). The gate refused the stale pin in the earlier draft and the example emitted the declared files after the authorized pin update. The actual pin drift was a configuration finding. No class C contract violation was found.
- Class B (§8). The contract specifies refusal on a mismatch. It leaves future edge and model pin update policy unspecified. The owner decision sets the values for this node.
- Exact string equality is characterized by synthetic tests. The existing Git collection trims Git's line ending before comparison. The test suite does not deliberately change a frozen file to exercise the full refusal path.
- The single release run characterizes the supplied worktree and host. Product TPS, p99 and failure-rate targets remain UNDETERMINED. This record makes no SLO, past baseline comparison, full-system, durability or production claim. Dedicated-hardware repetitions, exact-head hosted CI and independent A2 review remain outside this builder evidence.
