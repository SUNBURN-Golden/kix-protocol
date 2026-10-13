# TL-4 — 토큰 계층의 제한된 검증 기록

노드 `tl-4`. 이슈 없음. 문서일: 2026-10-09.

이 세션 시작에 `git fetch origin main`으로 확인한 `origin/main`과 작업 브랜치 `agent/kix-tl-4`의 HEAD는 같다: `6bdd571fcb88496c98e25b32213c60017e209198`. 그 커밋은 PR #159의 병합이다. 이 세션은 커밋하지 않는다. 구현 커밋 SHA는 없다. 나중의 커밋 SHA에 이 기준의 CI를 옮기지 않는다.

이 세션은 ASTRA 프로그램 모드가 아니다. 서명자가 없고, 배달 표시를 적지 않는다. 프로그램 모드가 적는 브랜치 이름은 `astra/tl-4`다. 이 노드의 이슈는 없고, 이슈가 브랜치 이름을 적지 않는다. 작업 지시는 `agent/kix-tl-4`다. 이 기록은 브랜치를 만들거나 이름을 바꾸지 않는다.

잠금 blob 둘은 작업 전 요구값과 일치했다. 이 기록과 하네스를 더한 뒤에도 같아야 한다. `runtime/crates/kix-kernel/src/lib.rs`는 `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`는 `b607996c83a119c349f1cc90469ac1ba82764e20`. 두 파일은 수정하지 않는다. `reference/v0.3-rc1/**`도 수정하지 않는다.

상태: 기록, 작성자=빌더, 독립 검토 아님. 패키지가 아니다. 효력은 사용자가 이 기록을 병합할 때에만 생긴다. 작성자가 빌더이므로 독립 검토가 아니고, 비작성자 exact-HEAD 검토가 아니다 ([AGENTS.md](../../AGENTS.md) §6, §14). 검토됨으로 표시하지 않는다. 자기 검토를 독립 PASS로 세지 않는다.

노드 입력은 `depends_on: tl-2, tl-3-onchain`, `audit_floor: A3`, `astra_gate` 없음, `user_merge` 없음이다. [.aiops/program.json](../../.aiops/program.json)의 `tl-4`는 `astra_auto_merge: true`이고 `user_merge` 키가 없다. [판정 표](../aiops/PROGRAM_ASTRA_DELEGATION.md)의 `tl-4` 행은 `contract_change` NO, 병합은 정책 C 위임, A3다. 로드맵 §1은 그 판정 표를 현재 병합 경계로 둔다. 로드맵 §3.5의 이 노드 행은 Astra 게이트 ARCHITECTURE, 병합 자동(M1·Fable)이다. `program.json`에는 `astra_gate`가 없다. 이 기록은 그 차이를 해소하지 않는다. 빌더는 병합하지 않는다.

`docs/tasks/`에 이 노드의 작업 문서는 없다. 입력은 `program.json`의 `tl-4` 스펙이다. 그 파일은 수정하지 않는다.

표시는 [청사진](../blueprints/optional-native-token-v1/README.md) §0과 같다. **[현재]**는 이 세션이 저장소에서 읽은 사실이다. **[제안]**은 채택 전 설계 문장이다. **[미확인]**은 이 기록이 채우지 않은 값이다.

이 기록은 청사진 TL-4 인수인 「TK-1~TK-9 독립 검증, 미해결 차단 없음」을 닫지 않는다. 패키지가 없으므로 그 문장을 충족했다고 적지 않는다.

## 1. 범위와 제한된 읽기

[TL-2 기록](TL2_DOES_NOT_OPEN_20261009.md)과 [TL-3 온체인 기록](TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md)은 둘 다 열리지 않는다는 기록이다 **[현재]**. Move 패키지도 온체인 보상 기록도 없다. [ADR-0003](../adr/0003-coin-tix-lock-localnet-re-ruling-request.md) §4 O1과 §7은 `tl-3-onchain`과 `tl-4`가 제한된 채로 남는다고 적는다. 그 문장이 「제한」의 절차를 정의하지는 않는다 **[미확인]**.

