# 1차 발행 가격·수수료 — 초안 0.1

노드 `move-primary-price-fee` (이슈 #95). 문서일: 2026-10-08.
이 세션 시작에 확인한 `origin/main`과 작업 브랜치 `agent/kix-move-primary-price-fee`의 HEAD는 같다: `2ead88aec7f5fc36ed802c32c98f3053367c7ede`.
이 문서는 그 기준 위에 추가된 초안 0.1이다. 미래 커밋 SHA를 적지 않는다.
잠금 blob 둘은 그대로다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`.
`reference/v0.3-rc1/**`는 이 노드가 바꾸지 않는다. Move 소스, `zk_gate`, 16슬롯 참조 프로파일 시험도 그대로다.

이 초안은 구조·바인딩·산술·사건 의미만 계약으로 적는다. 가격 값, 수수료 bps 값, 수취인, 환불 시 수수료 반환, 수수료가 가격에 포함되는지, 온체인 집행 위치는 정하지 않는다.
`docs/status/ORIGINAL_32_STATUS.md`의 라벨은 그대로다. 이 초안은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.

현행 승인 범위의 정본은 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md)다. §12는 기존 shared-`Show` Move를 회귀 자산으로 둔다. §18은 16슬롯 참조 프로파일을 보존한다.
[PROGRAM_DECISIONS_20260928.md](../decisions/PROGRAM_DECISIONS_20260928.md) §6의 후보 「Move 1차 발행 가격·수수료 계약화」가 이 노드의 자리다. §2.1은 계약 문서와, 그 계약이 요구할 때의 `rights`·`zk_gate` localnet 확장을 승인 범위로 둔다. 이 초안은 계약 문서만 요구한다.
[PROGRAM_ROADMAP_20260930.md](../decisions/PROGRAM_ROADMAP_20260930.md)의 노드 행은 이 초안의 범위다. 운영 배포와 커널 잠금 변경은 승인되지 않는다.

비청구를 머리말에 둔다. 이 문서는 운영 준비, 실자금, 은행 잔액, 체인 확정, 법적 적합성을 주장하지 않는다. 증명자(attester)의 금액 주장은 은행 자금의 증거가 아니다. 이 노드에서 체인을 실행하지 않았다.

## 0. 범위와 상태

Wave 2 기록은 계약 미정의로 남긴 문장이다. Move `Show`에 1차 가격과 1차 수수료가 없고, 유료 발행은 증명자의 금액을 티켓에 저장하며 `Allocation`을 내지 않는다. 리셀의 `organizer_bps`·`platform_bps`는 거기에 적용되지 않는다. Python 모델의 `primaryPrice`·`primaryFeeBps`를 체인으로 복사하지 않았다 ([validation/2026-09-26-wave2-rights-issuance/README.md](../../validation/2026-09-26-wave2-rights-issuance/README.md) 24–30행). 그 기록은 역사 증거이며 이 노드가 고치지 않는다.

이 초안은 그 간극의 **구조**를 계약으로 닫는다. 상품 정책 값과 집행 위치를 채우면 간극이 값까지 닫힌다는 뜻이 아니다. 그 항목은 §6에 열린 채로 둔다.

이 문서를 소비하는 노드는 commerce `primary-price-fee-ui`, `settlement-policy-deepening`, `rs-1`, `read-model-reference`다.
`read-model-reference`가 읽는 목의 `primary_price`는 [READ_MODEL_QUERIES.md](READ_MODEL_QUERIES.md) §2.1·§2.2가 이미 적은 조회 키다. 이 초안은 그 조회 계약을 개정하지 않는다.
[RIGHTS_SCALE_PROFILE.md](RIGHTS_SCALE_PROFILE.md), [SETTLEMENT_DISTRIBUTION_F01_F03.md](SETTLEMENT_DISTRIBUTION_F01_F03.md), [BOOKING_RESALE_ADMISSION_GATES.md](BOOKING_RESALE_ADMISSION_GATES.md), [READ_MODEL_QUERIES.md](READ_MODEL_QUERIES.md)는 다른 노드의 계약이다. 이 초안은 그 파일을 바꾸지 않고 인용만 한다.

범위 밖이다. 새 coin/TIX 모듈, Sui testnet·mainnet, 실자금, 실 PG·은행·KYC, 공개 엔드포인트, R2, 자체 복제·합의·저장 엔진, `reference/v0.3-rc1/**` 수정, 잠금 blob 수정, CI 수정.

이 노드가 택한 인도 경계는 §4의 선택지 A다. 문서로 의미를 고정하고 Move는 그대로 둔다. A를 프로그램의 최종 집행 결정으로 확정하지는 않는다. 최종 선택은 §6의 `DECISION_REQUIRED · Astra`다.

## 1. 관측된 기준선

아래는 이 SHA에서 읽은 사실이다. 목표 술어(§3)와 섞지 않는다. 시험·어댑터가 넣은 금액은 정책 값이 아니다.

| 사실 | 출처 |
|---|---|
| `Show`에 1차 가격 필드와 1차 수수료 필드가 없다. 있는 경제 필드는 리셀 상한 `resale_cap`과 리셀 분할 `organizer_bps`, `platform_bps`다 | `reference/v0.3-rc1/sui/sources/rights.move:28-47` |
| `create_show`의 인자는 용량, 게이트, 결제 증명자, 리셀 상한, 두 bps, 검증자 ID다. 1차 가격·1차 수수료 인자가 없다 | `rights.move:93-94` |
| 생성 시 `organizer_bps`와 `platform_bps`는 각각 10000 이하이고 합도 10000 이하여야 한다. 이 검사는 리셀 필드의 검사다 | `rights.move:96` |
| 직접 발행 `issue`는 `kind` 0(`DIRECT`)이고 금액 0, 빈 `payment_ref`를 기록한다 | `rights.move:24`, `rights.move:150-155` |
| `attest_issuance`는 증명자가 주장한 금액을 `amount > 0`과 32바이트 `payment_ref`로만 검사하고, 슬롯을 예약한 뒤 `IssuancePayment`를 발행자에게 보낸다. `Ticket`을 만들지 않고 `Issuance`도 `Allocation`도 내지 않는다 | `rights.move:157-170` |
| `issue_paid`는 그 예약으로 같은 공개 `Ticket`을 만든다. `kind` 1(`PAID`)이고 금액은 증명자의 금액이다. 내는 사건은 `Issuance`와 `Change`다. `Allocation`은 없다 | `rights.move:25`, `rights.move:81-86`, `rights.move:137-148`, `rights.move:180-190` |
| `Allocation`은 `accept_sale`에서만 난다. 그때 `organizer_due`·`platform_due`는 리셀 금액에 `organizer_bps`·`platform_bps`를 u128로 곱해 10000으로 나눈 몫이다 | `rights.move:71-74`, `rights.move:232-242` |
| `cancel_issuance`는 예약을 버리고 슬롯을 비운다. 티켓을 만들지 않고 배분 사건을 내지 않는다 | `rights.move:171-179` |
| `refund`의 `RefundDutyRequested.amount`는 `last_amount`다. 유료 발행이면 그 값은 증명자가 저장한 금액이다 | `rights.move:258-263` |
| 오류 `EPayment`의 코드는 7이다. 현재 1차 경로는 금액이 0이거나 참조가 형식에 맞지 않을 때 이 코드로 중단한다. 공연에 고정된 1차 가격과의 일치는 검사하지 않는다 | `rights.move:17`, `rights.move:164`, `rights.move:188` |
| 이벤트 정책 키에 `primaryPrice`와 `primaryFeeBps`가 있다. `primaryFeeBps`는 0 이상 10000 이하 정수다. `policyHash`는 생성 때 한 번 기록된다 | `reference/v0.3-rc1/lifecycle.py:12-16`, `lifecycle.py:29` |
| 1차 거래 준비는 금액이 `primaryPrice`와 같아야 하고, 아니면 `PRIMARY_PRICE_MISMATCH`다 | `lifecycle.py:60-63` |
| 1차 커밋의 분할은 `fee = price * primaryFeeBps // 10000`이고, 주최자 줄은 `price - fee`, 플랫폼 줄은 `fee`다. 0원인 줄은 배분으로 만들지 않는다 | `reference/v0.3-rc1/core.py:155-165` |
| 양의 금액 한계는 `1 .. 10**12`이다. 실패 코드는 `INVALID_AMOUNT`다 | `reference/v0.3-rc1/common.py:24-25` |
| 예약 목의 `register_show`는 `primary_price`를 공연에 저장한다. `bind_order`는 주문 금액이 그 값과 같아야 하고, 아니면 `PRIMARY_PRICE_MISMATCH`다. 이 목에 1차 수수료 필드는 없다 | `reference/booking_resale_admission/mock_gates.py:14`, `mock_gates.py:57-58`, `mock_gates.py:113-172`, `mock_gates.py:261` |
| 정산 목의 1차 수수료 종류는 `PRIMARY_FEE_BPS`다. `fee_bps`는 0 이상 10000 이하이고, `fee = gross * fee_bps // 10000`, `residual = gross - fee`다. 0원 줄은 의무가 아니다. 두 액면의 합은 `gross`다 | `reference/settlement_f01_f03/mock_settlement.py:17-19`, `mock_settlement.py:56-82` |
| 그 돈 한계·bps 범위·바닥 나눗셈은 정산 계약 §1·§2다. 일반 잔여 단위의 우선순위는 §0.3에서 **UNDETERMINED**다. 목의 수수료 산술을 그 일반 정책으로 올리지 않는다 | [SETTLEMENT_DISTRIBUTION_F01_F03.md](SETTLEMENT_DISTRIBUTION_F01_F03.md) §1, §2, §0.3 |
| 확장 프로파일 `ShowControl`의 필드 목록에 1차 가격과 1차 수수료가 없다 | [RIGHTS_SCALE_PROFILE.md](RIGHTS_SCALE_PROFILE.md) 53행 |

`reference/v0.3-rc1/paid_integration.py:100`의 `primaryPrice=100000`, `primaryFeeBps=500`과 `reference/v0.3-rc1/client/paid-chain.mjs:24-25`의 같은 두 수는 로컬 어댑터 픽스처다. 상품 가격이나 상품 수수료가 아니다. `rights_tests.move`가 예약에 넣는 금액도 픽스처다. 이 초안은 그 수를 정책으로 인용하지 않는다.

Python 모델이 가격 일치를 검사한다고 해서 Move가 같은 검사를 한다는 뜻은 아니다. §1의 Move 행이 현재 체인 동작이다.

## 2. 용어

용어의 범위는 기존 목과 정산 계약에 이미 있는 범위다. 새 상품 한도가 아니다.

- `primary_price`. 공연 하나의 1차 발행 가격. 정수 KRW. `1 .. 10**12` (`common.py:24-25`, 정산 계약 §1). u64에 들어간다.
- `primary_fee_bps`. 그 공연의 1차 수수료. 정수 베이시스 포인트. `0 .. 10000` (`lifecycle.py:15-16`, 정산 계약 §2).
- 둘 다 공연 단위다. 슬롯마다, 등급마다 다른 가격은 이 초안이 정하지 않는다 (§6).
- 둘은 공연이 만들어지거나 봉인된 뒤 얼어 있다. 이는 생성 때 한 번 기록되는 `policyHash`(`lifecycle.py:29`)와 같은 자리다. 체인 위에 그 필드를 어느 객체에 둘지는 열려 있다 (§4, §6).
- 직접 발행(`Issuance.kind` 0)은 금액 0이다. 가격 일치와 수수료 분할의 바깥이다.
- 유료 발행(`Issuance.kind` 1)의 `amount`는 이 초안이 말하는 총액(gross)의 후보다. 현재 체인은 증명자가 주장한 값을 그대로 저장한다 (§1). 목표 바인딩은 §3의 PF-C01이다.
- 통화는 기존 1차 경로와 같이 `KRW`다. 다른 통화를 여기서 추가하지 않는다.

수수료를 가격 위에 더하는지, 가격 안에서 떼는지는 §6에 열린 상품 질문이다. 아래에 적는 산술은 그 질문을 닫지 않는다. 기존 목이 이미 하는 계산만 이름 붙인다. 그 계산은 지불된 총액 안에서 수수료를 바닥 나눗셈으로 떼고, 나머지를 잔여로 둔다 (`core.py:155-157`, 정산 계약 §2).

## 3. 술어

식별자 `PF-C01`부터는 이 초안의 제안 번호다. 카탈로그 명령이 아니다. 온체인 검사가 이미 있다는 뜻이 아니다. 집행 위치가 정해지기 전에는 §1의 Move가 이 술어를 구현하지 않는다.

### PF-C01 가격 바인딩

유료 1차 발행의 금액은 그 공연의 `primary_price`와 같다.
어긋나면 오프체인 목은 `PRIMARY_PRICE_MISMATCH`다 (`lifecycle.py:63`, `mock_gates.py:261`).
온체인에서 이 일치를 집행하게 되면 거절 코드는 기존 `EPayment`(7)다. 그 집행은 아직 없다 (§4).
직접 발행(kind 0)에는 이 술어를 적용하지 않는다.
예약(`attest_issuance`)만으로 금액을 가격과 맞았다고 확정하지 않는다. 현재 예약은 `amount > 0`만 본다.

### PF-C02 분할

지불된 총액 `amount`와 `primary_fee_bps`에 대해 다음이 성립한다.

```text
fee = amount × primary_fee_bps ÷ 10000
residual = amount − fee
```

나눗셈은 정수 바닥이다. 곱은 u128에서 한다. 이는 `accept_sale`이 리셀 금액에 쓰는 캐스팅과 같은 폭이다 (`rights.move:238-239`). `amount`의 상한 `10**12`와 bps 상한 10000의 곱은 `10**16`이라 u64에도 들어가나, 이 초안은 그 곱을 u128 바닥 나눗셈으로 적는다. 새 반올림이 아니다.
`fee + residual = amount`다.
`fee`가 0이면 수수료 의무 줄을 만들지 않는다. `residual`이 0이면 잔여 줄을 만들지 않는다 (`core.py:161-162`, `mock_settlement.py:73-82`, 정산 계약 §2).
이 산술은 정산 계약 §0.3이 말하는 일반 잔여 단위 우선순위가 아니다. 그 우선순위는 **UNDETERMINED**로 남는다. 담당은 정산 계약 §0.3 그대로다.
리셀 분할은 이 식에 넣지 않는다 (PF-C05).

### PF-C03 시점 (제안, Astra 대기)

현재 체인은 1차 발행에서 `Allocation`을 내지 않는다 (§1).
1차 배분 관찰을 새로 둘 경우, 그 관찰은 민트(`issue_paid`)에서만 난다. 예약(`attest_issuance`)과 `cancel_issuance`에서는 나지 않는다.
사건 또는 명령의 필드와 이름은 여기서 정하지 않는다. 새 프로토콜 표면이라 §6에서 `DECISION_REQUIRED · Astra`다. 이 절은 시점 제안이지 사건 스키마의 결정이 아니다.

### PF-C04 환불 연결

유료 발행이 민트된 뒤 `refund`가 내는 `RefundDutyRequested.amount`는 지불된 총액이다. 현재 구현은 `last_amount`를 그대로 싣는다 (`rights.move:262-263`).
수수료를 그 총액에서 빼서 돌려줄지, 총액을 그대로 환불 의무로 둘지는 정하지 않는다. `settlement-policy-deepening`이 정산 계약의 열린 환불 항목을 다룬다. 이 초안은 그 계약을 개정하지 않는다.
증명자의 금액이 환불 의무의 수로 실리더라도, 그 수는 은행이 돈을 받았다는 증거가 아니다.

### PF-C05 격리

리셀의 `organizer_bps`와 `platform_bps`는 `accept_sale`에만 남는다 (`rights.move:238-241`).
1차 수수료 `primary_fee_bps`와 더하거나 바꾸지 않는다. Wave 2 기록 28–29행과 같다.
정산 계약 §2가 리셀 분할을 `PRIMARY_FEE_BPS` 정책 밖에 두는 문장도 그대로다.

## 4. 집행 선택지

이 노드의 인도물은 선택지 A를 경계로 한 계약 문서다. B와 C는 Move를 바꾼다. 이 노드에서 하지 않는다.

| 선택지 | 내용 | 이 노드 |
|---|---|---|
| A | 오프체인 집행. 증명자와 정산 층이 가격 일치와 분할을 보고, 체인은 주장된 금액을 기록한다. 현재 `attest_issuance`·`issue_paid`와 같다 | 권장하는 잠정 경계. Move를 바꾸지 않는다. 프로그램의 최종 선택으로 확정하지는 않는다 |
| B | 확장 프로파일의 `ShowControl`에 가격·수수료 필드를 둔다. [RIGHTS_SCALE_PROFILE.md](RIGHTS_SCALE_PROFILE.md)는 `rs-1`이 소유한다. 그 문서의 53행 필드 목록에는 이 필드가 없다 | 다른 노드의 계약 개정. 여기서 수정하지 않는다 |
| C | `reference/v0.3-rc1/sui`의 `create_show`에 인자를 넣거나 그 트리에 파일을 추가한다. `rights_tests.move`가 `create_show`를 호출하므로 16슬롯 참조 시험이 그대로 통과하지 않는다. 개발계획 §18의 참조 프로파일 보존과 충돌한다 | 권장하지 않는다. 착수 전에 `DECISION_REQUIRED`다. 이 노드는 그 파일을 바꾸지 않는다 |

선택지 A에서도 증명자의 서명은 은행 대사가 아니다. 모델 1의 문장 그대로, 체인 기록이 은행 자금·계약상 채무·공연 이행을 보증하지 않는다 ([AUTHORITY_MODEL_1.md](../decisions/AUTHORITY_MODEL_1.md)).

## 5. 산술 예시

아래 수는 합성이다. 상품 가격도 상품 수수료도 아니다. `paid_integration.py`와 `paid-chain.mjs`의 100000·500을 쓰지 않는다.
식은 PF-C02다. `python3 -c`로 다시 계산했다.

| 총액 (KRW) | bps | fee | residual | 줄을 만드는 쪽 |
|---|---:|---:|---:|---|
| 999 | 333 | 33 | 966 | 둘 다 |
| 1 | 1 | 0 | 1 | 잔여만. 수수료 줄 없음 |
| 4 | 0 | 0 | 4 | 잔여만 |
| 4 | 10000 | 4 | 0 | 수수료만. 잔여 줄 없음 |

`999 * 333 // 10000 = 33`이고 `999 - 33 = 966`이다. 합은 999다.

## 6. 열린 항목

값을 채우지 않는다. 상품 정책 값과 새 프로토콜 표면은 `DECISION_REQUIRED · Astra`다. 법률·세무·회계·제공자 확인은 `UNDETERMINED`이고 담당을 이름 붙인다.

| 항목 | 상태 | 담당 |
|---|---|---|
| `primary_price`의 실제 값. 공연·등급·슬롯 중 어느 단위인지, 할인과 어떻게 만나는지 | `DECISION_REQUIRED · Astra` | Astra |
| `primary_fee_bps`의 실제 값 | `DECISION_REQUIRED · Astra` | Astra |
| 수수료 수취인과 역할. 역사 `core.py:157`은 고정 문자열 `"platform"`과 이벤트의 `organizer`다. 정산 목은 `fee_payee`·`residual_payee` 역할 라벨이다 (`mock_settlement.py:19`, `mock_settlement.py:62-64`). 체인에는 플랫폼 주소가 없다. 주소를 올리면 새 수취인 표면이다 | `DECISION_REQUIRED · Astra` | Astra |
| 환불 때 수수료를 돌려주는지. PF-C04는 총액만 연결한다 | `DECISION_REQUIRED · Astra` | Astra. 정산 쪽 후속은 `settlement-policy-deepening` |
| 수수료가 가격에 포함되는지, 가격 위에 더해지는지. PF-C02는 기존 목처럼 총액 안에서 떼는 산술만 이름 붙인다 | `DECISION_REQUIRED · Astra` | Astra |
| 집행 위치. §4의 A, B, C | `DECISION_REQUIRED · Astra` | Astra. B는 `rs-1`의 `RIGHTS_SCALE_PROFILE` 개정. C는 16슬롯 참조를 건드리므로 그 결정 뒤에만 착수한다 |
| 1차 배분 사건 또는 명령. PF-C03의 시점 제안은 스키마가 아니다 | `DECISION_REQUIRED · Astra` | Astra |
| 수수료의 법률·세무·회계 처리. 수수료에 대한 부가가치세, 수수료 부담 주체의 표시를 포함한다 | `UNDETERMINED — 사용자와 법률·회계 담당` | 사용자, 법률·회계 담당 |
| 토스 경로의 수수료 정산 동작 | `UNDETERMINED — 토스와 사용자` | 토스, 사용자 |

## 7. 기존 커버리지

AGENTS §7. 이 노드는 시험을 추가하지 않는다. 체인에 가격 일치·수수료 분할·1차 `Allocation`이 없고, 그 집행 위치는 §6에 열려 있다. 없는 온체인 동작을 시험으로 만들면 선택지 C로 기울어진다.

충분히 덮인 것. 인용만 한다.

- 직접 발행이 금액 0을 기록한다. `reference/v0.3-rc1/sui/tests/rights_tests.move:94-103` (`direct_issue_records_no_payment`).
- 유료 발행이 같은 공개 티켓을 구매자에게 만들고, 저장 금액은 증명자가 넘긴 금액이다. `rights_tests.move:105-117` (`paid_issuance_mints_the_same_ticket_to_the_buyer`).
- 예약 취소는 티켓을 만들지 않는다. `rights_tests.move:140-163` (`cancel_issuance_frees_the_slot_without_minting`).
- 유료 환불은 `last_amount`를 유지한 채 재고를 다음 세대에 연다. `rights_tests.move:165-183` (`paid_refund_frees_inventory_for_the_next_generation`).
- 1차 금액 0은 `EPayment`로 거절된다. `rights_tests.move:206-210` (`zero_primary_amount_is_rejected`).
- 그 밖의 1차 경로(증명자 권한, 예약된 슬롯의 직접 발행 금지, 참조 재사용, 닫힌 공연, 다른 공연의 cap·결제)는 `rights_tests.move:185-336`이다.
- 목의 가격 불일치는 `reference/booking_resale_admission/test_mock_gates.py:149`와 `reference/booking_resale_admission/test_reservation_fsm.py:189`의 `PRIMARY_PRICE_MISMATCH`다.
- 정산 목의 0 bps·10000 bps·바닥으로 수수료가 0이 되는 경우는 `reference/settlement_f01_f03/test_mock_settlement.py:92-120` (`test_f01_fee_floor_zero_fee_and_rejected_policies`)이다. 그 시험이 쓰는 금액과 500 bps는 픽스처다.

부분적으로 덮인 것.

- 오프체인 가격 일치와 바닥 분할은 위 목 시험이 본다. Move는 가격 일치를 보지 않는다. 같은 술어가 두 층에 같이 있다고 읽지 않는다.

덮이지 않은 것.

- 유료 발행 금액이 공연에 고정된 `primary_price`와 같은지. 체인에 그 필드가 없다.
- 1차 발행의 `primary_fee_bps` 분할. `issue_paid`는 분할을 계산하지 않는다.
- 민트 시점의 1차 배분 관찰. 사건이 없다. PF-C03은 제안이다.

## 8. 비청구

- 이 초안은 1차 가격과 1차 수수료의 상품 값을 정하지 않는다. §6의 열린 행을 값으로 읽지 않는다.
- 증명자의 `amount`는 은행 입금, PG 승인, 정산 완료가 아니다. Wave 2 기록 32행과 같다.
- `Issuance`는 대체 가능 코인도 현금도 아니다 (`rights.move:81-82`).
- 선택지 A는 이 노드가 Move를 건드리지 않는 경계다. 온체인 가격 검사가 생겼다는 뜻이 아니다.
- 16슬롯 참조 프로파일의 통과를 이 문서가 다시 측정하지 않는다. 그 경로는 CI의 `scripts/verify_runtime.py`가 `move-tests`로 돌린다. 이 노드의 작업 트리에서 그 명령은 돌리지 않았다. Sui localnet 여정도 돌리지 않았다.
- 체인 확정, 운영 준비, 내구성, 법적·세무 적합성을 주장하지 않는다.
- 정산 계약의 일반 잔여 우선순위, 토스 가맹, 조회 계약의 필드 목록을 이 초안이 개정하지 않는다.
