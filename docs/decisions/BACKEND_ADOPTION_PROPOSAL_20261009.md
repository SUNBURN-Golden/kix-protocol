# 백엔드 채택 결정 제안 (2026-10-09)

노드 `k-stage4-adoption-decision`. 이슈는 없다. 4단계 로컬 탐색 뒤에, 5단계가 얹을 backend를 고를지, 아직 고르지 않을지에 대한 결정 제안이다. 비교 답의 정본은 [개발계획](../DEVELOPMENT_PLAN.md) §9 한 곳이다. 이 파일은 두 번째 비교표를 만들지 않는다.

## 0. 상태와 효력

상태: **제안.** 작성만으로 확정이 아니다. 이 파일은 독립 검토가 아니다. 작성자가 빌더이므로, 비작성자 exact-HEAD 검토가 아니다.

효력은 사용자가 이 문서를 병합할 때에만 생긴다. [로드맵](PROGRAM_ROADMAP_20260930.md) §1은 판정 표가 현재 병합 경계이고, `user_merge`는 대표님 몫이라고 적는다. [판정 표](../aiops/PROGRAM_ASTRA_DELEGATION.md)의 이 노드 행은 계약 변경 NO, 대표님 병합, A3다. R-6이 `k-stage5-durable-tx`를 시작하는 사건은 그 중 **병합**이다. 그 병합 전에는 이 권고가 개발계획, 열린 입력, 구현을 바꾸지 않는다.

[완료 설계](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md) §5.1은 사용자 결정 문서가 병합돼 `DONE`인 것과, 권고한 기능이 실제로 채택된 것을 별개로 둔다. 문서 병합과 권고의 이름만으로 `ADOPT`를 추론하지 않는다. `ADOPT`는 실제로 고른 backend와 승인된 범위가 문장으로 있을 때 그 범위의 구현으로 간다. 그 문장은 §6에 있다.

빌더는 병합하지 않는다. `k-stage5-durable-tx`를 시작하지 않는다. 아래 권고를 실행하지 않는다. 이 세션은 커밋, 푸시, PR, 이슈, 댓글을 만들지 않는다.

사용자는 병합 전에 §6의 문장을 바꿀 수 있다.

## 1. 기준

- 작업 시작 시 `git fetch origin main` 뒤의 `origin/main`과 HEAD: `6e54e723d582e88ae89df309eb144d4664c7e1f5`. 같은 커밋이다. 브랜치는 `agent/kix-k-stage4-adoption-decision`이다. 이 세션은 커밋하지 않으므로 구현 커밋 SHA는 없다. 나중의 커밋 SHA에 이 기준의 CI를 옮기지 않는다.
- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 문서 추가 뒤에 다시 계산한다. 두 파일은 수정하지 않는다.
- `docs/tasks/`에는 이 노드의 과제 파일이 없다. 이슈도 없다. 과제 파일과 이슈를 만들지 않았고 고치지 않았다. 입력은 노드 명세와 그것이 가리키는 문서다.
- `.aiops/program.json`의 이 노드 필드는 `user_merge: true`, `audit_floor: A3`, `astra_auto_merge: false`, `depends_on: k-stage4-local-exploration`이다. `astra_gate` 키는 없다. 노드 명세 머리의 `astra_gate: None`은 그 빈 칸과 같다. 초기 로드맵 표(93행)의 이 노드 칸은 A3, ARCHITECTURE, 병합은 사용자다. 판정 표는 계약 변경 NO, 대표님 병합, A3다. 병합 주체는 같다. Astra 게이트 칸의 차이는 이 문서가 정하지 않는다. 판정 표 문서는 머리말에서 비실행 초안이라고 적는다.
- 노드 명세가 가리키는 [프로그램 결정](PROGRAM_DECISIONS_20260928.md) 「~60행」은 현재 본문 60행이다. 그 문장은 탐색 결과에 「탐색 자료」를 붙이고, backend 채택·5단계 영속 거래·자체 R2 판단은 별도 결정이라고 적는다. 명세가 가리키는 [개발계획](../DEVELOPMENT_PLAN.md) 「~118행」은 어긋난다. 118행은 첫 묶음에 회수·물리 저널·복제·frontend·색인 변경이 없다는 문장이다. 4단계 행은 **111행**, 5단계 행은 **112행**, 「backend 채택은 별도 결정」은 **121행**이다.
- 고치지 않은 파일: 두 잠금 blob, `reference/v0.3-rc1/**`, `.aiops/`, `.github/`, `docs/tasks/`, `docs/contracts/**`, `docs/adr/**`, 개발계획, 루트 README, `runtime/**`, CI, `validation/2026-10-08-k-stage4-local-exploration/`의 탐색 스크립트와 원시 자료.
- 승인된 공수 추정은 없다. 숫자 없음.

