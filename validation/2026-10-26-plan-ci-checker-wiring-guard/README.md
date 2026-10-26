# plan-plan-ci-checker-wiring-guard

## Identity and base

Node: `plan-plan-ci-checker-wiring-guard`. Issue: none. Depends on: none.
Audit floor A2, `astra_gate: None`, `user_merge: False`.
Source: KIX planner run 1792980988, loop-proposed node, not in
`.aiops/program.json`. Task input is the supervisor's node specification and
read-only design supplied in this session; there is no corresponding task
document under `docs/tasks/`. This is not an ASTRA program-mode session.

- Branch: `agent/kix-plan-plan-ci-checker-wiring-guard`.
- Starting HEAD and observed cached `origin/main`:
  `ff1a955815a054f2345a2e06939f2c84bfc29be6`; starting worktree clean,
  no local base delta. The supervisor prohibits network actions, so
  `git fetch origin main` was not run, overriding AGENTS.md §1 step 1.
  Remote freshness is unverified. No rebase or base change occurred.
- Implementation head and exact final task head: not assigned; delivery is
  uncommitted changes above the starting HEAD. Supervisor owns git/GitHub.
- Merge commit and post-merge main CI run ID/status/conclusion: not applicable.
- Exact-head KTX kernel verification and KIX protocol verification run
  ID/status/conclusion: unavailable, not queried or claimed. Both must be
  completed/success on the eventual published head before merge readiness.

No commit, push, reset, PR, issue, comment, tag/branch mutation, network action,
background job, polling or automatic retry was performed.
READY describes this local builder delivery, not merge readiness or A2 review.

## Locks

`git hash-object` before and after work matches both required blobs:

| Path | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The reference-tree byte comparison and protected-path checks are recorded below.
Final-merge verification is not applicable; no merge took place.

## What this change does

Adds a stdlib-only checker for all regular `scripts/check_*.py` files, requiring
standalone `python3 scripts/check_NAME.py` invocations in protocol.yml both plain
and with `--self-test`. The fixed, reasoned `check_stage5_host.py` exception must
run self-test only because CI is not the pinned stage-5 host. Missing/stale
allowlist entries and workflow invocations of missing scripts also fail.

The checker scans the union of top-level `docs/status/*EVIDENCE_MAP*.md`,
`*MATRIX*.md` and `*REVIEW_PACK*.md`, de-duplicating overlapping matches, and
requires each cited checker basename to exist and appear in the workflow.
Empty script, invocation or document sets fail. It reports deterministic errors
and usage errors exit 2. It uses a textual standalone-command convention;
it does not interpret YAML, shell control flow, step guards or job conditions.

`--self-test` uses a synthetic passing baseline, 13 negative controls and
temporary file fixtures. The controls cover unwired/plain-only/unlisted
self-test-only scripts, missing/unrun citations, a plain-wired stage-5 entry,
missing stage-5 self-test/file, a workflow invoking a missing file, a commented
invocation and each empty-set sanity check. File fixtures check all three doc
globs, their overlap, unrelated-doc exclusion and regular-file selection.

Exactly two lines wire the new checker into the existing unguarded stdlib
offline step, before stage-5. Seven dated one-line amendments preserve the old
sentences as historical observations: three product maps cite #289, two I12
amendments cite #199 and two RS0 amendments cite #170. No other cell, grade,
status, owner, workflow line, contract or runtime behavior changes.

## Changed paths

| Path | Change |
|---|---|
| `scripts/check_ci_checker_wiring.py` | New wiring/citation guard and synthetic self-test. |
| `.github/workflows/protocol.yml` | Two added commands in the existing stdlib step. |
| `docs/status/SETTLEMENT_CONTRACT_EVIDENCE_MAP.md` | One amendment paragraph citing #289. |
| `docs/status/BRA_CONTRACT_EVIDENCE_MAP.md` | One amendment paragraph citing #289. |
| `docs/status/CREDIT_F04_CONTRACT_EVIDENCE_MAP.md` | One amendment paragraph citing #289. |
| `docs/status/I12_REVIEW_PACK.md` | Two amendment bullets citing #199. |
| `docs/status/RS0_REVIEW_PACK.md` | Two amendment bullets citing #170. |
| `docs/README.md` | One validation index bullet and separating blank line. |
| `validation/2026-10-26-plan-ci-checker-wiring-guard/README.md` | This execution record. |

## Existing coverage mapping

