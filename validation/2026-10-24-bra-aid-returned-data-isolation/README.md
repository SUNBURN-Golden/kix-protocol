# BRA and AI delegation returned-data isolation

Node: `plan-plan-bra-aid-returned-data-isolation`. Builder: Codex, 2026-10-24.
Builder-authored, source-informed, deterministic offline MOCK evidence; no
independent audit, capability promotion, activation or production claim.

## Task input and source anchors

The executing task document is the supervisor-supplied node specification and
read-only design plan, from planner run `1792804497`
(`/workspace/kix-run/logs/planner_1792804497`). No issue or `docs/tasks/` document
exists for this node. This is not ASTRA program mode.
Branch: `agent/kix-plan-plan-bra-aid-returned-data-isolation`.
Initial HEAD/base and locally observed `origin/main` are both
`5a09a325e2f6415b7fe638d0dbcd826b4d45fb86`; no local base delta.
The supervisor's explicit no-network rule overrides AGENTS.md §1's fetch:
`git fetch origin main` was NOT RUN; remote freshness is unverified.
Implementation/final task commit: not created; changes remain uncommitted over
that HEAD. Exact-head KTX and KIX CI run IDs/status/conclusions: unavailable /
NOT RUN. Merge SHA and post-merge main CI: N/A. Local passes do not satisfy the
hosted exact-head merge gate. Git/GitHub publication belongs to the supervisor.

Read authority: root README, DEVELOPMENT_PLAN, BASELINES, AUTHORITY_MODEL_1,
PROGRAM_DECISIONS_20260928 §5, control-plane pointer/client pin (candidate,
runtime disabled), the contracts below and #265/#275 validation records.

