# KIX Task 002 — STATE_LIFECYCLE 0.6 ReturnRequired / review precedence

## Status

- Task ID: `002`
- Execution session: new session required
- Task document: immutable once execution starts
- Repository-wide rules: follow root `AGENTS.md`

## Objective

Resolve the single documented contract ambiguity discovered by Task 001:

after an order has entered `OrderState::ReturnRequired`, a later mismatching capture may produce `ObservationOutcome::Review` and set `review_required = true`, while the order's primary lifecycle/economic state remains `ReturnRequired`.

This task is a **contract clarification only**. It must not change kernel/runtime semantics.

The intended 0.6 rule is:

1. `ReturnRequired` is the retained primary lifecycle/economic state once that obligation exists.
2. `review_required` is an orthogonal sticky review/quarantine predicate, not a competing lifecycle state.
3. `ObservationOutcome::Review` describes the processing outcome of the newly observed evidence; it does not overwrite an existing `OrderState::ReturnRequired`.
4. Later mismatching evidence after `ReturnRequired`:
   - preserves the retained capture/economic fact;
   - preserves `OrderState::ReturnRequired`;
   - sets/keeps `review_required = true`;
   - may return `ObservationOutcome::Review`;
   - must not release inventory again, erase the capture, clear review, or imply refund execution/completion.
5. Later matching duplicate evidence remains duplicate-effect handling and must not clear review or erase the return obligation.
6. 0.6 does **not** define review resolution, ReturnRequired release, refund execution, slot release, lifecycle GC, or any new transition.

If an existing authoritative contract explicitly contradicts this intended rule, do not silently reconcile it. Produce the conflicting citations, report a blocker, and stop the merge path.

## Base

- Requested base SHA: `a83d09cd99017875f583383e6ebbabc46a6a63eb`
- This is the ordinary merge commit for PR #21 (agent governance).
- At session start, run `git fetch origin main`.
- Verify `origin/main` and report any drift.
- Do not silently rebase or change the base.

### Governance merge precondition

Before making Task 002 implementation/document changes, verify the **main/push CI** for merge commit
`a83d09cd99017875f583383e6ebbabc46a6a63eb`.

If required post-merge CI is not terminal success, report its exact state and stop before modifying Task 002 outputs.

## Mandatory task-specific reading

Follow root `AGENTS.md`, then read:

- `docs/contracts/STATE_LIFECYCLE.md`
- `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md`
- `docs/contracts/PG_TOSS_CARD_PROFILE.md`
- `docs/DEVELOPMENT_PLAN.md`
- `docs/contracts/CONTRACT_INVARIANTS.md`
- `runtime/crates/kix-kernel/README.md`
- `runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
- `validation/2026-09-18-contract-edge-cases/README.md`

## Existing evidence to reuse

Task 001 already provides the key deterministic regression:

`runtime/crates/kix-kernel/tests/contract_edge_cases.rs::return_required_is_stable_under_further_late_evidence`

It currently demonstrates:

- first late capture → `ObservationOutcome::ReturnRequired`;
- order state → `OrderState::ReturnRequired`;
- second matching capture → `DuplicateEffect`;
- later mismatching capture → `ObservationOutcome::Review`;
- order state remains `ReturnRequired`;
- captured amount remains retained;
- `review_required` becomes true;
- inventory is not released twice.

Before adding any test, map all existing coverage relevant to this rule. Do not duplicate this regression merely to increase test count.

## Authorized scope

This task may modify only contract/current-reference documentation and narrowly scoped validation evidence needed to publish 0.6.

Expected authorized paths, subject to actual current-reference audit:

- `docs/contracts/STATE_LIFECYCLE.md`
- `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md`
- `docs/contracts/PG_TOSS_CARD_PROFILE.md`
- `docs/DEVELOPMENT_PLAN.md`
- one new narrowly scoped validation note under `validation/`

A path outside this list requires an explicit explanation and must still remain documentation/evidence only.

The executing agent must not modify this Task document.

## Required contract changes

### A. Publish STATE_LIFECYCLE 0.6

Advance the current contract version from 0.5 to **0.6**.

0.6 must be described as a narrow precedence/orthogonality clarification, not as a new runtime feature.

Preserve historical 0.1–0.5 records as historical originals. Do not relabel an old blob as 0.6.

Add a 0.6 version-history entry and a clear 0.5 → 0.6 change description.

### B. State the precedence rule normatively

Place the rule in the most appropriate current lifecycle section, near the existing ReturnRequired discussion.

The text must make unambiguous that:

- `ReturnRequired` is retained as the order's primary lifecycle/economic state;
- `review_required` may coexist with it;
- an observation returning `Review` does not imply an order-state replacement;
- review/quarantine is orthogonal to the retained return obligation;
- neither marker erases the underlying captured fact;
- this clarification does not authorize review release, ReturnRequired release, refund execution, or new lifecycle transitions.

Avoid implementation-specific private-map wording.

### C. Update current references only

Audit current, non-historical references to the lifecycle contract and update them from 0.5 to 0.6 where appropriate.

At minimum inspect:

- `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md`
- `docs/contracts/PG_TOSS_CARD_PROFILE.md`
- `docs/DEVELOPMENT_PLAN.md`

Do not rewrite historical statements that intentionally describe 0.5 or earlier versions.

### D. Evidence

Add a narrowly scoped validation note recording:

- base/head;
- exact paths changed;
- existing coverage reused;
- why no duplicate test was added, if none is needed;
- locked blob verification;
- commands/tests actually run;
- exact-head CI;
- explicit non-claims;
- remaining uncertainty, if any.

## Additional out-of-scope constraints

Root `AGENTS.md` prohibitions remain in force.

Specifically, do not:

- change `runtime/crates/kix-kernel/src/lib.rs`;
- change `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`;
- change any kernel/runtime semantics;
- edit this Task 002 document;
- implement review resolution or ReturnRequired release;
- implement refund execution;
- implement lifecycle slot release/GC/index;
- implement R2 or PR #11 integration (a);
- add storage/log engines;
- perform live PG/bank/Sui execution;
- perform unrelated hygiene or version sweeps.

## Contract discrepancy handling

Follow root `AGENTS.md`.

For this task in particular:

- If current authoritative documents already support the intended 0.6 rule, clarify it narrowly and proceed.
- If they are silent, 0.6 may define the precedence explicitly as authorized above.
- If another authoritative current contract explicitly says that Review must replace ReturnRequired, or otherwise contradicts the intended rule, create a precise documentation conflict report and block merge. Do not change kernel semantics or reinterpret the conflicting text silently.

## Verification

Because this is contract/documentation-only work:

1. Reuse and run the existing relevant kernel regression(s), including
   `return_required_is_stable_under_further_late_evidence`.
2. Run the relevant kernel suite and broader checks required by root `AGENTS.md`.
3. Run formatting/lint or documentation checks that the repository CI expects where practical.
4. Verify both locked blobs before and after.
5. Verify exact final-head KTX and full KIX protocol CI.

Do not claim that passing current kernel tests proves refund execution, review resolution, durability, distributed fencing, or production correctness.

## Acceptance criteria

The task is complete only when all applicable items are true:

- [ ] PR #21 merge commit `a83d09cd99017875f583383e6ebbabc46a6a63eb` required main CI was verified terminal success before Task 002 output changes.
- [ ] Current Task 002 document was not modified by the executing agent.
- [ ] STATE_LIFECYCLE current version is 0.6.
- [ ] 0.6 explicitly defines ReturnRequired/review precedence and orthogonality.
- [ ] Historical 0.1–0.5 records remain historical and are not relabeled.
- [ ] Current cross-document references are consistent with 0.6.
- [ ] No kernel/runtime semantics changed.
- [ ] Existing coverage was mapped before any new test decision.
- [ ] No duplicate test was added unless a material uncovered predicate was identified.
- [ ] Both locked blobs still match their required values.
- [ ] Relevant local tests/checks pass.
- [ ] Exact final-head KTX CI is completed/success.
- [ ] Exact final-head KIX protocol CI is completed/success.
- [ ] Required evidence and non-claims are reported.
- [ ] No explicit current-contract contradiction remains on the merge path.
- [ ] PR remains unmerged until explicit human approval.

## Evidence requirements

In addition to root `AGENTS.md`, report:

- exact 0.5 text/locations that were clarified;
- exact new normative 0.6 rule;
- every current-reference version bump and every historical version reference intentionally left unchanged;
- reused test names and why they are sufficient;
- whether any new test was necessary;
- exact locked blobs before/after;
- exact local commands/results;
- exact-head KTX and protocol CI run IDs/status/conclusion;
- explicit non-claims;
- any remaining ambiguity.

## Open questions / dependencies

- Task 003-A (E-4 reference-model state schema) must not begin until Task 002 is merged and its post-merge main CI is terminal success.
- Task 003-A must use the merged 0.6 contract as its base.
