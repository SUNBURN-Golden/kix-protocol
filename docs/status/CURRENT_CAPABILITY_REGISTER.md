# 현재 capability / coverage register

## 입력·판정 범위

노드 `k-current-capability-map` (Mac task
`MAC-0B6C5AD76F624CE1BF8577DE13EB110C-E6CEC419A163`). 원 spec와 sources는
`.aiops/program.json`이다. canonical 선행은 **`roadmap-sync`** 그대로다.
그 선행의 ACCEPTED/병합 판정은 host 소유이며 이 문서는 재판정하지 않는다.
관측 origin/main, 작업 HEAD, 요구·소스 기준은 모두
`2554173ebdda0922aaf7a0bc7ea773075187a3d9` (2026-10-06)이다.
그 줄은 당시 스냅샷의 기록으로 둔다.
위치 동기화 기준: observed origin/main `eb14da2a6c5b5366cd4aed855bd453dcb4d79a42` (2026-10-09).
2026-10-09 위치 동기화는 TL-A, TL-0, TL-1, TL price source / coin-lock ADR, TL-2, TL-3 offchain, TL-3 onchain, EV-GATE, K3, P catalogue/gate/readiness 행의 경로만 그 기준으로 옮긴다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다. 나머지 행은 2026-10-06 스냅샷이다.
위치 동기화 기준(TL-3 onchain, TL-4): observed origin/main `5e20a467160148ad5c2debfe357dfb8da084a30a` (2026-10-09). 다시 맞춘 행은 TL-3 onchain과 TL-4뿐이다. 위 문장의 다른 행은 `eb14da2a6c5b5366cd4aed855bd453dcb4d79a42`에 둔다.
프로그램 blob은 `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`.
`git show <base>:<path>`로 고정 입력과 현재 바이트를 대조했다.
이 register는 현재 소스의 색인이다. 기존 라벨·승인·완료 predicate를 바꾸지 않는다.

정본은 `docs/DEVELOPMENT_PLAN.md`, `docs/decisions/AUTHORITY_MODEL_1.md`,
`docs/decisions/PROGRAM_ROADMAP_20260930.md`,
`docs/decisions/PROGRAM_DECISIONS_20260928.md`다. Task 005 charter와 RS/TL
청사진은 이 결정과 함께 읽는다. `docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md`,
`FINANCE_COMPLETION_DESIGN_KO.md`, `CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md`는
**pending 후보**이며 구현·운영 승인으로 사용하지 않는다. 등록/확대 후보와
`docs/decisions/PROGRAM_ROADMAP_20260930_PENDING.json`의 외부 선행도 보존한다.

| 근거 등급 | 이 문서에서 뜻하는 것 | 완료로 올릴 수 없는 것 |
|---|---|---|
| SOURCE_ONLY | 실제 소스 또는 계약만 확인; 실행은 따로 기록 | 문서, 헤더, stub, 미실행 fixture는 기능/운영 PASS가 아님 |
| MOCK | 합성 입력·인메모리 reference/FSM의 제한된 동작 | 실 PG·은행·KYC·실여신·법적 의무·체인 확정 |
| LOCAL_DURABLE | 명시한 로컬 파일/SQLite 재시작 경계의 구현 | 운영 원장·분산 fencing·전원/매체 장애 보장·FSM durable |
| LOCALNET | disposable Sui package/network의 제한된 여정 | testnet/mainnet·운영 규모·실자금·독립 ceremony |
| OPERATIONAL | 별도 unlock·실환경·감사·수용 근거가 있어야 함 | **이 register에 인정한 운영 근거 없음** |

등급은 순차 승급 점수가 아니다. source 존재, 기존 실행 evidence, 이번 실행을
분리한다. 아래 fixture 경로는 재사용할 coverage이며 모든 suite를 이번에 실행했다는
뜻이 아니다. 범위 밖 운영 요구는 전부 not covered / NOT_RUN이다.
모델1에서 체인 재고·권리 권위, 오프체인 약정/위임 실행, 제공자 자금 관측은
각각 다르다. `captured`, FSM `COMMITTED`, 로컬 generation은 다른 권위의
성공·finality·새 실행 허가를 대신하지 않는다.

