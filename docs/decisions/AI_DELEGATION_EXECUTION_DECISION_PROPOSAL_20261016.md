요약. 이 문서는 위임 실행을 언제, 어떤 방식으로 켤 수 있는지의 형태를 제안만 한다. 실행은 꺼진 채로 둔다. 플래그도 코드도 바꾸지 않는다.
권고는 §6의 O1이다. 켜는 일은 나중의 별도 사용자 결정과 Astra 판정으로 미루고, 이 문서의 체크리스트는 문턱일 뿐이다. 그 권고는 실행하지 않는다. 한도, 기간, 이름, 정족수는 비어 있고 담당자만 적었다.
효력은 사용자가 이 문서를 병합할 때에만 생긴다. 수정 없이 병합하면 권고된 형태만 채택되고, 위임 실행은 계속 꺼져 있다.

# AI delegation execution decision proposal (2026-10-16)

Node `ai-delegation-execution-decision`. No issue. No file under `docs/tasks/` names this node. This is a User decision document. It proposes when and how delegated execution may be enabled: the prerequisites from the delegation contract and from RS-3, the I11 items the User and Astra must set, and what revocation does and does not guarantee. It stops at the shape. Execution stays disabled.

Date: 2026-10-16.
Status: proposed. This is a User decision document. It takes effect only when the User merges it ([roadmap](PROGRAM_ROADMAP_20260930.md) §1; writing alone has no effect, roadmap §0 `:14-15`). The builder does not merge this file and does not act on the recommendation in §4 and §6.

If the User merges this file without edits, only the recommended branch is adopted (G2, L2, R2, and O1). Every `DECISION_REQUIRED` and `UNDETERMINED` value stays empty. Every lock stays. `delegated_execution_enabled` stays `false`.

## 0. Status and effect

Effect rule, in plain terms. A draft in the repository does nothing. The roadmap says writing that document alone creates no effect (`PROGRAM_ROADMAP_20260930.md:14-15`). [Program decisions](PROGRAM_DECISIONS_20260928.md) §0 uses the same rule.

It takes effect only when the User merges it. The builder does not merge it and does not act on the recommendation. The builder's check is not an independent review and is not a non-author exact-HEAD review (`AGENTS.md` §6, §14). This session has no task issue, no `ASTRA_TASK_KEY_V1` line, and no signer, so the program-mode precedence at the top of `AGENTS.md` does not apply here. Architecture rulings stay with Claude Fable through the central `aiops-fable` tool (`AGENTS.md:30`, User decision M5). This session issues none.

What a merge adopts. The shape in §4 and the checklist in §5, if merged without edits. The checklist is a bar a later request must clear. Clearing it is not an approval, and merging this file turns nothing on.

## 1. Base and evidence

Each identifier below was read on the fetched base. None of them is a CI result for this file. CI from an earlier SHA does not transfer to a later SHA (`AGENTS.md` §6, §11).

Observed `origin/main` and branch HEAD at session start, after `git fetch origin main`: `47eed4b01b93dc4b00e102729bad1c74abdbae95`. That commit is the merge of pull request #192. The branch is `agent/kix-ai-delegation-execution-decision`. Program mode would name the branch `astra/<task id>`. This node has no issue, and no issue names a branch. This session does not rename the branch. This session does not commit, so there is no implementation commit SHA.

Locked blobs, checked before this file was added:

| File | Required blob | Observed |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match |

`reference/v0.3-rc1/**` was not modified.

Dependencies, read with `git log` on the base. All three are merged and are fixtures or a mock:

| Dependency | Merge | What it is |
|---|---|---|
| `ai-delegation-contract-mock` | #130 (`90c6e7a`) | [Contract draft](../contracts/AI_DELEGATION_AUTHORITY.md) and an in-memory Python mock. Execution is defined and always refused |
| `rs-3a` | #183 (`adcddc5`) | localnet `GrantControl`, page delegation, `revoke_grant` ([record](../../validation/2026-10-14-rs-3a-delegation-primitives/README.md)) |
| `rs-3b` | #184 (`ced0e2f`) | in-memory page-to-kernel map with a grant mirror ([record](../../validation/2026-10-14-rs-3b-delegated-exec/README.md)) |

