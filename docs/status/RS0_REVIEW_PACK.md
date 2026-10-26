# RS-0 review pack — builder-authored evidence for the Astra review

**This document is not a review, not an acceptance, and not a change of status.**
It is builder-authored evidence, prepared so that the Astra architecture review
of `docs/contracts/RIGHTS_SCALE_PROFILE.md` 0.1 and
`docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md` — and the User's
acceptance record that the `rs-1` stop requires — has the traceability,
open-item and discrepancy material in one place. Writing it does not review,
accept, confirm or merge anything, and it does not unblock `rs-1`.

## 0. Basis

- Node: `plan-rs0-review-pack` (loop-proposed; not in `.aiops/program.json`;
  no task file under `docs/tasks/`; the node spec is the task input).
- Observed `origin/main` and branch HEAD: `ba352dfe9789af89983e9c1b1a303461ea240016`.
  `git fetch origin main` was not run (this session forbids network/GitHub
  actions); the value is the local `origin/main` ref, equal to HEAD.
- Locked blobs verified at that base: `runtime/crates/kix-kernel/src/lib.rs`
  `69564b166f0c27f9af5d8422f0a466b18d74c20f`,
  `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`
  `b607996c83a119c349f1cc90469ac1ba82764e20`. This node does not touch them.
- Documents under review (unchanged by this node):
  - `docs/contracts/RIGHTS_SCALE_PROFILE.md` ("계약 0.1 (초안)",
    `docs/contracts/RIGHTS_SCALE_PROFILE.md:1`; "초안. 미검토. 미측정." `:3`;
    "Astra 아키텍처 검토와 사용자 병합 전에는 확정이 아니다" `:7`).
  - `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md` ("결정 초안." `:3`;
    confirmation is Astra review + User merge `:3,:31,:59`).
  - `docs/blueprints/rights-scale-v1/README.md` (historical proposal, kept as-is).
- Stop record this pack serves: `/workspace/kix-run/state/rs-1.decision.md`
  (outside the repository). It records that `rs-1` needs an Astra architecture
  review of the two texts plus a User record that the reviewed text is the
  accepted RS-0 contract, and that the owner selected option 1 on 2026-10-09
  (`/workspace/kix-run/state/rs-1.decision_answer.md`) without naming a commit
  or saying profile 0.1 is accepted — the confirmation step is still open.
- Capability register state (cited, not edited):
  `docs/status/CURRENT_CAPABILITY_REGISTER.md:146` records RS-0 as merged draft
  documents only ("확정 조건의 Astra 아키텍처 검토·… 미충족"); `:147` records
  RS-1 as "not covered; RS-0 후 1,024 public localnet/IssuerCap 동시 probe".
- Mechanical check: `scripts/check_rs_profile_traceability.py` (stdlib only,
  `--self-test`) counts each RS-C/IM id used as a first-column table key on
  both documents. It is a convenience check, not a contract gate, and is not
  wired into CI.
- Amendment 2026-10-26: `scripts/check_rs_profile_traceability.py` is now wired, plain and `--self-test`, into the `Stdlib offline document checks` step of `.github/workflows/protocol.yml` by #170; the "not wired into CI" wording above records the state when this pack was written.

## 1. Traceability table — RS-C01..RS-C17 and IM-01..IM-30

All 17 RS-C and 30 IM ids appear exactly once below. Columns: blueprint
location (id definition), profile location (contract text), proposed test id
(profile §8 column; `—` where the profile defines none), and the owning node
per blueprint §8.1 (`docs/blueprints/rights-scale-v1/README.md:443-451`) and
the RS-node scope rows (`:472`, `:484`, `:497`). The profile confirms the
assignment: "담당은 청사진 §8.1을 확정한 것이다"
(`docs/contracts/RIGHTS_SCALE_PROFILE.md:135`).

