#![forbid(unsafe_code)]
//! Typed KIX-BCS1 canonical envelope codec.
//!
//! Callers never supply domain/schema/version at encode/decode time. Each body
//! type implements [`KixBcsSchema`] and permanently binds those identifiers.
//! This prevents schema-confusion and downgrade-style caller negotiation.

use core::fmt;
use serde::de::{DeserializeOwned, Error as _};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use sha2::{Digest, Sha256};

use kix_types::{Hash32, KIX_BCS1_MAGIC};

pub const MAX_ENVELOPE_OVERHEAD_BYTES: usize = 32;
pub const TEST_VECTOR_DOMAIN_ID: u16 = u16::MAX;
pub const TEST_VECTOR_SCHEMA_ID: u16 = u16::MAX;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CodecError {
    InvalidSchemaIdentity,
    BodyEncode,
    BodyDecode,
    EnvelopeEncode,
    EnvelopeDecode,
    EnvelopeTooLarge,
    BodyTooLarge,
    MagicMismatch,
    SchemaMismatch,
    BoundedUtf8Exceeded,
}

impl fmt::Display for CodecError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::InvalidSchemaIdentity => "KIX-BCS1 domain/schema/version must be non-zero",
            Self::BodyEncode => "failed to BCS-encode schema body",
            Self::BodyDecode => "failed to BCS-decode schema body",
            Self::EnvelopeEncode => "failed to BCS-encode KIX-BCS1 envelope",
            Self::EnvelopeDecode => "failed to BCS-decode KIX-BCS1 envelope",
            Self::EnvelopeTooLarge => "KIX-BCS1 envelope exceeds schema bound",
            Self::BodyTooLarge => "KIX-BCS1 body exceeds schema bound",
            Self::MagicMismatch => "KIX-BCS1 magic mismatch",
            Self::SchemaMismatch => "KIX-BCS1 domain/schema/version mismatch",
            Self::BoundedUtf8Exceeded => "bounded UTF-8 value exceeds byte limit",
        })
    }
}

impl std::error::Error for CodecError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SchemaDescriptor {
    pub domain_id: u16,
    pub schema_id: u16,
    pub schema_version: u16,
    pub max_body_bytes: usize,
}

impl SchemaDescriptor {
    pub fn of<T: KixBcsSchema>() -> Result<Self, CodecError> {
        if T::DOMAIN_ID == 0 || T::SCHEMA_ID == 0 || T::SCHEMA_VERSION == 0 {
            return Err(CodecError::InvalidSchemaIdentity);
        }
        Ok(Self {
            domain_id: T::DOMAIN_ID,
            schema_id: T::SCHEMA_ID,
            schema_version: T::SCHEMA_VERSION,
            max_body_bytes: T::MAX_BODY_BYTES,
        })
    }

    fn max_envelope_bytes(self) -> usize {
        self.max_body_bytes
            .saturating_add(MAX_ENVELOPE_OVERHEAD_BYTES)
    }
}

/// A production schema owns its KIX-BCS1 identity and body validation.
///
/// Implementations should normally use [`encode_bcs_body`] and
/// [`decode_bcs_body`] over a schema-specific wire struct, then validate/convert
/// into domain types before returning from `decode_body`.
pub trait KixBcsSchema: Sized {
    const DOMAIN_ID: u16;
    const SCHEMA_ID: u16;
    const SCHEMA_VERSION: u16;
    const MAX_BODY_BYTES: usize;

    fn encode_body(&self) -> Result<Vec<u8>, CodecError>;
    fn decode_body(bytes: &[u8]) -> Result<Self, CodecError>;
}

#[derive(Debug, Serialize, Deserialize)]
struct WireEnvelopeV1 {
    magic: [u8; 4],
    domain_id: u16,
    schema_id: u16,
    schema_version: u16,
    body: Vec<u8>,
}

pub fn encode_bcs_body<T: Serialize>(value: &T) -> Result<Vec<u8>, CodecError> {
    bcs::to_bytes(value).map_err(|_| CodecError::BodyEncode)
}

pub fn decode_bcs_body<T: DeserializeOwned>(bytes: &[u8]) -> Result<T, CodecError> {
    bcs::from_bytes(bytes).map_err(|_| CodecError::BodyDecode)
}

pub fn canonical_bytes<T: KixBcsSchema>(value: &T) -> Result<Vec<u8>, CodecError> {
    let descriptor = SchemaDescriptor::of::<T>()?;
    let body = value.encode_body()?;
    if body.len() > descriptor.max_body_bytes {
        return Err(CodecError::BodyTooLarge);
    }

    let envelope = WireEnvelopeV1 {
        magic: KIX_BCS1_MAGIC,
        domain_id: descriptor.domain_id,
        schema_id: descriptor.schema_id,
        schema_version: descriptor.schema_version,
        body,
    };
    let bytes = bcs::to_bytes(&envelope).map_err(|_| CodecError::EnvelopeEncode)?;
    if bytes.len() > descriptor.max_envelope_bytes() {
        return Err(CodecError::EnvelopeTooLarge);
    }
    Ok(bytes)
}

