# E-4 residual review — isolated Mac implementation handoff

Node: `k1-e4-residual-review`; canonical dependencies: none.
Mac task: `MAC-B2C18CAE631444669EB529E0E258CBB5-C65530CE5A7B`.
Sources: `.aiops/program.json` at plan/base
`9aa464b6b9d89cdf1da65f828b55e6e97bf7bef0`, and
`docs/tasks/DEVIN_FIRST_BATCH_E4_AUDIT.md` (original immutable spec).
Observed HEAD and origin/main both equal that plan/base. The historical Task 001
bootstrap `5fffc196be37425366b2a6ec7faeec1db9bbca46` is a different, earlier
anchor; this node uses the admitted Mac pin without rebasing or rewriting it.
The host performed fetch. No Git metadata was written by this session.

This record is the only delivery change. No tests were added because the
requested predicates already have deterministic regressions and generated
evidence gates. Review completion here means handoff to independent code review,
not checks-green acceptance, legacy task completion, merge readiness or release.
There is no committed implementation/final head, merge SHA, hosted CI run ID,
or post-merge evidence for this delivery yet.

## Coverage inventory at the admitted pin

Paths abbreviated below are under `runtime/crates/kix-kernel/tests/`.
“Sufficient” describes the existing assertions for the stated local predicate;
it does not assert that these tests executed successfully in this session.

| Original audit requirement | Existing deterministic coverage | Review classification |
|---|---|---|
| Original result versus current state | `transitions.rs::expired_hold_retry_keeps_original_result_and_separate_current_state`; `contract_edge_cases.rs::rejection_replay_stays_immutable_after_the_blocking_hold_is_released` | Sufficient: successful and rejected originals survive state changes; replay is checked read-only. |
| Same identity, altered payload | `contract_edge_cases.rs::altered_payload_conflicts_before_fence_and_clock_guards`; `transitions.rs::identical_id_with_changed_payload_is_a_conflict` | Sufficient: four individually changed fields across normal/stale/regressed contexts, plus amount conflict. |
| Contract-significant guard precedence | `contract_edge_cases.rs::replay_lookup_is_guarded_by_scope_and_semantics_only`; `quarantine_capacity.rs::rejected_evidence_that_quarantines_also_advances_logical_time` | Sufficient: replay bypasses new-attempt fence/time, not scope/semantics; conflict Capacity is a mutating safety path. No arbitrary private guard ordering is adopted as a new contract. |
| UNKNOWN across TTL | `transitions.rs::unknown_payment_is_not_released_by_ttl`; `contract_edge_cases.rs::unknown_retry_after_the_deadline_keeps_the_reservation_and_its_slot`; `::expiry_instant_is_treated_consistently_by_every_entry_point` | Sufficient: exact/strict-after deadline send refusal preserves inventory and slot; first late capture consumes the slot. |
| Late capture/ReturnRequired | `transitions.rs::late_capture_after_expiry_and_resale_does_not_release_new_buyer`; `::late_capture_after_cancellation_creates_return_marker_not_resurrection`; `contract_edge_cases.rs::return_required_is_stable_under_further_late_evidence` | Sufficient: no resurrection, second release or capture erasure; review is orthogonal. |
| Bound quarantine/review stickiness | `contract_edge_cases.rs::bound_quarantine_survives_owner_change_expiry_and_cancellation`; `quarantine_capacity.rs::original_event_and_command_replays_never_clear_quarantine`; `transitions.rs::reviewed_order_preserves_matching_capture_without_normal_confirmation` | Sufficient: control transitions and matching evidence do not clear review. |
| Retained versus unretained unbound identity | `quarantine_capacity.rs::retained_unbound_conflict_blocks_future_binding_without_expanding_bound_set`; `::unretained_unbound_conflict_creates_no_speculative_binding_ban`; `contract_edge_cases.rs::retained_unbound_conflict_bans_the_identity_for_any_future_order` | Sufficient: retained full operation identity blocks a different order; a sibling operation remains admissible; rejected evidence does not create a speculative ban. |
| First-capture observation capacity | `observation_slots.rs::full_observation_budget_blocks_first_unknown_without_state_change`; `::repeated_unknown_reserves_once_and_other_operation_cannot_take_slot`; `::conflicting_event_cannot_spend_slot_reserved_for_capture`; `quarantine_capacity.rs::full_budget_quarantine_preserves_the_already_promised_capture_slot` | Sufficient: failed send is atomic; retry reuses one slot; other evidence cannot consume its promise. |

## Model, invariant and evidence-path review

Contract anchors reviewed: ADR-0001 §§3–6/8 and its R1 addendum,
`CONTRACT_INVARIANTS.md` §§1–5, current kernel README, and
`STATE_LIFECYCLE.md` §5.7.1. Pinned/current byte equality was checked for those
documents and the task, plan, governance and baseline documents.

The model remains source-informed. `support/model_v4.rs::check_relations`
checks one-to-one operation/order bindings, slot bindings and uniqueness,
bound quarantine/review relations, retained-unbound provenance, event identity
and order relations, total observation budget, first-capture provenance, and
ReturnRequired's retained capture/non-ownership. `e4_state_model.rs::compare`
checks public counts/conflicts and full known-order request, writer, phase,
ownership, capture and review; order count equality prevents silently ignoring
extra created orders. Representation differs from the kernel, but shared semantic
mistakes remain possible.

