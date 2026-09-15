# KIX production Sui object topology — architecture v5

현재 `reference/v0.3-rc1`의 single shared `Show` + vectors 구조는 regression fixture다. 실제 production Move는 미구현이다. 정본·실행 계약은 [ADR-0001](../docs/adr/0001-ktx-authority-commit-recovery.md)을 따른다.

## 0. 실행 모드와 두 가지 분할 축

NativeChainExecution은 실제 권리 변경의 확정을 체인에서 받는다. KTX의 로컬 예약/주문 의도가 chain inventory 또는 발행 완료의 증거가 되지 않는다.

DelegatedExecution은 특정 재고 집합/수량에 대해 체인과 다른 실행자가 동시에 소비하지 못하는 배타적 grant를 전제로 한다. grant/회수/미발행 약정/비협조 처리까지 검증하기 전 비활성이다. 운영자 서명이나 Raft 복제를 독립 검증자의 비잔틴 합의와 동일시하지 않는다.

오프체인 KTX는 행·실제 연속 구간의 writer를 core-local shard로 묶을 수 있다. 이것은 온체인 지정석을 한 행 mutable object로 합치라는 뜻이 아니다. 논리적 구간, CPU 실행 단위, 복제 단위, 온체인 object 단위는 서로 다르다.

공통 목표는 독립 거래가 불필요하게 같은 mutable object를 건드리지 않는 것이다. 직렬화가 필요한 자원의 권한·원자성을 없애서 병렬화하지 않는다.

## 1. 목표 구조

```text
Immutable ShowConfig
   |
   +-- exact ShowControl identity (current cancellation/epoch authority)
   +-- InventoryCell / InventoryShard[N]
   |      +-- independent reservation/version state
   +-- Right(ticket): holder-owned independent object
   +-- SaleIntent: independent per-sale mutable object
   |      +-- PaymentEvidence: exact payment/commitment binding
   |      +-- terminal EXECUTED xor CANCELLED fence
   +-- AdmissionEpochConfig
          +-- AdmissionShard[0..N]: local nullifier/spend state

Immutable VerifierConfig / Policy commitments
Optional exclusive inventory grant: disabled until verified implementation
```

## 2. ShowConfig / ShowControl

ShowConfig에는 show id, organizer authority, 정확한 ShowControl id, immutable policy/version commitments, schedule/config 등 거래마다 바뀌지 않는 정보를 둔다. show-wide counters, payment refs, nullifiers, notes를 넣지 않는다.

취소 영향을 받는 거래는 정확한 권위 ShowControl의 현재 cancelled/epoch를 검사한다. 일반 거래는 control을 mutate하지 않는다. 새 immutable epoch commitment를 게시한 사실만으로 옛 epoch를 거절할 수 있다고 간주하지 않는다. 요청자가 control id를 대체하거나 생략하는 경로를 거절한다.

## 3. Inventory

- 온체인 지정석: 한 좌석당 독립 InventoryCell 또는 동등한 단일-seat 경쟁 단위. 여러 인기 좌석을 일반 mutable shard로 묶지 않는다.
- GA: fixed-capacity InventoryShard, 생성 시 합계와 immutable total의 일치.
- Order는 실제 필요한 자원만 touch한다. shard 수와 분할 크기는 검증/측정 대상이다.
- 주문의 권위 source identity와 chain inventory identity를 exact bind한다. PostgreSQL projection의 행 존재만으로 결합을 인증하지 않는다.
- grant 회수는 신규 약정 중단 source cut, 기존 미발행 약정 보존, 검증된 미사용 잔량 반환 순서를 갖는다. timeout만으로 재고를 재부여하지 않는다.

## 4. Right

공개 권리는 independent owned object를 기본으로 한다. Right 자체 또는 좁은 연계 object에 generation/version/policy commitment를 결합한다. stale generation 거절을 유지하되 show-wide generation vector에 의존하지 않는다. 실제 발행/이전 완료는 verified chain execution으로만 판정한다.

## 5. SaleIntent

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

필요한 shared object는 그 sale 하나로 범위를 제한한다. terminal 이후 SaleIntent/PaymentEvidence를 재사용하지 못한다. 한 거래 실패를 보상하려고 cancel_show를 사용하지 않는다. 핵심은 `EXECUTED xor CANCELLED`다.

## 6. PaymentEvidence

show vector에 payment_ref를 쌓지 않고 payment/order/sale별 독립 identity를 사용한다. 실제 provider fact와 on-chain commitment는 다른 사실이다. PaymentEvidence 생성 자체가 PG/은행 자금 이동을 증명하는 것은 아니다. 동일 evidence가 서로 양립할 수 없는 두 SaleIntent에 소비되지 않도록 binding/fence를 둔다.

구체 ownership/immutability는 KTX-R2/R3의 명령·결제 정체성과 Sui primitive 검증 후 확정한다. 외부 요청의 오래된 성공 관측은 원래 binding으로 보존하되 새 권리를 임의 부활시키지 않는다.

## 7. Admission / nullifier

global notes/nullifiers/spent_challenges vector를 production에 사용하지 않는다. AdmissionEpochConfig는 가능한 immutable로, 소비 상태는 `(showId, admissionEpoch, shard)` 단위로 분리한다. 동일 spend가 동일 shard와 경쟁하도록 deterministic routing을 정의한다.

root-based privacy는 root epoch/history와 shard-local commitment를 함께 설계해 무관한 티켓 변화로 모든 proof가 stale해지는 범위를 줄인다. proof 검증·현재성·nullifier 소비가 권한 전제인 거래에서는 이를 후행 분석으로 옮기지 않는다. 회로와 실제 처리량을 함께 검증한다.

## 8. 취소 완료의 분리

KTX의 취소 barrier는 authority-placement version에 결합한다. shard 이동/분할/새 owner는 pending cancellation을 상속해야 한다. A/B만 완료하고 C의 신규 writer를 빠뜨리는 경로를 금지한다. 단절된 권위를 증명 가능하게 차단하지 못하면 전체 완료로 표시하지 않는다.

취소 요청 기록, 신규 명령 차단, 체인 fence 확인, 기존 외부 작업 대사, 환불 이행 완료를 구분한다. R1 `cancel_scope`는 로컬 상태 전이일 뿐 이 전체 barrier나 실제 Move 취소가 아니다.

## 9. 구현 종료 시험

1. 독립 seat sale/resale가 불필요한 mutable show/sale object를 공유하지 않는다.
2. one-sale failure가 show-wide compensation fence를 요구하지 않는다.
3. admission shard A의 spend가 무관한 shard B의 mutable object를 요구하지 않는다.
4. shard count별 contention/latency를 실제로 측정한다.
5. chain identity와 KIX-BCS1 Order/Sale/Payment commitments를 정확히 결합하고 Rust↔Move golden을 검증한다.
6. 취소 완료 후 구 epoch를 거절한다. control id 대체/누락·취소 경합·authority 이동을 시험한다.
7. `[1,2]`와 `[2,3]` 연석 경쟁은 중복 배정/묶음 부분 성공을 허용하지 않는다. 로컬 writer, durable commit, 결제 관측, chain execution 각각의 보장을 구분한다.
8. GA 재발급은 원래 queue position을 보존하며 구/신 token 동시 소비가 capacity를 중복 차감하지 못한다.
9. 위임 재고는 동시에 native 경로나 다른 실행자에서 소비되지 않는다. 회수 도중 미발행 약정이 사라지지 않는다. 비협조 복구를 시험한다.

기존 shared-Show Move는 역사적 fixture로 보존하며 production API에서 import/호출하는 경로를 만들지 않는다.
