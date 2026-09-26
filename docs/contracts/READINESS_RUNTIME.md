# 준비 런타임 경계

이 문서는 프로토콜 정본이 아니다. 개발계획 정본은 `docs/DEVELOPMENT_PLAN.md`이고, 명령의 의미는 기존 FSM과 `reference/v0.3-rc1`의 `Core.execute`에 있다. `readiness/`는 그 확정 결과를 한 프로세스의 로컬 파일에 남겨 재시작 뒤에 재생하는 래퍼다. 저장소가 프로토콜 진실을 대신하지 않는다.

표식은 코드와 통합 관문 문서에서 모두 꺼 둔다.

| 표식 | 값 | 의미 |
|---|---|---|
| `protocolTruth` | `false` | 저널 레코드는 프로토콜 명령이나 권위 있는 상태가 아니다 |
| `productionConformance` | `false` | 로컬 재생은 운영 적합 선언이 아니다 |
| `productionReadiness` | `false` | `/health`와 `/ready`는 프로세스 프로브다. 운영 준비가 아니다 |
| `productionEndpoint` | `false` | 공개 운영 엔드포인트가 아니다 |
| FSM `durable` | `false` | 래퍼가 FSM 뷰의 이 플래그를 켜지 않는다 |

## 파일 저널

스키마 1 파일은 `journal.v1`이다. 헤더는 `KIXRDY01`과 버전이다. 레코드는 길이와 정규화 JSON, CRC32다. 한 레코드를 쓴 뒤 `fsync`한다. 한 디렉터리에는 작성자가 하나다. 잠금을 못 얻으면 `JOURNAL_LOCKED`로 닫는다.

복구 규칙은 두 갈래다.

- 끝의 불완전한 프레임은 찢긴 쓰기다. 그 꼬리만 버리고, 체크섬이 맞는 앞선 레코드는 재생한다.
- 길이가 맞는 프레임의 체크섬이 틀리면 `CHECKSUM_MISMATCH`다. 그 레코드를 건너뛰거나 파일 내용을 추측해 고치지 않는다.

FSM 레코드는 그 기계의 `export_journal` 항목 하나다. 재시작은 공개 `restore`로 그 항목을 다시 적용한다. 통합 관문의 `core_commit`은 `operationId`, `actor`, `action`, `body`와 영수증 다이제스트다. 재생한 영수증 다이제스트가 기록과 다르면 `RECEIPT_MISMATCH`로 닫고 요청을 받지 않는다.

같은 멱등 키나 같은 `operationId` 지문은 저장된 결과를 다시 준다. 경제 효과와 소유 이전을 두 번 적용하지 않는다. 응답을 돌려주기 전에 기록이 내구성 있게 끝나지 않았으면 성공으로 반환하지 않는다. 메모리만 앞서고 기록이 실패하면 그 프로세스는 더 이상 명령을 받지 않는다.

## 버전 이전

`readiness/migrate.py`의 `migrate`는 스키마 1에서 스키마 1로 가는 항등 함수다. 다른 원본 버전은 `UNSUPPORTED_SCHEMA`다. 필드를 짐작해 바꾸거나, 모르는 키를 버리거나, 조용히 올리거나 내리지 않는다. 이후 스키마는 그 원본 버전용 함수가 이 모듈에 생기고 `migrate`가 그 함수를 호출할 때만 읽을 수 있다.

## 통합 관문

기본 바인드는 `127.0.0.1`이다. `0.0.0.0`과 그 밖의 호스트는 거절한다. 동시 처리 상한은 기본 8이고, 넘치면 `OVERLOADED`로 거절하며 줄을 무한히 만들지 않는다. 코어 호출은 한 스레드에서만 실행한다. 종료 중에는 `/health`만 살리고 명령은 `NOT_READY`다. 요청에는 `X-Request-Id`와 `X-Correlation-Id`를 붙이고, 감사 줄은 stderr의 JSON이다. 감사 줄은 본문을 담지 않는다.

`--readiness-dir`가 없으면 재시작 뒤에 인메모리 상태는 사라진다. 디렉터리를 줘도 `x-kix-limits.durableAcrossRestart`의 기본 표식은 `false`다. 준비 응답의 `localFileJournal`은 그 파일 재생이 켜졌는지만 말한다.

저널 레코드 수와 바이트 상한을 넘기는 새 커밋은 `JOURNAL_BUDGET`이다. 이미 기록된 호출의 재생은 그 상한으로 막지 않는다.

## 이 경계가 보인 것

통제된 로컬 프로세스에서 아래를 검사한다.

- 정산 커밋의 `confirmed_cash`와 한 번의 배분이 재시작과 찢긴 쓰기 뒤에 한 번만 남는다.
- 예약 슬롯 점유는 동시에 두 요청이 들어와도 하나다.
- 리셀 수락은 버전을 한 단계만 올린다.
- 신용 인출의 `outstanding_exposure`는 한 번만 늘어난다.
- 입장 소비는 `CONSUMED` 한 번이고, 버전은 2에서 멈춘다.
- 죽인 통합 관문 프로세스는 같은 `create_event`를 다시 적용하지 않는다.

검사 명령과 이번 실행 결과는 `validation/2026-09-26-prod-readiness-infra/README.md`에 둔다.

## 보류

다음은 이 경계의 성공으로 성립하지 않는다.

- 공개 배포, DNS, TLS 제품화, `0.0.0.0` 기본 노출
- 실 PG, 은행, KYC, 공연장, 체인 최종성, 외부 정확히 한 번
- 운영 적합 또는 운영 준비 완료라는 주장
- R2, 복제, 합의, 자체 저장 엔진, 백엔드 선택
- `kix-commerce-apps` 결합
- 프로토콜 계약에 없는 새 명령
