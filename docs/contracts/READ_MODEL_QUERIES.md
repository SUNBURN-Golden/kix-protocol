# 조회·목록 쿼리 — 초안 0.1

노드 `read-model-contract` (이슈 #100). 문서일: 2026-10-08.
이 세션에서 확인한 `origin/main`: `547d9fd5cd0e2d54e4fd61050d6f4fff530f3750`.
작업 트리 HEAD는 `7481b0e16ce9b903abbffa62249bb91cd9e63cfe`다. 그 커밋은 `origin/main`의 조상이고, 그 사이 15개 커밋은 이 문서가 인용하는 FSM, `protocol_contract.json`, 게이트 계약을 바꾸지 않는다.
이 문서는 초안 0.1이다. 와이어 본문과 카탈로그 삽입은 하지 않는다.
`docs/status/ORIGINAL_32_STATUS.md`의 B01–B05, R01–R05, P03, F01–F03, P04 라벨은 **설계중** 그대로다.
F04·E06도 **설계중** 그대로다. 이 초안은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.
조회 라벨 `lifecycle_authority = IN_MEMORY_FSM`은 그 한계를 적는다. 법적 권위, 체인 권위, 입장 권한이 아니다.

현행 승인 범위의 정본은 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md)다.
[BOOKING_RESALE_ADMISSION_GATES.md](BOOKING_RESALE_ADMISSION_GATES.md) §9, §10, §11은 새 프로토콜 명령을 `DECISION_REQUIRED · Astra`로 둔다.
그 질문은 이 노드에서 이미 답했다. 사용자 JunTae, 2026-10-08 13:32 KST, 선택지 A.
점 조회와 목록을 전용 카탈로그 조회 명령으로 둔다. 쓰기 본문을 재사용하지 않는다.
이름은 `list_shows`, `get_show`, `get_booking`, `list_bookings`, `get_right`, `get_presentation`, `list_open_listings`, `get_listing`, `get_admission`, `get_credential`, `get_settlement`, `get_credit_advance`, `get_credit_claim`이다.
`ReadObservationV1`의 `source_cut`, `projection_watermark`, `snapshot_digest`, `observed_receipt_refs`, `producer_manifest_digest`는 첫 봉투에 넣지 않는다. 소유는 `protocol-read-projection-evidence`다.
`get_credit_advance`와 `get_credit_claim`은 기존 `CreditMachine` view 키의 인용만이다. 금융 계좌, 분개, 의무, 익스포저, 대사, 수출 스키마는 넣지 않는다.
가시성 행렬의 값, `limit` 상한과 기본값, 커서 수명, 정렬 키, 열린 리스팅의 단계, 목록의 보존·이력 깊이는 `UNDETERMINED`다. 담당은 Astra.
법률·개인정보와 토스 MID·웹훅 사실도 `UNDETERMINED`다. 담당은 §9에 적는다.

## 0. 범위와 상태

이 문서는 상거래 표면이 필요로 하고 카탈로그에 없는 조회와 목록의 **의미**만 적는다.
구현, 공개 엔드포인트, 인증 스킴, OpenAPI, `protocol_contract.json`, SDK, 매니페스트, 루프백 게이트, 프로젝션 저장소는 범위 밖이다.
그 파일과 경로는 이 초안이 바꾸지 않는다. 와이어 본문, `operationId`, 오류 코드의 신규 이름, 카탈로그 삽입은 `read-model-reference`가 한다.
명령 이름은 머리말의 사용자 결정으로 정해져 있다. 이 문서가 카탈로그 바이트를 바꾸지는 않는다.

개발계획의 Track P는 조회가 상태를 바꾸지 않는다고 적는다.
로드맵 R-11(2)는 그 다음 노드 `read-model-reference`가, 승인된 조회를 참조 모듈과 카탈로그에 넣되 상태를 바꾸지 않는다고 적는다.
R-11(2)는 카탈로그 삽입의 자리이지, 이 초안이 카탈로그를 이미 고쳤다는 뜻이 아니다. 이름은 머리말의 사용자 결정이다.

이 초안을 소비하는 노드는 `read-model-reference`, commerce `bind-list-read`, 그리고 후속 `ps-02-query-contract`다.
`ps-02-query-contract`의 검색·델타·재생과 `fin-catalogue-read-model`의 금융 조회 스키마는 여기서 정의하지 않는다.
F04 점 조회 두 줄은 이 저장소에 이미 있는 `CreditMachine`의 `view`를 인용할 뿐이며, 금융 원장·수출·대사 스키마를 흡수하지 않는다.

`reference/v0.3-rc1/protocol_contract.json`의 `commands` 키는 이 SHA에서 40개다.
그 40개 안에 `list_*`, `get_*`, `view_*`, `read_*` 명령은 없다.
`observe_dispatch_lookup`은 그 40개 안의 쓰기 계열 이름이지 목록 조회가 아니다.
FSM의 `view*`는 식별자 하나의 점 조회이고, 카탈로그 액션이 그것을 노출하지 않는다.

### 0.1 이름 충돌과 명령 대체 금지

`reference/booking_resale_admission/mock_gates.py`와 `ResaleMachine.list_resale`는 **쓰기**다.
살아 있는 권리를 리스팅으로 받는다. 목록을 돌려주지 않는다.
카탈로그 키 `list_resale`는 없다. 가까운 카탈로그 쓰기는 `create_listing`, `cancel_listing`, `reserve_listing`이다.
상거래 쪽 이름 `listResale`와 이 쓰기를 한 명령으로 읽지 않는다.
목록 제안 이름은 `list_open_listings`다. 쓰기 명령의 이름을 재사용하지 않는다.

조회 쿼리를 기존 카탈로그 쓰기 본문에 대응시키지 않는다.
capability register가 금융 조회에 적은 command substitution 금지를 이 초안의 모든 쿼리에 같이 적용한다.
`settle_capture`, `offer_gift`, `create_listing`, `admit`을 포함한 기존 본문으로 조회를 대체하지 않는다.

### 0.2 관측된 간극 (계약 미정의)

`kix-commerce-apps`의 `packages/protocol-adapter/src/commerce-bindings.ts`는 이 작업 트리에 없다.
`listPerformances`, `getBooking`, `listResale`, `view*`의 시그니처는 노드 명세의 이름만 인용한다.
인수, 반환 필드, 호출 주체는 **UNVERIFIED**다.
AGENTS §8의 분류 B다. 없는 시그니처로 의미를 만들지 않았다.
아래 표의 commerce 메서드 열은 모두 그 한계를 가진다.

