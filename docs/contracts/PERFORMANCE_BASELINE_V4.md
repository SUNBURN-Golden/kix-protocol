# V4-SMOKE-001 — 고정 측정 조건과 해석

2026-09-16. 이전 측정은 commit `0394a36a655b86bacb568b055d377d4c4fd91185`,
KTX CI `35062501720` / test-merge `bdc663b47663b885dce36e7138a407b7b0658089`,
tree `38096dc849dc338f12aa69bce2200cda971a6d3c`에서 실행했다.
원시 artifact 10432559404 ZIP SHA-256:
`3f8a050a880f5ef15e4ee4668b7c3909d49a0e7486dbb5136a4d52f8fa401c8d`.

## 1. 직접 측정한 것과 측정하지 않은 것

직접 측정은 **고정 예산 아래 누적 입력을 회수 없이 적용했을 때의 포화**다.
하지만 이 workload는 예약 만료를 u64::MAX로 설정하고 expire/final-failure/void,
보존 완료 또는 명시적 회수 자격을 발생시키지 않는다. 따라서 75% 안팎 Capacity를
'회수 기능이 없기 때문에 생긴 비율'의 통제된 인과 측정으로 부르면 안 된다.
회수 기능이 생겨도 이 똑같은 입력에서는 회수 자격이 없어 여전히 포화될 수 있다.

Uniform과 HotSeat의 384/512는 정확히 75%다. Conflict의 385/512는
75.1953125%다. 이는 행정적으로 선택한 작은 예산·표본 수의 결과이지 KIX의
실서비스 실패율이나 회수 개선률이 아니다. 명령상한2의 만료 재현은 별도 테스트
증거이며 이 smoke의 입력에 몰래 포함시키지 않는다.

## 2. 비교를 위해 고정하는 입력·코드

| 항목 | V4-SMOKE-001 값 |
|---|---|
| kernel | semantics=4; blob 69564b166f0c27f9af5d8422f0a466b18d74c20f |
| generator | tests/support/perf_probe.rs; blob df8bf63daf52d35f49e109fa10d14a59ee494ee7 |
| smoke test | tests/performance_harness.rs; blob 6ee81c86a6f587b6b1bf549ce0043a5e43555d43 |
| samples | 512 per workload; scheduled control separately 16 |
| inventory | one contiguous segment [4096], initially empty |
| limits | commands=128, orders=4096, observations=128 |
| amount/context | 1000 atoms; fixed AssetId [10;32], registry version1/hash[11;32]; quote[12;32], policy[13;32] |
| scope/principal/owner | ids80/81/90; owner generation1; business epoch1 |
| provider/account | ids82/83 |
| request expiry | u64::MAX; no expiry/final-failure/void/GC action emitted |
| logical time | index+10 during measured loop; 0-based index |
| rate | 0 for four primary workloads; scheduled HotSeat control rate10000 |
| seed | none: fixed deterministic index-based inputs |
| concurrency | one driver; no production scheduler/network/replicas |
| reset | fresh kernel between independent workloads, ZERO reset inside each workload |
| setup/timing | inputs preconstructed; conflict prefill outside loop; timed loop includes call and outcome classification, excludes file output |

Uniform: request i+1, order10001+i, operation i+1, seat i mod4096, count1.
HotSeat: same distinct identities but seat0. Retry: request1/order10001/operation1 and
seat0 on every call. Conflict: prefill request1 seat0 at time1; capture event500
at time2 with evidence[60;32]. Then same provider/account/event and amount, new
operation20000+i, for 512 calls. Its original observation already occupies one
of 128 evidence slots. There is no first-send mark call in this prefill.

## 3. Fixed result signature (not latency target)

| workload | new Held | business rejected | replayed | conflict retained | Capacity | first Capacity index | final remaining |
|---|---:|---:|---:|---:|---:|---:|---:|
| Uniform | 128 | 0 | 0 | 0 | 384 | 128 | 3968 |
| HotSeat | 1 | 127 | 0 | 0 | 384 | 128 | 4095 |
| Retry | 1 | 0 | 511 | 0 | 0 | none | 4095 |
| Conflict | 0 | 0 | 0 | 127 | 385 | 127 | 4095 |
| scheduled HotSeat (16 calls) | 1 | 15 | 0 | 0 | 0 | none | 4095 |

## 4. Environment and comparability

Original workflow requested ubuntu-24.04 and Rust1.98.1, cargo test --locked,
debug assertions=true, shared GitHub-hosted runner. Actual CPU model/count,
NUMA/host load/frequency and isolation were NOT captured in the retained artifact:
**미정 / 숫자 없음**. They must not be retroactively invented. This is a logical
result baseline, not a controlled hardware latency baseline. Tests may execute
concurrently under the default Rust test runner; single-driver does not mean
whole-runner exclusive CPU use. The new invariant suite may change runner load.

Preserve original CSV and outcome partitions, count all samples after saturation,
and do not compare a future release run against this debug run as a speedup.
Use nearest-rank p99 on the same sample/phase/outcome definition. Rate>0 uses a
fixed origin i/rate, and rate=0 is not called open-loop. New versions must preserve
this baseline's bytes and parameters under this ID. A changed policy/action mix
is a new profile, not an edited V4-SMOKE-001.

When lifecycle semantics are approved, repeat this unchanged profile as a control.
A separate paired profile must include the APPROVED terminal/expiry/retention
facts on both baselines to measure reclamation effects; it is not specified or
implemented in this turn because those inputs are still unresolved. No release
transition, kernel change, benchmark reset workaround or new performance SLO is
introduced. Current smoke source and assertions remain unchanged.
