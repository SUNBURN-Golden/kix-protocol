//! Scalar edge fixtures for FEATURE_SEMANTICS_V1 helpers.
//!
//! In-memory scalar helpers only: not a wire, exporter, Polars, DuckDB or GPU result, and no
//! f64 tolerance policy or zero normalisation is chosen here. `characterize_*` tests pin today's
//! behaviour where the contract is silent (AGENTS section 8 class B); see
//! `validation/2026-10-17-feature-semantics-v1-edge-fixtures/README.md`.

use kix_feature_semantics::*;
use std::collections::HashSet;
use std::hash::{DefaultHasher, Hash, Hasher};

const BOUNDARY: [i64; 5] = [i64::MIN, -1, 0, 1, i64::MAX];

fn pow2_63() -> f64 {
    (1_u64 << 63) as f64
}

fn cat(vocabulary_id: u32, semantic_code: u32) -> CategoryValue {
    CategoryValue {
        vocabulary_id,
        semantic_code,
    }
}

fn hash_of(value: &CategoryValue) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

#[test]
fn filter_keeps_table_matches_section_2() {
    let rows = [(Some(true), true), (Some(false), false), (None, false)];
    for (predicate, expected) in rows {
        assert_eq!(filter_keeps(predicate), expected, "{predicate:?}");
    }
}

/// Class B: `(false, false)` is `true` under both policies; the helper decides only the null
/// component and never compares key values. The contract does not define the helper's scope.
#[test]
fn nullable_keys_equal_table_covers_all_null_combinations_under_both_policies() {
    let rows = [
        (true, true, NullEquality::Equal, true),
        (true, true, NullEquality::Unequal, false),
        (true, false, NullEquality::Equal, false),
        (true, false, NullEquality::Unequal, false),
        (false, true, NullEquality::Equal, false),
        (false, true, NullEquality::Unequal, false),
        (false, false, NullEquality::Equal, true),
        (false, false, NullEquality::Unequal, true),
    ];
    for (left, right, policy, expected) in rows {
        assert_eq!(
            nullable_keys_equal(left, right, policy),
            expected,
            "left_null={left} right_null={right} {policy:?}"
        );
    }
}

#[test]
fn aggregate_empty_policy_is_exhaustive_over_aggregate_kind() {
    const ALL: [AggregateKind; 5] = [
        AggregateKind::Count,
        AggregateKind::Sum,
        AggregateKind::Min,
        AggregateKind::Max,
        AggregateKind::Mean,
    ];

    // No wildcard arms: adding an AggregateKind variant breaks the build here.
    const fn ordinal(kind: AggregateKind) -> usize {
        match kind {
            AggregateKind::Count => 0,
            AggregateKind::Sum => 1,
            AggregateKind::Min => 2,
            AggregateKind::Max => 3,
            AggregateKind::Mean => 4,
        }
    }
    fn expected(kind: AggregateKind) -> EmptyAggregatePolicy {
        match kind {
            AggregateKind::Count => EmptyAggregatePolicy::Zero,
            AggregateKind::Sum | AggregateKind::Min | AggregateKind::Max | AggregateKind::Mean => {
                EmptyAggregatePolicy::Null
            }
        }
    }

    let ordinals: HashSet<usize> = ALL.iter().map(|k| ordinal(*k)).collect();
    assert_eq!(ordinals.len(), ALL.len(), "ALL must list each kind once");
    for kind in ALL {
        assert_eq!(empty_policy(kind), expected(kind), "{kind:?}");
    }
}

#[test]
fn divide_yields_none_for_zero_or_null_operand() {
    for a in BOUNDARY {
        assert_eq!(divide_i64_to_terminal_f64(Some(a), Some(0)), None, "{a}/0");
        assert_eq!(divide_i64_to_terminal_f64(Some(a), None), None, "{a}/null");
        assert_eq!(divide_i64_to_terminal_f64(None, Some(a)), None, "null/{a}");
    }
    assert_eq!(divide_i64_to_terminal_f64(None, None), None);
}

#[test]
fn divide_matches_independent_f64_expression_over_boundary_set() {
    for n in BOUNDARY {
        for d in BOUNDARY.into_iter().filter(|d| *d != 0) {
            let got = divide_i64_to_terminal_f64(Some(n), Some(d))
                .unwrap_or_else(|| panic!("{n}/{d} must be Some"));
            assert!(got.is_finite(), "{n}/{d}");
            // `==` on purpose: the sign of zero is characterised separately.
            assert_eq!(got, n as f64 / d as f64, "{n}/{d}");
            assert_eq!(validate_terminal_f64(got), Ok(got), "{n}/{d}");
        }
    }
}

