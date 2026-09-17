# Sui 소유 객체 equivocation과 복제 실행자 제약
## 모델 1 설계 전 사전 조사 — 객체 배치·구현·backend 선택 제외

**상태: 조사 문서.** 커널 변경, R2 개발, (a) 통합, 체인 거래 제출·rescue 실행, 전체 객체 배치 설계는 수행하지 않았다. Kiosk·zkLogin은 검토하지 않았다. 이 문서의 제안은 채택·착수 승인이 아니다.

### 검증 기준과 식별자

| 구분 | 기준 |
|---|---|
| 자료 확인 시점 `T0` | **2026-09-16~2026-09-17, Asia/Seoul(UTC+09:00)**. 본문의 `·T0`는 이 확인 구간을 뜻한다. 인터넷 시계 대조: 2026-09-17 00:08:31 KST. |
| KIX 기준 commit | `94376835ea4fc818619fc79e2be4df7d4947496a` |
| 유일한 backend 비교 정본 | `docs/DEVELOPMENT_PLAN.md §9` |
| 위 정본의 전체 Git blob | **`6efea0adcc2b1c7f4bd62c43673cc54830a8fc37`** |
| 모델 1 승인 문서 | `docs/decisions/AUTHORITY_MODEL_1.md` |
| 승인 문서의 전체 Git blob | `fec140112e11fe7403fa4fbda57d629e52a99f72` |
| 대조한 Sui 공개 Mainnet 릴리스 | `mainnet-v1.79.1`, protocol `136`; 릴리스 소스 commit `58386edc269ef88ff0f40ab0a9d50e87cba80ca8` |
| 실제 네트워크 검증 범위 | 공식 문서·변경 기록·고정 릴리스 소스의 읽기 검토. 대상 RPC의 live protocol/feature flag 조회, localnet 재현, 장애 주입, 성능 실측은 **하지 않았다**. |

KIX 기준은 모델 1, 즉 체인 원권위와 오프체인 배타 위임 실행이다. 예약 확정·결제 확인·체인 권리 발행 완료는 서로 다른 사실이며, 과거 기록의 재생이 새로운 외부 실행 허가는 아니다. 이 승인 조건은 변경하지 않는다. [K1·T0] [K2·T0]

표시를 구분한다. **[공식 문서]**는 설명 문서의 내용, **[공식 소스]**는 고정 릴리스 코드·변경 기록에서 확인한 내용, **[설계 제안/추론]**은 그 사실을 복제 실행자에 적용한 판단, **[확인 불가]**는 이번 증거로 확정할 수 없는 사항이다. 설명 문서와 코드가 충돌하면 둘을 함께 밝히며, 구형 동작을 현행 사실로 승격하지 않는다.

---

## 0. 가장 먼저 바로잡아야 하는 현행 버전 전제

**[공식 소스] 현재 공개 Mainnet 릴리스에는 소유 객체의 합의 전 잠금이 제거되어 있다. 따라서 “같은 소유 객체에 충돌 거래를 보내면 현행 Sui에서도 무조건 다음 epoch까지 동결된다”는 전제를 채택할 수 없다.** 공식 PR #24676은 잠금을 합의 전에서 합의 후로 옮겨 epoch 변경까지 잠기는 문제를 막는다고 명시한다. 후속 PR #26278은 이 변경이 Mainnet protocol v105부터 활성화됐다고 기록한다. `mainnet-v1.79.1`의 실제 `object_locks.rs`도 서명 전에는 버전·digest만 검증하고, 잠금은 합의 후에 처리한다고 명시한다. [S2·T0] [S3·T0] [S4·T0]

**[공식 문서와의 불일치]** Troubleshooting, SDK executor, Sponsored Transactions에는 여전히 epoch 잠금 경고가 남아 있다. 반면 현행 lifecycle은 모든 거래를 Mysticeti DAG가 순서화한다고 설명한다. 따라서 이 조사에서는 **과거 pre-consensus equivocation 동결**과 **현재의 동일 객체 버전 충돌·미확정 결과**를 분리한다. 이는 “Sui에서 모든 장애나 객체 대기가 사라졌다”는 주장이 아니다. [S1·T0] [S7·T0] [S12·T0] [S17·T0]

| 확인 대상 | 확인한 내용 | 이 조사에서의 사용 |
|---|---|---|
| PR #24676, 2026-01-01 병합 | pre-consensus → post-consensus locking; epoch 동결 방지, 기존 fastpath execution 비활성화 | 현행 변경의 직접 근거. **병합일을 Mainnet 활성화일로 간주하지 않음**. [S2·T0] |
| PR #26278, 2026-04-17 병합 | Mainnet protocol v105 이후 해당 잠금 비활성화가 활성 경로임을 명시 | 프로토콜 버전 기준. 정확한 Mainnet 전환 epoch·시각은 확인 불가. [S3·T0] |
| Mainnet v1.79.1 / protocol 136 | 고정 소스에 pre-consensus locking 경로 없음 | 현재 공개 릴리스 판정 기준. [S4·T0] [S5·T0] [S6·T0] |
| Troubleshooting·SDK의 epoch 경고 | 구형 설명이 계속 게시되어 있음 | 역사적 동작/문서 불일치로 표시. 현행 RTO 산정에 그대로 적용하지 않음. [S1·T0] [S12·T0] |
| Object Versioning·Shared Objects의 fastpath 우회 설명 | consensus를 우회하므로 owned가 빠르다는 설명 잔존 | 현행 owned/shared 지연 우열의 근거로 사용하지 않음. [S8·T0] [S19·T0] |

**[설계 제안/추론]** 이번 조사로 남는 핵심 제약은 “epoch 잠금을 피하는 리더 하나”보다 넓다. **동일 입력 버전에 서로 다른 업무 의도를 발행하지 않고, 구 리더가 이미 외부에 내보낸 거래의 정체성과 종결 결과를 새 리더가 이어받는 것**이다. epoch 동결 제거가 이 의무까지 없애지는 않는다.

## 1. 제약 확인

### 1-1. 발생 조건, 결과, 기간, 해제 및 rescue

#### A. 과거 방식에서의 equivocation

**[공식 문서 — 구형 방식에 한정]** 서로 다른 거래가 같은 mutable owned object의 동일 버전을 입력으로 사용하고, validator들의 예약이 서로 다른 거래로 갈라져 어느 거래도 quorum을 얻지 못하면 해당 버전이 다음 epoch까지 사용할 수 없는 상태가 된다. 단순히 다른 거래가 먼저 사용 중인 `reserved` 오류와, quorum을 만들 수 없게 갈라진 `equivocated` 상태는 다르다. quorum은 서버 대수의 과반이 아니라 epoch의 stake 가중치 기준이다. [S1·T0] [S9·T0]

