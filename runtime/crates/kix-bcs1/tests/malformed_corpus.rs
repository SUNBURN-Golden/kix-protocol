// Malformed-input boundary corpus for the KIX-BCS1 envelope codec.
//
// Covers the malformed side of the capability-register EV-BCS gap
// ("malformed/mixed-schema 독립 corpus" under "protocol canonical identity
// conformance"). Every case asserts the specific `CodecError` that
// `runtime/CANONICAL_BINARY_BCS_V1.md` implies for the mutated input; contract
// predicates are cited per test. Corpus inputs are derived from the contract
// §7 golden bytes as a fixed external constant, not re-encoded output.
//
// Non-claims: this corpus is contract/source-informed, not clean-room or
// mixed-client evidence. Independent Rust/TS/Move tuple conformance stays with
// the schema/SDK conformance work item.

use kix_bcs1::{
    BoundedUtf8, CodecError, KixBcsSchema, TEST_VECTOR_DOMAIN_ID, TEST_VECTOR_SCHEMA_ID,
    canonical_bytes, decode_bcs_body, decode_canonical, encode_bcs_body,
};
use serde::{Deserialize, Serialize};

// Contract §7 fixed canonical bytes for the 65535/65535 test-vector schema.
// Layout: 0..4 magic "KIX1", 4..6 domain u16, 6..8 schema u16, 8..10 version
// u16, 10 body length ULEB128 (0x44 = 68), 11..79 body (id 11..27,
// asset_id 27..59, atoms 59..75, label length 75, label 76..79).
const GOLDEN: [u8; 79] = [
    0x4b, 0x49, 0x58, 0x31, 0xff, 0xff, 0xff, 0xff, 0x01, 0x00, 0x44, 0x00, 0x01, 0x02, 0x03, 0x04,
    0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0xa0, 0xa1, 0xa2, 0xa3, 0xa4,
    0xa5, 0xa6, 0xa7, 0xa8, 0xa9, 0xaa, 0xab, 0xac, 0xad, 0xae, 0xaf, 0xb0, 0xb1, 0xb2, 0xb3, 0xb4,
    0xb5, 0xb6, 0xb7, 0xb8, 0xb9, 0xba, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x03, 0x6b, 0x69, 0x78,
];

#[derive(Debug, PartialEq, Serialize, Deserialize)]
struct CorpusBodyV1 {
    id: [u8; 16],
    asset_id: [u8; 32],
    atoms: u128,
    label: BoundedUtf8<8>,
}

impl KixBcsSchema for CorpusBodyV1 {
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

// Envelope cap for CorpusBodyV1: 128 body + 32 overhead = 160 bytes.

fn uleb(len: usize) -> Vec<u8> {
    assert!(len < 1 << 14);
    let mut out = vec![(len & 0x7f) as u8];
    if len >= 1 << 7 {
        out[0] |= 0x80;
        out.push((len >> 7) as u8);
    }
    out
}

fn envelope_with_body(body: &[u8]) -> Vec<u8> {
    let mut bytes = GOLDEN[..10].to_vec();
    bytes.extend_from_slice(&uleb(body.len()));
    bytes.extend_from_slice(body);
    bytes
}

fn mutate(offset: usize, f: impl Fn(&mut u8)) -> Vec<u8> {
    let mut bytes = GOLDEN.to_vec();
    f(&mut bytes[offset]);
    bytes
}

// Contract §8 item 3 + §2 decode bound: every proper prefix of the golden
// envelope fails inside envelope decoding (short header or declared body
// length beyond available bytes).
#[test]
fn every_truncated_prefix_is_envelope_decode() {
    assert!(decode_canonical::<CorpusBodyV1>(&GOLDEN).is_ok());
    for k in 0..GOLDEN.len() {
        assert_eq!(
            decode_canonical::<CorpusBodyV1>(&GOLDEN[..k]),
            Err(CodecError::EnvelopeDecode),
            "prefix length {k}"
        );
    }
}

// Contract §8 item 3: extra bytes after a complete frame are rejected while
// the envelope is still inside the schema cap.
#[test]
fn trailing_bytes_after_valid_frame_are_envelope_decode() {
    for extra in 1..=2 {
        let mut bytes = GOLDEN.to_vec();
        bytes.extend(std::iter::repeat_n(0, extra));
        assert_eq!(
            decode_canonical::<CorpusBodyV1>(&bytes),
            Err(CodecError::EnvelopeDecode),
            "{extra} trailing byte(s)"
        );
    }
}

// Contract §2: the whole-envelope length is checked against the schema bound
// before BCS decoding, so an over-cap input is EnvelopeTooLarge even when its
// tail would otherwise be a trailing-bytes violation.
#[test]
fn envelope_cap_fires_before_trailing_rejection() {
    let mut bytes = GOLDEN.to_vec();
    bytes.extend(std::iter::repeat_n(0, 82)); // 161 bytes > 160 cap
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&bytes),
        Err(CodecError::EnvelopeTooLarge)
    );
}

// Contract §2: body length is checked against MAX_BODY_BYTES after envelope
// decode; the bound is inclusive (128 passes the bound and fails later in
// body decode, 129 is BodyTooLarge).
#[test]
fn body_bound_is_inclusive_at_max_body_bytes() {
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&envelope_with_body(&[0; 128])),
        Err(CodecError::BodyDecode)
    );
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&envelope_with_body(&[0; 129])),
        Err(CodecError::BodyTooLarge)
    );
}

// Contract §2: the envelope-length bound is exclusive of the cap value —
// exactly 160 bytes reaches the body-length check, 161 is EnvelopeTooLarge.
#[test]
fn envelope_cap_boundary() {
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&envelope_with_body(&[0; 148])), // 160 total
        Err(CodecError::BodyTooLarge)
    );
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&envelope_with_body(&[0; 149])), // 161 total
        Err(CodecError::EnvelopeTooLarge)
    );
}

// Contract §8 item 2: magic mutations are rejected after envelope decode.
#[test]
fn wrong_magic_bytes_are_magic_mismatch() {
    for offset in 0..4 {
        assert_eq!(
            decode_canonical::<CorpusBodyV1>(&mutate(offset, |b| *b ^= 0x01)),
            Err(CodecError::MagicMismatch),
            "magic offset {offset}"
        );
    }
    let mut zero_magic = GOLDEN.to_vec();
    zero_magic[..4].fill(0);
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&zero_magic),
        Err(CodecError::MagicMismatch)
    );
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&mutate(3, |b| *b = b'2')), // "KIX2"
        Err(CodecError::MagicMismatch)
    );
}

// Contract §8 item 2 + §2 (no caller negotiation): any deviation in the
// bound domain/schema/version triple is SchemaMismatch, including the
// all-zero identity that would be invalid as a descriptor.
#[test]
fn domain_schema_version_mutations_are_schema_mismatch() {
    for offset in 4..10 {
        assert_eq!(
            decode_canonical::<CorpusBodyV1>(&mutate(offset, |b| *b ^= 0x01)),
            Err(CodecError::SchemaMismatch),
            "identity offset {offset}"
        );
    }
    for pair in [0..2, 2..4, 4..6] {
        let mut bytes = GOLDEN.to_vec();
        bytes[4 + pair.start..4 + pair.end].fill(0);
        assert_eq!(
            decode_canonical::<CorpusBodyV1>(&bytes),
            Err(CodecError::SchemaMismatch),
            "zeroed identity field at {}",
            4 + pair.start
        );
    }
}

// Contract §8 item 3: non-canonical or overflowing length prefixes are
// malformed input at the envelope layer.
#[test]
fn malformed_envelope_length_prefixes_are_envelope_decode() {
    // Overlong two-byte encoding of the canonical 68.
    let mut overlong = GOLDEN[..10].to_vec();
    overlong.extend_from_slice(&[0xc4, 0x00]);
    overlong.extend_from_slice(&GOLDEN[11..]);
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&overlong),
        Err(CodecError::EnvelopeDecode)
    );

    for prefix in [
        vec![0xff, 0xff, 0xff, 0xff, 0x7f], // exceeds u32
        vec![0xff, 0xff, 0xff, 0xff, 0x0f], // u32::MAX > BCS MAX_SEQUENCE_LENGTH
        vec![0xff, 0xff, 0xff, 0xff, 0xff], // unterminated past the u32 range
        vec![0x7f],                         // declares 127 body bytes, 68 follow
    ] {
        let mut bytes = GOLDEN[..10].to_vec();
        bytes.extend_from_slice(&prefix);
        bytes.extend_from_slice(&GOLDEN[11..]);
        assert_eq!(
            decode_canonical::<CorpusBodyV1>(&bytes),
            Err(CodecError::EnvelopeDecode),
            "prefix {prefix:?}"
        );
    }
}

// Contract §8 item 3: the same non-canonical length encoding inside the body
// surfaces at the body layer instead.
#[test]
fn overlong_body_length_prefix_is_body_decode() {
    let mut bytes = GOLDEN[..10].to_vec();
    bytes.push(0x45); // body length grows by one inserted byte
    bytes.extend_from_slice(&GOLDEN[11..75]);
    bytes.extend_from_slice(&[0x83, 0x00]); // overlong encoding of label length 3
    bytes.extend_from_slice(&GOLDEN[76..]);
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&bytes),
        Err(CodecError::BodyDecode)
    );
}

// Contract §8 item 5 + §2 BoundedUtf8 decode bound: invalid UTF-8 bytes in
// the label are a body decode failure.
#[test]
fn invalid_utf8_label_is_body_decode() {
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&mutate(78, |b| *b = 0xff)),
        Err(CodecError::BodyDecode)
    );
}

