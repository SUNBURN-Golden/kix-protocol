# v5-lifecycle-seeded-model-test — seeded model test for the v5-only lifecycle surface

Node: `plan-v5-lifecycle-seeded-model-test`. Not an ASTRA program-mode session.
No issue (`issue: none` in the node input). Depends on `k-stage2-v5-impl`.
Audit floor A2. `astra_gate: None`, `user_merge: false`.
Source: KIX planner run 1792307132 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an
issue, or comment anywhere. There is no implementation head SHA, no final task
head SHA, and no KTX kernel verification or KIX protocol verification run ID for
a head containing these files.

Observed `origin/main` = branch HEAD = `90d320325a601e1f604cd901703fd2a5094ca527`,
recorded from the local clone. `git fetch` is outside this session's authority
(supervisor owns git/GitHub), so no fetch delta is reported; the worktree HEAD
equals the local `origin/main`. Branch `agent/kix-plan-v5-lifecycle-seeded-model-test`.

`rustc 1.98.1 (48a229cea 2026-09-01)`, the workflow pin. `python3` 3.13.5.

Locked blobs before and after the edits:

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

`git status --short` names only the new test file and this record; `git diff`
over `runtime/crates/kix-kernel/**`, `runtime/crates/kix-kernel-v5/src/**`,
`runtime/Cargo.toml`, `runtime/Cargo.lock`, `reference/v0.3-rc1/**`, `.aiops/`,
`.github/`, `docs/tasks/` is empty. `kix-kernel-v5/Cargo.toml` is untouched, so
`tests/boundary.rs`'s dev-dependency assertion still holds (`kix-kernel` only).

## Changed paths

| Path | Change |
|---|---|
| `runtime/crates/kix-kernel-v5/tests/lifecycle_model.rs` | New. Seeded generator + test-local oracle + delete-minimizing shrinker + coverage guard. |
| `validation/2026-10-19-v5-lifecycle-seeded-model-test/README.md` | This record. |
| `docs/README.md` | One index bullet under a new `2026-10-19` section (required by `check_docs_index.py`). |

No `src/lib.rs` change, no contract change, no new dependency, no `Cargo.lock`
change, no workflow edit. The PRNG is the same LCG `v4_differential.rs` uses,
inside the test file.

## What the test does

`seeded_lifecycle_histories_match_oracle` runs 8 seeds
(`1, 2, 7, 11, 42, 99, 0x51A6E25B, 0x00C0FFEE`) x 128 steps = 1,024 commands over
reserve / `mark_payment_unknown` / `expire` / `observe_capture` /
`replace_owner` / `cancel_scope` and the v5-only `terminate`, `place_hold`,
`clear_hold`, `reclaim_report`, `reclaim_reports`. Per-op counts actually run
(all seeds): reserve 144, send 191, expire 63, capture 146, terminate 151,
place_hold 139, clear_hold 27, report 68, batch 32, owner/cancel 63.

A test-local `Model` mirrors every command in the documented check order —
decision/hold-id replay before context, `AutomaticApprovalDisabled` before
order checks, `AlreadyTerminated` before the `InvalidTransition` predicate,
`ConditionNotSatisfied` before `StaleEvaluation`, report blockers in the
declared order `ActiveOp, ReservedSlot, ReviewRequired, UnboundFence,
ReturnObligation, ReplayWindow, Hold, I09, I10, I13`, batch order
`(terminated_at, order_id)` — from `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md`
§5–§6 and `validation/2026-10-13-k-stage2-v5-impl/README.md`. It never calls
`operation_snapshot`, `reclaim_report` or `reclaim_reports` to compute an
expectation: `Terminate::evaluated` and every report field come from the
model's own maps. After every step the test compares the result, a whole-kernel
equality check for mutation expectations (`Err` changes nothing except the
documented `observe_capture` conflict→`Capacity` path, which still quarantines
bound operations and advances ordered time), the public view (per-order row,
termination, hold, counts, conflicts), and `reclaim_report`/`reclaim_reports`
for every order id at the model's `now` and `now - 1` — which pins the ordered
clock exactly, since a report at `now` rejects iff kernel time is ahead and one
at `now - 1` accepts iff it is behind.

