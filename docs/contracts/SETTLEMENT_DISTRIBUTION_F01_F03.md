# 정산 분배 F01–F03 — 목 계약

Task 005 Wave 3. 문서일: 2026-09-26.
구현 기준 `origin/main`: `a2814923bc671889da49984a2c95964340a1506d`.
이 문서는 오프라인 목(mock)이 지킬 술어와, 아직 정하지 않은 간극을 적는다.
`docs/status/ORIGINAL_32_STATUS.md`의 F01·F02·F03·P04 라벨은 **설계중** 그대로다.
이 계약은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.

현행 승인 범위의 정본은 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md)다.
[PROTOCOL_MASTERPLAN_V2.md](../PROTOCOL_MASTERPLAN_V2.md) §7은 역사 계획이다.
아래 “역사 참조가 이미 말한 계산”은 그 참조를 다시 구현한 것이 아니라,
목이 베끼는 범위와 베끼지 않는 범위를 고정하기 위한 인용이다.

## 0. 이 웨이브가 하는 일

| 항목 | 목에서 고정하는 것 | 고정하지 않는 것 |
|---|---|---|
| F01 정산채권 / 의무 | 정수 KRW 총액에 묶인 청구와 수취인별 의무 액면 | 법적 채무자·채권 발생/소멸·수익 귀속 |
| F02 분할정산 | 일차 판매 수수료 bps 분할, 호출자가 적은 순서대로 확인 현금을 배정, 부족분 잔여 의무 | 수익 waterfall 상품 정책, 실제 자금 이동 |
| F03 환불 / 취소 | 환불 의무 한도, 전액 1회 재분류, 목 취소 수락과 가맹점 조정 잔액 | 권리 취소, 담보, 외부 반환 종결, 은행 출금 |

실행 파일은 `reference/settlement_f01_f03/mock_settlement.py`다.
실행 방법과 비청구는 [validation/2026-09-26-wave3-settlement-f01-f03/README.md](../../validation/2026-09-26-wave3-settlement-f01-f03/README.md)에 있다.
네트워크, 파일, PG, 은행, 커널, Move를 호출하지 않는다.
프로세스 메모리 안의 결과이며 내구 원장이 아니다.
모든 조회에 `provenance = MOCK_SETTLEMENT_ONLY`를 붙인다.

모델 1의 문장 그대로, 체인 기록이 은행 자금·계약상 채무·공연 이행을 보증하지 않는다.
커널의 `ReturnRequired`는 환불 요청 승인도 환불 완료도 아니다
([STATE_LIFECYCLE.md](STATE_LIFECYCLE.md) §5.7). 이 목의 환불 의무는 그 표식이 아니고,
그 표식을 해제하거나 대체하지 않는다.

## 1. 공통 돈·식별 한계

역사 참조 `reference/v0.3-rc1/contracts.py`의 정수 상한과 같다. 새 상품 한도가 아니다.

- 통화는 `KRW`만 받는다. 다른 통화는 `CURRENCY_UNSUPPORTED`.
- 금액은 `bool`이 아닌 `int`다. 양수 금액은 `1 .. 10**12`, 비음수 금액은 `0 .. 10**12`.
- 식별자와 역할 라벨은 길이 1..100인 문자열이고, 앞뒤 공백을 허용하지 않는다. 실패 코드는 `INVALID_ID`.
- 역할 문자열(`debtor_role`, 수취인, 환불 상대)은 저장만 한다. 사람·계좌·사업자·법률 당사자로 해석하지 않는다.
- 같은 키의 재전송은 바인딩이 같으면 경제 효과를 한 번만 낸다(`duplicate: true`). 바인딩이 다르면 충돌이다.
- 조회 플래그 `legal_debtor_bound`, `admission_granted`, `right_cancelled`, `bank_debit_observed`, `external_return_closed`, `funds_executed`는 항상 거짓이다. 성공한 호출이 이 값을 참으로 만들지 못한다.

