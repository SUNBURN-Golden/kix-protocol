# Open-decisions closure validation — 2026-10-23

Node: `audit14-audit14-open-decisions-closure-addendum`. Source: KIX audit #14,
the supervisor-supplied node specification and read-only design plan. Issue:
none; dependencies: none; audit floor A2; `astra_gate: None`, `user_merge: False`.
Not ASTRA program mode. No node-specific task document exists; the supplied
prompt is the immutable task input. Builder-authored documentary evidence,
not independent review, an owner answer or merge authorization.

## Basis and delivery boundary

- Status basis: `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` (#269).
- Observed cached `origin/main`, base and starting branch HEAD:
  `2d2e93eb14fe41bafaf2dbaa91f02d861c8be8b5` (#270). Branch:
  `agent/kix-audit14-audit14-open-decisions-closure-addendum`.
  Initial worktree clean; no local base delta. The requested status basis is
  one first-parent merge older; #270 changed only the plan, register, index
  and its record, with none of the resolving artefacts changed.
- `git fetch origin main`: NOT_RUN under the explicit supervisor no-network
  instruction, which overrides the session-start fetch requirement.
  Remote freshness is unverified; no network or GitHub action was attempted.
- Implementation head / final task head: no new commit assigned; the patch
  remains uncommitted above the starting HEAD. No commit, push, PR, issue,
  comment, branch/tag mutation, merge or history rewrite was performed.
- Exact-head KTX kernel verification and KIX protocol verification: run IDs,
  statuses and conclusions unavailable, NOT_RUN / not queried. Merge SHA,
  final-merge blob checks and post-merge main CI: not applicable.
  Publication, exact-head CI, non-author review and any user merge remain
  supervisor gates. Local READY means builder handoff, not merge-ready.

## Changed paths and result

Exactly three paths:

| Path | Change |
|---|---|
| `docs/status/OPEN_USER_DECISIONS_20261023_CLOSURE.md` | New dated closure: all nine source items, four RESOLVED-BY-MERGE and five STILL OPEN, original owners, full resolving merge SHAs and artefacts; unchanged open options by reference. |
| `docs/README.md` | One closure link beside the ledger/supplement links, preserving the long read-order line, and one validation-record entry after #266. |
| `validation/2026-10-23-audit14-open-decisions-closure/README.md` | This distinct evidence record. |

The [closure addendum](../../docs/status/OPEN_USER_DECISIONS_20261023_CLOSURE.md)
preserves both dated source bodies. It selects no option and changes no node
state. #270 is a separate node and supplies no duplicate-sync disposition.
The #266 missing validation record is disclosed without creating retrospective
execution evidence; #267's old-base class C finding is not a current-defect
claim. Owner permissions discussed in #267–#269 remain attributions to merged
records, not newly verified external decisions.

## Locks and preserved evidence

Before edits and after work, the observed Git blobs match the required values:

| Path | Required / observed blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The HEAD reference tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
All 108 immutable reference files, including non-ASCII paths, are compared
against HEAD using `git ls-tree -rz` and `git hash-object --no-filters`;
the complete on-disk file set also matches. No immutable file was transiently
mutated. Both historical decision documents match their HEAD bytes and their
cached-main diff is empty. The exact three-path check also excludes all
runtime, reference, contract, CI, checker, program and task-input changes.

## Existing coverage mapping (AGENTS §7)

| Requirement | Existing coverage before work | Evidence used here |
|---|---|---|
| Index coverage and target existence | Sufficiently covered by `scripts/check_docs_index.py` and its negative self-test | Both new documents indexed; no allowlist change. |
| Status register consistency | Sufficiently covered by `scripts/check_status_register.py` and its negative self-test | Reused unchanged, register unedited. |
| Readiness counts and BRA-RES9 citations | Sufficiently covered by `scripts/check_readiness_evidence_map.py` and `scripts/check_contract_error_codes.py`, both self-tests | Reused unchanged; no map/status reclassification. |
| Nine-item closure reconciliation, PR/SHA identity, named artefacts at basis | Partially covered: existing general checkers do not reconcile this ledger | One-time source-id, first-parent history and AST/content assertions. |
| Locked blobs, preserved snapshots, reference bytes, exact path scope | Partially covered by existing repository guards | Before/after hashes, complete reference comparison and exact path-set assertions. |

No persistent test or helper was added. The new documentary evidence fills
the missing dated reconciliation; one-time assertions cover its mechanical
predicates. Existing cited runtime tests are inspected, not rerun or promoted
to new execution evidence.

## Commands actually run and results

Baseline narrow commands ran before edits: `python3 scripts/check_docs_index.py`
exited 0 (216 scanned / 181 indexed / 35 allowlisted), then
`python3 scripts/check_status_register.py` exited 0 (347 paths / 15 EV ids /
32 original ids).

After edits, foreground `python3 /tmp/audit14-closure-checks.py` ran nine narrow
commands first: index, status register, readiness evidence and contract error-code
checkers, each plain and `--self-test`, then stage-5 host `--self-test`.
All nine exited 0. It then read the actual unguarded
`Stdlib offline document checks` run block from `.github/workflows/protocol.yml`,
asserted 27 commands and ran every command in order with `subprocess.run`,
stopping on any nonzero exit. All 27 exited 0. The table below transcribes
actual final summary lines; synthetic fault detections are successful
self-tests, not repository failures. Logs and JSON are local scratch evidence;
no long job ran in the background.

| Command | Actual result (all exit 0) |
|---|---|
| `python3 scripts/check_status_register.py` | capability register ok: paths=347 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | self-test: pass |
| `python3 scripts/check_docs_index.py` | docs index ok: scanned=218 indexed=183 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | rs predicate evidence map ok: rows=23 expected=23 citations=173 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | rs im evidence map ok: rows=30 expected=30 citations=197 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | self-test: pass |
| `python3 scripts/check_stage5_host.py --self-test` | self-test: pass |

| Additional command / check actually run | Actual result |
|---|---|
| `pwd`, `git status --short --untracked-files=all`, `git branch --show-current` | Exit 0; expected worktree/branch, initially clean; final scope exactly three paths. |
| `git rev-parse origin/main HEAD` | Exit 0; both equal the full #270 SHA above. |
| `git log --first-parent --merges --format='%H %s' 2393988e..HEAD` | Exit 0; #266–#269 match the four full SHAs in the closure; #270 is the later separate sync. |
| `git diff --name-only c7b470fc..HEAD` | Exit 0; only plan, register, index and #270 record; none of the eleven resolving source/record paths changed. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before edits: exit 0; required full blobs match. After work the acceptance script repeats these hash checks, also against HEAD. |
| `git rev-parse HEAD:reference/v0.3-rc1` | Exit 0; full reference tree above. Acceptance script repeats the tree check and all 108 file comparisons. |
| `python3 /tmp/audit14-closure-acceptance.py` (initial attempt) | Exit 1: scratch row selector counted the BRA-RES9 catalogue row as an error-code row. Restricted the selector to uppercase code tokens; no repository change or status correction was needed. |
| `python3 /tmp/audit14-closure-acceptance.py` (corrected, repeated after final record transcription) | Exit 0; nine ordered items, four/five statuses, merge identities, all artefacts at basis/HEAD, cited paths, locks, snapshots, 108 reference files and exact three-path scope pass. |
| `test -f <each cited file>` (via acceptance script) | Every inventory entry below exits 0. Existing source files also pass `git cat-file -e HEAD:<path>`; the two new deliverables are checked on disk pending supervisor commit. |
| `git diff --exit-code origin/main -- docs/status/OPEN_USER_DECISIONS_20261022.md docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md` | Exit 0; both preserved snapshots unchanged. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git diff -- docs/README.md`, `git diff --numstat`, `git status --short --untracked-files=all` | Exit 0; reviewed index additions and exact three specified paths, including the two untracked files. |

After final record transcription, the same acceptance script and the plain /
self-test index and register checks are repeated. No repository checker failed
and no CI or checker modification was needed.

## Citation inventory

Every repository file cited by either new document, including the command
scripts, is listed below. Paths are repo-relative; Markdown links resolve
relative to their containing document. Symbols and section fragments are
checked separately from file existence. Commands with placeholders in the
table describe the calls performed by the acceptance script, not literal
shell commands with angle brackets.

- `.github/workflows/ktx-kernel.yml` — `test -f`: exit 0.
- `.github/workflows/protocol.yml` — `test -f`: exit 0.
- `AGENTS.md` — `test -f`: exit 0.
- `docs/DEVELOPMENT_PLAN.md` — `test -f`: exit 0.
- `docs/README.md` — `test -f`: exit 0.
- `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` — `test -f`: exit 0.
- `docs/status/OPEN_USER_DECISIONS_20261022.md` — `test -f`: exit 0.
- `docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md` — `test -f`: exit 0.
- `docs/status/OPEN_USER_DECISIONS_20261023_CLOSURE.md` — `test -f`: exit 0.
- `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md` — `test -f`: exit 0.
- `integration_gate/test_http_gate.py` — `test -f`: exit 0.
- `readiness/CONFORMANCE.md` — `test -f`: exit 0.
- `readiness/test_conformance_sensitivity.py` — `test -f`: exit 0.
- `readiness/test_faults.py` — `test -f`: exit 0.
- `reference/booking_resale_admission/test_gate_properties.py` — `test -f`: exit 0.
- `runtime/crates/kix-kernel/src/lib.rs` — `test -f`: exit 0.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` — `test -f`: exit 0.
- `scripts/check_adapter_identity_map.py` — `test -f`: exit 0.
- `scripts/check_contract_error_codes.py` — `test -f`: exit 0.
- `scripts/check_delegation_layer_matrix.py` — `test -f`: exit 0.
- `scripts/check_docs_index.py` — `test -f`: exit 0.
- `scripts/check_i12_proof_ids.py` — `test -f`: exit 0.
- `scripts/check_read_model_source_map.py` — `test -f`: exit 0.
- `scripts/check_readiness_evidence_map.py` — `test -f`: exit 0.
- `scripts/check_rs_im_evidence_map.py` — `test -f`: exit 0.
- `scripts/check_rs_predicate_evidence_map.py` — `test -f`: exit 0.
- `scripts/check_rs_profile_traceability.py` — `test -f`: exit 0.
- `scripts/check_stage5_host.py` — `test -f`: exit 0.
- `scripts/check_status_register.py` — `test -f`: exit 0.
- `scripts/check_tl_predicate_evidence_map.py` — `test -f`: exit 0.
- `scripts/check_v5_transition_evidence_map.py` — `test -f`: exit 0.
- `validation/2026-10-17-booking-resale-admission-seeded-property/README.md` — `test -f`: exit 0.
- `validation/2026-10-23-audit14-open-decisions-closure/README.md` — `test -f`: exit 0.
- `validation/2026-10-23-bra-section9-error-code-coverage/README.md` — `test -f`: exit 0.
- `validation/2026-10-23-readiness-receipt-audit-tests/README.md` — `test -f`: exit 0.

The acceptance script compares ordered ids against ledger §1 and supplement
headings. For both the status basis and HEAD it checks the exact #266 import
at line 38 and the Negative controls heading, four AST methods on
`TransportTests`, the 27/0/0/9 readiness count line, absence of
`expectedFailure`, the BRA-RES9 `TABLES` key, ten COVERED code rows and the
six-pass-through exclusion statement. It verifies that all eleven resolving
source/record files have no basis-to-HEAD diff. Presence/structure checks do
not prove test semantics or reproduce other records' results.

## Contract findings, non-claims and residuals

- A (contract-defined and matching): cited documentary facts match the local
  merged artefacts and history; local checkers pass for this working tree.
- B (contract undefined): no new runtime characterization. Historical source
  records retain their own class B/C findings and limits.
- C (explicit contract violation): none found within this documentation task.
- No option, owner, policy value, evidence grade, protocol command or program
  node state changes. The five open items retain original owners/options by
  reference; RS-4 acceptable load remains UNDETERMINED and nine readiness rows
  stay OPEN. No owner response is inferred from this closure document.
- Cargo, Clippy/formatting, Move, ZK, Node, the HTTP/readiness/reference suites,
  and heavy `.github/workflows/ktx-kernel.yml` steps: NOT_RUN, docs-only paths.
  The local CI equivalent is only the 27-command offline document step, not
  either full workflow or its separate rights-scale job. Plain stage-5 host
  evaluation, provisioning, load measurement and external calls: NOT_RUN.
- No production readiness, durability, distributed fencing, bank exactly-once,
  chain finality, legal compliance or full protocol verification is claimed.
  No historical hosted CI success transfers to this patch. Exact-head CI and
  non-author review remain pending supervisor publication.
- No hardware, spending, paid service, credential, secret, real funds, real
  PG/bank/KYC call, public endpoint, Sui testnet/mainnet, new coin/TIX module,
  R2, replication/consensus/storage engine or production runtime was needed.

## Deviations

Fetch omitted under the supervisor's explicit no-network instruction; only
cached refs are observed. No substantive design deviation. The scratch
acceptance selector was corrected as recorded above. Open owner decisions,
#266's missing historical execution record and remote freshness remain outside
this node's evidence; this patch makes no merge proposal.
