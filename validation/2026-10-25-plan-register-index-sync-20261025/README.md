# Plan, register and loop-node crosswalk sync — 2026-10-25

Node: `audit15-plan-register-index-crosswalk-sync-20261`. Source: KIX audit #15
(`/workspace/kix-run/audits/audit_15_20261025.md`), the supervisor-supplied node
specification and read-only Sonnet design plan. Issue: none; depends_on: [];
audit floor A2; astra_gate: None; user_merge: False. No corresponding task file
exists under `docs/tasks/`; the supplied prompt is the immutable task input.
This is not ASTRA program mode. Builder-authored documentary evidence only.
Location pointers only: no new approval, no decision text, no grade raise.
Canonical counting remains `DECISION_REQUIRED · Astra`.

## Basis and delivery boundary

Observed cached `origin/main`, base and starting branch HEAD all equal
`d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313` (#280). Branch:
`agent/kix-audit15-plan-register-index-crosswalk-sync-20261`. The worktree was
clean on entry; no local base delta. `git fetch origin main`: NOT_RUN under the
supervisor's explicit no-network instruction, overriding AGENTS §1. Remote
freshness is unverified. No base change was made.

Implementation head / exact final committed task head: no new commit assigned;
changes remain uncommitted above the starting HEAD. No commit, push, PR, issue,
comment, tag/branch operation, merge, rebase or history rewrite was performed.
Exact-head KTX kernel verification and KIX protocol verification run IDs,
statuses and conclusions: unavailable, NOT_RUN / not queried. Merge SHA,
final-merge lock verification and post-merge main CI: not applicable.
Publication, exact-head CI and non-author review remain supervisor gates.
Local READY means builder handoff only, not merge-ready evidence.

## Git-derived mapping

The first-parent range after #275 contains exactly five merges. Each receives
one §5 row, with its full SHA, merge-commit author and a complete clause quoted
verbatim from one physical line of its own record. All five authors are
`soulbound_jt`; this is not a claim about GitHub's merger identity. Existing
§5 rows, headings and preamble remain byte-identical, including #275.

| PR | Merge SHA | Validation record directory | Quoted clause |
|---|---|---|---|
| #276 | `5a09a325e2f6415b7fe638d0dbcd826b4d45fb86` | `validation/2026-10-24-plan-register-index-sync/` | Location pointers only: no new approval, no decision text, no grade raise. |
| #277 | `99f30c2d641646d653b62383b213452fd0a0498b` | `validation/2026-10-24-bra-aid-returned-data-isolation/` | Git/GitHub publication belongs to the supervisor. |
| #278 | `41a799987fe3a6a207abcce75045265c5796e1e4` | `validation/2026-10-24-resale-admission-rejection-atomicity/` | No grade change. |
| #279 | `4480c9db7be539abd5a99e640b5a25c7eef8cafe` | `validation/2026-10-25-aid-rejection-atomicity/` | No older SHA's CI is transferred to this patch. |
| #280 | `d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313` | `validation/2026-10-25-restore-fingerprint-equivalence/` | not independent A2 review, acceptance, a capability grade increase or merge readiness. |

The dated register basis and both index summaries use #280. Only the fixture
cells in EV-SET, EV-CREDIT, EV-BRA, P AI delegation and TL-3 offchain gain
pointers. #277 supplies BRA and AI returned-data modules; #278 supplies resale
and admission rejection modules; #279 supplies AI rejection atomicity; #280
supplies one restore-fingerprint module in each of the five reference suites.
No source/contract/coverage cell or grade changes. The #277 import-precedence
fix to `test_read_model_fixtures.py` needs no new capability pointer.

### Crosswalk selection and accounting

Cutoff program blob: `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`, identical to
the historical #209/#269 blob. Apply the original normalized literal rule:
``'not in `.aiops/program.json`' in ' '.join(text.split())``.
Four records in #270–#280 match (#272, #275, #276, #280). #274 instead states
“loop-proposed and absent from `.aiops/program.json`”; the existing equivalent
explicit-statement allowance selects it, as it did #264. #272 qualifies by
quoting the selection phrase, following #210's precedent. No audit exclusion
or branch-name inference is added. At the cutoff there are 51 literal-match
records plus those two equivalent-statement records: 53 crosswalk rows.

| PR | Record | Selection / accounting |
|---|---|---|
| #270 | `validation/2026-10-23-audit14-plan-register-index-sync/README.md` | Neither literal nor equivalent explicit absence statement; §2 accounting |
| #271 | `validation/2026-10-23-audit14-open-decisions-closure/README.md` | Neither literal nor equivalent explicit absence statement; §2 accounting |
| #272 | `validation/2026-10-23-audit14-loop-node-crosswalk-refresh/README.md` | Literal match; §1 row |
| #274 | `validation/2026-10-23-rs-map-gap-closure-batch-2/README.md` | Equivalent explicit absence statement; §1 row |
| #275 | `validation/2026-10-24-reward-snapshot-isolation/README.md` | Literal match; §1 row |
| #276 | `validation/2026-10-24-plan-register-index-sync/README.md` | Literal match; §1 row |
| #277 | `validation/2026-10-24-bra-aid-returned-data-isolation/README.md` | Neither literal nor equivalent explicit absence statement; §2 accounting |
| #278 | `validation/2026-10-24-resale-admission-rejection-atomicity/README.md` | Neither literal nor equivalent explicit absence statement; §2 accounting |
| #279 | `validation/2026-10-25-aid-rejection-atomicity/README.md` | Neither literal nor equivalent explicit absence statement; §2 accounting |
| #280 | `validation/2026-10-25-restore-fingerprint-equivalence/README.md` | Literal match; §1 row |
| #273 | No first-parent merge in #269..#280 | Absent number; not a remote PR-state claim |

Range total: 11 numbers, 10 merges, five added rows, five unselected merges,
one absent number. Audit #15's statement about all eleven records saying
“not in” does not match the actual selection statements for #270, #271,
#277, #278 and #279, and #273 has no merge in this range. The records are
accounted for without rewriting them or inferring canonical acceptance.

Overlaps reuse the existing quoted phrases: #274 follows #217; #275 names
TL-3 offchain and replay preservation; #276 follows #194; #280 names the
settlement, credit, BRA, AI mock, reward and replay-preservation artifacts.
Every quoted phrase is checked against the named parsed `spec` at the cutoff.
`depends_on` clauses are copied from existing rows and checked against the
JSON. The merged rule is re-evaluated against first-parent branch names:
`p-sdk-0` is observed at #123 `a74e7c459d3be6754ac3cf24503e43c7bc312358`,
`tl-1` at #147 `841408e77065c841ea73e2cf04fe8c03fbd35f5d`; `roadmap-sync`,
`k-current-capability-map`, `k1-e4-residual-review` and
`k-stage3-schema-sdk-conformance` have no exact branch-name match.
These are branch-name observations only, not node acceptance.

## Complete changed paths

- `docs/DEVELOPMENT_PLAN.md`
- `docs/status/CURRENT_CAPABILITY_REGISTER.md`
- `docs/status/LOOP_NODE_CROSSWALK.md`
- `docs/README.md`
- `validation/2026-10-25-plan-register-index-sync-20261025/README.md`

## Locks and preserved bytes

| File | Before / after required Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` / identical |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` / identical |

`HEAD:reference/v0.3-rc1` before/after:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. The acceptance verifier compares
all 108 tracked historical files and modes, and the complete on-disk path set,
with HEAD. The protected-path diff is empty. No locked file or reference file
was edited, regenerated or transiently mutated.

Removing only the inserted strings/lines restores the exact HEAD bytes of all
four tracked documents. The verifier also checks unchanged register cells and
rows, old crosswalk §2 subsections, §3/§4, prior plan rows and index content.
One-time scripts and their logs are under `/tmp`, outside the deliverable;
no persistent regression test or checker change is added for this document edit.

## Coverage mapping (AGENTS §7)

| Requirement | Existing evidence | Initial coverage / action |
|---|---|---|
| Register paths, EV definitions, original 32 IDs | `scripts/check_status_register.py`, including `--self-test` | Sufficiently covered; reuse unchanged. |
| Record index and broken/duplicate allowlist entries | `scripts/check_docs_index.py`, including `--self-test` | Sufficiently covered; reuse unchanged. |
| Related document maps and contracts | The 27-command `Stdlib offline document checks` step in `.github/workflows/protocol.yml` | Sufficiently covered for existing validators; run the exact unguarded block. |
| Full merge SHAs, authors and single-line complete quotes | #276's historical record and Git history; no continuing checker | Partially covered; one-time Git/quote assertion plus clause inspection for these five rows. |
| New crosswalk selection, dependencies, spec phrases and range accounting | Existing literal/equivalent rules, #210/#264 precedents and canonical JSON | Partially covered; one-time history/JSON assertions for #270–#280. |
| Insertion-only preservation, exact scope and immutable reference | Git baseline and AGENTS lock values | Not covered by document checkers; one-time byte/path/mode assertions. |
| Fixture locations and characterization limits | #277–#280 records; existing returned-data, rejection and restore-fingerprint test modules | Sufficiently covered as existing pointers; AST/path inspection only, no fresh fixture execution claim. |

## Commands and actual results

Baseline narrow checks passed before edits: register `paths=349 ev_ids=15
original32=32`; index `scanned=226 indexed=191 allowlisted=35`; both self-tests
passed. Foreground local verification uses the available Python interpreter;
no background long job is launched. Python 3.13.5 was used locally; the workflow
setup pin is 3.12. The runner extracts the authoritative
workflow block, asserts there is no step guard and exactly 27 commands, then
executes them sequentially and stops on any failure.

| Command from `protocol.yml` | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=364 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=227 indexed=192 allowlisted=35 |
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
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

Other commands actually run:

| Command | Actual result |
|---|---|
| `pwd`; `git status --short --branch`; `git rev-parse origin/main HEAD` | Exit 0; expected worktree and branch, initially clean; both SHAs equal the basis above. |
| `git log --first-parent --merges --reverse --format='%H %an %s' 7327a00a68ef6efa81a795173af5e4572ccd90ef..HEAD` | Exit 0; exactly #276–#280 in order, all authors `soulbound_jt`. |
| `git log --first-parent --merges --reverse --format=%H %an %s c7b470fc39ad6f6aa6ad59c18b5595cde41a7200..HEAD`; `git show --format= --name-only --diff-merges=first-parent <merge SHA>`; `git show <SHA>:<record>` (inside inline inspection and verifier) | Exit 0; 10 actual merges in #270–#280, one record per merge; exact node IDs and selection classifications above; #273 absent. The format is passed as one argument by Python. |
| `git rev-parse HEAD:.aiops/program.json`; local JSON/spec inspection | Exit 0; `ff0f39a8129ca8b8d30818cce35c3d4e588872fc`, unchanged from the historical cutoff; overlapping spec phrases retained. |
| Initial inline JSON inspection indexing `node['depends_on']` | Exit 1, exploratory helper `KeyError`: the field is absent on nodes with no dependencies. No repository defect or mutation. Subsequent verifier uses `node.get('depends_on', [])` and confirms the existing clauses. |
| Inline stdlib AST inspection of the 10 named Python fixture modules | Exit 0; all paths parse and expected classes exist. Static inspection only; not test collection or execution. |
| `python3 --version` | Exit 0; Python 3.13.5 locally versus workflow setup pin 3.12; no interpreter install. |
| `python3 scripts/check_status_register.py`; `python3 scripts/check_status_register.py --self-test` | Baseline: exit 0, paths=349/EV IDs=15/original32=32, self-test pass. After edits: exit 0, paths=364/15/32, self-test pass. Final rerun uses `env PYTHONDONTWRITEBYTECODE=1`. |
| `python3 scripts/check_docs_index.py`; `python3 scripts/check_docs_index.py --self-test` | Baseline: exit 0, scanned=226/indexed=191/allowlisted=35, self-test pass. After edits: exit 0, 227/192/35, self-test pass. Final rerun uses `env PYTHONDONTWRITEBYTECODE=1`. |
| `python3 /tmp/audit15-run-stdlib.py` | Exit 0; exact 27-command unguarded workflow block, all passed in foreground, with `PYTHONDONTWRITEBYTECODE=1` in child environments. Individual results above. |
| `python3 /tmp/audit15-verify.py` | Exit 0; all four acceptance/preservation groups passed, including exact insertion reversal, full merge mapping, selection/accounting, specs/dependencies, locks/reference bytes, index/scope/whitespace. Repeated after recording results. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before/after) | Exit 0; both required hashes in Locks match before and after. |
| `git rev-parse HEAD:reference/v0.3-rc1` (before/after) | Exit 0; `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` both times. |
| `git ls-tree -r -z HEAD reference/v0.3-rc1`, `git show HEAD:<path>` and on-disk byte/mode/path inspection (inside verifier) | Exit 0; all 108 files/modes and complete on-disk set equal HEAD. |
| `git diff --name-only origin/main -- runtime reference .github .aiops docs/tasks docs/contracts scripts 'docs/status/RS_*'` | Exit 0; empty. |
| `git diff --check`; `git diff --no-index --check /dev/null validation/2026-10-25-plan-register-index-sync-20261025/README.md` (inside verifier) | Tracked check exit 0; new-file comparison exit 1 for the added file with no stdout/stderr, i.e. no whitespace diagnostics. |
| `git diff --stat`; `git diff -- <four tracked documents>`; `git status --short --untracked-files=all` | Exit 0; four tracked document edits plus exactly this new validation record. |
| `cat`, `sed`, `rg`, inline stdlib/Git source inspection | Read-only governance, plan/baseline/authority, control-plane candidate pin, program decisions §5, source audit, records, fixture names, checker coverage and workflow inspection. No source fixture execution claim. |