## 2. 출처와 우선순위

이 제안이 읽는 순서다.

1. [프로그램 결정](PROGRAM_DECISIONS_20260928.md) §2.2 54–60행. 4단계는 비교 준비, 공식 자료 선별, 같은 조건의 로컬 탐색, readiness fault의 공통 적합성까지다. 채택과 5단계와 R2는 그 다음의 별도 결정이다. 같은 절 61–63행의 v5 착수 조건은 R-4가 고친 쪽이 현재다.
2. 같은 문서 §5. 114행은 R2·자체 복제·합의·저장 엔진의 해제 조건이다. 기성 backend의 구체적 부족, 비용·검증·운영 책임의 문서, 사용자 승인이 모두 있어야 한다. 117행의 schema·SDK 안정 1.0과 일괄 명칭 치환도 이 제안이 열지 않는다. 실자금, 실 PG·은행·KYC, 공개 운영 엔드포인트, Sui testnet·mainnet, 새 coin/TIX 모듈은 같은 표의 잠금이다.
3. [로드맵](PROGRAM_ROADMAP_20260930.md) R-4(37행). v5 설계 결정을 사용자가 병합하면 `k-stage2-v5-impl`이 시작한다. 아직 열린 행에 기대는 부분만 `DECISION_REQUIRED`로 멈춘다.
4. 같은 문서 R-6(39행). 이 채택 문서를 사용자가 병합하면 `k-stage5-durable-tx`가 시작한다. R2와 자체 복제·합의는 계속 잠금이다. §5 218행은 R2·자체 복제·합의·저장 엔진을 실행 노드로 넣지 않는다.
5. 같은 문서 §1(22–28행). 판정 표가 병합 경계다. 제품 정책과 새 명령은 `DECISION_REQUIRED`로 멈추고, 법률·회계·제공자 답변은 `UNDETERMINED`와 담당을 남긴다.
6. [개발계획](../DEVELOPMENT_PLAN.md) §5 111–112행과 121행, §9, §9.3–§9.5, §10 467–474행. §9 비교표가 유일한 정본이다. §9.5는 결과를 탐색 자료로 두고, 제품 SLO·backend 채택·내구성 우열·R2 근거가 아니라고 적는다.
7. [ADR-0001](../adr/0001-ktx-authority-commit-recovery.md) 부록 B(147–151행). 어댑터 durable inbox의 책임이다. 그 패치는 inbox를 구현하지 않는다. 5단계 행이 말하는 outbox는 이 부록의 문장이 아니다. outbox는 개발계획 112행과 §10이 이름만 둔다.
8. [완료 설계](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md) §5.1. `DONE`은 긍정 채택이 아니다. `none yet`는 `DEFERRED`이고, 그 영향을 받는 구현은 `WAITING/HOLD`로 남는다. 이 노드의 「아직 없음」을 그 절이 이미 `DEFERRED`로 적는다.

프로그램 결정 §5의 잠금은 유지한다. 실자금, 실 PG·은행·KYC, 공개 운영 엔드포인트, Sui testnet·mainnet, R2, 자체 복제·합의·저장 엔진, 새 coin/TIX 모듈은 이 제안이 열지 않는다.

## 3. 탐색이 보여 준 것

아래는 [개발계획](../DEVELOPMENT_PLAN.md) §9 비교표와 §9.5의 문장을 보통 말로 옮긴 것이다. 숫자의 정본은 그 표의 바이트와 건수다. 이 절은 그 표를 다시 그리지 않는다. [manifest](../../validation/2026-10-08-k-stage4-local-exploration/manifest.json)의 `ranking`은 `null`이고, 이 제안이 그 값을 채우지 않는다. 원시는 [탐색 기록](../../validation/2026-10-08-k-stage4-local-exploration/README.md)에 있다.

