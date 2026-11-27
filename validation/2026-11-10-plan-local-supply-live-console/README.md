# plan-local-supply-live-console — local builder evidence

Task input: the supervisor's inline node specification and read-only design plan;
no issue or task document exists. This is not ASTRA program mode. Branch:
`agent/kix-plan-local-supply-live-console`.

Observed local `origin/main`, base, initial implementation HEAD and unchanged
final Git HEAD: `25e7f2ebaa08e3688a92b36ad3025325b5011d84`. These changes are
uncommitted. No final committed task head or merge commit exists. The supervisor
owns commits/publication. Fetch was deliberately omitted under its explicit
no-network rule; remote freshness is unverified, and no base delta was observed
between the available local ref and HEAD.

The implementation adds a reusable one-request-per-child supply client and an
explicit console subprocess mode. Event composition/invalidation stays in the
console. Calculations and classifications stay in the unchanged service/model.
A successful report is forwarded whole into an explicitly confirmed comparison
with caller-entered synthetic chain supply. Construction launches nothing.
Uncertainty permanently fences the client, without retry or fallback.

## Existing coverage mapping (before new tests)

| Requirement | Existing coverage | Initial assessment / new gap evidence |
|---|---|---|
| Supply arithmetic, burns, alarm classifications | `test_reward_model.SupplyTests.test_v6_supply_recompute_and_alarm_classes`; `test_tl4_model_properties.SupplyPropertyTests` | Sufficient; reused without duplicating arithmetic |
| Exact CLI envelopes, domain codes, file/stdin exits | `test_supply_cli.SupplyCliTests`; `test_supply_reconciliation.SupplyDispatchTests` | Sufficient for CLI/service; reusable transport was uncovered |
| Six successful console journeys | `test_supply_console.SupplyConsoleTests.test_fixture_journeys_complete_parity_identity_and_single_calls`; terminal fixtures | Partial: now replayed through real subprocess mode |
| Whole report forwarding | `SupplyConsoleTests.test_full_report_forwarded_without_repair_or_metadata_loss` | Sufficient in-process; new live boundary identity/content and wire snapshot tests |
| Edit, failed/cancelled edit, recalculation invalidation | `SupplyConsoleTests.test_edits_invalidate_immediately_and_stage_without_partial_install`; `test_recalculation_decline_cancel_or_failure_cannot_reuse_old_selections` | Sufficient in-process; new live invalidation and no-old-report dispatch tests |
| Preview/cancellation/decline/invalid input do not calculate | Existing console prompt/IO tests and boundary fixture | Partial: new live launch-count checks and failed-preview test |
| Strict reply decoding, exit agreement, request correlation | No supply client existed | Uncovered: malformed JSON/Unicode/duplicates/non-finite values, exact fields/types/metadata, events/chain correlation, mismatched exits tested |
| Transport uncertainty, single outstanding request, child cleanup | Pool client precedent only; different persistent JSONL interface | Uncovered: new supply tests for launch/I/O/interruption failures, retained evidence, permanent fencing, busy/closed rejection, terminate/kill and real child reaping |
| Existing console behavior | Full `SupplyConsoleTests` and `SupplyConsoleSubprocessTests` | Sufficient and retained; terminal test subclass replays all existing terminal regressions in subprocess mode |

New boundary tests are in `test_supply_client.py`, `SupplyConsoleLiveTests` and
`SupplyConsoleLiveSubprocessTests`. They are builder-authored/source-informed;
no independent-review claim is made.

## Commands and results

The machine-readable [command ledger](commands.jsonl) records exact verification
commands, exit codes and per-command full output captures (`check-*.log`).
Python 3.12.15 is used for verification, matching CI's Python 3.12 family;
default `python3` is 3.13.5. Cargo and rustc are 1.98.1.

The [in-process captures](transcripts-in-process.jsonl) and
[subprocess captures](transcripts-subprocess.jsonl) each contain nine complete
terminal fixture journeys, including stdin paths, argv, complete stdout/stderr
and actual exits. Reproduce with [capture_transcripts.py](capture_transcripts.py).
All jobs run in the foreground. No CI or workflow files are changed.

