# AI 위임 권한 — 초안 0.1

이슈 #97. 문서일: 2026-10-08.
구현 기준 `origin/main`: `d71b4117741f596e2b618ed1c32a42597bc0980b`.
이 문서는 오프라인 목이 지킬 술어와, 아직 정하지 않은 간극을 적는다.
`docs/status/ORIGINAL_32_STATUS.md`의 F04·E06 라벨은 **설계중** 그대로다.
이 계약은 그 라벨을 설계확정·구현됨·검증됨으로 올리지 않는다.

현행 승인 범위의 정본은 [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) §14다.
프로그램 결정 [PROGRAM_DECISIONS_20260928.md](../decisions/PROGRAM_DECISIONS_20260928.md) §2.1·§6이 이 초안과 mock을 연다.
로드맵의 `ai-delegation-execution-decision`은 이 노드의 후속이며, 여기서 실행을 켜지 않는다.

목은 `reference/ai_delegation/ai_delegation_mock.py`다.
실행 방법과 비청구는 [validation/2026-10-08-ai-delegation-contract-mock/README.md](../../validation/2026-10-08-ai-delegation-contract-mock/README.md)에 있다.

## 0. 범위와 상태

이 초안은 인간 주체가 AI 에이전트에 주는 조회·제안·실행 권한을 적는다.
범위(scope), 금액, 기간, 회수 조건을 그 권한과 구분한다.
모델 출력만으로 발행하거나 지급하지 않는다(개발계획 §14).
AI가 자기 부여를 넓히지 못한다([FIRST_BATCH_OPEN_INPUTS](FIRST_BATCH_OPEN_INPUTS.md) I11).
위임 실행은 꺼 둔다(개발계획 §12). 실제 grant와 비협조 회수가 없기 때문이다.

| 항목 | 목에서 고정하는 것 | 고정하지 않는 것 |
|---|---|---|
| 조회 | 상태를 바꾸지 않는 읽기 | 조회가 사실의 인증이라는 주장 |
| 제안 | 효과를 실행하지 않는 메모 | 제안이 승인·발행·지급이 된다는 주장 |
| 실행 | 정의만 하고 항상 거절 | 실행을 켜는 스위치, 체인 grant |
| 회수 | 기록 즉시 그 세대의 대기 제안을 멈추고 이력은 남김 | 체인 회수 cut, 법적 효력 |

네트워크, 파일, PG, 은행, KYC, 커널, Move, 서명을 호출하지 않는다.
`reference/v0.3-rc1`을 import하지 않는다.
`protocol_contract.json`과 계약 전용 OpenAPI에 명령을 넣지 않는다.
모든 조회에 `provenance = MOCK_AI_DELEGATION_ONLY`, `lifecycle_authority = IN_MEMORY_FSM`을 붙인다.
이 결과는 내구 원장이 아니다.

## 1. 용어

이 문서에서 부여(grant)는 인간 주체가 AI 에이전트에 적어 둔 권한 기록이다.
명령 이름 `delegate`와 같은 낱말로 부르지 않는다.

| 용어 | 의미 |
|---|---|
| 인간 주체 | 부여를 발급·철회하고 제안을 승인하거나 거절할 수 있는 등록된 사람 쪽 식별자. 목의 등록부는 fixture다 |
| AI 에이전트 | `call_tool`만 호출하는 등록된 식별자. 발급·철회·결정을 하지 못한다 |
| 부여 | 불변 본문과 세대 번호를 가진 기록. 본문을 고치려면 새 세대다 |
| 제안 | AI가 남긴 메모. 승인돼도 `effects_executed`는 거짓이다 |

I11이 적은 발급자·대체 담당자의 이름은 이 목이 등록부를 채우는 값이 아니다.
시험이 넣는 식별자는 fixture다.

## 2. `delegate` / `close_delegation`과의 관계

관찰 기준은 위 SHA의 `reference/v0.3-rc1/core.py`다.
`_delegate`는 티켓 소유자가 열린 행사의 `ACTIVE` 티켓을 `DELEGATED`로 두고 venue 세션을 만든다.
`_close_delegation`은 venue가 그 세션과 컨트롤러 로그로 티켓을 닫는다.
이 축은 권리 보유자와 회장 사이다. AI 주체, scope, 금액, 기간이 없다.

