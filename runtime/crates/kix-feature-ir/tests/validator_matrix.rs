//! Public-API regression matrices for FEATURE_SEMANTICS_V1 §§4 and 10.
use kix_feature_ir::*;
use kix_feature_semantics::*;
use kix_types::KixId;

const JOIN_KINDS: [JoinKind; 4] = [
    JoinKind::Inner,
    JoinKind::Left,
    JoinKind::Semi,
    JoinKind::Anti,
];
const INTEGER_KINDS: [OutputKind; 2] = [OutputKind::I64, OutputKind::U64];

fn dataset(byte: u8) -> DatasetRef {
    DatasetRef {
        dataset_id: KixId::from_bytes([byte; 16]),
        schema_version: 1,
    }
}

fn schema(byte: u8, columns: &[(u16, OutputKind)]) -> DatasetSchema {
    DatasetSchema {
        dataset: dataset(byte),
        columns: columns
            .iter()
            .map(|&(id, kind)| ColumnSchema {
                column: ColumnId(id),
                kind,
            })
            .collect(),
    }
}

fn catalog() -> Vec<DatasetSchema> {
    vec![
        schema(
            2,
            &[
                (1, OutputKind::I64),
                (2, OutputKind::I64),
                (6, OutputKind::U64),
                (7, OutputKind::U64),
                (3, OutputKind::Bool),
            ],
        ),
        schema(3, &[(4, OutputKind::I64), (5, OutputKind::Bytes)]),
    ]
}

fn plan(stages: Vec<Stage>) -> FeaturePlanV1 {
    FeaturePlanV1 {
        plan_id: KixId::from_bytes([1; 16]),
        source: dataset(2),
        stages,
    }
}

fn col(id: u16) -> Expr {
    Expr::Column(ColumnId(id))
}

fn integer(kind: OutputKind) -> Expr {
    Expr::Literal(match kind {
        OutputKind::I64 => Scalar::I64(2),
        OutputKind::U64 => Scalar::U64(2),
        _ => unreachable!("integer fixture only"),
    })
}

fn arithmetic(op: ArithmeticOp, left: Expr, right: Expr) -> Expr {
    Expr::Arithmetic {
        op,
        overflow: OverflowPolicy::Error,
        left: Box::new(left),
        right: Box::new(right),
    }
}

fn divide(numerator: Expr, denominator: Expr) -> Expr {
    Expr::DivideToF64 {
        numerator: Box::new(numerator),
        denominator: Box::new(denominator),
        divide_by_zero: DivideByZeroPolicy::Null,
    }
}

fn filter(predicate: Expr) -> Stage {
    Stage::Filter {
        predicate,
        null_predicate: NullPredicatePolicy::Drop,
    }
}

fn project(expr: Expr, output_kind: OutputKind) -> Stage {
    Stage::Project(vec![Projection {
        output: ColumnId(9),
        output_kind,
        expr,
    }])
}

fn join_to(right: DatasetRef, kind: JoinKind, right_key: u16) -> Stage {
    Stage::Join(JoinSpec {
        right,
        kind,
        left_key: ColumnId(1),
        right_key: ColumnId(right_key),
        null_equality: NullEquality::Unequal,
    })
}

fn assert_both(candidate: &FeaturePlanV1, expected: Result<(), FeatureIrError>) {
    assert_eq!(candidate.validate(), expected, "preflight: {candidate:?}");
    assert_eq!(
        candidate.validate_with_schemas(&catalog()).map(|_| ()),
        expected,
        "schema-bound: {candidate:?}"
    );
}

#[test]
fn join_right_dataset_identity_and_version_failure_matrix() {
    let mut wrong_version = dataset(3);
    wrong_version.schema_version = 2;
    let mut zero_version = dataset(3);
    zero_version.schema_version = 0;
    for kind in JOIN_KINDS {
        for right in [dataset(4), wrong_version] {
            let candidate = plan(vec![join_to(right, kind, 4)]);
            // Class A: §10 preflight has no catalog; it cannot resolve identity.
            assert_eq!(candidate.validate(), Ok(()));
            assert_eq!(
                candidate.validate_with_schemas(&catalog()).map(|_| ()),
                Err(FeatureIrError::UnknownDataset),
                "{kind:?}, {right:?}"
            );
        }
        let candidate = plan(vec![join_to(dataset(3), kind, 4)]);
        let mut schemas = catalog();
        schemas[1].dataset.schema_version = 2;
        assert_eq!(
            candidate.validate_with_schemas(&schemas).map(|_| ()),
            Err(FeatureIrError::UnknownDataset),
            "catalog has only v2: {kind:?}"
        );
        assert_both(&candidate, Ok(()));
        assert_both(
            &plan(vec![join_to(zero_version, kind, 4)]),
            Err(FeatureIrError::InvalidSchema),
        );
    }
}

