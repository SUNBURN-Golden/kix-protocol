# plan-plan-local-reward-live-console — local builder evidence

Task input: the supervisor-supplied node specification and read-only design in
this session; no issue or task document under `docs/tasks/` exists for this node.
This is not ASTRA program mode. Builder-authored, source-informed composition
evidence only; no independent review, capability grade change or merge approval.

## Identity and preservation

Branch: `agent/kix-plan-plan-local-reward-live-console`. Locally observed
`origin/main`, initial task HEAD and task base all equal
`c3c5c001dd46c581b3414b98fc2f1c196baf9a3e`; no observed local delta.
The supervisor prohibits all network/GitHub actions and owns Git publication,
so the §1 fetch was not performed and remote freshness remains unverified.
No commit, push, PR, issue, comment, tag, branch mutation or merge was performed.
Implementation/final committed head remains unassigned; HEAD stays at the initial
SHA plus this uncommitted patch. No merge commit or post-merge checks apply.

Before edits, `git hash-object` verified locked kernel blobs
`69564b166f0c27f9af5d8422f0a466b18d74c20f` and
`b607996c83a119c349f1cc90469ac1ba82764e20`.
[preservation-before.json](preservation-before.json) records pre-edit SHA-256
hashes for the protected reference tree, `.aiops/`, `.github/`, `docs/tasks/`,
locked kernel files and unchanged token_reward implementation/fixture files.
After work, membership and all 153 file hashes match; all 108 protected
`reference/v0.3-rc1/` files remain byte-identical. Its HEAD Git tree is
`a6ecb124dc2b2267ca6be19e39fbe2aef143074b`. Both locked Git blobs still match
the required values above, and the protected path diff is empty. The final
comparison source and output are retained in `commands.json`.

## Coverage mapped before adding tests

All test paths below are under `reference/token_reward/`.

| Acceptance | Existing coverage classification and exact source | Composition gap addressed |
|---|---|---|
| Journey, reads and historical receipts | Partial: `test_reward_console.py::test_success_transcript`; `test_reward_client.py::test_live_participation_before_eof_and_response_derived_reads` | `test_live_console_journey_before_eof` incrementally supplies the next selection only after a full reply, checks open child stdin, one launch, complete public-session envelope parity, historical replay and single pool spend |
| UNKNOWN, cancellation and refund distinct | Sufficient underlying semantics; partial composition: client `test_live_unknown_requires_separately_supplied_resolution`, `test_live_cancellation_and_krw_refund_are_distinct`; console `test_other_selectors_and_explicit_unknown_resolution` | `test_live_console_scenario_parity` reuses cancellation, pending UNKNOWN, separate resolution, boundary and supersession inputs and exercises all twelve selectors |
| Confirmation and exact inputs | Partial: console `test_all_mutations_literal_confirmation_and_fresh_fields`, `test_omitted_null_optionals_and_opaque_metadata_forward_unchanged` | `test_client_confirmation_dispatch_counts` checks every mutation, declines send nothing and confirmations send once; `test_optional_omission_null_and_opaque_inputs_reach_child` compares actual wire bytes decoded with caller records |
| Domain errors visible and sticky | Partial: console `test_boundary_transcript_sticky_exit`; client `test_live_boundary_refusals_allow_only_explicit_continuation` | Live scenario and CLI parity tests preserve every refusal and explicit continuation; `test_client_error_envelopes_and_status` stops on terminal setup/typed envelopes unchanged |
| Uncertainty fences forever | Sufficient client behavior; partial composition: client malformed/exited, short-write and interruption tests | `test_uncertainty_stops_and_preserves_evidence`, `test_partial_reply_interruption_and_short_write_stop` queue more actions, verify one request, no replacement/fallback, exact detached request/wire/reply bytes and exception chain; retained client rejects later use |
| Explicit inputs, cleanup ownership | Client timeout validation and terminate/kill/reap coverage sufficient; console ownership not covered | `test_subprocess_options_and_mode_isolation`, `test_quit_eof_interrupt_and_render_failure_reap`, `test_eof_at_confirmation_reaps_without_sending`, `test_invalid_fixture_is_terminal_and_reaped_without_fallback`, cleanup-primary diagnostic and unexpected-exit tests |
| False flags and compatibility | Sufficient underlying coverage: console import/no-child, client synthetic assertions and complete fixture suites | Composition parity checks POINT_F4, non-transferability and all seven false flags; `test_cli_transcripts_match_default_in_process` compares complete stdout and exit codes |

## Complete changed-path list

- `reference/token_reward/reward_console.py`: explicit mode/options, shared prompt
  loop, one-client ownership, terminal error handling, cleanup and diagnostics.
- `reference/token_reward/test_reward_console_subprocess.py`: fifteen composition
  tests; the existing console's fourteen tests remain unchanged and passing.
- `reference/token_reward/README.md`: both modes, lifetime, statuses and limitations.
- `docs/README.md`: usage/evidence links with no grade change.
- `validation/2026-11-07-plan-plan-local-reward-live-console/README.md`
- `validation/2026-11-07-plan-plan-local-reward-live-console/commands.json`
- `validation/2026-11-07-plan-plan-local-reward-live-console/preservation-before.json`
- `validation/2026-11-07-plan-plan-local-reward-live-console/journey.stdout.txt`
- `validation/2026-11-07-plan-plan-local-reward-live-console/journey.stderr.txt`
- `validation/2026-11-07-plan-plan-local-reward-live-console/boundaries.stdout.txt`
- `validation/2026-11-07-plan-plan-local-reward-live-console/boundaries.stderr.txt`
- `validation/2026-11-07-plan-plan-local-reward-live-console/uncertainty.stdout.txt`
- `validation/2026-11-07-plan-plan-local-reward-live-console/uncertainty.stderr.txt`

