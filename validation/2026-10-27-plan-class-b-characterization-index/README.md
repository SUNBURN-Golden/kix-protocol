# plan-plan-class-b-characterization-index — class B characterization index

Node: `plan-plan-class-b-characterization-index` (loop-proposed node, not in `.aiops/program.json`;
no task issue). Not an ASTRA program-mode session. Builder-authored record. It is not a review,
decision, classification or recommendation.

Adds [`docs/status/CLASS_B_CHARACTERIZATION_INDEX.md`](../../docs/status/CLASS_B_CHARACTERIZATION_INDEX.md),
an index of the class B (contract-undefined, AGENTS.md §8 B) characterizations recorded on `main` in
`validation/*/README.md` and `docs/status/*EVIDENCE_MAP*.md`, and
[`scripts/check_class_b_index.py`](../../scripts/check_class_b_index.py), a stdlib citation checker wired
plain and `--self-test` into the `Stdlib offline document checks` step.

## AGENTS §14 fields

| Field | Value |
|---|---|
| Task | node `plan-plan-class-b-characterization-index`; task input is the session node text (no `docs/tasks/` document for this node) |
| Observed `origin/main` / base | `b7d0fe551d3ebfab9c94c4bbd3ffee544596d42b` (branch HEAD equal to it at session start) |
| Implementation head / final head / merge commit | Not committed by the builder; the supervisor commits. Exact-head CI goes in the PR closure report (AGENTS §11). |
| Changed paths | `docs/status/CLASS_B_CHARACTERIZATION_INDEX.md` (new), `scripts/check_class_b_index.py` (new), `.github/workflows/protocol.yml` (two lines), `docs/README.md` (one bullet), `validation/2026-10-27-plan-class-b-characterization-index/README.md` (new) |
| Locked blobs | `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`, before and after |
| Contract violations found | None established by this node. Nothing was classified (see remaining uncertainty) |
| Contract-undefined characterizations found | None new. The index lists the existing ones |
| Exact-head KTX / KIX CI | Not available to the builder; record in the PR closure report |

## Existing coverage mapping

| Requirement | Before this node | After |
|---|---|---|
| One list of class B characterizations across records and maps | Not covered. Each evidence map lists its own class B notes. Validation records keep theirs. `CONTRACT_ERROR_CODE_COVERAGE.md` has a `CLASS_B` count for error-code rows only (0) | Index, 216 rows |
| Citation check of quotes, tests, owners and contracts for those items | Partially covered. Per-map checkers check their own rows and test symbols. No checker reads validation-record class B text | `check_class_b_index.py` |
| CI wiring | Not applicable before | Two lines in `protocol.yml`; `check_ci_checker_wiring.py` passes |

## Search used

Run from the repository root on the base tree, before this record existed (so the record does not
find itself):

```
grep -nEi '\bclass[ _-]?b\b|\bcontract[ -]undefined\b' validation/*/README.md docs/status/*EVIDENCE_MAP*.md
grep -nE '\|[[:space:]]*B[[:space:]]*\|' validation/*/README.md docs/status/*EVIDENCE_MAP*.md
```

