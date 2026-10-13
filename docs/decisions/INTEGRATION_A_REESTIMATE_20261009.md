# 통합 (a) 잔여 공수 재산정 (2026-10-09)

노드 `k-a-reestimate`. 이슈는 없다. PR #11 저널의 통합 (a)에 대해, 첫 묶음의 잔여 통합 검토·증거 마감이 닫힌 뒤의 계획용 잔여 공수다. 대상은 셋이다. T0는 잠금 v4 그대로, T1는 계획된 `kix-kernel-v5` crate, T2는 T1에서 저널 역할을 5단계 로컬 PostgreSQL에 두는 경우다.

## 0. 상태와 효력

상태: **추정.** 결정이 아니다. 이 파일은 독립 검토가 아니다. 작성자가 빌더이므로, 비작성자 exact-HEAD 검토가 아니다.

입력은 노드 명세와 그것이 가리키는 문서다. 사용자 결정은 다음 노드 `k-a-integration-decision`이다. [로드맵](PROGRAM_ROADMAP_20260930.md) 101행·219행이 그 순서를 적는다.

이 문서는 아무것도 승인하지 않는다. (a)의 착수, R2, 저널, 저장 엔진, v5 crate의 구현, 5단계 영속 거래를 승인하지 않는다. 아래 인일은 계획용 범위다. 청구 공수, 납기, 견적이 아니다. 실제 작업시간표는 없고, 실제 소진 인일은 **숫자 없음**이다.

빌더는 병합하지 않는다. `k-a-integration-decision`, `k-stage2-v5-impl`, `k-stage5-durable-tx`를 시작하지 않는다. 이 세션은 커밋, 푸시, PR, 이슈, 댓글을 만들지 않는다.

## 1. 기준

- 작업 시작 시 `git fetch origin main` 뒤의 `origin/main`과 HEAD: `bb193efb5d238581096372c8a20bee1271dfe4df`. 같은 커밋이다. 브랜치는 `agent/kix-k-a-reestimate`다. 이 세션은 커밋하지 않으므로 구현 커밋 SHA는 없다. 나중의 커밋 SHA에 이 기준의 CI를 옮기지 않는다.
- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 두 파일은 수정하지 않는다. 문서 추가 뒤에 다시 계산한다.
- `docs/tasks/`에는 이 노드의 과제 파일이 없다. 이슈도 없다. 과제 파일과 이슈를 만들지 않았고 고치지 않았다.
- 명세가 가리키는 줄은 현재 본문과 맞다. [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) 86–94행은 §3이다. 88–90행이 16~26에 2~4를 더해 조건부 18~30이 되는 문장이다. [수명 계약](../contracts/STATE_LIFECYCLE.md) 581–587행이 같은 가산이다. [모델 1](AUTHORITY_MODEL_1.md) 42–44행은 수명 계약을 먼저 닫고 잔여 통합량을 재산정하며, 10~16과 16~26을 합산하지 말라는 문장이다. 16~26의 가산 자체는 같은 파일 35–40행이고, 숫자는 37–38행이다. 6~10에 권위/출처 4~6, 회수 경계 3~5, 재생·오류 시험 3~5를 더한다.
- 선행 증거. `git log --merges -- validation/2026-10-08-k1-evidence-close`는 비었다. 기본 이력 단순화 때문이다. `git log --merges --full-history -- validation/2026-10-08-k1-evidence-close`는 `a059bd69eae321ccfeb5940f3d675b962103d361`, PR #137이다. 그 병합은 이 HEAD의 조상이다.
- 병합된 문장. #138 병합 `a483ab1777ad0c3e15ff71798822cbf6b3666f83`의 [v5 설계 결정](STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) §5는 그대로다. 「사용자가 이 문서를 문장 수정 없이 병합하면, 이 문서에서 「권고」로 표시한 갈래(O1)와 §6에서 정지라고 적지 않은 구현 게이트만 채택되고, 그 채택이 `k-stage2-v5-impl`의 구현 범위가 된다.」 #140 병합이 이 HEAD다. [백엔드 채택 제안](BACKEND_ADOPTION_PROPOSAL_20261009.md) §6은 그대로다. 「사용자가 이 문서를 문장 수정 없이 병합하면, 선택지 A만 채택되고, 채택되는 backend는 5단계의 로컬·비운영 PostgreSQL 17.11(Debian 17.11-0+deb13u1)이며, 그 범위는 단일 프로세스·단일 작성자·기본 꺼짐·운영 플래그 false·R2와 복제와 합의는 열지 않음·이미 멈춘 항목은 멈춘 채로다.」
- [완료 설계](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md) §5.1은 이렇게 적는다. 「User-only 결정 문서가 병합돼 `DONE`인 것과 권고한 기능이 실제 채택된 것은 별개다.」 같은 절은 「문서 병합·명칭·recommendation만으로 ADOPT를 추론하지 않음」이라고 적는다. T1과 T2는 위 두 문장을 계획 대상으로 읽는 것이다. v5 crate가 이미 있다거나, 5단계가 시작됐다는 뜻이 아니다.
- `runtime/crates`에는 오늘 `kix-bcs1`, `kix-feature-ir`, `kix-feature-semantics`, `kix-kernel`, `kix-types`가 있다. `kix-kernel-v5`, `kix-ktx-wire`, `kix-journal-local`은 없다.
- 잠금 `lib.rs` 22행의 `SEMANTICS_VERSION`은 4다. 19–22행은 바뀐 의미론 아래에서 이전 입력을 조용히 재생하지 말라고 적는다. 공개 진입점은 `new`, `reserve`, `mark_payment_unknown`, `expire`, `cancel_scope`, `replace_owner`, `observe_capture`와 읽기 함수다. 승인, 종결, 슬롯 해제, 기록 회수, review 해제는 없다. [v5 설계 결정](STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) §3이 그 면을 적고, 이 세션이 같은 blob에서 `pub fn` 목록을 다시 보았다.
- 고치지 않은 파일: 두 잠금 blob, `reference/v0.3-rc1/**`, `.aiops/`, `.github/`, `docs/tasks/`, `docs/contracts/**`, `docs/adr/**`, 개발계획, 루트 README, `runtime/**`, CI. 옛 16~26과 18~30 문장은 그 자리에 둔다. 이 파일이 링크로 그 뒤를 잇는다.

