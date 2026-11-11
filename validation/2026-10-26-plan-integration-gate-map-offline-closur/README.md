# Offline integration-gate map closure

Builder evidence for node `plan-plan-integration-gate-map-offline-closur`.
Task document: supplied node/design prompt, no issue and no node document under
`docs/tasks/`; these immutable inputs were not edited. This is local builder
delivery, not independent A2 review, acceptance, a capability grade change or
merge readiness.

Observed local `origin/main`, base, initial and current committed HEAD:
`e00e68e680d586346abada94500955abfe938ca3`; no local base delta.
Branch: `agent/kix-plan-plan-integration-gate-map-offline-closur`.
Remote freshness is unverified: supervisor forbids fetch and all network/GitHub
actions. Implementation changes remain uncommitted for the supervisor; no final
implementation commit exists yet. Exact-head KTX and KIX CI run IDs, status and
conclusion: unavailable / not run. No merge or post-merge main CI exists here.

Changed paths:

- `integration_gate/test_offline_limits.py`
- `scripts/check_openapi_contract.py`
- `scripts/check_integration_gate_contract_evidence_map.py`
- `.github/workflows/protocol.yml`
- `docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-26-plan-integration-gate-map-offline-closur/README.md`

## Existing coverage mapped before changes

| Requirement | Before | Existing evidence and gap addressed |
|---|---|---|
| G-LIMITS | Partially covered | `TransportTests.test_body_limit_and_request_timeout` uses 64 bytes and 0.5 s; `test_transport_limits_and_malformed_bodies` exceeds the header limit. Neither pins defaults against README or static constant use. |
| G-LOOPBACK-BIND | Partially covered | `OpenApiAndSchemaTests.test_refuses_non_loopback_bind` and `TransportTests.test_loopback_refusal_still_applies_with_a_readiness_directory` check refusal; neither asserts default port. |
| F-REFERENCE-OBSERVED | Partially covered | `TransportTests.test_representative_commands_match_local_call` and `test_transport_limits_and_malformed_bodies` show conflict/spaced identifiers, but the checker lacked the extension/length comparison to ident source. |
| C-ENVELOPE | Partially covered | `check_openapi_contract.validate` pins local parameters/mapping and the representative HTTP test compares calls, but no explicit specification actorContext/protocolDomain comparison was asserted. |
| Existing schemas, source pins and transport markers | Sufficiently covered | Existing `check_openapi_contract.validate/self_test` and `integration_gate.openapi_doc.validate/self_test` retained; no duplicate schema tests. |

Existing test references above are in `integration_gate/test_http_gate.py` and
were inspected as source only in this session.

## Closed (C-ENVELOPE, F-REFERENCE-OBSERVED)

`envelope_domain_problems` checks specification fields, local parameter names,
actor mapping, the separate body-domain extension, the source signature and the
source DOMAIN_MISMATCH comparison. `reference_observed_problems` parses ident's
non-empty string/upper bound/trim predicate and error literal, checks both
Core.execute ident calls and its fingerprint-conflict check, and compares the
observed extensions to these source facts. Reference source bytes are parsed,
never imported or mutated. These are source-informed static checks, not clean-room
independence or execution of the reference core.

Self-tests include all eight planned negatives: rule bound, missing actor block,
error drift, source bound drift, injected protocolDomain property, wrong
specificationField, separate-argument flag and pinnedDomain drift. Five additional
in-memory source negatives remove trimming/actor validation, change the conflict
code/domain comparison, and add a protocol_domain parameter. Each requires its
own diagnostic. Canonical positive controls cover both new checker functions.

The map citation checker additionally rejects a fabricated offline test method,
alone and mixed with a valid citation. No other citation paths were opened.

## Left PARTIAL (G-LIMITS, G-LOOPBACK-BIND)

Four stdlib tests run under a module socket guard. They compare README and literal
default limits, assert constant use through AST, pin the separate request-line
literals, verify all guarded constructors fail, and call only `parse_args([])` to
show 127.0.0.1:8765. Neither `main` nor `build_server` is invoked. CI gains just the
new test invocation in the existing offline step.

HTTP enforcement of default limits and the exact 8192 boundary remain untested.
No bound listener is observed; deployment absence is not runtime acceptance.
Counts now read `rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1`.

