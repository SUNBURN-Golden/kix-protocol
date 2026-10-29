# Malformed readiness wrapper journal rejection characterizations

Node: `plan-readiness-wrap-restore-rejections`; issue: none. Task document:
the user-supplied node specification and read-only design plan in the builder
prompt; no corresponding task file under `docs/tasks/`. Source: planner run
`1793230233`, loop-proposed node outside `.aiops/program.json`. Dependencies:
`readiness-extensions`, `plan-plan-token-reward-readiness-wrap`,
`plan-plan-restore-fingerprint-equivalence`. Audit floor A2; Astra gate none;
not ASTRA program mode. Execution date: 2026-10-29.

Builder-authored, source-informed local evidence. No independent A2 review,
acceptance or evidence-grade increase is claimed.

## Source state and publication boundary

Branch: `agent/kix-plan-readiness-wrap-restore-rejections`. Initial task HEAD
and cached `origin/main` both equal
`472f3c6676dcfa706f53ba8f91cfd6152001000c`; initial worktree clean. No delta
between those local refs. `git fetch origin main` NOT_RUN: the explicit
supervisor rule prohibits all network/GitHub actions. Remote-main freshness
is unverified. No rebase or merge was performed.

Implementation/final task commit SHA: unassigned; this is an uncommitted
worktree patch and the supervisor owns commit/publication. The unchanged
branch HEAD identifies the inspected base, not a committed implementation.
No commit, push, PR, issue, comment, tag, branch mutation or merge performed.
Merge SHA and post-merge CI: not applicable. Exact-head KTX kernel verification
and KIX protocol verification run IDs/status/conclusions: unavailable,
unverified; no hosted workflow queried or invoked. Local PASS is readiness
for supervisor handoff only, not merge readiness.

## Coverage mapped before implementation (AGENTS §7)

