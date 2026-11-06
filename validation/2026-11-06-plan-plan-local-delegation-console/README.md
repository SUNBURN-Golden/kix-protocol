# Local delegation console builder evidence

Node: `plan-plan-local-delegation-console`. Task input: supplied user node specification and read-only design plan; no issue or docs/tasks task document assigned.

Branch: `agent/kix-plan-plan-local-delegation-console`. Observed cached origin/main and starting/task HEAD: `4e04ac9158ae7b27170a80dd9042a4cddd82d8d0`. No local base delta. Fetch NOT_RUN under the explicit supervisor no-network rule; remote freshness unverified. No commit, push, publication or merge is authorized in this session. Final implementation is an uncommitted patch over that HEAD; no separate implementation/final commit exists.

## Coverage map recorded before adding console tests

| Acceptance | Existing coverage and classification | Console gap |
|---|---|---|
| Grant/query/proposal/human decision/revocation/retained views | Partially covered: `reference/ai_delegation/test_delegation_cli.py::test_lifecycle_complete_receipts_retained_views_and_inert_change_memo` | Guided real-session transcript and dispatcher equivalence |
| Explicit current-record replay | Partially covered: same module `test_replay_returns_current_records_and_preserves_first_revocation_reason` | Explicit confirmation for each replay and binding conflicts |
| All effects false, approval inert | Sufficient domain coverage: `test_ai_delegation_mock.py::test_flags_remain_false`, `test_decide_rechecks_grant_and_approval_does_not_execute` | Every emitted console body retains eleven false flags, provenance/lifecycle and effects_executed |
| Invalid/declined zero dispatch, confirmed once | Console not covered; `test_delegation_session.py::test_each_method_forwards_original_objects_once_and_returns_same_object` covers forwarding | Stream injection and dispatcher spy, exact preview payload, no implicit reads |
| EOF/output/unexpected failure stops without retry | Console not covered | Failure at input, preview, confirmation, dispatch, result and diagnostic; appended sentinel actions |
| A5 / missing-grant uncertainty | Sufficient documentation coverage: October 26 addendum and October 27 closure linked from delegation README | Keep class-C discrepancy and Astra/User ownership; exclude simultaneous-error case from new normative transcripts |
| Local suite/checks | Existing CI discovery and checker infrastructure | Run narrow suite before complete delegation suite and applicable CI equivalents |

This is builder-authored evidence, not independent A2 review, exact-head CI, merge readiness or acceptance. A5 remains unresolved; no ordered-precedence conformance is claimed.

## Console verification added

All test symbols below are in `reference/ai_delegation/test_delegation_console.py::ConsoleTests`.

| New evidence | Gap addressed |
|---|---|
| `test_console_journey` | 19 confirmed actions against the real session, all five tools, approve/reject/withdraw, inert grant-change memo, revocation, retained views, new generation; exact envelopes equal the existing dispatcher |
| `test_console_replay` | 28 explicitly confirmed requests, current approved/withdrawn/voided proposals and revoked grants, first revocation reason, literal binding-conflict codes |
| `test_console_boundaries` | Unknown/malformed/declined input; 11 previews but only 9 dispatches; separately confirmed scope/expiry/amount/transfer/execution/revocation refusals |
| `test_preview_is_complete_and_flushed_before_confirmation_without_session_calls` | No mock/session/dispatcher call before confirmation; exact canonical preview flushed before reading SUBMIT |
| `test_declined_every_operation_has_no_dispatch_or_implicit_views` | All seven operations, including views; only literal SUBMIT can dispatch |
| `test_invalid_console_shapes_dispatch_zero_and_return_to_menu` | Invalid/missing/extra/wrong-type structured fields, strict JSON, Unicode, duplicate keys, non-finite numbers; zero dispatch |
| `test_confirmed_value_refusals_belong_to_mock_and_dispatch_once` | Shape-valid domain refusals forwarded unchanged once, preserving mock predicates |
| `test_eof_at_each_grant_prompt_or_confirmation_never_dispatches` | EOF at every stage before submission terminates without dispatch |
| `test_input_errors_and_interruptions_fence_sentinel` | Input failures before/after dispatch stop appended sentinel actions |
| `test_output_write_short_write_and_flush_failures_fence_sentinel` | Startup/prompt/preview/confirmation/result failures stop immediately; applied result retained in diagnostic |
| `test_unexpected_dispatch_errors_invariant_and_bad_diagnostic_stop_without_retry` | Failure after possibly applied mutation, MOCK_INVARIANT, internal FixtureError, interruption and unavailable diagnostic sink; exactly one call and no retry |
| `test_executable_transcripts_and_fresh_processes` | Runnable entry point, deterministic repeated fresh processes and complete output envelopes |
| `test_setup_failure_never_dispatches_and_preserves_error_envelope` | Missing/malformed fixture and registry invariant failure stop before dispatch |