## 1. 쿼리 목록

이름은 사용자 결정의 조회 명령 이름이다. 쓰기 본문이 아니다. 카탈로그 상태는 전부 `NOT_IN_CATALOGUE`이며 `OWNER_DECIDED_OPTION_A`다. 이 40개 키 안에 아직 없다.

| 제안 이름 | 종류 | 뒷받침 | 카탈로그 | commerce 메서드 (UNVERIFIED) |
|---|---|---|---|---|
| `list_shows` | list | `NONE` (신규). 모집단은 `mock_gates.py`의 공연 레지스트리 | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `listPerformances` |
| `get_show` | point | `ReservationMachine.view_show` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view_show`에 대응하는 읽기 |
| `get_booking` | point | `ReservationMachine.view` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `getBooking` |
| `list_bookings` | list | `NONE` (신규). 모집단은 그 기계의 예약 케이스 | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | 보유자별 예약 목록 |
| `get_right` | point | `ResaleMachine.view_right` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view*` |
| `get_presentation` | point | `ResaleMachine.view_presentation` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view*` |
| `list_open_listings` | list | `NONE` (신규). 모집단은 `ResaleMachine`의 리스팅. 쓰기 `list_resale`가 아님 | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `listResale` |
| `get_listing` | point | `ResaleMachine.view` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view*` |
| `get_admission` | point | `AdmissionMachine.view` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view*` |
| `get_credential` | point | `AdmissionMachine.view_credential` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view*` |
| `get_settlement` | point | `SettlementMachine.view` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view*` |
| `get_credit_advance` | point | `CreditMachine.view` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view*` |
| `get_credit_claim` | point | `CreditMachine.view_claim` | NOT_IN_CATALOGUE; OWNER_DECIDED_OPTION_A | `view*` |

점 조회의 노출 필드는 해당 `_view`가 이미 만드는 dict의 키를 그대로 쓴다.
목록은 그 키의 **요약 부분집합**만 제안한다. 요약에 없는 키는 점 조회로만 간다.
부분집합의 경계(무엇이 요약인가)는 §6의 가시성 값과 함께 `UNDETERMINED`다. 담당은 Astra.
아래 추천 키는 최소 공개의 추천이지 결정이 아니다.

## 2. 쿼리별 명세

공통으로, 조회는 그 프로세스가 이미 수락한 상태만 비춘다. 자세한 일관성은 §4, 페이지는 §5, 가시성 값은 §6, 비증명 이유는 §7, 비변경 술어는 §8이다.
각 절의 "기계"는 그 응답이 읽은 기계다. 다른 기계의 dict가 중첩되면 키 이름으로 적고, 하나의 단계로 합치지 않는다.

### 2.1 `list_shows`

- **노출 상태.** 메서드는 없다. 모집단은 `MockGates._shows`다. 원소의 모양은 `MockGates._show_view`다.
  추천 요약 키: `show_id`, `currency`, `capacity`, `primary_price`, `resale_allowed`, `open`.
  점 조회에 남기는 키: `organizer_role`, `resale_cap`, `organizer_bps`, `platform_bps`, `gate_roles`, `slots`, `payment_ref_count`.
  `slots[].reservation_id`와 `payment_ref_count`는 요약에 넣지 않는 쪽을 추천한다.
- **행위자 가시성.** 클래스 `public listing`. 값과 추천은 §6. fixture 필터는 접근 통제가 아니다.
- **일관성.** 기계: 그 `MockGates` 인스턴스. `ReservationMachine`이 같은 게이트를 들고 있으면 시각은 그 기계의 `logical_time_ms`다. 두 저장소를 새로 만들지 않는다.
  반영하는 수락: 그 게이트에 이미 적용된 `register_show`. 거절된 등록과 멱등 재전송의 두 번째 효과는 없다.
- **페이지.** §5. 정렬 키는 미정이다.
- **오류.** 원천을 읽지 못하면 빈 목록으로 바꾸지 않는다. 이 목은 프로세스 안 객체라 네트워크 실패를 새로 정의하지 않는다.
  커서·스냅샷·`limit`의 형식 오류는 §5. 코드 이름은 정하지 않는다.
- **비청구.** 공연 목록은 재고의 체인 현재성, 주최자 인증, 판매 가능의 운영 승인이 아니다. `open`은 목의 bool이다.

### 2.2 `get_show`

- **노출 상태.** `ReservationMachine.view_show`가 반환하는 봉투와 그 `show`.
  봉투에 이미 있는 키: `provenance` (`MOCK_GATE_ONLY`), `lifecycle_authority` (`IN_MEMORY_FSM`), `duplicate` (거짓), `applied` (`view_show`), `logical_time_ms`, `external_payment` (`UNSUPPORTED`), `external_admission` (`UNSUPPORTED`), `economic_finality_claimed` (거짓), 그리고 `mock_gates.NON_CLAIMS`의 항상 거짓 플래그.
  `show`는 `_show_snapshot`이며 키는 `_show_view`와 같다. `show_id`, `organizer_role`, `currency`, `capacity`, `primary_price`, `resale_cap`, `resale_allowed`, `organizer_bps`, `platform_bps`, `gate_roles`, `open`, `slots` (`slot`, `state`, `reservation_id`, `right_id`), `payment_ref_count`.
  `MockGates.view_show` 단독 반환에는 `lifecycle_authority`가 없다. 이 쿼리의 뒷받침은 FSM 쪽 `view_show`다.
- **행위자 가시성.** `public listing`에 `organizer`를 더해 슬롯 점유를 볼지의 문제다. 값은 §6. `slots[].reservation_id`를 공개 목록과 같이 보이는 필드로 확정하지 않는다.
- **일관성.** 기계: `ReservationMachine`과 그 기계가 읽는 `MockGates`. 한 응답 안에서의 중첩이며, 예약 기계와 리셀·검표·정산 기계의 원자적 스냅샷이 아니다.
  반영하는 수락: 그 저널에 있는 `register_show`와, 슬롯을 바꾼 이미 수락된 예약 명령. 시계는 이미 주입된 값이다.
- **페이지.** 해당 없음.
- **오류.** 없는 공연은 `UNKNOWN_SHOW`. 식별자 거절은 `INVALID_ID`. 둘 다 기존 `view_show`의 코드다.
- **비청구.** §7. `payment_ref_count`는 주입된 목 사실의 개수이지 입금 건수가 아니다.

