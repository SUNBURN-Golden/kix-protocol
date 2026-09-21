# Task 003-C1 — generated crosswalk evidence gates

Author-side verification, 2026-09-21. This is test/evidence work only.
The old PR #26 is not reopened or relabelled complete by this record.
Final exact-head CI belongs in the new draft PR; no remote CI success is asserted here.

## Provenance and scope

- Observed main / base: `6332bca0f54cc2114d986b24ab218ace33a5df12`.
- Task bootstrap: `7949fe3e7ac4a370c0b4cbb05ac39a3779e8c466`.
- Immutable task: `docs/tasks/TASK_003C1_EVIDENCE_GATES.md`, blob
  `411e7a592fa4219ed606ec770ab903c6a6fd36c7`.
- Branch: `agent/task-003c1-evidence-gates-20260921`.
- Selective test carry-forward: PR #26 head
  `7f99812f4558e4802a51d5468da35754db693c43`.
- Historical Task 003-C document: that head's
  `docs/tasks/TASK_003C_E4_DETERMINISTIC_CROSSWALK.md`, blob
  `1f9cceb99404cd673205d5fa1f46db8900e74da4`. It is an input, not imported or edited.
- Task 003-B post-merge protocol run `35448485847` was independently checked as
  completed/success at main/base. Its success is not assigned to the new head.

Shell git fetch was unavailable because the configured network Git endpoint
required unavailable credentials. The orchestrator fetched exact branch/tree/blob
state through the authenticated GitHub connector instead. Implementation used an
isolated partial source snapshot; publication builds on the main tree and adds
only explicitly allowed paths. It does not publish the partial snapshot as a tree.
An isolated official Rust 1.98.1 toolchain was installed for local execution.

Changed paths: bootstrap Task above; `runtime/crates/kix-kernel/tests/e4_state_model.rs`;
`runtime/crates/kix-kernel/tests/support/coverage_v4.rs`;
`runtime/crates/kix-kernel/tests/support/evidence_gates.rs`; this README.
No workflow, production, model, deterministic source or historical validation edits.

## Frozen blobs, verified before and after

| Path below `runtime/crates/kix-kernel/` | Git blob |
|---|---|
| `src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `tests/contract_edge_cases.rs` | `d37ea7df55423c83bedee16bf12bdc8dd61f7cae` |
| `tests/support/model_v4.rs` | `f020860b86933bf7511befccdb833b0c532b3629` |

Implementation test blobs for this record:

| Path below `runtime/crates/kix-kernel/` | Git blob |
|---|---|
| `tests/e4_state_model.rs` | `7ae4535c472cbe5416cf68a298fd4cd1dcf2a38a` |
| `tests/support/coverage_v4.rs` | `2f527f4fa6d0a1c6185deca7dc29eef49de01005` |
| `tests/support/evidence_gates.rs` | `78ed34d37568d9084f75a546bbb6377d16397521` |

## Existing coverage and exact corrections

The prior review classified Rows 1–7 partial, Row 8 sufficient. Existing generated
traces already reach the required paths. No generator changes were needed.
Historical `trace()`, configurations, required_classes(), shrink helpers and old
sensitivity tests are preserved, as are 256 × 128 baseline and 64 × 48 relation
parameters. The two P1/P3 steering changes from 003-C are selectively preserved.

F01 checks actual Kernel Clone+Eq before/after contract-defined read-only calls,
not only public counters or source-informed model agreement. It covers reserve
replay/errors, unit errors, expiry errors and non-mutating capture errors.
Known-event conflict Capacity is deliberately excluded: quarantine/time can change.
Successful capture replay and expiry checks can also advance time. The gate runs
in the kernel-backed generated path; model-only sensitivity does not claim Kernel Eq.

F02 adds twelve single-field × disjoint-context gates. Resetting only the named
field must recover the complete original typed request. Multi-field, altered
quote/asset/epoch and combined stale+regressed contexts do not supply these cells.

F03 links the exact same order/ProviderOperation/slot from a refused UNKNOWN
retry to a later first matching capture at/after expiry, with cancellation false,
reservation consumption and one inventory release. Exact and strictly-after retry
bins remain separate requirements. The linked history need not contain both bins:
they are alternative boundaries; the later capture is causally linked to its retry.

F04 tracks one order through first ReturnRequired, a new matching duplicate event,
a later new mismatching event that changes review from false to true, and
reviewed=true refused send. Captured fact,
phase and inventory are checked throughout; final send also has whole-Kernel Eq.
Counts are qualifying final-send transitions, not unique orders.

F05 initializes the cumulative history only at retained Ok(Conflict) naming two
distinct bound operations, retaining both full operation/order IDs and evidence.
It advances through successful owner change, actual Held inventory release,
cancellation, then refused send while the order is still Expired. If a later
capture legitimately changes Expired to ReturnRequired, that final send does not
supply this narrower Row 7 anchor. Broad Capacity-origin classes remain supporting
coverage, not closure evidence for the retained-conflict path.

## Eight-row crosswalk, local generated evidence

All counts below are relation-corpus hits; baseline counts never satisfy a gate.
The generated JSON contains exact class names, first family/config/seed/step,
full identities for new cumulative witnesses and separate baseline inventory.
`P#/c#/s#` means family/config/seed; steps are zero-based.

