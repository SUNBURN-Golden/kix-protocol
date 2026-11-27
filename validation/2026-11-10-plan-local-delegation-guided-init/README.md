# Guided local delegation initialization — builder evidence

Node: `plan-local-delegation-guided-init`. Task input is the supervisor's supplied
node specification and design plan in this session; no issue or `docs/tasks/`
document exists. This is not ASTRA program mode. Dependencies named by the input:
`plan-plan-local-delegation-live-console`, `plan-local-delegation-input-composer`.

Local implementation only. A2 non-author exact-head review and both required
exact-head CI workflows remain separate supervisor gates. This evidence does not
claim merge-ready status, policy adoption, runtime activation or independent review.

Observed local `origin/main`, base and task HEAD:
`a5f8192df8909451c875828839e8517facdbe289`. Branch:
`agent/kix-plan-local-delegation-guided-init`. Initial worktree was clean. Remote
freshness is unverified: the supervisor explicitly prohibited GitHub/network
activity, overriding AGENTS.md §1's fetch. No fetch, commit, push, issue, PR,
comment, merge, history rewrite or branch/tag mutation was performed. There is no
new implementation/final commit SHA; changes are an uncommitted worktree patch.
Merge SHA and post-merge CI: N/A.

## Implementation and preserved boundaries

Shared `validate_fixture` / `session_from_fixture` helpers preserve file mode and
forward domain registry validation to the existing constructor. Opt-in
`delegation_cli.py --init-stdin --requests -` accepts one newline-terminated input,
constructs one session and flushes the accepted fixture acknowledgement before
reading operations. `DelegationClient.launch_from_fixture` submits one detached
snapshot and requires an exact acknowledgement, including registry order. Failed
startup fences requests, retains wire/cause/setup-error evidence and cleans up the
owned child without retry. The guided console composes explicit registries,
flushes the complete preview, requires literal SUBMIT before launch, renders the
acknowledgement and enters the existing operation loop.

The seven operation schemas/dispatch selectors, mock and session implementations,
existing fixture inputs, authoritative contracts, workflows, `.aiops/`,
`docs/tasks/`, runtime, both kernel locks and `reference/v0.3-rc1/**` are preserved.
The new transcript contains explicit registries and the existing guided lifecycle,
followed by an explicit refused execution attempt (expected exit 1).

## Existing coverage mapped before adding tests

| Requirement | Existing evidence / classification before this change | New gap evidence |
|---|---|---|
| Fixture-free full journey | Partial: `test_delegation_console_subprocess.DelegationConsoleSubprocessTests.test_guided_real_child_journey_matches_raw` covers fixture-backed composition | `test_guided_init_real_child_journey`: real console and child, grant/query/proposal/human decision/revocation, retained views, execution refusal, all eleven false flags and effects_executed false |
| Equivalent operation replies | Partial: CLI `test_file_stdin_and_repeated_process_transcripts_are_identical`, client `test_live_lifecycle_before_eof`, console `test_default_explicit_and_subprocess_cli_transcripts_are_identical` | `test_fixture_and_stdin_init_reply_parity` compares entire lifecycle/boundary/replay streams; `test_initialized_live_client_parity_and_detached_snapshots` compares all replies through both clients |
| Constructor-identical registries | Partial: serialization `test_fixture_requires_exact_schema_version_provenance_and_both_registries` | `test_registry_initialization_matches_constructor`: 400 registry pairs; empty/order/Unicode/whitespace/length/types/duplicates/overlap; shape/forwarding, real CLI and client rejection and empty/Unicode/order echo tests |
| No child before confirmation | Not covered for startup; operation-level composer decline/EOF tests already sufficient for operation behavior | Console `test_guided_init_confirmation_precedes_launch`, `test_guided_init_eof_invalid_composition_interrupt_and_output_start_no_child`, `test_guided_init_verbatim_empty_order_and_flushed_preview`, option isolation |
| Malformed/mismatched acknowledgement fences without retry | Partial: client `test_strict_frames_and_response_shapes_fence_with_raw_evidence`, I/O interruption and cleanup tests cover operations | Startup ack matrix tests, live hostile child cleanup, setup errors, short/broken/interrupted write/flush/read; console malformed ack and render-failure tests stop queued sentinel |
| Existing flags, replay and A5 boundaries | Sufficient: existing mock/property/session/CLI/client/console suites, including mock `test_flags_remain_false`; existing execution refusal and replay characterizations | Reused unchanged plus new full-stream parity and journey flag assertions; no new domain semantics or normative simultaneous-error cases |