| Requirement | Coverage before this node | Evidence / addressed gap |
|---|---|---|
| Every checker wired plain and self-test, with stage-5 exception | Partially covered: existing workflow commands and manual inspection | No existing checker enforces the complete set; new pure checks and synthetic negative controls address that gap. |
| Evidence-map/matrix/review-pack checker citations exist and run | Not covered as a global rule | Existing per-map checkers check map-specific structure and test citations; new guard checks checker citations against files and workflow. |
| Five amended documents retain structure and evidence labels | Sufficiently covered | Existing `check_settlement_evidence_map.py`, `check_bra_evidence_map.py`, `check_credit_evidence_map.py`, `check_i12_proof_ids.py`, `check_rs_profile_traceability.py`, each plain/self-test; rerun without duplicate tests. |
| Validation record indexed | Sufficiently covered | Existing `check_docs_index.py` plain/self-test; baseline scanned=258 indexed=223 allowlisted=35. |
| Workflow/amendment scope and protected bytes | Partially covered by git diff and locked-blob checks | Explicit additions-only comparison and reference Git-blob byte comparison recorded below. |
| Exact-head KTX and KIX CI acceptance | Not covered in this session | Supervisor must publish, obtain non-author review and verify eventual exact-head CI. |

## Commands and results

Commands run from the repository root with Python 3.13.5. The narrow run precedes
the full stdlib step (one subprocess per workflow command, in workflow order),
followed by the OpenAPI, integration-gate and SDK checker pairs. Actual exit
codes and final output lines are recorded below.

The initial new-checker plain/self-test pair exited 0 before this run,
reporting 28 scripts and `self-test: pass (13 negative controls)`.
All 14 narrow invocations and 49 stdlib-step commands exited 0.
The invalid-argument CLI control exited 2 with its usage message.
OpenAPI and integration-gate checker pairs exited 0. The SDK plain
invocation initially exited 1 because system Node 20.19.2 does not
match the Node 24 pin. An existing local Node 24.19.0 was selected
via PATH, and both SDK invocations then exited 0. No download, pin
change or checker change was needed. No full-step rerun was needed
because no source changed in resolving this environment mismatch.

| Command | Result |
|---|---|
| `python3 scripts/check_ci_checker_wiring.py --invalid` | Exit 2. `usage: check_ci_checker_wiring.py [--self-test]` |
| `python3 scripts/check_status_register.py` | Exit 0. `capability register ok: paths=385 ev_ids=15 original32=32` |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. `rs profile traceability ok: blueprint=47 profile=47 expected=47` |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145` |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_docs_index.py` | Exit 0. `docs index ok: scanned=259 indexed=224 allowlisted=35` |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14` |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0. `delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6` |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0. `rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2` |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0. `rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2` |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0. `tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7` |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_contract_error_codes.py` | Exit 0. `contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0` |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0. `adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8` |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0. `v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0` |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0. `readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9` |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0. `settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8` |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0. `self-test: pass (33 negative controls)` |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0. `bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2` |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0. `self-test: pass (50 negative controls)` |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0. `credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3` |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0. `self-test: pass (55 negative controls)` |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0. `primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5` |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0. `self-test: pass (76 negative controls)` |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0. `ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1` |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0. `self-test: pass (86 negative controls)` |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0. `lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK` |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0. `self-test: positive injected citation and 49 negative fixtures passed (memory only)` |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0. `contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK` |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0. `contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only)` |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0. `Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK` |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0. `Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only)` |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0. `BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17` |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0. `self-test: pass (2 positive controls, 50 negative fixtures)` |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0. `performance evidence map ok: Counts: rows=42 COVERED=17 PARTIAL=20 NOT_COVERED=2 NOT_RUN=3` |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0. `self-test: pass (2 positive controls, 66 negative fixtures; memory only)` |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0. `ci checker wiring ok: scripts=28 plain=27 self_test=28 self_test_only=1 docs=19 citations=25` |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0. `self-test: pass (13 negative controls)` |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_openapi_contract.py` | Exit 0. `openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff` |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0. `integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false` |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0. `self-test: pass` |
| `python3 scripts/check_sdk_client.py` | Exit 1. `node 20.19.2 does not match toolchains.json nodeMajor 24` |
| `PATH=/workspace/toolchain/node-v24.19.0-linux-x64/bin:$PATH node --version` | Exit 0. `v24.19.0` |
| `PATH=/workspace/toolchain/node-v24.19.0-linux-x64/bin:$PATH python3 scripts/check_sdk_client.py` | Exit 0. `sdk client pin ok: commands=84 node=24.19.0 sourceSha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e` |
| `PATH=/workspace/toolchain/node-v24.19.0-linux-x64/bin:$PATH python3 scripts/check_sdk_client.py --self-test` | Exit 0. `self-test: pass` |

## Other verification

| Command | Actual result |
|---|---|
| `git rev-parse HEAD origin/main` | Exit 0; both `ff1a955815a054f2345a2e06939f2c84bfc29be6`. |
| `git branch --show-current` | Exit 0; `agent/kix-plan-plan-ci-checker-wiring-guard`. |
| `python3 --version` | Exit 0; Python 3.13.5. The workflow configures 3.12 after the stdlib step; the new checker uses stdlib features available in 3.12. |
| `git log --first-parent --oneline -S check_i12_proof_ids.py -- .github/workflows/protocol.yml` | Exit 0; `624b28d Merge pull request #199`. |
| `git log --first-parent --oneline -S check_rs_profile_traceability.py -- .github/workflows/protocol.yml` | Exit 0; `5e8ee3f Merge pull request #170`. |
| `git log --first-parent --oneline -S check_settlement_evidence_map.py -- .github/workflows/protocol.yml` | Exit 0; `22df2e9 Merge pull request #289`. |
| `python3 scripts/check_docs_index.py` before edits | Exit 0; `docs index ok: scanned=258 indexed=223 allowlisted=35`. |
| `python3 /tmp/kix_ci_wiring_checks.py` | Initial driver exited 1 at the SDK Node-version mismatch; all 14 narrow commands, the CLI usage control, 49 stdlib commands and four OpenAPI commands had the expected exits. Full subprocess output captured in `/tmp/kix_ci_wiring_results.json`; table above records summaries. |
| `python3 /tmp/kix_ci_wiring_finish_checks.py` | Exit 0; local Node 24.19.0 selected, SDK plain/self-test pass, actual command table rendered. |
| `python3 /tmp/kix_ci_wiring_scope.py` | Exit 0; exactly two workflow additions, two additions/no removals per amended document, seven correctly dated/cited amendments, exact index bullet, exactly nine authorized changed paths. All 108 reference files match `origin/main` Git blobs byte-for-byte; no extra files. |
| `git diff -U0 -- .github/workflows/protocol.yml` | Exit 0; sole hunk `@@ -256,0 +257,2 @@ jobs:` adds only the new plain/self-test commands. |
| `git diff --numstat` | Exit 0; `2 0` for workflow, docs index and each of the five amended documents. The two new files are untracked and therefore absent from this diff statistic. |
| `rg -n 'Amendment 2026-10-26' docs/status/{SETTLEMENT_CONTRACT_EVIDENCE_MAP,BRA_CONTRACT_EVIDENCE_MAP,CREDIT_F04_CONTRACT_EVIDENCE_MAP,I12_REVIEW_PACK,RS0_REVIEW_PACK}.md` | Exit 0; seven hits, distributed 1/1/1/2/2. |
| `git diff --quiet origin/main -- runtime .aiops reference/v0.3-rc1 docs/tasks docs/contracts docs/decisions` | Exit 0; protected paths unchanged. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` before/after | Exit 0; both match the full required hashes in Locks. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git status --short --untracked-files=all` | Exit 0; seven modified and two new files, exactly as listed in Changed paths. |

