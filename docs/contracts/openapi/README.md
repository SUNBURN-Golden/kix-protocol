# KIX 계약 전용 OpenAPI와 비운영 통합 관문

**운영 엔드포인트는 없다. 공개 호스트는 없다. 로컬 HTTP 테스트의 성공은 운영 승인이 아니다.**

`kix-protocol.contract-only.openapi.json`은 `reference/v0.3-rc1/protocol_contract.json`의 로컬 호출 명령을 OpenAPI 3.1로 옮긴 **계약 전용 핀**이다. 그 파일은 라이브 서버를 선언하지 않는다. `x-kix-live-http-server`는 `false`이고 `x-kix-production-endpoint`는 `false`다. 명령을 새로 만들거나, 인증·재시도·전송 보장·운영 URL을 정하지 않는다.

`kix-protocol.integration-gate.openapi.json`은 그 같은 40개 명령과 같은 로컬 호출 경로를 **비운영 루프백 통합 관문**으로 적는다. `python3 -m integration_gate`는 `127.0.0.1`에만 붙고, `POST /x-kix-contract-only/local-call` 봉투를 `Core.execute`로 넘긴다. 상태는 기존 인메모리 참조 모형이다. PG·KYC·공연장·은행 실연동을 만들지 않는다.

## 파일

| 파일 | 역할 |
|---|---|
| [`kix-protocol.contract-only.openapi.json`](kix-protocol.contract-only.openapi.json) | 계약 전용 OpenAPI 3.1 문서. 라이브 서버를 선언하지 않는다 |
| [`kix-protocol.integration-gate.openapi.json`](kix-protocol.integration-gate.openapi.json) | 비운영 루프백 통합 관문 설명. 명령은 40개 그대로다 |
| [`../../../scripts/check_openapi_contract.py`](../../../scripts/check_openapi_contract.py) | 계약 전용 문서의 명령 키·본문 스키마·핀 검사 |
| [`../../../scripts/check_integration_gate_openapi.py`](../../../scripts/check_integration_gate_openapi.py) | 통합 관문 문서가 같은 40개 명령·비운영 표식을 유지하는지 검사 |
| [`../../../integration_gate/`](../../../integration_gate/) | 루프백 HTTP 프로세스. 운영 배치물이 아니다 |

OpenAPI 산출물은 JSON이다. 검사는 Python 표준 라이브러리만 쓰고, 별도 YAML 패키지를 요구하지 않는다.

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

이 절은 계약 전용 파일의 자리다. 그 경로는 프로토콜의 자원 나무가 아니고, 공개된 HTTP 서비스도 아니다. `POST`는 그 파일에서 문법 자리였다. 통합 관문 문서는 같은 경로의 POST만 비운영 루프백 전송으로 적고, 명령을 늘리지 않는다. `servers`는 어느 문서에도 없다.

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
2. 계약 전용 파일의 경로를 공개 서비스 주소로 쓰지 않는다. 개발자가 비운영 통합 관문 프로세스를 루프백에 띄운 경우에만 같은 경로가 그 프로세스의 POST를 받는다.
3. 로컬 호출 준비 형태는 `operationId`, `actor`, `action`, `body`다. `action`으로 `components.schemas`의 명령 스키마를 고른다.
4. 본문의 알려지지 않은 필드는 거절한다 (`additionalProperties: false`, `unknownFields: REJECT`).
5. `actor`를 인증 결과로 믿지 않는다. 인증 구현은 이 문서에 없다.
6. 재시도, 전송 성공, 운영 엔드포인트를 이 문서에서 추론하지 않는다.
7. 비운영 루프백 통합 관문은 아래 절이 적는다. 그 관문은 운영 엔드포인트가 아니고, 상거래 앱 결합도 아니다.

## 검사

```bash
python3 scripts/check_openapi_contract.py
python3 scripts/check_openapi_contract.py --self-test
python3 scripts/check_integration_gate_openapi.py
python3 scripts/check_integration_gate_openapi.py --self-test
python3 -m unittest integration_gate.test_http_gate
```

계약 전용 검사는 커밋된 카탈로그가 원본 명령 키·스키마·핀과 같은지 본다. 명령이 늘거나 줄거나, `additionalProperties`가 빠지거나, 서버 URL·보안 스킴이 생기면 실패한다. `--self-test`는 그 실패 경로를 메모리에서 확인한다.

## 비운영 통합 관문

로컬에서만 띄운다. 기본 바인드는 `127.0.0.1`과 포트 `8765`다. 다른 호스트는 프로세스가 거절한다. 공개 DNS, TLS 종단, OAuth, 운영 배치를 만들지 않는다.

```bash
python3 -m integration_gate --port 8765
```

| 구분 | 동작 |
|---|---|
| `POST /x-kix-contract-only/local-call` | 봉투 `operationId`, `actor`, `action`, `body`. 본문은 그 명령의 공개 스키마로 검사한 뒤 `Core.execute` |
| `GET /health` | 프로세스가 응답하는지만 본다. 프로토콜 명령이 아니다 |
| `GET /ready` | 인메모리 참조 코어와 40개 명령 카탈로그가 열려 있는지만 본다. 운영 준비가 아니다 |
| 그 밖 경로·메서드 | 실패로 닫는다. 이벤트·티켓·결제·공연장·시장의 REST 트리는 없다 |

거절은 HTTP 200으로 숨기지 않는다. 스키마·봉투 오류는 4xx이고, `Core.execute`가 `Rejected`를 던지면 422에 그 코드가 담긴다. 본문 상한은 65536바이트, 요청 시간 상한은 5초, 헤더 상한은 8192바이트다.

같은 프로세스 안에서는 참조 모형 그대로, 같은 `operationId`와 같은 actor·action·body 지문이면 저장 영수증을 다시 주고, 지문이 다르면 `OPERATION_ID_CONFLICT`다. HTTP `Idempotency-Key`는 보지 않는다. 프로세스를 다시 시작하면 인메모리 상태와 그 재생은 사라진다. 재시작 생존을 내구성으로 읽지 않는다.

`actor`는 픽스처 문자열이다. 인증 결과가 아니다. 외부 PG·KYC·공연장·은행 어댑터는 붙이지 않는다. 성공한 로컬 호출은 실자금·실입장·운영 적합성의 증거가 아니다.
