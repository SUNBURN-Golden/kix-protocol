# STATE_LIFECYCLE 0.6 — ReturnRequired/review precedence clarification (Task 002)

Task: `docs/tasks/TASK_002_LIFECYCLE_PRECEDENCE.md` (immutable input, not edited).
Base (`origin/main` observed at session start): `a83d09cd99017875f583383e6ebbabc46a6a63eb`.
This equals the base named by the task; no main drift, no rebase or merge of main.
Task branch: `agent/task-002-lifecycle-precedence`, HEAD before this change
`d1cc57a7d6c640b5df3eacd65a1d8593f0beb346`.
The implementation head is the commit adding the files listed below; the exact
final head and its CI are reported in the PR closure summary, not in a commit.

This is a documentation-contract task. No kernel or runtime semantics, no wire
change, no new test, no review resolution, no ReturnRequired release, no refund
execution, no slot release/GC/index work, no R2, no PR #11 integration (a), no
storage/log engine, and no live PG/bank/Sui work is included.

## Governance precondition: post-merge CI of the base

The push-triggered main run for the governance merge commit
`a83d09cd99017875f583383e6ebbabc46a6a63eb` was read from the GitHub Actions API
before any output file was edited:

| Workflow | Event | Head SHA | Run ID | Status / conclusion |
|---|---|---|---|---|
| KIX protocol verification | push (main) | a83d09cd99017875f583383e6ebbabc46a6a63eb | 35405597758 | completed / success |

The run was `in_progress` when first queried and was polled to its terminal
state before editing began.

## Locked blob verification

`git hash-object` before and after the change, both equal to the required values:

| Path | Required blob | Observed before | Observed after |
|---|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | same | same |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 | same | same |

Neither locked file was opened for writing, reformatted or transiently mutated;
`cargo fmt` was run in `--check` mode only.

## Changed paths

- `docs/contracts/STATE_LIFECYCLE.md` — 0.6 header/revision metadata, new §5.7.1,
  0.5 historical row plus 0.6 current row, 0.5 → 0.6 change table, next version
  minimum raised to 0.7, §7 note that the open-input tally is unchanged.
- `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md` — current authority pointer 0.5 → 0.6.
- `docs/contracts/PG_TOSS_CARD_PROFILE.md` — current authority pointer 0.5 → 0.6
  plus one sentence that a mismatching capture's Review/quarantine does not
  replace ReturnRequired or erase the retained capture.
- `docs/DEVELOPMENT_PLAN.md` — §6.2/§6.3 current-contract statements 0.5 → 0.6,
  keeping the historical description of what 0.5 itself decided.
- `docs/adr/0001-ktx-authority-commit-recovery.md` — the single "current draft"
  pointer in the 2026-09-17 LC-TERM update line 0.5 → 0.6; the ADR's historical
  sentence "Contract 0.4 remains a historical draft; the changed text is version
  0.5." is left untouched.
- `runtime/crates/kix-kernel/README.md` — one bullet stating the precedence and
  orthogonality that the kernel already implements, pointing at 0.6 §5.7.1.
- `validation/2026-09-19-task-002-lifecycle-precedence/README.md` — this note.

## Current-reference audit (0.5 → 0.6)

Every `0.5` occurrence in the repository was inspected and classified.

| Location | Classification | Action |
|---|---|---|
| `STATE_LIFECYCLE.md` header/revision block | current | updated to 0.6, with the 0.5 revision ID kept as the inherited predecessor |
| `STATE_LIFECYCLE.md` §5.4 heading "초안 0.5" | historical (records which draft introduced §5.4) | unchanged |
| `STATE_LIFECYCLE.md` §5.5 "0.4→0.5 and authority generation are different axes" | historical | unchanged |
| `STATE_LIFECYCLE.md` §7 "0.4·이번 0.5" tally sentence | current wording | reworded to historical 0.4·0.5 plus an explicit statement that 0.6 does not change the tally |
| `STATE_LIFECYCLE.md` §8 version history rows 0.1–0.5 | historical | preserved verbatim; the 0.5 row is marked historical with blob `063e37c7d23bae6deeb51b3ff142fccfabf74d42`, and a new 0.6 row was added |
| `STATE_LIFECYCLE.md` "0.4 → 0.5 change table" | historical | unchanged; a separate 0.5 → 0.6 table was added |
| `FIRST_BATCH_OPEN_INPUTS.md` "정본은 … 초안 0.5" | current | updated |
| `FIRST_BATCH_OPEN_INPUTS.md` line 77 "0.5~1" | unrelated (a schedule range, not a contract version) | unchanged |
| `PG_TOSS_CARD_PROFILE.md` "공통 정본은 … 0.5" | current | updated |
| `DEVELOPMENT_PLAN.md` §6.2 "초안 0.5가 현행 정본" and §6.3 "현행 0.5가 계승한", "현행 계약은 0.5다" | current | updated |
| `DEVELOPMENT_PLAN.md` sentence describing what 0.5 decided | historical | kept, with the 0.6 inheritance appended |
| `adr/0001` "current draft 0.5" | current | updated |
| `adr/0001` "the changed text is version 0.5" | historical | unchanged |
| `CONTRACT_INVARIANTS.md` anchor L blob `e953c4870aaeee24b13c75a8647c50609720ae01` | historical: the table states all paths refer to commit `0394a36a655b86bacb568b055d377d4c4fd91185`, and that blob predates even 0.5 | unchanged; rewriting it would falsify a dated evidence anchor |
| `validation/2026-09-18-contract-edge-cases/README.md` | historical evidence from Task 001 | unchanged |

