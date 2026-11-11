# Open User decisions — October 26 AI delegation check-order stop addendum

## Basis and provenance

Builder-authored, dated 2026-10-26. Node:
`plan-plan-open-decisions-addendum-20261026-ai`; issue: none;
`depends_on: []`; audit floor A2; `astra_gate: None`; `user_merge: False`.
This is not ASTRA program mode. This loop-proposed node is absent from
`.aiops/program.json` and has no corresponding task document under `docs/tasks/`.
Task input is the supervisor-supplied node specification and read-only design plan.
Source: KIX planner run 1792972994 (`/workspace/kix-run/logs/planner_1792972994`,
as supplied; no planner execution is claimed).

Observed cached `origin/main`, base and starting branch HEAD:
`957f75d75ea4854eba117d66d07663133f0b7b2c` (#297), on
`agent/kix-plan-plan-open-decisions-addendum-20261026-ai`.
Fetch was NOT_RUN under the supervisor's no-network rule; remote freshness
remains unverified. No local base delta was observed.

The source stop is
`/workspace/kix-run/wt/plan-plan-aid-contract-map-partial-closure/DECISION_REQUIRED.md`,
SHA-256 `24338c0753381529f3a9c00936dd8792130d8021cdef4ce0b60b9e8c6dae8e12`.
This external, unmerged branch record was read as attributed task input.
Its outcomes are attributed below, not reproduced by this node. It is a
source pointer, not a repository Markdown link or a merged contract.

The [October 22 ledger](OPEN_USER_DECISIONS_20261022.md),
[October 23 owner-stop supplement](OPEN_USER_DECISIONS_20261023_ADDENDUM.md),
[October 23 closure](OPEN_USER_DECISIONS_20261023_CLOSURE.md) and
[October 25 closure](OPEN_USER_DECISIONS_20261025_CLOSURE.md) are preserved.
The [validation record](../../validation/2026-10-26-plan-open-decisions-addendum-20261026-ai/README.md) contains exact gathering commands,
raw outputs, counts and local verification.

**This document selects no option and changes no node state.**

## New stop — plan-plan-aid-contract-map-partial-closure

- **Item:** A5; class C under AGENTS.md §8, per the source stop.
- **Contract clause:** [AI_DELEGATION_AUTHORITY.md §7](../contracts/AI_DELEGATION_AUTHORITY.md#7-부여와-제안의-단계),
  numbered items 1–3 at basis lines 210–212, verbatim:

> 1. `actor`가 그 부여의 `agent_id`인지.
> 2. 도구 이름이 거부 목록인지, 허용 목록인지.
> 3. 부여가 있는지, 철회됐는지, 그 쌍의 `ACTIVE` 세대인지.

- **Mock site:** [ai_delegation_mock.py](../../reference/ai_delegation/ai_delegation_mock.py)::`AiDelegationMock.call_tool`.
  At the basis, line 281 checks registration; lines 284–286 reject deny/unknown
  tools; line 291 checks grant-agent binding. The order still matches the
  source's diagnosis.
- **Observed vs required (source report):** a registered wrong agent receives
  `TRANSFER_FORBIDDEN`, or `TOOL_NOT_ALLOWED` for `no_such_tool`, against
  contract-required `UNKNOWN_ACTOR`. See the source stop's “Smallest reproduction”
  snippet and its named characterization; neither is rerun here.
- **Decision owner (verbatim, source line wrapping joined):**
  Astra as contract/design authority, with User authorization of any resulting scope/contract change and User merge.
- **Option 1:** Fix the mock in a separately authorized node. See source stop,
  “Options”, item 1, by reference only.
- **Option 2:** Amend the contract in a separately authorized node. See source stop,
  “Options”, item 2, by reference only.
- **Source recommendation:** The stop record recommends option 1; this addendum
  does not endorse it.
- **Unresolved interpretation:** missing-grant binding remains UNDETERMINED.
  The stop says “this evidence does not define it”; it remains with the same
  decision owner. This addendum supplies no semantics.
- **Branch-only artifacts, not on main; excluded from the inventory and counts:**
  `reference/ai_delegation/test_check_order_precedence.py::CheckOrderPrecedenceTests.test_c_repro_actor_binding_after_tool_lists`,
  `validation/2026-10-26-plan-aid-contract-map-partial-closure/README.md`
  and that worktree's `DECISION_REQUIRED.md`. Paths are relative to the external
  source worktree; none is represented as a main artifact.

## Still open — by reference

Owners below copy the October 25 closure table's “Original owner (as recorded)”
cells verbatim. Options remain at the linked sources; no disposition is inferred.

| Item | Original owner (as recorded) | Source |
|---|---|---|
| L1 · `k-stage5-durable-tx` host | User / supervisor (build host) | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) |
| L2 · `rs-4-l2` host | User (spend / environment); Astra (workload) | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) |
| A2 · `plan-plan-gate-fsm-seeded-journey-differentia` loopback host | Supervisor / repository owner controlling the execution host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) |
| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | User / repository owner | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) |

