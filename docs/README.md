# KIX 문서 색인

**현행 개발계획 정본은 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) 하나입니다.** 현재 승인·금지·진행 순서는 §1·§5, 4단계 backend 비교는 §9를 따릅니다. 이 색인은 별도의 승인 문서가 아닙니다.

**[루트 README](../README.md)의 역할:** 프로젝트와 현재 기준·잠금·금지·읽는 순서를 안내하는 최초 입구.
**이 `docs/README.md`의 역할:** 같은 정본 아래 계약·검증·보존 자료의 위치를 안내하는 색인.

## 현재 문서 — 이 순서로 읽기

1. [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) — 현재 계획·승인 범위.
2. [기준 commit·태그 표](status/BASELINES.md) — 현재 main, 고정 R1 태그, PR 검토 SHA, #11 실험을 구분. [main 상태 정합 기록](status/MAIN_STATE_20260928.md) — 2026-09-25~27 병합 범위, hosted CI 공백, D-1~D-3 결정 전 사실. [프로그램 결정 D-1~D-3](decisions/PROGRAM_DECISIONS_20260928.md) — 2026-09-28 #73 병합으로 승인. Track K/P, Wave 게이트, readiness 저널 한도, 유지되는 잠금과 해제 조건.
3. [모델 1 결정](decisions/AUTHORITY_MODEL_1.md) — 체인 권위 / 오프체인 위임 실행. R2·(a) 착수 승인이 아님.
4. [수명 계약 초안](contracts/STATE_LIFECYCLE.md), [열린 입력·답할 주체](contracts/FIRST_BATCH_OPEN_INPUTS.md), [담당자 질문서](status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md)(위치만. 회신·정책 결정이 아니다), [세 묶음 결정 시트](status/ASTRA_DECISION_SHEETS_KO.md)(위치만. 결정·채택·회신이 아니다), [두 번째 묶음 결정 시트](status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md)(위치만. 결정·채택·회신이 아니다), [열린 사용자 결정 원장(2026-10-22)](status/OPEN_USER_DECISIONS_20261022.md)(위치만. 결정·채택·회신이 아니다).
5. [계약 불변식·비교 모델의 한계](contracts/CONTRACT_INVARIANTS.md), [첫 묶음 실행 근거](../validation/2026-09-16-first-batch/README.md).
6. [측정 계약](contracts/PERFORMANCE_MEASUREMENT.md), [고정 smoke 조건](contracts/PERFORMANCE_BASELINE_V4.md)(역사적 debug 논리 서명, 제품 p99 아님), [Task 004 장치 메모](../validation/2026-09-25-task-004-perf-measurement/README.md).
7. [잠금의 실제 CI 경로](status/LOCK_ENFORCEMENT.md), [위생 목록 — 실행 금지](CODE_HYGIENE_BACKLOG.md).
8. [원래 32개 항목](status/ORIGINAL_32_STATUS.md), [M 제외 부분 앵커](status/PARTIAL_ANCHOR_COUNTS.md), [#11 태그 보존](status/PR11_PRESERVATION.md).
9. [범위 편입 결정 기록(2026-09-29)](decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md) — #79 사용자 병합(`5cf4168`)으로 승인. 선택적 자체 토큰 계층과 확장형 권리·재고·검표 계층. 당시 설계·계획 문서화 한정이며 후속 조건부 범위는 [프로그램 로드맵 R-1~R-11](decisions/PROGRAM_ROADMAP_20260930.md)을 따른다. D-1~D-3의 잠금·해제 조건은 유지하며 범위 승인과 실행 시작을 분리한다. [개발계획 §18](DEVELOPMENT_PLAN.md#18-2026-09-29--선택적-자체-토큰-계층과-확장형-권리재고검표-계층의-범위-편입).
10. [.aiops/program.json](../.aiops/program.json) — 현재 노드 입력·canonical 의존성. [감사·병합 판정 표](aiops/PROGRAM_ASTRA_DELEGATION.md), [pending catalogue](decisions/PROGRAM_ROADMAP_20260930_PENDING.json), [확대 후보](aiops/PROGRAM_EXPANSION_20261002_KO.md) — 외부 선행·별도 채택·release 결정을 완료로 간주하지 않는다. 후보 집계 반영은 별도 채택 뒤 개발계획 §17에 따른다.

## 계약 전용 OpenAPI

[계약 전용 OpenAPI](contracts/openapi/README.md)는 `reference/v0.3-rc1/protocol_contract.json`의 로컬 호출 명령과 FSM `REPLAYABLE` 명령을 담은 OpenAPI 3.1 핀이다. 그 핀은 라이브 서버를 선언하지 않고, 운영 엔드포인트도 없다. 같은 84개 명령과 같은 로컬 호출 경로를 루프백에서 부르는 비운영 통합 관문이 따로 있다. 공개 호스트·실 PG·KYC·공연장·은행 연동이 아니며, 로컬 HTTP 성공은 운영 승인이 아니다. 선택적 로컬 파일 저널과 재시작 재생은 [준비 런타임 경계](contracts/READINESS_RUNTIME.md)에 적는다. 그 저장은 프로토콜 정본이 아니고, 공개 배치·운영 적합·외부 연동의 승인이 아니다.

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
| [확장 권리 프로파일](contracts/RIGHTS_SCALE_PROFILE.md) | 확장 프로파일 계약 | 0.2 (초안). 미검토·미측정 |
| [RS-0 결정 기록](decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md) | 권리 확장의 객체·재고 권위 | 결정 초안. 확정 조건은 그 문서가 정한다 |
| [RS-1 착수 권한 기록](decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md) | RS-1 공개 경로의 초안 0.1 기준 구현 착수 | owner 결정 기록. 구현 착수 권한만 적으며 프로파일 초안 상태는 바꾸지 않음 |
| [RS-1 owner 답변 원문](decisions/archive/rs-1.decision_answer.md) | RS-1 착수 권한 기록 §4가 보존하는 owner 답변 원문 | 그 문서가 스스로 적은 대로: "Appended verbatim from the task input." RS-1 병합(#180) 후 이동; Astra 게이트 기록은 이 트리에 없음. 보존 규칙(§2)에 따라 아카이브에 있으며 내용 불변 |
| [루프백 관문의 브라우저 접근](decisions/GATE_BROWSER_ACCESS_DECISION_20261008.md) | 브라우저가 루프백 관문에 닿는 방식의 비교 | "채택 제안"(그 문서의 표현). 관문 코드 변경 없음 |
| [I12 절단 증명](decisions/CUT_PROOF_I12_20261008.md) | C_g/H_g 절단, 옛 작성자 차단, 미발행 약정 보존 | 증명 초안, 사용자 병합 때에만 효력. I12는 미완결 |
| [ADR-0002](adr/0002-token-layer-scope-and-limits.md) | 선택적 자체 토큰 계층의 범위·한계 | ADR (제안 기록). 범위·한계 기록이며 잠금 해제 아님 |
| [토스 수단 확장 검토](reviews/TOSS_METHOD_EXPANSION_REVIEW.md) | 토스 내 간편결제·가상계좌의 차이 | 문서 전용 검토 (2026-10-05) |
| [공개 엔드포인트 준비 계획](operations/PUBLIC_ENDPOINT_READINESS_PLAN.md) | 공개 운영 엔드포인트를 열기 전의 조건 | 문서 전용 계획. 공개 엔드포인트 잠금 닫힘 유지 |
| [현재 capability register](status/CURRENT_CAPABILITY_REGISTER.md) | 경로별 근거 색인 | 행별 위치 동기화 기준: TL·catalogue·SDK `eb14da2a6c5b5366cd4aed855bd453dcb4d79a42`(2026-10-09), TL-3 onchain·TL-4 `5e20a467160148ad5c2debfe357dfb8da084a30a`(2026-10-09), 비-TL 잔여 행 `3ce6e4975b7f439d67482451bb47a22c940add26`(2026-10-12), TL-L/TL-5 `aba875635f682bb9914e0dee016ced58e130cc04`(2026-10-13), K2·RS-1·RS-2·RS-3a·RS-3b·EV-V5/EV-DELEG/EV-RS `ced0e2f42c0491753db91acf87bd61574eb37ce4`(2026-10-14), RS-4 `ea867668696d6b1114a443d0fe4e840d96b948f6`(2026-10-16), RS-0·RS-5 / testnet keys·P AI delegation `aca49f6e5498291c1f221185df1ee5cdbf333342`(2026-10-16), EV-SET·EV-CREDIT·EV-IR·EV-BRA·F04·P Wave5 credit `244595db1524cbb1a01148baa07d6d28cd1b8dc6`(2026-10-17), EV-READY `08b317e5096893432116e41c8312697793500cfe`(2026-10-18), EV-BRA·EV-V5·EV-READY·RS-0·RS-3a·RS-3b·RS-4·TL-3 offchain·TL-4와 RS/TL evidence-map 안내·checker 목록 `01a86f66f1a2a0de98ae00f89e49d45ec07ec8da`(2026-10-20), EV-SET·EV-READY·EV-V5·K1·K2·K5·P AI delegation·RS-4·TL-3 offchain·protocol read projection evidence와 evidence-map 안내·checker 목록 `a114b5bd67164dd1264bc4ad838566809b5bc0b4`(2026-10-21), EV-RS·EV-READY·EV-V5·EV-BCS와 evidence-map 안내·checker 목록 `f6558996c611f74b88c60928f5b285c553303c14`(2026-10-22). 그 외 행은 2026-10-06 `2554173` 스냅샷 |

[현재 capability register](status/CURRENT_CAPABILITY_REGISTER.md)의 위치 동기화 기준은 행별로 다르다. TL·catalogue·SDK 행은 `eb14da2a6c5b5366cd4aed855bd453dcb4d79a42`(2026-10-09), TL-3 onchain·TL-4 행은 `5e20a467160148ad5c2debfe357dfb8da084a30a`(2026-10-09), 비-TL 잔여 행은 `3ce6e4975b7f439d67482451bb47a22c940add26`(2026-10-12), TL-L/TL-5 행은 `aba875635f682bb9914e0dee016ced58e130cc04`(2026-10-13), K2·RS-1·RS-2·RS-3a·RS-3b와 새 EV-V5·EV-DELEG·EV-RS 행은 `ced0e2f42c0491753db91acf87bd61574eb37ce4`(2026-10-14) 기준이고, RS-4 L1→L2→L3 행은 `ea867668696d6b1114a443d0fe4e840d96b948f6`(2026-10-16) 기준이고, RS-0·RS-5 / testnet keys·P AI delegation 행은 `aca49f6e5498291c1f221185df1ee5cdbf333342`(2026-10-16) 기준이고, EV-SET·EV-CREDIT·EV-IR·EV-BRA·F04·P Wave5 credit 행은 `244595db1524cbb1a01148baa07d6d28cd1b8dc6`(2026-10-17) 기준이고, EV-READY 행은 `08b317e5096893432116e41c8312697793500cfe`(2026-10-18) 기준이고, EV-BRA·EV-V5·EV-READY·RS-0·RS-3a·RS-3b·RS-4·TL-3 offchain·TL-4 행과 RS/TL evidence-map 안내·checker 목록은 `01a86f66f1a2a0de98ae00f89e49d45ec07ec8da`(2026-10-20) 기준이고, EV-SET·EV-READY·EV-V5·K1·K2·K5·P AI delegation·RS-4·TL-3 offchain·protocol read projection evidence 행과 evidence-map 안내·checker 목록은 `a114b5bd67164dd1264bc4ad838566809b5bc0b4`(2026-10-21) 기준이고, EV-RS·EV-READY·EV-V5·EV-BCS 행과 evidence-map 안내·checker 목록은 `f6558996c611f74b88c60928f5b285c553303c14`(2026-10-22) 기준이다. 나머지는 2026-10-06 `2554173` 스냅샷이다.

같은 날짜의 검증 기록:

- [k-stage4-local-exploration](../validation/2026-10-08-k-stage4-local-exploration/README.md) — 탐색 자료, 제품 SLO·backend 채택·우열 아님. 비교표 정본은 개발계획 §9.
- [ai-delegation-contract-mock](../validation/2026-10-08-ai-delegation-contract-mock/README.md) — 오프라인 목 시험 기록.
- [k1-adapter-event-identity](../validation/2026-10-08-k1-adapter-event-identity/README.md) — 초안 증거 기록.
- [k1-evidence-close](../validation/2026-10-08-k1-evidence-close/README.md) — 첫 묶음 통합 검토·증거 마감 기록. 수명 입력 반영과 고정 환경 성능 반복은 미완결로 둔다.

## 2026-10-09 병합 문서 색인 — 계약·결정·기록

이 절은 문서의 위치만 안내한다. 승인 문서가 아니며, 확정 조건은 그 문서가 정한다.

| 문서 | 다루는 것 | 상태(문서가 스스로 적은 대로) |
|---|---|---|
| [v5 crate 설계 결정](decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) | 종결·슬롯 해제·기록 회수·review 해제·색인을 잠금 v4 밖에 둘 새 crate | 설계 결정 제안. 사용자 병합 때에만 효력. 구현 없음 |
| [백엔드 채택 결정 제안](decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md) | 5단계에 쓸 로컬·비운영 backend, 또는 아직 없음 | 결정 제안, 사용자 병합 때에만 효력, 구현 없음 |
| [통합 (a) 잔여 공수 재산정](decisions/INTEGRATION_A_REESTIMATE_20261009.md) | PR #11 저널 통합 (a)의 잔여 계획 인일. 대상은 잠금 v4, 계획된 v5 crate, 5단계 로컬 PostgreSQL | 추정 기록. 결정이 아님. (a)·R2·저널·저장을 승인하지 않음 |
| [통합 (a) 결정 제안](decisions/INTEGRATION_A_DECISION_PROPOSAL_20261009.md) | PR #11 저널 통합 (a)를 지금 할지, 한다면 잠금 v4·v5 프레임 저널·v5와 로컬 PostgreSQL 중 어디인지 | 결정 제안, 사용자 병합 때에만 효력, 구현 없음. 문장 수정 없이 병합하면 DEFERRED |
| [OpenAPI 카탈로그 승격 — 소유자 결정 위치 기록](decisions/OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md) | 2026-10-09 소유자 결정(JunTae)이 인용되는 위치와 네 항목의 산출물 포인터 | 상태: 위치 기록. 결정을 새로 만들지 않는다. 검토됨으로 표시하지 않는다. |
| [정산·예매/리셀/검표·F04 정책 심화 — 소유자 결정 위치 기록](decisions/POLICY_DEEPENING_OWNER_DECISION_20261009.md) | 2026-10-09 소유자 결정(JunTae)이 정산(L0/W0/R0/S0/T0/B0/P0), 예매·리셀·검표(선택지 A), F04(선택지 A) 계약에서 인용되는 위치 | 상태: 위치 기록. 결정을 새로 만들지 않는다. 검토됨으로 표시하지 않는다. |
| [F04 실자금 해제 조건](decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md) | 실제 여신 잠금을 풀자는 제안이 갖춰야 할 조건 목록(법률·자본·위험·운영·승인) | Status: proposed. This is a User decision document. It takes effect only when the User merges it …. 조건 목록 채택은 해제가 아니며 잠금은 그대로다 |
| [토스 sandbox 적합성 계획](operations/TOSS_SANDBOX_CONFORMANCE_PLAN.md) | 실 PG 호출 전에 필요한 Toss sandbox 적합성 증거의 시험 사례, 필요한 토스 답변, 증거 기록 위치 | 문서 전용 계획. 호출·자격 증명 없음. sandbox 증거는 실자금 잠금을 열지 않음 |

같은 날짜의 검증 기록:

- [k-a-reestimate](../validation/2026-10-09-k-a-reestimate/README.md) — 2026-10-09 통합 (a) 잔여 공수 재산정 기록. 계획용 추정이며 착수 승인이 아니다.
- [k-a-integration-decision](../validation/2026-10-09-k-a-integration-decision/README.md) — 2026-10-09 통합 (a) 결정 제안 기록. 권고는 실행하지 않음. 사용자 병합 때에만 효력.
- [openapi-catalogue-promotion](../validation/2026-10-09-openapi-catalogue-promotion/README.md) — Evidence for the contract-only catalogue promotion of the 44 FSM `REPLAYABLE` commands.
- [audit2-gate-browser-access-test-determinism](../validation/2026-10-09-audit2-gate-browser-access-test-determinism/README.md) — Test harness only.
- [k2-retention-proposal](../validation/2026-10-09-k2-retention-proposal/README.md) — Document only. No code, no new tests, no duration numbers, no new protocol command.
- [toss-sandbox-conformance-plan](../validation/2026-10-09-toss-sandbox-conformance-plan/README.md) — Document only. No Toss call, no credential, no new test, no new protocol command.
- [k-stage4-adoption-decision](../validation/2026-10-09-k-stage4-adoption-decision/README.md) — Document only. No code, no new tests, no backend implementation, no second comparison table, no SLO or cost numbers.
- [ci-wire-token-reward-suite](../validation/2026-10-09-ci-wire-token-reward-suite/README.md) — No new tests and no policy values. No independent verification of TK-4, TK-7, TK-8, TK-12, or V6.
- [tl-4-token-layer-verification](../validation/2026-10-09-tl-4-token-layer-verification/README.md) — No independent verification. No production endpoint, public host, real payment, KYC, bank, or venue call. No Sui testnet or mainnet. … It does not close the blueprint TL-4 acceptance line that asks for independent verification of TK-1 through TK-9 with no open blockers.
- [f04-real-funds-lift-criteria](../validation/2026-10-09-f04-real-funds-lift-criteria/README.md) — Document only. No code, no new tests, no policy numbers, no new protocol command.
- [audit3-openapi-promotion-owner-decision-record](../validation/2026-10-09-audit3-openapi-promotion-owner-decision-record/README.md) — Pointer record only. No new authorisation, no contract edit, no code, no new protocol command.
- [tl-5-decision](../validation/2026-10-09-tl-5-decision/README.md) — Document only. No code, no new tests, no policy numbers, no new protocol command. Criteria for testnet, mainnet, and issuance. They stay locked. The recommendation is not acted on.

## 2026-10-09 병합 문서 색인 — 토큰 계층(TL)

이 절은 문서의 위치만 안내한다. 승인 문서가 아니며, 확정 조건은 그 문서가 정한다.

| 문서 | 다루는 것 | 상태(문서가 스스로 적은 대로) |
|---|---|---|
| [토큰 역할·공급 (TL-0)](contracts/TOKEN_ROLE_AND_SUPPLY.md) | 역할 등급, 표현 선택지, 공급 술어 | 상태: 제안. 효력은 사용자가 이 문서를 병합할 때에만 생긴다 (로드맵 §1). |
| [토큰 가격원 기록](decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md) | 가격원이 이 권고 아래 필요하지 않다는 기록 | 상태: 기록. 가격원 계약의 초안이 아니다. |
| [토큰 권한·수명 (TL-1)](contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md) | 권한 분리, 키 사건, 정지·업그레이드 수명 | 상태: 제안. 효력은 사용자가 이 문서를 병합할 때에만 생긴다 (로드맵 §1). |
| [ADR-0003](adr/0003-coin-tix-lock-localnet-re-ruling-request.md) | coin/TIX 잠금의 localnet 재결정 요청 | Status: proposed. This is a User decision document. … Writing this file does not lift the lock. |
| [TL-2는 열리지 않음](decisions/TL2_DOES_NOT_OPEN_20261009.md) | TL-2가 열리지 않는다는 기록 | 상태: 기록. 패키지가 아니다. |
| [token_reward 참조](../reference/token_reward/) | 보상–거래 결합의 오프라인 참조 술어 | Offline reference predicates for reward–transaction coupling. |
| [외부 검토 질문서](status/TOKEN_LEGAL_REVIEW_BRIEF_KO.md) | 법률·회계·세무·금융 질문서 | 상태: 질문서만이다. 전송하지 않았다. … 검토됨으로 표시하지 않는다. |
| [TL-3 on-chain은 열리지 않음](decisions/TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md) | TL-3 온체인 부분이 열리지 않는다는 기록; Move 패키지·보상 기록 스키마 없음 | 상태: 기록. 패키지가 아니다. 효력은 사용자가 이 기록을 병합할 때에만 생긴다. 작성자가 빌더이므로 독립 검토가 아니고, 비작성자 exact-HEAD 검토가 아니다 … 검토됨으로 표시하지 않는다. |
| [TL-4 위협 모델](decisions/TL4_THREAT_MODEL_20261009.md) | 오프체인 토큰 계층의 위협 모델과 작성자 측 하네스; 패키지가 필요한 술어는 NOT VERIFIABLE | 상태: 기록, 작성자=빌더, 독립 검토 아님. 패키지가 아니다. 효력은 사용자가 이 기록을 병합할 때에만 생긴다. 작성자가 빌더이므로 독립 검토가 아니고, 비작성자 exact-HEAD 검토가 아니다 … 검토됨으로 표시하지 않는다. 자기 검토를 독립 PASS로 세지 않는다. |
| [TL-5 운영 활성화 결정 제안](decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md) | testnet 배포, mainnet 배포, 발행의 조건 목록 | Status: proposed. This is a User decision document. It takes effect only when the User merges it. 조건 목록을 채택해도 활성화가 아니며 세 관문은 잠긴 채로 남는다. |

## 2026-10-13 색인 보정 — 위치 안내만

이 절은 문서의 위치만 안내한다. 승인 문서가 아니며, 확정 조건은 그 문서가 정한다.

| 문서 | 다루는 것 | 상태(문서가 스스로 적은 대로) |
|---|---|---|
| [RS-0 검토 자료 묶음](status/RS0_REVIEW_PACK.md) | RS-0 프로파일·결정 기록의 Astra 검토를 위한 명제·가정별 근거 대응표와 열린 항목 | 빌더 작성 검토 자료. 검토·수락·상태 변경·rs-1 해제 아님 |
| [정산 분배 F01–F03 목 계약](contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md) | Wave 3 정산 mock 술어와 §7 정책 선택지 | 목 계약. F01·F02·F03·P04는 설계중 그대로. §7 권고 0.3 |
| [예매·리셀·검표 게이트 목 계약](contracts/BOOKING_RESALE_ADMISSION_GATES.md) | Wave 4 예매·리셀·검표 mock 술어와 수락 상태 기계 | 목 계약. B01–B05, R01–R05, P03은 설계중 그대로. §7 초안 0.2 |
| [여신·신용 선지급 F04 목 계약](contracts/CREDIT_ADVANCE_F04.md) | Wave 5 F04 mock 술어 | 목 계약. mock/sim only. F04·E06은 설계중 그대로 |
| [조회 원천 지도](contracts/READ_MODEL_SOURCE_MAP.md) | 승인된 13개 조회 이름의 소스 표면·보존 술어·카탈로그 기작 | 입력 자료. 결정·구현·카탈로그 변경 없음 |
| [I12 검토 자료 묶음](status/I12_REVIEW_PACK.md) | 절단 증명의 명제 P1–P4·가정 A1–A10별 기존 근거 대응표 | 빌더 작성 검토 자료 묶음. 독립 검토·수락·상태 변경 아님. I12는 미완결 |

## 2026-10-13~15 병합 기록 색인 — 위치 안내만

이 절은 문서·기록의 위치만 안내한다. 승인 문서가 아니며, 확정 조건은 그 문서가 정한다.

| 기록 | 다루는 것 | 상태(기록이 스스로 적은 대로) |
|---|---|---|
| [k-stage2-v5-impl 기록](../validation/2026-10-13-k-stage2-v5-impl/README.md) | 잠금 v4 밖 새 in-memory v5 커널 slice | This record claims `merge-ready` for nothing; the node state is implementation complete locally, awaiting exact-head CI, non-author review, Astra's architecture audit and the user merge. |
| [rs-1-public-path 기록](../validation/2026-10-14-rs-1-public-path/README.md) | 확장 프로파일 공개 경로 Move 패키지·모델·localnet | `docs/contracts/RIGHTS_SCALE_PROFILE.md` stays draft (`초안`) until Astra review at the RS-1 ARCHITECTURE gate. |
| [rs-1-issuercap-probe 기록](../validation/2026-10-14-rs-1-issuercap-probe/README.md) | `IssuerCap` 동시 사용 직렬화 localnet 프로브 | This node records the measured fact; it does not pick an option, and the cap-split RS-C01 test remains closed until that choice is made. |
| [rs-2-private-path 기록](../validation/2026-10-14-rs-2-private-path/README.md) | 루트 규칙·depth-10 회로·Verifier·manifest v2 | **Everything here is a localnet fixture.** |
| [rs-3a-delegation-primitives 기록](../validation/2026-10-14-rs-3a-delegation-primitives/README.md) | 페이지 단위 grant·GrantControl·회수 cut | **Everything here is a localnet fixture.** |
| [rs-3b-delegated-exec 기록](../validation/2026-10-14-rs-3b-delegated-exec/README.md) | 페이지↔커널·GA 카운터 대응 in-memory crate | No delegated execution is enabled (`runtime/ARCHITECTURE.toml` keeps `delegated_execution_enabled = false` and the architecture verifier still passes). |
| [docs-index-check-validation-records 기록](../validation/2026-10-15-docs-index-check-validation-records/README.md) | `validation/*/README.md`의 색인 연결 검사 추가 | This record extends a checker and its allowlist only; it retroactively indexes no historical record, raises no evidence grade, and marks nothing reviewed or operational. |
| [rs-4-l1-load 기록](../validation/2026-10-15-rs-4-l1-load/README.md) | 1,024-slot 단계 부하 localnet 측정 — 공개·비공개·위임 경로 분리 | **Everything here is exploration data.** |
| [kix-kernel-v5](../runtime/crates/kix-kernel-v5/README.md) | 새 in-memory v5 커널 crate | It is not a durable service, a storage engine, or a production runtime. |
| [kix-delegated-exec](../runtime/crates/kix-delegated-exec/README.md) | 위임 실행 map crate | It is not a service, not a chain client, not a storage engine, and not a production runtime. |

## 2026-10-16 결정 제안 색인 — 위치 안내만

이 절은 문서의 위치만 안내한다. 승인 문서가 아니며, 확정 조건은 그 문서가 정한다.

| 문서 | 다루는 것 | 상태(문서가 스스로 적은 대로) |
|---|---|---|
| [Sui testnet 키 관리 결정 제안](decisions/TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md) | 장래 testnet 배포가 필요로 할 키 보관, 교체, 사고 대응, 운영 주체의 형태 | Status: proposed. This is a User decision document. It takes effect only when the User merges it. 키도 비밀도 만들지 않고 배포하지 않으며 testnet 잠금은 잠긴 채로 남는다. |
| [위임 실행 활성화 결정 제안](decisions/AI_DELEGATION_EXECUTION_DECISION_PROPOSAL_20261016.md) | 위임 실행을 언제, 어떤 선행조건·I11 한도·회수 보장으로 켤 수 있는지의 형태 | Status: proposed. This is a User decision document. It takes effect only when the User merges it. 위임 실행은 꺼진 채로 남고 한도·이름·기간 값은 비어 있다. |
| [AI 위임 계층 매트릭스](status/AI_DELEGATION_LAYER_MATRIX.md) | AI 위임 계약 §6의 DLG-01..DLG-36 각각에 대해 목 시험, 체인 grant, executor map, readiness wrap이 담은 것 | Builder-authored map, not a review or acceptance. 어느 계층도 충분하다고 평가하지 않으며 인용된 소스 밖의 실행·한도·회수 보장을 주장하지 않는다. |
| [RS 술어 증거 지도](status/RS_PREDICATE_EVIDENCE_MAP.md) ([검증 기록](../validation/2026-10-16-rs-predicate-evidence-map/README.md)) | 권리 확장 프로파일 §8의 RS-C01..RS-C17과 §9의 RR-1..RR-6 각각에 대해 지금 있는 Move 시험, Python 모델 시험, Rust 메모리 시험, localnet 기록 | Builder-authored map, not a review or acceptance. Astra 아키텍처 검토가 아니며 등급을 올리지 않고 운영 수는 0으로 남는다. 어떤 간극도 닫지 않는다. |
| [RS 영향표 증거 지도](status/RS_IM_EVIDENCE_MAP.md) ([검증 기록](../validation/2026-10-17-rs-im-evidence-map/README.md)) | 권리 확장 프로파일 §12의 영향표 IM-01..IM-30 각각에 대해 처리 단어(유지·변경·새 프로파일·손대지 않음)와 지금 있는 Move 시험, Python 모델 시험, Rust 시험, localnet 기록, 손대지 않은 파일의 증거 | Builder-authored map, not a review or acceptance. Astra 아키텍처 검토가 아니며 등급을 올리지 않고 운영 수는 0으로 남는다. 어떤 간극도 닫지 않는다. |
| [계약 오류 코드 커버리지](status/CONTRACT_ERROR_CODE_COVERAGE.md) ([검증 기록](../validation/2026-10-18-contract-error-code-coverage/README.md), [FSM 확장 기록](../validation/2026-10-19-bra-fsm-error-code-coverage/README.md)) | 정산·예매/리셀/입장·F04·AI 위임 계약의 오류 코드 표 일곱 개(세 FSM 추가 표 포함)의 코드 각각에 대해 목·FSM이 던지는 자리와 그 코드를 이름으로 대는 시험 | Builder-authored map, not a review or acceptance. Astra 아키텍처 검토가 아니며 등급을 올리지 않고 운영 수는 0으로 남는다. 이름이 시험 본문에 있다는 것만 보이고 시험이 무엇을 단언하는지는 보이지 않는다. |

같은 날짜의 검증 기록:

- [testnet-key-management-decision](../validation/2026-10-16-testnet-key-management-decision/README.md) — Document only. No code, no new tests, no policy numbers, no new protocol command, no key. The recommendation is not acted on.
- [ai-delegation-execution-decision](../validation/2026-10-16-ai-delegation-execution-decision/README.md) — Document only. No code, no new tests, no policy values, no new protocol command. `delegated_execution_enabled` stays `false`. The recommendation is not acted on.
- [plan-register-index-sync-20261016](../validation/2026-10-16-plan-register-index-sync-20261016/README.md) — Location pointers only: no new approval, no decision text, no grade raise.
- [feature-ir-plan-limit-edge-tests](../validation/2026-10-16-feature-ir-plan-limit-edge-tests/README.md) — Characterization of the stated FeatureIR plan limits (1,024 stages, depth 64, 100,000 nodes): in-memory validator tests, not a wire, exporter, Polars/DuckDB or GPU result, and not a new budget or policy value.
- [audit7-plan-register-index-sync-20261016b](../validation/2026-10-16-audit7-plan-register-index-sync-20261016b/README.md) — Location pointers only: no new approval, no decision text, no grade raise.
- [audit7-docs-index-allowlist-prune](../validation/2026-10-16-audit7-docs-index-allowlist-prune/README.md) — This record removes four allowlist entries and adds one checker rule; it retroactively indexes nothing, raises no evidence grade, and marks nothing reviewed or operational.
- [ci-wire-i12-proof-ids-check](../validation/2026-10-16-ci-wire-i12-proof-ids-check/README.md) — This record raises no evidence grade, marks nothing reviewed or operational, and does not close I12.
- [delegation-layer-gap-matrix](../validation/2026-10-16-delegation-layer-gap-matrix/README.md) — Builder-authored map and stdlib checker; no binding designed, no command, flag, limit or value added, no layer graded sufficient, nothing enabled.
- [settlement-seeded-property-suite](../validation/2026-10-16-settlement-seeded-property-suite/README.md) — Builder-authored seeded property tests for the F01-F03 settlement mock and FSM; no mock or contract change, no grade change, no real payment.

## 2026-10-17 검증 기록 색인 — 위치 안내만

이 절은 기록의 위치만 안내한다. 승인 문서가 아니며, 각 기록의 효력은 그 기록이 스스로 적은 대로다.

- [credit-f04-seeded-property-suite](../validation/2026-10-17-credit-f04-seeded-property-suite/README.md) — Builder-authored seeded property tests for the F04 credit mock and FSM; MOCK only, no mock or contract change, no grade change, no real funds, not a regulated credit product.
- [feature-semantics-v1-edge-fixtures](../validation/2026-10-17-feature-semantics-v1-edge-fixtures/README.md) — Builder-authored scalar edge tests for kix-feature-semantics with a section-to-test map; in-memory helpers only, no src change, no grade change, no tolerance policy chosen.
- [readiness-journal-byte-sweep](../validation/2026-10-17-readiness-journal-byte-sweep/README.md) — Builder-authored byte-level tear and flip sweep of the local readiness journal; tests only, no store or contract change, no grade change, no durability or production claim.
- [booking-resale-adopt-issued-atomicity-fix](../validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md) — Builder-authored all-or-nothing fix for adopt_issued in the resale and admission machines; no command, error code, field or policy change, no accepted-path change, no grade change, no durability or production claim.
- [audit8-plan-register-index-sync-20261017](../validation/2026-10-17-audit8-plan-register-index-sync-20261017/README.md) — Location pointers only: no new approval, no decision text, no grade raise.
- [ai-delegation-seeded-property-suite](../validation/2026-10-17-ai-delegation-seeded-property-suite/README.md) — Builder-authored seeded property tests for the AI delegation mock; MOCK only, no mock or contract change, no grade change, no AI service, no grant on chain, no execution.
- [delegated-exec-seeded-differential](../validation/2026-10-17-delegated-exec-seeded-differential/README.md) — Builder-authored seeded differential and invariant test for the in-memory delegated-execution map against bare page kernels; tests and record only, no src change, no grade change, in-memory only, delegated execution stays disabled.

## 2026-10-18 검증 기록 색인 — 위치 안내만

이 절은 기록의 위치만 안내한다. 승인 문서가 아니며, 각 기록의 효력은 그 기록이 스스로 적은 대로다.

- [readiness-crash-point-sweep](../validation/2026-10-18-readiness-crash-point-sweep/README.md) — Builder-authored command-level crash-point sweep (40 cases) of the readiness-wrapped FSM machines; tests and record only, no readiness source, format or contract change, no grade change, no power-loss, fsync or production claim.
- [audit8-rs-map-rs-c01-issuercap-open-cell](../validation/2026-10-18-audit8-rs-map-rs-c01-issuercap-open-cell/README.md) — Builder-authored wording fix in one cell of the RS predicate evidence map; no test, option choice, profile/register/checker change, no grade change.
- [audit8-readiness-conformance-sweep-limit-note](../validation/2026-10-18-audit8-readiness-conformance-sweep-limit-note/README.md) — Builder-authored wording in the readiness conformance doc and one register cell; no test, store, format or contract change, no classification decision, no grade change.
- [audit8-loop-node-canonical-crosswalk](../validation/2026-10-18-audit8-loop-node-canonical-crosswalk/README.md) — Builder-authored textual crosswalk of merged loop-proposed nodes to overlapping canonical `.aiops/program.json` nodes ([표](status/LOOP_NODE_CROSSWALK.md)); no counting decision, no test or code change, no grade change.

## 2026-10-19 검증 기록 색인 — 위치 안내만

이 절은 기록의 위치만 안내한다. 승인 문서가 아니며, 각 기록의 효력은 그 기록이 스스로 적은 대로다.

- [v5-lifecycle-seeded-model-test](../validation/2026-10-19-v5-lifecycle-seeded-model-test/README.md) — Builder-authored seeded model test for the v5-only lifecycle surface (terminate, holds, reclaim report); tests and record only, no src or contract change, no grade change, oracle not independent.
- [rs-model-gap-closure](../validation/2026-10-19-rs-model-gap-closure/README.md) — Builder-authored in-memory tests closing the Python/Rust-closable PARTIAL gaps of the RS predicate and IM evidence maps ([술어 지도](status/RS_PREDICATE_EVIDENCE_MAP.md), [영향표 지도](status/RS_IM_EVIDENCE_MAP.md)); tests, row/status/counts updates and record only, no profile/Move/vector/contract change, no grade change, operational count stays 0.
- [tl-predicate-evidence-map](../validation/2026-10-19-tl-predicate-evidence-map/README.md) — Builder-authored, checker-backed token-layer predicate evidence map ([TL predicate evidence map](status/TL_PREDICATE_EVIDENCE_MAP.md)); no independent verification, no package, no testnet/mainnet, no real funds, operational count stays 0.
- [bra-fsm-error-code-coverage](../validation/2026-10-19-bra-fsm-error-code-coverage/README.md) — Builder-authored extension of the contract error-code coverage map and checker to the three FSM-added tables (booking sections 10.8 and 11.6, F04 section 7.8) plus six tests for seven unasserted codes; no contract, mock, FSM or command change, no grade change.

## 2026-10-20 검증 기록 색인 — 위치 안내만

이 절은 기록의 위치만 안내한다. 승인 문서가 아니며, 각 기록의 효력은 그 기록이 스스로 적은 대로다.

- [plan-rs-grant-cut-order-tests](../validation/2026-10-20-plan-rs-grant-cut-order-tests/README.md) — Builder-authored Move tests ordering the grant cut against delegated paid issue and delegated-page admission consume in both serial orders ([술어 지도](status/RS_PREDICATE_EVIDENCE_MAP.md) rows RS-C06/RS-C07); tests, row text updates and record only, no profile/Move-source/vector/contract change, no grade change, operational count stays 0.
- [plan-register-index-sync-20261020](../validation/2026-10-20-plan-register-index-sync-20261020/README.md) — Location pointers only: no new approval, no decision text, no grade raise.
- [adapter-identity-evidence-map](../validation/2026-10-20-adapter-identity-evidence-map/README.md) — Builder-authored evidence map for [어댑터 정체성 계약](contracts/ADAPTER_EVENT_IDENTITY.md) §§2–4 ([지도](status/ADAPTER_IDENTITY_EVIDENCE_MAP.md)); map, checker and record only, no adapter code, no schema/domain id, no contract change, every open input stays UNDETERMINED.
- [token-reward-readiness-wrap](../validation/2026-10-20-token-reward-readiness-wrap/README.md) — Builder-authored local readiness journal wrap for the token-reward FSM plus restart/fault tests; wrap, registration, tests and record only, no FSM/contract/command change, `durable` and the truth/production labels stay false, `MOCK_TOKEN_REWARD_ONLY` provenance and no-real-payout non-claims unchanged.
- [v5-transition-evidence-map](../validation/2026-10-20-v5-transition-evidence-map/README.md) — Builder-authored per-transition evidence map from the lifecycle contract §§5–6 to the `kix-kernel-v5` test tree ([지도](status/V5_TRANSITION_EVIDENCE_MAP.md)); map, checker and record only, no src or contract change, stopped transitions stay STOPPED, no open input resolved, no grade change.

- [ai-delegation-wrap-conformance](../validation/2026-10-20-ai-delegation-wrap-conformance/README.md) — Builder-authored adapter conformance scenarios and six AI delegation crash-point cells; tests and record only, no wrap, journal or contract change, execution disabled and durable false, no grade change.
- [stage5-host-preflight-checker](../validation/2026-10-20-stage5-preflight/README.md) — Builder-authored stdlib-only read-only preflight checker (`scripts/check_stage5_host.py`) for the stage-5 pinned-host prerequisites named in the `k-stage5-durable-tx` DECISION_REQUIRED record; checker and record only, evidence preparation for option 1, no provisioning, no option selected, no acceptance run, no grade change.
- [token-reward-rejection-atomicity](../validation/2026-10-20-token-reward-rejection-atomicity/README.md) — Builder-authored rejection-atomicity audit for the token-reward FSM repeating the #219 reservation pattern; test module and record only, no FSM/contract/command change, deterministic rejections leave no trace against a control machine, late-fault seams recorded as class B characterizations, no grade change.
- [read-model-contract-fixture-prep](../validation/2026-10-20-read-model-contract-fixture-prep/README.md) — Builder-authored candidate fixture vectors for the 13 approved read-model queries ([fixture dir](../reference/read_model/)); generator, vectors, self-check and record only, no query implementation, no wire binding, no catalogue change — candidate evidence pending the `read-model-reference` merge, not conformance evidence.

## 2026-10-21 검증 기록 색인 — 위치 안내만

이 절은 기록의 위치만 안내한다. 승인 문서가 아니며, 각 기록의 효력은 그 기록이 스스로 적은 대로다.

- [v5-evidence-citation-guard](../validation/2026-10-21-v5-evidence-citation-guard/README.md) — Builder-authored checker regression fix for incomplete test citations in both v5 fixture columns; citation validity only, map statuses unchanged, no semantic coverage, independent review or lifecycle approval claim.
- [plan-rs-ptau-header-tests](../validation/2026-10-21-plan-rs-ptau-header-tests/README.md) — Source-informed phase-1 header parsing characterizations with synthetic buffers and dependency-free CI invocation; no complete PTAU validation, ceremony, cryptographic-verification or policy-value claim.
- [plan-rs-zk-encoding-regressions](../validation/2026-10-21-plan-rs-zk-encoding-regressions/README.md) — Source-informed public-byte encoder characterizations with fabricated coordinates and dependency-free CI invocation; no curve-membership, proof-validity, independent cryptographic-verification or policy-value claim.
- [plan-rs-manifest-offline-regressions](../validation/2026-10-21-plan-rs-manifest-offline-regressions/README.md) — Source-informed synthetic metadata regressions for existing manifest/key guards, with dependency-free CI invocation; no cryptographic verification, policy value, grade or operational-readiness claim.

- [settlement-multi-payee-refund-corpus](../validation/2026-10-21-settlement-multi-payee-refund-corpus/README.md) — Builder-authored seeded multi-payee refund corpus for the F01-F03 settlement mock and FSM; tests and record only, no mock, FSM or contract change, no grade change, no real payment.
- [plan-register-index-sync-20261021](../validation/2026-10-21-plan-register-index-sync-20261021/README.md) — Location pointers only: no new approval, no decision text, no grade raise.
- [reward-wrap-conformance](../validation/2026-10-21-reward-wrap-conformance/README.md) — Builder-authored adapter conformance scenarios and twelve reward crash-point cells; tests and record only, no wrap, journal or contract change, `durable` and the truth/production labels stay false, no grade change.
- [readiness-runtime-evidence-map](../validation/2026-10-21-readiness-runtime-evidence-map/README.md) — Builder-authored clause-to-fixture evidence map for [준비 런타임 경계](contracts/READINESS_RUNTIME.md) ([지도](status/READINESS_RUNTIME_EVIDENCE_MAP.md)); map, checker and record only, no readiness/gate/contract change, the three class-B items and six `보류` stay OPEN with their owners, no grade change, operational count stays 0.
- [readiness-checker-partial-fixture](../validation/2026-10-21-readiness-checker-partial-fixture/README.md) — Builder-authored checker regression correction: validated synthetic PARTIAL ownership fixture and complete self-tests on a zero-PARTIAL in-memory map; real map and all nine OPEN rows unchanged, receipt/audit node still requires owner-approved input revision, no grade change.
- [kix-types-boundary-fixtures](../validation/2026-10-21-kix-types-boundary-fixtures/README.md) — Builder-authored boundary fixtures for the kix-types constructors and edges; tests and record only, no src or contract change, no grade change, source-informed and not independent, no completeness claim.
- [astra-decision-sheets-rs-stage5](../validation/2026-10-21-astra-decision-sheets-rs-stage5/README.md) — Builder-authored second decision sheet ([시트](status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md)) collecting the RS profile's named-but-unsheeted open items (IssuerCap choice, test-only fixture operational values, RS-C02 sentence 2, the stage-5 record's Astra items); document and record only, no value chosen, no contract, decision, program or source change, every cited value stays UNDETERMINED/DECISION_REQUIRED with its named owner, no grade change.
- [plan-rs-witness-offline-regressions](../validation/2026-10-21-plan-rs-witness-offline-regressions/README.md) — Synthetic public-event reconstruction regressions with injected object reads for RR-4 / IM-19; passes locally under Node 24 and, at that record's head, no workflow ran it (wired since; see the next entry), no new localnet/ZK result, no grade or operational-value change.
- [plan-rs-witness-ci-wiring](../validation/2026-10-21-plan-rs-witness-ci-wiring/README.md) — Subsequent CI-wiring record: the protocol rights-scale job explicitly invokes the existing offline witness-reconstruction suite under Node 24; local execution is recorded separately from pending exact-head CI, with no grade, gap, owner or operational-value change. The preceding entry describes the earlier snapshot.
- [plan-rs-spend-witness-offline-tests (2026-10-21)](../validation/2026-10-21-plan-rs-spend-witness-offline-tests/README.md) — Synthetic offline spendWitness construction regressions for IM-14/IM-15 and additive CI invocation within EV-RS; shared Poseidon, no circuit verification, independent cryptographic proof, RS-4 measurement or operational-value change.

## 2026-10-22 검증 기록 색인 — 위치 안내만

이 절은 기록의 위치만 안내한다. 승인 문서가 아니며, 각 기록의 효력은 그 기록이 스스로 적은 대로다.

- [plan-rs-offline-test-entrypoint](../validation/2026-10-22-plan-rs-offline-test-entrypoint/README.md) — Repair the offline package entry point to invoke all five existing suites; file-level and named-case results recorded separately, no tests, dependencies, workflows, policy values or qualification claims added.
- [plan-rs-admission-packet-offline-tests](../validation/2026-10-22-plan-rs-admission-packet-offline-tests/README.md) — Synthetic offline packet-construction and proof-wrapper rejection regressions through the unchanged admissionProof implementation; test-only dependency mocks, no cryptographic privacy, gate transport, localnet or complete IM-19 closure claim. Operational parameters remain UNDETERMINED with Astra as owner.
- [plan-rs-mint-wrapper-offline-tests](../validation/2026-10-22-plan-rs-mint-wrapper-offline-tests/README.md) — Synthetic offline mintNote construction and public-signal binding regressions for IM-14 and the mint-specific portion of IM-27; source-informed with shared Poseidon, no circuit validity, cryptographic independence or operational-readiness claim. Owner policy values remain UNDETERMINED with their existing owners.
- [plan-rs-verifier-binding-offline-tests](../validation/2026-10-22-plan-rs-verifier-binding-offline-tests/README.md) — Synthetic offline artifact-hash/pin and verifier-object binding regressions through the unchanged artifacts and checkVerifier (IM-17 / IM-27 evidence); in-memory file map, fake RPC and explicit Verifier.parse stub, so no decoder, actual-chain or operational-qualification claim. Operational parameters and the Verifier ID pin remain UNDETERMINED with their existing owners.
- [plan-register-index-sync-20261022](../validation/2026-10-22-plan-register-index-sync-20261022/README.md) — Location pointers only: no new approval, no decision text, no grade raise.
- [ci-wire-stage5-host-preflight-selftest](../validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md) — CI wiring of the stage-5 host preflight checker's `--self-test` into the unguarded stdlib step; the plain invocation is deliberately not wired because it would report the CI runner's host, which is not the pinned stage-5 host; workflow line, comment, register sentence and record only, no acceptance run, no provisioning, no option selected, no grade change.
- [rs4-load-host-conditions-recorder](../validation/2026-10-22-rs4-load-host-conditions-recorder/README.md) — Stdlib sampler and summarizer of dynamic host conditions (load average, MemAvailable, uptime, wall-clock gaps) for future RS-4 load runs, with synthetic-input tests and the procedure for attaching the summary to a record; not wired into the runner, no threshold or verdict, the acceptable load level stays UNDETERMINED (User); not a measurement, not an L2 attempt, not an option choice, no grade change.
- [rs-offline-suite-evidence-sync](../validation/2026-10-22-rs-offline-suite-evidence-sync/README.md) — Builder-authored citation sync: the eight CI-run offline Node suites cited by `.test.mjs::<node:test name>` in the [RS predicate map](status/RS_PREDICATE_EVIDENCE_MAP.md) and [RS impact-table map](status/RS_IM_EVIDENCE_MAP.md), both checkers extended to resolve such names (existence only); wording corrected where a sentence became false, no status change, no test, CI, contract or source change, no exact-head CI claim, no grade change.
- [open-user-decisions-ledger](../validation/2026-10-22-open-user-decisions-ledger/README.md) — Builder-authored in-repo ledger ([원장](status/OPEN_USER_DECISIONS_20261022.md)) of the five open `DECISION_REQUIRED` records (`k-stage5-durable-tx` host, `rs-4-l2` host, readiness negative-controls option A/B, readiness receipt/audit checker prerequisite, BRA seeded-property class C stop), one row each with owner, options and recommendation as its record states them plus HEAD-verified repo facts since; chooses no option, assigns no value, marks nothing reviewed, the owner must re-trigger a node outside the builder session; document and record only, no node state change, no grade change.

## 2026-10-23 검증 기록 색인 — 위치 안내만

이 절은 기록의 위치만 안내한다. 승인 문서가 아니며, 각 기록의 효력은 그 기록이 스스로 적은 대로다.

- [settlement-credit-rejection-atomicity](../validation/2026-10-23-settlement-credit-rejection-atomicity/README.md) — Builder-authored rejection-atomicity audit for the settlement and credit machines repeating the #219/#228 pattern; two test modules and a record only, no FSM/mock/contract/command change, deterministic rejections leave no trace against a control machine, late-fault seams recorded as class B characterizations, no grade change.

## 역사 문서와 증거

[루트 역사 문서 목록](../README.md#6-역사-문서--현행-계획-아님)의 V24·V23·V2·BLUEPRINT·ROADMAP 등은 현행 계획이 아닙니다. 특히 V24의 자동 R2 진행은 현재 금지입니다. 역사 문서의 상단 경고 뒤 본문은 당시 기록으로 보존합니다.

[ADR-0001](adr/0001-ktx-authority-commit-recovery.md)의 안전 관계와 [보안 보완](PROTOCOL_HARDENING.md)·[저장 조사](STORAGE_INVESTIGATION.md)·[회귀 검증](RUNTIME_VALIDATION.md)은 근거별 범위로 읽습니다. 옛 계획의 승인 효력을 폐기했다고 안전 규칙이나 사건 기록을 삭제하지 않습니다.

모델 1·첫 묶음 승인은 backend 채택·커널 전환 완료·실금전 운영 승인과 다릅니다. 미정 항목, 두 잠금 blob, R2 금지, (a) 보류, 위생 일괄 금지는 유지합니다.
