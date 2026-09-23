# KIX 운영 플랫폼·Rust 서비스·업무 흐름 설계

공통 명칭·체인/원장/은행 간 순서와 권위는 [CROSS_BOUNDARY_CONTRACTS](CROSS_BOUNDARY_CONTRACTS.md)를 함께 따른다. 본문 논리 상태와 토큰 표현을 별도 경제 자산으로 중복 계상하지 않는다.

상태: 제안 설계. 구현 완료·실거래 승인·backend 채택·R2 착수 승인이 아니다.
검토 기준: main `6dbf8dfed6ee790e2ee56b49a75b727edd9db977`의 `docs/DEVELOPMENT_PLAN.md`, `docs/decisions/AUTHORITY_MODEL_1.md`, `docs/contracts/STATE_LIFECYCLE.md` 0.6 및 2026-09-22 검토 청사진.
잠금 v4 커널과 회귀를 변경하지 않는다. 문서·작업 흐름 제안이 기존 승인 범위를 확장하지 않는다. 최신 자동화 PR #32의 구현 상태를 이 문서에서는 재감사하지 않는다.

## 1. 그림을 제품 구조로 옮기는 원칙

사용자 그림의 운영 플랫폼은 KIX 프로토콜의 첫 소비자이며 여러 판매 채널 가운데 하나다. 플랫폼의 예매 UI·CRM·대출 심사 화면은 바뀔 수 있지만, 동일 권리·가격 정책·재고·명령·금액의 검증 규칙은 SDK/API와 Rust/Move 계약에 둔다. 공식 앱만 사용할 때 성립하는 안전 보장은 프로토콜 보장이 아니다. 독립 파트너 클라이언트도 같은 계약을 통과해야 한다.

그림의 Sui/Move는 단순 감사 로그 부착물이 아니다. 승인된 모델 1에 따라 재고와 관람권 발행·소유·이전·소비의 원권위를 맡는다. 오프체인 Rust는 검증된 배타 위임 범위의 예약·판매 약정과 결제·배분·채무·대사를 담당한다. 은행의 실제 송금 사실, 법률상 채권 효력, 공연 이행 사실까지 체인 원권위로 옮기지 않는다.

처음부터 모든 논리 모듈을 별도 microservice로 만들 필요는 없다. Rust 모듈 경계와 권한·트랜잭션 경계부터 명시하고, 배포 단위는 거래 처리, 외부 어댑터, 조회/운영, 분석을 분리한다. 하나의 DB/프로세스를 쓰더라도 위임 범위·임차인별 권한과 경제 원자성은 독립적으로 검증한다. backend 비교 전 PostgreSQL이나 자체 복제 엔진을 최종 경제 정본으로 확정하지 않는다.

## 2. 사용자·포털·서비스 경계

