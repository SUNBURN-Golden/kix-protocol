# Local delegation live console — builder evidence

Task: `plan-plan-local-delegation-live-console`. Task input is the supplied node/design plan in the supervisor prompt; no issue or docs/tasks document is assigned. Not ASTRA program mode.

## Coverage mapped before implementation

| Requirement | Existing evidence | Coverage / gap |
|---|---|---|
| Lifecycle, grant/query/proposal/human decision/revocation/views | test_delegation_cli.DelegationCliTests.test_lifecycle_complete_receipts_retained_views_and_inert_change_memo | Partial: no response-dependent reads with stdin open |
| Replay current records and first revocation reason | test_delegation_cli.DelegationCliTests.test_replay_returns_current_records_and_preserves_first_revocation_reason; test_delegation_console.ConsoleTests.test_console_replay | Partial: no client/console subprocess composition |
| Confirmations including views | test_delegation_console.ConsoleTests.test_declined_every_operation_has_no_dispatch_or_implicit_views | Partial: no child write counts |
| Strict framing, correlation, response structure | test_delegation_serialization.py (input decoding) | Not covered for client replies |
| Terminal fencing and retained diagnostics | test_delegation_console.py stream failure tests | Partial: no subprocess interruption/transport/cleanup coverage |
| Disabled execution / false flags | test_ai_delegation_mock.py; test_delegation_cli.py; test_delegation_console.py | Sufficient domain evidence; new composition assertions needed |
| Default in-process API | test_delegation_console.py | Sufficient; run unchanged, compare explicit modes |
| A5 | reference/ai_delegation/README.md A5 attribution | Existing class-C discrepancy retained; no new normative precedence claim |

This is builder-authored, source-informed verification, not A2 non-author review. No merge readiness, activation or full contract conformance claim.

## Implementation and focused evidence

The client owns a single ordinary-buffered `delegation_cli.py` child. It shares
strict JSON and selector/signature definitions, validates response structure and
identifier correlation without reimplementing mock predicates, and fences on
transport uncertainty. Typed/startup/invariant error envelopes remain available
as complete replies while prohibiting subsequent client use. The only CLI change
is `_emit(..., flush=True)`. Both console entry points use the same prompt loop;
all requests, including views, require explicit preview and literal SUBMIT.

New source-informed coverage (not clean-room or independent A2 verification):

| New tests | Gap addressed |
|---|---|
| `test_delegation_client.py::test_live_lifecycle_before_eof` | Real ordinary-buffered child; fixture lifecycle compared to public session calls; response-derived explicit views before EOF; exact launch command and inherited stderr |
| `test_replay_current_records_and_explicit_disabled_execution` | Existing replay vector, current approved/withdrawn/voided/revoked records, first reason, binding conflicts; explicit execution refusal followed by another view |
| `test_invalid_local_requests_write_nothing_and_client_remains_usable` | Invalid local JSON/envelope/signature writes zero; nested business refusal still forwarded and next explicit read works |
| `test_strict_frames_and_response_shapes_fence_with_raw_evidence` | Injected framing/UTF-8/duplicate-key/nonfinite/Unicode failures; envelope/payload/type/nullable/provenance/identifier/effect flag mismatches, successful execution rejection; raw bytes/cause retained and next call writes nothing |
| `test_terminal_complete_errors_are_retained` | Real worker complete typed/startup/MOCK_INVARIANT errors retained; no subsequent use or replacement |
| `test_hostile_live_children_and_startup_failures_no_replacement` | Real worker truncation, malformed/mismatched reply, child exit and absent fixture; one submitted line, no retry or replacement |
| `test_short_write_broken_pipe_flush_and_interruptions_retain_diagnostics` | Partial/None writes, broken pipe, interrupted write/read, failed flush/read; detached input and prior reply, raw bytes and cause survive cleanup |
| `test_overlapping_request_and_cleanup_rejected_before_write` | Busy request and close rejected before writes; original request completes and later explicit read works |
| `test_launch_validation_import_safety_and_context_cleanup`, `test_bounded_cleanup_terminates_kills_and_reaps_owned_child` | Explicit timeout validation, import launches nothing, context cleanup, idempotent close, real terminate/kill/reap ownership |
| `test_delegation_console_subprocess.py::test_real_child_journey_and_replay_match_existing_fixtures` | Real child composition; complete envelopes and actual child writes compared to unchanged lifecycle/replay vectors; all effects false |
| `test_interactive_response_dependent_reads_and_preview_before_confirmation` | Input depends on prior reply while child stdin remains open; preview flushed and no sender call before SUBMIT |
| `test_all_seven_selectors_confirm_once_declines_and_invalid_dispatch_nothing` | All seven selectors including views, actual write counts, literal confirmation, declined/invalid input zero writes and no hidden reads |
| `test_default_explicit_and_subprocess_cli_transcripts_are_identical`, `test_mode_isolation_and_cleanup_timeout_validation` | Three existing transcripts byte-identical across default, explicit in-process and subprocess modes; options/modes isolated, no sockets/fallback |
| Remaining console subprocess failure tests | Quit/EOF/interruption, preview/result write/short-write/flush, malformed real child, startup/typed/invariant/client-state failures stop queued sentinel actions; cleanup diagnostics retain primary wire/cause/last reply and owned child is reaped |