The first command gave 333 lines and the second gave 25. No line is in both, so there are 358 hit lines
in 152 files. The second pattern catches the `Class` = `B` table cells that carry no "class B" words
(for example the #278 clock-skew row). The 69 hit lines that contain the `CLASS_B` checker token
were excluded as Counts vocabulary.

The other 289 lines were read in context: the heading or lead-in, and the items under it.
Characterizations are often the list items or table rows below a hit heading, and those items do not
contain the search words themselves. Six parallel builder sub-reads extracted candidate units.
The builder merged them, removed restatements and checked every quote, symbol, owner and contract
with the checker. Of the 358 hit lines, 58 are indexed rows and 300 are excluded with a reason.

Row rules (indexing only, never classifying):

- A row exists only where the source itself labels a specific observation class B or contract undefined.
  It uses the source's own unit: a list item, an `F-B*` finding, a numbered item, or a table row with a
  `B` class cell.
- One row per characterization. The source is the record that first labels it, and the owner and
  contract cells are copied only from that source. A later record or map that restates the same item gets
  no row. Those units are listed under "Restatements not indexed" below.
- Exception: the CONTRACT_INVARIANTS `F-B1`…`F-B6` findings cite the evidence map that defines those ids.
  The per-branch `B:` cells of the F-B3 reply-assertion record and the F-B5 and F-B6 sub-items of the S5
  records are treated as detail of those findings.
- In `validation/2026-10-25-restore-fingerprint-equivalence/README.md`, table rows that share one class
  cell were grouped under that cell's text, because the field-name cells repeat across tables and would
  not identify a row. The groups are Resale §10.7, Admission §11.5, Reward `prior_record` and the other
  Reward fields. The Reservation and AI rows keep one row each.
- Contract-undefined open items in decision records ("Contract-undefined items, left open in the
  proposal §N") are indexed as the record labels them. An item repeated word for word in a later
  decision record is a restatement.
- `superseded` is used only where a later merged record says so in its own words. No such statement was
  found, so `superseded=0`. Two near-statements were seen and left as `none`, because neither says
  "superseded":
  - `validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md:92` says the admission
    live-versus-restored divergence (CB-086) is "removed by the same change".
  - `validation/2026-10-05-k1-e4-residual-review/README.md:84` says an earlier ReturnRequired/review
    uncertainty "is resolved by current 0.6 §5.7.1". This concerns the state-lifecycle text, not a row
    in this index.

## Hit table

Disposition is the `CB-NNN` row the hit line carries, or `excluded:` with the reason. Line numbers are on
the base tree.

| # | path:line | Disposition |
|---|---|---|
| 1 | `docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md:47` | excluded: source marks as existing/restated ("Existing Class B characterization accepts INVALID_ID or EXECUTE_AUTHORITY_DISABLED") |
| 2 | `docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md:138` | excluded: source marks as existing/restated ("The existing Class B cases characterize malformed authority-list code") |
| 3 | `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md:30` | excluded: restates CB-001 in same file (FU-ZERO-ID gap cell) |
| 4 | `docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md:87` | excluded: heading/lead-in for CB-001..CB-004 |
| 5 | `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md:101` | excluded: restates CB-178 (§11.2 gap cell "recorded class B") |
| 6 | `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md:149` | excluded: heading/lead-in; its items are indexed as CB-171, CB-172, CB-173, CB-174, CB-178, CB-179, CB-185, CB-186, CB-187 |
| 7 | `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md:164` | excluded: continuation of an item indexed as CB-185..CB-187 |
| 8 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:15` | excluded: restates CB-009 in same file (F-B5 pointer) |
| 9 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:17` | excluded: restates CB-010 in same file (F-B6 pointer) |
| 10 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:51` | excluded: restates CB-007 in same file (S4-PROBES gap cell, "F-B3 narrowed"; names validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md) |
| 11 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:57` | excluded: restates CB-009 in same file (S5-SAFE-REJECT gap cell, F-B5) |
| 12 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:58` | excluded: restates CB-010 in same file (S5-PRECEDENCE gap cell, F-B6) |
| 13 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:84` | CB-005 |
| 14 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:85` | CB-006 |
| 15 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:86` | CB-007 |
| 16 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:87` | CB-008 |
| 17 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:88` | CB-009 |
| 18 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:89` | CB-010 |
| 19 | `docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md:95` | excluded: restates CB-010 in same file (non-claim "class B pairs are not fixed") |
| 20 | `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md:103` | excluded: source marks as existing/restated ("The following pre-existing class B observations remain characterizations") |
| 21 | `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md:115` | excluded: source marks as existing/restated ("is already labeled class B") |
| 22 | `docs/status/EVIDENCE_MAP_ROLLUP.md:59` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 23 | `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:44` | excluded: restates CB-194 (S6-EXPORT-BOUNDARY gap cell) |
| 24 | `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:64` | excluded: restates CB-065 (S10-LIMITS gap cell, root-at-zero depth) |
| 25 | `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:77` | excluded: heading/lead-in; its items are indexed as CB-065, CB-099, CB-100, CB-101, CB-194 |
| 26 | `docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:89` | excluded: source marks as existing/restated ("existing three class-B recovery uncertainties"); points to docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md |
| 27 | `docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md:39` | CB-011 |
| 28 | `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:90` | excluded: heading/lead-in; its items are indexed as CB-012, CB-013, CB-014, CB-196, CB-197, CB-198, CB-199, CB-200, CB-205, CB-206, CB-207, CB-208, CB-209, CB-210 |
| 29 | `docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md:85` | excluded: absence statement ("No new class B behavior is characterized"; also "Existing contract-undefined provider inputs ... remain open in the rows above") |
| 30 | `docs/status/PRIMARY_PRICE_FEE_CONTRACT_EVIDENCE_MAP.md:115` | excluded: continuation of an item indexed as CB-201 |
| 31 | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:27` | excluded: restates CB-102, CB-104, CB-105 (status vocabulary) |
| 32 | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:62` | excluded: restates CB-102 |
| 33 | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:63` | excluded: restates CB-104 |
| 34 | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:64` | excluded: restates CB-105 |
| 35 | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:78` | excluded: restates CB-102, CB-104, CB-105 (OPEN summary) |
| 36 | `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:84` | excluded: restates CB-102, CB-104, CB-105 (non-claim) |
| 37 | `docs/status/RS_IM_EVIDENCE_MAP.md:29` | excluded: source marks as existing/restated ("which the record lists as a class B item"; owner-cell convention, no specific observation) |
| 38 | `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md:87` | excluded: source marks as existing/restated ("Existing class B zero-cash-commit characterization"); line 97 names the seeded property record §7(iii) |
| 39 | `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md:107` | excluded: continuation of an item indexed as CB-163 |
| 40 | `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md:109` | excluded: source marks as existing/restated ("remain class B characterizations") |
| 41 | `validation/2026-09-19-task-002-lifecycle-precedence/README.md:92` | excluded: continuation line of CB-015 |
| 42 | `validation/2026-09-19-task-003a-e4-model-schema/README.md:149` | excluded: absence statement |
| 43 | `validation/2026-09-19-task-003b-e4-property-expansion/README.md:141` | excluded: absence statement ("No contract-undefined behaviour needed a new characterization beyond what 003-A already documents") |
| 44 | `validation/2026-09-26-wave2-rights-issuance/README.md:24` | excluded: heading/lead-in for CB-016 |
| 45 | `validation/2026-10-05-k1-e4-residual-review/README.md:87` | excluded: absence statement ("No ... new contract-undefined behavior was identified") |
| 46 | `validation/2026-10-08-k1-evidence-close/README.md:172` | excluded: source marks as existing/restated ("Contract-undefined items already recorded elsewhere, left open") |
| 47 | `validation/2026-10-09-audit2-gate-browser-access-test-determinism/README.md:164` | excluded: heading/lead-in for CB-017 |
| 48 | `validation/2026-10-09-audit3-openapi-promotion-owner-decision-record/README.md:97` | CB-018 |
| 49 | `validation/2026-10-09-ci-wire-token-reward-suite/README.md:89` | excluded: absence statement |
| 50 | `validation/2026-10-09-k-a-integration-decision/README.md:95` | excluded: heading/lead-in; its items are indexed as CB-019..CB-021 |
| 51 | `validation/2026-10-09-k-a-reestimate/README.md:155` | excluded: heading/lead-in for CB-020..CB-022 |
| 52 | `validation/2026-10-09-tl-5-decision/README.md:97` | excluded: heading/lead-in for CB-023..CB-027 |
| 53 | `validation/2026-10-13-audit5-docs-index-check-ci-wire/README.md:165` | excluded: absence statement |
| 54 | `validation/2026-10-13-audit5-source-map-checker-decouple/README.md:163` | excluded: absence statement |
| 55 | `validation/2026-10-13-offline-doc-checks-ci/README.md:150` | excluded: absence statement |
| 56 | `validation/2026-10-14-audit6-plan-index-sync/README.md:199` | excluded: absence statement |
| 57 | `validation/2026-10-14-rs-1-issuercap-probe/README.md:142` | excluded: heading/lead-in with no rows (its items are a class C absence statement and a restated class B item) |
| 58 | `validation/2026-10-14-rs-1-issuercap-probe/README.md:146` | excluded: source marks as existing/restated ("already recorded by RS-0/RS-1, restated for this node's evidence"); RS-0/RS-1 records |
| 59 | `validation/2026-10-14-rs-1-public-path/README.md:110` | excluded: coverage-map table row pointing to the contract-undefined notes (CB-028..CB-031) |
| 60 | `validation/2026-10-14-rs-1-public-path/README.md:113` | excluded: heading/lead-in for CB-028..CB-031 |
| 61 | `validation/2026-10-14-rs-1-public-path/README.md:228` | excluded: restates CB-031 in same file |
| 62 | `validation/2026-10-14-rs-2-private-path/README.md:173` | excluded: heading/lead-in for CB-032..CB-040 |
| 63 | `validation/2026-10-14-rs-3a-delegation-primitives/README.md:151` | excluded: heading/lead-in for CB-041..CB-047 |
| 64 | `validation/2026-10-14-rs-3b-delegated-exec/README.md:151` | excluded: heading/lead-in for CB-048..CB-055 |
| 65 | `validation/2026-10-14-rs1-state-answer-archive/README.md:139` | excluded: absence statement |
| 66 | `validation/2026-10-15-docs-index-check-validation-records/README.md:189` | excluded: absence statement |
| 67 | `validation/2026-10-15-rs-4-l1-load/README.md:185` | excluded: heading/lead-in for CB-056..CB-059 |
| 68 | `validation/2026-10-16-ai-delegation-execution-decision/README.md:94` | excluded: heading/lead-in for CB-060..CB-064 |
| 69 | `validation/2026-10-16-audit7-docs-index-allowlist-prune/README.md:100` | excluded: absence statement |
| 70 | `validation/2026-10-16-audit7-plan-register-index-sync-20261016b/README.md:75` | excluded: restates CB-065 |
| 71 | `validation/2026-10-16-ci-wire-i12-proof-ids-check/README.md:97` | excluded: absence statement |
| 72 | `validation/2026-10-16-feature-ir-plan-limit-edge-tests/README.md:57` | excluded: heading/lead-in for CB-065..CB-067 |
| 73 | `validation/2026-10-16-feature-ir-plan-limit-edge-tests/README.md:91` | excluded: restates CB-065 in same file |
| 74 | `validation/2026-10-16-plan-register-index-sync-20261016/README.md:121` | CB-068 |
| 75 | `validation/2026-10-16-rs-predicate-evidence-map/README.md:71` | excluded: heading/lead-in; its items are indexed as CB-028, CB-039, CB-069, CB-070, CB-071, CB-072, CB-073, CB-074 |
| 76 | `validation/2026-10-16-settlement-seeded-property-suite/README.md:21` | excluded: restates CB-076 in same file |
| 77 | `validation/2026-10-16-settlement-seeded-property-suite/README.md:64` | CB-075 |
| 78 | `validation/2026-10-16-settlement-seeded-property-suite/README.md:65` | CB-076 |
| 79 | `validation/2026-10-16-testnet-key-management-decision/README.md:99` | excluded: heading/lead-in; its items are indexed as CB-023, CB-024, CB-078, CB-079, CB-080 |
| 80 | `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md:67` | CB-081 |
| 81 | `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md:68` | CB-082 |
| 82 | `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md:69` | CB-083 |
| 83 | `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md:70` | CB-084 |
| 84 | `validation/2026-10-17-ai-delegation-seeded-property-suite/README.md:71` | CB-085 |
| 85 | `validation/2026-10-17-audit8-plan-register-index-sync-20261017/README.md:71` | excluded: absence statement |
| 86 | `validation/2026-10-17-audit8-plan-register-index-sync-20261017/README.md:79` | excluded: source marks as existing/restated ("its class B observations stay in that record"); #205 |
| 87 | `validation/2026-10-17-booking-resale-admission-seeded-property/README.md:76` | CB-086 |
| 88 | `validation/2026-10-17-booking-resale-admission-seeded-property/README.md:82` | excluded: heading/lead-in for CB-087..CB-089 |
| 89 | `validation/2026-10-17-booking-resale-admission-seeded-property/README.md:88` | excluded: source classifies these replay distinctions as class A ("not new class B semantics") |
| 90 | `validation/2026-10-17-booking-resale-admission-seeded-property/README.md:170` | excluded: restates CB-086..CB-089 in same file ("The existing class B uncertainties and all MOCK non-claims remain") |
| 91 | `validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md:92` | excluded: restates CB-086 |
| 92 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:22` | excluded: restates CB-094 in same file |
| 93 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:73` | CB-090 |
| 94 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:74` | CB-091 |
| 95 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:75` | CB-092 |
| 96 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:76` | CB-093 |
| 97 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:77` | CB-094 |
| 98 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:78` | CB-095 |
| 99 | `validation/2026-10-17-credit-f04-seeded-property-suite/README.md:84` | excluded: generic mention, no specific observation (test count "3 class B") |
| 100 | `validation/2026-10-17-delegated-exec-seeded-differential/README.md:50` | CB-096 |
| 101 | `validation/2026-10-17-feature-semantics-v1-edge-fixtures/README.md:36` | excluded: restates CB-099 in same file (table cell 'class B, see below') |
| 102 | `validation/2026-10-17-feature-semantics-v1-edge-fixtures/README.md:64` | excluded: heading/lead-in for CB-099..CB-101 |
| 103 | `validation/2026-10-17-readiness-journal-byte-sweep/README.md:66` | excluded: restates CB-104 in same file (outcome-table count of the empty-file reinit) |
| 104 | `validation/2026-10-17-readiness-journal-byte-sweep/README.md:80` | CB-102 |
| 105 | `validation/2026-10-17-readiness-journal-byte-sweep/README.md:81` | CB-103 |
| 106 | `validation/2026-10-17-readiness-journal-byte-sweep/README.md:82` | CB-104 |
| 107 | `validation/2026-10-17-readiness-journal-byte-sweep/README.md:83` | CB-105 |
| 108 | `validation/2026-10-17-readiness-journal-byte-sweep/README.md:84` | CB-106 |
| 109 | `validation/2026-10-17-rs-im-evidence-map/README.md:78` | excluded: heading/lead-in for CB-107..CB-113 |
| 110 | `validation/2026-10-18-audit8-readiness-conformance-sweep-limit-note/README.md:23` | excluded: source marks as existing/restated ("Numbers are copied from the outcome table of `validation/2026-10-17-readiness-journal-byte-sweep/README.md`"; the three observations are the #205 sweep findings) also: validation/2026-10-17-readiness-journal-byte-sweep/README.md, #205 |
| 111 | `validation/2026-10-18-contract-error-code-coverage/README.md:64` | excluded: absence statement (heading followed by "None."; the following characterization is not labelled class B) |
| 112 | `validation/2026-10-18-contract-error-code-coverage/README.md:74` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 113 | `validation/2026-10-18-contract-error-code-coverage/README.md:75` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 114 | `validation/2026-10-18-readiness-crash-point-sweep/README.md:79` | CB-114 |
| 115 | `validation/2026-10-19-bra-fsm-error-code-coverage/README.md:31` | excluded: absence statement (heading followed by "None.") |
| 116 | `validation/2026-10-19-bra-fsm-error-code-coverage/README.md:33` | excluded: absence statement ("None. ... no row needed a contract-undefined fence"; carried-over characterization is from validation/2026-10-18-contract-error-code-coverage/README.md and not labelled class B) |
| 117 | `validation/2026-10-19-bra-fsm-error-code-coverage/README.md:43` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 118 | `validation/2026-10-19-rs-model-gap-closure/README.md:61` | excluded: heading/lead-in for CB-115..CB-119 |
| 119 | `validation/2026-10-19-v5-lifecycle-seeded-model-test/README.md:112` | excluded: absence statement ("No class C ... and no class B ambiguity blocked the node") |
| 120 | `validation/2026-10-19-v5-lifecycle-seeded-model-test/README.md:115` | excluded: source marks as existing/restated ("class-B characterization inherited from that record is restated, not amended") also: the `k-stage2-v5-impl` record |
| 121 | `validation/2026-10-20-adapter-identity-evidence-map/README.md:64` | excluded: heading/lead-in for CB-120..CB-123 |
| 122 | `validation/2026-10-20-ai-delegation-wrap-conformance/README.md:17` | excluded: restates CB-124 in same file (changed-path summary of CONFORMANCE.md) |
| 123 | `validation/2026-10-20-ai-delegation-wrap-conformance/README.md:69` | CB-124 |
| 124 | `validation/2026-10-20-plan-register-index-sync-20261020/README.md:79` | CB-125 |
| 125 | `validation/2026-10-20-plan-rs-grant-cut-order-tests/README.md:54` | excluded: heading/lead-in; its items are indexed as CB-046, CB-126, CB-127 |
| 126 | `validation/2026-10-20-read-model-contract-fixture-prep/README.md:91` | excluded: heading/lead-in for CB-128 |
| 127 | `validation/2026-10-20-token-reward-readiness-wrap/README.md:65` | CB-129 |
| 128 | `validation/2026-10-20-token-reward-rejection-atomicity/README.md:57` | excluded: heading/lead-in for CB-130..CB-134 |
| 129 | `validation/2026-10-20-token-reward-rejection-atomicity/README.md:58` | CB-130 |
| 130 | `validation/2026-10-20-token-reward-rejection-atomicity/README.md:87` | excluded: generic mention, no specific observation ("The class B rows are recorded characterizations, not proposed contract text") |
| 131 | `validation/2026-10-20-v5-transition-evidence-map/README.md:58` | CB-135 |
| 132 | `validation/2026-10-21-kix-types-boundary-fixtures/README.md:36` | excluded: restates CB-136 in same file (table cell 'see class B below') |
| 133 | `validation/2026-10-21-kix-types-boundary-fixtures/README.md:55` | excluded: restates CB-136 in same file (coverage cell '(class B)') |
| 134 | `validation/2026-10-21-kix-types-boundary-fixtures/README.md:65` | excluded: heading/lead-in for CB-136..CB-138 |
| 135 | `validation/2026-10-21-plan-register-index-sync-20261021/README.md:88` | excluded: source marks as existing/restated ("identity remains undecided") also: validation/2026-10-20-plan-register-index-sync-20261020/README.md |
| 136 | `validation/2026-10-21-plan-rs-manifest-offline-regressions/README.md:146` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 137 | `validation/2026-10-21-plan-rs-ptau-header-tests/README.md:170` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 138 | `validation/2026-10-21-plan-rs-ptau-header-tests/README.md:189` | CB-139 |
| 139 | `validation/2026-10-21-plan-rs-spend-witness-offline-tests/README.md:166` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 140 | `validation/2026-10-21-plan-rs-witness-ci-wiring/README.md:124` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 141 | `validation/2026-10-21-plan-rs-witness-ci-wiring/README.md:168` | excluded: source marks as existing/restated ("predecessor's class-B characterization of the broken `test:offline` package script remains unresolved and unchanged") also: validation/2026-10-21-plan-rs-witness-offline-regressions/README.md |
| 142 | `validation/2026-10-21-plan-rs-witness-offline-regressions/README.md:137` | CB-140 |
| 143 | `validation/2026-10-21-plan-rs-zk-encoding-regressions/README.md:167` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 144 | `validation/2026-10-21-plan-rs-zk-encoding-regressions/README.md:185` | CB-141 |
| 145 | `validation/2026-10-21-readiness-checker-partial-fixture/README.md:160` | excluded: absence statement ("No new contract violation or contract-undefined runtime characterization was found"; "The existing three recovery characterizations remain unresolved") also: validation/2026-10-17-readiness-journal-byte-sweep/README.md |
| 146 | `validation/2026-10-21-readiness-runtime-evidence-map/README.md:3` | excluded: source marks as existing/restated ("3 class-B open items" are map rows for the journal byte sweep items) also: validation/2026-10-17-readiness-journal-byte-sweep/README.md |
| 147 | `validation/2026-10-21-readiness-runtime-evidence-map/README.md:22` | excluded: source marks as existing/restated ("The three class-B characterizations ... stay `OPEN` with owner `Astra`") also: validation/2026-10-17-readiness-journal-byte-sweep/README.md |
| 148 | `validation/2026-10-21-readiness-runtime-evidence-map/README.md:62` | excluded: source marks as existing/restated ("Class-B characterizations; classification waits on the pending Astra ruling") also: validation/2026-10-17-readiness-journal-byte-sweep/README.md |
| 149 | `validation/2026-10-21-readiness-runtime-evidence-map/README.md:71` | excluded: heading/lead-in for CB-142, CB-143 |
| 150 | `validation/2026-10-21-readiness-runtime-evidence-map/README.md:73` | excluded: source marks as existing/restated ("The three class-B items from the journal byte sweep stay `OPEN`") also: validation/2026-10-17-readiness-journal-byte-sweep/README.md |
| 151 | `validation/2026-10-21-reward-wrap-conformance/README.md:17` | excluded: restates CB-144 in same file (changed-path description of the class-B replay characterization in readiness/CONFORMANCE.md) |
| 152 | `validation/2026-10-21-reward-wrap-conformance/README.md:72` | CB-144 |
| 153 | `validation/2026-10-21-settlement-multi-payee-refund-corpus/README.md:65` | CB-145 |
| 154 | `validation/2026-10-21-settlement-multi-payee-refund-corpus/README.md:66` | CB-146 |
| 155 | `validation/2026-10-21-settlement-multi-payee-refund-corpus/README.md:67` | CB-147 |
| 156 | `validation/2026-10-21-v5-evidence-citation-guard/README.md:119` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 157 | `validation/2026-10-21-v5-evidence-citation-guard/README.md:167` | excluded: absence statement |
| 158 | `validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md:158` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 159 | `validation/2026-10-22-ci-wire-stage5-host-preflight-selftest/README.md:193` | excluded: absence statement |
| 160 | `validation/2026-10-22-plan-register-index-sync-20261022/README.md:118` | excluded: source marks as existing/restated ("identity remains undecided"); the partial-quote observation in the same bullet is CB-148 |
| 161 | `validation/2026-10-22-plan-rs-admission-packet-offline-tests/README.md:161` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 162 | `validation/2026-10-22-plan-rs-admission-packet-offline-tests/README.md:202` | excluded: absence statement |
| 163 | `validation/2026-10-22-plan-rs-mint-wrapper-offline-tests/README.md:140` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 164 | `validation/2026-10-22-plan-rs-mint-wrapper-offline-tests/README.md:194` | excluded: absence statement |
| 165 | `validation/2026-10-22-plan-rs-offline-test-entrypoint/README.md:166` | excluded: source marks as existing/restated ("The predecessor's class-B broken-entry characterization"); predecessor records: validation/2026-10-21-plan-rs-witness-offline-regressions/README.md and wiring/spend records |
| 166 | `validation/2026-10-22-plan-rs-offline-test-entrypoint/README.md:168` | excluded: absence statement |
| 167 | `validation/2026-10-22-plan-rs-verifier-binding-offline-tests/README.md:122` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 168 | `validation/2026-10-22-plan-rs-verifier-binding-offline-tests/README.md:162` | excluded: heading/lead-in for CB-149..CB-151 |
| 169 | `validation/2026-10-22-rs-offline-suite-evidence-sync/README.md:208` | excluded: absence statement |
| 170 | `validation/2026-10-22-rs4-load-host-conditions-recorder/README.md:103` | excluded: heading/lead-in for CB-152..CB-155 |
| 171 | `validation/2026-10-23-audit14-loop-node-crosswalk-refresh/README.md:223` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 172 | `validation/2026-10-23-audit14-open-decisions-closure/README.md:119` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 173 | `validation/2026-10-23-audit14-open-decisions-closure/README.md:206` | excluded: absence statement |
| 174 | `validation/2026-10-23-audit14-open-decisions-closure/README.md:207` | excluded: source marks as existing/restated ("Historical source records retain their own class B/C findings and limits") |
| 175 | `validation/2026-10-23-audit14-plan-register-index-sync/README.md:122` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 176 | `validation/2026-10-23-audit14-plan-register-index-sync/README.md:174` | excluded: absence statement ("no new runtime characterization"); the merge-commit author sentence continuing on line 175 is CB-125 |
| 177 | `validation/2026-10-23-audit14-plan-register-index-sync/README.md:176` | excluded: source marks as existing/restated ("Source records' class B findings retain their own scope and limits") |
| 178 | `validation/2026-10-23-bra-section9-error-code-coverage/README.md:84` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 179 | `validation/2026-10-23-bra-section9-error-code-coverage/README.md:140` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 180 | `validation/2026-10-23-fsm-returned-data-isolation/README.md:72` | CB-156 |
| 181 | `validation/2026-10-23-owner-stop-handoff-addendum/README.md:146` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 182 | `validation/2026-10-23-plan-readiness-migration-edge-tests/README.md:63` | excluded: absence statement |
| 183 | `validation/2026-10-23-plan-register-index-sync-20261023/README.md:139` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 184 | `validation/2026-10-23-plan-register-index-sync-20261023/README.md:194` | excluded: restates CB-125 |
| 185 | `validation/2026-10-23-plan-register-index-sync-20261023/README.md:196` | excluded: source marks as existing/restated ("Existing source-record class B findings remain observations") |
| 186 | `validation/2026-10-23-plan-rs-summary-arithmetic-tests/README.md:122` | excluded: heading/lead-in for CB-157..CB-160 |
| 187 | `validation/2026-10-23-readiness-receipt-audit-tests/README.md:156` | excluded: source marks as existing/restated ("The three existing class-B recovery characterizations remain OPEN with owner Astra") |
| 188 | `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md:87` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 189 | `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md:213` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 190 | `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md:256` | excluded: absence statement |
| 191 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md:148` | excluded: restates CB-170 in same file |
| 192 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md:242` | excluded: restates CB-170 in same file |
| 193 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md:244` | excluded: heading of fault-row tables whose content is summarized as CB-163..CB-167 in same file |
| 194 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md:311` | excluded: heading/lead-in for CB-162..CB-170 |
| 195 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md:312` | CB-162 |
| 196 | `validation/2026-10-23-settlement-credit-rejection-atomicity/README.md:346` | excluded: generic mention, no specific observation |
| 197 | `validation/2026-10-24-bra-aid-returned-data-isolation/README.md:84` | excluded: restates CB-171..CB-177 in same file (class-level summary of the BRA/AID B table rows) |
| 198 | `validation/2026-10-24-bra-aid-returned-data-isolation/README.md:137` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 199 | `validation/2026-10-24-bra-aid-returned-data-isolation/README.md:156` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 200 | `validation/2026-10-24-plan-register-index-sync/README.md:146` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 201 | `validation/2026-10-24-plan-register-index-sync/README.md:206` | excluded: absence statement ("no new runtime characterization"); the merge-commit author sentence continuing on line 207 is CB-125 |
| 202 | `validation/2026-10-24-resale-admission-rejection-atomicity/README.md:301` | CB-178 |
| 203 | `validation/2026-10-24-resale-admission-rejection-atomicity/README.md:302` | CB-179 |
| 204 | `validation/2026-10-24-resale-admission-rejection-atomicity/README.md:401` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 205 | `validation/2026-10-24-reward-snapshot-isolation/README.md:79` | CB-180 |
| 206 | `validation/2026-10-24-reward-snapshot-isolation/README.md:83` | excluded: restates CB-180 in same file (same unit, names test class purpose) |
| 207 | `validation/2026-10-24-reward-snapshot-isolation/README.md:96` | excluded: absence statement |
| 208 | `validation/2026-10-24-reward-snapshot-isolation/README.md:152` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 209 | `validation/2026-10-24-reward-snapshot-isolation/README.md:306` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 210 | `validation/2026-10-25-aid-rejection-atomicity/README.md:76` | excluded: heading/lead-in for CB-181..CB-183 |
| 211 | `validation/2026-10-25-aid-rejection-atomicity/README.md:147` | excluded: source marks as existing/restated ("remains the pre-existing property suite's class-B characterization") |
| 212 | `validation/2026-10-25-aid-rejection-atomicity/README.md:192` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 213 | `validation/2026-10-25-audit15-open-decisions-closure/README.md:96` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 214 | `validation/2026-10-25-audit15-open-decisions-closure/README.md:239` | excluded: source marks as existing/restated ("pointers to their existing class B records"); #278, #280 |
| 215 | `validation/2026-10-25-audit15-reference-test-sibling-path-guard/README.md:133` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 216 | `validation/2026-10-25-bra-contract-clause-evidence-map/README.md:90` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 217 | `validation/2026-10-25-bra-contract-clause-evidence-map/README.md:170` | excluded: source marks as existing/restated ("the recorded clock-skew class B limit") |
| 218 | `validation/2026-10-25-bra-contract-clause-evidence-map/README.md:182` | excluded: source marks as existing/restated ("The existing class B ... described in the map and linked prior records") |
| 219 | `validation/2026-10-25-bra-contract-clause-evidence-map/README.md:206` | excluded: generic mention, no specific observation |
| 220 | `validation/2026-10-25-ci-wire-product-contract-evidence-checkers/README.md:123` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 221 | `validation/2026-10-25-ci-wire-product-contract-evidence-checkers/README.md:184` | excluded: absence statement |
| 222 | `validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md:94` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 223 | `validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md:190` | excluded: source marks as existing/restated ("Existing class B observations remain class B") |
| 224 | `validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md:191` | excluded: source marks as existing/restated ("Existing class B observations remain class B") |
| 225 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:47` | CB-184 |
| 226 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:65` | excluded: restates CB-184 in same file |
| 227 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:109` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 228 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:117` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 229 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:163` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 230 | `validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md:176` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 231 | `validation/2026-10-25-plan-primary-price-fee-contract-clause-eviden/README.md:122` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 232 | `validation/2026-10-25-plan-primary-price-fee-contract-clause-eviden/README.md:150` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 233 | `validation/2026-10-25-plan-primary-price-fee-contract-clause-eviden/README.md:197` | excluded: absence statement |
| 234 | `validation/2026-10-25-plan-register-index-crosswalk-sync/README.md:157` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 235 | `validation/2026-10-25-plan-register-index-crosswalk-sync/README.md:210` | excluded: source marks as existing/restated ("Existing ... class B observations remain in their original records"); #278, #280 |
| 236 | `validation/2026-10-25-plan-register-index-sync-20261025/README.md:167` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 237 | `validation/2026-10-25-plan-register-index-sync-20261025/README.md:212` | excluded: source marks as existing/restated ("remains its class B observation pending Astra"); #280, #278 |
| 238 | `validation/2026-10-25-plan-register-index-sync-20261025/README.md:215` | excluded: source marks as existing/restated ("other class B characterizations remain in their original records") |
| 239 | `validation/2026-10-25-plan-register-index-sync-20261025/README.md:252` | excluded: source marks as existing/restated ("the reward/clock-skew class B questions remain open") |
| 240 | `validation/2026-10-25-plan-section5-quote-completeness/README.md:80` | excluded: quoted transcript/diff (quoted source line of validation/2026-10-21-plan-rs-zk-encoding-regressions/README.md:185) |
| 241 | `validation/2026-10-25-plan-section5-quote-completeness/README.md:355` | excluded: absence statement |
| 242 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:38` | excluded: absence statement |
| 243 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:39` | excluded: source marks as existing/restated ("Existing class B observations remain characterized") |
| 244 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:61` | excluded: source marks as existing/restated ("Settlement §9.2's pre-existing class B") |
| 245 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:80` | excluded: source marks as existing/restated ("Existing class B zero-cash-commit characterization"; "Prior record") |
| 246 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:100` | excluded: source marks as existing/restated ("recorded class B") |
| 247 | `validation/2026-10-25-product-contract-map-partial-closure/README.md:168` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 248 | `validation/2026-10-25-restore-fingerprint-equivalence/README.md:99` | excluded: heading/lead-in for CB-188, CB-189 |
| 249 | `validation/2026-10-25-restore-fingerprint-equivalence/README.md:180` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 250 | `validation/2026-10-25-restore-fingerprint-equivalence/README.md:229` | excluded: restates CB-188, CB-189 in same file |
| 251 | `validation/2026-10-25-settlement-contract-clause-evidence-map/README.md:76` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 252 | `validation/2026-10-25-settlement-contract-clause-evidence-map/README.md:159` | excluded: source marks as existing/restated ("retain their previously recorded limits") |
| 253 | `validation/2026-10-26-plan-ai-delegation-contract-clause-evidence-m/README.md:92` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 254 | `validation/2026-10-26-plan-ai-delegation-contract-clause-evidence-m/README.md:180` | excluded: source marks as existing/restated ("the existing four-entry authority-list test is a Class B characterization") |
| 255 | `validation/2026-10-26-plan-ai-delegation-contract-clause-evidence-m/README.md:185` | excluded: source marks as existing/restated ("Existing contract-undefined observations remain open") |
| 256 | `validation/2026-10-26-plan-bcs1-contract-clause-evidence-map/README.md:80` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 257 | `validation/2026-10-26-plan-bcs1-contract-clause-evidence-map/README.md:110` | excluded: restates CB-001..CB-004 |
| 258 | `validation/2026-10-26-plan-ci-checker-wiring-guard/README.md:133` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 259 | `validation/2026-10-26-plan-ci-checker-wiring-guard/README.md:224` | excluded: absence statement |
| 260 | `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md:73` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 261 | `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md:99` | excluded: restates CB-005 |
| 262 | `validation/2026-10-26-plan-contract-invariants-inv3-sensitivity/README.md:71` | excluded: restates CB-006 |
| 263 | `validation/2026-10-26-plan-contract-invariants-inv3-sensitivity/README.md:101` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 264 | `validation/2026-10-26-plan-evidence-map-rollup-check/README.md:52` | excluded: heading/lead-in for CB-193 |
| 265 | `validation/2026-10-26-plan-feature-ir-money-profile-precedence-tests/README.md:14` | excluded: restates CB-194 in same file |
| 266 | `validation/2026-10-26-plan-feature-ir-money-profile-precedence-tests/README.md:32` | CB-194 |
| 267 | `validation/2026-10-26-plan-feature-ir-money-profile-precedence-tests/README.md:83` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 268 | `validation/2026-10-26-plan-feature-ir-validator-matrix-closure/README.md:46` | excluded: source states the item is not class B ("not class B or a defect") |
| 269 | `validation/2026-10-26-plan-feature-ir-validator-matrix-closure/README.md:48` | excluded: absence statement |
| 270 | `validation/2026-10-26-plan-feature-semantics-v1-evidence-map/README.md:38` | excluded: generic mention, no specific observation (checker checks class-B citations) |
| 271 | `validation/2026-10-26-plan-feature-semantics-v1-evidence-map/README.md:84` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 272 | `validation/2026-10-26-plan-feature-semantics-v1-evidence-map/README.md:121` | excluded: source marks as existing/restated ("Class B retained") |
| 273 | `validation/2026-10-26-plan-integration-gate-contract-clause-ev/README.md:47` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 274 | `validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md:77` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 275 | `validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md:194` | excluded: absence statement |
| 276 | `validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:173` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 277 | `validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md:341` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 278 | `validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md:1508` | CB-195 |
| 279 | `validation/2026-10-26-plan-open-decisions-addendum-bcs1-checke/README.md:51` | excluded: source marks as existing/restated ("the map's §4 contract-undefined characterizations remain open"); BCS1 evidence map |
| 280 | `validation/2026-10-26-plan-open-decisions-addendum-bcs1-checke/README.md:108` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 281 | `validation/2026-10-26-plan-open-decisions-addendum-bcs1-checke/README.md:393` | excluded: absence statement |
| 282 | `validation/2026-10-26-plan-perf-harness-map-partial-closure/README.md:117` | excluded: heading/lead-in for CB-196..CB-199 |
| 283 | `validation/2026-10-26-plan-perf-harness-map-partial-closure/README.md:197` | excluded: absence statement (also "the existing observability limitations and non-claims above remain") |
| 284 | `validation/2026-10-26-plan-perf-harness-map-partial-closure/README.md:335` | excluded: absence statement |
| 285 | `validation/2026-10-26-plan-performance-measurement-clause-evid/README.md:85` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 286 | `validation/2026-10-26-plan-performance-measurement-clause-evid/README.md:117` | CB-200 |
| 287 | `validation/2026-10-26-plan-primary-fee-pf-c05-isolation-tests/README.md:64` | CB-201 |
| 288 | `validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md:135` | excluded: quoted transcript/diff |
| 289 | `validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md:789` | CB-202 |
| 290 | `validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md:834` | excluded: restates CB-202 |
| 291 | `validation/2026-10-26-plan-toss-card-profile-evidence-map/README.md:83` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 292 | `validation/2026-10-26-plan-toss-card-profile-evidence-map/README.md:123` | CB-203 |
| 293 | `validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md:155` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 294 | `validation/2026-10-27-plan-ci-test-suite-discovery-guard/README.md:248` | excluded: absence statement |
| 295 | `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:53` | excluded: generic mention, no specific observation (coverage-table gap cell "retain class B"; specific items are CB-007) |
| 296 | `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:62` | excluded: generic mention, no specific observation |
| 297 | `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:101` | excluded: restates CB-007 |
| 298 | `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:220` | excluded: restates CB-007 (follow-up candidate pointer) |
| 299 | `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:245` | excluded: restates CB-007 |
| 300 | `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:279` | excluded: absence statement |
| 301 | `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:63` | excluded: restates CB-009 |
| 302 | `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:68` | excluded: heading/lead-in; its items are indexed as CB-009 |
| 303 | `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:75` | excluded: heading/lead-in; its items are indexed as CB-009 (table header; per-test column restates F-B5 items) |
| 304 | `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:80` | excluded: restates CB-009 |
| 305 | `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:91` | excluded: heading/lead-in; its items are indexed as CB-009 |
| 306 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:95` | excluded: heading/lead-in; its items are indexed as CB-010 (labelling rule) |
| 307 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:104` | excluded: generic mention, no specific observation (matrix label legend) |
| 308 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:141` | excluded: restates CB-010 (pair count) |
| 309 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:164` | excluded: B cell not a classification column (Clause column; B = bounded records family) |
| 310 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:171` | excluded: B cell not a classification column (Clause column; B = bounded records family) |
| 311 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:191` | excluded: heading/lead-in; its items are indexed as CB-010 |
| 312 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:239` | excluded: restates CB-010 (command result cell) |
| 313 | `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:284` | excluded: generic mention, no specific observation |
| 314 | `validation/2026-10-27-plan-loop-node-crosswalk-refresh/README.md:382` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 315 | `validation/2026-10-27-plan-loop-node-crosswalk-refresh/README.md:458` | excluded: source marks as existing/restated ("#320 class B characterization remain attributed to their source records"); PR #320 |
| 316 | `validation/2026-10-27-plan-loopback-host-preflight/README.md:312` | CB-204 |
| 317 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:110` | excluded: source marks as existing/restated ("the existing class B F-B1 characterization"); docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md F-B1 |
| 318 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:3635` | excluded: quoted transcript/diff |
| 319 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4270` | excluded: quoted transcript/diff |
| 320 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4368` | excluded: quoted transcript/diff |
| 321 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4377` | excluded: quoted transcript/diff |
| 322 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4435` | excluded: quoted transcript/diff |
| 323 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4500` | excluded: quoted transcript/diff |
| 324 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4524` | excluded: quoted transcript/diff |
| 325 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4581` | excluded: quoted transcript/diff |
| 326 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4622` | excluded: quoted transcript/diff |
| 327 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4721` | excluded: quoted transcript/diff |
| 328 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:4728` | excluded: quoted transcript/diff |
| 329 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6320` | excluded: quoted transcript/diff |
| 330 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6321` | excluded: quoted transcript/diff |
| 331 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6322` | excluded: quoted transcript/diff |
| 332 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6323` | excluded: quoted transcript/diff |
| 333 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6324` | excluded: quoted transcript/diff |
| 334 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6634` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 335 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6646` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 336 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:6670` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 337 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:7487` | excluded: quoted transcript/diff |
| 338 | `validation/2026-10-27-plan-open-decisions-addendum-perf-probe-pin/README.md:7488` | excluded: quoted transcript/diff |
| 339 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:117` | excluded: source marks as existing/restated ("Existing contract-undefined interpretations stay with their recorded owners") |
| 340 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:1561` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 341 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:1577` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 342 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:1601` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 343 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:2739` | excluded: quoted transcript/diff |
| 344 | `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:2740` | excluded: quoted transcript/diff |
| 345 | `validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md:69` | CB-205 |
| 346 | `validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md:70` | CB-206 |
| 347 | `validation/2026-10-27-plan-perf-harness-kernel-construction-co/README.md:71` | CB-207 |
| 348 | `validation/2026-10-27-plan-perf-harness-map-json-csv-closure-2/README.md:91` | excluded: heading/lead-in for CB-208..CB-210 |
| 349 | `validation/2026-10-27-plan-register-sync-20261027/README.md:115` | excluded: source marks as existing/restated ("EV-V5 #320 stays finite, source-informed, class B"); PR #320 |
| 350 | `validation/2026-10-27-plan-register-sync-20261027/README.md:185` | excluded: checker/Counts vocabulary (CLASS_B token) |
| 351 | `validation/2026-10-27-plan-register-sync-20261027/README.md:412` | excluded: absence statement |
| 352 | `validation/2026-10-27-plan-register-sync-20261027/README.md:413` | excluded: source marks as existing/restated ("class B characterizations and all owner decisions remain at their attributed sources") |
| 353 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md:100` | excluded: restates CB-214 in same file |
| 354 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md:116` | excluded: restates CB-213 in same file |
| 355 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md:211` | excluded: heading/lead-in for CB-211..CB-216 (class B scope rationale) |
| 356 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md:214` | excluded: heading/lead-in for CB-211..CB-216 |
| 357 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md:296` | excluded: generic mention, no specific observation (follow-up candidate) |
| 358 | `validation/2026-10-27-v5-kernel-only-contract-invariant-histories/README.md:297` | excluded: restates CB-211, CB-214 in same file (follow-up candidate) |

## Restatements not indexed

These units were read as class B items, but each restates a characterization first recorded in the
record of the cited row. Most of them are not hit lines themselves. Because owner cells are copied only
from the chosen source, an owner a restating map names (for example `Astra` for the readiness `OPEN-*`
rows or `User` for the feature-semantics rows) does not appear in the index row. It stays in the map,
unchanged.

| Unit (path:line) | Restates |
|---|---|
| `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md:151` | CB-178 |
| `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md:156` | CB-179 |
| `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md:160` | CB-171..CB-174 |
| `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md:162` | CB-185..CB-187 |
| `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:79` | CB-065 |
| `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:80` | CB-099 |
| `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:81` | CB-100 |
| `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:82` | CB-101 |
| `docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md:83` | CB-194 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:92` | CB-205..CB-207 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:93` | CB-200 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:94` | CB-200 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:95` | CB-196 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:96` | CB-197 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:97` | CB-198 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:98` | CB-208 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:102` | CB-210 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:103` | CB-209 |
| `docs/status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md:104` | CB-199 |
| `docs/status/PRIMARY_PRICE_FEE_CONTRACT_EVIDENCE_MAP.md:113` | CB-201 |
| `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:62` | CB-102 |
| `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:63` | CB-104 |
| `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md:64` | CB-105 |
| `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md:105` | CB-163 |
| `validation/2026-10-09-k-a-integration-decision/README.md:97` | CB-021 |
| `validation/2026-10-09-k-a-integration-decision/README.md:98` | CB-020 |
| `validation/2026-10-16-audit7-plan-register-index-sync-20261016b/README.md:75` | CB-065 |
| `validation/2026-10-16-rs-predicate-evidence-map/README.md:77` | CB-028 |
| `validation/2026-10-16-rs-predicate-evidence-map/README.md:79` | CB-039 |
| `validation/2026-10-16-testnet-key-management-decision/README.md:102` | CB-023 |
| `validation/2026-10-16-testnet-key-management-decision/README.md:103` | CB-024 |
| `validation/2026-10-17-booking-resale-adopt-issued-atomicity-fix/README.md:92` | CB-086 |
| `validation/2026-10-20-plan-rs-grant-cut-order-tests/README.md:56` | CB-046 |
| `validation/2026-10-23-audit14-plan-register-index-sync/README.md:175` | CB-125 |
| `validation/2026-10-23-plan-register-index-sync-20261023/README.md:194` | CB-125 |
| `validation/2026-10-24-plan-register-index-sync/README.md:207` | CB-125 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:71` | CB-186 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:72` | CB-186 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:73` | CB-186 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:75` | CB-187 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:76` | CB-187 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:77` | CB-187 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:79` | CB-188 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:81` | CB-189 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:82` | CB-189 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:83` | CB-189 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:84` | CB-189 |
| `validation/2026-10-25-restore-fingerprint-equivalence/README.md:101` | CB-188, CB-189 |
| `validation/2026-10-26-plan-bcs1-contract-clause-evidence-map/README.md:110` | CB-001..CB-004 |
| `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md:99` | CB-005 |
| `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md:99` | CB-006 |
| `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md:99` | CB-007 |
| `validation/2026-10-26-plan-contract-invariants-evidence-map/README.md:99` | CB-008 |
| `validation/2026-10-26-plan-contract-invariants-inv3-sensitivity/README.md:71` | CB-006 |
| `validation/2026-10-26-plan-rs4-l2-option-impact-inventory/README.md:834` | CB-202 |
| `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:80` | CB-007 |
| `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:81` | CB-007 |
| `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:82` | CB-007 |
| `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:83` | CB-007 |
| `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:85` | CB-007 |
| `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:86` | CB-007 |
| `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:97` | CB-007 |
| `validation/2026-10-27-plan-contract-invariants-f-b3-reply-assertions/README.md:98` | CB-007 |
| `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:93` | CB-009 |
| `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:95` | CB-009 |
| `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:97` | CB-009 |
| `validation/2026-10-27-plan-contract-invariants-s5-availability/README.md:100` | CB-009 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:201` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:204` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:207` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:209` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:212` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:216` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:217` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:218` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:219` | CB-010 |
| `validation/2026-10-27-plan-contract-invariants-s5-precedence/README.md:220` | CB-010 |

## Tests named in a source but not cited as symbols

The Test cell reads `unresolved: see validation record` for these rows. Glob families and
template-named tests (`test_char_fault_<command>` is generated at runtime by `install_faults`) have no
static definition to check. The named symbols in the third column are not defined anywhere in the tree
at the base. That is a stale name in the source record, which is left unchanged here, not a missing test
claim.

| Row | Glob or template family | Named but not defined |
|---|---|---|
| CB-096 | none | `open_defect_late_ga_capture_leaves_map_free_set_behind_the_kernel`, `open_defect_is_found_by_the_differential_when_not_excluded` |
| CB-131 | `test_fault_*_late_rejection_leaves_unapplied_mutation` | none |
| CB-132 | `test_fault_pool_*_spend_leaves_unapplied_mutation` | none |
| CB-146 | none | `test_g_post_reclass_distribution_applies_zero_to_every_line` |
| CB-163 | `test_fault_*` | none |
| CB-168 | `test_guard_drift_*` | none |
| CB-179 | `test_char_fault_<command>` | none |

## Commands run and results

Local host Python 3.13.5 (CI pins 3.12), run from the repository root on the working tree. No commit was
made by the builder.

| Command | Result |
|---|---|
| `git fetch origin main`; `git rev-parse origin/main HEAD` | both `b7d0fe551d3ebfab9c94c4bbd3ffee544596d42b` |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20` both times |
| The two search `grep` commands above (base tree) | 333 + 25 = 358 lines, 152 files |
| `python3 -I scripts/check_class_b_index.py` | exit 0: `class B index ok: rows=216 sources=71 symbols=39; textual index only` |
| `python3 -I scripts/check_class_b_index.py --self-test` | exit 0: 20 negative controls detected (missing path, missing test path, altered quote, short quote, piped quote, unknown symbol, unknown dotted part, unknown node:test name, duplicate id, bad id, wrong count, missing count token, two counts lines, invented owner, invented contract, out-of-scope source, invented status, superseded without supersession quote, superseded with wrong PR, wrong header); `self-test: pass (20 negative controls)` |
| `python3 -I scripts/check_class_b_index.py --bogus` | exit 2, usage line |
| `python3 -I scripts/check_ci_checker_wiring.py` / `--self-test` | exit 0: `scripts=34 plain=33 self_test=34 self_test_only=1 docs=22 citations=99` / `self-test: pass (13 negative controls)` |
| `python3 -I scripts/check_docs_index.py` / `--self-test` | exit 0: `scanned=293 indexed=258 allowlisted=35` / `self-test: pass` |
| `python3 -I scripts/check_status_register.py` / `--self-test` | exit 0: `paths=452 ev_ids=15 original32=32` / `self-test: pass` |
| `python3 -I scripts/check_evidence_map_rollup.py` / `--self-test` | exit 0: `contracts=25; textual index only` / `self-test: pass (16 negative controls)` |
| `python3 -I scripts/check_ci_test_discovery.py` / `--self-test` | exit 0: `reference_suites=6 node_tests=8 modules=4 excluded=3` / `self-test: pass (18 negative controls)` |
| Every `python3 scripts/check_*.py` line of the `Stdlib offline document checks` step (61 lines, including the two new ones), run one by one as `python3 -I` | all exit 0 |
| `git diff --quiet origin/main -- reference/v0.3-rc1 runtime .aiops docs/tasks docs/contracts` | exit 0 (unchanged) |
| `git status --short` | only the five changed paths listed above |

No Rust, Node or Move suite was run: no runtime, reference or test path changed. Exact-head KTX kernel
verification and KIX protocol verification are required on the final head and are not claimed here.

## Non-claims

- No contract, map row, status, grade, owner, test or source file is changed. No item is classified,
  reclassified, resolved, ranked or recommended.
- A row says that its source labels an observation class B. It does not confirm the observation, and the
  quote is an excerpt, not a restatement.
- The checker checks citations textually: path existence, byte-for-byte quote presence, symbol definition,
  verbatim owner and contract text, ids and counts. It does not check that a quote is the best excerpt,
  that a test asserts the characterization, or that the row set is complete.
- No production durability, distributed fencing, bank exactly-once, chain finality, legal compliance or
  production readiness is claimed.

## Remaining uncertainty and follow-up candidates

- Completeness depends on the search. A characterization that is labelled only with other words (for
  example "contract does not define" with no "class B" or "contract undefined"), or only in files outside
  the two globs, is not indexed.
- Row granularity, the choice of first record and the restatement links are builder readings. Astra or the
  named owners may regroup them; ids stay stable and new rows are appended.
- Some evidence maps were amended after their first record, so a map wording can be newer than the record
  the row cites. The restatement table names each such map unit.
- The checker couples to the quoted text. A later edit to a quoted line in a source record or map fails
  `check_class_b_index.py` until the index row is updated by a later node.
- CB-082 (`validation/2026-10-17-ai-delegation-seeded-property-suite/README.md`) records `INVALID_ID` where
  the source says "contract DLG-03 says `EXECUTE_AUTHORITY_DISABLED`". The source labels it B, and later
  records keep it as a Class B characterization accepting either code. This index copies that label and
  does not assess it.
- CB-146 cites `test_g_post_reclass_distribution_applies_zero_to_every_line`, and CB-096 cites the two
  `open_defect_*` names. None of these is defined at the base. The source records are left unchanged.
