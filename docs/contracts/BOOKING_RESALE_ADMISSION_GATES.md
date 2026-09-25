# 예매·리셀·검표 게이트 — 목 계약

Task 005 Wave 4. 문서일: 2026-09-26.
구현 기준 `origin/main`: `9e2dad654d7c6e46efade803018ef3e2cfea5e0a`.
이 문서는 오프라인 목(mock)이 지킬 술어와, 아직 정하지 않은 간극을 적는다.
`docs/status/ORIGINAL_32_STATUS.md`의 B01–B05, R01–R05, P03 라벨은 **설계중** 그대로다.
이 계약은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.

현행 승인 범위의 정본은 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md)다.
[PROTOCOL_MASTERPLAN_V2.md](../PROTOCOL_MASTERPLAN_V2.md)는 역사 계획이다.
아래 수치는 그 계획을 제품 규칙으로 다시 정한 것이 아니라, 이미 저장소에 있는
`kix::rights`와 역사 `lifecycle.py` 술어 중 목이 베끼는 것과 베끼지 않는 것을 고정한다.

## 0. 이 웨이브가 하는 일

모델 1의 문장 그대로, 예약 확정과 결제 확인과 체인 권리 발행 완료는 서로 다르다.
체인 기록이 은행 자금·계약상 채무·공연 이행을 보증하지 않는다.
이 목은 그 세 단계를 한 호출로 합치지 않는다.

| 행 | 목에서 고정하는 것 | 고정하지 않는 것 |
|---|---|---|
| B01 공연 등록 | 용량 1..16, 비어 있지 않은 게이트 역할, bps 합 상한, 슬롯 0..capacity-1 | 주최자 인증, 내구 ShowConfig |
| B02 좌석·재고 | 한 슬롯에 예약 하나. 주문 전에는 해제 가능. 발행 뒤 점유 유지 | 체인 grant, 회수, 내구 예약 |
| B03 가격 | 주문 금액은 등록 `primary_price`와 같다. `quote_ref`는 불투명 문자열 | 할인 계산, 견적 승인, `commerce.py` 재계산 |
| B04 주문·결제 | 주문과 주입된 32바이트 결제 사실을 분리. 같은 사실의 재전송은 한 번 | 영속 Order/Payment, 라이브 PG, 은행 자금 |
| B05 예매 확정 | 예약·주문·결제 사실이 맞을 때만 메모리 발행 증거 `kind = 1` | 구매자 증거 가용성, 체인 발행 최종성 |
| R01 재판매 등록 | 현재 보유자·현재 버전·권리당 살아있는 리스팅 하나 | 판매자 인증 |
| R02 양도 규칙 | 수신자 ≠ 보유자, 금액 ≤ `resale_cap`, `resale_allowed`, 창 900000ms | 그 밖의 자격·제한 정책 |
| R03 2차 결제 | 리스팅 금액과 같은 주입 사실. 만료·미지급이면 이전하지 않음 | 실패 보상, 판매자 지급, 정산 목 연동 |
| R04 소유권 이전 | 메모리 보유자 교체, 버전 +1, Move와 같은 정수 액면 | 체인 현재 소유, 새 Right 객체 |
| R05 중복 판매 | 이 프로세스 안에서 리스팅·검표 허가·결제 참조·버전이 서로 막힘 | 다른 실행자·채널의 배타성·현재성 |
| P03 검표 | 등록 게이트의 허가 뒤 1회 `CONSUMED`. 재소비 거절 | 운영 라우팅, 독립 현재성, `consume_private` 증명 |

실행 파일은 `reference/booking_resale_admission/mock_gates.py`다.
실행 방법과 비청구는 [validation/2026-09-26-wave4-booking-resale-admission/README.md](../../validation/2026-09-26-wave4-booking-resale-admission/README.md)에 있다.
네트워크, 파일, PG, 은행, 커널, Move, `zk_gate`, Wave 3 정산 목을 호출하지 않는다.
`reference/v0.3-rc1`은 수정하지 않는다.
프로세스 메모리 안의 결과이며 내구 원장이 아니다.
모든 응답에 `provenance = MOCK_GATE_ONLY`를 붙인다.

