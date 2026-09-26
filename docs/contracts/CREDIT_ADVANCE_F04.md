# 여신·신용 선지급 F04 — 목 계약

Task 005 Wave 5. 문서일: 2026-09-26.
구현 기준 `origin/main`: `4ec0f93255b9be1715784f1d2a5edde411cc96c6`.
이 문서는 오프라인 목(mock)이 지킬 술어와, 아직 정하지 않은 간극을 적는다.
`docs/status/ORIGINAL_32_STATUS.md`의 F04·E06 라벨은 **설계중** 그대로다.
이 계약은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.

2026-09-26 credit depth가 §7의 수락 상태 기계를 앞에 둔다.
그 세션에서 확인한 `origin/main`은 `ef942b7713c7468e8851c6b372b64d42b5333ad8`다.
Wave 5 목 술어와 그 기준 SHA는 그대로다. F04·E06 라벨도 그대로다.

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
| 수락 상태 | offer부터 reconcile까지의 목 노출 전이, 멱등키, 종결 뒤 불변, 저널 재생. 정산이 묶여 있으면 `COMMITTED`를 읽은 뒤에만 노출을 늘림 | 실여신, 심사, 이자, 은행 상환, 티켓 소유권 이전 |

예약 술어는 `reference/credit_advance_f04/mock_credit.py`다.
수락 상태 기계는 `reference/credit_advance_f04/credit_fsm.py`다. §7.
실행 방법과 비청구는 [validation/2026-09-26-wave5-credit-f04-mock/README.md](../../validation/2026-09-26-wave5-credit-f04-mock/README.md)에 있다.
네트워크, 파일, PG, 은행, 커널, Move를 호출하지 않는다.
Wave 3 모듈을 import하지 않고, 그 장부에 쓰지 않는다.
호출자가 넘긴 조회 dict만 읽는다. 그 dict는 프로세스 메모리 안의 스냅샷이다.
이 결과는 내구 원장이 아니다.
모든 조회에 `provenance = MOCK_CREDIT_F04_ONLY`를 붙인다.
위의 import 금지와, 호출자가 넘긴 조회 dict만 읽는다는 문장은 Wave 5 목의 술어다.
§7의 기계도 정산 모듈을 import하지 않고 정산 장부에 쓰지 않는다.
정산이 묶인 인출만, 주입된 정산 기계의 `view`를 읽는다.

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
상태 기계의 `matched: true`는 이 프로세스 저널의 재생 일치다. 은행 exactly-once, 여신 실행, 체인 최종성이 아니다.

## 7. 참조 수락 상태 기계

Wave 5 목은 액면 스냅샷에 대한 메모 예약과 해제만 고정했다. 제안, 승인, 인출, 노출, 상환 메모, 종결을 나누지 않았고, 프로세스 저널을 재생하지 않았다.
이 절의 기계가 그 앞에 선다. `mock_credit.py`는 그대로다. 기계가 목 함수를 호출하기 전에 전이를 거절하거나, 수락한 명령을 저널에 한 번 적는다.

F04·E06은 **설계중**이다. 이 절이 그 라벨을 올리지 않는다.

이 기계는 `protocol_contract.json`에 명령을 넣지 않는다.
OpenAPI 카탈로그도 바꾸지 않는다. 새 프로토콜 명령이 필요하면 `DECISION_REQUIRED · Astra`다.
이 깊이는 그 명령을 요구하지 않는다. 수락 기준은 이 참조 모듈 안의 결정이다. 법적 권위, 체인 권위, 대주, 면허, 은행 권한이 아니다.
조회 라벨 `lifecycle_authority = IN_MEMORY_FSM`은 그 한계를 적는다.
`provenance`는 `MOCK_CREDIT_F04_ONLY`다.
`exposure_ledger = MOCK_EXPOSURE`는 이 프로세스의 노출 장부다. 은행 잔액이 아니다.

`draw`와 `repay`는 그 장부의 전이다. §3의 `attempt_execution`이 거절하는 `DISBURSE` / `REPAY` / `DEBIT`이 아니다.
리셀 명령은 이 기계에 없다. 보유자, 버전, 리스팅을 바꾸지 않는다.

### 7.1 단계

