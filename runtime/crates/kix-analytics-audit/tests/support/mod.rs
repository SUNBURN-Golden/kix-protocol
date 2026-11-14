pub mod compare;
pub mod data;
pub mod duck;
pub mod polar;
pub mod reference;

use data::*;
use kix_feature_ir::*;
use kix_feature_semantics::*;

pub fn plan(source: DatasetRef, stages: Vec<Stage>) -> FeaturePlanV1 {
    FeaturePlanV1 {
        plan_id: id(250),
        source,
        stages,
    }
}
pub fn project(items: Vec<(u16, OutputKind, Expr)>) -> Stage {
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
pub fn aggregate(
    output: u16,
    input: Option<u16>,
    op: AggregateOp,
    kind: OutputKind,
) -> AggregateSpec {
    AggregateSpec {
        output: ColumnId(output),
        output_kind: kind,
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
pub fn col(id: u16) -> Expr {
    Expr::Column(ColumnId(id))
}
pub fn run(
    case: &str,
    clause: &str,
    data: &Data,
    plan: &FeaturePlanV1,
    expected: Result<Vec<Vec<V>>, String>,
    ordered: bool,
) {
    let catalog = data.catalog();
    let validated = plan
        .validate_with_schemas(&catalog)
        .expect("catalog-bound plan");
    let rust = reference::execute(data, &validated);
    let polars = polar::execute(data, &validated);
    let (sql, duckdb) = duck::execute(data, &validated);
    let outcomes = [("rust", &rust), ("polars", &polars), ("duckdb", &duckdb)];
    let passed = outcomes
        .iter()
        .all(|(_, actual)| compare::equivalent(&expected, actual, ordered));
    if let Ok(directory) = std::env::var("KIX_AUDIT_RESULTS") {
        std::fs::create_dir_all(&directory).unwrap();
        let suffix = std::env::var("KIX_AUDIT_SOURCE").unwrap_or("synthetic".into());
        let record = serde_json::json!({
            "schemaVersion": 1, "caseId": case, "contractClause": clause,
            "fixtureKind": data.fixture_kind, "planId": format!("{:?}", plan.plan_id),
            "plan": format!("{plan:?}"), "querySql": sql,
            "exportTrace": data.trace, "datasets": if data.fixture_kind == "synthetic-boundary-characterization" { format!("{:?}", data.tables) } else { "authenticated files identified by exportTrace".into() }, "expected": format!("{expected:?}"),
            "rust": format!("{rust:?}"), "polars": format!("{polars:?}"),
            "duckdb": format!("{duckdb:?}"), "comparison": if ordered {"ordered"} else {"duplicate-preserving multiset"},
            "normalizedOutcomes": {
                "rust": rust.as_ref().map(|_| "ROWS").unwrap_or_else(|e| compare::error_category(e)),
                "polars": polars.as_ref().map(|_| "ROWS").unwrap_or_else(|e| compare::error_category(e)),
                "duckdb": duckdb.as_ref().map(|_| "ROWS").unwrap_or_else(|e| compare::error_category(e))
            },
            "status": if passed { "PASS" } else { "FAIL" }, "limitations": "local fixture; source-informed; no economic writes or production claim"
        });
        std::fs::write(
            format!("{directory}/{suffix}-{case}.json"),
            serde_json::to_vec_pretty(&record).unwrap(),
        )
        .unwrap();
    }
    // Preserve raw mismatches in the artifact before failing the acceptance run.
    for (engine, actual) in outcomes {
        assert!(
            compare::equivalent(&expected, actual, ordered),
            "{case} {engine}: expected {expected:?}, got {actual:?}; SQL={sql}"
        );
    }
}
