# Restore fingerprint equivalence — builder evidence

Date: 2026-10-25. Node: `plan-plan-restore-fingerprint-equivalence`.
Builder-authored, source-informed, deterministic offline MOCK evidence. This is
not independent A2 review, acceptance, a capability grade increase or merge readiness.

## Task and baseline

The task input is the supervisor-supplied node specification and read-only design
plan in the executing prompt, sourced from planner run `1792804497`
(`/workspace/kix-run/logs/planner_1792804497`). No task issue or node document
under `docs/tasks/` exists; none was created or edited. This is not ASTRA program
mode and this node is not in `.aiops/program.json`. Dependencies: none.

Branch: `agent/kix-plan-plan-restore-fingerprint-equivalence`.
Initial HEAD, implementation base, and locally observed `origin/main` all equal
`4480c9db7be539abd5a99e640b5a25c7eef8cafe`; no local base delta.
`git fetch origin main`: NOT RUN because the supervisor prohibits network/GitHub
actions. Remote freshness is unverified. No rebase or merge occurred.
Implementation/final committed task head: not created; changes remain uncommitted
on the initial HEAD as instructed. Merge SHA and post-merge verification: N/A.
Exact-head KTX and KIX CI run ID/status/conclusion: unavailable / NOT RUN for both.
The supervisor owns commits/publication. Non-author exact-HEAD review and both
completed/success workflow gates remain required before any merge-ready claim.

Python: `3.13.5` locally; workflow requests `3.12`. All Python commands below set
`PYTHONDONTWRITEBYTECODE=1`. No production runtime or external provider is used.
The existing HTTP tests use temporary loopback services only.

## Existing coverage mapped before additions

Paths below are relative to `reference/` unless stated otherwise.

| Requirement | Existing coverage | Mapping / gap |
|---|---|---|
| Settlement replay and restore | `settlement_f01_f03/test_settlement_properties.py::MachinePropertyTests.test_e_every_journal_prefix_restores_to_itself`; `test_settlement_fsm.py::SettlementFsmTests.test_reconcile_matches_restore_and_does_not_enter_the_economic_journal` | Partially covered: digest/prefix reconstruction present; omitted currency/reasons versus explicit defaults across restore absent. |
| Credit restore | `credit_advance_f04/test_credit_properties.py::MachinePropertyTests.test_restore_reproduces_the_digest_at_every_prefix` | Partially covered: restored prefixes present; omitted/None product retry comparison absent. |
| Reservation restore | `booking_resale_admission/test_reservation_fsm.py::ReservationFsmTests.test_restore_replays_a_lost_success_and_omits_rejections` | Partially covered: lost issuance response present; confirm quote omission/default/control absent. |
| Resale restore | `booking_resale_admission/test_resale_fsm.py::ResaleFsmTests.test_restore_replays_one_transfer_and_omits_rejections` | Partially covered: transferred state and replay present; optional adopt/list/payment fields absent. |
| Admission restore | `booking_resale_admission/test_admission_fsm.py::AdmissionFsmTests.test_restart_replays_journal_and_retry_is_duplicate` | Partially covered: bound source recovery/retry present; unbound adopt and external-dependency defaults absent. |
| AI wrap restart | `ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests`; `readiness/CONFORMANCE.md`, registry/issue replay across restart case | Partially covered: full-state rejection/recovery and ordinary issue replay present; scope/requested-scope/subject variant matrices absent. |
| Reward restore | `token_reward/test_reward_fsm.py::RewardFsmTests.test_restore_replays_the_same_digest`; `token_reward/test_snapshot_isolation.py::RewardReplayIsolationTests.test_restore_replays_complete_first_envelopes` | Partially covered: digest and complete replay envelopes present; latter supplies explicit prior_record=None, leaving omitted prior_record untested. |
| Reward payout bounds | `token_reward/test_tl4_fsm_properties.py::RewardFsmPropertyTests.test_TL4_TK07_replay_idempotency_and_supersede_bound_payouts` | Ordinary TK-7 coverage sufficient; new matrix adds only the omission/explicit retry gap. |
| Rejected keys lost on restore | Existing rejection-atomicity modules and settlement §9.3 / credit §7.3 | Sufficient; deliberately excluded, not a newly discovered discrepancy. |

No new module imports another `test_*.py` module. Fixture imports use the existing
non-test support modules. Every probe accepts a first command, records live
retry outcomes, restores the exported journal afresh for each retry, checks
canonical state/digest equality, then checks restored retry outcomes. State and
entire journal equality are checked after every retry (stronger than unchanged
length). Reward also checks the pool view and payout count after every retry.
AI arguments make a plain JSON round trip through the public readiness wrap.
No source, mock, wrapper or contract is changed.

