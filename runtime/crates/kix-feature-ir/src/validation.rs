//! Structural preflight and schema-bound validation share the same expression walker.
use std::collections::{BTreeMap, HashSet};

use super::*;

const MAX_STAGES: usize = 1_024;
const MAX_EXPR_DEPTH: usize = 64;
const MAX_EXPR_NODES: usize = 100_000;
type Columns = BTreeMap<ColumnId, OutputKind>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ColumnSchema {
    pub column: ColumnId,
    pub kind: OutputKind,
}

/// Logical schema supplied by the catalog/export boundary, never by the plan.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DatasetSchema {
    pub dataset: DatasetRef,
    pub columns: Vec<ColumnSchema>,
}

/// Type-checked against the supplied catalog. This is not proof that the catalog
/// or data is authentic; the authenticated exporter remains an S07-D gate.
/// The borrow prevents mutation of the plan while this validation is in use.
#[derive(Debug)]
pub struct ValidatedFeaturePlan<'a> {
    plan: &'a FeaturePlanV1,
    catalog: &'a [DatasetSchema],
    output: Vec<ColumnSchema>,
}

impl<'a> ValidatedFeaturePlan<'a> {
    pub fn plan(&self) -> &'a FeaturePlanV1 {
        self.plan
    }

    pub fn catalog(&self) -> &'a [DatasetSchema] {
        self.catalog
    }

    pub fn output_schema(&self) -> &[ColumnSchema] {
        &self.output
    }
}

fn require_kind(actual: Option<OutputKind>, expected: OutputKind) -> Result<(), FeatureIrError> {
    if actual.is_some_and(|kind| kind != expected) {
        return Err(FeatureIrError::ExpressionTypeMismatch);
    }
    Ok(())
}

fn require_integer(kind: Option<OutputKind>) -> Result<(), FeatureIrError> {
    if kind.is_some_and(|kind| !matches!(kind, OutputKind::I64 | OutputKind::U64)) {
        return Err(FeatureIrError::ExpressionTypeMismatch);
    }
    Ok(())
}

fn require_same(left: Option<OutputKind>, right: Option<OutputKind>) -> Result<(), FeatureIrError> {
    if let (Some(left), Some(right)) = (left, right) {
        require_kind(Some(left), right)?;
    }
    Ok(())
}

fn column_kind(
    id: ColumnId,
    columns: Option<&Columns>,
) -> Result<Option<OutputKind>, FeatureIrError> {
    let Some(columns) = columns else {
        return Ok(None); // Only structural preflight can reach an unknown schema.
    };
    let kind = *columns.get(&id).ok_or(FeatureIrError::UnknownColumn)?;
    if kind == OutputKind::TerminalF64 {
        return Err(FeatureIrError::TerminalF64Input);
    }
    Ok(Some(kind))
}

fn infer_expr(
    expr: &Expr,
    columns: Option<&Columns>,
    terminal_root: bool,
    depth: usize,
    remaining: &mut usize,
) -> Result<Option<OutputKind>, FeatureIrError> {
    if depth > MAX_EXPR_DEPTH || *remaining == 0 {
        return Err(FeatureIrError::PlanTooComplex);
    }
    *remaining -= 1;
    let mut child = |expr: &Expr| infer_expr(expr, columns, false, depth + 1, remaining);
    match expr {
        Expr::Column(id) => column_kind(*id, columns),
        Expr::Literal(value) => Ok(Some(match value {
            Scalar::Bool(_) => OutputKind::Bool,
            Scalar::I64(_) => OutputKind::I64,
            Scalar::U64(_) => OutputKind::U64,
            Scalar::Bytes(_) => OutputKind::Bytes,
            Scalar::Category { .. } => OutputKind::Category,
        })),
        Expr::Compare { left, right, .. } => {
            let left = child(left)?;
            let right = child(right)?;
            require_same(left, right)?;
            Ok(Some(OutputKind::Bool))
        }
        Expr::Arithmetic { left, right, .. } => {
            let left = child(left)?;
            let right = child(right)?;
            require_integer(left)?;
            require_integer(right)?;
            require_same(left, right)?;
            Ok(left.or(right))
        }
        Expr::DivideToF64 {
            numerator,
            denominator,
            ..
        } => {
            if !terminal_root {
                return Err(FeatureIrError::TerminalF64MustBeFinal);
            }
            // Even an allowed terminal root must validate both complete operands.
            let numerator = child(numerator)?;
            let denominator = child(denominator)?;
            require_integer(numerator)?;
            require_integer(denominator)?;
            require_same(numerator, denominator)?;
            Ok(Some(OutputKind::TerminalF64))
        }
        Expr::And(left, right) | Expr::Or(left, right) => {
            require_kind(child(left)?, OutputKind::Bool)?;
            require_kind(child(right)?, OutputKind::Bool)?;
            Ok(Some(OutputKind::Bool))
        }
        Expr::Not(inner) => {
            require_kind(child(inner)?, OutputKind::Bool)?;
            Ok(Some(OutputKind::Bool))
        }
    }
}

