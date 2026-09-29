# 잠금 blob의 실제 CI 강제 경로 — 확인 기록

확인일 2026-09-16. 확인 소스는 main
`d5b9f2d67b5532fa35464c8557e88f70be300888`입니다.
**판정: 두 파일은 기존 CI가 실행하는 테스트에서 이미 실제 blob 대조를 받습니다. 문서상 약속만인 상태가 아닙니다.**
이번 작업은 문서 확인이며 코드·workflow·설정·시험 입력을 바꾸지 않았습니다.

## 1. 정확한 검사 경로

| 단계 | 파일과 전체 Git blob | 실제 동작 |
|---|---|---|
| KTX workflow | `.github/workflows/ktx-kernel.yml` / `696420af819ebc004067fd52971d016e51e6cdcb` | PR·수동 실행에서 `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked`; pipefail로 실패 전파 |
| 전체 workflow | `.github/workflows/protocol.yml` / `62fd4302af952a66c1a6e3fb3b3ea5a1eeebee64` | main push·PR·수동 실행에서 `cargo test --manifest-path runtime/Cargo.toml --workspace --locked`; 필터로 E-4를 제외하지 않음 |
| 두 blob assert | `runtime/crates/kix-kernel/tests/e4_state_model.rs` / `f021965129e767234225364e229fb4be99395e6a` | 일반 `#[test] locked_sources_and_new_harness_sources_are_identified`; 두 파일 각각 `git hash-object`, 성공 exit와 고정 문자열 일치를 assert |

테스트의 고정값:
- `src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

해당 테스트에는 ignore나 건너뛰기 분기가 없습니다. 상수는 파일 앞부분, 대조는
위 함수의 첫 loop에 있습니다. 파일을 읽지 못하거나 Git 호출이 실패해도 테스트는 실패합니다.
`git hash-object`의 stdout 문자열과 상수의 equality가 판정입니다.

workflow의 `sha256sum` 출력은 **증거 기록**일 뿐 고정값 assert가 아닙니다.
`cargo --locked`도 의존성 lockfile 조건이지 이 두 소스 blob의 잠금 명령이 아닙니다.
실제 소스 잠금은 위 Rust integration test의 assert가 담당합니다.
기준선 검증 artifact의 `workspace-tests.log`에도 해당 테스트 `... ok`가 남아 있습니다
(exact-main operation run `35079754929`, target main d5b9f2d).

## 2. 강제 수준의 한계

- 테스트 경로가 유지된 상태에서 잠금 소스 바이트를 바꾸면 고정 blob assert가 실패합니다. 주석·포맷도 같습니다.
- 같은 변경에서 기대 상수·테스트·workflow를 함께 바꾸거나 실행을 생략할 수 없는 보안 장치까지 뜻하지는 않습니다.
- 확인 시 main은 protected=false이며 필수 상태 검사가 적용되지 않았습니다. CI 실패가 검출되는 것과 서버가 병합을 반드시 거절하는 것은 다릅니다.
- 이번에 잠금 소스를 실제로 변이시켜 실패시키지는 않았습니다. 코드와 기존 실제 실행 로그의 경로를 확인한 것이며 새로운 우회 불가 증명은 아닙니다.

## 3. 추가 강제 방법 — 제안만, 구현하지 않음

이미 있는 대조를 없애거나 중복 구현을 필수라고 주장하지 않습니다. 강화가 승인될 때에는
컴파일 전에 두 경로·승인된 고정 blob을 대조하는 별도 빠른 gate를 두고, 그 gate와
기존 검증의 성공을 서버의 필수 상태 검사로 연결하는 방법을 검토할 수 있습니다.
기대값·gate를 같은 PR에서 무심사로 바꾸면 다시 우회되므로 승인된 base의 목록 또는
독립 검토·보호된 규칙을 신뢰 기준으로 삼아야 합니다. 권한·요금제와 관리 주체가 필요합니다.

이 제안은 **코드 위생 (나)의 목록**에만 추가합니다. workflow, Cargo, 테스트 상수,
브랜치/태그 보호 설정을 이번에 바꾸지 않았습니다. 잠금 파일은 어떤 위생 사유로도 수정하지 않습니다.

## 4. 2026-09-29 추가 — CI 실행 조건 변경 뒤의 강제 경로

위 1~3절은 2026-09-16 기록이므로 그대로 둡니다. 그 뒤 두 가지가 바뀌었습니다.
하나는 문서 전용 변경이면 무거운 검증을 건너뛰는 분류(#75)입니다. 다른 하나는
draft PR에서 CI를 건너뛰는 조건(#76)입니다. 이 절은 그 뒤의 값을 적습니다.
확인 소스는 #76 head `76b5e342c298ebaac42d6ebc7d5ecd6bd27811e6`입니다
(base main `b8b7455cf346d98689238d3eeaf07fc139fa6a7d`).

| 단계 | 파일과 전체 Git blob | 바뀐 점 |
|---|---|---|
| KTX workflow | `.github/workflows/ktx-kernel.yml` / `4a73103904a8b8428cc1424a6e9f52b13ef3ed09` | 검증 명령은 그대로. 변경 경로 분류 단계와 draft 건너뛰기 조건이 추가됨 |
| 전체 workflow | `.github/workflows/protocol.yml` / `9e5d96e995fe2cff29b2b52863f6d6dc5c4d9289` | 검증 명령은 그대로. 같은 분류 단계와 draft 건너뛰기 조건이 추가됨. main push는 계속 실행 |
| 두 blob assert | `runtime/crates/kix-kernel/tests/e4_state_model.rs` / `7ae4535c472cbe5416cf68a298fd4cd1dcf2a38a` | 테스트 파일 blob은 바뀜. `locked_sources_and_new_harness_sources_are_identified`의 고정값과 대조 방식은 1절 설명과 같음. ignore 표시 없음 |

잠금 소스의 blob은 그대로입니다. `lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
`quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`입니다.

