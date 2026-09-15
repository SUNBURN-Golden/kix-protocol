# KIX on-sale admission control and inventory routing — v5

정본은 [ADR-0001](../docs/adr/0001-ktx-authority-commit-recovery.md)의 실행 모드/배타 범위로 결정한다. Waiting room은 load-control 및 GA routing이며 재고 권위를 만들지 않는다. 아래는 KTX-R4의 구현 계약이다. 현재 R1 커널에 edge/queue/scheduler가 구현됐다는 뜻이 아니다.

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
