# docs-index-coverage-check

Node: `plan-docs-index-coverage-check`. Mechanical check that active
documents are indexed, plus fixes for the current index misses. The new
stdlib-only checker `scripts/check_docs_index.py` verifies that every
regular file under the active document subtrees
(`docs/contracts/**`, `docs/decisions/**`, `docs/status/*.md`,
`docs/operations/**`, `docs/adr/**`, `docs/reviews/**`,
`docs/blueprints/**/README.md`) is the target of at least one markdown
link in `docs/README.md` or `docs/DEVELOPMENT_PLAN.md`, unless named in
its explicit inline allowlist. The check indexes nothing and approves
nothing; it reports coverage only.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`.
Source: KIX planner run 1791848082 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close
an issue, or comment. There is no implementation commit SHA. Local
results below are not exact-head CI. There is no KTX kernel verification
run ID and no KIX protocol verification run ID for a head that contains
these files.

Observed `origin/main` and branch HEAD at session start:
`3b8067d48cbda967cbf531258215c5243b96fbcd`.
`git fetch origin main` was not run: the session rules forbid network and
GitHub actions. The recorded SHA is the local `origin/main` ref, which
equals the task-branch HEAD (`git status -sb` shows the branch tracks
`origin/main` with no divergence).
Branch: `agent/kix-plan-docs-index-coverage-check`.

Working directory: repository root of this worktree. Python 3.13.5
(workflow installs 3.12), rustc/cargo 1.98.1 (matches
`rust-toolchain.toml`), node 20.19.2 (toolchains.json pins nodeMajor 24 —
see Attempted but environment-blocked).

## Locks

`git hash-object` after all edits (the files were never opened for edit;
`git diff --quiet origin/main -- runtime/` exits 0):

| File | Blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github
docs/tasks docs/contracts docs/decisions docs/status docs/adr
docs/operations docs/reviews docs/blueprints runtime` exited 0. Every
indexed document, the tasks tree, the pinned reference and the kernel
are byte-identical to the recorded base.

## What this record points at

`scripts/check_docs_index.py` is new: stdlib only, mirrors the structure
of `scripts/check_rs_profile_traceability.py`. It collects `](target)`
link targets from the two index files, resolves them relative to `docs/`
(fragments and external URLs ignored, exact-file match only), scans the
seven subtree globs, and reports three problem classes: a scanned file
no index link reaches (`not indexed`), an allowlist entry outside the
scanned set (stale allowlist), and a resolved index link into a scanned
subtree whose target does not exist (`broken index link`). The allowlist
holds only the three machine-readable OpenAPI pins under
`docs/contracts/openapi/`, which are reached through the already linked
`docs/contracts/openapi/README.md` and checked mechanically by
`check_openapi_contract.py` / `check_integration_gate_openapi.py`.
`--self-test` mutates in-memory copies and requires each check to catch
its break, including removed-index-link detection. It is not wired into
CI — that wiring is left to a later node.

Before the fix the checker reported four misses:
`docs/status/RS0_REVIEW_PACK.md`,
`docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md`,
`docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md`,
`docs/contracts/CREDIT_ADVANCE_F04.md`.

`docs/README.md` gained one dated section, `2026-10-13 색인 보정 —
위치 안내만`, with the stock location-only disclaimer and four
pointer rows (the RS-0 review pack and the three Wave 3–5 mock
contracts). No existing row, link, or sentence was changed.

