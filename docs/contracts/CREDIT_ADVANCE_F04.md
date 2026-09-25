# 여신·신용 선지급 F04 — 목 계약

Task 005 Wave 5. 문서일: 2026-09-26.
구현 기준 `origin/main`: `4ec0f93255b9be1715784f1d2a5edde411cc96c6`.
이 문서는 오프라인 목(mock)이 지킬 술어와, 아직 정하지 않은 간극을 적는다.
`docs/status/ORIGINAL_32_STATUS.md`의 F04·E06 라벨은 **설계중** 그대로다.
이 계약은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.

현행 승인 범위의 정본은 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md)다.
[PROTOCOL_MASTERPLAN_V2.md](../PROTOCOL_MASTERPLAN_V2.md) §7은 역사 계획이다.
아래 문장은 그 계획을 여신 상품으로 다시 정한 것이 아니다.
목이 베끼는 술어와 베끼지 않는 상품 조건을 고정하기 위한 인용이다.

Astra 결정 6 (2026-09-25, 개발총괄): 여신 / 신용 선지급 = **F04**, **mock/sim only**.
실여신, 규제 상품, 실자금 경로는 별도 Astra 결정과 명시적 OK 전까지 금지한다.

## 0. 이 웨이브가 하는 일

모델 1의 문장 그대로, 체인 기록이 은행 자금·계약상 채무·공연 이행을 보증하지 않는다.
[STATE_LIFECYCLE.md](STATE_LIFECYCLE.md)가 이미 적은 대로, 기록은 위험 공개에 필요하지만
독립 담보의 실재·우선순위·법적 효력을 대신하지 않는다.

| 항목 | 목에서 고정하는 것 | 고정하지 않는 것 |
|---|---|---|
| F04 담보 / 선지급 / 금융상품 | 한 프로세스 안에서, Wave 3 청구 조회의 미지급 액면 합을 넘지 않는 메모 예약. 같은 바인딩은 한 번. 부담 미정 환불이 열려 있으면 예약하지 않음 | 인허가, 이자·상환, 우선순위, 담보 완성, 처분, 실자금 |
| E06 규정 / 컴플라이언스 | 조회 플래그를 거짓으로 고정해 규제 상품·면허를 적지 않음 | 인허가 판단, 법적 책임, 개인정보 보존 |

실행 파일은 `reference/credit_advance_f04/mock_credit.py`다.
실행 방법과 비청구는 [validation/2026-09-26-wave5-credit-f04-mock/README.md](../../validation/2026-09-26-wave5-credit-f04-mock/README.md)에 있다.
네트워크, 파일, PG, 은행, 커널, Move를 호출하지 않는다.
Wave 3 모듈을 import하지 않고, 그 장부에 쓰지 않는다.
호출자가 넘긴 조회 dict만 읽는다. 그 dict는 프로세스 메모리 안의 스냅샷이다.
이 결과는 내구 원장이 아니다.
모든 조회에 `provenance = MOCK_CREDIT_F04_ONLY`를 붙인다.

역사 계획 §7과 불변조건 9가 이미 말한 것 가운데, 이 목이 베끼는 것은 다음뿐이다.

- 금융 메모는 관람·검표 권한이 아니다.
- 이 프로세스가 본 등록 액면의 합을 넘겨 메모를 쌓지 않는다.
- 외부에서 이미 양도·담보된 채권이 이 기록으로 사라졌다고 하지 않는다.

같은 절의 약정·인출·이자/비용·상환·연체·손실·우선순위·계약상 집행은 베끼지 않는다.
실제 심사와 법정화폐 공급은 역사 계획도 외부 근거가 필요하다고 적었다. 이 목은 그 근거를 만들지 않는다.

## 1. 공통 한계

금액 상한은 Wave 3 정산 목과 같다. 새 여신 한도가 아니다.

