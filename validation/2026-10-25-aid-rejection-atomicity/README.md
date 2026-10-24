# AI delegation full-state rejection atomicity

Node: `plan-plan-aid-rejection-atomicity`. Builder: Codex, 2026-10-25.
Builder-authored, source-informed local evidence, not an independent PASS,
architecture audit, capability promotion or merge-readiness claim.

## Acceptance interpretation (G0)

The supplied supervisor task and design authorize the existing
`readiness/ai_delegation_wrap.py::AiDelegationWrap` as the journal/restore
surface. Its docstring names it a public restore target for readiness journals.
`export_journal()` returns its actual journal; `restore(journal)` reconstructs
the registry and replays recorded calls through the same public methods.
Views, canonical state and digest are forwarded to the unchanged mock.
`_call` journals only after the mock returns successfully and its digest changes;
a rejected mock call therefore must leave the journal unchanged. No harness-owned
command log or substitute replay is used, and no mock/wrap API is added.

The 2026-10-17 property record correctly describes the mock alone as having no
journal/restore. The existing readiness surface, with conformance evidence in
`validation/2026-10-20-ai-delegation-wrap-conformance/README.md`, supplies those
assertions here. PROGRAM_DECISIONS_20260928 §4 classifies this wrapper as
non-production and outside the storage/log-engine prohibition within its bounds.
This interpretation covers same-process exported-journal recovery only.

## Task input and bases

Task input: supervisor-supplied node specification and read-only design from
planner run `1792804497` (`/workspace/kix-run/logs/planner_1792804497`). No task
issue or file under `docs/tasks/` exists for this node; that input gap is recorded,
and none is created. This is not ASTRA program mode.

Branch: `agent/kix-plan-plan-aid-rejection-atomicity`. Initial task HEAD/base and
observed local `origin/main` both equal
`41a799987fe3a6a207abcce75045265c5796e1e4`; no local base delta; clean on entry.
`git fetch origin main` was NOT RUN because the explicit supervisor no-network
rule overrides AGENTS §1's fetch. Remote freshness is unverified.

Implementation/final task commit SHA: unassigned (uncommitted worktree over the
base above). Exact-head KTX and KIX CI run IDs/status/conclusions: unavailable /
NOT RUN, supervisor-owned after commit. Merge SHA, merge lock checks and
post-merge main CI: N/A. No older SHA's CI is transferred to this patch.

## Existing coverage map (inspected before adding tests)

| Requirement / source | Prior classification | Existing checks and remaining gap |
|---|---|---|
| Exact error names: `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests` | Sufficient for its deterministic code assertions; partial for full rejection atomicity | `fails()` compares only the digest. Individual tests sometimes inspect one view or proceed, but do not pair every code with full views/state/journal/restore/control progress. |
| Seeded rejection checks: `reference/ai_delegation/test_ai_delegation_properties.py::Base.rejected`, `AtomicityAndCodesTests.test_every_seeded_rejection_has_an_expected_code_and_leaves_state`, `test_coverage_guard_op_families_and_codes` | Partially covered | Digest and canonical state unchanged; seeded codes come from an oracle set; all 25 reachable codes occur. No per-rejection journal/restore/full-view equality or independent subsequent-command control. |
| Missing proposal paths: `reference/ai_delegation/test_contract_error_codes.py::AiDelegationErrorCodeGapTests.test_unknown_proposal_id_is_unknown_proposal_on_every_path` | Partially covered | Exact UNKNOWN_PROPOSAL on view, decide and withdraw, digest-only `fails()`; missing the full snapshot/recovery/progress checks. |
| Layer traceability: `docs/status/AI_DELEGATION_LAYER_MATRIX.md` | Sufficient as a 36-predicate citation map; not covered as executable full-state rejection evidence | Wrapper cells cite forwarded views/digest and digest-changing journal calls; no equivalence or layer binding is established. All statuses and DX-8/9/13 remain unchanged. |
| Wrapper recovery: `validation/2026-10-20-ai-delegation-wrap-conformance/README.md`, `readiness/conformance.py::BackendConformance` AI scenarios | Partially covered | Opens, issue/revoke, duplicate replay, fault recovery and execution-off checks; the record explicitly excludes a rejected-command sweep. |
| Returned data: `reference/ai_delegation/test_returned_data_isolation.py` | Sufficient for its copy/replay characterizations; not covered for this rejection corpus | Detached views/state, current-record duplicates and later-transition history; no rejected-command journal/restore/control sweep. |
| All 25 reachable codes, each with full views/state/digest/journal equality, restore and next valid command against control | Not fully covered for every code | New deterministic corpus fills this combined gap; existing static/code-name/copy tests are retained without duplication. |
| Execution flags and disabled constructor | Sufficient standalone; partial around rejection and recovery | Existing flags and constructor tests retained; new snapshots check every FALSE_FLAGS value and proposal effects_executed before/after rejection, restore and progress. |

