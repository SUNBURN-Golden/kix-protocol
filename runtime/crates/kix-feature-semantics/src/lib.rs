#![forbid(unsafe_code)]
//! Engine-independent semantic rules for KIX analytical/AI feature execution.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NullEquality {
    Equal,
    Unequal,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NullPredicatePolicy {
    Drop,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NullKeyPolicy {
    Include,
    Exclude,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NullOrder {
    First,
    Last,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SortStability {
    Stable,
    Unstable,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NullValuePolicy {
    Ignore,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EmptyAggregatePolicy {
    Null,
    Zero,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OverflowPolicy {
    Error,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DivideByZeroPolicy {
    Null,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AggregateKind {
    Count,
    Sum,
    Min,
    Max,
    Mean,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SemanticError {
    NonFiniteF64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct CategoryValue {
    pub vocabulary_id: u32,
    pub semantic_code: u32,
}

/// KIX Filter semantics: NULL is not truthy and is dropped.
pub const fn filter_keeps(predicate: Option<bool>) -> bool {
    matches!(predicate, Some(true))
}

/// Returns whether two nullable join keys are considered equal under the plan.
pub const fn nullable_keys_equal(
    left_is_null: bool,
    right_is_null: bool,
    policy: NullEquality,
) -> bool {
    match (left_is_null, right_is_null) {
        (true, true) => matches!(policy, NullEquality::Equal),
        (true, false) | (false, true) => false,
        (false, false) => true,
    }
}

pub const fn empty_policy(kind: AggregateKind) -> EmptyAggregatePolicy {
    match kind {
        AggregateKind::Count => EmptyAggregatePolicy::Zero,
        AggregateKind::Sum | AggregateKind::Min | AggregateKind::Max | AggregateKind::Mean => {
            EmptyAggregatePolicy::Null
        }
    }
}

/// F64 is terminal-only in Semantics v1. NULL numerator/denominator or zero denominator yields NULL.
pub fn divide_i64_to_terminal_f64(numerator: Option<i64>, denominator: Option<i64>) -> Option<f64> {
    let numerator = numerator?;
    let denominator = denominator?;
    if denominator == 0 {
        return None;
    }
    let value = numerator as f64 / denominator as f64;
    debug_assert!(value.is_finite(), "i64/i64 division must be finite");
    Some(value)
}

pub fn validate_terminal_f64(value: f64) -> Result<f64, SemanticError> {
    if value.is_finite() {
        Ok(value)
    } else {
        Err(SemanticError::NonFiniteF64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn filter_null_is_dropped() {
        assert!(filter_keeps(Some(true)));
        assert!(!filter_keeps(Some(false)));
        assert!(!filter_keeps(None));
    }

    #[test]
    fn null_join_semantics_are_explicit() {
        assert!(nullable_keys_equal(true, true, NullEquality::Equal));
        assert!(!nullable_keys_equal(true, true, NullEquality::Unequal));
        assert!(!nullable_keys_equal(true, false, NullEquality::Equal));
    }

    #[test]
    fn aggregate_empty_semantics_are_fixed() {
        assert_eq!(
            empty_policy(AggregateKind::Count),
            EmptyAggregatePolicy::Zero
        );
        assert_eq!(empty_policy(AggregateKind::Sum), EmptyAggregatePolicy::Null);
        assert_eq!(
            empty_policy(AggregateKind::Mean),
            EmptyAggregatePolicy::Null
        );
    }

    #[test]
    fn divide_by_zero_and_null_produce_null() {
        assert_eq!(divide_i64_to_terminal_f64(Some(10), Some(2)), Some(5.0));
        assert_eq!(divide_i64_to_terminal_f64(Some(10), Some(0)), None);
        assert_eq!(divide_i64_to_terminal_f64(None, Some(2)), None);
        assert_eq!(divide_i64_to_terminal_f64(Some(10), None), None);
    }

    #[test]
    fn non_finite_terminal_values_are_rejected() {
        assert_eq!(
            validate_terminal_f64(f64::NAN),
            Err(SemanticError::NonFiniteF64)
        );
        assert_eq!(
            validate_terminal_f64(f64::INFINITY),
            Err(SemanticError::NonFiniteF64)
        );
        assert_eq!(validate_terminal_f64(1.25), Ok(1.25));
    }

    #[test]
    fn category_equality_is_semantic_not_dictionary_position() {
        let a = CategoryValue {
            vocabulary_id: 7,
            semantic_code: 42,
        };
        let b = CategoryValue {
            vocabulary_id: 7,
            semantic_code: 42,
        };
        assert_eq!(a, b);
    }
}
