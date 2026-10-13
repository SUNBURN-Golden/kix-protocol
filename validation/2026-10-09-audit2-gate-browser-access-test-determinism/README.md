# audit2-gate-browser-access-test-determinism

Node: `audit2-gate-browser-access-test-determinism`. Test harness only.
Issue: none.
Depends on: none.
Audit floor A2. Source: KIX audit #2, the `415 != 503` flake recorded in
`validation/2026-10-08-k1-evidence-close/README.md` (commands table). That
historical file was not edited.

This session did not commit, push, open a PR, or comment. There is no
implementation commit SHA. Local results below are not exact-head CI.

## Task and base

Observed `origin/main` and branch HEAD at session start, after
`git fetch origin main`: `e2a029d8ac3af7575888dac22fc4bf173ebec232`.
Branch: `agent/kix-audit2-gate-browser-access-test-determinism`.
The task base matches current `origin/main`. No rebase and no merge from main.

Working directory: repository root. Python 3.13.5. Hosted CI uses Python 3.12.
Cargo and rustc 1.98.1, with rustfmt and clippy installed. PATH Node is
v20.19.2. An extracted Node v24.21.0 binary was used only for the SDK pin
check. `sui` and `snarkjs` are absent. `.venv` is absent. `sdk/node_modules`
is absent.

## Heads

| Name | SHA |
|---|---|
| `origin/main` | `e2a029d8ac3af7575888dac22fc4bf173ebec232` |
| Branch HEAD | `e2a029d8ac3af7575888dac22fc4bf173ebec232` (unchanged; no commit) |
| Implementation head | none |

## Changed paths

| Path | Change |
|---|---|
| `integration_gate/test_http_gate.py` | `wait_admit_idle`, waits in `test_real_responses_add_cors_only_for_the_allowed_origin`, and one characterization test. |
| `validation/2026-10-09-audit2-gate-browser-access-test-determinism/README.md` | This record. Untracked until the supervisor commits it. |

`git diff --stat origin/main` lists only the test file (55 insertions, no
deletions). `git diff -U0` has no removed lines. No assertion was weakened
or removed. `git diff --stat origin/main -- docs/contracts` is empty.
`git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks runtime`
is empty. `integration_gate/server.py` and `readiness/` are unchanged.

## Locked blobs

Checked at the unchanged HEAD before and after the edit:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`reference/v0.3-rc1/**` is byte-identical to `origin/main`.

## Existing coverage

| Requirement | Where it is already mapped |
|---|---|
| `OVERLOADED` when a slot is already held | `integration_gate/test_http_gate.py` `test_bounded_concurrency_fails_closed` and `test_overload_observation_does_not_queue`. Sufficient. Unchanged. |
| `AdmitGate` unit semantics | `readiness/test_faults.py` `test_budget_names_the_existing_limit_and_overload_does_not_queue`. Sufficient. Unchanged. |
| Response written before the admit slot is released | Not covered before this node. The new characterization test is that gap. |

The other `max_in_flight=1` tests (`test_bounded_concurrency_fails_closed`,
`test_overload_observation_does_not_queue`,
`test_preflight_does_not_take_an_admit_slot_or_advance_the_core`) hold a slot
on the client thread and release it before the next admitted call. They were
not given waits.

## New tests

`BrowserAccessTests.test_response_can_complete_while_admit_slot_is_held`
characterizes the current handler order. It is not a contract claim.

The test wraps `httpd.release_admit` so the handler blocks before the original
release. A `text/plain` POST returns 415 with `UNSUPPORTED_MEDIA_TYPE` while
`admit.view()['inFlight']` is still 1. `wait_admit_idle(httpd, timeout=0.2)`
raises `AssertionError` with text `admit slot not released`. After the event
is set, `wait_admit_idle` returns and a following `post_call` returns 200.
The event is set in `finally`.

`wait_admit_idle` polls `httpd.admit.view()['inFlight'] == 0` until a bounded
timeout (default 3 seconds, 5 ms interval) and raises
`AssertionError('admit slot not released')` on timeout. It does not sleep a
fixed delay in place of the condition.

Call sites in `test_real_responses_add_cors_only_for_the_allowed_origin`, all
with `max_in_flight=1`:

- after each request inside `paired` (the 400 pair and the 415 pair);
- between `op-miss-a` and `op-miss-b`;
- after `op-miss-b`, before `op-ok`;
- after `op-ok`, immediately before `httpd.try_admit()`.

## Loop results

Pre-fix, the test file was the `origin/main` copy.

An earlier plain loop stopped at iteration 46 because the filesystem returned
`No space left on device` while writing a per-iteration log. That was not an
assertion failure. The log files were removed and the plain loop was rerun.

| Loop | Result |
|---|---|
| Pre-fix plain, 50 iterations, stop on first failure | 50 ok, 0 fail. The historical `415 != 503` message did not recur. |
| Pre-fix contention, 4 parallel copies of that loop, each stops on first failure | Worker 1 failed iteration 1: `AssertionError: 503 != 422`. Worker 2 failed iteration 2 after 1 pass: `AssertionError: 'OVERLOADED' != 'OK'`. Worker 3 failed iteration 1: `AssertionError: 'OVERLOADED' != 'OK'`. Worker 4: 50 ok, 0 fail. |
| Post-fix plain, same single test, 50 iterations | 50 ok, 0 fail. |
| Post-fix contention, 4 parallel copies, 50 each | 4 workers, each 50 ok, 0 fail. |
| Post-fix characterization test, 50 iterations | 50 ok, 0 fail. |
| Post-fix `python3 -m unittest integration_gate.test_http_gate readiness.test_faults`, 20 sequential runs | 20 ok, 0 fail. Each run is 54 tests (53 on `origin/main`, plus the new test). The first run's summary line was `Ran 54 tests in 4.918s OK`. |

