# KIX Task 003-B — E-4 property/generator transition expansion

## Status

- Task ID: `003-B`
- Execution session: new session required
- Task document: immutable once execution starts
- Repository-wide rules: follow root `AGENTS.md`

## Objective

Expand E-4 generated transition/property coverage on top of the explicit reference-model schema merged by Task 003-A.

Task 003-A made these relations explicit in the model:

- operation ↔ order binding;
- event identity → operation → bound order;
- bound quarantine versus retained-unbound blocking;
- reserved first-capture observation slot;
- retained first capture/economic effect;
- primary lifecycle phase versus orthogonal review predicate.

Task 003-B must now generate enough deterministic, reproducible transition sequences to deliberately exercise those relations and verify that the locked v4 kernel and the reference model continue to agree.

This is a **test-generator/property task only**. It must not change production/runtime semantics.

Task 003-C remains separate and will later connect Task 001's eight deterministic examples to property-model anchor/cross-validation. Do not perform that crosswalk here.

## Base

- Requested base SHA: `c3a2b304641dcd2373e0267030dc69ea48d55f5e`
- This is the ordinary merge commit for Task 003-A.
- At session start run `git fetch origin main`.
- Record exact `origin/main` and report any drift.
- Do not silently rebase, merge main into the task branch, or change the base.

### Task 003-A closure precondition

Task 003-A post-merge closure is already recorded:

- merge commit: `c3a2b304641dcd2373e0267030dc69ea48d55f5e`
- post-merge main/push KIX protocol run `35437552975`: completed / success
- reviewed exact-head KTX run `35416941412`: completed / success
- locked kernel and quarantine blobs exact on the merge commit.

Before editing Task 003-B outputs, independently confirm the base/current-main relationship and both locked blobs.

## Mandatory task-specific reading

Follow root `AGENTS.md`, then read:

- `docs/DEVELOPMENT_PLAN.md` §6.1
- `docs/contracts/CONTRACT_INVARIANTS.md`, especially §§3–5
- `docs/contracts/STATE_LIFECYCLE.md` 0.6 §5.7.1
- `runtime/crates/kix-kernel/README.md`
- `runtime/crates/kix-kernel/tests/e4_state_model.rs`
- `runtime/crates/kix-kernel/tests/support/model_v4.rs`
- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
- `runtime/crates/kix-kernel/tests/observation_slots.rs`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
- `runtime/crates/kix-kernel/tests/transitions.rs`
- `validation/2026-09-19-task-003a-e4-model-schema/README.md`
- `validation/2026-09-18-contract-edge-cases/README.md`

## Existing coverage first

Before changing any generator:

1. Map the current frozen E-4 generated workload to the explicit Task 003-A relations.
2. Identify which transitions/relations are only incidentally or weakly reached.
3. Record actual observed baseline counts where practical.
4. Do not assume that a relation is covered merely because its state type exists.
5. Do not duplicate deterministic regressions simply to increase test count.

The pre-Task-003-B baseline generator must remain available as a regression asset.

## Required design principle: additive expansion

Prefer an **additive property suite** rather than silently rewriting the historical baseline generator.

The existing baseline differential workload should continue to run with its established constants/seed behavior so historical evidence remains comparable.

Task 003-B may add:

- a second deterministic relation-aware generator;
- targeted generated trace families;
- additional coverage counters/assertions;
- additional shrink/minimization support if necessary for the new generated family.

If changing the existing baseline generator is truly necessary, explain exactly why and preserve a reproducible compatibility path for the old workload. Do not casually invalidate the old histogram/evidence.

## Property families that must receive deliberate generated coverage

The exact implementation shape is not prescribed. The smallest auditable approach is preferred.

### P1. Command identity / replay / altered payload

Generate sequences that include:

- accepted and rejected reservation first results;
- exact replay after relevant state has changed;
- same command identity with altered payload fields;
- stale fence / regressed clock contexts around replay/conflict;
- verification that original-result replay remains immutable and read-only;
- verification that altered payload conflicts do not silently execute as a new command.

Do not hardcode Task 001's exact eight example traces; that crosswalk is Task 003-C.

### P2. Explicit operation binding and reuse

Generate sequences that exercise:

- accepted order creates exactly one operation↔order binding;
- rejected reservation creates no binding;
- second order attempting to reuse a bound operation;
- sibling operation under the same provider/account remaining independent;
- retained-unbound blocked operation refusing future binding;
- unretained unbound conflict not creating a speculative permanent binding ban.

