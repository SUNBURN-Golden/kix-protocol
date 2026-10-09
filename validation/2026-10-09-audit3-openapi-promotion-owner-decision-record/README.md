# audit3-openapi-promotion-owner-decision-record

Node: `audit3-openapi-promotion-owner-decision-record`. Pointer record only.
No new authorisation, no contract edit, no code, no new protocol command.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2.
Source: KIX audit #3, the 2026-10-09 owner decision cited by the catalogue promotion.

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results below
are not exact-head CI. There is no KTX kernel verification run ID and no KIX
protocol verification run ID for a head that contains these files.

Observed `origin/main` and branch HEAD at session start, after
`git fetch origin main`: `1c9488499bbd954f1c14e5f571f24f3f1d976338`.
Branch: `agent/kix-audit3-openapi-promotion-owner-decision-record`.
`git rev-list --left-right --count origin/main...HEAD` was `0 0`. No rebase.

Working directory: repository root. Python 3.13.5. The workflow installs
Python 3.12. These checks use the standard library only.

## Locks

Checked before the edits and again after the checks below. Both matched.
`reference/v0.3-rc1/protocol_contract.json` was `619ae21c82ca3df5661bd3831613f15fa65225ff`.

| File | Blob (`git hash-object`) |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime docs/contracts docs/adr README.md AGENTS.md sdk integration_gate scripts` exited 0.

## What this record points at

Location only. [OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md](../../docs/decisions/OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md) quotes contiguous sentences from the merged catalogue-promotion files. It does not define DR-1 through DR-4. Those definitions are not in this repository. `git grep` for `DR-[1-4]` finds only `validation/2026-10-09-openapi-catalogue-promotion/README.md` lines 13 and 83.

PR #152 merge `d63768ddf276c60173aa2c933f4feef3449a9452` has parents `c2cde86e21a6e5ba6f24a56548636db6d0a34c6f` and `a9be88d3da4d735aabc5168c68007c062956b412`. `gh pr view 152` reports `mergedBy.login` `BeautifulMind-JT` and `mergedAt` `2026-10-09T04:13:43Z`.

[DEVELOPMENT_PLAN.md](../../docs/DEVELOPMENT_PLAN.md) §5 gains one row. The table heading says merged documents. This file is not merged, so the PR, merge-commit, and `merged_by` cells are `—`. The 효력 cell records the merge the decision cites, `#152` `d63768dd…`, and says the row is a location pointer. That is a builder choice for an unmerged file. It does not invent a PR number for this record.

[docs/README.md](../../docs/README.md) gains one row in the 2026-10-08 index table, which already holds 2026-10-09 decision rows. It does not index this file.

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md` | New pointer record. |
| `docs/README.md` | One index row. |
| `docs/DEVELOPMENT_PLAN.md` | One §5 row. |
| `validation/2026-10-09-audit3-openapi-promotion-owner-decision-record/README.md` | This record. Not added to `docs/README.md`. |

## Commands and results

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0. Both `1c9488499bbd954f1c14e5f571f24f3f1d976338`. |
| `git rev-list --left-right --count origin/main...HEAD` | Exit 0. `0 0`. |
| `git show -s --format='%H %P %an' d63768ddf276c60173aa2c933f4feef3449a9452` | Exit 0. `d63768ddf276c60173aa2c933f4feef3449a9452` parents `c2cde86e21a6e5ba6f24a56548636db6d0a34c6f a9be88d3da4d735aabc5168c68007c062956b412` author `soulbound_jt`. |
| `gh pr view 152 --repo SUNBURN-Golden/kix-protocol --json mergedBy,mergeCommit,mergedAt` | Exit 0. `mergedBy.login` `BeautifulMind-JT`. `mergeCommit.oid` `d63768ddf276c60173aa2c933f4feef3449a9452`. `mergedAt` `2026-10-09T04:13:43Z`. |
| `git hash-object` on the two locked files, before the edit | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git hash-object` on the two locked files, after the edit | Same two values. |
| `git hash-object reference/v0.3-rc1/protocol_contract.json` | `619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime docs/contracts docs/adr README.md AGENTS.md sdk integration_gate scripts` | Exit 0. |
| `git diff --check` | Exit 0. A whitespace scan of the two new files found no trailing whitespace and no tab. |
| `git diff --raw --no-renames origin/main` | Two modifications, both `docs/*`: `docs/README.md`, `docs/DEVELOPMENT_PLAN.md`. Untracked files are absent from that diff because this session did not commit. |
| Worktree classifier, same path rules as `.github/workflows/protocol.yml` lines 82–90 and `ktx-kernel.yml` lines 76–80, over that diff plus untracked additions | `docs_only=true` for the four paths in the table above. A docs-only green is not full verification. |
| `git ls-files --error-unmatch` on the artefact paths named in the pointer record | Exit 0. Each path is tracked. |
| `python3 -I /tmp/kix-verbatim-check.py` | Exit 0. `failures=0`. |
| `python3 -I /tmp/kix-link-check.py` on the four touched files | Exit 0. `links_scanned=171 external=12 missing=0`. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `commands=84 core=40 fsm=44` pin `ed827de1…` / `619ae21…`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `commands=84 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0. Ran 58 tests in 4.657s. OK. Regression sanity only. The catalogue promotion already recorded these tests. This re-run is not new coverage. |

## Not run

| Command | Why |
|---|---|
| Rust, Move, ZK, and SDK (`scripts/check_sdk_client.py`, `npm --prefix sdk run conformance`, `npm --prefix sdk run verify-compat`) | No code change. The docs-only classifier skips them |
| `bash scripts/bootstrap.sh` | Requires Python 3.12. This machine has Python 3.13.5 only |
| Exact-head GitHub Actions | No commit and no pull request in this session. Dispatch is not this session's task. CI run IDs are not available |

## Deviations

- The design plan cited the TypeScript / `bootstrap-2` sentence as validation README line 21. In the merged file that sentence is line 22. Line 21 is the loopback refusal bullet. The pointer record quotes line 22 and points at line 21 from the DR-4 artefact cell.
- The design plan abbreviated validation README line 83 with an ellipsis. The record quotes the whole contiguous paragraph, including "It names the approved fail-closed behavior.", so the substring check can match a merged sentence.
- DEVELOPMENT_PLAN §5 is headed as a table of merged documents. This file has no PR. The PR, merge-commit, and `merged_by` cells are `—`. The cited `#152` merge is written in the 효력 cell, as the plan required.

## Non-claims

This record does not adopt a recommendation, add an authorisation, name a DR definition, rename `READINESS_FSM_REFUSED`, publish stable 1.0, or lift a lock in `docs/decisions/PROGRAM_DECISIONS_20260928.md` §5. Semantic conformance stays on HOLD. A later docs-only workflow success would still not be full verification.

## Contract classification

No contract violation found. The DR option definitions are contract-undefined in this repository: the merged files cite the labels and the artefacts, and the program state decision text is absent. This record does not invent that text.

## Follow-up candidates

Not done here:

- After a supervisor merge, a separate sync can fill this record's own PR and merge SHA in DEVELOPMENT_PLAN §5. This session must not commit that SHA (AGENTS.md §11).