#[test]
fn join_right_version_selects_its_own_schema() {
    let mut schemas = catalog();
    let mut v2 = schema(3, &[(8, OutputKind::I64)]);
    v2.dataset.schema_version = 2;
    let right = v2.dataset;
    schemas.push(v2);
    for kind in JOIN_KINDS {
        assert_eq!(
            plan(vec![join_to(right, kind, 4)])
                .validate_with_schemas(&schemas)
                .map(|_| ()),
            Err(FeatureIrError::UnknownColumn),
            "v1 key cannot bind v2: {kind:?}"
        );
        let candidate = plan(vec![join_to(right, kind, 8)]);
        let checked = candidate.validate_with_schemas(&schemas).unwrap();
        if matches!(kind, JoinKind::Inner | JoinKind::Left) {
            assert!(checked.output_schema().contains(&ColumnSchema {
                column: ColumnId(8),
                kind: OutputKind::I64,
            }));
            assert!(
                checked
                    .output_schema()
                    .iter()
                    .all(|c| c.column != ColumnId(4))
            );
        }
    }
}

// Each operand independently ranges over a literal, catalog column and a
// same-type arithmetic tree. Numeric values do not imply execution evidence.
fn operands(kind: OutputKind, denominator: bool) -> [Expr; 3] {
    let id = match (kind, denominator) {
        (OutputKind::I64, false) => 1,
        (OutputKind::I64, true) => 2,
        (OutputKind::U64, false) => 6,
        (OutputKind::U64, true) => 7,
        _ => unreachable!("integer fixture only"),
    };
    [
        integer(kind),
        col(id),
        arithmetic(ArithmeticOp::Mul, col(id), integer(kind)),
    ]
}

#[test]
fn divide_to_f64_root_operand_type_matrix() {
    let schemas = catalog();
    for numerator_kind in INTEGER_KINDS {
        for denominator_kind in INTEGER_KINDS {
            let expected = if numerator_kind == denominator_kind {
                Ok(())
            } else {
                Err(FeatureIrError::ExpressionTypeMismatch)
            };
            for (i, numerator) in operands(numerator_kind, false).into_iter().enumerate() {
                for (j, denominator) in operands(denominator_kind, true).into_iter().enumerate() {
                    let candidate = plan(vec![project(
                        divide(numerator.clone(), denominator),
                        OutputKind::TerminalF64,
                    )]);
                    let checked = candidate.validate_with_schemas(&schemas);
                    assert_eq!(
                        checked.as_ref().map(|_| ()).map_err(|&e| e),
                        expected,
                        "{numerator_kind:?}/{denominator_kind:?}, operand shapes {i}/{j}"
                    );
                    if let Ok(checked) = checked {
                        assert_eq!(
                            checked.output_schema(),
                            &[ColumnSchema {
                                column: ColumnId(9),
                                kind: OutputKind::TerminalF64,
                            }]
                        );
                    }
                    if i == 0 && j == 0 {
                        assert_eq!(candidate.validate(), expected);
                    }
                }
            }
        }
    }
    // An outer matching type must not hide coercion inside either operand.
    for kind in INTEGER_KINDS {
        let other = if kind == OutputKind::I64 {
            OutputKind::U64
        } else {
            OutputKind::I64
        };
        let mixed = arithmetic(ArithmeticOp::Add, integer(kind), integer(other));
        for expr in [
            divide(mixed.clone(), integer(kind)),
            divide(integer(kind), mixed),
        ] {
            assert_both(
                &plan(vec![project(expr, OutputKind::TerminalF64)]),
                Err(FeatureIrError::ExpressionTypeMismatch),
            );
        }
    }
}

