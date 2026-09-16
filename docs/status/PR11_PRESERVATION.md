# PR #11 — 태그로 보존된 v1 로컬 저널 실험

2026-09-16. 사용자 승인: PR #12/#13 main 병합, #11은 병합하지 않고 태그 검증 후 닫음.
**코드는 사라진 것이 아니다.** 아래 annotated tag와 원래 브랜치에 그대로 보존돼 있다.
이 문서는 보존 위치 기록이며 R2 또는 (a) 통합의 착수/완료를 승인하지 않는다.

## 보존 위치

- 검증된 보존 태그: [`kix-exp-r2a-local-journal-v1-20260916-r2`](https://github.com/BeautifulMind-JT/kix-protocol/tree/kix-exp-r2a-local-journal-v1-20260916-r2).
- tag object: `1311668253bbbbffdc90f1a9f446c42d43e5fa1f` (annotated, unsigned).
- target commit: `55a3df4968f5684bb4cb9e3c9781ab5f00165235`.
- target tree: `38901ede6a20dc67025014116ea92c0ea35f8bf5`.
- 원 브랜치: `codex/ktx-r2a-registered-local-replay-20260915` — 삭제하지 않음.
- [PR #11](https://github.com/BeautifulMind-JT/kix-protocol/pull/11)은 태그 ref/target/주석을 확인한 뒤 closed, merged=false로 처리했다.
- 원본 CI: [34938172828](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/34938172828) (KTX), [34938172791](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/34938172791) (전체 protocol), 모두 원본 v1 기준 success.

Crates: `kix-types`, `kix-feature-semantics`, `kix-feature-ir`, `kix-bcs1`,
`kix-kernel`, `kix-ktx-wire`, `kix-journal-local` (7개).
실험의 커널 의미론은 **1**, 현재 main의 잠금 커널 의미론은 **4**다.

## 실제 호환성 시험 — 수정/통합이 아닌 격리된 진단

[Cold-build run 35079017799](https://github.com/BeautifulMind-JT/kix-protocol/actions/runs/35079017799).
진단 workflow commit `78f7f80e22f35b8a8cfae56cbded38f3caf22331`은 별도 미병합
`codex/r1-baseline-preservation-20260916`에 있다. main의 workflow는 바꾸지 않았다.

Runner의 disposable worktree 두 개를 모두 원본 #11 commit에서 만들었다.
두 번째에서 **기존 잠금 v4 커널 파일의 바이트를 그대로 사용**했고,
wire/registry/golden/journal/테스트의 소스는 수정하지 않았다.
두 구성 각각 처음에 존재하지 않는 별도의 `CARGO_TARGET_DIR`와
`CARGO_INCREMENTAL=0`을 사용했고 각 kernel의 재컴파일 로그를 확인했다.

| 대상 | v1 원본 | 잠금 v4 커널과의 조합 |
|---|---|---|
| wire `golden_vectors` | 9 통과, 0 실패, exit 0 | **4 통과, 5 실패, exit 101** |
| journal library/recovery | 1+13 통과, 상위 helper ignore 2 | 1+13 통과, 상위 helper ignore 2 |

실패한 wire 시험과 실제 오류:

| 시험 | 오류 |
|---|---|
| `every_action_preserves_context_and_fixed_width_payloads` | `BodyEncode` |
| `genesis_validates_layout_limits_and_semantics_without_accepting_preoccupied_state` | `BodyEncode` |
| `independently_calculated_genesis_command_and_result_vectors` | `BodyEncode` |
| `ordered_wire_replay_recovers_original_result_intent_owner_and_late_capture` | `UnsupportedSemantics` |
| `wire_replay_retains_unbound_operation_quarantine_and_recorded_rejection` | `UnsupportedSemantics` |

고정 golden의 genesis/command에는 의미론 1이 들어 있다. 현재 버전과 대조하는
encode/kernel 생성 경계에서 거절된 것이며, SHA-256 함수 자체가 틀렸다는 판정이 아니다.
반면 journal recovery fixture는 `SEMANTICS_VERSION`으로 새 입력을 생성한다.
따라서 v4에서 journal 시험이 통과해도 **과거 v1 파일을 v4로 이관했다는 뜻이 아니며**,
v4 슬롯 예약·만석 상태변경형 `Err(Capacity)`의 모든 복구 경로를 검증한 것도 아니다.

- wire golden source blob: `fc3ed1b33bf294cb48f3fbcb9cce5df058e51733`.
- journal recovery source blob: `dedfdf11878696bea956df61ad53498c247cd8da`.
- journal source blob: `40d904318b58d1ccfd2e86e77e6b290856ec95a7`.
- overlay에 사용한 기존 커널 blob: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- raw artifact: `10439546137`, `pr11-v4-cold-compatibility-35079017799`.
- ZIP SHA-256: `ea1d734e9a06f430875fb86ddc42be39d5bea723605338dc70de3f5b0bca4a35`.

## 처음 발행한 태그의 증거 정정 — 덮어쓰기하지 않음

`kix-exp-r2a-local-journal-v1-20260916` (tag object
`7e6d215031d7ff454b132b8c1ca657455cbc2734`)도 같은 v1 commit을 가리킨다.
그러나 이 첫 태그는 shared build target을 사용한 run `35078643445`의
all-pass overlay 결과를 주석에 넣었다. v4 재컴파일 없이 같은 binary가 사용될
가능성을 배제하지 못해 **그 실행 및 주석의 호환성 결과는 인수 근거에서 제외**했다.
태그를 강제로 이동/삭제하지 않고, cold-build 결과를 담은 `-r2` 태그로 대체했다.
소스 보존 위치가 잘못됐다는 뜻은 아니나, 초기 태그의 통과 주장을 재사용하면 안 된다.

## main 기준선과 통합 보류

PR #12 merge: `31e60b2269e90cba6da9a1a41dacf039f5662c30`.
PR #13 merge: `bf6c2be37e8c55778f4fe378634f7895fd69a327`.
두 번째 merge 직후 tree는 #13 head `0cb65749492bf78e6cea00d3c9c7eee4f891827d`와
같은 `59746105a8e1b82b0109bb958e6f9104abb70f39`였다.
이 보존 문서의 추가 commit은 내용 없는 merge가 아니므로 최종 tree에는 이 문서가
추가된다. 코드 동일성과 전체 tree 동일성을 혼동하지 않는다.

R1 잠금은 그대로다.
- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

(a)는 승인 전 미착수다. 종전 모델1의 제한된 통합 추정 **16~26인일**은 상태 수명
계약과 A-4의 회수·보존 중복이 닫힌 뒤 재산정한다. local fsync는 quorum ACK나
체인 확정의 대체물이 아니다. 소스·golden 수정을 통한 실패 수리는 이번에 하지 않았다.

이후 기준 태그는 **R1 v4 + 검증 장치** 기준선으로, 실제 main commit/tree와
그 SHA의 최종 CI를 주석에 기록한 뒤 발행한다. 통합 완료·R2 완료 태그가 아니다.
브랜치·태그 보호 설정은 조회만 하며, annotated tag 발행을 보호 규칙 적용이나
암호학적 서명 완료로 설명하지 않는다.
