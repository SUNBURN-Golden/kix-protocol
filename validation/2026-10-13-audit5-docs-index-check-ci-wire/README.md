# audit5-docs-index-check-ci-wire

Node: `audit5-docs-index-check-ci-wire`. Wire
`scripts/check_docs_index.py` (merged by PR #173, record at
`validation/2026-10-13-docs-index-coverage-check/`) into the existing
unguarded `Stdlib offline document checks` step of
`.github/workflows/protocol.yml` — two commands appended after the
existing six — and update the two text lines that recorded it as not
wired. Additive only: no new step, no `if:` guard, no trigger, pin,
step-order or concurrency change, no edit to indexed documents or to
the checker's logic. Closes KIX audit #5 finding 3.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`.
Source: KIX audit #5 finding 3
(`/workspace/kix-run/audits/audit_5_20261013.md`, fix_nodes entry
`docs-index-check-ci-wire`).

This session did not commit, push, open a pull request, create or close
an issue, or comment. There is no implementation commit SHA and no final
task head SHA yet. Local results below are not exact-head CI. There is
no KTX kernel verification run ID and no KIX protocol verification run
ID for a head that contains these files.

Observed `origin/main` and branch HEAD at session start:
`2862f34b588e70841a57762d8ce756fd240f5e95`.
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which
equals the task-branch HEAD.
Branch: `agent/kix-audit5-docs-index-check-ci-wire`.

Working directory: repository root of this worktree. Python 3.13.5
(the checkers are stdlib-only and run on the ubuntu-24.04 image's system
`python3`; the workflow's `setup-python` installs 3.12), cargo via
`runtime/` toolchain, node 20.19.2 (toolchains.json pins nodeMajor 24 —
see Attempted but environment-blocked).

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

The `Stdlib offline document checks` step (`.github/workflows/protocol.yml`)
now runs eight commands instead of six: the two new lines
`python3 scripts/check_docs_index.py` and
`python3 scripts/check_docs_index.py --self-test` are appended after the
existing six, same 10-space indentation, inside the same `run:` block.
The step keeps **no `if:`** — it inherits only the job-level draft skip,
so it runs on every non-draft execution: docs-only PRs, full runs, main
pushes where the same-tree-skip fires, schedule and dispatch runs. The
script is stdlib-only and runs before `actions/setup-python`, so no
toolchain dependency is added. The step comment (which enumerates the
checked documents) gains "and the doc index", matching how the
read-model source map checker was wired in commit `6b7c28b`.

`scripts/check_docs_index.py`: docstring only — the "Not wired into CI;
wiring it ... is a separate node" sentence is replaced with the
wired-state wording used by the sibling checkers
(`check_status_register.py`, `check_read_model_source_map.py`). No code,
constant or behaviour change.

`validation/2026-10-13-docs-index-coverage-check/README.md`: only the
first `Follow-up candidates` bullet changes — it now records that the
wiring is discharged by this node. The dated body statements "It is not
wired into CI" stay byte-identical per AGENTS.md §6 (they were true at
that session; precedent: `offline-doc-checks-ci` left
`RS0_REVIEW_PACK.md` unchanged).

