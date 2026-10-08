# 루프백 관문의 브라우저 접근 결정 (2026-10-08)

상태: **채택 제안.** 작성만으로 확정이 아니다. 확정 조건은 Astra 아키텍처 검토와 사용자 병합이다. 이 문서는 관문 코드를 바꾸지 않는다. 구현은 다음 노드 `gate-browser-access`다.

노드 명세가 비교를 요구한 세 갈래 가운데 채택 제안은 (1)이다. 기본은 꺼 둔다. 켜면 허용 출처는 `http://127.0.0.1:5173` 하나다. 관문은 `127.0.0.1`에만 붙는다.

## 1. 기준

- 작업 시작 시 `origin/main`과 HEAD: `771545ae4b64f069396667f399b5200c44fd9af0`. 같은 커밋이다.
- 잠금 blob은 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`.
- `docs/tasks/`에는 이 노드의 과제 파일이 없다. 입력은 노드 명세와 그것이 가리키는 문서다. 이슈 [#99](https://github.com/SUNBURN-Golden/kix-protocol/issues/99)의 본문은 배정 전 자리 표시이며 봉투 전문이 아니다. 과제 파일을 만들지 않았다.
- 이 노드의 실행 입력은 `user_merge: true`, `astra_gate: ARCHITECTURE`, `audit_floor: A3`다. 빌더는 병합하지 않는다. [로드맵](PROGRAM_ROADMAP_20260930.md) §1은 초기 노드 표보다 판정 표의 병합 경계가 우선한다고 적는다. [판정 표](../aiops/PROGRAM_ASTRA_DELEGATION.md)의 이 노드 행은 계약 변경 YES, 대표님 병합, A3다. 초기 노드 표의 병합 칸은 자동(M1·Fable)이다. 그 차이는 이 문서가 정하지 않는다. 판정 표 문서는 머리말에서 비실행 초안이라고 적는다.
- 로드맵 R-11 (1)은 `gate-browser-access`의 구현 범위를 이렇게 한정한다. 루프백 관문의 동작 변경, 기본 꺼짐, 루프백 출처만, 이 결정 문서가 정한 방식으로만. 프로그램 결정 §5의 공개 운영 엔드포인트 잠금은 유지된다.
- 상거래 저장소에서 읽은 기준은 `BeautifulMind-JT/kix-commerce-apps` `83f1f17bbfea81a8371e4c598d41f2915102a6e8`이다. 결합 문서 blob `9a8da873074aa96ceda07a772629098762238773`, `apps/web/vite.config.ts` blob `8785416213151b7cdfefae2bccbac00ef168e3da`, `apps/web/package.json` blob `8931820e77860f575faee636cacca2c45e4f2c98`. 그 저장소는 이 노드에서 수정하지 않는다.

## 2. 지금 관문이 하는 일

`integration_gate/server.py`는 `127.0.0.1`이 아닌 `--host`를 `REFUSING_NON_LOOPBACK_BIND`로 거절한다. `0.0.0.0`, `localhost`, `::1`이 그 거절에 들어 있다. `integration_gate/test_http_gate.py`의 `test_refuses_non_loopback_bind`가 그 셋을 본다.

로컬 호출 경로의 `GET`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS`, `TRACE`, `CONNECT`, `FOO`는 405 `METHOD_NOT_ALLOWED`와 `Allow: POST`다. 같은 파일의 `test_unsupported_paths_methods_and_actions`가 그것을 본다. `POST` 본문은 `application/json`만 받는다. 다른 미디어 유형은 415다.

응답을 만드는 `_send`는 `Content-Type`, 길이, `Cache-Control: no-store`, `X-Content-Type-Options`, 전송·운영 표식, 추적 식별자를 넣는다. `Access-Control-Allow-Origin`을 비롯한 CORS 헤더는 코드에 없다. `Origin`을 읽지 않는다. `Host`로 거절하지 않는다. 이 세션이 돌린 시험은 §8에 있다.

브라우저의 교차 출처 `POST`가 `Content-Type: application/json`이거나 `X-Request-Id`를 보내면 프리플라이트 `OPTIONS`가 먼저 간다. 405이고 CORS 헤더가 없으면 브라우저는 본 `POST`를 보내지 않는다.

