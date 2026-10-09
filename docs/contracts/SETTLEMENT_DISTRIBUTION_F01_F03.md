# 정산 분배 F01–F03 — 목 계약

Task 005 Wave 3. 문서일: 2026-09-26.
구현 기준 `origin/main`: `a2814923bc671889da49984a2c95964340a1506d`.
이 문서는 오프라인 목(mock)이 지킬 술어와, 아직 정하지 않은 간극을 적는다.
`docs/status/ORIGINAL_32_STATUS.md`의 F01·F02·F03·P04 라벨은 **설계중** 그대로다.
이 계약은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.

2026-10-08 개정 ID `SET-POLICY-DRAFT-0.2`.
이 세션에서 확인한 `origin/main`과 작업 브랜치 HEAD는 `771545ae4b64f069396667f399b5200c44fd9af0`다.
이 개정은 §7을 번호 있는 선택지 초안으로 바꾼다. §0.3과 §5에는 그 절로 가는 문장만 더한다. §8에는 비채택 한 줄을 더한다. §0–§6과 §8–§9의 술어는 그대로다.
값을 채택하지 않는다. 제품 정책의 채택은 `DECISION_REQUIRED · Astra`다
([PROGRAM_ROADMAP_20260930.md](../decisions/PROGRAM_ROADMAP_20260930.md) §2 R-9).
법률·세무·회계가 필요한 값은 `UNDETERMINED`이고, 담당 경로는
[FIRST_BATCH_OPEN_INPUTS.md](FIRST_BATCH_OPEN_INPUTS.md) I10이다.
2026-09-26 본문에는 개정 ID가 없었다. `0.2`는 그 본문을 0.1 발행으로 소급하지 않는다.
산술 계약 위에 올린, 아직 채택되지 않은 정책 선택지 층이다.
결정된 항목이 0이므로 `reference/settlement_f01_f03`와 그 시험은 바꾸지 않는다.
카탈로그, 게이트, 스키마, 영수증, manifest에 묶인 원본 바이트도 바꾸지 않는다.
이 개정은 새 프로토콜 명령이 아니고, BOOTSTRAP이나 SEMANTIC_CONFORMANCE 적격이 아니다.
0.2의 「값을 채택하지 않는다」는 그 초안이 멈춘 기록이다. 아래 0.3이 권고 행만 목의 자세로 채택한다.

2026-10-09 개정 ID `SET-POLICY-DRAFT-0.3`.
소유자 JunTae가 2026-10-09 12:34 KST에 0.2의 권고 L0, W0, R0, S0, T0, B0, P0를 이 목의 자세로 채택했다.
이 세션에서 확인한 `origin/main`은 `17c8a7dc66e49b090067b94ff7bc68cb6d79c5ee`다.
작업 브랜치 HEAD는 `771545ae4b64f069396667f399b5200c44fd9af0`이고, 그 `origin/main`보다 48커밋 뒤다.
이 개정은 그 브랜치의 0.2 초안을 이어 고친다. main을 이 브랜치에 병합하지 않는다.
`origin/main`의 정산 계약은 §9에서 OpenAPI 카탈로그의 `settlement_<op>`를 말한다. 그 카탈로그 바이트는 이 브랜치에 없다. 이 개정은 그 바이트를 다시 만들지 않고, 이 트리가 그 명령을 가진 것처럼 적지 않는다.
채택은 목의 지금 술어를 자세로 고정하는 일이다. 산술 파일 `mock_settlement.py`와 `settlement_fsm.py`는 바꾸지 않는다.
세율, 준비율, 리셀 bps, waterfall의 상한·원가·구간·지급 시점, 잔여 단위의 수취인 지명은 권고가 비운 그대로 `UNDETERMINED`다.
법률상 채무자·채권자, 세금의 성격, 예수·준비금의 회계 분류도 `UNDETERMINED`다. 담당 경로는 I10이다.
P04를 저장 엔진이나 실 PG·은행 관찰로 구현하는 일은 프로그램 결정 §5의 잠금 안에 있어 미룬다. 실자금, Sui mainnet, 운영 런타임, 비밀은 범위 밖이다.
이 채택은 Astra의 아키텍처 서명이 아니다. 새 프로토콜 명령을 만들지 않는다.
카탈로그, 게이트, 스키마, 영수증, manifest에 묶인 원본 바이트는 바꾸지 않는다.
이 개정은 BOOTSTRAP이나 SEMANTIC_CONFORMANCE 적격이 아니다.
L0·W0·R0·S0·B0·P0의 관찰값은 이미 있는 시험이 고정한다. T0에서 세금·보류가 0이 아닌 경우는 그 시험에 없었다.
`reference/settlement_f01_f03/test_adopted_policy.py`가 그 빈자리와, 일곱 자세의 관찰값을 한 자리에 묶는다.

2026-09-26 settlement depth가 §9의 수락 상태 기계를 앞에 둔다.
그 세션에서 확인한 `origin/main`은 `a744b0a036d7e1edb48416871af20cd182f23df4`다.
산술 술어와 Wave 3의 기준 SHA는 그대로다. 라벨도 그대로다.

