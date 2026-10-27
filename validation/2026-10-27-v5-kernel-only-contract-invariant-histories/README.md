# v5-kernel-only-contract-invariant-histories — INV-1..INV-5 over kix-kernel-v5, including terminate, hold and reclaim report

Node: `plan-v5-kernel-only-contract-invariant-histor`. Not an ASTRA program-mode
session. No issue (`issue: none` in the node input). `depends_on: []`, audit
floor A2, `astra_gate: None`, `user_merge: false`.
Source: KIX planner run 1793078707 (loop-proposed node, not in `.aiops/program.json`).

This session did not commit, push, open a pull request, create or close an
issue, or comment anywhere. There is no implementation head SHA, no final task
head SHA, and no KTX kernel verification or KIX protocol verification run ID for
a head containing these files.

`git fetch origin main` then `git rev-parse origin/main HEAD`: both
`9d50fb660248b66a5959f48f7dc96e68c9d5530b`. No base delta. Branch
`agent/kix-plan-v5-kernel-only-contract-invariant-histor`.
`rustc 1.98.1 (48a229cea 2026-09-01)`, `python3` 3.13.5.

Locked blobs, before and after the edits (`git hash-object`):

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

## Changed paths

| Path | Change |
|---|---|
| `runtime/crates/kix-kernel-v5/tests/contract_invariants_v5.rs` | New. Seeded generator, public-getter view, INV-1..INV-5 predicates, INV-3 replay probes, corpus test, five sensitivity tests. |
| `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md` | This record. |
| `docs/README.md` | One index bullet under `2026-10-27 검증 기록 색인`, required by `check_docs_index.py`. |

No change to `runtime/crates/kix-kernel-v5/src/**`, `kix-kernel-v5/Cargo.toml`,
`runtime/Cargo.lock`, `runtime/crates/kix-kernel/**`, `reference/v0.3-rc1/**`,
`.aiops/`, `.github/`, `docs/tasks/`, `docs/contracts/**` or `docs/status/**`.
No contract, evidence-map status or capability grade changes. The test imports only
`kix_kernel_v5`, `kix_types` and the crate's `tests/common` helpers (`amount`,
`closure`, `human`). It does not import `lifecycle_model.rs`, `v4_differential.rs`
or the v4 `kix_kernel` crate. `rg -n 'lifecycle_model|v4_differential|kix_kernel::'`
matches only the header comment line that says so.

## What the test does

Every history runs on one v5 `Kernel` and uses only its public API. There is no
reference model, no reply oracle and no state machine. No reply is predicted.
Stimuli depend only on the seed, inputs already emitted, and public getters
(`order`, `operation_snapshot`, `termination`). The getters are used to choose
targets for send and terminate, never to compute an expected reply.

**Prefix (14 steps, identical in every history).**

1. Reserve a, send a, capture a (event 500).
2. Reserve b, then the same capture again.
3. A conflicting capture under the same event id for b's operation.
4. Reserve c (expiry 9), send c.
5. Terminate c with a human decision on the current `operation_snapshot`, all
   five flags true.
6. A late capture of c at time 10. This is after c's expiry and after its
   termination (LC-TERM §5.6).
7. Place a hold on a, clear it, place a hold on c, then one `reclaim_reports`.

Vacuity guards then assert, on observed state only:

- a capture was retained;
- a termination was recorded;
- a captured order is also terminated;
- a hold was placed and cleared.

**Seeded phase (114 steps).** Time is `index + 20`. Slot `index % 16` picks the
input:

| Slot | Input |
|---|---|
| 0–2 | `reserve`. About 1 in 13 has a zero amount. About 1 in 7 (slots 0–1) binds the same payment to another order id. Slot 2 is sent with `semantics_version` 4. |
| 3 | `mark_payment_unknown`. Half aim at the latest Held order. |
| 4 | Fresh capture. |
| 5 | Duplicate of the first capture. |
| 6 | Same event id with another operation and amount. |
| 7 | `expire`. |
| 8 | Exact replay of a's reserve with the stale `ctx(1, generation 1)`. |
| 9 | `replace_owner`. |
| 10 | `terminate`. Current snapshot (weight 3), stale snapshot, one false condition, `ActorKind::Automatic`, exact replay of a recorded decision, the same decision with a changed `rule_hash`, or an unknown order. |
| 11 | `place_hold`. Hold ids 200–205, all three kinds, two placers. |
| 12 | `clear_hold`. |
| 13 | `reclaim_report`. `now` is the largest emitted time plus 0–2, or 0 one time in eight. |
| 14 | `reclaim_reports`. |
| 15 | `cancel_scope` when `index > 85`, otherwise a capture under a new event id for a. |

