# KIX Task 003-A — E-4 reference-model state schema expansion

## Status

- Task ID: `003-A`
- Execution session: new session required
- Task document: immutable once execution starts
- Repository-wide rules: follow root `AGENTS.md`

## Objective

Strengthen the existing E-4 sequential reference model by making the model state explicitly represent the relationships that are currently only implicit or partially represented:

- event identity → provider operation;
- provider operation → bound order;
- bound versus retained-unbound quarantine/blocking;
- first-capture observation-slot reservation and consumption;
- primary order lifecycle state versus orthogonal review/quarantine state;
- retained economic capture/effect state.

This task is a **reference-model schema task**. It is not the generator/property-corpus expansion task.

The purpose is to make the oracle capable of representing the contract boundaries exposed by Task 001 and clarified by STATE_LIFECYCLE 0.6 before Task 003-B expands generated transition sequences.

## Base

- Requested base SHA: `db02ae11bf4a1d7705f31b328c627714f91e1c78`
- This is the ordinary merge commit for Task 002 / STATE_LIFECYCLE 0.6.
- At session start run `git fetch origin main`.
- Record exact `origin/main` and report any drift.
- Do not silently rebase, merge main into the task branch, or change the base.

### Task 002 closure precondition

Task 002 post-merge verification is already recorded:

- merge commit: `db02ae11bf4a1d7705f31b328c627714f91e1c78`
- main/push KIX protocol run `35408175012`: completed / success
- reviewed merged-content KTX run `35406674412`: completed / success
- KTX workflow is PR-triggered only and therefore has no push run for the merge commit.

Before editing Task 003-A outputs, independently confirm that the current repository still reflects this base and that the two locked blobs are unchanged.

## Mandatory task-specific reading

Follow root `AGENTS.md`, then read:

- `docs/DEVELOPMENT_PLAN.md` §6.1
- `docs/contracts/CONTRACT_INVARIANTS.md`, especially §§1, 3 and 5
- `docs/contracts/STATE_LIFECYCLE.md` 0.6, especially §2, §3 and §5.7.1
- `runtime/crates/kix-kernel/README.md`
- `runtime/crates/kix-kernel/tests/e4_state_model.rs`
- `runtime/crates/kix-kernel/tests/support/model_v4.rs`
- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
- `runtime/crates/kix-kernel/tests/observation_slots.rs`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
- `validation/2026-09-18-contract-edge-cases/README.md`
- `validation/2026-09-19-task-002-lifecycle-precedence/README.md`

## Existing model limitations to address

The current source-informed model already represents orders, stored events, retained conflicts, promised first-capture capacity and quarantined operations, but several relationships are implicit:

1. operation → order binding is recovered by scanning `orders`;
2. retained-unbound operation bans are inferred from retained conflict observations;
3. reserved first-capture slots are represented as a flat `promised: Vec<ProviderOperation>`;
4. event records do not explicitly expose the event → operation → order relation as model state;
5. bound quarantine and unbound retained blocking are not represented as distinct concepts;
6. lifecycle phase and review are already separate fields, but the schema should explicitly preserve the STATE_LIFECYCLE 0.6 rule that `ReturnRequired` and `review_required` may coexist;
7. observation-budget accounting is computed from aggregate vectors without an explicit relational consistency layer.

Task 003-A must make these model relationships explicit enough that Task 003-B can later generate transitions against them without relying on accidental inference.

## Authorized scope

Expected authorized implementation paths:

- `runtime/crates/kix-kernel/tests/support/model_v4.rs`
- `runtime/crates/kix-kernel/tests/e4_state_model.rs`
- one new narrowly scoped validation note under `validation/`

No production/runtime source file may be changed.

A documentation change outside the validation note is not expected and requires explicit justification. Do not edit this Task document.

## Required schema capabilities

Exact type names are not prescribed. Choose the smallest representation that remains independent of kernel internals.

### A. Explicit operation binding

The reference model must explicitly represent the one-to-one economic binding:

`ProviderOperation ↔ order_id`

Required properties:

- one operation may bind to at most one order;
- one accepted order's payment operation must have the corresponding binding;
- a rejected order must not create a binding;
- retained-unbound conflict evidence must not create a speculative order binding;
- operation reuse rejection must be explainable from explicit binding or retained blocking state, not only by scanning an order row.

The model may retain redundant order input for comparison, but binding must exist as an explicit model relation.

### B. Explicit event relation