The narrow suite runs first. An initial local capture helper allocated one log
filename twice during overlapping independent checks; that mixed capture was
discarded and both affected checks rerun. The ledger retains the actual commands
and observed exit codes with a capture note. The helper now reserves log names
exclusively. Final clean captures are linked in the result table below.

Final review found and fixed a transport edge case: an I/O error after child exit
can still leave open pipes, and exception-carried output bytes must survive that
cleanup. A focused regression checks pipe closure and byte retention. The narrow
and full suites were rerun after the correction.

## Boundaries, deviations and remaining gates

No contract violation found. Simultaneous unapproved mint/path behavior retains
the existing class-B `UNAPPROVED_PATH` precedence characterization; TL-4 §6.B
leaves policy precedence undefined. No semantics or authoritative contract changes.

Design deviations: no functional scope change. Offline kernel test and Clippy
commands cannot resolve the workspace because the local crates.io cache lacks
`bcs` (required by `kix-bcs1`), so both exit 101 before testing/linting. No fetch,
installation or network fallback was attempted. Formatting and architecture
checks do run successfully. The implementation touches no Rust paths.
Fetch is omitted per supervisor;
no task document is created. No commit, push, PR, issue, comment or network action
is performed. Verification uses Python 3.12 explicitly rather than default Python.

KTX exact-head CI: not run; run ID/status/conclusion unavailable.
KIX protocol exact-head CI: not run; run ID/status/conclusion unavailable.
Post-merge CI and final-merge blob checks: not applicable (no merge).
A2 non-author exact-head review and successful exact-head workflows remain
supervisor delivery gates. READY here denotes local builder handoff only,
not merge readiness, independent PASS or any capability-grade increase.

No production, chain, public endpoint, socket, external service, funds, bank/PG/KYC,
new dependency, receipt digest, public schema, protocol command or runtime
activation is introduced or tested. No full protocol CI, Move, ZK, SDK, durability,
authenticity, distributed fencing or operational-policy verification is claimed.
`stop_payout` remains reported data. Supply policy and operational responses
remain **UNDETERMINED — Astra/User**. A blocking calculation still needs caller
interruption; cleanup timeout is not a response deadline.

## Protected paths and complete delivery paths

[Before manifest](protected-before.json) and [after manifest](protected-after.json)
cover 110 protected files, including all files under `reference/v0.3-rc1/**` and
both locked kernel files. The file sets and SHA-256 values match byte for byte.
[verify_preservation.py](verify_preservation.py) also verifies the required Git
blobs and unchanged CLI/service/model, CI, `.aiops/`, and task documents against
HEAD. Both locked blobs match before and after:

| Path | Required / observed before / observed after Git blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

The complete [changed-path list](changed-paths.txt) includes these seven delivery
source/document paths and every new validation artifact:

- `reference/token_reward/supply_client.py` — reusable binary subprocess client.
- `reference/token_reward/supply_console.py` — explicit mode and cleanup options.
- `reference/token_reward/test_supply_client.py` — strict decoding, live parity,
  lifecycle, retained uncertainty and fencing tests.
- `reference/token_reward/test_supply_console.py` — live dispatch and selection boundaries.
- `reference/token_reward/test_supply_console_subprocess.py` — both-mode terminal replay.
- `reference/token_reward/README.md` — CLI/client usage, exits, lifecycle and scope.
- `docs/README.md` — usage and validation index pointers.

Remaining uncertainty/follow-up: supervisor-owned A2 review and exact committed
HEAD CI, plus offline Rust dependencies if kernel checks are to run locally.
No new product decision is required for this local implementation. Cleanup
failure diagnostics remain uncertainty; they do not establish rejection or
permit resubmission. The tests are source-informed boundary checks, not an
independent report oracle or proof of OS behavior under every failure.

## Final local verification results

Commands below were actually run; prior runs and capture notes remain in the ledger.