| 사용자/포털 | 주요 화면과 명령 | 보이는 사실 | 직접 가질 수 없는 권한 |
|---|---|---|---|
| 구매자·관람객 | 공연 탐색, 좌석/GA, 견적, 결제, 티켓 지갑, 양도/리셀, 취소·환불 이력 | 예약·결제·발권 상태, 현재 권리, 미해결 사유, 반환 진행 | 임의 결제 성공 선언, 타인 재고 조작, 정책 우회 발권 |
| 리셀 판매자 | 판매 가능성 확인, 가격·만료 조건, 등록/철회, 이전·판매대금 지급 현황 | listing 예약, 구매자 결제, 권리 이전, 판매자 지급을 각각 표시 | 구매자 개인정보 전체 조회, 취소된 권리 판매, 미확정 수익 인출 |
| 주최자 | 공연/가격/정책 작성, 판매 배정, 채널 위임, 정산내역, 취소, 자금 선지급 신청 | 실제 판매/발권/수취/미지급·환불노출, 계약상 분배 | 자기 대출 단독 승인, refund reserve 임의 해제, 타 주최자 원장 조회 |
| 공연장·검표 운영자 | 회차·구역·게이트, 스캐너 권한, 검표 현황, 오류 처리 | 자신의 회차 권리 유효성·사용 상태, 필요한 최소 식별정보 | 판매대금·여신·캠페인 고객 원문 전체 접근 |
| 마케팅 담당자 | 동의 기반 segment, 선예매 자격, 쿠폰·캠페인·추천 보상, 성과 | 허용된 개인/집계 데이터, 발행 예산, 정책 버전 | 당첨/쿠폰을 DB 직수정하여 한도 우회, 신용심사정보 열람 |
| 자본 공급자 | 자금 약정·여신 한도, 자산별 적격채권, 실행 승인, 회수·손실·예외 | 자신의 계약 포트폴리오, 검증 시점·미확정/부담/환불노출 | 고객 티켓 소유권 자동 취득, 다른 공급자 전용 정보, 단독 은행 지급 승인 |
| 심사·리스크 | 차주/공연 심사, 자료 부족 큐, facility/covenant, borrowing base, 한도 부족·부담 충돌 | 원천 자료·정책 계산·모델 버전·수기 조정 이유 | 심사와 지급·수취계좌 변경을 한 사람/AI가 전부 승인 |
| Treasury·정산 | PG/은행 대사, 지급 승인, 분배, 미배분금·환불자금·자본회수 | 원금/수수료/수익권의 확정 및 보류, 계좌 검증 상태 | 은행 미확인 출금을 장부에서 완료로 조작 |
| 고객지원·분쟁 | 주문 타임라인, 본인 확인, 환불 제안, 원인 조사·정정 요청 | 필요한 마스킹 정보와 사건별 근거 | evidence 삭제, 원명령 결과 덮어쓰기, 임의 새 operation 재송신 |
| 감사·보안·플랫폼 관리 | 권한/승인 이력, 정책 배포, 키·어댑터 상태, 장애·복구 증거 | 조회 전용 증거·출처·버전·가용성 | 과거 경제 사실 수정. 관리 권한이 경제 승인 권한을 자동 포함하지 않음 |

동일 사람이 여러 조직 역할을 가질 수 있으므로 '계정 하나=역할 하나'에 의존하지 않는다. 활동 중인 조직·행사·역할을 명확히 선택하고, 서버에서 매 요청의 권한·이해충돌을 검증한다.

## 3. Rust 논리 모듈과 계약

아래 이름은 제안 모듈명이며 현재 존재하는 crate로 보고하지 않는다.

| 모듈 | 소유하는 논리적 기록 | 입력→출력/불변식 |
|---|---|---|
| Identity/Authorization | 조직·주체·서비스 계정·scope·capability·승인 규칙 | 현재 권한 평가. principal, tenant, event, action, 금액/자산, 기간, 승인 세대 결합 |
| Catalog/Policy | EventVersion, VenueMapVersion, PolicyVersion, AssetRegistryVersion | 서명/발급자 인증된 snapshot. draft 편집과 거래가 채택한 불변 snapshot 분리 |
| Quote | QuoteSnapshot, OrderLine 계산결과·배분 근거 | 입력·할인 중첩·반올림·자산과 정책 해시 고정. 표시 가격을 authoritative quote로 오인하지 않음 |
| Inventory/Reservation | scope별 예약, 명령 이력, 위임 사용량 | 검증된 grant 범위 단일 writer, 묶음 전체 성공/실패, GA 수량 보존 |
| Order/Payment | Order, Intent, ProviderOperation, Observation, Allocation | 이벤트 수신 중복과 경제 효과 중복 분리. 원 operation·금액·자산·계정을 결합 |
| Obligation/Refund | ReturnObligation, RefundReservation, RefundIntent, Dispute | 잔여 반환 한도를 원자 예약. 필요/요청/전송/UNKNOWN/확인 완료 분리 |
| Settlement/Ledger | postings, payables, distributions, payout reservations | 자산별 차변=대변; 수정은 반대분개/새 기록; 고객·판매자·자본·플랫폼 자금 구분 |
| Resale | Listing, SaleAgreement, transfer intent, seller payable | 현 소유/정책·취소·사용 상태 확인. 권리 이전과 fiat 지급을 단일 원자 거래인 것처럼 표시하지 않음 |
| Credit | Facility, DrawRequest, BorrowingBaseSnapshot, Encumbrance, RepaymentAllocation | 계약별 적격채권·선순위 부담·준비금을 반영. 승인/담보가능액/현금이 각각 상한 |
| Chain | chain fact, grant/right binding, transaction submission | 원 bytes/digest/입력·서명·effects 보존; 재생과 새로운 서명 권한 분리 |
| Case/Lifecycle | case, decision, retention reference, custody handoff | LC-TERM·후기 사실 인계·review 해제 각각 별도 승인. 사실을 삭제하는 '해결' 금지 |
| Export/Analytics | source cut, manifests, projection watermark | 일관 snapshot/CDC·tenant 권한·출처 검증. 분석 결과가 정본을 직접 수정하지 않음 |