Represent accepted/stored event identity separately from economic operation identity.

The model must be able to state, for every stored accepted event:

- canonical event identity used by the current v4 contract (provider/account/event_id boundary);
- full observed payload needed to distinguish identical replay from conflicting reuse;
- provider operation named by the event;
- bound order, when the operation is bound;
- original observation outcome/effect classification required for replay.

Do not collapse event dedupe and economic-operation dedupe into one identity.

### C. Explicit retained-unbound blocking

Represent the distinction exposed by Task 001:

- bound operation quarantine/review;
- retained unbound operation identity that blocks future binding;
- unretained unbound conflict that must **not** create a speculative permanent ban.

The state representation must make this difference directly inspectable rather than relying only on a scan of raw conflict entries.

Any derived blocking index must remain consistent with retained evidence. Do not invent a scope-wide quarantine latch.

### D. Explicit first-capture slot state

Replace or wrap the flat `promised` concept with an explicit model representation for the reserved first-capture observation slot.

The schema must support these facts:

- at most one reserved first-capture slot per bound operation;
- reservation occurs before/with successful send authorization according to current v4 behavior;
- UNKNOWN retry reuses the same reservation;
- owner replacement, expiry checks and cancellation do not release that reserved slot;
- first accepted bound capture consumes the reservation into stored observation/effect accounting;
- unrelated evidence/conflicts cannot consume another operation's reserved slot;
- no terminal release/GC behavior is introduced.

The representation may be a small record or explicit relation; do not implement future slot release.

### E. Primary lifecycle state and orthogonal review

Keep the order's primary lifecycle state and review/quarantine predicate independently representable.

The schema must explicitly allow:

`phase = ReturnRequired` and `review_required = true`

at the same time, consistent with STATE_LIFECYCLE 0.6 §5.7.1.

Do not normalize that combination into `OrderState::Review`.

### F. Retained capture/economic effect

The model must preserve the first retained capture/economic effect independently from later event outcomes.

Required properties:

- first capture amount/effect cannot silently disappear;
- a later matching event is duplicate-effect handling, not a second economic effect;
- a later mismatching event may raise review without overwriting the retained first capture or ReturnRequired;
- inventory ownership may be released at most once by the currently implemented paths.

Use contract-level model concepts, not copies of private kernel maps.

## Schema consistency checks

Add model-side consistency validation that can run after each existing step.

At minimum check applicable invariants such as:

- every explicit binding points to exactly one existing accepted order with the same `ProviderOperation`;
- no two bindings use the same operation or order inconsistently;
- every reserved slot belongs to a bound operation and is unique;
- every bound quarantined operation resolves to a bound order whose review predicate is set;
- every retained-unbound blocked operation has retained conflict evidence supporting the ban and no speculative order binding;
- stored event relations preserve event identity, operation and replay outcome consistency;
- stored observations + retained conflicts + reserved slots remain within the observation budget;
- retained capture/effect agrees with the order projection;
- `ReturnRequired + review_required` is valid and must not be rejected as an inconsistent schema state;
- existing inventory-conservation checks continue to hold.

These checks must not call the Kernel or inspect private kernel state.

## Existing coverage first

Before editing the model, map the current tests to the schema requirements.

At minimum include:

- `contract_edge_cases.rs` 8 Task-001 edge cases;
- `observation_slots.rs`;
- `quarantine_capacity.rs`;
- `transitions.rs` coverage relevant to operation binding, review, replay and late capture;
- existing `e4_state_model.rs` generated differential traces;
- contract-invariant checks INV-1 through INV-5.

Do not duplicate deterministic kernel tests merely to increase test count.

## Generator freeze for Task 003-A

Task 003-A must **not** expand the generated workload.

Do not change, except for minimal compile/schema adaptation if unavoidable:

- `CASES`;
- `STEPS`;
- seed algorithm or seed range;
- action distribution percentages;
- action kinds;
- mutation probabilities;
- shrink algorithm;
- fixture configurations;
- failure-corpus generation policy.

If a minimal mechanical adjustment is needed because a model field/type changed, document it and show that generated input semantics are unchanged.

New model-only schema consistency tests are allowed if they test the new representation itself and do not duplicate an existing kernel behavioral regression.

The actual generator/property expansion belongs to Task 003-B.

## Behavioral preservation requirement

On all pre-existing E-4 traces, the schema-expanded model must preserve the current reference model's externally predicted behavior unless an explicit current contract violation is discovered.

That means, for the unchanged existing generator:

- per-step expected replies remain equivalent;
- public state comparison remains equivalent or stronger;
- existing oracle-sensitivity injection still produces a detectable mismatch and shrink;
- current deterministic regressions remain green.

If the schema refactor itself reveals a disagreement between the old model, the locked kernel and an explicit current contract:

- classify it under root `AGENTS.md`;
- create the smallest useful reproduction;
- do not silently choose the kernel or old model as authoritative;
- block merge if it is an explicit contract violation.

## Independence requirement

The E-4 model remains **source-informed**, not clean-room independent.

Do not make stronger independence claims.

The schema may import public KIX value/types needed to express inputs/results, but:

- do not call `Kernel` from the reference model;
- do not use kernel private state or serialization as the oracle;
- do not clone the kernel's private map/bitmap layout merely for convenience;
- keep independent relation/state representation where practical.

## Additional out-of-scope constraints

Root `AGENTS.md` prohibitions remain in force.

Specifically do not:

- modify `runtime/crates/kix-kernel/src/lib.rs`;
- modify `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`;
- modify Task 003-A document;
- change kernel/runtime semantics;
- expand generator/property transition coverage (Task 003-B);
- add Task-001 deterministic anchor/property crosswalk execution (Task 003-C);
- implement review resolution, ReturnRequired discharge, observation-slot release, lifecycle GC/index;
- implement R2 or PR #11 integration (a);
- add storage/log engines;
- perform live PG/bank/Sui execution;
- perform unrelated cleanup, renaming or CI edits.

## Verification

At minimum:

1. run the existing E-4 state-model suite;
2. run any new model-only schema consistency tests;
3. run `contract_edge_cases`, relevant observation/quarantine regressions and the full kernel suite;
4. run runtime workspace tests;
5. run `cargo fmt --check` and workspace Clippy with `-D warnings`;
6. run the runtime architecture gate/tests where practical;
7. verify both locked blobs before and after;
8. verify exact final-head KTX and full KIX protocol CI.

Report exact commands and actual results.

## Acceptance criteria

The task is complete only when:

- [ ] base is `db02ae11bf4a1d7705f31b328c627714f91e1c78` with no unreported drift;
- [ ] Task 003-A document is unchanged by the executing agent;
- [ ] both locked blobs remain exact;
- [ ] existing coverage was mapped before new tests;
- [ ] operation→order binding is explicit model state;
- [ ] event→operation→order relation is explicit enough to inspect and validate;
- [ ] bound quarantine and retained-unbound blocking are explicitly distinguishable;
- [ ] reserved first-capture slot state is explicit and budget-accounted;
- [ ] retained first capture/economic effect is preserved explicitly;
- [ ] primary phase and review predicate remain orthogonal and support ReturnRequired+review;
- [ ] model-side relation consistency is checked after existing generated steps;
- [ ] existing generator semantics are unchanged;
- [ ] existing oracle-sensitivity detection/shrinking still works;
- [ ] no production/kernel semantics changed;
- [ ] relevant local tests/checks pass;
- [ ] exact final-head KTX CI is completed/success;
- [ ] exact final-head KIX protocol CI is completed/success;
- [ ] evidence/non-claims and remaining uncertainty are reported;
- [ ] PR remains unmerged until explicit human approval.

## Evidence requirements

Final report must include:

- exact base / pre-session branch head / final head;
- complete changed-path list;
- locked blobs before/after;
- current implicit-state → new explicit-schema mapping;
- which fields/relations are authoritative model state versus derived consistency indexes;
- existing coverage map;
- whether any new tests were added and why;
- proof that generator constants/distribution/seeds/shrinker were unchanged;
- existing oracle-sensitivity result;
- local command results;
- exact-head CI run IDs/status/conclusion;
- explicit non-claims;
- remaining model gaps reserved for Task 003-B and Task 003-C.

## Non-claims

Task 003-A does not prove:

- clean-room independence;
- exhaustive correctness;
- durability/persistence/crash recovery;
- distributed fencing;
- chain authority/finality;
- bank/PG exactly-once;
- refund execution;
- concurrency/performance;
- future lifecycle release/GC/index correctness.

## Follow-up boundary

- Task 003-B may begin only after Task 003-A is merged and post-merge main CI is terminal success.
- Task 003-B will expand generator/property transition coverage using the merged explicit schema.
- Task 003-C remains separate and will connect Task 001 deterministic edge cases to property-model anchor/cross-validation.