| ID | Blueprint | Profile | Test id (proposed) | Owning node |
|---|---|---|---|---|
| RS-C01 | §4 `:299` | §8 `:139` | RS-C01-T1 | RS-1 |
| RS-C02 | §4 `:300` | §8 `:140` | RS-C02-T1 | RS-1 |
| RS-C03 | §4 `:301` | §8 `:141` | RS-C03-T1, RS-C03-T2 | RS-1 (a); RS-3a, RS-3b (b) |
| RS-C04 | §4 `:302` | §8 `:142` | RS-C04-T1 | RS-1 |
| RS-C05 | §4 `:303` | §8 `:143` | RS-C05-T1 | RS-1 |
| RS-C06 | §4 `:304` | §8 `:144` | RS-C06-T1, RS-C06-T2 | RS-1 (a); RS-3a (b) |
| RS-C07 | §4 `:305` | §8 `:145` | RS-C07-T1, RS-C07-T2 | RS-1 (a); RS-3a, RS-3b (b) |
| RS-C08 | §4 `:306` | §8 `:146` | RS-C08-T1 | RS-1 |
| RS-C09 | §4 `:307` | §8 `:147` | RS-C09-T1 | RS-2 |
| RS-C10 | §4 `:308` | §8 `:148` | RS-C10-T1 | RS-2 |
| RS-C11 | §4 `:309` | §8 `:149` | RS-C11-T1 | RS-2 |
| RS-C12 | §4 `:310` | §8 `:150` | RS-C12-T1 | RS-2 |
| RS-C13 | §4 `:311` | §8 `:151` | RS-C13-T1 | RS-2 |
| RS-C14 | §4 `:312` | §8 `:152` | RS-C14-T1, RS-C14-T2, RS-C14-T3 | RS-1, RS-2, RS-3a, RS-3b (per path) |
| RS-C15 | §4 `:313` | §8 `:153` | RS-C15-T1 | RS-1 |
| RS-C16 | §4 `:314` | §8 `:154` | RS-C16-T1 | RS-1 |
| RS-C17 | §4 `:315` | §8 `:155` | RS-C17-T1 | RS-2 |
| IM-01 | §2.1 `:81` | §12 `:198` | — | RS-1 (`:472`) |
| IM-02 | §2.1 `:82` | §12 `:199` | — | RS-1 (`:472`) |
| IM-03 | §2.1 `:83` | §12 `:200` | — | RS-1 (`:472`) |
| IM-04 | §2.1 `:84` | §12 `:201` | — | RS-1 (`:472`) |
| IM-05 | §2.1 `:85` | §12 `:202` | — | RS-1 (`:472`) |
| IM-06 | §2.1 `:86` | §12 `:203` | — | RS-1 (`:472`) |
| IM-07 | §2.1 `:87` | §12 `:204` | — | RS-1 (`:472`) |
| IM-08 | §2.1 `:88` | §12 `:205` | — | RS-1 (`:472`) |
| IM-09 | §2.1 `:89` | §12 `:206` | — | RS-2 (`:484`) |
| IM-10 | §2.1 `:90` | §12 `:207` | — | RS-2 (`:484`) |
| IM-11 | §2.1 `:91` | §12 `:208` | — | RS-2 (`:484`) |
| IM-12 | §2.1 `:92` | §12 `:209` | — | RS-2 (`:484`) |
| IM-13 | §2.1 `:93` | §12 `:210` | — | RS-2 (`:484`) |
| IM-14 | §2.2 `:101` | §12 `:211` | — | RS-2 (`:484`) |
| IM-15 | §2.2 `:102` | §12 `:212` | — | RS-2 (`:484`) |
| IM-16 | §2.2 `:103` | §12 `:213` | — | RS-2 (`:484`) |
| IM-17 | §2.2 `:104` | §12 `:214` | — | RS-2 (`:484`) |
| IM-18 | §2.2 `:105` | §12 `:215` | — | RS-2 (`:484`) |
| IM-19 | §2.3 `:115` | §12 `:216` | — | RS-2 (`:484`) |
| IM-20 | §2.3 `:116` | §12 `:217` | — | RS-1 (`:472`) |
| IM-21 | §2.3 `:117` | §12 `:218` | — | RS-1 (`:472`) |
| IM-22 | §2.3 `:118` | §12 `:219` | — | RS-2 (`:484`) |
| IM-23 | §2.4 `:124` | §12 `:220` | — | RS-1 (`:472`) |
| IM-24 | §2.4 `:125` | §12 `:221` | — | RS-1 (`:472`) |
| IM-25 | §2.4 `:126` | §12 `:222` | — | none (do-not-touch; no node) |
| IM-26 | §2.5 `:132` | §12 `:223` | — | RS-3b, via Track K v5 (`:497`) |
| IM-27 | §2.2 `:106` | §12 `:224` | — | RS-2 (`:484`) |
| IM-28 | §2.1 `:94` | §12 `:225` | — | RS-1 (`:472`) |
| IM-29 | §2.1 `:95` | §12 `:226` | — | RS-1 (`:472`) |
| IM-30 | §2.2 `:107` | §12 `:227` | — | RS-1, RS-2 (`:107`, `:227`) |

