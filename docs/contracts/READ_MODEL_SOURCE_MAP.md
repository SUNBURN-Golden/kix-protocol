# 조회 원천 지도 — 승인된 13개 조회 이름의 소스 표면·보존 술어 표

노드 `plan-read-model-source-map`. 이슈 없음 (루프 제안 노드, `.aiops/program.json` 미등재). 문서일: 2026-10-13.
이 세션에서 확인한 `origin/main`: `cb59612b847fc2e6ef71810202be5e2ca5f76724`. 작업 시작 HEAD도 같은 SHA다.
읽는 계약: [READ_MODEL_QUERIES.md](READ_MODEL_QUERIES.md) 초안 0.1, git blob `06b9ec68f9dc9dd4af4d70c236360be964a84ae1`.
상태: **입력 자료. 결정 문서가 아니다.** 소비자는 `read-model-reference` 노드(`.aiops/program.json`의 노드 id), commerce `bind-list-read`, 후속 `ps-02-query-contract`다 (READ_MODEL_QUERIES.md:32).
이 문서의 파일:줄 앵커는 위 작업 시작 SHA의 작업 트리 기준이다. 소스가 움직이면 §6 검사가 낡은 앵커를 알린다.

현행 승인 범위의 정본은 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md)다.

## 1. 범위와 비주장

이 문서가 하는 일은 세 가지다.

1. 승인된 13개 조회 이름 각각에 대해, 지금 참조 FSM 표면에 뒷받침이 있는지(`SOURCE_FOUND`) 없는지(`SOURCE_MISSING`) 기록한다.
2. `read-model-reference`가 보존해야 할 계약 술어를, 인용된 술어마다 `READ_MODEL_QUERIES.md`의 file:line 앵커와 함께 모은다.
3. 읽기 삽입이 나중에 어떤 카탈로그·게이트 기작을 거쳐야 하는지 적는다.

이 문서가 하지 않는 일.

- `UNDETERMINED` 값을 결정하지 않는다. 가시성 행렬 값, `limit` 상한·기본값, 커서 수명, 정렬 키, 열린 리스팅 단계(`NOT_BOUND`), 보존·이력 깊이는 그대로다. 담당은 Astra다 (READ_MODEL_QUERIES.md:386-389).
- 와이어 본문, `operationId`, 오류 코드 신규 이름, 카탈로그 삽입을 하지 않는다. 그 자리는 `read-model-reference`다 (READ_MODEL_QUERIES.md:25).
- 쿼리를 구현하지 않는다. 이 문서는 지도이지 구현 승인이 아니다.
- 카탈로그·OpenAPI·`protocol_contract.json`·SDK·매니페스트·`reference/v0.3-rc1/**`·두 잠금 커널 blob의 바이트를 바꾸지 않는다.
- 조회 성공이 결제·발행·입장·체인 현재성·내구성의 증거라고 읽지 않는다 (READ_MODEL_QUERIES.md:347-357).
- `MockGates`·`MockSettlement`·`MockCredit`에는 `canonical_state`/`export_journal`이 없다. §8의 비변경 술어가 FSM 기계를 대상으로 하는 동안 이 관측은 계약 미정의 영역의 특성 기록이며, 목에 없는 술어를 만들지 않는다 (AGENTS §8 분류 B).

## 2. 쿼리별 원천 지도

이름은 사용자 결정(2026-10-08, 선택지 A)으로 정해져 있다 (READ_MODEL_QUERIES.md:15, :377-378). 카탈로그 상태는 13개 모두 `NOT_IN_CATALOGUE`이며 이 문서도 그대로 둔다. 검사기가 두 카탈로그 JSON에 13개 이름이 없음을 다시 확인한다 (§5, §6).

