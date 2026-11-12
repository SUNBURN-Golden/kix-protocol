# KIX on-sale admission control and inventory routing — v5

정본은 [ADR-0001](../docs/adr/0001-ktx-authority-commit-recovery.md)의 실행 모드/배타 범위로 결정한다. Waiting room은 load-control 및 GA routing이며 재고 권위를 만들지 않는다. 아래는 KTX-R4의 구현 계약이다. 현재 R1 커널에 edge/queue/scheduler가 구현됐다는 뜻이 아니다.

## 개정 헤더 — ONSALE-STAGE5-LOCAL-0.1 (2026-11-12)

- 개정 id: `ONSALE-STAGE5-LOCAL-0.1`. 관측 base: `2ec62ca73ee41f397268944e8e0de98ef9d03305` (`origin/main`, 노드 `k-onsale-admission-control` 시작 시점).
- 상태: **로컬·비운영.** 이 개정은 §1–8의 술어를 하나도 약화하거나 대체하지 않는다. §1–8은 그대로 효력이 있고, §9는 그 술어를 채택된 stage-5 로컬 backend 위에 어떻게 실현했는지 대응표일 뿐이다. §10은 열린 값, §11은 비주장이다.
- backend 근거: [백엔드 채택 제안](../docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md) §6 채택 문장(선택지 A, 로컬·비운영 PostgreSQL 17.11 (Debian 17.11-0+deb13u1), 단일 프로세스·단일 작성자·기본 꺼짐·운영 플래그 false). User 병합 `bb193efb5d238581096372c8a20bee1271dfe4df`(PR #140)는 이 브랜치 HEAD의 조상이고 파일은 병합본과 바이트 동일하다. 선행 `k-stage5-durable-tx`는 PR #443(병합 `2ec62ca`)으로 병합됐고 `durable/` 계층이 HEAD에 있다. [완료 설계 §5.1](../docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md)의 ADOPT 판정 근거는 이름이 아니라 §6 문장이 backend를 직접 지목한다는 사실이다.
- 구현 위치: 최상위 `onsale/` 패키지(로컬 Python API). `durable/`은 수정 없이 합성(compose)한다. 새 프로토콜/wire 명령은 없다. 공개 엔드포인트는 없다. 권위 모델·구현 승인 상태는 이 개정으로 바뀌지 않는다: 모델 1에서 현재 v4 커널은 완전 구현이 아니고, 이 로컬 계층도 모델 1의 완전 구현이 아니다.
- Waiting room은 계속 load-control/router이며 재고 권위를 만들지 않는다. NativeChainExecution의 local HOLD는 체인 재고/발행 확정이 아니다. DelegatedExecution은 grant 검증 전 비활성이다(`runtime/ARCHITECTURE.toml`의 `delegated_execution_enabled = false` 유지).

## 1. 재고와 실행 단위

ReservedSeating와 GeneralAdmissionSharded를 분리한다. 온체인 지정석은 단일-seat contention cell을 유지한다. 오프체인 writer는 행/실제 연속 구간을 소유하고 여러 구간을 실행/복제 shard에 묶을 수 있다. 행 하나당 thread/Raft group 하나를 요구하지 않는다.

GA는 생성 시 `sum(initialShardCapacity) == immutableTotalCapacity`를 검증한다. 권위 shard는 capacity를 독립 강제한다. 전역 mutable capacity hot row를 만들지 않는다. 동시 소비 가능 자원을 단순 캐시 수치로 승인하지 않는다.

## 2. 상태와 비용을 분리

Waiting users는 queue token + coarse versioned artifact를 받으며 좌석 스트림을 받지 않는다. Admitted buyers는 홈 권위/세대에 결합된 제한된 세션 상태와 bounded snapshot/delta를 사용한다. Audit evidence는 온라인 스케줄러와 별도로 보존한다.

live scheduling state의 목표와 전체 장기 저장량을 혼동하지 않는다. 정산/환불/재시도/공정성 증거는 거래/보존기간에 따라 증가한다. active session cap, records, bytes와 보존 전략을 각각 정의한다.

## 3. Router의 추정과 정본

```text
effectiveRemaining = observedShardRemaining - outstandingUnexpiredTokens
```

이는 routing hint다. 실제 reservation은 해당 실행 모드의 권위 경계를 통과한다. NativeChainExecution에서 local HOLD는 체인 재고/발행 확정이 아니다. DelegatedExecution은 grant 검증 전 비활성이다. PostgreSQL pool을 무제한 유입 버퍼로 사용하지 않는다.

## 4. Admission token

```text
showId / queueTicketId / queuePositionIdentity
inventoryEpoch / inventoryMode / authorityPlacementVersion
shardId (GA routing) / nonce / issuedAt / expiresAt / signature/keyVersion
```

다른 show/epoch/scope로 token을 재사용하지 못한다. 서명된 attempt_no만으로 outstanding=1이나 전 세계 single execution을 주장하지 않는다. admitted session의 제한된 서버 상태와 원자적 검사로 이를 강제한다.

CommandIdentity는 stable business scope + authenticated principal + client_command_id다. owner generation이나 routing 변경으로 동일 명령이 새 명령이 되지 않는다. fingerprint는 원래 payload와 따로 저장하며 payload를 key에 섞어 변조 명령에 새 identity를 주지 않는다.

## 5. 재시도와 availability hints

```text
bounded parsing/authentication/routing
 -> existing command result or in-flight coalescing
 -> eligibility for a NEW attempt
 -> versioned negative hint
 -> authoritative decision
 -> durable commit / truthful result
```

같은 key의 payload가 다르면 충돌로 거절한다. 최초 성공 응답 유실 뒤 bitmap HELD만 보고 새 실패를 응답하지 않는다. 최초 결과와 현재 예약 만료 여부는 별도다. 결과 조회도 인증/권한 검사와 durable proof 경계를 유지한다.

SOLD는 refund/reopen으로 바뀔 수 있다. 공개 뷰는 inventory epoch, segment version, source commit position, expiry를 포함한다. stale negative hint는 영구 재고 판정이나 자동적인 idempotent business outcome이 아니다. 재공개/무효화와 retry/query 경로를 별도 보장한다.

## 6. Queue-position preserving reissue

```text
old token -> terminal REPLACED/EXPIRED
new token -> same queueTicketId + same queuePositionIdentity
             new shardId + new nonce + new expiry
```

재발급은 원래 순위를 유지하며 사용자를 뒤로 보내지 않는다. 구/신 token 동시 소비는 한 번의 용량 소비만 만들 수 있어야 한다. 단순 uniform random 대신 capacity-aware/power-of-two choices 등을 후보로 비교하되 재고 정합성과 순위 보존 조건은 바뀌지 않는다.

## 7. 실행·관측·복구 예산

cell/shard/provider별 request count, payload bytes, 최대 queue wait, outstanding external operations, HOLD 수, retry budget을 제한한다. 신규 claim 폭주가 payment observations, 만료, 취소 fence, 복구, 환불 예약을 굶기지 않도록 별도 예산과 공정 스케줄링을 둔다. 반대로 무제한 strict priority도 금지한다.

group commit은 count/bytes/max wait 중 먼저 도달한 경계로 제안한다. 저부하에서 큰 배치를 기다리는 latency를 숨기지 않는다. PG/chain/export backlog age/bytes와 retained WAL에 상한을 두고 영향 제공자/판매 범위의 신규 의도를 줄인다. UNKNOWN 작업을 다른 PG에 새 요청으로 우회하지 않는다.

## 8. Audit/fairness

append-only evidence에 queueTicketId, queuePositionIdentity, admission/reissue sequence, old/new shard, reason, issued/expiresAt, final reservation outcome을 보존한다. 필수 증거를 telemetry sampling으로 제거하지 않는다. 메트릭에 request/user/seat별 무한 label cardinality를 만들지 않는다.

시험은 queue latency/admitted RPS/retry amplification/durable reservation success/GA reissue/순위 위반/각 queue saturation/완료 작업 지연을 분리한다. reject RPS를 purchase TPS라고 표기하지 않는다.

## 9. Stage-5 로컬 backend 대응표 (ONSALE-STAGE5-LOCAL-0.1)

아래는 §1–8 각 술어의 로컬 실현이다. 권위 shard 경계는 채택된 PostgreSQL 위 `onsale/unit.py` `AdmissionUnit`의 단일 작성자 SERIALIZABLE 커밋으로 실현한다. 예약 좌석(reserved-seat) 권위는 기존 `durable/unit.py` `DurableUnit`(`slot_hold`)에 그대로 남는다. 토큰 계층은 시도(attempt)를 게이트할 뿐 좌석 재고를 감소시키지 않는다. 두 저장 단위 사이의 원자성은 주장하지 않는다(§11).

| 절 | 술어 | 로컬 실현 | 시험 |
|---|---|---|---|
| §1 | GA 생성 시 `sum(initialShardCapacity) == immutableTotalCapacity` | `onsale/model.py` `validate_ga_config`가 생성 시점에 검증하고, `onsale_ga_config`의 total은 불변 행(CRC)으로 고정된다. 다른 값의 재설정은 거부된다 | `test_pure`.bad-sum/중복/비양수 거부; `test_onsale` 재설정 거부 |
| §1 | 권위 shard의 독립 capacity 강제, 전역 mutable hot row 없음 | shard별 `onsale_ga_shard.remaining`을 같은 커밋에서 `remaining > 0` 검사 후 1 감소. 전역 capacity 행은 없다. 감소는 커밋된 admit 증거 수와 Opening 시 대조하여 불변식으로 검증한다 | `test_onsale` 동시 소비가 shard capacity를 초과하지 않음; 전역 행 부재; remaining 변조 fail-closed |
| §2 | waiting은 queue token + coarse versioned artifact, 좌석 스트림 없음 | `onsale_queue_ticket`(단조 seq·position identity) + `room.queue_artifact`(버전·대기/입장 수만, 좌석·사용자별 label 없음) | `test_onsale` artifact에 좌석 스트림·개인 label 부재, 버전 단조 |
| §2 | admitted는 제한된 세션 상태 + bounded snapshot, session cap | `onsale_session` 행 + `max_sessions` 필수 인자. 초과 시 새 admit은 capacity 거부(무기록) | `test_onsale` session cap 거부·무기록 |
| §3 | `effectiveRemaining = observedShardRemaining - outstandingUnexpiredTokens`, hint ≠ 권위 | `onsale/model.py` `effective_remaining`(0 클램프) + `onsale/router.py` 읽기 전용 라우터. stale/낙관 hint로 라우팅해도 커밋 시 shard 검사가 다시 거부한다. remaining의 유일한 작성자는 `AdmissionUnit` 커밋이다 | `test_pure` hint 산술; `test_onsale` stale hint 라우팅 후 커밋 거부 |
| §3 | PostgreSQL pool을 무제한 유입 버퍼로 쓰지 않음 | 단일 프로세스·단일 작성자 FileLock + 5클래스 count/bytes/age 예산(`durable/budgets.py` 재사용). 유입 폭주는 별도 클래스를 굶기지 않는다 | `test_onsale` inflow 포화에서도 reissue/expiry/replay 동작 |
| §4 | token 필드와 바인딩, 재사용 금지 | `onsale/tokens.py`가 §4 필드명 그대로(`showId/queueTicketId/queuePositionIdentity/inventoryEpoch/inventoryMode/authorityPlacementVersion/shardId/nonce/issuedAt/expiresAt/signature/keyVersion`) 발급·검증. 서명은 호출자 공급 키의 fixture HMAC-SHA256이며 키는 저장소에 커밋하지 않는다. 소비는 커밋 내 원자적 상태 검사(ISSUED→CONSUMED)로 강제한다 | `test_pure`/`test_onsale` wrong show/epoch/scope/expiry/tamper 거부; 서명된 attempt_no만으로 single execution을 주장하지 않음(상태 검사가 강제) |
| §4 | CommandIdentity = stable scope + principal + client_command_id, fingerprint 분리 | identity = (show, epoch, mode) + principal + client_command_id의 해시. shardId/nonce/placement는 키에 넣지 않는다. payload sha256은 `onsale_command`에 별도 저장 | `test_pure` routing 변경이 identity를 바꾸지 않음; `test_onsale` payload 변조는 conflict |
| §5 | retry → 기존 결과 → 새 시도 자격 → versioned negative hint → 권위 결정 → durable commit | `onsale_command`의 replay/conflict_retained 경로(durable과 같은 어휘), `CommitUnknown`→unknown, `onsale_hint`(epoch·version·source commit position·expiry) | `test_onsale` replay는 저장된 최초 결과; conflict 1회 보존; lost-ack 뒤 read-truth; negative hint 만료·epoch 무효화, 영구 SOLD 없음 |
| §5 | 최초 성공 응답 유실 뒤 bitmap HELD만 보고 새 실패 응답 금지 | 최초 결과는 불변 행으로 저장되고 replay가 그대로 반환한다. 현재 예약 만료 여부와 별도다 | `test_onsale` lost-ack 후 재시도는 replay |
| §6 | reissue: old→REPLACED, new는 same ticket+position, new shard/nonce/expiry | `AdmissionUnit.reissue`가 한 커밋에서 old를 terminal REPLACED로 닫고 new를 발급한다. position identity·seq는 그대로 | `test_onsale` 순위 불변; old+new 경쟁에서 용량 소비 1회 |
| §6 | capacity-aware/power-of-two 후보 비교, 정합성·순위 조건 불변 | `onsale/router.py` 두 전략(호출자 공급 seeded RNG). 전략 선택은 운영 결정(§10)이며 어느 전략도 remaining을 쓰지 않는다 | `test_pure`/`test_onsale` 두 전략 모두 순위 위반 없음 |
| §7 | 클래스별 count/bytes/age 예산, 굶김 금지, strict priority 금지 | `durable/budgets.py` `BudgetSpec`/`ClassLimit` 재사용(5클래스 모두 필수). enqueue/최초 admit=inflow, reissue=recovery, expiry sweep=completion, conflict 증거=observation, cancel=작성자 없는 필수 슬롯 | `test_pure`/`test_onsale` 클래스 독립·포화 시나리오 |
| §7 | group commit은 count/bytes/max wait 중 먼저 도달한 경계 | `onsale/model.py` `propose_group`(순수 함수). 저부하에서 max wait가 먼저 오면 작은 배치를 제안한다 | `test_pure` 세 경계 각각 first-of |
| §8 | append-only 증거에 §8 필드 전부, sampling 금지, 무한 label cardinality 금지 | `onsale_evidence`는 append-only + 전 행 CRC. 메트릭 counter는 (show, shard, class) 키만 | `test_onsale` 전 필드 존재; CRC 변조 fail-closed; reject RPS와 admitted 분리 보고 |

로컬 커밋 위치(`source_commit_position`)는 이 저장소의 단조 커밋 카운터이며 체인 source cut가 아니다(ADR-0001 §9). `runtime/ARCHITECTURE.toml`의 `oltp_major = 18`과 채택 핀 17.11의 차이는 characterization으로만 기록하고 toml은 수정하지 않는다.

## 10. 열린 값 — DECISION_REQUIRED · Astra / UNDETERMINED

구현은 전부 파라미터화되어 있고 기본값은 없다. 아래 값은 이 개정이 정하지 않는다.

| 값 | 상태 | 담당 |
|---|---|---|
| 최대 queue wait, 우선순위/부스트 규칙 등 공정성 수치 | DECISION_REQUIRED | Astra |
| shard capacity, session cap, outstanding-token cap, token TTL | DECISION_REQUIRED | Astra |
| 운영 routing 전략 선택(capacity_aware vs power_of_two) | DECISION_REQUIRED | Astra |
| 운영 서명 방식·키 관리 | DECISION_REQUIRED | Astra |
| 운영 group commit 경계(count/bytes/max wait) | DECISION_REQUIRED | Astra |
| queue/admission 증거 보존 기간 | UNDETERMINED | User ([보존 기간 제안](../docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md), 법률 입력 의존) |
| refund/reopen에 의한 SOLD 뷰 무효화 | UNDETERMINED | User/Astra (잠금 lifecycle 전이 의존; 로컬에서 hint는 epoch/version/expiry로만 무효화) |
| 만료된 ticket의 순위 부활 정책 | DECISION_REQUIRED | Astra (로컬 reissue는 ISSUED 토큰에서만; ticket의 position identity·seq는 보존) |

새 프로토콜 명령(예: cancel command)은 이 개정이 만들지 않는다. `cancel` 예산 클래스는 작성자 없는 필수 슬롯으로만 존재한다.

## 11. 비주장 (non-claims)

이 개정과 `onsale/` 구현은 다음을 주장하지 않는다: production 준비, 내구성 동등성, power/OS crash 거동, 하드웨어 flush, 독립 장애 도메인, bank exactly-once, 체인 finality, 분산 fencing, 법률 준수, SLO/TPS/p99/RTO/RPO 수치, 독립 인수. 모든 증거는 빌더 작성 로컬 fixture 증거이며 비작성자 검토·Astra 감사·exact-head CI·User 병합 전이다. `protocolTruth`/`productionConformance`/`productionReadiness`/`productionEndpoint`/`chainWriter`/`fundsExecuted`는 false이고 `LOCAL_ONSALE_FIXTURE_ONLY` 라벨만 로컬 표시다. R2·복제·합의·자체 저장 엔진, 실 PG/은행/KYC 호출, 공개 엔드포인트, Sui testnet/mainnet, 새 coin/TIX 모듈은 열리지 않는다. 토큰 계층과 reserved-seat(`DurableUnit`) 사이 cross-store 원자성은 주장하지 않는다. 시험 수치는 fixture이며 제품 정책이 아니다.
