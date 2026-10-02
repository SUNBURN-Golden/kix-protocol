# kix-protocol — 원대한 제품 목표와 상세 실행 계획

2026-10-02 KST · 확대 계획 후보 / 이번 변경은 계획·문서만 작성

## 목표

체인 원권위와 위임 실행을 기반으로 예매·리셀·검표·정산·환불·금융·마케팅·AI 위임이 공유하는 프로토콜. 공연당 RS profile과 플랫폼 전체 100만~3,000만 권리를 구분하여 확장하고, 정산채권 적격성부터 여신 상환·연체·회수까지 경제적 사실을 끝까지 추적한다.

사용자 원문: “ZARI, film-unit-mv-studio, Kixprotocol, kixcommerce 전부 최대한 원대하고 .aiops/program.json 넣어줘”, 후속 “원대하고 자세히”. 기능 목록을 넘어 구현 범위·산출물·실패 검증·정확한 선행관계를 작성하라는 지시로 반영했다. 현재 대화는 계획 작성의 근거이며 미래의 모든 상품 정책·실환경 권한·릴리스 결정을 미리 승인한 기록으로 사용하지 않는다.

## 계획을 읽는 방법

- `.aiops/program.json`: schema-v1 형태의 로컬 작업 **73개**. 현재 pointer는 PENDING이므로 실행 입력으로 사용할 수 없다. 기존 67개 정의를 보존하고 6개를 추가했다.
- `docs/decisions/PROGRAM_ROADMAP_20260930_PENDING.json`: 외부 선행·새 계약·실환경 자격이 필요한 **36개**. 기존 15개를 보존하고 21개를 추가했다. 이 catalogue는 스케줄러가 실행하지 않는다.
- 전체 검토 분모: **109개**. Finance 등 같은 ID의 부분집합을 두 번 세지 않는다. 필요 없는 기능의 연기는 명시적인 범위 개정으로 기록하며 완료로 바꾸지 않는다.
- `docs/aiops/KIX_PROGRAM_DRAFT.json`는 위 program과 바이트가 같은 비활성 원본이다. `REGISTRATION_SCOPE_DRAFT.json`은 전체 정의와 문서 해시를 묶는다.
- 기존 작업의 구현을 반복하는 계획이 아니다. 착수 시 현재 소스·증거와 대조해 이미 충족된 요구는 정확한 근거를 연결하고, 남은 gap만 구현한다. 기존 source/의미를 보존한 채 검증 없이 DONE 처리하지 않는다.

## 기준과 기존 등록 PR의 관계

