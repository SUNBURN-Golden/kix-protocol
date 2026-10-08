# 어댑터 전송·이벤트·결제·operation 정체성 계약 — 초안 0.1

문서일: **2026-10-08**. 작성 기준 main: `7481b0e16ce9b903abbffa62249bb91cd9e63cfe`.
상태: **계약 초안 제출; 구현·schema·wire 아님.**
노드: `k1-adapter-event-identity` (I06, document only). 이 파일은 사용자 병합으로만 효력이 생긴다.
병합 경계는 [PROGRAM_ASTRA_DELEGATION](../aiops/PROGRAM_ASTRA_DELEGATION.md) 35행이다.
그 행은 `contract_change=YES`, 병합 주체 **대표님**이다. 노드 입력도 `user_merge=true`다.
[PROGRAM_ROADMAP_20260930](../decisions/PROGRAM_ROADMAP_20260930.md) §3.3 표의 같은 노드는 여전히
「자동(M1·Fable)」이다. 이 초안은 로드맵 표가 아니라 위임 표와 노드 입력을 따른다.
로드맵 표의 정합은 이 노드가 고치지 않는다.

정본으로 참조만 하고 본문을 바꾸지 않는 문서:
[STATE_LIFECYCLE](STATE_LIFECYCLE.md) 초안 0.6,
[PG_TOSS_CARD_PROFILE](PG_TOSS_CARD_PROFILE.md),
[runtime/CANONICAL_BINARY_BCS_V1.md](../../runtime/CANONICAL_BINARY_BCS_V1.md),
[TOSS_METHOD_EXPANSION_REVIEW](../reviews/TOSS_METHOD_EXPANSION_REVIEW.md).

## 1. 범위와 비주장

이 초안은 토스페이먼츠 잠정 선택, 국내 KRW 일반 카드 한 경로에서
전송·원문 증거·이벤트 항목·결제·경제 operation이 어떻게 묶이는지만 정한다.
프로파일 §4대로 일반 결제 웹훅 서명을 가정하지 않는다. 서명이 없다는 뜻도 아니다.
서명 범위는 I04로 열려 있다.

하지 않는 것:

- 어댑터, inbox, outbox, 조회 클라이언트, 바인딩 저장소의 코드.
- Rust trait, wire schema, domain/schema id 할당.
- 커널 필드·enum·명령의 추가. `UNMATCHED`는 계약 용어다.
- 보존 기간. 그 숫자는 `k2-retention-proposal`의 몫이며 여기서 만들지 않는다.
- 간편결제·가상계좌의 수단별 매핑. [수단 확장 검토](../reviews/TOSS_METHOD_EXPANSION_REVIEW.md)가
  그 차이를 연다. 이 초안의 정체성 규칙은 그 수단을 막지 않게만 둔다.
- 실자금, 실 PG/은행/KYC 호출, 공개 엔드포인트, Sui testnet/mainnet.

비주장:

- 토스의 실제 동작을 검증하지 않았다. 공개 문서의 기존 확인일 2026-09-17을 재확인하지 않았다.
- 서명, 내구성, exactly-once, 제공자 최종성을 주장하지 않는다.
- production readiness를 주장하지 않는다.
- I06은 사용자가 이 초안을 병합하고, 토스가 TM04와 I04에 답하기 전에는 완결이 아니다.

## 2. 정체성 용어

이름은 이 초안에서 고정한다. 커널 표면은 잠금
`runtime/crates/kix-kernel/src/lib.rs` blob `69564b166f0c27f9af5d8422f0a466b18d74c20f`의
공개 타입이다. `KixId`는 16바이트다.

| 이름 | 의미 | 사는 곳 |
|---|---|---|
| `TransmissionId` | 제공자 전달 한 건. 재전달을 가로질러 같은 값이 유지되는지는 UNDETERMINED (TM04). | 보관 메타데이터만. 이벤트 ID가 아니다. |
| `RawEvidenceRef` | 원문 바이트·헤더·수신 시각의 내용 해시와 위치. | 보관(custody) |
| `PaymentRef` | `(provider, account/MID, environment, paymentKey, orderId)`. 결제 정체성이며 이벤트 ID가 아니다. | 어댑터 결합 |
| `ProviderFactKey` | 제공자가 항목마다 안정적으로 주는 키(예: transaction key). 어느 필드가 그 키인지는 UNDETERMINED. | 어댑터 |
| `EventItemId` | 커널 `event_id: KixId`로 매핑되는 지속 별칭. | 커널 경계 |
| `OperationRef` | 커널 `ProviderOperation { provider, account, operation }`. KIX가 송신 전에 만드는 capture 한 건. 결제 전체가 아니다. | 커널 |