| 쿼리 이름 | 종류 | 상태 | 원천 표면 (file:line) | 모집단·중첩 | RMQ 앵커 |
|---|---|---|---|---|---|
| `list_shows` | list | SOURCE_MISSING | 없음 — `def list_shows`가 어느 쪽에도 없다 | 모집단 `MockGates._shows` `mock_gates.py:97`; 원소 `MockGates._show_view` `mock_gates.py:732`; FSM 쪽 등록 id 집합 `ReservationMachine._shows` `reservation_fsm.py:155` | READ_MODEL_QUERIES.md:91-103 |
| `get_show` | point | SOURCE_FOUND | `ReservationMachine.view_show` `reservation_fsm.py:705` → `_show_snapshot` `reservation_fsm.py:908` → `MockGates.view_show` `mock_gates.py:633` | 원소 dict는 `_show_view` `mock_gates.py:732`. `MockGates.view_show` 단독 봉투에는 `lifecycle_authority`가 없어 뒷받침은 FSM 쪽이다 (READ_MODEL_QUERIES.md:110) | READ_MODEL_QUERIES.md:105-116 |
| `get_booking` | point | SOURCE_FOUND | `ReservationMachine.view` `reservation_fsm.py:702` → `_view` `reservation_fsm.py:931` | 중첩 `right`는 `MockGates._right_view` `mock_gates.py:783` | READ_MODEL_QUERIES.md:118-132 |
| `list_bookings` | list | SOURCE_MISSING | 없음 — `def list_bookings`가 없다 | 모집단 `ReservationMachine._cases` `reservation_fsm.py:156`; 원소는 `_view` `reservation_fsm.py:931`의 요약 부분집합 | READ_MODEL_QUERIES.md:134-145 |
| `get_right` | point | SOURCE_FOUND | `ResaleMachine.view_right` `resale_fsm.py:659` → `_ticket_view` `resale_fsm.py:1069` | 중첩 `right`는 `_public_right` `resale_fsm.py:1042`가 부르는 `MockGates._right_view` `mock_gates.py:783` | READ_MODEL_QUERIES.md:147-158 |
| `get_presentation` | point | SOURCE_FOUND | `ResaleMachine.view_presentation` `resale_fsm.py:664` | 중첩 `right`는 같은 `_public_right` 경로 | READ_MODEL_QUERIES.md:160-170 |
| `list_open_listings` | list | SOURCE_MISSING | 없음 — `def list_open_listings`가 없다 | 모집단 `ResaleMachine._listings` `resale_fsm.py:163`; 원소 `_listing_view` `resale_fsm.py:1094`; 기존 전이 집합 `OPEN_PHASES` `resale_fsm.py:49`. 쓰기 `list_resale` `resale_fsm.py:259`를 조회로 쓰지 않는다 (READ_MODEL_QUERIES.md:43-47) | READ_MODEL_QUERIES.md:172-184 |
| `get_listing` | point | SOURCE_FOUND | `ResaleMachine.view` `resale_fsm.py:656` → `_listing_view` `resale_fsm.py:1094` | 권리·슬롯 필드는 `_public_right` `resale_fsm.py:1042`의 중첩 관찰 | READ_MODEL_QUERIES.md:186-195 |
| `get_admission` | point | SOURCE_FOUND | `AdmissionMachine.view` `admission_fsm.py:512` → `_credential_view` `admission_fsm.py:1030` | 권리·슬롯 필드는 `_local_right`/`_local_show`가 묶인 게이트에서 읽는다 | READ_MODEL_QUERIES.md:197-207 |
| `get_credential` | point | SOURCE_FOUND | `AdmissionMachine.view_credential` `admission_fsm.py:515` | 중첩 `credential`은 `_credential_view` `admission_fsm.py:1030`; 원천 불능 코드는 `decision`으로 보고된다 (READ_MODEL_QUERIES.md:218) | READ_MODEL_QUERIES.md:209-219 |
| `get_settlement` | point | SOURCE_FOUND | `SettlementMachine.view` `settlement_fsm.py:476` → `_view` `settlement_fsm.py:635` | 중첩 `claim`은 `MockSettlement.view` `mock_settlement.py:289` → `_view` `mock_settlement.py:298`. `CAPTURED`/`COMMITTED`에서만 채운다 (READ_MODEL_QUERIES.md:225) | READ_MODEL_QUERIES.md:221-233 |
| `get_credit_advance` | point | SOURCE_FOUND | `CreditMachine.view` `credit_fsm.py:523` → `_view` `credit_fsm.py:760` | 비변경 감시 `_witness` `credit_fsm.py:830` / `_guard` `credit_fsm.py:839` | READ_MODEL_QUERIES.md:235-247 |
| `get_credit_claim` | point | SOURCE_FOUND | `CreditMachine.view_claim` `credit_fsm.py:530` → `_mock_claim` `credit_fsm.py:620` → `MockCredit.view_claim` `mock_credit.py:264` → `_view_claim` `mock_credit.py:290` | 이 dict에는 `lifecycle_authority`가 없다 (READ_MODEL_QUERIES.md:253) | READ_MODEL_QUERIES.md:249-259 |

관측 정리.

- 점 조회 10개는 모두 `SOURCE_FOUND`다. 목록 3개는 모두 `SOURCE_MISSING`이다. 모집단은 있으나 그 모집단을 열거하는 view가 없다.
- 목록 3개의 뒷받침은 RMQ 표의 `NONE` (READ_MODEL_QUERIES.md:67, :70, :73)과 같다. `NONE`은 원천이 없다가 아니라 열거 표면이 없다는 뜻으로 읽었다. 모집단 자체는 위 표가 적은 대로 존재한다.
- `list_resale`는 목록을 돌려주는 조회가 아니라 살아 있는 권리를 리스팅으로 받는 쓰기다 (READ_MODEL_QUERIES.md:43-47, `resale_fsm.py:259`, `mock_gates.py:372`). 이름을 재사용하지 않는다.