```text
(없음)
  | offer
  v
OFFERED --approve--> APPROVED --draw--> DRAWN --close--> CLOSED
   |                    |                  | \
   | reject             | cancel           |  repay (단계 유지, outstanding 감소)
   |                    v                  |  default (outstanding > 0)
   v                 CANCELLED             v
REJECTED                               DEFAULTED
```

`bind_settlement`은 `OFFERED`와 `APPROVED`에서 단계를 유지한다.
`DRAWN`의 `repay`도 단계를 유지한다.
`close`는 `outstanding_exposure`가 0일 때만 `CLOSED`다.
`default`는 남은 노출이 있을 때만 `DEFAULTED`다.
`REJECTED`, `CANCELLED`, `CLOSED`, `DEFAULTED`만 종결이다. 이후 변경 명령은 `TERMINAL_IMMUTABLE`이다.
`reconcile`과 `view`는 종결 뒤에도 된다. `reject_unsupported`와 `attempt_execution`은 종결을 바꾸지 않고 거절만 한다.

`cancel`은 인출 전이다. `DRAWN` 뒤를 `cancel`로 지우지 않는다.
인출 뒤의 감소는 `repay`다. 남은 노출의 종결은 `default`다. 둘 다 은행 회수가 아니다.

`approve`는 호출자가 적은 결정이다. 점수, KYC, 면허, 한도 심사를 계산하지 않는다.
`underwriting_executed`와 `kyc_executed`는 거짓으로 남는다.

### 7.2 전이

| 단계 | 명령 | 다음 단계 | 효과 |
|---|---|---|---|
| 없음 | `offer` | `OFFERED` | 액면·금액·역할 라벨을 고정. 목 노트는 없음. `product`가 있으면 `CREDIT_PRODUCT_UNDEFINED` |
| `OFFERED` | `approve` | `APPROVED` | 단계만 이동. 예약도 노출도 없음 |
| `OFFERED` | `reject` | `REJECTED` | 이유 라벨만 기록. 심사 결과가 아님 |
| `OFFERED`, `APPROVED` | `cancel` | `CANCELLED` | 이유 라벨만 기록. 노트가 없으므로 해제할 예약도 없음 |
| `OFFERED`, `APPROVED` | `bind_settlement` | 유지 | 정산 id 기록만. 정산 명령을 호출하지 않음 |
| `APPROVED` | `draw` | `DRAWN` | 정산 게이트 §7.5 뒤에 `note_advance`. 노출은 제안 금액 전부. 한 번 |
| `DRAWN` | `repay` | `DRAWN` | 목 노출만 줄임. `reserved_open`은 유지. `repayment_observed`는 거짓 |
| `DRAWN` | `close` | `CLOSED` | 노출이 0일 때만 `release_note`. 천장만 되돌림 |
| `DRAWN` | `default` | `DEFAULTED` | 남은 노출이 있을 때만. 노트는 `NOTED`로 남고 천장을 계속 잡음 |
| 있는 건 | `reconcile` | 유지 | 재생 비교만 |
| 아무 때 | `reject_unsupported` | 유지 | §7.6. 항상 거절 |
| 아무 때 | `attempt_execution` | 유지 | §3 그대로. 항상 거절. 노트를 바꾸지 않음 |

`draw`는 제안 금액을 한 번에 노출로 올린다. 부분 인출은 없다. 부분 감소는 `repay`다.
같은 `draw_id`의 재전송은 효과를 다시 내지 않는다. 다른 `draw_id`로 이미 인출된 건을 다시 인출하면 `DUPLICATE_DRAW`다. 종결 뒤의 다른 `draw_id`는 `TERMINAL_IMMUTABLE`이다.
같은 `repay_id`와 같은 바인딩의 재전송은 효과를 다시 내지 않는다. 금액이나 순번이 다르면 `REPAY_BINDING_CONFLICT`다.
`sequence`는 1부터 빈틈 없이 증가하는 양의 `int`다. 아니면 `REPAYMENT_ORDER`다.
갚는 금액이 남은 노출보다 크면 `REPAYMENT_EXCEEDS_OUTSTANDING`이다. 노출이 0인 뒤의 새 상환 메모도 그 코드다.
`close` 전에 노출이 남아 있으면 `OUTSTANDING_REMAINS`이고 노트는 `NOTED`로 남는다.
노출이 0인데 `default`하면 `DEFAULT_REQUIRES_EXPOSURE`다.

