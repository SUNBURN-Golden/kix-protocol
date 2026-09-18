## Task identity

- Task ID:
- Task document:
- Agent session:
- Exact observed `origin/main` / base SHA:
- Implementation head SHA:
- Exact final head SHA:
- Merge SHA (if merged):

## Changed paths

- <path — purpose>

## KIX guardrails

- [ ] Read root `AGENTS.md`, current `docs/DEVELOPMENT_PLAN.md`, and the immutable task document.
- [ ] Current task document under `docs/tasks/` was not modified by the executing agent.
- [ ] `runtime/crates/kix-kernel/src/lib.rs` matches blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- [ ] `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` matches blob `b607996c83a119c349f1cc90469ac1ba82764e20`.
- [ ] No unauthorized R2/custom replication/storage/log implementation.
- [ ] No unauthorized PR #11 integration (a).
- [ ] No unauthorized lifecycle release/GC/index implementation.
- [ ] No live PG/bank/Sui production execution.
- [ ] No unrelated bulk hygiene, tag movement, force-push, branch deletion, direct main push, or repository-setting changes.

## Existing coverage / state mapping

- Sufficiently covered:
- Partially covered:
- Not covered:

## Verification

Commands actually run and actual results:

```text
<commands and results>
```

### Exact final-head CI

- KTX kernel verification
  - Run ID:
  - Status:
  - Conclusion:
- KIX protocol verification
  - Run ID:
  - Status:
  - Conclusion:

If either is queued/in_progress, report that state and do not propose merge.

## Contract discrepancy classification

- Contract-defined and matching:
- Contract-undefined characterizations:
- Explicit contract violations / blockers:

## Evidence and limitations

- New tests/evidence and the gap each addresses:
- What this PR does **not** prove:
- Remaining uncertainty / follow-up candidates:

## Review state

- [ ] Current state is evidence-backed: `in_progress`, `blocked`, or `merge-ready`.
- [ ] No merge is authorized by CI alone.
- [ ] Human approval is required before draft removal/merge.
- [ ] If merged, record merge SHA and post-merge main CI below.

## Post-merge verification

- Merge SHA:
- Locked blobs re-verified on merge SHA:
- Main/post-merge KTX CI run ID/status/conclusion:
- Main/post-merge KIX protocol CI run ID/status/conclusion:
- Task closed only after required post-merge checks complete:
