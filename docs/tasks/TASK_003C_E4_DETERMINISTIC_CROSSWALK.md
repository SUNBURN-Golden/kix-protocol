# KIX Task 003-C — E-4 deterministic ↔ property cross-validation

## Status

- Task ID: `003-C`
- Execution session: **new session required**
- Task document: immutable once execution starts
- Repository-wide rules: follow root `AGENTS.md`

## Objective

Close the validation boundary deliberately left by Tasks 001 and 003-B.

Task 001 added eight contract-derived deterministic edge cases in
`runtime/crates/kix-kernel/tests/contract_edge_cases.rs`. Task 003-B then added
relation-aware generated coverage P1–P7, but explicitly did **not** map those
eight deterministic cases to the generated/reference-model evidence.

Task 003-C must now:

1. map each of the eight Task 001 deterministic edge cases to the exact merged
   Task 003-B property/reference-model relations and observed coverage classes;
2. distinguish **sufficiently cross-validated**, **partially cross-validated**,
   and **not cross-validated** predicates;
3. identify the exact semantic gap for every partial/missing row;
4. add only the smallest genuinely missing **generated/model cross-validation
   anchors** needed to close those gaps;
5. emit an auditable deterministic ↔ property crosswalk with actual witness
   counts/evidence.

This is a **test/evidence task only**. It must not change production/runtime
semantics.

Do not mechanically copy the eight deterministic traces into the property
suite. Cross-validation must come from the existing reference-model/property
path or from narrowly added relation-aware generated witnesses.

## Base

- Requested base SHA: `6332bca0f54cc2114d986b24ab218ace33a5df12`
- This is the ordinary merge commit for Task 003-B.
- At task bootstrap, `main` was independently observed at the same SHA; no drift.
- At session start run `git fetch origin main` and record exact `origin/main`.
- If `origin/main` differs, report the delta before editing. Do not silently
  rebase, merge main into the task branch, or change the task base.

### Task 003-B closure precondition

Task 003-B is closed under `AGENTS.md` §13:

- merge commit: `6332bca0f54cc2114d986b24ab218ace33a5df12`;
- main/push KIX protocol verification run `35448485847`: `completed / success`;
- run event / branch / head: `push` / `main` /
  `6332bca0f54cc2114d986b24ab218ace33a5df12`;
- locked kernel blob on the merge/current-main tree:
  `69564b166f0c27f9af5d8422f0a466b18d74c20f`;
- locked quarantine regression blob:
  `b607996c83a119c349f1cc90469ac1ba82764e20`.

Before editing Task 003-C outputs, independently confirm the base/current-main
relationship and both locked blobs.

## Mandatory reading

Follow root `AGENTS.md`, then read at minimum:

- `README.md`
- `docs/DEVELOPMENT_PLAN.md`, especially the current E-4/R1 validation scope
- `docs/status/BASELINES.md`
- `docs/decisions/AUTHORITY_MODEL_1.md`
- this Task document
- `docs/adr/0001-ktx-authority-commit-recovery.md` §§3, 5, 6
- `docs/contracts/CONTRACT_INVARIANTS.md` §§3–5
- `docs/contracts/STATE_LIFECYCLE.md` 0.6, especially §5.7.1
- `runtime/crates/kix-kernel/README.md`
- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
- `runtime/crates/kix-kernel/tests/e4_state_model.rs`
- `runtime/crates/kix-kernel/tests/support/model_v4.rs`
- `runtime/crates/kix-kernel/tests/support/coverage_v4.rs`
- `runtime/crates/kix-kernel/tests/observation_slots.rs`
- `runtime/crates/kix-kernel/tests/transitions.rs`
- locked `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
- `validation/2026-09-18-contract-edge-cases/README.md`
- `validation/2026-09-19-task-003a-e4-model-schema/README.md`
- `validation/2026-09-19-task-003b-e4-property-expansion/README.md`

## Frozen deterministic source set

The Task 001 deterministic corpus is exactly these eight tests and must remain
unchanged by this task:

1. `rejection_replay_stays_immutable_after_the_blocking_hold_is_released`
2. `altered_payload_conflicts_before_fence_and_clock_guards`
3. `replay_lookup_is_guarded_by_scope_and_semantics_only`
4. `expiry_instant_is_treated_consistently_by_every_entry_point`
5. `unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot`
6. `return_required_is_stable_under_further_late_evidence`
7. `bound_quarantine_survives_owner_change_expiry_and_cancellation`
8. `retained_unbound_conflict_bans_the_identity_for_any_future_order`

Do **not** edit `contract_edge_cases.rs` merely to make the crosswalk easier.
Do not import its helper functions or replay its exact traces as property
fixtures.

## Existing Task 003-B property families

The merged relation-aware suite deliberately covers:

- P1 — command identity / replay / altered payload;
- P2 — explicit operation binding and reuse;
- P3 — first-capture slot lifecycle;
- P4 — event identity versus economic-operation identity;
- P5 — quarantine / retained-unbound evidence;
- P6 — ReturnRequired / review orthogonality;
- P7 — observation-budget relational accounting.

The merged Task 003-B evidence reports all required classes reached, with
86,016 relation-directed compared transitions and zero relation-property/kernel-
model failures, while preserving the historical 131,072-transition baseline.
Those counts establish non-vacuous reachability, **not** that every Task 001
predicate has already been cross-validated.

## Required crosswalk

Produce one stable matrix with one row per Task 001 test. At minimum each row
must record:

| Field | Required meaning |
|---|---|
| deterministic test | exact Task 001 test name |
| contract predicate | the precise semantic proposition the deterministic test asserts |
| relevant family | P1–P7, one or more |
| existing property classes | exact `coverage_v4` class names that bear on the predicate |
| generated witness | exact family/config/seed/step or deterministic aggregate evidence proving the relevant path is actually reached |
| strength | `sufficient`, `partial`, or `missing` |
| gap | exact semantic distinction not proved by existing property evidence; `none` if sufficient |
| added anchor | exact new generated/model anchor, if any; otherwise `none` |
| post-anchor evidence | actual count/witness after the task |

Do not call a row `sufficient` merely because it belongs to the same broad
P-family. The generated witness must establish the material predicate, including
relevant ordering/boundary/identity distinctions.

### Initial semantic regions to verify independently

These are mapping hints, not pre-approved conclusions. Confirm them from code
and evidence before assigning strength:

1. rejected-result replay after the cause disappears → primarily P1;
2. altered payload versus stale fence/regressed clock precedence → P1;
3. replay lookup scope/semantics versus fence/clock precedence → P1;
4. exact expiry boundary across reserve/expire/send/capture → lifecycle behavior
   spanning P3/P6 and model transition semantics;
5. UNKNOWN retry at/after deadline while preserving reserved slot/inventory →
   P3, with P6/P7 only where the evidence actually bears on the predicate;
6. duplicate/mismatching evidence after ReturnRequired → P4/P6;
7. bound quarantine stickiness across owner/expiry/cancellation → P5;
8. retained-unbound operation ban plus sibling-operation independence → P2/P5
   (and P4 only for the conflict evidence identity path).

## What counts as a genuine missing anchor

A new anchor is justified only when the existing Task 003-B observer/corpus does
not distinguish a contract-significant predicate of a Task 001 case.

Examples of legitimate gaps, **if confirmed**:

- a counter merges two materially different guard-precedence cases that Task 001
  distinguishes;
- generic `replay_after_state_changed` does not prove that the original
  rejection's blocking cause specifically disappeared before replay;
- generic expiry/slot reachability does not prove the exact
  `now_ms == expires_at_ms` boundary required by the contract;
- one class proves a sticky fact but not the ordered transition sequence that
  the deterministic predicate requires.

Preferred remedy, in order:

1. reuse an already generated witness and expose/audit it more precisely;
2. add a more precise **observer class/counter** for an already generated path;
3. minimally steer an existing relation-aware family so that the missing
   semantic path is generated reproducibly;
4. only if necessary, add a small test-only crosswalk support helper.

Do not add a fixed copy of the Task 001 trace simply to obtain a second green
test.

## Cross-validation design constraints

- Preserve the historical baseline generator and its parameters unchanged.
- Preserve Task 003-B's existing P1–P7 required classes and evidence behavior;
  new anchors are additive.
- Preserve existing seeds/configurations unless a narrowly documented extra
  corpus is necessary for a missing anchor.
- New evidence must be deterministic and auditable from explicit
  family/config/seed/step or equivalent stable witness identity.
- If a witness is already present in the merged corpus, prefer extracting it to
  generating another corpus.
- Do not treat the source-informed reference model as clean-room independent.
- Cross-validation means two different validation shapes agree on the same
  contract predicate; it is not a formal proof of correctness.

## Authorized paths

Expected implementation scope is limited to test/evidence paths such as:

- `runtime/crates/kix-kernel/tests/e4_state_model.rs`
- `runtime/crates/kix-kernel/tests/support/coverage_v4.rs`
- optionally one narrowly scoped new support file under
  `runtime/crates/kix-kernel/tests/support/` if materially needed
- one new validation note under
  `validation/2026-09-20-task-003c-e4-deterministic-crosswalk/`

`runtime/crates/kix-kernel/tests/contract_edge_cases.rs` is an input corpus for
this task and should not be changed.

`runtime/crates/kix-kernel/tests/support/model_v4.rs` should remain unchanged;
Task 003-C is not a reference-model schema/semantics task. If the crosswalk
appears to require changing model semantics, stop and classify why rather than
silently broadening scope.

The executing agent must not modify this Task document.

## Absolute prohibitions for Task 003-C

In addition to root `AGENTS.md`, do not:

- modify `runtime/crates/kix-kernel/src/lib.rs`;
- modify locked `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`;
- modify this Task document;
- change `contract_edge_cases.rs` to fit the property model;
- change production/kernel semantics;
- change reference-model semantics to mimic a kernel result;
- implement review resolution, ReturnRequired discharge, slot release,
  lifecycle GC/index;
- implement R2 or custom replication/storage/logging;
- integrate PR #11 integration (a);
- perform live PG/bank/Sui production execution;
- alter CI merely to make this task pass;
- do unrelated hygiene, renaming, performance work or repository settings work;
- mark the draft PR ready or merge it without new explicit human approval.

## Contract discrepancy handling

Follow `AGENTS.md` §8 exactly.

If cross-validation exposes an explicit contract-defined mismatch:

- create the smallest useful reproduction in an allowed test/evidence path;
- preserve the locked files;
- mark the task blocked;
- do not make the model/property checker imitate the kernel;
- do not report merge-ready.

If behavior is contract-undefined, label it characterization/remaining
uncertainty rather than inventing semantics.

## Verification

At minimum:

1. independently verify Task 003-B post-merge closure and exact base;
2. verify both locked blobs before editing;
3. run the eight Task 001 deterministic tests unchanged;
4. run the preserved historical E-4 baseline suite;
5. run the merged Task 003-B relation-aware P1–P7 suite before modification and
   inventory the existing witnesses relevant to all eight rows;
6. implement only confirmed missing anchors;
7. run the crosswalk/anchor verification and emit the stable eight-row matrix;
8. rerun the relation-aware suite and verify all original P1–P7 required classes
   still reach their gates;
9. run existing oracle-sensitivity/shrink tests unchanged;
10. run the full kernel suite and runtime workspace tests;
11. run `cargo fmt --check` and kernel/workspace Clippy with `-D warnings`;
12. run runtime architecture gate/tests where practical;
13. verify both locked blobs after changes;
14. verify exact final-head **KTX kernel verification** and **KIX protocol
    verification** are both `completed / success`.

Record exact commands and actual results. Do not infer success from an older SHA.

## Acceptance criteria

Task 003-C is complete only when:

- [ ] observed `origin/main` is recorded and any drift from requested base is reported;
- [ ] Task 003-B post-merge closure is independently confirmed;
- [ ] this Task document is unchanged by the executing agent;
- [ ] both absolute locked blobs remain exact;
- [ ] `contract_edge_cases.rs` remains unchanged;
- [ ] `model_v4.rs` semantics remain unchanged;
- [ ] all eight Task 001 tests have explicit deterministic ↔ property/model rows;
- [ ] every row cites exact existing property classes and actual generated evidence;
- [ ] every row is classified `sufficient`, `partial`, or `missing` before new anchors;
- [ ] every partial/missing row states its exact gap;
- [ ] only genuinely missing anchors are added;
- [ ] no deterministic Task 001 trace is mechanically copied as a property fixture;
- [ ] post-anchor evidence proves each intended cross-validation predicate is actually reached;
- [ ] original Task 003-B P1–P7 coverage gates remain green and historical baseline remains reproducible;
- [ ] existing sensitivity/shrink checks remain effective;
- [ ] no production/kernel or reference-model semantics changed;
- [ ] relevant local verification passes;
- [ ] exact final-head KTX CI is completed/success;
- [ ] exact final-head KIX protocol CI is completed/success;
- [ ] contract violations/undefined characterizations and non-claims are reported;
- [ ] PR remains draft/unmerged pending new human approval.

## Evidence requirements

Final report must include:

- exact requested base, observed `origin/main`, pre-session branch head,
  implementation head and exact final head;
- full-PR changed paths and executing-session changed paths if different;
- Task 003-B closure verification, including main/push run ID;
- locked blobs before/after;
- unchanged blob for `contract_edge_cases.rs` and unchanged reference-model
  semantics;
- the complete eight-row crosswalk;
- pre-anchor classification and exact gap for each row;
- every new anchor and why existing coverage was insufficient;
- family/config/seed/step or other stable witness for each mapped predicate;
- pre/post relevant coverage counts;
- preserved historical baseline parameters/results;
- sensitivity/shrink results;
- commands actually run and actual results;
- exact-head KTX and KIX protocol run IDs/status/conclusion;
- any contract violation or undefined characterization;
- explicit non-claims and remaining uncertainty.

## Non-claims

Task 003-C does not establish:

- clean-room independence of the reference model or test authorship;
- formal verification or exhaustive correctness;
- durability, persistence or crash recovery;
- distributed fencing/consensus correctness;
- chain authority/finality;
- bank/PG exactly-once or refund execution;
- concurrency, throughput or latency properties;
- future lifecycle release/GC/index correctness;
- production or staging readiness.

## Closure boundary

Green CI means only `merge-ready`. It does not authorize draft removal or
merge. A new explicit human approval is required before Task 003-C may be
marked ready or merged. If later merged, follow `AGENTS.md` §13 post-merge
verification before closing Task 003-C.