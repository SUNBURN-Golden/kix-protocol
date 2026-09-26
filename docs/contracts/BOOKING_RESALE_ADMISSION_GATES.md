# 예매·리셀·검표 게이트 — 목 계약

Task 005 Wave 4. 문서일: 2026-09-26.
구현 기준 `origin/main`: `9e2dad654d7c6e46efade803018ef3e2cfea5e0a`.
이 문서는 오프라인 목(mock)이 지킬 술어와, 아직 정하지 않은 간극을 적는다.
`docs/status/ORIGINAL_32_STATUS.md`의 B01–B05, R01–R05, P03 라벨은 **설계중** 그대로다.
이 계약은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.

2026-09-26 reservation/ticketing depth가 §9의 수락 상태 기계를 앞에 둔다.
그 세션에서 확인한 `origin/main`은 `85145eb33799a7c712890ff81708def8a7d61ee5`다.
Wave 4 목 술어와 그 기준 SHA는 그대로다. B01–B05, R01–R05, P03 라벨도 그대로다.

2026-09-26 resale depth가 §10의 수락 상태 기계를 앞에 둔다.
그 세션에서 확인한 `origin/main`은 `a47828dd4517c5a7397e09eb6b563a64e4265c82`다.
Wave 4 목과 §9 예약 기계는 그대로다. R01–R05는 **설계중**이다.

2026-09-26 admission depth가 §11의 수락 상태 기계를 앞에 둔다.
그 세션에서 확인한 `origin/main`은 `5c59d95ec52379e010f8e9c660da11cfa6498def`다.
Wave 4 목, §9 예약 기계, §10 리셀 기계는 그대로다. B01–B05, R01–R05, P03은 **설계중**이다.
`protocol_contract.json`과 OpenAPI 카탈로그는 그대로다.

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
| 수락 상태 | 재고 점유, 만료 뒤의 명시적 해제, 확정·취소, 발행, 1회 검표, 멱등키, 저널 재생, 미커밋 정산에 대한 최종성 거부 | 라이브 입장, 내구 예약, 자금 최종성, 리셀·여신 확장 |

게이트 술어 파일은 `reference/booking_resale_admission/mock_gates.py`다.
예약 수락 상태 기계는 `reference/booking_resale_admission/reservation_fsm.py`다. §9.
리셀 수락 상태 기계는 `reference/booking_resale_admission/resale_fsm.py`다. §10.
검표 자격 수락 상태 기계는 `reference/booking_resale_admission/admission_fsm.py`다. §11.
리셀 명령은 예약 기계에 넣지 않는다. 검표 기계의 명령도 예약 기계와 리셀 기계에 더하지 않는다.
실행 방법과 비청구는 [validation/2026-09-26-wave4-booking-resale-admission/README.md](../../validation/2026-09-26-wave4-booking-resale-admission/README.md)에 있다.
`mock_gates.py`는 네트워크, 파일, PG, 은행, 커널, Move, `zk_gate`, 정산 목을 호출하지 않는다.
§9의 기계도 네트워크, 파일, PG, 은행, 커널, Move, `zk_gate`를 호출하지 않는다. 정산은 주입된 기계의 `view`만 읽는다.
§10의 기계도 네트워크, 파일, PG, 은행, 커널, Move, `zk_gate`를 호출하지 않는다. 묶인 예약 기계와 정산 기계의 `view`만 읽는다. 정산 명령은 호출하지 않는다.
§11의 기계도 네트워크, 파일, PG, 은행, 커널, Move, `zk_gate`를 호출하지 않는다. 묶인 예약 기계의 허가·소비와, 예약·리셀·정산 기계의 `view`만 사용한다. 정산 명령은 호출하지 않는다. 외부 현장 신원과 회수 원천은 읽지 않는다.
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
- 이 상태 기계의 저널을 내구 원장, 체인 커밋먼트, 은행 exactly-once로 읽는 일
- 발행 성공을 경제 최종성이나 운영 검표로 읽는 일
- 리셀 리스팅, 이전, F04 여신을 이 기계의 명령으로 넣는 일

## 8. 비청구

이 문서와 목 시험의 통과는 B01–B05, R01–R05, P03이 구현되었다는 뜻이 아니다.
라벨은 설계중이다.
메모리 발행 증거는 체인 발행이 아니고, 주입된 결제 사실은 입금이 아니고, `CONSUMED_ONCE`는 운영 검표가 아니다.
`reference/v0.3-rc1`의 상거래 모형과 Move `rights`를 대체하지 않으며 그 파일을 수정하지 않는다.
§9의 `matched: true`는 이 프로세스 저널의 재생 일치다.
`economic_finality_claimed`는 발행이 성공해도 거짓이다.
`MOCK_COMMIT_OBSERVED`는 정산 목의 `COMMITTED`를 읽었다는 뜻이지 입금이 아니다.

## 9. 예약·발행 수락 상태 기계

Wave 4 목은 슬롯, 가격, 주입된 결제 사실, 검표 술어를 고정했다. 단계, 멱등키, 프로세스 저널은 없었다.
이 절의 기계가 그 앞에 선다. `mock_gates.py`는 그대로다. 기계가 그 함수를 호출하기 전에 전이를 거절하거나, 수락한 명령을 저널에 한 번 적는다.

B01–B05, R01–R05, P03은 **설계중**이다. 이 절이 그 라벨을 올리지 않는다.

이 기계는 `protocol_contract.json`에 명령을 넣지 않는다.
OpenAPI 카탈로그도 바꾸지 않는다. 새 프로토콜 명령이 필요하면 `DECISION_REQUIRED · Astra`다.
이 깊이는 그 명령을 요구하지 않는다. 수락 기준은 이 참조 모듈 안의 결정이다. 법적 권위, 체인 권위, 입장 권한이 아니다.
조회 라벨 `lifecycle_authority = IN_MEMORY_FSM`은 그 한계를 적는다.
`provenance`는 `MOCK_GATE_ONLY`다.

리셀 명령은 이 기계에 없다. `list_resale`, `cancel_listing`, `observe_resale_payment`, `accept_resale`, `hold_buy`, `release_hold`, `close`를 두지 않는다. 그 명령은 §10의 `ResaleMachine`에만 있다.
F04 여신 명령도 두지 않는다. `resale_allowed`는 공연 등록 술어의 필드일 뿐이고, 이 기계는 그 필드로 리스팅을 열지 않는다.
Wave 4 목을 직접 부르면 리셀 술어는 그 파일에 그대로 있다. 그 직접 호출은 이 단계 게이트를 지나지 않는다.

시계는 `set_clock`으로만 움직이고, 그 명령은 저널에 남는다. 벽시계를 읽지 않는다. 만료는 단계가 아니다.

### 9.1 단계

```text
(없음) --hold--> HELD --confirm--> CONFIRMED --observe_payment--> PAYMENT_NOTED --issue--> ISSUED
                  |                  |
                  | release          | cancel
                  v                  v
               RELEASED           CANCELLED

ISSUED --authorize_admission--> ADMISSION_AUTHORIZED --consume--> CONSUMED
```