2026-09-26 SETTLEMENT-EXTENSIBILITY-DOC-001이 §0.1–§0.3을 추가했다.
그 확인의 `origin/main`은 `85145eb33799a7c712890ff81708def8a7d61ee5`다.
위 기준 SHA와 §9는 그대로다.

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
| 수락 상태 | initiate부터 reconcile까지의 결정론적 전이, 멱등키, 종결 뒤 불변, 저널 재생 | 은행·PG 실행, 내구 원장, P04 종결 |

산술 파일은 `reference/settlement_f01_f03/mock_settlement.py`다.
수락 상태 기계는 `reference/settlement_f01_f03/settlement_fsm.py`다. §9.
실행 방법과 비청구는 [validation/2026-09-26-wave3-settlement-f01-f03/README.md](../../validation/2026-09-26-wave3-settlement-f01-f03/README.md)에 있다.
네트워크, 파일, PG, 은행, 커널, Move를 호출하지 않는다.
프로세스 메모리 안의 결과이며 내구 원장이 아니다.
모든 조회에 `provenance = MOCK_SETTLEMENT_ONLY`를 붙인다.

모델 1의 문장 그대로, 체인 기록이 은행 자금·계약상 채무·공연 이행을 보증하지 않는다.
커널의 `ReturnRequired`는 환불 요청 승인도 환불 완료도 아니다
([STATE_LIFECYCLE.md](STATE_LIFECYCLE.md) §5.7). 이 목의 환불 의무는 그 표식이 아니고,
그 표식을 해제하거나 대체하지 않는다.

### 0.1 커널 정산 책임 경계

잠금 커널은 읽기만 했다. 이 절은 커널 파일을 바꾸지 않는다.
예약, 수명, 격리, 용량은 커널 의무로 남고, 그 범위를 `captured`로 줄이지 않는다.

| 확인 | 값 |
|---|---|
| 스캔한 파일 | `runtime/crates/kix-kernel/src/lib.rs` |
| 그 blob | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| 잠금만 확인, 본문은 스캔하지 않음 | `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20` |
| 이 확인의 `origin/main` | `85145eb33799a7c712890ff81708def8a7d61ee5` |

`lib.rs`를 읽기 전용으로 검색했다. `payee`, `recipient`, `payout`, `settle`, `split`, `allocate`, `obligation` 식별자는 없다. `distribute` 식별자도 없다.

주석에만 있는 근접 표현은 둘이다.

- 예약 거절 근처(L418): “The inbox must reconcile evidence the kernel could not retain.” 커널이 남기지 못한 증거의 대사를 inbox에 둔다. 은행 정산 대사가 아니다.
- `replace_owner` 문서(L521): “Actual distributed handoff”는 소유권 교체의 분산 인계가 구현되지 않았다는 뜻이다. 정산 지급이 아니다.

금액이 실리는 필드는 다음 세 개다.

- `Reserve.amount: AssetAmount`
- `Order.captured: Option<AssetAmount>`
- `CaptureObservation.amount: AssetAmount`

`observe_capture`는 수취인별로 나누지 않는다.
이미 `captured`가 있으면 그 값과 `observation.amount`의 같음만 본다. 같으면 `DuplicateEffect`이고, 다르면 `Review`다.
첫 포착은 `observation.amount`를 `captured`에 저장한다.
그 값이 `order.request.amount`와 다르면 포착 결과 경로로 `Review`를 기록한다.

비공식 요약 “금액 필드 세 개, 비교만”은 이 파일보다 좁다. 세 필드는 맞다.
그에 더해 예약은 `request.amount.atoms() == 0`이면 `InvalidRequest`로 거절한다(L407).
첫 포착은 금액을 보존하고, 이후 포착은 보존된 `captured`와 비교한다.
관측 구조체 전체의 같음(`original == observation`)과 예약 명령 페이로드 전체의 같음(`record.request != request`)에도 금액이 들어 있다.
이 비교와 보존은 포착 사실의 결합이다. 수취인별 배분이 아니다.

커널은 지원하는 포착 사실을 결합하고, 비교하고, 보존한다.
수취인별 의무, 배분, 지급, 은행 정산의 대사는 커널 밖에 있다.
`captured`는 은행 정산 완료도 실제 지급 완료도 아니다.
커널 밖에 둔다는 문장은 R2, (a), 실자금, 새 구현의 승인이 아니다.

### 0.2 수취인 수

「정산 수취인 단일 전제를 계약에 고정하지 않는다.」

현재 목의 `residual_payee`, `fee_payee`와 픽스처 주문의 제한된 수취인 프로파일은 시험 프로파일이다.
일반 계약이 앞으로 가질 수 있는 수취인 수의 한도가 아니다.
새 타입, 스키마, API는 만들지 않는다.

한 결제 대금을 복수 수취인에게 나눌 수 있는지는 [PG_TOSS_CARD_PROFILE.md](PG_TOSS_CARD_PROFILE.md) §8의 미확인 질문이다.
그 질문을 가맹 허용의 증거로 읽지 않는다.

### 0.3 정수 잔여 단위의 배분 원칙

