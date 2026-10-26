# Perf harness map partial closure — local builder validation

Builder-authored evidence only; not non-author A2 review, acceptance, capability increase or merge readiness.

## Basis

Node: `plan-plan-perf-harness-map-partial-closure`; planner run `1792990860`.
The immutable task input is the supervisor-provided node and design plan in this session. There is no issue or current task document under `docs/tasks/` for this node. `docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md` was read as historical context, not this node's authorization. This is not ASTRA program mode.

Observed cached `origin/main`, starting task HEAD, implementation-base HEAD and final local HEAD: `a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4`.
Branch: `agent/kix-plan-plan-perf-harness-map-partial-closure`.
Local base/HEAD delta: zero. Live-main freshness and delta are unverified: the supervisor prohibited network actions, so `git fetch origin main` was not run. No base change occurred. Implementation is an uncommitted working-tree patch; the supervisor will establish the committed final task head.

Locked blob verification before and after tests:

| Path | Before | After |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Complete changed-path list:

- `runtime/crates/kix-kernel/tests/performance_harness.rs`: seven new tests and one private scalar JSON lookup helper; existing tests unchanged.
- `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`: seven row citations/gaps, three status promotions, counts and characterization notes; original basis retained.
- `validation/2026-10-26-plan-perf-harness-map-partial-closure/README.md`: this record.

No probe, example, kernel, contract, checker, CI, task document, `.aiops/` or `reference/v0.3-rc1/` changes.

## Existing coverage and new test mapping

Coverage was inspected before adding tests. All seven targets were partially covered; no target was sufficiently covered or entirely untested. Existing functions in `runtime/crates/kix-kernel/tests/performance_harness.rs`:

- `memory_probe_reports_saturation_without_recreating_kernel`: smoke counts, report Capacity positions, outcome separation and retained CSV samples; lacks targeted scalar JSON and final remaining assertions.
- `low_load_uniform_is_distinct_from_hot_seat_retry_and_saturation`: low-load and under-budget controls; no seat-wrap run.
- `outcome_summaries_do_not_label_mixed_p99_as_success`: separated outcome counts and mixed summary labels; no non-zero other case.
- `evidence_binding_records_budgets_toolchain_and_non_claims`: synthetic budget/binding fields; no full-inventory reservation or workload inventory JSON assertion.

Every new test is in that same allowed test file and calls the existing probe, which calls public kernel APIs. Expected values come from the contract/logical baseline; source inspection informed reachability and observability limits. These are not clean-room independent tests.

| Row | New test function | Gap addressed | Before → after |
|---|---|---|---|
| M-CAPACITY | `capacity_json_is_top_level_and_separate_from_business_reject` | Scalar capacity key/value and uniqueness across four workloads and controls; HotSeat business_rejected 127 versus capacity 384. | PARTIAL → COVERED |
| M-FIRST-CAPACITY-INDEX | `first_capacity_index_json_is_zero_based_or_null` | JSON 128/127 aligned with prior CSV outcome and indexed Capacity row; null for Retry/low-load/scheduled controls. | PARTIAL → COVERED |
| M-OTHER | `other_stays_zero_for_every_reachable_probe_input` | Zero other/error/observation report and JSON across eight selected cases, with absent other-error service summary. No non-zero case is reachable by the existing input shapes according to source inspection. | PARTIAL → PARTIAL |
| L-UNIFORM | `uniform_order_budget_saturates_before_seat_wrap` | 4097 calls at command_limit 8192 produce 4096 Held, one Capacity at index 4096, zero remaining and saturation phase. Seat wrap remains unobservable. | PARTIAL → PARTIAL |
| B-INVENTORY-4096 | `inventory_is_4096_seats_all_reservable_by_uniform` | inventory_seats 4096 JSON/constant, remaining 4095 after one call and zero after 4096 successful single-seat reserves. Segment boundaries remain untested. | PARTIAL → PARTIAL |
| B-CONFLICT-AT-OBSERVATION-LIMIT | `conflict_saturation_ignores_command_limit` | command_limit 1/128/512/4096 all retain 127 conflicts, then 129 Capacity outcomes in 256 calls; first index 127, 128 later samples; observation/command limit JSON. | PARTIAL → COVERED |
| C-SMOKE-V4-COUNTS | `smoke_final_remaining_matches_v4_smoke_signature` | All five historical logical count tuples plus final remaining 3968/4095/4095/4095/4095 and matching remaining JSON. | PARTIAL → PARTIAL |

