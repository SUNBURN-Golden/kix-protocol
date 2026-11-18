# plan-local-reward-guided-init — builder evidence

Task input: the supervisor-supplied node and read-only design in this session;
there is no issue or current task document under `docs/tasks/`. Node is a
loop proposal outside `.aiops/program.json`; this is not ASTRA program mode.
Branch: `agent/kix-plan-local-reward-guided-init`.
Observed local `origin/main`, task base and starting HEAD:
`93fbedd8741c51da43d95f2d1515e15cb3124571` (no local delta).
The supervisor prohibits network/GitHub actions and commits, so no fetch was run;
freshness against remote main is unverified. Implementation and final commit
SHAs, A2 non-author exact-head review, exact-head KTX/KIX run IDs/status/conclusion
and post-merge evidence are unavailable, reserved for the supervisor. No merge.
Local results do not establish merge readiness or transfer CI from the base.

The node adds fixture-free, explicitly confirmed five-pool synthetic opening
inputs, one stdin initialization record and a complete accepted-input startup
acknowledgement. The operational session belongs to one child. Disposable
parent-side constructor validation performs no operations. All existing business
selectors and envelopes remain unchanged; `initialize` is startup-only.

## Coverage inspected before adding tests

All coverage here is source-informed builder evidence, not independent review.
Paths below are relative to `reference/token_reward/`.

| Requirement | Previous coverage and classification | Added evidence/gap addressed |
|---|---|---|
| Explicit opening balances, session isolation | Sufficient domain coverage: `test_reward_session.py::RewardSessionTests.test_no_implicit_opening_balances_and_sessions_are_isolated`; partial transport coverage in `test_reward_cli.py::RewardCliTests.test_bad_stream_setup_and_io_exit_two_without_tracebacks` | `RewardInitializationCliTests.test_file_stdin_and_shared_validation_match_without_defaults` checks each missing pool, extra fields, duplicate keys, booleans, negatives, oversized and other invalid values with shared/file/stdin parity. Preflight client and console tests assert no launch. |
| Existing operation replies, effects and pool views | Partial for new startup: `test_reward_cli.py::RewardCliTests.test_every_fixture_file_stdin_and_repeat_transcripts_are_identical`; `test_reward_client.py::RewardClientTests.test_live_participation_before_eof_and_response_derived_reads`; `test_reward_console_subprocess.py::RewardConsoleSubprocessTests.test_live_console_scenario_parity` | New CLI queued-record parity across all five existing journeys; live guided/client vs file parity; explicit guided console observe/eligibility/submit/effects/view/pool_view journey with replies required before EOF. |
| Complete preview and confirmation before launch | Not covered for opening prompts; existing operation composer tests cover per-operation confirmation | `test_reward_console.py::RewardGuidedInitializationTests` covers all five prompts and confirmation EOF, invalid values, literal confirmation/declines, flushed complete preview, failed flush, interruption and option validation. |
| Binding startup acknowledgement before business requests | Not covered for reward; pool client and console startup suites inspected as transport references | `test_reward_client.py::RewardInitializationClientTests` covers absent/truncated/malformed/non-UTF-8/duplicate/missing/extra/wrong-provenance/mismatched acknowledgements, bool/float substitution, short/failed writes, flush/read failure and interruption. Assert initialization bytes only, permanent fencing, reaping and retained cause/phase. |
| Detached input and acknowledgement, one owned child | Partial: existing client request snapshot and cleanup tests | New launch snapshot and returned acknowledgement mutation tests; fixed argv/one Popen assertion. New startup failure reaping checks reuse the existing cleanup path and existing owned-child terminate/kill coverage. |
| No new operation selector; zero/max boundary values | Existing selector and model tests sufficient underneath, partial for stdin | New framing/mode/rejected-initialize tests and 0/`MONEY_MAX` round trips. |
| False execution/finality/durability flags | Sufficient existing `ALWAYS_FALSE_FLAGS` assertions in CLI/client/console parity suites | Reused in guided live parity; no new economic/FSM semantics. |
| Existing offline coverage and protected bytes | Existing workflow definitions inspected (`ktx-kernel.yml`, `protocol.yml`) | Focused suite first, full directory and applicable offline checks; protected membership/hashes compared before/after. |

