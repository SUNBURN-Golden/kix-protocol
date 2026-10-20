# token-reward-readiness-wrap

Node: `plan-plan-token-reward-readiness-wrap`. Adds `readiness/reward_wrap.py`, a local readiness journal wrap for `reference/token_reward/reward_fsm.py::RewardMachine` (the only reference FSM without one), registers it as the `reward` machine, and adds `RewardWrapTests` to `readiness/test_faults.py`. Issue: none (loop-proposed node, not in `.aiops/program.json`). Depends on: `plan-tl-predicate-evidence-map`. Audit floor A2. Not an ASTRA program-mode session. Scope follows `docs/decisions/PROGRAM_DECISIONS_20260928.md` §4 ("새 FSM 래핑" inside the bounds) and `docs/contracts/READINESS_RUNTIME.md`.

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head or final task head SHA and no exact-head CI run for this work; those belong in the pull request closure report (AGENTS.md §11).

Observed `origin/main` = branch HEAD = `6cdff624203a9610ed9b84fafec8dad07995c414` (merge of #223). No `git fetch` was run in this session (network actions are reserved to the supervisor); the recorded value is the worktree's local `origin/main` ref.

**This record is a builder-authored reading, not an independent review. No grade is raised and nothing is claimed for production.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `git rev-parse HEAD:reference/v0.3-rc1` = `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` before and after.

## Changed paths

| Path | Change |
|---|---|
| `readiness/reward_wrap.py` | New. `RewardWrap` mirrors `AiDelegationWrap`: explicit `open(opening_balances)`, the nine `REPLAYABLE` commands journaled only when `state_digest()` changed, pass-through views, `reject_external` delegation, `restore` replaying entries through public methods only. |
| `readiness/store.py` | `'reward'` added to `FSM_MACHINES`. |
| `readiness/machines.py` | `RewardWrap` import; `'reward'` in `MACHINES` and `RESTORE`. |
| `readiness/test_faults.py` | Additive only: `token_reward_model` import (same lazy-path pattern as `ai_delegation_mock`), `RewardWrap` import, module fixtures, `RewardWrapTests` (3 tests). No existing test edited. |
| `readiness/CONFORMANCE.md` | New section "Token reward wrap". |
| `validation/2026-10-20-token-reward-readiness-wrap/README.md` | This record. |
| `docs/README.md` | One index bullet. |

No `reference/**`, `runtime/**`, contract, mock, FSM, command, workflow, `.github`, `.aiops` or `docs/tasks` change. `integration_gate/fsm_contract.py` `MACHINE_TABLE` untouched: `reward` is an internal machine label, not a catalogue command; the gate still refuses FSM calls under a readiness dir.

## AGENTS.md §7: existing coverage

| Requirement | Existing | Status |
|---|---|---|
| Wrap with explicit open + digest-gated journaling | `readiness/ai_delegation_wrap.py` precedent | sufficiently covered for ai_delegation only; reward had no wrap |
| Torn write replays once | `test_ai_delegation_torn_revoke_replays_once_and_execution_stays_off` | partial: delegation machine only |
| Crash-before-durable leaves no record | `test_ai_delegation_crash_before_issue_does_not_create_the_grant` | partial: delegation machine only |
| `restore(export_journal())` round-trip | `FsmBoundary._recover` equality check, crash-point sweep digests | partial: reward machine not exercised |
| `durable` label stays false | false-label assertions in existing tests and sweep | partial: reward view/result flags not exercised |

The three new tests cover the reward-machine gap of each row. Existing readiness tests are unchanged and still green.

## What the wrap does

`RewardWrap.open(opening_balances)` constructs `RewardMachine` and journals `{'op': 'open', 'opening_balances': ...}`; a second open raises `ALREADY_OPEN`. Each public command builds a canonical entry from the caller's arguments, calls the inner FSM method, and appends the entry only when `state_digest()` changed (duplicates and stored rejections add nothing, matching FSM semantics). `restore(journal)` replays `open` then the command ops through the same public methods and requires `export_journal() == journal`; any divergence raises `RECOVERY_DIVERGENCE`. `restore([])` yields an unopened wrap (shared `ExploreBoundary` restores every registered machine).

## Commands run and results

| Command | Result |
|---|---|
| `git status`; `git rev-parse HEAD origin/main` | clean tree; both `6cdff62…` |
| `git hash-object` on the two locked files (before and after) | match the required blobs |
| `git rev-parse HEAD:reference/v0.3-rc1` (before and after) | `a6ecb12…` both times |
| `python3 -m unittest -v readiness.test_faults.RewardWrapTests` | 3 tests OK |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 74 tests OK (was 71) |
| `unittest discover` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward` | 48 / 155 / 48 / 70 / 61 tests OK |
| `check_docs_index.py`, `check_status_register.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`, `check_tl_predicate_evidence_map.py`, `check_contract_error_codes.py`, `check_adapter_identity_map.py`, `check_openapi_contract.py`, `check_integration_gate_openapi.py`, each plain and `--self-test` | exit 0 for all 26 runs |
| `check_sdk_client.py` | NOT_RUN: local toolchain mismatch, `node 20.19.2` vs `toolchains.json` nodeMajor 24; identical failure on the clean tree, runs hosted |
| `verify_runtime_architecture.py`, `test_runtime_architecture.py` | exit 0 |
| cargo, clippy, fmt | NOT_RUN: nothing under `runtime/` changed; they run hosted |
| npm SDK conformance/verify-compat | NOT_RUN: no `sdk` path change and local node is 20.19.2 vs required 24; runs hosted |
| exact-head KTX and KIX CI | NOT_RUN locally: belongs to the PR head per §10 |

## Class A / B / C

- Class A (contract-defined, matched): torn tail dropped and prefix replayed; crash-before-durable attempt absent after recovery; same idempotency key returns the stored result once (`READINESS_RUNTIME.md` lines 21–26); `durable`, `protocolTruth`, `productionConformance` false.
- Class B (contract does not define; observed characterizations): `restore(export_journal())` round-trips `canonical_state` (a `str`) and `state_digest` byte-for-byte in this process; an unopened wrap reports the `_UNOPENED` sentinel digest; a second `open` raises `ALREADY_OPEN`.
- Class C: none found.

## Non-claims

No power-loss, OS-crash or `fsync` result. Single process, single writer, one local file, off unless `--readiness-dir`. No real payout, PG, bank, KYC or chain call; `MOCK_TOKEN_REWARD_ONLY` provenance and the no-real-payout non-claims pass through verbatim. Not a `BackendConformance` or crash-point-sweep case; no backend adoption. No independent verification of TK-4, TK-7, TK-8, TK-12 or V6. Pool balances and amounts are caller-supplied test fixtures, not product policy. Untested for this machine: concurrency, rejected-command journals, multi-entry commands, `reconcile_unknown`, `observe_source_cancel`, `observe_krw_refund`, `supersede` journeys (the restore path supports them; no scenario exercises them here).

## Remaining uncertainty / follow-up candidates

- `docs/contracts/READINESS_RUNTIME.md` line 24 enumerates the wrapped machines and does not name `reward`; `docs/status/CURRENT_CAPABILITY_REGISTER.md` EV-READY lists `readiness/*.py` without `reward_wrap.py`. Both edits are outside this node's authorization; a later doc-sync node should update them.
- The wrap's journal entries store caller inputs, not the FSM's internal journal entries; equality is checked against the wrap journal. This matches the delegation precedent.

## Follow-ups owed to a later sync

`docs/status/CURRENT_CAPABILITY_REGISTER.md`, `DEVELOPMENT_PLAN.md` §5 and `.aiops` were not edited.