Notes on the table (no silent corrections):

- Blueprint §8.1 conditions RS-C02's RS-1 assignment on RS-0 choosing to
  include on-chain GA ("온체인 GA를 RS-0가 포함하기로 한 경우",
  `docs/blueprints/rights-scale-v1/README.md:449`). The draft includes the GA
  slot-range shard (`docs/contracts/RIGHTS_SCALE_PROFILE.md:44`) and the
  decision record proposes inclusion (`:70`), so the assignment reads as
  active — pending review, not settled by this pack.
- Blueprint §8.1 splits delegated shares: "Move 술어는 RS-3a, 실행자 통합과
  안정 명령 정체성은 RS-3b" (`docs/blueprints/rights-scale-v1/README.md:451`).
  The profile's 담당 column names the same nodes (`:141`,`:144`,`:145`,`:152`).
- IM-30 names both RS-1 and RS-2: "새 프로파일 시험의 CI 연결은 RS-1·RS-2의
  범위다" (`docs/blueprints/rights-scale-v1/README.md:107`); "새 프로파일
  시험을 CI에 연결하는 일은 RS-1·RS-2의 범위다"
  (`docs/contracts/RIGHTS_SCALE_PROFILE.md:227`).

## 2. Open items carried by the profile — no value chosen here

Every UNDETERMINED, DECISION_REQUIRED and OPEN item the profile itself
records, with its named owner and the RS node it gates. This table chooses
nothing; the "blocks" column says which node cannot finalize the item, not
that the node cannot start. Numbers quoted elsewhere in this pack (e.g. the
512-issue event ceiling, `max_input_objects` 2048, blueprint size examples
1·64·256·1,024·4,096) are quoted proposals or fixed-snapshot values, not
chosen contract values.

| Item | Status (as written) | Named owner | Node it gates |
|---|---|---|---|
| `IssuerCap` 처리 | OPEN. `rs-1-issuercap-probe` 전까지 선택 없음 | 프로브 뒤 Astra | RS-1 (three options listed `:233-235`; split-cap RS-C01 test opens only after the choice `:237`) |
| 페이지 크기 P | UNDETERMINED. 기본값 없는 시험 행렬 | Astra. 측정은 RS-4 L1 | RS-1 (test matrix), RS-4 (measurement), RS-3b (delegation granularity, §10 `:181`) |
| 샤드 개수 S와 라우팅 해시 알고리즘 | UNDETERMINED. 유일성 술어만 고정 | RS-1이 시험 행렬. 운영 값은 Astra | RS-1 |
| 노트 루트 이력 K | UNDETERMINED. manifest 필드 | DECISION_REQUIRED · Astra | RS-2 (RR-1 `:167`) |
| 0이 아닌 폐기 창 | 제품 정책. W=0만 초안 채택 | DECISION_REQUIRED · Astra | RS-2 (RR-3 `:169`) |
| 공개 트리 보존 기간 | UNDETERMINED | DECISION_REQUIRED · Astra (정책 값인 경우) | RS-2 (RR-4 `:170`) |
| `MAX_BUNDLE_CHAIN` 숫자 상수 | 공식만 채택. 이벤트 산술 천장 512는 상수가 아니다 | RS-1 / Astra | RS-1 |
| 봉인 뒤 페이지 추가 | OPEN. 0.1 범위표는 불변 | Astra | RS-0 review (rule adopted as draft; the requirement question is open `:84,:131`) |
| 구획·행·열과 슬롯 번호의 대응 | OPEN | RS-3b / Astra | RS-3b |
| 페이지와 커널 구간의 대응 | OPEN | RS-3b / Astra | RS-3b |
| 온체인 GA의 빈 슬롯 선택과 커널 카운터 대응 | OPEN. GA 범위 객체 자체는 §3에 포함 | RS-3b / Astra | RS-3b |
| `Claimed` 동적 필드가 더하는 새 ID 계수 | 미확인 | RS-1이 측정 | RS-1 |
| `shield` 경합의 완화 연산 | OPEN. 새 명령 없음 | 측정은 RS-4. 새 명령은 DECISION_REQUIRED · Astra | RS-4 (measurement); any new command — Astra |
| 폐기 저장 (b)의 충돌이 클 때의 대체 | OPEN. 임계 숫자 없음 | RS-4 보고 뒤 Astra | RS-4 → Astra |