## Per-code evidence

All 25 rows were **partially covered** for this node's combined requirement.
`M` = `reference/ai_delegation/test_ai_delegation_mock.py::AiDelegationMockTests`;
`P` = `reference/ai_delegation/test_ai_delegation_properties.py`;
`E` = `reference/ai_delegation/test_contract_error_codes.py::AiDelegationErrorCodeGapTests`.
The seeded guard is `P::AtomicityAndCodesTests.test_coverage_guard_op_families_and_codes`.
Prior references identify existing evidence rather than claim every trigger was
already deterministic or checked beyond its digest/state.

`F` (checks added) means: exact expected code; every grant/proposal view,
canonical state, digest and actual exported journal equal the before snapshot
and independently built unrejected control; restore equals that snapshot;
next valid result and full snapshot equal control on subject and restored
instance; exactly one new journal entry with the old prefix retained; restore
after progress; every FALSE_FLAGS value and proposal effects_executed false.
`R[code]` = `reference/ai_delegation/test_rejection_atomicity.py::RejectionAtomicityTests.test_every_aid_code_is_atomic_and_recoverable`
with that code as its subTest. All rows passed. Class A in this table concerns
the contract-defined code/state/view/flag behavior; journal/restore observations
are separately class B below, not new contract semantics.

| Code | Method | Trigger | Prior coverage | Checks added | Class | Test |
|---|---|---|---|---|---|---|
| `AI_SELF_EXPANSION_FORBIDDEN` | `issue_grant` | AI A attempts issue | Partial: `M.test_ai_cannot_issue_widen_reissue_or_revive` | F | A | `R[AI_SELF_EXPANSION_FORBIDDEN]` |
| `AI_CANNOT_DECIDE` | `decide_proposal` | A approves p1 | Partial: `M.test_ai_cannot_decide_and_strangers_are_rejected` | F | A | `R[AI_CANNOT_DECIDE]` |
| `UNKNOWN_ACTOR` | `call_tool` | stranger queries g1 | Partial: `M.test_ai_cannot_decide_and_strangers_are_rejected` | F | A | `R[UNKNOWN_ACTOR]` |
| `UNKNOWN_GRANT` | `revoke_grant` | H revokes missing grant | Partial: `M.test_grant_idempotency; seeded guard` | F | A | `R[UNKNOWN_GRANT]` |
| `UNKNOWN_PROPOSAL` | `decide_proposal` | H decides missing proposal | Partial: `E.test_unknown_proposal_id_is_unknown_proposal_on_every_path` | F | A | `R[UNKNOWN_PROPOSAL]` |
| `TOOL_NOT_ALLOWED` | `call_tool` | A2 proposes on QUERY-only g2 | Partial: `M.test_tool_level_follows_the_grant` | F | A | `R[TOOL_NOT_ALLOWED]` |
| `TRANSFER_FORBIDDEN` | `call_tool` | transfer deny tool | Partial: `M.test_denylist_and_unknown_tools` | F | A | `R[TRANSFER_FORBIDDEN]` |
| `REFUND_EXECUTION_FORBIDDEN` | `call_tool` | refund_execution deny tool | Partial: `M.test_denylist_and_unknown_tools` | F | A | `R[REFUND_EXECUTION_FORBIDDEN]` |
| `SIGNING_FORBIDDEN` | `call_tool` | sign deny tool | Partial: `M.test_denylist_and_unknown_tools` | F | A | `R[SIGNING_FORBIDDEN]` |
| `MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY` | `call_tool` | pay deny tool | Partial: `M.test_denylist_and_unknown_tools` | F | A | `R[MODEL_OUTPUT_CANNOT_ISSUE_OR_PAY]` |
| `EXECUTE_AUTHORITY_DISABLED` | `issue_grant` | H2 to A2 with EXECUTE | Partial: `M.test_execute_authority_and_attempt_are_disabled` | F | A | `R[EXECUTE_AUTHORITY_DISABLED]` |
| `DELEGATED_EXECUTION_DISABLED` | `attempt_execution` | A attempts execution of p1 | Partial: `M.test_execute_authority_and_attempt_are_disabled` | F | A | `R[DELEGATED_EXECUTION_DISABLED]` |
| `GRANT_NOT_CURRENT` | `call_tool` | g1 query at now=9 before start=10 | Partial: `M.test_period_boundaries` | F | A | `R[GRANT_NOT_CURRENT]` |
| `GRANT_REVOKED` | `call_tool` | query revoked g3 | Partial: `M.test_revocation_is_immediate_and_keeps_history` | F | A | `R[GRANT_REVOKED]` |
| `GRANT_EXPIRED` | `call_tool` | g1 query at now=21 after end=20 | Partial: `M.test_period_boundaries` | F | A | `R[GRANT_EXPIRED]` |
| `SCOPE_VIOLATION` | `call_tool` | proposal on s-b outside g1 scope | Partial: `M.test_scope_checks_membership_only` | F | A | `R[SCOPE_VIOLATION]` |
| `LIMIT_REQUIRED` | `issue_grant` | H2 to A2 with currency USD | Partial: `M.test_limits_are_required_fixture_bounds` | F | A | `R[LIMIT_REQUIRED]` |
| `PER_ACTION_EXCEEDED` | `call_tool` | amount 61 > per-action 60; prior charge 1, sum 62 <= 100 | Partial: `M.test_per_action_boundary` | F | A | `R[PER_ACTION_EXCEEDED]` |
| `CUMULATIVE_EXCEEDED` | `call_tool` | prior 60 + amount 41 > cumulative 100; amount <= 60 | Partial: `M.test_caps_count_open_proposals_and_release_on_reject_or_withdraw` | F | A | `R[CUMULATIVE_EXCEEDED]` |
| `COUNT_EXCEEDED` | `call_tool` | p1 + two count-only memos fill count 3; next proposal adds 1 | Partial: `P.CapTests.test_count_boundary_and_changes_consume_count` | F | A | `R[COUNT_EXCEEDED]` |
| `INVALID_ID` | `call_tool` | query_grant args contain x=1 | Partial: `P.AtomicityAndCodesTests.test_invalid_amounts_ids_and_now; seeded guard` | F | A | `R[INVALID_ID]` |
| `INVALID_AMOUNT` | `call_tool` | proposal amount 0 | Partial: `M.test_caps_count_open_proposals_and_release_on_reject_or_withdraw` | F | A | `R[INVALID_AMOUNT]` |
| `INVALID_PERIOD` | `call_tool` | query at now=-1 | Partial: `P.AtomicityAndCodesTests.test_invalid_amounts_ids_and_now` | F | A | `R[INVALID_PERIOD]` |
| `GRANT_BINDING_CONFLICT` | `issue_grant` | reissue g1 with changed scope s-b | Partial: `M.test_grant_idempotency` | F | A | `R[GRANT_BINDING_CONFLICT]` |
| `PROPOSAL_BINDING_CONFLICT` | `call_tool` | reuse p1 with amount 59 instead of 60 | Partial: `M.test_proposal_idempotency` | F | A | `R[PROPOSAL_BINDING_CONFLICT]` |