커널 관측은 `CaptureObservation { event_id, operation, amount, evidence_hash }`다.
`observe_capture`의 중복 키는 `(provider, account, event_id)`다.
같은 키가 다시 오면 관측 전체(`event_id`, `operation`, `amount`, `evidence_hash`)를 비교한다.

## 3. 관계와 기수

| 관계 | 기수 | 규칙 |
|---|---|---|
| 전송 → 이벤트 항목 | 다대일 | 같은 사실의 재전달·관리자 재시도·유실 ACK는 전송을 늘릴 수 있다. 이벤트 항목은 늘리지 않는다. |
| 결제 → 이벤트 항목 | 일대다 | 한 `PaymentRef`가 상태 변화와 `cancels[]`의 항목을 여럿 가진다. `paymentKey`는 상태가 바뀌어도 같다. |
| operation → 결제 | 일대영 또는 일대일 | 한 `OperationRef`는 많아야 하나의 `PaymentRef`에 묶인다. 송신 전에 KIX가 operation을 만들고, 커널은 그 operation을 한 주문에만 묶는다. |
| operation → 주문 | 일대일 | 이미 묶인 operation으로 둘째 주문을 열지 않는다. 커널 거절은 `OperationAlreadyBound`다. |

같은 operation에 다른 `paymentKey`가 오면 결합 충돌이다. 새 operation도 새 주문도 만들지 않고
검토·대사로 보낸다. 커널에 그 사실을 새 capture로 넣지 않는다.

프로파일 §6을 그대로 둔다. `paymentKey` 단독, `orderId` 단독, `lastTransactionKey` 단독은
이벤트 ID가 아니다. `lastTransactionKey`는 마지막 거래를 가리키므로 고정 capture ID로 쓰지 않는다.
한 Payment의 `cancels[]`는 독립 결제 batch가 아니다.

## 4. `EventItemId`와 `evidence_hash` 유도

### 4.1 커널이 강제하는 두 점

1. `evidence_hash`는 인증된 조회의 **정규화된 사실**에 대해 계산한다.
   원문 전달 바이트나 헤더에 대해 계산하지 않는다.
   같은 `event_id`에서 `amount` 또는 `evidence_hash`만 달라도 `observe_capture`는
   `Conflict`를 내고, 그 키가 묶는 주문을 격리한다.
   무해한 재전달의 바이트 차이가 주문을 격리하면 안 된다.
   원문 바이트는 `RawEvidenceRef`로 따로 보관한다.
2. `event_id`는 제공자에서 안정적인 필드만으로 만들고, provider·account·environment·
   프로파일 버전으로 범위를 한정한다.
   전송 ID, 수신 시각, 재시도 횟수, 상태 문자열만으로는 만들지 않는다.

상태가 `DONE`에서 `CANCELED`로 바뀌면 그것은 같은 항목의 덮어쓰기가 아니다.
새 이벤트 항목이다. 원래 capture 항목의 `evidence_hash`를 최신 snapshot으로 다시 계산하지 않는다.
다시 계산하면 같은 `event_id`의 내용 변경이 되어 `Conflict`가 된다.

### 4.2 넣으면 안 되는 입력

`EventItemId`에 다음만으로, 또는 이들만의 조합으로 만들지 않는다.

- `TransmissionId`, 수신 시각, 재시도 횟수
- `paymentKey` 단독, `orderId` 단독, `lastTransactionKey` 단독
- 상태 문자열 단독
- 멱등 키, ACK 시각, 어댑터 프로세스 ID

### 4.3 반드시 넣는 범위