객체 ID만 같다는 것으로 부족하다. **동일 버전의 경쟁 사용**이 문제다. immutable object는 이 mutable owned 잠금과 구별한다. 또한 같은 거래의 재전송과, gas·입력·만료 등 TransactionData를 바꾼 다른 거래의 제출을 구별해야 한다. [S8·T0] [S7·T0]

| 상태 | 구형 방식의 결과·해제 | 현행 공개 릴리스와의 관계 |
|---|---|---|
| 한 거래가 진행 중이고 다른 요청이 같은 버전을 요구 | 앞 거래의 종결 후 effects에 맞는 현재 참조로 후속 거래 구성 | 현재도 입력 버전 의존성은 남는다. [S1·T0] [S4·T0] |
| 잠금이 일부에만 존재하고 한 거래가 quorum에 도달할 여지가 있음 | 그 기존 거래를 완결시키는 rescue가 이론적으로 가능 | 아래 도구는 존재하나 현행 일반 복구 경로로 검증된 것은 아님. [S10·T0] [S11·T0] |
| 예약 분열로 어느 거래도 quorum을 얻을 수 없음 | 다음 epoch까지 대기 후 현재 상태 대사 | 이 **합의 전 분열에 의한 epoch 동결 메커니즘은 현행에서 제거**됨. [S1·T0] [S2·T0] [S4·T0] |

**[공식 문서 + 조건부 산술]** 과거 동결의 대기는 “발생 시각부터 고정 24시간”이 아니라 **현재 epoch의 남은 시간**이다. Mainnet/Testnet epoch가 통상 약 24시간이므로 정상적인 epoch 진행을 가정하면 대기 범위는 대략 0~24시간이다. 네트워크 장애까지 포함한 강제 상한은 아니며, **이 범위를 현행 failover 지연으로 사용하면 안 된다**. [S1·T0] [S9·T0] [S2·T0]

#### B. 현행에서 남는 제약

**[공식 소스]** 현행 릴리스는 서명 전 소유 입력의 최신 version/digest를 검사하며, 합의 후 잠금을 사용한다. 동일 객체 버전을 소비하는 서로 다른 업무 거래를 두 번 확정할 수 있다는 뜻은 아니다. 과거의 epoch 동결을 없앤 변경과, 객체 버전의 단일 소비·선형 이력 제약은 별개다. [S4·T0] [S8·T0]

**[설계 제안/추론]** 구 리더의 거래 A와 새 리더의 거래 B가 경쟁하면, 체인은 로컬 Raft가 원하는 업무 의도를 알아서 선택해 주지 않는다. A가 먼저 확정되어 B의 입력을 낡게 만들거나, 이미 끝난 A를 확인하지 않고 새 버전으로 같은 업무를 다시 만드는 문제가 남는다. 따라서 현재 조사 대상은 **불필요한 충돌·실패, 잘못된 재작성, 결과 불명 인계와 업무 멱등성**이다.

#### C. rescue: 존재와 성공 보장은 다르다

**[공식 소스]** `sui-tool`에는 `locked-object`와 `--rescue` 옵션이 있다. object ID 또는 주소의 gas 객체들을 조사하며, `GroupedObjectOutput`이 stake와 잠금 정보를 모아 `fully_locked` 여부를 판단한다. fully locked로 판단되면 재실행하지 않고 반환한다. 그 외 후보는 validator에서 거래 정보를 얻어 실행 API로 재제출하려는 구조다. **임의의 잠금을 지우는 관리 API가 아니라 기존 거래를 실행시키려는 도구**다. [S10·T0] [S11·T0]

**[설계 추론 — 구형 rescue 필요조건]** 완전하고 같은 시점의 validator 정보가 있다고 가정하자. 어떤 기존 거래 T를 지지하는 잠금 stake가 `L(T)`, 아직 다른 거래에 잠기지 않은 stake가 `U`, quorum 문턱이 `Q`라면 `L(T) + U ≥ Q`인 후보가 있어야 한다. 이것만으로 충분하지는 않다. T의 **다른 소유 입력·gas 입력도** 처리 가능하고, 거래가 여전히 유효하며, 필요한 네트워크 응답을 얻어야 한다. 무응답 validator를 자유 stake로 간주할 수 없고, 한 객체의 진단 결과만으로 다중 입력 거래의 실행 성공을 보증할 수 없다. [S9·T0] [S10·T0] [S11·T0]

**[공식 소스에서 발견한 불일치]** 대조한 릴리스의 `GroupedObjectOutput` tuple은 `.2`에 `previous_transaction`인 부모 거래 digest, `.4`에 잠금 거래 digest를 둔다. 그런데 `check_locked_object()`는 `.4`의 존재로 잠금을 확인한 뒤 재제출 대상 `tx_digest`는 `.2`에서 가져온다. **잠금 거래 대신 부모 거래를 선택하는 코드 경로가 확인된다.** 따라서 `rescueable` 출력이나 옵션의 존재만으로 실제 잠금 거래가 복구된다고 말할 수 없다. 이 경로의 운영상 영향·수정 여부·실제 성공은 **확인 불가**이며, 이번에 실행하지 않았다. [S10·T0] [S11·T0]

**[설계 제안]** rescue를 자동 복구의 성공 전제로 두지 않는다. 특히 rescue가 거래 실행을 수반할 수 있으므로, 모델 1의 회수 cut 이후에는 “예전에 서명됐고 재전송이 멱등적이다”만으로 실행을 허가해서도 안 된다. 원래 업무 의도와 현재 권한을 별도로 확인해야 한다. [K2·T0]

**해제 수단의 확인 한계:** 과거 방식에서는 거래 완결 또는 다음 epoch가 공식 설명상의 수단이다. 현행 릴리스에서 과거의 분열 동결을 임의로 조기 해제하는 일반 사용자 API는 이번 자료에서 확인하지 못했다. 프로세스 재시작, Raft term 증가, 로컬 pending 삭제를 체인상의 해제로 취급할 근거도 없다. [S1·T0] [S2·T0] [S10·T0]

### 1-2. 한 계정의 병렬 발행과 회피 도구

**[공식 자료에 따른 정정] “한 계정에서 병렬 발행하면 equivocation이 발생한다”는 무조건형 문장은 성립하지 않는다.** 같은 주소라도 충돌하지 않는 객체 입력을 사용하는 거래는 병렬 실행할 수 있다. 문제는 주소 공유 자체가 아니라 **동일 소유 입력 버전 또는 gas 입력의 재사용**이다. 과거에는 이 충돌이 epoch 동결로 이어질 수 있었고, 현행에서는 앞 절의 변경을 반영해야 한다. [S7·T0] [S8·T0] [S12·T0] [S2·T0]

