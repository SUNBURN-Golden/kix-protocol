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
위치 동기화 기준(비-TL 잔여 행): observed origin/main `3ce6e4975b7f439d67482451bb47a22c940add26` (2026-10-12). 다시 맞춘 행은 EV-SET, EV-BRA, EV-CREDIT, EV-GATE, EV-READY의 source/fixture 목록, original32의 E01·F04 gap 포인터, Track K(K1, K2, K3 SDK, K4, K(a)), Track P(Wave2–5, catalogue/gate/readiness, AI delegation), RS-0, RS-1, 그리고 Finance/protocol 표의 read model 두 행이다. 병합되지 않은 노드 k-stage2-v5-impl, read-model-reference, rs-1은 not merged / DECISION_REQUIRED로 적는다. TL 행과 나머지 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다.
위치 동기화 기준(TL-L / TL-5): observed origin/main `aba875635f682bb9914e0dee016ced58e130cc04` (2026-10-13). 다시 맞춘 행은 TL-L / TL-5뿐이다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(v5·RS 병합 행): observed origin/main `ced0e2f42c0491753db91acf87bd61574eb37ce4` (2026-10-14). 다시 맞춘 행은 K2, RS-1, RS-2, RS-3a, RS-3b와 공유 evidence 색인에 새로 둔 EV-V5·EV-DELEG·EV-RS 행뿐이다. 2026-10-12 기준 줄이 기록한 k-stage2-v5-impl·rs-1의 not merged 표기는 이 동기화로 대체된다(read-model-reference는 그대로 not merged). 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(RS-4 L1→L2→L3, RS-5 / testnet keys, P AI delegation 행): observed origin/main `ea867668696d6b1114a443d0fe4e840d96b948f6` (2026-10-16). 다시 맞춘 행은 이 세 행뿐이다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-IR, RS-0, P AI delegation, RS-5 / testnet keys 행): observed origin/main `aca49f6e5498291c1f221185df1ee5cdbf333342` (2026-10-16). 다시 맞춘 행은 이 네 행뿐이다. P AI delegation과 RS-5 / testnet keys 행은 이 기준이 위 `ea867668696d6b1114a443d0fe4e840d96b948f6` 기준을 대체하고, RS-4 행은 `ea867668696d6b1114a443d0fe4e840d96b948f6`에 둔다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-SET, EV-CREDIT, EV-IR, EV-BRA, EV-READY, F04, P Wave5 credit 행): observed origin/main `244595db1524cbb1a01148baa07d6d28cd1b8dc6` (2026-10-17). 다시 맞춘 행은 이 일곱 행뿐이다. EV-SET·EV-CREDIT·EV-IR의 fixture 칸에는 #202·#203·#204의 시험 이름이 이미 있었고 이제 이 기준에 둔다. EV-BRA와 EV-READY에는 #206·#205 기록 포인터를 더했다. EV-CREDIT, F04, P Wave5 credit 행의 F04 해제 조건 문서 표기는 #192/#193에 쓴 관례(User merged (#160); 문서 자신의 채택 문장에 따라 O1만 채택; 잠금 유지)로 맞췄다. EV-IR 행은 이 기준이 위 `aca49f6e5498291c1f221185df1ee5cdbf333342` 기준을 대체한다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-READY 행): observed origin/main `08b317e5096893432116e41c8312697793500cfe` (2026-10-18). 다시 맞춘 행은 EV-READY뿐이다. fixture 칸에 JournalByteSweepTests의 관측 한계(길이 접두 손상, 0바이트 journal, 프레임 경계 절단)와 Astra 판정 보류를 더했다. EV-READY 행은 이 기준이 위 `244595db1524cbb1a01148baa07d6d28cd1b8dc6` 기준을 대체한다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-BRA, EV-V5, EV-READY, RS-0, RS-3a, RS-3b, RS-4, TL-3 offchain, TL-4 행): observed origin/main `01a86f66f1a2a0de98ae00f89e49d45ec07ec8da` (2026-10-20). 다시 맞춘 행은 이 아홉 행과 RS/TL evidence-map 안내, 검증·handoff checker 목록뿐이다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-SET, EV-READY, EV-V5, K1, K2, K5, P AI delegation, RS-4, TL-3 offchain, protocol read projection evidence 행): observed origin/main `a114b5bd67164dd1264bc4ad838566809b5bc0b4` (2026-10-21). 다시 맞춘 행은 이 열 행과 evidence-map 안내, 검증·handoff checker 목록뿐이다. EV-SET의 fixture 칸에는 #231의 시험 이름이 이미 있었고 이제 이 기준에 둔다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-RS, EV-READY, EV-V5, EV-BCS 행): observed origin/main `f6558996c611f74b88c60928f5b285c553303c14` (2026-10-22). 다시 맞춘 행은 이 네 행과 evidence-map 안내, 검증·handoff checker 목록뿐이다. RS-4 행의 measurement_gap 포인터는 위 `a114b5bd67164dd1264bc4ad838566809b5bc0b4` 기준에 이미 있어 그대로 둔다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-SET, EV-CREDIT 행): observed origin/main `d84cc50f78a37420ca9d12752ac23f9f9b51c5fc` (2026-10-22). 다시 맞춘 행은 이 두 행의 fixture 칸뿐이다. 두 칸에 거절 원자성 시험 모듈의 이름과 기록 포인터를 더했다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(RS-4, K5, EV-RS 행): observed origin/main `2393988eeca984f12f0819ac56b6870be1a5832f` (2026-10-23). 다시 맞춘 행은 이 세 행과 evidence-map 안내, 검증·handoff checker 목록뿐이다. RS-4 행에는 host 조건 기록기(#256) 포인터를, K5 행에는 `--self-test` CI 배선(#255) 포인터를, EV-RS 행에는 오프라인 suite 증거 인용 동기화(#257) 포인터를 더했다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-READY, EV-BRA, EV-SET, EV-CREDIT, RS-4 행): observed origin/main `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` (2026-10-23). 다시 맞춘 행은 이 다섯 행과 검증·handoff checker 목록뿐이다. EV-READY에는 migration 경계(#263), negative controls(#266, 검증 기록 없음), receipt·audit 시험(#268) 포인터와 지도 집계 27/0/9를, EV-BRA에는 seeded property(#267), EV-SET·EV-CREDIT에는 반환 데이터 격리(#265), RS-4에는 합성 산술·CSV 회귀(#262) 포인터를 더했다. error-code coverage 안내에는 BRA-RES9 포함 199행(#269)을 적었다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-RS, TL-3 offchain 행): observed origin/main `7327a00a68ef6efa81a795173af5e4572ccd90ef` (2026-10-24). 다시 맞춘 행은 이 두 행의 fixture 칸뿐이다. EV-RS에는 RS map gap closure batch 2(#274)의 Move 시험 이름과 `MoveParity.test_consume_private_signature_has_no_secret_or_witness_path` 포인터를, TL-3 offchain에는 reward 중첩 snapshot 격리(#275) 시험 모듈과 기록 포인터를 더했다. EV-SET·EV-CREDIT의 #265 포인터는 `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` 기준에 이미 있어 그대로 둔다. RS-C09·IM-18·IM-19 지도 행은 #274가 이미 갱신했고 이 동기화는 지도를 바꾸지 않는다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-BRA, EV-SET, EV-CREDIT, TL-3 offchain, P AI delegation 행): observed origin/main `d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313` (2026-10-25). 다시 맞춘 행은 이 다섯 행의 fixture 칸뿐이다. EV-BRA에는 반환 데이터 격리(#277)·리셀/검표 거절 원자성(#278)·restore fingerprint 동등성(#280) 시험 모듈을, EV-SET·EV-CREDIT·TL-3 offchain에는 #280 시험 모듈을, P AI delegation에는 #277·#279·#280 시험 모듈과 기록 포인터를 더했다. TL-3 offchain의 reward fingerprint class B 관측(#280)과 BRA clock-skew class B 관측(#278)은 각 기록과 owner에 그대로 둔다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
위치 동기화 기준(EV-SET, EV-BRA, EV-CREDIT, P Wave2 rights issuance 행, evidence-map 안내): observed origin/main `22df2e96d1a7de4d0de371a1f64776e80af9d999` (2026-10-25). 병합 범위 #281–#289: #281 `0db660a1085ca179c341c89129eeda763977b1fb`, #282 `ff88c441f36cde5b581ba29ce4c46ac47f22b218`, #283 `fe08e4134b2f2e58f48b636bdae7440d8cdb70dc`, #284 `590e544b3d097ba3de2fc573deae43b15bc39773`, #285 `c0fc5b4aed4da32284d9879ad21ef6b584db01d2`, #286 `a329ec07ac52ec15bff6c48079115d81ace5ab67`, #287 `53c16b226346f2df824f93a5756a080acd489ec1`, #288 `c7762c2724d5d28fd2e5e4f00cc5aae4f1f7908f`, #289 `22df2e96d1a7de4d0de371a1f64776e80af9d999`. #285·#286·#287 지도/checker와 #288 오프라인 fixture 포인터를 더했다. #289 checker 목록은 아래 handoff 안내에 이미 있다. #281–#283은 문서 정합화 기록이며 #284의 모듈은 기존 P AI delegation·TL-3 offchain 포인터에 둔다. 다른 행은 위 기준들 또는 2026-10-06 스냅샷에 둔다. 등급은 올리지 않는다. 실행 근거가 없는 자리는 not covered로 둔다.
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
2026-10-06 스냅샷 행의 경로는 그 base SHA에 고정한다. 2026-10-09·2026-10-12 위치 동기화로 옮긴 행과 2026-10-14·2026-10-16 동기화로 옮기거나 새로 둔 행은 각 동기화 기준의 경로다. 역사 앵커 K/M/Q/J는
`docs/status/ORIGINAL_32_STATUS.md`의 원 SHA/blob/CI로만 해석한다.