provider, account(MID의 별칭), environment, 프로파일 버전.
커널 키는 `(provider, account, event_id)`뿐이다. environment와 프로파일 버전은
별도 커널 필드가 아니다. 어댑터는 두 환경을 같은 account 별칭에 겹치지 않게 하고,
`EventItemId`를 자르거나 별칭을 만들기 **전에** 그 범위를 입력에 넣는다.
API·계약 버전, 상품, 결제수단, operation 종류는 프로파일 §6대로 증거 범위에 남는다.
그 값을 커널 필드로 늘리지는 않는다.

### 4.4 정규화된 사실

인증된 조회 응답에서 만든다. 미검증 웹훅 본문에서 만들지 않는다.

- 금액은 KRW 원 단위 정수다. JSON number를 `f64`로 바꾸지 않는다.
- 시각은 원문 텍스트와, 있으면 offset을 함께 보존한다. offset이 없는 `createdAt`에
  시간대를 가정하지 않는다.
- 통화, 수단, 상태, 취소 항목의 금액은 그 항목의 사실에 남긴다.
- 최신 snapshot 전체가 과거 모든 항목의 정의는 아니다. 항목마다 그 항목의 정규화 사실을 해싱한다.

`evidence_hash`는 그 정규화 사실의 SHA-256이다.
[KIX-BCS1](../../runtime/CANONICAL_BINARY_BCS_V1.md)에서 `canonical_hash`는 envelope 바이트의 SHA-256이고,
domain/schema registry는 따로 버전된다. 이 초안은 domain id와 schema id를 **할당하지 않는다**.
테스트용 `65535/65535`를 쓰지 않는다. 바이트 레이아웃이 정해지기 전에는
이 규칙이 논리 정체성이지 운영 해시 구현이 아니다.

### 4.5 선택지 — 채택하지 않음

어느 쪽도 이 초안이 고르지 않는다. 권장만 적고 §9에 둔다.

| | `EventItemId`의 원천 | 결과 |
|---|---|---|
| A (권장) | 토스가 항목 단위로 불변·유일하다고 확인한 `ProviderFactKey` (TM04) | 같은 키의 내용 변경은 같은 `event_id`와 다른 `evidence_hash`/`amount`가 되어 `Conflict`다. 상태 변화·부분 취소는 다른 키이므로 새 항목이다. |
| B (대체) | 정규화 사실의 내용 주소 | 내용이 바뀌면 키가 바뀐다. 같은 항목의 정정이 `Conflict`가 되려면, 내용 주소 위에 다시 「같은 항목」 규칙이 필요하다. 그 규칙은 이 초안이 만들지 않는다. |

`KixId`가 16바이트이므로 외부 키를 그대로 넣지 못한다.

| | 별칭 | 결과 |
|---|---|---|
| 별칭 표 (권장) | 외부 키 전체와 `EventItemId`의 지속 표. 넣을 때 충돌을 검사한다. | 잘림 충돌을 표가 거부한다. 표의 내구 저장은 5단계이며 이 초안이 만들지 않는다. |
| 결정적 유도 | SHA-256을 128비트로 자른 값. 불일치 시 외부 키 전체를 다시 대조한다. | 표가 없어도 재계산할 수 있다. 충돌 검사 없이 자르면 다른 사실이 한 `event_id`가 된다. |

## 5. 경우 행렬

각 행의 마지막 칸은 그 경우에 일어나면 안 되는 일이다.