#[test]
fn divide_to_f64_placement_and_output_kind_matrix() {
    for kind in INTEGER_KINDS {
        let ratio = divide(integer(kind), integer(kind));
        for output_kind in INTEGER_KINDS {
            assert_both(
                &plan(vec![project(ratio.clone(), output_kind)]),
                Err(FeatureIrError::TerminalF64KindMismatch),
            );
        }
        assert_both(
            &plan(vec![project(integer(kind), OutputKind::TerminalF64)]),
            Err(FeatureIrError::TerminalF64KindMismatch),
        );
        for expr in [
            arithmetic(ArithmeticOp::Add, ratio.clone(), integer(kind)),
            arithmetic(ArithmeticOp::Add, integer(kind), ratio.clone()),
        ] {
            assert_both(
                &plan(vec![project(expr, kind)]),
                Err(FeatureIrError::TerminalF64MustBeFinal),
            );
        }
        assert_both(
            &plan(vec![filter(Expr::Compare {
                op: CompareOp::Lt,
                left: Box::new(ratio.clone()),
                right: Box::new(integer(kind)),
            })]),
            Err(FeatureIrError::TerminalF64MustBeFinal),
        );
        assert_both(
            &plan(vec![
                project(ratio, OutputKind::TerminalF64),
                Stage::Limit(10),
            ]),
            Ok(()),
        );
    }
}

#[test]
fn implicit_signed_unsigned_coercion_is_rejected_in_compare_and_arithmetic() {
    for left in INTEGER_KINDS {
        for right in INTEGER_KINDS {
            let expected = if left == right {
                Ok(())
            } else {
                Err(FeatureIrError::ExpressionTypeMismatch)
            };
            for op in [ArithmeticOp::Add, ArithmeticOp::Sub, ArithmeticOp::Mul] {
                assert_both(
                    &plan(vec![project(
                        arithmetic(op, integer(left), integer(right)),
                        left,
                    )]),
                    expected,
                );
            }
            for op in [
                CompareOp::Eq,
                CompareOp::Ne,
                CompareOp::Lt,
                CompareOp::Le,
                CompareOp::Gt,
                CompareOp::Ge,
            ] {
                let comparison = Expr::Compare {
                    op,
                    left: Box::new(integer(left)),
                    right: Box::new(integer(right)),
                };
                for predicate in [
                    comparison.clone(),
                    Expr::Not(Box::new(comparison.clone())),
                    Expr::And(
                        Box::new(Expr::Literal(Scalar::Bool(true))),
                        Box::new(comparison),
                    ),
                ] {
                    assert_both(&plan(vec![filter(predicate)]), expected);
                }
            }
        }
    }
}

fn aggregate_specs() -> [AggregateSpec; 5] {
    // Independent oracle: the explicit §4 table, not empty_policy(). Each
    // mismatch case changes only this policy, leaving input/output valid.
    [
        (
            AggregateOp::Count,
            None,
            OutputKind::U64,
            EmptyAggregatePolicy::Zero,
        ),
        (
            AggregateOp::Sum,
            Some(1),
            OutputKind::I64,
            EmptyAggregatePolicy::Null,
        ),
        (
            AggregateOp::Min,
            Some(1),
            OutputKind::I64,
            EmptyAggregatePolicy::Null,
        ),
        (
            AggregateOp::Max,
            Some(1),
            OutputKind::I64,
            EmptyAggregatePolicy::Null,
        ),
        (
            AggregateOp::Mean,
            Some(1),
            OutputKind::TerminalF64,
            EmptyAggregatePolicy::Null,
        ),
    ]
    .map(|(op, input, output_kind, empty_policy)| AggregateSpec {
        output: ColumnId(9),
        output_kind,
        op,
        input: input.map(ColumnId),
        null_policy: NullValuePolicy::Ignore,
        empty_policy,
        overflow_policy: OverflowPolicy::Error,
    })
}

fn group(aggregate: AggregateSpec) -> Stage {
    Stage::GroupBy {
        keys: vec![],
        aggregates: vec![aggregate],
        null_keys: NullKeyPolicy::Include,
    }
}

#[test]
fn aggregate_empty_policy_mismatch_is_rejected_for_every_op() {
    for mut spec in aggregate_specs() {
        spec.empty_policy = match spec.empty_policy {
            EmptyAggregatePolicy::Zero => EmptyAggregatePolicy::Null,
            EmptyAggregatePolicy::Null => EmptyAggregatePolicy::Zero,
        };
        assert_both(
            &plan(vec![group(spec)]),
            Err(FeatureIrError::AggregatePolicyMismatch),
        );
    }
}

#[test]
fn aggregate_contract_empty_policy_control_validates() {
    for spec in aggregate_specs() {
        assert_both(&plan(vec![group(spec)]), Ok(()));
    }
}
