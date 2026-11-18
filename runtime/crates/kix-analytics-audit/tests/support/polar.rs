use super::data::*;
use kix_feature_ir::{self as ir, ColumnSchema, OutputKind, Stage, ValidatedFeaturePlan};
use kix_feature_semantics::*;
use polars::prelude::*;

fn dtype(kind: OutputKind) -> DataType {
    match kind {
        OutputKind::Bool => DataType::Boolean,
        OutputKind::I64 => DataType::Int64,
        OutputKind::U64 => DataType::UInt64,
        OutputKind::TerminalF64 => DataType::Float64,
        _ => DataType::Binary,
    }
}
fn frame(table: &Table) -> PolarsResult<DataFrame> {
    let columns = table
        .schema
        .columns
        .iter()
        .enumerate()
        .map(|(i, c)| {
            let n = name(c.column).into();
            let series = match c.kind {
                OutputKind::I64 => Series::new(
                    n,
                    table
                        .rows
                        .iter()
                        .map(|r| if let V::I(v) = r[i] { Some(v) } else { None })
                        .collect::<Vec<_>>(),
                ),
                OutputKind::U64 => Series::new(
                    n,
                    table
                        .rows
                        .iter()
                        .map(|r| if let V::U(v) = r[i] { Some(v) } else { None })
                        .collect::<Vec<_>>(),
                ),
                OutputKind::Bool => Series::new(
                    n,
                    table
                        .rows
                        .iter()
                        .map(|r| if let V::Bool(v) = r[i] { Some(v) } else { None })
                        .collect::<Vec<_>>(),
                ),
                _ => Series::new(
                    n,
                    table
                        .rows
                        .iter()
                        .map(|r| {
                            if let V::B(ref b) = r[i] {
                                Some(b.as_slice())
                            } else {
                                None
                            }
                        })
                        .collect::<Vec<_>>(),
                ),
            };
            series.into_column()
        })
        .collect();
    DataFrame::new_infer_height(columns)
}
fn kind(e: &ir::Expr, schema: &[ColumnSchema]) -> OutputKind {
    match e {
        ir::Expr::Column(c) => schema[index(schema, *c)].kind,
        ir::Expr::Literal(ir::Scalar::U64(_)) => OutputKind::U64,
        ir::Expr::Literal(ir::Scalar::I64(_)) => OutputKind::I64,
        ir::Expr::Arithmetic { left, .. } => kind(left, schema),
        _ => OutputKind::Bool,
    }
}
fn expression(e: &ir::Expr, schema: &[ColumnSchema]) -> Result<Expr, String> {
    use ir::{ArithmeticOp as A, CompareOp as C, Expr as E, Scalar as S};
    Ok(match e {
        E::Column(c) => col(name(*c)),
        E::Literal(S::I64(i)) => lit(*i),
        E::Literal(S::U64(u)) => lit(*u),
        E::Literal(S::Bool(b)) => lit(*b),
        E::Compare { op, left, right } => {
            let (l, r) = (expression(left, schema)?, expression(right, schema)?);
            match op {
                C::Eq => l.eq(r),
                C::Ne => l.neq(r),
                C::Lt => l.lt(r),
                C::Le => l.lt_eq(r),
                C::Gt => l.gt(r),
                C::Ge => l.gt_eq(r),
            }
        }
        E::Arithmetic {
            op, left, right, ..
        } => {
            let target = kind(left, schema);
            let (l, r) = (expression(left, schema)?, expression(right, schema)?);
            // I64 products and all I64/U64 sums/differences fit in Int128.
            // U64 products need an engine-side division guard before widening.
            let result = if target == OutputKind::U64 && *op == A::Mul {
                let nonzero = when(r.clone().eq(lit(0u64)))
                    .then(lit(1u64))
                    .otherwise(r.clone());
                let invalid = l.clone().gt(lit(u64::MAX).floor_div(nonzero));
                let safe_l = when(invalid.clone()).then(lit(0u64)).otherwise(l);
                when(invalid)
                    .then(lit(-1i64).cast(DataType::Int128))
                    .otherwise(safe_l.cast(DataType::Int128) * r.cast(DataType::Int128))
            } else {
                let (l, r) = (l.cast(DataType::Int128), r.cast(DataType::Int128));
                match op {
                    A::Add => l + r,
                    A::Sub => l - r,
                    A::Mul => l * r,
                }
            };
            result.strict_cast(dtype(target))
        }
        _ => return Err("unsupported expression (including Wide128 money arithmetic)".into()),
    })
}
pub fn execute(data: &Data, plan: &ValidatedFeaturePlan<'_>) -> Outcome {
    execute_inner(data, plan).map_err(|e| format!("Polars: {e}"))
}
fn execute_inner(data: &Data, plan: &ValidatedFeaturePlan<'_>) -> Outcome {
    let input = data.table(plan.plan().source);
    let mut schema = input.schema.columns.clone();
    let mut df = frame(input).map_err(|e| e.to_string())?;
    for stage in &plan.plan().stages {
        let mut lazy = df.lazy();
        match stage {
            Stage::Project(items) => {
                let expressions = items
                    .iter()
                    .map(|p| Ok(expression(&p.expr, &schema)?.alias(name(p.output))))
                    .collect::<Result<Vec<_>, String>>()?;
                lazy = lazy.select(expressions);
                schema = items
                    .iter()
                    .map(|p| ColumnSchema {
                        column: p.output,
                        kind: p.output_kind,
                    })
                    .collect();
            }
            Stage::Filter { predicate, .. } => lazy = lazy.filter(expression(predicate, &schema)?),
            Stage::Sort {
                by,
                descending,
                null_order,
                stability,
            } => {
                lazy = lazy.sort(
                    by.iter()
                        .map(|c| name(*c).into())
                        .collect::<Vec<PlSmallStr>>(),
                    SortMultipleOptions::default()
                        .with_order_descending(*descending)
                        .with_nulls_last(*null_order == NullOrder::Last)
                        .with_maintain_order(*stability == SortStability::Stable),
                );
            }
            Stage::Limit(n) => lazy = lazy.limit((*n).try_into().map_err(|_| "limit range")?),
            Stage::Join(spec) => {
                let right = data.table(spec.right);
                let how = match spec.kind {
                    ir::JoinKind::Inner => JoinType::Inner,
                    ir::JoinKind::Left => JoinType::Left,
                    ir::JoinKind::Semi => JoinType::Semi,
                    ir::JoinKind::Anti => JoinType::Anti,
                };
                let mut args = JoinArgs::new(how);
                args.nulls_equal = spec.null_equality == NullEquality::Equal;
                args.coalesce = JoinCoalesce::KeepColumns;
                args.maintain_order = MaintainOrderJoin::LeftRight;
                lazy = lazy.join(
                    frame(right).map_err(|e| e.to_string())?.lazy(),
                    [col(name(spec.left_key))],
                    [col(name(spec.right_key))],
                    args,
                );
                if matches!(spec.kind, ir::JoinKind::Inner | ir::JoinKind::Left) {
                    schema.extend(right.schema.columns.clone());
                }
            }
            Stage::GroupBy {
                keys,
                aggregates,
                null_keys,
            } => {
                if *null_keys == NullKeyPolicy::Exclude {
                    for k in keys {
                        lazy = lazy.filter(col(name(*k)).is_not_null());
                    }
                }
                let expressions = aggregates
                    .iter()
                    .map(|a| {
                        let input = a.input.map(|c| col(name(c)));
                        let value = match a.op {
                            ir::AggregateOp::Count => input
                                .map(|c| c.count())
                                .unwrap_or_else(len)
                                .cast(DataType::UInt64),
                            _ => {
                                let c = input.unwrap();
                                let value = match a.op {
                                    ir::AggregateOp::Sum => c
                                        .clone()
                                        .cast(DataType::Int128)
                                        .sum()
                                        .strict_cast(dtype(a.output_kind)),
                                    ir::AggregateOp::Min => c.clone().min(),
                                    ir::AggregateOp::Max => c.clone().max(),
                                    ir::AggregateOp::Mean => c.clone().mean(),
                                    _ => unreachable!(),
                                };
                                // Upstream SUM(empty)=0; KIX requires NULL.
                                when(c.count().gt(lit(0u32)))
                                    .then(value)
                                    .otherwise(lit(NULL).cast(dtype(a.output_kind)))
                            }
                        };
                        value.alias(name(a.output))
                    })
                    .collect::<Vec<_>>();
                lazy = if keys.is_empty() {
                    lazy.select(expressions)
                } else {
                    lazy.group_by(keys.iter().map(|k| col(name(*k))).collect::<Vec<_>>())
                        .agg(expressions)
                };
                schema = keys
                    .iter()
                    .map(|k| schema[index(&schema, *k)])
                    .chain(aggregates.iter().map(|a| ColumnSchema {
                        column: a.output,
                        kind: a.output_kind,
                    }))
                    .collect();
            }
        }
        // Materialize stages so optimizer reordering cannot suppress an error.
        df = lazy.collect().map_err(|e| e.to_string())?;
    }
    schema.sort_by_key(|c| c.column);
    (0..df.height())
        .map(|i| {
            schema
                .iter()
                .map(|c| {
                    let column = df.column(&name(c.column)).map_err(|e| e.to_string())?;
                    if column.is_null().get(i) == Some(true) {
                        return Ok(V::Null);
                    }
                    Ok(match c.kind {
                        OutputKind::I64 => V::I(column.i64().unwrap().get(i).unwrap()),
                        OutputKind::U64 => V::U(column.u64().unwrap().get(i).unwrap()),
                        OutputKind::Bool => V::Bool(column.bool().unwrap().get(i).unwrap()),
                        OutputKind::TerminalF64 => {
                            let f = column.f64().unwrap().get(i).unwrap();
                            validate_terminal_f64(f).map_err(|_| "nonfinite")?;
                            V::F(f.to_string())
                        }
                        _ => V::B(column.binary().unwrap().get(i).unwrap().to_vec()),
                    })
                })
                .collect()
        })
        .collect()
}
