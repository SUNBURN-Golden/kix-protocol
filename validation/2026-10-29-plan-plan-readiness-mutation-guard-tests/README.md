# Readiness boundary mutation guards

Node: `plan-plan-readiness-mutation-guard-tests`. Task input: the supervisor's
supplied node specification and read-only design plan; no issue or node-specific
`docs/tasks/` document exists. Source: planner run `1793200863`
(`/workspace/kix-run/logs/planner_1793200863`). Dependencies: `readiness-extensions`,
`plan-readiness-crash-point-sweep`, `plan-readiness-conformance-negative-controls`.
Non-ASTRA session; audit floor A2; no publication or merge authorization.

## Source and coverage mapped before adding tests

Local observed `origin/main`, starting branch HEAD and base all equal
`04efe5beddb5621c96690ee5e5e02922e2f9781c`; local base delta is zero.
Branch: `agent/kix-plan-plan-readiness-mutation-guard-tests`.
Fetch was NOT RUN under the supervisor's no-network instruction, overriding
AGENTS §1; remote freshness is unverified. No task-base change was made.

| Requirement | Prior coverage and classification | Added evidence |
|---|---|---|
| Successful callback rewrites a journal prefix | Not covered: neither `CrashPointSweepTests` nor `ConformanceSensitivityTests` injects this callback behavior | `BoundaryMutationGuardTests.test_journal_rewrite_fences_without_persisting` |
| Successful callback changes only the state digest | Not covered by those suites | `test_unjournaled_mutation_fences_without_persisting` |
| Mutating callback raises; preserve original exception | Not covered by those suites | `test_mutation_then_exception_preserves_original_and_fences`, rewrite and digest subtests |
| Fencing and committed-prefix recovery | Partially covered: `readiness/test_faults.py::CrashPointSweepTests._sweep_case` checks append-fault closure/recovery | Every mutation case also checks unchanged bytes, full records/count, byte accounting, zero subsequent callback invocations on reservation and settlement, real restore after close |
| Nonmutating calls keep boundary usable | Partially covered: `readiness/conformance.py::BackendConformance.test_ai_delegation_registry_opens_once_and_issue_replays_across_restart` and `test_reward_open_observe_and_hold_replay_across_restart` cover duplicates and repeated-open exceptions | Explicit success and exception controls, each followed by a valid journaled reservation hold |
| Append faults and faulty adapters | Sufficient: `CrashPointSweepTests._sweep_case` (both append faults); `readiness/test_conformance_sensitivity.py::ConformanceSensitivityTests` (seven faulty adapters and unmodified control) | Retained unchanged; no duplicate scenarios |

These are source-informed, injected local-wrapper characterizations of
`FsmBoundary.call`, outside `BackendConformance` requirements. The persisted
prefix comes from a real reservation machine; only one boundary's machine is
replaced by a test-local journal/digest double. Recovery uses real restore.

## Verification

Five new test methods cover four injected mutation cases (two success paths
and two exception subtests) and two controls. The first execution was the new
class, followed by the combined readiness modules. The combined command runs
sensitivity tests both via the retained import and the explicit module; 72 is
the runner's execution count, not a claim of 72 unique tests. All commands
below were actually run from the repository root. No failing test or local
verification required an implementation fix.

| Command | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest readiness.test_faults.BoundaryMutationGuardTests` | PASS, 5 tests; exception test has rewrite and digest subtests |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest readiness.test_faults readiness.test_conformance_sensitivity` | PASS, 72 test executions, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_docs_index.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_test_discovery.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_test_discovery.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_readiness_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_readiness_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_loopback_host.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_status_register.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_profile_traceability.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_profile_traceability.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_read_model_source_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_read_model_source_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_i12_proof_ids.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_i12_proof_ids.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_delegation_layer_matrix.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_delegation_layer_matrix.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_predicate_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_im_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_rs_im_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_tl_predicate_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_error_codes.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_error_codes.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_adapter_identity_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_adapter_identity_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_v5_transition_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_v5_transition_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_settlement_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_settlement_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bra_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bra_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_credit_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_credit_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_primary_price_fee_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ai_delegation_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ai_delegation_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_lifecycle_adr_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_invariants_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_contract_invariants_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_toss_card_profile_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bcs1_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_bcs1_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_performance_measurement_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_performance_measurement_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_feature_semantics_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_feature_semantics_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_integration_gate_contract_evidence_map.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_evidence_map_rollup.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_evidence_map_rollup.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_class_b_index.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_class_b_index.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_checker_wiring.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_ci_checker_wiring.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_cargo_offline_cache.py` | PASS, exit 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_cargo_offline_cache.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_stage5_host.py --self-test` | PASS, exit 0; self-test passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_runtime_architecture.py` | PASS, architecture v5 + KTX-R1 dependency gate |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_runtime_architecture.py` | PASS, 7 tests |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS, exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | PASS, all workspace tests and doc-tests, including kix-kernel; exit 0 |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | PASS, exit 0 |
| `git diff --check` | PASS, exit 0 |
| `git rev-parse HEAD` | 04efe5beddb5621c96690ee5e5e02922e2f9781c |
| `git rev-parse origin/main` | 04efe5beddb5621c96690ee5e5e02922e2f9781c (local ref only) |
| `git branch --show-current` | agent/kix-plan-plan-readiness-mutation-guard-tests |