`HELD`가 만료돼도 단계는 그대로다. 슬롯은 `RESERVED`로 남는다. `release`만 그 슬롯을 `FREE`로 돌린다.
`PAYMENT_NOTED`에서 시계가 예약을 넘기면 `issue`는 `RESERVATION_EXPIRED`다. 단계는 `PAYMENT_NOTED`로 남고, 권리 id는 생기지 않는다.
`RELEASED`, `CANCELLED`, `CONSUMED`가 이 기계의 종결이다. 발행 뒤의 `cancel`은 종결로 가지 않고 거절된다.

`register_show`와 `set_clock`은 예약 단계가 아니다. 공연 재고와 주입 시계를 만든다.
`reconcile`과 `view`는 단계를 바꾸지 않는다. `reject_external`은 단계를 바꾸지 않고 거절만 한다.

### 9.2 전이

| 단계 | 명령 | 다음 단계 | 효과 |
|---|---|---|---|
| 없음 | `register_show` | 공연만 | 슬롯 `FREE`. 리셀 명령은 생기지 않음 |
| 없음 | `set_clock` | 시계 | 감소는 `CLOCK_REGRESSION` |
| 없음 | `hold` | `HELD` | 빈 슬롯 하나 `RESERVED`. 겹치면 `SLOT_OCCUPIED` |
| `HELD` | `release` | `RELEASED` | 주문이 없으면 만료 뒤에도 `FREE` |
| `HELD` | `confirm` | `CONFIRMED` | 주문. 만료면 `RESERVATION_EXPIRED`, 단계 유지 |
| `CONFIRMED` | `cancel` | `CANCELLED` | 결제 사실이 없을 때만 주문 중단. 슬롯 `FREE` |
| `CONFIRMED` | `observe_payment` | `PAYMENT_NOTED` | 주입된 32바이트 사실. 자금을 움직이지 않음 |
| `CONFIRMED`, `PAYMENT_NOTED` | `bind_settlement` | 유지 | 정산 id 기록만. 정산 명령은 호출하지 않음 |
| `PAYMENT_NOTED` | `issue` | `ISSUED` | 메모리 증거 `kind = 1`. 정산 게이트는 §9.5 |
| `ISSUED`, `ADMISSION_AUTHORIZED` | `authorize_admission` | `ADMISSION_AUTHORIZED` | 목 허가. 살아있는 허가가 있으면 `ADMISSION_LOCKED` |
| `CONSUMED` | `authorize_admission` | 유지 | 게이트의 `RIGHT_NOT_ACTIVE` |
| `ISSUED`, `ADMISSION_AUTHORIZED` | `consume` | `CONSUMED` | 1회 `CONSUMED_ONCE` |
| `CONSUMED` | `consume` | 유지 | `ALREADY_CONSUMED`. 버전을 다시 올리지 않음 |
| `PAYMENT_NOTED` | `cancel` | 유지 | `COMPENSATION_UNDEFINED`. 환불 레코드 없음 |
| `ISSUED`, `ADMISSION_AUTHORIZED`, `CONSUMED` | `cancel` | 유지 | `CANCEL_AFTER_ISSUE`. 슬롯은 `ISSUED` |
| `RELEASED`, `CANCELLED` | 변경 명령 | 유지 | `TERMINAL_IMMUTABLE` |
| 있는 예약 | `reconcile` | 유지 | 재생 비교만 |
| 아무 때 | `reject_external` | 유지 | `EXTERNAL_UNSUPPORTED` |

창, 가격, 결제 참조, 게이트 불일치는 `mock_gates.py`의 코드 그대로다. 이 기계가 그 코드를 다른 정책으로 바꾸지 않는다.
`release`는 `HELD`만 받는다. 발행 뒤에 `release`로 좌석을 되돌리지 않는다.
이미 주문이 있는 예약에 다른 주문을 붙이면 `RESERVATION_ALREADY_ORDERED`다.
이미 발행된 주문에 다른 `issuance_id`를 주면 `ORDER_ALREADY_ISSUED`다.

만료된 검표 허가 뒤에 새 `authorize_admission`이 성공하는 것은 Wave 4 목과 같다. 기계가 그 허가를 영구 잠금으로 바꾸지 않는다.
그 다음 `consume`도 한 번이다.

### 9.3 재고가 겹칠 때

점유 단계는 `HELD`, `CONFIRMED`, `PAYMENT_NOTED`, `ISSUED`, `ADMISSION_AUTHORIZED`, `CONSUMED`다.
`RELEASED`와 `CANCELLED`는 점유가 아니다.
한 공연의 한 슬롯에 점유 단계는 하나다. 두 번째 `hold`는 `SLOT_OCCUPIED`이고 저널에 들어가지 않는다.
만료만으로 점유가 풀리지 않으므로, 만료된 보유가 남아 있는 동안 다른 예약은 그 슬롯을 받지 못한다.

이 배타는 한 프로세스 안의 순차 명령이다. 스레드, 다른 실행자, 다른 채널의 현재성이 아니다.
`cross_channel_exclusive`는 거짓으로 남는다.

### 9.4 멱등키와 재생

멱등키는 길이 1..100인 문자열이다. 형식 실패는 `INVALID_ID`이고, 그 호출은 키를 잡지 않는다.
키는 `(op, subject_id, 인자)`의 정규 JSON에 묶인다.

- 같은 키와 같은 정규 인자로 이미 수락된 명령은 `duplicate: true`, `applied: null`과 함께 처음 응답 스냅샷을 돌려준다. 효과는 한 번이다.
- 그 스냅샷은 수락 시점의 응답이다. 그 뒤의 전이는 `view`가 현재다. 발행 뒤에 검표로 버전이 올라가도, 같은 발행 키의 재생 스냅샷 안 증거 `version`은 1로 남고, `view`의 권리 버전은 현재 값이다.
- 같은 키와 같은 정규 인자로 이미 거절된 명령은 같은 오류를 다시 낸다.
- 같은 키와 다른 정규 인자는 `IDEMPOTENCY_CONFLICT`다.
- 다른 키로 이미 있는 예약 id는, 바인딩이 같으면 `ILLEGAL_TRANSITION` 또는 종결이면 `TERMINAL_IMMUTABLE`이다. 바인딩이 다르면 `RESERVATION_BINDING_CONFLICT`다.
- `CONSUMED` 뒤의 다른 `consume` 키는 `ALREADY_CONSUMED`다.
- 거절된 명령은 저널에 들어가지 않는다. `restore`는 그 거절을 복원하지 않는다.

수락된 명령만 `export_journal`에 쌓인다.
`ReservationMachine.restore(journal, settlement_source)`는 빈 기계에 그 명령을 다시 적용한다.
같은 저널이고, 정산에 묶인 `issue`가 있으면 같은 정산 조회이면, `canonical_state`와 `state_digest`가 같다.