| 도구·관행 | 확인된 역할 | 복제 실행자 관점의 한계 |
|---|---|---|
| `SerialTransactionExecutor` | 내부 queue, 객체 버전 cache, 순차 실행. coin 모드의 첫 거래에서 sender SUI coins를 모아 이후 재사용하는 경로. [S12·T0] | 특정 실행자 바깥의 접근까지 조정하는 분산 fencing 증거는 없음. |
| `ParallelTransactionExecutor` | 객체 ID 의존성을 감지해 충돌을 피하도록 scheduling하고 gas pool을 관리. 공식 문서상 **experimental**. [S12·T0] | 같은 `sourceCoins`를 여러 인스턴스가 사용하거나 외부 wallet이 pool을 건드리면 충돌 위험. Raft failover·durable pending 인계를 제공한다는 보장은 확인 불가. |
| 독립 입력·전용 gas pool·PTB 묶음 | 공식 오류/후원 문서에서 안내하는 회피 방향. [S1·T0] [S17·T0] | 업무 객체가 하나에 집중되면 gas만 나누어도 그 업무 객체 의존성은 남음. |
| `Sui Owned Object Pools` / SuiOOP | 과거 backend 동시 실행을 위한 worker/object pool 도구. 현재 README는 **deprecated·유지보수 중단**, Parallel executor로 이동 권고. [S13·T0] [S14·T0] | 신규 도입의 현행 기본 도구로 취급하지 않음. |

**[확인 범위]** 공식 개발 도구와 2024년 공개 안내를 통해 회피 방법이 존재함은 확인했다. “현재 커뮤니티 대부분이 owned object를 기피한다”는 비율·일반화는 **확인 불가**다. SuiOOP의 과거 문제 설명을 현재 생태계 전체의 실태로 인용하지 않는다. [S13·T0] [S14·T0]

### 1-3. gas coin, gas smashing, 기본 선택 로직

**[공식 문서] 실제 `Coin<SUI>`를 gas로 사용하는 방식에서는 gas도 버전이 있는 소유 입력이다.** 서로 다른 업무 객체를 사용하더라도 동일 gas coin 버전을 공유하면 독립 거래가 아니다. sponsored transaction에서도 sender의 입력과 sponsor의 gas 양쪽에서 충돌이 생길 수 있다. 후원 문서의 epoch 동결 문구는 §0의 현행 변경과 구분한다. [S17·T0] [S15·T0] [S2·T0]

**[공식 문서]** gas payment에 실제 coin 여러 개를 제공하면 자동으로 첫 coin에 병합되며 나머지는 삭제된다. Move 실행이 실패해도 gas 병합·차감 결과가 남을 수 있다. 따라서 “업무 실패 = gas 객체가 원래 상태”라고 간주할 수 없다. [S15·T0]

**[설계 추론]** 사용 coin 집합을 넓히는 선택은 다른 in-flight 거래와의 입력 교집합을 늘리고, 병합은 다음 병렬 실행에 쓸 독립 coin 수를 줄일 수 있다. 과거에는 동결 위험을, 현재에는 입력 충돌·낡은 참조·재구성 비용을 악화시키는 요인이다. 실패 결과까지 포함해 effects와 pool 상태를 맞춰야 한다.

**기본 로직은 도구별로 구분해야 한다.** [공식 문서] SuiOOP README의 “SDK가 모든 coin을 선택한다”는 과거 설명을 모든 현행 builder에 일반화할 수 없다. 다만 현행 Serial executor의 첫 거래, Parallel executor의 기본 `sourceCoins`, 그리고 v1.77.2 CLI 변경 기록에는 전체 가용 coin을 사용하거나 병합하는 경로가 여전히 명시되어 있다. **도구·버전·gasMode를 지정하지 않은 채 기본값이 안전하다고 가정할 수 없다.** [S13·T0] [S12·T0] [S5·T0]

**[공식 문서 — 중요한 현행 선택지] gas coin을 모든 거래가 반드시 가져야 하는 것은 아니다.** Address-balance gas payment는 빈 gas-payment 목록을 사용하여 실제 gas coin 선택·병합을 없앤다. 현재 executor 문서에도 `gasMode: 'addressBalance'`가 있다. 이 경우에도 다른 owned 업무 입력의 버전 충돌은 남는다. [S15·T0] [S16·T0] [S12·T0]

Address-balance 사용 문서는 feature flag `enable_address_balance_gas_payments` 확인을 요구한다. **KIX가 사용할 네트워크·RPC에서 실제 활성화되어 있는지는 확인 불가**다. expiration도 버전 의존적이다. 사용 문서는 `ValidDuring`을 설명하고, 최신 릴리스에는 `Validity`/`allowed_proposers` 변화가 있다. 재시도 때 nonce·expiry·gas를 새로 만들면 원거래와 정체성이 달라질 수 있으므로 원본 TransactionData를 보존해야 한다. [S16·T0] [S5·T0]

## 2. 복제 실행자와의 결합

### 2-1. 객체당 단일 서명 권한과 Raft

**[설계 제안]** “객체당 서명자 정확히 하나”는 **물리 머신 한 대 또는 키 한 벌**보다 다음의 논리적 규칙으로 해석하는 것이 정확하다.

> 하나의 소유 입력 `(network, object ID, version, digest)`에 대해 미종결 상태에서 승인하는 **서로 다른 transaction intent는 하나**다. 같은 거래를 여러 프로세스가 조회하거나, 허가된 범위에서 같은 서명 바이트를 재전송하는 것은 별개다.

Sui가 모든 애플리케이션에 이런 단일 실행자 구현을 의무화했다는 뜻은 아니다. 동일 버전 충돌을 체인에 떠넘기지 않고 KIX 업무 의도와 체인 결과를 일치시키기 위한 **애플리케이션 차원의 제안**이다. 같은 키를 가진 한 프로세스도 다른 거래 두 개를 만들 수 있고, 여러 signer가 동일 거래 하나를 승인하는 것은 서로 다른 거래에 대한 equivocation과 다르다.

Raft와 결합할 때 필요한 경계는 다음과 같다. **구현안이나 새 저장 schema를 정하는 것이 아니라, 향후 후보가 충족해야 할 증거·순서 조건**이다.

