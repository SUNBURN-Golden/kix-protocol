# KIX Protocol — 의미·권위·복구를 끝까지 연결하는 설계 후보

2026-10-01. 상태: **PENDING 설계·계획 개정 후보**. 제품 구현 또는 운영 채택 기록이 아니다.
현재 정본 `docs/DEVELOPMENT_PLAN.md`, 모델 1, 프로그램 결정 D-1~D-3, 로드맵 R-1의 승인·잠금 범위를 보존한다.

## 1. 이어받은 범위와 고도화의 목적

설계 작업선은 PR #81 → #82 → #83이며, 이 개정의 정확한 입력은 #83 HEAD
`b665f9a0ad41a46e2169cb142b91d598665aa7ab`이다. 작업 시작 때 읽기 전용으로 관측한
main은 `78b78b1b4a4ffe92de461edd351235ce858b335a`다. main이 더 새롭다는 이유로
후보 작업선을 재정의하거나 묵시적으로 rebase하지 않는다. 제출 HEAD와 최종 CI는 PR에서 확인한다.

기존 active `kix` 67개와 기존 pending `wave7-marketing-contracts`를 보존한다.
새로 만드는 여섯 후속 노드는 같은 pending catalogue에 둔다. Finance는 별도 저장소가 아니라
이 프로토콜의 경제·관측·회계 기능으로 연결하며 [금융 설계](FINANCE_COMPLETION_DESIGN_KO.md)의
새 노드도 같은 inventory에 한 번만 센다. commerce 소비 구현은 그 저장소가 소유한다.
원래 32개 항목의 이름·역사 라벨은 바꾸지 않는다.

고도화의 목적은 문서가 존재한다는 이유로 완료 처리되는 구간을 없애는 것이다.
SDK 파일은 계약 의미의 검증이 아니고, Rust 타입 검사는 데이터 출처 인증이 아니며,
로컬 저널은 체인·은행 정본이 아니다. 각 후속 노드는 정확한 입력과 증거를 연결하고
해결되지 않은 경계는 필요한 담당자와 HOLD 이유를 남긴다.

| 기존 자산 | 이 개정이 보강하는 경계 | 구현 담당 |
|---|---|---|
| BOOTSTRAP/SEMANTIC_CONFORMANCE manifest | 현재 producer tuple의 생성·검증·소비, 변경 때 새 qualification | 기존 SDK/profile 노드; 새 canonical/read conformance |
| FeatureIR·schema-bound validator·semantic helpers | 전체 실행 결과와 validator/decoder의 책임 구분 | 기존 CPU analytics; 새 FeatureIR conformance |
| KIX-BCS1 codec·고정 golden vector | 실제 schema를 쓰는 독립 소비자, JSON/CE1/BCS namespace 분리 | 기존 stage3; 새 canonical identity conformance |
| D-3 readiness fault suite·stage5 후보 | ACK·first result·inbox/outbox·재생의 원자적 단위 검증 | 기존 stage5; 새 local recovery conformance |
| reference query·read-model 계약 | source cut/projection watermark·관측 receipt·권위·stale 구분 | 기존 read-model; 새 read projection evidence |
| 개별 노드 완료 | 전체 정의·User decision·외부 입력·qualification의 분모와 최종 보고 | 새 integration evidence closeout |

## 2. 무엇을 실제로 검증했는지 나타내는 증거 계약

후속 결과마다 대상과 증거를 다음처럼 기록한다. 이 표는 승인 전 설계 필드이며
공개 API를 곧바로 변경하는 권한이 아니다. 실제 계약 개정·A3 검토 이후 schema를 고정한다.

- **실행 대상:** source commit/tree, runtime 또는 reference path, dependency/toolchain pin,
  정확한 fixture corpus와 seed, 승인된 schema/domain/semantics/profile revision.
- **자료 대상:** 원천 dataset id·schema revision·snapshot digest, 권위 종류, source cut,
  projection watermark, asset/registry version/hash, 접근 scope와 export 경계.