A4 is listed STILL OPEN by the Oct 25 closure; not named in this node's spec;
no disposition inferred. Including this fourth by-reference item is an explicit
design-plan deviation from the three-item specification list, preserving the ledger.

## Per-option artifact inventory

Mechanical selection; membership does not mean an option requires editing that
artifact. All paths and symbols in this inventory exist at
`957f75d75ea4854eba117d66d07663133f0b7b2c`.
G1–G7 and their raw outputs are in the validation record. These are candidates
for owner review, not an exhaustive change specification.

Code set K: `UNKNOWN_ACTOR`, `UNKNOWN_GRANT`, `TOOL_NOT_ALLOWED`,
`TRANSFER_FORBIDDEN`, `REFUND_EXECUTION_FORBIDDEN`, `SIGNING_FORBIDDEN`,
`MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY`. This is the supplied selection set for
§7 checks 1–3 and deny-code evidence; `DENY_CODES` is also matched in test bodies.

### I-T — tests and parameterized cases (8 artifacts)

G1 selects seven call_tool-using files; G2 selects test bodies containing both
`call_tool` and a K code or `DENY_CODES`. Function lines identify definitions.
This lexical rule finds seven functions. They assert current actor/tool
rejections; membership does not prove the disputed simultaneous-fault precedence.
The module-level `CASES` artifact adds one, with six matching case entries.

| Path and symbol | Basis line(s) | Command |
|---|---|---|
| [reference/ai_delegation/test_ai_delegation_mock.py](../../reference/ai_delegation/test_ai_delegation_mock.py)::`AiDelegationMockTests.test_ai_cannot_decide_and_strangers_are_rejected` | 162 | G2 |
| [reference/ai_delegation/test_ai_delegation_mock.py](../../reference/ai_delegation/test_ai_delegation_mock.py)::`AiDelegationMockTests.test_allowlist_is_disjoint_from_protocol_commands` | 240 | G2 |
| [reference/ai_delegation/test_ai_delegation_mock.py](../../reference/ai_delegation/test_ai_delegation_mock.py)::`AiDelegationMockTests.test_denylist_and_unknown_tools` | 222 | G2 |
| [reference/ai_delegation/test_ai_delegation_mock.py](../../reference/ai_delegation/test_ai_delegation_mock.py)::`AiDelegationMockTests.test_tool_level_follows_the_grant` | 483 | G2 |
| [reference/ai_delegation/test_ai_delegation_properties.py](../../reference/ai_delegation/test_ai_delegation_properties.py)::`AuthorityAndInertnessTests.test_ai_actors_never_issue_revoke_or_decide` | 433 | G2 |
| [reference/ai_delegation/test_ai_delegation_properties.py](../../reference/ai_delegation/test_ai_delegation_properties.py)::`AuthorityAndInertnessTests.test_deny_and_unknown_tools` | 400 | G2 |
| [reference/ai_delegation/test_ai_delegation_properties.py](../../reference/ai_delegation/test_ai_delegation_properties.py)::`AuthorityAndInertnessTests.test_tool_level_follows_the_grant` | 449 | G2 |
| [reference/ai_delegation/test_rejection_atomicity.py](../../reference/ai_delegation/test_rejection_atomicity.py)::`CASES` | 57, 62, 64–67 (matching entries) | G2-CASES |

### I-M — contract evidence map (9 rows)

Path: [AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md](AI_DELEGATION_CONTRACT_EVIDENCE_MAP.md).
Select §2 rows §5 and §7, plus §3 error-code rows in K. Existing status cells
remain unchanged.

| Row key | Basis line | Command |
|---|---|---|
| §5 | 49 | G3 |
| §7 | 51 | G3 |
| `UNKNOWN_ACTOR` | 68 | G3 |
| `UNKNOWN_GRANT` | 69 | G3 |
| `TOOL_NOT_ALLOWED` | 71 | G3 |
| `TRANSFER_FORBIDDEN` | 72 | G3 |
| `REFUND_EXECUTION_FORBIDDEN` | 73 | G3 |
| `SIGNING_FORBIDDEN` | 74 | G3 |
| `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY` | 75 | G3 |

### I-C — error-code coverage (7 rows)

Path: [CONTRACT_ERROR_CODE_COVERAGE.md](CONTRACT_ERROR_CODE_COVERAGE.md).
Select AID rows in K.

| AID code | Basis line | Command |
|---|---|---|
| `UNKNOWN_ACTOR` | 222 | G4 |
| `UNKNOWN_GRANT` | 223 | G4 |
| `TOOL_NOT_ALLOWED` | 225 | G4 |
| `TRANSFER_FORBIDDEN` | 226 | G4 |
| `REFUND_EXECUTION_FORBIDDEN` | 227 | G4 |
| `SIGNING_FORBIDDEN` | 228 | G4 |
| `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY` | 229 | G4 |