| | `delegate` / `close_delegation` | 이 계약 |
|---|---|---|
| 대상 | 티켓 | 인간 주체가 AI 에이전트에게 적은 부여 |
| 행위자 | 티켓 소유자, 회장(venue) | 인간 주체 issuer, AI 에이전트 |
| 상태 | 티켓 `ACTIVE` → `DELEGATED` → 회장이 닫음 | 부여 `ACTIVE` → `REVOKED`. 제안은 아래 §7 |
| 축 | 권리 보유자–회장 | 인간 주체–AI 에이전트 |
| 카탈로그 | `protocol_contract.json`의 기존 명령 | 명령을 추가하지 않음 |

이 계약은 그 두 명령을 호출하지 않고, 재사용하지 않고, 이름을 바꾸지 않고, 본문을 바꾸지 않는다.
목을 그 모듈에 연결하지 않는다.
그 명령을 바꾸거나 새 와이어 명령을 카탈로그에 올리는 일은 이 노드의 범위 밖이다.
그렇게 해야 한다면 구현을 멈추고 Astra의 `DECISION_REQUIRED`로 올린다. 이 초안은 그렇게 하지 않는다.

## 3. 권한 수준

| 수준 | 목에서의 의미 |
|---|---|
| `QUERY` | `query_grant`, `query_subject`만. 상태를 바꾸지 않는다 |
| `PROPOSE` | 제안 메모를 쓰거나, 아직 `PROPOSED`인 자기 제안을 철회(`withdraw_proposal`)한다. 발행·지급·서명은 없다 |
| `EXECUTE` | 이름만 있다. 부여 본문에 넣을 수 없다. `attempt_execution`은 항상 실패한다 |

부여의 `authority`는 `QUERY`와 `PROPOSE`의 비어 있지 않은 부분집합이다.
`EXECUTE`가 하나라도 있으면 `EXECUTE_AUTHORITY_DISABLED`이고 기록하지 않는다.
생성자에는 실행을 켜는 인자가 없다.

한 수준이 없다고 다른 수준이 생기지 않는다.
`QUERY`만 있는 부여는 제안을 쓰지 못한다.
`PROPOSE`만 있는 부여는 조회 도구를 쓰지 못한다.

## 4. 부여 기록

[STATE_LIFECYCLE](STATE_LIFECYCLE.md) §5.5대로 기존 규칙을 덮어쓰지 않는다.
변경은 새 세대다. 철회된 세대를 같은 `grant_id`로 되살리지 않는다.

| 필드 | 규칙 |
|---|---|
| `grant_id` | 길이 1..100인 `str`. 앞뒤 공백 없음. 한 세대의 식별자 |
| `generation` | 목이 `(issuer, agent_id)`마다 1부터 매긴다. 호출자가 넣지 않는다 |
| `issuer` | `issue_grant`의 `actor`. 등록된 인간 주체 |
| `agent_id` | 등록된 AI 에이전트 |
| `authority` | §3. 저장 순서는 정렬한다 |
| `scope` | `surfaces`는 비어 있지 않은 불투명 식별자 목록. `subjects`는 생략할 수 있다. 목은 소속만 보고 식별자를 해석하지 않는다 |
| `limits` | `per_action_max`, `cumulative_max`, `count_max`, `currency`가 모두 있어야 한다. 기본값과 무제한은 없다 |
| `period` | `not_before`, `not_after`. 호출자가 넣는 논리 정수. 벽시계는 없다. `not_after`는 필수이고 `not_before`도 필수다 |
| `phase` | `ACTIVE` 또는 `REVOKED` |
| `revoked_at_seq` | 철회 순번. 철회 전에는 없다. 벽시계가 아니다 |
| `reason` | 철회 사유 식별자. 철회 전에는 없다 |

금액·건수 상한의 정수 범위는 `1 .. 10**12`다. 통화 키는 `KRW`만 받는다.
이 범위는 F04 목이 쓰던 입력 상한이지, 제품 한도·집계 창·기간 길이가 아니다(§9).

