# Task 004 — performance measurement apparatus

Task document (immutable, not modified by this implementation):
`docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md` on
`docs/task-004-perf-measurement-20260925`.
Issue: https://github.com/BeautifulMind-JT/kix-protocol/issues/55
Docs PR: https://github.com/BeautifulMind-JT/kix-protocol/pull/54

Requested base: `729a106add049ad1a75b90f99c00b6e0ccb8a67d`.
Implementation branch: `agent/task-004-perf-measurement-20260925`.

This note records the apparatus change. It does not adopt a product TPS, p99,
or fail-rate SLO. It does not select a backend or compare PostgreSQL.

## What changed

`runtime/crates/kix-kernel/tests/support/perf_probe.rs` now reports:

- separate counts for new Held, business reject, same-command replay, Capacity,
  and retained conflict (`other` no longer stores retained conflict);
- per-outcome service and scheduled-latency p99, null when that outcome has
  zero samples;
- mixed nearest-rank p99 only under `mixed_result_p99_service_ns` and
  `mixed_result_p99_scheduled_latency_ns`, with an explicit interpretation that
  this distribution is not new-success, purchase, or product p99;
- `memory_only_new_held_per_elapsed_s` as an integer workload-loop ratio,
  labeled as not product TPS (rate>0 includes scheduled waits);
- load distinctions: `low_load`, `hot_seat`, `same_command_retry`,
  `history_growth`, `saturation`, and `budget_phase`;
- samples after the first Capacity index, still present in the raw CSV;
- build mode, target os/arch, budgets, and kernel resets during the workload (0).

`examples/r1_perf_probe.rs` writes those artifacts plus `low-load-uniform.*`
(`min(32, command_limit-1)` uniform samples) and `binding.json`. The example
refuses to write the directory when the four frozen blobs differ from:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`
- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs` `d37ea7df55423c83bedee16bf12bdc8dd61f7cae`
- `runtime/crates/kix-kernel/tests/support/model_v4.rs` `f020860b86933bf7511befccdb833b0c532b3629`

No kernel, quarantine, contract-edge, or model_v4 source was edited.

## Commands

Debug apparatus check (CI also runs this inside `cargo test -p kix-kernel`):

```bash
cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked
```

Release-mode local evidence. This is not a CI step and not a product result.
Output is gitignored under `.local/perf/task-004/`. Run it on the commit being
described so `binding.json` `commit` matches that HEAD. Do not copy latency,
goodput, or p99 integers from that directory into git.

```bash
cargo run --manifest-path runtime/Cargo.toml -p kix-kernel --example r1_perf_probe --release --locked -- .local/perf/task-004 8192 4096 1000
```

`binding.json` should show `build_mode` `release`, `debug_assertions` false,
the frozen blobs above, `samples` 8192, `low_load_samples` 32, `command_limit`
4096, `orders_limit` 4096, `observations_limit` 128, `rate` 1000, `product_slo`
null, and `kernel_resets_during_workload` 0. `host_uname` and `toolchain` are
whatever that process observed. A shared or local machine is not a pinned
benchmark host.

V4-SMOKE-001 (`docs/contracts/PERFORMANCE_BASELINE_V4.md`) stays the 2026-09-16
historical debug profile. Its latency figures are not reused here, and its
profile bytes were not edited. Debug smoke and this release run are not a
speedup comparison.

## Logical admission counts for the release invocation

These counts follow the existing v4 admission rules at 8192 samples, command
limit 4096, order limit 4096, observation limit 128, one seat segment of 4096.
They are deterministic classifications, not latency targets. Rate does not
change them. The 512-sample debug smoke in `performance_harness` remains the
checked-in regression; this table is the same rules at the documented local
probe size.

Before the implementation commit, a debug `rate=0` run of this same sample and
budget size wrote `.local/perf/task-004-debug-counts/` and matched the table.
That directory is gitignored, it is not the release evidence, and its latency
and goodput integers are not copied here.

| file | new Held | business rejected | replayed | conflict retained | Capacity | first Capacity index | samples after first Capacity | low-load |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| uniform | 4096 | 0 | 0 | 0 | 4096 | 4096 | 4095 | no |
| hot-seat | 1 | 4095 | 0 | 0 | 4096 | 4096 | 4095 | no |
| same-command-retry | 1 | 0 | 8191 | 0 | 0 | none | 0 | no |
| retained-conflict-growth | 0 | 0 | 0 | 127 | 8065 | 127 | 8064 | no |
| low-load-uniform | 32 | 0 | 0 | 0 | 0 | none | 0 | yes |

Conflict capacity is the observation budget (128, one slot already used by the
prefill), not the command limit. Hot-seat under the command budget still
business-rejects and is not low-load. Retry does not spend a new command slot
per replay.

## Non-claims

- No approved absolute TPS, p99, or fail-rate.
- Mixed p99 is not purchase p99 or new-success p99. Per-outcome `held` latency
  is the new-success slice only, and it is still a memory-only local sample.
- The harness is pure in-memory v4 on one driver. It does not measure a
  database, chain finality, network, or multi-threaded cell.
- CI debug smoke is apparatus verification, not production p99/TPS.
- One release-mode local directory is not a durable throughput result and not
  a repeated controlled-hardware campaign.
- No PostgreSQL comparison and no backend selection.
- No Stage2 reclaim/GC/index, R2, PR #11 (a), schema/SDK product work, or v4
  kernel behavior change.
- No claim that the kernel, fencing, or money movement is production-ready.

Secondary E-4 / lifecycle evidence was not added. Open lifecycle inputs in
`docs/contracts/FIRST_BATCH_OPEN_INPUTS.md` are still unresolved, and the frozen
model and contract-edge files were left unchanged.

## Exact-head CI

Record KTX kernel verification and KIX protocol verification for the final
implementation head in the PR conversation. Do not add a later commit only to
store those run IDs. Success of an earlier SHA does not apply to this head.