경제 원장의 논리적 정본은 선택된 거래 backend에서 보장한다. 이는 사용자에게 실제 은행 잔액이나 법률상 채권 성립을 보장한다는 뜻이 아니다. provider 사실→원장 반영→계약상 지급 가능액을 근거로 연결한다. 모델별 별도 원장을 무조건 복제해 이중 정본을 만들지 않는다.

## 4. Source of truth·저장 책임 표

| 정보 | 권위/사실 원천 | KIX의 내구 기록 | UI·분석의 읽기 경계 |
|---|---|---|---|
| 재고 원본·관람권·소비/취소 현재성 | 지정 네트워크/패키지의 검증된 Sui 상태 | 객체/버전·거래/effects·정책/원예약 결합 | 인덱서만으로 현재 권위 확정 금지; 검증 수준·watermark 표시 |
| 배타 위임 내 예약·판매 약정 | 현재 유효 grant + 오프체인 거래 계약 | 명령·원payload·최초 결과·예약·order·intent 원자 커밋 | projection 지연 중에도 command 응답 receipt 조회 가능 |
| 실제 승인/capture/반환/송금 | 계약된 PG·은행의 인증된 원천 | 원문·요청/관측·검증 결과·operation identity·대사 | 웹훅 수신 자체를 verified 자금 사실로 표시 금지 |
| 분배·지급·환불·대출 채무 | 채택된 계약/정책 + 인증된 경제 사실 | 원장·배분·잔여의무·승인·실행 결과 | 원장상 예정액과 실제 은행 이행액을 각각 표시 |
| 여신 계약·양도/담보·우선순위 | 당사자 계약 및 적용 절차/확인 | 계약 문서 hash·서명·실행/통지 증거·등록/조회 범위 | 온체인 token/해시를 법적 효력·전체 외부 부담 부재로 승격 금지 |
| 운영 종결·예외 처리 | 지정 권한자의 유효한 결정 | 이유·자료·정책·허용 조치·잔여 위험·서명/기록 | 외부 사실 UNKNOWN과 운영 사건 CLOSED가 공존 가능 |
| 검색·고객 화면·마케팅 지표 | 위 정본에서 파생 | read model, 검색색인, 허용된 캐시 | source cut·staleness 공개; 거래 판정에 재사용하려면 정본 재검증 |
| 제공자 원문·첨부 증거 | 인증 경로와 원본 원천 | 암호화 custody 저장소 + 내용/접근/복구 검증 | hash 존재만으로 원문 가용성 인정 금지 |

## 5. API와 상태 표시

### 5.1 공통 명령 계약

예시 엔드포인트는 `POST /v1/commands` 또는 자원별 command endpoint, `GET /v1/commands/{command_id}`, `GET /v1/orders/{order_id}`, `GET /v1/cases/{case_id}`다. endpoint 수보다 동일 계약을 구현하는 것이 우선이다.

명령 identity = 안정된 업무 scope + 인증 principal + client_command_id. fingerprint에는 원래 업무 payload·견적/정책/자산 identity가 들어간다. transport timestamp, 새 session ID, owner generation을 바꿨다고 다른 구매로 처리하지 않는다. 원래 expires_at 등 업무 필드는 재시도에서 임의 변경하지 않는다. 서버의 논리 apply time과 제공자 발생시각·수신시각은 별도 필드다.

