# Live synthetic pool client — builder evidence

Node `plan-local-pool-live-console`. Task input: supervisor-supplied node and design
in this session; no issue/task document exists. Single writer, uncommitted patch.
Base, starting HEAD and cached origin/main: `992bb392a890508ce8736fc5c63159de789c53ea`.
Branch: `agent/kix-plan-local-pool-live-console`. No base delta locally.
Fetch omitted under the explicit supervisor no-network rule; freshness unverified.

## Coverage map recorded before new tests

All symbols below are in `reference/token_reward/`.

| Requirement | Existing coverage / classification | Gap to close |
|---|---|---|
| Persistent incremental child journey | Partial: `test_pool_cli.PoolCliTests.test_real_file_and_stdin_journey_match_direct_model` | Client handshake and exchanges before EOF; complete envelopes |
| Forbidden obligation spend, exhaustion | Sufficient semantics: `test_pool_session.PoolSessionTests.test_all_ordinary_rejections_preserve_full_snapshot_and_precedence`, `test_pool_cli.PoolCliTests.test_real_boundaries_keep_state_and_original_codes` | Live transport parity using the same boundary fixture |
| Repeated references append again | Sufficient semantics: `test_pool_session.PoolSessionTests.test_repeated_refs_match_direct_model_and_append_again` | Incremental client and console journey parity |
| Declined initialization/mutations | Partial: `test_pool_console.PoolConsoleTests.test_decline_initialization_does_not_construct_any_ledger`, `test_declined_mutations_and_eof_at_every_prompt_do_not_dispatch` | Confirm before child launch/write; output failures and interruption |
| Handshake, strict framing, complete metadata | Not covered at new boundary | Invalid acknowledgements, fixture changes, wrong shapes/flags/operation |
| Broken pipes, missing replies, fencing, cleanup | Not covered for pool client | Retained evidence, no retry/replacement, startup reap, idempotent/escalated cleanup, concurrency rejection |
| Existing fixture and guided modes | Sufficient: `test_pool_console.py`, including `test_guided_opening_journey_matches_fixture` and `test_real_guided_journey_and_boundaries` | Default/explicit in-process parity; subprocess fixtures |
| Stdlib/discovery/architecture | Partial: session import allowlist and CI checkers | Extend exact module list; execute existing checks |

Predecessor evidence read: `validation/2026-11-09-plan-plan-local-pool-accounting-workbench/README.md`
and `validation/2026-11-09-plan-local-pool-opening-composer/README.md`.

## Implementation and gap closure

`pool_client.py` owns one persistent, synchronous `pool_cli.py` child. It checks
confirmed inputs before launch and validates the existing initialization response
before accepting requests. Every response retains the whole service envelope,
synthetic provenance, POINT_F4 unit, notice and literal false flags. Request shape
validation forwards finite domain values unchanged. The client never recalculates
balances or supplies funding/policy defaults. No service, ledger or fixture changed.

`pool_console.py` shares its existing action loop across default/explicit in-process
and explicit subprocess modes. The opening snapshot is detached before preview.
Launch follows literal SUBMIT; mutations follow their own literal SUBMIT; views
are explicit reads. Subprocess mode requires a fixture and explicit finite positive
cleanup timeout. Guided initialization remains in-process. Cleanup runs on every
post-launch path and unexpected child exits are terminal failures.

New source-informed tests close the mapped transport/integration gaps:

| Test path / symbols | Evidence added |
|---|---|
| `test_pool_client.py`: `test_real_incremental_journeys_complete_envelopes_one_child`, `test_real_domain_types_and_repeated_refs_remain_model_inputs` | Real child initialization/credit/spend/view before EOF, one launch, exact complete envelope parity, boundary refusal/state parity, exact finite types and repeated references |
| `test_initialization_failures_reap_without_request_submission`, `test_changed_fixture_at_child_start_fences_acknowledgement`, `test_invalid_timeout_fixture_or_confirmed_snapshot_launches_nothing` | Missing/malformed/wrong ack, type-sensitive snapshot comparison, all seven false flags, changed fixture, no request on startup failure, reap |
| `test_malformed_response_matrix_fences_with_exact_evidence`, `test_write_flush_and_partial_read_faults_retain_snapshot_without_retry` | Framing, UTF-8/duplicate keys/nonfinite input, operation/metadata/payload shapes, pipe/short-write/read/interruption failure, retained exact snapshot and partial bytes, no second submission |
| `test_lost_ack_after_real_accepted_mutation_fences_without_rollback` | An actual accepted child credit is observed by the fault injector, then its acknowledgement is lost to the client; subsequent submission is rejected; cleanup makes no rollback claim |
| `test_invalid_requests_fail_locally_without_fencing_or_coercion`, `test_typed_service_error_is_preserved_and_terminal` | Local shape failure sends nothing and permits a later explicit request; full typed errors are preserved and fence use |
| `test_overlap_rejects_request_and_cleanup_before_second_write`, `test_cleanup_escalation_and_interruption_reap_once` | Reject overlap; idempotent cleanup, terminate/kill escalation and interrupted cleanup reap the owned child |
| `test_pool_console_subprocess.py`: `test_real_console_modes_have_identical_complete_journeys`, `test_launch_and_mutation_follow_flushed_confirmation_only` | Real fixture/default/explicit/live transcript parity, one live child, declined mutations send nothing, initialization has no implicit read |
| Other subprocess-console tests | No launch on decline/EOF/interruption/initial output failure, detached preview snapshot, no sends after incomplete input/preview failure, no second action after output/transport failures, cleanup on all post-launch exits, unexpected-exit and option-combination rejection |