1. **외부 노출 전 확정:** 업무 operation ID, 원본 transaction bytes, 전체 소유 입력·gas 참조, 원래 grant와 실행 권한의 결합을 내구성 있는 committed intent로 만든 뒤 외부 서명·송신을 허가한다. 서명 산출물도 송신 전에 인계 가능하게 보존한다. 메모리의 전송 의도만으로는 부족하다.
2. **입력 집합 전체의 배타성:** 위임 객체만이 아니라 gas·기타 owned 입력도 같은 승인·예약 범위에서 검사한다. 여러 입력의 일부만 예약한 상태를 성공으로 공개하지 않는다.
3. **서명 권한의 실제 fencing:** 새 리더의 term을 확인하는 gate가 서명 요청의 허가를 검증한다. 구 리더가 독립적으로 raw key를 보유하고 gate를 우회할 수 있다면 로컬 리더 election만으로는 서명이 차단되지 않는다.
4. **인계 대상은 원거래:** 리더 교체 후 원래 digest·bytes·서명·관측을 복원한다. “같은 업무”라는 이유로 gas·nonce·입력 version을 새로 골라 거래를 다시 만드는 것은 동일 거래 재전송이 아니다.
5. **종결에 따른 입력 해제:** finality/확정 무효 근거를 원래 intent와 대조하고 결과를 보존한 뒤 종결·재사용을 판단한다. timeout, 단일 RPC의 NotFound, cache miss를 미실행으로 치환하지 않는다.
6. **회수 후 실행 허가 재검사:** 같은 bytes의 체인 수준 멱등성과, 회수 cut 이후 그 bytes를 다시 송신해도 되는지는 다른 판단이다. 재송신 권한이 증명되지 않으면 조회·대사만 수행한다.

1·4·5의 체인 근거는 Sui의 원거래 보존·재전송·finality 안내이고, 6은 모델 1의 승인 조건이다. **Raft 자체가 이 외부 실행 계약을 자동 제공한다는 주장은 아니다.** [S7·T0] [K2·T0] [R1·T0]

또한 **Raft term, 실행자 generation, chain lease generation, Sui object version, Sui epoch를 동일 카운터로 합치지 않는다.** 모델 1 문서가 이미 권위·커밋·회수 경계를 분리하고 있다. [K2·T0]

### 2-2. 내부 fencing만으로 충분한가

**[설계 판단] 충분하지 않다.** 내부 fencing은 구 리더의 신규 로그 확정·신규 서명 허가를 막을 수 있지만, **구 리더 또는 외부 중계자가 이미 가진 유효한 서명 거래를 체인에서 회수하는 기능은 아니다.** Sui의 결과 확인은 해당 거래의 certified effects 또는 확정 무효 근거에 대한 판단이며, 로컬 Raft의 리더 변경과 별도다. [S7·T0] [S9·T0]

다만 **“리더가 바뀔 때마다 모든 거래를 멈추고 다음 epoch를 기다린다”도 아니다.** 무엇을 다시 하려는지에 따라 다르다.

| 인계 시 확인된 상태 | 새 리더가 취할 수 있는 방향 — 설계 제안 | chain 결과를 기다려야 하는 경계 |
|---|---|---|
| 기존 거래의 확정 effects가 이미 보존됨 | 원결과를 재사용하고 effects에서 후속 참조를 얻음 | 다시 확정시킬 필요 없음. 증거와 원거래의 결합 검증은 필요. |
| 원본 서명 거래가 있으나 송신 여부/결과가 불명 | 현재 실행 허가를 확인한 뒤 조회 또는 **동일 거래** 재제출 | 다른 intent로 해당 입력을 재사용하기 전에는 종결 대사 필요. |
| 로컬 기록은 없지만 외부에 서명 거래가 나갔을 가능성이 있음 | 영향 입력을 미확정으로 격리하고 증거 대사 | “기록 없음”만으로 교체 거래 허가 불가. |
| 서명·외부 노출이 없었다는 것을 보장할 수 있음 | 복원된 권한과 최신 입력에서 새 승인 진행 | 기다릴 기존 외부 거래는 없음. 단순 cache miss는 이 증명이 아님. |
| 구 거래가 확정 실패 또는 확정 무효 | 원인과 실제 effects를 확인하고 업무상 후속 조치 결정 | 실패했다는 이유로 gas·입력 상태가 원래라고 가정하지 않음. |
| 별개의 입력·권한 범위에서 처리하는 거래 | 해당 범위의 currentness와 복원 상태가 유효하면 계속 처리 가능 | 미확정 거래와 무관한 범위까지 일괄 정지할 필연성은 없음. |

표의 체인상 사실은 **같은 거래의 at-most-once, NotFound의 비확정성, 실패 effects, 입력 버전 제약**에 근거한다. 표의 재개 정책은 KIX에 대한 설계 제안이지 Sui SDK가 제공하는 HA 보장이 아니다. [S7·T0] [S4·T0] [S15·T0]

**확정 경계도 나누어야 한다.** [공식 문서] certified effects로 settlement finality가 확인되면 매번 indexer나 별도의 checkpoint 조회 완료까지 중복 대기할 필요는 없다. 반면 조회 경로의 동기화가 늦을 수 있으므로 NotFound를 확정 실패로 사용할 수 없다. [S7·T0] [S9·T0]

**[설계 추론]** 현행에서 과거의 epoch 동결이 없어져도 A/B 충돌을 일부러 발생시켜 리더 fencing을 대신할 수는 없다. 체인에서 한 버전의 이중 소비를 막는 것과 **올바른 업무 intent만 실행되게 하는 것**은 다른 보장이다. 또한 이미 서명된 거래의 원래 입력이 무효가 되었다는 사실과, 같은 업무가 과거에 성공한 적 없다는 사실도 다르다. 새 버전으로 재구성하기 전에는 업무 결과까지 대사해야 한다.

### 2-3. 예매 가용성에 미치는 지연

**[조건부 추정 — 실측 없음]** 영향 범위의 재개 지연은 아래 항목으로 나누어 산정할 수 있다. 각 항목이 반드시 직렬인 것은 아니므로 실제 중첩은 추후 측정해야 한다.

`D ≈ 리더 장애 감지·선출 + committed 상태/서명 권한 복구 + 구 거래 결과 대사 + 필요한 후속 체인 확정`

| 상황 | 이번에 제시할 수 있는 지연 범위 |
|---|---|
| 외부 미확정 거래가 없음 | 로컬 failover·권한 복구 비용. KIX 실측이 없어 ms/초 범위는 **확인 불가**. |
| 기존 finality 증거를 새 리더가 이미 보유 | 추가 체인 합의를 기다리는 부분은 0일 수 있음. 로컬 복원·검증 시간은 별도. |
| 정상 네트워크에서 원거래가 진행 중 | 잔여 확정·관측 대기. 공식 일반 거래 finality의 전형값은 **400~700ms**이나 KIX 인계 RTO·p99·최대값이 아님. 조회 동기화 지연은 그보다 길 수 있음. [S7·T0] |
| 확정 무효 이후 별도 후속 거래가 필요한 경우 | 대사 후 필요한 거래의 확정 시간이 추가됨. 항상 한 번 또는 두 번이라는 고정 횟수는 객체 배치·업무 동작 미정으로 **확인 불가**. |
| 과거 pre-consensus 방식에서 완전 분열 동결 | 정상 epoch 진행 가정 시 잔여 epoch 약 0~24시간. **현행 공개 릴리스의 기본 가용성 추정에서 제외**. [S1·T0] [S9·T0] [S2·T0] |
| 장기 네트워크 단절·증거 접근 불가·허가 복구 불가 | 안전성을 유지하는 재개 시간의 유한 상한을 이번 자료로 보장할 수 없음. |