이 노드가 택한 읽기 **[제안]**. 제한은 오프체인에 있는 것만 검증하고, 패키지가 있어야 하는 술어는 `NOT VERIFIABLE · no package`로 적는 것이다. 온체인 대역을 만들지 않는다. 잠금을 푼 것으로 읽지 않는다. 이 읽기가 거절되면 갈래는 TL-2를 다시 여는 길과, 짧은 기록만 내는 길이다. 둘 다 `DECISION_REQUIRED · Astra`다. TL-2를 다시 여는 길은 ADR-0003 O2와 사용자 병합이 필요하다. 이 세션은 그 갈래를 실행하지 않는다. Astra 감사가 이 읽기를 확인한다.

있는 구현 **[현재]**. `reference/token_reward/token_reward_model.py`와 `reward_fsm.py`는 F4 포인트, 인메모리, `MOCK_TOKEN_REWARD_ONLY`다. 제품 코드는 바꾸지 않는다. 청사진은 발견된 결함을 새 작업으로 둔다.

검증하는 것.

- 이 위협 모델.
- `reference/token_reward` 위의 결정적 속성·퍼즈 하네스. 적대적 오라클이다. TK-4, TK-7, TK-8, TK-12, V6, 그리고 TK-6 `TL1-TK06-T6`와 TK-10의 오프체인 조각을 다룬다.
- 패키지가 없다는 저장소 경계. `TL1-TK02-T1`과 TK-9 이름 스캔.
- TK-11 문구 보조 검사와 TK-10 게이트 기록 검토.

검증하지 않는 것. `NOT VERIFIABLE · no package`. TK-1, TK-2의 T2–T4, TK-3, TK-5의 V1–V5, TK-6의 T1–T5, TK-9의 실제 가스 경로, `TL1-LC-T1`, `TL1-LC-T2`. Move 코드를 만들지 않는다.

## 2. 자산과 신뢰 경계

아래는 인메모리 모델 안의 자산이다. 체인 잔고나 은행 잔고가 아니다 **[현재]**.

| 자산 | 경계 |
|---|---|
| F4 포인트 | `UNIT`은 `POINT_F4`. 코인 원자나 원화 지급이 아니다 |
| 다섯 풀 | 고객 예치금, 주최자 정산금, 환불 준비금, 프로토콜 수익, 토큰 재무·보상. 시작 잔액은 호출자가 준다 |
| 저널과 멱등 표 | 수용된 명령만 저널에 남는다. 멱등 표는 재생 결과와 거절 코드를 기억한다 |
| 승인 슬롯 | 구조적 칸이다. 승인자를 지명하지 않는다. E-1은 열려 있다 |
| 출처 뷰 스냅샷 | 호출자가 넣은 COMMITTED 뷰다. 이 기계가 다른 기계를 호출하지 않는다 |
| 공급 숫자 | 합성 사건 목록을 다시 계산한 값이다. 체인에서 읽지 않는다 |

`ALWAYS_FALSE_FLAGS`는 일곱 개다. 그중 권한 플래그의 이름은 모델 소스의 그 튜플과 같고, 이 기록은 그 플래그를 참으로 두지 않는다. 모델이 이 플래그를 참으로 두는 경로를 이 세션은 보지 못했다 **[현재]**.

## 3. 행위자

공격 절차를 적지 않는다. 이름은 위협의 자리다.

| 행위자 | 자리 |
|---|---|
| 중복·지연 제출자 | 같은 원거래의 보상 요청을 다시 내거나 늦게 낸다 |
| 형식 오류 전송자 | 풀, 담보, 저널, 승인 칸에 기대하지 않은 값을 넣는다 |
| 규칙 버전을 바꾸는 쪽 | 같은 보상 ID에 다른 규칙 버전으로 다시 지급을 요구한다 |
| 남용 | 자기거래, 중복 계정, 추천 농사. 종류 이름만 있다. 탐지 정책 숫자는 없다 |
| UNKNOWN 재전송자 | 결과를 모르는 제출을 허가 없이, 또는 다른 digest로 다시 낸다 |
| 위조 관측자 | 출처 뷰나 공급 보고서를 호출자 값으로 넣는다. 체인 서명은 이 모델에 없다 |
| 지시문을 넣는 AI | 승인 주체를 AI로 두거나, 근거에 UNKNOWN을 넣는다 |
| 승인 슬롯을 가진 내부자 | 같은 `record_id`를 다시 쓰거나, 사람 슬롯의 형태만 채운다. 사람 이름은 비어 있다 |

## 4. 위협 표

