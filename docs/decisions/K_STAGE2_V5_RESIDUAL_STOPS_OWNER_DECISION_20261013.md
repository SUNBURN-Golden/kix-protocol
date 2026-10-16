# k-stage2-v5-impl 잔여 정지 — 소유자 결정 위치 기록 (2026-10-13)

노드 `plan-v5-residual-stops-owner-decision-record`. 이슈 없음. 문서일: 2026-10-16.

상태: 위치 기록. 결정을 새로 만들지 않는다. 검토됨으로 표시하지 않는다.

이 파일은 이미 병합된 v5 crate(PR #179)가 인용하는 2026-10-13 소유자 위임 결정의 원문이 저장소에 있는 위치를 적는다. [AGENTS.md](../../AGENTS.md) §5가 적는 `docs/decisions/` 아래에 가리키며, RS-1의 선례([RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md](RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md), [archive/rs-1.decision_answer.md](archive/rs-1.decision_answer.md))를 따른다. 원문의 값은 이 파일에 옮기지 않는다. 값은 보존본의 줄 번호로만 가리킨다.

## 1. 출처와 보존

| 항목 | 값 |
|---|---|
| 원문 제목 | 보존본 1행: `Decision answer — k-stage2-v5-impl residual stops (final)` |
| 날짜 | 2026-10-13 |
| 작성자 | 소유자 위임(owner delegate). 보존본 3행이 적은 대로. 이름은 이 파일에 적지 않는다. 지명은 [FIRST_BATCH_OPEN_INPUTS.md](../contracts/FIRST_BATCH_OPEN_INPUTS.md) I11(11, 35, 50행)에 이미 있다 |
| 원래 위치 | `/workspace/kix-run/state/k-stage2-v5-impl.decision_answer.md`. 저장소 밖 |
| 보존본 | `docs/decisions/archive/k-stage2-v5-impl.decision_answer.md` |
| 줄 수 | 37 |
| sha256 (원본과 보존본 동일) | `7ec8a961550b3f71c014c93da8b18b0fc1ea5250de717809af8d8cf37a3c0399` |
| git blob | `e106dab2a6e1aa3a55ee59ef2a3034e72a9a88c7` |
| 확인 명령 | `cmp /workspace/kix-run/state/k-stage2-v5-impl.decision_answer.md docs/decisions/archive/k-stage2-v5-impl.decision_answer.md` 출력 없음, 종료 0 |

보존본은 `cp`로 만든 바이트 그대로의 사본이다. 머리말도 편집도 없다. 이 노드 `k-stage2-v5-impl`의 입력이었다([검증 기록](../../validation/2026-10-13-k-stage2-v5-impl/README.md) 8–10행).

## 2. 하지 않는 것

이 파일은 출처 기록이다. 새 결정이 아니다. 보존본 3행이 스스로 적듯 법적 권위도 제공자 권위도 주장하지 않는다. 값을 채택하지 않고, 어떤 계약·계획·등록부 칸에도 값을 옮기지 않으며, 등급을 올리지 않고, 잠금을 열지 않는다.

## 3. 이 결정을 인용하는 병합된 파일

결정을 인용하는 곳 (`path:line`, 이 기록의 기준 SHA 시점):

- `runtime/crates/kix-kernel-v5/src/lib.rs:13,37-42,344`
- `runtime/crates/kix-kernel-v5/README.md:3,5,44,48`
- `validation/2026-10-13-k-stage2-v5-impl/README.md:8-10,137-139,195`
- `validation/2026-10-14-register-sync-v5-rs/README.md:69-71`
- `docs/status/CURRENT_CAPABILITY_REGISTER.md`의 EV-V5 행과 K2 행(이 노드가 그 포인터를 이 파일로 바꾼다)

주제만 이름 붙이고 결정 문서를 인용하지는 않는 곳: `docs/status/I12_REVIEW_PACK.md:9,194`, `docs/status/ASTRA_DECISION_SHEETS_KO.md:82`.

위 검증 기록 두 개의 "저장소 내 파일이 아님"이라는 옛 문장은 당시 기록이므로 고치지 않는다(AGENTS §6). 이 파일이 그 문장을 대체하되 편집하지 않는다.

## 4. 열린 충돌

보존본은 병합된 문장과 다른 곳에 값을 둔다. 아래 표는 두 쪽을 줄 번호로 놓을 뿐 어느 쪽도 고르지 않는다. 오른쪽 열은 보존본 줄 번호만 적고 값은 적지 않는다. 보존본 줄: 9 = I13 보관 주체와 예산, 14–18 = I09 값, 19 = I10 보류 형태.

| # | 병합된 문장(A쪽) | 보존본(B쪽) | 충돌 | 주인 |
|---|---|---|---|---|
| 1 | [RETENTION_PERIODS_PROPOSAL_20261009.md](RETENTION_PERIODS_PROPOSAL_20261009.md) 104, 108, 144행(§5 R1, §7: 기본값 없음, 호출자가 넣는 자리만). 130행: 병합은 R1만 채택 | `archive:3, 13–18` | 보존본은 커널 기본값을 둔다. 제안은 칸을 기본값으로 채우면 R1을 벗어난다고 적는다 | `DECISION_REQUIRED · Astra` |
| 2 | [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) 225행(§6.3: 구체 기간 미정, 기간 값은 두지 않는다) | `archive:14–18` | 계획은 기간 값을 두지 않는다고 적고 보존본은 값을 둔다 | `DECISION_REQUIRED · Astra` |
| 3 | [FIRST_BATCH_OPEN_INPUTS.md](../contracts/FIRST_BATCH_OPEN_INPUTS.md) 33행(I09: 미완결, 사용자 정책 선택과 측정) | `archive:14–18` | 행은 미완결로 남는데 보존본은 값과 SLO를 정한다. SLO는 정해졌을 뿐 측정이 아니다 | `DECISION_REQUIRED · Astra` |
| 4 | FIRST_BATCH_OPEN_INPUTS.md 34행, 제안 145행(I10: 미완결, 법정 기간 미산정) | `archive:16, 17, 19` | 보존본의 하한·증거 보존·보류 형태는 법적 검토 앞에 있다. 보존본 16행 자신이 법정 기간은 I10 대기라고 적는다 | `UNDETERMINED · 법무/개인정보` |
| 5 | FIRST_BATCH_OPEN_INPUTS.md 37행, 제안 52, 146행(I13: 미완결, 책임자 이름 없음, 지명은 사용자) | `archive:9` | 보존본은 임시 주체와 자리표시 예산을 적는다 | `UNDETERMINED · 운영/보안` |
| 6 | FIRST_BATCH_OPEN_INPUTS.md 31행(I07), 제안 58, 118행, [STATE_LIFECYCLE.md](../contracts/STATE_LIFECYCLE.md) 81, 221행, DEVELOPMENT_PLAN.md 212행: 제공자 공개 멱등 기간은 KIX 임계·보존기간이 아니다 (not a threshold) | `archive:14` | 보존본의 재시도 지원 기본값이 그 제공자 공개 기간과 같은 수다. I07의 상태는 「기존 공개값 재확인」이다 | `DECISION_REQUIRED · Astra` |

## 5. 어느 문장이 우선하는가

`DECISION_REQUIRED · Astra`. 병합된 제안·계획·계약과 2026-10-13 소유자 위임 결정 중 어느 쪽이 우선하는지는 정해지지 않았고 이 노드는 정하지 않는다. 사용자 병합이 필요하다. 승자를 고르지 않으며, 이 충돌을 AGENTS §8의 A/B/C로 분류하지 않는다(분류가 우선 문장에 달려 있다). 이 노드는 runtime 변경이 없다.

표 밖에서 함께 관찰한 것(주인을 정하지 않음): I11 `archive:25`와 FIRST_BATCH_OPEN_INPUTS.md 35행, [STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md](STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md) 137행. I12 `archive:7–8`과 FIRST_BATCH_OPEN_INPUTS.md 36행.

## 6. 비주장

- 작성자는 builder다. 독립 검토가 아니다.
- 사용자 병합이 필요하다.
- 이 글을 쓴 시점에 exact-head CI는 없다. 기록은 PR 종결 보고에 둔다(AGENTS §11).
- 등급을 올리지 않고 잠금을 열지 않는다. 「새로 실입력까지 완결된 행: 0」은 그대로다.
- 줄 번호는 기준 SHA `a013cb0c471be0422a4a70d6b98e86c03f7131fa` 시점이다.
