# KIX Task Documents

Task documents under this directory define one bounded unit of agent work.

Repository-wide agent behavior is governed by the root `AGENTS.md`. A task document may narrow that scope further but should not duplicate the full governance rules.

## Task lifecycle

Each task uses:

- one task document;
- one task-specific branch;
- one agent session;
- one PR or explicitly documented no-change result.

Do not reuse a completed session for another task.

Once execution starts, the current task document is an immutable input to the agent. The executing agent must not edit it. If the task needs clarification or revision, stop the session and obtain an explicitly authorized task-document update outside that executing session.

## Naming

Recommended:

- document: `TASK_NNN_<SHORT_NAME>.md`
- branch: `agent/task-NNN-<short-name>`
- validation: `validation/<YYYY-MM-DD>-task-NNN-<short-name>/`
- PR title: `task(NNN): <short description>`

Historical task documents are preserved as execution records. Do not rewrite an old task document to match later implementation.

## What belongs in a task document

A task document should contain only task-specific material:

- Task ID and objective;
- requested/base SHA or base rule;
- mandatory task-specific reading;
- authorized scope;
- explicit out-of-scope items if additional restrictions are needed;
- work plan;
- acceptance criteria;
- task-specific evidence requirements;
- known dependencies or questions.

Do not copy the entire root `AGENTS.md` into every task. Reference it.

## Active / recent task documents

| ID | Document | Notes |
|----|----------|-------|
| 004 | `TASK_004_PERFORMANCE_MEASUREMENT.md` | Perf apparatus (Wave0). **Done:** docs PR #54 and implementation PR #58 merged. Exact-head CI on `28c9c13` was success (KTX `36130889407`, protocol `36130889326`). Issue #55 closed. No implementation writer is active for this task. |
| 005 | `TASK_005_MEGA_COMMERCE_PROGRAM.md` | Mega commerce program. The Wave1 charter was merged via PR #57. The Wave 2–5 implementations (#59–#62) and follow-up state machines, gates and journal (#63–#71) were merged on 2026-09-26. There is no gate-open record, and the relation to `DEVELOPMENT_PLAN.md` §1 is open (D-1/D-2 in `docs/status/MAIN_STATE_20260928.md`). Waves 6–7 are not started. Astra wave order + locks remain binding. |

Row status updated 2026-09-28 on the user's explicit instruction. The task documents themselves were not edited.

Historical task documents above remain execution records.

## Template

Use `TASK_TEMPLATE.md` as the starting structure for future task documents.
