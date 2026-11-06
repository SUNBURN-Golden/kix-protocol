# plan-local-reward-stdio-client — local builder evidence

Task input: the supervisor-supplied node specification and read-only design in
this session. There is no task issue or `docs/tasks/` document for this node.
This is not ASTRA program mode. This record is builder-authored, source-informed
and is not independent A2 review or an acceptance/merge authorization.

## Identity and preservation

- Branch: `agent/kix-plan-local-reward-stdio-client`.
- Locally observed `origin/main`, task base and initial HEAD:
  `7623936f015aafb6a175b22beb72abe4ca338dc2` (equal; no local delta).
  `git fetch origin main` was not run: the supervisor explicitly prohibits every
  GitHub/network action. Remote freshness is unverified.
- Implementation/final committed HEAD: not created; the supervisor owns commits
  and publication. HEAD remains the initial SHA with this uncommitted patch.
- No merge commit; no PR, issue, comment, push, tag or branch mutation performed.
- Before work, `git hash-object` returned the required kernel blobs:
  `69564b166f0c27f9af5d8422f0a466b18d74c20f` (`src/lib.rs`) and
  `b607996c83a119c349f1cc90469ac1ba82764e20` (`tests/quarantine_capacity.rs`).
- Protected reference tree at initial HEAD:
  `a6ecb124dc2b2267ca6be19e39fbe2aef143074b` (`reference/v0.3-rc1`).
  A pre-change SHA-256 manifest of every tracked protected-reference, `.aiops/`,
  `.github/`, `docs/tasks/` and locked-kernel file was captured outside the repo.
  After work, all 125 manifest entries match, including all 108 tracked files
  under `reference/v0.3-rc1/`. Both kernel blobs still match the hashes above.
  Final comparison script, pre-change hashes and stdout are in `commands.json`.
  No runtime/model/session/fixture/contract/configuration diff was found.

## Scope and changed paths

1. `reference/token_reward/reward_client.py`: one child, synchronous explicit
   requests, strict replies, detached uncertainty evidence, fencing and cleanup.
2. `reference/token_reward/reward_cli.py`: only `_emit` gains `flush=True`.
3. `reference/token_reward/test_reward_client.py`: live and fault regressions.
4. `reference/token_reward/example_reward_client.py`: caller-selected transcript
   with the next view's reward ID derived from each receipt.
5. `reference/token_reward/README.md`: API, schemas, ownership, errors and example.
6. `docs/README.md`: client-guide and evidence links.
7. `validation/2026-11-06-plan-local-reward-stdio-client/README.md`: this report.
8. `validation/2026-11-06-plan-local-reward-stdio-client/commands.json`: actual
   verification commands, interpreter/environment, exit status, stdout and stderr.

## Existing coverage mapped before new tests

All paths in this table are under `reference/token_reward/`.

| Requirement | Existing coverage classification and exact source | Gap addressed by client tests |
|---|---|---|
| Lifecycle vectors and session forwarding | Sufficient business coverage: `test_reward_session.py::RewardSessionTests.test_each_journey_matches_direct_machine_receipts_errors_and_reads` | Live public-session parity reuses participation, cancellation, boundaries, unknown_pending and unknown_resolution without inventing lifecycle rules |
| Live replies and explicit pool reads before EOF | Not covered: existing `test_reward_cli.py` uses batch `subprocess.run` | `test_live_participation_before_eof_and_response_derived_reads` removes inherited `PYTHONUNBUFFERED`, omits `-u`, checks stdin remains open after every exchange and proves one child |
| Replay, immutable first results, no extra pool spend | Partially covered at transport boundary: `test_reward_cli.py::RewardCliTests.test_participation_historical_receipts_and_one_pool_spend`; `test_snapshot_isolation.py` | Live duplicate receipts retain original snapshots, `duplicate=true`, `applied=null`; pool has one spend and treasury balance 475 |
| UNKNOWN remains pending until explicit resolution | Partially covered: `test_reward_cli.py::RewardCliTests.test_unknown_remains_pending_until_separate_explicit_resolution_in_same_session` | `test_live_unknown_requires_separately_supplied_resolution` interposes reads, verifies no spend, then separately sends resolution in the same child |
| Cancellation distinct from KRW refund | Partially covered: `test_reward_cli.py::RewardCliTests.test_cancellation_and_krw_effect_remain_separate` | `test_live_cancellation_and_krw_refund_are_distinct` preserves REVERSED/CLAWBACK_CLAIM, distinct effects and retained spend |
| Request schemas, optionals and source/approval pass-through | Sufficient serialization coverage: `test_reward_serialization.py`; session optional/supersede tests | `test_all_operations_supersession_and_exact_caller_inputs` captures actual wire requests, verifies omission/null and approvals unchanged and runs supersede live |
| Operation/provenance and operation-specific replies | Not covered for reward client | `test_operation_specific_payload_shapes_and_reward_id_arrays`, malformed-child and startup tests cover empty/populated arrays, wrong payloads, pool/entry shapes, exact envelopes, strict Unicode/JSON and errors |
| Fault fencing; no retry or replacement | Not covered for reward client | Malformed/exited worker tests record exactly one submitted line and one launch; subsequent read, mutation and reconciliation fail locally; short-write/flush/pipe/interruption tests retain diagnostics |
| Ownership, overlapping calls, example and cleanup | Not covered for reward client | Import-safety/example, overlapping-call, context-cleanup and POSIX termination/kill/reaping tests cover these boundaries |