## Field inventory and observed classification

`D` = `("ok", True, None)` (duplicate); `I` =
`("error", "IDEMPOTENCY_CONFLICT")`. `O` = omitted; `N` = explicit None
(JSON null). Every omitted/default pair is submitted both ways round. Other
first values are tested where stated. This is the complete optional/default
command-field inventory examined; required-field sorting is out of scope.

| Suite | Command.field | Variants / observed live → restored | Contract clause and class |
|---|---|---|---|
| Settlement | `initiate.currency` | O / KRW, both directions: D → D | `SETTLEMENT_DISTRIBUTION_F01_F03.md` §§9.3–9.4: A |
| Settlement | `commit.adjustment_reason` | adjustment=0; O / N: D → D | same §§9.3–9.4: A |
| Settlement | `observe_statement.adjustment_reason` | adjustment=0; O / N: D → D | same §§9.3–9.4: A |
| Credit | `offer.product` | O / N: D → D; product absent in exported body | `CREDIT_ADVANCE_F04.md` §§7.3–7.4: A |
| Reservation | `confirm.quote_ref` | O / N: D → D; quote-1 control gives I → I against either; quote-1-first retries itself D → D, O/N I → I | `BOOKING_RESALE_ADMISSION_GATES.md` §9.4: live normalization/replay and restored-state equality A; retry after restore undefined B |
| Resale | `adopt_issued.reservation_id` | unbound, no ticket source; O / N: D → D | same §10.7: live/state A; restored retry undefined B |
| Resale | `adopt_issued.quote_ref` | unbound; O / N: D → D | same §10.7: live/state A; restored retry undefined B |
| Resale | `list_resale.reservation_id` | unbound; O / N: D → D | same §10.7: live/state A; restored retry undefined B |
| Resale | `observe_resale_payment.buyer_role` | LISTED path; O / N: D → D | same §10.7: live/state A; restored retry undefined B |
| Admission | `adopt_issued.reservation_id` | unbound; O / N: D → D | same §11.5: live/state A; restored retry undefined B |
| Admission | `adopt_issued.quote_ref` | unbound; O / N: D → D | same §11.5: live/state A; restored retry undefined B |
| Admission | `authorize_admission.external_dependency` | O / N: D → D | same §11.5: live/state A; restored retry undefined B |
| Admission | `consume.external_dependency` | O / N: D → D | same §11.5: live/state A; restored retry undefined B |
| Reward | `submit.approval_ref.prior_record` | O / N / approval-0; response matrix below | normalized replay response undefined: B; TK-7 payout bounds A |
| Reward | `supersede.approval_ref.prior_record` | O / N / approval-0; same matrix | normalized replay response undefined: B; TK-7 payout bounds A |
| Reward | `mark_eligible.abuse_kind` | O / N: D → D | replay response undefined: B; TK-7 A |
| Reward | `mark_eligible.recipient_cap` | O / N: D → D | replay response undefined: B; TK-7 A |
| Reward | `mark_eligible.program_cap` | O / N: D → D | replay response undefined: B; TK-7 A |
| Reward | `submit.budget_ceiling` | O / N: D → D (approval prior_record explicitly N) | replay response undefined: B; TK-7 A |
| Reward | `submit.execution_permit` | O / N: D → D (approval prior_record explicitly N) | replay response undefined: B; TK-7 A |
| AI | `issue_grant.scope.subjects` | O / [] / [x1] first; retries O / [] / [x1] / null. Same binding D → D; differing non-null variant GRANT_BINDING_CONFLICT → same; null INVALID_ID → same | `AI_DELEGATION_AUTHORITY.md` §4, DLG-25, §7 + `READINESS_RUNTIME.md` file-journal restart: same-binding replay A. O/[]/[x1] equivalence and null parse precedence undefined B |
| AI | `call_tool(propose_grant_change).args.requested.scope.subjects` | O / [] / [x1] first; retries O / [] / [x1] / null. Same binding D → D; differing non-null PROPOSAL_BINDING_CONFLICT → same; null INVALID_ID → same | AI §5, DLG-26, §7 + readiness restart: same binding A; explicit variant/parse distinctions undefined B |
| AI | `call_tool(propose_action).args.subject` | O / x1 first; retries O / x1 / null. Same binding D → D; changed subject PROPOSAL_BINDING_CONFLICT → same; null INVALID_ID → same | AI DLG-26 + readiness restart: same binding A; O/explicit/null distinctions undefined B |
| AI | `call_tool(query_subject).args.subject` | O / x1, g-open and g-list: success `(ok, False, None)` → same; match.subject None / x1 respectively; query never appends | AI §5 optional subject, DLG-01, §7 step 6 + readiness read-only journal: A |

