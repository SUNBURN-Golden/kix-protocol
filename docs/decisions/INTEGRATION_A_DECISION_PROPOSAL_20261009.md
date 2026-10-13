# 통합 (a) 결정 제안 (2026-10-09)

노드 `k-a-integration-decision`. 이슈는 없다. PR #11 저널의 통합 (a)를 지금 할지, 한다면 어디에 얹을지에 대한 결정 제안이다. 계획 인일의 정본은 [재산정](INTEGRATION_A_REESTIMATE_20261009.md) §4 한 곳이다. 이 파일은 그 표를 다시 그리지 않고, 합계를 다시 계산하지 않는다.

## 0. 상태와 효력

상태: **제안.** 작성만으로 확정이 아니다. 이 파일은 독립 검토가 아니다. 작성자가 빌더이므로, 비작성자 exact-HEAD 검토가 아니다. [재산정](INTEGRATION_A_REESTIMATE_20261009.md)도 빌더가 쓴 계획용 추정이다. 이 제안은 그 파일을 추정으로만 인용한다.

효력은 사용자가 이 문서를 병합할 때에만 생긴다. [로드맵](PROGRAM_ROADMAP_20260930.md) §1(22–28행, 그중 26행)은 판정 표가 현재 병합 경계이고, `user_merge`는 대표님 몫이라고 적는다. [판정 표](../aiops/PROGRAM_ASTRA_DELEGATION.md) 54행의 이 노드 행은 계약 변경 NO, 대표님 병합, A3다. 그 병합 전에는 이 권고가 AGENTS.md, 개발계획, `.aiops/`, 구현을 바꾸지 않는다.

[완료 설계](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md) §5.1(179행)은 사용자 결정 문서가 병합돼 `DONE`인 것과, 권고한 기능이 실제로 채택된 것을 별개로 둔다. 문서 병합과 권고의 이름만으로 `ADOPT`를 추론하지 않는다. 이 권고의 결과 이름은 `DEFERRED`다. `ADOPT` 문장은 §6에 없다.

빌더는 병합하지 않는다. 권고를 실행하지 않는다. 통합 (a)의 구현 노드, `k-stage2-v5-impl`, `k-stage5-durable-tx`를 시작하지 않는다. 이 세션은 커밋, 푸시, PR, 이슈, 댓글을 만들지 않는다.

사용자는 병합 전에 §6의 문장을 바꿀 수 있다.

## 1. 기준