- **증거 대상:** 검증 command, 입력·출력/오류 digest, 원본 결과·실패 재현 경로,
  `PASS / FAIL / BLOCKED / NOT_RUN`과 실제 검사 대상 mode. skip은 PASS가 아니다.
- **완료 대상:** 중앙의 기존 host-pinned exact delivered HEAD 병합 predicate,
  qualification/acceptance/release 상태와 각 증거. artifact identity와 감사·승인은 분리한다.

| mode | 증명 가능한 범위 | 유지되는 한계 |
|---|---|---|
| `REFERENCE_IN_MEMORY` | 선언된 synthetic command/receipt 및 경제 FSM 전이 | 영속 ACK·실 제공자 사실·체인 확정 아님 |
| `READINESS_LOCAL` | D-3 단일 작성자 로컬 파일의 재생과 제한된 장애 사례 | protocolTruth/productionConformance/productionReadiness/productionEndpoint/FSM durable 모두 false |
| `BACKEND_LOCAL_CONFORMANCE` | User 채택 backend의 명시한 transaction/ACK/fault model에서 같은 계약 | production 자격·분산 fencing·은행 exactly-once로 전이하지 않음 |
| `MOVE_LOCALNET` | 고정 localnet package/network/schema에 대한 실행·거절 증거 | testnet/mainnet 운영 권한·finality 운영 보장 아님 |
| `PRODUCTION` | 별도 승인·실 환경 시험이 있을 때만 해당 범위 | 현재 후보에는 없음; 문서·mock·localnet의 결과를 승격하지 않음 |

mode별로 증거를 따로 둔다. 실행이 없던 mode는 NOT_RUN 또는 UNQUALIFIED다.
권위·서명·현재성·승인 근거가 없는 입력을 synthetic 이외의 사실로 바꾸지 않는다.

## 3. producer 계약과 SDK를 같은 입력으로 묶기

[CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md](CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md)의
manifest-v1, BOOTSTRAP/SEMANTIC_CONFORMANCE 구분을 계승한다. 최초 verifier는 `p-sdk-0`,
확대 catalogue의 의미 검증은 `contract-compatibility-profile`이 소유한다. 새 후속 노드가
초기 producer의 선행이 되어 역방향 의존성을 만들지 않는다.

### 3.1 immutable artifact의 작성·확인 순서

1. 승인된 계약/FSM/gate/SDK/vector의 실제 바이트를 producer source commit으로 고정한다.
2. 그 source와 tree, 두 OpenAPI blob/hash, 생성기 source/toolchain, SDK output,
   domain/schema/profile/vector를 canonical manifest로 결합한다. manifest 자신의 digest나
   manifest를 추가하는 미래 commit을 본문에 넣지 않는다.
3. verifier는 producer source의 관련 경로, manifest 입력, 실제 vendored SDK/vector를 대조한다.
   후속 기록 commit이 관련 바이트를 바꾸면 새 source/manifest가 필요하다.
4. 독립 exact-HEAD 검토·현재 checks·보호된 완료 evidence는 artifact 밖에서 결합한다.
   consumer의 최종 HEAD도 별도 evidence에서 고정한다.
5. 변경된 catalogue/receipt/query를 소비할 때는 **그 변경의 정확한 새 tuple**을 검증한다.
   `contract-compatibility-profile` 노드가 과거에 DONE이었던 사실은 새 tuple의 qualification이 아니다.

원본 catalogue의 BOOTSTRAP를 확대 query나 Finance catalogue의 SEMANTIC_CONFORMANCE로
승격하지 않는다. domain/schema/receipt/error의 의미 변경은 명시적인 profile 개정과
positive/negative vectors를 요구한다. 필수/선택 필드가 늘 때 strict consumer가 자동으로
호환된다고 추론하지 않는다. 지원 기간, stable 1.0, 배포·registry publishing은 별도 결정이다.

### 3.2 SDK의 수치·오류·전송 경계

- protocol `u128 atoms`는 JavaScript Number로 바꾸지 않는다. 기존 schema가 정한
  bounded integer/string 표현과 typed parse를 사용하고 zero/max/범위 밖/coercion을 검사한다.
  display formatting으로 서명·hash·경제 금액을 재구성하지 않는다.
