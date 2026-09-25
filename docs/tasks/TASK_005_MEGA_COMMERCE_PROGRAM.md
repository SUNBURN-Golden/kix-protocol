# Task 005 — Mega commerce program (Wave1 charter)

Issued by the KIX Maintainer on 2026-09-25 (KST) under **Astra / 개발총괄**
`DECISION_REQUIRED · Astra` ruling (JunTae re-confirm not required). This
document is the **Wave1 charter only**: scope, non-scope, hard locks, and wave
sequencing for the product surfaces JunTae named (여신, Sui Move / TIX-parity
issuance, rights tokenization, settlement distribution, credit advance,
resale / box-office / booking / admission frontends, marketing).

**Wave1 authorizes documentation and tracking issues only.** It does **not**
authorize an implementation writer, code branches for product features, or
implementation PRs.

## Status

- Task ID: `005`
- Phase: **Wave1 — charter / issues (no impl writer)**
- Task document: immutable once any later implementation wave starts against it
- Repository-wide rules: follow root `AGENTS.md`
- Product `runtime_enabled` remains false; do not re-enable Control Plane
  Runtime workflow previously marked `disabled_manually`
- Parallel with Task 004: **docs/issues only**. Task 004 implementation writer
  remains the sole code writer until Task 004 draft PR + **GROK_BUILD
  exact-HEAD** (non-author) complete.

## Objective

Produce a durable program charter that:

1. Aligns JunTae’s mega ask with `docs/status/ORIGINAL_32_STATUS.md` and
   `docs/PROTOCOL_MASTERPLAN_V2.md` / `docs/DEVELOPMENT_PLAN.md`.
2. Records Astra-approved **wave order**, **repo placement**, **Move strategy**,
   and **F04 credit policy**.
3. Gives later waves a single non-negotiable scope / non-scope / lock list so
   builders do not invent SLOs, real credit products, new coin modules, or
   monorepo frontends.

Wave1 success = this document + GitHub tracking issue(s) merged or at least
draft-PR’d for review. **No product code.**

## Base

- Charter base SHA: `729a106add049ad1a75b90f99c00b6e0ccb8a67d` (`origin/main` at
  Wave1 draft, 2026-09-25).
- Docs branch: `docs/task-005-mega-commerce-program-20260925`
- Do not silently rebase. Report `origin/main` drift at any later wave start.

## Mandatory reading