BRA clauses explicitly promise restored canonical state/digest equality but do
not explicitly promise the post-restore retry envelope. Following the plan's
caveat, those retry assertions are B, distinct from their A live predicates.
AI schema says subjects may be omitted but names no explicit equivalent value.
`[]` is not asserted equivalent to omission. Null is rejected before an existing
binding lookup, also for nested requested scope. AI fixtures register H/H2 and
A/A2, use g-open without subject restriction and g-list restricted to x1;
all limits and periods are synthetic (now=15, period=10..20).

### Reward response matrix (class B)

This matrix is observed for both submit and supersede. Each row is an accepted
first approval; each cell is live → restored for the same key and retry body.

| First prior_record | Retry O | Retry N | Retry approval-0 |
|---|---|---|---|
| O | D → I | I → D | I → I |
| N | I → I | D → D | I → I |
| approval-0 | I → I | I → I | D → D |

The raw fingerprint preserves the omission; the exported approval body fills
prior_record=None, and restore fingerprints that body. The explicit string
control stays distinct. No reward contract clause was found defining the
normalized retry response (reviewed `TOKEN_ROLE_AND_SUPPLY.md` TK-7,
`TOKEN_AUTHORITY_AND_LIFECYCLE.md` approval structure and the optional-token
blueprint TK-7). The source comment saying idempotency follows settlement is
not treated as a contract. This is B, not a source fix or a new semantic rule.

Class A is limited to TK-7 (`TOKEN_ROLE_AND_SUPPLY.md` TK-7 and
`docs/status/TL_PREDICATE_EVIDENCE_MAP.md`, TK-7 row): each fixture completes
one first payout before retries, with payout_effect_count=1, exactly one pool
spend of 4 synthetic points, and PROTOCOL_REVENUE balance 500−4. These stay
fixed on live and restored retries, including historical mark_eligible/submit
replay and supersede. No successor payout is submitted in this probe.
No class C contract violation was found.

## Files changed

- `reference/settlement_f01_f03/test_restore_fingerprint_equivalence.py`
- `reference/credit_advance_f04/test_restore_fingerprint_equivalence.py`
- `reference/booking_resale_admission/test_restore_fingerprint_equivalence.py`
- `reference/ai_delegation/test_restore_fingerprint_equivalence.py`
- `reference/token_reward/test_restore_fingerprint_equivalence.py`
- `validation/2026-10-25-restore-fingerprint-equivalence/README.md`
- `docs/README.md` (one evidence-index bullet)

## Commands and actual results

All verification commands below exited 0 unless explicitly marked otherwise.
The first narrow loop failure and correction are recorded separately below.
Narrow command template (each actual suite invocation is tabulated):
`python3 -m unittest discover -s reference/<suite> -t reference/<suite> -p test_restore_fingerprint_equivalence.py -v`.
Full command template: `python3 -m unittest discover -s reference/<suite> -t reference/<suite>`.
Both were executed as foreground fail-fast shell loops with the listed suite names;
no long job was launched in the background.

| Actual command / suite substitution | Result |
|---|---|
| `python3 --version` | Python 3.13.5 |
| `git status --short` (initial) | Clean |
| `git rev-parse origin/main HEAD` | Both 4480c9db7be539abd5a99e640b5a25c7eef8cafe |
| `git branch --show-current` | agent/kix-plan-plan-restore-fingerprint-equivalence |
| Narrow template: `settlement_f01_f03` | 3 passed (initial and complete rerun) |
| Narrow template: `credit_advance_f04` | 1 passed (initial and complete rerun) |
| Narrow template: `booking_resale_admission` | 7 passed (initial and complete rerun) |
| Narrow template: `ai_delegation` | Initial exit 1: 5 passed, 1 incorrect query expectation; corrected test only; complete rerun 6 passed |
| Narrow template: `token_reward` | Initial loop did not reach suite; complete rerun 4 passed |
| Full template: `settlement_f01_f03` | 187 passed |
| Full template: `booking_resale_admission` | 402 passed |
| Full template: `credit_advance_f04` | 147 passed |
| Full template: `ai_delegation` | 83 passed |
| Full template: `token_reward` | 167 passed |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 100 passed; self-test pass; full output captured in temporary `/tmp/restore-fingerprint-http-tests.log` |

