# plan-local-reward-desk — local builder evidence

Node: `plan-local-reward-desk`, SUNBURN-Golden/kix-protocol. Issue: none.
Task input: the supervisor-supplied node specification and read-only design in
this session; there is no task document under `docs/tasks/` for this node.
Dependencies: `tl-3-offchain`, `tl-4`. Audit floor A2; not ASTRA program mode.

## Identity and gates

| Item | Observed value |
|---|---|
| Branch | `agent/kix-plan-local-reward-desk` |
| Local `origin/main` and initial task HEAD | `32acc05a27ef0b297306973da5d013050485da4c` |
| Base delta against local ref | none |
| Fetch | NOT_RUN: supervisor explicitly prohibits network/GitHub actions, overriding AGENTS §1 fetch |
| Implementation/final task commit | none created; supervisor owns git. Working-tree delivery only |
| Merge commit / post-merge CI | not applicable; no merge |
| Exact-final-head KTX CI | NOT_RUN; no run ID/status/conclusion available |
| Exact-final-head KIX CI | NOT_RUN; no run ID/status/conclusion available |
| A2 non-author exact-final-head review | pending supervisor workflow; builder checks are not independent review |

No commit, push, PR, issue, comment, tag, branch mutation or merge was performed.
No prior CI result transfers to the supervisor's eventual final head. Completed,
successful KTX and KIX exact-head CI and non-author review remain required before
any merge proposal, together with explicit human merge authorization.

## Coverage map (before adding tests)

Existing paths below are under `reference/token_reward/` unless fully qualified.
The FSM and model are unchanged. New tests address desk boundaries only.

| Requirement | Existing evidence and classification | New gap coverage |
|---|---|---|
| Lifecycle, caller snapshots and explicit window closure | sufficiently covered: `test_reward_fsm.py::test_window_must_be_closed_before_eligibility`, `test_source_kinds_require_a_committed_krw_snapshot`, and `test_flags_and_points_stay_non_transferable_on_every_phase` | session integration was partial; `test_reward_session.py` compares every journey receipt/error/read to direct machine calls; full signatures and supersede parity |
| First-result replay and one pool spend | sufficiently covered: `test_reward_fsm.py::test_TL0_TK07_T1_one_payout_effect_under_retry_delay_and_reencoding`; `test_snapshot_isolation.py::test_mutated_first_results_do_not_change_state_or_replay`, `test_mutated_duplicate_results_do_not_change_later_replays` | `test_reward_cli.py` checks complete historical receipts and one serialized spend |
| Cancellation before/after issuance | sufficiently covered: `test_reward_fsm.py::test_cancel_before_issuing_reverses_and_after_issued_is_clawback` | cancellation transcript asserts REVERSED/CLAWBACK_CLAIM and retained spend |
| UNKNOWN, same digest and explicit resend | sufficiently covered: `test_reward_fsm.py::test_unknown_creates_no_new_reward_and_resolves_only_on_the_same_digest`; `test_tl4_fsm_properties.py::test_TL4_TK07_unknown_reconcile_creates_no_reward` | pending transcript remains UNKNOWN after refused requests and explicit permitted resend; separately supplied resolution resolves in the same process |
| Reward/KRW separation | sufficiently covered: `test_reward_fsm.py::test_TL0_TK08_T1_token_and_krw_effects_stay_apart` | serialized refund receipt retains ISSUED token phase and distinct KRW effect ID |
| Forbidden pools, AI approval, non-transferability and false flags | sufficiently covered: `test_reward_fsm.py::test_forbidden_pool_is_rejected_on_submit`, `test_ai_approval_is_rejected_and_external_execution_is_unsupported`, `test_flags_and_points_stay_non_transferable_on_every_phase`; TL-4 model/FSM properties | CLI boundary transcript retains codes; all emitted reward views/receipts checked for false flags and non-transferability |
| Forwarding/optional omission/null and no manufactured approvals | not covered for the new session | signature parity, supplied object identity, optional values and absence of inserted prior_record; no automatic extra machine calls |
| Strict JSON/shape/serialization and no malformed dispatch | not covered for the new desk | `test_reward_serialization.py`: nested duplicates, non-finite/overflow, invalid JSON/Unicode, all missing/extra arguments/selectors/nested structures, opaque metadata, setup completeness; dispatch spies |
| CLI exit behavior, stop boundary, file/stdin parity and determinism | not covered | `test_reward_cli.py`: real subprocess journeys and repeated byte-identical outputs, explicit domain continuation, malformed stop without consuming key, setup/I/O failures |

