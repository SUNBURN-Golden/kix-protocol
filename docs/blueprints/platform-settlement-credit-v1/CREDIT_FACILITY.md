# KIX 여신·선지급·회수 설계

공통 명칭·체인/원장/은행 간 순서와 권위는 [CROSS_BOUNDARY_CONTRACTS](CROSS_BOUNDARY_CONTRACTS.md)를 함께 따른다. 본문 논리 상태와 토큰 표현을 별도 경제 자산으로 중복 계상하지 않는다.

상태: **제안 설계**. 기준 소스는 main `6dbf8dfed6ee790e2ee56b49a75b727edd9db977`의 `docs/DEVELOPMENT_PLAN.md`, `docs/contracts/STATE_LIFECYCLE.md` 0.6 및 `reference/v0.3-rc1/finance.py`다. 현재 Rust 커널에 이 여신 엔진이 구현됐다는 뜻이 아니다. 생산 소스·잠금 파일은 변경하지 않았다.

## 1. 첫 금융 구조

**첫 실행형은 특정 금융기관/적법한 금융사업자와 특정 주최자 사이의 기명 여신한도(facility), 지정 수취·통제계좌, KIX의 기술·원장·servicing 결합을 권고한다.** 그림의 자본 공급자 → KIX → 공연장·주최자는 권한·명령·기록의 연결이다. 실제 원화는 계약상 지급 주체의 은행/PG 계좌를 통해 이동한다. KIX가 자동으로 예금을 수취하거나 금융기관이 되는 설계가 아니다.

공개 투자자 pool, 예금형 상품, 무허가 중개, 고객 환불자금 재대출을 초기 기본값으로 두지 않는다. 여러 기관 참여, 채권매입/factoring, 증권형 조각투자는 같은 데이터 모델 위의 별도 상품·계약·인가 경로로 확장할 수 있다. 협력 금융기관이 있다는 사실만으로 KIX의 실제 모집·중개·추심 행위가 허용되는 것도 아니므로 행위와 계약당사자를 별도로 정한다.

금융상품을 두 개로 나눈다.

| 상품 | 기초와 위험 | 첫 정책 |
|---|---|---|
| 정산채권 선지급 | 이미 발생하고 채무자·금액·정산일·공제 사유를 식별한 정산채권. PG 확인과 법률상 권리는 별도 증거 | 적격채권만 borrowing base에 편입. 미확인 결제·취소분·분쟁분 제외 |
| 공연 전 제작·운영자금 | 아직 발생하지 않은 티켓 매출, 공연 이행·판매율·주최자 신용에 의존 | 별도 프로젝트 여신한도·자기자본·보증/신용보완·단계별 지급. 예측매출을 확정 정산채권으로 등록하지 않음 |

공연장이 실제 차주라면 공연장 facility, 주최자가 차주이고 공연장이 지정 지급처라면 `UseOfProceedsPayee`로 기록한다. 돈을 받은 주체와 법률상 채무자를 혼동하지 않는다.

## 2. 권리·채권·채무의 분리

| 객체 | 핵심 필드 | 책임·구분 |
|---|---|---|
| AdmissionRight | show/seat-or-GA, holder, policy, issue/transfer/use/cancel 상태 | 관객 입장권. 주최자 대출의 담보 토큰으로 자동 전용 금지 |
| SettlementClaim | creditor/debtor, contract, source allocation IDs, asset, outstanding, maturity, defenses, refunds, source cut | 주최자 등의 정산채권. 티켓 판매가 발생했다고 무조건 확정되지 않음 |
| EligibleReceivableLot | claim ID/version, eligible amount, exclusions, haircut, legal verification, control status | 특정 facility의 담보평가 대상. 평가 결과와 원래 채권은 별개 |
| CreditFacility | lender/borrower/servicer, contract, asset, limit, maturity, draw policy, covenants, recourse, authority | 기명 약정. 한도와 실제 대출잔액 분리 |
| DrawCommitment | immutable request, facility version, amount, cash reservation, allocation, bank operation, state | 승인·예약된 미실행/결과불명 실행도 한도 점유 |
| CreditPosition | original principal, funded outstanding, accrued contract charges, paid totals, arrears | 자금 공급자의 대출채권. 차주 원장에는 대응 채무 |
| Encumbrance | exact claim slice, facility, amount/extent, rank evidence, valid from, release condition | 담보 부담. 외부 담보·법적 우선순위는 별도 확인 |
| RefundProtection | asset, show, liability/risk basis, restricted cash, guarantee, shortfall | 고객 반환 자금과 여신 재원을 분리. 준비금 비율이 전체 취소를 보장하는 것은 아님 |
| CollectionAllocation | bank movement ID, source claim IDs, facility, principal/interest/other allocation | 입금 사실과 상환 적용은 별개. 같은 입금 이중 상환 금지 |
| WaterfallPolicy | beneficiaries, order, caps, reserve method, contract version, approval | 계약에 따른 배분. 법률상 우선변제권을 생성하지 않음 |
| CreditDecision | verified inputs/cut, risk model version, proposed limits, approver, conditions | AI 예측과 금융기관 승인 분리 |
| CovenantEvent / RecoveryCase | actual breach/evidence, cure deadline, freeze, enforcement authority, recoveries | 회수·손실·분쟁. 장부상 상각이 법률상 면제와 같지 않음 |

