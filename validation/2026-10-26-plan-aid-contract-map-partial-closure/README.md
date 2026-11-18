# AI delegation precedence and inertness validation

`plan-plan-aid-contract-map-partial-closure` is ready for supervisor handoff
after fix round 1. This is builder-authored, source-informed evidence for the
offline mock. The 2026-11-18 owner decision (JunTae delegation `[pt224u]`,
delivered by the KIX supervisor) authorizes the option 1 fix under
[AI_DELEGATION_AUTHORITY.md](../../docs/contracts/AI_DELEGATION_AUTHORITY.md) §7.
The decision text, provenance and scope are preserved verbatim in the
[owner decision location record](../../docs/decisions/AI_DELEGATION_CHECK_ORDER_OWNER_DECISION_20261118.md),
written in fix round 1 as the remedy named by the round-1 independent review.
The earlier blocked draft supplied the validation path and test fixtures.

## Task and source basis

| Item | Evidence |
|---|---|
| Task input | Supervisor node specification, design and owner decision in the session. No issue, matching `docs/tasks/` file or ASTRA envelope. Audit floor A2. |
| Branch | `agent/kix-plan-plan-aid-contract-map-partial-closure` |
| Base and initial branch HEAD | `a38e1679449e74186c5a4e3d19b6cb79f6b791d5` |
| Round-0 implementation head | `d524eefc2d758163d60e7de495bcada17c136fc2` (supervisor-committed; reviewed in r1) |
| Cached `origin/main` | `9f118dc3584edd61ca1076f5f0c2123c1c9428fe` is 353 commits ahead (`git rev-list --left-right --count HEAD...origin/main` → `1 353`, rechecked in fix round 1). The contract, mock, seeded oracle and evidence map are unchanged on cached main relative to the base; only this branch edits them. The supplied base was preserved. Remote freshness is unverified. |
| Fix-round-1 and final task commit SHAs | Unavailable at writing. Fix-round-1 changes reside in the uncommitted worktree patch; the supervisor commits and owns the final head. |
| Exact-head KTX and KIX protocol CI | NOT_RUN / NOT_QUERIED. Run IDs, status and conclusion unavailable. |
| Merge and main/push CI | N/A. Publication and merge are supervisor-owned. |

## Changed files

- `reference/ai_delegation/ai_delegation_mock.py` checks existing grant binding
  before either tool list. Missing grants reach the original `UNKNOWN_GRANT`
  check after the tool lists and the existing `now` and `args` checks.
- `reference/ai_delegation/ai_delegation_property_support.py` and
  `reference/ai_delegation/test_ai_delegation_properties.py` update the seeded
  expectation for exact codes from requests that target another agent's grant.
- `reference/ai_delegation/test_check_order_precedence.py` adds the pair matrix,
  actor-binding regression, missing-grant controls and decision precedence.
- `reference/ai_delegation/test_mock_static_inertness.py` adds a closed AST
  scan with in-memory controls and direct checks of both command catalogs.
- `docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md` updates the §0 and §7
  citations and remaining gap descriptions; the §0 Basis update note cites the
  owner decision location record (fix round 1). `docs/README.md` links this
  record and the decision record from the AI delegation contract index entry.
- `docs/decisions/AI_DELEGATION_CHECK_ORDER_OWNER_DECISION_20261118.md` (fix
  round 1) preserves the supervisor-delivered owner decision verbatim with its
  provenance, scope and non-claims, following the location-record genre of
  `OPENAPI_CATALOGUE_PROMOTION_OWNER_DECISION_20261009.md` and
  `POLICY_DEEPENING_OWNER_DECISION_20261009.md`. It creates no new decision.
- `validation/2026-10-26-plan-aid-contract-map-partial-closure/README.md` is this record.

## Existing coverage and new evidence