| 입력 | 정체성 결과 | 커널에 보이는 결과 | 절대 금지 |
|---|---|---|---|
| 같은 전송이 다시 도착 | 같은 `EventItemId`, 같은 `evidence_hash`. 새 `RawEvidenceRef`만 추가할 수 있다. | 관측 전체가 같으면 기존 결과를 다시 반환하고 `ctx.now_ms`만 나아간다. capture를 다시 적용하지 않는다. | 둘째 주문, 둘째 operation, 원문 바이트 차이를 `evidence_hash`에 넣어 만드는 `Conflict`. |
| 새 전송, 같은 사실 | 전송 ID는 달라도 이벤트 항목은 하나. | 위와 같다. 중복 키는 전송이 아니라 `(provider, account, event_id)`다. | 전송마다 새 `event_id`. |
| 관리자 「다시 시도」, 또는 수신 뒤 응답만 유실 | 새 전송일 수 있다. 사실은 기존 항목이다. 진행 중 자동 시도를 무효화했다는 공개 설명은 경제 효과의 취소가 아니다. | 같은 관측의 재수락, 또는 아직 없는 항목의 첫 관측. 새 operation 없음. | 유실 ACK를 미적용으로 보고 같은 operation을 다시 보내거나 둘째 결제를 여는 일. |
| 같은 사실의 snapshot 반복 | 정규화 사실이 같으면 `EventItemId`와 `evidence_hash`가 같다. | 재수락. 관측 개수는 늘지 않는다. | snapshot 시각이나 조회 횟수로 새 항목을 만드는 일. |
| 같은 `event_id`, 다른 내용 | 원래 항목을 유지한다. 정정이 아니다. | `Conflict`. 묶인 주문을 격리한다. 원래 capture 금액은 남는다. 용량이 부족하면 `Err(Capacity)`여도 격리와 논리 시각 진행은 이미 적용된 결과다. | 제자리 수정, 원래 capture 삭제, 둘째 주문, `Capacity`를 전부 롤백으로 보는 일. |
| 이후 상태 변화 (예: DONE→CANCELED) | **새** 이벤트 항목. 원래 capture 항목은 그대로다. | 새 `event_id`. 금액이 이미 잡힌 주문에 같은 금액이면 `DuplicateEffect`, 다른 금액이면 `Review`와 `review_required`. 어느 쪽이든 원래 capture를 지우지 않는다. | 상태 문자열만으로 기존 `event_id`를 재사용하거나, 취소를 「capture가 없었다」로 바꾸는 일. |
| 부분 취소 | `cancels[]`의 그 취소는 반환 종류의 **별도** 항목이다. | 별도 `event_id`. 원 capture 항목과 공존한다. | 부분 취소를 원 capture의 `evidence_hash` 갱신으로 흡수하는 일. |
| 순서가 뒤집힘, 또는 새 snapshot 뒤에 옛 snapshot | 둘 다 보관한다. 더 이른 발생 시각이 더 늦은 항목을 지우지 않는다. | 이미 본 같은 관측은 재수락이다. 시계를 과거로 돌리면 `ClockRegression`이며 상태를 바꾸지 않는다. 얼마나 기다릴지는 숫자를 정하지 않는다 (§9). | 옛 snapshot으로 새 사실을 덮어쓰기, `ctx.now_ms`를 되돌리기. |
| 만료 뒤 늦은 capture | 발생 시각과 적용 시각을 분리해 보관한다. | 첫 capture는 보존되고, `ctx.now_ms >= expires_at_ms`이면 `ReturnRequired`. 재고를 가진 경우에만 그 주문의 재고를 놓는다. | `ctx.now_ms`를 승인 시각으로 바꿔 더 이른 관측처럼 보이게 하는 일. `ReturnRequired`를 환불 완료로 보는 일. |
| 묶이지 않은 사실 | 계약 용어 **UNMATCHED**. 주문을 만들지 않는다. | 커널 enum이 아니다. 이 사실을 `observe_capture`에 넣지 않는다. 넣으면 `UnknownOperation`이며, 그 오류로 주문을 만들지 않는다. | UNMATCHED를 커널 변이로 추가하거나, 맞는 주문을 추측해 생성하는 일. |
| 다른 MID, 환경, 또는 수단 | 다른 범위의 사실로 보관하고 대사만 한다. | 새 권리·새 송신을 승인하지 않는다. 카드 프로파일의 부재 경로를 다른 수단에 복사하지 않는다. | 다른 MID를 같은 account 별칭에 합치거나, 범위 밖 수단으로 권리를 발행하는 일. |

`DuplicateEffect`는 다른 이벤트 항목이 이미 잡힌 같은 금액이다.
같은 항목의 재전달(관측 전체 일치)과는 다른 경계다.
수명 계약 §3의 문장 그대로, event identity와 경제 operation identity는 서로 다른 중복 경계다.

## 6. 시각과 결합 기록

### 6.1 세 시각

수명 계약 §5.7을 따른다. 세 시각을 하나로 합치지 않는다.

