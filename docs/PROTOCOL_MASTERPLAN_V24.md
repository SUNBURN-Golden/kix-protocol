# KIX 개발계획 2.4 — KTX 실행·저장·장애 격리 재설계

작성일 2026-09-15. 기준 S07-A `98d5f6372b68f875bcb2b670c5998697ecfb76c1`.

## 결정

기존에 검증한 경제 기능과 안전 보장을 Rust 운영 구현으로 재구축하고, 없었던 영속 모델을 함께 구현한다. 언어만 번역하거나 PostgreSQL 앞에 캐시를 붙이는 변경이 아니다. Rust 타입·KIX-BCS1·FeatureIR/의미론·기존 보안/장애 회귀는 보존한다. Python/Node/SQLite는 historical fixture이며 production 거래를 완료하는 실행 의존성이 될 수 없다. Move는 유지하되 production 객체는 별도 구현한다.

실행·정본·저장 계약의 우선순위는 [ADR-0001](adr/0001-ktx-authority-commit-recovery.md) → `runtime/ARCHITECTURE.toml` v6 → 이 계획이다. 2.3의 PostgreSQL-only 정본과 S07-B 선행 순서는 역사적 비교 기준으로 남긴다. 기존 하위 문서의 타입/계산/보안 조건은 보존하되 PostgreSQL-only 권한 가정은 ADR이 대체한다.

## 실제 완료와 목표를 분리

| 대상 | 상태 |
|---|---|
| S07-A BCS 코덱·고정 vector | 보존. 기존 bytes/hash 변경 없음 |
| Cargo.lock / locked CI | R0/R1에서 완료. 의존성 해석 고정이며 전체 바이너리 재현성과 구별 |
| 기본 schema 등록 | R2-A에서 Genesis/Command/Result 등록·sealed 진입점·고정 vector 구현. 전체 상태 snapshot schema와 운영 거버넌스는 후속 |
| KTX-R0 권한·커밋·복구 계약 | 이 변경에서 작성 |
| KTX-R1 단일 shard Rust 커널 | 이 변경에서 구현. 메모리 내 전이/회귀만 |
| 로컬 journal / 전체 로그 재생 | R2-A에서 file sync·길이/체크섬 검증·실제 프로세스 종료 후 재시작 시험 구현 |
| replicated log/quorum ACK/state snapshot | 미구현, R2-B |
| 실제 PG·은행·Sui 운영 어댑터 | 미구현, R3/R5 |
| 성능 하한·처리량 우위 | 미측정. CI 성공으로 승계하지 않음 |

## 권한과 확정성

DelegatedExecution은 사전의 검증 가능한 배타적 재고 위임을 전제로 KTX가 예약·판매 약정을 확정하는 목표다. 위임/회수/비협조 검증 전에는 비활성이다. NativeChainExecution의 실제 권리 변경은 체인이 확정한다. KTX 예약 성공과 체인 발행 완료는 다른 상태다. Raft는 체인의 독립 비잔틴 합의를 대체한다고 간주하지 않는다.

동일 재고에는 한 권위 writer만 둔다. PostgreSQL은 KTX 범위의 projection/control metadata 후보이며, SQL 정본 비교는 분리된 시험 재고에서 수행한다. 내부 원장이 승인 조건인 거래는 그 원장 예약을 기다린다. 후행 회계 projection과 혼동하지 않는다.

## 새 순서와 종료 조건

### KTX-R0 — 계약

CommandIdentity와 ExecutionFence/BusinessFence/ReplayVersion 분리. 커밋/ACK·위임 회수·취소 placement barrier·외부 UNKNOWN·이관·export 경계 명세. 기존 검사를 지우지 않고 v5로 교체한다.

### KTX-R1 — 순수 커널

실제 구간/GA 재고, 최소 주문, 견적/정책/자산 binding, stable external intent, 최초 결과, 지연/상충 capture의 메모리 내 전이. 동일 키 변조·연석 중복·word/통로 경계·UNKNOWN 만료·권한 이동 후 재시도·늦은 관측을 실제 Rust 테스트로 검증한다. 외부 입력 인증·지속 저장·네트워크·성과 수치는 포함하지 않는다.

