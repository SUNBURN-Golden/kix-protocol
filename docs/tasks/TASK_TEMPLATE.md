# KIX Task NNN — <short title>

## Status

- Task ID: `NNN`
- Execution session: new session required
- Task document: immutable once execution starts
- Repository-wide rules: follow root `AGENTS.md`

## Objective

<One bounded outcome. State what should be learned, proven, implemented or documented.>

## Base

- Requested base SHA or base rule: `<sha or origin/main at task creation>`
- At session start, fetch `origin/main` and report any drift.
- Do not silently rebase or change the base.

## Mandatory task-specific reading

- `<path>`
- `<path>`

## Authorized scope

- <specific allowed change>
- <specific allowed test/evidence work>

## Additional out-of-scope constraints

Root `AGENTS.md` prohibitions remain in force.

Add only task-specific restrictions here:

- <restriction>
- <restriction>

## Work plan

### A. Existing coverage / state inventory

Before adding new tests or implementation, map existing coverage and repository state relevant to this task.

### B. Work

- <step>
- <step>

### C. Contract discrepancy handling

Follow root `AGENTS.md` classification:

- contract-defined and matching → proceed;
- contract undefined → record characterization, do not invent semantics;
- explicit contract violation → minimal reproduction, block merge.

## Acceptance criteria

The task is complete only when all applicable items are true:

- [ ] requested outcome is satisfied within authorized scope;
- [ ] current task document was not modified by the executing agent;
- [ ] locked blobs match required values;
- [ ] existing coverage was mapped before new tests were added;
- [ ] relevant local tests/checks pass;
- [ ] exact final-head KTX CI is completed/success;
- [ ] exact final-head KIX protocol CI is completed/success;
- [ ] required evidence and non-claims are reported;
- [ ] no unresolved explicit contract violation remains on the merge path;
- [ ] PR remains unmerged until explicit human approval.

## Evidence requirements

In addition to root `AGENTS.md`, record any task-specific evidence here:

- <evidence>
- <evidence>

## Open questions / dependencies

- <question or none>
