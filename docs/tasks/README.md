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

## Template

Use `TASK_TEMPLATE.md` as the starting structure for future task documents.