`validation/2026-10-13-audit5-docs-index-check-ci-wire/README.md` is this
record. Not added to `docs/README.md` (validation/ is outside the
checker's scan patterns, same as sibling records).

## Changed paths

| Path | Change |
|---|---|
| `.github/workflows/protocol.yml` | Two commands appended to the `Stdlib offline document checks` run block; step comment updated to name the doc index. |
| `scripts/check_docs_index.py` | Docstring only: "Not wired into CI" -> wired-into `protocol.yml` description. |
| `validation/2026-10-13-docs-index-coverage-check/README.md` | First follow-up bullet records the wiring is discharged. |
| `validation/2026-10-13-audit5-docs-index-check-ci-wire/README.md` | This record. |

## Coverage mapping

- Doc-index coverage (scanned/indexed/allowlisted, broken index links):
  previously covered only by manual local runs
  (`validation/2026-10-13-docs-index-coverage-check`); now covered
  mechanically on every non-draft protocol run.
- Docs-only execution of the step: guaranteed structurally by the
  absent `if:` — not observed by this change's own run, which classifies
  as full (see below). Recorded as a structural property, not an
  observed run.

## Commands and results

| Command | Result |
|---|---|
| `git rev-parse HEAD origin/main`, `git status --porcelain`, `git branch --show-current` | Exit 0. HEAD = `origin/main` = `2862f34b588e70841a57762d8ce756fd240f5e95` on `agent/kix-audit5-docs-index-check-ci-wire`; clean tree at start. `git fetch` not run (network forbidden this session). |
| `python3 scripts/check_docs_index.py` (before edits) | Exit 0. `docs index ok: scanned=65 indexed=62 allowlisted=3`. |
| `python3 scripts/check_docs_index.py --self-test` (before edits) | Exit 0. Detected all five mutations (removed index link, unindexed scanned file, dropped allowlist entry, stale allowlist, broken index link); `self-test: pass`. |
| `python3 scripts/check_docs_index.py` (after edits) | Exit 0. `docs index ok: scanned=65 indexed=62 allowlisted=3`. |
| `python3 scripts/check_docs_index.py --self-test` (after edits) | Exit 0. `self-test: pass`. |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=171 ev_ids=12 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. `self-test: pass`. |
| `/workspace/venv-r77/bin/python -c "yaml.safe_load(...)"` on `protocol.yml` | Exit 0. Parses; the `Stdlib offline document checks` step has no `if` key; its run block holds the eight commands in the order above. System `python3` has no `yaml` module (stdlib env, no `.venv`). |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. Ran 58 tests, `OK`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. Ran 22 tests, `OK`. |
| same for `reference/booking_resale_admission` | Exit 0. Ran 47 tests, `OK`. |
| same for `reference/credit_advance_f04` | Exit 0. Ran 26 tests, `OK`. |
| same for `reference/ai_delegation` | Exit 0. Ran 22 tests, `OK`. |
| same for `reference/token_reward` | Exit 0. Ran 61 tests, `OK`. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `commands=84 core=40 fsm=44`, sha256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`, gitBlob `619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `commands=84 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. Ran 7 tests, `OK`. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 78 tests passed, 0 failed across 9 test binaries. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 128 tests passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `git diff --check` | Exit 0. |
| `git hash-object` on the two locked files | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks runtime` | Exit 0. Protected paths unchanged. |
| `git status --short` | Modified: `.github/workflows/protocol.yml`, `scripts/check_docs_index.py`, `validation/2026-10-13-docs-index-coverage-check/README.md`. Untracked: `validation/2026-10-13-audit5-docs-index-check-ci-wire/`. Nothing else. |

## Attempted but environment-blocked

| Command | Result |
|---|---|
| `python3 scripts/check_sdk_client.py` | Exit 1 before checking: `node 20.19.2 does not match toolchains.json nodeMajor 24`. Environment gate, unrelated to this change (`sdk/` untouched). |

## Not run

`scripts/bootstrap.sh` outputs (`.venv` steps: `verify_runtime.py`,
`verify_commerce.py`, `verify_canonical.py`, storage probes, localnet
journeys, ZK fixtures): the script pins Python 3.12 and node 24 and
performs pip/npm/Sui installs — this session has Python 3.13.5, node
20.19.2 and no network. `npm --prefix sdk run conformance` /
`verify-compat`, `reference/v0.3-rc1` client vitest suites, and hosted
KTX/KIX runs for a head containing these files: not run here.

CI classification note: `.github/workflows/protocol.yml`,
`scripts/check_docs_index.py` and `validation/**` — the first two are
non-documentation paths under both classifiers
(`.github/workflows/protocol.yml`, `.github/workflows/ktx-kernel.yml`),
so this change is **not** docs-only; hosted exact-head runs will execute
the full suites including the newly wired commands.

## Contract findings

- Contract violations found: none.
- Contract-undefined characterizations found: none. The missing CI
  wiring for `check_docs_index.py` was already recorded as a follow-up
  candidate and as audit #5 finding 3; this node performs exactly that
  wiring.

## Non-claims

This record raises no evidence grade, marks nothing reviewed or
operational, and keeps the operational count at 0. Wiring the checker
into `protocol.yml` makes it a CI gate on every non-draft run, but local
passes are not exact-head CI and are not independent verification.
Docs-only execution of the step is a structural property (no `if:`), not
an observed run — the next docs-only PR exercises it. No code path,
contract predicate, protocol command, policy value, secret,
Move/circuit/localnet artifact, or runtime byte was added or changed.
No real funds, real PG/bank/KYC calls, public endpoints, Sui
testnet/mainnet, R2, storage engine or production runtime were touched
or needed.

## Remaining uncertainty and follow-ups

- Exact-head KTX kernel verification and KIX protocol verification runs
  happen in hosted CI after the supervisor commits and the PR opens;
  not observed here. Merge remains user-only (`user_merge: false`).
- No new follow-up candidates. The "wire the checker into CI" follow-up
  from `validation/2026-10-13-docs-index-coverage-check` is discharged
  here; dated packs keep their historical wording by design.
