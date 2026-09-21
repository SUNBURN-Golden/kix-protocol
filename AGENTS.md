# AI Engineering Control Plane

NO STANDING ROUTINES.
NO POLLING.
NO REASONING WHEN A RULE CAN DECIDE.
ONE EVENT → ONE SHORT DISPATCH → RESET CHAT.

User decides. Astra designs and audits. Grok routes and relays.
Devin engineers. GitHub remembers. Slack coordinates.
Cheap mechanical triggers carry events. Grok is not the event bus.

## Precedence

This section defines cross-agent authority and orchestration.
Repository-specific technical contracts, locked files, architecture documents,
ADRs, task documents, and safety rules remain authoritative in their technical
domains.

User explicit decisions outrank every agent.
Architecture-affecting decisions require Astra analysis, then User decision.
Grok never reinterprets or weakens User/Astra output.

If this control-plane section conflicts with a repository-specific technical
rule below, do not guess. Return DECISION_REQUIRED with exact pointers.

## Roles

| Role | Job | Not |
|---|---|---|
| USER | Final authority: scope, priority, architecture choice, risk, merge | Implementation |
| ASTRA | Principal Architect + Independent Auditor | Implementer |
| GROK | Stateless dispatcher / clerk | Engineer, architect, reviewer, event bus |
| DEVIN | Ticket owner: investigate → implement → test → debug → PR → proof | Product owner |
| CHEAP_WORKER | Narrow low-risk work or explicitly allowed read-only review | Primary owner of a substantive Devin ticket |
| SLACK | Command / event / status cockpit | Source of truth |
| GITHUB | Persistent source of truth | Chat log |
| ACTIONS / WEBHOOKS / SLACK WORKFLOW | Cheap mechanical nervous system | Reasoning |

## Grok may do

- Identify configured project, repo and task ID.
- Apply `RUNBOOKS/DISPATCH.md`.
- Fill `TASKS/TEMPLATE.md` by substitution only.
- Start at most one writer session for one dispatch event.
- Collect pointers: issue, PR, URL, SHA, CI/check status.
- Relay exact findings and exact User/Astra decisions.
- Record dispatch/status markers.
- Write one short status.
- End session.

## Grok must not do

- Architecture, protocol, schema, API, security, concurrency, consistency,
  financial/blockchain design, major refactor, scope expansion, option selection.
- Rewrite requirements or invent missing policy.
- Perform semantic code review or debugging.
- Poll, stand by, create routines, or monitor in the background.
- Re-read long worker transcripts.
- Summarize work another agent already did when a pointer exists.
- Auto-merge.
- Appoint another model as replacement dispatcher after quota exhaustion.

## Devin

Devin is the primary autonomous software engineer.

Default substantive flow:

investigate → understand → implement inside approved boundaries → run → test →
debug → fix → retest → PR → exact HEAD SHA → proof.

Prefer one task → one owner → one writer → one PR.
Do not micromanage Devin line-by-line.
If an approved contract/invariant/architecture must change, Devin must stop and
return DECISION_REQUIRED.

## Audit depths

A0 NO AUDIT — typo / formatting only; no behavior change.
A1 STANDARD — correctness, acceptance criteria, tests, regression, contract/scope compliance.
A2 DEEP — A1 plus relevant concurrency, state machine, persistence, payments, security, protocol.
A3 ARCHITECTURE GATE — invariant, schema, public contract, Sui/blockchain architecture, financial semantics.

Touching an already-approved A3 area does not itself require a new architecture
decision. If the approved contract can be preserved, Devin may implement and
Astra audits at A3. If the approved contract itself must change:
DECISION_REQUIRED → Astra analysis → User decision → GitHub record → resume.

## Audit results

PASS — no merge-blocking finding.
PASS_WITH_NOTES — non-blocking improvements only; no unresolved correctness/invariant/security/contract issue.
FAIL — merge-blocking correctness, regression, invariant, security, contract, or acceptance failure.
DECISION_REQUIRED — architecture/requirements choice rather than ordinary implementation defect.

Grok does not soften FAIL.
Every audit is bound to the exact audited HEAD SHA.
If HEAD moves, the prior audit is not the final gate for the new SHA.

## Quota failover

IF GROK_QUOTA_UNAVAILABLE:
write `[BLOCKED] Reason: GROK_QUOTA`.
Do not appoint Cursor, ChatGPT, another Grok session, or another model as dispatcher.
USER may manually hand the existing GitHub task package to Devin.
Fail closed.

## Credentials

Router uses a dedicated least-privilege identity/tokens.
GitHub: only repository read, issue/comment and checks/PR read capabilities
actually needed by the runbook. No admin, secrets, delete, org admin, or merge.
Slack: control/decision/audit + configured project channels only.
Do not park a personal main GitHub/Slack session on the Grok computer.