응답은 command_id, immutable first_result reference, 업무 outcome, 적용한 계약/의미론 버전, durable receipt/source position, 후속 intent ID, 현재 조회 링크를 제공한다. 최초 요청의 결과와 이후 주문 상태는 구분한다. replay에서 '당시 예약 성공'을 반환해도 현재 order는 환불 중일 수 있다. 권한 없는 principal에게 과거 결과를 노출하지 않는다.

별도 effect contract가 필요하다. 현재 v4의 상충 `Err(Capacity)`는 격리·시간이 이미 변할 수 있으므로 HTTP 오류/enum 오류를 곧 rollback 신호로 쓰지 않는다. adapter는 전이별 `ReadOnlyResult / CommittedBusinessResult / CommittedProtectiveEffect / NotCommitted` 등 구별 가능한 효과·receipt 계약을 채택하되, 이 문서가 현재 커널 enum을 변경하는 것은 아니다.

### 5.2 한 상태 문자열로 합치지 않을 것

| 상태 축 | 예시 표현 |
|---|---|
| 예약 | 없음 / 확보 / 만료·해제 / 취소 차단 |
| 주문 이행 | 미이행 / 일부 이행 / 이행 / 반환 필요 |
| 결제 사실 | 미전송 / UNKNOWN / capture 확인 / 부분 반환 확인 / 반환 확인 |
| 체인 권리 | 미발행 / 제출·확인 대기 / 발행 확인 / 이전 확인 / 사용 / 취소 |
| 운영 심사 | 정상 / review_required / 조사 중 / 승인된 제한 종결 |
| 환불 의무 | 없음 / 존재 / 예약 / 요청 전송 / 결과 불명 / 실제 완료 |
| 여신 | 미승인 / 승인 한도 / 실행 대기 / 실행 UNKNOWN / 실행 확인 / 회수 중 / 연체·분쟁 / 종결 |

UI 예: '결제 확인 · 발권 중', '반환 필요 · 상충 증거 심사 중', '송금 요청 접수 · 입금 미확인'. '성공' 하나로 예약, 자금, 권리, 환불을 덮지 않는다. 구매자 화면에는 필요한 행동과 예상 안내를 보여주되 내부 enum·backend 이름을 그대로 노출하지 않는다.

실시간 업데이트는 source revision/cursor로 재연결하고 누락 구간은 재조회한다. 스트림 메시지는 편의 알림이지 정본 자체가 아니다. client의 낙관적 좌석 색상이나 버튼 잠금은 이중 판매 방지 근거가 아니다.

## 6. 종단 업무 workflow

### 6.1 1차 구매

1. 검색/cache → 사용자가 선택 → 서버가 current event/policy/grant와 재고를 검증한다.
2. 불변 견적 채택 후 예약·최소 주문·원요청·최초 결과·외부 intent를 같은 내부 커밋에 둔다.
3. commit 뒤 PG adapter가 stable operation으로 외부 호출한다. timeout은 UNKNOWN이다. retry identity를 바꾸지 않는다.
4. webhook/조회 원문을 durable inbox에 먼저 기록한다. 인증 검증과 operation binding 뒤 경제 effect를 적용한다. 미바인딩은 UNMATCHED 큐로 보존한다.
5. capture 확인 후 현재 예약·grant·취소·정책을 확인해 체인 발행을 요청한다. 예약·결제·권리 발행은 서로 다른 확정 경계다.
6. chain verifier가 일치하는 effects와 Right를 확인하면 고객에게 발행 완료를 표시한다. 이행 불가 capture는 반환 의무로 남긴다.
7. 모든 재요청·중복 관측·process crash·outbox 재송신에서 단일 경제 효과와 같은 최초 결과를 확인한다.

### 6.2 리셀

현 소유권/미사용/현재 취소·양도 정책 → listing scope lock/판매 약정 → 구매자 견적·예약 → capture 사실 → 승인된 chain 이전 → 판매자 payable → 보호기간/부담/환불 exposure에 따른 지급 가능액 → 지급 실행 → 은행 사실 확인. 카드 결제와 Move 이전의 원자성을 주장하지 않는다. 이전 불가/성공 후 PG 정정/판매자 payout UNKNOWN 등 각 compensation·hold 경로를 별도로 정의한다. 권리 소유자와 지급 수취인·KYC 결합은 정책에 따라 검증한다.

### 6.3 취소·환불