The import guard changes only its exact helper allowlist and inspected module tuple;
the AST walk and stdlib/selected-local assertion remain intact.

## Actual local validation

[Command → result table](command-results.md) and [machine-readable ledger](commands.jsonl)
record actual commands, exit codes and log names. All validation Python commands
use `PYTHONDONTWRITEBYTECODE=1`. The first focused run passed 56 tests; after two
additional snapshot/output boundary tests, the final focused run passed 58 tests.
Full default Python 3.13.5 token-reward discovery passed 346 tests, as did the
CI Python 3.12.15 interpreter (346 tests). Architecture
verification and its 7 regressions passed. All seven applicable checkers (docs
index, TL predicate evidence, Class B index, CI wiring, discovery, OpenAPI contract,
integration-gate OpenAPI) passed normal and self-test modes. Rust formatting passed.

The kernel test, workspace test and workspace Clippy commands each exited 101
before compilation: the offline crates.io cache lacks `bcs`. These are
**unavailable, not passing**. No dependency acquisition or CI changes were made.
Rust paths are untouched. Cache provisioning and those remaining Rust checks
belong to the supervisor's delivery environment.

Captured real console transcripts use caller-selected existing fixture inputs:

| Mode | Journey | Boundary journey |
|---|---|---|
| Subprocess | [stdout](subprocess-journey.stdout), [stderr](subprocess-journey.stderr), exit 0 | [stdout](subprocess-boundaries.stdout), [stderr](subprocess-boundaries.stderr), exit 1 |
| Explicit in-process fixture | [stdout](in-process-journey.stdout), [stderr](in-process-journey.stderr), exit 0 | [stdout](in-process-boundaries.stdout), [stderr](in-process-boundaries.stderr), exit 1 |
| Guided initialization | [stdout](guided-journey.stdout), [stderr](guided-journey.stderr), exit 0 | [stdout](guided-boundaries.stdout), [stderr](guided-boundaries.stderr), exit 1 |

All six transcript stderr captures are empty. [Transcript comparison](verify_transcripts.py) passed: 8 journey and 6 boundary
envelopes match across modes;
boundaries retain the three forbidden obligation-pool refusals and exhausted-funds
refusal. Existing fixtures include declines and repeated accepted source/program refs.

## Preservation and changed paths

Before editing, both locked kernel working-file Git hashes matched:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

[Preservation checker](verify_preservation.py) compares the
[captured protected bytes](protected-before.json) and each file at unchanged HEAD,
including both locks, `reference/v0.3-rc1/**`, `.aiops/**`, `docs/tasks/**` and workflows.
All 123 protected files matched their captured bytes and unchanged HEAD.
It verifies the locked Git blobs again and restricts changed paths to the seven
implementation/test/document paths plus this evidence directory.
[Complete changed-path list](changed-paths.txt) includes every evidence artifact.
PoolLedger, pool_session.py, pool_cli.py, reward_client.py and existing fixtures
remain byte-identical to HEAD under the same scope check.

## Limits, deviations and supervisor gates

No explicit contract violation was found. Repeated-reference append behavior is
an existing characterization, not an idempotency guarantee. The tests are
source-informed service/transport comparisons, not independent conformance proof.
No new accounting or funding semantics were invented: pool balances/funding policy
remain caller-supplied synthetic inputs / **UNDETERMINED — Astra/User**;
accounting treatment remains **UNDETERMINED — User/designated advisers**.

No sockets, external services, secrets, paid services, real funds/providers/KYC,
production runtime, Sui testnet/mainnet, issuance, coin/TIX module, storage engine,
replication, consensus, receipts, deduplication, reward coupling or new protocol
commands were added or tested. No durability, rollback after lost acknowledgement,
chain finality, legal authority or production-readiness claim is made. Reads have
no product response deadline; test-only thread deadlines verify replies before EOF.
Unrelated chain/bootstrap/artifact-generation CI stages were intentionally not run.

Design implementation deviation: none in service/ledger semantics. A detached
console opening snapshot and preservation of the original startup uncertainty
if cleanup itself is interrupted strengthen the specified confirmation/evidence
boundaries. Fetch was omitted under the later supervisor prohibition. An initial
protected-file capture failed because newline-delimited Git paths were quoted for
a Unicode filename; the capture was corrected to NUL-delimited paths before tests.
No protected file was written. An ad hoc whole-stdout comparison initially failed
because guided initialization adds opening-entry prompts; the corrected comparison
checks complete decoded service envelopes across all modes and byte-identical
stdout for fixture/live modes. That comparison passed. Evidence began on 2026-11-09 and completed after
the session date advanced to 2026-11-10; the original directory date is retained.

Implementation/final committed head: not created; HEAD remains the starting SHA
above with this uncommitted patch. The supervisor owns commits and publication.
Merge commit/main-push/post-merge verification: not applicable; no merge occurred.
Exact-head KTX run ID/status/conclusion: NOT_RUN / unavailable in this session.
Exact-head KIX run ID/status/conclusion: NOT_RUN / unavailable in this session.
Non-author A2 exact-final-head review: pending supervisor delivery. Local passes
are builder evidence and authorize no merge. There was no GitHub/network action,
commit, push, PR/issue/comment, marker, branch or tag operation.