원칙이다. 새 알고리즘 구현이 아니다. 픽스처, 코드, 시험은 바꾸지 않는다.

- 자산 최소 단위로 정확한 정수 산술을 한다.
- 나눗셈 뒤의 잔여 단위는 배분 전에 정한 고정된 결정론적 우선순위로 배정한다.
- 운영자가 사후에 임의로 귀속하지 않는다. 부동소수점 반올림을 쓰지 않는다.
- 배분액의 합은 배분 총액을 보존한다.
- 구체적인 수취인 순서와 우선순위 방법은 **UNDETERMINED**다. 기본 정책을 두지 않는다. §7.3의 채택은 R0다. R0는 이 방법을 정하지 않고, 수취인 지명을 만들지 않는다.

이 원칙은 아래 셋과 다른 문장이다. 셋을 일반 정산 정책으로 올리지 않는다.

1. 부족 현금의 지급 우선순위. §4의 F02는 호출자가 적은 순서, 곧 픽스처 우선순위로 확인 현금을 배정한다. 나눗셈 잔여 단위의 귀속 방법이 아니다.
2. 기존 목의 수수료·잔여 계산. §2의 `fee = gross * fee_bps // 10000`, `residual = gross - fee`는 일차 판매 수수료의 목 산술이다.
3. 기존 주문 줄 할인 배분. `reference/v0.3-rc1/commerce.py`의 `proportional`은 줄 할인에 대한 largest-remainder이고, 동점은 줄 ID 오름차순이다. 그 규칙을 정산 정책으로 가져오지 않으며, 그 파일을 수정하지 않는다.

토큰, 수익권, 크레딧 타입, 법적 구조, 수취인의 법률상 지위, 상품 waterfall은 이 절의 범위 밖이다.
§9의 수락 상태 기계는 이 추가가 바꾸지 않는다.

## 1. 공통 돈·식별 한계

역사 참조 `reference/v0.3-rc1/contracts.py`의 정수 상한과 같다. 새 상품 한도가 아니다.

- 통화는 `KRW`만 받는다. 다른 통화는 `CURRENCY_UNSUPPORTED`.
- 금액은 `bool`이 아닌 `int`다. 양수 금액은 `1 .. 10**12`, 비음수 금액은 `0 .. 10**12`.
- 식별자와 역할 라벨은 길이 1..100인 문자열이고, 앞뒤 공백을 허용하지 않는다. 실패 코드는 `INVALID_ID`.
- 역할 문자열(`debtor_role`, 수취인, 환불 상대)은 저장만 한다. 사람·계좌·사업자·법률 당사자로 해석하지 않는다.
- 같은 키의 재전송은 바인딩이 같으면 경제 효과를 한 번만 낸다(`duplicate: true`). 바인딩이 다르면 충돌이다. 이 문장의 키는 청구·명세서·환불·수락 식별자다. 명령 멱등키는 §9다.
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

수익 참여의 회수 순서·원가·상한·반올림 부담의 숫자는 `UNDETERMINED`다. 상품 waterfall을 이 목에 만들지 않는 채택은 §7.2 W0다.
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
- 부분 환불(전액이 아닌 경우, 또는 여러 번에 나뉜 경우)은 의무만 쌓는다. 수취인 액면을 취소하거나 회수채권으로 바꾸지 않는다. `refund_bearer_policy = UNDEFINED`. 법률상 부담자는 미정이다. §7.6이 B0를 이 목의 자세로 채택한다. B0는 이 값을 `UNDEFINED`로 둔다.
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
| `UNKNOWN_SETTLEMENT` | 상태 기계에 없는 정산 건 |
| `ILLEGAL_TRANSITION` | 현재 단계에서 허용되지 않은 명령 |
| `TERMINAL_IMMUTABLE` | `FAILED` 또는 `CANCELLED` 뒤의 변경 명령 |
| `IDEMPOTENCY_CONFLICT` | 같은 멱등키, 다른 정규 인자 |
| `EXTERNAL_PAYMENT_UNSUPPORTED` | 은행·PG·지급 시도 |
| `INVALID_JOURNAL` | `restore`에 넘긴 저널 형식 |

`MOCK_INVARIANT`는 목 내부 불변식이 깨진 구현 오류다. 호출자가 맞출 수 있는 입력 거절이 아니다.
재생한 상태가 저널과 어긋날 때도 이 코드다.

## 7. 정책 자세 — 개정 `SET-POLICY-DRAFT-0.3`

0.2의 표는 선택지로 남긴다. 0.3은 각 표의 권고 행만 이 목의 자세로 채택한다.
채택된 행은 L0, W0, R0, S0, T0, B0, P0이다. 다른 행은 채택하지 않는다.
채택은 새 산술이 아니다. `mock_settlement.py`와 `settlement_fsm.py`는 그대로다.

법률·세무·회계가 필요한 값은 `UNDETERMINED`로 남긴다. 권고가 숫자를 비운 항목도 `UNDETERMINED`다.
비운 숫자는 세율, 준비율, 리셀 bps, waterfall의 상한·원가·구간·지급 시점, 잔여 단위의 수취인 지명이다.
그 숫자를 이 개정은 적지 않는다.

