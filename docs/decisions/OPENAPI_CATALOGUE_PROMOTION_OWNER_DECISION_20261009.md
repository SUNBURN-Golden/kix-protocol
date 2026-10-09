# OpenAPI 카탈로그 승격 — 소유자 결정 위치 기록 (2026-10-09)

노드 `audit3-openapi-promotion-owner-decision-record`. 이슈 없음. 문서일: 2026-10-09.

상태: 위치 기록. 결정을 새로 만들지 않는다. 검토됨으로 표시하지 않는다.

이 파일은 이미 병합된 글이 인용하는 2026-10-09 소유자 결정을 [AGENTS.md](../../AGENTS.md) §5가 적는 `docs/decisions/` 아래에 가리킨다. 결정 문장을 새로 만들지 않는다.

## 1. 결정

결정자는 JunTae다. 날짜는 2026-10-09다.

출처: `validation/2026-10-09-openapi-catalogue-promotion/README.md:13`

> JunTae, 2026-10-09: proceed with the recommended options in the program state decision (DR-1 B, DR-2 A, DR-3 `bootstrap-2`, DR-4)

그 문장이 말하는 프로그램 상태 결정은 이 저장소에 없다. DR-1, DR-2, DR-3, DR-4의 정의 문장도 이 저장소에 없다. 저장소에서 `DR-1`부터 `DR-4`를 찾으면 그 검증 README의 13행과 83행뿐이다. 이 기록은 빈 정의를 채우지 않는다.

이 결정을 인용하는 병합된 위치는 다음이다.

- [docs/contracts/openapi/README.md](../contracts/openapi/README.md) 81행
- [docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md](../contracts/BOOKING_RESALE_ADMISSION_GATES.md) 20, 291, 453, 678, 849행
- [docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md](../contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md) 288행
- [docs/contracts/CREDIT_ADVANCE_F04.md](../contracts/CREDIT_ADVANCE_F04.md) 197, 407행
- [validation/2026-10-09-openapi-catalogue-promotion/README.md](../../validation/2026-10-09-openapi-catalogue-promotion/README.md) 13행

산출물이 병합된 PR은 #152다. 병합 커밋은 `d63768ddf276c60173aa2c933f4feef3449a9452`다. `git show -s --format='%H %P %an' d63768ddf276c60173aa2c933f4feef3449a9452`로 읽은 부모는 `c2cde86e21a6e5ba6f24a56548636db6d0a34c6f`와 `a9be88d3da4d735aabc5168c68007c062956b412`다. 그 커밋의 작성자 이름은 `soulbound_jt`다. `gh pr view 152 --repo SUNBURN-Golden/kix-protocol --json mergedBy,mergeCommit,mergedAt`로 읽은 `mergeCommit.oid`는 같은 커밋이다. `mergedBy.login`은 `BeautifulMind-JT`다. `mergedAt`은 `2026-10-09T04:13:43Z`다.

## 2. 네 항목과 병합된 산출물

항목과 산출물의 대응은 노드가 적은 네 항목과 [openapi/README.md](../contracts/openapi/README.md) 81행의 순서(두 번째 핀, 균일 접두 와이어 이름, `bootstrap-2`, 루프백 의미)를 따른다. DR 라벨은 검증 README 13행에만 나온다. 아래 표의 문장은 병합된 파일이 적은 문장이다. DR 선택지의 정의가 아니다.

| 항목 | 라벨 | 산출물 | 원문 (`file:line`) |
|---|---|---|---|
| DR-1, 두 번째 핀 | B | [fsm-command-contract.json](../contracts/openapi/fsm-command-contract.json) (git blob `3771a8739b906a478b54c597df37e27d1afc5f21`, [openapi/README.md](../contracts/openapi/README.md) 34행과 같음). 같은 README 14행, 33–35행, 79행. [검증 README](../../validation/2026-10-09-openapi-catalogue-promotion/README.md) 19행 | `validation/2026-10-09-openapi-catalogue-promotion/README.md:19` — Second pin `docs/contracts/openapi/fsm-command-contract.json` (44 commands, wire names `<machine>_<op>`). |
| DR-2, 접두 와이어 이름 | A | [openapi/README.md](../contracts/openapi/README.md) 49행, 81행. [BOOKING_RESALE_ADMISSION_GATES.md](../contracts/BOOKING_RESALE_ADMISSION_GATES.md) 20, 291, 453, 678, 849행. [SETTLEMENT_DISTRIBUTION_F01_F03.md](../contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md) 288행. [CREDIT_ADVANCE_F04.md](../contracts/CREDIT_ADVANCE_F04.md) 197, 407행 | `docs/contracts/openapi/README.md:81` — 2026-10-09 소유자 결정(JunTae)이 두 번째 핀, 균일 접두 와이어 이름, `bootstrap-2`, 루프백 의미를 승인했다. |
| DR-3, `bootstrap-2` | `bootstrap-2` | [manifest.bootstrap-2.json](../../sdk/compat/manifests/manifest.bootstrap-2.json). [bootstrap-2.profile.json](../../sdk/compat/profiles/bootstrap-2.profile.json). [COMPATIBILITY_MANIFEST_V1.md](../contracts/sdk/COMPATIBILITY_MANIFEST_V1.md). [검증 README](../../validation/2026-10-09-openapi-catalogue-promotion/README.md) 22행 | `validation/2026-10-09-openapi-catalogue-promotion/README.md:22` — TypeScript 0.x client regenerated. New manifest revision `bootstrap-2`. `bootstrap-1` files are unchanged historical pins. |
| DR-4, readiness 거절 | 13행에 글자 라벨 없음 | [integration_gate/server.py](../../integration_gate/server.py). [integration_gate/constants.py](../../integration_gate/constants.py). [integration_gate/test_http_gate.py](../../integration_gate/test_http_gate.py). [openapi/README.md](../contracts/openapi/README.md) 83행. [검증 README](../../validation/2026-10-09-openapi-catalogue-promotion/README.md) 21행, 83행 | `docs/contracts/openapi/README.md:83` — `--readiness-dir`가 있으면 FSM 명령은 저널에 쓰기 전에 `READINESS_FSM_REFUSED`로 거절한다. 그 철자는 승인된 실패-닫힘 동작의 루프백 라벨이다. 철자를 바꾸는 주체는 Astra다. `validation/2026-10-09-openapi-catalogue-promotion/README.md:83` — DR-4 left the readiness refusal token for Astra to name and said not to invent one. The loopback label used here is `READINESS_FSM_REFUSED` (HTTP 422, `rejected: true`). It names the approved fail-closed behavior. A different spelling is Astra's. It is not a product-policy number. |

