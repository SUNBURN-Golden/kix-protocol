요약. 이 문서는 testnet 배포, mainnet 배포, 토큰 발행을 열 조건을 제안만 한다. 세 가지는 잠긴 채로 남는다.
권고는 세 관문의 조건 목록을 채택하는 것이다. 그 권고는 실행하지 않는다. 체크리스트를 채우는 일도 활성화가 아니다.
효력은 사용자가 이 문서를 병합할 때에만 생긴다. 수정 없이 병합하면 권고만 채택되고, 잠금은 풀리지 않는다.

# Operational activation decision proposal (2026-10-09)

Node `tl-5-decision`. No issue. No file under `docs/tasks/` names this node. This is a User decision document. It lists conditions for three separate activations: testnet deployment, mainnet deployment, and token issuance. It stops at criteria. The three stay locked.

Date: 2026-10-09.
Status: proposed. This is a User decision document. It takes effect only when the User merges it ([roadmap](PROGRAM_ROADMAP_20260930.md) §1 `:26`; writing alone has no effect, roadmap §0 `:14-15`). The builder does not merge this file and does not act on the recommendation in §6.

## 0. Status and effect

Effect rule, in plain terms. A draft in the repository does nothing to a lock. The roadmap says writing that document alone creates no effect (`PROGRAM_ROADMAP_20260930.md:14-15`). Section 1 of the same file says `user_merge` stays the User's and that the delegation table is the current merge boundary (`:26`). [Program decisions](PROGRAM_DECISIONS_20260928.md) §0 (`:13-14`) uses the same rule: writing alone creates no effect, and effect is the User's merge. This file uses that rule for testnet deployment, mainnet deployment, and issuance.

It takes effect only when the User merges it. The builder does not merge it and does not act on the recommendation in §6. The builder's check is not an independent review and is not a non-author exact-HEAD review (`AGENTS.md` §6, §14). This session has no task issue and no `ASTRA_TASK_KEY_V1` line, so the program-mode precedence at `AGENTS.md:13-16` does not apply here. Architecture rulings stay with Claude Fable through the central `aiops-fable` tool (`AGENTS.md:30-31`, User decision M5, 2026-09-30). This session does not issue one.

What a merge of this file adopts is only the criteria list in §4, and only if the User merges the file without edits (§6). That merge does not deploy to testnet, does not deploy to mainnet, and does not issue a token. No completed row activates a gate. The blueprint's own last row for this work says the activation condition is a separate explicit approval and that activation is not this work's output (`optional-native-token-v1/README.md:546`, "착수 조건과 **별개**의 명시 승인. 활성화는 이 작업의 산출물이 아니다"). The acceptance row (`:543`) names both an explicit User approval and a decision document. This file is the decision document. The explicit approval that would open a gate is P-3 in §4. An unedited merge does not serve as P-3.

A completed checklist is not approval. The recommendation in §6 is not approval.

## 1. Base and evidence