금액은 자산·registry version/hash와 결합된 정수 원자로 계산한다. 원화와 SUI 또는 stablecoin을 한 잔액으로 합치지 않는다. FX는 별도 계약·가격시점·노출·실제 환전 사실을 기록한다. multi-asset 지원은 원화 facility의 암묵적 담보 확장을 뜻하지 않는다.

## 3. Sui/Move는 실제 금융 상태를 표현한다

단순 해시 앵커만 두지 않고 다음 **제한된 양도형 금융 객체**를 설계한다. 이름은 신규 제안이며 이미 구현된 crate/type 명칭이 아니다.

| Move 객체/전이 | 실제 온체인 기능 | 온체인만으로 증명하지 못하는 것 |
|---|---|---|
| `ReceivablePosition` 발행 | 검증된 claim ID·금액·자산·원천 allocation·법률문서 commitment를 한 객체로 기록. 동일 origin의 재발행 차단 | 원천 채권 실재·항변·제삼자 담보 부존재 |
| `split_position` / `merge_position` | 원 객체를 소비/갱신하고 자식 금액 합계 보존. slice 단위 배분 | 분할채권 양도의 실제 법적 효력 |
| `transfer_position` | 수취인 허용목록, 현재 부담, 정책, 승인 증거를 확인하여 소유권 전이 | 민법상 통지·승낙 및 제삼자 대항요건 완료 |
| `pledge_position` / `Encumbrance` | exact slice를 특정 facility에 잠금. 같은 slice의 중복 부담 생성 거절 | 외부 금융기관에 이미 담보제공된 사실 탐지 |
| `FacilityPosition` / `CreditPosition` | 기명 facility, 승인한도와 실제 funded principal, 상환누계를 연결 | 토큰 민팅만으로 은행이 실제 대출 실행했다는 사실 |
| `apply_collection` | 검증된 외부 입금 attestation ID를 한 번만 적용하고 원리금/잔액을 변경 | 실제 은행 이체의 독립 확정. attestor 신뢰 필요 |
| `release_encumbrance` | payoff/cure 조건·지정 권한·외부 해제증거 확인 후 특정 부담 해제 | 법률상 담보 해제절차 자동완료 |
| `retire_position` | paid/cancelled 상태와 이력 고정, 재사용 차단, 잔액 0 조건 | 이력 삭제 또는 과거 사실 취소 |

초기에는 광범위한 `public_transfer` 경로를 노출하지 않고 모듈의 검증된 이전 함수만 허용하는 객체 설계를 검토한다. `key/store` 능력 선택과 wrapper 우회 여부는 Move 구현 때 직접 시험한다. 제한형·비대체성이라는 이유만으로 법적 증권성 판단이 면제되지는 않는다.

`ReceivablePosition`은 차주의 정산채권을 표현하고 `CreditPosition`은 대주의 대출채권을 표현한다. 담보로 묶인 정산채권과 대출채권을 각각 동일한 free cash 또는 투자자 원금으로 더하지 않는다. 채권 자체의 완전 매입/factoring 상품으로 바꾸면 `legal_form`과 인식·소유권·회수정책을 새 상품으로 구분한다.

금융 객체의 현재 version과 facility 한도를 함께 소비/갱신하는 원자적 Move 전이를 사용한다. 금융 facility 객체의 경합은 금융 lane에 한정하며 모든 티켓 예약이 이 객체를 쓰도록 만들지 않는다. 은행 지급과 Move 전이는 분산 원자 transaction이 아니다. 원화 실행에 앞서 담보 잠금/승인을 확정하고, 불명 상태의 지급은 reservation을 유지하며 대사한다. 체인 commit 성공만으로 fiat 지급 완료를 응답하지 않는다.