## 공유 evidence 색인

동일 ID는 아래의 동일 자산을 참조한다. 여러 행 연결을 여러 구현/독립 시험으로 세지 않는다.
2026-10-06 스냅샷 행의 경로는 그 base SHA에 고정한다. 2026-10-09 위치 동기화로 옮긴 행은 그 동기화 기준의 경로다. 역사 앵커 K/M/Q/J는
`docs/status/ORIGINAL_32_STATUS.md`의 원 SHA/blob/CI로만 해석한다.

| ID | 현재 source | contract | fixture / coverage와 한계 |
|---|---|---|---|
| EV-K | `runtime/crates/kix-kernel/src/lib.rs` | `docs/contracts/CONTRACT_INVARIANTS.md`, `STATE_LIFECYCLE.md` | `runtime/crates/kix-kernel/tests/{transitions,quarantine_capacity,observation_slots,contract_invariants,contract_edge_cases,e4_state_model}.rs`; MOCK(memory). E-4 `support/model_v4.rs`는 source-informed, clean-room 아님 |
| EV-PERF | `runtime/crates/kix-kernel/tests/support/perf_probe.rs`, `examples/r1_perf_probe.rs` | `docs/contracts/PERFORMANCE_MEASUREMENT.md` | `runtime/crates/kix-kernel/tests/performance_harness.rs`; memory smoke/과거 Task 004 `validation/2026-09-25-task-004-perf-measurement/README.md`, DB/체인 p99 아님 |
| EV-MOVE | `reference/v0.3-rc1/sui/sources/{rights,zk_gate}.move` | `reference/v0.3-rc1/DESIGN_SUI_ZK.md`, `runtime/MOVE_PRODUCTION_TOPOLOGY.md` | `reference/v0.3-rc1/sui/tests/rights_tests.move`, `client/{localnet,localnet-paid,private,zk-regression}.mjs`, `zk/circuits/{mint,spend}.circom`; 16슬롯 reference, LOCALNET 재현 경로, 이번 NOT_RUN |
| EV-REF | `reference/v0.3-rc1/{core,commerce,assets,finance,execution_contracts}.py` | `reference/v0.3-rc1/protocol_contract.json` | `reference/v0.3-rc1/{test_core,test_commerce,test_assets,test_execution_contracts}.py`; MOCK 합성 계산·명령, 인증/실자금 아님 |
| EV-STORE | `reference/v0.3-rc1/{lifecycle,paid_recovery,paid_archive,storage_receipt}.py` | `reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md` | `reference/v0.3-rc1/{test_storage_receipt,test_paid_recovery,test_paid_archive}.py`; SQLite/local continuity fixture, LOCAL_DURABLE 경로, Rust stage5 아님 |
| EV-SET | `reference/settlement_f01_f03/{mock_settlement,settlement_fsm}.py` | `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md` | `reference/settlement_f01_f03/{test_mock_settlement,test_settlement_fsm}.py`; MOCK 정수 KRW, first result·refund/replay, 지급 아님 |
| EV-BRA | `reference/booking_resale_admission/{mock_gates,reservation_fsm,resale_fsm,admission_fsm}.py` | `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md` | `reference/booking_resale_admission/test_*.py`; MOCK overlapping holds, transfer/entry race, stale ownership, external-source refusal |
| EV-CREDIT | `reference/credit_advance_f04/{mock_credit,credit_fsm}.py` | `docs/contracts/CREDIT_ADVANCE_F04.md` | `reference/credit_advance_f04/{test_mock_credit,test_credit_fsm}.py`; MOCK exposure·draw/repay·COMMITTED query, 규제 여신 아님 |
| EV-GATE | `integration_gate/{catalogue,schema,server,recovery}.py` | `docs/contracts/openapi/{kix-protocol.contract-only.openapi,kix-protocol.integration-gate.openapi}.json`, `docs/contracts/openapi/fsm-command-contract.json`, `README.md` | `integration_gate/test_http_gate.py`, `scripts/check_openapi_contract.py`, `scripts/check_integration_gate_openapi.py`; MOCK opt-in loopback, actor fixture, 84 commands (40 core plus 44 FSM); FSM 이름을 새 endpoint로 추정 금지 |
| EV-READY | `readiness/{store,boundary,local_adapter,conformance}.py` | `docs/contracts/READINESS_RUNTIME.md`, `readiness/CONFORMANCE.md` | `readiness/test_faults.py`; LOCAL_DURABLE single writer, torn-tail/checksum/schema/restart/budget, production/truth/FSM durable false |
| EV-BCS | `runtime/crates/kix-bcs1/src/lib.rs`, `reference/v0.3-rc1/canonical_encoding.py`, `client/canonical_encoding.ts` | `runtime/CANONICAL_BINARY_BCS_V1.md` | `runtime/crates/kix-bcs1/tests/golden_vectors.rs`, `reference/v0.3-rc1/fixtures/canonical_encoding_v1.json`, `test_canonical_encoding.py`; SOURCE_ONLY/current execution NOT_RUN, BCS와 JSON/CE1 namespace는 별개 |
| EV-IR | `runtime/crates/kix-feature-ir/src/validation.rs`, `kix-feature-semantics/src/lib.rs` (같은 `runtime/crates/` 아래) | `runtime/FEATURE_SEMANTICS_V1.md` | `runtime/crates/kix-feature-ir/tests/{audit_regressions,schema_bound}.rs`; SOURCE_ONLY validator/scalar helpers, 전체 Polars/DuckDB/GPU compiler·dataset 인증 없음 |

