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

Implementation head / exact final committed task head: not assigned; this is an
uncommitted worktree patch over `22df2e96d1a7de4d0de371a1f64776e80af9d999`. The supervisor
owns commits, publication and review. No commit, push, reset, PR, issue, comment,
merge, branch/tag mutation or network action was performed. No long job was run
in the background, and no polling or automatic retry was performed.

Exact-head KTX kernel verification and KIX protocol verification run IDs,
status/conclusion: unavailable, NOT_RUN/not queried. No earlier-SHA CI is
transferred. Merge SHA, final-merge blob verification and post-merge main CI:
not applicable. Local READY is builder handoff only; it does not satisfy the
AGENTS §10 merge gate or independent/non-author exact-HEAD review.

## Git-derived merge inventory and complete-clause quotations

The bounded first-parent range `d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313..HEAD`
contains exactly #281–#289. Each merge's first-parent diff identifies the record
below. All merge-commit authors are `soulbound_jt`, obtained with
`git show -s --format=%an <SHA>`; this does not identify GitHub's merged_by.
Each new §5 quote is an exact substring of one physical source-record line at
its merge SHA and at the cutoff; manual clause inspection preserves negation.

| PR | Merge SHA | Author | Record | Complete quoted clause |
|---|---|---|---|---|
| #281 | `0db660a1085ca179c341c89129eeda763977b1fb` | soulbound_jt | [plan-register-index-sync-20261025](../../validation/2026-10-25-plan-register-index-sync-20261025/README.md) | Location pointers only: no new approval, no decision text, no grade raise. |
| #282 | `ff88c441f36cde5b581ba29ce4c46ac47f22b218` | soulbound_jt | [plan-section5-quote-completeness](../../validation/2026-10-25-plan-section5-quote-completeness/README.md) | This is manual documentary interpretation, not an automatic grammar proof. |
| #283 | `fe08e4134b2f2e58f48b636bdae7440d8cdb70dc` | soulbound_jt | [audit15-open-decisions-closure](../../validation/2026-10-25-audit15-open-decisions-closure/README.md) | No owner approval was independently verified here. |
| #284 | `590e544b3d097ba3de2fc573deae43b15bc39773` | soulbound_jt | [audit15-reference-test-sibling-path-guard](../../validation/2026-10-25-audit15-reference-test-sibling-path-guard/README.md) | No commit, push, PR, issue, comment, merge, tag or branch operation is performed. |
| #285 | `c0fc5b4aed4da32284d9879ad21ef6b584db01d2` | soulbound_jt | [settlement-contract-clause-evidence-map](../../validation/2026-10-25-settlement-contract-clause-evidence-map/README.md) | Builder-authored map, not a review or an acceptance; no grade change. |
| #286 | `a329ec07ac52ec15bff6c48079115d81ace5ab67` | soulbound_jt | [bra-contract-clause-evidence-map](../../validation/2026-10-25-bra-contract-clause-evidence-map/README.md) | Builder-authored record, not a review or an acceptance; no grade change. |
| #287 | `53c16b226346f2df824f93a5756a080acd489ec1` | soulbound_jt | [credit-f04-contract-clause-evidence-map](../../validation/2026-10-25-credit-f04-contract-clause-evidence-map/README.md) | no grade change. |
| #288 | `c7762c2724d5d28fd2e5e4f00cc5aae4f1f7908f` | soulbound_jt | [plan-primary-fee-split-offline-differential](../../validation/2026-10-25-plan-primary-fee-split-offline-differential/README.md) | READY here means local builder delivery, not merge-ready. |
| #289 | `22df2e96d1a7de4d0de371a1f64776e80af9d999` | soulbound_jt | [ci-wire-product-contract-evidence-checkers](../../validation/2026-10-25-ci-wire-product-contract-evidence-checkers/README.md) | This is a local builder delivery, not merge-ready or independent A2 review. |

#282 and #283 were reversed in the supplied design's record inventory. Git proves
#282 is quote completeness and #283 is open-decisions closure. The SHA values
were correct; all new pointers use the Git-derived record association. The old
index bullet's “closure at #282” describes that record's observed base, not its
own merge number, and remains unchanged. The #287 quote begins after a semicolon
and retains the complete `no grade change.` clause. No prior §5 row is re-quoted.

