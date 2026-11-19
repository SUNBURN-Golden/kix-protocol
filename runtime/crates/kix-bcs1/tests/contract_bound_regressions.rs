use kix_bcs1::{
    BoundedUtf8, CodecError, KixBcsSchema, MAX_ENVELOPE_OVERHEAD_BYTES, TEST_VECTOR_DOMAIN_ID,
    TEST_VECTOR_SCHEMA_ID, canonical_bytes, decode_bcs_body, decode_canonical, encode_bcs_body,
};
use serde::{Deserialize, Serialize};

// CANONICAL_BINARY_BCS_V1.md §1 layout and §7 reserved-identity golden prefix.
const PREFIX: [u8; 10] = [0x4b, 0x49, 0x58, 0x31, 0xff, 0xff, 0xff, 0xff, 0x01, 0x00];

fn envelope(body: &[u8]) -> Vec<u8> {
    assert!(body.len() < 0x80, "fixture needs a one-byte ULEB128 length");
    let mut bytes = Vec::from(PREFIX);
    bytes.push(body.len() as u8);
    bytes.extend_from_slice(body);
    bytes
}

#[derive(Debug, PartialEq, Eq)]
struct RawBody<const MAX: usize, const VERSION: u16 = 1>(Vec<u8>);

impl<const MAX: usize, const VERSION: u16> KixBcsSchema for RawBody<MAX, VERSION> {
    const DOMAIN_ID: u16 = TEST_VECTOR_DOMAIN_ID;
    const SCHEMA_ID: u16 = TEST_VECTOR_SCHEMA_ID;
    const SCHEMA_VERSION: u16 = VERSION;
    const MAX_BODY_BYTES: usize = MAX;

    fn encode_body(&self) -> Result<Vec<u8>, CodecError> {
        Ok(self.0.clone())
    }

    fn decode_body(bytes: &[u8]) -> Result<Self, CodecError> {
        Ok(Self(bytes.to_vec()))
    }
}

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
struct Utf8Body {
    label: BoundedUtf8<3>,
}

