# KIX 개발계획 정본 — 모델 1·Rust 이행·첫 묶음

정본 경로: `docs/DEVELOPMENT_PLAN.md`. 개정일 2026-09-17 — 토스 카드 잠정 선택과 문서 불일치 정리. 실행·저장 구현의 새 승인은 없음.
2026-09-28 — [프로그램 결정 D-1~D-3](decisions/PROGRAM_DECISIONS_20260928.md) 반영.
이 결정은 사용자가 PR #73을 병합(`cfeb0d6`)하면서 승인했다. 내용은 세 가지다.
- Track P(Task 005)를 승인 범위에 편입한다.
- 4단계 비교 준비를 연다.
- readiness 래퍼를 허용한다.

실자금·실 제공자·운영 엔드포인트·mainnet·커널 잠금·R2 잠금은 유지한다.

2026-09-29 — [범위 편입 결정 기록](decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md) 반영(§18).
사용자가 PR #79를 병합(`5cf4168`)하면서 선택적 자체 토큰 계층(TL)과 확장형 권리·재고·검표 계층(RS)의 범위 편입을 승인했다.
당시 승인은 설계·계획 문서화에 한정했다. 이후 조건부 구현 범위는 아래 로드맵을 따르며, 운영 발행과 새 coin/TIX 모듈 잠금은 유지한다.

2026-09-30 — [프로그램 로드맵 R-1~R-11](decisions/PROGRAM_ROADMAP_20260930.md) 반영.
#81 병합은 범위 승인이고 실행 시작은 별도 시작 결정·감사·병합·host 자격의 대상이다. 현재 노드 정의와 의존성은 [.aiops/program.json](../.aiops/program.json), 감사·병합 경계는 [PROGRAM_ASTRA_DELEGATION](aiops/PROGRAM_ASTRA_DELEGATION.md)을 따른다. 이번 Mac 구현 인계는 legacy DONE·프로그램 완료·운영 활성화의 증거가 아니다.

2026-10-09 — Track K 결정 문서의 위치를 §5 「병합된 문서 위치(2026-10-09, 위치 안내만)」 표에 반영했다. 위치와 현재 상태만이며, 각 문서의 채택 문장은 그 표가 원문 그대로 인용한다.

근거 원안: 제출 문서 Git blob `57adb8d579986a945b716f0f181c0be938ceb389`.
원안은 GitHub에서 검증된 기존 정본이 아니었다. 해당 제출 바이트를 로컬
Git blob으로 대조한 뒤, 이번 승인·보류 범위를 반영하여 이 경로를 게시한다.
현재 진행 순서와 **4단계 backend 비교 항목의 정본은 이 문서 §9 하나**다.
`BACKEND_COMPARISON_STAGE4.md`는 안내 링크만 유지한다.

## 1. 목표와 확정·승인 범위

티켓 권리·거래 프로토콜을 예매·리셀·금융·마케팅·권한을 위임받은 AI가
공통 사용한다. 자체 소비자 UI 출시는 프로토콜 완료의 선행조건이 아니다.
CLI·SDK·독립 클라이언트로 검증한다. 묶음·복잡한 할인·다중 자산·비공개 거래·
리셀·정산·환불·금융·AI 범위를 삭제하지 않는다.

모델 1(체인 원권위 / 오프체인 위임 실행)과 기존 A-4·A-5 답변은 승인됐다.
권위 결정은 `decisions/AUTHORITY_MODEL_1.md`를 따른다. 체인 재고·권리 원권위와
제공자 자금 사실, 오프체인 예약 약정은 다른 사실이다. backend 기록의 위치는 §5 「병합된 문서 위치(2026-10-09, 위치 안내만)」 표다. 운영 backend 선택은 여기서 결정하지 않는다.

PG는 사용자 결정으로 **토스페이먼츠 잠정 선택**. 결제수단 1단계는 토스를 통한
국내 KRW 일반 카드 결제다. 간편결제·가상계좌는 토스 내 수단으로 후속 검토하며
직접 간편결제 가맹은 제외한다. 리셀·금융 가맹 범위와 일반 결제 웹훅 서명은 미확인이다.
[제공자 프로파일](contracts/PG_TOSS_CARD_PROFILE.md)의 공개 확인값과 계약/MID별 미정은
구분한다. 이는 어댑터·실자금·R2·(a)의 구현/착수 승인이 아니다.

첫 묶음만 착수 승인: **현재 v4 E-4 + 상태 수명 계약 + 성능 계약·측정 장치**.

