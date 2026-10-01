# KIX Finance — 정산·금융 개발 설계 확장안

문서일: 2026-10-01 KST. 상태: **PENDING 설계 후보 / 미채택 / 실행 금지**.
KIX Finance는 이 설계의 제품 범위명이다. 새 저장소나 제3의 AIOPS 프로그램을 만들지 않는다. 프로토콜·경제 모델의 작성자는 `BeautifulMind-JT/kix-protocol`의 `kix`이고, 금융 운영 화면의 작성자는 `BeautifulMind-JT/kix-commerce-apps`의 `kixc`다. 이 문서는 금융상품·규제·법률·회계 판단을 확정하지 않는 개발 설계다.

## 1. 읽은 기준과 기존 자산

| 기준 | 정확한 소스 |
|---|---|
| protocol 설계 후보 #83 | `b665f9a0ad41a46e2169cb142b91d598665aa7ab` |
| commerce 설계 후보 #16 | `bb24207cb648acfe3083c4a2e7720251b06ad639` |
| 중앙 복구 구현 후보 #47 | `94a768e19df12703ea0b9a49e49972feb2f6ef4f`; 제품·실자금 실행 자격의 증거 아님 |
| 현행 승인 범위 | protocol `docs/DEVELOPMENT_PLAN.md`, `docs/decisions/PROGRAM_DECISIONS_20260928.md`, `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md` |
| 계약·열린 입력 | `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md`, `CREDIT_ADVANCE_F04.md`, `STATE_LIFECYCLE.md` 0.6, `PG_TOSS_CARD_PROFILE.md`, `FIRST_BATCH_OPEN_INPUTS.md` |
| export 경계 | `runtime/AUTHENTICATED_EXPORT.md` |
| 생산자·소비자 계약 | protocol `docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md`, commerce `docs/aiops/INTEGRATED_JOURNEY_COMPLETION_DESIGN_KO.md`, commerce `README.md`와 `packages/protocol-adapter/src/commerce-bindings.ts` |

이 기준은 원격 exact-head 파일과 tree를 읽은 기록이다. 소스의 존재를 승인·감사·실행·제품 수용 완료로 읽지 않는다. 현행 결정 문서와 충돌하면 이 후보의 실행을 막고 결정 대상으로 남긴다.

이미 있는 것은 다음과 같다.

- `reference/settlement_f01_f03/mock_settlement.py`는 정수 KRW F01–F03 산술과 목 배정을, `settlement_fsm.py`는 수락 상태·최초 결과·프로세스 저널 재생을 갖고 있다. 내구 금융 원장이나 은행 정산은 아니다.
- `reference/credit_advance_f04/mock_credit.py`와 `credit_fsm.py`는 목 청구 액면 예약·공유 노출 한도·목 상환·종결과 정산 `COMMITTED` 조회 게이트를 갖고 있다. 실여신·담보 완성·면허·입금 관측은 아니다.
- commerce는 settlement/credit desk와 패널을 이미 갖고 있다. 현재 HTTP 메서드는 몸체가 같은 공표 명령이 없으면 `not-bound`다. 건강 상태 확인, `offer_gift`, `settle_capture`를 다른 금융 메서드의 대체 몸체로 보내지 않는다. 앱은 정산 산술·Move·커널을 복사하지 않는다.
- 기존 `settlement-policy-deepening`, `f04-mock-deepening`, `k1-adapter-event-identity`, `k-stage5-durable-tx`, `k-stage6-economics-reference`, `k-stage7-authenticated-export`가 각각 정책 결정, 식별, 선택 backend, 경제 효과와 일반 export를 맡는다. 아래 후속 노드는 그 일을 재발행하지 않고 금융 투영·보존식·대사·소비 증거를 덧붙인다.
- 기존 `f04-real-funds-lift-criteria`, `toss-sandbox-conformance-plan` 등 잠금 해제 제안과 원래 User-only 14개 노드는 그대로다. 이번 후보가 그 노드의 완료를 대신하거나 승인 범위를 넓히지 않는다.

