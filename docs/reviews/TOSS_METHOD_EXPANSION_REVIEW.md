# 토스 내 간편결제·가상계좌 수단 확장 검토

문서 전용 검토 · 2026-10-05 · 노드 `toss-method-expansion-review`.
원본 spec/source: `.aiops/program.json`, plan/base
`c8b806ebd0f959814acfd184edadf244bf18d1b4`, program blob
`ff0f39a8129ca8b8d30818cce35c3d4e588872fc`. canonical dependencies: 없음.

이 문서는 [토스 프로파일 §6·§8](../contracts/PG_TOSS_CARD_PROFILE.md)의
후속 검토 부록이다. [개발계획](../DEVELOPMENT_PLAN.md)의 국내 KRW 일반 카드
1단계 선택을 유지한다. 토스 경유 수단만 검토하며 간편결제 직접 가맹은 제외한다.
계약 개정·채택, 구현, 계정 발급, sandbox 또는 실제 PG/은행 호출은 하지 않는다.
토스 공개 자료의 기존 확인일은 **2026-09-17**이며 이번에 현행 웹 문서를 재확인하거나
토스 회신을 받지 않았다. 아래는 검토할 차이와 질문이지 제공자 동작의 새 확정값이 아니다.

## 1. 수단별 영향

| 경계 | 토스 내 간편결제 | 토스 내 가상계좌 |
|---|---|---|
| 어댑터 이벤트 | 프로파일 S4/S6에 따르면 카드 정보가 함께 있을 수 있다. `card` 존재만으로 일반 카드로 분류하지 않고 실제 method/type, 간편결제 제공자와 카드·머니·포인트 구성의 의미를 확인해야 한다. 인증/승인 신호, 취소 및 잔액 변화를 서로 구별할 검토가 필요하다 | 계좌 발급·입금 대기와 자금 수취 사실을 분리해야 한다. 발급/화면 성공/입금 안내를 capture로 옮기지 않는다. 프로파일 §6이 지적한 입금오류 재전이, 지연 입금·만료·취소 뒤 관측을 별도로 검토한다. 이벤트명·순서·최종성은 회신 전 UNDETERMINED |
| identity | 기존 KIX economic operation을 유지하고 provider/MID/환경/API·계약 버전/상품/수단/프로파일과 결합한다. 간편결제 브랜드 또는 하위 자금원을 새 operation으로 자동 분할하지 않는다. 각 구성과 승인·취소 거래를 어떤 ID로 식별하는지는 UNDETERMINED | 계좌번호·입금자명·`orderId`만으로 입금 event identity를 만들지 않는다. 계좌 발급, 재발급/재사용, 실제 입금 및 정정·환불의 관계를 확인해야 한다. 계좌번호의 재사용 여부·ID 보존 범위는 UNDETERMINED |
| 환불 | 카드·머니·포인트가 섞인 경우 취소 요청액, 실제 반환액, 원천별 반환 및 할인 복원을 구별할 필요가 있다. 전액/부분취소 지원, 순서, 한도, 실패·지연·중복과 완료 증거는 UNDETERMINED | 미입금 계좌 취소와 입금 후 환불을 구별한다. 환불계좌 필요 여부, 수취인 확인, 부분환불, 반대거래 및 입금오류 정정 의미는 UNDETERMINED. 환불계좌 등 개인정보를 fixture·Git에 넣지 않는다 |
| 정산 | 구매자가 사용한 포인트/할인과 가맹점이 받을 채권·수수료·실입금은 같은 금액이라는 보장이 없다. 승인 총액·원천별 구성·취소·제공자 정산의 결합을 확인해야 한다 | 입금 확인, 가맹점 정산 예정, 실제 은행 입금, 이후 조정/반환을 각각 구별한다. 입금 완료가 분리 지급이나 모든 수취인 지급 완료라는 뜻은 아니다 |

## 2. 공통 경계와 미지원 사실

- transmission, event-item, payment, provider transaction과 stable economic operation은
  서로 다른 정체성이다. `paymentKey`는 상태가 바뀌어도 같은 결제의 키이며 단독
  event ID가 아니다. `lastTransactionKey`를 고정 capture ID로 대체하지 않는다.
  반복 snapshot, 중복 전송, 정정 및 순서 역전의 매핑은 별도 노드
  `k1-adapter-event-identity`의 미완결 I06을 유지한다. 이번에 schema를 정의하지 않는다.
- 일반 결제 웹훅 서명 미확정은 두 수단에도 남는다. 가상계좌의 특정 인증 필드가
  있더라도 전체 본문 서명·재전달 방지·모든 이벤트 인증을 보장한다고 확장하지 않는다.
  프로파일 §4의 미검증 신호/계정 결합 인증 조회/원문 증거 분리를 따른다.
  수신·발생·적용 시각을 분리하고 snapshot을 전체 거래 이력으로 취급하지 않는다.