제어 열은 모델이 돌려주는 코드 이름이다. 절차가 아니다. 하네스 열은 작성자 측 시험이다. 독립 PASS가 아니다.

| ID | 위협 | 자산 | 모델 안 제어 | 하네스 | 잔여 |
|---|---|---|---|---|---|
| T1 | 의무 풀로 포인트 지출 | 다섯 풀 | `POOL_FORBIDDEN_FOR_TOKEN_SPEND` | `test_TL4_TK04_*` | 풀 잔액 숫자는 `DECISION_REQUIRED · Astra` |
| T2 | 부족한 풀을 다른 풀로 메움 | 다섯 풀 | `POOL_EXHAUSTED_PAUSED`. 이전·보충 메서드 없음 | 같은 시험 | 회계 순서는 `UNDETERMINED · 외부 검토` |
| T3 | 토큰만으로 원화 부채를 담보 | 담보 산정 | `TOKEN_ONLY_COLLATERAL_REJECTED` | `test_TL4_TK12_*` | 담보 자산 선택은 `DECISION_REQUIRED · Astra` |
| T4 | 가격 평가 키로 토큰을 원화에 넣음 | 담보 산정 | `PRICE_SOURCE_UNDEFINED` | 같은 시험 | 가격원 계약은 열리지 않았다 **[현재]** |
| T5 | 승인되지 않은 민팅·경로로 지급을 계속 | 공급 숫자 | `stop_payout`가 그 두 경보에서만 참 | `test_TL4_V6_*` | V1–V5는 패키지 없음 |
| T6 | 보고서 필드를 바꿈 | 공급 숫자 | `SUPPLY_REPORT_MISMATCH` | 같은 시험 | 체인 그림은 호출자가 넣은 정수다 |
| T7 | 같은 보상을 다시 지급 | 저널, 풀 | 중복은 `duplicate`. 다른 본문은 `IDEMPOTENCY_CONFLICT` | `test_TL4_TK07_*` | 온체인 1회는 패키지 없음 |
| T8 | 규칙 버전만 바꿔 다시 지급 | 보상 ID | ID 입력에 규칙 버전이 없다. 관측 후 변경은 `RULE_VERSION_REPAY_FORBIDDEN`. 지급 뒤 변경은 `supersede` 한 건당 효과 하나 | 같은 시험 | 규칙 버전 값은 정책 값. 비어 있다 |
| T9 | 토큰 단계를 원화 환급 기록으로 이동 | 두 effect | `observe_krw_refund`가 토큰 단계와 결과를 유지. effect ID가 다르다 | `test_TL4_TK08_*` | 원화 기계의 실행은 이 모델이 아니다 |
| T10 | AI 또는 UNKNOWN 근거로 승인 | 승인 슬롯 | `AI_APPROVAL_REJECTED`, `APPROVAL_EVIDENCE_UNKNOWN`, `ACTOR_TYPE_REJECTED` | `test_TL4_TK06_T6_slice_*` | E-1은 `DECISION_REQUIRED · User` |
| T11 | 허가 없이 UNKNOWN을 재전송 | 저널 | `RESEND_PERMIT_REQUIRED`, `DIGEST_MISMATCH`. 대사는 새 보상을 만들지 않는다 | `test_TL4_TK07_unknown_*` | fence는 커널 fence가 아니다 |
| T12 | 망가진 저널로 상태를 바꿈 | 저널 | `TokenRewardError` | `test_TL4_mutated_journals_*` | `effect_id`의 비정규 인자는 §6.B |
| T13 | 다음 단계 산출물을 게이트 없이 둠 | 단계 | 패키지·배포·발행 기록이 없다 | TK-10 검토 | S3는 TL-5 |
| T14 | 산출물 문구가 권리 주장을 함 | 문구 | 보조 스캔과 이 절의 비주장 | TK-11 검토 | 사람 검토가 남는다 |

## 5. TK-1부터 TK-12까지

상태 이름은 이 노드의 분류다. 독립 PASS가 아니다. 예약 ID는 프로토콜 명령이 아니다.

