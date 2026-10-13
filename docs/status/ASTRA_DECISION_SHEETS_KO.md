# 세 묶음 결정 시트 — 목록 쿼리 값, v5 잔여 정지, RS-0 수락 문장

작업: `plan-astra-decision-sheets-listvalues-v5-rs0` · canonical 선행: 없음.
입력 정본: 이 노드의 명세와 그것이 가리키는 문서다. `.aiops/program.json`에 없는
루프 제안 노드이고 `docs/tasks/`에 과제 파일이 없으며 이슈도 없다.
읽은 기준 커밋: `77517f0c74cd892ca299cacf987cbab64a03337d`
(`git fetch origin main` 뒤의 `origin/main`, 작업 브랜치 HEAD와 같다).

**이 문서는 아무것도 결정하지 않는다. 어느 선택지도 고르지 않는다. 아무것도 보내지
않았고, 어느 담당의 회신도 아니다.** 빌더가 작성한 시트이며 Astra 또는 사용자의
결정이 아니다. 어느 노드의 상태도 바꾸지 않는다.

세 묶음의 결정이 각각 주인은 있는데 답할 준비가 된 시트가 없어 멈춰 있다.
이 문서는 그 세 묶음을 항목별로 모아, 무엇이 열려 있는지, 그 문장이 어디에 있는지,
어떤 답이 와야 다음 노드가 진행하는지만 정리한다.

## 0. 기준

- 노드 입력: `depends_on: []`, `audit_floor: A2`, `astra_gate: None`,
  `user_merge: false`. 루프 제안 노드이며 `.aiops/program.json`에 없다.