두 후보 모두 같은 업무 필드를 한 커밋에 넣었다. 명령 identity, payload sha256, 최초 결과, 합성 show `synthetic-show`의 slot, 최소 주문, 외부 의도 기록이다. 외부 의도 기록은 `FIXTURE_NOT_DISPATCHED`이고 호출은 없다. 업무 거절은 주문 없이 명령 결과만 남긴다. 금액은 u128 십진 문자열이다. 체인 재고 writer는 없다. PostgreSQL은 그 필드를 로컬 트랜잭션 하나에 넣는다. FoundationDB는 같은 필드를 한 트랜잭션의 여러 key로 넣으며, 관계·재고·결과는 application key다.

둘 다 로컬 readiness `BackendConformance`를 각 어댑터에 묶어 통과했다고 §9와 §9.5가 적는다. 통과는 채택이 아니고 production conformance가 아니다. `production_conformance`는 false다.

예산이 찬 뒤에도 이미 저장된 최초 결과는 읽힌다. `max_entries=3`에서 신규 성공 3, capacity 3, 이어서 기존 명령의 replay 1이다. capacity는 경제 효과 행을 더하지 않는다. 같은 명령의 replay는 저장된 최초 결과를 돌려준다.

프로세스 crash는 디스크가 남은 채 SIGKILL한 뒤의 재시작이다. 두 후보 모두 그 재시작에서 최초 결과가 남았다. 전원·OS crash는 주입하지 않았고, 하드웨어 flush는 확인하지 않았다.

u128 최댓값 `340282366920938463463374607431768211455`를 십진 문자열로 저장하고 다시 읽었다. signed 정수로 줄이지 않았다.

checksum이 어긋나면 둘 다 `CHECKSUM_MISMATCH`로 닫는다.

자원 cap은 두 후보에 같았다. CPU는 코어 2개(affinity 0–1), RAM cap은 536870912바이트(서버 RSS와 클라이언트 RSS의 합), 디스크 cap은 268435456바이트다. 둘 다 cap 안에서 끝났고, 동시에 띄우지 않았다. 인력·투자 축에 적힌 바이트는 PostgreSQL이 서버 RSS 23158784, 클라이언트 RSS 36859904, 디스크 41535867이고, FoundationDB가 서버 RSS 90161152, 클라이언트 RSS 56180736, 디스크 210918811이다. 이 한 번의 실행에서 PostgreSQL 쪽 RSS 합과 디스크가 더 작다. 탐색 자료이며 순위가 아니다. 메가바이트로 다시 적지 않는다.

## 4. 아직 증명되지 않은 것

§9.5가 비어 있다고 적은 것과, 그 실행의 조건이 범위를 한정하는 것이다.

- 두 후보의 내구성이 같다는 판정은 없다. `durability_equal_to_other_candidate`는 false다. 장애 보장이 다르므로 우열 결론은 보류다.
- 하드웨어 flush는 미검증이다. 장비 자료가 없다.
- 전원 crash와 OS crash는 주입하지 않았다. 디스크가 남은 프로세스 crash와 다른 사건이다.
- 독립 장애 도메인은 없다. FoundationDB는 프로세스 1개, `redundancy_mode` `single`, usable region 1이다. zone 장애 허용은 데이터와 가용성 모두 0이다. 한 호스트의 프로세스 하나는 장애 도메인이 아니다.
- TiKV는 측정하지 않았다. §9.3의 release·client ACK 조건이 그 실행에서 새로 충족되지 않았다.
- TigerBeetle은 §9.3이 이번 전체 업무 단위의 단독 backend 실측에서 제외한 상태 그대로다. 제품 일반의 채택 거절이 아니다.
- 탐색 설정은 warmup 2, repeats 1, arrival rate 0, concurrency 1이다. rate 0은 열린 루프가 아니다. 그 축의 초당 성공 수와 p99는 제품 TPS와 제품 p99가 아니다. 이 제안은 그 수를 옮기지 않는다.
- 실행한 PostgreSQL은 17.11 (Debian 17.11-0+deb13u1)이다. §9.3이 읽은 선별 문서는 PostgreSQL 18이다. §9.3은 후속 실행이 binary·client 버전과 문서 revision을 pin하라고 적는다. 선택지 A를 병합하면 5단계 로컬 핀은 이번 탐색이 실행한 **17.11 (Debian 17.11-0+deb13u1)** 이다. 18 문서로의 이동은 새 pin이고, 이 채택이 아니다.
- `autovacuum=off`는 짧은 탐색에서 retry WAL을 vacuum과 섞지 않으려는 설정이다. 운영 설정으로 승인된 값이 아니다.
- 인건비, 전력, 연간 운영비, 투자 한도. `UNDETERMINED — 사용자/운영 책임자`. 장비 구매·클라우드·라이선스 지출은 없었다. 단가는 비어 있다.
- 승인된 SLO, TPS, p99, RTO, RPO는 없다. 2배/0.1%도 승인 목표가 아니다. `DECISION_REQUIRED · Astra`. 이 제안이 수를 만들지 않는다.
- 보존 기간과 I09·I10·I13은 그대로 열려 있다. [보존 기간 제안](RETENTION_PERIODS_PROPOSAL_20261009.md)이 칸과 주인을 적었고, 기간의 숫자는 없다. 이 제안이 그 값을 채우지 않는다.
- I12 절단 증명은 열려 있다. 슬롯 해제는 멈춘 채로 둔다. [v5 설계 결정](STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) §6과 [I12 절단 증명](CUT_PROOF_I12_20261008.md).
- R2, 자체 복제, 합의, 자체 저장 엔진. 이 탐색은 그 잠금의 해제 근거가 아니다.

