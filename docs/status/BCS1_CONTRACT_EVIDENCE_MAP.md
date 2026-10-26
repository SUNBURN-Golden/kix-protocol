# KIX-BCS1 contract clause evidence map

**Builder-authored map, not A2 review, acceptance or a capability grade change.**

## 0. Basis

Node: `plan-plan-bcs1-contract-clause-evidence-map`. Task input is the supervisor-provided node/design plan; no task file or issue exists for this node.
Observed local `origin/main` and starting branch HEAD: `18aefc8f7c0dd13b7249e0d80304f3b97459fa3a`. No fetch was permitted by the supervisor; remote freshness is unverified. Branch: `agent/kix-plan-plan-bcs1-contract-clause-evidence-map`.
Contract: `runtime/CANONICAL_BINARY_BCS_V1.md`, Git blob `19a58ab1e232c54eb39b717a94c637322c493a4d`.
Locked blobs before work: kernel lib `69564b166f0c27f9af5d8422f0a466b18d74c20f`; quarantine test `b607996c83a119c349f1cc90469ac1ba82764e20`.

Unmapped with reason: §4 JSON/Protobuf transport role has no implementation/test in the two mapped files; §8 benchmark sentence requires separate measurements; §8 Rust CI lead sentence is structural (protocol.yml cargo workspace tests), rather than a test function. These exclusions do not imply coverage. All numbered sections are monitored for unexpected additions by the checker.

## 1. Vocabulary

- COVERED: cited existing tests exercise the stated fixture predicate; Gap and Owner are none.
- PARTIAL: cited existing tests exercise part of the clause; Gap and Owner identify the remainder.
- NOT_COVERED: Tests is none; Gap and Owner identify missing evidence.

Statuses are builder judgments. Symbol existence and fixed golden constant checks do not prove semantic coverage, registry enforcement or independent review. Candidate owners below describe follow-up responsibility, not assigned or authorized implementation work.

## 2. Map

| ID | Section | Clause | Tests | Status | Gap | Owner |
|---|---|---|---|---|---|---|
| S1-ENVELOPE-FIELDS | §1 | Envelope magic, typed ids/version and BCS body field order. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | COVERED | none | none |
| S1-CANONICAL-BYTES | §1 | Canonical bytes wrap the BCS body in the BCS envelope. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | COVERED | none | none |
| S1-CANONICAL-HASH | §1 | SHA-256 over canonical envelope bytes. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values`, `runtime/crates/kix-bcs1/src/lib.rs::round_trip_and_hash_are_deterministic` | COVERED | none | none |
| S1-SCHEMA-PERMANENCE | §1 | Schema field type/order/meaning is permanent; changes require new identity. | none | NOT_COVERED | No registry or schema-evolution test. | KIX-BCS1 contract owner |
| S1-VERSION-POSITIVE | §1 | Schema version is positive. | none | NOT_COVERED | FU-ZERO-ID: InvalidSchemaIdentity on zero domain/schema/version has no test; zero domain/schema semantics are contract-undefined. | kix-bcs1 maintainer |
| S2-TYPED-IDENTITY | §2 | Schema trait owns identity and bound; callers do not negotiate ids. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::domain_schema_and_version_are_bound`, `runtime/crates/kix-bcs1/src/lib.rs::wrong_magic_schema_version_and_trailing_bytes_are_rejected` | PARTIAL | Mutation rejection only; no compile-time API or zero-id regression. | kix-bcs1 maintainer |
| S2-DECODE-ORDER | §2 | Check envelope bound before BCS decoding, then magic/identity/body bound. | `runtime/crates/kix-bcs1/src/lib.rs::wrong_magic_schema_version_and_trailing_bytes_are_rejected`, `runtime/crates/kix-bcs1/tests/golden_vectors.rs::domain_schema_and_version_are_bound` | PARTIAL | Identity rejection covered; predecode ordering and length bounds untested. | kix-bcs1 maintainer |
| S2-ENVELOPE-BOUND | §2 | EnvelopeTooLarge guard. | none | NOT_COVERED | FU-ENVELOPE-TOO-LARGE: no encode/decode envelope oversize regression; encode behavior is characterization only. | kix-bcs1 maintainer |
| S2-BODY-BOUND-ENCODE | §2 | Encode body size guard (implementation-bound characterization). | none | NOT_COVERED | FU-BODY-TOO-LARGE-ENCODE: no encode BodyTooLarge regression; error semantics not stated by contract. | kix-bcs1 maintainer |
| S2-BODY-BOUND-DECODE | §2 | Decode body size guard. | none | NOT_COVERED | FU-BODY-TOO-LARGE-DECODE: no decode BodyTooLarge regression. | kix-bcs1 maintainer |
| S2-SCHEMA-OWNS-BODY | §2 | Schema owns body conversion and domain validation. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | PARTIAL | Golden wire conversion only; no schema-specific invalid domain object. | kix-bcs1 maintainer |
| S2-HASH-EXACT | §2 | Canonical hash hashes exact envelope bytes. | `runtime/crates/kix-bcs1/src/lib.rs::round_trip_and_hash_are_deterministic`, `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | COVERED | none | none |
| S2-BOUNDED-UTF8 | §2 | BoundedUtf8 rejects oversize construction and body decode. | `runtime/crates/kix-bcs1/src/lib.rs::bounded_utf8_rejects_oversize_values` | PARTIAL | ASCII-only probe; decode check uses decode_bcs_body (BodyDecode), not decode_canonical; see FU-UTF8-MULTIBYTE. | kix-bcs1 maintainer |
| S2-UTF8-MULTIBYTE | §2 | UTF-8 byte limit differs from character count. | none | NOT_COVERED | FU-UTF8-MULTIBYTE: no multi-byte UTF-8 byte-versus-character boundary test. | kix-bcs1 maintainer |
| S2-TEST-DOMAIN-RESERVED | §2 | Test-only domain/schema is permanently reserved from production registry. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | PARTIAL | Golden fixture uses reserved ids; permanent production non-reuse untested. | KIX-BCS1 contract owner |
| S3-AMOUNT-U128 | §3 | Amounts use u128 atoms; no float. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::u128_zero_and_max_are_lossless` | PARTIAL | Zero/max lossless fixture only; no production schema or float-exclusion proof. | kix-bcs1 maintainer |
| S3-FIXED-WIDTH-IDS | §3 | UUID identity uses 16 bytes where possible; AssetId/hash use 32 bytes. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | PARTIAL | Fixture id and asset widths only; generated UUIDv7 and registry/content hash schemas absent. | kix-bcs1 maintainer |
| S3-BIGINT-FAST-LANE | §3 | Execution profile separately limits BIGINT fast lane without changing canonical amounts. | none | NOT_COVERED | No production registry execution profile. | KIX-BCS1 contract owner |
| S3-FIXED-INTEGERS-ENUMS | §3 | Semantic fixed-width integers and stable/versioned enums. | none | NOT_COVERED | No production schema integer/enum conformance. | KIX-BCS1 contract owner |
| S3-BOUNDED-STRINGS | §3 | Bounded strings only for provider opaque ids and display strings. | none | NOT_COVERED | No production schema enforcing field role restrictions. | KIX-BCS1 contract owner |
| S3-NO-MAP-SORTED | §3 | Avoid map/set in signed core; sort unordered collections by specified binary key. | none | NOT_COVERED | No collection-ordering schema/test. | KIX-BCS1 contract owner |
| S5-RUST-MOVE-EQUALITY | §5 | Rust/Move field order and integer widths agree; Sui transaction and KIX envelope/registry remain distinct. | none | NOT_COVERED | FU-S08-MOVE-EQUALITY: Rust↔Move equality deferred to S08 production schema. | S08 Move/SDK schema owner |
| S5-CHAIN-BINDING | §5 | Chain-bound objects carry schema/version/commitment as needed for exact binding. | none | NOT_COVERED | No chain-bound production object or binding fixture. | S08 Move/SDK schema owner |
| S6-CE1-PRESERVED | §6 | Preserve historical CE1 Commerce v2 results and hashes. | none | NOT_COVERED | No historical CE1 preservation test in the two mapped files. | KIX-BCS1 contract owner |
| S6-NO-PROMOTION | §6 | Do not implicitly promote CE1 hash or equate ID namespaces. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::legacy_json_is_not_kix_bcs1_identity` | PARTIAL | CE1-like synthetic JSON differs; no namespace/migration implementation or real CE1 fixture. | kix-bcs1 maintainer |
| S6-ORDER-SNAPSHOT | §6 | S07 production Order creates a new KIX-BCS1 snapshot. | none | NOT_COVERED | No production Order snapshot fixture. | KIX-BCS1 contract owner |
| S6-CE1-FIXTURE-ROLE | §6 | Python/TypeScript CE1 stays a regression fixture, without runtime design authority. | none | NOT_COVERED | Governance role has no test function in mapped files. | KIX-BCS1 contract owner |
| S7-GOLDEN-INPUTS | §7 | Golden inputs: reserved ids, version 1, 00..0f id, a0..bf asset, u128 max, kix label. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | COVERED | none | none |
| S7-GOLDEN-BYTES | §7 | Exact external canonical bytes. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | COVERED | none | none |
| S7-GOLDEN-HASH | §7 | Exact external SHA-256. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | COVERED | none | none |
| S7-EXTERNAL-CONSTANT | §7 | Expected values are external constants rather than self-serialization. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values` | COVERED | none | none |
| S8-G1-FIXED-VALUES | §8 | Gate 1: fixed encode/decode/hash values. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::fixed_bytes_and_hash_match_external_golden_values`, `runtime/crates/kix-bcs1/src/lib.rs::round_trip_and_hash_are_deterministic` | COVERED | none | none |
| S8-G2-IDENTITY-MUTATION | §8 | Gate 2: reject magic/domain/schema/version mutation. | `runtime/crates/kix-bcs1/src/lib.rs::wrong_magic_schema_version_and_trailing_bytes_are_rejected`, `runtime/crates/kix-bcs1/tests/golden_vectors.rs::domain_schema_and_version_are_bound` | COVERED | none | none |
| S8-G3-MALFORMED-TRAILING | §8 | Gate 3: malformed/trailing rejection. | `runtime/crates/kix-bcs1/src/lib.rs::wrong_magic_schema_version_and_trailing_bytes_are_rejected` | PARTIAL | Trailing byte only; truncation is FU-TRUNCATED-ENVELOPE; no malformed corpus (parked boundary-corpus). | kix-bcs1 maintainer |
| S8-G3-TRUNCATED | §8 | Gate 3: truncated envelope rejection. | none | NOT_COVERED | FU-TRUNCATED-ENVELOPE: no truncated envelope test; parked boundary-corpus remains outside this node. | kix-bcs1 maintainer |
| S8-G4-U128 | §8 | Gate 4: u128 zero/max lossless round-trip. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::u128_zero_and_max_are_lossless` | COVERED | none | none |
| S8-G5-BOUNDED-UTF8 | §8 | Gate 5: oversize bounded UTF-8 rejection. | `runtime/crates/kix-bcs1/src/lib.rs::bounded_utf8_rejects_oversize_values` | PARTIAL | ASCII-only probe; decode check uses decode_bcs_body (BodyDecode), not decode_canonical; see FU-UTF8-MULTIBYTE. | kix-bcs1 maintainer |
| S8-G6-CE1-SEPARATION | §8 | Gate 6: CE1-like JSON bytes/hash differ from KIX-BCS1. | `runtime/crates/kix-bcs1/tests/golden_vectors.rs::legacy_json_is_not_kix_bcs1_identity` | COVERED | none | none |
| S8-MOVE-SDK-EQUALITY | §8 | S08 Rust↔Move equality and SDK↔Rust equality use shared fixture. | none | NOT_COVERED | FU-S08-SDK-EQUALITY: no Rust↔Move/SDK equality; deferred to S08 and SDK schema delivery. | S08 Move/SDK schema owner |

Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17

