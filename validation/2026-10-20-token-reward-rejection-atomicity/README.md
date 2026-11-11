# token-reward-rejection-atomicity

Node: `plan-token-reward-rejection-atomicity`. Adds `reference/token_reward/test_reward_rejection_atomicity.py` (95 tests), an audit of `reward_fsm.py::RewardMachine` rejection atomicity that repeats the merged `test_reservation_rejection_atomicity.py` (#219) pattern inside the TL-3 off-chain MOCK bounds: every `_call`-routed command's deterministic rejections are compared against an untouched control on `state_digest`, `canonical_state`, `export_journal` and the `restore(export_journal())` round trip, and a test-owned fault-injection harness (`mock.patch.object` on `RewardMachine._invariant` and on `PoolLedger._conserve`) pins what a late failure leaves. Issue: none (loop-proposed node, not in `.aiops/program.json`). Depends on: `tl-3-offchain`. Audit floor A2. Not an ASTRA program-mode session.

This session did not commit, push, open a pull request, create or close an issue, or comment. There is no implementation head or final task head SHA and no exact-head CI run for this work; those belong in the pull request closure report (AGENTS.md §11).

Observed `origin/main` = branch HEAD = `154e9aae3da1bf0044dad606fcfd7e2fb6b3f8df` (merge of #227). No `git fetch` was run in this session (network actions are reserved to the supervisor); the recorded value is the worktree's local `origin/main` ref.

**This record is a builder-authored reading, not an independent review. No grade is raised and nothing is claimed for production.**

## Locks

`git hash-object` before and after: `runtime/crates/kix-kernel/src/lib.rs` `69564b166f0c27f9af5d8422f0a466b18d74c20f`; `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` `b607996c83a119c349f1cc90469ac1ba82764e20`. Both match. `git rev-parse HEAD:reference/v0.3-rc1` = `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` before and after.

## Changed paths

| Path | Change |
|---|---|
| `reference/token_reward/test_reward_rejection_atomicity.py` | New test module. Audit cases only; imports `RewardMachine`, `PoolLedger`/`TokenRewardError`, and the shared `tl4_support` fixtures. |
| `validation/2026-10-20-token-reward-rejection-atomicity/README.md` | This record. |
| `docs/README.md` | One index bullet under the 2026-10-20 section. |

No `reward_fsm.py`, `token_reward_model.py`, `tl4_support.py`, contract, register, plan, `.aiops`, `docs/tasks`, `readiness/` or workflow change. Findings are recorded, not fixed.

## Command enumeration

Every `_call`-routed command has deterministic rejection cases (`test_<cmd>_<reason>_leaves_no_trace`): reject with its own fresh idempotency key, replay the stored error, compare against the untouched control, then run a valid op on both and compare again.

| Command | Mutation boundary | Covered deterministic rejections |
|---|---|---|
| `observe` | `self._rewards[derived]` → `_invariant` → `_accept` | `REWARD_ALREADY_OBSERVED`, `RULE_VERSION_REPAY_FORBIDDEN`, `SOURCE_NOT_COMMITTED`, `SOURCE_VIEW_REJECTED`, `CURRENCY_UNSUPPORTED`, `SOURCE_KIND_UNSUPPORTED`, `REWARD_KEY_FIELDS`, `INVALID_AMOUNT`, `INVALID_ID`, `INVALID_RULE_VERSION` |
| `hold` | `reward["phase"]` → `_invariant` | `UNKNOWN_REWARD`, `ILLEGAL_TRANSITION`, `TERMINAL_IMMUTABLE` |
| `mark_eligible` | `_apply_caps` gate → phase+fields → `_invariant` | `UNKNOWN_REWARD`, `ILLEGAL_TRANSITION`, `TERMINAL_IMMUTABLE`, `WINDOW_OPEN`, `ABUSE_BLOCKED`, `ABUSE_KIND_UNEXPECTED`, `ABUSE_KIND_UNSUPPORTED`, `CAP_EXHAUSTED_PAUSED`, `FLAG_TYPE`, `SOURCE_NOT_COMMITTED`, `INVALID_NONNEGATIVE` |
| `submit` | `_approval_ids.add` + fields → `_invariant`; UNKNOWN→`_resend` | `UNKNOWN_REWARD`, `ILLEGAL_TRANSITION`, `TERMINAL_IMMUTABLE`, `AI_APPROVAL_REJECTED`, `APPROVAL_FIELDS`, `ACTOR_TYPE_REJECTED`, `APPROVAL_GENERATION`, `APPROVAL_EVIDENCE_REQUIRED`, `APPROVAL_EVIDENCE_UNKNOWN`, `APPROVAL_RECORD_REUSED`, `BUDGET_EXCEEDED_PAUSED`, `PERMIT_UNEXPECTED`, `POOL_UNKNOWN`, `POOL_FORBIDDEN_FOR_TOKEN_SPEND`, `DIGEST_INVALID`, `INVALID_NONNEGATIVE`; resend: `RESEND_PERMIT_REQUIRED`, `DIGEST_MISMATCH`, `SPEND_POOL_CONFLICT`, `BUDGET_EXCEEDED_PAUSED` |
| `observe_transfer_effects` | `_apply_outcome` (pool spend + fields) → `_invariant` | `UNKNOWN_REWARD`, `ILLEGAL_TRANSITION`, `TERMINAL_IMMUTABLE` (ISSUED and REVERSED), `DIGEST_INVALID`, `OUTCOME_UNSUPPORTED`, `TOKEN_EFFECT_CLOSED`, `POOL_EXHAUSTED_PAUSED` |
| `reconcile_unknown` | `_apply_outcome`/fields → post-checks → `_invariant` | `UNKNOWN_REWARD`, `ILLEGAL_TRANSITION`, `TERMINAL_IMMUTABLE`, `DIGEST_INVALID`, `OUTCOME_UNSUPPORTED`, `DIGEST_MISMATCH`, `POOL_EXHAUSTED_PAUSED` (drained-pool construction) |
| `observe_source_cancel` | source_view+phase+clawback → `_invariant` | `UNKNOWN_REWARD`, `TERMINAL_IMMUTABLE` (REVERSED and CLAWBACK_CLAIM), `SOURCE_NOT_COMMITTED`, `SOURCE_VIEW_REJECTED`, `INVALID_ID` |
| `observe_krw_refund` | `krw_phase` → post-checks → `_invariant` | `UNKNOWN_REWARD`, `KRW_EFFECT_ALREADY_NOTED`, `SOURCE_NOT_COMMITTED`, `INVALID_ID` |
| `supersede` | `_approval_ids.add` + many fields → `_invariant` | `UNKNOWN_REWARD`, `ILLEGAL_TRANSITION`, `TERMINAL_IMMUTABLE` (clawback), `RULE_VERSION_UNCHANGED`, `APPROVAL_RECORD_REUSED`, `AI_APPROVAL_REJECTED`, `APPROVAL_FIELDS`, `INVALID_RULE_VERSION` |
| `reject_external` | none; journals nothing | `EXTERNAL_EXECUTION_UNSUPPORTED`, `INVALID_ID` — one case, no `_call` wrapper |
| generic `_call` | — | `IDEMPOTENCY_CONFLICT` (unstored, repeated raise), stored-rejection replay (inside `reject()`), unfingerprintable body (`amount=object()` → `INVALID_AMOUNT`, nothing stored) |

Not-applicable rows: `view`, `reward_ids`, `pool_view`, `export_journal`, `canonical_state`, `state_digest` are read-only. `restore` is a classmethod — `INVALID_JOURNAL` asserted for a non-list journal, a missing-keys entry and an unknown op, all on fresh builds. The internal `MOCK_INVARIANT` checks in `submit`/`_resend`/`_apply_outcome`/`supersede` and the `POOL_FORBIDDEN_FOR_TOKEN_SPEND` recheck in `_apply_outcome` have no deterministic caller input (their guards are established earlier) — they get fault-seam coverage instead.

## AGENTS.md §7: existing coverage

| Requirement | Existing | Status |
|---|---|---|
| Deterministic rejection codes raised | `test_reward_fsm.py::unchanged` covers most codes | partially covered: same-machine canonical/journal compare only; no control, no restore round-trip, no fault seam |
| Rejected command leaves canonical+journal unchanged vs an untouched control | none | not covered → this file's `assert_same_as` cases |
| `restore(export_journal())` cannot reproduce a post-rejection machine | `test_restore_replays_the_same_digest` (success path only) | partially covered → restore compared on both sides of every case |
| Late failure after mutation but before journal append | none for this machine | not covered → `test_fault_*` characterization cases |

## Class A / B / C

- Class A (contract-defined, matched): none for the atomicity property itself — no contract document states a reward-side rejection clause. `BOOKING_RESALE_ADMISSION_GATES.md` §9.4 covers the reservation machine only. Every deterministic rejection case still passed: all 79 `*_leaves_no_trace` cases leave `state_digest`, `canonical_state`, `export_journal` and the restore round trip identical to the control.
- Class B (contract does not define; observed characterizations):
  - Umbrella: reward-side rejection atomicity is contract-undefined but implemented (all 79 deterministic cases hold; a stored rejection under the caller's key is the only allowed trace).
  - `test_fault_*_late_rejection_leaves_unapplied_mutation` (10 cases): `RewardMachine` mutates before `_invariant` and has no rollback wrapper, so a `MOCK_INVARIANT` fault at that seam leaves the mutation applied but unjournaled — journal still equal to control, canonical/digest divergent, `restore(export_journal())` equal to the control, and a later op diverging permanently (e.g., re-`observe` → `REWARD_ALREADY_OBSERVED`, retry `hold` → `ILLEGAL_TRANSITION`, resubmit on a second reward with the same approval record → `APPROVAL_RECORD_REUSED`, resend → `resend_count` off by one). Minimal reproduction: any `test_fault_` case.
  - `test_fault_pool_*_spend_leaves_unapplied_mutation` (2 cases): a fault at `PoolLedger._conserve` inside `spend` leaves the pool balance moved and the spend recorded with no journal entry and no reward mutation; the unjournaled spend is repeatable by a later command, so the machine and its restore diverge in `pool_view`.
  - `test_restore_forgets_stored_rejections`: `_idempotency` is outside `canonical_state` and stored rejections are not journaled; after `restore`, the same key under different canonical args re-executes to acceptance instead of `IDEMPOTENCY_CONFLICT`.
  - `test_submit_resend_does_not_consume_the_approval_record`: the resend path never adds `approval.record_id` to `_approval_ids` — the same record is accepted on two consecutive resends (the first-submit path would raise `APPROVAL_RECORD_REUSED`).
- Class C: none found. No deterministic rejection diverged, and no written contract clause was found that the observed behavior violates; the merge path is not stopped.

## Commands run and results

| Command | Result |
|---|---|
| `git status`; `git rev-parse HEAD` | clean tree; HEAD `154e9aa…` |
| `git hash-object` on the two locked files (before and after) | match the required blobs |
| `git rev-parse HEAD:reference/v0.3-rc1` (before and after) | `a6ecb12…` both times |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_reward_rejection_atomicity` (in `reference/token_reward`) | 95 tests OK |
| `unittest discover` for `settlement_f01_f03`, `booking_resale_admission`, `credit_advance_f04`, `ai_delegation`, `token_reward` | 48 / 155 / 48 / 70 / 156 tests OK |
| `python3 -m unittest integration_gate.test_http_gate readiness.test_faults` | 78 tests OK |
| `check_openapi_contract.py`, `check_integration_gate_openapi.py`, each plain and `--self-test` | exit 0 for all 4 runs |
| `check_status_register.py`, `check_rs_profile_traceability.py`, `check_read_model_source_map.py`, `check_docs_index.py`, `check_i12_proof_ids.py`, `check_delegation_layer_matrix.py`, `check_rs_predicate_evidence_map.py`, `check_rs_im_evidence_map.py`, `check_tl_predicate_evidence_map.py`, `check_contract_error_codes.py`, `check_adapter_identity_map.py`, `check_v5_transition_evidence_map.py`, each plain and `--self-test` | exit 0 for all 24 runs |
| `verify_runtime_architecture.py`; `test_runtime_architecture.py` | exit 0; 7 tests OK |
| `check_sdk_client.py` | NOT_RUN as a pass signal: local toolchain mismatch, `node 20.19.2` vs `toolchains.json` nodeMajor 24; identical failure on the clean tree, runs hosted |
| cargo, clippy, fmt | NOT_RUN: nothing under `runtime/` changed; they run hosted |
| npm SDK conformance/verify-compat | NOT_RUN: no `sdk` path change and local node is 20.19.2 vs required 24; runs hosted |
| exact-head KTX and KIX CI | NOT_RUN locally: belongs to the PR head per §10 |

Local python is 3.13.5; the workflow pins 3.12. The new module uses no 3.13-only constructs (same syntax as the existing suite).

## Non-claims

No real payout, PG, bank, KYC, chain, or public-endpoint call; `MOCK_TOKEN_REWARD_ONLY` provenance and the `ALWAYS_FALSE` flags are untouched. The `_invariant`/`_conserve` faults are `unittest.mock` injections inside test code — they do not claim that a real `MOCK_INVARIANT` can be reached by caller input. `canonical_state`/`state_digest` equality is an in-process comparison, not durability or chain finality. The class B rows are recorded characterizations, not proposed contract text; no contract semantics were invented and no non-test source was edited.

## Remaining uncertainty / follow-up candidates

- Whether the unapplied-mutation seam should gain a rollback wrapper (the `test_adopt_issued_atomicity.py` fix precedent added one to the reservation path in #219) is a contract/design question outside this node: an `_atomic` wrapper for `RewardMachine` would be a non-test source change requiring its own authorization.
- `docs/status/CURRENT_CAPABILITY_REGISTER.md` TL-3-offchain row and `docs/status/TL_PREDICATE_EVIDENCE_MAP.md` do not name this file; a later sync node owns pointer updates (same precedent as #219).
- `MOCK_INVARIANT`/`_conserve`/`_invariant` fault reachability in production terms is out of scope; in this mock the seam can only be reached by injection.
