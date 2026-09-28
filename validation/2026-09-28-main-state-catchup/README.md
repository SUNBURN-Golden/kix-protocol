# main 상태 정합 — 2026-09-28 로컬 검증

hosted GitHub Actions 사용량이 소진된 기간의 로컬 대체 확인이다. **hosted CI 결과가 아니다.** 이 기록의 수치는 아래 실행 한 번의 값이다.

- 작업 근거: 사용자 2026-09-28 대화 지시. `docs/tasks/` 과제 문서 없음
- 작업 시작 시 `origin/main`과 작업 브랜치 HEAD: `34a722d26fa894366c26bac9de4187c598fbf3eb`
- 작업 브랜치: `claude/awesome-lovelace-bf9ual`(세션 지정 브랜치)
- 구현 commit SHA는 이 파일을 담은 commit이며, 자기 SHA를 파일에 쓰지 않는다. PR에서 확인한다.

## 변경

- `.github/workflows/protocol.yml`: "Offline reference state machines and OpenAPI pins" 단계를 추가했다. 이 단계는 `reference/` 세 상태기계의 단위 시험과 두 OpenAPI 핀 검사를 실행한다. 기존 단계는 바꾸지 않았다.
- `docs/status/MAIN_STATE_20260928.md`를 새로 썼다. 병합 범위, CI 공백, 열린 결정 D-1~D-3을 담는다.
- `README.md`, `docs/README.md`, `docs/DEVELOPMENT_PLAN.md`(§17), `docs/status/BASELINES.md`, `docs/status/ORIGINAL_32_STATUS.md`에는 안내와 추가 절만 넣었다. 승인·금지 범위, 32항목 라벨, 기존 집계는 바꾸지 않았다.

## 기존 범위 대조 (AGENTS.md §7)

| 요구 | 판단 | 근거 |
|---|---|---|
| 세 상태기계 단위 시험의 CI 실행 | 미연결 → 이번에 연결 | 이전 `protocol.yml`은 `integration_gate.test_http_gate`와 `readiness.test_faults`만 실행 |
| 상태기계 재시작 경로 | 부분 커버(간접) | `readiness/test_faults.py`가 FSM을 import해 찢긴 쓰기·재시작 경로를 시험 |
| OpenAPI 핀 검사 | 미연결 → 이번에 연결 | #63 본문: "The new pin check is local. GitHub workflows were not edited." |
| Wave 2 Move 시험 | 충분히 커버 | `scripts/verify_runtime.py`의 `move-tests` 단계 |

새 시험은 만들지 않았다. 기존 시험을 CI에 연결했을 뿐이다.

## 실행 명령과 결과

환경: Linux, `/usr/bin/python3.12`(Python 3.12.3, CI의 `setup-python` 3.12와 같은 minor), Rust 1.98.1(`rust-toolchain.toml`).

`protocol.yml`의 두 Python 단계 본문을 YAML에서 추출해 `bash -e`로 그대로 실행했다.

```text
python3 -m unittest integration_gate.test_http_gate readiness.test_faults            Ran 33 tests, OK
unittest discover reference/settlement_f01_f03                                         Ran 20 tests, OK
unittest discover reference/booking_resale_admission                                   Ran 43 tests, OK
unittest discover reference/credit_advance_f04                                         Ran 20 tests, OK
python3 scripts/check_openapi_contract.py
  openapi contract pin ok: commands=40 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff
python3 scripts/check_openapi_contract.py --self-test                                   self-test: pass
python3 scripts/check_integration_gate_openapi.py
  integration-gate openapi ok: commands=40 productionEndpoint=false publicHost=false
python3 scripts/check_integration_gate_openapi.py --self-test                           self-test: pass
exit 0
```

실패가 단계를 멈추는지도 따로 확인했다. 존재하지 않는 suite 이름을 넣으면 `bash -e` 반복문이 `ImportError` 뒤 exit 1로 끝났다.

나머지 로컬 대응 검사:

```text
python3 scripts/verify_runtime_architecture.py                                          exit 0
python3 scripts/test_runtime_architecture.py                                            Ran 7 tests, OK
cargo fmt --manifest-path runtime/Cargo.toml --all -- --check                           exit 0
cargo test --manifest-path runtime/Cargo.toml --workspace --locked                      128 passed, 0 failed
cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked -- -D warnings   exit 0
cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked                    78 passed, 0 failed
```

잠금 blob은 작업 전과 작업 후 모두 규정값과 같았다. `git ls-tree HEAD`와 `git hash-object` 두 방법으로 확인했다.

- `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`

## 실행하지 않은 것

- `scripts/bootstrap.sh` 이후의 `protocol.yml` 단계는 실행하지 않았다. 여기에는 Sui CLI·Move·ZK 회로, 저장 복구 탐침, localnet 여정이 들어간다. 이번 변경은 그 단계들을 바꾸지 않았다.
- hosted CI 두 workflow의 exact-head 결과는 아직 없다. 사용량 복구(사용자 안내: 2026-10-01) 전까지 merge-ready를 주장하지 않는다.

## 비주장

로컬 통과는 운영 준비, 실자금·체인 확정, 법적 적합성의 근거가 아니다. mock 상태기계 시험 통과는 해당 원래 32항목의 라벨 승격 근거가 아니다.
