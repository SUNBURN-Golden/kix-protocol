# Guided delegation composer — builder evidence

Task: `plan-local-delegation-input-composer`; supplied supervisor node/design is the immutable task input. No issue or docs/tasks task document assigned. Not ASTRA program mode.

## Initial coverage map (recorded before adding tests)

All test paths below are under reference/ai_delegation. This is source-informed builder evidence, not independent conformance or A2 review.

| Requirement | Existing tests/evidence | Classification and gap |
|---|---|---|
| Guided/raw envelope and reply parity | test_delegation_console.ConsoleTests.test_console_journey | Not covered for guided entry; raw lifecycle sufficient |
| One real child grant/proposal/human decision/revocation, all five tools | test_delegation_console_subprocess.DelegationConsoleSubprocessTests.test_real_child_journey_and_replay_match_existing_fixtures | Partially covered: raw only |
| Optional fields, exact integers, opaque identifiers, no defaults | test_delegation_console.ConsoleTests.test_invalid_console_shapes_dispatch_zero_and_return_to_menu; test_delegation_serialization.DelegationSerializationTests.test_nested_values_and_tools_are_forwarded_without_transport_reinterpretation | Partially covered: guided composition absent |
| Decline/malformed/incomplete zero requests, confirmed once | test_delegation_console.ConsoleTests.test_declined_every_operation_has_no_dispatch_or_implicit_views; test_delegation_console_subprocess.DelegationConsoleSubprocessTests.test_all_seven_selectors_confirm_once_declines_and_invalid_dispatch_nothing | Partially covered: new prompt branches absent |
| EOF and output failure fence | test_delegation_console.ConsoleTests.test_eof_at_each_grant_prompt_or_confirmation_never_dispatches; test_output_write_short_write_and_flush_failures_fence_sentinel | Partially covered: guided prompts absent |
| Transport uncertainty no retries/fallback | test_delegation_console_subprocess.DelegationConsoleSubprocessTests.test_live_malformed_reply_and_child_exit_stop_queued_sentinel; test_delegation_client.DelegationClientTests.test_short_write_broken_pipe_flush_and_interruptions_retain_diagnostics | Sufficient transport coverage; add guided composition sentinel |
| EXECUTE refused, eleven FALSE_FLAGS and effects_executed false | test_delegation_console.ConsoleTests.test_confirmed_value_refusals_belong_to_mock_and_dispatch_once; test_console_journey; subprocess lifecycle assertions | Sufficient domain evidence; add guided parity |
| Existing A5 unresolved | reference/ai_delegation/README.md A5 attribution; docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md | Sufficient attribution; preserve discrepancy/owners |

## Initial observations

Branch agent/kix-plan-local-delegation-input-composer. Initial HEAD and cached origin/main both ba1da31b0935f5356567014b23b38c76e764a7f9. Initial worktree clean. Fetch omitted under explicit supervisor no-network rule; remote freshness unverified. No task base delta observed locally. Preservation-before.json records protected bytes before edits; both required kernel blobs match.

## Delivered behavior and new coverage

The private composer accepts literal `:guided` only at structured-value prompts.
Counts and explicit include/omit choices are presentation inputs, never serialized.
All completed values pass the existing strict JSON and structural checks, then the
same flushed preview, literal SUBMIT and one dispatch. It holds no client/session
and adds no protocol command, policy default, implicit view or retry. Nested
strings remain verbatim; top-level identifier checks remain unchanged. Requests
preserve exact integers, list order/duplicates and omitted versus included keys.
Raw JSON remains available, including within a guided grant-change memo.

The new test helpers render input from the documented schemas; expected envelopes
come from independent literal requests or pre-existing desk vectors, never the
composer's field tables. This is source-informed evidence, not clean-room review.

