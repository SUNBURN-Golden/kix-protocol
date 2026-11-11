# audit6-docs-index-check-validation-records

Node: `audit6-docs-index-check-validation-records`. Closes the residual
the audit5 record names (`validation/2026-10-13-audit5-plan-index-sync-b/README.md:221`
— unindexed validation records passed the check; KIX audit #6 finding 2):
`scripts/check_docs_index.py` now scans `validation/*/README.md`, so every
validation record must be the target of a markdown link in `docs/README.md`
or `docs/DEVELOPMENT_PLAN.md` or carry an explicit allowlist entry. Link
resolution stays relative to `docs/`, unchanged. The 36 records unindexed
at this node's base are allowlisted with one-line reasons rather than
retroactively indexed; the only file newly indexed is this record itself,
via one `docs/README.md` row.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`.
Source: KIX audit #6 (`/workspace/kix-run/audits/audit_6_20261014.md`,
fix_nodes entry `docs-index-check-validation-records`).

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA and no final task
head SHA yet. Local results below are not exact-head CI. There is no KTX
kernel verification run ID and no KIX protocol verification run ID for a
head that contains these files.

Observed `origin/main` and branch HEAD at session start:
`2ae8f1d0774befb0d71eb07f2e3d7454d3fcdc64` (merge of PR #188, the sibling
`audit6-rs1-state-answer-archive` node). `git fetch origin main` was not
run: the session rules forbid network and GitHub actions. The recorded SHA
is the local `origin/main` ref, which equals the task-branch HEAD; no delta
was observed and no rebase or merge was performed.
Branch: `agent/kix-audit6-docs-index-check-validation-records`.

Working directory: repository root of this worktree. Python 3.13.5 (workflow
installs 3.12); the checkers are stdlib-only.

## Locks

`git hash-object` at session start and after all edits (neither locked file
was opened for edit; `git diff --stat origin/main -- runtime/` is empty):

| File | Blob | Status |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | unchanged |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | unchanged |

`git diff --stat origin/main -- runtime/ reference/v0.3-rc1 .github
docs/tasks .aiops` produced no output: `reference/v0.3-rc1/**`,
`.aiops/`, `docs/tasks/`, the workflows and the whole `runtime/` tree are
byte-identical to the base.

## Newly indexed files

Exactly one file gained index coverage from this node — this record:

- `validation/2026-10-15-docs-index-check-validation-records/README.md`
  (row added in the `docs/README.md` `2026-10-13/14 병합 기록 색인` table,
  immediately after the rs-3b row; the section header is unchanged per the
  node spec, so the table now holds one record dated past its title).

No pre-existing validation record was linked from an index by this node.

## Allowlist entries added

36 entries, one per validation record unindexed at this node's base,
enumerated verbatim from the checker's own failure output at
`2ae8f1d` (the list below is that output, not a hand transcript). 32 carry
the reason `historical record pre-dating the validation-record scan
(KIX audit #6); not retroactively indexed`:

`2026-09-11`, `2026-09-13`, `2026-09-14`, `2026-09-14-archive`,
`2026-09-14-commerce`, `2026-09-14-foundation`, `2026-09-14-recovery`,
`2026-09-14-storage`, `2026-09-15-audit-fix`, `2026-09-15-ktx-r1-audit-fix`,
`2026-09-15-r1-observation-slots`, `2026-09-18-contract-edge-cases`,
`2026-09-19-task-002-lifecycle-precedence`,
`2026-09-19-task-003a-e4-model-schema`,
`2026-09-19-task-003b-e4-property-expansion`,
`2026-09-21-task-003c1-evidence-gates`, `2026-09-23-cp-boundary-003`,
`2026-09-26-prod-readiness-infra`, `2026-09-26-wave2-rights-issuance`,
`2026-09-26-wave3-settlement-f01-f03`,
`2026-09-26-wave4-booking-resale-admission`,
`2026-09-26-wave5-credit-f04-mock`, `2026-09-28-main-state-catchup`,
`2026-10-05-k1-e4-residual-review`,
`2026-10-09-audit3-tl-docs-plan-index-sync`,
`2026-10-09-audit4-audit4-plan-s5-index-f04-criteria-toss-p`,
`2026-10-09-audit4-tl-plan-index-register-sync`,
`2026-10-12-register-nontl-rows-sync`, `2026-10-12-rs0-review-pack`,
`2026-10-13-astra-decision-sheets-listvalues-v5-rs0`,
`2026-10-13-i12-review-pack`, `2026-10-13-offline-doc-checks-ci`.

4 carry the reason `merged audit6 fix-node record; plan/index sync row
belongs to a later index-sync node`:

`2026-10-14-audit6-plan-index-sync`, `2026-10-14-register-sync-v5-rs`,
`2026-10-14-rs-profile-revision-log-0-2`, `2026-10-14-rs1-state-answer-archive`.

The three pre-existing OpenAPI pin entries are untouched. With this node
landed the allowlist holds 39 entries, all matching scanned files.

## What changed in the checker

- `SCAN_PATTERNS` gains `validation/*/README.md` (record pointers only; the
  evidence artifacts beside a README stay out).
- `SCANNED_PREFIXES` gains `validation/`, so a resolved index link into
  `validation/` at a nonexistent target is now reported as a broken index
  link (none existed at the base; the transitional run reported only
  `not indexed` problems).
- `collect_referenced` is unchanged: `../validation/...` links from
  `docs/README.md`/`docs/DEVELOPMENT_PLAN.md` already resolve to the same
  repo-relative paths the scan produces.
- The module docstring lists the new pattern and the allowlist's new role;
  a comment above `ALLOWLIST` states the maintenance rule (a later
  index-sync node that links one of these records must drop its entry).
- `--self-test` gains one case: an injected
  `validation/SELFTEST_UNINDEXED/README.md` must be reported
  `not indexed`. The pre-existing self-test victims are unaffected
  (`docs/...` still sorts before `validation/...`).

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_docs_index.py` | `SCAN_PATTERNS` + `SCANNED_PREFIXES` extended to `validation/`; 36 allowlist entries + comment added; docstring updated; one `--self-test` case added. No check semantics, helper or output format changed. |
| `docs/README.md` | One row added in the `2026-10-13/14 병합 기록 색인` table after the rs-3b row, linking this record; status cell quotes this record's own non-claim sentence. No other row, link or sentence changed. |
| `validation/2026-10-13-docs-index-coverage-check/README.md` | One pointer bullet appended to `Follow-up candidates` (discharged: validation records are scanned since this node). Zero existing lines changed. |
| `validation/2026-10-15-docs-index-check-validation-records/README.md` | This record. |

## Existing coverage mapping (AGENTS §7)

| Requirement | Classification | Evidence |
|---|---|---|
| every scanned doc is index-linked (docs subtrees) | sufficiently covered | pre-existing `scripts/check_docs_index.py` cases; unchanged by this node |
| every `validation/*/README.md` is index-linked or allowlisted | not covered before, covered now | new scan pattern + the 36 allowlist entries + this node's index row; verified by the transitional and final runs below |
| an unindexed validation record is detected | not covered before, covered now | new `--self-test` case (`unindexed validation record validation/SELFTEST_UNINDEXED/README.md`) |
| broken index link into `validation/` is detected | partially covered before (pattern existed for docs subtrees), extended now | `SCANNED_PREFIXES` + `validation/`; exercised indirectly by the pre-existing broken-link self-test case |
| register / profile / source-map consistency | sufficiently covered, untouched | `check_status_register.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py` (+ self-tests) pass unchanged |

No new test files were added; the coverage for this node's requirement is
the checker's own scan plus its extended `--self-test`, consistent with the
sibling stdlib-checker nodes.

## Commands and results

All run from this worktree in the foreground, no network, no GitHub
actions.

| Command | Result |
|---|---|
| `git status --porcelain`, `git branch --show-current`, `git rev-parse origin/main HEAD` | Exit 0. Branch `agent/kix-audit6-docs-index-check-validation-records`; HEAD = local `origin/main` = `2ae8f1d0774befb0d71eb07f2e3d7454d3fcdc64`. `git fetch` not run (network forbidden this session). |
| `python3 scripts/check_docs_index.py` (baseline, before edits) | Exit 0. `docs index ok: scanned=67 indexed=64 allowlisted=3` — the check passes today because `validation/` is not scanned: the gap this node closes. |
| `python3 scripts/check_docs_index.py --self-test` (baseline) | Exit 0. 5 cases detected, `self-test: pass`. |
| `git hash-object` on both locked files (start) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — required values. |
| `python3 scripts/check_docs_index.py` (after `SCAN_PATTERNS`/`SCANNED_PREFIXES` edit, before allowlist) | Exit 1. Exactly 36 problems, all `not indexed: validation/<dir>/README.md` (list transcribed into the allowlist section above); no `broken index link:` and no other class. 64 records scanned, 28 already index-linked. |
| `python3 scripts/check_docs_index.py` (after allowlist, before this record) | Exit 0. `docs index ok: scanned=131 indexed=92 allowlisted=39`. |
| `python3 scripts/check_docs_index.py --self-test` (after allowlist) | Exit 0. 6 cases including `detected unindexed validation record validation/SELFTEST_UNINDEXED/README.md`; `self-test: pass`. |
| `python3 scripts/check_status_register.py` (+`--self-test`) | Exit 0. `capability register ok: paths=219 ev_ids=15 original32=32`; `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` (+`--self-test`) | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47`; `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` (+`--self-test`) | Exit 0. `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145`; `self-test: pass`. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`. |
| `python3 scripts/test_runtime_architecture.py` | Exit 0. Ran 7 tests, OK. |
| `python3 scripts/check_docs_index.py` (final, this record + index row in place) | Exit 0. `docs index ok: scanned=132 indexed=93 allowlisted=39`. |
| `python3 scripts/check_docs_index.py --self-test` (final) | Exit 0. 6 cases, `self-test: pass`. |
| `git hash-object` on both locked files (final) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` — unchanged. |
| `git diff --stat origin/main -- runtime/ reference/v0.3-rc1 .github docs/tasks .aiops` | No output. Protected paths unchanged. |
| `git diff --check` | Exit 0. |
| `git status --porcelain` (final) | ` M scripts/check_docs_index.py`; ` M docs/README.md`; ` M validation/2026-10-13-docs-index-coverage-check/README.md`; untracked `validation/2026-10-15-docs-index-check-validation-records/`. Nothing else. |

The eight checker commands are the unguarded `Stdlib offline document
checks` step of `.github/workflows/protocol.yml` — the closest local
equivalent for the touched paths; the two architecture commands mirror the
kernel workflow's architecture gate. No workflow file was edited.

CI classification note: `scripts/check_docs_index.py` is a
non-documentation path under both classifiers
(`.github/workflows/protocol.yml`, `.github/workflows/ktx-kernel.yml`),
so a pull request containing this node is **not** docs-only; hosted
exact-head runs will execute the full suites. Expected behavior; CI was
not edited to change it.

## Not run

Cargo/rustc suites under `runtime/` (no Rust source changed; the empty
`runtime/` diff is recorded above — NOT_RUN-for-cargo rather than claimed),
Move tests, localnet journeys, ZK fixtures, `bootstrap.sh`
(`.venv`/pip/npm/Sui installs; no network this session), the `sdk` suite,
and hosted KTX/KIX runs for a head containing these files: not run here.

## Contract findings

- Contract violations found: none.
- Contract-undefined characterizations found: none. The checker reports
  index coverage only; no contract, decision, status, ADR, blueprint or
  register semantics were defined or amended.

## Non-claims

This record extends a checker and its allowlist only; it retroactively
indexes no historical record, raises no evidence grade, and marks nothing
reviewed or operational. No document content beyond index links and the
two pointer bullets named under Changed paths was changed; every quoted
sentence in `docs/README.md` is copied verbatim from the record it names.
Local checker passes are not exact-head CI and not independent
verification. The checker still cannot detect a missing plan-table row
(a link-only row passes), and it does not flag a redundant allowlist entry
for a record that is also index-linked (stale-allowlist fires only for
files outside the scanned set). No real funds, real PG/bank/KYC calls,
public endpoint, Sui testnet/mainnet, R2, storage engine, new coin/TIX
module, secret or production runtime was touched or needed.

## Residuals and follow-up candidates

- Exact-head KTX kernel verification and KIX protocol verification runs
  happen in hosted CI after the supervisor commits and the PR opens; not
  observed here. This PR will run **full** verification (see CI
  classification note). Merge remains user-only (`user_merge: false`);
  record final-head CI run IDs in the PR closure report, not in a new
  commit (AGENTS §11).
- A later index-sync node that links one of the 36 allowlisted records
  from an index file must also drop its allowlist entry; the checker does
  not flag the redundancy itself. The four 2026-10-14 audit6 fix-node
  records are the most likely first candidates (their §5/index rows belong
  to that node, per the reason strings).
- The `docs/README.md` table now titled `2026-10-13/14` holds one record
  dated 2026-10-15 (this one): the spec fixed the placement and forbade a
  header rename. A later index-sync node may regroup or retitle the
  section.
- Plan-row detection (audit5 residual,
  `validation/2026-10-13-audit5-plan-index-sync-b/README.md:221-222`)
  remains open and out of scope for this node.
- The `docs/DEVELOPMENT_PLAN.md` §5 merge-table row and merge-record
  section entry for this node's own PR belong to a later index-sync node,
  same as the sibling audit6 records.
