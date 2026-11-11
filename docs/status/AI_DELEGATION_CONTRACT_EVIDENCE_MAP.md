# AI delegation contract clause-to-test evidence map

**Builder-authored map, not a review or an acceptance; no grade change.**
`delegated_execution_enabled` stays `false`. Enablement remains a User/Astra
decision under `ai-delegation-execution-decision`.

## 0. Basis

Node `plan-ai-delegation-contract-clause-evidence-m`; immutable task input is the
supervisor-provided specification/design, with no issue or matching task file
under `docs/tasks/`. Observed cached `origin/main`, base and initial task HEAD:
`a0db1e226e27b1c5f60ee938fb528ff795907056`, branch
`agent/kix-plan-ai-delegation-contract-clause-evidence-m`.
Fetch was not run because the supervisor forbids network actions. Remote
freshness is unverified; no local base delta was observed.

Source: [AI_DELEGATION_AUTHORITY.md](../contracts/AI_DELEGATION_AUTHORITY.md),
revision **초안 0.1**. Bodies inspected: `test_ai_delegation_mock.py`,
`test_ai_delegation_properties.py`, `test_rejection_atomicity.py`,
`test_contract_error_codes.py`, `test_returned_data_isolation.py`,
`test_restore_fingerprint_equivalence.py` under `reference/ai_delegation/`,
and the cited AI delegation tests in `readiness/conformance.py` and
`readiness/test_faults.py`. This is source-informed evidence.

## 1. Vocabulary

| Status | Rule |
|---|---|
| COVERED | Existing tests sufficiently cover the scoped offline assertions; gap is `none`. |
| PARTIAL | At least one cited test covers part of the section; a specific gap remains. |
| NOT_COVERED | Evidence is `none`; missing scope is named. |
| OPEN | Gap contains UNDETERMINED, DECISION_REQUIRED · Astra or 이 노드 밖, with the contract owner verbatim. |

OPEN citations, if any, describe only the adopted mock posture. Owner `none`
assigns nobody. Other clause owners are verbatim contract owner cells separated
by semicolons. DLG pointers refer to existing rows of
[AI_DELEGATION_LAYER_MATRIX.md](AI_DELEGATION_LAYER_MATRIX.md); they do not copy,
regrade or close those rows. No DLG predicate table is repeated here.

## 2. Clause map

