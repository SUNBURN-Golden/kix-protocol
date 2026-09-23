# Sui/Move 권리 토큰화 설계

공통 명칭·체인/원장/은행 간 순서와 권위는 [CROSS_BOUNDARY_CONTRACTS](CROSS_BOUNDARY_CONTRACTS.md)를 함께 따른다. 본문 논리 상태와 토큰 표현을 별도 경제 자산으로 중복 계상하지 않는다.
기준: `BeautifulMind-JT/kix-protocol` main `6dbf8dfed6ee790e2ee56b49a75b727edd9db977`. 검토일 2026-09-22. 본문 객체명·전이는 **설계 제안**이며 구현/배포 완료가 아니다. 제품 코드 변경·체인 제출 없음. backend 미정, R2/자체 복제·저장·로그 착수 금지와 잠금 커널은 유지한다.

## 1. 그림의 의미를 실제 책임으로 풀기

Sui는 그림 아래의 단순 영수증 보관소가 아니라, 승인된 모델 1에서 **재고 원권위·관람권 발행/소유/이전/소비의 권위**다. Rust는 검증된 배타 grant 안의 예약·주문·금전 의무와 외부 작업을 담당한다. 운영 플랫폼은 그 프로토콜의 클라이언트다.

반대로 KRW 은행 자금, 주최자의 실제 공연 이행, 오프체인 채권의 법률상 성립·대항력·회수 가능성을 Sui가 자동 보증하지 않는다. 이 영역의 인증된 사실과 계약을 등록·대조하고, 온체인에서 약정된 통제만 집행한다.

이 구분은 새 원칙이 아니라 현재 `docs/decisions/AUTHORITY_MODEL_1.md`, `docs/DEVELOPMENT_PLAN.md §§3,11,12,14`와 일치한다. 예약확정·결제관측·권리발행·차주선지급·투자자상환은 독립 상태다.

## 2. 제안 패키지와 객체 모델

패키지는 아래 논리 경계다. 당장 7개 별도 배포 패키지로 고정하지 않는다. 외부 API와 데이터 계약을 먼저 고정하고, 타입순환·업그레이드 영향에 따라 배포 단위를 확정한다.

| 논리 모듈 | 제안 객체/데이터 | ownership / 동시성 | 필수 결합 |
|---|---|---|---|
| identity/config | `ShowConfig`, `PolicySnapshot`, `AssetSnapshot` | immutable; 변경은 새 버전 발급 | chain/network/package origin, show, 정확한 control id, policy/hash, asset/version |
| show control | `ShowControl` | show별 shared, 평상시 read-only; 취소/권한전환만 mutate | 현재 sale/cancel generation, pause 범위, 허용 package/object version |
| inventory | `SeatCell` | 좌석별 독립 경쟁 단위, 필요한 좌석만 mutate | config, seat identity, delegation generation, issued Right |
| inventory | `GaQuotaShard` | 고정 할당량 shard별 shared | immutable total 대비 합계보존, grant, shard-generation, 발행/반환 누계 |
| delegation | `GrantControl`, `ExecutorAuthority` | grant별 currentness/control; 가능한 read-only 확인 | 위임 범위·행위·수임자·시간원·generation·회수 cut/proof |
| rights | `AdmissionRight` | 개별 사용자 소유; 정책상 제한된 transfer API | show/control, inventory origin, right generation, policy, issued operation |
| sale | `SaleIntent` | 판매 건별 독립 shared escrow; 티켓을 잠그거나 모듈이 통제하는 escrow에 보관 | seller, exact Right, buyer 제한, quote/asset, expiry, terminal executed XOR cancelled |
| payment evidence | `PaymentAttestation`, `EvidenceUse` | operation별 독립 기록/소비상태 | provider/MID/environment/API, operation, amount, recipient, Order/Sale, 발행자·증거버전 |
| admission | `AdmissionConfig`, `NullifierShard` | config immutable, spend shard별 mutate | current control, proof/verifier version, routing identity, 소비 generation |
| settlement | `SettlementBatchCommitment`, `SettlementClaim` | batch 증거 immutable; claim별 상태 | 자산, 수취인, 정확한 배분원천, source cut, bank operation, 정정전표 |
| finance | `ReceivablePosition`, `Encumbrance`, `FacilityPosition` | 동일 채권 부담은 동일 canonical position에서 직렬화 | 채권원천·권리자·의무자·순위·배정액·계약/증거·facility |
| governance | `UpgradeCap`, scope별 관리 capability | 일반 실행 키와 분리, 승인 정책으로 custody | 서명정책, package digest, object version, 승인/활성 경계 |