- 업무 성공, 업무 거절, 전송/파싱 실패, UNKNOWN을 서로 다른 typed 결과로 유지한다.
  timeout·빈 응답·일시적 오류는 command 실패 또는 retry 허가가 아니다.
- actor 문자열은 인증이 아니며 base URL·인증 자격·재시도 전략을 SDK가 발명하지 않는다.
  loopback opt-in·one attempt·no fallback 경계를 보존한다.
- 실제 승인되지 않은 schema/명령/enum은 쓰기 전에 거부한다. 기존 receipt를 새 receipt의
  부족 필드나 승인 값으로 보충하지 않는다.

## 4. FeatureIR의 검증·실행·자료 인증을 분리

정본은 `runtime/FEATURE_SEMANTICS_V1.md`다. #83에는 실제 schema-bound validator와
과거 F64/type 회귀, `kix-feature-semantics`의 scalar helpers가 있다. 전체 Polars compiler와
전체 scalar pipeline, catalog 서명/출처 인증, 실제 CPU/GPU 실행이 완성됐다고 표시하지 않는다.

### 4.1 입력과 실행 경계

`validate()`는 구조적 사전 검사다. 실행은 신뢰할 수 있는 exporter/catalog 경계가 공급한
schema에 대해 `validate_with_schemas()`로 얻은 `ValidatedFeaturePlan`만 받는다.
검증기는 catalog 인증을 대신하지 않는다. 실행 직전 dataset/schema/snapshot와 원본 plan의
binding을 확인하고 validation 뒤 입력이 바뀐 경우 거부한다. 검증한 계획을 serializer나
backend adapter가 암묵적으로 다른 의미로 바꾸지 않는다.

parser는 wire bytes/배열/문자열/재귀 할당을 schema의 승인된 유한 예산으로 먼저 제한한다.
현재 validator의 1,024 stages, 표현식 깊이 64, 총 100,000 nodes는 실제 구조 검사 한도다.
이 값들이 wire parsing의 전체 메모리 상한이라고 주장하지 않는다. 각 계층의 경계값과
경계 밖 입력, unknown fields/schema, 중복 dataset/column/output, truncated 입력을 검사한다.
새 예산과 정책값이 필요하면 Astra 결정으로 닫고 수치를 발명하지 않는다.

### 4.2 의미 불변식과 확인할 오류

| 의미 | 요구되는 conformance |
|---|---|
| null/filter/join/group/sort | null drop/equality/key inclusion/ordering/stability가 IR의 명시값과 같음; 엔진 default 금지 |
| 정수·금액 | overflow는 ERROR; wrap/saturate/float coercion 금지; asset/registry tuple 혼합 거부 |
| Fast64 | `(asset_id, registry_version, registry_hash)` 일치와 `atoms <= executionMaxAtoms <= i64::MAX`; 새 registry에 이전 판정 승계 금지 |
| Wide128 | lossless export만; 지원하지 않는 SUM/MEAN/arithmetic을 명시적으로 거부 |
| F64 | 정수 MEAN 또는 Project 루트 DivideToF64에서 terminal 생성; finite-only; 이후 Limit만; join/group/sort/filter/중첩 divide/다음 arithmetic 금지 |
| aggregate | COUNT(empty)=0; 다른 empty/all-null은 NULL; COUNT(*)만 input 생략; output type과 integer 입력 정확히 대조 |
| column scope | Project의 모든 표현식은 stage 입력만 참조; 새 alias를 같은 Project의 입력으로 쓰지 않음; join column 충돌 거부 |
| category/ordering | dictionary index 대신 decoded logical value 비교; 요구된 stable order만 exact 비교 |

terminal F64 tolerance는 versioned policy가 실제 승인된 fixture에 있어야 한다.
미정이면 conformance를 BLOCKED로 둔다. 금액·identity·권리 판정에는 이 tolerance를 사용하지 않는다.