The following exact script paths were each executed as `python3 <path>` and
`python3 <path> --self-test`, in the protocol workflow order. Both invocations
exited 0 for every row. The document checker command list was read directly from
`.github/workflows/protocol.yml` (check_status_register through check_readiness_evidence_map).

| Script path (plain and --self-test commands) | Result |
|---|---|
| `scripts/check_status_register.py` | PASS / PASS |
| `scripts/check_rs_profile_traceability.py` | PASS / PASS |
| `scripts/check_read_model_source_map.py` | PASS / PASS |
| `scripts/check_docs_index.py` | PASS / PASS; scanned=226, indexed=191, allowlisted=35 |
| `scripts/check_i12_proof_ids.py` | PASS / PASS |
| `scripts/check_delegation_layer_matrix.py` | PASS / PASS |
| `scripts/check_rs_predicate_evidence_map.py` | PASS / PASS |
| `scripts/check_rs_im_evidence_map.py` | PASS / PASS |
| `scripts/check_tl_predicate_evidence_map.py` | PASS / PASS |
| `scripts/check_contract_error_codes.py` | PASS / PASS; existing map remains rows=199, COVERED=199, CLASS_B=0, CLASS_C=0 (map unchanged; these are error-code coverage statuses, not this node's characterizations) |
| `scripts/check_adapter_identity_map.py` | PASS / PASS |
| `scripts/check_v5_transition_evidence_map.py` | PASS / PASS |
| `scripts/check_readiness_evidence_map.py` | PASS / PASS |
| `scripts/check_openapi_contract.py` | PASS / PASS; commands=84, core=40, fsm=44 |
| `scripts/check_integration_gate_openapi.py` | PASS / PASS; commands=84, productionEndpoint=false, publicHost=false |

| Other actual command / check | Result |
|---|---|
| `python3 scripts/check_stage5_host.py --self-test` | PASS, exit 0; simulated host cases only; no host qualification or database runtime attempted |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: required blobs match (values below) |
| `git rev-parse HEAD:reference/v0.3-rc1` | Before and after: a6ecb124dc2b2267ca6be19e39fbe2aef143074b |
| Inline `python3` check using NUL-delimited `git ls-tree -rz HEAD -- reference/v0.3-rc1`, `git cat-file blob <blob>`, and worktree byte reads | All 108 tracked blobs byte-identical to HEAD; no untracked non-ignored paths under reference/v0.3-rc1 |
| `git diff --check` | PASS |
| `git status --porcelain=v1 --untracked-files=all` | Exactly the seven listed paths |

Required locked blobs, verified before and after:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

KTX kernel workflow local jobs (runtime architecture scripts, Rust kernel tests,
Clippy, formatting and dependency-tree inspection): NOT RUN; only Python test
modules and evidence/index documentation change. No Rust/kernel/workflow input
changed. Move/ZK/TypeScript and production/database workflows: NOT RUN; outside
touched paths. Hosted exact-head KTX/KIX CI and post-merge main CI: NOT RUN / no
run IDs, because no commit/publication/merge is authorized in this builder session.
The local results above are not a substitute claim for exact-head hosted CI.

## Deviations, limits and uncertainty

- Fetch omitted under the explicit supervisor network prohibition; local ref only.
- BRA section references verified as §§9.4 / 10.7 / 11.5. Restored retries are B
  under the plan's explicit contract-wording caveat; no contract is amended.
- Expanded controls to include explicit-first quote-1 and approval-0, empty-list
  AI scope first, and both g-open/g-list query paths. No new commands/semantics.
- First narrow run: settlement 3, credit 1 and BRA 7 passed; AI 5 passed/1 failed
  because the test incorrectly expected missing query subject on g-list to be
  SCOPE_VIOLATION. §5 explicitly makes subject optional; corrected only that
  test expectation. Reward was not reached by that fail-fast loop. The complete
  narrow rerun passed all five modules (3 / 1 / 7 / 6 / 4 methods).
- Local Python 3.13.5 differs from CI 3.12. Exact-head CI and independent A2 review
  remain outstanding and belong to the supervisor workflow, not this evidence.
- Owner policy values remain UNDETERMINED; all numbers/identifiers are fixtures.
  No hardware, paid service, secrets, Sui network, production runtime, storage
  engine, new protocol command or product policy decision is required.
- Required-field normalizations/sorting, rejected-key recovery, durable storage,
  distributed fencing, bank exactly-once, chain finality, live funds, production
  readiness and clean-room independence are not claimed or tested here.
- Reward normalized replay responses remain contract-undefined; any future
  specification/fix requires a separately authorized task. No FSM or contract
  changes are proposed in this node. DECISION_REQUIRED.md is not needed.