**전역 mutable Show에 주문·결제·nullifier·정산·대출 counter를 모두 넣지 않는다.** per-seat/GA shard/grant/claim별로 실제 공유 자원만 경합시킨다. shared parent 아래 dynamic field를 나눴다는 사실만으로 parent 경합이 없어지지 않는다. Sui 공식 local-fee 문서도 하나의 shared object write가 직렬화·유예·혼잡 취소를 일으킨다고 설명한다. [Sui local fee markets](https://docs.sui.io/develop/transaction-payment/local-fee-markets)

`ShowControl`을 각 거래가 정확히 read-only로 확인하는 것은 show-wide write counter와 다르다. 그럼에도 취소 write와 거래 read의 순서·네트워크 비용은 실측 대상이다. 공통 control을 삭제해서 성능을 높인 것으로 보고하지 않는다.

## 3. AdmissionRight를 만들 때 피해야 할 우회

판매가격 상한·공식 리셀·취소 현재성·양도 정책을 Move가 강제하려면 일반 `public_transfer`로 우회할 수 없어야 한다. 초기 제안은 `AdmissionRight`를 **key-only**로 두고 defining module의 승인된 transfer/sale/recovery 함수만 허용하는 것이다. `key + store`를 주는 순간 외부 모듈의 public transfer가 열릴 수 있으므로 제품 정책과 타입 능력을 같이 검토한다. [Sui transfer framework](https://docs.sui.io/references/framework/sui_sui/transfer), [Custom receiving rules](https://docs.sui.io/develop/objects/transfers/transfer-to-object)

다만 key-only는 그 자체로 관리자 임의 회수 기능을 제공하지 않는다. 소유자가 티켓 객체를 제출하지 않아도 긴급 무효화/재발급이 필요하면, 정확한 Right id에 결합한 좁은 `RightControl`(current generation/revocation) 또는 사전에 합의한 custody/recovery 구조가 추가로 필요하다. 어떤 경로도 옛 티켓과 재발급 티켓을 동시에 유효하게 두지 않는다. 이 선택은 최초 배포 전에 닫아야 하며 “업그레이드하면 해결”로 미룰 수 없다.

판매자는 SaleIntent escrow 생성 시 Right를 묶는다. 한 Right로 두 판매 intent를 동시에 활성화하지 않는다. 실행은 payment evidence 검증·소비와 티켓 이전을 하나의 Sui PTB에 넣는다. 취소와 실행은 동일 SaleIntent terminal state를 두고 경쟁한다. 단, PG 승인/은행 지급은 이 PTB 안에 들어가지 않으므로 별도의 보상·환불 의무 상태가 필요하다.

## 4. 원재고·배타 위임과 회수

### 권위 보존식

- 지정석: 한 `SeatCell`은 한 시점에 free / delegated(grant,generation) / issued(right) / retired 중 하나의 canonical 상태.
- GA: 총수량 = free quotas + delegated-but-unissued quotas + issued active rights + 정책상 retired/consumed 영역. 반환/재발급을 어떤 항에 반영할지 상태전이별 정한다. 이동 전후 합계가 같아야 한다.
- 오프체인 보유 예약은 delegated 영역 내부의 추가 사실이다. onchain 미발행은 오프체인 미판매를 뜻하지 않는다.
- native execution은 delegated 영역을 동시에 소비할 수 없다. 다른 실행자로 재위임할 때도 미발행 약정을 먼저 보존한다.

### 최소 grant 계약

`grant_id, chain_id, package_origin, exact_inventory_scope, capacity, grantee, allowed_actions, grant_generation, execution_generation, business_epoch, valid_from, valid_until, time_source, config/policy commitments`.

세 generation을 합치지 않는다. owner 이동이 stable command ID를 바꾸면 안 된다. 발행 과정이 매번 하나의 mutable GrantControl counter를 건드리면 위임 성능이 global counter로 돌아가므로, control은 read-only currentness 확인, 실제 quota는 권한이 분할된 inventory/shard에서 소비한다.

체인 발행 명령에는 `grant + reservation/command identity + quote/payment binding + issuance nonce`를 결합한다. 동일 명령을 새 Sui 거래 bytes로 재작성해도 Right가 두 개 생기지 않도록 **canonical issuance key의 온체인 사용 기록**이 필요하다. 단순히 매 호출에서 새 UID를 만들거나 “Sui digest는 멱등적”이라고 하는 것으로 충분하지 않다. 사용 기록은 권위가 있는 shard에서 경쟁하며 보존/회수 계약과 결합한다.

### 회수 단계

1. 회수 의사를 내구 기록하고 영향 grant/generation을 확정한다.
2. 새 약정/서명의 차단 cut `C_g`를 세우고 실제 실행 권한을 fencing한다.
3. 체인 경계 `H_g`에서 grant 신규 소비를 차단한다. 과거 서명/제출된 거래의 결과는 따로 대사한다.
4. `C_g` 이전에 확정된 미발행 약정·늦은 capture·발행 대기·반환 의무를 enumerated commitment와 custody 증거로 보존한다.
5. 검증된 미사용 잔량만 회수·재위임한다. 종료 manifest는 원장 source cut과 체인 effects/checkpoint를 각각 가리킨다.
6. 비협조/증거 유실이면 영향 재고를 hold한다. 시간 경과만으로 전량 회수하지 않는다. 분쟁·준비금·보상으로 종료하는 별도 계약과 지정 승인 없이는 재판매 금지.

**잔여 미결:** 비협조 시 모든 약정의 독립 가용성을 무엇이 보장하는지는 아직 구현/제품 계약으로 닫히지 않았다. 인증된 archive/공동 custody/공개 commitment와 조회 증거 등을 평가해야 하며, 이 문서가 그 불확실성을 해소했다고 표시하지 않는다.

## 5. 지정석·GA·연석·묶음

- 좌석별 onchain 경쟁과 Rust row/segment 실행 단위는 서로 다르다.
- 동일 트랜잭션에 들어갈 수 있는 연석/작은 bundle은 필요한 SeatCell을 **하나의 PTB**에서 검사·소비하여 체인상의 부분 성공을 막는다. [Sui PTB](https://docs.sui.io/develop/transactions/ptbs/)
- `[1,2]`와 `[2,3]` 경쟁에서 좌석 2는 한쪽만 소비한다. 한쪽을 개별 티켓 발행 여러 건으로 분해하면 all-or-none 보장이 깨지므로 그렇게 처리하지 않는다.
- 프로토콜 한도보다 큰 bundle은 사전에 상한으로 거절하거나 별도 staging/prepare/finalize 계약을 설계한다. 여러 PTB를 “하나의 원자 거래”로 부르지 않는다.
- GA shard 이동·재발급은 quota를 보존하며 구 token과 새 token의 동시 소비를 차단한다. queue position과 권위 generation은 분리한다.
- 여러 shard의 Rust 예약/결제/체인 발행은 한 distributed ACID가 아니다. 승인된 commit/compensation 상태를 각각 보여준다. 무료 티켓도 동일한 inventory/issuance 중복 방지를 거치되 가짜 PaymentCapture를 만들지 않는다.

## 6. 취소·현재성·검표

모든 취소 민감 함수(issue, transfer/resale, admission, 새로운 담보 등록 중 취소위험이 관련되는 함수)는 ShowConfig가 고정한 **정확한** ShowControl을 요구하고 current cancellation generation을 검사한다. 호출자가 대체 control을 제출하거나 생략할 수 없다. 새 immutable epoch 문서 게시만으로 옛 증명을 무효화하지 않는다.

체인 이전에 offchain 취소 barrier를 세울 때는 authority-placement version을 함께 고정한다. 이동·분할 중 새 owner는 pending cancellation을 상속한다. UI는 최소:
`요청 접수 → 신규 실행 차단 → 체인 취소 확인 → 과거 외부 작업 대사 → 환불 의무 이행`.
앞 단계 완료를 뒤 단계 완료로 표시하지 않는다.

검표는 current right/control 확인, proof 검증, 동일 사용에 대한 nullifier 소비를 같은 권위 경계에서 처리한다. nullifier deterministic routing을 고정해 같은 증명을 shard만 바꿔 재사용할 수 없게 한다. private admission의 회로/키 버전·root history·proof currentness는 실제 운영 ZK 감사 항목이다.

오프라인 검표와 실시간 전역 중복 거절/취소 보장은 동시에 당연히 얻어지지 않는다. 오프라인 모드는 별도 제한된 운영 프로파일(미리 배타 배정된 입장 자원, 위험 한도, 동기화/분쟁)로만 설계한다. 온라인 보장을 그대로 승계하지 않는다.

## 7. Sui signer·gas·원거래 인계

체인 어댑터는 전송 전에 원래 TransactionData/signed bytes/digest, 전체 owned 입력의 id/version/digest, shared 입력과 mode, gas 모든 입력 또는 address-balance 모드, expiry, stable operation, 현재 발행 허가를 내구 기록한다.

- 같은 입력 버전에 서로 다른 업무 의도를 두 signer가 생성하지 못하도록 실제 서명 키 사용 경계를 통제한다. DB writer 변경만으로 이미 배포된 개인키가 무효화되지 않는다.
- logical signer authority 하나는 물리 단일 프로세스와 다르다. 대기 복구자는 원 bytes와 미확정 입력을 인계받고, 현재 권한을 검증한 뒤 조회/동일원거래 재송신을 수행한다.
- `NotFound`/timeout은 미실행 확정이 아니다. 거래가 최종적으로 실패했더라도 gas/effects 변화를 반영해야 한다.
- wallet/backend/sponsor가 동일 gas pool을 독립적으로 선택하지 않도록 입력 소유권을 나눈다. address-balance gas는 대상 네트워크/SDK의 실제 지원과 한계를 검증한 별도 프로파일로만 사용한다.
- 일반 거래 재송신이 체인에서 at-most-once인 것과 회수 cut 이후 그 거래를 재송신할 업무 권한이 있는 것은 다르다.
- Sui SDK executor는 로컬 queue·input/gas 관리 도구이지 여러 host의 서명 fencing·미확정 인계 전체를 제공한다고 주장하지 않는다. [Mysten executor docs](https://sdk.mystenlabs.com/sui/executors)

### 공식 자료의 버전 충돌

이번 조회에서도 ownership/versioning 문서는 owned fastpath가 consensus를 우회한다고 설명하지만 transaction lifecycle은 **모든 거래가 consensus sequencing**된다고 설명한다. 저장소 조사도 고정 release 소스와 문서의 이 불일치를 기록했다. “owned이므로 무조건 빠름” 또는 “충돌하면 무조건 다음 epoch까지 정지”를 현행 성능/복구 보장으로 사용하지 않는다. 실제 network/protocol/SDK/gas 설정과 고정 source를 대조하고 통합 시험으로 확정한다. [Lifecycle](https://docs.sui.io/develop/transactions/transaction-lifecycle), [Object versioning](https://docs.sui.io/develop/objects/versioning), [KIX 조사 문서](https://github.com/BeautifulMind-JT/kix-protocol/blob/6dbf8dfed6ee790e2ee56b49a75b727edd9db977/docs/research/SUI_EQUIVOCATION_REPLICATION_RESEARCH_5440de0cf721.md)

사용자 UX의 `CHAIN_FINALIZED`는 성공 effects 검증과 정확한 발행/이전 대상 결합을 요구한다. 단순 digest 존재·indexer row 존재는 부족하다. 두 독립 클라이언트가 동일 검증 계약을 사용한다. 운영 초기 trusted RPC를 채택한다면 그 신뢰를 명시하며, quorum/checkpoint 검증을 구현하지 않고 trustless client라고 부르지 않는다. [Sui finality](https://docs.sui.io/develop/transactions/transaction-lifecycle)

## 8. 여신·정산 연결에서 반드시 분리할 토큰/사실

| 대상 | 의미 | 금지할 오인 |
|---|---|---|
| AdmissionRight | 관람·양도·검표에 쓰는 권리 | 주최자의 대출채권 또는 투자자 수익증권과 동일 취급 |
| SettlementClaim | 인증된 배분 원천에 결합된 정산청구/미지급금 | 아직 입금되지 않은 돈을 현금잔고로 간주 |
| ReceivablePosition | 특정 의무자·권리자·금액·기한·조건의 채권 기록 | token mint가 채권 법적 성립·우선순위·회수능력까지 보증 |
| Encumbrance | 특정 facility가 점유한 채권범위/순위/액수 | KIX 밖 이중양도·이중담보까지 자동 탐지 |
| FacilityPosition | 자금약정, 인출, 원리금·수수료·한도·연체·변제 상태 | 실제 은행 인출·상환 전에 서명/commitment만으로 돈 이동 인정 |
| CapitalInterest | 필요시 자본 공급자 몫/배분참여 기록 | 자유양도 토큰 발행 자체가 허가된 금융상품이라는 주장 |

본 제안의 1차 금융 구조는 실제 정산 원천에 결합한 제한된 자금공급/선지급과 채권 부담 관리다. 공개 투자토큰·DEX 유동성·KIX 토큰은 자동 선행 조건도 자동 승인 범위도 아니다.

같은 receivable의 담보/양도 등록은 canonical source identity와 **한 권위의 encumbrance 상태**를 변경한다. 동일 잔여액을 두 facility가 동시에 담보로 잡지 못하도록 원자적으로 검사한다. 부분담보·순위·한도·분배 합계를 보존하며 split child를 새 무부담 채권처럼 다시 발급하지 못한다.

고객 환불·차지백·취소가 발생하면 정산 원천/담보 적격성/borrowing base를 재평가하고 신규 인출 또는 수익배분을 해당 범위에서 차단한다. **담보권자의 지급 순서를 임의로 소비자 환불보다 높게 하거나 낮게 확정하지 않는다.** 법적·계약상 우선순위와 실제 자금통제 계약을 제품별 waterfall로 고정해야 한다.

마케팅 쿠폰·스폰서 보전액도 할인 계산만으로 현금 또는 적격채권이 되지 않는다. 약정의 당사자·실제 지급/청구 가능성·중복 청구 여부를 별도로 검증한다.

## 9. KRW 사실을 체인에 넣는 신뢰 경계

### 여신도 단순 해시 기록으로 끝내지 않는 실행 범위

아래는 **온체인 상태전이의 제안**이다. 법적 상품/양도 요건이 확정되지 않은 기록을 먼저 자유유통 금융토큰으로 만들지 않는다. 계약에 어떤 효력을 부여할지는 해당 금융상품의 승인 문서와 외부 법률·수탁·지급 계약이 정한다.

| 타입/명령 | Move가 실제로 강제할 것 | 외부 전제/신뢰 |
|---|---|---|
| AdmissionRight mint/transfer/check-in/revoke | 유일 발행·현재 소유/세대·정책상 이전·한번 소비·취소 상태 | 실제 공연 제공·사용자 신원/회복 정책 |
| ReceivablePosition issue/split/assign | 인증된 origin position과의 결합, 총 청구액 보존, 같은 원천 중복 토큰화 거절, 허용 양도자 | 해당 채권의 존재/적격성/양도효력·외부부담 검증 |
| FacilityPosition activate/draw/repay/default | 약정버전·한도·현재 채무·인출 승인·상환 적용의 중복방지 | 자본약정·은행 자금수령·이자/연체 및 실제 지급 계약 |
| CapitalInterest issue/transfer/redeem | investor별 배정지분·전달조건·발행/소각 및 상환배분 총량 | 참여자 자격·양도 허용범위·상품 계약 확정 |
| Encumbrance create/amend/release | 같은 원천잔여액을 중복 사용 못함, 담보잡힌 부분의 처분·분할·부담변경 통제, 상환 뒤에도 정확한 해제증거/승인 필요 | 법적 순위와 KIX 밖의 부담, 집행/도산 효력 |
| BankInstructionAuthorization create/consume | 정확한 수취인·자산·금액·facility/obligation·operation에 묶인 1회 사용 권한; 재사용 불가 | 실제 송금·중복방지·대사 계약은 은행 어댑터 책임 |

BankInstructionAuthorization 소비/소각은 **한 번의 송금 의도를 승인했다**는 상태다. 실제 이체 완료 표시가 아니다. 소비 결과는 stable operation과 원 instruction bytes에 결합해 영속 보존하고, outbox는 같은 operation만 재송신한다. 권한을 소각했더라도 이미 전송된 은행 요청은 나중에 성공할 수 있고, 은행이 멱등성을 제공하지 않으면 체인 소각만으로 exactly-once가 생기지 않는다. consume 뒤 송금 전 장애에서도 원 의도와 미결상태를 재구성해야 한다. 결과 불명을 이유로 새 authorization과 새 bank operation을 자동 발급하지 않는다.

**주최자 채무와 관객 티켓은 분리한다.** 주최자의 선지급 연체를 이유로 이미 발행된 관객의 AdmissionRight를 대주에게 이전·소각하거나 검표를 막지 않는다. 대주의 담보대상은 명시한 정산채권/주최자 수익범위이며, 소비자 권리·환불 청구에 영향을 주는 권한은 별도 법적/상품 계약 없이 만들지 않는다.

향후 **별도 KIX 자체 토큰**(거버넌스·경제적 사용·수수료 등)을 검토한다면 관람권·채권 토큰화와 구분한 의사결정 트랙으로 다룬다. 목적·권리·공급·수익귀속·시장/규제·보안 계약을 확정한 뒤 추진하며, 이번 관람권·채권·여신 토큰화 구현의 필수 선행조건으로 삼지 않는다.

KRW의 사실정본은 PG/은행 인증 결과와 계약상 수탁/정산 책임이다. `PaymentAttestation`은 “누가 무엇을 어떤 근거로 확인했는가”를 체인에 명시하는 증거이며, 체인이 은행계좌를 직접 검증했다는 뜻이 아니다.

최소 attestation: provider+merchant/account+environment+API/product/operation kind, original operation and evidence key, exact amount/asset/recipient, observed state, event/observed times, authoritative lookup reference, evidence hash/custody pointer, issuer+key generation, payload/schema version. 동일 provider event에 복수 결제가 실릴 수 있는 경우 adapter가 canonical item identity를 정의한다. event dedupe와 economic operation dedupe는 분리한다.

원문에 개인정보·계좌·결제 비밀을 올리지 않는다. offchain 접근통제 보관과 숨김값/충분한 entropy를 포함한 commitment를 사용하며, 공개 해시만으로 작은 값/식별자의 추측 노출이 사라지는 것은 아니다.

오류 정정은 원본 삭제가 아니라 새 attestation/correction과 영향 의무의 재계산으로 남긴다. attestor 키 회수는 과거 정당한 사실을 소거하지 않고, 회수 전후 발행 권한·새 사실의 수용·재감사 대상을 나눈다. LC-TERM 운영 종결을 payment FAILED나 무부담 collateral certificate로 변환하지 않는다.

## 10. 운영 capability 및 업그레이드

역할을 최소한 OrganizerConfig, InventoryGrant, Canceller, PaymentAttestor, SettlementApprover, CreditApprover, TreasurySigner, EmergencyPauser, PackageUpgrader로 나눈다. 한 운영자/AI가 자기 수익자의 채권을 만들고 심사하고 송금하는 전권을 갖지 않는다. 통제 규칙은 제품 위험에 맞게 범위·금액·기간·승인 주체로 표현한다.

pause는 신규 위험 명령을 막되 이미 일어난 외부 사실의 수신·증거보존·대사를 계속 허용한다. 모든 키를 멈춰 늦은 결제가 사라지는 복구 방법은 금지한다. 긴급 중단과 자산이전/담보해제/환불실행은 별도 권한이다.

Sui 업그레이드는 옛 package를 삭제하지 않는다. 따라서 old entrypoint가 현재 object를 잘못 처리하지 못하도록 최초 배포부터 version guard/currentness가 필요하다. UpgradeCap custody, 승인된 bytecode digest, dependency package IDs, 새 schema/semantics, migration rehearsal, activation boundary, rollback 가능한 범위를 명시한다. [Sui upgrading packages](https://docs.sui.io/develop/publish-upgrade-packages/upgrade)

키 분실 복구는 전 계정 만능키를 두기보다 사전에 합의한 user recovery와 operator capability rotation을 나누고, 과거 signer의 새 명령을 차단한다. 복구된 operator는 먼저 read/reconcile 모드에서 grant/cut/pendingtx를 확인한다.

## 11. 구현 인수 시험 목록 — 설계 후 별도 Task

1. package/network/control ID 바꿔치기, 옛 generation/정책/schema, 권한없는 capability 거절.
2. 동일 좌석 두 구매, 겹치는 연석 [1,2]/[2,3], GA quota 경계, 재발급 구/신 token 경쟁.
3. grant/native 이중소비 거절, grant split/이동 합계보존, 회수 직전 커밋/응답유실/구 signer 지연 제출.
4. 미발행 약정을 가진 grant 회수와 비협조 시 “미사용” 오판 금지.
5. 실제 취소와 발행/리셀/검표 경쟁, stale/foreign ShowControl 거절.
6. 한 PaymentAttestation을 두 SaleIntent/issue operation에 재사용 거절; 동일 operation을 새 txbytes로 재발행 거절.
7. 결제 성공·체인 실패/UNKNOWN, 체인 성공·응답유실, 늦은 결제·취소/만료 후 반환 의무, 판매자 지급·응답유실.
8. 모든 owned input/gas 버전·원 signedbytes 인계, signer failover, 실패 tx gas/effects 대사, NotFound를 failure로 취급하지 않음.
9. reviewed/operationally closed UNKNOWN을 자동 담보적격/선지급대상으로 승격하지 않음.
10. 같은 채권의 동시 담보, split/양도 후 중복부담, 일부 상환, 차지백 후 담보평가·인출 제한, KIX 밖 미확인부담 표기.
11. 공식 취소/환불 의무와 대주 상환/주최자 잔여분 사이 waterfall 보존; 자금부족을 원장삭제/자동부활로 숨기지 않음.
12. old package 호출, unauthorized migration, capability rotation 후 구키 명령, 이전에 유효했던 지연 관측 보존.
13. private proof version/root/currentness/nullifier shard replay; 운영 ZK 설정·키 이관·회로 독립감사.
14. network loss·RPC disagreement·indexer lag 중 두 독립 클라이언트가 같은 상태/신뢰등급을 표시.
15. 좌석/GA/grant/shared control별 실제 goodput·p99·혼잡취소·gas 측정. 구조분할만으로 성능목표 달성 주장 금지.
16. 고객/주최자/자본공급자/관리자의 권한우회·자기승인·증거누락·PII 노출 검사.
17. custody/source cut와 chain proof를 포함한 복원에서 권리·은행 사실·채권 부담이 혼동되지 않는지 검증.

## 12. 기존 코드와의 경계 및 다음 설계 산출물

현재 `runtime/MOVE_PRODUCTION_TOPOLOGY.md`는 목표이고 production Move는 없다. historical `reference/v0.3-rc1`의 shared Show fixture와 제한된 실제 Sui+mock PG/bank 흐름을 운영 구현으로 재명명하지 않는다.

다음 설계 묶음:
- M-01: object/capability matrix + canonical identities + invariants.
- M-02: grant/revocation/noncooperation + cancellation matrix.
- M-03: issue/resale/return/admission state machines + atomicity boundaries.
- M-04: evidence authority + receivable/encumbrance interoperability contracts.
- M-05: pinned Sui/SDK target + Rust↔Move golden + signer/gas handoff.
- M-06: upgrade/recovery + multi-client conformance + load/fault test plan.

각 산출물은 인터페이스 단위로 Rust 경제/플랫폼/금융 작업에 연결한다. 병렬 설계는 가능하나, 현재 금지된 R2나 잠금 커널을 임의로 수정하는 작업으로 읽지 않는다.
