# Open User decisions ledger — 2026-10-22

> Builder-authored ledger, not a decision, not an adoption, not a review, and
> not a reply from any owner. It collects, in one place, the open User/owner
> decisions that live in `DECISION_REQUIRED` records outside main, and the
> repository facts that changed since each record was written.

작업: `plan-plan-open-user-decisions-ledger-20261022` · 루프 제안 노드(
`.aiops/program.json`에 없음, 이슈 없음, `docs/tasks/`에 과제 파일 없음).
선행: `plan-plan-astra-decision-sheets-rs-stage5`,
`plan-readiness-checker-partial-fixture`,
`plan-plan-booking-resale-adopt-issued-atomici`.
입력 정본: 이 노드의 명세와 그것이 가리키는 기록이다.

**이 원장은 어느 선택지도 고르지 않고, 어떤 값도 정하지 않고, 무엇을 검토됨으로
표시하지도 않고, 어느 노드의 상태도 바꾸지 않는다. 소유자는 빌더 세션 밖에서
노드를 다시 발동시켜야 한다.**

## 0. 기준

- 노드 입력: `audit_floor: A2`, `astra_gate: None`, `user_merge: false`.
- 읽은 기준 커밋: `56d5f59468969825e0e2cd22f6803ebb5e6fb662`
  (`git fetch origin main` 뒤 확인한 `origin/main`. 작업 브랜치 HEAD와 같다).
  브랜치: `agent/kix-plan-plan-open-user-decisions-ledger-20261022`.
- 다섯 기록은 모두 main 밖에 있고 이 원장은 그 본문을 병합된 계약으로 인용하지
  않는다. 본문은 이 세션에서 읽은 노드 입력(각 노드의 `DECISION_REQUIRED.md`)
  그대로이며, 출처는 각 행의 기록 원천에 적는다:
  - `k-stage5-durable-tx` — `/workspace/kix-run/state/k-stage5-durable-tx.decision.md`
    (2026-10-13; 미병합 작업트리 `agent/kix-k-stage5-durable-tx`의
    `DECISION_REQUIRED.md`와 같은 본문).
  - `rs-4-l2` — 미병합 작업트리 `/workspace/kix-run/wt/rs-4-l2/DECISION_REQUIRED.md`
    (2026-10-15).
  - `plan-readiness-conformance-negative-controls` — 미병합 작업트리
    `/workspace/kix-run/wt/plan-readiness-conformance-negative-controls/DECISION_REQUIRED.md`.
  - `plan-readiness-receipt-audit-tests` — 미병합 작업트리
    `/workspace/kix-run/wt/plan-readiness-receipt-audit-tests/DECISION_REQUIRED.md`
    (2026-10-21).
  - `plan-booking-resale-admission-seeded-property`(BRA 종류 C 정지) — 미병합
    작업트리 `/workspace/kix-run/wt/plan-booking-resale-admission-seeded-property/DECISION_REQUIRED.md`.
  모든 칸이 기록 본문을 그대로 재현할 수 있었으므로, 어느 칸에도
  「text not in repo; summarised from the node input」 표기를 쓰지 않았다.
- 「main 이후의 저장소 사실」 칼럼은 위 HEAD에서만 검증했다. 존재한다고 적은
  경로는 모두 `test -f`로 확인했고, 없다고 적은 경로는 모두 부재를 확인했다.
  main 밖 경로는 존재하는 것으로 링크하지 않는다.