`LegalAttestation`, `ProviderFactAttestation`, `BankMovementAttestation`은 발급 주체·scope·정책 버전·원문 위치·검증시점·유효기간/폐기상태·idempotency를 명시한다. 법률 증거와 은행 증거는 다른 권한으로 서명한다. public chain에는 주민정보·계좌번호·계약 원문·신용평가 상세를 올리지 않는다. 작은 개인정보를 그대로 hash하는 것도 사전대입 위험이 있어 비식별 ID와 접근통제된 증거저장소를 사용한다.

## 4. 차입가능액: 한도·담보·현금 세 가지를 동시에 검사

정산채권 facility의 평가 시점 `t`에서, 자산별로 계산한다.

```text
U_i = 해당 채권의 미수 잔액 (이미 실현된 수수료·세금·정산공제 반영 여부를 고정)
X_i = 미수 잔액 안에서 제외하는 고유 금액 구간의 합집합
      (취소, 환불/차지백 위험, 분쟁, 양도 불가, 외부 선순위 부담 등)
E_i = max(0, U_i - X_i)
BB_receivable = concentration_caps(sum(floor(E_i * advance_rate_i)))
C_pledged = 이 facility에 유효하게 귀속된 적격 담보 현금
            (고객 환불 보호금·이미 지급 예약된 현금 제외)
BB = BB_receivable + C_pledged
Exposure = funded_principal + live_draw_commitments + other_counted_exposure
CreditHeadroom = max(0, min(contract_limit, BB) - Exposure)
FundingHeadroom = max(0, provider_eligible_cash_balance - existing_cash_reservations - other_restricted_cash)
NewDraw <= min(CreditHeadroom, FundingHeadroom, approved_draw_limit)
```

`other_counted_exposure`에 이자·보증 등을 포함할지는 facility가 정한다. 예제에서는 0이다. 같은 환불 금액을 채권 `U_i`에서 이미 차감했다면 다시 `X_i`로 차감하지 않는다. 복수 사유가 같은 10원에 붙으면 금액 합집합은 10원이며 20원 공제가 아니다. haircut의 위험 커버 범위를 명시해 별도 공제와 임의 중복하지 않는다. 보수적 중복 haircut을 의도하면 그 정책 자체를 승인·설명한다.

**숫자 예시 — 단위 백만원, 사업 정책 제안이 아닌 산술 예제.** 미수 100, 중복 제거한 제외분 20, advance rate 80%, 담보 현금 10 → BB = 80×0.8+10 = 74. 약정한도 80, funded 40, live draw 15 → credit headroom 19. 자금 제공자의 공제 전 적격 현금 잔액 60, 기존 지급예약 15, 기타 제한 5 → funding headroom 40. 신규 인출 최대는 19다.

기존 예약 15 중 10이 은행에서 성공하면 `funded 40→50`, `live 15→5`이므로 Exposure는 계속 55다. 같은 순간 현금 `60→50`, 지급예약 `15→5`이므로 funding headroom도 계속 40이다. 예약과 funded를 동시에 차감하는 이중 점유를 만들지 않는다. `UNKNOWN`을 시간이나 운영 종결만으로 노출에서 제거하지 않는다. 승인된 custody·위험 인계에 따라 live 관리 상태를 회수할 수 있지만, 미해결 지급위험은 해당 계약의 contingent/counted exposure와 준비금으로 보존한다. 이를 외부 지급 실패 확정으로 표시하지 않는다. 같은 로컬 원장 안의 reservation 상태와 자금 증거 적용은 원자적으로 변경한다.

채권 20이 현금으로 수취되면 같은 원천 lot에 대해 `미수 -20 / 현금 +20`을 함께 적용한다. 한 source cut에서 미수 20과 그 수취 현금 20을 동시에 담보로 세지 않는다. 현금을 상환에 사용하면 `담보 현금 -상환액 / 대출잔액 -원금상환액`도 연결한다. 은행 배치 한 건은 여러 채권에 배분 가능하되 배분 합계가 실제 입금액을 넘지 않는다.

