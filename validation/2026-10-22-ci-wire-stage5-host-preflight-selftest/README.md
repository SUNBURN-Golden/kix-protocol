# ci-wire-stage5-host-preflight-selftest

Node: `plan-plan-ci-wire-stage5-host-preflight-selft`. Wire
`python3 scripts/check_stage5_host.py --self-test` into the existing
unguarded `Stdlib offline document checks` step of
`.github/workflows/protocol.yml` (step now at lines 203-237). The checker
(#227, `scripts/check_stage5_host.py`) was the only stdlib checker in
`scripts/` whose `--self-test` CI did not execute; its self-test injects
synthetic observations and never probes the host it runs on. The **plain**
invocation is deliberately **not** wired: it would report the CI runner's
host, which is not the pinned stage-5 host (PostgreSQL 17.11 Debian pin,
cores 0/1), so it would fail or mislead.
Issue: none. Depends on: `plan-stage5-host-preflight-checker` (#227).
Audit floor A2. `astra_gate: None`, `user_merge: False`. Not an ASTRA
program-mode session.
Source: KIX planner run 1792645030 (loop-proposed node, not in
`.aiops/program.json`).

This session did not commit, push, open a pull request, create or close
an issue, or comment. There is no implementation head SHA, no final task
head SHA, and no KTX kernel verification or KIX protocol verification
run ID for a head containing these files.

## Identity and base

- Branch: `agent/kix-plan-plan-ci-wire-stage5-host-preflight-selft`.
- Starting HEAD and cached `origin/main`:
  `8e85ef4e14c2615a94b8efca6acd60ea4fe52fb0`; the starting worktree was
  clean and `git status` reported the branch up to date with
  `origin/main`. There is no local base delta. The supervisor prohibits
  all network actions, so `git fetch origin main` was not run; remote
  freshness is unverified (the session instruction overrides AGENTS.md
  §1 step 1).
- Implementation/final task head: not assigned in this session; these
  are uncommitted working-tree changes above that starting HEAD. The
  supervisor owns commits, pushes and GitHub publication.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs`
`69564b166f0c27f9af5d8422f0a466b18d74c20f`;
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
`b607996c83a119c349f1cc90469ac1ba82764e20`. Nothing under `runtime/`,
`.aiops/`, `reference/v0.3-rc1/` or `docs/tasks/` changed.

## What this change does

One run line, `python3 scripts/check_stage5_host.py --self-test`, is
appended to the step's `run:` block after
`check_readiness_evidence_map.py --self-test`. The step has no `if:`, so
it inherits only the job-level draft skip; the self-test runs on every
non-draft execution including docs-only and same-tree-skip runs. The
plain invocation is not added, per the node specification, and the step
comment gains three lines recording why: the evaluator's `--self-test`
is wired, its plain invocation is not, because it would report this
runner's host, which is not the pinned stage-5 host. The other two
comment lines are untouched.

`docs/status/CURRENT_CAPABILITY_REGISTER.md`: the 검증·handoff checker
sentence at line 215 keeps its `f655899…` observation and the
thirteen-checker plain + `--self-test` enumeration (true at that SHA),
and now states that `scripts/check_stage5_host.py` was added to the same
step with `--self-test` only — the one checker that is self-test-only —
because the plain invocation reports the running host and the CI runner
is not the pinned stage-5 host. The
"`.github/workflows/protocol.yml`이 정본이다 / 목록은 자동으로
동기화되지 않는다" caveat is unchanged. No 위치 동기화 기준 line is
added (those belong to sync nodes).

`docs/README.md` gains one index bullet for this record (required by
`check_docs_index.py`); no allowlist entry.

Deliberately unchanged: `scripts/check_stage5_host.py` itself (its
docstring makes no wired-state claim), `docs/tasks/` (no task document
for this node), `.aiops/`, `reference/v0.3-rc1/`, `ktx-kernel.yml`,
`docs/DEVELOPMENT_PLAN.md` (location rows are post-merge sync-node
work), and every earlier `validation/*` record including
`2026-10-20-stage5-preflight` (its "runs locally only" framing describes
the preceding snapshot).

## Changed paths

| Path | Change |
|---|---|
| `.github/workflows/protocol.yml` | One added run line in the stdlib step; three added comment lines (comment correction only). |
| `docs/status/CURRENT_CAPABILITY_REGISTER.md` | Checker sentence extended to say which checkers run plain + `--self-test` and which runs `--self-test` only. |
| `docs/README.md` | One index bullet. |
| `validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md` | This record. |

## Existing coverage mapping

- Evaluator correctness (per-prerequisite PASS/FAIL, summary flags):
  previously covered only by local `--self-test` runs recorded in
  `validation/2026-10-20-stage5-preflight/README.md`; now a CI step on
  every non-draft run by construction.
- Docs-only execution of the new line: structural (no `if:`), not
  observed.
- Plain host probing in CI: intentionally not covered — see above.

## Commands and results

All commands were run in the repository root with `python3` =
`platform.python_version()` `3.13.5`, except the YAML parse, which used
`/workspace/venvs/film312/bin/python3` (3.12.15, PyYAML 6.0.3); the
default interpreter has no PyYAML (`ModuleNotFoundError`).

`python3 scripts/check_stage5_host.py --self-test` → exit 0, verbatim
output:

```
self-test: caught all prerequisites pass
self-test: caught postgres binary missing
self-test: caught postgres binary not executable
self-test: caught postgres --version exits non-zero
self-test: caught postgres --version times out
self-test: caught wrong upstream version 17.10
self-test: caught wrong version 17.110 (no substring match)
self-test: caught wrong debian revision deb13u2
self-test: caught missing debian revision
self-test: caught trailing suffix on banner
self-test: caught initdb banner mismatches independently
self-test: caught psycopg import fails
self-test: caught psycopg probe times out (error-key dict)
self-test: caught psycopg major version 2
self-test: caught psycopg major version 4
self-test: caught psycopg version unparseable
self-test: caught taskset missing from PATH
self-test: caught ss missing from PATH
self-test: caught core 1 outside affinity mask
self-test: caught affinity API unavailable
self-test: pass
```

Every command of the edited `run:` block was then executed individually
— all thirteen checkers plain and `--self-test` plus the new line
(twenty-seven commands), each exit 0:

| Command | Result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=322 ev_ids=15 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. `queries=13 anchors=128 catalogues=2 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_docs_index.py` | Exit 0. `scanned=201 indexed=166 allowlisted=35` (before this record's index bullet and file: `scanned=200 indexed=165`; the link alone produced `broken index link` until this file existed). |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14`. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0. `rows=36 citations=79; MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6`. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0. `rows=23 citations=168; COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2`. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0. `rows=30 citations=179; COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2`. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0. `rows=49 citations=58; HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7`. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0. `rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0`. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0. `rows=17 citations=56; CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8`. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0. `rows=10 citations=77; TESTED=6 STOPPED=4 OPEN=0`. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0. `rows=36 citations=177; EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9`. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0. `self-test: pass`. |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0. Twenty `self-test: caught …` lines then `self-test: pass` (quoted above). |

Other verification:

| Command | Result |
|---|---|
| `git rev-parse HEAD` / `git rev-parse origin/main` | Both `8e85ef4e14c2615a94b8efca6acd60ea4fe52fb0`. |
| `git hash-object` on both locked files, before and after | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` both times. |
| `git diff -U0 .github/workflows/protocol.yml` | Two additive hunks: `@@ -204,0 +205,3 @@` (comment) and `@@ -233,0 +237 @@` (run line); no removed lines. |
| PyYAML `BaseLoader` parse of `protocol.yml` and `ktx-kernel.yml` | Both parse. The step has no `if:` key; the run block holds 27 commands; the last is the new line; no bare `check_stage5_host.py` command exists. |
| `python3 scripts/check_docs_index.py` (before edits) | Exit 0. `scanned=200 indexed=165 allowlisted=35`. |
| `git diff --check` | Exit 0, clean. |
| `git diff --quiet origin/main -- runtime .aiops reference/v0.3-rc1 docs/tasks` | Exit 0. |
| `git status --short` | Exactly the four delivery paths (three modified, one new). |
| `python3 scripts/check_stage5_host.py` (plain, recorded observation only) | Exit 1 on this builder host: `postgres`, `initdb` and `psycopg` FAIL (`file not present` / `ModuleNotFoundError`), `taskset`, `ss` and `cpu_affinity` PASS; summary `status: FAIL`, `mode: host`, `evidence_prep: true`, `acceptance_run: false`. This is why the plain line is not wired: the CI runner is not the pinned stage-5 host. |

## CI classification note

`.github/workflows/protocol.yml` is a non-documentation path under both
classifiers, so this change is **not** docs-only. The classifiers were
read, not executed. The new line runs on docs-only PRs by construction
(no `if:` on the step); no docs-only run was observed. Exact-head KTX
kernel verification and KIX protocol verification runs are required and
are not claimed here.

## Contract findings

Contract violations: none. Contract-undefined characterizations: none.

## Non-claims

This record raises no evidence grade, marks nothing reviewed or
operational, performs no provisioning and selects no option for
`k-stage5-durable-tx`. **The stage-5 acceptance run remains
DECISION_REQUIRED for the User**; wiring the self-test is not host
qualification and says nothing about the CI runner's fitness for the
pinned prerequisites. Local passes are not exact-head CI. No funds,
PG/bank/KYC, public endpoint, Sui testnet/mainnet, R2, storage engine,
secret or production runtime was touched.

## Residuals

- The register's checker list is manual and drifts: any later
  checker addition or removal must update that sentence by hand, and a
  sync node may re-anchor the observation SHA.
- Older records cite `protocol.yml` step line numbers that drift with
  each wiring (the step is now at lines 203-237); historical, left
  as-is.
- Any later PR breaking the evaluator's synthetic cases now fails this
  step (intended).