읽은 tree의 잠금 blob은 `runtime/crates/kix-kernel/src/lib.rs = 69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs = b607996c83a119c349f1cc90469ac1ba82764e20`다. 이번 작성 경로는 문서 두 개뿐이며 잠금·참조 구현을 수정하지 않는다.

## 2. 권위와 책임 경계

커널의 예약·수명·격리·용량 책임은 그대로다. 지원되는 `captured` 사실의 결합·비교·보존 뒤, 복수 수취인 의무·배분·지급·은행 대사는 커널 밖 경제 계층에 둔다. `captured`, 목 FSM의 `COMMITTED`, chain 기록을 실제 수취·이행·정산·담보·운영 준비 완료로 승격하지 않는다. 기존 `ReturnRequired`와 `Review`의 직교성, 원 포착 사실 보존도 그대로다.

| 작성자 | 맡는 것 | 지켜야 할 경계 |
|---|---|---|
| 채택된 stage 5 backend / stage 6 경제 모델 | 승인된 명령·최초 결과·원 operation과 합성 경제 효과 | 현행 권위 모델·선택 backend의 원자성; 새 자체 로그·복제·합의 없음 |
| finance 투영 | 경제 사건의 복식 수치 표현·의무/노출/대사 조회·합성 회계 export | 재계산 가능한 파생 데이터; 권리·실자금·명령 승인 권위 없음 |
| 관측 수신 | 원문/출처/범위/원 operation 결합, 사실과 적용 상태 구분 | 미검증 신호를 인증 사실로 승격하지 않음; 원 제공자 결합 유지 |
| commerce adapter / UI | 정확한 생산자 계약을 소비하고 상태·차이·기준시점을 표시 | 쓰기 산술 없음; 쿼리·배너·manifest hash를 권한·Fable PASS로 해석하지 않음 |
| User / 지정 외부 담당 | 상품·당사자·회계·법무·가맹·운영 결정 | AI가 빈 정책을 임의 입력하거나 미확인 조건을 승인으로 면제하지 않음 |

새 경제 명령, 결과 판정, 금융 원장 권위, 거절 결과 보존 의미를 바꾸려면 후보 ADR과 독립 exact-head 설계 검토가 먼저다. 단순 조회 계약의 채택도 감사·현재 tuple 검증을 생략하지 않는다. 원 operation의 불명확한 응답을 새 ID·키·제공자·HTTP 재시도로 해결하지 않는다.

## 3. 금융 투영의 수치 계약

`fin-ledger-contract`가 버전이 있는 후보 ADR과 수치 스키마를 먼저 만든다. 아래는 합성 계산의 검증 계약이며 계정과목의 법률·회계 분류를 승인하지 않는다.

