# Guided live pool initialization — builder evidence

Node: `plan-local-pool-guided-live-init`. Task input: user/supervisor-supplied node
and read-only design in this session; no issue or task document path exists.
Base, starting HEAD and cached `origin/main`:
`61e581acb3c702dafa145ab0e9e96996cc2e0be2`; local base delta: none.
Branch: `agent/kix-plan-local-pool-guided-live-init`.
Fetch NOT_RUN under the supervisor's explicit no-network instruction; remote
freshness is unverified. Single writer; supervisor owns commit/publication.

This record describes a local synthetic interface, not a production runtime.
The implementation adds a fixture-shaped stdin startup record without adding a
protocol command. File startup, default in-process use and credit/spend/view
semantics remain unchanged. All five synthetic balances require explicit entry
and literal SUBMIT after a flushed preview before launching one child. The
client validates a detached snapshot before launch and compares the complete
initialization acknowledgement against it before any ordinary request.

## Existing coverage map (inspected before adding tests)

All test paths below are under `reference/token_reward/`.

| Requirement | Existing evidence / classification | Gap addressed |
|---|---|---|
| Guided five-balance entry and confirmation | Partial: `test_pool_console.PoolConsoleTests.test_guided_opening_journey_matches_fixture`, `test_guided_opening_abort_never_constructs`, `test_guided_opening_terminal_output_failures_fence_construction_and_dispatch` | Connect confirmed guided values to one real child; no launch for input/preview failures |
| Complete envelopes, same-child credit/spend/explicit view | Partial: `test_pool_client.PoolClientTests.test_real_incremental_journeys_complete_envelopes_one_child`; fixture journeys in `test_pool_console_subprocess.py` | Run both stdin and file startup through the actual child, compare all envelopes |
| Fixture validation and constructor errors | Partial: `test_pool_session.PoolSessionTests.test_fixture_shape_and_constructor_errors_stay_separate`, `test_pool_cli.PoolCliTests.test_fixture_setup_and_io_errors_are_status_two` | Share text/file decoder and validate initialization framing before acknowledgement/dispatch |
| Startup uncertainty, exact evidence and cleanup | Partial: `test_pool_client.PoolClientTests.test_initialization_failures_reap_without_request_submission` and existing request fault/cleanup tests | Initialization write/short-write/flush/read/interruption faults; retain attempted init bytes, no retry or fallback |
| Forbidden pools, exhaustion, immutable refusal state | Sufficient semantics: `test_pool_session.PoolSessionTests.test_all_ordinary_rejections_preserve_full_snapshot_and_precedence`, `test_pool_cli.PoolCliTests.test_real_boundaries_keep_state_and_original_codes` | Reuse boundary fixtures for stdin transport parity |
| Repeated references append again | Sufficient semantics: `test_pool_session.PoolSessionTests.test_repeated_refs_match_direct_model_and_append_again` | Extend real client parity to both startup modes |
| All false execution flags | Partial boundary coverage: existing client malformed acknowledgement matrix, session/CLI metadata assertions | Apply existing matrix to stdin initialization too |

## New and extended focused evidence

| Test path / symbols | Gap closed |
|---|---|
| `test_pool_session.py`: extended fixture/constructor separation test; `test_decoder_and_file_reader_share_strict_json_rules` | Same decoder, duplicate/nonfinite/Unicode rejection; unchanged domain classification |
| `test_pool_cli.py`: `test_stdin_initialization_matches_complete_fixture_envelopes`, `test_invalid_stdin_initialization_never_acknowledges_or_dispatches`, `test_initialization_options_reject_before_consuming_stdin` | Byte-identical envelopes and exits for both startup modes; malformed startup framing, shape/version/provenance/domain input; no ack/request; option rejection before reads |
| `test_pool_client.py`: extended real journeys, repeated refs and acknowledgement failure matrix | One real child, unchanged complete envelopes, type-sensitive snapshot and every false flag; initialization bytes distinguished from request bytes |
| `test_stdin_preflight_rejects_invalid_balances_and_timeout_without_launch`, `test_stdin_initialization_uses_detached_confirmed_snapshot`, `test_initialization_transport_faults_fence_and_reap_without_retry` | No child on invalid inputs, detached prelaunch snapshot, one write/flush, terminal uncertainty with chained cause and exact bytes, reaped child and rejected subsequent use |
| `test_pool_console_subprocess.py`: guided real-child journey/CLI tests; guided prelaunch input/output matrices; extended invalid-option matrix | Confirmed initialization/credit/spend and explicit view through the same child, complete fixture parity, no launch on decline/EOF/lexical/domain failure/interruption/display failure |

Existing request fencing, concurrency rejection, cleanup escalation, postlaunch
terminal handling and output failure tests are reused without duplicating model
semantics. These are source-informed transport/interface tests, not independent
conformance proof.

## Actual verification

The [command → result table](command-results.md) and [machine ledger](commands.jsonl)
record actual commands, exit codes and adjacent output logs. All validation Python
commands set `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=reference/token_reward`.
Default Python is 3.13.5; CI-compatible Python 3.12.15 is installed. Cargo/rustc
are 1.98.1, matching the CI Rust toolchain.

