use kix_feature_ir::*;
use kix_feature_semantics::*;
use kix_types::{AssetAmount, AssetId, Hash32, KixId, RegistryVersion};

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
            .map(|(id, kind)| ColumnSchema {
                column: ColumnId(*id),
                kind: *kind,
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
fn integer(value: i64) -> Expr {
    Expr::Literal(Scalar::I64(value))
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
fn project(expr: Expr, kind: OutputKind) -> Stage {
    Stage::Project(vec![Projection {
        output: ColumnId(9),
        output_kind: kind,
        expr,
    }])
}
fn sort(id: u16) -> Stage {
    Stage::Sort {
        by: vec![ColumnId(id)],
        descending: false,
        null_order: NullOrder::Last,
        stability: SortStability::Stable,
    }
}
fn join(kind: JoinKind) -> Stage {
    Stage::Join(JoinSpec {
        right: dataset(3),
        kind,
        left_key: ColumnId(1),
        right_key: ColumnId(4),
        null_equality: NullEquality::Unequal,
    })
}
fn aggregate(op: AggregateOp, input: Option<u16>, output_kind: OutputKind) -> AggregateSpec {
    AggregateSpec {
        output: ColumnId(9),
        output_kind,
        op,
        input: input.map(ColumnId),
        null_policy: NullValuePolicy::Ignore,
        empty_policy: if op == AggregateOp::Count {
            EmptyAggregatePolicy::Zero
        } else {
            EmptyAggregatePolicy::Null
        },
        overflow_policy: OverflowPolicy::Error,
    }
}
fn group(keys: Vec<ColumnId>, aggregate: AggregateSpec) -> Stage {
    Stage::GroupBy {
        keys,
        aggregates: vec![aggregate],
        null_keys: NullKeyPolicy::Include,
    }
}

#[test]
fn nested_f64_in_either_operand_and_boolean_wrappers_is_rejected() {
    let ratio = divide(integer(1), integer(2));
    for expr in [
        divide(ratio.clone(), integer(3)),
        divide(integer(3), ratio.clone()),
    ] {
        let candidate = plan(vec![project(expr, OutputKind::TerminalF64)]);
        assert_eq!(
            candidate.validate(),
            Err(FeatureIrError::TerminalF64MustBeFinal)
        );
    }
    let comparison = Expr::Compare {
        op: CompareOp::Lt,
        left: Box::new(ratio),
        right: Box::new(integer(3)),
    };
    for expr in [
        comparison.clone(),
        Expr::Not(Box::new(comparison.clone())),
        Expr::And(
            Box::new(Expr::Literal(Scalar::Bool(false))),
            Box::new(comparison.clone()),
        ),
        Expr::Or(
            Box::new(Expr::Literal(Scalar::Bool(true))),
            Box::new(comparison),
        ),
    ] {
        assert_eq!(
            plan(vec![filter(expr)]).validate(),
            Err(FeatureIrError::TerminalF64MustBeFinal)
        );
    }
}

#[test]
fn valid_integer_expression_can_feed_terminal_division() {
    let numerator = Expr::Arithmetic {
        op: ArithmeticOp::Mul,
        overflow: OverflowPolicy::Error,
        left: Box::new(col(1)),
        right: Box::new(integer(10)),
    };
    let candidate = plan(vec![
        filter(col(3)),
        sort(1),
        project(divide(numerator, col(2)), OutputKind::TerminalF64),
        Stage::Limit(10),
    ]);
    let schemas = catalog();
    let checked = candidate.validate_with_schemas(&schemas).unwrap();
    assert_eq!(
        checked.output_schema(),
        &[ColumnSchema {
            column: ColumnId(9),
            kind: OutputKind::TerminalF64
        }]
    );
    assert_eq!(checked.plan(), &candidate);
    assert_eq!(checked.catalog(), &schemas);
}

#[test]
fn terminal_mean_can_only_be_followed_by_limits() {
    let mean = group(
        vec![ColumnId(1)],
        aggregate(AggregateOp::Mean, Some(2), OutputKind::TerminalF64),
    );
    assert!(
        plan(vec![mean.clone(), Stage::Limit(10)])
            .validate_with_schemas(&catalog())
            .is_ok()
    );
    for later in [
        filter(Expr::Literal(Scalar::Bool(true))),
        sort(1),
        project(col(1), OutputKind::I64),
        join(JoinKind::Semi),
    ] {
        assert_eq!(
            plan(vec![mean.clone(), Stage::Limit(10), later]).validate(),
            Err(FeatureIrError::TerminalF64MustBeFinal)
        );
    }
}

#[test]
fn source_f64_is_rejected_even_for_limit_only_plan() {
    let schemas = vec![schema(2, &[(1, OutputKind::TerminalF64)])];
    for stage in [
        Stage::Limit(1),
        filter(col(1)),
        project(divide(col(1), integer(2)), OutputKind::TerminalF64),
        sort(1),
    ] {
        assert!(matches!(
            plan(vec![stage]).validate_with_schemas(&schemas),
            Err(FeatureIrError::TerminalF64Input)
        ));
    }
}

#[test]
fn column_types_are_checked_inside_all_operators() {
    let invalid = [
        filter(col(1)),
        project(col(3), OutputKind::I64),
        filter(Expr::Not(Box::new(col(1)))),
        project(
            Expr::Arithmetic {
                op: ArithmeticOp::Add,
                overflow: OverflowPolicy::Error,
                left: Box::new(col(3)),
                right: Box::new(col(1)),
            },
            OutputKind::I64,
        ),
        project(divide(col(3), col(1)), OutputKind::TerminalF64),
        filter(Expr::Compare {
            op: CompareOp::Eq,
            left: Box::new(col(3)),
            right: Box::new(col(1)),
        }),
    ];
    for stage in invalid {
        assert!(matches!(
            plan(vec![stage]).validate_with_schemas(&catalog()),
            Err(FeatureIrError::ExpressionTypeMismatch)
        ));
    }
}

#[test]
fn mixed_signed_unsigned_arithmetic_requires_explicit_future_conversion() {
    let expr = Expr::Arithmetic {
        op: ArithmeticOp::Add,
        overflow: OverflowPolicy::Error,
        left: Box::new(integer(1)),
        right: Box::new(Expr::Literal(Scalar::U64(1))),
    };
    assert_eq!(
        plan(vec![project(expr, OutputKind::I64)]).validate(),
        Err(FeatureIrError::ExpressionTypeMismatch)
    );
}

#[test]
fn missing_columns_are_rejected_in_expressions_aggregates_and_keys() {
    for stage in [
        filter(col(99)),
        project(col(99), OutputKind::I64),
        sort(99),
        group(
            vec![ColumnId(99)],
            aggregate(AggregateOp::Count, None, OutputKind::U64),
        ),
        group(
            vec![],
            aggregate(AggregateOp::Sum, Some(99), OutputKind::I64),
        ),
        group(
            vec![],
            aggregate(AggregateOp::Count, Some(99), OutputKind::U64),
        ),
    ] {
        assert!(matches!(
            plan(vec![stage]).validate_with_schemas(&catalog()),
            Err(FeatureIrError::UnknownColumn)
        ));
    }
}

#[test]
fn projection_drops_source_columns_and_does_not_allow_sibling_alias_reuse() {
    let schemas = catalog();
    assert!(
        plan(vec![project(col(1), OutputKind::I64), sort(9)])
            .validate_with_schemas(&schemas)
            .is_ok()
    );
    assert!(matches!(
        plan(vec![project(col(1), OutputKind::I64), sort(1)]).validate_with_schemas(&schemas),
        Err(FeatureIrError::UnknownColumn)
    ));
    let candidate = plan(vec![Stage::Project(vec![
        Projection {
            output: ColumnId(9),
            output_kind: OutputKind::I64,
            expr: col(1),
        },
        Projection {
            output: ColumnId(10),
            output_kind: OutputKind::I64,
            expr: col(9),
        },
    ])]);
    assert!(matches!(
        candidate.validate_with_schemas(&schemas),
        Err(FeatureIrError::UnknownColumn)
    ));
}

#[test]
fn duplicate_output_and_key_ids_are_rejected() {
    let projection = Projection {
        output: ColumnId(9),
        output_kind: OutputKind::I64,
        expr: integer(1),
    };
    assert_eq!(
        plan(vec![Stage::Project(vec![projection.clone(), projection])]).validate(),
        Err(FeatureIrError::DuplicateColumn)
    );
    let count = aggregate(AggregateOp::Count, None, OutputKind::U64);
    assert_eq!(
        plan(vec![group(vec![ColumnId(9)], count)]).validate(),
        Err(FeatureIrError::DuplicateColumn)
    );
    assert_eq!(
        plan(vec![group(vec![ColumnId(1), ColumnId(1)], count)]).validate(),
        Err(FeatureIrError::DuplicateColumn)
    );
    assert_eq!(
        plan(vec![Stage::GroupBy {
            keys: vec![],
            aggregates: vec![count, count],
            null_keys: NullKeyPolicy::Include
        }])
        .validate(),
        Err(FeatureIrError::DuplicateColumn)
    );
}

#[test]
fn only_count_star_can_omit_input() {
    for (op, kind) in [
        (AggregateOp::Sum, OutputKind::I64),
        (AggregateOp::Min, OutputKind::I64),
        (AggregateOp::Max, OutputKind::I64),
        (AggregateOp::Mean, OutputKind::TerminalF64),
    ] {
        assert_eq!(
            plan(vec![group(vec![], aggregate(op, None, kind))]).validate(),
            Err(FeatureIrError::AggregateInputRequired)
        );
    }
    assert!(
        plan(vec![group(
            vec![],
            aggregate(AggregateOp::Count, None, OutputKind::U64)
        )])
        .validate_with_schemas(&catalog())
        .is_ok()
    );
}

#[test]
fn aggregate_input_and_output_kinds_must_match_contract() {
    for spec in [
        aggregate(AggregateOp::Count, None, OutputKind::I64),
        aggregate(AggregateOp::Sum, Some(3), OutputKind::I64),
        aggregate(AggregateOp::Sum, Some(1), OutputKind::U64),
        aggregate(AggregateOp::Min, Some(1), OutputKind::Bool),
        aggregate(AggregateOp::Mean, Some(3), OutputKind::TerminalF64),
    ] {
        assert!(matches!(
            plan(vec![group(vec![], spec)]).validate_with_schemas(&catalog()),
            Err(FeatureIrError::ExpressionTypeMismatch)
        ));
    }
}

#[test]
fn group_output_contains_only_keys_and_aggregate_results() {
    let sum = group(
        vec![ColumnId(1)],
        aggregate(AggregateOp::Sum, Some(2), OutputKind::I64),
    );
    assert!(
        plan(vec![sum.clone(), sort(9), sort(1)])
            .validate_with_schemas(&catalog())
            .is_ok()
    );
    assert!(matches!(
        plan(vec![sum, sort(2)]).validate_with_schemas(&catalog()),
        Err(FeatureIrError::UnknownColumn)
    ));
}

#[test]
fn inner_and_left_join_output_include_right_columns() {
    for kind in [JoinKind::Inner, JoinKind::Left] {
        assert!(
            plan(vec![join(kind), project(col(5), OutputKind::Bytes)])
                .validate_with_schemas(&catalog())
                .is_ok()
        );
    }
}

#[test]
fn semi_and_anti_join_output_exclude_right_columns() {
    for kind in [JoinKind::Semi, JoinKind::Anti] {
        assert!(
            plan(vec![join(kind), sort(1)])
                .validate_with_schemas(&catalog())
                .is_ok()
        );
        assert!(matches!(
            plan(vec![join(kind), sort(5)]).validate_with_schemas(&catalog()),
            Err(FeatureIrError::UnknownColumn)
        ));
    }
}

#[test]
fn joins_require_existing_matching_keys_and_unambiguous_output_ids() {
    let mut schemas = catalog();
    schemas[1].columns[0].kind = OutputKind::Bool;
    assert!(matches!(
        plan(vec![join(JoinKind::Inner)]).validate_with_schemas(&schemas),
        Err(FeatureIrError::ExpressionTypeMismatch)
    ));
    schemas = catalog();
    schemas[1].columns[1].column = ColumnId(3);
    assert!(matches!(
        plan(vec![join(JoinKind::Inner)]).validate_with_schemas(&schemas),
        Err(FeatureIrError::DuplicateColumn)
    ));
    for (left_key, right_key) in [(ColumnId(99), ColumnId(4)), (ColumnId(1), ColumnId(99))] {
        let candidate = plan(vec![Stage::Join(JoinSpec {
            right: dataset(3),
            kind: JoinKind::Semi,
            left_key,
            right_key,
            null_equality: NullEquality::Unequal,
        })]);
        assert!(matches!(
            candidate.validate_with_schemas(&catalog()),
            Err(FeatureIrError::UnknownColumn)
        ));
    }
}

#[test]
fn catalog_resolution_checks_identity_version_and_duplicates() {
    let candidate = plan(vec![Stage::Limit(1)]);
    assert!(matches!(
        candidate.validate_with_schemas(&[]),
        Err(FeatureIrError::UnknownDataset)
    ));
    let mut schemas = catalog();
    schemas[0].dataset.schema_version = 2;
    assert!(matches!(
        candidate.validate_with_schemas(&schemas),
        Err(FeatureIrError::UnknownDataset)
    ));
    schemas = catalog();
    schemas.push(schemas[0].clone());
    assert!(matches!(
        candidate.validate_with_schemas(&schemas),
        Err(FeatureIrError::InvalidSchema)
    ));
    schemas = catalog();
    let duplicate = schemas[0].columns[0];
    schemas[0].columns.push(duplicate);
    assert!(matches!(
        candidate.validate_with_schemas(&schemas),
        Err(FeatureIrError::DuplicateColumn)
    ));
}

#[test]
fn excessively_nested_expression_is_rejected_without_unbounded_walk() {
    let mut expr = Expr::Literal(Scalar::Bool(true));
    for _ in 0..66 {
        expr = Expr::Not(Box::new(expr));
    }
    assert_eq!(
        plan(vec![filter(expr)]).validate(),
        Err(FeatureIrError::PlanTooComplex)
    );
}

#[test]
fn fast64_rejects_wrong_asset_version_or_hash_at_export() {
    let asset = AssetId::from_bytes([1; 32]);
    let version = RegistryVersion::new(2).unwrap();
    let hash = Hash32::from_bytes([3; 32]);
    let profile = Fast64MoneyProfile::checked(
        MoneyProfileKey {
            asset_id: asset,
            registry_version: version,
        },
        hash,
        100,
    )
    .unwrap();
    for (a, v, h) in [
        (AssetId::from_bytes([9; 32]), version, hash),
        (asset, RegistryVersion::new(3).unwrap(), hash),
        (asset, version, Hash32::from_bytes([9; 32])),
    ] {
        let amount = AssetAmount::checked(a, 1, 1, v, h).unwrap();
        assert_eq!(
            profile.export_amount(amount),
            Err(FeatureIrError::Fast64IdentityMismatch)
        );
    }
    let make_amount = |atoms| AssetAmount::checked(asset, atoms, u128::MAX, version, hash).unwrap();
    assert_eq!(profile.export_amount(make_amount(100)), Ok(100));
    assert_eq!(
        profile.export_amount(make_amount(101)),
        Err(FeatureIrError::Fast64AmountOutOfRange)
    );
    assert_eq!(
        profile.export_amount(make_amount(u128::MAX)),
        Err(FeatureIrError::Fast64AmountOutOfRange)
    );
    let maximum = Fast64MoneyProfile::checked(profile.key(), hash, i64::MAX as u128).unwrap();
    assert_eq!(
        maximum.export_amount(make_amount(i64::MAX as u128)),
        Ok(i64::MAX)
    );
    assert_eq!(
        maximum.export_amount(make_amount(i64::MAX as u128 + 1)),
        Err(FeatureIrError::Fast64AmountOutOfRange)
    );
}
