# ci-wire-i12-proof-ids-check

Node: `plan-ci-wire-i12-proof-ids-check`. Wire
`scripts/check_i12_proof_ids.py` and its `--self-test` into the existing
unguarded `Stdlib offline document checks` step of
`.github/workflows/protocol.yml` (step now at lines 187-201), as the
checker's docstring and `docs/status/I12_REVIEW_PACK.md` named as a
follow-up. Additive only: two lines, no new step, `if:`, trigger, pin or
draft-skip change.
Issue: none. Depends on: none. Audit floor A2. `astra_gate: None`,
`user_merge: false`. Not an ASTRA program-mode session.
Source: KIX planner run 1792111947 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close
an issue, or comment. There is no implementation head SHA, no final task
head SHA, and no KTX kernel verification or KIX protocol verification run
ID for a head containing these files.

Observed `origin/main` = branch HEAD = `9d1ff76377fd7c65911c1fb7cb7b515a55489e2d`
(`git fetch origin main` run; unchanged). Branch
`agent/kix-plan-ci-wire-i12-proof-ids-check`.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs`
`69564b166f0c27f9af5d8422f0a466b18d74c20f`;
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
`b607996c83a119c349f1cc90469ac1ba82764e20`. Nothing under `runtime/`,
`.aiops/`, `reference/v0.3-rc1/` or `docs/tasks/` changed.

## What this change does

Two lines are appended to the step's `run:` block after
`check_docs_index.py --self-test`: `python3 scripts/check_i12_proof_ids.py`
and `python3 scripts/check_i12_proof_ids.py --self-test`. The step has no
`if:`, so it inherits only the job-level draft skip. The checker is
stdlib-only and reads only `docs/decisions/CUT_PROOF_I12_20261008.md` and
`docs/status/I12_REVIEW_PACK.md`. The checker docstring now describes the
wired state; no code change. `docs/README.md` gains one index bullet for
this record (required by `check_docs_index.py`); no allowlist entry.

Deliberately unchanged: `docs/status/I12_REVIEW_PACK.md` ("not wired"
statements at its lines 44-45 and 205-208 are dated evidence), every
earlier `validation/*` record including `2026-10-13-i12-review-pack`
(superseded by pointer only), and the register handoff note
(`CURRENT_CAPABILITY_REGISTER.md`), which names the register and
RS-profile checkers and does not claim to enumerate every wired checker.
Wiring is a mechanical id/section check; I12 stays open.

## Changed paths

| Path | Change |
|---|---|
| `.github/workflows/protocol.yml` | Two added lines in the stdlib step. |
| `scripts/check_i12_proof_ids.py` | Docstring only. |
| `docs/README.md` | One index bullet. |
| `validation/2026-10-16-ci-wire-i12-proof-ids-check/README.md` | This record. |

## Coverage mapping

- P1-P4 / A1-A10 ids and `proof §N` references: previously manual local
  runs only; now a CI step on every non-draft run (by construction).
- Docs-only execution: structural (no `if:`), not observed.

## Commands and results

| Command | Result |
|---|---|
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14`. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. Six `detected` lines, `self-test: pass`. |
| `python3 scripts/check_docs_index.py` (before) | Exit 0. `scanned=141 indexed=106 allowlisted=35`. |
| `python3 scripts/check_docs_index.py` (after), `--self-test` | Exit 0 both. `scanned=142 indexed=107 allowlisted=35` (+1/+1/unchanged); `self-test: pass`. |
| YAML parse of `protocol.yml` (`/workspace/venv-r77/bin/python`) | Parses; the step has no `if` key; run block holds 10 commands, last two are the new ones. |
| `git diff -U0 .github/workflows/protocol.yml` | One hunk `@@ -199,0 +200,2 @@`, no removed lines. |

Also exit 0 after edits: `check_status_register.py` (`paths=231 ev_ids=15
original32=32`), `check_rs_profile_traceability.py` (`47/47/47`),
`check_read_model_source_map.py` (`queries=13 anchors=128 catalogues=2
citations=145`), each with `--self-test` (`pass`); `git diff --check` exit
0; lock blobs match; `git diff --quiet origin/main -- runtime .aiops
reference/v0.3-rc1 docs/tasks docs/status
validation/2026-10-13-i12-review-pack` exit 0.

## CI classification note

`.github/workflows/protocol.yml` is a non-documentation path under the
classifier in `protocol.yml` (the `*/*) full` case) and under
`ktx-kernel.yml`, so this change is **not** docs-only. The classifiers were
read, not executed. The new lines run on docs-only PRs by construction (no
`if:` on the step); no docs-only run was observed. Exact-head KTX kernel
verification and KIX protocol verification runs are required and are not
claimed here.

## Contract findings

Contract violations: none. Contract-undefined characterizations: none.

## Non-claims

This record raises no evidence grade, marks nothing reviewed or
operational, and does not close I12. Local passes are not exact-head CI.
No funds, PG/bank/KYC, public endpoint, Sui testnet/mainnet, R2, storage
engine, secret or production runtime was touched.

## Residuals

- The step comment (lines 188-190) lists register, profile contract,
  read-model source map and doc index but not I12; left as-is to keep the
  diff at exactly two lines. Follow-up candidate.
- Any later PR that drops an id or adds a dangling `proof §N` reference
  now fails this step (intended).
- Older records cite `protocol.yml:187-199` for the step (now 187-201);
  historical, left as-is.