### 2.3 `get_booking`

- **노출 상태.** `ReservationMachine.view`가 반환하는 `_view` dict를 그대로 쓴다.
  키: `provenance`, `lifecycle_authority`, `reservation_id`, `phase`, `terminal`, `show_id`, `slot`, `buyer_role`, `expires_ms`, `expired`, `order_id`, `amount`, `currency`, `quote_ref`, `payment_ref`, `issuance_id`, `admission_id`, `admission_expired`, `consume_id`, `settlement_id`, `settlement_gate`, `mock_settlement_commit_observed`, `economic_finality_claimed`, `slot_state`, `slot_reservation_id`, `slot_right_id`, `right`, `accepted_entries`, `external_payment`, `external_admission`, `NON_CLAIMS`의 항상 거짓 플래그, `funds_executed`, `chain_issued`.
  `right`는 `right_id`가 있을 때만 `MockGates._right_view`다. 없으면 null. 키 이름 `right`로 남기고 예약 단계와 합치지 않는다.
  `settlement_gate`는 `UNBOUND`, `BOUND`, `MOCK_COMMIT_OBSERVED` 중 하나인 라벨이다. 정산 객체가 아니다.
  이 dict에는 `logical_time_ms` 키가 없다. 시각은 기계의 시계로 §3 `accepted_through`에만 제안한다. `_view`에 시각 키를 새로 끼워 넣지 않는다.
- **행위자 가시성.** 클래스 `owner or holder` (fixture `buyer_role`). `buyer_role`, `payment_ref`, `amount`를 다른 클래스에 보일지는 §6과 §9의 법률 행.
- **일관성.** 기계: `ReservationMachine`. 중첩 `right`의 기계: 그 기계에 묶인 `MockGates`.
  `accepted_entries`는 그 케이스의 `subject_ids`에 해당하는 저널 항목 수다. 기계 전체 저널 길이가 아니다.
  반영하는 수락: 그 예약에 대해 저널에 남은 명령. 거절은 저널에 없다. 멱등 재전송은 항목을 늘리지 않는다.
  `expired`와 `admission_expired`는 이미 주입된 시계와 저장 `expires_ms`의 비교다. 조회가 해제 명령이 된다거나 단계를 바꾸지 않는다.
- **페이지.** 해당 없음.
- **오류.** 없는 예약은 `UNKNOWN_RESERVATION`. 식별자 거절은 `INVALID_ID`.
- **비청구.** §7. `phase`가 `PAYMENT_NOTED`이거나 `payment_ref`가 있어도 입금이 아니다. `chain_issued`는 거짓이다. `MOCK_COMMIT_OBSERVED`는 정산 목의 `COMMITTED`를 읽었다는 라벨이다.

### 2.4 `list_bookings`

- **노출 상태.** 메서드는 없다. 모집단은 `ReservationMachine`의 예약 케이스다. 원소는 `_view`의 요약이다.
  추천 요약 키: `reservation_id`, `phase`, `terminal`, `show_id`, `slot`, `expires_ms`, `expired`.
  점 조회에 남기는 키: `buyer_role`, `order_id`, `amount`, `currency`, `quote_ref`, `payment_ref`, `issuance_id`, `admission_id`, `admission_expired`, `consume_id`, `settlement_id`, `settlement_gate`, `mock_settlement_commit_observed`, `right`, `slot_state`, `slot_reservation_id`, `slot_right_id`, `accepted_entries`, 그리고 항상 거짓 플래그 전부.
  "보유자별" 필터의 보유자는 이 기계의 `buyer_role` fixture다. 사람 식별자가 아니다.
- **행위자 가시성.** 호출 fixture와 `buyer_role`이 같은 행만 보이기를 추천한다. 그 동등 비교는 인증이 아니다 (§6). 다른 예약의 존재 자체를 숨길지의 값도 미정이다.
- **일관성.** 기계: `ReservationMachine` 하나. 리셀·검표·정산 기계의 행을 이 목록에 합치지 않는다.
  반영하는 수락: 그 기계 저널에 남은 예약 명령. 빈 페이지는 그 기계를 읽었고 맞는 행이 없다는 뜻이다. 원천 불능의 대체가 아니다.
- **페이지.** §5.
- **오류.** §5의 커서·스냅샷·범위 조건. 코드 이름은 정하지 않는다. 필터 문자열이 식별자 규칙을 어기면 기존 `INVALID_ID`를 재사용하는 쪽이 이 초안의 한계다. 새 코드를 만들지 않는다.
- **비청구.** 목록에 행이 있음은 결제, 발행, 입장의 증거가 아니다. §7.

### 2.5 `get_right`

- **노출 상태.** `ResaleMachine.view_right`의 봉투. `applied`는 `view_right`. `ticket`은 `_ticket_view`, `right`는 `MockGates._right_view`다.
  `ticket` 키: `provenance`, `lifecycle_authority`, `right_id`, `sale_phase`, `eligible`, `reservation_id`, `show_id`, `slot`, `holder_role`, `version`, `active_listing_id`, `economic_finality_claimed`, `venue_credential_reissued`, `funds_executed`, `external_marketplace`, `NON_CLAIMS`.
  `right` 키: `right_id`, `show_id`, `slot`, `holder_role`, `state`, `version`, `generation`, `listing_id`, `admission_id`, `last_payment`, `last_amount`, `last_payer`.
  두 dict를 한 레코드로 합치지 않는다.
- **행위자 가시성.** 클래스 `owner or holder` (`holder_role`). `last_payer`, `last_payment`, `last_amount`는 최소 공개 추천에서 다른 클래스에 보이지 않는다. 값은 §6.
- **일관성.** 기계: `ResaleMachine`. 중첩 `right`의 기계: 묶인 `MockGates`.
  `eligible`은 살아 있는 리스팅 식별자가 없음을 이 프로세스에서 본 것이다. 다른 채널의 배타성이 아니다 (`cross_channel_exclusive`는 거짓).
- **페이지.** 해당 없음.
- **오류.** 없는 권리는 `UNKNOWN_RIGHT`. 식별자 거절은 `INVALID_ID`.
- **비청구.** §7. `venue_credential_reissued`는 거짓이다. 권리 조회는 입장 자격 재발급이 아니다.

### 2.6 `get_presentation`

