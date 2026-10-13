# ADR-0003 — Ask Astra to re-rule the coin/TIX lock for one localnet package

Date: 2026-10-09.
Status: proposed. This is a User decision document. It takes effect only when the User merges it ([roadmap](../decisions/PROGRAM_ROADMAP_20260930.md) §1 `:26`; the roadmap's own writing-alone rule is §0 `:14-15`). A lift of the new coin/TIX module lock takes effect only if an Astra re-ruling exists before that merge. Writing this file does not lift the lock. The builder does not merge this file and does not act on the recommendation in §4.
Base: observed `origin/main` `841408e77065c841ea73e2cf04fe8c03fbd35f5d`, fetched 2026-10-09. At the start of this session the branch `agent/kix-tl-coin-lock-adr` HEAD was that same SHA. No issue and no file under `docs/tasks/` names this node. `docs/adr/` then contained only `0001-ktx-authority-commit-recovery.md` and [ADR-0002](0002-token-layer-scope-and-limits.md), so this file uses the next free number, 0003.

Markers follow the token blueprint and [ADR-0002](0002-token-layer-scope-and-limits.md). **[현재]** is a fact read in this session. **[제안]** is a design sentence this ADR does not adopt. **[미확인]** is a value this ADR leaves empty.

## 0. Status and effect

This document asks Astra to re-rule one lock: the prohibition on a new coin/TIX module, and only for a non-production localnet package. It is the ADR that [ADR-0002](0002-token-layer-scope-and-limits.md) §5 left for later. It is not that re-ruling, and it is not the package.

Effect rule, in plain terms. A draft in the repository does nothing to the lock. The roadmap says writing that document alone creates no effect, and that its scope takes effect when the User merges it (`PROGRAM_ROADMAP_20260930.md:14-15`). Section 1 of the same file says `user_merge` stays the User's and that the delegation table is the current merge boundary (`:26`). [Program decisions](../decisions/PROGRAM_DECISIONS_20260928.md) §0 (`:13-14`) uses the same rule for that decision: writing alone creates no effect, and effect is the User's merge. [AGENTS.md](../../AGENTS.md) §4 (`:105`) says a locked kernel blob changes only through a separate explicit human decision. This ADR uses that same effect rule for the coin/TIX row in program decisions §5. The human decision is the User's merge, and only after Astra has re-ruled.

The builder's check of this file is not an independent review and is not a non-author exact-HEAD review (`AGENTS.md` §6, §14). This session has no task issue and no `ASTRA_TASK_KEY_V1` line, so the program-mode precedence at `AGENTS.md:13-16` does not apply here. Architecture rulings stay with Claude Fable through the central `aiops-fable` tool (`AGENTS.md:30-31`, User decision M5, 2026-09-30). This session does not issue one.

The User should not merge this ADR before that re-ruling exists. A ruling that contradicts this request means this ADR is revised before merge. §5 records the ruling as not yet issued.

## 1. Base and evidence

Each identifier below was read on the fetched base. None of them is a CI result for this file. CI from an earlier SHA does not transfer to a later SHA (`AGENTS.md` §6, §11). This session makes no CI claim for `841408e77065c841ea73e2cf04fe8c03fbd35f5d` or for any parent.

Locked blobs, checked before this file was added **[현재]**:

| File | Required blob | Observed |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |

`reference/v0.3-rc1/**` was not modified. The Sui framework pin in [Move.toml](../../reference/v0.3-rc1/sui/Move.toml) `:6` is `808640d9b49aecf29d8e6f46033c15eca236efa7` **[현재]**.

Merged inputs on this base **[현재]**:

| Input | What was merged | SHA read this session |
|---|---|---|
| [ADR-0002](0002-token-layer-scope-and-limits.md) | PR #126, scope and limits. Not a lock lift | merge `547d9fd5cd0e2d54e4fd61050d6f4fff530f3750` |
| [TL-0 role and supply](../contracts/TOKEN_ROLE_AND_SUPPLY.md) | PR #145 | merge `5714603158ddac1a5dcbe2e645c902e26f2b20a9` |
| [Price-source record](../decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md) | PR #146. Conversion is not required under the TL-0 recommendation | merge `28539987d1e676f0724081c41b22db51e731a967` |
| [TL-1 authority and lifecycle](../contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md) | PR #147. This base is that merge | `841408e77065c841ea73e2cf04fe8c03fbd35f5d` |

Node fields read from [.aiops/program.json](../../.aiops/program.json) `:557-566` **[현재]**: `depends_on` is `tl-0` and `tl-1`; `audit_floor` is A3; `user_merge` is true; `astra_auto_merge` is false. That object has no `astra_gate` key. The dispatch header for this node says `astra_gate: None`. The roadmap row says otherwise. §7 records that difference and does not resolve it.

## 2. What is locked, and why

Three different locks are easy to mix up. This ADR asks about only the third.

The kernel-blob lock is [AGENTS.md](../../AGENTS.md) §4. Two files stay byte-identical. This request does not touch them. A contract violation that could be fixed only by editing those files would stop, not by editing them (`AGENTS.md:100-105`).

[ADR-0002](0002-token-layer-scope-and-limits.md) is the scope-and-limits record (TL-A). Its §1 and §5 say a User merge of that file does not lift the coin/TIX lock and does not stand in for `tl-coin-lock-adr` or for an Astra re-ruling. Roadmap R-1 (`PROGRAM_ROADMAP_20260930.md:34`) accepted that placement: the unlock path "ADR + Astra 재결정" stays as it was. ADR-0002 pinned the token-layer sentence of the development plan at `:542` on its own base. On this base that sentence is [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) `:599`.

The lock this ADR asks Astra to re-rule is the new coin/TIX module, option B in Task 005. The sources, read here **[현재]**:

| Source | What it says |
|---|---|
| [Task 005](../tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md) decision 5, `:71` | "New coin/TIX module (B) forbidden until ADR + Astra re-ruling." |
| Same file, open question `:174` | "ADR trigger if someone proposes coin/TIX module (B) again." |
| [Program decisions](../decisions/PROGRAM_DECISIONS_20260928.md) §2.1, `:44` | Move `rights` and `zk_gate` extensions and localnet tests are in Track P. "새 coin/TIX 모듈은 제외한다(Task 005 결정 5)." |
| Same file §5, `:116` | "새 coin/TIX 모듈 \| ADR과 Astra 재결정(Task 005 결정 5)" |
| [Scope decision](../decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md) `:92` | The prohibition stays. TL-2, the non-production implementation, needs ADR + Astra re-ruling. "이번 요청은 그 재결정이 아니다." That sentence is about the scope PR, not about this file |
| [Roadmap](../decisions/PROGRAM_ROADMAP_20260930.md) `:28` | The only coin/TIX exception, `tl-2`, is possible only after an Astra re-ruling and the User's merge of `tl-coin-lock-adr` |
| Same file `:220` | "새 coin/TIX 모듈 \| ADR과 Astra 재결정, 잠금 변경은 사람 결정 \| `tl-coin-lock-adr`(사용자) 뒤 localnet `tl-2`만" |
| [README.md](../../README.md) `:34` | The new coin/TIX module stays locked. The only TL-2 localnet exception follows an Astra re-ruling and the User's merge of `tl-coin-lock-adr` |
| [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) `:599` | "coin/TIX 잠금 유지." The only TL-2 localnet exception is after the Astra re-ruling and the User's merge of `tl-coin-lock-adr`. `:604` records ADR-0002 as merged and as not a lift |

Why the lock exists, in plain terms. Task 005 chose to extend the existing Move `rights` module (and `zk_gate`) for issuance parity, and forbade a separate coin or TIX module until two things both exist: an ADR, and an Astra re-ruling. The program decisions kept that row. The token blueprint later put a localnet package on the map. Astra then said the blueprint counts as "proposing" that module again, so a scope ADR had to come first, and that scope ADR does not replace the later unlock. This file is the later request. It asks for a re-ruling. It does not perform the unlock.

Wave 2 recorded that no new coin module and no `tix` module existed (`validation/2026-09-26-wave2-rights-issuance/README.md:22`). This session did not add one **[현재]**.

## 3. The request to Astra

Astra is asked to re-rule the `:116` row for a non-production localnet package only. Five questions follow. Q2 and Q4 decide whether a later `tl-2` has anything it is allowed to build. This ADR does not answer them.

### Q1. Scope

Is the lift limited to one separate Move package on localnet, with no dependency on `kix::rights`, with existing packages unchanged, and with the Sui pin `808640d9b49aecf29d8e6f46033c15eca236efa7` unchanged?

That shape is the blueprint's TL-2 row (`docs/blueprints/optional-native-token-v1/README.md:504-510`) **[제안]** and the `tl-2` node spec in `.aiops/program.json:574` **[현재]**. This ADR asks Astra to confirm it. It does not widen it.

### Q2. Representation

Which of F1, F2, or F3, if any, is inside the lifted scope?

The TL-0 contract §3, as merged, says **[현재]**:

- F1, an open-loop `Coin<T>`: do not distribute it before TL-L. TL-0 does not recommend stage-1 distribution (`TOKEN_ROLE_AND_SUPPLY.md:99`, `:108`).
- F2, a closed-loop `Token<T>`: the only retained later candidate. That sentence is not a choice to implement F2 now. Until a later node selects F2 as the implementation representation, TL-2's representation precondition does not hold (`:100`, `:107`).
- F3, a receipt object: not a coin. Whether it is a "coin/TIX module" at all is Astra's call. The blueprint says so (`optional-native-token-v1/README.md:504`). TL-0 does not make that call (`TOKEN_ROLE_AND_SUPPLY.md:101`).
- F4, an off-chain point ledger: TL-0's stage-1 recommendation. No new Move module. TL-2 does not open (`:102`, `:106`). The F4 path does not need this lift.

No node has selected F1 or F2 as the implementation representation **[현재]**. This ADR does not select F1, F2, or F3.

If Astra names none of F1, F2, and F3, the lift has no operative content. That result is the same as option O1 in §4. A sentence that "the lock is lifted" without a named representation authorizes no package.

### Q3. Localnet bounds

The blueprint TL-2 start condition says "키 생성 없음(localnet)" (`optional-native-token-v1/README.md:509`). The stage table forbids key generation on the non-production stage (`:388`). This ADR asks Astra to state what localnet-only key handling means for that package: what may be created inside a localnet run, and what remains forbidden. **[미확인]**. This file does not resolve it.

### Q4. How E-1 interacts with a lift

TL-1 records exception E-1 as open (`TOKEN_AUTHORITY_AND_LIFECYCLE.md:112`). No token approver and no token custodian is named. The owner is `DECISION_REQUIRED · User`. Predicate `TL1-TK06-T5` (`:124`) says issuance and treasury spend do not start while any exception row is open, and that the localnet exclusion applies only to TL-2 after the lock lift. The same recommendation is at `:114`. TL-0 said the blueprint's localnet exclusion applies only after this ADR is merged by the User and Astra has re-ruled (`TOKEN_ROLE_AND_SUPPLY.md:234`).

Question for Astra: after a narrow lift, may localnet tests of mint and treasury paths run while E-1 is still open? This ADR does not name an approver or a custodian, and it does not close E-1.

### Q5. Record

Where does the re-ruling live, and what sunset or re-check ends it? §5 says where this repository will point at the ruling once it exists. The sunset is Astra's to set. This ADR sets none. Any number, cap, quorum, timelock, or pool balance is `DECISION_REQUIRED · Astra`. This ADR states none.

## 4. Options, consequences, recommendation

The recommendation is **[제안]**. It is not acted on. Merging a file that contains a recommendation does not, by itself, choose the option. The choice is the User's merge after a ruling exists, and the operative text is the ruling.

### O1. Keep the lock

The `:116` row stays as written. `tl-2` then follows its own spec: where the stage-1 representation is F4, that node delivers the short note that TL-2 does not open (`.aiops/program.json:574`). `tl-3-onchain` and `tl-4` stay limited, because both depend on `tl-2` (roadmap `:130-131`). The F4 path, the off-chain TL-3 model, and the other §5 locks are unchanged.

Consequence in plain terms: no localnet coin package is started. Design documents already merged stay design documents.

### O2. Narrow conditional lift

Astra names the representation and the bounds, and the lift is exactly that text. It is localnet-only. It is one separate package. Existing packages and the Sui pin stay. `tl-2` still needs a representation that Q2 placed inside the lift, and it still needs whatever Q4 says about E-1. A ruling that names no representation collapses this option to O1.

Consequence in plain terms: a later node may build only the package Astra described, on localnet, and only after the User merges this ADR. Sale, distribution, public networks, and real funds stay closed.

### O3. Broad lift

Any of F1, F2, and F3, in any package, would be treated as unlocked. This ADR does not recommend O3. It would drop the "localnet package only" boundary the roadmap states at `:28` and `:220`.

Consequence in plain terms: the original reason for the lock, a forbidden separate coin module, would be open in general. That is a different decision from the one this node is allowed to ask.

### O4. Defer

Leave the lock in place until some later node selects F1 or F2 as the implementation representation, and ask again then.

Consequence in plain terms: nothing is built now, and the question returns only if a representation is actually chosen. The wait is real, because TL-0 left F2 as a candidate and did not select it.

### Suggested recommendation

O2, collapsing to O1 if Astra names no representation. The TL-0 evidence supports that collapse: stage 1 is F4, F2 is only a later candidate, and no node has selected F1 or F2. The builder does not start `tl-2`, does not add a package, and does not edit the `:116` row to match this suggestion.

## 5. Astra re-ruling record

Status: not yet issued **[현재]**.

This file does not contain a link to a re-ruling, because none exists. When a ruling is issued, it is recorded in the pull-request audit comment on the exact head of this ADR. No later commit is made only to store that comment (`AGENTS.md` §11). The same shape is already used for a decision that stays a draft until the Astra review and the User merge exist ([RS-0 decision](../decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md) `:3`).

The User should not merge this ADR before that comment exists. If the ruling contradicts Q1–Q5 as asked, this ADR is revised, and the revised text is what the User considers.

Earlier rulings are context. They are not this re-ruling **[현재]**:

- PR #79 comment [`5901429335`](https://github.com/SUNBURN-Golden/kix-protocol/pull/79#issuecomment-5901429335), read this session on `SUNBURN-Golden/kix-protocol` (`cursor[bot]`, created 2026-09-30). The scope decision quotes it at `:107`. Item 4 keeps the unlock path as ADR plus Astra re-ruling, applying from TL-2. Item 5 says the token blueprint triggers the Task 005 `:174` question, and that the scope-and-limits ADR does not replace TL-2's ADR plus Astra re-ruling. Item 5 is why ADR-0002 exists. It is not the lift.
- D-D conditions (a)–(e), recorded at `TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:178` and accepted by roadmap R-2 (`PROGRAM_ROADMAP_20260930.md:35`). They bound the rights-scale reading of a `rights` / `zk_gate` extension. They are not a coin/TIX lift. Condition (a) says that reading does not include a coin/TIX module or a new economic-asset module. This request asks Astra whether a separate localnet package can be carved out without weakening (a)–(e) for the rights-scale work.

## 6. What this ADR does not authorize

This ADR authorizes none of the following. A future ruling can narrow Q1–Q5. It does not silently grant this list.

1. This file does not lift the new coin/TIX module lock. Source: `PROGRAM_DECISIONS_20260928.md:116`, "새 coin/TIX 모듈 | ADR과 Astra 재결정(Task 005 결정 5)". Any exception is the Astra ruling's own text, and only after the User merges this ADR.
2. Token issuance, sale, distribution, pools, buyback, a stablecoin, token gas, and an own chain stay out of the plan. Source: roadmap §5 `:221`, "토큰 발행·판매·분배·풀·바이백, 스테이블코인, 토큰 가스, 자체 체인 | 승인되지 않음 | 없음".
3. Real funds, and real PG, bank and KYC calls, stay unauthorized. Source: `AGENTS.md:114`; `PROGRAM_DECISIONS_20260928.md:109`.
4. Sui testnet deployment and Sui mainnet execution stay unauthorized. Source: `PROGRAM_DECISIONS_20260928.md:111-112`.
5. Key generation and repository secrets stay unauthorized. Source: blueprint §10.1 S1 (`:388`, "키 생성"); blueprint TL-2 (`:509`, "키 생성 없음(localnet)"); `AGENTS.md:119`. Q3 asks what the localnet phrase means. It does not permit key generation.
6. Public operational endpoints stay unauthorized. Source: `PROGRAM_DECISIONS_20260928.md:113`.
7. R2, and an own replication, consensus or storage engine, stay unauthorized. Source: `AGENTS.md:111`; `PROGRAM_DECISIONS_20260928.md:114`.
8. The two locked kernel blobs stay unchanged. Source: `AGENTS.md` §4; scope decision `:94` ("변경 없음"). `reference/v0.3-rc1/**` stays unchanged. Source: D-D condition (b), scope decision `:178`.
9. A production runtime stays unauthorized, including live-money execution and live Sui production execution. Source: `AGENTS.md:114`; `DEVELOPMENT_PLAN.md:599` ("실자금·운영 발행은 미승인").
10. A merge of this ADR does not start `tl-2`. That node still needs its own audit, its own task input, a representation inside the ruling, and the Q4 answer on E-1. Source: roadmap `:128`; `AGENTS.md` §2.

## 7. Consequences and gating

Roadmap §3.5 (`:123-133`) gives the TL order. The rows this request can affect:

- `tl-coin-lock-adr` depends on `tl-0` and `tl-1`. Both are merged on this base (§1).
- `tl-2` depends on `tl-coin-lock-adr`. Its spec (`.aiops/program.json:574`) is a separate localnet package only inside the lift a merged ADR grants. If the representation is F4, the node delivers a note that TL-2 does not open. This ADR does not open it.
- `tl-3-offchain` depends on `tl-1` only. It is not gated by this lift.
- `tl-3-onchain` depends on `tl-2` and `tl-3-offchain`. It stays limited while `tl-2` is closed.
- `tl-4` depends on `tl-2` and `tl-3-onchain`. It stays limited the same way.
- `tl-5-decision` depends on `tl-4` and `tl-legal-brief`. It is an operational judgment, not work this ADR starts. Program decisions §5 still bind it.

No later TL node starts on this ADR alone. Each still needs its own audit, its own merge, and its own task input.

Merge boundary, recorded and not changed:

| Place | What it says on this base |
|---|---|
| Roadmap §3.5 `:127` | `tl-coin-lock-adr`: audit floor A3, Astra gate ARCHITECTURE, merge **사용자** |
| [Delegation table](../aiops/PROGRAM_ASTRA_DELEGATION.md) `:70` | contract change NO, merge 대표님, audit floor A3. The table header (`:3`) says the table is a non-executable draft |
| Node object `.aiops/program.json:564-566` | `audit_floor` A3, `user_merge` true, `astra_auto_merge` false, no `astra_gate` key |
| Dispatch header for this node | `astra_gate: None`, `user_merge: true` |

Roadmap §1 (`:26`) says the delegation table is the current merge boundary. The merge actor in the roadmap row, the delegation row, and `user_merge: true` is the User. The Astra-gate cell does not match: the roadmap says ARCHITECTURE, and the node object has no `astra_gate` key, which the dispatch header calls None. This file does not pick a winner and does not edit those sources. It follows `user_merge: true`: the User merges, the builder does not.

Index and plan back-links are outside this record. `docs/README.md`, [CURRENT_CAPABILITY_REGISTER.md](../status/CURRENT_CAPABILITY_REGISTER.md) `:149`, and `DEVELOPMENT_PLAN.md` §18.1 stay as they were. A later sync node owns those pointers. ADR-0002 said the same about its own back-links.

## 8. Register

No row below is closed by this ADR. Product policy values and new protocol commands are `DECISION_REQUIRED · Astra`. Legal, tax, accounting, and provider answers stay UNDETERMINED with the owner named in the source.

| Item | Class | Owner | What this ADR does |
|---|---|---|---|
| The re-ruling asked in Q1–Q5 | `DECISION_REQUIRED · Astra` | Astra, through the central audit (`AGENTS.md:30-31`) | Asks. Does not write the ruling |
| Which of F1, F2, F3 is inside a lift | `DECISION_REQUIRED · Astra` | Astra (Q2). TL-0 left the implementation choice open | Does not pick a representation |
| Whether F3 is a coin/TIX module | `DECISION_REQUIRED · Astra` | Astra. Blueprint `:504` | Does not decide |
| Meaning of "키 생성 없음(localnet)" | `DECISION_REQUIRED · Astra` | Astra (Q3) | Does not resolve |
| Any supply, cap, quorum, timelock, pool balance, or other policy number | `DECISION_REQUIRED · Astra` | Astra | States none |
| A new protocol command | `DECISION_REQUIRED · Astra` | Astra | Adds none. `to_coin` and `from_coin` stay future package names in TL-0, not catalogue commands |
| Token approver and custodian (E-1) | `DECISION_REQUIRED · User` | User. `TOKEN_AUTHORITY_AND_LIFECYCLE.md:112` | Does not name anyone |
| Whether to merge this ADR | `DECISION_REQUIRED · User` | User. Roadmap §1 | Does not merge |
| Who starts the external TL-L review (D-E) | `DECISION_REQUIRED · User` | User. Scope decision `:179` | Does not name a starter |
| Legal, tax, and accounting conclusions | UNDETERMINED | External TL-L review. The User names the starter (D-E) | States none |
| Wallet and exchange compatibility | UNDETERMINED | No owner is named. Blueprint §13 (`:572`, `:576`) lists it as 미확인 and names no owner | States none |
| Chargeback window | UNDETERMINED | Card or payment provider, through the Toss profile. TL-0 `:260` | States no length |

## 9. Coverage, classification, non-claims, references

### Coverage (`AGENTS.md` §7)

| Requirement | Coverage | Action here |
|---|---|---|
| The coin/TIX prohibition and its unlock path are written down | Sufficient as documents: Task 005 `:71`, program decisions `:116`, scope decision `:92`, roadmap `:28` and `:220`, README `:34`, development plan `:599`, ADR-0002 | Cited. Not copied into a new test |
| A localnet package and its tests (`tl-2`) | Not covered. No package exists | No test added. The gap is the missing ruling and the missing representation |
| E-1 versus a localnet mint path | Partial. `TL1-TK06-T5` states the exclusion. It does not say whether tests may run while E-1 is open after a lift | No test added. Classified below |
| Price conversion as a precondition of this ADR | Sufficient. PR #146 records that the TL-0 recommendation needs no price source | Cited in §1. Not re-decided |

### Classification (`AGENTS.md` §8)

A. The written lock matches the sources in §2. This ADR does not change runtime behavior.

B. Contract undefined, recorded and not invented:

- Which representation a lift would cover, given that TL-0 recommended F4 and selected neither F1 nor F2.
- Whether localnet mint and treasury tests may run while E-1 is open, after a lift.
- What "키 생성 없음(localnet)" requires of a package.

C. No explicit contract violation. No locked file is changed. No merge blocker of class C is filed. The absent re-ruling is an open Astra decision (§5), not a kernel-contract breach.

### Non-claims

This ADR states no claim of legality, licensing, return, liquidity, or price maintenance. It states no claim that a token is implemented, issued, or adopted. It states no supply figure, allocation, SLO, or price. It states no claim that exact-head CI has run for a head that includes this file. The author's check is not an independent review (scope decision §7, `:197`).

### References

Pinned to observed `origin/main` `841408e77065c841ea73e2cf04fe8c03fbd35f5d`.

- `AGENTS.md` §4 `:100-105`; `:30-31`; §5 `:111-119`; §6; §7; §8; §11; §14.
- `README.md:34`.
- `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md:71` and `:174`.
- `docs/decisions/PROGRAM_DECISIONS_20260928.md` §0 `:13-14`; §2.1 `:44`; §5 `:109-116`.
- `docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:92`, `:94`, `:103-107`, `:178`, `:179`, `:197`.
- `docs/decisions/PROGRAM_ROADMAP_20260930.md` §0 `:14-15`; §1 `:26`; `:28`; R-1 `:34`; R-2 `:35`; §3.5 `:123-133`; §5 `:220-221`.
- `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md:3`.
- `docs/decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md`.
- `docs/adr/0002-token-layer-scope-and-limits.md` §1 and §5.
- `docs/contracts/TOKEN_ROLE_AND_SUPPLY.md` §3 `:99-115`; `:234`; §11.
- `docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md:112`, `:114`, `:124`.
- `docs/blueprints/optional-native-token-v1/README.md:388`, `:504-510`, `:572`, `:576`.
- `docs/DEVELOPMENT_PLAN.md:599`, `:604`.
- `docs/aiops/PROGRAM_ASTRA_DELEGATION.md:3`, `:70`.
- `.aiops/program.json:557-566`, `:574`.
- `reference/v0.3-rc1/sui/Move.toml:6`.
- `validation/2026-09-26-wave2-rights-issuance/README.md:22`.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md:149` (not updated by this ADR).
- PR #79 comment `5901429335`, read 2026-10-09 on `SUNBURN-Golden/kix-protocol`.
