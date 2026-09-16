#![forbid(unsafe_code)]
//! Fixed-width production boundary types for KIX S07+.
//!
//! This crate is intentionally zero-dependency and I/O-free. Production identity
//! is binary-first: KIX-generated IDs are 128-bit, asset/content identities are
//! 256-bit, money keeps asset+registry context, and KIX-BCS1 schema/domain fields
//! are distinct types. Legacy CE1/text parsing is compatibility-only.

use core::fmt;

pub const KIX_BCS1_MAGIC: [u8; 4] = *b"KIX1";
pub const LEGACY_ASSET_ID_PREFIX: &str = "asset-v2-";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TypeError {
    InvalidLegacyAssetId,
    InvalidHash,
    ZeroRegistryVersion,
    ZeroSchemaIdentity,
    CounterOutOfRange,
    AssetAmountOutOfRange,
}

impl fmt::Display for TypeError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::InvalidLegacyAssetId => "invalid legacy asset-v2 text id",
            Self::InvalidHash => "invalid lowercase SHA-256 hex",
            Self::ZeroRegistryVersion => "registry version must be positive",
            Self::ZeroSchemaIdentity => "KIX-BCS1 domain/schema/version must be positive",
            Self::CounterOutOfRange => "typed counter out of range",
            Self::AssetAmountOutOfRange => "asset amount exceeds approved maximum",
        })
    }
}

impl std::error::Error for TypeError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct KixId([u8; 16]);

impl KixId {
    pub const fn from_bytes(value: [u8; 16]) -> Self {
        Self(value)
    }

    pub const fn as_bytes(&self) -> &[u8; 16] {
        &self.0
    }
}

fn decode_lower_hex_32(value: &str) -> Result<[u8; 32], TypeError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err(TypeError::InvalidHash);
    }
    let mut out = [0_u8; 32];
    let bytes = value.as_bytes();
    for (index, slot) in out.iter_mut().enumerate() {
        let hi = hex_nibble(bytes[index * 2]);
        let lo = hex_nibble(bytes[index * 2 + 1]);
        *slot = (hi << 4) | lo;
    }
    Ok(out)
}

fn hex_nibble(byte: u8) -> u8 {
    match byte {
        b'0'..=b'9' => byte - b'0',
        b'a'..=b'f' => byte - b'a' + 10,
        _ => unreachable!("validated lowercase hex"),
    }
}

