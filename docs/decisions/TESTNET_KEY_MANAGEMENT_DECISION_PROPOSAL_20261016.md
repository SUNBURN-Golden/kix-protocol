요약. 이 문서는 장래 Sui testnet 배포가 필요로 할 키 관리의 형태(보관, 교체, 사고 대응, 운영 주체)를 제안만 한다. 키도 비밀도 만들지 않고 아무것도 배포하지 않는다.
권고는 §4의 형태를 채택하는 것이다. 그 권고는 실행하지 않는다. 제품, 사람 이름, 정족수, 기간, 비용은 비어 있고 담당자만 적었다.
효력은 사용자가 이 문서를 병합할 때에만 생긴다. 수정 없이 병합하면 권고만 채택되고, testnet 잠금은 풀리지 않는다.

# Sui testnet key management decision proposal (2026-10-16)

Node `testnet-key-management-decision`. No issue. No file under `docs/tasks/` names this node. This is a User decision document. It proposes the shape of key custody, rotation, incident handling, and operation that a future Sui testnet deployment needs. It stops at the shape. Nothing is created and nothing is deployed.

Date: 2026-10-16.
Status: proposed. This is a User decision document. It takes effect only when the User merges it ([roadmap](PROGRAM_ROADMAP_20260930.md) §1 `:26`; writing alone has no effect, roadmap §0 `:14-15`). The builder does not merge this file and does not act on the recommendation in §4 and §7.

If the User merges this file without edits, only the recommended branch is adopted (C3, R2, I2, W2, and O1). Every `DECISION_REQUIRED` and `UNDETERMINED` value stays empty. Every lock stays.

## 0. Status and effect

Effect rule, in plain terms. A draft in the repository does nothing to a lock. The roadmap says writing that document alone creates no effect (`PROGRAM_ROADMAP_20260930.md:14-15`). [Program decisions](PROGRAM_DECISIONS_20260928.md) §0 (`:13-14`) uses the same rule.

It takes effect only when the User merges it. The builder does not merge it and does not act on the recommendation. The builder's check is not an independent review and is not a non-author exact-HEAD review (`AGENTS.md` §6, §14). This session has no task issue, no `ASTRA_TASK_KEY_V1` line, and no signer, so the program-mode precedence at `AGENTS.md:13-16` does not apply here. Architecture rulings stay with Claude Fable through the central `aiops-fable` tool (`AGENTS.md:30-31`, User decision M5, 2026-09-30). This session issues none.

What a merge adopts. The shape in §4, if merged without edits. That supplies the "키 관리 방식 결정 문서" half of the testnet unlock (`PROGRAM_DECISIONS_20260928.md:111`: "키 관리 방식 결정 문서와 사용자 승인"). The other half is a separate explicit User approval of the deployment itself. An unedited merge is not that approval. Sui testnet deployment stays locked.

## 1. Base and evidence

