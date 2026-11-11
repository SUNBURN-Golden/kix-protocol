# feature-ir-plan-limit-edge-tests

Node: `plan-feature-ir-plan-limit-edge-tests`. Edge tests for the FeatureIR validator limits stated in
`runtime/FEATURE_SEMANTICS_V1.md` §10 (1,024 stages, depth 64, 100,000 nodes).
Issue: none. Depends on: none. Audit floor A2. `astra_gate: None`, `user_merge: false`.
Loop-proposed node, not in `.aiops/program.json`. No ASTRA markers were posted.

This session did not commit, push, open a pull request, create or close an issue, or comment.
There is no implementation commit SHA and no final task head SHA. Local results below are not
exact-head CI. Exact-head CI for the final head is not recorded in the commit (AGENTS §11); it
belongs in the PR closure report.

Observed `origin/main` and branch HEAD at session start: `a013cb0c471be0422a4a70d6b98e86c03f7131fa`
(merge of PR #194). `git fetch origin main` left it unchanged (no delta).

## Locks

| File | Required blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

No change under `runtime/crates/kix-feature-ir/src`, to existing tests, `Cargo.toml`, `Cargo.lock`,
`reference/v0.3-rc1/**`, `.aiops/`, `.github/` or `docs/tasks/`.

## Contract sentence (FEATURE_SEMANTICS_V1 §10)

> plan은 최대 1,024 stages, 표현식은 깊이 64 및 총 100,000 nodes를 허용한다. wire 크기/파서 할당 제한은 별도의 구현 gate다.

## Existing coverage (before this node)

| Limit | Coverage | Evidence |
|---|---|---|
| 1,024 stages | not covered | no test |
| depth 64 | partial | `runtime/crates/kix-feature-ir/tests/schema_bound.rs` `excessively_nested_expression_is_rejected_without_unbounded_walk`: 66 `Not` wrappers, rejection only, structural entry only; neither side of the boundary pinned |
| 100,000 nodes | not covered | the `remaining == 0` path was never exercised |

## New tests (`runtime/crates/kix-feature-ir/tests/plan_limits.rs`)

All are characterization of contract-stated limits. Each asserts that `validate()` and
`validate_with_schemas()` give the same result, and rejections are exactly `PlanTooComplex`.
Fixtures assert their own node count and depth, so "exactly N" does not rest on the validator.

| Test | Gap closed |
|---|---|
| `characterize_stage_limit_with_limit_stages` | 1,024 accepted, 1,025 rejected |
| `characterize_stage_limit_with_mixed_stage_kinds` | same boundary with Limit/Filter/Sort stages |
| `characterize_depth_limit_for_filter_predicate` | 64 `Not` wrappers accepted, 65 rejected |
| `characterize_depth_limit_for_project_item` | same boundary for a Project item, binary left spine |
| `characterize_depth_limit_restarts_for_each_expression` | depth is per expression: two 64-deep filters accepted |
| `characterize_node_limit_for_single_filter` | exactly 100,000 nodes accepted, 100,001 rejected (balanced tree) |
| `characterize_node_budget_is_plan_wide_across_stages_and_items` | 40,000 + 30,000 + 20,000 + 10,000 across Filter, a two-item Project and Filter accepted; 10,001 in the last part rejected. No part exceeds 40,001, so the budget is plan-wide, not per expression or per stage |

## AGENTS §8 classification

- **Class A (contract-defined and matching):** the 1,024-stage boundary; the numeric 100,000-node boundary under the counting below.
- **Class B (contract undefined), recorded as characterization:**
  1. *Depth counting.* The contract does not say how depth is counted. Today the root is depth 0, so 64 wrappers around a leaf (65 nodes on the longest path) are accepted and 65 are rejected. If "depth 64" meant 64 levels with the root as level 1, the code would accept one level too many; that would be a class C finding needing a separate explicit decision. This node does not decide it and does not amend the contract.
  2. *What counts as a node.* Today every `Expr` variant counts, leaves included. The contract does not say.
  3. *Scope of the node budget.* The contract does not say whether the total is per expression or per plan. Today it is one plan-wide counter over all Filter predicates and Project items.
- **Class C (explicit violation):** none found; all tests pass on unmodified `src/`.

## Commands actually run (all from the worktree root)

| Command | Result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD` | both `a013cb0c…`, no delta |
| `git hash-object` on both locked files (before and after) | both match required blobs |
| `rustfmt --edition 2024 runtime/crates/kix-feature-ir/tests/plan_limits.rs` | formatted |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-feature-ir --locked` | pass; `plan_limits` 7 passed |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | pass |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings` | pass |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked` | pass, no failures |
| `python3 scripts/verify_runtime_architecture.py`; `scripts/test_runtime_architecture.py` | OK; OK |
| `check_docs_index`, `check_status_register`, `check_rs_profile_traceability`, `check_read_model_source_map`, each plain and `--self-test` | exit 0 |
| Sensitivity check on a copy of `runtime/` under `/tmp` (own target dir, removed afterwards): `MAX_STAGES`, `MAX_EXPR_DEPTH`, `MAX_EXPR_NODES` each ±1 | every one of the six mutations fails at least two `plan_limits` tests; the worktree `src/` was never mutated |

Not run locally: the Python gate and reference suites, SDK, verify_runtime/commerce/canonical,
storage probes, localnet, ZK and Sui steps. They are unaffected by this change and run in hosted CI.

## Non-claims

- These are in-memory validator tests. They are not an authenticated-exporter, wire-parser, Polars/DuckDB or GPU result.
- They are not a new budget or policy value; no limit, error variant or `src/` file changed.
- Wire-size and parser-allocation limits (a separate gate per the contract) are not tested or claimed.
- They are not a time, memory or stack bound.
- Test count is not a completion criterion.

## Remaining uncertainty and follow-ups

- The depth-counting convention (class B item 1) stays open; any contract clarification needs separate explicit authorization.
- Add `plan_limits` to the capability register EV-IR row in a later sync node.