- timeout, 조회 실패/부재, 만료 또는 취소 문자열로 UNKNOWN을 해제하거나 새 키·새 PG로
  같은 operation을 다시 실행하지 않는다. 원operation, 최초 결과와 늦은 자금 사실은
  보존한다. 미지원 수단의 사실도 버리지 않고 대사 대상으로 남기되 새 권리·전송을
  승인하지 않는다. 늦은 입금으로 만료 주문을 부활시키거나 다른 주문의 재고를 해제하지 않는다.
- [STATE_LIFECYCLE](../contracts/STATE_LIFECYCLE.md)의 LC-FACT/LC-CUT/LC-TERM
  경계를 유지한다. 카드 전용 승인 사실 미확인 종결 경로를 두 수단에 자동 승계하지 않는다.
  계좌 발급·미입금과 카드 승인 부재는 같은 종결 증거가 아니다.
  `ReturnRequired`는 실제 환불 완료가 아니며 정정도 원capture를 삭제하는 허가가 아니다.
- [정산 목 계약](../contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md)의 채권/의무,
  확인 현금, 환불 의무와 실제 지급을 분리한다. 원결제 총액·취소별 금액·잔액·수수료·
  정산 조정의 대사가 필요하되 새 계산식·배분 정책·법적 채무 의미를 여기서 정하지 않는다.
  복수 수취인 지급은 프로파일 §8의 미확인 가맹 질문 그대로다.

## 3. 토스 답변 및 결정 입력

모든 행은 **UNDETERMINED**다. 사용자와 아래 담당자가 실제 MID/환경/상품/API·계약
버전별 서면 자료를 확보해야 한다. 질문을 보냈거나 답을 받았다는 기록이 아니다.

| ID | 질문·필요한 증거 | 답할 주체 | 미확정 시 차단 |
|---|---|---|---|
| TM01 | 지원 간편결제 브랜드/자금원 및 가상계좌 상품, 일반 예매·리셀·금융별 허용 여부, 추가 계약/MID 요건은 무엇인가? | 사용자·토스 영업/계약 담당 | 해당 수단 가맹·운영 수취 |
| TM02 | 간편결제의 method/type 및 card/easyPay 구성별 금액·할인·포인트 의미, 승인/취소 상태와 거래 이력 예시는 무엇인가? | 토스 기술 담당 | 원천별 금액 및 capture 정규화 확정 |
| TM03 | 가상계좌 발급/입금/만료/취소/입금오류 정정의 상태·이벤트·조회 필드, 늦은/중복/부족/초과/분할 입금 처리와 순서 역전 가능성은 무엇인가? | 토스 기술 담당 | 입금의 경제 효과 및 종결 해석 확정 |
| TM04 | 수단별 전송/이벤트/승인/입금/취소/정정 ID의 불변성·유일 범위는? 재전달, 반복 조회, 계좌 재발급/재사용 때 무엇이 유지되는가? | 토스 기술 담당·어댑터 계약 담당(I06) | stable event 매핑 확정; I06 완료 주장 |
| TM05 | 각 웹훅의 인증·서명/secret 범위, 키 교체, 재전달 정책, 인증 조회 및 거래 이력의 접근/보존 범위는? 카드의 공개 멱등키 규격이 각 승인/발급/취소 API에도 적용되는가? | 토스 기술/보안 담당(I04/I07/I08/I13) | 인증 사실·재송신 안전성·증거 완전성 주장 |
| TM06 | 간편결제 혼합 원천의 전액/부분취소와 할인·포인트 복원, 가상계좌 미입금 취소/입금 후 환불의 API·한도·계좌 검증·실패/지연 상태·완료 증거는? | 토스 기술/계약 담당 | 환불 요청/완료 매핑·운영 환불 |
| TM07 | 수단별 총액/순액/수수료/정산일·정산 ID·취소 조정 자료, 입금오류 정정과 이미 정산된 금액 회수는 어떻게 연결되는가? 복수 수취인 분리 지급이 계약상 가능한가? | 토스 정산/계약 담당·사용자 | 정산 대사·분리 지급 확정 |
| TM08 | 예약 만료와 입금 기한 관계, 지연 입금 대응·환불 비용 부담·지원기간·SLO를 어떻게 정할 것인가? | 제품 정책 담당·Astra·사용자 | DECISION_REQUIRED · Astra. 새 정책값/명령 도입 |
| TM09 | 환불계좌/입금자 개인정보 최소 수집·보관·삭제 보류, 현금영수증/세금 및 채권·수익 인식은 무엇인가? | 사용자·법무/개인정보·세무·회계 담당, 토스 증빙 담당 | 법률·세무·회계 적합성 및 운영 승인 |

## 4. 기존 증거 대응과 인수 경계

