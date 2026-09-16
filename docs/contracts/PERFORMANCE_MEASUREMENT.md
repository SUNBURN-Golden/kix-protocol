# 성능 계약·측정 장치 — 첫 묶음 초안 0.1

2026-09-16. 범위: 잠금 v4를 호출하는 별도 memory-only single-driver 하네스.
승인된 제품 TPS·p99·실패율은 **미정, 숫자 없음**. 이 문서는 측정 의미를 정하고
장치를 시험하는 문서이며 release 성능 달성·backend 우월성·R2 승인을 하지 않는다.

## 측정 의미

| 값 | 정의 |
|---|---|
| 신규 성공 | 최초 Reserve가 Held를 반환한 횟수. retry는 제외 |
| 재시도 | 이미 저장된 최초 결과를 반환. 신규 경제 효과로 세지 않음 |
| 업무 거절 | unavailable 등 최초 업무 결과가 거절인 경우 |
| Capacity | 기록/관측 예산 고갈로 거절된 명령. 품절과 분리 |
| conflict retained | 상충 원문이 보존된 관측. 성공 구매로 세지 않음 |
| service_ns | 개별 커널 호출과 결과 분류를 실행한 계측 구간. 실제 I/O 없음 |
| scheduled_latency_ns | 고정 예정 도착시각부터 완료까지. rate=0이면 호출 구간 지연 |
| elapsed_ns | workload 루프 전체 시간. 입력 사전 구성·파일 출력은 제외 |
| first_capacity_index | 첫 고갈의 0-based 명령 위치. 고갈 뒤 표본도 보존 |

현재 CSV는 모든 호출의 scheduled/start/end/service/latency/outcome을 저장한다.
p99 요약은 혼합 결과 분포이므로 CSV의 outcome별 분석 없이 구매 p99라고 쓰지 않는다.
실제 신규 성공 goodput은 실패·재시도 처리량과 구분해 산출해야 한다.

## 구현 범위

별도 파일 `runtime/crates/kix-kernel/examples/r1_perf_probe.rs`와 지원 모듈이
현재 커널의 public API만 호출한다. 커널 소스·색인·release 전이는 변경하지 않는다.
워크로드는 균등 좌석, hot seat, 동일 명령 재시도, retained conflict 증가의 네 개다.
명령 예산·요청 수·rate를 명시한다. workload 중 커널 재생성은 0회다.

rate=0은 서비스 시간 microbenchmark이며 open-loop라고 부르지 않는다.
rate>0은 고정 origin의 i/rate 예정시각을 유지한다. 늦었다고 다음 도착시각을
응답 시점에서 다시 잡지 않는다. 단일 드라이버의 backlog를 드러내지만 네트워크·
멀티스레드 경쟁·cell 장애 격리를 구현/측정하는 것은 아니다.

초기 CI smoke는 4×512 호출과 16개 scheduled 호출을 수행한다. 작은 표본·debug
빌드·공유 CI 환경이므로 그 p99를 제품 수치나 안정적인 성능 하한으로 채택하지 않는다.
고갈까지와 고갈 이후를 함께 기록해 기록 수명 부재를 숨기지 않는다.

## 실행과 자료

```bash
cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test e4_state_model --locked
cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --test performance_harness --locked
cargo run --manifest-path runtime/Cargo.toml -p kix-kernel --example r1_perf_probe --release --locked -- .local/perf/manual 8192 4096 1000
```

마지막 명령은 재현용 사용법이지 이번 CI에서 release 실행했다는 기록이 아니다.
기존 Cargo/CI 설정은 그대로이며 Cargo의 자동 tests/examples 탐지를 사용한다.
테스트용 시간/파일 출력 허용은 새 harness target에만 적용하고 kernel lint는 유지한다.

기록에는 exact commit/tree, 두 locked blob, 신규 source blob, toolchain·OS/arch,
빌드 모드, workload·표본·예산·rate·예정시각·원시 분포를 연결한다.
출력물은 `.local/verification/ktx/`의 기존 artifact 경로로 보존하되 이것은
테스트 증거 파일이지 거래 저널이나 R2 영속 저장 구현이 아니다.

## 다음 판단의 한계

현재 장치의 실행은 latency 계산·분류·포화 노출이 동작하는지의 검사다.
실제 목표 숫자, 전용 장비·release 반복 측정, outcome별 분포와 낮은 부하/편중,
동등 PostgreSQL 조건의 비교는 남아 있다. 임의 2배·0.1% 기준을 승인 SLO로 쓰지 않는다.
과반 상실이나 제공자 불능에서 신규 성공 처리량을 약속하지 않는다.
숫자가 없는 제품 계약까지 완료됐다고 표시하지 않는다.
