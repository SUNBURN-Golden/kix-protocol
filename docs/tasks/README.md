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
- branch: `agent/task-NNN-<short-name>` (program mode tasks use `astra/<task id>`; see `AGENTS.md`)
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
| 005 | `TASK_005_MEGA_COMMERCE_PROGRAM.md` | Historical charter and Wave 2–5 delivery record (#57, #59–#71). D-1~D-3 (#73) added Track P and opened Wave 6. [Roadmap R-7/R-8](../decisions/PROGRAM_ROADMAP_20260930.md) recognizes commerce #1 and #3–#12 as approved stub/mock/loopback deliveries; #13 CI followed the gate. Wave 7 opens only after commerce `w6a-evidence` merges; the #3 marketing stub is not contract integration. Protocol `wave7-marketing-contracts` remains pending external evidence and a separate plan revision. Astra order, audits and locks remain binding; this is not Wave/program completion. |

Row pointers synchronized with the approved roadmap for `roadmap-sync`. Current input: [.aiops/program.json](../../.aiops/program.json); this Mac node has no canonical dependencies. Conditional candidate adoption remains separate (development plan §17). The task documents themselves were not edited; Mac implementation checkpoints do not establish legacy DONE or post-merge proof.

Historical task documents above remain execution records.

## Template

Use `TASK_TEMPLATE.md` as the starting structure for future task documents.