The new suites contain 5 session, 6 serialization and 7 CLI tests. These are
builder-authored, source-informed checks, not clean-room verification.

## Runnable transcripts

The fixture directory is `reference/token_reward/fixtures/`. Every command uses
`python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json`.
The `--requests` argument below supplies the only operations performed.

| Request input | Expected exit | Evidence output |
|---|---|---|
| `--requests reference/token_reward/fixtures/participation.jsonl` | 0 | [participation.stdout.jsonl](participation.stdout.jsonl) |
| `--requests reference/token_reward/fixtures/cancellation.jsonl` | 0 | [cancellation.stdout.jsonl](cancellation.stdout.jsonl) |
| `--requests reference/token_reward/fixtures/boundaries.jsonl` | 1 (explicit semantic refusals) | [boundaries.stdout.jsonl](boundaries.stdout.jsonl) |
| `--requests reference/token_reward/fixtures/unknown_pending.jsonl` | 1 (explicit semantic refusals; final state UNKNOWN) | [unknown_pending.stdout.jsonl](unknown_pending.stdout.jsonl) |
| `--requests reference/token_reward/fixtures/unknown_resolution.jsonl` | 1 (fresh session has no reward) | [unknown_resolution.stdout.jsonl](unknown_resolution.stdout.jsonl) |
| `cat reference/token_reward/fixtures/unknown_pending.jsonl reference/token_reward/fixtures/unknown_resolution.jsonl` piped to `--requests -` | 1 (earlier refusals retained in exit status; final state ISSUED) | [unknown_combined.stdout.jsonl](unknown_combined.stdout.jsonl) |

Every transcript is executed twice and compared byte-for-byte during capture;
CLI tests also compare file/stdin interfaces, expected payloads and exit codes.
Recorded JSONL is synthetic output evidence, not a persistence/restoration format.

## Commands and results

Results below come from actual foreground executions. No hosted workflow
or background long job is started. CI definitions inspected:
`.github/workflows/protocol.yml` and `.github/workflows/ktx-kernel.yml`.
Python 3.13.5 is the local default; Python 3.12.15 is also available for the CI pin.

All Python commands below ran with `PYTHONDONTWRITEBYTECODE=1`. Actual stdout/stderr, exit codes, transcript hashes and the complete path list are in [commands.json](commands.json).