- 관측 main: `dd0a501248e092c2a4475088d94d7449b7bd98b5`.
- 기존 시작 PR #87: `df7b026590677448438be62d2249f13f2da1cbaf` / `aiops/register-program-20261002`. 이번 확대 후보는 그 위의 별도 draft PR이며 원래 시작 PR을 수정하지 않는다.
- 기존 [중앙 #57](https://github.com/BeautifulMind-JT/ai-ops-control-plane/issues/57)의 시작 범위·과거 감사는 새 정의에 승계되지 않는다. 원래 시작 PR을 선택할지 확대 범위로 대체할지는 검토 후 한 개의 채택 plan으로 정한다.
- 승인 전 program mirror를 운영 중인 기본 브랜치에 합치지 않는다. 확대 정의를 검토·채택한 뒤 시작 개정에서는 승인된 원본을 복사하고 approval_pointer만 정확한 결정으로 바꾼다. 기존 schema-v1 reader는 PENDING을 실제 거절한다.
- 이번 형식 검증에 사용한 중앙 소스: `a34a38b73f096c9f6597b38a111d95ca12ecd159`. source 읽기/검증 사실은 설치·호스트 자격·독립 감사가 아니다.

## 단계와 의존관계

| 작업 묶음 | 신규 작업 ID |
|---|---|
| 기존 프로그램 완성도 | `k-current-capability-map`, `k-adversarial-corpus`, `k-sdk-examples`, `k-benchmark-reproduction`, `k-operator-evidence`, `k-local-program-closeout` |
| 대규모 권리·거래 플랫폼 | `ps-01-routing-authority`, `ps-02-query-contract`, `ps-03-resale-contract`, `ps-04-execution-partitions`, `ps-05-query-projections`, `ps-06-admission-load`, `ps-07-scale-qualification` |
| 여신 전체 수명 | `cr-01-product-authority`, `cr-02-claim-eligibility`, `cr-03-facility-reservations`, `cr-04-underwriting-consent`, `cr-05-disbursement-observation`, `cr-06-repayment-allocation`, `cr-07-delinquency-recovery`, `cr-08-producer-sdk`, `cr-10-credit-qualification` |
| 외부 자격과 운영 준비 | `k-provider-sandbox`, `k-authority-qualification`, `k-token-platform-contract`, `k-operator-contract` |
| 출시와 운영 | `k-platform-release` |

각 노드의 `depends_on`은 같은 레포의 정확한 ID를 가리킨다. pending의 `depends_on_external`은 producer/consumer의 정확한 repo·program·node를 가리킨다. 목록 순서를 실행 순서로 추정하지 않는다. 독립 branch는 선행이 충족되면 진행할 수 있지만 같은 task/checkout의 writer는 하나다.

외부 의존성이 충족되지 않은 노드를 “문서에 적어두었으니 실행 가능”으로 승격하지 않는다. reader가 채택되거나, 실제 외부 완료와 현재 producer tuple을 검토해 승인된 계획 개정을 만들 때까지 pending을 유지한다. 같은 레포의 미래 계약 노드도 명시된 승격 조건을 만족해야 한다.

## AIOPS가 자율적으로 진행할 범위

- 한 작업 소유자가 구현→테스트→실패 분석→수정→PR을 이어간다. 일상적 알고리즘·리팩터링·레이아웃 선택은 승인 계약 안에서 자율 결정한다.
- 독립 reviewer는 같은 HEAD의 실제 diff와 acceptance를 확인한다. 실패하면 같은 소유자에게 지적을 돌리고 변경 HEAD에서 다시 검토한다. 작성 세션은 자기 독립 감사 PASS를 발급하지 않는다.
- 작업별 실제 산출물과 검증 근거가 필요하다. 빈 모듈·고정 성공 응답·미연결 화면·테스트 대역만으로 실사용 완료를 선언하지 않는다.
- 계정 로그인/OS 권한/제공자 scope·중요 계약/실제 공개·릴리스처럼 사용자 권한이 필요한 결정만 질문한다. 기존 user_merge·A3·RELEASE를 일반 구현 질문으로 대체하지 않는다.
- 계획 노드 개수와 실제 비용·기간은 다르다. 정액 소요 기간·무제한 계정 사용·운영 성능을 약속하지 않는다. 사용량/외부 실행의 미확정 결과는 중복 제출하지 않는다.

## 공통 완료 판정

개발 delivery, 실제 기기/provider qualification, 사용자 화면/작품 수용, 운영 release를 분리한다. 각 근거는 해당 source·contract/profile·environment·artifact에 연결한다. 필요한 실제 환경이 없으면 UNQUALIFIED 또는 PENDING으로 남긴다. 계획 문서의 존재·PR 생성·합성 테스트 성공은 제품 완료가 아니다.

## 신규 작업 상세

### k-current-capability-map — 현재 소스와 전체 프로토콜 요구의 대응표

**배치:** schema-v1 로컬 후보 · **선행:** roadmap-sync · **검토:** A2/NONE

목표: 이미 구현된 것과 새 구현·독립 검증·실환경 확인이 필요한 것을 구분한다.

작업 묶음: 기존 프로그램 완성도

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. original32/TrackK/TrackP/RS/TL/Finance를 source path·contract·fixture로 매핑한다
2. SOURCE_ONLY/MOCK/LOCAL_DURABLE/LOCALNET/운영 근거를 분리한다
3. 중복 항목은 동일 evidence를 연결하고 없는 근거는 명시한다

필수 산출물:
- 현재 capability/coverage register
- 요구별 source와 검증 gap 표

완료 판정/실패 검증:
1. 문서/빈 stub/합성 결과가 운영 완료로 집계되지 않는다
2. 과거 baseline을 새 소스 검증으로 재라벨링하지 않는다
3. 잠금 두 blob을 원래 값과 대조한다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

### k-adversarial-corpus — 계약 중심 경계·순서·수치·재생 corpus

**배치:** schema-v1 로컬 후보 · **선행:** k-current-capability-map, k1-e4-residual-review, k-stage3-schema-sdk-conformance · **검토:** A2/NONE

목표: 기존 계약에서 누락된 반례를 재현 가능한 입력 집합으로 보완한다.

작업 묶음: 기존 프로그램 완성도

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. 중복/역순/늦은 사실/만료/overflow/UNKNOWN을 계약별로 분류한다
2. 충분한 기존 tests는 재사용하고 새 gap에 최소 반례를 추가한다
3. seed와 shrinking/replay 입력을 저장한다

필수 산출물:
- 허용 경로의 adversarial fixtures와 실행 도구
- 불변식별 oracle·분모·결과

완료 판정/실패 검증:
1. 커널 소스와 같은 모델의 일치를 독립 증명으로 부르지 않는다
2. 거절된 명령이 효과를 만들지 않는다
3. 재생 시 첫 결과·지급/권리/재고 의미가 보존된다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

### k-sdk-examples — 독립 클라이언트가 따라 할 수 있는 SDK 여정

**배치:** schema-v1 로컬 후보 · **선행:** p-sdk-1, contract-compatibility-profile · **검토:** A2/NONE

목표: UI 없이도 발행·예약·거래·환불·검표의 계약을 검증한다.

작업 묶음: 기존 프로그램 완성도

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. 현재 producer tuple에 묶인 예제와 불완전 기능의 NOT_BOUND를 제공한다
2. command→receipt→다음 body의 실제 필드 연결을 설명한다
3. 오류/UNKNOWN 이후 금지되는 다음 행동을 예제에 포함한다

필수 산출물:
- TypeScript/CLI 예제와 계약 fixture
- current tuple 확인 명령 및 개발자 문서

완료 판정/실패 검증:
1. 다른 SDK/OpenAPI/gate 버전을 섞으면 호출 전에 거절한다
2. 결제 완료와 권리 발행 완료가 별도 관측으로 남는다
3. 예제에서 실자금·공개 endpoint 기본값이 없다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

### k-benchmark-reproduction — 워크로드·분모·지연·비용 실측 재현

**배치:** schema-v1 로컬 후보 · **선행:** k-stage4-local-exploration, rs-4-l3 · **검토:** A2/NONE

목표: 실패 요청 수나 합성 처리량을 실제 거래 성능으로 오해하지 않게 한다.

작업 묶음: 기존 프로그램 완성도

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. 성공/reject/UNKNOWN·권리 수·명령 수·동시 공연·hot key를 구분한다
2. load seed·환경·backend·chain config·budget을 묶는다
3. 과거 기준과 동등 조건의 차이만 비교한다

필수 산출물:
- 실측 재실행 packet과 보고서 template
- 안전성 중단 조건과 측정 누락 표

완료 판정/실패 검증:
1. RPS와 성공 TPS를 혼합하지 않는다
2. cardinality·보유 권리·누적 이벤트를 같은 규모 숫자로 합산하지 않는다
3. 미정 SLO를 통과 목표로 임의 설정하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

### k-operator-evidence — 개발·대사·복구 작업자의 읽기 전용 진단

**배치:** schema-v1 로컬 후보 · **선행:** read-model-reference, k-stage7-authenticated-export, k-adversarial-corpus · **검토:** A2/NONE

목표: UNKNOWN과 근거 부족을 실제 조회 가능한 사건과 연결한다.

작업 묶음: 기존 프로그램 완성도

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. command/operation/payment/chain/grant identity의 조회 경로를 문서·로컬 도구로 제공한다
2. 시점·source cut·권한·현재성·보존 근거를 함께 표시한다
3. 권위 없는 read가 해소할 수 없는 blocker를 설명한다

필수 산출물:
- 읽기 전용 진단/증거 export 도구
- 정보 누락/오래된 cut/권한 부족 fixtures

완료 판정/실패 검증:
1. 진단 조회가 경제 상태·grant·권리를 변경하지 않는다
2. dump에 자격증명·민감한 원문을 포함하지 않는다
3. UNKNOWN을 timeout만으로 실패/성공 처리하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

### k-local-program-closeout — 기존 로컬 프로그램과 보완 작업의 완료 근거

**배치:** schema-v1 로컬 후보 · **선행:** k-current-capability-map, k-adversarial-corpus, k-sdk-examples, k-benchmark-reproduction, k-operator-evidence · **검토:** A2/NONE

목표: 기존 구현 범위의 source delivery를 검토 가능한 단위로 인계한다.

작업 묶음: 기존 프로그램 완성도

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. 범위별 current-head tests/독립 검토/실환경 여부를 묶는다
2. 잠금·미정 입력·pending catalogue와 장기 확장을 연결한다
3. provider·권위·실자금 미완료를 완료율에서 숨기지 않는다

필수 산출물:
- local delivery packet과 gap-to-node 지도
- 설치/검증/다음 계획 개정 안내

완료 판정/실패 검증:
1. 모든 pending을 완료 분모에서 조용히 제거하지 않는다
2. Finance 부분집합은 한 번만 센다
3. 운영 활성화·kernel unlock·A3 PASS를 합성하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

### ps-01-routing-authority — 공연·페이지·cell·shard·epoch의 경합 단위 계약

**배치:** pending catalogue · **선행:** rs-0, k-onsale-admission-control · **검토:** A3/ARCHITECTURE

목표: 100만~3,000만 플랫폼 권리를 단일 공연 슬롯 수와 분리하여 설계한다.

작업 묶음: 대규모 권리·거래 플랫폼

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #85 f931cfc87bdeaa1ed2495df0ce659ee832ac1c33 docs/blueprints/platform-scale-v1/{README,DELIVERY_PLAN}.md (미병합, 구현/채택 증거 아님)

구현 범위:
1. Show/InventoryPage/ExecutionCell/PlacementVersion 식별과 권위를 구분한다
2. 특정 좌석·GA·리셀 매물의 경합 키와 세대를 정의한다
3. 공연당 65,536 후보·페이지 크기·플랫폼 총량의 의미를 분리한다

필수 산출물:
- 라우팅/권위 ADR와 수용 vectors
- 기존 16슬롯 legacy 및 신규 RS profile 호환표

완료 판정/실패 검증:
1. 플랫폼 총량이 단일 객체·전역 mutex·브라우저 전체 다운로드를 요구하지 않는다
2. route epoch가 chain generation을 대신하지 않는다
3. #84 localnet 증거를 운영 확장 증거로 해석하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #84/#85의 해당 계약이 실제 채택되고 RS/TrackK 선행의 현재 증거가 확인되어야 한다. 구현 노드는 승인 backend·독립 A3·새 계획 개정을 추가로 요구한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### ps-02-query-contract — 조회·검색·snapshot·delta·재생 계약

**배치:** pending catalogue · **선행:** ps-01-routing-authority, read-model-contract, k-stage7-authenticated-export · **검토:** A3/ARCHITECTURE

목표: 크게 늘어나는 권리·매물을 권위와 시점을 보존하며 조회한다.

작업 묶음: 대규모 권리·거래 플랫폼

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #85 f931cfc87bdeaa1ed2495df0ce659ee832ac1c33 docs/blueprints/platform-scale-v1/{README,DELIVERY_PLAN}.md (미병합, 구현/채택 증거 아님)

구현 범위:
1. 인덱스 watermark/source cut/gap/cursor/tenant scope를 정의한다
2. 요약→페이지→권리 상세의 bounded read 계약을 만든다
3. 중복·역순·재구축·cross-shard cut의 표현을 고정한다

필수 산출물:
- 조회 투영/검색 계약과 SDK fixture 후보
- gap/rebuild/stale cursor 벡터

완료 판정/실패 검증:
1. 검색 hit가 구매·검표·지급 권한을 만들지 않는다
2. cursor vector만으로 전역 원자 snapshot을 주장하지 않는다
3. 권한 필터 누락과 다른 tenant cursor 재사용을 거절한다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #84/#85의 해당 계약이 실제 채택되고 RS/TrackK 선행의 현재 증거가 확인되어야 한다. 구현 노드는 승인 backend·독립 A3·새 계획 개정을 추가로 요구한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### ps-03-resale-contract — 다중 채널 리셀·조건부 체결·자금 대사

**배치:** pending catalogue · **선행:** ps-01-routing-authority, booking-resale-admission-deepening, settlement-policy-deepening · **검토:** A3/ARCHITECTURE

목표: 여러 채널의 동일 권리 판매 경쟁을 한 경제적 체결로 연결한다.

작업 묶음: 대규모 권리·거래 플랫폼

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #85 f931cfc87bdeaa1ed2495df0ce659ee832ac1c33 docs/blueprints/platform-scale-v1/{README,DELIVERY_PLAN}.md (미병합, 구현/채택 증거 아님)

구현 범위:
1. 매물/hold/체결/결제/권리 이전을 별도 state로 정의한다
2. 가격 변경·양도·환불·기한·동시 체결의 first-result를 정한다
3. 지급 응답 유실 뒤 대사와 새 체결 차단을 명시한다

필수 산출물:
- 리셀 거래 ADR·순서 경합 vectors
- producer/consumer 필드 연결 명세

완료 판정/실패 검증:
1. 같은 권리를 두 채널에서 동시에 확정 판매하지 않는다
2. HTTP timeout이 결제 취소나 권리 미이전을 뜻하지 않는다
3. unsupported 가격/수수료 정책을 임의 채우지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #84/#85의 해당 계약이 실제 채택되고 RS/TrackK 선행의 현재 증거가 확인되어야 한다. 구현 노드는 승인 backend·독립 A3·새 계획 개정을 추가로 요구한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### ps-04-execution-partitions — 승인 backend의 실행 partition·입출력·fencing

**배치:** pending catalogue · **선행:** ps-01-routing-authority, k-stage5-durable-tx, k1-cut-proof, rs-3b · **검토:** A3/ARCHITECTURE

목표: 기존 경제 writer를 승인된 저장 기반의 partition에서 안전하게 실행한다.

작업 묶음: 대규모 권리·거래 플랫폼

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #85 f931cfc87bdeaa1ed2495df0ce659ee832ac1c33 docs/blueprints/platform-scale-v1/{README,DELIVERY_PLAN}.md (미병합, 구현/채택 증거 아님)

구현 범위:
1. 원자 범위별 first result/inbox/outbox·backpressure를 구현한다
2. 신규 소비 차단→cut→옛 writer 차단→새 epoch의 이전을 검증한다
3. 늦은 사실과 UNKNOWN을 이동 중에도 보존한다

필수 산출물:
- 채택 backend 기반 partition 구현
- crash/동시 writer/늦은 결과 fault suite

완료 판정/실패 검증:
1. 차단을 증명하지 못하면 writer를 승격하지 않는다
2. local commit을 은행·체인 원자 커밋으로 주장하지 않는다
3. 자체 consensus/복제/log engine을 새로 만들지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #84/#85의 해당 계약이 실제 채택되고 RS/TrackK 선행의 현재 증거가 확인되어야 한다. 구현 노드는 승인 backend·독립 A3·새 계획 개정을 추가로 요구한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### ps-05-query-projections — 권리·매물 조회 투영과 versioned SDK

**배치:** pending catalogue · **선행:** ps-02-query-contract, ps-04-execution-partitions, contract-compatibility-profile · **검토:** A3/ARCHITECTURE

목표: 큰 데이터셋에서도 갱신 근거와 stale을 추적할 수 있는 조회를 제공한다.

작업 묶음: 대규모 권리·거래 플랫폼

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #85 f931cfc87bdeaa1ed2495df0ce659ee832ac1c33 docs/blueprints/platform-scale-v1/{README,DELIVERY_PLAN}.md (미병합, 구현/채택 증거 아님)

구현 범위:
1. 승인된 source event에서 projection·index를 재구축한다
2. bounded cursor·permission filter·delta gap 복구를 구현한다
3. schema/OpenAPI/SDK/manifest/vectors를 같은 소스로 갱신한다

필수 산출물:
- local projection/index와 query SDK
- 재구축·중복·역순·권한 경계 적합성 결과

완료 판정/실패 검증:
1. projection을 경제 writer나 원권리 정본으로 바꾸지 않는다
2. source cut이 다른 페이지를 단일 확정 시점으로 합치지 않는다
3. producer tuple 변경이 consumer에서 검출된다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #84/#85의 해당 계약이 실제 채택되고 RS/TrackK 선행의 현재 증거가 확인되어야 한다. 구현 노드는 승인 backend·독립 A3·새 계획 개정을 추가로 요구한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### ps-06-admission-load — 대기열·과부하·공정성·복구 자원 예산

**배치:** pending catalogue · **선행:** ps-04-execution-partitions, ps-05-query-projections, k-onsale-admission-control · **검토:** A3/ARCHITECTURE

목표: 동시 판매 집중에도 환불·관측·복구가 굶지 않는 입장 제어를 검증한다.

작업 묶음: 대규모 권리·거래 플랫폼

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #85 f931cfc87bdeaa1ed2495df0ce659ee832ac1c33 docs/blueprints/platform-scale-v1/{README,DELIVERY_PLAN}.md (미병합, 구현/채택 증거 아님)

구현 범위:
1. 공연/cell/provider별 요청·bytes·backlog와 admission budget을 둔다
2. queue token을 epoch/scope/nonce/expiry/key-version에 결합한다
3. 관측·취소·환불에 예약 자원을 두고 telemetry cardinality를 제한한다

필수 산출물:
- admission/backpressure 구현과 부하 재현
- 공정성·token replay·expiry·hot-key 보고서

완료 판정/실패 검증:
1. 재발급이 순번 점프나 이중 입장을 만들지 않는다
2. 부하 거절이 권리·지급 상태를 임의 변경하지 않는다
3. queue token을 권리 소유·결제 완료로 표시하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #84/#85의 해당 계약이 실제 채택되고 RS/TrackK 선행의 현재 증거가 확인되어야 한다. 구현 노드는 승인 backend·독립 A3·새 계획 개정을 추가로 요구한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### ps-07-scale-qualification — 100만→1,000만→3,000만 규모의 단계별 증거

**배치:** pending catalogue · **선행:** ps-03-resale-contract, ps-05-query-projections, ps-06-admission-load, k-benchmark-reproduction · **검토:** A3/ARCHITECTURE

목표: 목표 용량을 숫자 약속 대신 경로별 실제 검증으로 바꾼다.

작업 묶음: 대규모 권리·거래 플랫폼

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #85 f931cfc87bdeaa1ed2495df0ce659ee832ac1c33 docs/blueprints/platform-scale-v1/{README,DELIVERY_PLAN}.md (미병합, 구현/채택 증거 아님)

구현 범위:
1. workload profile S1/S2/S3의 권리·매물·명령·분포를 고정한다
2. hot key/실패/복구/인덱스 lag/비용을 경로별로 측정한다
3. Commerce 연결의 UNKNOWN·경합·stale 검증을 포함한다

필수 산출물:
- 단계별 source/env/workload/분모 보고서
- 보존식·TPS/지연·backlog·복구·비용 evidence

완료 판정/실패 검증:
1. 하위 단계 안전성 실패 시 상위 부하로 진입하지 않는다
2. 합성 index 처리량을 체인 실거래 처리량으로 표시하지 않는다
3. 미정 SLO는 측정치만 보고하고 수용은 보류한다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #84/#85의 해당 계약이 실제 채택되고 RS/TrackK 선행의 현재 증거가 확인되어야 한다. 구현 노드는 승인 backend·독립 A3·새 계획 개정을 추가로 요구한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

외부 선행: BeautifulMind-JT/kix-commerce-apps / kixc/c-platform-journey

### cr-01-product-authority — 여신 상품·주체·권위·정책 버전 계약

**배치:** pending catalogue · **선행:** f04-mock-deepening, fin-ledger-contract, f04-real-funds-lift-criteria · **검토:** A3/ARCHITECTURE

목표: 정산채권 기반 선지급의 대주·차주·정책·증거 권위를 먼저 확정한다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. 사업자 선지급/반복 한도/제작 자금/소비자 후불/재고 금융을 별도 범위로 둔다
2. Party/Relationship/ProductPolicy와 채택/만료 규칙을 정의한다
3. 기존 FACE_SNAPSHOT_FROZEN·DEFAULTED terminal을 보존한다

필수 산출물:
- 여신 lifecycle ADR와 정책 미정 입력표
- 구/신 profile 호환·migration vectors

완료 판정/실패 검증:
1. 티켓 소유·매물·판매총액이 현금/담보 완성으로 승격되지 않는다
2. 금리·수수료·기간·담보 효력을 임의 결정하지 않는다
3. 토큰 발행이 여신 선행으로 강제되지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### cr-02-claim-eligibility — 채권 적격성·borrowing base·중복 사용 통제

**배치:** pending catalogue · **선행:** cr-01-product-authority, fin-credit-exposure-reconciliation · **검토:** A3/ARCHITECTURE

목표: 확인 가능한 정산 의무와 부담을 기반으로 사용 가능한 채권 범위를 계산한다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. ClaimEvidence/source cut/귀속/기한/환불 부담/양도 확인을 고정한다
2. claim slice와 평가 revision으로 중복 사용을 막는다
3. 재평가 부족·만료·취소 시 신규 draw와 기존 노출을 구분한다

필수 산출물:
- 적격성 계약과 합성 평가 모형
- 중복 slice·stale evidence·deficit vectors

완료 판정/실패 검증:
1. 불확실한 소유/부담은 적격으로 처리하지 않는다
2. 같은 claim이 여러 facility에 이중 담보로 계산되지 않는다
3. 재평가 감소가 기존 채무를 임의 소멸시키지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### cr-03-facility-reservations — 약정·공유 한도·재원 원자 예약

**배치:** pending catalogue · **선행:** cr-02-claim-eligibility, k-stage5-durable-tx, k-stage6-economics-reference · **검토:** A3/ARCHITECTURE

목표: 인출 하나가 차주·관계자·상품·포트폴리오·재원 한도를 함께 지킨다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. facility/draw/commitment의 identity와 사용 가능량을 정의한다
2. 동일 원자 범위에서 공유 한도·재원을 예약한다
3. UNKNOWN 지급과 정책별 재인출·해제 조건을 보존한다

필수 산출물:
- 승인 backend의 합성 reservation 구현
- 경쟁 인출·crash·공유 한도 보존식 tests

완료 판정/실패 검증:
1. 각 한도가 따로 성공하여 총량을 초과하지 않는다
2. cash 관측이나 부분 repay가 미채택 회전 한도를 만들지 않는다
3. UNKNOWN의 예약을 timeout만으로 해제하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### cr-04-underwriting-consent — 심사·동의·이유·예외 승인·정책 변경

**배치:** pending catalogue · **선행:** cr-01-product-authority, protocol-canonical-identity-conformance · **검토:** A3/ARCHITECTURE

목표: 판단 입력과 결정 근거가 재현되며 권한과 만료가 유지된다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. 입력 출처/snapshot·모델/규칙 revision·판단 시점·이유를 기록한다
2. 동의 철회·자료 만료·추가 자료·override의 근거를 관리한다
3. maker/checker와 수취계좌 변경 권한을 정의한다

필수 산출물:
- versioned 심사/동의 contract와 합성 decision 서비스
- 만료·변조·권한 분리·override fixtures

완료 판정/실패 검증:
1. LLM 요약이 한도 승인·담보 판정·자금 송신 권한이 되지 않는다
2. 현재 자료와 다른 revision의 동의를 재사용하지 않는다
3. 거절 사유를 재현하되 비공개 민감 자료를 무단 공개하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### cr-05-disbursement-observation — 지급 지시·외부 관측·UNKNOWN·복구

**배치:** pending catalogue · **선행:** cr-03-facility-reservations, cr-04-underwriting-consent, k1-adapter-event-identity, fin-observation-reconciliation · **검토:** A3/ARCHITECTURE

목표: 인출 승인과 실제 지급 결과를 구별하고 중복 지급을 방지한다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. 승인된 draw의 outbox와 제공자 관측 inbox를 기존 기반에 연결한다
2. 제공자 identity/계좌 revision/최초 결과를 보존한다
3. 지시 뒤 응답 유실·늦은 지급·중복 관측을 합성 대사한다

필수 산출물:
- 합성 rail adapter와 지급 대사 상태기계
- 중단/거절/부분 관측/late success fault corpus

완료 판정/실패 검증:
1. DB commit을 실제 송금 완료로 표시하지 않는다
2. 관측이 불명확하면 새 지급을 재제출하지 않는다
3. 변경된 수취계좌가 오래된 승인에 묵시 반영되지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### cr-06-repayment-allocation — 상환표·입금 배분·미식별 입금·조정

**배치:** pending catalogue · **선행:** cr-05-disbursement-observation, fin-double-entry-projection, fin-multi-payee-refund-proof · **검토:** A3/ARCHITECTURE

목표: 상환과 비용·원금·이자·미배분금을 정책에 따라 보존한다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. 정수/rational·반올림·기산·정책 revision을 명시한다
2. receipt마다 원금/이자/비용/suspense/reversal을 기록한다
3. 중도/부분/과입금·회수 취소·정책 변경을 재생한다

필수 산출물:
- 합성 상환 schedule와 allocation 모델
- 독립 산술 vectors와 보존식 tests

완료 판정/실패 검증:
1. 수령액=배분액+미배분액이라는 보존식을 지킨다
2. 동일 입금을 여러 번 상환에 반영하지 않는다
3. 미정 금융 조건을 운영 기본값으로 넣지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### cr-07-delinquency-recovery — 연체·조정·회수·상각·후기 입금

**배치:** pending catalogue · **선행:** cr-06-repayment-allocation, fin-credit-exposure-reconciliation, fin-consistent-accounting-export · **검토:** A3/ARCHITECTURE

목표: 채무 상태와 회계 손실·운영 case를 분리해 끝까지 추적한다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. 연체 구간·약정 변경·회수 case·상각·면제의 별도 권위를 정의한다
2. 후기 입금·취소·반환 의무를 기존 사실에 연결한다
3. 보존/접근/개인정보와 승인 근거를 관리한다

필수 산출물:
- servicing 합성 모델과 사건 연표
- 종결 후 사실·조정 reversal·late recovery tests

완료 판정/실패 검증:
1. 상각이 채무 소멸이나 담보 자동 처분을 의미하지 않는다
2. 기존 DEFAULTED terminal을 조용히 재개하지 않는다
3. 모형이 외부 추심 연락·법적 절차·실계좌 거래를 실행하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### cr-08-producer-sdk — 여신 producer 계약·query·SDK 적합성

**배치:** pending catalogue · **선행:** cr-02-claim-eligibility, cr-03-facility-reservations, cr-04-underwriting-consent, cr-05-disbursement-observation, cr-06-repayment-allocation, cr-07-delinquency-recovery, fin-catalogue-read-model, contract-compatibility-profile · **검토:** A3/ARCHITECTURE

목표: Commerce가 임의 금융 계산 없이 정확한 여신 상태를 소비하게 한다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. 승인 command/query의 schema·상태·reason·source cut을 게시한다
2. 기존 compatibility 절차로 SDK/manifest/vectors를 재생성한다
3. actor/scope/profile/revision 불일치를 호출 전에 거절한다

필수 산출물:
- 여신 catalogue/SDK/compatibility tuple
- consumer용 정상/거절/STALE/UNKNOWN fixtures

완료 판정/실패 검증:
1. 옛 F04 tuple을 새 여신 API 자격으로 재사용하지 않는다
2. source/SDK/manifest/vector가 섞이면 fail-closed다
3. UI 계산을 경제 원장으로 만드는 필드가 없다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### cr-10-credit-qualification — 여신 전체 여정·스트레스·합성 수용

**배치:** pending catalogue · **선행:** cr-08-producer-sdk · **검토:** A3/ARCHITECTURE

목표: 채권 확인부터 인출·상환·연체·회수까지 producer/consumer로 검증한다.

작업 묶음: 여신 전체 수명

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md; 설계 후보 PR #86 0846e4ddf1d55cc4ac619e2c350c4e3574547bda docs/blueprints/credit-lifecycle-v1/{README,LIFECYCLE,DELIVERY_PLAN}.md (미병합, 상품 승인 아님)

구현 범위:
1. 동시 draw·환불 부담·지급 유실·재평가 부족·상환 역순·후기 회수를 실행한다
2. 차주/관계자/재원별 노출 보존식을 검사한다
3. code/합성 수용/실제 상품/실자금 권한을 별도로 보고한다

필수 산출물:
- 여신 전체 current tuple의 통합 보고서
- 정책별 미정 입력·위반·미실행 경로

완료 판정/실패 검증:
1. 초기 SDK PASS가 이후 변경 여신 버전을 승인하지 않는다
2. finance closeout과 consumer의 순환 선행이 없다
3. 합성 성공으로 실대출·신용 결정·은행 연결을 활성화하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: PR #86 여신 계약과 해당 상품/정책 revision을 별도로 채택한 뒤 승격한다. 구현은 승인 backend 및 TrackK 경제 전이 선행을 요구하며 모든 개발 fixture는 SYNTHETIC_UNIT이다. 실자금·심사 제공자·법적 효력은 별도 권한/근거 없이는 활성화하지 않는다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

외부 선행: BeautifulMind-JT/kix-commerce-apps / kixc/c-credit-servicing-journey

### k-provider-sandbox — PG·은행·KYC 제공자 sandbox 적합성

**배치:** pending catalogue · **선행:** toss-sandbox-conformance-plan, k1-adapter-event-identity, public-endpoint-readiness-plan · **검토:** A3/ARCHITECTURE

목표: 승인된 테스트 계정 범위에서 실제 제공자 계약과 어댑터 의미를 확인한다.

작업 묶음: 외부 자격과 운영 준비

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. 선택 제공자·계약/MID별 권한·서명·금액·이벤트 identity를 검증한다
2. replay/역순/응답 유실/키 교체/금지 환경 호출을 시험한다
3. 제한된 test credential의 보관·삭제·감사 경로를 확인한다

필수 산출물:
- 제공자별 실제 sandbox qualification
- 어댑터 사건/경제 효과 대사 결과

완료 판정/실패 검증:
1. 공개 문서만으로 실제 계약 기능 지원을 단정하지 않는다
2. 실제 계정 부재는 fake 결과와 분리한다
3. sandbox 성공이 production 자금·KYC 허가를 만들지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: 계약/제공자 scope와 sandbox 계정 사용 승인이 확인된 뒤 새 계획 개정으로 승격한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### k-authority-qualification — 체인 위임·회수·backend writer의 실제 자격

**배치:** pending catalogue · **선행:** ps-07-scale-qualification, ai-delegation-execution-decision, testnet-key-management-decision, rs-5-decision · **검토:** A3/ARCHITECTURE

목표: 정의된 체인/키/backend 범위에서 권위 이전과 늦은 사실 보존을 입증한다.

작업 묶음: 외부 자격과 운영 준비

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. grant generation/C_g/H_g·현재성·키 교체·비협조 writer를 시험한다
2. 체인 관측과 DB commit 위치를 별도로 대사한다
3. 승인된 testnet 등 정확한 환경에서 실패·회수·재개를 검증한다

필수 산출물:
- 환경별 grant/fencing qualification packet
- 미확정 권위에서 실행 차단 증거

완료 판정/실패 검증:
1. 로컬 PID 종료가 분산 writer fencing을 대신하지 않는다
2. 체인 재조직/관측 지연을 local sequence로 덮지 않는다
3. 실제 환경 미검증을 current authority PASS로 표시하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: testnet/키 관리/위임/backend의 개별 unlock과 host 자격을 확인한 뒤 승격한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### k-token-platform-contract — 선택적 토큰과 리워드·거래의 연결 자격

**배치:** pending catalogue · **선행:** tl-4, tl-5-decision, ps-03-resale-contract · **검토:** A3/ARCHITECTURE

목표: 토큰을 선택적 확장으로 유지하면서 거래·환불·리워드의 경계를 검증한다.

작업 묶음: 외부 자격과 운영 준비

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. 공급·권한·가격 source·리워드 eligibility와 경제 거래 coupling을 대조한다
2. 환불/취소/부분 이행/소급 정정 시 중복 리워드를 검증한다
3. 토큰 없는 기본 경로와 독립 비교한다

필수 산출물:
- 선택적 토큰 통합 계약/합성 vectors
- 공급/리워드/환불 보존식과 운영 미정 표

완료 판정/실패 검증:
1. 발행·상장·가격·수익을 자동 보장하지 않는다
2. 일반 거래가 토큰 발행을 필수로 요구하지 않는다
3. coin lock 및 실제 발행 권한을 계획으로 우회하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: 상세 계약 채택·정확한 소스의 독립 검토·범위별 실제 환경 자격 확인 뒤 계획 개정으로 승격한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### k-operator-contract — 플랫폼 운영·권한·감사·장애 대응 계약

**배치:** pending catalogue · **선행:** k-operator-evidence, ps-06-admission-load, cr-08-producer-sdk · **검토:** A3/ARCHITECTURE

목표: 운영자가 큰 플랫폼의 상태를 보고 권한 있는 조치를 수행할 계약을 만든다.

작업 묶음: 외부 자격과 운영 준비

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. tenant/운영자/금융/감사자별 읽기·제안·실행 권한을 분리한다
2. maker/checker·비상중지·보존·민감정보 export를 정의한다
3. 운영 조치와 원래 경제 사실의 audit trail을 결합한다

필수 산출물:
- 운영자 command/query 계약과 SDK 후보
- privilege escalation·stale decision·감사 누락 vectors

완료 판정/실패 검증:
1. read console이 새 자금 writer가 되지 않는다
2. 운영자 편의를 위해 UNKNOWN과 보존 사실을 삭제하지 않는다
3. 실제 운영 SLO/보존 정책 미정을 임의 채택하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: 상세 계약 채택·정확한 소스의 독립 검토·범위별 실제 환경 자격 확인 뒤 계획 개정으로 승격한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

### k-platform-release — 대규모 프로토콜·금융·체인 운영 인계

**배치:** pending catalogue · **선행:** k-local-program-closeout, protocol-integration-evidence-closeout, cr-10-credit-qualification, k-provider-sandbox, k-authority-qualification, k-token-platform-contract, k-operator-contract · **검토:** A3/RELEASE

목표: 선택한 서비스 범위의 구현·독립 검토·실환경·운영 승인을 함께 검수한다.

작업 묶음: 출시와 운영

설계 근거: docs/DEVELOPMENT_PLAN.md; docs/decisions/AUTHORITY_MODEL_1.md; docs/aiops/PROTOCOL_COMPLETION_DESIGN_KO.md; docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md; docs/aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md

구현 범위:
1. producer/consumer version과 현재 권한·chain/backend/provider tuple을 고정한다
2. 성능·보존·장애·운영·보안·금융 미해결을 scope별 집계한다
3. 배포/되돌리기/지원/키 rotation과 최종 결정을 준비한다

필수 산출물:
- 현재 source의 release readiness packet
- 서비스 범위별 승인/보류/연기 지도

완료 판정/실패 검증:
1. 운영 거절·UNKNOWN·복구 경로가 빠지면 완료되지 않는다
2. 선택적 토큰 운영 보류를 기본 서비스 강제 발행으로 바꾸지 않는다
3. User RELEASE 결정 전 운영 자금·공개 활성화를 하지 않는다

공통 경계: 잠금 kernel 두 blob과 reference/v0.3-rc1 기준선을 보존한다. 모델1의 체인 권위/위임 실행/자금 관측을 분리한다. 새 backend·수명·권위·상품 정책은 선행 채택 없이는 구현하지 않는다. R2/자체 합의·복제·로그 엔진을 만들지 않는다. 합성 금액과 localnet은 실자금/운영 규모 증거가 아니다. 실 PG·은행·KYC·testnet/mainnet·토큰 운영은 별도 unlock이 필요하다.

증거/인계: 실제 변경 파일·실행 명령·성공 및 실패 사례·정확한 소스 SHA를 PR에 남긴다. 기존 충분한 coverage는 재사용하고 새 gap만 검증한다. UI 변경은 실제 브라우저의 정상/빈 값/오류/진행 중 화면과 키보드 동작을 확인한다. 실환경 부재는 미검증으로 남긴다. 독립 검토 지적과 CI 실패는 같은 소유자가 수정하고 변경 HEAD를 다시 검토한다. 일반 구현 선택은 자율 결정하며 계정·중요 계약·실사용 승인만 구체적인 결정을 요청한다.

승격 조건: 상세 계약 채택·정확한 소스의 독립 검토·범위별 실제 환경 자격 확인 뒤 계획 개정으로 승격한다. 이 항목은 pending catalogue이며 현재 schema-v1 dispatch 대상이 아니다. depends_on_external을 spec 문장으로 바꾸거나 삭제하여 우회하지 않는다.

외부 선행: BeautifulMind-JT/kix-commerce-apps / kixc/c-platform-operational-qualification

## 2026-10-02 대규모·여신 설계 출처

- [권리 확장 #84](https://github.com/BeautifulMind-JT/kix-protocol/pull/84), [플랫폼 규모 #85](https://github.com/BeautifulMind-JT/kix-protocol/pull/85), [여신 lifecycle #86](https://github.com/BeautifulMind-JT/kix-protocol/pull/86)는 관측 시 미병합 후보다.
- 읽은 합성 설계 source: `0846e4ddf1d55cc4ac619e2c350c4e3574547bda`. [플랫폼 상세](https://github.com/BeautifulMind-JT/kix-protocol/blob/0846e4ddf1d55cc4ac619e2c350c4e3574547bda/docs/blueprints/platform-scale-v1/README.md), [여신 상세](https://github.com/BeautifulMind-JT/kix-protocol/blob/0846e4ddf1d55cc4ac619e2c350c4e3574547bda/docs/blueprints/credit-lifecycle-v1/README.md).
- PS/CR 추적 ID를 새 노드에 대응하되 기존 RS/Finance/F04 구현을 새로 완성된 것으로 세지 않는다. producer→consumer→통합검증 방향을 유지하고 최종 closeout을 producer 자체의 선행으로 역참조하지 않는다.

## 전체 작업 색인

| ID | 작업 | 배치 | 선행 |
|---|---|---|---|
| roadmap-sync | Reflect the approved roadmap into DEVELOPMENT_PLAN, README, AGENTS and the task index | local candidate | 없음 |
| agents-scope-sync | Reflect the roadmap's approved scope into AGENTS.md §5 | local candidate | 없음 |
| sui-commit-mismatch-note | Record why two Sui framework commits appear in the docs | local candidate | 없음 |
| p-sdk-0 | P-SDK-0: TypeScript 0.x client from the contract-only OpenAPI, with conformance tests | local candidate | 없음 |
| openapi-catalogue-promotion | Promote settlement, booking, resale, admission and credit commands into the contract-only OpenAPI catalogue | local candidate | p-sdk-0 |
| move-primary-price-fee | Define primary issuance price and fee for the Move rights module | local candidate | 없음 |
| ai-delegation-contract-mock | AI delegation authority contract draft and in-memory mock | local candidate | 없음 |
| readiness-extensions | Extend the readiness journal inside the D-3 bounds | local candidate | p-sdk-0 |
| settlement-policy-deepening | Settlement contract §7: turn the open policy items into a decided draft revision | local candidate | p-sdk-0 |
| booking-resale-admission-deepening | Booking/resale/admission contract §7: decide the open items as a draft revision | local candidate | p-sdk-0 |
| f04-mock-deepening | F04 credit contract: product terms for the mock | local candidate | p-sdk-0 |
| toss-method-expansion-review | Review easy-pay and virtual accounts inside the Toss profile (document only) | local candidate | 없음 |
| gate-browser-access-decision | Decide how the commerce browser may reach the loopback gate (CORS) | local candidate | 없음 |
| gate-browser-access | Implement the chosen browser access option in the loopback gate | local candidate | gate-browser-access-decision, p-sdk-0 |
| read-model-contract | Read and list query contract for commerce surfaces | local candidate | 없음 |
| read-model-reference | Implement the approved read queries and add them to the catalogue | local candidate | read-model-contract, openapi-catalogue-promotion |
| p-sdk-1 | P-SDK-1: regenerate the TypeScript 0.x client for the full catalogue | local candidate | openapi-catalogue-promotion, read-model-reference |
| k1-e4-residual-review | First batch: residual review of the E-4 model and contract invariants | local candidate | 없음 |
| k1-adapter-event-identity | I06: design adapter transmission, event, payment and operation identities (document only) | local candidate | 없음 |
| k1-cut-proof | I12: technical proof of the C_g/H_g cut and old-writer fencing | local candidate | 없음 |
| k1-open-inputs-brief | Ready-to-send question sheets for the open first-batch inputs | local candidate | 없음 |
| k1-evidence-close | First batch: integration review and evidence close-out | local candidate | k1-e4-residual-review, k1-adapter-event-identity |
| k-stage2-v5-design-decision | Track K stage 2: v5 crate design decision proposal (document only) | local candidate | 없음 |
| k-stage2-v5-impl | Track K stage 2: implement the lifecycle transitions in the v5 crate | local candidate | k-stage2-v5-design-decision |
| k2-retention-proposal | Retention periods proposal (legal, reconciliation, retry support, memory) | local candidate | 없음 |
| k-stage3-schema-sdk-conformance | Track K stage 3: schema and SDK conformance | local candidate | p-sdk-1 |
| k-stage4-comparison-plan | Track K stage 4: backend comparison plan and candidate screening | local candidate | 없음 |
| k-readiness-conformance-suite | Split the readiness fault suite into a backend-common conformance test | local candidate | 없음 |
| k-stage4-local-exploration | Track K stage 4: local exploratory measurement under equal conditions | local candidate | k-stage4-comparison-plan, k-readiness-conformance-suite |
| k-stage4-adoption-decision | Track K stage 4: backend adoption decision proposal | local candidate | k-stage4-local-exploration |
| k-stage5-durable-tx | Track K stage 5: durable transactions on the adopted backend (local, non-production) | local candidate | k-stage4-adoption-decision, k-stage2-v5-impl |
| k-onsale-admission-control | On-sale admission control: waiting room and GA routing | local candidate | k-stage5-durable-tx |
| k-stage6-economics-reference | Track K stage 6: economics as a reference model with synthetic money | local candidate | k-stage5-durable-tx, settlement-policy-deepening, booking-resale-admission-deepening |
| k-stage7-authenticated-export | Track K stage 7: authenticated, consistent export | local candidate | k-stage5-durable-tx |
| k-stage7-cpu-analytics-sql-audit | Track K stage 7: CPU analytics semantics audit (Polars, DuckDB) | local candidate | k-stage7-authenticated-export |
| k-stage8-gpu-plan | Track K stage 8: native GPU path plan (document only) | local candidate | k-stage7-cpu-analytics-sql-audit |
| k-a-reestimate | Re-estimate integration (a) of the PR #11 journal | local candidate | k1-evidence-close |
| k-a-integration-decision | Integration (a) decision proposal | local candidate | k-a-reestimate |
| rs-0 | RS-0: rights-scale object and inventory authority design | local candidate | 없음 |
| rs-1 | RS-1: public path on the new profile at 1,024 slots (localnet) | local candidate | rs-0 |
| rs-1-issuercap-probe | RS-1 probe: does concurrent IssuerCap use by reference serialize? | local candidate | rs-1 |
| rs-2 | RS-2: private path (root rules, new circuit, verifier, manifest v2) | local candidate | rs-1 |
| rs-3a | RS-3a: on-chain delegation primitives (page-level grant, GrantControl, revocation cut) | local candidate | rs-1 |
| rs-3b | RS-3b: Rust delegated execution integration (new crate) | local candidate | rs-3a, k-stage2-v5-impl |
| rs-4-l1 | RS-4 L1: staged load validation at 1,024 slots | local candidate | rs-1, rs-2, rs-3a |
| rs-4-l2 | RS-4 L2: staged load validation at 16,384 slots | local candidate | rs-4-l1 |
| rs-4-l3 | RS-4 L3: staged load validation at 65,536 slots with concurrent shows | local candidate | rs-4-l2 |
| testnet-key-management-decision | Sui testnet key management decision proposal | local candidate | rs-1 |
| rs-5-decision | RS-5: operational adoption decision proposal | local candidate | rs-4-l3, rs-1-issuercap-probe, testnet-key-management-decision |
| tl-a | TL-A: token layer scope-and-limits ADR | local candidate | 없음 |
| tl-0 | TL-0: token role and supply contract | local candidate | tl-a |
| tl-price-source-contract | Token price source contract (only if TL-0 needs conversion) | local candidate | tl-0 |
| tl-1 | TL-1: token authority and lifecycle contract | local candidate | tl-0 |
| tl-coin-lock-adr | ADR requesting the Astra re-ruling to lift the coin/TIX lock for a localnet package | local candidate | tl-0, tl-1 |
| tl-2 | TL-2: non-production token package on localnet | local candidate | tl-coin-lock-adr |
| tl-3-offchain | TL-3 off-chain: reward-transaction coupling in a reference model | local candidate | tl-1 |
| tl-3-onchain | TL-3 on-chain: reward records on localnet | local candidate | tl-2, tl-3-offchain |
| tl-4 | TL-4: independent verification of the token layer | local candidate | tl-2, tl-3-onchain |
| tl-legal-brief | Brief for external legal, accounting, tax and finance review | local candidate | tl-0 |
| tl-5-decision | TL-5: operational activation decision proposal | local candidate | tl-4, tl-legal-brief |
| ai-delegation-execution-decision | Decision proposal for enabling delegated execution | local candidate | ai-delegation-contract-mock, rs-3a, rs-3b |
| f04-real-funds-lift-criteria | Criteria for lifting real credit (document only) | local candidate | f04-mock-deepening |
| toss-sandbox-conformance-plan | Plan for Toss sandbox conformance evidence (document only) | local candidate | k1-adapter-event-identity, toss-method-expansion-review |
| public-endpoint-readiness-plan | Plan for the public endpoint unlock (document only) | local candidate | 없음 |
| sdk-1-0-decision | Decision proposal for a stable schema/SDK 1.0 and publishing | local candidate | k-stage3-schema-sdk-conformance |
| ktx-kix-rename-plan | Plan for the bulk KTX to KIX rename (document only) | local candidate | k-stage3-schema-sdk-conformance |
| contract-compatibility-profile | Verify the immutable contract/gate/SDK compatibility profile | local candidate | p-sdk-1, k-stage3-schema-sdk-conformance |
| k-current-capability-map | 현재 소스와 전체 프로토콜 요구의 대응표 | local candidate | roadmap-sync |
| k-adversarial-corpus | 계약 중심 경계·순서·수치·재생 corpus | local candidate | k-current-capability-map, k1-e4-residual-review, k-stage3-schema-sdk-conformance |
| k-sdk-examples | 독립 클라이언트가 따라 할 수 있는 SDK 여정 | local candidate | p-sdk-1, contract-compatibility-profile |
| k-benchmark-reproduction | 워크로드·분모·지연·비용 실측 재현 | local candidate | k-stage4-local-exploration, rs-4-l3 |
| k-operator-evidence | 개발·대사·복구 작업자의 읽기 전용 진단 | local candidate | read-model-reference, k-stage7-authenticated-export, k-adversarial-corpus |
| k-local-program-closeout | 기존 로컬 프로그램과 보완 작업의 완료 근거 | local candidate | k-current-capability-map, k-adversarial-corpus, k-sdk-examples, k-benchmark-reproduction, k-operator-evidence |
| wave7-marketing-contracts | Wave 7: protocol-side marketing contracts M01-M04 and the M05 consent link | pending |  ; kix-commerce-apps:w6a-evidence |
| protocol-runtime-boundary-register | Register protocol authority, execution modes and evidence ownership | pending | 없음 |
| protocol-featureir-conformance | Verify complete FeatureIR execution and schema/numeric boundaries | pending | protocol-runtime-boundary-register, k-stage3-schema-sdk-conformance, k-stage7-cpu-analytics-sql-audit |
| protocol-canonical-identity-conformance | Verify supported canonical identities across Rust and an independent client | pending | protocol-runtime-boundary-register, k-stage3-schema-sdk-conformance, contract-compatibility-profile |
| protocol-read-projection-evidence | Bind read observations to source cuts, snapshots and current producer tuples | pending | protocol-runtime-boundary-register, read-model-reference, contract-compatibility-profile |
| protocol-local-recovery-conformance | Verify local transaction ACK and crash recovery on the User-adopted backend | pending | protocol-runtime-boundary-register, k-stage5-durable-tx, k-readiness-conformance-suite |
| protocol-integration-evidence-closeout | Close the complete protocol inventory with mode-bound evidence and Finance consumers | pending | roadmap-sync, agents-scope-sync, sui-commit-mismatch-note, p-sdk-0, openapi-catalogue-promotion, move-primary-price-fee, ai-delegation-contract-mock, readiness-extensions, settlement-policy-deepening, booking-resale-admission-deepening, f04-mock-deepening, toss-method-expansion-review, gate-browser-access-decision, gate-browser-access, read-model-contract, read-model-reference, p-sdk-1, k1-e4-residual-review, k1-adapter-event-identity, k1-cut-proof, k1-open-inputs-brief, k1-evidence-close, k-stage2-v5-design-decision, k-stage2-v5-impl, k2-retention-proposal, k-stage3-schema-sdk-conformance, k-stage4-comparison-plan, k-readiness-conformance-suite, k-stage4-local-exploration, k-stage4-adoption-decision, k-stage5-durable-tx, k-onsale-admission-control, k-stage6-economics-reference, k-stage7-authenticated-export, k-stage7-cpu-analytics-sql-audit, k-stage8-gpu-plan, k-a-reestimate, k-a-integration-decision, rs-0, rs-1, rs-1-issuercap-probe, rs-2, rs-3a, rs-3b, rs-4-l1, rs-4-l2, rs-4-l3, testnet-key-management-decision, rs-5-decision, tl-a, tl-0, tl-price-source-contract, tl-1, tl-coin-lock-adr, tl-2, tl-3-offchain, tl-3-onchain, tl-4, tl-legal-brief, tl-5-decision, ai-delegation-execution-decision, f04-real-funds-lift-criteria, toss-sandbox-conformance-plan, public-endpoint-readiness-plan, sdk-1-0-decision, ktx-kix-rename-plan, contract-compatibility-profile, wave7-marketing-contracts, protocol-runtime-boundary-register, protocol-featureir-conformance, protocol-canonical-identity-conformance, protocol-read-projection-evidence, protocol-local-recovery-conformance, fin-ledger-contract, fin-double-entry-projection, fin-observation-reconciliation, fin-multi-payee-refund-proof, fin-credit-exposure-reconciliation, fin-consistent-accounting-export, fin-catalogue-read-model, fin-finance-closeout |
| fin-ledger-contract | KIX Finance: version the synthetic finance projection and authority contract | pending | protocol-runtime-boundary-register, settlement-policy-deepening, f04-mock-deepening |
| fin-double-entry-projection | KIX Finance: project synthetic economic events into a balanced finance view | pending | fin-ledger-contract, k-stage5-durable-tx, k-stage6-economics-reference |
| fin-observation-reconciliation | KIX Finance: reconcile original observations, economic effects and finance projections | pending | fin-ledger-contract, k1-adapter-event-identity, k-stage5-durable-tx, fin-double-entry-projection |
| fin-multi-payee-refund-proof | KIX Finance: verify multi-payee, remainder and refund conservation without default policies | pending | fin-ledger-contract, settlement-policy-deepening, k-stage6-economics-reference |
| fin-credit-exposure-reconciliation | KIX Finance: read F04 exposure with current settlement and refund evidence | pending | f04-mock-deepening, fin-double-entry-projection, fin-observation-reconciliation, fin-multi-payee-refund-proof |
| fin-consistent-accounting-export | KIX Finance: export synthetic accounting views at an evidenced source cut | pending | fin-double-entry-projection, fin-observation-reconciliation, k-stage7-authenticated-export |
| fin-catalogue-read-model | KIX Finance: publish finance queries with the exact current qualified producer tuple | pending | fin-credit-exposure-reconciliation, fin-consistent-accounting-export, openapi-catalogue-promotion, contract-compatibility-profile, protocol-read-projection-evidence |
| fin-finance-closeout | KIX Finance: close the adopted synthetic producer and consumer scope with protected evidence | pending | fin-ledger-contract, fin-double-entry-projection, fin-observation-reconciliation, fin-multi-payee-refund-proof, fin-credit-exposure-reconciliation, fin-consistent-accounting-export, fin-catalogue-read-model ; kix-commerce-apps:c-finance-projection ; kix-commerce-apps:refund-surface ; kix-commerce-apps:gift-surface ; kix-commerce-apps:bind-reservation-fsm ; kix-commerce-apps:bind-resale-fsm ; kix-commerce-apps:bind-admission-fsm ; kix-commerce-apps:e2e-browser-journeys ; kix-commerce-apps:delegation-surface ; kix-commerce-apps:c-async-session-fence |
| ps-01-routing-authority | 공연·페이지·cell·shard·epoch의 경합 단위 계약 | pending | rs-0, k-onsale-admission-control |
| ps-02-query-contract | 조회·검색·snapshot·delta·재생 계약 | pending | ps-01-routing-authority, read-model-contract, k-stage7-authenticated-export |
| ps-03-resale-contract | 다중 채널 리셀·조건부 체결·자금 대사 | pending | ps-01-routing-authority, booking-resale-admission-deepening, settlement-policy-deepening |
| ps-04-execution-partitions | 승인 backend의 실행 partition·입출력·fencing | pending | ps-01-routing-authority, k-stage5-durable-tx, k1-cut-proof, rs-3b |
| ps-05-query-projections | 권리·매물 조회 투영과 versioned SDK | pending | ps-02-query-contract, ps-04-execution-partitions, contract-compatibility-profile |
| ps-06-admission-load | 대기열·과부하·공정성·복구 자원 예산 | pending | ps-04-execution-partitions, ps-05-query-projections, k-onsale-admission-control |
| ps-07-scale-qualification | 100만→1,000만→3,000만 규모의 단계별 증거 | pending | ps-03-resale-contract, ps-05-query-projections, ps-06-admission-load, k-benchmark-reproduction ; kix-commerce-apps:c-platform-journey |
| cr-01-product-authority | 여신 상품·주체·권위·정책 버전 계약 | pending | f04-mock-deepening, fin-ledger-contract, f04-real-funds-lift-criteria |
| cr-02-claim-eligibility | 채권 적격성·borrowing base·중복 사용 통제 | pending | cr-01-product-authority, fin-credit-exposure-reconciliation |
| cr-03-facility-reservations | 약정·공유 한도·재원 원자 예약 | pending | cr-02-claim-eligibility, k-stage5-durable-tx, k-stage6-economics-reference |
| cr-04-underwriting-consent | 심사·동의·이유·예외 승인·정책 변경 | pending | cr-01-product-authority, protocol-canonical-identity-conformance |
| cr-05-disbursement-observation | 지급 지시·외부 관측·UNKNOWN·복구 | pending | cr-03-facility-reservations, cr-04-underwriting-consent, k1-adapter-event-identity, fin-observation-reconciliation |
| cr-06-repayment-allocation | 상환표·입금 배분·미식별 입금·조정 | pending | cr-05-disbursement-observation, fin-double-entry-projection, fin-multi-payee-refund-proof |
| cr-07-delinquency-recovery | 연체·조정·회수·상각·후기 입금 | pending | cr-06-repayment-allocation, fin-credit-exposure-reconciliation, fin-consistent-accounting-export |
| cr-08-producer-sdk | 여신 producer 계약·query·SDK 적합성 | pending | cr-02-claim-eligibility, cr-03-facility-reservations, cr-04-underwriting-consent, cr-05-disbursement-observation, cr-06-repayment-allocation, cr-07-delinquency-recovery, fin-catalogue-read-model, contract-compatibility-profile |
| cr-10-credit-qualification | 여신 전체 여정·스트레스·합성 수용 | pending | cr-08-producer-sdk ; kix-commerce-apps:c-credit-servicing-journey |
| k-provider-sandbox | PG·은행·KYC 제공자 sandbox 적합성 | pending | toss-sandbox-conformance-plan, k1-adapter-event-identity, public-endpoint-readiness-plan |
| k-authority-qualification | 체인 위임·회수·backend writer의 실제 자격 | pending | ps-07-scale-qualification, ai-delegation-execution-decision, testnet-key-management-decision, rs-5-decision |
| k-token-platform-contract | 선택적 토큰과 리워드·거래의 연결 자격 | pending | tl-4, tl-5-decision, ps-03-resale-contract |
| k-operator-contract | 플랫폼 운영·권한·감사·장애 대응 계약 | pending | k-operator-evidence, ps-06-admission-load, cr-08-producer-sdk |
| k-platform-release | 대규모 프로토콜·금융·체인 운영 인계 | pending | k-local-program-closeout, protocol-integration-evidence-closeout, cr-10-credit-qualification, k-provider-sandbox, k-authority-qualification, k-token-platform-contract, k-operator-contract ; kix-commerce-apps:c-platform-operational-qualification |

## 계획 검증 명령

이 검사는 계획의 구조와 해시를 확인한다. 제품 구현 테스트·독립 A3·실제 실행 자격을 대신하지 않는다.

```bash
python3 scripts/validate_program_expansion.py
# 네 레포의 이번 확대 후보를 같은 상위 디렉터리에 checkout한 경우
python3 scripts/validate_program_expansion.py --workspace /path/to/sibling-repositories
```

JSON 중복 key·ID 충돌·잘못된 선행·순환·전체 정의 해시·정본 mirror·문서 해시·Finance alias를 검사한다. 전체 workspace 검사는 외부 선행의 실제 ID와 네 레포 결합 DAG까지 확인한다. 작업 완료 사실이나 외부 승인 여부를 자동 추정하지 않는다.