| Row | Material predicate / evidence | Same-trace requirement | Local strength |
|---|---|---|---|
| 1 | Rejected replay after unavailable cause clears: 79; new identity, same selection and operation Held: 4; no rejected binding; replay Kernel Eq | Cause-clear replay and same-operation reuse each carry their own prior-command relation; they may be separate generated histories | sufficient |
| 2 | All 12 single-field/context cells below; exact replay retained; whole-Kernel Eq | Each cell is one original-command/altered-request relation; different matrix cells may use different traces | sufficient |
| 3 | WrongScope 356; UnsupportedSemantics 386; regressed replay 411; stale replay 400, each with Kernel Eq | Alternative guards may be separate traces, each refers to its known command | sufficient |
| 4 | Exact Held expiry 666; expired new reserve 263; exact Held send 37; first matching exact Held capture 82; failed-send Eq | Four alternative entry points are separate traces by design | sufficient |
| 5 | Exact retry 9, strict-after 36; linked non-cancelled retry/capture 22. First P3/c0/s12 steps 6→9 | Same order, operation and reserved slot for linked history | sufficient |
| 6 | Cumulative reviewed-send hits 11. First P6/c0/s30 steps 23→24→31→36 | Same order and retained capture; distinct events, ordered stages | sufficient |
| 7 | Retained-two-bound cumulative hits 9. First P5/c0/s15 steps 5→6→27→35→36 | Exact retained origin pair, same expiring order, ordered successful transitions | sufficient |
| 8 | Existing retained-unbound and sibling classes preserved; sibling anchor 688. P2/c0/s1 steps 18→20→23 exported | Same trace identifies retained unbound operation, failed reuse, then same-provider/account different operation Held | sufficient |

This is author-side finite-corpus sufficiency for the stated predicates, not an
independent final audit or universal semantic proof.

| Altered field | Normal | Stale fence only | Regressed clock only |
|---|---:|---:|---:|
| order_id | 422 | 188 | 234 |
| payment.operation | 477 | 179 | 222 |
| expires_at_ms | 551 | 193 | 212 |
| selection | 341 | 162 | 166 |

Additional linked baseline counts: F03 73, F04 3, F05 2.
Whole-Kernel read-only checks: relation 36,069; baseline 85,775.
Total generated main transitions remain 86,016 relation + 131,072 baseline.
Repeated suite execution is not additional unique coverage.

## Sensitivity and local verification

The new clock-only sensitivity test uses a generated live Held state, observes
CommandConflict, then deliberately invokes an extra successful public expiry check
before deadline on the test Kernel. Old public comparison still returns Ok; exact
read-only Kernel equality rejects the perturbation. Frozen sources are never
mutated. The missing Devin injection patch was not reconstructed, and its claimed
662 figure is not represented as reproduced here.

Negative observer-stream tests retain actual kernel/model execution but suppress
or alter only observer input: missing retry, cancellation-caused capture, missing
duplicate, already-reviewed mismatch, unreviewed final send, Capacity-origin conflict, missing owner change,
and new trace boundaries cannot complete the corresponding history gate. A
single-field checker test excludes multiple payload changes and hidden epoch change.
These are checker sensitivity tests, not a production mutation campaign.

Commands executed with isolated Rust 1.98.1 and the committed lockfile:

```sh
cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked
cargo test --manifest-path runtime/Cargo.toml --workspace --locked
cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings
cargo fmt --manifest-path runtime/Cargo.toml --all --check
git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs runtime/crates/kix-kernel/tests/contract_edge_cases.rs runtime/crates/kix-kernel/tests/support/model_v4.rs
```

During implementation, a baseline trace exposed an over-strict Row 7 observer
assertion: a later valid capture can change Expired to ReturnRequired. The anchor
now excludes that final phase instead of treating valid behavior as a violation.
The first F04 draft counted 38 relation final-send hits, including mismatches
where review was already set. Requiring the mismatch itself to change review
false→true narrowed this to 11 and moved the first positive generated witness
from P6/config0/seed3 to seed30. One nested-if Clippy finding was also corrected.

Local E-4: 12 tests passed; workspace: 125 tests passed, including all eight frozen
Task 001 tests; Clippy and formatting passed. Final exact-head remote workflows
must still both reach completed/success before verification is reported complete.
Architecture checks and full Sui/reference protocol checks belong to that remote
verification, not inferred from the local Rust run.

Evidence emitted by the test under `.local/verification/ktx/`:

- `e4-deterministic-crosswalk.json`: all eight rows, required classes and new gates;
- `e4-evidence-gates.txt`: separate relation/baseline counts and full first witnesses;
- `e4-row8-generated-identities.txt`: generated input/result/binding/evidence at steps 18/20/23;
- `e4-read-only-sensitivity.txt`: clock-only checker sensitivity and provenance limitation;
- existing baseline, relation, shrink, source-blob and sensitivity artifacts remain.

No production contract violation was demonstrated by these checks. The reference
model is source-informed; shared errors remain possible outside explicit contracts.
No R2, persistence, recovery, distributed fencing, lifecycle release/GC/index,
chain/bank exactly-once, performance, formal proof or production-readiness claim.
The new PR remains draft; merge and independent approval are outside this task.