한도 다툼은 한 프로세스 안의 명령 순서다. 스레드나 다른 채널의 현재성이 아니다.
`draw`가 `note_advance`를 부르는 순간에 §2의 `open_face - reserved_open`이 적용된다.
`confirmed_cash`와 `recovery_due`는 천장에 더하지 않는다.
먼저 수락된 노트가 천장을 차지하면 나중 인출은 `ADVANCE_EXCEEDS_OPEN_FACE`이고, 그 제안은 `APPROVED`로 남는다.
부분 상환은 `reserved_open`을 줄이지 않는다. `close`의 `release_note`만 그 금액만큼 천장을 되돌린다.
`default`는 되돌리지 않는다. 남은 노출이 있는 한 그 청구의 미예약 액면은 계속 줄어 있다.
되돌린 천장으로 새 `advance_id`를 인출할 수 있다. 그것은 재인출 약정이 아니다. 닫힌 id는 다시 `NOTED`가 되지 않는다.

§3의 해제는 상환이 아니다. `close`가 부르는 `release_note`도 같다.
그 호출은 목 노출이 이미 0인 뒤에 예약만 푼다. `repayment_observed`와 `funds_executed`는 거짓으로 남는다.
`repaid_exposure`는 이 기계가 센 목 메모의 합이다. 은행이 관찰한 입금이 아니다.

첫 수락 노트가 청구 조회를 고정하는 규칙은 §2 그대로다.
기계를 거치는 인출도 그 규칙을 다시 쓰지 않는다. 정산 목이 나중에 배정하거나 커밋해도 이 노출의 `open_face`는 제안 때 고정한 조회다.

역할 라벨은 여전히 대주가 아니다. `priority_bound`는 거짓이다.

### 7.3 멱등키

멱등키는 길이 1..100인 문자열이다. 형식 실패는 `INVALID_ID`이고, 그 호출은 키를 잡지 않는다.
키는 `(op, advance_id, 인자)`의 정규 JSON에 묶인다.

- 같은 키와 같은 정규 인자로 이미 수락된 명령은 `duplicate: true`, `applied: null`과 함께 처음 응답 스냅샷을 돌려준다. 효과는 한 번이다.
- 그 스냅샷은 수락 시점의 응답이다. 그 뒤의 전이는 `view`가 현재다.
- 같은 키와 같은 정규 인자로 이미 거절된 명령은 같은 오류를 다시 낸다.
- 같은 키와 다른 정규 인자는 `IDEMPOTENCY_CONFLICT`다.
- 거절된 명령은 저널에 들어가지 않는다. `restore`는 그 거절을 복원하지 않는다.
- 인출이 `SETTLEMENT_NOT_COMMITTED`로 거절된 키는, 나중에 정산 목이 `COMMITTED`가 되어도 그 키로 인출하지 않는다. 인출은 새 키가 필요하다.

`product`가 있으면 키를 잡은 뒤, 식별자보다 먼저 `CREDIT_PRODUCT_UNDEFINED`다.
같은 `advance_id`를 다른 키로 다시 `offer`하면, 바인딩이 같으면 `ILLEGAL_TRANSITION`이고 다르면 `ADVANCE_BINDING_CONFLICT`다. 제안의 재전송 경로는 같은 키다.

### 7.4 재생

수락된 명령만 `export_journal`에 쌓인다.
`CreditMachine.restore(journal, settlement_source, ownership_source)`는 빈 기계에 그 명령을 다시 적용한다.
같은 저널이고, 묶인 정산 조회가 그 명령이 요구하는 상태이면, `canonical_state`와 `state_digest`가 같다.

수락 뒤에 응답을 잃어도, 복원한 기계에 같은 키와 같은 인자를 다시 내면 duplicate이고 노출은 한 번이다.
거절된 명령은 저널에 없으므로 복원 결과에 포함되지 않는다.

`reconcile`은 현재 저널을 재생해 현재 상태와 비교한다.
같으면 `matched: true`다. 다르면 `MOCK_INVARIANT`다.
영수증은 저널에 넣지 않는다. 같은 프로세스에서 같은 키는 duplicate다.
`restore`는 영수증을 복원하지 않는다.
`state_digest`는 그 상태의 sha256이다. 서명이나 커밋먼트가 아니다.

