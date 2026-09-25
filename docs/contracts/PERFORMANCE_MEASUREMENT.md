# 성능 계약·측정 장치 — 첫 묶음

2026-09-16 초안 0.1. 2026-09-25 Task 004는 장치 출력, 부하 구분, 로컬 release
증거 경로, 비주장만 명확히 했다. 승인된 제품 숫자를 추가하지 않았다.

범위: 잠금 v4를 호출하는 별도 memory-only single-driver 하네스.
승인된 제품 TPS·p99·실패율은 **미정, 숫자 없음**. 이 문서는 측정 의미를 정하고
장치를 시험하는 문서이며 release 성능 달성·backend 우월성·R2 승인을 하지 않는다.
PostgreSQL 비교와 backend 선택은 이 명확화에서 시작하지 않는다.

## 측정 의미

| 값 | 정의 |
|---|---|
| 신규 성공 | 최초 Reserve가 Held를 반환한 횟수. retry는 제외. JSON `new_success_count`와 `new_held` |
| 재시도 | 이미 저장된 최초 결과를 반환. 신규 경제 효과로 세지 않음. JSON `replayed` |
| 업무 거절 | unavailable 등 최초 업무 결과가 거절인 경우. JSON `business_rejected` |
| Capacity | 기록/관측 예산 고갈로 거절된 명령. 품절과 분리. JSON `capacity` |
| conflict retained | 상충 원문이 보존된 관측. 성공 구매로 세지 않음. JSON `conflict_retained`. `other`에 넣지 않음 |
| other | Capacity가 아닌 기타 오류와, Conflict가 아닌 기타 관측의 합. 신규 성공이 아님 |
| service_ns | 개별 커널 호출과 결과 분류를 실행한 계측 구간. 실제 I/O 없음 |
| scheduled_latency_ns | 고정 예정 도착시각부터 완료까지. rate=0이면 호출 구간 지연이며 open-loop가 아님 |
| elapsed_ns | workload 루프 전체 시간. 입력 사전 구성·파일 출력은 제외. rate>0이면 예정 대기가 포함됨 |
| first_capacity_index | 첫 고갈의 0-based 명령 위치. 없으면 null |
| samples_after_first_capacity | 첫 고갈 표본 뒤의 호출 수. 고갈 뒤 표본을 버리지 않음 |
| mixed_result_p99_* | 모든 outcome을 한 분포로 모은 nearest-rank p99. 구매 p99·신규 성공 p99·제품 p99가 아님 |
| outcomes.* | outcome별 개수와 그 outcome만의 service/scheduled p99. 개수가 0이면 p99는 null |
| memory_only_new_held_per_elapsed_s | `new_held * 1000000000 / elapsed_ns` 정수. 메모리 루프 비율이며 제품 TPS가 아님 |

현재 CSV는 모든 호출의 scheduled/start/end/service/latency/outcome을 저장한다.
JSON의 혼합 p99 키는 `mixed_result_p99_service_ns`와
`mixed_result_p99_scheduled_latency_ns`뿐이다. 이 값을 구매 성공 지연으로 읽지 않는다.
신규 성공 건수는 `new_success_count`이고, 그 호출만의 지연은 `outcomes` 안 `held`다.
빠른 업무 거절이나 Capacity를 성공률·성공 지연에 섞지 않는다.
표본이 모두 Held여도 혼합 p99 키 이름은 그대로다. 숫자 일치를 구매 p99로 바꾸지 않는다.

2026-09-16 JSON은 retained conflict 건수를 `other`에 넣었다. 2026-09-25 장치는
`conflict_retained`로 분리한다. [V4-SMOKE-001](PERFORMANCE_BASELINE_V4.md)의 논리
서명 표는 이미 그 건수를 conflict retained로 적고 있으며, 그 ID의 역사 바이트는
고치지 않는다.

## 부하 구분

한 실행은 입력 형태와 예산 단계를 함께 적는다.

| 구분 | 장치에서의 의미 |
|---|---|
| low-load | `uniform`이고 Capacity·업무 거절·재시도·retained conflict·기타가 0. 예시의 `low-load-uniform`은 표본 수 `min(32, command_limit-1)` |
| 균등 | 좌석을 세그먼트 안에서 순환. 명령 예산을 넘으면 low-load가 아니라 saturation |
| hot-seat | 서로 다른 명령이 좌석 0만 반복. 예산 안이어도 업무 거절이 난다. low-load가 아님 |
| same-command retry | 동일 명령의 최초 Held와 이후 replay. 새 명령 예산을 같은 방식으로 다시 소모하지 않음. low-load가 아님 |
| history-growth | retained-conflict 입력이 관측 슬롯에 누적. Capacity 전에도 history-growth |
| saturation | 첫 Capacity가 있다. `budget_phase`는 `includes-samples-after-first-capacity`. 그 뒤 CSV 행을 남긴다 |

