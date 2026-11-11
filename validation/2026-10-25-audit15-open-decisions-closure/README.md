# Audit 15 open-decisions closure — builder validation

## Basis and delivery boundary

Node: `audit15-open-decisions-closure-20261025`. Date: 2026-10-25.
Source: KIX audit #15 finding 3 and the supervisor-supplied node specification
and read-only design plan. Issue: none; `depends_on: []`; audit floor A2;
`astra_gate: None`; `user_merge: False`. Not ASTRA program mode; no task file
under `docs/tasks/`. The supplied node input is the task document.

Branch: `agent/kix-audit15-open-decisions-closure-20261025`.
Starting HEAD/base and observed cached `origin/main` all equal
`ff88c441f36cde5b581ba29ce4c46ac47f22b218` (#282); no local base delta.
`git fetch origin main`: NOT_RUN under the supervisor's explicit prohibition
on network/GitHub actions, overriding AGENTS §1. Remote freshness is unverified.
Implementation/final task head: uncommitted working-tree patch above this base;
no new SHA assigned. Merge SHA/final-merge lock verification/post-merge main CI:
not applicable. Exact-head KTX and KIX run IDs/status/conclusions: unavailable,
NOT_RUN/not queried. No commit, push, PR, issue, comment, merge, tag/branch or
history operation occurred. Local READY denotes builder handoff only.

## Changed paths

- `docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md` (new)
- `docs/README.md` (two location pointers)
- `validation/2026-10-25-audit15-open-decisions-closure/README.md` (new)

## Locks and preserved evidence

Required kernel blobs, checked before editing and again during final verification:

| Path | Required / observed blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The immutable `reference/v0.3-rc1` tree at HEAD is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. One-time assertions compare all
tracked file bytes/modes and the complete on-disk file set to HEAD. Neither
lock nor reference file was edited, even transiently. Earlier ledger,
supplement, closure and validation records stay byte-identical to HEAD.
No plan, register, crosswalk, contracts, decisions, checkers, CI, task inputs,
`.aiops/`, runtime or reference files change.

## Existing coverage mapping (AGENTS §7)

| Requirement | Existing coverage before edits | Evidence used here |
|---|---|---|
| New status/validation files indexed; link targets exist | Sufficiently covered by `scripts/check_docs_index.py` and its negative self-test | Reuse unchanged, add both links |
| Register remains consistent | Sufficiently covered by `scripts/check_status_register.py` and its self-test | Reuse unchanged |
| Nine item identities/owners and unchanged open options | Partially covered by October 23 closure; checker does not reconcile rows | One-time comparison of ordered ids, owners, source links and verbatim remaining-open bullets |
| Current A3 resolution, A4 disposition and #274–#280 stops | Not covered by older snapshot | New dated closure and attributed record/line checks, first-parent merge and artefact checks |
| Cited SHAs/paths/anchors; locks, snapshots and exact scope | Partially covered by existing path/blob guards | One-time read-only Git, anchor, full-byte preservation and scope assertions |

No persistent test/helper added. The dated evidence fills a documentary gap;
existing runtime tests and other records' results are not rerun or promoted.

## Commands actually run and results

Baseline: `python3 scripts/check_docs_index.py` exited 0 before edits,
`docs index ok: scanned=228 indexed=193 allowlisted=35`.
After edits, narrow checks ran first: the plain index check exited 0 with
`scanned=230 indexed=195 allowlisted=35` (two added files); the plain register
check exited 0 with `paths=364 ev_ids=15 original32=32`. Both `--self-test`
forms exited 0, `self-test: pass`. Intended synthetic fault detections are
self-test success, not broken repository documents.

Foreground `python3 /tmp/audit15-closure-ci.py` extracted the actual unguarded
`Stdlib offline document checks` run block from `.github/workflows/protocol.yml`,
asserted its 27-command length and no step guard, and ran each command in order
using `subprocess.run`, stopping on the first nonzero exit. All 27 exited 0.
The following are the commands actually invoked and their terminal output.
Complete local output/exit data is scratch at `/tmp/audit15-closure-ci-results.json`;
it is not a committed deliverable. No long job ran in the background.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; `capability register ok: paths=364 ev_ids=15 original32=32`. |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; `rs profile traceability ok: blueprint=47 profile=47 expected=47`. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; `read model source map ok: queries=13 anchors=128 catalogues=2 citations=145`. |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_docs_index.py` | Exit 0; `docs index ok: scanned=230 indexed=195 allowlisted=35`. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0; `i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14`. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0; `delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6`. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0; `rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2`. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0; `rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2`. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0; `tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7`. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_contract_error_codes.py` | Exit 0; `contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0`. |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0; `adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8`. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0; `v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0`. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0; `readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9`. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0; `self-test: pass`. |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; `self-test: pass`. |

Additional commands actually run (grouped where outputs are parallel):

| Command / check | Actual result |
|---|---|
| `pwd`; `git status --short`; `git branch --show-current`; `git rev-parse HEAD origin/main` | Exit 0; expected worktree and branch, initially clean; HEAD/cached main equal the full basis above. |
| `git log --first-parent --format='%H %s' 2393988e..HEAD` | Exit 0; #266–#269 and #274–#282 map to the SHAs below; no #273 first-parent merge. |
| `git diff-tree --no-commit-id --name-only -r ff88c441^1 ff88c441`; same for `0db660a1^1 0db660a1` | Exit 0; #282 touches plan/index/own record; #281 touches plan/register/crosswalk/index/own record. No stop disposition artefact. |
| `rg -n 'register-index-sync-20261023' validation/2026-10-24-plan-register-index-sync/README.md` | Exit 1 with no match, expected absence; #276 does not name the A4 node. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0 before edits; required blobs match. Repeated after work and by acceptance assertions, same result. |
| `git rev-parse HEAD:reference/v0.3-rc1` | Exit 0; exact reference tree above, also checked by final assertions. |
| `python3 /tmp/audit15-closure-acceptance.py` (initial) | Exit 1: scratch helper mistakenly required the intentionally changed docs index to equal HEAD. Item/history/record assertions passed before that helper failure. |
| `python3 /tmp/audit15-closure-acceptance.py` (corrected; repeated after final transcription) | Exit 0; nine ordered ids/sources/owners, five resolved/four open, unchanged remaining-open bullets, all merge identities, record statements/anchors/paths, two locks, all 108 reference files/modes, prior snapshots/records and exact three-path scope pass. The index is checked by reversing only its two authorized additions. |
| `git merge-base --is-ancestor <merge SHA> HEAD` for all 13 inventory SHAs, via assertions | Each exit 0; all are also present in the local first-parent inventory with the expected PR number. |
| `git cat-file -e HEAD:<cited path>` for each existing repository file, via assertions | Each exit 0. New closure/record checked on disk pending supervisor commit; existing artefacts also byte-match HEAD. |
| `git ls-tree -r -z HEAD reference/v0.3-rc1` and `git show HEAD:<path>` / on-disk byte and mode comparisons, via assertions | Exit 0; all 108 tracked files, complete path set and modes match HEAD. |
| `git diff --name-only HEAD -- runtime reference .github .aiops docs/tasks scripts docs/contracts docs/decisions` | Exit 0; empty. Exact changed-path assertion additionally excludes every other tracked or untracked nonignored path. |
| `git diff --exit-code HEAD -- docs/status/OPEN_USER_DECISIONS_20261022.md docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md docs/status/OPEN_USER_DECISIONS_20261023_CLOSURE.md` | Exit 0; all three preserved snapshots unchanged. |
| `git diff --check` | Exit 0; no whitespace diagnostics. New untracked files also pass trailing-whitespace assertions. |
| `git diff -- docs/README.md`; `git status --short --untracked-files=all` | Exit 0; reviewed two index additions and exactly the three specified paths. |
| `cat`, `sed`, `rg` of governance, plan/baselines/authority, candidate policy pointer/pin, program decisions, source audit, dated snapshots, records, checker and workflows | Read-only source inspection; no runtime evidence reproduced. |

The scratch helper correction changes no repository content or acceptance
criterion. Final text review also removed four unrelated receipt-test-name bullets
accidentally copied by a broad scratch selector into the remaining-open
section. The helper now restricts its comparison to that section and asserts
exactly the four explicit open node names. No repository checker failed and
no CI/checker modification was needed. After transcribing the record, the same acceptance assertions and
plain/self-test index/register checks are repeated, plus final whitespace,
lock and scope checks. These are local working-tree results only.

## Citation inventory

First-parent merge identities checked locally (each ancestor test exits 0):

| PR | Full merge SHA | Role |
|---|---|---|
| #266 | `fc28ad4eda7e49f34324d46253dfd950533740db` | Carried-forward resolution |
| #267 | `f4df0d8ce0253e7b9755f7eb77e857b2d49057e0` | Carried-forward resolution |
| #268 | `a3f0fea3160fdea2f59fa8658573be173e242074` | Carried-forward resolution |
| #269 | `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` | Carried-forward resolution |
| #274 | `a7e6febded343fe0fd43df2059874525194efecf` | A3 resolution and scanned record |
| #275 | `7327a00a68ef6efa81a795173af5e4572ccd90ef` | Scanned record; no new stop |
| #276 | `5a09a325e2f6415b7fe638d0dbcd826b4d45fb86` | Scanned record; no new stop |
| #277 | `99f30c2d641646d653b62383b213452fd0a0498b` | Scanned record; no new stop |
| #278 | `41a799987fe3a6a207abcce75045265c5796e1e4` | Scanned record; no new stop |
| #279 | `4480c9db7be539abd5a99e640b5a25c7eef8cafe` | Scanned record; no new stop |
| #280 | `d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313` | Scanned record; no new stop |
| #281 | `0db660a1085ca179c341c89129eeda763977b1fb` | Later documentation sync |
| #282 | `ff88c441f36cde5b581ba29ce4c46ac47f22b218` | Status basis; later documentation sync |

#273 is absent from the observed first-parent history. This agrees with the
#276 record, lines 46–51, and makes no claim about remote PR state.

The closure's local Markdown links and fragments resolve. The same nine
ordered item ids, source-row links and owner strings match the October 23
closure byte for byte; remaining-open bullets are copied verbatim with A3
dropped. RESOLVED-BY-MERGE retains that closure's exact definition.

Source facts checked against their recorded line numbers:

- A3: #274 record line 3 attributes the resume to owner-provisioned Rust
  toolchain/cache. Line 174 says “The owner approved Option 1 and completed
  toolchain/cache provisioning outside this builder session.” Lines 191–192
  report workspace tests/Clippy exit 0. The approval remains that record's
  attribution, not a newly verified decision or new authority here.
- A4: #276 record identifies `plan-plan-register-index-sync-20261024` and has
  no occurrence of `register-index-sync-20261023`; it gives no disposition of
  A4. The audit's supersession wording is recorded as a mismatch, not adopted.
- No new stop: #274 line 24/174 (own environment stop resolved); #275 lines
  223–224; #276 lines 244–245; #277 lines 85–86/207 (no class C; import issue);
  #278 lines 472–473; #279 lines 148–149; #280 line 231. These are attributed
  record statements, not independent reproduction of their tests.
- Uncertainty pointers only: #278 lines 479–482 (clock skew, internal fault
  semantics/source trust); #280 lines 229–231 (reward normalized replay).
  No stop, owner, option or item is created from those pointers.