이 재생은 메모리 안의 결정론이다. 디스크 원장, 은행 재시도, 체인 재생, 여신 재시도가 아니다.
정산 명령과 리셀 명령은 이 저널에 없다. `restore`는 그 기계를 다시 실행하지 않고, 묶인 인출이 요구할 때 정산 `view`만 다시 읽는다.

### 7.5 정산 게이트

`draw`는 경제 최종성을 주장하지 않는다. `economic_finality_claimed`를 참으로 만드는 인자는 없다.
성공, 거절, 재생의 봉투와 조회에서 그 필드는 거짓이다. `funds_executed`와 `bank_debit_observed`도 거짓이다.

`bind_settlement`은 정산 id만 적는다. `initiate`, `authorize`, `capture`, `commit`, `distribute`, `bind_refund`를 호출하지 않는다.
자금을 움직이지 않는다. 정산 기계의 `canonical_state`를 바꾸지 않는다.
인출 뒤에 정산을 묶지 않는다. 노출이 생긴 뒤의 `bind_settlement`은 `ILLEGAL_TRANSITION`이다.

정산 id가 없는 `draw`는 목 노출만 만든다.
`settlement_gate`는 `UNBOUND`이고, `mock_settlement_commit_observed`는 거짓이다.

정산 id가 있으면 `draw`는 노트를 만들기 전에 그 조회의 다음을 모두 요구한다.

- `phase`가 `COMMITTED`
- `settlement_id`가 제안 조회의 `claim_id`와 같음
- `currency`가 `KRW`이고 `gross`가 제안 조회의 `gross`와 같은 정수
- 안쪽 `claim`이 있고, 그 `provenance`는 `MOCK_SETTLEMENT_ONLY`, `claim_id`와 `gross`가 제안과 같음
- `funds_executed`, `bank_debit_observed`, `legal_debtor_bound`, `admission_granted`, `durable`이 모두 거짓
- `economic_finality_claimed`가 없거나 거짓. 참이면 거절
- 조회에 있는 그 밖의 최종성·담보 플래그도 거짓

하나라도 아니면 노트도 노출도 생기지 않는다. 단계는 `APPROVED`로 남는다.

| 조회 | 코드 |
|---|---|
| 정산 id가 있는데 정산 원천이 없음 | `SETTLEMENT_SOURCE_REQUIRED` |
| id가 정산 기계에 없음 | `UNKNOWN_SETTLEMENT` |
| `phase`가 `COMMITTED`가 아님 | `SETTLEMENT_NOT_COMMITTED` |
| 통화 또는 `gross`가 제안 조회와 다름 | `SETTLEMENT_AMOUNT_MISMATCH` |
| id가 다른 청구를 가리킴 | `SETTLEMENT_BINDING_CONFLICT` |
| 위 최종성 플래그가 참 | `SETTLEMENT_VIEW_REJECTED` |
| 같은 제안에 다른 정산 id | `SETTLEMENT_BINDING_CONFLICT` |

통과해도 `economic_finality_claimed`는 거짓이다.
`mock_settlement_commit_observed`만 참이고, `settlement_gate`는 `MOCK_COMMIT_OBSERVED`다.
이 참은 목 단계가 `COMMITTED`였다는 관찰이다. 입금, 은행 확정, 체인 최종성, 선지급 실행이 아니다.

이 관찰은 노출을 늘리는 `draw` 앞에만 선다. `repay`는 정산 명령을 다시 부르지 않는다.
묶인 인출을 재생하려면, 그 시점에 정산 조회가 `COMMITTED`이고 `gross`가 제안과 같아야 한다.

### 7.6 거절하는 상품·자금 경로

`reject_unsupported(kind)`는 단계를 바꾸지 않는다.

| `kind` | 코드 |
|---|---|
| `DISBURSE`, `REPAY`, `DEBIT`, `DISBURSE_TO_BANK` | `REAL_FUNDS_FORBIDDEN` |
| `ACCRUE`, `LICENSE`, `FORECLOSE`, `PRIORITY`, `PERFECT`, `INTEREST`, `FEE`, `KYC`, `AML`, `KYC_AML`, `RISK_SCORE`, `UNDERWRITE` | `CREDIT_PRODUCT_UNDEFINED` |
| 그 밖 | `EXECUTION_KIND` |

