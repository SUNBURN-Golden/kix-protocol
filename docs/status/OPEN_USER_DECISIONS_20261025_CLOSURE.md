# Open User decisions — October 25 closure follow-up

## Basis and provenance

Builder-authored, dated 2026-10-25. Node:
`audit15-open-decisions-closure-20261025`; source: KIX audit #15, finding 3,
and the supervisor-supplied node specification and read-only design plan.
Issue: none; `depends_on: []`; audit floor A2; `astra_gate: None`;
`user_merge: False`. This is not ASTRA program mode; there is no node-specific
task document under `docs/tasks/`.

Status basis, starting branch HEAD and cached `origin/main`:
`ff88c441f36cde5b581ba29ce4c46ac47f22b218` (#282). Fetch was NOT_RUN under
the supervisor's no-network rule; remote freshness remains unverified.
The scan range is first-parent merges #274–#280. There is no #273 merge in
this observed history, as also recorded in the [#276 record](../../validation/2026-10-24-plan-register-index-sync/README.md),
lines 46–51. #281 and #282 are later documentation syncs affecting only the
plan, register, crosswalk, index and their own validation records; they settle
none of these items.

The [October 22 ledger](OPEN_USER_DECISIONS_20261022.md),
[October 23 owner-stop supplement](OPEN_USER_DECISIONS_20261023_ADDENDUM.md)
and [October 23 closure](OPEN_USER_DECISIONS_20261023_CLOSURE.md) remain
preserved dated snapshots. Item ids L1–L5 and A1–A4, source rows and owner
strings carry forward from the October 23 closure. Option lists for open
items remain at their original sources, by reference only.

**This document selects no option and changes no node state.**

## Closure table

| Item id | Source row | Original owner (as recorded) | Status at ff88c44 | Resolving merge (PR · SHA) | Merged artefact |
|---|---|---|---|---|---|
| L1 · `k-stage5-durable-tx` host | [Ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User / supervisor (build host) | STILL OPEN | — | Owner and options unchanged; see ledger §1 row 1. |
| L2 · `rs-4-l2` host | [Ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User (spend / environment); Astra (workload) | STILL OPEN | — | Owner and options unchanged; see ledger §1 row 2. |
| L3 · `plan-readiness-conformance-negative-controls` A/B | [Ledger §1 row 3](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User/owner | RESOLVED-BY-MERGE | #266 · `fc28ad4eda7e49f34324d46253dfd950533740db` | [readiness/test_faults.py](../../readiness/test_faults.py), [readiness/CONFORMANCE.md](../../readiness/CONFORMANCE.md#negative-controls-fault-sensitivity) and [readiness/test_conformance_sensitivity.py](../../readiness/test_conformance_sensitivity.py); [October 23 closure details](OPEN_USER_DECISIONS_20261023_CLOSURE.md#closure-table). No validation record exists for #266. |
| L4 · `plan-readiness-receipt-audit-tests` | [Ledger §1 row 4](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | User/repository owner | RESOLVED-BY-MERGE | #268 · `a3f0fea3160fdea2f59fa8658573be173e242074` | [integration_gate/test_http_gate.py](../../integration_gate/test_http_gate.py), [readiness evidence map](READINESS_RUNTIME_EVIDENCE_MAP.md) and [receipt/audit record](../../validation/2026-10-23-readiness-receipt-audit-tests/README.md); [October 23 closure details](OPEN_USER_DECISIONS_20261023_CLOSURE.md#closure-table). |
| L5 · `plan-booking-resale-admission-seeded-property` class C stop | [Ledger §1 row 5](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행) | Astra (design / audit); User (merge) | RESOLVED-BY-MERGE | #267 · `f4df0d8ce0253e7b9755f7eb77e857b2d49057e0` | [reference/booking_resale_admission/test_gate_properties.py](../../reference/booking_resale_admission/test_gate_properties.py) and [seeded-property record](../../validation/2026-10-17-booking-resale-admission-seeded-property/README.md); [October 23 closure details](OPEN_USER_DECISIONS_20261023_CLOSURE.md#closure-table). |
| A1 · `plan-plan-bra-section9-inline-error-code-cove` | [Supplement stop 1](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-bra-section9-inline-error-code-cove) | User or orchestrator owning the node specification | RESOLVED-BY-MERGE | #269 · `c7b470fc39ad6f6aa6ad59c18b5595cde41a7200` | [scripts/check_contract_error_codes.py](../../scripts/check_contract_error_codes.py), [error-code coverage](CONTRACT_ERROR_CODE_COVERAGE.md) and [BRA-RES9 record](../../validation/2026-10-23-bra-section9-error-code-coverage/README.md); [October 23 closure details](OPEN_USER_DECISIONS_20261023_CLOSURE.md#closure-table). |
| A2 · `plan-plan-gate-fsm-seeded-journey-differentia` host | [Supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia) | Supervisor / repository owner controlling the execution host | STILL OPEN | — | Owner and options unchanged; see the linked supplement heading. |
| A3 · `plan-plan-rs-map-gap-closure-batch-2` dependency | [Supplement stop 3](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-rs-map-gap-closure-batch-2) | Supervisor (dependency provisioning / handoff); User (network authorization) | RESOLVED-BY-MERGE | #274 · `a7e6febded343fe0fd43df2059874525194efecf` | [reference/rights_scale/sui/tests/private_path_tests.move](../../reference/rights_scale/sui/tests/private_path_tests.move) and [reference/rights_scale/test_private_model.py](../../reference/rights_scale/test_private_model.py), merged by #274. The [resumed verification record](../../validation/2026-10-23-rs-map-gap-closure-batch-2/README.md#resumed-verification-after-the-owner-decision-2026-10-24), line 174, states: “The owner approved Option 1 and completed toolchain/cache provisioning outside this builder session.” That approval belongs to the record; it is not independently verified here. Its workspace test and Clippy results at lines 191–192 are recorded as exit 0. |
| A4 · `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition | [Supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023) | User / repository owner | STILL OPEN | — | Owner and options unchanged. #276 delivered `plan-plan-register-index-sync-20261024`; its record names no disposition of this node. See the [#276 record](../../validation/2026-10-24-plan-register-index-sync/README.md). |

## Stops recorded in #274–#280

Statements below are attributed to each merged record at this status basis;
line numbers identify its own no-stop or no-class-C statement. They do not
reproduce the underlying runtime verification.

| PR | Merge SHA | Record | Record's statement |
|---|---|---|---|
| #274 | `a7e6febded343fe0fd43df2059874525194efecf` | [RS map gap closure batch 2](../../validation/2026-10-23-rs-map-gap-closure-batch-2/README.md) | Line 24 says the owner resolved the earlier Rust environment blocker outside the session and authorized removal of the decision file; line 174 attributes Option 1 approval and completed provisioning to the owner. Its own stop is resolved. |
| #275 | `7327a00a68ef6efa81a795173af5e4572ccd90ef` | [Reward snapshot isolation](../../validation/2026-10-24-reward-snapshot-isolation/README.md) | Lines 223–224: “No stop-condition resource or owner policy decision is needed” for the test-only node; no decision file created. |
| #276 | `5a09a325e2f6415b7fe638d0dbcd826b4d45fb86` | [Plan/register/index sync](../../validation/2026-10-24-plan-register-index-sync/README.md) | Lines 244–245 say no decision file is needed for the pointer-only scope. |
| #277 | `99f30c2d641646d653b62383b213452fd0a0498b` | [BRA/AID returned-data isolation](../../validation/2026-10-24-bra-aid-returned-data-isolation/README.md) | Lines 85–86 report no explicit class C contract violation; line 207 identifies the import issue as a test import issue, not class C. |
| #278 | `41a799987fe3a6a207abcce75045265c5796e1e4` | [Resale/admission rejection atomicity](../../validation/2026-10-24-resale-admission-rejection-atomicity/README.md) | Lines 472–473 say a root decision file is unnecessary: no listed stop resource, new command or policy value is needed. |
| #279 | `4480c9db7be539abd5a99e640b5a25c7eef8cafe` | [AID rejection atomicity](../../validation/2026-10-25-aid-rejection-atomicity/README.md) | Lines 148–149 report class C: none found; no reproduction/stop file needed. |
| #280 | `d6a6a10f3f5fbaf31f54ad676a9b5e36c0e3d313` | [Restore fingerprint equivalence](../../validation/2026-10-25-restore-fingerprint-equivalence/README.md) | Line 231 says no FSM/contract changes are proposed and no decision file is needed. |

No new stop item is added.

## Recorded uncertainties (not stops)

- The [#278 record](../../validation/2026-10-24-resale-admission-rejection-atomicity/README.md),
  lines 479–482, leaves cross-machine atomicity under clock skew, gate-level/
  internal fault semantics and external source trust to separately scoped
  contract decisions. Its clock-skew observation is class B.
- The [#280 record](../../validation/2026-10-25-restore-fingerprint-equivalence/README.md),
  lines 229–231, leaves reward normalized replay responses contract-undefined;
  any future specification/fix requires a separately authorized task.

These are pointers only; no owner, item or option is created here.

## Still open — by reference

Owners and option lists are unchanged; these links retain their original wording.

- `k-stage5-durable-tx` host — User / supervisor (build host): [ledger §1 row 1](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행).
- `rs-4-l2` host — User (spend / environment), with Astra for any workload change: [ledger §1 row 2](OPEN_USER_DECISIONS_20261022.md#1-원장--열린-항목-하나에-한-행).
- `plan-plan-gate-fsm-seeded-journey-differentia` host — Supervisor / repository owner: [supplement stop 2](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-gate-fsm-seeded-journey-differentia).
- `plan-plan-plan-register-index-sync-20261023` duplicate-sync disposition — User / repository owner: [supplement stop 4](OPEN_USER_DECISIONS_20261023_ADDENDUM.md#plan-plan-plan-register-index-sync-20261023).

## Verification method

RESOLVED-BY-MERGE means that the artefact named by the stop's option or
acceptance exists on main at the status basis. It does not mean the owner
reviewed or accepted the node. Local first-parent history identifies the PRs
and merge SHAs; cited file contents supply the artefact evidence. Owner
permission mentioned by merged records remains attributed to those records;
this document provides no new owner answer or authorization to resume work.

The [validation record](../../validation/2026-10-25-audit15-open-decisions-closure/README.md)
records first-parent SHA checks, artefact/anchor presence, preservation checks
and local document-check results. These establish documentary consistency,
not runtime behavior or independent owner approval.

## Non-claims

- No option, node disposition, program status, evidence grade, policy value,
  owner, acceptance criterion or protocol command is selected or changed.
  No node is resumed, completed, retired or retried by this document.
- The ledger, supplement, previous closure and historical validation records
  are preserved. Both locked kernel blobs and the immutable reference
  snapshot are untouched. Contracts, runtime, CI, task inputs and program
  files are unchanged.
- Audit #15 finding 3 says “#276 superseded the duplicate”; the #276 record
  names `plan-plan-register-index-sync-20261024` and records no disposition of
  `plan-plan-plan-register-index-sync-20261023`. This mismatch is an observation,
  not a correction to the audit or a node disposition. A4 remains STILL OPEN.
- The RS-4 acceptable load level remains `UNDETERMINED` (User), and all nine
  OPEN readiness rows retain their owners and unresolved values.
- Canonical counting remains `DECISION_REQUIRED · Astra`.
- No hosted CI success transfers from any historical SHA. This is builder
  evidence, not non-author exact-HEAD review or a merge-ready claim.
- No production readiness, durability, distributed fencing, bank exactly-once,
  chain finality, legal compliance or protocol-completeness claim is made.
