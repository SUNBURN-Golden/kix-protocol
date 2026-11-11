# 두 번째 묶음 결정 시트 — RS 프로파일의 열린 값과 stage5의 열린 Astra 항목

작업: `plan-plan-astra-decision-sheets-rs-stage5` · canonical 선행: 없음
(`depends_on: ['plan-astra-decision-sheets-listvalues-v5-rs0',
'plan-stage5-host-preflight-checker']`).
입력 정본: 이 노드의 명세와 그것이 가리키는 문서다. `.aiops/program.json`에 없는
루프 제안 노드이고 `docs/tasks/`에 과제 파일이 없으며 이슈도 없다.
읽은 기준 커밋: `e2313ab473ea1b5a7b5b9246a564749188c1c2c8`
(작업 브랜치 HEAD와 같은 로컬 `origin/main` 레퍼런스. 이 세션의 규칙이
네트워크 동작을 금지해 `git fetch`는 실행하지 않았다).

**이 문서는 아무것도 결정하지 않는다. 어느 선택지도 고르지 않는다. 아무것도 보내지
않았고, 어느 담당의 회신도 아니다.** 빌더가 작성한 시트이며 Astra 또는 사용자의
결정이 아니다. 어느 노드의 상태도 바꾸지 않는다.

선행 시트 [ASTRA_DECISION_SHEETS_KO](ASTRA_DECISION_SHEETS_KO.md)는 목록 쿼리 값,
v5 잔여 정지, RS-0 수락 문장 세 묶음을 모았다. 이 시트는 그 다음 묶음이다.
이름은 적혀 있는데 답할 준비가 된 시트가 없어 멈춰 있는 나머지 항목 —
`RIGHTS_SCALE_PROFILE.md` §13의 `IssuerCap` 선택, 시험 전용으로만 채워진 수치
픽스처의 운영 값, RS-C02 문장 2의 재분배 연산, `k-stage5-durable-tx` 기록이
이름 붙인 stage5 항목 — 을 모아, 무엇이 열려 있는지, 그 문장이 어디에 있는지,
어떤 답이 와야 다음 노드가 진행하는지만 정리한다.

## 0. 기준

- 노드 입력: `audit_floor: A2`, `astra_gate: None`, `user_merge: false`.
  루프 제안 노드이며 `.aiops/program.json`에 없다.
