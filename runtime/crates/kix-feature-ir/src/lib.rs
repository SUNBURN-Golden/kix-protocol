#![forbid(unsafe_code)]
//! Engine-neutral feature/query IR for KIX analytical and AI workloads.
//!
//! The IR carries KIX semantic policy explicitly. Polars/libcudf adapters must
//! compile these fields without relying on upstream defaults.

use kix_feature_semantics::{
    AggregateKind, DivideByZeroPolicy, EmptyAggregatePolicy, NullEquality, NullKeyPolicy,
    NullOrder, NullPredicatePolicy, NullValuePolicy, OverflowPolicy, SortStability, empty_policy,
};
use kix_types::{AssetId, KixId, RegistryVersion};

pub const FEATURE_IR_VERSION: u16 = 1;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FeatureIrError {
    EmptyPlan,
    InvalidStage,
    EmptyProjection,
    EmptyGroupKeysAndAggregates,
    TerminalF64KindMismatch,
    TerminalF64MustBeFinal,
    AggregatePolicyMismatch,
    Fast64ProfileOutOfRange,
    Fast64AmountOutOfRange,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ColumnId(pub u16);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum JoinKind {
    Inner,
    Left,
    Semi,
    Anti,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CompareOp {
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ArithmeticOp {
    Add,
    Sub,
    Mul,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AggregateOp {
    Count,
    Sum,
    Min,
    Max,
    Mean,
}

impl AggregateOp {
    const fn semantics_kind(self) -> AggregateKind {
        match self {
            Self::Count => AggregateKind::Count,
            Self::Sum => AggregateKind::Sum,
            Self::Min => AggregateKind::Min,
            Self::Max => AggregateKind::Max,
            Self::Mean => AggregateKind::Mean,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OutputKind {
    Bool,
    I64,
    U64,
    Bytes,
    Category,
    TerminalF64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Scalar {
    Bool(bool),
    I64(i64),
    U64(u64),
    Bytes(Vec<u8>),
    Category {
        vocabulary_id: u32,
        semantic_code: u32,
    },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Expr {
    Column(ColumnId),
    Literal(Scalar),
    Compare {
        op: CompareOp,
        left: Box<Expr>,
        right: Box<Expr>,
    },
    Arithmetic {
        op: ArithmeticOp,
        overflow: OverflowPolicy,
        left: Box<Expr>,
        right: Box<Expr>,
    },
    DivideToF64 {
        numerator: Box<Expr>,
        denominator: Box<Expr>,
        divide_by_zero: DivideByZeroPolicy,
    },
    And(Box<Expr>, Box<Expr>),
    Or(Box<Expr>, Box<Expr>),
    Not(Box<Expr>),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct DatasetRef {
    pub dataset_id: KixId,
    pub schema_version: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Projection {
    pub output: ColumnId,
    pub output_kind: OutputKind,
    pub expr: Expr,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct JoinSpec {
    pub right: DatasetRef,
    pub kind: JoinKind,
    pub left_key: ColumnId,
    pub right_key: ColumnId,
    pub null_equality: NullEquality,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AggregateSpec {
    pub output: ColumnId,
    pub output_kind: OutputKind,
    pub op: AggregateOp,
    pub input: Option<ColumnId>,
    pub null_policy: NullValuePolicy,
    pub empty_policy: EmptyAggregatePolicy,
    pub overflow_policy: OverflowPolicy,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Stage {
    Filter {
        predicate: Expr,
        null_predicate: NullPredicatePolicy,
    },
    Project(Vec<Projection>),
    Join(JoinSpec),
    GroupBy {
        keys: Vec<ColumnId>,
        aggregates: Vec<AggregateSpec>,
        null_keys: NullKeyPolicy,
    },
    Sort {
        by: Vec<ColumnId>,
        descending: bool,
        null_order: NullOrder,
        stability: SortStability,
    },
    Limit(u64),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FeaturePlanV1 {
    pub plan_id: KixId,
    pub source: DatasetRef,
    pub stages: Vec<Stage>,
}

fn contains_divide_to_f64(expr: &Expr) -> bool {
    match expr {
        Expr::DivideToF64 { .. } => true,
        Expr::Compare { left, right, .. } | Expr::Arithmetic { left, right, .. } => {
            contains_divide_to_f64(left) || contains_divide_to_f64(right)
        }
        Expr::And(left, right) | Expr::Or(left, right) => {
            contains_divide_to_f64(left) || contains_divide_to_f64(right)
        }
        Expr::Not(inner) => contains_divide_to_f64(inner),
        Expr::Column(_) | Expr::Literal(_) => false,
    }
}

fn stage_produces_terminal_f64(stage: &Stage) -> Result<bool, FeatureIrError> {
    match stage {
        Stage::Project(items) => {
            for item in items {
                let root_divide = matches!(item.expr, Expr::DivideToF64 { .. });
                if root_divide != (item.output_kind == OutputKind::TerminalF64) {
                    return Err(FeatureIrError::TerminalF64KindMismatch);
                }
                if !root_divide && contains_divide_to_f64(&item.expr) {
                    return Err(FeatureIrError::TerminalF64MustBeFinal);
                }
            }
            Ok(items
                .iter()
                .any(|item| item.output_kind == OutputKind::TerminalF64))
        }
        Stage::GroupBy { aggregates, .. } => {
            for aggregate in aggregates {
                let is_mean = aggregate.op == AggregateOp::Mean;
                if is_mean != (aggregate.output_kind == OutputKind::TerminalF64) {
                    return Err(FeatureIrError::TerminalF64KindMismatch);
                }
                if aggregate.empty_policy != empty_policy(aggregate.op.semantics_kind()) {
                    return Err(FeatureIrError::AggregatePolicyMismatch);
                }
            }
            Ok(aggregates
                .iter()
                .any(|aggregate| aggregate.output_kind == OutputKind::TerminalF64))
        }
        _ => Ok(false),
    }
}

impl FeaturePlanV1 {
    pub fn validate(&self) -> Result<(), FeatureIrError> {
        if self.stages.is_empty() {
            return Err(FeatureIrError::EmptyPlan);
        }
        for (index, stage) in self.stages.iter().enumerate() {
            match stage {
                Stage::Project(items) if items.is_empty() => {
                    return Err(FeatureIrError::EmptyProjection);
                }
                Stage::GroupBy {
                    keys, aggregates, ..
                } if keys.is_empty() && aggregates.is_empty() => {
                    return Err(FeatureIrError::EmptyGroupKeysAndAggregates);
                }
                Stage::Sort { by, .. } if by.is_empty() => {
                    return Err(FeatureIrError::InvalidStage);
                }
                _ => {}
            }

            if stage_produces_terminal_f64(stage)?
                && self.stages[index + 1..]
                    .iter()
                    .any(|later| !matches!(later, Stage::Limit(_)))
            {
                return Err(FeatureIrError::TerminalF64MustBeFinal);
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct MoneyProfileKey {
    pub asset_id: AssetId,
    pub registry_version: RegistryVersion,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Fast64MoneyProfile {
    pub key: MoneyProfileKey,
    execution_max_atoms: i64,
}

impl Fast64MoneyProfile {
    pub fn checked(
        key: MoneyProfileKey,
        execution_max_atoms: u128,
    ) -> Result<Self, FeatureIrError> {
        if execution_max_atoms > i64::MAX as u128 {
            return Err(FeatureIrError::Fast64ProfileOutOfRange);
        }
        Ok(Self {
            key,
            execution_max_atoms: execution_max_atoms as i64,
        })
    }

    pub const fn execution_max_atoms(self) -> i64 {
        self.execution_max_atoms
    }

    pub fn export_atoms(self, atoms: u128) -> Result<i64, FeatureIrError> {
        if atoms > self.execution_max_atoms as u128 {
            return Err(FeatureIrError::Fast64AmountOutOfRange);
        }
        i64::try_from(atoms).map_err(|_| FeatureIrError::Fast64AmountOutOfRange)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn id(byte: u8) -> KixId {
        KixId::from_bytes([byte; 16])
    }

    fn sum_spec(output: u16, input: u16) -> AggregateSpec {
        AggregateSpec {
            output: ColumnId(output),
            output_kind: OutputKind::I64,
            op: AggregateOp::Sum,
            input: Some(ColumnId(input)),
            null_policy: NullValuePolicy::Ignore,
            empty_policy: EmptyAggregatePolicy::Null,
            overflow_policy: OverflowPolicy::Error,
        }
    }

    #[test]
    fn engine_neutral_plan_validates_with_explicit_semantics() {
        let plan = FeaturePlanV1 {
            plan_id: id(1),
            source: DatasetRef {
                dataset_id: id(2),
                schema_version: 7,
            },
            stages: vec![
                Stage::Filter {
                    predicate: Expr::Compare {
                        op: CompareOp::Gt,
                        left: Box::new(Expr::Column(ColumnId(3))),
                        right: Box::new(Expr::Literal(Scalar::I64(100))),
                    },
                    null_predicate: NullPredicatePolicy::Drop,
                },
                Stage::GroupBy {
                    keys: vec![ColumnId(1)],
                    aggregates: vec![sum_spec(10, 3)],
                    null_keys: NullKeyPolicy::Include,
                },
            ],
        };
        assert_eq!(plan.validate(), Ok(()));
    }

    #[test]
    fn terminal_f64_must_be_final_except_limit() {
        let divide = Projection {
            output: ColumnId(9),
            output_kind: OutputKind::TerminalF64,
            expr: Expr::DivideToF64 {
                numerator: Box::new(Expr::Column(ColumnId(1))),
                denominator: Box::new(Expr::Column(ColumnId(2))),
                divide_by_zero: DivideByZeroPolicy::Null,
            },
        };
        let invalid = FeaturePlanV1 {
            plan_id: id(1),
            source: DatasetRef {
                dataset_id: id(2),
                schema_version: 1,
            },
            stages: vec![
                Stage::Project(vec![divide.clone()]),
                Stage::Sort {
                    by: vec![ColumnId(9)],
                    descending: false,
                    null_order: NullOrder::Last,
                    stability: SortStability::Stable,
                },
            ],
        };
        assert_eq!(
            invalid.validate(),
            Err(FeatureIrError::TerminalF64MustBeFinal)
        );

        let valid = FeaturePlanV1 {
            plan_id: id(1),
            source: DatasetRef {
                dataset_id: id(2),
                schema_version: 1,
            },
            stages: vec![Stage::Project(vec![divide]), Stage::Limit(100)],
        };
        assert_eq!(valid.validate(), Ok(()));
    }

    #[test]
    fn mean_is_terminal_and_empty_is_null() {
        let plan = FeaturePlanV1 {
            plan_id: id(1),
            source: DatasetRef {
                dataset_id: id(2),
                schema_version: 1,
            },
            stages: vec![Stage::GroupBy {
                keys: vec![ColumnId(1)],
                aggregates: vec![AggregateSpec {
                    output: ColumnId(8),
                    output_kind: OutputKind::TerminalF64,
                    op: AggregateOp::Mean,
                    input: Some(ColumnId(2)),
                    null_policy: NullValuePolicy::Ignore,
                    empty_policy: EmptyAggregatePolicy::Null,
                    overflow_policy: OverflowPolicy::Error,
                }],
                null_keys: NullKeyPolicy::Include,
            }],
        };
        assert_eq!(plan.validate(), Ok(()));
    }

    #[test]
    fn fast64_profile_is_bound_to_asset_and_registry_version() {
        let asset = AssetId::from_bytes([3_u8; 32]);
        let v2 = RegistryVersion::new(2).unwrap();
        let v3 = RegistryVersion::new(3).unwrap();
        let p2 = Fast64MoneyProfile::checked(
            MoneyProfileKey {
                asset_id: asset,
                registry_version: v2,
            },
            i64::MAX as u128,
        )
        .unwrap();
        assert_eq!(p2.export_atoms(100).unwrap(), 100);
        assert_eq!(p2.key.registry_version, v2);
        assert_ne!(p2.key.registry_version, v3);
        assert_eq!(
            Fast64MoneyProfile::checked(
                MoneyProfileKey {
                    asset_id: asset,
                    registry_version: v3,
                },
                i64::MAX as u128 + 1,
            ),
            Err(FeatureIrError::Fast64ProfileOutOfRange)
        );
    }

    #[test]
    fn empty_plan_is_rejected() {
        let plan = FeaturePlanV1 {
            plan_id: id(1),
            source: DatasetRef {
                dataset_id: id(2),
                schema_version: 1,
            },
            stages: vec![],
        };
        assert_eq!(plan.validate(), Err(FeatureIrError::EmptyPlan));
    }
}