| ID | 상태 | 이 세션이 한 일 |
|---|---|---|
| TK-1 | `NOT VERIFIABLE · no package` | 여섯 자산의 타입 분리를 볼 패키지가 없다. TL-2 기록 |
| TK-2 | T1은 저장소 경계. T2–T4는 `NOT VERIFIABLE · no package` | `TL1-TK02-T1`. Move 매니페스트는 `reference/v0.3-rc1/sui/Move.toml` 하나다 **[현재]**. 정산·예매·여신·AI 참조 모듈이 `token_reward`를 import하지 않는다 |
| TK-3 | `NOT VERIFIABLE · no package` | 토큰 쪽 정지가 관람권·원화 의무를 끄는 경로를 볼 패키지가 없다 |
| TK-4 | `HARNESS (author-side)` | 풀 오라클. 잔액 = 시작 + 적립 − 지출. 의무 풀은 거절. 부족은 다른 풀을 바꾸지 않는다 |
| TK-5 | V6은 `HARNESS (author-side)`. V1–V5는 `NOT VERIFIABLE · no package` | 공급 오라클은 §5.1과 §5.2 V6만 다시 적는다 |
| TK-6 | T6 조각은 `HARNESS (author-side)`. T1–T5는 `NOT VERIFIABLE · no package` | AI·다른 행위자·UNKNOWN 근거·`record_id` 재사용을 거절한다. 승인자를 지명하지 않는다 |
| TK-7 | `HARNESS (author-side)` | 무작위 명령열, 재생, 멱등, UNKNOWN 대사. 지급 효과 수 ≤ 1 + 대체 수 |
| TK-8 | `HARNESS (author-side)` | 원화 환급 기록이 토큰 단계와 결과를 옮기지 않는다. effect ID가 다르다 |
| TK-9 | 이름 스캔은 보조. 실제 가스 경로는 `NOT VERIFIABLE · no package` | `token_reward_model.py`와 `reward_fsm.py`에 `gas`·`sponsor` 문자열이 없다 **[현재]**. 증명이라고 적지 않는다 |
| TK-10 | `REVIEWED (gate records)` | §5.1. 배포·발행을 연 게이트 기록은 없다 |
| TK-11 | `REVIEWED (wording)` | §5.2. 작성자 검토다. 독립 검토가 아니다 |
| TK-12 | `HARNESS (author-side)` | 인정액은 KRW 보증과 에스크로 합. 토큰 인정액은 0. `valuation` 키는 거절 |

### 5.1 TK-10 게이트 기록

권한·수명 계약 §6의 S0–S3를 저장소 기록에 대조했다. 판단이 아니다.

| 단계 | 산출물 | 이 세션이 본 기록 |
|---|---|---|
| S0 설계 | 청사진, ADR-0002, TL-0, TL-1 | 문서가 있다 **[현재]**. 이 파일이 S0을 다시 승인하지 않는다 |
| S1 비운영 구현 | localnet 패키지 | TL-2 기록은 패키지를 만들지 않았다. Move 매니페스트는 잠긴 하나다 |
| S2 통합·보안 검증 | TL-4 | 이 파일은 작성자 하네스다. S3를 여는 게이트 기록이 아니다 |
| S3 배포·발행 | TL-5 | 프로그램 결정 §5가 묶는다. testnet·mainnet 배포 기록은 없다 **[현재]** |

`TL1-TK10-T1`부터 `T3`의 확인 판단은 TL-5다. 이 노드는 그 판단을 하지 않는다.

### 5.2 TK-11 문구

담당은 이 노드다. 보조 스캔은 새 TL-4 산출물만 본다. 긍정 주장으로 보는 낱말은 legal, return, liquidity, price-keeping, production-ready와 합법, 인허가, 투자수익, 유동성, 가격 유지다. 줄에 `않`, `아니`, `없`, `not`, `no `가 있으면 그 줄은 건너뛴다. 건너뛴 줄은 사람이 아직 읽지 않은 것이다. 이 스캔의 통과는 TK-11의 독립 검토가 아니다.

작성자가 이 기록과 하네스와 증거 README를 읽었다. 권리 주장으로 읽을 문장을 두지 않으려 했다. 비작성자가 다시 읽어야 한다.

일부러 고치지 않은 교차 참조. [능력 대장](../status/CURRENT_CAPABILITY_REGISTER.md)의 TL-4 행은 아직 not covered다. 그 문장은 이 하네스가 독립 검증이 아니라는 뜻에서는 맞다. 경로를 이 노드가 맞추지 않는다. 개발계획 §18의 포인터도 맞추지 않는다. 맞추는 일은 나중 동기화에 남긴다.