The offline document step's socket-free commands all passed (62 executions,
including self-tests). The plain Cargo cache inspection reported all 18
registry archives present; actual offline test and Clippy success, rather
than archive presence alone, supplies compilation evidence.

## Protected files and final scope

Before and after implementation, an inline Python verifier ran `git hash-object`
on each locked file and compared it to the required blob. It also generated a
sorted mapping of every protected reference path to its SHA-256 byte hash;
the after-work mapping equals the saved before-work mapping, including its
complete path set.

| Protected asset | Before | After |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, PASS | Same required blob, PASS |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20`, PASS | Same required blob, PASS |
| `reference/v0.3-rc1/**` | 108 files; path/SHA-256 mapping saved before edits | Identical 108 paths and byte hashes, PASS |

Reference manifest SHA-256 (JSON mapping serialized with `sort_keys=True`):
`dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
No merge was performed, so final-merge lock verification is not applicable.

Complete changed-path list:

- `readiness/test_faults.py`: test-local double, five tests and assertions.
- `readiness/CONFORMANCE.md`: labeled coverage mapping and limits.
- `validation/2026-10-29-plan-plan-readiness-mutation-guard-tests/README.md`: this record.
- `docs/README.md`: one relative link to this record.

Implementation content is uncommitted in the worktree. Implementation/final
committed head is therefore not established; unchanged branch HEAD is the
starting SHA above. The supervisor owns commit/push/publication. No wrapper,
FSM, common conformance requirement, contract, CI, SDK, `.aiops/` or task
input changed.

## Gates, deviations and discrepancies

| Gate | Run ID | Status / conclusion |
|---|---|---|
| Exact-head KTX kernel verification | None | NOT_RUN / unavailable; supervisor must establish final committed head |
| Exact-head KIX protocol verification | None | NOT_RUN / unavailable; no older SHA success transferred |
| Non-author exact-head review / applicable A2 audit | None | Outstanding; builder evidence is not review |
| Merge / post-merge main CI | None | Not performed / not applicable |

Design followed within the four authorized paths. Session-start fetch was
excluded by the later supervisor no-network rule. The plain
`python3 scripts/check_loopback_host.py` and
`integration_gate.test_http_gate` were NOT RUN because they use real sockets;
the injected loopback self-test and readiness component ran. Full hosted
workflows, backend provisioning, paid-storage probes and Sui were not run.
No authorization or CI gate is waived by these local exclusions.

No explicit contract violation was found. Characterization (AGENTS §8 class B):
successful journal rewrite is reported as `JOURNAL_REWRITE`, successful
digest-only mutation as `UNJOURNALED_MUTATION`; either mutating callback failure
preserves the original exception object and observes `UNJOURNALED_MUTATION`.
These observation/error details are implementation characterizations, not new
contract semantics. Neither failed in-memory object is asserted to roll back.
Nonmutating return/exception identity and continued usability are controls.

Remaining uncertainty/follow-up: exact-head hosted checks and independent
review are outstanding; pre-existing journal-corruption/recovery uncertainties
and open product-policy decisions stay open with their existing owners. No
additional implementation or policy decision is needed for this local node.

## Limits

No rollback, power-loss, OS-crash, physical-media/fsync, production durability,
distributed fencing, backend adoption, external exactly-once, chain finality or
production-readiness proof. No product-policy value or evidence-map grade is
changed. Existing recovery uncertainties remain UNDETERMINED. A failed in-memory
machine is not asserted to have rolled back. No contracts or implementations
are changed. Builder evidence is not independent review or merge readiness.