행사/주문 취소 요청 기록 → 해당 범위 신규 판매 차단 → 체인 취소 현재성 확인 → 이미 보낸 PG/체인 결과 수집 → 주문별 잔여 반환 의무 계산 → refund limit 원자 예약 → stable refund operation 송신 → 인증된 완료 사실 → 원장·의무 감소. 환불 요청 두 개가 같은 잔여한도를 동시에 소비할 수 없다. 취소 접수·신규 차단·발권 취소·환불 완료를 각각 보고한다. 여신이 걸려 있어도 소비자의 반환 필요 사실을 지우지 않는다.

### 6.4 선지급·여신

차주/주최자 신청 → 공연·정산계약·수취권/기존부담·이행/환불 리스크 확인 → 승인된 정책으로 적격채권과 borrowing base 산정 → 심사결론/조건·한도 승인 → 서명된 facility/담보·통지 등 전제조건 충족 → draw 요청 → 가용한도·현금·준비금·우선순위 동시 확인 → 로컬 draw 명령·최초 결과·현금예약·원 intent 커밋 → Move 담보/노출 예약 확정 → 동일 operation의 BankInstructionAuthorization 소비 확정 → 은행 송신/UNKNOWN 보존 → 실제 지급 확인 → 계약별 회수·원금/이자/수수료 배분 → 종료 또는 연체/워크아웃.

금융 기능은 별도 법적 계약이 정하는 현금흐름에 연결한다. 예상 매출과 이미 성립한 정산채권은 분리하며, 차주 대출채권과 티켓 구매자의 관람권을 같은 token으로 모델링하지 않는다. 초기 정책이 실제 확정 정산채권만 적격으로 채택한다면 미래 매출 기반 선지급은 다른 상품 버전이다. 마케팅 모델의 낙관적 판매 예측을 검증된 담보 금액으로 자동 올리지 않는다.

### 6.5 정산/회수 waterfall

원천 자금 확인 → 자산별 지급 가능액과 계약상 우선순위 산정 → 법적/계약상 보호되어야 하는 환불·분쟁·수수료/세금 등 의무 반영 → 유효한 자본 회수 배분 → 잔여 주최자/공연장 지급. 정확한 순서는 상품/가맹/계약별 규칙으로 버전 고정해야 하며 본 예시는 임의의 보편 우선순위를 선언하지 않는다. PG capture가 확인돼도 은행에서 아직 수취하지 않은 금액을 출금 가능한 현금과 합치지 않는다.

## 7. Inbox/outbox·예외 큐·custody

| 큐/기록 | 접수 보장 | 처리와 해제 조건 |
|---|---|---|
| Raw inbox | ACK 전 원문·출처·profile/계정·수신시각·범위 내구 저장 | 인증/검증·정규화. 미인증은 원문 신호로만 보존 |
| Unmatched fact | operation binding 실패에도 원문 보존 | 인증된 원작업/계약 연결 후 적용 또는 별도 사건 종결. 새 주문 임의 생성 금지 |
| Conflict/review | 원본·상충 내용 별도 보존; bound 위험 차단 | 영향 범위 특정·근거·권한 있는 review 결정. 만석이 격리 우회 사유가 아님 |
| Transactional outbox | 상태 변경과 외부 intent 같은 커밋 | 현재 송신 권한 확인 후 동일 stable operation; 전송 후 불명은 조회·대사 |
| Provider UNKNOWN | 원요청·통신 시도·원operation·auth profile | timeout만으로 재판매/새 지급 허가 금지. LC-TERM 운영 판단과 사실 상태 분리 |
| Chain pending | 원 bytes/digest/전체 owned 입력·gas·서명·노출 이력 | 검증 effects·명시된 재전송 조건; 다른 gas/버전의 새 intent로 조용히 대체 금지 |
| Refund/chargeback | 잔여 의무·선행 반환·정정 자료 보존 | 경제 효과 중복 방지 후 한도/원장 적용 |
| Treasury exception | 잘못된 수취인·계좌 변경·과입금·미배분·payout 불명 | 별도 승인·대사. 금액을 정상 거래에 억지로 배분하지 않음 |
| Credit exception | 담보 중복·covenant 위반·한도 부족·자료 stale·공연취소 | 신규 draw 차단과 기존 사실 수신/환불·회수 분리 |