이미 있는 시험이 채택된 자세의 대부분을 고정한다.

| 자세 | 시험 |
|---|---|
| L0 | `test_f01_split_opens_obligations_without_cash_or_legal_binding` |
| W0 | `test_f02_caller_order_selects_shortfall_and_then_freezes` |
| R0 | `test_f01_fee_floor_zero_fee_and_rejected_policies` |
| S0 | 같은 시험의 `POLICY_KIND` (`kind`가 `RESALE_BPS`) |
| B0 | `test_f03_partial_refund_blocks_distribution_without_reclassifying`, `test_f03_partial_after_distribution_does_not_claw_back`, `test_refund_block_survives_replay_and_is_not_a_clawback` |
| P0 | `test_happy_path_posts_mock_economics_without_external_execution`, `test_terminal_fail_and_cancel_are_immutable` |
| T0 | 기존 명세서는 `tax`와 `held`가 0이다. `test_t0_tax_and_held_stay_non_cash`가 0이 아닌 경우를 고정한다 |

`test_adopted_policy_posture`는 위 일곱 자세의 관찰값을 한 청구 흐름에 묶는다. 오류 행렬을 다시 쓰지 않는다.
전액 1회 재분류는 채택된 부담 규칙이 아니다. `test_f03_full_refund_reclassifies_and_mock_acceptance_is_not_closure`가 픽스처 재분류로 남긴다.

I10은 법정·대사·분쟁의 보존과 삭제 보류이고 상태는 미완결이다. 담당은 사용자가 당사자·관할·자료를 제공한 뒤의 법무·개인정보 검토다.
채무자 특정과 세금 분류는 I10의 보존 기간 질문 자체가 아니다. 같은 담당 경로에 두되, I10의 답을 채무자나 세율의 답으로 바꾸지 않는다.
이 개정은 I10 문서를 고치지 않는다. 로드맵 D-E의 법률·회계·세무 검토 주체와 시점은 사용자 몫이다.

아래 표의 「지금 효력」은 §0–§6과 §9의 목 동작이고, 0.3이 권고 행에서 그 동작을 자세로 채택한 것이다. 다른 선택지는 구현이 아니다.

### 7.1 법적 채무자·채권자

| | |
|---|---|
| 지금 효력 | 역할 문자열은 저장만 한다(§1). `legal_debtor_bound`는 항상 거짓이다. F01이 고정하지 않는 열은 법적 채무자·채권 발생/소멸·수익 귀속이다(§0). |
| 분류 | L0 채택(목). 법률상 채무자·채권자의 이름은 `UNDETERMINED`. 법률 조언이 필요하다. 제품 값으로 채우지 않는다. |
| 담당 | 사용자(당사자·관할·자료), 그 다음 법무. 경로는 I10과 같다. 보존 기간 질문은 별도로 미완결이다. |

| 선택지 | 내용 | 0.3에서의 위치 |
|---|---|---|
| L0 | 역할 라벨을 법률 당사자에 묶지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |
| L1 | 사용자가 당사자와 관할을 주고 법무가 채무자·채권자를 특정한 뒤에만 묶는다. | 그 입력이 오기 전에는 없다. 이 개정은 이름을 만들지 않는다. |
| L2 | 플랫폼 또는 주최자를 장부 채무자로 둔다. | 법률 결론이다. 채택하지 않는다. |

환불채무자의 법률상 특정은 §7.6의 법률 열과 같은 담당이다. 여기서 따로 정하지 않는다.

### 7.2 수익 waterfall

| | |
|---|---|
| 지금 효력 | 확인 현금은 호출자가 적은 의무 수취인 순열로만 배정한다(§4). 그 순서는 픽스처 우선순위다. 원가 회수, 구간, 상한, 수익 참여가 아니다. 부족분은 잔여 의무로 남는다. |
| 분류 | W0 채택(목). 원가·구간·상한·지급 시점의 숫자는 `UNDETERMINED`다. 원가의 회계 정의가 필요하면 담당은 사용자와 회계다. |
| 담당 | 숫자 상한·원가 정의·지급 시점을 이 개정은 적지 않는다. 그 숫자의 담당은 사용자와 회계다. |

| 선택지 | 내용 | 0.3에서의 위치 |
|---|---|---|
| W0 | 호출자 순서를 픽스처로만 둔다. 상품 waterfall을 만들지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |
| W1 | 수수료 수취인을 잔여 수취인보다 앞에 두는 2인 순서. | `PRIMARY_FEE_BPS`의 두 라벨에만 맞는다. 일반 waterfall이 아니다. 권고하지 않는다. |
| W2 | 원가 회수, 상한이 있는 참여, 그 다음 잔여. | 원가·구간·상한·지급 시점이 비어 있다. 그 숫자를 만들지 않는다. |
| W3 | 미지급 액면 비율로 나눈다. | §4의 호출자 순서와 다른 술어다. 채택하지 않는다. |
| W4 | 계산 전에 얼린 순위표. 순위표의 내용은 별도 결정이다. | 순위·원가·상한·시점이 정해진 뒤의 자리다. 지금 그 표를 쓰지 않는다. |