- **노출 상태.** `ResaleMachine.view_presentation`의 봉투. `applied`는 `view_presentation`. 중첩 `presentation`과 `right`.
  `presentation` 키: `right_id`, `version`, `holder_role`, `matches_current_right`, `current_version`, `current_holder_role`, `venue_credential_reissued`, `admission_routing_production`.
  `right`는 §2.5의 `_right_view`다.
  `matches_current_right`가 참이 되는 기존 조건은 `right.state == ACTIVE`, 버전이 같고, `holder_role`이 같고, `listing_id`가 null인 경우다. 이 초안이 그 조건을 완화하거나 강화하지 않는다.
- **행위자 가시성.** 클래스 `owner or holder`. 게이트 역할이 이 비교를 볼지는 §6. 추천은 게이트에 `fresh` 비교(§2.10)만 열고, 이 프레젠테이션의 `holder_role` 원문은 보유자에게만 두는 것이다.
- **일관성.** 기계: `ResaleMachine`과 묶인 `MockGates`. 검표 기계의 단계와 원자적으로 맞지 않는다.
- **페이지.** 해당 없음.
- **오류.** 없는 권리는 `UNKNOWN_RIGHT`. 식별자 거절은 `INVALID_ID`. 버전이 오래되었거나 보유자 라벨이 다르면 예외가 아니라 `matches_current_right: false`다. 그것을 성공한 입장으로 읽지 않는다.
- **비청구.** 메서드 주석과 같다. 공연장 스캔이 아니고 자격 증명을 다시 발급하지 않는다. `matches_current_right`는 비교 결과다. §7.

### 2.7 `list_open_listings`

- **노출 상태.** 메서드는 없다. 모집단은 `ResaleMachine`의 리스팅이다. 원소는 `_listing_view`의 요약이다.
  어떤 단계를 "열린 목록"으로 셀지는 `UNDETERMINED`다. 담당은 Astra. `OPEN_PHASES`는 `LISTED`, `BUY_HELD`, `PAYMENT_NOTED`다. 이것은 기존 전이 집합의 이름이지 공개 목록의 정의가 아니다.
  최소 공개 추천: `phase`가 `LISTED`이고 `expired`가 거짓이며 `attached`가 참인 행만. `BUY_HELD`와 `PAYMENT_NOTED`는 추천에서 뺀다. 그 추천은 결정이 아니다.
  추천 요약 키: `listing_id`, `show_id`, `amount`, `currency`, `expires_ms`, `expired`, `phase`.
  점 조회에 남기는 키: `seller_role`, `recipient_role`, `buyer_role`, `hold_id`, `payment_ref`, `settlement_id`, `settlement_gate`, `transfer_id`, `holder_role`, `right_id`를 포함한 나머지 `_listing_view` 키.
- **행위자 가시성.** 클래스 `public listing`. 판매자·수신자·구매자 라벨은 추천에서 공개하지 않는다.
- **일관성.** 기계: `ResaleMachine` 하나. 예약 기계의 재고와 합쳐 하나의 "판매 중" 플래그를 만들지 않는다.
  쓰기 `list_resale`의 수락 결과가 모집단에 들어온다. 그 쓰기 자체를 이 조회로 호출하지 않는다.
- **페이지.** §5.
- **오류.** §5. 코드 이름은 정하지 않는다. 빈 페이지는 그 기계를 읽었고 적용된 범위의 행이 없다는 뜻으로만 쓴다. 단계 범위가 `UNDETERMINED`인 동안 구현은 그 술어를 묶지 않는다 (`NOT_BOUND`). 명령 이름 자체는 사용자 결정으로 정해져 있다.
- **비청구.** 목록의 금액은 목 리스팅 금액이다. 판매자 지급, 정산 분개, 체인 소유가 아니다. §7.

### 2.8 `get_listing`

- **노출 상태.** `ResaleMachine.view`가 반환하는 `_listing_view`를 그대로 쓴다.
  키: `provenance`, `lifecycle_authority`, `listing_id`, `phase`, `terminal`, `right_id`, `show_id`, `seller_role`, `recipient_role`, `buyer_role`, `hold_id`, `amount`, `currency`, `expires_ms`, `expired`, `attached`, `version`, `version_after`, `payment_ref`, `settlement_id`, `settlement_gate`, `mock_settlement_commit_observed`, `transfer_id`, `ownership_transferred`, `prior_presentation_valid`, `venue_credential_reissued`, `economic_finality_claimed`, `holder_role`, `current_version`, `generation`, `slot_state`, `slot_right_id`, `accepted_entries`, `external_marketplace`, `external_payment`, `NON_CLAIMS`, `funds_executed`, `chain_owner_current`.
  `holder_role`, `current_version`, `generation`, `slot_state`, `slot_right_id`는 읽을 때 `MockGates`의 공개 권리·슬롯에서 복사한 중첩 관찰이다. 별도 키로 남긴다.
- **행위자 가시성.** 클래스 `owner or holder` (판매자 또는, 이전 뒤라면 현재 `holder_role`). 공개 목록으로 이 dict 전체를 내보이지 않는 쪽을 추천한다.
- **일관성.** 기계: `ResaleMachine`. 슬롯·권리 필드의 기계: 묶인 `MockGates`. `settlement_gate`는 라벨이다. 정산 기계의 `view`와 한 트랜잭션이 아니다.
- **페이지.** 해당 없음.
- **오류.** 없는 리스팅은 `UNKNOWN_LISTING`. 식별자 거절은 `INVALID_ID`.
- **비청구.** `ownership_transferred`가 참이어도 `chain_owner_current`는 거짓이다. `payment_ref`는 주입 사실이다. §7.

### 2.9 `get_admission`

- **노출 상태.** `AdmissionMachine.view`가 반환하는 `_credential_view`를 그대로 쓴다.
  키: `provenance`, `lifecycle_authority`, `right_id`, `reservation_id`, `phase`, `terminal`, `show_id`, `slot`, `holder_role`, `version`, `issued_version`, `generation`, `state`, `admission_id`, `admission_expired`, `consume_id`, `version_after`, `gate_role`, `slot_state`, `slot_right_id`, `economic_finality_claimed`, `venue_credential_reissued`, `offline_admission`, `external_admission`, `admission_routing_production`, `NON_CLAIMS`, `funds_executed`.
  `version`, `generation`, `state`, `admission_id`, `slot_state`, `slot_right_id`는 묶인 게이트의 권리·공연을 읽어 채운다. 검표 단계와 한 필드로 합치지 않는다.
