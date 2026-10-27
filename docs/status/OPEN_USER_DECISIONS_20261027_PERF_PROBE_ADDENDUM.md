# Open User decisions — October 27 perf-probe pin addendum

## Basis and provenance

Builder-authored, dated 2026-10-27; a record, not a decision. Node:
`plan-plan-open-decisions-addendum-perf-probe-`; issue: none;
`depends_on: []`; audit floor A2; `astra_gate: None`; `user_merge: False`.
This is not ASTRA program mode. The supervisor-supplied node specification and
read-only design plan are the task input; there is no task document under
`docs/tasks/` for this loop-proposed node and no entry in `.aiops/program.json`.
Historical Task 004 is background, not current authorization.
Source: supplied KIX planner run `1793083431`
(`/workspace/kix-run/logs/planner_1793083431`); the planner was not executed.

Observed cached `origin/main`, base and starting branch HEAD:
`8e4813e868961adbabb7d1ee450a346f8fb6add1` (#321), on
`agent/kix-plan-plan-open-decisions-addendum-perf-probe-`.
Fetch was NOT_RUN under the supervisor's no-network rule; remote freshness
is unverified. No local base delta was observed or introduced. All current
blobs, source line numbers and statuses below refer to this recorded HEAD.

**This document selects no option and changes no node state.**
Decision owner for PERF-PROBE: **the User (repository owner)**.
The [October 27 closure](OPEN_USER_DECISIONS_20261027_CLOSURE.md) and its
linked earlier ledgers/addenda remain preserved. The
[validation record](../../validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md)
contains the Git outputs, candidate classification, preservation checks and
local documentation checks. This addendum supplies no owner answer.

## New stop — plan-perf-probe-fail-closed-and-release-repro

The external, unmerged source record is
`/workspace/kix-run/wt/plan-perf-probe-fail-closed-and-release-repro/DECISION_REQUIRED.md`,
SHA-256 `e3e2c6143c019b9b0ca704a4be6e4e6e26910fcb4acd568acd745975a80d272b`.
It was read as attributed input, not as a merged contract. Its numbered text
and digest are preserved in the validation record: lines 3–23 give its basis
and failed-run finding; 25–34 give the needed decision/options; 36–42 give
its recommendation and owner.

The stop reports a single release invocation at its basis
`9ed15a7adc93359e99bb5c3512a3ca20c77cb264`, exit 1 with
`frozen blob mismatch; refusing to write unbound performance evidence`, no
output directory and no measurements. **This node did not run that command.**
The stop also reports its branch-only BD-FAIL-CLOSED refactor and synthetic-hash
refusal tests as complete. That uncommitted work is not the implementation at
this addendum's HEAD and is not imported, tested or accepted here.

At the recorded HEAD,
[r1_perf_probe.rs](../../runtime/crates/kix-kernel/examples/r1_perf_probe.rs):8–11
pins `LOCKED_KERNEL`, `LOCKED_QUARANTINE`, `LOCKED_EDGE` and `LOCKED_MODEL`.
The complete mismatch/refusal block, lines 71–77, is:

```rust
    if kernel_blob != LOCKED_KERNEL
        || quarantine_blob != LOCKED_QUARANTINE
        || edge_blob != LOCKED_EDGE
        || model_blob != LOCKED_MODEL
    {
        return Err("frozen blob mismatch; refusing to write unbound performance evidence".into());
    }
```

The inputs are working-file hashes collected at lines 39–70. The block precedes
workload calls (85 and 88) and directory creation (95). `LOCKED_EDGE` is
`d37ea7df55423c83bedee16bf12bdc8dd61f7cae`; builder command
`git rev-parse HEAD:runtime/crates/kix-kernel/tests/contract_edge_cases.rs`
returns `8533d6419077d6a073d16ca2fce3a7d461a4de5b`, matching the stop's
reported current blob. Working-file `git hash-object` agrees. The other three
example pins match. This is an example-specific frozen-input mismatch, not a
change to either AGENTS §4 lock and not a newly established class C violation.

The stop names `7ba8003` (availability) and `41abd14` (precedence).
Those are implementation commits, **not first-parent merge SHAs**. The merge
identities and parent-to-merge edge blobs are:

| PR | First-parent merge SHA | Implementation commit (merge second parent) | Edge blob: first parent → merge |
|---|---|---|---|
| #317 | `d016caee4ae40f28f531809359ee77ac22db0073` | `7ba8003f4a18bbd622ce87b1cfb0fa856e4a4178` | `d37ea7df55423c83bedee16bf12bdc8dd61f7cae` → `dab33001dee34f7e773645b3ff17119cfb56a614` |
| #318 | `70b976c0b8db686b1d21ff0831c275abf77a3d0a` | `41abd142e7b16a6ab1370cf001b3fccb4b720900` | `dab33001dee34f7e773645b3ff17119cfb56a614` → `8533d6419077d6a073d16ca2fce3a7d461a4de5b` |

These are the only first-parent merges changing the edge file after the pinned
version; their diffs append availability/precedence tests without changing the
example. The stop attributes the pin to `9e8f489` on September 18; Git shows
that commit introduced the **edge source blob**. The example's `LOCKED_EDGE`
constant was introduced later in `28c9c130e9ab9be017a8302dc1e4a4cbd3cbfffa`.
This distinction corrects provenance only; it does not change any pin.

Source inspection of tracked runtime tests, scripts and workflows finds **no
test or CI step that runs the release example**. The release command in
[PERFORMANCE_MEASUREMENT.md](../contracts/PERFORMANCE_MEASUREMENT.md#실행과-자료)
is a manual procedure, explicitly not CI execution evidence. Cargo example
compilation, Clippy `--all-targets`, helper calls in `performance_harness.rs`
and the test-discovery guard do not execute the example's `main` refusal path.
The performance-map checker enforces the two AGENTS locks and their example
constants; it does not enforce the edge/model pins against current sources.

The [performance map](PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md#2-map) rows
`X-RELEASE-REPRO`, `X-OUTPUT-FILES` and `BD-RUN-VALUES` stay **NOT_RUN**.
No map row is edited or regraded. Product TPS, p99 and failure-rate targets
remain **UNDETERMINED (owner: User)**; all other existing policy uncertainties
retain their recorded owners. Preserving the rows is not a selection of D.

## Options — verbatim source text

Source: external stop identified above, lines 31–34. Quoted qualifications are
part of each option; none is selected or endorsed by this addendum.

> - **A. Re-pin in a separate task.** A new task, branch, session and PR updates `LOCKED_EDGE` to the current blob, with owner authorization, then runs the release example once and records the eleven files and `binding.json`. The two AGENTS §4 locks stay unchanged. Cost: the pin goes stale again whenever `contract_edge_cases.rs` changes, unless a check is added.
> - **B. Bind but do not gate on the example-specific blobs.** Record the edge and model blobs in `binding.json` but refuse only on the two AGENTS §4 locks. This changes the contract clause `잠금 blob이 필요한 값과 다르면 예시는 증거 파일을 쓰지 않고 실패한다` as it applies to four blobs, so it needs a contract decision.
> - **C. Run against a historical tree** where all four pins match (before `7ba8003`). That measures old test sources, so it is not current evidence.
> - **D. Leave the three release rows NOT_RUN** and take no action.

Source recommendation (stop line 38), quoted separately and **not endorsed**:

> **A**, as a separate task. Optionally that task, or another one, adds a cheap test or checker rule that compares `LOCKED_EDGE` and `LOCKED_MODEL` with the current blobs, so future drift fails CI instead of failing silently at release time. Any such checker or CI change needs its own scope.

The source's “Who decides” section names the User (repository owner).
Choosing A or B, commissioning a checker, running C or accepting D requires
an owner disposition outside this builder task. This document makes none.

## Read-only blob-pin inventory

Scope: all tracked Rust, Python and Markdown at the basis HEAD, scanned with
`git grep -n -E '(^|[^0-9a-f])[0-9a-f]{40}([^0-9a-f]|$)' HEAD -- '*.rs' '*.py' '*.md'`.
The scan has 2,105 matching lines and 434 unique exact-width values. Every
candidate is classified in the validation record. Longer digests do not match;
commit/tree/tag IDs are excluded. Historical input/output snapshots and
external-source citations are documentary evidence, not current equality
requirements. They are classified separately rather than treated as executable
pins. The A/L/R anchors explicitly required by this task are retained even
though they are historical provenance requirements, not live source locks.

The table includes every executable blob constant/dictionary, synthetic binding
literal and assertion, the normative Markdown locks and specified historical
anchors. Repeated Markdown evidence copies of these same values are enumerated
by file:line in the occurrence appendix; the table's pinned/current/status and
impact apply to every listed occurrence. Current means `HEAD:<target>`, also
checked against working bytes. Raw pinned literals come from the recorded
`git grep`/`git show`; object types from `git cat-file -t`; current IDs from
`git rev-parse` and `git hash-object`. A/L/R are additionally verified at
`0394a36a655b86bacb568b055d377d4c4fd91185`.

| ID | Occurrence file:line (principal sites) | Symbol/role | Target path | Pinned value | Current HEAD blob | MATCH/DIFFERS | Conditional option impact | Evidence reference |
|---|---|---|---|---|---|---|---|---|
| P1 | runtime/crates/kix-kernel/examples/r1_perf_probe.rs:8; tests/contract_invariants.rs:17; tests/e4_state_model.rs:30 (tests relative to that crate) | LOCKED_KERNEL / LOCKED / Python lock dictionaries / normative kernel lock | `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | MATCH | None; AGENTS lock remains required under A–D | Validation: pin P1; complete source scan; occurrence appendix |
| P2 | runtime/crates/kix-kernel/examples/r1_perf_probe.rs:9; runtime/crates/kix-kernel/tests/e4_state_model.rs:31 | LOCKED_QUARANTINE / LOCKED_TEST / Python lock dictionaries / normative quarantine lock | `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` | MATCH | None; AGENTS lock remains required under A–D | Validation: pin P2; complete source scan; occurrence appendix |
| P3 | runtime/crates/kix-kernel/examples/r1_perf_probe.rs:10; docs/tasks/TASK_003C1_EVIDENCE_GATES.md:22; docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:66 | LOCKED_EDGE; immutable historical task input; synthetic binding literals | `runtime/crates/kix-kernel/tests/contract_edge_cases.rs` | `d37ea7df55423c83bedee16bf12bdc8dd61f7cae` | `8533d6419077d6a073d16ca2fce3a7d461a4de5b` | DIFFERS | A: re-pin example only in a separate task; B: change gating, retain binding; C: historical tree; D: no change. No task-input rewrite | Validation: pin P3; complete source scan; occurrence appendix |
| P4 | runtime/crates/kix-kernel/examples/r1_perf_probe.rs:11; docs/tasks/TASK_003C1_EVIDENCE_GATES.md:23; docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:67 | LOCKED_MODEL; immutable historical task input; synthetic binding literals | `runtime/crates/kix-kernel/tests/support/model_v4.rs` | `f020860b86933bf7511befccdb833b0c532b3629` | `f020860b86933bf7511befccdb833b0c532b3629` | MATCH | B: change gating, retain binding; A: no pin update needed; C: historical tree; D: no change. No task-input rewrite | Validation: pin P4; complete source scan; occurrence appendix |
| P5 | scripts/check_sdk_client.py:31 | SOURCE_BLOB; historical SDK source binding | `reference/v0.3-rc1/protocol_contract.json` | `619ae21c82ca3df5661bd3831613f15fa65225ff` | `619ae21c82ca3df5661bd3831613f15fa65225ff` | MATCH | None under A–D | Validation: pin P5; complete source scan; occurrence appendix |
| A | docs/contracts/CONTRACT_INVARIANTS.md:32; docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:84; docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:9 | Historical anchor A; S2-ANCHORS / F-B1 | `docs/adr/0001-ktx-authority-commit-recovery.md` | `07c36869e7b68fff10b02e6c59d7119df56d0785` | `054bc714b3c475fb8536df8d2d788b42e8c74b6c` | DIFFERS | None under A–D; preserve historical anchor | Validation: pin A; complete source scan; occurrence appendix |
| L | docs/contracts/CONTRACT_INVARIANTS.md:33; docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:84; docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:9 | Historical anchor L; S2-ANCHORS / F-B1 | `docs/contracts/STATE_LIFECYCLE.md` | `e953c4870aaeee24b13c75a8647c50609720ae01` | `8682b6ecd3de2f10dc8bb73ff8a03e3b8f9ace9d` | DIFFERS | None under A–D; preserve historical anchor | Validation: pin L; complete source scan; occurrence appendix |
| R | docs/contracts/CONTRACT_INVARIANTS.md:34; docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:84 | Historical anchor R; S2-ANCHORS / F-B1 | `runtime/crates/kix-kernel/README.md` | `900866ee99a71254fb7da1ad2aa4640477ac550c` | `788896ed3e00bae3d06d26b7e2ce999a00ff1029` | DIFFERS | None under A–D; preserve historical anchor | Validation: pin R; complete source scan; occurrence appendix |

A–D are conditional descriptions of the source options, not a change plan.
B also needs the source's contract decision about four-blob refusal; its impact
is semantic, even where a constant's value stays the same. C edits no current
pin and measures another tree. D edits nothing. Neither A nor B authorizes
changing synthetic fixture strings merely because they contain an old blob.
All other locks and historical anchors are untouched under these options.

`performance_harness.rs:192–195,211–214` supplies/asserts synthetic binding
strings. Those are serialization fixtures, not current-source comparisons.
Their edge string DIFFERS from the current file but does not fail that test.
The Python sites below enforce the two locks or SDK source pin; they do not
add a release-example invocation. S2-ANCHORS (map line 40) stays NOT_COVERED;
F-B1 (84) is a class B historical-source characterization, not a re-pin request.
The A/L/R DIFFERS results are expected provenance observations.

## Eight-stop table

Owners are copied verbatim from the October 27 closure, whose holding records
remain authoritative for the seven existing stops. PERF-PROBE is a document-local
identifier. As in that closure, RESOLVED-BY-MERGE would require the named blocking
condition to be gone at this basis, with a PR, full SHA and artifact; it would
still be documentary evidence, not owner approval. No such resolution is found.
All eight first-parent merges #314–#321 and their changed paths were inspected.

| Item id | Stop | Holding record | Owner (verbatim, as recorded) | Status at 8e4813e | Resolved by (PR · SHA) | #314–#321 facts |
|---|---|---|---|---|---|---|
| L1 | `k-stage5-durable-tx` host | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User / supervisor (build host) | STILL OPEN | none | #314 carries the host stop; #321 checks discovery only and preserves the stage-5 self-test-only exception. No pinned-backend acceptance artifacts added. |
| L2 | `rs-4-l2` measurement environment | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User (spend / environment); Astra (workload) | STILL OPEN | none | #314 carries the environment/workload stop. #315–#321 add no L2 measurement or acceptable-load decision. |
| A2 | `plan-plan-gate-fsm-seeded-journey-differentia` loopback host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) | Supervisor / repository owner controlling the execution host | STILL OPEN | none | #314 carries the owned host gap. #321 checks textual reachability of existing test modules; no seeded journey or bound-listener observation is added. |
| A4 | `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) | User / repository owner | STILL OPEN | none | #314 carries the duplicate-sync stop; #315–#321 contain no disposition of that duplicate. |
| A5 | AI delegation §7 check order | [AI delegation addendum](OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure) | Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge. | STILL OPEN | none | #314 carries the attributed class C order stop; #315–#321 change neither the mock nor its contract. |
| BCS1 | BCS1 checker scope | [BCS1 addendum](OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md#new-stop--plan-plan-bcs1-contract-bound-regressions) | the User/orchestrator owning this loop-proposed node. | STILL OPEN | none | #314 carries the checker-scope stop; #321 adds suite discovery, without adapting BCS1 TEST_FILES or its NOT_COVERED locks. |
| SD1 | SDK manifest §4 check order | [SDK addendum](OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md#new-stop--plan-plan-sdk-compat-manifest-clause-evidence) | Who decides: the User. | STILL OPEN | none | #314 carries the attributed class C order stop; #315–#321 change neither verifier nor contract and add no manifest evidence map. |
| PERF-PROBE | `LOCKED_EDGE` frozen-input drift | External stop, digest and lines in §New stop above | The User (repository owner). | STILL OPEN | none | #317/#318 changed edge bytes; #316/#319 leave release rows NOT_RUN; #321 adds no release-example execution. |

The basis still lacks L1's `durable/`, `scripts/stage5_local_check.py` and
`validation/2026-10-13-k-stage5-durable-tx/`, L2's
`validation/2026-10-15-rs-4-l2-load/`, and SD1's manifest evidence map/checker.
These are absent-artifact observations, not links asserting existence.
A2's integration-gate map still explicitly holds the seeded-journey gap;
A5 registration/tool/binding order, BCS1's two allowed test paths and SD1
comparisons-before-profile order remain unchanged. Earlier owner options are
available through the [closure's options](OPEN_USER_DECISIONS_20261027_CLOSURE.md#options--verbatim-from-the-holding-records).

## Repository facts in #314–#321

PR numbers and full SHAs come from local first-parent history, not a GitHub
query. Merge diffs and the cited records were inspected. Existing stops are
carried forward only after checking their named blocking evidence.

| PR | Merge SHA | Record | Fact relevant to item(s) |
|---|---|---|---|
| #314 | `035d5705c93b318a49941ce5f7410f843360c427` | [October 27 closure](OPEN_USER_DECISIONS_20261027_CLOSURE.md) | All seven existing stops remain STILL OPEN; the record selects no option and changes no node state. |
| #315 | `eb1caf8285c174697d78834246a304ffe9006427` | [Reply assertions](../../validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md) | F-B3 assertions/sensitivity are source-informed; S4-PROBES remains PARTIAL. No open-stop decision or release-example execution. |
| #316 | `876f41067bc7eb70bcd6ebd9c744c11b46f046b6` | [JSON/CSV closure](../../validation/2026-10-27-plan-perf-harness-map-json-csv-closure-2/README.md) | Six public-API debug tests; six rows become COVERED, M-ELAPSED becomes PARTIAL. X-RELEASE-REPRO, X-OUTPUT-FILES and BD-RUN-VALUES stay NOT_RUN. |
| #317 | `d016caee4ae40f28f531809359ee77ac22db0073` | [S5 availability](../../validation/2026-10-27-plan-contract-invariants-s5-availability/README.md) | Seven deterministic success examples append to edge file; S5-SAFE-REJECT/S5-FINITE stay PARTIAL; class B F-B5. First edge drift; example pin unchanged. |
| #318 | `70b976c0b8db686b1d21ff0831c275abf77a3d0a` | [S5 precedence](../../validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md) | Nineteen guard-pair tests append to edge file; S5-PRECEDENCE stays PARTIAL; class B F-B6. Second edge change; example pin unchanged. |
| #319 | `9d50fb660248b66a5959f48f7dc96e68c9d5530b` | [Kernel construction counter](../../validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md) | B-ZERO-KERNEL-REBUILD becomes COVERED through a counted helper and three tests. Example/contract/checker unchanged; three release rows still NOT_RUN. |
| #320 | `9ed15a7adc93359e99bb5c3512a3ca20c77cb264` | [v5 histories](../../validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md) | Finite source-informed public-API histories/sensitivity only; class B, no reported class C. No locked v4 source, owner decision or contract change. |
| #321 | `8e4813e868961adbabb7d1ee450a346f8fb6add1` | [Test-discovery guard](../../validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md) | Adds the stdlib textual suite-reachability guard and plain/self-test workflow calls. Does not discover/execute the release example, provision a host or resolve a stop. |

## Complete occurrence appendix

Every occurrence of the eight inventoried pin values in the basis scan is
listed below, grouped only by value and containing file. Line numbers identify
matching lines, not counts of repeated tokens on one line. P1–P5 and A/L/R refer
to the full pinned/current/target/status/option columns above. Markdown copies
inside old validation transcripts are evidence copies, not extra enforcement
sites. This appendix deliberately excludes this uncommitted addendum and its
validation record from the basis scan to avoid self-reference.

| Inventory ID | Occurrence file:line(s) |
|---|---|
| P1 | `.github/PULL_REQUEST_TEMPLATE/devin_pr_template.md:19` |
| P1 | `AGENTS.md:92` |
| P1 | `README.md:20` |
| P1 | `docs/CODE_HYGIENE_BACKLOG.md:28` |
| P1 | `docs/DEVELOPMENT_PLAN.md:57` |
| P1 | `docs/adr/0001-ktx-authority-commit-recovery.md:70` |
| P1 | `docs/adr/0003-coin-tix-lock-localnet-re-ruling-request.md:27` |
| P1 | `docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md:28` |
| P1 | `docs/contracts/ADAPTER_EVENT_IDENTITY.md:45` |
| P1 | `docs/contracts/CONTRACT_INVARIANTS.md:5` |
| P1 | `docs/contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md:6` |
| P1 | `docs/contracts/PERFORMANCE_BASELINE_V4.md:26` |
| P1 | `docs/contracts/PG_TOSS_CARD_PROFILE.md:61` |
| P1 | `docs/contracts/RIGHTS_SCALE_PROFILE.md:24` |
| P1 | `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:81` |
| P1 | `docs/contracts/STATE_LIFECYCLE.md:12,488` |
| P1 | `docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md:7` |
| P1 | `docs/contracts/TOKEN_ROLE_AND_SUPPLY.md:7` |
| P1 | `docs/decisions/AI_DELEGATION_EXECUTION_DECISION_PROPOSAL_20261016.md:32` |
| P1 | `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md:20` |
| P1 | `docs/decisions/CUT_PROOF_I12_20261008.md:12` |
| P1 | `docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md:28` |
| P1 | `docs/decisions/GATE_BROWSER_ACCESS_DECISION_20261008.md:10` |
| P1 | `docs/decisions/INTEGRATION_A_DECISION_PROPOSAL_20261009.md:20` |
| P1 | `docs/decisions/INTEGRATION_A_REESTIMATE_20261009.md:18` |
| P1 | `docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md:18` |
| P1 | `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md:10` |
| P1 | `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md:16` |
| P1 | `docs/decisions/TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md:32` |
| P1 | `docs/decisions/TL2_DOES_NOT_OPEN_20261009.md:9` |
| P1 | `docs/decisions/TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md:9` |
| P1 | `docs/decisions/TL4_THREAT_MODEL_20261009.md:9` |
| P1 | `docs/decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md:32` |
| P1 | `docs/decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md:7` |
| P1 | `docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:31,207` |
| P1 | `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md:8` |
| P1 | `docs/status/AI_DELEGATION_LAYER_MATRIX.md:10` |
| P1 | `docs/status/ASTRA_DECISION_SHEETS_KO.md:22` |
| P1 | `docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md:29` |
| P1 | `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md:10` |
| P1 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:10` |
| P1 | `docs/status/CURRENT_CAPABILITY_REGISTER.md:257` |
| P1 | `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:11` |
| P1 | `docs/status/I12_REVIEW_PACK.md:20` |
| P1 | `docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:10` |
| P1 | `docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:10` |
| P1 | `docs/status/LOCK_ENFORCEMENT.md:17,62` |
| P1 | `docs/status/OPEN_USER_DECISIONS_20261022.md:46` |
| P1 | `docs/status/ORIGINAL_32_STATUS.md:70` |
| P1 | `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:11` |
| P1 | `docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md:10` |
| P1 | `docs/status/PR11_PRESERVATION.md:57,81` |
| P1 | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:8` |
| P1 | `docs/status/RS0_REVIEW_PACK.md:19` |
| P1 | `docs/status/TOKEN_LEGAL_REVIEW_BRIEF_KO.md:7` |
| P1 | `docs/status/V5_TRANSITION_EVIDENCE_MAP.md:8` |
| P1 | `docs/tasks/DEVIN_FIRST_BATCH_E4_AUDIT.md:26` |
| P1 | `docs/tasks/TASK_003C1_EVIDENCE_GATES.md:20` |
| P1 | `docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:64` |
| P1 | `exploration/stage4/budget.py:40` |
| P1 | `runtime/crates/kix-kernel/README.md:8` |
| P1 | `runtime/crates/kix-kernel/examples/r1_perf_probe.rs:8` |
| P1 | `runtime/crates/kix-kernel/tests/contract_invariants.rs:17` |
| P1 | `runtime/crates/kix-kernel/tests/e4_state_model.rs:30` |
| P1 | `runtime/crates/kix-kernel/tests/performance_harness.rs:192,211` |
| P1 | `scripts/check_adapter_identity_map.py:63` |
| P1 | `scripts/check_bcs1_evidence_map.py:17` |
| P1 | `scripts/check_contract_invariants_evidence_map.py:18` |
| P1 | `scripts/check_feature_semantics_evidence_map.py:70` |
| P1 | `scripts/check_integration_gate_contract_evidence_map.py:88` |
| P1 | `scripts/check_lifecycle_adr_evidence_map.py:23` |
| P1 | `scripts/check_performance_measurement_evidence_map.py:22` |
| P1 | `scripts/check_readiness_evidence_map.py:71` |
| P1 | `scripts/check_toss_card_profile_evidence_map.py:22` |
| P1 | `scripts/check_v5_transition_evidence_map.py:69` |
| P1 | `validation/2026-09-15-r1-observation-slots/README.md:16` |
| P1 | `validation/2026-09-16-first-batch/README.md:4` |
| P1 | `validation/2026-09-18-contract-edge-cases/README.md:21` |
| P1 | `validation/2026-09-19-task-002-lifecycle-precedence/README.md:35` |
| P1 | `validation/2026-09-19-task-003a-e4-model-schema/README.md:34` |
| P1 | `validation/2026-09-19-task-003b-e4-property-expansion/README.md:33` |
| P1 | `validation/2026-09-21-task-003c1-evidence-gates/README.md:38` |
| P1 | `validation/2026-09-23-cp-boundary-003/README.md:18` |
| P1 | `validation/2026-09-25-task-004-perf-measurement/README.md:37` |
| P1 | `validation/2026-09-26-prod-readiness-infra/README.md:36` |
| P1 | `validation/2026-09-28-main-state-catchup/README.md:69` |
| P1 | `validation/2026-10-05-k1-e4-residual-review/README.md:103` |
| P1 | `validation/2026-10-08-ai-delegation-contract-mock/README.md:21` |
| P1 | `validation/2026-10-08-k1-adapter-event-identity/README.md:46` |
| P1 | `validation/2026-10-08-k1-evidence-close/README.md:17,115` |
| P1 | `validation/2026-10-09-audit2-gate-browser-access-test-determinism/README.md:51,126` |
| P1 | `validation/2026-10-09-audit3-openapi-promotion-owner-decision-record/README.md:29,61` |
| P1 | `validation/2026-10-09-audit3-tl-docs-plan-index-sync/README.md:28,55` |
| P1 | `validation/2026-10-09-audit4-audit4-plan-s5-index-f04-criteria-toss-p/README.md:29,64` |
| P1 | `validation/2026-10-09-audit4-tl-plan-index-register-sync/README.md:29,59` |
| P1 | `validation/2026-10-09-ci-wire-token-reward-suite/README.md:32` |
| P1 | `validation/2026-10-09-f04-real-funds-lift-criteria/README.md:18,51` |
| P1 | `validation/2026-10-09-k-a-integration-decision/README.md:19,53` |
| P1 | `validation/2026-10-09-k-a-reestimate/README.md:15,74` |
| P1 | `validation/2026-10-09-k-stage4-adoption-decision/README.md:18,40` |
| P1 | `validation/2026-10-09-k2-retention-proposal/README.md:20,42` |
| P1 | `validation/2026-10-09-openapi-catalogue-promotion/README.md:29` |
| P1 | `validation/2026-10-09-tl-4-token-layer-verification/README.md:43,69` |
| P1 | `validation/2026-10-09-tl-5-decision/README.md:19,54` |
| P1 | `validation/2026-10-09-toss-sandbox-conformance-plan/README.md:19,58` |
| P1 | `validation/2026-10-12-register-nontl-rows-sync/README.md:36,101` |
| P1 | `validation/2026-10-12-rs0-review-pack/README.md:40,108` |
| P1 | `validation/2026-10-13-astra-decision-sheets-listvalues-v5-rs0/README.md:34,90` |
| P1 | `validation/2026-10-13-audit5-docs-index-check-ci-wire/README.md:44,135` |
| P1 | `validation/2026-10-13-audit5-plan-index-sync-b/README.md:48,161` |
| P1 | `validation/2026-10-13-audit5-source-map-checker-decouple/README.md:44,135` |
| P1 | `validation/2026-10-13-docs-index-coverage-check/README.md:44,140` |
| P1 | `validation/2026-10-13-i12-review-pack/README.md:41,116` |
| P1 | `validation/2026-10-13-k-stage2-v5-impl/README.md:30,158` |
| P1 | `validation/2026-10-13-offline-doc-checks-ci/README.md:41,122` |
| P1 | `validation/2026-10-14-audit6-plan-index-sync/README.md:36,169` |
| P1 | `validation/2026-10-14-register-sync-v5-rs/README.md:36,132` |
| P1 | `validation/2026-10-14-rs-1-issuercap-probe/README.md:89` |
| P1 | `validation/2026-10-14-rs-1-public-path/README.md:75` |
| P1 | `validation/2026-10-14-rs-2-private-path/README.md:61` |
| P1 | `validation/2026-10-14-rs-3a-delegation-primitives/README.md:91` |
| P1 | `validation/2026-10-14-rs-3b-delegated-exec/README.md:87` |
| P1 | `validation/2026-10-14-rs-profile-revision-log-0-2/README.md:43,118` |
| P1 | `validation/2026-10-14-rs1-state-answer-archive/README.md:55` |
| P1 | `validation/2026-10-15-docs-index-check-validation-records/README.md:42,150,161` |
| P1 | `validation/2026-10-15-rs-4-l1-load/README.md:141` |
| P1 | `validation/2026-10-16-ai-delegation-execution-decision/README.md:19,47` |
| P1 | `validation/2026-10-16-audit7-docs-index-allowlist-prune/README.md:21` |
| P1 | `validation/2026-10-16-audit7-plan-register-index-sync-20261016b/README.md:21` |
| P1 | `validation/2026-10-16-ci-wire-i12-proof-ids-check/README.md:27` |
| P1 | `validation/2026-10-16-delegation-layer-gap-matrix/README.md:15` |
| P1 | `validation/2026-10-16-feature-ir-plan-limit-edge-tests/README.md:20` |
| P1 | `validation/2026-10-16-plan-register-index-sync-20261016/README.md:22` |
| P1 | `validation/2026-10-16-rs-predicate-evidence-map/README.md:15,89` |
| P1 | `validation/2026-10-16-settlement-seeded-property-suite/README.md:15` |
| P1 | `validation/2026-10-16-testnet-key-management-decision/README.md:19,51` |
| P1 | `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md:15,99` |
| P1 | `validation/2026-10-17-audit8-plan-register-index-sync-20261017/README.md:21` |
| P1 | `validation/2026-10-17-booking-resale-admission-seeded-property/README.md:24,102` |
| P1 | `validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md:18` |
| P1 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:15` |
| P1 | `validation/2026-10-17-delegated-exec-seeded-differential/README.md:15` |
| P1 | `validation/2026-10-17-feature-semantics-v1-edge-fixtures/README.md:20` |
| P1 | `validation/2026-10-17-readiness-journal-byte-sweep/README.md:21` |
| P1 | `validation/2026-10-17-rs-im-evidence-map/README.md:15,95` |
| P1 | `validation/2026-10-18-audit8-loop-node-canonical-crosswalk/README.md:19` |
| P1 | `validation/2026-10-18-audit8-readiness-conformance-sweep-limit-note/README.md:17` |
| P1 | `validation/2026-10-18-audit8-rs-map-rs-c01-issuercap-open-cell/README.md:18` |
| P1 | `validation/2026-10-18-contract-error-code-coverage/README.md:14` |
| P1 | `validation/2026-10-18-readiness-crash-point-sweep/README.md:13` |
| P1 | `validation/2026-10-19-bra-fsm-error-code-coverage/README.md:14` |
| P1 | `validation/2026-10-19-rs-model-gap-closure/README.md:15,76` |
| P1 | `validation/2026-10-19-tl-predicate-evidence-map/README.md:14,79` |
| P1 | `validation/2026-10-19-v5-lifecycle-seeded-model-test/README.md:22` |
| P1 | `validation/2026-10-20-adapter-identity-evidence-map/README.md:16,78` |
| P1 | `validation/2026-10-20-ai-delegation-wrap-conformance/README.md:29` |
| P1 | `validation/2026-10-20-plan-register-index-sync-20261020/README.md:22` |
| P1 | `validation/2026-10-20-plan-rs-grant-cut-order-tests/README.md:15,67` |
| P1 | `validation/2026-10-20-read-model-contract-fixture-prep/README.md:27,104` |
| P1 | `validation/2026-10-20-stage5-preflight/README.md:112,122` |
| P1 | `validation/2026-10-20-token-reward-readiness-wrap/README.md:13` |
| P1 | `validation/2026-10-20-token-reward-rejection-atomicity/README.md:13` |
| P1 | `validation/2026-10-20-v5-transition-evidence-map/README.md:16,69` |
| P1 | `validation/2026-10-21-astra-decision-sheets-rs-stage5/README.md:42,105` |
| P1 | `validation/2026-10-21-kix-types-boundary-fixtures/README.md:25` |
| P1 | `validation/2026-10-21-plan-register-index-sync-20261021/README.md:24` |
| P1 | `validation/2026-10-21-plan-rs-manifest-offline-regressions/README.md:84` |
| P1 | `validation/2026-10-21-plan-rs-ptau-header-tests/README.md:77` |
| P1 | `validation/2026-10-21-plan-rs-spend-witness-offline-tests/README.md:91` |
| P1 | `validation/2026-10-21-plan-rs-witness-ci-wiring/README.md:44` |
| P1 | `validation/2026-10-21-plan-rs-witness-offline-regressions/README.md:21` |
| P1 | `validation/2026-10-21-plan-rs-zk-encoding-regressions/README.md:72` |
| P1 | `validation/2026-10-21-readiness-checker-partial-fixture/README.md:133` |
| P1 | `validation/2026-10-21-readiness-runtime-evidence-map/README.md:16,84` |
| P1 | `validation/2026-10-21-reward-wrap-conformance/README.md:29` |
| P1 | `validation/2026-10-21-settlement-multi-payee-refund-corpus/README.md:15` |
| P1 | `validation/2026-10-21-v5-evidence-citation-guard/README.md:150` |
| P1 | `validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md:41,173` |
| P1 | `validation/2026-10-22-open-user-decisions-ledger/README.md:41,149` |
| P1 | `validation/2026-10-22-plan-register-index-sync-20261022/README.md:25` |
| P1 | `validation/2026-10-22-plan-rs-admission-packet-offline-tests/README.md:188` |
| P1 | `validation/2026-10-22-plan-rs-mint-wrapper-offline-tests/README.md:161` |
| P1 | `validation/2026-10-22-plan-rs-offline-test-entrypoint/README.md:142` |
| P1 | `validation/2026-10-22-plan-rs-verifier-binding-offline-tests/README.md:138` |
| P1 | `validation/2026-10-22-rs-offline-suite-evidence-sync/README.md:172` |
| P1 | `validation/2026-10-22-rs4-load-host-conditions-recorder/README.md:141` |
| P1 | `validation/2026-10-23-audit14-loop-node-crosswalk-refresh/README.md:175,424` |
| P1 | `validation/2026-10-23-audit14-open-decisions-closure/README.md:55` |
| P1 | `validation/2026-10-23-audit14-plan-register-index-sync/README.md:29` |
| P1 | `validation/2026-10-23-bra-section9-error-code-coverage/README.md:131` |
| P1 | `validation/2026-10-23-fsm-returned-data-isolation/README.md:155` |
| P1 | `validation/2026-10-23-owner-stop-handoff-addendum/README.md:191` |
| P1 | `validation/2026-10-23-plan-readiness-migration-edge-tests/README.md:134` |
| P1 | `validation/2026-10-23-plan-register-index-sync-20261023/README.md:32` |
| P1 | `validation/2026-10-23-plan-rs-summary-arithmetic-tests/README.md:169` |
| P1 | `validation/2026-10-23-readiness-receipt-audit-tests/README.md:20,270` |
| P1 | `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md:138,169,249,293` |
| P1 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md:15` |
| P1 | `validation/2026-10-24-bra-aid-returned-data-isolation/README.md:173` |
| P1 | `validation/2026-10-24-plan-register-index-sync/README.md:78` |
| P1 | `validation/2026-10-24-resale-admission-rejection-atomicity/README.md:22` |
| P1 | `validation/2026-10-24-reward-snapshot-isolation/README.md:186,326` |
| P1 | `validation/2026-10-25-aid-rejection-atomicity/README.md:230` |
| P1 | `validation/2026-10-25-audit15-open-decisions-closure/README.md:34` |
| P1 | `validation/2026-10-25-audit15-reference-test-sibling-path-guard/README.md:31` |
| P1 | `validation/2026-10-25-bra-contract-clause-evidence-map/README.md:134,222` |
| P1 | `validation/2026-10-25-ci-wire-product-contract-evidence-checkers/README.md:45` |
| P1 | `validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md:70,171` |
| P1 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:231` |
| P1 | `validation/2026-10-25-plan-primary-price-fee-contract-clause-eviden/README.md:144,186` |
| P1 | `validation/2026-10-25-plan-register-index-crosswalk-sync/README.md:106,189` |
| P1 | `validation/2026-10-25-plan-register-index-sync-20261025/README.md:110` |
| P1 | `validation/2026-10-25-plan-section5-quote-completeness/README.md:339` |
| P1 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:216` |
| P1 | `validation/2026-10-25-restore-fingerprint-equivalence/README.md:198` |
| P1 | `validation/2026-10-25-settlement-contract-clause-evidence-map/README.md:141` |
| P1 | `validation/2026-10-26-plan-ai-delegation-contract-clause-evidence-m/README.md:157` |
| P1 | `validation/2026-10-26-plan-bcs1-contract-clause-evidence-map/README.md:41` |
| P1 | `validation/2026-10-26-plan-ci-checker-wiring-guard/README.md:35` |
| P1 | `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md:25` |
| P1 | `validation/2026-10-26-plan-contract-invariants-inv3-sensitivity/README.md:32,145` |
| P1 | `validation/2026-10-26-plan-evidence-map-rollup-check/README.md:84` |
| P1 | `validation/2026-10-26-plan-feature-ir-money-profile-precedence-tests/README.md:127` |
| P1 | `validation/2026-10-26-plan-feature-ir-validator-matrix-closure/README.md:146` |
| P1 | `validation/2026-10-26-plan-feature-semantics-v1-evidence-map/README.md:27` |
| P1 | `validation/2026-10-26-plan-integration-gate-contract-clause-ev/README.md:19` |
| P1 | `validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md:47,162` |
| P1 | `validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:116,217` |
| P1 | `validation/2026-10-26-plan-lifecycle-adr-clause-evidence-map/README.md:23` |
| P1 | `validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md:45,519,559` |
| P1 | `validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md:138,1197,1232,1673,1688` |
| P1 | `validation/2026-10-26-plan-open-decisions-addendum-bcs1-checke/README.md:206,220` |
| P1 | `validation/2026-10-26-plan-perf-harness-map-partial-closure/README.md:18,188,329` |
| P1 | `validation/2026-10-26-plan-performance-measurement-clause-evid/README.md:43` |
| P1 | `validation/2026-10-26-plan-primary-fee-pf-c05-isolation-tests/README.md:97` |
| P1 | `validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md:482,713,745,773,880` |
| P1 | `validation/2026-10-26-plan-toss-card-profile-evidence-map/README.md:25` |
| P1 | `validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md:35` |
| P1 | `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:22` |
| P1 | `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:22` |
| P1 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:25` |
| P1 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:65,316,329,1644,1708,1966,1992,3042,3055` |
| P1 | `validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md:17` |
| P1 | `validation/2026-10-27-plan-perf-harness-map-json-csv-closure-2/README.md:18` |
| P1 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md:20` |
| P2 | `.github/PULL_REQUEST_TEMPLATE/devin_pr_template.md:20` |
| P2 | `AGENTS.md:94` |
| P2 | `README.md:21` |
| P2 | `docs/CODE_HYGIENE_BACKLOG.md:29` |
| P2 | `docs/DEVELOPMENT_PLAN.md:58` |
| P2 | `docs/adr/0003-coin-tix-lock-localnet-re-ruling-request.md:28` |
| P2 | `docs/aiops/FINANCE_COMPLETION_DESIGN_KO.md:28` |
| P2 | `docs/contracts/CONTRACT_INVARIANTS.md:6` |
| P2 | `docs/contracts/MOVE_PRIMARY_ISSUANCE_PRICE_FEE.md:6` |
| P2 | `docs/contracts/RIGHTS_SCALE_PROFILE.md:24` |
| P2 | `docs/contracts/SETTLEMENT_DISTRIBUTION_F01_F03.md:82` |
| P2 | `docs/contracts/TOKEN_AUTHORITY_AND_LIFECYCLE.md:7` |
| P2 | `docs/contracts/TOKEN_ROLE_AND_SUPPLY.md:7` |
| P2 | `docs/decisions/AI_DELEGATION_EXECUTION_DECISION_PROPOSAL_20261016.md:33` |
| P2 | `docs/decisions/BACKEND_ADOPTION_PROPOSAL_20261009.md:20` |
| P2 | `docs/decisions/CUT_PROOF_I12_20261008.md:12` |
| P2 | `docs/decisions/F04_REAL_FUNDS_LIFT_CRITERIA_20261009.md:29` |
| P2 | `docs/decisions/GATE_BROWSER_ACCESS_DECISION_20261008.md:10` |
| P2 | `docs/decisions/INTEGRATION_A_DECISION_PROPOSAL_20261009.md:20` |
| P2 | `docs/decisions/INTEGRATION_A_REESTIMATE_20261009.md:18` |
| P2 | `docs/decisions/RETENTION_PERIODS_PROPOSAL_20261009.md:18` |
| P2 | `docs/decisions/RIGHTS_SCALE_RS0_DECISION_20261008.md:10` |
| P2 | `docs/decisions/STAGE2_V5_CRATE_DESIGN_DECISION_20261008.md:16` |
| P2 | `docs/decisions/TESTNET_KEY_MANAGEMENT_DECISION_PROPOSAL_20261016.md:33` |
| P2 | `docs/decisions/TL2_DOES_NOT_OPEN_20261009.md:9` |
| P2 | `docs/decisions/TL3_ONCHAIN_DOES_NOT_OPEN_20261009.md:9` |
| P2 | `docs/decisions/TL4_THREAT_MODEL_20261009.md:9` |
| P2 | `docs/decisions/TL5_ACTIVATION_DECISION_PROPOSAL_20261009.md:33` |
| P2 | `docs/decisions/TL_PRICE_SOURCE_NOT_NEEDED_20261009.md:7` |
| P2 | `docs/decisions/TOKEN_LAYER_AND_RIGHTS_SCALE_SCOPE_20260929.md:31,207` |
| P2 | `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md:8` |
| P2 | `docs/status/AI_DELEGATION_LAYER_MATRIX.md:10` |
| P2 | `docs/status/ASTRA_DECISION_SHEETS_KO.md:24` |
| P2 | `docs/status/ASTRA_DECISION_SHEETS_RS_STAGE5_KO.md:31` |
| P2 | `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md:10` |
| P2 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:10` |
| P2 | `docs/status/CURRENT_CAPABILITY_REGISTER.md:258` |
| P2 | `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:11` |
| P2 | `docs/status/I12_REVIEW_PACK.md:22` |
| P2 | `docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:10` |
| P2 | `docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:10` |
| P2 | `docs/status/LOCK_ENFORCEMENT.md:18,63` |
| P2 | `docs/status/OPEN_USER_DECISIONS_20261022.md:48` |
| P2 | `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:11` |
| P2 | `docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md:10` |
| P2 | `docs/status/PR11_PRESERVATION.md:82` |
| P2 | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:8` |
| P2 | `docs/status/RS0_REVIEW_PACK.md:21` |
| P2 | `docs/status/TOKEN_LEGAL_REVIEW_BRIEF_KO.md:7` |
| P2 | `docs/status/V5_TRANSITION_EVIDENCE_MAP.md:8` |
| P2 | `docs/tasks/DEVIN_FIRST_BATCH_E4_AUDIT.md:28` |
| P2 | `docs/tasks/TASK_003C1_EVIDENCE_GATES.md:21` |
| P2 | `docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:65` |
| P2 | `exploration/stage4/budget.py:41` |
| P2 | `runtime/crates/kix-kernel/README.md:9` |
| P2 | `runtime/crates/kix-kernel/examples/r1_perf_probe.rs:9` |
| P2 | `runtime/crates/kix-kernel/tests/e4_state_model.rs:31` |
| P2 | `runtime/crates/kix-kernel/tests/performance_harness.rs:193,212` |
| P2 | `scripts/check_adapter_identity_map.py:64` |
| P2 | `scripts/check_bcs1_evidence_map.py:19` |
| P2 | `scripts/check_contract_invariants_evidence_map.py:20` |
| P2 | `scripts/check_feature_semantics_evidence_map.py:72` |
| P2 | `scripts/check_integration_gate_contract_evidence_map.py:90` |
| P2 | `scripts/check_lifecycle_adr_evidence_map.py:25` |
| P2 | `scripts/check_performance_measurement_evidence_map.py:24` |
| P2 | `scripts/check_readiness_evidence_map.py:72` |
| P2 | `scripts/check_toss_card_profile_evidence_map.py:24` |
| P2 | `scripts/check_v5_transition_evidence_map.py:70` |
| P2 | `validation/2026-09-15-r1-observation-slots/README.md:17` |
| P2 | `validation/2026-09-16-first-batch/README.md:5` |
| P2 | `validation/2026-09-18-contract-edge-cases/README.md:22` |
| P2 | `validation/2026-09-19-task-002-lifecycle-precedence/README.md:36` |
| P2 | `validation/2026-09-19-task-003a-e4-model-schema/README.md:35` |
| P2 | `validation/2026-09-19-task-003b-e4-property-expansion/README.md:34` |
| P2 | `validation/2026-09-21-task-003c1-evidence-gates/README.md:39` |
| P2 | `validation/2026-09-23-cp-boundary-003/README.md:19` |
| P2 | `validation/2026-09-25-task-004-perf-measurement/README.md:38` |
| P2 | `validation/2026-09-26-prod-readiness-infra/README.md:37` |
| P2 | `validation/2026-09-28-main-state-catchup/README.md:70` |
| P2 | `validation/2026-10-05-k1-e4-residual-review/README.md:103` |
| P2 | `validation/2026-10-08-ai-delegation-contract-mock/README.md:22` |
| P2 | `validation/2026-10-08-k1-adapter-event-identity/README.md:47` |
| P2 | `validation/2026-10-08-k1-evidence-close/README.md:18,116` |
| P2 | `validation/2026-10-09-audit2-gate-browser-access-test-determinism/README.md:52,127` |
| P2 | `validation/2026-10-09-audit3-openapi-promotion-owner-decision-record/README.md:30,61` |
| P2 | `validation/2026-10-09-audit3-tl-docs-plan-index-sync/README.md:29,55` |
| P2 | `validation/2026-10-09-audit4-audit4-plan-s5-index-f04-criteria-toss-p/README.md:30,64` |
| P2 | `validation/2026-10-09-audit4-tl-plan-index-register-sync/README.md:30,59` |
| P2 | `validation/2026-10-09-ci-wire-token-reward-suite/README.md:33` |
| P2 | `validation/2026-10-09-f04-real-funds-lift-criteria/README.md:19,51` |
| P2 | `validation/2026-10-09-k-a-integration-decision/README.md:20,53` |
| P2 | `validation/2026-10-09-k-a-reestimate/README.md:16,75` |
| P2 | `validation/2026-10-09-k-stage4-adoption-decision/README.md:19,40` |
| P2 | `validation/2026-10-09-k2-retention-proposal/README.md:21,42` |
| P2 | `validation/2026-10-09-openapi-catalogue-promotion/README.md:30` |
| P2 | `validation/2026-10-09-tl-4-token-layer-verification/README.md:44,69` |
| P2 | `validation/2026-10-09-tl-5-decision/README.md:20,54` |
| P2 | `validation/2026-10-09-toss-sandbox-conformance-plan/README.md:20,58` |
| P2 | `validation/2026-10-12-register-nontl-rows-sync/README.md:37,101` |
| P2 | `validation/2026-10-12-rs0-review-pack/README.md:41,108` |
| P2 | `validation/2026-10-13-astra-decision-sheets-listvalues-v5-rs0/README.md:35,90` |
| P2 | `validation/2026-10-13-audit5-docs-index-check-ci-wire/README.md:45,135` |
| P2 | `validation/2026-10-13-audit5-plan-index-sync-b/README.md:49,161` |
| P2 | `validation/2026-10-13-audit5-source-map-checker-decouple/README.md:45,135` |
| P2 | `validation/2026-10-13-docs-index-coverage-check/README.md:45,140` |
| P2 | `validation/2026-10-13-i12-review-pack/README.md:42,116` |
| P2 | `validation/2026-10-13-k-stage2-v5-impl/README.md:31,158` |
| P2 | `validation/2026-10-13-offline-doc-checks-ci/README.md:42,122` |
| P2 | `validation/2026-10-14-audit6-plan-index-sync/README.md:37,169` |
| P2 | `validation/2026-10-14-register-sync-v5-rs/README.md:37,132` |
| P2 | `validation/2026-10-14-rs-1-issuercap-probe/README.md:90` |
| P2 | `validation/2026-10-14-rs-1-public-path/README.md:76` |
| P2 | `validation/2026-10-14-rs-2-private-path/README.md:62` |
| P2 | `validation/2026-10-14-rs-3a-delegation-primitives/README.md:92` |
| P2 | `validation/2026-10-14-rs-3b-delegated-exec/README.md:88` |
| P2 | `validation/2026-10-14-rs-profile-revision-log-0-2/README.md:44,118` |
| P2 | `validation/2026-10-14-rs1-state-answer-archive/README.md:56` |
| P2 | `validation/2026-10-15-docs-index-check-validation-records/README.md:43,150,161` |
| P2 | `validation/2026-10-15-rs-4-l1-load/README.md:142` |
| P2 | `validation/2026-10-16-ai-delegation-execution-decision/README.md:20,47` |
| P2 | `validation/2026-10-16-audit7-docs-index-allowlist-prune/README.md:22` |
| P2 | `validation/2026-10-16-audit7-plan-register-index-sync-20261016b/README.md:22` |
| P2 | `validation/2026-10-16-ci-wire-i12-proof-ids-check/README.md:29` |
| P2 | `validation/2026-10-16-delegation-layer-gap-matrix/README.md:15` |
| P2 | `validation/2026-10-16-feature-ir-plan-limit-edge-tests/README.md:21` |
| P2 | `validation/2026-10-16-plan-register-index-sync-20261016/README.md:23` |
| P2 | `validation/2026-10-16-rs-predicate-evidence-map/README.md:15,89` |
| P2 | `validation/2026-10-16-settlement-seeded-property-suite/README.md:15` |
| P2 | `validation/2026-10-16-testnet-key-management-decision/README.md:20,51` |
| P2 | `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md:15,100` |
| P2 | `validation/2026-10-17-audit8-plan-register-index-sync-20261017/README.md:22` |
| P2 | `validation/2026-10-17-booking-resale-admission-seeded-property/README.md:24,102` |
| P2 | `validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md:19` |
| P2 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:15` |
| P2 | `validation/2026-10-17-delegated-exec-seeded-differential/README.md:15` |
| P2 | `validation/2026-10-17-feature-semantics-v1-edge-fixtures/README.md:21` |
| P2 | `validation/2026-10-17-readiness-journal-byte-sweep/README.md:22` |
| P2 | `validation/2026-10-17-rs-im-evidence-map/README.md:15,95` |
| P2 | `validation/2026-10-18-audit8-loop-node-canonical-crosswalk/README.md:20` |
| P2 | `validation/2026-10-18-audit8-readiness-conformance-sweep-limit-note/README.md:18` |
| P2 | `validation/2026-10-18-audit8-rs-map-rs-c01-issuercap-open-cell/README.md:19` |
| P2 | `validation/2026-10-18-contract-error-code-coverage/README.md:14` |
| P2 | `validation/2026-10-18-readiness-crash-point-sweep/README.md:13` |
| P2 | `validation/2026-10-19-bra-fsm-error-code-coverage/README.md:14` |
| P2 | `validation/2026-10-19-rs-model-gap-closure/README.md:15,76` |
| P2 | `validation/2026-10-19-tl-predicate-evidence-map/README.md:15,80` |
| P2 | `validation/2026-10-19-v5-lifecycle-seeded-model-test/README.md:23` |
| P2 | `validation/2026-10-20-adapter-identity-evidence-map/README.md:16,78` |
| P2 | `validation/2026-10-20-ai-delegation-wrap-conformance/README.md:30` |
| P2 | `validation/2026-10-20-plan-register-index-sync-20261020/README.md:23` |
| P2 | `validation/2026-10-20-plan-rs-grant-cut-order-tests/README.md:15,67` |
| P2 | `validation/2026-10-20-read-model-contract-fixture-prep/README.md:29,104` |
| P2 | `validation/2026-10-20-stage5-preflight/README.md:113,122` |
| P2 | `validation/2026-10-20-token-reward-readiness-wrap/README.md:13` |
| P2 | `validation/2026-10-20-token-reward-rejection-atomicity/README.md:13` |
| P2 | `validation/2026-10-20-v5-transition-evidence-map/README.md:16,69` |
| P2 | `validation/2026-10-21-astra-decision-sheets-rs-stage5/README.md:43,105` |
| P2 | `validation/2026-10-21-kix-types-boundary-fixtures/README.md:26` |
| P2 | `validation/2026-10-21-plan-register-index-sync-20261021/README.md:25` |
| P2 | `validation/2026-10-21-plan-rs-manifest-offline-regressions/README.md:85` |
| P2 | `validation/2026-10-21-plan-rs-ptau-header-tests/README.md:78` |
| P2 | `validation/2026-10-21-plan-rs-spend-witness-offline-tests/README.md:92` |
| P2 | `validation/2026-10-21-plan-rs-witness-ci-wiring/README.md:45` |
| P2 | `validation/2026-10-21-plan-rs-witness-offline-regressions/README.md:22` |
| P2 | `validation/2026-10-21-plan-rs-zk-encoding-regressions/README.md:73` |
| P2 | `validation/2026-10-21-readiness-checker-partial-fixture/README.md:135` |
| P2 | `validation/2026-10-21-readiness-runtime-evidence-map/README.md:16,84` |
| P2 | `validation/2026-10-21-reward-wrap-conformance/README.md:30` |
| P2 | `validation/2026-10-21-settlement-multi-payee-refund-corpus/README.md:15` |
| P2 | `validation/2026-10-21-v5-evidence-citation-guard/README.md:151` |
| P2 | `validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md:43,173` |
| P2 | `validation/2026-10-22-open-user-decisions-ledger/README.md:42,149` |
| P2 | `validation/2026-10-22-plan-register-index-sync-20261022/README.md:26` |
| P2 | `validation/2026-10-22-plan-rs-admission-packet-offline-tests/README.md:189` |
| P2 | `validation/2026-10-22-plan-rs-mint-wrapper-offline-tests/README.md:162` |
| P2 | `validation/2026-10-22-plan-rs-offline-test-entrypoint/README.md:143` |
| P2 | `validation/2026-10-22-plan-rs-verifier-binding-offline-tests/README.md:139` |
| P2 | `validation/2026-10-22-rs-offline-suite-evidence-sync/README.md:172` |
| P2 | `validation/2026-10-22-rs4-load-host-conditions-recorder/README.md:142` |
| P2 | `validation/2026-10-23-audit14-loop-node-crosswalk-refresh/README.md:176,425` |
| P2 | `validation/2026-10-23-audit14-open-decisions-closure/README.md:56` |
| P2 | `validation/2026-10-23-audit14-plan-register-index-sync/README.md:30` |
| P2 | `validation/2026-10-23-bra-section9-error-code-coverage/README.md:132` |
| P2 | `validation/2026-10-23-fsm-returned-data-isolation/README.md:156` |
| P2 | `validation/2026-10-23-owner-stop-handoff-addendum/README.md:192` |
| P2 | `validation/2026-10-23-plan-readiness-migration-edge-tests/README.md:136` |
| P2 | `validation/2026-10-23-plan-register-index-sync-20261023/README.md:33` |
| P2 | `validation/2026-10-23-plan-rs-summary-arithmetic-tests/README.md:170` |
| P2 | `validation/2026-10-23-readiness-receipt-audit-tests/README.md:22,271` |
| P2 | `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md:139,169,249,293` |
| P2 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md:15` |
| P2 | `validation/2026-10-24-bra-aid-returned-data-isolation/README.md:174` |
| P2 | `validation/2026-10-24-plan-register-index-sync/README.md:79` |
| P2 | `validation/2026-10-24-resale-admission-rejection-atomicity/README.md:24` |
| P2 | `validation/2026-10-24-reward-snapshot-isolation/README.md:187,326` |
| P2 | `validation/2026-10-25-aid-rejection-atomicity/README.md:231` |
| P2 | `validation/2026-10-25-audit15-open-decisions-closure/README.md:35` |
| P2 | `validation/2026-10-25-audit15-reference-test-sibling-path-guard/README.md:32` |
| P2 | `validation/2026-10-25-bra-contract-clause-evidence-map/README.md:135,222` |
| P2 | `validation/2026-10-25-ci-wire-product-contract-evidence-checkers/README.md:46` |
| P2 | `validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md:70,172` |
| P2 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:232` |
| P2 | `validation/2026-10-25-plan-primary-price-fee-contract-clause-eviden/README.md:144,187` |
| P2 | `validation/2026-10-25-plan-register-index-crosswalk-sync/README.md:107,189` |
| P2 | `validation/2026-10-25-plan-register-index-sync-20261025/README.md:111` |
| P2 | `validation/2026-10-25-plan-section5-quote-completeness/README.md:340` |
| P2 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:217` |
| P2 | `validation/2026-10-25-restore-fingerprint-equivalence/README.md:199` |
| P2 | `validation/2026-10-25-settlement-contract-clause-evidence-map/README.md:142` |
| P2 | `validation/2026-10-26-plan-ai-delegation-contract-clause-evidence-m/README.md:158` |
| P2 | `validation/2026-10-26-plan-bcs1-contract-clause-evidence-map/README.md:41` |
| P2 | `validation/2026-10-26-plan-ci-checker-wiring-guard/README.md:36` |
| P2 | `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md:26` |
| P2 | `validation/2026-10-26-plan-contract-invariants-inv3-sensitivity/README.md:33,145` |
| P2 | `validation/2026-10-26-plan-evidence-map-rollup-check/README.md:85` |
| P2 | `validation/2026-10-26-plan-feature-ir-money-profile-precedence-tests/README.md:128` |
| P2 | `validation/2026-10-26-plan-feature-ir-validator-matrix-closure/README.md:147` |
| P2 | `validation/2026-10-26-plan-feature-semantics-v1-evidence-map/README.md:28` |
| P2 | `validation/2026-10-26-plan-integration-gate-contract-clause-ev/README.md:19` |
| P2 | `validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md:47,162` |
| P2 | `validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:116,217` |
| P2 | `validation/2026-10-26-plan-lifecycle-adr-clause-evidence-map/README.md:24` |
| P2 | `validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md:46,520,560` |
| P2 | `validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md:139,1198,1233,1674,1689` |
| P2 | `validation/2026-10-26-plan-open-decisions-addendum-bcs1-checke/README.md:207,221` |
| P2 | `validation/2026-10-26-plan-perf-harness-map-partial-closure/README.md:19,189,330` |
| P2 | `validation/2026-10-26-plan-performance-measurement-clause-evid/README.md:43` |
| P2 | `validation/2026-10-26-plan-primary-fee-pf-c05-isolation-tests/README.md:97` |
| P2 | `validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md:483,714,745,774,881` |
| P2 | `validation/2026-10-26-plan-toss-card-profile-evidence-map/README.md:26` |
| P2 | `validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md:36` |
| P2 | `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:24` |
| P2 | `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:24` |
| P2 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:27` |
| P2 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:66,317,330,3043,3056` |
| P2 | `validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md:18` |
| P2 | `validation/2026-10-27-plan-perf-harness-map-json-csv-closure-2/README.md:19` |
| P2 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md:21` |
| P3 | `docs/tasks/TASK_003C1_EVIDENCE_GATES.md:22` |
| P3 | `docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:66` |
| P3 | `runtime/crates/kix-kernel/examples/r1_perf_probe.rs:10` |
| P3 | `runtime/crates/kix-kernel/tests/performance_harness.rs:194,213` |
| P3 | `validation/2026-09-18-contract-edge-cases/README.md:29` |
| P3 | `validation/2026-09-21-task-003c1-evidence-gates/README.md:40` |
| P3 | `validation/2026-09-25-task-004-perf-measurement/README.md:39` |
| P4 | `docs/tasks/TASK_003C1_EVIDENCE_GATES.md:23` |
| P4 | `docs/tasks/TASK_004_PERFORMANCE_MEASUREMENT.md:67` |
| P4 | `runtime/crates/kix-kernel/examples/r1_perf_probe.rs:11` |
| P4 | `runtime/crates/kix-kernel/tests/performance_harness.rs:195,214` |
| P4 | `validation/2026-09-21-task-003c1-evidence-gates/README.md:41` |
| P4 | `validation/2026-09-25-task-004-perf-measurement/README.md:40` |
| P5 | `docs/contracts/openapi/README.md:30` |
| P5 | `scripts/check_sdk_client.py:31` |
| P5 | `validation/2026-09-26-prod-readiness-infra/README.md:29` |
| P5 | `validation/2026-09-28-main-state-catchup/README.md:46` |
| P5 | `validation/2026-10-09-audit3-openapi-promotion-owner-decision-record/README.md:25,63` |
| P5 | `validation/2026-10-09-audit4-audit4-plan-s5-index-f04-criteria-toss-p/README.md:75` |
| P5 | `validation/2026-10-09-audit4-tl-plan-index-register-sync/README.md:69` |
| P5 | `validation/2026-10-09-ci-wire-token-reward-suite/README.md:34` |
| P5 | `validation/2026-10-09-f04-real-funds-lift-criteria/README.md:57` |
| P5 | `validation/2026-10-09-k-a-integration-decision/README.md:65` |
| P5 | `validation/2026-10-09-k-stage4-adoption-decision/README.md:45` |
| P5 | `validation/2026-10-09-k2-retention-proposal/README.md:46` |
| P5 | `validation/2026-10-09-openapi-catalogue-promotion/README.md:31` |
| P5 | `validation/2026-10-09-tl-5-decision/README.md:68` |
| P5 | `validation/2026-10-12-register-nontl-rows-sync/README.md:90` |
| P5 | `validation/2026-10-12-rs0-review-pack/README.md:95` |
| P5 | `validation/2026-10-13-audit5-docs-index-check-ci-wire/README.md:124` |
| P5 | `validation/2026-10-13-audit5-source-map-checker-decouple/README.md:125` |
| P5 | `validation/2026-10-13-docs-index-coverage-check/README.md:129` |
| P5 | `validation/2026-10-13-i12-review-pack/README.md:105` |
| P5 | `validation/2026-10-13-offline-doc-checks-ci/README.md:111` |
| P5 | `validation/2026-10-24-bra-aid-returned-data-isolation/README.md:146` |
| P5 | `validation/2026-10-24-resale-admission-rejection-atomicity/README.md:419` |
| P5 | `validation/2026-10-24-reward-snapshot-isolation/README.md:161,318` |
| P5 | `validation/2026-10-25-aid-rejection-atomicity/README.md:201` |
| P5 | `validation/2026-10-25-audit15-reference-test-sibling-path-guard/README.md:85` |
| P5 | `validation/2026-10-25-bra-contract-clause-evidence-map/README.md:104` |
| P5 | `validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md:108` |
| P5 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:130` |
| P5 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:191` |
| P5 | `validation/2026-10-25-settlement-contract-clause-evidence-map/README.md:85` |
| P5 | `validation/2026-10-26-plan-ai-delegation-contract-clause-evidence-m/README.md:138` |
| P5 | `validation/2026-10-26-plan-ci-checker-wiring-guard/README.md:164` |
| P5 | `validation/2026-10-26-plan-integration-gate-contract-clause-ev/README.md:82` |
| P5 | `validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md:49,122` |
| P5 | `validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:143` |
| P5 | `validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md:192` |
| A | `docs/contracts/CONTRACT_INVARIANTS.md:32` |
| A | `docs/contracts/STATE_LIFECYCLE.md:34` |
| A | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:84` |
| A | `docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:9` |
| L | `docs/contracts/CONTRACT_INVARIANTS.md:33` |
| L | `docs/contracts/STATE_LIFECYCLE.md:595` |
| L | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:84` |
| L | `docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:9` |
| L | `validation/2026-09-19-task-002-lifecycle-precedence/README.md:79` |
| R | `docs/contracts/CONTRACT_INVARIANTS.md:34` |
| R | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:84` |

## Non-claims and remaining uncertainty

This builder record does not resolve, resume, retry, retire, complete or accept
any node; it changes no owner, evidence grade, map status or policy value.
The attributed A5/SD1 class C stops are not rerun or newly discovered here.
PERF-PROBE is an observed apparatus refusal/decision boundary; F-B1 remains
historical class B drift. No contract semantics are invented. Canonical counting
remains `DECISION_REQUIRED · Astra`; the RS-4 load/workload, missing-grant binding
and SDK extension-profile uncertainties retain their recorded owners.

No pin, example, test, checker, contract, CI, program or task input is edited.
The two AGENTS locks, `reference/v0.3-rc1/**` and `.aiops/` are preserved byte for
byte. No release probe, Rust workload, host provisioning, paid service, secret,
PG/bank/KYC call, public endpoint, Sui testnet/mainnet, real fund, storage engine,
R2, replication/consensus, coin/TIX module or production runtime is used.
No TPS, latency, failure-rate, durability, distributed fencing, bank exactly-once,
chain finality, legal compliance or production-readiness claim follows.

Remote freshness and final-head hosted CI are unverified. Local document checks
are builder evidence, not non-author exact-HEAD review, an A2/Astra audit, merge
readiness or an owner decision. The User's choice and separately scoped follow-up
remain outstanding; this node is only a documentary handoff.
