//! Boundary fixtures for the approved boundary types in `kix-types` (fixed-width ids,
//! versioned asset-bound money, typed counters) as used by `kix-bcs1`, `kix-feature-ir`,
//! `kix-kernel-v5` and `kix-delegated-exec`.
//!
//! These are in-memory tests through the public constructors and parsers. They pin both
//! sides of each boundary as it behaves today; they are not a wire, storage, exporter,
//! durability or production result, and they introduce no new semantics. Where the
//! contract is silent the observation is recorded as AGENTS section 8 class B (see
//! `validation/2026-10-21-kix-types-boundary-fixtures/README.md`): `Sequence`,
//! `Version`, `Quantity`, `Generation`, `AdmissionEpoch` and `DurationSeconds` are each
//! bounded at the primitive max, so no in-domain input reaches `CounterOutOfRange` for
//! them.
use kix_types::*;
use std::cmp::Ordering;
use std::collections::HashSet;
use std::hash::{DefaultHasher, Hash, Hasher};

const HEX64: &str = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";

fn hash_of<T: Hash>(value: &T) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

fn check_id<T>(a: T, b: T, a_bytes: &[u8], b_bytes: &[u8])
where
    T: Copy + Eq + Ord + Hash,
{
    assert_eq!(a.cmp(&b), a_bytes.cmp(b_bytes));
    assert_eq!(a == b, a.cmp(&b) == Ordering::Equal);
    let mut set = HashSet::new();
    set.insert(a);
    set.insert(b);
    set.insert(a);
    assert_eq!(set.len(), if a == b { 1 } else { 2 });
    if a == b {
        assert_eq!(hash_of(&a), hash_of(&b));
    }
}

#[test]
fn full_range_counters_accept_zero_and_primitive_max() {
    // Class B (contract undefined): each of these six counters is declared with
    // `counter!(Name, T, T::MAX)`, so the `CounterOutOfRange` guard cannot be reached
    // by any value of the input type; the "max+1" rejection cell is empty. Zero is
    // accepted, unlike `RegistryVersion` and the schema ids which reject it.
    assert_eq!(Sequence::new(0).unwrap().get(), 0);
    assert_eq!(Sequence::new(u64::MAX).unwrap().get(), u64::MAX);
    assert_eq!(Generation::new(0).unwrap().get(), 0);
    assert_eq!(Generation::new(u64::MAX).unwrap().get(), u64::MAX);
    assert_eq!(AdmissionEpoch::new(0).unwrap().get(), 0);
    assert_eq!(AdmissionEpoch::new(u64::MAX).unwrap().get(), u64::MAX);
    assert_eq!(Version::new(0).unwrap().get(), 0);
    assert_eq!(Version::new(u32::MAX).unwrap().get(), u32::MAX);
    assert_eq!(Quantity::new(0).unwrap().get(), 0);
    assert_eq!(Quantity::new(u32::MAX).unwrap().get(), u32::MAX);
    assert_eq!(DurationSeconds::new(0).unwrap().get(), 0);
    assert_eq!(DurationSeconds::new(u32::MAX).unwrap().get(), u32::MAX);
}

#[test]
fn hash32_display_round_trips_lowercase_hex() {
    let mut ascending = [0_u8; 32];
    for (index, byte) in ascending.iter_mut().enumerate() {
        *byte = index as u8;
    }
    for bytes in [ascending, [0xff_u8; 32], [0xa5_u8; 32]] {
        let hash = Hash32::from_bytes(bytes);
        let text = hash.to_string();
        assert_eq!(text.len(), 64);
        assert!(
            text.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)),
            "display emitted non-lowercase-hex: {text}"
        );
        assert_eq!(Hash32::parse_lower_hex(&text), Ok(hash));
    }
}

#[test]
fn hash32_parse_rejects_malformed_lengths_and_case() {
    let rejections = [
        "A".repeat(64),
        format!("{}g", "0".repeat(63)),
        format!("g{}", "0".repeat(63)),
        format!("{}z{}", "0".repeat(32), "0".repeat(31)),
        format!("{}-{}", "0".repeat(32), "0".repeat(31)),
        "0".repeat(63),
        "0".repeat(65),
        String::new(),
    ];
    for input in rejections {
        assert_eq!(
            Hash32::parse_lower_hex(&input),
            Err(TypeError::InvalidHash),
            "input: {input:?}"
        );
    }
    assert_eq!(
        Hash32::parse_lower_hex(HEX64).unwrap().as_bytes(),
        &[0xaa_u8; 32]
    );
}