채택은 W0이다. W1–W4는 채택하지 않는다. W2와 W4는 원가·구간·상한·지급 시점이 문서로 정해진 뒤에만 다시 연다. 그 값은 이 문서에 없고 `UNDETERMINED`다.

### 7.3 정수 잔여 단위의 수취인 순서

| | |
|---|---|
| 지금 효력 | 원칙은 §0.3이다. 방법은 **UNDETERMINED**이고 기본 정책이 없다. §2의 `fee = gross * fee_bps // 10000`, `residual = gross - fee`는 일차 판매 수수료의 목 산술이다. 일반 잔여 단위 정책이 아니다. |
| 분류 | R0 채택(목). 방법은 여전히 `UNDETERMINED`이고 기본 정책이 없다. |
| 담당 | 수취인 지명은 없다. §4의 부족 현금 순서, §2의 수수료 산술, `reference/v0.3-rc1/commerce.py`의 줄 할인 배분과 다른 문장으로 남긴다. |

| 선택지 | 내용 | 0.3에서의 위치 |
|---|---|---|
| R0 | 방법을 비운 채로 둔다. §2의 바닥 나눗셈을 일반 정책으로 올리지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |
| R1 | largest-remainder, 동점은 식별자 오름차순. | 줄 할인 규칙이다(§0.3). 정산 정책으로 가져오지 않는다. 권고하지 않는다. |
| R2 | 나눗셈 전에 정책이 지명한 한 수취인에게 잔여 단위를 준다. | 지명이 있어야 한다. 지금 지명이 없다. |
| R3 | 잔여 단위가 §4의 호출자 순서를 따른다. | 부족 현금과 나눗셈 잔여를 한 술어로 합친다. §0.3이 둘을 다른 문장으로 둔다. 권고하지 않는다. |
| R4 | 정책에 얼린 순서의 마지막 수취인에게 준다. | 그 순서가 정해진 뒤의 자리다. 지금 쓰지 않는다. |

채택은 R0이다. 방법과 수취인 지명은 `UNDETERMINED`로 남는다. R1과 R3는 채택하지 않는다. 이 절은 알고리즘을 구현하지 않는다. §0.3이 픽스처와 코드를 바꾸지 말라고 한 문장은 그대로다.

### 7.4 리셀 대금 분할

| | |
|---|---|
| 지금 효력 | `resaleFeeBps`, `resaleOrganizerBps`, 판매자 잔여는 이 정책에 없다(§2). 역사 `core.py`의 계산을 이 목이 상품 규칙으로 다시 정하지 않는다. `kind`는 `PRIMARY_FEE_BPS`만이다. |
| 분류 | S0 채택(목). 리셀 bps는 `UNDETERMINED`다. 비율 숫자를 만들지 않는다. |
| 담당 | 리셀 비율의 담당은 사용자다. 역사 계획의 인용은 아래 S3이다. 그 인용을 새 채택으로 세지 않는다. |

| 선택지 | 내용 | 0.3에서의 위치 |
|---|---|---|
| S0 | 리셀 분할을 이 F01 정책 밖에 둔다. | 지금 효력. 0.3이 이 행을 채택한다. |
| S1 | 나중 개정에서 리셀용 `kind`를 따로 둔다. bps는 그 개정이 정한다. | 지금 `kind`를 늘리지 않는다. 카탈로그 명령도 만들지 않는다. |
| S2 | 역사 `core.py`의 리셀 식을 이 목의 규칙으로 가져온다. | §2가 막는다. 권고하지 않는다. |
| S3 | 직전 구매자가 이후 리셀 이익에 계속 참가한다. | [PROTOCOL_MASTERPLAN_V2.md](../PROTOCOL_MASTERPLAN_V2.md) §7은 과거 구매자라는 이유만으로 후속 리셀 이익을 계속 받는 구조를 포함하지 않는다고 적었다. 그 파일은 역사 계획이다(이 문서 머리말). 이 개정은 그 문장으로 새 긍정 규칙을 만들지 않고, 반대 규칙도 만들지 않는다. 다시 여는 것은 Astra의 별도 결정이다. |

채택은 S0이다. S1–S3는 채택하지 않는다. S3를 이 목의 규칙으로 추가하지 않는다. 리셀 bps는 `UNDETERMINED`이고 담당은 사용자다.

### 7.5 세금·보류·준비금

| | |
|---|---|
| 지금 효력 | 명세서의 `tax`·`held`·`adjustment`는 미수에서 빠지지만 배정 가능한 현금이 아니고 의무 액면을 줄이지 않는다(§3). 해제, 실제 회수, 거래 간 상계, 준비금, 연체, 상각은 비어 있다. |
| 분류 | T0 채택(목). 세금의 성격, 예수·준비금·손실의 회계 분류, 보존 기간은 `UNDETERMINED`다. 세무·회계 조언이 필요하다. 세율·준비율·해제 기한을 적지 않는다. |
| 담당 | 사용자(관할·자료), 그 다음 세무·회계. 경로는 I10과 같다. I10의 보존·삭제 보류는 그 자체로 미완결이고, 이 표의 세율 질문이 아니다. |

