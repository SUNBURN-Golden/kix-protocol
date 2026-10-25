# AI delegation contract clause evidence map — validation

Builder-authored, source-informed local evidence; not independent review,
acceptance, an Astra audit or a grade change.

## Task and source basis

- Node: `plan-ai-delegation-contract-clause-evidence-m`.
- Immutable task document: the supervisor-provided node specification and design
  in this session; no issue and no matching task document under `docs/tasks/`.
- Dependency: `plan-primary-price-fee-contract-clause-eviden`, present in the base.
- Branch: `agent/kix-plan-ai-delegation-contract-clause-evidence-m`.
- Observed cached `origin/main`, base, initial and end-of-session HEAD:
  `a0db1e226e27b1c5f60ee938fb528ff795907056`. No local base delta.
- No fetch: the supervisor explicitly forbids GitHub/network actions. Remote
  freshness is unverified. No commit, push, PR, issue or comment was created.
- Implementation is the uncommitted worktree patch. A final implementation/task
  commit SHA does not yet exist; the unchanged HEAD is not a commit of this patch.
- Environment: repository root, Python 3.13.5 (workflow requests Python 3.12).
  Test HTTP calls were disposable loopback fixtures only; no external services.

## Complete changed-path list

1. `docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md` (new).
2. `scripts/check_ai_delegation_evidence_map.py` (new).
3. `.github/workflows/protocol.yml` (two commands added to the existing unguarded
   Stdlib offline document checks step; no gate weakened).
4. `docs/README.md` (location/index entry).
5. `validation/2026-10-26-plan-ai-delegation-contract-clause-evidence-m/README.md` (this record).

## Existing coverage mapping and new evidence

The [map](../../docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md) holds exactly
one row per numbered heading in
[AI_DELEGATION_AUTHORITY.md](../../docs/contracts/AI_DELEGATION_AUTHORITY.md)
revision **초안 0.1**. Source bodies were read before classification.

| Requirements | Existing evidence | Classification |
|---|---|---|
| §1 terminology/authority, §5 allow/deny tools, §8 codes/flags | Named mock/property/rejection tests in the map | Sufficiently covered within the stated offline assertions: COVERED=3 |
| §0 scope, §2 command separation, §3 authority, §4 grant records, §6 traceability, §7 transitions/replay | Mock/property suites, returned-data isolation, restore-fingerprint equivalence, readiness conformance | Partially covered: PARTIAL=6; each row names its gap |
| §10 non-claims | No executable predicate; no evidence asserted | NOT_COVERED=1 |
| §9 policy and follow-up decisions | No decision supplied, eight verbatim items/statuses/owners | OPEN=1 section, OPEN=8 items |
| §8 errors and always-false flags | 25 reachable-code rejection/restore cases plus constructor-only MOCK_INVARIANT; mock/property flag checks | 26 code rows and 11 flag rows, all scoped COVERED |
| DLG predicates | Pointers to existing AI_DELEGATION_LAYER_MATRIX rows | No DLG row copied, regraded or closed |

No existing test, mock or contract was changed and no duplicate behavior tests
were added. The new checker fills the structural drift gap: heading/title
completeness, ordered codes/flags/open items, count lines, verbatim owners,
ECC pointers, DLG references, execution-off posture, and canonical allowed test
paths with AST symbol validation. It resolves transitive in-module TestCase
bases and accepts BackendConformance only with a concrete test_faults consumer.
It never imports tests or reads the frozen reference tree.
Its 86 in-memory negative controls plus synthetic inheritance and temporary
symlink-escape checks exercise these rejection paths.

## Commands actually run and results

Narrow checks ran first, followed by the complete stdlib workflow step, then
all five offline suites and the local HTTP/readiness workflow step. Results
below are actual local runs, not historical CI results. Shell inspection/read
commands were also used to read governance, contracts, workflows and test bodies.

