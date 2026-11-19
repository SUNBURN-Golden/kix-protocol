#![forbid(unsafe_code)]
//! Test-only offline analytics audit. No production entrypoint.

#[cfg(all(test, not(feature = "engines")))]
mod tests {
    #[test]
    #[ignore = "CPU/SQL engines require the owner-provisioned offline bundle; run --features engines --test conformance (analytics_audit/README.md)"]
    fn local_engine_acceptance_requires_explicit_feature() {}
}