| Command | Actual result | Full output |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/token_reward python3.12 -m unittest test_reward_model.SupplyTests test_tl4_model_properties.SupplyPropertyTests test_supply_reconciliation test_supply_cli test_supply_client test_supply_console test_supply_console_subprocess` | PASS: 59 tests | [check-30.log](check-30.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS: 370 tests | [check-31.log](check-31.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_docs_index.py` | PASS (exit 0) | [check-29.log](check-29.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_docs_index.py --self-test` | PASS (exit 0) | [check-05.log](check-05.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_tl_predicate_evidence_map.py` | PASS (exit 0) | [check-06.log](check-06.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_tl_predicate_evidence_map.py --self-test` | PASS (exit 0) | [check-07.log](check-07.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_class_b_index.py` | PASS (exit 0) | [check-08.log](check-08.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_class_b_index.py --self-test` | PASS (exit 0) | [check-09.log](check-09.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_ci_checker_wiring.py` | PASS (exit 0) | [check-10.log](check-10.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_ci_checker_wiring.py --self-test` | PASS (exit 0) | [check-11.log](check-11.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_ci_test_discovery.py` | PASS (exit 0) | [check-12.log](check-12.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_ci_test_discovery.py --self-test` | PASS (exit 0) | [check-13.log](check-13.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_openapi_contract.py` | PASS (exit 0) | [check-15.log](check-15.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_openapi_contract.py --self-test` | PASS (exit 0) | [check-16.log](check-16.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_integration_gate_openapi.py` | PASS (exit 0) | [check-17.log](check-17.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/check_integration_gate_openapi.py --self-test` | PASS (exit 0) | [check-18.log](check-18.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/verify_runtime_architecture.py` | PASS (exit 0) | [check-19.log](check-19.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/test_runtime_architecture.py` | PASS: 7 tests | [check-20.log](check-20.log) |
| `PYTHONDONTWRITEBYTECODE=1 cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE: missing offline bcs; exit 101 before checks | [check-21.log](check-21.log) |
| `PYTHONDONTWRITEBYTECODE=1 cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE: missing offline bcs; exit 101 before checks | [check-22.log](check-22.log) |
| `PYTHONDONTWRITEBYTECODE=1 cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | PASS (exit 0) | [check-23.log](check-23.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 validation/2026-11-10-plan-local-supply-live-console/capture_transcripts.py` | PASS: 18 complete journeys | [check-32.log](check-32.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 validation/2026-11-10-plan-local-supply-live-console/verify_preservation.py` | PASS: 110 files byte-identical; both required Git blobs match | [check-33.log](check-33.log) |
| `PYTHONDONTWRITEBYTECODE=1 git diff --check` | PASS (exit 0) | [check-34.log](check-34.log) |
| `PYTHONDONTWRITEBYTECODE=1 git rev-parse origin/main HEAD` | PASS (exit 0) | [check-27.log](check-27.log) |
| `PYTHONDONTWRITEBYTECODE=1 git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | PASS (exit 0) | [check-28.log](check-28.log) |

## PR fix round 1 — reconciliation response correlation

This section records the follow-up to the supplied blocking review; the original
builder evidence above remains historical. Task ID: `plan-local-supply-live-console`;
task document: the supervisor's inline specification (no issue or `docs/tasks/`
document exists). Branch: `agent/kix-plan-local-supply-live-console`.
Observed local `origin/main` and merge base:
`25e7f2ebaa08e3688a92b36ad3025325b5011d84`. Implementation HEAD at entry and
unchanged Git HEAD at handoff: `df1e9dd1e189a6ad622f1e4c6cd1a0532473bf73`.
The fix is uncommitted; a final committed fix head and merge SHA do not exist.
Fetch and all network/publication actions are omitted under the supervisor's
explicit instruction. Remote freshness is unverified; the local base matches
the earlier builder base. No commit, push, comment, branch change or merge occurs.

The blocking finding is confirmed and fixed. A successful reconciliation reply
must now return `offchain_supply` equal to the submitted report's `layer_supply`.
The comparison uses the submitted field directly, without recalculating supply
or classifying alarms. Disagreement follows the existing decode-uncertainty path,
which retains the complete observation and permanently fences further requests.

Coverage mapping before this fix: arithmetic/classifications, real subprocess
journeys, report forwarding, event invalidation, confirmation boundaries and
in-process behavior were sufficiently covered by the tests mapped above.
Reconciliation correlation was partially covered: chain input and amount types
were checked, but the old test explicitly accepted an offchain mismatch.
`SupplyClientTests.test_offchain_supply_mismatch_retains_evidence_and_fences`
replaces that acceptance with the review's `99` versus `7` reproduction. It
checks uncertainty phase, request bytes, complete stdout/stderr, child exit,
retained uncertainty identity, and rejection of both repeated reconciliation
and a subsequent report request with only one child launch. This closes the
documented gap; existing arithmetic and console tests are reused unchanged.

| Evidence / command actually run | Result | Capture |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/token_reward python3.12 -m unittest test_supply_client.SupplyClientTests.test_offchain_supply_mismatch_retains_evidence_and_fences` before implementation fix | Expected FAIL: uncertainty not raised (exit 1) | [regression-before.log](fix-round-1/regression-before.log) |
| Same regression command after implementation fix | PASS: 1 test (exit 0) | [regression-after.log](fix-round-1/regression-after.log) |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/token_reward python3.12 -m unittest test_reward_model.SupplyTests test_tl4_model_properties.SupplyPropertyTests test_supply_reconciliation test_supply_cli test_supply_client test_supply_console test_supply_console_subprocess` | PASS: 60 tests (exit 0) | [focused.log](fix-round-1/focused.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | PASS: 371 tests (exit 0) | [discovery.log](fix-round-1/discovery.log) |
| Documentation index, TL predicate evidence map, class-B index, checker wiring and test discovery, each plain and `--self-test` | PASS: all 10 commands (exit 0 each) | [Exact argv and results](fix-round-1/checks.jsonl), `check-01.log` through `check-10.log` |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/verify_runtime_architecture.py` | PASS (exit 0) | [check-11.log](fix-round-1/check-11.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 scripts/test_runtime_architecture.py` | PASS: 7 tests (exit 0) | [check-12.log](fix-round-1/check-12.log) |
| `PYTHONDONTWRITEBYTECODE=1 python3.12 validation/2026-11-10-plan-local-supply-live-console/verify_preservation.py` | PASS: 110 protected files unchanged, both locked blobs match | [check-13.log](fix-round-1/check-13.log) |
| `git diff --check` | PASS (exit 0) | [check-14.log](fix-round-1/check-14.log) |

Both kernel Git blobs matched the required values before editing and after
the fix: `69564b166f0c27f9af5d8422f0a466b18d74c20f` (`src/lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`tests/quarantine_capacity.rs`).
All 110 protected-file hashes match the original before/after manifests,
including `reference/v0.3-rc1/**`. The CLI, service, model, CI, `.aiops/`, and
task documents remain unchanged from entry HEAD.

Complete round-1 changed paths are listed in
[changed-paths.txt](fix-round-1/changed-paths.txt). Source/document edits are
limited to `reference/token_reward/supply_client.py`,
`reference/token_reward/test_supply_client.py`,
`reference/token_reward/README.md`, and this validation README; all other
round-1 paths are validation logs/ledgers/path evidence under `fix-round-1/`.

No remaining model-contract violation or new undefined behavior was found.
The reviewed issue was a client task-acceptance gap; the model contract and
arithmetic are unchanged. Existing simultaneous-unapproved-cause precedence
remains the class-B characterization documented above. Policy and operational
responses remain **UNDETERMINED — Astra/User**; `stop_payout` remains data.

No CI failure log was supplied. KTX and KIX exact-head CI run IDs, statuses and
conclusions are unavailable and were not queried. Post-merge CI and merge-blob
checks are not applicable. Rust, Move, ZK, SDK and full protocol CI are not rerun
for this Python-only correction; prior Rust cache limitations above remain
historical. This is source-informed local builder evidence, not independent
A2 approval or merge readiness. Supervisor-owned committed-head review and CI
remain delivery gates. No production, chain, external services, sockets, funds,
credentials, new dependency, policy default or runtime activation is introduced.

Round-1 outcome: **STATUS: READY** for local builder handoff. The final
[documentation and whitespace checks](fix-round-1/final-checks.log) pass after
this evidence update. READY does not authorize merge.
