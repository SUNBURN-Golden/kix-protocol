# audit8-loop-node-canonical-crosswalk

Node: `audit8-loop-node-canonical-crosswalk`. Source: KIX audit #8 (`/workspace/kix-run/audits/audit_8_20261017.md`), finding 6.
Adds a textual crosswalk, `docs/status/LOOP_NODE_CROSSWALK.md`, from merged loop-proposed nodes to the canonical `.aiops/program.json` nodes whose spec text they overlap. It counts no loop work toward any canonical node; that question stays `DECISION_REQUIRED · Astra`. No test, code, script, CI or `.aiops/` change, no grade change.
Issue: none. Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not a program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment.
There is no implementation commit SHA and no final task head SHA. Local results below are not
exact-head CI. Exact-head CI for the final head is not recorded in the commit (AGENTS §11); it
belongs in the PR closure report.

Observed `origin/main` and branch HEAD at session start: `85acc3399a23e87ee4092693840c4e0a620867a0`
(merge of PR #209). `git fetch origin main` ran and left it unchanged (no delta).
`git rev-parse HEAD:.aiops/program.json` = `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` =
`69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
`b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `reference/v0.3-rc1/**` is untouched.

## What changed

- `docs/status/LOOP_NODE_CROSSWALK.md`: 18 rows, one per validation record that says "not in `.aiops/program.json`" (PRs #167-#171, #173-#175, #194, #196, #199-#206). Each row has PR, merge commit, plan-* id, quoted overlapping spec phrase(s), the canonical node's declared `depends_on` with a merged / not determinable cell per dependency, and the fixed cell "does not complete or start the canonical node". Section 2 accounts for #195, #197, #198, #172 and #207-#209.
- `docs/README.md`: one index bullet.

## Changed paths

- `docs/status/LOOP_NODE_CROSSWALK.md`
- `docs/README.md`
- `validation/2026-10-18-audit8-loop-node-canonical-crosswalk/README.md` (this file)

## Existing coverage mapping (AGENTS §7)

| Requirement | Coverage | Evidence |
|---|---|---|
| Doc indexed | covered by the checker | `scripts/check_docs_index.py` |
| Cited PRs, merge commits, node ids, spec phrases, depends_on | not covered by any repository checker | throwaway script outside the repo (`/tmp/ks/`), results below |
| Counting question | not decidable by a builder | left as `DECISION_REQUIRED · Astra` |

No test, script or checker was added.

## Contract findings (AGENTS §8)

- A: none needed.
- B: whether loop work counts toward a canonical node is undefined; recorded as open, not decided.
- C: none.

## Not run

- `cargo`, clippy, fmt, Move, ZK, localnet, Node and SDK suites: NOT_RUN, docs-only change.
- Exact-head CI: not available before commit. Every changed path is `docs/*` or `validation/*`, so hosted runs classify as docs-only and skip the heavy steps; that green result is not full verification.

## Non-claims

- "Overlap" is textual only; no row says any acceptance clause is met.
- A merged cell is a branch-name observation in first-parent history, not a node acceptance; "not determinable" does not mean unmerged.
- No merge-authority or merger-identity statement; no grade or count change.

## Residuals

- #195 has no merge or record in this tree. #197 and #198 cite audit #7 and carry no such phrase, so they have no row.
- PR #191 and the parallel `plan-booking-resale-admission-seeded-property` branch are unmerged; a later sync adds rows.
- Rows for #169, #170, #173 and #174 name no canonical node: the builder found no honest exact phrase.
- Merged-ness is derived from branch names only; GitHub was not read.