The complete fixture/error matrix is in
[readiness/CONFORMANCE.md](../../readiness/CONFORMANCE.md#malformed-wrapper-journal-restoration).
All new methods below are on `readiness.test_faults.WrapperRestoreRejectionTests`.

| Requirement | Existing evidence | Prior classification / addition |
|---|---|---|
| Valid reward recovery | `RewardWrapTests.test_reward_restore_round_trips_canonical_state_and_digest` in `readiness/test_faults.py` | Sufficient; retained unchanged |
| Valid AI recovery and execution off | `ExtensionTests.test_ai_delegation_torn_revoke_replays_once_and_execution_stays_off`, `test_ai_delegation_crash_before_issue_does_not_create_the_grant` | Sufficient; retained unchanged |
| Crash-prefix and resend journeys | `CrashPointSweepTests.test_crash_point_sweep_ai_delegation`, `test_crash_point_sweep_reward` | Sufficient; retained unchanged |
| Open once / replay after restart | `readiness/conformance.py::BackendConformance.test_ai_delegation_registry_opens_once_and_issue_replays_across_restart`, `test_reward_open_observe_and_hold_replay_across_restart` | Sufficient live coverage; malformed restore partial → `test_repeated_open` |
| Fingerprint recovery | `reference/ai_delegation/test_restore_fingerprint_equivalence.py` (AI wrapper), `reference/token_reward/test_restore_fingerprint_equivalence.py` (reward FSM) | Sufficient valid fingerprint controls; inner reward journals/errors do not cover wrapper restore |
| Non-list journals | No direct wrapper tests | Not covered → `test_non_list_journals` |
| Malformed entries and op fields | No direct wrapper tests | Not covered → `test_malformed_entries_and_ops` |
| Unknown/public non-replay operations | No direct wrapper tests | Not covered → `test_unknown_operations` |
| Missing opening fields | No direct wrapper tests | Not covered → `test_missing_open_fields` |
| Commands before opening | No direct malformed-restore tests | Not covered → `test_commands_before_open` |
| Invalid arguments | Live validation in `reference/ai_delegation/test_rejection_atomicity.py` and `reference/token_reward/test_reward_rejection_atomicity.py`; no wrapper recovery-error mapping | Partially covered → `test_invalid_arguments` |
| Export-journal equality guard | No direct wrapper tests | Not covered → `test_redundant_entries` |
| Caller input preservation for selected malformed journals | No direct tests | Not covered → shared `_assert_restore_rejected` in every rejection fixture |
| Minimal paired valid histories, empty journal, false labels | Broad recovery controls above | Partially covered → `test_valid_controls` |

## Fixtures and observed behavior

Each test builds fresh accepted AI `open_registry` + `issue_grant` and reward
`open` + `observe` histories using the existing `ai_delegation_issue`,
`_reward_opening`, `_observe_reward`, `_reward_rid` and `json_copy` helpers.
No cross-test-module fixtures, private state, patched methods, store frames or
inner reward FSM records are used. Values are synthetic, not product policy.

Selected mutations are non-list `None`, `{}`, `''`, `0`; entries `None`, `[]`,
`''`, `0`, `{}` and non-string `op` values `None`, `0`, `[]`, `{}` both alone
and after opening; unknown `unknown_operation` and public non-replay
`state_digest` operations in both positions; each missing opening field;
the command without its opening; repeated opening; missing command argument
(AI `actor`, reward `idempotency_key`), unexpected command keyword, invalid
opening value (`None`), AI zero `limits.per_action_max` / reward zero `amount`;
and a redundant accepted command or extra nested opening field.

Every selected malformed input refuses to return a wrapper. Tests require
the exact wrapper-specific `WrapError` class with `.code` equal to
`RECOVERY_DIVERGENCE`, except AI missing `humans` / `agents`, which requires
exact `KeyError` with `.args` equal to `('humans',)` / `('agents',)`.
Reward missing `opening_balances` raises its own `WrapError` with
`RECOVERY_DIVERGENCE`. Commands before open and repeated open also become
`RECOVERY_DIVERGENCE` instead of live `NOT_OPEN` / `ALREADY_OPEN`.
The wrappers define distinct error classes. No alternative error tuple or
broad `Exception` assertion is accepted.

`_assert_restore_rejected` snapshots the complete nested caller journal and
compares it in `finally`, including unexpected returns/exceptions. Redundant
command controls first call the public command again and require
`duplicate=True` and unchanged export/digest; manually appending that entry
then fails restore. Extra opening fields are ignored during replay but fail
restored export equality. Each invalid-argument fixture changes one field.

Paired untouched histories restore identical journal, canonical state and
digest and preserve caller input. Both original and restored AI grant views
keep `durable`, `execution_enabled`, `funds_executed` exactly false; reward
views keep `durable`, `token_issued`, `onchain_recorded`, `funds_executed`,
`krw_paid`, `chain_finality` exactly false and provenance exactly
`MOCK_TOKEN_REWARD_ONLY`. Empty journals restore valid unopened wrappers
with equal export/digest and unchanged input, without querying unopened
canonical state.

Classification: **B**, source-informed characterization of contract-undefined
error details and equality-guard behavior. No explicit contract violation was
found. These observations do not amend contracts or standardize exceptions.
The AI tool-check-order question remains excluded and unresolved.

## Commands actually run and results

All commands ran from repository root, in the foreground. Tests/checkers used
`PYTHONDONTWRITEBYTECODE=1`. Python: `3.13.5` (hosted workflow selects 3.12;
3.12 was not exercised here). Read-only `cat`, `sed`, `rg` inspections covered
governance, wrappers, conformance helpers, existing tests and workflow steps.

| Command | Actual result |
|---|---|
| `pwd && git status --short && git branch --show-current && git rev-parse HEAD origin/main` | Expected directory/branch; clean; both refs equal the SHA above |
| `python3 --version` | Python 3.13.5 |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` (before) | Both match required blobs below |
| `python3 -` reference SHA-256 snapshot (`Path.rglob`, `read_bytes`, `hashlib.sha256`) | 108 files fingerprinted before edits in `/tmp/kix-wrap-restore-reference-before.json` |
| `python3 -m unittest readiness.test_faults.WrapperRestoreRejectionTests -v` | PASS, exit 0: 9 tests |
| `python3 -m unittest readiness.test_faults` | PASS, exit 0: 88 tests |
| `python3 scripts/check_ci_test_discovery.py` | PASS, exit 0: reference_suites=7, node_tests=8, modules=4, excluded=3; readiness.test_faults reached by CI |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS, exit 0: 18 negative controls detected |
| `python3 scripts/check_docs_index.py` | PASS, exit 0: scanned=316, indexed=281, allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | PASS, exit 0: all seven intended negative fixtures detected |
| `git diff --check` | PASS, exit 0: no whitespace errors |
| `git diff --stat`, `git diff -- readiness/test_faults.py`, `git diff -- readiness/CONFORMANCE.md docs/README.md`, `git status --short` | Reviewed test/document diff and four-path scope, including the untracked new record |
| `python3 -` final protected-path verification using SHA-256 snapshot comparison, `git ls-files -z reference/v0.3-rc1`, `git show HEAD:<path>`, `git hash-object`, `git diff HEAD --name-only` and `git ls-files --others --exclude-standard` | PASS, exit 0: 108 reference files unchanged from before and HEAD; both required blobs match; exactly four authorized paths changed |
| `git rev-parse HEAD origin/main` (after edits) | Both remain `472f3c6676dcfa706f53ba8f91cfd6152001000c` |

All requested tests/checks passed on their first invocation; no implementation
fix or test rerun was needed. Initial read-only file discovery returned exit 1
when no task filename matched; a later inspection included two nonexistent
reference README paths. Subsequent reads located the actual task context and
source/tests. These were inspection misses, not test/check failures.

## Changed paths and protected files

- `readiness/test_faults.py`: import `AiDelegationWrap` and add the nine-method
  public-API `WrapperRestoreRejectionTests` class.
- `readiness/CONFORMANCE.md`: coverage matrix, exact class-B errors and limits.
- `validation/2026-10-29-plan-readiness-wrap-restore-rejections/README.md`: this record.
- `docs/README.md`: direct index link to this record.

Required locked blobs (verified before and after work):

| Path | Required / observed Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Final byte/path verification passed: all 108 `reference/v0.3-rc1/**` files
match the pre-edit snapshot and tracked HEAD content. Only the four listed
paths differ from HEAD (including untracked files). No production source or
protected-path changes occurred. Locked blobs on a final merge are not
applicable: no merge was performed.

## Scope, deviations and remaining uncertainty

The design plan was followed. The explicit no-network supervisor rule overrides
AGENTS §1's fetch step; only cached main is observed. There is no task document
under `docs/tasks/` for this loop-proposed node; the prompt is the immutable task
input. No new decision requirement was identified.

The closest scoped local protocol CI equivalents are `readiness.test_faults`,
discovery and docs-index checks including their self-tests. The workflow combines
readiness with `integration_gate.test_http_gate`; socket-based HTTP tests were
not required or run. No token package, backend acceptance or reference-suite run
was needed. No Rust inputs changed; architecture/kernel/Cargo tests, Clippy,
formatting and dependency jobs from `ktx-kernel.yml` were not run. Full hosted
exact-head verification remains the supervisor's later gate.

No production source, contracts, workflow, owner decision, evidence map/grade,
`.aiops/**`, `docs/tasks/**`, reference implementation or runtime change is
authorized or intended. No new command or policy value. No funds, providers,
network, sockets, Sui, credentials, equipment, paid services, production runtime
or backend/storage-engine implementation used. Existing recovery uncertainties,
policy values and open decisions remain unchanged. Error standardization or
the blocked AI tool-check-order question would require separate authorization.

No production durability, physical-media/fsync, power-loss/OS-crash, distributed
fencing, bank exactly-once, chain finality, payout, backend acceptance,
clean-room independence or complete malformed-input coverage claim follows.
