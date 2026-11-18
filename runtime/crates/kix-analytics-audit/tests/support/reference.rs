use super::data::*;
use kix_feature_ir::*;
use kix_feature_semantics::*;
use std::collections::BTreeMap;

fn scalar(s: &Scalar) -> V {
    match s {
        Scalar::Bool(b) => V::Bool(*b),
        Scalar::I64(i) => V::I(*i),
        Scalar::U64(u) => V::U(*u),
        Scalar::Bytes(b) => V::B(b.clone()),
        _ => panic!("unsupported literal"),
    }
}
fn expr(e: &Expr, row: &[V], schema: &[ColumnSchema]) -> Result<V, String> {
    Ok(match e {
        Expr::Column(c) => row[index(schema, *c)].clone(),
        Expr::Literal(s) => scalar(s),
        Expr::Compare { op, left, right } => {
            let (l, r) = (expr(left, row, schema)?, expr(right, row, schema)?);
            if l.is_null() || r.is_null() {
                V::Null
            } else {
                V::Bool(match op {
                    CompareOp::Eq => l == r,
                    CompareOp::Ne => l != r,
                    CompareOp::Lt => l < r,
                    CompareOp::Le => l <= r,
                    CompareOp::Gt => l > r,
                    CompareOp::Ge => l >= r,
                })
            }
        }
        Expr::Arithmetic {
            op, left, right, ..
        } => {
            let (l, r) = (expr(left, row, schema)?, expr(right, row, schema)?);
            match (l, r) {
                (V::Null, _) | (_, V::Null) => V::Null,
                (V::I(l), V::I(r)) => V::I(
                    match op {
                        ArithmeticOp::Add => l.checked_add(r),
                        ArithmeticOp::Sub => l.checked_sub(r),
                        ArithmeticOp::Mul => l.checked_mul(r),
                    }
                    .ok_or("overflow")?,
                ),
                (V::U(l), V::U(r)) => V::U(
                    match op {
                        ArithmeticOp::Add => l.checked_add(r),
                        ArithmeticOp::Sub => l.checked_sub(r),
                        ArithmeticOp::Mul => l.checked_mul(r),
                    }
                    .ok_or("overflow")?,
                ),
                _ => return Err("unsupported arithmetic".into()),
            }
        }
        _ => return Err("unsupported expression".into()),
    })
}
pub fn execute(data: &Data, plan: &ValidatedFeaturePlan<'_>) -> Outcome {
    let input = data.table(plan.plan().source);
    let (mut rows, mut schema) = (input.rows.clone(), input.schema.columns.clone());
    for stage in &plan.plan().stages {
        match stage {
            Stage::Filter { predicate, .. } => {
                let mut kept = vec![];
                for row in rows {
                    let v = expr(predicate, &row, &schema)?;
                    if filter_keeps(match v {
                        V::Bool(b) => Some(b),
                        _ => None,
                    }) {
                        kept.push(row);
                    }
                }
                rows = kept;
            }
            Stage::Project(items) => {
                rows = rows
                    .iter()
                    .map(|row| items.iter().map(|p| expr(&p.expr, row, &schema)).collect())
                    .collect::<Result<_, _>>()?;
                schema = items
                    .iter()
                    .map(|p| ColumnSchema {
                        column: p.output,
                        kind: p.output_kind,
                    })
                    .collect();
            }
            Stage::Sort {
                by,
                descending,
                null_order,
                ..
            } => {
                rows.sort_by(|a, b| {
                    for c in by {
                        let (l, r) = (&a[index(&schema, *c)], &b[index(&schema, *c)]);
                        let ordering = match (l.is_null(), r.is_null()) {
                            (true, true) => std::cmp::Ordering::Equal,
                            (true, false) => {
                                if *null_order == NullOrder::First {
                                    std::cmp::Ordering::Less
                                } else {
                                    std::cmp::Ordering::Greater
                                }
                            }
                            (false, true) => {
                                if *null_order == NullOrder::First {
                                    std::cmp::Ordering::Greater
                                } else {
                                    std::cmp::Ordering::Less
                                }
                            }
                            _ => {
                                if *descending {
                                    r.cmp(l)
                                } else {
                                    l.cmp(r)
                                }
                            }
                        };
                        if !ordering.is_eq() {
                            return ordering;
                        }
                    }
                    std::cmp::Ordering::Equal
                });
            }
            Stage::Limit(n) => rows.truncate(*n as usize),
            Stage::Join(spec) => {
                let right = data.table(spec.right);
                let (li, ri) = (
                    index(&schema, spec.left_key),
                    index(&right.schema.columns, spec.right_key),
                );
                let mut output = vec![];
                for left in &rows {
                    let matches: Vec<_> = right
                        .rows
                        .iter()
                        .filter(|r| {
                            let (l, r) = (&left[li], &r[ri]);
                            nullable_keys_equal(l.is_null(), r.is_null(), spec.null_equality)
                                && (l.is_null() || l == r)
                        })
                        .collect();
                    match spec.kind {
                        JoinKind::Inner | JoinKind::Left => {
                            if matches.is_empty() && spec.kind == JoinKind::Left {
                                let mut row = left.clone();
                                row.extend(vec![V::Null; right.schema.columns.len()]);
                                output.push(row);
                            }
                            for r in matches {
                                let mut row = left.clone();
                                row.extend(r.clone());
                                output.push(row);
                            }
                        }
                        JoinKind::Semi if !matches.is_empty() => output.push(left.clone()),
                        JoinKind::Anti if matches.is_empty() => output.push(left.clone()),
                        _ => (),
                    }
                }
                if matches!(spec.kind, JoinKind::Inner | JoinKind::Left) {
                    schema.extend(right.schema.columns.clone());
                }
                rows = output;
            }
            Stage::GroupBy {
                keys,
                aggregates,
                null_keys,
            } => {
                let mut groups: BTreeMap<Vec<V>, Rows> = BTreeMap::new();
                for row in rows {
                    let key: Vec<_> = keys
                        .iter()
                        .map(|k| row[index(&schema, *k)].clone())
                        .collect();
                    if *null_keys == NullKeyPolicy::Exclude && key.iter().any(V::is_null) {
                        continue;
                    }
                    groups.entry(key).or_default().push(row);
                }
                if keys.is_empty() && groups.is_empty() {
                    groups.insert(vec![], vec![]);
                }
                rows = vec![];
                for (mut key, group) in groups {
                    for a in aggregates {
                        let values: Vec<_> = a
                            .input
                            .map(|c| {
                                group
                                    .iter()
                                    .map(|r| r[index(&schema, c)].clone())
                                    .filter(|v| !v.is_null())
                                    .collect()
                            })
                            .unwrap_or_default();
                        let result = match a.op {
                            AggregateOp::Count => V::U(if a.input.is_none() {
                                group.len()
                            } else {
                                values.len()
                            } as u64),
                            _ if values.is_empty() => V::Null,
                            AggregateOp::Min => values.iter().min().unwrap().clone(),
                            AggregateOp::Max => values.iter().max().unwrap().clone(),
                            AggregateOp::Mean => {
                                let sum: f64 = values
                                    .iter()
                                    .map(|v| match v {
                                        V::I(i) => *i as f64,
                                        V::U(u) => *u as f64,
                                        _ => panic!(),
                                    })
                                    .sum();
                                V::F((sum / values.len() as f64).to_string())
                            }
                            AggregateOp::Sum => match a.output_kind {
                                OutputKind::I64 => V::I(
                                    values
                                        .iter()
                                        .try_fold(0i64, |n, v| {
                                            if let V::I(i) = v {
                                                n.checked_add(*i)
                                            } else {
                                                None
                                            }
                                        })
                                        .ok_or("overflow")?,
                                ),
                                OutputKind::U64 => V::U(
                                    values
                                        .iter()
                                        .try_fold(0u64, |n, v| {
                                            if let V::U(u) = v {
                                                n.checked_add(*u)
                                            } else {
                                                None
                                            }
                                        })
                                        .ok_or("overflow")?,
                                ),
                                _ => return Err("unsupported sum".into()),
                            },
                        };
                        key.push(result);
                    }
                    rows.push(key);
                }
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
    }
    // Canonical output column identity is ColumnId order, not physical join layout.
    let mut indices: Vec<_> = (0..schema.len()).collect();
    indices.sort_by_key(|i| schema[*i].column);
    Ok(rows
        .iter()
        .map(|r| indices.iter().map(|i| r[*i].clone()).collect())
        .collect())
}