The shared fixture opens H/H2 and A/A2, issues g1 (QUERY+PROPOSE, scope s-a/x1,
period 10..20, KRW per-action/cumulative/count 60/100/3), creates p1, issues
QUERY-only g2 to A2, and issues/revokes H2-to-A g3. Each control is built
separately using the same public API, not restored from the subject. The
per-action case uses p1 amount 1; other cases use 60. The count case adds two
change memos without amounts before the snapshot. Thus the three cap rejections
each isolate one cap. All arguments are plain JSON; fixture numbers are not
product values.

Next command: A proposes p-next on g1 for amount 1 at now=15, reusing the rejected
p-next ids except for the existing-p1 binding-conflict case. For the full-count case,
H revokes g1 instead, exercising the revoke sequence and voiding pending
proposals. It succeeds first on the control, then identically on the subject
and restored instance. A coverage guard reads the contract's exact §8 heading,
excludes MOCK_INVARIANT, and checks that every other code occurs exactly once.
The new tests import the same AiDelegationError class as the wrapper; full
discovery found no duplicate-module identity error.


## Classification

- **A:** all 25 exact-code rejection cases match contract §§3–8: their public
  state and views are unchanged, flags stay false, and the next valid command
  has the same observable behavior as on the unrejected control. No code was
  unreachable in this corpus. MOCK_INVARIANT is excluded as in the contract
  error-code checker; constructor overlap already has dedicated existing tests.
