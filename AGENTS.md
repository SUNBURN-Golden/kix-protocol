# Product agent governance

Shared engineering policy is maintained in `BeautifulMind-JT/ai-ops-control-plane`.
See `docs/CONTROL_PLANE_POINTER.md` and `.github/control-plane-client.json` for
the candidate pin, pending central PR acceptance. Policy adoption is not runtime
activation. User-only merge, non-author exact-HEAD review, single writer, UNKNOWN
fencing, no polling and no automatic retry remain required.
If shared policy and project contracts conflict, stop with DECISION_REQUIRED.

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

Explicit human authorizations granted after this list are recorded under `docs/decisions/`. The 2026-09-28 owner-approved program decisions (`docs/decisions/PROGRAM_DECISIONS_20260928.md`, approved by merging PR #73) do three things:

- They classify the non-production `readiness/` local wrapper, within its stated bounds, as outside the storage/log-engine item above.
- They open Track P (Task 005 waves) on gate records.
- They keep every other item in this list locked, each with its unlock criteria.

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

### Draft-first CI

Both workflows skip draft PRs. A PR runs them when it is opened as ready, when it is marked Ready for review, and on every push after that. Push to `main` and `workflow_dispatch` still run them.

- Keep the PR in draft while working, and run the relevant tests locally.
- Batch commits and push them together, not one push per commit.
- When the work is a merge candidate, it is marked Ready for review. The CI run triggered then is the exact-head evidence for this section. Marking a draft ready still follows §12: an agent does it only with explicit human approval.
- After Ready, push only review fixes. Each push runs full CI again.
- A draft PR's skipped or absent CI is not a pass. Never report it as one. A skipped job shows as success on the check, but a draft cannot be merged.
- If CI evidence is needed while the PR is still in draft, run `workflow_dispatch` on the branch by hand, once.

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