## 1. 공통 한계

역사 `reference/v0.3-rc1/common.py`의 정수 상한과 같다. 새 상품 한도가 아니다.

- 통화는 응답에 `KRW`만 적는다. 다른 통화를 받는 인자는 없다.
- 금액은 `bool`이 아닌 `int`다. 양수 금액은 `1 .. 10**12`. 실패 코드는 `INVALID_AMOUNT`.
- 식별자와 역할 라벨은 길이 1..100인 `str`이고, 앞뒤 공백을 허용하지 않는다. `bool`과 `str` 하위 클래스는 거절한다. 실패 코드는 `INVALID_ID`.
- 역할 문자열은 저장만 한다. 사람·주소·사업자·Sui address로 해석하지 않는다.
- 시각은 호출자가 `set_clock`으로 넣는 정수 밀리초다. 벽시계가 아니고, 역사 lifecycle의 초 단위 시계를 밀리초로 바꾸지 않는다. 감소는 `CLOCK_REGRESSION`. 상한 `10**15`은 입력 한계이지 시간 표준이 아니다.
- 결제 참조와 검표 요청은 소문자 16진 64글자다. 32바이트의 목 표현이며, 대문자는 다른 값으로 정규화하지 않고 거절한다. Move의 `vector<u8>` 길이 32에 대응시키는 자리지, 체인 인코딩 그 자체는 아니다.
- 같은 키의 재전송은 바인딩이 같으면 효과를 다시 내지 않는다(`duplicate: true`, `applied: null`). 그 사이의 상태 변화는 현재 조회로 보인다. 취소된 주문은 재전송으로 되살리지 않는다. 바인딩이 다르면 충돌이다. 창 검사는 첫 적용에만 하고, 이후 시계가 지나도 같은 바인딩의 재전송을 창 오류로 바꾸지 않는다.
- 다음 플래그는 항상 거짓이다. 성공한 호출이 참을 만들지 못한다.
  `role_authenticated`, `organizer_authenticated`, `chain_grant_current`, `durable`,
  `quote_policy_approved`, `discount_applied`, `provider_fact_live`, `funds_executed`,
  `buyer_evidence_available`, `chain_owner_current`, `cross_channel_exclusive`,
  `admission_routing_production`, `private_proof_verified`, `compensation_defined`.

## 2. 게이트 호출

HTTP 서버는 없다. 아래는 목 함수다. 조회 `view_show` / `view_right`는 상태를 바꾸지 않는다.

| 함수 | 필요한 것 |
|---|---|
| `set_clock(now_ms)` | 현재 이상인 정수 밀리초 |
| `register_show` | `show_id`, `organizer_role`, `capacity`, `gate_roles`, `primary_price`, `resale_cap`, `resale_allowed`, `organizer_bps`, `platform_bps` |
| `reserve_slot` | `reservation_id`, `show_id`, `slot`, `buyer_role`, `expires_ms` |
| `cancel_reservation` | `reservation_id` |
| `bind_order` | `order_id`, `reservation_id`, `amount`, 선택 `quote_ref` |
| `abort_order` | `order_id` |
| `observe_payment_fact` | `payment_ref`, `order_id`, `amount` |
| `issue` | `issuance_id`, `order_id` |
| `list_resale` | `listing_id`, `right_id`, `version`, `seller_role`, `recipient_role`, `amount`, `expires_ms` |
| `cancel_listing` | `listing_id`, `seller_role` |
| `observe_resale_payment` | `payment_ref`, `listing_id`, `amount` |
| `accept_resale` | `transfer_id`, `listing_id` |
| `authorize_admission` | `admission_id`, `right_id`, `version`, `holder_role`, `gate_role`, `request`, `expires_ms` |
| `consume_admission` | `consume_id`, `right_id`, `version`, `gate_role`, `request` |