공연 전 여신은 위 BB에 미래매출을 슬쩍 더하지 않는다. 별도 승인된 프로젝트 exposure 한도·금융기관 자금·신용보완을 사용하고, 실제 적격채권이 발생하면 명시적 `collateral_substitution`을 통해 전환한다. 재평가로 BB가 잔액 아래로 내려가면 신규 인출 중단과 cure/default 계약이 발동하며 잔액을 소급 삭제하지 않는다.

## 5. 분개: 서로 다른 법인의 원장을 구분한다

아래는 소프트웨어 보조원장 검증용 예시다. 회계기준상 총액/순액, 수익 인식 시점, 세무는 실제 principal-agent 계약에 맞춰 따로 확정한다. 금액 단위 백만원, 단일 KRW, 수수료·세금 0으로 단순화했다. KIX 회사가 모든 자산/부채를 보유한다는 뜻이 아니다.

### 정상 경로

1. 금융기관이 주최자에게 자기 자금 60을 선지급한다.
   - 대주 장부: 차변 대출채권 60 / 대변 은행현금 60.
   - 차주 장부: 차변 은행현금 60 / 대변 대출채무 60.
   - 이 돈은 고객 티켓대금 100과 별개다.
2. 관객 결제 100 확인: 정산 보조원장 차변 PG미수 100 / 대변 조건부 주최자 지급예정 100.
3. PG 입금 100 확인: 차변 통제계좌 현금 100 / 대변 PG미수 100.
4. 공연 이행·정산조건 충족 후 위험정책상 10을 유보한다: 차변 조건부 지급예정 100 / 대변 배분가능 지급채무 90, 제한된 주최자 지급채무 10. 유보 10은 아직 발생하지 않은 환불채무 자체와 구분한다.
5. 배분가능 90을 계약에 따라 대주 원금 60 + 확정 이자 3 + 공연장 10 + 주최자 17로 배분한다. 원금·이자채무 발생과 lender payable의 source link를 보존한다. 각 지급에 차변 해당 지급채무 / 대변 현금, 총 90.
6. 대주 장부는 현금 63 수령과 원금 60·이미 인식한 이자미수 3 상환을 기록한다. 차주 장부에는 원금채무 60·이자채무 3 소멸을 대응 기록한다.
7. 잔여 위험조건 해소 후 유보 10을 주최자에게 지급한다. 티켓대금 100의 최종 합은 **대주 63 + 공연장 10 + 주최자 27 = 100**이다. 최초 대주 선지급 60을 티켓매출에 다시 더하지 않는다.

### 지급 전 공연 취소

위 3번 이후, 4~7번 이전에 전체 취소하면 차변 조건부 주최자 지급예정 100 / 대변 고객 환불채무 100. 통제계좌에서 차변 환불채무 100 / 대변 현금 100으로 반환한다. 대주의 선지급 대출채권 60은 그대로 남고 주최자 상환능력·보증·담보로 회수한다. 관객에게 돌려줄 100에서 먼저 대주 60을 떼어 회수하지 않는다. 계약상 통제와 실제 계좌가 이 결과를 강제해야 한다.

### 배분 후 뒤늦은 반환 및 자금 부족

유보 현금/지급채무 10만 남은 시점에 확인된 환불채무 20이 발생했다고 가정한다. 차변 유보 지급채무 10 + 이미 지급받은 계약당사자에 대한 회수채권 10 / 대변 환불채무 20. 회수채권 10은 **현금이 아니다**. 회수 입금 또는 보증/약정된 유동성 10이 확인되어야 나머지 반환을 실행할 수 있다. 부족하면 `RefundFundingShortfall(10)`을 표시하고 의무를 보존한다. 회수 요구·예상 보험금·새 대출 승인만으로 환불 완료를 표시하지 않는다.

### 차주 부도

대출잔액 60 중 확인된 회수 15이면 대주 장부 차변 현금 15 / 대변 대출채권 15. 잔여 45에 전액 손상이 필요하다는 승인된 판단이라면 차변 손상손실 45 / 대변 대손충당금 45. 후속 상각은 회계처리와 별도의 법적 채무·회수 사건을 연결한다. 상각, 토큰 retirement, 회수 불능 판단 어느 것도 임의 채무면제 명령으로 취급하지 않는다. 별도 합의에 따른 면제는 권한·대가·증거를 가진 전이다.

## 6. 배분·지급통제 계약

