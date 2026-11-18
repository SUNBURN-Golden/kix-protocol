//! Source-informed class B characterizations: FEATURE_SEMANTICS_V1 does not
//! define empty-stage restrictions or their exact error variants. Their normative
//! status remains UNDETERMINED (owner: User). No error precedence or backend
//! execution behavior is asserted here.
use kix_feature_ir::*;
use kix_feature_semantics::*;
use kix_types::KixId;

fn dataset() -> DatasetRef {
    DatasetRef {
        dataset_id: KixId::from_bytes([2; 16]),
        schema_version: 1,
    }
}

fn catalog() -> Vec<DatasetSchema> {
    vec![DatasetSchema {
        dataset: dataset(),
        columns: vec![ColumnSchema {
            column: ColumnId(1),
            kind: OutputKind::I64,
        }],
    }]
}

fn plan(stage: Stage) -> FeaturePlanV1 {
    FeaturePlanV1 {
        plan_id: KixId::from_bytes([1; 16]),
        source: dataset(),
        stages: vec![stage],
    }
}

fn assert_both_unchanged(
    plan: &FeaturePlanV1,
    catalog: &[DatasetSchema],
    expected: Result<(), FeatureIrError>,
) {
    let original_plan = plan.clone();
    let original_catalog = catalog.to_vec();

    assert_eq!(plan.validate(), expected);
    assert_eq!(plan, &original_plan);
    assert_eq!(catalog, original_catalog.as_slice());

    assert_eq!(plan.validate_with_schemas(catalog).map(|_| ()), expected);
    assert_eq!(plan, &original_plan);
    assert_eq!(catalog, original_catalog.as_slice());
}

#[test]
fn characterize_empty_projection_rejection() {
    let catalog = catalog();
    assert_both_unchanged(
        &plan(Stage::Project(vec![])),
        &catalog,
        Err(FeatureIrError::EmptyProjection),
    );
    assert_both_unchanged(
        &plan(Stage::Project(vec![Projection {
            output: ColumnId(9),
            output_kind: OutputKind::I64,
            expr: Expr::Column(ColumnId(1)),
        }])),
        &catalog,
        Ok(()),
    );
}

#[test]
fn characterize_empty_group_by_rejection() {
    let catalog = catalog();
    assert_both_unchanged(
        &plan(Stage::GroupBy {
            keys: vec![],
            aggregates: vec![],
            null_keys: NullKeyPolicy::Include,
        }),
        &catalog,
        Err(FeatureIrError::EmptyGroupKeysAndAggregates),
    );
    assert_both_unchanged(
        &plan(Stage::GroupBy {
            keys: vec![ColumnId(1)],
            aggregates: vec![],
            null_keys: NullKeyPolicy::Include,
        }),
        &catalog,
        Ok(()),
    );
    assert_both_unchanged(
        &plan(Stage::GroupBy {
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
        }),
        &catalog,
        Ok(()),
    );
}

#[test]
fn characterize_empty_sort_rejection() {
    let catalog = catalog();
    let sort = |by| {
        plan(Stage::Sort {
            by,
            descending: false,
            null_order: NullOrder::Last,
            stability: SortStability::Stable,
        })
    };
    assert_both_unchanged(&sort(vec![]), &catalog, Err(FeatureIrError::InvalidStage));
    assert_both_unchanged(&sort(vec![ColumnId(1)]), &catalog, Ok(()));
}