Properties should be asserted through the explicit Task 003-A model relations plus public kernel behavior.

### P3. First-capture slot lifecycle

Generate sequences that deliberately cover:

- successful send reserving exactly one slot;
- UNKNOWN retry reusing the same reservation;
- capacity refusal when a new slot cannot be reserved;
- owner replacement without slot release;
- expiry check without slot release;
- scope cancellation without slot release;
- unrelated event/conflict not consuming another operation's reservation;
- matching accepted first capture consuming the correct reservation.

Do not add terminal slot-release/GC semantics.

### P4. Event identity vs economic-operation identity

Generate sequences that distinguish:

- identical event replay;
- same event identity with altered payload;
- same operation through a different event identity;
- event conflict naming two bound operations;
- event conflict naming one bound and one unbound operation;
- repeated matching capture as duplicate economic effect rather than second capture effect.

Keep event dedupe and economic dedupe separate.

### P5. Quarantine / retained-unbound evidence behavior

Generate sequences that cover:

- bound conflict making the bound order reviewed/quarantined;
- bound quarantine surviving owner replacement;
- bound quarantine surviving expiry/cancellation transitions that do not resolve review;
- retained-unbound conflict blocking future binding;
- unretained unbound evidence under full capacity not creating a speculative ban;
- no scope-wide quarantine latch.

### P6. ReturnRequired / review orthogonality

Generate traces that deliberately reach:

- late matching capture → ReturnRequired;
- later matching capture → duplicate effect;
- later mismatching capture → Review outcome while primary state remains ReturnRequired;
- retained capture preserved;
- review predicate sticky;
- no second inventory release.

This must follow STATE_LIFECYCLE 0.6 §5.7.1.

### P7. Observation-budget relational accounting

Generate capacity pressure around:

- stored events;
- retained conflicts;
- reserved slots;
- conversion of reserved first-capture capacity into stored event capacity;
- conflict admission/refusal at the limit;
- preservation of already-promised capacity.

Verify the explicit model budget and public kernel counters stay consistent.

## Coverage observability

The expanded generated suite must emit auditable coverage evidence rather than only "all seeds passed."

Add deterministic counters or equivalent evidence for the property families above.

At minimum the final evidence must show that each P1–P7 family was actually exercised by the generated corpus.

Avoid brittle arbitrary score claims. The key requirement is non-vacuous, reproducible reachability with enough evidence to see which relation/transition classes were hit.

If a family cannot be generated without reproducing a deterministic fixed example verbatim, report that limitation instead of disguising a fixed test as property coverage.

## Generator requirements

Generated inputs must remain:

- deterministic from explicit seeds;
- independent of wall-clock time;
- independent of thread/process RNG;
- reproducible from failure evidence;
- shrinkable/minimizable to a useful failing trace.

The generator may consult the reference model to choose currently meaningful operations/orders, as the existing suite does, but must not call `Kernel` or inspect kernel private state to construct the expected answer.

Prefer relation-aware generation over merely increasing CASES or STEPS.

Increasing raw seed/step counts alone does not satisfy this task.

## Shrinking / failure evidence

Every newly generated property family must preserve useful failure reproduction.

At minimum:

- record seed/family/configuration;
- record failing step and expected/actual reply or failed relation;
- run the existing deletion shrinker where applicable;
- if a new trace shape needs additional minimization logic, keep it test-only and deterministic.

Do not weaken or remove the existing oracle-sensitivity shrink test.

## Oracle sensitivity

The existing independent-model-only fault injection must remain detectable.

Task 003-B may add at most a small number of **model-only** sensitivity injections specifically targeting newly added relation coverage if they materially prove that a new property checker is not vacuous.

Do not mutate the locked kernel or production code.

Do not turn this into a general mutation-testing campaign.

## Authorized scope

Expected authorized implementation paths:

- `runtime/crates/kix-kernel/tests/e4_state_model.rs`
- `runtime/crates/kix-kernel/tests/support/model_v4.rs` only if small helpers are needed for generated relation-aware actions/assertions
- optionally one additional test-support file under `runtime/crates/kix-kernel/tests/support/` if it materially improves auditability
- one new narrowly scoped validation note under `validation/`

No production/runtime source may change.

The executing agent must not modify this Task document.

## Task 003-C boundary