- 입력 조회의 `currency`는 `KRW`만 받는다. 다른 통화는 `CURRENCY_UNSUPPORTED`.
- 예약 금액은 `bool`이 아닌 `int`다. `1 .. 10**12`. 실패 코드는 `INVALID_AMOUNT`.
- 식별자와 역할 라벨은 길이 1..100인 `str`이고, 앞뒤 공백을 허용하지 않는다. `bool`과 `str` 하위 클래스는 거절한다. 실패 코드는 `INVALID_ID`.
- `beneficiary_role`은 저장만 한다. 대주, 면허 소지자, 계좌, 사람, 사업자로 해석하지 않는다.
- 같은 `advance_id`의 재전송은 바인딩이 같으면 효과를 다시 내지 않는다(`duplicate: true`, `applied: null`). 바인딩이 다르면 `ADVANCE_BINDING_CONFLICT`.
- 다음 플래그는 항상 거짓이다. 성공한 호출이 참을 만들지 못한다.
  `funds_executed`, `license_granted`, `regulated_product`, `collateral_perfected`,
  `priority_bound`, `disposal_controlled`, `revenue_assigned`, `admission_granted`,
  `legal_debtor_bound`, `bank_debit_observed`, `external_pledge_complete`,
  `durable`, `repayment_observed`, `interest_defined`.

## 2. 입력 — Wave 3 청구 조회 스냅샷

`note_advance`의 `face`는 [SETTLEMENT_DISTRIBUTION_F01_F03.md](SETTLEMENT_DISTRIBUTION_F01_F03.md) 목의 `view`가 만드는 dict를 호출자가 넘긴 것이다.
이 모듈은 `MockSettlement`를 호출하지 않는다. 확인 현금은 은행 잔고가 아니고, 여기서 다시 정산하지 않는다.

조회는 다음을 만족해야 한다.

- `provenance`는 `MOCK_SETTLEMENT_ONLY`다. Wave 3이 항상 거짓으로 두는 플래그(`legal_debtor_bound`, `admission_granted`, `right_cancelled`, `bank_debit_observed`, `external_return_closed`, `funds_executed`)는 값 `False`다. 키가 없으면 `SETTLEMENT_FACE_FIELDS`다. 값이 `False`가 아니면 `SETTLEMENT_FACE_NOT_MOCK`이다.
- `gross`와 의무 줄의 `face`·`distributed`·`cancelled_unpaid`·`outstanding`은 정수다. `outstanding`은 `face - distributed - cancelled_unpaid`와 같아야 하고, 그 값은 0 이상이다. 의무 `face`의 합은 `gross`다. 아니면 `SETTLEMENT_FACE_MISMATCH`.
- `fixture_reclassified`가 참이면 `refund_face == gross`, `refund_bearer_policy`는 `FIXTURE_FULL_GROSS_RECLASS`, 미지급 액면 합은 0이다.
- 재분류가 아니고 `refund_face > 0`이면 `refund_bearer_policy`는 `UNDEFINED`이고, 각 줄의 `cancelled_unpaid`는 0이다.
- 환불 액면이 0이면 `refund_bearer_policy`는 `NONE`이고, 각 줄의 `cancelled_unpaid`는 0이다.
- 수취인 라벨은 한 조회 안에서 겹치지 않는다.

이 검사는 스냅샷이 `MockSettlement.view`의 출력이라는 서명이 아니다.
구조·산술·항상 거짓인 플래그만 본다. 통과는 정산 원장의 인증이 아니다.

천장 `open_face`는 그 스냅샷의 `outstanding` 합이다.
`confirmed_cash`와 `recovery_due`는 조회에 복사만 한다(`confirmed_cash_on_face`, `recovery_due_on_face`).
천장에 더하지 않는다. 확인 현금은 대여 재원이 아니고, 회수채권은 선지급 한도가 아니다.