- **행위자 가시성.** 클래스 `owner or holder`와 `gate role`. `gate_role`과 `holder_role`을 공개 목록에 넣지 않는 쪽을 추천한다.
- **일관성.** 기계: `AdmissionMachine`. 권리·슬롯의 기계: 묶인 `MockGates`. 예약 기계·정산 기계와 원자적이지 않다.
  `admission_expired`는 주입된 시계와 `admission_expires_ms`의 비교다. 조회가 `consume`이 되지 않는다.
- **페이지.** 해당 없음.
- **오류.** 없는 자격은 `UNKNOWN_RIGHT` (`_credential`). 식별자 거절은 `INVALID_ID`.
- **비청구.** `phase`가 `CONSUMED`이거나 소비 증거의 `decision`이 `CONSUMED_ONCE`여도 현장 입장이 아니다. `offline_admission`과 `admission_routing_production`은 거짓이다. `admission_granted`는 이 dict의 키가 아니다. 정산 조회에서 그 키가 있으면 거짓이다 (§2.11, §7).

### 2.10 `get_credential`

- **노출 상태.** `AdmissionMachine.view_credential`의 봉투. `applied`는 `view_credential`. 중첩 `credential`은 §2.9의 `_credential_view`. 중첩 `presentation` 키: `right_id`, `version`, `holder_role`, `fresh`, `decision`, `offline_admission`, `venue_credential_reissued`, `admission_routing_production`, `external_admission`.
  `fresh`가 거짓이 되는 기존 경로는 `_assert_external`, `_assert_ownership`, `_assert_reservation`, `_assert_settlement`가 `AdmissionError`를 내는 경우다. `decision`은 그 코드다. 이 초안이 그 판정을 입장 허용으로 뒤집지 않는다.
- **행위자 가시성.** 클래스 `gate role`과 `owner or holder`. `decision`에 원천 코드가 있어도 그것은 비교 결과다.
- **일관성.** 기계: `AdmissionMachine`. 판정은 그 호출이 읽는 예약·리셀·정산 `view`와 게이트에 의존한다. 그 읽기는 한 기계의 저널이 아니다. 응답은 `credential`과 `presentation`을 갈라 적는다.
  외부 현장 신원·회수 원천을 새로 붙이지 않는다. 의존이 있으면 기존처럼 실패한다.
- **페이지.** 해당 없음.
- **오류.** 없는 자격은 `UNKNOWN_RIGHT`. 식별자 거절은 `INVALID_ID`.
  원천 불능은 빈 성공이 아니다. 기존 코드 `VENUE_SOURCE_UNAVAILABLE`, `REVOCATION_SOURCE_UNAVAILABLE`, `OWNERSHIP_SOURCE_UNAVAILABLE`, `TICKET_SOURCE_UNAVAILABLE`, `SETTLEMENT_SOURCE_UNAVAILABLE`는 `presentation.decision`으로 보고되고 `fresh`는 거짓이다. 그 코드를 성공이나 "자격 없음"의 부재로 바꾸지 않는다.
- **비청구.** 메서드 주석과 같다. `fresh`는 입장 허가도, 오프라인 허용도, 현장 스캔도 아니다. §7.

### 2.11 `get_settlement`

- **노출 상태.** `SettlementMachine.view`의 `_view`를 그대로 쓴다.
  키: `provenance` (`MOCK_SETTLEMENT_ONLY`), `lifecycle_authority` (`IN_MEMORY_FSM`), `settlement_id`, `phase`, `terminal`, `trade_id`, `currency`, `gross`, `debtor_role`, `policy`, `mock_authorized`, `provider_authorization_executed`, `commit_movement_id`, `failure_reason`, `cancel_reason`, `external_payment`, `legal_debtor_bound`, `admission_granted`, `right_cancelled`, `bank_debit_observed`, `external_return_closed`, `funds_executed`, `durable`, `accepted_entries`, `claim`.
  `claim`은 `phase`가 `CAPTURED` 또는 `COMMITTED`일 때만 `MockSettlement.view`다. 그 밖의 단계에서는 null이다. `claim` 안의 `provenance`도 `MOCK_SETTLEMENT_ONLY`다.
  이 기계에는 `logical_time_ms`가 없다. 없는 시계를 0이나 벽시계로 채우지 않는다.
  GATES §1의 `NON_CLAIMS` 키 집합을 이 dict에 합치지 않는다. 이 조회가 이미 거짓으로 두는 플래그만 유지한다.
- **행위자 가시성.** 클래스 `organizer`와, 채권의 `debtor_role` fixture. `policy`, `gross`, 수취인별 `claim.obligations`를 공개 목록에 넣지 않는 쪽을 추천한다. 법률상 채무자 표시는 `legal_debtor_bound`가 거짓이므로 하지 않는다.
- **일관성.** 기계: `SettlementMachine`. 중첩 `claim`의 기계: 그 기계의 `MockSettlement` 장부. 예약·리셀이 가진 `settlement_gate` 라벨과 원자적으로 갱신된다고 적지 않는다.
  `accepted_entries`는 그 `settlement_id`의 저널 항목 수다.
- **페이지.** 해당 없음.
- **오류.** 없는 정산은 `UNKNOWN_SETTLEMENT`. 식별자 거절은 `INVALID_ID`. 장부를 읽지 못하면 성공한 빈 `claim`으로 바꾸지 않는다. 기존 코드가 예외이면 그 예외를 유지한다.
- **비청구.** `funds_executed`, `bank_debit_observed`, `legal_debtor_bound`, `admission_granted`, `durable`은 거짓이다. `provider_authorization_executed`는 거짓이다. 목 커밋은 입금이 아니다. §7. 금융 조회 스키마는 `fin-catalogue-read-model` 소관이다.

### 2.12 `get_credit_advance`