Every applicable body in all three transcripts is checked for MOCK provenance,
IN_MEMORY_FSM lifecycle, all eleven FALSE_FLAGS and proposal effects_executed=false.
The journey and replay requests were transcribed from the existing desk fixtures;
test expectations use those inputs plus literal phases/errors, independently of
the console prompt tables. These are source-informed tests, not clean-room or
independent A2 evidence. Mock spies count every call, including any hidden views.

## Actual commands and results

[commands.json](commands.json) records exact verification commands, environment,
exit codes, durations and captured stdout/stderr (inline for checks, separate files for transcripts). Python commands use
`PYTHONDONTWRITEBYTECODE=1`; narrow tests also set `PYTHONPATH=reference/ai_delegation`.
Initial and reviewed narrow/full runs are retained: the later runs followed test
improvements for preview flush observation and counting all mock calls. All runs
passed; there was no implementation test failure or automatic retry.

| Command | Actual result |
|---|---|
| `PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_console` | exit 0 on all three runs; 13 tests passed per run |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | exit 0 on both runs; 117 tests passed, including 13 console tests |
| `python3 scripts/check_ai_delegation_evidence_map.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_delegation_layer_matrix.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_contract_error_codes.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_evidence_map_rollup.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_class_b_index.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_docs_index.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_status_register.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_ci_test_discovery.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/check_ci_checker_wiring.py` and separately `--self-test` | both exit 0 |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; dependency gate passes; no durability/performance certification |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json < reference/ai_delegation/fixtures/delegation_console_journey.txt` | expected exit 0; 19 previews / 19 desk replies; [stdout](transcript-journey.stdout.txt) |
| Same executable/fixture, input `delegation_console_replay.txt` | expected exit 1 for binding conflicts; 28 previews / 28 desk replies; [stdout](transcript-replay.stdout.txt) |
| Same executable/fixture, input `delegation_console_boundaries.txt` | expected exit 1 for domain refusals; 11 previews / 9 desk replies; [stdout](transcript-boundaries.stdout.txt) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; uncached `bcs`, required by workspace member kix-bcs1; no compilation/tests reached |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; same offline resolution failure; Clippy analysis not reached |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0; no mutations |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | exit 101; same offline resolution failure; tree not certified |
| Protected-byte Python comparison (exact `python3 -c` in commands.json) | exit 0; both locks match before/after, all 108 frozen paths/bytes match before and HEAD |
| `git diff --exit-code HEAD --` protected/runtime/governance/mock/desk/existing-test paths (complete arguments in commands.json) | exit 0; no changes |
| `git diff --check` | exit 0 |
| `git rev-parse HEAD origin/main` | both `4e04ac9158ae7b27170a80dd9042a4cddd82d8d0` |

The workflow definitions inspected were `.github/workflows/protocol.yml` and
`.github/workflows/ktx-kernel.yml`. Selected stdlib reference discovery and
checker commands are the protocol equivalents applicable to these Python/docs
paths. Architecture/kernel/Clippy/format/tree commands follow the KTX steps;
Cargo uses --offline to honor the supervisor no-network rule. Workspace
resolution needs bcs even when selecting only kix-kernel. No dependency install,
network fallback, automatic retry, Cargo change or CI change was attempted.
Untouched Rust/Move/SDK/ZK workflow steps and full hosted workflows were not run.

## Protected bytes and changed paths

The initial worktree was clean. [protected-before.json](protected-before.json)
and [protected-after.json](protected-after.json) contain complete frozen path,
size and SHA256 manifests, plus locked Git blobs. Both snapshots match exactly;
all 108 frozen files also match Git HEAD, with no missing or extra paths.

| Locked file | Before / after Git blob (identical) |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

Code/docs outputs are delegation_console.py, test_delegation_console.py, three
console transcript fixtures, reference/ai_delegation/README.md and docs/README.md.
The evidence directory contains this report, command records, captured output
and protected manifests. The complete individual file list is
[changed-paths.txt](changed-paths.txt): 18 files, including every evidence artifact.
No existing mock, session, dispatcher, fixture, test, contract, status map,
runtime, frozen reference, task, .aiops or CI file was modified.
Final-merge blob verification is N/A (no merge).

## Review, CI and task state

| Gate | Run ID / status / conclusion |
|---|---|
| A2 non-author exact-final-head review | Not performed; builder tests are not independent review |
| Exact-head KTX kernel verification | ID unavailable; NOT_RUN / unverified; no commit or publication authorized |
| Exact-head KIX protocol verification | ID unavailable; NOT_RUN / unverified; no commit or publication authorized |
| Post-merge main/push CI | N/A; not merged; merge SHA N/A |

Starting/base, implementation-parent and final branch HEAD remain
`4e04ac9158ae7b27170a80dd9042a4cddd82d8d0`. The implementation is an uncommitted
patch, so that HEAD does not identify its new bytes. Supervisor must establish
the final commit, independent A2 review and exact-head CI; no older SHA's CI is
transferred. Local READY means completed console builder handoff, not merge
readiness or acceptance. Offline Rust checks remain unexecuted beyond resolution.

## Findings, deviations, uncertainty and non-claims

No new contract violation or contract-undefined semantics were established.
The pre-existing **A5 class-C discrepancy remains unresolved**, with
[October 26 addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure)
and [October 27 closure](../../docs/status/OPEN_USER_DECISIONS_20261027_CLOSURE.md)
retaining the owner: Astra as contract/design authority, with User authorization
of any resulting scope/contract change and User merge. Mock registration, tool
lists, then grant-agent binding differs from contract §7. New normative
transcripts exclude registered wrong agents paired with denied/unknown tools.
No mock validation change, resolution or ordered-precedence conformance is claimed.
Missing-grant binding interpretation remains UNDETERMINED with the same owner;
existing broader simultaneous-error characterizations are not promoted.

Deviations: fetch and all Git/GitHub publication actions omitted under the explicit
supervisor rule; cached origin/main only, remote freshness unverified. No task
document exists for this loop-proposed node; supplied user specification is the
immutable task input. Offline Cargo dependencies were unavailable; no automatic
retry or install. Initial protected-tree verification used newline-delimited
ls-tree output, which quotes a Korean filename and caused a parsing assertion;
corrected to NUL-delimited ls-tree -rz before implementation. No protected file
changed. No product/design scope deviation or product policy value was needed.
Short-write detection is included as output-failure handling.

Product limits/aggregation/permitted surfaces remain UNDETERMINED — Astra;
identity policy — Astra/User; authoritative time/chain cuts — k1-cut-proof / RS-3a;
legal authority — User/legal. Fixtures are synthetic inputs, not product policy,
identity designation or legal decisions. Human approval remains an inert memo.
There is no model connection, execution service, persistence, protocol command,
production runtime, public endpoint, real funds, real PG/bank/KYC call, Sui
testnet/mainnet, storage/replication/consensus engine, coin/TIX change or secret.
No durability, distributed fencing, bank exactly-once, chain finality, compliance,
production readiness, capability grade or project completion is inferred.
Follow-up candidates are the separate owner-held A5/missing-grant decisions and
supervisor-provided offline Cargo cache / publication and review gates.