정산 게이트의 거절도 그 키에 남는다. 나중에 정산 목이 `COMMITTED`가 되어도 그 키는 저장된 거절을 다시 낸다. 발행은 새 키가 필요하다.
그 거절은 저널에 없으므로 `restore`가 되살리지 않는다.

`reconcile`은 현재 저널을 재생해 현재 상태와 비교한다. 같으면 `matched: true`다. 다르면 `MOCK_INVARIANT`다.
영수증은 저널에 넣지 않는다. `restore`는 영수증을 복원하지 않는다.
`state_digest`는 그 상태의 sha256이다. 서명이나 커밋먼트가 아니다.

이 재생은 메모리 안의 결정론이다. 디스크 원장, 은행 재시도, 체인 재생, 운영 검표 재생이 아니다.

정산 명령은 이 저널에 없다. `restore`는 주입된 정산 기계를 다시 실행하지 않고 `view`만 다시 읽는다.
묶인 `issue`를 재생하려면, 그 시점에 정산 조회가 `COMMITTED`이고 `gross`가 주문 금액과 같아야 한다.
정산 저널을 먼저 복원한 뒤에 예약 저널을 복원한다. 예약 저널이 정산 커밋을 얼려 두지는 않는다.

### 9.5 정산 게이트

`issue`는 경제 최종성을 주장하지 않는다. `economic_finality_claimed`를 참으로 만드는 인자는 없다.
성공, 거절, 재생의 봉투와 조회에서 그 필드는 거짓이다. `funds_executed`도 거짓이다.

`bind_settlement`은 예약에 정산 id만 적는다. `initiate`, `authorize`, `capture`, `commit`, `distribute`, `bind_refund`를 호출하지 않는다.
자금을 움직이지 않는다. 정산 기계의 `canonical_state`를 바꾸지 않는다.

정산 id가 없는 `issue`는 Wave 4와 같이 메모리 증거만 만든다.
`settlement_gate`는 `UNBOUND`이고, `mock_settlement_commit_observed`는 거짓이다.

정산 id가 있으면 `issue`는 그 조회의 다음을 모두 요구한다.

- `phase`가 `COMMITTED`
- `currency`가 `KRW`
- `gross`가 주문 금액과 같은 정수
- `funds_executed`, `admission_granted`, `bank_debit_observed`, `legal_debtor_bound`, `durable`, `external_return_closed`, `right_cancelled`가 모두 거짓

하나라도 아니면 권리 id는 생기지 않고 슬롯은 그대로다.

| 조회 | 코드 |
|---|---|
| 정산 원천이 없음 | `SETTLEMENT_SOURCE_REQUIRED` |
| id가 정산 기계에 없음 | `UNKNOWN_SETTLEMENT` |
| `phase`가 `COMMITTED`가 아님 | `SETTLEMENT_NOT_COMMITTED` |
| 통화 또는 `gross`가 주문과 다름 | `SETTLEMENT_AMOUNT_MISMATCH` |
| 위 최종성 플래그가 참 | `SETTLEMENT_VIEW_REJECTED` |
| 같은 예약에 다른 정산 id | `SETTLEMENT_BINDING_CONFLICT` |

통과해도 `economic_finality_claimed`는 거짓이다.
`mock_settlement_commit_observed`만 참이고, `settlement_gate`는 `MOCK_COMMIT_OBSERVED`다.
이 참은 목 단계가 `COMMITTED`였다는 관찰이다. 입금, 은행 확정, 체인 최종성, P04 종결이 아니다.
발행 증거는 `kind = 1`이고 `chain_issued`는 거짓이며 `seller_due`가 없다.
정산 조회의 `admission_granted`는 거짓으로 남는다. 검표는 정산 단계가 대신하지 않는다.

### 9.6 종결과 발행 뒤 취소

`RELEASED`와 `CANCELLED` 뒤의 변경 명령은 `TERMINAL_IMMUTABLE`이다. 같은 키의 재생만 처음 결과를 돌려준다.
`PAYMENT_NOTED`의 `cancel`은 `COMPENSATION_UNDEFINED`다. 보상, 환불, 재고 반환 레코드를 만들지 않는다.
`ISSUED` 이후의 `cancel`은 `CANCEL_AFTER_ISSUE`다. 슬롯은 `ISSUED`로 남고, 권리는 그대로다.
`CONSUMED` 뒤의 다른 소비는 `ALREADY_CONSUMED`다. 버전은 한 번만 오른다. 이 기계는 리셀로 버전을 올리지 않으므로, 소비 뒤 버전은 2다.
`reject_external`은 라벨 형식이 맞으면 `EXTERNAL_UNSUPPORTED`다. PG, 은행, 현장 장비, HTTP로 분기하지 않는다.

### 9.7 비청구

- 통과가 B01–B05, R01–R05, P03의 구현이나 설계확정이 아니다.
- `matched: true`는 이 프로세스의 저널과 조회가 같다는 뜻이다.
- `MOCK_COMMIT_OBSERVED`는 목 정산 단계의 관찰이다. 자금 집행이 아니다.
- `CONSUMED_ONCE`는 운영 검표가 아니다. `admission_routing_production`과 `private_proof_verified`는 거짓이다.
- 이 저널은 내구 원장, 체인 커밋먼트, 은행 exactly-once가 아니다.
- 직접 `MockGates` 호출은 이 단계 게이트를 지나지 않는 Wave 4 술어다. hold부터 consume까지의 수락 기준은 `ReservationMachine`이다.
- 리셀 리스팅과 이전의 수락 기준은 §10의 `ResaleMachine`이다. 이 기계의 명령이 아니다.

## 10. 리셀 수락 상태 기계

Wave 4 목은 리스팅, 주입된 리셀 결제 사실, 보유자 교체, 버전 +1을 고정했다. 단계, 멱등키, 프로세스 저널, 정산 조회와의 결합은 없었다.
이 절의 기계가 그 앞에 선다. `mock_gates.py`와 `reservation_fsm.py`는 그대로다. 리셀 기계가 목 함수를 호출하기 전에 전이를 거절하거나, 수락한 명령을 저널에 한 번 적는다.

R01–R05는 **설계중**이다. 이 절이 그 라벨을 올리지 않는다.

이 기계는 `protocol_contract.json`에 명령을 넣지 않는다.
OpenAPI 카탈로그도 바꾸지 않는다. 새 프로토콜 명령이 필요하면 `DECISION_REQUIRED · Astra`다.
이 깊이는 그 명령을 요구하지 않는다. 수락 기준은 이 참조 모듈 안의 결정이다. 법적 권위, 체인 권위, 마켓 권한, 입장 권한이 아니다.
조회 라벨 `lifecycle_authority = IN_MEMORY_FSM`은 그 한계를 적는다.
`provenance`는 `MOCK_GATE_ONLY`다.

예약 명령은 이 기계에 없다. `hold`, `confirm`, `issue`, `consume`을 두지 않는다.
F04 여신 명령도 두지 않는다.
발행된 권리를 이 기계에 들이는 명령은 `adopt_issued`다. 그것은 예약 단계가 아니라, 이미 발행된 메모리 권리를 리셀 술어가 읽을 수 있게 베끼는 선행이다.