`rights.move`의 `live`와 같이, 리스팅과 검표 허가에서는 버전을 보유자 라벨보다 먼저 본다.
맞는 버전이 아니면 `STALE_VERSION`이고, 그 다음에야 라벨이 다르면 `NOT_HOLDER`다.

## 3. B01–B05 — 예약, 주문, 발행 증거

`register_show`는 `kix::rights::create_show`의 다음만 가져온다.

- `capacity`는 1 이상 16 이하. 이 16은 Move 프로토타입 상한이지 상품 재고 상한이 아니다. 역사 lifecycle의 좌석 300은 여기 적용하지 않는다.
- `gate_roles`는 비어 있지 않은 역할 라벨 목록이다. 순서는 바인딩에 들어간다. 중복은 `GATES_DUPLICATE`.
- 목록 길이 상한 16은 Move가 게이트 개수에 둔 규칙이 아니다. 목이 입력 길이를 막으려고 용량 상한과 같게 둔 값이다.
- `organizer_bps`와 `platform_bps`는 각각 0..10000이고 합은 10000 이하다.
- 슬롯은 이름 없는 정수 `0 .. capacity-1`이다. lifecycle의 좌석 문자열 식별자는 만들지 않는다.
- 공연은 이 목에서 닫히지 않는다. `cancel_show`는 감싸지 않는다.

`primary_price`와 `resale_cap`은 역사 lifecycle이 양수 KRW로 요구하는 필드를 가져온 것이다.
Move `Show`에는 일차 가격이 없다. 0원 직접 발행(`kind = 0`)과 초대 발행은 이 목에 없다.
`resale_cap`이 0인 등록은 lifecycle의 `positive(resaleCap)`을 따라 `INVALID_AMOUNT`다.
Move `create_show`는 `resale_cap > 0`을 요구하지 않는다. 그 차이는 상품 최저가가 아니다.

`resale_allowed`는 lifecycle 정책의 bool이다. Move에는 같은 플래그가 없다. 생략하거나 정수가 오면 `POLICY_FLAG`.

예약 만료는 `now < expires_ms <= now + 900_000`이다.
900_000은 `rights::offer`의 창이다. 이 목에 따로 승인된 예약 TTL이 없어서 그 상수를 픽스처로 쓴다.
15분 상품 보유 시간이 아니고, lifecycle의 `reservationSeconds` 1..900(초)도 아니다.

`reserve_slot`은 빈 슬롯을 `RESERVED`로 둔다. 티켓을 만들지 않는다.
다른 예약이 그 슬롯을 잡으면 `SLOT_OCCUPIED`.
`cancel_reservation`은 주문이 없을 때만 슬롯을 `FREE`로 돌린다. 만료 뒤에도, 주문이 없으면 해제된다.
만료만으로 슬롯이 풀리지는 않는다.

`bind_order`는 살아있는 예약에만 붙는다.

- 금액이 `primary_price`와 다르면 `PRIMARY_PRICE_MISMATCH`. 할인을 빼서 맞추지 않는다.
- `quote_ref`가 있으면 식별자 형식의 문자열로 주문에 붙인다. 없으면 null이다.
- 이 문자열은 `reference/v0.3-rc1/commerce.py`를 다시 계산하지 않는다. `quote_policy_approved`는 거짓으로 남는다.
- 한 예약에 주문은 하나다.

`abort_order`는 결제 사실이 없을 때 주문과 예약을 취소하고 슬롯을 비운다.
결제 사실이 있으면 `COMPENSATION_UNDEFINED`. 환불 의무를 만들지 않는다.

`observe_payment_fact`는 호출자가 넣은 목 사실이다. 토스·PG·은행을 호출하지 않았고, 자금을 움직이지 않았다.
금액은 주문 금액과 같아야 한다. 참조는 그 공연의 `payment_facts` 안에서만 유일하다.
다른 공연의 같은 16진 문자열은 Move가 공연별 `payment_refs`를 보는 것과 같이 별도다.
이것은 채널을 넘는 중복 결제 방지가 아니다.