The complementary `contract_invariants.rs` observer imports no model oracle.
`five_contract_invariants_on_kernel_only_generated_histories` checks INV-1
inventory ownership/conservation, INV-2 bounded record sums, INV-3 immutable
original results, INV-4 unique economic capture/binding, and INV-5 capture
preservation. The corrupted-view sensitivity test checks detection of overlap,
over-budget state, capture loss and duplicate transitions. These are finite
local safety checks, not a full transition/availability oracle.

The generated crosswalk
`e4_state_model.rs::task_001_deterministic_edge_cases_are_cross_validated_by_generated_witnesses`
requires every row class and additional gate to have nonzero **relation** hits.
Baseline hits are inventoried separately and cannot satisfy a missing gate.
`check_relations_trace` compares actual kernel replies/state and applies whole
Kernel Clone/Eq on contract-defined read-only paths before accepting witnesses.
`support/evidence_gates.rs` explicitly excludes known-event conflict Capacity
from blanket error non-mutation: quarantine and time may change on that path.

The additional gates cover the twelve single-field/disjoint-context cells;
same-order/operation/slot UNKNOWN retry followed by late capture without
cancellation; same-order retained ReturnRequired through duplicate, mismatch
that newly sets review, then refused send; and retained two-bound conflict through
owner change, actual expiry release, cancellation and refused send. Gate histories
are initialized per trace, retaining full typed identities. Sensitivity tests
reject missing stages, substituted origins, multi-field changes and clock-only
mutation. Baseline constants and seeded corpus parameters are unchanged.

Historical evidence read: first batch (2026-09-16), contract edge cases
(2026-09-18), lifecycle precedence and model schema/property expansion
(2026-09-19), evidence gates (2026-09-21). Their counts and CI results remain
historical and are not evidence for this delivery. In particular, the old
ReturnRequired/review uncertainty in the 2026-09-18 note is resolved by current
0.6 §5.7.1; the historical note is intentionally not rewritten.

No explicit contract violation or new contract-undefined behavior was identified
by this source review. Existing capacity-two admission characterization remains
in `e4_state_model.rs::capacity_two_sequence_is_observed_not_repaired`: releasing
inventory does not reclaim completed command capacity. This is not a GC defect
or permission to change retention. Unmatched inbox custody and future release
paths remain outside this node and unimplemented by the kernel.

## Actual local verification and environment limits

All commands completed; no background process remains. Commands used login=false.

| Executed command/check | Observed result |
|---|---|
| `git status --short` at start | Exit 0, clean; Git emitted sandbox cache/global-ignore warnings. |
| `git rev-parse HEAD origin/main` | Exit 0, both `9aa464b6b9d89cdf1da65f828b55e6e97bf7bef0`. |
| Read-only Python comparison using `git show base:path` and current bytes for 14 task/governance/contract/plan inputs | Exit 0, all identical; selected original node spec read from pinned program. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before/after | Exit 0; `69564b166f0c27f9af5d8422f0a466b18d74c20f` / `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| From `runtime/`: `cargo test -p kix-kernel --test contract_edge_cases --test e4_state_model --test contract_invariants` | Exit 127: sandbox reports `operation not permitted: cargo`; tests did not execute. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | Exit 127, same denial; no workspace test PASS. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | Exit 127, same denial; no Clippy PASS. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 127, same denial; no formatting PASS. |
| `python3 --version` | Exit 0, Python 3.10.1. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 1, missing `tomllib`; architecture verification did not execute. |
| `python3 scripts/test_runtime_architecture.py` | Exit 1, same missing module; architecture tests did not execute. |
| Explicit `/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12` attempts for each architecture command | Exit 127, interpreter absent; no substitute PASS. |

No interpreter shim, toolchain installation, policy/CI alteration or sandbox
bypass was introduced. The final handoff also checks whitespace, evidence links
and tracked-tree preservation; those are documentation checks, not Rust tests.

## Acceptance and later-stage gates

This review record maps all eight audit requirements and all five invariant
predicates to existing assertions. New evidence addresses the residual review
and current-versus-historical authority distinction; no duplicate regression is
needed. Only this new note changes; locked sources, task inputs, historical
evidence, `.aiops/program.json`, CI and `reference/v0.3-rc1/**` remain unchanged.

Independent non-author review remains required. The app owns Draft publication,
exact-head hosted CI collection, the A2/NONE audit gate and final supervision.
No trust qualification is asserted from the supplied `MAC_CODEX_TRUST_REQUIRED`
marker. This handoff does not approve publication or override host trust checks.
Both KTX kernel verification and KIX protocol verification must be verified at
the actual published head before ready/merge acceptance; skipped Draft jobs and
documentation-only heavy-step skips are not full kernel/protocol test evidence.
Hosted full verification must cover the unexecuted kernel/E-4/invariant tests,
workspace tests, formatting, Clippy and Python architecture checks, plus required
protocol stages. No hosted run was queried or claimed by this implementation role.

No durability, recovery, distributed fencing, bank exactly-once, chain finality,
legal compliance, performance/SLO, production readiness or overall first-batch
completion claim. No real funds/provider calls, public endpoint, chain execution,
R2, replication, storage engine, PR #11 integration, lifecycle release/GC/index,
new policy value or protocol command was introduced. External inputs I02–I13
retain their recorded owners/status; this review closes none of them. Separate
cut proof, adapter identity, integration close-out, architecture adoption and
release decisions remain separately gated nodes/decisions.
