# 여신 고도화 후속 개발 제안·검증 지도

설계 후보. CR ID는 문서 내 추적용이며 실행 task key가 아니다. 기존 전체 118개·Finance 8개의 수, 상태, seed closure, 선행, manifest, 실행 포인터를 변경하지 않는다. 계획 편입 시 중복을 기존 노드의 승인 범위와 대조하고 개정 catalogue/DAG 검사를 수행한다.

## 1. 후속 산출물

| 후보 | 산출물 | 제안 내 선행 | 기존 노드 연결·중복 방지 | 인수 조건 |
|---|---|---|---|---|
| CR-01 | 상품/권위/버전/미정 입력 ADR | 없음 | `f04-mock-deepening`, `fin-ledger-contract`, `f04-real-funds-lift-criteria` | 기존 목 유지, 상품 범위·담당·게이트·호환 차이 확정 |
| CR-02 | claim 적격성·borrowing base 계약 | CR-01 | `settlement-policy-deepening`, `fin-credit-exposure-reconciliation` | 환불/부담·현재성·중복 slice·revision·재평가 부족 정의 |
| CR-03 | 약정·공유 한도·재원 예약 계약 | CR-02 | `k-stage5-durable-tx`, `k-stage6-economics-reference` | 같은 원자 범위에서 다중 한도 검사; UNKNOWN 포함 |
| CR-04 | 심사·동의·정책 변경 계약 | CR-01 | F04 policy, protocol canonical identity | 입력 출처·만료·이유·override·동의 증거; AI 권한 분리 |
| CR-05 | 지급 관측·복구 연결 | CR-03, CR-04 | `k1-adapter-event-identity`, `fin-observation-reconciliation` | 기존 inbox/outbox 재사용; 실제 rail 없이 합성 UNKNOWN/fault vectors |
| CR-06 | 상환표·상환 배분·조정 계약/모형 | CR-01, CR-05 | `fin-double-entry-projection`, `fin-multi-payee-refund-proof` | exact integer/rational, round 정책, suspense·reversal 보존식 |
| CR-07 | 연체·회수·손실·후기 입금 모델 | CR-06 | `fin-credit-exposure-reconciliation`, finance export | 채무/회계/case 분리, terminal 목 보존, 후기 사실 유지 |
| CR-08 | 여신 producer 계약·SDK 적합성 | CR-02, CR-03, CR-04, CR-05, CR-06, CR-07 | `fin-catalogue-read-model`, `contract-compatibility-profile` | 새 query/command의 exact tuple·vectors·manifest 검증 |
| CR-09 | Commerce 여신 journey·운영 desk | CR-08 | commerce `bind-credit-fsm`, `c-finance-projection`, `c-journey-identity` | 정상/거절/NOT_BOUND/STALE/UNKNOWN, actor/session fencing 브라우저 증거 |
| CR-10 | 여신 통합 수용·스트레스 패키지 | CR-09 | `fin-finance-closeout`, `e2e-browser-journeys` | 사건별 불변식·scope·증거, 합성 수용과 실자금 게이트 분리 |

위 표의 기존 노드 연결은 **범위 대응이며 자동 선행 추가가 아니다**. 새 CR-08→CR-09→CR-10 producer/consumer 순서를 유지하고 기존 finance closeout과 서로를 기다리는 순환을 만들지 않는다. 기존 노드 변경으로 편입할지 신규 노드로 둘지는 승인된 계획 개정에서 결정한다. 구현 단계는 표의 문서 선행 외에도 승인 backend·stage 5/6·현행 상품/운영 게이트를 충족해야 한다.

실행 순서는 (a) CR-01~04 문서·합성 벡터, (b) 승인된 local 구현 범위의 CR-05~07, (c) CR-08~09 계약 생산/소비, (d) CR-10 합성 수용이다. 실제 제공자 sandbox·실자금 운영은 기존 별도 unlock 경로다. source 완성, 합성 수용, 운영 준비를 하나의 DONE으로 합치지 않는다.