| ID | 현재 source | contract | fixture / coverage와 한계 |
|---|---|---|---|
| EV-K | `runtime/crates/kix-kernel/src/lib.rs` | `docs/contracts/CONTRACT_INVARIANTS.md`, `STATE_LIFECYCLE.md` | `runtime/crates/kix-kernel/tests/{transitions,quarantine_capacity,observation_slots,contract_invariants,contract_edge_cases,e4_state_model}.rs`; MOCK(memory). E-4 `support/model_v4.rs`는 source-informed, clean-room 아님 |
| EV-PERF | `runtime/crates/kix-kernel/tests/support/perf_probe.rs`, `examples/r1_perf_probe.rs` | `docs/contracts/PERFORMANCE_MEASUREMENT.md` | `runtime/crates/kix-kernel/tests/performance_harness.rs`; memory smoke/과거 Task 004 `validation/2026-09-25-task-004-perf-measurement/README.md`, DB/체인 p99 아님 |
| EV-MOVE | `reference/v0.3-rc1/sui/sources/{rights,zk_gate}.move` | `reference/v0.3-rc1/DESIGN_SUI_ZK.md`, `runtime/MOVE_PRODUCTION_TOPOLOGY.md` | `reference/v0.3-rc1/sui/tests/rights_tests.move`, `reference/v0.3-rc1/client/{localnet,localnet-paid,private,zk-regression}.mjs`, `zk/circuits/{mint,spend}.circom`; 16슬롯 reference, LOCALNET 재현 경로, 이번 NOT_RUN |
| EV-REF | `reference/v0.3-rc1/{core,commerce,assets,finance,execution_contracts}.py` | `reference/v0.3-rc1/protocol_contract.json` | `reference/v0.3-rc1/{test_core,test_commerce,test_assets,test_execution_contracts}.py`; MOCK 합성 계산·명령, 인증/실자금 아님 |
| EV-STORE | `reference/v0.3-rc1/{lifecycle,paid_recovery,paid_archive,storage_receipt}.py` | `reference/v0.3-rc1/KIX_v0.3_rc1_구현결과와_실행조건.md` | `reference/v0.3-rc1/{test_storage_receipt,test_paid_recovery,test_paid_archive}.py`; SQLite/local continuity fixture, LOCAL_DURABLE 경로, Rust stage5 아님 |
| EV-SET | `reference/settlement_f01_f03/{mock_settlement,settlement_fsm}.py` | `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md` §7 채택 초안(인용 위치 `docs/decisions/POLICY_DEEPENING_OWNER_DECISION_20261009.md`) | `reference/settlement_f01_f03/{test_mock_settlement,test_settlement_fsm,test_adopted_policy,test_settlement_properties,test_settlement_multi_payee_refund,test_settlement_rejection_atomicity,test_returned_data_isolation}.py`; MOCK 정수 KRW, first result·refund/replay·채택 정책 고정, 지급 아님; control comparison과 fault injection으로 거절 원자성을 고정, class B 관측은 `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md` 참조; #265 반환 데이터 격리 회귀·source-informed copy-isolation 특성화(`validation/2026-10-23-fsm-returned-data-isolation/README.md`); `reference/settlement_f01_f03/test_restore_fingerprint_equivalence.py`(#280, `validation/2026-10-25-restore-fingerprint-equivalence/README.md`, omitted/default replay across restore, 등급 변경 없음); `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md`·`scripts/check_settlement_evidence_map.py`(#285, 검토·수락 아님), `reference/settlement_f01_f03/test_primary_fee_split.py`(#288, PF-C01/PF-C02 오프라인, 등급 변경 없음) |
| EV-BRA | `reference/booking_resale_admission/{mock_gates,reservation_fsm,resale_fsm,admission_fsm,open_items}.py` | `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md` §7 초안 결정(인용 위치 `docs/decisions/POLICY_DEEPENING_OWNER_DECISION_20261009.md`) | `reference/booking_resale_admission/test_*.py`; MOCK overlapping holds, transfer/entry race, stale ownership, external-source refusal, open-item predicate; `test_adopt_issued_atomicity.py`(#206)는 거절된 `adopt_issued`가 resale·admission FSM에 gate 상태를 남기지 않음을 고정; `test_reservation_rejection_atomicity.py`(#219)는 contract §9.4의 ReservationMachine 명령이 닿는 모든 mutation boundary에서 control comparison과 `_rolls_back` fault injection으로 거절 원자성을 고정; `reference/booking_resale_admission/{test_gate_properties,bra_property_support}.py`(#267, `validation/2026-10-17-booking-resale-admission-seeded-property/README.md`, 2026-10-23 재개)는 source-informed seeded MOCK 시험이다. 그 기록의 class C finding은 옛 base에 대한 것이며 #206으로 고쳐졌으므로 현재 결함 근거로 인용하지 않는다; `reference/booking_resale_admission/test_returned_data_isolation.py`(#277, `validation/2026-10-24-bra-aid-returned-data-isolation/README.md`), `reference/booking_resale_admission/test_resale_rejection_atomicity.py`, `reference/booking_resale_admission/test_admission_rejection_atomicity.py`(#278, `validation/2026-10-24-resale-admission-rejection-atomicity/README.md`, clock-skew class B 특성화), `reference/booking_resale_admission/test_restore_fingerprint_equivalence.py`(#280); `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md`·`scripts/check_bra_evidence_map.py`(#286, 검토·수락 아님), `reference/booking_resale_admission/test_primary_price_binding.py`(#288, PF-C01 오프라인, 등급 변경 없음) |
| EV-CREDIT | `reference/credit_advance_f04/{mock_credit,credit_fsm,open_terms}.py` | `docs/contracts/CREDIT_ADVANCE_F04.md`(선택지 A 채택 초안), `docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md`(User merged (#160); per the document's own adoption sentence only O1 is adopted; lock stays) | `reference/credit_advance_f04/{test_mock_credit,test_credit_fsm,test_open_terms,test_credit_properties,test_credit_rejection_atomicity,test_returned_data_isolation}.py`; MOCK exposure·draw/repay·COMMITTED query·채택 terms, 규제 여신 아님; control comparison과 fault injection으로 거절 원자성을 고정, class B 관측은 `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md` 참조; #265 반환 데이터 격리 회귀·source-informed copy-isolation 특성화(`validation/2026-10-23-fsm-returned-data-isolation/README.md`); `reference/credit_advance_f04/test_restore_fingerprint_equivalence.py`(#280, `validation/2026-10-25-restore-fingerprint-equivalence/README.md`, omitted/default replay across restore, 등급 변경 없음); `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md`·`scripts/check_credit_evidence_map.py`(#287, 검토·수락 아님) |
| EV-GATE | `integration_gate/{catalogue,schema,server,recovery,fsm_contract,fsm_host,openapi_doc,audit,constants}.py` | `docs/contracts/openapi/{kix-protocol.contract-only.openapi,kix-protocol.integration-gate.openapi}.json`, `docs/contracts/openapi/fsm-command-contract.json`, `README.md` | `integration_gate/test_http_gate.py`, `scripts/check_openapi_contract.py`, `scripts/check_integration_gate_openapi.py`; MOCK opt-in loopback, actor fixture, 84 commands (40 core plus 44 FSM), `--browser-origin` CORS 기본 off·loopback 전용; FSM 이름을 새 endpoint로 추정 금지 |
| EV-READY | `readiness/{store,boundary,local_adapter,conformance,codec,machines,migrate,observe,policy,ai_delegation_wrap,reward_wrap}.py` | `docs/contracts/READINESS_RUNTIME.md`, `readiness/CONFORMANCE.md` | `readiness/test_faults.py`; LOCAL_DURABLE single writer, torn-tail/checksum/schema/restart/budget·schema-1 읽기·명시 migrate·관측 dict·예산 정책 모듈·ai_delegation wrap·reward wrap, production/truth/FSM durable false; `CrashPointSweepTests`(`readiness/test_faults.py`, #215)는 readiness-wrapped FSM machines의 command-level crash point 40 cases를 고정하지만 power-loss·`fsync`·durability 주장은 하지 않음(`validation/2026-10-18-readiness-crash-point-sweep/README.md`); `RewardWrapTests`(`readiness/test_faults.py`, #224)는 `reward_wrap.py`의 reward FSM local journal wrap을 등록·재시작/고장 시험으로 고정(`validation/2026-10-20-token-reward-readiness-wrap/README.md`), #226은 ai_delegation wrap의 conformance 시나리오·crash-point 셀을 추가(`validation/2026-10-20-ai-delegation-wrap-conformance/README.md`), #233은 reward wrap의 adapter-neutral conformance 시나리오와 `CrashPointSweepTests`의 reward 행을 추가(`validation/2026-10-21-reward-wrap-conformance/README.md`); `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`(#234, `docs/contracts/READINESS_RUNTIME.md` 절별 36행 지도: EXERCISED 27·PARTIAL 0·OPEN 9 (#268 기준), 빌더 해석이며 검토나 수락 아님)와 `scripts/check_readiness_evidence_map.py`(`validation/2026-10-21-readiness-runtime-evidence-map/README.md`), #239는 그 checker self-test의 PARTIAL 합성 fixture 교정(`validation/2026-10-21-readiness-checker-partial-fixture/README.md`); `JournalByteSweepTests`(`readiness/test_faults.py`, #205)의 class B 관측은 `validation/2026-10-17-readiness-journal-byte-sweep/README.md` 참조; 한계: 마지막이 아닌 프레임의 길이 접두 손상은 찢긴 꼬리로 읽혀 뒤의 확정 프레임을 조용히 자르고, 0바이트 journal은 재초기화되며, 프레임 경계 절단은 탐지되지 않는다. `docs/contracts/READINESS_RUNTIME.md` 21행에 대한 Astra 판정은 보류라서 중간 길이 손상에 대한 fail-closed 근거가 아니다(`readiness/CONFORMANCE.md` 참조); `MigrationEdgeTests`(`readiness/test_faults.py`, #263, `validation/2026-10-23-plan-readiness-migration-edge-tests/README.md`)는 명시 migration 경계 회귀; `readiness/test_conformance_sensitivity.py`(#266)는 negative controls이며 검증 기록은 없고 `readiness/CONFORMANCE.md` §Negative controls (fault sensitivity)를 참조; `integration_gate/test_http_gate.py`(#268)의 `test_core_receipt_replay_preserves_receipt_and_journal`, `test_checksum_valid_receipt_mismatch_refuses_startup`, `test_readiness_disabled_call_audits_inactive`, `test_append_failure_diverges_and_blocks_subsequent_commands`는 receipt replay·불일치 거절·inactive/diverged audit·후속 명령 차단을 고정(`validation/2026-10-23-readiness-receipt-audit-tests/README.md`) |
| EV-BCS | `runtime/crates/kix-bcs1/src/lib.rs`, `reference/v0.3-rc1/canonical_encoding.py`, `client/canonical_encoding.ts` | `runtime/CANONICAL_BINARY_BCS_V1.md` | `runtime/crates/kix-bcs1/tests/golden_vectors.rs`, `reference/v0.3-rc1/fixtures/canonical_encoding_v1.json`, `test_canonical_encoding.py`; SOURCE_ONLY/current execution NOT_RUN, BCS와 JSON/CE1 namespace는 별개; `kix-bcs1`이 쓰는 경계 타입 crate `kix-types`는 `runtime/crates/kix-types/tests/boundary_edges.rs`(#235)가 id·금액·카운터 생성자 경계를 in-memory로 고정하고(`validation/2026-10-21-kix-types-boundary-fixtures/README.md`), source-informed이며 완전성·wire·직렬화 주장은 없음 |
| EV-IR | `runtime/crates/kix-feature-ir/src/validation.rs`, `kix-feature-semantics/src/lib.rs` (같은 `runtime/crates/` 아래) | `runtime/FEATURE_SEMANTICS_V1.md` | `runtime/crates/kix-feature-ir/tests/{audit_regressions,plan_limits,schema_bound}.rs`, `runtime/crates/kix-feature-semantics/tests/semantics_v1_edges.rs`; `plan_limits.rs`는 FEATURE_SEMANTICS_V1 §10 한도(1,024 stages·깊이 64·100,000 nodes)의 in-memory 특성화(#196), 깊이 계산 방식은 계약 미정(class B), wire/parser 한도 not covered; `semantics_v1_edges.rs`는 scalar helper의 in-memory 특성화(음의 0 등 class B 기록), group/sort/aggregate/join 실행은 evaluator 없음으로 not covered; SOURCE_ONLY validator/scalar helpers, 전체 Polars/DuckDB/GPU compiler·dataset 인증 없음 |
| EV-V5 | `runtime/crates/kix-kernel-v5/src/lib.rs` | `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md`(O1, #138 병합)·`docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md` | `runtime/crates/kix-kernel-v5/tests/{boundary,conflict_index,holds,lifecycle_model,reclaim_batch,reclaim_report,stopped_transitions,termination,v4_differential}.rs`, `validation/2026-10-13-k-stage2-v5-impl/README.md`, `validation/2026-10-19-v5-lifecycle-seeded-model-test/README.md`, `docs/status/V5_TRANSITION_EVIDENCE_MAP.md`와 `validation/2026-10-20-v5-transition-evidence-map/README.md`(#225, 수명 계약 §§5–6 전이별 TESTED/STOPPED 위치 지도), `validation/2026-10-21-v5-evidence-citation-guard/README.md`(#247, `scripts/check_v5_transition_evidence_map.py`의 인용 유효성 가드만 고침: 지도 10행·TESTED 6·STOPPED 4·OPEN 0과 각 행 상태는 그대로이며 인용된 시험이 무엇을 단언하는지는 주장하지 않음); MOCK(memory). `lifecycle_model.rs`(#216)는 source-informed oracle의 seeded model test이며 독립 증명이 아님. 종결·state-changing 회수·review 해제는 정지 유지; retention 기본값의 소유자 2026-10-13 결정은 저장소 내 파일이 아님(그 기록이 플래그) |
| EV-DELEG | `runtime/crates/kix-delegated-exec/src/lib.rs` | `docs/contracts/RIGHTS_SCALE_PROFILE.md` §5·§10·§13(초안·미검토) | `runtime/crates/kix-delegated-exec/tests/{range_table,routing,ga_slots,delegation_fence,boundary}.rs`, `validation/2026-10-14-rs-3b-delegated-exec/README.md`; MOCK(memory). 위임 실행 활성화·grant TTL·체인 클라이언트·durable 없음 |
| EV-RS | `reference/rights_scale/sui/sources/{rights_scale,zk_gate}.move`, `reference/rights_scale/{model,test_model,test_private_model,replay,replay_private,compare_localnet,compare_private}.py`, `reference/rights_scale/client/*.mjs`, `reference/rights_scale/zk/circuits/{common,mint_scale,spend_scale}.circom` | `docs/contracts/RIGHTS_SCALE_PROFILE.md`(초안), `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md`, `docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md` | `reference/rights_scale/sui/tests/*.move`, `reference/rights_scale/vectors/{public_path,private_path}.json`, `validation/2026-10-14-rs-1-public-path/README.md`, `validation/2026-10-14-rs-1-issuercap-probe/README.md`, `validation/2026-10-14-rs-2-private-path/README.md`, `validation/2026-10-14-rs-3a-delegation-primitives/README.md`, `validation/2026-10-14-rs-3b-delegated-exec/README.md`, `reference/rights_scale/client/{zk-policy-v2,zk-helpers,ptau-header,witness-reconstruction,spend-witness,admission-packet,mint-note,verifier-binding}.test.mjs`, `validation/2026-10-21-plan-rs-{witness-offline-regressions,witness-ci-wiring,manifest-offline-regressions,zk-encoding-regressions,spend-witness-offline-tests,ptau-header-tests}/README.md`, `validation/2026-10-22-plan-rs-{offline-test-entrypoint,admission-packet-offline-tests,mint-wrapper-offline-tests,verifier-binding-offline-tests}/README.md`; LOCALNET(disposable localnet 여정, model은 인메모리 MOCK). 위 `*.test.mjs` 여덟 suite(#240–#253)는 합성 입력과 주입 stub을 쓰는 오프라인 시험이며 source-informed이고 localnet·체인·암호 독립 검증 결과가 아니다. `.github/workflows/protocol.yml`의 `rights-scale` job이 `Offline … regressions` step으로 실행하고(마지막 셋 admission packet·mint note·verifier binding은 `--experimental-test-module-mocks`), `reference/rights_scale/client/package.json`의 `test:offline` 스크립트(#248)가 같은 여덟 파일을 한 번에 실행한다. `validation/2026-10-22-rs-offline-suite-evidence-sync/README.md`(#257)는 두 RS 지도에 이 suite들의 이름 인용을 더한 빌더 작성 위치 기록이다. 등급은 바꾸지 않고 IM-17·IM-19의 PARTIAL과 UNDETERMINED 운영값(depth·K·shard·retention)은 그대로다. `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md`(#274)는 RS-C09 공개 소비 후 shield 거절(`a_publicly_consumed_ticket_cannot_be_shielded`)·IM-18 verifier 유지(`a_show_keeps_consuming_with_its_pinned_verifier_after_a_new_manifest_is_claimed`)와 다른 verifier 거절(`a_verifier_other_than_the_pinned_one_is_rejected`) Move 회귀, IM-19 source-informed gate signature 특성화(`MoveParity.test_consume_private_signature_has_no_secret_or_witness_path`)를 기록한다. IM-18만 COVERED_MODEL_OR_MEMORY로 바뀌며 등급 변경은 없다. 실자금·testnet/mainnet 아님 |

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
| E01 PG / 은행 | EV-K, EV-REF, EV-SET | partial MOCK | 제공자 인증·inbox·실 MID/가맹/은행 관측; I02–I08; `docs/operations/TOSS_SANDBOX_CONFORMANCE_PLAN.md`는 문서 전용 계획, 호출·자격 증명 없음 |
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
| F04 담보 / 선지급 / 금융상품 | EV-CREDIT | partial MOCK | 담보 우선순위/처분·실여신 unlock·법률; `docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md`는 해제 조건 목록; User merged (#160); per the document's own adoption sentence only O1 is adopted; lock stays |
| F05 원장 / 리스크 관리 | EV-REF, EV-STORE, EV-CREDIT | partial | adopted durable 원장·손실/상계/충당·risk policy |
| M01 팬 자격 / 멤버십 | 없음 | not covered | 발급/회수·동의·증명 계약; 외부 Wave7 gate |
| M02 선예매 | 없음 | not covered | 자격/우선순위/한도/재발급; 외부 Wave7 gate |
| M03 쿠폰 / 프로모션 | EV-REF | partial MOCK | coupon lifecycle·budget/order 원자성 |
| M04 추천 / 리워드 | 없음 | not covered | 귀속·부정사용·지급/회수; TL은 대체 완료 아님 |
| M05 CRM / 데이터 활용 | 없음 | not covered | 데이터/동의/접근 계약부터 없음; 원 라벨 미착수 |

## Track K / Track P 대응

| 요구 | 재사용 source/contract/fixture | coverage와 gap / gate |
|---|---|---|
| K1 E-4·수명·측정 | EV-K, EV-PERF; `docs/tasks/TASK_003A_E4_MODEL_SCHEMA.md`, `TASK_003B_E4_PROPERTY_EXPANSION.md`, `TASK_004_PERFORMANCE_MEASUREMENT.md`; `docs/contracts/ADAPTER_EVENT_IDENTITY.md` 초안 0.1, `docs/decisions/CUT_PROOF_I12_20261008.md` 증명 초안, `validation/2026-10-08-k1-adapter-event-identity/README.md`, `validation/2026-10-08-k1-evidence-close/README.md`, `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md`와 `validation/2026-10-20-adapter-identity-evidence-map/README.md`(#223, 계약 §§2–4 대응 위치 지도) | partial; 국소 regression 충분, I06는 계약 초안·I12는 미완결 증명 초안으로 남고 clean-room residual review·열린 입력은 잔여 |
| K2 lifecycle v5·retention | EV-K, EV-V5; `docs/contracts/STATE_LIFECYCLE.md`, `FIRST_BATCH_OPEN_INPUTS.md`; `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md`, `docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md`, `validation/2026-10-09-k2-retention-proposal/README.md`, `validation/2026-10-13-k-stage2-v5-impl/README.md`, `docs/status/V5_TRANSITION_EVIDENCE_MAP.md`, `validation/2026-10-20-v5-transition-evidence-map/README.md` | in-memory v5 slice merged (PR #179); MOCK(memory); 잠금 v4 수정 불가로 별도 crate; retention 기본값은 저장소 내 파일이 아닌 소유자 2026-10-13 결정에 의존(v5 검증 기록이 플래그, `RETENTION_PERIODS_PROPOSAL_20261009.md` §7과의 관계 미결); durable store·종결·state-changing 회수·review 해제는 not covered; Astra ARCHITECTURE 검토 기록은 이 트리에 없음 |
| K3 schema·SDK | EV-BCS, EV-GATE; `sdk/README.md`, `sdk/sdk-pin.json`, `docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md`, `sdk/compat/manifests/manifest.bootstrap-2.json`, `sdk/compat/profiles/bootstrap-2.profile.json` | partial. bootstrap-2 exists; semantic conformance consumer HOLD. p-sdk-1·supported schema별 독립 tuple conformance; stable 1.0/publish/rename 별도 결정 |
| K4 backend 비교 | EV-PERF, EV-READY; `docs/DEVELOPMENT_PLAN.md` §9; `exploration/stage4/`, `scripts/stage4_local_explore.py`, `validation/2026-10-08-k-stage4-local-exploration/README.md`, `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md`, `validation/2026-10-09-k-stage4-adoption-decision/README.md` | partial 준비 문서/공통 local fault·local 탐색 자료(제품 SLO·우열 아님); 5단계 로컬·비운영 PostgreSQL 선택은 결정 제안 병합 기록뿐 구현 없음; 후보 adapter·동등 ACK/goodput/p99/비용 fixture 없음, 운영 backend 채택 없음 |
| K5 durable tx/inbox/outbox | EV-READY/EV-STORE는 대체 아님; `docs/DEVELOPMENT_PLAN.md` §10; `scripts/check_stage5_host.py`와 `validation/2026-10-20-stage5-preflight/README.md`(#227)는 읽기 전용 host preflight 증거 준비일 뿐 option 선택·provisioning·수용 실행 아님; `--self-test`만 `.github/workflows/protocol.yml` stdlib step에 배선(#255), 수용 실행·provisioning 아님 | not covered Rust adopted backend; User ADOPT+v5 선행, DEFERRED/none yet/불명확 HOLD |
| K on-sale admission | `runtime/ONSALE_ADMISSION_CONTROL.md`만 | not covered; stage5와 아키텍처/정책 결정 후 구현 |
| K6 경제 reference | EV-REF, EV-SET, EV-BRA | partial 합성 계산; stage5+계약 심화 뒤 Rust 통합, 실 PG/은행 불포함 |
| K7 authenticated export·CPU SQL | EV-IR; `runtime/AUTHENTICATED_EXPORT.md`, `FEATURE_SEMANTICS_V1.md` | partial validator; exporter/consistent source cut/전체 Polars·DuckDB·독립 결과 fixture 없음; stage5 이후 |
| K8 native GPU | `runtime/{AI_GPU_DATA_PLANE,NATIVE_GPU_EXECUTION}.md`, `native_gpu/include/kix_gpu.h` | SOURCE_ONLY 문서/header; GPU runtime/measurement 없음, CPU 감사 후 계획 노드 |
| K(a) PR11 integration | historical J, `docs/status/PR11_PRESERVATION.md`; `docs/decisions/INTEGRATION_A_REESTIMATE_20261009.md`, `docs/decisions/INTEGRATION_A_DECISION_PROPOSAL_20261009.md`(문장 수정 없는 병합은 DEFERRED 기록), `validation/2026-10-09-k-a-reestimate/README.md`, `validation/2026-10-09-k-a-integration-decision/README.md` | not covered current integration; DEFERRED 기록은 착수 승인이 아니며 보존만, R2 금지 |
| P Wave0–1 charter/tracking | `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md` | SOURCE_ONLY; charter/issues는 runtime 기능 아님 |
| P Wave2 rights issuance | EV-MOVE; `docs/contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md` 초안 0.1(가격·수수료 값 미정); `reference/settlement_f01_f03/test_primary_fee_split.py`·`reference/booking_resale_admission/test_primary_price_binding.py`·`validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md`(#288; on-chain enforcement NOT_COVERED, 값·위치 DECISION_REQUIRED · Astra) | partial reference/localnet·가격/fee 계약 초안; 발행/실 PG 분리, 새 RS와 16슬롯 혼합 금지 |
| P Wave3 settlement | EV-SET; `reference/settlement_f01_f03/test_adopted_policy.py`, `docs/decisions/POLICY_DEEPENING_OWNER_DECISION_20261009.md` | MOCK 범위 기존 suite+채택 정책 고정; §7은 채택 초안, accounting·durability·실 지급 gap |
| P Wave4 booking/resale/admission | EV-BRA; `reference/booking_resale_admission/{open_items,test_open_items}.py`, `docs/decisions/POLICY_DEEPENING_OWNER_DECISION_20261009.md` | MOCK 범위 기존 races/negative suite+채택 open-item predicate; §7 초안 결정, real currentness·routing gap |
| P Wave5 credit | EV-CREDIT; `reference/credit_advance_f04/{open_terms,test_open_terms}.py`, `docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md` | MOCK 범위 기존 exposure/replay suite+채택 terms; 상품 정책 초안, 실여신/법적 담보 gap(해제 조건 문서: User merged (#160); per the document's own adoption sentence only O1 is adopted; lock stays) |
| P catalogue/gate/readiness | EV-GATE, EV-READY; `sdk/README.md`, `sdk/sdk-pin.json`, `docs/contracts/sdk/COMPATIBILITY_MANIFEST_V1.md`; `docs/contracts/READ_MODEL_QUERIES.md` 초안 0.1, `docs/decisions/GATE_BROWSER_ACCESS_DECISION_20261008.md`, `docs/decisions/OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md`, `docs/operations/PUBLIC_ENDPOINT_READINESS_PLAN.md`(문서 전용 계획) | partial. 84 commands (40 core plus 44 FSM). 계약 catalogue 존재 ≠ 새 FSM HTTP binding. bootstrap-2 exists; semantic conformance consumer HOLD. browser-origin CORS는 opt-in loopback으로 구현됨(기본 off); read-model-reference는 not merged / DECISION_REQUIRED, 쿼리 wire·카탈로그 삽입 없음. 공개 엔드포인트 잠금 유지 |
| P Wave6 commerce | `docs/decisions/PROGRAM_ROADMAP_20260930.md` R-7/R-8의 외부 포인터 | 외부 `kix-commerce-apps` source/browser/tests 이 checkout에서 미검증; stub/mock/loopback·w6a-evidence 구분, 병합/수용 host gate |
| P Wave7 marketing | pending catalogue, 원 M01–M05 | source/fixture 없음; commerce w6a-evidence 병합 확인+별도 plan revision, marketing stub는 계약 구현 아님 |
| P AI delegation | 모델1, Task005, `FIRST_BATCH_OPEN_INPUTS.md` I11/I12; `docs/contracts/AI_DELEGATION_AUTHORITY.md` 초안 0.1(실행 off), `reference/ai_delegation/{ai_delegation_mock,test_ai_delegation_mock}.py`, `readiness/ai_delegation_wrap.py`, `validation/2026-10-08-ai-delegation-contract-mock/README.md`; `.github/workflows/protocol.yml`의 offline suite 연결; `docs/decisions/AI_DELEGATION_EXECUTION_DECISION_PROPOSAL_20261016.md`, `validation/2026-10-16-ai-delegation-execution-decision/README.md`, `validation/2026-10-20-ai-delegation-wrap-conformance/README.md`(#226, wrap conformance 시나리오·crash-point 셀, 실행·durable 그대로 off/false), `reference/ai_delegation/test_returned_data_isolation.py`(#277), `reference/ai_delegation/test_rejection_atomicity.py`(#279, `validation/2026-10-25-aid-rejection-atomicity/README.md`), `reference/ai_delegation/test_restore_fingerprint_equivalence.py`(#280) | contract+오프라인 MOCK fixture만; 실행 활성화 결정은 User merged (#193); per the document's own adoption sentence only the recommended shape is adopted, `runtime/ARCHITECTURE.toml`의 `delegated_execution_enabled = false`와 잠금은 그대로; integration·실행 결정·A3·RS-3a/3b 후, AI 자기 권한 확대 금지 |

## RS / TL 요구·검증 gap

RS contract는 `docs/blueprints/rights-scale-v1/README.md` §8의 RS-C01–C17,
IM-01–IM-30이며 TL contract는 `docs/blueprints/optional-native-token-v1/README.md`
§12의 TK-1–TK-12, V1–V6다. 제안 술어 배정은 각각 RS-0/TL-0 확정 전이다.
확장 프로파일의 새 source/fixture는 main에 병합돼 EV-RS(`reference/rights_scale`)와
EV-DELEG(`runtime/crates/kix-delegated-exec`)로 색인한다(커널 v5는 EV-V5).
EV-MOVE는 비교용 16슬롯 regression이며
RS/TL 구현 evidence로 세지 않는다. 빌더 작성 지도 `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`(RS-C01..C17·RR-1..6), `docs/status/RS_IM_EVIDENCE_MAP.md`(IM-01..30), `docs/status/TL_PREDICATE_EVIDENCE_MAP.md`(TK-1..12·V1..6)는 각각 stdlib checker에 연결됐지만 검토나 수락이 아니다. 같은 성격의 빌더 작성 지도 `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md`(어댑터 정체성 계약 §§2–4), `docs/status/V5_TRANSITION_EVIDENCE_MAP.md`(수명 계약 §§5–6 전이), `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`(readiness 런타임 계약 절)도 각각 stdlib checker에 연결됐지만 검토나 수락이 아니다. 두 RS checker는 `reference/rights_scale/client/*.test.mjs`의 `::<node:test name>` 인용도 이름 존재만 확인한다(#257); 실행이나 술어 단언의 증명이 아니다. 같은 성격의 빌더 작성 지도 `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md`(#285), `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md`(#286), `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md`(#287)도 각각 stdlib checker에 연결됐지만(#289) 검토나 수락이 아니다.

| 요구 | source/fixture | coverage / 미충족 gate |
|---|---|---|
| RS-0 | `docs/contracts/RIGHTS_SCALE_PROFILE.md` 0.2 (초안), `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md`(#125 병합), `docs/status/RS_PREDICATE_EVIDENCE_MAP.md`, `docs/status/RS_IM_EVIDENCE_MAP.md`, 청사진 SOURCE_ONLY | 결정 초안 문서 병합만; 확정 조건의 Astra 아키텍처 검토·RS-C/IM 처리·상한·RR 선택·측정은 미충족 |
| RS-1, issuer-cap probe | EV-RS: `reference/rights_scale/` Move 패키지·model·vectors·localnet driver, `validation/2026-10-14-rs-1-public-path/README.md`, `validation/2026-10-14-rs-1-issuercap-probe/README.md` | merged (PR #180, probe PR #181); authorized against draft 0.1 @ 9b12626b (`docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md`); LOCALNET — RS-0 후 1,024 public localnet/IssuerCap 동시 probe를 실행해 동시 `&IssuerCap` 발행 tx가 직렬화됨을 측정(§13 선택은 OPEN·Astra 그대로); Astra ARCHITECTURE 검토 기록은 이 트리에 없음(프로파일 미검토) |
| RS-2 | EV-RS: `reference/rights_scale/sui/sources/zk_gate.move`, `reference/rights_scale/zk/circuits/{common,mint_scale,spend_scale}.circom`, `reference/rights_scale/client/{setup-zk,private-scale,private-localnet,zk-regression}.mjs`, `reference/rights_scale/vectors/private_path.json`, `validation/2026-10-14-rs-2-private-path/README.md` | merged (PR #182); localnet fixture만 (깊이 10 회로·Verifier·manifest v2·루트 규칙 RR-1~RR-6·비공개 여정, 단일 당사자 fixture ceremony, K·샤드 수·깊이는 시험 전용 값); Astra ARCHITECTURE 검토 기록은 이 트리에 없음(프로파일 미검토); 익명성·운영 ceremony·회로 감사·성능은 미주장, 비공개 리셀·환불·재발행·키 교체와 RS-4 측정은 not covered |
| RS-3a | EV-RS: `reference/rights_scale/sui/sources/rights_scale.move`(`GrantControl`·grant 수명주기·위임 다섯 경로·묶음), `reference/rights_scale/sui/tests/{support,delegation_tests}.move`, `reference/rights_scale/model.py`, `reference/rights_scale/vectors/public_path.json`(`rs3a_delegation_cut`), `reference/rights_scale/client/{localnet,types}.mjs`, `reference/rights_scale/compare_localnet.py`, `validation/2026-10-14-rs-3a-delegation-primitives/README.md` | merged (PR #183); localnet fixture만 (페이지 단위 grant·`GrantControl`·revocation cut·`undelegate_page` 회수·직접 경로 `EDelegated` 차단; RS-1 공개 경로·RS-2 비공개 경로 회귀 유지); Astra ARCHITECTURE 검토 기록은 이 트리에 없음(프로파일 미검토); 위임 실행·executor handoff·커널 lease/fence/GC·grant 만료/TTL·허용 연산 집합은 not covered; #221은 `delegation_tests.move`에 grant cut과 delegated paid issue/admission consume의 양쪽 순서를 고정; 페이지↔커널 대응은 EV-DELEG 인메모리 crate(RS-3b)로 옮김 |
| RS-3b | EV-DELEG: `runtime/crates/kix-delegated-exec/{Cargo.toml,clippy.toml,README.md}`, `runtime/crates/kix-delegated-exec/src/lib.rs`, `runtime/crates/kix-delegated-exec/tests/{common/mod.rs,range_table.rs,routing.rs,ga_slots.rs,delegation_fence.rs,boundary.rs,seeded_differential.rs}`, `docs/contracts/RIGHTS_SCALE_PROFILE.md` §5·§10·§13 초안 규칙 기록, `validation/2026-10-14-rs-3b-delegated-exec/README.md`, `validation/2026-10-17-delegated-exec-seeded-differential/README.md`, `validation/2026-10-19-rs-model-gap-closure/README.md` | merged (PR #184); in-memory crate tests만 (페이지↔커널 인벤토리 대응·좌석 페이지 ≤ `MAX_SEATS`·GA 카운터↔빈 슬롯 집합 대응·4,096석 초과 공연의 다중 페이지 동시 운영·grant 거울과 회수 cut의 fence 대응·공연→페이지 스코프 명령 정체); `seeded_differential.rs`(#212)는 source-informed oracle이고 #217은 `delegation_fence.rs`의 Python/Rust-closable map gap을 보강; Astra ARCHITECTURE 검토 기록은 이 트리에 없음(프로파일 미검토); 위임 실행 활성화·grant TTL/만료·허용 연산 집합·P 값·구획·행·열 대응·체인 클라이언트·durable은 not covered |
| RS-4 L1→L2→L3 | EV-RS; `validation/2026-10-15-rs-4-l1-load/README.md`, `scripts/run_rights_scale_l1_load.py`, `reference/rights_scale/load_plan.py`, `reference/rights_scale/summarize_load.py`, `reference/rights_scale/test_summarize_load.py`(#217); #262 합성 산술·CSV 회귀 (`validation/2026-10-23-plan-rs-summary-arithmetic-tests/README.md`), 측정·L2 아님, `reference/rights_scale/{measurement_gap,test_measurement_gap}.py`(#230, 기록 파일의 경로별 측정 공백 오프라인 집계; 측정·게이트·옵션 선택 아님), `reference/rights_scale/{host_conditions,test_host_conditions}.py`(#256, 부하 실행용 host 조건 샘플러·요약기; 임계값·판정·측정·L2 시도·옵션 선택 아님, 허용 부하는 UNDETERMINED·User), `reference/rights_scale/client/load-l1.mjs` | L1은 탐색 자료로만 병합됨(#190): 1,024-slot, 단일 validator, closed-loop localnet 측정이며 공개·비공개·위임 경로를 따로 보고하고 SLO·처리량·지연·gas·내구성·장애 허용 주장이 없다. L2는 병합되지 않은 draft PR #191에서 FAILED_MEASUREMENT로 기록되어 보류(이 트리에 기록 없음, 노드 입력 기준). L3는 not covered; 실제 16,384→65,536/복수 공연 raw workload·분모/지연·경로별 predecessors는 그대로 열림. Astra ARCHITECTURE 검토 기록은 이 트리에 없음 |
| RS-5 / testnet keys | `docs/decisions/TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md`, `validation/2026-10-16-testnet-key-management-decision/README.md` | not covered; 키 관리 형태는 User merged (#192); per the document's own adoption sentence only the recommended shape is adopted, 키·비밀·배포는 없다. Sui testnet 잠금(`docs/decisions/PROGRAM_DECISIONS_20260928.md` §5)은 그대로. independent Move/circuit audit·testnet 운영·책임자·별도 배포 승인은 not covered |
| TL-A | `docs/adr/0002-token-layer-scope-and-limits.md` | SOURCE_ONLY. 범위·한계 기록. 실행 가능한 authority fixture 없음. coin/TIX 잠금 해제 아님 |
| TL-0 | `docs/contracts/TOKEN_ROLE_AND_SUPPLY.md` | SOURCE_ONLY. 역할·공급 계약. 실행 가능한 authority fixture 없음. 그 계약은 이 계층의 시험이 아직 없다고 적는다 |
| TL-1 | `docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md` | SOURCE_ONLY. 권한·수명 계약. 실행 가능한 authority fixture 없음. 그 계약 §12: 이 계층의 권한 시험은 아직 없다 |
| TL price source / coin-lock ADR | `docs/decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md`, `docs/adr/0003-coin-tix-lock-localnet-re-ruling-request.md` | SOURCE_ONLY. not needed under the TL-0 recommendation. Astra re-ruling not recorded. lock unchanged. 가격원 값과 패키지 실행은 not covered |
| TL-2 | `docs/decisions/TL2_DOES_NOT_OPEN_20261009.md` | SOURCE_ONLY 기록. package와 fixture는 not covered. 잠금은 열리지 않음 |
| TL-3 offchain | `reference/token_reward/{token_reward_model,reward_fsm,test_reward_model,test_reward_fsm,test_reward_rejection_atomicity,test_snapshot_isolation}.py`, `docs/status/TL_PREDICATE_EVIDENCE_MAP.md`, `validation/2026-10-20-token-reward-rejection-atomicity/README.md`(#228), `validation/2026-10-20-token-reward-readiness-wrap/README.md`(#224, `readiness/reward_wrap.py`의 local journal wrap; EV-READY에 색인), `validation/2026-10-24-reward-snapshot-isolation/README.md`(#275, source-informed MOCK copy-isolation 특성화, 등급 변경 없음), `reference/token_reward/test_restore_fingerprint_equivalence.py`(#280, reward fingerprint class B 특성화, Astra 판단 대기, 등급 변경 없음) | MOCK. `.github/workflows/protocol.yml:140`에 suite가 연결되어 있다(PR #153). 37 tests는 `validation/2026-10-09-ci-wire-token-reward-suite/README.md`의 이전 로컬 기록이다. 이 위치 동기화는 그 기록을 실행 근거로 올리지 않는다. TL-4가 독립 검증을 소유한다 |
| TL-3 onchain | `docs/decisions/TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md` | SOURCE_ONLY 기록. package와 Move 시험은 not covered. 잠금은 열리지 않음. onchain은 TL-2와 offchain 뒤. KRW와 token은 분리 |
| TL-4 | `reference/token_reward/test_tl4_model_properties.py`, `reference/token_reward/test_tl4_fsm_properties.py`, `reference/token_reward/test_tl4_fuzz_boundaries.py`, `reference/token_reward/tl4_support.py`, `docs/decisions/TL4_THREAT_MODEL_20261009.md`, `docs/status/TL_PREDICATE_EVIDENCE_MAP.md` | MOCK. 작성자 측 하네스. `.github/workflows/protocol.yml:140` 루프가 `reference/token_reward`의 `unittest discover`로 `test_tl4_*.py`를 수집한다. `tl4_support.py`는 수집되지 않는다. 독립 검증은 not covered; 패키지가 필요한 술어는 NOT VERIFIABLE · no package |
| TL-L / TL-5 | `docs/decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md` | SOURCE_ONLY. testnet·mainnet·발행의 조건 목록 제안(병합 #166). 세 관문은 잠긴 채로 남는다. 실행 가능한 fixture 없음. not covered; 외부 법무/회계/세무/금융 서면·키/감사/운영 승인, issuance 자동 개방 없음 |

## Finance / protocol 후보 대응

Finance는 별도 repo/program이 아니다. 아래 **pending 정의를 현재 구현으로 세지 않는다**.
원 F01–F05는 위 동일 EV-SET/EV-CREDIT/EV-REF로 연결한다. Finance seed closure의
60/118 등 설계 시점 수치는 후보 DAG 기록이지 현 소스 검증/완료 수가 아니다.

| 후보 요구 | 재사용 evidence/contract | coverage / 새 구현·검증 gap |
|---|---|---|
| protocol runtime boundary register | 이 register와 EV 색인; protocol design §2 | 현 후보 전체 boundary register와 qualification은 별도 채택 대상, 본 노드 완료로 대신하지 않음 |
| protocol canonical identity conformance | EV-BCS; protocol design §5 | partial codec/vectors; 실제 supported Rust/TS/Move tuple·malformed/mixed-schema 독립 corpus |
| protocol FeatureIR conformance | EV-IR; protocol design §4 | partial validator/helpers; 전체 결과 oracle·dataset binding·CPU/GPU 실행 없음 |
| protocol read projection evidence | EV-GATE; protocol design §6; `docs/contracts/READ_MODEL_QUERIES.md` 초안 0.1, `reference/read_model/`, `validation/2026-10-20-read-model-contract-fixture-prep/README.md` | ReadObservationV1는 후보; source cut/watermark/cursor/visibility·현재 tuple fixture 없음, read-model-reference는 not merged / DECISION_REQUIRED; #229의 `reference/read_model/` 벡터는 후보 증거 기록일 뿐 conformance 증거 아님 |
| protocol local recovery conformance | EV-READY; protocol design §7 | partial local fault만; adopted stage5 transaction/ACK/inbox/outbox·UNKNOWN fixture 없음 |
| protocol integration closeout | contract completion design §§5–6 | 보호 receipt/승인/전체 active+pending+external 실제 완료 pack 없음 |
| fin-ledger-contract | Finance design §3; EV-SET/EV-CREDIT | not covered actual ADR/schema; 준비 문서는 가능, 없는 backend/cut 발명 금지 |
| fin-double-entry-projection | EV-SET/EV-REF 산술만; Finance §3 | not covered projection source/fixture; per-asset debit=credit·원 사건 unique·reversal/정수 범위 |
| fin-observation-reconciliation | EV-K/EV-SET mock 관측만; Finance §§2–4 | not covered authenticated identity/raw receipt/source cut·conflict/UNKNOWN/late fact reconciliation |
| fin-multi-payee-refund-proof | EV-SET refund negative suite; Finance §5 | partial mock; multi-payee 원 배분/refund reservation/conservation corpus·외부 반환 분리 |
| fin-credit-exposure-reconciliation | EV-CREDIT mock; Finance §5 | partial exposure; source-bound exposure/claim/repayment/refund·watermark gap corpus |
| fin-consistent-accounting-export | `runtime/AUTHENTICATED_EXPORT.md`; Finance §6 | not covered exporter; exact atoms/current tuple/snapshot/cursor/hash/schema·lag/partial-upload refusal |
| fin-catalogue-read-model | EV-GATE 비교만; Finance §7; `docs/contracts/READ_MODEL_QUERIES.md` 초안(신용 조회는 기존 view 키 인용만) | not covered finance query/SDK/manifest, read-model-reference는 not merged / DECISION_REQUIRED; unsupported는 not-bound, command substitution 금지 |
| fin-finance-closeout | Finance §§8–9 | not covered; 위 7 producer+commerce finance/refund/gift/reservation/resale/admission/delegation/session/E2E 실제 evidence, release HOLD |

stage5/6/7 없는 상황에서 준비 ADR을 기술 구현·Finance synthetic acceptance로 승격하지 않는다.
User decision 문서 병합 ≠ ADOPT. DEFERRED/none yet, DECLINED 뒤 별도 적용 범위 개정
없음, 불명확 승인은 후손 HOLD이며 분모에서 제거하지 않는다. 새 후보 채택·필수
A3/ARCHITECTURE 감사·merged dependencies·법무/회계/세무·provider 답변·출시 결정은
후속 구현/수용의 명시적 blocker다. 이 문서 산출물 자체의 결함과 구분한다.

## 검증·handoff

이번 위치 동기화 변경은 이 문서, `docs/README.md`, `scripts/check_status_register.py`,
`validation/2026-10-12-register-nontl-rows-sync/README.md` 넷이다. runtime/contract/CI/program/역사
evidence/reference는 수정하지 않았다. 새 runtime test는 없음.
`scripts/check_status_register.py`가 이 register 안의 backtick·link 경로 존재, EV-*
참조의 정의, 32개 원 ID의 첫 열 유일성을 검사한다(stdlib만). 이 checker와
`scripts/check_rs_profile_traceability.py`는 `.github/workflows/protocol.yml`의
guard 없는 step으로 연결됐다: docs-only 실행을 포함한 모든 non-draft 실행에서 돈다.
관측 origin/main `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200`에서 그 `Stdlib offline document checks` step의 checker는 열세 개이고 각각 plain과 `--self-test`로 돈다: `check_status_register.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_docs_index.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`, `check_tl_predicate_evidence_map.py`, `check_contract_error_codes.py`, `check_adapter_identity_map.py`, `check_v5_transition_evidence_map.py`, `check_readiness_evidence_map.py`. 이후 `scripts/check_stage5_host.py`가 `--self-test`만으로 같은 step에 추가됐다. 이 checker만 self-test 전용이다: plain 호출은 실행 호스트를 보고하며 CI runner는 고정 stage-5 호스트가 아니므로 배선하지 않는다. 이후 `check_settlement_evidence_map.py`, `check_bra_evidence_map.py`, `check_credit_evidence_map.py`가 각각 plain과 `--self-test`로 같은 step에 추가됐다(제품 계약 증거 지도 checker). 이 목록은 그 SHA 기준이며 `.github/workflows/protocol.yml`이 정본이다. 목록은 자동으로 동기화되지 않는다. `check_contract_error_codes.py`는 #269 이후 `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md`에 BRA-RES9 표를 포함해 199행을 보고한다.
2026-10-17 위치 동기화 변경은 `docs/DEVELOPMENT_PLAN.md`, 이 문서, `docs/README.md`,
`validation/2026-10-17-audit8-plan-register-index-sync-20261017/README.md` 넷이다.
2026-10-20 위치 동기화 변경은 `docs/DEVELOPMENT_PLAN.md`, 이 문서, `docs/README.md`, `validation/2026-10-20-plan-register-index-sync-20261020/README.md` 넷이다.
2026-10-21 위치 동기화 변경은 `docs/DEVELOPMENT_PLAN.md`, 이 문서, `docs/README.md`, `validation/2026-10-21-plan-register-index-sync-20261021/README.md` 넷이다.
2026-10-22 위치 동기화 변경은 `docs/DEVELOPMENT_PLAN.md`, 이 문서, `docs/README.md`, `validation/2026-10-22-plan-register-index-sync-20261022/README.md` 넷이다.
2026-10-23 위치 동기화 변경은 `docs/DEVELOPMENT_PLAN.md`, 이 문서, `docs/README.md`, `validation/2026-10-23-plan-register-index-sync-20261023/README.md` 넷이다.
2026-10-23 audit14 위치 동기화 변경은 `docs/DEVELOPMENT_PLAN.md`, 이 문서, `docs/README.md`, `validation/2026-10-23-audit14-plan-register-index-sync/README.md` 넷이다.
2026-10-25 위치 동기화 변경은 `docs/DEVELOPMENT_PLAN.md`, 이 문서, `docs/README.md`, `docs/status/LOOP_NODE_CROSSWALK.md`, `validation/2026-10-25-plan-register-index-crosswalk-sync/README.md` 다섯이다.
나머지 검사 명령과 결과는 그 validation 기록에 적는다. fixture 색인 자체를 실행
PASS로 사용하지 않는다.

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