| 선택지 | 내용 | 0.3에서의 위치 |
|---|---|---|
| T0 | `tax`와 `held`를 현금이 아닌 명세서 사실로만 둔다. 해제·적립·납부를 목에 만들지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |
| T1 | `held`를 확인 현금으로 옮기는 해제 술어. | 보류의 회계 분류와 시점이 없다. 채택하지 않는다. |
| T2 | 세금을 수취인 의무로 만든다. | 세무 결론이다. 채택하지 않는다. |
| T3 | 총액의 일정 비율을 준비금으로 쌓는다. | 비율이 제품 값이다. 만들지 않는다. |

채택은 T0이다. T1–T3는 채택하지 않는다. 세율과 준비율은 `UNDETERMINED`다. 담당은 사용자, 그 다음 세무·회계다. 회계 담당이 분류를 답하기 전에 해제 스위치를 열지 않는다.

### 7.6 부분 환불의 부담자

| | |
|---|---|
| 지금 효력 | 부분 환불은 `refund_bearer_policy = UNDEFINED`다(§5). 액면을 취소하거나 회수채권으로 바꾸지 않는다. 그 동안 `apply_distribution`은 `DISTRIBUTION_BLOCKED_REFUND_BEARER_UNDEFINED`다. 이미 배정한 금액은 되돌리지 않는다. 전액 1회는 `FIXTURE_FULL_GROSS_RECLASS`이고, 법적 부담자 확정이 아니다. 부분을 더해 합이 `gross`가 되어도 전액 재분류가 되지 않는다. |
| 분류 | B0 채택(목). `refund_bearer_policy`는 `UNDEFINED`다. 법률상 환불채무자는 `UNDETERMINED`(사용자 → 법무, I10 경로). |
| 담당 | 법률 당사자는 법무. 픽스처 줄의 이동은 그 법률 답 뒤에 남긴다. 이 개정은 B1–B4를 고르지 않는다. |

| 선택지 | 내용 | 0.3에서의 위치 |
|---|---|---|
| B0 | `UNDEFINED`를 유지한다. 추가 배정을 멈추고 액면을 그대로 둔다. 자동 상계를 만들지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |
| B1 | 미지급 액면을 비율로 줄이고, 이미 배정한 금액은 그 비율의 `recovery_due`로 둔다. | 전액 재분류를 부분으로 늘린 상품 규칙이다. 채택하지 않는다. |
| B2 | 수수료 수취인이 먼저 부담한다. | 상품 규칙이다. 채택하지 않는다. |
| B3 | 잔여 수취인이 먼저 부담한다. | 상품 규칙이다. 채택하지 않는다. |
| B4 | 플랫폼이 전액 부담한다. | 플랫폼을 법률상 환불채무자로 두는 결론이 먼저다(§7.1 L2). 채택하지 않는다. |

할인 재계산과 복수 결제수단 배분은 이 표에 넣지 않는다. §7.8에 빈 항목으로 남긴다.
채택은 B0이다. 법률상 환불채무자는 `UNDETERMINED`다. B1–B4는 채택하지 않는다.

### 7.7 P04 영속 종결

| | |
|---|---|
| 지금 효력 | `FAILED`와 `CANCELLED`는 이 목의 종결이다(§8, §9). P04 정산 종결이나 외부 반환 종결이 아니다. `durable`은 수락 뒤에도 거짓이다. 재생은 프로세스 메모리 안이다. |
| 분류 | P0 채택(목). 목의 `FAILED`와 `CANCELLED`를 P04 종결로 읽지 않는다. 영속 저장이나 제공자 자금 이동의 구현은 프로그램 결정 §5의 잠금이라 미룬다. |
| 담당 | 저장 엔진의 해제와 실 PG·은행 관찰의 해제는 사용자(프로그램 결정 §5). 이 개정은 그 해제를 요청하지 않고, 해제된 것처럼 쓰지 않는다. |

| 선택지 | 내용 | 0.3에서의 위치 |
|---|---|---|
| P0 | P04 종결을 성공으로 정의하지 않는다. 목 종결을 P04로 읽지 않는다. | 지금 효력. 0.3이 이 행을 채택한다. |
| P1 | 나중에, 실행 없이, 종결에 필요한 증거 이름만 적는다. 제공자 이동 식별, 의무 잔액, 영속 커밋 위치. | 구현은 `k-stage5-durable-tx`와 `k-stage6-economics-reference` 쪽의 후속이다. 실자금 관찰은 §5 잠금 뒤다. 이 개정은 그 증거 스키마를 쓰지 않는다. |
| P2 | 새 저장소에 영속 종결을 구현한다. | 저장 엔진과 실자금이다. 이 노드의 범위 밖이다. |
| P3 | `FAILED` 또는 `CANCELLED`를 P04 종결로 본다. | §8이 막는다. 권고하지 않는다. |

채택은 P0이다. P1–P3는 채택하지 않는다. 새 종결 명령을 만들지 않는다. `durable`은 거짓으로 남는다. §9가 새 프로토콜 명령은 `DECISION_REQUIRED · Astra`라고 한 문장은 그대로다.

