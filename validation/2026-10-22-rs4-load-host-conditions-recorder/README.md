# RS-4 load host-conditions recorder

## Identity and delivery boundary

Node: `plan-rs4-load-host-conditions-recorder`; proposed by KIX planner run
`1792645030` as a loop-proposed node. It is not in `.aiops/program.json`, has no
issue and no task document under `docs/tasks/`, and is not ASTRA program mode.
Audit floor A2. The builder has no merge authority; nothing is committed,
published or merged by the builder.
Branch: `agent/kix-plan-plan-rs4-load-host-conditions-recorder`.
Starting HEAD (and cached `origin/main`, no fetch run; the supervisor prohibits
network actions): `1a69364eca0e2a219854c443f8183a9b0e733a2d`.

Delivered: `reference/rights_scale/host_conditions.py` (stdlib only),
`reference/rights_scale/test_host_conditions.py`, this record and one docs index
line. Unchanged: `scripts/**` (including `run_rights_scale_l1_load.py`),
`.github/**`, `reference/v0.3-rc1/**`, `runtime/**`, `.aiops/`, `docs/tasks/`,
the load driver and the load plan.

Why it exists: the rs-4-l2 `DECISION_REQUIRED` attributes its `FAILED_MEASUREMENT`
to shared-host conditions (load average 14 to 125 on 8 vCPUs, memory exhaustion,
a suspend of about 6.8 h). The L1 `host.json` records static facts only
(`cpu_count`, `mem_total_bytes`, versions), so no committed tool captured those
conditions. This module supplies the recorder; it supplies no threshold.

## What it does

`python3 reference/rights_scale/host_conditions.py sample --out F --interval S [--count N]`
appends one JSON line per interval: `/proc/loadavg`, `/proc/meminfo` (MemTotal,
MemAvailable, SwapTotal, SwapFree), `/proc/uptime`, the `btime` line of
`/proc/stat`, `os.cpu_count()`, the `sched_getaffinity` size, the wall clock
(UTC text and epoch seconds) and the monotonic clock. A file that cannot be read
or parsed makes its fields `null` and is named in the line's `errors`; the
sampler keeps running. It flushes every line and stops after `--count` samples or
on SIGTERM/SIGINT.

`python3 reference/rights_scale/host_conditions.py summarize --samples F --interval S --gap-factor N [--out F]`
writes `host-conditions-summary.json` (version
`kix-rs4-host-conditions-summary-v1`, beside the samples unless `--out` is given):

- min/median/max of `load1`, `load5`, `load15`, raw and divided by the affinity
  core count (`cpu_count` when the affinity size is unavailable);
- min/median/max of `MemAvailable` and `SwapFree` in bytes;
- every pair of consecutive samples whose wall-clock distance exceeds
  `gap-factor x interval`, each with the monotonic distance beside it;
- the distinct `btime` values, the number of `uptime` regressions, the number of
  backward wall-clock steps, the number of samples with read errors.

`--interval` and `--gap-factor` are required with no default, so no policy value
enters the tree. The summary has no verdict, status, pass/fail, quiet or idle
field, and its `note` says the acceptable load level is UNDETERMINED (User).

## How a future L1/L2 run would use it

This is a procedure for whoever runs the driver; it is not an edit to the runner.
The runner `scripts/run_rights_scale_l1_load.py` refuses a non-empty output
directory and writes `manifest.json` itself at the end, so the sampler writes
outside the record directory and the files are attached afterwards.

1. Choose the interval and the gap factor for that run and write both into the
   run's own record. This record chooses neither.
2. Before starting the runner, start the sampler as a sibling process:
   `python3 reference/rights_scale/host_conditions.py sample --out .local/host-conditions/<run>/host-conditions.jsonl --interval <S> &`
   Start it before `sui genesis` so the bring-up is covered.
3. Start the runner as usual. Do not change its arguments or workload.
4. When the runner has exited (pass or fail), send the sampler SIGTERM
   (`kill <pid>`); it flushes and exits 0. Do not leave it running.
5. Run `python3 reference/rights_scale/host_conditions.py summarize --samples .local/host-conditions/<run>/host-conditions.jsonl --interval <S> --gap-factor <N>`.
6. Copy `host-conditions.jsonl` and `host-conditions-summary.json` into the record
   directory beside `host.json`, and state in the record's own README that they
   were attached after the runner finished. Because `manifest.json` is written
   before they are copied, its `files` map does not list them; record their
   `sha256sum` in the record's README or in a manifest addendum written by whoever
   attaches them.
7. Quote the summary's measured values and detected gaps as they are. Whether a
   run's load level was acceptable is not decided by the summary or by this record.

A sampler running on the same host adds its own small load. Its cost is not
measured here.

## Existing coverage mapping

| Requirement | Classification | Evidence |
|---|---|---|
| Static host facts for an L1 run | Sufficiently covered | `host_facts()` and `host.json` in `scripts/run_rights_scale_l1_load.py`; unchanged. |
| Dynamic host conditions during a run | Not covered before this node | No committed tool read `/proc/loadavg`, `/proc/meminfo` or `/proc/uptime` over time. |
| Record-file arithmetic without a measurement | Sufficiently covered | `reference/rights_scale/measurement_gap.py` and `test_measurement_gap.py` set the shape followed here (pure functions, `UNREADABLE_INPUT` only on bad input). Not duplicated. |
| Discovery of the new tests | Sufficiently covered | The existing `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` step in `.github/workflows/protocol.yml`; no workflow change. |