상거래 결합 문서 `docs/http-integration-gate-apps-bind.md`는 같은 사실을 적는다. 어댑터는 `X-Request-Id`와 `X-Correlation-Id`를 보내므로 브라우저 요청은 프리플라이트가 필요하다. 브라우저에서는 데스크가 불가이고, 스텁으로 내려가지 않는다. 라이브 관문을 도는 경로는 Node 어댑터 시험이다. 브라우저 경로는 kix-protocol의 관문 변경이 필요하다. 그 문서는 이 앱이 관문 앞에 프록시를 두지 않는다고 적는다. 이 결정은 그 저장소에 프록시를 제안하지 않는다.

어댑터의 `baseUrl`은 명시적 `http://127.0.0.1:<port>`만 받는다. `https`, `localhost`, 포트 생략, 다른 호스트는 클라이언트에서 거절된다. 웹 개발 서버는 `vite.config.ts`와 `package.json`의 `dev` 스크립트가 포트 5173이다. `server.host`와 `--host`는 `0.0.0.0`이다. 페이지 출처는 브라우저가 연 주소다. `http://127.0.0.1:5173`과 `http://localhost:5173`은 다른 출처다. `strictPort`는 없다. 포트가 이미 쓰이면 Vite가 다른 포트를 고를 수 있다. 그 다른 포트는 이 결정의 허용 출처가 아니다.

[준비 런타임](../contracts/READINESS_RUNTIME.md)의 보류 목록에 `kix-commerce-apps` 결합이 있다. 그 문장은 준비 경계의 성공이 앱 결합을 성립시키지 않는다는 뜻이다. 공개 배포와 `0.0.0.0` 기본 노출도 같은 목록에 있다. [공개 엔드포인트 계획](../operations/PUBLIC_ENDPOINT_READINESS_PLAN.md)은 CORS 허가가 인증이 아니라고 적는다.

## 3. 비교

| 갈래 | 내용 | 처리 |
|---|---|---|
| (1) 명시적 루프백 출처의 옵트인 CORS | 기본 꺼짐. 켠 뒤에만 아래 §5의 출처 하나에 프리플라이트와 응답 읽기를 연다. 바인드는 `127.0.0.1` | 채택 제안. R-11이 허용한 구현 범위 안이다 |
| (2) 관문을 닫아 두고 Node 시험만 라이브 경로로 둔다 | 코드는 그대로다. 브라우저 프리플라이트는 계속 405다. 상거래 결합 문서가 이미 그렇게 적는다 | 채택하지 않음. 브라우저가 관문에 닿는 방식을 열지 않는다. 다음 노드 명세는 이 갈래를 고르면 그 문서가 이름 하는 문서만 고치라고 한다 |
| (3) 그 밖의 방식 | 아래에서 각각 거절한다 | 채택하지 않음 |

(3)으로 검토하고 거절한 방식:

- 상거래 앱의 개발 프록시. 그 저장소의 결합 문서가 프록시를 두지 않는다고 적고, 이 노드도 거기에 프록시를 제안하지 말라고 한다.
- kix-protocol 안의 두 번째 리스너나 중계. R-11의 구현은 기존 루프백 관문의 동작 변경이다. 새 홉은 출처 결정을 없애지 않는다.
- `0.0.0.0`, 공개 호스트, 터널. 프로그램 결정 §5의 공개 운영 엔드포인트 잠금이고, 이 노드의 제약이다.
- `Access-Control-Allow-Origin: *`, 요청 출처를 그대로 반사, 자격 증명 허용, 포트 범위, `localhost`·`::1`·사설망 주소를 루프백과 같은 것으로 보는 정규식. §4가 그 이유를 적는다.
- 새 프로토콜 명령, 인증 스킴, `actor`를 로그인으로 읽는 변경. 이 노드의 산출물이 아니다.

(2)는 브라우저에서 오는 호출을 지금처럼 프리플라이트에서 멈춘다. Node·curl·파이썬은 CORS를 적용하지 않으므로 오늘도 관문에 닿는다. 그 경로는 유지된다. (1)을 켜도 `Origin`이 없는 요청은 오늘과 같은 응답이다.

## 4. 위협 모델

CORS는 브라우저가 스크립트에 응답을 보여줄지와, 단순하지 않은 요청을 보내기 전에 프리플라이트를 통과시킬지를 정한다. 같은 기계의 비브라우저 클라이언트는 오늘도 `127.0.0.1`로 `POST`할 수 있다. (1)은 그 사실을 인증으로 바꾸지 않는다.

### DNS 리바인딩