EV-SET의 `test_full_refund_acceptance_does_not_close_an_external_return`, EV-CREDIT의
`test_bound_draw_waits_for_mock_commit_and_does_not_claim_finality`, EV-BRA의
`test_payment_fact_is_not_funds_and_expiry_does_not_compensate`는 합성 성공을
운영 성공으로 세지 않을 기존 negative coverage다. EV-READY의
`StoreTests.test_protocol_truth_label_cannot_be_written`과 conformance의 false-label
assertions를 재사용한다. 이미 충분한 이 경계를 복제하는 runtime test는 추가하지 않는다.

## original32 요구별 대응·검증 gap

원 이름·라벨·분모는 `ORIGINAL_32_STATUS.md` 그대로: 0/0/0/31/1.
아래 coverage는 종단 요구에 대해 **모두 부분(partial)** 또는 **없음(not covered)**이다.
부분 소스가 늘어도 historical 24/32, 34 links, 4 anchors 집계를 수정하지 않는다.

| ID / 요구 | 현재 evidence | coverage | 추가 구현·독립/실환경 검증 gap |
|---|---|---|---|
| E01 PG / 은행 | EV-K, EV-REF, EV-SET | partial MOCK | 제공자 인증·inbox·실 MID/가맹/은행 관측; I02–I08 |
| E02 블록체인 / 체인 권리 | EV-MOVE | partial LOCALNET path | 배타 grant·회수 cut·현재성; RS-3; 현재 블록 KIX 권위 계층 |
| E03 운영자 / 주최자 | EV-MOVE, EV-K | partial MOCK/source | 실 주체 인증·권한 회수·환불 채무자 |
| E04 판매 채널 / 앱 / 웹 | EV-GATE, EV-BCS | partial MOCK/source | generated 0.x SDK/manifest/current tuple 독립 소비; 다른 repo 앱 미검증 |
| E05 AI / 분석 | EV-IR | partial SOURCE_ONLY | 인증 export·전체 실행·AI grant·자원 격리 |
| E06 규정 / 컴플라이언스 | 없음; EV-CREDIT는 합성 경계만 | not covered | 법무/개인정보/회계·보존·당사자 서면 입력 |
| P01 권리 발행 | EV-MOVE, EV-BRA | partial | 위임 세대/원재고 소진/독립 확정 |
| P02 권리 이전 | EV-MOVE, EV-BRA | partial | production 양도 정책/결제 결합 |
| P03 검표 / 사용 | EV-MOVE, EV-BRA | partial | 운영 routing·offline/current ownership·독립 검표 |
| P04 정산 / 분배 | EV-SET, EV-REF | partial MOCK | durable obligations·다수 실제 지급·대사 |
| P05 정책 엔진 | EV-REF, EV-K | partial MOCK | 인증 PolicyVersion·변경 권한 결합 |
| P06 감사 / 추적 | EV-READY, EV-STORE | partial LOCAL_DURABLE | 권위별 source cut·원문 인증/가용성·수명; historical J는 미통합 |
| B01 공연 / 이벤트 등록 | EV-MOVE, EV-BRA | partial | 주최자 인증·ShowConfig 원권위 |
| B02 좌석 / 재고 관리 | EV-K, EV-BRA | partial MOCK | chain grant 배타성·durable 예약 |
| B03 가격 / 할인 정책 | EV-REF, EV-BRA | partial MOCK | 승인 가격/fee·인증 견적과 주문 결합 |
| B04 주문 / 결제 | EV-K, EV-REF, EV-BRA | partial MOCK | durable order/payment·실 관측·발행 결합 |
| B05 예매 확정 | EV-K, EV-BRA | partial MOCK | 예약/지급/발행 구분·구매자 증거 가용성 |
| R01 재판매 등록 | EV-MOVE, EV-BRA | partial | 실 판매자 권한·채널간 intent lock |
| R02 양도 규칙 | EV-MOVE, EV-BRA | partial | 인증 policy·실 가격/자격 강제 |
| R03 2차 거래 결제 | EV-MOVE, EV-BRA, EV-SET | partial | durable transfer/payment/보상과 실 관측 |
| R04 소유권 이전 | EV-MOVE, EV-BRA | partial | chain Right/PaymentEvidence 현재성·확정 |
| R05 사기 / 중복판매 방지 | EV-K, EV-MOVE, EV-BRA | partial | 독립 채널/실행자 배타성·인증 |
| F01 정산채권 / 의무 | EV-SET, EV-MOVE | partial MOCK/source | 법적 채무자·귀속·채권 소멸 |
| F02 분할정산 | EV-SET, EV-REF | partial MOCK | waterfall 승인·실 지급·잔여 의무 |
| F03 환불 / 취소 | EV-SET, EV-K, EV-MOVE | partial | ReturnRequired와 실환불 분리·외부 반환 종결 |
| F04 담보 / 선지급 / 금융상품 | EV-CREDIT | partial MOCK | 담보 우선순위/처분·실여신 unlock·법률 |
| F05 원장 / 리스크 관리 | EV-REF, EV-STORE, EV-CREDIT | partial | adopted durable 원장·손실/상계/충당·risk policy |
| M01 팬 자격 / 멤버십 | 없음 | not covered | 발급/회수·동의·증명 계약; 외부 Wave7 gate |
| M02 선예매 | 없음 | not covered | 자격/우선순위/한도/재발급; 외부 Wave7 gate |
| M03 쿠폰 / 프로모션 | EV-REF | partial MOCK | coupon lifecycle·budget/order 원자성 |
| M04 추천 / 리워드 | 없음 | not covered | 귀속·부정사용·지급/회수; TL은 대체 완료 아님 |
| M05 CRM / 데이터 활용 | 없음 | not covered | 데이터/동의/접근 계약부터 없음; 원 라벨 미착수 |