`503 != 422` is `assertEqual` on an `op-miss` status whose expected value is
422. `'OVERLOADED' != 'OK'` is `assertEqual(httpd.try_admit(), 'OK')`. Both
match a sequential client issuing the next admission while the previous
handler still holds the only slot. The historical `415 != 503` is the same
window inside `paired` (`assertEqual(status_a, status_b)` on the `text/plain`
pair). This session did not reproduce that exact message. The delayed-release
test reproduces the cause without a schedule race: the 415 body is readable
while `inFlight` is still 1.

## Commands run

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0. Both `e2a029d8ac3af7575888dac22fc4bf173ebec232`. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` before and after. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` before and after. |
| Pre-fix plain 50 and pre-fix 4-way contention | See loop results. Contention reproduced the race. |
| `python3 -m unittest` of the new characterization test and the browser-access test, once, after the edit | Exit 0. 2 tests, OK. |
| Post-fix plain 50, 4-way contention, characterization 50 | All ok. See loop results. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` ×20 | Exit 0 each time. 54 tests, OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. 20 tests, OK. |
| same for `reference/booking_resale_admission` | Exit 0. 43 tests, OK. |
| same for `reference/credit_advance_f04` | Exit 0. 20 tests, OK. |
| same for `reference/ai_delegation` | Exit 0. 22 tests, OK. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. commands=40, pin OK. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. pass. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. commands=40, productionEndpoint=false, publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. pass. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. 7 tests, OK. |
| `python3 scripts/check_sdk_client.py` with PATH Node v20.19.2 | Exit 1. `node 20.19.2 does not match toolchains.json nodeMajor 24`. |
| same command with extracted Node v24.21.0 on `PATH` | Exit 0. `sdk client pin ok: commands=40 node=24.21.0`. |
| `python3 scripts/check_sdk_client.py --self-test` with that Node 24 | Exit 0. pass. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. bcs1 3, golden_vectors 4, feature-ir 5, audit_regressions 8, schema_bound 18, feature-semantics 6, kernel lib 0, contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32, kix-types 6. Sum 128 passed, 0 failed. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `git diff --check` | Exit 0. |
| `git diff --stat origin/main` | `integration_gate/test_http_gate.py` only, 55 insertions. |
| `git diff --stat origin/main -- docs/contracts` | Empty. |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks runtime` | Empty. |

## CI

No commit and no push, so there is no exact-head workflow run. KTX kernel
verification and KIX protocol verification run IDs are absent. A skipped or
absent draft-PR check is not a pass. Local equivalents above are the evidence
this session can record.

## Contract violations

None.

## Contract-undefined characterizations

`docs/contracts/READINESS_RUNTIME.md` says the default in-flight cap is 8 and
that a request over the cap is refused with `OVERLOADED`. It does not say
whether the admit slot is released before or after the response is written.

Observed, and left unchanged: `GateHandler._local_call` admits, writes the
full response in `_send`, and calls `release_admit` in a `finally` that runs
after that write. With `max_in_flight` saturated, a sequential loopback client
that sends its next request immediately after reading a response can be
refused with `OVERLOADED`. This session does not invent a release-order rule
and does not change the server.

## Non-claims

- CORS semantics, the allowed origin, and default-off behaviour are unchanged.
- OpenAPI pins and `READINESS_RUNTIME.md` semantics are unchanged.
- No new endpoint, command, error code, or schema field.
- This is not a production-readiness, durability, or load result.
- Real-client behaviour outside this in-process loopback harness was not tested.
- Slot-release ordering in the server was not changed.
- Hosted CI on a future commit was not run.

## Uncertainty

The plain 50-iteration loop did not fail, before or after the fix. The
contention loop failed before the fix and passed after it. A pass of the
plain loop does not by itself prove the cause. The delayed-release test is
the deterministic evidence for the write-before-release order.

## Not run locally

`scripts/bootstrap.sh`, `scripts/verify_runtime.py`, `scripts/verify_commerce.py`,
`scripts/verify_canonical.py`, the storage probes, `scripts/run_localnet.py`
(including `--paid` and `--private`), `npm --prefix sdk run conformance`,
`npm --prefix sdk run verify-compat`, and the ZK steps. No Sui CLI, no
snarkjs, no `.venv`, and no `sdk/node_modules`. `cargo tree` from the KTX
workflow was not run; the workspace test and clippy commands above were.
Those steps are unchanged by this node and are covered only by hosted CI,
which does not exist for this uncommitted tree.

## Deviations from the design plan

- One extra `wait_admit_idle` after `op-miss-b` and before `op-ok`. The plan
  named four sites. This fifth site is the same write-before-release window.
  The contention failures were on the op-miss status and on `try_admit`, not
  on `op-ok`.
- The characterization test also checks the 415 error code and the helper's
  exception text. The plan's ordering checks were kept; none were dropped.
- `check_sdk_client.py` was run twice: PATH Node 20 failed the major check,
  then an extracted Node 24.21.0 passed. `npm` SDK scripts were not run.
- Exact-head GitHub Actions were not started. This session must not commit
  or push.