## Source of truth

1. approved repository contracts / ADRs / architecture docs
2. accepted GitHub issue/task package
3. exact source at known SHA
4. CI/test evidence
5. Slack transient communication
6. agent memory

Slack is not memory. Agent memory is not authoritative.
Consequential decisions must be recorded back to GitHub.

## Success

Correct task → correct worker → pointers not essays → worker finishes →
only consequential judgment escalated → exact SHA audited as required →
GitHub records durable decisions → User controls merge.

Less Grok reasoning is better.

---

# Repository-specific engineering rules (preserved)

# KIX Protocol — Agent Governance

These rules apply to Devin and every other coding agent working in this repository. They are repository-wide execution constraints. A task document may narrow scope further. If a task document, repository state, and these rules conflict or are ambiguous, stop and report the conflict instead of guessing.

## 1. Session start and source of truth

Before editing anything:

1. Run `git fetch origin main`.
2. Record the exact `origin/main` SHA as the observed current main.
3. Record the task branch HEAD.
4. Read, in this order:
   - `README.md`
   - `docs/DEVELOPMENT_PLAN.md`
   - `docs/status/BASELINES.md`
   - `docs/decisions/AUTHORITY_MODEL_1.md`
   - the current task document under `docs/tasks/`
   - any contracts/evidence explicitly named by that task.

`docs/DEVELOPMENT_PLAN.md` is the current authority for approved, deferred and prohibited implementation scope. Historical roadmaps are evidence, not current authorization.

If the task's stated base differs from current `origin/main`, report the delta. Do not silently rebase, merge main into the task branch, or change the task base.

## 2. One session = one task

One agent session handles exactly one task.

- Do not reuse a completed session for a new task.
- A new task uses a new task document, new branch and new agent session.
- Recommended naming:
  - task: `Task NNN`
  - branch: `agent/task-NNN-<short-name>`
  - validation: `validation/<date>-task-NNN-<short-name>/`

Do not begin the next task as cleanup, follow-up or "while here" work in the current session.

## 3. Task documents are immutable inputs

Files under `docs/tasks/` that define the current task are instructions, not agent-owned outputs.

Agents must not edit, rewrite, reinterpret, broaden or "clarify" the current task document.

If the task is ambiguous, contradictory, incompatible with repository state, or appears to require work outside its authorization:

- stop;
- report the exact ambiguity/conflict;
- ask for human clarification.

A task document may be created or revised only outside the executing agent session by an explicitly authorized human/orchestrator workflow.

## 4. Absolute locked files

Do not modify, reformat, rename, regenerate, or transiently mutate these files:

- `runtime/crates/kix-kernel/src/lib.rs`
  - required Git blob: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
  - required Git blob: `b607996c83a119c349f1cc90469ac1ba82764e20`

Verify both blobs before and after work.

If a contract violation can only be fixed by changing a locked file:

- do not change the locked file;
- create the smallest useful reproduction using allowed files;
- report the blocker;
- do not propose merge.

The lock changes only through a separate explicit human decision.

## 5. Work not authorized by default

Unless a later explicit human authorization specifically permits it, do not perform:

- R2, custom replication, consensus, storage-engine or log-engine implementation;
- integration (a) of PR #11 wire/local-journal experiments onto v4;
- lifecycle release/GC, new terminal release behavior, evidence reclamation, review release or index changes;
- production PG/bank calls, live-money execution, or live Sui production execution;
- bulk KTX→KIX renaming or unrelated Cargo/workflow/lint/code hygiene sweeps;
- moving or deleting existing tags;
- force-moving, force-pushing or deleting existing branches;
- direct pushes to `main`;
- repository settings, branch protection, secrets, permissions or environment changes.

Creating a new task-specific branch is allowed.

Model 1 (chain authority / off-chain delegated execution) is the approved authority model, but the current v4 kernel is not a complete implementation of it.

## 6. Change discipline

- Prefer the smallest patch that proves the requested point.
- Do not rewrite historical evidence to make it look current.
- Do not claim that CI from an older SHA applies to a newer SHA.
- Do not convert source-informed tests into claims of clean-room independence.
- Do not infer production durability, distributed fencing, bank exactly-once, chain finality, legal compliance or production readiness from in-memory tests.
- Preserve stable operation identity, immutable first-result semantics, UNKNOWN handling, retained evidence and bounded-capacity distinctions unless the task explicitly changes an authorized contract.
- Never force-push or rebase reviewed history unless an explicit human instruction authorizes that exact operation.
- Test-count growth is not itself a completion criterion.

## 7. Existing coverage first

Before adding a new test, inspect and map the existing test/evidence coverage relevant to the requested behavior.

Classify each task requirement as:

- sufficiently covered;
- partially covered;
- not covered.

If existing deterministic regression coverage is sufficient, cite the exact test/path instead of duplicating it.