Total before: `Counts: rows=42 COVERED=17 PARTIAL=20 NOT_COVERED=2 NOT_RUN=3`.
Total after: `Counts: rows=42 COVERED=20 PARTIAL=17 NOT_COVERED=2 NOT_RUN=3`.
The four checker-pinned rows are byte-identical: X-RELEASE-REPRO, X-OUTPUT-FILES and BD-RUN-VALUES stay NOT_RUN; BD-FAIL-CLOSED stays NOT_COVERED.

## Commands and actual results

Inspected `.github/workflows/ktx-kernel.yml` and the relevant stdlib/Rust blocks of `.github/workflows/protocol.yml`. The commands below are the closest local equivalents for these touched paths, plus the node's acceptance checks. Unrelated network, SDK, Move/localnet, ZK and storage workflow steps were not run; this is not a full hosted protocol-CI result.

All Cargo checks used `CARGO_NET_OFFLINE=true` and locked cached dependencies; Python checks used `PYTHONDONTWRITEBYTECODE=1`. Commands ran sequentially in foreground subprocesses, without shell background jobs. Local capture utilities/logs under `/tmp/kix-perf-harness-closure/` are not delivery files. Rustfmt targeted only the allowed harness file; subsequent workspace formatting was check-only. No test/check failures or corrective retries occurred.

| Command | Actual result |
|---|---|
| `git status --short` (before) | Empty; clean worktree. |
| `git rev-parse origin/main HEAD` | Both a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4. |
| `git branch --show-current` | agent/kix-plan-plan-perf-harness-map-partial-closure. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before/after) | Both match the locked values in the table above. |
| `rustfmt --edition 2024 runtime/crates/kix-kernel/tests/performance_harness.rs` | Exit 0; no output. |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked` | Exit 0; 11 passed, 0 failed, 0 ignored. |
| `rustc --version` | Exit 0; rustc 1.98.1 (48a229cea 2026-09-01) |
| `CARGO_NET_OFFLINE=true cargo --version` | Exit 0; cargo 1.98.1 (797e8a9bc 2026-08-05) |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0; 85 passed; 0 failed across 9 result groups (including zero-test groups). |
| `CARGO_NET_OFFLINE=true cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0; 264 passed; 0 failed across 42 result groups (including zero-test groups). |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0; Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.77s |
| `CARGO_NET_OFFLINE=true cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0; Finished `dev` profile [unoptimized + debuginfo] target(s) in 1.70s |
| `CARGO_NET_OFFLINE=true cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; No output. |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=20 PARTIAL=17 NOT_COVERED=2 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=64 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; Ran 7 tests; OK. |
| `git diff --check` | Exit 0; no output/whitespace errors. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 runtime/crates/kix-kernel/src runtime/crates/kix-kernel/tests/quarantine_capacity.rs .aiops docs/tasks docs/contracts .github scripts runtime/crates/kix-kernel/tests/support/perf_probe.rs` | Exit 0; protected and out-of-scope paths unchanged. |
| `python3 -` (compare the four pinned map rows to `git show origin/main:docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md`) | All four checker-pinned map rows byte-identical to origin/main. |

Narrow-test output excerpt (verbatim):

```text
running 11 tests
test evidence_binding_records_budgets_toolchain_and_non_claims ... ok
test low_load_uniform_is_distinct_from_hot_seat_retry_and_saturation ... ok
test conflict_saturation_ignores_command_limit ... ok
test outcome_summaries_do_not_label_mixed_p99_as_success ... ok
test first_capacity_index_json_is_zero_based_or_null ... ok
test smoke_final_remaining_matches_v4_smoke_signature ... ok
test memory_probe_reports_saturation_without_recreating_kernel ... ok
test capacity_json_is_top_level_and_separate_from_business_reject ... ok
test inventory_is_4096_seats_all_reservable_by_uniform ... ok
test uniform_order_budget_saturates_before_seat_wrap ... ok
test other_stays_zero_for_every_reachable_probe_input ... ok