한 `claim_id`에 처음 수락된 노트가 조회 전체를 고정한다. 고정 문자열은 호출자가 넣은 키를 포함해, 키를 정렬하고 공백을 넣지 않은 JSON이다.
이후 같은 청구의 다른 조회는 `FACE_SNAPSHOT_FROZEN`이다.
정산 목이 나중에 배정하거나 환불해도 이 목은 따라가지 않는다. 차입 기초를 재평가하지 않기 위한 정지고, 담보 가액의 시세가 아니다.

## 3. 게이트 호출

HTTP 서버는 없다. 아래는 목 함수다. `view` / `view_claim`은 상태를 바꾸지 않는다.

| 함수 | 필요한 것 |
|---|---|
| `note_advance` | `advance_id`, `face`, `amount`, `beneficiary_role`. `product`의 기본값은 `None` |
| `release_note` | `advance_id` |
| `attempt_execution` | `advance_id`, `kind`. 항상 예외. 상태를 바꾸지 않음 |
| `view` | `advance_id` |
| `view_claim` | `claim_id`. 수락된 노트가 한 번도 없는 청구는 `UNKNOWN_CLAIM` |

`note_advance`의 검사 순서는 다음과 같다.

1. `product is not None`이면 `CREDIT_PRODUCT_UNDEFINED`. 빈 dict도 포함이다. 이자·수수료·APR·기간·상환표·면허·담보 문서를 받는 자리가 아니다.
2. `advance_id`, `beneficiary_role`, `amount`의 형식.
3. `face`의 구조·산술.
4. 같은 `advance_id`가 있으면, 바인딩이 같을 때 중복이고 다를 때 `ADVANCE_BINDING_CONFLICT`. 중복은 아래 검사를 다시 하지 않으며, 해제된 노트를 다시 열지 않는다.
5. `refund_face > 0`이고 전액 재분류가 아니면 `REFUND_OBLIGATION_OPEN`. Wave 3이 부담자를 `UNDEFINED`로 둔 동안, 환불과 메모 중 어느 쪽이 앞인지 정하지 않는다.
6. 그 청구의 고정 조회와 다르면 `FACE_SNAPSHOT_FROZEN`.
7. `amount`가 `open_face - reserved_open`보다 크면 `ADVANCE_EXCEEDS_OPEN_FACE`.
8. 수락하면 상태를 `NOTED`로 둔다. `reserved_open`은 그 청구에서 `NOTED`인 금액의 합이다.

바인딩은 `advance_id`, `amount`, `beneficiary_role`, 조회 정규 JSON이다.
역할 라벨은 우선순위가 아니다. 먼저 적은 노트가 나중 노트보다 선순위가 되지 않는다.
합만 천장 안에 있으면 둘 다 남고, `priority_bound`는 거짓이다.

`release_note`는 `NOTED`를 `RELEASED`로 바꾸고 그 금액을 `reserved_open`에서 뺀다.
이미 해제된 호출은 중복이다. 없는 id는 `UNKNOWN_ADVANCE`.
해제는 상환이 아니다. `repayment_observed`와 `funds_executed`는 거짓으로 남는다.
해제한 id로 같은 바인딩을 다시 넣으면 중복일 뿐 다시 `NOTED`가 되지 않는다.
다른 새 id는 돌아간 천장 안에서 다시 메모할 수 있다. 그것은 재인출 약정이 아니다.

`attempt_execution`은 장부에 쓰지 않고 항상 예외다. 순서는 식별자, `kind`, 노트 존재, 그다음 거절 코드다. `kind`가 목록 밖이면 노트가 없어도 `EXECUTION_KIND`다.

| `kind` | 코드 |
|---|---|
| `DISBURSE`, `REPAY`, `DEBIT` | `REAL_FUNDS_FORBIDDEN` |
| `ACCRUE`, `LICENSE`, `FORECLOSE`, `PRIORITY`, `PERFECT` | `CREDIT_PRODUCT_UNDEFINED` |