The initial Python 3.13 focused run passed 69 tests (observed tool output, no
separate saved log). Python 3.12 focused runs passed 69 tests both before and
after tightening raw initialization framing to require LF (CRLF remains valid;
bare CR is rejected before universal-newline translation). No semantics or
confirmation boundary changed.

The first full Python 3.12 discovery passed all 382 tests. After the framing
change, the next full run had one failure in the unchanged
`test_reward_console_subprocess.RewardConsoleSubprocessTests.test_source_incomplete_no_dispatch`:
its observe/invalid-empty-source-field case exceeded the harness's 10-second
reply deadline. [The original failure](check-23.log) is retained. The same symptom
is recorded in the predecessor [opening composer evidence](../2026-11-09-plan-local-pool-opening-composer/README.md).
A read-only diff confirmed both reward-console test files and the reward
console/client implementation unchanged. The harness runs many real child cases
under test-only deadlines; exceeding that deadline is the observed failure, not
a proven root cause. The isolated unchanged test passed (one test, [output](check-33.log)).
No unrelated harness or runtime code was changed. The final full Python 3.12
run passed **all 382 tests** ([output](check-34.log)); the final focused run passed
**69 tests** ([output](check-22.log)). This preserves the intermittent failed run
as evidence rather than silently treating it as a pass.

All eight applicable document/pin/index/discovery checkers passed in normal and
self-test modes (16 invocations). Both architecture checks passed, including
seven regression tests. Rust formatting passed. Kernel tests, workspace tests,
workspace Clippy and kernel dependency-tree commands each exited 101 before
compilation/resolution because the offline cache lacks `bcs`. These four checks
are **unavailable, not passes**; no dependency bootstrap/network acquisition or
CI change was attempted. The supervisor must provide the offline dependencies
and run those checks in its delivery environment.

[Transcript capture/comparison](verify_transcripts.py) passed: the guided and
fixture subprocess journeys contain eight identical complete envelopes each;
the boundary journeys contain six. All four stderr captures are empty. Journey
exits are 0; boundary exits are the expected sticky 1, preserving three forbidden
obligation-pool refusals and one exhaustion refusal. Existing journey transcripts
also exercise declined mutations and repeated references.

| Startup over one local child | Journey | Boundaries |
|---|---|---|
| Guided balances, no initialization fixture | [stdout](guided-journey.stdout), [stderr](guided-journey.stderr), exit 0 | [stdout](guided-boundaries.stdout), [stderr](guided-boundaries.stderr), exit 1 |
| Fixture file | [stdout](fixture-journey.stdout), [stderr](fixture-journey.stderr), exit 0 | [stdout](fixture-boundaries.stdout), [stderr](fixture-boundaries.stderr), exit 1 |

## Preservation and delivery gates

Before editing, working-file Git blobs matched both required locks:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

A pre-edit path/SHA-256 inventory captured 108 files under `reference/v0.3-rc1/`,
one under `.aiops/`, and ten under `docs/tasks/`. The [preservation checker](verify_preservation.py) and [pre-edit inventory](protected-before.json)
compare the complete path/byte sets before and after work and with unchanged
HEAD, including both locked blobs. All 121 protected files match. Its changed-path
allowlist also proves the model, reward machinery, existing fixtures and workflows
unchanged. The complete [changed-path inventory](changed-paths.txt) lists code,
tests, documentation and every evidence artifact. No protected file was written. Final docs-index, whitespace and preservation
checks passed again after completing this report (see the command table).

Implementation/final committed head: not created; HEAD remains the starting SHA
with an uncommitted patch. Merge SHA/main-push/post-merge results: not applicable.
Exact-head KTX run ID/status/conclusion: NOT_RUN / unavailable in this session.
Exact-head KIX run ID/status/conclusion: NOT_RUN / unavailable in this session.
Independent A2 non-author exact-final-head review: pending supervisor delivery.
Required KTX/KIX CI and non-author review remain delivery gates; this record
claims no merge readiness. No commit, push, branch/tag operation, GitHub/network
action, PR, issue, comment or ASTRA marker was made.

## Limits and deviations

No explicit contract violation or new contract-undefined behavior was found.
Repeated-reference append behavior remains an existing characterization, not an
idempotency guarantee. Funding policy remains **UNDETERMINED — Astra/User**;
accounting treatment remains **UNDETERMINED — User/designated advisers**.

No model, reward coupling, persistence, financial execution, protocol command,
production runtime, public endpoint, secret, paid service, coin/TIX, storage
engine, replication or consensus was added. No real funds/PG/bank/KYC or Sui
testnet/mainnet was used. No rollback, durability, chain finality, legal compliance,
production readiness or clean-room independence is claimed. Product reads remain
blocking and interruptible, with no polling, response deadline or automatic retry.
Unrelated bootstrap/chain/ZK/SDK artifact-generation CI stages are outside these
touched paths and were not run. Fetch omission follows the later explicit
supervisor restriction. Reading initialization bytes before text newline conversion
makes the specified LF framing explicit; ordinary request handling is unchanged.
There is no semantic design deviation. Verification deviations are the unavailable
offline Rust checks and the retained unchanged reward-harness deadline failure;
no diagnosis stronger than the observed evidence is claimed.


Builder handoff: READY for supervisor handling of this uncommitted patch. The
four unavailable Rust checks, non-author A2 review and required exact-head CI
remain outstanding; READY here is local implementation handoff, not merge-ready.