Do not:

- import or mechanically replay the eight Task 001 deterministic tests as property fixtures;
- build the final deterministic ↔ property anchor matrix;
- claim each Task 001 case is now cross-validated.

That is Task 003-C.

Task 003-B may target the same **semantic regions** generatively, but must remain a generator/property expansion task.

## Contract discrepancy handling

Follow root `AGENTS.md`.

If generated traces expose:

- contract-defined mismatch → create the smallest useful reproduction and block merge;
- contract-undefined behavior → record characterization and continue only if it does not require inventing semantics;
- model-only bug → fix the model/test code within scope and preserve evidence.

Do not silently make the model mimic a kernel result that contradicts an explicit contract.

## Additional out-of-scope constraints

Root `AGENTS.md` prohibitions remain in force.

Specifically do not:

- modify `runtime/crates/kix-kernel/src/lib.rs`;
- modify `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`;
- modify Task 003-B document;
- change production/kernel semantics;
- implement Task 003-C crosswalk;
- implement review resolution, ReturnRequired discharge, observation-slot release, lifecycle GC/index;
- implement R2 or PR #11 integration (a);
- add storage/log engines;
- perform live PG/bank/Sui execution;
- perform performance benchmarking or unrelated hygiene;
- modify CI merely to make the task pass.

## Verification

At minimum:

1. run the existing baseline E-4 generated differential suite;
2. run the new relation-aware generated property suite;
3. verify all required P1–P7 coverage families are actually reached;
4. run existing oracle-sensitivity/shrinking tests;
5. run `contract_edge_cases`, `observation_slots`, relevant quarantine/transition tests, and the full kernel suite;
6. run runtime workspace tests;
7. run `cargo fmt --check`;
8. run kernel/workspace Clippy with `-D warnings`;
9. run runtime architecture gate/tests where practical;
10. verify both locked blobs before and after;
11. verify exact final-head KTX and full KIX protocol CI.

Record exact commands and actual results.

## Acceptance criteria

The task is complete only when:

- [ ] base is `c3a2b304641dcd2373e0267030dc69ea48d55f5e` with no unreported drift;
- [ ] Task 003-B document is unchanged by the executing agent;
- [ ] both locked blobs remain exact;
- [ ] existing generator/property coverage was inventoried before expansion;
- [ ] historical baseline E-4 generated workload remains reproducible;
- [ ] an additive or equivalently auditable relation-aware generated suite exists;
- [ ] P1 command replay/conflict coverage is reached;
- [ ] P2 binding/reuse/retained-unbound coverage is reached;
- [ ] P3 slot lifecycle/capacity coverage is reached;
- [ ] P4 event-vs-economic identity coverage is reached;
- [ ] P5 bound/unbound quarantine behavior is reached;
- [ ] P6 ReturnRequired/review orthogonality is reached;
- [ ] P7 observation-budget relational accounting is reached;
- [ ] generated coverage evidence is deterministic and non-vacuous;
- [ ] failing generated traces remain reproducible and shrinkable;
- [ ] existing oracle-sensitivity test still detects/shrinks its injected defect;
- [ ] no production/kernel semantics changed;
- [ ] no Task 003-C deterministic/property crosswalk was performed;
- [ ] relevant local tests/checks pass;
- [ ] exact final-head KTX CI is completed/success;
- [ ] exact final-head KIX protocol CI is completed/success;
- [ ] evidence/non-claims and remaining uncertainty are reported;
- [ ] PR remains unmerged until explicit human approval.

## Evidence requirements

Final report must include:

- exact base / pre-session branch head / final head;
- complete full-PR changed-path list and executing-session changed-path list if different;
- locked blobs before/after;
- baseline generator inventory and preserved baseline parameters;
- description of new generator/property families;
- P1–P7 actual generated coverage counts/evidence;
- seeds/configurations/step counts for each generated family;
- failure reproduction/shrink strategy;
- oracle-sensitivity results;
- local command results;
- exact-head CI run IDs/status/conclusion;
- contract violations or undefined characterizations found;
- explicit non-claims;
- remaining gaps reserved for Task 003-C.

## Non-claims

Task 003-B does not prove:

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

- Task 003-C may begin only after Task 003-B is merged and post-merge main CI is terminal success.
- Task 003-C will map the Task 001 deterministic edge cases to the property/reference-model coverage and add only the missing cross-validation anchors.
