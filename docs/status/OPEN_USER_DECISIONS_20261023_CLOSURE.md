# Open User decisions — October 23 closure addendum

## Basis and provenance

Builder-authored, dated 2026-10-23. Node:
`audit14-audit14-open-decisions-closure-addendum`; source: KIX audit #14 and
the supervisor-supplied node specification and read-only design plan. Issue:
none; dependencies: none; audit floor A2; `astra_gate: None`, `user_merge: False`.
This is not ASTRA program mode; no node-specific task file exists.

Status basis: `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` (#269), confirmed
in local first-parent merge history. Observed starting HEAD and cached
`origin/main`: `2d2e93eb14fe41bafaf2dbaa91f02d861c8be8b5` (#270).
Fetch was NOT_RUN under the supervisor's no-network rule; remote freshness is
unverified. #270 changed only the plan, capability register, docs index and
its validation record; none of the resolving artefacts below changed after
the status basis. #270 is a separate audit14 node and does not dispose of
`plan-plan-plan-register-index-sync-20261023`, which remains STILL OPEN.

The [October 22 ledger](OPEN_USER_DECISIONS_20261022.md) and
[October 23 owner-stop supplement](OPEN_USER_DECISIONS_20261023_ADDENDUM.md)
remain dated snapshots, with their bodies unchanged. L1–L5 below correspond
to ledger §1 rows 1–5; A1–A4 correspond to the supplement's four Owner stops,
in order. Owners are short forms of the original recorded owners. Option
lists for open items remain at those sources, by reference only.

**This document selects no option and changes no node state.**

## Closure table

| Item id | Source row | Original owner (as recorded) | Status at c7b470f | Resolving merge (PR · SHA) | Merged artefact |
|---|---|---|---|---|---|
| L1 · `k-stage5-durable-tx` host | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User / supervisor (build host) | STILL OPEN | — | Owner and options unchanged; see ledger §1 row 1. |
| L2 · `rs-4-l2` host | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User (spend / environment); Astra (workload) | STILL OPEN | — | Owner and options unchanged; see ledger §1 row 2. |
| L3 · `plan-readiness-conformance-negative-controls` A/B | [Ledger §1 row 3](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User/owner | RESOLVED-BY-MERGE | #266 · `fc28ad4eda7e49f34324d46253dfd950533740db` | [readiness/test_faults.py](../../readiness/test_faults.py) line 38 imports `ConformanceSensitivityTests` from `readiness.test_conformance_sensitivity`; [readiness/CONFORMANCE.md §Negative controls (fault sensitivity)](../../readiness/CONFORMANCE.md#negative-controls-fault-sensitivity) describes the unchanged CI entry point executing the controls. No validation record exists for #266. |
| L4 · `plan-readiness-receipt-audit-tests` | [Ledger §1 row 4](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User/repository owner | RESOLVED-BY-MERGE | #268 · `a3f0fea3160fdea2f59fa8658573be173e242074` | Four `TransportTests` methods in [integration_gate/test_http_gate.py](../../integration_gate/test_http_gate.py), named below; [READINESS_RUNTIME_EVIDENCE_MAP.md](READINESS_RUNTIME_EVIDENCE_MAP.md) now reports `Counts: EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9` (ledger: 25/2/0/9). [Receipt/audit record](../../validation/2026-10-23-readiness-receipt-audit-tests/README.md) attributes resumption and the checker path to its owner decision. |
| L5 · `plan-booking-resale-admission-seeded-property` class C stop | [Ledger §1 row 5](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | Astra (design / audit); User (merge) | RESOLVED-BY-MERGE | #267 · `f4df0d8ce0253e7b9755f7eb77e857b2d49057e0` | [reference/booking_resale_admission/test_gate_properties.py](../../reference/booking_resale_admission/test_gate_properties.py) is merged without `expectedFailure` decorators. The [seeded-property record](../../validation/2026-10-17-booking-resale-admission-seeded-property/README.md), directory date retained and resumed October 23, attributes the characterization to its owner decision; its old-base finding is not a current-defect claim. |
| A1 · `plan-plan-bra-section9-inline-error-code-cove` | [Supplement stop 1](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-bra-section9-inline-error-code-cove) | User or orchestrator owning the node specification | RESOLVED-BY-MERGE | #269 · `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` | [scripts/check_contract_error_codes.py](../../scripts/check_contract_error_codes.py) contains `TABLES['BRA-RES9']`; [CONTRACT_ERROR_CODE_COVERAGE.md](CONTRACT_ERROR_CODE_COVERAGE.md) has ten COVERED BRA-RES9 rows and explicitly excludes six pass-throughs. The [BRA-RES9 record](../../validation/2026-10-23-bra-section9-error-code-coverage/README.md) says “The owner approved Option (c)”; that is the record's attribution, not a decision here. |
| A2 · `plan-plan-gate-fsm-seeded-journey-differentia` host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) | Supervisor / repository owner controlling the execution host | STILL OPEN | — | Owner and options unchanged; see the linked supplement heading. |
| A3 · `plan-plan-rs-map-gap-closure-batch-2` dependency | [Supplement stop 3](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-rs-map-gap-closure-batch-2) | Supervisor (dependency provisioning / handoff); User (network authorization) | STILL OPEN | — | Owner and options unchanged; see the linked supplement heading. |
| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) | User / repository owner | STILL OPEN | — | Owner and options unchanged; see the linked supplement heading. |

The four #268 methods in `TransportTests` are:

- `test_core_receipt_replay_preserves_receipt_and_journal`
- `test_checksum_valid_receipt_mismatch_refuses_startup`
- `test_readiness_disabled_call_audits_inactive`
- `test_append_failure_diverges_and_blocks_subsequent_commands`

The exact #266 import is
`from readiness.test_conformance_sensitivity import ConformanceSensitivityTests`.
Its test module, [readiness/test_conformance_sensitivity.py](../../readiness/test_conformance_sensitivity.py),
is present at the basis. The absence of a #266 validation record is also
recorded in [DEVELOPMENT_PLAN.md §5](../DEVELOPMENT_PLAN.md#5-전체-단계);
this closure note does not create retrospective execution evidence for it.

## Still open — by reference

Owners and option lists are unchanged; these links retain their original wording.

- `k-stage5-durable-tx` host — User / supervisor (build host): [ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행).
- `rs-4-l2` host — User (spend / environment), with Astra for any workload change: [ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행).
- `plan-plan-gate-fsm-seeded-journey-differentia` host — Supervisor / repository owner: [supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia).
- `plan-plan-rs-map-gap-closure-batch-2` dependency — Supervisor; User for any network authorization: [supplement stop 3](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-rs-map-gap-closure-batch-2).
- `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition — User / repository owner: [supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023).

## Verification method

RESOLVED-BY-MERGE means that the artefact named by the stop's option or
acceptance exists on main at the status basis. It does not mean the owner
reviewed or accepted the node. Local first-parent history identifies the PRs
and merge SHAs; cited file contents supply the artefact evidence. Owner
permission mentioned by merged records remains attributed to those records;
this document provides no new owner answer or authorization to resume work.

The [validation record](../../validation/2026-10-23-audit14-open-decisions-closure/README.md)
records path checks, preservation checks and local document-check results.
Those checks establish citation presence and consistency, not runtime behavior.

## Non-claims

- No option, node disposition, program status, evidence grade, policy value,
  owner, acceptance criterion or protocol command is selected or changed.
  No node is resumed, completed, retired or retried by this document.
- The ledger, supplement and historical validation records are preserved.
  Both locked kernel blobs and the immutable reference snapshot are untouched.
  Contracts, runtime, CI, task inputs and program files are unchanged.
- The RS-4 acceptable load level remains `UNDETERMINED` (User), and all nine
  OPEN readiness rows retain their owners and unresolved values.
- No hosted CI success transfers from any historical SHA. This is builder
  evidence, not non-author exact-HEAD review or a merge-ready claim.
- No production readiness, durability, distributed fencing, bank exactly-once,
  chain finality, legal compliance or protocol-completeness claim is made.
