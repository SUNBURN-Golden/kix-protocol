# 프로그램 로드맵 R-1 — 2026-09-30 (사용자 위임)

상태: **범위 결정안.** #81의 대표님 병합은 범위 승인이고, 시작은 별도 시작 PR이다. 작성 기준 main은 `78b78b1b4a4ffe92de461edd351235ce858b335a`다.
이 문서는 [프로그램 결정 D-1~D-3](PROGRAM_DECISIONS_20260928.md)을 이어받아 KIX 두 저장소의 장기 계획을 한 번에 승인하기 위한 것이다.

## 0. 작성 근거와 효력 발생

- 2026-09-30 사용자(저장소 소유자)가 대화에서 다음을 지시했다.
  - "KIX 두개에는 좀더 방대하게 엄청나게 원대한 계획을 넣을수 없니?"
  - "그록봇한테 진행해라잇! 딸깍 하면 지 알아서 완성을 시켜놓는게 목표거든? 그러니까 존나 계획을 크게크게 던져주면 되지 않냐 이말이지. 그렇게 될 수 있게 세팅해"
- 지시의 요지는 두 가지다.
  - kix-protocol과 kix-commerce-apps에 장기·대규모 계획을 넣는다.
  - 한 번 시작하면 사람의 결정이 꼭 필요한 곳 말고는 멈추지 않고 끝까지 진행되게 한다.
- 이 문서는 그 지시에 따라 Claude가 작성한 **결정안**이다. 에이전트가 승인 범위를 스스로 넓히지 않도록, 작성만으로는 효력이 생기지 않는다.
- **범위 효력 발생:** 대표님이 #81을 병합하거나 이 범위를 따로 명시 승인한 때다. 실행/시작은 승인 초안을 복사하고 승인 링크만 바꾸는 별도 시작 PR의 exact-HEAD Fable 감사와 대표님 병합 뒤에 열린다. 사용자는 언제든 바꾸거나 되돌릴 수 있고, 그 경우 새 결정 문서가 이 문서를 대체한다.
- 이 문서는 다음을 바꾸지 않는다.
  - AGENTS.md의 program mode 규칙, 비작성자 exact-HEAD 검토, 단일 작성자, UNKNOWN fencing, 잠금 blob 규칙
  - [프로그램 결정](PROGRAM_DECISIONS_20260928.md) §5의 잠금과 해제 조건
  - [Task 005](../tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md)의 Astra 결정 1~6과 [모델 1 결정](AUTHORITY_MODEL_1.md)
- 효력이 생긴 뒤 개발계획·README·AGENTS.md에 반영하는 일은 노드 `roadmap-sync`가 한다. 반영 전까지 충돌하면, 이 문서의 범위 안에서는 이 문서가 개발계획보다 우선한다.

## 1. 계획의 형태와 승인 방식

