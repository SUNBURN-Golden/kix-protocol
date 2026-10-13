# offline-doc-checks-ci

Node: `plan-offline-doc-checks-ci`. Wire the two stdlib documentation
checkers — `scripts/check_status_register.py` and
`scripts/check_rs_profile_traceability.py`, each plus its `--self-test` —
into `.github/workflows/protocol.yml` as one step with no `docs_only` or
verified-tree guard, and update the three text lines that declared them
"not wired into CI". Additive only: no existing step, pin, `if:` guard,
trigger or draft-skip behavior changed. No new protocol command, no
policy value, no runtime change.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2.
Source: KIX planner run 1791848082 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close
an issue, or comment. There is no implementation commit SHA and no final
task head SHA yet. Local results below are not exact-head CI. There is
no KTX kernel verification run ID and no KIX protocol verification run
ID for a head that contains these files.

Observed `origin/main` and branch HEAD at session start:
`1eb7d7d2978950073973a43e495ec5e31c5f543e` (merge of PR #169).
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which
equals the task-branch HEAD.
Branch: `agent/kix-plan-offline-doc-checks-ci`.

Working directory: repository root of this worktree. Python 3.13.5
(workflow installs 3.12), cargo via `runtime/` toolchain, node 20.19.2
(toolchains.json pins nodeMajor 24 — see Attempted but
environment-blocked).

## Locks

`git hash-object` before and after all edits (the files were never
opened for edit; `git diff --quiet origin/main -- runtime/` exits 0):

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks runtime`
exited 0. The only `.github` change is `protocol.yml` itself.

## What this change does

One new step `Capability register and rights-scale traceability` in
`.github/workflows/protocol.yml`, placed between the `verified` tree-lookup
step and `actions/setup-python`. It has **no `if:`** — it inherits only
the job-level draft skip (`if:` on line 27), so it runs on every
non-draft execution: docs-only PRs, full runs, main pushes where the
same-tree-skip fires, schedule and dispatch runs. Both scripts are
stdlib-only, so the step uses the ubuntu-24.04 image's system `python3`
and needs neither `setup-python` nor `.venv`. Multi-line `run:` keeps the
default `bash -e` fail-fast convention, matching the existing
multi-command steps.

The step is deliberately unguarded because the capability register and
the RS profile contract are documents: a register-sync PR is exactly the
`docs_only=true` case, and every guarded step would skip it. Placing the
step before `setup-python` also keeps docs-only runs free of any
toolchain setup.

Docstring updates record the wiring in both scripts, and the register's
living `검증·handoff` note replaces `(stdlib만, CI 미연결은 후속 후보)`
with the wired state. Dated evidence that recorded "not wired" as
historical truth (`docs/status/RS0_REVIEW_PACK.md`,
`docs/status/MAIN_STATE_20260928.md`, earlier `validation/*` READMEs) is
left byte-identical per AGENTS.md §6.

## Changed paths

| Path | Change |
|---|---|
| `.github/workflows/protocol.yml` | New unguarded step running the four checker commands; step index 3 of 29. |
| `scripts/check_status_register.py` | Docstring only: "Not wired into CI" -> wired-into `protocol.yml` description. |
| `scripts/check_rs_profile_traceability.py` | Docstring only: same replacement. |
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | `검증·handoff` note records the CI wiring for both checkers. |
| `validation/2026-10-13-offline-doc-checks-ci/README.md` | This record. Not added to `docs/README.md`. |

## Coverage mapping

- Register path/EV-id/original32 checks: previously covered only by
  manual local runs (`validation/2026-10-12-register-nontl-rows-sync`);
  now covered mechanically on every non-draft protocol run.
- RS blueprint/profile id traceability: previously covered only by manual
  local runs (`validation/2026-10-12-rs0-review-pack`); same.
- Docs-only execution of the new step: guaranteed structurally by the
  absent `if:` — not observed by this change's own run, which classifies
  as full (see below). Recorded as a structural property, not an
  observed run.

## Commands and results

| Command | Result |
|---|---|
| `git rev-parse HEAD origin/main`, `git status --short` | Exit 0. Both `1eb7d7d2978950073973a43e495ec5e31c5f543e`; clean tree at start. `git fetch` not run (network forbidden this session). |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=170 ev_ids=12 original32=32` (paths count rose 168->170: the register now names `scripts/check_rs_profile_traceability.py` and `.github/workflows/protocol.yml` in the handoff note). |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. Detects injected missing path, undefined `EV-XXX`, dropped E01 row, duplicated E01 row; `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. Detects all seven injected mutations (removed/duplicated ids on both sides, extra ids); `self-test: pass`. |
| `/workspace/venv-r77/bin/python -c "yaml.safe_load(...)"` on `protocol.yml` | Exit 0. Parses; new step is index 3 of 29 with no `if` key; run block contains the four commands in order. System `python3` has no `yaml` module (stdlib env, no `.venv`). |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. `OK`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. `OK`. |
| same for `reference/booking_resale_admission` | Exit 0. `OK`. |
| same for `reference/credit_advance_f04` | Exit 0. `OK`. |
| same for `reference/ai_delegation` | Exit 0. `OK`. |
| same for `reference/token_reward` | Exit 0. `OK`. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `commands=84 core=40 fsm=44`, sha256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`, gitBlob `619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `commands=84 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. Ran 7 tests, `OK`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 78 tests passed, 0 failed across 9 test binaries. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 128 tests passed, 0 failed. |
| `git diff --check` | Exit 0. |
| `git hash-object` on the two locked files | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks runtime` | Exit 0. Protected paths unchanged. |
| `git status --short` | Modified: `.github/workflows/protocol.yml`, `docs/status/CURRENT_CAPABILITY_REGISTER.md`, `scripts/check_status_register.py`, `scripts/check_rs_profile_traceability.py`. Untracked: `validation/2026-10-13-offline-doc-checks-ci/`. Nothing else. |

## Attempted but environment-blocked

| Command | Result |
|---|---|
| `python3 scripts/check_sdk_client.py` | Exit 1 before checking: `node 20.19.2 does not match toolchains.json nodeMajor 24`. Environment gate, unrelated to this change. |
| `npm --prefix sdk run conformance` | Exit 1 under node 20 (`ERR_TEST_FAILURE`); the suite needs node 24 type stripping. |

## Not run

`scripts/bootstrap.sh` outputs (`.venv` steps: `verify_runtime.py`,
`verify_commerce.py`, `verify_canonical.py`, storage probes, localnet
journeys, ZK fixtures): the script pins Python 3.12 and node 24 and
performs pip/npm/Sui installs — this session has Python 3.13.5, node
20.19.2 and no network. Hosted KTX/KIX runs for a head containing these
files: not run here.

CI classification note: `.github/workflows/protocol.yml` and
`scripts/*.py` are non-documentation paths under both classifiers, so
this change is **not** docs-only; hosted exact-head runs will execute
the full suites including the new step.

## Contract findings

- Contract violations found: none.
- Contract-undefined characterizations found: none. The pre-existing
  absence of CI wiring for the two checkers was already recorded as a
  follow-up candidate; this node performs exactly that wiring.

## Non-claims

This record raises no evidence grade, marks nothing reviewed or
operational, and keeps the operational count at 0. Wiring the checkers
into `protocol.yml` makes them a CI gate on every non-draft run, but
local passes are not exact-head CI and are not independent verification.
Docs-only execution of the step is a structural property (no `if:`), not
an observed run — the next docs-only PR exercises it. Nothing here
certifies durability, performance, or production readiness.

## Follow-up candidates

- None new from this node. The earlier "wire the checkers into CI"
  follow-up is discharged here; dated packs keep their historical
  wording by design.