이 `REPAY`는 장부 명령 `repay`의 동의어가 아니다. 실자금 상환 라벨이다.
`INTEREST`, `FEE`, `KYC`, `RISK_SCORE`, `UNDERWRITE`를 성공 경로로 만들지 않는다.
`FORECLOSE`는 담보 실행이 아니다. `default` 뒤에도 같은 코드로 거절하고, 보유자와 버전은 그대로다.

`attempt_execution`은 §3의 닫힌 목록 그대로다. 기계가 그 앞에 있어도 노트를 바꾸지 않고 항상 예외다.
목록 안의 `REPAY`는 `REAL_FUNDS_FORBIDDEN`이다. 장부 `repay`와 함께 쓰지 않는다.

### 7.7 소유권

이 기계는 리셀 이전을 호출하지 않는다.
`ownership_source`가 있으면 명령 앞뒤로 그 객체의 `canonical_state`만 읽는다.
달라지면 `MOCK_INVARIANT`다. 보유자 교체, 버전 증가, 리스팅 단계 변경을 하지 않는다.
`ownership_mutated`와 `ticket_ownership_authoritative`는 거짓이다.
여신 단계는 티켓 소유의 권한이 아니다.

### 7.8 이 기계가 더하는 코드

§4의 코드는 목이 그대로 낸다. 기계가 더하는 코드는 다음이다.

| 코드 | 조건 |
|---|---|
| `ILLEGAL_TRANSITION` | 그 단계의 명령이 아님. 같은 바인딩의 재제안, 이미 묶인 같은 정산 id 포함 |
| `TERMINAL_IMMUTABLE` | 종결 뒤의 변경 |
| `IDEMPOTENCY_CONFLICT` | 같은 키, 다른 정규 인자 |
| `INVALID_JOURNAL` | `restore`가 읽을 수 없는 저널 |
| `DUPLICATE_DRAW` | 이미 인출된 건의 다른 `draw_id` |
| `REPAYMENT_ORDER` | 순번이 다음 양의 정수가 아님 |
| `REPAYMENT_EXCEEDS_OUTSTANDING` | 남은 목 노출보다 큰 상환 메모 |
| `REPAY_BINDING_CONFLICT` | 같은 `repay_id`, 다른 바인딩 |
| `OUTSTANDING_REMAINS` | 노출이 남은 `close` |
| `DEFAULT_REQUIRES_EXPOSURE` | 노출이 0인 `default` |
| `SETTLEMENT_SOURCE_REQUIRED` / `SETTLEMENT_NOT_COMMITTED` / `SETTLEMENT_AMOUNT_MISMATCH` / `SETTLEMENT_VIEW_REJECTED` / `SETTLEMENT_BINDING_CONFLICT` | §7.5 |

`UNKNOWN_SETTLEMENT`은 묶인 정산 기계의 코드다.

### 7.9 비청구

- 통과가 F04 또는 E06의 구현이나 설계확정이 아니다. 라벨은 설계중이다.
- `matched: true`는 이 프로세스의 저널과 조회가 같다는 뜻이다.
- `MOCK_COMMIT_OBSERVED`는 목 정산 단계의 관찰이다. 자금 집행이나 선지급이 아니다.
- `economic_finality_claimed`, `funds_executed`, `bank_debit_observed`, `repayment_observed`, `interest_defined`는 인출과 상환 메모 뒤에도 거짓이다.
- `repaid_exposure`와 `outstanding_exposure`는 목 장부 정수다. 규제 상환, 연체, 손실 귀속, 상각이 아니다.
- `default`는 연체 판정, 상각, 처분, 유질, 우선순위가 아니다. 티켓을 넘기지 않는다.
- `approve`와 `reject`는 심사, KYC-AML, 위험 점수, 인허가가 아니다.
- 한도 순서는 한 프로세스 안의 배타다. 분산 잠금이나 은행 한도가 아니다.
- 이 저널은 내구 원장, 체인 커밋먼트, 은행 exactly-once가 아니다.
- 직접 `MockCredit` 호출은 이 단계 게이트를 지나지 않는 Wave 5 술어다.
- 라이브 HTTP, 언더라이팅, KYC-AML, PG·은행 레일, 실여신, commerce-apps 변경은 없다.
- 새 `protocol_contract` 명령과 OpenAPI 카탈로그 명령은 없다.
