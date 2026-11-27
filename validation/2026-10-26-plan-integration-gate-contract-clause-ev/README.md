# Integration gate contract evidence map validation

Builder-authored record, not A2 review, acceptance, a capability grade change or merge readiness.

Node: `plan-plan-integration-gate-contract-clause-ev`. No issue and no task document under `docs/tasks/`: the supplied node/design prompt is the task input. Branch: `agent/kix-plan-plan-integration-gate-contract-clause-ev`.

Locally observed `origin/main`, base and unchanged HEAD: `22d05a0c82693ad4575a72c2d342b4e47114447f`; no local delta. Fetch omitted under the supervisor's explicit no-network instruction; remote freshness is unverified. Implementation/final committed task head: none created; delivery is five uncommitted files on that HEAD. Merge commit: none. KTX exact-head CI, KIX exact-head CI and post-merge CI: no run IDs/status/conclusion available; not invoked or claimed. Supervisor owns subsequent Git/GitHub actions.

HTTP suite runs only where loopback is permitted (CI or an authorized local host). This host permitted loopback: the unchanged suite passed locally. No tests, gate code or fixtures were changed.

Changed paths (complete):

- `.github/workflows/protocol.yml`: exactly two checker invocation lines, plain and self-test.
- `docs/README.md`: one index bullet linking map and this record.
- `docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md`: 54 normative-clause rows (33 COVERED, 19 PARTIAL, 2 NOT_COVERED), owned gaps and non-claims.
- `scripts/check_integration_gate_contract_evidence_map.py`: static stdlib citation/anchor/status/count/path/AST/lock/workflow checks and 83 in-memory negative controls.
- `validation/2026-10-26-plan-integration-gate-contract-clause-ev/README.md`: this record.

Locked blobs verified before work and again after work: `runtime/crates/kix-kernel/src/lib.rs` = `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` = `b607996c83a119c349f1cc90469ac1ba82764e20`. Final-merge verification is not applicable. Contract README blob: `1fa6676860710e6bad6d882a57a91972407e2e41`.

Existing coverage mapping: the [map](../../docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md) records assertion-level coverage before adding any HTTP tests (none added). The 83 checker fixtures address structural/citation drift, status consistency, required open gaps, forbidden imports, locks and workflow commands; they never start a server, open sockets or import gate code. Citation existence does not establish semantic coverage.

Narrow verification ran first: `python3 -m py_compile scripts/check_integration_gate_contract_evidence_map.py`, then the checker plain and with `--self-test` (all exit 0; 54 rows, 83 negative controls detected). Next, all 53 lines of the actual protocol workflow's `Stdlib offline document checks` block ran in order, followed by its four OpenAPI pin lines; all 57 commands exited 0. The actual per-command results follow.

Commands below use `PYTHONDONTWRITEBYTECODE=1` and run sequentially in the foreground.

