# audit7-docs-index-allowlist-prune

Node: `audit7-docs-index-allowlist-prune`. Drop four now-indexed audit6 records from the
`scripts/check_docs_index.py` `ALLOWLIST` and make the checker report an allowlisted entry that an
index link also reaches. Source: `/workspace/kix-run/audits/audit_7_20261016.md`, finding 6.
This record removes four allowlist entries and adds one checker rule; it retroactively indexes nothing, raises no evidence grade, and marks nothing reviewed or operational.
Issue: none. `docs/tasks/` has no file for this node. Depends on: none. Audit floor A2.
`astra_gate: None`, `user_merge: false`. Not a program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment.
There is no implementation commit SHA and no final task head SHA. Local results below are not
exact-head CI. Exact-head CI for the final head is not recorded in the commit (AGENTS §11); it
belongs in the PR closure report.

Observed `origin/main` and branch HEAD at session start: `2497471dfab21ffd68d600e6ce508e5d6d65bae5`
(merge of PR #197). `git fetch origin main` ran and left it unchanged (no delta).

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` =
`69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
`b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `reference/v0.3-rc1/**`, `.github/`,
`.aiops/`, `docs/tasks/` and `runtime/` are untouched.

## Removed entries

`docs/DEVELOPMENT_PLAN.md` lines 175-178 already link these four records, so their allowlist entries
were redundant:

- `validation/2026-10-14-audit6-plan-index-sync/README.md`
- `validation/2026-10-14-register-sync-v5-rs/README.md`
- `validation/2026-10-14-rs-profile-revision-log-0-2/README.md`
- `validation/2026-10-14-rs1-state-answer-archive/README.md`

The records themselves are unchanged. The 35 remaining entries (3 OpenAPI pins, 32 historical
records) are not linked from either index file.

## What changed in the checker

- `find_problems` reports `allowlisted but indexed: <path>` for every entry in `allowlist & referenced`.
- `--self-test` has one new case, `allowlisted entry also index-linked`, that injects the first
  allowlist entry into the referenced set and requires the marker.
- The module docstring and the comment above `ALLOWLIST` name the new check.
- The four entries above are removed. The prune and the rule land together: the unmodified-tree guard
  of `--self-test` fails otherwise.

Counts (`scanned` / `indexed` / `allowlisted`):

| State | scanned | indexed | allowlisted |
|---|---|---|---|
| Baseline (base `2497471`) | 140 | 105 | 39 |
| Transitional (rule added, no prune) | exit 1 with exactly four `allowlisted but indexed:` lines, one per removed path | | |
| Final (this tree) | 141 | 106 | 35 |

The final scanned and indexed counts are one higher than baseline because this record is a new
scanned file and is linked from `docs/README.md`.

## Changed paths

- `scripts/check_docs_index.py`
- `docs/README.md` (one bullet linking this record)
- `validation/2026-10-16-audit7-docs-index-allowlist-prune/README.md` (this file)

## Existing coverage mapping (AGENTS §7)

| Requirement | Coverage | Evidence |
|---|---|---|
| Unindexed scanned file, dropped entry, missing scan target, broken link | sufficiently covered, unchanged | `scripts/check_docs_index.py --self-test`, first six cases |
| Redundant (allowlisted and indexed) entry detected | not covered before; covered now | new rule and new self-test case |
| New record linked from the docs index | sufficiently covered | `scripts/check_docs_index.py` |

No new test file was added. Older records that state the checker does not flag a redundant allowlist
entry (for example `validation/2026-10-15-docs-index-check-validation-records/README.md`) are
historical evidence and are left unchanged; this record supersedes that statement by pointer only.

## Commands and results

Python 3.13.5 (CI uses 3.12; the checkers use the standard library only).

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | both `2497471dfab21ffd68d600e6ce508e5d6d65bae5` |
| `git hash-object` on the two locked files | `69564b16…` and `b607996c…`, match |
| baseline `check_docs_index.py` and `--self-test` | `scanned=140 indexed=105 allowlisted=39`; self-test pass (6 cases) |
| rule added, no prune: `check_docs_index.py` | exit 1, four `allowlisted but indexed:` lines for the four paths above |
| rule added, no prune: `--self-test` | exit 1, `unmodified index already fails` (same four lines) |
| after prune, before the record: `check_docs_index.py` | `scanned=140 indexed=105 allowlisted=35` |
| after prune: `--self-test` | pass, 7 cases including `detected allowlisted entry also index-linked` |

The final-tree commands are listed in the session report, not copied here, so this record does not
claim a result before it was produced.

## Not run

`cargo` test, clippy and fmt (no Rust changed); the Move, ZK and SDK suites; `bootstrap.sh`; hosted
KTX and KIX workflow runs for a head containing these files.

## Contract findings

No contract violation found. No contract-undefined behaviour found. No locked file needed editing.

## Non-claims

This is a documentation-index consistency check only. It says nothing about whether any listed
record is correct, reviewed, merged as evidence or operational. The index sentence in
`docs/README.md` is quoted from this record by hand; the checker does not verify that it matches.
Local passes are not exact-head CI, and nothing here is `merge-ready` until both workflows are
`completed/success` on the final head. Merge is user-only.

## Residuals

The 32 historical-record allowlist entries remain preserved as evidence and are still unindexed.