The generator emits small id ranges so replays and conflicts occur naturally,
plus boundary-exact report times resolved against the model (first result ±
retry window, termination + residency, large jumps, regressions). Generated
`order`/`decision`/`hold` bytes are hints the driver resolves against the model
— a stored decision for the replay and `CommandConflict` variants, a terminated
order + free decision for `AlreadyTerminated`, a terminatable order for the
`Stale`/`FalseCondition` paths, stored or free hold ids for the hold modes, a
still-reachable boundary order for report `now`. Selection is a pure function
of the seed because the model is one; every issued command is still compared
with the same oracle, so the check is not weakened. On failure the test prints
the seed, the failing step, and a delete-minimized command list that replays
through the same driver.

A coverage guard requires every listed behaviour at least once across the seeds
so a seed set cannot pass vacuously. Counts from the passing run: applied
termination 8, termination replay 5, `AlreadyTerminated` 25, `StaleEvaluation` 3,
`ConditionNotSatisfied` 5, `AutomaticApprovalDisabled` 5, terminate
`InvalidTransition` 23, terminate `CommandConflict` 14, send-after-terminate 12,
hold placed 21, hold replayed 24, `HoldExists` 3, hold `CommandConflict` 41,
`UnknownHold` 18, clear 9, `ReturnRequired` implicit hold 87, `OpenConflict`
implicit hold 891, replay-window boundary below 9 / at 6, report
`ClockRegression` 15, reserve replay 5, conflict outcome 16, conflict→`Capacity`
mutated-error path 22.

## Existing coverage (AGENTS §7)

Fixed-case coverage stays; this file adds only the seeded-interleaving axis.

| Requirement | Class before | Existing tests | What the seeded sequences add |
|---|---|---|---|
| Termination once, replay by `decision_id`, payload conflict, second decision, automatic rejection, false C1–C5, stale evaluation, send blocked after termination | sufficiently covered | `termination.rs` (13) | interleavings with holds, reports, cancels, owner changes, conflicts; mutation check on every rejected command |
| Report blocker order, boundary-exact windows, saturating arithmetic, implicit holds, read-only, errors | sufficiently covered | `reclaim_report.rs` (13) | boundary hits found by generated `now` (below/at the replay window), batch and per-order reports re-checked after every single step |
| Hold kinds, one per order, replay, conflicting reuse, explicit clear | sufficiently covered | `holds.rs` (9) | seeded place/clear/re-place sequences across orders and times |
| Batch order and cap flag | sufficiently covered | `reclaim_batch.rs` (6) | batch compared after every step, including `(terminated_at, order_id)` ties the seeds produce |
| Termination/hold/report/clear release no slot, inventory, review or evidence | sufficiently covered | `stopped_transitions.rs` (5) | the same absence under random interleaving, via whole-kernel equality and the public view |
| Shared-command equivalence with v4 | partially covered | `v4_differential.rs` (3), `conflict_index.rs` (4) | the shared commands re-driven inside v5-only sequences |
| Seeded v5-only lifecycle sequence | not covered | none | this file |

## Discrepancy classes (AGENTS §8)

No class C (explicit contract violation) and no class B ambiguity blocked the
node: the check order and report shape mirror the crate's documented semantics
as recorded in the design decision §5–§6 and the `k-stage2-v5-impl` record. One
class-B characterization inherited from that record is restated, not amended:
the oracle reads `UnboundFence` as retained conflict evidence for the
candidate's own operation identity, and "open conflict" as a quarantined
operation or retained conflict, matching the crate's comments.

**Oracle non-independence (required note):** the oracle was written with the v5
source in view, like `v4_differential.rs`. Agreement is not an independence
proof and does not show either side is free of a shared mistake.

## Negative control (acceptance 4)

In a throwaway copy (`tar --exclude=target` of `runtime/` into `/tmp/lc_scratch`,
deleted afterwards — never committed), one line was removed from
`report_for` in `crates/kix-kernel-v5/src/lib.rs` (the `ReservedSlot` blocker
push). `cargo test --manifest-path /tmp/lc_scratch/runtime/Cargo.toml -p
kix-kernel-v5 --test lifecycle_model --locked` failed at `seed=1`, step 4:
model `blockers=[ActiveOp, ReservedSlot, ReplayWindow, Hold, I09, I10, I13]`
vs mutated kernel `blockers=[ActiveOp, ReplayWindow, Hold, I09, I10, I13]`,
and the shrinker reduced the failing history to 2 steps.