// Contract §8 item 5 + §2: the BoundedUtf8 byte limit is enforced on both
// sides — a declared over-limit label fails body decode, and constructing an
// over-limit value for encoding fails with BoundedUtf8Exceeded.
#[test]
fn over_limit_bounded_utf8_is_rejected() {
    let mut bytes = GOLDEN[..10].to_vec();
    bytes.push(0x4a); // body length 74
    bytes.extend_from_slice(&GOLDEN[11..75]);
    bytes.push(0x09); // label length 9 > BoundedUtf8<8>
    bytes.extend_from_slice(b"123456789");
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&bytes),
        Err(CodecError::BodyDecode)
    );
    assert_eq!(
        BoundedUtf8::<8>::try_new("123456789".to_owned()),
        Err(CodecError::BoundedUtf8Exceeded)
    );
}

// Contract §3 fixed-width types + §8 item 3: a body cut inside a fixed-width
// field, or carrying bytes past the last field, fails body decode.
#[test]
fn wrong_fixed_width_body_lengths_are_body_decode() {
    // 15 bytes: cuts inside id[16].
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&envelope_with_body(&GOLDEN[11..26])),
        Err(CodecError::BodyDecode)
    );
    // 47 bytes: id complete, asset_id one byte short.
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&envelope_with_body(&GOLDEN[11..58])),
        Err(CodecError::BodyDecode)
    );
    // 69 bytes: complete golden body plus one byte past the last field.
    let mut body = GOLDEN[11..].to_vec();
    body.push(0);
    assert_eq!(
        decode_canonical::<CorpusBodyV1>(&envelope_with_body(&body)),
        Err(CodecError::BodyDecode)
    );
}

// Contract §2: the schema identity is owned by the body type, and a zero
// domain/schema/version descriptor is rejected at the entry of both encode
// and decode before any bytes are examined.
#[test]
fn zero_descriptor_fields_are_invalid_schema_identity() {
    #[derive(Debug, PartialEq)]
    struct ZeroIdentity<const D: u16, const S: u16, const V: u16>;

    impl<const D: u16, const S: u16, const V: u16> KixBcsSchema for ZeroIdentity<D, S, V> {
        const DOMAIN_ID: u16 = D;
        const SCHEMA_ID: u16 = S;
        const SCHEMA_VERSION: u16 = V;
        const MAX_BODY_BYTES: usize = 16;

        fn encode_body(&self) -> Result<Vec<u8>, CodecError> {
            Ok(Vec::new())
        }

        fn decode_body(_bytes: &[u8]) -> Result<Self, CodecError> {
            Err(CodecError::BodyDecode)
        }
    }

    assert_eq!(
        canonical_bytes(&ZeroIdentity::<0, 1, 1>),
        Err(CodecError::InvalidSchemaIdentity)
    );
    assert_eq!(
        canonical_bytes(&ZeroIdentity::<1, 0, 1>),
        Err(CodecError::InvalidSchemaIdentity)
    );
    assert_eq!(
        canonical_bytes(&ZeroIdentity::<1, 1, 0>),
        Err(CodecError::InvalidSchemaIdentity)
    );
    assert_eq!(
        decode_canonical::<ZeroIdentity::<0, 1, 1>>(&GOLDEN),
        Err(CodecError::InvalidSchemaIdentity)
    );
    // With every descriptor field non-zero the identity check passes and the
    // next gate (envelope length) produces the error instead.
    assert_eq!(
        decode_canonical::<ZeroIdentity::<1, 1, 1>>(&GOLDEN),
        Err(CodecError::EnvelopeTooLarge)
    );
}

// Contract §2: the body byte bound is enforced on encode as well — a body
// encoding one byte past MAX_BODY_BYTES is BodyTooLarge, at the bound it
// round-trips.
#[test]
fn encode_side_body_bound_is_enforced() {
    #[derive(Debug, PartialEq, Serialize, Deserialize)]
    struct VecBody {
        data: Vec<u8>,
    }

    impl KixBcsSchema for VecBody {
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

    let at_bound = VecBody { data: vec![0; 15] }; // encodes to 16 bytes
    let bytes = canonical_bytes(&at_bound).unwrap();
    assert_eq!(decode_canonical::<VecBody>(&bytes), Ok(at_bound));

    assert_eq!(
        canonical_bytes(&VecBody { data: vec![0; 16] }), // encodes to 17 bytes
        Err(CodecError::BodyTooLarge)
    );
}

// Contract §2: a body type BCS cannot express fails with BodyEncode rather
// than producing non-canonical output.
#[test]
fn unsupported_body_type_is_body_encode() {
    assert_eq!(encode_bcs_body(&'x'), Err(CodecError::BodyEncode));
}