초기 권고 워터폴은 (a) 확인된 환불/차지백 및 필요한 고객보호재원 확보, (b) 세금·PG 등 계약상 필수 지급과 법적 제한 반영, (c) 적격 금융 원리금, (d) 공연장·주최자 등 잔여 수취인이다. 정확한 순위는 상품·법률 검토·PG·은행 계약에서 확정한다. **이는 제안한 계약상 지급통제 순서이지 관객의 법정 최우선변제권 또는 대주의 무조건 선순위라는 주장이 아니다.** 실제 도산·압류·상계·계좌명의·신탁 여부에 따라 권리가 달라진다.

고객환불 보호준비금은 자산 분리·권한 분리·은행 계좌 통제·일일 대사로 강제한다. 단순 DB `restricted=true`는 도산격리나 법적 신탁을 만들지 않는다. 10% 유보는 전액 공연취소를 감당하지 못하므로 계약상 부족분 부담자와 확보된 보증/보험/현금이 별도로 필요하다. 그 능력이 없으면 선지급 한도를 줄이거나 실행을 보류한다.

정책/상태/version 변경과 지급예약 경쟁은 같은 경제 권위에서 직렬화한다. 취소·담보해제·신규 인출이 경합해도 고객 의무를 소거하지 않는다. 공연 간 상계·재원 이동은 명시적 cross-collateral 계약과 승인 범위가 없으면 금지한다. 워터폴 버전을 바꿔 과거 이미 채택된 권리를 재배분하지 않는다.

## 7. 업무 워크플로우와 권한

1. **온보딩:** 차주/주최자/공연장/대주/수취계좌/KYB와 실소유자, 실제 계약당사자, 대표권·위임·대리권을 확인한다. 고객 관객 KYC와 기업 KYB는 별도 필요 범위로 설계한다.
2. **심사:** venue·artist 계약, 예산, 자기자본, 행사·환불·보험 위험, PG 정산조건, 판매데이터 원천·누락·부정거래, 기존 담보·집중도·관련자거래를 평가한다. ML 매출예측은 입력 자료이며 인출 권한이 아니다.
3. **약정·담보:** 금융기관 승인, 계약, 채권 특정·양도/질권 절차, 지정계좌 통제, 담보 중복확인, origin ID를 결합한다. 법무 증거 attestation 이후 허용한 범위만 활성화한다.
4. **인출:** 최신 평가컷·facility 현재성·한도·현금·수취계좌를 재확인한다. 로컬 draw 명령·최초 결과·현금예약·원 intent를 먼저 커밋한다. 이어 정확한 Move 담보/노출 예약의 확정을 확인하고, 동일 operation의 BankInstructionAuthorization 소비가 확정된 뒤 은행에 송신한다. 이 단계들은 하나의 분산 ACID가 아니며 중단 시 원 operation으로 조회·복구한다. 운영자 한 명이 본인 제안 심사·승인·지급을 모두 수행하지 못하도록 신규 금융 업무 권한을 나눈다. 기존 LC-TERM 인적 역할 계약을 바꾸지 않는다.
5. **실행·대사:** 금융기관/은행 adapter가 durable intent로 송신한다. 시간초과는 UNKNOWN이다. 변조계좌·다른 currency·동일 key 다른 payload를 거절한다. 성공·실패·부분지급 사실을 내구 inbox에 보존한다.
6. **상환·분배:** 은행 입금→원천채권 소멸→waterfall 배분→원리금 반영→온체인 position 갱신. 각 경계의 사실·결과를 재시도 가능하게 하고 webhook 중복을 economic operation 중복과 구분한다.
7. **경보·부도:** 한도부족/계약위반/취소/회수불능에서 신규 인출을 동결한다. cure·담보보강·약정종료·회수집행 권한을 구별한다. 채권 회수 권한이 티켓 입장권 박탈 권한을 주지 않는다.
8. **종결:** 실제 원금·이자·분쟁·refund exposure와 해제 조건을 확인하여 구체적 부담을 해제한다. LC-TERM 운영종결만으로 담보가 무부담이 되거나 원채무가 소멸하지 않는다. 금융/리셀 범위의 기존 승인자 권한은 현행 계약이 요구하는 별도 재검토 대상이다.

자동화는 사전 승인된 rule/limit/증거 검증으로 제한한다. AI는 평가 요약·자료 수집·이상 탐지·대사 제안까지 할 수 있으나 독자적으로 한도/금리/담보순위/수취계좌/송금권한을 바꾸지 않는다. 금융 사고의 emergency freeze는 관측 수신·고객환불 접수·증거 보존까지 막는 전체 kill switch가 되어서는 안 된다.