시계는 `set_clock`으로만 움직이고, 그 명령은 저널에 남는다. 벽시계를 읽지 않는다. 만료는 단계가 아니다.

### 10.1 단계

```text
(발행된 ACTIVE 권리)
  adopt_issued --> ELIGIBLE
                     |
                     | list_resale
                     v
                  LISTED --hold_buy--> BUY_HELD
                     |                    |
                     | observe_resale_payment
                     v                    v
                  PAYMENT_NOTED -------> PAYMENT_NOTED
                     |
                     | accept_resale   (정산이 묶여 있으면 §10.5)
                     v
                 TRANSFERRED --close--> CLOSED

LISTED 또는 BUY_HELD --cancel_listing--> CANCELLED
BUY_HELD --release_hold--> LISTED
```

`hold_buy`는 생략할 수 있다. `LISTED`에서 `observe_resale_payment`로 바로 간다.
`CLOSED`와 `CANCELLED`가 이 리스팅의 종결이다. `TRANSFERRED`는 이전이 끝난 단계이고, `close` 뒤에야 종결이다.
만료돼도 단계는 그대로다. 만료된 리스팅은 살아 있는 잠금이 아니다.
`reconcile`과 `view`는 단계를 바꾸지 않는다. `reject_external`은 단계를 바꾸지 않고 거절만 한다.

### 10.2 전이

| 단계 | 명령 | 다음 단계 | 효과 |
|---|---|---|---|
| 없음 | `set_clock` | 시계 | 감소는 `CLOCK_REGRESSION` |
| 없음 | `adopt_issued` | 권리 `ELIGIBLE` | 메모리 발행 권리를 이 기계의 목에 한 번 만든다. `kind = 1`. 예약 기계를 호출하지 않음 |
| `ELIGIBLE` | `list_resale` | `LISTED` | 현재 보유자, 현재 버전, 권리당 살아 있는 리스팅 하나 |
| `LISTED` | `hold_buy` | `BUY_HELD` | 리스팅에 적힌 수신자만. 목 전송은 없음 |
| `BUY_HELD` | `release_hold` | `LISTED` | 구매 보류만 푼다. 리스팅은 열려 있음 |
| `LISTED`, `BUY_HELD` | `cancel_listing` | `CANCELLED` | 결제 사실이 없고 창 안일 때만. 판매자 라벨 |
| `LISTED`, `BUY_HELD` | `observe_resale_payment` | `PAYMENT_NOTED` | 주입된 32바이트 사실. 자금을 움직이지 않음 |
| `LISTED`, `BUY_HELD`, `PAYMENT_NOTED` | `bind_settlement` | 유지 | 정산 id 기록만. 정산 명령을 호출하지 않음 |
| `PAYMENT_NOTED` | `accept_resale` | `TRANSFERRED` | 보유자 교체, 버전 +1, 세대는 1. 정산 게이트는 §10.5 |
| `TRANSFERRED` | `close` | `CLOSED` | 그 리스팅 id의 종결. 권리를 지우지 않음 |
| `PAYMENT_NOTED` | `cancel_listing` | 유지 | `COMPENSATION_UNDEFINED` |
| `PAYMENT_NOTED` | `observe_resale_payment` | 유지 | `LISTING_PAYMENT_BOUND` |
| `BUY_HELD` | `hold_buy` | 유지 | `BUYER_HOLD_LOCKED` |
| `TRANSFERRED` | 같은 리스팅의 `list_resale` 또는 `accept_resale` | 유지 | `ILLEGAL_TRANSITION` 또는 `LISTING_BINDING_CONFLICT` |
| `CLOSED`, `CANCELLED` | 변경 명령 | 유지 | `TERMINAL_IMMUTABLE` |
| 있는 리스팅 | `reconcile` | 유지 | 재생 비교만 |
| 아무 때 | `reject_external` | 유지 | `EXTERNAL_UNSUPPORTED` |

창, 가격 상한, 수신자, 결제 참조, 보유자, 버전은 `mock_gates.py`의 코드 그대로다.
`LISTED`에서 `accept_resale`는 `ILLEGAL_TRANSITION`이다. 결제 사실을 이 기계가 먼저 적는다.
같은 리스팅 id는 `LISTED`로 돌아가지 않는다. 취소나 이전 뒤에 그 권리를 다시 내려면 새 리스팅 id다.
이전 뒤 새 리스팅은 새 보유자와 새 버전으로만 열린다. 권리 id와 세대는 바뀌지 않는다.

### 10.3 보유, 자격, 잠금, 낡은 리스팅

`list_resale`와 `accept_resale`는 판매자 라벨이 그 시점의 보유자 라벨과 같아야 한다. 아니면 `NOT_HOLDER`.
권리는 `ACTIVE`여야 한다. 소비된 권리는 `ALREADY_CONSUMED` 또는 `RIGHT_NOT_ACTIVE`다.
`resale_allowed`가 아니면 `RESALE_POLICY_REJECTED`. 수신자가 보유자와 같으면 `RECIPIENT_IS_HOLDER`. 금액이 `resale_cap`을 넘으면 `RESALE_CAP`.

살아 있는 리스팅은 권리당 하나다. 두 번째 리스팅은 `RIGHT_SALE_LOCKED`이고 저널에 들어가지 않는다.
만료된 리스팅은 살아 있는 잠금이 아니다. 그 리스팅의 결제나 이전은 `LISTING_NOT_OPEN`이다. 단계는 만료만으로 바뀌지 않는다.

낡은 리스팅은 다음으로 거절한다.

| 어긋남 | 코드 |
|---|---|
| 명령의 버전이 현재 권리 버전과 다름 | `STALE_VERSION` |
| 판매자 라벨이 현재 보유자와 다름 | `NOT_HOLDER` |
| 시계가 리스팅 만료를 넘음 | `LISTING_NOT_OPEN` |

묶인 예약 기계가 있으면 `accept_resale`는 그 조회를 다시 읽는다. 예약이 그 사이에 `CONSUMED`면 `ALREADY_CONSUMED`이고, 이 기계의 버전은 오르지 않는다.
이 재생은 예약 단계를 얼리지 않는다. 예약 저널을 먼저 그 시점의 상태로 복원한 뒤에 리셀 저널을 복원한다.

### 10.4 구매 보류와 한 프로세스 안의 순서

`hold_buy`는 선택이다. 리스팅의 `recipient_role`과 같은 라벨만 보류할 수 있다. 다른 라벨은 `RECIPIENT_MISMATCH`.
이미 보류 중이면 다른 보류 id는 `BUYER_HOLD_LOCKED`다.
`BUY_HELD`의 결제 명령은 그 보류 라벨과 같아야 한다. 아니면 `BUYER_MISMATCH`이고 결제 사실은 생기지 않는다.
보류가 없으면 결제 명령의 구매자 라벨은 없거나 수신자와 같아야 한다.