- Root `AGENTS.md`
- `docs/DEVELOPMENT_PLAN.md`
- `docs/PROTOCOL_MASTERPLAN_V2.md`
- `docs/status/ORIGINAL_32_STATUS.md`
- `docs/contracts/` (commerce / settlement / performance as applicable)
- `reference/v0.3-rc1/sui/sources/rights.move`
- `reference/v0.3-rc1/sui/sources/zk_gate.move`
- Task 004 charter (immutable): `docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md`
  (on docs PR #54 / issue #55 until merged) — **do not edit**

## Astra rulings (binding)

Recorded 2026-09-25 from 개발총괄 (Astra role). JunTae re-ask forbidden for
these items unless Astra reverses them.

| # | Decision |
|---|----------|
| 1 | Mega ask is **one program, many waves**. Do **not** start all waves at once. |
| 2 | Until Task 004 finishes (draft PR + GROK_BUILD exact-HEAD), **no second implementation writer**. |
| 3 | Wave1 may proceed **in parallel** as Maintainer **docs/issues only** (no impl code/branch/PR). |
| 4 | Product frontends / marketing apps = **separate app repo(s)** under BeautifulMind-JT. Do **not** plant product frontend trees inside `kix-protocol`. Protocol contracts / OpenAPI stay in `kix-protocol`; apps consume them. |
| 5 | TIX-parity issuance = **extend existing Move `rights` (+ `zk_gate`)** (option A). **New coin/TIX module (B) forbidden** until ADR + Astra re-ruling. |
| 6 | 여신 / 신용 선지급 = **F04**, **mock/sim only** for now. Real credit, regulated products, real funds paths forbidden until separate Astra ruling + explicit OK. |

## Wave plan (approved order)

| Wave | Name | Allowed work | Writer |
|------|------|--------------|--------|
| **0** | Task 004 perf apparatus | Measurement harness / evidence; draft PR; GROK_BUILD exact-HEAD | Cursor CLI `grok-4.7-xhigh` (current); no preemption |
| **1** | This charter | Task doc + tracking issues; ORIGINAL_32 / masterplan alignment | Maintainer (docs only) |
| **2** | Rights + TIX-parity on Move | Extend `rights` (+ `zk_gate`); issuance mechanism parity with TIX **without** new coin module | One impl writer after Wave0+1 gate |
| **3** | Settlement distribution | F01–F03 first; contract + mock settlement path | One impl writer |
| **4** | Booking / resale / admission **protocol** | B/R + admission **API/gates** (not frontends) | One impl writer |
| **5** | Credit advance (F04) | **Mock/sim only**; no real funds / license claims | One impl writer |
| **6** | Frontends | Box-office / booking / admission / resale UIs in **separate app repo**; entry when Wave2–4 contracts/APIs are draft-usable | App-repo writer (separate) |
| **7** | Marketing | M01–M05 after frontend ↔ contract alignment | App-repo / protocol docs as scoped |

Waves after 0 start **only** when Astra/ Maintainer gate for that wave is open.
Default gate into Wave2: Task 004 draft PR exists + GROK_BUILD exact-HEAD
non-author review recorded (merge may still wait human approval).

## ORIGINAL_32 alignment (program map)

Labels remain those in `docs/status/ORIGINAL_32_STATUS.md` (mostly 설계중).
This charter does **not** promote labels.

| Surface (JunTae) | Primary ORIGINAL_32 rows | Wave |
|------------------|--------------------------|------|
| 권리토큰화 / Move / TIX-parity 발행 | P01, P02, E02; Move anchor M | 2 |
| 정산분배 | P04, F01, F02 (, F03 as needed) | 3 |
| 예매·매표 프로토콜 | B01–B05 | 4 |
| 리셀 프로토콜 | R01–R05 | 4 |
| 검표 프로토콜 | P03 | 4 |
| 여신·신용 선지급 | F04 (+ E06 compliance boundary) | 5 (mock only) |
| 매표/예매/검표/리셀 프론트 | E04 clients consuming protocol APIs | 6 (separate repo) |
| 마케팅 | M01–M05 | 7 (separate repo + contracts) |

## Authorized scope (Wave1 only)

- Add/update **this** task charter under `docs/tasks/`.
- Optional short pointer from `docs/tasks/README.md` if present.
- Open GitHub tracking issue(s) linking waves and locks.
- Draft docs PR for this charter (no product code).

## Out of scope / hard locks (all waves until Astra lifts)

Root `AGENTS.md` prohibitions remain. Additionally:

- Kernel frozen blobs / v4 kernel production semantics edits
- Stage2 reclaim / GC / index
- R2
- schema / SDK productization
- Blueprint / issue **#35** implementation
- `runtime_enabled` unauthorized flip; re-enable of manually disabled Control Plane Runtime workflow
- Cloud Devin
- Self-merge / main direct or force push
- Extra paid purchase / quota bump / silent provider fallback
- JunTae mid-flight ping for routine decisions (use `DECISION_REQUIRED · Astra`)
- **New** Move coin / TIX module (until ADR + Astra)
- **Real** credit / regulated lending / real-funds paths (until Astra + explicit OK)
- Product frontend trees inside `kix-protocol`
- Inventing product TPS / p99 / fail-rate SLOs
- Second implementation writer while Task 004 writer is active

## Work plan (Wave1)

### A. Inventory

- Confirm ORIGINAL_32 / masterplan / Move `rights`+`zk_gate` / absence of product
  frontend apps in-repo (already done at charter time).
- Confirm Task 004 still sole impl writer.

### B. Charter + issues

- Land this document via docs draft PR.
- Open tracking issue for Task 005 / mega program with wave checklist.
- Do **not** open implementation branches for Waves 2–7 yet.

### C. Contract discrepancy

- Undefined contract → characterize; do not invent semantics.
- Explicit violation → block and escalate `DECISION_REQUIRED · Astra`.

## Acceptance criteria (Wave1)

- [ ] This charter exists on a docs branch / draft PR
- [ ] Tracking GitHub issue opened with wave checklist and locks
- [ ] No implementation commits for Waves 2–7 under this task
- [ ] Task 004 writer undisturbed
- [ ] Astra rulings § above quoted without dilution
- [ ] PR unmerged until explicit human approval (docs may merge when approved)

## Evidence

- Link to Astra decision message (개발총괄 DM / KIX chat, 2026-09-25)
- Links: Task 004 issue #55, docs PR #54, impl branch
  `agent/task-004-perf-measurement-20260925`
- Charter base SHA `729a106add049ad1a75b90f99c00b6e0ccb8a67d`

## Open questions (escalate to Astra only if blocking)

None open for Wave1. Later waves must re-check:

- App repo name(s) under BeautifulMind-JT when Wave6 opens
- ADR trigger if someone proposes coin/TIX module (B) again
- Real-funds F04 lift criteria (explicit; not implied by mock work)

## Non-claims

- This charter is **not** proof that ORIGINAL_32 rows are implemented.
- Mock settlement / mock F04 are **not** production finance or licensed credit.
- Extending `rights` is **not** authorization for a separate fungible TIX coin.