## Crosswalk selection and accounting

Use the unchanged normalized literal rule on each record at the cutoff:
``'not in `.aiops/program.json`' in ' '.join(text.split())``. The cutoff is
#289, not this uncommitted record. Existing equivalent statements #264 and #274
remain included. The cutoff has 53 literal matches plus those two equivalents:
55 §1 rows, up from 53 at #280. Nine PR numbers, nine actual merges, two new
selected rows, seven accounted nonmatches, zero absent numbers.

| PR | Selection | Exact selection text / reason |
|---|---|---|
| #281 | Literal, quoting the rule | ``'not in `.aiops/program.json`' in ' '.join(text.split())``; like #210/#272, quoting the phrase qualifies. Node `audit15-plan-register-index-crosswalk-sync-20261`. |
| #289 | Literal | loop-proposed node, not in `.aiops/program.json`. Node `plan-ci-wire-product-contract-evidence-checke`. |
| #282–#288 | Not selected; §2 accounting only | Each record contains neither the literal phrase nor an equivalent explicit statement of absence from the canonical program. All seven SHA/path pairs are retained in the crosswalk. |

`git rev-parse 22df2e96d1a7de4d0de371a1f64776e80af9d999:.aiops/program.json`
is `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`, unchanged from #209/#269/#280.
For #281, the `roadmap-sync` phrase “docs/DEVELOPMENT_PLAN.md header, §1, §5,
§17 and §18” and `k-current-capability-map` phrase “현재 capability/coverage
register” are exact substrings of normalized parsed specs. Their dependency lists
are respectively none and `roadmap-sync`, copied from JSON. No exact first-parent
merge of `agent/kix-roadmap-sync` exists through #289; this is a branch-name
observation, not node acceptance. #289 has no canonical overlap identified by
the builder, following the #170 wiring precedent. Every earlier crosswalk row,
its effect cell, historical accounting and open decision remain byte-identical.

## Complete changed paths

