# I12 review pack — builder-authored evidence for the non-author review

**This document is not a review, not an acceptance, and not a change of status.**
It is builder-authored evidence, prepared so that the non-author independent
review of `docs/decisions/CUT_PROOF_I12_20261008.md` — and the User's
trust-policy approval that the I12 open-inputs row requires — has the
traceability, open-item and discrepancy material in one place. Writing it does
not review, accept, confirm or close I12; it records no option 1/2/3
acceptance; it does not unblock `k-stage2-v5-impl`'s residual stop; it does
not execute the proof's recommendation.

## 0. Basis

- Node: `plan-i12-review-pack` (loop-proposed; not in `.aiops/program.json`;
  no task file under `docs/tasks/`; the node spec is the task input).
- Observed `origin/main` and branch HEAD: `5e8ee3f1882d97f1c442fe485407e51822ec22ce`.
  `git fetch origin main` was not run (this session forbids network/GitHub
  actions); the value is the local `origin/main` ref, equal to HEAD.
- Locked blobs verified at that base: `runtime/crates/kix-kernel/src/lib.rs`
  `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
  `b607996c83a119c349f1cc90469ac1ba82764e20`. This node does not touch them.
- Document under review (unchanged by this node):
  `docs/decisions/CUT_PROOF_I12_20261008.md`, merged by the User in PR #136 at
  `ae869f38438d8174103171ec741a41376aee60df`. The dev plan §5 merged-documents
  table records "기록된 수락 갈래 없음. §5는 선택지 1/2/3을 제시하고 채택 문장을
  두지 않는다. I12 미완결." (`docs/DEVELOPMENT_PLAN.md:140`). The proof itself
  states it is a draft ("제안이자 증명 초안", proof :3), not an independent
  review ("이 파일은 독립 검토가 아니다", :5), and that I12 stays open until the
  protocol owner's technical proof, a non-author independent review and the
  User's trust-policy approval meet (:5; open-inputs row I12,
  `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md:36`).
- Adjacent node cited, not built: `plan-i12-cut-proof-bounded-model`
  (recorded in `/workspace/kix-run/state/planned_nodes.json`; plan file
  `/workspace/kix-run/plans/plan-i12-cut-proof-bounded-model_plan.md`; both
  paths are outside this repository). Its target `reference/cut_proof_model/`
  does not exist in this tree. This pack maps only evidence that already
  exists; it does not supply the bounded model.
- Mechanical check: `scripts/check_i12_proof_ids.py` (stdlib only,
  `--self-test`) verifies that the proof still defines each `P1`–`P4` as a
  `### P` heading and each `A1`–`A10` as a first-column key of its proof §4
  table, that this pack carries each id exactly once as a first-column key in
  its §1 table, and that every `proof §N` reference in the pack resolves to a
  `## N.` heading in the proof. It is a convenience check, not a contract
  gate, and is not wired into CI.
- Amendment 2026-10-26: `scripts/check_i12_proof_ids.py` is now wired, plain and `--self-test`, into the `Stdlib offline document checks` step of `.github/workflows/protocol.yml` by #199; the "not wired into CI" wording above records the state when this pack was written.

## 1. Coverage table — P1–P4 and A1–A10

Every proposition and assumption the proof defines appears exactly once below.
"Existing machine-checked evidence" lists paths and lines, verified at the
recorded base, that mechanically exercise the cited behaviour in the locked
in-memory kernel. Kernel line numbers are stable because the file is locked;
test/doc line numbers are at the recorded base. The status column marks each
row `machine-checked in-memory model only`, `prose-only`, or
`depends on unimplemented`. The owner column restates the proof's own 주인
cell; this table chooses nothing.