The §9 RR rules carry the same opens (already folded into the rows above):
RR-1's K (`:167`), RR-3's nonzero window (`:169`), RR-4's retention period
(`:170`), RR-5's `shield` contention and possible new command (`:171`),
RR-6's invalidation rate (`:172`), and RR-2's collision rate, which RS-4
reports as raw samples with no threshold (`:168`).

## 3. Findings while tracing — AGENTS.md §8 classification, no silent fixes

Quotes are verbatim; line numbers are at the recorded base. Class A =
contract-defined and matching; B = contract-undefined (recorded
characterization, remaining uncertainty); C = explicit contract violation.
**No class C item was found** while tracing or by the checker; no fix was
applied to any document.

### 3.1 Class A — defined and matching

- **A-1: Id coverage is complete and singular.** Every RS-C01..RS-C17 row of
  blueprint §4 (`:299-315`) appears exactly once in profile §8 (`:139-155`);
  every IM-01..IM-30 row of blueprint §2 (`:81-95`,`:101-107`,`:115-118`,
  `:124-126`,`:132`) appears exactly once in profile §12 (`:198-227`). The
  decision record's self-check — "프로파일의 표 행은 `RS-C01`부터 `RS-C17`,
  `RR-1`부터 `RR-6`, `IM-01`부터 `IM-30`이 각 한 번씩이다"
  (`docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md:139`) — is confirmed
  mechanically by `scripts/check_rs_profile_traceability.py` on this tree
  (exit 0, `blueprint=47 profile=47 expected=47`).
- **A-2: Node assignment agrees with blueprint §8.1.** The profile's 담당
  column (`:139-155`) matches the §8.1 split
  (`docs/blueprints/rights-scale-v1/README.md:449-451`): public share RS-1,
  private share RS-2, delegated shares RS-3a/RS-3b — including the (a)/(b)
  splits on RS-C03, RS-C06, RS-C07 and the four-node split on RS-C14.
- **A-3: Draft status is stated identically in both documents.** Profile
  `:3,:7` and decision `:3,:31,:59` all condition confirmation on Astra
  review plus User merge; neither text claims acceptance.
- **A-4: The six ceilings keep blueprint semantics without chosen values.**
  Profile §4 (`:82-91`) mirrors blueprint §1.2 (`:57-64`) one-to-one,
  including the separation from kernel `MAX_BUNDLE = 64` / `MAX_SEATS = 4,096`
  (`docs/contracts/RIGHTS_SCALE_PROFILE.md:91`;
  `docs/blueprints/rights-scale-v1/README.md:64`).

### 3.2 Class B — undefined or divergent; recorded, not resolved

- **B-1: `IssuerCap` probe sits inside RS-1 in the blueprint but is a separate
  later node in the roadmap and profile.** Blueprint RS-1 acceptance:
  "**초기 확인 시험:** 같은 `IssuerCap`을 참조(`&`)로 쓰는 발행자 서명
  트랜잭션 2건을 localnet에서 동시에 보내 소유 객체 잠금 여부를 확정한다."
  (`docs/blueprints/rights-scale-v1/README.md:473`). The profile states:
  "청사진 RS-1 인수 조건은 이 프로브를 RS-1 안에 적는다. 로드맵과 노드 정의는
  `rs-1-issuercap-probe`로 분리한다. 0.1은 로드맵의 분리 노드를 따른다.
  불일치는 결정 기록의 범주 B다." (`docs/contracts/RIGHTS_SCALE_PROFILE.md:239`;
  `.aiops/program.json` `rs-1-issuercap-probe` depends on `rs-1`). Already
  recorded as B in the decision record (`:91`,`:121`). Consequence worth
  review attention: under the roadmap order the public path is built before
  the probe answers whether a referenced owned object serializes issuer
  transactions.