## Track K / Track P 대응

| 요구 | 재사용 source/contract/fixture | coverage와 gap / gate |
|---|---|---|
| K1 E-4·수명·측정 | EV-K, EV-PERF; `docs/tasks/TASK_003A_E4_MODEL_SCHEMA.md`, `TASK_003B_E4_PROPERTY_EXPANSION.md`, `TASK_004_PERFORMANCE_MEASUREMENT.md` | partial; 국소 regression 충분, clean-room residual review·I06 identity·I12 cut proof·열린 입력/evidence close 남음 |
| K2 lifecycle v5·retention | EV-K의 기존 경계만; `docs/contracts/STATE_LIFECYCLE.md`, `FIRST_BATCH_OPEN_INPUTS.md` | 새 v5 source/fixture 없음; 설계 User 병합·A3·보존 입력 뒤 별도 crate, 잠금 v4 수정 불가 |
| K3 schema·SDK | EV-BCS, EV-GATE; `sdk/README.md`, `sdk/sdk-pin.json`, `docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md` | partial. bootstrap-2 exists; semantic conformance consumer HOLD. p-sdk-1·supported schema별 독립 tuple conformance; stable 1.0/publish/rename 별도 결정 |
| K4 backend 비교 | EV-PERF, EV-READY; `docs/DEVELOPMENT_PLAN.md` §9 | partial 준비 문서/공통 local fault; 후보 adapter·동등 ACK/goodput/p99/비용 fixture 없음, backend 채택 없음 |
| K5 durable tx/inbox/outbox | EV-READY/EV-STORE는 대체 아님; `docs/DEVELOPMENT_PLAN.md` §10 | not covered Rust adopted backend; User ADOPT+v5 선행, DEFERRED/none yet/불명확 HOLD |
| K on-sale admission | `runtime/ONSALE_ADMISSION_CONTROL.md`만 | not covered; stage5와 아키텍처/정책 결정 후 구현 |
| K6 경제 reference | EV-REF, EV-SET, EV-BRA | partial 합성 계산; stage5+계약 심화 뒤 Rust 통합, 실 PG/은행 불포함 |
| K7 authenticated export·CPU SQL | EV-IR; `runtime/AUTHENTICATED_EXPORT.md`, `FEATURE_SEMANTICS_V1.md` | partial validator; exporter/consistent source cut/전체 Polars·DuckDB·독립 결과 fixture 없음; stage5 이후 |
| K8 native GPU | `runtime/{AI_GPU_DATA_PLANE,NATIVE_GPU_EXECUTION}.md`, `native_gpu/include/kix_gpu.h` | SOURCE_ONLY 문서/header; GPU runtime/measurement 없음, CPU 감사 후 계획 노드 |
| K(a) PR11 integration | historical J, `docs/status/PR11_PRESERVATION.md` | not covered current integration; 별도 승인 전 보존만, R2 금지 |
| P Wave0–1 charter/tracking | `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md` | SOURCE_ONLY; charter/issues는 runtime 기능 아님 |
| P Wave2 rights issuance | EV-MOVE | partial reference/localnet; 가격/fee·발행/실 PG 분리, 새 RS와 16슬롯 혼합 금지 |
| P Wave3 settlement | EV-SET | MOCK 범위 충분한 기존 suite; §7 policy/accounting·durability·실 지급 gap |
| P Wave4 booking/resale/admission | EV-BRA | MOCK 범위 기존 races/negative suite 재사용; §7 policy·real currentness·routing gap |
| P Wave5 credit | EV-CREDIT | MOCK 범위 기존 exposure/replay suite 재사용; 상품 정책·실여신/법적 담보 gap |
| P catalogue/gate/readiness | EV-GATE, EV-READY; `sdk/README.md`, `sdk/sdk-pin.json`, `docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md` | partial. 84 commands (40 core plus 44 FSM). 계약 catalogue 존재 ≠ 새 FSM HTTP binding. bootstrap-2 exists; semantic conformance consumer HOLD. read queries·CORS 결정/구현 gap |
| P Wave6 commerce | `docs/decisions/PROGRAM_ROADMAP_20260930.md` R-7/R-8의 외부 포인터 | 외부 `kix-commerce-apps` source/browser/tests 이 checkout에서 미검증; stub/mock/loopback·w6a-evidence 구분, 병합/수용 host gate |
| P Wave7 marketing | pending catalogue, 원 M01–M05 | source/fixture 없음; commerce w6a-evidence 병합 확인+별도 plan revision, marketing stub는 계약 구현 아님 |
| P AI delegation | 모델1, Task005, `FIRST_BATCH_OPEN_INPUTS.md` I11/I12 | contract/mock/integration 현재 fixture 없음; A3 계약·RS-3a/3b·실행 결정 후, AI 자기 권한 확대 금지 |