## Commands and results

All run from the node worktree in the foreground.

| Command | Result |
|---|---|
| `git rev-parse HEAD`; `git rev-parse origin/main`; `git hash-object` on the two locked paths (start and end) | HEAD = `origin/main` = `90d320325a601e1f604cd901703fd2a5094ca527`; blobs `69564b16…`, `b607996c…` unchanged |
| `rustc -V` | `rustc 1.98.1 (48a229cea 2026-09-01)` |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test lifecycle_model --locked` | exit 0. 1 test, pass. 8 seeds x 128 steps = 1,024 commands; coverage table above |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --locked` | exit 0. 56 tests: boundary 2, conflict_index 4, holds 9, lifecycle_model 1, reclaim_batch 6, reclaim_report 13, stopped_transitions 5, termination 13, v4_differential 3 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test boundary --locked` | exit 0. 2 tests, pass |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0. All crates pass |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0 |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 after `cargo fmt` on the new file (final run clean) |
| `python3 scripts/verify_runtime_architecture.py` | exit 0. `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |
| `python3 scripts/test_runtime_architecture.py` | exit 0. 7 tests, OK |
| `python3 scripts/check_docs_index.py` | exit 0 after the `docs/README.md` bullet |
| `python3 scripts/check_docs_index.py --self-test` | exit 0. `self-test: pass` |
| `python3 scripts/check_status_register.py` + `--self-test` | exit 0 |
| `python3 scripts/check_rs_profile_traceability.py` + `--self-test` | exit 0 |
| `python3 scripts/check_read_model_source_map.py` + `--self-test` | exit 0 |
| `python3 scripts/check_i12_proof_ids.py` + `--self-test` | exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` + `--self-test` | exit 0 |
| `python3 scripts/check_rs_predicate_evidence_map.py` + `--self-test` | exit 0 |
| `python3 scripts/check_rs_im_evidence_map.py` + `--self-test` | exit 0 |
| `python3 scripts/check_contract_error_codes.py` + `--self-test` | exit 0 |
| Scratch mutation of `report_for` (dropped `ReservedSlot` push) + `cargo test ... --test lifecycle_model --locked` | exit 1 as required: `seed=1` step 4 blocker-list mismatch, shrunk to 2 steps |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --edges normal --locked` | `kix-kernel-v5` → `kix-types` only |

Not run (environment limits, none reads the new test file): `.venv` steps
(`verify_runtime.py`, commerce, canonical, paid storage, localnet), Node 24
SDK steps (`node` here is 20.19.2 vs `toolchains.json` 24), Move tests, ZK
setup, `sui` (not on `PATH`), and the `ktx-kernel.yml`/`protocol.yml` workflows
as workflows. The record states what actually ran; no CI evidence is claimed.

## CI (AGENTS §10, §14)

- Exact-head KTX kernel verification run: none. No commit exists.
- Exact-head KIX protocol verification run: none. No commit exists.
- Merge commit and post-merge main CI: not applicable.

The supervisor commits and opens the PR. This record claims `merge-ready` for
nothing; the node state is implementation complete locally, awaiting exact-head
CI, non-author review, Astra's architecture audit and the user merge.

## Non-claims

This record does not claim durability, distributed fencing, bank exactly-once
behavior, chain finality, legal compliance, production readiness, a retention
policy, or state-changing reclamation. It does not choose, change or ratify the
retention defaults and does not close I09, I10, I13 or any stopped transition
(no entry point exists for slot release, review release or record reclamation).
The `ReclaimPolicy` values the test passes other than `Default`
(`retry_support_window_ms` 100, `memory_residency_ms` 40, cap 2, floor 300) are
test fixtures only — they keep boundaries reachable inside a 128-step history
and are not policy choices. Termination here is the in-memory record, not a
durable approval. No provider fact was evaluated and no principal was
authenticated. It is not an Astra review, and the oracle agreement is not an
independence proof (source in view). Local success is not exact-head CI and is
not merge authorization.