## Commands and results

Actual verification commands, exit codes and durations are in [commands.json](commands.json),
with complete combined stdout/stderr in the corresponding `check-*.log` files.
Every recorded Python subprocess uses `PYTHONDONTWRITEBYTECODE=1`; Python is
3.12.15. Rust tooling reports cargo 1.98.1. No long job was launched in the
background. The full actual command-to-result table and captured transcripts follow below.

## Preservation and scope

Before work, direct `git hash-object` returned the required locked blobs:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`

[protected-before.json](protected-before.json) captures SHA-256 for all 110 files
in the protected reference tree plus both locks, including membership. The final
[protected-after.json](protected-after.json) is identical in membership and hashes.
Both required Git blobs also match after work; see [check-30.log](check-30.log).
No `.aiops/`, task documents, CI, model/FSM/session semantics or authoritative
contracts are edited.

No contract violation found; no new contract-undefined characterization is
introduced. Existing Class B uncertainties in the reward README remain, including
late injected failure rollback limits, UNKNOWN resend approval consumption,
approval normalization/restoration fingerprint and noncanonical effect IDs.
No funding, token issuance, real PG/bank/KYC, public endpoint, Sui, money, secrets,
new protocol command, production runtime, storage engine, settlement connection
or shared PoolSession accounting. No persistence/finality/authentication or
independent verification claim. Amounts, budgets, caps, durations and approval
policy remain UNDETERMINED — Astra/User. Startup only proves local input agreement.

## Deviations and remaining gates

- No fetch: explicit supervisor network prohibition overrides session-start fetch.
- No task issue/document exists: the supplied node/design is the immutable task input.
- Protected tree, workflows and policy pins stay unchanged. No CI was edited.
- No commit, push, PR, issue or comment; supervisor owns git/GitHub publication.
- Offline equivalents replace network-dependent CI for this local node. Hosted
  exact-head KTX/KIX results, A2 review and all merge decisions remain external gates.
- Product response timeouts are intentionally absent, preserving blocking reads.
  Startup silence while stdout remains open requires caller interruption; EOF is
  detected as uncertainty. There is no automatic retry/restart.

## Final local verification results

Focused reward tests: **226 passed**. Complete `reference/token_reward` discovery:
**397 passed**. Eight selected offline checkers and their self-tests pass; the
architecture verifier, seven architecture tests and Rust formatting also pass.
No product/test fix was needed after the first focused run.

Four Cargo test/Clippy commands are **blocked before compilation**, exit 101:
the offline index cannot resolve `bcs` for workspace member `kix-bcs1`.
The cache preflight reports 7/18 archives present and 11 missing (exit 1 with
`--require`). No dependency download, cache repair, dependency/CI change or
retry without `--offline` was attempted. These are environment-blocked broad
Rust checks on unchanged paths, never reported as passes. A prepared offline
Cargo cache is needed for supervisor verification. No product policy decision
or prohibited implementation was needed for this node.

The checked Python code was complete before both test runs. Later changes
only document results and add evidence artifacts. The unchanged Git HEAD is
`93fbedd8741c51da43d95f2d1515e15cb3124571`; tests cover the uncommitted worktree,
not an implementation commit carrying that SHA. Exact implementation/final
commit and CI evidence must be established after supervisor publication.

| Actual command | Result | Full output |
|---|---|---|
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_reward*.py` | PASS (exit 0); 226 tests | [check-01.log](check-01.log) |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS (exit 0); 397 tests | [check-02.log](check-02.log) |
| `python3.12 scripts/check_docs_index.py` | PASS (exit 0) | [check-03.log](check-03.log) |
| `python3.12 scripts/check_docs_index.py` | PASS (exit 0) | [check-04.log](check-04.log) |
| `python3.12 scripts/check_docs_index.py --self-test` | PASS (exit 0) | [check-05.log](check-05.log) |
| `python3.12 scripts/check_status_register.py` | PASS (exit 0) | [check-06.log](check-06.log) |
| `python3.12 scripts/check_status_register.py --self-test` | PASS (exit 0) | [check-07.log](check-07.log) |
| `python3.12 scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0) | [check-08.log](check-08.log) |
| `python3.12 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0) | [check-09.log](check-09.log) |
| `python3.12 scripts/check_class_b_index.py` | PASS (exit 0) | [check-10.log](check-10.log) |
| `python3.12 scripts/check_class_b_index.py --self-test` | PASS (exit 0) | [check-11.log](check-11.log) |
| `python3.12 scripts/check_ci_test_discovery.py` | PASS (exit 0) | [check-12.log](check-12.log) |
| `python3.12 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0) | [check-13.log](check-13.log) |
| `python3.12 scripts/check_ci_checker_wiring.py` | PASS (exit 0) | [check-14.log](check-14.log) |
| `python3.12 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0) | [check-15.log](check-15.log) |
| `python3.12 scripts/check_openapi_contract.py` | PASS (exit 0) | [check-16.log](check-16.log) |
| `python3.12 scripts/check_openapi_contract.py --self-test` | PASS (exit 0) | [check-17.log](check-17.log) |
| `python3.12 scripts/check_integration_gate_openapi.py` | PASS (exit 0) | [check-18.log](check-18.log) |
| `python3.12 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0) | [check-19.log](check-19.log) |
| `python3.12 scripts/verify_runtime_architecture.py` | PASS (exit 0) | [check-20.log](check-20.log) |
| `python3.12 scripts/test_runtime_architecture.py` | PASS (exit 0); 7 tests | [check-21.log](check-21.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) | [check-22.log](check-22.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | BLOCKED (exit 101); offline Cargo cache incomplete | [check-23.log](check-23.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | BLOCKED (exit 101); offline Cargo cache incomplete | [check-24.log](check-24.log) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | BLOCKED (exit 101); offline Cargo cache incomplete | [check-25.log](check-25.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | BLOCKED (exit 101); offline Cargo cache incomplete | [check-26.log](check-26.log) |
| `python3.12 scripts/check_cargo_offline_cache.py --require` | BLOCKED (exit 1); offline Cargo cache incomplete | [check-27.log](check-27.log) |
| `bash validation/2026-11-10-plan-local-reward-guided-init/guided-heredoc.sh` | PASS (exit 0) | [check-28.log](check-28.log) |
| `bash validation/2026-11-10-plan-local-reward-guided-init/file-mode.sh` | PASS (exit 0) | [check-29.log](check-29.log) |
| `python3.12 validation/2026-11-10-plan-local-reward-guided-init/verify_evidence.py` | PASS (exit 0) | [check-30.log](check-30.log) |
| `git diff --check` | PASS (exit 0) | [check-31.log](check-31.log) |
| `python3.12 scripts/check_docs_index.py` | PASS (exit 0); final evidence documentation | [check-32.log](check-32.log) |
| `git diff --check` | PASS (exit 0); final evidence documentation | [check-33.log](check-33.log) |

## Real subprocess captures

- [Guided here-document input](guided-heredoc.sh) starts with five explicitly
  entered balances and literal SUBMIT, with no initialization fixture-file read.
  [Raw guided stdout/stderr](check-28.log), exit 0.
- [Equivalent fixture-mode command](file-mode.sh) and [raw output](check-29.log),
  exit 0, use the unchanged source/approval journey.
- [Offline evidence comparison](verify_evidence.py), [actual result](check-30.log):
  all 11 complete business replies match, including historical duplicate receipts,
  explicit ISSUED reward view and one-spend final pool view. Seven false flags
  remain false. Startup preview and acknowledgement bind the complete input.
- The incremental subprocess test requires each operation reply before yielding
  the next input and before stdin EOF. The capture above provides replayable raw
  evidence; it does not itself prove an interactive timing bound.

## Changed paths and final state

[Complete changed-path list](changed-paths.txt) includes all code, tests,
documentation, transcript inputs, command logs and evidence files. Product paths:
`reward_fixture.py`, `reward_cli.py`, `reward_client.py`, `reward_console.py`,
their four existing test modules, `fixtures/reward_console_opening_journey.txt`,
`reference/token_reward/README.md` and `docs/README.md`.

Local implementation is ready for supervisor review with the Cargo cache
limitation above. This is not merge-ready: A2 non-author exact-final-head review,
completed/success KTX and KIX CI, and user merge authorization remain separate.
No merge/post-merge checks apply to this uncommitted, unpublished builder result.