- **B-2: RS-C02's GA redistribution has no operation in the §3 table.**
  "재분배는 두 페이지를 한 PTB에서 옮기고 총량을 유지한다"
  (`docs/contracts/RIGHTS_SCALE_PROFILE.md:140`), but no redistribution row
  exists in the operations table (`:61-74`). The `rs-1` stop records the same
  gap: "That is a new protocol command: `DECISION_REQUIRED · Astra`."
  (`/workspace/kix-run/state/rs-1.decision.md:45`). Recorded, not resolved.
- **B-3: RS-C17 was blueprint-undefined; 0.1 defines a draft rule.**
  Blueprint: "이 규칙은 **계약 미정 특성**이며 RS-0가 정한다"
  (`docs/blueprints/rights-scale-v1/README.md:315`). Profile: "RS-C17은
  청사진이 계약 미정으로 남긴 항목이다. 0.1이 위 문장으로 초안 규칙을
  정의한다. 확정은 Astra 아키텍처 검토와 사용자 병합이다."
  (`docs/contracts/RIGHTS_SCALE_PROFILE.md:159`; draft rule `:155`). The
  `ChallengeShard` name is itself marked draft: "초안 이름이며 RS-2가 모듈
  이름을 맞출 수 있다" (`:47`).
- **B-4: Package path and module name — blueprint assigns the choice to
  RS-0; the profile leaves it to RS-1/RS-2.** Blueprint: "**확장 프로파일**:
  새 패키지, 새 회로, 새 manifest, 새 도메인 분리 값. 경로와 이름은 RS-0에서
  정한다." (`docs/blueprints/rights-scale-v1/README.md:69`); RS-1 row:
  "새 Move 패키지·모듈(경로는 RS-0에서 확정)" (`:472`). Profile: "경로와
  모듈 이름의 최종 값은 **RS-1·RS-2가 고른다**. 이 계약은 그 경로가
  `reference/v0.3-rc1/**` 밖일 것만 요구한다"
  (`docs/contracts/RIGHTS_SCALE_PROFILE.md:26`). Newly noted while tracing;
  not previously classified in the decision record. Whether a confirmed
  contract may leave the path open is a question for the review (§5).
- **B-5: Post-seal page addition.** Blueprint open question 1
  (`docs/blueprints/rights-scale-v1/README.md:549`) asks whether a
  requirement exists. Profile: "봉인 뒤 페이지 추가는 0.1에 없다. 범위표
  불변이 이 버전의 전제다. 그 요구가 있는지는 OPEN이며 주체는 Astra다."
  (`docs/contracts/RIGHTS_SCALE_PROFILE.md:131`; same in §4 `:84`). Already
  classed B in the decision record (`:123`).
- **B-6: Equivalence lemma is a plan, not a proof.** "참조 프로파일에서
  노트는 `shield` 뒤에만 생긴다. … 그 전제 아래에서 "폐기된 최대 세대"와
  "현재 세대"는 같은 합격·불합격을 낸다. RS-2가 이 문장을 보조정리로 적고,
  RR-2-T1로 … 본다." (`docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md:53`;
  "이 노드에서 증명하지 않음" `:69`,`:131`). The premise breaks if private
  refund/reissue is ever added (`:53`).

## 4. The three unlock routes recorded in the `rs-1` stop — none chosen here

Source: `/workspace/kix-run/state/rs-1.decision.md:35-37`. For each route,
the exact sentence the User would have to write is given as a template
(`<SHA>` = the commit that carries the reviewed text); the User may reword.
The owner already selected route 1 on 2026-10-09, but that selection did not
name a commit and did not accept the draft — its confirmation step is still
open (`/workspace/kix-run/state/rs-1.decision.md:31`). Merging a document
that declares itself unconfirmed does not confirm it (`:29`).

