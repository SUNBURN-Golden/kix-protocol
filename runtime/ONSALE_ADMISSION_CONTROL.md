# KIX on-sale admission control and inventory routing

KIX 티켓 오픈 성능은 평균 TPS보다 burst admission을 먼저 통제해야 한다. Waiting room은 load-control 및 GA shard router지만 inventory correctness authority는 아니다.

## 1. Inventory mode를 지금 분리

```text
ReservedSeating
GeneralAdmissionSharded
```

### ReservedSeating

- 지정석 1개 = 독립 `InventoryCell` 또는 동등한 단일-seat 경쟁 단위.
- 일반 판매 경로에서 여러 인기 좌석을 한 mutable shard에 묶지 않는다.
- 동일 좌석에 대한 경쟁은 본질적으로 직렬화되지만 다른 좌석은 독립 병렬 처리된다.

### GeneralAdmissionSharded

- 총량형 재고를 여러 `InventoryShard`로 분할한다.
- 생성 시 `sum(initialShardCapacity) == immutableTotalCapacity`를 검증한다.
- 각 shard는 `reserved <= capacity`를 독립적으로 강제한다.
- 일반 구매 경로에서 global mutable capacity counter를 두지 않는다.

## 2. Waiting room 역할

Waiting room은 두 일을 한다.

1. backend/PostgreSQL/chain으로 들어가는 유입 속도 제어
2. GA token 발급 시 현재 추정 여유가 있는 shard로 라우팅

Waiting room의 `effectiveRemaining`은 최적화용 추정치다.

```text
effectiveRemaining
 = observedShardRemaining
 - outstandingUnexpiredTokens
```

실제 capacity authority는 inventory state/chain이다. Waiting room이 stale하면 shard reservation이 fail closed 할 수 있다.

## 3. Admission token

최소 binding:

```text
showId
queueTicketId
queuePositionIdentity
inventoryEpoch
inventoryMode
shardId (GA only)
nonce
issuedAt
expiresAt
signature/keyVersion
```

토큰은 다른 show/epoch/shard로 재사용할 수 없다. ReservedSeating에서는 seat choice/reservation identity를 별도로 bind할 수 있다.

## 4. Queue-position preserving reissue

GA에서 token을 발급했지만 실제 reservation 시 shard가 full이면:

```text
old token -> terminal REPLACED/EXPIRED
new token -> same queueTicketId + same queuePositionIdentity
             new shardId + new nonce + new expiry
```

**재발급은 원래 queue 위치를 보존하고 shard만 바꾼다.** 사용자를 waiting room 맨 뒤로 보내지 않는다.

이 규칙은 fairness contract다. shard routing 오차는 지연으로 보일 수는 있어도 순위 박탈로 보이면 안 된다.

## 5. Shard selection

단순 uniform random을 기본으로 하지 않는다. 초기 후보는 capacity-aware routing이다.

예:

```text
candidate shards with effectiveRemaining > 0
 -> sample/select
 -> prefer larger effectiveRemaining
```

power-of-two choices 같은 경량 알고리즘을 benchmark 후보로 둔다. 알고리즘을 바꾸더라도 queue-position-preserving reissue와 chain capacity authority는 바뀌지 않는다.

## 6. Admission control

- waiting room 밖 요청은 bounded admission gate를 통과하지 못하면 빠르게 거절/재대기시킨다.
- Postgres connection pool을 무한 queue로 사용하지 않는다.
- client retry는 stable command/idempotency identity를 사용한다.
- admission token replay/duplicate submit은 동일 경제효과를 두 번 만들 수 없다.
- burst benchmark는 평균 TPS가 아니라 queue latency, admitted RPS, reservation success, retry amplification, DB pool saturation을 함께 측정한다.

## 7. Audit/fairness

다음은 append-only evidence로 남긴다.

```text
queueTicketId
queuePositionIdentity
admission/reissue sequence
old/new shardId
reason = SHARD_FULL | TOKEN_EXPIRED | ROUTER_REFRESH | ...
issuedAt/expiresAt
final reservation outcome
```

운영자는 '왜 이 사용자의 shard가 바뀌었는가'와 '원래 대기 순위를 유지했는가'를 설명할 수 있어야 한다.