**[모델 1에 대한 추론]** 오프체인 예약 한 건마다 위임 객체를 체인에서 갱신한다고 가정하지 않는다. 이미 유효한 배타 위임과 복구 가능한 예약 상태가 있고 그 범위의 currentness가 유지된다면, 단지 다른 체인 거래가 미확정이라는 이유로 모든 예약을 중단할 필요는 없다. 반대로 문제의 거래가 위임 갱신·회수·재위임의 유효성 경계라면 그 범위의 **신규 약정**을 보류해야 할 수 있다. 어느 경우인지는 전체 객체 배치를 정하지 않았으므로 **확인 불가**다. [K2·T0]

수요에 대한 단순 추정식은 `영향받는 시도 수 ≈ 영향 범위의 도착률 λ × 정지 시간 D`다. 이는 유실 매출이나 전체 서비스 장애율이 아니라 **대기·재시도에 노출되는 시도 수의 조건부 산술**이다. 전체 시도 중 영향 비중을 알지 못하므로 “리더 교체 = 전 예매 중단”이나 숫자 가용률을 제시하지 않는다.

## 3. R2 추정과 4단계 backend 비교에 미치는 영향

### 3-1. 난이도 변화

**[설계 영향]** 제약을 전혀 고려하지 않은 “Raft 상태 복제 + 리더가 체인 호출” 모델에 비해서는 일이 늘어난다. 그러나 **현행에서 제거된 epoch 동결 회피를 R2의 필수 난제로 다시 넣어 비용을 부풀려서는 안 된다.** 추가되는 중심은 다음 범위다.

| 추가 검토 범위 | 제약을 무시하면 빠지는 내용 | 현행에서도 필요한가 |
|---|---|---|
| 원거래와 전체 입력의 보존 | 업무 ID만 저장하고 failover 때 새 bytes 생성 | 필요. |
| 서명 허가의 배타성 | DB leader만 바꾸고 구 리더 key 접근 유지 | 필요. |
| 결과 불명·부분 노출 인계 | 송신 상태 기록 이전/이후 crash를 구분하지 못함 | 필요. |
| gas 동시성·effects 갱신 | gas pool 공유·병합 후 낡은 참조 재사용 | 실제 coin 모드에서 필요. address-balance면 해당 coin 관리 범위는 축소. [S15·T0] [S16·T0] |
| 회수와 늦은 사실의 대사 | 옛 intent·미발행·환불 의무를 삭제 | 모델 1에서 필요. [K2·T0] |
| epoch 분열 동결과 rescue 운영 | 구형 프로토콜 전용 대응 | 현행 전제로 추가하지 않음. 과거 환경 지원이 별도 요구일 때만 분리 산정. [S2·T0] [S4·T0] |

이 부담은 **custom Raft backend만의 문제는 아니다.** 기성 DB를 골라도 DB 트랜잭션과 외부 Sui 실행은 같은 커밋이 아니므로 공통 실행자·서명·관측 계층의 책임을 비교해야 한다. 반대로 그 기능을 이미 검증된 외부 실행 계층이 제공한다면 backend에 동일 기능을 다시 만드는 비용을 중복 산정하면 안 된다. 이는 backend 선정 결론이 아니라 비교 범위에 대한 제안이다.

### 3-2. 작업량 범위

**현재의 독립적인 R2 작업량 추정치: 없다.** 대조한 정본 §15와 모델 1 승인 기록에는 이번 R2의 기준 인일·수행 인력·범위가 확정되어 있지 않다. 모델 1의 `(a) 16~26인일`은 제한된 로컬 통합의 기존 추정이며, 승인 기록이 **실제 production grant/Move와 Raft/quorum을 제외**한다고 명시한다. 이를 R2 추정으로 재사용할 수 없다. [K1·T0] [K2·T0]

| 요청한 비교 | 판정 |
|---|---|
| 제약 미반영 R2 기준 작업량 | **없다.** |
| 제약 반영 R2 총작업량 | 범위 미정으로 **산정 불가**. |
| 차이의 인일 범위·배수 | **확인 불가. 숫자를 만들지 않는다.** |
| 현행에서 제거된 epoch 잠금 때문에 추가할 필수 작업량 | 해당 과거 장애만을 이유로 증액할 근거 없음. 단, 미확정 실행 인계 작업이 0이라는 뜻은 아님. |

**비정량적인 범위는 제시할 수 있다.** 하단은 이미 원거래 영속 보존·서명 fencing·gas 독점·failover 대사를 검증한 실행 계층을 이용하여 적합성 확인과 연결 조건을 정하는 경우다. 상단은 이 기능과 장애 시험·운영 복구 절차를 별도로 만들어야 하는 경우다. 현재 SDK executor가 그 분산 HA 전체를 제공한다는 증거는 없으므로, 단순 SDK 설정만의 작업량으로 간주할 수 없다. [S12·T0]

숫자 범위를 산정하려면 최소한 **서명 키의 실제 관리 주체, 독립 실행자 수, coin/address-balance 모드, 원거래 보존 책임, 허용 장애 모델과 재개 목표**가 필요하다. 이번 조사는 이를 결정하지 않으며 R2 착수 금지를 해제하지 않는다.

### 3-3. §9 비교 항목 추가 여부와 질문 문단

**[설계 제안] 추가하는 것이 타당하다.** 기존 §9의 “확정·장애·복구”, “별도 구현 부담”, “응답 유실·재시작”에 걸치는 **외부 서명·체인 종결 경계**로 비교한다. 정본은 계속 `docs/DEVELOPMENT_PLAN.md §9`이며, 다음 문단은 그곳에 추가할 수 있는 **제안문**일 뿐 실제 파일을 변경하지 않았다. [K1·T0]

> **외부 서명·Sui 입력 충돌·미확정 인계:** 동일한 Sui 네트워크/프로토콜·SDK/gas 모드와 모델 1 권한 범위에서, 후보 backend 및 결합 실행자는 원거래 bytes·digest·전체 owned/gas 입력·최초 결과·외부 실행 허가를 어떻게 내구성 있게 결합하며, 리더 교체·응답 유실·구 리더 잔존 시 서로 다른 거래의 같은 입력 버전 사용을 어떻게 통제하는가? 내부 writer fencing과 이미 서명·송신된 거래의 체인상 종결을 분리하고, NotFound·timeout·저장 예산 만석에서도 원결과 조회와 검증된 관측을 미실행으로 오인하지 않는가? 현행 post-consensus 충돌 처리, 회수 cut 이후의 재송신 권한, owned/shared 및 실제 gas coin/address-balance의 차이를 같은 ACK·안정 저장·허용 장애 조건에서 비교할 때, 영향 범위·재개 지연·정상 goodput·추가 구현/운영 책임은 각각 무엇인가?

