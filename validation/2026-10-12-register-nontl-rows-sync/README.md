# register-nontl-rows-sync

Node: `plan-register-nontl-rows-sync`. Location index sync of the non-TL rows
in `docs/status/CURRENT_CAPABILITY_REGISTER.md` plus a new stdlib checker.
No decision text, no grade raise, no reviewed/operational claim, no code
change to any shipped surface, no new protocol command.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2.
Source: KIX planner run 1791773087 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results below
are not exact-head CI. There is no KTX kernel verification run ID and no KIX
protocol verification run ID for a head that contains these files.

Observed `origin/main` and branch HEAD at session start:
`3ce6e4975b7f439d67482451bb47a22c940add26` (merge of PR #166).
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which equals
the task-branch HEAD (`git rev-list --left-right --count` was not needed;
`git status -sb` shows the branch tracks `origin/main` with no divergence).
Branch: `agent/kix-plan-register-nontl-rows-sync`.

Working directory: repository root of this worktree. Python 3.13.5 (workflow
installs 3.12), rustc/cargo 1.98.1 (matches `rust-toolchain.toml`), node
20.19.2 (toolchains.json pins nodeMajor 24 — see Not run).

## Locks

`git hash-object` after all edits (the files were never opened for edit;
`git diff --quiet origin/main -- runtime/` exits 0):

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks runtime`
exited 0.

## What this record points at

Locations only. A third sync-base line in
[the register](../../docs/status/CURRENT_CAPABILITY_REGISTER.md) names
`3ce6e4975b7f439d67482451bb47a22c940add26` (2026-10-12) for: EV-SET, EV-BRA,
EV-CREDIT, EV-GATE, EV-READY source/fixture lists; original32 E01 and F04 gap
pointers; Track K rows K1, K2, K3, K4, K(a); Track P rows Wave2–Wave5,
catalogue/gate/readiness, AI delegation; RS-0 and RS-1; and the two
read-model rows of the Finance/protocol table. Rows not moved keep their
earlier bases (`eb14da2a…`, `5e20a467…`, or the 2026-10-06 `2554173`
snapshot). `k-stage2-v5-impl`, `read-model-reference` and `rs-1` are recorded
as not merged / DECISION_REQUIRED. No evidence grade was raised; the
operational count stays 0; every "not covered" cell still says so.

`docs/README.md` lines that state the register's sync bases now include the
2026-10-12 base for the non-TL rows.

`scripts/check_status_register.py` is new: stdlib only, checks that every
repo path named in backticks or markdown links of the register exists
(brace expansion, `:NNN` strip, glob patterns, unique-suffix resolution for
non-root-relative fragments, ambiguity failure on multi-match suffixes),
that every referenced `EV-*` id is defined by the evidence index, and that
each of the 32 original ids appears exactly once as a first-column row key.
`--self-test` mutates in-memory copies and requires each check to catch its
break. It is not wired into CI — see follow-ups.

## Changed paths

| Path | Change |
|---|---|
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | New sync-base line; EV index, original32, Track K/P, RS and read-model row locations; handoff paragraph. |
| `docs/README.md` | Register snapshot sentences (table cell and following paragraph). |
| `scripts/check_status_register.py` | New checker. |
| `validation/2026-10-12-register-nontl-rows-sync/README.md` | This record. Not added to `docs/README.md`. |

## Commands and results

| Command | Result |
|---|---|
| `git status -sb`, `git rev-parse HEAD`, `git rev-parse origin/main` | Exit 0. Branch tracks `origin/main`; both SHAs `3ce6e4975b7f439d67482451bb47a22c940add26`. `git fetch` not run (network forbidden this session). |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=168 ev_ids=12 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. Prints detection of the injected missing path `docs/status/NO_SUCH_FILE_9f3a.md`, undefined `EV-XXX`, dropped E01 row (count 0), duplicated E01 row (count 2); `self-test: pass`. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. Ran 58 tests, OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0. Ran 22 tests, OK. |
| same for `reference/booking_resale_admission` | Exit 0. Ran 47 tests, OK. |
| same for `reference/credit_advance_f04` | Exit 0. Ran 26 tests, OK. |
| same for `reference/ai_delegation` | Exit 0. Ran 22 tests, OK. |
| same for `reference/token_reward` | Exit 0. Ran 61 tests, OK. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `commands=84 core=40 fsm=44`, sha256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`, gitBlob `619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `commands=84 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. Ran 7 tests, OK. |
| `cargo fmt --all -- --check` (in `runtime/`) | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 78 tests passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 128 tests passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `git hash-object` on the two locked files | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values. |
| `git diff --check` | Exit 0. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks runtime` | Exit 0. Protected paths unchanged. |
| `git status --short` / `git diff --name-only origin/main` | Modified: `docs/README.md`, `docs/status/CURRENT_CAPABILITY_REGISTER.md`. Untracked: `scripts/check_status_register.py`, `validation/2026-10-12-register-nontl-rows-sync/`. Nothing else. |

## Attempted but environment-blocked

| Command | Result |
|---|---|
| `python3 scripts/check_sdk_client.py` and `--self-test` | Exit 1 before checking: `node 20.19.2 does not match toolchains.json nodeMajor 24`. Environment gate, unrelated to this change. |
| `npm --prefix sdk run conformance` | Fails under node 20: `ERR_UNKNOWN_FILE_EXTENSION` importing `../src/client.ts` (the suite needs node 24 type stripping). |
| `npm --prefix sdk run verify-compat` | Same class of failure under node 20. |

## Not run

`scripts/bootstrap.sh` outputs (`.venv` steps: `verify_runtime.py`,
`verify_commerce.py`, `verify_canonical.py`, storage probes, localnet
journeys, ZK fixtures): the script pins Python 3.12 and node 24 and performs
pip/npm/Sui installs — this session has Python 3.13.5, node 20.19.2 and no
network. Move package tests, `reference/v0.3-rc1` client vitest suites, and
hosted KTX/KIX runs for a head containing these files: not run here.

CI classification note: `scripts/check_status_register.py` is a
non-documentation path under both classifiers, so this change is **not**
docs-only; hosted exact-head runs will execute the full suites.

## Non-claims

This record raises no evidence grade, marks nothing reviewed or operational,
and keeps the operational count at 0. Every register cell that lacked
executed evidence still says `not covered` or the same partial wording; the
new pointers name merged documents, mock sources and test files only. No
decision text was adopted by this change; merged "proposal" documents are
cited as records with their own stated conditions. The new checker is a
convenience check, not a contract gate: it is not wired into CI. Local suite
passes are not exact-head CI and are not independent verification.

## Follow-up candidates

- Wire `scripts/check_status_register.py` into a suitable CI step (follow-up
  candidate only; not done here).
- The `TL-L / TL-5` register row still names no source although
  `docs/decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md` merged in
  PR #166 at this base. Re-pointing TL rows is outside this node's scope; a
  TL-row sync can pick it up.
- Bare-filename register tokens (e.g. `README.md`, `test_canonical_encoding.py`)
  are checked as "exists somewhere in the tree"; a stricter root-relative
  wording pass would need the register's fragment cells rewritten to full
  paths.
