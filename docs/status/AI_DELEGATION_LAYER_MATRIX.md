# AI delegation layer matrix — builder-authored map of what each layer holds for DLG-01..DLG-36

**This document is a builder-authored map, not a review, not an acceptance, and not a change of status. It grades no layer as sufficient, and it claims no execution, limit-enforcement or revocation guarantee beyond the cited sources.**
It lists, for each predicate of `docs/contracts/AI_DELEGATION_AUTHORITY.md` §6, the mock test that cites it and what the chain grant, the executor map and the readiness wrap hold that resembles it. It designs no binding, adds no command, flag, limit, name or value, and enables nothing. `delegated_execution_enabled` stays `false`. DX-8 and DX-9 of the delegated-execution decision proposal stay `DECISION_REQUIRED · Astra`; DX-13 stays `UNDETERMINED · 법무`.

## 0. Basis

- Node: `plan-delegation-layer-gap-matrix` (loop-proposed; not in `.aiops/program.json`; no task file under `docs/tasks/`; the node spec is the task input). Depends on `plan-ci-wire-i12-proof-ids-check` (#199).
- Observed `origin/main` and branch HEAD: `624b28d024279bd077e1247f37566333457750bd`. `git fetch origin main` was not run (this session forbids network actions); the value is the local `origin/main` ref, equal to HEAD.
- Locked blobs verified at that base: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`, `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. This node does not touch them.
- Predicates: the 36 rows of the contract §6 table. Mock tests: `reference/ai_delegation/test_ai_delegation_mock.py`, whose test docstrings cite every id.
- Context: `docs/decisions/AI_DELEGATION_EXECUTION_DECISION_PROPOSAL_20261016.md` (#193) §3 findings 1, 2 and 4 and prerequisites DX-8, DX-9, DX-13.
- Checker: `python3 scripts/check_delegation_layer_matrix.py [--self-test]`. It verifies ids, statuses, paths, symbols, mock citations and the gap summary below. It does not verify that an analogue is really equivalent; that is a builder reading.

## 1. Status vocabulary

Citations are written `` `path::symbol` `` (symbols, not line numbers). `none` means the layer holds nothing for the predicate. `absent: ` marks a source that itself records the capability as undefined or stopped. Free text after a citation is a builder note. The wrap column is never a second enforcement: the wrap forwards every call to the mock and is cited only to show what it forwards or journals.

| Status | Meaning |
|---|---|
| `MOCK_ONLY` | Chain and executor cells are `none`. Only the mock tests hold the predicate; the wrap may forward it. |
| `ANALOGUE_NOT_BOUND` | At least one non-`absent:` chain or executor citation resembles the predicate. Nothing links it to the mock. "Analogue" is a builder reading, not equivalence. |
| `NO_LAYER` | At least one `absent:` chain or executor citation, and no non-absent one. A source records the capability as undefined or stopped. |
| `NOT_APPLICABLE_BY_DESIGN` | Chain and executor cells are `none`, and the status cell names the contract section that scopes the predicate to the mock. |

Tie-break: where two statuses seemed possible, the one that claims less was used (`MOCK_ONLY`). Astra may reclassify any row.

## 2. Matrix

| ID | Predicate (paraphrase) | Mock test | Chain analogue | Executor-map analogue | Readiness wrap | Status |
|---|---|---|---|---|---|---|
| DLG-01 | QUERY tools and view_* leave state unchanged. | `reference/ai_delegation/test_ai_delegation_mock.py::test_query_does_not_change_state_and_propose_is_a_memo` | none | none | none | MOCK_ONLY |
| DLG-02 | PROPOSE writes only an inactive proposal memo. | `reference/ai_delegation/test_ai_delegation_mock.py::test_query_does_not_change_state_and_propose_is_a_memo` | none | none | none | MOCK_ONLY |
| DLG-03 | A grant naming EXECUTE is refused with EXECUTE_AUTHORITY_DISABLED. | `reference/ai_delegation/test_ai_delegation_mock.py::test_execute_authority_and_attempt_are_disabled` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
| DLG-04 | attempt_execution always fails with DELEGATED_EXECUTION_DISABLED and changes no state. | `reference/ai_delegation/test_ai_delegation_mock.py::test_execute_authority_and_attempt_are_disabled` | none | absent: `runtime/crates/kix-delegated-exec/README.md` | `readiness/ai_delegation_wrap.py::attempt_execution` forwards to the mock | NO_LAYER |
| DLG-05 | issue and pay tools are refused MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY; issue and pay flags stay false. | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` `reference/ai_delegation/test_ai_delegation_mock.py::test_flags_remain_false` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
| DLG-06 | AI issue, widen, reissue or revive is refused AI_SELF_EXPANSION_FORBIDDEN with state unchanged. | `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_issue_widen_reissue_or_revive` | `reference/rights_scale/sui/tests/delegation_tests.move::only_the_issuer_creates_grants` issuer-only creation (EAuthority) | none | none | ANALOGUE_NOT_BOUND |
| DLG-07 | An AI decide_proposal is refused AI_CANNOT_DECIDE with state unchanged. | `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_decide_and_strangers_are_rejected` | none | none | none | MOCK_ONLY |
| DLG-08 | propose_grant_change leaves only a memo and does not change the grant body. | `reference/ai_delegation/test_ai_delegation_mock.py::test_grant_change_memo_does_not_widen_the_grant` | none | none | none | MOCK_ONLY |
| DLG-09 | Allow and deny lists are disjoint; transfer, refund execution and signing are deny codes. | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
| DLG-10 | The allow list is disjoint from the protocol_contract.json command keys. | `reference/ai_delegation/test_ai_delegation_mock.py::test_allowlist_is_disjoint_from_protocol_commands` | none | none | none | NOT_APPLICABLE_BY_DESIGN: contract §2 keeps the mock off the command catalogue |
| DLG-11 | The mock does not import reference/v0.3-rc1. | `reference/ai_delegation/test_ai_delegation_mock.py::test_mock_has_no_v03_import` | none | none | none | NOT_APPLICABLE_BY_DESIGN: contract §0 scopes the mock to no v0.3 import |
| DLG-12 | delegate and close_delegation are not called, reused or renamed. | `reference/ai_delegation/test_ai_delegation_mock.py::test_allowlist_is_disjoint_from_protocol_commands` `reference/ai_delegation/test_ai_delegation_mock.py::test_mock_has_no_v03_import` | none | none | none | NOT_APPLICABLE_BY_DESIGN: contract §2 separates the two delegation axes |
| DLG-13 | Scope checks membership only and does not interpret identifiers. | `reference/ai_delegation/test_ai_delegation_mock.py::test_scope_checks_membership_only` | `reference/rights_scale/sui/sources/rights_scale.move::check_grant` grant and page binding, not a scope set | none | none | ANALOGUE_NOT_BOUND |
| DLG-14 | Three limits and currency are required; no default and no unlimited. | `reference/ai_delegation/test_ai_delegation_mock.py::test_limits_are_required_fixture_bounds` | none | none | none | MOCK_ONLY |
| DLG-15 | Cumulative amount and count include PROPOSED and HUMAN_APPROVED. | `reference/ai_delegation/test_ai_delegation_mock.py::test_caps_count_open_proposals_and_release_on_reject_or_withdraw` `reference/ai_delegation/test_ai_delegation_mock.py::test_per_action_boundary` | none | none | none | MOCK_ONLY |
| DLG-16 | HUMAN_REJECTED and WITHDRAWN return their share of the limits. | `reference/ai_delegation/test_ai_delegation_mock.py::test_caps_count_open_proposals_and_release_on_reject_or_withdraw` | none | none | none | MOCK_ONLY |
| DLG-17 | Splitting a request cannot exceed the cumulative or count limit. | `reference/ai_delegation/test_ai_delegation_mock.py::test_caps_count_open_proposals_and_release_on_reject_or_withdraw` | none | none | none | MOCK_ONLY |
| DLG-18 | bool, zero and out-of-range amounts are INVALID_AMOUNT. | `reference/ai_delegation/test_ai_delegation_mock.py::test_caps_count_open_proposals_and_release_on_reject_or_withdraw` `reference/ai_delegation/test_ai_delegation_mock.py::test_per_action_boundary` | none | none | none | MOCK_ONLY |
| DLG-19 | The period is inclusive at both ends: GRANT_NOT_CURRENT before, GRANT_EXPIRED after. | `reference/ai_delegation/test_ai_delegation_mock.py::test_period_boundaries` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
| DLG-20 | Revocation blocks tool use of that generation as soon as it is recorded. | `reference/ai_delegation/test_ai_delegation_mock.py::test_revocation_is_immediate_and_keeps_history` | `reference/rights_scale/sui/sources/rights_scale.move::revoke_grant` `reference/rights_scale/sui/tests/delegation_tests.move::the_cut_blocks_delegated_issue` | `runtime/crates/kix-delegated-exec/src/lib.rs::revoke_grant` `runtime/crates/kix-delegated-exec/tests/delegation_fence.rs::the_cut_refuses_new_commitments_but_replays_stored_results` | `readiness/ai_delegation_wrap.py::revoke_grant` forwards to the mock | ANALOGUE_NOT_BOUND |
| DLG-21 | Revocation sets PROPOSED proposals to VOIDED_BY_REVOCATION without deleting them. | `reference/ai_delegation/test_ai_delegation_mock.py::test_revocation_is_immediate_and_keeps_history` | none | none | none | MOCK_ONLY |
| DLG-22 | History is not deleted; revoked generations and proposals stay queryable. | `reference/ai_delegation/test_ai_delegation_mock.py::test_revocation_is_immediate_and_keeps_history` | `reference/rights_scale/sui/sources/rights_scale.move::GrantRevoked` durable cut record | `runtime/crates/kix-delegated-exec/tests/delegation_fence.rs::the_cut_refuses_new_commitments_but_replays_stored_results` stored results still replay | `readiness/ai_delegation_wrap.py::export_journal` journals digest-changing calls | ANALOGUE_NOT_BOUND |
| DLG-23 | A revoked generation is not revived under the same grant_id. | `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_issue_widen_reissue_or_revive` | `reference/rights_scale/sui/tests/delegation_tests.move::a_grant_is_cut_once` `reference/rights_scale/sui/sources/rights_scale.move::check_grant` | `runtime/crates/kix-delegated-exec/src/lib.rs::revoke_grant` a second cut is GrantClosed | none | ANALOGUE_NOT_BOUND |
| DLG-24 | A next generation is issued only when the pair previous generation is REVOKED. | `reference/ai_delegation/test_ai_delegation_mock.py::test_next_generation_requires_revoke` | none | none | none | MOCK_ONLY: chain GrantControl generation (starts 1, bumps at the cut) and executor GrantExists are different conditions |
| DLG-25 | The same grant_id with the same binding is duplicate true; a different binding is GRANT_BINDING_CONFLICT. | `reference/ai_delegation/test_ai_delegation_mock.py::test_grant_idempotency` | none | none | `readiness/ai_delegation_wrap.py::_call` skips journaling when the digest is unchanged | MOCK_ONLY: executor GrantExists is a different condition |
| DLG-26 | The same proposal_id with the same binding is duplicate true; a different binding is PROPOSAL_BINDING_CONFLICT. | `reference/ai_delegation/test_ai_delegation_mock.py::test_proposal_idempotency` | none | `runtime/crates/kix-delegated-exec/tests/delegation_fence.rs::identical_retries_replay_the_stored_first_result` `runtime/crates/kix-delegated-exec/tests/delegation_fence.rs::same_request_identity_with_a_different_payload_conflicts` command identity, not proposal identity | `readiness/ai_delegation_wrap.py::_call` skips journaling when the digest is unchanged | ANALOGUE_NOT_BOUND |
| DLG-27 | decide_proposal rechecks currency, revocation, period and limits at decision time. | `reference/ai_delegation/test_ai_delegation_mock.py::test_decide_rechecks_grant_and_approval_does_not_execute` | none | none | none | MOCK_ONLY |
| DLG-28 | Approval is a memo; effects_executed stays false. | `reference/ai_delegation/test_ai_delegation_mock.py::test_decide_rechecks_grant_and_approval_does_not_execute` | none | none | none | MOCK_ONLY |
| DLG-29 | The section 8 flags are always false. | `reference/ai_delegation/test_ai_delegation_mock.py::test_flags_remain_false` | none | none | none | MOCK_ONLY |
| DLG-30 | Views carry provenance and lifecycle_authority. | `reference/ai_delegation/test_ai_delegation_mock.py::test_query_does_not_change_state_and_propose_is_a_memo` | none | none | `readiness/ai_delegation_wrap.py::view_grant` forwards to the mock | NOT_APPLICABLE_BY_DESIGN: contract §0 labels every mock view |
| DLG-31 | No constructor argument enables execution. | `reference/ai_delegation/test_ai_delegation_mock.py::test_execute_authority_and_attempt_are_disabled` | none | absent: `runtime/crates/kix-delegated-exec/README.md` | `readiness/ai_delegation_wrap.py::open_registry` takes only humans and agents | NO_LAYER |
| DLG-32 | issue_grant, revoke_grant and decide_proposal are callable only by human principals. | `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_issue_widen_reissue_or_revive` `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_decide_and_strangers_are_rejected` | `reference/rights_scale/sui/tests/delegation_tests.move::only_the_issuer_creates_grants` `reference/rights_scale/sui/tests/delegation_tests.move::only_the_grant_issuer_cuts_it` issuer address check | absent: `runtime/crates/kix-delegated-exec/README.md` | none | ANALOGUE_NOT_BOUND |
| DLG-33 | Query tools need QUERY and propose tools need PROPOSE on the grant. | `reference/ai_delegation/test_ai_delegation_mock.py::test_tool_level_follows_the_grant` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |
| DLG-34 | currency is KRW; the integer bound 1..10**12 is a fixture range, not a product limit. | `reference/ai_delegation/test_ai_delegation_mock.py::test_limits_are_required_fixture_bounds` | none | none | none | NOT_APPLICABLE_BY_DESIGN: contract §4 calls the range an input bound, not a product limit |
| DLG-35 | state_digest is the sha256 hex of canonical JSON and is not a signature. | `reference/ai_delegation/test_ai_delegation_mock.py::test_digest_is_sha256_of_canonical_json` | none | none | `readiness/ai_delegation_wrap.py::state_digest` forwards to the mock | NOT_APPLICABLE_BY_DESIGN: contract §10 says the digest is process-memory sha256 |
| DLG-36 | A tool in neither list is TOOL_NOT_ALLOWED. | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` | absent: `reference/rights_scale/sui/sources/rights_scale.move::create_grant` | absent: `runtime/crates/kix-delegated-exec/README.md` | none | NO_LAYER |

## 3. Gap summary

A cell counts as "no analogue" when it is `none` or holds only `absent:` citations. Nothing below closes a gap.

- No chain analogue: DLG-01, DLG-02, DLG-03, DLG-04, DLG-05, DLG-07, DLG-08, DLG-09, DLG-10, DLG-11, DLG-12, DLG-14, DLG-15, DLG-16, DLG-17, DLG-18, DLG-19, DLG-21, DLG-24, DLG-25, DLG-26, DLG-27, DLG-28, DLG-29, DLG-30, DLG-31, DLG-33, DLG-34, DLG-35, DLG-36
- No executor analogue: DLG-01, DLG-02, DLG-03, DLG-04, DLG-05, DLG-06, DLG-07, DLG-08, DLG-09, DLG-10, DLG-11, DLG-12, DLG-13, DLG-14, DLG-15, DLG-16, DLG-17, DLG-18, DLG-19, DLG-21, DLG-24, DLG-25, DLG-27, DLG-28, DLG-29, DLG-30, DLG-31, DLG-32, DLG-33, DLG-34, DLG-35, DLG-36
- Neither: DLG-01, DLG-02, DLG-03, DLG-04, DLG-05, DLG-07, DLG-08, DLG-09, DLG-10, DLG-11, DLG-12, DLG-14, DLG-15, DLG-16, DLG-17, DLG-18, DLG-19, DLG-21, DLG-24, DLG-25, DLG-27, DLG-28, DLG-29, DLG-30, DLG-31, DLG-33, DLG-34, DLG-35, DLG-36

Owners are recorded, not assigned here. Every row is open; not closed here.

| Group | Ids | Owner |
|---|---|---|
| Limits and windows | DLG-14 to DLG-18 | `DECISION_REQUIRED · Astra` (DX-8); open; not closed here |
| Period and time source | DLG-19 | `DECISION_REQUIRED · Astra`; open; not closed here |
| Tool gating and execute level | DLG-03, DLG-05, DLG-09, DLG-33, DLG-36 | `DECISION_REQUIRED · Astra`, and a new command only if Astra says so; open; not closed here |
| Mock-to-chain revocation link | DLG-20 to DLG-24 | `DECISION_REQUIRED · Astra` (DX-8); open; not closed here |
| Principals | DLG-06, DLG-07, DLG-32 | `DECISION_REQUIRED · Astra` (DX-9); open; not closed here |
| Legal character of approval and effects | DLG-28, DLG-29 | `UNDETERMINED · 법무` (DX-13); open; not closed here |

## 4. Cross-check against proposal §3 findings 1, 2 and 4

Run from the repository root on the base above. Output recorded in the validation record.

| Finding | Method | Result |
|---|---|---|
| 1. Limits do not reach the chain | `grep -rlE "per_action_max\|cumulative_max\|count_max\|not_after\|not_before"` over `runtime`, `reference/rights_scale`, `readiness`, `reference/ai_delegation` | Agrees. No hit under `runtime/` or `reference/rights_scale/`. Hits are `reference/ai_delegation/` (mock and its test) and `readiness/test_faults.py` (fixture values only). `readiness/ai_delegation_wrap.py` has none. Matches the matrix: DLG-14 to DLG-18 are `MOCK_ONLY`, DLG-19 is `NO_LAYER`. |
| 2. No link between mock revocation and the chain cut | `grep -rlI ai_delegation` over `*.rs`, `*.move`, `*.toml`, `*.mjs`; `grep -rlE "GrantControl\|rights_scale"` over `reference/ai_delegation` and `readiness`; the mock's `chain_grant_confirmed` and `revocation_cut_confirmed` flags | Agrees. No `.rs`, `.move`, `.toml` or `.mjs` file names `ai_delegation`. Neither `reference/ai_delegation/` nor `readiness/` names `GrantControl` or `rights_scale`. The mock lists both flags among its always-false flags. |
| 4. The executor map does not authenticate anyone | Read of the crate README (`:23`) and the `lib.rs` module doc | Agrees. The README "Chain reads" bullet and the `lib.rs` module doc both say nothing authenticates principals, delegates, issuers or grants. Matches the matrix: the executor cell of DLG-32 is `absent:`. |

Nuance, not a disagreement on a finding. The proposal's capability table says the mock's DLG-20 to DLG-24 guarantee holds "nowhere on the chain or in the executor". The matrix marks DLG-20, DLG-22 and DLG-23 `ANALOGUE_NOT_BOUND` because the chain `revoke_grant` cut and the map's cut resemble the immediate-block, history-kept and no-revival conditions for their own objects. They are not the mock's guarantee: DLG-21 and DLG-24 have no analogue, and nothing binds the mock grant to a `GrantControl`. The two readings agree on the point finding 2 makes (no link). The proposal was not edited.

## 5. Non-claims

- This is a builder-authored map. It is not a review, not an acceptance, and not an Astra audit.
- It grades no layer as sufficient. A status says what a cited source holds, not that it is enough.
- It claims no execution, limit enforcement or revocation guarantee beyond the cited sources, and no equivalence between a mock predicate and a chain or executor behavior.
- It designs no binding between the mock, the chain grant, the executor map and the wrap, and creates no node for DX-8 or DX-9.
- It adds no command, flag, limit, name or value, and changes no contract, mock, runtime, Move source or architecture flag.
- Status calls are builder readings and may be reclassified by Astra.