## 4. 회피·완화 후보 — 선택지만 제시

### 4-1. 공유 객체만 쓰는 경우

**[공식 문서]** shared input은 거래마다 특정 최신 사용 version을 지정하는 대신 object ID·initial shared version·접근 모드를 제공하고, 실제 사용 순서는 consensus scheduling이 정한다. 따라서 **그 업무 객체에 관한** owned exact-version 교체·충돌 문제를 줄일 수 있다. 동시에 같은 shared object를 쓰는 거래들이 모두 안전한 업무 결과를 만든다는 뜻은 아니다. [S8·T0]

**[설계 추론]** “업무 객체를 shared로 만들었다”와 “거래에서 충돌 가능한 owned 입력을 모두 제거했다”는 다르다. 실제 gas coin이나 별도 owned 입력을 사용하면 그 의존성은 남는다. Address-balance gas가 사용 가능한 환경에서는 gas coin 의존성을 제거하는 선택지가 있지만, 다른 owned 입력까지 자동으로 사라지지는 않는다. [S15·T0] [S16·T0]

**[공식 문서]** shared object는 누구나 참조할 수 있으므로 privileged operation의 권한 검증은 Move 코드가 담당해야 한다. 단일 주소 소유가 제공하던 접근 경계를 단순히 제거한 채로 동등한 위임 수단이라고 할 수 없다. [S19·T0]

**[공식 문서] 공유 객체 혼잡 제어에는 걸릴 수 있다.** 같은 shared object를 변경하는 거래는 순서대로 처리되고, 객체별 실행 예산을 넘으면 다음 consensus commit으로 유예될 수 있다. 반복 유예 뒤 `ExecutionCancelledDueToSharedObjectCongestion`으로 취소될 수 있으며, 높은 gas price는 우선순위를 바꾸지만 해당 객체의 총 실행 용량 자체를 늘리지 않는다. 이 값으로 KIX 실제 TPS나 지연을 계산할 근거는 없다. [S18·T0]

**[설계 추론]** 공유 객체 선택에서 별도로 부담하는 것은 Move 권한·업무 멱등성·현재 generation 검사와 혼잡 시 가용성이다. 서로 다른 거래가 순서대로 실행 가능하다는 특성 때문에, 같은 업무 요청을 새 nonce/bytes로 반복하는 경우를 계약이 별도로 막아야 할 수 있다. 또한 구 리더가 이미 보낸 거래 문제는 shared에서도 사라지지 않는다. **현재 owned 대비 얼마만큼 latency/gas를 잃는지는 확인 불가**이며, 구형 “owned만 consensus 우회” 설명으로 손실을 산정하지 않는다. [S2·T0] [S7·T0]

### 4-2. 소유 객체와 논리적 단일 서명 권한을 유지하는 경우

**[설계 후보]** 가용성을 “서명 가능한 복제본 여러 개가 각자 거래 생성”으로 확보하지 않고, **복원 가능한 승인 상태와 활성 서명 권한의 인계**로 확보하는 방식이다. 물리적인 signer 고가용성과, 동일 입력 버전에 대한 하나의 논리적 intent 승인 규칙을 분리한다.

가능한 수단은 활성/대기 실행자의 원거래·결과 공유, 실제 key 사용 권한을 검사하는 별도 signing gate 또는 그와 동등한 fencing, 미확정 입력의 범위별 격리, gas pool 인계와 재검증이다. 특정 제품·키 구조·복제 topology를 이번에 선택하지 않는다. **기성 SDK의 로컬 scheduling을 분산 서명 fencing으로 간주하지 않는 것**이 조건이다. [S12·T0]

남는 가용성 비용은 영향 객체의 다음 거래를 허가하기 전까지의 종결·버전 인계 대기와 signer failover 자체다. 사전에 유효한 위임 아래에서 체인 객체를 매 예약마다 소비하지 않는 업무는 별도일 수 있다. 정확한 영향 범위·재개 시간은 미정이다. **현행에서 이를 무조건 epoch 대기로 계산하지 않는다.** [S2·T0] [S4·T0] [K2·T0]

### 4-3. 비교표

아래 표는 두 방식의 선택 조건을 병렬로 정리한 것이다. 우열·채택 결론은 내리지 않는다. 사실 근거는 §0~§4-2와 각 행의 공식 링크, 판단 부분은 위 설계 제안에 따른다.

| 비교축 | A. shared 업무 객체 중심 | B. owned 업무 객체 + 논리적 단일 서명 권한 |
|---|---|---|
| 현행 epoch 분열 동결 | 이 과거 장애의 회피만을 단독 채택 이유로 삼을 수 없음 | 공개 현행 릴리스는 해당 pre-consensus 동결 메커니즘 제거. [S2·T0] [S4·T0] |
| 업무 객체 버전 관리 | 실제 접근 버전은 consensus scheduling이 결정 | 소유 입력의 정확한 version/digest 관리 필요. [S8·T0] [S4·T0] |
| 권한 경계 | privileged operation을 Move에서 검증해야 함 | 소유권 경계와 별도로 KIX의 위임·실행 허가 결합 필요. [S19·T0] [K2·T0] |
| 복제 실행자 동시성 | 체인 호출 순서는 조정되지만 업무상 중복·구 generation 처리는 별도 | 같은 입력 버전에 다른 intent가 생기지 않도록 승인/서명 인계 |
| gas | 실제 owned gas를 쓰면 gas 의존성은 남음. Address-balance는 사용 가능 여부 확인 필요 | 같은 조건. gas 분리는 업무 객체 충돌을 대신 해결하지 않음. [S15·T0] [S16·T0] |
| 주요 가용성 제약 | hot shared write의 예산·defer·congestion cancel | 입력별 종결 대기, signer failover, 잘못된 bytes 재작성 방지. [S18·T0] [S4·T0] |
| 구 리더의 이미 제출한 거래 | 로컬 fencing으로 회수되지 않으므로 결과 대사 필요 | 동일. 서명자 단일화도 이미 외부로 나간 거래를 소거하지 않음. [S7·T0] |
| HA에 필요한 추가 계약 | 권한/currentness·업무 멱등성·관측 인계 | 승인된 intent·원서명 bytes·전체 입력/gas·관측 인계 |
| 혼잡 비용 | 객체별 local fee market의 직접 영향 | owned라고 전체 네트워크 부하·충돌·gas 비용을 면제받는 것은 아님. 상대 차이 실측 없음. [S18·T0] [S7·T0] |
| latency·goodput 우열 | **확인 불가** | **확인 불가**. 과거 consensus-free fastpath 비교는 현행 근거에서 제외. [S2·T0] [S7·T0] |
| R2 추가 인일 | 기준 추정 없음, 정량 비교 불가 | 기준 추정 없음, 정량 비교 불가. [K1·T0] |

