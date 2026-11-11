# Offline integration-gate map gap checks

Builder evidence for node `plan-plan-integration-gate-map-offline-checke`.
Task document: supplied node/design prompt; no issue or task file under `docs/tasks/`.
Local verification is being recorded below; this is not independent A2 review,
acceptance, merge authorization or exact-head CI evidence.

Observed local `origin/main`, base and initial branch HEAD:
`a176c1f22c0af21500cb52a777bc889b808e561c`; no local delta.
Branch: `agent/kix-plan-plan-integration-gate-map-offline-checke`.
No fetch: supervisor explicitly prohibits network/GitHub actions; remote freshness
is unverified. No commits, pushes, issues, comments, PRs or merges are authorized.
Implementation and final committed task head remain the initial HEAD; the patch
is uncommitted for supervisor delivery. KTX/KIX exact-head CI and post-merge run
IDs/status/conclusions: not run, unavailable in this local-only session.

Changed paths:

- `scripts/check_openapi_contract.py`
- `docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md`
- `docs/README.md`
- `validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md`

## Existing coverage mapped before changes

| Requirement | Before | Existing evidence and gap addressed |
|---|---|---|
| README table matches both document pins | Not covered | No README parity function; new readme_pin_problems compares nine labels with both sources and contract-only status. |
| Added command and security injection fail | Partially covered | check_openapi_contract.validate rejects schema-name drift and securitySchemes; self_test lacked these two negative fixtures. |
| No OPTIONS in either paths object | Partially covered | Both validators already forbid servers/security; neither explicitly rejected OPTIONS. New validate loop rejects it in either document. Historical byte identity remains outside this checker. |
| Gate public/production flags remain false | Partially covered | integration_gate.openapi_doc.validate already checks markers; contract checker now checks three flags and self_test flips each independently, requiring both validators to reject it. HTTP /ready publicHost assertion remains absent. |
| Existing schema/pin/lost-field/URL rejection | Sufficiently covered | Existing check_openapi_contract.validate/self_test and integration_gate.openapi_doc.validate/self_test retained. |

New in-memory negatives: added command, security scheme, contract-only OPTIONS,
gate OPTIONS, gate publicHost, liveHttpServer.publicHost, productionEndpoint,
README sha256 mismatch, missing FSM domain row, duplicated git blob row, and gate
source sha256 drift. Each requires its specific diagnostic. Positive controls
validate the canonical contract-only document, committed gate document and README.

## Commands and actual results

| Command | Actual result |
|---|---|
| `git status --short` (initial) | Exit 0; clean. |
| `git rev-parse origin/main HEAD` | Exit 0; both a176c1f22c0af21500cb52a777bc889b808e561c. |
| `git branch --show-current` | Exit 0; agent/kix-plan-plan-integration-gate-map-offline-checke. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before) | Exit 0; 69564b166f0c27f9af5d8422f0a466b18d74c20f and b607996c83a119c349f1cc90469ac1ba82764e20. |
| `python3 -m py_compile scripts/check_openapi_contract.py` | Exit 0. |
| `python3 scripts/check_openapi_contract.py` (before map edits) | Exit 0; commands=84 core=40 fsm=44; source sha256 ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e, gitBlob 619ae21c82ca3df5661bd3831613f15fa65225ff. |
| `python3 scripts/check_openapi_contract.py --self-test` (before map edits) | Exit 0; all 11 new negatives printed detected with their specific diagnostic, then self-test: pass. |

### Protocol workflow stdlib block