Contract anchors:
[BRA §§9.4, 10.7, 11.5](../../docs/contracts/BOOKING_RESALE_ADMISSION_GATES.md)
require first-response snapshots, `duplicate: true`, `applied: null` and one
effect. Section 9.4 explicitly keeps issue evidence version 1 after consumption.
[AID §7 / DLG-21/22/25/26](../../docs/contracts/AI_DELEGATION_AUTHORITY.md)
requires duplicates of current records, including REVOKED and
VOIDED_BY_REVOCATION, preserved first revocation reason, and no second charge.
The patterns extend
[#265](../2026-10-23-fsm-returned-data-isolation/README.md) and
[#275](../2026-10-24-reward-snapshot-isolation/README.md) without changing contracts.

## Existing coverage map (inspected before adding tests)

Paths below are relative to `reference/` unless specified otherwise.

| Requirement | Existing evidence | Classification and remaining gap |
|---|---|---|
| BRA ordinary first-result replay after later transitions | `booking_resale_admission/bra_property_support.py::Script.probe_replay`, reached by `test_gate_properties.py::SeededSequenceTests`; `test_reservation_fsm.py::test_unbound_issue_is_memory_evidence_without_economic_finality`, `test_resale_fsm.py::test_transfer_is_idempotent_and_does_not_reissue_a_credential`, `test_admission_fsm.py::test_issued_credential_is_consumed_once_and_replay_does_not_bump_version` | Sufficient for ordinary replay; caller-corrupted first and duplicate envelopes not covered. |
| BRA restoration | `bra_property_support.py::prefix_restore`; `test_reservation_fsm.py::test_restore_replays_a_lost_success_and_omits_rejections`; `test_resale_fsm.py::test_restore_replays_one_transfer_and_omits_rejections`; `test_admission_fsm.py::test_restart_replays_journal_and_retry_is_duplicate` | Sufficient for prefix state/digest restoration; partial for full historical response replay after caller corruption. |
| BRA export detachment | Reservation restore test above clears the exported outer list | Sufficient for reservation outer-list clearing; partial overall. Nested bodies, gate_roles, entry metadata and restore-input detachment not covered. No duplicate outer-clear-only test added. |
| BRA views, retained snapshot lifetime, inputs | Existing lifecycle/read-model views check contents and read-only queries | Not covered for directed nested mutations, lifetime and caller-held input detachment. |
| BRA rejection atomicity | `test_reservation_rejection_atomicity.py`, `test_adopt_issued_atomicity.py` | Sufficient existing evidence; out of scope here. |
| AID ordinary duplicate semantics | `ai_delegation/test_ai_delegation_properties.py::IdempotencyTests`; lifecycle replay checks in `test_ai_delegation_mock.py` | Sufficient for ordinary duplicates; partial for corruption: `Driver.step` already scribbles every returned result but checks digest only, without a separate untouched machine or exact subsequent full envelope. |
| AID view copies | `test_ai_delegation_properties.py::test_views_are_copies`, `ai_delegation_property_support.py::Driver.step` / `scribble` | Partial: no untouched control comparison, nested canonical-state mutation, or retained-view lifetime. |
| AID deterministic rebuild | `test_ai_delegation_properties.py::test_command_log_replay_reproduces_every_digest` | Sufficient; cited rather than duplicated. No journal/export/restore API exists. |
| AID input detachment and retained snapshots | Seeded command parameters are deep-copied into the driver log | Not covered for post-call caller mutations and retained snapshots across transitions. |
| Discovery infrastructure | `.github/workflows/protocol.yml` default unittest discovery | Sufficient; filenames match `test*.py`, no workflow edit. Only module-level fixture helpers/constants imported, no TestCase classes. |

## New evidence: gap per test and A/B/C classification

Both new modules contain exactly two classes, `ReturnedResultReplayTests` and
`CopyIsolationCharacterizationTests`. Only public machine methods are used.
Subject and untouched control machines are independently constructed with fresh
`deepcopy` arguments. Expected snapshots use stdlib `deepcopy`, not the
implementation's JSON-copy code. `_mutated` saves a deep copy and asserts each
individual mutation actually changed its target. Recursive corruption edits
nested scalar fields, deletes existing keys, clears nonempty lists and appends
to lists. Sentinels stay in caller-owned objects and never select policy values.
Each test compares fresh public views, canonical state and digest with the
control; BRA also compares fresh journals. AID checks envelope non-claim flags
and an independently encoded canonical digest.

| Suite / class | Test | Gap addressed |
|---|---|---|
| BRA / A | `test_reservation_first_results_survive_corruption_transitions_and_restore` | Corrupt every first response through clock/show/hold/confirm/payment/issue/authorize/consume and later slot-1 hold/release/clock. Replay every historical whole envelope at each prefix and from fresh-export restore. Mutates slots, gate_roles, reservation.right, evidence and admission. Assert replayed issue version 1 versus current right version 2. |
| BRA / A | `test_resale_first_results_survive_corruption_transitions_and_restore` | Same whole-envelope corruption/replay across standalone adopt/list/hold/release/payment/transfer/close and version-2 listing. Includes listing, ticket, right and evidence dues. |
| BRA / A | `test_admission_first_results_survive_corruption_transitions_and_restore` | Same corruption/replay across standalone adopt/authorize/consume, then a distinct slot-1 issued credential and clock. Includes credential, admission, evidence and right. |
| BRA / A | `test_mutated_duplicate_results_do_not_change_later_replays` | Corrupt duplicate envelopes for every accepted key immediately, after subsequent transitions, and on restored machines; exact replay equality and no second effect. |
| BRA / B | `test_views_are_detached` | Nested mutation of view/view_show/view_right/view_presentation/view_credential at valid prefixes, compared with independent controls. |
| BRA / B | `test_nested_journal_export_bodies_are_detached` | Nested journal body gate_roles/fields and entry metadata mutation; restore from fresh export, then mutate the retained restore input. |
| BRA / B | `test_retained_snapshots_survive_later_transitions` | First responses, views and exports retain their old values while each fresh canonical state advances. Afterwards corrupt retained objects and compare controls. |
| BRA / B | `test_inputs_detached_after_call` | Mutate the actual gate_roles input retained after register_show/adopt_issued, then check fresh state, original-argument replay and subsequent valid transitions. |
| AID / A | `test_corrupted_first_and_duplicate_results_do_not_change_duplicates` | Corrupt issue_grant, propose_action, propose_grant_change and decide_proposal results; compare exact duplicate envelopes with control's current views immediately and after every transition. Exercise approve, withdraw, reject, revoke and second revoke with changed reason. Assert explicit charged amount/count at every stage; voids/withdrawal/rejection release shares and first revoke reason remains. |
| AID / B | `test_views_and_canonical_state_are_detached` | Nested grant scope.subjects/limits/period, proposal memo.limits and canonical-state dictionary/list mutation, with controls. |
| AID / B | `test_retained_snapshots_survive_later_transitions` | Retain first responses, views and canonical-state snapshots across approval, withdrawal, rejection and revocation; fresh state changes, duplicate revoke does not. Corrupt retained snapshots afterwards. |
| AID / B | `test_inputs_detached_after_call` | Mutate actual authority/scope/limits/period passed to issue_grant and actual call_tool args/requested, including nested memo fields, after return; original-argument duplicate still matches control. |

Class A: contract-defined and matching. Class B: contract-undefined copy
ownership/lifetime, observed source-informed characterization only. Class C:
no explicit contract violation observed; no FSM fix or contract redefinition.
Sources are unbound: no settlement, ticket, ownership or external providers.
AID export/restore and first-response-store tests are N/A because the mock has
none; deterministic command-log rebuild remains covered by the cited test.

## Complete changed-path list

- `reference/booking_resale_admission/test_returned_data_isolation.py`
- `reference/ai_delegation/test_returned_data_isolation.py`
- `reference/booking_resale_admission/test_read_model_fixtures.py` (one import-precedence line; see deviation below)
- `validation/2026-10-24-bra-aid-returned-data-isolation/README.md`
- `docs/README.md` (one dated validation index bullet)

## Commands actually run and results

Test/check commands
use `PYTHONDONTWRITEBYTECODE=1`. Narrow modules run before full discovery and
local CI equivalents. No long job runs in the background.


| Command | Actual result |
|---|---|
| `git rev-parse HEAD origin/main`, `git branch --show-current`, `git status --short` | Base/HEAD/main and branch recorded above; entering worktree clean. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs`; `git ls-tree HEAD reference/v0.3-rc1` | Before edits: exact locks and historical tree match values below. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_returned_data_isolation.py -v` | PASS: 8 tests initially (0.534s), then 8 after sentinel helper fix (0.610s). |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation -p test_returned_data_isolation.py -v` | Initial FAIL: 4 tests, 1 mutation-effect assertion failure in repeated sentinel assignment (0.174s); after helper fix PASS: 4 tests (0.190s). |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` (first full attempt) | Exit 1 during collection: same-named credit module imported ahead of BRA due to existing read-model test path insertion. No FSM failure; corrected below. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission -p test_read_model_fixtures.py -v` | PASS: 7 tests (0.206s), after the import-precedence fix. |
| `python3 -m unittest discover -s reference/settlement_f01_f03 -t reference/settlement_f01_f03` | PASS (exit 0, 2.15s): 184 tests, 2.028s test time. |
| `python3 -m unittest discover -s reference/booking_resale_admission -t reference/booking_resale_admission` | PASS (exit 0, 7.165s): 187 tests, 6.916s test time. |
| `python3 -m unittest discover -s reference/credit_advance_f04 -t reference/credit_advance_f04` | PASS (exit 0, 22.97s): 146 tests, 22.380s test time. |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS (exit 0, 4.504s): 74 tests, 4.169s test time. |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS (exit 0, 3.595s): 163 tests, 3.328s test time. |
| `python3 scripts/check_status_register.py` | PASS (exit 0, 0.281s): capability register ok: paths=349 ev_ids=15 original32=32. |
| `python3 scripts/check_status_register.py --self-test` | PASS (exit 0, 0.745s): self-test: pass. |
| `python3 scripts/check_rs_profile_traceability.py` | PASS (exit 0, 0.025s): rs profile traceability ok: blueprint=47 profile=47 expected=47. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0, 0.026s): self-test: pass. |
| `python3 scripts/check_read_model_source_map.py` | PASS (exit 0, 0.436s): read model source map ok: queries=13 anchors=128 catalogues=2 citations=145. |
| `python3 scripts/check_read_model_source_map.py --self-test` | PASS (exit 0, 7.076s): self-test: pass. |
| `python3 scripts/check_docs_index.py` | PASS (exit 0, 0.041s): docs index ok: scanned=223 indexed=188 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0, 0.045s): self-test: pass. |
| `python3 scripts/check_i12_proof_ids.py` | PASS (exit 0, 0.03s): i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | PASS (exit 0, 0.022s): self-test: pass. |
| `python3 scripts/check_delegation_layer_matrix.py` | PASS (exit 0, 0.058s): delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | PASS (exit 0, 0.176s): self-test: pass. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | PASS (exit 0, 0.137s): rs predicate evidence map ok: rows=23 expected=23 citations=174 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | PASS (exit 0, 0.355s): self-test: pass. |
| `python3 scripts/check_rs_im_evidence_map.py` | PASS (exit 0, 0.08s): rs im evidence map ok: rows=30 expected=30 citations=200 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=5 PARTIAL=12 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | PASS (exit 0, 0.387s): self-test: pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0, 0.063s): tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0, 0.117s): self-test: pass. |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0, 0.491s): contract error code coverage ok: SET=34 BRA=64 BRA-RES9=10 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=199 RAISED=199 ASSERTED=199 COVERED=199 CLASS_B=0 CLASS_C=0. |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0, 33.298s): self-test: pass. |
| `python3 scripts/check_adapter_identity_map.py` | PASS (exit 0, 0.438s): adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | PASS (exit 0, 0.211s): self-test: pass. |
| `python3 scripts/check_v5_transition_evidence_map.py` | PASS (exit 0, 0.099s): v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | PASS (exit 0, 0.695s): self-test: pass. |
| `python3 scripts/check_readiness_evidence_map.py` | PASS (exit 0, 0.156s): readiness runtime evidence map ok: rows=36 expected=36 citations=183 EXERCISED=27 PARTIAL=0 NOT_EXERCISED=0 OPEN=9. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0, 3.524s): self-test: pass. |
| `python3 scripts/check_stage5_host.py --self-test` | PASS (exit 0, 0.114s): self-test: pass. |
| `python3 scripts/check_openapi_contract.py` | PASS (exit 0, 0.131s): openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff. |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS (exit 0, 0.113s): self-test: pass. |
| `python3 scripts/check_integration_gate_openapi.py` | PASS (exit 0, 0.137s): integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0, 0.119s): self-test: pass. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS (exit 0, 7.85s): 100 tests, 7.612s test time; non-failing unclosed-file ResourceWarning. |
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0, 0.034s): architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS (exit 0, 0.238s): 7 tests, 0.171s test time. |
| `python3 --version` | PASS (exit 0, 0.001s): Python 3.13.5. |
| Inline stdlib preservation verifier (`git hash-object`, NUL-delimited `git ls-tree` / `git show`, expanded `git status`, tracked/untracked whitespace checks) | PASS: required locks match; all 108 historical files byte-identical, no extra/missing paths; exactly five changed paths; no whitespace diagnostics. |
| `git diff --check`, `git diff --stat`, `git diff -- docs/README.md reference/booking_resale_admission/test_read_model_fixtures.py`, `git status --short` | PASS: no whitespace diagnostics; only the five listed authorized/deviation paths. Ordinary diff stat excludes the three untracked new files. |
| `python3 scripts/check_docs_index.py`, `python3 scripts/check_read_model_source_map.py`, `python3 scripts/check_contract_error_codes.py` (final rerun) | All PASS after the import fix and evidence update: index 223/188/35; source map 13 queries/128 anchors; error coverage 199 rows, all RAISED/ASSERTED/COVERED, CLASS_B=0/CLASS_C=0. |

All commands ran in the foreground. The stdlib runner captured the full-suite
and checker commands' actual exit/output and checked failures. Full reference runs
collected 187 BRA tests (179 existing plus 8 new) and 74 AID tests (70 existing
plus 4 new); no imported TestCase classes are collected twice. The document
block has 27 commands, plus four OpenAPI normal/self-test commands: all 31
passed. Python 3.13.5 locally versus CI Python 3.12; hosted evidence remains
unavailable. The integration suite uses synthetic loopback only; no public
endpoint or external provider was used.

## Preservation, deviations and limits

Before edits, both locked files matched with `git hash-object`:

| File | Before / after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` / identical |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` / identical |

Initial and final `reference/v0.3-rc1` tree:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. A NUL-delimited verifier used
`git ls-tree -r --name-only -z HEAD reference/v0.3-rc1` and `git show HEAD:<path>`
to compare all 108 actual worktree files byte-for-byte and check the exact path
set. Both locked files were rehashed after the tests and matched. Expanded
`git status --porcelain=v1 --untracked-files=all -z` contains exactly the five
listed paths. `git diff --no-index --check /dev/null <new-file>` on each of the
three new files exited 1 with no stdout/stderr (difference exit status, no
whitespace diagnostics); tracked `git diff --check` exited 0. No merge occurred,
so final-merge lock verification is N/A.
No machine, mock, contract, workflow, checker, register, .aiops or task input is
changed. All owner policy values stay `UNDETERMINED`; synthetic fixture limits,
amounts and periods do not define product policy.

Deviations: fetch omitted under the supervisor network prohibition; no task
file created under the explicit task-input restriction; AID restore is N/A as
anticipated by the design. Coverage mapping corrects the design's missing
reservation outer-export-clear evidence and recognizes AID's seeded result
scribble checks as partial corruption coverage. Scripts replay all historical
commands at every accepted prefix, strengthening the three requested stages.

A repository-proven design deviation adds a fifth changed path:
`test_read_model_fixtures.py` prepended sibling suite directories to `sys.path`.
During default BRA discovery, that made Python import credit's existing
`test_returned_data_isolation.py` when unittest expected BRA's same-named new
module. The narrow test pattern did not import the read-model test, so did not
show this collision. One line now inserts sibling paths at index 1, keeping
the active suite first, consistent with the lifecycle test helpers. Its seven
existing tests and the full default suites pass. This test-only collection fix
is necessary to meet default discovery acceptance; no workflow/checker or
machine changes were made. The design's exactly-four-path estimate is thus
superseded by these five paths. This is a test import issue, not class C.

An initial AID narrow run found a test-helper defect: a second corruption of
an already corrupted nested requested dictionary assigned the same sentinel,
so its mutation-effect assertion failed. No machine/control mismatch occurred.
The helper now alternates sentinels when needed, preserving the requirement
that every individual mutation changes its target; both narrow modules were
rerun successfully after the helper fix.

No external service, secrets, paid resources, equipment or policy decision is
needed. Not tested: production runtime, durability, concurrency, distributed
fencing, real bank/PG/KYC, real funds, chain execution/finality, legal compliance
or operational readiness. Rust/Move/SDK/ZK/bootstrap/localnet jobs are outside
the touched-path local verification; none of those implementations changed.
Non-author exact-HEAD review and exact-head KTX/KIX CI remain supervisor gates;
READY means local builder handoff only, not merge-ready or permission to merge.
