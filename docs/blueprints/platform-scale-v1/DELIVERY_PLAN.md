# 플랫폼 확장 후속 작업 제안

2026-10-02 · 설계 산출물. 작업문서·dispatch 입력·승인 결정이 아니다.

기존 프로그램은 Protocol 82 + Commerce 36 = 118개다. 아래 PS ID는 제안 내 추적용이며 기존 task key를 대체하지 않는다. 중복 범위를 먼저 기존 노드에 매핑하고, 필요한 계획 개정을 승인받은 뒤 orchestrator가 작업문서를 발급한다. 이 문서로 pending/active/완료 상태, 의존성, manifest hash, 실행 포인터를 바꾸지 않는다.

| 제안 | 산출물 | 제안 내 선행 | 기존 영역과 연결 | 인수 조건 |
|---|---|---|---|---|
| PS-01 | 경합 단위·식별·라우팅 ADR | 없음 | RS-0/RS-1, 입장 제어 계약 | 단일 좌석 계약과 256슬롯 페이지 후보의 적용 범위 명시; 세대·명령·epoch 분리 |
| PS-02 | 조회·검색·재생 계약 | PS-01 | Protocol 적합성/인증 export, Commerce 조회 | source cut·watermark·접근 scope·cursor·gap·역순 규칙 확정 |
| PS-03 | 리셀 다중 채널 체결·결제 계약 | PS-01 | RS 공개 권리, Commerce 구매/리셀, Finance | 매물/잠금/권리 구분; 조건부 체결·UNKNOWN·자금 대사 정의 |
| PS-04 | backend 및 실행 partition 적합성 | PS-01 | Track K, R-4/R-6, RS-3b | 승인 backend 선행; 내구 첫 결과/inbox/outbox와 fencing 시험. 위임은 Grant 게이트 별도 |
| PS-05 | 조회 투영 구현 후보 | PS-02 | Protocol producer/SDK 적합성, Commerce adapter | 승인된 입력 tuple; 중복·역순·재구축·권한 분리 local 증거 |
| PS-06 | Commerce 거래 연결 후보 | PS-03, PS-04, PS-05 | Commerce journey/adapter, Finance 대사 | UI context fencing; UNKNOWN 뒤 새 쓰기 차단; 확정 영수증 연결 |
| PS-07 | 규모·혼잡·장애 시험 | PS-04, PS-05, PS-06 | RS-4, 성능 측정 계약 | L1~L3 경로별 결과, 합성/실제 분리, hot key·복구·비용 보고 |
| PS-08 | 운영 적합성 검토 패키지 | PS-07 | 별도 운영·외부 연동 게이트 | 수치 SLO와 증거 보존 정책 승인; 독립 검토; 배포는 추가 승인 |

문서 작업 PS-01~03은 기존 승인 범위 안에서 작업문서로 구체화할 수 있다. 구현 PS-04 이후는 표의 선행만 만족한다고 착수할 수 없다. 현행 개발계획의 backend·위임·운영 잠금과 프로그램 개정 조건을 함께 만족해야 한다. 예를 들어 승인 backend가 없으면 PS-04는 BLOCKED다.

L1 합성 조회 시험은 PS-02 계약 확정 이후 별도 승인 범위에서 먼저 수행할 수 있다. PS-07 전체 완료나 체인 규모 검증으로 계산하지 않는다. PS-08의 검토 완료 역시 배포·활성화 승인이 아니다.

## 검증 보고서 필수 필드

- source commit/tree, profile, schema/SDK/producer tuple, chain protocol/config, backend/config.
- 실물/합성 데이터 구분, 공연·슬롯·활성 권리·매물·누적 사건·명령 수.
- 부하 seed/분포, 동시 입장, 요청 도착률, 실제 성공 TPS, reject/UNKNOWN/retry 수.
- 지연 분포, 최고 backlog age/bytes, 인덱스 lag, 복구 cut과 복구 시간, 저장량·체인 비용.
- 불변식별 oracle/분모/위반 수, 중단 기준, 미시험 경로, 정확한 수용/차단 판정.

용량 단계는 S1 → S2 → S3 순서다. 직전 단계에서 안전성 위반이 있으면 다음 단계로 올리지 않는다. 성능 기준이 미정이면 결과 수집만 가능하고 수용 판정은 내리지 않는다.
