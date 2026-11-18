# AI delegation precedence and inertness validation

`plan-plan-aid-contract-map-partial-closure` is ready for supervisor handoff.
This is builder-authored, source-informed evidence for the offline mock.
The 2026-11-18 owner decision (pt224u) authorizes the option 1 fix under
[AI_DELEGATION_AUTHORITY.md](../../docs/contracts/AI_DELEGATION_AUTHORITY.md) §7.
The earlier blocked draft supplied the validation path and test fixtures.

## Task and source basis

| Item | Evidence |
|---|---|
| Task input | Supervisor node specification, design and owner decision in the session. No issue, matching `docs/tasks/` file or ASTRA envelope. Audit floor A2. |
| Branch | `agent/kix-plan-plan-aid-contract-map-partial-closure` |
| Base, initial and final branch HEAD | `a38e1679449e74186c5a4e3d19b6cb79f6b791d5` |
| Cached `origin/main` | `9f118dc3584edd61ca1076f5f0c2123c1c9428fe` is 353 commits ahead. The contract, mock and evidence map at the two Git refs match. The supplied base was preserved. Remote freshness is unverified. |
| Implementation and final task commit SHAs | Unavailable. Implementation resides in the uncommitted worktree patch. |
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
  citations and remaining gap descriptions. `docs/README.md` links this record
  from the AI delegation contract index entry.
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

## Verification commands and results

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

The owner decision supersedes the design's diagnostic stop and authorizes the
mock change. The seeded harness required an exact expectation update. The
direct catalog check was included. The index link was placed at the existing
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