## 8. 독립 인수 시험

- 동일 receivable의 이중 등록, split/merge 후 합계, 같은 slice의 동시 담보 설정·외부 부담 발견.
- 원화/다른 자산 혼동, BCS schema mismatch, 잘못된 beneficiary/currency, 과거 valuation replay.
- 서로 다른 draw가 동시에 한도 끝을 예약해도 총 funded+live가 한도를 넘지 않음.
- 성공 송금 뒤 응답유실, 중복 observation, 송금 도중 facility freeze, 옛 worker의 지연 성공.
- PG미수→은행현금 변환 중 crash에도 담보 이중 계상 없음.
- refund/chargeback/분쟁 제외 사유가 중첩돼도 동일 금액 중복 공제·중복 회수 없음.
- 전체 공연취소 시 신규 인출 금지, 관객 refund obligation 보존, 대출손실과 고객자금을 분리.
- 부분상환/이자/수수료/원금 배분 합계, 연체·손상·회수 이후 재수신 한 번만 적용.
- 부분 지급 후 환불자금 부족을 감추지 않으며 미수 회수채권을 현금처럼 쓰지 않음.
- 외부 해제 증거 없는 담보 release, 권한 회수 뒤 토큰 이전, 임의 debt forgiveness 거절.
- public chain 포인터만 남고 원문 증거가 유실되면 적격평가/새 인출 보류, 관측·회수 경로는 유지.
- 고객·영업·금융·회계 tenant 권한 교차 접근, bank instruction maker/checker 우회, AI 권한상승 거절.

## 9. 한국 법률 분류와 현재 공식 자료

법률분류는 상품 구현 입력이다. KIX가 무엇을 발행·보유·모집·중개·대여·추심하는지 실제 계약과 자금 흐름을 확정한 뒤 금융기관·법무 검토를 받아야 한다. 다음은 현재 확인한 경계이며 개별 상품 적법성 의견이 아니다.

1. **채권양도:** 민법 제450조는 양도인의 통지/채무자 승낙 및 제삼자 대항요건을 구분한다. Sui 기록만으로 이 요건을 충족했다고 가정하지 않는다. 질권·담보등기·신탁 등 다른 구조는 그 구조의 절차를 따로 모델링한다. [국가법령정보센터, 민법 제450조 — 시행 2026-03-17](https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1032403261)
2. **여신·중개 행위:** 금융기관과 연결한다고 자동으로 KIX의 모든 행위가 등록 대상에서 제외되는 것은 아니다. 대여·중개·채권매입·추심의 실질과 적용 법령을 역할별로 판정한다. [국가법령정보센터, 대부업법 현행 본문 — 시행 2026-01-02](https://www.law.go.kr/LSW/lsInfoP.do?ancYnChk=0&lsId=009348)
3. **토큰 증권:** 금융위는 증권 해당 여부가 권리의 실질에 따른다고 설명한다. 입장권 token, 담보관계의 제한된 기록, 투자자에게 수익을 귀속하는 발행을 동일 법적 범주로 처리하지 않는다. [금융위원회, 2026-01-15](https://www.fsc.go.kr/no010101/86064)
4. **최신 시행·인프라 구분:** 2026-09-04 금융위 정책방향은 개정 전자증권법의 **2027-02-04 시행 예정**, 예탁원 연계·분산원장 심사, 단계적 토큰화 구축을 설명한다. KIX의 Sui 객체가 그 법정 계좌부로 이미 인정됐다는 주장을 하지 않는다. 장래매출채권의 조건부 활용 방향 역시 KIX 상품의 즉시 허용이나 담보가치 보장이 아니다. [금융위원회, 토큰증권 정책방향 2026-09-04](https://www.fsc.go.kr/no010101/87650?curPage=&srchBeginDt=&srchCtgry=&srchEndDt=&srchKey=&srchText=)

따라서 설계는 **기명 기관금융 + 실제 Move 금융 상태 + 법률상 권리 문서/계좌/승인 연결**을 먼저 완성하고, 공개 유동성·증권 유통은 별도 승인된 상품 단계로 둔다. 법적 조건이 남았다는 이유로 Rust 계산·모의 자금·토큰 전이·장애 시험의 개발을 중단할 필요는 없다. 실자금 활성화와 투자자 모집만 별도 게이트로 분리한다.