신규 판매의 예산과 completion/관측/취소/복구의 예산을 분리한다. 가득 찬 신규 명령 큐가 기존 결제 사실 보존과 환불 종결까지 막아서는 안 된다. count뿐 아니라 byte/age/미결액의 한도를 정의하고 오래된 UNKNOWN·retention 참조·backlog는 운영 지표로 노출한다. 이 설계는 메모리 무한 증가나 영구 tombstone을 허용한다는 뜻이 아니다.

## 8. 권한·승인·데이터 분리

- RBAC는 역할, ABAC는 tenant/event/facility/provider-account/asset/action/금액·시간·상태 범위다. 조회와 명령·승인·서명 권한을 따로 둔다.
- 민감한 지급·계좌변경·facility/한도 변경은 제안자와 승인자를 분리한다. 기존 LC-TERM의 지정 승인 구조를 임의로 2인 필수로 바꾸지 않는다. 그 계약에 없는 새 maker-checker 조건은 신규 상품/운영 정책으로 명시적으로 채택한다.
- 승인 token은 대상 내용 hash·액션·금액/자산·수취인·scope·정책/권한 세대·유효기한에 결합한다. 승인 뒤 payload/계좌/금액이 변하면 기존 승인 무효다. 최종 commit와 실제 송신 시 현재 권한·회수를 재검증한다.
- 고객지원 impersonation은 읽기/제안 범위만 허용하고 요청자·대리자 이력을 남긴다. break-glass는 제한된 시간·정확한 조치·사후 증거를 갖추고 사실 삭제나 경제 승인 우회 권한으로 쓰지 않는다.
- chain admin, operator signer, PG adapter, treasury approver, read exporter, marketing worker의 service identity와 비밀을 분리한다. 민감정보·PG 자격증명은 프론트엔드/LLM prompt/빌드 산출물에 넣지 않는다.
- 조직별 행 수준 권한만으로 충분하다고 가정하지 않는다. export·캐시 key·파일 경로·메시지 consumer·admin tool도 같은 scope를 검증한다. tenant A의 fact를 tenant B의 operation ID 충돌로 결합하지 않는다.
- AI는 capability에 따라 조회/추천/명령 제안/제한 실행을 분리한다. 자신의 capability·한도·승인 규칙·검증기를 수정하지 못한다. 분석 예측이 은행 지급이나 grant 서명을 직접 호출하지 않는다.

## 9. 마케팅·데이터·Polars/DuckDB/GPU

CRM 동의, 광고 수신, 금융 심사 활용의 목적과 범위를 구분한다. 캠페인 적격성·선예매 entitlement·쿠폰 사용·추천 보상이 거래 조건을 바꾸면 공통 command와 budget reservation에 들어간다. 이메일 발송·화면 추천·집계 보고는 비동기 응용 경로에 둔다.

원천 정본 → 인증 export(manifest, source cut, 권한, completeness) → Rust 기준 의미론/Polars CPU → DuckDB 읽기 분석·대사 → 필요 시 native GPU 비교. 분석 작업이 거래 예약을 직접 쓰지 않으며, 여신 의사결정에 사용되는 결과는 source cut·model/policy/feature version·staleness·검증 상태를 기록한다. GPU는 marketing scoring이나 대규모 위험 시뮬레이션 후보이고 주문 하나의 동기 결제 승인을 통과시키는 필수 단계가 아니다.

FeatureIR의 null/overflow/정렬·join·group·금액/자산 규칙을 유지한다. F64 결과를 정본 금액/재고/키로 재유입하지 않는다. 금전 계산은 typed integer atoms로 수행하고 currency conversion은 별도 승인된 quote/rate·시점·반올림 계약이다. Polars/DuckDB/libcudf를 설치했다는 사실로 semantic parity나 최대 성능을 주장하지 않는다.

## 10. 배포·장애·관측·복구