같은 `(issuer, agent_id)`에 `ACTIVE` 부여는 하나다.
다른 issuer의 부여는 다른 쌍이다. 한 에이전트가 여러 issuer의 부여를 동시에 가질 수 있는지는 집계 정책이 정한다(§9).
목은 쌍마다 한도를 따로 두며, 그것을 우회 방지의 제품 규칙으로 읽지 않는다.
이미 `ACTIVE`가 있는데 다른 `grant_id`를 발급하면 기록하지 않고 `GRANT_NOT_CURRENT`다.
먼저 철회한 뒤에만 다음 세대가 된다.
이것은 한도 술어를 한 세대 안에서 시험하려는 목 불변식이다.
동시에 여러 부여를 둘지는 집계 정책이 정하기 전이며, 그 답을 여기 채우지 않는다(§9).

만료는 저장하지 않는다. 호출자가 넣은 `now`와 `period`를 비교해 그때그때 계산한다.

## 5. 도구 허용 목록과 거부 목록

AI의 진입점은 `call_tool` 하나다. 허용 목록은 닫혀 있다.

| 도구 | 필요한 수준 | 효과 |
|---|---|---|
| `query_grant` | `QUERY` | 부여 조회. 상태 불변 |
| `query_subject` | `QUERY` | `surface`와 선택적 `subject`의 소속만 확인. 상태 불변 |
| `propose_action` | `PROPOSE` | 비활성 제안 메모 |
| `withdraw_proposal` | `PROPOSE` | `PROPOSED`인 그 부여의 제안을 `WITHDRAWN`으로 둔다 |
| `propose_grant_change` | `PROPOSE` | 부여 변경을 요청하는 메모. 부여 본문은 그대로다 |

거부 목록은 허용 목록과 서로소다. 이 이름이면 해당 코드로 거절하고 상태를 바꾸지 않는다.

| 도구 | 코드 |
|---|---|
| `transfer` | `TRANSFER_FORBIDDEN` |
| `refund_execution` | `REFUND_EXECUTION_FORBIDDEN` |
| `sign` | `SIGNING_FORBIDDEN` |
| `issue`, `pay` | `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY` |
| `widen_grant`, `reissue_grant`, `revive_grant` | `AI_SELF_EXPANSION_FORBIDDEN` |

그 밖의 이름은 `TOOL_NOT_ALLOWED`다.
허용 목록은 `reference/v0.3-rc1/protocol_contract.json`의 `commands` 키와 서로소다.
`delegate`와 `close_delegation`을 도구로 호출해도 명령이 실행되지 않고 `TOOL_NOT_ALLOWED`다.

`propose_grant_change`의 `requested`는 `authority`, `scope`, `limits`, `period`, `note`만 담는 메모다.
`authority`에 `EXECUTE`가 있으면 `EXECUTE_AUTHORITY_DISABLED`이고 메모도 남기지 않는다.
나머지 요청이 적히더라도 발급된 부여의 권한·범위·한도·기간·세대는 바뀌지 않는다.

## 6. 술어

시험 docstring은 이 식별자를 인용한다.