New tests reside in `test_reward_console_subprocess.py::RewardConsoleSubprocessTests`.
Existing FSM/serialization and client transport tests are reused without new
business rules or duplicate economic oracles. Event waits/joins and subprocess
harness deadlines are test safeguards only, not product response policy.

## Verification

[commands.json](commands.json) retains actual verification argv, exit codes,
elapsed times, stdout and stderr, including failed development runs. Python
bytecode writes were disabled through `PYTHONDONTWRITEBYTECODE=1`, inherited by
children. Default Python is 3.13.5; final narrow and full discovery also ran on
workflow-equivalent Python 3.12.15. Rust is the workflow-pinned 1.98.1.

| Command | Actual result |
|---|---|
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward -p 'test_reward_console*.py'` | exit 0; 29 tests passed |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 228 tests passed, including existing client/console regressions |
| `python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode subprocess --cleanup-timeout 1 < reference/token_reward/fixtures/reward_console_journey.txt` | expected exit 0; complete stdout captured, empty stderr |
| Same console command with stdin `reward_console_boundaries.txt` | expected exit 1; complete refusal/read envelopes captured, empty stderr |
| `python3.12 /tmp/kix-live-console-uncertainty.py` (source retained in JSON) | expected exit 2; owned fault child supplies partial invalid bytes `7bff`; queued read never sent; complete FENCED diagnostic captured |
| `python3 scripts/check_docs_index.py` and `--self-test` | both exit 0; plain check scanned=368, indexed=333, allowlisted=35 |
| `python3 scripts/check_status_register.py` and `--self-test` | both exit 0 |
| `python3 scripts/check_tl_predicate_evidence_map.py` and `--self-test` | both exit 0; 49 rows unchanged |
| `python3 scripts/check_class_b_index.py` and `--self-test` | both exit 0; textual index only |
| `python3 scripts/check_ci_test_discovery.py` and `--self-test` | both exit 0; all 14 token_reward test files reached by workflow discovery |
| `python3 scripts/check_ci_checker_wiring.py` and `--self-test` | both exit 0 |
| `python3 scripts/check_openapi_contract.py` and `--self-test` | both exit 0; 84-command pin unchanged |
| `python3 scripts/check_integration_gate_openapi.py` and `--self-test` | both exit 0; productionEndpoint/publicHost false |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; architecture/dependency boundary accepted; no durability/performance certification |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; offline cache lacks `bcs`; tests did not execute |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; same dependency-resolution failure; lint did not execute |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 101; same dependency-resolution failure; tests did not execute |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 101; same dependency-resolution failure; lint did not execute |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `python3.12 /tmp/kix-live-console-preservation.py` (source retained in JSON) | exit 0; all 153 hashes/membership match, 108 protected reference files, required locked blobs match, protected path diff empty |
| `git diff --check` | exit 0 |

The initial narrow run passed all 14 existing console tests. The first composed
run had one test setup failure: the test incorrectly expected the valid default
in-process mode to be rejected. Corrected that test; the next Python 3.13 narrow
run passed 28 tests and full discovery passed 227. Added the explicit client-state
failure case, then final Python 3.12 narrow/full discovery passed 29/228 as above.
No failing result was removed from the command history.

The two normal CLI captures are [journey.stdout.txt](journey.stdout.txt) and
[boundaries.stdout.txt](boundaries.stdout.txt), with empty corresponding stderr
files. They match the default in-process console byte-for-byte in the CLI parity
test. [uncertainty.stdout.txt](uncertainty.stdout.txt) and
[uncertainty.stderr.txt](uncertainty.stderr.txt) retain the deliberately malformed
exchange and lossless diagnostic evidence, with no subsequent desk reply.

The four Rust test/Clippy commands are **unavailable checks, never passes**.
They fail at dependency resolution, before tests or lint execute; no Rust code
changed. Network bootstrap is prohibited, so no dependency download was attempted.
The touched token_reward suite and applicable documentation/architecture checks
are green locally. Unrelated Move, Sui/localnet, ZK, storage and production jobs
were not run. A supervisor with an available dependency cache/CI must satisfy
remaining Rust/exact-head gates.

## Limitations and outstanding gates

No explicit contract violation found. Existing Class B late-fault, restoration
fingerprint, UNKNOWN approval-use and non-canonical-effect characterizations in
the reward guide remain unchanged. Startup setup-error/write races and blocking
response reads retain the existing client behavior. Cleanup cannot prove rollback.

All seven production flags remain false. No settlement sources, adapter, sockets,
external services, dependencies, persistence/storage engine, new command,
coin/TIX module, funds, provider calls, chain activity or runtime activation.
Policy amounts, caps, budgets and durations remain **UNDETERMINED — Astra/User**;
legal effects remain **UNDETERMINED — User/legal**. No independent economic,
production, durability, bank exactly-once, distributed-fencing or finality claim.

A2 non-author exact-final-head review, completed/success exact-head **KTX kernel
verification** and **KIX protocol verification** remain outstanding supervisor
gates. Run IDs/status/conclusions are unavailable: no committed delivery head or
network access in this session. No older CI result is transferred. No merge is
proposed. Ready-for-review and merge authorization remain with User.

Deviations: option/isolation tests are concentrated in the new subprocess test
module; the existing console test file is unchanged. Missing offline `bcs` blocks
Rust execution as described above. The explicit supervisor no-network/no-publication instructions replace
the startup fetch and publication steps. The task input is the supplied node,
not a manufactured issue or `docs/tasks/` file. No implementation design or scope expansion was needed.