New tests should cover a documented gap, contract predicate, minimal reproduction or explicitly labeled characterization.

For `kix-kernel` tests:

- prefer public APIs and externally observable state;
- keep contract-invariant tests separate from the source-informed differential model where practical;
- avoid asserting private layout or implementation trivia unless the task explicitly requires characterization of that implementation.

## 8. Contract/implementation discrepancy rule

Classify a discovered behavior before changing anything:

### A. Contract-defined and matching

Proceed normally.

### B. Contract undefined

Record it as an observed characterization and remaining uncertainty. Do not invent semantics or amend authoritative contracts inside the task unless explicitly authorized.

The task may otherwise proceed.

### C. Explicit contract violation

Create the smallest useful reproduction.

Do not silently redefine the contract or change a locked file.

Stop the merge path and report a blocker. A PR containing diagnostic evidence may remain open, but the agent must not report it as merge-ready.

## 9. Testing and local verification

Run the narrow relevant tests first, then the broader repository verification required by the task.

For Rust work, use the `runtime/` workspace. At minimum, run relevant crate tests and the workspace tests covering changed code, plus Clippy/formatting when applicable.

Inspect the repository's GitHub Actions definitions and run the closest practical local equivalents.

Do not edit CI merely to make the current task pass.

Record commands actually run and their actual results. Do not fabricate or infer results.

## 10. Exact-head CI gate

After all task changes are committed, identify the exact final task head.

The agent may propose merge only after both workflows for that exact head are:

- KTX kernel verification: `status=completed`, `conclusion=success`
- KIX protocol verification: `status=completed`, `conclusion=success`

Rules:

- CI success from an earlier SHA does not transfer to a later SHA.
- If either workflow is `queued` or `in_progress`, report that exact state and wait. Do not propose merge.
- If either workflow fails, diagnose the failure. Make only a minimal in-task fix if authorized; otherwise report a blocker.

## 11. Avoid CI evidence self-reference loops

Do not create an infinite loop by committing CI run IDs for the same "final" head and thereby creating a new final head.

Use this pattern:

1. Implementation/evidence content may record CI for an earlier implementation head if useful.
2. Once the true final head is established, verify its exact-head CI.
3. Record the final-head CI result in the PR closure report/comment, not by creating another repository commit solely to record that final-head result.

Do not make a new commit merely to record the CI of the previous "final" commit unless a human explicitly asks for it.

## 12. Human-only merge authorization

Green CI means `merge-ready`; it does not authorize merge.

Without explicit human approval, the agent must not:

- mark a draft PR ready for review;
- merge a PR;
- squash or rebase-merge;
- create/move/delete tags;
- delete branches;
- push directly to `main`.

When human merge approval is given, the default is an ordinary merge commit preserving reviewed commit lineage. Squash, rebase merge or history rewriting require separate explicit approval.

## 13. Post-merge verification

After an authorized merge:

1. Record the merge commit SHA on `main`.
2. Verify the locked blobs again on the merge commit.
3. Verify the main/push CI for that merge commit through its terminal state.
4. End the task only after the required post-merge checks are complete.

If post-merge CI fails:

- do not patch `main` directly;
- report the failure and diagnosis;
- any corrective change must use a new task, new branch, new session and new PR.

## 14. Required evidence report

Every agent task report must include, as applicable:

- Task ID and task document path;
- exact observed `origin/main` / base SHA;
- implementation head SHA;
- exact final task head SHA;
- merge commit SHA if merged;
- complete changed-path list;
- locked blob verification before/after/final merge;
- existing coverage mapping;
- new tests/evidence and what gap each addresses;
- commands actually run and actual results;
- exact-head KTX CI run ID/status/conclusion;
- exact-head KIX protocol CI run ID/status/conclusion;
- post-merge main CI run ID/status/conclusion when merged;
- contract violations found;
- contract-undefined characterizations found;
- explicit non-claims / what was not tested;
- remaining uncertainty and follow-up candidates.

Do not fabricate test counts, performance numbers, hashes, CI run IDs or external verification.

## 15. Agent self-assessment limits

Report concrete acceptance criteria and evidence, not broad assurances.

Acceptable:
- "67 tests passed; locked blobs match; exact-head CI is green."

Not acceptable without separate evidence and authorization:
- "The kernel is safe."
- "This is production-ready."
- "Durability is solved."
- "The protocol is fully verified."

Agents should report `merge-ready`, `blocked`, `in_progress` or equivalent evidence-backed task state rather than an unqualified project-level verdict.

## 16. Security and credentials

Do not commit private keys, proving keys, credentials, non-public notes, local chain databases or secrets.

Do not broaden repository permissions or external-service access as part of an ordinary task.

Prefer separation between the coding agent and GitHub publication credentials where automation permits it.