workload 도중 커널 재생성은 0회다. 무한 예산으로 고갈을 숨기지 않는다.
재고는 좌석 세그먼트 `[4096]`, 주문 예산 4096, 관측 예산 128이다.
Conflict 포화는 명령 한도가 아니라 관측 예산 128에서 난다. 명령 한도를 올려도
관측 한도가 늘어나지는 않는다. 사전 관측 1건이 이미 슬롯 하나를 쓴다.

## 구현 범위

별도 파일 `runtime/crates/kix-kernel/examples/r1_perf_probe.rs`와
`tests/support/perf_probe.rs`가 현재 커널의 public API만 호출한다.
커널 소스·색인·release 전이는 변경하지 않는다.
워크로드는 균등 좌석, hot seat, 동일 명령 재시도, retained conflict 증가의 네 개다.
예시는 같은 한도·rate로 low-load uniform 대조 파일도 쓴다.
명령 예산·주문 예산·관측 예산·요청 수·rate를 JSON에 명시한다.

rate=0은 서비스 시간 microbenchmark이며 open-loop라고 부르지 않는다.
rate>0은 고정 origin의 i/rate 예정시각을 유지한다. 늦었다고 다음 도착시각을
응답 시점에서 다시 잡지 않는다. 단일 드라이버의 backlog를 드러내지만 네트워크·
멀티스레드 경쟁·cell 장애 격리를 구현/측정하는 것은 아니다.

초기 CI smoke는 4×512 호출과 16개 scheduled 호출을 debug 테스트로 수행한다.
작은 표본·debug 빌드·공유 CI 환경이므로 그 p99를 제품 수치나 안정적인 성능 하한으로
채택하지 않는다. 이 smoke는 분류·포화 뒤 표본 보존·결과 분리 키를 확인하는 장치
검증이다. production p99/TPS 결과가 아니다. 논리 건수는 V4-SMOKE-001 표와 맞춘다.
그 문서의 지연 숫자를 이번 명확화의 현재 실측으로 가져오지 않는다.

## 실행과 자료

```bash
cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked
cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked
cargo run --manifest-path runtime/Cargo.toml -p kix-kernel --example r1_perf_probe --release --locked -- .local/perf/task-004 8192 4096 1000
```

마지막 명령은 로컬 재현 절차다. CI가 이 release 프로브를 실행했다는 기록이 아니다.
출력 디렉터리는 `.local/perf/task-004/`이며 git에 들어가지 않는다. 제품 SLO로
커밋하지 않는다. 파일은 네 workload의 CSV/JSON, `low-load-uniform.csv/json`,
`binding.json`이다. 일반 사용 경로 `.local/perf/manual`도 같은 예시다.

`binding.json`은 그 실행의 commit·tree, 잠금 blob 4개, 프로브 소스 blob,
`rustc --version`, 가능하면 `uname -srvm`, target os/arch, build mode, 표본 수,
command limit, rate, 출력 파일 이름을 묶는다. 잠금 blob이 필요한 값과 다르면
예시는 증거 파일을 쓰지 않고 실패한다. 이 묶음은 그 한 번의 로컬 실행 설명이다.
전용 장비의 반복 캠페인이나 승인 SLO가 아니다.

debug smoke artifact는 `.local/verification/ktx/`에 남는다. 테스트 증거 파일이며
거래 저널이나 R2 영속 저장이 아니다.

기존 Cargo/CI 설정은 그대로이며 Cargo의 자동 tests/examples 탐지를 사용한다.
테스트용 시간/파일 출력 허용은 harness와 example에만 있고 kernel lint는 유지한다.

## 비주장

이 장치가 보여 주는 것은 결과 분류, 예정 지연과 서비스 시간의 분리, 예산 고갈
이후 표본 보존, outcome별 요약, low-load와 hot-seat·retry·history-growth·
saturation의 구분이다. 아래는 이 문서와 로컬 출력으로 성립하지 않는다.

- 승인된 절대 TPS, p99, 허용 실패율. 임의 2배·0.1%도 승인 SLO가 아니다.
- 혼합 p99를 구매 p99 또는 신규 성공 p99로 부르는 것.
- 전체 시스템, DB, 체인 확정, 네트워크, 다중 드라이버 측정.
- release 로컬 1회를 전용 장비의 반복 하한이나 내구 TPS로 채택하는 것.
- debug CI smoke와 release 로컬 실행의 지연을 속도 향상으로 비교하는 것.
- PostgreSQL이나 다른 backend와의 우열, backend 선택, R2 착수.
- 과반 상실이나 제공자 불능에서의 신규 성공 처리량 약속.
- 숫자가 없는 제품 성능 계약이 완료됐다는 표시.

전용 장비의 반복 release 측정, 승인된 목표 숫자, 동등 조건의 backend 비교는
아직 없다. 목표 없는 탐색 출력은 탐색 자료다.

실행 메모는 `validation/2026-09-25-task-004-perf-measurement/README.md`다.