**After every main step** the test does the following:

1. It builds a `View` from public getters over every attempted order id:
   - the orders;
   - `remaining`, `order_count`, observation, conflict, reserved-slot and
     quarantine counts;
   - `termination(id)`, `hold(id)`, and `reclaim_reports(max emitted time).terminated_records`.
2. It checks the five predicates as CONTRACT_INVARIANTS §3 states them:
   - **INV-1.** The order count matches. No seat has two `inventory_owned` owners.
     No segment crosses the aisle. `used + remaining == total`, with GA sums in
     `u64`.
   - **INV-2.** The checked sum `events + conflicts + reserved` is at most the
     observation bound. `order_count` and recorded command first results stay
     within their limits. The quarantine count is at most `order_count`. Class B
     v5 extension: `terminated_records == terminations` and both termination and
     hold records are at most `order_count`.
   - **INV-3.** Every recorded `Termination` is still returned unchanged by
     `termination(order)`. Every placed hold still shows its first placement.
   - **INV-4.** No two observed orders share a payment operation. No operation
     has more than one `None→Some` capture transition. A capture may appear only
     on a capture input for that operation, so terminate, hold and report steps
     never create one. A repeated capture leaves inventory ownership unchanged.
   - **INV-5.** Every retained capture is still present on the same order, with
     the same operation and an identical `AssetAmount` (asset, atoms, registry
     version, hash). This holds across terminate, hold place/clear and report
     steps (LC-FACT §3, LC-TERM §5.6).
3. A main-step reserve, terminate or place_hold that returns `replayed: true`
   must equal the recorded first result. A new `Ok` becomes the first result.
4. Report steps must leave the kernel `==` its pre-step clone. A terminate `Err`
   must also leave the kernel unchanged (class B, see below).
5. It runs the INV-3 read-only replay probes with the **original** context:
   - every reserve first result, including rejections;
   - every termination decision;
   - every currently placed hold.

   Each probe requires the recorded reply with `replayed: true`, an unchanged
   public view, and an unchanged whole-kernel `Eq` sentinel. The sentinel is the
   only observable for the private admitted time. The predicates are then
   checked again.

## Corpus, seeds and step counts

| Fixture | Inventory | Limits (commands, orders, observations) | Seeds | Steps | Applied terminations |
|---|---|---|---|---|---|
| F0 | seats `[65, 5]` | 48, 24, 24 | 1..=32 | 4,096 | 55 |
| F1 | seats `[65, 5]` | 8, 4, 3 | 1..=32 | 4,096 | 32 |
| F2 | GA 6 | 48, 24, 24 | 1..=32 | 4,096 | 47 |
| F3 | GA 6 | 8, 3, 3 | 1..=32 | 4,096 | 32 |

Totals from the passing run (`--nocapture` output):

- 128 histories × 128 steps = **16,384 main steps** (asserted exactly);
- 134,263 read-only replay probes;
- 313 retained capture facts;
- 166 applied terminations: 128 from the prefix and 38 seeded;
- 134 terminated orders that also carry a retained capture;
- 280 holds cleared;
- main-step replays: reserve 896, terminate 114, place_hold 8.

Per-family calls and `Ok` replies (every family ran and succeeded at least
once; asserted):

| Family | Calls | Ok |
|---|---|---|
| reserve | 4,224 | 2,098 |
| send (`mark_payment_unknown`) | 1,152 | 337 |
| expire | 896 | 201 |
| observe_capture | 3,840 | 2,276 |
| replace_owner | 896 | 896 |
| cancel_scope | 256 | 256 |
| terminate | 1,024 | 280 |
| place_hold | 1,152 | 406 |
| clear_hold | 1,024 | 280 |
| reclaim_report | 896 | 503 |
| reclaim_reports | 1,024 | 1,024 |

In F1 and F3 the prefix already fills the order limit, so their seeded reserves
are rejected and no seeded termination applies there. Those fixtures exercise
the tight observation budget instead.

## Sensitivity fixtures

