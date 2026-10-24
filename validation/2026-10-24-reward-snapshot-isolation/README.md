# Reward nested snapshot isolation — builder record

Date: 2026-10-24. Node: `plan-plan-reward-snapshot-isolation`.
Author: Codex builder. This is separately attributed builder-authored,
source-informed, deterministic offline MOCK-only evidence, not independent
A2 review, acceptance, a capability grade increase, or merge readiness.

## Task input and source anchors

The task document is the supervisor-supplied node specification and read-only
Sonnet design plan in the executing prompt, from planner run `1792721264`
(supplied source `/workspace/kix-run/logs/planner_1792721264`). There is no
task issue or current `docs/tasks/` document for this node; none was created
or edited. This is not ASTRA program mode and the node is not in
`.aiops/program.json`. Dependencies: `tl-3-offchain`, `tl-4`,
`plan-token-reward-rejection-atomicity`, `plan-fsm-returned-data-isolation`;
their existing FSM, fixtures and test modules were inspected locally.

Branch: `agent/kix-plan-plan-reward-snapshot-isolation`.
Initial task HEAD / implementation base:
`afe7ded7abc1b6e6cc65c8b179c2d6dac009c891` (PR #265 merge).
Locally recorded `origin/main`: `a7e6febded343fe0fd43df2059874525194efecf`
(PR #274 merge). `git rev-list --left-right --count HEAD...origin/main`
returned `0 22`: this supplied worktree base is 22 commits behind that ref.
The delta was reported, with no rebase or merge. A scoped comparison found
no committed delta in `reference/token_reward/` or either verification
workflow. The supervisor explicitly prohibits network/GitHub actions, so
`git fetch origin main` was NOT RUN; remote freshness is unverified.

Implementation head and final committed task head: not created; edits remain
uncommitted over the initial HEAD, as instructed. Merge commit/post-merge
checks: not applicable. Exact-head KTX and KIX CI run IDs/status/conclusions:
unavailable / NOT RUN. Required non-author exact-HEAD review and both
completed/success CI gates still apply before merge readiness. The supervisor
owns publication; no commit, push, PR, issue, comment or merge was performed.

## Existing coverage mapped before adding tests

All test paths in this table are under `reference/token_reward/` unless noted.

| Requirement | Existing evidence | Coverage and remaining gap |
|---|---|---|
| Export detachment | `test_reward_fsm.py::RewardFsmTests.test_exported_journal_is_detached` | Sufficient for outer-list append and top-level view phase replacement. Nested journal bodies, approvals, payout/supersession lists and pool data only partially covered; those shallow cases are not added as standalone duplicates. |
| Input snapshots | `test_reward_fsm.py::RewardFsmTests.test_live_settlement_view_field_names_match_and_can_be_read` | Sufficient for top-level caller `source_view.phase` replacement; deeper input metadata, approval evidence, reward-key and resend-permit changes not covered. |
| Restore | `test_reward_fsm.py::RewardFsmTests.test_restore_replays_the_same_digest` | Canonical state/digest and a duplicate flag sufficiently covered. Complete historical replay envelopes, all scripted keys, and restore-input detachment not covered. |
| Replay/payout bounds | `test_tl4_fsm_properties.py::MachineScript.attempt`, `RewardFsmPropertyTests.test_TL4_TK07_replay_idempotency_and_supersede_bound_payouts`, `test_TL4_TK07_unknown_reconcile_creates_no_reward`, `test_TL4_TK07_random_command_sequences_hold_invariants` | Ordinary duplicate/applied, journal prefix preservation, same-byte resend, seeded sequences and final replay sufficiently covered. Caller-corrupted returned objects and full original envelopes after later transitions/restore not covered. |
| Token/KRW separation | `test_reward_fsm.py::RewardFsmTests.test_TL0_TK08_T1_token_and_krw_effects_stay_apart`; `test_tl4_fsm_properties.py::RewardFsmPropertyTests.test_TL4_TK08_krw_refund_does_not_move_the_token_phase` | Existing separation cases sufficient; partially covered under malicious caller mutation. New tests check separation after mutations without repeating a standalone ordinary-refund case. |
| Rejections | `test_reward_rejection_atomicity.py::RewardRejectionAtomicityTests` | Existing deterministic rejection/control/restore evidence and late-fault characterizations sufficient; no new rejection or fault-injection case. |
| Retained snapshots | Historical replay/property comparisons above; settlement/credit `test_returned_data_isolation.py` modules | Partial precedent; reward first results, views, pools and exports kept across later transitions not explicitly covered. |
| Discovery | `.github/workflows/protocol.yml`, “Offline reference state machines and OpenAPI pins” | Existing default `test*.py` unittest discovery collects the new module, without importing another test module or changing workflows. Local collection/results below. |

## New evidence and classification

Only `reference/token_reward/test_snapshot_isolation.py` is added as code.
It imports existing synthetic fixtures from `tl4_support`, uses public machine
methods and `copy.deepcopy` for expectations independently of the FSM's JSON
copy mechanism. Subject and control machines are constructed separately with
fresh fixture arguments. Every edit is checked against a saved copy to prove
it changes the caller-owned object. Fresh reward IDs/views, pool balances and
lists, canonical state, digest and journal are compared with the untouched
control after each mutation. Controls are unaffected by all caller edits.
This extends the TL-3 offchain MOCK evidence associated with the
[capability register](../../docs/status/CURRENT_CAPABILITY_REGISTER.md);
neither the register nor its grades are changed.

Class A (contract-defined and matching) is limited to TK-7 payout bounds under
duplicates/stable operation identity and TK-8 separate token/KRW effect IDs
and state machines, as stated in the [blueprint](../../docs/blueprints/optional-native-token-v1/README.md)
and [predicate map TK-7/TK-8](../../docs/status/TL_PREDICATE_EVIDENCE_MAP.md).
The script uses A: first payout, KRW refund note, supersede and second payout;
B: UNKNOWN, permitted same-byte resend and successful reconciliation. Final
counts are A=2 and B=1, with A's second effect marked as a supersession and
B's resend count fixed at 1. Intermediate counts also match the exact accepted
success steps. Pool spend count equals payout count and total spend is four
synthetic points per payout. KRW refund leaves token phase/outcome/effects
unchanged; KRW IDs never enter retained token IDs. MOCK provenance and all
`ALWAYS_FALSE_FLAGS` remain fixed. These checks run throughout mutation tests.

Class B (source-informed characterization, contract undefined) covers all
copying assertions, complete first-result envelopes, snapshot lifetime and
restore-input detachment. `RewardReplayIsolationTests` keeps those assertions
separate in its helper docstrings from its class A predicates;
`RewardCopyIsolationCharacterizationTests` labels its whole purpose as class B.
The seven new methods cover:

| New method | Gap addressed |
|---|---|
| `test_mutated_first_results_do_not_change_state_or_replay` | First results are kept by reference, then approval evidence is appended/replaced, payout outcomes edited, payout lists forged/cleared, supersession evidence/rules edited, effect IDs/KRW phase overwritten, nested source data/token IDs changed, and the reward key deleted from the envelope. Replays still equal the entire original result except `duplicate=True`, `applied=None`, including historical phases and accepted-entry counts. Both script phases' results are corrupted. |
| `test_mutated_duplicate_results_do_not_change_later_replays` | Every phase-1 and phase-2 key is replayed, its returned duplicate corrupted, and every complete original envelope replayed again before/after later transitions. |
| `test_mutated_inputs_after_call_are_detached` | Caller reward-key recipient, source nested metadata list, approval evidence list and resend-permit dictionary are changed immediately after their calls; replays always use freshly constructed identical arguments. |
| `test_mutated_views_and_pool_views_are_detached` | Nested reward views receive the same corruptions; pool balance, individual spend amount and credits list are changed without reaching retained state. |
| `test_mutated_journal_bodies_do_not_reach_state_or_restore` | Exported approval/source evidence, source phase, reward-key recipient, non-null execution permit deletion and entry reward ID changes are discarded. Restore uses a fresh unmodified export; the caller list supplied to restore is then corrupted, with restored state and original replays unchanged. |
| `test_retained_snapshots_survive_later_transitions` | Actual first-result references, views, pool and export snapshots stay equal to their deep copies at each subsequent valid transition. Fresh A phase differs during supersede and its final rule/payout count differs; B moves UNKNOWN→ISSUED. Fresh pools/exports differ too. |
| `test_restore_replays_complete_first_envelopes` | The normalized `prior_record=None` fixture is asserted in submit journals. All keys replay completely after restoring phase 1, advancing the restored machine, and restoring the full unmodified journal; corrupting a restored duplicate cannot change its next replay. |

No class C contract violation or failing class B isolation assertion was found.
No implementation or semantics were changed. Copy behavior is observed, not
newly specified. A source-reading uncertainty remains outside these assertions:
`reward_fsm.py::_call/_fingerprint` fingerprints raw arguments, whereas
`restore` replays normalized bodies and `_approval` adds `prior_record`.
An approval omitting `prior_record` can therefore replay before restore yet
conflict after restore. This note is source-informed, not separately executed
evidence or a class C claim. All module approvals explicitly set
`prior_record=None`, including supersede/resend and every identical replay.

## Complete changed-path list

- `reference/token_reward/test_snapshot_isolation.py` (new tests).
- `validation/2026-10-24-reward-snapshot-isolation/README.md` (this record).
- `docs/README.md` (one validation index link).

## Actual local verification

Environment: Python 3.13.5 (CI selects 3.12). Every Python test/check below
uses `PYTHONDONTWRITEBYTECODE=1`. Commands are run in the foreground, narrow
discovery first, then complete discovery and the relevant local workflow
equivalents. The actual workflow contains 27 document-check commands (13
plain/self-test pairs plus stage-5 host self-test), rather than the design's
stated 25. The run block is authoritative; all 27 are required here.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_snapshot_isolation.py -v` | PASS: 7 tests, 0.672s. |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS: 163 tests, 1.774s; all seven new tests collected by default discovery. |

The following commands were executed sequentially by a stdlib
`subprocess.run` driver. Each exit status and output was captured; the
durations for checks are measured elapsed process time. There were no
test/check failures and no fixes or retries were needed.

| Command | Actual result |
|---|---|
| `for s in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do python3 -m unittest discover -s reference/$s -t reference/$s \|\| exit; done` | PASS (foreground `bash -c` with bytecode disabled): settlement 184 tests / 1.729s; booking/resale/admission 162 / 0.995s; credit 146 / 7.619s; AI delegation 70 / 2.604s; token reward 163 / 1.683s. |
| `python3 scripts/check_status_register.py` | PASS (exit 0, 0.161s): capability register ok: paths=331 ev_ids=15 original32=32. |
| `python3 scripts/check_status_register.py --self-test` | PASS (exit 0, 0.553s): self-test: pass. |
| `python3 scripts/check_rs_profile_traceability.py` | PASS (exit 0, 0.030s): rs profile traceability ok: blueprint=47 profile=47 expected=47. |
| `python3 scripts/check_rs_profile_traceability.py --self-test` | PASS (exit 0, 0.023s): self-test: pass. |
| `python3 scripts/check_read_model_source_map.py` | PASS (exit 0, 0.535s): read model source map ok: queries=13 anchors=128 catalogues=2 citations=145. |
| `python3 scripts/check_read_model_source_map.py --self-test` | PASS (exit 0, 6.580s): self-test: pass. |
| `python3 scripts/check_docs_index.py` | PASS (exit 0, 0.027s): docs index ok: scanned=213 indexed=178 allowlisted=35. |
| `python3 scripts/check_docs_index.py --self-test` | PASS (exit 0, 0.034s): self-test: pass. |
| `python3 scripts/check_i12_proof_ids.py` | PASS (exit 0, 0.024s): i12 proof ids ok: proof_headings=4 proof_keys=10 pack_keys=14 expected=14. |
| `python3 scripts/check_i12_proof_ids.py --self-test` | PASS (exit 0, 0.022s): self-test: pass. |
| `python3 scripts/check_delegation_layer_matrix.py` | PASS (exit 0, 0.061s): delegation layer matrix ok: rows=36 expected=36 citations=79 MOCK_ONLY=15 ANALOGUE_NOT_BOUND=7 NO_LAYER=8 NOT_APPLICABLE_BY_DESIGN=6. |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | PASS (exit 0, 0.199s): self-test: pass. |
| `python3 scripts/check_rs_predicate_evidence_map.py` | PASS (exit 0, 0.084s): rs predicate evidence map ok: rows=23 expected=23 citations=173 COVERED_LOCALNET=13 COVERED_MODEL_OR_MEMORY=2 PARTIAL=6 NOT_COVERED=0 MEASUREMENT_ONLY=2. |
| `python3 scripts/check_rs_predicate_evidence_map.py --self-test` | PASS (exit 0, 0.344s): self-test: pass. |
| `python3 scripts/check_rs_im_evidence_map.py` | PASS (exit 0, 0.072s): rs im evidence map ok: rows=30 expected=30 citations=197 COVERED_LOCALNET=11 COVERED_MODEL_OR_MEMORY=4 PARTIAL=13 NOT_COVERED=0 MEASUREMENT_ONLY=0 UNCHANGED_BY_DESIGN=2. |
| `python3 scripts/check_rs_im_evidence_map.py --self-test` | PASS (exit 0, 0.372s): self-test: pass. |
| `python3 scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0, 0.034s): tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7. |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0, 0.090s): self-test: pass. |
| `python3 scripts/check_contract_error_codes.py` | PASS (exit 0, 0.342s): contract error code coverage ok: SET=34 BRA=64 BRA-RES=20 BRA-ADM=15 F04=16 F04-FSM=15 AID=25 rows=189 RAISED=189 ASSERTED=189 COVERED=189 CLASS_B=0 CLASS_C=0. |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS (exit 0, 8.354s): self-test: pass. |
| `python3 scripts/check_adapter_identity_map.py` | PASS (exit 0, 0.039s): adapter identity evidence map ok: rows=17 expected=17 citations=56 CARRIED=2 PARTIAL=7 NO_SURFACE=0 UNDETERMINED=8. |
| `python3 scripts/check_adapter_identity_map.py --self-test` | PASS (exit 0, 0.169s): self-test: pass. |
| `python3 scripts/check_v5_transition_evidence_map.py` | PASS (exit 0, 0.049s): v5 transition evidence map ok: rows=10 expected=10 citations=77 TESTED=6 STOPPED=4 OPEN=0. |
| `python3 scripts/check_v5_transition_evidence_map.py --self-test` | PASS (exit 0, 0.523s): self-test: pass. |
| `python3 scripts/check_readiness_evidence_map.py` | PASS (exit 0, 0.125s): readiness runtime evidence map ok: rows=36 expected=36 citations=177 EXERCISED=25 PARTIAL=2 NOT_EXERCISED=0 OPEN=9. |
| `python3 scripts/check_readiness_evidence_map.py --self-test` | PASS (exit 0, 2.352s): self-test: pass. |
| `python3 scripts/check_stage5_host.py --self-test` | PASS (exit 0, 0.028s): self-test: pass. |
| `python3 scripts/check_openapi_contract.py` | PASS (exit 0, 0.072s): openapi contract pin ok: commands=84 core=40 fsm=44 sha256=ed827de1a8bfe7c48612473965793dcaab65137e575f862761fd160f77ae4c1e gitBlob=619ae21c82ca3df5661bd3831613f15fa65225ff. |
| `python3 scripts/check_openapi_contract.py --self-test` | PASS (exit 0, 0.097s): self-test: pass. |
| `python3 scripts/check_integration_gate_openapi.py` | PASS (exit 0, 0.079s): integration-gate openapi ok: commands=84 productionEndpoint=false publicHost=false. |
| `python3 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0, 0.108s): self-test: pass. |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS (exit 0, 5.803s): 88 tests, 5.631s test time. |
| `python3 scripts/verify_runtime_architecture.py` | PASS (exit 0, 0.035s): architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified. |
| `python3 scripts/test_runtime_architecture.py` | PASS (exit 0, 0.348s): 7 tests, 0.269s test time. |
| `python3 --version` | Python 3.13.5. |
| `git rev-parse HEAD origin/main HEAD:reference/v0.3-rc1` | Recorded the three exact source anchors above before edits. |
| `git rev-list --left-right --count HEAD...origin/main` | `0 22`; supplied base preserved. |
| `git diff --name-only HEAD origin/main -- reference/token_reward .github/workflows/protocol.yml .github/workflows/ktx-kernel.yml` | No output: scoped inputs/workflows identical across the base/main delta. |
| `git diff --check` | PASS (exit 0). |
| `git diff --no-index --check /dev/null reference/token_reward/test_snapshot_isolation.py` and the same command for the new validation README | Each exits 1 because `--no-index` implies difference exit status for the added file; stdout/stderr empty (no whitespace diagnostics). A stdlib driver confirmed those exact results. |
| `git status --short`, `git diff --stat`, `git diff -- docs/README.md` | Only the three authorized paths (expanded individually by the verifier); one new index bullet. Untracked test/record are absent from ordinary diff stat until the supervisor stages them. |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | Before and after: both match the exact required blobs below. |
| `git rev-parse HEAD:reference/v0.3-rc1` | Before and after: `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. |
| Inline `PYTHONDONTWRITEBYTECODE=1 python3 -` preservation verifier | PASS: `git hash-object` checks literal lock hashes; `git ls-tree -r --name-only -z HEAD reference/v0.3-rc1` and `git show HEAD:<path>` verify all 108 files byte-for-byte and exact path set; expanded `git status --porcelain=v1 --untracked-files=all` equals exactly the three authorized files. |