Each identifier below was read on the fetched base. None of them is a CI result for this file. CI from an earlier SHA does not transfer to a later SHA (`AGENTS.md` §6, §11).

Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`: `751c51bdff661673eb2edb9de0dea8f6cbdac2e0`. That commit is the merge of pull request #190. The branch is `agent/kix-testnet-key-management-decision`. Program mode would name the branch `astra/<task id>`. This node has no issue, and no issue names a branch. This session does not rename the branch. This session does not commit, so there is no implementation commit SHA.

Locked blobs, checked before this file was added:

| File | Required blob | Observed |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |

`reference/v0.3-rc1/**` was not modified.

Node fields read from [`.aiops/program.json`](../../.aiops/program.json) `:488-498`: `depends_on` is `rs-1`; `audit_floor` is A3; `user_merge` is true; `astra_auto_merge` is false. That object has no `astra_gate` key. `rs-1` is merged (see the [rs-1 record](../../validation/2026-10-14-rs-1-public-path/README.md)).

Astra-gate mismatch, recorded and not resolved:

| Place | What it says on this base |
|---|---|
| Dispatch header for this node | `astra_gate: None`, `user_merge: true` |
| Roadmap §3 table, row for this node | Astra gate ARCHITECTURE, merge **사용자** |
| Node object `.aiops/program.json:488-498` | no `astra_gate` key |
| [Delegation table](../aiops/PROGRAM_ASTRA_DELEGATION.md) | contract change NO, merge 대표님, audit floor A3. The document status line (`:3`) says the table is a non-executable draft |

The merge actor in every cell that names one is the User. This file does not pick a winner among the gate cells and does not edit those sources. It follows `user_merge: true`.

Sibling nodes. No file in the tree is `rs-5-decision` (it depends on this node). The capability register row "RS-5 / testnet keys" is `not covered` (`docs/status/CURRENT_CAPABILITY_REGISTER.md:159`). That matches the facts in §3. It does not contradict them.

## 2. What is locked, and where it is written

| Source | What it says |
|---|---|
| [Program decisions](PROGRAM_DECISIONS_20260928.md) §5 `:111` | "Sui testnet 배포 \| 키 관리 방식 결정 문서와 사용자 승인. localnet 시험은 이미 허용" |
| Same file `:112` | "Sui mainnet 실행 \| Move 독립 감사, testnet 운용 증거, 키 관리 운영 책임자, 사용자 승인" |
| Same file §1 `:25` | "잠금은 영구 금지가 아니다. 증거가 모이면 여는 문이며, 각 잠금의 해제 조건을 §5에 적는다." |
| [Roadmap](PROGRAM_ROADMAP_20260930.md) §5 `:215` | "Sui testnet 배포 \| 키 관리 결정 문서와 사용자 승인 \| `testnet-key-management-decision`(사용자)" |
| Same file `:216` | "Sui mainnet \| 독립 Move 감사, testnet 운용 증거, 운영 책임자, 사용자 승인 \| `rs-5-decision`, `tl-5-decision`(사용자)" |
| [ADR-0002](../adr/0002-token-layer-scope-and-limits.md) §4 item 5 `:58` | Key generation and repository secrets stay unauthorized |
| [Blueprint](../blueprints/optional-native-token-v1/README.md) TL-2 `:509` | "키 생성 없음(localnet)". Its operational-activation row (`:510`) says testnet needs the key-management decision document and User approval |

Neighbouring locks stay on their own rows and stay separate. This file does not open any of them: real funds and real PG, bank, and KYC calls; real credit or regulated finance; Sui mainnet execution; public operational endpoints; R2 and an own replication, consensus, or storage engine; a new coin or TIX module. The full list is in §8.

## 3. Facts today

**Where keys live today.** Localnet runs are disposable. The runners say "All keys, signed submissions and node state remain in ignored .local folders" (`scripts/run_localnet.py`, `scripts/run_localnet_rights_scale.py`, and `scripts/run_localnet_rights_scale_private.py` docstrings). `scripts/env.sh:4` points the Sui client config into `.local/`. `.gitignore` excludes `.local/`, `*.keystore`, `.env`, `*.pem`, and `*.key` (`:7`, `:25`, `:28-32`). No key custody, rotation, or incident procedure for a persistent network is written anywhere in the repository.

**The ZK fixture ceremony is single-party.** "Groth16 파라미터는 단일 주체 시험용이다. 신뢰 설정, 회로 감사, 운영 검증키 관리가 남아 있다" (`docs/RUNTIME_VALIDATION.md:46`). The key check does not certify an operational trust setup (`docs/PROTOCOL_HARDENING.md:18`). Proving and verifying keys are out of scope here (see below).

**Why custody matters for the delegated-execution design.** The Sui research says a local leader gate does not stop signing if the former leader independently holds the raw key (`docs/research/SUI_EQUIVOCATION_REPLICATION_RESEARCH_5440de0cf721.md:118`). It says internal fencing cannot recall a valid signed transaction already held by a former leader or an external relay (`:129`). It names "서명 키의 실제 관리 주체" as an input any numeric range needs, and does not decide it (`:197`). The cut-proof review pack records the same gap as assumption A7: UNDETERMINED, "no testnet key decision, no real keys", owner User, later node `testnet-key-management-decision` ([I12 review pack](../status/I12_REVIEW_PACK.md) `:70`). This file is that later node's proposal. It does not close A7.

**Key-role inventory for the rights-scale package.** Sources are the [rights-scale profile](../contracts/RIGHTS_SCALE_PROFILE.md) (draft) and `reference/rights_scale/sui/sources/rights_scale.move`. All of it is localnet today.

| Role | Today | Needed for a testnet package | Source |
|---|---|---|---|
| Package publisher | A throwaway localnet address | A named holder, decided under §4 | `reference/rights_scale/sui/tests/support.move:34`; `rights_scale.move:97-99` |
| Upgrade authority for the package | Not described in the repository | Unknown. A holder and a mode would have to be chosen | grep of `docs/`, `reference/rights_scale`, `scripts/` found it named only for the future token package (`TOKEN_AUTHORITY_AND_LIFECYCLE.md` §2). Nothing for rights-scale |
| `IssuerCap` holder | Minted once to the publisher in `init`; `key` only; no transfer function | **OPEN.** The profile leaves its handling to Astra after the probe. This file does not pick | profile `:48`, `:250-262`; `rights_scale.move:97-99` |
| Payment attesters and gates | Lists stored in `ShowControl` | A holder per attester | profile `:63` |
| Grant `issuer` (calls `revoke_grant`) and grant `delegate` (calls the delegated operations) | Localnet addresses | Two separate holders | profile `:86-92` |
| Gas payer | Every transaction also uses a gas coin | A funding source and a holder | profile `:69` |

Out of scope for this file: token-side keys (`TreasuryCap`, `UpgradeCap` for a token package, and the rest of the matrix in `TOKEN_AUTHORITY_AND_LIFECYCLE.md` §2) and ZK proving or verifying keys. Whether this decision covers token keys is TL-5 row K-2 and stays open (§5).

**Absent on this base:** a key-management document; a named operator; a custody product; any testnet operation evidence; a budget.

## 4. Decision axes

Four axes. On each, the recommendation is a form, not a product, a count, or a name. The precedent wording for the form is the token-layer contract's recommendation: separate custody for upgrade and for issuance, "숫자와 사람 이름과 수탁 제품은 비워 둔다. 빌더는 키를 만들지 않는다" (`TOKEN_AUTHORITY_AND_LIFECYCLE.md:78`).

### Custody (C)

| Option | Consequence in plain terms | Recommendation |
|---|---|---|
| C1. One operator holds one key for everything | Simplest. If that one key is lost or taken, every role is lost or taken at once, and the package can be changed by whoever has it. It also puts the delegated-execution gate at the mercy of the raw-key problem in §3 | Not recommended |
| C2. Role-separated keys; admin-class roles kept off the machine that runs things | A leak from the runtime machine cannot change the package or the grants. More keys to look after, and more ways to lose one | Acceptable fallback |
| C3. Admin-class roles under multi-party control; the runtime machine holds only one hot key limited to delegated execution | The strongest of the forms that need no purchase. The cost is people and procedure: more than one human must act for an admin-class change. It names no product, no signer count, and no quorum, so those stay open | **Recommended, as a form only** |
| C4. A managed KMS, HSM, or custodian | Moves the keys to a provider. Needs spend and secrets and a provider choice | `DECISION_REQUIRED · User`. Not decided here |

Rules that go with the recommended form: admin keys and runtime keys are different keys. A testnet key is never reused for mainnet. Nothing key-like goes into the repository, into CI secrets, or into a log. Agents never hold keys (`AGENTS.md` §16). The product behind C3, the signer count, the quorum, and any timelock are empty: product and spend are `DECISION_REQUIRED · User`; count, quorum, and timelock values are `DECISION_REQUIRED · Astra`. Sui feature facts needed to build C3 (multi-signature support, key formats, address derivation) are `UNDETERMINED`. No repository source pins them. This file asserts none.

### Rotation (R)

| Option | Consequence in plain terms | Recommendation |
|---|---|---|
| R1. Never rotate; redeploy instead | No rotation procedure to get wrong. A leaked key can only be answered by abandoning the deployment. On testnet that may be cheap, but it teaches nothing about rotation | Not recommended |
| R2. Rotate on an event, and rehearse the hand-over first | Keys move only when something happened (a person leaves, a key may be exposed). The hand-over is practiced and recorded before it is used. No calendar to forget. Follows the precedent that holder replacement needs a rehearsal record first (`TOKEN_AUTHORITY_AND_LIFECYCLE.md:165`) | **Recommended** |
| R3. Rotate on a schedule | Regular practice. Needs a period, and a period is a number | `DECISION_REQUIRED · Astra`. Not decided here |

No rotation period appears in this file.

### Incident handling (I)

Events, modelled on the token-layer key-event table (`TOKEN_AUTHORITY_AND_LIFECYCLE.md` §5, `:150-171`). The structure column is a shape. It is not a runnable procedure. No time target appears in any cell.

| Event | Fact and source | Structure | What is not done | Record fields |
|---|---|---|---|---|
| Runtime (delegate) key lost | The delegate can no longer sign delegated operations. `refund_delegated` still runs from the ticket owner (profile `:92`, `:200`) | Issuer closes the grant with the cut (`revoke_grant`, profile `:201`), then reclaims unused capacity page by page (`undelegate_page`) | No claim that lost keys are recoverable | Common fields below |
| Runtime key compromised | A holder of the key can sign delegated operations until the grant is closed. `revoke_grant` is one write to `GrantControl`; `GrantRevoked` is the durable record (profile `:201`). A cut does not recall a transaction already signed and held elsewhere (research `:129`) | Cut first. Then reconcile every submission made under that grant by looking up the original bytes. UNKNOWN stays UNKNOWN until observed | Do not choose a new gas coin or version and rebuild the same business action. A missing record is not read as "not executed" (`AGENTS.md` §6; `TOKEN_AUTHORITY_AND_LIFECYCLE.md:156`) | Common fields, grant id, cut generation, digests observed |
| Admin or upgrade key lost | The matching admin action cannot be done. No repository source says it can be recovered | Treat the deployment as frozen for that action. Decide redeploy versus wait under the User's authority | No promise of recovery | Common fields |
| Admin or upgrade key compromised | A holder could change the package or the grants. No repository source describes what Sui allows after that | Stop using the deployment. Record. Decide under the User's authority | No claim that damage can be undone | Common fields |
| Key leaked into the repository, a log, or CI | A leaked secret is treated as compromised, whatever its apparent age | Rotate (R2). No history rewrite without an explicit human instruction (`AGENTS.md` §6) | No force-push to hide it | Common fields; the location of the leak, never the secret |
| Operator unavailable | One person is a single point of failure | The backup operator in W2 acts | No agent acts as a stand-in key holder | Common fields |

Common record fields, as in the token-layer contract (`:158` of the same file): `record_id`, event kind, generation, target role, observed digest if any, reason, preceding record, and where the authoritative record lives. The location is empty: no executor and no store exists. A secret key is never written in a record.

| Option | Consequence in plain terms | Recommendation |
|---|---|---|
| I1. Stop and write down what happened; nothing else is written in advance | Least to maintain. In the middle of an incident, people improvise exactly the steps (gas, versions, retries) that the UNKNOWN rule forbids | Not recommended |
| I2. A written runbook in the shape of the table above: cut first, then reconcile the original bytes | People under pressure follow a page instead of improvising. The runbook must be written, rehearsed (R2), and kept current. It sets no response time | **Recommended** |
| I3. An automatic kill switch | Faster than a person. It is a new protocol command or new automation, which this program does not allow without an Astra decision | `DECISION_REQUIRED · Astra`. Not decided here |

### Who operates it (W)

| Option | Consequence in plain terms | Recommendation |
|---|---|---|
| W1. The User, personally | No hand-over needed. The User is then both key holder and final approver, so nobody independent can check them, and absence stops everything | Not recommended |
| W2. A human operator and a backup, each named by the User, kept apart from the independent reviewer | Matches how the unlock rows are written: a named person, not a role in the abstract. Costs two people's time. Names are empty here | **Recommended, names empty** |
| W3. An external operator | Takes the work off the team. Needs spend, a contract, and a provider | `DECISION_REQUIRED · User`. Not decided here |

Agents never hold keys (`AGENTS.md` §16; the same rule as `TOKEN_AUTHORITY_AND_LIFECYCLE.md:97`). Do not copy the people who hold the first-batch approval roles into the operator slot (`FIRST_BATCH_OPEN_INPUTS.md:35`); the token-layer contract sets the same precedent (`:129`). Whether this testnet operator is also the mainnet "키 관리 운영 책임자" (`PROGRAM_DECISIONS_20260928.md:112`) and the TL-5 operator is `DECISION_REQUIRED · User` and is not decided here.

## 5. Boundaries and interactions

- **TL-5 rows.** [TL-5 proposal](TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md) K-1 ("a written key-management decision exists") is the row this file feeds. K-2 (does the decision cover token keys), K-3 (a named operator for mainnet), and K-5 (what "키 생성 없음(localnet)" allows, ADR-0003 Q3) stay open with the owners in that file. This file does not answer them.
- **RS-5.** `rs-5-decision` depends on this node (roadmap §3 table). Ceremony, audits, mainnet, and operational adoption are its subject. Merging this file satisfies only the "key-management decision document" input. It does not satisfy RS-5, and RS-5 would not satisfy this file.
- **`IssuerCap`.** The choice of how that capability is held is Astra's, after the probe (profile `:250-262`). Any form in §4 works with each of the three choices the profile lists; this file picks none.
- **Locks.** No lock text changes. The testnet row in program decisions `:111` is not edited.

## 6. Prerequisites for a later request to deploy to testnet

A checklist for a later, separate proposal. Completing it is not approval. Every cell is empty on purpose.

| ID | Prerequisite | Evidence a later proposal would bring | Owner |
|---|---|---|---|
| KM-1 | Operator and backup named | A User record naming them. None here | `DECISION_REQUIRED · User` |
| KM-2 | Custody product chosen, if C3 or C4 needs one | The choice and its cost | `DECISION_REQUIRED · User` |
| KM-3 | Signer count, quorum, timelock | Values | `DECISION_REQUIRED · Astra` |
| KM-4 | Written key-generation procedure | A document. Not performed by this node | `DECISION_REQUIRED · Astra` |
| KM-5 | Funding source for testnet gas | Any external or paid service is a spend decision | `DECISION_REQUIRED · User` |
| KM-6 | Backup, recovery, and hand-over drill record (R2, I2) | A drill record. None exists | The named operator, after KM-1 |
| KM-7 | Secrets-handling rules (where keys may never appear) | A document | `DECISION_REQUIRED · User` |
| KM-8 | Sui facts the design relies on, pinned to a source | Cited sources | `UNDETERMINED` until pinned |
| KM-9 | Astra ruling on the deployment | The ruling text | `DECISION_REQUIRED · Astra` |
| KM-10 | Separate explicit User approval naming testnet deployment | A later User merge or other explicit OK | `DECISION_REQUIRED · User` |
| KM-11 | Legal character of custody, if any custody is done for others | A written view | `UNDETERMINED · external review` |

## 7. Options for the User on this document

The recommendation is a suggestion. It is not acted on. The builder does not merge, does not edit a lock row, and does not start a later node.

### O1. Adopt the shape in §4

Adopt C3, R2, I2, and W2 as the shape a later testnet request must follow, with the empty cells left empty.

Consequence in plain terms: a later request to deploy to testnet must come with role-separated and multi-party-controlled keys, an event-driven and rehearsed rotation, a written cut-then-reconcile runbook, and a named human operator with a backup. The "key-management decision document" half of the testnet unlock is then met. The User's separate approval is still needed, and so is everything in §6. Merging creates no key, deploys nothing, and fills in no name, number, or product. This is the suggestion.

### O2. Defer

Adopt no shape.

Consequence in plain terms: the question stays open. The testnet lock stays as written, and `rs-5-decision` continues without a key-management input. Anyone who later wants a testnet deployment has to start this proposal again.

### O3. State a permanent no-testnet prohibition

Consequence in plain terms: testnet would be written as never allowed. The program decisions say a lock is a door that opens when evidence exists, not a permanent ban (`PROGRAM_DECISIONS_20260928.md:25`). Choosing this would be a different decision from the one on record. This file does not make it.

## 8. What this document does not authorize

The §5 locks, in the words already adopted (`PROGRAM_DECISIONS_20260928.md:108-117`), all stay:

1. 커널 잠금 blob 2개. 해제 조건: 별도 사람 결정. This file changes neither blob.
2. 실자금, 실 PG·은행·KYC 호출. Not satisfied here.
3. 실제 여신·규제 금융. Not satisfied here.
4. Sui testnet 배포. 해제 조건: 키 관리 방식 결정 문서와 사용자 승인. Not satisfied here. This file does not deploy to testnet. Adopting §4 does not deploy to testnet.
5. Sui mainnet 실행. Not satisfied here.
6. 공개 운영 엔드포인트. Not satisfied here.
7. R2, 자체 복제·합의·저장 엔진. Not satisfied here.
8. (a) PR #11 통합. Not satisfied here.
9. 새 coin/TIX 모듈. No new coin or TIX module is added. The localnet exception stays where the roadmap puts it and is not opened here.
10. schema·SDK 안정 1.0, KTX→KIX 일괄 치환. Not satisfied here.

Also not authorized: a production runtime, live-money execution, and live Sui production execution (`AGENTS.md` §5). No key, secret, or credential is created. No `sui` command, faucet call, or network call was made for this file. No new protocol command, kill switch, or key registry is added, and the OpenAPI catalogue is untouched.

This file does not edit the blueprint, the roadmap, the development plan, the capability register, any ADR, or any contract. `docs/README.md` gains one index section so a reader can find this file. That index is not an approval. The register row "RS-5 / testnet keys" stays `not covered`.

## 9. Register

No row below is closed by this document. Product policy values and new protocol commands are `DECISION_REQUIRED · Astra`. Legal and provider answers stay `UNDETERMINED` with the owner named.

| Item | Class | Owner | What this document does |
|---|---|---|---|
| Custody product (C4, KM-2) and any spend | `DECISION_REQUIRED · User` | User | Chooses none |
| Operator and backup names (W2, KM-1) | `DECISION_REQUIRED · User` | User | Names no one |
| Same person as the mainnet operator and TL-5 K-3 / O-1 | `DECISION_REQUIRED · User` | User | Does not decide |
| External operator (W3), gas funding (KM-5), secrets rules (KM-7) | `DECISION_REQUIRED · User` | User | Decides none |
| Signer count, quorum, timelock, rotation period, response or recovery time | `DECISION_REQUIRED · Astra` | Astra | States none |
| Key-generation procedure (KM-4) | `DECISION_REQUIRED · Astra` | Astra | Writes none and generates no key |
| Automatic kill switch or any new command (I3) | `DECISION_REQUIRED · Astra` | Astra | Adds none |
| `IssuerCap` handling | `DECISION_REQUIRED · Astra` | Astra, after the probe | Picks none |
| Whether this decision covers token keys (TL-5 K-2) | `DECISION_REQUIRED · User` | User | Does not answer |
| Meaning of "키 생성 없음(localnet)" (TL-5 K-5) | `DECISION_REQUIRED · Astra` | Astra | Does not resolve |
| Legal character of custody (KM-11) | `UNDETERMINED · external review` | External review. Who starts it is TL-5 D-E, `UNDETERMINED · User` | States no conclusion |
| Sui multi-signature, key-format, and upgrade facts (KM-8) | `UNDETERMINED` | None named by the sources | Asserts none |
| Upgrade authority holder for the rights-scale package | `UNDETERMINED` | Not described in the repository | Records the gap |
| Astra-gate cell mismatch (§1) | Recorded, not resolved | Not assigned by this document | Follows `user_merge: true` and edits no source |
| RS-5 content (ceremony, audits, mainnet) | Separate decision | User, in `rs-5-decision` | Does not satisfy it |
| Final testnet approval (KM-10) | `DECISION_REQUIRED · User` | User, after KM-9 | Does not approve |

## 10. Coverage (AGENTS §7), classification (§8), non-claims, references

### Coverage (`AGENTS.md` §7)

This node adds no test. It is prose.

| Requirement | Coverage | Action here |
|---|---|---|
| Localnet key handling for the existing journeys | Partial, localnet only. `scripts/run_localnet.py`, `scripts/run_localnet_rights_scale.py`, `scripts/run_localnet_rights_scale_private.py` keep keys under ignored `.local/`. The rs-1 record is the evidence for the public path | Cited. Not duplicated |
| Custody, rotation, incident handling, and operation for a persistent network | Not covered. The register row says so (`CURRENT_CAPABILITY_REGISTER.md:159`) | No test added. The gap is the missing evidence in §3 and the open prerequisites in §6. This document does not close the row |

### Classification (`AGENTS.md` §8)

A. The locks match their sources in §2. The A7 gap matches the I12 review pack (`I12_REVIEW_PACK.md:70`).

B. Contract undefined, recorded and not invented:

- The upgrade-authority holder for the rights-scale package.
- Whether the shared decision covers token keys (TL-5 K-2).
- Whether the testnet operator and the mainnet operator are the same person.
- Sui multi-signature, key-format, and upgrade facts not pinned by a repository source.
- Signer count, quorum, timelock, rotation period, response and recovery times, and cost. None is decided here.
- The Astra-gate cell mismatch in §1.

This document does not invent those semantics and does not amend a contract, an ADR, the blueprint, or the roadmap.

C. No explicit contract violation. No locked file is changed. Testnet stays locked, which is what the sources say. No merge blocker of class C is filed.

### Non-claims

This document does not claim that the proposed shape is sufficient, safe, or tested, that merging it opens the testnet gate, or that a completed §6 checklist opens it by itself. It does not claim that testnet, mainnet, real PG, bank, KYC, a public endpoint, a token module, or R2 is unlocked. It states no legal conclusion about custody. It does not claim that any part of this work is production-ready. It states no claim of durability, distributed fencing, bank exactly-once, or chain finality. It states no signer count, quorum, timelock, rotation period, service level, date, or cost. It states no claim that exact-head CI has run for a head that includes this file. A documentation-only green is not full verification. The author's check is not an independent review. No key was created and nothing was deployed.

### References

Pinned to observed `origin/main` `751c51bdff661673eb2edb9de0dea8f6cbdac2e0`.

- `AGENTS.md` §4; §5; §6; §10; §11; §12; §14; §16; `:13-16`; `:30-31`.
- `docs/decisions/PROGRAM_DECISIONS_20260928.md` §0 `:13-14`; §1 `:25`; §5 `:108-117`.
- `docs/decisions/PROGRAM_ROADMAP_20260930.md` §0 `:14-15`; §1 `:26`; §3 table; §5 `:215-216`.
- `docs/decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md` §4 rows K-1 to K-5, O-1.
- `docs/adr/0002-token-layer-scope-and-limits.md` §4 `:58`.
- `docs/blueprints/optional-native-token-v1/README.md:509-510`.
- `docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md:78`, `:97`, `:129`, `:150-171`.
- `docs/contracts/RIGHTS_SCALE_PROFILE.md:48`, `:60-69`, `:86-92`, `:196-205`, `:250-262`.
- `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md:35`.
- `docs/research/SUI_EQUIVOCATION_REPLICATION_RESEARCH_5440de0cf721.md:118`, `:129`, `:197`.
- `docs/status/I12_REVIEW_PACK.md:70`.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md:159`.
- `docs/RUNTIME_VALIDATION.md:46`; `docs/PROTOCOL_HARDENING.md:18`.
- `docs/aiops/PROGRAM_ASTRA_DELEGATION.md:3`.
- `.aiops/program.json:488-498`.
- `reference/rights_scale/sui/sources/rights_scale.move:97-99`; `reference/rights_scale/sui/tests/support.move:34`.
- `scripts/env.sh:4`; `.gitignore:7`, `:25`, `:28-32`; `scripts/run_localnet*.py` docstrings.
