# plan-local-reward-console — local builder evidence

Node `plan-local-reward-console` in SUNBURN-Golden/kix-protocol; issue: none.
Task document: supervisor-supplied node specification and read-only design in
this session; no `docs/tasks/` document exists for this node. Dependencies:
`plan-local-reward-desk`, `plan-plan-local-settlement-console`. A2 audit floor;
not an ASTRA program-mode session. Builder-authored evidence, not independent review.

## Identity and outstanding gates

| Item | Value |
|---|---|
| Branch | `agent/kix-plan-local-reward-console` |
| Observed local `origin/main`, base and task HEAD | `00267bc478df74faf944f4c216f8a254dd3aa1da` |
| Base delta against observed local ref | none |
| `git fetch origin main` | NOT_RUN: session instructions explicitly prohibit network actions |
| Implementation/final task commit | none created; uncommitted worktree delivery; supervisor owns Git |
| Exact-final-head KTX CI run ID/status/conclusion | NOT_RUN / unavailable; no final commit or publication authorized |
| Exact-final-head KIX CI run ID/status/conclusion | NOT_RUN / unavailable; no final commit or publication authorized |
| A2 non-author exact-head review | pending supervisor workflow |
| Merge commit / post-merge main CI | not applicable; no merge |

No commit, push, PR, issue, comment, tag, branch mutation or merge was performed.
These local checks do not make a merge proposal. Non-author review and both
completed/success exact-final-head workflows remain separate gates. No older
SHA's CI result transfers to the supervisor's eventual delivery commit.

## Coverage mapping before new tests

Paths below are under `reference/token_reward/` unless explicitly qualified.
No existing FSM/model/session test is duplicated to redefine its semantics.

| Requirement | Existing coverage and classification | Console gap addressed |
|---|---|---|
| Reward lifecycle, cancellation, refund, supersession | sufficiently covered: `test_reward_fsm.py::test_cancel_before_issuing_reverses_and_after_issued_is_clawback`, `test_TL0_TK08_T1_token_and_krw_effects_stay_apart`, `test_rule_version_change_pays_once_unless_superseded`; `test_reward_session.py::test_each_journey_matches_direct_machine_receipts_errors_and_reads`, `test_supersede_parity_and_omitted_versus_null_optionals` | Console routing absent; `test_other_selectors_and_explicit_unknown_resolution` compares exact dispatches/envelopes to direct dispatcher, including all twelve selectors |
| UNKNOWN and explicit reconciliation/resend | sufficiently covered: `test_reward_fsm.py::test_unknown_creates_no_new_reward_and_resolves_only_on_the_same_digest`; CLI UNKNOWN continuation test | Console routing absent; explicit pending/resolution inputs, unchanged permit/digest and no automatic calls |
| Historical replay and one pool spend | sufficiently covered: `test_reward_fsm.py::test_TL0_TK07_T1_one_payout_effect_under_retry_delay_and_reencoding`, `test_snapshot_isolation.py::test_mutated_first_results_do_not_change_state_or_replay`; `test_reward_cli.py::test_participation_historical_receipts_and_one_pool_spend` | `test_success_transcript`: exact requests/envelopes, historical OBSERVED versus current ISSUED, deterministic subprocess stdout, exit 0 |
| Domain refusals and sticky exit | partially covered: `test_reward_cli.py::test_semantic_refusals_retain_machine_error_codes` and UNKNOWN test | `test_boundary_transcript_sticky_exit`: exit 1 despite later accepted action/reads; exact existing codes |
| Literal confirmation, fresh fields, no implicit dispatch | not covered for reward console; precedent `reference/booking_resale_admission/test_settlement_console.py` | `test_all_mutations_literal_confirmation_and_fresh_fields`, `test_proposal_is_complete_and_flushed_before_confirmation`, `test_quit_unknown_menu_and_reads_have_no_implicit_dispatch` |
| Nested schemas, omission/null, finite opaque metadata and approval identity | sufficiently covered at dispatcher: `test_reward_serialization.py::test_nested_structures_and_nonjson_python_data_never_dispatch`, `test_optional_fields_and_prior_record_are_not_inserted_by_dispatch`, `test_metadata_and_receipt_payload_survive_canonical_roundtrip` | Console parsing absent; `test_omitted_null_optionals_and_opaque_metadata_forward_unchanged`, `test_prompt_syntax_errors_discard_selection_without_dispatch`, `test_economic_predicates_are_left_to_fsm` |
| Terminal failure and status 2 | not covered for reward console | `test_eof_at_every_prompt_and_confirmation_stops`, `test_dispatch_format_and_unexpected_failure_stop_queued_actions`, `test_output_and_diagnostic_failure_cannot_resume`, `test_setup_required_fixture_once_and_failures_exit_two` |
| No sockets, network or child execution | new console boundary | `test_import_and_execution_without_sockets_or_child_launch` guards socket creation/connections and Popen through import plus full success journey; only standard-library and existing local imports |