**2026-09-28 추가(D-1, PR #73 병합으로 승인):** 위 문장은 2026-09-16 당시 Track K 기준이다. 이제 승인 범위는 두 트랙이다.

- **Track K:** 이 문서 §5의 1~8단계다. 기존 순서와 잠금을 유지하고, 4단계 비교 준비·탐색 실측을 새로 연다.
- **Track P:** [Task 005](tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md)의 Wave 0~7과 그 후속 심화다. 게이트 기록만으로 착수한다.

현재 범위는 [로드맵](decisions/PROGRAM_ROADMAP_20260930.md) R-1~R-11을 함께 따른다. Track K의 조건부 v5·적합성·로컬 영속 거래·합성 경제·인증 export와 Track P의 계약 공백 심화·조회·loopback 접근, TL·RS 후속을 포함한다. 개별 선행 병합·아키텍처 감사·작업 입력을 충족해야 하며, 정책 값과 새 명령은 `DECISION_REQUIRED · Astra`, 법률·세무·회계·제공자 답변 의존 값은 담당을 명시한 `UNDETERMINED`로 둔다. 잠금 해제 조건은 [프로그램 결정](decisions/PROGRAM_DECISIONS_20260928.md) §5를 유지한다.

10~16인 개발일은 계획용 노력 추정이며 이 PR의 완료 주장이나 납기 약속이 아니다.
(a) 통합의 재산정과 결정 제안 위치는 §5 「병합된 문서 위치(2026-10-09, 위치 안내만)」 표의 #141·#142다. R2 및 자체 복제·저장·로그 구현 금지는 유지한다.

두 파일은 주석·명칭·포맷을 포함하여 잠근다.
- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

코드 위생은 이번에 목록만 보고한다. KTX→KIX Runtime 일괄 치환은 잠금 파일에
영향을 주므로 3단계 schema·SDK 시점의 별도 승인까지 유보한다. 기존 branch/tag,
Cargo/CI/lint 설정 정리·코드 삭제는 하지 않는다. 첫 묶음의 새 테스트·하네스
파일 추가는 이 위생 목록과 별개인 승인 작업이다. 색인·회수·해제 전이는 제외한다.

## 2. 기준과 실제 상태

코드 기준 PR #12 `c8267d1c2bdbcd732aa46401fe059b92d8ae72a6`, 그 안의 v4 잠금
소스는 `b57d49d068c14d1a012e73cbc8c10c8f6ee5d631`과 같다. c8267d1 대상
KTX CI `35047176862`, 전체 protocol CI `35047176861`은 모두 completed/success.
이 성공은 새 첫 묶음 head의 성공으로 승계하지 않는다.

R1에는 메모리 내 지정석·연석·GA, 최소주문·최초 결과·operation 결합,
첫 capture·UNKNOWN·관측 중복·상충 격리·전송 전 슬롯 예약이 있다.
슬롯 종결 회수·review 해결·증거 회수·durable inbox·실제 제공자 인증은 없다.
`replace_owner`는 분산 fencing/membership/state transfer가 아니며 체인
클라이언트도 없다. R1은 모델 1의 완전 구현이 아니다.

PR #11 `55a3df4968f5684bb4cb9e3c9781ab5f00165235`의 v1 wire·local journal은
실험으로 보존한다. 최신 v4의 저장·재생 구현으로 합산하지 않는다. 존재했다는
사실은 R2 금지 해제 근거가 아니다. 실제 영속 경제 엔진·production Move·
Polars/DuckDB/libcudf 연동·성능 우월성은 미완료다.

## 3. 계층과 이행

| 계층 | 책임 |
|---|---|
| 프로토콜 계약 | 권리·자산·정책·명령·권한·확정성·재시도 규칙 |
| Rust/Move 실행 | 선언한 범위의 상태 변경과 안전 보장 |
| SDK/API/어댑터 | 인증·서명·직렬화·외부 사실 정규화·대사 |
| 데이터 처리 | 일관된 export·CPU 분석·SQL 감사·선택적 GPU |
| 응용 서비스 | 예매 UI·마케팅·금융 상품·운영 경험 |

기존 Python/Node/SQLite 경제 경로는 운영 구현으로 승격하지 않고 Rust로
재구축한다. 기존 기능·안전 보장과 없었던 영속 모델의 신규 구현을 구분한다.
Move는 유지한다. TypeScript SDK나 Python 시험 도구까지 Rust로 강제하지 않는다.

## 4. 기존 2.4와의 우선순위

이 문서는 사용자 승인을 반영한 진행 순서·금지 범위에서 기존 2.4의 자동 R2
진행보다 우선한다. ADR의 금액 보존·명령 정체성·UNKNOWN·회수 안전 원칙은
보존한다. 성능 비교는 R6까지 미루지 않는다. 기존 architecture 설정·검사기
코드는 이번에 변경하지 않았으며, 그 안의 replicated-ktx 목표가 착수 승인을
대신하지 않는다. 새 권위·진행 결정은 문서와 실제 구현 상태를 분리하여 읽는다.

## 5. 전체 단계

| 단계 | 범위 | 현재 착수 판단 |
|---|---|---|
| 1 | v4 E-4, 수명 계약, 성능 계약·측정 장치 | 첫 묶음 승인. v4 코드 수정 금지 |
| 2 | 종결·회수·보존·재시도·격리 해제와 색인 | R-4 문서 위치는 아래 2026-10-09 표의 #138. 열린 입력에 기대는 부분만 정지. 잠금 v4 불변 |
| 3 | schema·버전·SDK·독립 클라이언트 적합성 | R-5: 적합성 작업 승인, p-sdk-1 선행. 안정 1.0·공개 배포·일괄 명칭 치환은 별도 결정 |
| 4 | 실행·저장 후보 비교 | §9의 단일 비교표 사용. 실측 범위 별도 확정 |
| 5 | 선택 backend의 영속 거래·inbox/outbox | R-6 문서 위치는 아래 2026-10-09 표의 #140. 5단계의 선행은 v5 구현이다. 자체 R2·복제·합의 잠금 유지 |
| 6 | 경제·Move·복합 거래 | R-10: 합성 금액 참조 모델만 승인. 5단계·정산·예매/리셀/검표 계약 심화 선행 |
| 7 | 인증 export·CPU 분석·SQL 감사 | R-11: 5단계 로컬 원천 위 인증·일관 export, 그 뒤 CPU/SQL 의미론 감사 |
| 8 | native GPU 선택적 가속 | CPU/SQL 감사 뒤 문서 전용 계획. 가속 구현·성능 달성 승인 아님 |
| 병행 | AI 위임·금융 확장 | 필요한 공통 권한·경제 계약에 연결. GPU 선행 아님 |

현재 첫 묶음에 새 회수 정책의 구현, 물리 저널, 복제, frontend, 색인 변경은 없다.

이 표는 Track K이며 9월 28일 결정과 후속 로드맵을 반영한다.
- 4단계는 비교 계획·후보 선별·로컬 탐색 실측까지 열렸다. backend 기록 위치는 아래 2026-10-09 표의 #140이다. 운영 backend 선택은 이 문서가 결정하지 않는다.
- 2단계 기록 위치는 아래 2026-10-09 표의 #138이다. 열린 입력 전체의 확정을 기다리지 않고 해당 부분만 정지한다. 잠금 v4는 그대로다.

Track P는 이 표와 병행한다. 범위는 제품 프로토콜의 다음 항목이다.
- 계약·참조 모델·mock
- Move 확장
- 계약 전용 OpenAPI와 비운영 0.x SDK
- 분리 저장소 앱
- AI 위임 계약

게이트는 [프로그램 결정](decisions/PROGRAM_DECISIONS_20260928.md) §3과 [로드맵](decisions/PROGRAM_ROADMAP_20260930.md) R-7~R-9·R-11을 따른다. Wave 7은 commerce `w6a-evidence` 병합 뒤 열리며, protocol `wave7-marketing-contracts`는 외부 선행 확인 후 별도 plan revision으로 편입한다. 조회는 상태를 바꾸지 않으며 browser 접근은 결정된 방식·기본 꺼짐·loopback 출처만 허용한다. on-sale admission control은 5단계 뒤 별도 계약·감사 경로를 따른다.

병합된 문서 위치(2026-10-08, 위치 안내만): [어댑터 이벤트 정체성](contracts/ADAPTER_EVENT_IDENTITY.md)(#124), [조회·목록 쿼리](contracts/READ_MODEL_QUERIES.md)(#127), [AI 위임 권한](contracts/AI_DELEGATION_AUTHORITY.md)(#130), [1차 발행 가격·수수료](contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md)(#129), [브라우저 접근 결정](decisions/GATE_BROWSER_ACCESS_DECISION_20261008.md)(#132). 각 문서의 확정 조건은 그 문서가 정하며 이 문단은 승인이나 상태 변경이 아니다.

병합된 문서 위치(2026-10-09, 위치 안내만): 아래 표는 위치와 현재 상태만 적는다. 채택 문장은 병합된 파일의 문장을 그대로 옮긴 것이며, 「문장 수정 없이」 조건이 지켜졌는지는 이 표가 판단하지 않는다.

| 문서 | PR | 병합 커밋 | merged_by | 문서 자체의 채택 문장(원문) | 효력 표기 |
|---|---|---|---|---|---|
| [I12 절단 증명](decisions/CUT_PROOF_I12_20261008.md) | #136 | `ae869f38438d8174103171ec741a41376aee60df` | BeautifulMind-JT | 기록된 수락 갈래 없음. §5는 선택지 1/2/3을 제시하고 채택 문장을 두지 않는다. I12 미완결. | 효력 발생(User 병합) |
| [v5 crate 설계 결정 제안](decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) | #138 | `a483ab1777ad0c3e15ff71798822cbf6b3666f83` | BeautifulMind-JT | 사용자가 이 문서를 문장 수정 없이 병합하면, 이 문서에서 「권고」로 표시한 갈래(O1)와 §6에서 정지라고 적지 않은 구현 게이트만 채택되고, 그 채택이 `k-stage2-v5-impl`의 구현 범위가 된다. | 효력 발생(User 병합) |
| [보존 기간 제안](decisions/RETENTION_PERIODS_PROPOSAL_20261009.md) | #139 | `6e54e723d582e88ae89df309eb144d4664c7e1f5` | BeautifulMind-JT | 사용자가 이 문서를 문장 수정 없이 병합하면, 이 문서에서 「권고」로 표시한 갈래(R1)만 채택되고, `DECISION_REQUIRED` 또는 `UNDETERMINED`로 적힌 값은 멈춘 채로 남는다. | 효력 발생(User 병합) |
| [백엔드 채택 제안](decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md) | #140 | `bb193efb5d238581096372c8a20bee1271dfe4df` | BeautifulMind-JT | 사용자가 이 문서를 문장 수정 없이 병합하면, 선택지 A만 채택되고, 채택되는 backend는 5단계의 로컬·비운영 PostgreSQL 17.11(Debian 17.11-0+deb13u1)이며, 그 범위는 단일 프로세스·단일 작성자·기본 꺼짐·운영 플래그 false·R2와 복제와 합의는 열지 않음·이미 멈춘 항목은 멈춘 채로다. | 효력 발생(User 병합) |
| [통합 (a) 잔여 공수 재산정](decisions/INTEGRATION_A_REESTIMATE_20261009.md) | #141 | `57a3e3049c84a2ac0112371594e9bb4b85a8296f` | BeautifulMind-JT | 추정. 결정 아님. | 효력 발생(User 병합) |
| [통합 (a) 결정 제안](decisions/INTEGRATION_A_DECISION_PROPOSAL_20261009.md) | #142 | `b6cc9978c64b1ff54f822ea930424b5d78dfca2a` | BeautifulMind-JT | 사용자가 이 문서를 문장 수정 없이 병합하면, 선택지 B만 채택되고, 통합 (a)는 DEFERRED이며, 착수·R2·저널·저장 엔진은 열리지 않고, 재개한다면 대상은 v4가 아니며 별도 프레임 저널을 두지 않고, 이미 멈춘 항목은 멈춘 채로다. | 효력 발생(User 병합) |
| [OpenAPI 카탈로그 승격 — 소유자 결정 위치 기록](decisions/OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md) | — | — | — | 기록된 채택 문장 없음(위치 포인터). 상태: 위치 기록. 결정을 새로 만들지 않는다. 검토됨으로 표시하지 않는다. | 위치 포인터. 새 승인 아님. 결정이 인용한 병합: #152 `d63768dd…` |

## 6. E-4와 상태 수명

### 6.1 E-4

잠금 v4를 public API로 호출하는 별도 integration test와 owner-array/명령이력
비교 모델을 둔다. 자료구조·실행 경로는 분리했으나 작성자가 커널 소스를 읽고
reserve 판정 순서도 참고했다. **작성 출처가 독립된 clean-room 명세 모델이 아니다.**
생성·재현 seed·실패 명령열 축소로 결과와 공개 상태를 매 전이 비교하지만, 그 일치는
어느 쪽이 옳은지 또는 공유 오류가 없는지의 증명이 아니다. 테스트 모델에서 Kernel·
bitmap 구현을 정답 계산에 다시 호출하지 않는다는 것과 출처 독립성을 구분한다.
정확한 제한은 [CONTRACT_INVARIANTS §1](contracts/CONTRACT_INVARIANTS.md)을 따른다.
모델을 거치지 않는 별도 계약 불변식 검사도 현재 공개 상태의 범위에서 해석한다.
현재 v4의 만석, retained/unretained unbound 구별, UNKNOWN, 원결과 재사용,
owner 변경·논리시간과 늦은 capture를 대상으로 한다. 회수·해제 전이는 없다.
잠금 소스의 일시적 변이도 하지 않는다. 초기 민감도 검사는 참조 모델 쪽의
과거 격리 누락만 주입하며, 실제 커널 mutation campaign이라고 표시하지 않는다.

### 6.2 수명 계약 정본

`contracts/STATE_LIFECYCLE.md` 초안 **0.6**이 수명 계약의 현행 정본이다.
LC-TERM의 정의는 0.3에서 조건·승인·내구 기록에 따른 운영 종결로 닫혔으며,
0.5는 0.4의 승인 주체·기간·철회·승계를 계승하고 대체자의 동일한 전체 범위를 확정했으며,
현행 0.6은 그 내용을 그대로 계승한 채 §5.7.1에서 ReturnRequired와 review_required의
우선순위·직교성만 명확화한다. 이는 문서 명확화이고 커널 전이·해제 권한 변경이 아니다.
외부 자금 사실의 확정과는 구별한다. A-4와 중복되는
늦은 사실 보존(LC-FACT), 회수 후 재생 경계(LC-CUT), 종결 근거(LC-TERM)를
한 번만 정의한다. 이후 저널·wire는 이를 참조하며 다른 정책을 따로 만들지 않는다.
토스 카드의 공개 확인값은 [제공자 부록](contracts/PG_TOSS_CARD_PROFILE.md)에 결합한다.
15일 멱등키와 webhook 스케줄을 KIX 보존기간·최종 실패·회수 cut으로 바꾸지 않는다.
종결 근거는 provider/MID/환경/API·계약 버전/상품/결제수단/operation 종류별로 구분한다.
명령 결과 캐시 축출과 권위 있는 중복 방지 기록 폐기는 다르다. UNKNOWN을
시간으로 실패 처리하지 않는다. reserved→stored는 총 관측 예산의 회수가 아니다.
실제 보관 계층 없이 보존 성공을 가정하여 운영 회수를 완료 처리하지 않는다.

### 6.3 후속 구현 유보

LC-TERM 0.3에서 정의하고 현행 0.6이 계승한 **조건·지정 승인·내구 기록에 따른 운영 종결**,
그 결정에 연결되되 별도 인계 조건을 요구하는 예약 슬롯의 한 번만 해제, 참조 관계와
증거 회수·review 해제·상충 색인은 후속 구현 단계다. 운영 종결은 제공자의 영구
실패/비실행 보증이나 외부 사실 확정이 아니며, 승인만으로 슬롯·증거·권리를 자동 해제하지 않는다.
보존·회수와 색인을 함께 다루며 이번에는 구현하지 않는다.
법정 보존·사업상 대사·재시도 지원·메모리 상주는 별도 기간이다. 구체 기간은 미정. 네 기간의 기록 위치는 §5 「병합된 문서 위치(2026-10-09, 위치 안내만)」 표의 #139다. 네 기간은 서로 나뉘어 있고 기간 값은 두지 않는다.

## 7. 성능 계약·측정 장치

정본은 `contracts/PERFORMANCE_MEASUREMENT.md`다. 승인된 절대 TPS·p99·허용
실패율 숫자는 없다. 초기 부하 예시는 제품 SLO나 측정 성과가 아니다.
예약 성공·업무 거절·동일 명령 재시도·Capacity·관측 처리를 분리한다.
예정 도착시각 기준 지연과 실제 서비스 시간을 구분한다. 기계·toolchain·빌드·
입력·예산·원시 샘플을 보존한다. 전체 성공률을 빠른 거절로 부풀리지 않는다.

순수 v4 하네스는 메모리 계산만 측정한다. 전체 실측과 DB·체인 확정 지연을
대신하지 못한다. 저부하·균등·hot seat·재시도·이력 증가/포화를 구분하고,
측정 중 커널 재생성이나 무한 예산으로 고갈을 숨기지 않는다.
CI debug smoke는 장치 동작 검증이지 production p99/TPS 결과가 아니다.
2026-09-25 Task 004는 같은 절의 측정 장치를 결과별 요약, 저부하·hot seat·재시도·
이력 증가/포화 구분, `.local/` release 증거 경로, 비주장으로 보완한다. 정본 의미의
변경이나 승인 SLO 추가는 아니다. 혼합 결과 p99는 구매 또는 신규 성공 p99가 아니다.
실행 메모는 `validation/2026-09-25-task-004-perf-measurement/README.md`다.
PostgreSQL 비교와 backend 선택은 Task 004 범위의 기록이다. 이후 비교·탐색 자료는 §9.5, 기록 위치는 §5 「병합된 문서 위치(2026-10-09, 위치 안내만)」 표다.

## 8. schema·SDK

identity/domain/schema/version, 필드·순서·의미·한도, wire와 업무 의미론 버전,
정책/자산 commitment, 상태 snapshot 버전을 구별한다. 충돌·test namespace·
잘린 입력·ULEB128·UTF-8·trailing·정수 범위를 검증한다. 원시 증거 해시와
검증된 객체 commitment를 구별한다. 독립 클라이언트의 bytes·결과·오류를
맞추고 production Move 타입이 정해진 뒤 Rust↔Move vector를 추가한다.
예약·결제·권리발행·반환 필요·실환불 완료를 API에서 구별한다.

## 9. 4단계 실행·저장 backend 비교 — 유일한 정본

PostgreSQL/TigerBeetle/FoundationDB/TiKV는 후보이며 자체 KIX Runtime 저장
엔진도 자동 채택하지 않는다. KTX는 현재 저장소의 옛 코드명 표기이며 이번에
일괄 치환하지 않는다. 요구에 맞지 않는 후보는 공식 자료·구체 부족 근거로
제외하고 비교 가치가 있는 소수만 동일 거래 범위에서 실측한다.

| 비교축 | 질문·기록할 결과 | PostgreSQL 탐색 자료 (2026-10-08) | FoundationDB 탐색 자료 (2026-10-08) |
|---|---|---|---|
| 원자적 업무 범위 | 주문·예약·명령 결과·외부 의도를 같은 단위로 묶는가 | 탐색 자료. 한 로컬 트랜잭션에 명령 identity, payload sha256, 최초 결과, 합성 show `synthetic-show`의 slot, 최소 주문, 외부 의도 기록(`FIXTURE_NOT_DISPATCHED`, 호출 없음)을 commit한다. 업무 거절은 주문 없이 명령 결과만 남긴다. 금액은 u128 십진 문자열이다. 체인 재고 writer는 없다. | 탐색 자료. 같은 필드를 한 FoundationDB 트랜잭션의 여러 key로 commit한다. 관계·재고·결과는 application key다. 체인 재고 writer는 없다. |
| 별도 구현 부담 | 추가 자료구조·인증·관계 검사·대사 기능은 무엇인가 | 탐색 자료. 명령 결과 표, slot 표, 충돌 관찰 표, entry/byte 예산, crc가 adapter에 있다. serializable 거래를 쓴다. 로컬 readiness `BackendConformance`를 이 adapter로 통과했다. 채택은 아니다. | 탐색 자료. key prefix, meta index, crc, 예산, conflict range가 adapter에 있다. 재시도 조회만 snapshot read이고 신규 성공의 쓰기 트랜잭션은 snapshot read를 쓰지 않는다. 버전 7.3.77, redundancy `single`, storage/log `ssd-2`, coordinator 1, commit proxy 3, GRV proxy 1, resolver 1, usable region 1의 단일 프로세스다. 같은 conformance를 통과했다. 채택은 아니다. |
| 확정·장애·복구 | 같은 ACK·안정 저장·허용 장애에서 어떤 결과가 남는가 | 탐색 자료. ACK는 `synchronous_commit=on`, `fsync=on`, `full_page_writes=on`의 commit 반환이다. `data_checksums=on`, `listen_addresses`는 비어 있고 유닉스 소켓만 쓴다. `autovacuum=off`는 짧은 탐색에서 retry WAL을 vacuum과 섞지 않으려는 설정이다. SIGKILL 후 디스크가 남은 재시작에서 최초 결과가 보존됐다(`restart_to_replay_ns` 323014119). checksum 불일치는 `CHECKSUM_MISMATCH`로 닫힌다. `partial`은 rollback, `crash_before_durable`은 미기록이다. 전원·OS crash는 주입하지 않았고 하드웨어 flush는 미검증이다. 내구성 동등 비교와 우열 결론은 보류다. | 탐색 자료. ACK는 commit 반환이다. zone 장애 허용은 데이터·가용성 모두 0이다. 한 호스트의 프로세스 1개는 독립 장애 도메인이 아니다. SIGKILL 후 디스크가 남은 재시작에서 최초 결과가 보존됐다(`restart_to_replay_ns` 1377877234). checksum 불일치는 `CHECKSUM_MISMATCH`로 닫힌다. 같은 in-process fault 이름을 쓴다. 전원·OS crash는 주입하지 않았고 하드웨어 flush는 미검증이다. 단일 디스크 flush와 같은 보장으로 두지 않는다. 내구성 동등 비교와 우열 결론은 보류다. |
| **상한과 멱등 조회** | 신규 쓰기 entry/byte 예산 만석에서도 검증된 최초 결과를 읽는가. 재시도가 새 WAL/log·fsync·예산을 소비하는가. 동일 ID 변조는 거절하는가 | 탐색 자료. `max_entries=3`에서 신규 성공 3, capacity 3, 이어서 기존 명령 replay 1이다. `first_capacity_index` 3, 그 뒤 표본 3건을 남긴다. capacity는 경제 효과 행을 추가하지 않는다. 동일 명령 replay 4회의 `log_delta`는 각 0이고, 그 workload의 `log_delta_sum` 976은 첫 commit 쪽이다. 동일 ID·다른 payload는 `conflict_retained` 5건이며 원 slot과 최초 결과는 유지된다. `2^128-1`(`340282366920938463463374607431768211455`)을 십진 문자열로 저장하고 다시 읽었다. signed 정수로 줄이지 않았다. 예산 숫자는 fixture다. | 탐색 자료. 같은 건수와 같은 최초 결과 조회다. 단일 디스크 WAL LSN은 없어 `log_delta`는 빈 값이다. same-command-retry의 디렉터리 크기 변화는 0바이트로 기록됐고, 프로세스 끝 데이터·로그 디렉터리는 210918811바이트로 엔진 footprint가 대부분이다. 그 0바이트를 fsync 부재의 증명으로 쓰지 않는다. u128 최댓값 문자열 왕복은 같았다. |
| **응답 유실·재시작** | 같은 명령의 최초 결과와 원래 내구성 근거를 반환하는가. cache miss나 복구 미완료를 미실행으로 처리하지 않는가 | 탐색 자료. 같은 payload의 replay는 저장된 최초 결과 문자열을 반환한다. 프로세스 재시작 뒤에도 `replayed`다. 이번 실행에서 commit 결과 unknown은 없었다. unknown을 미실행으로 바꾸는 경로는 두지 않았다. | 탐색 자료. 같은 replay·재시작 결과다. `commit_unknown_result`이면 새 업무 성공으로 재시도하지 않고 outcome `unknown`으로 남긴다. 이번 실행에서는 그 오류가 없었다. |
| 자료·운영 연결 | 관측·export·보존·업그레이드·자동화 비용 | 탐색 자료. 원시 파일은 `validation/2026-10-08-k-stage4-local-exploration/postgresql/`. 업그레이드·백업·대사 절차는 이번 측정이 아니다. 시스템 클러스터는 TCP를 열지 않았다. | 탐색 자료. 원시 파일은 `validation/2026-10-08-k-stage4-local-exploration/foundationdb/`. 패키지 기본 프로세스(`public-address auto`, storage engine memory)는 측정 대상이 아니며 시작 전에 중지했다. 측정 프로세스는 `127.0.0.1:4501`만 사용했다. |
| 인력·투자 | 책임자·장애 대응·패치·연간 유지 작업량·투자 한도 | 탐색 자료. 서버 RSS 23158784, 클라이언트 RSS 36859904, 디스크 41535867바이트. 인건비·장비 감가·전력 단가·연간 운영비·투자 한도는 **UNDETERMINED — 사용자/운영 책임자**. 장비 구매·클라우드·라이선스 지출은 없었다. | 탐색 자료. 서버 RSS 90161152, 클라이언트 RSS 56180736, 디스크 210918811바이트. 같은 총 RAM cap 536870912와 디스크 cap 268435456 안이다. 비용 단가는 **UNDETERMINED — 사용자/운영 책임자**. 지출은 없었다. |
| 동등 조건 성능 | 같은 입력검증·정합성·내구성·실패 모델의 지속 성공 goodput·지연·비용 | 탐색 자료. 입력 fingerprint `507971bd647d34dfa40d1bfbcd7089b79fc58f6a17c19e6cfac06b5f1650eec2`. warmup 2, repeats 1, arrival rate 0, concurrency 1, CPU 0–1. rate 0이라 scheduled latency는 service time과 같다. `exploration_new_success_per_elapsed_s`는 제품 TPS가 아니고 mixed nearest-rank p99는 신규 성공 p99가 아니다. low-load-uniform: 신규 8, elapsed 74301251 ns, goodput 107, 신규성공 p99 13057107, mixed p99 13057107. uniform: 신규 4, 거절 4, elapsed 50999787, goodput 78, 신규성공 p99 9159903, mixed p99 9159903. hot-seat: 신규 1, 거절 7, elapsed 49998493, goodput 20, 신규성공 p99 6627227, mixed p99 7386729. same-command-retry: 신규 1, replay 4, elapsed 25884781, goodput 38, 신규성공 p99 6574612, mixed p99 6574612. history-growth: 신규 1, conflict 5, elapsed 52018580, goodput 19, 신규성공 p99 10346253, mixed p99 10346253. saturation: 신규 3, capacity 3, replay 1, elapsed 48999080, goodput 61, 신규성공 p99 10940803, mixed p99 10940803. 장애 보장이 다르므로 우열 결론은 없다. | 탐색 자료. 같은 fingerprint·warmup·rate·concurrency·CPU cap. low-load-uniform: 신규 8, elapsed 34253600 ns, goodput 233, 신규성공 p99 5857356, mixed p99 5857356. uniform: 신규 4, 거절 4, elapsed 31300668, goodput 127, 신규성공 p99 3619502, mixed p99 5289976. hot-seat: 신규 1, 거절 7, elapsed 29250123, goodput 34, 신규성공 p99 2678442, mixed p99 4378075. same-command-retry: 신규 1, replay 4, elapsed 4072371, goodput 245, 신규성공 p99 2499899, mixed p99 2499899. history-growth: 신규 1, conflict 5, elapsed 19249927, goodput 51, 신규성공 p99 2652680, mixed p99 3765520. saturation: 신규 3, capacity 3, replay 1, elapsed 11902269, goodput 252, 신규성공 p99 3429495, mixed p99 3429495. 이 숫자를 PostgreSQL goodput과 견줘 이기거나 진 것으로 읽지 않는다. 우열 결론은 없다. |
| **외부 Sui 서명·미확정 거래 인계** | R2가 별도 승인될 경우 객체당 논리적 서명 권한 단일화와 구 리더 미확정 거래 인계를 반드시 다룬다. 동일 owned 입력 버전·전체 입력 집합, 원거래 bytes/digest/서명·effects, 실제 서명 권한 차단과 이미 노출된 거래의 대사를 구분한다. 아래 §9.1 참조. | 이번 로컬 탐색은 측정하지 않았다. R2 금지를 유지한다. 체인 writer는 없다. | 이번 로컬 탐색은 측정하지 않았다. R2 금지를 유지한다. 체인 writer는 없다. |

PR #11의 `LocalJournal::execute()`는 next sequence/byte 예산을 커널의 기존
명령 조회보다 먼저 검사한다. `max_entries=1`에서 첫 명령 응답이 유실된 뒤
동일 명령이 저널 Capacity에 막힐 수 있다. 이는 source-derived 제한이며 이번
PR에서 저널을 실행·수정하지 않는다. 검증된 읽기 전용 원결과 조회와 신규 쓰기
admission의 분리를 후보별로 비교한다. mutating reserve를 사전 조회로 호출하지
않고, 실패 명령에는 주문이 없을 수 있으므로 order lookup으로 대체하지 않는다.
원래 receipt의 sequence/hash를 꾸며 쓰지 않고 읽기만으로 시간 watermark를
비내구성 변경하지 않는다. v4의 상태 변경형 Err(Capacity)는 기록·재생 대상이다.

SQL 비교 재고와 체인 위임 재고에 동시 writer를 두지 않는다. 메모리 수치와
동기 영속 수치를 비교해 승리를 선언하지 않는다. 승인 목표·장비/비용·ACK·장애
범위를 비교 전에 정한다. 목표 없는 탐색 결과는 탐색 자료이지 자체 R2 근거가 아니다.
기존 2배/0.1% 제안은 승인 SLO가 아니다. 자체 저장 개발은 구체 비용/기능 부족,
개선 가설, 검증 방법, 운영 책임을 먼저 입증한다. 현재 착수 금지는 해제되지 않았다.

### 9.1 Sui 조사 반영 — 향후 R2의 필수 취급 범위, 착수 승인 아님

2026-09-17 문서 반영. [보존 조사 원문](research/SUI_EQUIVOCATION_REPLICATION_RESEARCH_5440de0cf721.md)
전체 Git blob은 `5440de0cf721932398af87344fe59d48b9858ad3`이며, 확인 시점은
2026-09-16~17 KST, Sui 기준은 mainnet-v1.79.1 / protocol 136 /
`58386edc269ef88ff0f40ab0a9d50e87cba80ca8`이다. [게시·검증 범위](research/SUI_EQUIVOCATION_IMPORT.md)를 함께 읽는다.

**2026-10-05 커밋 표기 보충:** 위 값은 보존 조사 기준이며, 공식 릴리스 API의
`target_commitish`와 일치한다. 실제 `mainnet-v1.79.1` 태그와 참조 `Move.toml`의
framework pin은 `808640d9b49aecf29d8e6f46033c15eca236efa7`이다. 릴리스 메타데이터와
태그 해석을 같은 것으로 읽으면 두 커밋이 섞인다. [대조 기록과 재현 명령](status/SUI_COMMIT_MISMATCH_20261005.md)은
두 기준 및 확인한 파일의 동등성 범위를 구분한다. 원문·기존 pin·역사 증거는 변경하지 않는다.

**R2 금지는 유지한다.** 별도 착수 승인이 주어질 경우 다음 두 가지를 반드시 다룬다.

1. **객체당 서명 권한 단일화:** 하나의 mutable owned 입력
   `(network, object ID, version, digest)`에 대해 미종결 상태의 서로 다른 transaction
   intent를 중복 승인하지 않는 논리적 권한을 둔다. 실제 gas coin을 쓰는 경우를 포함한
   전체 소유 입력 집합이 대상이다. 동일 거래의 조회·허용된 동일 bytes 재전달은
   다른 intent 생성과 구분한다. 머신/키 하나 또는 Raft leader 변수만으로 실제
   서명 권한의 fencing이 성립했다고 간주하지 않는다. 제품·키 구조·객체 배치는 정하지 않는다.
2. **구 리더의 미확정 거래 인계:** 원 operation과 원본 transaction bytes·digest·서명,
   전체 입력 참조, 송신/노출 기록과 검증된 관측·effects를 인계한다. 로컬 fence는
   이미 외부에 나온 유효한 서명 거래를 취소하지 않는다. timeout·단일 NotFound·기록 부재를
   미실행으로 바꾸거나 gas/nonce/version을 새로 골라 같은 업무를 재실행하지 않는다.
   과거 거래의 결과·업무 효과를 대사하고 현재 실행 허가를 따로 확인한다. 회수 cut 뒤
   재송신 허가가 입증되지 않으면 조회·대사만 한다. 세부 저장/wire/인계 구현은 이번에 하지 않는다.

원문의 §§0·1-1은 **합의 전 잠금 분열에 따른 epoch 종료까지의 동결**이 고정 Mainnet
릴리스에서 제거됐음을 설명한다. 그 과거 동결을 현행 RTO의 필수 epoch 대기나
R2 비용 증액 전제로 쓰지 않는다. **동일 버전 단일 소비와 구 리더 거래 인계는 여전히
남는다.** 원문의 §§2-1·2-2·3-2가 위 두 항목과 추정 구분의 근거다. 실제 RPC의
프로토콜/feature 상태·장애/성능은 이번에 측정하지 않았고, 잠금 제거가 모든 대기를
없앴다는 뜻도 아니다.

**독립적인 R2 작업량 추정치는 현재 없다. 숫자 없음.** 첫 묶음이나 제한된 (a)의
인일을 R2 추정으로 전용하지 않는다. 이번은 두 필수 취급 범위를 기록한 것이며,
그 두 가지의 완료만으로 모든 착수 조건이 충족되거나 R2/(a)가 자동 승인되는 것도 아니다.
객체 배치 설계·Kiosk·zkLogin·SDK/gas 모드 선정은 이번 범위에서 제외한다.

### 9.2 비교 준비 계획 — 탐색 자료 (2026-10-06)

입력은 base `403d3e29413b1e78c5da945cd33389b50d4514a4`의
[.aiops/program.json](../.aiops/program.json) 노드 `k-stage4-comparison-plan`이다.
canonical 선행은 없다. [프로그램 결정](decisions/PROGRAM_DECISIONS_20260928.md)
§2.2의 **1~2번(계획·공식 자료 선별)만** 이 산출물에 해당한다.
아래는 **탐색 자료 / exploration data**이며 측정 결과·backend 채택 결정이 아니다.
§9의 기존 비교축 표를 그대로 사용하고 별도 비교표를 만들지 않는다.

**목표와 거래 경계.** 승인된 것은 동일 업무·내구성 조건을 준비하고 기능 부족과
추가 구현 비용을 확인하는 일이다. 절대 TPS·p99·허용 실패율·RTO/RPO의 승인 수치는
없다. 2배/0.1%도 채택하지 않는다. 탐색의 기능 판정은 다음 기존 요구에 둔다.

- 합성 재고에서 명령 identity와 원payload(또는 검증 가능한 결합), 최초 결과,
  예약·최소 주문·외부 의도를 한 업무 트랜잭션으로 보존한다. 업무 거절에는 주문이
  없어도 명령 결과가 필요하다. 외부 의도 기록은 PG·은행·체인 실행이 아니다.
- 동일 ID·동일 입력은 검증된 최초 결과와 원래 commit/receipt 근거를 반환한다.
  동일 ID·다른 입력은 거절한다. 응답 유실 뒤에도 신규 경제 효과를 만들지 않는다.
  복구 미완료·조회 불능·timeout은 UNKNOWN으로 보류하며 미실행/최종 실패로 바꾸지 않는다.
- entry/byte 예산 포화에서 신규 admission과 읽기 전용 원결과 조회를 분리한다.
  retry 조회의 추가 WAL/log·fsync·예산 소비를 계측할 계획이다. 실패 결과·상태 변경형
  Capacity도 버리지 않는다. 저장소 내부 housekeeping I/O는 업무 신규 쓰기와 따로 기록한다.
- 재고 경합·GA 한도·명령 중복·관계 제약은 backend 종류와 무관하게 유지한다.
  SQL/키값 재고는 격리된 합성 fixture만 쓰며 실제 체인 위임 재고의 writer가 되지 않는다.
  u128 정본을 signed DB 정수로 축소하지 않고 표현·검증 비용을 포함한다.

**ACK와 안정 저장.** 비교 기준 ACK는 위 업무 단위의 commit 성공 및 선언한 장애
범위의 안정 저장 이후에만 반환하는 응답이다. 메모리 적용·비동기 flush·외부 자금 확인을
동일 ACK로 세지 않는다. PostgreSQL은 `fsync=on`, `full_page_writes=on`과 로컬 WAL flush를
기다리는 `synchronous_commit=on`(동기 standby 없는 로컬 구성)을 기준안으로 둔다.
FoundationDB/TiKV는 선택 버전·client API·복제 설정의 commit 완료와 안정 저장 조건을
공식 자료 및 적합성 시험으로 확인한 뒤 같은 로컬 장애 범위에 묶는다. Raft 과반 ACK를
단일 디스크 flush와 같은 장애 보장으로 단정하지 않는다. 해당 설정을 확인하지 못하면
그 후보의 내구성 동등 비교는 보류한다. cache hit에는 새 commit 근거를 만들지 않는다.

**장애 범위.** 후속 로컬 탐색의 공통 범위는 disposable backend/client 프로세스의
commit 전 중단, commit 후 응답 전 유실, 재시작, 찢긴 tail/손상 검출, 예산 거절,
동시 재고 경합과 동일 명령 경합이다. 복구 뒤 ACK된 결과 보존·중복 효과 부재·손상 시
fail-closed를 확인한다. 로컬 디스크가 유지되는 process crash와 전원/OS crash는 구별한다.
현재 Mac의 전원·OS 장애를 주입하지 않으며, 실제 stable-media flush의 하드웨어 보장은
장비 자료와 별도 검증 없이는 미검증이다. 한 host의 여러 replica는 독립 장애 도메인이
아니다. 디스크 영구 소실·host 상실·네트워크 분할·과반 상실·다중 지역·Byzantine 장애·
PG/bank exactly-once·Sui finality는 이 공통 로컬 비교의 보장 밖이다. 후보 고유 복제 장애는
별도 조건으로 표시하고 공통 성능 표본에 섞지 않는다. 자체 복제/합의 구현은 하지 않는다.

**장비·비용.** 이번 문서/공개 자료 검토에는 장비 구매·클라우드·유료 서비스·quota가
필요하지 않고 지출하지 않는다. 후속 탐색은 이미 사용 허가된 로컬 장비와 격리된 임시
데이터 경로만을 후보로 삼는다. 실행 담당자가 시작 전에 CPU/architecture·RAM·OS·디스크
모델/여유 공간/flush 특성·toolchain·backend/client 버전·프로세스/replica 수·자원 상한을
기록하고, 모든 후보에 동일한 **총** CPU/RAM/디스크 예산을 적용해야 한다. PD·proxy·
복제본·driver·관측의 자원도 총량에 포함한다. 특정 Mac에서의 설치 가능성·가용 용량은
아직 확인하지 않았으며, 이 계획은 설치나 host 서비스 가동 권한이 아니다.

기존 장비 재사용도 총비용 0이라는 뜻은 아니다. 실행 시간·저장 byte/증폭·CPU/RAM·
복구 시간·adapter 구현/유지 노력·패치/백업/대사 작업을 기록하고, 인건비·장비 감가·
전력 단가·연간 운영비·투자 한도는 **UNDETERMINED — 사용자/운영 책임자**로 남긴다.
실행자는 기능/측정 근거를, 운영 책임자는 복구·패치·보존 책임과 비용 입력을 인계한다.
새 장비·VM/클라우드·라이선스·지원 계약 등 지출이 필요하면 구매/실행 전에
**DECISION_REQUIRED**로 멈춘다. 이번 계획은 예산 승인이나 운영 책임자 지명이 아니다.

### 9.3 공식 자료 후보 선별 — 탐색 자료

2026-10-06 읽은 공식 문서의 기능 설명과 KIX 요구의 간극을 아래에 기록한다.
PostgreSQL은 18 문서, FoundationDB와 TigerBeetle은 조회 시점의 온라인 문서다.
온라인 문서는 움직일 수 있으므로 후속 실행은 실제 binary/client 버전·문서 revision과
설정을 pin해야 한다. 공식 수치/데모를 KIX 실측이나 적합성 PASS로 전용하지 않는다.

- **PostgreSQL — 우선 탐색 후보 유지.** [18 transaction isolation](https://www.postgresql.org/docs/18/transaction-iso.html),
  [18 WAL 설정](https://www.postgresql.org/docs/18/runtime-config-wal.html),
  [18 reliability](https://www.postgresql.org/docs/18/wal-reliability.html)는 serializable
  거래와 commit WAL flush/하드웨어 cache의 경계를 설명한다. 관계형 업무 단위를 묶을
  비교 기준으로 적합하나 KIX schema·명령 결과 저장·payload 충돌 검사·합성 재고 경합·
  entry/byte admission·읽기 전용 retry 경로는 별도 설계/검증이 필요하다. serialization
  failure 처리는 원 ID와 결합하고 자동 재시도를 새 업무 성공으로 세지 않는다.
  원결과 조회가 예산 포화에서도 동작한다는 실증은 아직 없다.
- **FoundationDB — 우선 탐색 후보 유지, 크기/시간 경계 확인 조건.**
  [developer guide](https://apple.github.io/foundationdb/developer-guide.html)의
  Transactions, Conflict ranges, Transactions with unknown results와
  [known limitations](https://apple.github.io/foundationdb/known-limitations.html)을 읽었다.
  ordered key-value의 다중 key 거래·serializable conflict 검사는 후보 가치가 있다.
  snapshot read/conflict range 생략은 정합성을 약화할 수 있다. 조회 문서의 거래 한도는
  affected data 10,000,000 bytes, 장기 거래는 약 5초이며 이는 **backend 제약이지 KIX SLO가
  아니다**. key/value 한도도 입력 fixture와 대조해야 한다. 관계/인덱스·재고·결과·예산을
  application layer에 표현하는 부담, client/cluster 운영·인증 경계를 포함한다.
  `commit_unknown_result`에서 미실행을 추정하거나 side effect를 retry loop에 넣지 않는다.
  KIX의 검증된 최초 결과 조회·같은 identity 보존은 별도 증명이 필요하다.
- **TigerBeetle — 이번 전체 업무 단위의 단독 backend 실측 후보에서 제외.**
  [system architecture](https://docs.tigerbeetle.com/coding/system-architecture/),
  [data modeling](https://docs.tigerbeetle.com/coding/data-modeling/),
  [linked events](https://docs.tigerbeetle.com/coding/linked-events/)는 account/transfer와
  일반 metadata 저장소의 역할을 분리하고, linked account/transfer chain의 원자성을
  설명한다. 그 기능만으로 임의 KIX 주문·예약·명령 원문/거절 결과·외부 의도를 같은
  commit에 보존하는 API는 확인하지 못했다. companion DB의 metadata commit을 linked
  transfer와 원자적이라고 가정할 수 없다. ledger 전용 throughput 비교는 요구 경계를
  줄이므로 하지 않는다. 이는 ledger 제품의 일반적 부적합 판정/채택 거절이 아니라 이
  비교의 단독 backend 범위에 대한 선별이다. 결합 backend 설계·경제 단계 판단은 별도다.
- **TiKV — 조건부 예비 후보.** 공식 website 7.1의
  [distributed transaction](https://github.com/tikv/website/blob/1578bc39bd256d4e894ce341a108be1647b9e14d/content/docs/7.1/concepts/explore-tikv-features/distributed-transaction.md),
  [replication/rebalancing](https://github.com/tikv/website/blob/1578bc39bd256d4e894ce341a108be1647b9e14d/content/docs/7.1/concepts/explore-tikv-features/replication-and-rebalancing.md),
  [fault tolerance](https://github.com/tikv/website/blob/1578bc39bd256d4e894ce341a108be1647b9e14d/content/docs/7.1/concepts/explore-tikv-features/fault-tolerance.md)
  원문을 읽었다. `tikv.org` 해당 경로는 HTTP 오류로 읽지 못해 공식 저장소의 위 commit을
  근거로 사용했다. TxnKV는 snapshot isolation과 optimistic/pessimistic write conflict를
  설명한다. SI를 serializable과 동일시하지 않으며, write skew를 막는 공통 충돌 key/관계
  검증이 KIX 불변식을 보존하는지 후속 적합성 시험이 필요하다. RawKV 데모는 다중 key
  업무 거래 증거가 아니다. Region Raft replicas와 PD의 추가 자원/운영 부담도 포함한다.
  선택 release/client의 ACK·flush 설정 및 전체 업무 mapping 확인 전 우선 실측군에 넣지
  않는다. 문서의 노드 장애 데모가 이 Mac의 독립 host 장애 보장을 뜻하지 않는다.

우선 비교 준비군은 PostgreSQL/FoundationDB 두 개다. 두 후보도 아직 채택/적합성 PASS가
아니다. TiKV의 조건이 충족되면 후속 노드에서 같은 범위로 비교 여부를 기록한다.
기성 제품의 문서상 불일치/미확인만으로 자체 KIX 저장 엔진이나 R2를 정당화하지 않는다.

### 9.4 기존 증거·후속 실행 인계

기존 coverage는 다음과 같이 구분한다. 새 runtime test나 backend adapter는 이번에 추가하지 않는다.

- **충분히 covered(요구/측정 의미):** §9의 기존 비교축과
  [PERFORMANCE_MEASUREMENT](contracts/PERFORMANCE_MEASUREMENT.md)는 신규 성공·업무 거절·
  retry·Capacity와 scheduled/service latency·포화 이후 표본 보존을 정의한다.
  `runtime/crates/kix-kernel/tests/performance_harness.rs`는 memory-only 장치 회귀이며
  backend I/O 실증이 아니다.
- **부분 covered(로컬 fault 시나리오):** `readiness/test_faults.py`의
  `StoreTests.test_torn_tail_is_discarded_and_a_bad_checksum_fails_closed`와
  `readiness/conformance.py`의 `test_budget_rejection_preserves_records_and_replay_identity`,
  `test_settlement_crash_before_durable_authorize_applies_once`,
  `test_concurrent_reservation_holds_occupy_the_slot_once` 등은 torn write·복구·예산·
  중복·경합을 다룬다. readiness의 비운영 local adapter 증거이며 네 후보의 PASS는 아니다.
- **이번 문서로 채운 gap:** 동일 업무/ACK/장애/장비·비용의 준비 계획과 공식 자료 선별.
  **not covered:** 후보별 실제 mapping·동등 내구성·포화 원결과 조회·goodput/p99/비용 실측·
  hardware flush/독립 장애 도메인 검증. 이를 자료 조회나 memory smoke로 완료 처리하지 않는다.
  이 not covered는 계획 노드 시점의 인계다. 그 뒤 로컬 탐색이 채운 범위와 여전히 비어 있는 범위는 §9.5다.

후속 `k-stage4-local-exploration`의 canonical 선행은 이 노드와
`k-readiness-conformance-suite`다. 실제 승인/병합 근거를 host가 확인한 뒤, 실행자는 동일
입력·검증·예산·총 장비 자원·ACK·장애 범위를 고정하고 버전/설정과 fixture/seed를 남긴다.
저부하·균등·hot seat·동일 명령 retry·이력 증가/포화를 분리하며 신규 성공 goodput과
outcome별 scheduled/service latency, 원시 표본·거절·오류·복구·공간/비용을 보존한다.
warmup·실행 길이·반복·도착률·동시성은 탐색 설정으로 명시하고 제품 목표로 승격하지 않는다.
업무 경계나 장애 보장이 다르면 우열 결론을 보류한다. 이 절은 그 실행을 하지 않았다.
실행 기록은 §9.5다.

I02~I13의 미완결 정책/외부 입력은 [열린 입력](contracts/FIRST_BATCH_OPEN_INPUTS.md)의
담당과 상태를 유지한다. 보존기간·제공자 보증·권위 cut을 이 선별로 결정하지 않는다.
인계 완료는 이 Mac 구현 단계의 문서 준비를 뜻한다. A2 비작성자 review, app의 Draft
게시 이후 실제 exact-head KTX/KIX CI와 독립 최종 supervision은 여전히 필요하며,
skipped/absent CI는 전체 검증 PASS가 아니다. backend 채택은 별도 사용자 결정,
5단계는 채택 결정 병합과 v5 선행, R2는 §5 잠금 해제 근거/사용자 승인 뒤다.

### 9.5 로컬 탐색 실측 — 탐색 자료 (2026-10-08)

이 절은 §9 비교표의 측정 조건과 원시 파일 위치다. 후보별 답은 위 비교표의
PostgreSQL·FoundationDB 열에만 적는다. 다른 파일에 두 번째 비교표를 두지 않는다.
결과는 **탐색 자료**다. 제품 SLO, backend 채택, 내구성 우열, R2 근거가 아니다.

측정 시작 전에 기록한 host는 `validation/2026-10-08-k-stage4-local-exploration/host.json`이다.
그때의 `origin/main`과 HEAD 커밋은 `7481b0e16ce9b903abbffa62249bb91cd9e63cfe`다.
탐색 코드는 그 커밋 위의 작업 트리에서 실행됐다. 그 SHA 안에 이 절이 들어 있다는 뜻이 아니다.
잠금 blob 두 개는 그 시점에 일치했다. 기계는 Linux 6.12.94+ x86_64, CPU 8
(측정은 affinity 0–1), Intel Xeon(가상), MemTotal 16397616 kB, MemAvailable 6244004 kB,
swap 0, 디스크 vda/vdb 128G rotational 표식 1·모델 문자열 없음, overlay 여유
31741984768바이트다. 하드웨어 flush 특성은 장비 자료가 없어 미검증이다.
Python 3.13.5, PostgreSQL 17.11 (Debian 17.11-0+deb13u1), FoundationDB 7.3.77
(source `3ea44ce1d9003ad095e408039e1f755c319c4dfb`, protocol `fdb00b073000000`).
두 후보에 같은 총 cap을 적용했다. CPU 2코어, RAM 536870912바이트(서버 RSS와
클라이언트 RSS의 합), 디스크 268435456바이트(데이터와 로그). FoundationDB 프로세스
한도는 memory 384MiB, storage-memory 96MiB, cache-memory 64MiB다. PostgreSQL
`shared_buffers`는 64MB다. 둘 다 cap 안에서 끝났고, 후보를 동시에 띄우지 않았다.

탐색 설정은 warmup 2, repeats 1, arrival rate 0, concurrency 1이다. rate 0은
열린 루프가 아니다. 업무 입력 fingerprint는
`507971bd647d34dfa40d1bfbcd7089b79fc58f6a17c19e6cfac06b5f1650eec2`다.
재고는 합성 fixture이고 체인 위임 재고의 writer가 아니다. TigerBeetle은 §9.3의
단독 backend 제외를 유지해 실행하지 않았다. TiKV는 §9.3의 release/client ACK
조건이 이 실행에서 새로 충족되지 않아 같은 실측군에 넣지 않았다.

공통 기능 확인은 `readiness.conformance.BackendConformance`를 각 adapter에
결합한 로컬 unittest다. 통과는 production conformance가 아니다. 원시 요약은
`postgresql/summary.json`, `foundationdb/summary.json`과 각 `samples.csv`다.
재현은 저장소 루트에서 `python3 scripts/stage4_local_explore.py validation/2026-10-08-k-stage4-local-exploration`이다.
로컬 PostgreSQL 17 바이너리와 FoundationDB 7.3.77 클라이언트·서버가 필요하며,
공개 주소로 열지 않는다.

이 실행이 채운 것: 두 우선 후보의 로컬 업무 mapping, 공통 conformance, 예산 포화
뒤의 원결과 조회, 프로세스 crash(디스크 유지) 후 보존, 탐색 설정의 goodput·지연·
바이트·RSS. 여전히 비어 있는 것: 하드웨어 flush, 전원·OS crash, 독립 장애 도메인,
동등 내구성 판정, 인건비·전력·연간 운영비(UNDETERMINED — 사용자/운영 책임자),
TiKV, 채택, R2. 기성 제품의 이 결과만으로 자체 저장 엔진이나 R2를 열지 않는다.

## 10. backend 선택 이후 영속 거래

명령·원payload·최초 결과·예약·최소 주문·외부 의도를 원자적으로 보존하고,
commit/응답 전후 장애에서 복원한다. inbox 수신 보존과 경제 효과 적용은 구별한다.
PG/은행/체인 호출은 커널 밖에서 stable operation identity로 수행한다.
신규 유입과 완료·관측·취소·복구의 count/byte/age 예산을 구분한다.
writer 차단과 이미 보낸 외부 요청의 종결은 다르다. 실제 backend의 장애 모델로
검증하며 기성 DB가 제공하는 로그를 불필요하게 다시 만들지 않는다. 전부 미착수다.

## 11. 경제 기능

자산/정책 인증, OrderLine·불변 견적·무료 주문·복잡 할인·묶음, 다중 intent·
부분/복수 capture·배분·초과금, 반환의무·환불예약/실행·분할정산·미지급금,
리셀 권리 이전과 판매자 지급, 복수 티켓·쿠폰·한도·잔액·다중 자산 결합을 유지한다.
기존 계산 계약과 실제 제한된 유상 흐름을 이관표에서 구분한다. u128 정본을
DB signed 범위에 맞춰 조용히 줄이지 않는다. Fast64는 승인 프로파일에 한한다.
sandbox와 실제 인증·자금 계약은 다르다. 토스페이먼츠 일반 카드 경로를 잠정
선택했지만 **실제 MID·가맹 허용 범위·일반 결제 웹훅 서명 규격은 아직 미확정**이다.
종결 정의는 LC-TERM 0.3에서 닫혔고 현행 계약은 0.6이다. 제공자의 영구 비실행 보증을
필수로 기다리지 않는다. 실제 사건의 조건 충족·유효한 승인·내구 기록과 후속 조치의
별도 조건은 여전히 필요하며, 정의가 닫힌 것이 실행 구현·사건 승인 완료를 뜻하지 않는다.
사용자에게 리셀·금융 범위의 영업 확인이 남아 있으며, 그 전까지 해당 대금의 운영 수취는 막는다.
PG 선택을 다시 미정으로 쓰거나 잠정 선택을 모든 경제 기능의 가맹 승인으로 읽지 않는다.

## 12. Move·권리·프라이버시

모델 1의 chain inventory/Right, 배타 grant·회수·미발행 약정 보존·잔여 회수,
취소 placement 및 현재성, 지정석·GA·SaleIntent·PaymentEvidence·검표 nullifier,
비공개 증명·권한, 운영 ZK와 키 이관을 닫아야 한다. 실제 grant·비협조 회수는
미구현이므로 위임 실행 비활성을 유지한다. 체인 클라이언트나 자체 암호를 이번에
추가하지 않는다. 기존 shared-Show Move는 회귀 자산이다.

## 13. 데이터 처리

인증된 일관 export부터 구현하고 source cut과 projection watermark를 구분한다.
Rust 기준 의미론과 Polars·DuckDB를 null/정렬/join/overflow/정수 금액/버전으로
대조한다. 분석 자원은 거래 경로와 분리한다. fixture 검증을 운영 연동으로 표시하지
않는다. native libcudf는 검증·변환·전송·계산·회수 전체 비용과 no-fallback 결과로
판정한다. 연속 3개 scale 비교 조건은 유지하되 실제 결과는 없다. 작은 작업 대기,
큰 작업 메모리·GPU 장애에서도 거래 영향 범위를 평가한다. GPU는 금융/AI 선행 아님.

## 14. 응용 확장

팬 자격·선예매·쿠폰·추천 보상이 거래를 바꾸면 공통 검증에 결합한다. 캠페인
편집·추천 UI·CRM은 별도 제품이다. 금융은 권리·정산채권·채무·부담을 구별하고,
실제 심사·지급통제·계약을 별도 검증한다. AI는 조회/제안/실행 권한과 scope·금액·
기간·회수 조건을 구별하며 모델 출력만으로 발행/지급하지 않는다. 두 독립 클라이언트
적합성 검증을 먼저 하고 frontend 출시를 공통 프로토콜의 선행으로 만들지 않는다.

## 15. 노력 추정과 승인 경계

원안 첫 묶음은 E-4 3~5 + 수명 계약 4~6 + 성능 계약·장치 3~5 = **추정 10~16인일**.
이 합계는 승인된 작업량 범위이며 이번 PR을 그 전부 완료로 표시하지 않는다.
상태 수명 후속 구현을 포함한 원안 R1 관련 추정은 16~26인일, 초기 성능 별도
3~5인일이었다. 지금 그 후속 구현 전체를 승인한 것은 아니다.
모델1의 (a) 16~26인일 추정은 첫 묶음 수명 계약과 중복이 있으므로 단순 합산하지
않는다. 중복 산출물이 닫힌 뒤 잔여 구현만 다시 산정한다. 인일은 1인 전담 노력이고
실제 달력 기간·운영 인력·법적/제공자 협의 대기는 별도다. 전체 총기간은 미정이다.

## 16. 증거와 진척

각 PR에 base/head·파일 blob·실제 CI SHA·결과·한계·원시 자료를 남긴다.
부분 구현 근거와 원래 32항목의 종단 상태를 분리한다. E02의 현재 블록은
'KIX 권위 계층'이며 원래 외부 그룹은 역사적 매핑으로만 남긴다. 새 그림은 만들지
않는다. 원표의 31/1은 유지하고 부분 앵커 연결 수·고유 수와 E-4/측정 실행
근거를 보조 지표로 기록한다. 부분 코드/시험 개수로 전체 구현을 승격하지 않는다.

이번 게시가 main 병합이나 기존 #11/#12 정리, 태그 발행, 저장 backend 채택을
뜻하지 않는다. 신규 작업선에서 문서·시험을 게시하고 기존 소스 잠금을 대조한다.

## 17. 2026-09-28 main 반영 현황과 결정

아래 9월 28일 목록과 CI는 당시 기록이다. 후속 [로드맵](decisions/PROGRAM_ROADMAP_20260930.md) R-7은 commerce `w6a-evidence` 병합을 Wave 7 조건부 게이트로 정했고, R-8은 commerce #1·#3~#12의 stub·mock·loopback 병합분을 사후 승인했다. #13 CI는 게이트 뒤 병합분이다. #3 마케팅 stub은 stub으로만 인정하며 Wave 7 개방 전 계약에 결합하지 않는다. 이를 Wave 6 전체 완료나 외부 선행의 완료 증거로 읽지 않는다.

현재 Mac 노드 입력은 [.aiops/program.json](../.aiops/program.json)의 `roadmap-sync`이며 canonical 선행은 없다. pending/external 항목은 [pending catalogue](decisions/PROGRAM_ROADMAP_20260930_PENDING.json)에 보존한다. [확대 후보](aiops/PROGRAM_EXPANSION_20261002_KO.md)·[등록 범위](aiops/REGISTRATION_SCOPE_APPROVAL_KO.md)의 별도 채택 전에는 현재 계획을 후보 집계로 바꾸지 않는다. 별도 채택 시 immutable 후보의 protocol active 67/pending 1, commerce active 10/pending 20 포인터·집계를 반영하고 과거 결정·증거·집계는 그대로 연결한다.

2026-09-25~27 main에는 다음이 병합됐다. 목록·CI 상태·근거 표시는 [main 상태 정합 기록](status/MAIN_STATE_20260928.md)에 있다.

- Task 004 측정 장치(§7)
- [Task 005](tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md) Wave 2~5 산출물
- 계약 전용 OpenAPI, loopback HTTP 관문, 로컬 readiness 파일 저널

같은 날 사용자가 D-1~D-3의 결정을 위임했다. 결정안은 사용자가 PR #73을 병합(`cfeb0d6`)하면서 승인됐고, 전문은 [프로그램 결정](decisions/PROGRAM_DECISIONS_20260928.md)에 있다.

- **D-1 — 두 트랙 병행:** Track P(Task 005)를 승인 범위에 편입한다. Track K는 4단계 비교 준비를 연다.
- **D-2 — Wave 게이트:**
  - Wave 2~5와 후속 병합분(#59~#71)을 사후 승인한다. 조건은 hosted CI 복구 뒤 main 확인이다.
  - Wave 6 게이트를 연다(`kix-commerce-apps`).
  - Wave 7은 Wave 6 정합 뒤에 연다.
- **D-3 — readiness 저널:** 비운영 로컬 래퍼로 허용한다.
  - 단일 프로세스, 단일 작성자, 기본 비활성으로 한정한다.
  - 복제·합의·운영 정본은 금지한다.
  - fault suite는 backend 공통 적합성 시험으로 재사용한다.

다음은 여전히 없다. 해제 조건은 결정 문서 §5에 있다.
- 실 PG·은행·KYC·체인 mainnet 호출
- 공개 운영 엔드포인트
- R2
- 커널 잠금 변경

backend 기록의 위치는 §5 「병합된 문서 위치(2026-10-09, 위치 안내만)」 표다.

2026-09-26 이후 병합분의 hosted CI 성공 기록은 Actions 사용량 복구 뒤 생겼다. #59~#74를 포함한 main `60e7683`에서 두 workflow가 성공했다(run ID는 [기준 표](status/BASELINES.md)). #73·#74는 그 전에 사용자 지시로 CI 예외를 적용해 병합했다.

## 18. 2026-09-29 — 선택적 자체 토큰 계층과 확장형 권리·재고·검표 계층의 범위 편입

사용자 요청으로 아래 두 항목을 개발 범위에 편입한다. 근거·한계·기존 제한과의 공존은
[범위 편입 결정 기록](decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md)이 정한다.
PR #79의 사용자 병합(`5cf4168`)으로 효력이 생겼다. 후속 범위는 [로드맵](decisions/PROGRAM_ROADMAP_20260930.md) R-1~R-3을 함께 따른다.
**이 절의 범위 승인은 개별 노드 착수 게이트·감사·배포·토큰 발행 승인을 대체하지 않는다.**

| 보완 항목 | 성격 | 청사진 | 현재 상태 |
|---|---|---|---|
| **TL** 선택적 자체 토큰 발행·운영 계층 | 독립 개발 대상. 토큰 없이도 기본 예매·이전·검표·환불·정산이 성립해야 한다 | [optional-native-token-v1](blueprints/optional-native-token-v1/README.md) | 구체 설계·구현 미완료. 토큰 모듈 없음 |
| **RS** 확장형 권리·재고·검표 계층 | 핵심 개발 과제. 16슬롯 참조 프로파일은 회귀 기준으로 보존하고, 새 프로파일은 구조를 바꿔 16을 넘는다 | [rights-scale-v1](blueprints/rights-scale-v1/README.md) | 16슬롯 참조 프로파일만 있음 |

### 18.1 승인된 것과 승인되지 않은 것

| | 범위 편입과 후속 로드맵 | 유지되는 조건·잠금 |
|---|---|---|
| TL | R-1은 D-B 수락: TL-A → TL-0 → TL-1. R-3은 U2(담보)·U3(보상) 설계 범위이며 최종 확정은 사용자 tl-0 병합. TL-3 off-chain은 TL-1 뒤, on-chain은 TL-2와 off-chain 뒤 | **coin/TIX 잠금 유지.** 유일한 TL-2 localnet 예외도 Astra 재결정과 사용자 tl-coin-lock-adr 병합 뒤. TL-4 검증·TL-5 운영 판단은 선행을 충족해야 하며 실자금·운영 발행은 미승인 |
| RS | R-2는 D-D의 독립 객체 분할 및 rights·zk_gate 확장 해석을 조건 (a)~(e)와 함께 수락. RS-0 설계·감사 뒤 새 프로파일 RS-1 → RS-2·RS-3a → 단계별 RS-4 localnet 검증 | coin/TIX 불포함, 16슬롯 참조 불변, localnet 한정. RS-3b는 RS-3a와 Track K v5 별도 승인·구현 선행. 수명 전이를 R-2만으로 승인하지 않음. 운영 배포·커널 잠금 변경 미승인 |

현재 문서 포인터:

- TL: TL-A ADR [ADR-0002](adr/0002-token-layer-scope-and-limits.md) 병합됨(#126). 범위·한계 기록이며 coin/TIX 잠금 해제가 아니다.
- RS: RS-0 프로파일 0.1·결정 기록 병합됨(#125): [프로파일](contracts/RIGHTS_SCALE_PROFILE.md), [결정 기록](decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md). 확정 조건은 그 문서가 정한다.

병합된 TL 문서 위치(2026-10-09, 위치 안내만): 아래 표는 위치와 현재 상태만 적는다. 채택 문장은 병합된 파일의 문장을 그대로 옮긴 것이며, 「문장 수정 없이」 조건이 지켜졌는지는 이 표가 판단하지 않는다.

| 문서 | PR | 병합 커밋 | merged_by | 문서 자체의 채택 문장(원문) | 효력 표기 |
|---|---|---|---|---|---|
| [토큰 역할·공급 (TL-0)](contracts/TOKEN_ROLE_AND_SUPPLY.md) | #145 | `5714603158ddac1a5dcbe2e645c902e26f2b20a9` | BeautifulMind-JT | 사용자가 이 문서를 문장 수정 없이 병합하면, 이 문서에서 「권고」로 표시한 갈래만 채택되고, `DECISION_REQUIRED` 또는 `UNDETERMINED`로 적힌 값은 멈춘 채로 남는다. 이 채택은 새 coin/TIX 모듈 잠금의 해제도, `tl-coin-lock-adr`도, Astra 재결정도 아니다. | 효력 발생(User 병합) |
| [토큰 가격원 기록](decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md) | #146 | `28539987d1e676f0724081c41b22db51e731a967` | BeautifulMind-JT | 상태: 기록. 가격원 계약의 초안이 아니다. 효력은 사용자가 이 기록을 병합할 때에만 생긴다. | 효력 발생(User 병합) |
| [토큰 권한·수명 (TL-1)](contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md) | #147 | `841408e77065c841ea73e2cf04fe8c03fbd35f5d` | BeautifulMind-JT | 사용자가 이 문서를 문장 수정 없이 병합하면, 이 문서에서 「권고」로 표시한 갈래만 채택되고, `DECISION_REQUIRED` 또는 `UNDETERMINED`로 적힌 값은 멈춘 채로 남는다. 이 채택은 새 coin/TIX 모듈 잠금의 해제도, `tl-coin-lock-adr`도, Astra 재결정도 아니다. | 효력 발생(User 병합) |
| [ADR-0003 coin/TIX 잠금 재결정 요청](adr/0003-coin-tix-lock-localnet-re-ruling-request.md) | #148 | `ad3cee9e6aa68aa14c3b35901f66b6cab40cf75a` | BeautifulMind-JT | Status: proposed. This is a User decision document. … A lift of the new coin/TIX module lock takes effect only if an Astra re-ruling exists before that merge. Writing this file does not lift the lock. | 병합됨(User). Astra 재결정 기록 없음(ADR §5). 잠금 변경 없음 |
| [TL-2는 열리지 않음](decisions/TL2_DOES_NOT_OPEN_20261009.md) | #149 | `1cb2d26c4b6d8cc7aa2d362bf017e4d30f5a2080` | BeautifulMind-JT | 상태: 기록. 패키지가 아니다. 효력은 사용자가 이 기록을 병합할 때에만 생긴다. | 효력 발생(User 병합) |
| [token_reward 참조](../reference/token_reward/) | #150 | `fff19605f0ccff71b6f24e61f1f8114b5c0ddd57` | BeautifulMind-JT | 기록된 채택 문장 없음(소스 디렉터리). Offline reference predicates for reward–transaction coupling. | 효력 발생(User 병합) |
| [외부 검토 질문서](status/TOKEN_LEGAL_REVIEW_BRIEF_KO.md) | #151 | `c2cde86e21a6e5ba6f24a56548636db6d0a34c6f` | BeautifulMind-JT | 상태: 질문서만이다. 전송하지 않았다. 자문 주체의 이름, 조직의 이름, 착수 시점을 적지 않는다. 작성자가 빌더이므로 비작성자 검토가 아니고, 법률 의견이 아니다. 검토됨으로 표시하지 않는다. | 효력 발생(User 병합) |

### 18.2 의존성과 우선순위

- TL과 RS는 **서로의 선행조건이 아니다.** 다른 트랙에 대한 **직접** 의존은 RS-3b가 Track K(2단계 v5 설계·승인·구현)에, TL-2가 새 coin/TIX 모듈 잠금 해제에 두는 것뿐이다. TL-3의 온체인 부분과 TL-4·TL-5는 TL-2를 거쳐 간접 의존하고, TL-5는 프로그램 결정 §5에도 직접 의존한다. 현재 canonical 선행은 `.aiops/program.json`의 각 노드 정의를 따른다.
- 진행 중이거나 예정된 Track K·Track P 작업은 이 편입 때문에 중단하거나 순서를 바꾸지 않는다.
- 권고 순서는 RS-0(문서)을 먼저 두고, TL-A(ADR)를 거친 TL-0(문서)와 외부 검토(TL-L)를 RS-0과 병행하고, 이어서 RS-1·RS-2·TL-1, 그다음 RS-3a·RS-4·TL-2(잠금 해제 뒤)다. 세부는 결정 기록 §5.
- 후속 작업의 설계 근거·인수 조건은 두 청사진의 §8(RS)·§12(TL)에 있다. **청사진 자체는 작업문서나 dispatch 대상이 아니다.** 현재 노드의 완전한 spec·선행은 `.aiops/program.json`에 보존하며, 실행 입력은 승인된 orchestrator/host가 작성자 세션 밖에서 확정한다.
- 원래 32개 항목의 라벨과 31/1 집계, 과거 Task 005와 9월 28일 결정은 바꾸지 않았다. TL·RS는 관련 행에 연결만 한다(결정 기록 §5.4).
