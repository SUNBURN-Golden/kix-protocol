# E-4 relation-aware property expansion (Task 003-B)

Task: `docs/tasks/TASK_003B_E4_PROPERTY_EXPANSION.md` (immutable input, not edited).
Base (`origin/main` observed at session start): `c3a2b304641dcd2373e0267030dc69ea48d55f5e`.
This equals the base named by the task; no main drift, no rebase, no merge of main.
Task branch: `agent/task-003b-e4-property-expansion`, HEAD before this change
`7f59ed18129960724696400f7f4c9fca3d465fd9` (the task document commit).
The implementation head is the commit adding the files listed below; the exact
final head and its CI are reported in the PR closure summary, not in a commit.

This is a test-only generator/property task. No kernel or runtime source, no wire
change, no reference-model schema change (Task 003-A is frozen), no
deterministic/property crosswalk and no verbatim replay of Task 001's eight
deterministic examples (Task 003-C), no review resolution, no ReturnRequired
discharge, no observation-slot release/GC/index work, no R2, no storage/log
engine, and no live PG/bank/Sui work is included.

## Governance preconditions

Read from the GitHub Actions API before any file was edited:

| Workflow | Event | Head SHA | Run ID | Status / conclusion |
|---|---|---|---|---|
| KIX protocol verification | push (main) | c3a2b304641dcd2373e0267030dc69ea48d55f5e | 35437552975 | completed / success |
| KTX kernel verification | pull_request (Task 003-A head) | d554ffc40d93b85fdd01057f48fdccfa0d991d94 | 35416941412 | completed / success |

## Locked blob verification

`git hash-object` before and after the change, both equal to the required values:

| Path | Required blob | Observed before | Observed after |
|---|---|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f | same | same |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 | same | same |

`cargo fmt` was run in write mode for the runtime workspace; the locked files were
already canonical and their blobs are unchanged.

## Changed paths

- `runtime/crates/kix-kernel/tests/support/coverage_v4.rs` (new) — the P1–P7
  `Family` enumeration, the required transition classes per family, the
  relation observer that classifies each (pre-model, step, reply, post-model)
  transition and asserts the family's relation properties, and stable JSON
  rendering of the counters.
- `runtime/crates/kix-kernel/tests/e4_state_model.rs` — additive relation-aware
  runner, family-directed generator, baseline inventory, relation sensitivity
  test, evidence output. The baseline generator, `CASES`/`STEPS`, shrinker and
  existing tests are unchanged in behaviour; `shrink` now delegates to
  `shrink_with`, the same deletion strategy over an arbitrary failing predicate.
- `validation/2026-09-19-task-003b-e4-property-expansion/README.md` — this note.

No production/runtime source file was changed. `support/model_v4.rs` was not changed.

## 1. Inventory of the pre-existing generated coverage

The historical E-4 workload (`locked_v4_matches_independent_state_model`) is
4 configurations × seeds 1..=256 × 128 steps = 1024 sequences, 131072 compared
transitions, action histogram `[55753, 20884, 15946, 30522, 7325, 642]`. It is
preserved verbatim and still emits `e4-summary.json` with the same values.

The new test `baseline_corpus_relation_coverage_is_inventoried_not_retuned`
runs the observer over that exact baseline corpus (kernel not in the loop) and
writes `.local/verification/ktx/e4-baseline-relation-inventory.txt`. Result:

| Family | Classification of baseline | Required classes never reached by the baseline |
|---|---|---|
| P1 command identity | partial | `altered_field_order_id` |
| P2 operation binding | partial | `reuse_of_bound_operation_rejected`, `retained_unbound_operation_refused`, `bound_quarantined_operation_refused`, `unretained_conflict_operation_bound_later` |
| P3 slot lifecycle | covered (all 10 classes reached, thinly: `scope_cancellation_keeps_reservation` 103) | — |
| P4 event vs economic identity | covered by accident (all 12 reached; `later_mismatch_raises_review` 366, `retained_conflict_replayed_without_new_evidence` 147) | — |
| P5 quarantine evidence | partial | `retained_unbound_blocks_binding`, `retained_unbound_ban_coexists_with_bound_sibling`, `unretained_conflict_left_no_ban` |
| P6 ReturnRequired / review | covered thinly (`mismatch_after_return_required_keeps_phase` 13, `retained_capture_preserved_under_mismatch` 13, `return_required_after_cancellation` 21) | — |
| P7 observation budget | covered | — |