fn insert_column(
    columns: &mut Columns,
    id: ColumnId,
    kind: OutputKind,
) -> Result<(), FeatureIrError> {
    if columns.insert(id, kind).is_some() {
        return Err(FeatureIrError::DuplicateColumn);
    }
    Ok(())
}

fn check_keys(keys: &[ColumnId], columns: Option<&Columns>) -> Result<(), FeatureIrError> {
    let mut seen = HashSet::new();
    for key in keys {
        if !seen.insert(*key) {
            return Err(FeatureIrError::DuplicateColumn);
        }
        column_kind(*key, columns)?;
    }
    Ok(())
}

fn resolve_dataset(
    dataset: DatasetRef,
    catalog: &[DatasetSchema],
) -> Result<Columns, FeatureIrError> {
    let schema = catalog
        .iter()
        .find(|schema| schema.dataset == dataset)
        .ok_or(FeatureIrError::UnknownDataset)?;
    Ok(schema
        .columns
        .iter()
        .map(|column| (column.column, column.kind))
        .collect())
}

impl FeaturePlanV1 {
    /// Structural/type preflight only. An unresolved source column is not proof
    /// of a safe executable plan. Backends must use `validate_with_schemas`.
    pub fn validate(&self) -> Result<(), FeatureIrError> {
        self.validate_stages(None).map(|_| ())
    }