fn write_lower_hex(bytes: &[u8; 32], f: &mut fmt::Formatter<'_>) -> fmt::Result {
    for byte in bytes {
        write!(f, "{byte:02x}")?;
    }
    Ok(())
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Hash32([u8; 32]);

impl Hash32 {
    pub const fn from_bytes(value: [u8; 32]) -> Self {
        Self(value)
    }

    pub const fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    /// Compatibility/debug boundary only. Production KIX-BCS1 carries bytes.
    pub fn parse_lower_hex(value: &str) -> Result<Self, TypeError> {
        Ok(Self(decode_lower_hex_32(value)?))
    }
}

impl fmt::Display for Hash32 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write_lower_hex(&self.0, f)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct AssetId([u8; 32]);

impl AssetId {
    pub const fn from_bytes(value: [u8; 32]) -> Self {
        Self(value)
    }

    pub const fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    /// Compatibility with S06.1 text IDs. Never the production canonical form.
    pub fn parse_legacy_asset_v2(value: &str) -> Result<Self, TypeError> {
        let digest = value
            .strip_prefix(LEGACY_ASSET_ID_PREFIX)
            .ok_or(TypeError::InvalidLegacyAssetId)?;
        decode_lower_hex_32(digest)
            .map(Self)
            .map_err(|_| TypeError::InvalidLegacyAssetId)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct RegistryVersion(u32);

impl RegistryVersion {
    pub fn new(value: u32) -> Result<Self, TypeError> {
        if value == 0 {
            return Err(TypeError::ZeroRegistryVersion);
        }
        Ok(Self(value))
    }

    pub const fn get(self) -> u32 {
        self.0
    }
}

macro_rules! positive_u16_id {
    ($name:ident) => {
        #[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
        pub struct $name(u16);

        impl $name {
            pub fn new(value: u16) -> Result<Self, TypeError> {
                if value == 0 {
                    return Err(TypeError::ZeroSchemaIdentity);
                }
                Ok(Self(value))
            }

            pub const fn get(self) -> u16 {
                self.0
            }
        }
    };
}

positive_u16_id!(DomainId);
positive_u16_id!(SchemaId);
positive_u16_id!(SchemaVersion);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct KixBcs1Header {
    magic: [u8; 4],
    domain_id: DomainId,
    schema_id: SchemaId,
    schema_version: SchemaVersion,
}

impl KixBcs1Header {
    pub const fn new(
        domain_id: DomainId,
        schema_id: SchemaId,
        schema_version: SchemaVersion,
    ) -> Self {
        Self {
            magic: KIX_BCS1_MAGIC,
            domain_id,
            schema_id,
            schema_version,
        }
    }

    pub const fn magic(self) -> [u8; 4] {
        self.magic
    }

    pub const fn domain_id(self) -> DomainId {
        self.domain_id
    }

    pub const fn schema_id(self) -> SchemaId {
        self.schema_id
    }

    pub const fn schema_version(self) -> SchemaVersion {
        self.schema_version
    }
}

macro_rules! counter {
    ($name:ident, $inner:ty, $max:expr) => {
        #[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
        pub struct $name($inner);

        impl $name {
            pub fn new(value: $inner) -> Result<Self, TypeError> {
                if value > $max {
                    return Err(TypeError::CounterOutOfRange);
                }
                Ok(Self(value))
            }

            pub const fn get(self) -> $inner {
                self.0
            }
        }
    };
}

counter!(TimestampMs, u64, i64::MAX as u64);
counter!(Sequence, u64, u64::MAX);
counter!(Version, u32, u32::MAX);
counter!(Quantity, u32, u32::MAX);
counter!(Generation, u64, u64::MAX);
counter!(AdmissionEpoch, u64, u64::MAX);
counter!(DurationSeconds, u32, u32::MAX);
counter!(BasisPoints, u16, 10_000_u16);

/// Money remains inseparable from asset and registry identity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct AssetAmount {
    asset_id: AssetId,
    atoms: u128,
    registry_version: RegistryVersion,
    registry_hash: Hash32,
}

impl AssetAmount {
    pub fn checked(
        asset_id: AssetId,
        atoms: u128,
        approved_max_atoms: u128,
        registry_version: RegistryVersion,
        registry_hash: Hash32,
    ) -> Result<Self, TypeError> {
        if atoms > approved_max_atoms {
            return Err(TypeError::AssetAmountOutOfRange);
        }
        Ok(Self {
            asset_id,
            atoms,
            registry_version,
            registry_hash,
        })
    }

    pub const fn asset_id(self) -> AssetId {
        self.asset_id
    }

    pub const fn atoms(self) -> u128 {
        self.atoms
    }

    pub const fn registry_version(self) -> RegistryVersion {
        self.registry_version
    }

    pub const fn registry_hash(self) -> Hash32 {
        self.registry_hash
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const ZERO_HASH: &str = "0000000000000000000000000000000000000000000000000000000000000000";
    const LEGACY_ASSET: &str =
        "asset-v2-0000000000000000000000000000000000000000000000000000000000000000";

    #[test]
    fn production_id_is_fixed_128_bits() {
        let id = KixId::from_bytes([7_u8; 16]);
        assert_eq!(id.as_bytes(), &[7_u8; 16]);
    }

    #[test]
    fn asset_identity_is_binary_first() {
        let asset = AssetId::from_bytes([3_u8; 32]);
        assert_eq!(asset.as_bytes(), &[3_u8; 32]);
        let legacy = AssetId::parse_legacy_asset_v2(LEGACY_ASSET).unwrap();
        assert_eq!(legacy.as_bytes(), &[0_u8; 32]);
        assert_eq!(
            AssetId::parse_legacy_asset_v2(&LEGACY_ASSET.to_uppercase()),
            Err(TypeError::InvalidLegacyAssetId)
        );
    }

    #[test]
    fn hash_parser_is_compatibility_only_and_strict() {
        assert!(Hash32::parse_lower_hex(ZERO_HASH).is_ok());
        assert_eq!(
            Hash32::parse_lower_hex(&"A".repeat(64)),
            Err(TypeError::InvalidHash)
        );
        assert_eq!(Hash32::parse_lower_hex("00"), Err(TypeError::InvalidHash));
    }

    #[test]
    fn bcs_header_types_cannot_be_zero() {
        assert_eq!(DomainId::new(0), Err(TypeError::ZeroSchemaIdentity));
        assert_eq!(SchemaId::new(0), Err(TypeError::ZeroSchemaIdentity));
        assert_eq!(SchemaVersion::new(0), Err(TypeError::ZeroSchemaIdentity));
        let header = KixBcs1Header::new(
            DomainId::new(1).unwrap(),
            SchemaId::new(2).unwrap(),
            SchemaVersion::new(3).unwrap(),
        );
        assert_eq!(header.magic(), KIX_BCS1_MAGIC);
        assert_eq!(header.domain_id().get(), 1);
        assert_eq!(header.schema_id().get(), 2);
        assert_eq!(header.schema_version().get(), 3);
    }

    #[test]
    fn semantic_integer_types_keep_distinct_ranges() {
        assert_eq!(
            TimestampMs::new(i64::MAX as u64).unwrap().get(),
            i64::MAX as u64
        );
        assert_eq!(
            TimestampMs::new(i64::MAX as u64 + 1),
            Err(TypeError::CounterOutOfRange)
        );
        assert_eq!(BasisPoints::new(10_000).unwrap().get(), 10_000);
        assert_eq!(BasisPoints::new(10_001), Err(TypeError::CounterOutOfRange));
        assert_eq!(RegistryVersion::new(0), Err(TypeError::ZeroRegistryVersion));
    }

    #[test]
    fn amount_cannot_lose_asset_or_registry_context() {
        let asset = AssetId::from_bytes([9_u8; 32]);
        let registry_hash = Hash32::from_bytes([5_u8; 32]);
        let version = RegistryVersion::new(7).unwrap();
        let amount =
            AssetAmount::checked(asset, 1_000_000, 10_000_000, version, registry_hash).unwrap();
        assert_eq!(amount.asset_id(), asset);
        assert_eq!(amount.atoms(), 1_000_000);
        assert_eq!(amount.registry_version(), version);
        assert_eq!(amount.registry_hash(), registry_hash);
        assert_eq!(
            AssetAmount::checked(asset, 10_000_001, 10_000_000, version, registry_hash),
            Err(TypeError::AssetAmountOutOfRange)
        );
    }
}