Related, already merged: the I12 cut proof (#136, `ae869f3`, [proof](CUT_PROOF_I12_20261008.md)) and the v5 kernel (#179, `4813388`).

Node fields read from [`.aiops/program.json`](../../.aiops/program.json) `:639-650`: `depends_on` is the three nodes above; `audit_floor` is A3; `user_merge` is true; `astra_auto_merge` is false. That object has no `astra_gate` key.

Astra-gate mismatch, recorded and not resolved:

| Place | What it says on this base |
|---|---|
| Dispatch header for this node | `astra_gate: None`, `user_merge: true` |
| Roadmap §3 table, row for this node (`:139`) | Astra gate ARCHITECTURE, merge **사용자** |
| Node object `.aiops/program.json:639-650` | no `astra_gate` key |
| [Delegation table](../aiops/PROGRAM_ASTRA_DELEGATION.md) (`:77`) | contract change NO, merge 대표님, audit floor A3. The document status line says the table is a non-executable draft |

The merge actor in every cell that names one is the User. This file does not pick a winner among the gate cells and does not edit those sources. It follows `user_merge: true`.

## 2. Where "off" is written

| Source | What it says |
|---|---|
| `runtime/ARCHITECTURE.toml:29` | `delegated_execution_enabled = false`. The same file keeps `exclusive_grant_required = true` and `same_resource_dual_write = false` |
| `scripts/verify_runtime_architecture.py:53` | The verifier pins the value to `False` |
| `scripts/test_runtime_architecture.py:48` | A test mutates it to `true` and expects the verifier to fail |
| [Contract](../contracts/AI_DELEGATION_AUTHORITY.md) §0 | "위임 실행은 꺼 둔다(개발계획 §12). 실제 grant와 비협조 회수가 없기 때문이다" |
| Contract predicates DLG-03, DLG-04, DLG-31 | An `EXECUTE` grant is refused; `attempt_execution` always refuses and changes nothing; no constructor argument enables execution |
| `docs/DEVELOPMENT_PLAN.md` §12 (`:530-536`) | Grant primitives and the extended package are fixtures; the profile stays a draft before Astra review and keeps delegated execution off. Production grants and non-cooperative revocation are unimplemented |
| `runtime/crates/kix-delegated-exec/README.md:21` | "`delegated_execution_enabled` stays `false`. Enabling delegated execution belongs to the user decision named in the program roadmap, not to a crate" |
| [Capability register](../status/CURRENT_CAPABILITY_REGISTER.md) `:139`, `:156-157` | Row "P AI delegation": contract and offline mock only; row RS-3a and RS-3b: fixtures |

This file edits none of those places. A later change to the flag needs its own node after a User decision (§7).

## 3. Facts today

What each merged piece gives, and what it does not give.

| Piece | What it gives | What it does not give | Source |
|---|---|---|---|
| Contract and mock (#130) | Grant records with three required limits and a currency, a period, scope, human-only issue and revoke, human-only decisions on proposals, revocation that blocks the generation at once and keeps history (DLG-14 to DLG-24, DLG-32) | Any link to the chain or to the executor. Limits, period and scope exist only in the Python mock. DLG-34 says the fixture integer range is not a product limit | Contract §4, §6, §9 |
| RS-3a chain primitives | One shared `GrantControl` per grant. `revoke_grant` is one write: `open` flips, `generation` bumps, pre-cut obligations are untouched, and every delegated path aborts with `EGrantClosed` from then on | Limits, expiry and an allowed-operation set. `GrantControl` carries show, issuer, delegate, generation and open, nothing more. The Move source says no expiry and no allowed-operation set are defined | `rights_scale.move:212`, `:898-900`, `:909-921` |
| RS-3b map | A caller-maintained grant mirror; after the cut, new `reserve` and `mark_payment_unknown` get `GrantClosed`, old fences get `ExecutionFenced`, stored first results still replay | Authentication of principals, delegates, issuers or grants; chain reads; grant expiry; durability of the map | crate README `:15-30` |
| I12 cut proof (#136) | A proof draft of the cut, conditional on a cooperating executor. Scopes whose cut is unproven hold new consumption and re-delegation | An independent review, a trust-policy acceptance, or a recorded branch choice. The open-input row still says the merge record does not record acceptance of option 1, 2 or 3 | `FIRST_BATCH_OPEN_INPUTS.md:36`; proof §5 |
| Lifecycle §5.5 | A three-tier approval shape that excludes automatic action on these paths | Any running automation. The active first-tier auto-approval scope is zero | `STATE_LIFECYCLE.md:419`, `:454-455` |

Findings, each checked at its source on this base:

1. **Limits do not reach the chain.** A grep for `per_action_max`, `cumulative_max` and `not_after` finds nothing in `runtime/**/*.rs`, in the Move sources, or in the `reference/rights_scale` Python. They exist only in the contract mock under `reference/ai_delegation`.
2. **No link between mock revocation and the chain cut.** Revoking in the mock does not close a `GrantControl`, and closing a `GrantControl` does not revoke in the mock. No roadmap node binds them. §5 lists this as a follow-up candidate and does not invent a node.
3. **The cut needs the issuer.** `revoke_grant` asserts `ctx.sender() == g.issuer` and takes an `IssuerCap` (`rights_scale.move:916-917`). How `IssuerCap` is held is still OPEN (profile §13). If the issuer key is lost, no cut can be written. Key custody is a separate input (A7; see the [testnet key management proposal](TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md), which is itself a proposal until merged).
4. **The executor map does not authenticate anyone.** Crate README `:23`.
5. **Two gaps recorded by RS-3a.** `cancel_show` does not revoke grants, and `shield` and `consume_private` take no delegation gate. Both are recorded as contract-undefined and left to Astra ([record](../../validation/2026-10-14-rs-3a-delegation-primitives/README.md) classification B items 2 and 4).
6. **The I12 branch is not recorded.** `FIRST_BATCH_OPEN_INPUTS.md:36` says so. This file does not infer a branch from the #136 merge.
7. **No Astra review of the profile is on the tree.** The register rows at `:156-157` and the plan at `:534` both say the profile is a draft before Astra review.
8. **Human designation exists; the service side does not.** The I11 row (`FIRST_BATCH_OPEN_INPUTS.md:35`) records a designated issuer and default approver, a designated alternate, a default scope, no periodic reconfirmation, immediate withdrawal on record, and the rule that the AI cannot widen its own delegation. It leaves the automatic service, automatic limits and batch post-checks undecided. This file copies none of that and changes none of it.

## 4. Decision axes

Three axes: when (G), the I11 limits (L), and revocation (R). On each, the recommendation is a form, not a value.

**Invariants, not options.** These hold under every option below and this file does not offer to relax them:

- The AI cannot widen its own grant, reissue it, or revive it (I11; DLG-06, DLG-07, DLG-32).
- Model output alone cannot issue or pay (DLG-05; `DEVELOPMENT_PLAN.md:552`; program decisions `:49`).
- No agent holds keys (`AGENTS.md` §16).
- Credit stays excluded unless a separate User decision names it. That is the F04 criterion O-8 ([F04 lift criteria](F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md) `:153`).
- UNKNOWN stays UNKNOWN. A timeout, a single NotFound, or a missing record is not "not executed" (`DEVELOPMENT_PLAN.md:296-301`).

### When (G)

| Option | Consequence in plain terms | Recommendation |
|---|---|---|
| G1. Turn it on as soon as the §5 checklist is complete | Fast. The checklist then acts as the switch, so a checklist that is complete on paper but wrong in practice turns on real authority with no further look | Not recommended |
| G2. The checklist is only a bar. Turning it on is a later, separate User decision plus an Astra ruling, in a named non-production scope first | Slower. Each step has a person who says yes. A scope that has not cleared the bar stays held. Nothing in this file has to be undone if the checklist is not met | **Recommended** |
| G3. State a permanent prohibition | Delegated execution would be written as never allowed. The program decisions say a lock is a door that opens when evidence exists, not a permanent ban (`PROGRAM_DECISIONS_20260928.md:25`). Choosing this would be a different decision from the one on record | Not offered as a recommendation; see O4 |

### The I11 limits (L)

I11 is not complete. The items below are what still has to be set before any grant can be real. Every value cell is empty on purpose.

| Item | What has to be set | Owner | Value here |
|---|---|---|---|
| Service identity | Which AI service identity a grant names, and which humans besides the designated issuer and alternate are accountable (U11-ID) | `DECISION_REQUIRED · Astra` and User | empty |
| Per-action, cumulative and count limits | Three limits and a currency. The contract allows no default and no "unlimited" (DLG-14) | `DECISION_REQUIRED · Astra` (U11-L) | empty |
| Aggregation window and anti-splitting basis | What is summed: per order, per account, per period; and whether several issuers' grants for one agent add up (contract §4, §9) | `DECISION_REQUIRED · Astra` (U11-L) | empty |
| Grant period | Length and the authoritative time source (A5) | `DECISION_REQUIRED · Astra` | empty |
| Grantable surfaces and allowed proposal kinds | Which surfaces a grant may name; which proposal kinds are allowed (contract §9) | `DECISION_REQUIRED · Astra` | empty |
| Allowed-operation set and grant TTL on the chain | `GrantControl` has neither (Move source `:212`) | `DECISION_REQUIRED · Astra`, and a new command if the answer needs one | empty |
| Pause and resume | The mock has revocation and a new generation only (contract §9) | `DECISION_REQUIRED · Astra` | empty |
| Batch post-check owner and deadline | Who checks after the fact, and by when. I11 leaves automatic batch post-checks undecided | `DECISION_REQUIRED · Astra` for the deadline; the owner is named by the User | empty |

| Option | Consequence in plain terms | Recommendation |
|---|---|---|
| L1. Put the values in this merge | One step. The values would be invented by the builder, and the contract says fixture ranges are not limits (DLG-34) | Not offered |
| L2. A later User decision document carries the values after Astra proposes them | The numbers come from the owner and are visible when the User merges them. This file stays a form | **Recommended** |
| L3. Leave the values to whoever implements it | Fast, and the implementer ends up setting product policy. The contract forbids the AI from widening its own scope, and an implementer would be doing the same by default | Not recommended |

### Revocation (R)

What revocation guarantees today, and where it stops.

| Guarantee | Where it holds | Where it does not hold |
|---|---|---|
| A revoked generation stops that generation's tool use at once, pending proposals are voided and kept, history stays, and the same `grant_id` is not revived (DLG-20 to DLG-24) | The in-memory mock only | Nowhere on the chain or in the executor |
| One write closes the grant. Every delegated path aborts with `EGrantClosed` from then on. Pre-cut obligations such as live tickets and refund duties are kept | The localnet `GrantControl` (`rights_scale.move:909-921`) | Operationally: the localnet is a fixture, and the issuer must still be able to sign |
| After the cut the map refuses new reserves and unknown-marking, fences old commands, and replays stored first results | The in-memory map (crate README) | Durability of the map; authentication of who calls it |
| Signed bytes that are already out are not recalled | Not guaranteed anywhere. `DEVELOPMENT_PLAN.md:296-301` says the local fence does not cancel a valid signed transaction already outside | Always. This is why the cut is a stop on new commitments and not a recall |
| After the cut, resend only the same bytes and only with proven permission. Otherwise look up and reconcile only | A rule in the plan and the profile (`DEVELOPMENT_PLAN.md:296-301`; profile §10 item 6) | Whether the rule is followed depends on the executor |

Still open under revocation: the finality policy that closes `H_g` (A4), the authoritative time source (A5), the raw key held outside the gate (A7), the completeness of the send-path list (A8), and a non-cooperating executor (A10). The review pack records each as unsupplied ([I12 review pack](../status/I12_REVIEW_PACK.md)). The cut is proven, if at all, only for a cooperating executor and only for scopes the proof covers.

| Option | Consequence in plain terms | Recommendation |
|---|---|---|
| R1. Accept the cooperating-executor guarantee only (I12 branch 1) | Smaller ask. Unproven scopes stay held. An executor that is not cooperating, or that gives an incomplete history, leaves its scope unproven and held | Acceptable fallback |
| R2. Also require a design for a non-cooperating executor (I12 branch 2) before any enablement | Closer to what an enabled system needs. The design may need an on-chain anchor or a new command, so it is `DECISION_REQUIRED · Astra`. The cut-proof document already recommends branch 1 as accepted and branch 2 as a condition before this node (`CUT_PROOF_I12_20261008.md:138`), and that recommendation is itself undecided until the User merges it | **Recommended** |
| R3. Independent review of the proof first, then choose | Slowest. Matches branch 3. The proof needs a non-author review and a User trust-policy approval anyway | Not recommended as the only step; it is already a prerequisite in §5 |

## 5. Prerequisites for a later request to enable delegated execution

A checklist for a later, separate proposal. Completing it is not approval. Every cell is empty on purpose. "Status today" is read from the cited source.

| ID | Prerequisite | Evidence a later proposal would bring | Status today | Owner |
|---|---|---|---|---|
| DX-1 | Astra review of the rights-scale profile and the delegation contract | A ruling text. Both are drafts | Not on the tree (register `:156-157`; plan `:534`) | `DECISION_REQUIRED · Astra` |
| DX-2 | I11 service identity and limits (§4 L) | A merged User decision document carrying the values | Empty | `DECISION_REQUIRED · Astra`, then User |
| DX-3 | I12 closed: independent non-author review, User trust-policy acceptance, a recorded branch | The review text and the recorded choice | Not recorded (`FIRST_BATCH_OPEN_INPUTS.md:36`) | User names the reviewer; Astra |
| DX-4 | Finality policy for `H_g` (A4), time source (A5), non-cooperating executor design (A10) | Astra decisions, with a new command if needed | Unsupplied (review pack) | `DECISION_REQUIRED · Astra` |
| DX-5 | Durable authority: ordered commit authority, durable generation check, durable approval and late-receipt path (A1, A2, I13) | Merged Track K stage nodes (`k-stage4-adoption-decision`, `k-stage5-durable-tx`) | Not merged. In-memory models only | Track K; User |
| DX-6 | Send-path completeness (A8) and evidence availability (A6, I13) | A complete send-path list, and a history readable by an independent party | Unsupplied | Operations and security |
| DX-7 | Key custody (A7), including who can write the cut | A merged key-management decision and the RS-5 decision | Proposed only; not merged | User; `rs-5-decision` |
| DX-8 | Binding the contract's limits and revocation to the chain grant and the executor | Design and tests that connect the mock, the chain and the map | No roadmap node covers it. Follow-up candidate, not created here | `DECISION_REQUIRED · Astra` |
| DX-9 | Authenticated principals for the executor | A design that names who may call the map | The map does not authenticate (crate README `:23`) | `DECISION_REQUIRED · Astra` |
| DX-10 | `IssuerCap` handling | An Astra choice among the three options in profile §13 | OPEN | Astra, after the probe |
| DX-11 | `cancel_show` and the private-path delegation gate (RS-3a classification B items 2 and 4) | Astra rulings | Recorded, not decided | `DECISION_REQUIRED · Astra` |
| DX-12 | Measured load at the larger rights-scale levels | Merged L2 and L3 records (`rs-4-l2`, `rs-4-l3`) | Level one only; the larger levels are `not covered` (register) | RS-4 |
| DX-13 | Legal character of acts by an AI, and what binds the issuer | A written view | `UNDETERMINED · 법무`, started through the User (D-E) | `UNDETERMINED` |
| DX-14 | Who bears residual risk after the cut | A User statement | Not stated | `DECISION_REQUIRED · User` (U-R2) |
| DX-15 | Exact-head CI and a non-author review of the later enabling change | Run IDs and review text for that head | None, by nature | A later node |
| DX-16 | Separate explicit User approval naming the enabling and its scope | A later User merge or other explicit OK | None | `DECISION_REQUIRED · User` |

## 6. Options for the User on this document

The recommendation is a suggestion. It is not acted on. The builder does not merge, does not edit the flag or a lock row, and does not start a later node.

### O1. Adopt the shape: G2, L2, R2

Consequence in plain terms: enabling delegated execution becomes a later, separate decision, backed by an Astra ruling, with the §5 list as the bar, the I11 values supplied by Astra and merged by the User, and a design for a non-cooperating executor required first. Merging creates no grant, turns nothing on, and fills in no limit, name or date. This is the suggestion.

### O2. Adopt G2 and L2 with R1

Same as O1, but only the cooperating-executor guarantee is required.

Consequence in plain terms: a smaller bar. A later request could move forward without a non-cooperating design. Scopes that the proof does not cover stay held, and a failure by an uncooperative executor is something the User would accept. That residual risk is not sized here.

### O3. Defer

Adopt no shape.

Consequence in plain terms: the question stays open. The flag stays off, and anyone who later wants to enable delegated execution has to start this proposal again.

### O4. State a permanent no-delegated-execution prohibition

Consequence in plain terms: delegated execution would be written as never allowed. That differs from the principle on record that a lock is a door (`PROGRAM_DECISIONS_20260928.md:25`). This file does not make that decision.

## 7. What this document does not authorize

The §5 locks, in the words already adopted (`PROGRAM_DECISIONS_20260928.md:108-117`), all stay: the two kernel blobs; real funds and real PG, bank and KYC calls; real credit and regulated finance; Sui testnet; Sui mainnet; public operational endpoints; R2 and an own replication, consensus or storage engine; integration (a) of PR #11; a new coin or TIX module; stable 1.0 and the bulk rename. Not one is satisfied here.

Also not authorized:

- A change to `delegated_execution_enabled`, to `runtime/ARCHITECTURE.toml`, or to the architecture verifier or its test.
- A new protocol command, an on-chain anchor, a kill switch, or any change to `docs/contracts/*` or `docs/adr/*`.
- Any connection between the mock, the chain and the executor, a service, or an AI identity.
- A production runtime, live-money execution, a key, a secret, or any network call.

This file does not edit the blueprint, the roadmap, the development plan, the capability register, any ADR or any contract. `docs/README.md` gains one index row and one validation bullet so a reader can find this file. That index is not an approval. The register rows stay as they are.

## 8. Register

No row below is closed by this document. Product policy values and new protocol commands are `DECISION_REQUIRED · Astra`. Legal and provider answers stay `UNDETERMINED` with the owner named.

| Item | Class | Owner | What this document does |
|---|---|---|---|
| Per-action, cumulative and count limits, window, anti-splitting basis | `DECISION_REQUIRED · Astra` | Astra | States none |
| Grant period and time source | `DECISION_REQUIRED · Astra` | Astra | States none |
| Service identity and further accountable humans | `DECISION_REQUIRED · Astra` and User | Astra and User | Names no one |
| Grantable surfaces, proposal kinds, allowed operations, grant TTL, pause and resume | `DECISION_REQUIRED · Astra` | Astra | States none |
| Post-check owner and deadline | `DECISION_REQUIRED · Astra` (deadline); User names the owner | Astra, User | States none |
| `H_g` policy, non-cooperating executor design, any new command or anchor | `DECISION_REQUIRED · Astra` | Astra | Adds none |
| `IssuerCap` handling | `DECISION_REQUIRED · Astra` | Astra, after the probe | Picks none |
| `cancel_show` and private-path gates | `DECISION_REQUIRED · Astra` | Astra | Decides none |
| Binding limits and revocation across mock, chain and map; authenticated principals | `DECISION_REQUIRED · Astra` | Astra | Creates no node |
| I12 branch and independent reviewer | `DECISION_REQUIRED · User` | User | Records no branch |
| Residual-risk bearer (U-R2) | `DECISION_REQUIRED · User` | User | Does not decide |
| Credit under delegated execution (F04 O-8) | `DECISION_REQUIRED · User` | User | Excludes it |
| Legal character of acts by an AI (D-E) | `UNDETERMINED · 법무` | Legal review, started through the User | States no conclusion |
| Astra-gate cell mismatch (§1) | Recorded, not resolved | Not assigned by this document | Follows `user_merge: true` and edits no source |
| Enabling itself | `DECISION_REQUIRED · User` | User, after Astra | Does not enable |

## 9. Coverage (AGENTS §7), classification (§8), non-claims, references

### Coverage (`AGENTS.md` §7)

This node adds no test. It is prose.

| Requirement | Coverage | Action here |
|---|---|---|
| The mock refuses execution and keeps the contract predicates | Covered by `reference/ai_delegation/test_ai_delegation_mock.py` (offline, in-memory) | Cited. Not duplicated |
| The architecture flag stays off | Covered by `scripts/verify_runtime_architecture.py` and `scripts/test_runtime_architecture.py` | Cited. Run unchanged |
| The chain cut and the map's behavior after it | Covered for the fixtures by the RS-3a and RS-3b records and tests | Cited. Not duplicated |
| Limits, period and scope on the chain; binding of mock and chain; authenticated principals; non-cooperating revocation | Not covered. §3 findings 1, 2 and 4, and I12 A10 | No test added. These are the open prerequisites in §5 |

### Classification (`AGENTS.md` §8)

A. The off-switch matches its sources in §2. The cut behavior matches the Move source and the crate README.

B. Contract undefined, recorded and not invented:

- Limits, period and allowed operations on the chain grant.
- The link between mock revocation and the chain cut.
- `cancel_show` against grants, and the private-path gate.
- The I12 branch, the `H_g` policy, the time source, and the non-cooperating design.
- The Astra-gate cell mismatch in §1.
- Every value in §4 L.

This document does not invent those semantics and does not amend a contract, an ADR, the blueprint or the roadmap.

C. No explicit contract violation. No locked file is changed. Delegated execution stays off, which is what the sources say. No merge blocker of class C is filed.

### Non-claims

This document does not claim that the proposed shape is sufficient, safe or tested, that merging it enables anything, or that a completed §5 checklist enables anything by itself. It does not claim that testnet, mainnet, real PG, bank, KYC, a public endpoint, a token module or R2 is unlocked. It states no legal conclusion about acts by an AI. It states no claim of production readiness, durability, distributed fencing, bank exactly-once or chain finality. It states no limit, window, period, quorum, service level, date or cost. It does not claim that exact-head CI has run for a head that includes this file. A documentation-only green is not full verification. The author's check is not an independent review. Nothing was enabled, deployed or connected.

### References

Pinned to observed `origin/main` `47eed4b01b93dc4b00e102729bad1c74abdbae95`.

- `AGENTS.md` §4; §5; §6; §10; §11; §12; §14; §16; `:30`.
- `docs/decisions/PROGRAM_DECISIONS_20260928.md` §0; `:25`; `:49`; §5 `:108-117`.
- `docs/decisions/PROGRAM_ROADMAP_20260930.md` §0 `:14-15`; §1; §3 table `:139`.
- `docs/decisions/CUT_PROOF_I12_20261008.md` §4 (A1 to A10), §5, `:138`.
- `docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md:153`.
- `docs/decisions/TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md`.
- `docs/contracts/AI_DELEGATION_AUTHORITY.md` §0; §4; §6 (DLG-01 to DLG-36); §9; §10.
- `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md:35-36`.
- `docs/contracts/RIGHTS_SCALE_PROFILE.md` §10; §13.
- `docs/contracts/STATE_LIFECYCLE.md:419`, `:454-455`.
- `docs/DEVELOPMENT_PLAN.md:296-301`, `:530-536`, `:552`.
- `docs/status/I12_REVIEW_PACK.md` assumption rows A1 to A10.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md:139`, `:156-157`.
- `docs/aiops/PROGRAM_ASTRA_DELEGATION.md:77`.
- `.aiops/program.json:639-650`.
- `runtime/ARCHITECTURE.toml:29`; `runtime/crates/kix-delegated-exec/README.md:15-30`.
- `scripts/verify_runtime_architecture.py:53`; `scripts/test_runtime_architecture.py:48`.
- `reference/rights_scale/sui/sources/rights_scale.move:212`, `:898-900`, `:909-921`.
- `reference/ai_delegation/ai_delegation_mock.py`; `validation/2026-10-14-rs-3a-delegation-primitives/README.md`; `validation/2026-10-14-rs-3b-delegated-exec/README.md`.