## 6. 발견 기록

이 세션의 로컬 실행에서 작성자 측 오라클과 모델이 어긋나지 않았다. 명령과 종료 코드는 증거 README에 있다. 그 일치는 독립 PASS가 아니다.

### A. 계약과 일치

풀, 담보, 예산, `reward_id`, V6, 상태 기계의 작성자 측 오라클이 모델과 같았다. 거절된 명령은 `canonical_state`와 저널을 바꾸지 않았다. 의무 풀 지출은 거절되었다. 토큰만의 담보와 `valuation` 키는 거절되었다. `stop_payout`는 `UNAPPROVED_MINT`와 `UNAPPROVED_PATH`에서만 참이었다. 보유자 소각은 체인 숫자가 계층 공급에서 그 소각을 뺀 값일 때 불일치가 아니었다. AI 승인과 UNKNOWN 근거와 `record_id` 재사용은 거절되었다. 패키지를 만들지 않은 것은 TL-2·TL-3 온체인 기록과 같다.

이 일치는 어느 쪽이 옳은지의 증명이 아니다. 작성자가 계약 문장으로 오라클을 다시 적었고, 그 작성자가 빌더다.

### B. 계약이 정의하지 않음. 성격만 기록

`effect_id`는 정규 인자로 digest를 만든다. 계약이 그 함수의 오류 클래스를 적지 않는다. 집합을 넣으면 `TypeError`가 난다. `TokenRewardError`로 감싸지 않는다. 펜스가 있는 명령 표면(풀, 담보, 공급, 예산, `RewardMachine`의 공개 메서드, `restore`)은 같은 종류의 쓰레기 값에서 `TokenRewardError`만 냈고, 거절은 상태를 바꾸지 않았다. 제품 코드를 고치지 않는다. 청사진은 결함을 새 작업으로 둔다. 이 관찰을 그 새 작업의 입력으로 올릴지는 비작성자 검토가 본다. 이 노드를 계약 위반으로 닫지 않는다.

`ISSUED`는 모델의 종결 집합에 들어 있다. `supersede`와 `observe_source_cancel`은 그 단계에서 나가는 정의된 전이다. 하네스는 `REVERSED`와 `CLAWBACK_CLAIM`만 단계가 바뀌지 않는다고 검사한다. 계약이 「종결은 불변」을 `ISSUED`의 그 두 출구까지 금지한다고 적지 않는다. 의미를 지어 계약을 고치지 않았다.

두 원인이 같이 있으면 모델은 `UNAPPROVED_PATH`를 `UNAPPROVED_MINT`보다 앞에 둔다. V6은 둘 다 지급을 멈추는 원인이라고 적는다. 우선순위를 적지 않는다. 하네스는 `stop_payout`가 그 두 경보에 해당하는지만 고정한다.

### C. 명시적 계약 위반

없음. 잠금 파일을 고칠 위반이 아니다. 오라클과 모델이 어긋나는 재현이 생기면 이 절을 그 재현으로 바꾸고, 병합을 제안하지 않는다.

## 7. 비작성자 검토에 넘기는 것

검토자는 제품 코드를 답으로 베끼지 않고 아래 오라클을 계약에서 다시 적는다.

- 풀. 역할·공급 계약 §6. 잔액 = 시작 + 적립 − 지출. 의무 세 풀은 토큰 지출 금지. 부족은 다른 풀을 움직이지 않는다.
- 담보. TK-12. 인정액은 KRW 보증과 에스크로의 합. 토큰 인정액은 0. `valuation`은 거절.
- 공급. §5.1과 §5.2 V6. `allocate`는 계층 공급을 바꾸지 않는다. 승인되지 않은 민팅과 승인되지 않은 경로는 지급을 멈춘다. 보유자 소각은 그 조건에서 불일치가 아니다.
- 예산. §6. `min(상한, floor(잔여 × 분자 / 분모))`. 기간 개수는 곱수가 아니다. 창 안 수익은 잔여에서 빠진다.
- `reward_id`. 네 칸에 민감하고 규칙 버전을 입력으로 받지 않는다.
- 상태 기계. 권한·수명 계약 §4와 §5와 §7. 지급 효과와 원화 효과의 분리. UNKNOWN은 미실행이 아니다.