공격자 이름이 희생자 브라우저에서 `127.0.0.1`로 풀려도, 그 문서의 출처는 공격자 이름이다. `http://127.0.0.1:5173`이 아니다. 허용 목록이 그 문자열 하나이고 다른 출처를 반사하지 않으면 프리플라이트는 거절된다. 브라우저는 `application/json` `POST`를 보내지 않는다.

관문은 `Host`로 라우팅하지 않는다. 리바인딩된 이름의 TCP 연결이 `127.0.0.1`에 도착하면 오늘도 처리한다. 브라우저가 `http://127.0.0.1:8765`로 보내면 `Host`는 그 주소다. 문서 자체가 리바인딩된 이름이고 요청 대상도 그 이름이면 `Host`는 공격자 이름이다. §5는 플래그가 켜졌을 때 그 `Host`를 거절한다. 플래그가 꺼져 있으면 `Host` 검사는 더하지 않는다. 꺼진 동작은 오늘과 같다.

공개 페이지가 루프백을 호출할 때 브라우저가 `Access-Control-Request-Private-Network: true`를 요구하는 경우가 있다. 이 결정은 그 헤더를 허용하지 않고 `Access-Control-Allow-Private-Network`를 보내지 않는다. 허용 페이지와 관문은 둘 다 IPv4 루프백이라 같은 주소 공간이다. 이 세션은 브라우저를 실행하지 않았다. 이후 브라우저가 루프백에서 루프백으로 가는 요청에 그 헤더를 필수로 바꾸면, 조용히 허용하지 않고 새 결정으로 연다.

### 다른 로컬 출처

다음은 허용 문자열과 다르다. 플래그가 켜져도 프리플라이트는 405이고 CORS 헤더가 없다.

- `http://localhost:5173`, `http://[::1]:5173`, `https://127.0.0.1:5173`
- 다른 포트. 5174를 포함해 Vite가 비어 있는 다음 포트를 고른 경우
- 사설·링크 로컬 주소, `null`, 확장 프로그램 출처
- 끝이 `/`이거나 공백이 있거나 사용자 정보가 있는 값

웹 개발 서버가 `0.0.0.0:5173`에 붙어 있어도 관문은 따라가지 않는다. 랜 주소로 연 페이지는 위 거절에 들어간다. 그 페이지의 브라우저는 개발 기계의 관문이 아니라 자기 쪽 루프백을 보게 된다. 상거래 서버의 `0.0.0.0`은 그 저장소의 현재 사실이고, 이 결정이 관문 바인드를 넓히는 근거가 아니다.

허용 출처의 페이지는 관문을 호출할 수 있다. 그것이 이 결정이 여는 개발 페이지다. 그 페이지에 실린 스크립트도 같은 권한이다. CORS는 그 페이지의 공급망을 검사하지 않는다.

### 자격 증명

관문은 쿠키를 읽지 않는다. `actor`는 픽스처 문자열이다. OpenAPI 소비 절은 `actor`를 인증 결과로 믿지 말라고 적는다. `Access-Control-Allow-Credentials`를 보내지 않는다. `Authorization`과 `Cookie`는 허용 요청 헤더가 아니다. 자격 증명 모드와 `*`의 조합은 만들지 않는다. 공개 엔드포인트 계획의 문장 그대로, CORS 허가는 인증이 아니다.

단순 요청은 프리플라이트 없이 서버에 닿을 수 있다. `GET /health`가 그렇다. CORS 헤더가 없으면 스크립트는 본문을 읽지 못한다. JSON이 아닌 `POST`는 415이고 `Core.execute`에 들어가지 않는다. 이 결정은 그 거절을 느슨하게 하지 않는다. 플래그가 꺼져 있으면 단순 요청에도 CORS 헤더를 붙이지 않는다.

## 5. 채택 제안의 방식

다음 노드가 구현하는 방식은 이 절뿐이다. 여기 없는 출처, 시간, 헤더를 더하지 않는다.

### 플래그

- CLI `--browser-origin`. 기본값은 없다. 없으면 CORS는 꺼져 있다.
- 값이 정확히 `http://127.0.0.1:5173`일 때만 켠다. 다른 값, 빈 값, 두 번 지정은 시작을 거절한다. 거절 코드는 `REFUSING_BROWSER_ORIGIN`.
- 환경 변수나 설정 파일로 켜지지 않는다.
- 꺼져 있으면 헤더, 상태, 본문, `Host` 처리가 오늘과 같다. `test_unsupported_paths_methods_and_actions`의 405 기대는 그대로다. 그 시험을 끄지 않는다.

### 바인드와 Host

