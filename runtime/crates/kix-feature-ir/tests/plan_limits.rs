//! Characterization of the plan limits stated in `runtime/FEATURE_SEMANTICS_V1.md` section 10:
//! at most 1,024 stages, expression depth 64 and 100,000 expression nodes in total.
//!
//! These are in-memory validator tests through the public `validate()` and
//! `validate_with_schemas()` API. They pin both sides of each boundary as it behaves today.
//! They are not a wire-size, parser-allocation, authenticated-exporter, Polars, DuckDB or GPU
//! result, and they do not introduce a budget or policy value. The contract does not say how
//! depth is counted; the root is depth 0 here (AGENTS section 8 class B, see
//! validation/2026-10-16-feature-ir-plan-limit-edge-tests/).
use kix_feature_ir::*;
use kix_feature_semantics::*;
use kix_types::KixId;

// Duplicated on purpose: the constants in `src/validation.rs` are private.
const MAX_STAGES: usize = 1_024;
const MAX_EXPR_DEPTH: usize = 64;
const MAX_EXPR_NODES: usize = 100_000;

fn dataset(byte: u8) -> DatasetRef {
    DatasetRef {
        dataset_id: KixId::from_bytes([byte; 16]),
        schema_version: 1,
    }
}

fn catalog() -> Vec<DatasetSchema> {
    vec![DatasetSchema {
        dataset: dataset(2),
        columns: [
            (1, OutputKind::I64),
            (2, OutputKind::I64),
            (3, OutputKind::Bool),
        ]
        .into_iter()
        .map(|(id, kind)| ColumnSchema {
            column: ColumnId(id),
            kind,
        })
        .collect(),
    }]
}

fn plan(stages: Vec<Stage>) -> FeaturePlanV1 {
    FeaturePlanV1 {
        plan_id: KixId::from_bytes([1; 16]),
        source: dataset(2),
        stages,
    }
}

fn filter(predicate: Expr) -> Stage {
    Stage::Filter {
        predicate,
        null_predicate: NullPredicatePolicy::Drop,
    }
}

fn project(items: Vec<(u16, OutputKind, Expr)>) -> Stage {
    Stage::Project(
        items
            .into_iter()
            .map(|(output, output_kind, expr)| Projection {
                output: ColumnId(output),
                output_kind,
                expr,
            })
            .collect(),
    )
}

fn sort() -> Stage {
    Stage::Sort {
        by: vec![ColumnId(1)],
        descending: false,
        null_order: NullOrder::Last,
        stability: SortStability::Stable,
    }
}

fn leaf() -> Expr {
    Expr::Literal(Scalar::Bool(true))
}

/// Number of nodes in `expr`, leaves included.
fn nodes(expr: &Expr) -> usize {
    1 + match expr {
        Expr::Column(_) | Expr::Literal(_) => 0,
        Expr::Compare { left, right, .. } | Expr::Arithmetic { left, right, .. } => {
            nodes(left) + nodes(right)
        }
        Expr::DivideToF64 {
            numerator,
            denominator,
            ..
        } => nodes(numerator) + nodes(denominator),
        Expr::And(left, right) | Expr::Or(left, right) => nodes(left) + nodes(right),
        Expr::Not(inner) => nodes(inner),
    }
}

/// Wrapper depth of `expr`; the root is depth 0, so a lone leaf has depth 0.
fn depth(expr: &Expr) -> usize {
    match expr {
        Expr::Column(_) | Expr::Literal(_) => 0,
        Expr::Compare { left, right, .. } | Expr::Arithmetic { left, right, .. } => {
            1 + depth(left).max(depth(right))
        }
        Expr::DivideToF64 {
            numerator,
            denominator,
            ..
        } => 1 + depth(numerator).max(depth(denominator)),
        Expr::And(left, right) | Expr::Or(left, right) => 1 + depth(left).max(depth(right)),
        Expr::Not(inner) => 1 + depth(inner),
    }
}

/// `wrappers` nested `Not` around a Bool literal: depth == `wrappers`.
fn not_chain(wrappers: usize) -> Expr {
    let mut expr = leaf();
    for _ in 0..wrappers {
        expr = Expr::Not(Box::new(expr));
    }
    assert_eq!(depth(&expr), wrappers);
    expr
}