## Characterizations and non-claims

AGENTS §8 B: the existing header comparison measures
`len(self.headers.as_string())`, re-serialized characters rather than raw header
bytes. The request-line `readline(65537)` / `> 65536` check is a separate literal,
not body-limit constant use. Both are preserved; no semantics are invented.
No explicit contract violation was found in this bounded static review.

No HTTP/readiness suite was run: `python3 -m unittest integration_gate.test_http_gate readiness.test_faults`
starts a gate and is deliberately excluded by this node. That suite remains
wired in CI; no CI execution or result is claimed. No gate was started or socket
opened. No Rust paths changed, so Rust builds/tests/Clippy/formatting were not run;
kernel evidence here is locked-blob identity only. No funds, PG/bank/KYC calls,
Sui execution, public endpoints, storage engine, production runtime, secrets,
new protocol commands, product policy, durability or authentication verification.

## Deviations

- No fetch under the supervisor's explicit no-network rule; local refs only.
- The planned function replacement for `socket.socket` broke the stdlib ssl
  import with TypeError because ssl subclasses socket.socket. The first narrow
  run had three passes and one import error, without a socket attempt. Fixed the
  guard using a subclass whose construction raises OSError; socket connection
  helpers remain raising functions. No server refactor or behavior change.
- Added five source-negative controls beyond the eight planned document/source
  fixtures to exercise source predicate/signature rejection directly.

## Commands and actual results

Local Python: `Python 3.13.5` (`python3 --version`); workflow requests Python
3.12. No dependencies were installed. The foreground stdlib harness ran the narrow
compile/test first, then five reference suites and the offline pin block, then all
53 document-check commands in workflow order. All 65 commands exited 0. The
harness set `PYTHONDONTWRITEBYTECODE=1` for child processes; reference commands
also retain that prefix exactly as CI does. No jobs ran in the background.

### Initial checks and corrected narrow run