- **B:** wrapper journal/restore behavior is an observed readiness API property,
  not an added AI delegation journal-format contract. Rejected calls leave no
  exported entry, restore reproduces the snapshots, and these valid progress
  commands each append exactly one entry. `_call`'s general digest-change-only
  journaling policy is source-observed; successful no-op journaling is not a new
  exhaustive check here.
- **B:** `test_unopened_registry_rejection_leaves_no_trace` observes INVALID_ID
  on an invalid open, unchanged unopened digest, empty actual journal, NOT_OPEN
  on canonical_state, empty-journal restore, then the same valid open as a
  control and restore after that open. These wrapper details are not specified
  by the delegation contract.
- **B, source observation only:** the wrapper JSON-normalizes arguments through
  `_entry`/`canonical_json`, so tuple inputs can become lists; this corpus uses
  only plain JSON inputs and makes no tuple-input contract claim. Precedence
  among simultaneous violations where unspecified remains the pre-existing
  property suite's class-B characterization; these cases do not decide it.
- **C:** none found by the new corpus or local checks. No reproduction/stop file
  was needed. The mock, wrapper and contracts are unchanged.

## Commands actually run and results

All Python verification commands ran with `PYTHONDONTWRITEBYTECODE=1`, in
foreground subprocesses, sequentially (no shell background jobs). The local
interpreter is Python 3.13.5; CI selects Python 3.12. Workflow inspection covered
`.github/workflows/protocol.yml` and `.github/workflows/ktx-kernel.yml`. The
runner extracted the 27 command lines verbatim from the protocol workflow's
“Stdlib offline document checks” block and executed every one, then its four
OpenAPI commands. The table records each actual command, exit and result.

| Command | Actual result |
|---|---|
| `git status --short`, `git rev-parse origin/main HEAD`, `git branch --show-current` | Clean entry; identical local refs and expected branch recorded above. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Both required blobs matched before edits. |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation -p test_rejection_atomicity.py -v` | PASS: 3 tests, including all 25 subcases. Initial run 0.134s; rerun after per-action isolation refinement 0.151s. |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation -v` (initial full run) | PASS: 77 tests, 2.991s, before the cap-isolation refinement. |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation -v` | PASS (exit 0): 77 tests, 3.316s test time. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS (exit 0): 184 tests, 1.766s test time. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS (exit 0): 395 tests, 9.376s test time. |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS (exit 0): 146 tests, 24.119s test time. |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS (exit 0): 163 tests, 2.543s test time. |
| `python3 -m unittest discover -s reference/rights_scale -t reference/rights_scale` | PASS (exit 0): 173 tests, 3.816s test time. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS (exit 0): 100 tests, 6.437s test time; non-failing unclosed-file ResourceWarning; embedded self-test: pass. |
| `python3 scripts/check_status_register.py` | PASS (exit 0): capability register ok: paths=349 ev_ids=15 original32=32. |
| `python3 scripts/check_status_register.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_rs_profile_traceability.py` | PASS (exit 0): rs profile traceability ok: blueprint=47 profile=47 expected=47. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_read_model_source_map.py` | PASS (exit 0): read model source map ok: queries=13 anchors=128 catalogues=2 citations=145. |
| `python3 scripts/check_read_model_source_map.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_docs_index.py` | PASS (exit 0): docs index ok: scanned=225 indexed=190 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_i12_proof_ids.py` | PASS (exit 0): i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_delegation_layer_matrix.py` | PASS (exit 0): delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_rs_predicate_evidence_map.py` | PASS (exit 0): rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_rs_im_evidence_map.py` | PASS (exit 0): rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0): tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0): contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0. |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_adapter_identity_map.py` | PASS (exit 0): adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_v5_transition_evidence_map.py` | PASS (exit 0): v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_readiness_evidence_map.py` | PASS (exit 0): readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_stage5_host.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_openapi_contract.py` | PASS (exit 0): openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff. |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 scripts/check_integration_gate_openapi.py` | PASS (exit 0): integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0): self-test: pass (intended negative fixtures detected). |
| `python3 --version` | Python 3.13.5. |
| Inline preservation verifier: `git hash-object`, `git ls-tree -r --name-only -z HEAD reference/v0.3-rc1`, `git show HEAD:<path>`, exact filesystem path-set comparison | PASS: locked blobs match; 108 historical files byte-identical, no extra/missing files. |
| `git rev-parse HEAD:reference/v0.3-rc1` | `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| `git diff --exit-code origin/main -- reference/v0.3-rc1 runtime .github .aiops docs/contracts docs/tasks docs/status readiness reference/ai_delegation/ai_delegation_mock.py reference/ai_delegation/ai_delegation_property_support.py` | PASS: empty diff. |
| `git status --porcelain=v1 --untracked-files=all -z` with exact allowed-path assertion | PASS: exactly the three changed paths below. |
| `git diff --check`; `git diff --no-index --check /dev/null <each-new-file>` | PASS: no whitespace diagnostics; tracked exit 0; new-file exit 1 indicates differences only, stdout/stderr empty. |
| `python3 scripts/check_docs_index.py` and `python3 scripts/check_docs_index.py --self-test` (after completing the record) | PASS: 225 scanned / 190 indexed / 35 allowlisted; self-test passed. |
| `git diff --check`, locked-file `git hash-object`, `git status --short`, `git rev-parse origin/main HEAD` (final recheck) | PASS: no whitespace diagnostics; required locks unchanged; three paths only; local main and HEAD still equal the recorded base. |

