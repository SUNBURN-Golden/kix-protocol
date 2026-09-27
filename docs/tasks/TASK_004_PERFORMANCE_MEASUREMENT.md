# Task 004 — Performance contract & measurement apparatus (first-bundle gap)

Issued by the KIX orchestrator on 2026-09-25 (KST) under 개발총괄 / Astra product
coding resume authorization. Immutable input for a new execution session once
implementation starts. This task authorizes harness/tests/validation/docs changes
for the measurement apparatus and a draft PR, not merge.

Writer for implementation = **DEVIN local CLI only** (`devin --print`). No Cloud
Devin, no Cursor CloudAgent for implementation, no ChatGPT, no extra paid purchase.
Independent **GROK_BUILD** exact-HEAD review is required before any merge request
is treated as ready. Executing writer must **not** modify this Task 004 markdown.

## Status

- Task ID: `004`
- Execution session: new session required (local Devin CLI)
- Task document: immutable once execution starts
- Repository-wide rules: follow root `AGENTS.md`
- Product `runtime_enabled` remains false; do not re-enable Control Plane Runtime
  workflow previously marked `disabled_manually`

## Objective

Close unfinished first-bundle gaps in the performance **contract meaning** and
**measurement apparatus** described by `docs/DEVELOPMENT_PLAN.md` §7 and
`docs/contracts/PERFORMANCE_MEASUREMENT.md`, within authorized paths only.

Primary outcome: apparatus that (a) separates outcomes in summaries, (b) distinguishes
low-load vs hot-seat vs same-command retry vs history-growth/saturation evidence,
(c) records release-mode local evidence under `.local/` without product-SLO claims,
and (d) states clearer non-claims — without inventing absolute TPS/p99/fail-rate SLOs
and without starting PostgreSQL or backend-selection work.

Secondary (only if primary fits cleanly): residual first-bundle E-4 / lifecycle
**evidence-only** gaps. No kernel semantics changes.

## Base

- Requested base SHA: `729a106add049ad1a75b90f99c00b6e0ccb8a67d` (`origin/main` at
  task creation, 2026-09-25).
- Implementation branch for the executing writer:
  `agent/task-004-perf-measurement-20260925` (create from the recorded base; do not
  reuse this docs branch for implementation commits).
- At session start, fetch `origin/main` and report any drift.
- Do not silently rebase or change the base.

## Mandatory task-specific reading

- Root `AGENTS.md`
- `docs/DEVELOPMENT_PLAN.md` §7
- `docs/contracts/PERFORMANCE_MEASUREMENT.md`
- `docs/contracts/PERFORMANCE_BASELINE_V4.md` (if present; smoke profile only)
- `runtime/crates/kix-kernel/examples/r1_perf_probe.rs`
- `runtime/crates/kix-kernel/tests/performance_harness.rs`
- `runtime/crates/kix-kernel/tests/support/perf_probe.rs`
- `validation/2026-09-16-first-batch/README.md` (prior apparatus evidence; do not
  import old numbers as current claims)
- This task document (read-only after execution starts)

## Frozen inputs (must remain unchanged)

Verify before work, after work, and on the final PR head:

- `runtime/crates/kix-kernel/src/lib.rs` → `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` → `b607996c83a119c349f1cc90469ac1ba82764e20`
- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs` → `d37ea7df55423c83bedee16bf12bdc8dd61f7cae`
- `runtime/crates/kix-kernel/tests/support/model_v4.rs` → `f020860b86933bf7511befccdb833b0c532b3629`

No production/kernel/model edits, including temporary mutations or formatting of
locked/frozen sources. No Stage2 reclaim/GC/index, R2, schema/SDK product work,
PR#11 (a) integration, blueprint #35 implementation, real money/chain, or v4 kernel
production code edits.

## Contract reminders (do not invent SLOs)

From `PERFORMANCE_MEASUREMENT.md` / DEVELOPMENT_PLAN §7:

- No approved absolute TPS / p99 / fail-rate product numbers.
- Separate **new-success** vs **business-reject** vs **same-command retry** vs
  **Capacity** vs **retained conflict**.
- Separate **scheduled-arrival latency** vs **actual service time**; do not inflate
  success with fast rejects.
- Preserve machine / toolchain / build mode / input / budget / raw samples.
- Pure v4 harness = **memory compute only**; do not claim full-system measurement.
- CI debug smoke ≠ production p99/TPS.
- Do **not** start PostgreSQL comparison or backend selection in this task.

## Known incomplete gaps (encode and close in-apparatus)

Inventory at task creation (existing smoke exists; gaps remain):

1. **Outcome-separated summaries** — CSV already stores per-call `outcome`, but
   JSON/report p99 is a mixed-result distribution; add outcome-separated goodput /
   latency summaries so mixed p99 is never labeled purchase/success p99.
2. **Load-regime distinctions** — strengthen explicit apparatus/docs/tests that
   separate low-load vs hot-seat vs same-command retry vs retained-conflict /
   history-growth / saturation (including post-first-capacity samples).
3. **Release-mode local evidence under `.local/`** — document and (where authorized)
   record a reproducible release-mode local probe under `.local/` paths without
   claiming product SLO or durable TPS; keep CI debug smoke clearly non-production.
4. **Clearer non-claims** — tighten contract/validation prose so apparatus checks
   are not misread as approved product performance, full-system measurement, or
   backend superiority.
5. **Metadata binding** — ensure recorded evidence continues to bind exact commit /
   tree, locked blobs, toolchain, OS/arch, build mode, workload, sample counts,
   budgets, rate, and raw samples.
6. **Secondary only if primary fits** — residual first-bundle E-4 / lifecycle
   evidence-only gaps with no kernel semantics changes.

## Authorized scope

Allowed change paths (measurement apparatus only):

- `runtime/crates/kix-kernel/examples/r1_perf_probe.rs`
- `runtime/crates/kix-kernel/tests/performance_harness.rs`
- `runtime/crates/kix-kernel/tests/support/perf_probe.rs`
- Narrow test-only helpers under `runtime/crates/kix-kernel/tests/support/` if
  required for outcome-separated summaries (no kernel production edits)
- `docs/contracts/PERFORMANCE_MEASUREMENT.md` (clarifying apparatus/non-claims only;
  do not invent numeric SLOs)
- Optional clarifying pointers in `docs/DEVELOPMENT_PLAN.md` §7 / related status docs
  if needed to avoid claim inflation (no scope expansion)
- New validation directory under `validation/` dated for this task (e.g.
  `validation/2026-09-25-task-004-perf-measurement/README.md`) documenting commands,
  heads, non-claims, and evidence paths
- Local evidence under `.local/` (not committed as product claims)

This Task document is bootstrap-only. The executing writer must not modify
`docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md` after execution starts.

## Additional out-of-scope constraints

Root `AGENTS.md` prohibitions remain in force. Task-specific restrictions:

- Do not edit locked/frozen blobs listed above
- No Stage2 reclaim / GC / index work
- No R2, replication, storage, log implementation
- No schema / SDK product work
- No PR#11 (a) integration
- No blueprint #35 implementation
- No real money / chain / bank / PostgreSQL comparison / backend selection
- No v4 kernel production code edits
- No `runtime_enabled=true` and do not re-enable disabled Control Plane Runtime workflow
- No main direct push / force-push / self-merge
- No inventing absolute TPS/p99/fail-rate product SLOs
- Questions/conflicts → `DECISION_REQUIRED` for 개발총괄 (do not ping JunTae)

## Work plan

### A. Existing coverage / state inventory

Before adding new tests or implementation:

- Fetch `origin/main`; record base SHA drift vs `729a106add049ad1a75b90f99c00b6e0ccb8a67d`
- Verify the four frozen blobs
- Map current `perf_probe` / `performance_harness` / `r1_perf_probe` behavior vs the
  gap list above
- Skim prior `validation/2026-09-16-first-batch/` evidence without reusing old numbers
  as current claims

### B. Apparatus completion

- Implement outcome-separated summary fields / exports (and minimal tests) so
  new-success, business-reject, retry, Capacity, and retained-conflict are not
  collapsed into a misleading success metric
- Preserve/clarify scheduled-arrival latency vs service time in reports
- Ensure low-load / hot-seat / retry / history-growth-saturation distinctions remain
  explicit in harness + docs + validation README
- Add or document release-mode local recording under `.local/` without product-SLO claims
- Clarify non-claims in `PERFORMANCE_MEASUREMENT.md` and the new validation README
- Keep CI debug smoke clearly labeled as apparatus verification only

### C. Contract discrepancy handling

Follow root `AGENTS.md` classification:

- contract-defined and matching → proceed;
- contract undefined → record characterization, do not invent semantics or SLOs;
- explicit contract violation → minimal reproduction, block merge.

Stop with `DECISION_REQUIRED` for 개발총괄 on conflicts.

## Acceptance criteria

The task is complete only when all applicable items are true:

- [ ] requested outcome is satisfied within authorized scope;
- [ ] current task document was not modified by the executing agent;
- [ ] locked/frozen blobs match required values before and after;
- [ ] existing coverage was mapped before new tests were added;
- [ ] outcome-separated summaries exist (or evidence proves already sufficient) and
      mixed p99 is not labeled as purchase/success p99;
- [ ] low-load / hot-seat / retry / saturation distinctions and non-claims are clear
      in apparatus docs/validation;
- [ ] release-mode `.local/` evidence path is documented/recorded without product SLO claims;
- [ ] relevant local tests/checks pass (`performance_harness`, related locked tests as applicable);
- [ ] exact final-head KTX CI is completed/success;
- [ ] exact final-head KIX protocol CI is completed/success;
- [ ] required evidence and non-claims are reported;
- [ ] no unresolved explicit contract violation remains on the merge path;
- [ ] independent GROK_BUILD exact-HEAD review completed before merge consideration;
- [ ] PR remains draft/unmerged until explicit human approval.

## Evidence requirements

In addition to root `AGENTS.md`, record:

- base SHA, implementation branch, final head SHA;
- frozen blob verification before/after;
- changed paths only within authorized scope;
- commands and results for `performance_harness` and any release-mode local probe;
- outcome-separated summary samples (or CSV analysis procedure) under `.local/` /
  validation README;
- both exact-head CI run IDs with head_sha / status / conclusion;
- explicit non-claims: no product TPS/p99 SLO, no full-system measurement, no PG/
  backend selection, no kernel readiness claim from this apparatus work.

## Open questions / dependencies

- Host `max_active_sessions=1`: if a local Devin session is already active when
  implementation is about to start, do not launch a second session — report
  `DECISION_REQUIRED` for 개발총괄 / Astra sequence coordination.
- Whether any residual E-4 / lifecycle evidence-only item should be included in the
  same PR is secondary and must not expand scope past the primary apparatus gaps.
- Numeric product SLOs remain intentionally undefined; do not invent them.