`issue`는 주문이 열려 있고, 결제 사실이 있고, 예약이 만료 전일 때만 발행 증거를 남긴다.

- 증거 `kind`는 1이다. Move `PAID`와 같은 숫자다. `kind = 0` 직접 발행은 하지 않는다.
- `generation`은 1, 발행 시점 `version`은 1, 보유자는 예약의 구매자 역할이다.
- 권리 id는 발행 id와 같다. Sui 객체 id가 아니다.
- 슬롯은 `ISSUED`로 남는다. 재고를 다시 열지 않는다.
- 일차 발행은 Move `issue_paid`처럼 분배 이벤트를 내지 않는다. 증거에 `seller_due`가 없다.
- 일차 수수료 bps는 적용하지 않는다. 그 분할은 Wave 3 정산 목의 일이고, 이 목은 그 모듈을 호출하지 않는다.
- 결제 사실 뒤에 시계가 예약을 넘기면 `RESERVATION_EXPIRED`다. 슬롯은 `RESERVED`로 남고, 권리 id는 생기지 않는다. 환불·보상·재고 반환 레코드를 만들지 않는다.

발행 증거는 만든 시점의 스냅샷이다. 이후 검표로 권리 버전이 올라가도 증거 안의 `version`은 1로 남는다.
그 스냅샷이 현재 권리의 증명은 아니다. `buyer_evidence_available`과 `chain_issued`는 거짓이다.

## 4. R01–R05 — 리스팅과 이전

`list_resale`는 상태가 `ACTIVE`인 권리만 받는다.

- 버전이 현재 권리 버전과 같아야 한다. 판매자 역할은 현재 보유자 라벨과 같아야 한다.
- `resale_allowed`가 아니면 `RESALE_POLICY_REJECTED`.
- 수신자가 보유자와 같으면 `RECIPIENT_IS_HOLDER`. 금액이 `resale_cap`을 넘으면 `RESALE_CAP`.
- 만료 창은 예약과 같은 900_000ms다. Move `offer`의 창을 그대로 쓴다. lifecycle 리스팅의 86400초는 가져오지 않는다.
- 살아있는 검표 허가가 있으면 `ADMISSION_LOCKED`. 살아있는 다른 리스팅이 있으면 `RIGHT_SALE_LOCKED`.
- 이미 만료된 검표 허가는 리스팅이 성공할 때 권리에서 떼어 낸다. Move `offer`가 만료된 admission을 지우는 쪽만 따른다. 살아있는 허가를 덮어쓰지는 않는다.

`cancel_listing`은 판매자 라벨이 같고, 리스팅이 살아 있고, 리셀 결제 사실이 없을 때만 된다.
결제 사실이 있으면 `COMPENSATION_UNDEFINED`.

`observe_resale_payment`의 금액은 리스팅 금액과 같아야 한다. 참조는 같은 공연의 일차 결제 사실과도 겹치면 `PAYMENT_BINDING_CONFLICT`다.

`accept_resale`는 리스팅이 살아 있고 결제 사실이 있고 버전과 보유자가 그대로일 때만 이전한다.

- 보유자 역할을 수신자로 바꾸고 `version`을 1 올린다. `generation`은 1로 남는다.
- 리스팅과 검표 허가를 권리에서 떼고, 리스팅 상태는 `ACCEPTED`다.
- 액면은 Move `accept_sale`의 정수 나눗셈이다.

```text
organizer_due = amount * organizer_bps // 10000
platform_due = amount * platform_bps // 10000
seller_due = amount - organizer_due - platform_due
```

이 세 수의 합은 `amount`다. 액면은 정산 목이 받는 현금이 아니고, 판매자 지급이 아니다.
`funds_executed`와 `chain_owner_current`는 거짓이다.
Wave 3 계약이 리셀 분할을 정산 정책으로 다시 정하지 않은 것과 같다. 이 목도 그 분배를 정산 호출로 넘기지 않는다.

만료된 리스팅은 결제 사실이 있어도 이전하지 않는다(`LISTING_NOT_OPEN`). 보상 레코드는 없다.

