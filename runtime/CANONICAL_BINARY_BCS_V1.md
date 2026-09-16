# KIX Binary Canonical Encoding v1 (KIX-BCS1)

KIX production runtime의 서명·해시·불변 snapshot identity는 JSON canonicalization이 아니라 **versioned BCS body + KIX 고정 framing**을 사용한다. 기존 CE1은 S06.1과 역사적 fixture의 호환·회귀 규격으로 보존하되 S07 production identity의 정본이 아니다.

BCS는 Sui/Move 생태계가 사용하는 canonical binary serialization이고 정수·고정 길이 바이트 배열을 JSON보다 직접적으로 표현할 수 있다. 다만 BCS 자체는 self-describing format이 아니므로 KIX는 schema id/version/domain을 별도로 고정한다.

## 1. Envelope

production canonical bytes는 다음 논리 구조를 BCS로 직렬화한 값이다.

```rust
struct KixEnvelopeV1 {
    magic: [u8; 4],        // b"KIX1"
    domain_id: u16,        // immutable registry
    schema_id: u16,        // immutable registry
    schema_version: u16,   // positive
    body: Vec<u8>,         // BCS(T) for the registered schema
}
```

`canonical_bytes(T) = BCS(KixEnvelopeV1 { body: BCS(T), ... })`

`canonical_hash(T) = SHA-256(canonical_bytes(T))`

동일 `domain_id/schema_id/schema_version`은 영구히 동일 schema를 뜻한다. 기존 schema의 field type/order/meaning을 바꾸지 않는다. 변경은 새 version 또는 새 schema id를 사용한다.

## 2. S07-A 구현 경계

실제 Rust 구현은 `runtime/crates/kix-bcs1`이다.

- body 타입이 `KixBcsSchema` trait의 `DOMAIN_ID`, `SCHEMA_ID`, `SCHEMA_VERSION`, `MAX_BODY_BYTES`를 고정한다.
- encode/decode 호출자가 domain/schema/version을 전달하지 않는다. caller-controlled schema negotiation을 허용하지 않는다.
- decode는 envelope 전체 길이를 schema bound와 비교한 뒤 BCS decode를 수행하고, magic/domain/schema/version/body 길이를 다시 검증한다.
- body encode/decode와 domain object validation은 schema 구현이 소유한다. wire struct를 domain type으로 바꾸는 과정에서 schema-specific invariant를 검사한다.
- `canonical_hash`는 정확히 canonical envelope bytes의 SHA-256이다.
- 외부 문자열용 `BoundedUtf8<N>`은 UTF-8 byte length를 encode 전과 decode 시 모두 제한한다.
- test-only golden-vector domain/schema는 `65535/65535`로 영구 예약하며 production schema registry에서 재사용하지 않는다.

## 3. 타입 원칙

- protocol amount: `u128 atoms`; float 금지.
- online BIGINT fast lane은 registry execution profile에서 별도 제한하며 canonical amount 의미를 바꾸지 않는다.
- KIX generated UUIDv7 identity: 가능한 경우 `[u8;16]`.
- AssetId, registry/content hash: `[u8;32]`.
- timestamp/version/quantity/generation은 의미별 고정 integer type을 사용한다.
- machine enum/state는 안정된 numeric discriminant 또는 versioned enum schema를 사용한다.
- 외부 provider opaque id와 사용자 표시 문자열만 bounded string을 사용한다.
- map/set을 canonical body의 핵심 서명 객체에서 무분별하게 사용하지 않는다. 순서가 의미 없는 집합은 encode 전에 명시된 binary key ordering으로 정렬하거나 schema가 sorted vector를 요구한다.

## 4. JSON/Protobuf의 역할

JSON은 사람·브라우저·외부 호환 API에서 사용할 수 있으나 JSON 원문은 production signing/hash identity가 아니다. 검증된 request를 Rust typed struct로 parse한 뒤 KIX-BCS1 canonical bytes를 만든다.

Protobuf/gRPC는 transport schema로 사용할 수 있으나 transport wire bytes를 KIX canonical identity로 간주하지 않는다. canonical identity가 필요한 객체는 typed value에서 KIX-BCS1을 별도로 계산한다.

## 5. Sui와의 경계

Move/Sui에서 동일 객체 의미를 공유할 때 Rust와 Move가 BCS field order와 integer width를 동일하게 가져야 한다. Sui transaction 자체의 BCS와 KIX application envelope를 혼동하지 않는다. KIX application domain/schema registry는 KIX가 별도로 version한다.

S07 이후 chain-bound object에는 필요한 경우 `kix_schema_id`, `kix_schema_version`, canonical commitment를 명시하여 off-chain Order/Payment/SaleIntent와 exact binding을 확인한다.

## 6. CE1 migration policy

- CE1 Commerce v2 결과와 기존 hash는 역사적 검증 자료로 유지한다.
- CE1 hash를 KIX-BCS1 hash로 암묵 승격하거나 같은 ID namespace에서 동일시하지 않는다.
- S07 production Order는 KIX-BCS1 snapshot을 새로 생성한다.
- Python/TypeScript CE1 구현은 regression fixture이며 새 production runtime 설계권한이 아니다.

## 7. S07-A golden vector

고정 conformance fixture는 다음 의미를 가진다.

```text
domainId      = 65535
schemaId      = 65535
schemaVersion = 1
id            = 00 01 ... 0f
assetId       = a0 a1 ... bf
atoms         = u128::MAX
label         = "kix"
```

고정 canonical bytes hex:

```text
4b495831ffffffff010044000102030405060708090a0b0c0d0e0fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfffffffffffffffffffffffffffffffff036b6978
```

고정 SHA-256:

```text
3668b984571c93a71c3a618a65305fef5321515a7253cb885ffbae6e4b3bfe09
```

이 값은 코드가 자기 자신을 다시 serialize해서 기대값을 만드는 방식이 아니라 외부 고정 상수로 테스트한다.

## 8. 검증 게이트

S07-A에서 다음을 Rust CI가 검사한다.

1. Rust KIX-BCS1 encode/decode/hash 고정값.
2. magic/domain/schema/version 변이 거절.
3. malformed/trailing bytes 거절.
4. `u128` zero/max lossless round-trip.
5. bounded UTF-8 oversize encode/decode 거절.
6. CE1-like JSON bytes/hash와 KIX-BCS1 identity 분리.

Move-bound production schema가 생기는 S08부터 Rust↔Move BCS equality golden vector를 추가한다. 외부 SDK를 제공할 때는 SDK↔Rust 일치도 같은 fixture를 사용한다.

성능 benchmark에서는 JSON CE1 encode/hash와 KIX-BCS1 encode/hash의 CPU time, allocations, encoded size를 별도 측정한다.