All new tests are source-informed. Constructor parity is not independent contract
conformance. Counts measure executed test methods, not coverage completeness.

## Actual commands and results

Machine-readable invocations and exits: [commands.jsonl](commands.jsonl).
Each log retains actual output, including failures. Focused initialization/client/
console tests run first, then full delegation discovery, the real transcript,
applicable workflow document checkers and offline architecture/Rust equivalents.
| Command (from repository root) | Actual result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/ai_delegation python3 -m unittest test_delegation_serialization test_delegation_cli test_delegation_client test_delegation_console test_delegation_console_subprocess` | Final: exit 0, 79 tests passed ([log](focused.log)). Initial: exit 1, 77 tests / one failure ([log](focused-initial.log)); assertion assumed print used one write. CLI now checks one frame write plus flush, and tests cover short writes. Intermediate runs: 77 passed, then [78 passed](focused-before-type-gap.log). Final extra test verifies acknowledgement registry types even when a malformed echo matches the submitted input. |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=reference/ai_delegation python3 -m unittest discover -s reference/ai_delegation -t reference/ai_delegation` | Final: exit 0, 169 tests passed ([log](delegation-suite.log)); earlier run before the final type-gap test passed 168. |
| `python3 reference/ai_delegation/delegation_console.py --guided-init --mode subprocess --cleanup-timeout 1 < reference/ai_delegation/fixtures/delegation_console_guided_init_journey.txt` | Exit 1, expected explicit `DELEGATED_EXECUTION_DISABLED`; no stderr. [stdout](guided-transcript.stdout.txt), [stderr](guided-transcript.stderr.txt). New real-child test compares every reply to the existing session lifecycle plus explicit execution refusal. |
| `python3 scripts/check_NAME.py` and `python3 scripts/check_NAME.py --self-test`, for NAME = `ai_delegation_evidence_map`, `delegation_layer_matrix`, `contract_error_codes`, `evidence_map_rollup`, `class_b_index`, `docs_index`, `status_register`, `ci_test_discovery`, `ci_checker_wiring` | All 18 invocations exit 0; exact expanded commands and individual logs are in commands.jsonl. No checker or workflow was changed. |
| `python3 scripts/verify_runtime_architecture.py` | Exit 0; architecture v5 + KTX-R1 dependency gate OK ([log](verify_runtime_architecture.log)). |
| `python3 scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed ([log](test_runtime_architecture.log)). |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | UNAVAILABLE, exit 101; missing cached `bcs` ([log](kernel-tests.log)). No tests executed. |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | UNAVAILABLE, exit 101; missing cached `bcs` ([log](workspace-tests.log)). No tests executed. |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101; missing cached `bcs` ([log](workspace-clippy.log)). No Clippy result. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | UNAVAILABLE, exit 101; missing cached `bcs` ([log](kernel-clippy.log)). No Clippy result. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 ([log](rust-format.log)). |
| `cargo tree --manifest-path runtime/Cargo.toml -p kix-kernel --edges normal --locked --offline` | UNAVAILABLE, exit 101; missing cached `bcs` ([log](kernel-dependencies.log)). No dependency-tree result. |

Rust commands used installed toolchain 1.98.1 and `RUSTUP_AUTO_INSTALL=0`.
Offline failures are recorded as unavailable, never passed. No download or retry
was attempted. Full hosted workflows and unrelated Sui/ZK/bootstrap jobs were not
run; no live-network or production-equivalent claim is made.

## Preservation and delivery gates

[Protected-before](protected-before.json) and [protected-after](protected-after.json)
SHA-256 manifests match for all 110 files: two locked kernel files and 108 files
under `reference/v0.3-rc1/**`. [Preservation summary](preservation.json) records
both actual Git blob hashes; because content matches the initial manifest, the
same blobs hold before and after. No merge was performed, so final-merge lock
verification is N/A. [Context](context.json) records the observed SHAs and gates.

Complete changed-path list: [changed-paths.json](changed-paths.json). Product/code
paths: `reference/ai_delegation/delegation_fixture.py`, `delegation_cli.py`,
`delegation_client.py`, `delegation_console.py`; existing tests
`test_delegation_serialization.py`, `test_delegation_cli.py`,
`test_delegation_client.py`, `test_delegation_console.py`,
`test_delegation_console_subprocess.py`; `fixtures/delegation_console_guided_init_journey.txt`;
`reference/ai_delegation/README.md`; `docs/README.md` (only validation link).
Remaining additions are this validation directory's report, command/log records,
transcript, context and preservation/path manifests. Both required Git blobs are checked from file contents:

| File | Required blob |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

| Gate | State / run ID / conclusion |
|---|---|
| A2 non-author exact-final-head review | PENDING supervisor; builder evidence is not non-author review |
| Exact-head KTX kernel verification | NOT_RUN / unavailable / none; no publication or final commit |
| Exact-head KIX protocol verification | NOT_RUN / unavailable / none; no publication or final commit |
| Merge and post-merge main/push CI | N/A; not authorized or performed |

No earlier SHA's CI success is transferred. STATUS READY means the builder patch
is ready for supervisor handling; it does not authorize merge.

## Deviations, discrepancies, uncertainty and non-claims

The supervisor's no-network/no-publication instructions replace fetch and GitHub
delivery with a local freshness-unverified base and an uncommitted patch. CLI
output uses a single checked write and flush so a short acknowledgement write
terminates before consuming operations. Request input errors keep their existing
error envelope. The five offline Cargo dependency checks are unavailable because cached `bcs`
is missing; formatting and all applicable available Python/document/architecture
checks pass. This environment limitation remains for supervisor CI. No
implementation scope expansion or new policy decision was needed.

No new contract violation or undefined business behavior was discovered. Existing
class-C A5 remains unresolved: mock registration → tool lists → grant binding
conflicts with contract §7's binding-before-tool-lists order. New transcripts
exclude that disputed simultaneous-error case. The [October 26 addendum](../../docs/status/OPEN_USER_DECISIONS_20261026_ADDENDUM.md#new-stop--plan-plan-aid-contract-map-partial-closure)
retains Astra as design/contract authority, with User authorization of resulting
changes. Missing-grant binding remains UNDETERMINED with the same owner. No A5
repair or full contract-conformance claim is made.

Product limits/surfaces/proposal kinds remain UNDETERMINED — Astra; authority and
identity policy UNDETERMINED — Astra/User; legal effects UNDETERMINED — User/legal.
All registries are synthetic identities. All eleven flags and proposal
`effects_executed` remain false. Approval is an inert memo. No authentication,
credentials, funds/provider/bank/KYC calls, public endpoint, production runtime,
Sui testnet/mainnet, storage engine, replication/consensus, coin/TIX module or new
protocol command was required or added. No production readiness, durability,
distributed fencing, exactly-once funds, chain finality, legal compliance or
capability-grade increase is claimed. Hardware, authoritative time, actual
identity and external effects were not tested.

Supervisor follow-up: commit/publication, A2 exact-final-head non-author review,
and required KTX/KIX CI. A5 disposition remains a separate Astra/User decision.