## 2. 기존 coverage와 남는 간극

소스 기준 `f931cfc87bdeaa1ed2495df0ce659ee832ac1c33`. 아래는 시험 소스를 읽은 대응표이며 이번 문서 작성에서 시험을 재실행한 결과가 아니다.

| 요구 | 기존 증거 | 판단 | 추가 확인 |
|---|---|---|---|
| 같은 draw/repay 중복 효과 방지 | `test_credit_fsm.py::test_same_draw_and_repay_notes_do_not_apply_twice` | 메모리 목 범위 충족 | DB crash/관측 중복/외부 제공자 경계 |
| 공유 액면 제한·현금 미가산 | `test_limit_race_is_ordered_and_cash_is_not_capacity`, `test_mock_credit.py::test_confirmed_cash_and_recovery_are_not_capacity` | 부분 | 차주/관계자/포트폴리오/재원 원자성 |
| 상환과 예약 해제 구분 | `test_repayment_order_partial_and_double_application`, `test_close_rejects_remaining_exposure_before_release` | 목 범위 충족 | 실제 입금·정책별 회전 한도 복원 |
| 부도 뒤 예약·소유권 보존 | `test_default_keeps_the_reservation_and_does_not_foreclose`, `test_credit_commands_do_not_mutate_resale_ownership` | 목 범위 충족 | 연체·조정·상각·후기 회수의 별도 case |
| replay | `test_reconcile_replays_the_journal_without_a_second_draw` | 부분 | 거절/UNKNOWN 내구 첫 결과와 과거 입력 복구 |
| snapshot·환불 | `test_refund_freeze_and_bad_inputs_follow_the_wave5_predicate` | 목 범위 충족 | 새 평가 revision·deficit·동시 draw |
| 실상품 실행 차단 | `test_unsupported_product_and_real_funds_do_not_change_state` | 목 범위 충족 | 새 profile도 승인 전 rail 차단 |
| 이자·상환표·심사·실입금·회수 | 현재 F04가 명시적으로 지원하지 않음 | 없음 | CR 계약·합성 oracle·독립 검토 |

시험 파일은 `reference/credit_advance_f04/` 아래에 있다. 기존 시험을 복제하거나 목의 false 플래그를 true로 바꿔 새 기능을 구현하지 않는다. 독립 oracle·정확한 정책 revision을 가진 vectors를 별도로 만든다.

## 3. 합성 시나리오와 증거 등급

[scenarios.json](scenarios.json)은 문서용 산술/사건 입력이며 실행 프로그램이나 상품 설정이 아니다. arbitrary 합성 단위 `SYNTHETIC_UNIT`만 사용한다. 금리·공급 자금·상품 조건을 운영 기본값으로 제공하지 않는다.

- 산술 예제: 가용 한도, 원자 예약의 경쟁, 재평가 부족, 상환 입금 배분 보존식.
- 사건 예제: 제공자 응답 유실, 늦은 지급/입금, 거절 재생, 약정 만료, 중복 claim, 과납, 상각 후 회수, 정책 변경.
- fault 검증: backend commit/outbox/관측/투영 경계마다 크래시·중복·역순을 주입한다. 원 command 첫 결과와 사실 보존을 oracle로 삼는다.
- 규모 검증: 활성 facility/claim/draw, 누적 사건, 동시 인출, 동일 차주 집중을 독립 축으로 늘린다. 플랫폼 슬롯 수를 대출 처리 TPS로 환산하지 않는다.

작성 단계는 산술·문서 링크·선행 DAG 확인만 수행한다. 런타임 시나리오 PASS, 내구성, 실입금 관측, 독립 감사, 운영 적합성을 주장하지 않는다. 실제 구현 수용 시 고정 source/schema/policy/SDK tuple, 각 사건의 입력·결과·원천 증거, 안전성 위반 수·분모·기간, p95/p99와 복구·비용 기준을 함께 제출한다.