바뀐 조건에서 assert가 언제 실행되는지는 다음과 같습니다.

- **잠금 파일이나 테스트를 바꾼 PR.** `runtime/` 경로는 문서가 아니므로 분류가 전체 검증을 고릅니다.
  분류 단계가 실패해도 전체 검증으로 갑니다.
- **draft 동안.** 두 workflow 모두 건너뜁니다. 이때 초록 표시는 통과가 아닙니다.
  draft는 병합할 수 없습니다.
- **Ready for review로 바꿀 때와 그 뒤 push마다.** 두 workflow가 다시 실행됩니다. 문서 전용 변경이 아니면 위 테스트가 포함됩니다.
- **main push.** `protocol.yml`이 실행됩니다. 문서 전용 push가 아니면 workspace 테스트에 위 테스트가 포함됩니다.

2절의 한계는 그대로입니다. 이번 확인 시에도 main은 protected=false였습니다.
필수 상태 검사가 없으므로, Ready 직후 실행이 끝나기 전에 병합하는 것을 서버가 막지 않습니다.
AGENTS.md §10의 규칙(Ready 때 실행이 병합 근거)이 이 부분을 대신합니다.
이번에도 잠금 소스를 실제로 바꿔 실패를 재현하지는 않았습니다.

## 5. 2026-09-29 추가 — main push의 같은 트리 생략

main push는 이제 다음 조건을 모두 만족하면 무거운 검증을 건너뜁니다.

- 병합된 PR head(병합 커밋의 두 번째 부모)에 대한 PR 실행이 있어야 합니다.
- 그 실행이 같은 Git tree에서 전체 검증에 성공했어야 합니다.

이때 위 assert는 main push에서 다시 돌지 않습니다. 대신 job summary가 가리키는 PR 실행에서 같은 내용으로 이미 실행된 것입니다.
PR 실행 뒤 main이 움직였다면 tree가 달라져 전체 검증이 돕니다. 조회가 실패해도 전체 검증이 돕니다.
매주 예약 실행은 main에서 항상 전체 검증을 합니다. 이 절은 workflow 규칙을 옮긴 것이며, 잠금 소스를 바꿔 실패를 재현하지는 않았습니다.