### 7.8 이 개정이 열지 않는 항목

아래는 2026-09-26과 같이 비어 있다. 이 개정은 선택지 표도 만들지 않는다.

- 채권 양도·담보·중복 담보의 대외 완전성
- 부분 환불의 할인 재계산, 복수 결제수단 배분
- 권리 폐기·재고 반환·검표 차단
- 은행 출금, PG 라이브 취소, 차지백, 고객 계정 입금 확인
- 거래 간 정산 상계, 준비금, 연체, 상각. 준비금의 비율은 §7.5에서 만들지 않는다고 적었고, 이 항목은 비어 있다
- F04 여신·선지급·실자금
- 내구성, 정확히 한 번의 은행 반영, 체인 최종성, 규제 준수. P04의 자리는 §7.7이다
- 제품 TPS, p99, 실패율
- 상태 기계의 저널을 내구 원장이나 체인 커밋먼트로 읽는 일

## 8. 비청구

이 문서와 목 시험의 통과는 F01–F03이 구현되었다는 뜻이 아니다.
라벨은 설계중이다.
개정 `SET-POLICY-DRAFT-0.2`의 선택지 표는 남아 있다. `SET-POLICY-DRAFT-0.3`은 그 표의 L0, W0, R0, S0, T0, B0, P0만 목의 자세로 채택한다. 그 채택은 법률·세무·회계의 답도, 비운 제품 숫자의 확정도 아니다.
목 배정은 정산 입금이 아니고, 목 취소 수락은 환불 완료가 아니다.
`reference/v0.3-rc1`의 금융 모형 전체를 대체하지 않으며 그 파일을 수정하지 않는다.
상태 기계의 `matched: true`는 이 프로세스 저널의 재생 일치다. 은행 exactly-once, 토스 대사, 체인 최종성이 아니다.
`FAILED`와 `CANCELLED`는 이 목의 종결이다. P04 정산 종결이나 외부 반환 종결이 아니다.
`state_digest`는 케이스와 저널의 sha256이다. 서명이나 커밋먼트가 아니다.

## 9. 참조 수락 상태 기계

Wave 3 목은 계산 술어만 고정했다. 단계가 없었고, 포착 전에 실패·취소를 나누지 않았고, 프로세스 저널을 재생하지 않았다.
이 절의 기계가 그 빈자리를 채운다. 산술 파일은 그대로다. 기계가 술어를 호출하기 전에 전이를 거절하거나, 수락한 명령을 저널에 한 번 적는다.

F01·F02·F03·P04는 **설계중**이다. 이 절이 그 라벨을 올리지 않는다.

이 기계는 `protocol_contract.json`에 명령을 넣지 않는다.
역사 스키마의 `capture`와 `settle_capture`는 로컬 호출 목록에 남아 있고, 이 기계는 그 명령을 실행하지 않는다.
이 개정은 OpenAPI 카탈로그 바이트를 바꾸지 않는다. `origin/main` `17c8a7dc66e49b090067b94ff7bc68cb6d79c5ee`의 같은 절은, 카탈로그에 이 기계의 `REPLAYABLE`만 `settlement_<op>`로 있다고 적는다. 그 카탈로그 변경은 이 브랜치에 없다. 그 집합 밖의 새 프로토콜 명령은 `DECISION_REQUIRED · Astra`다.

수락 기준은 이 참조 모듈 안의 결정이다. 법적 권위, 체인 권위, 은행 권한이 아니다.
조회 라벨 `lifecycle_authority = IN_MEMORY_FSM`은 그 한계를 적는다.

### 9.1 단계

```text
(없음)
  | initiate
  v
INITIATED --authorize--> AUTHORIZED --capture--> CAPTURED --commit--> COMMITTED
    | \                      | \
    |  \ fail / cancel       |  \ fail / cancel
    v   v                    v   v
 FAILED  CANCELLED        FAILED  CANCELLED
```

`COMMITTED`에서 `observe_statement`, `distribute`, `bind_refund`, `observe_mock_cancel_acceptance`는 단계를 유지한다.
`CAPTURED`에서도 환불 바인딩과 목 취소 수락은 단계를 유지한다.
단계는 뒤로 가지 않는다.

`FAILED`와 `CANCELLED`만 종결이다. 이후 변경 명령은 `TERMINAL_IMMUTABLE`이다.
`reconcile`과 `view`는 종결 뒤에도 된다. `reject_external`은 종결을 바꾸지 않고 거절만 한다.

포착 전의 `cancel`은 청구를 열지 않는 목 무효다.
포착 뒤의 환불은 `bind_refund`다. 포착 뒤에 `cancel`이나 `fail`로 청구를 지우지 않는다.

### 9.2 전이

