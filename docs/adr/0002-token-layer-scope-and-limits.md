# ADR-0002 — Optional native token layer: scope and limits

Date: 2026-10-08.
Status: proposed; takes effect only when the User merges it. Records scope and limits. Not a lock lift.
Base: observed `origin/main` `7481b0e16ce9b903abbffa62249bb91cd9e63cfe` (fetched 2026-10-08). Issue #110 does not name an ADR path. `docs/adr/` contained only `0001-ktx-authority-commit-recovery.md`, so this file uses the next free number, 0002.

## 1. Purpose and status

This document is a scope-and-limits record for the optional native token layer (TL). It is not a lock lift. It does not unlock the new coin/TIX module lock.

It does not replace the separate ADR plus Astra re-ruling that TL-2 requires before any localnet token package.

Merging this ADR is neither of those two things. A User merge of this file does not lift the coin/TIX lock, and it does not stand in for `tl-coin-lock-adr` or for an Astra re-ruling.

## 2. Context

Each fact below is cited at the observed base.

No coin module and no `tix` module exists. `validation/2026-09-26-wave2-rights-issuance/README.md:22` states: "There is no new coin module and no `tix` module." The blueprint records the same fact at §2.1 (`docs/blueprints/optional-native-token-v1/README.md:52-58`).

Task 005 decision 5 (`docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md:71`) states: "New coin/TIX module (B) forbidden until ADR + Astra re-ruling." The open question at `:174` is: "ADR trigger if someone proposes coin/TIX module (B) again."

Astra ruled that the token blueprint applies to that trigger. The decision record §4.1 (`docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:103-107`) quotes PR #79 comment `5901429335`. On 2026-10-08 that comment was read on `SUNBURN-Golden/kix-protocol` (`cursor[bot]`, created 2026-09-30). Item 5 of the comment says the blueprint "해당한다", that the trigger is "proposes" and not "implements", and: "범위·한계를 기록하는 ADR을 TL-0 착수 전에 두되(TL-2의 ADR+Astra 재결정을 대체하지 않음)".

Roadmap R-1 (`docs/decisions/PROGRAM_ROADMAP_20260930.md:34`) records D-B in these words: "D-B 수락. Astra 판정대로 범위·한계 ADR(TL-A)을 TL-0 앞에 둔다. 새 coin/TIX 모듈 잠금의 해제 경로(ADR + Astra 재결정)는 그대로다." That sentence is about D-B. It is not a status label for this ADR.

Blueprint §3.1 (`:77-88`) separates six rights and assets (admission right, settlement claim, credit position, collateral, the token, and KRW or a stablecoin). That separation is context for this record. Its TK-* predicates are blueprint proposals. TL-0 finalizes them. This ADR does not adopt them.

## 3. Decision: what is in scope

The TL is an independent, optional layer, and this ADR documents it as design only. "Optional" is a property of the layer, not a mark of lower priority. Blueprint §1.2 (`:40-43`) states that booking, transfer, admission, refund and settlement must still stand if the token is not issued or the layer is off, and that the layer is designed, implemented and checked on its own. TK-2 in blueprint §3.2 (`:95`) is marked **[제안]**. This ADR cites that proposal. It does not adopt TK-2, TK-1 through TK-12, or V1 through V6.

The documentation-first sequence, taken from blueprint §12 (`:443-451`), decision record §5.2 (`:116-126`) and `docs/DEVELOPMENT_PLAN.md` §18.1 (`:542`), is:

- TL-A, then TL-0, then TL-1.
- TL-L runs in parallel and does not wait on this ADR (decision record §5.2 row 1′, `:122`; blueprint TL-L `:548-557`).
- TL-3 off-chain follows TL-1. The on-chain part of TL-3 follows TL-2 and the off-chain model (`DEVELOPMENT_PLAN.md:542`).

The stage table below mirrors blueprint §10.1 (`:385-390`). No stage is added, dropped or reworded in substance.