명령은 증거 README의 표와 같다. exact-head CI의 실행 ID는 그 헤드가 생긴 뒤의 PR 보고에 둔다. 이 세션의 커밋이 아니므로 이 문서에 실행 ID를 적지 않는다 ([AGENTS.md](../../AGENTS.md) §11).

## 8. Move 감사 준비 점검표

문서만이다. 감사를 실행하지 않았다. 패키지가 없다.

| 항목 | 상태 | 담당 |
|---|---|---|
| `TL1-LC-T1` 옛 진입점이 정지를 우회하는가 | **[미확인]**. 시험하지 않음 | TL-2. 잠금 해제 뒤 |
| `TL1-LC-T2` 해제 기록이 수신까지 열었는가 | **[미확인]**. 표준 사실은 청사진 인용 | TL-2 |
| F2 `spent_balance` / `flush` | 택하지 않음. 소스를 이 세션이 다시 읽지 않음 | TL-2 |
| E-1 승인자와 수탁 | `DECISION_REQUIRED · User`. 열림 | User |
| 「키 생성 없음(localnet)」의 뜻 | `DECISION_REQUIRED · Astra` | Astra. ADR-0003 Q3 |
| 프레임워크 핀 | `808640d9b49aecf29d8e6f46033c15eca236efa7` 그대로 **[현재]** | 이 노드가 움직이지 않음 |
| 독립 Move 감사 | 하지 않음. 대상 패키지 없음 | 나중 노드 |

## 9. 레지스터와 비주장

이 기록이 아래 행을 닫지 않는다. 숫자를 넣지 않는다.

| 항목 | 분류 | 담당 |
|---|---|---|
| 「제한」의 절차 | 이 문서의 읽기 **[제안]**. Astra가 확인 | Astra |
| Astra 재결정이 저장소에 있는가 | 기록 없음 **[현재]** | ADR-0003 §5. 빌더는 PR 감사 댓글을 읽지 않는다 |
| 공급, 상한, 소수 자릿수, 풀 잔액, 비율, 기간 개수, 보상 금액 | `DECISION_REQUIRED · Astra` | Astra. 역할·공급 계약 §5.3 |
| 보상 기록 스키마와 새 명령 | `DECISION_REQUIRED · Astra` | Astra. 이 노드는 명령을 만들지 않는다 |
| 토큰 승인자, 수탁, 수탁 제품 (E-1) | `DECISION_REQUIRED · User` | User |
| 법률, 세무, 회계의 결론 | `UNDETERMINED · 외부 검토` | 착수 주체는 사용자 (D-E) |
| 지갑과 거래소 호환 | `UNDETERMINED · 담당 없음` | 청사진 §13과 ADR-0002 §6이 주인을 지명하지 않는다 |
| 차지백 가능 기간 | `UNDETERMINED · 카드/결제 제공자` | 토스 프로파일 경유 |
| 옛 진입점, F2와 fixed 또는 burn-only | **[미확인]** | TL-2 |

비주장.

- 독립 검증이 있었다는 것. 작성자 점검은 비작성자 exact-HEAD 검토가 아니다.
- 청사진 TL-4 인수가 닫혔다는 것. TK-1부터 TK-9까지의 온체인 검증이 끝났다는 것.
- 합법성, 인허가 충족, 투자수익, 유동성이 있음, 가격 유지를 주장하지 않는다.
- 토큰이 발행되었거나 채택되었거나 패키지가 있다는 것. `onchain_recorded`가 참이라는 것.
- 운영 준비, 실자금, 은행의 정확 1회, 체인 확정, 내구성, 분산 fence.
- exact-head CI가 이 기록을 담은 헤드에서 돌았다는 것. 이전 SHA의 녹색을 이 헤드로 옮기지 않는다.
- 보조 문구 스캔이 TK-11의 사람 검토를 대신한다는 것. 이름 스캔이 가스 경로가 없다는 증명이라는 것.

[프로그램 결정](PROGRAM_DECISIONS_20260928.md) §5의 잠금은 유지한다. 실자금, 실 PG·은행·KYC 호출, 공개 운영 엔드포인트, Sui testnet·mainnet, R2, 자체 복제·합의·저장 엔진, 새 coin/TIX 모듈을 열지 않는다. 프로토콜 명령을 새로 만들지 않았다. 키를 만들지 않았다. testnet과 mainnet을 호출하지 않았다. 운영 런타임을 만들지 않았다.