| Clause | Heading | Paraphrase | Evidence | DLG pointer | Status | Open or missing | Owner |
|---|---|---|---|---|---|---|---|
| §0 | 범위와 상태 | Query is read-only, proposals are inert, provenance is mock-only and execution stays off. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_mock_has_no_v03_import`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_query_does_not_change_state_and_propose_is_a_memo`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false` | AI_DELEGATION_LAYER_MATRIX.md: DLG-11, DLG-30 | PARTIAL | Import scan alone does not assert absence of every network/file/PG/bank/KYC/kernel/Move/signing call; enablement is outside this node. | none |
| §1 | 용어 | Humans issue, revoke and decide; agents cannot expand grants or execute approved memos. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_ai_cannot_issue_widen_reissue_or_revive`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_ai_cannot_decide_and_strangers_are_rejected`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_next_generation_requires_revoke`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_decide_rechecks_grant_and_approval_does_not_execute` | AI_DELEGATION_LAYER_MATRIX.md: DLG-32 | COVERED | none | none |
| §2 | `delegate` / `close_delegation`과의 관계 | AI grant records remain separate from ticket delegate/close_delegation commands. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_allowlist_is_disjoint_from_protocol_commands`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_mock_has_no_v03_import` | AI_DELEGATION_LAYER_MATRIX.md: DLG-10, DLG-12 | PARTIAL | Frozen ticket-command observations are not executable citations here; no cross-layer binding is established. | none |
| §3 | 권한 수준 | QUERY and PROPOSE are separate permissions; EXECUTE and execution attempts are refused. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_execute_authority_and_attempt_are_disabled`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_tool_level_follows_the_grant`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_execute_is_never_grantable_and_attempt_is_disabled`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_b_four_entry_authority_list_with_execute`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_tool_level_follows_the_grant` | AI_DELEGATION_LAYER_MATRIX.md: DLG-03, DLG-31, DLG-33 | PARTIAL | Existing Class B characterization accepts INVALID_ID or EXECUTE_AUTHORITY_DISABLED for a four-entry authority list; exact malformed-input precedence is not proved. | none |
| §4 | 부여 기록 | Required fixture bounds and immutable grant bindings apply within each revoked/new generation pair. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_limits_are_required_fixture_bounds`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_grant_idempotency`; `reference/ai_delegation/test_ai_delegation_properties.py::LimitTests.test_limits_and_currency_are_required`; `reference/ai_delegation/test_ai_delegation_properties.py::RevocationTests.test_revoked_grant_id_is_never_revived_and_next_generation_needs_revoke` | AI_DELEGATION_LAYER_MATRIX.md: DLG-14, DLG-23..DLG-25, DLG-34 | PARTIAL | Concurrent grants across issuers and aggregation policy remain UNDETERMINED (§9, U11-L); fixture bounds are not product policy. | Astra (U11-L) |
| §5 | 도구 허용 목록과 거부 목록 | Closed allow/deny lists refuse transfer, refund, signing, self-expansion and unknown tools; grant-change requests are memos. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_denylist_and_unknown_tools`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_allowlist_is_disjoint_from_protocol_commands`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_grant_change_memo_does_not_widen_the_grant`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_deny_and_unknown_tools` | AI_DELEGATION_LAYER_MATRIX.md: DLG-05, DLG-06, DLG-08, DLG-09, DLG-10, DLG-36 | COVERED | none | none |
| §6 | 술어 | All predicate identifiers are traced to test docstrings; layer evidence remains in the matrix. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_every_contract_predicate_is_named_in_a_docstring`; `reference/ai_delegation/test_ai_delegation_properties.py::TraceabilityTests.test_docstrings_cite_the_predicates` | AI_DELEGATION_LAYER_MATRIX.md: DLG-01..DLG-36 | PARTIAL | Per-predicate MOCK_ONLY / NO_LAYER / ANALOGUE_NOT_BOUND gaps remain in the matrix; traceability does not close them. | none |
| §7 | 부여와 제안의 단계 | Caps, periods, revocation/history, idempotency and canonical digest have offline and local restart evidence. | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_caps_count_open_proposals_and_release_on_reject_or_withdraw`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_period_boundaries`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_revocation_is_immediate_and_keeps_history`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_proposal_idempotency`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_digest_is_sha256_of_canonical_json`; `reference/ai_delegation/test_ai_delegation_properties.py::PeriodTests.test_decide_rechecks_the_period`; `reference/ai_delegation/test_ai_delegation_properties.py::IdempotencyTests.test_replay_after_revocation_is_still_a_duplicate`; `reference/ai_delegation/test_ai_delegation_properties.py::ReplayDeterminismTests.test_command_log_replay_reproduces_every_digest`; `reference/ai_delegation/test_ai_delegation_properties.py::ClassBCharacterizationTests.test_b_precedence_among_several_violations_is_set_membership`; `reference/ai_delegation/test_returned_data_isolation.py::ReturnedResultReplayTests.test_corrupted_first_and_duplicate_results_do_not_change_duplicates`; `reference/ai_delegation/test_restore_fingerprint_equivalence.py::AiDelegationRestoreFingerprintClassATests.test_same_grant_binding_replays`; `readiness/conformance.py::BackendConformance.test_ai_delegation_registry_opens_once_and_issue_replays_across_restart`; `readiness/test_faults.py::ExtensionTests.test_ai_delegation_torn_revoke_replays_once_and_execution_stays_off` | AI_DELEGATION_LAYER_MATRIX.md: DLG-15..DLG-28, DLG-35 | PARTIAL | Check order 1–8 is characterized only as set membership for simultaneous violations. Local readiness journal tests do not establish production durability. | none |
| §8 | 오류 코드와 항상 거짓인 플래그 | All §8 codes have scoped rejection or constructor evidence and all eleven flags stay false. | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable`; `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_cases_cover_every_contract_code`; `reference/ai_delegation/test_ai_delegation_properties.py::ContractConstantTests.test_code_tables`; `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos`; `reference/ai_delegation/test_contract_error_codes.py::AiDelegationErrorCodeGapTests.test_unknown_proposal_id_is_unknown_proposal_on_every_path` | AI_DELEGATION_LAYER_MATRIX.md: DLG-29 | COVERED | none | none |
| §9 | UNDETERMINED와 후속 결정 | Eight policy, identity, authority, legal, binding and enablement questions remain open. | none | none | OPEN | UNDETERMINED and 이 노드 밖: retain all contract owners and decisions; no answer supplied. | Astra (U11-L); Astra와 사용자 (U11-ID); Astra; `k1-cut-proof`, RS-3a; 법무 검토 (D-E, 사용자); 후속 노드; `ai-delegation-execution-decision` (사용자 병합) |
| §10 | 비주장 | Non-claims bound the meaning of mock results and do not establish operating assurances. | none | none | NOT_COVERED | Non-claims are not executable predicates: no durability, chain grant, identity, signing, funds, legal effect or production readiness is verified. | none |

Counts: COVERED=3 PARTIAL=6 NOT_COVERED=1 OPEN=1

## 3. §8 error codes

AID points to the existing code row in
[CONTRACT_ERROR_CODE_COVERAGE.md](CONTRACT_ERROR_CODE_COVERAGE.md), without copying its citations.
MOCK_INVARIANT is constructor-only and excluded from that map.

| Code | Evidence | Coverage-map row | Status | Gap |
|---|---|---|---|---|
| `AI_SELF_EXPANSION_FORBIDDEN` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `AI_CANNOT_DECIDE` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `UNKNOWN_ACTOR` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `UNKNOWN_GRANT` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `UNKNOWN_PROPOSAL` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `TOOL_NOT_ALLOWED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `TRANSFER_FORBIDDEN` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `REFUND_EXECUTION_FORBIDDEN` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `SIGNING_FORBIDDEN` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `EXECUTE_AUTHORITY_DISABLED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `DELEGATED_EXECUTION_DISABLED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `GRANT_NOT_CURRENT` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `GRANT_REVOKED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `GRANT_EXPIRED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `SCOPE_VIOLATION` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `LIMIT_REQUIRED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `PER_ACTION_EXCEEDED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `CUMULATIVE_EXCEEDED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `COUNT_EXCEEDED` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `INVALID_ID` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `INVALID_AMOUNT` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `INVALID_PERIOD` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `GRANT_BINDING_CONFLICT` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `PROPOSAL_BINDING_CONFLICT` | `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable` | AID | COVERED | none |
| `MOCK_INVARIANT` | `reference/ai_delegation/test_ai_delegation_properties.py::ContractConstantTests.test_overlapping_registries_give_mock_invariant` | excluded | COVERED | none |

Codes: COVERED=26

## 4. §8 always-false flags

| Flag | Evidence | Status | Gap |
|---|---|---|---|
| `execution_enabled` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `funds_executed` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `issued` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `paid` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `signed` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `transferred` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `refund_executed` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `chain_grant_confirmed` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `revocation_cut_confirmed` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `durable` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |
| `legal_authority` | `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests.test_flags_remain_false`; `reference/ai_delegation/test_ai_delegation_properties.py::AuthorityAndInertnessTests.test_flags_provenance_and_inert_memos` | COVERED | none |

Flags: COVERED=11

## 5. Open items (contract §9)

Contract item, status and owner cells are copied verbatim, in order.

| Item | Contract item | Contract status | Evidence | Status | Open | Owner |
|---|---|---|---|---|---|---|
| O1 | 건별·누적·건수의 제품 한도, 기간의 길이, 집계 창(주문·계정·기간) | UNDETERMINED | none | OPEN | UNDETERMINED: no decision or external answer supplied. | Astra (U11-L) |
| O2 | AI 서비스 identity, I11의 발급자·대체자 외에 누가 인간 주체인지 | UNDETERMINED | none | OPEN | UNDETERMINED: no decision or external answer supplied. | Astra와 사용자 (U11-ID) |
| O3 | 어떤 표면을 부여할 수 있는지, 어떤 제안 종류를 허용하는지 | UNDETERMINED | none | OPEN | UNDETERMINED: no decision or external answer supplied. | Astra |
| O4 | 기간의 권위 있는 시각원, 체인 회수 cut `C_g`/`H_g` | UNDETERMINED | none | OPEN | UNDETERMINED: no decision or external answer supplied. | `k1-cut-proof`, RS-3a |
| O5 | 정지와 재개. 목은 철회와 새 세대만 둔다 | UNDETERMINED | none | OPEN | UNDETERMINED: no decision or external answer supplied. | Astra |
| O6 | AI의 행위가 issuer를 구속하는지, 책임과 법적 성격 | UNDETERMINED | none | OPEN | UNDETERMINED: no decision or external answer supplied. | 법무 검토 (D-E, 사용자) |
| O7 | 와이어 명령, 온체인 grant (RS-3a), Rust 결합 (RS-3b) | 이 노드 밖 | none | OPEN | 이 노드 밖: no decision or external answer supplied. | 후속 노드 |
| O8 | 실행을 켜는 결정 | 이 노드 밖 | none | OPEN | 이 노드 밖: no decision or external answer supplied. delegated_execution_enabled = false; User/Astra enablement decision remains pending. | `ai-delegation-execution-decision` (사용자 병합) |

Open items: OPEN=8

## 6. Limits and follow-up

No policy value, identity, grantable surface, authoritative time source, chain
cut, suspend/resume behavior, legal character, wire command or binding is
selected. All §9 items retain their owners and remain UNDETERMINED or 이 노드 밖.
`delegated_execution_enabled` stays `false`; enablement remains User/Astra's
`ai-delegation-execution-decision`, requiring user merge.

The existing Class B cases characterize malformed authority-list code
precedence, simultaneous-violation precedence, omitted/empty/null binding and
copy ownership. They do not close unspecified semantics. No new explicit
contract violation was established by this mapping exercise.

The checker verifies structure, counts and cited test symbol existence without
importing tests or reading the frozen reference tree. It cannot judge test
adequacy. No independent review, acceptance, grade/register promotion, durability,
distributed fencing, bank exactly-once, chain finality, legal compliance or
production readiness is claimed. Contracts, mocks and existing tests are unchanged.
The local readiness fixture establishes no production durability guarantee.

See the [actual validation record](../../validation/2026-10-26-plan-ai-delegation-contract-clause-evidence-m/README.md).
