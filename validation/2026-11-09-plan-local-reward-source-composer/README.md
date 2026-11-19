# Guided synthetic reward source snapshots — builder evidence

Node/task ID: `plan-local-reward-source-composer`. Task input is the supervisor's
supplied objective, acceptance and read-only design plan (KIX planner run
1794201720); no issue or task-document file exists. This is not ASTRA program
mode. Dependencies `plan-plan-local-reward-live-console` and
`plan-local-reward-approval-composer` are present in the base. Audit floor A2;
Astra gate none. This is source-informed builder evidence, not non-author review.

Observed local `origin/main`, base and initial/current HEAD are all
`f0eab3e083f9ca317482ea10576c4605364fd51b`, branch
`agent/kix-plan-local-reward-source-composer`. The initial working tree was clean.
The supervisor prohibits network and publication, so `git fetch origin main` is
NOT_RUN; remote freshness is unverified. No base delta is visible locally.
Implementation/final task commit SHAs, exact-head KTX/KIX run IDs/status/conclusions
and merge/post-merge identifiers are unavailable: the supervisor owns commits and
GitHub. No commit, push, PR, issue, comment, tag or branch mutation was performed.

The composer collects phase and currency verbatim and every existing
`SOURCE_FINALITY_FLAGS` boolean explicitly. Additional finite JSON fields are
merged only after rejecting top-level collisions with all seven prompted names,
even equal collisions. Nested metadata stays opaque. Raw JSON remains available
for every selection, including incomplete source objects. The completed snapshot
uses the unchanged preview, literal SUBMIT, RewardClient, CLI, session and FSM.
No composer field enters the envelope and no source semantics are added.

## Coverage mapping

Existing coverage was inspected before adding tests. Paths below are relative to
`reference/token_reward/`. New shared tests are in `GuidedCompositionTests` in
`test_reward_console.py`, inherited by the in-process and subprocess classes.
The live shared harness captures actual JSONL writes and matches them to the
requests; every invocation owns exactly one real child, reaped on completion.

| Requirement | Existing classification and reuse | Composition gap covered |
|---|---|---|
| Observation, eligibility, historical replay | Sufficient lifecycle: `test_reward_console.py::test_success_transcript`, `test_reward_session.py` participation vectors; partial guided source coverage | `test_source_guided_raw_parity`, `test_source_transcripts`; complete proposals and receipts match raw and mixed entry |
| Source cancellation/refund separation | Sufficient lifecycle: `test_reward_fsm.py::test_cancel_before_issuing_reverses_and_after_issued_is_clawback`, `test_krw_refund_does_not_reverse_the_token_until_source_cancel`, `test_reward_console_subprocess.py::test_live_console_scenario_parity` | Reuse cancellation vectors with guided source; REVERSED, CLAWBACK_CLAIM, refund ISSUED/KRW_REFUND_NOTED and separate effect identity |
| Reply before EOF, one live child | Sufficient live harness; missing new-path integration | Existing `test_live_console_journey_before_eof` now guides source too, retains stdin open after every reply, one launch |
| Opaque metadata, precision, fresh values | Partial: existing raw opaque-forwarding tests | `test_source_metadata_preservation_and_fresh_snapshots`: empty extras, nested reserved names, Unicode, null, array order, positive/negative integers above 2**53, unwrapped fields, metadata identity cannot replace reward key |
| No inferred domain values | Partial: `test_reward_fsm.py::test_source_kinds_require_a_committed_krw_snapshot`, `test_window_must_be_closed_before_eligibility` | `test_source_domain_refusal_parity`: all four operations, blank/whitespace/invalid phase/currency, each true finality flag unchanged through raw and guided child writes; false window remains WINDOW_OPEN; raw incomplete/mistyped flags still reach FSM |
| Malformed composition, decline and EOF | Partial: existing raw and approval composer boundary tests | `test_source_incomplete_no_dispatch`: every source prompt and confirmation cutoff, every boolean wrong type/malformed JSON, nonobject/nonfinite/duplicate/surrogate extras, every equal reserved-key collision; zero dispatches and writes |
| Complete flushed preview and explicit confirmation | Sufficient shared harness and literal-confirmation tests | Shared live harness verifies complete proposed request and flush before write; source boundary transcript includes a declined proposal |
| Transport uncertainty, no retry/fallback | Sufficient transport tests; missing source integration | Existing `test_uncertainty_stops_and_preserves_evidence` and `test_partial_reply_interruption_and_short_write_stop` run with raw and completed guided source; preserve request/reply bytes, stop queued actions, one submission, terminal fencing and child cleanup |
| CLI transcripts | Partial: existing raw/approval fixtures | Three source fixtures in both modes; `test_cli_transcripts_match_default_in_process` checks full stdout/status parity |

## Commands and results

Actual invocations, exit codes, durations and stdout/stderr filenames are in
[commands.json](commands.json). Captures retain failures as well as passing
reruns. A boundary transcript intentionally exits 1 for domain refusals; this is
expected evidence, not a failed check. Python 3.12 and repository-pinned Rust
1.98.1 are used, with bytecode disabled and Cargo locked/offline.

