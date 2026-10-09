# audit4-audit4-plan-s5-index-f04-criteria-toss-p

Node: `audit4-audit4-plan-s5-index-f04-criteria-toss-p`. Location index only. No decision text,
no grade raise, no code, no new protocol command.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: none. Audit floor A2.
Source: KIX audit #4, finding 「DEVELOPMENT_PLAN §5 merged-document table and docs index miss #160 and #155's companions」. This node adds the #160 and #161 location rows that finding names. It does not take the rest of that heading.

This session did not commit, push, open a pull request, create or close an
issue, or comment. There is no implementation commit SHA. Local results below
are not exact-head CI. There is no KTX kernel verification run ID and no KIX
protocol verification run ID for a head that contains these files.

Observed `origin/main` and branch HEAD at session start, after
`git fetch origin main`: `a0e16328c1b4939458b2abe5b4b5167b79a15c26`.
Branch: `agent/kix-audit4-audit4-plan-s5-index-f04-criteria-toss-p`.
`git rev-list --left-right --count origin/main...HEAD` was left=0 right=0.
No rebase. The fetched `origin/main` matches the branch HEAD.

Working directory: repository root. Python 3.13.5. The workflow installs
Python 3.12. These checks use the standard library only.

## Locks

Checked before the edits and again after the checks below. Both matched.

| File | Blob (`git hash-object`) |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime docs/contracts docs/adr docs/decisions docs/operations README.md AGENTS.md` exited 0. `reference/v0.3-rc1/**` is unchanged.

## What this record points at

Locations only. The §5 table intro is unchanged. It already says the table does not judge whether a 「문장 수정 없이」 condition held. This record does not judge that either.

`git rev-parse d7549d1^{commit}` is `d7549d1473258dda617e241fff22bcbd697fbb17`. `gh pr view 160` reports `state` `MERGED`, `mergedBy.login` `BeautifulMind-JT`, and that same `mergeCommit.oid`. That login is the same account as the earlier `효력 발생(User 병합)` rows, so the #160 effect cell uses that existing wording.

`git rev-parse 31eac06^{commit}` is `31eac0637a324244aeca00e849fdb0f7c685232e`. `gh pr view 161` reports `state` `MERGED`, `mergedBy.login` `BeautifulMind-JT`, and that same `mergeCommit.oid`. The #161 row is a document-only plan. Its adoption cell is `문서 전용 계획. 채택 문장 없음.` plus the plan's own opening `Status: document-only plan.` The effect cell is `문서 전용 계획. 새 승인 아님.` It does not claim a User merge. The `.aiops` entry `toss-sandbox-conformance-plan` has `astra_auto_merge: true` and no `user_merge`. The observed login is still recorded in the `merged_by` column.

[docs/README.md](../../docs/README.md) already indexed the Toss plan and the [toss-sandbox-conformance-plan](../2026-10-09-toss-sandbox-conformance-plan/README.md) validation bullet. Those two lines are unchanged. This node adds the F04 index row and bullets for [f04-real-funds-lift-criteria](../2026-10-09-f04-real-funds-lift-criteria/README.md) and [audit3-openapi-promotion-owner-decision-record](../2026-10-09-audit3-openapi-promotion-owner-decision-record/README.md). It does not index this file.

The F04 status cell quotes `Status: proposed. This is a User decision document. It takes effect only when the User merges it` and uses `…` where the source status line continues into a relative link, the same cut the ADR-0003 index row uses. The Korean ending restates §0 and §6 of [F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md](../../docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md): adopting the criteria list does not lift the lock. The two validation bullets join each record's own scope sentence, which those files wrap across lines 3–4.

## Changed paths

| Path | Change |
|---|---|
| `docs/DEVELOPMENT_PLAN.md` | §5 location table only. Two rows after the OpenAPI promotion pointer. |
| `docs/README.md` | One F04 index row, directly before the existing Toss row. Two validation bullets. |
| `validation/2026-10-09-audit4-audit4-plan-s5-index-f04-criteria-toss-p/README.md` | This record. Not added to `docs/README.md`. |

## Commands and results

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | Exit 0. Both `a0e16328c1b4939458b2abe5b4b5167b79a15c26`. |
| `git rev-list --left-right --count origin/main...HEAD` | Exit 0. left=0 right=0. |
| `git rev-parse d7549d1^{commit}` | Exit 0. `d7549d1473258dda617e241fff22bcbd697fbb17`. |
| `git rev-parse 31eac06^{commit}` | Exit 0. `31eac0637a324244aeca00e849fdb0f7c685232e`. |
| `gh pr view 160 --json mergedBy,mergeCommit,number` | Exit 0. `mergedBy.login` `BeautifulMind-JT`. `mergeCommit.oid` `d7549d1473258dda617e241fff22bcbd697fbb17`. `number` 160. `state` `MERGED`. |
| `gh pr view 161 --json mergedBy,mergeCommit,number` | Exit 0. `mergedBy.login` `BeautifulMind-JT`. `mergeCommit.oid` `31eac0637a324244aeca00e849fdb0f7c685232e`. `number` 161. `state` `MERGED`. |
| `git hash-object` on the two locked files, before the edit | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git hash-object` on the two locked files, after the edit | Same two values. |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime docs/contracts docs/adr docs/decisions docs/operations README.md AGENTS.md` | Exit 0. |
| `git diff --check` | Exit 0. |
| `git diff --name-status origin/main` | `M` on `docs/DEVELOPMENT_PLAN.md` and `docs/README.md`. This file is untracked because this session did not commit. |
| `git diff --numstat origin/main -- docs/DEVELOPMENT_PLAN.md docs/README.md` | `2 0` and `3 0`. Added lines only. |
| `git diff --raw --no-renames origin/main HEAD` | Empty. This session did not commit, so HEAD is still `origin/main`. |
| `git ls-files --error-unmatch` on the two documents and the three validation READMEs named by the new links | Exit 0. All five paths are tracked. |
| Worktree classifier, same path rules as `.github/workflows/protocol.yml` lines 82–90 and `ktx-kernel.yml` lines 74–78 | `docs_only=true` for the two edited documents plus this `validation/*` file. A docs-only green is not full verification. |
| `python3 -I /tmp/kix-link-check.py` on the two edited documents and this file | Exit 0. `links_scanned=148 missing=0`. |
| `python3 -I /tmp/kix-verbatim-check.py` | Exit 0. `failures=0`. The two scope sentences are compared after collapsing whitespace, because each source record wraps them across lines 3–4. |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff`. |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false`. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass`. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | Exit 0. Ran 26 tests in 0.040s. OK. Regression sanity only. Not new coverage and not independent verification. |

## Not run

Rust, Move, ZK, SDK (`scripts/check_sdk_client.py`, `npm --prefix sdk run conformance`, `npm --prefix sdk run verify-compat`), and the rest of the protocol workflow. The docs-only classifier skips them, and no code changed. Hosted KTX and KIX runs for a head that contains these files do not exist yet. This session did not commit, push, or dispatch them.

## Non-claims

This record does not judge whether the #160 no-edit merge condition held, raise a grade, adopt O1, lift the real-credit lock, or call either validation record reviewed or independent. A docs-only green is not full verification. F04 values stay `DECISION_REQUIRED` and `UNDETERMINED`, as written in that document.

## Follow-up candidates

Not done here:

- A §5 row for the policy-deepening record (#163). `docs/README.md` already indexes it.
- Root `README.md` was not synced.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md` was not synced.
