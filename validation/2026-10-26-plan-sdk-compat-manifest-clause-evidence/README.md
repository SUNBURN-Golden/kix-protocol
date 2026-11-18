# Validation — SDK compatibility manifest clause evidence

## Task and basis

- Task ID `plan-plan-sdk-compat-manifest-clause-evidence`. Task input is the supervisor's node specification and the 2026-11-18 owner decision (pt224u), now recorded in-tree as [docs/decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md](../../docs/decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md) (fix round 1; see the fix-round-1 section below). There is no issue or task file under `docs/tasks/`.
- Branch `agent/kix-plan-plan-sdk-compat-manifest-clause-evidence`, local base and unchanged branch HEAD `22d05a0c82693ad4575a72c2d342b4e47114447f`. The observed local `origin/main` ref was `b2357bc4d3f6de2e7dd0a09f53596f24d0a944f7`, 339 commits ahead. The supplied branch was retained. The supervisor's no-network rule superseded the session-start fetch.
- Implementation and final delivery are uncommitted. KTX kernel verification and KIX protocol verification have no exact-head run ID, status or conclusion for this worktree. Merge SHA and post-merge results do not apply.

## Changed paths

| Path | Change |
|---|---|
| `.github/workflows/protocol.yml` | Two checker invocations in the stdlib step. |
| `docs/README.md` | Index entry for this record and the map; links the owner-decision location record (fix round 1). |
| `docs/decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md` | Owner-decision location record (fix round 1): verbatim pt224u decision, provenance, scope, non-claims. |
| `docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md` | 51 clauses with evidence, status, gap and owner. |
| `scripts/check_sdk_compat_manifest_evidence_map.py` | Stdlib checker and in-memory controls. |
| `sdk/compat/verify_compat.mjs` | Profile byte-hash check moved before both OpenAPI references. |
| `sdk/conformance/conformance.test.mjs` | Regression for the §4 stage order and fail-closed exit. |
| `validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/README.md` | This record. |
| `validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py` | Standalone two-fault precedence regression. |

## Coverage and findings

The [map](../../docs/status/SDK_COMPAT_MANIFEST_EVIDENCE_MAP.md) gives the complete coverage mapping. It has 18 COVERED, 31 PARTIAL and 2 NOT_COVERED clauses. The existing canonical vectors assert all eight named reasons. Existing mixed inputs exercise fail-closed behavior with single mutations and establish the bootstrap-2 happy path. The historical bootstrap-1 artifacts are checked by byte pin. The bootstrap-2 reproduction check writes comparison outputs to temporary directories.

The inherited §4 class C discrepancy reproduced on the supplied verifier. The new conformance test failed before the fix because the profile byte hash came after OpenAPI, generator/toolchain and output. It now verifies that canonical parse failures gate all later checks and that the named stages report diagnostics in contract order. The two-fault regression supplies a valid sidecar and requires the profile hash to be the first error. Both use temporary manifests. C4-CHECK-ORDER is COVERED and the stdlib checker validates the regression citation and source-stage anchors. The source anchors are a drift guard. The conformance test runs the verifier itself.

The new checker accepts one injected positive citation and rejects 71 in-memory negative fixtures. The required four controls detect a missing cited test, duplicate clause ID, wrong row count and a NOT_COVERED row citing a test. Further controls check contract anchors, status/gap/owner rules, stage ordering, locks and citation formats.

The parser's `depth`, `non-canonical` and `invalid-string` and the serializer's `unsupported-value` remain class B characterizations. The contract specifies a depth limit of 32 and leaves the depth reason unspecified. Remaining gaps include depth boundaries, precise unavailable-profile rejection without an expected revision, and profile and artifact validation negatives. The map records follow-up owners by row.

The producer qualification tuple (`docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json`) exists on the newer local `origin/main` ref. Its 18 artifact entries contain no verifier byte pin. The verifier SHA-256 moved from `b1ed26b977666f796a68c5de0a108e5558ca3c98486dc188d385b220a448cf89` to `8628518c41b4110f0adf9a5d841240ae06dc6c1fa5d5c4974f00d96a718c5de6`. No tuple pin update was needed.

## Locked blobs and protected bytes

| Path | Required Git blob | Before | After |
|---|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | match | match |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | match | match |

The direct byte audit matches 229 protected Git blobs against HEAD. This includes generated SDK files, manifests, profiles, sidecars, vectors, OpenAPI, the manifest contract, `reference/v0.3-rc1/`, `.aiops/`, `docs/tasks/` and runtime. The verifier and its conformance test are the two authorized SDK source edits. `DECISION_REQUIRED.md` was absent at resume and final audit.

