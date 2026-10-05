# 확장형 권리·재고·검표 계층 — 청사진 v1 (설계 제안)

문서 버전 0.1 제안 · 작성 2026-09-29 · 상태: **설계 제안. 구현·배포·운영 활성화가 아니다.**

사용자 요청으로 개발 범위 편입이 제안된(병합 시 효력) **핵심 개발 과제**다. 선택 부가기능이 아니다.
편입의 효력과 한계는 [범위 편입 결정 기록](../../decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md)이 정한다.
이 문서는 다음 네 가지만 한다.

1. 16슬롯 가정이 어디에 있는지 **변경 영향 지도**를 만든다(§2).
2. 16을 넘는 새 프로파일의 **구조 대안을 비교하고 하나를 권고**한다(§3).
3. **필수 안전 조건**, ZK 현재성 설계 질문, **검증 규모와 측정 계획**을 정한다(§4~§7).
4. 후속 작업의 **범위·인수 조건·착수 조건**을 정의한다(§8).

제품 코드, Move, 회로, SDK, 스키마, CI는 바꾸지 않았다. 측정도 하지 않았다. 아래 숫자 중 "산술"이라고 표시한 것은
저장소 소스의 필드 타입과 고정 소스의 설정값으로 계산한 값이며 측정 결과가 아니다.

## 0. 읽는 법과 기준

| 표시 | 뜻 |
|---|---|
| **[현재]** | 이번 세션에서 저장소 파일이나 고정 소스를 직접 읽어 확인한 사실. 출처는 `파일:줄` |
| **[제안]** | 이 청사진의 설계 제안. 채택·구현 전이며 바뀔 수 있다 |
| **[해석]** | 문서와 코드를 잇는 추론. 측정이나 후속 확인 전까지 사실로 쓰지 않는다 |
| **[미확인]** | 확인하지 못했거나 이번 범위 밖. 추정으로 채우지 않았다 |
| **[비활성]** | 구현이 없거나 운영에서 꺼져 있는 상태 |

**관측 기준.**