| Command actually run | Actual result |
|---|---|
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_reward_session.py` | exit 0; 5 tests passed |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_reward_serialization.py` | exit 0; 6 tests passed |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward -p test_reward_cli.py` | exit 0; 7 tests passed |
| `python3 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 186 tests passed |
| `python3.12 -m unittest discover -s reference/token_reward -t reference/token_reward` | exit 0; 186 tests passed |
| `python3 scripts/check_docs_index.py` | exit 0; docs index ok: scanned=330 indexed=295 allowlisted=35 |
| `python3 scripts/check_docs_index.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_status_register.py` | exit 0; capability register ok: paths=457 ev_ids=15 original32=32 |
| `python3 scripts/check_status_register.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_tl_predicate_evidence_map.py` | exit 0; tl predicate evidence map ok: rows=49 expected=49 citations=58 HARNESS_AUTHOR_SIDE=12 REVIEWED_RECORD=6 NOT_VERIFIABLE_NO_PACKAGE=24 PARTIAL=7 |
| `python3 scripts/check_tl_predicate_evidence_map.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_class_b_index.py` | exit 0; class B index ok: rows=218 sources=73 symbols=47; textual index only |
| `python3 scripts/check_class_b_index.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_ci_test_discovery.py` | exit 0; ci test discovery ok: reference_suites=7 node_tests=8 modules=4 excluded=3 |
| `python3 scripts/check_ci_test_discovery.py --self-test` | exit 0; self-test pass |
| `python3 scripts/check_ci_checker_wiring.py` | exit 0; ci checker wiring ok: scripts=35 plain=34 self_test=35 self_test_only=1 docs=22 citations=99 |
| `python3 scripts/check_ci_checker_wiring.py --self-test` | exit 0; self-test pass |
| `python3 scripts/verify_runtime_architecture.py` | exit 0; architecture v5 + KTX-R1 dependency gate OK; durability/performance NOT certified |
| `python3 scripts/test_runtime_architecture.py` | exit 0; 7 tests passed |
| `/usr/bin/cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | exit 101; unavailable offline dependency `const-oid`; no Rust tests executed |
| `git diff --check` | exit 0 |
| `python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/participation.jsonl` | exit 0; 11 JSONL lines; two runs byte-identical |
| `python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/cancellation.jsonl` | exit 0; 13 JSONL lines; two runs byte-identical |
| `python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/boundaries.jsonl` | exit 1; 10 JSONL lines; two runs byte-identical |
| `python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/unknown_pending.jsonl` | exit 1; 14 JSONL lines; two runs byte-identical |
| `python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests reference/token_reward/fixtures/unknown_resolution.jsonl` | exit 1; 4 JSONL lines; two runs byte-identical |
| `cat reference/token_reward/fixtures/unknown_pending.jsonl reference/token_reward/fixtures/unknown_resolution.jsonl \| python3 reference/token_reward/reward_cli.py --fixture reference/token_reward/fixtures/reward_session.json --requests -` | exit 1; 18 JSONL lines; two runs byte-identical |
| `git hash-object runtime/crates/kix-kernel/src/lib.rs runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | exit 0; both required blobs match before and after |
| `git diff --exit-code origin/main -- reference/v0.3-rc1 .aiops docs/tasks .github runtime reference/token_reward/reward_fsm.py reference/token_reward/token_reward_model.py` | exit 0; protected/model paths unchanged against local origin/main |

| Required check not run | Reason |
|---|---|
| `git fetch origin main` | Supervisor explicitly prohibits network actions. |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked (pinned 1.98.1)` | No installed rustup toolchains; offline system Cargo attempt recorded separately. |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked -- -D warnings` | Pinned 1.98.1 absent; system Clippy absent; no network installation authorized. |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Pinned 1.98.1 absent; system rustfmt absent; no network installation authorized. |
| `Hosted exact-final-head KTX and KIX workflows` | No commit/publication authorized; supervisor owns git and GitHub. |

Rust environment discovery: `rustup toolchain list` reported no installed toolchains; `/usr/bin/cargo --version` and `/usr/bin/rustc --version` reported 1.85.1. `/usr/bin/cargo-clippy` and `/usr/bin/rustfmt` are absent. The offline attempt used `RUSTC=/usr/bin/rustc`, `RUSTDOC=/usr/bin/rustdoc`, `CARGO_NET_OFFLINE=true`, and `CARGO_TARGET_DIR=/tmp/reward-desk-target`. No toolchain or dependency download was attempted. The repository pin remains 1.98.1. These environment limitations are not counted as passing Rust checks.

Final historical-reference comparison: all 108 files are byte-identical to the pre-edit SHA-256 manifest; digest remains `dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`. Both locked blobs match.


## Preservation

Before edits both kernel Git blobs matched their required values:
`69564b166f0c27f9af5d8422f0a466b18d74c20f` (`lib.rs`) and
`b607996c83a119c349f1cc90469ac1ba82764e20` (`quarantine_capacity.rs`).
The initial SHA-256 manifest of all 108 tracked `reference/v0.3-rc1/` files has
canonical-manifest digest `dbfe11de81169745a46e7c2ccfbb705d1ec6e71be2f9922158429a0bfc5ff00f`.
The first manifest attempt used newline Git output and failed on a quoted
non-ASCII filename; the corrected `git ls-files -z` capture succeeded before edits.
Final preservation checks are recorded in the actual-results table.