| ID | 술어 |
|---|---|
| DLG-01 | `QUERY` 도구와 `view_*`는 상태를 바꾸지 않는다 |
| DLG-02 | `PROPOSE`는 비활성 제안 메모만 쓴다 |
| DLG-03 | 부여에 `EXECUTE`를 넣으면 `EXECUTE_AUTHORITY_DISABLED` |
| DLG-04 | `attempt_execution`은 항상 `DELEGATED_EXECUTION_DISABLED`이고 상태를 바꾸지 않는다 |
| DLG-05 | `issue`·`pay`는 `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY`. 발행·지급 플래그는 거짓이다 |
| DLG-06 | AI의 발급·확대·재발급·부활은 `AI_SELF_EXPANSION_FORBIDDEN`이고 상태가 그대로다 |
| DLG-07 | AI의 `decide_proposal`은 `AI_CANNOT_DECIDE`이고 상태가 그대로다 |
| DLG-08 | `propose_grant_change`는 메모만 남기고 부여 본문을 바꾸지 않는다 |
| DLG-09 | 허용 목록과 거부 목록은 서로소다. 이전·환불 실행·서명은 거부 코드다 |
| DLG-10 | 허용 목록은 `protocol_contract.json` 명령 키와 서로소다 |
| DLG-11 | 목은 `reference/v0.3-rc1`을 import하지 않는다 |
| DLG-12 | `delegate`와 `close_delegation`을 호출·재사용·개명하지 않는다 |
| DLG-13 | scope는 소속만 검사하고 식별자를 해석하지 않는다 |
| DLG-14 | 세 한도와 `currency`는 필수다. 기본값·무제한은 없다 |
| DLG-15 | 누적액과 건수는 `PROPOSED`와 `HUMAN_APPROVED`를 포함한다 |
| DLG-16 | `HUMAN_REJECTED`와 `WITHDRAWN`은 한도 몫을 되돌린다 |
| DLG-17 | 요청을 나눠도 누적·건수 한도를 넘지 못한다 |
| DLG-18 | `bool`·0·범위 밖 금액은 `INVALID_AMOUNT` |
| DLG-19 | 기간은 양 끝 포함이다. `now < not_before`이면 `GRANT_NOT_CURRENT`, `now > not_after`이면 `GRANT_EXPIRED` |
| DLG-20 | 철회는 기록되는 즉시 그 세대의 도구 사용을 막는다 |
| DLG-21 | 철회는 `PROPOSED` 제안을 `VOIDED_BY_REVOCATION`으로 두되 지우지 않는다 |
| DLG-22 | 이력은 삭제하지 않는다. 철회된 세대와 제안이 조회에 남는다 |
| DLG-23 | 철회된 세대는 같은 `grant_id`로 되살리지 않는다 |
| DLG-24 | 다음 세대는 그 쌍의 이전 세대가 `REVOKED`일 때만 발급된다 |
| DLG-25 | 같은 `grant_id`와 같은 바인딩은 `duplicate: true`. 다른 바인딩은 `GRANT_BINDING_CONFLICT` |
| DLG-26 | 같은 `proposal_id`와 같은 바인딩은 `duplicate: true`. 다른 바인딩은 `PROPOSAL_BINDING_CONFLICT` |
| DLG-27 | `decide_proposal`은 결정 시점에 통화·철회·기간·한도를 다시 확인한다 |
| DLG-28 | 승인은 메모다. `effects_executed`는 거짓이다 |
| DLG-29 | §8의 플래그는 항상 거짓이다 |
| DLG-30 | 조회에 `provenance`와 `lifecycle_authority`가 있다 |
| DLG-31 | 실행을 켜는 생성자 인자가 없다 |
| DLG-32 | `issue_grant`, `revoke_grant`, `decide_proposal`은 인간 주체만 호출한다 |
| DLG-33 | 조회 도구는 `QUERY`, 제안 도구는 `PROPOSE`가 있어야 한다 |
| DLG-34 | `currency`는 `KRW`다. 정수 상한 `1 .. 10**12`는 fixture 범위이지 제품 한도가 아니다 |
| DLG-35 | `state_digest`는 정규 JSON의 sha256 16진 문자열이다. 서명이 아니다 |
| DLG-36 | 허용·거부 목록 어느 쪽에도 없는 도구는 `TOOL_NOT_ALLOWED`다 |

## 7. 부여와 제안의 단계

제안 단계만 움직인다. 승인이나 거절은 부여 본문을 바꾸지 않는다.

```text
PROPOSED --> HUMAN_APPROVED
         \-> HUMAN_REJECTED
         \-> WITHDRAWN
         \-> VOIDED_BY_REVOCATION
```

`HUMAN_APPROVED`는 사람이 메모를 승인했다는 기록이다.
그 자리에서 도구·이전·환불·서명·발행·지급을 실행하지 않는다.
`effects_executed`는 거짓으로 남는다.

한도와 기간을 보는 순서 (`propose_action`):

