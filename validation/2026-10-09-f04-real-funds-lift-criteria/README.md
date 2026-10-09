# f04-real-funds-lift-criteria — real-credit lift criteria

Node: `f04-real-funds-lift-criteria`. Document only. No code, no new tests, no
policy numbers, no new protocol command.
Issue: none. `docs/tasks/` has no file for this node.
Depends on: `f04-mock-deepening` (merged as pull request #158).
Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`:
`9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1`.
Branch: `agent/kix-f04-real-funds-lift-criteria`.
This session did not commit, push, open a PR, dispatch a workflow, or comment.
There is no implementation commit SHA. Local results below are not exact-head CI.
There is no KTX kernel verification run ID and no KIX protocol verification
run ID for a head that contains these files.

Locked blobs at that HEAD, before and after the documentation edit (HEAD is
unchanged; the new files are untracked):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts runtime`
was empty. `git diff --raw --no-renames origin/main` was empty because the new
files are untracked. `git status --short` is the list of changed paths. Both
paths are under `docs/decisions/` and `validation/`, outside `docs/contracts/`,
`docs/adr/`, and `README.md`.

## Changed paths

| Path | Change |
|---|---|
| `docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md` | Criteria and User decision document. Effect only on User merge. Suggestion is O1 (the full criteria set). The lock stays. |
| `validation/2026-10-09-f04-real-funds-lift-criteria/README.md` | This record. |

## Commands and results

Toolchain: `rustc 1.98.1 (48a229cea 2026-09-01)`, `cargo 1.98.1 (797e8a9bc 2026-08-05)`.
That matches `rust-toolchain.toml` and the workflow pin `1.98.1`.

The first `cargo test --workspace` attempt exited 101. The compiler reported
`No space left on device (os error 28)` while creating a temp dir under
`runtime/target`, and the linker then hit a bus error. `runtime/target` was
removed. The fmt, clippy, and test commands below were then run with
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`,
`CARGO_INCREMENTAL=0`, and `CARGO_BUILD_JOBS=1` so the same checks could fit
in the remaining space. Those variables drop debug info. They do not change
the sources or the warning gate.

| Command | Result |
|---|---|
| `git fetch origin main && git rev-parse origin/main HEAD` | both `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1` |
| `git hash-object` on the two locked files, before and after | both times `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `git diff --stat origin/main -- reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts runtime` | empty |
| `git status --short` | `?? docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md` and `?? validation/2026-10-09-f04-real-funds-lift-criteria/` |
| `git diff --raw --no-renames origin/main` | empty, because the new files are untracked |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | exit 0. 7 tests, OK |
| `python3 scripts/check_openapi_contract.py` | exit 0. `openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff` |
| `python3 scripts/check_openapi_contract.py --self-test` | exit 0. `self-test: pass` |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | first attempt exit 101 (disk full). Rerun exit 0 with the debug-info settings above. kix-bcs1 3 + golden_vectors 4, kix-feature-ir 5 + audit_regressions 8 + schema_bound 18, kix-feature-semantics 6, kix-kernel lib 0 + contract_edge_cases 8 + contract_invariants 3 + e4_state_model 12 + observation_slots 11 + performance_harness 4 + quarantine_capacity 8 + transitions 32, kix-types 6. Doc-tests 0. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0, with the same debug-info settings |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | exit 0. 26 tests, OK |

After the successful rerun, `runtime/target` was deleted. That directory is
gitignored. It is not a repository change.

## What was not run

Hosted `protocol.yml` and `ktx-kernel.yml` were not run. This session did not
open a pull request and did not dispatch either workflow. For a diff limited
to `docs/decisions/*` and `validation/*` other than `validation/2026-09-11/*`,
both workflows classify the change as documentation-only and skip the heavy
steps. A skipped heavy job is not a full-verification pass. A skipped draft
pull request is not a pass. This local run is not that classification and
does not transfer to a later SHA.

Not run locally: integration gate, reference suites other than
`reference/credit_advance_f04`, SDK conformance, `scripts/verify_runtime.py`,
commerce and canonical verifiers, storage probes, localnet, ZK.

## Non-claims

No legal, tax, accounting, or licensing conclusion. No amount, cap, rate,
reserve, service level, or pilot size. No lock changed. No real funds, real
PG, bank, or KYC call. No production durability. The criteria document does
not lift the real-credit row. A documentation-only local green is not full
verification.