| Command | Actual result |
|---|---|
| `python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward -p 'test_reward_console*.py'` | Initial run exit 1: 47 tests, one new test assertion failure; corrected run exit 0, 47 tests passed |
| `python3.12 -B -m unittest discover -s reference/token_reward -t reference/token_reward` | Exit 0; all 288 tests passed |
| `python3.12 -B scripts/check_docs_index.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_status_register.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_tl_predicate_evidence_map.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_class_b_index.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_ci_test_discovery.py` and `--self-test` | Both exit 0; existing CI discovery reaches both changed test modules |
| `python3.12 -B scripts/check_ci_checker_wiring.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_openapi_contract.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/check_integration_gate_openapi.py` and `--self-test` | Both exit 0 |
| `python3.12 -B scripts/verify_runtime_architecture.py` | Exit 0; dependency boundary gate passes, no durability/performance certification |
| `python3.12 -B scripts/test_runtime_architecture.py` | Exit 0; 7 tests passed |
| `cargo test --manifest-path runtime/Cargo.toml -p kix-kernel --locked --offline` | Exit 101; BLOCKED before compilation: missing offline `bcs` dependency |
| `cargo clippy --manifest-path runtime/Cargo.toml -p kix-kernel --all-targets --locked --offline -- -D warnings` | Exit 101; BLOCKED by same dependency resolution failure; lint did not execute |
| `cargo test --manifest-path runtime/Cargo.toml --workspace --locked --offline` | Exit 101; BLOCKED by same dependency resolution failure; tests did not execute |
| `cargo clippy --manifest-path runtime/Cargo.toml --workspace --all-targets --locked --offline -- -D warnings` | Exit 101; BLOCKED by same dependency resolution failure; lint did not execute |
| `cargo fmt --manifest-path runtime/Cargo.toml --all -- --check` | Exit 0 |
| `python3.12 -B reference/token_reward/reward_console.py --fixture reference/token_reward/fixtures/reward_session.json --mode in-process < reference/token_reward/fixtures/reward_console_source_{journey,cancellation,boundaries}.txt` (three separate commands) | Exits 0, 0, 1 respectively; empty stderr |
| Same three commands with `--mode subprocess --cleanup-timeout 1` | Exits 0, 0, 1 respectively; empty stderr; complete output identical to in-process captures |
| `python3.12 -B validation/2026-11-09-plan-local-reward-source-composer/verify_preservation.py` | Exit 0; required locked blobs and all 123 protected files match before/after |
| `git diff --check` | Exit 0 |

The initial failure was an overly strict new assertion: it expected every
printed proposal to have dispatched, but the boundary transcript deliberately
contains one declined proposal. The test now checks full raw/guided receipt
parity and explicitly includes that declined proposal in the preview expectation.
No product implementation fix or contract change was required. The passing
focused rerun preceded the passing full suite.

Both transcript modes reproduce the same envelopes. Journey receipts retain
historical OBSERVED duplicates while the explicit view is ISSUED with one spend.
Cancellation views are REVERSED then CLAWBACK_CLAIM. The separate refund receipt
retains token phase ISSUED, records KRW_REFUND_NOTED and has a distinct effect ID.
Boundary captures contain three recoverable input errors, one decline and the
existing WINDOW_OPEN / forbidden-pool / AI-approval domain refusals.

These are the closest applicable local checks from `.github/workflows/protocol.yml`
and `ktx-kernel.yml`, plus the design plan's Rust checks. Full hosted workflows,
Move/ZK/chain jobs and unrelated suites were not run. Rust tests/Clippy require
a provisioned offline cache; network access was not attempted.

## Changed paths and preservation

The complete delivered path inventory is [changed-paths.txt](changed-paths.txt).
It includes the console, two existing test modules, three new transcripts,
`reference/token_reward/README.md`, `docs/README.md` and this evidence directory.
No client, CLI, session, model, FSM, authoritative contract or policy was changed.

Before editing, both locked Git blobs matched:

| Path | Git blob before and required after |
|---|---|
| `runtime/crates/kix-kernel/src/lib.rs` | `69564b166f0c27f9af5d8422f0a466b18d74c20f` |
| `runtime/crates/kix-kernel/tests/quarantine_capacity.rs` | `b607996c83a119c349f1cc90469ac1ba82764e20` |

[preservation-before.json](preservation-before.json) records SHA-256 for both
locked files and every file under `reference/v0.3-rc1/`, `.aiops/`, `docs/tasks/`
and `.github/workflows/` (123 files). [verify_preservation.py](verify_preservation.py)
compares membership and bytes and verifies the required Git blobs without mutation.
There was no merge, so merge-commit lock verification is not applicable.

## Deviations, limitations and pending gates

The design was implemented without a scope change. The startup fetch is intentionally omitted under the supervisor's explicit
network prohibition, as are commit/publication and hosted CI queries. Local
checks do not establish hosted workflow success. Four Rust test/Clippy commands
are blocked by the missing offline `bcs` dependency, as recorded above; supplying
the existing pinned dependency cache and completing those checks remains a
supervisor verification item, not a product-policy decision. A2 non-author exact-head review
and completed/success KTX kernel verification and KIX protocol verification for
the supervisor's eventual final head remain required; this delivery is not
merge-ready. No previous head's CI is reused.

No hardware, money, service, credential, product policy value, protocol command,
new coin/TIX module, storage engine or consequential scope expansion was needed.
Policy values remain **UNDETERMINED — Astra/User**; legal effects remain
**UNDETERMINED — User/legal**. All activation locks and capability grades remain.
No real funds, PG/bank/KYC calls, public endpoint, chain execution, production
runtime, durability, distributed fencing, chain finality, legal compliance or
production readiness is tested or claimed. No source machine is connected.

No explicit contract violation or new contract-undefined behavior was found.
Existing class-B observations are unchanged; source inputs are unauthenticated
synthetic assertions. The existing FSM owns refusal ordering and cancellation /
refund semantics. Follow-up is limited to supervisor publication and the required
review/CI gates, outside this builder session.