1. `actor`가 그 부여의 `agent_id`인지.
2. 도구 이름이 거부 목록인지, 허용 목록인지.
3. 부여가 있는지, 철회됐는지, 그 쌍의 `ACTIVE` 세대인지.
4. `not_before <= now <= not_after` 인지.
5. 필요한 권한 수준이 있는지.
6. `surface`가 `surfaces`에 있는지. `subjects`가 있으면 넘긴 `subject`만 그 목록에 있어야 한다. `subjects`를 생략하면 subject를 제한하지 않는다.
7. 금액이 `per_action_max` 이하인지.
8. 이번 금액을 더해도 `cumulative_max` 이하인지, 건수가 `count_max` 이하인지.

누적액과 건수에는 `PROPOSED`와 `HUMAN_APPROVED`만 들어간다.
거절·철회(`withdraw`)·회수에 따른 void는 몫을 뺀다.
따라서 한 요청을 여러 `proposal_id`로 나눠도 합과 건수로 막힌다.
`propose_grant_change`는 금액이 없고 건수만 쓴다.

`decide_proposal`은 새 결정을 쓰기 전에 부여의 `currency`, 철회, 기간, 건별·누적·건수 한도를 다시 읽는다.
이미 같은 결정이 있으면 `duplicate: true`이고 다시 검사해 실패로 바꾸지 않는다.
기간이 지났거나 아직 시작 전이면 제안은 `PROPOSED`로 남고 결정만 거절된다.
철회된 뒤의 대기 제안은 이미 `VOIDED_BY_REVOCATION`이다.

`withdraw_proposal`은 기간이 지난 뒤의 `PROPOSED`도 거둘 수 있다.
부여가 이미 철회됐으면 `GRANT_REVOKED`다.
`now`의 형식은 검사한다. 기간 창으로 이 도구를 거절하지는 않는다.

같은 `grant_id`의 재전송은 바인딩이 같으면 효과를 다시 내지 않는다.
바인딩이 다르면 `GRANT_BINDING_CONFLICT`다.
철회된 기록과 바인딩이 같으면 `duplicate: true`이고 `phase`는 `REVOKED`로 남는다.
제안도 같다. 같은 바인딩은 `duplicate: true`, 다른 바인딩은 `PROPOSAL_BINDING_CONFLICT`다.
이미 있는 제안과 바인딩이 같으면, 그 부여가 나중에 철회되거나 기간 밖이어도 검사를 다시 하지 않고 `duplicate: true`를 돌려준다.
새 제안만 그때의 철회·세대·기간·권한 수준을 본다.
두 번째 철회는 사유가 달라도 사유를 덮어쓰지 않고 `duplicate: true`다.

`state_digest`는 `canonical_state()`를 키 정렬, `ensure_ascii` 거짓, 구분자 `(",", ":")`인 JSON으로 만든 뒤 UTF-8 sha256을 16진으로 적는다.
서명도 체인 약속도 아니다.

## 8. 오류 코드와 항상 거짓인 플래그

| 코드 | 언제 |
|---|---|
| `AI_SELF_EXPANSION_FORBIDDEN` | AI가 발급·철회·확대·재발급·부활을 시도 |
| `AI_CANNOT_DECIDE` | AI가 `decide_proposal`을 호출 |
| `UNKNOWN_ACTOR` | 등록되지 않은 행위자, 또는 그 기록의 issuer·agent가 아닌 행위자 |
| `UNKNOWN_GRANT` | 없는 `grant_id` |
| `UNKNOWN_PROPOSAL` | 없는 `proposal_id` |
| `TOOL_NOT_ALLOWED` | 허용 목록에 없거나, 부여에 그 도구의 수준이 없음 |
| `TRANSFER_FORBIDDEN` | `transfer` |
| `REFUND_EXECUTION_FORBIDDEN` | `refund_execution` |
| `SIGNING_FORBIDDEN` | `sign` |
| `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY` | `issue`, `pay` |
| `EXECUTE_AUTHORITY_DISABLED` | `EXECUTE`를 구조화된 권한에 넣음 |
| `DELEGATED_EXECUTION_DISABLED` | `attempt_execution` |
| `GRANT_NOT_CURRENT` | 시작 전, 또는 그 쌍에 이미 `ACTIVE` 세대가 있는데 다른 부여를 발급 |
| `GRANT_REVOKED` | 철회된 세대의 사용, 또는 이미 void된 제안을 결정·철회 |
| `GRANT_EXPIRED` | `now > not_after` |
| `SCOPE_VIOLATION` | 범위 형식 또는 소속 실패 |
| `LIMIT_REQUIRED` | 한도 필드가 빠지거나 `currency`가 `KRW`가 아님 |
| `PER_ACTION_EXCEEDED` | 건별 상한 초과 |
| `CUMULATIVE_EXCEEDED` | 누적 상한 초과 |
| `COUNT_EXCEEDED` | 건수 상한 초과 |
| `INVALID_ID` | 식별자·결정 토큰·인자 형식 |
| `INVALID_AMOUNT` | `bool`, 0, 음수, `10**12` 초과, 정수가 아닌 금액·건수 |
| `INVALID_PERIOD` | 기간 또는 `now` 형식, `not_before > not_after` |
| `GRANT_BINDING_CONFLICT` | 같은 `grant_id`, 다른 본문 |
| `PROPOSAL_BINDING_CONFLICT` | 같은 `proposal_id`, 다른 본문. 또는 결정할 수 없는 단계 |
| `MOCK_INVARIANT` | 목 내부 불변식 |

