# KIX Protocol — Agent Instructions

These instructions apply to Devin and any other coding agent working in this repository.

## 1. Source of truth and session start

Before editing anything:

1. `git fetch origin main`.
2. Record the exact `origin/main` SHA used as the base.
3. Read, in this order:
   - `README.md`
   - `docs/DEVELOPMENT_PLAN.md`
   - `docs/status/BASELINES.md`
   - `docs/decisions/AUTHORITY_MODEL_1.md`
   - `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md`
   - `docs/contracts/CONTRACT_INVARIANTS.md`
   - `docs/contracts/PERFORMANCE_MEASUREMENT.md`
   - `docs/contracts/STATE_LIFECYCLE.md`

`docs/DEVELOPMENT_PLAN.md` is the current authority for approved, deferred and prohibited implementation scope. Historical roadmaps are evidence, not current authorization.

## 2. Absolute locked files

Do not modify, reformat, rename, regenerate, or transiently mutate these files:

- `runtime/crates/kix-kernel/src/lib.rs`
  - required Git blob: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
  - required Git blob: `b607996c83a119c349f1cc90469ac1ba82764e20`

Verify these blobs before and after work. A task that appears to require changing either file is blocked unless the user explicitly changes the lock in a later authoritative instruction.

## 3. Work that is NOT authorized by default

Do not start any of the following unless the current task explicitly authorizes it:

- R2, custom replication, consensus, storage engine or log implementation.
- Integration (a) of PR #11 wire/local-journal experiments onto v4.
- Lifecycle release/GC, new terminal transitions, evidence reclamation, review release or index changes.
- Production PG/bank calls, live-money execution, or live Sui chain execution.
- Bulk KTX→KIX renaming.
- Cargo/workflow/lint/branch/tag hygiene sweeps unrelated to the task.
- Moving or deleting existing tags or branches.
- Repository protection/settings changes.
- Merging a PR or marking a draft PR ready for review unless explicitly instructed.

Model 1 (chain authority / off-chain delegated execution) is the approved authority model, but the current v4 kernel is not a complete implementation of it.

## 4. Change discipline

- Prefer the smallest patch that proves the requested point.
- Do not rewrite historical evidence to make it look current.
- Do not claim that old CI results apply to a new head.
- Do not convert source-informed tests into claims of clean-room independence.
- Do not infer production durability, distributed fencing, bank exactly-once, chain finality, or legal compliance from in-memory tests.
- Preserve stable operation identity, immutable first-result semantics, UNKNOWN handling, retained evidence and bounded-capacity distinctions.
- If documentation and implementation appear inconsistent, report the inconsistency before changing semantics.
- Never force-push or rebase reviewed history unless explicitly instructed.

## 5. Testing and verification

For Rust work, use the `runtime/` workspace. At minimum, run the relevant crate tests and the workspace tests that cover changed code. Inspect the repository's GitHub Actions definitions and run the closest local equivalents where practical. Do not edit CI solely to make a task pass.

For tests around `kix-kernel`:

- Prefer public APIs and externally observable state.
- Keep contract-invariant tests separate from the source-informed differential model when possible.
- Do not duplicate an existing regression merely to increase test count; map existing coverage instead.
- A failing discovery in a locked file must be reported with a minimal reproduction. Do not silently change the locked implementation.

## 6. PR evidence requirements

Every agent PR must state:

- exact base SHA and head SHA;
- all changed paths;
- whether each locked blob matched before and after;
- commands/tests actually run and their actual results;
- what was not tested;
- scope exclusions, especially R2, integration (a), storage durability, live PG and live chain execution;
- any remaining uncertainty or conflict with the current development plan.

Do not fabricate test counts, performance numbers, CI run IDs, hashes or external verification.

## 7. Security and repository hygiene

Do not commit private keys, proving keys, credentials, non-public notes, local chain databases or secrets. Do not broaden repository permissions or external service access as part of an ordinary coding task.