Each identifier below was read on the fetched base. None of them is a CI result for this file. CI from an earlier SHA does not transfer to a later SHA (`AGENTS.md` §6, §11). This session makes no CI claim for `18b80a79614b3a5866f61728b0935294360cfa85` or for any parent. Local commands are in [the validation record](../../validation/2026-10-09-tl-5-decision/README.md). They are not exact-head CI.

Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`: `18b80a79614b3a5866f61728b0935294360cfa85`. The branch is `agent/kix-tl-5-decision`. That commit is the merge of pull request #165. Program mode would name the branch `astra/tl-5-decision`. This node has no issue, and no issue names a branch. This session does not rename the branch. This session does not commit, so there is no implementation commit SHA.

Locked blobs, checked before this file was added:

| File | Required blob | Observed |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |

`reference/v0.3-rc1/**` was not modified.

Node fields read from [`.aiops/program.json`](../../.aiops/program.json) `:627-637`: `depends_on` is `tl-4` and `tl-legal-brief`; `audit_floor` is A3; `user_merge` is true; `astra_auto_merge` is false. That object has no `astra_gate` key.

Astra-gate mismatch, recorded and not resolved:

| Place | What it says on this base |
|---|---|
| Dispatch header for this node | `astra_gate: None`, `user_merge: true` |
| Roadmap §3.5 `:133` | Astra gate ARCHITECTURE, merge **사용자** |
| Node object `.aiops/program.json:627-637` | no `astra_gate` key |
| [Delegation table](../aiops/PROGRAM_ASTRA_DELEGATION.md) `:76` | contract change NO, merge 대표님, audit floor A3. The document status line (`:3`) says the table is a non-executable draft |

The merge actor in the roadmap row, the delegation row, and `user_merge: true` is the User. This file does not pick a winner among the gate cells and does not edit those sources. It follows `user_merge: true`.

Sibling decisions, re-checked on this base. No file in the tree is the `testnet-key-management-decision`. No file is the `rs-5-decision`. The capability register still marks that pair not covered (`CURRENT_CAPABILITY_REGISTER.md:151`). That matches the facts in §3. It does not contradict them.

Documents this section relies on, all present on the same base:

| Input | What it is on this base |
|---|---|
| [TL-4 record](TL4_THREAT_MODEL_20261009.md) | Author-side harness. Not independent review (`:11`, `:19`) |
| [TL-2 record](TL2_DOES_NOT_OPEN_20261009.md) | TL-2 does not open. No package |
| [TL-3 on-chain record](TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md) | The on-chain part does not open. No package |
| [Legal brief](../status/TOKEN_LEGAL_REVIEW_BRIEF_KO.md) | Questionnaire only. Not sent (`:9`) |
| [ADR-0003](../adr/0003-coin-tix-lock-localnet-re-ruling-request.md) | Re-ruling request. §5 `:142` says the re-ruling is not yet issued |

## 2. What is locked and where it is written

The locks this document is about are Sui testnet deployment, Sui mainnet execution, and token issuance. Neighbouring locks stay on their own rows. A sentence in this file cannot substitute for any of them.

| Source | What it says |
|---|---|
| [Program decisions](PROGRAM_DECISIONS_20260928.md) §5 `:111` | "Sui testnet 배포 \| 키 관리 방식 결정 문서와 사용자 승인. localnet 시험은 이미 허용" |
| Same file `:112` | "Sui mainnet 실행 \| Move 독립 감사, testnet 운용 증거, 키 관리 운영 책임자, 사용자 승인" |
| Same file `:116` | "새 coin/TIX 모듈 \| ADR과 Astra 재결정(Task 005 결정 5)" |
| Same file §1 `:25` | "잠금은 영구 금지가 아니다. 증거가 모이면 여는 문이며, 각 잠금의 해제 조건을 §5에 적는다." |
| [Roadmap](PROGRAM_ROADMAP_20260930.md) §5 `:215` | "Sui testnet 배포 \| 키 관리 결정 문서와 사용자 승인 \| `testnet-key-management-decision`(사용자)" |
| Same file `:216` | "Sui mainnet \| 독립 Move 감사, testnet 운용 증거, 운영 책임자, 사용자 승인 \| `rs-5-decision`, `tl-5-decision`(사용자)" |
| Same file `:220` | "새 coin/TIX 모듈 \| ADR과 Astra 재결정, 잠금 변경은 사람 결정 \| `tl-coin-lock-adr`(사용자) 뒤 localnet `tl-2`만" |
| Same file `:221` | "토큰 발행·판매·분배·풀·바이백, 스테이블코인, 토큰 가스, 자체 체인 \| 승인되지 않음 \| 없음" |
| Same file `:28` | Product policy and new commands stop at `DECISION_REQUIRED`. Legal, accounting, and provider answers stay `UNDETERMINED` with an owner. No conclusion is stated here. The §5 locks stay. The only coin/TIX exception is localnet `tl-2`, and only after an Astra re-ruling and the User's merge of `tl-coin-lock-adr`. |
| [ADR-0002](../adr/0002-token-layer-scope-and-limits.md) §3 S3 `:46` | Operational deployment and issuance are a judgment at TL-5. Entry wants external review finished, the §5 testnet and mainnet conditions, and an explicit User authorization. Forbidden: automatic progression. |
| Same file §4 `:57-58` | Testnet deployment, mainnet execution, key generation, and repository secrets stay unauthorized. |
| [Blueprint](../blueprints/optional-native-token-v1/README.md) S3 `:390` | "S3 운영 배포·발행 \| mainnet 배포, 발행 (TL-5) \| 아래 외부 검토 완료, 프로그램 결정 §5의 testnet·mainnet 조건(키 관리 결정 문서, Move 독립 감사, testnet 운용 증거, 운영 책임자), **사용자의 명시 승인** \| 자동 진행" |

`rs-5-decision` and `tl-5-decision` are both named on roadmap `:216`. One document does not satisfy the other. Rights-scale adoption and token activation stay separate decisions.

Neighbouring locks stay separate. Opening one of the three gates would not open these:

| Lock, quoted from program decisions §5 | Unlock, quoted from the same row | Where else it is written |
|---|---|---|
| 실자금, 실 PG·은행·KYC 호출 | 토스 프로파일의 미확인 항목(MID, 가맹 범위, 웹훅 서명) 확인, sandbox 적합성 증거, 사용자 명시 승인 (`:109`) | Roadmap §5 `:213` |
| 실제 여신·규제 금융 | 법률·인허가 검토와 Astra·사용자 명시 승인(Task 005 결정 6) (`:110`) | Roadmap §5 `:214`. Criteria live in [the F04 document](F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md). That file is not this one |
| 공개 운영 엔드포인트 | 인증, TLS, 운영 책임자, 장애 대응 계획, 사용자 승인 (`:113`) | Roadmap §5 `:217` |
| R2, 자체 복제·합의·저장 엔진 | §9 비교가 기성 backend의 구체적 부족을 입증하고, 비용·검증·운영 책임이 문서화되고, 사용자가 승인 (`:114`) | Roadmap §5 `:218`. `AGENTS.md:111` |

[Model 1](AUTHORITY_MODEL_1.md) `:12-13` already says a chain record does not by itself guarantee bank funds, a contractual debt, or performance of the show. An issuance decision does not change that sentence.

## 3. Evidence today against blueprint line 544

Blueprint TL-5 (`:536-546`) asks for a judgment, not for the deployment or the issuance itself. The evidence row (`:544`) says: "독립 검토 보고, TL-L의 서면 결과, 키 관리 결정 문서, Move 독립 감사, testnet 운용 기록(프로그램 결정 §5)". None of those items exists on this base. The named operator in program decisions `:112` and roadmap `:216` is also absent. So are the Astra re-ruling, E-1, and a meaning for "키 생성 없음(localnet)".

| Item | Present? | Source on this base | Owner |
|---|---|---|---|
| Independent review report | No | [TL-4](TL4_THREAT_MODEL_20261009.md) `:11` says the author is the builder and the record is not independent review. `:19` says the blueprint acceptance for independent verification is not closed | Unmet. No independent reviewer is named |
| Written TL-L result | No | [The brief](../status/TOKEN_LEGAL_REVIEW_BRIEF_KO.md) `:9`: "상태: 질문서만이다. 전송하지 않았다." No written reply is in the tree | `UNDETERMINED · external review`. Who starts the review is D-E, `UNDETERMINED · User` |
| Key-management decision document | No | No such file. Roadmap `:215` names `testnet-key-management-decision`, which is not on this base | `DECISION_REQUIRED · User` |
| Independent Move audit | No | No package exists to audit. [TL-2](TL2_DOES_NOT_OPEN_20261009.md) and [TL-3 on-chain](TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md) both say they do not open | Unmet |
| Testnet operation records | No | TL-4 `:117`: "testnet·mainnet 배포 기록은 없다" | Unmet. Producing them would be the testnet lock |
| Named operator | No | Program decisions `:112` "키 관리 운영 책임자". Roadmap `:216` "운영 책임자". No person is named | `DECISION_REQUIRED · User` |
| Astra re-ruling | No | ADR-0003 §5 `:142`: "Status: not yet issued" | `DECISION_REQUIRED · Astra` |
| E-1 approver and custodian | No | [Authority contract](../contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md) `:112` leaves the token approver and custodian empty. Status: open. Owner on that row: `DECISION_REQUIRED · User` | `DECISION_REQUIRED · User` |
| Meaning of "키 생성 없음(localnet)" | No | Blueprint TL-2 `:509`. ADR-0003 Q3 `:94-96` leaves the meaning unresolved and does not permit key generation | `DECISION_REQUIRED · Astra` |

Dependency gap, recorded and not closed. This node's `depends_on` is `tl-4` and `tl-legal-brief`. Both documents are on this base, so the dispatch dependency is satisfied by the brief and by the TL-4 record. The blueprint precondition is "TL-L의 결과" (`:541`) and the TL-L row says the review must finish before TL-5 is entered (`:558`, "이 검토가 끝나기 전에는 TL-5로 진입할 수 없다"). The brief is not that result. This file does not treat the questionnaire as a written opinion, and it does not treat the author-side harness as independent review.

Under the TL-0 recommendation there is nothing on-chain to deploy or issue. [Role and supply](../contracts/TOKEN_ROLE_AND_SUPPLY.md) §3 D and §11 recommend F4 only for stage 1, and say that F4-only does not open TL-2. No node on this base has selected F1, F2, or F3 as the implementation representation.

## 4. Gates and criteria

Three gates. `G-T` is testnet deployment. `G-M` is mainnet deployment. `G-I` is token issuance. Issuance is not deployment. A failed or withdrawn condition re-locks that gate (P-5). No cell states a supply, a cap, a quorum, a timelock, a service level, a date, or a cost. An empty cell stays empty.

Program decisions `:111` is the written unlock for testnet: a key-management decision document and User approval. The legal rows below are not in that sentence. This file does not add them to `G-T`. Blueprint S3 `:390` requires the external review before mainnet deployment and issuance. Those legal rows apply to `G-M` and `G-I` as that sentence already says. They are not a new rule.

### L. Outside review (the brief's LB-01 through LB-11, and D-E)

This group states no legal conclusion, no licensing conclusion, and no tax or accounting treatment. The brief was not sent.

| ID | Criterion | Gates | Evidence a later proposal would bring | Owner and status | Source anchor |
|---|---|---|---|---|---|
| D-E | Who starts the outside review, and when | Precondition of the L rows. Not itself a gate | A User record that names the starter. This file names no person and no date | `UNDETERMINED · User`. The act of naming the starter is `DECISION_REQUIRED · User` | Brief `:31`. Roadmap `:46`. Scope decision `:179`. Blueprint TL-L `:557` |
| L-01 | A written view of legal character, for the facts the brief lists, in a named jurisdiction | `G-M`, `G-I` | A dated written opinion. The character is not filled here | `UNDETERMINED · external review` | Brief LB-01. Blueprint §10.2 item 1 |
| L-02 | A written view of how issuance and distribution would be done. The blueprint does not cover a sale | `G-I` | The same kind of opinion. This file adopts no distribution plan | `UNDETERMINED · external review` | Brief LB-02. Roadmap `:221` |
| L-03 | A written view of the reward's contractual character, including withdrawal | `G-I` | The opinion. No terms draft is in the tree | `UNDETERMINED · external review` | Brief LB-03 |
| L-04 | A written view of deposit, slashing, set-off, and insolvency position | `G-I` | The opinion. No collateral asset is chosen | `UNDETERMINED · external review` | Brief LB-04 |
| L-05 | Accounting treatment | `G-I` | A written conclusion from the owner the User names. No amount is stated | `UNDETERMINED · external review` | Brief LB-05. Roadmap D-E `:46` |
| L-06 | Tax treatment of reward, burn, and any buyback the design does not define | `G-I` | A written conclusion. No treatment is chosen | `UNDETERMINED · external review` | Brief LB-06 |
| L-07 | Personal-data and AML/KYC duties, if any | `G-M`, `G-I` | The opinion. A real KYC call stays the separate lock in §2 | `UNDETERMINED · external review` | Brief LB-07. Program decisions `:109` |
| L-08 | Whether a partner contract allows a token-related flow of funds | `G-I` | Partner confirmation. Not obtained here | `UNDETERMINED · external review` for the reading. Provider facts stay with the provider | Brief LB-08 |
| L-09 | The jurisdiction list, and a written view for those jurisdictions | `G-M`, `G-I` | The list from the User. The view from outside review. Neither is in this file | List: `DECISION_REQUIRED · User`. View: `UNDETERMINED · external review` | Brief LB-09 |
| L-10 | Governance responsibility and conflicts. The approver's name is E-1 | `G-I` | The opinion. The name stays empty until the User writes it | Opinion: `UNDETERMINED · external review`. Name: `DECISION_REQUIRED · User` | Brief LB-10. Authority contract `:112` |
| L-11 | Market circulation and exchange listing | None of `G-T`, `G-M`, `G-I` | The blueprint leaves this outside. A later adoption would be a separate review. This file does not adopt it | `UNDETERMINED · external review` if a later decision adopts it | Brief LB-11. Blueprint §10.2 item 11 |
| L-CB | The chargeback period | `G-I` | The provider's rule. No period is written | `UNDETERMINED · card/payment provider` | Blueprint `:376`. Role and supply `:280` |

### K. Keys and custody

This group creates no key, no secret, and no credential.

| ID | Criterion | Gates | Evidence a later proposal would bring | Owner and status | Source anchor |
|---|---|---|---|---|---|
| K-1 | A written key-management decision exists | `G-T`, `G-M` | The merged `testnet-key-management-decision`. It is not on this base | `DECISION_REQUIRED · User` | Program decisions `:111`. Roadmap `:215` |
| K-2 | Whether that shared key-management decision covers token keys | `G-T`, `G-M`, `G-I` | A User sentence that answers the question. This file does not answer it | `DECISION_REQUIRED · User` | ADR-0002 §6 `:89` assigns testnet key management to that node and does not say the decision covers token keys. Role and supply `:283` |
| K-3 | A named key-management operator | `G-M` | A User decision that names the person. This file names no one | `DECISION_REQUIRED · User` | Program decisions `:112`, "키 관리 운영 책임자" |
| K-4 | E-1 closed: a token approver and a token custodian, disjoint from ticket-side roles | `G-I` | A User record that closes E-1. While it is open, issuance and treasury spend do not start | `DECISION_REQUIRED · User` | Authority contract `:112`, `:114`, `:124` (`TL1-TK06-T5`) |
| K-5 | What "키 생성 없음(localnet)" allows inside a localnet run | Precondition of a localnet package. Not a gate | Astra's answer to ADR-0003 Q3. This file does not resolve it | `DECISION_REQUIRED · Astra` | ADR-0003 `:94-96`. Blueprint `:388`, `:509` |

Whether the person in K-3 is the same person as the operator in O-1 is `DECISION_REQUIRED · User`. The two source phrases are not the same words. This file does not merge them.

### V. Verification

| ID | Criterion | Gates | Evidence a later proposal would bring | Owner and status | Source anchor |
|---|---|---|---|---|---|
| V-1 | Something on-chain to deploy or issue. That means TL-2 reopened only through ADR-0003 option O2 plus an Astra re-ruling, for a representation the ruling names | `G-T`, `G-M`, `G-I` when the act is on-chain | The ruling text, the User's merge of that ruling's ADR, and a later package. None of these exists. F4-only means there is nothing on-chain to deploy or issue | Re-ruling: `DECISION_REQUIRED · Astra`. The User merge of the revised ADR: `DECISION_REQUIRED · User` | ADR-0003 §5 `:142`, O2 `:118-122`. TL-2 record. TL-3 on-chain record. Role and supply §3 D and §11 |
| V-2 | Independent verification of TK-1 through TK-12 by someone other than the author | `G-T`, `G-M`, `G-I` | A non-author review record. The TL-4 file is an author-side harness. It is not this evidence | Unmet. This file does not close it | Blueprint TL-4 `:531`. TL-4 `:11`, `:19`, `:95-103` |
| V-3 | An independent Move audit | `G-M`. Also `G-I` when the thing issued is a Move package | The audit report. There is no package, so there is no audit | Unmet | Program decisions `:112`. Roadmap `:216` |
| V-4 | `TL1-TK10-T1`: no S1 output without an S0 gate record | Precondition of S1. Not these three gates | A gate record this file does not confirm | The confirming judgment is TL-5's. This file does not make it | Authority contract `:280` |
| V-5 | `TL1-TK10-T2`: no S2 output without an S1 gate record | Precondition of S2. Not these three gates | Same | Same | Authority contract `:281` |
| V-6 | `TL1-TK10-T3`: no S3 output without an S2 gate record, a written TL-L result, and program decisions §5 | `G-M`, `G-I` | Those three inputs. All are absent. This file does not confirm the predicate | Same. The judgment stays open | Authority contract `:282`. Blueprint `:390` |

TK-1, TK-3, TK-2 parts T2 through T4, TK-5 parts V1 through V5, and TK-9's actual gas path are `NOT VERIFIABLE · no package` on the TL-4 record. TK-2 part T1 is a repository-boundary check. TK-5 part V6 is an author-side harness. None of those labels is an independent pass.

An F4-only point ledger is not a Move package. V-3 does not apply to it as a package audit. Using that ledger as a production runtime is the production-runtime lock in §7, not a substitute for V-3.

### O. Operations

No service level is stated in this group.

| ID | Criterion | Gates | Evidence a later proposal would bring | Owner and status | Source anchor |
|---|---|---|---|---|---|
| O-1 | A named operator for mainnet | `G-M` | A User decision that names the person. This file names no one | `DECISION_REQUIRED · User` | Roadmap `:216`, "운영 책임자" |
| O-2 | Testnet operation evidence | `G-M` only | Records of testnet operation. None exist. This file does not deploy to testnet in order to create them | Unmet. Creating them is the testnet lock | Program decisions `:112`. Roadmap `:216`. Blueprint `:544` |
| O-3 | An incident plan for the token activity | `G-M`, `G-I` | A written plan. Any service level inside it comes from a separate Astra decision. None is stated here | Who operates is `DECISION_REQUIRED · User` (O-1). Any service level is `DECISION_REQUIRED · Astra` | This proposal lists the plan. It does not import the public-endpoint unlock. That unlock's "장애 대응 계획" stays on program decisions `:113` |

### P. Approval

Each gate needs its own approval. Merging this file is not that approval.

| ID | Criterion | Gates | Evidence a later proposal would bring | Owner and status | Source anchor |
|---|---|---|---|---|---|
| P-1 | A separate Astra ruling on the gate being asked | `G-T`, `G-M`, `G-I`, each on its own | The ruling text, from the Astra path. This file is not that ruling. The coin/TIX re-ruling in V-1 is not a substitute | `DECISION_REQUIRED · Astra` | `AGENTS.md:30-31`. Blueprint `:390` |
| P-2 | Non-author exact-HEAD review, at the A3 floor | `G-T`, `G-M`, `G-I` | Review and audit records for the proposal that asks to open that gate. This author's check is not that review | Required by `AGENTS.md` §6, §10, and §12. Unmet, because no such proposal exists | `AGENTS.md` §6, §10, §12. Delegation table `:76` |
| P-3 | Explicit User approval that names the gate, separate from the merge of this file | `G-T`, `G-M`, `G-I` | A later User merge or other explicit OK that names the gate. The names of people, caps, and windows are not in this file | `DECISION_REQUIRED · User` | Blueprint `:546`. Program decisions `:111-112`. Roadmap `:216` |
| P-4 | Issuance approval is not a deployment approval | `G-I` | The `G-I` approval names issuance. A `G-T` or `G-M` approval does not count as it | `DECISION_REQUIRED · User` | Blueprint `:540`. Roadmap `:221` leaves issuance unapproved |
| P-5 | A failed or withdrawn condition re-locks that gate | `G-T`, `G-M`, `G-I` | The later approval says so. Nothing is open today, so there is nothing to re-lock | `DECISION_REQUIRED · User` to accept that sentence in the later approval | Program decisions `:25` |
| P-6 | Rights-scale adoption is a different decision | Not a substitute for any of these gates | `rs-5-decision` is not on this base. This file does not satisfy it. A later RS-5 file would not satisfy this one | Separate User decision | Roadmap `:216`. Capability register `:151` |

## 5. Dependency chain, as facts

The list is not a schedule. It authorizes no next step. The builder starts none of these items.

1. The TL-0 recommendation for stage 1 is F4, an off-chain point ledger. That recommendation says TL-2 does not open and that no new Move module is created (role and supply §3 D and §11).
2. ADR-0003 asks Astra for a re-ruling. Section 5 says the re-ruling is not yet issued. This session does not read a pull-request audit comment and does not assume one exists.
3. The TL-2 record says the node does not open. There is no package.
4. The TL-3 on-chain record says that part does not open. There is no reward-record schema.
5. The off-chain reference model is an in-memory F4 mock. It is not a deployment.
6. The TL-4 record is an author-side harness. It says it is not independent review, and that it does not close the blueprint acceptance for independent verification.
7. The legal brief is a questionnaire. It says it was not sent. No written TL-L result is in the repository. The blueprint says this work is not entered before that result (`:558`). This node's dispatch dependency is the brief, which is present. The blueprint's "TL-L의 결과" is not. This file does not treat the brief as the result.
8. No key-management decision document is on this base.
9. No `rs-5-decision` document is on this base. This file cannot satisfy that node. That node cannot satisfy this file.
10. E-1 is open. The authority contract says issuance and treasury spend do not start while it is open.
11. The meaning of "키 생성 없음(localnet)" is unresolved (ADR-0003 Q3).
12. An F4-only point ledger has no on-chain deployment and nothing on-chain to issue. Using that ledger as a production runtime would hit the production-runtime lock (`AGENTS.md:114`, [development plan](../DEVELOPMENT_PLAN.md) `:602`, "실자금·운영 발행은 미승인"). This file does not authorize that use.

## 6. Options, consequences, recommendation

The recommendation is a suggestion. It is not acted on. The builder does not merge, does not edit a lock row, and does not start a later node. A completed checklist does not activate testnet, mainnet, or issuance.

If the User merges this file without edits, only O1 is adopted. Every `DECISION_REQUIRED` and `UNDETERMINED` value stays empty. Every lock stays. No gate opens.

### O1. Adopt the criteria for all three gates

Adopt §4 as the list that has to be met before anyone may ask to open testnet deployment, mainnet deployment, or issuance.

Consequence in plain terms: the checklist becomes the list people have to satisfy before anyone may even ask to open one of those three. Opening still needs a separate Astra ruling and a separate explicit OK from the User for that gate. Merging this file does not deploy anything, does not issue anything, does not create a key, and does not fill in a blank number or an outside reviewer's answer.

This is the suggestion.

### O2. Adopt the testnet criteria only

Adopt only the rows whose gate column includes `G-T`. Leave the mainnet-only and issuance-only rows out of this document.

Consequence in plain terms: this file would carry a testnet checklist and would not carry the mainnet list or the issuance list. Mainnet and issuance would wait until testnet evidence exists, and someone would have to write their conditions later. The locks already on the books would still forbid testnet, mainnet, and issuance. A reader could mistake a testnet checklist for permission to deploy. That mistake is why O1 is the suggestion.

### O3. Defer

Adopt no criteria list.

Consequence in plain terms: the question stays open. The locks stay as they are written today. The next person who wants a checklist has to write one later, under a new decision.

### O4. State a permanent prohibition

Restate testnet deployment, mainnet deployment, and issuance as forbidden with no unlock path.

Consequence in plain terms: those three would be written as never allowed. The program decisions already say a lock is a door that can open when the evidence exists, not a permanent ban (`PROGRAM_DECISIONS_20260928.md:25`). Choosing O4 would be a different decision from that one. This file does not make that change.

## 7. What this document does not authorize

This document authorizes none of the following. A later proposal can ask. This file does not grant the list.

The §5 locks, in the words already adopted (`PROGRAM_DECISIONS_20260928.md:108-117`):

1. 커널 잠금 blob 2개. 해제 조건: 별도 사람 결정. 권장 경로는 잠금 파일을 그대로 두고 새 버전 crate를 추가하는 것(§2.2). This file does not change either blob (`AGENTS.md` §4 `:91-94`).
2. 실자금, 실 PG·은행·KYC 호출. 해제 조건: 토스 프로파일의 미확인 항목(MID, 가맹 범위, 웹훅 서명) 확인, sandbox 적합성 증거, 사용자 명시 승인. Not satisfied here.
3. 실제 여신·규제 금융. 해제 조건: 법률·인허가 검토와 Astra·사용자 명시 승인(Task 005 결정 6). Not satisfied here. The criteria for that row are a different document.
4. Sui testnet 배포. 해제 조건: 키 관리 방식 결정 문서와 사용자 승인. localnet 시험은 이미 허용. Not satisfied here. This file does not deploy to testnet. Adopting §4 does not deploy to testnet.
5. Sui mainnet 실행. 해제 조건: Move 독립 감사, testnet 운용 증거, 키 관리 운영 책임자, 사용자 승인. Not satisfied here. This file does not deploy to mainnet.
6. 공개 운영 엔드포인트. 해제 조건: 인증, TLS, 운영 책임자, 장애 대응 계획, 사용자 승인. Not satisfied here.
7. R2, 자체 복제·합의·저장 엔진. 해제 조건: §9 비교가 기성 backend의 구체적 부족을 입증하고, 비용·검증·운영 책임이 문서화되고, 사용자가 승인. Not satisfied here.
8. (a) PR #11 통합. 해제 조건: 수명 계약 잔여 통합량 재산정과 사용자 승인. Not satisfied here.
9. 새 coin/TIX 모듈. 해제 조건: ADR과 Astra 재결정(Task 005 결정 5). Not satisfied here. No new coin or TIX module is added. The localnet exception stays where roadmap `:28` and `:220` already put it, and that exception is not opened here.
10. schema·SDK 안정 1.0, KTX→KIX 일괄 치환. 해제 조건: Track K 3단계 재승인. Not satisfied here.

Also unauthorized, in the same sense (`AGENTS.md:114`, development plan `:602`): a production runtime, live-money execution, and live Sui production execution. No secret, credential, or key is created (`AGENTS.md:119`; blueprint `:388` and `:509`). No new protocol command is added. Issuance, sale, distribution, pools, buyback, a stablecoin, token gas, and an own chain stay out of the plan (roadmap `:221`).

This file does not edit the blueprint, the roadmap, the development plan, the capability register, any ADR, or any contract. `docs/README.md` gains one index row and one validation bullet so a reader can find this file. That index is not an approval. The register's TL-5 row stays not covered.

## 8. Register

No row below is closed by this document. Product policy values and new protocol commands are `DECISION_REQUIRED · Astra`. Legal, tax, accounting, and AML/KYC answers stay `UNDETERMINED` with the owner named. This document does not fill any of them. No supply, cap, quorum, timelock, service level, date, or cost appears as a value.

| Item | Class | Owner | What this document does |
|---|---|---|---|
| D-E, who starts the outside review | `UNDETERMINED` | User | Names no starter and no date |
| L-01 through L-04, L-07, L-08, L-10's opinion, L-11 | `UNDETERMINED` | External review | Lists the questions. States no conclusion |
| L-05 accounting and L-06 tax | `UNDETERMINED` | External review. The User names that owner (D-E) | States no treatment |
| L-09 jurisdiction list | `DECISION_REQUIRED · User` | User | States no list |
| L-09 opinion for that list | `UNDETERMINED` | External review | States no conclusion |
| L-10 approver name, which is E-1 | `DECISION_REQUIRED · User` | User | Names no approver and no custodian |
| L-CB chargeback period | `UNDETERMINED` | Card or payment provider | States no period |
| K-1 key-management decision | `DECISION_REQUIRED · User` | User | Does not write that decision |
| K-2 whether the shared decision covers token keys | `DECISION_REQUIRED · User` | User | Does not answer |
| K-3 key-management operator and O-1 mainnet operator | `DECISION_REQUIRED · User` | User | Names neither, and does not decide whether they are one person |
| K-4 E-1 | `DECISION_REQUIRED · User` | User | Does not close E-1. Issuance and treasury spend stay unstarted |
| K-5 meaning of the localnet key phrase | `DECISION_REQUIRED · Astra` | Astra | Does not resolve it and generates no key |
| V-1 package and Astra re-ruling | `DECISION_REQUIRED · Astra` for the ruling. `DECISION_REQUIRED · User` for the ADR merge | Astra, then the User | Does not rule and does not add a package |
| V-2 independent TK-1 through TK-12 verification | Unmet | A non-author reviewer, not named | Does not count the author-side harness as that review |
| V-3 independent Move audit | Unmet | Not named, because there is no package | Does not commission an audit |
| V-4, V-5, V-6 gate predicates | Open judgment | TL-5 is the confirming judgment. This file does not make it | Does not confirm `TL1-TK10-T1`, `T2`, or `T3` |
| O-2 testnet operation evidence | Unmet | The testnet lock stays in §2 | Does not deploy |
| O-3 incident plan | `DECISION_REQUIRED · User` for the plan. `DECISION_REQUIRED · Astra` for any service level | User and Astra | States no service level |
| P-1 Astra ruling on a gate | `DECISION_REQUIRED · Astra` | Astra | Does not issue the ruling |
| P-2 non-author exact-HEAD review | Unmet | Required by `AGENTS.md`. Not this author | Does not count this check as that review |
| P-3 explicit approval per gate | `DECISION_REQUIRED · User` | User | Does not approve `G-T`, `G-M`, or `G-I` |
| P-4 issuance separate from deployment | `DECISION_REQUIRED · User` | User | Does not treat a deployment approval as issuance |
| P-5 re-lock | `DECISION_REQUIRED · User` | User, in a later approval | Does not open a gate, so there is nothing to re-lock |
| P-6 RS-5 | Separate decision | User, in `rs-5-decision` | Does not satisfy RS-5, and RS-5 would not satisfy this file |
| Supply, caps, quorum, timelock, service level, dates, cost | `DECISION_REQUIRED · Astra` | Astra | States none |
| Wallet and exchange compatibility | `UNDETERMINED` | No owner named by the sources | States no compatibility |
| Astra-gate cell mismatch (§1) | Recorded, not resolved | Not assigned by this document | Follows `user_merge: true` and edits no source |
| Final activation of any gate | `DECISION_REQUIRED · User` | User, and only after P-1 for that gate | Does not activate |

## 9. Coverage (AGENTS §7), classification (§8), non-claims, references

### Coverage (`AGENTS.md` §7)

This node adds no test. The token-layer checks that exist are an author-side mock. They are not independent verification and they are not a deployment.

| Requirement | Coverage | Action here |
|---|---|---|
| Author-side mock of the off-chain reward model | Partial, and only as a mock. `reference/token_reward/test_tl4_model_properties.py`, `reference/token_reward/test_tl4_fsm_properties.py`, `reference/token_reward/test_tl4_fuzz_boundaries.py`. The capability register calls this MOCK and says independent verification is not covered (`CURRENT_CAPABILITY_REGISTER.md:159`) | Cited. Not duplicated. Not counted as V-2 |
| TL-5 operational activation, written TL-L results, a key-management decision, an independent Move audit, testnet operation records, a named operator | Not covered. The register's TL-5 row says so (`CURRENT_CAPABILITY_REGISTER.md:160`, "not covered; 외부 법무/회계/세무/금융 서면·키/감사/운영 승인, issuance 자동 개방 없음") | No test added. The gap is the missing evidence in §3. This document does not close the row |

### Classification (`AGENTS.md` §8)

A. The written locks match the sources in §2. The blueprint asks for a judgment and forbids automatic progression. This document records that judgment as criteria and does not change runtime behavior. The TL-2 and TL-3 records match the F4 recommendation: there is no package.

B. Contract undefined, recorded and not invented:

- Whether the shared key-management decision covers token keys (K-2).
- Whether the key-management operator and the mainnet operator are the same person.
- What "키 생성 없음(localnet)" requires of a package (K-5).
- Outside-review, tax, accounting, AML/KYC, jurisdiction, chargeback, supply, cap, quorum, timelock, service-level, date, and cost values in §4 and §8. None of them is decided here.
- Wallet and exchange compatibility, which the sources leave with no owner.
- The Astra-gate cell mismatch in §1.

This document does not invent those semantics and does not amend a contract, an ADR, the blueprint, or the roadmap.

C. No explicit contract violation. No locked file is changed. Testnet, mainnet, and issuance stay locked, which is what the sources say. No merge blocker of class C is filed.

### Non-claims

This document does not claim that the criteria are satisfied, that merging it opens a gate, or that a completed checklist opens a gate by itself. It does not claim that testnet, mainnet, issuance, real PG, bank, KYC, a public endpoint, a token module, or R2 is unlocked or satisfied. It states no legal conclusion and no licensing conclusion. It does not claim a return, liquidity, or price support. It does not claim that any part of this work is production-ready. 합법, 인허가, 투자수익, 유동성, 가격 유지를 주장하지 않는다. It states no supply, cap, quorum, timelock, service level, date, or cost. It states no claim of durability, bank exactly-once, or chain finality. It states no claim that exact-head CI has run for a head that includes this file. A documentation-only green is not full verification. The author's check is not an independent review.

### References

Pinned to observed `origin/main` `18b80a79614b3a5866f61728b0935294360cfa85`.

- `AGENTS.md` §4 `:91-94`; `:13-16`; `:30-31`; §5 `:111`, `:114`, `:119`; §6; §10; §11; §12; §14.
- `docs/decisions/PROGRAM_DECISIONS_20260928.md` §0 `:13-14`; §1 `:25`; §5 `:108-117`.
- `docs/decisions/PROGRAM_ROADMAP_20260930.md` §0 `:14-15`; §1 `:26`, `:28`; §2 `:46`; §3.5 `:133`; §5 `:213-221`.
- `docs/decisions/AUTHORITY_MODEL_1.md:12-13`.
- `docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:179`.
- `docs/blueprints/optional-native-token-v1/README.md:376`, `:388`, `:390`, `:509`, `:531`, `:536-546`, `:557-558`.
- `docs/adr/0002-token-layer-scope-and-limits.md:46`, `:57-58`, `:89`.
- `docs/adr/0003-coin-tix-lock-localnet-re-ruling-request.md:94-96`, `:118-122`, `:140-142`.
- `docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md:112`, `:114`, `:124`, `:280-282`.
- `docs/contracts/TOKEN_ROLE_AND_SUPPLY.md` §3 D, §11, `:280`, `:283`.
- `docs/decisions/TL2_DOES_NOT_OPEN_20261009.md`.
- `docs/decisions/TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md`.
- `docs/decisions/TL4_THREAT_MODEL_20261009.md:11`, `:19`, `:95-103`, `:117`.
- `docs/status/TOKEN_LEGAL_REVIEW_BRIEF_KO.md:9`, `:31`, LB-01 through LB-11.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md:151`, `:159`, `:160`.
- `docs/DEVELOPMENT_PLAN.md:602`.
- `docs/aiops/PROGRAM_ASTRA_DELEGATION.md:3`, `:76`.
- `.aiops/program.json:627-637`.
- `reference/token_reward/test_tl4_model_properties.py`.
- `reference/token_reward/test_tl4_fsm_properties.py`.
- `reference/token_reward/test_tl4_fuzz_boundaries.py`.