| 요구 | 기존 coverage | 이번 산출물 |
|---|---|---|
| 수단별 이벤트·identity | 부분: 토스 프로파일 §4·§6·§7, FIRST_BATCH_OPEN_INPUTS I06 | §1·§2·TM02–TM05가 차이와 질문을 보완. 매핑 설계/실연동 검증은 없음 |
| 수단별 환불·정산 | 부분: 프로파일 §8, 정산 목 계약 §0·§9와 `reference/settlement_f01_f03/test_mock_settlement.py`, `test_settlement_fsm.py` | §1·§2·TM06–TM09가 외부 미정 입력을 보완. 목 시험은 토스 환불·지급 증거가 아님 |
| 통합 수단 검증 | 없음: 두 수단의 실제 제공자 conformance 증거 없음 | 새 테스트를 복제하지 않는다. 문서 검토만으로 제공자 적합성을 주장하지 않음 |

인수 기준은 두 수단 각각의 이벤트/identity/환불/정산 영향과 필요한 토스 답변을
기록하고, 잠금·기존 계약·정책값을 유지하는 것이다. 후속 sandbox 계획 노드
`toss-sandbox-conformance-plan`은 이 문서와 별도 I06 노드에 의존하며 여기서 수행하지 않는다.
실 PG/은행 호출과 실자금은 프로그램 결정 §5의 외부 입력·sandbox 증거·사용자 승인
전까지 차단된다. 새 공개 계약은 별도 권위 채택 대상이다.

Mac 구현 checkpoint는 legacy DONE, 감사 PASS, 병합 또는 운영 승인 증거가 아니다.
독립 exact-head 검토, 호스트 신뢰 확인, application의 Draft 게시, 실제 최종 head의
KTX/KIX hosted CI, 지정 감사 게이트 및 사용자 최종 supervision/병합은 별도다.
로컬 확인 결과가 이 게이트를 대신하지 않는다. 실연동·서명·내구성·실제 환불/정산·
법적 적합성·production readiness는 검증하거나 주장하지 않는다.

## 5. 로컬 확인과 후속 게이트 — 2026-10-05

base, 관측 `origin/main`, 구현 시작 HEAD는 모두
`c8b806ebd0f959814acfd184edadf244bf18d1b4`다. 호스트가 fetch를 수행했으며
작성자는 Git 메타데이터를 변경하지 않았다. 원본 `.aiops/program.json`과 위 정본을
`git show <base>:<path>`로 대조했다. 이 노드의 변경 경로는 이 부록 한 파일이다.
커널 두 파일의 작업 전 blob은 AGENTS.md §4 요구값과 일치했다.

기존 mock 경계의 회귀는 충분히 있으며 중복 테스트를 추가하지 않는다.
`reference/settlement_f01_f03/test_mock_settlement.py`의
`test_f02_statement_does_not_infer_fee_or_shrink_faces`,
`test_f03_partial_refund_blocks_distribution_without_reclassifying`,
`test_f03_full_refund_reclassifies_and_mock_acceptance_is_not_closure`와
`reference/settlement_f01_f03/test_settlement_fsm.py`의
`test_same_key_replays_and_a_different_body_is_rejected`,
`test_external_payment_attempts_leave_the_journal_unchanged`가 정산/환불/멱등성 및
외부 실행 거절을 다룬다. 이는 §4의 수단별 제공자 coverage가 부분/없음이라는
판정을 바꾸지 않는다. 새 증거는 §1–§3의 검토·질문 대응표다.

아래 명령은 모두 실제 실행했고 exit 0을 확인했다(Python 3.10.1).

| 명령 | 실제 결과 |
|---|---|
| `python3 -B -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 20 tests · OK |
| `python3 -B -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 43 tests · OK |
| `python3 -B -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 20 tests · OK |
| `python3 -B scripts/check_openapi_contract.py` | 40 commands · pin OK |
| `python3 -B scripts/check_openapi_contract.py --self-test` | pass |
| `python3 -B scripts/check_integration_gate_openapi.py` | 40 commands · productionEndpoint=false, publicHost=false |
| `python3 -B scripts/check_integration_gate_openapi.py --self-test` | pass |

`scripts/verify_runtime_architecture.py`는 `tomllib`이 필요하므로 로컬 Python
3.10.1에서는 실행하지 않았다. 검증기·CI를 변경하지 않고 지원 Python을 쓰는 일반
exact-head hosted CI에서 확인한다. Rust/Move/ZK·전체 protocol 실행도 이 로컬 결과에는
포함하지 않는다. 계약 위반은 발견하지 않았으며 제공자 의존 미정 부분은 TM01–TM09에
담당과 차단 범위를 남긴다. 최종 commit/CI run ID·독립 검토·지정 A2/NONE 게이트·
User supervision은 application의 후속 증거이며 미확보 PASS나 merge-ready를 선언하지 않는다.