한 프로세스 안의 잠금(슬롯 하나, 리스팅 하나, 검표와 리스팅의 동시 불가, 공연 안 결제 참조 하나, 낡은 버전 거절)은 R05의 운영 배타성이 아니다.
`cross_channel_exclusive`는 거짓으로 남는다.

## 5. P03 — 검표 1회

`authorize_admission`은 현재 보유자 라벨과 현재 버전, 공연에 등록된 게이트 역할을 요구한다.
요청은 32바이트 목 표현이고, 만료는 `now < expires_ms <= now + 120_000`이다.
120_000은 `rights::authorize_admission`의 창이다. 상품 입장 시간이 아니다.
살아있는 리스팅이 있으면 `LISTING_LOCKED`. 살아있는 다른 검표 허가가 있으면 `ADMISSION_LOCKED`.
이미 만료된 리스팅 포인터는 허가가 성공할 때 떼어 낸다.

`consume_admission`은 다음 순서로 거절한다.

1. 권리가 이미 `CONSUMED`면 `ALREADY_CONSUMED`.
2. 버전이 다르면 `STALE_VERSION`.
3. 게이트 역할이 공연 목록에 없으면 `GATE_UNKNOWN`.
4. 붙어 있는 허가가 없으면 `ADMISSION_REQUIRED`.
5. 허가의 게이트·요청·버전이 다르면 `GATE_MISMATCH`, `ADMISSION_REQUEST_MISMATCH`, `STALE_VERSION`.
6. 그 다음에 시계가 만료를 넘었으면 `ADMISSION_EXPIRED`. 소비하지 않는다.

통과하면 상태를 `CONSUMED`로 두고 버전을 1 올리고 허가를 떼어 낸다.
결정 문자열은 `CONSUMED_ONCE`다. 역사 `core._admit`의 `ADMITTED_ONCE`를 호출한 것이 아니다.
두 번째 다른 `consume_id`는 `ALREADY_CONSUMED`다. 같은 `consume_id`의 같은 바인딩은 중복이고 버전을 다시 올리지 않는다.
슬롯은 `ISSUED`로 남는다. Move `consume`도 재고를 다시 열지 않는다.

이 경로는 공개 권리의 `authorize_admission` / `consume`만 흉내 낸다.
`zk_gate`와 `consume_private`는 호출하지 않는다. 증명을 검증하지 않는다.
`private_proof_verified`와 `admission_routing_production`은 거짓이다.
검표 성공이 정산 채권이나 관람 외의 자격을 만들지 않는다.

## 6. 오류 코드