| 시각 | 무엇 | 규칙 |
|---|---|---|
| 발생 | 제공자 원문 텍스트, 있으면 offset, 해석 근거 | offset이 없는 `createdAt`에 시간대를 가정하지 않는다. |
| 수신 | 어댑터가 원문을 받은 시각 | `RawEvidenceRef`에만 둔다. `event_id`에 넣지 않는다. |
| 적용 | 드라이버의 `ctx.now_ms` | 커널이 만료를 가르는 시각이다. 발생 시각으로 대체하지 않는다. |

### 6.2 송신 전에 남길 결합

한 operation을 보내기 전에 다음 넷을 지울 수 없는 기록으로 남긴다.

`OperationRef` ↔ 주문 `orderId` ↔ `PaymentRef`의 `paymentKey` ↔ 그 송신의 멱등 키.

요구만 정한다. 저장 장치는 정하지 않는다. 내구 기록은 Track K 5단계이며 아직 없다.
메모리 테스트의 잔존은 이 요구의 충족이 아니다.

토스 공개 규격의 멱등 키 15일과 첫 응답 재사용은 프로파일 §2의 값이다.
그 15일을 KIX 보존 기간으로 바꾸지 않는다 (I07·I08).
같은 UNKNOWN operation을 새 멱등 키나 새 PG의 새 요청으로 다시 보내지 않는다.

## 7. 교체 가능한 PG 경계

프로파일 §7의 표를 정체성에 적용한다. 반환형·trait·schema는 여전히 없다.

| 프로파일 §7의 책임 | 정체성에 적용하는 규칙 |
|---|---|
| 이벤트 정체성 정규화 | 제공자 필드 매핑은 어댑터 안이다. 공통 규칙은 원이벤트와 operation의 분리, 같은 identity의 내용 변경 거절, 원문 참조의 분리이다. |
| 서명·인증 | 서명 유무는 I04로 남긴다. 미검증 신호는 사실이 아니다. 사실은 계정에 묶인 인증 조회다. |
| 금액·시각 변환 | §4.4의 정수·원문 시각. 제공자 JSON 필드 이름은 코어에 박지 않는다. |
| 조회 경로 | `paymentKey`/`orderId` 조회는 원operation에 묶인다. 조회 실패는 UNKNOWN을 풀지 않는다. |
| 종결 판정 | 수단별 status 의미는 프로파일과 I05에 남긴다. 이 초안은 종결 조건을 추가하지 않는다. |

provider는 모든 키의 일부다. PG를 바꿔도 옛 키와 충돌하지 않는다.
이미 보낸 UNKNOWN과 그 증거·재시도·대사 책임은 원 account에 남는다.
새 provider는 새로 승인된 거래 범위에만 쓴다.
이 경계는 저장 backend 선택이 아니다.

## 8. UNDETERMINED 목록

답을 받지 않았다. 질문의 담당과, 답이 없을 때 막히는 것만 적는다.

| 항목 | 질문 | 담당 | 막히는 것 |
|---|---|---|---|
| I02 | 실제 MID, 환경, API·계약 버전, 허용 상품 | 사용자, 토스 계약/기술 | 그 범위의 운영 결합. 문서 초안은 막지 않는다. |
| I03 | 리셀·금융 대금의 가맹 범위 | 사용자, 토스 영업 | 그 대금의 운영 수취. |
| I04 | 일반 결제 웹훅 서명의 필드·키 범위 | 토스 기술 (질문지 5) | 웹훅 단독 인증. 서명 미확인을 서명 없음으로 바꾸지 않는다. |
| I05 | 최종 실패, void, 취소의 증거 의미 | 토스 기술 | 그 상태 문자열만으로 하는 종결·삭제. |
| I08 | 조회·증거 보존과 키 교체 예외 | 토스, PG 계정 운영 | 보존 기간·교체 뒤 UNKNOWN 처리의 확정. 15일을 보존 기간으로 쓰지 않는다. |
| TM04 | `transactionKey`와 전송 ID가 불변·유일한지, 재전달·재조회·재발급에서 무엇이 남는지 | 토스 기술 | 선택지 A의 채택, I06 완결 주장. |
| TM05 | 웹훅 인증·서명/secret 범위, 키 교체, 재전달, 조회 이력의 접근·보존. 카드 멱등 키가 승인·취소 API에도 적용되는지 | 토스 기술/보안 (I04/I07/I08/I13) | 인증된 사실·재송신 안전·증거 완전성 주장. |
| 서명 범위 | I04와 같다. 일반 카드 본문 전체의 서명 여부를 이 초안이 정하지 않는다. | 토스 기술 | 웹훅 바이트를 사실로 승격하는 일. |