초기 논리 배포 단위 제안: (1) edge/BFF+정적 UI, (2) Rust authoritative command service+선택 backend, (3) PG/은행/Sui adapter workers·signer isolation, (4) 조회/운영 및 projection workers, (5) 분석/export workers. 서비스 수 자체를 KPI로 삼지 않는다. 네트워크 호출은 경제 DB transaction 밖에서 수행한다.

환경은 dev/test/localnet, provider sandbox/testnet, 제한된 실제 운영을 별도로 구분하고 키·MID·체인 network/package·DB·source manifest를 교차 혼용하지 않는다. package/schema/semantics/policy의 지원 범위와 migration 경계를 배포 manifest에 넣는다. 과거 wire를 새로운 의미론으로 조용히 재생하지 않는다.

복구는 backup 생성보다 검증된 restore·증거 접근·원권위 확인·재전송 제한·signer fencing까지 포함한다. 복원된 사이트는 처음에는 조회/대사 전용으로 시작하고 active writer/signer 자격 부여는 별도 절차다. 이미 외부로 노출된 유효한 거래는 내부 failover로 취소되지 않는다. 동일 권한 범위의 두 active writer를 만들지 않는다.

필수 운영 지표: 명령 acceptance/업무 성공/거절/멱등 replay를 분리한 goodput, queue age/count/bytes, reserved/stored evidence 점유, UNKNOWN 미결 시간·금액, unmatched/conflict 발생·해결 age, grant stale/만료, chain submission→confirmed 지연, PG 수신→verified→applied 지연, refund/payout 미결, projection lag, borrowing base stale/부족, 월별·공연별 실제 손실·정정액. 원개인정보를 metric label로 쓰지 않고 command/operation 추적은 권한 통제된 trace/evidence에 둔다.

RPO/RTO·성공 ACK·장애 모델은 아직 승인 목표가 없으므로 숫자 달성으로 보고하지 않는다. '승인 ACK 뒤 유실되지 않는 범위'를 시험 조건별로 고정하고 장애 중 판매를 중단하더라도 기존 사실을 보존하는 fallback을 정의한다. 운영 플랫폼 장애와 protocolAPI·chain client 기능은 가능한 범위에서 분리한다.

## 11. 성능 workload와 인수 장면

읽기 조회 수와 경제 명령 수, 체인 거래 수는 별도 분모다. 탐색 부하 100/1,000/5,000/10,000 admitted command/s는 측정용 제안점일 뿐 승인 SLO가 아니다. 대기열에 버린 요청을 처리 성능으로 합산하지 않는다.

| workload | 재현할 장면 | 합격 판정의 형태 |
|---|---|---|
| 티켓 오픈 | hot seat·연석 교차, GA hot partition, 과도한 재시도 | 실제 성공 goodput·예정 도착 기준 p99, 이중 판매 0, 폭주 scope 국소화 |
| 이력 증가 | 긴 시간 동일 scope 운영, evidence/command 포화 | capacity 숨김용 커널 재생성 없이 측정; 원결과 조회/후기 사실 경로 유지 |
| 결제 지연 | PG timeout, 응답 유실, duplicate/batch events, late capture | 동일 effect, 원문 보존, 타 구매자 재고 해제 0 |
| 환불 폭주 | 공연 취소와 동시에 구매·늦은 capture·refund 두 건 | 취소 범위 현재성, 잔여한도 과다예약 0, 미결 증거 누락 0 |
| signer 장애 | 동일 owned input을 요구하는 두 작업, leader/process 교체 | 서명 권한 단일화, 원 bytes/effects 인계, 재실행으로 숨김 없음 |
| 여신 실행 | 동시 draw, 한도 변동, 계좌 변경, 지급응답 유실 | 가용한도/현금/부담 이중소비 0, 승인 payload 불일치 차단 |
| 데이터 격리 | 분석/export 대형 작업 중 구매/관측 | 메모리/CPU/IO quota, 거래 지연 예산 영향 측정, tenant 누출 0 |
| 복구 | 커밋 전후 crash·restore·오래된 backup·옛 writer 재등장 | ACK 계약, 회수 cut/identity 보존, 조회 복원과 writer 승격 구분 |

승인된 임계값이 있어야 '통과' 판정한다. 0건 안전 위반도 시험한 이력/장애 범위 안의 관측 결과이며 형식 증명으로 보고하지 않는다.