- **노출 상태.** `CreditMachine.view`의 `_view`를 그대로 쓴다. `provenance`는 `MOCK_CREDIT_F04_ONLY`. `lifecycle_authority`는 `IN_MEMORY_FSM`. `exposure_ledger`는 `MOCK_EXPOSURE`.
  키: `advance_id`, `phase`, `terminal`, `claim_id`, `trade_id`, `currency`, `amount`, `beneficiary_role`, `open_face`, `reserved_open`, `residual_unreserved`, `confirmed_cash_on_face`, `recovery_due_on_face`, `snapshot_frozen`, `note_status`, `draw_id`, `drawn_exposure`, `repaid_exposure`, `outstanding_exposure`, `repayments`, `next_repayment_sequence`, `settlement_id`, `settlement_gate`, `mock_settlement_commit_observed`, `reject_reason`, `cancel_reason`, `default_reason`, `external_credit`, `economic_finality_claimed`, `underwriting_executed`, `kyc_executed`, `ownership_mutated`, `ticket_ownership_authoritative`, `accepted_entries`, 그리고 `mock_credit._flags`의 항상 거짓 플래그 (`funds_executed`, `license_granted`, `regulated_product`, `collateral_perfected`, `priority_bound`, `disposal_controlled`, `revenue_assigned`, `admission_granted`, `legal_debtor_bound`, `bank_debit_observed`, `external_pledge_complete`, `durable`, `repayment_observed`, `interest_defined`).
  이 기계에는 `logical_time_ms`가 없다. 시계를 만들지 않는다.
  액면 숫자는 기존 목의 키를 인용한다. 복식부기, 수출, 대사 스키마를 여기서 정의하지 않는다.
  `snapshot_frozen`은 묶인 목 청구가 있을 때만 참이다. `MockCredit._view_claim`이 항상 참으로 두는 값과 같지 않다.
- **행위자 가시성.** 클래스 `owner or holder`에 해당하는 fixture는 `beneficiary_role`이다. 추천은 그 fixture의 자기 행만이다. 값은 §6.
- **일관성.** 기계: `CreditMachine`. 열린 청구 숫자의 원천은 묶인 `MockCredit`이다. `settlement_gate`는 라벨이다. 정산 기계와 원자적이지 않다.
  `view`는 기존처럼 호출 전후의 소유권 원천 `canonical_state`를 비교한다 (`_guard`). 조회가 소유권을 바꾸면 기존 `MOCK_INVARIANT`다.
- **페이지.** 해당 없음.
- **오류.** 없는 선급은 `UNKNOWN_ADVANCE` (`CreditMachine._case`). 식별자 거절은 `INVALID_ID`. 새 코드를 추가하지 않는다.
- **비청구.** `funds_executed`, `bank_debit_observed`, `repayment_observed`, `kyc_executed`, `underwriting_executed`는 거짓이다. 여신 조회는 대출, 출금, KYC가 아니다. 이 쿼리를 금융 카탈로그 조회로 세지 않는다. 사용자 결정은 이 이름을 조회 집합에 넣되 기존 view 키의 인용으로만 둔다. 금융 조회 스키마는 `fin-catalogue-read-model`이다.

### 2.13 `get_credit_claim`

- **노출 상태.** `CreditMachine.view_claim`이 반환하는 `MockCredit._view_claim`을 그대로 쓴다.
  키: `provenance` (`MOCK_CREDIT_F04_ONLY`), `claim_id`, `trade_id`, `currency`, `open_face`, `reserved_open`, `residual_unreserved`, `confirmed_cash_on_face`, `recovery_due_on_face`, `snapshot_frozen`, 그리고 §2.12와 같은 `_flags`.
  이 dict에는 `lifecycle_authority`가 없다. FSM `_view`와 다른 객체다. 둘을 한 스키마로 합치지 않는다.
  `snapshot_frozen`은 목 청구 뷰가 항상 참이다. 체인 스냅샷이나 `ReadObservationV1.snapshot_digest`가 아니다.
- **행위자 가시성.** §2.12와 같은 추천. 청구는 여러 선급이 예약할 수 있으므로, 다른 `beneficiary_role`의 존재 노출은 §6에서 미정이다. 추천은 자기 fixture가 예약한 청구만이다.
- **일관성.** 기계: `CreditMachine`이 읽는 `MockCredit`. 정산 기계의 `claim` (§2.11)과 다른 객체다. 이름이 같다고 합치지 않는다.
- **페이지.** 해당 없음.
- **오류.** 없는 청구는 `UNKNOWN_CLAIM`. 식별자 거절은 `INVALID_ID`.
- **비청구.** §2.12와 같다. `reserved_open`은 목 장부의 정수다. 은행 예약이 아니다.

## 3. 공통 봉투 (제안)

기존 `view*`가 이 절의 키를 이미 모두 반환한다고 읽지 않는다.
점 조회의 본문은 §2의 기존 dict다. 아래 추가 키는 `read-model-reference`가 그 dict를 감쌀 때 쓴다.
이 노드는 기존 메서드의 키를 늘리지 않는다.

기계가 이미 두는 값만 재사용한다.

| 키 | 이 초안에서의 위치 |
|---|---|
| `provenance` | 기계마다 다르다. 예약·리셀·검표는 `MOCK_GATE_ONLY`. 정산은 `MOCK_SETTLEMENT_ONLY`. 여신은 `MOCK_CREDIT_F04_ONLY`. 한 문자열로 합치지 않는다. |
| `lifecycle_authority` | 이미 두는 기계에서는 `IN_MEMORY_FSM`. `MockGates.view_show` 단독과 `MockCredit._view_claim`에는 이 키가 없다. 없는 dict에 지어 넣지 않는다. |
| `logical_time_ms` | `ReservationMachine`, `ResaleMachine`, `AdmissionMachine`, `MockGates`의 기존 시계. 정산·여신 기계에는 없다. |
| 항상 거짓 플래그 | 그 기계의 뷰가 이미 거짓으로 두는 것만. GATES §1의 `role_authenticated`, `organizer_authenticated`, `chain_grant_current`, `durable`, `quote_policy_approved`, `discount_applied`, `provider_fact_live`, `funds_executed`, `buyer_evidence_available`, `chain_owner_current`, `cross_channel_exclusive`, `admission_routing_production`, `private_proof_verified`, `compensation_defined`는 그 플래그를 복사하는 예약·리셀·검표 뷰에 적용된다. `economic_finality_claimed`와 `chain_issued`는 그 뷰가 이미 거짓으로 두는 곳에서 거짓이다. 성공이 참을 만들지 못한다. |

초안 0.1이 공통 봉투에 더하는 키다. 해시 함수의 이름은 정하지 않는다.

- `read_schema_version`. 이 초안은 `0.1`이다. 기능 라벨을 설계확정으로 올리는 버전이 아니다.
- `query_digest`. 정규화된 쿼리 입력의 다이제스트. 알고리즘 이름은 정하지 않는다. 정규화는 각 기계가 이미 쓰는 canonical JSON을 재사용한다. 새 인코딩을 만들지 않는다.
- `fixture_mode`. 이 범위의 값은 `REFERENCE_IN_MEMORY`이다. `READINESS_LOCAL`과 운영 모드는 여기서 정의하지 않는다. 목을 운영으로 표시하지 않는다.
- `accepted_through`. 그 기계가 수락한 저널의 항목 수(`export_journal`의 길이)와, 시계가 있는 기계에만 `logical_time_ms`. 케이스별 `accepted_entries`와 바꾸지 않는다. 시계가 없는 기계는 `logical_time_ms`를 생략한다.

