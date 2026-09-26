# KIX 계약 전용 OpenAPI

**상태: 계약 전용. 라이브 HTTP 서버는 없다. 운영 엔드포인트는 없다.**

이 디렉터리는 `reference/v0.3-rc1/protocol_contract.json`에 있는 로컬 호출 명령을 OpenAPI 3.1로 옮긴 산출물이다. 명령을 새로 만들거나, 인증·재시도·전송 보장·운영 URL을 정하지 않는다. 라이브 HTTP 서버는 이후의 별도 관문이다.

## 파일

| 파일 | 역할 |
|---|---|
| [`kix-protocol.contract-only.openapi.json`](kix-protocol.contract-only.openapi.json) | 계약 전용 OpenAPI 3.1 문서 |
| [`../../../scripts/check_openapi_contract.py`](../../../scripts/check_openapi_contract.py) | 명령 키·본문 스키마·핀이 원본과 같아야 통과하는 검사 |

JSON만 둔다. 검사는 Python 표준 라이브러리만 쓰고, 별도 YAML 패키지를 요구하지 않는다.

## 핀

기계가 읽는 핀은 OpenAPI 문서의 `x-kix-source`다. 검사는 아래 파일 바이트로 git blob과 sha256을 다시 계산한다. README의 이 표는 그 핀을 사람이 읽도록 옮긴 것이다.

| 항목 | 값 |
|---|---|
| 원본 경로 | `reference/v0.3-rc1/protocol_contract.json` |
| git blob | `619ae21c82ca3df5661bd3831613f15fa65225ff` |
| sha256 | `ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e` |
| domain | `kix:fixture:lifecycle:0.3` |
| `x-kix-contract-status` | `contract-only` |

`info.version`은 `0.3-rc1+sha256:` 뒤에 위 sha256을 붙인다. `info.summary`는 “Contract-only. No live HTTP server. No production endpoint.”다.

## 문서가 따르는 호출

권위 있는 로컬 호출은 `Core.execute(operationId, actor, action, body)`다.

| 자리 | 의미 |
|---|---|
| `operationId` | 호출 한 건의 식별자. 명령 이름이 아니다. |
| `actor` | 참조 모형의 픽스처 문자열. 권한 증명으로 쓰지 않는다. |
| `action` | `protocol_contract.json`의 `commands` 키. 본문 스키마를 고른다. |
| `body` | 그 명령의 JSON Schema. `additionalProperties: false`. |

v0.1 통합명세 §9.1은 봉투 필드를 `protocolDomain, operationId, actorContext, action, body`로 적는다. 현재 Python 함수는 `actorContext`를 받지 않고 `body.domain`을 검사한다. `actorContext`는 명세가 인증·서명 검증 결과로 부르는 이름이다. 이 문서는 인증 스킴을 만들지 않는다. `sourceAuthentication: FIXTURE_ONLY`는 원본에 적힌 라벨이며 HTTP 보안 스킴이 아니다.

OpenAPI `paths`에는 자리 표시 하나뿐 있다.

- 경로: `/x-kix-contract-only/local-call`
- `x-kix-transport: contract-only-placeholder`
- `operationId: invokeLocalCall`

이 경로는 OpenAPI 문법을 맞추기 위한 자리다. 프로토콜의 경로 규칙도, 공개된 HTTP 서비스도 아니다. `POST`도 문법 자리이지 프로토콜이 정한 HTTP 메서드가 아니다. `servers`는 없다.

명령마다의 대응은 경로가 아니라 `x-kix-local-call-operations`에 있다. 그 `operationId`는 명령 이름이고 Python의 `action`과 같다. 호출 식별자인 봉투 `operationId`와 섞지 않는다. 본문은 `components.schemas.<명령>`이며 `x-kix-action-body-map`이 `action`에서 그 스키마로 연결한다. 같은 본문 스키마를 쓰는 명령이 있으므로, 필드 모양만으로 명령을 구분하지 않는다.

## 유지한 fail-closed 규칙

원본에서 그대로 복사한다.

- 각 명령 스키마의 `additionalProperties: false`
- `unknownFields: REJECT`
- `sourceAuthentication: FIXTURE_ONLY`
- `handlerConstraints` 문장 전체

`handlerConstraints`는 금액 부호, enum, actor 범위, 정책, 현재 버전, 잔액, 조건부 결합이 핸들러에서 더 검사되고, 이 카탈로그만으로는 업무 검증기가 아니라고 말한다. 그 핸들러 규칙을 이 OpenAPI에 새로 풀어 적지 않았다. 내보내진 스키마에 없는 `const`도 넣지 않았다.

참조 모형이 `operationId`·`actor`에 적용하는 `ident` 길이와, 같은 `operationId`의 지문 충돌(`OPERATION_ID_CONFLICT`)은 `x-kix-reference-model-observed`로만 적었다. HTTP 재시도 계약이 아니다.

## 명령 집합

v0.3-rc1 `commands` 키를 모두 싣는다. `x-kix-omitted-commands`는 빈 배열이다. 이 핀의 명령은 40개다.

아래 계약은 이 JSON의 키가 아니다. 일부를 빼서 숨긴 것이 아니라, 이 카탈로그의 범위 밖이다.

| 경로 | 이유 |
|---|---|
| `reference/booking_resale_admission/` | 별도 오프라인 목 |
| `reference/settlement_f01_f03/` | 별도 오프라인 목 |
| `reference/credit_advance_f04/` | 별도 오프라인 목 |
| `reference/v0.3-rc1/commerce_driver.py` | 계산 전용 `{action, args}` 봉투. 이 명령 카탈로그가 아님 |

## 상거래 앱이 나중에 읽는 방법

이 산출물이 병합된 뒤에 읽는다. 그 전이나 후에도 이 문서만으로 HTTP 클라이언트를 열지 않는다.

1. 파일 경로와 `x-kix-source.sha256`을 핀으로 고정한다. `servers`가 없으므로 base URL을 만들지 않는다.
2. `/x-kix-contract-only/local-call`을 호출 주소로 쓰지 않는다.
3. 로컬 호출 준비 형태는 `operationId`, `actor`, `action`, `body`다. `action`으로 `components.schemas`의 명령 스키마를 고른다.
4. 본문의 알려지지 않은 필드는 거절한다 (`additionalProperties: false`, `unknownFields: REJECT`).
5. `actor`를 인증 결과로 믿지 않는다. 인증 구현은 이 문서에 없다.
6. 재시도, 전송 성공, 운영 엔드포인트를 이 문서에서 추론하지 않는다.
7. 라이브 HTTP 서버가 필요하면 이 파일이 아니라 이후의 별도 관문에서 정한다.

## 검사

```bash
python3 scripts/check_openapi_contract.py
python3 scripts/check_openapi_contract.py --self-test
```

첫 명령은 커밋된 OpenAPI가 원본 명령 키·스키마·핀과 같은지 본다. 명령이 늘거나 줄거나, `additionalProperties`가 빠지거나, 서버 URL·보안 스킴이 생기면 실패한다. `--self-test`는 그 실패 경로를 메모리에서 확인한다.
