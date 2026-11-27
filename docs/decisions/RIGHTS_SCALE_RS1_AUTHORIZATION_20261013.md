# RS-1 착수 권한 기록 — 초안 0.1 기준 구현 (2026-10-13)

상태: **owner 결정 기록.** 작성자는 owner delegate다. 이 기록은 구현 착수의 권한만 적는다. `docs/contracts/RIGHTS_SCALE_PROFILE.md` 0.1의 상태 줄은 바꾸지 않으며, 그 문서는 Astra가 RS-1 ARCHITECTURE 게이트에서 서명할 때까지 "초안"으로 남는다. RS-0 결정 기록(`RIGHTS_SCALE_RS0_DECISION_20261008.md`)도 같은 검토를 기다린다.

## 1. 선택

**Option 2.** RS-1은 병합된 초안이 커밋 `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1`에 있는 그대로의 상태에 대해 공개 경로를 구현한다. 프로파일 0.1과 RS-0 결정 기록에 대한 Astra 아키텍처 검토는 선행 조건이 아니라 RS-1 게이트에서 일어난다. 이 문장이 Option 2가 요구한 명시적 User 승인이다.

## 2. 범위

`issue`, `seal`, 페이지 claim, bundle, `revoke`, `cancel_show`를 프로파일 §3 표가 읽는 그대로 구현한다. localnet만. 참조 모델과 시험을 포함한다.

열린 항목의 RS-1 해석:

- **GA 재분배(RS-C02 둘째 문장):** 구현하지 않는다. 새 §3 연산도 없다. `DECISION_REQUIRED · Astra`로 남는다. 패키지에 재분배 진입점이 없음을 확인하는 부정 시험을 둔다.
- **CI 연결:** builder가 `.github/workflows`에 `rights-scale` 잡을 추가해 새 Move 시험과 localnet driver를 `main` 향 pull request에서 돌린다. 필수 검사다.
- **localnet 상수(프로토콜 값 아님; mainnet 값은 `UNDETERMINED · Astra`):** `profile_version = 1`, `MAX_BUNDLE_CHAIN = 8`, `P = 1,024` 슬롯/공연, `S = 64` 슬롯/페이지. 라우팅 해시 = `blake2b256(show_id || page_index || profile_version)`. 한 모듈의 이름 붙은 상수로 선언하고 "localnet default; Astra-owned" 주석을 단다.
- **IssuerCap:** 패키지 발행 시 발행자에게 하나의 owned 객체로 만들어진다. `issue`는 `&IssuerCap`을 받는다. RS-1에는 transfer/burn 함수가 없다. `rs-1-issuercap-probe`는 RS-1 세션에서 먼저 돌고, 이 기록과 모순되면 프로브 결과가 이기며 기록된다.
- **페이지 claim 정렬 키:** `(page_index asc, claim_sequence asc)`.
- **가시성:** 모든 state·결정 파일은 `agent/kix-rs-1`에 커밋되어 저장소에 보인다. 비공개 채널 없음.
- **보존:** `docs/decisions`의 결정 기록은 영구다. `state/*.decision*.md`는 RS-1 게이트가 닫힐 때까지 보관한 뒤 `docs/decisions/archive/`로 옮긴다.
- **법적 보존(리걸 홀드):** 없다.

## 3. 제외(변경 없음)

돈, 하드웨어, Sui mainnet·testnet 또는 실운영 배포, 실제 비밀, production runtime이 필요한 모든 항목. deferred, owner는 Astra/User.

## 4. 기록 위치

- 이 기록: `docs/decisions/RIGHTS_SCALE_RS1_AUTHORIZATION_20261013.md`
- `docs/decisions/archive/rs-1.decision_answer.md`에 owner 답변 원문을 보존한다.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md`의 RS-1 행을 "in progress; authorized against draft 0.1 @ 9b12626b"로 갱신한다. RS-0 행은 `SOURCE_ONLY`로 남는다.