No historical 0.1–0.5 record was relabeled as 0.6.

## Contract conflict check

No authoritative current contract contradicts the 0.6 rule. The pre-0.6 documents
were **silent** on which marker determines `Order::state` when a retained return
obligation and an unresolved review coexist; they already required that captured
facts are not erased (§3 LC-FACT), that quarantine/review is a bound sticky
predicate (§2), and that matching later evidence never clears review
(kernel README). 0.6 fixes the undefined boundary in the direction those clauses
already imply, so this is classification **B** (contract undefined) from
`AGENTS.md` §8, not a violation, and the merge path is not blocked on a conflict.

## Existing coverage mapping — no new test added

| 0.6 predicate (§5.7.1) | Existing deterministic coverage | Status |
|---|---|---|
| ReturnRequired remains the order state after later mismatching evidence | `runtime/crates/kix-kernel/tests/contract_edge_cases.rs::return_required_is_stable_under_further_late_evidence` (asserts `state == ReturnRequired` after the mismatching event) | sufficiently covered |
| A `Review` observation outcome does not replace the order state | same test (`observe_capture` returns `ObservationOutcome::Review` while the order stays `ReturnRequired`) | sufficiently covered |
| review_required coexists with ReturnRequired | same test (`reviewed.review_required` is true with `state == ReturnRequired`) | sufficiently covered |
| The retained capture is not erased by either marker | same test (`captured == Some(order.amount)` after both later events) | sufficiently covered |
| No second inventory release from later evidence | same test (`remaining() == 10` and `!inventory_owned` after each later event) | sufficiently covered |
| Matching duplicate evidence stays duplicate-effect handling and does not clear review or the return obligation | same test (`DuplicateEffect`, state and capture unchanged) plus `transitions.rs::reviewed_late_capture_keeps_return_marker_and_review_requirement` and `quarantine_capacity.rs::original_event_and_command_replays_never_clear_quarantine` | sufficiently covered |
| Review/ReturnRequired release, refund execution, slot release | out of 0.6 scope by construction; 0.6 grants no release authority | not covered, not claimed |

Every material predicate of the clarification is already asserted by existing
deterministic regressions, so no test was added. Adding a near-copy of
`return_required_is_stable_under_further_late_evidence` would raise the test
count without covering a new predicate, which `AGENTS.md` §6/§7 disallows.

## Commands actually run and their results

Local machine, `rustc 1.98.1 (48a229cea 2026-09-01)` / `cargo 1.98.1 (797e8a9bc 2026-08-05)`
matching `rust-toolchain.toml`.

| Command | Result |
|---|---|
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --test contract_edge_cases` | ok — 8 passed, 0 failed (including `return_required_is_stable_under_further_late_evidence`) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | ok — 67 passed, 0 failed (contract_edge_cases 8, contract_invariants 3, e4_state_model 4, observation_slots 11, performance_harness 1, quarantine_capacity 8, transitions 32, lib/doc 0) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | ok — 117 passed, 0 failed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0, no warnings |
| `python3 scripts/verify_runtime_architecture.py` | `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified` |

Local limitation: this machine has Python 3.10 only, while `scripts/bootstrap.sh`
requires Python 3.12 (with Node 24 and a Sui install) for the full protocol
pipeline. `scripts/verify_runtime_architecture.py` was therefore run with a
`tomli`-backed `tomllib` shim on `PYTHONPATH` (the shim was deleted afterwards
and is not part of the change). `verify_runtime.py`, `verify_commerce.py`,
`verify_canonical.py`, the storage probes, the localnet journeys and the zk
fixture steps were not run locally; they are covered by the exact-head
`KIX protocol verification` run reported in the PR closure summary. Since this
change touches only Markdown, no Rust/Python/TS/Move input of those jobs changed.

## Exact-head CI

The exact final task head and both required workflow runs
(`KTX kernel verification`, `KIX protocol verification`) are reported in the PR
#22 closure summary rather than in a further commit, per `AGENTS.md` §11.

## Not tested / non-claims

- No claim that the kernel implements review resolution, ReturnRequired release,
  refund authorization or refund execution. 0.6 grants none of those.
- No claim about durability, crash recovery, distributed fencing, bank
  exactly-once semantics, chain finality, legal compliance or production
  readiness. All evidence here is in-memory and single-process.
- No claim that CI from the base commit or from an earlier task head applies to
  the final head.
- No claim that the kernel behavior changed: the kernel blob is identical to the
  locked value, and the observed behavior already matched the clarified rule.
- No claim that the open-input table advanced; 0.6 completes no open input row.

## Remaining uncertainty and follow-up candidates

- Release paths remain undefined in an executable sense: how review is resolved,
  how ReturnRequired is discharged, and how a reserved slot or retained evidence
  is reclaimed are deferred to later authorized tasks (§5.8 conditions stand).
- The interaction between an order that is simultaneously `ReturnRequired` and
  quarantined and any future bulk/GC or index work is unmodelled.
- `CONTRACT_INVARIANTS.md` anchors still pin pre-0.5 blobs at an older commit; a
  separate task could refresh that anchor table deliberately rather than as a
  side effect of a version bump.