- `--host`의 기본과 거절은 그대로다. `127.0.0.1`만 듣는다.
- 플래그가 켜졌을 때 `Host`는 `127.0.0.1` 또는 `127.0.0.1:<이 프로세스가 듣는 포트>`만 받는다. 그 밖은 400이고 CORS 헤더가 없다. `Host`가 없거나 두 개면 같은 거절이다.
- 플래그가 꺼져 있으면 이 `Host` 검사를 넣지 않는다.

### 프리플라이트

대상 경로는 오늘의 세 경로뿐이다. 로컬 호출, `/health`, `/ready`. 그 밖은 404다.

플래그가 켜져 있고 메서드가 `OPTIONS`이며 아래가 모두 맞으면 204, 본문 없음, 코어를 호출하지 않고, 동시 처리 슬롯을 잡지 않는다.

- `Origin` 헤더가 하나이고 값이 허용 출처와 한 글자도 같다.
- `Access-Control-Request-Method`가 하나다. 로컬 호출은 `POST`, 두 프로브는 `GET`.
- `Access-Control-Request-Headers`가 없거나, 쉼표로 나눈 토큰을 공백을 없애고 소문자로 봤을 때 집합 `{content-type, x-request-id, x-correlation-id}`의 부분집합이다. 중복 토큰은 거절이다.
- `Access-Control-Request-Private-Network`가 없다.

맞는 프리플라이트의 헤더:

- `Access-Control-Allow-Origin: http://127.0.0.1:5173`
- `Access-Control-Allow-Methods`: 그 경로의 `POST` 또는 `GET` 하나
- `Access-Control-Allow-Headers: content-type, x-request-id, x-correlation-id`
- `Allow`: 같은 메서드
- `Vary: Origin`
- 오늘의 비운영 표식과 `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`

보내지 않는 헤더: `Access-Control-Allow-Credentials`, `Access-Control-Allow-Private-Network`, `Access-Control-Max-Age`, `*`.

하나라도 어긋나면 오늘의 405 `METHOD_NOT_ALLOWED`와 `Allow`이다. CORS 헤더를 붙이지 않는다. 쿼리, 헤더 크기, `Transfer-Encoding`, `Expect`의 기존 거절은 메서드 분기보다 앞이다. 그 순서를 유지한다.

### 실제 요청

`Origin`이 없는 요청은 플래그와 관계없이 오늘과 같은 헤더다. Node 시험이 이 경우다.

플래그가 켜져 있고 `Origin`이 하나이며 허용 출처와 같으면, 이미 만들 응답에 다음만 더한다. `Access-Control-Allow-Origin`은 그 출처, `Vary: Origin`. 상태와 본문은 바꾸지 않는다. 성공과 4xx·5xx에 같이 붙인다. 자격 증명 헤더는 붙이지 않는다.

다른 `Origin`이면 CORS 헤더 없이 오늘의 상태와 본문이다. 미디어 유형은 계속 `application/json`만이다.

### 다음 노드의 문서 문장

구현 노드가 [READINESS_RUNTIME.md](../contracts/READINESS_RUNTIME.md)와 [OpenAPI README](../contracts/openapi/README.md)의 소비 절을 고친다. 이 노드가 그 파일을 고치지 않는 이유는 §7이다. 고칠 때 쓸 문장은 아래다.

- 브라우저 전송은 `--browser-origin http://127.0.0.1:5173`일 때만 열린다. 기본은 꺼져 있다.
- 그 전송은 운영 결합, 공개 엔드포인트, 인증, 프로토콜 정본이 아니다.
- 보류 목록의 `kix-commerce-apps` 결합은 그대로 둔다. 옵트인 전송이 그 보류를 끝내지 않는다고 한 문장 덧붙인다.
- 소비 절의 "상거래 앱 결합도 아니다"는 유지한다. 위에 같은 옵트인 문장을 덧붙인다.

OpenAPI 문서에 서버 URL, 보안 스킴, 명령을 넣지 않는다. `docs/contracts/`는 구현 노드의 변경이다.

## 6. 기존 커버리지

AGENTS.md §7. 이 노드는 시험을 추가하지 않는다. 구현과 새 시험은 `gate-browser-access`다.