#[test]
fn divide_boundary_rows_have_pinned_values() {
    // Class B: i64 -> f64 is lossy above 2^53; i64::MAX as f64 is exactly 2^63.
    assert_eq!(i64::MAX as f64, pow2_63());
    let rows = [
        (i64::MIN, -1, pow2_63()),
        (i64::MAX, i64::MIN, -1.0),
        (i64::MIN, i64::MAX, -1.0),
        (i64::MIN, i64::MIN, 1.0),
        (i64::MAX, i64::MAX, 1.0),
        (i64::MIN, 1, -pow2_63()),
        (i64::MAX, 1, pow2_63()),
        (1, i64::MAX, 1.0 / pow2_63()),
    ];
    for (n, d, expected) in rows {
        assert_eq!(
            divide_i64_to_terminal_f64(Some(n), Some(d)),
            Some(expected),
            "{n}/{d}"
        );
    }
}

/// Class B characterization: 0 divided by a negative denominator is -0.0 (sign bit set). The
/// contract says only "finite plus a versioned tolerance policy"; no normalisation is chosen.
/// Expected to change if a decision adopts one; this is not a contract assertion.
#[test]
fn characterize_zero_over_negative_denominator_is_negative_zero() {
    for d in [-1, i64::MIN] {
        let v = divide_i64_to_terminal_f64(Some(0), Some(d)).expect("nonzero denominator");
        assert_eq!(v, 0.0);
        assert!(v.is_sign_negative(), "0/{d}");
        assert_eq!(v.to_bits(), 0x8000_0000_0000_0000, "0/{d}");
        let validated = validate_terminal_f64(v).expect("finite");
        assert_eq!(validated.to_bits(), v.to_bits());
    }
    for d in [1, i64::MAX] {
        let v = divide_i64_to_terminal_f64(Some(0), Some(d)).expect("nonzero denominator");
        assert_eq!(v.to_bits(), 0, "0/{d}");
    }
}

#[test]
fn validate_terminal_f64_rejects_non_finite_values() {
    let pos_nan = f64::from_bits(0x7ff8_0000_0000_0000);
    let neg_nan = f64::from_bits(0xfff8_0000_0000_0000);
    assert!(pos_nan.is_nan() && pos_nan.is_sign_positive());
    assert!(neg_nan.is_nan() && neg_nan.is_sign_negative());
    for v in [
        pos_nan,
        neg_nan,
        f64::NAN,
        -f64::NAN,
        f64::INFINITY,
        f64::NEG_INFINITY,
    ] {
        assert_eq!(
            validate_terminal_f64(v),
            Err(SemanticError::NonFiniteF64),
            "bits {:#x}",
            v.to_bits()
        );
    }
}

#[test]
fn validate_terminal_f64_accepts_finite_extremes_and_zeros() {
    let subnormal = f64::from_bits(1);
    assert!(subnormal.is_subnormal());
    for v in [f64::MAX, f64::MIN, f64::MIN_POSITIVE, subnormal, 0.0, -0.0] {
        let got = validate_terminal_f64(v).expect("finite value");
        assert_eq!(got.to_bits(), v.to_bits());
    }
}

#[test]
fn category_value_equality_and_hash_ignore_dictionary_position() {
    let values = [cat(7, 42), cat(7, 43), cat(9, 1)];
    let orders: [[usize; 3]; 3] = [[0, 1, 2], [2, 1, 0], [1, 2, 0]];
    let sets: Vec<HashSet<CategoryValue>> = orders
        .iter()
        .map(|order| {
            // Each value inserted twice, as separately constructed duplicates.
            order
                .iter()
                .flat_map(|i| {
                    [
                        values[*i],
                        cat(values[*i].vocabulary_id, values[*i].semantic_code),
                    ]
                })
                .collect()
        })
        .collect();
    for set in &sets {
        assert_eq!(set.len(), 3);
        assert_eq!(*set, sets[0]);
    }
    assert_eq!(cat(7, 42), cat(7, 42));
    assert_eq!(hash_of(&cat(7, 42)), hash_of(&cat(7, 42)));
}

#[test]
fn category_value_differs_by_vocabulary_id_or_semantic_code() {
    let base = cat(7, 42);
    for other in [cat(8, 42), cat(7, 43), cat(42, 7)] {
        assert_ne!(base, other);
    }
    let set: HashSet<CategoryValue> = [base, cat(8, 42), cat(7, 43), cat(42, 7)].into();
    assert_eq!(set.len(), 4);
}