출처: `validation/2026-10-09-openapi-catalogue-promotion/README.md:19`

> Second pin `docs/contracts/openapi/fsm-command-contract.json` (44 commands, wire names `<machine>_<op>`).

출처: `docs/contracts/openapi/README.md:81`

> 2026-10-09 소유자 결정(JunTae)이 두 번째 핀, 균일 접두 와이어 이름, `bootstrap-2`, 루프백 의미를 승인했다.

출처: `validation/2026-10-09-openapi-catalogue-promotion/README.md:22`

> TypeScript 0.x client regenerated. New manifest revision `bootstrap-2`. `bootstrap-1` files are unchanged historical pins.

출처: `docs/contracts/openapi/README.md:83`

> `--readiness-dir`가 있으면 FSM 명령은 저널에 쓰기 전에 `READINESS_FSM_REFUSED`로 거절한다. 그 철자는 승인된 실패-닫힘 동작의 루프백 라벨이다. 철자를 바꾸는 주체는 Astra다.

출처: `validation/2026-10-09-openapi-catalogue-promotion/README.md:83`

> DR-4 left the readiness refusal token for Astra to name and said not to invent one. The loopback label used here is `READINESS_FSM_REFUSED` (HTTP 422, `rejected: true`). It names the approved fail-closed behavior. A different spelling is Astra's. It is not a product-policy number.

## 3. 라벨

검증 README 83행은 루프백 라벨을 이렇게 적는다.

출처: `validation/2026-10-09-openapi-catalogue-promotion/README.md:83`

> DR-4 left the readiness refusal token for Astra to name and said not to invent one. The loopback label used here is `READINESS_FSM_REFUSED` (HTTP 422, `rejected: true`). It names the approved fail-closed behavior. A different spelling is Astra's. It is not a product-policy number.

출처: `docs/contracts/openapi/README.md:83`

> 철자를 바꾸는 주체는 Astra다.

이 줄은 인용문이 아니다. the label is a builder-side loopback label, as the validation README records.

철자를 다른 문자열로 바꾸는 일은 이 기록이 하지 않는다. 그 주체는 위 인용이 적는 Astra다.

## 4. 승인하지 않는 것

아래는 병합된 파일의 문장이다. 그 문장들은 이 결정이 승인하지 않는 것을 적는다.

출처: `validation/2026-10-09-openapi-catalogue-promotion/README.md:90`

> No production endpoint, public host, server entry, or security scheme.

> No real payment, KYC, bank, or venue call.

> No Sui testnet or mainnet.

> No new protocol command outside the existing `REPLAYABLE` sets.

> Stable 1.0 is not published.

> `bootstrap-2` is catalogue-schema binding only. Semantic conformance stays on HOLD.

출처: `docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md:291`

> 그 집합 밖의 새 프로토콜 명령은 `DECISION_REQUIRED · Astra`다.

같은 문장은 [BOOKING_RESALE_ADMISSION_GATES.md](../contracts/BOOKING_RESALE_ADMISSION_GATES.md) 453행, [SETTLEMENT_DISTRIBUTION_F01_F03.md](../contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md) 288행, [CREDIT_ADVANCE_F04.md](../contracts/CREDIT_ADVANCE_F04.md) 197행에도 있다.

출처: `docs/contracts/openapi/README.md:60`

> `servers`는 어느 문서에도 없다.

잠금 포인터는 [프로그램 결정](PROGRAM_DECISIONS_20260928.md) §5다. 그 표에서 schema·SDK 안정 1.0 행은 그 파일 117행이다. 이 기록은 그 잠금을 열지 않는다.

## 5. 비주장·미정

1. 이 기록은 새 승인을 더하지 않는다.
2. 작성자는 빌더다. 비작성자 검토가 아니다.
3. 이 글을 쓸 때 이 파일을 담은 exact-head CI는 없다.
4. DR 정의와 프로그램 상태 결정 본문은 이 저장소 밖에 있다. 저장소 안의 해당 문자열은 §1이 적은 두 행뿐이다.