pub fn decode_canonical<T: KixBcsSchema>(bytes: &[u8]) -> Result<T, CodecError> {
    let descriptor = SchemaDescriptor::of::<T>()?;
    if bytes.len() > descriptor.max_envelope_bytes() {
        return Err(CodecError::EnvelopeTooLarge);
    }

    let envelope: WireEnvelopeV1 =
        bcs::from_bytes(bytes).map_err(|_| CodecError::EnvelopeDecode)?;
    if envelope.magic != KIX_BCS1_MAGIC {
        return Err(CodecError::MagicMismatch);
    }
    if envelope.domain_id != descriptor.domain_id
        || envelope.schema_id != descriptor.schema_id
        || envelope.schema_version != descriptor.schema_version
    {
        return Err(CodecError::SchemaMismatch);
    }
    if envelope.body.len() > descriptor.max_body_bytes {
        return Err(CodecError::BodyTooLarge);
    }
    T::decode_body(&envelope.body)
}

pub fn canonical_hash_bytes(bytes: &[u8]) -> Hash32 {
    let digest = Sha256::digest(bytes);
    let mut out = [0_u8; 32];
    out.copy_from_slice(&digest);
    Hash32::from_bytes(out)
}

pub fn canonical_hash<T: KixBcsSchema>(value: &T) -> Result<Hash32, CodecError> {
    let bytes = canonical_bytes(value)?;
    Ok(canonical_hash_bytes(&bytes))
}

pub fn canonical_bytes_and_hash<T: KixBcsSchema>(
    value: &T,
) -> Result<(Vec<u8>, Hash32), CodecError> {
    let bytes = canonical_bytes(value)?;
    let hash = canonical_hash_bytes(&bytes);
    Ok((bytes, hash))
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct BoundedUtf8<const MAX_BYTES: usize>(String);

impl<const MAX_BYTES: usize> BoundedUtf8<MAX_BYTES> {
    pub fn try_new(value: String) -> Result<Self, CodecError> {
        if value.len() > MAX_BYTES {
            return Err(CodecError::BoundedUtf8Exceeded);
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl<const MAX_BYTES: usize> Serialize for BoundedUtf8<MAX_BYTES> {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.0)
    }
}

impl<'de, const MAX_BYTES: usize> Deserialize<'de> for BoundedUtf8<MAX_BYTES> {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let value = String::deserialize(deserializer)?;
        if value.len() > MAX_BYTES {
            return Err(D::Error::custom("bounded UTF-8 byte limit exceeded"));
        }
        Ok(Self(value))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
    struct SmallBody {
        value: u64,
    }

    impl KixBcsSchema for SmallBody {
        const DOMAIN_ID: u16 = 1;
        const SCHEMA_ID: u16 = 1;
        const SCHEMA_VERSION: u16 = 1;
        const MAX_BODY_BYTES: usize = 16;

        fn encode_body(&self) -> Result<Vec<u8>, CodecError> {
            encode_bcs_body(self)
        }

        fn decode_body(bytes: &[u8]) -> Result<Self, CodecError> {
            decode_bcs_body(bytes)
        }
    }

    #[test]
    fn round_trip_and_hash_are_deterministic() {
        let value = SmallBody { value: 42 };
        let bytes_a = canonical_bytes(&value).unwrap();
        let bytes_b = canonical_bytes(&value).unwrap();
        assert_eq!(bytes_a, bytes_b);
        assert_eq!(decode_canonical::<SmallBody>(&bytes_a).unwrap(), value);
        assert_eq!(
            canonical_hash(&value).unwrap(),
            canonical_hash_bytes(&bytes_a)
        );
    }

    #[test]
    fn wrong_magic_schema_version_and_trailing_bytes_are_rejected() {
        let value = SmallBody { value: 42 };
        let bytes = canonical_bytes(&value).unwrap();

        let mut wrong_magic = bytes.clone();
        wrong_magic[0] ^= 0x01;
        assert_eq!(
            decode_canonical::<SmallBody>(&wrong_magic),
            Err(CodecError::MagicMismatch)
        );

        let mut wrong_schema = bytes.clone();
        wrong_schema[6] ^= 0x01;
        assert_eq!(
            decode_canonical::<SmallBody>(&wrong_schema),
            Err(CodecError::SchemaMismatch)
        );

        let mut wrong_version = bytes.clone();
        wrong_version[8] ^= 0x01;
        assert_eq!(
            decode_canonical::<SmallBody>(&wrong_version),
            Err(CodecError::SchemaMismatch)
        );

        let mut trailing = bytes;
        trailing.push(0);
        assert_eq!(
            decode_canonical::<SmallBody>(&trailing),
            Err(CodecError::EnvelopeDecode)
        );
    }

    #[test]
    fn bounded_utf8_rejects_oversize_values() {
        assert!(BoundedUtf8::<3>::try_new("kix".to_owned()).is_ok());
        assert_eq!(
            BoundedUtf8::<3>::try_new("kix!".to_owned()),
            Err(CodecError::BoundedUtf8Exceeded)
        );

        let raw = bcs::to_bytes(&"kix!".to_owned()).unwrap();
        assert_eq!(
            decode_bcs_body::<BoundedUtf8<3>>(&raw),
            Err(CodecError::BodyDecode)
        );
    }
}