다음은 `RESERVED_FOR ReadObservationV1`이다. 이 초안이 정의하지 않는다.
소유는 `protocol-read-projection-evidence`이고, 후보의 출처는 `docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md` §6이다.

- `source_cut`
- `projection_watermark`
- `snapshot_digest`
- `observed_receipt_refs`
- `producer_manifest_digest`

§6 후보인 `subject_scope`와 `profile_revision`도 같은 소유다. 여기서 필드 정의를 고정하지 않는다.
사용자 결정은 위 다섯 필드를 첫 봉투에 넣지 않는다. 미룬 자리는 `protocol-read-projection-evidence`다.

## 4. 일관성

조회가 반영하는 영수증은, 그 프로세스가 그 기계의 저널에 **수락해 남긴** 명령뿐이다.

- 거절된 명령은 저널에 남지 않는다. 조회에 수락된 명령으로 나타나지 않는다.
- 같은 바인딩의 멱등 재전송은 저널 항목을 늘리지 않는다. 조회는 첫 수락 뒤의 상태를 본다. 재전송 응답 자체가 새 영수증이 아니다.
- 예약, 리셀, 검표, 정산, 여신은 서로 다른 기계다. 한 응답이 둘 이상을 읽으면 원자적이지 않다. 응답은 읽은 기계를 이름과 중첩 키로 적는다. 단계를 조용히 하나로 합치지 않는다.
- 알 수 없음이나 닿지 않는 원천은 그대로 보고한다. 성공이나 "없음"으로 바꾸지 않는다. 재사용하는 코드는 `VENUE_SOURCE_UNAVAILABLE`, `REVOCATION_SOURCE_UNAVAILABLE`, `OWNERSHIP_SOURCE_UNAVAILABLE`, `TICKET_SOURCE_UNAVAILABLE`, `SETTLEMENT_SOURCE_UNAVAILABLE`이다. 조회 전용 새 코드를 만들지 않는다.
- 조회는 시계와 저널을 진행시키지 않는다. §8.
- 프로세스 사이, 내구 저장, 체인 위의 현재성을 주장하지 않는다. `durable`, `chain_grant_current`, `chain_owner_current`, `cross_channel_exclusive`는 해당 뷰에서 거짓이다.

다른 기계의 중첩을 읽는 동안 그 기계가 같은 프로세스에서 먼저 바뀌었으면, 조회는 각 기계를 읽는 시점의 상태를 보여줄 뿐 하나의 커밋 경계를 만들지 않는다.
그 어긋남을 숨기지 않는다.

## 5. 페이지

목록 쿼리만 이 절을 따른다. 점 조회는 페이지가 없다.
숫자 상한, 기본 쪽 크기, 커서 수명, 정렬 키는 적지 않는다. 분류는 `UNDETERMINED`이고 담당은 Astra다. 사용자 결정(2026-10-08)이 이 노드에서 숫자를 채우지 말라고 정했다.

- 커서는 불투명하다. 묶음은 `(query, scope, ordering, snapshot)`이다. 네 요소 중 하나라도 다르면 그 커서를 거절한다.
- 순서는 결정론적이다. 같은 정렬 키의 동순위는 유일한 식별자로 가른다. 정렬 키의 선택은 정하지 않는다.
- `limit`가 있다. 상한과 기본값이 모두 필요하다. 둘 다 값을 정하지 않는다.
- 끝을 명시한다. 그 스냅샷의 끝이면 `next_cursor`는 null이고 `truncated`는 false다. 상한으로 잘렸으면 `truncated`는 true이고 `next_cursor`는 null이 아니다.
- 페이지 사이에 스냅샷이 달라지면 침묵하고 건너뛰지 않는다. 형식 있는 오류다. 오류 코드의 이름은 이 초안이 정하지 않는다.
- 커서 수명은 정하지 않는다.
- 커서는 허가증이 아니다. 가시성 범위가 바뀐 뒤 다시 쓰지 못한다.
- 목록의 보존 기간이나 이력 깊이는 제품 값이다. 여기서 정하지 않는다 (§9).

## 6. 행위자 가시성

`actor`는 픽스처 문자열이다. 인증 결과가 아니다.
근거는 [openapi/README.md](openapi/README.md)다. `sourceAuthentication: FIXTURE_ONLY`는 HTTP 보안 스킴이 아니다.
이 초안은 인증 스킴, 세션, 서명을 만들지 않는다.

가시성 **클래스**만 둔다. 칸의 값(누가 무엇을 보는가)은 `UNDETERMINED`다. 담당은 Astra.
추천 열은 최소 공개다. 결정이 아니다.

| 클래스 | 이 목에서의 뜻 | 추천 (미결정) |
|---|---|---|
| `public listing` | 공연·열린 리스팅 목록에 놓을 수 있는 필드 | 식별자, 열림, 통화, 용량, 일차 가격, `resale_allowed`, 리스팅 금액·만료·단계. 역할 라벨, 결제 참조, 게이트 요청, `last_payer`는 제외 |
| `owner or holder` | 그 행의 `buyer_role`, `holder_role`, `seller_role`, `beneficiary_role`과 같은 fixture | 자기 행의 단계·금액·만료·자기 라벨. 다른 행은 제외 |
| `organizer` | 공연의 `organizer_role`과 같은 fixture | 자기 공연의 슬롯 상태. 결제 참조와 구매자 라벨은 제외 |
| `gate role` | 그 공연 `gate_roles`에 있는 fixture | `fresh`, `decision`, 버전 비교. 결제 참조는 제외 |
| `operator` | 진단 조회 | 이 초안이 정의하지 않는다. `k-operator-evidence` 소관 |

fixture끼리의 문자열 비교로 행을 거를 수 있다. 그 거름은 접근 통제가 아니라고 응답에 적는다.
`role_authenticated`와 `organizer_authenticated`는 참이 되지 않는다.

구매자 신원(라벨을 사람·계정에 묶는 일)은 법률·개인정보 검토가 필요하다.
담당은 사용자이며 경로는 로드맵 D-E의 `tl-legal-brief`다. 그 답변 전에는 `UNDETERMINED`다.
역할 라벨은 GATES §1대로 저장만 하는 문자열이다. 사람, 주소, 사업자, Sui address가 아니다.