| Command | Actual result |
|---|---|
| `git rev-parse origin/main HEAD` (before and after implementation) | Exit 0; both e00e68e680d586346abada94500955abfe938ca3. |
| `git status --short` (initial) | Exit 0; clean. |
| `git branch --show-current` | Exit 0; agent/kix-plan-plan-integration-gate-map-offline-closur. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before) | Exit 0; 69564b166f0c27f9af5d8422f0a466b18d74c20f and b607996c83a119c349f1cc90469ac1ba82764e20. |
| `sha256sum docs/contracts/openapi/*.json > /tmp/kix-offline-openapi-before.sha256` | Exit 0; three baseline digests below. |
| `python3 -m py_compile scripts/check_openapi_contract.py scripts/check_integration_gate_contract_evidence_map.py integration_gate/test_offline_limits.py` (initial and after guard fix) | Exit 0 both runs. |
| `python3 -m unittest -v integration_gate.test_offline_limits` (initial) | Exit 1; 4 tests: 3 passed, port test had TypeError during ssl import because socket.socket was replaced by a function. No socket opened. |
| `python3 -m unittest -v integration_gate.test_offline_limits` (after guard fix) | Exit 0; all 4 passed under the class-based socket guard. |
| `python3 scripts/check_openapi_contract.py` (narrow, before final source-error extraction refinement) | Exit 0; commands=84 core=40 fsm=44. |
| `python3 scripts/check_openapi_contract.py --self-test` (same narrow run) | Exit 0; 13 new negatives and 11 retained detected diagnostics; self-test: pass. |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` (after map edits) | Exit 0; Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1. |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` (same narrow run) | Exit 0; 85 negative controls and positive/status controls pass. |
| `python3 scripts/check_integration_gate_openapi.py` (same narrow run) | Exit 0; commands=84 productionEndpoint=false publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` (same narrow run) | Exit 0; self-test: pass. |
| `python3 scripts/check_ci_checker_wiring.py` (same narrow run) | Exit 0; scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=67. |
| `python3 scripts/check_ci_checker_wiring.py --self-test` (same narrow run) | Exit 0; 13 negative controls pass. |

### Final code: narrow tests and protocol offline step

The tables below were generated from the actual foreground command results.

| Command | Actual result |
|---|---|
| `python3 -m py_compile scripts/check_openapi_contract.py scripts/check_integration_gate_contract_evidence_map.py integration_gate/test_offline_limits.py` | Exit 0; no diagnostic output |
| `python3 -m unittest -v integration_gate.test_offline_limits` | Exit 0; Ran 4 tests in 0.036s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/settlement_f01_f03" -t "reference/settlement_f01_f03"` | Exit 0; Ran 196 tests in 1.929s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/booking_resale_admission" -t "reference/booking_resale_admission"` | Exit 0; Ran 418 tests in 9.289s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/credit_advance_f04" -t "reference/credit_advance_f04"` | Exit 0; Ran 148 tests in 8.502s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/ai_delegation" -t "reference/ai_delegation"` | Exit 0; Ran 85 tests in 2.939s; OK |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s "reference/token_reward" -t "reference/token_reward"` | Exit 0; Ran 168 tests in 1.911s; OK |
| `python3 scripts/check_openapi_contract.py` | Exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; self-test: pass; 24 detected diagnostics (13 new, 11 retained) |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test: pass |
| `python3 -m unittest integration_gate.test_offline_limits` | Exit 0; Ran 4 tests in 0.034s; OK |

### Protocol stdlib offline document block

All 53 commands ran in the workflow order below.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=275 indexed=240 allowlisted=35 |
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
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0; primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0; self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0; ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0; self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0; lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0; self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0; contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0; contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0; Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0; Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0; BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=22 PARTIAL=15 NOT_COVERED=2 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; feature semantics evidence map ok: Counts: rows=41 COVERED=3 PARTIAL=21 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; self-test: pass (77 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0; integration gate contract evidence map ok: Counts: rows=54 COVERED=37 PARTIAL=16 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0; self-test: pass (85 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=67 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

### Final scope and identity checks

| Command | Actual result |
|---|---|
| `python3 /tmp/kix-offline-scope-audit.py` | Exit 0; only four map rows plus Counts differ, all 50 other rows and sections outside the map preserved, only the one offline unittest line added to CI, exactly seven authorized paths changed, protected paths have no edits or untracked additions. |
| `sha256sum --check /tmp/kix-offline-openapi-before.sha256` | Exit 0; all three JSON files OK. |
| `git diff --exit-code HEAD -- docs/contracts/openapi integration_gate/server.py integration_gate/constants.py integration_gate/test_http_gate.py reference/v0.3-rc1 .aiops docs/tasks runtime` (run by scope audit) | Exit 0; empty diff. |
| `git ls-files --others --exclude-standard -- docs/contracts/openapi integration_gate/server.py integration_gate/constants.py integration_gate/test_http_gate.py reference/v0.3-rc1 .aiops docs/tasks runtime` (run by scope audit) | Exit 0; empty list. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (after) | Exit 0; 69564b166f0c27f9af5d8422f0a466b18d74c20f and b607996c83a119c349f1cc90469ac1ba82764e20; both match before and required locks. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `rg -n 'integration_gate.test_offline_limits' .github/workflows/protocol.yml` | Exit 0; line 281, one invocation in the existing offline step. |
| `git status --short --untracked-files=all` | Exit 0; exactly the seven changed paths listed above. |
| `python3 --version` | Exit 0; Python 3.13.5. |

The scratch scope audit compares HEAD and worktree while filtering only the four
allowed row IDs and Counts; everything remaining must match. It independently
counts statuses, checks the exact single-line workflow addition, checks the
complete changed-path set, and checks protected tracked and untracked paths.
It is a local verification helper, not a new repository checker or deliverable.

OpenAPI sha256 before and after:

| File under docs/contracts/openapi/ | sha256 (unchanged) |
|---|---|
| fsm-command-contract.json | 342e97cb37b199622d7bb436ca9164690d969b797058aaa539ff417cab01411c |
| kix-protocol.contract-only.openapi.json | 2248ff67aa0f43cb98bdd492f63b36fce64c53def6a403a97a7987a128b2d2dc |
| kix-protocol.integration-gate.openapi.json | d05beb48c234b924af086b886ce9bb524dc34407ad2e4a57f1e8af84255820f6 |

Remaining follow-up candidates are default-limit HTTP enforcement, the exact
header boundary, and bound-listener observation on an authorized host. These stay
PARTIAL; no host permission, policy decision or implementation is inferred here.
