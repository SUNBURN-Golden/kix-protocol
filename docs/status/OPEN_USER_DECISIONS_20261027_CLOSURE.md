# Open User decisions — October 27 closure follow-up

## Basis and provenance

Builder-authored, dated 2026-10-27. Node:
`plan-plan-open-decisions-closure-20261027`; issue: none; `depends_on: []`;
audit floor A2; `astra_gate: None`; `user_merge: False`.
This is not ASTRA program mode. This loop-proposed node is absent from
`.aiops/program.json` and has no task document under `docs/tasks/`.
Task input is the supervisor-supplied node specification and read-only design plan.
Source: KIX planner run 1793059450 (`/workspace/kix-run/logs/planner_1793059450`,
as supplied; no planner execution is claimed).

Observed cached `origin/main`, base and starting branch HEAD:
`09470db220965390edeecdb75f56f8c827dd15b6` (#313), on
`agent/kix-plan-plan-open-decisions-closure-20261027`.
Fetch was NOT_RUN under the supervisor's no-network rule; remote freshness
remains unverified. No local base delta was observed. Status and line citations
refer to these basis bytes, not a future delivery head.

The scan covers all 24 first-parent merges #290–#313, after #289
`22df2e96d1a7de4d0de371a1f64776e80af9d999` (the boundary identified in the
[docs index](../README.md), basis line 334). #281–#289 lie outside this node's
range. Status is judged at the basis HEAD; a resolving merge from any range
would be recorded with its PR number.

The [October 22 ledger](OPEN_USER_DECISIONS_20261022.md),
[October 23 supplement](OPEN_USER_DECISIONS_20261023_ADDENDUM.md),
[October 23 closure](OPEN_USER_DECISIONS_20261023_CLOSURE.md),
[October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md),
[October 26 AI delegation addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md),
[October 26 BCS1 addendum](OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md) and
[October 26 SDK addendum](OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md)
remain preserved dated records. External decision files were not re-read or rerun.

**This document selects no option and changes no node state.**

## Closure table

Owner cells carry forward the exact recorded strings, including the ledger's
§2 index strings for L1/L2 and SD1's “Who decides” wording. The options below
retain their original record wording; the table supplies no owner answer.

| Item id | Stop | Holding record | Owner (verbatim, as recorded) | Status at 09470db | Resolved by (PR · SHA) | #290–#313 facts |
|---|---|---|---|---|---|---|
| L1 | `k-stage5-durable-tx` host | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User / supervisor (build host) | STILL OPEN | none | No durable implementation or acceptance record on main; #301 preserves the stage-5 self-test-only exception. #313 closes no stop. |
| L2 | `rs-4-l2` measurement environment | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User (spend / environment); Astra (workload) | STILL OPEN | none | #302 inventories impacts only; L2 measurement record remains absent and acceptable load UNDETERMINED (User). #313 closes no stop. |
| A2 | `plan-plan-gate-fsm-seeded-journey-differentia` loopback host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) | Supervisor / repository owner controlling the execution host | STILL OPEN | none | #305 retains the owned gap; #307/#312 add offline checks without the seeded journey or a bound-listener observation. #313 closes no stop. |
| A4 | `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) | User / repository owner | STILL OPEN | none | #290 synchronizes pointers for a different node; no disposition of this duplicate appears in the scan. #313 is an index only. |
| A5 | AI delegation §7 check order | [AI delegation addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure) | Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge. | STILL OPEN | none | #293 maps evidence; #298 records the class C stop. Actor registration, tool lists, then grant-agent binding remain in that order; #313 changes no status. |
| BCS1 | BCS1 checker scope | [BCS1 addendum](OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md#new-stop--plan-plan-bcs1-contract-bound-regressions) | the User/orchestrator owning this loop-proposed node. | STILL OPEN | none | #299 adds the map/checker; #304 records its scope conflict. TEST_FILES still accepts only the original two paths. #301 wiring coverage does not authorize option C; #313 changes no status. |
| SD1 | SDK manifest §4 check order | [SDK addendum](OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md#new-stop--plan-plan-sdk-compat-manifest-clause-evidence) | Who decides: the User. | STILL OPEN | none | #306 records the class C stop; OpenAPI/generator/output byte comparisons still precede profile hashing. #313 explicitly retains the missing-map stop. |

A4 is listed STILL OPEN by the October 25 closure; it is not named in this
node's six-item list. Including it by reference is an explicit design-plan
deviation preserving the ledger; no disposition is inferred. The four open
October 25 items plus A5, BCS1 and SD1 yield seven rows.

## Options — verbatim from the holding records

Quoted recommendations belong to their source records. They are not decisions
by this follow-up. Source line numbers identify the basis above.

### L1

Source: [OPEN_USER_DECISIONS_20261022.md](OPEN_USER_DECISIONS_20261022.md), line 63, option and recommendation cells.

> 1. 「Provision the pinned backend, then rerun (recommended).」 — 「Install `postgresql-17` (17.11-0+deb13u1) and `python3-psycopg` on the build host, or run the node on the host that produced `validation/2026-10-08-k-stage4-local-exploration/`, then run `python3 -m unittest durable.test_durable` and `python3 scripts/stage5_local_check.py validation/2026-10-13-k-stage5-durable-tx`. Expect to fix small real-PostgreSQL issues: the SQL was only exercised against a throwaway sqlite stand-in (not evidence), and that is the main residual risk.」 2. 「Merge the code as an unverified candidate.」 — 「Not recommended: the acceptance criterion would be unmet, the suite is not wired into CI, so green CI would say nothing about the backend.」 3. 「Hold the node.」 — 「Keep it WAITING until option 1 is possible.」

> 별도의 권고 문단은 없다. 권고는 선택지 1의 표기 「(recommended)」가 담는다.

### L2

Source: [OPEN_USER_DECISIONS_20261022.md](OPEN_USER_DECISIONS_20261022.md), line 64, option and recommendation cells.

> 1. 「Run on a dedicated or quiet machine/VM (may involve cost): complete record, same scripts.」 2. 「Re-run on the builder machine in a quiet window with no other load: free, unreliable.」 3. 「Accept a reduced scope (e.g. public prefix only, or private and delegated first) as the L2 record: an Astra workload decision.」

> 「Option 1, or option 2 if the User can guarantee an idle builder host for several hours. The scripts need no change.」

### A2

Source: [OPEN_USER_DECISIONS_20261023_ADDENDUM.md](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia), lines 100–105.

- **Existing options:** (1) Supervisor runs the unchanged tests in its
  loopback-enabled local environment, reviews the outputs and returns any
  implementation failures for correction. (2) A new builder session permits
  local loopback tests under the same scope and production/external-network locks.
- **Source recommendation:** The supplied stop recommends option 1 and says
  not to weaken tests or change gate/CI code to evade the restriction.

### A4

Source: [OPEN_USER_DECISIONS_20261023_ADDENDUM.md](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023), lines 197–206.

- **Existing options:** Retire as superseded by #261, with explicit owner
  acceptance of the existing delivery; revise to independent verification with
  a distinct evidence record and externally revised changed-file/basis acceptance;
  or supply genuinely missing synchronization requirements with revised scope,
  attribution and acceptance. The source's suggested alternative path is
  `validation/2026-10-23-plan-plan-plan-register-index-sync-20261023/README.md`;
  its availability must be checked by a future authorized session before use.
- **Source recommendation:** The supplied record recommends retirement as
  superseded by #261 because it found no missing substantive edit. This
  supplement does not retire the node or accept that recommendation.

### A5

Source: [OPEN_USER_DECISIONS_20261026_ADDENDUM.md](OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure), lines 56–61.

- **Option 1:** Fix the mock in a separately authorized node. See source stop,
  “Options”, item 1, by reference only.
- **Option 2:** Amend the contract in a separately authorized node. See source stop,
  “Options”, item 2, by reference only.
- **Source recommendation:** The stop record recommends option 1; this addendum
  does not endorse it.

### BCS1

Source: [OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md](OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md#options-source-text), lines 210–221.

> 1. **A — recommended:** authorize only design plan §3.3's checker adaptation:
>    append the new test path; pin the six closed follow-up citations; retain the
>    two S08 NOT_COVERED locks; require FU tags only for remaining gaps; update the
>    follow-up heading; retarget the affected self-test fixtures to the unchanged
>    S08 row; add negative fixtures for lost closure citations and reverted status.
>    Then implement and verify the six tests and evidence-map updates as planned.
> 2. **B:** revise acceptance so the six rows remain NOT_COVERED and new evidence
>    appears only as prose. This does not meet current acceptance and was rejected
>    by the supplied design review.
> 3. **C:** authorize a separate checker node before this regression node.

Source recommendation: A. This addendum does not endorse it.

### SD1

Source: [OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md](OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md#new-stop--plan-plan-sdk-compat-manifest-clause-evidence), lines 85–95.
The external stop identified by this SHA-256 is not re-read here; the addendum
provides the options by reference only, verbatim:

- **Option 1:** See source stop (SHA-256
  `10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af`),
  “Options”, item 1, by reference only.
- **Option 2:** See source stop (SHA-256
  `10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af`),
  “Options”, item 2, by reference only.
- **Option 3:** See source stop (SHA-256
  `10777ef765eb0a1cd3e59d7dea6654ee6cf95c87666cb82bfd46e5b3344498af`),
  “Options”, item 3, by reference only.
- **Source recommendation:** option 1 (stop line 15); this addendum does not
  endorse it.

Quoted for reference; no option is endorsed or chosen.

## Repository facts in #290–#313

Each row is attributed documentary evidence, confirmed against the merge's
changed paths and the cited file/line at the basis. All 24 merges were inspected;
only those relevant to the seven stops are listed. Other map/test closures
in the range do not supply the missing artifacts or a duplicate disposition.
Absent paths below are explicitly missing artifacts, not links to main files.

| PR | Merge SHA | Record | Fact relevant to item(s) |
|---|---|---|---|
| #290 | `92d08e755dfe362ed224112c8dada6c5fcea17d4` | [Pointer sync](../../validation/2026-10-25-plan-register-index-crosswalk-sync/README.md) | A4: record identifies `plan-plan-register-index-crosswalk-sync-20261` (line 3); it records no duplicate-node disposition. The repository-wide name search finds only the older holding records and their copied evidence. |
| #293 | `a38e1679449e74186c5a4e3d19b6cb79f6b791d5` | [AI delegation map](AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md) | A5: line 51 keeps §7 PARTIAL: simultaneous violations are characterized as set membership, not ordered precedence. The new checker checks citations, not a remedy for the later stop. |
| #298 | `18aefc8f7c0dd13b7249e0d80304f3b97459fa3a` | [AI delegation addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md) | A5: lines 36–64 retain the mock order, class C report and owner; missing-grant binding remains UNDETERMINED with that same owner. No mock or contract change occurs in the range. |
| #299 | `1f01a9321c641c7a7fafa2a33e4350a2fa711730` | [BCS1 map](BCS1_CONTRACT_EVIDENCE_MAP.md) | BCS1: map lines 69–79 retain the eight NOT_COVERED follow-ups. [Checker](../../scripts/check_bcs1_evidence_map.py) line 14 still permits only the original source/golden-vector test paths; lines 78–88 pin all eight NOT_COVERED locks. |
| #301 | `fc11cdf0150e54ed38bb363f2ded7238c48c6e53` | [CI wiring guard](../../validation/2026-10-26-plan-ci-checker-wiring-guard/README.md) | L1/BCS1: [guard](../../scripts/check_ci_checker_wiring.py) lines 4–10 checks invocation coverage, not semantic adequacy. Lines 26–30 retain SELF_TEST_ONLY for stage 5 because CI is not the pinned host. This does not deliver the BCS1 option C checker adaptation or authorize it. |
| #302 | `412e1ed7bc740599227567f60bf315bb7ecab818` | [RS-4 L2 impact inventory](RS4_L2_DECISION_IMPACT_INVENTORY.md) | L2: lines 51–61 retain acceptable load UNDETERMINED (owner: User) and missing L2 workload inputs UNDETERMINED — Astra (workload). It inventories conditional impacts without measurements or acceptance; the L2 validation directory remains absent. |
| #304 | `22d05a0c82693ad4575a72c2d342b4e47114447f` | [BCS1 addendum](OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md) | BCS1: lines 42–55 hold the scope/acceptance conflict; lines 210–226 preserve A/B/C and the owner. Checker and map bytes have not changed since #299. |
| #305 | `23391ab50e0467bc7b234c55e98614713d531f58` | [Integration-gate map](INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md) | A2: lines 30 and 87 keep the seeded journey as an owned open gap, explicitly not implemented. No SeededJourneyDifferentialTests exists under integration_gate at this basis. |
| #306 | `a176c1f22c0af21500cb52a777bc889b808e561c` | [SDK addendum](OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md) | SD1: lines 55–73 retain comparisons before profile hashing and extension_profile interpretation UNDETERMINED — User. [Verifier](../../sdk/compat/verify_compat.mjs) comparisons at 168/190/201 still precede 235. The proposed manifest map/checker remain absent; no SDK or SDK-contract change occurs in the range. |
| #307 | `a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4` | [Offline checker closure](../../validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md) | A2: lines 197–217 limit the changes to four map rows and offline checks, with no gate/server behavior or HTTP test change; the seeded-journey host stop remains unchanged. |
| #312 | `d2b748aef0c7b4af5bef23c771c6bce22b52905f` | [Offline limits closure](../../validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md) | A2: lines 61–70 show default host/port only through argument parsing, no bound listener. [Map](INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md) line 87 still explicitly leaves the seeded-journey stop open. |
| #313 | `09470db220965390edeecdb75f56f8c827dd15b6` | [Evidence-map roll-up](EVIDENCE_MAP_ROLLUP.md) | All seven: lines 1–23 identify an index only and explicitly change no map status, owner or grade and close no decision or UNDETERMINED value. Line 51 retains the SDK map stop. Indexing evidence does not supply host execution or a disposition. |

L1 missing artifacts at the basis: `durable/`, `scripts/stage5_local_check.py`
and `validation/2026-10-13-k-stage5-durable-tx/`.
L2 missing artifact: `validation/2026-10-15-rs-4-l2-load/`.
SD1 missing artifacts: `docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md` and
`scripts/check_sdk_compat_manifest_evidence_map.py`.
These are absent-path observations, not repository citations asserting existence.
The L1 option quotation likewise names future acceptance commands/artifacts,
and A4's quoted alternative validation path is future work, not a main artifact.

## Verification method

Following the [October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md#verification-method),
RESOLVED-BY-MERGE means the blocking condition named by the stop is gone at
the main status basis: the artifact its option or acceptance names exists,
or the discrepancy it cites no longer exists. It is attributed documentary
evidence only, not owner approval, acceptance, review or a node state change.
A resolved cell would name the PR, full merge SHA and artifact paths.
`none` means the condition remains present and the row is STILL OPEN.
Partial or contradictory resolution evidence would require an owner decision;
no ambiguous resolution was found in this scan.

Local first-parent history identifies PRs and merge SHAs; source contents,
missing-artifact checks and historical-record attribution support each row.
The [validation record](../../validation/2026-10-27-plan-open-decisions-closure-20261027/README.md)
records commands, raw outputs, exit codes, owner/option/anchor checks,
coverage mapping and local documentation checks. These establish documentary
consistency, not runtime acceptance or independent owner approval.

## Non-claims

- No option, node disposition, program status, evidence grade, policy value,
  owner, acceptance criterion or protocol command is selected or changed.
  No node is resumed, completed, retired or retried by this document.
- L1/L2/A2 still need their recorded host/environment decisions; A4 still
  needs its duplicate-sync disposition. A5 and SD1 remain the attributed
  class C stops held by their named owners; their reproductions are not rerun.
  BCS1 remains a scope/acceptance stop, not a newly found codec violation.
  No checker, map, contract, test, source, task input, program file or CI is changed.
- The RS-4 acceptable load stays UNDETERMINED (User); missing L2 workload
  inputs stay UNDETERMINED — Astra (workload). A5 missing-grant binding stays
  UNDETERMINED with its quoted decision owner. SD1 extension_profile
  interpretation stays UNDETERMINED — User. All other open contract/readiness
  values retain their named owners; this document supplies no semantics.
- Canonical counting remains `DECISION_REQUIRED · Astra`.
- Earlier ledgers/addenda/closures and evidence remain preserved. Both locked
  kernel blobs and `reference/v0.3-rc1/**` stay byte-identical.
- No historical or hosted CI result transfers to this change. This is builder
  evidence, not non-author exact-HEAD review, an Astra audit or a merge-ready claim.
- No funds, PG/bank/KYC call, public endpoint, Sui testnet/mainnet, R2, own
  replication/consensus/storage engine, coin/TIX module, secrets or production
  runtime is introduced. No production readiness, durability, distributed
  fencing, bank exactly-once, chain finality, legal compliance or protocol
  completeness is verified. No Cargo, measurement or gate-listener run is claimed.
