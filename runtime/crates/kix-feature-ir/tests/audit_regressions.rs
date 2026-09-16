//! Proposed audit regression tests for KIX commit
//! 0bbc9b9cd421b386a542a8ed4351fb6aaeff907a.
//!
//! Executed during remediation with Rust 1.98.1: all five negative cases
//! failed on the audited baseline and all three controls passed. All eight
//! pass after remediation. See validation/2026-09-15-audit-fix/ for logs.
//!
use kix_feature_ir::{
    AggregateOp, AggregateSpec, ColumnId, CompareOp, DatasetRef, Expr, FeaturePlanV1, OutputKind,
    Projection, Scalar, Stage,
};
use kix_feature_semantics::{
    DivideByZeroPolicy, EmptyAggregatePolicy, NullKeyPolicy, NullPredicatePolicy, NullValuePolicy,
    OverflowPolicy,
};
use kix_types::KixId;

fn plan(stages: Vec<Stage>) -> FeaturePlanV1 {
    FeaturePlanV1 {
        plan_id: KixId::from_bytes([1; 16]),
        source: DatasetRef {
            dataset_id: KixId::from_bytes([2; 16]),
            schema_version: 1,
        },
        stages,
    }
}

fn integer(value: i64) -> Expr {
    Expr::Literal(Scalar::I64(value))
}

fn ratio(numerator: Expr, denominator: Expr) -> Expr {
    Expr::DivideToF64 {
        numerator: Box::new(numerator),
        denominator: Box::new(denominator),
        divide_by_zero: DivideByZeroPolicy::Null,
    }
}

// A02 — both operands produce f64; comparison itself has a boolean result.
// The audited baseline skipped expression inspection for Filter.
#[test]
fn audit_a02_filter_must_reject_nonterminal_f64() {
    let candidate = plan(vec![Stage::Filter {
        predicate: Expr::Compare {
            op: CompareOp::Lt,
            left: Box::new(ratio(integer(1), integer(2))),
            right: Box::new(ratio(integer(3), integer(4))),
        },
        null_predicate: NullPredicatePolicy::Drop,
    }]);
    assert!(
        candidate.validate().is_err(),
        "Filter accepted f64 calculations before the terminal output"
    );
}

// A03 — the audited baseline skipped recursive checks inside an allowed root divide.
#[test]
fn audit_a03_terminal_divide_must_reject_nested_divide() {
    let candidate = plan(vec![Stage::Project(vec![Projection {
        output: ColumnId(9),
        output_kind: OutputKind::TerminalF64,
        expr: ratio(ratio(integer(1), integer(2)), integer(3)),
    }])]);
    assert!(
        candidate.validate().is_err(),
        "Terminal root divide accepted another f64 operation as an operand"
    );
}

// A04 — proposed type-validation gate. These are structural/type gaps, not
// claims of a deployed transaction exploit.
#[test]
fn audit_a04_filter_requires_a_boolean_expression() {
    let candidate = plan(vec![Stage::Filter {
        predicate: integer(1),
        null_predicate: NullPredicatePolicy::Drop,
    }]);
    assert!(
        candidate.validate().is_err(),
        "Filter accepted an i64 literal"
    );
}

#[test]
fn audit_a04_projection_kind_must_match_literal_type() {
    let candidate = plan(vec![Stage::Project(vec![Projection {
        output: ColumnId(9),
        output_kind: OutputKind::I64,
        expr: Expr::Literal(Scalar::Bool(true)),
    }])]);
    assert!(
        candidate.validate().is_err(),
        "Projection declared an i64 result for a boolean literal"
    );
}

#[test]
fn audit_a04_sum_requires_an_input_column() {
    let candidate = plan(vec![Stage::GroupBy {
        keys: vec![ColumnId(1)],
        aggregates: vec![AggregateSpec {
            output: ColumnId(9),
            output_kind: OutputKind::I64,
            op: AggregateOp::Sum,
            input: None,
            null_policy: NullValuePolicy::Ignore,
            empty_policy: EmptyAggregatePolicy::Null,
            overflow_policy: OverflowPolicy::Error,
        }],
        null_keys: NullKeyPolicy::Include,
    }]);
    assert!(
        candidate.validate().is_err(),
        "SUM accepted a missing input"
    );
}

// Positive controls: the audit must not ban every expression or terminal f64.
#[test]
fn audit_control_integer_comparison_filter_is_allowed() {
    let candidate = plan(vec![Stage::Filter {
        predicate: Expr::Compare {
            op: CompareOp::Lt,
            left: Box::new(integer(1)),
            right: Box::new(integer(2)),
        },
        null_predicate: NullPredicatePolicy::Drop,
    }]);
    assert!(candidate.validate().is_ok());
}

#[test]
fn audit_control_single_terminal_divide_then_limit_is_allowed() {
    let candidate = plan(vec![
        Stage::Project(vec![Projection {
            output: ColumnId(9),
            output_kind: OutputKind::TerminalF64,
            expr: ratio(integer(1), integer(2)),
        }]),
        Stage::Limit(10),
    ]);
    assert!(candidate.validate().is_ok());
}

#[test]
fn audit_control_count_star_may_omit_an_input() {
    let candidate = plan(vec![Stage::GroupBy {
        keys: vec![],
        aggregates: vec![AggregateSpec {
            output: ColumnId(9),
            output_kind: OutputKind::U64,
            op: AggregateOp::Count,
            input: None,
            null_policy: NullValuePolicy::Ignore,
            empty_policy: EmptyAggregatePolicy::Zero,
            overflow_policy: OverflowPolicy::Error,
        }],
        null_keys: NullKeyPolicy::Include,
    }]);
    assert!(candidate.validate().is_ok());
}