- 비실행 정본은 kix-protocol `docs/aiops/KIX_PROGRAM_DRAFT.json`(67개)과 kix-commerce-apps `docs/aiops/KIX_COMMERCE_PROGRAM_DRAFT.json`(10개)이다. pending 정의는 protocol15/commerce26이며 전체82/36개다. Finance8은 protocol pending의 부분집합이다. §3·§4는 초기 roadmap 표이며 현재 전체 정의·병합 등급/경계는 각 초안 및 PROGRAM_ASTRA_DELEGATION 판정 표가 우선한다.
- **#81 병합 = 범위 승인, 시작 = 별도 시작 PR.** 승인 전 `.aiops/program.json`은 없다. PENDING pointer를 제품 시작 승인으로 바꾸는 일은 대표님 시작 결정 뒤에만 한다. 절차와 hash 규칙은 [등록 범위 문서](../aiops/REGISTRATION_SCOPE_APPROVAL_KO.md)를 따른다.
- 정책 C(2026-10-01, [대표님 원문](https://github.com/BeautifulMind-JT/ai-ops-control-plane/pull/47#issuecomment-5927605393))는 Fable PASS 위임 노드 자동 병합이며 contract_change=YES·RELEASE·user_merge는 대표님 몫이다. 기존14 User-only 외에 계약 변경 노드도 user_merge/A3로 바꿨다. [spec 판정 표](../aiops/PROGRAM_ASTRA_DELEGATION.md)가 현재 병합 경계다. source 후보의 설치·qualification 전에는 program을 켜지 않는다.
- 외부 선행 노드는 pending catalogue에 둔다. 실제 보호된 완료와 정확한 plan/definition/delivery/merge·post-merge 근거를 확인한 뒤 별도 대표님 병합 plan revision으로 승격한다. 미완료/UNKNOWN을 삭제해 실행하지 않는다.
- 제품 정책·새 명령은 DECISION_REQUIRED로 멈추며 법률/회계/토스 답변은 UNDETERMINED와 담당을 기록한다. §5 잠금은 유지한다. coin/TIX 유일 예외인 tl-2도 Astra 재결정 및 대표님 tl-coin-lock-adr 병합 뒤에만 가능하다.

## 2. 이 문서로 확정되는 결정

| 번호 | 결정 | 근거 |
|---|---|---|
| R-1 | **D-B 수락.** Astra 판정대로 범위·한계 ADR(TL-A)을 TL-0 앞에 둔다. 새 coin/TIX 모듈 잠금의 해제 경로(ADR + Astra 재결정)는 그대로다 | [TL·RS 범위 결정](TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md) §4.1, D-B |
| R-2 | **D-D 수락.** 권리 확장의 권고 구조(독립 객체 분할)를 받아들인다. 새 패키지·새 회로를 프로그램 결정 §2.1의 "`rights`·`zk_gate` 확장"으로 읽는 해석을 Astra 조건 (a)~(e)와 함께 확인한다 | 같은 문서 D-D |
| R-3 | **D-C.** 토큰 초기 역할 범위는 권고안 U2(담보)·U3(보상)로 설계한다. 되돌리기 어려운 선택이 들어가므로 최종 확정은 `tl-0` 계약 문서의 사용자 병합으로 한다 | 같은 문서 D-C |
| R-4 | **Track K 2단계 구현 착수 조건을 바꾼다.** 프로그램 결정 §2.2(61-63행)는 착수 조건을 둘로 정했다. 첫 묶음 열린 입력의 해당 행이 확정될 것, 그리고 v5 설계 결정 문서가 있을 것. R-4는 첫째 조건을 **착수 조건에서 부분별 정지 조건으로 바꾼다.** v5 설계 결정 문서(`k-stage2-v5-design-decision`)를 사용자가 병합하면 `k-stage2-v5-impl`이 시작한다. 이것이 §2.2의 "별도 승인"이다. 해당 행이 아직 열려 있으면 그 행에 기대는 부분만 `DECISION_REQUIRED`로 멈춘다 | 프로그램 결정 §2.2 |
| R-5 | **Track K 3단계 적합성 작업 승인.** 안정 1.0과 공개 배포는 여기에 들어가지 않는다(`sdk-1-0-decision`, 사용자) | 프로그램 결정 §5 |
| R-6 | **Track K 5단계 로컬·비운영 구현 착수 조건.** backend 채택 결정 문서(`k-stage4-adoption-decision`)를 사용자가 병합하면 `k-stage5-durable-tx`가 시작한다. R2와 자체 복제·합의는 계속 잠금이다 | 프로그램 결정 §2.2, §5 |
| R-7 | **Wave 7 조건부 게이트.** kix-commerce-apps 노드 `w6a-evidence`가 병합되면 Wave 7이 열린다. 이것이 프로그램 결정 §3의 진입 조건(최소 한 표면의 mock end-to-end 여정)이다. **이 절이 Wave 7의 게이트 기록이다.** 구현 PR은 이 절과 `w6a-evidence` PR 링크를 인용한다. `w6a-evidence`는 계약 변경/RELEASE/User-only가 아니면 정책 C의 보호된 Fable PASS와 exact-head gate 뒤 위임 병합한다. kix-protocol `wave7-marketing-contracts`는 편입 대기이며 그 병합 뒤 계획 개정으로 들어온다 | 프로그램 결정 §3 |
| R-8 | **kix-commerce-apps 사후 승인.** Wave 6 게이트 기록([#56 댓글](https://github.com/BeautifulMind-JT/kix-protocol/issues/56#issuecomment-5868307343), 2026-09-28 10:42Z) 전에 병합된 [#1](https://github.com/BeautifulMind-JT/kix-commerce-apps/pull/1), [#3](https://github.com/BeautifulMind-JT/kix-commerce-apps/pull/3)~[#12](https://github.com/BeautifulMind-JT/kix-commerce-apps/pull/12)(2026-09-25 23:35Z~09-28 08:49Z)를 승인된 병합분으로 인정한다. D-2가 Wave 2~5를 사후 승인한 것과 같은 방식이다. 모두 stub·mock·loopback 결합이라 Wave 6 범위(계약 소비와 mock backend) 안이다. CI [#13](https://github.com/BeautifulMind-JT/kix-commerce-apps/pull/13)은 게이트 뒤(09-28 23:14Z)에 병합됐다. #3의 Wave 7 마케팅 stub은 stub으로만 인정하고, Wave 7이 열리기 전에는 계약에 결합하지 않는다 | 프로그램 결정 §3 |
| R-9 | **계약 공백 심화 승인.** 정산 계약 §7, 예매·리셀·검표 계약 §7, F04 계약 §5("의도적으로 비운 항목")의 초안 작업을 승인한다. 정책 값은 Astra 결정 경로로 정하고, 법률 의존 값은 `UNDETERMINED`로 둔다 | 각 계약의 해당 절 |
| R-10 | **6단계 경제 기능은 참조 모델로만 승인한다.** 합성 금액만 쓴다. 실자금은 프로그램 결정 §5 조건을 따른다 | 개발계획 6단계 |
| R-11 | **이 문서가 따로 이름 붙여 승인하는 구현 범위.** 아래는 R-1~R-10에 없던 구현이다. 모두 §5 잠금 안에 있다. (1) `gate-browser-access`: loopback 관문의 동작 변경. 기본 꺼짐, loopback 출처만, 결정 문서가 정한 방식으로만. (2) `read-model-reference`: 새 조회 명령을 참조 모듈과 카탈로그에 추가. 상태를 바꾸지 않는다. (3) `k-onsale-admission-control`: R4 시기 계약(runtime/ONSALE_ADMISSION_CONTROL.md, 구현 없음)을 새로 고치고 로컬에 구현. 개발계획 §5의 단계 목록 밖이지만 5단계 뒤에만 시작한다. (4) `k-stage7-authenticated-export`, `k-stage7-cpu-analytics-sql-audit`: 개발계획 §5(111행)는 7단계에 원천·권위 연결이 먼저라고 적는다. 그래서 5단계 로컬 원천 위에서만 시작한다 | 개발계획 §5, 각 노드 |

D-E(법률·회계·세무·금융 검토의 주체와 시점)는 사람이 정할 일이라 사용자 몫으로 남긴다. `tl-legal-brief`가 질문지를 준비한다.

## 3. kix-protocol 노드 (program `kix`)

### 3.1 문서 정합

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `roadmap-sync` | Reflect the approved roadmap into DEVELOPMENT_PLAN, README, AGENTS and the task index | — | A1 | — | 자동(M1·Fable) |
| `agents-scope-sync` | Reflect the roadmap's approved scope into AGENTS.md §5 | — | A3 | ARCHITECTURE | **사용자** |
| `sui-commit-mismatch-note` | Record why two Sui framework commits appear in the docs | — | A1 | — | 자동(M1·Fable) |

### 3.2 Track P — 계약·카탈로그·SDK

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `p-sdk-0` | P-SDK-0: TypeScript 0.x client from the contract-only OpenAPI, with conformance tests | — | A2 | — | 자동(M1·Fable) |
| `openapi-catalogue-promotion` | Promote settlement, booking, resale, admission and credit commands into the contract-only OpenAPI catalogue | p-sdk-0 | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `move-primary-price-fee` | Define primary issuance price and fee for the Move rights module | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `ai-delegation-contract-mock` | AI delegation authority contract draft and in-memory mock | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `readiness-extensions` | Extend the readiness journal inside the D-3 bounds | — | A2 | — | 자동(M1·Fable) |
| `settlement-policy-deepening` | Settlement contract §7: turn the open policy items into a decided draft revision | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `booking-resale-admission-deepening` | Booking/resale/admission contract §7: decide the open items as a draft revision | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `f04-mock-deepening` | F04 credit contract: product terms for the mock | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `toss-method-expansion-review` | Review easy-pay and virtual accounts inside the Toss profile (document only) | — | A2 | — | 자동(M1·Fable) |
| `gate-browser-access-decision` | Decide how the commerce browser may reach the loopback gate (CORS) | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `gate-browser-access` | Implement the chosen browser access option in the loopback gate | gate-browser-access-decision | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `read-model-contract` | Read and list query contract for commerce surfaces | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `read-model-reference` | Implement the approved read queries and add them to the catalogue | read-model-contract, openapi-catalogue-promotion | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `p-sdk-1` | P-SDK-1: regenerate the TypeScript 0.x client for the full catalogue | openapi-catalogue-promotion, read-model-reference | A2 | — | 자동(M1·Fable) |

### 3.3 Track K — 첫 묶음 잔여와 1~8단계

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `k1-e4-residual-review` | First batch: residual review of the E-4 model and contract invariants | — | A2 | — | 자동(M1·Fable) |
| `k1-adapter-event-identity` | I06: design adapter transmission, event, payment and operation identities (document only) | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `k1-cut-proof` | I12: technical proof of the C_g/H_g cut and old-writer fencing | — | A3 | ARCHITECTURE | **사용자** |
| `k1-open-inputs-brief` | Ready-to-send question sheets for the open first-batch inputs | — | A1 | — | 자동(M1·Fable) |
| `k1-evidence-close` | First batch: integration review and evidence close-out | k1-e4-residual-review, k1-adapter-event-identity | A1 | — | 자동(M1·Fable) |
| `k-stage2-v5-design-decision` | Track K stage 2: v5 crate design decision proposal (document only) | — | A3 | ARCHITECTURE | **사용자** |
| `k-stage2-v5-impl` | Track K stage 2: implement the lifecycle transitions in the v5 crate | k-stage2-v5-design-decision | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `k2-retention-proposal` | Retention periods proposal (legal, reconciliation, retry support, memory) | — | A3 | ARCHITECTURE | **사용자** |
| `k-stage3-schema-sdk-conformance` | Track K stage 3: schema and SDK conformance | p-sdk-1 | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `k-stage4-comparison-plan` | Track K stage 4: backend comparison plan and candidate screening | — | A2 | — | 자동(M1·Fable) |
| `k-readiness-conformance-suite` | Split the readiness fault suite into a backend-common conformance test | — | A2 | — | 자동(M1·Fable) |
| `k-stage4-local-exploration` | Track K stage 4: local exploratory measurement under equal conditions | k-stage4-comparison-plan, k-readiness-conformance-suite | A2 | — | 자동(M1·Fable) |
| `k-stage4-adoption-decision` | Track K stage 4: backend adoption decision proposal | k-stage4-local-exploration | A3 | ARCHITECTURE | **사용자** |
| `k-stage5-durable-tx` | Track K stage 5: durable transactions on the adopted backend (local, non-production) | k-stage4-adoption-decision, k-stage2-v5-impl | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `k-onsale-admission-control` | On-sale admission control: waiting room and GA routing | k-stage5-durable-tx | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `k-stage6-economics-reference` | Track K stage 6: economics as a reference model with synthetic money | k-stage5-durable-tx, settlement-policy-deepening, booking-resale-admission-deepening | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `k-stage7-authenticated-export` | Track K stage 7: authenticated, consistent export | k-stage5-durable-tx | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `k-stage7-cpu-analytics-sql-audit` | Track K stage 7: CPU analytics semantics audit (Polars, DuckDB) | k-stage7-authenticated-export | A2 | — | 자동(M1·Fable) |
| `k-stage8-gpu-plan` | Track K stage 8: native GPU path plan (document only) | k-stage7-cpu-analytics-sql-audit | A2 | — | 자동(M1·Fable) |
| `k-a-reestimate` | Re-estimate integration (a) of the PR #11 journal | k1-evidence-close | A2 | — | 자동(M1·Fable) |
| `k-a-integration-decision` | Integration (a) decision proposal | k-a-reestimate | A3 | ARCHITECTURE | **사용자** |

### 3.4 권리 확장 (RS)

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `rs-0` | RS-0: rights-scale object and inventory authority design | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `rs-1` | RS-1: public path on the new profile at 1,024 slots (localnet) | rs-0 | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `rs-1-issuercap-probe` | RS-1 probe: does concurrent IssuerCap use by reference serialize? | rs-1 | A2 | — | 자동(M1·Fable) |
| `rs-2` | RS-2: private path (root rules, new circuit, verifier, manifest v2) | rs-1 | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `rs-3a` | RS-3a: on-chain delegation primitives (page-level grant, GrantControl, revocation cut) | rs-1 | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `rs-3b` | RS-3b: Rust delegated execution integration (new crate) | rs-3a, k-stage2-v5-impl | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `rs-4-l1` | RS-4 L1: staged load validation at 1,024 slots | rs-1, rs-2, rs-3a | A2 | — | 자동(M1·Fable) |
| `rs-4-l2` | RS-4 L2: staged load validation at 16,384 slots | rs-4-l1 | A2 | — | 자동(M1·Fable) |
| `rs-4-l3` | RS-4 L3: staged load validation at 65,536 slots with concurrent shows | rs-4-l2 | A2 | — | 자동(M1·Fable) |
| `testnet-key-management-decision` | Sui testnet key management decision proposal | rs-1 | A3 | ARCHITECTURE | **사용자** |
| `rs-5-decision` | RS-5: operational adoption decision proposal | rs-4-l3, rs-1-issuercap-probe, testnet-key-management-decision | A3 | ARCHITECTURE | **사용자** |

### 3.5 토큰 계층 (TL)

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `tl-a` | TL-A: token layer scope-and-limits ADR | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `tl-0` | TL-0: token role and supply contract | tl-a | A3 | ARCHITECTURE | **사용자** |
| `tl-price-source-contract` | Token price source contract (only if TL-0 needs conversion) | tl-0 | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `tl-1` | TL-1: token authority and lifecycle contract | tl-0 | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `tl-coin-lock-adr` | ADR requesting the Astra re-ruling to lift the coin/TIX lock for a localnet package | tl-0, tl-1 | A3 | ARCHITECTURE | **사용자** |
| `tl-2` | TL-2: non-production token package on localnet | tl-coin-lock-adr | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `tl-3-offchain` | TL-3 off-chain: reward-transaction coupling in a reference model | tl-1 | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `tl-3-onchain` | TL-3 on-chain: reward records on localnet | tl-2, tl-3-offchain | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `tl-4` | TL-4: independent verification of the token layer | tl-2, tl-3-onchain | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `tl-legal-brief` | Brief for external legal, accounting, tax and finance review | tl-0 | A2 | — | 자동(M1·Fable) |
| `tl-5-decision` | TL-5: operational activation decision proposal | tl-4, tl-legal-brief | A3 | ARCHITECTURE | **사용자** |

### 3.6 AI 위임·금융·출시 준비

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `ai-delegation-execution-decision` | Decision proposal for enabling delegated execution | ai-delegation-contract-mock, rs-3a, rs-3b | A3 | ARCHITECTURE | **사용자** |
| `f04-real-funds-lift-criteria` | Criteria for lifting real credit (document only) | f04-mock-deepening | A3 | ARCHITECTURE | **사용자** |
| `toss-sandbox-conformance-plan` | Plan for Toss sandbox conformance evidence (document only) | k1-adapter-event-identity, toss-method-expansion-review | A2 | — | 자동(M1·Fable) |
| `public-endpoint-readiness-plan` | Plan for the public endpoint unlock (document only) | — | A2 | — | 자동(M1·Fable) |
| `sdk-1-0-decision` | Decision proposal for a stable schema/SDK 1.0 and publishing | k-stage3-schema-sdk-conformance | A3 | ARCHITECTURE | **사용자** |
| `ktx-kix-rename-plan` | Plan for the bulk KTX to KIX rename (document only) | k-stage3-schema-sdk-conformance | A2 | — | 자동(M1·Fable) |

### 3.7 편입 대기 — kix-protocol

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `wave7-marketing-contracts` | Wave 7: protocol-side marketing contracts M01-M04 and the M05 consent link | 외부: kixc/w6a-evidence | A3 | ARCHITECTURE | 자동(M1·Fable) |

## 4. kix-commerce-apps 노드 (program `kixc`)

### 4.1 Wave 6-A — 첫 mock 여정

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `w6a-journey-map` | Wave 6-A step 1: map one receipt-chained mock booking journey onto published commands | — | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `w6a-journey-adapter` | Wave 6-A step 2: adapter helper that composes the approved journey | w6a-journey-map | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `w6a-journey-test` | Wave 6-A step 3: live-gate journey test and stub parity | w6a-journey-adapter | A2 | — | 자동(M1·Fable) |
| `w6a-ui-skeleton` | Wave 6-A step 4: booking and box-office screens show the journey | w6a-journey-adapter | A2 | — | 자동(M1·Fable) |
| `w6a-evidence` | Wave 6-A step 5: binding table, docs and the alignment evidence that opens Wave 7 | w6a-journey-test, w6a-ui-skeleton | A1 | MILESTONE | 자동(M1·Fable) |

### 4.2 Wave 6 심화 — 화면

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `organizer-admin-console` | Organizer console for event lifecycle commands | w6a-evidence | A2 | — | 자동(M1·Fable) |
| `gift-surface` | Gift transfer surface (offer, accept, cancel) | w6a-journey-adapter | A2 | — | 자동(M1·Fable) |
| `doc-m05-label` | Correct the M05 status label to the ORIGINAL_32 source | — | A1 | — | 자동(M1·Fable) |

### 4.3 Wave 7 — 마케팅

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `w7-marketing-align` | Wave 7: align the M01-M05 stub surfaces with the published contracts | w6a-evidence | A2 | — | 자동(M1·Fable) |
| `w7-m05-consent-bind` | Wave 7 M05: bind consent to set_consent and authorize_marketing | w7-marketing-align, w6a-journey-adapter | A3 | ARCHITECTURE | 자동(M1·Fable) |

### 4.4 편입 대기 — 계약 결합

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `consume-p-sdk-0` | Consume the generated TypeScript 0.x client from kix-protocol | 외부: kix/p-sdk-0 | A2 | — | 자동(M1·Fable) |
| `bind-settlement-fsm` | Bind the settlement desk methods to the promoted catalogue | consume-p-sdk-0, 외부: kix/openapi-catalogue-promotion | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `bind-reservation-fsm` | Bind the reservation desk methods to the promoted catalogue | consume-p-sdk-0, 외부: kix/openapi-catalogue-promotion | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `bind-admission-fsm` | Bind the admission desk methods (including authorize and consume) | consume-p-sdk-0, 외부: kix/openapi-catalogue-promotion | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `bind-resale-fsm` | Bind the resale desk methods to the promoted catalogue | consume-p-sdk-0, 외부: kix/openapi-catalogue-promotion | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `bind-credit-fsm` | Bind the credit desk methods (mock only) | consume-p-sdk-0, 외부: kix/openapi-catalogue-promotion | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `bind-wave4-pointers` | Rebind the Wave 4 pointer methods onto published bodies | w6a-journey-map, bind-reservation-fsm, bind-resale-fsm | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `bind-list-read` | Bind the list and read methods to the read-model queries | consume-p-sdk-0, 외부: kix/read-model-reference | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `browser-gate-path` | Browser HTTP path to the loopback gate, as kix-protocol decided | w6a-ui-skeleton, 외부: kix/gate-browser-access | A3 | ARCHITECTURE | 자동(M1·Fable) |

### 4.5 편입 대기 — 화면·Wave 7

| 노드 | 내용 | 선행 | 등급 | Astra 게이트 | 병합 |
|---|---|---|---|---|---|
| `primary-price-fee-ui` | Show the contracted primary price and fee | w6a-ui-skeleton, 외부: kix/move-primary-price-fee | A2 | — | 자동(M1·Fable) |
| `api-state-distinction` | UI separates reservation, payment, issuance, return and refund states | bind-reservation-fsm, bind-settlement-fsm | A2 | — | 자동(M1·Fable) |
| `refund-surface` | Refund and cancel flows as synthetic mocks | bind-settlement-fsm | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `delegation-surface` | Delegation surface: query and propose only | consume-p-sdk-0, 외부: kix/ai-delegation-contract-mock | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `w7-m01-membership` | Wave 7 M01: membership surface on the membership contract | w7-marketing-align, 외부: kix/wave7-marketing-contracts | A2 | — | 자동(M1·Fable) |
| `w7-m02-presale` | Wave 7 M02: presale surface on the presale contract | w7-marketing-align, bind-reservation-fsm, 외부: kix/wave7-marketing-contracts | A2 | — | 자동(M1·Fable) |
| `w7-m03-coupon` | Wave 7 M03: coupon surface on the coupon contract | w7-marketing-align, bind-reservation-fsm, 외부: kix/wave7-marketing-contracts | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `w7-m04-referral` | Wave 7 M04: referral surface on the referral contract (no payout) | w7-marketing-align, 외부: kix/wave7-marketing-contracts | A3 | ARCHITECTURE | 자동(M1·Fable) |
| `e2e-browser-journeys` | Browser end-to-end journeys across all surfaces | browser-gate-path, api-state-distinction, bind-list-read, organizer-admin-console | A2 | MILESTONE | 자동(M1·Fable) |

## 5. 계획에 넣지 않은 것

아래는 되돌리기 어렵거나 외부 조건이 필요해 **실행 노드로 넣지 않았다.** 필요한 것은 결정 문서나 계획 문서 노드로만 두었다.

| 항목 | 이유와 해제 조건 | 계획에 둔 것 |
|---|---|---|
| 실자금, 실 PG·은행·KYC 호출 | 프로그램 결정 §5: 토스 미확인 항목, sandbox 증거, 사용자 승인 | `toss-sandbox-conformance-plan`, `k1-open-inputs-brief` |
| 실제 여신·규제 금융 | 법률·인허가 검토와 Astra·사용자 승인 | `f04-real-funds-lift-criteria`(사용자) |
| Sui testnet 배포 | 키 관리 결정 문서와 사용자 승인 | `testnet-key-management-decision`(사용자) |
| Sui mainnet | 독립 Move 감사, testnet 운용 증거, 운영 책임자, 사용자 승인 | `rs-5-decision`, `tl-5-decision`(사용자) |
| 공개 운영 엔드포인트 | 인증, TLS, 운영 책임자, 장애 대응, 사용자 승인. 관문은 127.0.0.1 유지 | `public-endpoint-readiness-plan` |
| R2, 자체 복제·합의·저장 엔진 | §9 비교의 구체적 부족 입증과 사용자 승인 | 없음(4단계 비교가 근거를 만든다) |
| PR #11 통합(a) | 재산정과 사용자 승인 | `k-a-reestimate`, `k-a-integration-decision`(사용자) |
| 새 coin/TIX 모듈 | ADR과 Astra 재결정, 잠금 변경은 사람 결정 | `tl-coin-lock-adr`(사용자) 뒤 localnet `tl-2`만 |
| 토큰 발행·판매·분배·풀·바이백, 스테이블코인, 토큰 가스, 자체 체인 | 승인되지 않음 | 없음 |
| 안정 1.0, 공개 배포, KTX→KIX 일괄 치환 | 3단계 재승인과 잠금 변경 결정 | `sdk-1-0-decision`(사용자), `ktx-kix-rename-plan` |
| 첫 묶음의 수명 계약 입력 반영, 고정 환경 성능 반복 | 토스 답변, 승인된 수치와 장비가 필요 | `k1-evidence-close`가 열린 항목으로 기록 |
| 8단계 GPU 구현 | 장비 지출 | `k-stage8-gpu-plan`(계획만) |
| 현장 검표 장비, 실 마켓플레이스, 은행 rail, CRM 캠페인 편집 | 해제 조건이 정해지지 않았거나 별도 제품 | 없음 |
| 저장소 설정·보호 규칙·secret | 에이전트 금지(AGENTS.md §5) | 사용자 할 일(§6) |
| 위생 backlog 일괄 정리 | 목록만, 별도 승인 | 없음 |

## 6. 사용자에게 남는 일

1. #81과 커머스 범위 PR을 검토·병합한다. 범위 승인이며 실행 시작은 아니다.
2. 실제 시작을 정하고 각 저장소의 별도 **시작 PR**을 요청한다. 승인 초안을 그대로 복사하고 approval_pointer만 대표님 결정 링크 하나로 바꾼 PR의 exact-HEAD Fable 감사 뒤 대표님이 병합한다. 같은 PR에서 정의를 바꾸지 않는다.
3. 중앙 최종 source 채택·보호된 설치/authorization·host qualification/activation·attestation과 user_merge/contract_change/RELEASE/외부 선행 보호의 실제 근거를 확인한 뒤 코디네이터 시작을 승인한다.
4. PROGRAM_ASTRA_DELEGATION 판정 표의 대표님 노드 PR은 읽고 병합하거나 수정을 요청한다. 원래14 결정 노드 외에 새 계약 변경 노드도 포함된다.
5. 외부 답변(토스·법무·세무)은 k1-open-inputs-brief와 tl-legal-brief의 담당 질문지로 받는다. 실제 환경/자원/화면/작품 승인도 별도다.
6. 편입 대기는 실제 보호된 선행 완료 확인 후 별도 plan revision을 검토·병합한다. secret/host/실자금/chain/공개 운영을 이 초안 PR에서 설정하지 않는다.