판매자 취소와 구매 보류는 이 프로세스가 명령을 적용한 순서로 결정된다.
취소가 먼저면 다음 보류는 `TERMINAL_IMMUTABLE`이다.
보류가 먼저고 결제 사실이 없으면 판매자 취소는 `CANCELLED`다.
결제 사실 뒤의 취소는 `COMPENSATION_UNDEFINED`다. 보상 레코드는 없다.

이 순서는 한 프로세스 안의 순차 명령이다. 스레드, 다른 실행자, 다른 채널의 현재성이 아니다.
`cross_channel_exclusive`는 거짓으로 남는다.

### 10.5 정산 게이트

`accept_resale`는 경제 최종성을 주장하지 않는다. `economic_finality_claimed`를 참으로 만드는 인자는 없다.
성공, 거절, 재생의 봉투와 조회에서 그 필드는 거짓이다. `funds_executed`도 거짓이다.
`venue_credential_reissued`도 거짓이다. 이전은 현장 자격 재발급이 아니다.

`bind_settlement`은 리스팅에 정산 id만 적는다. `initiate`, `authorize`, `capture`, `commit`, `distribute`, `bind_refund`를 호출하지 않는다.
자금을 움직이지 않는다. 정산 기계의 `canonical_state`를 바꾸지 않는다.
액면 `seller_due`는 목의 정수 나눗셈이다. 정산 장부에 넘기지 않는다.

정산 id가 없는 `accept_resale`는 Wave 4와 같이 메모리 보유자 교체만 한다.
`settlement_gate`는 `UNBOUND`이고, `mock_settlement_commit_observed`는 거짓이다.

정산 id가 있으면 `accept_resale`는 그 조회의 다음을 모두 요구한다.

- `phase`가 `COMMITTED`
- `currency`가 `KRW`
- `gross`가 리스팅 금액과 같은 정수
- `funds_executed`, `admission_granted`, `bank_debit_observed`, `legal_debtor_bound`, `durable`, `external_return_closed`, `right_cancelled`가 모두 거짓

하나라도 아니면 보유자와 버전은 그대로다.

| 조회 | 코드 |
|---|---|
| 정산 원천이 없음 | `SETTLEMENT_SOURCE_REQUIRED` |
| id가 정산 기계에 없음 | `UNKNOWN_SETTLEMENT` |
| `phase`가 `COMMITTED`가 아님 | `SETTLEMENT_NOT_COMMITTED` |
| 통화 또는 `gross`가 리스팅과 다름 | `SETTLEMENT_AMOUNT_MISMATCH` |
| 위 최종성 플래그가 참 | `SETTLEMENT_VIEW_REJECTED` |
| 같은 리스팅에 다른 정산 id | `SETTLEMENT_BINDING_CONFLICT` |

통과해도 `economic_finality_claimed`는 거짓이다.
`mock_settlement_commit_observed`만 참이고, `settlement_gate`는 `MOCK_COMMIT_OBSERVED`다.
이 참은 목 단계가 `COMMITTED`였다는 관찰이다. 입금, 은행 확정, 체인 최종성, 판매자 지급이 아니다.

거절된 이전 키는 그 거절을 다시 낸다. 나중에 정산 목이 `COMMITTED`가 되어도 그 키로 이전하지 않는다. 이전은 새 키가 필요하다.
그 거절은 저널에 없으므로 `restore`가 되살리지 않는다.
묶인 이전을 재생하려면, 그 시점에 정산 조회가 `COMMITTED`이고 `gross`가 리스팅 금액과 같아야 한다.

### 10.6 이전 뒤의 제시

`accept_resale`가 수락되면 보유자는 수신자로 바뀌고 `version`은 1 오르고 `generation`은 1로 남는다.
권리 id는 그대로다. 새 Right 객체를 만들지 않는다. 슬롯은 `ISSUED`로 남는다.
리스팅과 검표 허가는 권리에서 떨어진다. 리스팅 상태는 `ACCEPTED`로 목에 남고, 이 기계의 단계는 `TRANSFERRED`다.

`prior_presentation_valid`는 리스팅 시점의 보유자와 버전이 아직 현재 권리일 때만 참이다.
`TRANSFERRED`와 `CLOSED`에서는 거짓으로 남는다.
`view_presentation`의 `matches_current_right`는 버전이 같고, 보유자 라벨이 같고, 권리가 `ACTIVE`이고, 살아 있는 리스팅이 없을 때만 참이다.
살아 있는 리스팅이 붙어 있으면 그 제시는 현재 권리와 맞지 않는다. 이것은 운영 검표가 아니다.
`admission_routing_production`과 `venue_credential_reissued`는 거짓이다.

같은 `transfer_id`와 같은 바인딩의 재전송은 `duplicate: true`이고 버전을 다시 올리지 않는다.
다른 `transfer_id`로 같은 리스팅을 다시 받으면 `ILLEGAL_TRANSITION` 또는, 종결 뒤면 `TERMINAL_IMMUTABLE`이다.

### 10.7 멱등키와 재생

멱등키는 길이 1..100인 문자열이다. 형식 실패는 `INVALID_ID`이고, 그 호출은 키를 잡지 않는다.
키는 `(op, subject_id, 인자)`의 정규 JSON에 묶인다.

- 같은 키와 같은 정규 인자로 이미 수락된 명령은 `duplicate: true`, `applied: null`과 함께 처음 응답 스냅샷을 돌려준다. 효과는 한 번이다.
- 그 스냅샷은 수락 시점의 응답이다. 그 뒤의 전이는 `view`가 현재다.
- 같은 키와 같은 정규 인자로 이미 거절된 명령은 같은 오류를 다시 낸다.
- 같은 키와 다른 정규 인자는 `IDEMPOTENCY_CONFLICT`다.
- 거절된 명령은 저널에 들어가지 않는다. `restore`는 그 거절을 복원하지 않는다.

수락된 명령만 `export_journal`에 쌓인다.
`ResaleMachine.restore(journal, ticket_source, settlement_source)`는 빈 기계에 그 명령을 다시 적용한다.
같은 저널이고, 묶인 예약·정산 조회가 그 명령이 요구하는 상태이면, `canonical_state`와 `state_digest`가 같다.

`reconcile`은 현재 저널을 재생해 현재 상태와 비교한다. 같으면 `matched: true`다. 다르면 `MOCK_INVARIANT`다.
영수증은 저널에 넣지 않는다.
`state_digest`는 그 상태의 sha256이다. 서명이나 커밋먼트가 아니다.

이 재생은 메모리 안의 결정론이다. 디스크 원장, 은행 재시도, 체인 재생, 마켓 재생이 아니다.
정산 명령과 예약 명령은 이 저널에 없다. `restore`는 그 기계를 다시 실행하지 않고, 리셀 명령이 요구할 때 `view`만 다시 읽는다.

### 10.8 거절

이 기계가 목 코드에 더하는 코드는 다음이다.

