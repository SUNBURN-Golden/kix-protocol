# Reward wrap conformance

Node: `plan-plan-reward-wrap-conformance`. Issue: none. Task document: the user-supplied node envelope and read-only design plan in this session; no file under `docs/tasks/` defines this loop-proposed node. Dependency: `plan-plan-token-reward-readiness-wrap`. Audit floor A2. Not an ASTRA program-mode session.

Builder-authored local evidence, not independent review or a grade increase. Implementation is ready for supervisor handoff only, not merge-ready.

## Source and publication boundaries

Observed local `origin/main` and branch HEAD both equal `4e3ce63eaca8ab766c9c88adc712554fb0027d36`; branch `agent/kix-plan-plan-reward-wrap-conformance`. `git fetch origin main` ran once at session start under the AGENTS §1 protocol; it is read-only and confirmed the base is current main. No base delta.

No commit, push, PR, issue or comment was made. Implementation/final task SHA: not yet assigned (uncommitted worktree). Exact-head KTX and KIX CI run IDs/status/conclusions: NOT_RUN, supervisor-owned after commit. Merge SHA and post-merge CI: not applicable. No old-head CI is transferred to this patch.

## Changed paths

- `readiness/conformance.py`: `token_reward` reference suite on the path, shared reward fixtures moved in from `test_faults.py`, three adapter-neutral reward scenarios, `_reward_open_call`/`_reward_opened` helpers.
- `readiness/test_faults.py`: reward fixtures re-imported under their existing `_reward_*` names (`RewardWrapTests` bodies unchanged), seventh machine sweep row (6 commands, 12 fault cells), two subsumption cells, per-cell `(error_type, code)` replay dispatch; existing `ExtensionTests`/`RewardWrapTests` retained.
- `readiness/CONFORMANCE.md`: 58 cases / 29 commands, eleven subsumed cells, class-B replay characterization for the reward `open`, and a reward fault-to-case table.
- `docs/README.md`: validation index pointer.
- `validation/2026-10-21-reward-wrap-conformance/README.md`: this evidence record.

No runtime, wrap, journal format, contract, workflow, `.aiops/`, task document or reference implementation change.

## Locks

Before and after work, `git hash-object` gives:

| Locked path | Required and observed blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

