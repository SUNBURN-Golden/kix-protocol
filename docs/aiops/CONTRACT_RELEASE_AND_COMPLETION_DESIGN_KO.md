# KIX 계약 호환 묶음과 개발 완료 설계 후보

공통 후속 규약: [중앙 #45](https://github.com/BeautifulMind-JT/ai-ops-control-plane/pull/45), 후보 HEAD `112110c2c0a996e309abf2c62a57368a9a673126`. [고정 설계](https://github.com/BeautifulMind-JT/ai-ops-control-plane/blob/112110c2c0a996e309abf2c62a57368a9a673126/engineering/docs/PROGRAM_EXECUTION_EVOLUTION_DESIGN_KO.md)는 아직 운영·승인 evidence가 아니다.

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
| semantics | 승인된 compatibility profile의 immutable revision, command/query/receipt schema 집합 digest |
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
| `p-sdk-0` / `p-sdk-1` | 재현 생성, 정확한 source·generator·output manifest, body/receipt vectors |
| `openapi-catalogue-promotion` | FSM command catalogue, gate, SDK, manifest 동시 개정; 관련 checks |
| `read-model-reference` | 새 read catalogue와 gate·SDK·manifest 동시 개정; query non-mutation 검사 |
| pending `wave7-marketing-contracts` | 문서 초안 범위를 지킴. 승인된 catalogue 변경을 수행하는 경우에만 SDK·gate·manifest도 갱신; 새 명령 의미는 DECISION_REQUIRED |
| `contract-compatibility-profile` | `p-sdk-1`과 `k-stage3-schema-sdk-conformance` 뒤에 profile verifier와 positive/negative conformance 증거를 완성 |

앱의 새 pending `consume-p-sdk-1`은 `p-sdk-1`과 compatibility-profile의 실제 완료를
기다린다. `bind-list-read`는 이 SDK 소비와 `read-model-reference`/`p-sdk-1`을 기다린다.
그 이후 catalogue 변경을 소비하는 각 앱 노드는 **그 변경의 정확한 새 manifest**와
생성 SDK를 다시 검증한다. 초기 SDK 소비의 PASS를 후속 버전으로 옮기지 않는다.

## 5. 저장소 사이 완료와 대기 노드

현재 active plan에는 `depends_on_external`을 넣지 않는다. 기존 pending protocol 1개와
commerce 18개에 새 SDK 소비와 최종 closeout 2개가 추가되므로 pending은 총 21개다.
현재 방식은 확인된 선행 병합 뒤 사용자 병합의 plan revision이다.
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
보고하지 않는다. 초기 95개에서 새 후보 3개가 늘어 **전체 정의 98개**다.

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
