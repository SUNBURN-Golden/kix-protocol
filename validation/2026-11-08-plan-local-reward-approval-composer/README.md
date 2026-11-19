# Reward identity and synthetic approval composer — builder evidence

Node/task ID: `plan-local-reward-approval-composer`. Task document: the supervisor's
supplied node objective, acceptance criteria and read-only design plan in this
session; no issue or `docs/tasks/` file exists for this loop-proposed node. This
is not ASTRA program mode. Dependency `plan-plan-local-reward-live-console` is
present in the observed base. Audit floor A2; Astra gate none.

Observed local `origin/main`, task base and initial/current uncommitted HEAD:
`3fa90881c1803a76f72ad1e0a9052862ddf655e2`, branch
`agent/kix-plan-local-reward-approval-composer`. They match. `git fetch origin main`
is NOT_RUN because the supervisor explicitly forbids network/GitHub actions.
Remote freshness is unverified. Implementation and final task commit SHAs are
unavailable: the supervisor owns commits/publication. No merge commit exists.

This changes optional console input composition only. Both object prompts accept
raw JSON or literal `:guided`. Composers collect caller values without session or
client access; existing shape/JSON validation, canonical preview, confirmation,
RewardClient and reward operations are reused. No approval, actor, evidence or
outcome is inferred. Amounts, caps, budgets, durations and approval policy remain
**UNDETERMINED — Astra/User**. Actual approvers remain User-owned; E-1 remains open.

## Coverage mapping (existing coverage inspected before new tests)

Paths in this table are relative to `reference/token_reward/`. New composition
checks share the existing harnesses through `GuidedCompositionTests` in
`test_reward_console.py`, inherited by both console test classes. Tests remain
source-informed, not clean-room or non-author review.

| Requirement | Existing coverage classification and reuse | New gap coverage |
|---|---|---|
| Raw input and all twelve selectors | Sufficient: `test_reward_console.py::test_success_transcript`, `test_other_selectors_and_explicit_unknown_resolution`, syntax/error tests | Raw behavior retained; no new economic oracle |
| Guided/raw envelopes and results in both modes, mixed input, supersede | Partial: `test_reward_console_subprocess.py::test_live_console_scenario_parity` covers raw mode | `test_guided_raw_envelope_parity` uses existing participation, UNKNOWN and supersede vectors; matches complete proposals and desk envelopes against raw input in both harnesses; live wrapper captures actual JSONL writes |
| Observe, explicit eligibility, synthetic submit, separately entered outcome | Partial: existing journey is raw | `test_live_console_journey_before_eof` now uses guided objects; next selection is generated after previous reply with stdin still open; one child, historical duplicate receipt, one spend, explicit ISSUED read |
| Opaque IDs, Unicode, duplicate/ordered evidence, precision, optional omission | Partial: existing optional tests cover raw | `test_guided_opaque_values_precision_and_prior_record`: accepted Unicode/delimiter identity journey, ordered duplicate evidence, absent/null/string prior record, >2**53 integer reaches child unchanged even though the FSM refuses it; empty evidence, blank/AI actor, whitespace-bearing key/approval ID and negative generation are caller values with domain refusals |
| Decline, malformed structure and EOF send nothing | Partial: raw syntax/EOF/confirmation tests | `test_guided_decline_invalid_and_eof_no_dispatch`: each new prompt and confirmation cut off for observe/submit/supersede including included prior record; wrong integer types/counts/inclusion choices, lone surrogates, no calls and no child writes; decline proposes but sends nothing |
| Confirm once, preview before sending | Sufficient raw confirmation tests | Existing `test_proposal_is_complete_and_flushed_before_confirmation` uses guided input and CRLF; live wrapper checks proposal/flush before every confirmed child write |
| Duplicate receipt, UNKNOWN fencing/no retry, false flags | Sufficient: success/scenario tests and client/console transport-fault tests | Guided replay/UNKNOWN vectors reuse those semantics and both parity helpers check all seven false flags; unchanged transport-fault tests remain in full suite |
| Replayable examples, local checks | Partial: raw fixtures/transcripts | Two guided fixtures; `test_guided_fixture_transcripts` in both harnesses and extended `test_cli_transcripts_match_default_in_process`; four fresh captured CLI runs |

## Changed paths

- `reference/token_reward/reward_console.py`
- `reference/token_reward/test_reward_console.py`
- `reference/token_reward/test_reward_console_subprocess.py`
- `reference/token_reward/fixtures/reward_console_guided_journey.txt`
- `reference/token_reward/fixtures/reward_console_guided_boundaries.txt`
- `reference/token_reward/README.md`
- `docs/README.md`
- `validation/2026-11-08-plan-local-reward-approval-composer/` (this record,
  command results and stdout/stderr, protected-file manifests).

An exact expanded changed-path list is retained in `changed-paths.txt` after
verification. No FSM, model, client, CLI, session, authoritative contract, grade,
CI, `.aiops/`, task input or protected path is changed.

## Preservation

`preservation-before.json` records Git blobs and SHA-256 bytes for both locked
kernel files and all 108 files in `reference/v0.3-rc1/**`. The two kernel blobs
match `69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20` before editing.
`preservation-after.json` matches all 110 entries and their membership.
`check_preservation.py` and its captured output also verify the protected-path
Git diff is empty (including `.aiops/`, task inputs, contracts and the unchanged
reward desk/client files). Both required blobs match after work.
No protected file was edited, even transiently.

## Actual verification

`commands.json` records each validation command's argv, cwd, environment,
exit status, duration and captured stdout/stderr files, including development
runs. Commands use workflow-equivalent Python 3.12 and the installed pinned
Rust 1.98.1. Python bytecode writes are disabled; Cargo stays offline. Commands
run in the foreground; no background long jobs or network bootstrapping.