## 2. F01 — 청구와 의무 액면

`recognize_claim`은 한 거래의 포착 총액으로 청구를 연다.

입력 정책은 다음 키만 가진다. `kind`는 `PRIMARY_FEE_BPS`만 허용한다.

| 필드 | 의미 |
|---|---|
| `fee_bps` | 0 이상 10000 이하 정수 |
| `residual_payee` | 잔여 액면의 역할 라벨 |
| `fee_payee` | 수수료 액면의 역할 라벨. 잔여 라벨과 달라야 한다 |

분할은 역사 `core._commit_trade`의 일차 판매 분기와 같은 정수 나눗셈이다.

```text
fee = gross * fee_bps // 10000
residual = gross - fee
```

액면이 0인 줄은 의무로 만들지 않는다. 두 액면의 합은 `gross`다.
이 시점에 확인 현금은 0이다. 포착을 쓸 수 있는 현금으로 바꾸지 않는다.
리셀 분할(`resaleFeeBps`, `resaleOrganizerBps`, 판매자 잔여)은 이 정책에 없다.
그 계산은 역사 `core.py`에만 있고, 이 목이 상품 규칙으로 다시 정하지 않는다.

같은 `claim_id`에 같은 바인딩을 다시 넣으면 중복이다. 다른 바인딩은 `CLAIM_BINDING_CONFLICT`.

청구는 관람 권한이 아니다. 의무 액면을 가진 역할에게 입장·검표 자격을 주지 않는다.

## 3. 정산 명세서 — 추측하지 않는 구성

`observe_settlement_statement`는 한 `movement_id`에 구성 금액을 묶는다.
역사 `finance._settle_capture`의 등식만 가져온다.

```text
gross = amount + fee + tax + held + adjustment
```

- 등식이 깨지면 `SETTLEMENT_COMPONENT_MISMATCH`. 입금액이 총액보다 작다고 차액을 수수료로 채우지 않는다.
- `adjustment > 0`이면 이유 문자열이 필요하다(`ADJUSTMENT_REASON_REQUIRED`). 조정이 0인데 이유를 주면 `ADJUSTMENT_REASON_UNEXPECTED`.
- 명세서 `gross`의 누계가 청구 총액을 넘으면 `SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE`.
- `amount`만 확인 현금에 더한다. `fee`·`tax`·`held`·`adjustment`는 미수에서 빠지지만 배정 가능한 현금이 아니고, 의무 액면을 줄이지 않는다.
- 같은 명세서가 플랫폼 배분 의무와 같은 돈이라는 뜻은 아니다. PG 수수료 3,000과 정책 수수료 액면 5,000은 별도다. 현금이 모자라면 액면을 몰래 줄이지 않고 잔여 의무로 남긴다.

이 입력은 목 사실이다. 토스 정산 API를 호출했거나 입금을 확인했다는 뜻이 아니다.
[PG_TOSS_CARD_PROFILE.md](PG_TOSS_CARD_PROFILE.md)의 잠정 카드 선택도 정산 실행 승인이 아니다.

## 4. F02 — 분할 배정과 호출자 순서

수익 참여의 회수 순서·원가·상한·반올림 부담은 상품 정책으로 미정이다.
역사 참조도 현금이 액면 합보다 작을 때 어느 수취인이 부족분을 질지 정하지 않는다.
따라서 목은 기본 순서를 두지 않는다.

`apply_distribution(order)`는 다음만 한다.

1. `order`는 현재 의무 수취인 전체의 순열이다. 빠지거나 겹치거나 모르는 라벨이면 `DISTRIBUTION_ORDER_MISMATCH` 또는 `DISTRIBUTION_ORDER_DUPLICATE`.
2. 아직 배정하지 않은 확인 현금을 그 순서대로, 각 의무의 미지급 잔액까지만 배정한다.
3. 액면·취소액·회수채권은 이 호출로 바꾸지 않는다. 바뀌는 것은 `distributed`뿐이다.
4. 수락된 첫 호출의 `order`가 그 청구의 순서로 고정된다. 이후 다른 순서는 `DISTRIBUTION_ORDER_FROZEN`. 같은 순서는 새로 들어온 확인 현금만 이어서 배정한다. 거절된 호출은 순서를 고정하지 않는다.
5. 현금이 0이어도 수락된 호출은 순서를 고정하고 배정액은 0이다.