## 5. 확인 불가 사항과 후속 검증 경계

| 항목 | 현재 확인 수준 |
|---|---|
| KIX가 실제 사용할 RPC·validator의 binary/protocol 및 gas feature 활성 상태 | **확인 불가.** 이번에는 공개 릴리스·코드만 대조했다. |
| pre-consensus 잠금 제거의 정확한 Mainnet 활성화 날짜·epoch | protocol v105라는 공식 후속 기록은 있음. 달력 시각·epoch는 **확인 불가**. [S3·T0] |
| 구형 epoch 경고를 남긴 공식 문서들의 정정 일정 | **확인 불가**. 해당 문장과 현행 소스의 충돌만 확인. |
| rescue 도구가 현행 네트워크에서 의도한 잠금 거래를 성공적으로 완결하는지 | **확인 불가**. source-level digest 선택 불일치가 있고 실행하지 않았다. [S10·T0] [S11·T0] |
| KIX 소유 객체 사용 빈도·인계 영향 집합·실측 p99/RTO | **확인 불가**. 객체 배치·구현·실측은 이번 범위 밖. |
| 현재 공식 SDK가 제공하는 multi-process/Raft HA 보장 | **확인 불가**. 확인된 것은 로컬 queue·입력 scheduling·gas pool 기능. [S12·T0] |
| R2 기준/추가 인일·배수 | 정본 기준 독립 추정치 **없다**. 숫자 범위는 산정하지 않았다. [K1·T0] [K2·T0] |

후속 검증이 승인될 경우 비교할 관찰점은 원거래 외부 노출 전후의 crash, 응답 유실 후 동일 bytes 인계, 구 리더의 지연 제출, 동일 입력·gas의 경쟁, 확정 실패 후 gas 변화, 회수 cut 이후 늦은 사실, shared 혼잡 취소다. **이는 조사에서 도출한 미검증 항목 목록이며, 이번에 시험을 작성·실행하거나 R2/(a)를 시작한 것이 아니다.**

---

## 6. 공식 출처 및 고정 소스 식별자

모든 아래 출처는 `T0 = 2026-09-16~17 KST`에 확인했다. Sui 설명 문서는 변경 가능한 웹 문서이고, 코드 대조는 위에 고정한 release commit 기준이다. GitHub blob과 commit은 서로 다른 식별자이며 혼용하지 않았다. 출처별 문서/소스 구분 및 불일치는 아래 설명을 따른다.

### K1. KIX DEVELOPMENT_PLAN.md §9·§10·§15