`k-stage7-cpu-analytics-sql-audit`가 CPU 실행/비교 자산을 먼저 제공한다. 새
`protocol-featureir-conformance`는 이를 재사용하여 원시 입력→검증된 계획→전체 결과/오류의
추적을 완성한다. expected result를 production adapter 자체로 계산하지 않는다.
scalar 계약 예와 별도 logical oracle의 출처를 기록하고 source-informed 일치를 독립 명세
증명으로 재라벨링하지 않는다. native GPU가 없으면 NOT_RUN이며 CPU 결과로 GPU PASS를 만들지 않는다.

## 5. canonical identity와 transport를 연결

정본은 `runtime/CANONICAL_BINARY_BCS_V1.md`이며 실제 `kix-bcs1` codec과 고정 S07-A
vector를 재사용한다. 지원하는 실제 schema는 trait의 immutable domain/schema/version/body bound를
사용한다. 호출자가 envelope의 domain/version을 협상해서 다른 schema에 맞추지 않는다.

- JSON/CE1 transport 또는 legacy fixture의 hash와 `SHA256(KIX-BCS1 envelope)`를 분리한다.
  manifest의 canonical JSON digest는 artifact identity이지 BCS 경제 객체 identity가 아니다.
- typed parse 뒤 semantic validation을 거친 객체만 canonical bytes를 만든다. 표시 문자열,
  JavaScript rounding, json key order로 object identity를 재계산하지 않는다.
- magic/domain/schema/version, field order/width/meaning, sorted-set 규칙, enum discriminant를
  승인 schema에 고정한다. 변경은 새 schema/version이며 기존 의미의 재사용은 금지한다.
- Rust encode/decode/hash와 독립 TypeScript client의 같은 실제 supported schema를 대조한다.
  test-only `65535/65535` domain을 실제 production schema로 사용하지 않는다.
- 잘못된 magic/domain/schema/version, noncanonical ULEB128, malformed UTF-8, trailing/truncated,
  bounded length/range 밖과 구/신 tuple 혼합을 거부하는 corpus를 재사용·보완한다.
- Move production type이 없는 schema는 Rust↔Move qualification을 BLOCKED/NOT_RUN으로 둔다.
  허용 localnet package/type이 실제 존재하는 경우만 exact package/network와 vector를 결합한다.

변경을 위해 잠금 kernel 파일을 손대야 하면 reproduction과 BLOCKER를 제출한다.
codec 범위의 통과로 kernel 의미·체인 확정·production conformance를 주장하지 않는다.

## 6. read projection은 관측이며 실행 권한이 아니다

새 `ReadObservationV1`은 기존 read-model 계약의 **후속 schema 후보**다. query/필드의 최종 의미는
해당 A3 계약 결정 이후 고정한다. 새로운 catalogue의 exact SDK/manifest/profile를 같은 source에서
만들고 소비한다. 공용 query를 승인 없이 바로 추가하지 않는다.

| 후보 필드 | 의미·거부 조건 |
|---|---|
| `read_schema_version`, `query_digest` | 승인 query/schema와 정확한 normalized query 입력; unknown/mixed version 거부 |
| `subject_scope` | 조회가 허용된 subject/visibility 범위; actor 이름이 인증을 대신하지 않음 |
| `fixture_mode` | REFERENCE_IN_MEMORY/READINESS_LOCAL 등 실제 대상; synthetic을 실 운영으로 표시하지 않음 |
| `source_cut` | source kind/id·generation·position domain/value·필요한 권위 evidence의 결합 |
| `projection_watermark` | 그 projection이 반영한 동일 source의 범위; 서로 다른 source/domain의 숫자를 비교하지 않음 |
| `snapshot_digest` | query가 실제 읽은 immutable dataset/state snapshot; 페이지 사이 snapshot drift 거부 |
| `observed_receipt_refs` | projection에 반영된 정확한 receipt identity/operation/version; existence가 현재 실행 허가를 뜻하지 않음 |
| `producer_manifest_digest`, `profile_revision` | 승인 schema/gate/SDK/vector의 정확한 current producer tuple |

