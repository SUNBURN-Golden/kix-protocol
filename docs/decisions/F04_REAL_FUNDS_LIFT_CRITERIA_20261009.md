# Criteria for lifting real credit (2026-10-09)

Node `f04-real-funds-lift-criteria`. No issue. No file under `docs/tasks/` names this node. This is a User decision document. It lists conditions a future proposal to lift the real-credit lock must meet. It stops at criteria.

Date: 2026-10-09.
Status: proposed. This is a User decision document. It takes effect only when the User merges it ([roadmap](PROGRAM_ROADMAP_20260930.md) §1 `:26`; writing alone has no effect, roadmap §0 `:14-15`). The builder does not merge this file and does not act on the recommendation in §6.

## 0. Status and effect

This document is the criteria list Task 005 left open. It is not a legal opinion, not an Astra ruling, and not an explicit User OK to move real credit.

Effect rule, in plain terms. A draft in the repository does nothing to the lock. The roadmap says writing that document alone creates no effect (`PROGRAM_ROADMAP_20260930.md:14-15`). Section 1 of the same file says `user_merge` stays the User's and that the delegation table is the current merge boundary (`:26`). [Program decisions](PROGRAM_DECISIONS_20260928.md) §0 (`:13-14`) uses the same rule for that decision: writing alone creates no effect, and effect is the User's merge. This file uses that rule for the real-credit row.

It takes effect only when the User merges it. The builder does not merge it and does not act on the recommendation in §6. The builder's check is not an independent review and is not a non-author exact-HEAD review (`AGENTS.md` §6, §14). This session has no task issue and no `ASTRA_TASK_KEY_V1` line, so the program-mode precedence at `AGENTS.md:13-16` does not apply here. Architecture rulings stay with Claude Fable through the central `aiops-fable` tool (`AGENTS.md:30-31`, User decision M5, 2026-09-30). This session does not issue one.

What a merge of this file adopts is only the criteria list in §4, and only if the User merges the file without edits (§6). That merge does not lift the lock. The criteria are necessary conditions for a later proposal. No criteria set triggers a lift automatically. Meeting a row, writing this file, or merging this file does not start `cr-01-product-authority` or any `fin-*` node. Those stay in the pending catalogue until their own later promotion (`PROGRAM_EXPANSION_20261002_KO.md` `cr-01-product-authority`, `:435-437` and `:463`).

## 1. Base and evidence