| Command | Exit | Result |
|---|---|---|
| `python3 scripts/check_status_register.py` | 0 | capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | 0 | rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | 0 | read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=267 indexed=232 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | 0 | i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | 0 | delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | 0 | rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | 0 | rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | 0 | tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | 0 | contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | 0 | adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | 0 | v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | 0 | readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | 0 | settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | 0 | self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | 0 | bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | 0 | self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | 0 | credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | 0 | self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | 0 | primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | 0 | self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | 0 | ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | 0 | self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | 0 | lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | 0 | self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | 0 | contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | 0 | contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | 0 | Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | 0 | Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | 0 | BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | 0 | self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | 0 | performance evidence map ok: Counts: rows=42 COVERED=17 PARTIAL=20 NOT_COVERED=2 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | 0 | self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | 0 | feature semantics evidence map ok: Counts: rows=41 COVERED=1 PARTIAL=23 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | 0 | self-test: pass (77 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | 0 | integration gate contract evidence map ok: Counts: rows=54 COVERED=33 PARTIAL=19 NOT_COVERED=2 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | 0 | self-test: pass (83 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_ci_checker_wiring.py` | 0 | ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=59 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | 0 | self-test: pass (13 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_openapi_contract.py` | 0 | openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_integration_gate_openapi.py` | 0 | integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | 0 | self-test: pass |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 0 | ............................................................; ----------------------------------------------------------------------; Ran 100 tests in 7.103s; OK |

HTTP suite attempt (actual selected output):

```text
Ran 100 tests in 7.103s
OK
```

Final verification after document completion and checker constant formatting:

| Command | Exit | Result |
|---|---|---|
| `python3 -m py_compile scripts/check_integration_gate_contract_evidence_map.py` | 0 | pass; no output |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | 0 | integration gate contract evidence map ok: Counts: rows=54 COVERED=33 PARTIAL=19 NOT_COVERED=2 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | 0 | self-test: pass (83 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --invalid` | 2 | usage: check_integration_gate_contract_evidence_map.py [--self-test] (expected usage rejection) |
| `python3 scripts/check_docs_index.py` | 0 | docs index ok: scanned=267 indexed=232 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | 0 | self-test: pass |
| `python3 scripts/check_ci_checker_wiring.py` | 0 | ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=59 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | 0 | self-test: pass (13 negative controls) |
| `git diff --check` | 0 | pass; no output |
| `git diff --numstat -- .github` | 0 | 2	0	.github/workflows/protocol.yml |
| `git diff --exit-code HEAD -- integration_gate docs/contracts/openapi reference/v0.3-rc1 .aiops docs/tasks runtime docs/status/CURRENT_CAPABILITY_REGISTER.md` | 0 | pass; no output |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | 0 | Both required blobs match (before and after work) |
| `git rev-parse origin/main HEAD` | 0 | Both 22d05a0c82693ad4575a72c2d342b4e47114447f |
| `python3 --version` | 0 | Python 3.13.5 |
| `git status --short` | 0 | Exactly five intended paths; no other changes |

Deviations and observations:

- The supervisor's later explicit no-network rule overrides the session-start fetch. Local base and HEAD match; no rebase or base change was made.
- Current source has 11 BrowserAccessTests test methods, rather than the design's stated 10. Existing names/assertions were used; no test was added.
- Assertion review lowered several proposed statuses. In particular, K-READINESS-FSM-REFUSED is PARTIAL: the existing fixture uses one FSM command and an imported refusal constant. Its spelling remains Astra-owned. Same-process replay is PARTIAL because the HTTP fixture does not vary actor and action independently. Lowered statuses identify coverage gaps, not implementation failures.
- The unchanged HTTP suite passed on this loopback-capable host. Its output included `ResourceWarning: unclosed file <_io.TextIOWrapper name=5 encoding='UTF-8'>`; no failure or socket denial occurred. CI's HTTP step still skips docs-only and verified-tree runs. This local pass does not supply exact-head CI evidence or close the seeded-journey owner stop.
- The self-test has 83 negative controls (more than the proposed approximately 40), including each forbidden import separately, mixed valid/invalid citation cells and synthetic valid PARTIAL/NOT_COVERED controls. Each negative must emit its expected diagnostic, not merely fail incidentally.
- An initial map-generation heredoc had a Python SyntaxError before writing any file; it was corrected before the narrow verification. No check/test failure required gate, contract or CI behavior changes. The only CI change is the two authorized checker invocations.
- Rust compilation, workspace tests, Clippy and formatting were not run: no Rust paths changed. The two blob checks are the scoped local KTX evidence; they do not replace KTX workflow execution.

Contract findings and remaining uncertainty:

- AGENTS §8 A: reviewed bounded schema/pin, loopback, dispatch, browser and optional-journal assertions match the mapped behavior.
- B: no new characterization. Authentication of actor, retry/transport semantics and commerce-app binding remain undefined here. The readiness map's three existing recovery characterizations remain open with Astra.
- C: no explicit contract violation found. No diagnostic reproduction or DECISION_REQUIRED is needed for this map/checker node.
- `plan-plan-gate-fsm-seeded-journey-differentia` is not implemented in this node. Owner remains Supervisor / repository owner controlling the execution host, per the [addendum](../../docs/status/OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia). Its separate candidate and verification remain unavailable here; the 100-test local run does not contain that candidate.
- Other follow-ups are exactly the 19 PARTIAL and 2 NOT_COVERED map rows, including README table parity, default port/limit boundaries, publicHost assertions and consumer trust/binding. This node resolves no policy value or owner decision.
- No production endpoint, live funds/provider calls, chain finality, production durability, external exactly-once, independent A2 review, capability upgrade or merge readiness is claimed. No Git publication or GitHub action was taken.

Delivery state: READY for supervisor review of the uncommitted five-path patch. Exact-head review, CI and merge decisions remain with the supervisor/user workflow.
