# October 27 open-decisions closure validation

Builder evidence for `plan-plan-open-decisions-closure-20261027`, dated 2026-10-27.
Task document: supervisor-supplied node specification and read-only design prompt;
no issue or node-specific document under `docs/tasks/`. Not ASTRA program mode;
no signer, marker, comment or external delivery. Source: supplied KIX planner run
1793059450; the planner and external decision files were not executed/read here.

Observed cached `origin/main`, base, starting and current committed branch HEAD:
`09470db220965390edeecdb75f56f8c827dd15b6` (#313). No local base delta.
Branch: `agent/kix-plan-plan-open-decisions-closure-20261027`.
`git fetch origin main`: NOT_RUN under the supervisor's explicit no-network rule,
overriding AGENTS §1; remote freshness is unverified. No rebase or base change.
Implementation head / exact final task head: not assigned; the implementation
is an uncommitted worktree patch over the SHA above, for the supervisor to commit.
KTX exact-head CI run ID/status/conclusion: unavailable / NOT_RUN / not queried.
KIX protocol exact-head CI run ID/status/conclusion: unavailable / NOT_RUN / not queried.
Merge SHA, final-merge blob checks and post-merge main CI: not applicable.
Local READY is builder handoff only; no merge-readiness claim or non-author review.

## Changed paths

- `docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md`
- `docs/README.md`
- `validation/2026-10-27-plan-open-decisions-closure-20261027/README.md`

No commit, push, reset, GitHub/network action, PR, issue, comment, branch/tag
mutation or background job was performed. Temporary verification scripts and
logs were kept under `/tmp`; they are reproduced below for review and are not
repository deliverables. Commands ran in the node worktree, in the foreground.

## Existing coverage mapped before changes

| Requirement | Before | Existing evidence and gap addressed |
|---|---|---|
| Dated closure through #313 with one row per open stop | Not covered at this date | October 25 closure holds L1/L2/A2/A4; October 26 AI/BCS1/SDK addenda hold A5/BCS1/SD1. New follow-up scans 24 merges and preserves all seven stops. |
| Exact options and owners | Sufficiently covered in the holding records | Ledger lines 63–64 and 73–74; supplement lines 95–105 and 192–206; AI addendum 55–61; BCS1 addendum 210–226; SDK addendum 83–95. Copied, not redefined. |
| Index reachability | Sufficiently covered | `scripts/check_docs_index.py::find_problems/self_test` checks scanned-file indexing, broken links and mutations. New direct index links address the two new files. |
| Register consistency | Sufficiently covered | `scripts/check_status_register.py::find_problems/self_test` checks paths, EV IDs and original requirement keys. No register edit needed. |
| Current follow-up links/anchors, options, seven-row set and merge identities | Partially covered | Existing index checker ignores fragments and does not validate this follow-up's row semantics; temporary acceptance script below checks these specific documentary predicates. |
| CI invocation/map consistency | Sufficiently covered | `check_ci_checker_wiring.py` and `check_evidence_map_rollup.py` plain/self-test; run unchanged with the complete offline block. |
| Immutable blobs/reference snapshot and three-file boundary | Sufficiently covered by direct Git checks | Before/after HEAD blob IDs plus working-tree `git hash-object`; reference diff and complete untracked-aware status. |

No repository tests were added or duplicated. The new evidence is documentary:
seven carried-forward rows, verbatim quotations, 12 relevant merge-fact rows,
40 existing links/anchors, and reproducible command outputs. Missing artifacts
are deliberately labeled absent, not linked as if on main. Seven explicitly
absent/future paths are checked as absent; planner/branch/Git-ref identifiers
are metadata, not filesystem citations. Quoted future commands are not executed.

## Verification scope and outcomes

Narrow checks ran first: docs-index and status-register checks, plain/self-test,
all exit 0. The closest local equivalent of protocol CI for these docs-only
paths is its unconditional **Stdlib offline document checks** step. All 55
commands extracted from that step ran, each exit 0, including the roll-up,
wiring guard and stage-5 host self-test. The host's plain evaluator is
intentionally not wired; its self-test does not provision or qualify a host.
The KTX workflow's docs-only classifier skips Cargo/Clippy/formatting for these
paths; none was run. No full workflow, hosted CI, HTTP listener, Rust runtime,
measurement or blocked-node reproduction is claimed.

Both locked Git blobs match before and after, including working-tree bytes:

- kernel lib: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- quarantine test: `b607996c83a119c349f1cc90469ac1ba82764e20`

The immutable `reference/v0.3-rc1/**` snapshot is unchanged against local
`origin/main`; the protected-path diff is empty. `git diff --check` covers
tracked changes; explicit no-index whitespace checks also cover both new files.
The complete changed-path set is exactly the three files listed above.

The no-selection scan returned two hits: “no option is endorsed or chosen”
and “No option ... is selected or changed.” Both are non-selection statements.
No option is marked chosen, and source recommendations remain attributed quotes.
All seven rows are STILL OPEN, with resolved-by `none`; no ambiguous resolution
was found. RS-4 load stays UNDETERMINED (User); workload inputs stay with Astra.
AI missing-grant binding and SDK extension-profile interpretation retain their
recorded owners. Canonical counting remains `DECISION_REQUIRED · Astra`.

## Deviations, diagnostic exits and remaining uncertainty

- Fetch omitted under the supervisor's explicit no-network rule. Status applies
  only to the observed local basis, not a later or freshly fetched main.
- A4 is retained as the seventh row although the node enumerates six stops:
  October 25 still lists it open. This follows the supplied design's explicit
  preservation rule; it does not retire or otherwise dispose of the duplicate.
- The design calls the preserved earlier records “six” but names seven; all
  seven named records are linked and unchanged. Basis-derived citation lines
  and the #290 node name were used where design examples were approximate.
- Expected `ls` exit 2 reports absent L1/L2/SDK artifacts; expected `rg` exit 1
  reports no seeded journey and no node definition in program/tasks. These
  are evidence of absence, not test failures. The successful A4 name search
  finds older records and quoted copies, not a disposition.
- First temporary acceptance-script run exited 1 after owner/option/link checks:
  it mistook `origin/main` for a path. Excluding that Git-ref identifier fixed
  the local script; rerun passed. Its initial output is preserved below.
- Initial `PYTHONPATH=/tmp python3 /tmp/kix_run_doc_ci.py > /tmp/kix_closure_ci.txt`
  exited 1 before running checkers: a temporary harness incorrectly asserted
  57 extracted commands; actual count was 55 (`AssertionError: 55`). The harness
  was corrected to require a nonempty extracted list and run every command.
  The corrected invocation exited 0, reporting 55 commands and zero failures.
  No repository or CI file was changed to address either harness issue.
- `git diff --no-index --check /dev/null <new-file>` returns 1 for a new
  nonempty file even when it reports no whitespace diagnostics. The first
  preservation harness incorrectly required exit 0 and stopped at that result;
  the remaining checks were then completed. Final no-index results are checked
  for empty diagnostic output and the expected exit 1; tracked `git diff --check`
  exits 0. No file change was needed to address this harness assumption.
- The new validation record initially failed its no-index whitespace check
  (exit 3): `git show --format=fuller` output contained an indented blank line,
  which the raw-output renderer copied literally. Output trailing spaces/tabs
  are now represented by literal escape sequences, preserving their identity
  without introducing Markdown whitespace errors. Final whitespace checks pass.
- A5 and SD1 are existing attributed class C stops; no new runtime violation
  is claimed or reproduced here. BCS1 remains a scope/acceptance conflict.
  Existing contract-undefined interpretations stay with their recorded owners.
- Host provisioning/execution, owner decisions and any future corrective node
  remain outside this task. No policy values, protocol commands, runtime,
  contract, map statuses, owners or node states changed. No production,
  durability, distributed fencing, bank exactly-once, chain finality, legal
  compliance or independent-review claim is made.

## Actual command evidence

Read-only context inspection additionally used `pwd`, `git status --short`,
`rg --files`, `cat`, `sed -n` and `nl -ba` over AGENTS, README, development plan,
baselines, authority/program decisions, control-plane pointers, earlier ledgers,
addenda, cited maps/records, both workflow definitions and the existing index/
register checker sources. No runtime tests were executed and no external decision files were read
through these commands. The tables and raw outputs below record the substantive
baseline, gathering, acceptance, CI-equivalent and preservation commands with
their actual exit codes. Identical commands may recur at distinct stages.

| # | Command | Result |
|---|---|---|
| 1 | `git rev-parse origin/main HEAD` | exit 0 |
| 2 | `git branch --show-current` | exit 0 |
| 3 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 4 | `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 5 | `git diff --exit-code origin/main -- reference/v0.3-rc1` | exit 0 |
| 6 | `git log --first-parent --merges --format='%H %s' 22df2e96d1a7de4d0de371a1f64776e80af9d999..HEAD` | exit 0 |
| 7 | `git show --stat --oneline 09470db220965390edeecdb75f56f8c827dd15b6` | exit 0 |
| 8 | `git show --stat --oneline d2b748aef0c7b4af5bef23c771c6bce22b52905f` | exit 0 |
| 9 | `git show --stat --oneline e00e68e680d586346abada94500955abfe938ca3` | exit 0 |
| 10 | `git show --stat --oneline 58dd527ff53097f5231e89f25ebdf3e94586ee65` | exit 0 |
| 11 | `git show --stat --oneline 118fc28862a6828b80166433bac6f5476037629d` | exit 0 |
| 12 | `git show --stat --oneline ae6b905104d0cb2022001fb32ad98b1a6b3046ec` | exit 0 |
| 13 | `git show --stat --oneline a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4` | exit 0 |
| 14 | `git show --stat --oneline a176c1f22c0af21500cb52a777bc889b808e561c` | exit 0 |
| 15 | `git show --stat --oneline 23391ab50e0467bc7b234c55e98614713d531f58` | exit 0 |
| 16 | `git show --stat --oneline 22d05a0c82693ad4575a72c2d342b4e47114447f` | exit 0 |
| 17 | `git show --stat --oneline 9fd4d4836ab4d7eb666ebd4ff2ac0708870d7a58` | exit 0 |
| 18 | `git show --stat --oneline 412e1ed7bc740599227567f60bf315bb7ecab818` | exit 0 |
| 19 | `git show --stat --oneline fc11cdf0150e54ed38bb363f2ded7238c48c6e53` | exit 0 |
| 20 | `git show --stat --oneline ff1a955815a054f2345a2e06939f2c84bfc29be6` | exit 0 |
| 21 | `git show --stat --oneline 1f01a9321c641c7a7fafa2a33e4350a2fa711730` | exit 0 |
| 22 | `git show --stat --oneline 18aefc8f7c0dd13b7249e0d80304f3b97459fa3a` | exit 0 |
| 23 | `git show --stat --oneline 957f75d75ea4854eba117d66d07663133f0b7b2c` | exit 0 |
| 24 | `git show --stat --oneline 1bb000bd125a1e8ecdd033cea01733d58588199e` | exit 0 |
| 25 | `git show --stat --oneline 54a785b864d629d623afc36ed807d9daebaf9285` | exit 0 |
| 26 | `git show --stat --oneline 944cb16f3ade5a395c0febe84fd47d5c16dc0fa3` | exit 0 |
| 27 | `git show --stat --oneline a38e1679449e74186c5a4e3d19b6cb79f6b791d5` | exit 0 |
| 28 | `git show --stat --oneline a0db1e226e27b1c5f60ee938fb528ff795907056` | exit 0 |
| 29 | `git show --stat --oneline 01f6c04c71dac27fab5d17017f4e837c076218c6` | exit 0 |
| 30 | `git show --stat --oneline 92d08e755dfe362ed224112c8dada6c5fcea17d4` | exit 0 |
| 31 | `ls durable scripts/stage5_local_check.py validation/2026-10-13-k-stage5-durable-tx` | exit 2 |
| 32 | `rg -n -A4 SELF_TEST_ONLY scripts/check_ci_checker_wiring.py` | exit 0 |
| 33 | `ls validation/2026-10-15-rs-4-l2-load` | exit 2 |
| 34 | `rg -n UNDETERMINED docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md` | exit 0 |
| 35 | `rg -n SeededJourney integration_gate` | exit 1 |
| 36 | `sed -n '87p' docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md` | exit 0 |
| 37 | `git grep -n plan-plan-plan-register-index-sync-20261023 -- ':!docs/status/OPEN_USER_DECISIONS_*'` | exit 0 |
| 38 | `sed -n '280,291p' reference/ai_delegation/ai_delegation_mock.py` | exit 0 |
| 39 | `git log --oneline 22df2e9..HEAD -- reference/ai_delegation docs/contracts/AI_DELEGATION_AUTHORITY.md` | exit 0 |
| 40 | `sed -n '14p' scripts/check_bcs1_evidence_map.py` | exit 0 |
| 41 | `git log --oneline 22df2e9..HEAD -- scripts/check_bcs1_evidence_map.py docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md runtime/crates/kix-bcs1` | exit 0 |
| 42 | `rg -n 'bytes drift\|profile_sha256' sdk/compat/verify_compat.mjs` | exit 0 |
| 43 | `ls docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md scripts/check_sdk_compat_manifest_evidence_map.py` | exit 2 |
| 44 | `git log --oneline 22df2e9..HEAD -- sdk docs/contracts/sdk` | exit 0 |
| 45 | `rg -n plan-plan-open-decisions-closure-20261027 .aiops/program.json docs/tasks` | exit 1 |
| 46 | `rg -n 'UNDETERMINED\|STILL OPEN\|#290\|seeded\|Seeded\|listener\|gate behavior\|No .*change\|No map' docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md docs/status/EVIDENCE_MAP_ROLLUP.md validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md` | exit 0 |
| 47 | `python3 scripts/check_docs_index.py` | exit 0 |
| 48 | `python3 scripts/check_docs_index.py --self-test` | exit 0 |
| 49 | `python3 scripts/check_status_register.py` | exit 0 |
| 50 | `python3 scripts/check_status_register.py --self-test` | exit 0 |
| 51 | `python3 /tmp/kix_check_closure.py` | exit 1 |
| 52 | `python3 /tmp/kix_check_closure.py` | exit 0 |
| 53 | `rg -n -i 'chosen\|selected\|approved\|adopt' docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md` | exit 0 |
| 54 | `python3 scripts/check_status_register.py` | exit 0 |
| 55 | `python3 scripts/check_status_register.py --self-test` | exit 0 |
| 56 | `python3 scripts/check_rs_profile_traceability.py` | exit 0 |
| 57 | `python3 scripts/check_rs_profile_traceability.py --self-test` | exit 0 |
| 58 | `python3 scripts/check_read_model_source_map.py` | exit 0 |
| 59 | `python3 scripts/check_read_model_source_map.py --self-test` | exit 0 |
| 60 | `python3 scripts/check_docs_index.py` | exit 0 |
| 61 | `python3 scripts/check_docs_index.py --self-test` | exit 0 |
| 62 | `python3 scripts/check_i12_proof_ids.py` | exit 0 |
| 63 | `python3 scripts/check_i12_proof_ids.py --self-test` | exit 0 |
| 64 | `python3 scripts/check_delegation_layer_matrix.py` | exit 0 |
| 65 | `python3 scripts/check_delegation_layer_matrix.py --self-test` | exit 0 |
| 66 | `python3 scripts/check_rs_predicate_evidence_map.py` | exit 0 |
| 67 | `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | exit 0 |
| 68 | `python3 scripts/check_rs_im_evidence_map.py` | exit 0 |
| 69 | `python3 scripts/check_rs_im_evidence_map.py --self-test` | exit 0 |
| 70 | `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0 |
| 71 | `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0 |
| 72 | `python3 scripts/check_contract_error_codes.py` | exit 0 |
| 73 | `python3 scripts/check_contract_error_codes.py --self-test` | exit 0 |
| 74 | `python3 scripts/check_adapter_identity_map.py` | exit 0 |
| 75 | `python3 scripts/check_adapter_identity_map.py --self-test` | exit 0 |
| 76 | `python3 scripts/check_v5_transition_evidence_map.py` | exit 0 |
| 77 | `python3 scripts/check_v5_transition_evidence_map.py --self-test` | exit 0 |
| 78 | `python3 scripts/check_readiness_evidence_map.py` | exit 0 |
| 79 | `rg -n -F 'User / supervisor (build host)' docs/status/OPEN_USER_DECISIONS_20261022.md` | exit 0 |
| 80 | `rg -n -F 'User (spend / environment); Astra (workload)' docs/status/OPEN_USER_DECISIONS_20261022.md` | exit 0 |
| 81 | `rg -n -F 'Supervisor / repository owner controlling the execution host' docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md` | exit 0 |
| 82 | `rg -n -F 'User / repository owner' docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md` | exit 0 |
| 83 | `rg -n -F 'Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.' docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md` | exit 0 |
| 84 | `rg -n -F 'the User/orchestrator owning this loop-proposed node.' docs/status/OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md` | exit 0 |
| 85 | `rg -n -F 'Who decides: the User.' docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md` | exit 0 |
| 86 | `git diff --exit-code 1f01a9321c641c7a7fafa2a33e4350a2fa711730 HEAD -- scripts/check_bcs1_evidence_map.py docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md` | exit 0 |
| 87 | `git show --format=fuller --stat 22df2e96d1a7de4d0de371a1f64776e80af9d999` | exit 0 |
| 88 | `sed -n '1,19p' validation/2026-10-25-plan-register-index-crosswalk-sync/README.md` | exit 0 |
| 89 | `sed -n '69,79p' docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md` | exit 0 |
| 90 | `sed -n '51,61p' docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md` | exit 0 |
| 91 | `sed -n '334p' docs/README.md` | exit 0 |
| 92 | `python3 scripts/check_readiness_evidence_map.py --self-test` | exit 0 |
| 93 | `python3 scripts/check_settlement_evidence_map.py` | exit 0 |
| 94 | `python3 scripts/check_settlement_evidence_map.py --self-test` | exit 0 |
| 95 | `python3 scripts/check_bra_evidence_map.py` | exit 0 |
| 96 | `python3 scripts/check_bra_evidence_map.py --self-test` | exit 0 |
| 97 | `python3 scripts/check_credit_evidence_map.py` | exit 0 |
| 98 | `python3 scripts/check_credit_evidence_map.py --self-test` | exit 0 |
| 99 | `python3 scripts/check_primary_price_fee_evidence_map.py` | exit 0 |
| 100 | `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | exit 0 |
| 101 | `python3 scripts/check_ai_delegation_evidence_map.py` | exit 0 |
| 102 | `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | exit 0 |
| 103 | `python3 scripts/check_lifecycle_adr_evidence_map.py` | exit 0 |
| 104 | `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | exit 0 |
| 105 | `python3 scripts/check_contract_invariants_evidence_map.py` | exit 0 |
| 106 | `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | exit 0 |
| 107 | `python3 scripts/check_toss_card_profile_evidence_map.py` | exit 0 |
| 108 | `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | exit 0 |
| 109 | `python3 scripts/check_bcs1_evidence_map.py` | exit 0 |
| 110 | `python3 scripts/check_bcs1_evidence_map.py --self-test` | exit 0 |
| 111 | `python3 scripts/check_performance_measurement_evidence_map.py` | exit 0 |
| 112 | `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | exit 0 |
| 113 | `python3 scripts/check_feature_semantics_evidence_map.py` | exit 0 |
| 114 | `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | exit 0 |
| 115 | `python3 scripts/check_integration_gate_contract_evidence_map.py` | exit 0 |
| 116 | `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | exit 0 |
| 117 | `python3 scripts/check_evidence_map_rollup.py` | exit 0 |
| 118 | `python3 scripts/check_evidence_map_rollup.py --self-test` | exit 0 |
| 119 | `python3 scripts/check_ci_checker_wiring.py` | exit 0 |
| 120 | `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0 |
| 121 | `python3 scripts/check_stage5_host.py --self-test` | exit 0 |
| 122 | `python3 /tmp/kix_check_closure.py` | exit 0 |
| 123 | `python3 scripts/check_docs_index.py` | exit 0 |
| 124 | `python3 scripts/check_status_register.py` | exit 0 |
| 125 | `git rev-parse origin/main HEAD` | exit 0 |
| 126 | `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 127 | `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0 |
| 128 | `git diff --exit-code origin/main -- reference/v0.3-rc1 runtime .aiops docs/tasks .github scripts sdk docs/contracts` | exit 0 |
| 129 | `git diff --check origin/main...HEAD` | exit 0 |
| 130 | `git diff --check` | exit 0 |
| 131 | `git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md` | exit 1 |
| 132 | `git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md` | exit 1 |
| 133 | `git diff --no-index --check /dev/null validation/2026-10-27-plan-open-decisions-closure-20261027/README.md` | exit 3 |
| 134 | `git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md` | exit 1 |
| 135 | `git diff --no-index --check /dev/null validation/2026-10-27-plan-open-decisions-closure-20261027/README.md` | exit 1 |
| 136 | `git diff --check` | exit 0 |
| 137 | `git status --porcelain --untracked-files=all` | exit 0 |
| 138 | `python3 /tmp/kix_check_closure.py` | exit 0 |
| 139 | `python3 scripts/check_docs_index.py` | exit 0 |
| 140 | `python3 scripts/check_status_register.py` | exit 0 |

## Raw output in execution order

Empty blocks mean no output. Exit codes are recorded separately. Output line-end spaces/tabs are shown as literal \x20/\x09 escapes to preserve them without Markdown trailing whitespace.

### Command 1

```sh
git rev-parse origin/main HEAD
```

Exit: 0

````text
09470db220965390edeecdb75f56f8c827dd15b6
09470db220965390edeecdb75f56f8c827dd15b6
````

### Command 2

```sh
git branch --show-current
```

Exit: 0

````text
agent/kix-plan-plan-open-decisions-closure-20261027
````

### Command 3

```sh
git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: 0

````text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
````

### Command 4

```sh
git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: 0

````text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
````

### Command 5

```sh
git diff --exit-code origin/main -- reference/v0.3-rc1
```

Exit: 0

````text

````

### Command 6

```sh
git log --first-parent --merges --format='%H %s' 22df2e96d1a7de4d0de371a1f64776e80af9d999..HEAD
```

Exit: 0

````text
09470db220965390edeecdb75f56f8c827dd15b6 Merge pull request #313 from SUNBURN-Golden/agent/kix-plan-plan-evidence-map-rollup-check
d2b748aef0c7b4af5bef23c771c6bce22b52905f Merge pull request #312 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-map-offline-closur
e00e68e680d586346abada94500955abfe938ca3 Merge pull request #311 from SUNBURN-Golden/agent/kix-plan-plan-feature-ir-validator-matrix-closure
58dd527ff53097f5231e89f25ebdf3e94586ee65 Merge pull request #310 from SUNBURN-Golden/agent/kix-plan-plan-feature-ir-money-profile-precedence
118fc28862a6828b80166433bac6f5476037629d Merge pull request #309 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-inv3-sensitivit
ae6b905104d0cb2022001fb32ad98b1a6b3046ec Merge pull request #308 from SUNBURN-Golden/agent/kix-plan-plan-perf-harness-map-partial-closure
a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4 Merge pull request #307 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-map-offline-checke
a176c1f22c0af21500cb52a777bc889b808e561c Merge pull request #306 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-20261026-sd
23391ab50e0467bc7b234c55e98614713d531f58 Merge pull request #305 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-contract-clause-ev
22d05a0c82693ad4575a72c2d342b4e47114447f Merge pull request #304 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-bcs1-checke
9fd4d4836ab4d7eb666ebd4ff2ac0708870d7a58 Merge pull request #303 from SUNBURN-Golden/agent/kix-plan-plan-feature-semantics-v1-evidence-map
412e1ed7bc740599227567f60bf315bb7ecab818 Merge pull request #302 from SUNBURN-Golden/agent/kix-plan-plan-rs4-l2-option-impact-inventory
fc11cdf0150e54ed38bb363f2ded7238c48c6e53 Merge pull request #301 from SUNBURN-Golden/agent/kix-plan-plan-ci-checker-wiring-guard
ff1a955815a054f2345a2e06939f2c84bfc29be6 Merge pull request #300 from SUNBURN-Golden/agent/kix-plan-plan-performance-measurement-clause-evid
1f01a9321c641c7a7fafa2a33e4350a2fa711730 Merge pull request #299 from SUNBURN-Golden/agent/kix-plan-plan-bcs1-contract-clause-evidence-map
18aefc8f7c0dd13b7249e0d80304f3b97459fa3a Merge pull request #298 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-20261026-ai
957f75d75ea4854eba117d66d07663133f0b7b2c Merge pull request #297 from SUNBURN-Golden/agent/kix-plan-plan-toss-card-profile-evidence-map
1bb000bd125a1e8ecdd033cea01733d58588199e Merge pull request #296 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-evidence-map
54a785b864d629d623afc36ed807d9daebaf9285 Merge pull request #295 from SUNBURN-Golden/agent/kix-plan-plan-lifecycle-adr-clause-evidence-map
944cb16f3ade5a395c0febe84fd47d5c16dc0fa3 Merge pull request #294 from SUNBURN-Golden/agent/kix-plan-plan-primary-fee-pf-c05-isolation-tests
a38e1679449e74186c5a4e3d19b6cb79f6b791d5 Merge pull request #293 from SUNBURN-Golden/agent/kix-plan-ai-delegation-contract-clause-evidence-m
a0db1e226e27b1c5f60ee938fb528ff795907056 Merge pull request #292 from SUNBURN-Golden/agent/kix-plan-product-contract-map-partial-closure
01f6c04c71dac27fab5d17017f4e837c076218c6 Merge pull request #291 from SUNBURN-Golden/agent/kix-plan-primary-price-fee-contract-clause-eviden
92d08e755dfe362ed224112c8dada6c5fcea17d4 Merge pull request #290 from SUNBURN-Golden/agent/kix-plan-plan-register-index-crosswalk-sync-20261
````

### Command 7

```sh
git show --stat --oneline 09470db220965390edeecdb75f56f8c827dd15b6
```

Exit: 0

````text
09470db Merge pull request #313 from SUNBURN-Golden/agent/kix-plan-plan-evidence-map-rollup-check

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 docs/status/EVIDENCE_MAP_ROLLUP.md                 |  71 ++++
 scripts/check_evidence_map_rollup.py               | 357 +++++++++++++++++++++
 .../README.md                                      | 100 ++++++
 5 files changed, 532 insertions(+)
````

### Command 8

```sh
git show --stat --oneline d2b748aef0c7b4af5bef23c771c6bce22b52905f
```

Exit: 0

````text
d2b748a Merge pull request #312 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-map-offline-closur

 .github/workflows/protocol.yml                     |   1 +
 docs/README.md                                     |   2 +
 .../INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md      |  10 +-
 integration_gate/test_offline_limits.py            | 102 +++++++++
 ...check_integration_gate_contract_evidence_map.py |   5 +-
 scripts/check_openapi_contract.py                  | 190 +++++++++++++++-
 .../README.md                                      | 239 +++++++++++++++++++++
 7 files changed, 540 insertions(+), 9 deletions(-)
````

### Command 9

```sh
git show --stat --oneline e00e68e680d586346abada94500955abfe938ca3
```

Exit: 0

````text
e00e68e Merge pull request #311 from SUNBURN-Golden/agent/kix-plan-plan-feature-ir-validator-matrix-closure

 docs/README.md                                     |   2 +
 docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md   |   6 +-
 .../kix-feature-ir/tests/validator_matrix.rs       | 421 +++++++++++++++++++++
 scripts/check_feature_semantics_evidence_map.py    |   1 +
 .../README.md                                      | 151 ++++++++
 5 files changed, 578 insertions(+), 3 deletions(-)
````

### Command 10

```sh
git show --stat --oneline 58dd527ff53097f5231e89f25ebdf3e94586ee65
```

Exit: 0

````text
58dd527 Merge pull request #310 from SUNBURN-Golden/agent/kix-plan-plan-feature-ir-money-profile-precedence

 docs/README.md                                     |   2 +
 docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md   |   7 +-
 .../crates/kix-feature-ir/tests/schema_bound.rs    | 149 +++++++++++++++++++++
 .../README.md                                      | 134 ++++++++++++++++++
 4 files changed, 290 insertions(+), 2 deletions(-)
````

### Command 11

```sh
git show --stat --oneline 118fc28862a6828b80166433bac6f5476037629d
```

Exit: 0

````text
118fc28 Merge pull request #309 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-inv3-sensitivit

 docs/README.md                                     |   2 +
 docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md    |  10 +-
 .../crates/kix-kernel/tests/contract_invariants.rs | 162 +++++++++++++++++++--
 .../README.md                                      | 149 +++++++++++++++++++
 4 files changed, 303 insertions(+), 20 deletions(-)
````

### Command 12

```sh
git show --stat --oneline ae6b905104d0cb2022001fb32ad98b1a6b3046ec
```

Exit: 0

````text
ae6b905 Merge pull request #308 from SUNBURN-Golden/agent/kix-plan-plan-perf-harness-map-partial-closure

 docs/README.md                                     |   2 +
 .../status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md |  30 +-
 .../crates/kix-kernel/tests/performance_harness.rs | 209 ++++++++++++
 .../crates/kix-kernel/tests/support/perf_probe.rs  |  26 +-
 .../README.md                                      | 373 +++++++++++++++++++++
 5 files changed, 627 insertions(+), 13 deletions(-)
````

### Command 13

```sh
git show --stat --oneline a8bc9e853f3b0d82c5c4ee2d0bb4620ac36662e4
```

Exit: 0

````text
a8bc9e8 Merge pull request #307 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-map-offline-checke

 docs/README.md                                     |   2 +
 .../INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md      |  14 +-
 scripts/check_openapi_contract.py                  | 154 ++++++++++++++-
 .../README.md                                      | 217 +++++++++++++++++++++
 4 files changed, 376 insertions(+), 11 deletions(-)
````

### Command 14

```sh
git show --stat --oneline a176c1f22c0af21500cb52a777bc889b808e561c
```

Exit: 0

````text
a176c1f Merge pull request #306 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-20261026-sd

 docs/README.md                                     |    2 +
 ..._USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md |  186 ++
 .../README.md                                      | 1990 ++++++++++++++++++++
 3 files changed, 2178 insertions(+)
````

### Command 15

```sh
git show --stat --oneline 23391ab50e0467bc7b234c55e98614713d531f58
```

Exit: 0

````text
23391ab Merge pull request #305 from SUNBURN-Golden/agent/kix-plan-plan-integration-gate-contract-clause-ev

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 .../INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md      | 100 ++++
 ...check_integration_gate_contract_evidence_map.py | 507 +++++++++++++++++++++
 .../README.md                                      | 134 ++++++
 5 files changed, 745 insertions(+)
````

### Command 16

```sh
git show --stat --oneline 22d05a0c82693ad4575a72c2d342b4e47114447f
```

Exit: 0

````text
22d05a0 Merge pull request #304 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-bcs1-checke

 docs/README.md                                     |   2 +
 .../OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md  | 403 ++++++++++++++++++++
 .../README.md                                      | 419 +++++++++++++++++++++
 3 files changed, 824 insertions(+)
````

### Command 17

```sh
git show --stat --oneline 9fd4d4836ab4d7eb666ebd4ff2ac0708870d7a58
```

Exit: 0

````text
9fd4d48 Merge pull request #303 from SUNBURN-Golden/agent/kix-plan-plan-feature-semantics-v1-evidence-map

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 docs/status/FEATURE_SEMANTICS_V1_EVIDENCE_MAP.md   |  86 +++++
 scripts/check_feature_semantics_evidence_map.py    | 402 +++++++++++++++++++++
 .../README.md                                      | 133 +++++++
 5 files changed, 625 insertions(+)
````

### Command 18

```sh
git show --stat --oneline 412e1ed7bc740599227567f60bf315bb7ecab818
```

Exit: 0

````text
412e1ed Merge pull request #302 from SUNBURN-Golden/agent/kix-plan-plan-rs4-l2-option-impact-inventory

 docs/README.md                                     |   4 +-
 docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md    | 433 ++++++++++
 .../README.md                                      | 887 +++++++++++++++++++++
 3 files changed, 1323 insertions(+), 1 deletion(-)
````

### Command 19

```sh
git show --stat --oneline fc11cdf0150e54ed38bb363f2ded7238c48c6e53
```

Exit: 0

````text
fc11cdf Merge pull request #301 from SUNBURN-Golden/agent/kix-plan-plan-ci-checker-wiring-guard

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 docs/status/BRA_CONTRACT_EVIDENCE_MAP.md           |   2 +
 docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md    |   2 +
 docs/status/I12_REVIEW_PACK.md                     |   2 +
 docs/status/RS0_REVIEW_PACK.md                     |   2 +
 docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md    |   2 +
 scripts/check_ci_checker_wiring.py                 | 202 +++++++++++++++++
 .../README.md                                      | 247 +++++++++++++++++++++
 9 files changed, 463 insertions(+)
````

### Command 20

```sh
git show --stat --oneline ff1a955815a054f2345a2e06939f2c84bfc29be6
```

Exit: 0

````text
ff1a955 Merge pull request #300 from SUNBURN-Golden/agent/kix-plan-plan-performance-measurement-clause-evid

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 .../status/PERFORMANCE_MEASUREMENT_EVIDENCE_MAP.md |  94 +++++
 .../check_performance_measurement_evidence_map.py  | 411 +++++++++++++++++++++
 .../README.md                                      | 127 +++++++
 5 files changed, 636 insertions(+)
````

### Command 21

```sh
git show --stat --oneline 1f01a9321c641c7a7fafa2a33e4350a2fa711730
```

Exit: 0

````text
1f01a93 Merge pull request #299 from SUNBURN-Golden/agent/kix-plan-plan-bcs1-contract-clause-evidence-map

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md          |  99 +++++
 scripts/check_bcs1_evidence_map.py                 | 430 +++++++++++++++++++++
 .../README.md                                      | 120 ++++++
 5 files changed, 653 insertions(+)
````

### Command 22

```sh
git show --stat --oneline 18aefc8f7c0dd13b7249e0d80304f3b97459fa3a
```

Exit: 0

````text
18aefc8 Merge pull request #298 from SUNBURN-Golden/agent/kix-plan-plan-open-decisions-addendum-20261026-ai

 docs/README.md                                     |   4 +-
 .../OPEN_USER_DECISIONS_20261026_ADDENDUM.md       | 215 +++++++
 .../README.md                                      | 632 +++++++++++++++++++++
 3 files changed, 850 insertions(+), 1 deletion(-)
````

### Command 23

```sh
git show --stat --oneline 957f75d75ea4854eba117d66d07663133f0b7b2c
```

Exit: 0

````text
957f75d Merge pull request #297 from SUNBURN-Golden/agent/kix-plan-plan-toss-card-profile-evidence-map

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 docs/status/PG_TOSS_CARD_PROFILE_EVIDENCE_MAP.md   |  89 ++++
 scripts/check_toss_card_profile_evidence_map.py    | 455 +++++++++++++++++++++
 .../README.md                                      | 129 ++++++
 5 files changed, 677 insertions(+)
````

### Command 24

```sh
git show --stat --oneline 1bb000bd125a1e8ecdd033cea01733d58588199e
```

Exit: 0

````text
1bb000b Merge pull request #296 from SUNBURN-Golden/agent/kix-plan-plan-contract-invariants-evidence-map

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 docs/status/CONTRACT_INVARIANTS_EVIDENCE_MAP.md    |  87 ++++
 scripts/check_contract_invariants_evidence_map.py  | 542 +++++++++++++++++++++
 .../README.md                                      | 105 ++++
 5 files changed, 738 insertions(+)
````

### Command 25

```sh
git show --stat --oneline 54a785b864d629d623afc36ed807d9daebaf9285
```

Exit: 0

````text
54a785b Merge pull request #295 from SUNBURN-Golden/agent/kix-plan-plan-lifecycle-adr-clause-evidence-map

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 docs/status/LIFECYCLE_ADR_CLAUSE_EVIDENCE_MAP.md   |  74 ++++
 scripts/check_lifecycle_adr_evidence_map.py        | 376 +++++++++++++++++++++
 .../README.md                                      | 108 ++++++
 5 files changed, 562 insertions(+)
````

### Command 26

```sh
git show --stat --oneline 944cb16f3ade5a395c0febe84fd47d5c16dc0fa3
```

Exit: 0

````text
944cb16 Merge pull request #294 from SUNBURN-Golden/agent/kix-plan-plan-primary-fee-pf-c05-isolation-tests

 docs/README.md                                     |   2 +
 .../PRIMARY_PRICE_FEE_CONTRACT_EVIDENCE_MAP.md     |  21 +-
 .../test_primary_resale_bps_isolation.py           | 278 +++++++++++++++++++++
 scripts/check_primary_price_fee_evidence_map.py    |  21 +-
 .../README.md                                      | 172 +++++++++++++
 5 files changed, 483 insertions(+), 11 deletions(-)
````

### Command 27

```sh
git show --stat --oneline a38e1679449e74186c5a4e3d19b6cb79f6b791d5
```

Exit: 0

````text
a38e167 Merge pull request #293 from SUNBURN-Golden/agent/kix-plan-ai-delegation-contract-clause-evidence-m

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   4 +
 docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md | 150 ++++++
 scripts/check_ai_delegation_evidence_map.py        | 545 +++++++++++++++++++++
 .../README.md                                      | 198 ++++++++
 5 files changed, 899 insertions(+)
````

### Command 28

```sh
git show --stat --oneline a0db1e226e27b1c5f60ee938fb528ff795907056
```

Exit: 0

````text
a0db1e2 Merge pull request #292 from SUNBURN-Golden/agent/kix-plan-product-contract-map-partial-closure

 docs/README.md                                     |   2 +
 docs/status/BRA_CONTRACT_EVIDENCE_MAP.md           |  15 +-
 docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md    |  14 +-
 docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md    |  18 +-
 .../test_contract_limit_boundaries.py              | 131 ++++++++++
 .../credit_advance_f04/test_credit_catalogue.py    |  33 +++
 .../test_settlement_catalogue.py                   |  63 +++++
 scripts/check_settlement_evidence_map.py           |  15 +-
 .../README.md                                      | 269 +++++++++++++++++++++
 9 files changed, 544 insertions(+), 16 deletions(-)
````

### Command 29

```sh
git show --stat --oneline 01f6c04c71dac27fab5d17017f4e837c076218c6
```

Exit: 0

````text
01f6c04 Merge pull request #291 from SUNBURN-Golden/agent/kix-plan-primary-price-fee-contract-clause-eviden

 .github/workflows/protocol.yml                     |   2 +
 docs/README.md                                     |   2 +
 .../PRIMARY_PRICE_FEE_CONTRACT_EVIDENCE_MAP.md     | 112 ++++++
 scripts/check_primary_price_fee_evidence_map.py    | 431 +++++++++++++++++++++
 .../README.md                                      | 233 +++++++++++
 5 files changed, 780 insertions(+)
````

### Command 30

```sh
git show --stat --oneline 92d08e755dfe362ed224112c8dada6c5fcea17d4
```

Exit: 0

````text
92d08e7 Merge pull request #290 from SUNBURN-Golden/agent/kix-plan-plan-register-index-crosswalk-sync-20261

 docs/DEVELOPMENT_PLAN.md                           |   9 +
 docs/README.md                                     |  18 ++
 docs/status/CURRENT_CAPABILITY_REGISTER.md         |  12 +-
 docs/status/LOOP_NODE_CROSSWALK.md                 |  24 ++
 .../README.md                                      | 241 +++++++++++++++++++++
 5 files changed, 299 insertions(+), 5 deletions(-)
````

### Command 31

```sh
ls durable scripts/stage5_local_check.py validation/2026-10-13-k-stage5-durable-tx
```

Exit: 2

````text
ls: cannot access 'durable': No such file or directory
ls: cannot access 'scripts/stage5_local_check.py': No such file or directory
ls: cannot access 'validation/2026-10-13-k-stage5-durable-tx': No such file or directory
````

### Command 32

```sh
rg -n -A4 SELF_TEST_ONLY scripts/check_ci_checker_wiring.py
```

Exit: 0

````text
26:SELF_TEST_ONLY = {
27-    'check_stage5_host.py':
28-        'CI runner is not the pinned stage-5 host; '
29-        'a plain run would report the runner host',
30-}
--
61:    for name in sorted(scripts - SELF_TEST_ONLY.keys()):
62-        if name not in run:
63-            errors.append('unwired: ' + name)
64-        elif name not in selftest:
65-            errors.append('plain-only: ' + name)
--
68:    for name in sorted(SELF_TEST_ONLY):
69-        if name not in scripts:
70-            errors.append('allowlist names missing script: ' + name)
71-        if name in plain:
72-            errors.append('allowlisted but wired plain: ' + name)
--
196:          % (len(scripts), len(plain), len(selftest), len(SELF_TEST_ONLY),
197-             len(docs), sum(len(CITE.findall(text)) for text in docs.values())))
198-    return 0
199-
200-
````

### Command 33

```sh
ls validation/2026-10-15-rs-4-l2-load
```

Exit: 2

````text
ls: cannot access 'validation/2026-10-15-rs-4-l2-load': No such file or directory
````

### Command 34

```sh
rg -n UNDETERMINED docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md
```

Exit: 0

````text
56:The acceptable load level remains **UNDETERMINED (owner: User)**, verbatim from
61:**UNDETERMINED — Astra (workload)**; this labels missing inputs and assigns no value.
145:| public | 16,384, per §1A | UNDETERMINED — Astra (workload) |
146:| private | 16,384, per §1A | UNDETERMINED — Astra (workload) |
147:| delegated | 16,384, per §1A | UNDETERMINED — Astra (workload) |
228:**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.
241:### Owner and UNDETERMINED items
245:Environment or spend remains with User; any workload change remains with Astra. Host and spend are unresolved; allowed load remains **UNDETERMINED (owner: User)**.
277:**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.
290:### Owner and UNDETERMINED items
294:The window and environment remain with User; any workload change remains with Astra. Allowed load remains **UNDETERMINED (owner: User)**. No reliability, idle-load or duration threshold is supplied.
330:**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.
334:Under the named “public prefix only” sub-variant, private and delegated have no samples in that scope, and the public remainder after the prefix has no data. The cut point is **UNDETERMINED — Astra (workload)**. RR-2, RR-5 and RR-6 lose their cited private measurement path; RS-C14 lacks the private and delegated components plus the unrecorded public remainder. Which public predicates or probes fall after the cut is not determined.
343:### Owner and UNDETERMINED items
347:Scope and prefix cut point remain **UNDETERMINED — Astra (workload)**. Accepting reduced scope is the option’s own “an Astra workload decision”. Environment/spend remains with User; allowed load remains **UNDETERMINED (owner: User)**.
383:**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.
387:The named “private and delegated first” sub-variant includes those paths first; it supplies no actual samples. Whether public follows is **UNDETERMINED — Astra (workload)**: “first” states an order and does not settle final scope. No path is definitively excluded by that phrase alone. If public is omitted, RS-C14’s public component has no data; RR-2, RR-5 and RR-6 remain private-path obligations, not satisfied by naming their path.
396:### Owner and UNDETERMINED items
400:Final scope and ordering details remain **UNDETERMINED — Astra (workload)**. Accepting reduced scope is the option’s own “an Astra workload decision”. Environment/spend remains with User; allowed load remains **UNDETERMINED (owner: User)**.
411:| O3a public prefix only | Private, delegated and public remainder; cut UNDETERMINED — Astra (workload) | RR-2, RR-5, RR-6; RS-C14 private/delegated components and public remainder | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
412:| O3b private and delegated first | Public inclusion UNDETERMINED — Astra (workload) | RS-C14 public component if public omitted; private obligations unchanged | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
418:  Acceptable load stays **UNDETERMINED (owner: User)**; any workload change
````

### Command 35

```sh
rg -n SeededJourney integration_gate
```

Exit: 1

````text

````

### Command 36

```sh
sed -n '87p' docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md
```

Exit: 0

````text
`plan-plan-gate-fsm-seeded-journey-differentia` is **not implemented in this node**. Owner: Supervisor / repository owner controlling the execution host. The [owner-stop addendum](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) records the unresolved authorized host, historical socket denial and unverified candidate identity. This map neither imports that branch nor closes its stop.
````

### Command 37

```sh
git grep -n plan-plan-plan-register-index-sync-20261023 -- ':!docs/status/OPEN_USER_DECISIONS_*'
```

Exit: 0

````text
validation/2026-10-23-owner-stop-handoff-addendum/README.md:61:`/workspace/kix-run/state/plan-plan-plan-register-index-sync-20261023.decision.md`
validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md:498:docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md:42:| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) | User / repository owner | STILL OPEN | — | Owner and options unchanged. #276 delivered `plan-plan-register-index-sync-20261024`; its record names no disposition of this node. See the [#276 record](../../validation/2026-10-24-plan-register-index-sync/README.md). |
validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md:499:docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md:81:- `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition — User / repository owner: [supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023).
validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md:500:docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md:81:| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | User / repository owner | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) |
validation/2026-10-26-plan-open-decisions-addendum-20261026-sd/README.md:1139:42:| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) | User / repository owner | STILL OPEN | — | Owner and options unchanged. #276 delivered `plan-plan-register-index-sync-20261024`; its record names no disposition of this node. See the [#276 record](../../validation/2026-10-24-plan-register-index-sync/README.md). |
````