All 38 broad-run commands passed: seven suite invocations, 27 stdlib document
checks and four OpenAPI checks. No failing test/check run occurred. The final
broad run follows the last test-code change; only this evidence record was
completed afterwards. Rust tests/Clippy/fmt and the local KTX job were NOT RUN:
no runtime path changes; this follows the supplied design's path selection.
Full hosted KTX/KIX verification remains required on the supervisor's final
commit. Plain stage5 host evaluation was not run, matching CI's self-test-only
selection; no stage5 host qualification is claimed.


## Preservation and changed paths

Before edits, `git hash-object` matched both locked files:

| Path | Before Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

After the tests, `git hash-object` matched those same blobs again. The
historical reference tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`;
all 108 worktree files match HEAD byte-for-byte and the path sets are identical.
The protected-path diff against local origin/main is empty: no mock, property
support, readiness, contract, workflow, architecture/runtime, status, task input,
`.aiops/` or historical reference change. The architecture execution setting is
untouched. No commit/publication/merge action was taken.

Complete changed-path list:

- `reference/ai_delegation/test_rejection_atomicity.py`: full snapshots, exact-code
  corpus, actual journal restore, subsequent control progress, false flags,
  contract-code coverage guard and unopened-registry characterization.
- `validation/2026-10-25-aid-rejection-atomicity/README.md`: this record, coverage
  map, per-code evidence, commands, classification and limits.
- `docs/README.md`: one validation index bullet.


## Deviations, non-claims and remaining gates

Fetch omitted under the supervisor prohibition; supplied node/design is the task
input rather than a newly created immutable task file. G0 is interpreted from
that explicit supplied design, with no separate approval invented by the builder.
The fixture's starting p1 amount varies only for PER_ACTION_EXCEEDED (1 rather
than 60), avoiding an overlapping cumulative failure; COUNT_EXCEEDED fills its
own count through memos as planned. This is the only fixture refinement to the
design. No additional changed path or scope expansion was needed.

In-memory mock and readiness wrap only. Restore occurs in the same process;
no durability, cross-process recovery, journal-format contract, multi-entry
fault guarantee or codec-error rejection sweep is claimed. No grant ledger,
chain grant, execution, AI service, policy value, grade change, production
runtime, real funds or real PG/bank/KYC/Sui call. The 25 cases are a fixed corpus,
not an exhaustive search or an independent conformance audit. Product policy,
time-source, identity and legal decisions remain open with their existing owners.
Rust/Move/SDK/ZK/bootstrap/localnet jobs are outside this touched-path local
verification. Exact-head hosted KTX/KIX CI and non-author review remain supervisor
gates. READY will mean local builder handoff only, not merge authorization.