| Stage | Output | Entry | Forbidden |
|---|---|---|---|
| S0 Design | This blueprint, TL-A (scope-and-limits ADR), TL-0 and TL-1 contracts | Merge of the scope inclusion, plus a task document. TL-0 and TL-1 come after TL-A (Astra ruling) | Code |
| S1 Non-production implementation | Localnet-only token package and a reference model (TL-2, and only when the representation chosen is F1 or F2). The TL-3 off-chain model may start after TL-1; its on-chain part starts after TL-2 | TL-2: a separate ADR plus an Astra re-ruling (the coin/TIX lock). TL-3 off-chain: TL-1. Each needs its own task document | testnet, mainnet, key generation, real funds |
| S2 Integration and security check | Non-author independent review, a threat model, property and fuzz tests (TL-4) | S1 exit criteria met | Issuance |
| S3 Operational deployment and issuance | mainnet deployment and issuance, as a judgment at TL-5, not as work this ADR starts | External review finished; `PROGRAM_DECISIONS` §5 testnet and mainnet conditions (key-management decision, independent Move audit, testnet operation evidence, an operator); explicit User authorization separate from this ADR | Automatic progression |

R-3 (`docs/decisions/PROGRAM_ROADMAP_20260930.md:36`) states: "토큰 초기 역할 범위는 권고안 U2(담보)·U3(보상)로 설계한다. 되돌리기 어려운 선택이 들어가므로 최종 확정은 `tl-0` 계약 문서의 사용자 병합으로 한다." U2 (collateral) and U3 (rewards) are therefore the design scope. Final confirmation is the User's merge of `tl-0`. This ADR does not make that confirmation.

## 4. Decision: limits (non-authorizations)

This ADR authorizes none of the following.

1. A new coin or TIX module remains locked. Source: `docs/decisions/PROGRAM_DECISIONS_20260928.md:116`, "새 coin/TIX 모듈 | ADR과 Astra 재결정(Task 005 결정 5)".
2. Token issuance, sale, distribution, pools, buyback, a stablecoin, token gas, and an own chain stay out of the plan. Source: roadmap §5 `:221`, "토큰 발행·판매·분배·풀·바이백, 스테이블코인, 토큰 가스, 자체 체인 | 승인되지 않음 | 없음".
3. Real funds, and real PG, bank and KYC calls, stay unauthorized. Source: `AGENTS.md:114`; `PROGRAM_DECISIONS_20260928.md:109`.
4. Sui testnet deployment and Sui mainnet execution stay unauthorized. Source: `PROGRAM_DECISIONS_20260928.md:111-112`.
5. Key generation and repository secrets stay unauthorized. Source: blueprint §10.1 S1 (`:388`, "키 생성"); blueprint TL-2 (`:509`, "키 생성 없음(localnet)"); `AGENTS.md:119`.
6. Public operational endpoints stay unauthorized. Source: `PROGRAM_DECISIONS_20260928.md:113`.
7. R2, and an own replication, consensus or storage engine, stay unauthorized. Source: `AGENTS.md:111`.
8. The two locked kernel blobs and `reference/v0.3-rc1/**` stay unchanged. Source: `AGENTS.md` §4; decision record §4 (`:94`).
9. A production runtime stays unauthorized, including live-money execution and live Sui production execution. Source: `AGENTS.md:114`; `DEVELOPMENT_PLAN.md:542` ("실자금·운영 발행은 미승인").

## 5. Lock and unlock path (unchanged)

The coin/TIX lock stays. The recorded path is a User merge of `tl-coin-lock-adr`, plus an Astra re-ruling, and only then a localnet-only `tl-2`. Sources: roadmap `:28` and `:220`; roadmap §3.5 `:127-128`; `DEVELOPMENT_PLAN.md:542`.

One reading is labeled 해석 and is not stated here as a fact. Decision record §4, first row (`:92`), says: "TL-0·TL-1은 문서 전용이라 구현 잠금 대상이 아니라고 읽는다(해석). **TL-2(비운영 구현)부터 ADR + Astra 재결정이 필요하다.** 이번 요청은 그 재결정이 아니다."

If TL-0 selects F3 or F4, whether a later TL-2 is inside the lock is Astra's call. Blueprint §12 TL-2 (`:504`) states that F3 (a receipt object) is a new Move module that is not a coin, and that Astra checks whether that module is inside the coin/TIX lock, and that choosing only F4 (off-chain points) means TL-2 does not open.

## 6. Not decided here (UNDETERMINED, owner named)

No row below is closed by this ADR. Product policy values and new protocol commands are `DECISION_REQUIRED · Astra`. Legal, tax, accounting and provider answers stay UNDETERMINED with the owner named in the source.