After transcribing results, the acceptance verifier, both narrow checkers in
plain/self-test modes and whitespace checks are repeated. The one-time
verifier checks Git-derived plan metadata, quote/link targets, register fixture
cells, inserted-byte removal, crosswalk literal/equivalent selection and full
range accounting, dependency branch observations, spec phrase substrings,
index uniqueness, protected bytes, allowed paths, and unchanged HEAD/base.

## Contract findings A/B/C

- A: location pointers match the merged records and local Git history; existing
  document checkers apply to this working tree. No semantic implementation change.
- B: no new runtime characterization. #280's reward omitted-`prior_record`
  replay difference remains its class B observation pending Astra; #278's
  cross-machine clock-skew observation remains with
  `booking-resale-admission-deepening`. Their source-informed limitations and
  other class B characterizations remain in their original records. Pointer
  updates neither resolve them nor infer an atomicity/replay contract.
- C: no explicit contract violation found within this documentation task.

## Non-claims and unrun work

No grade, map status, decision, approval, owner, policy value, protocol command,
operational count or canonical node status changes. No independent A2 review,
Astra acceptance, operational activation, durability, distributed fencing,
bank exactly-once, chain finality, legal compliance, clean-room independence,
production readiness or full workflow verification claim.

Cargo tests, Clippy, fmt, heavy KTX steps, Move, ZK, Node, HTTP/readiness and
reference fixture suites: NOT_RUN for this documentation-only patch. Plain
stage5 host evaluation and load/host qualification: NOT_RUN, matching the
workflow's self-test-only selection. Local document-check passes do not supply
exact-head hosted CI or non-author review. No external provider, real funds,
PG/bank/KYC, public endpoint, Sui testnet/mainnet, new coin/TIX module, secret,
hardware/equipment, spending, paid service, storage engine, R2 or production
runtime was needed or used.

## Deviations and remaining uncertainty

- Fetch omitted under the supervisor's explicit no-network rule; cached main
  freshness is unverified. No task issue/document was created.
- The brief mentions editing historical rows for “finding 2”, while acceptance
  requires insertion-only restoration. Following the supplied design, #275
  and all earlier rows stay unchanged; the sibling
  `plan-section5-quote-completeness` node owns their re-quoting. New clauses
  preserve their negations. This does not correct #275's existing truncated quote.
- #277 also gains a pointer on P AI delegation because it added a test module
  to that suite, in addition to its EV-BRA module.
- #270, #271, #277, #278 and #279 get accounting entries rather than crosswalk
  rows because their records lack the required explicit absence statement.
  #274 is an equivalent-statement match, not a literal match. #273 is absent
  from the bounded first-parent inventory; no record/row is invented.
- Canonical counting remains `DECISION_REQUIRED · Astra`. Owner decisions and
  the reward/clock-skew class B questions remain open; no decision text is edited.
- Exact-head CI and non-author review await supervisor publication. A later
  sync owns this node's merge row. `/tmp` assertions are one-time evidence,
  not ongoing enforcement. No STOP condition is needed within this scope.