| 코드 | 조건 |
|---|---|
| `TICKET_NOT_ISSUED` | 묶인 예약이 `ISSUED` 또는 `ADMISSION_AUTHORIZED`가 아님 |
| `TICKET_CANCELLED` | 묶인 예약이 `CANCELLED` |
| `TICKET_SOURCE_REQUIRED` | 예약 id가 있는데 예약 기계가 없음 |
| `ALREADY_CONSUMED` | 묶인 예약 또는 권리가 소비됨 |
| `ADMISSION_LOCKED` | 묶인 예약에 살아 있는 검표 허가가 있음 |
| `RECIPIENT_MISMATCH` | 보류 또는 결제 라벨이 리스팅 수신자가 아님 |
| `BUYER_HOLD_LOCKED` | 그 리스팅에 살아 있는 구매 보류가 있음 |
| `BUYER_MISMATCH` | 보류된 라벨과 다른 결제 |
| `UNKNOWN_HOLD` | 없는 보류 id |
| `HOLD_BINDING_CONFLICT` | 같은 보류 id, 다른 바인딩 |
| `ILLEGAL_TRANSITION` | 그 단계의 명령이 아님 |
| `TERMINAL_IMMUTABLE` | `CLOSED` 또는 `CANCELLED` 뒤의 변경 |
| `IDEMPOTENCY_CONFLICT` | 같은 키, 다른 정규 인자 |
| `EXTERNAL_UNSUPPORTED` | 마켓, HTTP, KYC, 현장 재발급, PG 라벨 |
| `INVALID_JOURNAL` | `restore`가 읽을 수 없는 저널 |
| `SETTLEMENT_SOURCE_REQUIRED` / `SETTLEMENT_NOT_COMMITTED` / `SETTLEMENT_AMOUNT_MISMATCH` / `SETTLEMENT_VIEW_REJECTED` / `SETTLEMENT_BINDING_CONFLICT` | §10.5 |

목의 `NOT_HOLDER`, `STALE_VERSION`, `RIGHT_NOT_ACTIVE`, `RESALE_POLICY_REJECTED`, `RIGHT_SALE_LOCKED`, `LISTING_NOT_OPEN`, `COMPENSATION_UNDEFINED`, `LISTING_PAYMENT_BOUND`는 §6 그대로다.

`reject_external`은 라벨 형식이 맞으면 `EXTERNAL_UNSUPPORTED`다. 마켓 전송, KYC, 현장 자격 재발급, PG, HTTP로 분기하지 않는다.

### 10.9 비청구

- 통과가 R01–R05의 구현이나 설계확정이 아니다. 라벨은 설계중이다.
- `matched: true`는 이 프로세스의 저널과 조회가 같다는 뜻이다.
- `MOCK_COMMIT_OBSERVED`는 목 정산 단계의 관찰이다. 자금 집행이나 판매자 지급이 아니다.
- `economic_finality_claimed`는 이전이 성공해도 거짓이다.
- `venue_credential_reissued`는 거짓이다. 버전 +1과 보유자 라벨 교체는 현장 자격 재발급이 아니고, 새 Right 객체가 아니다.
- `prior_presentation_valid`와 `matches_current_right`는 이 프로세스의 메모리 권리에 대한 비교다. 운영 검표가 아니다.
- 구매자 순서와 `RIGHT_SALE_LOCKED`는 한 프로세스 안의 배타다. `cross_channel_exclusive`는 거짓이다.
- 이 저널은 내구 원장, 체인 커밋먼트, 은행 exactly-once, 마켓 exactly-once가 아니다.
- 직접 `MockGates` 호출은 이 단계 게이트를 지나지 않는 Wave 4 술어다.
- 라이브 HTTP, 마켓 전송, KYC, 현장 장비, PG 청구, 여신, commerce-apps 변경은 없다.

## 11. 검표 자격 수락 상태 기계

Wave 4 목과 §9는 발행된 권리의 허가와 1회 소비를 고정했다. §10은 이전 뒤 옛 제시가 현재 권리와 맞지 않음을 고정했다.
이 절의 기계가 그 앞에 선다. `mock_gates.py`의 검표 술어는 그대로다. `reservation_fsm.py`와 `resale_fsm.py`에 명령을 더하지 않는다.
검표 기계가 목 함수를 호출하기 전에 신선도·외부 의존·정산 플래그를 거절하거나, 수락한 명령을 자기 저널에 한 번 적는다.

P03은 **설계중**이다. 이 절이 그 라벨을 올리지 않는다. B01–B05, R01–R05도 그대로다.

이 기계는 `protocol_contract.json`에 명령을 넣지 않는다.
OpenAPI 카탈로그도 바꾸지 않는다.

`DECISION_REQUIRED · Astra`: `authorize_admission`과 `consume`을 게시된 카탈로그 명령으로 올리는 일은 이 PR에서 멈추었다.
카탈로그에는 그 이름이 없다. 루프백은 그 액션을 `UNKNOWN_ACTION`으로 거절한다.
게시된 `admit`과 `open_admission`은 그대로다. 이 기계가 그 명령을 다시 정의하지 않는다.
없는 티켓의 `admit`은 로컬 `Core.execute`와 루프백이 같이 `TICKET_NOT_FOUND`다. 그것은 운영 검표가 아니다.

수락 기준은 이 참조 모듈 안의 결정이다. 법적 권위, 체인 권위, 현장 권한, 오프라인 신뢰가 아니다.
조회 라벨 `lifecycle_authority = IN_MEMORY_FSM`은 그 한계를 적는다.
`provenance`는 `MOCK_GATE_ONLY`다.
`admission_routing_production`, `offline_admission`, `venue_credential_reissued`는 거짓이다.
`external_admission`은 `UNSUPPORTED`다.

구현은 `reference/booking_resale_admission/admission_fsm.py`다.
시계는 `set_clock`으로만 움직이고, 그 명령은 저널에 남는다. 벽시계를 읽지 않는다.
묶인 예약 기계가 있으면 그 `set_clock`도 같은 시각으로 민다. 리셀 기계의 시계는 따로다.

### 11.1 단계

```text
(발행된 ACTIVE 권리, 버전 1)
  adopt_issued --> ELIGIBLE
                     |
                     | authorize_admission
                     v
                 AUTHORIZED --consume--> CONSUMED
```

`CONSUMED`가 이 자격의 종결이다. 만료는 단계가 아니다.
`AUTHORIZED`에서 허가가 만료되면 단계는 그대로고, 새 `admission_id`의 `authorize_admission`이 그 허가를 바꿀 수 있다. 그 다음 `consume`은 한 번이다.
`reconcile`, `view`, `view_credential`은 단계를 바꾸지 않는다. `reject_external`은 단계를 바꾸지 않고 거절만 한다.

묶인 예약이 있으면 수락된 허가와 소비는 예약 기계의 `authorize_admission` / `consume`에도 한 번 적용된다.
예약 단계는 `ISSUED`에서 `ADMISSION_AUTHORIZED`로, 그 다음 `CONSUMED`로 간다.
이 기계는 보유자를 바꾸거나 버전을 이전으로 올리지 않는다. 세대는 1이다.