첫 묶음은 완료가 아니다. [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) §4는 「잔여 통합 검토·증거 마감」만 닫고, 수명 계약 입력 반영과 고정 환경 성능 반복은 미완결로 둔다. 「새로 실입력까지 완결된 행: 0」은 그대로다. #136 병합은 I12 선택지 1/2/3의 수락을 적지 않는다. 이 문서가 추론하지 않는다.

## 2. 작업 묶음

옛 네 덩어리를 여섯 묶음으로 다시 자른다. 옛 숫자는 옆에 둔다. WP1과 WP2는 옛 6~10을 나눈 것이고, 6~10 위에 다시 더하는 값이 아니다. 나누는 식은 §6이다.

| WP | 하는 일 | 옛 숫자 | 출처 |
|---|---|---:|---|
| WP1 | wire/registry/golden 재구축 | 6~10의 계획 배분 3~6 | §6. 옛 합은 [모델 1](AUTHORITY_MODEL_1.md) 37행 |
| WP2 | 로컬 저널. append, recovery, 찢긴 tail, 예산 | 6~10의 계획 배분 3~4 | §6 |
| WP3 | 권위/출처 | 4~6 | [모델 1](AUTHORITY_MODEL_1.md) 38행 |
| WP4 | 회수 경계 기록 | 3~5 | 같은 행 |
| WP5 | 재생·오류 시험 | 3~5 | 같은 행 |
| WP6 | 수명 가산. 승인기록·규칙 참조·잔여위험의 wire 1~2, 그리고 승인·정정·금지된 재송신·슬롯 인계의 재생/거절 시험 1~2 | 2~4 | [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) 88–89행, [수명 계약](../contracts/STATE_LIFECYCLE.md) 583–584행 |

16~26은 WP1+WP2의 6~10에 WP3 4~6, WP4 3~5, WP5 3~5를 하한끼리·상한끼리 더한 값이다. 6+4+3+3=16, 10+6+5+5=26. 18~30은 거기에 WP6 2~4를 더한 값이다. 16+2=18, 26+4=30. [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) §2와 같은 덧셈이다.

제외는 세 대상 모두 그대로다. 실 PG/inbox, 승인 UI/서비스, 자금 재원, 완전 자동 규칙 엔진, distributed revocation·Raft/quorum. [모델 1](AUTHORITY_MODEL_1.md) 39–40행의 production grant/담보 Move, 비협조 완전 복구도 제외다. [개발계획](../DEVELOPMENT_PLAN.md) §9.1은 R2에 대해 「숫자 없음」이라고 적는다. (a)의 숫자를 R2로 옮기지 않는다. 승인된 v5 crate 구축 추정은 없다. [v5 설계 결정](STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) §1과 §4가 「숫자 없음」이라고 적는다. 그 구축 인일은 아래 합계에 넣지 않는다.