## 3. 보존 술어 지도

아래 표는 `read-model-reference`가 구현할 때 지켜야 할 술어를 그 근거와 함께 모은다. 각 행의 RMQ 앵커는 그 술어가 적힌 `READ_MODEL_QUERIES.md`의 줄이다. 이 문서는 술어를 새로 만들지 않고 모은다.

### 3.1 조회는 증명이 아니다 — 항상 거짓 플래그

| 술어 | 원천 표면 | RMQ 앵커 |
|---|---|---|
| `NON_CLAIMS` 14개 플래그 (`role_authenticated` … `compensation_defined`)는 그 플래그를 복사하는 예약·리셀·검표 뷰에서 항상 거짓 | `NON_CLAIMS` `mock_gates.py:23-38` | READ_MODEL_QUERIES.md:274, :349 |
| 정산 뷰의 `funds_executed`, `bank_debit_observed`, `legal_debtor_bound`, `admission_granted`, `durable`, `provider_authorization_executed`는 거짓 | `settlement_fsm.py:649-659` (`_view` 안의 거짓 리터럴) | READ_MODEL_QUERIES.md:233 |
| 여신 뷰의 `_flags` 14개(`funds_executed` … `interest_defined`)는 항상 거짓 | `_flags` `mock_credit.py:103` | READ_MODEL_QUERIES.md:238, :252 |
| `economic_finality_claimed`, `chain_issued`는 그 뷰가 이미 거짓으로 두는 곳에서 거짓. 성공이 참을 만들지 못한다 | 각 `_view`/`_envelope`의 거짓 리터럴 (예 `reservation_fsm.py:892-905`) | READ_MODEL_QUERIES.md:274 |
| `matches_current_right`와 `fresh`는 비교다. 입장 허가·현장 스캔·자격 재발급이 아니다 | `resale_fsm.py:664-693`, `admission_fsm.py:515-547` | READ_MODEL_QUERIES.md:357, :170, :219 |

### 3.2 비변경 (non-mutation)

술어: 조회 호출 전후에 그 기계의 `canonical_state()`, `export_journal()`, 시계가 있는 기계의 `logical_time_ms`가 같다 (READ_MODEL_QUERIES.md:361). 여신 기계는 묶인 소유권 원천의 `canonical_state`까지 같다 (READ_MODEL_QUERIES.md:362).

| 기계 | `canonical_state` | `export_journal` | `logical_time_ms` |
|---|---|---|---|
| `ReservationMachine` | `reservation_fsm.py:713` | `reservation_fsm.py:710` | 시계 있음 (`reservation_fsm.py:715`, 봉투 `:889`) |
| `ResaleMachine` | `resale_fsm.py:698` | `resale_fsm.py:695` | 시계 있음 (`resale_fsm.py:701`, 봉투 `:1023`) |
| `AdmissionMachine` | `admission_fsm.py:552` | `admission_fsm.py:549` | 시계 있음 (`admission_fsm.py:554`, 봉투 `:998`) |
| `SettlementMachine` | `settlement_fsm.py:485` | `settlement_fsm.py:482` | 시계 없음. 파일에 `logical_time_ms`가 없다 (READ_MODEL_QUERIES.md:226) |
| `CreditMachine` | `credit_fsm.py:543` | `credit_fsm.py:540` | 시계 없음 (READ_MODEL_QUERIES.md:239). `_guard` `credit_fsm.py:839`는 `_witness` `credit_fsm.py:830`가 읽은 묶인 소유권 `canonical_state` 전후 동등을 강제한다 (READ_MODEL_QUERIES.md:362) |
| `MockGates` | 없음 (관측, 분류 B) | 없음 (관측, 분류 B) | `_env`가 `logical_time_ms`를 낸다 `mock_gates.py:726`; `set_clock` `mock_gates.py:107` |
| `MockSettlement` | 없음 (관측, 분류 B) | 없음 (관측, 분류 B) | 시계 없음 |
| `MockCredit` | 없음 (관측, 분류 B) | 없음 (관측, 분류 B) | 시계 없음 |

게으른 만료.