## RS / TL 요구·검증 gap

RS contract는 `docs/blueprints/rights-scale-v1/README.md` §8의 RS-C01–C17,
IM-01–IM-30이며 TL contract는 `docs/blueprints/optional-native-token-v1/README.md`
§12의 TK-1–TK-12, V1–V6다. 제안 술어 배정은 각각 RS-0/TL-0 확정 전이다.
새 프로파일 source/fixture는 **없음**. EV-MOVE는 비교용 16슬롯 regression이며
RS/TL 구현 evidence로 세지 않는다.

| 요구 | source/fixture | coverage / 미충족 gate |
|---|---|---|
| RS-0 | 청사진 SOURCE_ONLY | RS-C/IM 처리·객체/권위·상한·RR 선택, A3/사용자 수락 |
| RS-1, issuer-cap probe | EV-MOVE 비교만, 새 source 없음 | not covered; RS-0 후 1,024 public localnet/IssuerCap 동시 probe |
| RS-2 | 기존 circuit 비교만, 새 source 없음 | not covered; RS-1·RR 채택 후 root/circuit/verifier/manifest-v2·cross-context 거부 |
| RS-3a | 없음 | not covered; page grant/GrantControl/revocation cut, RS-1/A3 |
| RS-3b | EV-K 비교만 | not covered; RS-3a+v5; GA counter/slot·4,096 cap·세대/회수 대응 미확인 |
| RS-4 L1→L2→L3 | 없음 | not covered; 실제 1,024→16,384→65,536/복수 공연 raw workload·분모/지연·경로별 predecessors |
| RS-5 / testnet keys | 없음 | not covered; independent Move/circuit audit·키관리 결정·testnet 운영·책임자·User 운영 결정 |
| TL-A | `docs/adr/0002-token-layer-scope-and-limits.md` | SOURCE_ONLY. 범위·한계 기록. 실행 가능한 authority fixture 없음. coin/TIX 잠금 해제 아님 |
| TL-0 | `docs/contracts/TOKEN_ROLE_AND_SUPPLY.md` | SOURCE_ONLY. 역할·공급 계약. 실행 가능한 authority fixture 없음. 그 계약은 이 계층의 시험이 아직 없다고 적는다 |
| TL-1 | `docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md` | SOURCE_ONLY. 권한·수명 계약. 실행 가능한 authority fixture 없음. 그 계약 §12: 이 계층의 권한 시험은 아직 없다 |
| TL price source / coin-lock ADR | `docs/decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md`, `docs/adr/0003-coin-tix-lock-localnet-re-ruling-request.md` | SOURCE_ONLY. not needed under the TL-0 recommendation. Astra re-ruling not recorded. lock unchanged. 가격원 값과 패키지 실행은 not covered |
| TL-2 | `docs/decisions/TL2_DOES_NOT_OPEN_20261009.md` | SOURCE_ONLY 기록. package와 fixture는 not covered. 잠금은 열리지 않음 |
| TL-3 offchain | `reference/token_reward/{token_reward_model,reward_fsm,test_reward_model,test_reward_fsm}.py` | MOCK. `.github/workflows/protocol.yml:140`에 suite가 연결되어 있다(PR #153). 37 tests는 `validation/2026-10-09-ci-wire-token-reward-suite/README.md`의 이전 로컬 기록이다. 이 위치 동기화는 그 기록을 실행 근거로 올리지 않는다. TL-4가 독립 검증을 소유한다 |
| TL-3 onchain | `docs/decisions/TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md` | SOURCE_ONLY 기록. package와 Move 시험은 not covered. 잠금은 열리지 않음. onchain은 TL-2와 offchain 뒤. KRW와 token은 분리 |
| TL-4 | `reference/token_reward/test_tl4_model_properties.py`, `reference/token_reward/test_tl4_fsm_properties.py`, `reference/token_reward/test_tl4_fuzz_boundaries.py`, `reference/token_reward/tl4_support.py`, `docs/decisions/TL4_THREAT_MODEL_20261009.md` | MOCK. 작성자 측 하네스. `.github/workflows/protocol.yml:140` 루프가 `reference/token_reward`의 `unittest discover`로 `test_tl4_*.py`를 수집한다. `tl4_support.py`는 수집되지 않는다. 독립 검증은 not covered; 패키지가 필요한 술어는 NOT VERIFIABLE · no package |
| TL-L / TL-5 | 없음 | not covered; 외부 법무/회계/세무/금융 서면·키/감사/운영 승인, issuance 자동 개방 없음 |

## Finance / protocol 후보 대응

Finance는 별도 repo/program이 아니다. 아래 **pending 정의를 현재 구현으로 세지 않는다**.
원 F01–F05는 위 동일 EV-SET/EV-CREDIT/EV-REF로 연결한다. Finance seed closure의
60/118 등 설계 시점 수치는 후보 DAG 기록이지 현 소스 검증/완료 수가 아니다.

| 후보 요구 | 재사용 evidence/contract | coverage / 새 구현·검증 gap |
|---|---|---|
| protocol runtime boundary register | 이 register와 EV 색인; protocol design §2 | 현 후보 전체 boundary register와 qualification은 별도 채택 대상, 본 노드 완료로 대신하지 않음 |
| protocol canonical identity conformance | EV-BCS; protocol design §5 | partial codec/vectors; 실제 supported Rust/TS/Move tuple·malformed/mixed-schema 독립 corpus |
| protocol FeatureIR conformance | EV-IR; protocol design §4 | partial validator/helpers; 전체 결과 oracle·dataset binding·CPU/GPU 실행 없음 |
| protocol read projection evidence | EV-GATE; protocol design §6 | ReadObservationV1는 후보; source cut/watermark/cursor/visibility·현재 tuple fixture 없음 |
| protocol local recovery conformance | EV-READY; protocol design §7 | partial local fault만; adopted stage5 transaction/ACK/inbox/outbox·UNKNOWN fixture 없음 |
| protocol integration closeout | contract completion design §§5–6 | 보호 receipt/승인/전체 active+pending+external 실제 완료 pack 없음 |
| fin-ledger-contract | Finance design §3; EV-SET/EV-CREDIT | not covered actual ADR/schema; 준비 문서는 가능, 없는 backend/cut 발명 금지 |
| fin-double-entry-projection | EV-SET/EV-REF 산술만; Finance §3 | not covered projection source/fixture; per-asset debit=credit·원 사건 unique·reversal/정수 범위 |
| fin-observation-reconciliation | EV-K/EV-SET mock 관측만; Finance §§2–4 | not covered authenticated identity/raw receipt/source cut·conflict/UNKNOWN/late fact reconciliation |
| fin-multi-payee-refund-proof | EV-SET refund negative suite; Finance §5 | partial mock; multi-payee 원 배분/refund reservation/conservation corpus·외부 반환 분리 |
| fin-credit-exposure-reconciliation | EV-CREDIT mock; Finance §5 | partial exposure; source-bound exposure/claim/repayment/refund·watermark gap corpus |
| fin-consistent-accounting-export | `runtime/AUTHENTICATED_EXPORT.md`; Finance §6 | not covered exporter; exact atoms/current tuple/snapshot/cursor/hash/schema·lag/partial-upload refusal |
| fin-catalogue-read-model | EV-GATE 비교만; Finance §7 | not covered finance query/SDK/manifest; unsupported는 not-bound, command substitution 금지 |
| fin-finance-closeout | Finance §§8–9 | not covered; 위 7 producer+commerce finance/refund/gift/reservation/resale/admission/delegation/session/E2E 실제 evidence, release HOLD |

stage5/6/7 없는 상황에서 준비 ADR을 기술 구현·Finance synthetic acceptance로 승격하지 않는다.
User decision 문서 병합 ≠ ADOPT. DEFERRED/none yet, DECLINED 뒤 별도 적용 범위 개정
없음, 불명확 승인은 후손 HOLD이며 분모에서 제거하지 않는다. 새 후보 채택·필수
A3/ARCHITECTURE 감사·merged dependencies·법무/회계/세무·provider 답변·출시 결정은
후속 구현/수용의 명시적 blocker다. 이 문서 산출물 자체의 결함과 구분한다.

## 검증·handoff

이번 변경은 이 문서 하나다. runtime/contract/CI/program/역사 evidence/reference는 수정하지
않았다. 새 runtime test는 없음. 새 gap은 여섯 영역의 현재 source/fixture 연결과 없는
근거의 명시다. register의 경로 존재·32 ID 유일성/원 이름·evidence reference·필수
영역·잠금 blob·고정 입력 동일성·변경 경계를 로컬에서 검사한다. fixture 색인 자체를
실행 PASS로 사용하지 않는다.

2026-10-06 실제 실행 기록 (아래 최종 검사 모두 exit 0, Python 3.10):

| command/check | 결과·실패 사례 범위 |
|---|---|
| `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 20 tests OK; mock 정산/환불·illegal transition·first-result conflict·외부 실행 거부 |
| `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 43 tests OK; hold/transfer/consume·중복/stale/외부 source 거부; test-owned loopback 종료 |
| `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 20 tests OK; mock draw/repay/exposure·중복/잔여 exposure/미관측 commit 거부 |
| `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest readiness.test_faults` | 14 tests OK; local restart/budget·torn/checksum/schema/false truth labels, power-loss 아님 |
| `python3 scripts/check_openapi_contract.py` 및 `--self-test` | 현재 pin 40 commands OK; negative self-test PASS |
| `python3 scripts/check_integration_gate_openapi.py` 및 `--self-test` | 40 commands, productionEndpoint/publicHost false OK; negative self-test PASS |
| `git diff --check`, `git status --short` | whitespace OK; 새 register 하나만 변경 |
| Python inline integrity check | 32 원 ID/이름 유일·일치, 12 EV 참조 완결, brace/glob 확장 97 경로 존재; 잠금 2 blobs·원 program blob/dependency 일치; reference 108 tracked files를 base 바이트와 대조해 불변 |

위 표의 「40 commands」 수치는 2026-10-06 `2554173` 기준의 기록이다.

첫 inline 검사에서는 `git ls-tree`의 quoted Unicode 경로를 그대로 `git show`에
넘겨 exit 1이었다. NUL-delimited `git ls-tree -rz --name-only`로 수정한 재검사는
exit 0이다. baseline을 고치지 않았다. Git의 sandbox xcrun cache/사용자 ignore
접근 경고와 별개로 읽기 검사의 종료 코드와 출력 값을 확인했다.
Rust/Move/ZK 전체 suite, 전체 HTTP suite, localnet/실환경은 이번 NOT_RUN.
문서만 변경했으며 fixture PASS를 전체 기능 qualification으로 만들지 않는다.
필수 hosted KTX/KIX 판정은 app가 실제 최종 head에 대해 수집해야 한다.

잠금 expected blobs:
`runtime/crates/kix-kernel/src/lib.rs = 69564b166f0c27f9af5d8422f0a466b18d74c20f`;
`runtime/crates/kix-kernel/tests/quarantine_capacity.rs = b607996c83a119c349f1cc90469ac1ba82764e20`.
전후 실제 대조를 요구하며 transient mutation도 하지 않는다.

역사 CI는 `docs/status/BASELINES.md` 및 `ORIGINAL_32_STATUS.md`의 정확한 과거
SHA에만 속한다. 새 source tests로 재라벨링하지 않는다. PR11 J는 보존 실험이고
current durable kernel source가 아니다. 실제 funds/provider/bank/KYC/public endpoint,
testnet/mainnet/token, R2/새 engine·production durability·GPU·browser UI는 이번 NOT_RUN.
UI 변경 없음. 운영 capability 인정 수는 **0**이며 전체 종단 완료율은 계산하지 않는다.

이 산출물의 구현 인계 이후 **A2 비작성자 검토 → app Draft 게시 → 실제 exact-head
KTX kernel verification 및 KIX protocol verification → 독립 최종 supervision**이 남는다.
Draft skipped/absent CI는 PASS가 아니다. Workflow의 docs-only 성공도 전체 suite 실행과
구분해야 한다. 검토/감사·source gate·User-only merge·post-merge CI·release 조건은 유지한다.
미커밋 문서에는 자기 미래 SHA나 CI run을 만들지 않으며 app가 실제 delivery head와
검사 결과를 밖에서 결합한다. 구현 인계는 legacy DONE/merge-ready/프로그램 완료가 아니다.
