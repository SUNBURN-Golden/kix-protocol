## Scope

- Task/spec:
- Exact base SHA:
- Exact head SHA:
- Changed paths:

## KIX guardrails

- [ ] Read `AGENTS.md` and current `docs/DEVELOPMENT_PLAN.md`.
- [ ] `runtime/crates/kix-kernel/src/lib.rs` still matches blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- [ ] `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` still matches blob `b607996c83a119c349f1cc90469ac1ba82764e20`.
- [ ] No R2/custom replication/storage/log implementation.
- [ ] No PR #11 integration (a).
- [ ] No lifecycle release/GC/index implementation unless explicitly authorized.
- [ ] No live PG/bank/Sui execution.
- [ ] No unrelated bulk hygiene, tag/branch movement, or repository-setting changes.

## Verification

Commands actually run:

```text
<commands and results>
```

CI runs on this exact head:

- Run:
- Result:

## Evidence and limitations

- Existing coverage reused:
- New coverage:
- What this PR does **not** prove:
- Remaining uncertainty / follow-up:

## Review state

- [ ] Keep as draft until human approval.
- [ ] Do not merge automatically.
