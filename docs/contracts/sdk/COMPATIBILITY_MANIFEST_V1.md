# 호환 manifest-v1과 BOOTSTRAP profile

이 문서는 `p-sdk-0`이 처음 고정하는 형식이다. 산출물은 감사 통과, 사용자 승인, 운영 적합, 출시 권한이 아니다. BOOTSTRAP은 원본 40개 명령 카탈로그의 스키마 결합만 부여한다. 확대 카탈로그의 의미 검증, N/N−1, production conformance로 읽지 않는다.

정확한 전달 HEAD와 소비 HEAD는 manifest 밖에 있는 보호된 증거로 묶는다. manifest와 profile은 자기 digest와 최종 commit을 입력에 넣지 않는다.

## 1. 정규 인코딩

프로파일 이름은 `kix-canonical-json/1`이다. 생성기와 검증기가 같은 바이트를 낸다.

| 규칙 | 내용 |
|---|---|
| 바이트 | UTF-8. 잘못된 UTF-8은 거부 |
| 객체 | 키를 유니코드 코드 포인트 순으로 정렬. 구분자 `,` `:`만 사용. 의미 없는 공백 없음 |
| 배열 | 요소 순서는 유지 |
| 문자열 | `JSON.stringify` 이스케이프. 비ASCII는 `\u`로 바꾸지 않음 |
| 숫자 | 십진 정수. 선행 0, `-0`, 소수, 지수 표기 없음 |
| 정수 범위 | `-9007199254740991` 이상 `9007199254740991` 이하. 그 밖은 `integer-range` |
| 끝 | 값 뒤의 바이트가 있으면 거부. 마지막 newline 없음 |
| 중복 키 | 거부 |
| 깊이 | 검증기 구현 한도 32. 프로토콜 필드 한도가 아님 |

거절 이유는 `duplicate-key`, `unsorted-keys`, `non-integer`, `integer-range`, `truncated`, `trailing-bytes`, `whitespace`, `invalid-utf8`이다.

OpenAPI 핀 파일 자체는 기존 pretty JSON이다. 이 정규 형식은 manifest, profile, golden vector에 적용한다. 명령 본문을 바이트로 읽을 때는 `parseStrict`를 쓰고, `JSON.parse`의 중복 키 덮어쓰기에 의존하지 않는다.

## 2. manifest-v1

필수 최상위 필드는 아래뿐이고, 다른 키는 거부한다.

| 필드 | 내용 |
|---|---|
| `manifest_schema_version` | `kix-compat-manifest/1` |
| `profile_kind` | `BOOTSTRAP` 또는 `SEMANTIC_CONFORMANCE` |
| `profile_revision` | 이 초기 산출물은 `bootstrap-1` |
| `profile_sha256` | profile 파일 바이트의 SHA-256. profile 안에는 없다 |
| `producer` | `repository`, `source_commit`, `source_tree`, `protocol_domain`, `contract_schema_version` |
| `contract` | `contract_only`와 `integration_gate`. 각각 `path`, `gitBlob`, `sha256` |
| `generator` | `path`, `sha256`, `toolchain` (`node-24`) |
| `sdk_output` | 생성 카탈로그의 `path`, `sha256` |
| `vectors` | `{name, path, sha256}` 배열 |
| `source_references` | `fixture_profile`은 `reference/v0.3-rc1/protocol_contract.json`. `extension_profile`은 `false` |

`producer.source_commit`과 `source_tree`는 이 카탈로그 입력이 있던 커밋 `7481b0e16ce9b903abbffa62249bb91cd9e63cfe`와 그 트리 `8495c7651e456cead3a8812b9e6fb183f818acd2`다. 전달 HEAD가 아니다.

`manifest_digest`는 정규 manifest 바이트의 SHA-256이다. `manifest.bootstrap-1.json.sha256`에 소문자 hex와 newline으로만 둔다. manifest 본문에 넣지 않는다.

금지 키: `manifest_digest`, `manifest_sha256`, `final_commit`, `delivery_head`, `consumer_head`.

## 3. BOOTSTRAP profile

경로 규칙은 `sdk/compat/profiles/<profile_revision>.profile.json`이다. 개정 이름에 경로 구분자는 없다.

profile은 `manifest_schema_version`, `profile_kind`, `profile_revision`, `catalogue`, `vectors`, `grants`, `non_claims`만 가진다. `grants`는 `catalogue-schema-binding only`다. `catalogue`는 OpenAPI 경로와 sha256, 정렬한 40개 명령 집합의 digest, 명령별 스키마 digest다.

profile에 `profile_sha256`, commit, 최종 HEAD를 넣지 않는다. `non_claims`는 의미 적합성, N/N−1, 운영 적합, 감사·승인을 부여하지 않는다고 적는다.

`SEMANTIC_CONFORMANCE`는 형식상 허용하는 kind 이름이다. 이 노드의 profile은 그 kind가 아니고, 그 검증은 후속 `contract-compatibility-profile`의 일이다. 이 노드가 그 완료를 기다리지 않는다.

## 4. 최소 검증기

`sdk/compat/verify_compat.mjs --manifest <path> [--expect-kind K] [--expect-revision R]`

순서는 정규 파싱, 필수 필드와 kind, profile 바이트 해시, 두 OpenAPI 파일의 경로·blob·sha256, 생성기 해시와 `toolchains.json`의 Node 주버전, 생성 산출물 sha256, vector digest, sidecar digest다. 하나라도 어긋나면 0이 아닌 상태로 끝난다. 판정은 JSON 한 줄이다.

검증기는 읽기 전용이다. `source_commit`이 git 역사의 조상인지는 보지 않는다. 바이트가 그 커밋에 있었는지는 생성 시점의 핀으로 남기고, 전달 HEAD의 결합은 이 파일이 하지 않는다.

## 5. 재생성

`sdk/generate/generate_client.mjs`가 카탈로그를 만들고 `sdk/generate/generate_manifest.mjs`가 profile·manifest·sidecar를 만든다. 카탈로그 원본 sha256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`가 바뀌면 이 BOOTSTRAP 핀은 실패한다. 새 바이트에 이전 manifest를 다시 쓰지 않는다.
