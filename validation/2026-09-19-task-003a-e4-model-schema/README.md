# E-4 reference-model state schema expansion (Task 003-A)

Task: `docs/tasks/TASK_003A_E4_MODEL_SCHEMA.md` (immutable input, not edited).
Base (`origin/main` observed at session start): `db02ae11bf4a1d7705f31b328c627714f91e1c78`.
This equals the base named by the task; no main drift, no rebase, no merge of main.
Task branch: `agent/task-003a-e4-model-schema`, HEAD before this change
`050a0e1e50f56622d8137e6516b01c6a0c8538cf` (the task document commit).
The implementation head is the commit adding the files listed below; the exact
final head and its CI are reported in the PR closure summary, not in a commit.

This is a reference-model schema task. No kernel or runtime source, no wire
change, no generator/property expansion (Task 003-B), no deterministic/property
crosswalk (Task 003-C), no review resolution, no ReturnRequired discharge, no
observation-slot release/GC/index work, no R2, no PR #11 integration (a), no
storage/log engine, and no live PG/bank/Sui work is included.

## Governance preconditions

Read from the GitHub Actions API before any file was edited:

| Workflow | Event | Head SHA | Run ID | Status / conclusion |
|---|---|---|---|---|
| KIX protocol verification | push (main) | db02ae11bf4a1d7705f31b328c627714f91e1c78 | 35408175012 | completed / success |
| KTX kernel verification | pull_request (merged content) | c51142ae5090fb00d68fa4f2d8722c6a1d526345 | 35406674412 | completed / success |

KTX is PR-triggered only, so the merge commit itself has no KTX push run.

## Locked blob verification

`git hash-object` before and after the change, both equal to the required values:

| Path | Required blob | Observed before | Observed after |
|---|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | same | same |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 | same | same |

Neither locked file was opened for writing or reformatted. `cargo fmt` was run
in write mode only for `-p kix-kernel`; the locked files were already canonical
and their blobs are unchanged, and the repository-wide `--check` run is clean.

## Changed paths

- `runtime/crates/kix-kernel/tests/support/model_v4.rs` — explicit schema records
  and the model-side relational consistency checker.
- `runtime/crates/kix-kernel/tests/e4_state_model.rs` — per-step relation check,
  mechanical field renames in the comparison/generator, one model-only test.
- `validation/2026-09-19-task-003a-e4-model-schema/README.md` — this note.

No production/runtime source file was changed.

## Implicit state → explicit schema mapping

| Task 003-A requirement | Before | After |
|---|---|---|
| A. operation ↔ order binding | recovered by scanning `orders` for `input.payment` | `Model::bindings: Vec<OperationBinding { operation, order_id }>`; `Model::bound()` resolves through the binding only |
| B. event relation | `events: Vec<(CaptureObservation, ObservationOutcome)>` | `StoredEvent { identity: EventIdentity, observation, operation, bound_order, outcome }` with `EventIdentity { provider, account, event_id }` kept separate from `ProviderOperation` |
| C. bound quarantine vs retained-unbound blocking | `quarantined: Vec<ProviderOperation>` plus ad-hoc conflict scans | `quarantined: Vec<BoundQuarantine { operation, order_id }>`; `retained_unbound_blocked()` / `retained_unbound_blocks()` derived from retained conflicts with no binding; `binding_blocked()` names both refusal reasons |
| D. first-capture slot | `promised: Vec<ProviderOperation>` | `reservations: Vec<SlotReservation { operation, order_id }>`, created at send, reused on UNKNOWN retry, retained across expiry/owner replacement/cancellation, removed only by the matching accepted bound capture |
| E. phase vs review | two fields, no stated invariant | `ModelOrder.phase` documented as the primary lifecycle phase and `review` as an orthogonal sticky predicate; the checker accepts `ReturnRequired + review_required` and rejects a `ReturnRequired` order that lost its capture or its inventory release |
| F. retained capture | `amount: Option<AssetAmount>` | `capture: Option<RetainedCapture { amount, identity }>` with `captured_amount()` for the public projection; later matching events are duplicate effect, later mismatching events raise review without overwriting |

### Authoritative state versus derived indexes

Authoritative model state: `orders`, `bindings`, `events`, `conflicts`,
`reservations`, `quarantined`, `commands`, `seats`, `epoch`, `writer`, `time`.

Derived (recomputed on demand, never stored): `binding()`, `bound()`,
`bound_quarantine_contains()`, `conflict_evidence_names()`,
`retained_unbound_blocked()`, `retained_unbound_blocks()`, `binding_blocked()`,
`reservation()`, `budget()`, `remaining()`, `ModelOrder::captured_amount()`.

Retained-unbound blocking is deliberately derived from retained conflict
evidence rather than stored, so it cannot outlive the evidence and cannot become
a scope-wide quarantine latch.

## Schema consistency checks

`Model::check_relations()` runs after every generated step in `check_trace()`,
before the public-state comparison. It calls no `Kernel` method and reads no
kernel state. It checks:

- each binding resolves to exactly one accepted order with the same operation,
  and bindings are one-to-one in both directions;
- every accepted order has its binding, and `bindings.len() == orders.len()`;
- every reserved slot belongs to a bound operation, matches that binding's order
  and is unique per operation;
