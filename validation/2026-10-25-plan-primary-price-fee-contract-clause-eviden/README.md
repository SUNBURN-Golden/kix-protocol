# Primary price/fee evidence map — builder validation

## Task, source and delivery boundary

Node: `plan-primary-price-fee-contract-clause-eviden`. Date: 2026-10-25.
Task document: supervisor-provided node specification and read-only design in
this session. No issue or corresponding `docs/tasks/` document exists. Source:
KIX planner run 1792916405; not an ASTRA program-mode task. This is builder
validation, not a non-author review, an A2 audit, acceptance or a grade increase.

Branch: `agent/kix-plan-primary-price-fee-contract-clause-eviden`.
Observed cached `origin/main`, stated base and initial task HEAD are all
`92d08e755dfe362ed224112c8dada6c5fcea17d4`. No local base delta; no rebase or merge.
`git fetch origin main`: NOT_RUN because the supervisor prohibits network actions,
overriding AGENTS §1. Remote freshness is unverified. The worktree began clean.
Implementation/final task head: uncommitted working-tree patch over that same
HEAD; there is no new implementation SHA. No commit, push, PR, issue, comment,
tag or branch operation was performed. READY means local builder delivery only.

Exact-head KTX kernel verification: run ID unavailable, status/conclusion
NOT_RUN/not queried. Exact-head KIX protocol verification: run ID unavailable,
status/conclusion NOT_RUN/not queried. Supervisor publication, exact-head CI and
non-author review remain outstanding; earlier-SHA CI is not transferred. No merge
was performed; merge SHA, merge-blob verification and post-merge main CI are N/A.
This record does not claim merge-ready.

## Complete changed-path list

- `docs/status/PRIMARY_PRICE_FEE_CONTRACT_EVIDENCE_MAP.md` — new map.
- `scripts/check_primary_price_fee_evidence_map.py` — new stdlib checker/self-test.
- `.github/workflows/protocol.yml` — exactly two requested commands added.
- `docs/README.md` — one bullet linking map and this record; merge-location table unchanged.
- `validation/2026-10-25-plan-primary-price-fee-contract-clause-eviden/README.md` — this record.

No contract, test, mock, FSM, Move, capability register, `.aiops/`, `docs/tasks/`
or frozen reference file is changed. Both locked kernel files are unchanged.

## Existing coverage mapping and new evidence (AGENTS §7)

The map supplies the exact full test citations. Before adding a checker, the
contract, #288 validation record and relevant test bodies were inspected.
No protocol test gap is filled by adding duplicate tests in this node.

| Requirement | Existing coverage classification | Reused evidence and remaining gap |
|---|---|---|
| §0 scope / §4 choices | OPEN | Final location is DECISION_REQUIRED · Astra; no option selected. |
| §1 observed baseline | PARTIAL | Gate price mismatch/replay and settlement floor/zero-policy tests; frozen Move/lifecycle/core and extended ShowControl observations not tested by these citations. |
| §2 terms | PARTIAL | #288 invalid amount/bps and price input tests cover existing bounds; no on-chain fields, fee inclusion decision or per-show freezing proof. |
| §3 predicates | PARTIAL | Existing PF-C01/PF-C02 Python evidence only. |
| PF-C01 offline | Sufficiently covered within MockGates.bind_order | #288 boundary/non-money/seeded prices plus GateTests price/replay, ReservationFsmTests unbound issue and rejection-atomicity mismatch test. Overall row PARTIAL across layers. |
| PF-C02 offline | Sufficiently covered within MockSettlement | #288 boundary goldens, four §5 examples and seeded grid; earlier SplitPropertyTests boundary/seeded Fraction oracle and SettlementMockTests floor/zero/rejected-policy anchor. Overall row PARTIAL across layers. |
| PF-C01/PF-C02 on-chain | NOT_COVERED | No primary price equality or u128 primary split enforcement; DECISION_REQUIRED · Astra remains. Two separate layer rows. |
| PF-C03 / PF-C04 | OPEN | Event/command schema and fee on refund remain DECISION_REQUIRED · Astra; no allowed citation establishes on-chain refund linkage. |
| PF-C05 | NOT_COVERED | No Python test asserts primary/resale bps isolation; frozen Move evidence excluded. Owner Astra. |
| §5 arithmetic examples | COVERED | PrimaryFeeSplitPfC02Tests.test_contract_section5_examples checks all four synthetic examples, roles, zero suppression and conservation. |
| §6 and its nine items | OPEN | All nine contract first sentences, status cells and full owners are retained verbatim in contract order. No value filled. |
| §7 existing coverage | PARTIAL | Reuses contract mock anchors and #288 citations; admission credential consumption and resale transfer tests are lifecycle evidence only. Frozen rights_tests.move evidence excluded. |
| §8 non-claims | NOT_COVERED | Offline mocks cannot establish funds receipt, chain finality, durability, legal/tax compliance or production readiness. |