### Command 38

```sh
sed -n '280,291p' reference/ai_delegation/ai_delegation_mock.py
```

Exit: 0

````text
    def call_tool(self, actor: object, grant_id: object, tool: object, args: object, now: object) -> dict:
        _require(type(actor) is str and actor in self._agents, "UNKNOWN_ACTOR")
        grant_id = _ident(grant_id)
        _require(type(tool) is str, "INVALID_ID")
        if tool in DENYLIST:
            raise AiDelegationError(DENYLIST[tool])
        _require(tool in ALLOWLIST, "TOOL_NOT_ALLOWED")
        now = _logical(now)
        _require(type(args) is dict, "INVALID_ID")
        grant = self._grants.get(grant_id)
        _require(grant is not None, "UNKNOWN_GRANT")
        _require(grant["agent_id"] == actor, "UNKNOWN_ACTOR")
````

### Command 39

```sh
git log --oneline 22df2e9..HEAD -- reference/ai_delegation docs/contracts/AI_DELEGATION_AUTHORITY.md
```

Exit: 0

````text

````

### Command 40

```sh
sed -n '14p' scripts/check_bcs1_evidence_map.py
```

Exit: 0

````text
TEST_FILES = ('runtime/crates/kix-bcs1/src/lib.rs', 'runtime/crates/kix-bcs1/tests/golden_vectors.rs')
````