- `expired`는 주입된 시계로 계산한다. `ReservationMachine._view`는 `expired`가 참이어도 `phase`를 `HELD`로 둔다 (`reservation_fsm.py:935`); 리셀 `resale_fsm.py:1098`, 검표 `admission_fsm.py:1039`도 같은 모양이다 (READ_MODEL_QUERIES.md:364-365).
- 조회가 해제·소비·시계 전이가 되지 않는다. `set_clock`은 조회가 아니라 명령이다 — 세 기계의 `REPLAYABLE`에 있다 (`reservation_fsm.py:55`, `resale_fsm.py:55`, `admission_fsm.py:55`; `def`는 `reservation_fsm.py:162`, `resale_fsm.py:167`, `admission_fsm.py:167`) (READ_MODEL_QUERIES.md:367).
- 기존 시험 증거: 시계 주입 전후의 `view` 관찰 `test_reservation_fsm.py:283`, `test_reservation_fsm.py:307` (READ_MODEL_QUERIES.md:366).
- 기존 view 메서드는 `_call`/`_accept`를 거치지 않고 저널에 쓰지 않는다 (예 `reservation_fsm.py:702-703`, `resale_fsm.py:656-657`). 여신 `view`·`view_claim`은 호출 전후를 `_guard`로 스스로 검사한다 (`credit_fsm.py:523-538`).

### 3.3 행위자 가시성 — fixture 배관

| 술어 | 배관 | RMQ 앵커 |
|---|---|---|
| 가시성 클래스는 `public listing`, `owner or holder`, `organizer`, `gate role`, `operator` 다섯 개뿐. 칸의 값은 `UNDETERMINED`(Astra) | 이 문서가 값을 정하지 않는다 | READ_MODEL_QUERIES.md:329-338, :386 |
| `actor`는 픽스처 문자열이지 인증 결과가 아니다 | `sourceAuthentication: FIXTURE_ONLY`가 원본 핀에 강제된다 `catalogue.py:76`, 생성기 `generate_client.mjs:128-129`, 문서 `openapi/README.md:52`, `openapi/README.md:70` | READ_MODEL_QUERIES.md:325-326 |
| fixture 문자열 비교로 행을 거를 수 있으나 그 거름은 접근 통제가 아니다. `role_authenticated`·`organizer_authenticated`는 참이 되지 않는다 | `NON_CLAIMS` `mock_gates.py:24-25` | READ_MODEL_QUERIES.md:340-341 |

## 4. 게이트·카탈로그 기작 노트

읽기 삽입 자체는 `read-model-reference`의 일이다. 이 절은 그 삽입이 지금 기작에서 어떤 모양이어야 하는지만 적고, 결정은 하지 않는다.

### 4.1 두 층의 명령 집합

- **잠금 핵심.** `reference/v0.3-rc1/protocol_contract.json`의 `commands`는 40개 (`constants.py:20`의 `CORE_COMMAND_COUNT`). 그 안에 `list_*`/`get_*`/`view_*`/`read_*`는 없다 (READ_MODEL_QUERIES.md:36-39). 이 파일은 `reference/v0.3-rc1/**` 잠금 아래 바이트 고정이며, 조회는 여기에 못 들어간다.
- **가산 FSM 핀.** `docs/contracts/openapi/fsm-command-contract.json`의 44개 `<machine>_<op>` 명령은 `canonical_fsm_document()` (`fsm_contract.py:149-197`)가 `MACHINE_TABLE` (`fsm_contract.py:26-84`)의 `replayable` 튜플에서 생성한다. view 연산은 어느 `REPLAYABLE`에도 없어 44개 전부 쓰기다. `drift_problems` (`fsm_contract.py:200-263`)는 명령 집합의 정확한 동등을 요구한다 (`fsm_contract.py:262`). 즉 읽기를 넣으려면 생성기·표를 확장하거나 새 핀을 더해야 하며, 그것은 카탈로그 바이트 변경이다.
- **동조 범프.** 그 변경이 일어나면 함께 움직이는 것: `FSM_COMMAND_COUNT` (`constants.py:21`), OpenAPI 핀의 `commandCount` 84 (`generate_client.mjs:150`), `components/schemas`·`x-kix-action-body-map`·봉투 `action` enum (`generate_client.mjs:166-195`), 재생성 `sdk/generated/catalogue.ts`와 `sdk-pin.json` (`check_sdk_client.py`의 바이트 동등), `check_openapi_contract.py`, `check_integration_gate_openapi.py`. 어느 하나만 바꾸는 삽입은 드리프트 검사에서 거절된다.

### 4.2 이름과 디스패치

