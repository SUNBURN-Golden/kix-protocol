# audit8-readiness-conformance-sweep-limit-note

Node: `audit8-readiness-conformance-sweep-limit-note`. Source: KIX audit #8.
Wording in the readiness conformance doc and one register cell; no test, store, format or contract change, no classification decision, no grade change.
Issue: none. Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`. Not a program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment.
There is no implementation commit SHA and no final task head SHA. Local results below are not
exact-head CI. Exact-head CI for the final head belongs in the PR closure report (AGENTS §11).

Observed `origin/main` and branch HEAD at session start: `08b317e5096893432116e41c8312697793500cfe`
(merge of PR #208). `git fetch origin main` ran; no delta.

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` =
`69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` =
`b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `reference/v0.3-rc1/**` is untouched.

## What changed

- `readiness/CONFORMANCE.md`: new final section "Journal byte sweep: observed limits". It names
  `readiness.test_faults.JournalByteSweepTests` and the families T/H/F/L/R, and states as AGENTS §8 class B
  (builder reading) that a damaged length prefix on a non-final frame is parsed as a torn tail and truncates later
  acknowledged frames, that a 0-byte journal is reinitialised, and that a clean frame-boundary truncation is
  undetectable. It says the Astra ruling on `docs/contracts/READINESS_RUNTIME.md` line 21 is pending and the suite is
  not evidence of fail-closed behaviour for mid-file length damage. Numbers are copied from the outcome table of
  `validation/2026-10-17-readiness-journal-byte-sweep/README.md`.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md`: the same limit in a few words in the EV-READY fixture cell, and a
  new basis line for the EV-READY row.
- `docs/README.md`: one index bullet; the register basis summaries now name EV-READY at the 2026-10-18 basis.

## Changed paths

- `readiness/CONFORMANCE.md`
- `docs/status/CURRENT_CAPABILITY_REGISTER.md`
- `docs/README.md`
- `validation/2026-10-18-audit8-readiness-conformance-sweep-limit-note/README.md` (this file)

## Existing coverage mapping (AGENTS §7)

| Requirement | Coverage | Evidence |
|---|---|---|
| Sweep findings exist and are pinned | sufficiently covered | `readiness/test_faults.py::JournalByteSweepTests`; the #205 record |
| Findings visible on the conformance surface | not covered before this node | now `readiness/CONFORMANCE.md` section above |
| EV-READY register cell carries the limit | partial (pointer only) | now the limit in the cell |

No test or script was added or renamed.

## Contract findings (AGENTS §8)

- A: none relevant.
- B: the three observations above; the contract does not define them.
- C: none recorded. Whether the first finding is B or C is Astra's ruling and is not decided here.

## Commands actually run

See the session evidence table. Cargo, clippy, fmt, Move, ZK, localnet, Node and SDK steps: NOT_RUN locally
(no Rust, Move or JS touched); they run hosted. `readiness/CONFORMANCE.md` is not a documentation-classified
path in the hosted classifier, so the hosted runs are expected to be full verification, not docs-only.
Exact-head CI is not available before commit.

## Non-claims

- No power-loss, OS-crash, `fsync` or production durability claim. No grade change.
- No B-versus-C decision; the Astra ruling is pending.
- Only the mutations the #205 sweep measured are described; unswept mutations are not characterized.

## Residuals

- The dated 2026-10-06 register row `readiness.test_faults | 14 tests OK` is left as history.
- The Astra ruling on `READINESS_RUNTIME.md` line 21 and the format-hardening ADR candidate remain open.
- The `docs/DEVELOPMENT_PLAN.md` §5 row for this node is owed to a later sync.
