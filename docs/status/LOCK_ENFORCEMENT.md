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