모델 3의 13~22는 [모델 1](AUTHORITY_MODEL_1.md) 39행의 당시 비교다. 이 합계에 넣지 않는다.

## 3. 겹침 (AGENTS §7)

닫힌 산출물을 대조했다. 사람 일수를 뺀 행은 없다. 첫 묶음 10~16은 (a)에 더하지 않고, (a)에서 빼지도 않는다. [개발계획](../DEVELOPMENT_PLAN.md) 518행의 10~16은 E-4 3~5 + 수명 계약 4~6 + 성능 계약·장치 3~5다. [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) §2의 「잔여 통합 검토·증거 마감」 0.5~1은 그 10~16 안이고, (a) 코드 통합이 아니다. #137이 그 한 칸을 닫는다. 18~30의 감액이 아니다.

readiness와 stage-4는 Python이다. Rust 커널 재생에 대한 코드 재사용이 아니라 시나리오 재사용이다. PR #11의 `kix-journal-local`과 readiness의 `journal.v1`은 다른 산출물이다. `readiness/store.py`의 `JOURNAL_NAME`은 `journal.v1`이다.

| 산출물 | 닿는 WP | 분류 | 잔여 |
|---|---|---|---|
| E-4 비교 모델과 `contract_invariants.rs`의 `five_contract_invariants_on_kernel_only_generated_histories`, `e4_state_model.rs`의 `locked_v4_matches_independent_state_model` | WP5. v4 메모리 이력 | 부분. v4만 | 3~5를 유지. 이 시험은 첫 묶음 E-4다. (a)의 저널/wire 재생을 대신하지 않으므로 빼지 않고, 10~16을 (a)에 더하지도 않는다 |
| `transitions.rs`의 `replaying_ordered_inputs_reconstructs_identical_state`, `response_loss_retry_returns_original_before_availability_check`. `contract_edge_cases.rs`의 `rejection_replay_stays_immutable_after_the_blocking_hold_is_released` | WP5. 잠금 커널의 기존 명령 | 부분. v4 공개 명령 | 같은 3~5. 저널 복구 시험이 아니다 |
| `observation_slots.rs`의 `previous_semantics_version_is_rejected_without_silent_replay_change`, `quarantine_capacity.rs`의 `v3_inputs_are_rejected_before_any_state_change`, `transitions.rs`의 `unknown_semantics_and_regressed_time_are_not_applied` | WP1·WP5. v4가 다른 의미론을 거절 | 부분 | wire crate를 통과로 만들지 않는다. WP1은 3~6 |
| [수명 계약](../contracts/STATE_LIFECYCLE.md) 0.6 | WP6 | 부분. 계약 문장 | 계약 작성 노력은 다시 더하지 않는다. 구현은 남는다. 시험 1~2는 §4에서 음성 시험으로 남고, wire 1~2는 세 대상에서 제외 |
| [어댑터 정체성](../contracts/ADAPTER_EVENT_IDENTITY.md) 0.1 | WP3 | 부분. 초안, 코드 없음. I06은 미완결 | 일수 공제 없음. WP3은 4~6 |
| [I12 절단 증명](CUT_PROOF_I12_20261008.md) | WP4 | 부분. 초안, 시험 없음. I12는 미완결. 선택지 수락은 추론하지 않음 | 일수 공제 없음. WP4는 3~5 |
| [readiness/test_faults.py](../../readiness/test_faults.py) `StoreTests.test_torn_tail_is_discarded_and_a_bad_checksum_fails_closed`, `test_budget_names_the_existing_limit_and_overload_does_not_queue`. [readiness/conformance.py](../../readiness/conformance.py) `BackendConformance.test_budget_rejection_preserves_records_and_replay_identity` | WP2 | 부분. Python `journal.v1` | 시나리오 재사용. T0·T1의 3~4를 줄이지 않는다. `kix-journal-local`의 통과로 세지 않는다 |
| [exploration/stage4/adapters.py](../../exploration/stage4/adapters.py), [stage-4 기록](../../validation/2026-10-08-k-stage4-local-exploration/README.md), [백엔드 채택 제안](BACKEND_ADOPTION_PROPOSAL_20261009.md) §3 | WP2의 T2 | 부분. Python 어댑터. 로컬 PostgreSQL이 명령 identity, payload sha256, 최초 결과를 한 트랜잭션에 넣었다는 탐색 자료 | 순위도 SLO도 아니다. 이 문서가 그 초당 건수와 p99를 옮기지 않는다. T2에서 Rust append 로그를 다시 만들지 않는 근거다 |
| [kix-bcs1 golden](../../runtime/crates/kix-bcs1/tests/golden_vectors.rs) 4건. `fixed_bytes_and_hash_match_external_golden_values`, `u128_zero_and_max_are_lossless`, `domain_schema_and_version_are_bound`, `legacy_json_is_not_kix_bcs1_identity` | WP1 | 부분. 현재 main의 canonical body | PR #11 wire golden 9건이 아니다. WP1을 줄이지 않는다 |
| [performance_harness.rs](../../runtime/crates/kix-kernel/tests/performance_harness.rs) 4건. `memory_probe_reports_saturation_without_recreating_kernel`, `low_load_uniform_is_distinct_from_hot_seat_retry_and_saturation`, `outcome_summaries_do_not_label_mixed_p99_as_success`, `evidence_binding_records_budgets_toolchain_and_non_claims` | WP2의 내구성 | 미커버 | 메모리 장치다. 저널 일수를 빼지 않는다. 제품 SLO가 아니다 |