cut은 단순 벽시계 timestamp가 아니다. 체인 position, provider observation, off-chain commit을
같은 숫자 하나로 합치지 않는다. watermark가 필요한 receipt/cut에 못 미치면 lag/WAITING을
명시한다. missing/UNKNOWN을 성공으로 보충하지 않는다. pagination cursor는 query/scope/snapshot/
ordering tuple에 결합하고 다른 tuple에서 재사용하지 않는다. export/access 권한 변경 뒤 옛
cursor나 cached view를 새 권한 근거로 재사용하지 않는다.

관측은 예약·payment fact·chain issuance·admission consume·return required·실 환불을
각각 표시한다. 읽기 성공이나 newest timestamp를 command 성공, UNKNOWN 해소 또는
새 외부 실행 권한으로 변환하지 않는다. authority별 evidence가 없으면 그 상태를 모른다고 둔다.

commerce는 refresh epoch/route/session으로 stale UI 응답을 차단하고 일관된 snapshot을
사용한다. 이 client epoch는 protocol execution generation·chain lease generation이 아니다.
새 `protocol-read-projection-evidence`는 non-mutation, mixed-cut, lagged view, cursor drift,
visibility, receipt binding을 검사하는 offline/loopback corpus를 제공한다. 실제 인증이나
공개 서비스가 없는 fixture는 그 범위의 qualification만 보고한다.

## 7. transaction·재생·UNKNOWN의 경계

backend 후보 비교의 유일 정본은 `docs/DEVELOPMENT_PLAN.md §9`다. 이 문서는 후보 채택을
반복하거나 자체 저장 엔진을 새로 설계하지 않는다. 새 recovery task는 기존 stage5와
공통 readiness suite 뒤에서 **User가 실제 채택한 backend의 local transaction 계약**을 검증한다.
backend가 선택되지 않았다면 BLOCKED이며 대체 backend를 임의로 켜지 않는다.