Map totals: **14 clause rows = COVERED=1 PARTIAL=6 NOT_COVERED=2 OPEN=5**;
**2 on-chain rows = NOT_COVERED=2**; **9 open items = OPEN=9**;
**38 citation occurrences** (repeated anchors included).

New evidence is structural: the checker uses AST to resolve direct `test_*`
methods of explicit TestCase subclasses in the two allowed Python test
directories. It checks exact titles, unique heading/PF-C rows, statuses/owners,
three count lines, on-chain gaps and verbatim open items/order. It rejects frozen,
escaping, noncanonical and non-test paths before reading them, and never imports
tests. Symbol existence does not prove assertion adequacy.

Its self-test first checks the unmodified map, then reports **72 negative
controls**, each required to fail with its intended diagnostic. Controls cover
missing/duplicate/invented clauses, heading/title drift, invalid citations and
Python, helper/ordinary classes, forbidden paths, policy/chain promotion, item
status/owner/order drift, malformed cells, counts and banners. A separate direct
TestCase selection assertion excludes ordinary/derived classes and helpers.

## Commands actually run and actual results

All verification ran from the worktree root, in foreground subprocesses with
`PYTHONDONTWRITEBYTECODE=1`; no detached/background job or external network
provisioning ran. A temporary stdlib driver outside the repository used
`subprocess.run` sequentially, recorded exit codes/output and stopped on failure.
Read-only inspection used `pwd`, `cat`, `sed`, `rg`, `wc`, `git status`,
`git rev-parse`, `git branch --show-current`, `git diff` and `git hash-object`.

Initial narrow verification, before broader checks:

| Command | Actual result |
|---|---|
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; rows=14 headings=14 chain=2 items=9 citations=38 COVERED=1 PARTIAL=6 NOT_COVERED=2 OPEN=5. |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; direct TestCase selection passes; all 72 negative controls detected as designed. |