| Requirement | Previous coverage | Added evidence |
|---|---|---|
| §7 proposal precedence | Partial. Existing individual boundary tests and `ClassBCharacterizationTests.test_b_precedence_among_several_violations_is_set_membership` do not assert the ordered result for each pair. | Exact-code matrix, with valid and isolated controls. Named checks for `agent-2` on `g-1` with `transfer` and `no_such_tool`, plus tool-list precedence for a missing grant. |
| §7 decision precedence | Partial. `AiDelegationMockTests.test_decide_rechecks_grant_and_approval_does_not_execute`, `PeriodTests.test_decide_rechecks_the_period` and `RevocationTests.test_revocation_is_immediate_voids_and_keeps_history` cover an approved duplicate after expiry, period rejection for a pending proposal, and in-window rejection for a voided proposal. | Duplicate approval and rejection after revocation both before and after the period. Voided proposals return `GRANT_REVOKED` before either period error. |
| §0 offline inertness | Partial. `AiDelegationMockTests.test_mock_has_no_v03_import`, `test_query_does_not_change_state_and_propose_is_a_memo`, `test_flags_remain_false` and `test_allowlist_is_disjoint_from_protocol_commands` cover the frozen-reference boundary, memo behavior and the frozen command allowlist. | AST test checks direct imports and references to I/O, process and signing APIs with negative controls. A separate test checks mock tools and method names against `protocol_contract.json` and the contract-only OpenAPI catalog. |
| §3 malformed authority order | Existing class B characterization in `AuthorityAndInertnessTests.test_b_four_entry_authority_list_with_execute`. | Existing characterization retained. |

The matrix enumerates **28 check pairs and 169 variant cells**. All 28 pairs
have strict cases. Of the 169 cells, **148** distinguish and assert the lower
check's contract code, **1** shares a code, and **20** lack an exactly-two
public fixture. The matrix evaluates applicable predicates before calling
the mock and verifies canonical state and digest on rejection. For an invalid
tool, later predicates refer to the otherwise unchanged `propose_action` payload.

**Class C resolved.** On the original mock, `agent-2` on `g-1` received
`TRANSFER_FORBIDDEN` for `transfer` and `TOOL_NOT_ALLOWED` for `no_such_tool`.
Both now return `UNKNOWN_ACTOR` with unchanged state. All nine wrong-agent
and invalid-tool variants are strict conformance cells. The pre-fix run
failed those nine cells and the two named subtests. The contract text remains
the expectation. No new class C discrepancy surfaced in these checks.

**Class B and remaining gaps.** Missing grants have no binding or downstream
predicates, though separate tests pin tool-list rejection before `UNKNOWN_GRANT`.
An unknown tool and missing PROPOSE level both return `TOOL_NOT_ALLOWED`.
A denied tool distinguishes that pair. A QUERY-only grant cannot acquire
count usage. A non-revoked generation is ACTIVE under the tested invariant.
Approved shares survive revocation and make the revoked-plus-count case
constructible. Decision-time currency and limit failures cannot be induced
through the public API. The §3 four-entry malformed-list case remains class B.

The [clause map](../../docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md) keeps
§0 and §7 `PARTIAL`. §0 now checks both catalogs and direct source references.
Dynamic effects are outside the AST scan. §7's unavailable variants and
re-checks are described above. Counts are `COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1`.
Cached main's evidence roll-up mirrors this counts line. The §9 inputs remain
owned and open. The record covers neither runtime sandboxing nor production
behavior such as durability, distributed fencing, bank exactly-once, chain
finality, legal authority or deployment readiness.

## Fix round 1 (2026-11-18)