    pub fn validate_with_schemas<'a>(
        &'a self,
        catalog: &'a [DatasetSchema],
    ) -> Result<ValidatedFeaturePlan<'a>, FeatureIrError> {
        let mut datasets = HashSet::new();
        for schema in catalog {
            if schema.dataset.schema_version == 0 || !datasets.insert(schema.dataset) {
                return Err(FeatureIrError::InvalidSchema);
            }
            let mut columns = Columns::new();
            for column in &schema.columns {
                if column.kind == OutputKind::TerminalF64 {
                    return Err(FeatureIrError::TerminalF64Input);
                }
                insert_column(&mut columns, column.column, column.kind)?;
            }
        }
        let output = self
            .validate_stages(Some(catalog))?
            .ok_or(FeatureIrError::UnknownDataset)?
            .into_iter()
            .map(|(column, kind)| ColumnSchema { column, kind })
            .collect();
        Ok(ValidatedFeaturePlan {
            plan: self,
            catalog,
            output,
        })
    }

    fn validate_stages(
        &self,
        catalog: Option<&[DatasetSchema]>,
    ) -> Result<Option<Columns>, FeatureIrError> {
        if self.stages.is_empty() {
            return Err(FeatureIrError::EmptyPlan);
        }
        if self.stages.len() > MAX_STAGES {
            return Err(FeatureIrError::PlanTooComplex);
        }
        if self.source.schema_version == 0 {
            return Err(FeatureIrError::InvalidSchema);
        }
        let mut columns = catalog
            .map(|catalog| resolve_dataset(self.source, catalog))
            .transpose()?;
        let mut remaining = MAX_EXPR_NODES;
        let mut terminal = false;
        for stage in &self.stages {
            if terminal && !matches!(stage, Stage::Limit(_)) {
                return Err(FeatureIrError::TerminalF64MustBeFinal);
            }
            match stage {
                Stage::Filter { predicate, .. } => {
                    let kind = infer_expr(predicate, columns.as_ref(), false, 0, &mut remaining)?;
                    require_kind(kind, OutputKind::Bool)?;
                }
                Stage::Project(items) => {
                    if items.is_empty() {
                        return Err(FeatureIrError::EmptyProjection);
                    }
                    let mut output = Columns::new();
                    for item in items {
                        let root_divide = matches!(item.expr, Expr::DivideToF64 { .. });
                        if root_divide != (item.output_kind == OutputKind::TerminalF64) {
                            return Err(FeatureIrError::TerminalF64KindMismatch);
                        }
                        let kind = infer_expr(
                            &item.expr,
                            columns.as_ref(),
                            root_divide,
                            0,
                            &mut remaining,
                        )?;
                        require_kind(kind, item.output_kind)?;
                        insert_column(&mut output, item.output, item.output_kind)?;
                        terminal |= root_divide;
                    }
                    columns = Some(output);
                }
                Stage::GroupBy {
                    keys, aggregates, ..
                } => {
                    if keys.is_empty() && aggregates.is_empty() {
                        return Err(FeatureIrError::EmptyGroupKeysAndAggregates);
                    }
                    check_keys(keys, columns.as_ref())?;
                    let mut output = Columns::new();
                    let mut seen: HashSet<_> = keys.iter().copied().collect();
                    for key in keys {
                        if let Some(kind) = column_kind(*key, columns.as_ref())? {
                            insert_column(&mut output, *key, kind)?;
                        }
                    }
                    for aggregate in aggregates {
                        if !seen.insert(aggregate.output) {
                            return Err(FeatureIrError::DuplicateColumn);
                        }
                        let is_mean = aggregate.op == AggregateOp::Mean;
                        if is_mean != (aggregate.output_kind == OutputKind::TerminalF64) {
                            return Err(FeatureIrError::TerminalF64KindMismatch);
                        }
                        if aggregate.empty_policy != empty_policy(aggregate.op.semantics_kind()) {
                            return Err(FeatureIrError::AggregatePolicyMismatch);
                        }
                        if aggregate.op != AggregateOp::Count && aggregate.input.is_none() {
                            return Err(FeatureIrError::AggregateInputRequired);
                        }
                        let input = match aggregate.input {
                            Some(id) => column_kind(id, columns.as_ref())?,
                            None => None,
                        };
                        match aggregate.op {
                            AggregateOp::Count => {
                                require_kind(Some(aggregate.output_kind), OutputKind::U64)?
                            }
                            AggregateOp::Sum => {
                                require_integer(input)?;
                                require_integer(Some(aggregate.output_kind))?;
                                require_kind(input, aggregate.output_kind)?;
                            }
                            AggregateOp::Mean => require_integer(input)?,
                            AggregateOp::Min | AggregateOp::Max => {
                                require_kind(input, aggregate.output_kind)?
                            }
                        }
                        insert_column(&mut output, aggregate.output, aggregate.output_kind)?;
                        terminal |= is_mean;
                    }
                    columns = if columns.is_some() || keys.is_empty() {
                        Some(output)
                    } else {
                        None
                    };
                }
                Stage::Join(join) => {
                    if join.right.schema_version == 0 {
                        return Err(FeatureIrError::InvalidSchema);
                    }
                    let left_kind = column_kind(join.left_key, columns.as_ref())?;
                    if let Some(catalog) = catalog {
                        let right = resolve_dataset(join.right, catalog)?;
                        let right_kind = column_kind(join.right_key, Some(&right))?;
                        require_same(left_kind, right_kind)?;
                        if matches!(join.kind, JoinKind::Inner | JoinKind::Left) {
                            let output = columns.as_mut().ok_or(FeatureIrError::UnknownDataset)?;
                            for (id, kind) in right {
                                insert_column(output, id, kind)?;
                            }
                        }
                    } else if matches!(join.kind, JoinKind::Inner | JoinKind::Left) {
                        columns = None;
                    }
                }
                Stage::Sort { by, .. } => {
                    if by.is_empty() {
                        return Err(FeatureIrError::InvalidStage);
                    }
                    check_keys(by, columns.as_ref())?;
                }
                Stage::Limit(_) => {}
            }
        }
        Ok(columns)
    }
}
