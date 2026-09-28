# main 상태 정합 기록 — 2026-09-28 (hosted CI 공백 기간)

확인 기준: 2026-09-28, `origin/main` `34a722d26fa894366c26bac9de4187c598fbf3eb`(PR #72 병합).
**이 문서는 사실 기록이다. 승인·금지 범위를 새로 정하거나 바꾸지 않는다.** 승인 범위의 정본은
[DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md)이다. 아래 `DECISION_REQUIRED` 항목은 사용자 결정 전까지 열려 있다.

작성 근거는 사용자의 2026-09-28 대화 지시("현재 해야하는 것들을 전부 진행")다. `docs/tasks/`에는 이 작업의 과제 문서가 없다.
AGENTS.md §3에 따라 실행 세션이 자기 과제 문서를 만들지 않았다.

## 1. 2026-09-25~27 main 병합분

병합 시각은 병합 commit의 KST 시각이다. "근거 표시"는 PR 본문이나 병합 commit에 적힌 과제·결정 인용만 옮긴 것이며, 그 결정이 실제로 있었는지는 이 기록이 검증하지 않았다.

| PR | 병합 commit | 병합 (KST) | 내용 | 근거 표시 | main push protocol CI | PR head KTX CI |
|---|---|---|---|---|---|---|
| #58 | `19bad99` | 09-26 02:56 | Task 004 성능 측정 장치(메모리 한정) | Task 004 | 36170293685 success | 36130889407 success |
| #59 | `a281492` | 09-26 03:48 | Wave 2: Move `rights` 유상 1차 발행. 새 coin 모듈 없음 | Task 005 Wave 2 | 36175712454 success | 36171313320 success |
| #60 | `9e2dad6` | 09-26 04:13 | Wave 3: F01–F03 정산 계약·오프라인 mock | Task 005 Wave 3 | 36178376776 success | 36176909555 success |
| #61 | `4ec0f93` | 09-26 04:50 | Wave 4: 예매·리셀·검표 계약·mock gate | Task 005 Wave 4 | 36182096662 success | 36180438521 success |
| #62 | `b61e48d` | 09-26 05:15 | Wave 5: F04 여신 mock | Task 005 Wave 5 | 36184686465 success | 36183257446 success |
| #63 | `a744b0a` | 09-26 11:11 | 계약 전용 OpenAPI 핀 | "Astra decision C (2026-09-26)" | 36210889219 failure | 36210147685 failure |
| #64 | `85145eb` | 09-26 12:29 | 정산 상태기계 | 인용 없음 | 36214967861 failure | 36214072116 failure |
| #66 | `a47828d` | 09-26 13:55 | 예매·발권 상태기계 | 인용 없음 | 36219244950 failure | 36218363472 failure |
| #67 | `ef942b7` | 09-26 15:36 | 리셀 소유권 상태기계 | 인용 없음 | 36224257960 failure | 36223660801 failure |
| #68 | `8c1a4db` | 09-26 17:07 | F04 여신 노출 상태기계 | 인용 없음 | 36228847914 failure | 36228132277 failure |
| #65 | `9b8b3f8` | 09-26 17:44 | 정산 확장성·정수 잔여 배분 원칙(문서) | SETTLEMENT-EXTENSIBILITY-DOC-001, 병합 commit에 "JunTae merge approval 2026-09-26" | 36230685881 failure | 36216686353 failure |
| #69 | `5c59d95` | 09-26 18:39 | loopback HTTP 통합 관문 | 인용 없음 | 36233449817 failure | 36232757594 failure |
| #70 | `3b6bdd2` | 09-26 20:03 | 검표 자격 상태기계 | 인용 없음. 본문의 `DECISION_REQUIRED · Astra`는 카탈로그 승격 중단 표시 | 36237658946 failure | 36237006343 failure |
| #71 | `52a9b5c` | 09-26 21:42 | readiness 로컬 파일 저널, 관문 강화 | 인용 없음 | 36242759974 failure | 36241389904 failure |
| #54 | `ccd8e43` | 09-27 14:52 | Task 004 과제 문서 | — | 36298466407 failure | 미조회 |
| #57 | `fac35ff` | 09-27 14:52 | Task 005 과제 문서(Wave 1 charter) | — | 36298478095 failure | 미조회 |
| #72 | `34a722d` | 09-27 16:50 | CP-OPT-002 중앙 정책 핀 | "JunTae's explicit instruction", hosted CI 한계 수용 명시 | 36304355015 failure | 36304007336 failure |

PR 작성 계정과 병합 계정은 모두 `BeautifulMind-JT`다. GitHub 기록만으로는 사람 병합과 에이전트 병합을 구별할 수 없다.
병합 기록에 사용자 승인 문구가 있는 것은 #65와 #72뿐이다.

## 2. hosted CI 공백

- 두 workflow(KTX kernel verification, KIX protocol verification)는 2026-09-26 01:57 UTC(#63 PR head)부터 main과 PR에서 모두 2~3초 만에 `failure`로 끝난다. job 로그는 API에서 404이며 테스트 본문이 실행되지 않았다.
- 원인 기록: PR #72 본문의 "Actions quota is User-reported exhausted". 사용자는 2026-09-28에 복구 가능 시점을 2026-10-01로 알렸다.
- 마지막 main push protocol CI 성공은 `b61e48d965e7ed3f1c5f4fcd5ad863b961ce4e28`(#62), run 36184686465다. 마지막 PR head KTX 성공은 #62 head `0262dd972aa07ca36fb4394311d910b55f80738f`, run 36183257446이다.
- 이전 SHA의 성공은 승계하지 않는다. `34a722d`와 그 뒤 PR head는 hosted CI 미검증이다. AGENTS.md §10 기준으로 이 기간의 PR은 merge-ready가 아니다.
- 사용량 복구 뒤에는 당시 main HEAD와 열린 PR head의 두 workflow 결과를 확인해야 한다. 재실행은 자동으로 하지 않는다. 실행 시점과 대상은 사용자가 정한다.

2026-09-28 로컬 대체 확인 결과는 [검증 기록](../../validation/2026-09-28-main-state-catchup/README.md)에 있다. 로컬 결과는 hosted CI가 아니다.

## 3. DECISION_REQUIRED D-1 — 정본 계획과 병합분의 관계

> 2026-09-28 결정안 제출: [프로그램 결정안](../decisions/PROGRAM_DECISIONS_20260928.md). **사용자 승인(이 PR 병합 또는 명시 승인) 전까지는 이 항목이 열린 상태다.**

- [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) §1은 "첫 묶음만 착수 승인"이라고 적는다. 루트 README §4도 "현재 승인된 것은 첫 묶음의 잔여 검토·보완"이라고 적는다.
- [Task 005](../tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md)는 Astra 결정으로 Wave 2~5를 순서대로 허용하되, 각 Wave의 게이트가 열릴 때만 시작하도록 정한다.
- main에는 §1 표의 Wave 2~5 산출물과 후속 상태기계·관문·저널이 이미 있다.

이 기록은 어느 쪽 문서도 개정하지 않는다. 선택지는 다음과 같다.

1. DEVELOPMENT_PLAN을 개정해 Task 005 프로그램을 승인 범위에 넣는다.
2. 병합분을 "병합됐으나 정본 승인 밖의 참고 자산"으로 분류한다.
3. 일부를 되돌린다. 이 경우 새 과제·새 PR이 필요하다.

## 4. DECISION_REQUIRED D-2 — 착수 근거 추적

> 2026-09-28 결정안 제출: [프로그램 결정안](../decisions/PROGRAM_DECISIONS_20260928.md). **사용자 승인(이 PR 병합 또는 명시 승인) 전까지는 이 항목이 열린 상태다.**

- Task 005는 Wave 2 진입 조건을 "Task 004 draft PR 존재 + GROK_BUILD exact-HEAD 비작성자 검토 기록"으로 정한다. 저장소와 이슈 #56(2026-09-28 기준 댓글 0)에서 Wave 2~5 게이트 개방 기록을 찾지 못했다.
- Task 005 문서의 main 병합(09-27 14:52 KST)이 Wave 2~5 병합(09-26 03:48~05:15 KST)보다 늦다.
- #64·#66·#67·#68·#69·#70·#71은 Task 005 Wave 표에 이름이 없는 후속 작업이다. `docs/tasks/`에 과제 문서가 없고 PR 본문에 결정 인용도 없다.
- #69와 #71 본문은 각각 "Draft. Do not merge from this description."와 "This draft is not a merge authorization."이라고 적었다. 두 PR은 생성 후 14분·26분 만에 병합됐다.

필요한 것은 게이트 개방 또는 사후 승인 여부의 기록이다. 작성 주체는 사용자 또는 Astra다. 사실 목록은 이슈 #56에 남긴다.

## 5. DECISION_REQUIRED D-3 — readiness 파일 저널과 저장·로그 구현 금지

> 2026-09-28 결정안 제출: [프로그램 결정안](../decisions/PROGRAM_DECISIONS_20260928.md). **사용자 승인(이 PR 병합 또는 명시 승인) 전까지는 이 항목이 열린 상태다.**

사실:

- `readiness/store.py`는 스키마 1 파일 저널을 둔다. 프레임은 길이, 정규화 JSON, CRC32다. 레코드마다 `fsync`하고, 작성자 잠금은 하나다.
- 찢긴 꼬리는 버리고, 재시작 때 재생하며, 레코드·바이트 예산을 둔다.
- `--readiness-dir`를 줄 때만 켜진다. [준비 런타임 경계](../contracts/READINESS_RUNTIME.md)는 `protocolTruth=false`를 선언하고, "R2, 복제, 합의, 자체 저장 엔진"을 범위 밖으로 적는다.

규칙:

- AGENTS.md §5는 "R2, custom replication, consensus, storage-engine or log-engine implementation"을 기본 금지한다.
- DEVELOPMENT_PLAN §1은 "R2 및 자체 복제·저장·로그 구현 금지"를 유지한다.

쟁점은 프로세스 로컬 재생 래퍼가 "로그 엔진 구현"에 해당하는지다. 이 기록은 위반으로 단정하지 않고, 허용으로 간주하지도 않는다. 선택지는 다음과 같다.

1. 허용: "비운영 로컬 준비 래퍼" 예외로 정본에 적고 한도를 정한다. 복제·다중 작성자·운영 기본 활성은 금지한다.
2. 금지 해당: 새 과제로 제거하거나 비활성으로 고정한다.
3. 보류: 현 상태를 유지하고, 결정 전에는 확장하지 않는다.

결정 전 기본 자세는 3이다. 이는 AGENTS.md의 충돌 시 정지 규칙에서 나온 것이며 새 규칙이 아니다.

## 6. CI에 연결되지 않았던 검사

2026-09-28 이전 `protocol.yml`의 Python 단계는 `integration_gate.test_http_gate`와 `readiness.test_faults`(합계 33개)만 실행했다.

| 검사 | 이전 CI 상태 | 비고 |
|---|---|---|
| `reference/settlement_f01_f03` 단위 시험 20개 | 미연결 | `readiness.test_faults`가 재시작 경로에서 FSM을 간접 사용 |
| `reference/booking_resale_admission` 단위 시험 43개 | 미연결 | 같음 |
| `reference/credit_advance_f04` 단위 시험 20개 | 미연결 | 같음 |
| `scripts/check_openapi_contract.py`와 `--self-test` | 미연결 | #63 본문: "The new pin check is local. GitHub workflows were not edited." |
| `scripts/check_integration_gate_openapi.py`와 `--self-test` | 미연결 | #69·#71 본문에 로컬 실행만 기록 |
| Wave 2 Move 시험 | 연결됨 | `scripts/verify_runtime.py`의 `move-tests`, #59 main push run 36175712454 success |

이 기록과 같은 변경에서 위 다섯 줄을 `protocol.yml`의 "Offline reference state machines and OpenAPI pins" 단계로 연결했다. 그 단계의 hosted 실행 결과는 사용량 복구 전까지 없다.

## 7. 정리 후보 — 2026-09-28 사용자 지시로 처리

처음에는 목록만 남겼으나, 사용자의 2026-09-28 명시 지시("전부 그냥 해결해")로 아래와 같이 처리했다. PR을 닫아도 branch는 삭제하지 않았다. 이슈·PR은 다시 열 수 있다.

| 대상 | 처리 | 근거 |
|---|---|---|
| PR #38 `PROBE-DO-NOT-MERGE` | 병합 없이 close. branch `probe/cp-boundary-003` 유지 | 제목이 병합 금지 probe. 증거는 branch와 `validation/2026-09-23-cp-boundary-003/`에 남음 |
| PR #35 청사진 | 병합 없이 close. branch 유지 | Task 005가 "#35 implementation"을 잠금. 필요하면 다시 열 수 있음 |
| 이슈 #55 Task 004 | completed로 close | #54·#58 병합. `28c9c13` exact-head KTX `36130889407`·protocol `36130889326` success |
| 이슈 #53 CP-EXTRACT-001 진단 canary | completed로 close | 2026-09-25 CONFIRMED 기록과 NO_CHANGE 증거 댓글 |
| 이슈 #28 PR #26 적대적 검토 | not planned로 close | 대상 PR #26이 2026-09-21 병합 없이 닫힘. 후속은 Task 003-C1 PR #30(병합) |
| 이슈 #33·#37·#40 control plane | not planned로 close. **PASS 아님** | control plane은 `ai-ops-control-plane`으로 분리(#52)되고 중앙 정책 핀(#72)으로 옮겨짐. 남은 조건(실 host 증거, 운영 runner 연결, `runtime_enabled`, 형제 repo rollout)은 충족되지 않았으며, close 댓글에 그대로 옮김 |
| 이슈 #56 Task 005 | 열어 둠. Wave 체크리스트를 병합 사실대로 갱신 | Wave 6~7 미착수. D-1·D-2는 여전히 열림 |
| `docs/tasks/README.md` | Task 004·005 행을 사실대로 갱신 | 사용자 명시 지시. 과제 문서 본문은 수정하지 않음 |
| 최상위 `.gitignore` | `target/` 한 줄 추가 | 사용자 명시 지시. 추적 중인 `target/` 파일은 0개. 다른 위생 항목의 일괄 실행은 하지 않음 |

## 8. 비주장

- 병합분은 in-memory mock, 로컬 관문, 프로세스 로컬 파일 저널이다. 실 PG·은행·KYC·공연장·체인 호출, 운영 엔드포인트, backend 선택, R2는 없다.
- [원래 32개 항목](ORIGINAL_32_STATUS.md)의 라벨 31/1은 바뀌지 않았다.
- 로컬 시험 통과 수는 그 실행 한 번의 값이며, hosted CI 결과가 아니다.
- 이 기록은 운영 준비, 법적 적합성, 실자금 안전, 체인 확정을 주장하지 않는다.