부족분은 `face - distributed - cancelled_unpaid`로 남는다.
이 순서는 호출자가 시험에 적은 픽스처 우선순위다. 법률상 waterfall, 원가 회수, 수익 참여 상한이 아니다.
순서에 따라 누가 잔여 의무를 가지는지만 결정론적으로 달라진다. 목은 그 차이를 숨기지 않는다.

## 5. F03 — 환불 의무와 목 취소 수락

`bind_refund`는 구매자 역할에 대한 환불 의무를 더한다.

- 한 청구의 환불 액면 합은 `gross`를 넘지 못한다(`REFUND_CEILING`).
- 이미 기록된 상대 역할과 다른 상대는 `REFUND_BENEFICIARY_CONFLICT`.
- 부분 환불(전액이 아닌 경우, 또는 여러 번에 나뉜 경우)은 의무만 쌓는다. 수취인 액면을 취소하거나 회수채권으로 바꾸지 않는다. `refund_bearer_policy = UNDEFINED`. 누가 그 환불을 부담하는지는 미정이다.
- 부담이 미정인 동안 `apply_distribution`은 `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED`다. 이미 배정된 금액은 되돌리지 않고, 추가 배정도 하지 않는다. 부담 규칙을 만들어 자동 상계하지 않기 위한 목의 정지다.
- 환불 액면이 아직 0일 때 한 번에 `gross` 전액을 묶으면, 역사 `finance.reverse`의 전액 분류만 따라 간다.
  - 각 의무의 미배정 잔액은 `cancelled_unpaid`로 옮긴다.
  - 이미 배정한 금액은 그 수취인의 `recovery_due`가 된다.
  - `refund_bearer_policy = FIXTURE_FULL_GROSS_RECLASS`.
  - 이것은 픽스처 재분류다. 법적 부담자 확정, 회수 실행, 권리 폐기가 아니다.
- 부분 환불 뒤에 나머지를 더해 합이 `gross`가 되어도 전액 재분류로 바꾸지 않는다.

`observe_mock_cancel_acceptance`는 주입된 목 사실 `MOCK` 취소 수락이다.

- 환불 의무가 없으면 `REFUND_OBLIGATION_REQUIRED`.
- 수락 누계는 환불 액면을 넘지 못한다(`REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION`).
- 수락액만큼 환불 미이행이 줄고 `pg_adjustment_outstanding`이 늘어난다.
- 확인 현금을 줄이지 않는다. 은행 출금으로 기록하지 않는다. `external_return_closed`를 참으로 만들지 않는다.
- 고객 계정 입금 확인(`CUSTOMER_CREDIT_CONFIRMED`)을 이 수락과 같은 사건으로 보지 않는다. 그 확인은 이 목에 없다.
- 다른 거래의 다음 정산금에서 상계하는 실행은 없다. 조정 잔액은 열린 채로 남는다.

현금 환불 송금, 계좌 참조, 지급 효과, 펜스, 재시도는 역사 `finance.py` 경로에 남아 있고 이 목에 다시 만들지 않았다.
원결제 취소와 현금 환불이 한 의무 한도를 공유한다는 역사 문장은, 여기서는 “수락이 환불 액면을 넘지 못한다”까지만 반영한다.

권리 오브젝트, 담보, 외부 반환의 법적 종결을 한 호출로 묶지 않는다. F03의 최약 의존성(환불채무자·권리 취소/담보·외부 반환 종결의 결합)은 그대로 열려 있다.

## 6. 오류 코드