All 14 new console tests are source-informed composition checks. False flags,
POINT_F4, provenance and non-transferability are checked on emitted snapshots.
No clean-room or independent verification claim.

## Actual commands and results

All recorded checks ran in the foreground, with `PYTHONDONTWRITEBYTECODE=1`.
[commands.json](commands.json) retains exact command strings, actual exit codes,
stdout/stderr and elapsed time, including the first narrow-test failure and its
correction. The workflow definitions inspected were `.github/workflows/protocol.yml`
and `.github/workflows/ktx-kernel.yml`. No CI file was changed.

Local Python is 3.13.5. Installed Cargo/rustc are 1.98.1 (the workflow pin),
Clippy 0.1.98 and rustfmt 1.9.0-stable. Rust builds used
`CARGO_TARGET_DIR=/tmp/reward-console-target`, `--locked --offline`; no network
installation or automatic retry was attempted. The target directory is temporary.

| Command | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_reward_console.py` (first run) | exit 1; 14 run, one test expectation failed on the existing pool error-code spelling |
| Same narrow command after correcting expectation | exit 0; 14 tests passed |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 200 tests passed |
| `python3 scripts/check_docs_index.py` | exit 0; scanned=360 indexed=325 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | exit 0; pass |
| `python3 scripts/check_status_register.py` | exit 0; paths=457 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | exit 0; pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0; rows=49 expected=49 citations=58; existing grades unchanged |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0; pass |
| `python3 scripts/check_class_b_index.py` | exit 0; rows=218 sources=73 symbols=47; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | exit 0; 20 negative controls passed |
| `python3 scripts/check_ci_test_discovery.py` | exit 0; reference_suites=7 node_tests=8 modules=4 excluded=3; token_reward files=12 reached |
| `python3 scripts/check_ci_test_discovery.py --self-test` | exit 0; 18 negative controls passed |
| `python3 scripts/check_ci_checker_wiring.py` | exit 0; scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0; 13 negative controls passed |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `CARGO_TARGET_DIR=/tmp/reward-console-target cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; BLOCKED before compilation: offline cache missing `bcs`, required by workspace member `kix-bcs1`; no Rust tests ran |
| `CARGO_TARGET_DIR=/tmp/reward-console-target cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | exit 101; BLOCKED before compilation by the same missing offline `bcs` dependency; not a passing Clippy check |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | exit 0 |
| `git diff --check` | exit 0 |
| `python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json < reference/token_reward/fixtures/reward_console_journey.txt > validation/2026-11-05-plan-local-reward-console/journey.stdout.txt` | exit 0; 11 complete desk envelopes; stderr empty |
| `python3 reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json < reference/token_reward/fixtures/reward_console_boundaries.txt > validation/2026-11-05-plan-local-reward-console/boundaries.stdout.txt` | expected exit 1; 10 complete desk envelopes; stderr empty |
| Protected-file Python SHA-256 comparison + `git hash-object` + `git diff --exit-code origin/main -- <protected/backend paths>` (full command in commands.json) | exit 0; all 110 protected files byte-identical, both locked blobs match; governance/backend paths unchanged |

Captured output: [success journey](journey.stdout.txt),
[boundary journey](boundaries.stdout.txt). Console tests also compare repeated
success-process stdout byte for byte and compare both captured interactions to
the direct dispatcher. These transcripts are synthetic output evidence, not a
persistence or recovery format.

Rust testing and linting require the supervisor's populated offline workspace
cache before they can complete. They are unavailable checks, not source failures
or successful CI. The Python console itself adds no dependency.

## Preservation, classification and limitations

Before edits, Git hashes matched both required blobs:

- `runtime/crates/kix-kernel/src/lib.rs`: `69564b166f0c27f9af5d8422f0a466b18d74c20f`.
- `runtime/crates/kix-kernel/tests/quarantine_capacity.rs`: `b607996c83a119c349f1cc90469ac1ba82764e20`.

A pre-edit SHA-256 manifest captured all 110 protected files (the two kernel
files plus all 108 files under `reference/v0.3-rc1/`). Final verification is
recorded in commands.json: PASS, including unchanged membership and bytes.
Both Git blob locks also match after work. The canonical pre/post manifest
SHA-256 is `1f8ff8890da49956e9b277f37f6cd37fd89213d8784087eee1858819a2a21f47`.
Final HEAD and local origin/main remain the initial SHA; no merge check applies.
`.aiops/`, `docs/tasks/`, CI, session, fixture loader, dispatcher,
FSM, model, existing JSON/JSONL fixtures and contracts are unchanged.

Class A: existing TK-4 pool restrictions, TK-7 payout bound, TK-8 reward/KRW
separation and synthetic flags are forwarded unchanged. No explicit contract
violation was found. No authoritative contract was amended.

Class B: historical first-result envelopes, copy isolation, late injected
invariant/pool failures without rollback, forgotten rejections on restoration,
UNKNOWN resends not consuming approvals and normalization of omitted
`prior_record` remain existing characterizations. See the existing
[atomicity record](../2026-10-20-token-reward-rejection-atomicity/README.md) and
[snapshot record](../2026-10-24-reward-snapshot-isolation/README.md).
This console offers no restoration, persistence or rollback guarantee.

No policy value was chosen. All caller identities, approvals, balances, amounts,
caps, budgets, fence slots and window assertions are synthetic. Amounts, caps,
budgets, durations and approval policy remain UNDETERMINED — Astra/User; actual
approver designation remains User-owned and chargeback timing with the provider.
No STOP resource or out-of-scope decision was required.

No real funds, PG/bank/KYC calls, endpoints, secrets, production runtime, Sui
testnet/mainnet, token/coin/TIX module, protocol command, storage engine,
settlement/reward coupling, parked adapter, readiness or Wave7 integration.
No durability, distributed fencing, chain finality, bank exactly-once, legal
compliance, activation or production-readiness claim. Full hosted workflows and
unrelated Move/ZK/localnet/storage checks are NOT_RUN. Remaining gates belong to
the supervisor: commit final content, obtain A2 non-author review and exact-head
KTX/KIX CI. Class B changes would require a separately authorized task.

Deviations: fetch omitted under the explicit no-network instruction; no task
document/issue was manufactured. Prompt-level structural mistakes recover as
`input_error=`; a dispatch-format failure retains the error envelope and fences.
The first narrow run exposed a test expectation using shortened pool-error codes;
the test was corrected to the actual existing `POOL_FORBIDDEN_FOR_TOKEN_SPEND`.
The pinned offline Rust cache is incomplete (`bcs` missing); tests/Clippy are
blocked without downloading dependencies, which this session prohibits. No
implementation scope deviation or STOP condition was encountered.

## Changed paths

- `docs/README.md`
- `reference/token_reward/README.md`
- `reference/token_reward/reward_console.py`
- `reference/token_reward/test_reward_console.py`
- `reference/token_reward/fixtures/reward_console_journey.txt`
- `reference/token_reward/fixtures/reward_console_boundaries.txt`
- `validation/2026-11-05-plan-local-reward-console/README.md`
- `validation/2026-11-05-plan-local-reward-console/commands.json`
- `validation/2026-11-05-plan-local-reward-console/journey.stdout.txt`
- `validation/2026-11-05-plan-local-reward-console/boundaries.stdout.txt`