| New test (under reference/ai_delegation) | Gap addressed |
|---|---|
| test_delegation_console.ConsoleTests.test_guided_raw_envelope_parity | Complete previews, exact dispatch envelopes and desk results equal the existing lifecycle vector; all five tools, grant, human decisions, revocation |
| test_guided_optionals_exact_integers_and_verbatim_strings | Omitted/present/empty optionals, ordered duplicate lists, Unicode/opaque identifiers, spaces/commas/empty strings, exact integer boundaries and values above 2**53; EXECUTE/empty authority/empty requested/unsupported currency reach unchanged domain refusal |
| test_guided_requested_allows_mixed_raw_structured_entry | Each included requested object can use raw JSON inside guided composition |
| test_guided_decline_and_eof_at_every_new_prompt_send_nothing | Every guided lifecycle grant/tool input prefix, including full nested requested and confirmation: EOF fences, zero dispatch; nonliteral confirmations decline |
| test_guided_malformed_composition_discards_action | Invalid list counts, all optional choices, limits/period/amount types, explicit null, invalid Unicode and unsupported guided tool; fresh menu, zero preview/dispatch |
| test_guided_preview_and_prompt_output_failures_fence_sentinel | Prompt/preview/confirmation/result write, short-write and flush failures; no later action or retry |
| test_delegation_console_subprocess.DelegationConsoleSubprocessTests.test_guided_real_child_journey_matches_raw | Each journey owns one actual child, asserts exact child writes and unchanged replies, closes/reaps it; all eleven flags and proposal effects_executed false |
| test_guided_boundaries_zero_invalid_writes_and_confirmed_refusals | Four input errors and two declines write nothing; confirmed raw boundary envelopes/replies plus one EXECUTE grant refusal |
| test_guided_confirmation_after_flushed_preview_writes_once | Complete flushed preview observed before literal confirmation, zero prior sender calls, one actual child write afterward |
| test_guided_eof_and_output_failures_stop_queued_sentinel | Real-child grant EOF prefixes and output failures before/after dispatch, reaping, retained last reply and no sentinel dispatch |
| test_guided_transport_uncertainty_stops_sentinel_without_retry | Real hostile child truncates reply and exits; one write/launch, request and raw reply retained, no retry/replacement/fallback |

## Commands actually run and results

The table lists actual commands, exit status and retained output. Python checks
used `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=reference/ai_delegation`.
[commands.jsonl](commands.jsonl) retains exact argv/environment and transcript
stdin paths. Checks were run once each; no automatic retry or network fallback.
Narrow tests ran first (45 tests, PASS), then full discovery (149 tests, PASS).
Nine applicable document checks plus their self-tests and both architecture
commands passed (20 commands; architecture negative-control suite: 7 tests).

The closest applicable workflow steps were inspected in
`.github/workflows/ktx-kernel.yml` (architecture, kernel tests/Clippy/format/tree)
and `.github/workflows/protocol.yml` (reference discovery, document checks,
architecture and workspace Rust). No workflow changed. This is bounded local
verification of touched paths, not a claim to have run the entire protocol
workflow, Move/localnet, ZK, unrelated reference suites or hosted CI.

Cargo test/Clippy/tree commands exited 101 before compilation: the local offline
cache lacks `bcs`, required by `kix-bcs1`. These five checks are UNAVAILABLE, not
passes or source failures; no dependency download, setting change or retry was
performed. Cargo formatting passed.

Subprocess transcripts retain complete stdout/stderr and actual exits. Journey
exits 0; replay/boundaries exit 1 for explicit expected domain refusals. All five
stderr files are empty. Guided journey sends the unchanged lifecycle vector.
Guided boundaries sends the same nine confirmed requests as raw boundaries plus
an EXECUTE-authority refusal; its four malformed compositions/two declines write
nothing. Cleanup timeout 1 is synthetic caller transport configuration.

