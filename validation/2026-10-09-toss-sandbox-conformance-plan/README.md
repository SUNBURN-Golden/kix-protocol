# toss-sandbox-conformance-plan — sandbox conformance evidence plan

Node: `toss-sandbox-conformance-plan`. Document only. No code, no new tests,
no Toss call, no credential, no new protocol command, no policy number.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: `k1-adapter-event-identity` (merged, draft 0.1, pull request #124)
and `toss-method-expansion-review` (merged 2026-10-05).
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`d7549d1473258dda617e241fff22bcbd697fbb17`.
Branch: `agent/kix-toss-sandbox-conformance-plan`.
This session did not commit, push, open a pull request, dispatch a workflow, or comment.
There is no implementation commit SHA. Local results below are not exact-head CI.
There is no KTX kernel verification run ID and no KIX protocol verification
run ID for a head that contains these files.

Locked blobs at that HEAD, before and after the documentation edit (HEAD is
unchanged; the new files are untracked):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts runtime`
was empty. `git diff --name-only origin/main` lists only `docs/README.md`,
because the two new paths are untracked. `git status --short` is the list of
changed paths.

No Toss call, no credential, and no external HTTP client command was run.
The integration-gate unittest is the repository's existing loopback suite.

## Changed paths

| Path | Change |
|---|---|
| `docs/operations/TOSS_SANDBOX_CONFORMANCE_PLAN.md` | The plan. 26 cases (TS-A1 through TS-I), the Toss answers, and where evidence is recorded. |
| `docs/README.md` | One index row beside the public-endpoint plan, and one validation bullet beside the k2 record. |
| `validation/2026-10-09-toss-sandbox-conformance-plan/README.md` | This record. |

## Commands and results

Toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)`, `cargo 1.98.1 (797e8a9bc 2026-08-05)`.
That matches `rust-toolchain.toml` and the workflow pin `1.98.1`. Python `3.13.5`.
The workflow installs Python 3.12 for the protocol job. These local Python
checks used the host 3.13.5.

The overlay filesystem had about 400MB free. A first `cargo test -p kix-kernel`
with `CARGO_TARGET_DIR=/dev/shm/kix-target` compiled and then exited 101:
`Permission denied (os error 13)` because that tmpfs is mounted `noexec`.
The fmt, test, and clippy commands below were then run with
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`,
`CARGO_INCREMENTAL=0`, and `CARGO_BUILD_JOBS=1`, and with the target directory
at `runtime/target`. Those variables drop debug info. They do not change the
sources or the warning gate. `runtime/target` was removed after the runs.
That directory is gitignored. It is not a repository change.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | both `d7549d1473258dda617e241fff22bcbd697fbb17` |
| `git hash-object` on the two locked files, before and after | both times `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts runtime` | empty |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | exit 0. 7 tests, OK |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | first attempt exit 101 (`noexec` on `/dev/shm`). Rerun exit 0 with the settings above. Lib unit tests 0. Suites: contract_edge_cases 8, contract_invariants 3, e4_state_model 12, observation_slots 11, performance_harness 4, quarantine_capacity 8, transitions 32. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0, with the same settings |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0, with the same settings. kix-bcs1 3 + golden_vectors 4, kix-feature-ir 5 + audit_regressions 8 + schema_bound 18, kix-feature-semantics 6, kernel suites as above, kix-types 6. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0, with the same settings |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | exit 0. 58 tests, OK. The runner printed one `ResourceWarning` for an unclosed file. The warning did not fail the run. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | exit 0. 20 tests, OK |
| same discover for `booking_resale_admission` | exit 0. 47 tests, OK |
| same discover for `credit_advance_f04` | exit 0. 26 tests, OK |
| same discover for `ai_delegation` | exit 0. 22 tests, OK |
| same discover for `token_reward` | exit 0. 37 tests, OK |
| `python3 scripts/check_openapi_contract.py` | exit 0. `openapi contract pin ok: commands=84 core=40 fsm=44` |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0. `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` | exit 0. `integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false` |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | exit 0. `self-test: pass` |

The workspace suite counts above were read from a second
`cargo test --manifest-path runtime/Cargo.toml --workspace --locked -- --quiet`
after the first log was truncated in the session capture. That second run
also exited 0.

A `python3 -I` check resolved every relative link in the plan, confirmed each
cited test and path name exists, counted 26 case rows, and found no `shall`.
The same check on the two added files found no credential-header spelling,
no secret-key prefix, and no 13-to-19 digit run. The OpenAPI pin command also
printed a hex digest. That digest contains a long decimal run, so the digest
is not copied into this file. A pre-existing `docs/README.md` line outside
this edit matches a naive prefix scan inside another word. That line was not
changed.

## What was not run

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. This session did not
open a pull request and did not dispatch either workflow. For a diff limited
to `docs/*` and `validation/*` other than `docs/contracts/*`, `docs/adr/*`,
`docs/PROTOCOL_MASTERPLAN_*`, the root `README.md`, and `validation/2026-09-11/*`,
both workflows classify the change as documentation-only and skip the heavy
steps. A skipped heavy job is not a full-verification pass. A skipped draft
pull request is not a pass. This local run is not that classification and
does not transfer to a later SHA.

Not run locally: `bootstrap.sh`, `scripts/verify_runtime.py`, localnet, ZK,
the storage probes, and the SDK npm steps (the workflow uses Node 24).

## Non-claims

No Toss behaviour, signature, finality, exactly-once, durability, readiness,
or legal sufficiency. No row of `FIRST_BATCH_OPEN_INPUTS.md` closed.
`새로 실입력까지 완결된 행: 0` is unchanged. No lock changed. Sandbox evidence
in the plan leaves the PG lock closed. No contract violation found. The open
Toss facts stay `UNDETERMINED` with the owners already named in the cited
documents. Product numbers and new commands stay `DECISION_REQUIRED · Astra`
inside the plan. No root decision file was added.