/// Left-nested `Add` chain over I64 literals: depth == `wrappers`.
fn add_chain(wrappers: usize) -> Expr {
    let one = || Expr::Literal(Scalar::I64(1));
    let mut expr = one();
    for _ in 0..wrappers {
        expr = Expr::Arithmetic {
            op: ArithmeticOp::Add,
            overflow: OverflowPolicy::Error,
            left: Box::new(expr),
            right: Box::new(one()),
        };
    }
    assert_eq!(depth(&expr), wrappers);
    expr
}

/// Balanced Bool expression with exactly `n` nodes (small depth, no deep recursion).
fn bool_tree(n: usize) -> Expr {
    assert!(n >= 1);
    let expr = match n {
        1 => leaf(),
        2 => Expr::Not(Box::new(leaf())),
        _ => {
            let rest = n - 1;
            Expr::And(
                Box::new(bool_tree(rest / 2)),
                Box::new(bool_tree(rest - rest / 2)),
            )
        }
    };
    debug_assert_eq!(nodes(&expr), n);
    expr
}

/// Result of both entry points, which must agree. Kept compact so a failure does not print
/// a 100,000-node `Debug` dump.
fn both(plan: &FeaturePlanV1) -> Result<(), FeatureIrError> {
    let structural = plan.validate();
    let schema_bound = plan.validate_with_schemas(&catalog()).map(|_| ());
    assert_eq!(structural, schema_bound, "entry points disagree");
    structural
}

fn assert_accepted(plan: &FeaturePlanV1) {
    assert_eq!(both(plan), Ok(()));
}

fn assert_too_complex(plan: &FeaturePlanV1) {
    assert_eq!(both(plan), Err(FeatureIrError::PlanTooComplex));
}

#[test]
fn characterize_stage_limit_with_limit_stages() {
    let at = |n: usize| plan(vec![Stage::Limit(1); n]);
    assert_accepted(&at(MAX_STAGES));
    assert_too_complex(&at(MAX_STAGES + 1));
}

#[test]
fn characterize_stage_limit_with_mixed_stage_kinds() {
    let at = |n: usize| {
        plan(
            (0..n)
                .map(|i| match i % 3 {
                    0 => Stage::Limit(1),
                    1 => filter(leaf()),
                    _ => sort(),
                })
                .collect(),
        )
    };
    assert_accepted(&at(MAX_STAGES));
    assert_too_complex(&at(MAX_STAGES + 1));
}

#[test]
fn characterize_depth_limit_for_filter_predicate() {
    assert_accepted(&plan(vec![filter(not_chain(MAX_EXPR_DEPTH))]));
    assert_too_complex(&plan(vec![filter(not_chain(MAX_EXPR_DEPTH + 1))]));
}

#[test]
fn characterize_depth_limit_for_project_item() {
    let at = |w: usize| plan(vec![project(vec![(9, OutputKind::I64, add_chain(w))])]);
    assert_accepted(&at(MAX_EXPR_DEPTH));
    assert_too_complex(&at(MAX_EXPR_DEPTH + 1));
}

#[test]
fn characterize_depth_limit_restarts_for_each_expression() {
    let max = || filter(not_chain(MAX_EXPR_DEPTH));
    assert_accepted(&plan(vec![max(), max()]));
}

#[test]
fn characterize_node_limit_for_single_filter() {
    let at = |n: usize| plan(vec![filter(bool_tree(n))]);
    assert_accepted(&at(MAX_EXPR_NODES));
    assert_too_complex(&at(MAX_EXPR_NODES + 1));
}

#[test]
fn characterize_node_budget_is_plan_wide_across_stages_and_items() {
    // Filter(40,000), Project{30,000; 20,000}, Filter(last). No part exceeds 40,001 nodes, so
    // a per-expression or per-stage cap of 100,000 cannot explain the rejection of the
    // 100,001-node total.
    let at = |last: usize| {
        plan(vec![
            filter(bool_tree(40_000)),
            project(vec![
                (9, OutputKind::Bool, bool_tree(30_000)),
                (10, OutputKind::Bool, bool_tree(20_000)),
            ]),
            filter(bool_tree(last)),
        ])
    };
    assert_eq!(40_000 + 30_000 + 20_000 + 10_000, MAX_EXPR_NODES);
    assert_accepted(&at(10_000));
    assert_too_complex(&at(10_001));
}