test result: ok. 11 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.08s
```

Checker output excerpts (verbatim):

```text
performance evidence map ok: Counts: rows=42 COVERED=20 PARTIAL=17 NOT_COVERED=2 NOT_RUN=3
self-test: pass (2 positive controls, 66 negative fixtures; memory only)
ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=64
self-test: pass (13 negative controls)
```

## Findings, deviations and non-claims

Class A: new assertions match PERFORMANCE_MEASUREMENT and the V4-SMOKE-001 logical signature. No class C explicit contract violation or failing reproduction was found. No contract or runtime behavior changed.

Class B/source-informed characterizations and uncertainties:

- Existing workload shapes do not expose a non-zero other outcome. Valid reserve contexts progress monotonically, retries preserve inputs, and capture variants share the prefilled event with different operations. The eight-case test is representative, not an exhaustive test of all accepted numeric arguments. Adding another input shape is beyond observability, so perf_probe.rs was not changed.
- Uniform generates and passes wrapped requests to reserve, but order-budget Capacity precedes inventory validation. With ORDER_LIMIT equal to INVENTORY_SEATS, observed results cannot distinguish wrapped from invalid seat indices. The new test proves saturation only.
- All 4096 single-seat selections succeed; this cannot establish segment boundary shape. B-INVENTORY-4096 stays PARTIAL.
- C-SMOKE-V4-COUNTS stays PARTIAL because the checker requires the historical disclaimer in Gap while COVERED requires Gap none. This is a documentation/checker constraint, not a missing final-remaining assertion.

Design deviations: seven tests were implemented, following the seven detailed test specifications (the design's overview mistakenly says six). The top_level helper restricts lookups to the flat prefix before outcomes, avoiding nested matches. Map wording limits the finite other-input test claim to sampled boundaries and clarifies that wrapped requests reach reserve but not inventory validation. Supervisor restrictions supersede fetch, publication and hosted-CI steps. The session input serves as task authorization; no current task document was created or changed. There were no scope-expanding requirements or STOP conditions; DECISION_REQUIRED.md was not needed.

Explicit non-claims: debug, memory-only apparatus verification. No TPS, p99, goodput or benchmark values are reported; no latency thresholds are asserted. No release probe was run and no release-mode measurement claim is made. Existing smoke output under ignored `.local/` is debug apparatus output only. Historical V4-SMOKE-001 remains historical, not current measurement; its contract bytes and original attribution are unchanged. No production durability, chain finality, provider/bank exactly-once, legal compliance, production readiness, full-system measurement, backend selection/superiority, independent conformance, A2 review or capability-grade increase is established.

Exact-head KTX CI run ID/status/conclusion: unavailable; not requested or queried. Exact-head KIX protocol CI run ID/status/conclusion: unavailable; not requested or queried. No committed delivery head, PR, merge SHA or post-merge main CI exists for this local builder delivery. The supervisor owns committed-head CI/review/publication. No older CI result is transferred. No git commit/push/reset, GitHub action, issue/comment, branch/tag mutation or merge was performed.

Remaining uncertainty/follow-up candidates: the map's 17 PARTIAL gaps, 2 NOT_COVERED rows and 3 NOT_RUN release rows remain explicit; non-zero other, segment boundaries and seat-wrap observability require separate authorized scope. Live-main freshness, final committed-head CI and non-author A2 review remain unverified. No hardware purchase, money/paid service, credentials, live funds/provider/KYC call, endpoint, Sui execution, storage engine, coin/TIX module, policy value, protocol command or production runtime was needed.

Local builder delivery: READY. Merge-ready is not claimed.