| Command (from repository root) | Actual result |
|---|---|
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward -p 'test_reward_console*.py'` | Initial development run: exit 0, 35 tests; completed version: exit 0, 37 tests |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0, 236 tests passed |
| `python3.12 scripts/check_docs_index.py` and `--self-test` | both exit 0; scanned=374, indexed=339, allowlisted=35 |
| `python3.12 scripts/check_status_register.py` and `--self-test` | both exit 0 |
| `python3.12 scripts/check_tl_predicate_evidence_map.py` and `--self-test` | both exit 0; 49 rows unchanged |
| `python3.12 scripts/check_class_b_index.py` and `--self-test` | both exit 0; textual index only |
| `python3.12 scripts/check_ci_test_discovery.py` and `--self-test` | both exit 0; all 14 token_reward test files reached by workflow discovery |
| `python3.12 scripts/check_ci_checker_wiring.py` and `--self-test` | both exit 0 |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test` | both exit 0; 84-command pin unchanged |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | both exit 0; productionEndpoint/publicHost false |
| `python3.12 scripts/verify_runtime_architecture.py` | exit 0; architecture/dependency boundaries accepted; no durability/performance certification |
| `python3.12 scripts/test_runtime_architecture.py` | exit 0, 7 tests passed |
| `python3.12 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode in-process < reference/token_reward/fixtures/reward_console_guided_journey.txt` | expected exit 0; stdout captured, empty stderr |
| Same command with `reward_console_guided_boundaries.txt` stdin | expected exit 1; three input errors and one decline dispatch nothing; five confirmed domain refusals and explicit reads retained |
| `python3.12 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_guided_journey.txt` | expected exit 0; stdout captured, empty stderr, byte-identical to in-process mode |
| Same subprocess command with `reward_console_guided_boundaries.txt` stdin | expected exit 1; stdout captured, empty stderr, byte-identical to in-process mode |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; missing offline `bcs`; test execution unavailable |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; same dependency resolution failure; lint unavailable |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 101; same dependency resolution failure; tests unavailable |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 101; same dependency resolution failure; lint unavailable |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `python3.12 validation/2026-11-08-plan-local-reward-approval-composer/check_preservation.py` | exit 0; 110 protected files match before/after; required blobs match; protected diff/additions empty; captured mode outputs match |
| Environment probe (complete argv in `commands.json`) | Python 3.12.15; Cargo/Rust toolchain 1.98.1; HEAD and local origin/main unchanged |
| `git diff --check` | exit 0 |

The initial 35-test narrow run passed before the fixture-focused test was added
for both harnesses and the accepted opaque-identity vectors were strengthened.
The completed narrow suite passed 37 tests, followed by the full 236-test suite.
A final whitespace-bearing reward-key forwarding vector was then added to the
existing composition test; narrow and full discovery were rerun on the delivered
version (37/236 tests respectively).
No failed Python test run occurred or was discarded.

Fresh guided captures are `in-process-journey.stdout.txt`,
`in-process-boundaries.stdout.txt`, `subprocess-journey.stdout.txt` and
`subprocess-boundaries.stdout.txt`, with empty matching stderr files. All four
invocations are recorded individually with full argv/stdin paths. The journey
separately enters observe, hold, eligibility, synthetic submit, effects, replays
and explicit reads. The boundary fixture demonstrates malformed generation,
negative evidence count, invalid included prior record, a declined whitespace-
bearing key, then the existing open-window, forbidden-pool and AI refusals.

The four Rust test/Clippy commands are **unavailable checks, not passes**; each
stops in dependency resolution before tests/lint execute. The supervisor's
no-network restriction prevents dependency bootstrapping, and no Rust code was
changed. This remains a verification limitation for the supervisor/CI with a
complete cache. No automatic retry or download was attempted. Unrelated Move,
Sui/localnet, ZK, SDK, storage and production jobs were not run.

`delivery-files.sha256` anchors the seven delivered source/test/fixture/doc files
outside the validation directory while the supervisor establishes a commit SHA.

## Contract findings, limits and outstanding gates

No explicit contract violation found. Existing Class B approval normalization
(`prior_record=None` inside the FSM), restoration fingerprint, late-fault
mutation, UNKNOWN approval consumption and non-canonical effect observations
remain unchanged; see the reward guide's Synthetic limitations and Class B.
No new contract-undefined semantic claim is introduced by the composer.

All seven external-effect flags remain false. Synthetic approvals provide no
signature, credential, authentication or real human authority. No source adapter,
settlement coupling, issuance, funds, PG/bank/KYC, sockets/public endpoints,
chain/testnet/mainnet, persistent storage, replication, new protocol command,
coin/TIX module or production runtime. These checks do not establish production
readiness, durability, bank exactly-once, distributed fencing, legal compliance
or chain finality. No capability grade or policy value changes.

A2 non-author exact-final-head review and completed/success exact-head **KTX kernel
verification** and **KIX protocol verification** remain supervisor gates. CI run
IDs/status/conclusions and post-merge CI are unavailable/not run: there is no
committed delivery head or network action in this session. No earlier CI is
transferred; this is local builder delivery, not merge readiness or approval.
User controls draft readiness and merge authorization outside this session.

Deviations: startup fetch/publication replaced by the supervisor's explicit
no-network/no-publication instruction; task input is the supplied node, not a
manufactured issue or task file. New assertions share a mixin to run the same
composition predicates through both existing harnesses, rather than duplicating
the tests. The existing live incremental test now uses guided objects, while raw
journey and CLI coverage is retained. The offline cache lacks `bcs`, so Rust tests/Clippy could not execute; this
limitation is retained for supervisor verification rather than treated as a pass.
No scope expansion or product decision.