## Actual commands and results

[commands.json](commands.json) stores exact command argument arrays, environment,
exit status, duration and stdout/stderr log paths. All Python verification sets
`PYTHONDONTWRITEBYTECODE=1`; unittest runs use
`PYTHONPATH=reference/ai_delegation`. Python 3.13.5; Cargo/rustc 1.98.1.
Workflow sources inspected: `.github/workflows/protocol.yml` and
`.github/workflows/ktx-kernel.yml`. Narrow tests preceded discovery and CI
counterparts. Early successful runs are retained; final focused/discovery runs
followed added correlation/preview/output-failure assertions. No failed test was
retried automatically. Cargo failures were not retried or downloaded around.

| Command | Actual result |
|---|---|
| `PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_client test_delegation_console` | exit 0, 23 tests passed (initial focused check) |
| `PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_client test_delegation_console_subprocess test_delegation_console test_delegation_cli test_delegation_serialization test_delegation_session` | exit 0, 53 tests passed on both runs |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | exit 0, 138 tests passed on both runs |
| `python3 scripts/check_ai_delegation_evidence_map.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_contract_error_codes.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_evidence_map_rollup.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_class_b_index.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_docs_index.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_status_register.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_ci_test_discovery.py` and separately `--self-test` | both exit 0; new modules reached by existing discovery |
| `python3 scripts/check_ci_checker_wiring.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; declaration/dependency boundary only |
| `python3 scripts/test_runtime_architecture.py` | exit 0, 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101, UNAVAILABLE: uncached `bcs` required by workspace member kix-bcs1; compilation/tests not reached |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101, UNAVAILABLE: same uncached dependency; analysis not reached |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0, no mutations |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | exit 101, UNAVAILABLE: same uncached dependency |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 101, UNAVAILABLE: same uncached dependency; no workspace tests ran |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 101, UNAVAILABLE: same uncached dependency; no workspace analysis ran |
| `python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_journey.txt` | expected exit 0, 19 previews / 19 replies; [stdout](transcript-journey.stdout.txt), empty stderr |
| Same executable/options/fixture with `delegation_console_replay.txt` | expected exit 1, 28 previews / 28 replies; [stdout](transcript-replay.stdout.txt), empty stderr |
| Same executable/options/fixture with `delegation_console_boundaries.txt` | expected exit 1, 11 previews / 9 replies; [stdout](transcript-boundaries.stdout.txt), empty stderr |
| Preservation comparison (`python3 -c` source recorded in commands.json) | exit 0; both locks and all 108 frozen paths/bytes match before and HEAD |
| `git diff --exit-code HEAD --` protected/runtime/governance/mock/desk/fixture/existing-test paths (full argument list in commands.json) | exit 0; unchanged |
| `git diff --check` | exit 0 |
| `git rev-parse HEAD origin/main` | both `81cea037095e992e4a9763f62e195a2ff7fa8513` |

These are the applicable local Python/docs/architecture checks, not full hosted
workflows. Untouched Move/SDK/ZK/runtime integration paths and real provider/chain
workflows were not executed. Missing Cargo dependencies are unavailable checks,
never passes. No dependency, Cargo, workflow or environment settings were changed.

## Identity, preservation and delivery gates

Starting and underlying final HEAD, and cached `origin/main`, are all
`81cea037095e992e4a9763f62e195a2ff7fa8513`; branch
`agent/kix-plan-plan-local-delegation-live-console`. No local base delta. Freshness
is unverified: `git fetch origin main` was NOT_RUN because the explicit supervisor
rule forbids all network/GitHub actions. No task document was supplied under
`docs/tasks/`; the supplied node/design is the task input. No commit was made,
so implementation/final task commit SHA is not yet assigned; the deliverable is
an uncommitted patch over the above HEAD. No merge commit or post-merge CI exists.

The initial worktree was clean. [preservation-before.json](preservation-before.json)
and [preservation-after.json](preservation-after.json) record both locked Git blobs
and SHA256/Git blob hashes for all 108 frozen files. The final comparison requires
exact path/byte equality with the initial manifest and with Git HEAD. The locked
files match before and after:

| Path | Before / after blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The full changed-path list is [changed-paths.json](changed-paths.json). Code/docs:
`reference/ai_delegation/delegation_client.py`, `delegation_cli.py`,
`delegation_console.py`, `test_delegation_client.py`,
`test_delegation_console_subprocess.py`, `reference/ai_delegation/README.md`,
`docs/README.md`; remaining changes are this validation directory's records,
manifests, logs and transcripts. No locked/frozen/runtime/program/task/CI/mock/
session/fixture/existing-test changes are part of this delivery.

| Required gate | Status / run ID / conclusion |
|---|---|
| A2 non-author review of exact final committed head | Pending supervisor; builder evidence does not satisfy it |
| Exact-head KTX kernel verification | NOT_RUN / unavailable / none (no final commit or publication) |
| Exact-head KIX protocol verification | NOT_RUN / unavailable / none (no final commit or publication) |
| Merge and main/push verification | Not applicable; no merge authorized or performed |

No earlier SHA's CI is transferred. `READY` means bounded local builder delivery,
not merge-ready. The supervisor owns commits, publication and subsequent review/CI.

## Preserved discrepancies, uncertainty and deviations

A5 remains the existing class-C check-order discrepancy attributed to the
[October 26 addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure)
and [October 27 closure](../../docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md).
Mock actor registration → tool lists → grant-agent binding still differs from
contract §7. The registered wrong-agent plus denied/unknown-tool case is excluded
from new normative transcripts. No new contract violation was found or repaired;
no full contract conformance is claimed. A5 and missing-grant binding uncertainty
remain with Astra as contract/design authority, User authorization of resulting
scope/contract changes and User merge. Existing broader simultaneous-error
characterizations are not promoted to precedence evidence.

No new business semantics were invented. Product limits/surfaces remain
UNDETERMINED — Astra; identity UNDETERMINED — Astra/User; legal effects
UNDETERMINED — User/legal. Current-record duplicate behavior and first revocation
reason are preserved. All eleven effect flags and proposal effects_executed are
false; human approval remains an inert memo. There is no model service, socket,
credential, public endpoint, production runtime, persistence, storage engine,
replication, consensus, new command, funds/provider/KYC or chain call. No durability,
distributed fencing, bank exactly-once, chain finality, legal compliance or production
readiness claim follows.

Plan deviations: supervisor no-network/no-publication rules replace fetch and
GitHub delivery with a freshness-unverified local SHA and uncommitted patch.
Kernel/workspace Cargo checks were attempted offline once each and are unavailable
due to missing cached bcs; no network fallback or retry. Cleanup's final kill wait
is also bounded by the explicit caller timeout. Most hostile-shape variants use
deterministic injected pipes, supplemented by real hostile child truncation,
mismatch/exit/startup/error/reaping tests. No design or policy scope expansion.
Follow-up: supervisor exact-final-head A2 review and KTX/KIX CI, cached-dependency
Rust verification in a qualified environment, and separate Astra/User A5 disposition.
