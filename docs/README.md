# KIX 문서 색인

**현행 개발계획 정본은 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) 하나입니다.** 현재 승인·금지·진행 순서는 §1·§5, 4단계 backend 비교는 §9를 따릅니다. [R-1](decisions/PROGRAM_ROADMAP_20260930.md)(#81 병합)의 명시한 범위는 이전 계획에 우선합니다. 이 색인은 별도의 승인 문서가 아닙니다.

**[루트 README](../README.md)의 역할:** 프로젝트와 현재 기준·잠금·금지·읽는 순서를 안내하는 최초 입구.
**이 `docs/README.md`의 역할:** 같은 정본 아래 계약·검증·보존 자료의 위치를 안내하는 색인.

## 현재 문서 — 이 순서로 읽기

1. [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) — 현재 계획·승인 범위.
2. [기준 commit·태그 표](status/BASELINES.md) — 현재 main, 고정 R1 태그, PR 검토 SHA, #11 실험을 구분. [main 상태 정합 기록](status/MAIN_STATE_20260928.md) — 2026-09-25~27 병합 범위, hosted CI 공백, D-1~D-3 결정 전 사실. [프로그램 결정 D-1~D-3](decisions/PROGRAM_DECISIONS_20260928.md) — 2026-09-28 #73 병합으로 승인. Track K/P, Wave 게이트, readiness 저널 한도, 유지되는 잠금과 해제 조건.
3. [모델 1 결정](decisions/AUTHORITY_MODEL_1.md) — 체인 권위 / 오프체인 위임 실행. R2·(a) 착수 승인이 아님.
4. [수명 계약 초안](contracts/STATE_LIFECYCLE.md), [열린 입력·답할 주체](contracts/FIRST_BATCH_OPEN_INPUTS.md).
5. [계약 불변식·비교 모델의 한계](contracts/CONTRACT_INVARIANTS.md), [첫 묶음 실행 근거](../validation/2026-09-16-first-batch/README.md).
6. [측정 계약](contracts/PERFORMANCE_MEASUREMENT.md), [고정 smoke 조건](contracts/PERFORMANCE_BASELINE_V4.md)(역사적 debug 논리 서명, 제품 p99 아님), [Task 004 장치 메모](../validation/2026-09-25-task-004-perf-measurement/README.md).
7. [잠금의 실제 CI 경로](status/LOCK_ENFORCEMENT.md), [위생 목록 — 실행 금지](CODE_HYGIENE_BACKLOG.md).
8. [원래 32개 항목](status/ORIGINAL_32_STATUS.md), [M 제외 부분 앵커](status/PARTIAL_ANCHOR_COUNTS.md), [#11 태그 보존](status/PR11_PRESERVATION.md).
9. [범위 편입 결정 기록(2026-09-29)](decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md) — 선택적 자체 토큰 계층과 확장형 권리·재고·검표 계층. PR #79 병합으로 범위 편입. 후속 조건은 R-1 및 개발계획 §19를 따른다. 토큰 발행·새 coin/TIX 잠금 유지. [개발계획 §18](DEVELOPMENT_PLAN.md#18-2026-09-29--선택적-자체-토큰-계층과-확장형-권리재고검표-계층의-범위-편입).

## 현재 프로그램 정의

Protocol 82(초안 67 + 편입 대기 15), Commerce 36(초안 10 + 편입 대기 26), 전체 118개. Finance 8개는 Protocol 부분집합입니다.
- [R-1 범위·조건](decisions/PROGRAM_ROADMAP_20260930.md)
- [Protocol 비실행 초안](aiops/KIX_PROGRAM_DRAFT.json) / [편입 대기](decisions/PROGRAM_ROADMAP_20260930_PENDING.json)
- [Protocol 후속 적합성](aiops/PROTOCOL_COMPLETION_DESIGN_KO.md) / [Finance 설계](aiops/FINANCE_COMPLETION_DESIGN_KO.md)
- [등록 범위·시작 절차](aiops/REGISTRATION_SCOPE_APPROVAL_KO.md) / [노드별 병합 경계](aiops/PROGRAM_ASTRA_DELEGATION.md)

범위 승인은 #81 병합으로 기록됐지만 편입 대기는 보호된 선행 완료와 별도 계획 개정까지 유지합니다. 비실행 초안의 `active`는 실행 중·완료가 아닙니다.

## 계약 전용 OpenAPI

[계약 전용 OpenAPI](contracts/openapi/README.md)는 `reference/v0.3-rc1/protocol_contract.json`의 로컬 호출 명령을 담은 OpenAPI 3.1 핀이다. 그 핀은 라이브 서버를 선언하지 않고, 운영 엔드포인트도 없다. 같은 40개 명령과 같은 로컬 호출 경로를 루프백에서 부르는 비운영 통합 관문이 따로 있다. 공개 호스트·실 PG·KYC·공연장·은행 연동이 아니며, 로컬 HTTP 성공은 운영 승인이 아니다. 선택적 로컬 파일 저널과 재시작 재생은 [준비 런타임 경계](contracts/READINESS_RUNTIME.md)에 적는다. 그 저장은 프로토콜 정본이 아니고, 공개 배치·운영 적합·외부 연동의 승인이 아니다.

`reference/v0.1/KIX_프로토콜_통합명세_v0.1.md` §9.1의 “HTTP 서버·OpenAPI 서비스는 아직 없다”는 그 명세를 쓰던 시점의 기록이다. 그 파일은 당시 패키지 해시에 묶인 역사 증거라 본문을 고치지 않았다. 예매·리셀·검표 목과 신용 목의 “HTTP 서버는 없다”는 각 목 함수에 대한 설명으로 그대로 둔다.

## 청사진 색인 — 설계 제안, 승인·구현 아님

아래 두 청사진은 2026-09-29 범위 편입([결정 기록](decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md))의 설계 제안이다. 구현·배포·발행을 승인하지 않으며, 후속 작업 정의는 작업문서가 아니다.

| 청사진 | 다루는 것 | 상태 |
|---|---|---|
| [선택적 자체 토큰 발행·운영 계층](blueprints/optional-native-token-v1/README.md) | 용도별 채택 평가, 필수 불변식, Sui 표준 대조, 공급·분배, 경제적 연결, 권한, 거래 결합, 활성화 단계, TIX 자료 등급 | 구체 설계·구현 미완료 |
| [확장형 권리·재고·검표 계층](blueprints/rights-scale-v1/README.md) | 16슬롯 변경 영향 지도, 구조 대안 비교와 권고, 필수 안전 조건, ZK 현재성 설계, 검증 규모 계획 | 설계 제안. 16슬롯 참조 프로파일은 회귀 기준으로 보존 |

닫힌 미병합 [PR #35](https://github.com/BeautifulMind-JT/kix-protocol/pull/35)의 금융·플랫폼 청사진은 이 색인의 항목이 아니다. 역사적 설계 자료로만 참고한다.

## 플랫폼 전체 용량 설계

[100만~3,000만 권리 확장 구조](blueprints/platform-scale-v1/README.md) / [후속 작업 제안](blueprints/platform-scale-v1/DELIVERY_PLAN.md): 공연별 정원과 플랫폼 합산 용량, 리셀 체결·검색 투영·분할·복구·단계별 검증을 구분한다. PR #84 후보를 기반으로 한 설계이며 기존 118개 노드에 자동 편입하거나 운영 성능을 보장하지 않는다.

## 공개 권리 확장 구현 후보

[RS-PUBLIC-1 계약](contracts/RIGHTS_SCALE_PROFILE.md) / [새 Move 패키지와 시험](../reference/rights-scale-v1/README.md): 256슬롯 페이지, 정원 1..65,536. 기존 16슬롯 회귀·ZK는 보존하며, 비공개·위임·운영 완료와 구분한다.

## 역사 문서와 증거

[루트 역사 문서 목록](../README.md#6-역사-문서--현행-계획-아님)의 V24·V23·V2·BLUEPRINT·ROADMAP 등은 현행 계획이 아닙니다. 특히 V24의 자동 R2 진행은 현재 금지입니다. 역사 문서의 상단 경고 뒤 본문은 당시 기록으로 보존합니다.

[ADR-0001](adr/0001-ktx-authority-commit-recovery.md)의 안전 관계와 [보안 보완](PROTOCOL_HARDENING.md)·[저장 조사](STORAGE_INVESTIGATION.md)·[회귀 검증](RUNTIME_VALIDATION.md)은 근거별 범위로 읽습니다. 옛 계획의 승인 효력을 폐기했다고 안전 규칙이나 사건 기록을 삭제하지 않습니다.

모델 1·첫 묶음 승인은 backend 채택·커널 전환 완료·실금전 운영 승인과 다릅니다. 미정 항목, 두 잠금 blob, R2 금지, (a) 보류, 위생 일괄 금지는 유지합니다.