Before this task none of these classes were asserted or counted; the baseline
only compared kernel and model replies/state and ran the 003-A relation checker.
The inventory is evidence, not a gate: the baseline is not required to reach
every class and is deliberately not retuned.

## 2. Additive relation-aware suite

`relation_aware_generated_traces_reach_every_property_family` runs one directed
corpus per family:

| Parameter | Value |
|---|---|
| Configurations | seats `[6,4]` (cmd 64 / orders 24 / obs 12); GA 5 (64 / 16 / 4); seats `[3]` (64 / 8 / 2); seats `[2,2]` (6 / 4 / 6) |
| Seeds per configuration | 1..=64 (`RELATION_SEEDS`) |
| Steps per sequence | 48 (`RELATION_STEPS`) |
| Sequences / compared transitions per family | 256 / 12288 |
| Total compared transitions | 7 × 12288 = 86016 |
| Generator | the existing SplitMix-style generator, seeded `seed ^ family_tag`; family-directed action choice consults the independent model only (never the kernel) |

Every step is applied to kernel and model, replies and public state are
compared, the 003-A model relation checker runs, and the observer classifies
the transition and asserts the family's properties. The test fails if any
family misses any required class; the observer reports which.

Observed counts (`.local/verification/ktx/e4-relation-coverage.json`,
`failures: 0`), own-family classes only:

| Family | Required | Reached | Min count | Total classified |
|---|---|---|---|---|
| P1 | 15 | 15 | 354 (`altered_field_selection`) | 26432 |
| P2 | 8 | 8 | 50 (`unretained_conflict_operation_bound_later`) | 12217 |
| P3 | 10 | 10 | 19 (`capture_leaves_other_reservations_intact`) | 1042 |
| P4 | 12 | 12 | 1 (`first_capture_reviewed`) | 8963 |
| P5 | 12 | 12 | 1 (`unretained_conflict_left_no_ban`) | 6486 |
| P6 | 12 | 12 | 5 (`return_required_on_already_reviewed_order`) | 11405 |
| P7 | 10 | 10 | 64 (`promised_capacity_honoured_at_full_budget`) | 14647 |

Across all seven corpora (the `total` object) every required class is reached
at least 20 times (`first_capture_reviewed` 20; `unretained_conflict_left_no_ban` 51).
The eight classes the baseline never reached are reached 418/1318/2320/51
(P2) and 418/418/51 (P5), and `altered_field_order_id` 914 (P1).

## 3. Failure reproduction and shrinking

A relation failure carries family, configuration index, seed, step index,
`kind` (`kernel_model_mismatch`, `model_relation`, `transition_property`), the
offending step and reply, and the failed predicate text. The runner writes
`.local/verification/ktx/e4-relation-failure.txt` with the original and
deletion-shrunk trace. Re-running with the same family/config/seed reproduces
the trace exactly; no wall-clock, process or thread randomness is involved.

## 4. Sensitivity

- Existing `oracle_sensitivity_detects_and_shrinks_missing_full_budget_quarantine`
  is unchanged and passes (model-only injection, kernel not in the loop).
- New `relation_properties_detect_model_only_quarantine_omission_and_shrink`
  injects the same model-only omission and checks the relation properties
  catch it without the kernel: seed 1, failure at step 25,
  `kind: transition_property`, `bound conflict did not quarantine`,
  48 steps shrunk to 6 (`e4-relation-property-sensitivity.txt`).

## 5. Contract violations and characterizations

No generated transition produced a kernel/model mismatch or a failed relation
property against the locked kernel. No contract violation was found; the model
was not taught to mimic the kernel. No contract-undefined behaviour needed a
new characterization beyond what 003-A already documents (model is
source-informed, sequential, public-API only).

## Commands run (all exit 0)

```
cargo test   --manifest-path runtime/Cargo.toml -p kix-kernel --locked          # 71 tests, e4_state_model: 8
cargo test   --manifest-path runtime/Cargo.toml --workspace --locked
cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings
cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings
cargo fmt    --manifest-path runtime/Cargo.toml --all -- --check
python3 scripts/verify_runtime_architecture.py   # architecture v5 + KTX-R1 dependency gate OK
python3 scripts/test_runtime_architecture.py     # 7 tests OK
git hash-object <both locked files>              # unchanged
```

## Non-claims

Reachability of transition classes in a generated corpus is not completeness,
not durability, not concurrency, not retention/replay, and not a proof about
production lifecycle. Counts are properties of these seeds and step budgets; a
class reached once is reached, not well-explored. Mapping each P-family to
Task 001's deterministic examples remains Task 003-C.