## Commands actually run and results

Commands ran in the foreground in Python 3.13.5 and Node 24.22.1 (npm 11.21.1). The narrow tests preceded the workflow steps. The workflow runner extracted both named shell blocks from the worktree YAML and executed each listed command in sequence. The full blocks ran again after the last map classification edit.

| Command | Actual result |
|---|---|
| `git status --short --branch`, `git rev-parse HEAD origin/main`, `git rev-list --left-right --count HEAD...origin/main` | Resumed draft on the requested branch. Commit counts 0/339. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required hashes matched at start and at final audit. |
| `node --version`, `npm --version`, `python3 --version` | v24.22.1, 11.21.1 and Python 3.13.5. |
| `node --test --test-name-pattern='manifest verifier reports failures in contract order' sdk/conformance/conformance.test.mjs` | Before fix, exit 1 with profile drift after output. After fix, exit 0 with one test passed. |
| `python3 -I validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py` | Original diagnostic exit 0 with OpenAPI at index 0 and profile at index 1. Revised regression exit 0 with profile at index 0, OpenAPI at index 1 and verifier exit 1. |
| `PYTHONPYCACHEPREFIX=/tmp/kix-sdk-evidence-pycache python3 -m py_compile scripts/check_sdk_compat_manifest_evidence_map.py validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py` | Exit 0. |
| `python3 scripts/check_sdk_compat_manifest_evidence_map.py --invalid` | Exit 2 with usage text, as expected. |
| `python3 scripts/check_openapi_contract.py` and `python3 scripts/check_openapi_contract.py --self-test` | Both exit 0. Pin for 84 commands (40 core and 44 FSM) and self-test passed. |
| `python3 scripts/check_integration_gate_openapi.py` and `python3 scripts/check_integration_gate_openapi.py --self-test` | Both exit 0. Pin for 84 commands with productionEndpoint=false and publicHost=false and self-test passed. |
| `git show origin/main:docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json` with an inline JSON artifact-path check | Exit 0. The verifier is absent from all 18 tuple artifacts. |
| Read-only `git merge-file -p` previews, using base and newer local main bytes from `git show` | SDK verifier and test merged cleanly. One insertion conflict each in workflow and docs index. |
| `git diff --check` and `git diff --numstat HEAD -- .github` | Exit 0. Workflow diff +2/-0. |
| `git diff --exit-code HEAD -- sdk docs/contracts reference/v0.3-rc1 .aiops docs/tasks runtime docs/status/CURRENT_CAPABILITY_REGISTER.md ':(exclude)sdk/compat/verify_compat.mjs' ':(exclude)sdk/conformance/conformance.test.mjs'` | Exit 0 with empty diff. |
| Foreground Python byte audit using `git ls-tree -rz HEAD`, `git diff --name-only -z HEAD` and `git ls-files --others --exclude-standard -z` | Exit 0. 229 protected blobs match. Eight delivery paths. Workflow differs only by the two checker invocations. |

### Stdlib offline document checks