[FIRST_BATCH_OPEN_INPUTS](FIRST_BATCH_OPEN_INPUTS.md)의 「새로 실입력까지 완결된 행: 0」과
13행 집계는 이 초안이 바꾸지 않는다. I06 행은 초안 제출이며 미완결이다.

## 9. DECISION_REQUIRED · Astra 목록

아래는 이 문서 안의 결정 요청이다. 값을 고르지 않았고, 루트 결정 파일을 만들지 않는다.
고르는 주체는 Astra(아키텍처 권한)이고, 계약 병합은 사용자다.

| 결정 | 선택지 | 이 초안의 권장 | 지금 하지 않는 것 |
|---|---|---|---|
| `EventItemId` 원천 | A 제공자 안정 키 / B 내용 주소 | A. TM04가 키를 확인해 주기 전에는 A도 쓸 수 없다. | 둘 중 하나를 효력 있는 규칙으로 채택. |
| 16바이트 별칭 | 지속 별칭 표 / SHA-256 128비트 절단 후 전체 키 대조 | 별칭 표와 충돌 검사. | 표나 절단 알고리즘의 구현, schema 할당. |
| domain/schema id | 정규화 사실의 KIX-BCS1 registry 할당 | 할당은 별도 계약 변경. | id 숫자를 만들거나 `65535/65535`를 재사용. |
| 역순 사실의 대기·만료 | 제품 정책 값 | 숫자를 권장하지 않는다. 두 사실은 대기 값과 무관하게 보존한다. | 대기 밀리초, 재시도 상한, SLO. |

새 커널 명령이나 `UNMATCHED` enum이 필요해지면 그 역시 DECISION_REQUIRED · Astra다.
이 초안은 그 명령을 도입하지 않는다.

## 10. 대응·비주장·버전

### 10.1 이미 있는 커널 회귀

어댑터 쪽 유도·결합·UNMATCHED를 이 테스트들이 증명하지는 않는다.
증명하는 것은 잠금 커널의 관찰 가능한 경계뿐이다.

| 요구 | 테스트 | 판정 |
|---|---|---|
| 이벤트 중복과 경제 효과 중복의 분리 | `transitions.rs::event_deduplication_and_economic_effect_deduplication_are_separate` | 충분 (커널) |
| 같은 이벤트·다른 payload는 `Conflict`이고 원래 capture가 남음 | `transitions.rs::same_event_different_payload_preserves_conflicting_evidence` | 충분 (커널) |
| 같은 관측의 재수락은 시각만 진행 | `transitions.rs::accepted_duplicate_observation_advances_time_without_reapplying_capture` | 충분 (커널) |
| 한 외부 operation이 두 주문을 열지 못함 | `transitions.rs::duplicate_external_operation_cannot_fund_two_orders` | 충분 (커널) |
| 원래 이벤트·명령 재생이 격리를 풀지 않음 | `quarantine_capacity.rs::original_event_and_command_replays_never_clear_quarantine` | 충분 (커널) |
| `event_id`/`evidence_hash` 유도, 송신 전 결합, UNMATCHED | 없음. 어댑터가 없다. | 미커버 |
| 토스 ID 안정성·서명 범위 | 없음. I02–I05, I08, TM04, TM05. | 미커버 |

### 10.2 버전

| 초안 | 내용 |
|---|---|
| 0.1 — 2026-10-08 | 첫 제출. 전송·원문·이벤트 항목·결제·operation의 관계, 중복·정정·PG 경계, 미확정과 Astra 결정 목록. |

본문이 바뀌면 0.1을 고치지 않고 다음 번호를 쓴다.
사용자 병합 전의 파일은 초안이며, 병합이 I06 완결은 아니다.