All 53 commands from the committed workflow run block ran in order. Each
exit code and the final output line are recorded below.

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0; capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0; rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0; read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0; self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0; docs index ok: scanned=270 indexed=235 allowlisted=35 |
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
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0; performance evidence map ok: Counts: rows=42 COVERED=17 PARTIAL=20 NOT_COVERED=2 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0; self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0; feature semantics evidence map ok: Counts: rows=41 COVERED=1 PARTIAL=23 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0; self-test: pass (77 negative controls, injected positive control) |
| `python3 scripts/check_integration_gate_contract_evidence_map.py` | Exit 0; integration gate contract evidence map ok: Counts: rows=54 COVERED=35 PARTIAL=18 NOT_COVERED=1 |
| `python3 scripts/check_integration_gate_contract_evidence_map.py --self-test` | Exit 0; self-test: pass (83 negative controls; injected positive and valid status controls) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0; ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=64 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0; self-test: pass (13 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0; self-test: pass |

### Reference, gate and SDK checks

| Command | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | Exit 0; 196 tests; OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | Exit 0; 418 tests; OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | Exit 0; 148 tests; OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | Exit 0; 85 tests; OK. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; 168 tests; OK. |
| `python3 scripts/check_openapi_contract.py` | Exit 0; openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff |
| `python3 scripts/check_openapi_contract.py --self-test` | Exit 0; 11 new detected diagnostics; self-test: pass. |
| `python3 scripts/check_integration_gate_openapi.py` | Exit 0; integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | Exit 0; self-test: pass |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | Exit 0; 100 tests; OK. |
| `python3 scripts/check_sdk_client.py` | Exit 1; node 20.19.2 does not match toolchains.json nodeMajor 24 |
| `python3 scripts/check_sdk_client.py --self-test` | Exit 1; node 20.19.2 does not match toolchains.json nodeMajor 24 |
| `/home/box/.local/share/cursor-agent/versions/2026.10.14-0f9edde/node -p process.versions.node` | Exit 0; 24.5.0. |
| `PATH=/home/box/.local/share/cursor-agent/versions/2026.10.14-0f9edde:$PATH python3 scripts/check_sdk_client.py` | Exit 0; sdk client pin ok: commands=84 node=24.5.0 sourceSha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e. |
| `PATH=/home/box/.local/share/cursor-agent/versions/2026.10.14-0f9edde:$PATH python3 scripts/check_sdk_client.py --self-test` | Exit 0; self-test: pass. |

The first SDK attempts stopped at the toolchain guard before running their
checks. A read-only search found the already-installed Node 24.5.0 binary;
rerunning with only PATH changed passed both modes. No download, installation,
SDK modification or toolchain relaxation was performed.

New negative diagnostics from the actual self-test output:

```text
self-test: detected added command: schema names drifted from protocol_contract.json commands
self-test: detected security scheme: forbidden transport or auth field: securitySchemes
self-test: detected contract-only OPTIONS: OPTIONS operation forbidden: contract-only /x-kix-contract-only/local-call
self-test: detected gate OPTIONS: OPTIONS operation forbidden: integration-gate /x-kix-contract-only/local-call
self-test: detected gate publicHost: integration-gate publicHost must be false
self-test: detected gate liveHttpServer.publicHost: integration-gate liveHttpServer.publicHost must be false
self-test: detected gate productionEndpoint: integration-gate productionEndpoint must be false
self-test: detected README sha256: README pin table mismatch: sha256 != contract-only sha256
self-test: detected README row removed: README pin table missing row: FSM domain
self-test: detected README row duplicated: README pin table duplicated row: git blob
self-test: detected gate pin drift: README pin table mismatch: sha256 != integration-gate sha256
self-test: pass
```

### Scope and preservation checks

| Command | Actual result |
|---|---|
| Inline Python scope audit (below) | Exit 0; exactly four authorized map rows and four changed paths; User/Astra/host rows and non-claims unchanged. |
| `git diff -U0 docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md` | Exit 0; only the four listed rows, Counts, Basis revision bullet and Other gaps paragraph changed. |
| `git diff --exit-code HEAD -- docs/contracts/openapi integration_gate .github reference/v0.3-rc1 .aiops docs/tasks runtime` | Exit 0; no diff. OpenAPI documents, gate sources, CI, protected reference, program/task inputs and runtime match HEAD. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (after) | Exit 0; 69564b166f0c27f9af5d8422f0a466b18d74c20f and b607996c83a119c349f1cc90469ac1ba82764e20 match the before/required blobs. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `git status --short --untracked-files=all` | Exit 0; exactly the four paths listed above (three modified, validation README new). |
| `git rev-parse origin/main HEAD` (after) | Exit 0; both remain a176c1f22c0af21500cb52a777bc889b808e561c. |

Scope audit executed from the repository root:

```python
from pathlib import Path
import subprocess
path = 'docs/status/INTEGRATION_GATE_CONTRACT_EVIDENCE_MAP.md'
before = subprocess.check_output(['git', 'show', 'HEAD:' + path], text=True)
after = Path(path).read_text()
def rows(text):
    return {line.split('|')[1].strip(): line for line in text.splitlines() if line.startswith('| ')}
old, new = rows(before), rows(after)
assert old.keys() == new.keys()
changed = {key for key in old if old[key] != new[key]}
assert changed == {'P-README-TABLE-MIRROR', 'CHK-CONTRACT-FAILS', 'G-OPENAPI-NO-CORS-CHANGE', 'G-NO-PUBLIC'}, changed
for key, line in old.items():
    if line.rstrip('| ').endswith(('User', 'Astra', 'Supervisor / repository owner controlling the execution host')):
        assert line == new[key], key
assert before.split('## 5. Non-claims', 1)[1] == after.split('## 5. Non-claims', 1)[1]
expected = {'scripts/check_openapi_contract.py', path, 'docs/README.md', 'validation/2026-10-26-plan-integration-gate-map-offline-checke/README.md'}
status = subprocess.check_output(['git', 'status', '--short', '--untracked-files=all'], text=True)
assert {line[3:] for line in status.splitlines()} == expected, status
print('scope audit ok: exactly four authorized map rows and four changed paths; User/Astra/host rows and non-claims unchanged')
```

## Findings, boundaries and deviations

Class A: committed README pins and gate markers match; no committed OPTIONS
operation was found. Class C: none found by the new checks. No new class B
characterization or policy value supplied. Existing undefined authentication,
retry/transport and commerce binding boundaries stay open with their owners.
Only P-README-TABLE-MIRROR, CHK-CONTRACT-FAILS, G-OPENAPI-NO-CORS-CHANGE and
G-NO-PUBLIC change; no User/Astra/host-owned row changes.

No gate/server behavior, HTTP test, protocol command, contract, OpenAPI or pin
bytes are changed. kyc_verify is solely an in-memory negative fixture. No real
funds, provider calls, secrets, public endpoints, Sui execution, storage engine,
production runtime or external exactly-once evidence is involved. No Rust source
changes; scoped kernel evidence is blob equality, not Rust tests/build/Clippy.
No historical OpenAPI byte-identity claim, runtime publicHost response assertion,
independent review, production readiness or full repository CI pass is claimed.

Deviation: session-start fetch omitted under the explicit supervisor no-network
rule. Publication and final exact-head CI remain supervisor responsibilities.

Implementation follows the supplied design. The SDK toolchain PATH adjustment
above is an environment-only verification deviation; its initial failures are
retained as evidence. All requested acceptance commands passed. Remaining
follow-ups are historical browser-change byte identity and HTTP response
publicHost assertion, both still PARTIAL and owned by integration_gate maintainer.
The seeded-journey host stop, User/Astra-owned decisions and capability grades
are unchanged. No merge-readiness or production claim is made.