## Preservation and limits

Before edits the worktree was clean. Both locked blobs matched their required
values with `git hash-object`:

| File | Before / after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` / identical |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` / identical |

`git rev-parse HEAD:reference/v0.3-rc1` before work:
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`.
After work the same tree ID was recorded; every one of its 108 files
was compared byte-for-byte with HEAD, with no extra or missing files. Both
locked blobs were rechecked and matched; exactly three authorized files differ.
No locked or historical-reference file, FSM/model, contract, workflow,
register, program or task file was edited. All owner policy values remain `UNDETERMINED` with their
existing owners; fixture points, balances, evidence and approval slots carry
no policy decision. No new protocol command, activation or external execution.

Not tested: concurrency, storage/durability, production runtime, distributed
fencing, provider/bank exactly-once behavior, chain execution/finality,
real funds, legal compliance, exhaustive mutations or operational readiness.
Rust tests/Clippy/formatting, SDK/Move/ZK/bootstrap/localnet jobs: NOT RUN,
because no corresponding implementation path changes and this node's
verification boundary is stdlib offline tests and document checks.
No independent audit or exact-head CI result is claimed; no merge occurred.

## Deviations and remaining gates

- Fetch omitted under the explicit supervisor ban on network actions; the
  locally observed main is newer than the supplied base, which was preserved.
- No `docs/tasks/` input created: the supplied prompt is the authorized node
  input and expressly forbids task-document edits.
- Python 3.13.5 locally versus CI's 3.12; hosted results remain required.
- The design's payout equality applies at completed cycles. During UNKNOWN
  B has zero payouts; after supersede but before its success A still has one.
  Tests check the exact intermediate counts and the explicit at-most bound.
- The source-view fixture extends `committed_view()` with opaque synthetic
  nested evidence metadata to probe deeper copying than the existing phase
  replacement test. It adds no command or policy semantics.
- Current workflow document-check list has 27 commands, not the design's 25.

Non-author exact-HEAD review and successful exact-head KTX/KIX workflows remain
supervisor gates. No stop-condition resource or owner policy decision is needed
for this test-only node; `DECISION_REQUIRED.md` is not created. Further mutation
surfaces or the normalized/raw fingerprint question require separately scoped
owner work; this record does not authorize a semantics change.