impl KixBcsSchema for Utf8Body {
    const DOMAIN_ID: u16 = TEST_VECTOR_DOMAIN_ID;
    const SCHEMA_ID: u16 = TEST_VECTOR_SCHEMA_ID;
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
fn fu_zero_id_schema_version_zero_is_rejected() {
    // CANONICAL_BINARY_BCS_V1.md §1 requires a positive schema version.
    let valid_body = RawBody::<16>(vec![]);
    let valid_envelope = envelope(&[]);
    assert_eq!(canonical_bytes(&valid_body).unwrap(), valid_envelope);
    assert_eq!(
        decode_canonical::<RawBody<16>>(&valid_envelope).unwrap(),
        valid_body
    );

    let mut zero_version_envelope = valid_envelope;
    zero_version_envelope[8] = 0;
    let encoded = canonical_bytes(&RawBody::<16, 0>(vec![]));
    let decoded = decode_canonical::<RawBody<16, 0>>(&zero_version_envelope);
    assert!(encoded.is_err(), "encoded a zero-version schema");
    assert!(decoded.is_err(), "decoded a matching zero-version schema");

    // Characterization (AGENTS §8 class B).
    assert_eq!(encoded, Err(CodecError::InvalidSchemaIdentity));
    assert_eq!(decoded, Err(CodecError::InvalidSchemaIdentity));
}

#[test]
fn fu_envelope_too_large_is_rejected_before_bcs_decode() {
    // CANONICAL_BINARY_BCS_V1.md §2 checks the envelope bound before BCS decode.
    let bound = RawBody::<16>::MAX_BODY_BYTES + MAX_ENVELOPE_OVERHEAD_BYTES;
    // The all-0xff fixture has an invalid BCS body length at either size.
    let malformed = vec![0xff; bound + 1];
    let too_large = decode_canonical::<RawBody<16>>(&malformed);
    let at_bound = decode_canonical::<RawBody<16>>(&malformed[..bound]);
    assert!(too_large.is_err(), "accepted an oversized envelope");
    assert!(at_bound.is_err(), "accepted malformed BCS at the bound");

    // Characterization (AGENTS §8 class B). The variants distinguish the guards.
    assert_eq!(too_large, Err(CodecError::EnvelopeTooLarge));
    assert_eq!(at_bound, Err(CodecError::EnvelopeDecode));
}

#[test]
fn fu_body_too_large_encode_is_rejected() {
    // CANONICAL_BINARY_BCS_V1.md §2 names MAX_BODY_BYTES.
    // The encode-side guard and its variant are characterization (AGENTS §8 class B).
    assert!(canonical_bytes(&RawBody::<16>(vec![0; 16])).is_ok());
    let oversized = canonical_bytes(&RawBody::<16>(vec![0; 17]));
    assert!(oversized.is_err(), "encoded a body above MAX_BODY_BYTES");
    assert_eq!(oversized, Err(CodecError::BodyTooLarge));
}

#[test]
fn fu_body_too_large_decode_is_rejected() {
    // CANONICAL_BINARY_BCS_V1.md §2 checks body length after parsing the envelope.
    let at_limit = RawBody::<16>(vec![0; 16]);
    let valid = canonical_bytes(&at_limit).unwrap();
    assert_eq!(decode_canonical::<RawBody<16>>(&valid).unwrap(), at_limit);

    let oversized = envelope(&[0; 17]);
    assert!(oversized.len() <= RawBody::<16>::MAX_BODY_BYTES + MAX_ENVELOPE_OVERHEAD_BYTES);
    let decoded = decode_canonical::<RawBody<16>>(&oversized);
    assert!(decoded.is_err(), "decoded a body above MAX_BODY_BYTES");

    // Characterization (AGENTS §8 class B).
    assert_eq!(decoded, Err(CodecError::BodyTooLarge));
}

#[test]
fn fu_utf8_multibyte_limit_counts_bytes_not_chars() {
    // CANONICAL_BINARY_BCS_V1.md §2 and §8 gate 5 require a UTF-8 byte limit.
    let at_limit = Utf8Body {
        label: BoundedUtf8::try_new("한".to_owned()).unwrap(),
    };
    let valid = canonical_bytes(&at_limit).unwrap();
    assert_eq!(decode_canonical::<Utf8Body>(&valid).unwrap(), at_limit);

    // "한a" has two characters and four UTF-8 bytes, one over the field limit.
    let oversized = "한a";
    let constructed = BoundedUtf8::<3>::try_new(oversized.to_owned());
    let raw_body = encode_bcs_body(&oversized).unwrap();
    let decoded = decode_canonical::<Utf8Body>(&envelope(&raw_body));
    assert!(constructed.is_err(), "constructed an oversized field");
    assert!(decoded.is_err(), "decoded an oversized field");

    // Characterization (AGENTS §8 class B).
    assert_eq!(constructed, Err(CodecError::BoundedUtf8Exceeded));
    assert_eq!(decoded, Err(CodecError::BodyDecode));
}

#[test]
fn fu_truncated_envelope_is_rejected() {
    // CANONICAL_BINARY_BCS_V1.md §8 gate 3 rejects malformed bytes.
    let body = RawBody::<16>(vec![1, 2, 3, 4]);
    let valid = canonical_bytes(&body).unwrap();
    assert_eq!(decode_canonical::<RawBody<16>>(&valid).unwrap(), body);

    for end in [0, 9, valid.len() - 1] {
        let decoded = decode_canonical::<RawBody<16>>(&valid[..end]);
        assert!(
            decoded.is_err(),
            "accepted truncated envelope at {end} bytes"
        );

        // Characterization (AGENTS §8 class B).
        assert_eq!(decoded, Err(CodecError::EnvelopeDecode));
    }
}