결정 문서 병합과 실제 backend 채택은 [호환·완료 설계 §5.1](CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md#51-사용자-결정-결과와-후손-적용-범위)에
따라 분리한다. `none yet`는 DEFERRED이며 stage5와 그 뒤 경제·export·CPU/GPU·
후속 conformance/Finance 구현을 기술 완료로 만들지 않는다. DECLINED도 승인된 적용
범위/계획 개정 전에는 같은 HOLD다. 결정에 결합된 비구현 note를 허용하는 개정은
User가 병합해야 하고, 원 정의·영향 범위·이전/개정 분모와 실제 note evidence를 보존한다.
준비 ADR와 독립적인 승인 작업은 계속할 수 있지만 없는 backend/source cut을 구현된
것처럼 쓰거나 서비스 qualification으로 바꾸지 않는다.

### 7.1 하나의 local durable transaction에 포함할 것

승인된 backend adapter의 transaction 계약은 업무 상태·명령의 immutable first result·
재고/권리 reference·정규화 inbox observation·중복 지문·outbox 의도를 같은 원자적 단위로
묶어야 한다. task는 실제 지원되는 원자적 경계와 ACK의 의미를 명시한다. 지원하지 못하는
범위는 구현 완료로 보고하지 않고 채택 결정의 부족으로 되돌린다.

provider/event id와 provider/account/environment/API-operation의 경제 identity는 구분한다.
같은 operation의 다른 이벤트가 경제 효과를 다시 적용하거나 서로 다른 operation을 하나로
합치지 않도록 기존 adapter-event-identity 계약을 재사용한다. conflict는 정규화해 덮어쓰지
않고 evidence와 review/UNKNOWN 상태로 보존한다.

외부 실행 의도가 있다면 dispatch 전에 그것과 관측 슬롯의 bound가 내구 기록에 있어야 한다.
local mock의 네트워크 실행 기록을 실 PG·은행 실행 증명으로 만들지 않는다. 새 노드는 실
외부 호출을 하지 않는다. snapshot에는 schema/semantics/source cut와 원본 결과의 출처를
결합하며 cache eviction과 권위 있는 dedupe/evidence 폐기를 혼동하지 않는다.

### 7.2 확인할 crash·재생 사례

- transaction 시작 전, 변경 뒤 commit 전, durable commit 뒤 response 전 crash.
- outbox intent 기록 뒤 mock dispatch 전·직후의 중단과 ambiguous response.
- 중복/역순/늦은 capture·상충 observation, 동일 command+다른 body, changed generation.
- 찢긴 끝 frame과 중간 checksum 오류, unsupported schema, 잘못된 snapshot/cut,
  command/observation budget 고갈과 이미 보존된 first result의 read-only replay.
- local concurrent hold·GA oversubscription·같은 admission consume·같은 경제 observation의
  한 번 전이. 그 결과는 명시한 단일 backend local 모델의 범위에서 해석한다.

`readiness/test_faults.py`를 먼저 coverage map에 매핑한다. 이미 검사하는 찢긴 쓰기,
commit 전 crash, replay, budget, 동시 보유를 중복 작성하지 않고 부족한 실제 stage5 경계를
검사한다. original result·captured fact·return obligation을 재생 중 지우지 않는다.
역사 입력으로 복원하는 것은 새 외부 실행 권한이 아니다. 현재 권한/cut이 불명확하면
영향을 받는 신규 소비·재위임을 HOLD한다. timeout은 최종 실패나 슬롯 해제의 근거가 아니다.

기존 #11 저널과 v4를 묵시적으로 통합하지 않는다. (a), R2, 자체 복제·합의·다중 작성자,
새 종결·증거 GC 또는 두 잠금 blob의 수정은 이 설계가 열지 않는다.

## 8. 후속 DAG와 전체 완료 분모

`docs/decisions/PROGRAM_ROADMAP_20260930_PENDING.json`이 새 여섯 노드의 실행 입력 후보를
소유한다. 여기서 지정한 acceptance는 계획 채택 뒤 task envelope로 materialize한다.
기존14 User-only와 선행은 유지하며, 계약 변경 노드도 user_merge=true/A3로 바꾼다. 현재 병합 경계는 PROGRAM_ASTRA_DELEGATION.md의 spec 판정 표다.

| 새 pending 노드 | 선행 | 제출·수용 조건 |
|---|---|---|
| `protocol-runtime-boundary-register` | — | 모든 경계의 mode/authority/source/evidence/owner/gap register, 기존 coverage map과 잠금 대조 |
| `protocol-featureir-conformance` | boundary; stage3; CPU analytics | 전체 입력→검증된 계획→결과/오류 trace, 논리 oracle/vector, F64/type/money/ordering/budget 거부 사례 |
| `protocol-canonical-identity-conformance` | boundary; stage3; compatibility profile | 실제 supported schema의 Rust/독립 client bytes/hash/error 일치와 namespace/malformed corpus |
| `protocol-read-projection-evidence` | boundary; read-model-reference; compatibility profile | 승인된 query envelope/cursor/receipt/cut/watermark corpus와 exact tuple 소비 증거 |
| `protocol-local-recovery-conformance` | boundary; stage5; readiness suite | 채택 backend의 transaction/ACK/crash/replay/UNKNOWN 증거와 coverage gap closure |
| `protocol-integration-evidence-closeout` | 상기 다섯 + 기존 67개 + 기존 Wave7 + 금융 후속 전체 | 전체 inventory, 실제 mode별 증거와 보호된 완료·qualification·acceptance·release 판정 보고 |

여섯 노드 모두 A3/ARCHITECTURE 후보이며 자동 병합 flag는 **채택한 범위 안에서 중앙 executor를
위임하는 후보**다. 이 PR 자체, plan 개정, User-only 결정을 자동 승인하는 flag가 아니다.
새 public schema 의미가 미정이면 Astra 결정으로 HOLD하며 새 정책값·수수료·법률 조건은
각 원 담당자에게 남긴다. 금융 후속은 기존 실자금 해제 결정을 대체하지 않는다.

closeout은 자신을 선행으로 넣지 않고 같은 inventory의 나머지 local 노드 전체를 기다린다.
Finance의 commerce 소비자는 `fin-catalogue-read-model`을 기다리고, Finance closeout이
그 소비를 기다린다. commerce 소비가 protocol 최종 closeout을 기다리는 역방향 edge를
만들지 않는다. 전체 DAG에서 검증하고 unresolved/cycle이 있으면 편입하지 않는다.

최종 결합 후보는 protocol **82개 = 기존 active67 + pending15**이고, commerce **36개 = active10 + pending26**다. KIX 전체 **118개**, 그중 pending **41개**이며 과거 98개/pending21개는 이전 체크포인트다. protocol closeout은 자신을 제외한 81개 local 정의 전체를 선행으로 두며 Finance fragment 8개는 같은 catalogue의 정의와 일치해야 한다. 이 수는 제안 정의의 수이며 승인·실행·완료 수가 아니다.

분모는 승인된 active와 모든 pending 정의의 `(repository, program, node_id)` 집합이다.
같은 금융 정의가 finance 문서·별도 node inventory·protocol pending catalogue에 등장해도
한 번만 센다. 개별 node DONE은 기존 중앙 predicate를 따르며 문서가 추가 조건으로 재정의하지
않는다. 전체 closeout은 각 노드 predicate와 해당 deliverable/qualification evidence를 집계한다.
pending, User decision, external input, qualification hold를 숨겨 전체 완료로 표시하지 않는다.
출시/실자금 권한은 완료 분모와 별도다. 일부 결정 문서의 DONE도 운영 lock 해제를 대신하지 않는다.

closeout은 ADOPT된 실제 구현, DEFERRED로 남은 구현, DECLINED 뒤 User가 승인한
적용 범위/비구현 산출물을 별도 행으로 보고한다. 후손 자동 DONE이나 조용한 분모 축소는
없다. 등록·materialization에서 결정 결과와 승인된 현재 정의를 함께 검증해야 하며,
현재 중앙이 새 결정 결과 parser를 이미 제공한다고 주장하지 않는다.

등록 전에는 새 pending catalogue 전체가 비활성이다. 기존 중앙에 지원되지 않는
`depends_on_external`을 active plan에 직접 넣지 않는다. 실제 upstream merge/evidence 뒤
승인된 plan revision을 만들거나, 별도 채택·qualification된 중앙 기능을 사용한다.
중앙 #47 HEAD `09e161caa652d75e9617caf632b3b9899be35740`은 #47의 **복구 source 후보**다.
소스에서 실패 journal과 검증된 한도 한 번 재시도를 구현했어도 실제 호스트 설치·authorization·
독립 감사·qualification·activation이 확인되지 않았다. 외부 완료 기능·전체 완료 query의
후속 구현도 이 제품 문서가 완성했다고 표시하지 않는다.

## 9. 경계 검토와 제출 증거

| 질문 | 수용 또는 거부 결과 |
|---|---|
| source/schema/gate/SDK/vector 중 하나만 바뀌었는가 | 새 tuple과 새 의미 qualification이 없으면 쓰기 전 거부 |
| validator 통과를 데이터 인증 또는 전체 backend 실행으로 읽는가 | 경계별 evidence 분리; 실제 없음은 BLOCKED/NOT_RUN |
| u128/asset/registry/F64/BCS 영역이 혼합됐는가 | exact typed binding과 negative vector로 거부 |
| read가 다른 cut 또는 lagged snapshot인가 | WAITING/visibility error; command 성공·재시도·UNKNOWN 해소로 승격 금지 |
| crash 뒤 response가 없지만 결과를 알 수 없는가 | original evidence 보존, UNKNOWN fence; 외부 재실행 자동 허가 금지 |
| local durable PASS를 production 또는 distributed PASS로 바꾸는가 | mode·failure model·source/환경 pin이 다르면 별도 qualification 필요 |
| 전체 pending/User-only/Finance가 분모에 있는가 | full inventory와 ancestry/evidence를 대조, 미충족은 그대로 표시 |

이 문서 개정에서는 JSON 구조·ID·DAG·기존 spec/잠금 보존을 검사한다. Rust·Move·SDK·backend
구현이나 실제 성능·장애·서비스 시험을 실행한 결과로 보고하지 않는다. independent Fable
감사와 User 채택, 호스트 qualification은 별도이며 이전 HEAD의 PASS를 새 HEAD로 전이하지 않는다.