| 요구·성질 | 기존 근거 | 분류 |
|---|---|---|
| 비루프백 바인드 거절 | `integration_gate/test_http_gate.py` `test_refuses_non_loopback_bind`, `test_loopback_refusal_still_applies_with_a_readiness_directory` | 충분. 이 결정이 바인드를 바꾸지 않음 |
| 로컬 호출의 `OPTIONS` 405와 `Allow: POST` | 같은 파일 `test_unsupported_paths_methods_and_actions` | 충분. 플래그가 꺼진 동작. 켜진 프리플라이트는 미커버 |
| `/health`의 `OPTIONS` 405 | `route`가 프로브의 비GET을 405로 보낸다. 위 시험은 그 경로의 `OPTIONS`를 돌리지 않는다 | 부분. 코드 경로. 전용 단정이 없음 |
| CORS 헤더가 없음 | `_send`에 해당 헤더가 없다. 시험은 `Access-Control-Allow-Origin` 부재를 단정하지 않는다 | 부분. 상거래 결합 문서가 부재를 적는다 |
| JSON만 수용 | `test_transport_limits_and_malformed_bodies`의 415 | 충분. 플래그가 꺼진 동작 |
| 허용 출처의 프리플라이트 204, 다른 출처 405, 자격 증명 헤더 부재, 플래그가 켜진 `Host` 거절 | 없음 | 미커버. 다음 노드 |
| 브라우저가 5173에서 프리플라이트를 통과함 | 이 세션은 브라우저를 실행하지 않음 | 미커버. 상거래 노드 `browser-gate-path`의 선행이 구현 노드다 |

## 7. 계약과 구현의 분류

AGENTS.md §8.

| 항목 | 분류 | 이유 |
|---|---|---|
| 꺼진 상태의 405, JSON 전용, `127.0.0.1` 바인드 | A. 계약과 맞음 | 시험과 `_send`, `build_server`가 같다. 이 노드가 코드를 바꾸지 않음 |
| 공개 호스트 금지 | A. 잠금과 맞음 | 프로그램 결정 §5, R-11, 이 문서 §5 |
| 켜진 CORS의 헤더와 204 | B. 지금 계약에는 없고, 이 문서가 다음 노드의 초안 규칙으로 정의 | OpenAPI는 CORS를 적지 않는다. 확정은 검토·병합 뒤 구현 노드가 코드와 소비 절에 옮긴다 |
| `Host`를 오늘 거절하지 않음 | B. 관찰된 특성 | 꺼진 상태에서는 유지한다. 켜진 상태의 거절은 §5의 제안이다 |
| Vite가 5173 다음 포트를 고를 수 있음 | B. 상거래 저장소에서 관찰 | 허용 목록을 넓히지 않는다. 그 포트의 브라우저는 닫힌 채로 둔다 |
| 명시적 계약 위반 | C에 해당하는 항목 없음 | 잠금 파일, `reference/v0.3-rc1/**`, 관문 코드를 바꿔야만 하는 위반을 찾지 못했다 |

`docs/contracts/`는 두 workflow 분류기에서 검증기 입력이다. 이 노드가 그 경로를 고치면 문서 전용 생략이 아니라 전체 검증이 된다. 구현과 그 문서 수정은 다음 노드로 남긴다. 이 파일은 `docs/decisions/`라서 분류기상 문서 전용이다. workflow를 고치지 않았다.

## 8. 이 세션의 확인

명령과 결과는 작업 보고의 증거 표에 있다. 여기 숫자를 옮겨 적지 않는다.

- `python3 -m unittest integration_gate.test_http_gate`
- 잠금 blob을 작업 전과 문서 추가 뒤에 다시 계산
- `reference/v0.3-rc1`와 잠금 파일의 작업 트리 차이가 없음

## 9. 비주장

- 운영 준비, 공개 엔드포인트 자격, 인증, 실자금 안전, 상거래 앱 결합 완료를 주장하지 않는다.
- 브라우저로 프리플라이트를 통과시켰다고 주장하지 않는다. 상거래 개발 서버를 띄우지 않았다.
- DNS 리바인딩이 이 규칙으로 사라졌다고 주장하지 않는다. §4는 브라우저 출처와, 플래그가 켜진 때의 `Host`에 한정한다. 비브라우저 로컬 호출은 오늘과 같다.
- 이후 브라우저의 로컬 네트워크 권한 창을 이 문서가 만족한다고 주장하지 않는다.
- exact-head CI는 커밋과 준비된 PR 뒤에서만 생긴다. 이 세션은 커밋, 푸시, PR, 이슈, 댓글을 만들지 않는다. 이전 SHA의 녹색을 이 문서의 통과로 옮기지 않는다.
- 저자 측 점검과 이 세션의 명령 기록은 비작성자 exact-HEAD 검토가 아니다.