- 작업 시작 시 `git fetch origin main` 뒤의 `origin/main`과 HEAD: `57a3e3049c84a2ac0112371594e9bb4b85a8296f`. 같은 커밋이다. 브랜치는 `agent/kix-k-a-integration-decision`이다. 이 커밋은 PR #141 병합이고, 그 병합이 [재산정](INTEGRATION_A_REESTIMATE_20261009.md)을 이 트리에 들였다. 이 세션은 커밋하지 않으므로 구현 커밋 SHA는 없다. 나중의 커밋 SHA에 이 기준의 CI를 옮기지 않는다.
- 잠금 blob은 작업 전 요구값과 일치했다. `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. 문서 추가 뒤에 다시 계산한다. 두 파일은 수정하지 않는다.
- `docs/tasks/`에는 이 노드의 과제 파일이 없다. 이슈도 없다. 과제 파일과 이슈를 만들지 않았고 고치지 않았다. 입력은 노드 명세와 그것이 가리키는 문서다.
- `.aiops/program.json`의 이 노드 필드는 `user_merge: true`, `audit_floor: A3`, `astra_auto_merge: false`, `depends_on: k-a-reestimate`다. `astra_gate` 키는 없다. 노드 명세 머리의 `astra_gate: None`은 그 빈 칸과 같다. 초기 로드맵 표(101행)의 이 노드 칸은 A3, ARCHITECTURE, 병합은 사용자다. 판정 표 54행은 계약 변경 NO, 대표님 병합, A3다. 병합 주체는 같다. Astra 게이트 칸의 차이는 이 문서가 정하지 않는다. 판정 표 문서는 머리말에서 비실행 초안이라고 적는다.
- 노드 명세가 가리키는 [프로그램 결정](PROGRAM_DECISIONS_20260928.md) 「~115행」은 현재 본문 115행이다. 그 행은 「(a) PR #11 통합」이고, 해제 조건은 「수명 계약 잔여 통합량 재산정과 사용자 승인」이다. 명세가 가리키는 AGENTS.md §5의 통합 (a) 항목은 현재 112행이다. 문장은 「integration (a) of PR #11 wire/local-journal experiments onto v4」다. 두 포인터는 현재 본문과 맞다.
- 같은 트리의 `runtime/crates`에는 `kix-bcs1`, `kix-feature-ir`, `kix-feature-semantics`, `kix-kernel`, `kix-types`가 있다. `kix-kernel-v5`, `kix-ktx-wire`, `kix-journal-local`은 없다. `.aiops/program.json`에서 통합 (a)를 다루는 노드는 `k-a-reestimate`와 `k-a-integration-decision`뿐이다. (a)를 구현하는 노드는 없다.
- 고치지 않은 파일: 두 잠금 blob, `reference/v0.3-rc1/**`, `.aiops/`, `.github/`, `docs/tasks/`, `docs/contracts/**`, `docs/adr/**`, AGENTS.md, 개발계획, 루트 README, `runtime/**`, `scripts/**`, CI, [재산정](INTEGRATION_A_REESTIMATE_20261009.md).

## 2. 출처와 우선순위

이 제안이 읽는 순서다.

1. [프로그램 결정](PROGRAM_DECISIONS_20260928.md) §5 115행. (a)의 해제 조건은 잔여 통합량 재산정과 사용자 승인의 둘이다. 재산정 문서는 이 트리에 있다. 사용자 승인은 이 문서의 병합으로만 생기고, 그 승인의 내용은 §6 한 문장이다. 같은 표 114행은 R2·자체 복제·합의·저장 엔진을 잠근다. 실자금, 실 PG·은행·KYC, 공개 운영 엔드포인트, Sui testnet·mainnet, 새 coin/TIX 모듈은 같은 표의 잠금이다.
2. AGENTS.md §5 111–112행. 111행은 로그 엔진 구현을 기본 금지한다. 112행은 PR #11 wire/로컬 저널 실험을 v4 위에 통합하는 일을 기본 금지한다. 이 제안이 두 줄을 고치지 않는다. 반영은 나중 노드 `agents-scope-sync`의 몫이다.
3. [모델 1](AUTHORITY_MODEL_1.md) 35–44행. 35–40행은 제한된 로컬 통합의 옛 16~26과 그 제외 범위다. 42–44행은 수명 계약을 먼저 닫고 잔여 통합량을 재산정하며, 10~16과 16~26을 합산하지 말라고 적는다. 그 재산정이 [재산정](INTEGRATION_A_REESTIMATE_20261009.md)이다. 추정 승인은 착수 승인이 아니다(40행).
4. [PR #11 보존](../status/PR11_PRESERVATION.md). 코드는 태그로 남아 있고, (a)는 승인 전 미착수다. 잠금 v4 커널 바이트 위의 cold-build는 wire 4 통과·5 실패, 저널 library/recovery 1+13 통과, helper ignore 2다. 이 세션이 그 cold-build를 다시 실행하지 않았다.
5. [재산정](INTEGRATION_A_REESTIMATE_20261009.md) §2–§5. 작업 묶음, 겹침, 세 대상의 계획 괄호, 열린 입력의 주인이다. §4 표가 인일의 정본이다.
6. [로드맵](PROGRAM_ROADMAP_20260930.md) §1과 §5 219행. §5는 「PR #11 통합(a)」를 실행 노드로 넣지 않고, 계획에 둔 것을 `k-a-reestimate`와 이 사용자 결정으로 적는다. 사용자가 이 문서에서 진행을 골라도, 그 선택만으로 구현 노드가 생기지 않는다. 구현을 여는 일은 따로 검토·병합되는 계획 개정이다.
7. [완료 설계](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md) §5.1. `ADOPT`는 실제 선택된 능력과 승인 입력·필요 증거가 있을 때만 그 범위의 구현으로 간다. `DEFERRED`는 영향 받는 구현을 `WAITING/HOLD`로 목록에 남긴다. `DECLINED`는 구현을 HOLD로 두고, 다음 처리에는 비작성자 검토와 사용자 병합의 계획 개정이 영향 노드를 고정해야 한다. 불명확하면 HOLD다.
8. [v5 설계 결정](STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) §3·§4·§5. #138 병합 `a483ab1777ad0c3e15ff71798822cbf6b3666f83`의 §5는 O1이다. v5 crate는 메모리 안이고, 그 crate 안에 저널을 만들지 않는다. 의미론 4 문맥을 성공으로 받아들이는 일은 조용한 재생이라 §3이 금지한다. 승인된 v5 구축 추정은 없다. 숫자 없음.
9. [백엔드 채택 제안](BACKEND_ADOPTION_PROPOSAL_20261009.md) §6. #140 병합 `bb193efb5d238581096372c8a20bee1271dfe4df`의 그 문장은 5단계의 로컬·비운영 PostgreSQL을 고른다. §5.1이 말하듯, 그 병합은 운영 backend의 `ADOPT`도 5단계의 시작도 아니다. 이 트리에 5단계 구현은 없다.
10. [개발계획](../DEVELOPMENT_PLAN.md) §9 224행과 §10 467–474행. 224행은 PR #11 `LocalJournal::execute()`가 예산을 커널의 기존 명령 조회보다 먼저 본다는 source-derived 제한이고, 그 PR에서 저널을 실행·수정하지 않는다고 적는다. 474행은 기성 DB가 제공하는 로그를 불필요하게 다시 만들지 말라고 적고, 그 일이 전부 미착수라고 적는다. 개발계획 본문의 반영은 `roadmap-sync`의 몫이다.

프로그램 결정 §5의 잠금은 유지한다. 실자금, 실 PG·은행·KYC, 공개 운영 엔드포인트, Sui testnet·mainnet, R2, 자체 복제·합의·저장 엔진, 새 coin/TIX 모듈은 이 제안이 열지 않는다.

## 3. 재산정이 보여 준 것

아래는 [재산정](INTEGRATION_A_REESTIMATE_20261009.md) §4를 보통 말로 옮긴 것이다. 숫자의 정본은 [그 절의 표](INTEGRATION_A_REESTIMATE_20261009.md)다. 이 절은 표를 다시 그리지 않고, 합계를 다시 더하지 않는다.

옛 조건부 18~30을 세 대상으로 다시 읽은 계획 괄호다. T0(잠금 v4 그대로)는 17~28이다. T1(계획된 v5 crate 위의 프레임 저널)은 17~28이다. T2(v5 위에서 내구 층을 5단계 로컬 PostgreSQL에 두고, 별도 저널은 만들지 않음)는 14~24다. T0와 T1의 괄호가 같은 것은 v5가 v4와 같은 일이라는 뜻이 아니다.

세 합계 밖에 크게 비어 있는 칸이 같다. v5 crate를 짓는 인일, T0 산출물을 v5로 옮기는 이관, WP3·WP4 안에서 막혀 있는 부분의 폭이다. 재산정은 그 칸을 **숫자 없음**으로 두었다. 이 제안이 그 칸에 수를 넣지 않는다.

T2에서 저널 묶음이 0인 것은 저널 구현이 끝났다는 뜻이 아니다. Rust append 로그를 다시 만들지 않는다는 계획상의 읽기다. 5단계가 그 어댑터를 업무 범위로 다시 쓰는 인일도 합계 밖이고 숫자 없음이다.

인일은 계획용 범위다. 청구, 납기, 착수 승인이 아니다. 실제 소진 인일은 숫자 없음이다.

## 4. 아직 증명되지 않은 것

[PR #11 보존](../status/PR11_PRESERVATION.md)의 cold-build를 이 세션이 다시 실행하지 않았다. 그 실행은 잠금 v4 커널 바이트를 올린 일회성 호스트 진단이다. 로컬에서 싸게 다시 돌릴 조합이 아니라, 그 기록을 인용한다.

- wire golden은 잠금 v4 위에서 9건 중 5건이 실패했다. 통과 4, 실패 5, exit 101이다. 실패의 오류는 `BodyEncode`와 `UnsupportedSemantics`다. 고정 golden의 genesis/command에는 의미론 1이 들어 있다. 현재 커널의 의미론은 4다. SHA-256 함수가 틀렸다는 판정이 아니다. v1 시대의 wire 통과는 v4로 넘어오지 않는다.
- 저널 library/recovery는 같은 기록에서 1+13 통과, helper ignore 2다. 그 통과는 fixture가 `SEMANTICS_VERSION`으로 새 입력을 만들기 때문이다. 과거 v1 파일을 v4로 이관한 것이 아니다. v4 슬롯 예약과 만석 상태변경형 `Err(Capacity)`의 모든 복구 경로를 검증한 것도 아니다.
- 개발계획 224행의 예산 선검사 제한은 그대로다. 이 제안이 저널 소스를 고치지 않는다.
- v5 crate와 5단계 구현은 이 트리에 없다. T1·T2는 그 둘을 계획 대상으로 읽을 뿐, 이미 있다는 뜻이 아니다.
- 재산정 §5의 열린 입력은 값이 없다. 주인과 이 제안이 채우지 않는다는 점은 §7이다. 새 wire·프로토콜 명령, H_g 최종성(A4), 시간원(A5), 비협조 실행자(A10), I09, I11은 `DECISION_REQUIRED · Astra`다. 토스 사실(I02–I05, I08, TM04, TM05)은 `UNDETERMINED · 토스 계약/기술`이다. I10은 `UNDETERMINED · 법무/개인정보`다. I13과 비용 단가는 `UNDETERMINED · 사용자/운영 책임자`다. 프레임 저널이 로그 엔진 잠금 안인지는 사용자 몫이고, 이 제안이 정하지 않는다. I12의 비작성자 독립 검토(A9)와 신뢰정책도 사용자 몫이다. #136 병합에서 I12 선택지를 추론하지 않는다.

## 5. 선택지, 결과, 권고

다섯 갈래다. 권고는 B다. 빌더는 어느 갈래도 실행하지 않는다.

[완료 설계](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md) §5.1의 결과 이름을 보통 말로 옮기면 이렇다. `ADOPT`는 고른 능력과 승인된 입력·증거가 있을 때만 그 범위의 구현으로 간다. `DEFERRED`는 그 구현을 목록에 `WAITING/HOLD`로 남기고, 다른 안으로 바꾸거나 완료로 치지 않는다. `DECLINED`는 구현을 HOLD로 둔 채, 나중에 사용자가 병합하는 계획 개정이 영향 노드를 고정해야 다음으로 간다.

(a)를 구현하는 노드는 없다. A1·A2·A3의 결과 이름이 `ADOPT`여도, 그 구현이 시작되려면 사용자가 병합하는 별도 계획 개정이 필요하다. 이 문서의 병합만으로는 노드가 생기지 않는다. 대상을 v5로 두는 A2·A3는 AGENTS.md §5 112행의 「onto v4」와 문장이 다르다. 그 문장을 고치는 일은 `agents-scope-sync`다. 이 제안이 AGENTS.md를 고치지 않는다.

| 선택 | 내용 | §5.1 결과 |
|---|---|---|
| A1 | 잠금 v4 위에 통합한다 (T0). | `ADOPT` |
| A2 | v5 위에, 길이 접두 프레임과 fsync의 저널을 둔다 (T1). | `ADOPT` |
| A3 | v5 위에서 내구 층은 5단계 로컬 PostgreSQL로 두고, 별도 저널은 만들지 않는다 (T2). | `ADOPT` |
| B | 지금은 하지 않는다. | `DEFERRED` |
| C | 거절한다. | `DECLINED` |

A2의 저널은 [재산정](INTEGRATION_A_REESTIMATE_20261009.md)이 PR #11 소스에서 본 모양이다. 길이 접두 프레임, 순번, 이전 해시, `canonical_hash_bytes`의 SHA-256, apply 앞의 append와 fsync다. CRC 상수는 그 소스에 없다. 「프레임 저널」은 그 산출물을 말한다.

### A1. 잠금 v4 (T0)

계획 괄호는 재산정 §4의 T0, 17~28이다. 역사적 18~30과 나란히 읽는 계획 범위이고, 착수 승인으로 읽지 않는다. v5로 나중에 옮기는 이관은 합계 밖이고 숫자 없음이다.

닿는 잠금은 프로그램 결정 115행의 (a)다. 사용자 승인이 그 행의 남은 해제 조건이다. 잠금 커널 blob 두 개는 이 갈래가 열지 않는다. 양성 수명 전이를 v4 파일 안에 만드는 일은 별도 사람 결정이고, 재산정이 합계 밖에 둔 일이다.

먼저 필요한 것은 (a) 구현 노드를 넣는 계획 개정이다. 이 문장을 A1로 고쳐 병합해도 그 노드가 생기지 않는다. wire 실패 5건은 의미론 1 golden이라, v4 통합은 그 실패를 그대로 통과로 만들지 못한다.

결과: `ADOPT` 이름이어도 구현은 계획 개정과 증거가 생기기 전에 시작하지 않는다. R2, 복제, 합의, 저장 엔진, 실자금, 실 PG, coin/TIX는 열리지 않는다. 이미 멈춘 입력은 멈춘 채로다. v5 설계가 고른 새 crate와 어긋나고, 의미론 4를 v5가 조용히 재생하는 일은 금지다. 이 길을 권고하지 않는다.

### A2. v5와 프레임 저널 (T1)

계획 괄호는 T1, 17~28이다. v5 crate 구축, T0에서 v5로의 이관, WP3·WP4의 막힌 폭은 숫자 없음이다. 저널 인일은 계획 칸에만 있고, 착수 승인이 아니다. v5 설계 O1은 v5 crate 안에 저널을 만들지 말라고 적는다. 저널은 그 crate 밖의 별도 산출물로 남는다.

닿는 잠금은 (a)다. 이 저널은 AGENTS.md 111행의 로그 엔진 잠금에 가깝다. 경계가 잠금 안인지 밖인지는 정해져 있지 않다. 이 갈래를 골라도 그 경계를 확정하는 문장이 아니다. 경계의 주인은 사용자다. 대상을 v5로 두면 112행의 「onto v4」를 먼저 고쳐야 한다.

먼저 필요한 것은 트리에 없는 v5 crate, (a) 구현 노드를 넣는 계획 개정, 그리고 그 AGENTS.md 문장 반영이다. v5 전이의 wire·OpenAPI·카탈로그는 새 프로토콜 명령이라 `DECISION_REQUIRED · Astra`다. 그 명령을 이 제안이 만들지 않고, 그 인일을 17~28 안에 넣지도 않는다.

결과: `ADOPT` 이름이어도 위 선행이 없으면 구현은 시작하지 않는다. 다른 잠금은 열리지 않는다. PostgreSQL 옆에 이 저널을 두면, 개발계획 474행이 기성 DB의 로그를 다시 만들지 말라고 한 일과 겹친다. 이 길을 권고하지 않는다.

### A3. v5와 로컬 PostgreSQL, 별도 저널 없음 (T2)

계획 괄호는 T2, 14~24다. 저널 묶음을 0으로 읽은 것은 다시 만들지 않는다는 뜻이다. 5단계 바인딩 공수는 합계 밖이고 숫자 없음이다. wire 묶음은 표에 남는다. 로컬 PostgreSQL이 넣은 것은 명령 identity, payload sha256, 최초 결과이지, PR #11 wire 바이트를 대체 완료한 것이 아니다.

닿는 잠금은 (a)다. 별도 프레임 저널을 만들지 않으므로, 로그 엔진 경계를 이 갈래가 새로 긋지 않는다. 기성 PostgreSQL을 쓰는 일은 프로그램 결정 114행의 자체 저장 엔진을 여는 일이 아니다. 백엔드 채택 §6의 범위는 로컬·비운영·단일 프로세스·단일 작성자·운영 플래그 false다. 대상이 v5이므로 AGENTS.md 112행의 「onto v4」는 바뀌어야 한다.

먼저 필요한 것은 트리에 없는 v5 crate, 트리에 없는 5단계 구현, (a) 구현 노드를 넣는 계획 개정, AGENTS.md 문장 반영이다. 백엔드 채택 문서의 병합은 그 5단계를 시작하지 않았다.

결과: 지금 진행을 고를 때의 모양은 이 갈래다. 결과 이름은 `ADOPT`이고, 이름만으로 구현이 시작되지 않는다. R2와 나머지 잠금은 열리지 않는다. 이미 멈춘 항목은 멈춘 채로다. 새 wire 명령은 만들지 않는다.

### B. 지금은 하지 않는다. 권고

계획 괄호 17~28과 14~24는 그대로 계획 범위다. 지금 그 인일을 쓰지 않는다. 착수 승인이 아니다.

닿는 잠금은 열리지 않는다. (a)는 115행 그대로다. 로그 엔진 경계는 정하지 않는다. 재개할 때의 한계 둘은 그 경계를 확정하는 문장이 아니다. 한계는 이렇다. 대상은 v4가 아니다. PostgreSQL 옆에 별도 프레임 저널을 두지 않는다.

먼저 필요한 구현은 없다. 사용자가 나중에 진행을 원하면 §6을 그 시점에 고치고, A3의 선행(v5 crate, 5단계, 계획 개정, AGENTS.md 문장)이 갖춰진 뒤에 별도 노드로 연다.

결과: `DEFERRED`다. (a)에 기대는 구현은 `WAITING/HOLD`로 목록에 남는다. 행을 지우거나 완료로 바꾸지 않는다. [pending catalogue](PROGRAM_ROADMAP_20260930_PENDING.json)에서 `protocol-integration-evidence-closeout`의 선행 130행에 이 노드가 있다. 이 문서를 병합해도 그 목록을 고치지 않는다. 마감 노드는 결정 문서의 `DONE`을 통합 (a)의 `ADOPT`로 읽지 않아야 한다. `.aiops/`와 catalogue는 이 제안이 고치지 않는다.

이 길을 권고하는 이유는 다섯이다. v5 crate와 5단계 구현이 이 트리에 없다. 세 합계가 같은 숫자 없음(v5 구축, 이관, WP3·WP4의 막힌 폭)을 나눠 가진다. (a) 구현 노드가 없다. 개발계획 474행이 기성 DB의 로그를 다시 만들지 말라고 한다. 프레임 저널은 로그 엔진 잠금에 가깝고, 그 경계는 미정이라 이 제안이 선을 긋지 않는다.

### C. 거절

결과: `DECLINED`다. 정상 구현은 HOLD로 남는다. 행을 빼거나 비구현 산출물로 닫으려면, 비작성자 검토와 사용자 병합의 계획 개정이 영향 노드의 정의와 분모를 고정해야 한다. 이 제안이 그 개정을 쓰지 않는다.

잠금이 이 갈래에서 풀리지는 않는다. 거절은 완료가 아니다. 재산정은 잔여 계획 범위를 남겼고, PR #11 소스는 태그에 남아 있다. 지금 거절을 권고하지 않는다. 사용자가 거절을 원하면 병합 전에 §6의 문장을 고친다.

## 6. 병합이 채택하는 범위

사용자가 이 문서를 문장 수정 없이 병합하면, 선택지 B만 채택되고, 통합 (a)는 DEFERRED이며, 착수·R2·저널·저장 엔진은 열리지 않고, 재개한다면 대상은 v4가 아니며 별도 프레임 저널을 두지 않고, 이미 멈춘 항목은 멈춘 채로다.

그 한 문장이 이후 노드가 읽을 범위다. 사용자는 병합 전에 위 문장을 바꿀 수 있다. A1, A2, A3, C를 채택하려면 그 문장을 먼저 고친다.

이 문장의 결과는 `DEFERRED`다. [완료 설계](../aiops/CONTRACT_RELEASE_AND_COMPLETION_DESIGN_KO.md) §5.1대로, 문서가 병합됐다는 사실만으로 `ADOPT`가 아니다. B를 고른 병합은 통합 (a)의 구현 착수가 아니다.

A1·A2·A3로 문장을 고쳐도, (a) 구현 노드가 생기기 전에는 착수하지 않는다. 그 노드를 넣는 일은 별도 계획 개정이고, 사용자가 병합한다. v5를 대상으로 하면 AGENTS.md §5 112행의 「onto v4」도 바뀌어야 하며, 그 반영은 `agents-scope-sync`다. 빌더는 문장을 실행하지 않는다.

재개의 두 한계는 로그 엔진 잠금의 안과 밖을 판결하지 않는다. 그 경계는 §9의 B로 남는다.

## 7. 열린 입력과 주인

값을 채우지 않는다. 상태 문장의 정본은 [열린 입력](../contracts/FIRST_BATCH_OPEN_INPUTS.md) §1·§4이고, 이 표는 [재산정](INTEGRATION_A_REESTIMATE_20261009.md) §5가 멈춘 항목을 옮긴 것이다.

| 항목 | 상태 | 주인 | 이 제안이 하는 일 |
|---|---|---|---|
| 새 wire·프로토콜 명령, v5 전이의 OpenAPI·카탈로그 | DECISION_REQUIRED · Astra | Astra | 명령을 만들지 않음. 인일을 만들지 않음 |
| H_g 최종성 (A4), 시간원 수치 (A5), 비협조 실행자와 온체인 앵커 (A10) | DECISION_REQUIRED · Astra | Astra | 값을 만들지 않음 |
| I09 보관·지원 기간, SLO·TPS·p99 | DECISION_REQUIRED · Astra | Astra | 수를 만들지 않음 |
| I11 자동 한도와 잔여위험 정책 | DECISION_REQUIRED · Astra | Astra | review 해제를 열지 않음. 한도를 채우지 않음 |
| 프레임 fsync 저널이 로그 엔진 잠금 안인지 | 계약 미정. 사용자 결정 | 사용자 | 판결하지 않음. 권고 B의 재개 한계는 별도 저널을 두지 않는 모양일 뿐, 경계의 확정이 아님 |
| (a)를 지금 허용할지 | 이 문서의 §6. 문장 수정 없이 병합하면 B, `DEFERRED` | 사용자 | 빌더는 실행하지 않음. A1·A2·A3·C는 §6을 고친 뒤에만 |
| 절단 증명의 비작성자 독립 검토 (A9)와 신뢰정책 승인 | 사용자 | 사용자 | I12는 미완결. #136에서 선택지를 추론하지 않음 |
| 인건비, 감가상각, 전력, 연간 운영, 투자 한도 | UNDETERMINED — 사용자/운영 책임자 | 사용자/운영 책임자 | 단가를 만들지 않음 |
| I02, I03, I04, I05, I08, TM04, TM05 | UNDETERMINED · 토스 계약/기술 | 토스 계약/기술 | 제공자 사실을 만들지 않음 |
| I10 | UNDETERMINED · 법무/개인정보 | 법무/개인정보 | 법정 기간을 산정하지 않음 |
| I13 | UNDETERMINED · 사용자/운영 책임자 | 사용자/운영 책임자 | 슬롯 해제를 열지 않음. 저장 backend 착수 승인이 아님 |

## 8. 기존 커버리지 (AGENTS §7)

이 노드는 시험을 추가하지 않는다. PR #11 cold-build를 다시 실행하지 않는다. 아래는 [재산정](INTEGRATION_A_REESTIMATE_20261009.md) §3이 이미 이름을 적은 시험이다. 통합 (a)의 구현을 대신하는 행은 없다.

| 요구 | 근거 | 분류 |
|---|---|---|
| (a)의 결정 제안. 선택지, 결과, 권고, 사용자 병합 때에만 효력 | 이 문서 §0·§5·§6 | 이 문서가 그 제안이다. 시험이 아니고, 병합 전에는 효력이 없다 |
| wire/registry/golden을 v4 또는 v5에 통합 | [PR #11 보존](../status/PR11_PRESERVATION.md)의 cold-build. [kix-bcs1 golden](../../runtime/crates/kix-bcs1/tests/golden_vectors.rs) 4건은 현재 main의 canonical body | 부분. 보존 기록은 v4 위 4 통과·5 실패다. bcs1 golden은 PR #11 wire 9건이 아니다. 이 세션의 재실행이 아니다 |
| 로컬 저널의 append, recovery, 찢긴 tail, 예산 | 보존 문서의 저널 1+13. [readiness/test_faults.py](../../readiness/test_faults.py) `StoreTests.test_torn_tail_is_discarded_and_a_bad_checksum_fails_closed`, `test_budget_names_the_existing_limit_and_overload_does_not_queue`. [readiness/conformance.py](../../readiness/conformance.py) `BackendConformance.test_budget_rejection_preserves_records_and_replay_identity` | 부분. 저널 통과는 새 입력 fixture다. 이관이 아니다. readiness는 Python `journal.v1`이라 PR #11 `kix-journal-local`이 아니다 |
| v4 메모리 재생과 다른 의미론의 거절 | `contract_invariants.rs`의 `five_contract_invariants_on_kernel_only_generated_histories`, `e4_state_model.rs`의 `locked_v4_matches_independent_state_model`, `transitions.rs`의 `replaying_ordered_inputs_reconstructs_identical_state`, `response_loss_retry_returns_original_before_availability_check`, `contract_edge_cases.rs`의 `rejection_replay_stays_immutable_after_the_blocking_hold_is_released`, `observation_slots.rs`의 `previous_semantics_version_is_rejected_without_silent_replay_change`, `quarantine_capacity.rs`의 `v3_inputs_are_rejected_before_any_state_change`, `transitions.rs`의 `unknown_semantics_and_regressed_time_are_not_applied` | 부분. 잠금 v4의 기존 시험이다. 저널 복구와 wire crate의 통과가 아니다 |
| 수명 계약, 어댑터 정체성, I12 절단 | [수명 계약](../contracts/STATE_LIFECYCLE.md) 0.6, [어댑터 정체성](../contracts/ADAPTER_EVENT_IDENTITY.md) 0.1, [I12 절단 증명](CUT_PROOF_I12_20261008.md) | 부분. 계약·초안이다. I06·I12는 미완결이다. 구현 일수를 끝낸 증거가 아니다 |
| T2에서 로컬 PostgreSQL이 명령 identity·payload sha256·최초 결과를 한 트랜잭션에 넣었다 | [exploration/stage4/adapters.py](../../exploration/stage4/adapters.py), [stage-4 기록](../../validation/2026-10-08-k-stage4-local-exploration/README.md), [백엔드 채택 제안](BACKEND_ADOPTION_PROPOSAL_20261009.md) §3 | 부분. 탐색 자료다. wire 바이트의 대체 완료가 아니고, 이 세션의 재실행이 아니다 |
| 저널 내구성, 하드웨어 flush, 제품 SLO | [performance_harness.rs](../../runtime/crates/kix-kernel/tests/performance_harness.rs)의 `memory_probe_reports_saturation_without_recreating_kernel`, `low_load_uniform_is_distinct_from_hot_seat_retry_and_saturation`, `outcome_summaries_do_not_label_mixed_p99_as_success`, `evidence_binding_records_budgets_toolchain_and_non_claims` | 미커버. 메모리 장치다. 저널 내구성이 아니고 제품 SLO가 아니다 |

## 9. 분류 (AGENTS §8)

### A. 계약과 일치

- (a)는 승인 전 미착수다. 프로그램 결정 115행, [PR #11 보존](../status/PR11_PRESERVATION.md), AGENTS.md 112행.
- 해제 조건은 잔여량 재산정과 사용자 승인의 둘이다. 재산정은 이 트리에 있다. 사용자 승인의 문장은 §6이고, 수정 없이 병합하면 그 승인은 `DEFERRED`다. 착수는 열리지 않는다.
- 프로그램 결정 §5의 다른 잠금과 해제 조건은 그대로다.
- `.aiops/program.json`에 (a) 구현 노드가 없다. 로드맵 §5 219행이 (a)를 실행 노드로 넣지 않은 것과 같다.
- 사용자 결정의 `DONE`은 그 자체로 `ADOPT`가 아니다. 완료 설계 §5.1.

### B. 계약이 정의하지 않음. 성격만 기록

- 프레임 fsync 저널이 로그 엔진 잠금 안인지. 재산정 §7이 미정으로 두었고, 결정 위치를 이 노드로 적었다. 이 제안은 그 경계를 판결하지 않는다. 주인은 사용자다. §6의 재개 한계는 별도 저널을 두지 않는 모양이다.
- 6~10을 wire와 저널로 나눈 값은 재산정 §6의 계획 배분이다. 이 제안이 다시 나누지 않는다.
- v5 crate 구축, T0→v5 이관, WP3·WP4의 막힌 폭, 5단계 바인딩, 실제 소진 인일. 숫자 없음. 이 제안이 수를 만들지 않는다.

이 항목에 의미를 지어 AGENTS.md, 개발계획, 계약, ADR을 고치지 않았다.

### C. 명시적 계약 위반

없음. 잠금 파일을 고칠 위반이 아니다. (a)가 아직 없는 것은 계약과 승인 기록이 이미 적은 상태다.

## 10. 비주장

이 문서는 다음을 주장하지 않는다.

- 운영 준비, 내구성, 분산 fencing, 은행 exactly-once, 체인 finality, 법적 적합성.
- 승인된 SLO, TPS, p99, 실패율, 비용, 단가. 보존 기간과 I09·I10의 숫자. I12 선택지. #136 병합에서 그 선택지를 추론하지 않는다.
- R2의 추정. 승인된 v5 구축 추정. 첫 묶음의 완료. 「새로 실입력까지 완결된 행: 0」은 그대로다.
- 17~28과 14~24가 청구, 납기, 착수 승인이라는 것. 그 수는 재산정의 계획 괄호다.
- 저널 시험의 v4 통과가 이관 완료거나 만석 복구의 완료라는 것.
- 프레임 저널이 로그 엔진 잠금 안이라는 판결, 또는 그 밖이라는 판결.
- 잠금이 풀렸다. 실자금, 실 PG·은행·KYC, 공개 엔드포인트, Sui testnet·mainnet, R2, 복제, 합의, 저장 엔진, 새 coin/TIX가 열렸다.
- 통합 (a), v5 crate, 5단계, wire crate, 저널 crate가 이 문서로 만들어졌다.
- 독립 검토가 있었다. 이 세션의 로컬 명령이 exact-head CI다. 문서만 바뀐 변경의 CI 초록은 전체 검증이 아니다. 이전 SHA의 녹색을 이 문서의 통과로 옮기지 않는다.

## 11. 병합 이후

아래는 이 세션에서 하지 않는다.

- §6을 실행하는 일. 병합 주체는 사용자다.
- (a) 구현 노드를 만들거나 시작하는 일. A1·A2·A3로 문장이 바뀌어도, 그 착수는 사용자가 병합하는 별도 계획 개정 다음이다.
- `k-stage2-v5-impl`과 `k-stage5-durable-tx`를 이 문서로 시작하는 일.
- AGENTS.md §5 112행을 고치는 일. 결과의 반영은 `agents-scope-sync`다. v5를 대상으로 문장을 고치면 그 노드가 「onto v4」를 읽는다. B는 착수를 열지 않는다. 이 제안이 그 반영의 문장을 대신 쓰지 않는다.
- 개발계획에 이 결과를 반영하는 일. 그 반영은 `roadmap-sync`다.
- `.aiops/program.json`과 pending catalogue를 고치는 일. `protocol-integration-evidence-closeout`은 이 노드를 선행으로 둔 채로 남는다. `DEFERRED`인 (a)는 목록에서 `WAITING/HOLD`다. 마감 보고가 이 문서의 병합을 `ADOPT`로 읽으면 §5.1과 어긋난다.
- 계약, ADR, CI, 잠금 blob, `reference/v0.3-rc1/**`을 고치는 일.
