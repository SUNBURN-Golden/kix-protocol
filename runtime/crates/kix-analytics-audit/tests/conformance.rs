mod support;
use kix_feature_ir::*;
use kix_feature_semantics::*;
use support::{aggregate, col, data::*, plan, project, run};

fn left() -> Table {
    Table {
        schema: schema(
            100,
            &[
                (1, OutputKind::I64),
                (2, OutputKind::I64),
                (3, OutputKind::U64),
            ],
        ),
        rows: vec![
            vec![V::Null, V::I(10), V::U(0)],
            vec![V::I(1), V::Null, V::U(1)],
            vec![V::I(1), V::I(20), V::U(2)],
            vec![V::I(2), V::I(30), V::U(3)],
            vec![V::I(3), V::I(40), V::U(4)],
        ],
    }
}
fn right() -> Table {
    Table {
        schema: schema(101, &[(4, OutputKind::I64), (5, OutputKind::I64)]),
        rows: vec![
            vec![V::Null, V::I(90)],
            vec![V::I(1), V::I(100)],
            vec![V::I(1), V::I(200)],
            vec![V::I(9), V::I(900)],
        ],
    }
}
#[test]
fn null_semantics() {
    let data = Data::synthetic(vec![left()]);
    run(
        "null-filter",
        "Feature Semantics §2",
        &data,
        &plan(
            dataset(100),
            vec![Stage::Filter {
                predicate: Expr::Compare {
                    op: CompareOp::Gt,
                    left: Box::new(col(2)),
                    right: Box::new(Expr::Literal(Scalar::I64(15))),
                },
                null_predicate: NullPredicatePolicy::Drop,
            }],
        ),
        Ok(left().rows[2..].to_vec()),
        false,
    );
    for policy in [NullKeyPolicy::Include, NullKeyPolicy::Exclude] {
        let aggregates = vec![
            aggregate(10, None, AggregateOp::Count, OutputKind::U64),
            aggregate(11, Some(2), AggregateOp::Count, OutputKind::U64),
            aggregate(12, Some(2), AggregateOp::Sum, OutputKind::I64),
            aggregate(13, Some(2), AggregateOp::Min, OutputKind::I64),
            aggregate(14, Some(2), AggregateOp::Max, OutputKind::I64),
            aggregate(15, Some(2), AggregateOp::Mean, OutputKind::TerminalF64),
        ];
        let row = |key, value, star| {
            vec![
                key,
                V::U(star),
                V::U(1),
                V::I(value),
                V::I(value),
                V::I(value),
                V::F(value.to_string()),
            ]
        };
        let mut expected = vec![
            row(V::I(1), 20, 2),
            row(V::I(2), 30, 1),
            row(V::I(3), 40, 1),
        ];
        if policy == NullKeyPolicy::Include {
            expected.push(row(V::Null, 10, 1));
        }
        run(
            &format!("group-{policy:?}"),
            "Feature Semantics §§2,4",
            &data,
            &plan(
                dataset(100),
                vec![Stage::GroupBy {
                    keys: vec![ColumnId(1)],
                    aggregates,
                    null_keys: policy,
                }],
            ),
            Ok(expected),
            false,
        );
    }
    for (label, rows, star) in [
        ("empty", vec![], 0),
        ("all-null", vec![vec![V::Null], vec![V::Null]], 2),
        (
            "nonempty",
            vec![vec![V::I(2)], vec![V::I(3)], vec![V::Null]],
            3,
        ),
    ] {
        let data = Data::synthetic(vec![Table {
            schema: schema(100, &[(1, OutputKind::I64)]),
            rows,
        }]);
        let aggregates = vec![
            aggregate(10, None, AggregateOp::Count, OutputKind::U64),
            aggregate(11, Some(1), AggregateOp::Count, OutputKind::U64),
            aggregate(12, Some(1), AggregateOp::Sum, OutputKind::I64),
            aggregate(13, Some(1), AggregateOp::Min, OutputKind::I64),
            aggregate(14, Some(1), AggregateOp::Max, OutputKind::I64),
            aggregate(15, Some(1), AggregateOp::Mean, OutputKind::TerminalF64),
        ];
        let expected = if label == "nonempty" {
            vec![
                V::U(3),
                V::U(2),
                V::I(5),
                V::I(2),
                V::I(3),
                V::F("2.5".into()),
            ]
        } else {
            vec![V::U(star), V::U(0), V::Null, V::Null, V::Null, V::Null]
        };
        run(
            &format!("aggregate-{label}"),
            "Feature Semantics §4",
            &data,
            &plan(
                dataset(100),
                vec![Stage::GroupBy {
                    keys: vec![],
                    aggregates,
                    null_keys: NullKeyPolicy::Include,
                }],
            ),
            Ok(vec![expected]),
            false,
        );
    }
}
#[test]
fn ordering_semantics() {
    let data = Data::synthetic(vec![left()]);
    for descending in [false, true] {
        for null_order in [NullOrder::First, NullOrder::Last] {
            let mut indices = if descending {
                vec![4, 3, 1, 2]
            } else {
                vec![1, 2, 3, 4]
            };
            if null_order == NullOrder::First {
                indices.insert(0, 0);
            } else {
                indices.push(0);
            }
            let expected = indices.iter().map(|i| left().rows[*i].clone()).collect();
            run(
                &format!("sort-{descending}-{null_order:?}"),
                "Feature Semantics §3",
                &data,
                &plan(
                    dataset(100),
                    vec![Stage::Sort {
                        by: vec![ColumnId(1)],
                        descending,
                        null_order,
                        stability: SortStability::Stable,
                    }],
                ),
                Ok(expected),
                true,
            );
        }
    }
}
#[test]
fn join_semantics() {
    let data = Data::synthetic(vec![left(), right()]);
    for policy in [NullEquality::Equal, NullEquality::Unequal] {
        for kind in [
            JoinKind::Inner,
            JoinKind::Left,
            JoinKind::Semi,
            JoinKind::Anti,
        ] {
            let l = left().rows;
            let mut expected = vec![];
            match kind {
                JoinKind::Inner | JoinKind::Left => {
                    for i in [1, 2] {
                        for value in [100, 200] {
                            let mut row = l[i].clone();
                            row.extend([V::I(1), V::I(value)]);
                            expected.push(row);
                        }
                    }
                    if policy == NullEquality::Equal {
                        let mut row = l[0].clone();
                        row.extend([V::Null, V::I(90)]);
                        expected.push(row);
                    } else if kind == JoinKind::Left {
                        let mut row = l[0].clone();
                        row.extend([V::Null, V::Null]);
                        expected.push(row);
                    }
                    if kind == JoinKind::Left {
                        for i in [3, 4] {
                            let mut row = l[i].clone();
                            row.extend([V::Null, V::Null]);
                            expected.push(row);
                        }
                    }
                }
                JoinKind::Semi => {
                    expected.extend([l[1].clone(), l[2].clone()]);
                    if policy == NullEquality::Equal {
                        expected.push(l[0].clone());
                    }
                }
                JoinKind::Anti => {
                    expected.extend([l[3].clone(), l[4].clone()]);
                    if policy == NullEquality::Unequal {
                        expected.push(l[0].clone());
                    }
                }
            }
            run(
                &format!("join-{kind:?}-{policy:?}"),
                "Feature Semantics §§2,10",
                &data,
                &plan(
                    dataset(100),
                    vec![Stage::Join(JoinSpec {
                        right: dataset(101),
                        kind,
                        left_key: ColumnId(1),
                        right_key: ColumnId(4),
                        null_equality: policy,
                    })],
                ),
                Ok(expected),
                false,
            );
        }
    }
}
#[test]
fn overflow_semantics() {
    use ArithmeticOp::*;
    for (kind, value) in [(OutputKind::I64, V::I(7)), (OutputKind::U64, V::U(7))] {
        for op in [Add, Sub, Mul] {
            let data = Data::synthetic(vec![Table {
                schema: schema(100, &[(1, kind), (2, kind)]),
                rows: vec![
                    vec![V::Null, value.clone()],
                    vec![value.clone(), V::Null],
                    vec![V::Null, V::Null],
                ],
            }]);
            run(
                &format!("nullable-{kind:?}-{op:?}"),
                "Class B: nullable arithmetic characterization; v1 has no explicit propagation rule",
                &data,
                &plan(
                    dataset(100),
                    vec![project(vec![(
                        10,
                        kind,
                        Expr::Arithmetic {
                            op,
                            overflow: OverflowPolicy::Error,
                            left: Box::new(col(1)),
                            right: Box::new(col(2)),
                        },
                    )])],
                ),
                Ok(vec![vec![V::Null]; 3]),
                false,
            );
        }
    }
    // A later stage must not hide an earlier checked-arithmetic failure.
    let data = Data::synthetic(vec![Table {
        schema: schema(100, &[(1, OutputKind::I64)]),
        rows: vec![vec![V::I(i64::MAX)]],
    }]);
    run(
        "overflow-before-limit",
        "Feature Semantics §4",
        &data,
        &plan(
            dataset(100),
            vec![
                project(vec![(
                    10,
                    OutputKind::I64,
                    Expr::Arithmetic {
                        op: Add,
                        overflow: OverflowPolicy::Error,
                        left: Box::new(col(1)),
                        right: Box::new(Expr::Literal(Scalar::I64(1))),
                    },
                )]),
                Stage::Limit(0),
            ],
        ),
        Err("overflow".into()),
        false,
    );
    let signed = [
        (Add, i64::MAX, 1, None),
        (Add, i64::MIN, -1, None),
        (Sub, i64::MIN, 1, None),
        (Sub, i64::MAX, -1, None),
        (Mul, i64::MIN, -1, None),
        (Mul, i64::MAX, 2, None),
        (Add, i64::MAX, 0, Some(i64::MAX)),
        (Sub, i64::MIN, 0, Some(i64::MIN)),
        (Mul, -3, 7, Some(-21)),
        (Mul, i64::MIN, 1, Some(i64::MIN)),
        (Mul, i64::MAX, 1, Some(i64::MAX)),
    ];
    for (i, (op, l, r, answer)) in signed.into_iter().enumerate() {
        let data = Data::synthetic(vec![Table {
            schema: schema(100, &[(1, OutputKind::I64), (2, OutputKind::I64)]),
            rows: vec![vec![V::I(l), V::I(r)]],
        }]);
        let expected = answer.map(|n| vec![vec![V::I(n)]]).ok_or("overflow".into());
        run(
            &format!("i64-{i}-{op:?}"),
            "Feature Semantics §4",
            &data,
            &plan(
                dataset(100),
                vec![project(vec![(
                    10,
                    OutputKind::I64,
                    Expr::Arithmetic {
                        op,
                        overflow: OverflowPolicy::Error,
                        left: Box::new(col(1)),
                        right: Box::new(col(2)),
                    },
                )])],
            ),
            expected,
            false,
        );
    }
    let unsigned = [
        (Add, u64::MAX, 1, None),
        (Sub, 0, 1, None),
        (Mul, u64::MAX, 2, None),
        (Mul, u64::MAX, u64::MAX, None),
        (Add, u64::MAX, 0, Some(u64::MAX)),
        (Sub, u64::MAX, u64::MAX, Some(0)),
        (Mul, u64::MAX, 0, Some(0)),
        (Mul, 3, 7, Some(21)),
        (Mul, u64::MAX, 1, Some(u64::MAX)),
        (Mul, u64::MAX / 3, 3, Some(u64::MAX)),
        (Mul, u64::MAX / 3 + 1, 3, None),
    ];
    for (i, (op, l, r, answer)) in unsigned.into_iter().enumerate() {
        let data = Data::synthetic(vec![Table {
            schema: schema(100, &[(1, OutputKind::U64), (2, OutputKind::U64)]),
            rows: vec![vec![V::U(l), V::U(r)]],
        }]);
        run(
            &format!("u64-{i}-{op:?}"),
            "Feature Semantics §4",
            &data,
            &plan(
                dataset(100),
                vec![project(vec![(
                    10,
                    OutputKind::U64,
                    Expr::Arithmetic {
                        op,
                        overflow: OverflowPolicy::Error,
                        left: Box::new(col(1)),
                        right: Box::new(col(2)),
                    },
                )])],
            ),
            answer.map(|n| vec![vec![V::U(n)]]).ok_or("overflow".into()),
            false,
        );
    }
    for (label, kind, values, expected) in [
        (
            "i64-positive",
            OutputKind::I64,
            vec![V::I(i64::MAX), V::I(1)],
            Err("overflow".into()),
        ),
        (
            "i64-negative",
            OutputKind::I64,
            vec![V::I(i64::MIN), V::I(-1)],
            Err("overflow".into()),
        ),
        (
            "u64-positive",
            OutputKind::U64,
            vec![V::U(u64::MAX), V::U(1)],
            Err("overflow".into()),
        ),
        (
            "i64-boundary",
            OutputKind::I64,
            vec![V::I(i64::MAX), V::I(0), V::Null],
            Ok(vec![vec![V::I(i64::MAX)]]),
        ),
        (
            "u64-boundary",
            OutputKind::U64,
            vec![V::U(u64::MAX), V::U(0), V::Null],
            Ok(vec![vec![V::U(u64::MAX)]]),
        ),
    ] {
        let data = Data::synthetic(vec![Table {
            schema: schema(100, &[(1, kind)]),
            rows: values.into_iter().map(|v| vec![v]).collect(),
        }]);
        run(
            &format!("sum-{label}"),
            "Feature Semantics §4",
            &data,
            &plan(
                dataset(100),
                vec![Stage::GroupBy {
                    keys: vec![],
                    aggregates: vec![aggregate(10, Some(1), AggregateOp::Sum, kind)],
                    null_keys: NullKeyPolicy::Include,
                }],
            ),
            expected,
            false,
        );
    }
}
#[test]
fn export_binding() {
    let data = exported();
    // Every table and column is consumed with its explicit mapped type.
    for (i, table) in data.tables.iter().enumerate() {
        run(
            &format!("export-table-{i}"),
            "Authenticated Export §§4,5",
            data,
            &plan(table.schema.dataset, vec![Stage::Limit(1_000_000)]),
            Ok(table.rows.clone()),
            true,
        );
    }
    let command = data.column("command_result", "command_id");
    let order_command = data.column("minimal_order", "command_id");
    let crc = data.column("minimal_order", "crc");
    let source = data
        .tables
        .iter()
        .find(|t| t.schema.columns.iter().any(|c| c.column == command))
        .unwrap();
    let right = data
        .tables
        .iter()
        .find(|t| t.schema.columns.iter().any(|c| c.column == order_command))
        .unwrap();
    let expected = source
        .rows
        .iter()
        .filter_map(|row| {
            let key = &row[index(&source.schema.columns, command)];
            if right
                .rows
                .iter()
                .any(|r| &r[index(&right.schema.columns, order_command)] == key)
            {
                None
            } else {
                Some(vec![key.clone(), V::Null])
            }
        })
        .collect::<Vec<_>>();
    let joined = plan(
        source.schema.dataset,
        vec![
            Stage::Join(JoinSpec {
                right: right.schema.dataset,
                kind: JoinKind::Left,
                left_key: command,
                right_key: order_command,
                null_equality: NullEquality::Unequal,
            }),
            Stage::Filter {
                predicate: Expr::Compare {
                    op: CompareOp::Eq,
                    left: Box::new(Expr::Column(crc)),
                    right: Box::new(Expr::Column(crc)),
                },
                null_predicate: NullPredicatePolicy::Drop,
            },
            project(vec![
                (2000, OutputKind::Bytes, Expr::Column(command)),
                (2001, OutputKind::U64, Expr::Column(crc)),
            ]),
        ],
    );
    let matched = source
        .rows
        .iter()
        .flat_map(|row| {
            let key = &row[index(&source.schema.columns, command)];
            right
                .rows
                .iter()
                .filter(move |r| &r[index(&right.schema.columns, order_command)] == key)
                .map(move |r| vec![key.clone(), r[index(&right.schema.columns, crc)].clone()])
        })
        .collect();
    run(
        "export-left-join-null-filter",
        "Feature Semantics §§2,10",
        data,
        &joined,
        Ok(matched),
        false,
    );
    assert!(
        !expected.is_empty(),
        "fixture must exercise unmatched exported rows"
    );
    let nullable = plan(
        source.schema.dataset,
        vec![
            Stage::Join(JoinSpec {
                right: right.schema.dataset,
                kind: JoinKind::Left,
                left_key: command,
                right_key: order_command,
                null_equality: NullEquality::Unequal,
            }),
            project(vec![
                (2000, OutputKind::Bytes, Expr::Column(command)),
                (2001, OutputKind::U64, Expr::Column(crc)),
            ]),
        ],
    );
    let mut all = expected;
    for row in &source.rows {
        for r in &right.rows {
            if row[index(&source.schema.columns, command)]
                == r[index(&right.schema.columns, order_command)]
            {
                all.push(vec![
                    row[index(&source.schema.columns, command)].clone(),
                    r[index(&right.schema.columns, crc)].clone(),
                ]);
            }
        }
    }
    run(
        "export-left-join-null-values",
        "Feature Semantics §2",
        data,
        &nullable,
        Ok(all.clone()),
        false,
    );
    for null_order in [NullOrder::First, NullOrder::Last] {
        let mut sorted_plan = nullable.clone();
        sorted_plan.stages.push(Stage::Sort {
            by: vec![ColumnId(2001)],
            descending: false,
            null_order,
            stability: SortStability::Stable,
        });
        let mut expected = all.clone();
        expected.sort_by(|a, b| match (a[1].is_null(), b[1].is_null()) {
            (true, false) => {
                if null_order == NullOrder::First {
                    std::cmp::Ordering::Less
                } else {
                    std::cmp::Ordering::Greater
                }
            }
            (false, true) => {
                if null_order == NullOrder::First {
                    std::cmp::Ordering::Greater
                } else {
                    std::cmp::Ordering::Less
                }
            }
            _ => a[1].cmp(&b[1]),
        });
        run(
            &format!("export-null-sort-{null_order:?}"),
            "Feature Semantics §§2,3",
            data,
            &sorted_plan,
            Ok(expected),
            true,
        );
    }
}
#[test]
fn money_roundtrip_and_version_rejection() {
    let data = exported();
    let amount = data.column("command_result", "amount_u128");
    let table = data
        .tables
        .iter()
        .find(|t| t.schema.columns.iter().any(|c| c.column == amount))
        .unwrap();
    let values = table
        .rows
        .iter()
        .map(|r| r[index(&table.schema.columns, amount)].clone())
        .collect::<Vec<_>>();
    for required in [
        0,
        2u128.pow(53),
        2u128.pow(53) + 1,
        i64::MAX as u128,
        i64::MAX as u128 + 1,
        u64::MAX as u128,
        u64::MAX as u128 + 1,
        u128::MAX,
    ] {
        assert!(
            values.contains(&V::bytes(&required.to_string())),
            "missing money boundary {required}"
        );
    }
    run(
        "money-lossless",
        "Feature Semantics §6; Authenticated Export §5",
        data,
        &plan(
            table.schema.dataset,
            vec![project(vec![(
                2000,
                OutputKind::Bytes,
                Expr::Column(amount),
            )])],
        ),
        Ok(values.into_iter().map(|v| vec![v]).collect()),
        true,
    );
    // Explicit UTF8/VARCHAR representation in addition to the lossless IR Bytes lane.
    let texts = table
        .rows
        .iter()
        .map(|r| {
            let V::B(bytes) = &r[index(&table.schema.columns, amount)] else {
                panic!("money bytes")
            };
            String::from_utf8(bytes.clone()).unwrap()
        })
        .collect::<Vec<_>>();
    let polars_text = {
        use polars::prelude::*;
        let df = DataFrame::new_infer_height(vec![
            Series::new("amount".into(), texts.clone()).into_column(),
        ])
        .unwrap();
        let out = df
            .lazy()
            .select([polars::prelude::col("amount")])
            .collect()
            .unwrap();
        let actual = out
            .column("amount")
            .unwrap()
            .str()
            .unwrap()
            .iter()
            .map(|s| s.unwrap().to_owned())
            .collect::<Vec<_>>();
        assert_eq!(actual, texts);
        actual
    };
    let connection = duckdb::Connection::open_in_memory().unwrap();
    connection.execute_batch("SET autoinstall_known_extensions=false; SET autoload_known_extensions=false; CREATE TABLE money_text (ord BIGINT, amount VARCHAR);").unwrap();
    for (i, text) in texts.iter().enumerate() {
        connection
            .execute(
                "INSERT INTO money_text VALUES (?, ?)",
                duckdb::params![i as i64, text],
            )
            .unwrap();
    }
    let actual = connection
        .prepare("SELECT amount FROM money_text ORDER BY ord")
        .unwrap()
        .query_map([], |r| r.get::<_, String>(0))
        .unwrap()
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    assert_eq!(actual, texts);
    let rust_text = actual
        .iter()
        .map(|text| money(text).unwrap().to_string())
        .collect::<Vec<_>>();
    assert_eq!(rust_text, texts);
    if let Ok(directory) = std::env::var("KIX_AUDIT_RESULTS") {
        std::fs::create_dir_all(&directory).unwrap();
        let source = std::env::var("KIX_AUDIT_SOURCE").unwrap_or("synthetic".into());
        std::fs::write(format!("{directory}/{source}-money-text.json"), serde_json::to_vec_pretty(&serde_json::json!({
            "schemaVersion": 1, "caseId": "money-text", "contractClause": "Feature Semantics §6; Authenticated Export §5",
            "fixtureKind": data.fixture_kind, "planId": "lossless-text-boundary-outside-arithmetic-IR",
            "querySql": "SELECT amount FROM money_text ORDER BY ord", "exportTrace": data.trace,
            "expected": texts, "rust": rust_text, "polars": polars_text, "duckdb": actual,
            "comparison": "exact ordered canonical decimal text", "status": "PASS",
            "limitations": "No money arithmetic, Fast64 permission or production authentication"
        })).unwrap()).unwrap();
    }
    for bad in [
        "01",
        "-1",
        "1.5",
        "1e3",
        "340282366920938463463374607431768211456",
    ] {
        assert!(money(bad).is_err());
    }
    let catalog = data.catalog();
    for op in [ArithmeticOp::Add, ArithmeticOp::Sub, ArithmeticOp::Mul] {
        let p = plan(
            table.schema.dataset,
            vec![project(vec![(
                2000,
                OutputKind::I64,
                Expr::Arithmetic {
                    op,
                    overflow: OverflowPolicy::Error,
                    left: Box::new(Expr::Column(amount)),
                    right: Box::new(Expr::Column(amount)),
                },
            )])],
        );
        assert!(
            p.validate_with_schemas(&catalog).is_err(),
            "Wide128 arithmetic must fail before either engine"
        );
    }
    for op in [AggregateOp::Sum, AggregateOp::Mean] {
        let p = plan(
            table.schema.dataset,
            vec![Stage::GroupBy {
                keys: vec![],
                aggregates: vec![aggregate(
                    2000,
                    Some(amount.0),
                    op,
                    if op == AggregateOp::Mean {
                        OutputKind::TerminalF64
                    } else {
                        OutputKind::I64
                    },
                )],
                null_keys: NullKeyPolicy::Include,
            }],
        );
        assert!(p.validate_with_schemas(&catalog).is_err());
    }
    let mut wrong = table.schema.dataset;
    wrong.schema_version += 1;
    assert!(
        plan(wrong, vec![Stage::Limit(1)])
            .validate_with_schemas(&catalog)
            .is_err()
    );
    // Declared integer/float narrowing of the Wide128 byte representation is rejected.
    for kind in [OutputKind::I64, OutputKind::U64, OutputKind::TerminalF64] {
        assert!(
            plan(
                table.schema.dataset,
                vec![project(vec![(2000, kind, Expr::Column(amount))])]
            )
            .validate_with_schemas(&catalog)
            .is_err()
        );
    }
}
#[test]
fn comparator_sensitivity() {
    use support::compare::equivalent;
    assert!(!equivalent(
        &Err("overflow".into()),
        &Err("unsupported operation".into()),
        false
    ));
    let rows = Ok(vec![
        vec![V::Null, V::I(1)],
        vec![V::I(2), V::I(3)],
        vec![V::I(2), V::I(3)],
    ]);
    assert!(!equivalent(
        &rows,
        &Ok(vec![vec![V::Null, V::I(1)], vec![V::I(2), V::I(3)]]),
        false
    ));
    assert!(!equivalent(
        &rows,
        &Ok(vec![
            vec![V::Null, V::I(9)],
            vec![V::I(2), V::I(3)],
            vec![V::I(2), V::I(3)]
        ]),
        false
    ));
    let reversed = Ok(rows.as_ref().unwrap().iter().rev().cloned().collect());
    assert!(!equivalent(&rows, &reversed, true));
    assert!(equivalent(&rows, &reversed, false));
    assert!(!equivalent(
        &Err("overflow".into()),
        &Ok(vec![vec![V::I(i64::MIN)]]),
        false
    ));
    assert!(!equivalent(
        &Err("overflow".into()),
        &Ok(vec![vec![V::U(u64::MAX)]]),
        false
    ));
    assert!(!equivalent(
        &Ok(vec![vec![V::Null, V::I(1)]]),
        &Ok(vec![vec![V::I(1), V::Null]]),
        false
    ));
}

#[test]
fn engine_versions() {
    assert_eq!(polars::VERSION, "0.55.2");
    let connection = duckdb::Connection::open_in_memory().unwrap();
    let version: String = connection
        .query_row("SELECT version()", [], |r| r.get(0))
        .unwrap();
    assert!(version.starts_with('v'));
    if let Ok(directory) = std::env::var("KIX_AUDIT_RESULTS") {
        std::fs::create_dir_all(&directory).unwrap();
        std::fs::write(
            format!("{directory}/engine-versions.json"),
            serde_json::to_vec_pretty(&serde_json::json!({
                "polarsCrate": polars::VERSION, "duckdbCrate": "1.20000.1", "duckdbLibrary": version,
                "extensionsDownloaded": false, "externalConnections": false,
                "productionRuntime": false, "productionConformance": false,
                "productionReadiness": false, "fundsExecuted": false
            }))
            .unwrap(),
        )
        .unwrap();
    }
}