- `_reject_names` (`catalogue.py:52-57`)는 소문자 식별자만 받는다. 13개 이름은 모두 그 규칙에 맞다.
- 디스패치는 `server.py:282`가 FSM 이름을 `_perform_fsm` (`server.py:337-355`)으로 돌린다. FSM 호출은 readiness 저널에 닿지 않고 저널이 켜져 있으면 `READINESS_FSM_REFUSED`로 거절된다 (`server.py:344`). 즉 이 경로로 들어온 읽기는 저널을 쓰지 않는 모양을 물려받는다.
- `FsmHost.call` (`fsm_host.py:80-92`)은 `machine.op(subject, **kwargs)`를 부른다. `subject`는 첫 파라미터다 (`fsm_contract.py:123-124`). 기존 view 시그니처(단일 subject, `view_presentation`/`view_credential`의 `version`·`holder_role` kwargs)는 이 호출 모양에 맞는다.
- `get_show`처럼 `<machine>_<op>` 접두가 없는 이름을 어떻게 명령 이름에 옮길지는 이 문서가 정하지 않는다. 기록만 한다 — 명령 이름 자체는 사용자 결정으로 닫혀 있다 (READ_MODEL_QUERIES.md:378).

## 5. 카탈로그 부재 확인

`protocol_contract.json`(40개)과 `fsm-command-contract.json`(44개)의 `commands` 키 어느 쪽에도 13개 조회 이름이 없다. `check_read_model_source_map.py`가 두 JSON을 직접 열어 부재를 다시 확인하고, 세 목록 이름의 `def`가 해당 모듈에 없음도 확인한다. 이 문서는 그 부재를 바꾸지 않는다.

## 6. 검사 표 (기계 판독)

아래 표는 `scripts/check_read_model_source_map.py`가 파싱한다. 규칙: `줄`이 양의 정수면 `파일`의 그 줄에 `포함 문자열`이 있어야 하고, `-`이면 그 파일 어디에도 없어야 한다. 실패는 앵커가 낡았다는 뜻이며 표면을 다시 대조해 문서를 고치라는 신호다 (AGENTS §8).