### Command 41

```sh
git log --oneline 22df2e9..HEAD -- scripts/check_bcs1_evidence_map.py docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md runtime/crates/kix-bcs1
```

Exit: 0

````text
acf8e35 plan-plan-bcs1-contract-clause-evidence-map: Clause-to-test evidence map for CANONICAL_BINARY_BCS_V1 with a stdlib ch
````

### Command 42

```sh
rg -n 'bytes drift|profile_sha256' sdk/compat/verify_compat.mjs
```

Exit: 0

````text
94:    "profile_sha256",
122:  if (typeof manifest.profile_sha256 !== "string" || !HEX64.test(manifest.profile_sha256)) {
123:    errors.push("profile_sha256 drift");
169:      errors.push(`${label} bytes drift`);
191:      errors.push("generator bytes drift");
202:      errors.push("sdk_output bytes drift");
223:          errors.push("extension_profile bytes drift");
235:  if (profileBytes && sha256Hex(profileBytes) !== manifest.profile_sha256) {
236:    errors.push("profile bytes drift");
262:    for (const key of ["commit", "final_commit", "profile_sha256", "source_commit", "source_tree"]) {
352:        errors.push(`vector bytes drift: ${vector.name}`);
````

### Command 43

```sh
ls docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md scripts/check_sdk_compat_manifest_evidence_map.py
```

Exit: 2

````text
ls: cannot access 'docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md': No such file or directory
ls: cannot access 'scripts/check_sdk_compat_manifest_evidence_map.py': No such file or directory
````

### Command 44

```sh
git log --oneline 22df2e9..HEAD -- sdk docs/contracts/sdk
```

Exit: 0

````text

````

### Command 45

```sh
rg -n plan-plan-open-decisions-closure-20261027 .aiops/program.json docs/tasks
```

Exit: 1

````text

````

### Command 46

```sh
rg -n 'UNDETERMINED|STILL OPEN|#290|seeded|Seeded|listener|gate behavior|No .*change|No map' docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md docs/status/EVIDENCE_MAP_ROLLUP.md validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md
```

Exit: 0

````text
validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:70:No bound listener is observed; deployment absence is not runtime acceptance.
validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:84:opened. No Rust paths changed, so Rust builds/tests/Clippy/formatting were not run;
validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:96:  helpers remain raising functions. No server refactor or behavior change.
validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:175:| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md:238:header boundary, and bound-listener observation on an authorized host. These stay
validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md:79:| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md:216:The seeded-journey host stop, User/Astra-owned decisions and capability grades
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:56:The acceptable load level remains **UNDETERMINED (owner: User)**, verbatim from
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:61:**UNDETERMINED — Astra (workload)**; this labels missing inputs and assigns no value.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:145:| public | 16,384, per §1A | UNDETERMINED — Astra (workload) |
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:146:| private | 16,384, per §1A | UNDETERMINED — Astra (workload) |
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:147:| delegated | 16,384, per §1A | UNDETERMINED — Astra (workload) |
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:228:**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:241:### Owner and UNDETERMINED items
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:245:Environment or spend remains with User; any workload change remains with Astra. Host and spend are unresolved; allowed load remains **UNDETERMINED (owner: User)**.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:277:**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:290:### Owner and UNDETERMINED items
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:294:The window and environment remain with User; any workload change remains with Astra. Allowed load remains **UNDETERMINED (owner: User)**. No reliability, idle-load or duration threshold is supplied.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:330:**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:334:Under the named “public prefix only” sub-variant, private and delegated have no samples in that scope, and the public remainder after the prefix has no data. The cut point is **UNDETERMINED — Astra (workload)**. RR-2, RR-5 and RR-6 lose their cited private measurement path; RS-C14 lacks the private and delegated components plus the unrecorded public remainder. Which public predicates or probes fall after the cut is not determined.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:343:### Owner and UNDETERMINED items
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:347:Scope and prefix cut point remain **UNDETERMINED — Astra (workload)**. Accepting reduced scope is the option’s own “an Astra workload decision”. Environment/spend remains with User; allowed load remains **UNDETERMINED (owner: User)**.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:383:**UNDETERMINED — Astra (workload)**. L1 counts are not reused as L2 counts.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:387:The named “private and delegated first” sub-variant includes those paths first; it supplies no actual samples. Whether public follows is **UNDETERMINED — Astra (workload)**: “first” states an order and does not settle final scope. No path is definitively excluded by that phrase alone. If public is omitted, RS-C14’s public component has no data; RR-2, RR-5 and RR-6 remain private-path obligations, not satisfied by naming their path.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:396:### Owner and UNDETERMINED items
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:400:Final scope and ordering details remain **UNDETERMINED — Astra (workload)**. Accepting reduced scope is the option’s own “an Astra workload decision”. Environment/spend remains with User; allowed load remains **UNDETERMINED (owner: User)**.
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:409:| O1 dedicated or quiet host | None excluded; no data acquired here | No path excluded; all four obligations remain open | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:410:| O2 idle builder window | None excluded; no data acquired here | No path excluded; all four obligations remain open | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:411:| O3a public prefix only | Private, delegated and public remainder; cut UNDETERMINED — Astra (workload) | RR-2, RR-5, RR-6; RS-C14 private/delegated components and public remainder | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:412:| O3b private and delegated first | Public inclusion UNDETERMINED — Astra (workload) | RS-C14 public component if public omitted; private obligations unchanged | `rs-4-l3`, `rs-5-decision`, `k-benchmark-reproduction` | User (spend / measurement environment), with Astra for any workload change. |
docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md:418:  Acceptable load stays **UNDETERMINED (owner: User)**; any workload change
docs/status/EVIDENCE_MAP_ROLLUP.md:22:No map's status, owner or grade is changed. No-map reasons report existing
docs/status/EVIDENCE_MAP_ROLLUP.md:23:scope or stops; they close no open decision or UNDETERMINED value.
docs/status/EVIDENCE_MAP_ROLLUP.md:29:| `docs/contracts/ADAPTER_EVENT_IDENTITY.md` | `docs/status/ADAPTER_IDENTITY_EVIDENCE_MAP.md` | `scripts/check_adapter_identity_map.py` | `Counts: CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8` | TM04<br>k1-adapter-event-identity<br>DECISION_REQUIRED · Astra; k-stage5-durable-tx<br>k-stage5-durable-tx<br>DECISION_REQUIRED · Astra<br>DECISION_REQUIRED · Astra; TM04 | none |
docs/status/EVIDENCE_MAP_ROLLUP.md:40:| `docs/contracts/READ_MODEL_QUERIES.md` | none | none | none | none | Waits on `read-model-reference` for the reference module/catalogue work (READ_MODEL_QUERIES.md:25, :29); open values remain UNDETERMINED. |
docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:14:- Revision `plan-plan-integration-gate-map-offline-checke`: closes README table parity and added-command/security self-test gaps; narrows OPTIONS and publicHost gaps with in-memory negatives. [Validation record](../../validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md). No other row or owner changed.
docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:30:| I-GATE-ROUTING | intro | Same 84 commands/path, core 40 via Core.execute, FSM 44 in process on the worker; default state is in memory. | `integration_gate/test_http_gate.py::TransportTests.test_all_forty_commands_have_explicit_rejects`, `integration_gate/test_http_gate.py::TransportTests.test_fsm_commands_match_a_direct_machine_call`, `integration_gate/test_http_gate.py::TransportTests.test_admission_happy_path_over_http` | `integration_gate/openapi_doc.py::validate` | PARTIAL | Minimal comparisons and admission path do not prove seeded journeys or worker ordering; plan-plan-gate-fsm-seeded-journey-differentia stays blocked. | Supervisor / repository owner controlling the execution host |
docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:64:| G-LOOPBACK-BIND | gate | Local bind defaults to IPv4 loopback and port 8765; refuse other hosts; no public DNS/TLS/OAuth/deployment. | `integration_gate/test_http_gate.py::OpenApiAndSchemaTests.test_refuses_non_loopback_bind`, `integration_gate/test_http_gate.py::TransportTests.test_loopback_refusal_still_applies_with_a_readiness_directory`, `integration_gate/test_offline_limits.py::OfflineLimitsTests.test_default_bind_is_loopback_8765_without_binding` | `integration_gate/openapi_doc.py::validate` | PARTIAL | Default host/port shown by argument parsing only; no bound listener observed; deployment absence is not runtime acceptance. | integration_gate maintainer |
docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:87:`plan-plan-gate-fsm-seeded-journey-differentia` is **not implemented in this node**. Owner: Supervisor / repository owner controlling the execution host. The [owner-stop addendum](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) records the unresolved authorized host, historical socket denial and unverified candidate identity. This map neither imports that branch nor closes its stop.
docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md:101:- no gate behavior change; no tests/endpoints/commands added; no contract, protected reference, runtime, task or program edits.
````

### Command 47

```sh
python3 scripts/check_docs_index.py
```

Exit: 0

````text
docs index ok: scanned=279 indexed=244 allowlisted=35
````

### Command 48

```sh
python3 scripts/check_docs_index.py --self-test
```

Exit: 0

````text
self-test: detected removed index link to docs/adr/0001-ktx-authority-commit-recovery.md (not indexed: docs/adr/0001-ktx-authority-commit-recovery.md)
self-test: detected unindexed scanned file docs/status/SELFTEST_UNINDEXED.md (not indexed: docs/status/SELFTEST_UNINDEXED.md)
self-test: detected unindexed validation record validation/SELFTEST_UNINDEXED/README.md (not indexed: validation/SELFTEST_UNINDEXED/README.md)
self-test: detected dropped allowlist entry docs/contracts/openapi/fsm-command-contract.json (not indexed: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected removed scanned file docs/contracts/openapi/fsm-command-contract.json (allowlist names a file outside the scanned set: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected allowlisted entry also index-linked docs/contracts/openapi/fsm-command-contract.json (allowlisted but indexed: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected broken index link docs/status/SELFTEST_MISSING_TARGET.md (broken index link: docs/status/SELFTEST_MISSING_TARGET.md)
self-test: pass
````

### Command 49

```sh
python3 scripts/check_status_register.py
```

Exit: 0

````text
capability register ok: paths=385 ev_ids=15 original32=32
````

### Command 50

```sh
python3 scripts/check_status_register.py --self-test
```

Exit: 0

````text
self-test: detected missing path (path not found: docs/status/NO_SUCH_FILE_9f3a.md)
self-test: detected undefined EV id (undefined evidence id referenced: EV-XXX)
self-test: detected dropped original id (original id E01 appears 0 times as a row key (want 1))
self-test: detected duplicated original id (original id E01 appears 2 times as a row key (want 1))
self-test: pass
````

### Command 51

```sh
python3 /tmp/kix_check_closure.py
```

Exit: 1

````text
rows/status/resolved-by: 7 unique; October 25 open set + A5/BCS1/SD1; all STILL OPEN / none
owners: all 7 exact substrings of holding records
options/recommendations: all 7 copied blocks match holding records verbatim
links/anchors: 40 checked; all exist
Traceback (most recent call last):
  File "/tmp/kix_check_closure.py", line 51, in <module>
    else: assert Path(token).exists(),token
                 ~~~~~~~~~~~~~~~~~~^^
AssertionError: origin/main
````

### Command 52

```sh
python3 /tmp/kix_check_closure.py
```

Exit: 0

````text
rows/status/resolved-by: 7 unique; October 25 open set + A5/BCS1/SD1; all STILL OPEN / none
owners: all 7 exact substrings of holding records
options/recommendations: all 7 copied blocks match holding records verbatim
links/anchors: 40 checked; all exist
backticked repo paths: 11 checked, including 7 explicitly absent/future artifacts (no links to them)
history: all 24 merges scanned; 12 relevant fact rows match PR/full-SHA pairs
index: both new files linked directly
PASS: documentary acceptance checks
````

### Command 53

```sh
rg -n -i 'chosen|selected|approved|adopt' docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md
```

Exit: 0

````text
152:Quoted for reference; no option is endorsed or chosen.
208:  owner, acceptance criterion or protocol command is selected or changed.
````

### Command 54

```sh
python3 scripts/check_status_register.py
```

Exit: 0

````text
capability register ok: paths=385 ev_ids=15 original32=32
````

### Command 55

```sh
python3 scripts/check_status_register.py --self-test
```

Exit: 0

````text
self-test: detected missing path (path not found: docs/status/NO_SUCH_FILE_9f3a.md)
self-test: detected undefined EV id (undefined evidence id referenced: EV-XXX)
self-test: detected dropped original id (original id E01 appears 0 times as a row key (want 1))
self-test: detected duplicated original id (original id E01 appears 2 times as a row key (want 1))
self-test: pass
````

### Command 56

```sh
python3 scripts/check_rs_profile_traceability.py
```

Exit: 0

````text
rs profile traceability ok: blueprint=47 profile=47 expected=47
````

### Command 57

```sh
python3 scripts/check_rs_profile_traceability.py --self-test
```

Exit: 0

````text
self-test: detected removed RS-C01 from profile (missing in profile: RS-C01)
self-test: detected duplicated RS-C01 in profile (duplicated in profile: RS-C01 (2))
self-test: detected removed IM-01 from profile (missing in profile: IM-01)
self-test: detected duplicated IM-01 in profile (duplicated in profile: IM-01 (2))
self-test: detected removed RS-C03 from blueprint (missing in blueprint: RS-C03)
self-test: detected duplicated RS-C03 in blueprint (duplicated in blueprint: RS-C03 (2))
self-test: detected extra ids in profile (extra in profile: RS-C99 (1))
self-test: pass
````

### Command 58

```sh
python3 scripts/check_read_model_source_map.py
```

Exit: 0

````text
read model source map ok: queries=13 anchors=128 catalogues=2 citations=145
````

### Command 59

```sh
python3 scripts/check_read_model_source_map.py --self-test
```

Exit: 0

````text
self-test: detected anchor line moved (A01: reference/booking_resale_admission/mock_gates.py:96 lacks self._shows (token at lines 97,148,170,657,905))
self-test: detected anchor line out of range (A01: reference/booking_resale_admission/mock_gates.py has 936 lines, cited 99999)
self-test: detected anchor token changed (A01: reference/booking_resale_admission/mock_gates.py:97 lacks self._nope)
self-test: detected query row dropped (missing query row: get_show)
self-test: detected query row duplicated (duplicated query row: get_show (2))
self-test: detected unknown query row (unknown query row: get_zilch)
self-test: detected status flipped (status drift for list_shows: declared SOURCE_FOUND but absence anchors remain: A04,A05)
self-test: detected source label on missing query (status drift for list_shows: declared SOURCE_MISSING but `list_shows 원천` anchors exist: A03)
self-test: detected absence anchors dropped (status drift for list_shows: declared SOURCE_MISSING but no def list_shows( absence anchor)
self-test: detected catalogue expectation flipped (catalogue C02: query name get_show must be in docs/contracts/openapi/fsm-command-contract.json commands)
self-test: detected catalogue row dropped (missing catalogue expectation for reference/v0.3-rc1/protocol_contract.json)
self-test: detected rmq cite out of range (citation out of range: docs/contracts/READ_MODEL_QUERIES.md:99999 (405 lines))
self-test: detected blob id mismatch (READ_MODEL_QUERIES.md blob drift: doc cites 0000000000000000000000000000000000000000, actual 06b9ec68f9dc9dd4af4d70c236360be964a84ae1)
self-test: detected cited surface renamed (A06: reference/booking_resale_admission/reservation_fsm.py:705 lacks def view_show()
self-test: detected absent surface added (A04: def list_shows( must not appear in reference/booking_resale_admission/mock_gates.py)
self-test: detected query in core catalogue (catalogue C01: query name now in reference/v0.3-rc1/protocol_contract.json commands: get_show)
self-test: pass
````

### Command 60

```sh
python3 scripts/check_docs_index.py
```

Exit: 0

````text
docs index ok: scanned=279 indexed=244 allowlisted=35
````

### Command 61

```sh
python3 scripts/check_docs_index.py --self-test
```

Exit: 0

````text
self-test: detected removed index link to docs/adr/0001-ktx-authority-commit-recovery.md (not indexed: docs/adr/0001-ktx-authority-commit-recovery.md)
self-test: detected unindexed scanned file docs/status/SELFTEST_UNINDEXED.md (not indexed: docs/status/SELFTEST_UNINDEXED.md)
self-test: detected unindexed validation record validation/SELFTEST_UNINDEXED/README.md (not indexed: validation/SELFTEST_UNINDEXED/README.md)
self-test: detected dropped allowlist entry docs/contracts/openapi/fsm-command-contract.json (not indexed: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected removed scanned file docs/contracts/openapi/fsm-command-contract.json (allowlist names a file outside the scanned set: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected allowlisted entry also index-linked docs/contracts/openapi/fsm-command-contract.json (allowlisted but indexed: docs/contracts/openapi/fsm-command-contract.json)
self-test: detected broken index link docs/status/SELFTEST_MISSING_TARGET.md (broken index link: docs/status/SELFTEST_MISSING_TARGET.md)
self-test: pass
````

### Command 62

```sh
python3 scripts/check_i12_proof_ids.py
```

Exit: 0

````text
i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14
````

### Command 63

```sh
python3 scripts/check_i12_proof_ids.py --self-test
```

Exit: 0

````text
self-test: detected removed P1 heading from proof (missing in proof: P1)
self-test: detected removed A5 row from proof (missing in proof: A5)
self-test: detected removed A9 row from pack (missing in pack: A9)
self-test: detected extra A11 row in pack (extra in pack: A11 (1))
self-test: detected extra P9 heading in proof (extra in proof: P9 (1))
self-test: detected unresolved proof §9 citation in pack (unresolved section reference in pack line 220: proof §9)
self-test: pass
````

### Command 64

```sh
python3 scripts/check_delegation_layer_matrix.py
```

Exit: 0

````text
delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6
````

### Command 65

```sh
python3 scripts/check_delegation_layer_matrix.py --self-test
```

Exit: 0

````text
self-test: detected removed DLG-17 row (missing in matrix: DLG-17)
self-test: detected dangling path (DLG-06: chain citation reference/rights_scale/sui/sources/NO_SUCH_FILE.move does not exist)
self-test: detected dangling symbol (DLG-06: chain citation reference/rights_scale/sui/sources/rights_scale.move::no_such_fn_9f3a is not defined in the file)
self-test: detected duplicated DLG-17 row (duplicated in matrix: DLG-17 (2))
self-test: detected unknown status (DLG-01: unknown status 'SUFFICIENT')
self-test: detected mock test that does not cite the id (DLG-01: mock tests ['test_period_boundaries'] differ from docstring citations ['test_query_does_not_change_state_and_propose_is_a_memo'])
self-test: detected MOCK_ONLY row with a chain citation (DLG-01: MOCK_ONLY needs none in chain and executor cells)
self-test: detected id dropped from the Neither line (gap summary '- Neither:' lists ['DLG-02', 'DLG-03', 'DLG-04', 'DLG-05', 'DLG-07', 'DLG-08', 'DLG-09', 'DLG-10', 'DLG-11', 'DLG-12', 'DLG-14', 'DLG-15', 'DLG-16', 'DLG-17', 'DLG-18', 'DLG-19', 'DLG-21', 'DLG-24', 'DLG-25', 'DLG-27', 'DLG-28', 'DLG-29', 'DLG-30', 'DLG-31', 'DLG-33', 'DLG-34', 'DLG-35', 'DLG-36'] but the table gives ['DLG-01', 'DLG-02', 'DLG-03', 'DLG-04', 'DLG-05', 'DLG-07', 'DLG-08', 'DLG-09', 'DLG-10', 'DLG-11', 'DLG-12', 'DLG-14', 'DLG-15', 'DLG-16', 'DLG-17', 'DLG-18', 'DLG-19', 'DLG-21', 'DLG-24', 'DLG-25', 'DLG-27', 'DLG-28', 'DLG-29', 'DLG-30', 'DLG-31', 'DLG-33', 'DLG-34', 'DLG-35', 'DLG-36'])
self-test: pass
````

### Command 66

```sh
python3 scripts/check_rs_predicate_evidence_map.py
```

Exit: 0

````text
rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2
````

### Command 67

```sh
python3 scripts/check_rs_predicate_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected removed RS-C01 row (missing in map: RS-C01)
self-test: detected duplicated RS-C01 row (duplicated in map: RS-C01 (2))
self-test: detected dangling path (RS-C01: move citation reference/rights_scale/sui/tests/no_such_file.move does not exist)
self-test: detected dangling symbol (RS-C01: move citation reference/rights_scale/sui/tests/predicate_tests.move::no_such_fn_9f3a is not defined in the file)
self-test: detected unknown status (RS-C01: unknown status 'SUFFICIENT')
self-test: detected NOT_COVERED row that carries a citation (RS-C01: NOT_COVERED row carries a citation)
self-test: detected uncited row that is not NOT_COVERED (RS-C13: COVERED_MODEL_OR_MEMORY row has no citation, so it must be NOT_COVERED)
self-test: detected altered test id (RS-C01: test id 'RS-C01-T9' differs from the profile 'RS-C01-T1')
self-test: detected owner not written in the profile (RS-C02: owner part 'Nobody Else' is not written in the profile)
self-test: detected empty missing cell on a PARTIAL row (RS-C07: PARTIAL row must say what is missing)
self-test: detected citation under reference/v0.3-rc1 (RS-C07: python citation reference/v0.3-rc1/x.py is under reference/v0.3-rc1)
self-test: detected split label dropped (RS-C07: split label '(a)' is missing)
self-test: detected misspelled node:test name (RR-4: local citation reference/rights_scale/client/witness-reconstruction.test.mjs::populated_tre is not defined in the file)
self-test: detected wrong counts line (counts line 'Counts: COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=96 NOT_COVERED=0 MEASUREMENT_ONLY=2' differs from the table 'Counts: COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2')
self-test: pass
````

### Command 68

```sh
python3 scripts/check_rs_im_evidence_map.py
```

Exit: 0

````text
rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2
````

### Command 69

```sh
python3 scripts/check_rs_im_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected removed IM-01 row (missing in map: IM-01)
self-test: detected duplicated IM-01 row (duplicated in map: IM-01 (2))
self-test: detected dangling path (IM-01: move citation reference/rights_scale/sui/tests/no_such_file.move does not exist)
self-test: detected dangling symbol (IM-01: move citation reference/rights_scale/sui/tests/predicate_tests.move::no_such_fn_9f3a is not defined in the file)
self-test: detected unknown status (IM-01: unknown status 'SUFFICIENT')
self-test: detected altered treatment word (IM-01: treatment '유지' differs from the profile '변경')
self-test: detected treatment word that is not a profile word (IM-01: treatment 'keep' is not one of the profile words)
self-test: detected NOT_COVERED row that carries a citation (IM-01: NOT_COVERED row carries a citation)
self-test: detected PARTIAL row with an empty missing cell (IM-03: PARTIAL row must say what is missing)
self-test: detected PARTIAL row with an owner the profile does not write (IM-03: owner part 'Nobody Else' is not written in the profile)
self-test: detected citation under reference/v0.3-rc1 (IM-01: python citation reference/v0.3-rc1/x.py is under reference/v0.3-rc1)
self-test: detected UNCHANGED_BY_DESIGN on a changed row (IM-01: UNCHANGED_BY_DESIGN is only for 손대지 않음 rows)
self-test: detected COVERED status on an untouched row (IM-25: a 손대지 않음 row is never COVERED_MODEL_OR_MEMORY)
self-test: detected misspelled node:test name (IM-19: local citation reference/rights_scale/client/witness-reconstruction.test.mjs::populated_tre is not defined in the file)
self-test: detected wrong cell count (IM-01: expected 11 cells, found 12)
self-test: detected wrong counts line (counts line 'Counts: COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=912 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2' differs from the table 'Counts: COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2')
self-test: pass
````

### Command 70

```sh
python3 scripts/check_tl_predicate_evidence_map.py
```

Exit: 0

````text
tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7
````

### Command 71

```sh
python3 scripts/check_tl_predicate_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected removed TK-4 row (missing in map: TK-4)
self-test: detected duplicated TK-4 row (duplicated in map: TK-4 (2))
self-test: detected invented id (invented id: TK-99)
self-test: detected dangling path (TK-4: citation reference/token_reward/no_such_file.py is not an allowed evidence path)
self-test: detected dangling symbol (TK-4: citation reference/token_reward/test_reward_model.py::no_such_fn_9f3a is not defined in the file)
self-test: detected unknown status (TK-4: unknown status 'SUFFICIENT')
self-test: detected uncited row that is not NOT_VERIFIABLE_NO_PACKAGE (V1: HARNESS_AUTHOR_SIDE row has no citation)
self-test: detected empty missing cell (V1: empty missing-or-open cell)
self-test: detected owner not in source (V1: owner 'Nobody Else' not found in docs/blueprints/optional-native-token-v1/README.md)
self-test: detected stale counts line (counts line 'Counts: HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=9924 PARTIAL=7' differs from 'Counts: HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7')
self-test: pass
````

### Command 72

```sh
python3 scripts/check_contract_error_codes.py
```

Exit: 0

````text
contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0
````

### Command 73

```sh
python3 scripts/check_contract_error_codes.py --self-test
```

Exit: 0

````text
self-test: detected removed doc row (SET: INVALID_ID missing in doc)
self-test: detected duplicated doc row (SET: INVALID_ID duplicated in doc (2))
self-test: detected misspelled code (missing side) (SET: INVALID_ID missing in doc)
self-test: detected misspelled code (extra side) (SET: INVALID_IDX is not in the contract table)
self-test: detected stale counts line (counts line 'Counts: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=9199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0' differs from the table 'Counts: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0')
self-test: detected wrong cell count (SET: expected 6 cells, found 7)
self-test: detected unknown status (SET INVALID_ID: unknown status 'SUFFICIENT')
self-test: detected MOCK_INVARIANT row (SET: MOCK_INVARIANT is excluded and must not have a row)
self-test: detected removed raise site (SET INVALID_ID: Raised cites a site but none is derived)
self-test: detected removed asserting test (SET INVALID_ID: Asserted cites a site but none is derived)
self-test: detected Raised cell set to no (SET INVALID_ID: Raised is no but the sources have 2 site(s))
self-test: detected dangling path (SET INVALID_ID: Raised citation reference/settlement_f01_f03/no_such.py::x: file does not exist)
self-test: detected dangling symbol (SET INVALID_ID: Raised citation reference/settlement_f01_f03/mock_settlement.py::no_such_fn_9f3a: symbol is not defined in the file)
self-test: detected citation outside the suite directory (SET INVALID_ID: Raised citation reference/ai_delegation/ai_delegation_mock.py::x is outside the suite directory reference/settlement_f01_f03)
self-test: detected citation under reference/v0.3-rc1 (SET INVALID_ID: Raised citation reference/v0.3-rc1/x.py::y is under reference/v0.3-rc1)
self-test: detected citation that is not a derived site (SET INVALID_ID: Raised citation reference/settlement_f01_f03/mock_settlement.py::MockSettlement.__init__ is not a derived site)
self-test: detected contract table with an added code (SET: ADDED_PROBE_CODE missing in doc)
self-test: detected contract table with a removed heading (SET: heading '## 6. 오류 코드' not found)
self-test: detected COVERED row without an asserting test (SET INVALID_ID: COVERED needs both a raise site and an asserting test)
self-test: detected added code in the BRA-RES contract table (BRA-RES: ADDED_PROBE_CODE missing in doc)
self-test: detected removed raise site on a BRA-RES row (BRA-RES TICKET_NOT_ISSUED: Raised cites a site but none is derived)
self-test: detected citation that is not a derived site on a BRA-RES row (BRA-RES TICKET_NOT_ISSUED: Raised citation reference/booking_resale_admission/resale_fsm.py::ResaleMachine._listing is not a derived site)
self-test: detected missing section 9 raise citation (BRA-RES9 ALREADY_CONSUMED: Raised is no but the sources have 1 site(s))
self-test: detected missing section 9 assertion citation (BRA-RES9 ALREADY_CONSUMED: Asserted is no but the sources have 11 site(s))
self-test: detected added code in the section 9.2 effect column (BRA-RES9: ADDED_PROBE_CODE missing in doc)
self-test: detected added code in the section 9.5 code column (BRA-RES9: ADDED_PROBE_CODE missing in doc)
self-test: detected removed section 9.5 heading (BRA-RES9: heading '### 9.5 정산 게이트' not found)
self-test: detected malformed section 9.5 row (BRA-RES9: heading '### 9.5 정산 게이트': expected 2 cells, found 3)
self-test: detected CLASS_B status on an asserted code with a none note (SET INVALID_ID: CLASS_B row needs a reasoned note)
self-test: detected CLASS_C status on an asserted code (SET INVALID_ID: CLASS_C row is asserted by a test, so it is COVERED)
self-test: pass
````

### Command 74

```sh
python3 scripts/check_adapter_identity_map.py
```

Exit: 0

````text
adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8
````

### Command 75

```sh
python3 scripts/check_adapter_identity_map.py --self-test
```

Exit: 0

````text
self-test: detected removed TransmissionId row (missing in map: TransmissionId)
self-test: detected duplicated TransmissionId row (duplicated in map: TransmissionId (2))
self-test: detected invented id (invented id in map section: FAKE-ID-9f3a)
self-test: detected dangling path (TransmissionId: kernel citation runtime/crates/kix-kernel/tests/no_such.rs does not exist)
self-test: detected dangling symbol (TransmissionId: kernel citation runtime/crates/kix-kernel/src/lib.rs::no_such_fn_9f3a is not defined in the file)
self-test: detected citation in the wrong column (TransmissionId: mock citation runtime/crates/kix-kernel/src/lib.rs is outside the mock column paths)
self-test: detected citation under reference/v0.3-rc1 (TransmissionId: mock citation reference/v0.3-rc1/core.py is under reference/v0.3-rc1)
self-test: detected unknown status (TransmissionId: unknown status 'SUFFICIENT')
self-test: detected status that does not match the cells (RULE-OBSERVE-KEY: status PARTIAL should be CARRIED for these cells)
self-test: detected UNDETERMINED cell with no owner (TransmissionId: profile cell has UNDETERMINED with no owner)
self-test: detected UNDETERMINED owner not in the contract (TransmissionId: owner 'Nobody Else' is not written in the contract)
self-test: detected non-CARRIED row with no owner (TransmissionId: UNDETERMINED row must have an owner)
self-test: detected owner not in the contract (TransmissionId: owner 'Nobody Else' is not written in the contract)
self-test: detected NO_SURFACE row that carries a citation (S4-SOURCE: status NO_SURFACE should be UNDETERMINED for these cells)
self-test: detected missing citation under wrong prefix is not the only bug; free-text-only surface cell (TransmissionId: mock cell is neither none, a citation, nor an owned UNDETERMINED)
self-test: detected wrong counts line (counts line 'Counts: CARRIED=2 PARTIAL=997 NO_SURFACE=0 UNDETERMINED=8' differs from the table 'Counts: CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8')
self-test: detected map cell that cites the missing cell (TransmissionId: ? citation runtime/crates/kix-kernel/src/lib.rs is inside the missing cell)
self-test: detected mutated locked blob (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs (have 2b91c41288b048a233f95b2d4e285b9c262d2333, want 69564b166f0c27f9af5d8422f0a466b18d74c20f))
self-test: detected removed contract anchor (RULE-OBSERVE-KEY: contract anchor 'observe_capture`의 중복 키는 `(provider, account, event_id)`다' is gone)
self-test: pass
````

### Command 76

```sh
python3 scripts/check_v5_transition_evidence_map.py
```

Exit: 0

````text
v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0
````

### Command 77

```sh
python3 scripts/check_v5_transition_evidence_map.py --self-test
```

Exit: 0

````text
self-test: exercised v5 tests bare existing path (alone and mixed lists)
self-test: exercised v5 tests bare missing path (alone and mixed lists)
self-test: exercised v5 tests bare injected path (alone and mixed lists)
self-test: exercised v5 tests empty symbol (alone and mixed lists)
self-test: exercised v5 tests spaces-only symbol (alone and mixed lists)
self-test: exercised v5 tests tabs-only symbol (alone and mixed lists)
self-test: exercised v5 tests missing file (alone and mixed lists)
self-test: exercised v5 tests missing function (alone and mixed lists)
self-test: exercised v5 tests helper function (alone and mixed lists)
self-test: exercised v5 tests invalid test path (alone and mixed lists)
self-test: exercised stop guard bare existing path (alone and mixed lists)
self-test: exercised stop guard bare missing path (alone and mixed lists)
self-test: exercised stop guard bare injected path (alone and mixed lists)
self-test: exercised stop guard empty symbol (alone and mixed lists)
self-test: exercised stop guard spaces-only symbol (alone and mixed lists)
self-test: exercised stop guard tabs-only symbol (alone and mixed lists)
self-test: exercised stop guard missing file (alone and mixed lists)
self-test: exercised stop guard missing function (alone and mixed lists)
self-test: exercised stop guard helper function (alone and mixed lists)
self-test: exercised stop guard invalid test path (alone and mixed lists)
self-test: detected removed TERM row (missing in map: TERM)
self-test: detected duplicated TERM row (duplicated in map: TERM (2))
self-test: detected invented id (invented id in map section: FAKE-ID-9f3a)
self-test: detected dangling path (citation runtime/crates/kix-kernel-v5/tests/no_such.rs::x does not exist)
self-test: detected helper fn cited as a test (citation runtime/crates/kix-kernel-v5/tests/termination.rs::unchanged is not defined in the file)
self-test: detected dangling test symbol (citation runtime/crates/kix-kernel-v5/tests/termination.rs::no_such_test_9f3a is not defined in the file)
self-test: detected test citation in the surface column (TERM: v5 surface citation runtime/crates/kix-kernel-v5/tests/termination.rs is not the v5 lib.rs)
self-test: detected citation under reference/v0.3-rc1 (citation reference/v0.3-rc1/core.py::execute is under reference/v0.3-rc1)
self-test: detected STOPPED row carrying a test (SLOT-RELEASE: status STOPPED should be TESTED for these cells)
self-test: detected TESTED row with none tests (TERM: status TESTED should be OPEN for these cells)
self-test: detected STOPPED without a decision citation (SLOT-RELEASE: STOPPED row must cite the design decision or the implementation record)
self-test: detected STOPPED with a none missing cell (SLOT-RELEASE: STOPPED row must say what is missing or open)
self-test: detected unknown status (TERM: unknown status 'SUFFICIENT')
self-test: detected citation inside the missing cell (TERM: citation docs/contracts/STATE_LIFECYCLE.md::LC-TERM is inside the missing cell)
self-test: detected decision citation to a non-decision file (TERM: decision citation runtime/crates/kix-kernel-v5/src/lib.rs is not a decision document)
self-test: detected open input not in the open-inputs file (open input I99 is not a row of docs/contracts/FIRST_BATCH_OPEN_INPUTS.md)
self-test: detected free-text-only surface cell (TERM: v5 surface is neither no entry point nor a lib.rs citation)
self-test: detected wrong counts line (counts line 'Counts: rows=10 TESTED=99 STOPPED=4 OPEN=0' differs from the table 'Counts: rows=10 TESTED=6 STOPPED=4 OPEN=0')
self-test: detected mutated locked blob (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs (have 2b91c41288b048a233f95b2d4e285b9c262d2333, want 69564b166f0c27f9af5d8422f0a466b18d74c20f))
self-test: detected removed anchor (TERM: contract anchor 'LC-TERM' is gone)
self-test: pass
````

### Command 78

```sh
python3 scripts/check_readiness_evidence_map.py
```

Exit: 0

````text
readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9
````

### Command 79

```sh
rg -n -F 'User / supervisor (build host)' docs/status/OPEN_USER_DECISIONS_20261022.md
```

Exit: 0

````text
73:| `k-stage5-durable-tx` host | User / supervisor (build host) | 채택 backend 위 수락 실행(`durable.test_durable`), 노드 병합 | 선택지 1의 증거 준비 검사기 존재(#227)·CI `--self-test` 배선(#255); 수락 실행·프로비저닝은 없음 |
````

### Command 80

```sh
rg -n -F 'User (spend / environment); Astra (workload)' docs/status/OPEN_USER_DECISIONS_20261022.md
```

Exit: 0

````text
74:| `rs-4-l2` host | User (spend / environment); Astra (workload) | 16,384슬롯 L2 기록 완결 | 경로별 분모 보고서(#230)·host 조건 기록기(#256) 존재; 허용 부하는 `UNDETERMINED` 유지 |
````

### Command 81

```sh
rg -n -F 'Supervisor / repository owner controlling the execution host' docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md
```

Exit: 0

````text
95:- **Decision owner:** Supervisor / repository owner controlling the execution host.
````

### Command 82

```sh
rg -n -F 'User / repository owner' docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md
```

Exit: 0

````text
192:- **Decision owner:** User / repository owner.
````

### Command 83

```sh
rg -n -F 'Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.' docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md
```

Exit: 0

````text
55:  Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.
````

### Command 84

```sh
rg -n -F 'the User/orchestrator owning this loop-proposed node.' docs/status/OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md
```

Exit: 0

````text
224:> **Who decides:** the User/orchestrator owning this loop-proposed node. The
````

### Command 85

```sh
rg -n -F 'Who decides: the User.' docs/status/OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md
```

Exit: 0

````text
83:> Who decides: the User.
````

### Command 86

```sh
git diff --exit-code 1f01a9321c641c7a7fafa2a33e4350a2fa711730 HEAD -- scripts/check_bcs1_evidence_map.py docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md
```

Exit: 0

````text

````

### Command 87

```sh
git show --format=fuller --stat 22df2e96d1a7de4d0de371a1f64776e80af9d999
```

Exit: 0

````text
commit 22df2e96d1a7de4d0de371a1f64776e80af9d999
Merge: c7762c2 ffb0111
Author:     soulbound_jt <justice.parkit@gmail.com>
AuthorDate: Sun Oct 25 17:19:45 2026 +0900
Commit:     GitHub <noreply@github.com>
CommitDate: Sun Oct 25 17:19:45 2026 +0900

    Merge pull request #289 from SUNBURN-Golden/agent/kix-plan-ci-wire-product-contract-evidence-checke
\x20\x20\x20\x20
    [KIX-PLAN-CI-WIRE-PRODUCT-CONTRACT-EVIDENCE-CHECKE] Run the three product-contract evidence-map checkers in the stdlib offline document-check step

 .github/workflows/protocol.yml                     |   6 +
 docs/README.md                                     |   2 +
 docs/status/CURRENT_CAPABILITY_REGISTER.md         |   2 +-
 .../README.md                                      | 205 +++++++++++++++++++++
 4 files changed, 214 insertions(+), 1 deletion(-)
````

### Command 88

```sh
sed -n '1,19p' validation/2026-10-25-plan-register-index-crosswalk-sync/README.md
```

Exit: 0

````text
# Plan, register, index and loop-node crosswalk location sync — 2026-10-25

Node: `plan-plan-register-index-crosswalk-sync-20261`. Source: KIX planner run
1792916405; loop-proposed node, not in `.aiops/program.json`. The supervisor's
node specification and read-only design in the builder prompt are the immutable
task input. No issue or corresponding task document under `docs/tasks/` exists.
`depends_on: []`; audit floor A2; `astra_gate: None`; `user_merge: False`.
This is not ASTRA program mode. Builder-authored documentary evidence only.
Location pointers only: no new approval, no decision text, no grade raise.
Canonical counting remains `DECISION_REQUIRED · Astra`.

## Basis and delivery boundary

Starting branch: `agent/kix-plan-plan-register-index-crosswalk-sync-20261`.
Observed cached `origin/main`, task base and starting HEAD all equal
`22df2e96d1a7de4d0de371a1f64776e80af9d999` (#289); the initial worktree was clean. No cached-base delta.
`git fetch origin main`: NOT_RUN under the supervisor's explicit no-network
instruction, overriding AGENTS §1. Remote freshness remains unverified.
No rebase or base change was made.
````

### Command 89

```sh
sed -n '69,79p' docs/status/BCS1_CONTRACT_EVIDENCE_MAP.md
```

Exit: 0

````text

| FU | Row | Path | Candidate owner |
|---|---|---|---|
| FU-ZERO-ID | S1-VERSION-POSITIVE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-ENVELOPE-TOO-LARGE | S2-ENVELOPE-BOUND | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-BODY-TOO-LARGE-ENCODE | S2-BODY-BOUND-ENCODE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-BODY-TOO-LARGE-DECODE | S2-BODY-BOUND-DECODE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-UTF8-MULTIBYTE | S2-UTF8-MULTIBYTE | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-S08-MOVE-EQUALITY | S5-RUST-MOVE-EQUALITY | runtime/crates/kix-bcs1/tests/golden_vectors.rs | S08 Move/SDK schema owner |
| FU-TRUNCATED-ENVELOPE | S8-G3-TRUNCATED | runtime/crates/kix-bcs1/src/lib.rs | kix-bcs1 maintainer |
| FU-S08-SDK-EQUALITY | S8-MOVE-SDK-EQUALITY | runtime/crates/kix-bcs1/tests/golden_vectors.rs | S08 Move/SDK schema owner |
````

### Command 90

```sh
sed -n '51,61p' docs/status/RS4_L2_DECISION_IMPACT_INVENTORY.md
```

Exit: 0

````text

### B. Decision ownership and open values

Ledger owner (verbatim): **User (spend / measurement environment), with Astra for any workload change.**

The acceptable load level remains **UNDETERMINED (owner: User)**, verbatim from
[host_conditions.py](../../reference/rights_scale/host_conditions.py), basis lines
21–22. No host, load, duration, interval, gap factor or threshold is set here.
Any workload change remains with Astra under the ledger owner sentence.
L2 workload denominators, scope and cut points below are
**UNDETERMINED — Astra (workload)**; this labels missing inputs and assigns no value.
````

### Command 91

```sh
sed -n '334p' docs/README.md
```

Exit: 0

````text
| #289 | `22df2e96d1a7de4d0de371a1f64776e80af9d999` | [ci-wire-product-contract-evidence-checkers](../validation/2026-10-25-ci-wire-product-contract-evidence-checkers/README.md) · [protocol.yml](../.github/workflows/protocol.yml) |
````

### Command 92

```sh
python3 scripts/check_readiness_evidence_map.py --self-test
```

Exit: 0

````text
self-test: baseline supplied map
self-test: synthetic PARTIAL positive control passed
self-test: detected PARTIAL row without an owner (REC-CORE-COMMIT: PARTIAL row must have an owner)
self-test: detected removed RCV-TORN-TAIL row (missing in map: RCV-TORN-TAIL)
self-test: detected duplicated RCV-TORN-TAIL row (duplicated in map: RCV-TORN-TAIL (2))
self-test: detected invented id (invented id in map section: FAKE-ID-9f3a)
self-test: detected dangling path (RCV-TORN-TAIL: readiness.test_conformance_sensitivity citation readiness/test_conformance_sensitivity.py does not exist)
self-test: detected dangling symbol (RCV-TORN-TAIL: readiness.test_faults citation readiness/test_faults.py::no_such_test_9f3a is not defined in the file)
self-test: detected citation in the wrong column (RCV-TORN-TAIL: readiness.test_faults citation readiness/conformance.py is outside the readiness.test_faults column paths)
self-test: detected citation under reference/v0.3-rc1 (RCV-TORN-TAIL: readiness.test_faults citation reference/v0.3-rc1/core.py is under reference/v0.3-rc1)
self-test: detected free-text-only fixture cell (RCV-TORN-TAIL: readiness.conformance cell is neither none nor a citation)
self-test: detected citation inside the missing cell (RCV-TORN-TAIL: ? citation readiness/store.py is inside the missing cell)
self-test: detected unknown status (RCV-TORN-TAIL: unknown status 'SUFFICIENT')
self-test: detected status that does not match the cells (JRN-SINGLE-WRITER: status PARTIAL should be EXERCISED for these cells)
self-test: detected EXERCISED row with no fixture citation (JRN-SINGLE-WRITER: status EXERCISED should be NOT_EXERCISED for these cells)
self-test: detected NOT_EXERCISED row carrying a citation (RCV-TORN-TAIL: status NOT_EXERCISED should be EXERCISED for these cells)
self-test: detected OPEN on a non-designated row (JRN-SINGLE-WRITER: OPEN is reserved for the designated open or held rows)
self-test: detected designated open row reclassified (HOLD-NEW-COMMANDS: EXERCISED row is a designated open row and must carry OPEN)
self-test: detected OPEN row with no owner (OPEN-LENPREFIX-MIDFRAME: OPEN row must have an owner)
self-test: detected owner not written in the owner sources (JRN-SINGLE-WRITER: owner 'Nobody Else' is not written in the owner sources)
self-test: detected EXERCISED row naming a gap (JRN-SINGLE-WRITER: status EXERCISED should be PARTIAL for these cells)
self-test: detected wrong counts line (counts line 'Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=999' differs from the table 'Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9')
self-test: detected dropped banner phrase (banner phrase 'operational count stays 0' is gone)
self-test: detected mutated locked blob (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs (have 2b91c41288b048a233f95b2d4e285b9c262d2333, want 69564b166f0c27f9af5d8422f0a466b18d74c20f))
self-test: detected removed contract anchor (FLAG-PROTOCOL-TRUTH: contract anchor '`protocolTruth` | `false` | 저널 레코드는 프로토콜 명령이나 권위 있는 상태가 아니다' is gone)
self-test: pass
self-test: baseline zero-PARTIAL map
self-test: synthetic PARTIAL positive control passed
self-test: detected PARTIAL row without an owner (REC-CORE-COMMIT: PARTIAL row must have an owner)
self-test: detected removed RCV-TORN-TAIL row (missing in map: RCV-TORN-TAIL)
self-test: detected duplicated RCV-TORN-TAIL row (duplicated in map: RCV-TORN-TAIL (2))
self-test: detected invented id (invented id in map section: FAKE-ID-9f3a)
self-test: detected dangling path (RCV-TORN-TAIL: readiness.test_conformance_sensitivity citation readiness/test_conformance_sensitivity.py does not exist)
self-test: detected dangling symbol (RCV-TORN-TAIL: readiness.test_faults citation readiness/test_faults.py::no_such_test_9f3a is not defined in the file)
self-test: detected citation in the wrong column (RCV-TORN-TAIL: readiness.test_faults citation readiness/conformance.py is outside the readiness.test_faults column paths)
self-test: detected citation under reference/v0.3-rc1 (RCV-TORN-TAIL: readiness.test_faults citation reference/v0.3-rc1/core.py is under reference/v0.3-rc1)
self-test: detected free-text-only fixture cell (RCV-TORN-TAIL: readiness.conformance cell is neither none nor a citation)
self-test: detected citation inside the missing cell (RCV-TORN-TAIL: ? citation readiness/store.py is inside the missing cell)
self-test: detected unknown status (RCV-TORN-TAIL: unknown status 'SUFFICIENT')
self-test: detected status that does not match the cells (JRN-SINGLE-WRITER: status PARTIAL should be EXERCISED for these cells)
self-test: detected EXERCISED row with no fixture citation (JRN-SINGLE-WRITER: status EXERCISED should be NOT_EXERCISED for these cells)
self-test: detected NOT_EXERCISED row carrying a citation (RCV-TORN-TAIL: status NOT_EXERCISED should be EXERCISED for these cells)
self-test: detected OPEN on a non-designated row (JRN-SINGLE-WRITER: OPEN is reserved for the designated open or held rows)
self-test: detected designated open row reclassified (HOLD-NEW-COMMANDS: EXERCISED row is a designated open row and must carry OPEN)
self-test: detected OPEN row with no owner (OPEN-LENPREFIX-MIDFRAME: OPEN row must have an owner)
self-test: detected owner not written in the owner sources (JRN-SINGLE-WRITER: owner 'Nobody Else' is not written in the owner sources)
self-test: detected EXERCISED row naming a gap (JRN-SINGLE-WRITER: status EXERCISED should be PARTIAL for these cells)
self-test: detected wrong counts line (counts line 'Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=999' differs from the table 'Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9')
self-test: detected dropped banner phrase (banner phrase 'operational count stays 0' is gone)
self-test: detected mutated locked blob (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs (have 2b91c41288b048a233f95b2d4e285b9c262d2333, want 69564b166f0c27f9af5d8422f0a466b18d74c20f))
self-test: detected removed contract anchor (FLAG-PROTOCOL-TRUTH: contract anchor '`protocolTruth` | `false` | 저널 레코드는 프로토콜 명령이나 권위 있는 상태가 아니다' is gone)
self-test: pass
````

### Command 93

```sh
python3 scripts/check_settlement_evidence_map.py
```

Exit: 0

````text
settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8
````

### Command 94

```sh
python3 scripts/check_settlement_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected missing clause
self-test: detected new contract heading
self-test: detected removed required heading
self-test: detected duplicate contract heading
self-test: detected duplicate row
self-test: detected invented row
self-test: detected dangling path
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected protected reference path
self-test: detected cross-suite on other row
self-test: detected unlisted credit file
self-test: detected absolute path
self-test: detected parent path
self-test: detected closed policy
self-test: detected unknown owner
self-test: detected missing owner
self-test: detected missing UNDETERMINED
self-test: detected heading drift
self-test: detected row width
self-test: detected unknown status
self-test: detected uncited COVERED
self-test: detected uncited PARTIAL
self-test: detected COVERED gap
self-test: detected PARTIAL missing gap
self-test: detected NOT_COVERED citation
self-test: detected bare citation
self-test: detected stale counts
self-test: detected duplicate counts
self-test: detected missing banner
self-test: detected missing grade banner
self-test: detected ordinary class
self-test: detected invalid Python
self-test: pass (33 negative controls)
````

### Command 95

```sh
python3 scripts/check_bra_evidence_map.py
```

Exit: 0

````text
bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2
````

### Command 96

```sh
python3 scripts/check_bra_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected missing clause
self-test: detected new contract heading
self-test: detected removed required heading
self-test: detected duplicate heading
self-test: detected duplicate row
self-test: detected invented row
self-test: detected dangling path
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected dynamic setattr row
self-test: detected protected path
self-test: detected absolute path
self-test: detected parent path
self-test: detected backslash path
self-test: detected closed open clause
self-test: detected closed options
self-test: detected promoted real gaps
self-test: detected unknown owner
self-test: detected missing owner
self-test: detected empty owner
self-test: detected missing UNDETERMINED
self-test: detected open item missing
self-test: detected open item invented
self-test: detected open item duplicate
self-test: detected open item adopted
self-test: detected open item status
self-test: detected open item owner drift
self-test: detected open item missing owner
self-test: detected open item missing UNDETERMINED
self-test: detected open item row width
self-test: detected open item dangling citation
self-test: detected title drift
self-test: detected row width
self-test: detected unknown status
self-test: detected missing paraphrase
self-test: detected uncited COVERED
self-test: detected uncited PARTIAL
self-test: detected COVERED gap
self-test: detected PARTIAL missing gap
self-test: detected NOT_COVERED missing gap
self-test: detected NOT_COVERED citation
self-test: detected bare citation
self-test: detected stale counts
self-test: detected duplicate counts
self-test: detected stale open-items count
self-test: detected duplicate open-items count
self-test: detected missing banner
self-test: detected missing grade banner
self-test: detected ordinary class
self-test: detected invalid Python
self-test: same-module transitive inheritance pass
self-test: pass (50 negative controls)
````

### Command 97

```sh
python3 scripts/check_credit_evidence_map.py
```

Exit: 0

````text
credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3
````

### Command 98

```sh
python3 scripts/check_credit_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected missing clause
self-test: detected new contract heading
self-test: detected removed required heading
self-test: detected duplicate heading
self-test: detected duplicate row
self-test: detected invented row
self-test: detected dangling path
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected non-test method
self-test: detected protected path
self-test: detected absolute path
self-test: detected parent path
self-test: detected backslash path
self-test: detected closed open clause
self-test: detected closed options
self-test: detected closed policy clause
self-test: detected promoted real gaps
self-test: detected unknown owner
self-test: detected incomplete owners
self-test: detected missing owner
self-test: detected empty owner
self-test: detected missing UNDETERMINED
self-test: detected open item missing
self-test: detected open item invented
self-test: detected open item duplicate
self-test: detected open item adopted
self-test: detected open item status
self-test: detected open item owner drift
self-test: detected open item shortened owner
self-test: detected open item missing owner
self-test: detected open item missing UNDETERMINED
self-test: detected open item row width
self-test: detected open item dangling citation
self-test: detected title drift
self-test: detected row width
self-test: detected unknown status
self-test: detected missing paraphrase
self-test: detected uncited COVERED
self-test: detected uncited PARTIAL
self-test: detected COVERED gap
self-test: detected PARTIAL missing gap
self-test: detected NOT_COVERED missing gap
self-test: detected NOT_COVERED citation
self-test: detected bare citation
self-test: detected stale counts
self-test: detected duplicate counts
self-test: detected stale open-items count
self-test: detected duplicate open-items count
self-test: detected missing banner
self-test: detected missing grade banner
self-test: detected both banners missing
self-test: detected contract policy drift
self-test: detected ordinary class
self-test: detected invalid Python
self-test: direct TestCase selection pass
self-test: pass (55 negative controls)
````

### Command 99

```sh
python3 scripts/check_primary_price_fee_evidence_map.py
```

Exit: 0

````text
primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5
````

### Command 100

```sh
python3 scripts/check_primary_price_fee_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected missing clause
self-test: detected duplicate clause
self-test: detected invented clause
self-test: detected new contract heading
self-test: detected removed PF-C heading
self-test: detected removed numbered heading
self-test: detected duplicate contract heading
self-test: detected title drift
self-test: detected dangling path
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected non-test method
self-test: detected protected path
self-test: detected absolute path
self-test: detected parent path
self-test: detected backslash path
self-test: detected noncanonical path
self-test: detected nested path
self-test: detected non-test file
self-test: detected bare citation
self-test: detected stale counts
self-test: detected duplicate counts
self-test: detected closed PF-C03
self-test: detected closed §4
self-test: detected closed §6
self-test: detected promoted PF-C04
self-test: detected promoted PF-C05
self-test: detected PF-C05 opened
self-test: detected PF-C05 owner drift
self-test: detected PF-C05 missing marker
self-test: detected PF-C owner drift
self-test: detected unknown owner
self-test: detected clause owner drift
self-test: detected missing owner
self-test: detected empty owner
self-test: detected missing open marker
self-test: detected closed chain row
self-test: detected cited chain row
self-test: detected missing chain row
self-test: detected missing chain PF-C05
self-test: detected duplicate chain row
self-test: detected invented chain row
self-test: detected chain owner drift
self-test: detected chain missing marker
self-test: detected chain row width
self-test: detected stale chain count
self-test: detected duplicate chain count
self-test: detected open item owner drift
self-test: detected open item shortened owner
self-test: detected open item status drift
self-test: detected contract status drift
self-test: detected open item title drift
self-test: detected missing open item
self-test: detected duplicate open item
self-test: detected invented open item
self-test: detected O-label order drift
self-test: detected open item missing marker
self-test: detected open item missing owner
self-test: detected cited open item
self-test: detected open item row width
self-test: detected stale open count
self-test: detected duplicate open count
self-test: detected missing contract open item
self-test: detected row width
self-test: detected unknown status
self-test: detected missing paraphrase
self-test: detected uncited COVERED
self-test: detected uncited PARTIAL
self-test: detected COVERED gap
self-test: detected PARTIAL missing gap
self-test: detected NOT_COVERED missing gap
self-test: detected NOT_COVERED citation
self-test: detected missing banner
self-test: detected missing grade banner
self-test: detected ordinary class
self-test: detected invalid Python
self-test: direct TestCase selection pass
self-test: pass (76 negative controls)
````

### Command 101

```sh
python3 scripts/check_ai_delegation_evidence_map.py
```

Exit: 0

````text
ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1
````

### Command 102

```sh
python3 scripts/check_ai_delegation_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected missing clause
self-test: detected duplicate clause
self-test: detected invented clause
self-test: detected clause row width
self-test: detected missing code
self-test: detected duplicate code
self-test: detected invented code
self-test: detected code row width
self-test: detected code order
self-test: detected missing flag
self-test: detected duplicate flag
self-test: detected invented flag
self-test: detected flag row width
self-test: detected flag order
self-test: detected missing item
self-test: detected duplicate item
self-test: detected invented item
self-test: detected item row width
self-test: detected item order
self-test: detected new contract heading
self-test: detected removed heading
self-test: detected duplicate contract heading
self-test: detected title drift
self-test: detected missing paraphrase
self-test: detected dangling path
self-test: detected protected path
self-test: detected absolute path
self-test: detected parent path
self-test: detected backslash path
self-test: detected noncanonical path
self-test: detected nested path
self-test: detected non-test file
self-test: detected unapproved readiness file
self-test: detected dangling symbol
self-test: detected helper symbol
self-test: detected non-test method
self-test: detected bare citation
self-test: detected ordinary class
self-test: detected invalid Python
self-test: detected orphan readiness mixin
self-test: detected stale Counts:
self-test: detected duplicate Counts:
self-test: detected stale Codes:
self-test: detected duplicate Codes:
self-test: detected stale Flags:
self-test: detected duplicate Flags:
self-test: detected stale Open items:
self-test: detected duplicate Open items:
self-test: detected closed §9
self-test: detected promoted §10
self-test: detected clause owner drift
self-test: detected unknown owner
self-test: detected empty owner
self-test: detected missing owner
self-test: detected missing open marker
self-test: detected §3 unknown status
self-test: detected §1 COVERED needs a citation
self-test: detected §3 PARTIAL needs a citation
self-test: detected §1 COVERED gap must be none
self-test: detected §3 PARTIAL needs a named gap
self-test: detected §10 NOT_COVERED needs a named gap
self-test: detected §10 NOT_COVERED evidence must be none
self-test: detected §3 unknown DLG id
self-test: detected §6 must point to all DLG
self-test: detected §3 DLG pointer format
self-test: detected §3 DLG pointer range
self-test: detected §3 DLG pointer duplicate
self-test: detected copied DLG row
self-test: detected missing matrix id
self-test: detected code absent from ECC
self-test: detected constructor exclusion
self-test: detected AID pointer drift
self-test: detected contract flag drift
self-test: detected mock flag drift
self-test: detected execution enabled
self-test: detected open item item title drift
self-test: detected open item item status drift
self-test: detected open item open-item evidence must be none
self-test: detected open item item must remain OPEN
self-test: detected open item OPEN needs an open marker
self-test: detected open item OPEN needs an owner
self-test: detected O8 owner drift
self-test: detected O8 execution posture
self-test: detected missing banner Builder-authored map, not a review or an acceptance
self-test: detected missing banner no grade change
self-test: detected missing banner `delegated_execution_enabled` stays `false`
self-test: transitive TestCase selection and symlink fencing pass
self-test: pass (86 negative controls)
````

### Command 103

```sh
python3 scripts/check_lifecycle_adr_evidence_map.py
```

Exit: 0

````text
lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK
````

### Command 104

```sh
python3 scripts/check_lifecycle_adr_evidence_map.py --self-test
```

Exit: 0

````text
self-test: positive injected citation and 49 negative fixtures passed (memory only)
````

### Command 105

```sh
python3 scripts/check_contract_invariants_evidence_map.py
```

Exit: 0

````text
contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK
````

### Command 106

```sh
python3 scripts/check_contract_invariants_evidence_map.py --self-test
```

Exit: 0

````text
contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only)
````

### Command 107

```sh
python3 scripts/check_toss_card_profile_evidence_map.py
```

Exit: 0

````text
Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK
````

### Command 108

```sh
python3 scripts/check_toss_card_profile_evidence_map.py --self-test
```

Exit: 0

````text
Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only)
````

### Command 109

```sh
python3 scripts/check_bcs1_evidence_map.py
```

Exit: 0

````text
BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17
````

### Command 110

```sh
python3 scripts/check_bcs1_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected missing test citation alone (is not a test function)
self-test: detected missing test citation mixed (is not a test function)
self-test: detected non-test helper alone (is not a test function)
self-test: detected non-test helper mixed (is not a test function)
self-test: detected bare path alone (needs a nonempty test symbol)
self-test: detected bare path mixed (needs a nonempty test symbol)
self-test: detected empty symbol alone (needs a nonempty test symbol)
self-test: detected empty symbol mixed (needs a nonempty test symbol)
self-test: detected blank symbol alone (needs a nonempty test symbol)
self-test: detected blank symbol mixed (needs a nonempty test symbol)
self-test: detected prose after citation alone (bad test-cell grammar)
self-test: detected prose after citation mixed (bad test-cell grammar)
self-test: detected kernel path (outside test paths)
self-test: detected absolute path (not repo-relative)
self-test: detected traversal (not repo-relative)
self-test: detected reference path (forbidden reference)
self-test: detected missing file (file missing)
self-test: detected non-UTF8 file (not UTF-8)
self-test: detected before module (not in mod tests)
self-test: detected after module (not in mod tests)
self-test: detected removed row (missing row)
self-test: detected duplicate row (duplicated row)
self-test: detected invented row (invented row)
self-test: detected row width (expected seven cells)
self-test: detected header (bad table header)
self-test: detected counts (counts mismatch)
self-test: detected duplicate section (expected one section)
self-test: detected FU row removed (follow-up table mismatch)
self-test: detected non-claim removed (missing non-claim)
self-test: detected section field (section/clause mismatch)
self-test: detected OPEN status (bad status)
self-test: detected SUFFICIENT status (bad status)
self-test: detected covered gap (COVERED needs)
self-test: detected covered without tests (COVERED needs)
self-test: detected partial without tests (PARTIAL needs)
self-test: detected partial without gap (PARTIAL needs)
self-test: detected partial without owner (PARTIAL needs)
self-test: detected not covered with tests (NOT_COVERED needs)
self-test: detected FU flipped (must stay NOT_COVERED)
self-test: detected FU tag dropped (missing follow-up tag)
self-test: detected preserved partial citation lost (must stay PARTIAL)
self-test: detected preserved partial promoted (must stay PARTIAL)
self-test: detected bad owner (unknown owner)
self-test: detected empty gap (Gap/Owner must be nonempty)
self-test: detected anchor removed (contract anchor is gone)
self-test: detected new numbered section (unmapped contract section)
self-test: detected contract hex drift (golden constant mismatch)
self-test: detected golden byte drift (golden constant mismatch)
self-test: detected locked-blob drift (locked blob mismatch)
self-test: detected locked-blob drift (locked blob mismatch)
self-test: pass (2 positive controls, 50 negative fixtures)
````

### Command 111

```sh
python3 scripts/check_performance_measurement_evidence_map.py
```

Exit: 0

````text
performance evidence map ok: Counts: rows=42 COVERED=22 PARTIAL=15 NOT_COVERED=2 NOT_RUN=3
````

### Command 112

```sh
python3 scripts/check_performance_measurement_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected fabricated test citation alone (is not a test function)
self-test: detected fabricated test citation mixed (is not a test function)
self-test: detected non-test helper alone (is not a test function)
self-test: detected non-test helper mixed (is not a test function)
self-test: detected bare test path alone (needs a nonempty test symbol)
self-test: detected bare test path mixed (needs a nonempty test symbol)
self-test: detected empty test symbol alone (needs a nonempty test symbol)
self-test: detected empty test symbol mixed (needs a nonempty test symbol)
self-test: detected blank test symbol alone (needs a nonempty test symbol)
self-test: detected blank test symbol mixed (needs a nonempty test symbol)
self-test: detected prose after citation alone (bad test-cell grammar)
self-test: detected prose after citation mixed (bad test-cell grammar)
self-test: detected outside allowed files (outside)
self-test: detected absolute path (not repo-relative)
self-test: detected traversal (not repo-relative)
self-test: detected reference path (forbidden reference)
self-test: detected missing file (file missing)
self-test: detected non-UTF8 file (not UTF-8)
self-test: detected outside allowed files (outside)
self-test: detected absolute path (not repo-relative)
self-test: detected traversal (not repo-relative)
self-test: detected reference path (forbidden reference)
self-test: detected missing file (file missing)
self-test: detected non-UTF8 file (not UTF-8)
self-test: detected source citation (is not a source symbol)
self-test: detected source citation (needs a nonempty source symbol)
self-test: detected source citation (bad source-cell grammar)
self-test: detected source citation (historical file only allowed)
self-test: detected removed row (missing row)
self-test: detected duplicate row (duplicated row)
self-test: detected invented row (invented row)
self-test: detected row width (expected eight cells)
self-test: detected header (bad table header)
self-test: detected counts (counts mismatch)
self-test: detected duplicate map heading (expected one section)
self-test: detected historical phrase (historical reference phrase missing)
self-test: detected historical attribution (historical attribution missing)
self-test: detected non-claim removed (missing non-claim: no product TPS, p99 or failure-rate value)
self-test: detected non-claim removed (missing non-claim: UNDETERMINED (owner: User))
self-test: detected non-claim removed (missing non-claim: no benchmark claim)
self-test: detected non-claim removed (missing non-claim: release probe NOT_RUN)
self-test: detected section field (section/clause mismatch)
self-test: detected empty clause (section/clause mismatch)
self-test: detected OPEN status (bad status)
self-test: detected covered gap (COVERED needs)
self-test: detected covered without tests (COVERED needs)
self-test: detected partial without tests (PARTIAL needs)
self-test: detected partial without gap (PARTIAL needs)
self-test: detected partial without owner (PARTIAL needs)
self-test: detected unknown owner (unknown owner)
self-test: detected empty gap (Gap must be nonempty)
self-test: detected not run with tests (NOT_RUN needs)
self-test: detected not covered with tests (NOT_COVERED needs)
self-test: detected historical row source (historical citation/phrase missing)
self-test: detected pinned status flipped (must stay NOT_RUN)
self-test: detected pinned status flipped (must stay NOT_RUN)
self-test: detected pinned status flipped (must stay NOT_RUN)
self-test: detected pinned status flipped (must stay NOT_COVERED)
self-test: detected anchor removed (contract anchor is gone)
self-test: detected new heading (unmapped contract section)
self-test: detected duplicate heading (duplicated contract section)
self-test: detected missing heading (missing contract section)
self-test: detected locked-blob drift (locked blob mismatch: runtime/crates/kix-kernel/src/lib.rs)
self-test: detected locked-blob drift (locked blob mismatch: runtime/crates/kix-kernel/tests/quarantine_capacity.rs)
self-test: detected example constant drift (example constant mismatch: LOCKED_KERNEL)
self-test: detected example constant drift (example constant mismatch: LOCKED_QUARANTINE)
self-test: pass (2 positive controls, 66 negative fixtures; memory only)
````

### Command 113

```sh
python3 scripts/check_feature_semantics_evidence_map.py
```

Exit: 0

````text
feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17
````

### Command 114

```sh
python3 scripts/check_feature_semantics_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected missing row
self-test: detected duplicate row
self-test: detected invented row
self-test: detected row width
self-test: detected table header
self-test: detected counts
self-test: detected duplicate map heading
self-test: detected section coverage
self-test: detected gate row
self-test: detected fabricated symbol alone
self-test: detected fabricated symbol mixed
self-test: detected non-test helper alone
self-test: detected non-test helper mixed
self-test: detected nested non-test helper alone
self-test: detected nested non-test helper mixed
self-test: detected bare path alone
self-test: detected bare path mixed
self-test: detected empty symbol alone
self-test: detected empty symbol mixed
self-test: detected blank symbol alone
self-test: detected blank symbol mixed
self-test: detected prose alone
self-test: detected prose mixed
self-test: detected absolute path alone
self-test: detected absolute path mixed
self-test: detected traversal alone
self-test: detected traversal mixed
self-test: detected reference path alone
self-test: detected reference path mixed
self-test: detected outside path alone
self-test: detected outside path mixed
self-test: detected missing file
self-test: detected non-UTF8 file
self-test: detected section cell
self-test: detected empty clause
self-test: detected bad status
self-test: detected covered gap
self-test: detected covered owner
self-test: detected covered no tests
self-test: detected partial no tests
self-test: detected partial no gap
self-test: detected partial no owner
self-test: detected uncovered has tests
self-test: detected uncovered no gap
self-test: detected uncovered no owner
self-test: detected unknown owner
self-test: detected empty gap
self-test: detected pinned status X-JOIN-EXEC
self-test: detected pinned owner X-JOIN-EXEC
self-test: detected pinned status X-GROUP-EXEC
self-test: detected pinned owner X-GROUP-EXEC
self-test: detected pinned status X-SORT-EXEC
self-test: detected pinned owner X-SORT-EXEC
self-test: detected pinned status X-AGG-EXEC
self-test: detected pinned owner X-AGG-EXEC
self-test: detected pinned status X-BACKEND-CONFORMANCE
self-test: detected pinned owner X-BACKEND-CONFORMANCE
self-test: detected characterization status S10-LIMITS
self-test: detected characterization owner S10-LIMITS
self-test: detected characterization status S8-F64-TOLERANCE
self-test: detected characterization owner S8-F64-TOLERANCE
self-test: detected class-B citation
self-test: detected class-B citation
self-test: detected non-claim
self-test: detected non-claim
self-test: detected non-claim
self-test: detected non-claim
self-test: detected new heading
self-test: detected duplicate heading
self-test: detected missing heading
self-test: detected unnumbered heading
self-test: detected gate removed
self-test: detected gate reordered
self-test: detected gate anchor drift
self-test: detected anchor drift
self-test: detected locked blob drift
self-test: detected locked blob drift
self-test: pass (77 negative controls, injected positive control)
````

### Command 115

```sh
python3 scripts/check_integration_gate_contract_evidence_map.py
```

Exit: 0

````text
integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1
````

### Command 116

```sh
python3 scripts/check_integration_gate_contract_evidence_map.py --self-test
```

Exit: 0

````text
self-test: detected missing row
self-test: detected duplicate row
self-test: detected invented row
self-test: detected row width
self-test: detected table header
self-test: detected counts
self-test: detected duplicate map heading
self-test: detected section coverage
self-test: detected fabricated method alone
self-test: detected fabricated method mixed
self-test: detected fabricated offline method alone
self-test: detected fabricated offline method mixed
self-test: detected module helper alone
self-test: detected module helper mixed
self-test: detected wrong class alone
self-test: detected wrong class mixed
self-test: detected bare path alone
self-test: detected bare path mixed
self-test: detected empty symbol alone
self-test: detected empty symbol mixed
self-test: detected absolute path alone
self-test: detected absolute path mixed
self-test: detected traversal alone
self-test: detected traversal mixed
self-test: detected backslash path alone
self-test: detected backslash path mixed
self-test: detected reference path alone
self-test: detected reference path mixed
self-test: detected outside path alone
self-test: detected outside path mixed
self-test: detected wrong column alone
self-test: detected wrong column mixed
self-test: detected prose alone
self-test: detected prose mixed
self-test: detected missing file
self-test: detected non-UTF8 file
self-test: detected syntax error
self-test: detected fabricated checker
self-test: detected nested checker
self-test: detected bare checker
self-test: detected checker wrong column
self-test: detected wrapper import removed
self-test: detected section cell
self-test: detected empty clause
self-test: detected bad status
self-test: detected covered gap
self-test: detected covered owner
self-test: detected partial no gap
self-test: detected partial no owner
self-test: detected uncovered has tests
self-test: detected uncovered has checkers
self-test: detected uncovered no gap
self-test: detected uncovered no owner
self-test: detected unknown owner
self-test: detected empty gap
self-test: detected backticks gap
self-test: detected covered no citations
self-test: detected partial no citations
self-test: detected pinned status I-GATE-ROUTING
self-test: detected pinned owner I-GATE-ROUTING
self-test: detected pinned status CHK-HTTP-SUITE
self-test: detected pinned owner CHK-HTTP-SUITE
self-test: detected required citation K-READINESS-FSM-REFUSED
self-test: detected required citation R-7
self-test: detected required citation G-LOOPBACK-BIND
self-test: detected required citation G-NO-PUBLIC
self-test: detected anchor drift
self-test: detected added heading
self-test: detected duplicate heading
self-test: detected read item 7 removed
self-test: detected workflow command missing
self-test: detected open gap not implemented in this node
self-test: detected open gap OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia
self-test: detected open gap owner
self-test: detected non-claim runs only where loopback is permitted
self-test: detected non-claim no production endpoint
self-test: detected non-claim no gate behavior change
self-test: detected non-claim no grade change
self-test: detected locked blob runtime/crates/kix-kernel/src/lib.rs
self-test: detected locked blob runtime/crates/kix-kernel/tests/quarantine_capacity.rs
self-test: detected forbidden import socket
self-test: detected forbidden import subprocess
self-test: detected forbidden import http
self-test: detected forbidden import integration_gate
self-test: detected forbidden from import
self-test: pass (85 negative controls; injected positive and valid status controls)
````

### Command 117

```sh
python3 scripts/check_evidence_map_rollup.py
```

Exit: 0

````text
evidence map roll-up ok: contracts=25; textual index only
````

### Command 118

```sh
python3 scripts/check_evidence_map_rollup.py --self-test
```

Exit: 0

````text
self-test: detected missing contract
self-test: detected stale copied Counts line
self-test: detected Counts disagree with table
self-test: detected missing map path
self-test: detected duplicate contract
self-test: detected non-contract row
self-test: detected missing checker
self-test: detected unlisted status
self-test: detected nonzero unexplained token
self-test: detected duplicate Counts line
self-test: detected owners mismatch
self-test: detected arity mismatch
self-test: detected no-map row without reason
self-test: detected source owner has break
self-test: detected Counts trailing whitespace
self-test: detected missing Status table
self-test: pass (16 negative controls)
````

### Command 119

```sh
python3 scripts/check_ci_checker_wiring.py
```

Exit: 0

````text
ci checker wiring ok: scripts=31 plain=30 self_test=31 self_test_only=1 docs=22 citations=99
````

### Command 120

```sh
python3 scripts/check_ci_checker_wiring.py --self-test
```

Exit: 0

````text
self-test: detected unwired checker
self-test: detected plain-only wiring
self-test: detected unlisted self-test-only checker
self-test: detected missing cited checker
self-test: detected document cites unrun checker
self-test: detected allowlisted script wired plain
self-test: detected allowlisted script missing self-test
self-test: detected missing allowlisted script
self-test: detected workflow invokes missing file
self-test: detected commented-out invocation
self-test: detected no scripts
self-test: detected no invocations
self-test: detected no documents
self-test: pass (13 negative controls)
````

### Command 121

```sh
python3 scripts/check_stage5_host.py --self-test
```

Exit: 0

````text
self-test: caught all prerequisites pass
self-test: caught postgres binary missing
self-test: caught postgres binary not executable
self-test: caught postgres --version exits non-zero
self-test: caught postgres --version times out
self-test: caught wrong upstream version 17.10
self-test: caught wrong version 17.110 (no substring match)
self-test: caught wrong debian revision deb13u2
self-test: caught missing debian revision
self-test: caught trailing suffix on banner
self-test: caught initdb banner mismatches independently
self-test: caught psycopg import fails
self-test: caught psycopg probe times out (error-key dict)
self-test: caught psycopg major version 2
self-test: caught psycopg major version 4
self-test: caught psycopg version unparseable
self-test: caught taskset missing from PATH
self-test: caught ss missing from PATH
self-test: caught core 1 outside affinity mask
self-test: caught affinity API unavailable
self-test: pass
````

### Command 122

```sh
python3 /tmp/kix_check_closure.py
```

Exit: 0

````text
rows/status/resolved-by: 7 unique; October 25 open set + A5/BCS1/SD1; all STILL OPEN / none
owners: all 7 exact substrings of holding records
options/recommendations: all 7 copied blocks match holding records verbatim
links/anchors: 40 checked; all exist
backticked repo paths: 11 checked, including 7 explicitly absent/future artifacts (no links to them)
history: all 24 merges scanned; 12 relevant fact rows match PR/full-SHA pairs
index: both new files linked directly
PASS: documentary acceptance checks
boundary: exactly 3 expected changed paths; branch unchanged
````

### Command 123

```sh
python3 scripts/check_docs_index.py
```

Exit: 0

````text
docs index ok: scanned=279 indexed=244 allowlisted=35
````

### Command 124

```sh
python3 scripts/check_status_register.py
```

Exit: 0

````text
capability register ok: paths=385 ev_ids=15 original32=32
````

### Command 125

```sh
git rev-parse origin/main HEAD
```

Exit: 0

````text
09470db220965390edeecdb75f56f8c827dd15b6
09470db220965390edeecdb75f56f8c827dd15b6
````

### Command 126

```sh
git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: 0

````text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
````

### Command 127

```sh
git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs
```

Exit: 0

````text
69564b166f0c27f9af5d8422f0a466b18d74c20f
b607996c83a119c349f1cc90469ac1ba82764e20
````

### Command 128

```sh
git diff --exit-code origin/main -- reference/v0.3-rc1 runtime .aiops docs/tasks .github scripts sdk docs/contracts
```

Exit: 0

````text

````

### Command 129

```sh
git diff --check origin/main...HEAD
```

Exit: 0

````text

````

### Command 130

```sh
git diff --check
```

Exit: 0

````text

````

### Command 131

```sh
git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md
```

Exit: 1

````text

````

### Command 132

```sh
git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md
```

Exit: 1

````text

````

### Command 133

```sh
git diff --no-index --check /dev/null validation/2026-10-27-plan-open-decisions-closure-20261027/README.md
```

Exit: 3

````text
validation/2026-10-27-plan-open-decisions-closure-20261027/README.md:1818: trailing whitespace.
+\x20\x20\x20\x20
````

### Command 134

```sh
git diff --no-index --check /dev/null docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md
```

Exit: 1

````text

````

### Command 135

```sh
git diff --no-index --check /dev/null validation/2026-10-27-plan-open-decisions-closure-20261027/README.md
```

Exit: 1

````text

````

### Command 136

```sh
git diff --check
```

Exit: 0

````text

````

### Command 137

```sh
git status --porcelain --untracked-files=all
```

Exit: 0

````text
 M docs/README.md
?? docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md
?? validation/2026-10-27-plan-open-decisions-closure-20261027/README.md
````

### Command 138

```sh
python3 /tmp/kix_check_closure.py
```

Exit: 0

````text
rows/status/resolved-by: 7 unique; October 25 open set + A5/BCS1/SD1; all STILL OPEN / none
owners: all 7 exact substrings of holding records
options/recommendations: all 7 copied blocks match holding records verbatim
links/anchors: 40 checked; all exist
backticked repo paths: 11 checked, including 7 explicitly absent/future artifacts (no links to them)
history: all 24 merges scanned; 12 relevant fact rows match PR/full-SHA pairs
index: both new files linked directly
PASS: documentary acceptance checks
boundary: exactly 3 expected changed paths; branch unchanged
````

### Command 139

```sh
python3 scripts/check_docs_index.py
```

Exit: 0

````text
docs index ok: scanned=279 indexed=244 allowlisted=35
````

### Command 140

```sh
python3 scripts/check_status_register.py
```

Exit: 0

````text
capability register ok: paths=385 ev_ids=15 original32=32
````

## Temporary documentary acceptance script

The final script used by `python3 /tmp/kix_check_closure.py`:

```python
from pathlib import Path
import re, subprocess
from urllib.parse import unquote
p=Path('docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md')
s=p.read_text()
section=s.split('## Closure table\n',1)[1].split('\n## Options',1)[0]
rows=[line.split('|')[1:-1] for line in section.splitlines() if re.match(r'^\| (L[12]|A[245]|BCS1|SD1) \|',line)]
ids=[c[0].strip() for c in rows]
old=Path('docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md').read_text()
oldids=set(re.findall(r'^\| ([LA]\d) ·[^\n]*\| STILL OPEN \|',old,re.M))
assert set(ids)==oldids|{'A5','BCS1','SD1'} and len(ids)==7, ids
for cells in rows:
    assert len(cells)==7
    assert cells[4].strip()=='STILL OPEN' and cells[5].strip()=='none'
    target=re.search(r'\]\(([^)#]+)',cells[2])[1]
    source=(p.parent/target).read_text()
    assert cells[3].strip() in source, cells[3]
print('rows/status/resolved-by: 7 unique; October 25 open set + A5/BCS1/SD1; all STILL OPEN / none')
print('owners: all 7 exact substrings of holding records')
# Verify the complete copied option/recommendation blocks, not keywords alone.
ledger=Path('docs/status/OPEN_USER_DECISIONS_20261022.md').read_text().splitlines()
for line in (63,64):
    cells=ledger[line-1].split('|')
    for n in (3,4): assert '> '+cells[n].strip() in s
for filename,start,end in [('OPEN_USER_DECISIONS_20261023_ADDENDUM.md',100,105),('OPEN_USER_DECISIONS_20261023_ADDENDUM.md',197,206),('OPEN_USER_DECISIONS_20261026_ADDENDUM.md',56,61),('OPEN_USER_DECISIONS_20261026_BCS1_ADDENDUM.md',210,221),('OPEN_USER_DECISIONS_20261026_SDK_COMPAT_ADDENDUM.md',85,95)]:
    assert '\n'.join((p.parent/filename).read_text().splitlines()[start-1:end]) in s, filename
print('options/recommendations: all 7 copied blocks match holding records verbatim')
def slug(h):
    return re.sub(r'[^\w\- ]','',h.lower()).replace(' ','-')
links=re.findall(r'\]\(([^)]+)\)',s)
for link in links:
    name,_,anchor=link.partition('#')
    target=(p.parent/unquote(name)).resolve() if name else p.resolve()
    assert target.exists(), link
    if anchor:
        headings=re.findall(r'^#{1,6} (.+)$',target.read_text(),re.M)
        assert unquote(anchor) in [slug(h) for h in headings], (link,headings)
print(f'links/anchors: {len(links)} checked; all exist')
# Backticked repository paths include deliberately absent artifacts and source quotes.
absent={
'durable/','scripts/stage5_local_check.py','validation/2026-10-13-k-stage5-durable-tx/',
'validation/2026-10-15-rs-4-l2-load/','docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md',
'scripts/check_sdk_compat_manifest_evidence_map.py',
'validation/2026-10-23-plan-plan-plan-register-index-sync-20261023/README.md'}
seen=set()
for token in re.findall(r'`([^`\n]+)`',s):
    if token == 'origin/main' or token.startswith(('agent/','/workspace/')) or ' ' in token: continue
    if '/' not in token: continue
    if token.endswith('/**'): assert Path(token[:-3]).exists()
    elif token in absent: assert not Path(token).exists(),token
    else: assert Path(token).exists(),token
    seen.add(token)
assert absent<=seen, absent-seen
print(f'backticked repo paths: {len(seen)} checked, including {len(absent)} explicitly absent/future artifacts (no links to them)')
# Check every PR/SHA pair against first-parent history.
merges=subprocess.check_output(['git','log','--first-parent','--merges','--format=%H %s','22df2e96d1a7de4d0de371a1f64776e80af9d999..HEAD'],text=True)
assert len(merges.splitlines())==24
facts=s.split('## Repository facts in #290–#313\n',1)[1]
prrows=re.findall(r'^\| #(\d+) \| `([0-9a-f]{40})`',facts,re.M)
for pr,sha in prrows: assert re.search(r'^'+sha+r' Merge pull request #'+pr+r' ',merges,re.M)
print(f'history: all 24 merges scanned; {len(prrows)} relevant fact rows match PR/full-SHA pairs')
assert ']('+str(p.relative_to('docs'))+')' in Path('docs/README.md').read_text()
validation='validation/2026-10-27-plan-open-decisions-closure-20261027/README.md'
assert '](../'+validation+')' in Path('docs/README.md').read_text()
print('index: both new files linked directly')
print('PASS: documentary acceptance checks')

expected={
'docs/README.md',
'docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md',
'validation/2026-10-27-plan-open-decisions-closure-20261027/README.md'}
tracked=set(subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())
untracked=set(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],text=True).splitlines())
assert tracked|untracked==expected,(tracked,untracked)
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='agent/kix-plan-plan-open-decisions-closure-20261027'
print('boundary: exactly 3 expected changed paths; branch unchanged')
```

## Temporary workflow-command runner

This reads the existing workflow and runs every command in its offline document step:

```python
from pathlib import Path
from kix_closure_evidence import run
import re
workflow=Path('.github/workflows/protocol.yml').read_text()
block=workflow.split('      - name: Stdlib offline document checks\n',1)[1].split('      - uses:',1)[0]
commands=re.findall(r'^          (python3 .+)$',block,re.M)
assert commands
failed=[]
for command in commands:
    if run(command).returncode: failed.append(command)
print(f'Offline workflow commands: {len(commands)}; failures: {len(failed)}')
assert not failed,failed
```

Command recorder imported by these temporary runners:

```python
import json, subprocess
from pathlib import Path
LOG=Path('/tmp/kix_closure_commands.json')
def run(command):
    result=subprocess.run(command,shell=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    data=json.loads(LOG.read_text()) if LOG.exists() else []
    data.append(dict(command=command,exit=result.returncode,output=result.stdout))
    LOG.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print(f'exit {result.returncode}: {command}\n{result.stdout}')
    return result
```
