# KIX production Sui object topology

현재 `reference/v0.3-rc1`의 single shared `Show` + vectors 구조는 regression fixture다. production architecture는 **독립 거래가 서로 다른 mutable objects를 건드리도록** 설계하여 show-wide contention을 만들지 않는다.

Sui에서 독립 object transaction은 병렬 처리 여지가 크고 shared mutable object는 ordering/consensus 경계를 만든다. 따라서 shared state가 필요한 경우에도 충돌 범위를 show 전체가 아니라 seat/sale/admission shard 수준으로 제한한다.

## 1. 목표 구조

```text
Immutable ShowConfig
   |
   +-- InventoryCell / InventoryShard[N]
   |      +-- independent reservation/version state
   |
   +-- Right(ticket) ------------------> holder-owned object
   |
   +-- SaleIntent(sale) ----------------> independent per-sale mutable object
   |      +-- PaymentEvidence(payment) -> independent evidence/commitment
   |      +-- terminal EXECUTED or CANCELLED fence
   |
   +-- AdmissionEpochConfig ------------> immutable epoch/config
          +-- AdmissionShard[0..N]
                 +-- nullifier/spend state local to shard

Immutable VerifierConfig / Policy commitments
```

## 2. ShowConfig

`ShowConfig`에는 show id, organizer authority, immutable policy/version commitments, schedule/config 등 **거래마다 변하지 않는 정보**만 둔다.

- production 목표는 immutable/read-only object다.
- 판매·입장·리셀마다 ShowConfig를 mutate하지 않는다.
- show-wide counters, payment refs, nullifiers, notes를 넣지 않는다.
- 공연 취소 같은 전역 정책 변화가 필요하면 새 immutable cancellation/policy epoch commitment를 만들거나 좁은 별도 control object를 사용하고, 모든 일반 거래가 그 object를 write하지 않게 한다.

## 3. Inventory

좌석/재고 확보 때문에 필요한 mutable contention은 최소 단위로 쪼갠다.

- 지정석: 한 좌석당 하나의 `InventoryCell`. 일반 mutable shard로 여러 지정석을 묶지 않는다.
- 비지정 수량형: hash/range 기반 `InventoryShard` 여러 개로 나눠 단일 counter를 피한다.
- Order는 필요한 cell/shard만 touch한다.
- shard 수와 분할 규칙은 production benchmark로 확정한다.
- DB의 Order/Reservation identity가 chain inventory identity와 exact binding되어야 한다.

## 4. Right

발행된 공개 권리는 독립 owned object를 기본으로 한다.

- 다른 티켓의 이전/사용/리셀과 mutable object가 겹치지 않게 한다.
- generation/version/policy commitment를 Right 자체 또는 좁은 연계 object에 결합한다.
- stale generation 거절 semantics는 현재 fixture의 좋은 특성이므로 유지하되 show-wide generation vector에 의존하지 않는다.

## 5. SaleIntent

리셀/유상 이전은 공연 전체 `Show`가 아니라 **거래별 `SaleIntent`**가 경쟁 단위다.

`SaleIntent`는 최소 다음을 결합한다.

```text
saleIntentId
rightId + expectedRightVersion/generation
seller authority
buyer constraint (optional)
price AssetAmount commitment
policyVersion commitment
payment binding rules
expiry
state: OPEN | EXECUTED | CANCELLED
```

여러 actor가 같은 listing을 다룰 필요가 있어 shared object가 필요하더라도 shared 범위는 그 SaleIntent 하나다.

핵심 불변조건:

```text
EXECUTED xor CANCELLED
```

terminal state 후 같은 SaleIntent/PaymentEvidence를 재사용할 수 없다. 실패한 판매를 보상하기 위해 `cancel_show`를 호출하지 않는다.

## 6. PaymentEvidence

결제 증거는 show vector에 `payment_ref`를 append하지 않는다.

- payment/order/sale별 independent evidence identity를 사용한다.
- 외부 provider fact와 on-chain commitment의 의미를 분리한다.
- `PaymentEvidence` 생성이 실제 은행/PG의 자금 이동 자체를 증명한다고 과장하지 않는다.
- 같은 evidence가 둘 이상의 incompatible SaleIntent에 소비되지 않도록 consumption binding/fence를 둔다.

