use super::data::*;
use duckdb::Connection;
use kix_feature_ir::*;
use kix_feature_semantics::*;

fn dtype(kind: OutputKind) -> &'static str {
    match kind {
        OutputKind::I64 => "BIGINT",
        OutputKind::U64 => "UBIGINT",
        OutputKind::Bool => "BOOLEAN",
        OutputKind::TerminalF64 => "DOUBLE",
        _ => "BLOB",
    }
}
fn literal(v: &V) -> String {
    match v {
        V::Null => "NULL".into(),
        V::I(i) => format!("CAST('{i}' AS BIGINT)"),
        V::U(u) => format!("CAST('{u}' AS UBIGINT)"),
        V::Bool(b) => b.to_string(),
        V::B(b) => format!("from_hex('{}')", hex(b)),
        V::F(_) => panic!("no f64 input"),
    }
}
fn expression(e: &Expr) -> Result<String, String> {
    Ok(match e {
        Expr::Column(c) => name(*c),
        Expr::Literal(s) => literal(&match s {
            Scalar::I64(i) => V::I(*i),
            Scalar::U64(u) => V::U(*u),
            Scalar::Bool(b) => V::Bool(*b),
            Scalar::Bytes(b) => V::B(b.clone()),
            _ => return Err("unsupported literal".into()),
        }),
        Expr::Compare { op, left, right } => format!(
            "({} {} {})",
            expression(left)?,
            match op {
                CompareOp::Eq => "=",
                CompareOp::Ne => "<>",
                CompareOp::Lt => "<",
                CompareOp::Le => "<=",
                CompareOp::Gt => ">",
                CompareOp::Ge => ">=",
            },
            expression(right)?
        ),
        Expr::Arithmetic {
            op, left, right, ..
        } => format!(
            "({} {} {})",
            expression(left)?,
            match op {
                ArithmeticOp::Add => "+",
                ArithmeticOp::Sub => "-",
                ArithmeticOp::Mul => "*",
            },
            expression(right)?
        ),
        _ => return Err("unsupported expression (including Wide128 money arithmetic)".into()),
    })
}
pub fn execute(data: &Data, plan: &ValidatedFeaturePlan<'_>) -> (String, Outcome) {
    let mut sql = String::new();
    let result = inner(data, plan, &mut sql).map_err(|e| format!("DuckDB: {e}"));
    (sql, result)
}
fn inner(data: &Data, plan: &ValidatedFeaturePlan<'_>, log: &mut String) -> Outcome {
    let conn = Connection::open_in_memory().map_err(|e| e.to_string())?;
    conn.execute_batch("SET autoinstall_known_extensions=false; SET autoload_known_extensions=false; SET threads=1;").map_err(|e|e.to_string())?;
    for (i, t) in data.tables.iter().enumerate() {
        let columns = t
            .schema
            .columns
            .iter()
            .map(|c| format!("{} {}", name(c.column), dtype(c.kind)))
            .collect::<Vec<_>>()
            .join(",");
        conn.execute_batch(&format!("CREATE TABLE t{i} ({columns}, _ord BIGINT);"))
            .map_err(|e| e.to_string())?;
        for (ord, row) in t.rows.iter().enumerate() {
            let values = row
                .iter()
                .map(literal)
                .chain([ord.to_string()])
                .collect::<Vec<_>>()
                .join(",");
            conn.execute_batch(&format!("INSERT INTO t{i} VALUES ({values});"))
                .map_err(|e| e.to_string())?;
        }
    }
    let source = data
        .tables
        .iter()
        .position(|t| t.schema.dataset == plan.plan().source)
        .unwrap();
    let mut current = format!("t{source}");
    let mut schema = data.tables[source].schema.columns.clone();
    for (i, stage) in plan.plan().stages.iter().enumerate() {
        let query = match stage {
            Stage::Project(items) => {
                let projected = items
                    .iter()
                    .map(|p| {
                        Ok(format!(
                            "CAST({} AS {}) AS {}",
                            expression(&p.expr)?,
                            dtype(p.output_kind),
                            name(p.output)
                        ))
                    })
                    .collect::<Result<Vec<_>, String>>()?
                    .join(",");
                schema = items
                    .iter()
                    .map(|p| ColumnSchema {
                        column: p.output,
                        kind: p.output_kind,
                    })
                    .collect();
                format!("SELECT {projected},_ord FROM {current}")
            }
            Stage::Filter { predicate, .. } => {
                format!("SELECT * FROM {current} WHERE {}", expression(predicate)?)
            }
            Stage::Limit(n) => format!("SELECT * FROM {current} ORDER BY _ord LIMIT {n}"),
            Stage::Sort {
                by,
                descending,
                null_order,
                stability,
            } => {
                let mut ordering = by
                    .iter()
                    .map(|c| {
                        format!(
                            "{} {} NULLS {}",
                            name(*c),
                            if *descending { "DESC" } else { "ASC" },
                            if *null_order == NullOrder::First {
                                "FIRST"
                            } else {
                                "LAST"
                            }
                        )
                    })
                    .collect::<Vec<_>>();
                if *stability == SortStability::Stable {
                    ordering.push("_ord ASC".into());
                }
                let ordering = ordering.join(",");
                format!(
                    "SELECT * EXCLUDE(_ord), row_number() OVER (ORDER BY {ordering}) AS _ord FROM {current}"
                )
            }
            Stage::Join(spec) => {
                let ri = data
                    .tables
                    .iter()
                    .position(|t| t.schema.dataset == spec.right)
                    .unwrap();
                let operator = if spec.null_equality == NullEquality::Equal {
                    "IS NOT DISTINCT FROM"
                } else {
                    "="
                };
                let condition = format!(
                    "l.{} {operator} r.{}",
                    name(spec.left_key),
                    name(spec.right_key)
                );
                let mut cols = schema
                    .iter()
                    .map(|c| format!("l.{}", name(c.column)))
                    .collect::<Vec<_>>();
                let (kind, order) = match spec.kind {
                    JoinKind::Inner | JoinKind::Left => {
                        cols.extend(
                            data.tables[ri]
                                .schema
                                .columns
                                .iter()
                                .map(|c| format!("r.{}", name(c.column))),
                        );
                        schema.extend(data.tables[ri].schema.columns.clone());
                        (
                            if spec.kind == JoinKind::Inner {
                                "INNER"
                            } else {
                                "LEFT"
                            },
                            "l._ord,r._ord",
                        )
                    }
                    JoinKind::Semi => ("SEMI", "l._ord"),
                    JoinKind::Anti => ("ANTI", "l._ord"),
                };
                format!(
                    "SELECT {},row_number() OVER (ORDER BY {order}) AS _ord FROM {current} l {kind} JOIN t{ri} r ON {condition}",
                    cols.join(",")
                )
            }
            Stage::GroupBy {
                keys,
                aggregates,
                null_keys,
            } => {
                let mut cols = keys.iter().map(|k| name(*k)).collect::<Vec<_>>();
                for a in aggregates {
                    let function = match a.op {
                        AggregateOp::Count => "count",
                        AggregateOp::Sum => "sum",
                        AggregateOp::Min => "min",
                        AggregateOp::Max => "max",
                        AggregateOp::Mean => "avg",
                    };
                    let input = a.input.map(name).unwrap_or("*".into());
                    cols.push(format!(
                        "CAST({function}({input}) AS {}) AS {}",
                        dtype(a.output_kind),
                        name(a.output)
                    ));
                }
                let where_clause = if *null_keys == NullKeyPolicy::Exclude && !keys.is_empty() {
                    format!(
                        " WHERE {}",
                        keys.iter()
                            .map(|k| format!("{} IS NOT NULL", name(*k)))
                            .collect::<Vec<_>>()
                            .join(" AND ")
                    )
                } else {
                    String::new()
                };
                let group = if keys.is_empty() {
                    String::new()
                } else {
                    format!(
                        " GROUP BY {}",
                        keys.iter().map(|k| name(*k)).collect::<Vec<_>>().join(",")
                    )
                };
                schema = keys
                    .iter()
                    .map(|k| schema[index(&schema, *k)])
                    .chain(aggregates.iter().map(|a| ColumnSchema {
                        column: a.output,
                        kind: a.output_kind,
                    }))
                    .collect();
                format!(
                    "SELECT {},row_number() OVER () AS _ord FROM {current}{where_clause}{group}",
                    cols.join(",")
                )
            }
        };
        let next = format!("stage{i}");
        let command = format!("CREATE TEMP TABLE {next} AS {query};\n");
        log.push_str(&command);
        conn.execute_batch(&command).map_err(|e| e.to_string())?;
        current = next;
    }
    schema.sort_by_key(|c| c.column);
    let output = schema
        .iter()
        .map(|c| match c.kind {
            OutputKind::Bytes | OutputKind::Category => format!("hex({})", name(c.column)),
            _ => format!("CAST({} AS VARCHAR)", name(c.column)),
        })
        .collect::<Vec<_>>()
        .join(",");
    let query = format!("SELECT {output} FROM {current} ORDER BY _ord");
    log.push_str(&query);
    let mut stmt = conn.prepare(&query).map_err(|e| e.to_string())?;
    let mut rows = stmt.query([]).map_err(|e| e.to_string())?;
    let mut output = vec![];
    while let Some(row) = rows.next().map_err(|e| e.to_string())? {
        let mut values = vec![];
        for (i, c) in schema.iter().enumerate() {
            let text: Option<String> = row.get(i).map_err(|e| e.to_string())?;
            values.push(match text {
                None => V::Null,
                Some(s) => match c.kind {
                    OutputKind::I64 => V::I(s.parse().unwrap()),
                    OutputKind::U64 => V::U(s.parse().unwrap()),
                    OutputKind::Bool => V::Bool(s == "true"),
                    OutputKind::TerminalF64 => {
                        let f: f64 = s.parse().unwrap();
                        validate_terminal_f64(f).map_err(|_| "nonfinite")?;
                        V::F(f.to_string())
                    }
                    _ => V::B(
                        (0..s.len())
                            .step_by(2)
                            .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
                            .collect(),
                    ),
                },
            });
        }
        output.push(values);
    }
    Ok(output)
}