| 코드 | 조건 |
|---|---|
| `INVALID_ID` | 식별자·역할·`quote_ref` 형식 |
| `INVALID_AMOUNT` | 금액 타입·범위. `bool`과 0 거절 |
| `VERSION_TYPE` | 버전이 0 이상의 `int`가 아님 |
| `CAPACITY` | 용량이 1..16의 `int`가 아님 |
| `GATES_TYPE` / `GATES_EMPTY` / `GATES_DUPLICATE` / `GATES_LIMIT` | 게이트 역할 목록 |
| `BPS` / `BPS_SUM` | 수수료 bps |
| `POLICY_FLAG` | `resale_allowed`가 bool이 아님 |
| `CLOCK` / `CLOCK_REGRESSION` | 주입 시각 |
| `SLOT` / `SLOT_OCCUPIED` | 슬롯 형식·점유 |
| `RESERVATION_WINDOW` / `LISTING_WINDOW` / `ADMISSION_WINDOW` | 각 창 밖이거나 시각 형식 오류 |
| `PAYMENT_REF` / `ADMISSION_REQUEST` | 소문자 16진 64글자가 아님 |
| `UNKNOWN_SHOW` / `UNKNOWN_RESERVATION` / `UNKNOWN_ORDER` / `UNKNOWN_RIGHT` / `UNKNOWN_LISTING` | 없는 키 |
| `SHOW_BINDING_CONFLICT` / `RESERVATION_BINDING_CONFLICT` / `ORDER_BINDING_CONFLICT` / `PAYMENT_BINDING_CONFLICT` / `ISSUANCE_BINDING_CONFLICT` / `LISTING_BINDING_CONFLICT` / `TRANSFER_BINDING_CONFLICT` / `ADMISSION_BINDING_CONFLICT` / `CONSUME_BINDING_CONFLICT` | 같은 키, 다른 바인딩 |
| `RESERVATION_NOT_OPEN` / `RESERVATION_EXPIRED` / `RESERVATION_ALREADY_ORDERED` | 예약 상태 |
| `ORDER_BOUND` / `ORDER_NOT_OPEN` / `ORDER_NOT_ABORTABLE` / `ORDER_ALREADY_ISSUED` / `ORDER_PAYMENT_BOUND` | 주문 상태 |
| `PRIMARY_PRICE_MISMATCH` / `PAYMENT_AMOUNT_MISMATCH` / `PAYMENT_FACT_REQUIRED` | 금액·사실 |
| `COMPENSATION_UNDEFINED` | 결제 사실이 있는 뒤의 취소·중단. 보상 규칙을 만들지 않음 |
| `NOT_HOLDER` / `STALE_VERSION` / `RIGHT_NOT_ACTIVE` | 보유자·버전·상태 |
| `RESALE_POLICY_REJECTED` / `RESALE_CAP` / `RECIPIENT_IS_HOLDER` | 리셀 정책 술어 |
| `RIGHT_SALE_LOCKED` / `LISTING_LOCKED` / `ADMISSION_LOCKED` | 한 프로세스 안의 배타 |
| `LISTING_NOT_OPEN` / `LISTING_PAYMENT_BOUND` / `RESALE_AMOUNT_MISMATCH` | 리스팅 결제·만료 |
| `GATE_UNKNOWN` / `GATE_MISMATCH` / `ADMISSION_REQUIRED` / `ADMISSION_EXPIRED` / `ADMISSION_REQUEST_MISMATCH` / `ALREADY_CONSUMED` | 검표 |

`MOCK_INVARIANT`는 목 내부 불변식이 깨진 구현 오류다. 호출자가 맞출 입력 거절이 아니다.

## 7. 의도적으로 비운 항목

다음에 값을 채워 넣지 않는다. 제품 정책이 필요하면 `DECISION_REQUIRED · Astra`다.

- 주최자·판매자·구매자·게이트의 인증과 권한 회수
- 체인 grant, durable ShowConfig, 지정석 이름, lifecycle 300석과의 단일 상한
- 승인된 예약 TTL. 900_000ms는 Move offer 상수의 픽스처다
- 할인, 쿠폰, 견적 재계산, 정책 버전 승인
- 라이브 PG, 결제 증명자(`payment_attesters`) 권한, 은행 자금, 웹훅
- 결제 사실 이후의 만료·실패에 대한 보상, 환불 의무, 재고 반환
- 구매자에게 발행 증거가 실제로 남는 경로, 체인 최종성
- 리셀 실패 보상, 판매자 지급, 정산 분개, F04 여신
- 다른 실행자·채널에 대한 현재성
- `consume_private` 증명, 운영 검표 라우팅, 위임 세션
- `refund`, `revoke`, `shield`, 증여, `cancel_show`. 세대는 1에서 올리지 않는다
- 커널 수명 상태. 이 목의 `CONSUMED`는 커널 전이가 아니다
- 내구성, 체인 최종성, 규제 준수, 제품 TPS, p99, 실패율
- 화면, 앱, 실자금

## 8. 비청구

이 문서와 목 시험의 통과는 B01–B05, R01–R05, P03이 구현되었다는 뜻이 아니다.
라벨은 설계중이다.
메모리 발행 증거는 체인 발행이 아니고, 주입된 결제 사실은 입금이 아니고, `CONSUMED_ONCE`는 운영 검표가 아니다.
`reference/v0.3-rc1`의 상거래 모형과 Move `rights`를 대체하지 않으며 그 파일을 수정하지 않는다.