- 잠금 blob은 작업 전 요구값과 일치했다.
  `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
  `b607996c83a119c349f1cc90469ac1ba82764e20`. 이 노드는 두 파일을 수정하지 않는다.
- 읽은 문서: [READ_MODEL_QUERIES](../contracts/READ_MODEL_QUERIES.md) 초안 0.1,
  [STATE_LIFECYCLE](../contracts/STATE_LIFECYCLE.md) 초안 0.6,
  [FIRST_BATCH_OPEN_INPUTS](../contracts/FIRST_BATCH_OPEN_INPUTS.md),
  [STAGE2_V5_CRATE_DESIGN_DECISION_20261008](../decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md),
  [RETENTION_PERIODS_PROPOSAL_20261009](../decisions/RETENTION_PERIODS_PROPOSAL_20261009.md),
  [CUT_PROOF_I12_20261008](../decisions/CUT_PROOF_I12_20261008.md),
  [RIGHTS_SCALE_RS0_DECISION_20261008](../decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md),
  [RIGHTS_SCALE_PROFILE](../contracts/RIGHTS_SCALE_PROFILE.md) 0.1,
  [RS0_REVIEW_PACK](RS0_REVIEW_PACK.md),
  [CURRENT_CAPABILITY_REGISTER](CURRENT_CAPABILITY_REGISTER.md),
  [FIRST_BATCH_OWNER_QUESTION_SHEETS_KO](FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md),
  [DEVELOPMENT_PLAN](../DEVELOPMENT_PLAN.md).
- 이 시트가 바꾸는 경로는 이 파일, `docs/README.md`의 위치 포인터 한 줄, 그리고
  `validation/2026-10-13-astra-decision-sheets-listvalues-v5-rs0/README.md`뿐이다.
  계약·결정 기록·프로그램 파일·`docs/tasks/`·`.aiops/`·`reference/v0.3-rc1/**`·
  `runtime/**`·CI는 고치지 않는다.

### 답의 형태와 정지 유지

각 행의 답은 그 담당이 기존 형식으로 가져온다. 제공자·법무·사용자 자료 답변은
[질문서](FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md)의 공통 회신 형식
`질문 번호 / 답변 / 적용 범위·버전 / 근거 자료 위치·작성일 / 회신자·역할`을 따르고,
Astra 판단이 필요한 정책 값·새 명령·결론 구조는 `DECISION_REQUIRED · Astra`의
결정 문장으로, 사용자 수락이 필요한 것은 그 문서가 정한 수락 문장으로 온다.
어느 쪽이든 값은 이 시트가 만들지 않는다.

아래 종류의 답은 노드를 멈춘 채로 둔다.

- 추정치·예상값, 또는 「합리적인 값으로 보인다」는 의견.
- 아직 병합되지 않은 권고·제안·초안의 재진술.
- 그 항목의 담당이 아닌 쪽의 답변(예: 빌더가 정한 정책 값, Astra가 내는 제공자 사실).
- 항목의 일부만 닫는 부분 답변(예: `limit` 상한만 있고 기본값이 없는 답).
- 「미정」·「나중에 정한다」의 재진술.
- 이 시트 자체, 또는 이 시트를 인용한 답.

## 1. 묶음 1 — 목록 쿼리의 열린 값 (`read-model-reference`, commerce `bind-list-read`)

[READ_MODEL_QUERIES](../contracts/READ_MODEL_QUERIES.md) 초안 0.1의 §5, §6, §9가
`UNDETERMINED`로 둔 항목이다. 명령 이름은 2026-10-08 사용자 결정으로 정해져 있고
(`:15`, `:378`), 그 결정은 이 노드에서 숫자를 채우지 말라고 정했다 (`:312`).
조회는 상태를 바꾸지 않으며, 와이어 본문·`operationId`·오류 코드 신규 이름·카탈로그
삽입은 `read-model-reference`의 몫이다 (`:25`).

| 항목 | 질문 | 열어 둔 계약 문장 (파일:행/절) | 답이 여는 것 | 기존 증거 | 담당 | 답의 형태 |
|---|---|---|---|---|---|---|
| `limit` 상한 | 목록 쿼리가 한 페이지에 돌려줄 수 있는 최대 건수를 얼마로 둘 것인가 | `READ_MODEL_QUERIES.md:316` (상한·기본값 둘 다 필요, 값 없음), `:312` (분류 `UNDETERMINED`·담당 Astra), `:387` (§9 표) | `read-model-reference`의 페이지 검사와 거절 시험, `bind-list-read`의 요청 형식 | `limit`가 있고 상한이 필요하다는 문장만 있다. 상한으로 잘린 응답의 `truncated`/`next_cursor` 규칙은 `:317`이 이미 적는다 | Astra | `DECISION_REQUIRED · Astra` 결정. 수치와 적용 범위(어느 목록에 적용되는가)가 든 문장 |
| `limit` 기본값 | 호출자가 `limit`를 주지 않을 때의 쪽 크기를 얼마로 둘 것인가 | `READ_MODEL_QUERIES.md:316`, `:312`, `:387` | 상한과 같은 대상. 둘 중 하나만 닫혀도 페이지 동작은 여전히 미정이다 | 위와 같다. 빈 칸을 임의 기본값으로 채우지 말라는 방향은 `:312`의 「숫자를 채우지 않는다」와 같은 결정이다 | Astra | 같은 결정 문장. 상한과 기본값의 관계(기본값 ≤ 상한 여부)를 함께 적는 문장 |
| 커서 수명 | 발급된 커서를 얼마 동안 유효하게 둘 것인가 | `READ_MODEL_QUERIES.md:319` (수명 미정), `:387` | 커서 만료 정책과 그 거절의 시험 | 커서는 불투명하고 묶음은 `(query, scope, ordering, snapshot)`이며 하나라도 다르면 거절한다 (`:314`). 커서는 허가증이 아니며 가시성 범위가 바뀐 뒤 다시 쓰지 못한다 (`:320`) | Astra | `DECISION_REQUIRED · Astra` 결정. 수명의 단위·기산점·만료 시 동작이 든 문장 |
| 목록 정렬 키 | 각 목록을 무엇으로 정렬할 것인가 | `READ_MODEL_QUERIES.md:315` (정렬 키 선택 미정), `:312`, `:387` | 결정론적 페이지 순서의 구현과 재현 시험 | 순서는 결정론적이어야 하고 같은 정렬 키의 동순위는 유일한 식별자로 가른다는 규칙은 이미 있다 (`:315`) | Astra | `DECISION_REQUIRED · Astra` 결정. 목록별 정렬 키와 동순위 처리를 적는 문장 |
| "열린 리스팅"에 넣을 단계 | `list_open_listings`가 어떤 단계의 행을 열린 것으로 셀 것인가 | `READ_MODEL_QUERIES.md:175` (어떤 단계를 셀지 `UNDETERMINED`. `OPEN_PHASES`는 기존 전이 집합의 이름이지 공개 목록 정의가 아님), `:388` (그 전까지 술어는 `NOT_BOUND`), `:183` | `list_open_listings`의 술어 바인딩과 결과 시험. `NOT_BOUND` 해제 | 최소 공개 추천(phase가 `LISTED`이고 `expired` 거짓이며 `attached` 참)은 `:176`이 적되 그 추천은 결정이 아니라고 같은 행이 적는다 | Astra | `DECISION_REQUIRED · Astra` 결정. 단계 조합과 `expired`·`attached`의 처리를 적는 문장 |
| 요약 키 부분집합의 경계 | 목록 원소에 들어가는 요약 키와 점 조회에만 남기는 키의 경계를 어디에 둘 것인가 | `READ_MODEL_QUERIES.md:83` (부분집합 경계 `UNDETERMINED`·담당 Astra), `:84` (추천은 결정이 아님), §2.1 `:94-96`, §2.4 `:137-138`, §2.7 `:177-178`의 추천 행 | 세 목록의 응답 스키마와 가시성 필터 결합 | 각 쿼리 절의 추천 요약 키·점 조회 잔류 키 목록. 추천 열은 최소 공개이지 결정이 아니다 (`:84`, `:330`) | Astra | `DECISION_REQUIRED · Astra` 결정. 목록별 요약 키 집합을 적는 문장. 가시성 행렬 값과 함께 정한다 (`:83`) |
| 목록의 보존·이력 깊이 | 목록·페이지 결과와 그 증거를 얼마나 어느 깊이로 보존할 것인가 | `READ_MODEL_QUERIES.md:321` (제품 값, 여기서 정하지 않음), `:389` | 조회 결과의 보존 정책과 `ps-02-query-contract`의 델타·재생 입력 | 제품 값이라는 분류만 있다. 네 기간 구조의 주인은 `RETENTION_PERIODS_PROPOSAL_20261009.md` §3 `:42-47`에 있다 | Astra | `DECISION_REQUIRED · Astra` 결정. 보존 대상·기간·깊이를 적는 문장 |
| 가시성 행렬의 칸 값 | 누가(어느 클래스가) 무엇을 볼 수 있는가. 각 칸의 값 | `READ_MODEL_QUERIES.md:329` (칸의 값 `UNDETERMINED`·담당 Astra), 행렬 `:332-338`, `:386` | 행 필터와 필드 노출의 구현. `public listing`, `owner or holder`, `organizer`, `gate role` 칸의 결정 | 클래스 다섯 개와 추천 열은 있다 (`:332-338`). 추천은 최소 공개이지 결정이 아니다 (`:330`). fixture 문자열 비교는 접근 통제가 아니다 (`:340-341`). `operator` 칸은 `k-operator-evidence` 소관이다 (`:338`) | Astra | `DECISION_REQUIRED · Astra` 결정. 행렬 각 칸의 값을 적는 문장 |
| 역할 라벨을 사람·계정에 묶는 일 | 구매자 신원, 즉 역할 라벨을 사람·계정에 묶어 보여줄지의 법률·개인정보 판단 | `READ_MODEL_QUERIES.md:343-344` (법률·개인정보 검토 필요, 담당 사용자, 경로 `tl-legal-brief`, 답 전 `UNDETERMINED`), `:390` | 그 판단에 의존하는 가시성 칸(구매자·보유자 라벨 노출) | 역할 라벨은 저장만 하는 문자열이며 사람·주소·사업자·Sui address가 아니다 (`:345`) | 사용자. 경로 `tl-legal-brief` | `UNDETERMINED` 회신. 라벨의 법적 성격과 노출 허용 범위를 적는 답 |
| 목록 오류 코드 이름 | 커서·스냅샷·`limit` 형식 오류와 페이지 사이 스냅샷 불일치의 오류 코드 이름을 무엇으로 둘 것인가 | `READ_MODEL_QUERIES.md:318` (형식 있는 오류, 이름 미정), `:102`·`:144`·`:183` (코드 이름을 정하지 않음), `:25` (신규 오류 코드 이름은 `read-model-reference`의 몫) | 목록 오류 응답의 와이어 형식과 거절 시험 | 재사용하는 기존 코드는 `INVALID_ID`, `UNKNOWN_*`, 원천 불능 코드 다섯 개다 (`:115`, `:302`, `:144`의 재사용 한계). 이 초안은 새 코드를 만들지 않는다 | `read-model-reference` 소관으로 적힌 대로 (`:25`). 정책 판단이 필요하면 `DECISION_REQUIRED · Astra` | 그 노드의 결정 기록. 이름과 대응 조건을 적는 문장. 기존 코드 재사용 여부를 함께 적는다 |
| 토스 결제 상태 사실 | MID, 웹훅 서명, 결제 상태의 제공자 사실을 무엇으로 확인할 것인가 | `READ_MODEL_QUERIES.md:391` (§9 표), `:351` (담당은 제공자이며 사용자를 거친다) | `payment_ref`·`PAYMENT_NOTED`·`MOCK_COMMIT_OBSERVED`를 제공자 사실로 읽는 경로. 이 조회로 제공자 미확정 항목을 채우지 않는다는 한계는 유지다 | [질문서](FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md)의 T02·T04·T05·T08 행이 이미 같은 사실을 묻는다. 질문서는 전송되지 않았다. `PG_TOSS_CARD_PROFILE.md`의 미확정 항목은 그대로다 | 제공자(토스). 사용자를 거쳐 회신 | `UNDETERMINED` 회신. 질문서 회신 형식의 답 |

## 2. 묶음 2 — `k-stage2-v5-impl`의 잔여 정지

[v5 crate 설계 결정](../decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md)이
사용자 병합으로 채택된 범위 안에서도, 아래 세 전이는 정지다. §6 전이 표의 정지
문장과 그 문장이 가리키는 열린 입력을 대응시킨다. 각 행의 담당은 문서가 적은
그대로이며, 이 시트가 담당을 다시 배정하지 않는다.

| 정지 전이 | 막는 문장 (파일:행/절) | 담당 | 후속 노드가 진행할 수 있는 정확한 조건 |
|---|---|---|---|
| 예약 슬롯 해제 | `STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md:110` (「정지. I12와 I13이 닫히기 전까지 만들지 않는다」), `STATE_LIFECYCLE.md` §5.8 `:541` (후기 사실 custody·처리예산 인계 검증, 전송차단, 원operation·기록 보존. 없으면 해제 금지). 열린 입력: I12 `FIRST_BATCH_OPEN_INPUTS.md:36` (#136 병합, 선택지 1/2/3의 수락 미기록, 비작성자 독립 검토·사용자 신뢰정책 승인 전, `CUT_PROOF_I12_20261008.md:5`), I13 `FIRST_BATCH_OPEN_INPUTS.md:37` (운영/보안 주체·예산·실제 보존/복구 검증, `STAGE2…:139`) | I12: 프로토콜 담당의 기술 증명·비작성자 독립 검토·사용자 신뢰정책 승인. I13: 운영/보안(주체 지명은 사용자) | I12가 수락된 선택지·독립 검토·신뢰정책 승인으로 닫히고, I13이 인계 custody·예산·검증된 복구 증거로 닫힐 때. 그 전에는 인계 술어를 만들지 않는다 (`STAGE2…:181`) |
| 상태를 바꾸는 기록 회수 | `STAGE2…:111` (막는 참조를 나열하는 **읽기 전용** 자격 보고만 만든다. 상태를 바꾸는 회수는 정지), `STATE_LIFECYCLE.md` §6 `:556-560` (회수 후보의 active order/operation·예약 슬롯·review·retained unbound fence·반환 의무·replay window·분쟁/법정 보존 참조 확인; 보관 성공은 해시가 아니라 원문 접근·출처·완전성·복구의 근거), `:552-553` (별도 거절/압축 경계 필요). 열린 입력: I09 `STAGE2…:135`·`RETENTION_PERIODS_PROPOSAL_20261009.md` §7 `:144`, I10 `STAGE2…:136`·`RETENTION…:145`, I13 `STAGE2…:139`·`RETENTION…:146` | I09: `DECISION_REQUIRED · Astra`. I10: `UNDETERMINED · 법무/개인정보`(사용자의 당사자·관할·자료 뒤 검토). I13: `UNDETERMINED · 사용자/운영 책임자` | 읽기 전용 자격 보고는 진행할 수 있다. 상태 변경 회수는 I09의 재시도 지원·메모리 상주·보관량 결정, I10의 법정·분쟁 보류 검토, I13의 저장 예산·주인·복구 검증이 닫힐 때까지 정지다. 네 기간 칸과 호출자 공급 자리만 쓰는 R1 채택 문장(`RETENTION…` §6 `:130`, 병합 위치 `DEVELOPMENT_PLAN.md:142`)이 그 경계다 |
| review 해제 | `STAGE2…:112` (「정지. 그 결론의 내용이 정해지기 전까지 만들지 않는다」), `STATE_LIFECYCLE.md` §5.8 `:543` (충돌 원인·영향 operation·모든 관련 사실의 해결과 권한이 한 결론으로 특정될 것; 미해결 충돌/분쟁이면 해제 금지), `STAGE2…` §9 B `:182` (권한 있는 결론에 들어갈 항목 목록이 없다), I11 잔여 `STAGE2…:137`·`FIRST_BATCH_OPEN_INPUTS.md:35` (자동 서비스·자동 한도·배치 사후점검 미정, `DECISION_REQUIRED · Astra`) | `DECISION_REQUIRED · Astra` (결론 내용·I11 자동 부분). I11의 인간 지명·전체 범위는 이미 확정이며 다시 묻지 않는다 | 권한 있는 결론의 필드(충돌 원인·영향 operation·모든 관련 사실의 해결과 그 권한)가 정의되고, I11의 자동 서비스 identity·자동 한도·배치 사후점검이 결정될 때. 자동 승인 활성 범위 0은 그대로다 |

## 3. 묶음 3 — `rs-1`의 RS-0 수락 문장

`rs-1`의 정지는 RS-0 계약 텍스트의 수락 기록을 요구한다. 수락 문장의 선택지는
[RS0_REVIEW_PACK](RS0_REVIEW_PACK.md) §4 `:238-252`가 세 경로의 템플릿으로
이미 적어 두었다(`<SHA>`는 검토된 텍스트를 싣는 커밋. 사용자가 문장을 고칠 수 있다).
그 파일은 main에 병합돼 있으므로 경로로 인용한다.

| 경로 | 사용자가 쓸 문장의 골자 (원문은 `RS0_REVIEW_PACK.md:250-252`) | 이 시트가 인용하는 근거 |
|---|---|---|
| 경로 1 — 검토된 텍스트를 `<SHA>`에서 확정 계약으로 수락하고 `rs-1`을 다시 연다 | Astra 아키텍처 검토에 이어 `RIGHTS_SCALE_PROFILE.md` 0.1과 `RIGHTS_SCALE_RS0_DECISION_20261008.md`를 커밋 `<SHA>`에서 확정 계약으로 수락한다는 문장 | 확정 조건은 두 문서가 스스로 적는다: `RIGHTS_SCALE_RS0_DECISION_20261008.md:3`, `RIGHTS_SCALE_PROFILE.md:3,:7`. 수락 뒤에도 §2의 열린 값·잠금은 담당과 함께 남는다 (`RS0_REVIEW_PACK.md:250`) |
| 경로 2 — `<SHA>`의 초안대로 구현을 허가하고 Astra 검토를 `rs-1` ARCHITECTURE 게이트로 옮긴다 | 명명된 초안의 공개 경로 구현 허가 문장. 시작 게이트이지 텍스트 수락이 아니다 | `RS0_REVIEW_PACK.md:251`. 초안 상태 문장(`RIGHTS_SCALE_PROFILE.md:3,:7`)은 그대로다 |
| 경로 3 — 초안을 후속 문서로 대체한 뒤 그 문서의 수락을 기다린다 | 후속 문서를 명명하고 `rs-1`이 그 수락을 기다린다는 문장 | `RS0_REVIEW_PACK.md:252` |

기록된 사실: 그 팩의 §0 `:29-34`는, 주인이 2026-10-09에 경로 1을 골랐으나 커밋을
명명하지 않았고 초안을 수락한다고도 적지 않아 확인 단계가 열린 채라고 적는다.
스스로 미확정이라고 적은 문서를 병합하는 일은 그 문서를 확정하지 않는다
(`RS0_REVIEW_PACK.md:245-246`). 그 정지 기록은 저장소 밖 파일이며 이 시트는
팩을 통해서만 인용한다. 레지스터는 RS-0를 「결정 초안 문서 병합만, 확정 조건
미충족」(`CURRENT_CAPABILITY_REGISTER.md:146`), RS-1을 not covered로 적는다
(`:147`). 이 시트는 세 경로 중 어느 것도 고르지 않는다.

## 4. 색인 — 열린 항목과 그것이 막는 노드

| 항목 | 분류 (문서가 적은 대로) | 담당 | 막는 노드 | 정지를 유지하는 답변의 종류 |
|---|---|---|---|---|
| `limit` 상한·기본값 | `UNDETERMINED` | Astra | `read-model-reference`, commerce `bind-list-read` | 추정 수치, 한쪽만의 답, 미병합 권고 |
| 커서 수명 | `UNDETERMINED` | Astra | 같음 | 추정 기간, 「만료 없음」의 임의 가정 |
| 목록 정렬 키 | `UNDETERMINED` | Astra | 같음 | 임의 키 선택, 정렬 없음 선언 |
| "열린 리스팅" 단계 | `UNDETERMINED`(술어 `NOT_BOUND`) | Astra | 같음 | `OPEN_PHASES` 재사용을 결정으로 읽기, 추천 문장의 채택 취급 |
| 요약 키 부분집합 | `UNDETERMINED` | Astra | 같음 | 추천 키 목록의 결정 취급, 점 조회 키 전체 노출 |
| 목록 보존·이력 깊이 | `UNDETERMINED` | Astra | `read-model-reference`, 후속 `ps-02-query-contract` | 제공자 공개값의 보존 기간으로의 전용, 임의 깊이 |
| 가시성 행렬 칸 | `UNDETERMINED` | Astra | `read-model-reference`, `bind-list-read` | 추천 열의 결정 취급, fixture 비교를 접근 통제로 읽기 |
| 역할 라벨의 사람·계정 결부 | `UNDETERMINED` | 사용자(`tl-legal-brief`) | `tl-legal-brief`, 가시성 칸 의존 부분 | 법적 결론의 추정, 라벨을 사람 식별자로 읽기 |
| 목록 오류 코드 이름 | 미지정 — 신규 이름은 `read-model-reference` 소관 (`READ_MODEL_QUERIES.md:25`) | `read-model-reference` / Astra | `read-model-reference` | 임의 이름 창작, 기존 코드 의미의 확장 |
| 토스 결제 상태 사실 | `UNDETERMINED` | 제공자(토스)·사용자 경유 | 종결 평가 의존 부분, `read-model-reference` | 질문서를 보낸 것으로 치기, 미확인을 「없음」으로 읽기 |
| I09 재시도 지원·메모리 상주·보관량·SLO | `DECISION_REQUIRED` | Astra | `k-stage2-v5-impl` 회수 상태 변경 | 미병합 기간 제안, 추정 기간, SLO 추정 |
| I10 법정·분쟁 보존·삭제 보류 | `UNDETERMINED` | 법무/개인정보(사용자 자료 뒤) | `k-stage2-v5-impl` 회수 상태 변경 | 법정 기간 추정, 사용자 자료 없는 검토 |
| I13 원문 보관·복구·저장 예산 | `UNDETERMINED` | 운영/보안(지명은 사용자) | `k-stage2-v5-impl` 슬롯 해제·회수, `k-stage5-durable-tx` | 해시만의 보관 확인, 저장 backend 착수로의 오인 |
| I12 절단 증명 수락 | 미완결 | 프로토콜 담당·비작성자 독립 검토·사용자 신뢰정책 | `k-stage2-v5-impl` 슬롯 해제 | #136 병합을 선택지 수락으로 읽기, 저자 측 문서를 독립 검토로 세기, PG 운영종결 대체 |
| I11 자동 서비스·한도·배치 사후점검 | `DECISION_REQUIRED` | Astra | `k-stage2-v5-impl` review 해제 | 임의 한도, 활성 범위 0을 승인된 한도로 읽기 |
| 잔여위험 정책 (U-R2) | `DECISION_REQUIRED` | Astra | 자원 해제 의존 부분 | 부담 주체·재원 없는 해제 허용 |
| 권한 있는 review 결론의 필드 | 계약 미정(§9 B) | Astra | `k-stage2-v5-impl` review 해제 | 항목 목록의 임의 창작 |
| RS-0 수락 문장 | 확인 단계 — 경로 1 선택 기록, 커밋 미지명 | 사용자 | `rs-1` → `rs-1-issuercap-probe`, `rs-2`, `rs-3a`, `rs-4` | 경로 문장 없는 병합, 커밋 없는 수락, 이 시트의 인용 |

## 5. 비주장

- 이 문서는 빌더가 작성했다. Astra의 결정도, 사용자의 결정도, 어느 담당의
  회신도 아니다. 어느 노드의 상태도 바꾸지 않는다.
- 수치 정책 값, 오류 코드 이름, 단계 목록, 가시성 칸 값을 하나도 제안하지
  않는다. 인용한 추천·선택지·템플릿은 그 출처가 적은 비결정·미선택 상태를
  그대로 둔다.
- 비밀, 실제 제공자 자료, 외부 당사자에게 연락하라는 지시를 담지 않는다.
  「담당은 제공자이며 사용자를 거친다」는 계약이 적은 주인의 기술이다.
- 두 잠금 blob과 `reference/v0.3-rc1/**`는 바꾸지 않는다. 계약·결정 기록·
  프로그램 파일·`docs/tasks/`·`.aiops/`·CI도 바꾸지 않는다.
- 로컬 점검 결과는 `validation/2026-10-13-astra-decision-sheets-listvalues-v5-rs0/README.md`에
  있다. exact-head CI가 아니며 이전 SHA의 녹색을 이 문서로 옮기지 않는다.
- 이 문서는 운영 준비, 안전, 프로토콜 검증 완료를 말하지 않는다.
