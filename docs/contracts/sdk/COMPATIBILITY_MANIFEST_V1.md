# 호환 manifest-v1과 BOOTSTRAP profile

이 문서는 `p-sdk-0`이 처음 고정하는 형식이다. 산출물은 감사 통과, 사용자 승인, 운영 적합, 출시 권한이 아니다. `bootstrap-1`은 원본 40개 명령 카탈로그의 스키마 결합만 부여한다. `bootstrap-2`는 84개 명령 카탈로그의 스키마 결합만 부여한다. 어느 쪽도 의미 검증, N/N−1, production conformance가 아니다. 소비자는 의미 적합까지 HOLD다.

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
| `profile_revision` | `bootstrap-1`은 40개 명령의 역사 핀이다. `bootstrap-2`는 84개 명령의 불변 개정이다. 다른 개정은 검증기가 프로파일 파일을 찾지 못하면 거절한다 |
| `profile_sha256` | profile 파일 바이트의 SHA-256. profile 안에는 없다 |
| `producer` | `repository`, `source_commit`, `source_tree`, `protocol_domain`, `contract_schema_version` |
| `contract` | `contract_only`와 `integration_gate`. 각각 `path`, `gitBlob`, `sha256` |
| `generator` | `path`, `sha256`, `toolchain` (`node-24`) |
| `sdk_output` | 생성 카탈로그의 `path`, `sha256` |
| `vectors` | `{name, path, sha256}` 배열 |
| `source_references` | `fixture_profile`은 `reference/v0.3-rc1/protocol_contract.json`. `bootstrap-1`의 `extension_profile`은 `false`다. `bootstrap-2`의 `extension_profile`은 `docs/contracts/openapi/fsm-command-contract.json`의 `path`, `gitBlob`, `sha256`이다 |

`bootstrap-1`의 `producer.source_commit`과 `source_tree`는 그 40개 명령 입력이 있던 커밋 `7481b0e16ce9b903abbffa62249bb91cd9e63cfe`와 그 트리 `8495c7651e456cead3a8812b9e6fb183f818acd2`다. `bootstrap-2`의 값은 생성기에 적힌 베이스 `c2cde86e21a6e5ba6f24a56548636db6d0a34c6f`와 트리 `394084b15e01bbe4a5612aeb3431f3278c43dd85`다. 검증기는 그 커밋을 git에서 풀지 않는다. 확대 카탈로그의 바이트 결합은 OpenAPI 두 파일과 FSM 원본 해시다. 둘 다 전달 HEAD가 아니다.

`manifest_digest`는 정규 manifest 바이트의 SHA-256이다. `manifest.bootstrap-1.json.sha256`에 소문자 hex와 newline으로만 둔다. manifest 본문에 넣지 않는다.

금지 키: `manifest_digest`, `manifest_sha256`, `final_commit`, `delivery_head`, `consumer_head`.

## 3. BOOTSTRAP profile

경로 규칙은 `sdk/compat/profiles/<profile_revision>.profile.json`이다. 개정 이름에 경로 구분자는 없다.

profile은 `manifest_schema_version`, `profile_kind`, `profile_revision`, `catalogue`, `vectors`, `grants`, `non_claims`만 가진다. `grants`는 `catalogue-schema-binding only`다. `bootstrap-1`의 `catalogue`는 정렬한 40개 명령이다. `bootstrap-2`의 `catalogue`는 정렬한 84개 명령이다. 명령별 스키마 digest와 OpenAPI 경로·sha256을 가진다.

profile에 `profile_sha256`, commit, 최종 HEAD를 넣지 않는다. `non_claims`는 의미 적합성, N/N−1, 운영 적합, 감사·승인을 부여하지 않는다고 적는다.

`SEMANTIC_CONFORMANCE`는 형식상 허용하는 kind 이름이다. 이 노드의 profile은 그 kind가 아니고, 그 검증은 후속 `contract-compatibility-profile`의 일이다. 이 노드가 그 완료를 기다리지 않는다.

## 4. 최소 검증기

`sdk/compat/verify_compat.mjs --manifest <path> [--expect-kind K] [--expect-revision R]`

순서는 정규 파싱, 필수 필드와 kind, profile 바이트 해시, 두 OpenAPI 파일의 경로·blob·sha256, 생성기 해시와 `toolchains.json`의 Node 주버전, 생성 산출물 sha256, vector digest, sidecar digest다. 하나라도 어긋나면 0이 아닌 상태로 끝난다. 판정은 JSON 한 줄이다.

검증기는 읽기 전용이다. `source_commit`이 git 역사의 조상인지는 보지 않는다. 바이트가 그 커밋에 있었는지는 생성 시점의 핀으로 남기고, 전달 HEAD의 결합은 이 파일이 하지 않는다.

## 5. 재생성

`sdk/generate/generate_client.mjs`가 카탈로그를 만들고 `sdk/generate/generate_manifest.mjs`가 `bootstrap-2` profile·manifest·sidecar를 만든다. `bootstrap-1` 파일은 역사 핀으로 두고 다시 생성하지 않는다. 그 파일은 옛 OpenAPI 바이트를 가리키므로 확대된 바이트와는 맞지 않는다. 핵심 원본 sha256 `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e`가 바뀌면 생성은 실패한다. 새 바이트에 이전 manifest를 다시 쓰지 않는다.