[공식/정본 원문](https://github.com/BeautifulMind-JT/kix-protocol/blob/94376835ea4fc818619fc79e2be4df7d4947496a/docs/DEVELOPMENT_PLAN.md) · **확인: T0**

정본. Git blob 6efea0adcc2b1c7f4bd62c43673cc54830a8fc37. §9의 비교 질문은 이번에 수정하지 않았다.

### K2. KIX AUTHORITY_MODEL_1.md

[공식/정본 원문](https://github.com/BeautifulMind-JT/kix-protocol/blob/94376835ea4fc818619fc79e2be4df7d4947496a/docs/decisions/AUTHORITY_MODEL_1.md) · **확인: T0**

승인 기록. Git blob fec140112e11fe7403fa4fbda57d629e52a99f72. 모델 1, A-4/A-5, (a) 보류 및 R2 금지.

### S1. Sui Troubleshooting Common Errors — Transaction errors

[공식/정본 원문](https://docs.sui.io/develop/testing-debugging/common-errors) · **확인: T0**

공식 설명 문서. reserved/equivocated-until-next-epoch 설명이 남아 있으나, 현행 릴리스 적용 판단에는 S2~S4를 우선한다.

### S2. MystenLabs/sui PR #24676 — Disable Owned Object Locking

[공식/정본 원문](https://github.com/MystenLabs/sui/pull/24676) · **확인: T0**

공식 프로토콜 변경 기록. 2026-01-01T02:54:31Z 병합. merge commit 22f9fc9781732d651e18384c9a8eb1dabddf73a6. 합의 전 잠금을 합의 후로 이동하여 epoch 동결을 방지하고 기존 fastpath execution을 비활성화한다고 명시.

### S3. MystenLabs/sui PR #26278 — Remove dead code

[공식/정본 원문](https://github.com/MystenLabs/sui/pull/26278) · **확인: T0**

공식 후속 변경 기록. 2026-04-17T16:26:50Z 병합. merge commit a1a8af283a7a22036485c3b7cb097db9855ad91f. disable_preconsensus_locking이 Mainnet protocol v105부터 활성화됐다고 명시.

### S4. mainnet-v1.79.1 object_locks.rs

[공식/정본 원문](https://github.com/MystenLabs/sui/blob/58386edc269ef88ff0f40ab0a9d50e87cba80ca8/crates/sui-core/src/execution_cache/object_locks.rs) · **확인: T0**

공식 릴리스 소스. 전체 Git blob 8fff6c191c690e803a1bb901a0cf7b5765167985. clear()와 validate_owned_object_versions(): 합의 전 잠금 비활성, 서명 전 버전·digest 검증, 합의 후 잠금.

### S5. Sui Release Notes

[공식/정본 원문](https://docs.sui.io/references/release-notes) · **확인: T0**

조회 목록의 최신 Mainnet v1.79.1/protocol 136, 최신 Testnet v1.80.0/protocol 137. v1.77.2 CLI gas 선택 변경 및 v1.79.1/v1.80.0 expiration 변경도 확인.

### S6. mainnet-v1.79.1 release

[공식/정본 원문](https://github.com/MystenLabs/sui/releases/tag/mainnet-v1.79.1) · **확인: T0**

공식 릴리스. 2026-09-09T17:18:01Z 게시. 소스 기준 commit 58386edc269ef88ff0f40ab0a9d50e87cba80ca8. 실제 사용 RPC의 실행 binary를 조회한 것은 아니다.

### S7. Sui Life of a Transaction

[공식/정본 원문](https://docs.sui.io/develop/transactions/transaction-lifecycle) · **확인: T0**

공식 현행 lifecycle. 전체 transaction의 DAG sequencing, certified effects, checkpoint, finality timing, 동일 거래 재전송, NotFound의 한계.

### S8. Sui Object Versioning

[공식/정본 원문](https://docs.sui.io/develop/objects/versioning) · **확인: T0**

객체 버전과 shared input 참조 방식. fastpath가 consensus를 우회한다는 문장은 S2~S4·S7과 충돌하므로 현행 성능 근거로 채택하지 않았다.

### S9. Sui Consensus

[공식/정본 원문](https://docs.sui.io/develop/sui-architecture/consensus) · **확인: T0**

epoch 약 24시간, stake 가중 quorum >2/3, 거래 sequencing 및 확정 경계.

### S10. mainnet-v1.79.1 sui-tool commands.rs

[공식/정본 원문](https://github.com/MystenLabs/sui/blob/58386edc269ef88ff0f40ab0a9d50e87cba80ca8/crates/sui-tool/src/commands.rs) · **확인: T0**

공식 도구 소스. 전체 Git blob fe865e6b94b5724e60f2d16371eb0a3b76f66fed. LockedObject, check_locked_object(), --rescue. 명령 실행은 하지 않았다.

### S11. mainnet-v1.79.1 sui-tool lib.rs

[공식/정본 원문](https://github.com/MystenLabs/sui/blob/58386edc269ef88ff0f40ab0a9d50e87cba80ca8/crates/sui-tool/src/lib.rs) · **확인: T0**

공식 도구 소스. 전체 Git blob 9805d74a1ef794f14a6eca9894cfe1a2034e2e91. GroupedObjectOutput::new()의 stake 합산 및 tuple 구성 확인.

### S12. Mysten Labs TypeScript SDK — Transaction Executors

[공식/정본 원문](https://sdk.mystenlabs.com/sui/executors) · **확인: T0**

Serial/Parallel executor, gasMode, object dependency scheduling, 여러 인스턴스의 동일 sourceCoins 경고. epoch 잠금 경고는 S2~S4와 버전 충돌이 있다.

### S13. MystenLabs Sui Owned Object Pools README

[공식/정본 원문](https://github.com/MystenLabs/Sui_Owned_Object_Pools/blob/main/README.md) · **확인: T0**

공식 개발사 저장소. 조회한 README Git blob 3181adca80c2979145ccf54e0abe8330c162f738. Deprecated/no longer maintained, ParallelTransactionExecutor로 이동 권고. 과거 동기·coin selection 설명은 역사적 자료로 구분.

### S14. Sui official forum — Sui Owned Object Pools Library

[공식/정본 원문](https://forums.sui.io/t/sui-owned-object-pools-library/45215) · **확인: T0**

2024-01-22 공개된 개발 도구 안내. 회피 관행의 역사적 근거이며 2026년 전체 커뮤니티 사용 비율을 증명하지 않는다.

### S15. Sui Gas Smashing

[공식/정본 원문](https://docs.sui.io/develop/transaction-payment/gas-smashing) · **확인: T0**

여러 실제 gas coin 병합, 실패 후에도 병합 유지, 첫 coin 외 삭제, address-balance gas와의 차이.

### S16. Sui Using Address Balances — gas payment

[공식/정본 원문](https://docs.sui.io/onchain-finance/asset-custody/address-balances/using-address-balances) · **확인: T0**

empty gas payment, expiration·nonce, enable_address_balance_gas_payments 조회 방법. 대상 네트워크의 live feature flag는 이번에 조회하지 않았다.

### S17. Sui Sponsored Transactions — Concurrent object use

[공식/정본 원문](https://docs.sui.io/develop/transaction-payment/sponsor-txn) · **확인: T0**

sender input과 sponsor gas의 충돌, 전체 TransactionData/GasData 결합. epoch 동결 문구는 현행 소스와 구분.

### S18. Sui Object-Based Local Fee Markets

[공식/정본 원문](https://docs.sui.io/develop/transaction-payment/local-fee-markets) · **확인: T0**

동일 shared object write 직렬화, 실행 예산, defer/cancel, gas-price 우선순위, per-object 총용량 한계.

### S19. Sui Shared Objects

[공식/정본 원문](https://docs.sui.io/develop/objects/object-ownership/shared) · **확인: T0**

shared object 접근과 Move 권한 검증 책임. owned가 consensus를 우회하므로 더 빠르다는 비교 문구는 현행 소스와 충돌해 채택하지 않았다.

### R1. etcd API guarantees

[공식/정본 원문](https://etcd.io/docs/v3.6/learning/api_guarantees/) · **확인: T0**

Raft 계열 저장 API의 보장 범위 참고. timeout/disruption 시 결과 불명 가능성을 외부 Sui 효과의 취소로 확대 해석하지 않는다.


<!-- Reference links: each citation contains its verification-window marker. -->
[K1·T0]: https://github.com/BeautifulMind-JT/kix-protocol/blob/94376835ea4fc818619fc79e2be4df7d4947496a/docs/DEVELOPMENT_PLAN.md
[K2·T0]: https://github.com/BeautifulMind-JT/kix-protocol/blob/94376835ea4fc818619fc79e2be4df7d4947496a/docs/decisions/AUTHORITY_MODEL_1.md
[S1·T0]: https://docs.sui.io/develop/testing-debugging/common-errors
[S2·T0]: https://github.com/MystenLabs/sui/pull/24676
[S3·T0]: https://github.com/MystenLabs/sui/pull/26278
[S4·T0]: https://github.com/MystenLabs/sui/blob/58386edc269ef88ff0f40ab0a9d50e87cba80ca8/crates/sui-core/src/execution_cache/object_locks.rs
[S5·T0]: https://docs.sui.io/references/release-notes
[S6·T0]: https://github.com/MystenLabs/sui/releases/tag/mainnet-v1.79.1
[S7·T0]: https://docs.sui.io/develop/transactions/transaction-lifecycle
[S8·T0]: https://docs.sui.io/develop/objects/versioning
[S9·T0]: https://docs.sui.io/develop/sui-architecture/consensus
[S10·T0]: https://github.com/MystenLabs/sui/blob/58386edc269ef88ff0f40ab0a9d50e87cba80ca8/crates/sui-tool/src/commands.rs
[S11·T0]: https://github.com/MystenLabs/sui/blob/58386edc269ef88ff0f40ab0a9d50e87cba80ca8/crates/sui-tool/src/lib.rs
[S12·T0]: https://sdk.mystenlabs.com/sui/executors
[S13·T0]: https://github.com/MystenLabs/Sui_Owned_Object_Pools/blob/main/README.md
[S14·T0]: https://forums.sui.io/t/sui-owned-object-pools-library/45215
[S15·T0]: https://docs.sui.io/develop/transaction-payment/gas-smashing
[S16·T0]: https://docs.sui.io/onchain-finance/asset-custody/address-balances/using-address-balances
[S17·T0]: https://docs.sui.io/develop/transaction-payment/sponsor-txn
[S18·T0]: https://docs.sui.io/develop/transaction-payment/local-fee-markets
[S19·T0]: https://docs.sui.io/develop/objects/object-ownership/shared
[R1·T0]: https://etcd.io/docs/v3.6/learning/api_guarantees/