- `docs/DEVELOPMENT_PLAN.md` — nine location rows, map/checker/test/CI pointers.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md` — dated full-SHA basis line;
  EV-SET/EV-BRA/EV-CREDIT fixture pointers, P Wave2 source pointers, map/handoff text.
- `docs/README.md` — nine full-SHA location rows plus this record's index bullet.
- `docs/status/LOOP_NODE_CROSSWALK.md` — #289 basis, two rows, seven accounting entries.
- `validation/2026-10-25-plan-register-index-crosswalk-sync/README.md` — this record.

Removing just the inserted strings restores the exact HEAD bytes of all four
tracked documents. Existing register cells remain unchanged except append-only
fixture/source pointers in those four rows; in particular every separate
coverage/grade cell and the P Wave2 `partial reference/localnet…` cell is unchanged.
No status, owner, approval, policy, decision or canonical-node effect is changed.

## Locked blobs and preserved reference

| Path | Required / before blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Before-work `HEAD:reference/v0.3-rc1` tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Final preservation results are in
the commands table below. The one-time verifier compares tracked historical
bytes, modes and the complete on-disk file set to HEAD. No locked/reference file
is edited or transiently mutated. No new persistent checker/test is introduced;
one-time scripts/logs remain under `/tmp` outside the deliverable.

## Existing coverage mapping (AGENTS §7)

| Requirement | Existing evidence | Initial coverage / action |
|---|---|---|
| Register paths, EV references and original 32 IDs | `scripts/check_status_register.py` and `--self-test` | Sufficiently covered; reused unchanged. |
| Index coverage and broken/allowlisted targets | `scripts/check_docs_index.py` and `--self-test` | Sufficiently covered; reused unchanged. Own record adds one indexed document. |
| Related document/contract evidence maps | `Stdlib offline document checks` in `.github/workflows/protocol.yml` | Sufficiently covered by existing validators; extract and run all 33 commands as-is, sequentially. |
| Exact merge mapping, authors, physical-line quotes, SHA citations | Git history and prior #281/#282 sync/quote records | Partially covered; one-time Git/quote/link assertions and manual complete-clause review for nine new rows. |
| Crosswalk selection, spec/dependency copying and range accounting | Existing literal/equivalent rule, JSON and #281 refresh precedent | Partially covered; one-time cutoff re-evaluation, new rows and seven accounting assertions. |
| No grade/effect changes; insertion-only bytes, locks/reference and scope | HEAD baseline, AGENTS locked blobs | Not covered by doc checkers; one-time byte/cell/path/mode assertions and Git hygiene. |
| New source fixture locations and limits | #285–#289 records, maps/checkers and PF-C01/PF-C02 test modules | Sufficient as location evidence; check paths only, no fresh business/reference suite execution claim. |

## Commands and actual results

Baseline, before edits: register `paths=367 ev_ids=15 original32=32`; index
`scanned=239 indexed=204 allowlisted=35`; both self-tests passed (all exit 0).
Local interpreter: Python 3.13.5; workflow setup pin is 3.12. No interpreter or
dependency install. The foreground runner extracts the exact authoritative
33-command run block, checks the step is unguarded, and executes it using
`bash -e` so a failure stops the block. It does not change the workflow.

| Command from the exact workflow run block | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=240 indexed=205 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; settlement evidence map ok: rows=27 headings=27 citations=106 COVERED=12 PARTIAL=5 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; self-test: pass (31 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=212 COVERED=21 PARTIAL=15 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; credit evidence map ok: rows=22 headings=22 items=5 citations=127 COVERED=13 PARTIAL=5 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; self-test: pass (55 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Other commands actually run (initial inspection, implementation and final checks):

| Command | Actual result |
|---|---|
| `pwd`; `git status --short`; `git branch --show-current`; `git rev-parse origin/main HEAD` | Exit 0; expected worktree/branch, initially clean, cached main and HEAD both `22df2e96d1a7de4d0de371a1f64776e80af9d999`. |
| `git log --first-parent --merges --reverse --format='%H %an %s' d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313..HEAD` | Exit 0; exactly nine merges #281–#289 in order, all authors `soulbound_jt`. #282/#283 record association corrected as above. |
| `git show --format= --name-only --diff-merges=first-parent <merge SHA>`; `git show <SHA>:<record>`; `git show -s --format=%an <merge SHA>` (inline inspection and verifier) | Exit 0; record/artifact paths and physical-line quote provenance confirmed for all nine merges. |
| `git rev-parse HEAD:.aiops/program.json`; `git rev-parse 22df2e96d1a7de4d0de371a1f64776e80af9d999:.aiops/program.json` (second inside verifier) | Exit 0; both `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`. |
| Inline cutoff-tree normalized record selection and JSON/spec inspection | Exit 0; #281/#289 literal, seven nonmatches, 53 literal records at cutoff, two prior equivalent statements; exact specs and dependencies confirmed. |
| `python3 --version` | Exit 0; Python 3.13.5. |
| `python3 /tmp/kix-location-sync-edit.py`; `python3 /tmp/kix-location-sync-record.py` | Exit 0; insertion-only document patch and validation draft created. No protected file modified. |
| `python3 /tmp/kix-location-sync-verify.py` (first run) | Exit 1 in the temporary helper: non-NUL `git ls-tree` quoted a Korean filename, causing `FileNotFoundError`. All four earlier assertion groups had passed. Helper changed to `git ls-tree -r -z`; no repository fix was needed. |
| `python3 /tmp/kix-location-sync-verify.py` (corrected and final rerun) | Exit 0; five assertion groups pass: exact insertion reversal, nine merge/quote/link/basis mappings, four append-only source/fixture cells, crosswalk selection/spec/dependencies/accounting, locks/reference/scope/whitespace. |
| `python3 scripts/check_status_register.py`; `python3 scripts/check_status_register.py --self-test` | Baseline: exit 0, paths=367/EV IDs=15/original32=32, self-test pass. After edit, workflow and final rerun: exit 0, paths=385/15/32, self-test pass. |
| `python3 scripts/check_docs_index.py`; `python3 scripts/check_docs_index.py --self-test` | Baseline: exit 0, scanned=239/indexed=204/allowlisted=35, self-test pass. After edit, workflow and final rerun: exit 0, 240/205/35, self-test pass. |
| `python3 /tmp/kix-location-sync-stdlib.py` | Exit 0; extracts unguarded authoritative block, asserts 33 commands, then runs `bash -ex /tmp/kix-location-sync-stdlib.sh` in foreground. All 33 pass; individual commands and summaries above. Trace/log and parsed observations stay in `/tmp`. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before/after; also verifier) | Exit 0; both required blobs match before and after: `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `b607996c83a119c349f1cc90469ac1ba82764e20`. |
| `git rev-parse HEAD:reference/v0.3-rc1` (before/after) | Exit 0; `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` both times. |
| `git ls-tree -r -z HEAD reference/v0.3-rc1`, `git show HEAD:<path>` and byte/mode/path-set comparisons (inside verifier) | Exit 0; all 108 tracked files and modes plus complete on-disk file set equal HEAD. |
| `git diff --quiet origin/main -- reference/v0.3-rc1` | Exit 0; empty reference diff. |
| `git diff --name-only origin/main -- runtime reference .github .aiops docs/tasks docs/contracts docs/decisions scripts` | Exit 0; empty protected/out-of-scope path diff. |
| `git diff --check` | Exit 0; no whitespace diagnostics. |
| `git diff --no-index --check /dev/null validation/2026-10-25-plan-register-index-crosswalk-sync/README.md` (inside verifier) | Exit 1 for the added-file comparison, with empty stdout/stderr: no whitespace diagnostics. |
| `git status --short --untracked-files=all`; `git diff --stat`; `git diff -- <four tracked documents>` | Exit 0; exactly four modified documents and one new validation record, matching Complete changed paths. |
| `cat`, `sed`, `rg`, `rg --files`, inline stdlib/Git read-only inspection | Governance, README, plan, baselines, authority, task-path list, control-plane pointer/pin, program decisions §5, merged records/maps, checker coverage and both CI definitions inspected. No business suite execution claim. |