`docs/DEVELOPMENT_PLAN.md` §5 gained one dated block, `병합된 문서
위치(2026-10-13, 위치 안내만)`, a six-column location table of the
post-2026-10-09 merged status documents — RS-0 review pack (#168,
`77517f0c74cd892ca299cacf987cbab64a03337d`), three-bundle decision
sheets (#169, `1eb7d7d2978950073973a43e495ec5e31c5f543e`), register
non-TL sync (#167, `ba352dfe9789af89983e9c1b1a303461ea240016`) — with
each document's own acceptance/status sentence quoted verbatim and the
효력 표기 cell fixed at `위치 포인터. 새 승인 아님.`. PR numbers and
merge commits were taken from `git log --merges --ancestry-path`; the
merge commit's second parent matches the file's own commit in each
case. `merged_by` follows every sibling row (`BeautifulMind-JT`). No
other plan line was changed.

`validation/2026-10-13-docs-index-coverage-check/README.md` is this
record.

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_docs_index.py` | New checker. |
| `docs/README.md` | One section added (`+11` lines in `git diff`). |
| `docs/DEVELOPMENT_PLAN.md` | One §5 location-table block added (`+8` lines in `git diff`). |
| `validation/2026-10-13-docs-index-coverage-check/README.md` | This record. |

## Commands and results

| Command | Result |
|---|---|
| `git status -sb`, `git rev-parse HEAD`, `git rev-parse origin/main` | Exit 0. Branch tracks `origin/main`; both SHAs `3b8067d48cbda967cbf531258215c5243b96fbcd`. `git fetch` not run (network forbidden this session). |
| `python3 scripts/check_docs_index.py` (before fix) | Exit 1. Reported `not indexed:` for `docs/status/RS0_REVIEW_PACK.md`, `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md`, `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md`, `docs/contracts/CREDIT_ADVANCE_F04.md`. |
| `python3 scripts/check_docs_index.py` (after fix) | Exit 0. `docs index ok: scanned=65 indexed=62 allowlisted=3`. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. Detected removed index link, unindexed scanned file, dropped allowlist entry, stale allowlist (scanned file removed), broken index link; `self-test: pass`. |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=170 ev_ids=12 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. `read model source map ok: queries=13 anchors=128 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14`. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. `self-test: pass`. |
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
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | Exit 0. 78 tests passed across 8 test binaries, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 0. 128 tests passed, 0 failed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 0. No warnings. |
| `git hash-object` on the two locked files | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values. |
| `git diff --check` | Exit 0. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/decisions docs/status docs/adr docs/operations docs/reviews docs/blueprints runtime` | Exit 0. Protected paths unchanged. |
| `git status --short` / `git diff --stat origin/main` | `M docs/README.md` (+11 lines), `M docs/DEVELOPMENT_PLAN.md` (+8 lines); untracked: `scripts/check_docs_index.py`, `validation/2026-10-13-docs-index-coverage-check/`. Nothing else. |

## Attempted but environment-blocked

| Command | Result |
|---|---|
| `python3 scripts/check_sdk_client.py` | Exit 1 before checking: `node 20.19.2 does not match toolchains.json nodeMajor 24`. Environment gate, unrelated to this change. |
| `python3 scripts/check_sdk_client.py --self-test` | Exit 1. Same node-version gate. |

## Not run

`scripts/bootstrap.sh` outputs (`.venv` steps: `verify_runtime.py`,
`verify_commerce.py`, `verify_canonical.py`, storage probes, localnet
journeys, ZK fixtures): the script pins Python 3.12 and node 24 and
performs pip/npm/Sui installs — this session has Python 3.13.5, node
20.19.2 and no network. `npm --prefix sdk run conformance` /
`verify-compat`, Move package tests, `reference/v0.3-rc1` client vitest
suites, and hosted KTX/KIX runs for a head containing these files: not
run here.

CI classification note: `scripts/check_docs_index.py` is a
non-documentation path under both classifiers
(`.github/workflows/protocol.yml:87`, `.github/workflows/ktx-kernel.yml`),
so a pull request containing this node is **not** docs-only; hosted
exact-head runs will execute the full suites.

## Non-claims

The checker reports index coverage only; it approves, reviews, merges
and changes nothing, and is not wired into CI — wiring is a separate
node. The index rows are location pointers: no contract, decision,
status, ADR, operation, review or blueprint document was edited, and no
document's acceptance language, status label or register grade was
altered; every quoted sentence was copied verbatim from the merged
file. The three OpenAPI pins are allowlisted, not newly indexed — they
remain covered by the linked `docs/contracts/openapi/README.md` and the
two mechanical pin checkers. Local suite passes are not exact-head CI
and are not independent verification. No code path, contract predicate,
protocol command, policy value, secret, Move/circuit/localnet artifact,
or runtime byte was added or changed. No real funds, real PG/bank/KYC
calls, public endpoints, Sui testnet/mainnet, R2, storage engine or
production runtime were touched or needed.

## Follow-up candidates

- Discharged: `scripts/check_docs_index.py` is wired into the unguarded
  `Stdlib offline document checks` step of
  `.github/workflows/protocol.yml` by node
  `audit5-docs-index-check-ci-wire` (KIX audit #5 finding 3; record at
  `validation/2026-10-13-audit5-docs-index-check-ci-wire/`). The dated
  "not wired into CI" statements above stay as historical fact.
- Discharged: `validation/*/README.md` is scanned by
  `scripts/check_docs_index.py` since node
  `audit6-docs-index-check-validation-records` (KIX audit #6 finding 2;
  record at `validation/2026-10-15-docs-index-check-validation-records/`).
  The dated coverage statements above described the checker of their day
  and stay as historical fact; records that predate the scan sit in the
  checker's allowlist with one-line reasons, not retroactively indexed.
- If a later node adds genuinely unindexable files under a scanned
  subtree (e.g. binary evidence), extend the inline allowlist with a
  reason rather than weakening the check.