| Route | Exact User sentence (template) | What stays locked afterward |
|---|---|---|
| 1. Confirm RS-0, then rerun RS-1 | "I accept `docs/contracts/RIGHTS_SCALE_PROFILE.md` 0.1 and `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md` at commit `<SHA>` as the confirmed contract following Astra's architecture review." | All §2 opens keep their owners: P, S, routing hash, K, W>0, retention period, `MAX_BUNDLE_CHAIN` constant, `profile_version` value stay UNDETERMINED/DECISION_REQUIRED · Astra; `IssuerCap` stays open until `rs-1-issuercap-probe`; GA redistribution stays a missing new command (DECISION_REQUIRED · Astra); CI wiring is a User decision; PROGRAM_DECISIONS §5 locks unchanged (no real funds, real PG/bank/KYC, public endpoints, testnet/mainnet, R2, coin/TIX, kernel lock). |
| 2. Authorize implementation against the named draft | "RS-1 may implement the public path from the draft as it sits on commit `<SHA>`; Astra review of the profile happens at the RS-1 ARCHITECTURE gate rather than as a predecessor." | Same locks as route 1, plus: the draft's own status sentences (`docs/contracts/RIGHTS_SCALE_PROFILE.md:3,:7`) are unchanged — the authorization is a start gate, not an acceptance of the text; every UNDETERMINED/DECISION_REQUIRED value still blocks its owner. |
| 3. Replace the draft first | "Supersede profile 0.1 with `<successor document>`; RS-1 waits for that document's acceptance." | Same locks as route 1; profile 0.1 stays an unreviewed draft unless the successor or an explicit acceptance changes it; the successor inherits the same §2 opens until it resolves them. |

## 5. Reviewer checklist — questions for Astra

1. Is adopting RR-2 ("폐기된 최대 세대" sparse revocation tree) with storage
   (b) sound, given that concurrent `revoke`s built on the same root conflict
   and exactly one succeeds
   (`docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md:49-51`)? Is the
   unproved equivalence lemma (B-6) acceptable as a draft premise?
2. Is W=0 (RR-3) the right default, and is a nonzero revocation window
   correctly gated as `DECISION_REQUIRED · Astra`
   (`docs/contracts/RIGHTS_SCALE_PROFILE.md:169`)?
3. K stays UNDETERMINED as a manifest field with owner
   `DECISION_REQUIRED · Astra` (`:167`,`:246`). Does the review want a bound
   now, given the privacy note that smaller K is better
   (`docs/blueprints/rights-scale-v1/README.md:343`)?
4. Probe placement (B-1): is building the public path before the
   `IssuerCap` serialization answer acceptable, or should the probe run
   inside/parallel to RS-1 as the blueprint's acceptance row says?
5. GA redistribution (B-2): does RS-1 need a new protocol command (two-page
   atomic move) to satisfy RS-C02, and should the profile name it before
   acceptance or mark it `DECISION_REQUIRED`?
6. Path/name deferral (B-4): can a confirmed contract leave the package
   path and module name to RS-1/RS-2 when the blueprint assigned the choice
   to RS-0?
7. Conditions (a)–(e): does the draft satisfy Astra's own five conditions as
   recorded (`docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md:19-25`),
   especially (d) the RS-3b/Track K v5 boundary and (e) no lifecycle
   transitions?
8. Post-seal capacity (B-5): is an immutable range table at seal the right
   0.1 rule, or is there a page-add requirement the profile should name?
9. Test-id sufficiency: does each proposed test id cover its predicate?
   Specifically — RS-C14-T1/T2/T3's per-path split
   (`docs/contracts/RIGHTS_SCALE_PROFILE.md:152`), and the 15/16/17 boundary
   test (`docs/blueprints/rights-scale-v1/README.md:393`), which has no
   dedicated predicate row.
10. `profile_version`: the profile requires the on-chain constant to differ
    from the reference profile (`docs/contracts/RIGHTS_SCALE_PROFILE.md:28`)
    but leaves its value open — who fixes it, and in which node?

## Non-claims

- Builder-authored evidence only; not a review, not an acceptance, not a
  change of status, and not the non-author exact-HEAD review that AGENTS.md
  requires separately.
- No profile, decision-record, blueprint or contract byte was edited; no
  policy value, ceiling, ceremony power, path or command was chosen; every
  UNDETERMINED/DECISION_REQUIRED/OPEN item keeps its named owner.
- `scripts/check_rs_profile_traceability.py` is a mechanical convenience
  check on first-cell table keys. It does not judge semantics, is not wired
  into CI, and its pass is not a contract gate.
- Amendment 2026-10-26: `scripts/check_rs_profile_traceability.py` is now wired, plain and `--self-test`, into the `Stdlib offline document checks` step of `.github/workflows/protocol.yml` by #170; the "not wired into CI" wording above records the state when this pack was written.
- Local command results are recorded in
  `validation/2026-10-12-rs0-review-pack/README.md`. They are not exact-head
  CI and are not independent verification.