## 5. 선택지, 결과, 권고

네 갈래다. 권고는 A다. 빌더는 어느 갈래도 실행하지 않는다. 운영 backend의 선택은 A를 골라도, C를 골라도, 이 문서 밖에 남는다.

| 선택 | 내용 | 판정 |
|---|---|---|
| A | 5단계의 로컬·비운영 범위에 PostgreSQL을 쓴다. | **권고** |
| B | 같은 로컬·비운영 범위에 FoundationDB를 쓴다. | 권고하지 않음 |
| C | 아직 없음 (`DEFERRED`). | 대안 |
| D | TiKV 또는 하드웨어·전원·OS 장애를 먼저 더 탐색한다. | `DECISION_REQUIRED` |

자체 저장 엔진과 R2는 선택지에 없다. 프로그램 결정 §5 114행이 잠그고, 이 탐색이 기성 backend의 구체적 부족을 입증하지 않았다.

### A. 권고. 5단계 로컬 PostgreSQL

업무 단위가 관계형 트랜잭션 하나에 올라간다. FoundationDB는 관계·재고·결과를 application key로 더 둔다. 개발계획 §9.3이 그 부담을 적는다. 어댑터가 트랜잭션 경계까지 새로 만들 부분이 더 적다. 부품 개수의 실측 순위는 아니다.

로컬 단일 프로세스 PostgreSQL에는 백업·패치·모니터링에 쓰는 보통의 도구가 있다. 그 절차의 시간·성공·비용은 이번 탐색이 재지 않았다. 책임과 단가는 §8에서 비어 있다.

§3의 RSS 합과 디스크 바이트는 이 한 번의 실행에서 PostgreSQL 쪽이 더 작다. 같은 cap 안의 탐색 자료다. 순위로 읽지 않는다.

`BackendConformance`는 PostgreSQL 어댑터로 통과했다. FoundationDB도 통과했다. 둘 다 통과했다는 사실이 우열이 아니다. 채택의 범위는 그 적합성의 로컬 재사용이지, production conformance가 아니다.

A를 골라도 운영 backend는 고르지 않는다. 내구성 동등, 하드웨어 flush, 전원·OS crash, 독립 장애 도메인, TiKV, 비용, SLO는 §4 그대로다. 멈춘 항목은 그대로다. R2·복제·합의·자체 저장 엔진은 열리지 않는다.

### B. 같은 범위의 FoundationDB

5단계가 단일 프로세스 FoundationDB 7.3.77, `redundancy_mode` `single` 위에 올라간다. 그 구성은 독립 장애 도메인이 아니다. zone 장애 허용은 0이다. 업무의 관계·재고·결과는 application key다. 같은 적합성은 통과했다. 내구성이 더 낫다는 근거는 없다. 이 로컬 범위의 권고는 아니다. 운영 backend의 후보로 남겨 두는 일과는 별개다. 그 결정은 이 문서가 내리지 않는다.

### C. 아직 없음 (`DEFERRED`)