#[test]
fn legacy_asset_id_rejects_malformed_inputs() {
    // Every decode failure maps to InvalidLegacyAssetId, not InvalidHash.
    let rejections = [
        HEX64.to_string(),
        format!("asset-v1-{HEX64}"),
        format!("ASSET-V2-{HEX64}"),
        format!("asset-v2-{}", HEX64.to_uppercase()),
        format!("asset-v2-{}g", &HEX64[..63]),
        format!("asset-v2-{}", &HEX64[..63]),
        format!("asset-v2-{HEX64}0"),
        "asset-v2-".to_string(),
        format!("xasset-v2-{HEX64}"),
    ];
    for input in rejections {
        assert_eq!(
            AssetId::parse_legacy_asset_v2(&input),
            Err(TypeError::InvalidLegacyAssetId),
            "input: {input:?}"
        );
    }
    assert_eq!(
        AssetId::parse_legacy_asset_v2(&format!("asset-v2-{HEX64}")),
        Ok(AssetId::from_bytes([0xaa_u8; 32]))
    );
}

#[test]
fn asset_amount_checked_at_approved_boundaries() {
    let asset = AssetId::from_bytes([9_u8; 32]);
    let registry_hash = Hash32::from_bytes([5_u8; 32]);
    let version = RegistryVersion::new(7).unwrap();
    let checked = |atoms, approved_max| {
        AssetAmount::checked(asset, atoms, approved_max, version, registry_hash)
    };
    assert_eq!(checked(10_000_000, 10_000_000).unwrap().atoms(), 10_000_000);
    assert_eq!(
        checked(10_000_001, 10_000_000),
        Err(TypeError::AssetAmountOutOfRange)
    );
    assert_eq!(checked(u128::MAX, u128::MAX).unwrap().atoms(), u128::MAX);
    assert_eq!(
        checked(u128::MAX, u128::MAX - 1),
        Err(TypeError::AssetAmountOutOfRange)
    );
    assert_eq!(checked(0, 0).unwrap().atoms(), 0);
}

#[test]
fn byte_array_ids_order_and_hash_consistently() {
    let mut first_diff_16 = [0x20_u8; 16];
    first_diff_16[0] = 0x21;
    let mut last_diff_16 = [0x20_u8; 16];
    last_diff_16[15] = 0x21;
    let mut first_diff_32 = [0x20_u8; 32];
    first_diff_32[0] = 0x21;
    let mut last_diff_32 = [0x20_u8; 32];
    last_diff_32[31] = 0x21;

    let kix_a = KixId::from_bytes([0x20; 16]);
    for b in [
        KixId::from_bytes(first_diff_16),
        KixId::from_bytes(last_diff_16),
        kix_a,
    ] {
        check_id(kix_a, b, kix_a.as_bytes(), b.as_bytes());
    }
    let hash_a = Hash32::from_bytes([0x20; 32]);
    for b in [
        Hash32::from_bytes(first_diff_32),
        Hash32::from_bytes(last_diff_32),
        hash_a,
    ] {
        check_id(hash_a, b, hash_a.as_bytes(), b.as_bytes());
    }
    let asset_a = AssetId::from_bytes([0x20; 32]);
    for b in [
        AssetId::from_bytes(first_diff_32),
        AssetId::from_bytes(last_diff_32),
        asset_a,
    ] {
        check_id(asset_a, b, asset_a.as_bytes(), b.as_bytes());
    }
}

#[test]
fn type_error_display_strings_are_pinned() {
    let cases = [
        (
            TypeError::InvalidLegacyAssetId,
            "invalid legacy asset-v2 text id",
        ),
        (TypeError::InvalidHash, "invalid lowercase SHA-256 hex"),
        (
            TypeError::ZeroRegistryVersion,
            "registry version must be positive",
        ),
        (
            TypeError::ZeroSchemaIdentity,
            "KIX-BCS1 domain/schema/version must be positive",
        ),
        (TypeError::CounterOutOfRange, "typed counter out of range"),
        (
            TypeError::AssetAmountOutOfRange,
            "asset amount exceeds approved maximum",
        ),
    ];
    for (error, expected) in cases {
        assert_eq!(error.to_string(), expected);
    }
    let boxed: Box<dyn std::error::Error> = TypeError::InvalidHash.into();
    assert_eq!(boxed.to_string(), "invalid lowercase SHA-256 hex");
}
