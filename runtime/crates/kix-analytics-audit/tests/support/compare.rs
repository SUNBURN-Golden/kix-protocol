use super::data::*;

pub fn error_category(error: &str) -> &str {
    let lower = error.to_ascii_lowercase();
    if lower.contains("overflow")
        || lower.contains("out of range")
        || lower.contains("conversion from `i128`")
    {
        "OVERFLOW"
    } else {
        error
    }
}
pub fn equivalent(expected: &Outcome, actual: &Outcome, ordered: bool) -> bool {
    match (expected, actual) {
        (Err(a), Err(b)) => error_category(a) == error_category(b),
        (Ok(a), Ok(b)) => {
            let (mut a, mut b) = (a.clone(), b.clone());
            if !ordered {
                a.sort();
                b.sort();
            }
            a == b
        }
        _ => false,
    }
}