| Actual command | Actual result / retained evidence |
|---|---|
| `python3 -m unittest test_delegation_console test_delegation_console_subprocess test_delegation_client` | PASS: 45 tests; exit 0; [narrow.log](narrow.log) |
| `python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | PASS: 149 tests; exit 0; [full-suite.log](full-suite.log) |
| `python3 scripts/check_ai_delegation_evidence_map.py` | PASS: exit 0; [ai_delegation_evidence_map.log](ai_delegation_evidence_map.log) |
| `python3 scripts/check_ai_delegation_evidence_map.py --self-test` | PASS: exit 0; [ai_delegation_evidence_map-self-test.log](ai_delegation_evidence_map-self-test.log) |
| `python3 scripts/check_delegation_layer_matrix.py` | PASS: exit 0; [delegation_layer_matrix.log](delegation_layer_matrix.log) |
| `python3 scripts/check_delegation_layer_matrix.py --self-test` | PASS: exit 0; [delegation_layer_matrix-self-test.log](delegation_layer_matrix-self-test.log) |
| `python3 scripts/check_contract_error_codes.py` | PASS: exit 0; [contract_error_codes.log](contract_error_codes.log) |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: missing cached bcs; exit 101; [kernel-tests.log](kernel-tests.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: missing cached bcs; exit 101; [kernel-clippy.log](kernel-clippy.log) |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS: exit 0; [rust-format.log](rust-format.log) |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | UNAVAILABLE: missing cached bcs; exit 101; [kernel-tree.log](kernel-tree.log) |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE: missing cached bcs; exit 101; [workspace-tests.log](workspace-tests.log) |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: missing cached bcs; exit 101; [workspace-clippy.log](workspace-clippy.log) |
| `python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_guided_journey.txt` | Expected exit 0; empty stderr; [guided_journey.stdout.txt](guided_journey.stdout.txt) |
| `python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_guided_boundaries.txt` | Expected exit 1; empty stderr; [guided_boundaries.stdout.txt](guided_boundaries.stdout.txt) |
| `python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_journey.txt` | Expected exit 0; empty stderr; [journey.stdout.txt](journey.stdout.txt) |
| `python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_replay.txt` | Expected exit 1; empty stderr; [replay.stdout.txt](replay.stdout.txt) |
| `python3 reference/ai_delegation/delegation_console.py --fixture reference/ai_delegation/fixtures/delegation_session.json --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_boundaries.txt` | Expected exit 1; empty stderr; [boundaries.stdout.txt](boundaries.stdout.txt) |
| `python3 scripts/check_contract_error_codes.py --self-test` | PASS: exit 0; [contract_error_codes-self-test.log](contract_error_codes-self-test.log) |
| `python3 scripts/check_evidence_map_rollup.py` | PASS: exit 0; [evidence_map_rollup.log](evidence_map_rollup.log) |
| `python3 scripts/check_evidence_map_rollup.py --self-test` | PASS: exit 0; [evidence_map_rollup-self-test.log](evidence_map_rollup-self-test.log) |
| `python3 scripts/check_class_b_index.py` | PASS: exit 0; [class_b_index.log](class_b_index.log) |
| `python3 scripts/check_class_b_index.py --self-test` | PASS: exit 0; [class_b_index-self-test.log](class_b_index-self-test.log) |
| `python3 scripts/check_docs_index.py` | PASS: exit 0; [docs_index.log](docs_index.log) |
| `python3 scripts/check_docs_index.py --self-test` | PASS: exit 0; [docs_index-self-test.log](docs_index-self-test.log) |
| `python3 scripts/check_status_register.py` | PASS: exit 0; [status_register.log](status_register.log) |
| `python3 scripts/check_status_register.py --self-test` | PASS: exit 0; [status_register-self-test.log](status_register-self-test.log) |
| `python3 scripts/check_ci_test_discovery.py` | PASS: exit 0; [ci_test_discovery.log](ci_test_discovery.log) |
| `python3 scripts/check_ci_test_discovery.py --self-test` | PASS: exit 0; [ci_test_discovery-self-test.log](ci_test_discovery-self-test.log) |
| `python3 scripts/check_ci_checker_wiring.py` | PASS: exit 0; [ci_checker_wiring.log](ci_checker_wiring.log) |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | PASS: exit 0; [ci_checker_wiring-self-test.log](ci_checker_wiring-self-test.log) |
| `python3 scripts/verify_runtime_architecture.py` | PASS: exit 0; [verify_runtime_architecture.log](verify_runtime_architecture.log) |
| `python3 scripts/test_runtime_architecture.py` | PASS: exit 0; [test_runtime_architecture.log](test_runtime_architecture.log) |
| `python3 validation/2026-11-08-plan-local-delegation-input-composer/verify_preservation.py` | PASS: exit 0; [preservation.log](preservation.log) |

## Base, preservation, changed paths and publication gates

Initial observed branch HEAD and locally cached `origin/main`:
`ba1da31b0935f5356567014b23b38c76e764a7f9`. Remote freshness is unverified:
`git fetch origin main` was NOT_RUN because the supervisor explicitly prohibits
network/GitHub actions. Read-only git status, branch, rev-parse, diff and hash-object
were used. Initial worktree was clean. The supplied node/design is the task input;
no task document was created or changed under docs/tasks.

Implementation/final committed task head is UNASSIGNED: this is an uncommitted
patch over the above HEAD. No commit, push, PR, issue/comment, merge, branch/tag
mutation or GitHub/network action was performed. Merge commit/post-merge CI: N/A.

[preservation-before.json](preservation-before.json) and
[preservation-after.json](preservation-after.json) match for all 121 protected
files: both locked files, every file under reference/v0.3-rc1, .aiops and docs/tasks.
The executable [verify_preservation.py](verify_preservation.py) also compares every
protected byte/path to Git HEAD. Both required blobs match before and after:

| Locked path | Before / after Git blob |
|---|---|
| runtime/crates/kix-kernel/src/lib.rs | 69564b166f0c27f9af5d8422f0a466b18d74c20f |
| runtime/crates/kix-kernel/tests/quarantine_capacity.rs | b607996c83a119c349f1cc90469ac1ba82764e20 |

Complete changed-path list: [changed-paths.json](changed-paths.json). Code/docs:
reference/ai_delegation/delegation_console.py, test_delegation_console.py,
test_delegation_console_subprocess.py, README.md; two new fixtures
fixtures/delegation_console_guided_journey.txt and
delegation_console_guided_boundaries.txt; docs/README.md (only validation link).
Remaining additions are this validation directory's report, command/log records,
transcripts and preservation evidence. Client, CLI, session, mock, contract,
catalogue, CI, execution flags and existing fixture inputs are unchanged.

| Required gate | Status / run ID / conclusion |
|---|---|
| A2 non-author exact-final-head review | PENDING supervisor; builder evidence does not satisfy it |
| Exact-head KTX kernel verification | NOT_RUN / unavailable / none; no final commit or publication |
| Exact-head KIX protocol verification | NOT_RUN / unavailable / none; no final commit or publication |
| Merge and post-merge main/push CI | N/A; not authorized or performed |

No older SHA's CI is transferred. STATUS READY means local builder delivery only;
it grants no merge authorization or merge-ready verdict.

## Deviations, discrepancies, uncertainty and non-claims

Plan deviations: supervisor no-network/no-publication rules replace fetch and
GitHub delivery with a locally observed, freshness-unverified base and uncommitted
patch. The five offline Cargo dependency checks are unavailable due to missing
cached bcs, as above; formatting and applicable Python/document/architecture
checks pass. No implementation/design scope deviation or new decision needed.

No new explicit contract violation or undefined business behavior was found.
Existing class-C A5 remains unresolved: mock registration → tool list → binding
order differs from contract §7. The new transcripts exclude the registered wrong
agent plus denied/unknown tool precedence case. Its owner remains Astra, with User
authorization for resulting scope/contract changes, per the
[October 26 addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure).
Missing-grant binding remains UNDETERMINED with the same owner. No precedence
repair or full contract-conformance claim is made.

Product limits/surfaces/proposal kinds remain UNDETERMINED — Astra; identity
policy UNDETERMINED — Astra/User; legal effects UNDETERMINED — User/legal.
Every input is caller-supplied; synthetic fixtures decide none of these values.
EXECUTE remains refused, human approval inert, all eleven flags and proposal
effects_executed false. No real funds/provider/bank/KYC calls, sockets/public
endpoints, credentials, production runtime, Sui network, storage engine,
replication/consensus, coin/TIX module or new protocol command was needed or added.
No durability, distributed fencing, bank exactly-once, chain finality, legal
compliance, production readiness or capability-grade increase is claimed.

Follow-up belongs to the supervisor: commit/publication, exact-final-head
non-author A2 review and required KTX/KIX CI including Rust verification in a
qualified environment. A5 disposition remains a separate Astra/User decision.

Final report checks: `python3 scripts/check_docs_index.py` passed (scanned=373, indexed=338, allowlisted=35; [log](final-docs-index.log)); `git diff --check` passed ([log](final-diff-check.log)). Their exact argv/results are also in commands.jsonl.