backend를 지금 고르지 않는다. [완료 설계](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md) §5.1의 `DEFERRED`다. 5단계 `k-stage5-durable-tx`, `k-onsale-admission-control`, 6단계, 7단계, 그리고 그 단계들에 기대는 뒤 구현은 `HOLD`다. 같은 절이 이름 붙인 CPU·GPU와, 실제 backend가 있어야 하는 뒤의 protocol·Finance·commerce 구현도 그 범위다. 목록에서 행을 지우거나, 다른 backend로 자동 대체하거나, 완료로 바꾸지 않는다. 운영 backend도 그대로 미정이다.

대가는 5단계와 그 뒤가 시작하지 않는다는 것이다. 사용자가 미루기를 원하면 병합 전에 §6의 문장을 고친다.

### D. 탐색을 더 한 뒤 고른다

TiKV를 같은 범위로 재거나, 하드웨어 flush·전원 crash·OS crash를 주입하려면 새 지출이 필요하다. 새 바이너리, 새 장비, 새 VM, 클라우드, 라이선스가 그 지출이다. `DECISION_REQUIRED`. 결정자는 사용자와 운영 책임자다. 이 제안은 그 탐색을 시작하지 않고, 견적과 장비 모델을 적지 않는다. 사용자가 이 갈래를 원하면 §6을 먼저 고치고, 지출 승인 뒤에 별도 노드로 연다.

## 6. 병합이 채택하는 범위

사용자가 이 문서를 문장 수정 없이 병합하면, 선택지 A만 채택되고, 채택되는 backend는 5단계의 로컬·비운영 PostgreSQL 17.11(Debian 17.11-0+deb13u1)이며, 그 범위는 단일 프로세스·단일 작성자·기본 꺼짐·운영 플래그 false·R2와 복제와 합의는 열지 않음·이미 멈춘 항목은 멈춘 채로다.

그 한 문장이 이후 노드가 읽을 범위다. backend의 이름이 문장 안에 있으므로, 병합됐다는 사실만으로 채택을 추론하지 않아도 된다. 사용자는 병합 전에 위 문장을 바꿀 수 있다. B, C, D를 채택하려면 그 문장을 먼저 고친다. C로 고치면 결과는 `DEFERRED`이고 5단계와 그 뒤는 `HOLD`다. 빌더는 문장을 실행하지 않는다.

운영 플래그는 [프로그램 결정](PROGRAM_DECISIONS_20260928.md) §4의 경계다. `protocolTruth`, `productionConformance`, `productionReadiness`, `productionEndpoint`는 false다. FSM `durable`도 false다. 복제, 합의, 다중 작성자, 네트워크 전송, 원격 저장, 운영 기본 활성은 이 채택 밖에 있다.

## 7. 5단계가 얹을 것

R-6은 이 문서의 사용자 병합 뒤에 `k-stage5-durable-tx`를 시작한다. 그 노드의 선행은 이 채택과 `k-stage2-v5-impl`이다. `runtime/crates`에는 오늘 v5 crate가 없다. 있는 crate는 `kix-bcs1`, `kix-feature-ir`, `kix-feature-semantics`, `kix-kernel`, `kix-types`다. v5 구현이 병합되기 전에는 5단계가 그 crate에 기댈 수 없다.

5단계 노드 명세가 가리키는 개발계획 「~109행, 268–275행」은 현재 본문에서 어긋난다. 109행은 2단계 행이고, 268–275행은 §9.1의 R2 범위다. 5단계가 읽을 문장은 **112행**과 **§10 467–474행**이다. ADR 부록 B는 147–151행으로, 명세의 「~145–151행」과 맞다. 5단계의 가드는 병합된 이 문서의 §6을 읽고, 명세의 옛 행 번호로 범위를 넓히지 않는다.

이미 있는 것을 다시 만들지 않는다.

- [readiness/conformance.py](../../readiness/conformance.py)의 `BackendConformance`.
- [exploration/stage4/adapters.py](../../exploration/stage4/adapters.py)의 어댑터. 5단계는 이 로컬 어댑터를 업무 범위로 재사용한다. 새 저장 엔진이 아니다.

§10이 5단계에 맡기는 일이다. 명령·원payload·최초 결과·예약·최소 주문·외부 의도를 원자적으로 보존하고, commit과 응답 전후의 장애에서 복원한다. inbox에 받은 것을 보존하는 일과 경제 효과를 적용하는 일은 구분한다. durable inbox의 책임은 ADR-0001 부록 B다. 수신 원문, provider/account/event/operation 식별자, 원문 해시, 검증 결과를 커널 호출과 제공자 수신 ACK 전에 보존한다. inbox 보존이 실패하거나 용량이 모자라면 수신 ACK를 보내지 않고 역압력을 적용한다. outbox는 112행이 이름만 둔다. 이 제안이 outbox의 새 명령을 만들지 않는다.