- 잠금 blob은 작업 전 요구값과 일치했다.
  `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
  `b607996c83a119c349f1cc90469ac1ba82764e20`. 이 노드는 두 파일을 수정하지 않는다.
- 이 원장이 바꾸는 경로는 이 파일, `docs/README.md`의 위치 포인터,
  `docs/DEVELOPMENT_PLAN.md` §5의 한 행, 그리고
  `validation/2026-10-22-open-user-decisions-ledger/README.md`뿐이다.
  계약·결정 기록·프로그램 파일·`docs/tasks/`·`.aiops/`·`reference/v0.3-rc1/**`·
  `runtime/**`·CI는 고치지 않는다.

## 1. 원장 — 열린 항목 하나에 한 행

「기록 원천」은 main 밖 입력의 위치만 적는다. 선택지·권고 인용은 그 기록이
적은 표기를 그대로 옮긴다(목록 구조는 표 칸 안에서 이어 붙였고, 이 문서는
어느 인용도 찬성하지 않는다).

| 열린 항목 / 기록 원천 | 담당 (기록 원문) | 선택지 (기록이 적은 대로) | 권고 (기록이 적은 대로) | 그 기록 이후의 저장소 사실 (HEAD `56d5f59…`에서 검증) |
|---|---|---|---|---|
| `k-stage5-durable-tx` 수락 실행 host · `/workspace/kix-run/state/k-stage5-durable-tx.decision.md` (2026-10-13) | 「The User (host provisioning is an operations action, and merge is User-only) or the supervisor acting on the User's behalf for the build host.」 기록은 이어서 「Nothing else is open: no product policy value, protocol command, or lock change is requested.」라 적고, 남은 Astra 항목(`EventItemId` 원천·별칭 규칙·충돌 항목의 inbox 정책)은 수락 실행을 막지 않는다고 적는다. | 1. 「Provision the pinned backend, then rerun (recommended).」 — 「Install `postgresql-17` (17.11-0+deb13u1) and `python3-psycopg` on the build host, or run the node on the host that produced `validation/2026-10-08-k-stage4-local-exploration/`, then run `python3 -m unittest durable.test_durable` and `python3 scripts/stage5_local_check.py validation/2026-10-13-k-stage5-durable-tx`. Expect to fix small real-PostgreSQL issues: the SQL was only exercised against a throwaway sqlite stand-in (not evidence), and that is the main residual risk.」 2. 「Merge the code as an unverified candidate.」 — 「Not recommended: the acceptance criterion would be unmet, the suite is not wired into CI, so green CI would say nothing about the backend.」 3. 「Hold the node.」 — 「Keep it WAITING until option 1 is possible.」 | 별도의 권고 문단은 없다. 권고는 선택지 1의 표기 「(recommended)」가 담는다. | `scripts/check_stage5_host.py`가 존재한다 — 병합 #227 `154e9aae…`, 기록 `validation/2026-10-20-stage5-preflight/README.md`, 스스로 「evidence preparation for option 1, no provisioning, no option selected」라 적는다. 그 `--self-test`는 `.github/workflows/protocol.yml`의 무조건 실행 stdlib 단계(237행)에 배선됐다 — 병합 #255 `1a69364…`, 기록 `validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md`; 일반 실행은 CI 러너 host가 고정 host가 아니므로 의도적으로 배선하지 않았다. 기록이 이름 붙인 Astra 항목 셋은 [ASTRA_DECISION_SHEETS_RS_STAGE5_KO](ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md) §4(묶음 4, 병합 #236)가 이미 모으므로 이 원장은 반복하지 않는다. `validation/2026-10-13-k-stage5-durable-tx/`, `durable/`, `scripts/stage5_local_check.py`는 여전히 main 밖이다(부재 확인). |
| `rs-4-l2` 16,384슬롯 부하 측정 host · `/workspace/kix-run/wt/rs-4-l2/DECISION_REQUIRED.md` (2026-10-15) | 「User (spend / measurement environment), with Astra for any workload change.」 | 1. 「Run on a dedicated or quiet machine/VM (may involve cost): complete record, same scripts.」 2. 「Re-run on the builder machine in a quiet window with no other load: free, unreliable.」 3. 「Accept a reduced scope (e.g. public prefix only, or private and delegated first) as the L2 record: an Astra workload decision.」 | 「Option 1, or option 2 if the User can guarantee an idle builder host for several hours. The scripts need no change.」 | `reference/rights_scale/measurement_gap.py`가 존재한다 — 병합 #230 `6f75594…`; 병합된 기록 목록에서 경로별 분모를 다시 계산하는 오프라인 보고서로, 선택지 3의 범위 질문에 들어갈 자료다. `reference/rights_scale/host_conditions.py`와 `reference/rights_scale/test_host_conditions.py`가 존재한다 — 병합 #256 `f1734e0…`, 기록 `validation/2026-10-22-rs4-load-host-conditions-recorder/README.md`; 부하 평균·MemAvailable·uptime·벽시계 간극을 기록하는 표준라이브러리 기록기로 선택지 1/2의 공유 host 조건 근거다(러너에 배선 안 됨, 역치·판정 없음). 같은 기록이 허용 부하 수준은 `UNDETERMINED`(User)로 유지한다. `validation/2026-10-15-rs-4-l2-load/README.md`는 여전히 main 밖이다(부재 확인). |
| `plan-readiness-conformance-negative-controls` CI 배선 선택지 A/B · `/workspace/kix-run/wt/plan-readiness-conformance-negative-controls/DECISION_REQUIRED.md` | 「The User/owner — either choice relaxes one clause of the node spec (AGENTS.md §3: a contradictory task document is reported, not reinterpreted).」 | A(권장) 「add one line to `readiness/test_faults.py`: `from readiness.test_conformance_sensitivity import ConformanceSensitivityTests`. The unchanged CI command then runs the suite (it becomes a `test_faults` module attribute and must also pass under it). Satisfies the objective; minimally relaxes the file-boundary acceptance bullet.」 B(구현됨) 「keep the file boundary exactly. The suite runs only when named: `python3 -m unittest integration_gate.test_http_gate readiness.test_faults readiness.test_conformance_sensitivity`. The unchanged CI command never executes the negative controls; the objective line is unmet and is documented as a gap in `readiness/CONFORMANCE.md`.」 C(기각) 「put the import in `integration_gate/test_http_gate.py` (outside `readiness/`). Letter-compliant on the `readiness/` file rule but mixes packages and still edits a module the acceptance requires to pass unchanged.」 | 「Option A. One import line satisfies the objective exactly; the alternative leaves a conformance negative-control suite that CI never runs.」 | 모순은 그대로다: `readiness/test_conformance_sensitivity.py`가 HEAD에 없다(부재 확인). `.github/workflows/protocol.yml`(244행)은 여전히 변경 없는 명령 `python3 -m unittest integration_gate.test_http_gate readiness.test_faults`를 실행한다. 선택지 B의 파일 세트(새 시험 모듈과 `readiness/CONFORMANCE.md`의 결함-사례 지도)는 main 밖에 있다. |
| `plan-readiness-receipt-audit-tests` 검사기 선행조건 · `/workspace/kix-run/wt/plan-readiness-receipt-audit-tests/DECISION_REQUIRED.md` (2026-10-21) | 「Decision owner: User/repository owner.」 (기록은 「The supervisor performs any Git/GitHub delivery.」라고 이어 적는다.) | 1. 「Recommended: the User/repository owner authorizes a separate checker-correction task, has it accepted, and revises this node's input outside the builder session.」 2. 「The User/repository owner explicitly expands this node's scope to include the checker and revises the input outside the builder session.」 | 별도의 권고 문단은 없다. 권고는 선택지 1의 표기 「Recommended:」가 담는다. | 기록이 이름 붙인 검사기 결함은 HEAD에서 고쳐졌다: 병합 #239 `9b462fd2…`의 기록 `validation/2026-10-21-readiness-checker-partial-fixture/README.md`. `scripts/check_readiness_evidence_map.py::self_test`는 이제 명시적 인용·상태·이름 붙은 간극·인식되는 담당·재계산된 개수를 가진 유효한 합성 `PARTIAL` 행을 만들어 양성 대조로 검증하고, 그 행의 담당을 지우면 소유권 진단을 요구하며, 유효한 `PARTIAL` 0개 메모리 지도에서 변이 묶음 전체를 다시 실행한다. 같은 기록은 「`plan-readiness-receipt-audit-tests` still requires owner-approved input revision outside its builder session. This prerequisite correction neither implements nor resumes that blocked node.」라고 적어, 남은 선행조건이 그 병합으로 바뀌지 않았음을 스스로 확인한다. `REC-CORE-COMMIT`과 `OBS-AUDIT`는 `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md`에서 여전히 `PARTIAL`이다(`Counts: EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9`). |
| `plan-booking-resale-admission-seeded-property` 종류 C 정지 (adopt_issued 거절 원자성) · `/workspace/kix-run/wt/plan-booking-resale-admission-seeded-property/DECISION_REQUIRED.md` | 「Astra holds the design authority and the audit for a change to the two machines; the User merges. A product policy value is not involved.」 | 1. 「Separate fix node (recommended).」 — 「A new node, new branch and new session changes `_materialize` in `resale_fsm.py` and `admission_fsm.py` to validate everything before any gate mutation, or to build on a scratch `MockGates` copy and swap it in on success, then removes the two `expectedFailure` markers. No new command, no semantic change to any accepted path. Audit floor A2.」 2. 「Accept as documented behaviour.」 — 「Record the Resale restore divergence as a known MOCK limitation in the contract, keep the `expectedFailure` tests as characterization, and merge this node as is. This weakens the restore-equality sentence.」 3. 「Drop the isolated tests from this node」 — 「and open the finding as an issue only. Loses the executable reproduction.」 | 「Option 1. This node can still merge as a test-only change with the two `expectedFailure` tests if the owner accepts a blocked-but-reported finding; they report an unexpected success once the fix lands.」 | 종류 C 발견 자체는 HEAD에서 고쳐졌다: 병합 #206 `244595db…`(별도 노드 가지 `agent/kix-plan-plan-booking-resale-adopt-issued-atomici`, 기록 `validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md`)가 `reference/booking_resale_admission/test_adopt_issued_atomicity.py`와 두 FSM(`resale_fsm.py`·`admission_fsm.py`)의 스크래치 사본 `_commit_adopt` 커밋 경로를 추가했다 — 거절된 `adopt_issued`는 게이트 변이를 남기지 않는다. 정지한 노드 자신의 시험 묶음 `reference/booking_resale_admission/test_gate_properties.py`와 그 두 `expectedFailure` 표시는 여전히 main 밖이다(부재 확인). 수정 기록은 그 묶음이 착륙하면 그 표시들이 「must be removed (they would report an unexpected success)」라고 적는다. 따라서 담당에게 열린 것은 발견의 수정이 아니라 정지한 노드 자체의 처분이다. |

## 2. 색인 — 행이 막는 것

| 열린 항목 | 담당 (기록 표기) | 막는 것 | HEAD에서 달라진 사실 한 줄 |
|---|---|---|---|
| `k-stage5-durable-tx` host | User / supervisor (build host) | 채택 backend 위 수락 실행(`durable.test_durable`), 노드 병합 | 선택지 1의 증거 준비 검사기 존재(#227)·CI `--self-test` 배선(#255); 수락 실행·프로비저닝은 없음 |
| `rs-4-l2` host | User (spend / environment); Astra (workload) | 16,384슬롯 L2 기록 완결 | 경로별 분모 보고서(#230)·host 조건 기록기(#256) 존재; 허용 부하는 `UNDETERMINED` 유지 |
| readiness 음성 대조 배선 A/B | User/owner | 음성 대조 묶음의 CI 실행 | 모순 그대로 — 시험 모듈 부재, CI 명령 무변경 |
| readiness 영수증·감사 시험 | User/repository owner | 노드 입력 개정(빌더 세션 밖) | 검사기 결함은 #239로 고쳐짐; 입력 개정 선행조건은 그 기록이 스스로 유지 |
| BRA 종류 C 정지 | Astra (설계·감사); User (병합) | 정지한 노드의 처분(권고 문장의 조건부 병합 포함) | 발견의 수정은 #206으로 병합됨; `test_gate_properties.py`·`expectedFailure` 둘은 main 밖 |

## 3. 비주장

- 이 문서는 빌더가 작성했다. Astra의 결정도, 사용자·소유자의 결정도, 어느
  담당의 회신도 아니다. 어느 노드의 상태도 바꾸지 않는다.
- 이 원장은 어느 선택지도 고르지 않고, 어떤 값도 배정하지 않고, 무엇을
  검토됨으로 표시하지 않는다. 인용한 권고·선택지는 그 출처가 적은
  비결정·미선택 상태를 그대로 둔다.
- 소유자는 이 원장을 결정으로 읽지 않고, 빌더 세션 밖에서 노드를 다시
  발동시켜야 한다. 이 원장은 어떤 노드도 재개·완료·시작하지 않는다.
- main 밖의 다섯 기록과 그 증거 기록은 위치와 이름으로만 인용하며, 그 본문을
  병합된 계약으로 읽지 않는다. 「main 이후의 저장소 사실」 칼럼의 문장은
  인용된 main 경로가 존재한다는 사실만 확인한다(검사기가 시험 본문의 의미를
  증명하지는 않는다).
- 비밀·실제 제공자 자료·외부 당사자 연락 지시를 담지 않는다.
- 두 잠금 blob과 `reference/v0.3-rc1/**`는 바꾸지 않는다. 계약·결정 기록·
  프로그램 파일·`docs/tasks/`·`.aiops/`·CI도 바꾸지 않는다.
- 실자금·실 PG/은행/KYC 호출·공개 엔드포인트·Sui testnet/mainnet·R2·자체
  복제/합의/저장 엔진·운영 런타임은 이 노드가 열지 않는다.
- 로컬 점검 결과는 `validation/2026-10-22-open-user-decisions-ledger/README.md`에
  있다. exact-head CI가 아니며 이전 SHA의 녹색을 이 문서로 옮기지 않는다.
- 이 문서는 운영 준비, 안전, 프로토콜 검증 완료를 말하지 않는다.