The scope helper uses `git show origin/main:<path>` and exact text comparisons
to verify the two workflow lines and index bullet. It uses `difflib.unified_diff`
to reject any removed document line or unexpected addition. It reads
`git ls-tree -r -z origin/main -- reference/v0.3-rc1` and compares every file's
bytes with `git cat-file blob <blob>`, then checks the filesystem path set for
extras. It compares the union of `git diff --name-only origin/main` and
`git ls-files --others --exclude-standard` against the nine-path allowlist.
The temporary drivers are local execution helpers, not repository deliverables.

After completing this record, the docs-index plain/self-test pair, wiring guard,
scope helper, whitespace/protected-path checks and both locked hashes were
checked again successfully; no implementation changed after the full run.

## CI classification note

The workflow and script changes are not documentation-only under the repository
classifiers, so the eventual hosted delivery requires full verification. The
stdlib step remains unguarded and stage-5 stays self-test-only. Local results
are not exact-head CI and do not transfer older CI results to a new head.
The supervisor must record the eventual exact-head KTX and KIX run IDs,
statuses and conclusions outside a follow-up evidence-only commit (§§10–11).

Cargo tests, Clippy, rustfmt, Move, ZK/localnet and npm suites were not run:
no Rust, reference or SDK source changed. The closest local equivalents for
the touched paths are the full stdlib document step and all other checker
pairs above, per the supplied design. No network or external runtime was used.

## Contract findings

No new explicit contract violation or contract-undefined characterization was
found. Existing document gaps, statuses, owners and OPEN/UNDETERMINED items are
unchanged. No runtime behavior was exercised or reclassified.

## Non-claims, residuals and deviations

- No grade, review, acceptance, legal/accounting treatment, production readiness,
  durability, distributed fencing, bank exactly-once or chain finality claim.
  No real funds, PG/bank/KYC calls, public endpoint, Sui testnet/mainnet, new
  coin/TIX module, R2, storage engine, secrets or production runtime was needed.
- A pass establishes textual wiring and checker-file/citation consistency;
  it does not prove execution under every workflow condition or semantic
  adequacy of the checker/test assertions. The new self-tests are builder-authored
  synthetic controls, not independent verification.
- The settlement, BRA and credit checker docstrings still describe their original
  local-only node scope. The capability register's checker list remains manual
  and can drift; both are outside this node's correction boundary.
- The seven amendments supersede only the historical wiring statements; they
  preserve each original sentence and every other cell and status. Historical
  validation records remain byte-identical.
- Execution deviations: fetch/GitHub actions were omitted under the supervisor's
  explicit prohibition; exact-head CI and remote freshness remain unverified.
  SDK verification required the existing local Node 24 on PATH after an initial
  Node 20 mismatch. No implementation-plan deviation or User decision needed.