### I-D — delegation layer matrix (8 mock-test cells)

Path: [AI_DELEGATION_LAYER_MATRIX.md](AI_DELEGATION_LAYER_MATRIX.md).
Select DLG rows whose mock-test cell cites a function selected by G2.
G5 returns eight rows, including the four expected examples DLG-05, DLG-09,
DLG-32 and DLG-36. Other layer columns and evidence grades are not changed.

| Row | Existing mock-test cell | Basis line | Command |
|---|---|---|---|
| DLG-05 | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` `reference/ai_delegation/test_ai_delegation_mock.py::test_flags_remain_false` | 36 | G5 |
| DLG-07 | `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_decide_and_strangers_are_rejected` | 38 | G5 |
| DLG-09 | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` | 40 | G5 |
| DLG-10 | `reference/ai_delegation/test_ai_delegation_mock.py::test_allowlist_is_disjoint_from_protocol_commands` | 41 | G5 |
| DLG-12 | `reference/ai_delegation/test_ai_delegation_mock.py::test_allowlist_is_disjoint_from_protocol_commands` `reference/ai_delegation/test_ai_delegation_mock.py::test_mock_has_no_v03_import` | 43 | G5 |
| DLG-32 | `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_issue_widen_reissue_or_revive` `reference/ai_delegation/test_ai_delegation_mock.py::test_ai_cannot_decide_and_strangers_are_rejected` | 63 | G5 |
| DLG-33 | `reference/ai_delegation/test_ai_delegation_mock.py::test_tool_level_follows_the_grant` | 64 | G5 |
| DLG-36 | `reference/ai_delegation/test_ai_delegation_mock.py::test_denylist_and_unknown_tools` | 67 | G5 |

### I-S1 — option 1 primary sites (5 symbols)

| Path and symbol | Basis line | Command |
|---|---|---|
| [reference/ai_delegation/ai_delegation_mock.py](../../reference/ai_delegation/ai_delegation_mock.py)::`AiDelegationMock.call_tool` | 280 | G6 |
| [reference/ai_delegation/ai_delegation_property_support.py](../../reference/ai_delegation/ai_delegation_property_support.py)::`Model.predict_call_tool` | 518 | G6 |
| [reference/ai_delegation/ai_delegation_property_support.py](../../reference/ai_delegation/ai_delegation_property_support.py)::`Driver.do_deny` | 1220 | G6 |
| [reference/ai_delegation/ai_delegation_property_support.py](../../reference/ai_delegation/ai_delegation_property_support.py)::`Driver.do_unknown_tool` | 1230 | G6 |
| [reference/ai_delegation/ai_delegation_property_support.py](../../reference/ai_delegation/ai_delegation_property_support.py)::`Driver.do_stranger` | 1272 | G6 |

### I-S2 — option 2 primary site (1 clause)

| Path and clause | Basis lines | Command |
|---|---|---|
| [docs/contracts/AI_DELEGATION_AUTHORITY.md](../contracts/AI_DELEGATION_AUTHORITY.md) §7, numbered items 1–3 | 210–212 | G7 |

### Per-option counts

| Option (source stop's item) | Primary sites | I-T | I-M | I-C | I-D |
|---|---|---|---|---|---|
| 1 · fix the mock | I-S1: 5 symbols | 8 artifacts (7 functions + 1 CASES; 6 matching entries) | 9 rows (2 clauses + 7 codes) | 7 rows | 8 cells |
| 2 · amend the contract | I-S2: 1 clause (3 numbered lines) | 8 artifacts (7 functions + 1 CASES; 6 matching entries) | 9 rows (2 clauses + 7 codes) | 7 rows | 8 cells |

The shared categories are exactly the same set under both options. Which
members an option would actually change is for the owner to decide. Counts
measure inventory units, not unique files, required edits, effort or coverage.

## Non-claims

- No option, node disposition, program status, evidence grade, policy value,
  owner, acceptance criterion or protocol command is selected or changed.
  No node is resumed, completed, retired or retried by this document.
- No mock, contract or test is changed; the blocked node is not redone.
  The class C stop remains open with its source owner.
- Earlier ledgers and evidence are preserved. Both locked kernel blobs and
  `reference/v0.3-rc1/**` stay byte-identical. No change under `reference/`,
  `docs/contracts/`, `runtime/`, `.aiops/`, `docs/tasks/` or CI.
- The RS-4 acceptable load level remains UNDETERMINED (User), and all open
  contract/readiness rows retain their owners and unresolved values.
- No hosted CI result transfers from another SHA. This is builder evidence,
  not non-author exact-HEAD review, an Astra audit or a merge-ready claim.
- No real funds, PG/bank/KYC call, public endpoint, Sui testnet/mainnet,
  R2, own replication/consensus/storage engine, coin/TIX module, secrets or
  production runtime is introduced. No production readiness, durability,
  distributed fencing, bank exactly-once, chain finality, legal compliance
  or protocol-completeness claim is made.