[PR #11 보존](../status/PR11_PRESERVATION.md)의 cold-build는 이 세션이 다시 실행하지 않았다. 그 기록은 잠금 v4 커널 바이트 위에서 wire golden이 4 통과, 5 실패라고 적는다. 실패 다섯은 `every_action_preserves_context_and_fixed_width_payloads`, `genesis_validates_layout_limits_and_semantics_without_accepting_preoccupied_state`, `independently_calculated_genesis_command_and_result_vectors`의 `BodyEncode`, 그리고 `ordered_wire_replay_recovers_original_result_intent_owner_and_late_capture`, `wire_replay_retains_unbound_operation_quarantine_and_recorded_rejection`의 `UnsupportedSemantics`다. v1 시대의 wire 비용은 v4로 넘어오지 않는다. WP1을 완료분으로 빼지 않는 근거다. 저널은 같은 기록에서 library/recovery 1+13 통과, helper ignore 2다. 그 통과는 v1 파일을 v4로 이관했다는 뜻이 아니고, v4 슬롯 예약·만석 상태변경형 `Err(Capacity)`의 모든 복구 경로를 검증한 것도 아니다. WP2를 완료분으로 빼지 않는 근거다.

## 4. 대상 비교

인일은 계획용이다. 하한끼리, 상한끼리 더한다. T0와 T1의 계획 인일이 같은 것은 v5가 v4와 같은 일이라는 뜻이 아니다. v5 crate 구축과, T0 산출물을 v5로 옮기는 이관은 합계 밖이고 **숫자 없음**이다.

| WP | 옛 숫자 | T0 잠금 v4 | T1 계획된 v5 crate | T2 T1 + 5단계 로컬 PostgreSQL |
|---|---:|---:|---:|---:|
| WP1 wire/registry/golden | 6~10의 일부 | 3~6 | 3~6 | 3~6 |
| WP2 로컬 저널 | 6~10의 나머지 | 3~4 | 3~4 | 0 |
| WP3 권위/출처 | 4~6 | 4~6 | 4~6 | 4~6 |
| WP4 회수 경계 | 3~5 | 3~5 | 3~5 | 3~5 |
| WP5 재생·오류 시험 | 3~5 | 3~5 | 3~5 | 3~5 |
| WP6 시험 (음성) | 2~4 안의 1~2 | 1~2 | 1~2 | 1~2 |
| WP6 wire | 2~4 안의 1~2 | 제외 | 제외 | 제외 |
| **합계** | **18~30** | **17~28** | **17~28** | **14~24** |
| 18~30과의 차 | 0 | −1 ~ −2 | −1 ~ −2 | −4 ~ −6 |

T0·T1 합계: 3+3+4+3+3+1=17, 6+4+6+5+5+2=28. T2 합계: 3+0+4+3+3+1=14, 6+0+6+5+5+2=24. 차이는 제외한 WP6 wire의 1~2이고, T2는 거기에 WP2의 3~4를 더 뺀다. 17−18=−1, 28−30=−2, 14−18=−4, 24−30=−6.

### T0

WP6의 wire 1~2가 붙을 전이가 없다. 수명 계약 545–546행은 잠금 커널에 종결 승인·해제 전이가 없다고 적는다. `expire`는 TTL이 지난 `Held` 재고만 되돌린다. 그래서 T0의 WP6은 그 전이가 없다는 음성 시험 1~2만 남는다. 양성 수명 전이를 v4에 만드는 일은 잠금 파일을 바꾸는 일이고, 이 추정의 합계 밖이다.

T0 다음에 v5로 가는 재작업은 이 17~28에 없다. 의미론 4 문맥을 v5가 성공으로 받아들이는 일은 [v5 설계 결정](STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) §3이 금지하는 조용한 재생이다. v4 저널이나 wire를 옮기려면 명시적이고 시험된 이관이 필요하다. 그 이관 비용은 **숫자 없음**이다. 추측으로 넣지 않는다.

T0를 바꾸는 것:

- 잠금 해제라는 별도 사람 결정이 전이를 v4에 만들면, 제외한 wire 1~2가 돌아온다. [프로그램 결정](PROGRAM_DECISIONS_20260928.md) §5의 커널 잠금 조건이다. 이 문서가 그 결정을 열지 않는다.
- 6~10을 바이트 비가 아닌 다른 근거로 나누면 WP1과 WP2만 움직인다. 둘의 합 6~10은 그 나눔이 지키도록 남아 있다.
- 인건비·달력·인원은 이 인일에 없다. 인일은 [개발계획](../DEVELOPMENT_PLAN.md) §15의 1인 전담이다.

### T1

WP1은 그대로 3~6이다. v1 wire는 의미론 1이고, 의미론 5 crate는 없다. 새 v5 전이의 wire·OpenAPI·카탈로그는 새 프로토콜 명령이라 `DECISION_REQUIRED · Astra`다. 그 명령의 인일은 만들지 않았고, 3~6 안에도 없다. 3~6은 옛 wire crate의 배분이다.

WP2는 그대로 3~4다. [v5 설계 결정](STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) O1은 v5 crate를 메모리 안으로 두고, 그 crate 안에 저널을 만들지 말라고 적는다. 저널은 (a)의 별도 산출물로 계획 인일만 적혀 있다. 착수를 승인하지 않는다.

WP3과 WP4의 계획 인일 4~6, 3~5는 막힌 부분을 포함한다. 만들 수 있는 것은 종결 기록의 모양, 읽기 전용 회수 자격 보고, 충돌 색인이다. 슬롯 해제는 I12·I13, 상태를 바꾸는 회수는 I09·I10·I13, review 해제는 I11 때문에 정지다. 정지 주인은 §5다. 막힌 부분이 4~6과 3~5의 얼마인지는 측정하지 않았다. 그 분할은 **숫자 없음**이다. 나중에 막힌 부분을 범위에서 빼면 합계가 줄어드는데, 줄어드는 폭도 **숫자 없음**이다.

종결 기록의 모양, 읽기 전용 회수 자격 보고, 충돌 색인의 구축 인일은 `k-stage2-v5-impl` 쪽이고, v5 설계가 이미 **숫자 없음**이라고 적은 공수다. (a) 합계에 더하지 않는다. 더하면 번호 없는 구축 비용을 이 표에 새로 만드는 일이 된다.

T1을 바꾸는 것:

- v5 crate 구축은 합계 밖이다. **숫자 없음**.
- T0 산출물을 나중에 v5로 옮기는 이관은 합계 밖이다. **숫자 없음**.
- 막힌 WP3·WP4 부분을 빼는 폭은 **숫자 없음**.
- 새 전이의 wire는 Astra 결정 전까지 제외다. 숫자를 만들지 않는다.

### T2

WP2는 0이다. 0은 구현이 끝났다는 뜻이 아니다. Rust append 로그를 다시 만들지 않는다는 뜻이다. [개발계획](../DEVELOPMENT_PLAN.md) §10 474행은 기성 DB가 제공하는 로그를 불필요하게 다시 만들지 말라고 적고, 그 일이 전부 미착수라고 적는다. [백엔드 채택 제안](BACKEND_ADOPTION_PROPOSAL_20261009.md) §3은 로컬 PostgreSQL이 명령 identity, payload sha256, 최초 결과를 한 트랜잭션에 넣었다고 적는다. §6의 인용 문장이 그 backend를 5단계의 로컬·비운영 범위로 적는다. §5.1이 말하듯, 그 문장 병합이 운영 backend의 ADOPT도, 5단계의 시작도 아니다.

가져온 `kix-journal-local`은 `kix_ktx_wire`의 `encode_registered`를 쓴다. 저널을 만들지 않는다는 이유가 wire crate까지 0으로 만들지는 않는다. stage-4가 저장한 것은 그 세 필드이지, PR #11 wire 바이트의 대체 완료가 아니다. WP1은 3~6으로 남는다. wire가 저널 프레임 전용이라는 나중의 범위 축소가 있다면 그 감액은 **숫자 없음**이다.

찢긴 tail과 예산의 Python 시험은 §3의 시나리오 재사용이다. Rust 저널을 0으로 둔 이유에 그 시험을 완료분으로 넣지 않는다. 5단계가 그 어댑터를 업무 범위로 다시 쓰는 인일은 `k-stage5-durable-tx` 쪽이고 이 합계에 없다. **숫자 없음**.

T2를 바꾸는 것:

- 사용자가 프레임 fsync 저널을 PostgreSQL 옆에도 두기로 하면 WP2의 3~4가 돌아온다. 그 허용 여부는 `k-a-integration-decision`이다. 가져온 저널은 길이 접두 프레임과 fsync이고, 체크섬은 `canonical_hash_bytes`의 SHA-256이다. CRC 상수는 그 소스에 없다. AGENTS.md §5의 로그 엔진 잠금에 가까운 산출물이다. 이 문서는 두 길의 계획 인일만 적고 어느 쪽도 승인하지 않는다.
- §6의 PostgreSQL 문장이 바뀌면 WP2는 3~4로 돌아온다.
- 5단계 바인딩 공수는 합계 밖이다. **숫자 없음**.

## 5. 열린 입력과 주인

값을 채우지 않는다. I01–I13의 상태 문장은 [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) §1·§4가 정본이다. 이 표는 이 추정이 멈추는 항목만 옮긴다.

| 항목 | 상태 | 주인 | 이 추정이 하는 일 |
|---|---|---|---|
| 새 wire·프로토콜 명령, v5 전이의 OpenAPI·카탈로그 | DECISION_REQUIRED · Astra | Astra | WP6 wire 1~2를 세 대상에서 제외. 숫자를 만들지 않음 |
| H_g 최종성 (A4), 시간원 수치 (A5), 비협조 실행자와 온체인 앵커 (A10) | DECISION_REQUIRED · Astra | Astra | 값을 만들지 않음. WP4의 그 부분은 계획 인일 안에 있고 착수하지 않음 |
| I09 보관·지원 기간, SLO·TPS·p99 | DECISION_REQUIRED · Astra | Astra | 숫자를 만들지 않음. 성능 하네스와 stage-4 탐색 자료를 SLO로 읽지 않음 |
| I11 자동 한도와 잔여위험 정책 | DECISION_REQUIRED · Astra | Astra | review 해제는 정지. 한도를 숫자로 채우지 않음 |
| (a)의 저널을 허용할지 | 사용자 결정. 다음 노드 `k-a-integration-decision` | 사용자 | T0·T1은 3~4를 계획 인일로만 적음. T2는 다시 만들지 않아 0. 어느 쪽도 승인하지 않음 |
| 절단 증명의 비작성자 독립 검토 (A9)와 신뢰정책 승인 | 사용자 | 사용자 | I12는 미완결. 선택지 1/2/3을 추론하지 않음 |
| 인건비, 감가상각, 전력, 연간 운영, 투자 한도 | UNDETERMINED — 사용자/운영 책임자 | 사용자/운영 책임자 | 단가 없음. 인일 범위에 넣지 않음 |
| I02, I03, I04, I05, I08, TM04, TM05 | UNDETERMINED · 토스 계약/기술 | 토스 계약/기술 | 행을 닫지 않음. 제공자 사실을 만들지 않음 |
| I10 | UNDETERMINED · 법무/개인정보 | 법무/개인정보 | 상태를 바꾸는 회수는 정지. 법정 기간을 산정하지 않음 |
| I13 | UNDETERMINED · 사용자/운영 책임자 | 사용자/운영 책임자. [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) §1은 운영/보안 주체·예산이라고 적음 | 슬롯 해제와 상태를 바꾸는 회수는 정지. 저장 backend 착수 승인이 아님 |

## 6. 근거와 방법

각 숫자의 출처다. 근거가 없는 칸은 **숫자 없음**이다.

1. 18~30과 그 가산은 측정값이 아니다. §1의 줄이 출처다. 실제 소진 인일은 숫자 없음.
2. WP1 3~6과 WP2 3~4는 옛 6~10을, main에 없는 두 crate의 Rust 바이트 비로 나눈 계획 배분이다. 나눈 값을 6~10 위에 더하지 않는다. README와 `Cargo.toml`은 비에서 뺐다. 구현과 시험 본문만 넣었다.
3. WP3 4~6, WP4 3~5, WP5 3~5는 [모델 1](AUTHORITY_MODEL_1.md) 38행 그대로다. §3에서 일수로 뺄 산출물이 없었다.
4. WP6의 1~2 / 1~2 분할은 [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) 88–89행과 [수명 계약](../contracts/STATE_LIFECYCLE.md) 583–584행에 이미 있다. 세 대상은 wire 쪽 1~2를 뺀다. T0에서는 붙일 전이가 없고, T1·T2에서는 그 wire가 새 프로토콜 명령이기 때문이다. 시험 쪽 1~2는 음성 시험으로 남긴다. 1~2를 더 잘게 줄이는 측정은 없어서, 음성 시험의 폭을 1~2보다 작게 적지 않는다.
5. T2의 WP2 0은 §4의 문장 근거다. 완료분이 아니다.
6. 합계는 하한끼리, 상한끼리. §4에 식을 적었다.
7. v5 crate 구축, R2, T0→v5 이관, WP3·WP4의 정지 분할, 5단계 바인딩, 실제 소진 인일, 인건비는 숫자 없음.

측정은 이 세션이 `bb193efb5d238581096372c8a20bee1271dfe4df`에서 했다.

main의 잠금 커널 `lib.rs`는 663줄, 24,159바이트다. 시험 파일 줄 수: `contract_edge_cases.rs` 440, `contract_invariants.rs` 589, `e4_state_model.rs` 2,202, `observation_slots.rs` 373, `performance_harness.rs` 292, `quarantine_capacity.rs` 335줄·11,293바이트, `transitions.rs` 685. support는 `coverage_v4.rs` 1,168, `evidence_gates.rs` 370, `model_v4.rs` 703, `perf_probe.rs` 623이다. 이 줄 수는 일수로 바꾸지 않았다. 잠금 커널이 수명 전이를 담지 않는다는 §4의 크기 맥락이다.

PR #11 커밋 `55a3df4968f5684bb4cb9e3c9781ab5f00165235`는 `git fetch --no-tags origin 55a3df4968f5684bb4cb9e3c9781ab5f00165235`로 가져왔다. ref와 tag는 만들지 않았다. `git ls-tree -r --long FETCH_HEAD`의 바이트와, `git show FETCH_HEAD:<path> | wc -l`의 줄이다.

| 파일 | 바이트 | 줄 |
|---|---:|---:|
| `runtime/crates/kix-ktx-wire/src/lib.rs` | 21,355 | 583 |
| `runtime/crates/kix-ktx-wire/src/registry.rs` | 5,428 | 146 |
| `runtime/crates/kix-ktx-wire/tests/golden_vectors.rs` | 17,810 | 491 |
| `runtime/crates/kix-journal-local/src/lib.rs` | 13,470 | 391 |
| `runtime/crates/kix-journal-local/tests/recovery.rs` | 20,133 | 589 |

wire 합 44,593바이트, 1,220줄. 저널 합 33,603바이트, 980줄. 바이트 합 78,196. 줄 합 2,200.

6~10의 바이트 배분: 하한 6 × 44,593 / 78,196 = 3.42, 6 × 33,603 / 78,196 = 2.58. 상한 10 × 같은 비 = 5.70과 4.30. 반올림은 0.5 이상을 올리는 정수다. 3~6과 3~4가 되고, 3+3=6, 6+4=10이라 옛 6~10의 양 끝이 유지된다. 줄 비는 1,220/2,200과 980/2,200이다. 같은 규칙의 정수도 3~6과 3~4다. 표에 쓴 정수는 바이트 비의 반올림이고, 줄 비는 그 정수가 같은지 본 대조다.

같은 트리에서 `#[test]`는 wire golden 9, 저널 라이브러리 1, recovery 15다. recovery의 `#[ignore]` helper는 2개다(331행, 394행). 15−2+1=14는 보존 문서의 「1+13」과 개수가 같다. 통과와 5건 실패는 보존 문서의 실행 결과이고, 이 세션의 재실행이 아니다. 저널 `lib.rs` 20–22행은 `FRAME_DOMAIN` `KTX-LOCAL-FRAME-v1`과 `FRAME_OVERHEAD` 4+8+32+32다. 101행 `frame`이 길이와 순번과 이전 해시를 두고, 다이제스트는 `canonical_hash_bytes`다. PR #11의 `kix-bcs1` 155–156행은 `Sha256::digest`를 호출한다. 263행 주석은 append와 fsync가 apply 앞이라고 적는다. CRC 상수는 없다.

## 7. 분류 (AGENTS §8)

### A. 계약과 일치

- (a)는 승인 전 미착수다. [PR #11 보존](../status/PR11_PRESERVATION.md)과 [프로그램 결정](PROGRAM_DECISIONS_20260928.md) §5.
- 잔여 통합량은 첫 묶음의 겹침을 뺀 뒤 다시 산정한다. [모델 1](AUTHORITY_MODEL_1.md) 44행, [수명 계약](../contracts/STATE_LIFECYCLE.md) 586행, [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) 93행. 이 파일이 그 재산정이다.
- 잠금 커널에 종결 승인·슬롯 해제·기록 회수·review 해제가 없다.
- `SEMANTICS_VERSION`은 4이고, 이전 입력의 조용한 재생은 금지다.
- 제외 범위와 I01–I13의 상태, 「새로 실입력까지 완결된 행: 0」은 이 파일이 바꾸지 않는다.

### B. 계약이 정의하지 않음. 성격만 기록

- 6~10을 wire와 저널로 나눈 옛 숫자는 없다. 이 파일의 3~6과 3~4는 측정한 바이트 비의 계획 배분이다. 새 견적이 아니다.
- v4에서 수명 전이의 양성 시험이 붙을 공개 함수는 없다. WP6을 음성 시험으로 읽는 것은 그 부재의 성격 기록이다. 계약에 음성 시험 의무를 새로 쓰지 않았다.
- 프레임 fsync 저널이 로그 엔진 잠금 안인지, (a)로 허용되는지는 정해져 있지 않다. 결정 위치는 `k-a-integration-decision`이다.
- v5 crate 구축 공수, T0 산출물의 v5 이관 절차, WP3·WP4 정지 부분의 폭은 정의돼 있지 않다. 숫자 없음.

이 항목들에 의미를 지어 계약 본문을 고치지 않았다.

### C. 명시적 계약 위반

없음. 잠금 파일을 고치지 않았다. 계약 문장을 고치지 않았다. (a)가 아직 없는 것은 계약과 승인 기록이 이미 적은 상태다.

## 8. 비주장

운영 준비, 내구성, 분산 fencing, 은행 exactly-once, 체인 최종성, 법적 적합성을 주장하지 않는다. 승인된 TPS, p99, 실패율, SLO는 없다. stage-4의 탐색 숫자를 순위나 SLO로 읽지 않는다. 이 파일은 그 숫자를 옮기지 않는다.

첫 묶음 완료를 주장하지 않는다. I01–I13의 어느 행도 이 파일로 닫히지 않는다. 새로 실입력까지 완결된 행은 0이다. I12 선택지를 추론하지 않는다.

17~28과 14~24는 계획용 범위다. 청구, 납기, 착수 승인이 아니다. v5 crate가 존재한다거나 5단계가 시작됐다는 주장이 아니다. R2 추정은 없다. 승인된 v5 구축 추정은 없다.

PR #11 저널 시험이 v4 바이트 위에서 통과했다는 보존 기록을, 이관 완료나 만석 복구의 완료로 읽지 않는다. wire 5건 실패는 보존 문서의 cold-build 기록이다. 이 세션이 그 조합을 다시 컴파일하지 않았다.

이 세션의 로컬 명령은 exact-head CI가 아니다. 문서만 바꾼 뒤의 호스트 실행이 무거운 단계를 생략하면, 그 초록은 전체 검증 통과가 아니다. 이전 SHA의 CI를 이 파일의 최종 헤드로 옮기지 않는다. 최종 헤드의 KTX·KIX protocol run ID는 그 헤드가 생긴 뒤의 PR 보고에 둔다. 그 ID를 적으려고 커밋을 더하지 않는다.

실자금, 실 PG·은행·KYC, 공개 엔드포인트, Sui testnet·mainnet, R2, 복제, 합의, 저장 엔진, 새 coin/TIX 모듈은 없다.

## 9. 남은 불확실성

- 3~6과 3~4는 바이트 비의 반올림이다. 다른 나눔은 WP1과 WP2만 바꾸고, 조건은 둘의 합이 6~10인 것이다.
- WP3·WP4 안에서 정지된 부분의 폭은 숫자 없음. 그 부분이 닫히기 전에는 착수하지 않는다.
- T0 산출물을 v5로 옮기는 비용은 숫자 없음. 17~28을 두 번 하거나 한 번으로 읽는 환산은 하지 않는다.
- T2의 0을 받아들이는지는 `k-a-integration-decision`이다. 로그 엔진 잠금과의 경계는 그 결정이 적는다.
- 토스 사실, I10, I09·I11·잔여위험, A4·A5·A10, A9와 신뢰정책, I13, 비용 단가는 §5의 주인에게 남아 있다.
- 이 트리의 exact-head CI는 아직 없다. 호스트 전체 검증은 헤드가 공개된 뒤에 있다. 문서 전용 생략은 전체 검증으로 보고하지 않는다.