| ID | Proof location | Existing machine-checked evidence (path:line) | Status | Named owner / trust policy |
|---|---|---|---|---|
| P1 | proof §3 `:53-59` | None. `GrantControl` consumption-ordering is draft predicate text only: RS-C06(b) `docs/contracts/RIGHTS_SCALE_PROFILE.md:144`, blueprint §6 rule 4 `docs/blueprints/rights-scale-v1/README.md:372`, profile §10 item 4 `:183`. Blueprint `:365` states the real grant and non-cooperative revoke are unimplemented and delegated execution is disabled | prose-only; depends on unimplemented (Move grant, `rs-1-issuercap-probe`, RS-3a) | A3 (RS-3a), A4 (Astra) |
| P2 | proof §3 `:61-67` | `lib.rs:22` (`SEMANTICS_VERSION = 4`), `:35-38` (`ExecutionFence{owner,generation}`), `:365-371` (`context()` rejects `UnsupportedSemantics`/`ExecutionFenced`), `:509-510`,`:521-529` (model-only comments). Tests: `transitions.rs:188-214` (`ExecutionFenced` at `:212`), `:238-248`, `:624-645`; model drivers `contract_invariants.rs:250-251`, `e4_state_model.rs:109-110` | machine-checked in-memory model only; the durable-store check (A2) does not exist | A1, A2 (Track K) |
| P3 | proof §3 `:69-79` | Commit channel: the P2 rows above. PG channel: `submitted_under` recorded at reserve (`lib.rs:134`,`:435`), `mark_payment_unknown` (`:459-487`), `observe_capture` conflict retention (`:540-560`); tests `transitions.rs:81-91` (`submitted_under` bound at `:87`), `:351-383` (quarantine blocks the send transition at `:378`), `:251-273` (late capture applied under the new owner, `submitted_under` preserved at `:272`). Signature channel: none | commit and PG channels machine-checked in-memory model only; signature channel prose-only; no adapter exists | A1·A2 (commit), A8 + ADR-0001 `:76`,`:78` (PG), A7 (signature) |
| P4 | proof §3 `:81-91` | `transitions.rs:228-235` (UNKNOWN not released by TTL), `:251-273` (historical capture after owner change not discarded), `:276-291` (late capture does not release the new buyer), `:294-306` (ReturnRequired marker, not resurrection), `:441-463` (retained conflict replays at capacity), `:464-492` (capacity failure keeps quarantine and original evidence), `:493-524` (retained conflict blocks a later binding), `:608-623` (bounded backpressure, no eviction); `quarantine_capacity.rs` (locked; cited only) | retained-evidence / immutable-first-result semantics machine-checked in-memory; Σ_g completeness and the `Q − Issued − Unissued − Unknown` arithmetic are prose-only | A6, A8, A1 |
| A1 | proof §4 `:109` | `replace_owner` model only (`lib.rs:521-529`); `transitions.rs:188-214`. Prose authority: model 1 `:14-15`, ADR-0001 `:92` | memory model only; no distributed ordered-commit authority exists | Track K; backend adoption is a later User decision (`k-stage4-adoption-decision`) |
| A2 | proof §4 `:110` | `context()` in-process check only (`lib.rs:365-371`,`:509-510`). No durable store checks a generation before committing; Track K stage 5 is gated | absent; depends on unimplemented (Track K backend; adoption proposal merged #140, implementation not started) | Track K |
| A3 | proof §4 `:111` | None. RS-C06(b) `docs/contracts/RIGHTS_SCALE_PROFILE.md:144` is a draft predicate; blueprint §6 rule 4 `:372` and profile §10 item 4 `:183` are prose | draft predicate; Move grant unimplemented; depends on `rs-1-issuercap-probe` and RS-3a | RS-3a |
| A4 | proof §4 `:112` | None. Sui research §2-2 `:144` distinguishes certified effects from lookup-path NotFound; neither is chosen as the H_g policy | DECISION_REQUIRED · Astra; no value chosen | Astra |
| A5 | proof §4 `:113` | None. Lifecycle `:100` and AI delegation §9 `:294` record the time source and C_g/H_g as 미정/UNDETERMINED | UNDETERMINED; the value is a product policy — DECISION_REQUIRED · Astra | contract row: this proof node + RS-3a; value: Astra |
| A6 | proof §4 `:114` | None. Open input I13, model 1 `:33`, question sheet O13 | UNDETERMINED; independent history availability is not built | operations/security (I13) |
| A7 | proof §4 `:115` | None. Sui research `:118` and dev plan `:273-274` (the proof cites `:258-259`; see B-1) are prose | UNDETERMINED; no testnet key decision, no real keys | User; later node `testnet-key-management-decision` (not started here) |
| A8 | proof §4 `:116` | Partial. ADR-0001 `:76` is prose authority; the model carries `submitted_under` (`lib.rs:134`,`:435`) and the pre-send UNKNOWN transition (`:459-487`), exercised by `transitions.rs:81-91`,`:351-383`. The complete send-path list is not machine-enumerated anywhere | UNDETERMINED; partial in-memory model evidence only | operations/security (I13) + Track K v5 |
| A9 | proof §4 `:117` | None — this pack is not that review. Open inputs `:36`; question sheet P12-V `:96` | UNDETERMINED; reviewer identity and same-version review evidence not supplied | User names the reviewer |
| A10 | proof §4 `:118` | None. Model 1 `:31-33` and blueprint `:365` (the proof cites `:366`; see B-2) record non-cooperative revoke as unimplemented | UNDETERMINED; the proof's central open item; any new design is DECISION_REQUIRED · Astra | Astra if the design needs an on-chain anchor or new command |

## 2. Inputs only the owner can supply — none supplied here

| Input | What only the owner can supply | Where the proof names it |
|---|---|---|
| Non-author reviewer (A9) | The reviewer's identity and the review evidence over the same source version | proof §4 `:117`; open inputs `docs/contracts/FIRST_BATCH_OPEN_INPUTS.md:36`; question sheet P12-V `docs/status/FIRST_BATCH_OWNER_QUESTION_SHEETS_KO.md:96` |
| Trust-policy approval | Per-assumption acceptance of the proof §4 신뢰정책 column | proof §4 `:107-118`; open inputs `:36` ("사용자 신뢰정책 승인 전") |
| Option 1/2/3 acceptance record | Which §5 branch is accepted; none is recorded | proof §5 `:124-138`; dev plan table `docs/DEVELOPMENT_PLAN.md:140` ("기록된 수락 갈래 없음") |
| H_g finality policy (A4) | certified effects vs checkpoint as the closing rule | proof §4 `:112` — DECISION_REQUIRED · Astra |
| Time source and values (A5) | The authoritative clock, its name and failure behaviour | proof §4 `:113` — UNDETERMINED / DECISION_REQUIRED · Astra |
| Non-cooperative design (A10) | Any new on-chain commitment anchor or protocol command | proof §4 `:118`, §5 `:145` — DECISION_REQUIRED · Astra |
| Orphan liability | Legal owner of 고아/늦은 사실 obligations | proof §5 `:144` — D-E, legal counsel (User) |
| Hold length / reclaim policy | 보류 기간·손실 부담·잔량 회수 수치 | proof §5 `:142-143` — DECISION_REQUIRED · Astra |

## 3. Findings while tracing — AGENTS.md §8 classification, no silent fixes

Quotes are verbatim; line numbers are at the recorded base. Class A =
contract-defined and matching; B = contract-undefined or recorded
characterization; C = explicit contract violation. **No class C item was
found** while tracing or by the checker; no fix was applied to any document.

### 3.1 Class A — defined and matching

- **A-1: Every kernel line the proof cites resolves exactly.**
  `lib.rs:22` is `pub const SEMANTICS_VERSION: u16 = 4;`; `:35-38` is the
  `ExecutionFence{owner, generation}` struct; `:365-371` is `context()`
  rejecting `UnsupportedSemantics` and `ExecutionFenced`; `:509-510` is
  "Local state-model fence only: NOT a cluster-wide cancellation barrier."
  on `cancel_scope`; `:521-529` is "Models ordered ownership replacement.
  Actual distributed handoff, membership, old-writer fencing, and state
  transfer are NOT implemented." on `replace_owner`; `:134` is the
  `submitted_under` field and `:435` binds it to `ctx.fence` at reserve;
  `:459-487` is `mark_payment_unknown`; `:540-560` is `observe_capture`'s
  conflict retention.
- **A-2: ADR-0001 citations are verbatim.** `:76` "Only committed external
  intents are executable. Commit an in-flight/UNKNOWN transition before
  sending."; `:78` "Internal fencing stops new internal writes by an old
  owner; it cannot cancel a request already sent to a provider."; `:88` the
  four-state distinction and "A local scope fence does not imply all these
  states."; `:92` "`cancel_scope` and `replace_owner` implement local ordered
  model transitions ONLY."
- **A-3: The named tests assert what the proof needs.** `transitions.rs:212`
  asserts `Err(KernelError::ExecutionFenced)` for a stale-generation write;
  `:378` asserts `mark_payment_unknown` is `InvalidTransition` while the
  order is quarantined; `:272` asserts `submitted_under` still holds the
  submitting fence after `replace_owner`; `:624-645` asserts
  `UnsupportedSemantics` and `ClockRegression` leave state untouched.
- **A-4: Id and section integrity is machine-checked.**
  `scripts/check_i12_proof_ids.py` exits 0 on this tree: the proof defines
  P1–P4 as `### P` headings and A1–A10 as first-column §4 keys exactly once
  each, the pack cites each exactly once, and every `proof §N` reference
  resolves.

### 3.2 Class B — drifted or undefined; recorded, not resolved

- **B-1: Dev-plan line citations in the proof have drifted; the cited
  sentences are unchanged.** Proof `:115` cites "개발계획 258–259행" for
  "머신·키 하나 또는 Raft 리더 변수만으로 fencing이 성립했다고 보지 말라고"; the
  sentence now lives at `docs/DEVELOPMENT_PLAN.md:273-274` ("머신/키 하나 또는
  Raft leader 변수만으로 실제 서명 권한의 fencing이 성립했다고 간주하지 않는다").
  Proof `:77` cites "개발계획 261–262행" for the same limit; the sentence now
  lives at `:275-279` ("로컬 fence는 이미 외부에 나온 유효한 서명 거래를 취소하지
  않는다"). The dev plan gained lines after the proof's recorded base
  `7be6b75…` (proof `:11`). Recorded, not fixed — the pack does not edit the
  proof.
- **B-2: Blueprint line citations have drifted by one.** Proof `:59` and
  `:118` cite blueprint `:366` for "실제 grant와 비협조 회수가 미구현이고 위임
  실행이 비활성"; the sentence is at `docs/blueprints/rights-scale-v1/README.md:365`.
  Proof `:57` cites "규칙 4(371–372행)"; rule 4 is the single line `:372`
  (`:371` is rule 3). Content verified verbatim at the new lines.
- **B-3: The model-versus-distributed gap is already declared, not hidden.**
  Model 1 `:14-15` (local generation is not chain lease generation;
  `replace_owner` is not real fencing/state transfer), ADR-0001 `:92`, and
  the kernel comments `:509-510`,`:521-529` all state the same limit the
  proof relies on. The pack repeats it rather than discovering it.
- **B-4: The §2 bundle-record field list and the five-step order are the
  draft's proposals.** The proof itself records that LC-CUT requires a
  relation proof without giving fields (proof `:35`), and that model 1 and
  LC-CUT do not carry the five steps in order (`:45`; blueprint `:373`;
  profile `:184`). Until the User merges an acceptance, these are not
  contract sentences.

### 3.3 Class C — explicit contract violation

None. The locked kernel not implementing fencing is the state that model 1
`:15` and ADR-0001 `:92` already record — the proof's own classification
(proof `:185`), not a new violation and not a reason to touch the lock.

## 4. Reviewer checklist — questions for the named reviewer

1. Does the conditional, model-level reading of P1–P4 hold on the proof's own
   terms — i.e. does each sketch plus its named assumptions entail its
   sentence, with no step silently stronger than A1–A10 allow?
2. Is the §1 status column fair: P1, the signature channel of P3, and the
   Σ_g/Q arithmetic of P4 prose-only; P2 and the commit/PG channels of P3
   machine-checked only inside the in-memory model; nothing durable?
3. A1/A2 — is the `context()`/`ExecutionFenced` check honestly an in-process
   model of "the store checks the current generation before durably
   committing", and does the review agree no durable check exists yet?
4. P3 PG channel — does `submitted_under` plus `mark_payment_unknown` plus
   conflict retention evidence the ADR-0001 `:76`/`:78` split (commit before
   send; fencing cannot cancel a sent request), or does the reviewer read
   more into it than a model allows?
5. E_g ⊆ Σ_g (proof `:89`) — the proof says a path that sends before
   committing breaks the inclusion. Is the A8 send-path list complete enough
   to review, given it is UNDETERMINED?
6. Case splits — in the "체인이 먼저" branch (proof `:98`), is treating the
   orphan interval's commitments as debt candidates rather than inventory
   errors correctly marked UNDETERMINED for the legal owner?
7. Line-drift findings B-1/B-2 — should the proof's stale line numbers be
   corrected in a later revision, and does the drift change any citation's
   meaning (this pack verified each target sentence verbatim)?
8. A9 — which reviewer does the User name, and what artefact constitutes the
   same-version review evidence (the proof names the question-sheet row
   P12-V as the shape of the answer)?
9. Trust policy — the proof §4 신뢰정책 column lists one policy sentence per
   assumption; does the User approve each verbatim, or does any row need
   rewording before acceptance?
10. Option 1/2/3 — if the User accepts an option, should the acceptance
    record also state explicitly that delegated execution stays off and the
    residual `k-stage2-v5-impl` stop is unaffected?

## Non-claims

- Builder-authored evidence only; not a review, not an acceptance, not a
  change of status, and not the non-author independent review that the I12
  row requires before closure.
- No proof, contract, blueprint, decision-record or kernel byte was edited;
  no policy value, time-source number, H_g finality policy, path or command
  was chosen; every UNDETERMINED/DECISION_REQUIRED item keeps its named
  owner.
- `scripts/check_i12_proof_ids.py` is a mechanical convenience check on
  headings, first-cell table keys and `proof §N` references. It does not
  judge semantics, is not wired into CI, and its pass is not a contract
  gate.
- Amendment 2026-10-26: `scripts/check_i12_proof_ids.py` is now wired, plain and `--self-test`, into the `Stdlib offline document checks` step of `.github/workflows/protocol.yml` by #199; the "not wired into CI" wording above records the state when this pack was written.
- The parked bounded-model node (`plan-i12-cut-proof-bounded-model`) is
  cited, not built; nothing under `reference/cut_proof_model/` exists.
- Local command results are recorded in
  `validation/2026-10-13-i12-review-pack/README.md`. They are not exact-head
  CI and are not independent verification.
- PROGRAM_DECISIONS §5 locks are untouched: no real funds, real PG/bank/KYC
  calls, public endpoints, Sui testnet/mainnet, R2, storage engine, secrets
  or production runtime were touched or needed.