`UNKNOWN_GRANT`와 `UNKNOWN_PROPOSAL`은 없는 식별자를 바인딩 충돌과 구분한다.

다음 플래그는 항상 거짓이다. 성공한 호출이 참을 만들지 못한다.

`execution_enabled`, `funds_executed`, `issued`, `paid`, `signed`, `transferred`,
`refund_executed`, `chain_grant_confirmed`, `revocation_cut_confirmed`, `durable`, `legal_authority`.

`issued`와 `paid`는 권리 발행과 자금 지급이다.
부여 레코드를 적거나 제안 메모를 승인해도 이 플래그는 거짓이다.

## 9. UNDETERMINED와 후속 결정

이 목이 숫자나 이름으로 채우지 않는 것이다. 시험 fixture는 정책 값이 아니다.

| 항목 | 상태 | 정할 주체 |
|---|---|---|
| 건별·누적·건수의 제품 한도, 기간의 길이, 집계 창(주문·계정·기간) | UNDETERMINED | Astra (U11-L) |
| AI 서비스 identity, I11의 발급자·대체자 외에 누가 인간 주체인지 | UNDETERMINED | Astra와 사용자 (U11-ID) |
| 어떤 표면을 부여할 수 있는지, 어떤 제안 종류를 허용하는지 | UNDETERMINED | Astra |
| 기간의 권위 있는 시각원, 체인 회수 cut `C_g`/`H_g` | UNDETERMINED | `k1-cut-proof`, RS-3a |
| 정지와 재개. 목은 철회와 새 세대만 둔다 | UNDETERMINED | Astra |
| AI의 행위가 issuer를 구속하는지, 책임과 법적 성격 | UNDETERMINED | 법무 검토 (D-E, 사용자) |
| 와이어 명령, 온체인 grant (RS-3a), Rust 결합 (RS-3b) | 이 노드 밖 | 후속 노드 |
| 실행을 켜는 결정 | 이 노드 밖 | `ai-delegation-execution-decision` (사용자 병합) |

제품 한도나 새 프로토콜 명령을 이 초안에서 정하지 않는다.
법적·세무·회계·제공자 답이 필요한 값도 비워 둔다.

## 10. 비주장

- 이 목의 통과는 AI 위임이 구현됐다는 뜻이 아니다.
- 내구 저장, 체인 grant, 신원 시스템, 서명, 자금 이동, 환불 실행이 아니다.
- `state_digest`는 이 프로세스 메모리의 sha256이다.
- `HUMAN_APPROVED`는 법적 승인도 결제 승인도 아니다.
- 등록된 인간 주체 이름은 운영 권한의 지명이 아니다.
- F04·E06과 원래 32개 항목의 라벨은 바뀌지 않는다.
- 프로토콜 검증 워크플로(`.github/workflows/protocol.yml`)는 2026-10-08부터 `reference/ai_delegation`의 시험을 발견해 실행한다. 이 실행은 이 목의 구현·운영 준비·내구성을 뜻하지 않는다. 초안 0.1 작성 시점에는 실행하지 않았다.