이 준비 ADR은 stage5 backend 구현보다 먼저 작성할 수 있다. source 계약의 상태를
계획됨·User 선택됨·구현됨·현재 없음으로 구분하고 immutable 결정/source 참조와 gap을
남긴다. 없는 backend에서 commit된 사건·source cut·durability를 발명하지 않는다.
실제 투영·관측·export 구현은 기존 stage5/6 선행 뒤에서만 하며, `none yet`는 DEFERRED로
HOLD다. DECLINED 뒤의 제외/비구현 산출물도 User 병합의 적용 범위/계획 개정이 먼저다.
[호환·완료 설계 §5.1](CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md#51-사용자-결정-결과와-후손-적용-범위)을
따르며 준비 문서가 뒤 일곱 금융 구현의 실제 evidence를 대신하지 않는다.

- `ProjectionEntry`는 원 program/plan revision/task/delivery head, 원 source event identity, operation/order/claim/advance identity, 자산 ID·registry version/hash, source cut, 계약·정책 revision, ordinal과 entry digest를 결합한다. 계약 tuple과 금융 사건의 업무 identity를 서로 대체하지 않는다.
- 금액은 자산 최소 단위의 정확한 정수다. bool·float·암묵적 통화 변환·타임존 추측·Wide128 잘림을 거절한다. KRW 목의 기존 상한은 시험 프로파일로 남기고 다중 자산의 새 상품 한도로 일반화하지 않는다. 선택 DB의 signed 표현에 맞춰 u128을 축소하지 않는다. 저장 mapping과 overflow 한계는 stage 5 결정과 형식 검증으로 고정한다.
- 투영 묶음마다 같은 자산의 debit 합과 credit 합이 같다. 서로 다른 자산을 합산해 균형을 맞추지 않는다. account 라벨은 승인되지 않은 법적 당사자·은행 계좌·회계 계정과목의 의미를 갖지 않는 합성 role이다.
- 원 경제 사건이 채택 backend에 commit된 뒤의 확정 source cut만 적용한다. source event + projection contract revision의 유일성 제약으로 한 번 적용하고, receipt 재전달·페이지 재읽기는 경제 효과나 금융 투영을 한 번 더 만들지 않는다. 오류·거절·UNKNOWN을 성공 분개로 채우지 않는다.
- 잘못된 투영은 원 entry를 덮어쓰지 않고, 승인된 투영 의미 안에서 reversal과 replacement를 원 사건·오류 근거에 연결한다. 이것은 원 operation의 최초 결과를 바꾸거나 외부 송신을 다시 허용하는 기능이 아니다.
- 금융 투영이 지연·누락·충돌하면 경제 writer가 투영 수치로 원장을 수정하지 않는다. source cut, 적용 watermark, gap, quarantine을 명시하고 재생 일치 범위만 보고한다.

계정 체계·수익 인식·예수/준비금/회수채권/손실 분류·세금·보존기간은 **UNDETERMINED**다. `settlement-policy-deepening`의 금융/회계 입력 책임자, User와 지명 외부 회계·법무 담당이 답할 목록으로 남긴다. 검증을 위해 사용할 합성 role과 fixture는 이 분류 결정의 증거가 아니다.

## 4. 복수 수취인·부분 환불·예수와 정산

현행 F01–F03 §0.2–0.3의 원칙을 유지한다. 수취인 단일 전제를 박지 않고, 자산 최소 단위 정수와 결정론적 사전 우선순위로 총액을 보존한다. 수취인 순서·우선순위 방법은 현재 **UNDETERMINED**이며 기본값을 두지 않는다.

완료할 기술 계약은 다음과 같다.

1. 결제/포착 사실, 정산 의무 액면, 배분 결정, 합성 배정, 외부 지급 관측, 대사 완료를 별도 record/state로 둔다. 새 record/state의 wire 의미는 후보 ADR 채택 뒤에만 구현한다. 목의 `distributed`와 실제 지급을 구별한다.
2. 승인된 버전의 배분 정책은 원 총액·대상 자산·수취인 집합·weights/fees·고정 우선순위와 digest를 계산 전에 동결한다. missing policy는 `DECISION_REQUIRED`이며 호출자나 운영자가 사후 순서를 바꾸지 않는다. F02의 부족 현금 호출자 순서는 시험 프로파일이다. 주문 줄 할인 largest-remainder를 일반 정산 정책으로 옮기지 않는다.
3. 양의 합성 가중치 합 `W`에 대해 기준 floor를 쓰는 채택 정책이면 `q_i = floor(T*w_i/W)`, `R = T - sum(q_i)`를 정확한 정수로 계산한다. 잔여 `R` 배정 알고리즘과 동점 순서는 채택 정책에 정의된 것만 적용한다. 이 식만으로 정책이 결정된 것은 아니다. 0총액·0가중치·오류 가중치·중복/누락 수취인·overflow를 시험하고 `sum(allocation_i) == T`를 검증한다.
4. 정상 지급, 부족 현금 우선순위, 반올림 잔여, 환불 부담, reserve/hold, 이미 배정된 금액의 회수 의무를 서로 다른 술어로 검증한다. 동일 총액의 의미가 달라도 같은 receipt를 쓰지 않는다.
5. 부분 환불·리셀 판매자 배분·수수료 반환·세금 부담은 현행 계약에서 빈 정책이면 그대로 열린 의무/미정 부담으로 남긴다. 전액 1회 fixture 재분류나 부분 환불의 누적 합을 근거로 자동 환수·상계를 만들지 않는다. 승인된 새 정책을 구현해도 과거 revision의 결과를 새 의미로 재해석하지 않는다.

`fin-multi-payee-refund-proof`는 stage 6 결과에 독립적인 보존식/negative vectors를 추가한다. 이는 stage 6의 allocation/refund/payout 기능을 다시 구현하는 일이 아니다. 교차 자산 상계, 지급대행 능력과 실제 복수 수취인 지급은 여전히 차단된다.

## 5. 원 관측·inbox/outbox·대사·장애 복구

`k1-adapter-event-identity`와 stage 5 inbox/outbox를 재사용한다. 금융 후속 노드는 합성 제공자 fixture로 다음 증거를 연결한다.

- transmission ID, source event ID, payment ID, operation ID, 원 제공자/계정/환경, 원문 hash, 원문 보존 참조, 발생 시각·수신 시각·적용 시각, 검증 방법/버전과 source cut을 기록한다. 이벤트 수신과 경제 적용은 별도 상태다.
- 동일 사건의 전송 중복, 동일 operation의 서로 다른 포착, 정정·취소·부분 환불, 순서 역전과 늦은 포착을 구분한다. 미검증 webhook fixture는 `UNVERIFIED_SIGNAL`로 남기며 실제 인증·서명 적합성 증거를 만들지 않는다.
- 대사는 원 명령/최초 결과/외부 의도·attempt/수신·적용·투영·미해결 항목을 원 operation 아래 연결한다. 한 행의 amount 일치와 전체 자료 complete를 별도 값으로 둔다. 페이지·기간·cursor 범위/누락·중복·watermark와 검증 출처 없이는 `RECONCILED_COMPLETE`를 보고하지 않는다.
- timeout, 연결 실패, 단일 `not-found`, 미처리 inbox, commit 여부 불명, 응답 유실은 UNKNOWN 또는 명시적 incomplete다. 허용된 조회·원문 재생과 새 경제 POST를 구별하며 앱은 한 번 요청하고 오류를 그대로 표시한다. 조회된 사실은 새로운 자금 실행 허가가 아니다.
- stage 5가 채택한 DB 트랜잭션 안의 중단점만 실제 fault matrix로 검증한다: 원 사건 commit 전, 경제 효과 후 응답 전, 투영 commit 전후, outbox enqueue/ack 경계, 정정 수신 뒤. 원 경제 효과·최초 결과의 불변성과 투영 중복 방지·gap 보존을 확인한다. 자체 로그/복제/consensus·생산 PG를 새로 구현하지 않는다.
- LC-TERM의 C1–C5·유효 승인·내구 기록과 LC-FACT/LC-CUT을 그대로 참조한다. 대사 투영의 matched, elapsed time, 해시, User 승인 중 하나만으로 원 UNKNOWN/슬롯/Review를 해제하지 않는다. 후기 사실은 운영 종결 뒤에도 보존한다. 이번 금융 노드는 운영 종결 명령이나 활성 자동승인 서비스를 제공하지 않는다.

## 6. F04 노출·선물 경로와 조회

금융 노출 조회는 기존 F04 목 계약의 `face`, `reserved_open`, `outstanding_exposure`, `repaid_exposure`, `recovery_due`의 의미를 분리한다. `confirmed_cash`·`recovery_due`를 대여 재원·선지급 가능 한도에 더하지 않는다. 원 고정 face snapshot과 그 뒤 새로 관측된 정산 revision을 함께 보여 주되, 기존 `FACE_SNAPSHOT_FROZEN` 계약을 자동 변경하지 않는다.

후속 평가 결과는 별도 합성 진단 revision이다. refund burden 미정, stale source, snapshot conflict, 이미 예약된 다른 advance 또는 불명확한 repayment면 `HOLD`/`UNKNOWN` 사유를 제공한다. 한도 재산정·우선순위·이자/상환표·손실·담보 효력은 기존 `f04-mock-deepening`과 지정 담당자의 결정 사항이다. 새 정의가 승인되기 전에는 진단이 기존 노출을 해제·늘리거나 새 인출을 수락하지 않는다.

gift·coupon·right는 금융 역할과 다른 domain이다. `offer_gift`를 credit draw로 쓰지 않고, 선물 수락·권리 이전·검표 자격을 수취인 배분·금융 담보·상환으로 간주하지 않는다. 합성 테스트는 미정 환불의 credit 거절, 중복 draw, 부분 목 상환 뒤 공유 한도, 다른 권리 버전·취소/양도/consume, gift 경로의 금융 호출 거절을 검증한다. app과 protocol은 각자의 계약 검사를 하고, 앱은 산술을 복제하지 않는다.

## 7. 일관 회계 export와 Finance API 소비

`k-stage7-authenticated-export`를 금융 조회의 기반으로 재사용한다. finance exporter는 그 범위의 원본 source cut/투영 watermark/snapshot·incremental boundary와 파일 hash를 결합해 accounts/entries/obligations/exposures/reconciliation exceptions를 합성 데이터로 내보낸다. 기준시점이 서로 다른 보고서를 하나의 닫힌 잔액으로 표시하지 않는다. 전역 consistent cut이 없으면 multi-shard 전체 금융 export에 전역 원자성·완전성 표식을 주지 않는다.

export에는 mode/profile, 자산 registry·계약·정책 revision, projection mapping revision, snapshot/cursor range, gap·staleness, 행/파일 수·hash·schema, 적용 source watermark, 명시적인 synthetic provenance를 넣는다. CSV/분석 포맷은 금액을 손실 없는 정수 문자열로 내보내며 Excel/JS 부동소수점 변환을 정본으로 쓰지 않는다. 계정 역할·보고서 분류와 필요한 사용자/외부 검토의 미정을 함께 적는다. tax filing·GAAP/IFRS 준수·regulated lending 보고서라는 표식을 주지 않는다.

`fin-catalogue-read-model`은 finance 조회 schema만 공표한다. `protocol-read-projection-evidence`의 `ReadObservationV1` 일반 read query/transport 경계와 finance ADR을 사용하며 finance 명령·query를 다른 기존 catalogue body에 remap하지 않는다. 새로운 catalogue/gate/schema/receipt bytes를 만들 때마다 다음을 갖춘다.

1. 그 exact producer source/tree와 양쪽 OpenAPI blobs/hash에 맞춘 새 TypeScript SDK 및 immutable manifest.
2. generator/toolchain/output, domain/schema, `SEMANTIC_CONFORMANCE` profile kind/revision/digest와 shared positive/negative vectors. 이전 profile 노드 PASS를 새 tuple에 전이하지 않는다. BOOTSTRAP은 확대 finance catalogue를 적격화하지 못한다.
3. source 자체에 자기 최종 commit을 넣지 않고, 실제 exact delivery head·독립 감사·merge·보호된 completion binding은 산출물 밖 현재 증거로 연결한다. manifest hash와 앱 query가 approval/receipt를 위조하지 못하게 한다.
4. commerce `c-finance-projection`은 기존 `bind-list-read`, `bind-settlement-fsm`, `bind-credit-fsm`, `primary-price-fee-ui`, `c-journey-identity` 및 external `kix/fin-catalogue-read-model`, `kix/contract-compatibility-profile` 뒤에서 소비한다. 실제 SDK/manifest/profile tuple 검증과 기존 다섯 pin 이동이 선행한다. query 부재는 `NOT_BOUND`, 오류는 오류, incomplete는 incomplete로 보여 준다.

금융 화면은 합성 잔액/배분/환불 의무/신용 노출, 대사 차이, source cut·수신/적용 시점, export 참조를 보여 준다. 누가 어떤 화면의 정상·오류·stale/UNKNOWN 상태를 수용했는지 실제 브라우저 증거를 남긴다. health/ready나 모의 완료를 실제 자금 안전·운영 승인으로 설명하지 않는다.

## 8. 새 후속 노드와 진행 순서

`FINANCE_PENDING_NODES.json`의 8개 node는 별도 실행 계획이 아니라 승인 전 후보 fragment다. protocol의 pending catalogue에 같은 정의로 편입하고, immutable catalogue digest와 cross-repo DAG 전체 검사를 거쳐 채택한다. 기존 `.aiops/program.json`은 이번 설계 작성으로 활성화하지 않는다. 중앙 #47은 실패 보존/제한된 Fable 모델 quota 복구 구현 후보이며 외부 의존성 admission·전체 완료 판정 능력이 설치/적격화됐다는 증거가 아니다. 그 Fable 재시도 자격을 금융 업무 operation의 재전송 권한으로 옮기지 않는다. 현재 runtime이 외부 의존성을 읽지 못하면 전제의 실제 보호된 완료·병합 뒤 승인된 plan revision PR로만 이동한다.

| 노드 | 새로 맡는 결과 | 주요 선행 |
|---|---|---|
| `fin-ledger-contract` | 합성 금융 투영 계약·권위/정책 미정 ADR·coverage map | 새 `protocol-runtime-boundary-register`, 기존 settlement/F04 policy |
| `fin-double-entry-projection` | 기존 경제 사건의 복식 수치 투영·중복/오류 보존 | ledger contract, stage 5/6 |
| `fin-observation-reconciliation` | 원 operation 관측·경제/투영 대사 및 실제 채택 DB fault evidence | ledger contract, double-entry projection, adapter identity, stage 5 |
| `fin-multi-payee-refund-proof` | 채택된 배분/환불 policy의 보존식·versioned vectors | ledger contract, settlement policy, stage 6 |
| `fin-credit-exposure-reconciliation` | F04 노출/환불/gift 교차 진단·HOLD 조회 | F04, projection, reconciliation, refund proof |
| `fin-consistent-accounting-export` | 금융 특화 source-cut export·손실 없는 mapping | projection, reconciliation, stage 7 |
| `fin-catalogue-read-model` | finance query schema와 exact current SDK/manifest/semantic profile tuple | finance exposure/export, catalogue promotion/profile, `protocol-read-projection-evidence` |
| `fin-finance-closeout` | 위 producer들과 commerce finance 소비의 실제 증거 마감 | 위 7개와 finance/refund/gift/reservation/resale/admission/E2E consumer |

교차 저장소 순서는 `fin-catalogue-read-model` 생산자 완료 → `c-finance-projection` 소비자 완료 → `fin-finance-closeout` 금융 증거 묶음 마감이다. 마감의 외부 선행에는 `refund-surface`, `gift-surface`, `bind-reservation-fsm`, `bind-resale-fsm`, `bind-admission-fsm`, `delegation-surface`, `c-async-session-fence`, `e2e-browser-journeys`도 포함한다. 금융 조회만으로 실제 환불·권리/선물·입장 경계의 소비를 빠뜨리지 않는다. 모든 새 금융 node의 실제 감사 gate는 A3/ARCHITECTURE다. closeout은 수용 이정표지만 중앙의 A3 gate 정규화와 일치하도록 MILESTONE을 선언하지 않는다. 금융 마감은 commerce 전체 closeout을 기다리지 않고, 소비자가 금융 마감을 선행으로 삼지도 않는다. protocol/commerce 최종 완료가 서로의 final-closeout을 의존하도록 만들지 않는다. 전체 DAG 검사로 이를 확인한다.

## 9. 완료 분모·수용·운영 경계

Finance는 세 번째 program/repository로 집계하지 않는다. 아래 목록은 합성 금융 개발의 **정확한 seed 집합**이다. 금융 분모 `D_F`는 채택된 immutable combined catalogue에서 이 seed들의 모든 local/external 선행을 재귀적으로 포함한 합집합이다. 키는 `(repository, program, node)`이며 중복은 한 번만 센다. 아직 채택되지 않은 seed는 pending으로 표시하며 승인된 active 분모에 섞지 않는다. 전체 118개 후보를 금융 완료로 축소하거나 바꿔 세지 않는다.

| seed 소유 범위 | 정확한 node ID |
|---|---|
| 기존 protocol 경제·정산·여신 | `settlement-policy-deepening`, `f04-mock-deepening`, `move-primary-price-fee`, `booking-resale-admission-deepening`, `k1-adapter-event-identity`, `k-stage5-durable-tx`, `k-stage6-economics-reference`, `k-stage7-authenticated-export`, `ai-delegation-contract-mock` |
| 기존 protocol 계약 생산자 | `p-sdk-0`, `openapi-catalogue-promotion`, `read-model-contract`, `read-model-reference`, `p-sdk-1`, `k-stage3-schema-sdk-conformance`, `contract-compatibility-profile` |
| 새 protocol 공통 경계 | `protocol-runtime-boundary-register`, `protocol-canonical-identity-conformance`, `protocol-read-projection-evidence`, `protocol-local-recovery-conformance` |
| 새 Finance producer | `fin-ledger-contract`, `fin-double-entry-projection`, `fin-observation-reconciliation`, `fin-multi-payee-refund-proof`, `fin-credit-exposure-reconciliation`, `fin-consistent-accounting-export`, `fin-catalogue-read-model`, `fin-finance-closeout` |
| 기존 commerce 금융·권리 소비 | `consume-p-sdk-0`, `consume-p-sdk-1`, `bind-list-read`, `bind-settlement-fsm`, `bind-credit-fsm`, `bind-reservation-fsm`, `bind-resale-fsm`, `bind-admission-fsm`, `primary-price-fee-ui`, `api-state-distinction`, `refund-surface`, `gift-surface`, `delegation-surface`, `e2e-browser-journeys` |
| 새 commerce 소비 경계 | `c-journey-identity`, `c-async-session-fence`, `c-finance-projection` |

seed 목록과 실제 채택 catalogue/digest/revision, closure 계산을 보고서에 기록한다. `fin-finance-closeout` 자신의 행도 분모에 있지만 소스 보고서 작성 중에는 pending이다. 자신의 현재 HEAD·CI·병합/receipt를 보고서 안에서 만들어 순환 완료를 요구하지 않는다. 실제 완료 후 중앙/독립 판정자가 밖의 보호된 증거로 그 행을 갱신한다. source pack 작성 완료와 금융 scope의 모든 node 완료는 별도 결과다.

기존 전체 후보 98개에는 pending 21개가 포함됐다. 이번 전체 KIX 후보는 protocol 후속 6개·Finance 8개·commerce 후속 6개를 더한 118개이며 pending은 41개다. 이 수는 현재 제안 inventory의 크기이며 실제 승인·완료 수가 아니다. 기존 active/pending node와 원래 User-only 14개는 그대로 남고, 새 8개 문서 작성으로 완료율을 올리지 않는다. 실제 채택 catalogue/revision이 바뀌면 새 분모와 이전 기록을 함께 보존한다.

Release 검토 행은 `f04-real-funds-lift-criteria`, `toss-method-expansion-review`, `toss-sandbox-conformance-plan`, `k1-open-inputs-brief`, `k2-retention-proposal`, `public-endpoint-readiness-plan`의 실제 상태와 각 unlock 입력/승인을 별도로 표시한다. 합성 Finance 증거 묶음은 이 행의 완료를 전제하거나 대체하지 않고 `FINANCE_RELEASE_READY=HOLD`를 유지한다. 이 행들을 global KIX 분모에서 빼지 않는다. 선행으로 실제 포함된 User-only stage 2/backend 결정 등도 closure에서 빠뜨리지 않는다.

`fin-finance-closeout` 보고서는 다음의 서로 다른 결과를 분리한다.

- SOURCE_IMPLEMENTED: 채택된 금융 작업의 실제 source와 exact-head tests/CI·독립 리뷰·merge/보호 receipt.
- FINANCE_SYNTHETIC_ACCEPTED: deterministic projections·allocation/refund/credit/reconcile/export vectors 및 실제 앱 finance 정상·주요 오류/stale/UNKNOWN 상태의 현재 수용 증거.
- FINANCE_RELEASE_READY: 현재는 **HOLD**. 합성 테스트와 위 마감은 real funds/credit/chain/public 운영 unlock 증거가 아니다.

금융 closeout이 central/global `DONE`을 재정의하지 않는다. global/제품 완료는 모든 원래 active+pending 및 채택 후속 node·외부 전제·User-only HOLD를 동일 immutable catalogue로 판정하는 중앙의 채택/적격화된 완료 기능을 따라야 한다. UI에서 finance closed를 전체 KIX done으로 바꾸지 않는다. missing/UNKNOWN/wrong revision receipt는 완료가 아니다. blocked User 결정·법무/회계·제공자 항목은 보고서에서 이름·담당·실제 입력 부재로 남긴다.

분모 보고는 실제 ADOPT된 구현과 DEFERRED, DECLINED 뒤 승인된 적용 범위를 따로
센다. 결정 문서의 DONE이나 backend 없는 note를 금융 기술 완료·합성 수용·qualification으로
승격하지 않는다. 승인된 개정이 node 적용 범위를 바꾸면 영향 정의·digest와 이전/개정
catalogue를 보존하며, 원래 여덟 금융 후보를 이 PR에서 없애거나 조용히 제외하지 않는다.

실자금·실 PG/은행/KYC·규제 여신·공개 endpoint·production conformity·Sui testnet/mainnet·coin·키·R2/자체 저장·합의는 계속 잠근다. 기존 unlock 문서가 요구하는 실제 MID/상품/가맹 범위·서명/조회 계약·sandbox 실제 증거·법무/인허가·운영 책임·보존/복구·독립 감사·User 명시 승인을 각각 현재 범위로 확인해야 한다. 기존 User-only 14개와 `f04-real-funds-lift-criteria`를 우회하는 새 승인이나 자동 활성화는 없다.

## 10. 이번 작성의 검증과 미실행

이번 결과는 문서와 node 정의 후보다. 실제 ledger·export·쿼리 구현, 합성 scenario 실행, 브라우저 금융 수용, 제공자 접속/서명 확인, 독립 Fable 감사, 운영 설치/활성화는 하지 않았다. 작성 중 JSON schema 필드·8개 A3/ARCHITECTURE gate·현재 combined candidate 118개 node의 선행 참조·중복·교차 DAG를 검증했다. missing reference/중복/cycle은 0이었다. §9의 정확한 Finance seed closure는 현재 후보에서 60개 node였고, closeout 자신을 뺀 전부가 실제 선언된 선행의 재귀 closure와 일치했다. 이것은 제안 DAG의 구조 검사이며 실행·완료 증거가 아니다. publication 전 최종 catalogue에 다시 합쳐 검사하고 그 실제 결과만 PR에 적는다. 잠금 blob·User-only node 원본·active plan 미변경을 함께 대조한다.
