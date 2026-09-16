use kix_bcs1::{
    BoundedUtf8, CodecError, KixBcsSchema, TEST_VECTOR_DOMAIN_ID, TEST_VECTOR_SCHEMA_ID,
    canonical_bytes, canonical_hash, decode_bcs_body, decode_canonical, encode_bcs_body,
};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
struct GoldenBodyV1 {
    id: [u8; 16],
    asset_id: [u8; 32],
    atoms: u128,
    label: BoundedUtf8<8>,
}

impl KixBcsSchema for GoldenBodyV1 {
    const DOMAIN_ID: u16 = TEST_VECTOR_DOMAIN_ID;
    const SCHEMA_ID: u16 = TEST_VECTOR_SCHEMA_ID;
    const SCHEMA_VERSION: u16 = 1;
    const MAX_BODY_BYTES: usize = 128;

    fn encode_body(&self) -> Result<Vec<u8>, CodecError> {
        encode_bcs_body(self)
    }

    fn decode_body(bytes: &[u8]) -> Result<Self, CodecError> {
        decode_bcs_body(bytes)
    }
}

const EXPECTED_BYTES: [u8; 79] = [
    0x4b, 0x49, 0x58, 0x31, 0xff, 0xff, 0xff, 0xff, 0x01, 0x00, 0x44, 0x00, 0x01, 0x02, 0x03, 0x04,
    0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0xa0, 0xa1, 0xa2, 0xa3, 0xa4,
    0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf, 0xb0, 0xb1, 0xb2, 0xb3, 0xb4,
    0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x03, 0x6b, 0x69, 0x78,
];

const EXPECTED_HASH: [u8; 32] = [
    0x36, 0x68, 0xb9, 0x84, 0x57, 0x1c, 0x93, 0xa7, 0x1c, 0x3a, 0x61, 0x8a, 0x65, 0x30, 0x5f, 0xef,
    0x53, 0x21, 0x51, 0x5a, 0x72, 0x53, 0xcb, 0x88, 0x5f, 0xfb, 0xae, 0x6e, 0x4b, 0x3b, 0xfe, 0x09,
];

fn golden() -> GoldenBodyV1 {
    GoldenBodyV1 {
        id: core::array::from_fn(|i| i as u8),
        asset_id: core::array::from_fn(|i| 0xa0 + i as u8),
        atoms: u128::MAX,
        label: BoundedUtf8::try_new("kix".to_owned()).unwrap(),
    }
}

#[test]
fn fixed_bytes_and_hash_match_external_golden_values() {
    let value = golden();
    let bytes = canonical_bytes(&value).unwrap();
    let hash = canonical_hash(&value).unwrap();

    assert_eq!(bytes, EXPECTED_BYTES);
    assert_eq!(hash.as_bytes(), &EXPECTED_HASH);
    assert_eq!(decode_canonical::<GoldenBodyV1>(&bytes).unwrap(), value);
}

#[test]
fn u128_zero_and_max_are_lossless() {
    let mut value = golden();
    value.atoms = 0;
    let zero = canonical_bytes(&value).unwrap();
    assert_eq!(decode_canonical::<GoldenBodyV1>(&zero).unwrap().atoms, 0);

    let max = canonical_bytes(&golden()).unwrap();
    assert_eq!(
        decode_canonical::<GoldenBodyV1>(&max).unwrap().atoms,
        u128::MAX
    );
}

#[test]
fn domain_schema_and_version_are_bound() {
    let bytes = canonical_bytes(&golden()).unwrap();

    let mut wrong_domain = bytes.clone();
    wrong_domain[4] ^= 0x01;
    assert_eq!(
        decode_canonical::<GoldenBodyV1>(&wrong_domain),
        Err(CodecError::SchemaMismatch)
    );

    let mut wrong_schema = bytes.clone();
    wrong_schema[6] ^= 0x01;
    assert_eq!(
        decode_canonical::<GoldenBodyV1>(&wrong_schema),
        Err(CodecError::SchemaMismatch)
    );

    let mut wrong_version = bytes;
    wrong_version[8] ^= 0x01;
    assert_eq!(
        decode_canonical::<GoldenBodyV1>(&wrong_version),
        Err(CodecError::SchemaMismatch)
    );
}

#[test]
fn legacy_json_is_not_kix_bcs1_identity() {
    let legacy_ce1_like =
        br#"{"schema":"kix:commerce:2","atoms":"340282366920938463463374607431768211455"}"#;
    let bytes = canonical_bytes(&golden()).unwrap();
    assert_ne!(bytes.as_slice(), legacy_ce1_like);
    assert_ne!(
        kix_bcs1::canonical_hash_bytes(legacy_ce1_like),
        canonical_hash(&golden()).unwrap()
    );
}