- every bound quarantine resolves to its bound order, that order's review
  predicate is set, and entries are unique;
- every retained-unbound block has retained conflict evidence, no speculative
  binding, and is not simultaneously a bound quarantine;
- stored events keep `identity == EventIdentity::of(observation)`, keep the named
  operation, are unique by identity, and resolve to their binding's order;
- `events + conflicts + reservations` stays within `limits.observations`;
- the retained capture agrees with the first stored event of that order;
- a `ReturnRequired` order still holds its retained capture and has released
  inventory, while `ReturnRequired + review_required` remains valid.

## Existing coverage first

Mapped before any new test was written:

| Requirement | Existing coverage | Classification |
|---|---|---|
| A binding / reuse rejection | `transitions.rs` operation-binding and command-identity cases, `contract_edge_cases.rs` retained-unbound conflict case | covered for kernel behavior; model representation not covered |
| B event vs economic identity | `transitions.rs` `same_event_different_payload_preserves_conflicting_evidence`, replay cases | covered for kernel behavior |
| C bound vs retained-unbound | `quarantine_capacity.rs` (8, locked), `contract_edge_cases.rs` retained-unbound case | covered for kernel behavior |
| D first-capture slot | `observation_slots.rs` (11) | covered for kernel behavior |
| E phase vs review | `contract_edge_cases.rs` `return_required_is_stable_under_further_late_evidence`, `transitions.rs` reviewed-late-capture cases | covered for kernel behavior |
| F retained capture | `contract_invariants.rs` INV-1..INV-5, `transitions.rs` duplicate/mismatched capture cases | covered for kernel behavior |
| model-side relational consistency | none | not covered — the gap this task fills |

No deterministic kernel regression was duplicated. Exactly one test was added,
`model_schema_relations_are_explicit_and_corruption_is_detected` in
`e4_state_model.rs`. It is model-only: it drives `Model` alone, asserts the new
explicit relations across reserve → send → expiry → owner replacement → late
capture → mismatching capture → unbound conflict, and then corrupts a cloned
model four ways (invalid binding, duplicated slot, dropped capture, unbound
quarantine entry) to show the checker rejects each. Without the corruption arm
the checker could pass vacuously.

## Generator freeze

Unchanged in `e4_state_model.rs`: `CASES = 256`, `STEPS = 128`, seed range
`1..=256`, the SplitMix-style `Rng`, all action-choice percentages, the action
kinds, the mutation probabilities, the four fixture configurations and the
deletion shrinker. The only generator-side edits are mechanical field renames
forced by the new types:

- `model.promised.len()` → `model.reservations.len()` in `compare()`;
- `expected.amount` → `expected.captured_amount()` in `compare()`;
- `model.events[i].0` → `model.events[i].observation` in `trace()`.

Evidence that generated input semantics are unchanged: the emitted
`.local/verification/ktx/e4-summary.json` action histogram is byte-identical to
the histogram recorded before this task in
`validation/2026-09-16-first-batch/README.md`:

`55753, 20884, 15946, 30522, 7325, 642` over 1024 sequences and 131072 compared
transitions, `failures: 0`.

## Behavioral preservation and oracle sensitivity

All 1024 pre-existing generated traces still produce per-step replies equal to
the locked kernel's, with the relation check additionally passing at each of the
131072 steps. `oracle_sensitivity_detects_and_shrinks_missing_full_budget_quarantine`
still injects the missing full-budget quarantine, still detects the mismatch and
still shrinks to the expected minimal trace.

No contract violation was discovered. No contract-undefined behavior was newly
characterized: the refactor only re-expresses relations the current contract and
the locked kernel already imply.

## Commands run

All from the repository root, toolchain `1.98.1`:

- `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked`
  → 68 passed, 0 failed (lib 0, contract_edge_cases 8, contract_invariants 3,
  e4_state_model 5, observation_slots 11, performance_harness 1,
  quarantine_capacity 8, transitions 32, doc-tests 0).
- `cargo test --manifest-path runtime/Cargo.toml --workspace --locked`
  → all packages pass, including `kix-types` 6 and the kernel suite above.
- `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` → clean.
- `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings`
  → clean.
- `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings`
  → clean.
- `python3.12 scripts/verify_runtime_architecture.py`
  → `architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified`.
- `python3.12 scripts/test_runtime_architecture.py` → 7 tests, OK.

The architecture scripts require `tomllib`; the machine's default `python3` is
3.10, so a 3.12 interpreter was used locally, matching the CI Python version.

## Non-claims

This note does not claim clean-room independence (the E-4 model remains
source-informed), exhaustive correctness, durability, persistence, crash
recovery, distributed fencing, chain authority or finality, bank/PG
exactly-once, refund execution, concurrency or performance properties, or any
future lifecycle release/GC/index correctness.

## Remaining gaps

- Generated transition coverage of the new relations is still limited to the
  frozen Task 003-A workload; expanding it is Task 003-B.
- Connecting the Task 001 deterministic edge cases to property-model anchors is
  Task 003-C.
- Slot release, review resolution, ReturnRequired discharge and evidence
  reclamation remain unimplemented and unmodelled by design.