### 11.2 전이

| 단계 | 명령 | 다음 단계 | 효과 |
|---|---|---|---|
| 없음 | `set_clock` | 시계 | 감소는 `CLOCK_REGRESSION`. 묶인 예약 시계도 같거나 이후로만 |
| 없음 | `adopt_issued` | `ELIGIBLE` | 발행 스냅샷을 이 기계의 목에 한 번 만든다. `kind = 1`. 예약이 묶여 있으면 그 조회가 `ISSUED`이고 버전이 1이어야 함 |
| `ELIGIBLE` | `authorize_admission` | `AUTHORIZED` | 현재 보유자, 현재 버전, 등록된 게이트. 창은 120_000ms |
| `AUTHORIZED` | `authorize_admission` | `AUTHORIZED` | 살아 있는 허가가 있으면 `ADMISSION_LOCKED`. 만료된 허가는 새 id로 교체 |
| `AUTHORIZED` | `consume` | `CONSUMED` | 1회 `CONSUMED_ONCE`. 버전 +1. 슬롯은 `ISSUED` |
| `ELIGIBLE` | `consume` | 유지 | `ADMISSION_REQUIRED` |
| `AUTHORIZED`가 만료 | `consume` | 유지 | `ADMISSION_EXPIRED`. 버전을 올리지 않음 |
| `CONSUMED` | `authorize_admission` | 유지 | `RIGHT_NOT_ACTIVE` |
| `CONSUMED` | `consume` | 유지 | `ALREADY_CONSUMED`. 버전을 다시 올리지 않음 |
| 있는 자격 | `reconcile` | 유지 | 재생 비교만. 묶인 원천을 다시 읽음 |
| 아무 때 | `reject_external` | 유지 | `EXTERNAL_UNSUPPORTED` |
| 아무 때 | `view` / `view_credential` | 유지 | 조회. `view_credential`의 `fresh`는 입장이 아님 |

창, 게이트, 요청, 버전, 1회 소비는 `mock_gates.py`의 코드 그대로다.
같은 `admission_id`의 다른 바인딩은 `ADMISSION_BINDING_CONFLICT` 또는, 같은 키면 `IDEMPOTENCY_CONFLICT`다.
같은 `consume_id`의 다른 바인딩은 `CONSUME_BINDING_CONFLICT`다.

### 11.3 신선도

허가와 소비 앞에 다음을 본다. 하나라도 아니면 예약 기계와 이 기계의 목을 소비로 바꾸지 않는다.

| 순서 | 어긋남 | 코드 |
|---|---|---|
| 1 | 현장 신원 원천이 붙어 있거나 의존이 `VENUE_IDENTITY` | `VENUE_SOURCE_UNAVAILABLE` |
| 2 | 회수 원천이 붙어 있거나 의존이 `REVOCATION` | `REVOCATION_SOURCE_UNAVAILABLE` |
| 3 | 그 밖의 외부 의존 | `EXTERNAL_UNSUPPORTED` |
| 4 | 묶인 소유 조회가 없거나 깨짐 | `OWNERSHIP_SOURCE_UNAVAILABLE` |
| 5 | 소유 권리가 이미 소비됨 | `ALREADY_CONSUMED` |
| 6 | 소유 버전이 제시와 다름 | `STALE_VERSION` |
| 7 | 소유 보유자 라벨이 제시와 다름 | `NOT_HOLDER` |
| 8 | 살아 있는 리스팅이 붙어 있음 | `LISTING_LOCKED` |
| 9 | 제시 비교가 현재 권리와 맞지 않음 | `CREDENTIAL_STALE` |
| 10 | 예약이 `CANCELLED` | `TICKET_CANCELLED` |
| 11 | 예약이 `CONSUMED` | 소비는 `ALREADY_CONSUMED`, 허가는 `RIGHT_NOT_ACTIVE` |
| 12 | 예약이 `ISSUED` 또는 `ADMISSION_AUTHORIZED`가 아님 | `TICKET_NOT_ISSUED` |
| 13 | 예약 권리의 버전 또는 보유자가 제시와 다름 | `STALE_VERSION`, 그 다음 `NOT_HOLDER` |
| 14 | 예약에 정산 id가 있는데 정산 원천이 없음 | `SETTLEMENT_SOURCE_REQUIRED` |
| 15 | 정산 조회의 최종성 플래그가 거짓이 아님. `admission_granted` 포함 | `SETTLEMENT_VIEW_REJECTED` |

소유 기계에 그 권리가 없으면 소유 기록은 없는 것이다. 그때는 예약 조회만 본다.
버전을 보유자보다 먼저 본다. §2와 같다.
외부 원천 객체는 읽지 않는다. `available`이 참인 것처럼 보여도 허용으로 쓰지 않는다. 오프라인 신뢰를 만들지 않는다.

정산 `COMMITTED`는 입장이 아니다. 검표 기계는 정산 명령을 호출하지 않고, 정산 기계의 `canonical_state`를 바꾸지 않는다.
`admission_granted`가 참이면 거절이다. 그 참을 입장으로 읽지 않는다.

### 11.4 순서

이 순서는 한 프로세스 안의 순차 명령이다. 스레드, 다른 실행자, 다른 채널의 현재성이 아니다.
`cross_channel_exclusive`는 거짓으로 남는다.
직접 `MockGates` 호출과, 이 기계를 거치지 않는 `ReservationMachine.authorize_admission` / `consume`은 이 신선도 게이트를 지나지 않는다.

| 먼저 | 다음 | 종결 |
|---|---|---|
| 리셀 `accept_resale` | 옛 보유자·버전 1의 허가 또는 소비 | `STALE_VERSION`. 예약은 `ISSUED`, 버전 1. 이 기계는 `ELIGIBLE` |
| 리셀 `accept_resale` | 새 보유자·버전 2의 허가 | `STALE_VERSION`. 현장 자격을 다시 발급하지 않음. `venue_credential_reissued`는 거짓 |
| `authorize_admission` | 리셀 `list_resale` | 리셀 `ADMISSION_LOCKED` |
| `consume` | 리셀 `list_resale` | 리셀 `ALREADY_CONSUMED`. 예약은 `CONSUMED`, 버전 2 |
| 살아 있는 `list_resale` | `authorize_admission` | `LISTING_LOCKED`. 예약은 `ISSUED` |
| `cancel_listing` | `authorize_admission` | `AUTHORIZED`. 취소된 리스팅은 자격을 지우지 않음 |
| 발행 전 `cancel` | `adopt_issued` | `TICKET_CANCELLED` |
| `PAYMENT_NOTED` | `adopt_issued` | `TICKET_NOT_ISSUED` |
| `issue` 뒤 `cancel` | 허가·소비 | 예약 취소는 `CANCEL_AFTER_ISSUE`. 자격은 남고, 입장은 계속 가능 |
| `consume` 뒤 `cancel` | 예약 `cancel` | `CANCEL_AFTER_ISSUE`. 단계는 `CONSUMED` |
| 첫 게이트 허가 | 다른 `admission_id` | `ADMISSION_LOCKED` |
| 첫 `consume` | 다른 `consume_id` | `ALREADY_CONSUMED`. 버전은 2에서 멈춤 |
| 같은 키·같은 바인딩 | 재전송 | `duplicate: true`. 효과를 다시 내지 않음 |
| 허가 만료 | `consume` | `ADMISSION_EXPIRED`. 버전은 1 |
| 허가 만료 | 새 `authorize_admission` | `AUTHORIZED`. 그 뒤 소비는 한 번 |
| 외부 의존 또는 `reject_external` | 허가·소비 | 거절. 저널에 들어가지 않음 |
| 저널 기록 뒤 소유가 이전 | `restore` / `reconcile` | `STALE_VERSION`. 맞은 재생으로 보고하지 않음 |