The workflow run block was extracted from the actual `Stdlib offline document
checks` step, asserted to have **35 commands**, then run in order below. The
textual workflow guard compared against `git show HEAD:.github/workflows/protocol.yml`:
exactly two command lines follow the credit self-test, with every other byte
unchanged. This checks preservation of the existing YAML structure without
claiming a separate YAML-parser run. The step remains unguarded by docs_only or
verified-tree conditions.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=242 indexed=207 allowlisted=35 |
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
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=2 items=9 citations=38 COVERED=1 PARTIAL=6 NOT_COVERED=2 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; self-test: pass (72 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; 194 tests passed; 0 failures. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; 405 tests passed; 0 failures. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed; 0 failures. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0; No diagnostics. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Exit 0; Both expected blobs match: 69564b166f0c27f9af5d8422f0a466b18d74c20f, b607996c83a119c349f1cc90469ac1ba82764e20. |
| `git diff --exit-code HEAD -- reference/v0.3-rc1` | Exit 0; No diagnostics. |
| `git diff --check` | Exit 0; No diagnostics. |
| `git status --porcelain --untracked-files=all` | Exit 0; Exactly the five planned paths (2 modified, 3 new). |

The doc index reports scanned=242 indexed=207 allowlisted=35. The error-code
catalogue remains rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0.
Settlement ran 194 tests; BRA ran 405 tests, all passing without skips. Existing
BRA tests include disposable loopback HTTP probes with production flags false;
no public endpoint or external provider was used. Architecture tests ran 7 tests.
Checker self-tests' intentional negative-control detections are expected success,
not repository failures. All repository checkers, reference suites and formatting checks passed on their
first run. The temporary scope helper correction is recorded below.

One earlier implementation helper failed before writing any repository file:
the initial `python3 -` in-memory map assembly used a header offset that counted
only eight open items and hit `assert len(items) == 9` (exit 1). The header filter
was corrected in the temporary builder script; all nine items were then written
and independently validated. This was not a test failure or a contract change.

Final checks after writing this record:

| Command | Actual result |
|---|---|
| `python3 /tmp/final_primary_scope_check.py` (initial temporary helper) | Exit 1: Git quoted a Korean filename in non-NUL ls-tree output; hash-object could not open that quoted spelling. No file was changed; this was a harness path-parsing error. |
| `python3 /tmp/final_primary_scope_check.py` (corrected to `git ls-tree -rz`) | Exit 0; exactly 5 planned paths, both locked blobs match, all 108 frozen files byte-identical to HEAD, exactly 2 workflow command lines added. |
| `python3 scripts/check_docs_index.py` | Exit 0; scanned=242 indexed=207 allowlisted=35 after record completion. |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0; all index negative controls detected; self-test: pass. |
| `git diff --check` | Exit 0; no whitespace diagnostics. |
| `git rev-parse origin/main HEAD` | Exit 0; both remain 92d08e755dfe362ed224112c8dada6c5fcea17d4. |

The temporary final scope helper separately compared each frozen file's raw Git
blob hash to HEAD using `git hash-object --no-filters`, with NUL-delimited
`git ls-tree -rz` paths. Its first filename-parsing attempt failed before the full
comparison; only the corrected successful run establishes the 108-file result.

## Preservation and exact-head limits

`git hash-object` before and after work returned:

| Locked path | Required and observed Git blob (before/after) |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`git diff --exit-code HEAD -- reference/v0.3-rc1` returned exit 0 without output;
final status has no tracked/untracked frozen-tree changes. No lock or frozen file
was transiently mutated. This node's checker does not read frozen files. The
unchanged settlement suite still runs its existing source-only frozen-core AST
characterization; executable differential remains NOT_MADE.

## Findings, deviations, non-claims and follow-up

- No explicit contract violation was found. No new contract-undefined semantics
  are asserted. The known gaps remain open, with their original owners. #288's
  frozen-core import-layout characterization is historical context, not a new
  executable comparison or cross-layer claim.
- Fetch is omitted under the supervisor's explicit no-network rule; cached main
  freshness is the remaining baseline uncertainty. No commit or hosted CI query
  is performed under the same delivery instructions.
- Minor checker adaptation: numeric heading/id regexes accept multiple digits,
  and the chain-row regex recognizes all two-digit PF-C ids, so future/invented
  rows are diagnosed rather than silently ignored. The allowed contract rows and
  chain layers are still exactly those requested. No substantive scope deviation.
- Separate YAML parsing is NOT_RUN: the stdlib extraction/byte-preservation guard
  validates the only workflow modification, two command lines. No YAML dependency
  was installed.
- Rust crate tests and Clippy are NOT_RUN because no Rust code/dependencies change;
  architecture regressions and workspace formatting checks passed. Move, localnet,
  ZK, `scripts/verify_runtime.py`, other reference suites, production runtime,
  performance and external service checks are NOT_RUN: no touched implementation
  depends on them, and this node's local CI equivalent is the entire stdlib step
  plus the required settlement/BRA regressions. Full hosted workflows remain the
  supervisor's exact-head gate, not a result inferred from these local checks.
- Price, bps, fee recipient, fee inclusion, fee on refund, enforcement A/B/C and
  allocation schema remain **UNDETERMINED** / **DECISION_REQUIRED · Astra**. Legal,
  accounting and Toss questions retain their named external owners. The
  100000/500 fixtures and synthetic examples are not adopted policy.
- No grade/register change, real funds, real PG/bank/KYC, public endpoint, Sui
  testnet/mainnet, production runtime, storage engine, coin/TIX module or secrets.
  No durability, distributed fencing, bank exactly-once, chain finality, legal
  compliance or production-readiness claim follows from this evidence.
- Follow-up: non-author semantic review and supervisor exact-head CI; separate
  register-sync node may extend the checker inventory sentence. No register edit
  belongs here. Owners must decide open inputs in separately authorized work.
  No STOP condition was needed to deliver this map/checker; DECISION_REQUIRED.md
  is not required.

Local builder state: READY; final committed SHA, review and merge gates remain
outside this session.