## Classification, limitations and deviations

Class A: desk outputs preserve the existing FSM's TK-4 pool restrictions, TK-7
payout bound and TK-8 separation within this synthetic process. No explicit
contract violation was found. No authoritative contract was amended.

Class B behavior remains unchanged: late injected invariant/conservation faults
can leave unjournaled mutation; restoring forgets stored rejections; UNKNOWN
resends do not consume approval records. See [the existing atomicity evidence](../2026-10-20-token-reward-rejection-atomicity/README.md).
Raw approval fingerprints can differ from normalized journal fingerprints when
`prior_record` was omitted: [snapshot-isolation record](../2026-10-24-reward-snapshot-isolation/README.md).
TL-4 also characterizes non-canonical `effect_id` errors, the two allowed exits
from ISSUED, and simultaneous supply-alarm precedence in
[threat model §6.B](../../docs/decisions/TL4_THREAT_MODEL_20261009.md).
Complete historical envelopes and detached snapshots remain Class B observations.
The desk changes none of these and offers no restoration or rollback guarantee.

Design deviations: strict Unicode/JSON-value validation also protects importable
dispatch; lone surrogates are rejected before UTF-8 hashing/output. A machine-readable
command record supplements this report. Fetch is omitted under the explicit
supervisor prohibition. Environment limitations for Rust are listed with results.

No policy value was chosen. Synthetic opening balances, identities, source
snapshots, caps/budgets, approvals, fence slots and window assertions are explicit
fixtures only. Policy remains UNDETERMINED with Astra/User, chargeback timing with
the payment provider, actual approver designation with User. No STOP condition
requiring any of those decisions is needed by this in-memory desk.

No real money, provider/KYC/bank calls, public endpoint, secrets, production
runtime, Sui testnet/mainnet, token module, protocol command, storage engine,
readiness/settlement integration, parked adapter or Wave7 work. All seven false
production flags and non-transferability are retained. No durability, chain
finality, bank exactly-once, legal-compliance, runtime activation or production
readiness claim. Unrelated Move/SDK/ZK/localnet/storage paths and full hosted
workflows are NOT_RUN. Remaining work belongs to the supervisor: commit the final
content, obtain A2 non-author exact-head review and exact-head KTX/KIX CI. Possible
future changes to Class B behavior need a separately authorized task.

## Changed paths

- `docs/README.md`
- `reference/token_reward/README.md`
- `reference/token_reward/fixtures/boundaries.jsonl`
- `reference/token_reward/fixtures/cancellation.jsonl`
- `reference/token_reward/fixtures/participation.jsonl`
- `reference/token_reward/fixtures/reward_session.json`
- `reference/token_reward/fixtures/unknown_pending.jsonl`
- `reference/token_reward/fixtures/unknown_resolution.jsonl`
- `reference/token_reward/reward_cli.py`
- `reference/token_reward/reward_fixture.py`
- `reference/token_reward/reward_session.py`
- `reference/token_reward/test_reward_cli.py`
- `reference/token_reward/test_reward_serialization.py`
- `reference/token_reward/test_reward_session.py`
- `validation/2026-11-02-plan-local-reward-desk/README.md`
- `validation/2026-11-02-plan-local-reward-desk/boundaries.stdout.jsonl`
- `validation/2026-11-02-plan-local-reward-desk/cancellation.stdout.jsonl`
- `validation/2026-11-02-plan-local-reward-desk/commands.json`
- `validation/2026-11-02-plan-local-reward-desk/participation.stdout.jsonl`
- `validation/2026-11-02-plan-local-reward-desk/unknown_combined.stdout.jsonl`
- `validation/2026-11-02-plan-local-reward-desk/unknown_pending.stdout.jsonl`
- `validation/2026-11-02-plan-local-reward-desk/unknown_resolution.stdout.jsonl`
