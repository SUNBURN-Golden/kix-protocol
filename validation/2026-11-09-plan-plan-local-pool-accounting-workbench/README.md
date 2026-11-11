# Synthetic pool accounting workbench — builder evidence

Node `plan-plan-local-pool-accounting-workbench`; source is the supervisor's node
and design text supplied in this session, with no issue and no corresponding
`docs/tasks/` document. Dependencies: `tl-3-offchain`, `tl-4`; audit floor A2.
This is source-informed builder evidence, not an independent review or approval.

Task branch `agent/kix-plan-plan-local-pool-accounting-workbench` and cached
`origin/main` both started at `9ad388b2cf04a8eadc820e28e6098371e2accf5b`.
The supervisor expressly forbids network/GitHub operations, so mandatory fetch
was NOT_RUN; remote freshness and a remote base delta are unverified. No branch
or history change was made. Implementation is uncommitted in this worktree;
there is no final implementation commit, exact final task head, or merge SHA.

[Coverage mapped before tests](coverage.md) identifies existing model coverage
and interface gaps. New tests in `test_pool_session.py`, `test_pool_cli.py` and
`test_pool_console.py` cover parity/ref repetition, constructor and method counts,
ordinary domain refusal atomicity, detached results, input shape and exact integer
handling, real process journeys, literal confirmations and terminal failure
fencing. Model-internal view calls are distinguished from selected session reads.

The interface wraps the unchanged `PoolLedger`. It does not construct a
RewardMachine. The existing `reward_fixture` imports reward code transitively;
only its pure JSON helpers are used. Its RewardSession-producing loader is never
called. No model, FSM, contract, protocol command, OpenAPI, runtime settings, CI,
`.aiops/`, task document or protected reference code is edited.

Pool balances, funding policy and approval values remain **UNDETERMINED —
Astra/User**. Accounting and legal treatment remain **UNDETERMINED —
User/designated advisers**. Fixture numbers are explicit demonstration inputs,
not selected policy values. Repeated source/program refs append again on accepted
calls; there are no deduplication keys or receipt semantics. All seven model
execution/finality/durability/legal flags remain false in interface envelopes.

## Actual local evidence

The machine-readable [command ledger](commands.jsonl) records executed validation
commands, actual exit codes, elapsed seconds and corresponding logs. The final
command table, transcripts and preservation report accompany this record.
Commands use `PYTHONDONTWRITEBYTECODE=1`; Rust checks use `--offline` and `--locked`
to honor the no-network instruction. Logs with unavailable tools/dependencies
must not be interpreted as passes.

## Limits and delivery gates

No contract violation has been found in this workbench scope. Repeated-reference
append behavior is an existing model characterization, not an idempotency
contract. Output failure after an accepted mutation leaves that process's ledger
changed and terminates without retry; it promises no rollback. Ordinary domain
rejection tests do not cover injected model-invariant failures or crash recovery.

No persistence, external service, real funds/provider/KYC calls, bank execution,
chain query/deployment, issuance, production runtime, policy/legal conclusion or
production readiness is tested or claimed. Unrelated Move/ZK/localnet CI stages
are not run. Local checks do not replace exact-head hosted CI.

Non-author A2 review at the supervisor's eventual exact final head is pending.
KTX kernel verification and KIX protocol verification run IDs/status/conclusions:
NOT_RUN / unavailable in this no-publication, no-network session. Main/push CI
and post-merge blob verification: not applicable; no merge. No merge-ready claim.
Supervisor owns commit/publication and remaining gates. No issues, PRs, comments,
markers, tags, commits or pushes were created by the builder.

## Results and deviations

- Existing narrow model/TL-4 coverage: 16 tests passed.
- Final focused workbench coverage: 28 tests passed (the earlier 26-test run also passed).
- Full token-reward discovery: 316 tests passed in the final run. The first full
  run failed one existing `RewardConsoleSubprocessTests.test_source_incomplete_no_dispatch`
  subcase at its 10-second harness deadline. The unchanged test passed alone;
  unchanged full discovery then passed. Root cause of the earlier timeout is not
  established; its failure log is retained, and no timeout or existing test was modified.
- Seven applicable offline checker scripts passed both normal and `--self-test`
  modes: docs index, TL predicate evidence map, Class B index, CI checker wiring,
  CI test discovery, OpenAPI contract and integration-gate OpenAPI. These are the
  applicable document/discovery/contract checks from `protocol.yml`.
- Architecture verification passed and all seven architecture regression tests passed.
- Rust formatting passed. Kernel tests, workspace tests and workspace Clippy each
  exited 101 before compilation because `bcs` was unavailable offline. The cache
  diagnostic found 7 of 18 locked registry archives present, 11 absent. These
  checks are **unavailable, not passing**. Rust paths are unchanged. No online
  dependency acquisition or CI modification was attempted under the supervisor's
  no-network boundary; cache provisioning/re-execution belongs to the supervisor.
- All four real subprocess transcripts have empty stderr. Journey exits are 0;
  boundary exits are the expected 1 after three obligation refusals and a shortfall.
  The boundary console also declines a proposed credit before the refusals.
- No design/implementation deviation was needed. Fetch was intentionally omitted
  under the later explicit supervisor instruction; no current-remote-main claim.

[Full command → result table](command-results.md), [raw ledger](commands.jsonl),
[complete changed paths](changed-paths.txt), [preservation report](preservation.json),
[pre-edit inventory](before-sha256.json), [post-edit inventory](after-sha256.json)
and [read-only preservation checker](verify_preservation.py) are the evidence.
The inventory compares all 2,260 original tracked file contents. Only
`docs/README.md` and `reference/token_reward/README.md` changed among those files;
new implementation/tests/fixtures/evidence are listed separately in changed paths.

| Protected input | Before Git blob | After Git blob |
|---|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` | `b607996c83a119c349f1cc90469ac1ba82764e20` |
| `reference/v0.3-rc1/**` | 108 tracked paths in before inventory | All 108 byte-identical |

| Real transcript | Input fixture | stdout | stderr | Exit |
|---|---|---|---|---|
| CLI journey | `pool_journey.jsonl` | [captured](pool-cli-journey.stdout) | [captured](pool-cli-journey.stderr) | [0](pool-cli-journey.exit) |
| CLI boundaries | `pool_boundaries.jsonl` | [captured](pool-cli-boundaries.stdout) | [captured](pool-cli-boundaries.stderr) | [1](pool-cli-boundaries.exit) |
| Guided journey | `pool_console_journey.txt` | [captured](pool-console-journey.stdout) | [captured](pool-console-journey.stderr) | [0](pool-console-journey.exit) |
| Guided boundaries | `pool_console_boundaries.txt` | [captured](pool-console-boundaries.stdout) | [captured](pool-console-boundaries.stderr) | [1](pool-console-boundaries.exit) |

Builder handoff is complete for this bounded node. Remaining uncertainty is the
unverified remote freshness, the prior test timeout, unavailable offline Rust
execution, and pending independent exact-head review/hosted CI. The supervisor's
future commit must receive its own required checks; none are inferred here.