### KTX-R2 — 내구성 있는 실행 기반

명령/상태 schema 등록과 고정 vector, 버전별 재생. 로그·hard-state·fsync·ACK 순서를 구현하고 성숙한 consensus 라이브러리를 통합한다. ACK 직후 crash, 응답 유실, torn writes, snapshot install, compaction, membership, old writer, dedupe retention을 실제 프로세스/저장장치 이력으로 검사한다. 원장/예약/최초 결과/outbox intent의 같은 커밋을 입증한다. SQL 정본 비교용 backend는 다른 시험 자원만 사용한다.

R2-A는 등록된 Genesis/Command/Result와 단일 호스트 local journal 검증 경로다. `LocalReceipt`는 파일 동기화 후의 로컬 결과이며 quorum ACK가 아니다. 완전한 미응답 명령은 재시작에서 채택될 수 있고, 잘린 로그는 자동 복구/절단하지 않고 거절한다. 완전한 과거 prefix로의 rollback은 독립 checkpoint 없이 탐지할 수 없다. 커널의 실제 상태 snapshot, compaction, Raft membership/leader/majority 장애 이력 및 production ACK는 R2-B 종료조건으로 유지한다.

### KTX-R3 — 경제 경로의 재구축과 확장

인증된 AssetRegistryVersion/PolicyVersion. Order/OrderLine/QuoteSnapshot, 여러 PaymentIntent와 event/operation dedupe, PaymentAllocation, IssuanceOutcome, Obligation, RefundReservation/Execution. provider 계약별 멱등성 보존기간·UNKNOWN 대사·늦은 성공·과다 입금·부분 지급·다중 자산. 첫 R1의 한 capture/양수 결제 제한은 구현 범위일 뿐 최종 상품 제한이 아니다. 실제 제공자 인증/자금 계약은 모의 실행과 별도 승인한다.

### KTX-R4 — 높은 플로어를 위한 자원 격리

waiting/active/evidence 상태 분리. bounded queues와 byte/age/outstanding 상한. 신규 claim과 completion/expiry/cancel/recovery 예산. provider별 backpressure, stale-view invalidation, cell isolation. open-loop 부하와 원시 histogram, 성공/거절/대기/복구를 따로 기록한다.

### KTX-R5 — 체인·복합 거래·프라이버시

실제 위임/회수/중복 소비 방지 또는 native chain 확정. 독립 Right/SaleIntent/PaymentEvidence, 지정석 cells/GA quota, 취소 currentness와 placement barrier. cross-shard durable coordinator; 쿠폰/한도/잔액 등 비좌석 자원도 포함. private proof/nullifier를 권한 경계에서 검증한다. Rust↔Move production schema golden을 추가한다.

### KTX-R6 — 측정 기반 최적화

같은 정합성/내구성/실패 모델에서 성능을 비교한다. low-load batch delay, hotspot, snapshot/catchup, provider outage, ACK loss, cross-shard 장애 시 floor와 ceiling을 모두 평가한다. core pinning/NUMA/io_uring/DPDK/GPU는 허용하되 안전 검증을 끄는 최적화는 금지한다.

## 기존 단계와의 관계

S07-A 자산은 유지한다. S07-B의 영속 주문/결제 범위는 R2/R3로, S07-C는 R2/R3의 외부 실행·의무·복구로, S07-D는 source-consistent export + 별도 CPU 의미론으로 재배치한다. S08/S09는 R5다. AI/GPU/금융 확장은 삭제하지 않으며 core의 동기 의존성으로 넣지 않는다.

각 기능별로 legacy 의미/새 구현/새 장애시험/미구현 범위를 표시한다. crate 수나 legacy CI 성공을 전환 완료로 계산하지 않는다. 전체 상태 JSON·SQLite 파일 배치·옛 직렬화의 구현 제약은 이관하지 않는다.

## 별도 미완료

역사적 저장 유실 원인, 호스트/지역 상실 복구, 운영 ZK 설정/키 이관, 독립 checkpoint 검증, 실 PG/은행 계약, 브랜치 보호 권한/요금제, production schema 거버넌스. 이 계획 개정이나 R1 통과가 해당 항목을 완료시키지 않는다.