| Command | Actual result |
|---|---|
| `git rev-parse origin/main HEAD` | Both `a0db1e226e27b1c5f60ee938fb528ff795907056`, before and after |
| `git branch --show-current` | `agent/kix-plan-ai-delegation-contract-clause-evidence-m` |
| `python3 --version` | Python 3.13.5 |
| `python3 scripts/check_ai_delegation_evidence_map.py` (initial) | Exit 0; 11 headings/rows, 26 codes, 11 flags, 8 items |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` (initial) | Exit 1: missing-banner control removed one of two occurrences; checker correctly still found the remaining phrase. Fixed the control to remove all occurrences. |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` (after fix) | Exit 0; 86 negative controls, transitive TestCase selection and symlink fencing pass |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` (narrow) | Exit 0; 85 tests, OK |
| `bash -ex /tmp/aid-stdlib.sh > /tmp/aid-stdlib.log 2>&1` | Exit 0; all 37 commands extracted verbatim/deindented from the edited protocol.yml stdlib run block completed (individual results below) |
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=245 indexed=210 allowlisted=35 |
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
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0; settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0; self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0; bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0; self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0; credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0; self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=2 items=9 citations=38 COVERED=1 PARTIAL=6 NOT_COVERED=2 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; self-test: pass (72 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0; ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0; self-test: pass (86 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

The temporary stdlib script was produced from the `Stdlib offline document
checks` run block with this extraction (no YAML dependency):

```python
workflow = Path('.github/workflows/protocol.yml').read_text()
block = workflow.split('      - name: Stdlib offline document checks\n', 1)[1].split('        run: |\n', 1)[1].split('      - ', 1)[0]
commands = '\n'.join(line[10:] for line in block.splitlines() if line.startswith('          ')) + '\n'
Path('/tmp/aid-stdlib.sh').write_text(commands)
```

The next shell loop was actually run; the expanded commands and their results
are listed below in loop order:

```sh
for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/$suite" -t "reference/$suite" || exit; done
```

| Command | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; 196 tests, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; 412 tests, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | Exit 0; 148 tests, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | Exit 0; 85 tests, OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; 168 tests, OK |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0; 100 tests, OK; integration self-test pass. Repeated with output redirected to `/tmp/aid-integration.log` because the first tool output was truncated; the repeat also passed (100 tests). |
| `python3 -m unittest readiness.test_conformance_sensitivity` | Exit 0; 8 tests, OK |
| `python3 scripts/check_openapi_contract.py` | Exit 0; commands=84 core=40 fsm=44; sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e; gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test pass |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test pass |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: required blobs match (see below) |
| `git diff --quiet origin/main -- reference/v0.3-rc1 .aiops docs/tasks docs/contracts reference/ai_delegation docs/status/AI_DELEGATION_LAYER_MATRIX.md docs/status/CONTRACT_ERROR_CODE_COVERAGE.md runtime/ARCHITECTURE.toml` | Exit 0; no tracked changes in any listed path |
| `git status --porcelain reference/v0.3-rc1 .aiops docs/tasks` | Exit 0; empty |
| `git diff --check` | Exit 0; no whitespace errors |

The combined integration/readiness run emitted Python 3.13 ResourceWarnings for
unclosed subprocess text streams in the existing test harness. Both runs still
completed successfully; no unrelated harness change was made.

## Locks, CI and non-claims

Both files were verified before and after the work:

| Locked file | Required and observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`reference/v0.3-rc1/**` is untouched. Contracts, existing mock/tests, matrix,
ECC, architecture flag, .aiops and task documents have no tracked changes.

| Remote evidence | Run ID | Status/conclusion |
|---|---|---|
| Exact-head KTX kernel verification | Not available | Not run/queried; no final committed patch head, supervisor owns publication |
| Exact-head KIX protocol verification | Not available | Not run/queried; local equivalents above only |
| Merge commit / post-merge main CI | Not applicable | No merge |

Rust tests/Clippy/formatting, Move, localnet and ZK jobs were not run: no such
code or inputs were changed. The closest touched-path equivalents were the full
stdlib step, offline reference/OpenAPI step and local HTTP/readiness step.
This is builder-local READY for supervisor handoff, **not merge-ready** under
AGENTS.md §10; final commit, exact-head CI and non-author review remain separate.

## Deviations, uncertainty and follow-up

- Fetch was omitted under the supervisor's no-network instruction. There is no
  remote freshness claim, and no base change was made.
- §3 is PARTIAL instead of the proposed COVERED because the existing four-entry
  authority-list test is a Class B characterization accepting either code.
  It is not evidence of exact malformed-input precedence. No mock fix or
  contract interpretation was introduced.
- Python 3.13.5 was available locally rather than CI's requested 3.12.
- The initial banner negative-control defect and fix are recorded above.
- Existing contract-undefined observations remain open: simultaneous violation
  precedence, omitted/empty/null binding distinctions, returned-data copy
  ownership, and malformed authority-list code precedence. The checker does
  not judge their semantics. No new explicit contract violation was established.
- All eight §9 items retain their verbatim contract status and owner; DLG layer
  gaps remain in the existing matrix. Policy values, authoritative clock/cut,
  identity, bindings, legal character and enablement are not selected here.
- `delegated_execution_enabled = false` remains unchanged. Enablement is a
  User/Astra decision under `ai-delegation-execution-decision`.
- No durability, distributed fencing, bank exactly-once, funds receipt, chain
  finality, identity/signing, legal effect, production runtime/readiness or
  independent acceptance is claimed. The checker verifies structure and test
  existence, not semantic adequacy. Register inventory sync and non-author
  exact-head review remain follow-up work outside this patch.