Each test first asserts that the real view or probe passes. It then asserts that
a deliberately corrupted observer copy fails with the predicate's prefix. Last,
it asserts that the kernel equals its snapshot, so no kernel was mutated. These
fixtures follow the style of INV-3's F-B2 fixture.

| Test | Corrupted copy |
|---|---|
| `inv1_rejects_corrupted_overlap_and_conservation_views` | Extra order overlapping an owned seat (seat fixtures). `remaining - 1` (all four fixtures). |
| `inv2_rejects_corrupted_budget_and_termination_count_views` | `events = bound + 1`. `terminated_records + 1`. |
| `inv3_rejects_corrupted_reserve_terminate_and_hold_replay_probes` | For reserve, terminate and hold probes: another original, `replayed: false`, `Err(CommandConflict)`, a changed `after` view, a false Eq sentinel. Rewritten saved first results (reserve outcome, `applied_at_ms + 1`, `placed_at_ms + 1`) re-probed on the real kernel. Corrupted `terminations`/`holds` in the view. |
| `inv4_rejects_corrupted_rebinding_and_double_capture_views` | Second order bound to an existing payment. Capture-transition count 2. |
| `inv5_rejects_corrupted_capture_on_terminated_and_held_orders` | On the terminated, held, late-captured order c (all four fixtures): capture removed, different atoms, same atoms under a different asset id. |

**Scratch negative control (not committed).** I copied `runtime/` with
`tar --exclude=target` into `/tmp/civ5_scratch` and deleted the copy afterwards.
Two separate one-line mutations of the copy's `kix-kernel-v5/src/lib.rs` were
each run with
`cargo test --manifest-path /tmp/civ5_scratch/runtime/Cargo.toml -p kix-kernel-v5 --test contract_invariants_v5 --locked five`:

| Mutation | Result |
|---|---|
| M1: the decision-replay path of `terminate` returns `replayed: false` | Failed at call 8: `INV-3 replay reply differs from recorded first result; terminate` |
| M2: `place_hold` clears the order's `captured` | Failed at call 10 (the prefix hold on a): `INV-5 captured fact changed or disappeared` |

## Existing coverage (AGENTS §7)

| Requirement | Class before | Existing tests | What this file adds |
|---|---|---|---|
| Termination once, decision replay, conflicts, automatic/false/stale rejections, send blocked after termination | sufficiently covered (fixed cases) | `termination.rs` (13) | the same commands inside INV-1..INV-5 histories |
| Hold kinds, replay, conflicting reuse, explicit clear | sufficiently covered (fixed cases) | `holds.rs` (9) | hold placement as an INV-3 first result while placed; INV-5 across hold changes |
| Report shape and read-only property | sufficiently covered | `reclaim_report.rs` (13), `reclaim_batch.rs` (6) | report steps checked as read-only (kernel `==` clone) inside the histories |
| Terminate/hold/report release no slot, inventory, review or evidence | sufficiently covered | `stopped_transitions.rs` (5) | INV-2/INV-5 stay true after each such step |
| Seeded v5 lifecycle agreement with an oracle | sufficiently covered (oracle-based) | `lifecycle_model.rs` (1) | none; this file has no oracle and stays separate |
| Shared-command equivalence with v4 | partially covered | `v4_differential.rs` (3), `conflict_index.rs` (4) | none; not a differential |
| INV-1..INV-5 over generated histories | covered for v4 only | `runtime/crates/kix-kernel/tests/contract_invariants.rs` | — |
| Seeded INV-1..INV-5 over v5 including terminate, hold and reclaim report | not covered | none | this file |

## Discrepancy classes (AGENTS §8)

**No class C was found.** All six tests pass on the unchanged v5 kernel, so the
file holds no `#[ignore]` reproduction.

**Class B rationale.** CONTRACT_INVARIANTS (title and §1–§3) is scoped to the
locked v4 kernel. Applying its predicates to v5 is a characterization, not a
contract claim. No contract text, `CONTRACT_INVARIANTS_EVIDENCE_MAP.md` row or
v5 source is changed. Class B notes:

- **Hold replay.** A hold placement replays to its first result only while the
  hold is placed. After `clear_hold`, a delayed identical placement re-places it,
  per the `ClearedHold` doc comment. The observer therefore drops the record on
  a successful clear.
- **Clear reply.** A successful `clear_hold` is asserted to report the placement
  it removed.