| 단계 | 명령 | 다음 단계 | 경제 효과 |
|---|---|---|---|
| 없음 | `initiate` | `INITIATED` | 없음. 총액·정책·역할만 고정 |
| `INITIATED` | `authorize` | `AUTHORIZED` | `mock_authorized`만 참. 제공자 호출 없음 |
| `INITIATED`, `AUTHORIZED` | `fail` | `FAILED` | 없음. 이유 라벨만 기록 |
| `INITIATED`, `AUTHORIZED` | `cancel` | `CANCELLED` | 없음. 이유 라벨만 기록 |
| `AUTHORIZED` | `capture` | `CAPTURED` | `recognize_claim`. 확인 현금은 0 |
| `CAPTURED` | `commit` | `COMMITTED` | 첫 `observe_settlement_statement` |
| `COMMITTED` | `observe_statement` | `COMMITTED` | 그 다음 명세서 |
| `COMMITTED` | `distribute` | `COMMITTED` | `apply_distribution` |
| `CAPTURED`, `COMMITTED` | `bind_refund` | 유지 | `bind_refund` |
| `CAPTURED`, `COMMITTED` | `observe_mock_cancel_acceptance` | 유지 | 목 취소 수락 |
| 있는 건 | `reconcile` | 유지 | 없음. 재생 비교만 |
| 아무 단계 | `reject_external` | 유지 | 없음. 항상 거절 |

`commit`은 한 번이다. 다음 명세서는 `observe_statement`다.
`distribute`는 `COMMITTED`에서만 된다. 현금 0인 순서 고정은 장부를 직접 부를 때의 술어로 남아 있고, 이 기계의 수락 경로에는 없다.
부분 환불의 배정 정지, 전액 1회 재분류, 액면을 몰래 줄이지 않는 규칙은 §4·§5 그대로다.

### 9.3 멱등키

멱등키는 길이 1..100인 문자열이다. 형식 실패는 `INVALID_ID`이고, 그 호출은 키를 잡지 않는다.

키는 `(op, settlement_id, 인자)`의 정규 JSON에 묶인다.

- 같은 키와 같은 정규 인자로 이미 수락된 명령은 `duplicate: true`, `applied: null`과 함께 처음 응답 스냅샷을 돌려준다. 경제 효과는 한 번이다.
- 같은 키와 같은 정규 인자로 이미 거절된 명령은 같은 오류를 다시 낸다. 장부와 단계는 그대로다.
- 같은 키와 다른 정규 인자는 `IDEMPOTENCY_CONFLICT`다.
- 다른 키로 이미 끝난 일회 전이를 다시 하면 `ILLEGAL_TRANSITION` 또는 `TERMINAL_IMMUTABLE`이다.
- 거절된 성립 명령은 그 프로세스의 키 표에만 남는다. 저널에는 들어가지 않는다.
- `distribute`의 `order`가 list가 아니면 키를 잡기 전에 `DISTRIBUTION_ORDER_TYPE`이다.

살아있는 프로세스에서 거절된 키로 본문만 고쳐 다시 내면 충돌이다. 고친 본문은 새 키가 필요하다.
프로세스 저널을 `restore`한 뒤에는 거절이 없으므로, 저널에 없던 키는 비어 있다.

### 9.4 재생

수락된 명령만 `export_journal`에 쌓인다.
`SettlementMachine.restore(journal)`은 빈 기계에 그 명령을 다시 적용한다.
같은 저널이면 `canonical_state`가 같고, `state_digest`도 같다.

수락 뒤에 응답을 잃어도, 복원한 기계에 같은 키와 같은 인자를 다시 내면 duplicate이고 금액은 한 번이다.
거절된 명령은 저널에 없으므로 복원 결과에 포함되지 않는다. 틀린 명세서를 낸 뒤의 단계는 그 호출 전과 같다.

`reconcile`은 현재 저널을 재생해 현재 상태와 비교한다.
같으면 `matched: true`다. 다르면 `MOCK_INVARIANT`다.
영수증은 경제 저널에 넣지 않는다. 같은 프로세스에서 같은 키는 duplicate다.
`restore`는 영수증을 복원하지 않는다. 복원 뒤 같은 키의 `reconcile`은 새 확인이고, digest는 같다.

이 재생은 메모리 안의 결정론이다. 디스크 원장, 은행 재시도, 체인 재생이 아니다.

### 9.5 외부 결제 경계

`reject_external(kind)`는 라벨 형식이 맞으면 `EXTERNAL_PAYMENT_UNSUPPORTED`다.
PG 승인·매입·취소, 은행 출금, 지급, 웹훅을 호출하지 않고, 그 이름으로 분기도 하지 않는다.
단계와 저널은 그대로다.

`authorize` 뒤에도 `provider_authorization_executed`는 거짓이다.
수락된 전이 뒤에도 `funds_executed`, `bank_debit_observed`, `external_return_closed`, `legal_debtor_bound`, `admission_granted`, `right_cancelled`, `durable`은 거짓이다.
`external_payment`는 `UNSUPPORTED`다. `provenance`는 `MOCK_SETTLEMENT_ONLY`다.

### 9.6 직접 장부 호출

`MockSettlement`를 직접 부르면 이 단계 게이트를 지나지 않는다.
그 경로는 산술 픽스처이고, F04가 읽는 액면 스냅샷의 출처로 남아 있다.
initiate부터 reconcile까지의 수락 기준은 `SettlementMachine`이다.