- 잠금 blob은 작업 전 요구값과 일치했다.
  `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
  `b607996c83a119c349f1cc90469ac1ba82764e20`. 이 노드는 두 파일을 수정하지 않는다.
- 읽은 문서: [RIGHTS_SCALE_PROFILE](../contracts/RIGHTS_SCALE_PROFILE.md) 초안
  (0.1 본문 + 0.2 RS-3a·RS-3b 편집, `:17`),
  [ADAPTER_EVENT_IDENTITY](../contracts/ADAPTER_EVENT_IDENTITY.md) 초안 0.1,
  [ADR-0001](../adr/0001-ktx-authority-commit-recovery.md),
  [RS_PREDICATE_EVIDENCE_MAP](RS_PREDICATE_EVIDENCE_MAP.md),
  [CURRENT_CAPABILITY_REGISTER](CURRENT_CAPABILITY_REGISTER.md),
  [ASTRA_DECISION_SHEETS_KO](ASTRA_DECISION_SHEETS_KO.md),
  [FIRST_BATCH_OWNER_QUESTION_SHEETS_KO](FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md),
  `reference/rights_scale/sui/sources/rights_scale.move`,
  `reference/rights_scale/test_model.py`,
  `runtime/crates/kix-delegated-exec/README.md`,
  `docs/blueprints/rights-scale-v1/README.md`,
  `validation/2026-10-14-rs-1-issuercap-probe/README.md`,
  `validation/2026-10-20-stage5-preflight/README.md`,
  [DEVELOPMENT_PLAN](../DEVELOPMENT_PLAN.md).
- 이 시트가 바꾸는 경로는 이 파일, `docs/README.md`의 위치 포인터, 그리고
  `validation/2026-10-21-astra-decision-sheets-rs-stage5/README.md`뿐이다.
  계약·결정 기록·프로그램 파일·`docs/tasks/`·`.aiops/`·`reference/v0.3-rc1/**`·
  `reference/rights_scale/**`·`runtime/**`·CI는 고치지 않는다.

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
- 항목의 일부만 닫는 부분 답변(예: 원천만 있고 별칭 규칙이 없는 답).
- 「미정」·「나중에 정한다」의 재진술.
- 이 시트 자체, 또는 이 시트를 인용한 답.

## 1. 묶음 1 — `IssuerCap` 캡 분할 선택

[RIGHTS_SCALE_PROFILE](../contracts/RIGHTS_SCALE_PROFILE.md) §13이 여는 문장
(`:250`):

> **`IssuerCap`은 OPEN이다.** 결정 시점은 `rs-1-issuercap-probe`가 끝난 뒤다.
> 그 프로브는 RS-1 다음의 별도 노드다. 선택지는 세 가지이며 0.1의 채택 값은
> 비어 있다.

선택지는 계약이 적은 그대로다 (`:252-254`):

1. cap을 페이지 또는 grant별로 나눈다.
2. 소유 객체를 쓰지 않는 권한 확인으로 바꾼다.
3. 한 cap이 만드는 처리량 천장을 수용한다.

결정 기준 (`:256`):

> 같은 `IssuerCap`을 참조로 쓰는 발행자 서명 트랜잭션 두 건을 localnet에서 동시에
> 보냈을 때 직렬화되는지. 프로브의 원시 출력 뒤에 Astra가 고른다. 그 전까지
> 연산 표의 소유 입력 열은 임시 기록이다. cap을 나눈 구성의 RS-C01 시험은
> 그 선택을 한 뒤에만 열린다.

| 항목 | 질문 | 열어 둔 계약 문장 (파일:행) | 답이 여는 것 | 기존 증거 | 담당 | 답의 형태 |
|---|---|---|---|---|---|---|
| `IssuerCap` 캡 분할 선택 | 세 선택지 중 어느 처리 방식을 채택하는가 | `RIGHTS_SCALE_PROFILE.md:250` (OPEN 문장), `:252-254` (세 선택지), `:256` (결정 기준), `:48`·`:69` (소유 입력 열은 임시 기록), `:262` (§13 표), `:258` (청사진/로드맵의 프로브 위치 불일치는 범주 B) | cap을 나눈 구성의 RS-C01 시험. 연산 표의 소유 입력 열의 임시 표기 해소 | 프로브는 끝났고 병합됐다 (PR #181, `validation/2026-10-14-rs-1-issuercap-probe/README.md`): 같은 `&IssuerCap`을 쓰는 두 발행자 서명 트랜잭션은 1-검증자 localnet에서 직렬화됐고 진 쪽은 제출 단계에서 거절됐다. 측정은 결정 기준의 입력이지 선택이 아니다. 지도도 cap 분할 시험을 주장하지 않는다 (`RS_PREDICATE_EVIDENCE_MAP.md:28`) | 프로브 뒤 Astra (`:262`) | `DECISION_REQUIRED · Astra` 결정. 고른 선택지와 그 적용 범위(어느 연산·어느 cap에 적용되는가)가 든 문장 |

기록된 사실: §13의 결정 시점으로 적힌 프로브 노드는 완료·병합됐다. 그러므로
남은 것은 측정이 아니라 Astra의 선택 한 가지다. 선택이 있기 전까지 cap 분할
구성의 RS-C01 시험은 닫힌 채로 둔다 (`:256`,
`RS_PREDICATE_EVIDENCE_MAP.md:28`). 이 시트는 세 선택지 중 어느 것도
고르지 않는다.

## 2. 묶음 2 — 시험 전용 수치 픽스처의 운영 값

`reference/rights_scale/sui/sources/rights_scale.move`의 상수는 시험 전용
픽스처다. 패키지 주석이 스스로 적는다 (`:77-80`): 「RS-2 localnet fixture
values; Astra-owned. None is a protocol value and none is an operational
default: K, the shard counts and the depth stay UNDETERMINED for mainnet
(profile sections 4 and 13).」 `LOCALNET_PAYMENT_SHARDS`도 같은 가족이며
「Not set by the owner decision: a fixture value chosen in RS-1's test matrix
(1, 2, 4, 8)」(`:75`)이다. 어느 숫자도 운영 값으로 읽지 않는다.

| 항목 | 픽스처 값 (파일:행) | 열어 둔 계약 문장 (파일:행) | 답이 여는 것 | 담당 | 답의 형태 |
|---|---|---|---|---|---|
| 노트 루트 이력 K | `LOCALNET_ROOT_HISTORY_K = 4` (`rights_scale.move:82`) | `RIGHTS_SCALE_PROFILE.md:106` (상한 5. K의 운영 값은 `DECISION_REQUIRED · Astra`. K는 UNDETERMINED), `:185` (RR-1: K는 manifest 필드, 운영 값 UNDETERMINED), `:233` (IM-17: manifest의 K 필드), `:265` (§13 표) | K의 운영 값과 그 값이 든 manifest 필드 | `DECISION_REQUIRED · Astra` (`:106`, `:185`, `:265`) | `DECISION_REQUIRED · Astra` 결정. 수치·단위(루트 개수)·적용 범위(manifest 필드, 어느 수용 규칙에 적용)가 든 문장 |
| nullifier 샤드 수 | `LOCALNET_NULLIFIER_SHARDS = 4` (`rights_scale.move:83`) | `RIGHTS_SCALE_PROFILE.md:67` (샤드 개수 S와 라우팅 해시 알고리즘은 운영 기본값 없이 RS-1의 시험 행렬에서 고른다), `:264` (§13 표: UNDETERMINED, 유일성 술어만 고정) | 운영 패키지의 nullifier 샤드 수와 라우팅 해시 알고리즘 | RS-1이 시험 행렬. 운영 값은 Astra (`:67`, `:264`) | `DECISION_REQUIRED · Astra` 결정. 샤드 수와 라우팅 해시 알고리즘, 적용 범위가 든 문장 |
| challenge 샤드 수 | `LOCALNET_CHALLENGE_SHARDS = 4` (`rights_scale.move:84`) | 위와 같은 문장 (`:67`, `:264`) | 운영 패키지의 challenge 샤드 수 | 같음 | 같은 결정 문장. 두 샤드 수를 하나의 답으로 묶을지도 그 문장이 적는다 |
| payment 샤드 수 | `LOCALNET_PAYMENT_SHARDS = 4` (`rights_scale.move:76`, 주석 `:75`) | 같은 가족의 픽스처다. `:67`의 S 문장은 nullifier·challenge 라우팅 입력을 적고, 결제 참조 바이트에서 라우팅하는 `PaymentRefShard`는 `:55`의 객체 표가 적는다 | 운영 패키지의 결제 참조 샤드 수 | 같음 | 같은 결정 문장 |
| 회로 깊이 | `ZK_DEPTH = 10` (`rights_scale.move:81`, 주석 `:77-80`: 두 트리의 깊이이자 회로 슬롯 범위 검사의 폭, 비공개 경로를 쓰는 공연의 슬롯 상한). 상한 적용은 `:368-369` | `RIGHTS_SCALE_PROFILE.md:231` (IM-15: 포함 증명 깊이는 파라미터), `:232` (IM-16: 새 회로의 ceremony 파워는 제약 수를 다시 센 뒤 RS-2가 정한다), `:233` (IM-17: manifest는 깊이를 가진다), `:35` (참조 프로파일의 깊이 4 산출물은 회귀로 유지) | 새 회로의 운영 깊이와 그 깊이가 묶는 슬롯 수 상한 | 픽스처 주석이 적은 대로 Astra (`rights_scale.move:77`). 새 회로의 파워는 RS-2 (`:232`) | `DECISION_REQUIRED · Astra` 결정. 깊이 값과 그것이 정하는 잎 용량·슬롯 범위 폭이 든 문장 |
| 묶음 상한 상수 | `MAX_BUNDLE_CHAIN = 8` (`rights_scale.move:72`, 거절 `:738`) | `RIGHTS_SCALE_PROFILE.md:107` (상한 6: 공식만 채택, 상수 UNDETERMINED, 이벤트 산술 천장 512는 상수가 아님), `:135` (공식과 천장 문장), `:161` (RS-C05), `:268` (§13 표). 지도: 「the limit 8 is a test-only localnet fixture and the numeric constant stays UNDETERMINED」(`RS_PREDICATE_EVIDENCE_MAP.md:32`) | §6 공식을 실제 호출 형태에 대입한 운영 상수와 그 상수의 전용 거절 시험 | RS-1 / Astra (`:107`, `:268`) | `DECISION_REQUIRED · Astra` 결정. 상수와 그것을 뒷받침하는 호출 형태(명령 수·입력 객체·인자·이벤트·크기 항)가 든 문장 |
| GA 페이지 카운터 상한 | 픽스처조차 없다. 커널 GA는 수량 카운터(`capacity: u32`, 청사진 `docs/blueprints/rights-scale-v1/README.md:132`)이고 체인 GA는 슬롯 범위다 (`:287`) | 계약 미정. `runtime/crates/kix-delegated-exec/README.md:35` 「The contract does not bound GA page size and this node does not choose one」, 같은 파일 `:22` (P·shard·K·W는 계약 미정) | 상한을 둘지 여부 자체 | 이름 붙은 주인 없음 — 계약 미정(AGENTS §8 범주 B). 상한은 제품 값이므로 두려면 `DECISION_REQUIRED · Astra` | 상한을 둘지, 둔다면 값·단위·적용 범위가 든 `DECISION_REQUIRED · Astra` 결정 문장 |

## 3. 묶음 3 — RS-C02 문장 2의 재분배 연산

[RIGHTS_SCALE_PROFILE](../contracts/RIGHTS_SCALE_PROFILE.md)의 RS-C02 행
(`:158`):

> GA를 겹치지 않는 익명 슬롯 범위로 둔다. 모든 전이 뒤 free+reserved+issued+
> retired의 합은 범위 크기다. **재분배는 두 페이지를 한 PTB에서 옮기고 총량을
> 유지한다.** 환불·취소·재발행 반복 뒤에도 같다.

문장 2가 요구하는 연산은 오늘 패키지에 없다. 지도는 그 행을 PARTIAL로 적는다
(`RS_PREDICATE_EVIDENCE_MAP.md:29`): 「Sentence 2 (redistribution moves two
pages in one PTB and keeps the total) has no operation and no test; the package
defines no such entry, and a test asserts that absence.」 부재를 단정하는 시험은
`reference/rights_scale/test_model.py:125`
`test_no_ga_redistribution_entry_exists_in_the_package`다. 지도는 이 갭을
기록할 뿐 닫지 않는다고 스스로 적는다 (`RS_PREDICATE_EVIDENCE_MAP.md:58`).

| 항목 | 질문 | 열어 둔 계약 문장 (파일:행) | 답이 여는 것 | 기존 증거 | 담당 | 답의 형태 |
|---|---|---|---|---|---|---|
| 재분배 연산의 존재 | 두 페이지를 한 PTB에서 옮기고 총량을 유지하는 재분배 연산(엔트리)을 둘 것인가 | `RIGHTS_SCALE_PROFILE.md:158` (RS-C02 문장 2), `RS_PREDICATE_EVIDENCE_MAP.md:29` (PARTIAL, 없음 기록), `:58` (지도는 닫지 않음) | RS-C02 문장 2의 시험 (RS-C02-T1의 재분배 절). 연산을 두기로 하면 그 엔트리의 형태 | 보존 자체는 덮인다(동일 행의 seated·GA 보존 시험들). 재분배 연산만 없다 | `RS-1; DECISION_REQUIRED · Astra` (`RS_PREDICATE_EVIDENCE_MAP.md:29`) | 재분배 엔트리를 둘지 여부의 `DECISION_REQUIRED · Astra` 결정 문장. 둔다면 새 연산은 새 프로토콜 명령이므로 그 이름·형태도 같은 결정이 정한다 |

## 4. 묶음 4 — `k-stage5-durable-tx` 기록이 이름 붙인 항목

`k-stage5-durable-tx`의 정지 기록은 저장소 밖 파일이다
(`/workspace/kix-run/state/k-stage5-durable-tx.decision.md`); 그것이 가리키는
증거 기록 `validation/2026-10-13-k-stage5-durable-tx/README.md`는 병합되지
않은 브랜치 `agent/kix-k-stage5-durable-tx`의 작업트리에 있다. 이 시트는
그 기록이 이름 붙인 항목을 저장소 밖 입력으로만 인용하고, 계약 쪽 앵커는
main의 문장으로 묶는다. 선행 시트가 rs-1 기록을 다룬 방식과 같다
(`ASTRA_DECISION_SHEETS_KO.md:111`).

기록이 적는 사실: 수락 실행의 정지는 제공 호스트이며 「the Astra decisions that
stay open are listed in the evidence record (`EventItemId` source and alias
rule; inbox policy for conflict items); they do not block the acceptance
run」이다. 호스트 확인 장치는 `plan-stage5-host-preflight-checker`가 이미 뒀다
(`scripts/check_stage5_host.py`, `validation/2026-10-20-stage5-preflight/README.md`).
아래 세 항목은 그 기록의 후속 목록이 Astra에게 남긴 것들이다.

| 항목 | 질문 | 열어 둔 계약 문장 (파일:행) | 답이 여는 것 | 기존 증거 | 담당 | 답의 형태 |
|---|---|---|---|---|---|---|
| `EventItemId`의 원천 | 커널 `event_id`로 매핑되는 항목 정체성을 제공자 안정 키(A)와 내용 주소(B) 중 무엇에서 유도하는가 | `ADAPTER_EVENT_IDENTITY.md:131` (어느 쪽도 고르지 않음), `:135` (A 권장), `:136` (B 대체), §9 `:234` (결정 요청 행) | 어댑터의 `event_id` 유도 규칙과 stage5 별칭 표의 입력 키 | TM04가 A의 전제다: 제공자 키의 불변·유일은 토스 기술이 답할 사실이고, 확인 전에는 A도 쓸 수 없다 (`:220`, `:234`). 질문서의 같은 사실 행은 보내지지 않았다 | `DECISION_REQUIRED · Astra` (`:234`). TM04는 제공자(토스)·사용자 경유 | `DECISION_REQUIRED · Astra` 결정. 원천과 그 적용 범위가 든 문장. TM04 회신이 선행 |
| 16바이트 별칭 규칙 | 16바이트 `KixId`에 외부 키를 싣는 규칙을 지속 별칭 표와 결정적 유도(SHA-256 128비트 절단 후 전체 키 대조) 중 무엇으로 하는가 | `ADAPTER_EVENT_IDENTITY.md:138` (16바이트 제약), `:142` (별칭 표 권장, 충돌 검사·표의 내구 저장은 이 초안이 만들지 않음), `:143` (결정적 유도 대체), §9 `:235` (결정 요청 행) | 별칭 저장의 형태와 충돌 검사의 위치. 표를 고르면 그 내구 저장은 5단계 계약이 묶는다 | stage5 후보는 첫 16바이트를 쓰는 시험 규칙으로 구현됐으나 저장소 밖 기록이 스스로 「local fixture rule」로 적는다 — 채택이 아니다 | `DECISION_REQUIRED · Astra` (`:235`) | `DECISION_REQUIRED · Astra` 결정. 별칭 규칙·충돌 검사 위치·schema 할당 여부가 든 문장 |
| 충돌 항목의 inbox 정책 | 보존된 충돌 항목을 커널 적용 훅에 첫 항목처럼 올릴 것인가, 어댑터가 보류할 것인가 | 계약 미정 — 범주 B. stage5 기록이 「Conflict items are offered to the apply hook like first items; whether the adapter withholds them from the kernel is the integrator's policy」로 특성만 기록했다. main의 앵커: `ADAPTER_EVENT_IDENTITY.md:160` (UNMATCHED는 계약 용어, 커널 변이 금지), `:239` (새 커널 명령·UNMATCHED enum이 필요해지면 그 역시 `DECISION_REQUIRED · Astra`), ADR-0001 `:80` (unknown/unbound/oversize는 커널 밖의 유한 inbox가 필요, 거절은 ACK·폐기의 허가가 아님), `:147-151` (inbox 보존 책임, `UnknownOperation`은 적용 보류) | 충돌 항목의 적용 경로(커널에 올리는가, inbox에 보류하는가)와 그것이 필요로 하는 명령·용어 | 충돌 증거의 보존·격리 자체는 커널이 강제한다(ADR-0001 `:80`, `:143`). 「integrator's policy」는 계약 문장이 아니라 미병합 기록의 특성 기록이다 | `DECISION_REQUIRED · Astra` (기록의 후속 목록이 적는 대로) | `DECISION_REQUIRED · Astra` 결정. 적용 훅에 올리는지 보류하는지, 보존 식별자와 ACK 조건이 든 문장 |

## 5. 색인 — 열린 항목과 그것이 막는 노드

| 항목 | 분류 (문서가 적은 대로) | 담당 | 막는 노드 | 정지를 유지하는 답변의 종류 |
|---|---|---|---|---|
| `IssuerCap` 캡 분할 선택 | OPEN. 채택 값 없음 | 프로브 뒤 Astra | cap 분할 구성의 RS-C01 시험, 연산 표 소유 입력 열의 확정 | 측정값을 선택으로 읽기, 세 선택지의 임의 채택, 미병합 권고의 재진술 |
| 노트 루트 이력 K | UNDETERMINED. manifest 필드 | `DECISION_REQUIRED · Astra` | 운영 manifest의 K 필드, RR-1의 운영 수용 규칙 | 픽스처 4를 운영 값으로 읽기 |
| nullifier·challenge·payment 샤드 수와 라우팅 해시 | UNDETERMINED. 유일성 술어만 고정 | RS-1 시험 행렬 / 운영 값 Astra | 운영 패키지의 샤드 상수 | 픽스처 4를 운영 값으로 읽기, 유일성 술어를 상수로 착각 |
| 회로 깊이 | UNDETERMINED. 파라미터 | Astra (새 회로 파워는 RS-2) | 새 회로·ceremony·manifest의 깊이 필드, 비공개 경로 공연의 슬롯 상한 | 픽스처 10을 운영 깊이로 읽기 |
| `MAX_BUNDLE_CHAIN` 상수 | 공식만 채택. 상수 UNDETERMINED | RS-1 / Astra | 운영 패키지의 묶음 상한과 RS-C05의 운영 시험 | 픽스처 8을 상수로 읽기, 천장 512를 상수로 확정 |
| GA 페이지 카운터 상한 | 계약 미정 (범주 B) | 주인 미명명; 두려면 `DECISION_REQUIRED · Astra` | 상한을 요구하는 운영·실행 경계 | 임의 상한의 발명, 커널 u32 폭을 계약 상한으로 읽기 |
| RS-C02 재분배 연산 | PARTIAL — 연산 없음 | RS-1; `DECISION_REQUIRED · Astra` | RS-C02 문장 2의 시험 | 부재 단정 시험을 존재 승인으로 읽기, 임의 연산 추가 |
| `EventItemId` 원천 | `DECISION_REQUIRED · Astra` (권장 A, TM04 선행) | Astra; TM04는 제공자·사용자 경유 | `k-stage5-durable-tx`의 채택(수락 실행 자체는 막지 않는다는 기록) | 권장 A의 채택 취급, TM04 미회신으로 A 채택 |
| 16바이트 별칭 규칙 | `DECISION_REQUIRED · Astra` (별칭 표 권장) | Astra | 같음 | 미병합 fixture 규칙의 채택 취급 |
| 충돌 항목의 inbox 정책 | 계약 미정 (범주 B) | `DECISION_REQUIRED · Astra` (기록의 후속 목록) | `k-stage5-durable-tx`의 채택 | integrator 정책을 계약으로 읽기, ACK·폐기를 거절의 허가로 읽기 |
| TM04 제공자 키 사실 | `UNDETERMINED` | 제공자(토스)·사용자 경유 | `EventItemId` 원천 A의 전제 | 질문서를 보낸 것으로 치기, 미확인을 「불변」으로 읽기 |

## 6. 비주장

- 이 문서는 빌더가 작성했다. Astra의 결정도, 사용자의 결정도, 어느 담당의
  회신도 아니다. 어느 노드의 상태도 바꾸지 않는다.
- 수치 픽스처 값, 선택지, 연산 이름, 정책을 하나도 제안하지 않는다. 인용한
  권장·선택지·후보는 그 출처가 적은 비결정·미선택 상태를 그대로 둔다.
- 저장소 밖의 stage5 정지 기록과 미병합 증거 기록은 위치와 이름으로만
  인용한다. 그 내용을 병합된 계약으로 읽지 않는다.
- 비밀, 실제 제공자 자료, 외부 당사자에게 연락하라는 지시를 담지 않는다.
  「제공자·사용자 경유」는 계약이 적은 주인의 기술이다.
- 두 잠금 blob과 `reference/v0.3-rc1/**`는 바꾸지 않는다. 계약·결정 기록·
  프로그램 파일·`docs/tasks/`·`.aiops/`·`reference/rights_scale/**`·CI도
  바꾸지 않는다.
- 로컬 점검 결과는 `validation/2026-10-21-astra-decision-sheets-rs-stage5/README.md`에
  있다. exact-head CI가 아니며 이전 SHA의 녹색을 이 문서로 옮기지 않는다.
- 이 문서는 운영 준비, 안전, 프로토콜 검증 완료를 말하지 않는다.