The new coverage is in `test_reward_client.py::RewardClientTests` (13 tests).
Test deadlines use events and joins solely to stop a regression from hanging;
there is no client response timeout, polling or automatic retry.

## Commands and results

Every verification invocation is captured in [commands.json](commands.json),
including complete stdout/stderr and failed/unavailable results if any.
`PYTHONDONTWRITEBYTECODE=1` is supplied for checks and inherited by children;
Python is 3.12.15 and the provisioned Rust toolchain is 1.98.1.
The focused invocation also supplies `PYTHONPATH=reference/token_reward`.

| Actual command (paired rows mean both plain and `--self-test` invocations) | Actual result |
|---|---|
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_reward_client.py` | exit 0; 13 tests passed |
| `PYTHONPATH=reference/token_reward python3.12 -m unittest test_reward_client test_reward_cli test_reward_session test_reward_serialization` | exit 0; 31 tests passed |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 213 tests passed |
| `python3.12 reference/token_reward/example_reward_client.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/participation.jsonl --cleanup-timeout 1` | exit 0; 19 reply envelopes; response-derived views and explicit final pool read |
| `python3.12 scripts/verify_runtime_architecture.py` | exit 0; architecture/dependency gate OK |
| `python3.12 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `python3.12 scripts/check_docs_index.py` and `--self-test` | both exit 0 |
| `python3.12 scripts/check_status_register.py` and `--self-test` | both exit 0 |
| `python3.12 scripts/check_tl_predicate_evidence_map.py` and `--self-test` | both exit 0 |
| `python3.12 scripts/check_class_b_index.py` and `--self-test` | both exit 0 |
| `python3.12 scripts/check_ci_checker_wiring.py` and `--self-test` | both exit 0 |
| `python3.12 scripts/check_ci_test_discovery.py` and `--self-test` | both exit 0; token_reward discovery remains wired |
| `python3.12 scripts/check_openapi_contract.py` and `--self-test` | both exit 0; 84-command pin unchanged |
| `python3.12 scripts/check_integration_gate_openapi.py` and `--self-test` | both exit 0; publicHost and productionEndpoint false |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; unavailable: offline cache lacks `bcs`; tests did not run |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; unavailable: same missing dependency; Clippy did not run |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | exit 101; unavailable: same missing dependency; tests did not run |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | exit 101; unavailable: same missing dependency; Clippy did not run |
| `python3.12 --version` | exit 0; Python 3.12.15 |
| `rustc --version` | exit 0; Rust 1.98.1 |
| `git diff --check` | exit 0 |
| `python3.12 /tmp/verify_reward_preservation.py` (source retained in JSON) | exit 0; all 125 protected file hashes match; kernel blobs match; prohibited paths/configuration unchanged |

Applicable workflow steps were inspected in `.github/workflows/ktx-kernel.yml`
and `.github/workflows/protocol.yml`. The touched token_reward suite and the
listed architecture/documentation/OpenAPI/discovery checks are green. The four
Rust test/Clippy invocations failed at dependency resolution before test/lint
execution; these are **unavailable checks, never passes**. No Rust paths changed.
No network dependency installation or unrelated Sui/ZK/storage job was attempted.
The complete example stdout, including historical replay and pool contents, is
retained in JSON; the extra eight views are example decisions, not client actions.

## Deviations, gates and limits

- The supervisor's later no-network/no-publication instruction overrides the
  repository's fetch/publication workflow. No fetch, commit or GitHub action ran.
  There is no node task document to read or modify.
- A pre-change manifest command initially failed on Git's quoted Unicode path
  output before making source changes. It was corrected to NUL-delimited
  `git ls-files -z`. This was a local capture error, not a test failure.
- Rust tests and Clippy are unavailable because the local offline cache lacks
  `bcs`; no network bootstrap is permitted. They remain outstanding alongside
  supervisor-owned review/CI gates. Formatting and applicable Python checks pass.
- The client shares the existing CLI selector/signature table and approval field
  constant; it imports no other reference suite at runtime. The CLI's sole change
  is stdout flush. No shared-client refactor or model/session change is needed.
- Blocking response reads intentionally have no timeout. Cleanup has two bounded
  wait stages followed by kill/reap, matching the existing client pattern.
- KTX exact-final-head CI: not run; ID/status/conclusion unavailable in this
  no-network uncommitted builder session. KIX protocol exact-final-head CI: same.
  Non-author A2 exact-final-head review and both completed/success CI workflows
  remain required after the supervisor establishes the final head. Prior CI is
  not inherited. Post-merge checks are not applicable; no merge occurred.
- No explicit contract violation found. Existing Class B restoration,
  normalization and late-failure characterizations remain unchanged, as described
  in the reward guide and historical rejection-atomicity/snapshot evidence. The
  client validates transport shapes; it neither authenticates synthetic source
  facts nor recomputes business decisions. Cleanup establishes no rollback.
- All seven production flags remain false; tests observe them on live receipts
  and views. Protected bytes, activation configuration, contracts, OpenAPI,
  fixture vectors, `.aiops/`, CI and task inputs are unchanged.
- No real funds/provider/KYC/bank calls, public endpoints, Sui, coin/TIX modules,
  production runtime, persistence, settlement-source connection or parked
  settlement-reward adapter. No durability, bank exactly-once, chain finality,
  legal compliance, independent verification or production readiness claim.
  Reward policy remains **UNDETERMINED — Astra/User**; legal effects remain
  **UNDETERMINED — User/legal**. Neither requires a new value for this node.