Each identifier below was read on the fetched base. None of them is a CI result for this file. CI from an earlier SHA does not transfer to a later SHA (`AGENTS.md` §6, §11). This session makes no CI claim for `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1` or for any parent. Local commands are in [the validation record](../../validation/2026-10-09-f04-real-funds-lift-criteria/README.md). They are not exact-head CI.

Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`: `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1`. The branch is `agent/kix-f04-real-funds-lift-criteria`. That commit is the merge of pull request #158 (`f04-mock-deepening`). This session does not commit, so there is no implementation commit SHA.

Locked blobs, checked before this file was added:

| File | Required blob | Observed |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |

`reference/v0.3-rc1/**` was not modified.

Merged input on this base:

| Input | What was merged | SHA read this session |
|---|---|---|
| [F04 mock contract](../contracts/CREDIT_ADVANCE_F04.md), node `f04-mock-deepening` | PR #158. Mock boundary only. Real credit stays locked | merge `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1` |

Node fields read from [`.aiops/program.json`](../../.aiops/program.json) `:652-660`: `depends_on` is `f04-mock-deepening`; `audit_floor` is A3; `user_merge` is true; `astra_auto_merge` is false. That object has no `astra_gate` key.

Astra-gate mismatch, recorded and not resolved:

| Place | What it says on this base |
|---|---|
| Dispatch header for this node | `astra_gate: None`, `user_merge: true` |
| Roadmap §3.6 `:140` | Astra gate ARCHITECTURE, merge **사용자** |
| Node object `.aiops/program.json:652-660` | no `astra_gate` key |
| [Delegation table](../aiops/PROGRAM_ASTRA_DELEGATION.md) `:78` | contract change NO, merge 대표님, audit floor A3. The table header (`:3`) says the table is a non-executable draft |

The merge actor in the roadmap row, the delegation row, and `user_merge: true` is the User. This file does not pick a winner among the gate cells and does not edit those sources. It follows `user_merge: true`.

## 2. What is locked and where it is written

The lock this document is about is real credit, regulated lending, and real-funds paths for F04. The sources, read here:

| Source | What it says |
|---|---|
| [Task 005](../tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md) decision 6, `:72` | "여신 / 신용 선지급 = **F04**, **mock/sim only** for now. Real credit, regulated products, real funds paths forbidden until separate Astra ruling + explicit OK." |
| Same file, hard lock `:129` | "**Real** credit / regulated lending / real-funds paths (until Astra + explicit OK)" |
| Same file, open question `:175` | "Real-funds F04 lift criteria (explicit; not implied by mock work)" |
| [Program decisions](PROGRAM_DECISIONS_20260928.md) §5 `:110` | "실제 여신·규제 금융 \| 법률·인허가 검토와 Astra·사용자 명시 승인(Task 005 결정 6)" |
| Same file §2.1 `:50` | "F04 여신은 mock·시뮬레이션만 한다(Task 005 결정 6)." |
| [Roadmap](PROGRAM_ROADMAP_20260930.md) §5 `:214` | "실제 여신·규제 금융 \| 법률·인허가 검토와 Astra·사용자 승인 \| `f04-real-funds-lift-criteria`(사용자)" |
| Same file `:28` | Product policy and new commands stop at `DECISION_REQUIRED`. Legal, accounting, and Toss answers stay `UNDETERMINED` with an owner. The §5 locks stay. |
| Same file `:45` | "D-E(법률·회계·세무·금융 검토의 주체와 시점)는 사람이 정할 일이라 사용자 몫으로 남긴다." |
| [F04 contract](../contracts/CREDIT_ADVANCE_F04.md) preamble `:18-19` | Astra decision 6: mock/sim only. Real credit, regulated products, and real-funds paths stay forbidden until a separate Astra decision and an explicit OK. |
| Same file §5.1 `:193` | "Task 005 결정 6대로 실여신·실지급은 잠금이다." |
| Same file §7.9 `:511` | Live HTTP, underwriting, KYC-AML, PG and bank rails, and real credit are absent. |

Neighbouring locks stay separate. A real-credit lift cannot substitute for any of them. Each keeps its own row and its own unlock:

| Lock, quoted from program decisions §5 | Unlock, quoted from the same row | Where else it is written |
|---|---|---|
| 실자금, 실 PG·은행·KYC 호출 | [토스 프로파일](../contracts/PG_TOSS_CARD_PROFILE.md)의 미확인 항목(MID, 가맹 범위, 웹훅 서명) 확인, sandbox 적합성 증거, 사용자 명시 승인 (`:109`) | Toss profile `:7`, `:170` (가맹 범위, MID), `:171` (일반 결제 웹훅 서명). Open inputs I02, I03, I04 |
| Sui testnet 배포 | 키 관리 방식 결정 문서와 사용자 승인. localnet 시험은 이미 허용 (`:111`) | Roadmap §5 `:215` |
| Sui mainnet 실행 | Move 독립 감사, testnet 운용 증거, 키 관리 운영 책임자, 사용자 승인 (`:112`) | Roadmap §5 `:216` |
| 공개 운영 엔드포인트 | 인증, TLS, 운영 책임자, 장애 대응 계획, 사용자 승인 (`:113`) | Roadmap §5 `:217` |
| R2, 자체 복제·합의·저장 엔진 | §9 비교가 기성 backend의 구체적 부족을 입증하고, 비용·검증·운영 책임이 문서화되고, 사용자가 승인 (`:114`) | Roadmap §5 `:218`. `AGENTS.md:111` |
| 새 coin/TIX 모듈 | ADR과 Astra 재결정(Task 005 결정 5) (`:116`) | Roadmap `:28` and `:220`. The only localnet exception is `tl-2`, and only after an Astra re-ruling and the User's merge of `tl-coin-lock-adr` |

[Model 1](AUTHORITY_MODEL_1.md) `:12-13` already says a chain record does not by itself guarantee bank funds, a contractual debt, or performance of the show. A credit lift does not change that sentence.

## 3. Scope of any future lift

A lift names exactly one product scope. The pending node `cr-01-product-authority` lists these as separate scopes (`PROGRAM_EXPANSION_20261002_KO.md:446`):

- business advance (사업자 선지급)
- recurring limit (반복 한도)
- production funding (제작 자금)
- consumer deferred payment (소비자 후불)
- inventory finance (재고 금융)

Which scope a lift names is empty. Owner: `DECISION_REQUIRED · User`. A lift for one scope covers no other scope. This document does not start `cr-01-product-authority`. That node is pending catalogue and is not a current schema-v1 dispatch target (`:463`).

## 4. Criteria

One table per group. Columns are the condition, the form of evidence a later proposal would have to bring, the owner and the status, and the source. No row states an amount, a cap, a rate, a reserve, a service level, a deadline, or a pilot size. An empty cell stays empty. Evidence that would change a protocol flag is not defined here (§5).

### L. Legal and licensing

Owner of this group: `UNDETERMINED · external counsel`. The User names who starts the review (roadmap D-E `:45`; open input I10). This document names no reviewer and states no legal conclusion.

| ID | Criterion | Evidence form | Owner and status | Source anchor |
|---|---|---|---|---|
| L-1 | A written product characterization and the jurisdiction it is written for, scoped to the single product in §3 | A dated written opinion. The characterization is not filled here | `UNDETERMINED · external counsel` | Task 005 decision 6 `:72`. F04 preamble `:18-19` |
| L-2 | Whether a licence or registration is required, and who would hold it | The same opinion, or a supplement that says the need and the holder are still open | `UNDETERMINED · external counsel` | Program decisions §5 `:110`. F04 §5 `:168` and §5.4 `:263` |
| L-3 | Legal parties: lender, borrower, secured party, and refund debtor | The opinion on parties. The mock label is not a party | `UNDETERMINED · external counsel`. The User names the starter (D-E) | F04 §5.2 `legal-parties` `:209`. Roadmap D-E `:45`. I10 |
| L-4 | Collateral or receivable assignment, and perfection, as counsel describes them | The opinion. This document does not say that any interest is perfected | `UNDETERMINED · external counsel` | F04 §5.2 `perfection` `:212`. I10 path, same row |
| L-5 | Whether term and disclosure are lawful, including any statutory limit counsel finds | The opinion. This document cites no statute and states no limit | `UNDETERMINED · external counsel` | F04 §5 `:168-169`. Task 005 `:129` |
| L-6 | KYC and AML duties that apply to the named product, if any | The opinion. The mock does not perform KYC | `UNDETERMINED · external counsel` | F04 §7.1 `:334-335`. F04 §7.9 `:506` and `:511` |
| L-7 | Personal data and retention for that product | Counsel's retention conclusion, after the User supplies parties, jurisdiction, and materials. No period is calculated here | `UNDETERMINED · external counsel` for the legal period. See also O-7 | Open input I10 `:34`. F04 §0 E06 row `:30` |
| L-8 | Tax and accounting treatment | A written conclusion from the owner the User names. No treatment is chosen here | `UNDETERMINED · external tax/accounting`. The User names that owner (D-E) | Roadmap D-E `:45`. F04 §5.4 `:261` leaves loss attribution empty |
| L-9 | Any contact with a regulator is made by a human, not by an agent or an automated sender | A record that a named human sent it, if a contact happens. This document sends nothing and names no one | `UNDETERMINED · external counsel` for the content. Who may send it is `DECISION_REQUIRED · User` | Roadmap D-E `:45`. `AGENTS.md` §5 does not authorize regulator contact |
| L-10 | Complaint and dispute handling for the named product | A written handling description from counsel, still without a timeline or a remedy amount | `UNDETERMINED · external counsel` | F04 §5 `:172` (disposal and enforcement left empty). I10 |
| L-11 | One written, dated conclusion, and that conclusion names only the product scope in §3 | The opinion itself, dated, and limited to that scope. A conclusion for a different scope does not count | `UNDETERMINED · external counsel` | Task 005 `:175`. Program decisions §5 `:110` |

### C. Capital and funding

| ID | Criterion | Evidence form | Owner and status | Source anchor |
|---|---|---|---|---|
| C-1 | The source of funds that would actually be lent, named as a source that is not the mock face | A User decision that names the source. `confirmed_cash` and `recovery_due` are not that source | `DECISION_REQUIRED · User` | F04 §2 `:87-88`. F04 §5 `:174`. F04 §5.5 `:281` |
| C-2 | Whether any regulatory or accounting capital must stand behind that source | A written answer from counsel or accounting. No amount is stated here | `UNDETERMINED · external counsel/accounting` | Program decisions §5 `:110`. Roadmap D-E `:45` |
| C-3 | Reserves, and who bears a loss | An Astra decision. No reserve and no split are stated here | `DECISION_REQUIRED · Astra` | F04 §5 `:169`. F04 §5.4 `:261` |
| C-4 | Exposure caps for the named product | An Astra decision. No cap is stated here | `DECISION_REQUIRED · Astra` | Roadmap `:28`. F04 §5 `:164` (product-policy numbers belong to Astra) |
| C-5 | Custody and segregation of lent funds from other flows | A written answer from the User, the bank, and Toss, including the still-open merchant scope | `UNDETERMINED · User/bank/Toss` | Open input I03 `:27`. Toss profile `:170`. Program decisions §5 `:109` |
| C-6 | APR and fees, if any | An Astra decision on `interest-apr-schedule`. The mock rejects a product object | `DECISION_REQUIRED · Astra` | F04 §5.2 `:210`. F04 §3 `:108` |
| C-7 | Who bears an open refund against an advance, while the settlement bearer is `UNDEFINED` | An Astra decision that waits on the settlement-policy dependency. This document does not pick a bearer | `DECISION_REQUIRED · Astra` | F04 §2 `:79` and §3 `:112`. Settlement contract `:195-196` (`refund_bearer_policy = UNDEFINED`). Roadmap node `settlement-policy-deepening` `:67` |

### R. Risk

| ID | Criterion | Evidence form | Owner and status | Source anchor |
|---|---|---|---|---|
| R-1 | An underwriting and eligibility policy for the named product | An Astra decision. The mock `approve` is a caller-recorded step and does not score, check KYC, or grant a licence | `DECISION_REQUIRED · Astra` | F04 §7.1 `:334-335`. F04 §7.9 `:506` |
| R-2 | What happens on borrower default, organizer default, or cancellation of the event | An Astra decision for the policy. Legal effect stays in L-3 and L-10 and is not decided here | `DECISION_REQUIRED · Astra` | F04 §7.1 `:327`. F04 §7.9 `:505` (`default` is not a delinquency judgment) |
| R-3 | How collateral is revalued after the first snapshot | An Astra decision on `limit-recalculation`. The mock freezes the first accepted face | `DECISION_REQUIRED · Astra` | F04 §5.2 `:213`. F04 §2 `:90-92` |
| R-4 | Double-pledge and double-financing of the same claim | An Astra decision. The mock does not say an external pledge disappeared | `DECISION_REQUIRED · Astra` | F04 §0 `:49`. Flag `external_pledge_complete` in §1 `:66` |
| R-5 | Concentration limits across borrowers, organizers, or events | An Astra decision. No limit is stated here | `DECISION_REQUIRED · Astra` | F04 §5 `:164`. Roadmap `:28` |
| R-6 | Independent external evidence for each always-false flag in §5 | Not defined in this document. Defining that evidence is a possible contract change and needs its own Astra decision. No new protocol command is added | `DECISION_REQUIRED · Astra` | F04 §1 `:63-67`. F04 §7 `:300-301` |
| R-7 | Residual-risk policy: who bears a late loss, from what source, and which follow-up actions are allowed | An Astra decision. No source, list, or limit is stated here | `DECISION_REQUIRED · Astra` | Open input I05 `:29`. Question U-R2 in [the question sheet](../status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md) `:63`. Open inputs §4 `:107` |
| R-8 | Delinquency, write-off, and recovery | An Astra decision. The mock revision left these empty on purpose | `DECISION_REQUIRED · Astra` | F04 §5.4 `:261`. F04 §7.9 `:504-505` |

### O. Operations

| ID | Criterion | Evidence form | Owner and status | Source anchor |
|---|---|---|---|---|
| O-1 | A named accountable operator and a named backup for the credit activity | A User decision that names both. Open-input I11 approvers are not automatically those operators. This document names neither | `DECISION_REQUIRED · User` | Open input I11 `:35`. Roadmap §5 `:214` (사용자 승인) |
| O-2 | Servicing and bank reconciliation that keep UNKNOWN fencing, a single writer, and no automatic retry or polling | A written operating note that repeats those existing rules. This document does not add a polling or retry path | The rules are already in `AGENTS.md:7-8`. Who operates is `DECISION_REQUIRED · User` (O-1) | `AGENTS.md:7-8`. Program decisions §0 `:18-19` |
| O-3 | An adopted durable backend for this scope, plus restore evidence | The adoption decision for that scope, and a closed I13 record. A local non-production stage-5 adoption is not this evidence. The mock flag `durable` stays false. R2 stays locked | Backend adoption for real credit: `DECISION_REQUIRED · User`. I13 restore evidence: `UNDETERMINED · User/operations owner` | Open input I13 `:37`. Program decisions §2.2 `:60` and §5 `:114`. Roadmap R-6 `:39`. [Backend adoption proposal](BACKEND_ADOPTION_PROPOSAL_20261009.md) §6 and §7 (local non-production scope; I13 stays open there) |
| O-4 | Provider sandbox evidence before any real PG call | The evidence the node `toss-sandbox-conformance-plan` is specified to plan. This document does not call a provider and does not store a credential | The PG lock stays on program decisions §5 `:109`. Owner of the Toss facts: `UNDETERMINED · Toss` | Program decisions §5 `:109`. Roadmap `:213`. `.aiops/program.json:663` |
| O-5 | Public-endpoint readiness, as its own unlock | The plan node `public-endpoint-readiness-plan`. This document does not deploy an endpoint. The gate stays loopback | Public-endpoint lock: program decisions §5 `:113`. Owner of the operations owner inside that unlock: `DECISION_REQUIRED · User` | Program decisions §5 `:113`. Roadmap `:217` |
| O-6 | A credit-specific incident runbook | A runbook whose service levels, if any, come from a separate Astra decision. None are stated here | `DECISION_REQUIRED · Astra` for any service level. The runbook's existence is a condition of a later proposal | Task 005 `:35` and `:131` (do not invent service levels). F04 §5.4 `:268` |
| O-7 | Retention handling and an independent audit of that handling | The retention proposal's open rows, closed by their owners, and an audit by someone other than the author of this file. No period is stated here | Legal period: `UNDETERMINED · external counsel` (L-7). Other retention rows keep the owners in [the retention proposal](RETENTION_PERIODS_PROPOSAL_20261009.md) | I10 `:34`. Retention proposal §0 and §11 |
| O-8 | AI-initiated credit actions, if any, require a separate User-approved decision | The merged `ai-delegation-execution-decision`, naming credit inside its scope. This document does not enable delegated execution | `DECISION_REQUIRED · User` | Roadmap `:139`. Program decisions §2.1 `:49` (model output alone does not disburse). Open input I11 `:35` (no expansion of AI self-delegation) |
| O-9 | A staged rollout and a way to re-lock | A separate decision document for pilot scope and for the conditions that stop the pilot. Those values are Astra's. None are stated here | `DECISION_REQUIRED · Astra` for the values. The User still approves the lift (P-2) | Program decisions §1 principle 2 `:25` (a lock is a door, not a permanent ban). Task 005 `:175` |

### P. Approval

| ID | Criterion | Evidence form | Owner and status | Source anchor |
|---|---|---|---|---|
| P-1 | A separate Astra ruling on the real-credit row | The ruling text, issued by the Astra path. This file is not that ruling | `DECISION_REQUIRED · Astra` | Task 005 decision 6 `:72`. `AGENTS.md:30-31` |
| P-2 | Explicit User approval that names the product, the jurisdiction, the caps, and the window | A User merge or other explicit OK that contains those names. The names are not in this file. Caps and the window stay empty until Astra supplies the values (C-4 and O-9) and the User writes them into that later approval | `DECISION_REQUIRED · User` | Program decisions §5 `:110`. Roadmap `:214` |
| P-3 | Non-author exact-HEAD review, and audits at the A3 floor | Review and audit records for the proposal that asks for the lift. This file's author check is not that review | Required by `AGENTS.md` §10 and §12. Audit floor on this node is A3. Unmet for any lift proposal, because no such proposal exists | `AGENTS.md` §6, §10, §12. Delegation table `:78` |
| P-4 | The sibling real-funds unlocks are satisfied first, or in the same explicit approval, and are not treated as already done | Evidence for the rows in §2: real PG, bank, and KYC; and, where the proposal needs them, the public endpoint. Sui, the token lock, and R2 are not implied | Each sibling keeps its own owner in §2. None are satisfied here | Program decisions §5 `:109-116` |
| P-5 | Any change of product scope voids earlier review | The later proposal says so, and new review is required after a scope change | `DECISION_REQUIRED · User` for the scope (see §3). Review rule: `AGENTS.md` §6 (an earlier SHA's CI does not transfer) | §3. `AGENTS.md` §6 |
| P-6 | An unmet criterion re-locks | The later proposal states that a failed or withdrawn criterion puts the lock back. This document does not open the lock, so there is nothing to re-lock today | `DECISION_REQUIRED · User` to accept that sentence in the later proposal | Program decisions §1 `:25`. Task 005 `:175` |

## 5. Mock-to-real gap table

Current state is the mock contract. The class of external evidence that would let a lift treat a flag as true is not defined here. Defining it would be a possible contract change. That definition is `DECISION_REQUIRED · Astra`. This document adds no protocol command. F04 §7 `:300-301` already says a new protocol command outside the existing replayable set is `DECISION_REQUIRED · Astra`.

The fourteen flags F04 §1 `:63-67` keeps always false:

| Flag | Current state | Class of external evidence a lift would need | Owner |
|---|---|---|---|
| `funds_executed` | Always false. A successful mock call cannot set it true (F04 §1 `:63-67`). `DISBURSE`, `REPAY`, and `DEBIT` return `REAL_FUNDS_FORBIDDEN` (F04 §3 `:131`) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `license_granted` | Always false (same §1). `LICENSE` is `CREDIT_PRODUCT_UNDEFINED` (F04 §3 `:132`) | Not defined. Defining it is `DECISION_REQUIRED · Astra`. A legal conclusion about a licence stays L-2, `UNDETERMINED · external counsel` | `DECISION_REQUIRED · Astra` |
| `regulated_product` | Always false (same §1) | Not defined. Defining it is `DECISION_REQUIRED · Astra`. Product characterization stays L-1 | `DECISION_REQUIRED · Astra` |
| `collateral_perfected` | Always false (same §1). `PERFECT` is `CREDIT_PRODUCT_UNDEFINED` | Not defined. Defining it is `DECISION_REQUIRED · Astra`. Perfection stays L-4 | `DECISION_REQUIRED · Astra` |
| `priority_bound` | Always false (same §1). Order of notes is not seniority (F04 §3 `:118-119`) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `disposal_controlled` | Always false (same §1) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `revenue_assigned` | Always false (same §1) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `admission_granted` | Always false (same §1). A credit memo is not an admission right (F04 §0 `:47`) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `legal_debtor_bound` | Always false (same §1). `beneficiary_role` is a label (F04 §5.2 `:209`) | Not defined. Defining it is `DECISION_REQUIRED · Astra`. Parties stay L-3 | `DECISION_REQUIRED · Astra` |
| `bank_debit_observed` | Always false (same §1) | Not defined. Defining it is `DECISION_REQUIRED · Astra`. The PG/bank lock stays §2 | `DECISION_REQUIRED · Astra` |
| `external_pledge_complete` | Always false (same §1) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `durable` | Always false (same §1). The acceptance machine's journal is not a durable ledger (F04 §7.9 `:508`) | Not defined. Defining it is `DECISION_REQUIRED · Astra`. O-3 does not set this flag | `DECISION_REQUIRED · Astra` |
| `repayment_observed` | Always false (same §1). Release is not repayment (F04 §3 `:123`). A mock `repay` note leaves the flag false (F04 §7.2 `:347`) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `interest_defined` | Always false (same §1) | Not defined. Defining it is `DECISION_REQUIRED · Astra`. APR and fees stay C-6 | `DECISION_REQUIRED · Astra` |

Flags the acceptance machine also keeps false:

| Flag | Current state | Class of external evidence a lift would need | Owner |
|---|---|---|---|
| `underwriting_executed` | False after `approve` (F04 §7.1 `:334-335`) | Not defined. Defining it is `DECISION_REQUIRED · Astra`. The policy stays R-1 | `DECISION_REQUIRED · Astra` |
| `kyc_executed` | False after `approve` (same sentences) | Not defined. Defining it is `DECISION_REQUIRED · Astra`. The duty stays L-6 | `DECISION_REQUIRED · Astra` |
| `economic_finality_claimed` | False after a draw note and a repay note (F04 §7.9 `:503`) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `ownership_mutated` | False. Credit commands do not transfer a ticket (F04 §7.9 `:505`) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |
| `ticket_ownership_authoritative` | False (same non-claim) | Not defined. Defining it is `DECISION_REQUIRED · Astra` | `DECISION_REQUIRED · Astra` |

## 6. Options, consequences, recommendation

The recommendation is a suggestion. It is not acted on. The builder does not merge, does not edit a lock row, and does not start a later node.

If the User merges without edits, only O1 is adopted; every `DECISION_REQUIRED`/`UNDETERMINED` value stays empty; the lock stays.

### O1. Adopt the full criteria set

Adopt §4 groups L, C, R, O, and P as the necessary conditions a later lift proposal must meet.

Consequence in plain terms: the checklist becomes the list people have to satisfy before anyone may even ask to open real credit. Opening still needs a separate Astra ruling and a separate explicit OK from the User. Merging this file does not open anything, does not fill in a blank amount or a legal answer, and does not hire a reviewer.

This is the suggestion.

### O2. Adopt a legal-only gate

Adopt only group L. Leave C, R, O, and P out of this document.

Consequence in plain terms: this file would carry only the lawyer's checklist. Capital, risk, operations, and the approval steps would not be conditions written here. The lock sentence already on the books still asks for a legal review and an Astra ruling and an explicit User OK. This option would not delete that sentence. A reader could mistake a lawyer's memo for permission to lend. That mistake is why O1 is the suggestion.

### O3. Defer

Adopt no criteria list.

Consequence in plain terms: Task 005's open question stays open. Mock work still must not be read as a lift. The next person who wants a checklist has to write one later, under a new decision. The lock stays as it is written today.

### O4. State a permanent prohibition

Restate real credit as forbidden with no unlock path.

Consequence in plain terms: real credit would be written as never allowed. The program decisions already say a lock is a door that can open when the evidence exists, not a permanent ban (`PROGRAM_DECISIONS_20260928.md:25`). Choosing O4 would be a different decision from that one. This file does not make that change.

## 7. What this document does not authorize

This document authorizes none of the following. A later proposal can ask. This file does not grant the list.

The §5 locks, in the words already adopted (`PROGRAM_DECISIONS_20260928.md:108-117`):

1. 커널 잠금 blob 2개. 해제 조건: 별도 사람 결정. 권장 경로는 잠금 파일을 그대로 두고 새 버전 crate를 추가하는 것(§2.2). This file does not change either blob (`AGENTS.md` §4 `:91-105`).
2. 실자금, 실 PG·은행·KYC 호출. 해제 조건: 토스 프로파일의 미확인 항목(MID, 가맹 범위, 웹훅 서명) 확인, sandbox 적합성 증거, 사용자 명시 승인. Not satisfied here.
3. 실제 여신·규제 금융. 해제 조건: 법률·인허가 검토와 Astra·사용자 명시 승인(Task 005 결정 6). This file is the criteria list the roadmap pointed at that row. It is not the legal review, not the Astra ruling, and not the explicit OK. The row stays locked.
4. Sui testnet 배포. 해제 조건: 키 관리 방식 결정 문서와 사용자 승인. localnet 시험은 이미 허용. Not satisfied here. This file does not deploy to testnet.
5. Sui mainnet 실행. 해제 조건: Move 독립 감사, testnet 운용 증거, 키 관리 운영 책임자, 사용자 승인. Not satisfied here.
6. 공개 운영 엔드포인트. 해제 조건: 인증, TLS, 운영 책임자, 장애 대응 계획, 사용자 승인. Not satisfied here.
7. R2, 자체 복제·합의·저장 엔진. 해제 조건: §9 비교가 기성 backend의 구체적 부족을 입증하고, 비용·검증·운영 책임이 문서화되고, 사용자가 승인. Not satisfied here.
8. (a) PR #11 통합. 해제 조건: 수명 계약 잔여 통합량 재산정과 사용자 승인. Not satisfied here. This file does not integrate that pull request.
9. 새 coin/TIX 모듈. 해제 조건: ADR과 Astra 재결정(Task 005 결정 5). Not satisfied here. No new coin or TIX module is added.
10. schema·SDK 안정 1.0, KTX→KIX 일괄 치환. 해제 조건: Track K 3단계 재승인. Not satisfied here. This file does not rename or publish a stable SDK.

Also unauthorized, because they are the same locks in other words (`AGENTS.md:111-114`): production PG or bank calls, live-money execution, live Sui production execution, a public operational endpoint, and a production runtime. No secret, credential, or key is created. No new protocol command is added. `CREDIT_ADVANCE_F04.md` is not edited.

Index and plan back-links are outside this record. `docs/README.md`, `DEVELOPMENT_PLAN.md`, and `docs/status/CURRENT_CAPABILITY_REGISTER.md` stay as they were. A later sync node owns those pointers. ADR-0003 §7 said the same about its own back-links.

## 8. Register

No row below is closed by this document. Product policy values and new protocol commands are `DECISION_REQUIRED · Astra`. Legal, tax, and accounting answers stay `UNDETERMINED` with the owner named. This document does not fill any of them.

| Item | Class | Owner | What this document does |
|---|---|---|---|
| L-1 through L-7, L-10, L-11 | `UNDETERMINED` | External counsel. The User names the starter (D-E, I10) | Lists the questions. States no conclusion and cites no statute |
| L-8 tax and accounting | `UNDETERMINED` | External tax/accounting. The User names the owner (D-E) | States no treatment |
| L-9 who may contact a regulator | `DECISION_REQUIRED · User` | User | Names no one and sends nothing |
| C-1 source of lent funds | `DECISION_REQUIRED · User` | User | Does not name a source. Does not treat `confirmed_cash` or `recovery_due` as funding |
| C-2 capital requirement | `UNDETERMINED` | External counsel/accounting | States no amount |
| C-3 reserves and loss attribution | `DECISION_REQUIRED · Astra` | Astra | States no reserve and no split |
| C-4 exposure caps | `DECISION_REQUIRED · Astra` | Astra | States no cap |
| C-5 custody and segregation | `UNDETERMINED` | User, bank, and Toss (I03) | Does not confirm MID, merchant scope, or webhook signing |
| C-6 APR and fees | `DECISION_REQUIRED · Astra` | Astra | States no rate and no fee |
| C-7 refund-versus-advance bearer | `DECISION_REQUIRED · Astra` | Astra, after the settlement-policy dependency | Leaves `UNDEFINED` as it is |
| R-1 through R-8 | `DECISION_REQUIRED · Astra` | Astra | States no underwriting rule, limit, or loss policy |
| R-6 and every §5 flag's external evidence | `DECISION_REQUIRED · Astra` | Astra | Does not define the evidence and adds no command |
| O-1 operator and backup | `DECISION_REQUIRED · User` | User | Does not appoint the I11 approvers or anyone else |
| O-3 real-credit backend adoption | `DECISION_REQUIRED · User` | User | Does not adopt a backend and does not unlock R2 |
| O-3 restore evidence (I13) | `UNDETERMINED` | User / operations owner | Does not close I13 |
| O-4 Toss sandbox facts | `UNDETERMINED` | Toss | Makes no provider call |
| O-6 service levels and O-9 pilot values | `DECISION_REQUIRED · Astra` | Astra | States none |
| O-8 delegated credit execution | `DECISION_REQUIRED · User` | User, via `ai-delegation-execution-decision` | Does not enable it |
| P-1 Astra ruling | `DECISION_REQUIRED · Astra` | Astra | Does not issue the ruling |
| P-2 explicit lift approval | `DECISION_REQUIRED · User` | User | Does not approve a lift |
| Product scope (§3) | `DECISION_REQUIRED · User` | User | Names no scope as chosen |
| Reviewer starter (D-E) | `DECISION_REQUIRED · User` | User | Names no starter |
| Final lift | `DECISION_REQUIRED · User` | User, and only after P-1 | Does not lift |
| Astra-gate cell mismatch (§1) | Recorded, not resolved | Not assigned by this document | Follows `user_merge: true` and edits no source |

## 9. Coverage (AGENTS §7), classification (§8), non-claims, references

### Coverage (`AGENTS.md` §7)

Existing deterministic checks already keep the mock on the forbidden side of real funds. This node adds no test.

| Requirement | Coverage | Action here |
|---|---|---|
| `REAL_FUNDS_FORBIDDEN` for disbursement, repayment, and debit | Sufficient for the mock. `reference/credit_advance_f04/test_mock_credit.py` `CreditAdvanceMockTests.test_execution_attempts_do_not_change_the_note` (`:318-344`). `reference/credit_advance_f04/test_credit_fsm.py` `CreditFsmTests.test_unsupported_product_and_real_funds_do_not_change_state` (`:729-795`) | Cited. Not duplicated |
| The fourteen always-false flags | Sufficient for the mock. `test_mock_credit.py` `FALSE_FLAGS` (`:15-30`) asserted in `test_note_reserves_unpaid_face_without_funds_or_license` (`:86-87`). A forged `funds_executed` is rejected in `test_forged_faces_and_bad_inputs_are_rejected` (`:349-352`) | Cited. Not duplicated |
| `underwriting_executed`, `kyc_executed`, `economic_finality_claimed`, `funds_executed`, `bank_debit_observed`, `repayment_observed`, `interest_defined` stay false on the acceptance machine | Sufficient for the mock. `test_credit_fsm.py` `assert_not_lending` (`:106-116`), used by `test_offer_approve_draw_repay_and_close_are_mock_ledger_only` (`:145-147`) | Cited. Not duplicated |
| Credit commands do not mutate ticket ownership | Sufficient for the mock. `test_credit_fsm.py` `test_credit_commands_do_not_mutate_resale_ownership` (`:876`, assertions `:936-937`) | Cited. Not duplicated |
| A real-credit lift, a licence, or an external flag becoming true | Not covered. The contract leaves those empty on purpose (F04 §5, §5.4, §7.9) | No test added. The gap is the missing ruling, the missing User OK, and the undefined evidence in §5 |

### Classification (`AGENTS.md` §8)

A. The written lock matches the sources in §2. The mock's always-false flags and `REAL_FUNDS_FORBIDDEN` match that lock. This document does not change runtime behavior.

B. Contract undefined, recorded and not invented:

- Which external fact would make any §5 flag true.
- Which single product scope a later lift would name.
- Every legal, tax, accounting, capital, cap, rate, reserve, service level, and pilot value in §4 and §8.

This document does not invent those semantics and does not amend `CREDIT_ADVANCE_F04.md`.

C. No explicit contract violation. No locked file is changed. The real-credit row is still locked, which is what the contract says. No merge blocker of class C is filed.

### Non-claims

This document does not claim that the criteria are satisfied, that merging it lifts the lock, or that a completed checklist lifts the lock by itself. It does not claim that real PG, bank, KYC, a public endpoint, Sui testnet or mainnet, a token module, or R2 is unlocked or satisfied. It states no legal, licensing, tax, or accounting conclusion. It states no amount, cap, rate, reserve, service level, or pilot size. It states no claim of production readiness, durability, bank exactly-once, or chain finality. It states no claim that exact-head CI has run for a head that includes this file. A documentation-only green is not full verification. The author's check is not an independent review.

### References

Pinned to observed `origin/main` `9b12626b61765f8c8d1ee6ad07d528c4b7eb20c1`.

- `AGENTS.md` §4 `:91-105`; `:7-8`; `:13-16`; `:30-33`; §5 `:111-114`; §6; §11; §14.
- `docs/tasks/TASK_005_MEGA_COMMERCE_PROGRAM.md:35`, `:72`, `:129`, `:131`, `:175`.
- `docs/decisions/PROGRAM_DECISIONS_20260928.md` §0 `:13-14`, `:18`; §1 `:25`; §2.1 `:49-50`; §2.2 `:60`; §5 `:108-116`.
- `docs/decisions/PROGRAM_ROADMAP_20260930.md` §0 `:14-15`; §1 `:26`, `:28`, `:45`; R-6 `:39`; §3.6 `:139-142`; §5 `:213-220`.
- `docs/decisions/AUTHORITY_MODEL_1.md:12-13`.
- `docs/contracts/CREDIT_ADVANCE_F04.md:18-19`, `:47-49`, `:63-67`, `:79`, `:87-88`, `:108`, `:112`, `:118-119`, `:123`, `:131-132`, `:164`, `:168-169`, `:174`, `:193`, `:209-213`, `:261`, `:263`, `:268`, `:281`, `:300-301`, `:327`, `:334-335`, `:347`, `:503-511`.
- `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:195-196`.
- `docs/contracts/PG_TOSS_CARD_PROFILE.md:7`, `:170-171`.
- `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md:27`, `:29`, `:34-35`, `:37`, `:107`.
- `docs/status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md:63`.
- `docs/aiops/PROGRAM_ASTRA_DELEGATION.md:3`, `:78`.
- `docs/aiops/PROGRAM_EXPANSION_20261002_KO.md:435-437`, `:446`, `:463`.
- `docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md`.
- `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md` §6 and §7.
- `docs/adr/0003-coin-tix-lock-localnet-re-ruling-request.md` §7 (back-links belong to a later sync).
- `.aiops/program.json:652-660`.
- `reference/credit_advance_f04/test_mock_credit.py:15-30`, `:86-87`, `:318-344`, `:349-352`.
- `reference/credit_advance_f04/test_credit_fsm.py:106-116`, `:145-147`, `:729-795`, `:876`.