After recording these results, the corrected acceptance verifier, both narrow
checkers in plain/self-test modes, lock/reference/scope and whitespace checks
are repeated. There was no repository checker/test failure. Self-tests'
intentionally detected synthetic faults are successful negative controls.


## Findings A/B/C, non-claims and unrun checks

- A: Git-derived location metadata agrees with the merged records. Existing
  document validators are reused; no contract or implementation semantics change.
- B: no new runtime characterization. Existing #278 clock-skew, #280 reward
  fingerprint and product-map class B observations remain in their original
  records with their limits and owners. This sync does not resolve them.
- C: no explicit contract violation found in this documentation scope.

No grade, map status, owner, decision, option, policy value, protocol command,
canonical state/count or operational approval changes. No independent A2 review,
Astra acceptance, clean-room independence, durable/distributed guarantee, bank
exactly-once, chain finality, legal/accounting treatment, performance, production
readiness or complete hosted-workflow pass is claimed.

Cargo tests, Clippy, fmt, KTX heavy steps, Move, ZK, Node, HTTP/readiness and
reference suites: NOT_RUN for these documentation-only paths. Plain stage5 host
evaluation, provisioning, qualification and load measurements: NOT_RUN, matching
the document step's self-test-only host selection. The separate rights-scale
job is not a docs-only local equivalent. No hardware/equipment, money/paid service,
secret/credential, real funds/PG/bank/KYC, public endpoint, Sui testnet/mainnet,
storage engine/R2/replication/consensus, new coin/TIX or production runtime was
needed or used. No STOP condition was encountered.

## Deviations and remaining uncertainty

- Fetch omitted under the explicit no-network instruction; cached main freshness
  remains unverified. No task issue/document is created.
- Corrected the supplied design's #282/#283 record association from local Git;
  no merge SHA changed. The closure-document extra link belongs to #283.
- Earlier documents/rows are preserved, including historical basis and count
  statements. A later sync owns this node's eventual merge row.
- Stale local-only/not-wired wording in maps and checker docstrings remains
  outside this node; #289's actual wiring is linked without rewriting those files.
- Canonical counting remains `DECISION_REQUIRED · Astra`; no decision is supplied.
  Exact-head CI and non-author review remain with the supervisor. Local READY
  means this bounded builder handoff, not merge-ready.