그 밖의 `kind`는 `EXECUTION_KIND`다. 동의어를 성공 경로로 만들지 않는다.
없는 `advance_id`는 `UNKNOWN_ADVANCE`다. 해제된 노트도 집행하지 않는다.

상태 문자열 `NOTED`와 `RELEASED`는 이 프로세스의 메모다.
대출 실행, 연체, 상각, 회수 완료가 아니다.

## 4. 오류 코드

| 코드 | 조건 |
|---|---|
| `INVALID_ID` | 식별자·역할 형식 |
| `INVALID_AMOUNT` | 예약 금액의 타입·범위. `bool`과 0 거절 |
| `CURRENCY_UNSUPPORTED` | 조회 통화가 `KRW`가 아님 |
| `SETTLEMENT_FACE_TYPE` | `face`가 dict가 아니거나 정규 JSON이 아님 |
| `SETTLEMENT_FACE_FIELDS` | 필요한 키가 없음 |
| `SETTLEMENT_FACE_NOT_MOCK` | 출처가 Wave 3 목이 아니거나, 항상 거짓이어야 하는 플래그가 `False`가 아님 |
| `SETTLEMENT_FACE_MISMATCH` | 액면 산술, 환불 재분류, 수취인 중복이 조회와 맞지 않음 |
| `CREDIT_PRODUCT_UNDEFINED` | `product`가 있거나, 상품·담보·면허로 분류한 집행 kind |
| `REAL_FUNDS_FORBIDDEN` | 지급·상환·출금을 요청 |
| `REFUND_OBLIGATION_OPEN` | 부담 미정 환불이 열린 조회 |
| `FACE_SNAPSHOT_FROZEN` | 같은 청구, 다른 조회 |
| `ADVANCE_EXCEEDS_OPEN_FACE` | 미예약 액면을 넘는 금액 |
| `ADVANCE_BINDING_CONFLICT` | 같은 `advance_id`, 다른 바인딩 |
| `UNKNOWN_ADVANCE` / `UNKNOWN_CLAIM` | 없는 노트 / 아직 노트하지 않은 청구 |
| `EXECUTION_KIND` | 닫힌 kind 목록 밖의 값 |

`MOCK_INVARIANT`는 목 내부 불변식이 깨진 구현 오류다. 호출자가 맞출 입력 거절이 아니다.

## 5. 의도적으로 비운 항목

다음에 값을 채워 넣지 않는다. 제품 정책이 필요하면 `DECISION_REQUIRED · Astra`다.

- 대주·차주·담보권자·환불채무자의 법적 확정
- 여신 인허가, 등록, 규제 상품 분류, 약관, 면허 번호
- 이자, 수수료, APR, 기간, 상환 일정, 연체, 손실 귀속, 상각
- 노트 사이의 우선순위, 후순위, 배당 순위
- 담보 대항요건, 등기, 점유, 외부 질권의 완전성
- 처분, 실행, 유질, 수익 귀속
- 은행 출금, PG, 고객 입금, 상환 관찰, 준비금
- `confirmed_cash` 또는 `recovery_due`를 재원으로 쓰는 일
- 스냅샷 이후 정산 변화에 맞춘 한도 재산정
- 부담 미정 환불과 메모의 상계
- 관람권, 검표, 권리 폐기
- 내구성, 은행 정확히 한 번, 체인 최종성, 규제 준수
- 제품 TPS, p99, 실패율
- 화면, 앱, 실자금

## 6. 비청구

이 문서와 목 시험의 통과는 F04가 구현되었다는 뜻이 아니다.
라벨은 설계중이다.
메모 예약은 선지급 실행이 아니고, 해제는 상환이 아니고, 조회 플래그의 거짓은 면허 없음의 규제 판단이 아니다.
`reference/v0.3-rc1`과 Wave 3 정산 목을 수정하지 않으며 대체하지 않는다.