| 코드 | 조건 |
|---|---|
| `INVALID_ID` | 식별자·역할·이유 형식 |
| `INVALID_AMOUNT` / `INVALID_NONNEGATIVE` | 금액 타입·범위. `bool` 거부 |
| `CURRENCY_UNSUPPORTED` | `KRW`가 아님 |
| `POLICY_TYPE` / `POLICY_FIELDS` / `POLICY_KIND` / `POLICY_FEE_BPS` / `POLICY_PAYEE` / `POLICY_PAYEE_COLLISION` | 정책 형식 |
| `UNKNOWN_CLAIM` | 없는 청구 |
| `CLAIM_BINDING_CONFLICT` | 같은 청구 ID, 다른 인식 바인딩 |
| `SETTLEMENT_COMPONENT_MISMATCH` | 구성 합이 `gross`와 다름 |
| `SETTLEMENT_EXCEEDS_OPEN_RECEIVABLE` | 명세서 누계가 청구 총액 초과 |
| `STATEMENT_BINDING_CONFLICT` | 같은 `movement_id`, 다른 명세서 |
| `ADJUSTMENT_REASON_REQUIRED` / `ADJUSTMENT_REASON_UNEXPECTED` | 조정 이유 |
| `DISTRIBUTION_ORDER_TYPE` / `DISTRIBUTION_ORDER_DUPLICATE` / `DISTRIBUTION_ORDER_MISMATCH` / `DISTRIBUTION_ORDER_FROZEN` | 배정 순서 |
| `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED` | 부담 미정 환불이 있는 동안의 배정 |
| `REFUND_CEILING` | 환불 합이 총액 초과 |
| `REFUND_BINDING_CONFLICT` / `REFUND_BENEFICIARY_CONFLICT` | 환불 재전송·상대 불일치 |
| `REFUND_OBLIGATION_REQUIRED` | 의무 없는 취소 수락 |
| `REFUND_ACCEPTANCE_EXCEEDS_OBLIGATION` | 수락이 남은 환불 의무 초과 |
| `ACCEPTANCE_BINDING_CONFLICT` | 같은 수락 ID, 다른 금액 |

`MOCK_INVARIANT`는 목 내부 불변식이 깨진 구현 오류다. 호출자가 맞출 수 있는 입력 거절이 아니다.

## 7. 의도적으로 비운 항목

다음에 값을 채워 넣지 않는다. 제품 정책이 필요하면 `DECISION_REQUIRED · Astra`다.

- 특정 법률 주체를 채무자·채권자·환불채무자로 확정하는 일
- 채권 양도·담보·중복 담보의 대외 완전성
- 수익 waterfall의 원가 정의, 구간, 상한, 반올림 귀속, 지급 시점
- 리셀 대금 분할과 직전 구매자 계속 참가(마스터플랜은 후자를 넣지 않는다고 이미 적었다. 이 목은 그 긍정 규칙을 새로 만들지 않는다)
- 세금·보류·조정 잔액의 해제와 실제 회수
- 부분 환불의 부담자, 할인 재계산, 복수 결제수단 배분
- 권리 폐기·재고 반환·검표 차단
- 은행 출금, PG 라이브 취소, 차지백, 고객 계정 입금 확인
- 거래 간 정산 상계, 준비금, 연체, 상각
- F04 여신·선지급·실자금
- P04의 영속 의무와 제공자 자금 이동을 대사해 종결하는 계약
- 내구성, 정확히 한 번의 은행 반영, 체인 최종성, 규제 준수
- 제품 TPS, p99, 실패율

## 8. 비청구

이 문서와 목 시험의 통과는 F01–F03이 구현되었다는 뜻이 아니다.
라벨은 설계중이다.
목 배정은 정산 입금이 아니고, 목 취소 수락은 환불 완료가 아니다.
`reference/v0.3-rc1`의 금융 모형 전체를 대체하지 않으며 그 파일을 수정하지 않는다.