구체적 object ownership/immutability는 S07 payment identity와 실제 Sui primitive benchmark 후 확정한다.

## 7. Admission / nullifier sharding

private admission의 global `notes/nullifiers/spent_challenges` vector를 production에 사용하지 않는다.

- `AdmissionEpochConfig`는 가능한 한 immutable.
- spend/nullifier mutable state는 `(showId, admissionEpoch, shard)` 단위로 나눈다.
- shard key는 nullifier/slot의 deterministic prefix/hash 등으로 정해 동일 spend만 동일 shard에서 충돌하게 한다.
- root-based privacy를 유지할 경우 root epoch/history와 shard-local commitment 구조를 함께 설계하여 unrelated ticket 변화가 모든 proof를 즉시 stale하게 만드는 범위를 축소한다.
- admission shard 수와 proof/update 전략은 ZK 회로와 함께 benchmark한다.

## 8. 전역 취소

공연 전체 취소는 실제 전역 상태이므로 별도 control primitive가 필요할 수 있다. 하지만 일반 order/sale/admission transaction마다 mutable cancellation object를 write해서 global bottleneck을 만들지 않는다.

S08 구현에서 검증할 기준 구조:

- immutable `ShowConfig`에 권위 있는 `ShowControl` object id를 고정한다. `ShowControl`은 organizer 권한으로만 epoch/cancelled 상태를 바꿀 수 있다.
- 판매/이전/입장 등 취소 영향을 받는 거래는 그 정확한 control object의 현재 상태를 read/check하고, cancelled가 아니며 요청의 expected epoch가 현재 epoch와 같은지 검사해야 한다. 일반 거래는 control을 mutate하지 않는다.
- 요청자가 제출한 과거 immutable epoch commitment만으로 현재성을 승인하지 않는다. 새 epoch 생성만으로 과거 epoch가 자동 폐기된다고 간주하지 않는다.
- 취소는 권위 object의 상태를 갱신해야 하며, 기존 권리/환불 의무는 off-chain Order/Obligation과 chain commitments로 대사한다.
- 이는 구현 예정 설계다. 실제 Sui에서 취소와 거래의 순서·read 경계·처리량을 확인해야 하며, 성능 때문에 현재성 검사를 생략하는 경로는 허용하지 않는다.

## 9. S07/S08 경계

S07은 PostgreSQL Order/Payment/Observation/Obligation identity를 먼저 확정하지만 schema가 single shared Show를 가정해서는 안 된다.

production Move 구현 단계에서는 다음을 gate로 둔다.

1. 두 독립 seat sale가 같은 mutable show object를 쓰지 않는다.
2. 두 독립 resales가 같은 mutable sale object를 쓰지 않는다.
3. one-sale failure/cancellation이 show-wide fence를 요구하지 않는다.
4. admission shard A의 spend가 shard B의 mutable object를 요구하지 않는다.
5. throughput/latency benchmark에서 shard count별 contention을 측정한다.
6. chain object identity와 off-chain KIX-BCS1 Order/Sale/Payment commitments를 exact bind한다.
7. 취소 완료 후 과거 epoch/commitment로 제출한 거래를 거절하고, control id 대체·누락 및 취소와의 경합을 시험한다.
8. `[1,2]`와 `[2,3]` 연석 요청이 경쟁할 때 중복 배정과 묶음 부분 성공을 거절한다. row-local single writer의 보장을 DB reservation commit·결제 observation·chain execution의 보장과 구분하고, 단계별 실패/대사 경로를 시험한다.
9. GA shard token 재발급은 원래 queue position을 보존하며 이전 token을 무효화해야 한다. 구/신 token의 동시 소비가 capacity를 두 번 차감하지 못하는지 실제 경합으로 확인한다.

기존 shared-Show Move 코드는 지우지 않고 역사적 fixture로 남길 수 있으나 production API가 이를 import/호출하는 경로는 만들지 않는다.