항목마다의 정규화는 [어댑터 정체성](../contracts/ADAPTER_EVENT_IDENTITY.md) §4.4가 이미 적는다. 인증된 조회의 항목별 사실이고, 미검증 웹훅 본문에서 만들지 않는다. I06은 미완결이다. 이 제안이 정규화 규칙이나 프로토콜 명령을 새로 만들지 않는다.

건수·바이트·나이 예산은 나뉜다. §10은 신규 유입과, 완료·관측·취소·복구의 count/byte/age를 구분한다. 숫자는 없다. 보존 기간 제안의 메모리 상주도 같은 세 종류의 이름만 가지고, 값은 `DECISION_REQUIRED · Astra`다.

v5 설계 결정에서 넘어오는 정지다. I09, I10, I12, I13은 열려 있다. 슬롯 해제는 I12와 I13이 닫히기 전까지 만들지 않는다. 상태를 바꾸는 기록 회수는 I09·I10·I13 때문에 정지다. 5단계가 그 정지를 이 backend 채택으로 풀지 않는다.

PG·은행·체인 호출은 커널 밖이고, 이번 채택이 실호출을 허용하지 않는다. 기성 데이터베이스가 제공하는 로그를 불필요하게 다시 만들지 않는다. §10은 그 일이 전부 미착수라고 적는다. 이 제안 이후에도, 사용자가 §6을 병합하기 전에는 미착수다.

## 8. 비용·운영 질문

값은 없다. 단가 칸은 비어 있다. 책임자의 이름은 없다. 지명은 사용자다. 상태는 모두 `UNDETERMINED — 사용자/운영 책임자`다.

| 질문 | 상태 |
|---|---|
| 운영 책임자의 이름 | `UNDETERMINED — 사용자/운영 책임자` |
| 패치와 보안 업데이트의 담당·주기 | 같은 상태. 단가 없음 |
| 백업의 담당·주기·보관 위치 | 같은 상태. 단가 없음 |
| 복구 훈련의 담당·주기 | 같은 상태. 단가 없음 |
| 업그레이드. 17.11 핀을 18 문서 기준으로 옮길지 | 같은 상태. 옮기려면 새 pin. 단가 없음 |
| 인건비, 전력, 연간 운영비, 투자 한도 | 같은 상태. 단가 없음 |

이 표는 저장 backend의 운영 착수 승인이 아니다. 지출이 필요해지면 구매 전에 `DECISION_REQUIRED`로 멈춘다. 결정자는 사용자와 운영 책임자다.

## 9. 기존 커버리지 (AGENTS §7)

이 노드는 시험을 추가하지 않는다. 4단계 측정을 다시 실행하지 않는다. 다시 실행하면 다른 호스트의 새 측정이 되고, 그 측정은 이 노드의 범위가 아니다.

| 요구 | 근거 | 분류 |
|---|---|---|
| 예산 거절이 기존 기록과 재생 identity를 남긴다 | [readiness/conformance.py](../../readiness/conformance.py) `BackendConformance.test_budget_rejection_preserves_records_and_replay_identity`. [exploration/stage4/test_stage4.py](../../exploration/stage4/test_stage4.py)가 이 mixin을 PostgreSQL·FoundationDB 어댑터에 묶는다. 개발계획 §9·§9.5는 그 로컬 unittest 통과를 탐색 자료로 적는다 | 부분. 로컬 어댑터 증거다. 이 세션이 다시 실행하지 않았다. CI가 `exploration.stage4.test_stage4`를 실행하지 않는다. production conformance가 아니고, 하드웨어 내구성이 아니다 |
| 찢긴 tail을 버리고 나쁜 checksum은 닫는다 | [readiness/test_faults.py](../../readiness/test_faults.py) `StoreTests.test_torn_tail_is_discarded_and_a_bad_checksum_fails_closed`. 개발계획 §9.4가 이 시험을 부분 커버로 적는다 | 부분. readiness 로컬 파일 저널의 증거다. PostgreSQL·FoundationDB 프로세스의 시험이 아니다. 탐색이 두 후보에서 `CHECKSUM_MISMATCH`로 닫힌 것은 별도 탐색 자료다 |
| 두 후보의 로컬 업무 mapping, 적합성 결합, 디스크가 남은 프로세스 crash 뒤의 보존 | 같은 `test_stage4.py`. 실행에는 로컬 PostgreSQL 17과 FoundationDB 7.3.77이 필요하고, 탐색 기록이 CI 밖이라고 적는다 | 부분. 2026-10-08 기록이 탐색 자료다. 이 세션의 재실행이 아니다. CI 밖이다 |
| 하드웨어 flush, 전원·OS crash, 독립 장애 도메인 | 개발계획 §9.5가 비어 있다고 적는다. 요약의 `hardware_flush_verified`는 false, `power_os_crash_injected`는 false, `independent_failure_domain`은 false | 미커버 |