- 관측한 `origin/main`: `ba5bd063daf87a365d4bf6f795c8940ee7fcfb17`(PR #77 병합). 작업 시작 시 작업 HEAD와 같았다. 이 값은 스냅샷이며 영구 최신값이 아니다.
- 잠금 blob 두 개(`lib.rs` `69564b16…`, `quarantine_capacity.rs` `b607996c…`)는 작업 전 요구값과 일치했다.
- **고정 Sui 기준.** `reference/v0.3-rc1/sui/Move.toml:6`의 framework rev는 `808640d9b49aecf29d8e6f46033c15eca236efa7`이다. 2026-09-29에 `git ls-remote`로 확인한 공식 태그 `mainnet-v1.79.1`이 같은 커밋을 가리킨다. 아래 프로토콜 한도는 그 rev의 Mainnet protocol 136 스냅샷 값이다. **현재 네트워크를 측정한 값이 아니며**, 이후 릴리스에서 달라질 수 있다.
- 저장소의 `docs/research/`와 `docs/DEVELOPMENT_PLAN.md` §9.1은 같은 릴리스의 소스 커밋을 `58386edc…`로 적는다. 이 값은 위와 다르다. 역사 증거와 현행 정본의 기존 문장이므로 고치지 않았고 이 문서에서는 쓰지 않는다. 불일치의 원인은 **[미확인]**이다.

**2026-10-05 보충:** 위의 미확인은 9월 29일 관측 기록이다. 현재 대조에서는 공식
릴리스 API의 `target_commitish`가 `58386edc…`, 실제 태그가 `808640d9…`로 확인됐다.
두 값은 서로 다른 Git 커밋이며 이 청사진의 고정 rev는 계속 `808640d9…`다.
[대조 기록·증거 명령](../../status/SUI_COMMIT_MISMATCH_20261005.md)은 메타데이터와 태그의 차이,
조사에 쓰인 두 파일의 동일 blob 및 확인하지 않은 범위를 설명한다. 당시 기록과 pin은 보존한다.
- **관측 이후의 이동.** 작업 중 `origin/main`이 `13134e49704815457fef444ce61d781b5a424713`(PR #78)로 이동했다. 이 문서의 줄 번호는 위 스냅샷(`ba5bd063…`) 기준이다. PR #78이 바꾼 파일 중 이 문서가 **줄 번호로** 인용한 것은 `client/setup-zk.mjs`뿐이며(IM-16·IM-17에 새 줄 번호를 함께 적었다), `.github/workflows/protocol.yml`(IM-30·§2.6), `docs/DEVELOPMENT.md`(IM-30), `zk/artifacts/README.md`(IM-16), `AGENTS.md`는 줄 번호 없이 그 서술을 인용하며 그 서술은 새 main에서도 유효하다. 잠금 blob과 CI 변경 범위 분류기의 경로 목록은 그대로다. 자동 rebase나 병합은 하지 않았다.

**보존 규칙.** `reference/v0.3-rc1/**`의 Move·회로·클라이언트·시험과 `docs/contracts/`의 기존 계약은 이 작업에서 수정하지 않았다. 역사 문서의 "16개 슬롯" 문구도 그대로 둔다.

## 1. 방향 — 16슬롯은 회귀 기준으로 보존한다

### 1.1 권고 요약 **[제안]**

1. 16슬롯 프로파일은 **작은 회귀 기준**으로 그대로 둔다. 개발계획 §12도 "기존 shared-Show Move는 회귀 자산이다"라고 적는다. 파일, 시험, 문서를 "이미 확장된 것"처럼 고쳐 쓰지 않는다.
2. 새 제품용 프로파일은 **구조를 바꿔서** 16을 넘는다. 상수 16을 더 큰 수로 바꾸는 것은 확장 설계가 아니다. §2.7이 그 반례를 산술로 보인다.
3. 권고 구조는 읽기 전용 `ShowControl` + 독립 공유 객체 `InventoryPage`(구획·GA 슬롯 범위) + 해시 라우팅 `PaymentRefShard`·`NullifierShard` + (비공개 경로) 증분 노트 트리·희소 폐기 트리다. 페이지는 고정 소스의 `derived_object`로 결정적 ID를 갖게 한다(§3.4~§3.5). 단 "판매는 페이지만 쓴다"는 서술은 ZK 규칙 RR-2를 전제한다(§3.4).
4. **위임 실행의 최소 단위는 페이지**다. 한 슬롯의 원권위는 그 슬롯을 소유한 페이지 하나이며, 온체인 직접 발행과 위임 실행이 같은 재고를 중복 소비하지 못한다(§6).
5. 검증 규모는 16 → 1,024 → 16,384 → 65,536(+복수 공연 동시) 순이다. 이 숫자는 **시험 규모 제안**이며 달성 성능, 승인된 TPS·p99, 출시 수용량, 최종 상한이 아니다(§7).

### 1.2 서로 다른 여섯 가지 상한

고정된 저장·증명 구획의 크기를 공연 전체 상한으로 오인하지 않는다.

| # | 상한 | 무엇의 한계인가 | 현행 16슬롯 프로파일 **[현재]** | 확장 프로파일에서 정하는 방식 **[제안]** | 오인 금지 |
|---|---|---|---|---|---|
| 1 | 공연 전체 정원 | 한 공연이 발행할 수 있는 권리(슬롯) 총수 | `capacity <= 16` (`rights.move:95`) | 공연 생성 때 확정하는 페이지·GA 범위의 합. 범위표는 불변 | 페이지 크기나 회로 깊이는 정원이 아니다 |
| 2 | 저장 페이지·샤드별 용량 | 한 객체가 담는 슬롯 수와 그 객체 크기 | 한 `Show`가 16칸을 고정 초기화 (`:100-103`) | 페이지 크기 P. 후보는 1(지정석별)부터 4,096까지이고 64·256·1,024는 예시다. 객체 크기 한도와 경합으로 정한다. **측정 전 미정** | 공연 상한이 아니다. 페이지 수와 곱해진다 |
| 3 | 동시에 유효한 권리 수 | ACTIVE·SHIELDED 상태의 권리 수 | 슬롯 수 이하 | 정원 이하. 환불·취소가 재고를 되돌리는 현행 규칙은 유지 | 누적 발행 수와 다르다 |
| 4 | 누적 발행·재발행 이력 | 세대 증가, `issued` 누적, 결제 참조, 이벤트 | 세대와 `issued`는 u64(`:139-141`). 결제 참조는 공연 안에 계속 쌓이고 `cancel_issuance`만 제거한다(`:171-179`) | 세대·누적은 u64 안. 결제 참조와 이력은 샤드·이벤트로 분리 | 정원을 넘을 수 있다(재발행) |
| 5 | ZK 노트·nullifier 보존량 | 노트 트리 잎 수, nullifier·challenge 집합 | 노트 16개 이하(`:299`), 트리 깊이 4 | 노트 트리 용량 ≥ 비공개 전환 가능한 권리 수 + 재발행 이력 정책. nullifier는 해시 샤드 | 회로 깊이 2^d는 **트리 하나**의 용량이다 |
| 6 | 단일 트랜잭션 처리 범위 | 한 PTB가 건드리는 객체·명령·크기 | Move에 묶음 API가 없다. PTB 한도는 §3.1 | `MAX_BUNDLE_CHAIN`. §3.1 한도에서 유도하고, 초과는 명시적으로 거절 | 위임 실행 쪽 좌석 묶음 상한 `MAX_BUNDLE = 64`(잠금 커널. GA 묶음에는 이 상한이 없다)와 별개다 |

### 1.3 프로파일 이름과 공존 규칙

- **16슬롯 참조 프로파일**: `reference/v0.3-rc1/sui`의 `kix::rights`, 회로 깊이 4 산출물, 그 클라이언트와 시험. 수정하지 않는다.
- **확장 프로파일**: 새 패키지, 새 회로, 새 manifest, 새 도메인 분리 값. 경로와 이름은 RS-0에서 정한다.
- Wave 2가 `rights`를 제자리에서 확장한 전례가 있다 (`validation/2026-09-26-wave2-rights-issuance/README.md`: `Show`·`Ticket` 필드 배치 불변). 이번 확장은 16 가정 자체를 바꾸므로 제자리 수정이 아니라 **새 프로파일**로 둘 것을 권고한다 **[제안]**.
- 두 프로파일의 증명은 서로 재사용할 수 없어야 한다(§4 RS-C11).

## 2. 변경 영향 지도

각 행의 "변경"은 **확장 프로파일에서** 필요한지를 뜻한다. 16슬롯 참조 프로파일 자체는 바꾸지 않는다.

### 2.1 Move 계약 — `reference/v0.3-rc1/sui/sources/`

| ID | 위치 | 현재의 16 가정 **[현재]** | 변경 | 보존할 의미 |
|---|---|---|---|---|
| IM-01 | `rights.move:93-108`, 특히 `:95` | `create_show`가 `capacity > 0 && capacity <= 16`을 검사 | 필요. 페이지 수·크기로 정원을 표현 | 용량 > 0, 게이트가 비어 있지 않음, bps 합 ≤ 10000 (`EPolicy`) |
| IM-02 | `:100-103` | `generations`·`occupied`를 capacity와 무관하게 16칸 초기화 | 필요. 페이지 객체로 이동 | 초기 세대 0, 미점유 |
| IM-03 | `:28-47`, `:105-107` | `Show` 하나에 재고·ZK 집합·결제 참조가 모두 있는 **단일 공유 객체** | 필요(§3). `Show`를 쓰는 함수는 `issue`, `attest_issuance`, `cancel_issuance`, `issue_paid`, `attest_payment`, `refund`, `cancel_show`, `revoke`, `shield`, `consume_private` | 읽기 전용(`&Show`)인 함수는 `offer`, `accept_gift`, `accept_sale`, `authorize_admission`, `consume` (`:193,:213,:232,:245,:252`). **이 읽기 전용성을 보존** |
| IM-04 | `:141` | `finish_issue`가 `s.issued`를 매번 증가시키는 전역 카운터 쓰기 | 필요. 페이지별 카운터, 합산은 읽을 때 | `Issuance` 이벤트의 slot·generation 필드 |
| IM-05 | `:152`, `:163`, `:175`, `:187` | `slot < s.capacity`와 `occupied[slot]` 벡터 인덱스 | 필요. (페이지, 오프셋)로 해석 | 슬롯 단일 점유. 예약된 슬롯의 직접 발급 거절(`EInventory`) |
| IM-06 | `:165`, `:188`, `:227`, `:308` | `payment_refs.contains`(중복 검사 `:165`·`:227`, 존재 확인 `:188`)와 `nullifiers.contains`·`spent_challenges.contains`(`:308`)가 **벡터 선형 검색**. 결제 참조는 `cancel_issuance` 외에는 제거되지 않음 | 필요. 해시 라우팅 테이블·샤드 | 결제 참조의 공연 내 유일성과 1차·2차 공유(`EPayment`), nullifier 재사용 거절(`EProof`) |
| IM-07 | `:111-114`, `:267-274` | `live`가 `generations[t.slot]`을 인덱스로 읽음(`:113`). `revoke`는 재고를 다시 열지 않음(`:272`) | 필요. 페이지에서 읽기 | 세대 불일치는 `EStale`. 폐기된 슬롯의 재발급 금지 |
| IM-08 | `:258-265` | `refund`가 `occupied`를 거짓으로 되돌려 재고를 다시 연다. SHIELDED는 환불 불가(`live`가 ACTIVE 요구) | 유지 | 환불 뒤 다음 세대 발급. 공연 취소 뒤에는 `live`의 `open` 검사 때문에 환불도 불가 — 관측된 특성이며 계약은 이를 정의하지 않는다 |
| IM-09 | `:276-286`, 특히 `:277` | `merkle`이 잎을 16개로 패딩하는 고정 폭. 16 초과이면서 2의 거듭제곱이 아닌 폭에서는 범위 밖 접근이 된다(예: 잎 18개 → 9개 → 범위 밖). `:299`가 잎을 16개 이하로 막아 도달하지 않음 | 필요. 증분 트리·가변 깊이 | 2-입력 Poseidon BN254 노드 해시(`:281`). 회로의 `Inclusion`과 일치해야 함 |
| IM-10 | `:287-295`, 특히 `:290` | `note_root`·`revocation_root`를 **매 호출마다 전체 상태에서 재계산**. 폐기 잎은 슬롯 i<16에 대한 H(i, generations[i], domain, 3) | 필요. 저장된 증분 루트 | 소비 시 현재 상태와 같은 루트만 수용(현행 규칙). §5에서 재설계 |
| IM-11 | `:296-303`, 특히 `:299` | `shield`가 `notes.length() < 16`을 요구 | 필요. 노트 트리 용량을 슬롯 용량과 정합 | SHIELDED 전이 뒤 공개 이전·환불·검표 불가 |
| IM-12 | `:304-318` | `consume_private`가 공연 전역 nullifier·challenge 집합을 씀 | 필요. 해시 라우팅 샤드 | 공연 취소 뒤 소비 거절(`EAuthority`), 재사용 거절, 게이트 주소에 묶인 context |
| IM-13 | `zk_gate.move:26-34` | `mint`는 공개 입력 4개(`:27`), `spend`는 6개(`:32`)를 요구 | 공개 입력에 프로파일·회로 버전이 들어가면 개수가 바뀌어 새 Verifier·키가 필요 | 호출자가 검증키를 줄 수 없음. 공연이 verifier ID를 한 번 고정(`:23` freeze, `rights.move:107`) |
| IM-28 | `rights.move:266` | `cancel_show`가 `open`을 거짓으로 바꾸는 한 줄의 쓰기 | 필요. `ShowControl`의 쓰기로 이동 | 취소 뒤 소비 거절(RS-C06). 예약 폐기는 취소 뒤에도 가능(RS-C07) |
| IM-29 | `rights.move:145-147` | `finish_issue`가 발급마다 `Issuance`와 `Change` 이벤트를 **2개** 낸다 | 이벤트 수가 인덱서 부하와 트랜잭션당 한도(`max_num_event_emit` 1024 → 한 트랜잭션에 최대 512 발급)를 정한다 | 이벤트의 slot·generation 필드. 클라이언트 재구성의 근거 |

### 2.2 회로·증명·키

| ID | 위치 | 현재의 16 가정 **[현재]** | 변경 | 보존할 의미 |
|---|---|---|---|---|
| IM-14 | `zk/circuits/mint.circom:12-13,:19` | slot `Num2Bits(4)`, generation `Num2Bits(64)`. 공개 입력 [commitment, slot, generation, domain] | 필요. slot 비트 수 = ⌈log2 슬롯 수⌉ | commitment = H(secret, slot, generation, domain, 1) 구조 |
| IM-15 | `spend.circom:15-17,:24,:38-43` | 노트·폐기 경로 배열이 `[4]`, `Inclusion(4)` 두 번. slot 4비트가 **폐기 경로 비트**를 겸함(`:42`) | 필요. 깊이 파라미터화 (`common.circom:5`의 `Inclusion(depth)`는 이미 파라미터형) | `action === 1`(검표 전용, `:23`), nullifier = H(secret, slot, generation, domain, 2), context 결합. 폐기 트리는 slot 인덱스, 노트 트리는 삽입 인덱스 |
| IM-16 | `client/setup-zk.mjs:18`(관측 main). `13134e4`에서는 `:24`(캐시를 쓰지 않는 분기 안) | `powersoftau new bn128 14` — 2^14 = 16,384 제약까지의 fixture ceremony. `13134e4`에서는 `KIX_ZK_PHASE1_PTAU`로 이전 1단계 파일을 재사용할 수 있고(`:20`) 재사용 여부와 ptau SHA-256을 manifest의 `phase1`에 기록한다(`:28`). 기록된 제약 수(깊이 4): mint 비선형 393·선형 513, spend 비선형 3,629·선형 4,167 (`validation/2026-09-11/circuit-build.log`) | 필요. 깊이별 제약 수를 다시 재고 ceremony 파워를 재결정 | 회로별 phase-2 기여 검증. 단일 당사자 fixture는 운영 ceremony가 아님(`zk/artifacts/README.md`) |
| IM-17 | `setup-zk.mjs:38`(관측 main, `13134e4`에서는 `:47`), `zk-policy.mjs:12`, `private.mjs:26` | manifest의 `depth: 4`, `manifest.depth!==4` 거절, `requirePhase2Key(key, 4\|6)` | 필요. manifest 스키마 v2(깊이·프로파일·회로 해시) | manifest hash 핀, 산출물 해시 대조(`private.mjs:16-23`), 다른 키 거절 |
| IM-18 | `rights.move:107`, `zk_gate.move:23` | 공연이 verifier를 생성 때 **한 번** 고정하고 바꾸는 함수가 없음 | 이전 정책 필요(RS-0). 진행 중인 공연은 옛 회로를 유지하는 것이 기본 | 다른 회로 버전의 증명 재사용 차단 |
| IM-27 | `client/private.mjs:31-40`, `:73-81` | `prove`가 공개 입력 배치(`CIRCUIT_PUBLIC_INPUT_LAYOUT`)와 로컬 Groth16 검증을 확인하고, `checkVerifier`가 온체인 `Verifier`의 타입·불변 소유·manifest hash·키 바이트를 클라이언트가 아는 값과 대조한다 | 필요. 새 회로의 공개 입력 개수·순서, 새 manifest, 새 Verifier ID 핀 | 호출자가 임의 키를 줄 수 없고 클라이언트가 Verifier를 핀으로 확인한다 |
| IM-30 | `.github/workflows/protocol.yml`의 job 제한 시간 | job 하나의 `timeout-minutes: 30`. `setup:zk`의 phase 1은 CI에서 약 7.5분이라고 PR #78이 `docs/DEVELOPMENT.md`에 적었다. PR #78의 phase-1 캐시 키는 `setup-zk.mjs`의 해시를 포함한다 | 큰 회로나 새 ceremony는 이 시간 예산과 캐시 키를 고려해야 한다. 새 프로파일 시험의 CI 연결은 RS-1·RS-2의 범위다 | 기존 검증 단계의 시간 예산 |

snarkjs v0.7.5 README(`snarkjs/README.md:93`)는 `powersoftau new`의 둘째 인자를 "ceremony가 받을 수 있는 최대 제약 수의 2의 거듭제곱 지수"로 설명한다(`14` → 16,384). 저장소 `client/package.json`이 같은 버전 `0.7.5`를 고정한다.

### 2.3 클라이언트 — `reference/v0.3-rc1/client/`

| ID | 위치 | 현재의 16 가정 **[현재]** | 변경 | 보존할 의미 |
|---|---|---|---|---|
| IM-19 | `private.mjs:48-54` | `pathFor`가 잎을 16개로 패딩하고 아니면 `TREE_CAPACITY` 오류. `:62`는 폐기 트리를 `show.generations` 전체로 구성 | 필요. 공개 트리 데이터로 경로 재구성. 전체 벡터 없이 | 노트 경로=삽입 인덱스, 폐기 경로=슬롯 인덱스. secret이 게이트에 전달되지 않음(`:69`) |
| IM-20 | `types.mjs:5-10` | `Ticket`·`Show`의 BCS 레이아웃을 필드 순서까지 고정해 디코드 | 필요. 새 프로파일 타입은 별도 정의 | 레거시 디코더는 회귀용으로 유지 |
| IM-21 | `independent.mjs:29` | `Show` 전체 필드를 읽어 `generations[Number(slot)]`와 대조 | 필요. 페이지 조회 | 독립 클라이언트의 현재성 검사 |
| IM-22 | `zk-regression.mjs:37`, `localnet-boundaries.mjs:9-14`, `localnet.mjs:149` | `Array(16)` 세대 배열, 용량 3 공연, 한계 문구 `'16-slot demo anonymity set'` | 확장 시험은 **별도 추가**. 기존 시험은 그대로 | 보정 nullifier·폐기 전 증명·오래된 루트·취소 뒤 검표의 거절 시험 |

### 2.4 mock·상태기계·계약 문서

| ID | 위치 | 현재의 16 가정 **[현재]** | 변경 | 보존할 의미 |
|---|---|---|---|---|
| IM-23 | `reference/booking_resale_admission/mock_gates.py:16,:128`, `reservation_fsm.py:204`, `resale_fsm.py:749`, `admission_fsm.py:613` | `CAPACITY_MAX = 16`. Move 프로토타입 상한을 그대로 복제. `GATE_ROLE_LIMIT = 16`(`mock_gates.py:17`)은 별개의 입력 길이 가드 | 새 Move 프로파일이 정해진 뒤에 **별도 상수·프로파일**로 확장 | `test_mock_gates.py:426-428`(0·17·bool 거절), `:439-442`(16 수용·중복·충돌)는 레거시 경계로 보존 |
| IM-24 | `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md:35,:107,:229` | "용량 1..16". `:107`이 "이 16은 Move 프로토타입 상한이지 상품 재고 상한이 아니다"라고 명시 | 새 프로파일 계약은 **별도 문서**(RS-0). 이 계약을 "확장됨"으로 고치지 않는다 | Wave 4 mock 술어와 SHA 앵커 |
| IM-25 | `DESIGN_SUI_ZK.md:76`, `KIX_v0.3_rc1_구현결과와_실행조건.md:85` | "16개 슬롯은 비용 측정을 시작하기 위한 제한이다", "최대 16개 슬롯의 제한 모형" | **수정하지 않는다** | 역사 증거 원문 보존 |

### 2.5 Rust 커널 — 잠금 파일, 별개의 상한

| ID | 위치 | 내용 **[현재]** | 처리 |
|---|---|---|---|
| IM-26 | `runtime/crates/kix-kernel/src/lib.rs:23-24,:183-192,:216-223,:231-239` | `MAX_SEATS = 4_096`(좌석 인덱스 u16). 좌석 묶음 상한 `MAX_BUNDLE = 64`는 `Selection::Seats` 분기(`:216-223`)에서만 검사하고 GA 분기(`:231-239`)에는 없다. GA는 `capacity: u32`. Move의 16과 **별개**인 위임 실행 쪽 상한 | 잠금 파일은 바꾸지 않는다. 4,096석을 넘는 지정석이나 64를 넘는 좌석 묶음의 위임 실행은 **새 버전 crate**(Track K 2단계 v5 경로, 별도 승인)가 필요하다 |

### 2.6 시험·증거 커버리지 — 기존 것을 먼저 매핑

16슬롯 참조 프로파일의 회귀 근거는 CI 전체 검증에 연결돼 있다 **[현재]**(`.github/workflows/protocol.yml`: `verify_runtime.py`의 Move 시험, `run_localnet.py`와 `--paid`·`--private`, `npm run test:zk`, `reference/booking_resale_admission` 단위 시험). 아래는 요구별 분류다.

| 요구·성질 | 기존 근거 | 분류 |
|---|---|---|
| 슬롯 단일 점유, 예약 슬롯의 직접 발급 거절 | `rights_tests.move`의 `reserved_slot_cannot_be_directly_issued`(abort 9) | **부분** — 예약 경로로만 발동 확인. 직접 발급 뒤 재발급 시험은 없음 |
| 환불 뒤 다음 세대 발급 | `paid_refund_frees_inventory_for_the_next_generation`. `refund`를 부르는 Move 시험은 이것 하나다 | 충분(공개 경로, 16 프로파일) |
| 공연 취소 뒤의 동작 | Move: `closed_show_cannot_reserve_primary`(`attest_issuance` 거절), `closed_show_cannot_mint_paid`(`issue_paid` 거절), `closed_show_can_drop_a_primary_reservation`(`cancel_issuance` 허용). 로컬넷: 유료 여정 `cancel-before-transfer`의 `accept_sale` 거절(`localnet-paid.mjs:69-82`), 비공개 검표 거절(`localnet-boundaries.mjs`) | **부분** — 직접 `issue`, `offer`, `authorize_admission`, `consume`, `refund`가 취소 뒤에 거절되는지는 Move 단위 시험이 없다 |
| 결제 참조 재사용 거절(1차·2차 공유) | `primary_payment_ref_cannot_be_reused`(1차→1차), `primary_ref_cannot_reuse_a_resale_ref`(2차→1차) | **부분** — 1차→2차, 2차→2차 방향은 시험이 없다 |
| 다른 공연의 cap·결제 증거 거절 | `paid_issue_rejects_cap_from_another_show`, `paid_issue_rejects_payment_from_another_show` | 충분 |
| 공개 검표 1회, 이전 보유자의 허가 불가 | Move: `independent_gate_consumes_once`, `paid_ticket_is_admitted_once_by_the_gate`(각각 소비 1회만 확인), `previous_holder_cannot_authorize_gate`. 두 번째 소비의 거절은 로컬넷 `localnet.mjs:153` | 충분(로컬넷 포함, 공개 경로). Move 단위만으로는 두 번째 소비 거절이 없다 |
| `capacity` 15/16/17 경계 (Move) | 없음. Move 시험의 `create_show` 용량 인자는 1과 2뿐이다(`rights_tests.move:14,:73,:299,:302,:319,:322`) | **미커버** — mock 층은 0·17·bool 거절과 16 수용을 시험한다(`test_mock_gates.py:426-428,:439-442`). 15는 없다 |
| 노트 상한(17번째 `shield`) | 없음 | **미커버** |
| 비공개 경로 전반 | Move 단위 시험 없음. 로컬넷 비공개 여정과 `localnet-boundaries.mjs`(용량 3, 슬롯 0..2), `zk-regression.mjs` | **부분** — 1회 시나리오, 16 프로파일 |
| 폐기 뒤 재발급 차단, 취소 뒤 비공개 검표 거절, 보정 nullifier·폐기 전 증명·오래된 루트 거절 | `localnet-boundaries.mjs` | 부분(로컬넷, 슬롯 3) |
| 겹치는 연석·묶음 | Move에 묶음 API 없음. PTB 조합 시험 없음 | **미커버** |
| GA 총량 | Move에 GA가 없다 | 해당 없음(온체인 **미구현**) |
| 다중 페이지·샤드·규모 | 없음 | **미커버** |

### 2.7 결론 — "16을 N으로 치환"이 실패하는 이유 (산술)

상수만 바꿨을 때 막히는 곳을 IM 항목에서 뽑으면 다음과 같다. 아래 값은 **산술**이다.

- **객체 크기(IM-03).** 고정 스냅샷의 `max_move_object_size`는 256,000바이트다(§3.1). `Show`에 슬롯당 들어가는 바이트는 `generations` 8 + `occupied` 1 = 9이고, 유료 발급이면 결제 참조 33(길이 접두 1 + 32)이 더해지며, 비공개 경로를 끝까지 쓰면 노트·nullifier·challenge가 각 32바이트씩 더해진다. 그래서 **직접 발급만**이면 슬롯당 9바이트로 N ≤ 28,444이고(16,384는 147,456바이트로 들어가지만 65,536은 589,824바이트로 넘친다), **유료 발급이 있으면** 42바이트로 N ≤ 6,095이며(16,384는 688,128바이트라 넘친다), **비공개 경로까지 끝까지 쓰면** 138바이트로 **N ≤ 1,855**다. 65,536은 어느 경우에도 단일 객체에 들어가지 않는다. 고정 필드와 2차 결제 참조는 무시한 값이라 실제 한도는 더 낮다.
- **루트 재계산(IM-10).** `consume_private` 한 번에 루트 재계산만으로 Poseidon 호출이 필요하다: 현행 46회(폐기 31 + 노트 15. context 해시 1회를 더하면 47회), 일반식 3N−2. N=1,024이면 3,070회, 16,384이면 49,150회, 65,536이면 196,606회. 매 검표마다 O(N)이다. 호출당 비용은 **[미확인]**이며 측정 항목이다.
- **경합(IM-03).** 쓰기 함수 10개가 모두 `Show` 하나를 쓴다. 같은 공유 객체를 쓰는 트랜잭션은 순차 실행되고 객체별 실행 용량에는 한도가 있다(§3.1의 공식 문서).
- **회로(IM-14~IM-17).** 깊이는 ⌈log2 N⌉: 1,024 → 10, 16,384 → 14, 65,536 → 16. 제약 수 증가와 ceremony 파워는 **[미확인]**이다.
- **클라이언트(IM-19~IM-21).** 전체 `Show` 벡터를 읽어 트리를 만든다. 256,000바이트에 가까운 객체를 매번 읽는다.
- **생성(IM-02).** 상수만 바꾸면 `create_show`가 벡터 초기화를 한 트랜잭션에 담는다. 그것이 크기·가스 안에 들어가는지는 **[미확인]**이다. 생성을 여러 트랜잭션으로 나눠야 하는 필연은 ③(독립 객체 분할)의 객체 수 한도에서 나온다(§3.7).

재현용 계산은 부록에 있다.

## 3. 구조 대안 비교와 권고

### 3.1 프로토콜 한도 **[현재]** — 고정 rev의 Mainnet protocol 136 스냅샷

출처: `crates/sui-protocol-config/src/snapshots/sui_protocol_config__test__Mainnet_version_136.snap`, 고정 rev의 blob `a45b246082453cb739e51bb0577bed646e4d1935`.

| 설정 | 값 | 이 문서에서의 의미 |
|---|---|---|
| `max_move_object_size` | 256000 | 한 객체(`Show`·페이지)의 크기 상한 |
| `max_programmable_tx_commands` | 1024 | 한 PTB의 명령 수. 공식 문서도 "up to 1,024 unique operations"라고 적는다 |
| `max_input_objects` | 2048 | 한 트랜잭션의 입력 객체 수. 묶음이 건드리는 페이지·티켓 수의 상한 |
| `max_tx_size_bytes` | 131072 | 트랜잭션 크기 |
| `max_num_new_move_object_ids` | 2048 | 한 트랜잭션이 만드는 객체 수. 생성 단계화의 근거 |
| `max_size_written_objects` | 5000000 | 한 트랜잭션이 쓰는 객체 총 크기 |
| `max_move_vector_len` | 262144 | 벡터 길이. 객체 크기보다 느슨하다 |
| `object_runtime_max_num_cached_objects` | 1000 | 한 트랜잭션의 런타임 객체 캐시. 소스가 "동적 필드에 영향을 준다"고 표시한 묶음에 속한다(`crates/sui-protocol-config/src/lib.rs:1606-1609`, blob `dafe686bfb708a309fcb36482f60fb1aaeb947b2`). ②와 표 기반 샤드에 관련 |
| `max_num_event_emit` | 1024 | 한 트랜잭션의 이벤트 수. 발급 하나가 이벤트를 2개 낸다(IM-29). 그래서 한 트랜잭션에 최대 512 발급 |
| `max_arguments` | 512 | 명령 하나의 인자 수 |
| `max_serialized_tx_effects_size_bytes` | 524288 | 트랜잭션 effects의 직렬화 크기 |
| `max_gas_computation_bucket` | 5000000 | 소스 주석은 "계산에 청구할 수 있는 최대치"라고 적는다(`crates/sui-protocol-config/src/lib.rs:1500-1501`). Poseidon·증명 검증 비용과의 환산은 **[미확인]** |
| `max_accumulated_txn_cost_per_object_in_mysticeti_commit` | 37000000 | 객체별·Mysticeti 커밋당 실행 비용 예산. 공유 객체가 이 한도에 닿으면 그 객체를 쓰는 트랜잭션은 이후 커밋으로 미뤄진다(`crates/sui-protocol-config/src/lib.rs:2107-2112` 주석). 비용 단위와 실제 처리량 환산은 **[미확인]** |

Poseidon의 가스 파라미터도 스냅샷에 있다(`poseidon_bn254_cost_base: 260`, `poseidon_bn254_cost_per_block: 388`, 스냅샷 `:396-397`). 단위를 실제 가스 비용으로 환산하는 것은 **[미확인]**이다.

관련 공식 문서(고정 rev의 `docs/content/`):

- `develop/transactions/ptbs/prog-txn-blocks.mdx:69`(blob `757131963bf63296cee3395158864d43d6ede2f3`): "If one transaction command fails, the entire block fails and no effects from the commands are applied." — PTB는 한 단위로 성공하거나 실패한다.
- `develop/transaction-payment/local-fee-markets.mdx`(blob `46e3b38a8dbde60f5a1cd197577a2dc73214ff2e`):
  - `:46` "if multiple transactions are all writing to the same shared object, they must execute in sequential order."
  - `:54` "Immutable shared objects do not consume any budget because multiple immutable uses of a shared object can execute in parallel."
  - `:64`, `:78` 객체별 커밋당 실행 용량에 한도가 있고 그 총량을 늘릴 방법이 없다.
  - `:72` 반복해서 지연되면 `ExecutionCancelledDueToSharedObjectCongestion`으로 취소된다.
  - `:84` "avoid using a single shared object if possible. For example, a DEX application with a single, main shared object and dynamic fields for each currency pair suffers much more congestion than one with a separate object per currency pair."
- `develop/objects/versioning.mdx`(blob `c4cfe54d4ef18ae8e99599ad4e9038ccf5d18a4c`):
  - `:87` 공유 입력은 "a flag indicating whether it is accessed mutably"로 참조하고, "Immutably referenced shared objects participate in scheduling but don't increment the object's version."
  - `:77` "Validators reject conflicting transactions that require the same mutable owned object version."
  - `:75` "If a fastpath object is frequently used by multiple senders, coordinate offchain access or use a consensus object instead."
- `develop/objects/derived-objects.mdx`(blob `34584c427260826cde67d726e18c92e01839817f`): `:50` 파생 객체는 부모의 자식이 아니다. `:54` "No parent bottleneck for unrelated keys." `:56` "1 object per `(parent, key)` without manual bookkeeping."
- 프레임워크 소스 `sources/derived_object.move`(blob `55b018503df24cfbe36cbf17bbf48a8c0778757f`): `claim(parent: &mut UID, key)`(`:38-43`)는 같은 부모·키를 두 번 claim하면 `EObjectAlreadyExists`로 중단하고(`:22`, `:41`), `derive_address`(`:54`)로 ID를 계산할 수 있다. `sources/transfer.move`(blob `756c2f78c9b6058b6acf1573aba052118669a2f5`) `:19-21`, `:113-116`: 공유 객체는 **만들어진 그 트랜잭션에서만** 공유할 수 있다(`ESharedNonNewObject`).

PTB의 공유 입력에는 가변 접근 여부 플래그가 있고(`versioning.mdx:87`, `prog-txn-blocks.mdx:199`의 "read-only shared objects (marked as not `mutable`)"), 읽기 전용 공유 참조는 스케줄링에는 참여하되 버전을 올리지 않고 혼잡 예산을 쓰지 않는다(`versioning.mdx:87`, `local-fee-markets.mdx:54`). 여기까지는 문서가 적은 **선언된 성질**이라 기능 시험으로 확인할 수 있다. Move 함수 서명의 `&T`가 그 플래그로 이어진다는 것은 **[해석]**이고, 읽기 전용 참조가 실제로 병렬성 이득을 주는 정도는 측정으로 확인한다. **소유 객체를 참조(`&`)로만 쓸 때도 같은 잠금·버전 증가가 일어나는지는 문서에서 확인하지 못했다 [미확인]**. `versioning.mdx:63`은 트랜잭션이 "건드리는" 모든 객체의 버전을 `1 + max(입력 버전)`으로 올린다고 적지만 참조 전용 소유 입력을 따로 다루지 않는다.

### 3.2 세 대안의 정의

| 대안 | 정의 |
|---|---|
| ① 큰 단일 Show·배열 유지 | 지금 구조에서 벡터 크기만 키운다. 모든 상태가 한 공유 `Show`에 있다 |
| ② Show 내부 페이지 분할 | 페이지를 `Show` 아래 동적 필드·`Table`·벡터로 둔다. 부모 `Show`가 모든 페이지 접근의 입력으로 남는다 |
| ③ 독립 객체 분할 | 재고를 페이지(구획) 단위의 **독립 공유 객체**로 나누고 GA는 슬롯 범위 샤드로 둔다. 페이지 ID는 `derived_object`로 결정한다. 취소·설정 기준은 읽기 전용 `ShowControl`이 맡는다. 페이지 크기 1이면 지정석별 객체다 |

### 3.3 비교

| 기준 | ① 단일 Show | ② Show 내부 분할 | ③ 독립 객체 분할 |
|---|---|---|---|
| 읽기·쓰기 객체 집합과 경합 지점 | 쓰기 함수 10개가 모두 `Show` 하나를 쓴다. 전부 순차(IM-03) | 동적 필드 접근은 부모 UID의 가변 접근을 요구하는 것으로 **해석**된다. 공식 문서의 `:84` 사례와 같은 유형이라 부모가 병목으로 남는다 | 판매는 해당 페이지와 결제 참조 샤드를 쓰고, 2차 결제 증거는 결제 참조 샤드만 쓴다. 환불은 해당 페이지만 쓴다. 이전·검표 허가는 `ShowControl`과 페이지를 읽고 티켓을 쓴다. `ShowControl`을 쓰는 것은 취소뿐이다(위임 회수는 `GrantControl`, §6). 경합 지점은 쓰는 페이지·샤드와 드문 `ShowControl` 쓰기다. **이 서술은 RR-2(§5.3)를 전제한다**. 연산별 집합은 §3.6 |
| 발행·검표·취소 비용 | 객체 크기·선형 검색·루트 O(N) 재계산으로 N이 크면 불가(§2.7) | 페이지 접근 비용은 줄지만 부모 쓰기 경합은 남음 | 페이지 크기 P에 비례한 비용 + 라우팅 상수. 검표는 샤드 O(1) 조회. 취소는 `ShowControl` 한 번의 쓰기 |
| 지정석·연석·GA·묶음의 원자성 | 한 객체 안에서 원자 | 같은 부모 아래에서 원자 | 여러 페이지를 **한 PTB**에 넣으면 원자(§3.1). 단 입력 객체·명령 한도 안에서. 넘는 묶음은 거절하거나 별도 계약(§4 RS-C05) |
| 전체 취소·권한 회수의 현재성 | 같은 객체의 `open`을 읽으므로 자명 | 부모의 `open`을 읽으므로 자명 | 모든 소비 함수가 **같은 `ShowControl`을 읽기 전용으로 요구**해야 한다(생략·대체 불가). 취소 쓰기와 읽기의 순서화 비용은 측정 항목 |
| 구현·검증·운영 복잡도 | 가장 낮다 | 중간 | 가장 높다: 객체 수, 생성 단계화, 조회 방법, 이전 |
| 프라이버시·증명 갱신 | 익명 집합이 최대이나, 모든 상태 변경이 루트를 바꿔 증인 갱신이 폭증(§5.2) | 같음 | 노트 트리를 전역 하나로 두면 익명 집합은 유지되나 `shield`가 한곳에 모인다. 구획별 트리는 익명 집합을 줄이고 라우팅 정보를 노출한다(§5.4). RR-2 없이는 ③에서도 발급마다 폐기 루트가 바뀌어 같은 문제가 남는다(§5.2) |

### 3.4 권고와 근거 **[제안]**

**③ 독립 객체 분할을 권고한다.** 근거는 다섯 가지이고, 전제가 하나 있다.

1. ①은 산술로 막힌다(§2.7). 직접 발급만이면 N ≤ 28,444이지만, 유료 발급이 있으면 N ≤ 6,095, 비공개 경로까지 끝까지 쓰면 N ≤ 1,855다. 65,536은 어느 경우에도 들어가지 않고 16,384는 유료 발급이 있으면 들어가지 않는다. 1,024는 최악에서도 141,312바이트라 들어가므로, ①은 **1,024 단계의 대조군**으로만 유용하다.
2. ②는 고정 rev의 공식 문서가 피하라고 한 유형(단일 공유 객체 + 동적 필드)과 같다. 동적 필드나 샤드를 추가했다는 이유만으로 부모 경합이 사라졌다고 주장하지 않는다.
3. ③은 쓰기 집합을 쓰는 페이지·샤드와 드문 `ShowControl` 쓰기로 줄인다. 현행에서도 이전·검표 허가·공개 검표는 읽기 전용이므로(`rights.move:193,213,232,245,252`) 그 성질을 그대로 계승한다.
4. ③은 위임의 최소 단위와 원권위 단위를 일치시킨다(§6).
5. 페이지 크기 1이 지정석별 객체이므로 ③은 "지정석별" 안을 포함한다. 크기는 측정으로 정하며, 이 문서는 정하지 않는다.

**전제와 결정 순서.** "판매는 페이지만 쓴다"는 서술은 RR-2(발급이 폐기 루트를 바꾸지 않음, §5.3)를 전제한다. RR-2를 채택하지 않으면 발급마다 폐기 트리의 전역 루트도 써야 하므로 전역 쓰기 지점이 남는다. 그래서 RS-0에서 RR-2의 채택 여부를 **이 구조 권고의 선행 결정**으로 다룬다.

**한계.** ③은 부모 경합이 사라진다고 주장하지 않는다. 경합 지점을 "줄인다"는 것은 쓰기 집합이 작아진다는 구조적 서술이며, 실제 경합·처리량의 개선은 측정 전이다. `ShowControl`은 모든 소비가 읽는 지점이고, 그 쓰기(취소)는 진행 중인 모든 소비와 순서화된다. 그 비용은 측정 대상이다. 또 페이지 분할은 공유 객체 경합만 나눈다. 발행자 서명 함수가 쓰는 소유 객체 `IssuerCap`의 직렬화는 별개의 문제다(§3.6).

### 3.5 권고 구조 스케치 **[제안]**

| 객체 | 공유·소유 | 주요 내용 | 쓰는 때 | 읽는 때 |
|---|---|---|---|---|
| `ShowControl` | 공유, 읽기 위주 | show id, 발행자, 프로파일 버전, `open`, `cancel_generation`, verifier ID, domain, 게이트·결제확인자 목록, 불변 범위표(페이지 크기·개수·GA 범위). **페이지 ID 목록은 담지 않는다** — 65,536개 ID는 2,097,152바이트라 256,000바이트를 넘는다. ID는 아래처럼 계산한다 | 생성 단계의 페이지 claim, `cancel_show` | 모든 소비 함수(읽기 전용, 생략 불가) |
| `InventoryPage` | 공유. ID는 `derived_object::claim(ShowControl의 UID, 페이지 번호)`로 결정한다 | 슬롯 범위 [start, end), `generations`, 점유 비트맵, 페이지별 발행 카운터, `delegated_to`(grant ID) | 그 범위의 발행·예약·환불·폐기, 위임 시작·종료 | 이전·검표 허가·현재성 확인 |
| GA 슬롯 범위 샤드 | 공유 | `InventoryPage`의 GA 모드. 구매자가 슬롯을 고르지 않는 익명 슬롯 | 그 범위의 발행·환불 | 같음 |
| `PaymentRefShard` | 공유. 결제 참조 해시로 라우팅 | 결제 참조 집합과 정준 발급 키의 사용 기록 | 판매 예약(`attest_issuance`), 2차 결제 증거(`attest_payment`), 예약 폐기(`cancel_issuance`) | 유료 발급 확인(`issue_paid`) |
| `NullifierShard` | 공유. **nullifier 해시로만** 라우팅 | nullifier 집합. challenge 집합의 라우팅과 유일성 범위는 RS-C17이 정한다 | 비공개 검표 | 없음 |
| 노트 트리 | 공유 | append-only 증분 트리의 루트·프론티어와 최근 K개 루트 이력(RR-1) | `shield` | 비공개 검표(루트 비교) |
| 폐기 트리 | 공유 | 슬롯 인덱스 **희소 트리**의 루트(RR-2·RR-6). 프론티어로는 슬롯 위치 갱신을 할 수 없다 | `revoke`(RR-2를 채택하지 않으면 발급도) | 비공개 검표(현재 루트 비교) |
| `GrantControl` | 공유. grant별 | grant 세대, 회수 cut 필드 [제안, RS-3a에서 확정] | 회수 | 위임 경로의 발급(읽기 전용) |
| `Ticket` | 공유(현행과 같음) | 슬롯, 세대, 보유자, 버전, 상태 등 | 이전·허가·검표·환불 | 각 함수 |

**페이지 정체성.** 페이지는 고정 소스의 `derived_object`로 만든다. 같은 (부모, 키)를 두 번 claim하면 중단되고(`derived_object.move:38-43`), 페이지 ID는 `derive_address(ShowControl ID, 페이지 번호)`로 클라이언트가 계산할 수 있다. 그러면 한 범위에 페이지가 둘 생겨 권위가 둘이 되는 일을 막을 수 있고 — 생성 트랜잭션의 응답이 유실된 뒤 새 바이트로 재시도해도 두 번째 claim은 중단된다 — `ShowControl`에 ID 목록을 두지 않아도 된다. 공유 객체는 만들어진 트랜잭션에서만 공유할 수 있으므로(`transfer.move:19-21`) claim·생성·공유는 한 트랜잭션에서 한다. claim은 부모를 `&mut`로 받으므로 생성 단계에서만 `ShowControl`을 쓴다. 파생 객체는 부모의 자식이 아니라서 이후 페이지 접근에 부모 쓰기가 필요 없다(`derived-objects.mdx:50`, `:54`). 봉인(seal) 전에는 `open`이 거짓이어야 한다(RS-C15).

GA를 슬롯 범위로 표현하는 이유: 비공개 경로에서 GA 티켓도 폐기 잎(슬롯 인덱스)이 필요하다. 범위가 서로 겹치지 않게 나눠지면 **총량 보존은 범위 분할의 성질**이 된다(§4 RS-C02).

### 3.6 연산별 읽기·쓰기 객체 집합

현행 열은 `rights.move`의 함수 서명에서 읽은 **[현재]** 값이고, 권고 열은 **[제안]**이다. "소유 입력"은 발신자가 소유한 객체를 인자로 받는 경우다. 모든 연산은 가스 코인도 쓴다.

| 연산 | 현행 16 프로파일: 쓰기 · 읽기 · 소유 입력 | 권고 구조(③): 쓰기 · 읽기 · 소유 입력 |
|---|---|---|
| `issue` | `Show`, 새 `Ticket` · — · `IssuerCap`(`&`) | 페이지, 새 `Ticket` · `ShowControl` · `IssuerCap` |
| `attest_issuance` | `Show`(점유·결제 참조), 새 `IssuancePayment`(발행자 소유) · — · — | 페이지, `PaymentRefShard`, 새 `IssuancePayment` · `ShowControl` · — |
| `issue_paid` | `Show`, 새 `Ticket` · — · `IssuerCap`(`&`), `IssuancePayment`(값) | 페이지, 새 `Ticket` · `ShowControl`, `PaymentRefShard` · 같음 |
| `cancel_issuance` | `Show` · — · `IssuerCap`(`&`), `IssuancePayment`(값) | 페이지, `PaymentRefShard` · `ShowControl` · 같음 |
| `offer`·`accept_gift`·`authorize_admission`·`consume` | `Ticket` · `Show`, `Clock` · — | `Ticket` · `ShowControl`, 페이지, `Clock` · — |
| `attest_payment` | `Show`(결제 참조), 새 `PaymentEvidence`(구매자 소유) · `Ticket`, `Clock` · — | `PaymentRefShard`, 새 `PaymentEvidence` · `ShowControl`, `Ticket`, 페이지, `Clock` · — |
| `accept_sale` | `Ticket` · `Show`, `Clock` · `PaymentEvidence`(값) | `Ticket` · `ShowControl`, 페이지, `Clock` · 같음 |
| `refund` | `Show`(점유 해제), `Ticket` · `Clock` · — | 페이지, `Ticket` · `ShowControl`, `Clock` · — |
| `revoke` | `Show`(세대), `Ticket` · — · `IssuerCap`(`&`) | 페이지, `Ticket`, (RR-2) 폐기 트리 · `ShowControl` · `IssuerCap` |
| `cancel_show` | `Show` · — · `IssuerCap`(`&`) | `ShowControl` · — · `IssuerCap` |
| `shield` | `Show`(노트), `Ticket` · `Verifier`(불변), `Clock` · — | 노트 트리, `Ticket` · `ShowControl`, 페이지, `Verifier`, `Clock` · — |
| `consume_private` | `Show`(nullifier·challenge) · `Verifier`, `Clock` · — (발신자는 게이트) | `NullifierShard` · `ShowControl`, 노트·폐기 트리, `Verifier`, `Clock` · — |

**소유 입력의 주의.** 발행자 서명 함수(`issue`, `issue_paid`, `cancel_issuance`, `revoke`, `cancel_show`)는 소유 객체 `IssuerCap`을 참조(`&`)로 받는다(`rights.move:104,:150,:171,:182,:266,:267`). 예약은 발행자 소유 `IssuancePayment`를 만든다(`:168-169`). 페이지 분할은 공유 객체 경합만 나눈다. 고정 소스 문서는 "변경 가능한 소유 객체 버전"을 쓰는 충돌 트랜잭션을 검증자가 거절한다고 적고(`versioning.mdx:77`), 여러 발신자가 같은 소유 객체를 자주 쓰면 오프체인에서 접근을 조정하거나 합의 객체를 쓰라고 한다(`:75`). **참조로만 쓰는 소유 객체도 같은 제약이 되는지는 확인하지 못했다 [미확인].** 그렇다면 같은 cap을 쓰는 발행자 트랜잭션은 직렬화되어 페이지 분할만으로는 병렬화되지 않는다. RS-0가 다룰 결정이다: cap을 페이지·grant별로 나누는 설계, 또는 소유 객체를 쓰지 않는 권한 확인. §7.3의 측정 항목에도 넣었다.

### 3.7 위험과 미결 **[제안]**

- **생성 단계화.** `max_num_new_move_object_ids`가 2048이다. 지정석별(P=1) 65,536개는 이 한도만으로 최소 32번의 생성 트랜잭션이 필요하고(16,384개는 8번), P=256이면 페이지 256개다. 페이지마다 `derived_object`의 `Claimed` 동적 필드도 새 ID를 쓴다면 한 트랜잭션에 만들 수 있는 페이지는 이 수의 절반 근처로 줄어든다(계수는 **[미확인]**, 측정으로 정한다). 생성이 끝나 봉인되기 전에는 `open`이 거짓이어야 한다.
- **소유 객체 `IssuerCap`의 직렬화.** §3.6. 판매 경로는 결제확인자의 `attest_issuance`와 발행자의 `issue_paid` 두 단계라서, 발행자 쪽이 한 cap과 한 키에 묶이면 처리량의 상한이 된다. 모델 1의 위임 실행이 실행자별 권한으로 이를 나눌 수 있는지는 RS-3에서 다룬다.
- **`spent_challenges`의 유일성 범위.** 현행은 공연 전체에서 challenge가 유일해야 한다(`rights.move:308`). nullifier 해시로 샤드를 나누면 유일성이 샤드 단위로 바뀐다. 이 의미 변경은 **계약 미정 특성**으로 기록하고 RS-C17이 결정한다. 샤드 안의 O(1) 조회에는 테이블(동적 필드)이 필요한데, 그것도 부모(샤드) 아래의 동적 필드라서 샤드 수 S로 분산해야 한다(§3.1의 `:84` 유형).
- **GA 샤드 편중.** 한 샤드가 매진되어도 전체에는 여유가 있을 수 있다. 재분배는 두 샤드의 원자 이동이어야 하고 총량을 보존한다.
- **GA의 체인 쪽과 커널 쪽 표현이 다르다.** 체인은 슬롯 범위(익명 슬롯)이고 커널의 GA는 수량 카운터다(`Inventory::GeneralAdmission { capacity, remaining }`, `lib.rs:175-178`). 위임된 GA 샤드에서 실행자가 빈 슬롯을 어떻게 고르는지(예: 범위 안 순차 할당)와 커널 카운터와의 대응은 정의가 없다. RS-3b 결정 항목이다.
- **조회.** 가용 좌석 지도를 읽으려면 다수 객체 조회나 인덱서가 필요하다. 인덱서의 신뢰·가용성은 **[미확인]**이다(`DESIGN_SUI_ZK.md` §2의 RPC 항목).
- **인접성.** 연석 묶음이 페이지 경계를 넘는 빈도를 줄이려면 슬롯 번호가 인접성을 보존해야 한다. 커널 v4의 좌석 구간도 "실제 연속 구간"이고(`lib.rs:171`의 `Inventory::Seats` 주석), 좌석 묶음은 한 구간 안에 있어야 한다(`:216-223`). 위임 경로에서는 구간을 넘는 묶음이 거절된다는 뜻이다. 매핑은 RS-0에서 정한다.
- **전역 노트 트리 vs 익명 집합.** §5.4.
- **클라이언트·CI.** BCS 디코더와 독립 클라이언트를 새로 써야 하고, 새 프로파일의 시험을 CI에 연결해야 한다. 이를 위한 CI 변경은 그 작업의 정당한 범위이며 "현재 작업을 통과시키려는 CI 수정"과 구분해 기록한다.

## 4. 필수 안전 조건과 검증 술어

각 조건은 확장 프로파일이 통과해야 하는 **술어**다. "현행 16 프로파일" 열은 그 조건이 지금 어디서 지켜지고 어떤 시험이 있는지 적는다.

| ID | 조건 | 현행 16 프로파일 **[현재]** | 확장 프로파일 후보 메커니즘 **[제안]** | 시험 술어 |
|---|---|---|---|---|
| RS-C01 | 같은 좌석의 중복 발행 금지 | `occupied[slot]` 검사(`rights.move:152,:163`). 예약 슬롯 경로로 시험됨 | 슬롯을 소유한 페이지가 유일한 권위. 범위표는 불변이며 겹치지 않음 | 같은 슬롯에 N개 동시 발급 중 정확히 1개 성공. 페이지 경계 양쪽 슬롯 모두. 발행자 서명 경로는 소유 객체 `IssuerCap`에서 먼저 직렬화될 수 있으므로(§3.6), 소유 객체 입력이 없는 `attest_issuance` 경로와 cap을 나눈 구성에서도 같은 술어를 시험한다 |
| RS-C02 | GA 총량 보존 | 온체인 GA 없음(**미구현**) | GA를 익명 슬롯 페이지(범위 분할)로 표현. 재분배는 두 페이지의 원자 이동 | 모든 전이 뒤 Σ(free+reserved+issued+retired) = 범위 크기. 환불·취소·재발행 반복 뒤에도 |
| RS-C03 | 중복·지연·재제출 명령의 중복 효과 방지. **(a)** 공개 경로의 명령 **(b)** 위임 실행의 안정 명령 정체성 | 유료 발급은 결제 참조 유일성(`:165`, 존재 확인 `:188`)으로, 2차 결제 증거는 `:227`로 보호된다. 직접 `issue`에는 명령 식별자가 없고 슬롯 점유가 재제출을 거절한다(`:152`). 단 `refund`가 점유를 되돌리므로(`:261`) 환불 뒤의 늦은 중복 명령은 새 발급이 될 수 있다 | (a) 정준 발급 키의 온체인 사용 기록. 슬롯 점유 자체를 키로 쓰려면 명령이 (slot, **기대 세대**)를 묶어야 한다. (b) 위임 실행의 안정 명령 정체성과 결합 | (a) 같은 명령을 **새 트랜잭션 바이트**로 다시 만들어도 권리는 1개. **환불 뒤에 같은 명령을 다시 보내도** 두 번째 권리가 생기지 않는다(기대 세대 불일치로 거절). 응답 유실 뒤 재전송은 동일 바이트이고, 회수 cut 뒤 재송신 허가가 입증되지 않으면 조회·대사만 한다(§7.2). (b)는 RS-3a·3b |
| RS-C04 | 겹치는 연석·묶음 요청의 부분 성공 금지 | 온체인 묶음 API 없음. 슬롯 단위 `issue`를 한 PTB에 여러 번 부르면 PTB 원자성(§3.1)에 의존하며 **시험은 없다** | 묶음 발급 함수(여러 페이지 포함)를 한 PTB에서 검사·소비 | `[1,2]`와 `[2,3]`이 경쟁할 때 슬롯 2는 한쪽만 소비하고 진 쪽은 아무것도 남기지 않음 |
| RS-C05 | 트랜잭션 한도를 넘는 묶음은 명시적으로 거절하거나 별도 계약 | 해당 없음 | `MAX_BUNDLE_CHAIN`을 §3.1의 입력 객체(2048)·명령(1024)·인자(512)·이벤트(발급당 2개 → 512발급)·effects 크기·트랜잭션 크기 한도에서 유도해 고정. 초과는 전용 오류 코드로 거절. **별도 계약**을 둔다면 prepare → finalize의 독립 PTB 두 단계이며 원자적이지 않다: 사이에 예약 상태가 남고, 만료와 해제 경로가 있어야 하며, 중간 상태를 정상으로 표시하고, "하나의 원자 거래"라 부르지 않는다 | 한도 −1, 한도, 한도 +1에서 각각 성공·성공·거절. 위임 경로의 좌석 묶음 상한 `MAX_BUNDLE = 64`(GA에는 없음)와의 대응표 |
| RS-C06 | 전체 공연 취소·위임 회수 뒤 옛 권한의 신규 소비 차단. **(a)** 공연 취소 **(b)** 위임 회수 | `open` 검사가 `live`(`:112`), `issue`(`:152`), `attest_issuance`(`:162`), `issue_paid`(`:186`), `consume_private`(`:306`)에 있음. Move 시험 3종(`attest_issuance`·`issue_paid`·`cancel_issuance`)과 로컬넷의 취소 뒤 `accept_sale`·비공개 검표 거절. 위임 회수는 **미구현** | (a) 모든 소비 함수가 `ShowControl`을 읽기 전용으로 요구. (b) 위임된 페이지의 **소비·해제 경로 전부**(`issue`, `attest_issuance`, `issue_paid`, `cancel_issuance`, `refund`)가 `GrantControl`의 현재성을 확인 | (a) 취소 커밋 이후 시작한 모든 소비 트랜잭션 거절. 취소 대 발급·검표 경쟁의 각 순서가 직렬 순서와 일치. (b) 회수 cut 뒤 옛 grant로 위임 페이지를 소비하는 모든 경로 거절. 위임·페이지 경계를 가로지르는 묶음도 부분 성공 없이 거절 |
| RS-C07 | 취소 전 유효했던 약정과 늦은 결제·발행 결과의 보존. **(a)** 공연 취소 **(b)** 위임 회수 | `cancel_issuance`는 공연 취소 뒤에도 가능, `issue_paid`는 거절(`EClosed`)되어 예약이 남는 상태가 존재. 공연 취소 뒤 `refund`도 불가이며 환불 의무는 체인 밖 | (a) 같은 의미를 페이지 단위로 보존. (b) 위임 회수 때 미발행 약정을 보존(모델 1의 A-4, **미구현**). 위임 시작 시점의 기존 예약(`IssuancePayment`)은 위임 전에 해소하거나, 예약이 남은 페이지는 위임하지 않는다(위임 단위가 페이지라 슬롯만 제외할 수 없다) **[미정]** | (a) 취소 뒤에도 예약 폐기는 가능, 발행은 불가. 늦은 사실은 현재 권한으로 대사. (b)는 RS-3a·3b |
| RS-C08 | 재발행 때 구 권리와 새 권리의 동시 유효성 차단 | `finish_issue`의 세대 +1(`:139-140`), `live`의 세대 비교(`:113`). 환불 뒤 재발급 시험 | 같음 | 재발행 뒤 옛 티켓의 모든 동작이 `EStale` 또는 `EClosed` |
| RS-C09 | 같은 티켓의 공개 검표와 비공개 검표 사이 이중 소비 차단 | `consume`은 ACTIVE가 필요, `shield` 뒤 SHIELDED(`:301`)이므로 공개 검표 불가. nullifier 유일 | nullifier 해시 라우팅(같은 nullifier는 항상 같은 샤드) + 상태 전이 원자성 | 공개→비공개, 비공개→공개 순서 모두에서 소비 1회 |
| RS-C10 | 공개→비공개 전환의 용량·권리 보존 | `shield`는 `occupied` 유지, SHIELDED, 노트 추가(`:299-302`). 노트 ≤ 슬롯 수 | 노트 트리 용량 ≥ 슬롯 용량(+재발행 이력 정책). SHIELDED 슬롯의 재판매·환불·재발급 금지 유지(`:316-317` 주석) | 슬롯 수만큼 `shield`한 뒤 다음 `shield`는 거절. 전환 전후 권리 수 불변 |
| RS-C11 | 서로 다른 공연·샤드·회로 버전 간 증명 재사용 차단 | `domain` = show id mod FR(`:99`), verifier 공연당 1회 고정, nullifier에 domain 포함(`spend.circom:32-35`). 로컬넷의 잘못된 verifier·바뀐 context 거절 시험 | domain에 프로파일 버전과 회로 manifest 해시를 포함. 샤드는 nullifier 해시로만 결정 | A 공연·A 버전 증명이 B 공연·B 버전·다른 샤드에서 거절 |
| RS-C12 | ZK 루트 갱신의 과거 루트 수용, 폐기 뒤 현재성, 증인 갱신, 자료 가용성 | 현재 상태와 같은 루트만 수용(`:313`). 로컬넷 시험 `staleRoot`, `oldRevoked` | §5의 후보 규칙 RR-1~RR-6 | §5.6 |
| RS-C13 | 슬롯을 라우팅 정보로 다시 노출하지 않고 익명 집합을 축소하지 않음 | 16슬롯은 비용 측정용 제한이고 한 노트만 발행된 실험은 익명성을 입증하지 못한다고 문서가 명시한다(`DESIGN_SUI_ZK.md:76`). 작은 집합에서 익명성을 주장하지 않는다(`KIX_v0.3_rc1_구현결과와_실행조건.md:85`) | §5.4의 평가와 규칙 | 관찰자가 공개 정보만으로 좁힐 수 있는 후보 수를 측정·보고 |
| RS-C14 | 공개 경로의 확장 성공을 비공개 경로에 합산하지 않음. 비공개 리셀·환불의 미구현 한계를 표시 | 비공개 리셀·환불·재발행·키 교체 **미구현**(`DESIGN_SUI_ZK.md:78`, `구현결과와_실행조건.md:85`) | 경로별로 따로 보고한다. RS-1은 공개, RS-2는 비공개, RS-3은 위임 경로의 결과를 각각 보고한다 | 보고서에 공개·비공개·위임 경로의 결과가 따로 있고, 미구현 한계가 적혀 있다 |
| RS-C15 | 페이지 정체성: 범위마다 페이지는 정확히 하나. 생성 재시도·UNKNOWN 뒤에도 | 해당 없음(`Show` 하나) | `derived_object::claim`으로 결정적 ID를 만든다(같은 부모·키의 두 번째 claim은 중단). 봉인 전에는 `open`이 거짓. 페이지 수가 범위표와 맞을 때만 봉인 | 같은 페이지 번호를 두 번 claim하면 두 번째가 중단된다. 봉인 전에는 모든 소비가 거절된다. 봉인 뒤 페이지 수 = 범위표의 페이지 수 |
| RS-C16 | 컨트롤 정합: 다른 공연의 `ShowControl`·페이지·`GrantControl`을 넣거나 생략한 소비의 거절 | 다른 공연의 cap·결제 증거는 거절된다(시험 2종). `live`는 `t.show == object::id(s)`를 확인한다(`:113`) | 모든 소비 함수가 정확한 `ShowControl` ID와 페이지 ID(계산값)를 검사한다. 호출자는 대체하거나 생략할 수 없다 | 다른 공연의 컨트롤·페이지를 넣은 호출과 옛 세대의 컨트롤을 넣은 호출이 모두 거절된다 |
| RS-C17 | challenge 유일성의 범위 | 공연 전체에서 유일하다(`:308`) | nullifier 샤드로 나누면 유일성이 샤드 단위가 되어 의미가 바뀐다. 선택지: challenge를 자기 해시로 라우팅하는 별도 집합, 또는 nullifier 샤드 안 유일성으로 충분함을 증명 | 같은 challenge를 서로 다른 nullifier로 다른 샤드에 제출했을 때의 결과가 정해진 규칙과 같다. 이 규칙은 **계약 미정 특성**이며 RS-0가 정한다 |

## 5. ZK 현재성 설계 — 루트·증인·자료 가용성

### 5.1 현행 규칙과 비용 **[현재]**

- Move는 제출자가 준 과거 루트를 믿지 않고 현재 상태에서 `note_root`·`revocation_root`를 다시 계산해 공개 입력으로 넣는다(`rights.move:313`). **현재 루트만 수용**한다.
- 그 결과 폐기 전 증명, 오래된 루트를 가진 증명은 체인이 거절한다. 로컬넷 경계 시험이 이를 확인한다(`localnet-boundaries.mjs`의 `oldRevoked`, `staleRoot`).
- 비용은 §2.7의 O(N) Poseidon 호출이고, 증인(형제 경로)은 전체 `Show` 벡터를 읽어 클라이언트가 만든다(`private.mjs:62`).

### 5.2 발견 — 발급도 폐기 루트를 바꾼다 **[현재]**

폐기 트리의 잎은 H(i, `generations[i]`, domain, 3)이고(`rights.move:291`), `finish_issue`가 발급마다 세대를 올린다(`:139-140`). 따라서 **모든 발급·환불 뒤 재발급·폐기가 폐기 루트를 바꾼다.** "현재 루트만 수용"을 규모에 그대로 옮기면, 판매나 폐기가 일어나는 동안 진행 중인 모든 비공개 검표 증명이 무효가 된다. 증명 생성과 체인 도착 사이에 시간이 걸리기 때문이다.

### 5.3 후보 규칙 **[제안 — 미검증]**

| ID | 후보 규칙 | 근거·이유 | 확인해야 할 것 |
|---|---|---|---|
| RR-1 | **노트 트리는 append-only 증분 트리**(프론티어 저장)로 두고, 노트 루트는 **최근 K개 이력**을 수용한다 | 노트 트리는 잎이 추가만 되므로, 옛 루트에 대한 포함 증명은 이후 루트에서도 사실이다. 과거 루트 수용이 안전한 쪽이다 | K의 값과 익명 집합 영향(§5.4) |
| RR-2 | **폐기 루트를 발급과 분리**한다. 폐기 트리는 슬롯 인덱스 **희소 트리**(기본값=유효)로 두어 발급이 루트를 바꾸지 않게 한다. 잎의 뜻을 "현재 세대"에서 "폐기된 최대 세대"로 바꾸고, 회로가 `generation > 폐기된 최대 세대`를 증명한다 | 현행 프로파일에서 노트는 `shield`된 티켓에만 생기고, SHIELDED 슬롯은 환불·재발급이 막혀 있다(`rights.move:299-302`, `:316-317` 주석). 그래서 노트의 세대를 바꾸는 사건은 `revoke`뿐이고, "폐기된 세대" 기록이 현행의 "현재 세대와 같다"와 같은 판정을 낸다는 것이 **[해석]**이다(증명 필요). 폐기가 드문 사건이면 루트 변경이 드물어진다. **저장 방식은 둘이다.** (a) 노드를 동적 필드로 저장하면 저장이 폐기 횟수×깊이에 비례하고 그 부모가 새 경합 지점이 된다. (b) 호출자가 형제 경로를 내고 체인은 루트만 저장하면 저장은 O(1)이고 경로는 공개 이벤트에서 재구성할 수 있지만, 같은 루트를 기준으로 만든 동시 폐기는 하나만 성공하고 나머지는 다시 만들어야 한다 | 회로 변경(비교기 추가)의 제약 수. 현행 의미와의 동치성 증명. 비공개 환불·재발행이 생길 때의 처리. 저장 방식 (a)/(b) 선택 |
| RR-3 | **폐기 루트는 현재값만 수용**(허용 창 W=0)한다. 지연 허용은 제품 정책으로 명시하고, 기본은 허용하지 않는다 | 폐기는 위험 방향으로 비단조다. 옛 폐기 루트를 받아 주면 폐기된 티켓이 창 W 동안 입장할 수 있다. 증명의 `expiresMs`가 최대 120초(`:309`)라는 점이 창의 상한 후보다 | 창을 허용할 제품상 이유가 있는가 |
| RR-4 | **증인은 공개 데이터로 재구성**한다. 사용자 백업은 (secret, slot, generation, domain, 노트 인덱스)만 담고, 경로는 항상 공개 트리 데이터에서 다시 계산한다 | 백업에 경로를 두면 갱신할 때마다 낡는다. 경로 제공자는 신뢰하지 않아도 된다(온체인 루트로 검증) | 공개 트리 데이터의 출처(이벤트·인덱서)와 보존 기간 |
| RR-5 | 노트 트리는 **전역 하나**를 기본으로 한다. nullifier는 해시 샤드, 재고 페이지는 공개 구조다 | 익명 집합을 shielded 노트 전체로 유지한다 | 전역 트리의 `shield` 경합(측정) |
| RR-6 | **폐기 트리도 전역 루트 하나**를 증명 대상으로 한다. 페이지별 하위 루트를 두더라도 증명 공개 입력에는 집계된 전역 루트만 넣는다 | 구획별 루트를 증명이 드러내면 슬롯의 구획이 새어 나간다. RR-2를 채택하면 발급은 이 루트를 쓰지 않고 `revoke`만 쓴다 | 폐기 사건 하나가 무효화하는 진행 중 증명의 비율과 재증명 지연(측정). 집계 방식이 `revoke`의 쓰기 집합(§3.6)에 미치는 영향 |

### 5.4 프라이버시 평가 항목 **[제안]**

- **익명 집합.** 루트 시점의 shielded·미사용 노트 수다. 공개 shield 기록은 보유자 주소와 노트 commitment를 이미 연결하므로(`DESIGN_SUI_ZK.md` §5), 집합은 "노트가 트리에 있다"까지만 숨긴다.
- **루트 선택의 노출.** 증명이 어느 과거 루트를 썼는지는 공개 정보다. K가 클수록 시간 분해능이 드러나 후보가 줄어든다. K는 작게 두는 것이 프라이버시에 유리하다.
- **샤드 라우팅.** nullifier를 슬롯이나 구획으로 라우팅하면 숨겨야 할 슬롯이 새어 나간다. **nullifier 해시로만** 라우팅한다(RS-C09, RS-C13).
- **구획별 트리.** 노트·폐기 트리를 구획별로 나누면 증명이 어느 구획의 루트를 썼는지 드러나 익명 집합이 그 구획으로 줄어든다. 전역 트리는 그 대신 `shield`를 한곳에 모은다. 어느 쪽이 나은지는 측정과 위협 평가로 정한다.
- **작은 집합.** 저장소 문서는 노트 하나만 발행된 실험이 익명성을 입증하지 못한다고 적고(`DESIGN_SUI_ZK.md:76`), 최대 16슬롯 모형에서 익명성이 보장된다고 주장하지 않는다고 적는다(`KIX_v0.3_rc1_구현결과와_실행조건.md:85`). 확장 후에도 일찍 `shield`한 노트의 집합은 작다.

### 5.5 회로·키·ceremony·verifier 이전 **[제안]**

- 깊이·공개 입력·프로파일 버전이 바뀌면 **새 회로, 새 phase-2, 새 Verifier 객체**가 필요하다. 진행 중인 공연은 옛 verifier에 고정된 채 끝까지 간다(IM-18). 새 공연만 새 프로파일을 쓴다.
- 현행 절차는 단일 당사자 fixture다. 다자·독립 ceremony와 회로 감사는 운영 전 조건이며 RS-2의 인수 조건이 아니다(RS-5).
- 제약 수, 증명 생성 시간·메모리, 키 크기는 **[미확인]**이며 측정 항목이다(§7.3).

### 5.6 검증해야 할 것

1. RR-1: 옛 노트 루트로 만든 증명이 K 안에서는 통과하고 K 밖에서는 거절된다.
2. RR-2: 발급·환불이 폐기 루트를 바꾸지 않는다. 폐기는 바꾼다. 폐기 전 증명은 폐기 뒤 거절된다.
3. RR-3: 폐기 커밋 뒤 도착한 폐기 전 증명이 거절된다(창 0).
4. RR-4: 이벤트·인덱서를 바꿔도 같은 증인이 재구성된다. 인덱서 없이 체인 데이터만으로 재구성되는 범위를 기록한다.
5. RR-5·RR-6: 폐기 사건당 무효화되는 증명 비율과 `shield` 경합을 측정한다.
6. 이전 프로파일·다른 공연·다른 샤드의 증명이 모두 거절된다(RS-C11).

## 6. 위임 실행과의 접점 — 원권위는 하나

**현재 [현재]:** 모델 1은 승인됐지만 실제 grant와 비협조 회수는 **미구현**이고 위임 실행은 **비활성**이다(`docs/DEVELOPMENT_PLAN.md` §12). 로컬 generation은 체인 lease generation이 아니다(`docs/decisions/AUTHORITY_MODEL_1.md`).

**규칙 [제안]:**

1. 한 슬롯의 원권위는 그 슬롯을 소유한 **페이지 하나**다. 범위표가 불변이고 겹치지 않으며 페이지 정체성이 `derived_object`로 유일하므로(RS-C15) 권위가 둘이 될 수 없다.
2. **위임의 최소 단위는 페이지(또는 GA 샤드)다.** 페이지 안의 일부 슬롯만 위임하지 않는다. 그러면 "정확한 재고 범위"가 페이지 ID 목록이 된다.
3. 위임된 페이지는 `delegated_to = Some(grant)`로 표시된다. 위임 중에는 그 페이지의 `occupied`를 바꾸는 **모든 경로**(`issue`, `attest_issuance`, `issue_paid`, `cancel_issuance`, `refund`)가 grant 현재성을 확인한 경로로만 허용되고, 온체인 직접 호출은 거절된다. 재고를 되돌리는 `refund`·`cancel_issuance`도 포함한다. 위임 시작 시점에 미해소 예약(`IssuancePayment`)이 남은 페이지는 위임하지 않는다(RS-C07).
4. **grant의 현재성은 `GrantControl` 한 곳에 둔다.** 페이지는 grant ID만 가리키고, 소비 경로는 `GrantControl`을 읽기 전용으로 확인한다. 그러면 신규 약정 차단 cut이 `GrantControl`에 대한 **한 번의 쓰기**이고 그 grant의 페이지가 많아도 원자적이다. 페이지별 위임 해제(`delegated_to = None`)는 그 뒤 검증된 미사용 잔량을 회수하는 단계이며 페이지마다 별도 쓰기다.
5. 회수 절차는 모델 1의 A-4 사실 표(`docs/decisions/AUTHORITY_MODEL_1.md:17-33`)와 LC-CUT(`docs/contracts/STATE_LIFECYCLE.md` §4)를 아래 순서로 구성한 **제안**이다. 그 문서들에는 이 다섯 단계가 순서대로 적혀 있지 않다. 회수 의사 기록 → 신규 약정 차단 cut → 체인 경계 확정 → cut 이전의 미발행 약정·늦은 capture·반환 의무 보존 → 검증된 미사용 잔량만 회수. 시간 경과만으로 전량 회수하지 않는다. cut을 증명하지 못하면 영향받는 페이지의 새 소비와 재위임을 보류한다.
6. 응답 유실·timeout·NotFound는 미실행이 아니다. 새 거래를 만들지 않고 같은 서명 바이트로 조회·대사한다. 재전송은 현재 실행 허가·fence가 확인된 경우에 한해 같은 바이트로만 하며, 회수 cut 뒤 재송신 허가가 입증되지 않으면 조회·대사만 한다(`docs/DEVELOPMENT_PLAN.md` §9.1). 로컬 참조 클라이언트는 서명 바이트와 digest를 먼저 보존하고 응답 유실을 `OUTCOME_UNKNOWN`으로 남기며 재제출에 같은 서명 바이트를 쓴다(`DESIGN_SUI_ZK.md:27`). 이것은 R2 fence의 구현이 아니다.
7. **Rust 쪽 정합 [미확인].** 잠금 v4 커널의 `Inventory::seats`는 구간 목록의 전체 좌석 수가 `MAX_SEATS = 4,096` 이내여야 하고(`lib.rs:182-202`), 좌석 묶음은 한 구간 안에서 64석 이하여야 한다(`:216-223`). 페이지를 구간 하나에, 페이지 하나를 `Inventory` 하나에 대응시킬 수 있는지, 여러 인벤토리를 한 공연에서 동시에 운용할 수 있는지는 RS-3b에서 확인한다. 이 문서는 대응이 가능하다고 주장하지 않는다.
8. **GA 정합 [미확인].** 체인의 GA는 슬롯 범위(익명 슬롯)이고 커널의 GA는 수량 카운터다(`Inventory::GeneralAdmission { capacity, remaining }`, `lib.rs:175-178`). 위임된 GA 샤드에서 실행자가 빈 슬롯을 고르는 방식과 카운터와의 대응은 정의가 없다. RS-3b가 정한다.

## 7. 검증 규모와 측정 계획 — 측정하지 않았다

### 7.1 규모 단계 **[제안]**

아래 숫자는 **시험 규모 제안**이다. 달성 성능, 승인된 TPS·p99, 출시 수용량, 최종 상한이 아니다. 기존 결과를 더 큰 규모의 결과로 전용하지 않는다.

| 단계 | 슬롯 수 | 목적 | 비고 |
|---|---|---|---|
| L0 | 16 | 기존 회귀 기준. 기존 시험 그대로 | 확장 프로파일의 결과로 세지 않는다 |
| L1 | 1,024 | 첫 확장 통합 검증 | ① 단일 객체 대조군을 함께 측정할 수 있다(산술상 최악 141,312바이트로 256,000바이트 안). 노트 트리 깊이 10 |
| L2 | 16,384 | 중간 규모 | ①은 결제 참조가 슬롯마다 있으면(42바이트/슬롯, 688,128바이트) 산술상 불가다. 직접 발급만이면 147,456바이트로 들어가지만 그 경우는 유료 판매 경로가 없는 공연이다. 잠금 v4 커널의 `MAX_SEATS = 4,096` 때문에 지정석 단일 인벤토리 위임은 불가하다. 페이지 분할·GA·새 버전 crate 중 무엇을 쓸지는 RS-3b 결정 |
| L3 | 65,536 및 복수 공연 동시 실행 | 대규모 | ①은 어느 경우에도 단일 객체에 들어가지 않는다(직접 발급만이어도 589,824바이트). 동시 공연 수는 RS-4 작업문서가 정한다. 여기서는 숫자를 제안하지 않는다 |

### 7.2 경계 사례

- 15 / 16 / 17: 16슬롯 참조 프로파일은 17을 거절하고(`EPolicy`), 확장 프로파일은 수용해야 한다. 두 프로파일의 결과를 따로 기록한다.
- 페이지·샤드 경계: P−1, P, P+1, 2P−1, 2P, 2P+1. GA 범위 경계.
- 1,023 / 1,024 / 1,025(깊이 10의 잎 한도). 확장 단계에서는 16,383/16,384/16,385, 65,535/65,536/65,537도 같은 방식으로 본다.
- 같은 좌석에 대한 동시 경쟁, 서로 다른 샤드의 동시 요청. 발행자 cap을 하나로 둔 구성과 나눈 구성을 따로 본다(§3.6).
- 취소·회수와 발권·검표의 경쟁: 네 가지 순서를 모두.
- 만석, 취소, 재발행, 반복 요청. **환불 뒤에 같은 명령을 다시 보내는 경우**(RS-C03).
- 페이지 생성 재시도: 같은 페이지 번호의 두 번째 claim, 봉인 전 소비 시도(RS-C15). 다른 공연·옛 세대의 `ShowControl`·페이지를 넣은 호출(RS-C16).
- 위임된 페이지에서 직접 `attest_issuance`·`issue_paid`·`cancel_issuance`·`refund`를 부르는 경우(RS-C06). 묶음이 위임·페이지 경계를 가로지르는 경우.
- 같은 challenge를 서로 다른 nullifier로 다른 샤드에 제출하는 경우(RS-C17).
- RPC 응답 유실과 UNKNOWN: 같은 서명 바이트로 조회·대사한다. 새 거래를 만들지 않으며, 재전송은 현재 실행 허가·fence가 확인된 경우의 같은 바이트로만 하고, 회수 cut 뒤 허가가 입증되지 않으면 조회·대사만 한다.

### 7.3 측정 항목

| 분류 | 항목 |
|---|---|
| 비용·지연 | 발권·이전·검표·취소별 가스 계산 비용과 저장 비용. 지연은 예정 도착시각 기준과 실제 서비스 시간을 분리 |
| 경합 | 공유 객체 경합과 과부하 거절. `ExecutionCancelledDueToSharedObjectCongestion` 발생 수와 지연. `ShowControl` 읽기와 취소 쓰기의 순서화 비용 |
| 저장·메모리 | 객체 바이트 대 256,000 한도, 클라이언트 트리 메모리, 인덱서 저장 |
| ZK | 깊이별 제약 수와 필요한 ptau 파워, 증명 생성 시간·메모리, 온체인 검증 비용, 루트 갱신 비용, 증인 갱신 비용, 폐기 사건당 무효화되는 진행 중 증명 비율과 재증명 지연 |
| 이벤트·인덱서 | 발급당 이벤트 2개(IM-29)와 트랜잭션당 512 발급 한도 확인, 인덱서 저장·재구성 시간, 공개 트리 데이터의 출처와 보존 |
| 생성 | 페이지 생성 트랜잭션 수와 가스, 트랜잭션당 새 객체 수(`Claimed` 동적 필드 포함), 봉인까지의 시간 |
| 소유 객체 직렬화 | 발행자 cap 하나와 나눈 cap의 처리량 비교(§3.6). 참조(`&`)로만 쓰는 소유 객체의 잠금 여부 확인 |
| CI 시간 | job 제한 시간 `timeout-minutes: 30`과 ceremony·회로 빌드·시험 시간의 합(IM-30) |
| 복구 | 재시작 뒤 상태 재구성, 미확정 거래 대사 시간, UNKNOWN 해소 |
| 환경 변수 | 같은 발신자·가스 객체의 경합 여부 |

### 7.4 측정 규칙 — [PERFORMANCE_MEASUREMENT](../../contracts/PERFORMANCE_MEASUREMENT.md)와 같은 원칙

- 신규 성공, 재시도(저장된 최초 결과 반환), 업무 거절, Capacity(예산 고갈), 충돌 보존을 **분리**한다. 빠른 거절로 성공률을 부풀리지 않는다.
- 혼합 p99를 구매 성공 지연으로 부르지 않는다.
- 저부하·균등·hot seat·재시도·포화를 구분한다. 측정 중 재생성이나 무한 예산으로 고갈을 숨기지 않는다.
- commit, toolchain, 장비, 입력, 예산, 원시 표본을 보존한다. 목표 숫자 없는 결과는 **탐색 자료**이며 SLO나 수용량이 아니다.
- 공개·비공개·위임 경로의 결과를 합산하지 않는다.
- 이번 작업에서는 계획만 썼다. 어떤 것도 실행하지 않았다.

## 8. 후속 작업 분해

**이 표는 작업문서가 아니며 dispatch 대상이 아니다.** 작업문서는 승인된 orchestrator가 작성자 세션 밖에서 확정한다.
작업 하나에 새 branch, 새 세션, 새 PR을 쓴다(`AGENTS.md` §2). 구현 작업은 이번 세션에서 착수하지 않았다.

| ID | 이름 | 성격 | 선행 |
|---|---|---|---|
| RS-0 | 객체·재고 권위 설계 | 문서 | 이 범위 편입의 병합 |
| RS-1 | 공개 경로 확장 | Move·reference·시험 | RS-0 |
| RS-2 | 비공개 증명 확장 | 회로·Move·클라이언트 | RS-1, RS-0의 RR 채택 |
| RS-3a | 온체인 위임 원시 | Move | RS-1 |
| RS-3b | Rust 위임 실행 통합 | Rust | RS-3a, **Track K** 2단계 v5 결정 |
| RS-4 | 단계별 부하 검증 | 측정 | 해당 단계 경로의 RS-1·RS-2(위임은 RS-3) |
| RS-5 | 운영 채택 판단 | 결정 | RS-1~RS-4, [프로그램 결정](../../decisions/PROGRAM_DECISIONS_20260928.md) §5의 조건 |

### 8.1 안전 조건의 작업 배정 **[제안 — RS-0가 확정]**

한 술어가 공연 취소(공개 경로)와 위임 회수에 걸쳐 있으면 (a)·(b)로 나눠 배정한다. 위임 몫은 RS-3a·RS-3b 전에는 시험할 수 없다.

| 경로 | 술어 | 담당 |
|---|---|---|
| 공개 | RS-C01, RS-C02(온체인 GA를 RS-0가 포함하기로 한 경우), RS-C03(a), RS-C04, RS-C05, RS-C06(a), RS-C07(a), RS-C08, RS-C15, RS-C16, RS-C14의 공개 몫 | RS-1 |
| 비공개 | RS-C09, RS-C10, RS-C11, RS-C12, RS-C13, RS-C17, RS-C14의 비공개 몫 | RS-2 |
| 위임 | RS-C03(b), RS-C06(b), RS-C07(b), RS-C14의 위임 몫 | Move 술어는 RS-3a, 실행자 통합과 안정 명령 정체성은 RS-3b |

### RS-0 — 객체·재고 권위 설계

| 항목 | 내용 |
|---|---|
| 목적·범위 | 분할 모델(페이지·GA 슬롯 범위·`ShowControl`·샤드), 페이지 크기 P(위임의 granularity를 함께 정한다), 슬롯 식별 체계와 인접성 매핑, 위임 최소 단위와 `GrantControl`, 프로파일 버전·공존·이전 규칙, ZK 루트 규칙(RR) 채택안(RR-2가 구조 권고의 선행 결정), 발행자 cap의 직렬화 대책, `MAX_BUNDLE_CHAIN`, 공연 생성 단계화와 페이지 정체성, challenge 유일성 범위, 측정 계획 확정 |
| 선행 조건 | 이 PR의 병합 |
| 변경 대상 | 문서만. 새 계약 초안(가칭 `docs/contracts/RIGHTS_SCALE_PROFILE.md`, 초안 0.1)과 결정 문서. `docs/contracts/`는 CI가 전체 검증을 도는 경로다 |
| 인수 조건 | RS-C01~C17 각각에 술어·시험 ID·담당 작업 배정(§8.1의 제안을 확정). §1.2의 여섯 상한 각각의 값 결정 방법. IM-01~IM-30 각각의 처리 방침. RR-2를 채택하면 현행 판정과의 동치 증명 계획과 폐기 트리 저장 방식 (a)/(b)의 선택. 대안 재검토 결과. 비작성자 검토. exact-head CI |
| 필요한 증거 | 고정 소스 인용(blob), 산술 재현, 검토 기록 |
| 착수 조건 | orchestrator의 작업문서와 게이트 기록(Track P). 새 승인은 필요 없다 |
| 문서 확정 조건 | 결정 문서를 확정하기 전에 Astra 아키텍처 검토를 받고, 사용자가 권고 구조를 수락하거나 대안을 택한다(결정 기록 §6.2 D-D). 새 패키지·새 회로를 프로그램 결정 §2.1의 "`rights`·`zk_gate` 확장" 범위로 읽는 해석은 Astra가 "경계 안"으로 판정했고(결정 기록 §6.2 D-D), 그 조건 (a) coin/TIX·새 경제자산 모듈 불포함, (b) 16슬롯 참조 프로파일 불변, (c) localnet 한정, (d) RS-3b는 §2.1이 아니라 Track K 2단계 v5의 별도 승인, (e) 2단계(종결·회수·GC) 미포함을 RS-0 확정 전에 명시 기록한다. 착수 조건이 아니라 **확정 조건**이다 |
| 운영 활성화 조건 | 없음(문서) |

### RS-1 — 공개 경로 확장

| 항목 | 내용 |
|---|---|
| 목적·범위 | 공개 경로(발급·이전·검표 허가·환불·취소)를 확장 프로파일로 구현하고 1,024 규모로 통합 검증한다. `reference/`의 in-memory 모델, 새 Move 프로파일, localnet 시험, 15/16/17과 페이지 경계 시험 |
| 선행 조건 | RS-0 수용 |
| 변경 대상 | 새 Move 패키지·모듈(경로는 RS-0에서 확정). 대응하는 영향 지도 항목은 IM-01~IM-08, IM-20·IM-21(공개 경로 디코더), IM-23·IM-24(mock·계약 문서의 별도 프로파일), IM-28, IM-29. **`reference/v0.3-rc1/sui`는 수정하지 않는다**. 새 시험, 그 시험의 CI 연결 |
| 인수 조건 | §8.1의 공개 경로 술어 통과. 16슬롯 참조 프로파일의 Move 시험 19개와 비공개 여정·zk 회귀가 그대로 통과. 계약-구현 불일치 분류 보고. L1 탐색 측정(공개 경로). **초기 확인 시험:** 같은 `IssuerCap`을 참조(`&`)로 쓰는 발행자 서명 트랜잭션 2건을 localnet에서 동시에 보내 소유 객체 잠금 여부를 확정한다. RS-0의 cap 처리 결정은 이 결과가 나오기 전에는 잠정이다 |
| 필요한 증거 | 실행한 명령과 실제 결과, exact-head CI, 측정 원시자료(탐색 표시) |
| 착수 조건 | 작업문서와 게이트 기록. Sui framework 고정 rev 변경 없음(바꾸려면 별도 결정) |
| 운영 활성화 조건 | localnet 한정. testnet·mainnet은 프로그램 결정 §5의 조건 |

### RS-2 — 비공개 증명 확장

| 항목 | 내용 |
|---|---|
| 목적·범위 | 회로 깊이·트리 구조, RR 규칙, 새 Verifier·manifest v2, 클라이언트 증인 재구성, 새 fixture ceremony 절차, 비공개 경로 시험. 증명 생성기와 Verifier 핀의 결합(IM-27), CI 시간 예산과 phase-1 캐시(IM-30) |
| 선행 조건 | RS-1(분할 구조), RS-0의 RR 채택 |
| 변경 대상 | 새 회로 파일(기존 circom 미변경), 새 Move 비공개 경로. 대응하는 영향 지도 항목은 IM-09~IM-19, IM-22, IM-27, IM-30. 새 클라이언트 모듈, 시험 |
| 인수 조건 | §8.1의 비공개 경로 술어 통과. 폐기 전 증명·오래된 루트·다른 샤드·다른 버전 증명의 거절. 증인 갱신 시험. 깊이별 제약 수와 ptau 파워 기록. 프라이버시 평가 문서화. "fixture ceremony는 운영 ceremony가 아니다" 표시 |
| 필요한 증거 | 회로 빌드 로그, 시험 결과, 측정 원시자료 |
| 착수 조건 | 작업문서와 게이트 기록 |
| 운영 활성화 조건 | localnet 한정. 독립 회로 감사와 다자 ceremony는 RS-5의 조건 |

### RS-3a / RS-3b — 위임·취소·복구 통합

| 항목 | 3a: 온체인 위임 원시 | 3b: Rust 위임 실행 통합 |
|---|---|---|
| 목적·범위 | 페이지 단위 grant, `GrantControl`의 현재성과 회수 cut 필드, 위임 중 페이지의 모든 소비·해제 경로 차단(§6 규칙 3·4) | Rust 위임 실행과의 통합. 페이지와 커널 인벤토리의 대응, GA 카운터 대응, 좌석 묶음 상한과의 정합(§6 규칙 7·8) |
| 범위 한정 | "회수 cut"은 **온체인 grant 무효화와 페이지 소비 차단**에 한정한다. 커널의 종결·회수·해제·색인(`AGENTS.md` §5의 lifecycle 항목, Track K 2단계)을 구현하지 않는다. 그 범위로 읽히는 부분이 생기면 Track K 승인이 먼저다 | 같음 |
| 선행 조건 | RS-1 | 3a, **Track K 2단계 v5 설계 결정·승인**, 모델 1 grant 구현 계획 |
| 변경 대상 | Move·시험 | 잠금 파일을 건드리지 않는 새 버전 crate(IM-26) |
| 인수 조건 | §8.1의 위임 몫 중 Move 술어. 직접 호출과 위임 호출이 같은 페이지를 중복 소비하지 못함(`issue`뿐 아니라 `attest_issuance`·`issue_paid`·`cancel_issuance`·`refund` 포함). 회수 cut 뒤 옛 grant의 신규 소비 차단. 위임 시작 시 미해소 예약이 있는 페이지의 처리 | §8.1의 위임 몫 중 실행자 통합. 위임 실행의 안정 명령 정체성, 늦은 결과·미발행 약정 보존, UNKNOWN에서 같은 바이트 조회·대사(허가가 있는 경우에만 재전송) |
| 필요한 증거 | 경쟁·회수 시험 결과, 독립 검토 | 경쟁·회수·응답 유실 시험 결과, 독립 검토 |
| 착수 조건 | 게이트 기록 | **Track K의 별도 승인**이며 자체 R2 금지는 유지 |
| 운영 활성화 조건 | "위임 실행 비활성 유지"(`DEVELOPMENT_PLAN.md` §12)의 해제는 별도 결정 | 같음 |

### RS-4 — 단계별 부하 검증

| 항목 | 내용 |
|---|---|
| 목적·범위 | L1→L2→L3 순서로 §7의 경계 사례와 측정 항목을 실행한다. 경로별로 나눈다: 공개 경로는 RS-1 뒤, 비공개 경로의 ZK 항목은 RS-2 뒤, 위임 경로는 RS-3 뒤에만 잰다 |
| 선행 조건 | 해당 단계 경로의 구현. 측정 계획 승인(목표 숫자 없이 탐색으로 하거나 승인된 목표를 쓴다) |
| 변경 대상 | 측정 하네스와 자료. 제품 코드 변경 없음 |
| 인수 조건 | 실행한 경로에 해당하는 §7.3 항목 전부를 원시자료와 함께 보고하고, 실행하지 않은 경로는 **미측정**으로 적는다. 결과에 "탐색 자료" 표시. 작은 규모 결과를 큰 규모 결과로 전용하지 않음. UNKNOWN 대사 포함 |
| 필요한 증거 | commit·toolchain·장비·입력·예산이 묶인 원시 표본 |
| 착수 조건 | 작업문서와 측정 환경 결정 |
| 운영 활성화 조건 | 없음. 출시 수용량은 별도 결정 |

### RS-5 — 운영 채택 판단

| 항목 | 내용 |
|---|---|
| 목적·범위 | testnet·mainnet 배포 여부, 키 관리, 독립 Move·회로 감사, 다자 ceremony, 운영 책임자 지정을 **판단**한다. 배포 실행 자체가 아니다 |
| 선행 조건 | RS-1~RS-4의 결과. 프로그램 결정 §5: 키 관리 결정 문서, Move 독립 감사, testnet 운용 증거, 운영 책임자 |
| 변경 대상 | 결정 문서. 코드 변경 없음 |
| 인수 조건 | 사용자의 명시 승인과 결정 문서 |
| 필요한 증거 | 감사 보고서, testnet 운용 기록, 키 관리 결정 문서, RS-4의 원시 측정 자료 |
| 착수 조건 | 별도 결정. 자동 진행 없음 |
| 운영 활성화 조건 | 착수 조건과 **별개**의 명시 승인. 활성화는 이 작업의 산출물이 아니다 |

## 9. 다른 트랙과의 관계

- **[자체 토큰 계층](../optional-native-token-v1/README.md)(TL)과는 서로의 선행조건이 아니다.** 한쪽이 늦어져도 다른 쪽은 진행할 수 있다. 접점은 세 가지뿐이다: 같은 Sui 고정 rev를 쓴다, 보상이 티켓 사건을 참조할 때는 온체인 의존 없이 안정 operation ID로 오프체인에서 잇는다, 토큰 관리 권한과 `IssuerCap`·결제확인자·검표자 권한을 분리한다.
- **Track K.** RS-3b만 Track K에 의존한다. 진행 중이거나 예정된 첫 묶음 잔여 작업, 4단계 backend 비교 준비, Track P의 Wave 6 골격은 이 문서 때문에 중단하거나 순서를 바꾸지 않는다.
- **원래 32개 항목.** 표의 라벨과 31/1 집계는 바꾸지 않았다. 관련 행은 연결만 한다: P01·P02·P03·B01·B02·R05·E02.

## 10. 비주장·잔여 불확실성·열린 질문

**비주장.**

- 이 문서는 확장 프로파일이 구현되었거나 동작한다고 주장하지 않는다.
- 16슬롯 참조 프로파일을 "이미 확장됨"으로 고쳐 쓰지 않았다.
- 산술 값은 측정이 아니다. ③이 쓰기 집합을 줄인다는 것은 **구조적 서술**이며, 경합 감소·비용·지연·처리량·수용량의 개선은 주장하지 않는다. 그것은 측정 뒤의 일이다.
- 고정 스냅샷의 한도는 현재 네트워크의 값이 아닐 수 있다.
- 위임 실행, 비협조 회수, 비공개 리셀·환불, 운영 ceremony는 미구현 또는 비활성이다.
- 프라이버시 평가는 위협 모델이 아직 없다. 익명성을 주장하지 않는다.
- 이 청사진의 저자 측 점검은 독립 검토가 아니다.

**잔여 불확실성 [미확인].** 페이지 크기 P, Poseidon·증명·검증 비용, 깊이별 제약 수, Move `&Show`의 병렬 실행 정도, 참조(`&`)로만 쓰는 소유 객체의 잠금 여부, 혼잡 예산 설정의 비용 단위와 처리량 환산, 인덱서·이벤트 보존, `docs/research/`와 개발계획 §9.1의 릴리스 커밋 표기 불일치 원인, 페이지와 커널 인벤토리의 대응, GA 슬롯 선택 방식.

**RS-0가 답할 열린 질문.**

1. 정원은 **봉인 때 고정**이 전제다(RS-C01·RS-C15, 불변 범위표). 봉인 뒤 페이지를 추가하려면 범위표 불변 전제를 바꿔야 하므로, 그런 요구가 있는지와 있다면 어떤 규칙으로 하는지를 정한다.
2. 슬롯 번호를 어떻게 매겨 인접성을 보존하는가. 구획·행·열과 커널 구간의 대응.
3. 노트 트리를 전역 하나로 둘 때 `shield` 경합을 어떻게 다루는가(일괄 삽입 등).
4. **RR-2의 회로 변경을 채택하는가**, 현행 의미를 유지하는가. 이 결정이 구조 권고(③)의 선행 조건이다(§3.4).
5. 폐기 허용 창 W를 0으로 고정하는가.
6. 진행 중인 16슬롯 공연을 새 프로파일로 옮기는 경로가 필요한가(권고: 필요 없음).
7. 위임의 최소 단위를 페이지로 고정하는 것이 운영상 충분한가. `GrantControl`을 grant별로 두는 설계로 충분한가. 페이지 크기 P가 위임의 granularity를 함께 정하므로 P와 같이 결정한다.
8. 발행자 서명 함수의 소유 객체 `IssuerCap` 직렬화를 어떻게 다루는가(cap 분할, 소유 객체를 쓰지 않는 권한 확인, 또는 처리량 상한으로 수용).
9. challenge 유일성의 범위(RS-C17)와 폐기 트리의 저장 방식(RR-2의 (a)/(b)).
10. 온체인 GA를 첫 확장 프로파일에 포함하는가, 포함한다면 슬롯 선택과 커널 카운터의 대응(§6 규칙 8).

## 11. 출처

**저장소(관측 main `ba5bd063…`).** `AGENTS.md`, `docs/DEVELOPMENT_PLAN.md`, `docs/decisions/{AUTHORITY_MODEL_1,PROGRAM_DECISIONS_20260928}.md`, `docs/contracts/{STATE_LIFECYCLE,BOOKING_RESALE_ADMISSION_GATES,PERFORMANCE_MEASUREMENT}.md`, `reference/v0.3-rc1/sui/sources/{rights,zk_gate}.move`, `sui/tests/rights_tests.move`, `sui/Move.toml`, `zk/circuits/{common,mint,spend}.circom`, `zk/artifacts/README.md`, `client/{private,types,independent,setup-zk,zk-policy,zk-regression,localnet,localnet-paid,localnet-boundaries}.mjs`, `client/package.json`, `DESIGN_SUI_ZK.md`, `KIX_v0.3_rc1_구현결과와_실행조건.md`, `validation/2026-09-11/circuit-build.log`, `validation/2026-09-26-wave2-rights-issuance/README.md`, `reference/booking_resale_admission/`, `runtime/crates/kix-kernel/src/lib.rs`(읽기만), `.github/workflows/protocol.yml`, `toolchains.json`.

**관측 이후 main(`13134e49…`, PR #78).** `client/setup-zk.mjs`의 줄 이동과 `phase1` 필드, `docs/DEVELOPMENT.md`의 phase-1 소요 시간 설명(IM-16·IM-17·IM-30). 이 문서는 그 파일을 읽기만 했다.

**고정 Sui 소스**(`github.com/MystenLabs/sui`, rev `808640d9b49aecf29d8e6f46033c15eca236efa7` = 태그 `mainnet-v1.79.1`, 2026-09-29 확인):
[스냅샷](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/crates/sui-protocol-config/src/snapshots/sui_protocol_config__test__Mainnet_version_136.snap),
[protocol config `lib.rs`](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/crates/sui-protocol-config/src/lib.rs)(blob `dafe686bfb708a309fcb36482f60fb1aaeb947b2`),
[PTB 문서](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/docs/content/develop/transactions/ptbs/prog-txn-blocks.mdx),
[local fee markets 문서](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/docs/content/develop/transaction-payment/local-fee-markets.mdx),
[versioning 문서](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/docs/content/develop/objects/versioning.mdx),
[derived objects 문서](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/docs/content/develop/objects/derived-objects.mdx),
[`derived_object.move`](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/crates/sui-framework/packages/sui-framework/sources/derived_object.move),
[`transfer.move`](https://github.com/MystenLabs/sui/blob/808640d9b49aecf29d8e6f46033c15eca236efa7/crates/sui-framework/packages/sui-framework/sources/transfer.move).

**snarkjs.** [`v0.7.5` README](https://github.com/iden3/snarkjs/blob/v0.7.5/README.md) `:93`.

**역사 참고(닫힌 미병합 제안, 현행 승인 아님).** [PR #35](https://github.com/BeautifulMind-JT/kix-protocol/pull/35)의 head `ea8b19ea533ebb9622900b0ca3bffe3f6405ac4b`, [`SUI_TOKENIZATION.md`](https://github.com/BeautifulMind-JT/kix-protocol/blob/ea8b19ea533ebb9622900b0ca3bffe3f6405ac4b/docs/blueprints/platform-settlement-credit-v1/SUI_TOKENIZATION.md)(blob `1a529d036d2d7f33eb17f4c143b16a3213f26973`). 좌석별 재고 객체, GA 할당량 샤드, 읽기 전용 `ShowControl`, "canonical issuance key" 개념을 그 문서에서 참고했다. 이 청사진은 그것을 채택하거나 되살리지 않고, 위의 근거로 다시 비교했다.

## 부록 — 산술 재현

```python
LIMIT = 256000                       # max_move_object_size (protocol 136 snapshot)
gen, occ, ref, sec = 8, 1, 33, 32    # bytes per slot: generations, occupied, payment ref, each ZK vector entry
direct_only = gen + occ              # 9: direct issue only, no payment refs
pub_only    = direct_only + ref      # 42: + one payment ref per slot
worst       = pub_only + 3 * sec     # 138: + notes + nullifiers + spent_challenges
print(LIMIT // direct_only, LIMIT // pub_only, LIMIT // worst)
for n in (1024, 16384, 65536):
    print(n, direct_only * n, pub_only * n, worst * n, 3 * n - 2)   # bytes (direct), bytes (public), bytes (worst), Poseidon calls per consume_private
print(-(-65536 // 2048), -(-16384 // 2048))                          # min creation txs for per-slot objects: 32 8
```

출력: `28444 6095 1855`, `1024 9216 43008 141312 3070`, `16384 147456 688128 2260992 49150`, `65536 589824 2752512 9043968 196606`, `32 8`.
현행 16슬롯의 Poseidon 호출 수는 폐기 트리 16(잎, 4-입력)+15(노드)와 노트 트리 15(노드)로 46이고, context 해시 1회가 더해진다.