`HEAD:reference/v0.3-rc1` tree is `a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Final diff and byte comparison against tracked HEAD verify that reference files remain byte-identical. No final merge exists to check.

## Existing coverage mapping (AGENTS §7)

| Requirement | Before this node | Gap addressed |
|---|---|---|
| Wrap opens once across restart; same reward replay and unchanged journal/digest; resent `open` refused | Not covered by BackendConformance | `test_reward_open_observe_and_hold_replay_across_restart` |
| Torn mark_eligible recovery; replay; external execution refusal | Partially covered: `RewardWrapTests.test_reward_torn_write_replays_once` uses FsmBoundary directly | `test_reward_torn_mark_eligible_recovers_and_replays_once` exposes it through the backend adapter and pins `reject_external` |
| Crash-before-observe leaves no reward | Partially covered: `RewardWrapTests.test_reward_crash_before_observe_leaves_no_reward` | `test_reward_crash_before_durable_observe_leaves_no_reward` adds the adapter-neutral scenario and exact reward replay |
| Every reward command index × both fault kinds | Not covered | `CrashPointSweepTests.test_crash_point_sweep_reward`: open, observe, hold, mark_eligible, submit, observe_transfer_effects × partial/crash_before_durable |
| Existing fault cells remain subsumed | Sufficient for six prior machines; missing reward rows | Subsumption test now pins eleven cells, including both dedicated reward fault cases |
| Restore round-trip, observation fields, pool view | Sufficient in `RewardWrapTests` | Retained without editing those methods |

The sweep retains prefix recovery, fail-stop, first-resend result, no second journal entry, final digest/journal, record budget and false-label assertions. The six existing machines retain their required `duplicate`/`applied` shapes; only the two keyless `open` resends ride the `REPLAY_ERRORS` path, each pinned to its own wrap's `WrapError` class.

## Commands actually run

All jobs were foreground. Python tests used `PYTHONDONTWRITEBYTECODE=1`.

| Command | Result |
|---|---|
| `git fetch origin main` | Fetched; local `origin/main` and HEAD both `4e3ce63e…` (read-only, session-start protocol) |
| `git status`, `git log --oneline -5`, `git branch --show-current` | Clean tree on `agent/kix-plan-plan-reward-wrap-conformance`, up to date with `origin/main` |
| `python3 -m unittest readiness.test_faults` (baseline) | PASS: 41 tests |
| `python3 -m unittest -v readiness.test_faults` | PASS: 45 tests, including the three reward conformance cases and `test_crash_point_sweep_reward` |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | PASS: 82 tests |
| `for suite in settlement_f01_f03 booking_resale_admission credit_advance_f04 ai_delegation token_reward; do python3 -m unittest discover -s "reference/$suite" -t "reference/$suite"; done` | PASS: respectively 67 / 162 / 48 / 70 / 156 tests |
| `python3 scripts/check_<name>.py` and `--self-test` for status_register, rs_profile_traceability, read_model_source_map, docs_index, i12_proof_ids, delegation_layer_matrix, rs_predicate_evidence_map, rs_im_evidence_map, tl_predicate_evidence_map, contract_error_codes, adapter_identity_map, v5_transition_evidence_map, openapi_contract, integration_gate_openapi | PASS: all 14 checks plus self-tests after the record file existed; `check_docs_index` failed once mid-task with `broken index link: validation/2026-10-21-reward-wrap-conformance/README.md` while the index entry preceded the file, then passed |
| Negative control heredoc (`python3 -`, throwaway, not committed) | `test_reward_torn_mark_eligible_recovers_and_replays_once`, `test_reward_crash_before_durable_observe_leaves_no_reward` and `test_crash_point_sweep_reward` FAIL under `FaultDroppingAdapter` (an `FsmBoundary.call` that drops the `fault` kwarg; `ReadinessFault` never raised); all three reward conformance cases and the sweep FAIL under `NonPersistingAdapter` (`open_boundary` lands on a fresh empty directory); `test_reward_open_observe_and_hold_replay_across_restart` passes under the fault-dropping adapter as expected because it injects no fault |
| `git diff --check` | PASS: no whitespace errors |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before and after) | PASS: required blobs above |
| `git rev-parse HEAD:reference/v0.3-rc1` | Unchanged tree above |
| `git diff --exit-code HEAD -- runtime reference .aiops docs/tasks .github` | PASS: no changes in protected/excluded tracked paths |
| `git status --short` | Only the five changed paths listed above; no unexpected/untracked protected files |

Rust tests, Clippy and fmt: NOT_RUN; no Rust files change, so `ktx-kernel.yml`'s compile steps have no touched input. The KTX workflow's locked-blob check is covered locally by the `git hash-object` rows above. Full protocol/kernel hosted checks remain required at the supervisor's exact final commit and are not claimed green here.

## Classification and non-claims

- Class A: observed behavior matches READINESS_RUNTIME's journal rules: prefix recovery after a torn tail, no reward before the accepted append, idempotent replay without a second effect, no record consumed by the injected fault, `reject_external` refused, `durable` false.
- Class B: `open` has no idempotency key or duplicate flag; reopening an open wrap raises `RewardWrap.WrapError('ALREADY_OPEN')` without journal/digest change, and the two wraps define distinct `WrapError` classes. Exact first-resend result and cross-instance digest equality remain characterizations. All 29 swept commands emit one entry; multi-entry fault behavior is untested. The reward wrap journals a command only when the digest changed.
- Class C: none found on unmodified wrap/source.

No power-loss, OS-crash, fsync, lost-ack-after-append, concurrency, rejected-command sweep, production durability, chain finality, real funds, live provider, backend adoption, payout or independent-conformance claim. `MOCK_TOKEN_REWARD_ONLY` provenance is unchanged and a matched replay is not a payout, bank debit or chain finality.

## Deviations and remaining gates

- The supplied design's negative control used only a fault-dropping adapter; `test_reward_open_observe_and_hold_replay_across_restart` injects no fault and would stay green under it, so a second wrong adapter (`NonPersistingAdapter`) was added so that every new case fails against at least one deliberately wrong adapter, as the node acceptance requires.
- The sweep sequence code uses the existing `_observe_reward`/`_eligible_reward` names (aliases of the moved fixtures) for consistency with `RewardWrapTests` instead of the public names shown in the design sketch.
- `reward_key`/`reward_source_view` are used only inside the moved fixtures, so only the four names the test module needs are re-imported; `POOLS`/`reward_id` dropped from the test module import list accordingly.
- One extra assertion beyond the design: restart replay equality of the reward view (`replay['reward'] == held['reward']`), mirroring the merged AI node's grant-equality check.
- DEVELOPMENT_PLAN §5 register row intentionally left to the register-sync node, as #226 did.

Supervisor must commit, obtain required exact-head KTX/KIX success and non-author review, and handle any authorized publication/merge and post-merge verification. No product decision or source change was required.