## 10. 분류 (AGENTS §8)

### A. 계약과 일치

- 4단계 결과는 탐색 자료다. 채택은 별도 사용자 결정이다. 프로그램 결정 60행, 개발계획 121행, §9.5.
- 비교표는 개발계획 §9 하나다. `ranking`은 null이다.
- 5단계 착수는 이 문서의 사용자 병합과 v5 구현 뒤의 로컬·비운영이다. R-6, 개발계획 112행.
- 프로그램 결정 §5의 잠금은 그대로다.
- 사용자 결정의 `DONE`은 그 자체로 긍정 채택이 아니다. 완료 설계 §5.1.

### B. 계약이 정의하지 않음. 성격만 기록

- 보존 기간, 보관량, 저장 예산. 개발계획 §6.3과 보존 기간 제안이 미정으로 둔다. 숫자를 만들지 않았다.
- SLO, TPS, p99, RTO, RPO. 승인된 수가 없다. `DECISION_REQUIRED · Astra`.
- I12 절단의 수락 갈래. I12는 미완결이다. 슬롯 해제는 정지다.
- 비용 단가와 운영 책임자의 이름. `UNDETERMINED — 사용자/운영 책임자`.
- 두 후보의 내구성 동등. 탐색이 보류라고 적었고, 이 제안이 동등이라고 정하지 않는다.

이 항목에 의미를 지어 개발계획, 계약, ADR을 고치지 않았다.

### C. 명시적 계약 위반

없음. 잠금 파일을 고칠 위반이 아니다.

## 11. 비주장

이 문서는 다음을 주장하지 않는다.

- 운영 준비, 내구성의 동등, 은행 exactly-once, 체인 finality.
- 후보의 순위. `ranking`은 null이다.
- 승인된 SLO, TPS, p99, RTO, RPO, 비용, 단가. 숫자 없음.
- 동등 조건 성능 축의 초당 성공 수를 비교 결과로 읽는 일. 그 수는 이 문서에 없다.
- 잠금이 풀렸다. 프로그램 결정 §5는 그대로다.
- 5단계, v5 crate, outbox 명령, 새 프로토콜 명령이 만들어졌다.
- I09·I10·I12·I13이 닫혔다. 슬롯 해제가 허용되었다.
- 독립 검토가 있었다.
- 공수. 숫자 없음.
- 이 세션의 로컬 명령이 exact-head CI다. 이전 SHA의 녹색을 이 문서의 통과로 옮기지 않는다. 문서만 바뀐 변경의 CI 초록은 전체 검증이 아니다.

## 12. 병합 이후

아래는 이 세션에서 하지 않는다.

- 개발계획 111–112행과 121행을 채택된 문장에 맞게 고치는 일. 로드맵이 개발계획 반영을 `roadmap-sync`에 둔 것과 같은 종류의 후속이다.
- R-6에 따라 `k-stage5-durable-tx`를 시작하는 일. 그 노드의 가드는 병합된 이 문서의 §6을 그대로 읽는다. 문장이 A이면 로컬·비운영 PostgreSQL 17.11의 그 범위만 구현한다. 문장이 C이면 정상 구현은 `HOLD`이고, 막힌 이유를 결정에 묶어 남긴다. 그 노드의 Astra 아키텍처 감사는 이 제안과 별개다.
- `k-stage2-v5-impl`을 이 문서로 시작하는 일. 그 시작은 R-4가 v5 설계 문서의 병합에 걸어 둔 사건이다.