The r1 independent review (supervisor-commissioned, read-only) returned one
blocking finding: the mock fix, seeded-oracle alignment and exact-code
expectation update exceed the node's "test-only / no mock change" acceptance
item, and the sole justification — the 2026-11-18 owner decision `[pt224u]` —
was recorded nowhere under `docs/decisions/` as AGENTS.md §5 requires. The
review accepted the fix itself as "correct, minimal, and contract-conformant"
and named the remedy: "record it under `docs/decisions/` (or have the owner
confirm it in-repo)". No other blocking finding was raised; exact-head CI for
the round-0 head passed (supervisor ledger: PR #470, `CI PASS`).

**Provenance check before applying the remedy.** The decision is genuine and
was granted outside the executing session:

- The supervisor-generated round-0 builder prompt
  `/workspace/kix-run/logs/plan-plan-aid-contract-map-partial-closure_build_a0_codex0.prompt.md`
  carries the section `=== Owner decision (answers the earlier
  DECISION_REQUIRED; authoritative for this node) ===` at lines 182–186;
  `grep -n "pt224u"` hits line 183. Lines 183–184 are quoted verbatim in the
  decision record. That file is supervisor-owned; builder sessions cannot
  write it.
- The supervisor loop ledger `/workspace/kix-run/AUTOLOOP_RESULT.md` uses the
  same `KIX 2026-11-18, JunTae delegation [pt224u]` tag on 24 lines for that
  day's batch of node dispositions, corroborating the tag as a supervisor
  batch identifier.
- The class C stop the decision answers is recorded on cached `origin/main`
  as item A5 of `docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md`
  (`git show origin/main:…`; merged as `be97eaa`, absent at this branch's
  base). It names the source stop's SHA-256, options 1/2, the option-1
  recommendation and the owner cell; its I-S1 option-1 inventory lists
  `Model.predict_call_tool`, covering the seeded-oracle alignment.

**Remedy applied (docs only).** Added
`docs/decisions/AI_DELEGATION_CHECK_ORDER_OWNER_DECISION_20261118.md`
(location record: verbatim decision, channel, scope, non-claims; no new
decision, no grade or ledger change), linked it from the existing AI
delegation contract index line in `docs/README.md`, cited it in the evidence
map's §0 Basis update note, and updated this record. No mock, oracle, test,
contract, flag, checker or CI change in this round
(`git diff --exit-code HEAD -- reference/ai_delegation` passed). The
index link sits on the line this PR already touches; `git merge-file --stdout`
against cached main merged cleanly (exit 0, no conflict markers, link
preserved). `DECISION_REQUIRED.md` is not recreated: the recorded owner
decision expressly instructs its removal and `STATUS: READY`, so the node's
STOP path is superseded for this fix by the now-recorded authorization.

**Fix-round-1 commands and actual results.** Python `3.13.5` (`python3`) and
`3.12.15` (`python3.12`); `PYTHONDONTWRITEBYTECODE=1` throughout.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | 98 tests, OK. |
| `python3 -m unittest discover … -p test_check_order_precedence.py` / `-p test_mock_static_inertness.py` | 9 tests OK / 4 tests OK. |
| Full `Stdlib offline document checks` `run:` block extracted from `.github/workflows/protocol.yml` and run with `bash -ex` | Exit 0. Includes `check_ai_delegation_evidence_map.py` (105 citations; COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1) and `--self-test` (86 negative controls), `check_contract_error_codes.py` (199 rows, CLASS_B=0 CLASS_C=0) and `--self-test`, `check_docs_index.py` (scanned=247 indexed=212 allowlisted=35; the new decision record is scanned and indexed) and `--self-test`, `check_status_register.py` (385 paths, 15 EV IDs, 32 original IDs) and `--self-test`, and every other checker in the block with its self-test. |
| `python3.12 -m unittest discover` for settlement_f01_f03, booking_resale_admission, credit_advance_f04, ai_delegation, token_reward | 196 / 412 / 148 / 98 / 168 tests, all OK. |
| `python3.12 -m unittest integration_gate.test_http_gate readiness.test_faults` | 100 tests, OK; the suite emitted an unclosed-file `ResourceWarning` (as in round 0). |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test`; `check_integration_gate_openapi.py` and `--self-test` | All passed. 84 commands (40 core, 44 FSM); `productionEndpoint=false`, `publicHost=false`. |
| `PYTHONPATH=reference/ai_delegation python3` enumerating `cells()` and `category({vi,vj})` | 28 pairs, 169 cells; 148 contract, 20 unbuildable, 1 same_code — equal to the module constants. |
| Cached-main overlay: `git archive origin/main` into a fresh directory, branch files overlaid, merged `docs/README.md` from `git merge-file`; then `python3.12 -m unittest discover -s …/reference/ai_delegation` | 182 tests, OK (main's extended suite). |
| Overlay: `python3.12` on main's `check_ai_delegation_evidence_map.py` (+`--self-test`, 86 controls), `check_evidence_map_rollup.py`, `check_docs_index.py` (+`--self-test`), `check_class_b_index.py`, `check_ci_test_discovery.py`, `check_status_register.py`, `check_contract_error_codes.py` | All passed. Roll-up 25 contracts; docs index scanned=435 indexed=400 allowlisted=35; class B index 218 rows; CI discovery 9 reference suites, both new modules discovered; register 577 paths; error codes 199 rows with main's own CLASS_B=1 row (pre-existing on main, untouched here). |
| `git merge-file --stdout` for `docs/README.md` (ours, base `a38e167`, cached main) | Exit 0, no conflict markers, decision-record link present in the merged preview. |
| Link check: every relative Markdown target in the new decision record resolved against the worktree | All 6 targets exist. |
| `git hash-object` on both locked files; `git diff --exit-code HEAD -- reference/v0.3-rc1 docs/contracts runtime .aiops docs/tasks .github scripts reference/ai_delegation`; `git diff --check`; Python Git-blob comparison of all `reference/v0.3-rc1` files | Locked blobs `69564b16…` / `b607996c…` match; protected paths and all round-0 code unchanged this round; no whitespace errors; 108 frozen files byte-identical. |
| `git rev-list --left-right --count HEAD...origin/main`; `git rev-parse origin/main` | `1 353`; `9f118dc3584edd61ca1076f5f0c2123c1c9428fe`. Fetch NOT_RUN (supervisor no-network rule); remote freshness unverified. |

Fix-round-1 changed paths: `docs/decisions/AI_DELEGATION_CHECK_ORDER_OWNER_DECISION_20261118.md`
(new), `docs/README.md`, `docs/status/AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md`,
`validation/2026-10-26-plan-aid-contract-map-partial-closure/README.md`.
Exact-head CI for the commit carrying these changes is supervisor-owned and
NOT_RUN at writing; per AGENTS.md §11 it belongs in the PR closure, not in a
further commit.

## Verification commands and results (round 0)

Python `3.13.5` supplies `python3`. `python3.12` is `3.12.15`, matching the
protocol workflow's 3.12 series. Python verification set `PYTHONDONTWRITEBYTECODE=1`.
For the stdlib block, a Python heredoc extracted the named `run: |` block
from `.github/workflows/protocol.yml` and ran its commands with `bash -ex -c`.
Entries that include a `--self-test` variant ran both commands independently.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation -p test_check_order_precedence.py` | Before fix, exit 1 with 11 failing subtests. Final run, 9 methods passed. |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation -p test_mock_static_inertness.py` | 4 methods passed. |
| `PYTHONPATH=reference/ai_delegation python3 -` enumerating `cells()` and `category()` | 28 pairs, 169 cells. Counts 148 contract, 20 unbuildable, 1 same code. |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | 98 passed after seeded oracle correction. |
| `python3 scripts/check_status_register.py` and `--self-test` | Passed. 385 paths, 15 EV IDs, 32 original IDs. |
| `python3 scripts/check_rs_profile_traceability.py` and `--self-test` | Both passed. |
| `python3 scripts/check_read_model_source_map.py` and `--self-test` | Both passed. |
| `python3 scripts/check_docs_index.py` and `--self-test` | Passed. 246 scanned, 211 indexed, 35 allowlisted. |
| `python3 scripts/check_i12_proof_ids.py` and `--self-test` | Both passed. |
| `python3 scripts/check_delegation_layer_matrix.py` and `--self-test` | Both passed. |
| `python3 scripts/check_rs_predicate_evidence_map.py` and `--self-test` | Both passed. |
| `python3 scripts/check_rs_im_evidence_map.py` and `--self-test` | Both passed. |
| `python3 scripts/check_tl_predicate_evidence_map.py` and `--self-test` | Both passed. |
| `python3 scripts/check_contract_error_codes.py` and `--self-test` | Passed. 199 rows with raised, asserted and covered codes. |
| `python3 scripts/check_adapter_identity_map.py` and `--self-test` | Both passed. |
| `python3 scripts/check_v5_transition_evidence_map.py` and `--self-test` | Both passed. |
| `python3 scripts/check_readiness_evidence_map.py` and `--self-test` | Both passed. |
| `python3 scripts/check_settlement_evidence_map.py` and `--self-test` | Passed, including 33 negative controls. |
| `python3 scripts/check_bra_evidence_map.py` and `--self-test` | Passed, including 50 negative controls. |
| `python3 scripts/check_credit_evidence_map.py` and `--self-test` | Passed, including 55 negative controls. |
| `python3 scripts/check_primary_price_fee_evidence_map.py` and `--self-test` | Passed, including 72 negative controls. |
| `python3 scripts/check_ai_delegation_evidence_map.py` and `--self-test` | Passed with 105 citations and counts 3 COVERED, 6 PARTIAL, 1 NOT_COVERED, 1 OPEN. Self-test passed 86 negative controls. |
| `python3 scripts/check_stage5_host.py --self-test` | Passed. |
| `python3.12 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | 196 passed. |
| `python3.12 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | 412 passed. |
| `python3.12 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | 148 passed. |
| `python3.12 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | After mock fix and before oracle correction, exit 1 with 18 failed methods. Final run, 98 passed. |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | 168 passed. |
| `python3.12 -m unittest integration_gate.test_http_gate readiness.test_faults` | 100 passed and embedded self-test passed. The suite emitted an unclosed-file `ResourceWarning`. |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test` | Passed. 84 commands, 40 core and 44 FSM. |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | Passed. 84 commands, `productionEndpoint=false`, `publicHost=false`. |
| `git archive refs/remotes/origin/main` with a temporary overlay, then `python3.12 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | 182 tests passed on cached main with the patch overlaid. |
| `python3.12 scripts/check_ai_delegation_evidence_map.py`, `python3.12 scripts/check_evidence_map_rollup.py`, `python3.12 scripts/check_docs_index.py`, `python3.12 scripts/check_class_b_index.py` and `python3.12 scripts/check_ci_test_discovery.py` on the cached-main overlay | All passed. 25 contracts in the roll-up and 434 docs-index entries scanned. Both new test modules are discovered. |
| `git merge-file --stdout` for `docs/README.md`, using HEAD and cached main files | Original adjacent index placement conflicted. The link at the existing contract entry produced a clean preview containing both the node's link and the cached main entry. |
| `git rev-parse HEAD refs/remotes/origin/main` and `git rev-list --left-right --count HEAD...refs/remotes/origin/main` | SHAs above. `0 353`. |
| `git diff --exit-code HEAD -- reference/v0.3-rc1 docs/contracts runtime .aiops docs/tasks .github scripts` and `git diff --check` | Passed. No tracked changes in the listed paths and no whitespace errors. |
| `git rev-parse HEAD:runtime/crates/kix-kernel/src/lib.rs HEAD:runtime/crates/kix-kernel/tests/quarantine_capacity.rs HEAD:reference/v0.3-rc1` and `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Required blobs match before and after. Frozen tree `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `git ls-tree -rz HEAD -- reference/v0.3-rc1` and Python Git blob hash comparison against working files | All 108 frozen files matched byte-for-byte. `DECISION_REQUIRED.md` was already absent at resume and is absent at delivery. |

## Preservation and deviations

| Locked file | Verified before and after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The [owner decision](../../docs/decisions/AI_DELEGATION_CHECK_ORDER_OWNER_DECISION_20261118.md),
recorded in fix round 1, supersedes the design's diagnostic stop and authorizes
the mock change. The seeded harness required an exact expectation update. The
direct catalog check was included. The index links were placed at the existing
AI contract entry to avoid the cached-main conflict. `delegated_execution_enabled`
is `false`. Fixture limits and periods are synthetic.

Fetch, commit, push, review, merge and GitHub actions were outside this session.
Rust crate/workspace, Clippy, formatting, TypeScript SDK, Move/localnet and ZK
jobs were outside the touched paths. The local run covers the branch's stdlib
block, five offline state-machine suites, local HTTP/readiness and OpenAPI.
The cached-main checks cover the delegation suite and applicable document
and discovery checks. A branch stdlib rerun during overlay extraction failed on
duplicate source filenames in the temporary snapshot. After snapshot cleanup,
the branch block was rerun in isolation.
Exact-head hosted CI and non-author review remain outside this evidence.
