# KIX 계약 호환 묶음과 개발 완료 설계 후보

공통 후속 규약: [중앙 #46](https://github.com/BeautifulMind-JT/ai-ops-control-plane/pull/46), 후보 HEAD `a8b7355712c58de8d27c85a535fb241a09a4037c`. [고정 설계](https://github.com/BeautifulMind-JT/ai-ops-control-plane/blob/a8b7355712c58de8d27c85a535fb241a09a4037c/engineering/docs/PROGRAM_EXECUTION_EVOLUTION_DESIGN_KO.md)는 아직 운영·승인 evidence가 아니다.

상태: **설계·계획 개정 후보. 구현·활성화·감사 PASS가 아니다.**
작성 기준은 protocol #82 `1fc02920d93fe0fb1f272fa917f6e20ba26cc987`와 commerce
#15 `a7c9d4467a9170ba4a062554562a4610c0b27573`다. 기존 원본 감사 대상
#81 `eee77d135f03471b78ce673223dafc7e0b0fb36b`와 #14
`e80c5d53989af35987aa0b8371b4220acd4e3808`를 바꾸지 않는다.
사용자의 2026-09-30 설계 고도화 지시에 따른 후속 초안이며, 기존 승인·감사·사용자
채택 절차를 대신하지 않는다. 운영 `approval_pointer`의 PENDING을 유지한다.

## 1. 범위와 권위

- 기존 [실행 위임 후보](PROGRAM_ASTRA_DELEGATION.md), AGENTS.md,
  `docs/decisions/PROGRAM_ROADMAP_20260930.md`와 잠금 조건을 이어받는다.
- 중앙 `BeautifulMind-JT/ai-ops-control-plane`의
  `engineering/docs/PROGRAM_EXECUTION_EVOLUTION_DESIGN_KO.md`는 **후속 설계 후보**다.
  아직 채택·설치·attestation된 런타임이라고 취급하지 않는다.
- 이 문서는 계약/관문/생성 SDK/소비 앱을 같은 비운영 묶음으로 검증하는 설계다.
  안정 SDK 1.0, 공개 배포, 실제 결제·KYC·chain 운영을 승인하지 않는다.
- 두 잠금 kernel blob, 참조 v0.3-rc1 보존, UNKNOWN fencing, no polling,
  User-only 노드 14개와 별도 잠금 해제 조건은 그대로다.
- 제품 정책이나 새 명령 의미를 만들 필요가 있으면 기존 DECISION_REQUIRED 경로를 따른다.

## 2. 호환 묶음의 입력 정본

문서의 버전 이름이나 저장소 HEAD가 같다는 이유만으로 호환을 추론하지 않는다.
producer는 다음 입력을 canonical UTF-8 JSON의 manifest로 기록한다. 객체 키 정렬,
공백 없는 compact JSON, 마지막 newline 없음, 중복 키 거부를 고정하고 숫자·문자열
표현은 생성기와 verifier가 공유하는 profile/golden vector로 검증한다. manifest
내용에는 감사/승인 결과를 넣지 않는다.

| 필드 묶음 | 고정하는 입력 |
|---|---|
| producer | repository, exact source commit/tree, protocol domain, contract schema version |
| contract | contract-only OpenAPI와 integration-gate OpenAPI 각각의 path, Git blob, file sha256 |
| generated SDK | tree/path, generator source revision과 고정 toolchain, output blob/tree digest와 file sha256 |
| semantics | 승인된 compatibility profile의 kind와 immutable revision, command/query/receipt schema 집합 digest |
| vectors | body/receipt/identity/error conformance vector 집합의 path와 digest |
| source references | 허용된 FSM source/contract revisions, 원본 fixture profile과 확장 profile 구분 |

`manifest_digest`는 위 입력 JSON 바이트의 SHA256이다. manifest 자기 digest와
manifest를 추가하는 commit의 SHA를 자기 입력에 넣지 않는다. producer source는
실제 구현/계약/SDK 바이트를 포함한 확인된 commit을 고정한다. 후속 기록 commit과
그 source의 차이가 docs만인지도 verifier가 관련 경로로 확인한다. 관련 바이트가
변했다면 새로운 source와 manifest가 필요하다.

consumer app의 최종 HEAD는 producer manifest 안에 넣지 않는다. app은 소비한
manifest digest와 producer 입력을 버전 관리하고, 최종 정확한 app HEAD의 독립
검토·CI·보호된 completion receipt가 그 소비 입력을 별도로 결합한다. 이 구조가
최종 HEAD를 기록하려다 HEAD를 끝없이 바꾸는 self-reference를 막는다.

### 2.1 초기 형식·검증과 후속 의미 검증의 담당

`p-sdk-0`가 **manifest-v1 형식, BOOTSTRAP profile, 최소 verifier와 golden vectors**를
처음 제공한다. 공유 schema/검증 경계를 만드는 일이므로 이 후보에서 해당 노드의
최소 등급을 A2에서 **A3/ARCHITECTURE**로 올린다. 새 노드는 추가하지 않는다.
이 설계의 채택은 형식·작업 범위의 승인일 뿐 실제 profile의 감사 PASS가 아니다.
소비 가능한 초기 profile revision은 그 작업의 비작성자 exact-HEAD A3 검토와 보호된
완료 증거·실제 병합을 거친 immutable source에 고정한다.

| 담당 | 제공·검증하는 것 | 주장하지 않는 것 |
|---|---|---|
| `p-sdk-0` | 기존 catalogue 의미를 유지한 manifest-v1 schema/encoding, BOOTSTRAP profile revision+digest, source/두 OpenAPI/generator/SDK/output/vector 결합을 확인하는 offline 최소 verifier, canonical encoding과 혼합 입력 거부 golden vectors | 확대 catalogue 의미 검증, N/N−1 호환, production conformance |
| `consume-p-sdk-0` | 원본 catalogue의 정확한 p-sdk-0 manifest와 BOOTSTRAP profile을 vendoring하고 같은 최소 verifier와 vectors로 입력 결합을 확인 | 변경된 catalogue나 후속 profile을 초기 PASS로 소비할 권한 |
| `contract-compatibility-profile` | 초기 형식·최소 verifier를 재사용하고 `p-sdk-1`/stage3 뒤 확대 command/query/receipt 및 승인 fixture 간 positive/negative 의미 conformance를 검증한 SEMANTIC_CONFORMANCE profile과 정확한 대상 tuple/evidence | 과거 BOOTSTRAP profile의 소급 승격, 이후 변경의 자동 qualification |

manifest-v1은 `manifest_schema_version`, `profile_kind`, `profile_revision`,
`profile_sha256`를 필수 입력으로 고정한다. 허용 kind는 `BOOTSTRAP`과
`SEMANTIC_CONFORMANCE`뿐이며 verifier는 누락/unknown kind와 요청한 kind·revision·
digest가 다른 입력을 거부한다. BOOTSTRAP의 허용 catalogue/schema/vector 집합은
초기 immutable profile에 한정한다. manifest와 profile은 위 표의 입력을 기록하는
artifact이며 보호된 감사·완료 증거를 대체하지 않는다. profile 자신의 digest는
profile 바이트 밖에서 계산하며 자기 digest/최종 commit을 profile 입력에 넣지 않는다.

초기 golden vectors는 생성기와 consumer verifier가 같은 바이트를 얻는 양성 사례와
중복 키, 잘못된 UTF-8/숫자 표현, wrong schema/kind/revision/digest, 다른 source,
혼합 OpenAPI/SDK, 잘린 입력 거부 사례를 포함한다. 허용 숫자·문자열 표현을
명시하고 같은 입력의 독립 encoder 결과를 비교한다. 실제 테스트를 이 문서가
실행한 것으로 기록하지 않는다.

`openapi-catalogue-promotion`/`read-model-reference`/`p-sdk-1`은 초기 형식·verifier로
새 입력 artifact를 생성·검증하지만 확대 catalogue를 BOOTSTRAP 대상으로 표시하지
않는다. 확대 catalogue를 소비하는 pending 앱 노드는 후속
`contract-compatibility-profile`의 실제 완료도 기다리며, 소비할 정확한 source tuple의
SEMANTIC_CONFORMANCE profile/evidence를 확인한다. 해당 tuple의 검증이 없으면 HOLD다.
따라서 초기 producer가 후속 profile 완료를 기다리는 역방향 의존성은 없으며,
추가 catalogue 소비가 초기 profile의 범위를 넘겨 앞서 시작하지 않는다.

## 3. 호환 규칙 후보

호환의 기본값은 **미검증 → 소비 거부**다. major/minor나 0.x 이름만으로 수락하지
않는다. 허용되는 변경의 명세를 승인된 profile에 적고 기존·신규 소비자와 shared
vectors로 증명한다. production compatibility라는 이름을 붙이지 않는다.

| 변경 | 후보 판정·필요 증거 |
|---|---|
| 명령/쿼리 추가 | 기존 의미 불변, strict action allowlist와 SDK 동시 갱신, 구/신 consumer negative tests |
| 필수 필드·enum·금액/identity domain 변경 | breaking 후보; 암묵적 coercion/재매핑 금지, 명시적 새 schema/profile와 승인 필요 |
| receipt 필드/뜻 변경 | strict receipt guards 갱신과 구/신 body→receipt vectors; extra key를 자동 무시하지 않음 |
| 오류 코드/phase 의미 변경 | 성공·거절·UNKNOWN 구분을 보존하는 명시적 mapping; 미정은 DECISION_REQUIRED |
| 선택 필드 추가 | `additionalProperties:false` consumer가 수락한다고 가정하지 않음; 검증 결과로 결정 |
| transport/CORS/readiness 변경 | 허용 loopback origin·opt-in·one attempt·no fallback 보존; URL/auth/retry 자동 생성 금지 |

지원 기간·호환 window·제품 가격/수수료·SLO 수치는 이 설계가 발명하지 않는다.
N/N−1 검사는 승인된 두 fixture version으로 수행하는 **시험 방법**이며, 운영 버전
지원 계약이나 release 약속이 아니다. 승인되지 않은 이전 버전은 unsupported로 표시한다.

## 4. producer 변경과 계획 의존성

catalogue 변경 한 번마다 생성 SDK와 manifest를 같은 source 입력에서 새로 만든다.
`contract-compatibility-profile`이 한 번 끝났다는 이유로 후속 변경이 검증됐다고 하지
않는다. 다음 노드 명세에 해당 의무를 붙인다.

| 노드 | 의무 |
|---|---|
| `p-sdk-0` | A3/ARCHITECTURE; §2.1 초기 형식·BOOTSTRAP profile·최소 verifier·golden vectors와 원본 catalogue SDK 재현 생성 |
| `p-sdk-1` | 초기 형식을 재사용해 확대 catalogue의 정확한 source·generator·output artifact와 body/receipt vectors 생성; 후속 의미 profile을 미리 PASS로 주장하지 않음 |
| `openapi-catalogue-promotion` | FSM command catalogue, gate, SDK, manifest 동시 개정; 관련 checks |
| `read-model-reference` | 새 read catalogue와 gate·SDK·manifest 동시 개정; query non-mutation 검사 |
| pending `wave7-marketing-contracts` | 문서 초안 범위를 지킴. 승인된 catalogue 변경을 수행하는 경우에만 SDK·gate·manifest도 갱신; 새 명령 의미는 DECISION_REQUIRED |
| `contract-compatibility-profile` | `p-sdk-1`과 `k-stage3-schema-sdk-conformance` 뒤 초기 verifier를 재사용해 SEMANTIC_CONFORMANCE profile과 정확한 대상 tuple의 positive/negative 의미 검증 증거를 완성 |
| `gate-browser-access` | `p-sdk-0` 뒤 승인된 CORS/transport 분기를 구현. 관련 gate/source 바이트를 바꾸면 같은 delivery PR에서 SDK 재생성과 새 manifest 결합·vectors를 검증. 관문을 닫아 두는 문서만의 분기는 관련 바이트 불변 evidence를 기록 |
| `settlement-policy-deepening`, `booking-resale-admission-deepening`, `f04-mock-deepening` | `p-sdk-0` 뒤 승인된 정책·계약만 개정. catalogue/schema/receipt/계약 의미나 manifest-bound source가 실제 바뀌면 같은 delivery PR에서 SDK·manifest와 해당 vectors를 갱신 |
| `readiness-extensions` | `p-sdk-0` 뒤 D-3 경계 안에서 작업. 관련 schema/receipt/계약·source 바이트가 바뀔 때만 같은 delivery PR의 SDK 재생성·새 manifest·vectors를 요구하며, 단순 관측/문서 변경으로 qualification을 발명하지 않음 |

위 다섯 producer는 형식·최소 verifier를 먼저 확보하도록 `p-sdk-0`을 선행으로 둔다.
관련 바이트 변경의 artifact 갱신은 별도 후속 노드가 언젠가 해 주는 일로 미루지 않는다.
transport만 바뀌어 SDK 출력이 같아도 실제 재생성과 새 source/gate 결합을 검증한다.
문서만 바뀌는 분기는 manifest-bound 입력의 바이트 대조를 남긴다. 아직 후속 의미
profile이 없다면 확대 catalogue를 BOOTSTRAP으로 적격화하지 않으며, 소비자는 해당
변경의 정확한 SEMANTIC_CONFORMANCE tuple/evidence가 확보될 때까지 HOLD다.

앱의 새 pending `consume-p-sdk-1`은 `p-sdk-1`과 compatibility-profile의 실제 완료를
기다린다. FSM 결합 다섯 노드와 `browser-gate-path`도 이 최종 SDK 소비를 먼저 기다린다.
`bind-list-read`는 이 SDK 소비와 `read-model-reference`/`p-sdk-1`을 기다린다.
초기 `consume-p-sdk-0` 이외 pending 앱 노드에는 후속 profile 완료의 명시적 외부
선행을 둔다. 이 선행은 기본 verifier의 제공 시점과 후속 의미 검증 시점을 구분하며,
그 자체로 소비할 새로운 tuple의 qualification을 대신하지 않는다. Wave 6-A의 기존
`w6a-evidence` 최소 gate와 active 노드의 선행은 바꾸지 않는다.
그 이후 catalogue 변경을 소비하는 각 앱 노드는 **그 변경의 정확한 새 manifest**와
생성 SDK를 다시 검증한다. 초기 SDK 소비의 PASS를 후속 버전으로 옮기지 않는다.

## 5. 저장소 사이 완료와 대기 노드

현재 active plan에는 `depends_on_external`을 넣지 않는다. #83 최초 후보의 checkpoint는
protocol pending 1개와 commerce pending 20개, 총 pending 21개였다. 이번 후속 개정은
[프로토콜 완료 설계](PROTOCOL_COMPLETION_DESIGN_KO.md)의 여섯 노드와
[금융 설계](FINANCE_COMPLETION_DESIGN_KO.md)의 후보, commerce 후속 노드를 추가한다.
현재 분모의 정본은 각 저장소 active plan + 완전히 결합된 pending catalogue의 정의 집합이며
금융 별도 inventory는 같은 정의를 복제해 세지 않는다. 제출 PR은 최종 실제 수를 기록한다.
현재 실행 방식은 확인된 선행 병합·보호된 evidence 뒤 사용자 병합의 plan revision이다.
pending의 `astra_auto_merge=true`는 별도 후보 위임이다. 실제 승인 범위와 해당 중앙
기능의 채택·qualification·attestation 없이는 실행이나 병합 권한이 되지 않는다.

미래 중앙 외부 의존성 기능을 채택하려면 독립 감사, 사용자 채택, root 설치,
qualification/canary, runtime attestation, 승인된 pending catalogue의 immutable commit,
계획 개정 승인 규칙을 먼저 고정한다. 채택 전에는 완료 이벤트만으로 pending을
active plan에 자동 편입하거나 envelope를 만들지 않는다.

외부 완료 settlement는 중앙 정의의 전체 binding을 검증해야 한다. 후보 필드는
`repository`, `program_id`, `node_key`, `approved_plan_commit`,
`node_definition_sha256`, `task_issue`, `task_revision`, `writer_launch_id`,
`delivered_pr`, `delivered_head`, `merge_commit`, `protected_receipt_id`,
`runtime_attestation_id`이며 `protected_receipt_sha256`도 결합한다. `artifacts`와
selector가 요구한 `qualification_state`/`qualification_evidence_ids`도 검증한다.
GitHub 댓글·OpenAPI pin·명칭이 같은 PR만으로 완료를 추론하지 않는다. 기존
protected root ledger/host pin의 signature/issuer와 revision, protected receipt 및
실제 merge ancestry까지 검증한다. 새 cross-host signer/key를 만들지 않으며 중앙이
등록·보호하지 않는 upstream은 UNSUPPORTED_AUTHORITY로 HOLD한다.
필드 이름·서명 format의 정본은 실제 채택된 중앙 schema이며 임의 값을 만들지 않는다.
짧은 tuple의 일부 일치만으로 READY를 부여하지 않는다.

upstream 완료 한 사건은 durable dedupe key로 한 번만 기록하고, 승인된 downstream을
한 번 깨운다. polling, 반복 model 호출, 무조건 재시도는 없다. 오래된 receipt·다른
head·다른 plan·중복/역순 event·알 수 없는 signature는 거부하고 해당 노드를 HOLD한다.

### 5.1 사용자 결정 결과와 후손 적용 범위

User-only 결정 문서가 병합돼 `DONE`인 것과 권고한 기능이 실제 채택된 것은 별개다.
해당 immutable 결정과 승인된 scope에서 다음 결과를 구분한다. 이 명칭은 적용 범위를
보고하는 설계 규칙이며, 기존 중앙 schema에 새 node_state나 자동 판독기를 추가한 것이 아니다.

| 결정 결과 | 후손 구현과 완료 처리 |
|---|---|
| `ADOPT` | 실제 선택된 backend/capability와 승인 입력·필요 evidence가 있을 때만 그 범위의 정상 구현을 진행 |
| `DEFERRED` (`none yet`, 아직 선택하지 않음 포함) | 영향을 받는 구현·소비는 `WAITING/HOLD`로 보존. 전체 catalogue와 분모에서 지우지 않고 자동 대안이나 완료를 만들지 않음 |
| `DECLINED` | 정상 구현은 계속 HOLD. 비작성자 검토와 User 병합의 적용 범위/계획 개정이 정확한 영향 node 정의·digest, 제외 또는 결정에 결합된 비구현 산출물, 이전·개정 분모를 고정해야 다음 처리가 가능 |
| 불명확하거나 승인 근거 없음 | HOLD. 문서 병합·명칭·recommendation만으로 ADOPT를 추론하지 않음 |

한 분기가 거절됐다고 모든 후손을 자동으로 `DONE`이나 해당 없음으로 바꾸지 않는다.
승인된 개정 전에는 원 정의와 선행을 그대로 보존한다. 결정에 결합된 비구현 note가
승인된 산출물이라면 그 실제 제출·독립 검토·병합 evidence를 따로 기록하며, 기술 구현·
서비스 qualification·제품 수용·출시 증거로 승격하지 않는다. closeout은 구현됨·보류·
거절 후 승인된 적용 범위를 각각 표시하고 분모 변경의 승인과 전후 catalogue를 보존한다.

`k-stage4-adoption-decision`의 아직 없음은 DEFERRED다. stage5와 onsale, stage6/7,
CPU/GPU 및 후속 protocol/Finance/commerce 구현은 필요한 실제 backend/capability 없이
진행하지 않는다. `fin-ledger-contract` 같은 준비 ADR·schema·coverage 문서는 승인된
준비 범위 안에서 먼저 작성할 수 있지만 계획됨·선택됨·구현됨·없음을 구분해야 한다.
원 경제 사건이나 commit/source cut·durability를 발명해서 뒤 구현의 선행을 충족시키지 않는다.

현재 중앙은 이 결정 결과를 새 wire field로 해석하지 않는다. 실제 적용 범위·선행 검증은
채택된 등록/계획 개정과 materialization에 결합해야 하며, 지원되지 않는 자동 조건부
dispatch나 plan 편집 권한을 이 문서가 만들지 않는다. 해당 검사 없이 결정 문서 DONE만
보고 정상 구현 envelope를 만들어서는 안 된다. 독립적인 승인된 준비·다른 분기는 계속할 수 있다.

## 6. 완료의 네 측면

| 필드 | 값 | 의미 |
|---|---|---|
| `node_state` | `NOT_STARTED / WAITING / IN_PROGRESS / DONE` | 신규 정규화 query 후보. DONE은 중앙 기존 core가 계산한 host-pinned exact delivered HEAD의 유효한 target 병합 predicate와 같음 |
| `qualification_state` | `NOT_REQUIRED / UNQUALIFIED / PARTIAL / QUALIFIED` | 필요한 환경/서비스와 그 시험이 실제로 확보되었는지 |
| `acceptance_state` | `NOT_REQUIRED / PENDING / ACCEPTED / REJECTED` | 필요한 사용자/제품 채택 판정 |
| `release_state` | `NOT_AUTHORIZED / NOT_RELEASED / RELEASED` | 별도 출시 권한과 실제 출시 사실 |

post-merge 시험·서비스 evidence는 요구된 task deliverable check 또는 별도
qualification/acceptance 측면에서 판정한다. node_state DONE의 중앙 predicate를
이 문서가 더 늘리거나 독자적으로 계산하지 않는다.
qualification에는 대상 mode/source/evidence를 함께 기록한다. stub, synthetic 또는
loopback-reference의 QUALIFIED를 production QUALIFIED로 표시하지 않는다.
해당 User-only 의사결정 문서가 DONE이어도 별도 실제 배포·자금·키 권한은 열리지 않는다.
노드별 완료와 양 저장소 프로그램 완료를 분리하고 active/pending/User decision/external
input/qualification hold 수를 각각 집계한다. pending 노드를 분모에서 없애 전체 완료라고
보고하지 않는다. 초기 95개에서 후보 3개를 추가한 **98개는 #83/#16의 이전 checkpoint**다.
후속 protocol·Finance·commerce 후보를 포함한 전체 정의를 다시 세며, 최종 protocol closeout은
기존 active 전체와 pending의 나머지 모든 정의를 기다린다. 새로운 User 승인·실 자금·출시
권한을 이 집계가 만들지 않는다.

## 7. 수용·거부 시험과 증거

- 같은 입력으로 생성 SDK와 manifest가 byte-identical이고, 양 독립 consumer가 shared vectors에 일치.
- contract/gate/SDK 중 하나만 옛 버전, wrong source commit, extra receipt field,
  domain/schema 혼합, truncation/UTF-8/정수 범위 오류를 쓰기 전에 거부.
- source 변경 후 이전 manifest/CI/qualification receipt를 재사용하지 못함.
- manifest를 보고 producer·consumer exact commit과 checks를 재현할 수 있음.
- 외부 receipt 중복/역순/wrong node·head·plan·issuer, merge 뒤 source drift, UNKNOWN은
  재실행 또는 조기 편입을 만들지 않음. 필드 누락은 미검증으로 HOLD.
- commerce final closeout은 필요한 각 표면과 adverse journey의 binding/evidence matrix를
  검증. stub PASS, live suite skip, 문서로만 완료한 browser-path 선택을 구분.
- 실제 qualification/acceptance/release evidence가 없으면 해당 측면은 실제 상태를 유지.

이 PR에는 설계 문서와 candidate plan만 있다. verifier/SDK/앱/E2E 구현, 실제 서비스
시험, 독립 Fable 감사·host qualification·배포를 실행한 것으로 보고하지 않는다.

중앙 bootstrap의 #44/#45 대체 후보는 [#46](https://github.com/BeautifulMind-JT/ai-ops-control-plane/pull/46)이며, 그 위 [#47](https://github.com/BeautifulMind-JT/ai-ops-control-plane/pull/47) HEAD `94a768e19df12703ea0b9a49e49972feb2f6ef4f`에 실패 보존·검증된 한도 한 번 재시도 source 후보가 추가됐다. 구현 source와 실제 설치·qualification을 구분한다. 기존 #44의 DECISION_REQUIRED를 PASS로 간주하지 않는다. PA-1 권한 예외, 독립 exact-HEAD 감사·User 채택·실제 보호 서비스 authorization·host qualification·activation은 PENDING이다. 외부 완료/전체 완료 query 후속 기능도 미구현이며 전체 실행은 NOT_READY다. 최종 registration에는 실제 채택·qualification commit/evidence를 pin해야 한다.
