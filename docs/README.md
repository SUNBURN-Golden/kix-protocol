# KIX 문서 색인

**현행 개발계획 정본은 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) 하나입니다.** 현재 승인·금지·진행 순서는 §1·§5, 4단계 backend 비교는 §9를 따릅니다. 이 색인은 별도의 승인 문서가 아닙니다.

**[루트 README](../README.md)의 역할:** 프로젝트와 현재 기준·잠금·금지·읽는 순서를 안내하는 최초 입구.
**이 `docs/README.md`의 역할:** 같은 정본 아래 계약·검증·보존 자료의 위치를 안내하는 색인.

## 현재 문서 — 이 순서로 읽기

1. [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) — 현재 계획·승인 범위.
2. [기준 commit·태그 표](status/BASELINES.md) — 현재 main, 고정 R1 태그, PR 검토 SHA, #11 실험을 구분. [main 상태 정합 기록](status/MAIN_STATE_20260928.md) — 2026-09-25~27 병합 범위, hosted CI 공백, 열린 결정 D-1~D-3.
3. [모델 1 결정](decisions/AUTHORITY_MODEL_1.md) — 체인 권위 / 오프체인 위임 실행. R2·(a) 착수 승인이 아님.
4. [수명 계약 초안](contracts/STATE_LIFECYCLE.md), [열린 입력·답할 주체](contracts/FIRST_BATCH_OPEN_INPUTS.md).
5. [계약 불변식·비교 모델의 한계](contracts/CONTRACT_INVARIANTS.md), [첫 묶음 실행 근거](../validation/2026-09-16-first-batch/README.md).
6. [측정 계약](contracts/PERFORMANCE_MEASUREMENT.md), [고정 smoke 조건](contracts/PERFORMANCE_BASELINE_V4.md)(역사적 debug 논리 서명, 제품 p99 아님), [Task 004 장치 메모](../validation/2026-09-25-task-004-perf-measurement/README.md).
7. [잠금의 실제 CI 경로](status/LOCK_ENFORCEMENT.md), [위생 목록 — 실행 금지](CODE_HYGIENE_BACKLOG.md).
8. [원래 32개 항목](status/ORIGINAL_32_STATUS.md), [M 제외 부분 앵커](status/PARTIAL_ANCHOR_COUNTS.md), [#11 태그 보존](status/PR11_PRESERVATION.md).

## 계약 전용 OpenAPI

[계약 전용 OpenAPI](contracts/openapi/README.md)는 `reference/v0.3-rc1/protocol_contract.json`의 로컬 호출 명령을 담은 OpenAPI 3.1 핀이다. 그 핀은 라이브 서버를 선언하지 않고, 운영 엔드포인트도 없다. 같은 40개 명령과 같은 로컬 호출 경로를 루프백에서 부르는 비운영 통합 관문이 따로 있다. 공개 호스트·실 PG·KYC·공연장·은행 연동이 아니며, 로컬 HTTP 성공은 운영 승인이 아니다. 선택적 로컬 파일 저널과 재시작 재생은 [준비 런타임 경계](contracts/READINESS_RUNTIME.md)에 적는다. 그 저장은 프로토콜 정본이 아니고, 공개 배치·운영 적합·외부 연동의 승인이 아니다.

`reference/v0.1/KIX_프로토콜_통합명세_v0.1.md` §9.1의 “HTTP 서버·OpenAPI 서비스는 아직 없다”는 그 명세를 쓰던 시점의 기록이다. 그 파일은 당시 패키지 해시에 묶인 역사 증거라 본문을 고치지 않았다. 예매·리셀·검표 목과 신용 목의 “HTTP 서버는 없다”는 각 목 함수에 대한 설명으로 그대로 둔다.

## 역사 문서와 증거

[루트 역사 문서 목록](../README.md#6-역사-문서--현행-계획-아님)의 V24·V23·V2·BLUEPRINT·ROADMAP 등은 현행 계획이 아닙니다. 특히 V24의 자동 R2 진행은 현재 금지입니다. 역사 문서의 상단 경고 뒤 본문은 당시 기록으로 보존합니다.

[ADR-0001](adr/0001-ktx-authority-commit-recovery.md)의 안전 관계와 [보안 보완](PROTOCOL_HARDENING.md)·[저장 조사](STORAGE_INVESTIGATION.md)·[회귀 검증](RUNTIME_VALIDATION.md)은 근거별 범위로 읽습니다. 옛 계획의 승인 효력을 폐기했다고 안전 규칙이나 사건 기록을 삭제하지 않습니다.

모델 1·첫 묶음 승인은 backend 채택·커널 전환 완료·실금전 운영 승인과 다릅니다. 미정 항목, 두 잠금 blob, R2 금지, (a) 보류, 위생 일괄 금지는 유지합니다.