| 앵커 id | 대상 | 파일 | 줄 | 포함 문자열 |
|---|---|---|---|---|
| A01 | `list_shows` 모집단 | reference/booking_resale_admission/mock_gates.py | 97 | `self._shows` |
| A02 | `list_shows` 원소 | reference/booking_resale_admission/mock_gates.py | 732 | `def _show_view(` |
| A03 | `list_shows` FSM 등록 id | reference/booking_resale_admission/reservation_fsm.py | 155 | `self._shows` |
| A04 | `list_shows` 부재(목) | reference/booking_resale_admission/mock_gates.py | - | `def list_shows(` |
| A05 | `list_shows` 부재(FSM) | reference/booking_resale_admission/reservation_fsm.py | - | `def list_shows(` |
| A06 | `get_show` 원천 | reference/booking_resale_admission/reservation_fsm.py | 705 | `def view_show(` |
| A07 | `get_show` 스냅샷 | reference/booking_resale_admission/reservation_fsm.py | 908 | `def _show_snapshot(` |
| A08 | `get_show` 게이트 view | reference/booking_resale_admission/mock_gates.py | 633 | `def view_show(` |
| A09 | `get_booking` 원천 | reference/booking_resale_admission/reservation_fsm.py | 702 | `def view(` |
| A10 | `get_booking` view | reference/booking_resale_admission/reservation_fsm.py | 931 | `def _view(` |
| A11 | `list_bookings` 모집단 | reference/booking_resale_admission/reservation_fsm.py | 156 | `self._cases` |
| A12 | `list_bookings` 부재 | reference/booking_resale_admission/reservation_fsm.py | - | `def list_bookings(` |
| A13 | `get_right` 원천 | reference/booking_resale_admission/resale_fsm.py | 659 | `def view_right(` |
| A14 | `get_right` 티켓 view | reference/booking_resale_admission/resale_fsm.py | 1069 | `def _ticket_view(` |
| A15 | `get_right` 공개 권리 | reference/booking_resale_admission/resale_fsm.py | 1042 | `def _public_right(` |
| A16 | `get_right` 게이트 view | reference/booking_resale_admission/mock_gates.py | 783 | `def _right_view(` |
| A17 | `get_presentation` 원천 | reference/booking_resale_admission/resale_fsm.py | 664 | `def view_presentation(` |
| A18 | `list_open_listings` 모집단 | reference/booking_resale_admission/resale_fsm.py | 163 | `self._listings` |
| A19 | `list_open_listings` 원소 | reference/booking_resale_admission/resale_fsm.py | 1094 | `def _listing_view(` |
| A20 | `list_open_listings` 전이 집합 | reference/booking_resale_admission/resale_fsm.py | 49 | `OPEN_PHASES` |
| A21 | `list_open_listings` 부재 | reference/booking_resale_admission/resale_fsm.py | - | `def list_open_listings(` |
| A22 | `list_resale`는 쓰기 | reference/booking_resale_admission/resale_fsm.py | 259 | `def list_resale(` |
| A23 | `get_listing` 원천 | reference/booking_resale_admission/resale_fsm.py | 656 | `def view(` |
| A24 | `get_admission` 원천 | reference/booking_resale_admission/admission_fsm.py | 512 | `def view(` |
| A25 | `get_admission` view | reference/booking_resale_admission/admission_fsm.py | 1030 | `def _credential_view(` |
| A26 | `get_credential` 원천 | reference/booking_resale_admission/admission_fsm.py | 515 | `def view_credential(` |
| A27 | `get_settlement` 원천 | reference/settlement_f01_f03/settlement_fsm.py | 476 | `def view(` |
| A28 | `get_settlement` view | reference/settlement_f01_f03/settlement_fsm.py | 635 | `def _view(` |
| A29 | `get_settlement` 중첩 claim | reference/settlement_f01_f03/mock_settlement.py | 289 | `def view(` |
| A30 | `get_settlement` claim view | reference/settlement_f01_f03/mock_settlement.py | 298 | `def _view(` |
| A31 | `get_credit_advance` 원천 | reference/credit_advance_f04/credit_fsm.py | 523 | `def view(` |
| A32 | `get_credit_advance` view | reference/credit_advance_f04/credit_fsm.py | 760 | `def _view(` |
| A33 | `get_credit_advance` 감시 | reference/credit_advance_f04/credit_fsm.py | 830 | `def _witness(` |
| A34 | `get_credit_advance` 감시 | reference/credit_advance_f04/credit_fsm.py | 839 | `def _guard(` |
| A35 | `get_credit_claim` 원천 | reference/credit_advance_f04/credit_fsm.py | 530 | `def view_claim(` |
| A36 | `get_credit_claim` 목 호출 | reference/credit_advance_f04/credit_fsm.py | 620 | `def _mock_claim(` |
| A37 | `get_credit_claim` 목 view | reference/credit_advance_f04/mock_credit.py | 264 | `def view_claim(` |
| A38 | `get_credit_claim` claim view | reference/credit_advance_f04/mock_credit.py | 290 | `def _view_claim(` |
| P01 | `NON_CLAIMS` | reference/booking_resale_admission/mock_gates.py | 23 | `NON_CLAIMS` |
| P02 | 여신 `_flags` | reference/credit_advance_f04/mock_credit.py | 103 | `def _flags(` |
| P03 | 예약 canonical | reference/booking_resale_admission/reservation_fsm.py | 713 | `def canonical_state(` |
| P04 | 예약 journal | reference/booking_resale_admission/reservation_fsm.py | 710 | `def export_journal(` |
| P05 | 예약 시계 | reference/booking_resale_admission/reservation_fsm.py | 715 | `"logical_time_ms"` |
| P06 | 예약 게으른 만료 | reference/booking_resale_admission/reservation_fsm.py | 935 | `PRE_ISSUE` |
| P07 | 리셀 canonical | reference/booking_resale_admission/resale_fsm.py | 698 | `def canonical_state(` |
| P08 | 리셀 journal | reference/booking_resale_admission/resale_fsm.py | 695 | `def export_journal(` |
| P09 | 리셀 시계 | reference/booking_resale_admission/resale_fsm.py | 701 | `"logical_time_ms"` |
| P10 | 리셀 게으른 만료 | reference/booking_resale_admission/resale_fsm.py | 1098 | `OPEN_PHASES` |
| P11 | 검표 canonical | reference/booking_resale_admission/admission_fsm.py | 552 | `def canonical_state(` |
| P12 | 검표 journal | reference/booking_resale_admission/admission_fsm.py | 549 | `def export_journal(` |
| P13 | 검표 시계 | reference/booking_resale_admission/admission_fsm.py | 554 | `"logical_time_ms"` |
| P14 | 검표 게으른 만료 | reference/booking_resale_admission/admission_fsm.py | 1039 | `expired` |
| P15 | 정산 canonical | reference/settlement_f01_f03/settlement_fsm.py | 485 | `def canonical_state(` |
| P16 | 정산 journal | reference/settlement_f01_f03/settlement_fsm.py | 482 | `def export_journal(` |
| P17 | 정산 시계 부재 | reference/settlement_f01_f03/settlement_fsm.py | - | `logical_time_ms` |
| P18 | 여신 canonical | reference/credit_advance_f04/credit_fsm.py | 543 | `def canonical_state(` |
| P19 | 여신 journal | reference/credit_advance_f04/credit_fsm.py | 540 | `def export_journal(` |
| P20 | 여신 시계 부재 | reference/credit_advance_f04/credit_fsm.py | - | `logical_time_ms` |
| P21 | 목 canonical 부재 | reference/booking_resale_admission/mock_gates.py | - | `def canonical_state` |
| P22 | 목 journal 부재 | reference/booking_resale_admission/mock_gates.py | - | `def export_journal` |
| P23 | 목 canonical 부재 | reference/settlement_f01_f03/mock_settlement.py | - | `def canonical_state` |
| P24 | 목 journal 부재 | reference/settlement_f01_f03/mock_settlement.py | - | `def export_journal` |
| P25 | 목 canonical 부재 | reference/credit_advance_f04/mock_credit.py | - | `def canonical_state` |
| P26 | 목 journal 부재 | reference/credit_advance_f04/mock_credit.py | - | `def export_journal` |
| P27 | 게이트 시계 | reference/booking_resale_admission/mock_gates.py | 726 | `"logical_time_ms"` |
| P28 | 게이트 set_clock | reference/booking_resale_admission/mock_gates.py | 107 | `def set_clock(` |
| P29 | 예약 set_clock 명령 | reference/booking_resale_admission/reservation_fsm.py | 55 | `"set_clock"` |
| P30 | 리셀 set_clock 명령 | reference/booking_resale_admission/resale_fsm.py | 55 | `"set_clock"` |
| P31 | 검표 set_clock 명령 | reference/booking_resale_admission/admission_fsm.py | 55 | `"set_clock"` |
| P32 | 게으른 만료 시험 | reference/booking_resale_admission/test_reservation_fsm.py | 283 | `expired` |
| P33 | 게으른 만료 시험 | reference/booking_resale_admission/test_reservation_fsm.py | 307 | `expired` |
| G01 | 핵심 40 | integration_gate/constants.py | 20 | `CORE_COMMAND_COUNT = 40` |
| G02 | FSM 44 | integration_gate/constants.py | 21 | `FSM_COMMAND_COUNT = 44` |
| G03 | 이름 거절 | integration_gate/catalogue.py | 52 | `def _reject_names(` |
| G04 | 소문자 규칙 | integration_gate/catalogue.py | 54 | `islower()` |
| G05 | fixture 인증 라벨 | integration_gate/catalogue.py | 76 | `FIXTURE_ONLY` |
| G06 | FSM 개수 검사 | integration_gate/catalogue.py | 84 | `FSM_COMMAND_COUNT` |
| G07 | 기계 표 | integration_gate/fsm_contract.py | 26 | `MACHINE_TABLE` |
| G08 | subject는 첫 인자 | integration_gate/fsm_contract.py | 123 | `subject is None` |
| G09 | 카탈로그 생성 | integration_gate/fsm_contract.py | 149 | `def canonical_fsm_document(` |
| G10 | 드리프트 검사 | integration_gate/fsm_contract.py | 200 | `def drift_problems(` |
| G11 | 명령 집합 동등 | integration_gate/fsm_contract.py | 262 | `expected_commands` |
| G12 | host 호출 | integration_gate/fsm_host.py | 80 | `def call(` |
| G13 | host 디스패치 | integration_gate/fsm_host.py | 90 | `method(subject, **kwargs)` |
| G14 | FSM 디스패치 | integration_gate/server.py | 282 | `fsm_name_set` |
| G15 | FSM 수행 | integration_gate/server.py | 337 | `def _perform_fsm(` |
| G16 | 저널 거절 | integration_gate/server.py | 344 | `READINESS_FSM_REFUSED` |
| G17 | 생성기 fixture 검사 | sdk/generate/generate_client.mjs | 128 | `FIXTURE_ONLY` |
| G18 | 생성기 개수 검사 | sdk/generate/generate_client.mjs | 150 | `commandCount` |
| G19 | 생성기 action enum | sdk/generate/generate_client.mjs | 184 | `actionEnum` |
| G20 | OpenAPI fixture 라벨 | docs/contracts/openapi/README.md | 70 | `FIXTURE_ONLY` |
| G21 | OpenAPI 비인증 설명 | docs/contracts/openapi/README.md | 52 | `FIXTURE_ONLY` |
| R01 | 13개 이름 | docs/contracts/READ_MODEL_QUERIES.md | 15 | `list_shows` |
| R02 | `list_shows` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 91 | `list_shows` |
| R03 | `get_show` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 105 | `get_show` |
| R04 | `get_booking` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 118 | `get_booking` |
| R05 | `list_bookings` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 134 | `list_bookings` |
| R06 | `get_right` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 147 | `get_right` |
| R07 | `get_presentation` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 160 | `get_presentation` |
| R08 | `list_open_listings` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 172 | `list_open_listings` |
| R09 | `get_listing` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 186 | `get_listing` |
| R10 | `get_admission` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 197 | `get_admission` |
| R11 | `get_credential` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 209 | `get_credential` |
| R12 | `get_settlement` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 221 | `get_settlement` |
| R13 | `get_credit_advance` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 235 | `get_credit_advance` |
| R14 | `get_credit_claim` 명세 | docs/contracts/READ_MODEL_QUERIES.md | 249 | `get_credit_claim` |
| R15 | 항상 거짓 플래그 목록 | docs/contracts/READ_MODEL_QUERIES.md | 274 | `role_authenticated` |
| R16 | 정산 거짓 플래그 | docs/contracts/READ_MODEL_QUERIES.md | 233 | `funds_executed` |
| R17 | 여신 `_flags` | docs/contracts/READ_MODEL_QUERIES.md | 238 | `_flags` |
| R18 | 비변경 술어 | docs/contracts/READ_MODEL_QUERIES.md | 361 | `canonical_state()` |
| R19 | 여신 비변경 `_guard` | docs/contracts/READ_MODEL_QUERIES.md | 362 | `_guard` |
| R20 | 게으른 만료 금지 | docs/contracts/READ_MODEL_QUERIES.md | 364 | `게으른 만료` |
| R21 | 만료 시험 인용 | docs/contracts/READ_MODEL_QUERIES.md | 366 | `test_reservation_fsm.py` |
| R22 | `set_clock`은 명령 | docs/contracts/READ_MODEL_QUERIES.md | 367 | `set_clock` |
| R23 | 가시성 클래스 | docs/contracts/READ_MODEL_QUERIES.md | 334 | `public listing` |
| R24 | fixture는 접근 통제 아님 | docs/contracts/READ_MODEL_QUERIES.md | 340 | `접근 통제` |
| R25 | fixture 라벨 근거 | docs/contracts/READ_MODEL_QUERIES.md | 326 | `FIXTURE_ONLY` |
| R26 | 가시성 값 미정 | docs/contracts/READ_MODEL_QUERIES.md | 386 | `UNDETERMINED` |
| R27 | 열린 단계 `NOT_BOUND` | docs/contracts/READ_MODEL_QUERIES.md | 388 | `NOT_BOUND` |
| R28 | `list_resale`는 쓰기 | docs/contracts/READ_MODEL_QUERIES.md | 43 | `list_resale` |
| R29 | 쓰기 본문 대체 금지 | docs/contracts/READ_MODEL_QUERIES.md | 49 | `대응` |
| R30 | `OPEN_PHASES` 인용 | docs/contracts/READ_MODEL_QUERIES.md | 175 | `OPEN_PHASES` |
| R31 | FSM `view_show`가 뒷받침 | docs/contracts/READ_MODEL_QUERIES.md | 110 | `lifecycle_authority` |
| R32 | F04 인용만 | docs/contracts/READ_MODEL_QUERIES.md | 17 | `인용` |
| R33 | `accepted_through` 제안 | docs/contracts/READ_MODEL_QUERIES.md | 281 | `accepted_through` |
| R34 | 핵심 40개 기록 | docs/contracts/READ_MODEL_QUERIES.md | 36 | `40` |
| R35 | 정산 시계 부재 | docs/contracts/READ_MODEL_QUERIES.md | 226 | `logical_time_ms` |
| R36 | claim dict에 권위 키 없음 | docs/contracts/READ_MODEL_QUERIES.md | 253 | `lifecycle_authority` |

## 7. 남은 불확실과 분류

- `NONE` 뒷받침 목록 3개의 구현 모양 (새 열거 view를 어느 기계·목에 두는지)은 `read-model-reference`가 Astra 값과 함께 정한다. 이 문서는 모집단이 존재함만 기록한다.
- commerce 메서드 시그니처는 RMQ §0.2대로 UNVERIFIED다 (READ_MODEL_QUERIES.md:53-59). 이 문서도 그 한계를 계승한다.
- 목( mock )의 비변경 표면은 계약 미정의 관측이다 (§1, 분류 B). 목에 `canonical_state`/`export_journal`를 새로 요구하지 않는다.
- 기존 커버리지: 점 조회 표면은 각 FSM 시험이 이미 다룬다 (예 `test_reservation_fsm.py:283,307`). 목록·커서·가시성 행렬은 구현 전이며 시험도 없다 (READ_MODEL_QUERIES.md:403). 이 문서는 시험을 추가하지 않고 존재 검사(`check_read_model_source_map.py`) 하나만 둔다.
- 이 문서는 운영 준비, 체인 최종성, 은행 exactly-once, 내구 현재성, 프로토콜 검증 완료를 주장하지 않는다 (READ_MODEL_QUERIES.md:393-405 계승).