| Command | Actual result |
|---|---|
| `python3 scripts/check_status_register.py` | Exit 0. capability register ok: paths=385 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_rs_profile_traceability.py` | Exit 0. rs profile traceability ok: blueprint=47 profile=47 expected=47 |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_read_model_source_map.py` | Exit 0. read model source map ok: queries=13 anchors=128 catalogues=2 citations=145 |
| `python3 scripts/check_read_model_source_map.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_docs_index.py` | Exit 0. docs index ok: scanned=267 indexed=232 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_i12_proof_ids.py` | Exit 0. i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14 |
| `python3 scripts/check_i12_proof_ids.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_delegation_layer_matrix.py` | Exit 0. delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6 |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_rs_predicate_evidence_map.py` | Exit 0. rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2 |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_rs_im_evidence_map.py` | Exit 0. rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2 |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | Exit 0. tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_contract_error_codes.py` | Exit 0. contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0 |
| `python3 scripts/check_contract_error_codes.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_adapter_identity_map.py` | Exit 0. adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8 |
| `python3 scripts/check_adapter_identity_map.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_v5_transition_evidence_map.py` | Exit 0. v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0 |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_readiness_evidence_map.py` | Exit 0. readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9 |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | Exit 0. self-test: pass |
| `python3 scripts/check_settlement_evidence_map.py` | Exit 0. settlement evidence map ok: rows=27 headings=27 citations=110 COVERED=14 PARTIAL=3 NOT_COVERED=2 OPEN=8 |
| `python3 scripts/check_settlement_evidence_map.py --self-test` | Exit 0. self-test: pass (33 negative controls) |
| `python3 scripts/check_bra_evidence_map.py` | Exit 0. bra evidence map ok: rows=39 headings=39 items=9 citations=219 COVERED=22 PARTIAL=14 NOT_COVERED=1 OPEN=2 |
| `python3 scripts/check_bra_evidence_map.py --self-test` | Exit 0. self-test: pass (50 negative controls) |
| `python3 scripts/check_credit_evidence_map.py` | Exit 0. credit evidence map ok: rows=22 headings=22 items=5 citations=128 COVERED=14 PARTIAL=4 NOT_COVERED=1 OPEN=3 |
| `python3 scripts/check_credit_evidence_map.py --self-test` | Exit 0. self-test: pass (55 negative controls) |
| `python3 scripts/check_primary_price_fee_evidence_map.py` | Exit 0. primary price fee evidence map ok: rows=14 headings=14 chain=3 items=9 citations=43 COVERED=1 PARTIAL=7 NOT_COVERED=1 OPEN=5 |
| `python3 scripts/check_primary_price_fee_evidence_map.py --self-test` | Exit 0. self-test: pass (76 negative controls) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | Exit 0. ai delegation evidence map ok: rows=11 headings=11 codes=26 flags=11 items=8 dlg_refs=71 citations=91 COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1 |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | Exit 0. self-test: pass (86 negative controls) |
| `python3 scripts/check_lifecycle_adr_evidence_map.py` | Exit 0. lifecycle/ADR map: 27 rows, anchors, test symbols, grammar, counts and both locked blobs OK |
| `python3 scripts/check_lifecycle_adr_evidence_map.py --self-test` | Exit 0. self-test: positive injected citation and 49 negative fixtures passed (memory only) |
| `python3 scripts/check_contract_invariants_evidence_map.py` | Exit 0. contract invariants map: 27 rows, corpus, anchors, test symbols, counts and locked blobs OK |
| `python3 scripts/check_contract_invariants_evidence_map.py --self-test` | Exit 0. contract invariants self-test: 2 positive controls and 66 negative fixtures OK (memory only) |
| `python3 scripts/check_toss_card_profile_evidence_map.py` | Exit 0. Toss profile map: 41 rows, sections, anchors, test symbols, open items, related IDs, arithmetic and locked blobs OK |
| `python3 scripts/check_toss_card_profile_evidence_map.py --self-test` | Exit 0. Toss profile self-test: 3 positive controls and 77 negative fixtures OK (memory only) |
| `python3 scripts/check_bcs1_evidence_map.py` | Exit 0. BCS1 evidence map ok: Counts: rows=39 COVERED=12 PARTIAL=10 NOT_COVERED=17 |
| `python3 scripts/check_bcs1_evidence_map.py --self-test` | Exit 0. self-test: pass (2 positive controls, 50 negative fixtures) |
| `python3 scripts/check_performance_measurement_evidence_map.py` | Exit 0. performance evidence map ok: Counts: rows=42 COVERED=17 PARTIAL=20 NOT_COVERED=2 NOT_RUN=3 |
| `python3 scripts/check_performance_measurement_evidence_map.py --self-test` | Exit 0. self-test: pass (2 positive controls, 66 negative fixtures; memory only) |
| `python3 scripts/check_feature_semantics_evidence_map.py` | Exit 0. feature semantics evidence map ok: Counts: rows=41 COVERED=1 PARTIAL=23 NOT_COVERED=17 |
| `python3 scripts/check_feature_semantics_evidence_map.py --self-test` | Exit 0. self-test: pass (77 negative controls, injected positive control) |
| `python3 scripts/check_sdk_compat_manifest_evidence_map.py` | Exit 0. sdk compat evidence map ok: Counts: rows=51 COVERED=18 PARTIAL=31 NOT_COVERED=2 |
| `python3 scripts/check_sdk_compat_manifest_evidence_map.py --self-test` | Exit 0. self-test: pass (71 negative fixtures, injected positive control; memory only) |
| `python3 scripts/check_ci_checker_wiring.py` | Exit 0. ci checker wiring ok: scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=53 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | Exit 0. self-test: pass (13 negative controls) |
| `python3 scripts/check_stage5_host.py --self-test` | Exit 0. self-test: pass |

53/53 passed.

### Contract-only TypeScript 0.x client

| Command | Actual result |
|---|---|
| `python3 scripts/check_sdk_client.py` | Exit 0. sdk client pin ok: commands=84 node=24.22.1 sourceSha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e |
| `python3 scripts/check_sdk_client.py --self-test` | Exit 0. self-test: pass |
| `npm --prefix sdk run conformance` | Exit 0. 7 tests passed, including the order regression. |
| `npm --prefix sdk run verify-compat` | Exit 0. {"ok":true,"manifest_sha256":"eec1750532d319ea06d8ae61bafa77316067088a84a9b70d20a1f6966dfba1e0","profile_kind":"BOOTSTRAP","profile_revision":"bootstrap-2"} |

4/4 passed.

## Deviations and limits

- The owner decision supersedes the original design's diagnostic-only stop and the byte-unchanged acceptance item for exactly `sdk/compat/verify_compat.mjs` and `sdk/conformance/conformance.test.mjs`. It authorizes the verifier move and the new SDK test. The authorization is recorded in-tree at [docs/decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md](../../docs/decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md). The revised map and checker treat §4 ordering as verified on the worktree. The drafting date remains in the validation directory name.
- The map separates decimal number form from integer range, for 51 rows. The unavailable-profile clause remains PARTIAL because the mixed-input test also supplies an expected revision.
- The newer local main has additional single-fault verifier vectors and a roll-up entry that describes the earlier blocked state. Verification here used the supplied branch. The merge preview identifies the two overlapping insertions for supervisor integration.
- Evidence is for bootstrap catalogue-schema binding only. Semantic conformance, N/N−1, production fitness, independent audit and consumer qualification are outside this validation. The unchanged runtime and kernel were checked by blob identity. Rust, localnet, ZK and hosted workflows were outside the executed checks.

## Fix round 1 (2026-11-18)

Round-0 head `4ccecef` (committed by the supervisor); round-1 changes are uncommitted in this worktree. The round-1 independent review returned one blocking finding: the two authorized SDK source edits rest on an owner decision (pt224u) with no in-tree record, so the "SDK sources byte-unchanged" acceptance item appeared unmet. The review accepted the fix itself as technically sound and named the remedy: record the decision in-tree, or revert to diagnostic-only delivery. Two non-blocking findings: the stale base disclosure and the `none` owner convention on COVERED rows.

### Provenance verification before recording

The authorization was verified genuine against supervisor-owned channels before writing any record; nothing was reconstructed from builder-authored artifacts:

| Check | Actual result |
|---|---|
| Read `/workspace/kix-run/logs/plan-plan-sdk-compat-manifest-clause-evidence_build_a0_codex0.prompt.md` lines 260–262 | Section `=== Owner decision (answers the earlier DECISION_REQUIRED; authoritative for this node) ===` carries the verbatim decision: option 1 approved in this node, JunTae delegation 2026-11-18 `[pt224u]`. |
| Read `/workspace/kix-run/state/plan-plan-sdk-compat-manifest-clause-evidence.decision.md` and `.decision_answer.md` | Supervisor state preserves the class C stop (options 1/2/3, recommendation option 1, User decides) and the answer text identical to the prompt section. |
| `grep -c pt224u /workspace/kix-run/AUTOLOOP_RESULT.md` | 24 lines carry the 2026-11-18 `[pt224u]` delegation tag, including this node's FIX row (line 17). Corroboration of the batch tag, not cryptographic verification. |
| Python comparison of the quoted block in the new decision record against prompt lines 261–262 | Exact string equality (`QUOTE MATCH: True`). |
| `git show origin/main:docs/decisions/AI_DELEGATION_CHECK_ORDER_OWNER_DECISION_20261118.md` | The sibling node's same-tag decision record is merged on cached main and establishes the location-record genre. It does not exist at this base, so the new record names it as a source pointer. |

### Remedy applied (docs only)

No code, test, checker, workflow, SDK, contract, manifest, profile or vector change this round; `git diff --exit-code HEAD -- sdk` exits 0.

1. New [docs/decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md](../../docs/decisions/SDK_COMPAT_CHECK_ORDER_OWNER_DECISION_20261118.md): location record with the verbatim decision, delivery channel and line numbers, the stop it answers, the exact authorized scope (the two SDK files, map reclassification, checker guard replacement, repro update, DECISION_REQUIRED.md removal), the checked conditional tuple-pin clause, and non-claims (recorder is the builder; no new decision, no Astra signature, no ledger closure, no merge authorization).
2. `docs/README.md`: this node's existing validation-index entry now links the decision record (single insertion point; no new index section).
3. Map §1: basis note cites the record and states it supersedes the byte-unchanged acceptance item for exactly the two named SDK files. Map §3 cites the record instead of restating the authorization as unsourced fact.
4. Map §1 also clarifies the owner convention (non-blocking finding 3): the Owner column names the gap owner; COVERED rows have no gap and carry `none`; every PARTIAL/NOT_COVERED row carries a named owner. No row or checker rule changed.
5. This record: basis, changed-paths table and deviations now cite the in-tree record.

The delivery is nine paths (the eight round-0 paths plus the decision record). `DECISION_REQUIRED.md` remains absent, as the recorded decision instructs.

### Base delta and merge preview (non-blocking finding 2)

Cached `origin/main` is unchanged at `b2357bc4d3f6de2e7dd0a09f53596f24d0a944f7`; `git rev-list --left-right --count HEAD...origin/main` gives 1/339. Fetch was NOT_RUN per the supervisor no-network rule. The map's coverage claims remain scoped to base `22d05a0c` evidence, as disclosed. Read-only `git merge-file -p` previews (base bytes from `git show 22d05a0`, main bytes from `git show origin/main`): `sdk/compat/verify_compat.mjs` and `sdk/conformance/conformance.test.mjs` merge cleanly (exit 0); `docs/README.md` and `.github/workflows/protocol.yml` each show one insertion conflict (exit 1), the same two overlapping insertions disclosed in round 0, for supervisor integration. All five other delivery paths are new files absent from cached main (no add/add conflict).

### Re-run commands and actual results (fix round 1)

All commands ran in the foreground in Python 3.13.5 and Node 24.22.1. The three workflow shell blocks were extracted from the worktree `protocol.yml` and executed with `bash -ex`.

| Command | Actual result |
|---|---|
| `python3 scripts/check_sdk_compat_manifest_evidence_map.py` | Exit 0. rows=51 COVERED=18 PARTIAL=31 NOT_COVERED=2 |
| `python3 scripts/check_sdk_compat_manifest_evidence_map.py --self-test` | Exit 0. 71 negative fixtures detected, injected positive control; memory only |
| `python3 scripts/check_docs_index.py` / `--self-test` | Exit 0. scanned=268 indexed=233 allowlisted=35 (decision record indexed); self-test pass |
| `python3 scripts/check_status_register.py` / `--self-test` | Exit 0. paths=385 ev_ids=15 original32=32; self-test pass |
| `python3 scripts/check_ci_checker_wiring.py` / `--self-test` | Exit 0. scripts=30 plain=29 self_test=30 self_test_only=1 docs=21 citations=53; self-test pass (13 controls) |
| Full `Stdlib offline document checks` block (53 commands, `bash -ex`) | Exit 0. 53/53 passed |
| Full `Offline reference state machines and OpenAPI pins` block (`bash -ex`) | Exit 0. Reference suites 196/418/148/85/168 tests OK; OpenAPI pin 84 commands (40 core, 44 FSM); integration-gate pin 84 commands, productionEndpoint=false publicHost=false; both self-tests pass |
| Full `Contract-only TypeScript 0.x client` block (`bash -ex`) | Exit 0. 4/4: sdk client pin ok (commands=84, sourceSha256=ed827de1…); self-test pass; conformance 7/7 including the order regression; verify-compat `{"ok":true,…,"profile_revision":"bootstrap-2"}` |
| `python3 -I validation/2026-10-26-plan-sdk-compat-manifest-clause-evidence/repro_c4_check_order.py` | Exit 0. `C4 profile hash first: profile index=0 contract_only index=1 verifier exit=1` |
| `git show origin/main:docs/status/PRODUCER_QUALIFICATION_TUPLE_V1.json` + inline JSON check | 18 artifact entries; no `verify_compat` pin. No tuple update needed |
| `PYTHONPYCACHEPREFIX=/tmp/kix-sdk-fix1-pycache python3 -m py_compile` (checker, repro) | Exit 0 |
| `git hash-object` on both locked kernel files | `69564b166f0c27f9af5d8422f0a466b18d74c20f` and `b607996c83a119c349f1cc90469ac1ba82764e20` — match |
| `git diff --exit-code HEAD -- sdk docs/contracts reference/v0.3-rc1 .aiops docs/tasks runtime docs/status/CURRENT_CAPABILITY_REGISTER.md` (excluding the two authorized SDK files) | Exit 0, empty diff. Protected bytes unchanged |
| `git diff --exit-code HEAD -- sdk` | Exit 0. SDK files byte-identical to round-0 head; this round touched docs only |
| `git diff --check` | Exit 0 |

Exact-head CI: the round-1 head does not exist yet (supervisor commits); no exact-head run ID, status or conclusion is claimed. Per the ledger row, round-0 exact-head CI passed; that evidence does not transfer to the round-1 head (AGENTS.md §6, §10). Merge authorization remains with the User.