- **Terminate errors** are asserted to change no state, per the `terminate` doc
  comment. They therefore have no first result to record.
- **INV-2 v5 extension.** The equalities and bounds on `terminated_records`,
  terminations and holds go beyond INV-2 as written for v4.
- **INV-3 persistence.** "A recorded termination is still returned by
  `termination(order)`" and "a placed hold keeps its first placement" are applied
  as INV-3 first-result persistence. The v4 contract has no such commands.
- **"Send"** means `mark_payment_unknown`, as in the v4 `contract_invariants.rs`.
  It is not a new command.

**Non-independence.** The author knew the v5 source. The test is source-informed,
not clean-room. Passing predicates and agreement can share a mistake with the
implementation.

## Commands and results

All run from the node worktree in the foreground.

| Command | Result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD` | both `9d50fb660248b66a5959f48f7dc96e68c9d5530b` |
| `git hash-object` on the two locked paths (start and end) | `69564b16…`, `b607996c…`, unchanged |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --test contract_invariants_v5 --locked -- --nocapture` | exit 0. 6 tests pass. Counts above. About 3.2 s on this host (not a timing claim). |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --locked` | exit 0. 62 tests: boundary 2, conflict_index 4, contract_invariants_v5 6, holds 9, lifecycle_model 1, reclaim_batch 6, reclaim_report 13, stopped_transitions 5, termination 13, v4_differential 3 |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked` | exit 0. 122 passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | exit 0. 44 result lines, 317 passed, 0 failed |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | exit 0. The first run flagged `large_enum_variant` on the test's `Reply` enum; the termination reply was boxed and the rerun is clean. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel-v5 --edges normal --locked` | `kix-kernel-v5` → `kix-types` only |
| `python3 scripts/verify_runtime_architecture.py`; `python3 scripts/test_runtime_architecture.py` | exit 0 (`architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`); exit 0, 7 tests OK |
| The 27 plain checker commands of the protocol.yml "Stdlib offline document checks" step, each also with `--self-test`, plus `check_stage5_host.py --self-test` | all exit 0, including `check_docs_index`, `check_contract_invariants_evidence_map`, `check_v5_transition_evidence_map`, `check_lifecycle_adr_evidence_map`, `check_evidence_map_rollup` and `check_ci_checker_wiring` |
| `git diff --exit-code origin/main -- runtime/crates/kix-kernel-v5/src runtime/crates/kix-kernel runtime/crates/kix-kernel-v5/Cargo.toml runtime/Cargo.lock reference/v0.3-rc1 .aiops .github docs/tasks docs/contracts docs/status` | exit 0, empty. `git status --short` names only the three changed paths above |
| Scratch negative controls M1 and M2 (above) | each fails as required |

Not run (environment limits; none reads the new test file):

- `.venv` steps: `verify_runtime.py`, commerce, canonical, paid storage, localnet;
- Node SDK and ZK steps;
- Move tests;
- `sui`;
- the `ktx-kernel.yml` and `protocol.yml` workflows themselves.

No CI evidence is claimed.

## CI (AGENTS §10, §14)

- Exact-head KTX kernel verification run: none, because no commit exists.
- Exact-head KIX protocol verification run: none, because no commit exists.
- Merge commit and post-merge main CI: not applicable.

This record claims `merge-ready` for nothing. The node is implemented and
verified locally. It still needs exact-head CI, non-author A2 review and the
User's merge decision.

## Non-claims

This record makes none of these claims:

- clean-room independence;
- durability, distributed fencing, bank exactly-once or settlement;
- chain finality, legal compliance or production readiness;
- lifecycle release: slot release, review release, record reclamation or evidence deletion (none exists in v5);
- any retention policy. Only `ReclaimPolicy::default()` is read and no policy value is chosen; I09, I10 and I13 stay open.

Termination here is the in-memory record, not a durable approval. No provider
fact was evaluated and no principal was authenticated. "Capture" means the
kernel's retained fact under trusted-input assumptions, not verified bank
settlement. Finite seeded histories are not a proof of completeness. Local
success is not exact-head CI and not merge authorization.

## Follow-up candidates

- In a separate node, cite these tests in `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md`
  (or a v5 map), keeping the class B scope note.
- If v5 gets its own invariant contract, promote the class B extensions above
  (hold-replay window, termination/hold record bounds) to contract text through
  an authorized contract change.