| Item | Owner | Resolving node |
|---|---|---|
| Token existence, name and symbol | User. Blueprint §1.1 (`:38`) leaves the name and symbol unset | `tl-0` for existence and role. Name and symbol stay open until the User records them |
| Role confirmation. U2 and U3 are the R-3 design scope only | User | `tl-0` (User merge of that contract) |
| Representation F1–F4 | User | `tl-0` |
| Supply mode | User | `tl-0` |
| Supply numbers | `DECISION_REQUIRED · Astra`. This ADR states no number | `tl-0` only after that path |
| Regulated flag as an initialization choice | User for the design choice. The legal character is UNDETERMINED | `tl-0` for the initialization choice; legal character is TL-L |
| TK-1…TK-12 and V1–V6 | Blueprint proposals (`§3.2`, `§12.1`). TL-0 finalizes them. Not adopted here | `tl-0` |
| Legal, tax and accounting conclusions | UNDETERMINED. D-E (`TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:179`) leaves the owner to the User | `tl-legal-brief` prepares questions. TL-L is external |
| Chargeback window | UNDETERMINED. Card and payment-provider rules; Toss profile. Blueprint `:376` marks the window 미확인 | Not this ADR. Owner is the card or payment provider |
| Token↔KRW price source | Not chosen here. The node exists only if `tl-0` needs conversion | `tl-price-source-contract` |
| Wallet and exchange compatibility | UNDETERMINED. Blueprint §13 (`:576`) lists it as 미확인 and names no owner | No cited node assigns it |
| Testnet key management | User | `testnet-key-management-decision` |
| Any other product policy value, or a new protocol command | `DECISION_REQUIRED · Astra` | The node that would need the value. Not this ADR |

## 7. Consequences and gating

The dependency list in roadmap §3.5 (`:123-133`) is:

- `tl-a` has no predecessor in that table.
- `tl-0` depends on `tl-a`.
- `tl-price-source-contract`, `tl-1` and `tl-legal-brief` depend on `tl-0`.
- `tl-coin-lock-adr` depends on `tl-0` and `tl-1`.
- `tl-2` depends on `tl-coin-lock-adr`.
- `tl-3-offchain` depends on `tl-1`.
- `tl-3-onchain` depends on `tl-2` and `tl-3-offchain`.
- `tl-4` depends on `tl-2` and `tl-3-onchain`.
- `tl-5-decision` depends on `tl-4` and `tl-legal-brief`.

No TL node starts on this ADR alone. Each later node still needs its own audit, its own merge and its own task input.

Merge boundary, recorded here and not changed. Roadmap §3.5 (`:123`) still shows `tl-a` as "자동(M1·Fable)". Roadmap §1 (`:24`) says the delegation table is the current merge boundary. `docs/aiops/PROGRAM_ASTRA_DELEGATION.md:66` marks `tl-a` as contract_change YES, merge 대표님, audit floor A3. This file does not merge itself, and it does not move that boundary.

Index and plan back-links to this ADR are outside this record.

## 8. Non-claims

This ADR states no claim of legality, licensing, return, liquidity or price maintenance. It states no claim that a token is implemented or adopted. It states no supply figure, allocation, SLO or price.

The author's own check is not an independent review (decision record §7, `:197`). Review of a published head, and that head's CI, belong in the pull-request comment, not in a further commit made only to store those results (`AGENTS.md` §11).

## 9. References

Pinned to observed `origin/main` `7481b0e16ce9b903abbffa62249bb91cd9e63cfe`.

- `AGENTS.md` §4; §5 `:107-129`; §11.
- `docs/blueprints/optional-native-token-v1/README.md` §1.1 `:38`; §1.2 `:40-43`; §2.1 `:52-58`; §3.1 `:77-88`; §3.2 `:91-95`; §10.1 `:383-390`; §12 `:437-474` and TL-2 `:500-510`; TL-L `:548-557`; §13 `:566-576`.
- `docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md` §4 `:90-94`; §4.1 `:103-107`; §5 `:109-149`; D-B `:176`; D-E `:179`; §7 `:191-198`.
- `docs/decisions/PROGRAM_ROADMAP_20260930.md` §1 `:24` and `:28`; R-1 `:34`; R-3 `:36`; §3.5 `:119-133`; §5 `:207-221`.
- `docs/decisions/PROGRAM_DECISIONS_20260928.md` §5 `:104-116`.
- `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md:71` and `:174`.
- `docs/DEVELOPMENT_PLAN.md` §18 `:526-551`. The token-layer text is this section. The paragraph near `:383` is a TiKV comparison note and is not a source for this ADR.
- `validation/2026-09-26-wave2-rights-issuance/README.md:22`.
- `docs/aiops/PROGRAM_ASTRA_DELEGATION.md:66`.
- PR #79 comment `5901429335`, read 2026-10-08 on `SUNBURN-Golden/kix-protocol`.