## New tests and the gap each addresses

`reference/rights_scale/test_host_conditions.py` uses only literal `/proc` text, a
synthetic proc directory (`--proc`) and synthetic JSONL.

| Group | Gap addressed |
|---|---|
| `TestParsers` | Literal `/proc` text for loadavg, meminfo (kB to bytes, missing key `null`), uptime and btime, and rejection of malformed text. |
| `TestSampler` | Sample schema from a synthetic proc dir; a missing or malformed file records an error instead of raising; `count` and append behaviour; stop by event, including during the wait; one skip-guarded call on the real `/proc` that asserts only that a dict is returned. |
| `TestSummary` | Hand-computed min/median/max, per-core normalisation by affinity and the `cpu_count` fallback; minimum MemAvailable; an injected 24 480 s hole (about 6.8 h) reported once with its index, wall gap, monotonic gap and threshold; a gap exactly at the factor not reported; backward wall step counted separately; absence of any verdict key; empty and single-sample input. |
| `TestLoadSamples` / `TestCli` | Malformed JSONL, non-object lines and missing `wall_epoch_s` exit non-zero with `UNREADABLE_INPUT`; the summary file name, version string and digest; required positive arguments; the sampler CLI with a synthetic proc dir and clean exit on SIGTERM. |
| `TestModuleHygiene` | The module imports only standard library names. |

## Observed characterizations (contract-undefined, class B)

- Gap detection has no contract definition. A gap is reported as measured, with
  the monotonic gap beside it; the output does not call it a suspend or a stall.
- A sample taken while the host is suspended cannot exist, so the sampler
  can show a gap only after the host resumes.
- Load averages are the kernel's exponentially damped values, not instantaneous
  load; the min/median/max are over those reported values.
- The per-core figure divides by the affinity size seen by the sampler process
  at each sample, which may differ from the affinity of the driver or of the
  processes it starts.

## Commands and actual results

Run from the repository root with `PYTHONDONTWRITEBYTECODE=1`, Python 3.12.15 from
`/workspace/venvs/film312/bin` (the protocol workflow uses 3.12), all in the
foreground, no network. `git fetch` was not run (supervisor prohibition).

| Command | Exit | Actual result |
|---|---|---|
| `python3 -m unittest reference/rights_scale/test_host_conditions.py` | 0 | 37 tests; OK. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | 0 | 166 tests; OK (includes the 37 above). |
| `python3 scripts/check_docs_index.py` (+ `--self-test`) | 0 / 0 | docs index ok: scanned=202 indexed=167 allowlisted=35; self-test pass. |
| `python3 scripts/check_status_register.py` (+ `--self-test`) | 0 / 0 | capability register ok: paths=322 ev_ids=15 original32=32; self-test pass. |
| `python3 scripts/check_rs_profile_traceability.py` (+ `--self-test`) | 0 / 0 | blueprint=47 profile=47 expected=47; self-test pass. |
| `python3 -m py_compile` on the two new files | 0 | No output. |
| `python3 scripts/verify_runtime_architecture.py` | 0 | architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | 0 | 7 tests; OK. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | 0 | Passed. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | 101 | Not run to completion: `no matching package named bcs found` in the offline registry of this session. `runtime/` is unchanged by this node, so this is an environment limit, not a result. |
| `python3 host_conditions.py sample` then `summarize` for 3 samples at 0.2 s into a temporary directory | 0 | Smoke only; output deleted and not recorded as a measurement. |

Bootstrap, Sui/Move tests, localnet journeys, ZK setup, the Node suites and the L1
load runner are outside this node and were not run.

## Preservation

Both locked kernel blobs matched before and after the work:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (`src/lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`tests/quarantine_capacity.rs`).
`git rev-parse HEAD:reference/v0.3-rc1` is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`
before the work; `git diff --stat HEAD -- reference/v0.3-rc1 scripts .github runtime .aiops docs/tasks`
is empty after it.

## Explicit non-claims

- Thresholds are UNDETERMINED (owner: User). This record is not a measurement,
  not an L2 attempt and not an option choice. Any workload change stays with
  Astra.
- No idle, quiet or acceptable load level is defined; the summary contains no
  verdict.
- Nothing was wired into `run_rights_scale_l1_load.py` or the load driver, and no
  load, localnet or Sui process ran.
- The tests are synthetic; no host value in this record is a measurement and the
  real-host smoke call asserts no value.
- The sampler's own overhead and its accuracy against an external monitor are not
  evaluated. Linux `/proc` is required; other systems give `null` fields.
- No grade, gap, owner or operational-value change; no production, durability or
  RS-4 performance claim.

## Delivery gates

Exact-head CI for the KTX kernel verification and KIX protocol verification
workflows is not assigned to this builder and no CI result is claimed here.
