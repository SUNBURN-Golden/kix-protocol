# KIX 비운영 TypeScript 0.x 클라이언트

안정 1.0이 아니다. 공개 배포나 레지스트리 발행물이 아니다. 운영 엔드포인트, 인증, 재시도, 전송 성공을 만들지 않는다.

이 디렉터리는 `docs/contracts/openapi/kix-protocol.contract-only.openapi.json`에서 결정적으로 생성한 로컬 호출 클라이언트다. 전송 함수는 호출자가 넣는다. base URL은 없다. 계약 전용 문서에 `servers`가 없기 때문이다.

`actor`는 참조 모형의 픽스처 문자열이다. v0.1 통합명세 §9.1의 `actorContext`는 인증·서명 검증 결과를 부르는 이름이고, 현재 Python `Core.execute`는 그 인자를 받지 않는다. 이 클라이언트는 그 Python 인자 목록(`operationId`, `actor`, `action`, `body`)을 따른다. `actor`를 인증 결과로 쓰지 않는다.

## 상거래 앱이 나중에 읽는 방법

`docs/contracts/openapi/README.md`의 소비자 규칙이다.

1. 파일 경로와 `x-kix-source.sha256`을 핀으로 고정한다. `servers`가 없으므로 base URL을 만들지 않는다.
2. 계약 전용 파일의 경로를 공개 서비스 주소로 쓰지 않는다. 개발자가 비운영 통합 관문 프로세스를 루프백에 띄운 경우에만 같은 경로가 그 프로세스의 POST를 받는다.
3. 로컬 호출 준비 형태는 `operationId`, `actor`, `action`, `body`다. `action`으로 `components.schemas`의 명령 스키마를 고른다.
4. 본문의 알려지지 않은 필드는 거절한다 (`additionalProperties: false`, `unknownFields: REJECT`).
5. `actor`를 인증 결과로 믿지 않는다. 인증 구현은 이 문서에 없다.
6. 재시도, 전송 성공, 운영 엔드포인트를 이 문서에서 추론하지 않는다.
7. 비운영 루프백 통합 관문은 아래 절이 적는다. 그 관문은 운영 엔드포인트가 아니고, 상거래 앱 결합도 아니다.

7번의 "아래 절"은 OpenAPI README의 통합 관문 절이다. 이 SDK는 그 프로세스를 띄우지 않는다.

## 생성물

| 파일 | 역할 |
|---|---|
| `generate/generate_client.mjs` | 카탈로그를 다시 만든다 |
| `generated/catalogue.ts` | 84개 명령과 본문 스키마, FSM 기계 맵. 바이트 동일 재생성의 대상 |
| `sdk-pin.json` | OpenAPI·원본 계약의 git blob과 sha256 |
| `src/client.ts` | `createLocalCallClient({ transport })` |
| `src/jsonschema.ts` | 엄격 JSON과 스키마 부분집합 |
| `compat/` | manifest-v1, BOOTSTRAP profile, 최소 검증기 |
| `conformance/` | 명령별 적합성과 golden vectors |

호환 형식은 [docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md](../docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md)에 있다. 현재 생성물은 `bootstrap-2`다. `bootstrap-1`은 40개 명령 역사 핀으로 트리에 남아 있고 다시 생성하지 않는다. 둘 다 카탈로그 스키마 결합만 부여한다. 의미 적합성, N/N−1, 운영 적합, 감사 통과, 사용자 승인이 아니다. 의미 적합의 소비자는 HOLD다.

타입 검사는 Node 24의 타입 제거로 돌린다. `tsc`와 패키지 의존성은 없다. 지울 수 있는 구문만 쓴다.

## 재생과 검사

```bash
npm --prefix sdk run generate
python3 scripts/check_sdk_client.py
python3 scripts/check_sdk_client.py --self-test
npm --prefix sdk run conformance
npm --prefix sdk run verify-compat
```

Node는 `toolchains.json`의 `nodeMajor` 24다.