Repository file inventory checked by the one-time script (all existing files
also pass `git cat-file -e HEAD:<path>`; new deliverables pass on-disk checks).
The generated list includes workflow command scripts; local `/tmp` helpers
are disposable scratch, not repository artefact citations. Directory mentions
are boundaries, not claims that new task/state files exist.

- `.github/workflows/ktx-kernel.yml` — present at HEAD.
- `.github/workflows/protocol.yml` — present at HEAD.
- `AGENTS.md` — present at HEAD.
- `docs/README.md` — present at HEAD.
- `docs/status/CONTRACT_ERROR_CODE_COVERAGE.md` — present at HEAD.
- `docs/status/OPEN_USER_DECISIONS_20261022.md` — present at HEAD.
- `docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md` — present at HEAD.
- `docs/status/OPEN_USER_DECISIONS_20261023_CLOSURE.md` — present at HEAD.
- `docs/status/OPEN_USER_DECISIONS_20261025_CLOSURE.md` — on disk; new deliverable pending commit.
- `docs/status/READINESS_RUNTIME_EVIDENCE_MAP.md` — present at HEAD.
- `integration_gate/test_http_gate.py` — present at HEAD.
- `readiness/CONFORMANCE.md` — present at HEAD.
- `readiness/test_conformance_sensitivity.py` — present at HEAD.
- `readiness/test_faults.py` — present at HEAD.
- `reference/booking_resale_admission/test_gate_properties.py` — present at HEAD.
- `reference/rights_scale/sui/tests/private_path_tests.move` — present at HEAD.
- `reference/rights_scale/test_private_model.py` — present at HEAD.
- `runtime/crates/kix-kernel/src/lib.rs` — present at HEAD.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` — present at HEAD.
- `scripts/check_adapter_identity_map.py` — present at HEAD.
- `scripts/check_contract_error_codes.py` — present at HEAD.
- `scripts/check_delegation_layer_matrix.py` — present at HEAD.
- `scripts/check_docs_index.py` — present at HEAD.
- `scripts/check_i12_proof_ids.py` — present at HEAD.
- `scripts/check_read_model_source_map.py` — present at HEAD.
- `scripts/check_readiness_evidence_map.py` — present at HEAD.
- `scripts/check_rs_im_evidence_map.py` — present at HEAD.
- `scripts/check_rs_predicate_evidence_map.py` — present at HEAD.
- `scripts/check_rs_profile_traceability.py` — present at HEAD.
- `scripts/check_stage5_host.py` — present at HEAD.
- `scripts/check_status_register.py` — present at HEAD.
- `scripts/check_tl_predicate_evidence_map.py` — present at HEAD.
- `scripts/check_v5_transition_evidence_map.py` — present at HEAD.
- `validation/2026-10-17-booking-resale-admission-seeded-property/README.md` — present at HEAD.
- `validation/2026-10-23-bra-section9-error-code-coverage/README.md` — present at HEAD.
- `validation/2026-10-23-readiness-receipt-audit-tests/README.md` — present at HEAD.
- `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md` — present at HEAD.
- `validation/2026-10-24-bra-aid-returned-data-isolation/README.md` — present at HEAD.
- `validation/2026-10-24-plan-register-index-sync/README.md` — present at HEAD.
- `validation/2026-10-24-resale-admission-rejection-atomicity/README.md` — present at HEAD.
- `validation/2026-10-24-reward-snapshot-isolation/README.md` — present at HEAD.
- `validation/2026-10-25-aid-rejection-atomicity/README.md` — present at HEAD.
- `validation/2026-10-25-audit15-open-decisions-closure/README.md` — on disk; new deliverable pending commit.
- `validation/2026-10-25-restore-fingerprint-equivalence/README.md` — present at HEAD.

## Contract findings (A/B/C) and non-claims

- A: documentary claims follow local first-parent history and the cited records.
  A3 resolves by #274's artefacts and its own attributed owner-provisioning
  statement. No owner approval was independently verified here.
- B: no new runtime characterization. #278 clock-skew and #280 reward normalized
  replay uncertainties are pointers to their existing class B records, not stops.
- C: no explicit contract violation found in this documentation task.
- Four items (L1, L2, A2, A4) retain original owners/options by reference. No
  option, owner, policy value, protocol command, grade or node state changes.
  RS-4 acceptable load stays UNDETERMINED (User); nine readiness rows stay OPEN.
  Canonical counting remains `DECISION_REQUIRED · Astra`.
- Cargo, Clippy/formatting, Move, ZK, Node, HTTP/readiness/reference suites and
  heavy KTX steps: NOT_RUN for these docs-only paths. Local CI equivalent is
  the unguarded 27-command offline document step in `.github/workflows/protocol.yml`,
  not either full workflow or its separate rights-scale job. The KTX workflow
  `.github/workflows/ktx-kernel.yml` skips heavy steps for these document paths.
  Plain stage-5 host evaluation, provisioning and load measurements: NOT_RUN.
- No production readiness, durability, distributed fencing, bank exactly-once,
  chain finality, legal compliance, clean-room independence or full protocol
  verification claim. No older CI result transfers; exact-head CI and non-author
  review remain pending supervisor publication.
- No hardware, equipment, money, paid service, secret/credential, real funds,
  PG/bank/KYC call, public endpoint, Sui testnet/mainnet, new coin/TIX module,
  R2, replication/consensus/storage engine or production runtime was needed.

## Deviations

Fetch omitted under the supervisor's explicit no-network instruction. No
substantive design deviation. Scratch helper corrections and the final text
review correction are recorded above; no repository checker failed. Audit #15
says #276 superseded the duplicate,
but the #276 record never names or disposes of A4's October 23 node. A4 stays
STILL OPEN as the supplied conditional acceptance and design require. No
DECISION_REQUIRED.md is needed for this documentary scope. Remote freshness,
remaining owner decisions, canonical counting, exact-head review and CI remain
outside this builder's evidence. No merge proposal is made.