## 7. 조회는 증명이 아니다

조회 성공은 결제, 발행, 입장의 증거가 아니다. GATES §1의 항상 거짓 플래그와 §8의 비청구를 그대로 둔다.

- **결제.** `payment_ref`, 단계 `PAYMENT_NOTED`, 라벨 `MOCK_COMMIT_OBSERVED`는 주입된 목 사실이다. 입금, 승인 매입, 은행 출금이 아니다. `funds_executed`, `bank_debit_observed`, `provider_fact_live`, `provider_authorization_executed`는 해당 뷰에서 거짓이다. 토스 MID, 웹훅 서명, 결제 상태의 제공자 사실은 `UNDETERMINED`다. 담당은 제공자(토스)이며 사용자를 거친다. [PG_TOSS_CARD_PROFILE.md](PG_TOSS_CARD_PROFILE.md)의 미확정 항목을 이 조회로 채우지 않는다.
- **발행.** 메모리 발행 증거의 `kind`는 1이고 `chain_issued`는 거짓이다. `buyer_evidence_available`과 `chain_grant_current`는 거짓이다. 조회가 이 증거를 체인 발행으로 올리지 않는다.
- **입장.** 소비 증거의 `CONSUMED_ONCE`는 목의 한 번 소비다. 현장 입장이 아니다. 정산 뷰의 `admission_granted`는 거짓이다. 검표 뷰의 `offline_admission`과 `admission_routing_production`은 거짓이다.
- 조회 결과를 명령의 전제, 멱등키, 재시도 허가로 쓰지 않는다.
- 조회 성공은 UNKNOWN을 해소하지 않는다. 원천 불능 코드는 원천 불능으로 남는다.
- 같은 프로세스의 다음 수락 명령이 조회 결과를 바로 낡은 것으로 만들 수 있다. 조회는 그 이후의 현재성을 예약하지 않는다.
- `get_presentation`의 `matches_current_right`와 `get_credential`의 `fresh`는 비교다. 입장이 아니다.

## 8. 비변경

술어: 제안된 조회를 호출해도 그 기계의 `canonical_state()`, `export_journal()`, 그리고 시계가 있는 기계의 `logical_time_ms`는 호출 전과 같다.
여신 기계는 그에 더해, 묶인 소유권 원천의 `canonical_state`도 같다. 기존 `CreditMachine.view`의 `_guard`와 같다.

조회는 시계를 올리지 않고, 저널 항목을 쓰지 않고, 멱등키를 저장하지 않고, 카운터를 증가시키지 않고, 게으른 만료 전이를 하지 않는다.
만료는 주입된 시계로 계산한다. `ReservationMachine.view`는 `expired`가 참이어도 `phase`를 `HELD`로 두고, 슬롯을 비우는 명령은 따로 있는 `release`다.
이 계산은 `reference/booking_resale_admission/test_reservation_fsm.py`의 시계 주입 뒤 `view` 관찰과 같다.
`set_clock`은 명령이다. 조회가 아니다.

이 술어는 `read-model-reference`가 다시 검사할 수 있는 형태로 둔다. 구현은 이 노드가 하지 않는다.

## 9. 열린 항목

사용자 결정으로 닫힌 것. 이 표는 다시 열지 않는다.

| 항목 | 결정 |
|---|---|
| 조회·목록을 어디에 둘지 | 선택지 A. 전용 카탈로그 조회 명령. 쓰기 본문 재사용 없음. JunTae, 2026-10-08 13:32 KST |
| 명령 이름 | `list_shows`, `get_show`, `get_booking`, `list_bookings`, `get_right`, `get_presentation`, `list_open_listings`, `get_listing`, `get_admission`, `get_credential`, `get_settlement`, `get_credit_advance`, `get_credit_claim` |
| `ReadObservationV1` 다섯 필드 | 첫 봉투에 넣지 않는다. `protocol-read-projection-evidence` |
| F04 두 조회 | 조회 집합에 포함한다. 기존 `CreditMachine` view 키의 인용만. 금융 스키마는 `fin-catalogue-read-model` |

아직 값이 없는 것. 숫자를 채우지 않는다. 법률 답을 추정하지 않는다.

| 항목 | 분류 | 담당 |
|---|---|---|
| 가시성 행렬의 값. 구매자 라벨, 보유자, 가격, 결제 참조를 누가 보는가 | `UNDETERMINED` | Astra |
| `limit` 상한, `limit` 기본값, 커서 수명, 목록 정렬 키 | `UNDETERMINED` | Astra |
| "열린 리스팅"에 넣을 단계 | `UNDETERMINED` | Astra. 그 전까지 술어는 `NOT_BOUND` |
| 목록의 보존·이력 깊이 | `UNDETERMINED` | Astra |
| 역할 라벨을 사람·계정에 보여줄지의 법률·개인정보 | `UNDETERMINED` | 사용자. 경로 `tl-legal-brief` (로드맵 D-E) |
| 토스 결제 상태 사실. MID, 웹훅 서명, 계정 키 | `UNDETERMINED` | 제공자(토스). 사용자를 거쳐 회신. 이 초안은 회신을 받지 않았다 |

## 10. 비청구

이 초안의 존재는 B01–B05, R01–R05, P03, F01–F03, P04, F04, E06이 구현되거나 설계확정되었다는 뜻이 아니다.
라벨은 설계중이다.

- 명령 이름은 사용자 결정으로 정해져 있다. 카탈로그, OpenAPI, `protocol_contract.json`, SDK, 매니페스트의 바이트는 이 노드가 바꾸지 않는다.
- 공개 엔드포인트, 인증, 루프백 동작 변경, 프로젝션 저장소, 인덱스, 백엔드를 만들지 않는다.
- 조회를 내구 현재성, 체인 최종성, 은행 exactly-once, 운영 검표, 운영 준비로 읽지 않는다.
- `matched: true`를 쓰는 기존 reconcile은 이 프로세스 저널의 재생 일치다. 조회 성공이 그 일치를 대신하지 않는다.
- `economic_finality_claimed`는 거짓으로 남는다.
- 점 조회에 대한 기존 FSM 시험이 목록, 커서, 가시성 행렬을 덮지 않는다. 그 셋은 구현 전이며 시험도 없다.
- commerce 메서드 시그니처는 §0.2대로 UNVERIFIED다.
- 이 문서는 운영 준비, 안전, 프로토콜 검증 완료를 말하지 않는다.