## 12. 구현 작업 묶음 제안과 완료 정의

기존 BP 번호를 유지하며 세부 플랫폼 작업으로 연결한다. 아래 하위 ID는 공식 Task 발행 전의 계획 식별자다.

| 제안 ID | 기존 BP 연결 | 산출물 | 선행/완료 기준 |
|---|---|---|---|
| OP-01 | BP-02/05/06 | tenant/principal/capability·상태축·명령/API 계약 | 공개 schema 및 두 client 오류/bytes 일치, replay vs current view 구분 |
| OP-02 | BP-09/10/11 | 영속 예약/주문·inbox/outbox·원장/환불 | backend선택·허가된 수명 전이; crash와 중복관측/late fact 검증 |
| OP-03 | BP-12/13/14 | Sui 위임/발권 adapter와 구매 포털 최소 흐름 | 실제 chain effects·자금사실·권리 구분; UI 없이도 두 독립 client 종단 재현 |
| OP-04 | BP-15/16 | 주최자·리셀·Treasury 화면/명령 | 동일사실 기반 수익/미지급/환불·resale이전·payout확인 |
| OP-05 | BP-17 | 공연장/검표 console·devicecapability | 현재 취소·중복소비·권한회수·네트워크장애 정책 시험 |
| OP-06 | BP-21 | capitalprovider·심사·facility/draw·회수 console | 금융 계약/전제조건·이중부담/한도·미결지급·환불노출 검증 |
| OP-07 | BP-18/19/20 | 인증 export·readmodel·marketing | sourcecut/권한·동의·쿠폰예산·CPU semantic parity |
| OP-08 | BP-22/24 | 제한 AI명령·지원/분쟁·감사·운영복구 | 역할분리·현재권한·actionapproval·restore/옛signer 시험 |

플랫폼 UI 작업은 디자인·mock phase를 병행할 수 있다. mock을 실제 계약·provider·chain 인수와 혼동하지 않는다. '화면 완성', 'sandbox 종단', '실제 제한 운영'을 진척판에서 각각 표시한다. 핵심 SDK/API 인수가 프론트엔드 리뉴얼에 종속되지 않도록 한다.

## 13. Builder가 넘겨야 하는 자료

모든 Task는 한 명의 writer를 정하고 인터페이스/schema·source of truth·성공 ACK·오류 효과·권한 범위·구현 금지 경계를 포함한다. 구현자는 branch/head, 계약 및 schema revision, 변경 파일, 실행 명령과 raw 결과, 실패/재현 seed, UI경로와 underlying receipts, 미해결 외부 입력을 전달한다. 비작성 reviewer는 이름이 아니라 실제 causal/identity/boundary 보장과 실패 전이를 검사한다.

권한·금융/체인·외부부작용 계약이 바뀌면 동일 Task 내부의 임의 구현 선택으로 숨기지 않는다. 반면 승인 계약 안의 routine refactor/테스트 수리는 담당 builder가 완료까지 진행한다. 실제 activation·실자금·merge는 해당 정본 승인을 따른다. 이 계획은 R2나 kernel lock 해제를 자동 승인하지 않는다.

## 14. 원문 근거

- [현행 개발계획](https://github.com/BeautifulMind-JT/kix-protocol/blob/6dbf8dfed6ee790e2ee56b49a75b727edd9db977/docs/DEVELOPMENT_PLAN.md)
- [모델 1 권위 승인](https://github.com/BeautifulMind-JT/kix-protocol/blob/6dbf8dfed6ee790e2ee56b49a75b727edd9db977/docs/decisions/AUTHORITY_MODEL_1.md)
- [LC-FACT/LC-CUT/LC-TERM 0.6](https://github.com/BeautifulMind-JT/kix-protocol/blob/6dbf8dfed6ee790e2ee56b49a75b727edd9db977/docs/contracts/STATE_LIFECYCLE.md)

여신의 상품 법적 분류·공시·심사·우선순위 판단과 Sui production 객체 상세는 별도 전문 설계와 교차 확인하여 이 운영 계약에 결합해야 한다. 이 문서는 그 검토를 수행했다고 주장하지 않는다.
