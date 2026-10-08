# KIX 문서 색인

**현행 개발계획 정본은 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) 하나입니다.** 현재 승인·금지·진행 순서는 §1·§5, 4단계 backend 비교는 §9를 따릅니다. 이 색인은 별도의 승인 문서가 아닙니다.

**[루트 README](../README.md)의 역할:** 프로젝트와 현재 기준·잠금·금지·읽는 순서를 안내하는 최초 입구.
**이 `docs/README.md`의 역할:** 같은 정본 아래 계약·검증·보존 자료의 위치를 안내하는 색인.

## 현재 문서 — 이 순서로 읽기

1. [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) — 현재 계획·승인 범위.
2. [기준 commit·태그 표](status/BASELINES.md) — 현재 main, 고정 R1 태그, PR 검토 SHA, #11 실험을 구분. [main 상태 정합 기록](status/MAIN_STATE_20260928.md) — 2026-09-25~27 병합 범위, hosted CI 공백, D-1~D-3 결정 전 사실. [프로그램 결정 D-1~D-3](decisions/PROGRAM_DECISIONS_20260928.md) — 2026-09-28 #73 병합으로 승인. Track K/P, Wave 게이트, readiness 저널 한도, 유지되는 잠금과 해제 조건.
3. [모델 1 결정](decisions/AUTHORITY_MODEL_1.md) — 체인 권위 / 오프체인 위임 실행. R2·(a) 착수 승인이 아님.
4. [수명 계약 초안](contracts/STATE_LIFECYCLE.md), [열린 입력·답할 주체](contracts/FIRST_BATCH_OPEN_INPUTS.md), [담당자 질문서](status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md)(위치만. 회신·정책 결정이 아니다).
5. [계약 불변식·비교 모델의 한계](contracts/CONTRACT_INVARIANTS.md), [첫 묶음 실행 근거](../validation/2026-09-16-first-batch/README.md).
6. [측정 계약](contracts/PERFORMANCE_MEASUREMENT.md), [고정 smoke 조건](contracts/PERFORMANCE_BASELINE_V4.md)(역사적 debug 논리 서명, 제품 p99 아님), [Task 004 장치 메모](../validation/2026-09-25-task-004-perf-measurement/README.md).
7. [잠금의 실제 CI 경로](status/LOCK_ENFORCEMENT.md), [위생 목록 — 실행 금지](CODE_HYGIENE_BACKLOG.md).
8. [원래 32개 항목](status/ORIGINAL_32_STATUS.md), [M 제외 부분 앵커](status/PARTIAL_ANCHOR_COUNTS.md), [#11 태그 보존](status/PR11_PRESERVATION.md).
9. [범위 편입 결정 기록(2026-09-29)](decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md) — #79 사용자 병합(`5cf4168`)으로 승인. 선택적 자체 토큰 계층과 확장형 권리·재고·검표 계층. 당시 설계·계획 문서화 한정이며 후속 조건부 범위는 [프로그램 로드맵 R-1~R-11](decisions/PROGRAM_ROADMAP_20260930.md)을 따른다. D-1~D-3의 잠금·해제 조건은 유지하며 범위 승인과 실행 시작을 분리한다. [개발계획 §18](DEVELOPMENT_PLAN.md#18-2026-09-29--선택적-자체-토큰-계층과-확장형-권리재고검표-계층의-범위-편입).
10. [.aiops/program.json](../.aiops/program.json) — 현재 노드 입력·canonical 의존성. [감사·병합 판정 표](aiops/PROGRAM_ASTRA_DELEGATION.md), [pending catalogue](decisions/PROGRAM_ROADMAP_20260930_PENDING.json), [확대 후보](aiops/PROGRAM_EXPANSION_20261002_KO.md) — 외부 선행·별도 채택·release 결정을 완료로 간주하지 않는다. 후보 집계 반영은 별도 채택 뒤 개발계획 §17에 따른다.

## 계약 전용 OpenAPI

[계약 전용 OpenAPI](contracts/openapi/README.md)는 `reference/v0.3-rc1/protocol_contract.json`의 로컬 호출 명령을 담은 OpenAPI 3.1 핀이다. 그 핀은 라이브 서버를 선언하지 않고, 운영 엔드포인트도 없다. 같은 40개 명령과 같은 로컬 호출 경로를 루프백에서 부르는 비운영 통합 관문이 따로 있다. 공개 호스트·실 PG·KYC·공연장·은행 연동이 아니며, 로컬 HTTP 성공은 운영 승인이 아니다. 선택적 로컬 파일 저널과 재시작 재생은 [준비 런타임 경계](contracts/READINESS_RUNTIME.md)에 적는다. 그 저장은 프로토콜 정본이 아니고, 공개 배치·운영 적합·외부 연동의 승인이 아니다.

`reference/v0.1/KIX_프로토콜_통합명세_v0.1.md` §9.1의 “HTTP 서버·OpenAPI 서비스는 아직 없다”는 그 명세를 쓰던 시점의 기록이다. 그 파일은 당시 패키지 해시에 묶인 역사 증거라 본문을 고치지 않았다. 예매·리셀·검표 목과 신용 목의 “HTTP 서버는 없다”는 각 목 함수에 대한 설명으로 그대로 둔다.

비운영 TypeScript 0.x 클라이언트는 [sdk/README.md](../sdk/README.md)에 있고, 계약 전용 OpenAPI에서 다시 생성한다. manifest-v1과 BOOTSTRAP profile은 [contracts/sdk/COMPATIBILITY_MANIFEST_V1.md](contracts/sdk/COMPATIBILITY_MANIFEST_V1.md)가 정한다. 이 산출물은 안정 1.0·공개 배포·운영 적합이 아니다.

## 청사진 색인 — 설계 제안, 승인·구현 아님

아래 두 청사진은 2026-09-29 범위 편입([결정 기록](decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md))의 설계 제안이다. 구현·배포·발행을 승인하지 않으며, 후속 작업 정의는 작업문서가 아니다.

| 청사진 | 다루는 것 | 상태 |
|---|---|---|
| [선택적 자체 토큰 발행·운영 계층](blueprints/optional-native-token-v1/README.md) | 용도별 채택 평가, 필수 불변식, Sui 표준 대조, 공급·분배, 경제적 연결, 권한, 거래 결합, 활성화 단계, TIX 자료 등급 | 구체 설계·구현 미완료 |
| [확장형 권리·재고·검표 계층](blueprints/rights-scale-v1/README.md) | 16슬롯 변경 영향 지도, 구조 대안 비교와 권고, 필수 안전 조건, ZK 현재성 설계, 검증 규모 계획 | 설계 제안. 16슬롯 참조 프로파일은 회귀 기준으로 보존 |

닫힌 미병합 [PR #35](https://github.com/BeautifulMind-JT/kix-protocol/pull/35)의 금융·플랫폼 청사진은 이 색인의 항목이 아니다. 역사적 설계 자료로만 참고한다.

## 2026-10-08 병합 문서 색인 — 초안·결정 초안·ADR

이 절은 문서의 위치만 안내한다. 승인 문서가 아니며, 확정 조건은 그 문서가 정한다.

| 문서 | 다루는 것 | 상태(문서가 스스로 적은 대로) |
|---|---|---|
| [어댑터 전송·이벤트·결제·operation 정체성](contracts/ADAPTER_EVENT_IDENTITY.md) | 전송·원문 증거·이벤트·결제·경제 operation의 묶음 | 계약 초안 0.1. 구현·schema·wire 아님 |
| [조회·목록 쿼리](contracts/READ_MODEL_QUERIES.md) | 상거래 표면의 조회·목록 의미 | 초안 0.1. 와이어 본문·카탈로그 삽입 없음 |
| [AI 위임 권한](contracts/AI_DELEGATION_AUTHORITY.md) | 조회·제안·실행 권한. 오프라인 목의 술어 | 초안 0.1. 실행을 켜지 않음. 목은 `reference/ai_delegation/` |
| [1차 발행 가격·수수료](contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md) | 1차 발행의 구조·바인딩·산술·사건 의미 | 초안 0.1. 가격·수수료 값은 정하지 않음 |
| [확장 권리 프로파일](contracts/RIGHTS_SCALE_PROFILE.md) | 확장 프로파일 계약 | 초안 0.1. 미검토·미측정 |
| [RS-0 결정 기록](decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md) | 권리 확장의 객체·재고 권위 | 결정 초안. 확정 조건은 그 문서가 정한다 |
| [루프백 관문의 브라우저 접근](decisions/GATE_BROWSER_ACCESS_DECISION_20261008.md) | 브라우저가 루프백 관문에 닿는 방식의 비교 | "채택 제안"(그 문서의 표현). 관문 코드 변경 없음 |
| [I12 절단 증명](decisions/CUT_PROOF_I12_20261008.md) | C_g/H_g 절단, 옛 작성자 차단, 미발행 약정 보존 | 증명 초안, 사용자 병합 때에만 효력. I12는 미완결 |
| [v5 crate 설계 결정](decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) | 종결·슬롯 해제·기록 회수·review 해제·색인을 잠금 v4 밖에 둘 새 crate | 설계 결정 제안. 사용자 병합 때에만 효력. 구현 없음 |
| [ADR-0002](adr/0002-token-layer-scope-and-limits.md) | 선택적 자체 토큰 계층의 범위·한계 | ADR (제안 기록). 범위·한계 기록이며 잠금 해제 아님 |
| [토스 수단 확장 검토](reviews/TOSS_METHOD_EXPANSION_REVIEW.md) | 토스 내 간편결제·가상계좌의 차이 | 문서 전용 검토 (2026-10-05) |
| [공개 엔드포인트 준비 계획](operations/PUBLIC_ENDPOINT_READINESS_PLAN.md) | 공개 운영 엔드포인트를 열기 전의 조건 | 문서 전용 계획. 공개 엔드포인트 잠금 닫힘 유지 |
| [현재 capability register](status/CURRENT_CAPABILITY_REGISTER.md) | 경로별 근거 색인 | 2026-10-06 `2554173` 시점 스냅샷. 이후 병합분은 반영하지 않음 |

[현재 capability register](status/CURRENT_CAPABILITY_REGISTER.md) 본문은 이 색인에서 고치지 않았다. 그 행은 2026-10-06 `2554173` 스냅샷의 한계이며, 그 뒤 들어온 문서를 반영하지 않는다.

같은 날짜의 검증 기록:

- [k-stage4-local-exploration](../validation/2026-10-08-k-stage4-local-exploration/README.md) — 탐색 자료, 제품 SLO·backend 채택·우열 아님. 비교표 정본은 개발계획 §9.
- [ai-delegation-contract-mock](../validation/2026-10-08-ai-delegation-contract-mock/README.md) — 오프라인 목 시험 기록.
- [k1-adapter-event-identity](../validation/2026-10-08-k1-adapter-event-identity/README.md) — 초안 증거 기록.
- [k1-evidence-close](../validation/2026-10-08-k1-evidence-close/README.md) — 첫 묶음 통합 검토·증거 마감 기록. 수명 입력 반영과 고정 환경 성능 반복은 미완결로 둔다.

## 역사 문서와 증거

[루트 역사 문서 목록](../README.md#6-역사-문서--현행-계획-아님)의 V24·V23·V2·BLUEPRINT·ROADMAP 등은 현행 계획이 아닙니다. 특히 V24의 자동 R2 진행은 현재 금지입니다. 역사 문서의 상단 경고 뒤 본문은 당시 기록으로 보존합니다.

[ADR-0001](adr/0001-ktx-authority-commit-recovery.md)의 안전 관계와 [보안 보완](PROTOCOL_HARDENING.md)·[저장 조사](STORAGE_INVESTIGATION.md)·[회귀 검증](RUNTIME_VALIDATION.md)은 근거별 범위로 읽습니다. 옛 계획의 승인 효력을 폐기했다고 안전 규칙이나 사건 기록을 삭제하지 않습니다.

모델 1·첫 묶음 승인은 backend 채택·커널 전환 완료·실금전 운영 승인과 다릅니다. 미정 항목, 두 잠금 blob, R2 금지, (a) 보류, 위생 일괄 금지는 유지합니다.