### 11.5 멱등키와 재생

멱등키는 길이 1..100인 문자열이다. 형식 실패는 `INVALID_ID`이고, 그 호출은 키를 잡지 않는다.
키는 `(op, subject_id, 인자)`의 정규 JSON에 묶인다.

- 같은 키와 같은 정규 인자로 이미 수락된 명령은 `duplicate: true`, `applied: null`과 함께 처음 응답 스냅샷을 돌려준다. 효과는 한 번이다.
- 그 스냅샷은 수락 시점의 응답이다. 그 뒤의 전이는 `view`가 현재다.
- 같은 키와 같은 정규 인자로 이미 거절된 명령은 같은 오류를 다시 낸다.
- 같은 키와 다른 정규 인자는 `IDEMPOTENCY_CONFLICT`다.
- 거절된 명령은 저널에 들어가지 않는다. `restore`는 그 거절을 복원하지 않는다.

수락된 명령만 `export_journal`에 쌓인다.
`AdmissionMachine.restore(journal, ticket_source, ownership_source, settlement_source)`는 빈 기계에 그 명령을 다시 적용한다.
같은 저널이고, 묶인 예약·소유·정산 조회가 그 명령이 요구하는 상태이면, `canonical_state`와 `state_digest`가 같다.
묶인 예약 저널은 허가·소비 없이 먼저 복원한다. 그 다음 이 저널을 재생하면 예약 허가와 소비가 다시 적용된다.
소유가 그 사이 이전되면 재생은 `STALE_VERSION`이고, 입장을 만들지 않는다.

`reconcile`은 현재 저널을 재생해 현재 로컬 상태와 비교한다. 같으면 `matched: true`다.
묶인 원천을 다시 읽으므로, 이후의 이전은 `matched` 대신 `STALE_VERSION`이다.
영수증은 저널에 넣지 않는다.
`state_digest`는 그 로컬 상태의 sha256이다. 서명이나 커밋먼트가 아니다.

이 재생은 메모리 안의 결정론이다. 디스크 원장, 은행 재시도, 체인 재생, 운영 검표 재생, 오프라인 입장이 아니다.

### 11.6 거절

이 기계가 목 코드에 더하는 코드는 다음이다.

| 코드 | 조건 |
|---|---|
| `TICKET_NOT_ISSUED` | 묶인 예약이 `ISSUED`가 아님. 재생 중 이미 허가·소비된 예약은 그 저널을 다시 적용할 때만 예외 |
| `TICKET_CANCELLED` | 묶인 예약이 `CANCELLED` |
| `TICKET_SOURCE_REQUIRED` | 예약 id가 있는데 예약 기계가 없음 |
| `TICKET_SOURCE_UNAVAILABLE` | 예약 조회가 깨짐 |
| `CREDENTIAL_STALE` | 버전·보유자·리스팅은 맞는데 제시 비교가 현재 권리가 아님 |
| `VENUE_SOURCE_UNAVAILABLE` | 현장 신원 원천이 필요하거나 붙어 있음. 읽지 않음 |
| `REVOCATION_SOURCE_UNAVAILABLE` | 회수 원천이 필요하거나 붙어 있음. 읽지 않음 |
| `OWNERSHIP_SOURCE_UNAVAILABLE` | 소유 조회가 깨짐. 그때 허용으로 넘기지 않음 |
| `SETTLEMENT_SOURCE_REQUIRED` | 예약에 정산 id가 있는데 정산 기계가 없음 |
| `SETTLEMENT_SOURCE_UNAVAILABLE` | 정산 조회가 깨짐 |
| `SETTLEMENT_VIEW_REJECTED` | 최종성 플래그가 거짓이 아님. `admission_granted` 포함 |
| `ILLEGAL_TRANSITION` | 같은 자격·허가 id를 다른 효과로 다시 적용 |
| `IDEMPOTENCY_CONFLICT` | 같은 키, 다른 정규 인자 |
| `EXTERNAL_UNSUPPORTED` | 스캐너, 오프라인 입장, 공개 바인드, 그 밖의 외부 라벨 |
| `INVALID_JOURNAL` | `restore`가 읽을 수 없는 저널 |

목의 `NOT_HOLDER`, `STALE_VERSION`, `ADMISSION_LOCKED`, `LISTING_LOCKED`, `ADMISSION_REQUIRED`, `ADMISSION_EXPIRED`, `ALREADY_CONSUMED`, `RIGHT_NOT_ACTIVE`, `GATE_MISMATCH`, `ADMISSION_REQUEST_MISMATCH`는 §6 그대로다.

### 11.7 비청구

- 통과가 B01–B05, R01–R05, P03의 구현이나 설계확정이 아니다. 라벨은 설계중이다.
- `matched: true`는 이 프로세스의 저널과 로컬 조회가 같고, 재생 시점의 묶인 원천이 그 명령을 다시 받아들였다는 뜻이다.
- `CONSUMED_ONCE`는 운영 검표가 아니다. `admission_routing_production`과 `private_proof_verified`는 거짓이다.
- `offline_admission`은 거짓이다. 외부 현장 신원이나 회수 원천의 부재를 마지막 허용으로 바꾸지 않는다.
- `venue_credential_reissued`는 거짓이다. 이전 뒤의 새 보유자·버전은 이 기계의 입장 자격이 아니다.
- 정산 `COMMITTED`와 `admission_granted: false`의 관찰은 입금이나 입장이 아니다. 정산 장부는 이 기계가 바꾸지 않는다.
- 스캐너 순서는 한 프로세스의 순차 명령이다. `cross_channel_exclusive`는 거짓이다.
- 이 저널은 내구 원장, 체인 커밋먼트, 은행 exactly-once, 현장 exactly-once가 아니다.
- 직접 `MockGates` 호출과 예약 기계에 바로 넣은 허가·소비는 이 신선도 게이트를 지나지 않는다.
- 라이브 HTTP에 이 기계의 명령을 올리지 않았다. 공개 엔드포인트, 현장 장비, 운영 자격 발급·회수, PG, KYC, commerce-apps 변경은 없다.
- 카탈로그에 `authorize_admission` / `consume_admission`을 넣는 일은 `DECISION_REQUIRED · Astra`로 멈춰 있다.