## 3. Follow-up candidates (NOT_COVERED, no tests added)

| FU | Row | Path | Candidate owner |
|---|---|---|---|
| FU-ZERO-ID | S1-VERSION-POSITIVE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-ENVELOPE-TOO-LARGE | S2-ENVELOPE-BOUND | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-BODY-TOO-LARGE-ENCODE | S2-BODY-BOUND-ENCODE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-BODY-TOO-LARGE-DECODE | S2-BODY-BOUND-DECODE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-UTF8-MULTIBYTE | S2-UTF8-MULTIBYTE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-S08-MOVE-EQUALITY | S5-RUST-MOVE-EQUALITY | runtime/crates/kix-bcs1/tests/golden_vectors.rs | S08 Move/SDK schema owner |
| FU-TRUNCATED-ENVELOPE | S8-G3-TRUNCATED | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-S08-SDK-EQUALITY | S8-MOVE-SDK-EQUALITY | runtime/crates/kix-bcs1/tests/golden_vectors.rs | S08 Move/SDK schema owner |

Paths identify candidate evidence locations only; no new tests are added or authorized. S08 equality will also need Move/SDK fixtures outside these two Rust files after a schema is approved. Other NOT_COVERED rows remain follow-up candidates with the gap and owner in §2.

## 4. Characterizations (AGENTS §8)

Class A: the cited deterministic tests match their limited predicates; no explicit contract violation was found by inspection.

Class B (contract undefined), observed by source reading rather than new tests:

- SchemaDescriptor::of also rejects zero domain_id and schema_id. The contract explicitly marks only schema_version as positive. InvalidSchemaIdentity zero-id coverage is absent.
- Encode-side BodyTooLarge and EnvelopeTooLarge error behavior is not stated by the contract.
- MAX_ENVELOPE_OVERHEAD_BYTES = 32 is not specified. Actual framing overhead appears to be 10 bytes plus the ULEB128 length; encode-side EnvelopeTooLarge appears unreachable for realistic bounds. This is an unverified source-informed observation, not a tested reachability claim.
- Oversize BoundedUtf8 body decode surfaces as BodyDecode, while construction uses BoundedUtf8Exceeded. The contract specifies no error variant. Existing decode evidence uses decode_bcs_body, not decode_canonical.

No class-C reproduction or contract change is made. The parked plan-bcs1-boundary-corpus scope remains parked.

## 5. Non-claims

no production schema registry; no Move/SDK equality; no malformed-input corpus.
No production runtime, durability, chain finality, provider/bank correctness, clean-room independence, A2 review, acceptance or capability grade change is established. The checker validates document structure, citation existence and golden constant equality; it does not execute the cited Rust tests or infer missing coverage.
